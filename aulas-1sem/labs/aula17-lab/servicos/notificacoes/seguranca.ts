// LogiTech Enterprise - validação de JWT por JWKS em Node, só com `node:crypto`.
//
// A quarta escrita do mesmo contrato, agora em TypeScript. Nenhuma dependência:
// o Node 22 importa uma chave pública no formato JWK direto e verifica RS256.
//
// Contrato (ADR-009):
//
//     LOGITECH_AUTH_ATIVA       false por padrão; a Aula 14 liga
//     LOGITECH_OIDC_ISSUER      o `iss` que o token precisa trazer
//     LOGITECH_OIDC_JWKS_URL    de onde as chaves públicas são lidas
//
// O papel viaja em `realm_access.roles`. Este arquivo lê de lá, como os
// serviços em Java, C# e Python leem. Foi para isso que a ADR-009 fixou o
// lugar: sem isso, o mesmo token autoriza numa stack e é recusado na outra.
//
// Não é tarefa. Este arquivo vem pronto.

import crypto from 'node:crypto';

export interface Veredito {
  status: 200 | 401 | 403;
  motivo: string;
  papeis: string[];
  sub?: string;
}

interface ChaveJwk {
  kid: string;
  kty: string;
  n: string;
  e: string;
  alg?: string;
}

const VALIDADE_DO_CACHE_MS = 5 * 60 * 1000;
let chaves: Map<string, crypto.KeyObject> = new Map();
let chavesLidasEm = 0;

function env(nome: string, padrao: string): string {
  const valor = process.env[nome];
  return valor === undefined || valor.trim() === '' ? padrao : valor;
}

/** A autenticação só entra em vigor com LOGITECH_AUTH_ATIVA ligada. */
export function ativa(): boolean {
  return ['1', 'true', 'sim', 'on'].includes(
    env('LOGITECH_AUTH_ATIVA', 'false').trim().toLowerCase(),
  );
}

function b64url(dado: string): Buffer {
  return Buffer.from(dado, 'base64url');
}

/**
 * Baixa e guarda as chaves públicas do provedor de identidade.
 *
 * O cache de cinco minutos é o motivo de o backend não consultar o Keycloak a
 * cada requisição: a chave muda raramente, o token traz o `kid` que diz qual
 * usar, e a verificação é local.
 */
async function carregarChaves(forcar: boolean): Promise<void> {
  if (!forcar && chaves.size > 0 && Date.now() - chavesLidasEm < VALIDADE_DO_CACHE_MS) return;

  const url = env('LOGITECH_OIDC_JWKS_URL', '');
  if (!url) throw new Error('LOGITECH_OIDC_JWKS_URL não configurada');

  const resposta = await fetch(url, { signal: AbortSignal.timeout(5000) });
  if (!resposta.ok) throw new Error(`o JWKS respondeu ${resposta.status}`);

  const documento = (await resposta.json()) as { keys?: ChaveJwk[] };
  const novas = new Map<string, crypto.KeyObject>();
  for (const chave of documento.keys ?? []) {
    if (chave.kty !== 'RSA') continue;
    novas.set(
      chave.kid,
      crypto.createPublicKey({
        key: { kty: 'RSA', n: chave.n, e: chave.e },
        format: 'jwk',
      }),
    );
  }
  if (novas.size === 0) throw new Error('o JWKS não trouxe nenhuma chave RSA');
  chaves = novas;
  chavesLidasEm = Date.now();
}

/**
 * Valida o cabeçalho `Authorization` e confere o papel.
 *
 * 401 quando não se sabe quem está chamando; 403 quando se sabe e o papel não
 * basta. A diferença entre os dois é critério do verificador da Aula 16.
 */
export async function exigir(
  cabecalho: string | undefined,
  ...aceitos: string[]
): Promise<Veredito> {
  if (!ativa()) return { status: 200, motivo: 'autenticação desligada', papeis: [] };

  if (!cabecalho || !cabecalho.toLowerCase().startsWith('bearer ')) {
    return {
      status: 401,
      motivo: 'cabeçalho Authorization ausente ou sem o esquema Bearer',
      papeis: [],
    };
  }

  const partes = cabecalho.slice(7).trim().split('.');
  if (partes.length !== 3) {
    return { status: 401, motivo: 'o token não tem as três partes de um JWT', papeis: [] };
  }

  let cabecalhoJwt: Record<string, unknown>;
  let payload: Record<string, unknown>;
  try {
    cabecalhoJwt = JSON.parse(b64url(partes[0]).toString('utf-8'));
    payload = JSON.parse(b64url(partes[1]).toString('utf-8'));
  } catch (erro) {
    return { status: 401, motivo: `token malformado: ${String(erro)}`, papeis: [] };
  }

  if (cabecalhoJwt.alg !== 'RS256') {
    return { status: 401, motivo: 'algoritmo recusado: este serviço só aceita RS256', papeis: [] };
  }

  const kid = String(cabecalhoJwt.kid ?? '');
  try {
    await carregarChaves(false);
    if (!chaves.has(kid)) await carregarChaves(true); // o provedor girou a chave
  } catch (erro) {
    return { status: 401, motivo: `não foi possível ler o JWKS: ${String(erro)}`, papeis: [] };
  }

  const chave = chaves.get(kid);
  if (!chave) return { status: 401, motivo: `kid ${kid} não está no JWKS`, papeis: [] };

  const conferiu = crypto.verify(
    'RSA-SHA256',
    Buffer.from(`${partes[0]}.${partes[1]}`, 'ascii'),
    chave,
    b64url(partes[2]),
  );
  if (!conferiu) return { status: 401, motivo: 'assinatura inválida', papeis: [] };

  const agora = Math.floor(Date.now() / 1000);
  if (typeof payload.exp === 'number' && payload.exp < agora) {
    return { status: 401, motivo: 'token expirado', papeis: [] };
  }

  const issuerEsperado = env('LOGITECH_OIDC_ISSUER', '');
  if (issuerEsperado && payload.iss !== issuerEsperado) {
    // O `iss` que o Keycloak grava é o endereço pelo qual o NAVEGADOR chegou
    // (localhost:8090); o JWKS é buscado pelo endereço da rede interna
    // (keycloak:8090). São dois valores diferentes, e é por isso que existem
    // duas variáveis em vez de uma.
    return {
      status: 401,
      motivo: `issuer divergente: o token traz ${String(payload.iss)} e este serviço espera ${issuerEsperado}`,
      papeis: [],
    };
  }

  const realm = (payload.realm_access ?? {}) as { roles?: string[] };
  const papeis = (realm.roles ?? []).map((p) => String(p).toUpperCase());

  if (aceitos.length > 0 && !aceitos.some((a) => papeis.includes(a.toUpperCase()))) {
    return {
      status: 403,
      motivo: `este token tem [${papeis.join(', ')}] e a rota exige um de [${aceitos.join(', ')}]`,
      papeis,
    };
  }

  return { status: 200, motivo: 'ok', papeis, sub: String(payload.sub ?? '') };
}
