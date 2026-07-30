// LogiTech Enterprise - Gateway HTTP/SSE de telemetria (camada L7).
//
// Este e o ESQUELETO do laboratorio da Aula 02. Ele sobe e responde, mas
// esta incompleto de proposito: os quatro blocos marcados com TODO sao seus.
//
// O que ja vem pronto e nao precisa ser alterado:
//   - lerPosicoes()          le data/telemetria.jsonl e devolve a ultima
//                            posicao de cada caminhao
//   - assistirTelemetria()   chama um callback a cada posicao nova gravada
//   - responderJson()        escreve uma resposta JSON com status e headers
//   - GET /health            exemplo completo de rota, use-o como modelo
//
// Rode com:  node http-l7/server.js
// Verifique: node http-l7/verificar.mjs

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORTA = Number(process.env.PORTA || 3000);
const ARQUIVO_TELEMETRIA = path.join(__dirname, '..', 'data', 'telemetria.jsonl');
const PAGINA_PAINEL = path.join(__dirname, 'public', 'index.html');
const INICIADO_EM = Date.now();

// ---------------------------------------------------------------------------
// Apoio pronto: leitura da telemetria gravada pelo coletor L4
// ---------------------------------------------------------------------------

/**
 * Le o arquivo inteiro e devolve a ultima posicao conhecida de cada placa.
 * @returns {Array<object>} uma posicao por caminhao, ordenada por placa
 */
function lerPosicoes() {
  if (!fs.existsSync(ARQUIVO_TELEMETRIA)) return [];

  const ultimaPorPlaca = new Map();
  const linhas = fs.readFileSync(ARQUIVO_TELEMETRIA, 'utf-8').split('\n');

  for (const linha of linhas) {
    if (!linha.trim()) continue;
    try {
      const posicao = JSON.parse(linha);
      if (posicao.placa) ultimaPorPlaca.set(posicao.placa, posicao);
    } catch {
      // linha parcial no fim do arquivo: o coletor ainda esta escrevendo
    }
  }

  return [...ultimaPorPlaca.values()].sort((a, b) => a.placa.localeCompare(b.placa));
}

/**
 * Observa o arquivo de telemetria e chama o callback para cada linha nova.
 * @param {(posicao: object) => void} aoChegarPosicao
 * @returns {() => void} funcao que encerra a observacao
 */
function assistirTelemetria(aoChegarPosicao) {
  let deslocamento = fs.existsSync(ARQUIVO_TELEMETRIA)
    ? fs.statSync(ARQUIVO_TELEMETRIA).size
    : 0;
  let resto = '';

  const cronometro = setInterval(() => {
    if (!fs.existsSync(ARQUIVO_TELEMETRIA)) return;
    const tamanho = fs.statSync(ARQUIVO_TELEMETRIA).size;
    if (tamanho <= deslocamento) {
      deslocamento = tamanho; // arquivo truncado ou recriado
      return;
    }

    const descritor = fs.openSync(ARQUIVO_TELEMETRIA, 'r');
    const buffer = Buffer.alloc(tamanho - deslocamento);
    fs.readSync(descritor, buffer, 0, buffer.length, deslocamento);
    fs.closeSync(descritor);
    deslocamento = tamanho;

    const linhas = (resto + buffer.toString('utf-8')).split('\n');
    resto = linhas.pop();

    for (const linha of linhas) {
      if (!linha.trim()) continue;
      try {
        aoChegarPosicao(JSON.parse(linha));
      } catch {
        // linha invalida: ignora e segue
      }
    }
  }, 500);

  return () => clearInterval(cronometro);
}

/** Escreve uma resposta JSON completa. */
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

const servidor = http.createServer((req, res) => {
  const rota = new URL(req.url, `http://${req.headers.host}`).pathname;

  // --- Exemplo completo. Use este bloco como modelo para os TODO. ---
  if (rota === '/health') {
    if (req.method !== 'GET') {
      return responderJson(res, 405, { erro: 'metodo nao permitido' }, { Allow: 'GET' });
    }
    return responderJson(res, 200, {
      servico: 'telemetria-logitech',
      status: 'no ar',
      uptime: Math.round((Date.now() - INICIADO_EM) / 1000),
      caminhoes: lerPosicoes().length,
    });
  }

  // Painel do operador, servido pronto.
  if (rota === '/' || rota === '/index.html') {
    if (req.method !== 'GET') {
      return responderJson(res, 405, { erro: 'metodo nao permitido' }, { Allow: 'GET' });
    }
    const html = fs.readFileSync(PAGINA_PAINEL);
    res.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8',
      'Content-Length': html.length,
    });
    return res.end(html);
  }

  // -------------------------------------------------------------------------
  // TODO 1: GET /api/v1/posicoes
  //
  //   Devolver 200 com a lista de lerPosicoes() em JSON.
  //   Exigencias: Content-Type de JSON e Cache-Control: max-age=5
  //   (o RNF de latencia do SDD tolera 5 segundos de defasagem na consulta).
  //   Dica: responderJson(res, 200, lerPosicoes(), { 'Cache-Control': ... })
  // -------------------------------------------------------------------------

  // -------------------------------------------------------------------------
  // TODO 2: GET /api/v1/eventos  (Server-Sent Events)
  //
  //   1. res.writeHead(200, { ... }) com:
  //        Content-Type: text/event-stream
  //        Cache-Control: no-cache
  //        Connection: keep-alive
  //   2. Enviar 'retry: 3000\n\n' logo de cara.
  //   3. Para cada posicao nova vinda de assistirTelemetria(), escrever:
  //        id: <numero sequencial>
  //        event: posicao
  //        data: <JSON da posicao>
  //        <LINHA EM BRANCO>
  //      Sem a linha em branco final o navegador nunca dispara o evento.
  //   4. Em req.on('close', ...), parar de observar o arquivo.
  //      Sem isso cada aba aberta deixa um observador vivo para sempre.
  // -------------------------------------------------------------------------

  // -------------------------------------------------------------------------
  // TODO 3: 405 Method Not Allowed
  //
  //   Se a rota e /api/v1/posicoes ou /api/v1/eventos mas o metodo nao e GET,
  //   responder 405 com o header Allow: GET. Nao responder 404: a rota existe.
  // -------------------------------------------------------------------------

  // -------------------------------------------------------------------------
  // TODO 4: 404 Not Found
  //
  //   Qualquer outra rota devolve 404 com um corpo JSON explicando o erro.
  //   Nunca devolver 200 com {"erro": ...}: isso apaga a informacao de status.
  // -------------------------------------------------------------------------

  responderJson(res, 501, {
    erro: 'rota ainda nao implementada',
    dica: 'complete os TODO de http-l7/server.js',
    rota,
  });
});

servidor.listen(PORTA, () => {
  console.log(`[HTTP] gateway de telemetria em http://localhost:${PORTA}`);
  console.log(`[HTTP] lendo ${ARQUIVO_TELEMETRIA}`);
});

module.exports = { lerPosicoes, assistirTelemetria, responderJson };
