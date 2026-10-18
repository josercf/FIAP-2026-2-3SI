/**
 * Testes de tela da cotação. Vêm prontos e VERMELHOS.
 *
 * CONGELADO. Não é tarefa, e não é para editar: é a especificação do
 * `TODO-5`.
 *
 * Os três testes daqui olham para **o que aparece na tela**. Eles provam
 * que o formulário funciona do ponto de vista de quem usa: preencheu,
 * clicou, viu o valor.
 *
 * Guarde essa frase, porque o `TODO-6` nasce dela: nenhum destes três
 * testes olha para **o que foi enviado**. Se o componente mandar a
 * modalidade errada para a plataforma, o dublê responde a mesma coisa, a
 * tela mostra a mesma coisa e os três continuam verdes. O cliente da
 * LogiTech é que descobre, na fatura.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { CotacaoFrete } from './CotacaoFrete';
import { cotarFrete, PlataformaIndisponivel } from '../api/logitech';

vi.mock('../api/logitech', async () => {
  const original =
    await vi.importActual<typeof import('../api/logitech')>('../api/logitech');
  return { ...original, cotarFrete: vi.fn() };
});

const cotarFreteDublado = vi.mocked(cotarFrete);

describe('CotacaoFrete', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('mostra o valor e o prazo devolvidos pela plataforma', async () => {
    cotarFreteDublado.mockResolvedValue({
      valor: 380.0,
      prazoDias: 2,
      modalidade: 'padrao',
    });

    render(<CotacaoFrete />);
    await userEvent.click(screen.getByRole('button', { name: /cotar/i }));

    const resultado = await screen.findByTestId('cotacao');
    expect(resultado).toHaveTextContent('380,00');
    expect(resultado).toHaveTextContent('2 dia');
  });

  it('mostra o erro quando a plataforma não responde', async () => {
    cotarFreteDublado.mockRejectedValue(
      new PlataformaIndisponivel('não foi possível falar com o serviço de frete'),
    );

    render(<CotacaoFrete />);
    await userEvent.click(screen.getByRole('button', { name: /cotar/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/frete/i);
  });

  it('oferece as três modalidades da LogiTech, com padrao já selecionada', () => {
    render(<CotacaoFrete />);

    const selecao = screen.getByLabelText(/modalidade/i) as HTMLSelectElement;
    const opcoes = Array.from(selecao.options).map((o) => o.value);

    expect(opcoes).toEqual(['expresso', 'padrao', 'economico']);
    expect(selecao.value).toBe('padrao');
  });
});
