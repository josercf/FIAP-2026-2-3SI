import { HttpClient, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Subject, Subscription } from 'rxjs';

import { appConfig } from '../app.config';
import { CABECALHO_CORRELACAO } from '../nucleo/correlacao';
import { ResultadoDaConsulta } from '../nucleo/modelos';
import { ESPERA_DE_DIGITACAO_MS, FaturamentoService } from './faturamento.service';

const URL_BASE = 'http://localhost:5080/api/v1/faturas';
const URL_METRICAS = 'http://localhost:5080/api/v1/metricas';

describe('TODO-1: injeção de dependências', () => {
  it('o FaturamentoService é resolvido sem ser listado em providers', () => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });

    expect(() => TestBed.inject(FaturamentoService)).not.toThrow();
  });

  it('o injetor raiz monta a cadeia HTTP com o interceptador de correlação', () => {
    TestBed.configureTestingModule({
      providers: [...appConfig.providers, provideHttpClientTesting()],
    });
    const rede = TestBed.inject(HttpTestingController);

    TestBed.inject(HttpClient).get(URL_METRICAS).subscribe({ error: () => undefined });

    expect(rede.expectOne(URL_METRICAS).request.headers.has(CABECALHO_CORRELACAO)).toBe(true);
  });

  it('cada requisição sai com um identificador de correlação diferente', () => {
    TestBed.configureTestingModule({
      providers: [...appConfig.providers, provideHttpClientTesting()],
    });
    const http = TestBed.inject(HttpClient);
    const rede = TestBed.inject(HttpTestingController);

    http.get(`${URL_BASE}/1001`).subscribe({ error: () => undefined });
    http.get(`${URL_BASE}/1002`).subscribe({ error: () => undefined });

    const carimbos = rede
      .match(() => true)
      .map((r) => r.request.headers.get(CABECALHO_CORRELACAO));

    expect(carimbos.length).toBe(2);
    expect(carimbos[0]).not.toBe(carimbos[1]);
  });
});

describe('TODO-6: a busca em tempo real', () => {
  let servico: FaturamentoService;
  let rede: HttpTestingController;
  let termos: Subject<string>;
  let recebidos: ResultadoDaConsulta[];
  const inscricoes: Subscription[] = [];

  beforeEach(() => {
    // Relógio virtual: o `debounceTime` agenda no `asyncScheduler`, que usa
    // `setInterval`. Sem isso, cada teste esperaria 300 ms de verdade.
    vi.useFakeTimers();

    TestBed.configureTestingModule({
      // O serviço entra explicitamente aqui para que este bloco não dependa
      // do TODO-1: cada critério é cobrado por si.
      providers: [provideHttpClient(), provideHttpClientTesting(), FaturamentoService],
    });

    servico = TestBed.inject(FaturamentoService);
    rede = TestBed.inject(HttpTestingController);
    termos = new Subject<string>();
    recebidos = [];
    inscricoes.push(servico.consultar(termos.asObservable()).subscribe((r) => recebidos.push(r)));
  });

  afterEach(() => {
    while (inscricoes.length) inscricoes.pop()?.unsubscribe();
    vi.useRealTimers();
  });

  it('não consulta nada enquanto o operador ainda está digitando', () => {
    termos.next('1');
    termos.next('10');
    termos.next('100');
    vi.advanceTimersByTime(ESPERA_DE_DIGITACAO_MS - 1);

    rede.expectNone(() => true);
  });

  it('consulta uma vez só, com o termo final, depois do silêncio', () => {
    termos.next('1');
    termos.next('10');
    termos.next('100');
    termos.next('1003');
    vi.advanceTimersByTime(ESPERA_DE_DIGITACAO_MS);

    const pedidas = rede.match(() => true);
    expect(pedidas.length).toBe(1);
    expect(pedidas[0].request.url).toBe(`${URL_BASE}/1003`);
  });

  it('apara os espaços antes de consultar', () => {
    termos.next('  1005  ');
    vi.advanceTimersByTime(ESPERA_DE_DIGITACAO_MS);

    expect(rede.match(() => true)[0].request.url).toBe(`${URL_BASE}/1005`);
  });

  it('não consulta com o campo vazio', () => {
    termos.next('1001');
    vi.advanceTimersByTime(ESPERA_DE_DIGITACAO_MS);
    rede.match(() => true);

    termos.next('   ');
    vi.advanceTimersByTime(ESPERA_DE_DIGITACAO_MS);

    rede.expectNone(() => true);
  });

  it('ignora o termo repetido, sem consultar de novo', () => {
    termos.next('1002');
    vi.advanceTimersByTime(ESPERA_DE_DIGITACAO_MS);
    expect(rede.match(() => true).length).toBe(1);

    termos.next('1002');
    vi.advanceTimersByTime(ESPERA_DE_DIGITACAO_MS);

    rede.expectNone(() => true);
  });

  it('cancela a consulta anterior quando um termo novo chega', () => {
    termos.next('1001');
    vi.advanceTimersByTime(ESPERA_DE_DIGITACAO_MS);
    const primeira = rede.expectOne(`${URL_BASE}/1001`);

    termos.next('1002');
    vi.advanceTimersByTime(ESPERA_DE_DIGITACAO_MS);
    const segunda = rede.expectOne(`${URL_BASE}/1002`);

    // É esta linha que separa switchMap de mergeMap. Com mergeMap as duas
    // requisições correm até o fim, e `cancelled` fica falso.
    expect(primeira.cancelled).toBe(true);
    expect(segunda.cancelled).toBe(false);
  });

  it('entrega a fatura encontrada a quem estiver inscrito', () => {
    termos.next('1004');
    vi.advanceTimersByTime(ESPERA_DE_DIGITACAO_MS);

    rede.expectOne(`${URL_BASE}/1004`).flush({
      pedidoId: 1004,
      numero: 'NF-00000004',
      cliente: 'Distribuidora Sul Alimentos',
      valor: 7655.2,
      emitidaEm: '2026-10-01T12:00:00+00:00',
    });

    expect(recebidos.length).toBe(1);
    expect(recebidos[0]?.cliente).toBe('Distribuidora Sul Alimentos');
  });

  it('pedido inexistente vira null, e o fluxo continua vivo', () => {
    termos.next('9999');
    vi.advanceTimersByTime(ESPERA_DE_DIGITACAO_MS);
    rede.expectOne(`${URL_BASE}/9999`).flush(
      { erro: 'fatura não encontrada' },
      { status: 404, statusText: 'Not Found' },
    );

    termos.next('1001');
    vi.advanceTimersByTime(ESPERA_DE_DIGITACAO_MS);
    rede.expectOne(`${URL_BASE}/1001`).flush({
      pedidoId: 1001,
      numero: 'NF-00000001',
      cliente: 'Supermercados Aurora',
      valor: 4820.5,
      emitidaEm: '2026-10-01T12:00:00+00:00',
    });

    expect(recebidos.length).toBe(2);
    expect(recebidos[0]).toBeNull();
    expect(recebidos[1]?.cliente).toBe('Supermercados Aurora');
  });
});
