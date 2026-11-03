/**
 * Authorization Code + PKCE no navegador.
 *
 * RESGATE: esta é a versão COM a lacuna TODO-5 preenchida.
 *
 * Use quando travar, e não como atalho:
 *     cp resgate/portal/pkce.ts portal/src/auth/pkce.ts
 * Registre `USEI_O_RESGATE: sim` em `docs/EVIDENCIAS.md` e siga.
 *
 * No Passo 3 você fez este fluxo à mão, com o `pkce.py`, e viu cada
 * parâmetro. Aqui ele vira código de produção: as mesmas quatro peças, em
 * TypeScript, rodando dentro do navegador.
 *
 * Duas coisas que este arquivo NÃO faz, e não é esquecimento:
 *
 *   1. não guarda `client_secret`. O portal é um client público. Qualquer
 *      segredo embutido numa SPA está visível na aba de rede, o que faz dele
 *      exatamente o contrário de um segredo. É esse buraco que o PKCE fecha;
 *
 *   2. não valida a assinatura do token. Quem valida é o backend, contra o
 *      JWKS. O navegador só carrega o token de um lado para o outro.
 *
 * Confira sem subir nada:
 *     cd portal && npm test
 */

/** O endereço pelo qual o NAVEGADOR alcança o Keycloak. */
const KEYCLOAK: string =
  import.meta.env.VITE_KEYCLOAK_URL ?? 'http://localhost:8090';
const REALM = 'logitech';
const CLIENT_ID: string =
  import.meta.env.VITE_OIDC_CLIENT_ID ?? 'logitech-portal';

export const AUTORIZACAO = `${KEYCLOAK}/realms/${REALM}/protocol/openid-connect/auth`;
export const TOKEN = `${KEYCLOAK}/realms/${REALM}/protocol/openid-connect/token`;
export const SAIDA = `${KEYCLOAK}/realms/${REALM}/protocol/openid-connect/logout`;

/** A URI de retorno precisa estar registrada no realm, byte a byte. */
export const RETORNO = `${window.location.origin}/`;

export interface Sessao {
  accessToken: string;
  expiraEm: number; // epoch em segundos
  usuario: string;
  papeis: string[];
}

// ---------------------------------------------------------------------------
// Ferramentas: CONGELADAS, já funcionam
// ---------------------------------------------------------------------------

/**
 * base64url sem o preenchimento `=`, como manda a RFC 7636.
 *
 * `btoa` devolve base64 comum, com `+`, `/` e `=`. Nenhum dos três sobrevive
 * a uma query string sem escape, e é por isso que o padrão exige a variante
 * url-safe. Trocar os três caracteres é literalmente toda a diferença.
 */
export function base64url(bytes: Uint8Array): string {
  let bruto = '';
  bytes.forEach((b) => {
    bruto += String.fromCharCode(b);
  });
  return btoa(bruto).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/** Decodifica uma das três partes de um JWT. Não valida nada. */
export function decodificarParte(parte: string): Record<string, unknown> {
  const normal = parte.replace(/-/g, '+').replace(/_/g, '/');
  const preenchido = normal + '='.repeat((4 - (normal.length % 4)) % 4);
  return JSON.parse(decodeURIComponent(escape(atob(preenchido))));
}

// ---------------------------------------------------------------------------
// TODO-5a: o par verificador/desafio
// ---------------------------------------------------------------------------

/**
 * O `code_verifier` (era o TODO-5a).
 *
 * Contrato (RFC 7636, seção 4.1):
 *   - aleatório criptograficamente seguro, e não `Math.random()`;
 *   - entre 43 e 128 caracteres do alfabeto url-safe.
 *
 * 48 bytes viram 64 caracteres, que está dentro da faixa.
 */
export function gerarVerifier(): string {
  return base64url(crypto.getRandomValues(new Uint8Array(48)));
}

/**
 * O `code_challenge` (era o TODO-5b).
 *
 * Contrato: `base64url(SHA-256(verifier))`, que é o método `S256`.
 *
 * Existe também o método `plain`, em que o desafio é o próprio verificador.
 * Ele está no padrão por compatibilidade e não serve para nada aqui: quem
 * interceptar o desafio na URL fica com o verificador de graça. O realm da
 * LogiTech exige `S256`, e o Keycloak recusa `plain`.
 *
 */
export async function desafioS256(verifier: string): Promise<string> {
  const resumo = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(verifier),
  );
  return base64url(new Uint8Array(resumo));
}

// ---------------------------------------------------------------------------
// TODO-5c: a ida
// ---------------------------------------------------------------------------

/**
 * A URL de autorização (era o TODO-5c).
 *
 * Parâmetros exigidos, todos na query string:
 *   client_id, response_type=code, scope=openid profile email,
 *   redirect_uri, state, code_challenge, code_challenge_method=S256
 *
 * `URLSearchParams` e não concatenação: o `redirect_uri` tem `:` e `/` e
 * precisa ser escapado.
 *
 * O `state` não é decoração. Ele é o que permite reconhecer, na volta, que
 * a resposta pertence à requisição que ESTE navegador iniciou. Sem ele, um
 * terceiro consegue empurrar um código de autorização dele para a sua
 * sessão, e você termina logado na conta do atacante sem perceber.
 */
export function urlDeAutorizacao(desafio: string, estado: string): string {
  const parametros = new URLSearchParams({
    client_id: CLIENT_ID,
    response_type: 'code',
    scope: 'openid profile email',
    redirect_uri: RETORNO,
    state: estado,
    code_challenge: desafio,
    code_challenge_method: 'S256',
  });
  return `${AUTORIZACAO}?${parametros.toString()}`;
}

// ---------------------------------------------------------------------------
// TODO-5d: a volta
// ---------------------------------------------------------------------------

/**
 * A troca do código pelo token (era o TODO-5d).
 *
 * `POST` para `TOKEN`, corpo `application/x-www-form-urlencoded` com:
 *   grant_type=authorization_code, client_id, code, redirect_uri, code_verifier
 *
 * Repare no que NÃO vai: senha e segredo de cliente. O que prova que quem
 * está trocando o código é quem o pediu é o `code_verifier`, e ele nunca
 * passou pela URL.
 *
 * Devolva a resposta JSON do Keycloak (`access_token`, `expires_in`, ...).
 * Em caso de erro, lance `new Error` com o corpo devolvido: a mensagem do
 * Keycloak diz exatamente o que faltou.
 */
export async function trocarCodigoPorToken(
  codigo: string,
  verifier: string,
): Promise<{ access_token: string; expires_in: number }> {
  const corpo = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: CLIENT_ID,
    code: codigo,
    redirect_uri: RETORNO,
    code_verifier: verifier,
  });

  const resposta = await fetch(TOKEN, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: corpo.toString(),
  });

  if (!resposta.ok) {
    const detalhe = await resposta.text();
    throw new Error(`o Keycloak recusou a troca (${resposta.status}): ${detalhe}`);
  }
  return (await resposta.json()) as { access_token: string; expires_in: number };
}

// ---------------------------------------------------------------------------
// Montagem da sessão: CONGELADA
// ---------------------------------------------------------------------------

/**
 * Lê do token o que a interface precisa mostrar.
 *
 * Os papéis vêm de `realm_access.roles`, o MESMO lugar de onde o serviço
 * Java e o serviço Node leem. Se a tela lesse de outro lugar, o botão
 * apareceria para quem o backend vai recusar, e o usuário levaria um 403 de
 * um botão que a própria aplicação ofereceu.
 *
 * Isto NÃO é segurança: é conveniência de interface. Esconder um botão não
 * protege rota nenhuma, porque qualquer um monta a requisição à mão. A
 * segurança de verdade acontece nos dois serviços de backend.
 */
export function sessaoDoToken(accessToken: string, ): Sessao {
  const conteudo = decodificarParte(accessToken.split('.')[1]) as {
    preferred_username?: string;
    exp: number;
    realm_access?: { roles?: string[] };
  };
  return {
    accessToken,
    expiraEm: conteudo.exp,
    usuario: conteudo.preferred_username ?? '(sem nome)',
    papeis: conteudo.realm_access?.roles ?? [],
  };
}
