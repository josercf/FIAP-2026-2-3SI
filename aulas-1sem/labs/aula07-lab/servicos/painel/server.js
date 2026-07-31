// LogiTech Enterprise - Painel de rastreamento (HTTP/SSE, camada L7).
//
// Serviço congelado das Aulas 02 e 03, **evoluído nesta aula**. Não é tarefa:
// não editem este arquivo. O artefato de hoje é o docker-compose.yml.
//
// A dívida da ADR-002, paga aqui
// ------------------------------
//
// Até a Aula 03 este serviço fazia `fs.readFileSync(LOGITECH_DADOS)`: ele e o
// coletor precisavam enxergar o mesmo arquivo, no mesmo volume, com o mesmo
// caminho. A ADR-002 registrou isso como simplificação deliberada e marcou a
// Aula 07 como o ponto de substituição.
//
// Não existe mais nenhuma leitura de arquivo aqui. O painel agora chama
// `GET /telemetria` no coletor, endereço vindo de LOGITECH_TELEMETRIA_URL. O
// que era acoplamento de sistema de arquivos virou **contrato de API**:
//
//   antes   coletor --grava--> /dados/telemetria.jsonl <--lê-- painel
//           (os dois precisam do mesmo volume montado no mesmo caminho)
//
//   depois  coletor --expõe--> GET :8082/telemetria <--chama-- painel
//           (o painel não sabe onde o coletor guarda nada, e nem precisa)
//
// Consequência prática, visível no laboratório de hoje: o serviço `painel`
// no Compose **não monta volume nenhum**. Se você montou, não terminou o
// Passo 3.
//
// Rotas (contrato da plataforma, ADR-006):
//   GET /health            estado do painel e da fonte de telemetria
//   GET /                  a tela do operador
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

// ---------------------------------------------------------------------------
// A nova fonte de telemetria: o coletor, por HTTP
// ---------------------------------------------------------------------------

/**
 * Busca a fotografia atual da frota no coletor.
 *
 * Timeout explícito de 2 segundos: sem ele, um coletor lento seguraria a
 * resposta do painel indefinidamente, e o healthcheck do Compose derrubaria
 * o serviço errado. Falha de rede aqui não é exceção do painel, é estado de
 * negócio ("a fonte está fora"), então devolvemos lista vazia e registramos.
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
 * O coletor devolve a fotografia inteira; o painel guarda a assinatura de
 * cada placa e só emite evento quando algo mudou de fato. Sem essa
 * comparação, cada aba aberta receberia a frota inteira de novo a cada
 * segundo, e o SSE viraria um relógio, não um fluxo de eventos.
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

  // 405 antes de tudo: a rota existe, o método é que não serve.
  if (ROTAS_CONHECIDAS.has(rota) && req.method !== 'GET') {
    return responderJson(res, 405, {
      erro: 'método não permitido',
      metodo: req.method,
      permitidos: ['GET'],
    }, { Allow: 'GET' });
  }

  if (rota === '/health') {
    // "fonte: http" é a evidência de que a dívida da ADR-002 foi paga: este
    // campo diria "arquivo" na versão da Aula 03. O verificador do
    // laboratório lê exatamente isto no Passo 3.
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
    });
  }

  if (rota === '/' || rota === '/index.html') {
    const html = fs.readFileSync(PAGINA_PAINEL);
    res.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8',
      'Content-Length': html.length,
    });
    return res.end(html);
  }

  if (rota === '/api/v1/posicoes') {
    const posicoes = await buscarPosicoes();
    return responderJson(res, 200, posicoes, { 'Cache-Control': 'max-age=5' });
  }

  if (rota === '/api/v1/eventos') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no', // desliga o buffer do nginx, quando houver
    });

    res.write('retry: 3000\n\n');

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
    req.on('close', () => {
      pararDeAssistir();
      clearInterval(batimento);
      res.end();
    });
    return;
  }

  return responderJson(res, 404, {
    erro: 'rota não encontrada',
    rota,
    disponiveis: [...ROTAS_CONHECIDAS],
  });
});

servidor.listen(PORTA, () => {
  console.log(`[HTTP] painel de rastreamento em http://localhost:${PORTA}`);
  console.log(`[HTTP] telemetria vinda de ${TELEMETRIA_URL} (não de arquivo)`);
});
