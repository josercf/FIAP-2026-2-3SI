/**
 * Testes da tela de rastreamento. Vêm prontos e VERMELHOS.
 *
 * CONGELADO. Não é tarefa, e não é para editar: é a especificação do
 * `TODO-4` escrita em código executável.
 *
 * Este arquivo é o ciclo do TDD acontecendo com você do lado de dentro: o
 * teste existe antes da implementação, ele falha, e o seu trabalho é
 * fazê-lo passar sem mudar o que ele cobra. Se der vontade de "ajustar o
 * teste para o meu componente", pare: quem ajusta a especificação para caber
 * no código entrega software que faz outra coisa.
 *
 * Repare em como o dublê entra. `vi.mock` troca o módulo inteiro
 * `../api/logitech` por funções falsas, e o componente nem fica sabendo. É a
 * mesma ideia do `ClientePedidosStub` do serviço de frete: o componente
 * depende de um contrato, e no teste quem cumpre o contrato é outro.
 *
 * E repare no que este dublê comprova de graça: nenhum destes testes precisa
 * de `pedidos` no ar. Rode com a máquina desconectada da rede que passa
 * igual.
 */

import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { RastreioPedido } from './RastreioPedido';
import { buscarPedido, PedidoNaoEncontrado } from '../api/logitech';
import type { Pedido } from '../api/tipos';

vi.mock('../api/logitech', async () => {
  const original =
    await vi.importActual<typeof import('../api/logitech')>('../api/logitech');
  return { ...original, buscarPedido: vi.fn() };
});

const buscarPedidoDublado = vi.mocked(buscarPedido);

const PEDIDO: Pedido = {
  id: 'PED-1001',
  cliente: 'Supermercados Aurora',
  origem: 'SAO',
  destino: 'LDB',
  pesoKg: 100,
  status: 'EM_TRANSITO',
  atualizadoEm: '2026-10-06T14:20:00',
};

describe('RastreioPedido', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('avisa que está consultando antes de a plataforma responder', () => {
    // Promessa que nunca resolve: congela o componente no primeiro estado.
    buscarPedidoDublado.mockReturnValue(new Promise(() => {}));

    render(<RastreioPedido pedidoId="PED-1001" />);

    expect(screen.getByRole('status')).toHaveTextContent(/consultando/i);
  });

  it('mostra o status do pedido em português quando a plataforma responde', async () => {
    buscarPedidoDublado.mockResolvedValue(PEDIDO);

    render(<RastreioPedido pedidoId="PED-1001" />);

    const cartao = await screen.findByTestId('rastreio');
    expect(cartao).toHaveTextContent('Em trânsito');
    expect(cartao).toHaveTextContent('Supermercados Aurora');
    expect(cartao).toHaveTextContent('SAO');
    expect(cartao).toHaveTextContent('LDB');
    expect(cartao).toHaveTextContent('100');
  });

  it('mostra o erro quando o pedido não existe', async () => {
    buscarPedidoDublado.mockRejectedValue(
      new PedidoNaoEncontrado('pedido não encontrado: PED-9999'),
    );

    render(<RastreioPedido pedidoId="PED-9999" />);

    const aviso = await screen.findByRole('alert');
    expect(aviso).toHaveTextContent(/não encontrado/i);
  });

  it('consulta de novo quando o pedido muda, e só quando ele muda', async () => {
    buscarPedidoDublado.mockResolvedValue(PEDIDO);

    const { rerender } = render(<RastreioPedido pedidoId="PED-1001" />);
    await screen.findByTestId('rastreio');

    // Mesma prop: o efeito não pode disparar de novo.
    rerender(<RastreioPedido pedidoId="PED-1001" />);
    expect(buscarPedidoDublado).toHaveBeenCalledTimes(1);

    // Prop diferente: agora sim.
    rerender(<RastreioPedido pedidoId="PED-1002" />);
    await waitFor(() => expect(buscarPedidoDublado).toHaveBeenCalledTimes(2));
    expect(buscarPedidoDublado).toHaveBeenLastCalledWith('PED-1002');
  });
});
