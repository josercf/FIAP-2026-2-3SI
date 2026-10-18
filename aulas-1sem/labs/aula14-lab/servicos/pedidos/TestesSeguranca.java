// LogiTech Enterprise - suite de testes da camada de seguranca do Pedidos.
//
// CONGELADO: nao e tarefa do laboratorio, e a sua regua.
//
// Roda SEM Keycloak, sem rede externa e sem banco: o teste gera um par de
// chaves RSA na hora, sobe um JWKS de mentira em `localhost` e assina os
// proprios tokens. Em menos de um segundo voce sabe se o TODO-2 e o TODO-3
// estao certos, sem esperar container subir.
//
// Rodar, com o servico ja construido:
//     docker compose up -d --build pedidos
//     docker compose exec pedidos java -cp /app/classes TestesSeguranca
//
// Ou, com um JDK 21 na maquina:
//     javac -d /tmp/aula14 servicos/pedidos/*.java && java -cp /tmp/aula14 TestesSeguranca
//
// Saida: "N de N testes passaram" e codigo de saida 0, ou a lista do que
// falhou e codigo 1.

import com.sun.net.httpserver.HttpServer;

import java.math.BigInteger;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.PrivateKey;
import java.security.Signature;
import java.security.interfaces.RSAPublicKey;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class TestesSeguranca {

    static final Base64.Encoder B64 = Base64.getUrlEncoder().withoutPadding();
    static final String EMISSOR = "http://localhost:8090/realms/logitech";
    static final String KID = "chave-de-teste-1";

    static KeyPair par;
    static final List<String> FALHAS = new ArrayList<>();
    static int total = 0;

    public static void main(String[] args) throws Exception {
        par = gerar();

        HttpServer jwks = subirJwksDeMentira();
        int porta = jwks.getAddress().getPort();

        Seguranca.ATIVA = true;
        Seguranca.JWKS_URL = "http://127.0.0.1:" + porta + "/certs";
        Seguranca.ISSUERS_ACEITOS = EMISSOR;
        Jwt.esquecerChaves();

        try {
            testarExtracaoDoCabecalho();
            testarTabelaDeRegras();
            testarPapeisVemDoRealmAccess();
            testarSemToken();
            testarTokenAdulterado();
            testarTokenExpirado();
            testarIssuerDivergente();
            testarPapelCerto();
            testarPapelErrado();
            testarSaudeSempreAberta();
            testarInterruptorDesligado();
        } finally {
            jwks.stop(0);
        }

        System.out.println();
        if (FALHAS.isEmpty()) {
            System.out.println("OK: " + total + " de " + total + " testes passaram.");
            System.exit(0);
        }
        System.out.println((total - FALHAS.size()) + " de " + total + " testes passaram. Faltam:");
        for (String f : FALHAS) System.out.println("  - " + f);
        System.exit(1);
    }

    static KeyPair gerar() throws Exception {
        KeyPairGenerator g = KeyPairGenerator.getInstance("RSA");
        g.initialize(2048);
        return g.generateKeyPair();
    }

    // -----------------------------------------------------------------
    // Os testes
    // -----------------------------------------------------------------

    static void testarExtracaoDoCabecalho() {
        confere("TODO-2a: 'Bearer abc' devolve o token",
                "abc".equals(Seguranca.extrairBearer("Bearer abc")));
        confere("TODO-2a: esquema em minusculas tambem vale (RFC 7235)",
                "abc".equals(Seguranca.extrairBearer("bearer abc")));
        confere("TODO-2a: cabecalho ausente devolve null",
                Seguranca.extrairBearer(null) == null);
        confere("TODO-2a: 'Basic dXNlcjpzZW5oYQ==' nao e Bearer, devolve null",
                Seguranca.extrairBearer("Basic dXNlcjpzZW5oYQ==") == null);
        confere("TODO-2a: 'Bearer' sem token devolve null",
                Seguranca.extrairBearer("Bearer") == null
                && Seguranca.extrairBearer("Bearer   ") == null);
    }

    static void testarTabelaDeRegras() {
        confere("TODO-3a: GET /health continua aberta",
                Seguranca.papeisExigidos("GET", "/health").isEmpty());
        confere("TODO-3a: GET /api/v1/pedidos aceita os tres papeis",
                Set.copyOf(Seguranca.papeisExigidos("GET", "/api/v1/pedidos"))
                   .equals(Set.of("CLIENTE", "MOTORISTA", "ADMIN")));
        confere("TODO-3a: POST /api/v1/pedidos aceita CLIENTE e ADMIN, e so",
                Set.copyOf(Seguranca.papeisExigidos("POST", "/api/v1/pedidos"))
                   .equals(Set.of("CLIENTE", "ADMIN")));
        confere("TODO-3a: PATCH .../endereco aceita CLIENTE e ADMIN",
                Set.copyOf(Seguranca.papeisExigidos("PATCH", "/api/v1/pedidos/PED-1042/endereco"))
                   .equals(Set.of("CLIENTE", "ADMIN")));
        confere("TODO-3a: GET .../status aceita qualquer papel",
                Set.copyOf(Seguranca.papeisExigidos("GET", "/api/v1/pedidos/PED-1042/status"))
                   .equals(Set.of("CLIENTE", "MOTORISTA", "ADMIN")));
        confere("TODO-3a: GET /api/v1/pedidos/{id} exige papel, e o regex do id "
                + "nao engole o /status nem o /endereco",
                !Seguranca.papeisExigidos("GET", "/api/v1/pedidos/PED-1042").isEmpty());
    }

    static void testarPapeisVemDoRealmAccess() throws Exception {
        Jwt jwt = Jwt.verificar(token("carla.admin", List.of("ADMIN"), EMISSOR, 300),
                                Seguranca.JWKS_URL, Seguranca.ISSUERS_ACEITOS);
        confere("TODO-3b: papeis lidos de realm_access.roles",
                Seguranca.papeisDoToken(jwt).equals(Set.of("ADMIN")));

        // Este e o teste que separa quem leu a ADR-009 de quem copiou um
        // tutorial: o mesmo token traz `resource_access` com um papel
        // DIFERENTE, que nao deve aparecer aqui.
        Jwt outro = Jwt.verificar(tokenComResourceAccess(), Seguranca.JWKS_URL, Seguranca.ISSUERS_ACEITOS);
        confere("TODO-3b: papel de resource_access NAO conta como papel de realm",
                Seguranca.papeisDoToken(outro).equals(Set.of("CLIENTE")));

        Jwt semPapel = Jwt.verificar(token("ninguem", List.of(), EMISSOR, 300),
                                     Seguranca.JWKS_URL, Seguranca.ISSUERS_ACEITOS);
        confere("TODO-3b: token sem papel devolve conjunto vazio, nao explode",
                Seguranca.papeisDoToken(semPapel).isEmpty());
    }

    static void testarSemToken() {
        confere("TODO-2b: sem cabecalho Authorization e 401, nao 403",
                lanca401(() -> Seguranca.guarda("GET", "/api/v1/pedidos", null)));
        confere("TODO-2b: cabecalho fora do formato tambem e 401",
                lanca401(() -> Seguranca.guarda("GET", "/api/v1/pedidos", "Bearer")));
    }

    static void testarTokenAdulterado() throws Exception {
        String bom = token("ana.cliente", List.of("CLIENTE"), EMISSOR, 300);
        String[] p = bom.split("\\.");
        // Troca o payload por um que se diz ADMIN, mantendo a assinatura.
        String forjado = p[0] + "." + B64.encodeToString(
                corpo("ana.cliente", List.of("ADMIN"), EMISSOR, 300).getBytes(StandardCharsets.UTF_8))
                + "." + p[2];
        confere("TODO-2b: payload trocado com a assinatura antiga e 401",
                lanca401(() -> Seguranca.guarda("POST", "/api/v1/pedidos", "Bearer " + forjado)));
    }

    static void testarTokenExpirado() throws Exception {
        String vencido = token("ana.cliente", List.of("CLIENTE"), EMISSOR, -600);
        confere("TODO-2b: token expirado e 401 (nao 403: o problema e saber quem e)",
                lanca401(() -> Seguranca.guarda("GET", "/api/v1/pedidos", "Bearer " + vencido)));
    }

    static void testarIssuerDivergente() throws Exception {
        String deOutroEndereco = token("ana.cliente", List.of("CLIENTE"),
                                       "http://keycloak:8090/realms/logitech", 300);
        confere("TODO-2b: token com issuer fora da lista e 401",
                lanca401(() -> Seguranca.guarda("GET", "/api/v1/pedidos", "Bearer " + deOutroEndereco)));

        // E agora com os dois endereços aceitos, que e o conserto do slide.
        String antes = Seguranca.ISSUERS_ACEITOS;
        Seguranca.ISSUERS_ACEITOS = EMISSOR + ",http://keycloak:8090/realms/logitech";
        boolean passou = true;
        try {
            Seguranca.guarda("GET", "/api/v1/pedidos", "Bearer " + deOutroEndereco);
        } catch (RuntimeException e) {
            passou = false;
        }
        Seguranca.ISSUERS_ACEITOS = antes;
        confere("TODO-2b: com os DOIS issuers na lista, o mesmo token passa", passou);
    }

    static void testarPapelCerto() throws Exception {
        String t = token("carla.admin", List.of("ADMIN"), EMISSOR, 300);
        Seguranca.Identidade quem = Seguranca.guarda("POST", "/api/v1/pedidos", "Bearer " + t);
        confere("TODO-3c: ADMIN passa no POST /api/v1/pedidos",
                quem != null && "carla.admin".equals(quem.usuario));
        confere("TODO-2c: a Identidade traz a validade lida do proprio token",
                quem != null && quem.expiraEmS == 300);
    }

    static void testarPapelErrado() throws Exception {
        String t = token("bruno.motorista", List.of("MOTORISTA"), EMISSOR, 300);
        confere("TODO-3c: MOTORISTA no POST /api/v1/pedidos e 403, nao 401",
                lanca403(() -> Seguranca.guarda("POST", "/api/v1/pedidos", "Bearer " + t)));
        confere("TODO-3c: o mesmo MOTORISTA passa no GET /api/v1/pedidos",
                naoLanca(() -> Seguranca.guarda("GET", "/api/v1/pedidos", "Bearer " + t)));
    }

    static void testarSaudeSempreAberta() {
        confere("TODO-3a: GET /health responde sem token nenhum",
                naoLanca(() -> Seguranca.guarda("GET", "/health", null)));
    }

    static void testarInterruptorDesligado() {
        Seguranca.ATIVA = false;
        boolean solto = naoLanca(() -> Seguranca.guarda("POST", "/api/v1/pedidos", null));
        Seguranca.ATIVA = true;
        confere("LOGITECH_AUTH_ATIVA=false devolve o comportamento das Aulas 05 a 12", solto);
    }

    // -----------------------------------------------------------------
    // Ferramenta: um Keycloak de mentira
    // -----------------------------------------------------------------

    static HttpServer subirJwksDeMentira() throws Exception {
        RSAPublicKey pub = (RSAPublicKey) par.getPublic();
        String n = B64.encodeToString(semSinal(pub.getModulus()));
        String e = B64.encodeToString(semSinal(pub.getPublicExponent()));
        String doc = "{\"keys\":[{\"kid\":\"" + KID + "\",\"kty\":\"RSA\",\"alg\":\"RS256\","
                     + "\"use\":\"sig\",\"n\":\"" + n + "\",\"e\":\"" + e + "\"}]}";

        HttpServer s = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        s.createContext("/certs", troca -> {
            byte[] b = doc.getBytes(StandardCharsets.UTF_8);
            troca.getResponseHeaders().add("Content-Type", "application/json");
            troca.sendResponseHeaders(200, b.length);
            troca.getResponseBody().write(b);
            troca.close();
        });
        s.start();
        return s;
    }

    /** BigInteger.toByteArray pode devolver um zero a esquerda, que o JWK nao tem. */
    static byte[] semSinal(BigInteger v) {
        byte[] b = v.toByteArray();
        if (b.length > 1 && b[0] == 0) {
            byte[] r = new byte[b.length - 1];
            System.arraycopy(b, 1, r, 0, r.length);
            return r;
        }
        return b;
    }

    static String corpo(String usuario, List<String> papeis, String emissor, long validadeS) {
        long agora = Instant.now().getEpochSecond();
        Map<String, Object> realm = new LinkedHashMap<>();
        realm.put("roles", papeis);
        Map<String, Object> c = new LinkedHashMap<>();
        c.put("iss", emissor);
        c.put("sub", "00000000-0000-0000-0000-0000000000aa");
        c.put("azp", "logitech-portal");
        c.put("typ", "Bearer");
        c.put("preferred_username", usuario);
        c.put("iat", agora);
        c.put("exp", agora + validadeS);
        c.put("realm_access", realm);
        return Json.escrever(c);
    }

    static String token(String usuario, List<String> papeis, String emissor, long validadeS)
            throws Exception {
        return assinar("{\"alg\":\"RS256\",\"typ\":\"JWT\",\"kid\":\"" + KID + "\"}",
                       corpo(usuario, papeis, emissor, validadeS));
    }

    static String tokenComResourceAccess() throws Exception {
        long agora = Instant.now().getEpochSecond();
        Map<String, Object> c = new LinkedHashMap<>();
        c.put("iss", EMISSOR);
        c.put("preferred_username", "ana.cliente");
        c.put("iat", agora);
        c.put("exp", agora + 300);
        c.put("realm_access", Map.of("roles", List.of("CLIENTE")));
        c.put("resource_access", Map.of("logitech-portal", Map.of("roles", List.of("ADMIN"))));
        return assinar("{\"alg\":\"RS256\",\"typ\":\"JWT\",\"kid\":\"" + KID + "\"}", Json.escrever(c));
    }

    static String assinar(String cabecalho, String conteudo) throws Exception {
        String base = B64.encodeToString(cabecalho.getBytes(StandardCharsets.UTF_8)) + "."
                    + B64.encodeToString(conteudo.getBytes(StandardCharsets.UTF_8));
        Signature s = Signature.getInstance("SHA256withRSA");
        s.initSign((PrivateKey) par.getPrivate());
        s.update(base.getBytes(StandardCharsets.US_ASCII));
        return base + "." + B64.encodeToString(s.sign());
    }

    // -----------------------------------------------------------------
    // Micro-arcabouco de teste
    // -----------------------------------------------------------------

    interface Bloco { void executar(); }

    static boolean lanca401(Bloco b) {
        try { b.executar(); return false; }
        catch (Seguranca.NaoAutenticado e) { return true; }
        catch (RuntimeException e) { return false; }
    }

    static boolean lanca403(Bloco b) {
        try { b.executar(); return false; }
        catch (Seguranca.SemPermissao e) { return true; }
        catch (RuntimeException e) { return false; }
    }

    static boolean naoLanca(Bloco b) {
        try { b.executar(); return true; }
        catch (RuntimeException e) { return false; }
    }

    static void confere(String nome, boolean passou) {
        total++;
        System.out.println((passou ? "  ok   " : "  FALHA") + "  " + nome);
        if (!passou) FALHAS.add(nome);
    }
}
