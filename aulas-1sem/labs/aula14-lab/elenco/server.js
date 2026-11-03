"use strict";

const http = require("http");
const { randomUUID } = require("crypto");
const { Pool } = require("pg");
const { validarAtleta } = require("./validar");

const PORTA = Number(process.env.PORT || 8081);

function enviar(resposta, status, corpo) {
  const dados = JSON.stringify(corpo);
  resposta.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  });
  resposta.end(dados);
}

function lerCorpo(requisicao) {
  return new Promise((resolve, reject) => {
    const pedacos = [];
    requisicao.on("data", (pedaço) => pedacos.push(pedaço));
    requisicao.on("end", () => {
      const texto = Buffer.concat(pedacos).toString("utf8");
      if (!texto) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(texto));
      } catch (erro) {
        reject(erro);
      }
    });
    requisicao.on("error", reject);
  });
}

async function conectar() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  for (let tentativa = 1; tentativa <= 30; tentativa += 1) {
    try {
      await pool.query("SELECT 1");
      return pool;
    } catch (erro) {
      if (tentativa === 30) throw erro;
      await new Promise((resolver) => setTimeout(resolver, 1000));
    }
  }
  return pool;
}

async function main() {
  const pool = await conectar();
  const servidor = http.createServer(async (requisicao, resposta) => {
    if (requisicao.method === "OPTIONS") {
      enviar(resposta, 204, {});
      return;
    }
    const url = new URL(requisicao.url, "http://elenco");
    try {
      if (requisicao.method === "GET" && url.pathname === "/health") {
        enviar(resposta, 200, { status: "ok" });
        return;
      }
      if (requisicao.method === "POST" && url.pathname === "/api/v1/atletas") {
        const corpo = await lerCorpo(requisicao);
        const erro = validarAtleta(corpo);
        if (erro) {
          enviar(resposta, 400, { erro });
          return;
        }
        const id = randomUUID();
        const nome = String(corpo.nome).trim();
        const campus = String(corpo.campus).trim();
        const canal = corpo.canal;
        await pool.query(
          "INSERT INTO elenco.atletas (id, nome, campus, canal) VALUES ($1, $2, $3, $4)",
          [id, nome, campus, canal]
        );
        enviar(resposta, 201, { id, nome, campus, canal });
        return;
      }
      const leitura = url.pathname.match(/^\/api\/v1\/atletas\/([^/]+)$/);
      if (requisicao.method === "GET" && leitura) {
        const consulta = await pool.query(
          "SELECT id, nome, campus, canal FROM elenco.atletas WHERE id = $1",
          [leitura[1]]
        );
        if (consulta.rowCount === 0) {
          enviar(resposta, 404, { erro: "atleta nao encontrado" });
          return;
        }
        const linha = consulta.rows[0];
        enviar(resposta, 200, {
          id: linha.id,
          nome: linha.nome,
          campus: linha.campus,
          canal: linha.canal,
        });
        return;
      }
      enviar(resposta, 404, { erro: "nao encontrado" });
    } catch (erro) {
      if (erro instanceof SyntaxError) {
        enviar(resposta, 400, { erro: "json invalido" });
        return;
      }
      enviar(resposta, 500, { erro: "falha no elenco" });
    }
  });
  servidor.listen(PORTA, "0.0.0.0");
}

main().catch((erro) => {
  console.error(erro);
  process.exit(1);
});
