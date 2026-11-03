"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { validarAtleta } = require("../validar");

test("nome_curto_e_recusado", () => {
  const erro = validarAtleta({ nome: "A", campus: "Centro", canal: "APP" });
  assert.ok(erro, "nome com 1 caractere tem de ser recusado");
});

test("nome_longo_e_recusado", () => {
  const erro = validarAtleta({
    nome: "A".repeat(81),
    campus: "Centro",
    canal: "APP",
  });
  assert.ok(erro, "nome com 81 caracteres tem de ser recusado");
});

test("campus_vazio_e_recusado", () => {
  const erro = validarAtleta({ nome: "Lia Park", campus: "   ", canal: "ARENA" });
  assert.ok(erro, "campus em branco tem de ser recusado");
});

test("canal_fora_da_lista_e_recusado", () => {
  const erro = validarAtleta({ nome: "Lia Park", campus: "Centro", canal: "TELEFONE" });
  assert.ok(erro, "canal fora de APP, ARENA e DISCORD tem de ser recusado");
});

test("atleta_valido_passa", () => {
  const erro = validarAtleta({
    nome: "  Lia Park  ",
    campus: "Campus Norte",
    canal: "DISCORD",
  });
  assert.equal(erro, null);
});
