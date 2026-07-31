/**
 * RESGATE do TODO-4: a tela de rastreamento, resolvida.
 *
 * Rede de segurança, não atalho. Leia `resgate/LEIA-ME.md` antes de copiar.
 */

import { useEffect, useState } from 'react';

import { buscarPedido } from '../api/logitech';
import { ROTULO_STATUS, type Pedido } from '../api/tipos';

interface Props {
  pedidoId: string;
}

export function RastreioPedido({ pedidoId }: Props) {
  const [pedido, setPedido] = useState<Pedido | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    // `ativo` fecha a corrida: se o pedido mudar antes da resposta chegar,
    // a limpeza do efeito derruba a bandeira e a resposta velha é
    // descartada em vez de sobrescrever a nova.
    let ativo = true;
    setCarregando(true);
    setErro(null);

    buscarPedido(pedidoId)
      .then((encontrado) => {
        if (ativo) {
          setPedido(encontrado);
        }
      })
      .catch((falha: Error) => {
        if (ativo) {
          setPedido(null);
          setErro(falha.message);
        }
      })
      .finally(() => {
        if (ativo) {
          setCarregando(false);
        }
      });

    return () => {
      ativo = false;
    };
  }, [pedidoId]);

  if (carregando) {
    return (
      <section className="cartao">
        <h2>Rastreamento</h2>
        <p role="status">Consultando a plataforma...</p>
      </section>
    );
  }

  if (erro !== null) {
    return (
      <section className="cartao">
        <h2>Rastreamento</h2>
        <p role="alert">{erro}</p>
      </section>
    );
  }

  if (pedido === null) {
    return null;
  }

  return (
    <section className="cartao" data-testid="rastreio">
      <h2>Rastreamento</h2>
      <p className="destaque">{ROTULO_STATUS[pedido.status] ?? pedido.status}</p>
      <dl>
        <dt>Pedido</dt>
        <dd>{pedido.id}</dd>
        <dt>Cliente</dt>
        <dd>{pedido.cliente}</dd>
        <dt>Rota</dt>
        <dd>
          {pedido.origem} para {pedido.destino}
        </dd>
        <dt>Peso</dt>
        <dd>{pedido.pesoKg} kg</dd>
        <dt>Atualizado em</dt>
        <dd>{pedido.atualizadoEm}</dd>
      </dl>
    </section>
  );
}
