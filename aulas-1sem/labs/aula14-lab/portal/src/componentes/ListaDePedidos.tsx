/**
 * A lista de pedidos, que só existe com token.
 *
 * CONGELADO. Não é tarefa da Aula 14.
 */

import { useEffect, useState } from 'react';

import { listarPedidos } from '../api/logitech';
import { ROTULO_STATUS, type ResumoPedido } from '../api/tipos';

export function ListaDePedidos({ token }: { token: string | null }) {
  const [pedidos, setPedidos] = useState<ResumoPedido[]>([]);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;
    setErro(null);
    if (!token) {
      setPedidos([]);
      return undefined;
    }
    listarPedidos(token)
      .then((resposta) => {
        if (ativo) setPedidos(resposta.pedidos);
      })
      .catch((falha: Error) => {
        if (ativo) {
          setPedidos([]);
          setErro(falha.message);
        }
      });
    return () => {
      ativo = false;
    };
  }, [token]);

  return (
    <section className="cartao" data-testid="pedidos">
      <h2>Seus pedidos</h2>
      {!token && <p role="status">Entre para ver os pedidos.</p>}
      {erro !== null && <p role="alert">{erro}</p>}
      <ul>
        {pedidos.map((p) => (
          <li key={p.pedidoId}>
            <strong>{p.pedidoId}</strong> {p.cliente} |{' '}
            {ROTULO_STATUS[p.status] ?? p.status} | previsão {p.previsaoEntrega}
          </li>
        ))}
      </ul>
    </section>
  );
}
