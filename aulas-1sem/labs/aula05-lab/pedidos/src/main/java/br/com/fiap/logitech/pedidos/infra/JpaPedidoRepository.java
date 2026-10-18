package br.com.fiap.logitech.pedidos.infra;

import br.com.fiap.logitech.pedidos.dominio.Pedido;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Persistência de pedidos em PostgreSQL, via JPA/Hibernate.
 *
 * <p><strong>TODO-1 (DIP):</strong> esta classe é a implementação concreta, e é
 * ela que precisa mudar. Hoje {@code PedidoService} depende deste tipo
 * diretamente, ou seja, a regra de negócio conhece o ORM. Faça esta classe
 * implementar a interface {@code PedidoRepository} que você vai criar no
 * pacote {@code dominio}, sem mudar o corpo de nenhum método.</p>
 *
 * <p>Os métodos são {@code public} e não são {@code final} de propósito: é o
 * que permite, hoje, o dublê de teste herdar desta classe. Depois do TODO-1
 * esse truque some, e é justamente esse o ponto.</p>
 */
@Repository
public class JpaPedidoRepository {

    private final PedidoJpa jpa;

    public JpaPedidoRepository(PedidoJpa jpa) {
        this.jpa = jpa;
    }

    public Pedido salvar(Pedido pedido) {
        return jpa.save(pedido);
    }

    public Optional<Pedido> porId(String id) {
        return jpa.findById(id);
    }

    public List<Pedido> todos() {
        return jpa.findAll();
    }
}
