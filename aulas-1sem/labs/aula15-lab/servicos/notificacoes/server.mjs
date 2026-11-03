// LogiTech Enterprise - Servico de Notificacoes (Bounded Context: Atendimento).
//
// CONGELADO: nao e tarefa do laboratorio. O que voce escreve esta em
// `seguranca.mjs`, e este arquivo so o chama.
//
// Node 22, sem dependencia nenhuma: `node:http` e `node:crypto` bastam.
// Contrato da plataforma (ADR-006 e ADR-009):
//
//   GET  /health                aberta
//   POST /api/v1/notificacoes   ADMIN
//        entra {canal, destinatario, mensagem}

import { createServer } from 'node:http';
import {
  ATIVA, ISSUERS_ACEITOS, JWKS_URL, NaoAutenticado, SemPermissao, guarda,
} from './seguranca.mjs';

const PORTA = Number(process.env.LOGITECH_PORTA || 3001);
const CANAIS = new Set(['email', 'sms', 'whatsapp', 'push']);
const ENVIADAS = [];

function responder(res, codigo, corpo) {
  const texto = JSON.stringify(corpo);
  res.writeHead(codigo, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(texto),
  });
  res.end(texto);
}

async function corpoDe(req) {
  const partes = [];
  for await (const p of req) partes.push(p);
  return JSON.parse(Buffer.concat(partes).toString('utf8') || '{}');
}

const servidor = createServer(async (req, res) => {
  const caminho = new URL(req.url, 'http://interno').pathname;

  let quem = null;
  try {
    quem = await guarda(req.method, caminho, req.headers.authorization);
  } catch (erro) {
    if (erro instanceof NaoAutenticado) {
      res.setHeader('WWW-Authenticate', 'Bearer realm="logitech", error="invalid_token"');
      return responder(res, 401, {
        erro: 'nao_autenticado',
        motivo: erro.message,
        comoResolver: 'obtenha um token pelo fluxo Authorization Code + PKCE e mande no '
                      + 'cabecalho Authorization: Bearer <token>',
      });
    }
    if (erro instanceof SemPermissao) {
      return responder(res, 403, {
        erro: 'sem_permissao',
        papeisQueVoceTem: erro.tinha,
        papeisAceitos: erro.precisava,
        comoResolver: 'repetir o login NAO resolve: este usuario nao tem o papel.',
      });
    }
    return responder(res, 500, { erro: 'falha_interna', detalhe: String(erro.message) });
  }

  if (req.method === 'GET' && caminho === '/health') {
    return responder(res, 200, { status: 'ok', servico: 'notificacoes', autenticacaoAtiva: ATIVA });
  }

  if (req.method === 'POST' && caminho === '/api/v1/notificacoes') {
    let corpo;
    try {
      corpo = await corpoDe(req);
    } catch {
      return responder(res, 400, { erro: 'json_invalido' });
    }
    const ausentes = ['canal', 'destinatario', 'mensagem'].filter((c) => !corpo[c]);
    if (ausentes.length) return responder(res, 400, { erro: 'campos_ausentes', campos: ausentes });
    if (!CANAIS.has(corpo.canal)) {
      return responder(res, 400, { erro: 'canal_invalido', aceitos: [...CANAIS] });
    }

    const registro = {
      notificacaoId: `NOT-${1000 + ENVIADAS.length}`,
      canal: corpo.canal,
      destinatario: corpo.destinatario,
      enviadaEm: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
      disparadaPor: quem ? quem.usuario : 'anonimo',
    };
    ENVIADAS.push(registro);
    console.log(`[notificacoes] ${registro.canal} para ${registro.destinatario} `
                + `por ${registro.disparadaPor}`);
    return responder(res, 201, registro);
  }

  return responder(res, 404, { erro: 'rota_desconhecida', caminho });
});

servidor.listen(PORTA, () => {
  console.log(`[notificacoes] no ar na porta ${PORTA}`);
  console.log(`[notificacoes] autenticacao ativa: ${ATIVA}`);
  console.log(`[notificacoes] issuers aceitos: ${ISSUERS_ACEITOS.join(', ')}`);
  console.log(`[notificacoes] jwks: ${JWKS_URL}`);
  if (!ATIVA) {
    console.log('[notificacoes] AVISO: LOGITECH_AUTH_ATIVA desligada. '
                + 'Qualquer um dispara notificacao, como nas Aulas 06 a 12.');
  }
});
