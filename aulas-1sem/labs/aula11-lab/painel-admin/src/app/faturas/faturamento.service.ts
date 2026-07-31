import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
// `debounceTime`, `distinctUntilChanged` e `switchMap` já estão importados e
// ainda não são usados: é o TODO-6 que os coloca em serviço.
import {
  catchError,
  debounceTime,
  distinctUntilChanged,
  filter,
  map,
  mergeMap,
  switchMap,
} from 'rxjs/operators';

import { AMBIENTE } from '../nucleo/ambiente';
import { Fatura, ResultadoDaConsulta } from '../nucleo/modelos';

/** Silêncio de digitação, em milissegundos, antes de consultar o servidor. */
export const ESPERA_DE_DIGITACAO_MS = 300;

/**
 * A consulta de fatura no serviço de Faturamento (C#/.NET, porta 5080,
 * nascido na Aula 05).
 *
 * Este é o outro lado do painel, e ele é deliberadamente diferente do fluxo
 * de frota: aqui não existe nada chegando sozinho. Existe um operador
 * digitando um número de pedido, e uma resposta por consulta. O que torna o
 * caso interessante é a **corrida**: o serviço demora, o operador continua
 * digitando, e a resposta da tecla antiga pode chegar depois da resposta da
 * tecla nova.
 *
 * Uma lacuna mora aqui: TODO-6. E o TODO-1 depende deste arquivo.
 */
// TODO-1a -------------------------------------------------------------------
// Um `@Injectable()` sem `providedIn` declara que a classe é injetável e não
// diz a ninguém onde encontrá-la. O `inject(FaturamentoService)` do
// componente estoura NullInjectorError.
//
// Complete o decorador com `{ providedIn: 'root' }`.
@Injectable()
export class FaturamentoService {
  /**
   * O `HttpClient` entregue pelo injetor.
   *
   * É o mesmo Dependency Injection da Aula 05, com uma diferença que vale
   * nomear: lá o contêiner era uma biblioteca (Spring, o contêiner do .NET);
   * aqui ele é parte do framework, e a "interface" pedida é a própria classe.
   * O que não muda é o princípio: a classe declara o que precisa e não sabe
   * quem constrói.
   */
  private readonly http = inject(HttpClient);

  /**
   * Uma consulta, uma resposta. Já vem pronto.
   *
   * O `catchError` transforma 404 em `null` de propósito: pedido inexistente
   * é resposta de negócio, não falha de infraestrutura. Sem ele, o primeiro
   * número inválido digitado mataria o fluxo inteiro, e o campo de busca
   * pararia de funcionar até o operador recarregar a página.
   */
  buscarUma(pedidoId: string): Observable<ResultadoDaConsulta> {
    return this.http
      .get<Fatura>(`${AMBIENTE.faturamentoUrl}/api/v1/faturas/${pedidoId}`)
      .pipe(catchError(() => of(null)));
  }

  // ---------------------------------------------------------------------------
  // TODO-6: a busca em tempo real, sem corrida
  // ---------------------------------------------------------------------------
  /**
   * Recebe o fluxo do que o operador está digitando e devolve o fluxo de
   * faturas encontradas.
   *
   * O que está aqui embaixo **funciona e está errado**, e é assim de
   * propósito: é o "antes" que vocês vão medir. Ele dispara uma requisição
   * por tecla e deixa todas correrem juntas, então a fatura do `100` pode
   * chegar depois da fatura do `1003` e sobrescrever a tela com o resultado
   * antigo.
   *
   * Reescreva o encadeamento nesta ordem, e a ordem importa:
   *
   *   map(termo => termo.trim())
   *   debounceTime(ESPERA_DE_DIGITACAO_MS)   espera o operador parar de digitar
   *   distinctUntilChanged()                 ignora o termo repetido
   *   filter(termo => termo.length > 0)      campo vazio não consulta nada
   *   switchMap(termo => this.buscarUma(termo))
   *
   * `switchMap` **cancela a inscrição anterior** ao receber um valor novo.
   * Cancelar a inscrição de uma requisição HTTP do Angular aborta a
   * requisição de verdade: o navegador fecha a conexão, e o serviço de
   * Faturamento contabiliza a consulta como cancelada em
   * `GET /api/v1/metricas`. É essa contagem que vocês vão registrar em
   * `docs/EVIDENCIAS.md`.
   */
  consultar(termos$: Observable<string>): Observable<ResultadoDaConsulta> {
    // TODO-6: substitua o encadeamento abaixo pelo descrito acima.
    return termos$.pipe(
      map((termo) => termo.trim()),
      filter((termo) => termo.length > 0),
      mergeMap((termo) => this.buscarUma(termo)),
    );
  }
}
