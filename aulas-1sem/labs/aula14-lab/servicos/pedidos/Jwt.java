// LogiTech Enterprise - verificador de JWT assinado em RS256, contra o JWKS.
//
// CONGELADO: nao e tarefa do laboratorio. Mas LEIA, porque este arquivo e a
// resposta da Pergunta de Verificacao 1 escrita em codigo que roda.
//
// O que ele faz, em ordem:
//
//   1. parte o token nos tres pedacos separados por ponto;
//   2. le o cabecalho e recusa qualquer coisa que nao seja alg=RS256;
//   3. pega o `kid` do cabecalho e procura a chave publica correspondente no
//      JWKS do Keycloak, baixado uma vez e guardado em memoria;
//   4. confere a assinatura de `cabecalho.payload` com essa chave publica;
//   5. so entao olha o conteudo: `exp`, `nbf` e `iss`.
//
// A ordem importa e nao e detalhe de implementacao: enquanto a assinatura
// nao for conferida, TODO campo do payload e texto que o cliente mandou.
// Ler `realm_access.roles` antes de verificar a assinatura seria o mesmo que
// perguntar ao visitante se ele e o gerente.
//
// Duas recusas que este arquivo faz de proposito e que quase todo tutorial
// esquece:
//
//   - `alg: none`. O JWT permite um token sem assinatura. Uma biblioteca que
//     obedece o campo `alg` do proprio token aceita um token forjado com a
//     assinatura vazia. Aqui o algoritmo aceito e decidido pelo SERVIDOR, e
//     o campo `alg` do token so serve para ser conferido.
//   - `alg: HS256` com a chave publica do JWKS usada como segredo. E o
//     ataque de confusao de algoritmo: o atacante pega a chave publica, que
//     e publica mesmo, e assina um token HMAC com ela. Se o servidor decidir
//     o algoritmo pelo token, ele valida.

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.Signature;
import java.security.spec.RSAPublicKeySpec;
import java.time.Instant;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class Jwt {

    /** Recusa de token, com um motivo legivel. Sempre vira 401. */
    public static class Invalido extends RuntimeException {
        public Invalido(String motivo) { super(motivo); }
    }

    private static final Base64.Decoder B64 = Base64.getUrlDecoder();

    /** Cache de chaves publicas por `kid`. O JWKS e baixado uma vez. */
    private static final Map<String, PublicKey> CHAVES = new HashMap<>();
    private static volatile long ultimaBusca = 0L;

    /** Segundos de tolerancia para relogio fora de sincronia entre maquinas. */
    private static final long FOLGA_DE_RELOGIO_S = 30;

    private final Map<String, Object> cabecalho;
    private final Map<String, Object> conteudo;

    private Jwt(Map<String, Object> cabecalho, Map<String, Object> conteudo) {
        this.cabecalho = cabecalho;
        this.conteudo = conteudo;
    }

    public Map<String, Object> conteudo() { return conteudo; }
    public Map<String, Object> cabecalho() { return cabecalho; }

    public String texto(String campo) {
        Object v = conteudo.get(campo);
        return v == null ? null : String.valueOf(v);
    }

    public long numero(String campo) {
        Object v = conteudo.get(campo);
        return v == null ? 0L : (long) Double.parseDouble(String.valueOf(v));
    }

    // -----------------------------------------------------------------
    // A verificacao
    // -----------------------------------------------------------------

    /**
     * Verifica um token compacto e devolve o conteudo ja conferido.
     *
     * @param compacto      o token como veio no cabecalho Authorization
     * @param jwksUrl       de onde baixar as chaves publicas
     * @param issuersAceitos lista de emissores confiaveis, separados por virgula
     * @throws Invalido em qualquer recusa, com o motivo em getMessage()
     */
    public static Jwt verificar(String compacto, String jwksUrl, String issuersAceitos) {
        String[] partes = compacto.split("\\.");
        if (partes.length != 3) {
            throw new Invalido("formato: um JWT tem tres partes separadas por ponto, vieram "
                               + partes.length);
        }

        Map<String, Object> cab;
        Map<String, Object> corpo;
        try {
            cab = Json.lerObjeto(new String(B64.decode(partes[0]), StandardCharsets.UTF_8));
            corpo = Json.lerObjeto(new String(B64.decode(partes[1]), StandardCharsets.UTF_8));
        } catch (RuntimeException e) {
            throw new Invalido("cabecalho ou payload nao sao base64url de JSON valido");
        }

        // 1. O algoritmo quem decide e o servidor, nao o token.
        String alg = String.valueOf(cab.get("alg"));
        if (!"RS256".equals(alg)) {
            throw new Invalido("algoritmo '" + alg + "' recusado: este servico so aceita RS256. "
                               + "Aceitar o que o token pede e como perguntar ao visitante se ele e o gerente.");
        }

        String kid = cab.get("kid") == null ? null : String.valueOf(cab.get("kid"));
        if (kid == null) {
            throw new Invalido("cabecalho sem 'kid': nao da para saber qual chave publica usar");
        }

        // 2. A chave publica correspondente ao kid.
        PublicKey chave = chavePorKid(kid, jwksUrl);
        if (chave == null) {
            throw new Invalido("kid '" + kid + "' nao existe no JWKS de " + jwksUrl
                               + ". O Keycloak foi recriado e girou a chave? Reinicie este servico ou espere o cache expirar.");
        }

        // 3. A assinatura. Antes disto, o payload e so texto do cliente.
        byte[] assinado = (partes[0] + "." + partes[1]).getBytes(StandardCharsets.US_ASCII);
        boolean confere;
        try {
            Signature s = Signature.getInstance("SHA256withRSA");
            s.initVerify(chave);
            s.update(assinado);
            confere = s.verify(B64.decode(partes[2]));
        } catch (Exception e) {
            throw new Invalido("nao foi possivel conferir a assinatura: " + e.getMessage());
        }
        if (!confere) {
            throw new Invalido("assinatura invalida: o token foi adulterado ou nao veio deste realm");
        }

        // 4. So agora o conteudo vale alguma coisa.
        long agora = Instant.now().getEpochSecond();
        Jwt jwt = new Jwt(cab, corpo);

        long exp = jwt.numero("exp");
        if (exp > 0 && agora > exp + FOLGA_DE_RELOGIO_S) {
            throw new Invalido("token expirado ha " + (agora - exp) + "s. Faca login de novo.");
        }
        long nbf = jwt.numero("nbf");
        if (nbf > 0 && agora + FOLGA_DE_RELOGIO_S < nbf) {
            throw new Invalido("token ainda nao vale (nbf no futuro)");
        }

        String iss = jwt.texto("iss");
        boolean confiavel = false;
        for (String aceito : issuersAceitos.split(",")) {
            if (aceito.trim().equals(iss)) { confiavel = true; break; }
        }
        if (!confiavel) {
            // Esta mensagem existe porque a mensagem padrao das bibliotecas
            // reais nesta situacao e pessima. Ver o slide do issuer divergente.
            throw new Invalido("issuer '" + iss + "' nao esta na lista de confiaveis ["
                               + issuersAceitos + "]. O token foi emitido por um endereco "
                               + "do Keycloak que este servico nao conhece.");
        }

        return jwt;
    }

    // -----------------------------------------------------------------
    // JWKS
    // -----------------------------------------------------------------

    private static synchronized PublicKey chavePorKid(String kid, String jwksUrl) {
        PublicKey k = CHAVES.get(kid);
        if (k != null) return k;

        // Sem cache para este kid. Pode ser a primeira chamada, ou o Keycloak
        // pode ter girado a chave. Rebaixar no maximo uma vez por minuto, para
        // um token forjado com kid aleatorio nao virar uma enxurrada de
        // requisicoes ao provedor de identidade.
        long agora = System.currentTimeMillis();
        if (agora - ultimaBusca < 60_000L) return null;
        ultimaBusca = agora;

        try {
            CHAVES.putAll(baixarJwks(jwksUrl));
        } catch (IOException e) {
            throw new Invalido("nao foi possivel baixar o JWKS de " + jwksUrl + ": " + e.getMessage());
        }
        return CHAVES.get(kid);
    }

    @SuppressWarnings("unchecked")
    static Map<String, PublicKey> baixarJwks(String jwksUrl) throws IOException {
        HttpURLConnection c = (HttpURLConnection) URI.create(jwksUrl).toURL().openConnection();
        c.setConnectTimeout(4000);
        c.setReadTimeout(4000);
        String corpo;
        try (InputStream in = c.getInputStream()) {
            corpo = new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }

        Map<String, Object> doc = Json.lerObjeto(corpo);
        Map<String, PublicKey> achadas = new HashMap<>();
        for (Object o : (List<Object>) doc.get("keys")) {
            Map<String, Object> jwk = (Map<String, Object>) o;
            if (!"RSA".equals(jwk.get("kty"))) continue;
            // O Keycloak publica no mesmo JWKS a chave de assinatura (sig) e a
            // de criptografia (enc). So a de assinatura serve aqui.
            if (jwk.get("use") != null && !"sig".equals(jwk.get("use"))) continue;
            try {
                BigInteger n = new BigInteger(1, B64.decode(String.valueOf(jwk.get("n"))));
                BigInteger e = new BigInteger(1, B64.decode(String.valueOf(jwk.get("e"))));
                PublicKey pk = KeyFactory.getInstance("RSA")
                        .generatePublic(new RSAPublicKeySpec(n, e));
                achadas.put(String.valueOf(jwk.get("kid")), pk);
            } catch (Exception ignorada) {
                // Uma chave ilegivel no JWKS nao pode derrubar as outras.
            }
        }
        return achadas;
    }

    /** So para o teste: limpa o cache de chaves. */
    static void esquecerChaves() {
        synchronized (Jwt.class) {
            CHAVES.clear();
            ultimaBusca = 0L;
        }
    }
}
