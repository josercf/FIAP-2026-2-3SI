package br.com.fiap.logitech.pedidos.web;

import br.com.fiap.logitech.pedidos.aplicacao.PedidoNaoEncontradoException;
import br.com.fiap.logitech.pedidos.aplicacao.PedidoService;
import br.com.fiap.logitech.pedidos.dominio.NovoPedido;
import br.com.fiap.logitech.pedidos.dominio.Pedido;
import br.com.fiap.logitech.pedidos.faturamento.ConectorNaoEncontradoException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

/**
 * Rotas do contexto de Pedidos, exatamente como o contrato da plataforma
 * (ADR-006) as define. A Aula 08 vai chamar {@code PATCH .../endereco} e
 * {@code GET .../status} a partir de um agente de IA: mudar caminho ou nome de
 * campo aqui quebra aquela aula.
 *
 * <p>Não é tarefa: o controlador já vem pronto e não precisa mudar por causa
 * de nenhum dos três TODOs.</p>
 */
@RestController
@RequestMapping("/api/v1/pedidos")
public class PedidoController {

    private final PedidoService servico;

    public PedidoController(PedidoService servico) {
        this.servico = servico;
    }

    @PostMapping
    public ResponseEntity<PedidoResposta> criar(@RequestBody NovoPedido novo) {
        Pedido pedido = servico.criar(novo);
        return ResponseEntity.status(HttpStatus.CREATED).body(PedidoResposta.de(pedido));
    }

    @GetMapping
    public List<PedidoResposta> listar() {
        return servico.listar().stream().map(PedidoResposta::de).toList();
    }

    @GetMapping("/{id}")
    public PedidoResposta porId(@PathVariable String id) {
        return PedidoResposta.de(servico.porId(id));
    }

    @GetMapping("/{id}/status")
    public Map<String, String> status(@PathVariable String id) {
        Pedido pedido = servico.porId(id);
        return Map.of(
                "id", pedido.getId(),
                "status", pedido.getStatus().name(),
                "destino", pedido.getDestino());
    }

    @PatchMapping("/{id}/endereco")
    public PedidoResposta alterarEndereco(@PathVariable String id,
                                          @RequestBody AlteracaoEndereco alteracao) {
        return PedidoResposta.de(servico.alterarEndereco(id, alteracao.enderecoEntrega()));
    }

    @ExceptionHandler(PedidoNaoEncontradoException.class)
    public ResponseEntity<Map<String, String>> naoEncontrado(PedidoNaoEncontradoException erro) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("erro", erro.getMessage()));
    }

    @ExceptionHandler({ConectorNaoEncontradoException.class, IllegalArgumentException.class,
            IllegalStateException.class})
    public ResponseEntity<Map<String, String>> entradaInvalida(RuntimeException erro) {
        return ResponseEntity.badRequest().body(Map.of("erro", erro.getMessage()));
    }
}
