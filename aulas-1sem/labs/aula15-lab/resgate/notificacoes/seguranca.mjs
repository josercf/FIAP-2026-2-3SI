// LogiTech Enterprise - camada de seguranca do servico de Notificacoes.
//
// RESGATE: esta e a versao COM a lacuna TODO-4 preenchida.
//
// Use quando travar, e nao como atalho:
//     cp resgate/notificacoes/seguranca.mjs servicos/notificacoes/seguranca.mjs
//     docker compose up -d --build notificacoes
// Registre `USEI_O_RESGATE: sim` em `docs/EVIDENCIAS.md` e siga.
//
// O ponto deste arquivo nao e escrever seguranca de novo: e escrever a MESMA
// decisao, em outra linguagem, lendo o papel DO MESMO LUGAR do token. O
// `Seguranca.java` do servico de Pedidos, em Java, le de `realm_access.roles`.
// Este aqui, em Node, tem de ler de `realm_access.roles`.
//
// Se um servico ler de `realm_access.roles` e o outro de
// `resource_access.<client>.roles`, o mesmo token, do mesmo usuario, na mesma
// requisicao, autoriza numa stack e devolve 403 na outra. Nao ha erro visivel
// em lugar nenhum: ha duas leituras diferentes de um documento correto. E o
// tipo de bug que consome uma tarde inteira, e e por isso que a ADR-009 fixa
// um lugar so.
//
// Confira sem subir nada:
//     node --test servicos/notificacoes/seguranca.test.mjs
//
// Nenhuma dependencia externa: `node:crypto` verifica RS256 a partir de uma
// chave em formato JWK desde o Node 16.

import { createPublicKey, createVerify } from 'node:crypto';

// ---------------------------------------------------------------------------
// Configuracao (contrato da ADR-009)
// ---------------------------------------------------------------------------

export const ATIVA = process.env.LOGITECH_AUTH_ATIVA === 'true';

export const JWKS_URL = process.env.LOGITECH_OIDC_JWKS_URL
  || 'http://keycloak:8090/realms/logitech/protocol/openid-connect/certs';

// Lista separada por virgula. Ver o comentario equivalente no Seguranca.java:
// o `iss` que vem dentro do token e o endereco pelo qual o NAVEGADOR falou
// com o Keycloak, e nao o endereco pelo qual este container o alcanca.
export const ISSUERS_ACEITOS = (process.env.LOGITECH_OIDC_ISSUER
  || 'http://keycloak:8090/realms/logitech').split(',').map((s) => s.trim());

const FOLGA_DE_RELOGIO_S = 30;

// ---------------------------------------------------------------------------
// Os dois jeitos de dizer nao
// ---------------------------------------------------------------------------

export class NaoAutenticado extends Error {
  constructor(motivo) { super(motivo); this.status = 401; }
}

export class SemPermissao extends Error {
  constructor(tinha, precisava) {
    super('papel insuficiente');
    this.status = 403;
    this.tinha = tinha;
    this.precisava = precisava;
  }
}

// ---------------------------------------------------------------------------
// O contrato de rotas deste servico (ADR-009)
//
//   notificacoes  GET  /health                     aberta
//                 POST /api/v1/notificacoes        ADMIN
//
// Uma rota so exigindo papel, e de proposito: e ela que produz o 403 mais
// limpo do laboratorio. O motorista Bruno passa no GET /api/v1/pedidos do
// servico Java e leva 403 aqui, com o mesmo token, na mesma sessao.
// ---------------------------------------------------------------------------

export const REGRAS = [
  { metodo: 'GET', padrao: /^\/health$/, papeis: [] },
  { metodo: 'POST', padrao: /^\/api\/v1\/notificacoes$/, papeis: ['ADMIN'] },
];

export function papeisExigidos(metodo, caminho) {
  const regra = REGRAS.find((r) => r.metodo === metodo && r.padrao.test(caminho));
  return regra ? regra.papeis : [];
}

// ---------------------------------------------------------------------------
// Verificacao da assinatura: CONGELADO, ja funciona
// ---------------------------------------------------------------------------

const chaves = new Map();
let ultimaBusca = 0;

async function chavePorKid(kid) {
  if (chaves.has(kid)) return chaves.get(kid);
  if (Date.now() - ultimaBusca < 60_000) return null;
  ultimaBusca = Date.now();

  const resp = await fetch(JWKS_URL, { signal: AbortSignal.timeout(4000) });
  if (!resp.ok) throw new NaoAutenticado(`JWKS respondeu ${resp.status} em ${JWKS_URL}`);
  const { keys } = await resp.json();
  for (const jwk of keys) {
    if (jwk.kty !== 'RSA') continue;
    if (jwk.use && jwk.use !== 'sig') continue;
    chaves.set(jwk.kid, createPublicKey({ key: jwk, format: 'jwk' }));
  }
  return chaves.get(kid) ?? null;
}

const daBase64Url = (s) => Buffer.from(s, 'base64url').toString('utf8');

/**
 * Confere assinatura, validade e emissor. Devolve o conteudo do token.
 * Lanca NaoAutenticado com um motivo legivel em qualquer recusa.
 *
 * CONGELADO: a criptografia ja esta pronta. A ordem das etapas e o que
 * importa ler aqui: enquanto a assinatura nao for conferida, todo campo do
 * payload e texto que o cliente mandou.
 */
export async function verificarToken(compacto, { agora = Math.floor(Date.now() / 1000) } = {}) {
  const partes = compacto.split('.');
  if (partes.length !== 3) {
    throw new NaoAutenticado(`formato: um JWT tem tres partes, vieram ${partes.length}`);
  }

  let cabecalho; let conteudo;
  try {
    cabecalho = JSON.parse(daBase64Url(partes[0]));
    conteudo = JSON.parse(daBase64Url(partes[1]));
  } catch {
    throw new NaoAutenticado('cabecalho ou payload nao sao base64url de JSON valido');
  }

  // O algoritmo quem decide e o servidor. Aceitar o que o token pede abre a
  // porta para `alg: none` e para a confusao de algoritmo com HS256.
  if (cabecalho.alg !== 'RS256') {
    throw new NaoAutenticado(`algoritmo '${cabecalho.alg}' recusado: este servico so aceita RS256`);
  }
  if (!cabecalho.kid) throw new NaoAutenticado("cabecalho sem 'kid'");

  const chave = await chavePorKid(cabecalho.kid);
  if (!chave) throw new NaoAutenticado(`kid '${cabecalho.kid}' nao existe no JWKS de ${JWKS_URL}`);

  const confere = createVerify('RSA-SHA256')
    .update(`${partes[0]}.${partes[1]}`)
    .verify(chave, Buffer.from(partes[2], 'base64url'));
  if (!confere) {
    throw new NaoAutenticado('assinatura invalida: o token foi adulterado ou nao veio deste realm');
  }

  if (conteudo.exp && agora > conteudo.exp + FOLGA_DE_RELOGIO_S) {
    throw new NaoAutenticado(`token expirado ha ${agora - conteudo.exp}s. Faca login de novo.`);
  }
  if (!ISSUERS_ACEITOS.includes(conteudo.iss)) {
    throw new NaoAutenticado(
      `issuer '${conteudo.iss}' nao esta na lista de confiaveis [${ISSUERS_ACEITOS.join(', ')}]. `
      + 'O token foi emitido por um endereco do Keycloak que este servico nao conhece.',
    );
  }

  return conteudo;
}

// ---------------------------------------------------------------------------
// As duas decisoes (era o TODO-4)
// ---------------------------------------------------------------------------

/**
 * Os papeis do token, lidos de `realm_access.roles`.
 *
 * Contrato:
 *   - devolve sempre um Array de strings;
 *   - token sem `realm_access` devolve `[]`, sem lancar erro;
 *   - `resource_access` NAO conta: e outro lugar do mesmo token, com os
 *     papeis de client, e neste realm ele vem vazio.
 */
export function papeisDoToken(conteudo) {
  const papeis = conteudo?.realm_access?.roles;
  return Array.isArray(papeis) ? papeis.map(String) : [];
}

/**
 * O portao deste servico.
 *
 * Recebe o metodo, o caminho e o cabecalho `Authorization` cru.
 * Devolve `{ usuario, papeis }`, ou `null` quando a rota e aberta ou a
 * autenticacao esta desligada.
 *
 * O que precisa acontecer, nesta ordem:
 *   1. `papeisExigidos(metodo, caminho)`; se vier vazio, devolva `null`;
 *   2. se `ATIVA` for falso, devolva `null` (o interruptor da ADR-009);
 *   3. tire o token de `Bearer <token>`. Sem token, ou com outro esquema,
 *      lance `new NaoAutenticado("cabecalho Authorization ausente ou fora do
 *      formato 'Bearer <token>'")`. O esquema nao diferencia maiusculas;
 *   4. `await verificarToken(compacto)`;
 *   5. `papeisDoToken(conteudo)`; se nenhum dos exigidos estiver la, lance
 *      `new SemPermissao(papeis, exigidos)`;
 *   6. devolva `{ usuario: conteudo.preferred_username, papeis }`.
 *
 * Erro classico a evitar: transformar tudo em 403. Token ausente, expirado ou
 * com assinatura errada e 401. So depois de SABER quem e que faz sentido
 * falar em permissao.
 */
export async function guarda(metodo, caminho, authorization) {
  const exigidos = papeisExigidos(metodo, caminho);
  if (exigidos.length === 0) return null;   // rota aberta, /health inclusive
  if (!ATIVA) return null;                  // o interruptor da ADR-009

  const [esquema, valor] = String(authorization ?? '').trim().split(/\s+/, 2);
  const compacto = esquema?.toLowerCase() === 'bearer' ? (valor ?? '').trim() : '';
  if (!compacto) {
    throw new NaoAutenticado("cabecalho Authorization ausente ou fora do formato 'Bearer <token>'");
  }

  const conteudo = await verificarToken(compacto);
  const papeis = papeisDoToken(conteudo);

  if (!exigidos.some((p) => papeis.includes(p))) {
    throw new SemPermissao(papeis, exigidos);
  }

  return { usuario: conteudo.preferred_username, papeis };
}
