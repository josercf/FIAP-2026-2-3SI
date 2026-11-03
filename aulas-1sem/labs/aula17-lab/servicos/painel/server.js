// LogiTech Enterprise - Painel de rastreamento (HTTP/SSE, camada L7).
//
// SERVIÇO CONGELADO. NÃO É TAREFA DESTE LABORATÓRIO.
// ==================================================
// Ele nasceu na Aula 02, perdeu a leitura de arquivo na Aula 07 e chega aqui
// pronto. O artefato da Aula 11 é o painel administrativo em Angular, dentro
// de `painel-admin/`. Não editem este arquivo.
//
// O que mudou em relação à versão da Aula 07: CORS, por causa da ADR-008.
// Até aqui todo consumidor deste serviço era outro processo de servidor, e
// servidor ignora a política de mesma origem. A partir de hoje quem consome
// é o Angular servido em http://localhost:4200, que é outra origem: porta
// diferente já basta. Sem `Access-Control-Allow-Origin` na resposta, o
// navegador recebe os bytes e os joga fora antes de o seu código vê-los.
//
// As origens permitidas vêm de LOGITECH_CORS_ORIGINS, lista separada por
// vírgula, com padrão "http://localhost:5173,http://localhost:4200".
//
// Rotas (contrato da plataforma, ADR-006):
//   GET /health            estado do painel e da fonte de telemetria
//   GET /                  a tela do operador (a versão de 2002 deste painel)
//   GET /api/v1/posicoes   última posição conhecida de cada placa
//   GET /api/v1/eventos    stream SSE das posições que forem chegando
//
// Uso:
//   node servicos/painel/server.js
//   LOGITECH_TELEMETRIA_URL=http://localhost:8082/telemetria node servicos/painel/server.js

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORTA = Number(process.env.PORTA || 3000);
const TELEMETRIA_URL = process.env.LOGITECH_TELEMETRIA_URL
  || 'http://localhost:8082/telemetria';
const INTERVALO_MS = Number(process.env.LOGITECH_INTERVALO_MS || 1000);
const PAGINA_PAINEL = path.join(__dirname, 'public', 'index.html');
const INICIADO_EM = Date.now();

const ORIGENS_PERMITIDAS = (process.env.LOGITECH_CORS_ORIGINS
  || 'http://localhost:5173,http://localhost:4200')
  .split(',')
  .map((o) => o.trim())
  .filter(Boolean);

const ROTAS_CONHECIDAS = new Set([
  '/health', '/', '/index.html', '/api/v1/posicoes', '/api/v1/eventos',
]);

// Estado observado da fonte. É o que /health reporta e o que prova, na
// correção, que a telemetria chega por HTTP e não por arquivo.
const fonte = {
  url: TELEMETRIA_URL,
  ultimoContato: null,
  ultimoErro: null,
  consultas: 0,
  falhas: 0,
};

// Quantos navegadores estão inscritos no SSE agora. É a evidência do
// laboratório de hoje: quando o componente Angular é destruído e o
// `unsubscribe` acontece, este número cai sozinho.
let assinantesSse = 0;
let assinaturasAbertas = 0;
let assinaturasFechadas = 0;

// ---------------------------------------------------------------------------
// CORS: a política de mesma origem, e a autorização explícita
// ---------------------------------------------------------------------------

/**
 * Devolve os cabeçalhos de CORS quando a origem que chamou está autorizada.
 *
 * Reflete a origem em vez de responder `*` porque `*` é incompatível com
 * credenciais e apaga a informação de quem chamou nos logs de proxy. Origem
 * desconhecida não recebe cabeçalho nenhum: quem decide o que fazer com isso
 * é o navegador, e a decisão dele é descartar a resposta.
 */
function cabecalhosCors(req) {
  const origem = req.headers.origin;
  if (!origem || !ORIGENS_PERMITIDAS.includes(origem)) return {};
  return {
    'Access-Control-Allow-Origin': origem,
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '600',
    Vary: 'Origin',
  };
}

// ---------------------------------------------------------------------------
// A fonte de telemetria: o coletor, por HTTP
// ---------------------------------------------------------------------------

/**
 * Busca a fotografia atual da frota no coletor.
 *
 * Timeout explícito de 2 segundos: sem ele, um coletor lento seguraria a
 * resposta do painel indefinidamente. Falha de rede aqui não é exceção do
 * painel, é estado de negócio ("a fonte está fora"), então devolvemos lista
 * vazia e registramos.
 */
async function buscarPosicoes() {
  const cancelamento = AbortSignal.timeout(2000);
  fonte.consultas += 1;
  try {
    const resposta = await fetch(TELEMETRIA_URL, { signal: cancelamento });
    if (!resposta.ok) {
      throw new Error(`o coletor respondeu HTTP ${resposta.status}`);
    }
    const corpo = await resposta.json();
    fonte.ultimoContato = new Date().toISOString();
    fonte.ultimoErro = null;
    return Array.isArray(corpo.posicoes) ? corpo.posicoes : [];
  } catch (erro) {
    fonte.falhas += 1;
    fonte.ultimoErro = erro.message;
    return [];
  }
}

/**
 * Observa a fonte e avisa a cada posição nova ou alterada.
 *
 * Este é o Observer Pattern em JavaScript puro, escrito à mão: uma função que
 * recebe o observador (`aoChegarPosicao`) e devolve a função de cancelamento.
 * O `Observable` do RxJS que vocês escrevem hoje tem exatamente esta forma,
 * com nomes melhores e um contrato explícito.
 */
function assistirTelemetria(aoChegarPosicao) {
  const visto = new Map();

  const cronometro = setInterval(async () => {
    const posicoes = await buscarPosicoes();
    for (const posicao of posicoes) {
      const assinatura = `${posicao.lat},${posicao.lng},${posicao.recebido_em || ''}`;
      if (visto.get(posicao.placa) === assinatura) continue;
      visto.set(posicao.placa, assinatura);
      aoChegarPosicao(posicao);
    }
  }, INTERVALO_MS);

  return () => clearInterval(cronometro);
}

function responderJson(res, status, corpo, headersExtra = {}) {
  const texto = JSON.stringify(corpo);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(texto),
    ...headersExtra,
  });
  res.end(texto);
}

// ---------------------------------------------------------------------------
// Roteamento
// ---------------------------------------------------------------------------

const servidor = http.createServer(async (req, res) => {
  const rota = new URL(req.url, `http://${req.headers.host}`).pathname;
  const cors = cabecalhosCors(req);

  // Preflight: o navegador pergunta antes de mandar a requisição de verdade.
  if (req.method === 'OPTIONS') {
    res.writeHead(204, cors);
    return res.end();
  }

  // 405 antes de tudo: a rota existe, o método é que não serve.
  if (ROTAS_CONHECIDAS.has(rota) && req.method !== 'GET') {
    return responderJson(res, 405, {
      erro: 'método não permitido',
      metodo: req.method,
      permitidos: ['GET'],
    }, { Allow: 'GET', ...cors });
  }

  if (rota === '/health') {
    return responderJson(res, 200, {
      status: 'ok',
      servico: 'painel',
      uptime_s: Math.round((Date.now() - INICIADO_EM) / 1000),
      fonte: 'http',
      telemetria_url: fonte.url,
      ultimo_contato: fonte.ultimoContato,
      ultimo_erro: fonte.ultimoErro,
      consultas: fonte.consultas,
      falhas: fonte.falhas,
      cors_origens: ORIGENS_PERMITIDAS,
      sse_assinantes: assinantesSse,
      sse_abertas: assinaturasAbertas,
      sse_fechadas: assinaturasFechadas,
    }, cors);
  }

  if (rota === '/' || rota === '/index.html') {
    const html = fs.readFileSync(PAGINA_PAINEL);
    res.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8',
      'Content-Length': html.length,
      ...cors,
    });
    return res.end(html);
  }

  if (rota === '/api/v1/posicoes') {
    const posicoes = await buscarPosicoes();
    return responderJson(res, 200, posicoes, { 'Cache-Control': 'max-age=5', ...cors });
  }

  if (rota === '/api/v1/eventos') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no', // desliga o buffer do nginx, quando houver
      ...cors,
    });

    res.write('retry: 3000\n\n');

    assinantesSse += 1;
    assinaturasAbertas += 1;
    console.log(`[SSE] assinatura aberta. assinantes agora: ${assinantesSse}`);

    let sequencia = 0;
    const emitir = (posicao) => {
      sequencia += 1;
      res.write(`id: ${sequencia}\n`);
      res.write('event: posicao\n');
      res.write(`data: ${JSON.stringify(posicao)}\n\n`);
    };

    // Estado inicial: quem abre o painel agora precisa ver a frota sem
    // esperar a próxima posição chegar.
    for (const posicao of await buscarPosicoes()) emitir(posicao);

    const pararDeAssistir = assistirTelemetria(emitir);

    // Heartbeat: comentário SSE que mantém a conexão viva atrás de proxies
    // com timeout de ociosidade.
    const batimento = setInterval(() => res.write(': ping\n\n'), 15000);

    // Sem este encerramento, cada aba fechada deixaria um observador vivo.
    // É o espelho, do lado do servidor, da função de teardown que vocês
    // escrevem hoje dentro do `new Observable(...)`.
    req.on('close', () => {
      pararDeAssistir();
      clearInterval(batimento);
      assinantesSse -= 1;
      assinaturasFechadas += 1;
      console.log(`[SSE] assinatura fechada. assinantes agora: ${assinantesSse}`);
      res.end();
    });
    return;
  }

  return responderJson(res, 404, {
    erro: 'rota não encontrada',
    rota,
    disponiveis: [...ROTAS_CONHECIDAS],
  }, cors);
});

servidor.listen(PORTA, () => {
  console.log(`[HTTP] painel de rastreamento em http://localhost:${PORTA}`);
  console.log(`[HTTP] telemetria vinda de ${TELEMETRIA_URL} (não de arquivo)`);
  console.log(`[CORS] origens permitidas: ${ORIGENS_PERMITIDAS.join(', ')}`);
});
