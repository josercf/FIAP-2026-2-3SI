/**
 * TODO-5: a tela de cotação de frete do Portal do Cliente.
 *
 * ESTE ARQUIVO É SEU. Escreva aqui.
 *
 * O cliente da LogiTech quer saber quanto custa e em quantos dias chega,
 * antes de fechar o pedido. O formulário tem quatro campos e um botão, e
 * fala com `POST /api/v1/frete/cotacao`, a mesma rota que vocês fizeram
 * responder na Aula 06.
 *
 * O que você escreve:
 *
 * 1. um `useState` por campo controlado (`origem`, `destino`, `peso`,
 *    `modalidade`) mais `cotacao`, `erro` e `cotando`;
 * 2. o `onSubmit` do formulário, chamando `cotarFrete(...)`;
 * 3. a marcação do resultado.
 *
 * Os campos começam preenchidos com a rota de referência do laboratório:
 * `SAO`, `LDB`, `100` e `padrao`. Os testes contam com isso.
 *
 * Contrato de tela que os testes cobram, à risca:
 *
 * | Elemento              | Como o teste encontra                          |
 * |-----------------------|------------------------------------------------|
 * | campo de origem       | rótulo `Origem`                                |
 * | campo de destino      | rótulo `Destino`                               |
 * | campo de peso         | rótulo `Peso (kg)`                             |
 * | seleção de modalidade | rótulo `Modalidade`, com as três opções        |
 * | botão                 | texto `Cotar`                                  |
 * | resultado             | `data-testid="cotacao"`, com valor e prazo     |
 * | erro                  | `role="alert"`                                 |
 *
 * O valor aparece na tela em reais, com vírgula decimal: `380,00`.
 *
 * DUAS ARMADILHAS, e as duas caem em prova:
 *
 * - **`event.preventDefault()`.** Sem ele o formulário recarrega a página,
 *   o React remonta tudo e o resultado some antes de você conseguir ler.
 * - **O peso é `number` no contrato.** O valor de um `<input>` é sempre
 *   `string`, mesmo com `type="number"`. Mandar `pesoKg: "100"` produz uma
 *   tela que funciona, um teste de tela que passa, e um `422` do Pydantic
 *   no dia em que alguém apertar o contrato. Converta com `Number(...)`.
 *   O `TODO-6` existe para pegar exatamente isso.
 */

import { useState, type FormEvent } from 'react';

import { cotarFrete } from '../api/logitech';
import type { Cotacao } from '../api/tipos';

const MODALIDADES = ['expresso', 'padrao', 'economico'];

export function CotacaoFrete() {
  // TODO-5: os `useState` dos campos e do resultado entram aqui.

  // TODO-5: o `onSubmit` entra aqui.

  // TODO-5: troque este bloco pelo formulário descrito acima.
  return (
    <section className="cartao">
      <h2>Cotação de frete</h2>
      <p>TODO-5: o formulário de cotação ainda não foi escrito.</p>
    </section>
  );
}
