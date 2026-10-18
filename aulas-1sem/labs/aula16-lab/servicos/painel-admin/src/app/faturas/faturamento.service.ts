import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import {
  catchError,
  debounceTime,
  distinctUntilChanged,
  filter,
  map,
  switchMap,
} from 'rxjs/operators';

import { AMBIENTE } from '../nucleo/ambiente';
import { Fatura, ResultadoDaConsulta } from '../nucleo/modelos';

/**
 * RESGATE dos TODO-1a e TODO-6.
 * Veja `resgate/README.md` antes de copiar.
 */

/** Silêncio de digitação, em milissegundos, antes de consultar o servidor. */
export const ESPERA_DE_DIGITACAO_MS = 300;

// TODO-1a resolvido: `providedIn: 'root'` registra a classe no injetor raiz,
// e o `inject(FaturamentoService)` do componente passa a encontrá-la.
@Injectable({ providedIn: 'root' })
export class FaturamentoService {
  private readonly http = inject(HttpClient);

  buscarUma(pedidoId: string): Observable<ResultadoDaConsulta> {
    return this.http
      .get<Fatura>(`${AMBIENTE.faturamentoUrl}/api/v1/faturas/${pedidoId}`)
      .pipe(catchError(() => of(null)));
  }

  // TODO-6 resolvido ---------------------------------------------------------
  //
  // A ordem dos operadores é a metade da resposta:
  //
  //   map antes de debounceTime  para o silêncio ser medido sobre o termo
  //                              já aparado
  //   distinctUntilChanged depois do debounce, senão ele compararia teclas
  //                              intermediárias que nunca virariam consulta
  //   filter antes do switchMap  para o campo vazio não chegar a virar URL
  //   switchMap por último       é ele que troca de inscrição, e trocar de
  //                              inscrição num HttpClient aborta a requisição
  consultar(termos$: Observable<string>): Observable<ResultadoDaConsulta> {
    return termos$.pipe(
      map((termo) => termo.trim()),
      debounceTime(ESPERA_DE_DIGITACAO_MS),
      distinctUntilChanged(),
      filter((termo) => termo.length > 0),
      switchMap((termo) => this.buscarUma(termo)),
    );
  }
}
