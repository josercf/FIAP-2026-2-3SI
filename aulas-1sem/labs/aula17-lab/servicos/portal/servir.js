// Servidor estático do Portal do Cliente, sem dependência nenhuma.
//
// O `npm run dev` do Vite é o caminho do desenvolvimento. Dentro do Compose o
// que sobe é o **resultado do build**, servido por este arquivo: é assim que o
// portal chega à banca, e é o que permite a imagem final não carregar o Vite,
// o TypeScript nem os 300 MB de node_modules.
//
// Uma única rota de exceção: qualquer caminho que não seja arquivo cai em
// index.html. É o mínimo que uma aplicação de página única precisa para
// sobreviver a um F5 fora da raiz.

import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

const PORTA = Number(process.env.LOGITECH_PORTA ?? 5173);
const RAIZ = new URL('./dist/', import.meta.url).pathname;

const TIPOS = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.json': 'application/json; charset=utf-8',
  '.ico': 'image/x-icon',
};

createServer(async (req, res) => {
  const caminho = new URL(req.url ?? '/', 'http://local').pathname;

  if (caminho === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    return res.end(JSON.stringify({ status: 'ok', servico: 'portal' }));
  }

  // `normalize` antes de juntar: sem isso, `/../../etc/passwd` sairia da raiz.
  const relativo = normalize(caminho === '/' ? '/index.html' : caminho).replace(/^(\.\.[/\\])+/, '');
  let arquivo = join(RAIZ, relativo);
  let corpo;
  try {
    corpo = await readFile(arquivo);
  } catch {
    arquivo = join(RAIZ, 'index.html');
    corpo = await readFile(arquivo);
  }
  res.writeHead(200, { 'Content-Type': TIPOS[extname(arquivo)] ?? 'application/octet-stream' });
  res.end(corpo);
}).listen(PORTA, () => {
  console.log('=== LogiTech Enterprise - Portal do Cliente ===');
  console.log(`[HTTP] portal servindo dist/ na porta ${PORTA}`);
});
