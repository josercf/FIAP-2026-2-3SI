/**
 * Contratos do serviço de notificações da LogiTech.
 *
 * Este arquivo não é tarefa: é o vocabulário comum que Decorator e Adapter
 * usam. Repare que `Enviador` é uma interface pequena de propósito. Decorator
 * só funciona quando o decorador consegue se passar pelo objeto decorado, e
 * interface enxuta é o que torna isso barato.
 */

/** Uma notificação a ser entregue a um destinatário da LogiTech. */
export interface Notificacao {
  /** Canal de entrega registrado: `email`, `sms` ou `whatsapp`. */
  canal: string;
  /** Endereço, telefone ou identificador do destinatário. */
  destinatario: string;
  /** Corpo da mensagem, já pronto para envio. */
  mensagem: string;
}

/** O que o serviço devolve depois de tentar entregar uma notificação. */
export interface ResultadoEnvio {
  entregue: boolean;
  canal: string;
  /** Quantas tentativas foram necessárias. O enviador base sempre devolve 1. */
  tentativas: number;
  /** Protocolo devolvido pelo provedor do canal. */
  identificador: string;
}

/**
 * O contrato que enviadores e decoradores cumprem.
 *
 * É o mesmo papel que `EstrategiaFrete` cumpre no serviço de frete: um
 * contrato comum. A diferença é o uso. Lá o contrato serve para **trocar**
 * a implementação (Strategy); aqui ele serve para **empilhar** implementações
 * (Decorator), cada uma embrulhando a anterior.
 */
export interface Enviador {
  readonly canal: string;
  enviar(notificacao: Notificacao): Promise<ResultadoEnvio>;
}

/** Destino das linhas de log. Existe para o teste conseguir ler o log. */
export interface Registrador {
  registrar(linha: string): void;
}
