/**
 * TODO-6: o teste que olha para a chamada, e não para a tela.
 *
 * ESTE ARQUIVO É SEU. Escreva aqui.
 *
 * `CotacaoFrete.tela.test.tsx` já prova que o formulário mostra o valor
 * certo. Ele não prova, e não tem como provar, que o formulário **pediu** a
 * coisa certa: o dublê responde igual de qualquer jeito.
 *
 * É o mesmo par de conceitos do serviço de frete, agora em TypeScript. Lá
 * foram `assert_called_once_with` e `assert_not_called`, aqui é
 * `toHaveBeenCalledWith` e `toHaveBeenCalledTimes`. A biblioteca muda, a
 * ideia não muda.
 *
 * O dublê do módulo já está montado logo abaixo, igual ao do arquivo de
 * tela. O que falta são os testes.
 *
 * Escreva **no mínimo dois**:
 *
 * 1. escolher uma modalidade **diferente da que já vem selecionada** e
 *    conferir que `cotarFrete` foi chamado uma vez, com exatamente
 *    `{ origem: 'SAO', destino: 'LDB', pesoKg: 100, modalidade: 'expresso' }`.
 *    Repare no `pesoKg`: é o número 100, não a string '100'. O valor de um
 *    `<input>` é sempre `string`, inclusive com `type="number"`, e essa
 *    conversão é justamente o que nenhum teste de tela enxerga;
 * 2. mudar origem e destino nos campos e conferir que os novos valores
 *    chegam à chamada, em maiúsculas.
 *
 * Ferramentas úteis:
 *
 *     await userEvent.selectOptions(screen.getByLabelText(/modalidade/i), 'expresso');
 *     await userEvent.clear(screen.getByLabelText(/origem/i));
 *     await userEvent.type(screen.getByLabelText(/origem/i), 'rio');
 *     expect(cotarFreteDublado).toHaveBeenCalledWith({ ... });
 *
 * Como o verificador avalia este arquivo (`--criterio 7`): ele estraga uma
 * cópia do componente de dois jeitos que **não mudam nada na tela**, porque
 * a resposta vem do dublê: primeiro cravando a modalidade em `padrao`,
 * depois mandando o peso como texto. Os seus testes precisam reprovar nas
 * duas.
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

  // TODO-6: escreva aqui os dois testes de chamada descritos acima.
});
