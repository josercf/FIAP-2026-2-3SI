/**
 * Preparação da suíte do Vitest.
 *
 * CONGELADO. Não é tarefa da Aula 10.
 *
 * Carrega os matchers do `@testing-library/jest-dom`, que é de onde vêm
 * `toHaveTextContent`, `toBeInTheDocument` e companhia, e limpa a árvore
 * renderizada entre um teste e outro. Sem essa limpeza, o segundo teste
 * enxerga o DOM do primeiro e `getByRole` reclama de elemento duplicado.
 */

import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});
