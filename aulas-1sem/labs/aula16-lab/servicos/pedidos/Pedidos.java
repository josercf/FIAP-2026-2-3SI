// LogiTech Enterprise - Serviço de Pedidos (Bounded Context: Pedidos).
//
// ATENÇÃO, LEIA ANTES DE COMPARAR COM A AULA 05
// ---------------------------------------------
// Esta é uma versão **mínima** do serviço, escrita para o laboratório da
// Aula 07 ter o que orquestrar. Ela cumpre exatamente o contrato da
// plataforma (ADR-006): porta 8080, as seis rotas, `/health` devolvendo
// {"status":"ok"} e o schema `pedidos` no PostgreSQL.
//
// O que ela **não** é: a implementação da Aula 05. Lá o serviço nasce em
// Spring Boot 3, com Repository, Factory Method e injeção de dependência,
// que é justamente o conteúdo daquela aula. Aqui só existe o servidor HTTP
// da própria JDK e JDBC direto, porque o assunto de hoje é orquestração, não
// arquitetura interna de serviço. Quando as duas aulas se encontrarem, esta
// pasta é substituída pela versão da Aula 05 sem que uma linha do
// docker-compose.yml precise mudar: é para isso que o contrato existe.
//
// Não é tarefa. Não editem este arquivo.
//
// Rotas (ADR-006 e ADR-009):
//   GET   /health                             aberta, sempre
//   GET   /api/v1/pedidos                     CLIENTE, MOTORISTA ou ADMIN
//   GET   /api/v1/pedidos/{id}                qualquer papel autenticado
//   POST  /api/v1/pedidos                     CLIENTE ou ADMIN
//   PATCH /api/v1/pedidos/{id}/endereco       CLIENTE ou ADMIN
//   GET   /api/v1/pedidos/{id}/status         qualquer papel autenticado
//
// Versão da Aula 16: ganhou CORS (ADR-008) e validação de JWT com RBAC
// (ADR-009), em `Seguranca.java`. Com LOGITECH_AUTH_ATIVA desligada este
// serviço se comporta exatamente como na Aula 07.

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;

public class Pedidos {

    static final int PORTA = Integer.parseInt(env("LOGITECH_PORTA", "8080"));
    static final String DB_URL = env("LOGITECH_DB_URL", "jdbc:postgresql://localhost:5432/logitech");
    static final String DB_USER = env("LOGITECH_DB_USER", "logitech");
    static final String DB_PASSWORD = env("LOGITECH_DB_PASSWORD", "logitech");
    static final String FRETE_URL = env("LOGITECH_FRETE_URL", "http://localhost:8000");
    static final String FATURAMENTO_URL = env("LOGITECH_FATURAMENTO_URL", "http://localhost:5080");
    static final String NOTIFICACOES_URL = env("LOGITECH_NOTIFICACOES_URL", "http://localhost:3001");
    static final String CORS_ORIGINS = env("LOGITECH_CORS_ORIGINS",
            "http://localhost:5173,http://localhost:4200");

    static final Instant INICIADO_EM = Instant.now();
    static Connection conexao;

    static final HttpClient http = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(3))
            .build();

    static String env(String nome, String padrao) {
        String valor = System.getenv(nome);
        return (valor == null || valor.isBlank()) ? padrao : valor;
    }

    // -----------------------------------------------------------------
    // Subida: falha rápido quando o banco não aceita conexão
    // -----------------------------------------------------------------

    public static void main(String[] args) throws Exception {
        System.out.println("=== LogiTech Enterprise - Serviço de Pedidos ===");
        System.out.println("banco: " + DB_URL);

        // Nenhuma retentativa aqui, de propósito. Um laço de espera dentro da
        // aplicação até o banco responder é uma solução legítima e usada em
        // produção, mas ela **esconde** o problema que o Passo 1 do
        // laboratório quer mostrar: sem `healthcheck` mais
        // `condition: service_healthy`, o Compose sobe este serviço enquanto
        // o PostgreSQL ainda está inicializando, e ele morre na largada.
        // Falhar rápido e alto é o que torna a lição visível.
        try {
            conexao = DriverManager.getConnection(DB_URL, DB_USER, DB_PASSWORD);
        } catch (SQLException erro) {
            System.err.println("[FATAL] o banco de dados não aceitou a conexão: "
                    + erro.getMessage());
            System.err.println("[FATAL] o serviço de pedidos não sobe sem banco. "
                    + "Encerrando com código 1.");
            System.exit(1);
            return;
        }

        criarSchema();

        HttpServer servidor = HttpServer.create(new InetSocketAddress("0.0.0.0", PORTA), 0);
        servidor.setExecutor(Executors.newFixedThreadPool(8));
        servidor.createContext("/health", Pedidos::health);
        servidor.createContext("/api/v1/pedidos", Pedidos::pedidos);
        servidor.start();

        System.out.println("[HTTP] pedidos escutando na porta " + PORTA);
    }

    /**
     * A conexão com o banco, reaberta quando o servidor a derruba.
     *
     * Uma única `Connection` compartilhada morre depois de algumas horas de
     * ociosidade, e a próxima consulta falha com "This connection has been
     * closed" mesmo com o PostgreSQL saudável. Aconteceu na validação deste
     * laboratório, 45 minutos depois da subida.
     *
     * Serviço de verdade usa **pool** de conexões (HikariCP no Spring Boot da
     * Aula 05), que resolve isto e mais uma dúzia de problemas. Aqui está a
     * versão mínima: conferir e reabrir. O importante é que isto vale para
     * **depois** da subida; a falha inicial continua fatal de propósito, para
     * o Passo 1 do laboratório continuar demonstrável.
     */
    static synchronized Connection banco() throws SQLException {
        if (conexao == null || conexao.isClosed() || !conexao.isValid(2)) {
            conexao = DriverManager.getConnection(DB_URL, DB_USER, DB_PASSWORD);
            System.out.println("[DB] conexão reaberta");
        }
        return conexao;
    }

    static void criarSchema() throws SQLException {
        // Um schema por Bounded Context, como manda a ADR-006. Ninguém lê a
        // tabela do vizinho: quem precisa de dado alheio chama a API dele.
        try (Statement st = banco().createStatement()) {
            st.execute("CREATE SCHEMA IF NOT EXISTS pedidos");
            st.execute("""
                CREATE TABLE IF NOT EXISTS pedidos.pedido (
                    id           SERIAL PRIMARY KEY,
                    cliente      TEXT        NOT NULL,
                    origem       TEXT        NOT NULL,
                    destino      TEXT        NOT NULL,
                    peso_kg      NUMERIC(10,2) NOT NULL,
                    modalidade   TEXT        NOT NULL,
                    valor_frete  NUMERIC(10,2),
                    prazo_dias   INTEGER,
                    situacao     TEXT        NOT NULL DEFAULT 'RECEBIDO',
                    criado_em    TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """);
        }
        System.out.println("[DB] schema pedidos pronto");
    }

    // -----------------------------------------------------------------
    // Rotas
    // -----------------------------------------------------------------

    static void health(HttpExchange troca) throws IOException {
        long uptime = Duration.between(INICIADO_EM, Instant.now()).toSeconds();
        boolean bancoOk;
        try {
            // `banco()` reabre a conexão se ela tiver caído, então o
            // healthcheck do Compose também é o que devolve o serviço ao ar
            // depois de uma queda de rede curta.
            bancoOk = banco().isValid(2);
        } catch (SQLException erro) {
            bancoOk = false;
        }
        Map<String, Object> corpo = new LinkedHashMap<>();
        corpo.put("status", bancoOk ? "ok" : "degradado");
        corpo.put("servico", "pedidos");
        corpo.put("uptime_s", uptime);
        corpo.put("banco", bancoOk ? "conectado" : "sem conexão");
        corpo.put("auth_ativa", Seguranca.ativa());
        responder(troca, bancoOk ? 200 : 503, Json.objeto(corpo));
    }

    static void pedidos(HttpExchange troca) throws IOException {
        String caminho = troca.getRequestURI().getPath();
        String metodo = troca.getRequestMethod();

        // Preflight do CORS. O navegador manda um OPTIONS antes de qualquer
        // PATCH ou de qualquer requisição com cabeçalho Authorization, e ele
        // vem SEM token: responder 401 aqui derrubaria a tela inteira com um
        // erro que não fala de autenticação em lugar nenhum.
        if (metodo.equals("OPTIONS")) {
            responder(troca, 204, "");
            return;
        }

        // RBAC, exatamente como a ADR-009 fixou. A tabela abaixo é o contrato
        // e a mesma que o verificador da Aula 16 confere.
        if (Seguranca.ativa()) {
            String[] aceitos;
            if (caminho.equals("/api/v1/pedidos") && metodo.equals("POST")) {
                aceitos = new String[]{"CLIENTE", "ADMIN"};
            } else if (caminho.endsWith("/endereco") && metodo.equals("PATCH")) {
                aceitos = new String[]{"CLIENTE", "ADMIN"};
            } else if (caminho.equals("/api/v1/pedidos") && metodo.equals("GET")) {
                aceitos = new String[]{"CLIENTE", "MOTORISTA", "ADMIN"};
            } else {
                aceitos = new String[0];      // qualquer papel autenticado
            }
            try {
                Seguranca.exigir(troca.getRequestHeaders().getFirst("Authorization"), aceitos);
            } catch (Seguranca.ErroDePapel erro) {
                responder(troca, 403, Json.erro("sem permissão para esta rota", erro.getMessage()));
                return;
            } catch (Seguranca.ErroDeToken erro) {
                responder(troca, 401, Json.erro("não autenticado", erro.getMessage()));
                return;
            }
        }

        try {
            if (caminho.equals("/api/v1/pedidos")) {
                if (metodo.equals("GET")) {
                    listar(troca);
                    return;
                }
                if (metodo.equals("POST")) {
                    criar(troca);
                    return;
                }
                responder(troca, 405, Json.erro("método não permitido", metodo));
                return;
            }

            if (caminho.endsWith("/status") && metodo.equals("GET")) {
                status(troca, idDe(caminho, "/status"));
                return;
            }

            if (caminho.endsWith("/endereco") && metodo.equals("PATCH")) {
                alterarEndereco(troca, idDe(caminho, "/endereco"));
                return;
            }

            if (metodo.equals("GET")) {
                buscar(troca, idDe(caminho, ""));
                return;
            }

            responder(troca, 405, Json.erro("método não permitido", metodo));
        } catch (SQLException erro) {
            responder(troca, 500, Json.erro("falha ao falar com o banco", erro.getMessage()));
        } catch (NumberFormatException erro) {
            responder(troca, 400, Json.erro("identificador de pedido inválido", caminho));
        }
    }

    static long idDe(String caminho, String sufixo) {
        String resto = caminho.substring("/api/v1/pedidos/".length());
        if (!sufixo.isEmpty()) {
            resto = resto.substring(0, resto.length() - sufixo.length());
        }
        return Long.parseLong(resto.replace("/", ""));
    }

    static void listar(HttpExchange troca) throws IOException, SQLException {
        List<String> linhas = new ArrayList<>();
        try (Statement st = banco().createStatement();
             ResultSet rs = st.executeQuery(
                     "SELECT * FROM pedidos.pedido ORDER BY id DESC LIMIT 100")) {
            while (rs.next()) linhas.add(Json.objeto(comoMapa(rs)));
        }
        responder(troca, 200, "[" + String.join(",", linhas) + "]");
    }

    static void buscar(HttpExchange troca, long id) throws IOException, SQLException {
        try (PreparedStatement st = banco().prepareStatement(
                "SELECT * FROM pedidos.pedido WHERE id = ?")) {
            st.setLong(1, id);
            try (ResultSet rs = st.executeQuery()) {
                if (!rs.next()) {
                    responder(troca, 404, Json.erro("pedido não encontrado", String.valueOf(id)));
                    return;
                }
                responder(troca, 200, Json.objeto(comoMapa(rs)));
            }
        }
    }

    static void status(HttpExchange troca, long id) throws IOException, SQLException {
        try (PreparedStatement st = banco().prepareStatement(
                "SELECT id, situacao, destino FROM pedidos.pedido WHERE id = ?")) {
            st.setLong(1, id);
            try (ResultSet rs = st.executeQuery()) {
                if (!rs.next()) {
                    responder(troca, 404, Json.erro("pedido não encontrado", String.valueOf(id)));
                    return;
                }
                Map<String, Object> corpo = new LinkedHashMap<>();
                corpo.put("id", rs.getLong("id"));
                corpo.put("situacao", rs.getString("situacao"));
                corpo.put("destino", rs.getString("destino"));
                responder(troca, 200, Json.objeto(corpo));
            }
        }
    }

    static void alterarEndereco(HttpExchange troca, long id) throws IOException, SQLException {
        Map<String, String> corpo = Json.lerObjetoPlano(corpoDe(troca));
        String destino = corpo.get("destino");
        if (destino == null || destino.isBlank()) {
            responder(troca, 400, Json.erro("campo obrigatório ausente", "destino"));
            return;
        }
        try (PreparedStatement st = banco().prepareStatement(
                "UPDATE pedidos.pedido SET destino = ? WHERE id = ?")) {
            st.setString(1, destino);
            st.setLong(2, id);
            if (st.executeUpdate() == 0) {
                responder(troca, 404, Json.erro("pedido não encontrado", String.valueOf(id)));
                return;
            }
        }
        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("id", id);
        resposta.put("destino", destino);
        resposta.put("alterado_em", Instant.now().toString());
        responder(troca, 200, Json.objeto(resposta));
    }

    /**
     * O caminho completo de um pedido pela plataforma: cota o frete, grava,
     * emite a fatura e notifica o cliente.
     *
     * Cada etapa registra o próprio resultado em `jornada` em vez de derrubar
     * a requisição inteira. É o que permite ao Passo 5 do laboratório provar,
     * numa única chamada, que os quatro serviços se enxergam pela rede do
     * Compose: se um deles não estiver de pé, a etapa dele aparece como
     * "indisponível", com o motivo, e o pedido continua gravado.
     */
    static void criar(HttpExchange troca) throws IOException, SQLException {
        // O token de quem chamou é repassado adiante. Nesta plataforma os
        // backends são *resource servers*, não clients (ADR-009): eles não têm
        // segredo próprio e não pedem token em nome de ninguém. O que resta é
        // propagar a credencial do usuário, e a consequência é visível: quem
        // entra como CLIENTE cria o pedido e recebe 403 na emissão da fatura,
        // porque `POST /api/v1/faturas` exige ADMIN. A jornada mostra isso.
        String autorizacao = troca.getRequestHeaders().getFirst("Authorization");
        Map<String, String> entrada = Json.lerObjetoPlano(corpoDe(troca));
        String cliente = entrada.getOrDefault("cliente", "");
        String origem = entrada.getOrDefault("origem", "");
        String destino = entrada.getOrDefault("destino", "");
        String modalidade = entrada.getOrDefault("modalidade", "economico");
        String pesoTexto = entrada.getOrDefault("pesoKg", "");

        List<String> faltando = new ArrayList<>();
        if (cliente.isBlank()) faltando.add("cliente");
        if (origem.isBlank()) faltando.add("origem");
        if (destino.isBlank()) faltando.add("destino");
        if (pesoTexto.isBlank()) faltando.add("pesoKg");
        if (!faltando.isEmpty()) {
            responder(troca, 400, Json.erro("campos obrigatórios ausentes",
                    String.join(", ", faltando)));
            return;
        }

        double pesoKg;
        try {
            pesoKg = Double.parseDouble(pesoTexto);
        } catch (NumberFormatException erro) {
            responder(troca, 400, Json.erro("pesoKg precisa ser numérico", pesoTexto));
            return;
        }

        Map<String, Object> jornada = new LinkedHashMap<>();

        // 1. Cotação de frete
        double valorFrete = 0;
        int prazoDias = 0;
        String cotacao = chamar("frete", FRETE_URL + "/api/v1/frete/cotacao", "POST",
                Json.objeto(Map.of("origem", origem, "destino", destino,
                        "pesoKg", pesoKg, "modalidade", modalidade)), jornada, autorizacao);
        if (cotacao != null) {
            Map<String, String> lido = Json.lerObjetoPlano(cotacao);
            valorFrete = Double.parseDouble(lido.getOrDefault("valor", "0"));
            prazoDias = (int) Double.parseDouble(lido.getOrDefault("prazoDias", "0"));
        }

        // 2. Gravação no banco, o único passo que não pode falhar em silêncio
        long id;
        try (PreparedStatement st = banco().prepareStatement(
                "INSERT INTO pedidos.pedido "
                        + "(cliente, origem, destino, peso_kg, modalidade, valor_frete, prazo_dias) "
                        + "VALUES (?,?,?,?,?,?,?) RETURNING id")) {
            st.setString(1, cliente);
            st.setString(2, origem);
            st.setString(3, destino);
            st.setDouble(4, pesoKg);
            st.setString(5, modalidade);
            st.setDouble(6, valorFrete);
            st.setInt(7, prazoDias);
            try (ResultSet rs = st.executeQuery()) {
                rs.next();
                id = rs.getLong(1);
            }
        }
        jornada.put("pedidos", "ok");

        // 3. Emissão da fatura
        chamar("faturamento", FATURAMENTO_URL + "/api/v1/faturas", "POST",
                Json.objeto(Map.of("pedidoId", id, "cliente", cliente, "valor", valorFrete)),
                jornada, autorizacao);

        // 4. Notificação ao cliente
        chamar("notificacoes", NOTIFICACOES_URL + "/api/v1/notificacoes", "POST",
                Json.objeto(Map.of("canal", "email",
                        "destinatario", cliente,
                        "mensagem", "Pedido " + id + " recebido, frete " + valorFrete)),
                jornada, autorizacao);

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("id", id);
        resposta.put("cliente", cliente);
        resposta.put("origem", origem);
        resposta.put("destino", destino);
        resposta.put("pesoKg", pesoKg);
        resposta.put("modalidade", modalidade);
        resposta.put("valorFrete", valorFrete);
        resposta.put("prazoDias", prazoDias);
        resposta.put("situacao", "RECEBIDO");
        resposta.put("jornada", jornada);
        responder(troca, 201, Json.objeto(resposta));
    }

    /** Faz a chamada a um serviço vizinho e anota o desfecho na jornada. */
    static String chamar(String servico, String url, String metodo,
                         String corpo, Map<String, Object> jornada, String autorizacao) {
        try {
            HttpRequest.Builder construtor = HttpRequest.newBuilder(URI.create(url))
                    .timeout(Duration.ofSeconds(5))
                    .header("Content-Type", "application/json")
                    .method(metodo, HttpRequest.BodyPublishers.ofString(corpo, StandardCharsets.UTF_8));
            if (autorizacao != null && !autorizacao.isBlank()) {
                construtor = construtor.header("Authorization", autorizacao);
            }
            HttpRequest requisicao = construtor.build();
            HttpResponse<String> resposta = http.send(requisicao, HttpResponse.BodyHandlers.ofString());
            if (resposta.statusCode() >= 200 && resposta.statusCode() < 300) {
                jornada.put(servico, "ok");
                return resposta.body();
            }
            jornada.put(servico, "recusado: HTTP " + resposta.statusCode());
            return null;
        } catch (Exception erro) {
            jornada.put(servico, "indisponível: " + erro.getClass().getSimpleName());
            return null;
        }
    }

    // -----------------------------------------------------------------
    // Apoio
    // -----------------------------------------------------------------

    static Map<String, Object> comoMapa(ResultSet rs) throws SQLException {
        Map<String, Object> mapa = new LinkedHashMap<>();
        mapa.put("id", rs.getLong("id"));
        mapa.put("cliente", rs.getString("cliente"));
        mapa.put("origem", rs.getString("origem"));
        mapa.put("destino", rs.getString("destino"));
        mapa.put("pesoKg", rs.getDouble("peso_kg"));
        mapa.put("modalidade", rs.getString("modalidade"));
        mapa.put("valorFrete", rs.getDouble("valor_frete"));
        mapa.put("prazoDias", rs.getInt("prazo_dias"));
        mapa.put("situacao", rs.getString("situacao"));
        mapa.put("criadoEm", String.valueOf(rs.getTimestamp("criado_em")));
        return mapa;
    }

    static String corpoDe(HttpExchange troca) throws IOException {
        try (InputStream entrada = troca.getRequestBody()) {
            return new String(entrada.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    static void responder(HttpExchange troca, int status, String corpo) throws IOException {
        byte[] bytes = corpo.getBytes(StandardCharsets.UTF_8);
        troca.getResponseHeaders().add("Content-Type", "application/json; charset=utf-8");
        aplicarCors(troca);
        // 204 não carrega corpo: informar tamanho aqui faz o cliente esperar
        // por bytes que nunca chegam.
        troca.sendResponseHeaders(status, status == 204 ? -1 : bytes.length);
        if (status != 204) troca.getResponseBody().write(bytes);
        troca.close();
    }

    /**
     * CORS entrou no contrato na ADR-008, quando o consumidor deixou de ser
     * outro servidor e passou a ser o navegador. `curl` ignora CORS: sem
     * estes cabeçalhos a suíte fica verde e a tela do Portal fica vazia.
     */
    static void aplicarCors(HttpExchange troca) {
        String origem = troca.getRequestHeaders().getFirst("Origin");
        if (origem == null) return;
        for (String permitida : CORS_ORIGINS.split(",")) {
            if (permitida.trim().equals(origem)) {
                troca.getResponseHeaders().add("Access-Control-Allow-Origin", origem);
                troca.getResponseHeaders().add("Access-Control-Allow-Credentials", "true");
                troca.getResponseHeaders().add("Access-Control-Allow-Headers",
                        "Authorization, Content-Type");
                troca.getResponseHeaders().add("Access-Control-Allow-Methods",
                        "GET, POST, PATCH, OPTIONS");
                return;
            }
        }
    }

    /**
     * JSON mínimo, só o suficiente para o contrato desta aula.
     *
     * Serviço de verdade usa Jackson ou System.Text.Json; aqui não há
     * dependência externa nenhuma de propósito, para a imagem ser pequena e
     * o build não depender de repositório de artefatos além do driver JDBC.
     */
    static final class Json {

        static String objeto(Map<String, ?> campos) {
            StringBuilder sb = new StringBuilder("{");
            boolean primeiro = true;
            for (Map.Entry<String, ?> campo : campos.entrySet()) {
                if (!primeiro) sb.append(',');
                primeiro = false;
                sb.append(texto(campo.getKey())).append(':').append(valor(campo.getValue()));
            }
            return sb.append('}').toString();
        }

        @SuppressWarnings("unchecked")
        static String valor(Object v) {
            if (v == null) return "null";
            if (v instanceof Number || v instanceof Boolean) return String.valueOf(v);
            if (v instanceof Map) return objeto((Map<String, ?>) v);
            return texto(String.valueOf(v));
        }

        static String texto(String s) {
            StringBuilder sb = new StringBuilder("\"");
            for (char c : s.toCharArray()) {
                switch (c) {
                    case '"' -> sb.append("\\\"");
                    case '\\' -> sb.append("\\\\");
                    case '\n' -> sb.append("\\n");
                    case '\r' -> sb.append("\\r");
                    case '\t' -> sb.append("\\t");
                    default -> {
                        if (c < 0x20) sb.append(String.format("\\u%04x", (int) c));
                        else sb.append(c);
                    }
                }
            }
            return sb.append('"').toString();
        }

        static String erro(String mensagem, String detalhe) {
            Map<String, Object> corpo = new LinkedHashMap<>();
            corpo.put("erro", mensagem);
            corpo.put("detalhe", detalhe);
            return objeto(corpo);
        }

        /**
         * Lê um objeto JSON de um nível só, devolvendo todo valor como texto.
         * Objetos e listas aninhados são ignorados: nenhum payload deste
         * laboratório precisa deles.
         */
        static Map<String, String> lerObjetoPlano(String json) {
            Map<String, String> mapa = new LinkedHashMap<>();
            if (json == null) return mapa;
            int i = 0;
            int n = json.length();
            int profundidade = 0;
            String chave = null;
            StringBuilder atual = new StringBuilder();
            boolean dentroDeTexto = false;
            boolean escapado = false;

            while (i < n) {
                char c = json.charAt(i++);
                if (dentroDeTexto) {
                    if (escapado) {
                        atual.append(switch (c) {
                            case 'n' -> '\n';
                            case 't' -> '\t';
                            case 'r' -> '\r';
                            default -> c;
                        });
                        escapado = false;
                    } else if (c == '\\') {
                        escapado = true;
                    } else if (c == '"') {
                        dentroDeTexto = false;
                    } else {
                        atual.append(c);
                    }
                    continue;
                }
                switch (c) {
                    case '"' -> {
                        dentroDeTexto = true;
                        atual.setLength(0);
                    }
                    case '{', '[' -> profundidade++;
                    case '}', ']' -> {
                        profundidade--;
                        // Ao fechar o objeto de nível 1 a profundidade volta a
                        // zero: é aí que o último par chave/valor se completa.
                        if (chave != null && profundidade == 0) {
                            mapa.put(chave, atual.toString().trim());
                            chave = null;
                        }
                    }
                    case ':' -> {
                        if (profundidade == 1) {
                            chave = atual.toString();
                            atual.setLength(0);
                        }
                    }
                    case ',' -> {
                        if (profundidade == 1 && chave != null) {
                            mapa.put(chave, atual.toString().trim());
                            chave = null;
                            atual.setLength(0);
                        }
                    }
                    default -> {
                        if (!Character.isWhitespace(c)) atual.append(c);
                    }
                }
            }
            if (chave != null && !atual.isEmpty()) {
                mapa.put(chave, atual.toString().trim());
            }
            return mapa;
        }
    }
}
