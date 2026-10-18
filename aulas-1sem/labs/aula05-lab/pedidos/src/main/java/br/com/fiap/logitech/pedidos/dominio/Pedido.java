package br.com.fiap.logitech.pedidos.dominio;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

/**
 * Pedido de transporte da LogiTech: a carga que sai de uma origem, vai para um
 * destino e precisa ser cobrada.
 *
 * <p>Encapsulamento de verdade: os campos são privados e nenhum deles tem
 * setter público. Quem quiser mudar o estado do pedido passa por um método de
 * negócio ({@link #faturar}, {@link #alterarEndereco}), que valida a regra
 * antes de deixar o objeto em um estado novo. Um objeto com setter para tudo
 * não encapsula nada: ele é um saco de campos com sintaxe de classe.</p>
 *
 * <p>Não é tarefa: esta classe já vem pronta.</p>
 */
@Entity
@Table(name = "pedidos")
public class Pedido {

    @Id
    @Column(length = 36)
    private String id;

    @Column(nullable = false, length = 120)
    private String cliente;

    @Column(name = "tipo_cliente", nullable = false, length = 20)
    private String tipoCliente;

    @Column(nullable = false, length = 160)
    private String origem;

    @Column(nullable = false, length = 160)
    private String destino;

    @Column(name = "endereco_entrega", nullable = false, length = 240)
    private String enderecoEntrega;

    @Column(name = "peso_kg", nullable = false)
    private BigDecimal pesoKg;

    @Column(nullable = false)
    private BigDecimal valor;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private StatusPedido status;

    @Column(name = "numero_nota_fiscal", length = 30)
    private String numeroNotaFiscal;

    @Column(name = "criado_em", nullable = false)
    private OffsetDateTime criadoEm;

    /** Exigido pelo JPA. Não use no código de negócio. */
    protected Pedido() {
    }

    public Pedido(String cliente, String tipoCliente, String origem, String destino,
                  String enderecoEntrega, BigDecimal pesoKg, BigDecimal valor) {
        exigirTexto(cliente, "cliente");
        exigirTexto(tipoCliente, "tipoCliente");
        exigirTexto(origem, "origem");
        exigirTexto(destino, "destino");
        exigirTexto(enderecoEntrega, "enderecoEntrega");
        exigirPositivo(pesoKg, "pesoKg");
        exigirPositivo(valor, "valor");

        this.id = UUID.randomUUID().toString();
        this.cliente = cliente;
        this.tipoCliente = tipoCliente;
        this.origem = origem;
        this.destino = destino;
        this.enderecoEntrega = enderecoEntrega;
        this.pesoKg = pesoKg;
        this.valor = valor;
        this.status = StatusPedido.CRIADO;
        this.criadoEm = OffsetDateTime.now();
    }

    /** Marca o pedido como faturado e guarda o número da nota fiscal emitida. */
    public void faturar(String numeroNotaFiscal) {
        exigirTexto(numeroNotaFiscal, "numeroNotaFiscal");
        this.numeroNotaFiscal = numeroNotaFiscal;
        this.status = StatusPedido.FATURADO;
    }

    /** Registra que a fatura não pôde ser emitida agora e ficou pendente. */
    public void aguardarFaturamento() {
        this.status = StatusPedido.AGUARDANDO_FATURAMENTO;
    }

    /**
     * Troca o endereço de entrega. É a operação que o agente de IA da Aula 08
     * vai chamar, e por isso a regra mora aqui, e não no controlador: pedido
     * já entregue não muda de endereço, venha o pedido de onde vier.
     */
    public void alterarEndereco(String novoEndereco) {
        exigirTexto(novoEndereco, "novoEndereco");
        if (this.status == StatusPedido.ENTREGUE) {
            throw new IllegalStateException(
                    "pedido já entregue: o endereço de entrega não pode mais ser alterado");
        }
        this.enderecoEntrega = novoEndereco;
    }

    private static void exigirTexto(String valor, String campo) {
        if (valor == null || valor.isBlank()) {
            throw new IllegalArgumentException(campo + " é obrigatório");
        }
    }

    private static void exigirPositivo(BigDecimal valor, String campo) {
        if (valor == null || valor.signum() <= 0) {
            throw new IllegalArgumentException(campo + " precisa ser maior que zero");
        }
    }

    public String getId() {
        return id;
    }

    public String getCliente() {
        return cliente;
    }

    public String getTipoCliente() {
        return tipoCliente;
    }

    public String getOrigem() {
        return origem;
    }

    public String getDestino() {
        return destino;
    }

    public String getEnderecoEntrega() {
        return enderecoEntrega;
    }

    public BigDecimal getPesoKg() {
        return pesoKg;
    }

    public BigDecimal getValor() {
        return valor;
    }

    public StatusPedido getStatus() {
        return status;
    }

    public String getNumeroNotaFiscal() {
        return numeroNotaFiscal;
    }

    public OffsetDateTime getCriadoEm() {
        return criadoEm;
    }
}
