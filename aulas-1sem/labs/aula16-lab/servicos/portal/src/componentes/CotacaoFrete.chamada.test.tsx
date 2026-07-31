/**
 * RESGATE do TODO-6: o teste de chamada, resolvido.
 *
 * Rede de segurança, não atalho. Leia `resgate/LEIA-ME.md` antes de copiar.
 *
 * Este arquivo vai para `portal/src/componentes/CotacaoFrete.chamada.test.tsx`.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { CotacaoFrete } from './CotacaoFrete';
import { cotarFrete } from '../api/logitech';

vi.mock('../api/logitech', async () => {
  const original =
    await vi.importActual<typeof import('../api/logitech')>('../api/logitech');
  return { ...original, cotarFrete: vi.fn() };
});

const cotarFreteDublado = vi.mocked(cotarFrete);

describe('CotacaoFrete: o que sai pela rede', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    cotarFreteDublado.mockResolvedValue({
      valor: 545.0,
      prazoDias: 1,
      modalidade: 'expresso',
    });
  });

  it('envia a modalidade escolhida, e o peso como número', async () => {
    render(<CotacaoFrete />);

    await userEvent.selectOptions(
      screen.getByLabelText(/modalidade/i),
      'expresso',
    );
    await userEvent.click(screen.getByRole('button', { name: /cotar/i }));

    expect(cotarFreteDublado).toHaveBeenCalledTimes(1);
    expect(cotarFreteDublado).toHaveBeenCalledWith({
      origem: 'SAO',
      destino: 'LDB',
      pesoKg: 100,
      modalidade: 'expresso',
    });
  });

  it('envia a rota digitada pelo cliente, normalizada em maiúsculas', async () => {
    render(<CotacaoFrete />);

    const origem = screen.getByLabelText(/origem/i);
    const destino = screen.getByLabelText(/destino/i);
    await userEvent.clear(origem);
    await userEvent.type(origem, 'rio');
    await userEvent.clear(destino);
    await userEvent.type(destino, 'bhz');
    await userEvent.click(screen.getByRole('button', { name: /cotar/i }));

    expect(cotarFreteDublado).toHaveBeenCalledWith({
      origem: 'RIO',
      destino: 'BHZ',
      pesoKg: 100,
      modalidade: 'padrao',
    });
  });
});
