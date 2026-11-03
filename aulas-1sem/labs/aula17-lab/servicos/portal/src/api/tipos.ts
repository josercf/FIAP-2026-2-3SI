/**
 * O contrato da plataforma LogiTech, escrito em TypeScript.
 *
 * CONGELADO. Não é tarefa da Aula 10.
 *
 * Os nomes dos campos são os da ADR-006 e não se traduzem: `pesoKg` e
 * `prazoDias` chegam assim do Python e do C# e ficam assim aqui. Traduzir
 * nome de campo na borda é a origem clássica do defeito que ninguém acha,
 * porque o TypeScript some em tempo de execução e o JSON não avisa nada.
 *
 * Vale reforçar o que este arquivo **não** faz: ele não valida nada. Uma
 * `interface` do TypeScript existe só durante a compilação. Se o backend
 * mudar o contrato, isto aqui continua compilando e a tela quebra. Quem
 * garante o contrato é o teste, e é por isso que a aula de frontend também
 * é aula de teste.
 */

/** Um pedido, como o serviço de Pedidos devolve. */
export interface Pedido {
  id: string;
  cliente: string;
  origem: string;
  destino: string;
  pesoKg: number;
  status: string;
  atualizadoEm: string;
}

/** O corpo de `POST /api/v1/frete/cotacao`. */
export interface EntradaCotacao {
  origem: string;
  destino: string;
  pesoKg: number;
  modalidade: string;
}

/** A resposta de `POST /api/v1/frete/cotacao`. */
export interface Cotacao {
  valor: number;
  prazoDias: number;
  modalidade: string;
}

/** Rótulo legível para os códigos de status que a API devolve. */
export const ROTULO_STATUS: Record<string, string> = {
  AGUARDANDO_COLETA: 'Aguardando coleta',
  COLETADO: 'Coletado',
  EM_TRANSITO: 'Em trânsito',
  ENTREGUE: 'Entregue',
};
