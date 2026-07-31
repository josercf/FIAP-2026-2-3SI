package br.com.fiap.logitech.pedidos.infra;

import br.com.fiap.logitech.pedidos.dominio.SolicitacaoFatura;
import br.com.fiap.logitech.pedidos.faturamento.ClienteFaturamento;
import br.com.fiap.logitech.pedidos.faturamento.FaturamentoIndisponivelException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * Implementação HTTP da porta {@link ClienteFaturamento}: fala com o serviço de
 * Faturamento em C# pela rota {@code POST /api/v1/faturas} do contrato da
 * plataforma (ADR-006).
 *
 * <p>O endereço vem de {@code LOGITECH_FATURAMENTO_URL} e nunca fica cravado
 * no código: é o que permite este mesmo binário rodar solto na sua máquina
 * hoje e dentro do Docker Compose na Aula 07.</p>
 *
 * <p>Não é tarefa: já vem pronto.</p>
 */
@Component
public class ClienteFaturamentoHttp implements ClienteFaturamento {

    private final HttpClient http;
    private final ObjectMapper json = new ObjectMapper();
    private final String urlBase;
    private final Duration tempoLimite;

    public ClienteFaturamentoHttp(@Value("${logitech.faturamento.url}") String urlBase,
                                  @Value("${logitech.faturamento.timeout-ms}") long timeoutMs) {
        this.urlBase = urlBase.endsWith("/") ? urlBase.substring(0, urlBase.length() - 1) : urlBase;
        this.tempoLimite = Duration.ofMillis(timeoutMs);
        this.http = HttpClient.newBuilder().connectTimeout(this.tempoLimite).build();
    }

    @Override
    public String emitir(SolicitacaoFatura solicitacao) {
        try {
            String corpo = json.writeValueAsString(solicitacao);
            HttpRequest requisicao = HttpRequest.newBuilder()
                    .uri(URI.create(urlBase + "/api/v1/faturas"))
                    .timeout(tempoLimite)
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(corpo))
                    .build();

            HttpResponse<String> resposta = http.send(requisicao, HttpResponse.BodyHandlers.ofString());
            if (resposta.statusCode() < 200 || resposta.statusCode() >= 300) {
                throw new FaturamentoIndisponivelException(
                        "faturamento respondeu HTTP " + resposta.statusCode() + ": " + resposta.body());
            }
            JsonNode no = json.readTree(resposta.body());
            String numero = no.path("numeroNotaFiscal").asText(null);
            if (numero == null || numero.isBlank()) {
                throw new FaturamentoIndisponivelException(
                        "faturamento respondeu sem numeroNotaFiscal: " + resposta.body());
            }
            return numero;
        } catch (InterruptedException erro) {
            Thread.currentThread().interrupt();
            throw new FaturamentoIndisponivelException("chamada ao faturamento interrompida", erro);
        } catch (FaturamentoIndisponivelException erro) {
            throw erro;
        } catch (Exception erro) {
            throw new FaturamentoIndisponivelException(
                    "não foi possível falar com o faturamento em " + urlBase, erro);
        }
    }
}
