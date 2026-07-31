// LogiTech Enterprise - Serviço de Notificações (Bounded Context: Atendimento).
//
// ATENÇÃO, LEIA ANTES DE COMPARAR COM A AULA 06
// ---------------------------------------------
// Versão **mínima**, escrita para o laboratório da Aula 07 ter o que
// orquestrar. Cumpre o contrato da plataforma (ADR-006): porta 3001, as duas
// rotas e `/health` devolvendo {"status":"ok"}.
//
// O que ela **não** é: a implementação da Aula 06. Lá o serviço nasce com
// `AdaptadorRastreioLegado` traduzindo o formato da transportadora parceira e
// dois Decorators empilháveis, `ComLog` e `ComRetentativa`, que são o
// conteúdo daquela aula. Aqui há um enviador direto, porque o assunto de hoje
// é orquestração.
//
// Não é tarefa. Não editem este arquivo.
//
// Roda em Node 22 com anotação de tipo apagada em tempo de carga
// (`--experimental-strip-types`): TypeScript de verdade, sem passo de build.
//
// Rotas (ADR-006 e ADR-009):
//   GET  /health                 aberta, sempre
//   POST /api/v1/notificacoes    ADMIN
//        entra {canal, destinatario, mensagem}
//
// Versão da Aula 16: ganhou validação de JWT com RBAC (ADR-009), em
// `seguranca.ts`. Com LOGITECH_AUTH_ATIVA desligada este serviço se comporta
// exatamente como na Aula 07.

import http from 'node:http';

import { ativa, exigir } from './seguranca.ts';

type Canal = 'email' | 'sms' | 'push';

interface Notificacao {
  id: string;
  canal: Canal;
  destinatario: string;
  mensagem: string;
  enfileiradaEm: string;
}

const PORTA: number = Number(process.env.LOGITECH_PORTA ?? 3001);
const CANAIS: readonly string[] = ['email', 'sms', 'push'];
const INICIADO_EM: number = Date.now();

// Fila em memória, limitada. Sem o teto, um laço de teste enchendo a fila
// derrubaria o container por consumo de memória, e o `mem_limit` do Compose
// mataria o serviço errado aos olhos de quem está depurando.
const LIMITE_DA_FILA = 500;
const fila: Notificacao[] = [];

function responderJson(
  res: http.ServerResponse,
  status: number,
  corpo: unknown,
): void {
  const texto = JSON.stringify(corpo);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(texto),
  });
  res.end(texto);
}

async function lerCorpo(req: http.IncomingMessage): Promise<string> {
  const pedacos: Buffer[] = [];
  for await (const pedaco of req) pedacos.push(pedaco as Buffer);
  return Buffer.concat(pedacos).toString('utf-8');
}

const servidor = http.createServer(async (req, res) => {
  const rota = new URL(req.url ?? '/', `http://${req.headers.host}`).pathname;

  if (rota === '/health' && req.method === 'GET') {
    return responderJson(res, 200, {
      status: 'ok',
      servico: 'notificacoes',
      uptime_s: Math.round((Date.now() - INICIADO_EM) / 1000),
      canais: CANAIS,
      na_fila: fila.length,
      auth_ativa: ativa(),
    });
  }

  if (rota === '/api/v1/notificacoes' && req.method === 'POST') {
    // Notificar cliente em nome da LogiTech é ato de ADMIN (ADR-009). Quem
    // cria um pedido como CLIENTE recebe 403 aqui, e a `jornada` devolvida
    // pelo serviço de Pedidos registra o 403 em vez de escondê-lo.
    const veredito = await exigir(req.headers.authorization, 'ADMIN');
    if (veredito.status !== 200) {
      return responderJson(res, veredito.status, {
        erro: 'acesso negado',
        detalhe: veredito.motivo,
      });
    }

    let entrada: Record<string, unknown>;
    try {
      entrada = JSON.parse(await lerCorpo(req));
    } catch {
      return responderJson(res, 400, { erro: 'corpo não é JSON válido' });
    }

    const canal = String(entrada.canal ?? '');
    const destinatario = String(entrada.destinatario ?? '');
    const mensagem = String(entrada.mensagem ?? '');

    const faltando: string[] = [];
    if (!CANAIS.includes(canal)) faltando.push('canal');
    if (!destinatario.trim()) faltando.push('destinatario');
    if (!mensagem.trim()) faltando.push('mensagem');
    if (faltando.length > 0) {
      return responderJson(res, 400, {
        erro: 'campos obrigatórios ausentes ou inválidos',
        detalhe: faltando.join(', '),
        canais_aceitos: CANAIS,
      });
    }

    const notificacao: Notificacao = {
      id: `NT-${Date.now().toString(36)}-${fila.length}`,
      canal: canal as Canal,
      destinatario,
      mensagem,
      enfileiradaEm: new Date().toISOString(),
    };

    fila.push(notificacao);
    if (fila.length > LIMITE_DA_FILA) fila.shift();

    console.log(`[NOTIFICACAO] ${notificacao.canal} para ${notificacao.destinatario}: ${notificacao.mensagem}`);
    return responderJson(res, 202, notificacao);
  }

  return responderJson(res, 404, {
    erro: 'rota não encontrada',
    rota,
    disponiveis: ['/health', '/api/v1/notificacoes'],
  });
});

servidor.listen(PORTA, () => {
  console.log('=== LogiTech Enterprise - Serviço de Notificações ===');
  console.log(`[HTTP] notificacoes escutando na porta ${PORTA}`);
  console.log(`[AUTH] validação de token: ${ativa() ? 'exigida' : 'DESLIGADA'}`);
});
