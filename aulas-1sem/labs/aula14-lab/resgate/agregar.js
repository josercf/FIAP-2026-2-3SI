"use strict";

const STATUS = ["ABERTO", "CONFIRMADO", "EM_JOGO", "ENCERRADO", "CANCELADO"];
const FAIXAS = ["BRONZE", "PRATA", "OURO", "LENDARIO"];

function agregar(desafios, campus) {
  const porStatus = Object.fromEntries(STATUS.map((status) => [status, 0]));
  const porFaixa = Object.fromEntries(FAIXAS.map((faixa) => [faixa, 0]));
  for (const item of desafios) {
    if (Object.prototype.hasOwnProperty.call(porStatus, item.status)) {
      porStatus[item.status] += 1;
    }
    if (Object.prototype.hasOwnProperty.call(porFaixa, item.faixa)) {
      porFaixa[item.faixa] += 1;
    }
  }
  return { campus, porStatus, porFaixa };
}

module.exports = { agregar, STATUS, FAIXAS };
