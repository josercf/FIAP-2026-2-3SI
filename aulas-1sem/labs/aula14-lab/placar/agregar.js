"use strict";

const STATUS = ["ABERTO", "CONFIRMADO", "EM_JOGO", "ENCERRADO", "CANCELADO"];
const FAIXAS = ["BRONZE", "PRATA", "OURO", "LENDARIO"];

/**
 * Passo 5 do README, slide "Missão 6. A TV".
 * Apague só esta função e cole a versão do roteiro.
 * Não apague STATUS, FAIXAS nem module.exports.
 */
function agregar(desafios, campus) {
  return { campus, desafios };
}

module.exports = { agregar, STATUS, FAIXAS };
