import { AsyncPipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { scan, startWith } from 'rxjs/operators';

import { Alerta } from '../nucleo/modelos';
import { FrotaService, LIMITE_VELOCIDADE_KMH, UF_TODAS } from './frota.service';

/**
 * O painel de frota. Componente pronto, não é lacuna.
 *
 * Repare no que **não** existe aqui: nenhum `subscribe`, nenhum `ngOnInit`,
 * nenhum `ngOnDestroy`, nenhuma `Subscription` guardada em campo. Quem
 * inscreve é o pipe `async` do template, e quem cancela a inscrição é ele
 * também, quando o componente é destruído. Cada `subscribe` manual é um
 * `unsubscribe` que alguém vai esquecer.
 */
@Component({
  selector: 'app-frota',
  imports: [AsyncPipe],
  template: `
    <section class="cartao">
      <header>
        <h2>Frota em operação</h2>
        <div class="filtros">
          @for (uf of ufs; track uf) {
            <button
              type="button"
              [class.ativo]="uf === ufSelecionada()"
              (click)="trocarUf(uf)">{{ uf }}</button>
          }
        </div>
      </header>

      @if (frotaFiltrada$ | async; as frota) {
        @if (frota.length === 0) {
          <p class="vazio">
            Nenhum caminhão no fluxo ainda. Confira se o coletor, o simulador e o
            painel estão de pé, e se o TODO-2 já foi preenchido.
          </p>
        } @else {
          <table>
            <thead>
              <tr><th>Placa</th><th>UF</th><th>Latitude</th><th>Longitude</th><th>km/h</th></tr>
            </thead>
            <tbody>
              @for (posicao of frota; track posicao.placa) {
                <tr [class.acelerado]="posicao.velocidade_kmh > limite">
                  <td class="mono">{{ posicao.placa }}</td>
                  <td>{{ posicao.uf }}</td>
                  <td class="mono">{{ posicao.lat }}</td>
                  <td class="mono">{{ posicao.lng }}</td>
                  <td class="mono direita">{{ posicao.velocidade_kmh }}</td>
                </tr>
              }
            </tbody>
          </table>
          <p class="rodape">{{ frota.length }} caminhão(ões) no filtro atual</p>
        }
      }
    </section>

    <section class="cartao">
      <header><h2>Alertas de velocidade acima de {{ limite }} km/h</h2></header>
      @if (alertas$ | async; as alertas) {
        @if (alertas.length === 0) {
          <p class="vazio">Sem alertas por enquanto.</p>
        } @else {
          <ul class="alertas">
            @for (alerta of alertas; track alerta.placa + alerta.em) {
              <li>
                <strong class="mono">{{ alerta.placa }}</strong>
                <span>{{ alerta.uf }}</span>
                <span class="grave">{{ alerta.velocidadeKmh }} km/h</span>
                <span class="quando mono">{{ alerta.em }}</span>
              </li>
            }
          </ul>
        }
      }
    </section>
  `,
})
export class FrotaComponent {
  private readonly frota = inject(FrotaService);

  /** As UFs em que a LogiTech opera, mais a opção de não filtrar. */
  readonly ufs: readonly string[] = [UF_TODAS, 'SP', 'PR', 'MG', 'RS'];
  readonly limite = LIMITE_VELOCIDADE_KMH;
  readonly ufSelecionada = signal<string>(UF_TODAS);

  readonly frotaFiltrada$ = this.frota.frotaFiltrada$;

  /**
   * Os oito alertas mais recentes.
   *
   * O serviço emite um alerta por vez; a tela precisa de uma lista. `scan`
   * faz a ponte, e `startWith` garante que o template tenha o que desenhar
   * antes do primeiro caminhão passar do limite.
   */
  readonly alertas$ = this.frota.alertas$.pipe(
    scan((lista: Alerta[], alerta: Alerta) => [alerta, ...lista].slice(0, 8), [] as Alerta[]),
    startWith([] as Alerta[]),
  );

  trocarUf(uf: string): void {
    this.ufSelecionada.set(uf);
    this.frota.definirFiltro(uf);
  }
}
