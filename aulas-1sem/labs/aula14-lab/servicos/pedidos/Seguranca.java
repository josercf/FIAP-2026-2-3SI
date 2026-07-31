// LogiTech Enterprise - a camada de seguranca do servico de Pedidos.
//
// ESTE ARQUIVO E SEU. Sao as lacunas TODO-2 e TODO-3 do laboratorio.
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
    // TODO-3a: a tabela de regras
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
     * TODO-3a: complete a tabela abaixo com o contrato da ADR-009.
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
            new Regra("GET", "/api/v1/pedidos", "CLIENTE", "MOTORISTA", "ADMIN")
            // TODO-3a-1: GET   /api/v1/pedidos/{id}          -> qualquer papel
            //            regex sugerido: "/api/v1/pedidos/[^/]+"
            // TODO-3a-2: GET   /api/v1/pedidos/{id}/status   -> qualquer papel
            //            regex sugerido: "/api/v1/pedidos/[^/]+/status"
            // TODO-3a-3: POST  /api/v1/pedidos               -> CLIENTE, ADMIN
            // TODO-3a-4: PATCH /api/v1/pedidos/{id}/endereco -> CLIENTE, ADMIN
            //            regex sugerido: "/api/v1/pedidos/[^/]+/endereco"
    );

    // -----------------------------------------------------------------
    // TODO-2a: o cabecalho Authorization
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
     *
     * TODO-2a: implemente.
     */
    static String extrairBearer(String authorization) {
        // Dica: separe em duas partes pelo primeiro espaco, confira se a
        // primeira e "bearer" ignorando a caixa, e devolva a segunda sem
        // espacos em volta. Qualquer outra forma devolve null.
        return null; // TODO-2a
    }

    // -----------------------------------------------------------------
    // TODO-3b: onde mora o papel
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
     *
     * TODO-3b: implemente.
     */
    @SuppressWarnings("unchecked")
    static Set<String> papeisDoToken(Jwt jwt) {
        Set<String> papeis = new LinkedHashSet<>();
        // Dica: `jwt.conteudo().get("realm_access")` devolve um Map<String,Object>
        // (ou null). Dentro dele, a chave "roles" e uma List<Object>. Converta
        // cada item com String.valueOf e acrescente em `papeis`.
        // TODO-3b
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
        // TODO-2b e TODO-2c: autenticar
        //
        // 1. `extrairBearer(authorization)`; se vier null, lance
        //    `new NaoAutenticado("cabecalho Authorization ausente ou fora do
        //    formato 'Bearer <token>'")`.
        // 2. `Jwt.verificar(compacto, JWKS_URL, ISSUERS_ACEITOS)` dentro de um
        //    try. Capture `Jwt.Invalido` e converta em `NaoAutenticado` com
        //    `e.getMessage()`: quem chamou precisa saber por que foi recusado.
        // 3. monte a `Identidade`, com:
        //       usuario   = jwt.texto("preferred_username")
        //       papeis    = papeisDoToken(jwt)
        //       expiraEmS = jwt.numero("exp") - jwt.numero("iat")
        //       issuer    = jwt.texto("iss")
        //
        // Erro classico a evitar: devolver 403 quando o token esta expirado
        // ou a assinatura nao confere. Isso e 401. A regra e simples: se o
        // problema esta em SABER QUEM E, e 401; se voce ja sabe quem e e o
        // problema e PERMISSAO, e 403.
        // ---------------------------------------------------------------
        Identidade quem = null; // TODO-2b e TODO-2c

        if (quem == null) {
            throw new NaoAutenticado("TODO-2 ainda nao implementado em Seguranca.java");
        }

        // ---------------------------------------------------------------
        // TODO-3c: autorizar
        //
        // Se `quem.papeis` nao tiver NENHUM dos `exigidos`, lance
        // `new SemPermissao(quem.papeis, exigidos)`. Caso contrario, devolva
        // `quem`.
        //
        // Basta UM papel em comum. Um usuario com ADMIN e CLIENTE passa numa
        // rota que aceita qualquer um dos dois.
        // ---------------------------------------------------------------
        // TODO-3c

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
