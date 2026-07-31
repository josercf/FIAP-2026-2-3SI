/**
 * Authorization Code com PKCE para o painel administrativo.
 *
 * CONGELADO. Não é tarefa da Aula 16.
 *
 * É o mesmo fluxo do Portal em React, com um `client_id` diferente
 * (`logitech-painel-admin`) e a mesma tese: SPA é *client público*, não guarda
 * segredo, e o par verifier/challenge é o que impede que quem interceptou o
 * código consiga trocá-lo por um token.
 *
 * Está escrito em TypeScript puro, sem nada de Angular, de propósito: o fluxo
 * é do OAuth, não do framework. O que o Angular acrescenta é o interceptador
 * de `autorizacao.ts`, que carimba o cabeçalho em toda requisição sem que
 * nenhum service precise lembrar disso.
 */

import { AMBIENTE } from './ambiente';

const URL_AUTORIZACAO = `${AMBIENTE.oidcAutoridade}/protocol/openid-connect/auth`;
const URL_TOKEN = `${AMBIENTE.oidcAutoridade}/protocol/openid-connect/token`;
const URL_SAIDA = `${AMBIENTE.oidcAutoridade}/protocol/openid-connect/logout`;

const CHAVE_VERIFIER = 'logitech.admin.pkce.verifier';
const CHAVE_ESTADO = 'logitech.admin.pkce.estado';
const CHAVE_TOKEN = 'logitech.admin.token';

export interface Sessao {
  token: string;
  usuario: string;
  papeis: string[];
  expiraEm: number;
}

function base64url(bytes: Uint8Array): string {
  let texto = '';
  bytes.forEach((b) => {
    texto += String.fromCharCode(b);
  });
  return btoa(texto).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function aleatorio(tamanho: number): string {
  return base64url(crypto.getRandomValues(new Uint8Array(tamanho)));
}

async function desafioDe(verifier: string): Promise<string> {
  const resumo = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
  return base64url(new Uint8Array(resumo));
}

/** Passo 1: manda o navegador ao Keycloak, levando o challenge. */
export async function entrar(): Promise<void> {
  const verifier = aleatorio(48);
  const estado = aleatorio(16);
  sessionStorage.setItem(CHAVE_VERIFIER, verifier);
  sessionStorage.setItem(CHAVE_ESTADO, estado);

  const parametros = new URLSearchParams({
    client_id: AMBIENTE.oidcClientId,
    response_type: 'code',
    scope: 'openid profile email',
    redirect_uri: window.location.origin + '/',
    state: estado,
    code_challenge: await desafioDe(verifier),
    code_challenge_method: 'S256',
  });
  window.location.assign(`${URL_AUTORIZACAO}?${parametros}`);
}

/** Passo 2: de volta do Keycloak, troca o `code` por token levando o verifier. */
export async function concluirEntrada(): Promise<Sessao | null> {
  const parametros = new URLSearchParams(window.location.search);
  const codigo = parametros.get('code');
  if (!codigo) return null;

  if (parametros.get('state') !== sessionStorage.getItem(CHAVE_ESTADO)) {
    limpar();
    throw new Error('state divergente na volta do login: possível adulteração');
  }
  const verifier = sessionStorage.getItem(CHAVE_VERIFIER);
  if (!verifier) throw new Error('code_verifier ausente: recomece o login');

  const resposta = await fetch(URL_TOKEN, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: AMBIENTE.oidcClientId,
      code: codigo,
      redirect_uri: window.location.origin + '/',
      code_verifier: verifier,
    }),
  });
  if (!resposta.ok) {
    throw new Error(`o Keycloak recusou a troca do código: HTTP ${resposta.status}`);
  }

  const dados = (await resposta.json()) as { access_token: string };
  sessionStorage.removeItem(CHAVE_VERIFIER);
  sessionStorage.removeItem(CHAVE_ESTADO);
  sessionStorage.setItem(CHAVE_TOKEN, dados.access_token);
  window.history.replaceState({}, '', window.location.pathname);
  return sessaoAtual();
}

/**
 * Lê a sessão do token guardado.
 *
 * O payload é lido só para a interface. Quem autoriza é o `faturamento` em C#,
 * conferindo a assinatura: as rotas de fatura exigem ADMIN, e um token de
 * CLIENTE vira 403 mesmo com a tela inteira montada.
 */
export function sessaoAtual(): Sessao | null {
  const token = sessionStorage.getItem(CHAVE_TOKEN);
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    if (payload.exp * 1000 < Date.now()) {
      limpar();
      return null;
    }
    return {
      token,
      usuario: String(payload.preferred_username ?? payload.sub ?? 'desconhecido'),
      papeis: ((payload.realm_access?.roles ?? []) as string[]).map((p: string) => p.toUpperCase()),
      expiraEm: payload.exp,
    };
  } catch {
    limpar();
    return null;
  }
}

export function limpar(): void {
  sessionStorage.removeItem(CHAVE_TOKEN);
  sessionStorage.removeItem(CHAVE_VERIFIER);
  sessionStorage.removeItem(CHAVE_ESTADO);
}

export function sair(): void {
  limpar();
  const parametros = new URLSearchParams({
    client_id: AMBIENTE.oidcClientId,
    post_logout_redirect_uri: window.location.origin + '/',
  });
  window.location.assign(`${URL_SAIDA}?${parametros}`);
}

/** O token cru, para o interceptador carimbar. */
export function tokenAtual(): string | null {
  return sessionStorage.getItem(CHAVE_TOKEN);
}
