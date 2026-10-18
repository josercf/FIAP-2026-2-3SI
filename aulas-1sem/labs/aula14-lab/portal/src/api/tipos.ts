/**
 * O contrato da plataforma LogiTech, escrito em TypeScript.
 *
 * CONGELADO. Não é tarefa da Aula 14.
 *
 * Os nomes dos campos são os da ADR-006 e não se traduzem: `pedidoId` chega
 * assim do serviço Java e fica assim aqui. Traduzir nome de campo na borda é
 * a origem clássica do defeito que ninguém acha, porque o TypeScript some em
 * tempo de execução e o JSON não avisa nada.
 */

export interface EnderecoEntrega {
  logradouro: string;
  numero: string;
  complemento?: string;
  cidade: string;
  uf: string;
  cep: string;
}

/** Um pedido, como `GET /api/v1/pedidos/{id}` devolve. */
export interface Pedido {
  pedidoId: string;
  cliente: string;
  status: string;
  transportadora: string;
  previsaoEntrega: string;
  ultimaPosicao: string;
  atualizadoEm: string;
  enderecoEntrega?: EnderecoEntrega;
}

/** O resumo que `GET /api/v1/pedidos` devolve na lista. */
export interface ResumoPedido {
  pedidoId: string;
  cliente: string;
  status: string;
  previsaoEntrega: string;
}

/** O corpo de `POST /api/v1/notificacoes`. */
export interface Notificacao {
  canal: 'email' | 'sms' | 'whatsapp' | 'push';
  destinatario: string;
  mensagem: string;
}

/** Rótulo legível para os códigos de status que a API devolve. */
export const ROTULO_STATUS: Record<string, string> = {
  AGUARDANDO_COLETA: 'Aguardando coleta',
  COLETADO: 'Coletado',
  EM_TRANSITO: 'Em trânsito',
  SAIU_PARA_ENTREGA: 'Saiu para entrega',
  ENTREGUE: 'Entregue',
};
