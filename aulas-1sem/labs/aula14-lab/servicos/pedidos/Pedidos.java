// LogiTech Enterprise - Servico de Pedidos (Bounded Context: Pedidos).
//
// CONGELADO: nao e tarefa do laboratorio. O que voce escreve hoje esta em
// `Seguranca.java`, e este arquivo so o chama.
//
// Versao minima do servico que nasce na Aula 05, escrita para o laboratorio
// da Aula 14 ter uma API real para proteger. Cumpre o contrato da plataforma
// (ADR-006): porta 8080, as rotas abaixo, `/health` devolvendo 200.
//
// Duas diferencas em relacao a Aula 05, as duas declaradas em
// `servicos/LEIA-ME.md`:
//   - o estado vive EM MEMORIA, sem PostgreSQL. O assunto de hoje e
//     autenticacao, e um banco a mais seria um container a mais para subir
//     sem ensinar nada de seguranca;
//   - nao ha Spring Boot: e o servidor HTTP da propria JDK. O filtro de
//     seguranca fica visivel linha a linha, em vez de escondido atras de uma
//     anotacao. Numa aula sobre validar token, ver a validacao vale mais do
//     que a comodidade.
//
// Rotas (ADR-006), com a autorizacao da ADR-009:
//   GET   /health                          aberta
//   GET   /api/v1/pedidos                  CLIENTE, MOTORISTA ou ADMIN
//   GET   /api/v1/pedidos/{id}             qualquer papel autenticado
//   POST  /api/v1/pedidos                  CLIENTE ou ADMIN
//   PATCH /api/v1/pedidos/{id}/endereco    CLIENTE ou ADMIN
//   GET   /api/v1/pedidos/{id}/status      qualquer papel autenticado

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

public class Pedidos {

    static final int PORTA = Integer.parseInt(env("LOGITECH_PORTA", "8080"));
    static final String CORS_ORIGINS = env("LOGITECH_CORS_ORIGINS",
            "http://localhost:5173,http://localhost:4200");

    static final String[] CAMPOS_ENDERECO = {"logradouro", "numero", "cidade", "uf", "cep"};

    static final Map<String, Map<String, Object>> BASE = new ConcurrentHashMap<>();
    static final AtomicInteger PROXIMO = new AtomicInteger(1045);

    public static void main(String[] args) throws IOException {
        semear();

        HttpServer servidor = HttpServer.create(new InetSocketAddress(PORTA), 0);
        servidor.createContext("/", Pedidos::despachar);
        servidor.setExecutor(Executors.newFixedThreadPool(8));
        servidor.start();

        System.out.println("[pedidos] no ar na porta " + PORTA);
        System.out.println("[pedidos] autenticacao ativa: " + Seguranca.ATIVA);
        System.out.println("[pedidos] " + Json.escrever(Seguranca.diagnostico()));
        if (!Seguranca.ATIVA) {
            System.out.println("[pedidos] AVISO: LOGITECH_AUTH_ATIVA esta desligada. "
                    + "Toda rota responde a qualquer um, como nas Aulas 05 a 12.");
        }
    }

    // -----------------------------------------------------------------
    // O portao, e so depois o roteador
    // -----------------------------------------------------------------

    static void despachar(HttpExchange troca) throws IOException {
        String metodo = troca.getRequestMethod();
        String caminho = troca.getRequestURI().getPath();

        cors(troca);
        if ("OPTIONS".equals(metodo)) {
            // Pre-flight do navegador. Nao carrega token e nao pode carregar:
            // e por isso que ele nunca passa pelo portao. Um servico que
            // devolve 401 no OPTIONS quebra qualquer SPA, e o sintoma no
            // console e um erro de CORS que nao tem nada a ver com CORS.
            responder(troca, 204, null);
            return;
        }

        Seguranca.Identidade quem;
        try {
            quem = Seguranca.guarda(metodo, caminho, troca.getRequestHeaders().getFirst("Authorization"));
        } catch (Seguranca.NaoAutenticado e) {
            troca.getResponseHeaders().add("WWW-Authenticate",
                    "Bearer realm=\"logitech\", error=\"invalid_token\"");
            responder(troca, 401, Map.of(
                    "erro", "nao_autenticado",
                    "motivo", String.valueOf(e.getMessage()),
                    "comoResolver", "obtenha um token pelo fluxo Authorization Code + PKCE "
                                    + "e mande no cabecalho Authorization: Bearer <token>"));
            return;
        } catch (Seguranca.SemPermissao e) {
            responder(troca, 403, Map.of(
                    "erro", "sem_permissao",
                    "papeisQueVoceTem", new ArrayList<>(e.tinha),
                    "papeisAceitos", e.precisava,
                    "comoResolver", "repetir o login NAO resolve: este usuario nao tem o papel. "
                                    + "Entre com um usuario que tenha."));
            return;
        } catch (Jwt.Invalido e) {
            // O JWKS pode falhar ao ser baixado dentro da verificacao.
            responder(troca, 401, Map.of("erro", "nao_autenticado", "motivo", String.valueOf(e.getMessage())));
            return;
        }

        try {
            rotear(troca, metodo, caminho, quem);
        } catch (RuntimeException e) {
            responder(troca, 500, Map.of("erro", "falha_interna", "detalhe", String.valueOf(e.getMessage())));
        }
    }

    static void rotear(HttpExchange troca, String metodo, String caminho, Seguranca.Identidade quem)
            throws IOException {

        if (caminho.equals("/health") && metodo.equals("GET")) {
            responder(troca, 200, Map.of(
                    "status", "ok",
                    "servico", "pedidos",
                    "autenticacaoAtiva", Seguranca.ATIVA));
            return;
        }

        if (caminho.equals("/api/v1/pedidos")) {
            if (metodo.equals("GET")) { listar(troca); return; }
            if (metodo.equals("POST")) { criar(troca, quem); return; }
        }

        if (caminho.matches("/api/v1/pedidos/[^/]+/status") && metodo.equals("GET")) {
            String id = caminho.split("/")[4];
            Map<String, Object> p = BASE.get(id);
            if (p == null) { naoAchou(troca, id); return; }
            responder(troca, 200, Map.of(
                    "pedidoId", p.get("pedidoId"),
                    "status", p.get("status"),
                    "ultimaPosicao", p.get("ultimaPosicao"),
                    "previsaoEntrega", p.get("previsaoEntrega"),
                    "atualizadoEm", p.get("atualizadoEm")));
            return;
        }

        if (caminho.matches("/api/v1/pedidos/[^/]+/endereco") && metodo.equals("PATCH")) {
            alterarEndereco(troca, caminho.split("/")[4], quem);
            return;
        }

        if (caminho.matches("/api/v1/pedidos/[^/]+") && metodo.equals("GET")) {
            String id = caminho.substring(caminho.lastIndexOf('/') + 1);
            Map<String, Object> p = BASE.get(id);
            if (p == null) { naoAchou(troca, id); return; }
            responder(troca, 200, p);
            return;
        }

        responder(troca, 404, Map.of("erro", "rota_desconhecida", "caminho", caminho));
    }

    // -----------------------------------------------------------------
    // As rotas
    // -----------------------------------------------------------------

    static void listar(HttpExchange troca) throws IOException {
        List<Object> lista = new ArrayList<>();
        List<String> ids = new ArrayList<>(BASE.keySet());
        Collections.sort(ids);
        for (String id : ids) {
            Map<String, Object> p = BASE.get(id);
            Map<String, Object> resumo = new LinkedHashMap<>();
            resumo.put("pedidoId", p.get("pedidoId"));
            resumo.put("cliente", p.get("cliente"));
            resumo.put("status", p.get("status"));
            resumo.put("previsaoEntrega", p.get("previsaoEntrega"));
            lista.add(resumo);
        }
        responder(troca, 200, Map.of("total", lista.size(), "pedidos", lista));
    }

    @SuppressWarnings("unchecked")
    static void criar(HttpExchange troca, Seguranca.Identidade quem) throws IOException {
        Map<String, Object> corpo;
        try {
            corpo = Json.lerObjeto(ler(troca));
        } catch (RuntimeException e) {
            responder(troca, 400, Map.of("erro", "json_invalido"));
            return;
        }
        String cliente = String.valueOf(corpo.getOrDefault("cliente", "")).trim();
        if (cliente.isEmpty()) {
            responder(troca, 400, Map.of("erro", "campos_ausentes", "campos", List.of("cliente")));
            return;
        }
        String id = "PED-" + PROXIMO.getAndIncrement();
        Map<String, Object> novo = new LinkedHashMap<>();
        novo.put("pedidoId", id);
        novo.put("cliente", cliente);
        novo.put("status", "AGUARDANDO_COLETA");
        novo.put("transportadora", "LogiTech Frota 07");
        novo.put("previsaoEntrega", LocalDate.now().plusDays(5).toString());
        novo.put("ultimaPosicao", "Centro de distribuicao Guarulhos");
        novo.put("atualizadoEm", agora());
        novo.put("criadoPor", quem == null ? "anonimo" : quem.usuario);
        novo.put("enderecoEntrega", corpo.get("enderecoEntrega"));
        BASE.put(id, novo);
        responder(troca, 201, novo);
    }

    @SuppressWarnings("unchecked")
    static void alterarEndereco(HttpExchange troca, String id, Seguranca.Identidade quem)
            throws IOException {
        Map<String, Object> pedido = BASE.get(id);
        if (pedido == null) { naoAchou(troca, id); return; }

        Map<String, Object> corpo;
        try {
            corpo = Json.lerObjeto(ler(troca));
        } catch (RuntimeException e) {
            responder(troca, 400, Map.of("erro", "json_invalido"));
            return;
        }

        List<String> ausentes = new ArrayList<>();
        for (String campo : CAMPOS_ENDERECO) {
            Object v = corpo.get(campo);
            if (v == null || String.valueOf(v).isBlank()) ausentes.add(campo);
        }
        if (!ausentes.isEmpty()) {
            responder(troca, 400, Map.of("erro", "campos_ausentes", "campos", ausentes));
            return;
        }

        Map<String, Object> endereco = new LinkedHashMap<>();
        for (String campo : CAMPOS_ENDERECO) endereco.put(campo, corpo.get(campo));
        if (corpo.get("complemento") != null) endereco.put("complemento", corpo.get("complemento"));

        pedido.put("enderecoEntrega", endereco);
        pedido.put("atualizadoEm", agora());
        pedido.put("alteradoPor", quem == null ? "anonimo" : quem.usuario);

        System.out.println("[pedidos] PATCH endereco " + id + " por "
                           + (quem == null ? "ANONIMO (autenticacao desligada)" : quem.usuario));
        responder(troca, 200, pedido);
    }

    static void naoAchou(HttpExchange troca, String id) throws IOException {
        responder(troca, 404, Map.of("erro", "pedido_nao_encontrado", "pedidoId", id));
    }

    // -----------------------------------------------------------------
    // Apoio
    // -----------------------------------------------------------------

    static void cors(HttpExchange troca) {
        String origem = troca.getRequestHeaders().getFirst("Origin");
        if (origem == null) return;
        for (String permitida : CORS_ORIGINS.split(",")) {
            if (permitida.trim().equals(origem)) {
                troca.getResponseHeaders().add("Access-Control-Allow-Origin", origem);
                troca.getResponseHeaders().add("Access-Control-Allow-Methods",
                        "GET,POST,PATCH,OPTIONS");
                // Sem este cabecalho o navegador recusa a requisicao que leva
                // o token, e o erro que aparece no console fala de CORS, nao
                // de autorizacao.
                troca.getResponseHeaders().add("Access-Control-Allow-Headers",
                        "Authorization,Content-Type");
                troca.getResponseHeaders().add("Access-Control-Max-Age", "600");
                return;
            }
        }
    }

    static String ler(HttpExchange troca) throws IOException {
        try (InputStream in = troca.getRequestBody()) {
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    static void responder(HttpExchange troca, int codigo, Object corpo) throws IOException {
        if (corpo == null) {
            troca.sendResponseHeaders(codigo, -1);
            troca.close();
            return;
        }
        byte[] bytes = Json.escrever(corpo).getBytes(StandardCharsets.UTF_8);
        troca.getResponseHeaders().add("Content-Type", "application/json; charset=utf-8");
        troca.sendResponseHeaders(codigo, bytes.length);
        troca.getResponseBody().write(bytes);
        troca.close();
    }

    static String agora() {
        return LocalDateTime.now().truncatedTo(ChronoUnit.SECONDS).toString();
    }

    static String env(String nome, String padrao) {
        String v = System.getenv(nome);
        return (v == null || v.isBlank()) ? padrao : v;
    }

    static void semear() {
        LocalDate hoje = LocalDate.now();
        BASE.put("PED-1042", pedido("PED-1042", "Distribuidora Sertao Norte", "EM_TRANSITO",
                "LogiTech Frota 07", hoje.plusDays(2).toString(), "Ribeirao Preto, SP",
                "Rua das Palmeiras", "455", "Ribeirao Preto", "SP", "14020-260"));
        BASE.put("PED-1043", pedido("PED-1043", "Supermercados Vale Verde", "AGUARDANDO_COLETA",
                "LogiTech Frota 12", hoje.plusDays(4).toString(), "Centro de distribuicao Guarulhos",
                "Avenida Brasil", "2100", "Guarulhos", "SP", "07034-000"));
        BASE.put("PED-1044", pedido("PED-1044", "Farmacias Vida Plena", "SAIU_PARA_ENTREGA",
                "LogiTech Frota 03", hoje.plusDays(1).toString(), "Sao Jose dos Campos, SP",
                "Rua Coronel Madureira", "88", "Sao Jose dos Campos", "SP", "12210-140"));
    }

    static Map<String, Object> pedido(String id, String cliente, String status,
                                      String frota, String previsao, String posicao,
                                      String logradouro, String numero, String cidade,
                                      String uf, String cep) {
        Map<String, Object> endereco = new LinkedHashMap<>();
        endereco.put("logradouro", logradouro);
        endereco.put("numero", numero);
        endereco.put("cidade", cidade);
        endereco.put("uf", uf);
        endereco.put("cep", cep);

        Map<String, Object> p = new LinkedHashMap<>();
        p.put("pedidoId", id);
        p.put("cliente", cliente);
        p.put("status", status);
        p.put("transportadora", frota);
        p.put("previsaoEntrega", previsao);
        p.put("ultimaPosicao", posicao);
        p.put("atualizadoEm", agora());
        p.put("enderecoEntrega", endereco);
        return p;
    }
}
