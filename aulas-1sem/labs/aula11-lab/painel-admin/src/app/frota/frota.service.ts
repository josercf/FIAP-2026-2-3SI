import { Injectable, inject } from '@angular/core';
// Tudo o que as quatro lacunas deste arquivo precisam já está importado. O
// exercício é sobre o fluxo, não sobre caçar `import`.
import { BehaviorSubject, EMPTY, Observable, Subject, combineLatest, of } from 'rxjs';
import { filter, map, scan, share, shareReplay } from 'rxjs/operators';

import { AMBIENTE } from '../nucleo/ambiente';
import { ABRIR_FONTE_DE_EVENTOS } from '../nucleo/fonte-de-eventos';
import { acumularPorPlaca, ordenarPorPlaca } from '../nucleo/acumulador';
import { Alerta, Posicao } from '../nucleo/modelos';

/** Acima disto, o caminhão vira alerta na tela do operador. */
export const LIMITE_VELOCIDADE_KMH = 90;

/** Valor do filtro que significa "não filtre nada". */
export const UF_TODAS = 'TODAS';

/**
 * O fluxo contínuo do painel administrativo: a posição dos 400 caminhões da
 * LogiTech, chegando o tempo todo pelo SSE do serviço `painel` (Aula 02).
 *
 * Este é o lado do case que **justifica** RxJS. Uma consulta pontual não
 * justificaria: para um valor futuro e único, `Promise` basta. Aqui não
 * existe "a resposta": existe um fluxo que começa quando alguém se inscreve,
 * emite indefinidamente e termina quando o último inscrito sai.
 *
 * Quatro lacunas moram aqui: TODO-2, TODO-3, TODO-4 e TODO-5.
 */
@Injectable({ providedIn: 'root' })
export class FrotaService {
  /** A fábrica da fonte de eventos, entregue pelo injetor (Aula 05, DI). */
  private readonly abrirFonte = inject(ABRIR_FONTE_DE_EVENTOS);

  /** Onde o painel busca o fluxo de posições. */
  readonly urlDeEventos = `${AMBIENTE.painelUrl}/api/v1/eventos`;

  // TODO-5a -----------------------------------------------------------------
  // Um `Subject` puro não guarda valor: quem se inscrever depois da última
  // emissão fica esperando a próxima. Como o filtro de UF só muda quando o
  // operador clica, o painel abriria vazio e continuaria vazio até o
  // primeiro clique.
  //
  // Troque por um `BehaviorSubject<string>` iniciado em `UF_TODAS`.
  private readonly filtroUf = new Subject<string>();

  /** O filtro de UF em vigor, como fluxo. */
  readonly filtroUf$: Observable<string> = this.filtroUf.asObservable();

  /**
   * Cada posição, uma a uma, como o servidor as emite.
   *
   * `share()` faz os vários inscritos dividirem **uma** conexão SSE. Sem ele,
   * cada `| async` do template abriria um `EventSource` próprio, e o
   * contador `sse_assinantes` do serviço `painel` denunciaria o desperdício.
   */
  readonly eventos$: Observable<Posicao> = this.criarFluxoDeEventos().pipe(share());

  /**
   * A fotografia da frota: a última posição conhecida de cada placa.
   *
   * `shareReplay` com `bufferSize: 1` entrega a fotografia atual a quem
   * chegar depois, e `refCount: true` desliga a fonte quando o último
   * inscrito sai, em vez de manter a conexão aberta para sempre.
   */
  readonly frota$: Observable<Posicao[]> = this.montarFrota().pipe(
    shareReplay({ bufferSize: 1, refCount: true }),
  );

  /** Só os caminhões acima do limite, já traduzidos para alerta. */
  readonly alertas$: Observable<Alerta> = this.montarAlertas();

  /** A frota depois do filtro de UF escolhido pelo operador. */
  readonly frotaFiltrada$: Observable<Posicao[]> = this.montarFrotaFiltrada();

  /** Chamado pelo componente quando o operador troca a UF. */
  definirFiltro(uf: string): void {
    this.filtroUf.next(uf);
  }

  // ---------------------------------------------------------------------------
  // TODO-2: o Observable escrito do zero, sobre o SSE
  // ---------------------------------------------------------------------------
  /**
   * Devolva um `new Observable<Posicao>(...)` que:
   *
   *   1. abra a fonte com `this.abrirFonte(this.urlDeEventos)`;
   *   2. inscreva um ouvinte no evento `'posicao'` e chame
   *      `inscrito.next(JSON.parse(evento.data))` a cada mensagem;
   *   3. inscreva um ouvinte em `'error'` e chame `inscrito.error(...)`;
   *   4. **devolva uma função de teardown** que faça `fonte.close()`.
   *
   * O item 4 é o que separa este Observable de um vazamento de recurso: sem
   * ele, cada componente destruído deixa uma conexão SSE viva no servidor. O
   * contador `sse_assinantes` do `GET /health` do painel mostra isso ao vivo.
   */
  private criarFluxoDeEventos(): Observable<Posicao> {
    // TODO-2: substitua o EMPTY pelo Observable descrito acima.
    // `EMPTY` completa na hora sem emitir nada: por isso a tela abre vazia.
    return EMPTY;
  }

  // ---------------------------------------------------------------------------
  // TODO-3: de evento avulso para fotografia da frota, com `scan` e `map`
  // ---------------------------------------------------------------------------
  /**
   * Encadeie sobre `this.eventos$`:
   *
   *   scan(acumularPorPlaca, new Map<string, Posicao>())
   *   map(ordenarPorPlaca)
   *
   * `scan` é o `reduce` que não espera o fim: ele emite o acumulado a cada
   * valor novo. Como o fluxo de telemetria nunca termina, um `reduce` aqui
   * jamais emitiria coisa alguma.
   */
  private montarFrota(): Observable<Posicao[]> {
    // TODO-3: substitua o of([]) pelo encadeamento descrito acima.
    return of([]);
  }

  // ---------------------------------------------------------------------------
  // TODO-4: o fluxo de alertas, com `filter` e `map`
  // ---------------------------------------------------------------------------
  /**
   * Encadeie sobre `this.eventos$`:
   *
   *   filter(...)   deixe passar só quem estiver acima de LIMITE_VELOCIDADE_KMH
   *   map(...)      transforme a `Posicao` em `Alerta`:
   *                 { placa, uf, velocidadeKmh: posicao.velocidade_kmh,
   *                   em: posicao.recebido_em ?? '' }
   *
   * Repare na divisão de trabalho: `filter` decide **se** o valor segue,
   * `map` decide **como** ele segue. É o `map` que traduz o vocabulário do
   * rastreador (`velocidade_kmh`) para o da tela (`velocidadeKmh`).
   */
  private montarAlertas(): Observable<Alerta> {
    // TODO-4: substitua o EMPTY pelo encadeamento descrito acima.
    return EMPTY;
  }

  // ---------------------------------------------------------------------------
  // TODO-5b: cruzar dois fluxos com `combineLatest`
  // ---------------------------------------------------------------------------
  /**
   * Combine `this.frota$` com `this.filtroUf$` e devolva a frota filtrada:
   *
   *   combineLatest([this.frota$, this.filtroUf$]).pipe(
   *     map(([frota, uf]) => uf === UF_TODAS ? frota : frota.filter(...)),
   *   )
   *
   * `combineLatest` reemite quando **qualquer** um dos dois emite, sempre com
   * o último valor de cada. É por isso que trocar a UF refiltra na hora sem
   * esperar o próximo caminhão, e um caminhão novo respeita a UF já escolhida.
   *
   * E é aqui que o `Subject` do TODO-5a cobra o preço: `combineLatest` não
   * emite nada enquanto um dos dois fluxos não tiver emitido pelo menos uma
   * vez.
   */
  private montarFrotaFiltrada(): Observable<Posicao[]> {
    // TODO-5b: substitua a linha abaixo pelo combineLatest descrito acima.
    return this.frota$;
  }
}
