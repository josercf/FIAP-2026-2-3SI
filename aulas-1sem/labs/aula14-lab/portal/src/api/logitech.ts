/**
 * A fronteira do Portal do Cliente com a plataforma LogiTech.
 *
 * CONGELADO. Não é tarefa da Aula 14.
 *
 * A novidade em relação à Aula 10 cabe em uma linha: toda requisição sai com
 * `Authorization: Bearer <token>`. Nenhum componente monta esse cabeçalho
 * sozinho, e é de propósito: cabeçalho de autenticação espalhado por dez
 * arquivos é a receita para a décima primeira chamada esquecer dele.
 *
 * Repare no tratamento separado de 401 e 403. Os dois são "não", e as ações
 * são opostas: no 401 faz sentido mandar o usuário entrar de novo; no 403,
 * repetir o login não muda nada, porque o problema é o papel.
 */

import type { Notificacao, Pedido, ResumoPedido } from './tipos';

const PEDIDOS_URL: string =
  import.meta.env.VITE_PEDIDOS_URL ?? 'http://localhost:8080';
const NOTIFICACOES_URL: string =
  import.meta.env.VITE_NOTIFICACOES_URL ?? 'http://localhost:3001';

export class NaoAutenticado extends Error {}
export class SemPermissao extends Error {}
export class PlataformaIndisponivel extends Error {}

async function chamar<T>(
  url: string,
  token: string | null,
  init: RequestInit = {},
): Promise<T> {
  const cabecalhos = new Headers(init.headers);
  if (token) cabecalhos.set('Authorization', `Bearer ${token}`);
  if (init.body) cabecalhos.set('Content-Type', 'application/json');

  let resposta: Response;
  try {
    resposta = await fetch(url, { ...init, headers: cabecalhos });
  } catch {
    throw new PlataformaIndisponivel('não foi possível falar com a plataforma');
  }

  if (resposta.status === 401) {
    const corpo = await resposta.json().catch(() => ({}));
    throw new NaoAutenticado(String(corpo.motivo ?? 'faça login para continuar'));
  }
  if (resposta.status === 403) {
    const corpo = await resposta.json().catch(() => ({}));
    const aceitos = (corpo.papeisAceitos ?? []).join(' ou ');
    throw new SemPermissao(
      aceitos
        ? `esta ação exige o papel ${aceitos}, e o seu login não tem`
        : 'o seu login não tem permissão para esta ação',
    );
  }
  if (!resposta.ok) {
    throw new PlataformaIndisponivel(`a plataforma devolveu ${resposta.status}`);
  }
  return (await resposta.json()) as T;
}

/** `GET /api/v1/pedidos`. Aceita CLIENTE, MOTORISTA ou ADMIN. */
export function listarPedidos(token: string | null): Promise<{ total: number; pedidos: ResumoPedido[] }> {
  return chamar(`${PEDIDOS_URL}/api/v1/pedidos`, token);
}

/** `GET /api/v1/pedidos/{id}`. Qualquer papel autenticado. */
export function buscarPedido(token: string | null, pedidoId: string): Promise<Pedido> {
  return chamar(`${PEDIDOS_URL}/api/v1/pedidos/${pedidoId}`, token);
}

/** `PATCH /api/v1/pedidos/{id}/endereco`. Só CLIENTE ou ADMIN. */
export function alterarEndereco(
  token: string | null,
  pedidoId: string,
  endereco: Record<string, string>,
): Promise<Pedido> {
  return chamar(`${PEDIDOS_URL}/api/v1/pedidos/${pedidoId}/endereco`, token, {
    method: 'PATCH',
    body: JSON.stringify(endereco),
  });
}

/** `POST /api/v1/notificacoes`, no serviço Node. Só ADMIN. */
export function notificar(token: string | null, dados: Notificacao): Promise<unknown> {
  return chamar(`${NOTIFICACOES_URL}/api/v1/notificacoes`, token, {
    method: 'POST',
    body: JSON.stringify(dados),
  });
}
