/**
 * A régua do TODO-5.
 *
 * CONGELADO. Roda sem Keycloak, sem rede e sem navegador de verdade: o
 * `fetch` é dublado e o `crypto` do jsdom já traz `getRandomValues` e
 * `subtle.digest`.
 *
 *     cd portal && npm test
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  AUTORIZACAO,
  RETORNO,
  base64url,
  desafioS256,
  gerarVerifier,
  sessaoDoToken,
  trocarCodigoPorToken,
  urlDeAutorizacao,
} from './pkce';

const URL_SEGURA = /^[A-Za-z0-9\-._~]+$/;

describe('TODO-5a: o code_verifier', () => {
  it('tem de 43 a 128 caracteres, como manda a RFC 7636', () => {
    const v = gerarVerifier();
    expect(v.length).toBeGreaterThanOrEqual(43);
    expect(v.length).toBeLessThanOrEqual(128);
  });

  it('usa só caracteres que sobrevivem a uma query string', () => {
    expect(gerarVerifier()).toMatch(URL_SEGURA);
  });

  it('é diferente a cada chamada, porque é aleatório', () => {
    const gerados = new Set(Array.from({ length: 20 }, () => gerarVerifier()));
    expect(gerados.size).toBe(20);
  });
});

describe('TODO-5b: o code_challenge', () => {
  // Vetor de teste do apêndice B da RFC 7636. Se o seu S256 estiver certo,
  // este verificador produz exatamente este desafio.
  const VERIFIER_DA_RFC = 'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk';
  const DESAFIO_DA_RFC = 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM';

  it('reproduz o vetor de teste da RFC 7636', async () => {
    expect(await desafioS256(VERIFIER_DA_RFC)).toBe(DESAFIO_DA_RFC);
  });

  it('não devolve o próprio verificador (isso seria o método `plain`)', async () => {
    const v = gerarVerifier();
    expect(await desafioS256(v)).not.toBe(v);
  });

  it('é base64url, sem +, / nem =', async () => {
    expect(await desafioS256(gerarVerifier())).toMatch(URL_SEGURA);
  });
});

describe('TODO-5c: a URL de autorização', () => {
  it('leva os sete parâmetros do fluxo', () => {
    const url = new URL(urlDeAutorizacao('DESAFIO', 'ESTADO'));
    expect(`${url.origin}${url.pathname}`).toBe(AUTORIZACAO);
    expect(url.searchParams.get('response_type')).toBe('code');
    expect(url.searchParams.get('client_id')).toBe('logitech-portal');
    expect(url.searchParams.get('redirect_uri')).toBe(RETORNO);
    expect(url.searchParams.get('state')).toBe('ESTADO');
    expect(url.searchParams.get('code_challenge')).toBe('DESAFIO');
    expect(url.searchParams.get('code_challenge_method')).toBe('S256');
    expect(url.searchParams.get('scope')).toContain('openid');
  });

  it('NUNCA leva o code_verifier nem segredo de cliente', () => {
    const url = urlDeAutorizacao('DESAFIO', 'ESTADO');
    expect(url).not.toContain('code_verifier');
    expect(url).not.toContain('client_secret');
  });
});

describe('TODO-5d: a troca do código pelo token', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('manda code, code_verifier e client_id, e nenhum segredo', async () => {
    const espia = vi.fn(async () => new Response(
      JSON.stringify({ access_token: 'a.b.c', expires_in: 300 }),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    ));
    vi.stubGlobal('fetch', espia);

    await trocarCodigoPorToken('CODIGO-1', 'VERIFICADOR-1');

    expect(espia).toHaveBeenCalledOnce();
    const [, init] = espia.mock.calls[0] as unknown as [string, RequestInit];
    expect(init.method).toBe('POST');
    const corpo = new URLSearchParams(String(init.body));
    expect(corpo.get('grant_type')).toBe('authorization_code');
    expect(corpo.get('code')).toBe('CODIGO-1');
    expect(corpo.get('code_verifier')).toBe('VERIFICADOR-1');
    expect(corpo.get('client_id')).toBe('logitech-portal');
    expect(corpo.get('client_secret')).toBeNull();
  });

  it('erra alto quando o Keycloak recusa', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(
      JSON.stringify({ error: 'invalid_grant' }), { status: 400 },
    )));
    await expect(trocarCodigoPorToken('X', 'Y')).rejects.toThrow();
  });
});

describe('a sessão sai de realm_access.roles', () => {
  function tokenDeMentira(conteudo: Record<string, unknown>): string {
    const parte = (o: unknown) =>
      btoa(JSON.stringify(o)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    return `${parte({ alg: 'RS256' })}.${parte(conteudo)}.assinatura`;
  }

  it('lê o usuário e os papéis do lugar certo', () => {
    const s = sessaoDoToken(tokenDeMentira({
      preferred_username: 'carla.admin',
      exp: 1893456000,
      realm_access: { roles: ['ADMIN'] },
      resource_access: { 'logitech-portal': { roles: ['NAO_E_DAQUI'] } },
    }));
    expect(s.usuario).toBe('carla.admin');
    expect(s.papeis).toEqual(['ADMIN']);
  });

  it('token sem papel nenhum não quebra a tela', () => {
    const s = sessaoDoToken(tokenDeMentira({ preferred_username: 'x', exp: 1 }));
    expect(s.papeis).toEqual([]);
  });
});

describe('base64url', () => {
  it('troca +, / e tira o preenchimento', () => {
    expect(base64url(new Uint8Array([251, 255, 190]))).toBe('-_--');
  });
});
