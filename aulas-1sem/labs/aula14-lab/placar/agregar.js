"use strict";

const STATUS = ["ABERTO", "CONFIRMADO", "EM_JOGO", "ENCERRADO", "CANCELADO"];
const FAIXAS = ["BRONZE", "PRATA", "OURO", "LENDARIO"];

/**
 * Missão 6.
 * Recebe a lista de desafios de um campus e devolve só o agregado:
 * { campus, porStatus, porFaixa }.
 * As cinco chaves de status e as quatro faixas existem sempre, com zero
 * quando não houver desafio.
 * O JSON não pode ter nome, descricao, atletaId, latitude, longitude nem id.
 */
function agregar(desafios, campus) {
  return { campus, desafios };
}

module.exports = { agregar, STATUS, FAIXAS };
