/**
 * TODO-4: a tela de rastreamento do Portal do Cliente.
 *
 * ESTE ARQUIVO É SEU. Escreva aqui.
 *
 * A dor de negócio é a da Aula 01, e ela ainda não tinha tela: o cliente da
 * LogiTech liga para o atendimento para saber onde está a carga. Hoje ele
 * escolhe o pedido e vê.
 *
 * O componente recebe `pedidoId` por `prop` e precisa passar por três
 * estados, os mesmos de qualquer tela que fala com rede:
 *
 *     carregando  ->  dados      (a plataforma respondeu)
 *                 ->  erro       (não respondeu, ou respondeu 404)
 *
 * O que você escreve:
 *
 * 1. três `useState`: `pedido`, `erro` e `carregando`;
 * 2. um `useEffect` com `[pedidoId]` no array de dependências, chamando
 *    `buscarPedido(pedidoId)`;
 * 3. a marcação dos três estados, com os `data-testid` e os papéis de
 *    acessibilidade que os testes já esperam (veja `RastreioPedido.test.tsx`,
 *    que vem pronto e vermelho).
 *
 * Contrato de tela que os testes cobram, à risca:
 *
 * | Estado     | O que precisa aparecer                                    |
 * |------------|-----------------------------------------------------------|
 * | carregando | um elemento com `role="status"` e o texto `Consultando...` |
 * | erro       | um elemento com `role="alert"` e o texto do erro           |
 * | dados      | `data-testid="rastreio"`, com o rótulo legível do status,  |
 * |            | o cliente, a rota `origem -> destino` e o peso em kg       |
 *
 * O rótulo legível sai de `ROTULO_STATUS`, que já está em `api/tipos.ts`:
 * a API devolve `EM_TRANSITO` e o cliente lê `Em trânsito`.
 *
 * DUAS ARMADILHAS, e as duas caem em prova:
 *
 * - **O array de dependências.** `useEffect(() => {...})` sem array roda a
 *   cada renderização. Como o efeito chama a API e a resposta muda o
 *   estado, e mudar o estado renderiza de novo, você acabou de escrever um
 *   laço infinito de requisições. Com `[pedidoId]`, o efeito só roda quando
 *   o pedido muda.
 * - **A corrida.** Se o pedido mudar antes de a primeira resposta chegar,
 *   as duas respostas voltam fora de ordem e a tela pode ficar mostrando o
 *   pedido errado. A saída padrão é uma bandeira local junto com a função
 *   de limpeza do efeito:
 *
 *       useEffect(() => {
 *         let ativo = true;
 *         buscarPedido(pedidoId).then((p) => { if (ativo) setPedido(p); });
 *         return () => { ativo = false; };
 *       }, [pedidoId]);
 */

import { useEffect, useState } from 'react';

import { buscarPedido } from '../api/logitech';
import { ROTULO_STATUS, type Pedido } from '../api/tipos';

interface Props {
  pedidoId: string;
}

export function RastreioPedido({ pedidoId }: Props) {
  // TODO-4: os três `useState` entram aqui.

  // TODO-4: o `useEffect` com `[pedidoId]` entra aqui.

  // TODO-4: troque este bloco pela marcação dos três estados.
  return (
    <section className="cartao">
      <h2>Rastreamento</h2>
      <p>TODO-4: o rastreamento do pedido {pedidoId} ainda não foi escrito.</p>
    </section>
  );
}
