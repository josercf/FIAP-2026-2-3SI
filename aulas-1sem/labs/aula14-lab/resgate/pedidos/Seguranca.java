// LogiTech Enterprise - a camada de seguranca do servico de Pedidos.
//
// RESGATE: esta e a versao COM as lacunas TODO-2 e TODO-3 preenchidas.
//
// Use quando travar, e nao como atalho: copie por cima de
// `servicos/pedidos/Seguranca.java`, reconstrua o servico, registre
// `USEI_O_RESGATE: sim` em `docs/EVIDENCIAS.md` e siga em frente. Os passos
// seguintes dependem deste, e ficar parado aqui custa o resto da noite.
//
//     cp resgate/pedidos/Seguranca.java servicos/pedidos/Seguranca.java
//     docker compose up -d --build pedidos
//
// Tudo em volta ja esta pronto: `Pedidos.java` chama `Seguranca.guarda(...)`
// antes de despachar qualquer rota, `Jwt.java` sabe conferir a assinatura
// contra o JWKS e `Json.java` le e escreve JSON. O que falta e a decisao:
//
//   TODO-2  quem esta chamando, e o que fazer quando nao da para saber  -> 401
//   TODO-3  esse alguem pode chamar esta rota                           -> 403
//
// Confira o seu trabalho sem subir nada:
//     docker compose exec pedidos java -cp /app/classes TestesSeguranca
// ou, com JDK 21 na maquina:
//     javac -d /tmp/a14 servicos/pedidos/*.java && java -cp /tmp/a14 TestesSeguranca

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class Seguranca {

    // -----------------------------------------------------------------
    // Configuracao, toda vinda do ambiente (contrato da ADR-009)
    // -----------------------------------------------------------------

    /**
     * O interruptor. Padrao `false`, e isso e deliberado: os laboratorios das
     * Aulas 05 a 12 foram escritos sem autenticacao e continuam passando com
     * ele desligado. O `docker-compose.yml` DESTE laboratorio liga, e o
     * verificador so da o criterio por cumprido com ele ligado.
     *
     * Nao e porta dos fundos escondida: esta no README, esta no slide, e o
     * proprio `/health` responde qual e o valor.
     */
    public static boolean ATIVA =
            Boolean.parseBoolean(env("LOGITECH_AUTH_ATIVA", "false"));

    /** De onde baixar a chave publica. Endereco DE REDE: `keycloak:8090`. */
    static String JWKS_URL = env("LOGITECH_OIDC_JWKS_URL",
            "http://keycloak:8090/realms/logitech/protocol/openid-connect/certs");

    /**
     * Emissores confiaveis, separados por virgula.
     *
     * Repare que sao DUAS variaveis diferentes, e que os valores nao batem.
     * O `iss` que vem dentro do token e o endereco pelo qual o NAVEGADOR
     * falou com o Keycloak (`localhost:8090`); o JWKS e baixado pelo
     * endereco pelo qual ESTE CONTAINER alcanca o Keycloak (`keycloak:8090`).
     * O mesmo servidor, dois nomes, e o token so conhece um deles.
     */
    static String ISSUERS_ACEITOS = env("LOGITECH_OIDC_ISSUER",
            "http://keycloak:8090/realms/logitech");

    // Os tres campos acima nao sao `final` por um motivo so: `TestesSeguranca`
    // troca os valores para apontar para um JWKS de mentira, em memoria, e
    // rodar a suite inteira sem Keycloak nenhum no ar. Em producao isso seria
    // uma superficie a mais; aqui e o que permite testar a decisao de
    // autorizacao offline, em menos de um segundo.

    static String env(String nome, String padrao) {
        String v = System.getenv(nome);
        return (v == null || v.isBlank()) ? padrao : v;
    }

    // -----------------------------------------------------------------
    // Os dois jeitos de dizer nao
    // -----------------------------------------------------------------

    /** 401: eu nao sei quem voce e. Vira `WWW-Authenticate: Bearer`. */
    public static class NaoAutenticado extends RuntimeException {
        public NaoAutenticado(String motivo) { super(motivo); }
    }

    /** 403: eu sei quem voce e, e voce nao pode. Repetir o login nao ajuda. */
    public static class SemPermissao extends RuntimeException {
        public final Set<String> tinha;
        public final List<String> precisava;
        public SemPermissao(Set<String> tinha, List<String> precisava) {
            super("papel insuficiente");
            this.tinha = tinha;
            this.precisava = precisava;
        }
    }

    /** Quem esta chamando, depois de a assinatura ter sido conferida. */
    public static final class Identidade {
        public final String usuario;
        public final Set<String> papeis;
        public final long expiraEmS;
        public final String issuer;

        public Identidade(String usuario, Set<String> papeis, long expiraEmS, String issuer) {
            this.usuario = usuario;
            this.papeis = papeis;
            this.expiraEmS = expiraEmS;
            this.issuer = issuer;
        }
    }

    // -----------------------------------------------------------------
    // A tabela de regras (era o TODO-3a)
    // -----------------------------------------------------------------

    /** Uma linha do contrato: metodo, padrao de caminho e papeis aceitos. */
    static final class Regra {
        final String metodo;
        final String padrao;          // regex do caminho
        final List<String> papeis;    // vazio = rota aberta

        Regra(String metodo, String padrao, String... papeis) {
            this.metodo = metodo;
            this.padrao = padrao;
            this.papeis = List.of(papeis);
        }

        boolean casa(String metodo, String caminho) {
            return this.metodo.equals(metodo) && caminho.matches(padrao);
        }
    }

    static final List<String> QUALQUER_PAPEL = List.of("CLIENTE", "MOTORISTA", "ADMIN");

    /*
     * A tabela abaixo e o contrato da ADR-009, ja completo.
     *
     *   pedidos  GET   /health                         aberta
     *            GET   /api/v1/pedidos                 CLIENTE, MOTORISTA ou ADMIN
     *            GET   /api/v1/pedidos/{id}            qualquer papel autenticado
     *            POST  /api/v1/pedidos                 CLIENTE ou ADMIN
     *            PATCH /api/v1/pedidos/{id}/endereco   CLIENTE ou ADMIN
     *            GET   /api/v1/pedidos/{id}/status     qualquer papel autenticado
     *
     * A ORDEM IMPORTA: a primeira regra que casar decide. `/api/v1/pedidos`
     * e `/api/v1/pedidos/PED-1042` sao caminhos diferentes, e o regex de um
     * nao pode engolir o outro. As duas primeiras linhas ja estao escritas e
     * servem de modelo.
     *
     * A rota `/health` fica ABERTA, e nao e descuido: o `healthcheck` do
     * Compose nao carrega token. Protege-la derruba a orquestracao inteira,
     * e o container fica `unhealthy` sem que nada esteja errado com o
     * servico.
     */
    static final List<Regra> REGRAS = List.of(
            new Regra("GET", "/health"),
            new Regra("GET", "/api/v1/pedidos", "CLIENTE", "MOTORISTA", "ADMIN"),
            // As duas rotas com sufixo vem ANTES da rota do id solto: o regex
            // "/api/v1/pedidos/[^/]+" nao casa com "/PED-1042/status" porque
            // [^/]+ nao atravessa a barra, mas deixar as especificas na frente
            // torna a tabela legivel e imune a um regex mais frouxo depois.
            new Regra("GET", "/api/v1/pedidos/[^/]+/status",
                      QUALQUER_PAPEL.toArray(new String[0])),
            new Regra("PATCH", "/api/v1/pedidos/[^/]+/endereco", "CLIENTE", "ADMIN"),
            new Regra("GET", "/api/v1/pedidos/[^/]+",
                      QUALQUER_PAPEL.toArray(new String[0])),
            new Regra("POST", "/api/v1/pedidos", "CLIENTE", "ADMIN")
    );

    // -----------------------------------------------------------------
    // O cabecalho Authorization (era o TODO-2a)
    // -----------------------------------------------------------------

    /**
     * Extrai o token de um cabecalho `Authorization`.
     *
     * Devolve `null` quando nao ha token nenhum a extrair: cabecalho ausente,
     * vazio, com outro esquema (`Basic`), ou `Bearer` sem nada depois.
     *
     * O esquema e comparado SEM diferenciar maiusculas de minusculas: a
     * RFC 7235 diz que o esquema nao e sensivel a caixa, e cliente que manda
     * `bearer` minusculo existe de verdade. O token, esse sim, e byte a byte.
     */
    static String extrairBearer(String authorization) {
        if (authorization == null) return null;
        String[] partes = authorization.trim().split("\\s+", 2);
        if (partes.length != 2) return null;
        if (!"bearer".equalsIgnoreCase(partes[0])) return null;
        String token = partes[1].trim();
        return token.isEmpty() ? null : token;
    }

    // -----------------------------------------------------------------
    // Onde mora o papel (era o TODO-3b)
    // -----------------------------------------------------------------

    /**
     * Le os papeis do token.
     *
     * O papel viaja em `realm_access.roles`, uma lista de strings. E DAI que
     * este servico le, e e do MESMO lugar que o servico de Notificacoes, em
     * Node, vai ler. Esse alinhamento e o ponto central da ADR-009.
     *
     * Metade dos exemplos da internet le de `resource_access.<client>.roles`,
     * que e outro lugar do mesmo token e guarda os papeis DE CLIENT, nao os
     * de realm. Neste realm ele vem vazio: um servico lendo de la nunca
     * encontraria papel nenhum e devolveria 403 para todo mundo, com o token
     * perfeitamente valido.
     *
     * Devolve conjunto vazio quando a reivindicacao nao existe. Token
     * autenticado sem papel nenhum e uma situacao legitima, e ela leva a 403,
     * nunca a 401.
     */
    @SuppressWarnings("unchecked")
    static Set<String> papeisDoToken(Jwt jwt) {
        Set<String> papeis = new LinkedHashSet<>();
        Object bloco = jwt.conteudo().get("realm_access");
        if (bloco instanceof Map) {
            Object lista = ((Map<String, Object>) bloco).get("roles");
            if (lista instanceof List) {
                for (Object papel : (List<Object>) lista) {
                    papeis.add(String.valueOf(papel));
                }
            }
        }
        return papeis;
    }

    // -----------------------------------------------------------------
    // O portao
    // -----------------------------------------------------------------

    /**
     * Chamado por `Pedidos.java` antes de despachar qualquer rota.
     *
     * Devolve a `Identidade` de quem chamou, ou `null` quando a rota e aberta
     * ou quando a autenticacao esta desligada. Lanca `NaoAutenticado` (401)
     * ou `SemPermissao` (403).
     */
    public static Identidade guarda(String metodo, String caminho, String authorization) {
        List<String> exigidos = papeisExigidos(metodo, caminho);

        // Rota aberta: `/health`, e o que nao esta na tabela. Repare que uma
        // rota desconhecida cai aqui e segue em frente: quem devolve 404 e o
        // roteador, nao o portao. Um 401 numa rota que nem existe conta ao
        // atacante que ela existe.
        if (exigidos.isEmpty()) return null;

        // O interruptor da ADR-009. Desligado, o servico se comporta como nas
        // Aulas 05 a 12.
        if (!ATIVA) return null;

        // ---------------------------------------------------------------
        // Autenticar (era o TODO-2b e o TODO-2c)
        //
        // ---------------------------------------------------------------
        String compacto = extrairBearer(authorization);
        if (compacto == null) {
            throw new NaoAutenticado("cabecalho Authorization ausente ou fora do formato "
                                     + "'Bearer <token>'");
        }

        Jwt jwt;
        try {
            jwt = Jwt.verificar(compacto, JWKS_URL, ISSUERS_ACEITOS);
        } catch (Jwt.Invalido e) {
            throw new NaoAutenticado(e.getMessage());
        }

        Identidade quem = new Identidade(
                jwt.texto("preferred_username"),
                papeisDoToken(jwt),
                jwt.numero("exp") - jwt.numero("iat"),
                jwt.texto("iss"));

        // ---------------------------------------------------------------
        // Autorizar (era o TODO-3c)
        //
        // Se `quem.papeis` nao tiver NENHUM dos `exigidos`, lance
        // `new SemPermissao(quem.papeis, exigidos)`. Caso contrario, devolva
        // `quem`.
        //
        // Basta UM papel em comum. Um usuario com ADMIN e CLIENTE passa numa
        // rota que aceita qualquer um dos dois.
        // ---------------------------------------------------------------
        boolean pode = false;
        for (String aceito : exigidos) {
            if (quem.papeis.contains(aceito)) { pode = true; break; }
        }
        if (!pode) {
            throw new SemPermissao(quem.papeis, exigidos);
        }

        return quem;
    }

    /** Papeis exigidos por uma rota, segundo a tabela. Vazio = aberta. */
    static List<String> papeisExigidos(String metodo, String caminho) {
        for (Regra r : REGRAS) {
            if (r.casa(metodo, caminho)) return r.papeis;
        }
        return List.of();
    }

    /** Usado pelo /health para mostrar em que modo o servico esta. */
    public static Map<String, Object> diagnostico() {
        List<Object> rotas = new ArrayList<>();
        for (Regra r : REGRAS) {
            rotas.add(r.metodo + " " + r.padrao + " -> "
                      + (r.papeis.isEmpty() ? "aberta" : String.join("|", r.papeis)));
        }
        return Map.of(
                "autenticacaoAtiva", ATIVA,
                "issuersAceitos", Arrays.asList(ISSUERS_ACEITOS.split(",")),
                "jwksUrl", JWKS_URL,
                "regras", rotas);
    }

    private Seguranca() { }
}
