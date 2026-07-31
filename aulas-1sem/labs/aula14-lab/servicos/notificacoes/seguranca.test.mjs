// LogiTech Enterprise - suite do TODO-4, em `node:test`.
//
// CONGELADO: nao e tarefa do laboratorio, e a sua regua.
//
// Roda SEM Keycloak e sem rede: o teste gera um par de chaves RSA na hora,
// sobe um JWKS de mentira em 127.0.0.1 e assina os proprios tokens.
//
//     node --test servicos/notificacoes/seguranca.test.mjs
//
// Nao ha `npm install`: `node:test`, `node:crypto` e `node:http` vem com o
// Node 22.

import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';
import { createServer } from 'node:http';
import { createSign, generateKeyPairSync } from 'node:crypto';

const EMISSOR = 'http://localhost:8090/realms/logitech';
const OUTRO_EMISSOR = 'http://keycloak:8090/realms/logitech';
const KID = 'chave-de-teste-1';

const { privateKey, publicKey } = generateKeyPairSync('rsa', { modulusLength: 2048 });
const jwk = { ...publicKey.export({ format: 'jwk' }), kid: KID, alg: 'RS256', use: 'sig' };

const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');

function assinar(conteudo, cabecalho = { alg: 'RS256', typ: 'JWT', kid: KID }) {
  const base = `${b64(cabecalho)}.${b64(conteudo)}`;
  const assinatura = createSign('RSA-SHA256').update(base).sign(privateKey);
  return `${base}.${assinatura.toString('base64url')}`;
}

function token({ usuario = 'carla.admin', papeis = ['ADMIN'], iss = EMISSOR, validadeS = 300 } = {}) {
  const agora = Math.floor(Date.now() / 1000);
  return assinar({
    iss,
    sub: '00000000-0000-0000-0000-0000000000aa',
    azp: 'logitech-portal',
    typ: 'Bearer',
    preferred_username: usuario,
    iat: agora,
    exp: agora + validadeS,
    realm_access: { roles: papeis },
  });
}

let jwks;
let seg;
let segEstrito;

before(async () => {
  jwks = createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ keys: [jwk] }));
  });
  await new Promise((ok) => jwks.listen(0, '127.0.0.1', ok));
  const porta = jwks.address().port;

  process.env.LOGITECH_AUTH_ATIVA = 'true';
  process.env.LOGITECH_OIDC_JWKS_URL = `http://127.0.0.1:${porta}/certs`;

  // Modulo 1: aceita os DOIS enderecos, que e o conserto do issuer divergente.
  process.env.LOGITECH_OIDC_ISSUER = `${EMISSOR},${OUTRO_EMISSOR}`;
  seg = await import('./seguranca.mjs');

  // Modulo 2: aceita so o endereco de rede, que e o estado em que o problema
  // do issuer aparece. A query no caminho quebra o cache de modulo do Node e
  // faz o arquivo ser avaliado de novo, com o outro ambiente.
  process.env.LOGITECH_OIDC_ISSUER = OUTRO_EMISSOR;
  segEstrito = await import('./seguranca.mjs?estrito=1');
});

after(() => jwks.close());

describe('TODO-4a: o papel vem de realm_access.roles', () => {
  it('le a lista de realm_access.roles', () => {
    assert.deepEqual(seg.papeisDoToken({ realm_access: { roles: ['ADMIN', 'CLIENTE'] } }),
                     ['ADMIN', 'CLIENTE']);
  });

  it('ignora resource_access, que e outro lugar do mesmo token', () => {
    const conteudo = {
      realm_access: { roles: ['CLIENTE'] },
      resource_access: { 'logitech-portal': { roles: ['ADMIN'] } },
    };
    assert.deepEqual(seg.papeisDoToken(conteudo), ['CLIENTE']);
  });

  it('token sem realm_access devolve lista vazia, sem lancar', () => {
    assert.deepEqual(seg.papeisDoToken({}), []);
    assert.deepEqual(seg.papeisDoToken({ realm_access: {} }), []);
  });
});

describe('TODO-4b: 401 e 403 sao coisas diferentes', () => {
  it('rota aberta passa sem token', async () => {
    assert.equal(await seg.guarda('GET', '/health', undefined), null);
  });

  it('sem cabecalho Authorization e 401', async () => {
    await assert.rejects(
      () => seg.guarda('POST', '/api/v1/notificacoes', undefined),
      (e) => e.status === 401,
    );
  });

  it('cabecalho com outro esquema e 401', async () => {
    await assert.rejects(
      () => seg.guarda('POST', '/api/v1/notificacoes', 'Basic dXNlcjpzZW5oYQ=='),
      (e) => e.status === 401,
    );
  });

  it('esquema em minusculas vale, porque a RFC 7235 nao diferencia caixa', async () => {
    const quem = await seg.guarda('POST', '/api/v1/notificacoes', `bearer ${token()}`);
    assert.equal(quem.usuario, 'carla.admin');
  });

  it('token expirado e 401, nao 403', async () => {
    await assert.rejects(
      () => seg.guarda('POST', '/api/v1/notificacoes', `Bearer ${token({ validadeS: -600 })}`),
      (e) => e.status === 401,
    );
  });

  it('payload trocado com a assinatura antiga e 401', async () => {
    const [cab, , sig] = token({ papeis: ['CLIENTE'] }).split('.');
    const forjado = [cab, b64({ ...JSON.parse(Buffer.from(cab, 'base64url')), realm_access: { roles: ['ADMIN'] } }), sig].join('.');
    await assert.rejects(
      () => seg.guarda('POST', '/api/v1/notificacoes', `Bearer ${forjado}`),
      (e) => e.status === 401,
    );
  });

  it('ADMIN dispara notificacao', async () => {
    const quem = await seg.guarda('POST', '/api/v1/notificacoes', `Bearer ${token()}`);
    assert.deepEqual(quem.papeis, ['ADMIN']);
  });

  it('MOTORISTA com token perfeitamente valido leva 403', async () => {
    const t = token({ usuario: 'bruno.motorista', papeis: ['MOTORISTA'] });
    await assert.rejects(
      () => seg.guarda('POST', '/api/v1/notificacoes', `Bearer ${t}`),
      (e) => e.status === 403 && e.tinha.includes('MOTORISTA') && e.precisava.includes('ADMIN'),
    );
  });

  it('CLIENTE tambem leva 403: so ADMIN dispara notificacao', async () => {
    const t = token({ usuario: 'ana.cliente', papeis: ['CLIENTE'] });
    await assert.rejects(
      () => seg.guarda('POST', '/api/v1/notificacoes', `Bearer ${t}`),
      (e) => e.status === 403,
    );
  });
});

describe('o issuer divergente', () => {
  it('com so o endereco de rede na lista, o token do navegador e recusado', async () => {
    await assert.rejects(
      () => segEstrito.guarda('POST', '/api/v1/notificacoes', `Bearer ${token()}`),
      (e) => e.status === 401 && /issuer/.test(e.message),
    );
  });

  it('com os dois enderecos na lista, o mesmo token passa', async () => {
    const quem = await seg.guarda('POST', '/api/v1/notificacoes', `Bearer ${token()}`);
    assert.equal(quem.usuario, 'carla.admin');
  });
});
