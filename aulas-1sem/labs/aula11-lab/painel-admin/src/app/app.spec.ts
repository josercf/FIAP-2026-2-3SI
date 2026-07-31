import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { App } from './app';
import { ABRIR_FONTE_DE_EVENTOS, FonteDeEventos } from './nucleo/fonte-de-eventos';

/** Fonte de eventos inerte: o teste da casca não é o teste do fluxo. */
class FonteInerte implements FonteDeEventos {
  addEventListener(): void {
    // não emite nada de propósito
  }
  close(): void {
    // nada a fechar
  }
}

/**
 * Teste de fumaça da casca: o painel monta, com os dois blocos no lugar.
 *
 * Repare no que os `providers` dizem: o teste troca a fonte SSE e o backend
 * HTTP por versões de teste, e nenhum componente ou serviço precisou saber
 * disso. É a resposta da Pergunta de Verificação 2 acontecendo na prática.
 */
describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ABRIR_FONTE_DE_EVENTOS, useValue: () => new FonteInerte() },
      ],
    }).compileComponents();
  });

  it('monta a casca com o bloco de frota e o de faturas', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';

    expect(texto).toContain('Painel administrativo');
    expect(texto).toContain('Frota em operação');
    expect(texto).toContain('Consulta de fatura');

    fixture.destroy();
  });
});
