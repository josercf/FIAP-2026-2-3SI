/**
 * A Linguagem Ubíqua da plataforma LogiTech, do lado do navegador.
 *
 * Os nomes em `Posicao` vêm com underscore porque é assim que o rastreador
 * do caminhão emite e assim que o coletor da Aula 02 grava. Renomear aqui
 * seria inventar um segundo vocabulário para a mesma coisa. Quem traduz o
 * formato do dispositivo para o vocabulário da tela é o `map` do fluxo de
 * alertas, e não um campo com dois nomes.
 */

/** Uma posição de caminhão, como o coletor a publica. */
export interface Posicao {
  placa: string;
  uf: string;
  lat: number;
  lng: number;
  velocidade_kmh: number;
  temperatura_c?: number;
  recebido_em?: string;
}

/** Um caminhão acima do limite de velocidade, já no vocabulário da tela. */
export interface Alerta {
  placa: string;
  uf: string;
  velocidadeKmh: number;
  em: string;
}

/** Uma fatura, como o serviço de Faturamento (C#/.NET) a devolve. */
export interface Fatura {
  pedidoId: number;
  numero: string;
  cliente: string;
  valor: number;
  emitidaEm: string;
}

/** O que a consulta de fatura devolve: a fatura, ou a ausência dela. */
export type ResultadoDaConsulta = Fatura | null;
