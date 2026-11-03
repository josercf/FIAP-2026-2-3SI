"use strict";

const CANAIS = new Set(["APP", "ARENA", "DISCORD"]);

function validarAtleta(corpo) {
  if (!corpo || typeof corpo !== "object") return "corpo ausente";
  const nome = typeof corpo.nome === "string" ? corpo.nome.trim() : "";
  if (nome.length < 2 || nome.length > 80) return "nome fora de 2 a 80 caracteres";
  const campus = typeof corpo.campus === "string" ? corpo.campus.trim() : "";
  if (!campus) return "campus obrigatorio";
  if (!CANAIS.has(corpo.canal)) return "canal invalido";
  return null;
}

module.exports = { validarAtleta, CANAIS };
