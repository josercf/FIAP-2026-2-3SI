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
 * Monta um JWT de mentira, só com o payload que a interface lê.
 *
 * Assinatura falsa de propósito, e isso não enfraquece o teste: quem confere
 * assinatura é o backend, com a chave pública do Keycloak. O que este arquivo
 * testa é o comportamento da casca diante de uma sessão, e para isso o payload
 * basta. Um token que o backend aceitasse não deixaria o teste mais forte:
 * deixaria o teste dependente de um Keycloak no ar.
 */
function tokenDeMentira(papeis: string[]): string {
  const b64 = (objeto: unknown) =>
    btoa(JSON.stringify(objeto)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  return [
    b64({ alg: 'RS256', kid: 'teste' }),
    b64({
      preferred_username: 'carla.admin',
      exp: Math.floor(Date.now() / 1000) + 3600,
      realm_access: { roles: papeis },
    }),
    'assinatura-de-mentira',
  ].join('.');
}

describe('App', () => {
  beforeEach(async () => {
    sessionStorage.clear();
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ABRIR_FONTE_DE_EVENTOS, useValue: () => new FonteInerte() },
      ],
    }).compileComponents();
  });

  afterEach(() => sessionStorage.clear());

  it('sem sessão, oferece o login e não monta as colunas', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';

    expect(texto).toContain('Painel administrativo');
    expect(texto).toContain('Entrar com a conta LogiTech');
    expect(texto).not.toContain('Frota em operação');

    fixture.destroy();
  });

  it('com sessão, monta a casca com o bloco de frota e o de faturas', () => {
    sessionStorage.setItem('logitech.admin.token', tokenDeMentira(['ADMIN']));

    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';

    expect(texto).toContain('carla.admin');
    expect(texto).toContain('Frota em operação');
    expect(texto).toContain('Consulta de fatura');

    fixture.destroy();
  });
});
