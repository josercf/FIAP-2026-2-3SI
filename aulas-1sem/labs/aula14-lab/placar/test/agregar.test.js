"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { agregar, STATUS, FAIXAS } = require("../agregar");

function chaves(valor, acumulado) {
  if (Array.isArray(valor)) {
    valor.forEach((item) => chaves(item, acumulado));
    return acumulado;
  }
  if (valor && typeof valor === "object") {
    Object.keys(valor).forEach((chave) => {
      acumulado.add(chave);
      chaves(valor[chave], acumulado);
    });
  }
  return acumulado;
}

test("resumo_publico_nao_expoe_dado_pessoal", () => {
  const lista = [
    {
      id: "d1",
      nome: "Lia Park",
      descricao: "Final de FPS no palco principal da arena.",
      atletaId: "a1",
      latitude: -23.5,
      longitude: -46.6,
      status: "ABERTO",
      faixa: "LENDARIO",
      campus: "Campus Rio",
    },
    {
      id: "d2",
      nome: "Otto Vega",
      descricao: "Segundo confronto de esporte no mesmo campus.",
      atletaId: "a2",
      latitude: -23.6,
      longitude: -46.7,
      status: "CONFIRMADO",
      faixa: "LENDARIO",
      campus: "Campus Rio",
    },
  ];
  const resumo = agregar(lista, "Campus Rio");
  const vistas = chaves(resumo, new Set());
  for (const proibida of ["nome", "descricao", "atletaId", "latitude", "longitude", "id"]) {
    assert.equal(vistas.has(proibida), false, `vazou ${proibida}`);
  }
  assert.equal(resumo.campus, "Campus Rio");
  assert.equal(resumo.porFaixa.LENDARIO, 2);
  assert.equal(resumo.porFaixa.BRONZE, 0);
  assert.equal(resumo.porStatus.ABERTO, 1);
  assert.equal(resumo.porStatus.CONFIRMADO, 1);
  for (const status of STATUS) assert.equal(typeof resumo.porStatus[status], "number");
  for (const faixa of FAIXAS) assert.equal(typeof resumo.porFaixa[faixa], "number");
});
