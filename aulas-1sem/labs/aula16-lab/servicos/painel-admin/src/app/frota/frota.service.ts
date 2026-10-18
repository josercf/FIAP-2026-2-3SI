import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, combineLatest } from 'rxjs';
import { filter, map, scan, share, shareReplay } from 'rxjs/operators';

import { AMBIENTE } from '../nucleo/ambiente';
import { ABRIR_FONTE_DE_EVENTOS } from '../nucleo/fonte-de-eventos';
import { acumularPorPlaca, ordenarPorPlaca } from '../nucleo/acumulador';
import { Alerta, Posicao } from '../nucleo/modelos';

/**
 * RESGATE dos TODO-2, TODO-3, TODO-4 e TODO-5.
 * Veja `resgate/README.md` antes de copiar.
 */

/** Acima disto, o caminhão vira alerta na tela do operador. */
export const LIMITE_VELOCIDADE_KMH = 90;

/** Valor do filtro que significa "não filtre nada". */
export const UF_TODAS = 'TODAS';

@Injectable({ providedIn: 'root' })
export class FrotaService {
  private readonly abrirFonte = inject(ABRIR_FONTE_DE_EVENTOS);

  readonly urlDeEventos = `${AMBIENTE.painelUrl}/api/v1/eventos`;

  // TODO-5a resolvido: BehaviorSubject guarda o valor atual, então quem se
  // inscreve depois recebe o filtro em vigor sem esperar o próximo clique.
  private readonly filtroUf = new BehaviorSubject<string>(UF_TODAS);

  readonly filtroUf$: Observable<string> = this.filtroUf.asObservable();

  readonly eventos$: Observable<Posicao> = this.criarFluxoDeEventos().pipe(share());

  readonly frota$: Observable<Posicao[]> = this.montarFrota().pipe(
    shareReplay({ bufferSize: 1, refCount: true }),
  );

  readonly alertas$: Observable<Alerta> = this.montarAlertas();

  readonly frotaFiltrada$: Observable<Posicao[]> = this.montarFrotaFiltrada();

  definirFiltro(uf: string): void {
    this.filtroUf.next(uf);
  }

  // TODO-2 resolvido ---------------------------------------------------------
  private criarFluxoDeEventos(): Observable<Posicao> {
    return new Observable<Posicao>((inscrito) => {
      const fonte = this.abrirFonte(this.urlDeEventos);

      fonte.addEventListener('posicao', (evento) => {
        inscrito.next(JSON.parse(evento.data) as Posicao);
      });

      fonte.addEventListener('error', () => {
        inscrito.error(new Error(`fluxo de telemetria interrompido em ${this.urlDeEventos}`));
      });

      // A função de teardown. Sem ela, cada componente destruído deixaria
      // uma conexão SSE viva no serviço `painel`.
      return () => fonte.close();
    });
  }

  // TODO-3 resolvido ---------------------------------------------------------
  private montarFrota(): Observable<Posicao[]> {
    return this.eventos$.pipe(
      scan(acumularPorPlaca, new Map<string, Posicao>()),
      map(ordenarPorPlaca),
    );
  }

  // TODO-4 resolvido ---------------------------------------------------------
  private montarAlertas(): Observable<Alerta> {
    return this.eventos$.pipe(
      filter((posicao) => posicao.velocidade_kmh > LIMITE_VELOCIDADE_KMH),
      map((posicao) => ({
        placa: posicao.placa,
        uf: posicao.uf,
        velocidadeKmh: posicao.velocidade_kmh,
        em: posicao.recebido_em ?? '',
      })),
    );
  }

  // TODO-5b resolvido --------------------------------------------------------
  private montarFrotaFiltrada(): Observable<Posicao[]> {
    return combineLatest([this.frota$, this.filtroUf$]).pipe(
      map(([frota, uf]) => (uf === UF_TODAS ? frota : frota.filter((p) => p.uf === uf))),
    );
  }
}
