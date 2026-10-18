/**
 * A fronteira do Portal do Cliente com a plataforma LogiTech.
 *
 * CONGELADO. Não é tarefa da Aula 10.
 *
 * Mesmo princípio do `cliente_pedidos.py` do serviço de frete, agora do
 * lado do navegador: as duas funções abaixo só traduzem JSON em objeto.
 * Não há regra de negócio aqui, e é de propósito. Fronteira burra é
 * fronteira fácil de dublar, e o que sobra do outro lado (os componentes)
 * se testa sem rede.
 *
 * Nenhum componente chama `fetch` diretamente. Todos passam por aqui, e é
 * por isso que os testes conseguem trocar este módulo inteiro por um dublê
 * com uma linha de `vi.mock`.
 *
 * Endereço nunca cravado no código: vem de variável de ambiente, com
 * padrão de desenvolvimento local, como manda a ADR-006.
 */

import type { Cotacao, EntradaCotacao, Pedido } from './tipos';

const PEDIDOS_URL: string =
  import.meta.env.VITE_PEDIDOS_URL ?? 'http://localhost:8080';
const FRETE_URL: string =
  import.meta.env.VITE_FRETE_URL ?? 'http://localhost:8000';

export class PedidoNaoEncontrado extends Error {}
export class PlataformaIndisponivel extends Error {}

/** Busca um pedido pelo identificador. Rota `GET /api/v1/pedidos/{id}`. */
export async function buscarPedido(pedidoId: string): Promise<Pedido> {
  let resposta: Response;
  try {
    resposta = await fetch(`${PEDIDOS_URL}/api/v1/pedidos/${pedidoId}`);
  } catch (erro) {
    throw new PlataformaIndisponivel(
      'não foi possível falar com o serviço de Pedidos',
    );
  }
  if (resposta.status === 404) {
    throw new PedidoNaoEncontrado(`pedido não encontrado: ${pedidoId}`);
  }
  if (!resposta.ok) {
    throw new PlataformaIndisponivel(
      `serviço de Pedidos devolveu ${resposta.status}`,
    );
  }
  return (await resposta.json()) as Pedido;
}

/** Cota um frete avulso. Rota `POST /api/v1/frete/cotacao`. */
export async function cotarFrete(entrada: EntradaCotacao): Promise<Cotacao> {
  let resposta: Response;
  try {
    resposta = await fetch(`${FRETE_URL}/api/v1/frete/cotacao`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entrada),
    });
  } catch (erro) {
    throw new PlataformaIndisponivel(
      'não foi possível falar com o serviço de frete',
    );
  }
  if (!resposta.ok) {
    throw new PlataformaIndisponivel(
      `serviço de frete devolveu ${resposta.status}`,
    );
  }
  return (await resposta.json()) as Cotacao;
}
