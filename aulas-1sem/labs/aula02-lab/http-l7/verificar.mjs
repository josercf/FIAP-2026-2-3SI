// Verificacao dos criterios de aceitacao da Aula 02.
//
// Rode com o servidor no ar e o coletor alimentando a telemetria:
//   node http-l7/verificar.mjs
//
// Sai com codigo 1 se algum criterio falhar. Pull Request com verificacao
// vermelha nao passa na revisao.

const BASE = process.env.BASE || 'http://localhost:3000';
const resultados = [];

function registrar(id, descricao, passou, detalhe = '') {
  resultados.push({ id, descricao, passou, detalhe });
  const marca = passou ? 'PASSOU' : 'FALHOU';
  console.log(`[${marca}] ${id}  ${descricao}`);
  if (detalhe) console.log(`         ${detalhe}`);
}

async function verificarHealth() {
  try {
    const res = await fetch(`${BASE}/health`);
    const tipo = res.headers.get('content-type') || '';
    const corpo = await res.json();
    const ok = res.status === 200
      && tipo.includes('application/json')
      && typeof corpo.uptime === 'number';
    registrar('CA-01', 'GET /health devolve 200 JSON com uptime numerico', ok,
      ok ? '' : `status=${res.status} content-type=${tipo} uptime=${corpo.uptime}`);
  } catch (erro) {
    registrar('CA-01', 'GET /health devolve 200 JSON com uptime numerico', false, String(erro));
  }
}

async function verificarPosicoes() {
  try {
    const res = await fetch(`${BASE}/api/v1/posicoes`);
    const tipo = res.headers.get('content-type') || '';
    const cache = res.headers.get('cache-control') || '';
    const corpo = await res.json();
    const eLista = Array.isArray(corpo);
    const quantidade = eLista ? corpo.length : 0;
    const temPlaca = eLista && corpo.every((p) => typeof p.placa === 'string');

    const ok = res.status === 200
      && tipo.includes('application/json')
      && cache.includes('max-age')
      && quantidade >= 5
      && temPlaca;

    registrar('CA-02', 'GET /api/v1/posicoes: 200, array com 5 ou mais caminhoes, Cache-Control com max-age', ok,
      ok ? '' : `status=${res.status} cache-control="${cache}" itens=${quantidade} placas=${temPlaca}`);
  } catch (erro) {
    registrar('CA-02', 'GET /api/v1/posicoes: 200, array com 5 ou mais caminhoes, Cache-Control com max-age', false, String(erro));
  }
}

async function verificarSse() {
  const controle = new AbortController();
  const limite = setTimeout(() => controle.abort(), 9000);

  try {
    const res = await fetch(`${BASE}/api/v1/eventos`, { signal: controle.signal });
    const tipo = res.headers.get('content-type') || '';
    const cache = res.headers.get('cache-control') || '';

    const cabecalhosOk = res.status === 200
      && tipo.includes('text/event-stream')
      && cache.includes('no-cache');
    registrar('CA-03', 'GET /api/v1/eventos: 200 com text/event-stream e no-cache', cabecalhosOk,
      cabecalhosOk ? '' : `status=${res.status} content-type="${tipo}" cache-control="${cache}"`);

    let acumulado = '';
    const marcasDeTempo = [];
    const leitor = res.body.getReader();
    const decodificador = new TextDecoder();

    while (marcasDeTempo.length < 3) {
      const { value, done } = await leitor.read();
      if (done) break;
      acumulado += decodificador.decode(value, { stream: true });

      let corte;
      while ((corte = acumulado.indexOf('\n\n')) !== -1) {
        const bloco = acumulado.slice(0, corte);
        acumulado = acumulado.slice(corte + 2);
        if (bloco.includes('data:')) marcasDeTempo.push(Date.now());
      }
    }
    clearTimeout(limite);
    controle.abort();

    const blocosCompletos = marcasDeTempo.length >= 2;
    registrar('CA-04', 'O stream entrega ao menos 2 eventos terminados em linha em branco', blocosCompletos,
      blocosCompletos ? '' : `eventos completos recebidos: ${marcasDeTempo.length}. Verifique o \\n\\n no fim de cada evento.`);
  } catch (erro) {
    clearTimeout(limite);
    registrar('CA-03', 'GET /api/v1/eventos: 200 com text/event-stream e no-cache', false, String(erro));
    registrar('CA-04', 'O stream entrega ao menos 2 eventos terminados em linha em branco', false, 'stream indisponivel');
  }
}

async function verificarCamposDoEvento() {
  const controle = new AbortController();
  const limite = setTimeout(() => controle.abort(), 9000);

  try {
    const res = await fetch(`${BASE}/api/v1/eventos`, { signal: controle.signal });
    const leitor = res.body.getReader();
    const decodificador = new TextDecoder();
    let acumulado = '';

    const temTudo = (texto) => /(^|\n)id:\s*\S+/.test(texto)
      && /(^|\n)event:\s*\S+/.test(texto)
      && /(^|\n)data:\s*\S+/.test(texto);

    // Le ate ver um evento completo, nao apenas o primeiro bloco: o bloco
    // inicial costuma trazer so o retry.
    while (!temTudo(acumulado) && acumulado.length < 65536) {
      const { value, done } = await leitor.read();
      if (done) break;
      acumulado += decodificador.decode(value, { stream: true });
    }
    clearTimeout(limite);
    controle.abort();

    const temRetry = /(^|\n)retry:\s*\d+/.test(acumulado);
    const temId = /(^|\n)id:\s*\S+/.test(acumulado);
    const temEvent = /(^|\n)event:\s*\S+/.test(acumulado);
    const temData = /(^|\n)data:\s*\S+/.test(acumulado);
    const ok = temRetry && temId && temEvent && temData;

    registrar('CA-05', 'Os eventos trazem retry, id, event e data', ok,
      ok ? '' : `retry=${temRetry} id=${temId} event=${temEvent} data=${temData}`);
  } catch (erro) {
    clearTimeout(limite);
    registrar('CA-05', 'Os eventos trazem retry, id, event e data', false, String(erro));
  }
}

async function verificarErros() {
  try {
    const res = await fetch(`${BASE}/api/v1/rota-inexistente`);
    registrar('CA-06', 'Rota desconhecida devolve 404', res.status === 404, `status=${res.status}`);
  } catch (erro) {
    registrar('CA-06', 'Rota desconhecida devolve 404', false, String(erro));
  }

  try {
    const res = await fetch(`${BASE}/api/v1/posicoes`, { method: 'POST' });
    const allow = res.headers.get('allow') || '';
    const ok = res.status === 405;
    registrar('CA-07', 'POST em rota so de leitura devolve 405', ok,
      ok ? (allow ? `Allow: ${allow}` : 'sugestao: acrescente o header Allow') : `status=${res.status}`);
  } catch (erro) {
    registrar('CA-07', 'POST em rota so de leitura devolve 405', false, String(erro));
  }
}

console.log(`Verificando ${BASE}\n`);
await verificarHealth();
await verificarPosicoes();
await verificarSse();
await verificarCamposDoEvento();
await verificarErros();

const falhas = resultados.filter((r) => !r.passou);
console.log(`\n${resultados.length - falhas.length} de ${resultados.length} criterios atendidos.`);

if (falhas.length) {
  console.log('Pendentes: ' + falhas.map((f) => f.id).join(', '));
  process.exit(1);
}
console.log('Tudo certo. Pode abrir o Pull Request.');
