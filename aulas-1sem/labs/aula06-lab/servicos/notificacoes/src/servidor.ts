/**
 * API HTTP do serviço de notificações da LogiTech (Node 22, porta 3001).
 *
 * Contrato da ADR-006: `GET /health` e `POST /api/v1/notificacoes` recebendo
 * `{canal, destinatario, mensagem}`. As duas rotas extras (`/esquema` e
 * `/rastreio/:codigo`) são internas e não entram no contrato da plataforma.
 *
 * Este arquivo não é tarefa. Ele já monta a pilha de decoradores e já
 * consome o Adapter: é justamente por isso que preencher as lacunas de
 * `decoradores.ts` e `adaptador.ts` muda o comportamento do serviço sem que
 * nenhuma linha daqui mude. Essa é a tese da aula, e ela está montada aqui.
 *
 * Para subir:
 *     npm run dev
 */

import http from 'node:http';

import { AdaptadorRastreioLegado, type RastreioLegado } from './adaptador';
import { ComLog, ComRetentativa } from './decoradores';
import { canaisDisponiveis, enviadorPara } from './enviadores';
import { EsquemaNotificacao, jsonSchemaDoContrato } from './esquema';
import { LogDeConsole } from './log';
import type { Enviador } from './tipos';

const PORTA = Number(process.env.PORT ?? 3001);

/**
 * Endereço do rastreamento da parceira. Nunca cravado no código: a ADR-006
 * exige variável de ambiente com padrão de desenvolvimento local, e é o que
 * permite este mesmo serviço rodar solto e dentro do Compose da Aula 07.
 */
const URL_PARCEIRA = process.env.LOGITECH_RASTREIO_PARCEIRA_URL ?? 'http://localhost:9090';

const log = new LogDeConsole();
const adaptador = new AdaptadorRastreioLegado();

/**
 * Monta a pilha de envio de um canal: retentativa por fora, log por dentro,
 * enviador de verdade no centro.
 *
 * Ler de fora para dentro: `ComRetentativa` decide se repete; `ComLog`
 * registra cada passagem; `enviadorPara(canal)` fala com o provedor.
 */
function pilhaDeEnvio(canal: string): Enviador {
  return new ComRetentativa(new ComLog(enviadorPara(canal), log), 3, 50);
}

function responder(res: http.ServerResponse, status: number, corpo: unknown): void {
  const texto = JSON.stringify(corpo);
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': Buffer.byteLength(texto),
  });
  res.end(texto);
}

function lerCorpo(req: http.IncomingMessage): Promise<string> {
  return new Promise((resolva, rejeite) => {
    const partes: Buffer[] = [];
    req.on('data', (parte: Buffer) => partes.push(parte));
    req.on('end', () => resolva(Buffer.concat(partes).toString('utf-8')));
    req.on('error', rejeite);
  });
}

async function postNotificacoes(req: http.IncomingMessage, res: http.ServerResponse): Promise<void> {
  let json: unknown;
  try {
    json = JSON.parse(await lerCorpo(req));
  } catch {
    responder(res, 400, { erro: 'corpo não é um JSON válido' });
    return;
  }

  const validacao = EsquemaNotificacao.safeParse(json);
  if (!validacao.success) {
    responder(res, 422, {
      erro: 'notificação fora do contrato',
      detalhes: validacao.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`),
      canaisDisponiveis: canaisDisponiveis(),
    });
    return;
  }

  try {
    const resultado = await pilhaDeEnvio(validacao.data.canal).enviar(validacao.data);
    responder(res, 202, resultado);
  } catch (erro) {
    responder(res, 502, {
      erro: 'canal não conseguiu entregar a notificação',
      motivo: (erro as Error).message,
    });
  }
}

async function getRastreio(codigo: string, res: http.ServerResponse): Promise<void> {
  try {
    const resposta = await fetch(`${URL_PARCEIRA}/consulta?objeto=${encodeURIComponent(codigo)}`);
    if (!resposta.ok) {
      responder(res, 502, { erro: `parceira respondeu ${resposta.status}` });
      return;
    }
    const bruto = (await resposta.json()) as RastreioLegado;
    responder(res, 200, adaptador.adaptar(bruto));
  } catch (erro) {
    responder(res, 502, {
      erro: 'rastreamento da parceira indisponível',
      motivo: (erro as Error).message,
      dica: `confira se ${URL_PARCEIRA} está no ar (python3 servicos/parceira-rastreio/servidor.py)`,
    });
  }
}

export const servidor = http.createServer((req, res) => {
  const url = new URL(req.url ?? '/', `http://localhost:${PORTA}`);
  const rota = `${req.method} ${url.pathname}`;

  if (rota === 'GET /health') {
    responder(res, 200, { status: 'ok' });
    return;
  }
  if (rota === 'GET /api/v1/notificacoes/esquema') {
    responder(res, 200, jsonSchemaDoContrato());
    return;
  }
  if (rota === 'POST /api/v1/notificacoes') {
    void postNotificacoes(req, res);
    return;
  }
  if (req.method === 'GET' && url.pathname.startsWith('/api/v1/rastreio/')) {
    void getRastreio(url.pathname.slice('/api/v1/rastreio/'.length), res);
    return;
  }

  responder(res, 404, { erro: 'rota não encontrada', rota });
});

/* Só sobe o servidor quando o arquivo é executado direto: importado por um
   teste, ele fica quieto e a suíte não deixa porta aberta. */
if (process.argv[1]?.endsWith('servidor.ts')) {
  servidor.listen(PORTA, () => {
    log.registrar(`notificacoes ouvindo em http://localhost:${PORTA}`);
    log.registrar(`rastreamento da parceira em ${URL_PARCEIRA}`);
  });
}
