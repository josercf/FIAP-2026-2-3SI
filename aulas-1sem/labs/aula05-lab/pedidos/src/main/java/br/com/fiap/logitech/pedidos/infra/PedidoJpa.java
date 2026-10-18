package br.com.fiap.logitech.pedidos.infra;

import br.com.fiap.logitech.pedidos.dominio.Pedido;
import org.springframework.data.jpa.repository.JpaRepository;

/**
 * Interface do Spring Data JPA. Detalhe de infraestrutura: é o Hibernate que a
 * implementa em tempo de execução.
 *
 * <p>Não é tarefa. Ela nunca deve ser injetada na camada de negócio: quem a usa
 * é {@link JpaPedidoRepository}, e é ele quem vai passar a implementar a
 * abstração de domínio que você cria no TODO-1.</p>
 */
public interface PedidoJpa extends JpaRepository<Pedido, String> {
}
