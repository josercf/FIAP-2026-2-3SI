/**
 * Authorization Code com PKCE, escrito à mão com a Web Crypto API.
 *
 * CONGELADO. Não é tarefa da Aula 16: aqui ele já vem funcionando, e o que a
 * aula cobra é ver o fluxo acontecer e o token chegar ao backend.
 *
 * Por que PKCE, e por que sem biblioteca
 * --------------------------------------
 * Uma SPA é um *client público*: tudo que ela carrega está visível no
 * navegador, então ela não pode guardar segredo nenhum. Sem segredo, quem
 * interceptasse o `code` da barra de endereço poderia trocá-lo por um token.
 *
 * O PKCE fecha essa porta com dois valores gerados na hora:
 *
 *   code_verifier    um segredo aleatório que NUNCA sai desta aba
 *   code_challenge   o SHA-256 do verifier, que vai junto do pedido de login
 *
 * O provedor guarda o challenge e, na troca do código por token, exige o
 * verifier. Quem roubou só o código não tem o verifier e não consegue trocar.
 *
 * Escrito com `crypto.subtle` de propósito: são quarenta linhas, não acrescenta
 * dependência, e deixa as duas mensagens do fluxo visíveis para quem for ler.
 */

const AUTORIDADE: string =
  import.meta.env.VITE_OIDC_AUTORIDADE ?? 'http://localhost:8090/realms/logitech';
const CLIENT_ID: string = import.meta.env.VITE_OIDC_CLIENT_ID ?? 'logitech-portal';

const URL_AUTORIZACAO = `${AUTORIDADE}/protocol/openid-connect/auth`;
const URL_TOKEN = `${AUTORIDADE}/protocol/openid-connect/token`;
const URL_SAIDA = `${AUTORIDADE}/protocol/openid-connect/logout`;

const CHAVE_VERIFIER = 'logitech.pkce.verifier';
const CHAVE_ESTADO = 'logitech.pkce.estado';
const CHAVE_TOKEN = 'logitech.token';

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
    client_id: CLIENT_ID,
    response_type: 'code',
    scope: 'openid profile email',
    redirect_uri: window.location.origin + '/',
    state: estado,
    code_challenge: await desafioDe(verifier),
    code_challenge_method: 'S256',
  });
  window.location.assign(`${URL_AUTORIZACAO}?${parametros}`);
}

/**
 * Passo 2: de volta do Keycloak, troca o `code` por token levando o verifier.
 *
 * Devolve a sessão quando a volta traz código, e `null` quando esta carga da
 * página não é uma volta de login.
 */
export async function concluirEntrada(): Promise<Sessao | null> {
  const parametros = new URLSearchParams(window.location.search);
  const codigo = parametros.get('code');
  if (!codigo) return null;

  const estadoEsperado = sessionStorage.getItem(CHAVE_ESTADO);
  if (parametros.get('state') !== estadoEsperado) {
    limpar();
    throw new Error('state divergente na volta do login: possível adulteração');
  }

  const verifier = sessionStorage.getItem(CHAVE_VERIFIER);
  if (!verifier) throw new Error('code_verifier ausente: recomece o login');

  const corpo = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: CLIENT_ID,
    code: codigo,
    redirect_uri: window.location.origin + '/',
    code_verifier: verifier,
  });

  const resposta = await fetch(URL_TOKEN, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: corpo,
  });
  if (!resposta.ok) {
    throw new Error(`o Keycloak recusou a troca do código: HTTP ${resposta.status}`);
  }

  const dados = (await resposta.json()) as { access_token: string };
  sessionStorage.removeItem(CHAVE_VERIFIER);
  sessionStorage.removeItem(CHAVE_ESTADO);
  sessionStorage.setItem(CHAVE_TOKEN, dados.access_token);

  // Limpa `?code=...&state=...` da barra de endereço: recarregar a página com o
  // código na URL tentaria trocar duas vezes o mesmo código, e o provedor
  // recusa a segunda, com razão.
  window.history.replaceState({}, '', window.location.pathname);
  return sessaoAtual();
}

/**
 * Lê a sessão do token guardado.
 *
 * O payload é lido **só para a interface**: quem decide o que o usuário pode
 * fazer é o backend, conferindo a assinatura. Guarda de rota no frontend é
 * conforto de navegação, nunca autorização.
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
      papeis: ((payload.realm_access?.roles ?? []) as string[]).map((p) => p.toUpperCase()),
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
    client_id: CLIENT_ID,
    post_logout_redirect_uri: window.location.origin + '/',
  });
  window.location.assign(`${URL_SAIDA}?${parametros}`);
}

/** O cabeçalho que toda chamada à plataforma carrega, quando há sessão. */
export function cabecalhoDeAutorizacao(): Record<string, string> {
  const token = sessionStorage.getItem(CHAVE_TOKEN);
  return token ? { Authorization: `Bearer ${token}` } : {};
}
