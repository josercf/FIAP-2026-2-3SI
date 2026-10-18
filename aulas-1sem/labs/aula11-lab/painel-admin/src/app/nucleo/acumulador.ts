import { Posicao } from './modelos';

/**
 * Funções puras de acumulação da frota. Já vêm prontas: o exercício de hoje
 * é ligá-las ao fluxo com `scan` e `map`, não reescrever aritmética de mapa.
 */

/**
 * Aplica uma posição nova sobre a fotografia atual da frota.
 *
 * Devolve um Map **novo** de propósito. O painel roda em modo zoneless: a
 * detecção de mudança compara referências, e mutar o acumulador no lugar
 * faria a tela ficar parada com o dado certo por baixo, que é o pior tipo
 * de defeito de interface.
 */
export function acumularPorPlaca(
  frotaAtual: Map<string, Posicao>,
  posicao: Posicao,
): Map<string, Posicao> {
  const proxima = new Map(frotaAtual);
  proxima.set(posicao.placa, posicao);
  return proxima;
}

/** A fotografia como lista, em ordem estável de placa. */
export function ordenarPorPlaca(frota: Map<string, Posicao>): Posicao[] {
  return [...frota.values()].sort((a, b) => a.placa.localeCompare(b.placa));
}
