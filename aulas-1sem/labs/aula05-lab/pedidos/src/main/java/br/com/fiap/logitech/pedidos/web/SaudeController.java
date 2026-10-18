package br.com.fiap.logitech.pedidos.web;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * {@code GET /health} devolvendo {@code 200} e {@code {"status":"ok"}}.
 *
 * <p>Obrigatório pelo contrato da plataforma (ADR-006): é neste endereço que o
 * {@code healthcheck} do Docker Compose da Aula 07 vai bater antes de deixar
 * outro serviço subir. Não é tarefa.</p>
 */
@RestController
public class SaudeController {

    @GetMapping("/health")
    public Map<String, String> saude() {
        return Map.of("status", "ok", "servico", "pedidos");
    }
}
