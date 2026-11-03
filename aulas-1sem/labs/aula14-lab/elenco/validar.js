"use strict";

const CANAIS = new Set(["APP", "ARENA", "DISCORD"]);

/**
 * Missão 2.
 * Devolva null quando o atleta puder ser gravado.
 * Devolva uma string curta quando o corpo for inválido.
 *
 * Regras:
 * - nome, depois do trim, tem de 2 a 80 caracteres
 * - campus, depois do trim, não pode ser vazio
 * - canal é exatamente APP, ARENA ou DISCORD
 */
function validarAtleta(corpo) {
  return null;
}

module.exports = { validarAtleta, CANAIS };
