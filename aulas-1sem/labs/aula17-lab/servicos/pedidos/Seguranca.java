// LogiTech Enterprise - validação de JWT por JWKS, só com a JDK.
//
// O mesmo contrato que o `seguranca.py` dos serviços Python cumpre, escrito na
// linguagem daqui. Nada de biblioteca externa: `java.security` já sabe
// verificar RSA com SHA-256, e o único artefato que o build baixa continua
// sendo o driver JDBC.
//
// Contrato (ADR-009):
//
//     LOGITECH_AUTH_ATIVA       false por padrão; a Aula 14 liga
//     LOGITECH_OIDC_ISSUER      o `iss` que o token precisa trazer
//     LOGITECH_OIDC_JWKS_URL    de onde as chaves públicas são lidas
//
// O papel viaja em `realm_access.roles`. É de lá que este serviço lê, e é de
// lá que o serviço em C#, o em Python e o em Node também leem. Fixar o lugar
// é o ponto central da ADR-009: metade dos exemplos da internet lê de
// `resource_access.<client>.roles`, e aí o mesmo token autoriza numa stack e
// é recusado na outra.
//
// Não é tarefa. Este arquivo vem pronto.

import java.io.IOException;
import java.math.BigInteger;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.Signature;
import java.security.spec.RSAPublicKeySpec;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public final class Seguranca {

    /** Token ausente, malformado, expirado ou com assinatura inválida: 401. */
    public static class ErroDeToken extends Exception {
        public ErroDeToken(String mensagem) { super(mensagem); }
    }

    /** Token válido, mas sem o papel que a rota exige: 403. */
    public static class ErroDePapel extends Exception {
        public ErroDePapel(String mensagem) { super(mensagem); }
    }

    private static final HttpClient HTTP = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();

    private static final Map<String, PublicKey> CHAVES = new HashMap<>();
    private static Instant chavesLidasEm = Instant.EPOCH;
    private static final Duration VALIDADE_DO_CACHE = Duration.ofMinutes(5);

    private Seguranca() { }

    private static String env(String nome, String padrao) {
        String valor = System.getenv(nome);
        return (valor == null || valor.isBlank()) ? padrao : valor;
    }

    /** A autenticação só entra em vigor com LOGITECH_AUTH_ATIVA ligada. */
    public static boolean ativa() {
        String valor = env("LOGITECH_AUTH_ATIVA", "false").trim().toLowerCase();
        return valor.equals("1") || valor.equals("true") || valor.equals("sim") || valor.equals("on");
    }

    private static byte[] b64url(String dado) {
        return Base64.getUrlDecoder().decode(dado);
    }

    // -----------------------------------------------------------------
    // JWKS: as chaves públicas do provedor de identidade
    // -----------------------------------------------------------------

    /**
     * O cache de cinco minutos é o motivo de o backend não consultar o
     * Keycloak a cada requisição. A chave pública muda raramente, o token traz
     * o `kid` que diz qual usar, e a validação acontece dentro deste processo.
     */
    private static synchronized void carregarChaves(boolean forcar) throws ErroDeToken {
        if (!forcar && !CHAVES.isEmpty()
                && Duration.between(chavesLidasEm, Instant.now()).compareTo(VALIDADE_DO_CACHE) < 0) {
            return;
        }
        String url = env("LOGITECH_OIDC_JWKS_URL", "");
        if (url.isBlank()) {
            throw new ErroDeToken("LOGITECH_OIDC_JWKS_URL não configurada");
        }
        try {
            HttpResponse<String> resposta = HTTP.send(
                    HttpRequest.newBuilder(URI.create(url))
                            .timeout(Duration.ofSeconds(5)).GET().build(),
                    HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            if (resposta.statusCode() != 200) {
                throw new ErroDeToken("o JWKS respondeu " + resposta.statusCode());
            }
            CHAVES.clear();
            for (String bloco : blocosDeChave(resposta.body())) {
                String kid = campoTexto(bloco, "kid");
                String n = campoTexto(bloco, "n");
                String e = campoTexto(bloco, "e");
                if (kid == null || n == null || e == null) continue;
                RSAPublicKeySpec spec = new RSAPublicKeySpec(
                        new BigInteger(1, b64url(n)), new BigInteger(1, b64url(e)));
                CHAVES.put(kid, KeyFactory.getInstance("RSA").generatePublic(spec));
            }
            if (CHAVES.isEmpty()) throw new ErroDeToken("o JWKS não trouxe nenhuma chave RSA");
            chavesLidasEm = Instant.now();
        } catch (ErroDeToken erro) {
            throw erro;
        } catch (IOException | InterruptedException erro) {
            throw new ErroDeToken("não foi possível ler o JWKS: " + erro.getMessage());
        } catch (Exception erro) {
            throw new ErroDeToken("JWKS inválido: " + erro.getMessage());
        }
    }

    /**
     * Recorte grosseiro do array `keys` do JWKS. Este serviço não tem parser
     * de JSON, e escrever um completo aqui seria conteúdo de outra aula: o
     * documento do Keycloak é previsível e um recorte por chaves resolve.
     */
    private static java.util.List<String> blocosDeChave(String json) {
        java.util.List<String> blocos = new java.util.ArrayList<>();
        int i = json.indexOf("\"keys\"");
        if (i < 0) return blocos;
        int profundidade = 0, inicio = -1;
        for (int p = i; p < json.length(); p++) {
            char c = json.charAt(p);
            if (c == '{') { if (profundidade == 0) inicio = p; profundidade++; }
            else if (c == '}') {
                profundidade--;
                if (profundidade == 0 && inicio >= 0) { blocos.add(json.substring(inicio, p + 1)); inicio = -1; }
            } else if (c == ']' && profundidade == 0) break;
        }
        return blocos;
    }

    private static String campoTexto(String json, String campo) {
        String alvo = "\"" + campo + "\"";
        int i = json.indexOf(alvo);
        if (i < 0) return null;
        int aspas = json.indexOf('"', json.indexOf(':', i) + 1);
        if (aspas < 0) return null;
        int fim = json.indexOf('"', aspas + 1);
        return fim < 0 ? null : json.substring(aspas + 1, fim);
    }

    // -----------------------------------------------------------------
    // Validação
    // -----------------------------------------------------------------

    /** Valida `Authorization: Bearer <token>` e devolve o payload cru. */
    public static String validar(String cabecalhoAuthorization) throws ErroDeToken {
        if (cabecalhoAuthorization == null
                || !cabecalhoAuthorization.toLowerCase().startsWith("bearer ")) {
            throw new ErroDeToken("cabeçalho Authorization ausente ou sem o esquema Bearer");
        }
        String token = cabecalhoAuthorization.substring(7).trim();
        String[] partes = token.split("\\.");
        if (partes.length != 3) throw new ErroDeToken("o token não tem as três partes de um JWT");

        String cabecalho = new String(b64url(partes[0]), StandardCharsets.UTF_8);
        String payload = new String(b64url(partes[1]), StandardCharsets.UTF_8);

        if (!"RS256".equals(campoTexto(cabecalho, "alg"))) {
            throw new ErroDeToken("algoritmo recusado: este serviço só aceita RS256");
        }
        String kid = campoTexto(cabecalho, "kid");

        carregarChaves(false);
        PublicKey chave = CHAVES.get(kid);
        if (chave == null) {                 // kid novo: o provedor girou a chave
            carregarChaves(true);
            chave = CHAVES.get(kid);
        }
        if (chave == null) throw new ErroDeToken("kid " + kid + " não está no JWKS");

        try {
            Signature verificador = Signature.getInstance("SHA256withRSA");
            verificador.initVerify(chave);
            verificador.update((partes[0] + "." + partes[1]).getBytes(StandardCharsets.US_ASCII));
            if (!verificador.verify(b64url(partes[2]))) {
                throw new ErroDeToken("assinatura inválida");
            }
        } catch (ErroDeToken erro) {
            throw erro;
        } catch (Exception erro) {
            throw new ErroDeToken("falha ao verificar a assinatura: " + erro.getMessage());
        }

        long agora = Instant.now().getEpochSecond();
        long exp = campoNumero(payload, "exp");
        if (exp > 0 && exp < agora) throw new ErroDeToken("token expirado");

        String issuerEsperado = env("LOGITECH_OIDC_ISSUER", "");
        String issuerDoToken = campoTexto(payload, "iss");
        if (!issuerEsperado.isBlank() && !issuerEsperado.equals(issuerDoToken)) {
            // O erro que mais custou tempo na construção do acervo: o `iss`
            // que o Keycloak grava é o endereço pelo qual o NAVEGADOR chegou
            // (`localhost:8090`), e o endereço pelo qual este serviço busca o
            // JWKS é o da rede interna (`keycloak:8090`). São dois valores
            // diferentes, e é por isso que existem duas variáveis.
            throw new ErroDeToken("issuer divergente: o token traz " + issuerDoToken
                    + " e este serviço espera " + issuerEsperado);
        }
        return payload;
    }

    private static long campoNumero(String json, String campo) {
        String alvo = "\"" + campo + "\"";
        int i = json.indexOf(alvo);
        if (i < 0) return 0;
        int p = json.indexOf(':', i) + 1;
        StringBuilder numero = new StringBuilder();
        while (p < json.length() && (Character.isDigit(json.charAt(p)) || json.charAt(p) == ' ')) {
            if (json.charAt(p) != ' ') numero.append(json.charAt(p));
            p++;
        }
        return numero.length() == 0 ? 0 : Long.parseLong(numero.toString());
    }

    /** Papéis lidos de `realm_access.roles`, e de nenhum outro lugar. */
    public static Set<String> papeis(String payload) {
        Set<String> encontrados = new HashSet<>();
        int i = payload.indexOf("\"realm_access\"");
        if (i < 0) return encontrados;
        int abre = payload.indexOf('[', i);
        int fecha = payload.indexOf(']', abre);
        if (abre < 0 || fecha < 0) return encontrados;
        for (String bruto : payload.substring(abre + 1, fecha).split(",")) {
            String papel = bruto.trim().replace("\"", "").toUpperCase();
            if (!papel.isEmpty()) encontrados.add(papel);
        }
        return encontrados;
    }

    /**
     * Valida o token e confere o papel.
     *
     * Sem token: ErroDeToken, que vira 401.
     * Token bom e papel errado: ErroDePapel, que vira 403.
     */
    public static String exigir(String cabecalhoAuthorization, String... aceitos)
            throws ErroDeToken, ErroDePapel {
        String payload = validar(cabecalhoAuthorization);
        if (aceitos.length == 0) return payload;
        Set<String> tenho = papeis(payload);
        for (String aceito : aceitos) {
            if (tenho.contains(aceito.toUpperCase())) return payload;
        }
        throw new ErroDePapel("este token tem " + tenho + " e a rota exige um de "
                + String.join(", ", aceitos));
    }
}
