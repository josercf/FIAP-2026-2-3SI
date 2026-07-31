import { AsyncPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { Subject, of, timer } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';

import { AMBIENTE } from '../nucleo/ambiente';
import { FaturamentoService } from './faturamento.service';

/** O que `GET /api/v1/metricas` do serviço de Faturamento devolve. */
interface MetricasDeConsulta {
  consultasRecebidas: number;
  consultasConcluidas: number;
  consultasCanceladas: number;
  linhaDoTempo: string[];
}

/**
 * A consulta de fatura e o painel de evidência. Componente pronto, não é
 * lacuna.
 *
 * O painel de métricas do lado direito existe para uma coisa só: mostrar,
 * enquanto vocês digitam, quantas consultas o serviço recebeu, quantas
 * concluiu e quantas o navegador **abandonou no meio**. Antes do TODO-6 o
 * contador de canceladas fica em zero. Depois dele, sobe.
 */
@Component({
  selector: 'app-faturas',
  imports: [AsyncPipe],
  template: `
    <section class="cartao">
      <header><h2>Consulta de fatura</h2></header>

      <label class="busca">
        <span>Número do pedido</span>
        <input
          type="text"
          inputmode="numeric"
          placeholder="tente 1001 a 1008"
          [value]="termo()"
          (input)="digitar($any($event.target).value)" />
      </label>

      @if (resultado$ | async; as fatura) {
        <dl class="fatura">
          <dt>Nota fiscal</dt><dd class="mono">{{ fatura.numero }}</dd>
          <dt>Pedido</dt><dd class="mono">{{ fatura.pedidoId }}</dd>
          <dt>Cliente</dt><dd>{{ fatura.cliente }}</dd>
          <dt>Valor</dt><dd class="mono">R$ {{ fatura.valor }}</dd>
          <dt>Emitida em</dt><dd class="mono">{{ fatura.emitidaEm }}</dd>
        </dl>
      } @else {
        <p class="vazio">
          Digite um número de pedido. Se nada acontecer, confira o TODO-1: sem o
          provedor do HttpClient nenhuma requisição chega a sair.
        </p>
      }
    </section>

    <section class="cartao">
      <header><h2>Evidência: o que o serviço de Faturamento viu</h2></header>
      @if (metricas$ | async; as m) {
        <div class="contadores">
          <div><span class="numero">{{ m.consultasRecebidas }}</span><span>recebidas</span></div>
          <div><span class="numero">{{ m.consultasConcluidas }}</span><span>concluídas</span></div>
          <div class="destaque">
            <span class="numero">{{ m.consultasCanceladas }}</span><span>canceladas</span>
          </div>
        </div>
        <ul class="linha-do-tempo mono">
          @for (linha of ultimasLinhas(m.linhaDoTempo); track linha) {
            <li [class.grave]="linha.includes('CANCELADA')">{{ linha }}</li>
          }
        </ul>
      } @else {
        <p class="vazio">Serviço de Faturamento fora do ar na porta 5080.</p>
      }
      <p class="rodape">
        Zerar os contadores:
        <code class="mono">curl -X POST {{ urlMetricas }}/zerar</code>
      </p>
    </section>
  `,
})
export class FaturasComponent {
  private readonly faturamento = inject(FaturamentoService);
  private readonly http = inject(HttpClient);

  /** O fluxo do que o operador está digitando. */
  private readonly termos = new Subject<string>();

  readonly termo = signal('');
  readonly urlMetricas = `${AMBIENTE.faturamentoUrl}/api/v1/metricas`;

  /** O resultado da consulta, já com o encadeamento do TODO-6 aplicado. */
  readonly resultado$ = this.faturamento.consultar(this.termos.asObservable());

  /**
   * As métricas do serviço, a cada segundo.
   *
   * `timer(0, 1000)` emite agora e depois a cada segundo; `switchMap` troca a
   * consulta pendente pela nova. Se o serviço demorar mais que um segundo,
   * não se acumula fila: a consulta velha é descartada. É o mesmo operador do
   * TODO-6, aqui numa sondagem em vez de numa busca.
   */
  readonly metricas$ = timer(0, 1000).pipe(
    switchMap(() =>
      this.http
        .get<MetricasDeConsulta>(this.urlMetricas)
        .pipe(catchError(() => of(null))),
    ),
  );

  digitar(valor: string): void {
    this.termo.set(valor);
    this.termos.next(valor);
  }

  ultimasLinhas(linhas: string[]): string[] {
    return linhas.slice(-8).reverse();
  }
}
