/**
 * A cola entre o fluxo PKCE e a interface.
 *
 * CONGELADO. Não é tarefa do laboratório: o que você escreve está em
 * `pkce.ts`. Este arquivo só decide QUANDO chamar cada peça e onde guardar
 * o que precisa sobreviver ao redirecionamento.
 *
 * O ponto sutil: entre o clique em "Entrar" e a volta do Keycloak, a página
 * é DESCARREGADA. Nenhuma variável de JavaScript sobrevive a isso. O
 * `code_verifier` e o `state` precisam estar em algum lugar que atravesse o
 * redirecionamento, e é para isso que o `sessionStorage` serve aqui.
 *
 * `sessionStorage` e não `localStorage`: o dado morre quando a aba fecha, e
 * não fica em disco esperando a próxima pessoa que usar aquele computador.
 */

import {
  RETORNO,
  SAIDA,
  type Sessao,
  base64url,
  desafioS256,
  gerarVerifier,
  sessaoDoToken,
  trocarCodigoPorToken,
  urlDeAutorizacao,
} from './pkce';

const CHAVE_VERIFIER = 'logitech.pkce.verifier';
const CHAVE_ESTADO = 'logitech.pkce.state';

/** Começa o fluxo: leva o navegador para a tela de login do Keycloak. */
export async function entrar(): Promise<void> {
  const verifier = gerarVerifier();
  if (!verifier || verifier.length < 43) {
    throw new Error(
      'TODO-5a: gerarVerifier() precisa devolver de 43 a 128 caracteres aleatorios',
    );
  }
  const estado = base64url(crypto.getRandomValues(new Uint8Array(12)));
  const desafio = await desafioS256(verifier);
  if (!desafio) {
    throw new Error('TODO-5b: desafioS256() ainda nao foi implementado');
  }

  sessionStorage.setItem(CHAVE_VERIFIER, verifier);
  sessionStorage.setItem(CHAVE_ESTADO, estado);

  const url = urlDeAutorizacao(desafio, estado);
  if (!url) {
    throw new Error('TODO-5c: urlDeAutorizacao() ainda nao foi implementada');
  }
  window.location.assign(url);
}

/**
 * Fecha o fluxo, se a URL atual for a volta do Keycloak.
 *
 * Devolve a sessão quando havia um código para trocar, e `null` quando a
 * página abriu normalmente.
 */
export async function concluirRetorno(): Promise<Sessao | null> {
  const parametros = new URLSearchParams(window.location.search);
  const codigo = parametros.get('code');
  if (!codigo) return null;

  const estadoEsperado = sessionStorage.getItem(CHAVE_ESTADO);
  const verifier = sessionStorage.getItem(CHAVE_VERIFIER);
  sessionStorage.removeItem(CHAVE_ESTADO);
  sessionStorage.removeItem(CHAVE_VERIFIER);

  // Limpa a barra de endereços: código de autorização não fica no histórico
  // do navegador nem no Referer da próxima requisição.
  window.history.replaceState({}, '', RETORNO);

  if (parametros.get('state') !== estadoEsperado) {
    throw new Error(
      'state divergente: a resposta nao pertence ao pedido que esta aba iniciou',
    );
  }
  if (!verifier) {
    throw new Error('o code_verifier sumiu do sessionStorage');
  }

  const resposta = await trocarCodigoPorToken(codigo, verifier);
  return sessaoDoToken(resposta.access_token);
}

/** Encerra a sessão no Keycloak e volta para o portal. */
export function sair(): void {
  const parametros = new URLSearchParams({ post_logout_redirect_uri: RETORNO,
    client_id: import.meta.env.VITE_OIDC_CLIENT_ID ?? 'logitech-portal' });
  window.location.assign(`${SAIDA}?${parametros.toString()}`);
}
