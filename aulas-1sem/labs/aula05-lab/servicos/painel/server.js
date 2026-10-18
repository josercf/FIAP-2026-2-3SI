// LogiTech Enterprise - Gateway HTTP/SSE de telemetria (camada L7).
//
// Serviço congelado da Aula 02 para a Aula 03: o caminho de dados é
// configurável pela variável de ambiente LOGITECH_DADOS. Quando ela não é
// definida, o padrão é "dados/telemetria.jsonl" na raiz do laboratório (dois
// níveis acima de servicos/gateway/, o mesmo nível de servicos/), não dentro
// da pasta deste serviço. Isso é o que faz o coletor e o gateway, rodados
// soltos e sem variável nenhuma, enxergarem o mesmo arquivo: se cada um
// resolvesse a própria pasta, o coletor gravaria em servicos/coletor/dados/
// e o gateway leria de servicos/gateway/dados/, dois arquivos diferentes, e
// o painel mostraria zero caminhão mesmo com o coletor funcionando. O
// caminho continua gravável sem privilégio especial (é dentro do checkout
// do repositório) e não depende de onde o aluno estava quando chamou o
// comando, porque é derivado da localização do próprio arquivo, não do
// diretório corrente. Os Dockerfiles do laboratório fixam essa variável
// para um caminho absoluto dentro do container (/dados/telemetria.jsonl);
// é o container, não o código, quem decide onde os dados moram lá dentro.
//
// Uso:
//   node servicos/gateway/server.js
//   LOGITECH_DADOS=/tmp/t.jsonl node servicos/gateway/server.js

const http = require('http');
const fs = require('fs');
const path = require('path');

const DIR_SERVICO = __dirname;
const RAIZ_LAB = path.dirname(path.dirname(DIR_SERVICO));

const PORTA = Number(process.env.PORTA || 3000);
const CAMINHO_DADOS = process.env.LOGITECH_DADOS || path.join(RAIZ_LAB, 'dados', 'telemetria.jsonl');
const PAGINA_PAINEL = path.join(__dirname, 'public', 'index.html');
const INICIADO_EM = Date.now();

const ROTAS_CONHECIDAS = new Set(['/health', '/', '/index.html', '/api/v1/posicoes', '/api/v1/eventos']);

// ---------------------------------------------------------------------------
// Apoio: leitura da telemetria gravada pelo coletor L4
// ---------------------------------------------------------------------------

function lerPosicoes() {
  if (!fs.existsSync(CAMINHO_DADOS)) return [];

  const ultimaPorPlaca = new Map();
  const linhas = fs.readFileSync(CAMINHO_DADOS, 'utf-8').split('\n');

  for (const linha of linhas) {
    if (!linha.trim()) continue;
    try {
      const posicao = JSON.parse(linha);
      if (posicao.placa) ultimaPorPlaca.set(posicao.placa, posicao);
    } catch {
      // linha parcial no fim do arquivo
    }
  }

  return [...ultimaPorPlaca.values()].sort((a, b) => a.placa.localeCompare(b.placa));
}

function assistirTelemetria(aoChegarPosicao) {
  let deslocamento = fs.existsSync(CAMINHO_DADOS)
    ? fs.statSync(CAMINHO_DADOS).size
    : 0;
  let resto = '';

  const cronometro = setInterval(() => {
    if (!fs.existsSync(CAMINHO_DADOS)) return;
    const tamanho = fs.statSync(CAMINHO_DADOS).size;
    if (tamanho <= deslocamento) {
      deslocamento = tamanho;
      return;
    }

    const descritor = fs.openSync(CAMINHO_DADOS, 'r');
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
        // linha inválida
      }
    }
  }, 500);

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

const servidor = http.createServer((req, res) => {
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
    return responderJson(res, 200, {
      servico: 'telemetria-logitech',
      status: 'no ar',
      uptime: Math.round((Date.now() - INICIADO_EM) / 1000),
      caminhoes: lerPosicoes().length,
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

  // TODO 1 resolvido: consulta pontual, com cache curto.
  if (rota === '/api/v1/posicoes') {
    return responderJson(res, 200, lerPosicoes(), { 'Cache-Control': 'max-age=5' });
  }

  // TODO 2 resolvido: stream SSE.
  if (rota === '/api/v1/eventos') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no', // desliga o buffer do nginx, quando houver
    });

    res.write('retry: 3000\n\n');

    let sequencia = 0;

    // Estado inicial: o operador que abre o painel agora precisa ver a frota
    // sem esperar a próxima posição chegar.
    for (const posicao of lerPosicoes()) {
      sequencia += 1;
      res.write(`id: ${sequencia}\n`);
      res.write('event: posicao\n');
      res.write(`data: ${JSON.stringify(posicao)}\n\n`);
    }

    const pararDeAssistir = assistirTelemetria((posicao) => {
      sequencia += 1;
      res.write(`id: ${sequencia}\n`);
      res.write('event: posicao\n');
      res.write(`data: ${JSON.stringify(posicao)}\n\n`);
    });

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

  // TODO 4 resolvido.
  return responderJson(res, 404, {
    erro: 'rota não encontrada',
    rota,
    disponiveis: [...ROTAS_CONHECIDAS],
  });
});

servidor.listen(PORTA, () => {
  console.log(`[HTTP] gateway de telemetria em http://localhost:${PORTA}`);
  console.log(`[HTTP] lendo ${CAMINHO_DADOS}`);
});
