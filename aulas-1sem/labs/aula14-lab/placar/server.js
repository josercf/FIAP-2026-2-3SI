"use strict";

const http = require("http");
const { agregar } = require("./agregar");

const PORTA = Number(process.env.PORT || 8082);
const PARTIDAS = (process.env.PARTIDAS_URL || "http://partidas:8080").replace(/\/$/, "");

function enviar(resposta, status, corpo) {
  const dados = JSON.stringify(corpo);
  resposta.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
  });
  resposta.end(dados);
}

function lerJson(url) {
  return new Promise((resolve, reject) => {
    const requisicao = http.get(url, (resposta) => {
      const pedacos = [];
      resposta.on("data", (pedaço) => pedacos.push(pedaço));
      resposta.on("end", () => {
        const texto = Buffer.concat(pedacos).toString("utf8");
        if (resposta.statusCode >= 500) {
          reject(new Error("partidas indisponivel"));
          return;
        }
        try {
          resolve(JSON.parse(texto || "[]"));
        } catch (erro) {
          reject(erro);
        }
      });
    });
    requisicao.on("error", reject);
    requisicao.setTimeout(4000, () => {
      requisicao.destroy(new Error("timeout"));
    });
  });
}

const servidor = http.createServer(async (requisicao, resposta) => {
  const url = new URL(requisicao.url, "http://placar");
  if (requisicao.method === "GET" && url.pathname === "/health") {
    enviar(resposta, 200, { status: "ok" });
    return;
  }
  if (requisicao.method === "GET" && url.pathname === "/api/v1/resumo") {
    const campus = url.searchParams.get("campus") || "";
    if (!campus.trim()) {
      enviar(resposta, 400, { erro: "campus obrigatorio" });
      return;
    }
    const destino = `${PARTIDAS}/api/v1/desafios?campus=${encodeURIComponent(campus)}`;
    try {
      const lista = await lerJson(destino);
      enviar(resposta, 200, agregar(Array.isArray(lista) ? lista : [], campus));
    } catch (erro) {
      enviar(resposta, 503, { erro: "partidas indisponivel" });
    }
    return;
  }
  enviar(resposta, 404, { erro: "nao encontrado" });
});

servidor.listen(PORTA, "0.0.0.0");
