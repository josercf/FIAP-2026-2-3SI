#!/usr/bin/env python3
"""Validador de JSON Schema, subconjunto suficiente para o laboratório.

PRONTO: não é tarefa. Você usa este módulo, não o escreve.

Em produção você usaria `jsonschema` ou `pydantic`. Aqui a implementação é
manual e sem dependência externa por dois motivos: o laboratório roda sem
`pip install`, e ler as trinta linhas que fazem a validação deixa evidente
que **schema é contrato executável**, não documentação.

Palavras-chave suportadas: `type`, `required`, `properties`, `enum`,
`pattern`, `minLength`, `maxLength`, `minimum`, `maximum` e
`additionalProperties: false`.
"""
import re

_TIPOS = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}


def _tipo_confere(valor, esperado):
    python = _TIPOS.get(esperado)
    if python is None:
        return True
    if esperado == "integer" and isinstance(valor, bool):
        return False
    if esperado == "number" and isinstance(valor, bool):
        return False
    return isinstance(valor, python)


def _validar_campo(nome, valor, regra):
    """Confere um valor contra a regra de uma propriedade. Devolve uma lista
    de mensagens de erro em português, vazia quando o valor está bom."""
    erros = []
    if not isinstance(regra, dict):
        return erros

    tipo = regra.get("type")
    if tipo and not _tipo_confere(valor, tipo):
        erros.append("o campo '%s' deveria ser do tipo %s e veio como %s"
                     % (nome, tipo, type(valor).__name__))
        return erros

    if "enum" in regra and valor not in regra["enum"]:
        erros.append("o campo '%s' aceita apenas %s e veio '%s'"
                     % (nome, ", ".join(str(v) for v in regra["enum"]), valor))

    if isinstance(valor, str):
        if "minLength" in regra and len(valor) < regra["minLength"]:
            erros.append("o campo '%s' precisa de pelo menos %d caracteres"
                         % (nome, regra["minLength"]))
        if "maxLength" in regra and len(valor) > regra["maxLength"]:
            erros.append("o campo '%s' aceita no máximo %d caracteres"
                         % (nome, regra["maxLength"]))
        if "pattern" in regra and not re.search(regra["pattern"], valor):
            erros.append("o campo '%s' não casa com o formato exigido (%s)"
                         % (nome, regra["pattern"]))

    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        if "minimum" in regra and valor < regra["minimum"]:
            erros.append("o campo '%s' precisa ser no mínimo %s"
                         % (nome, regra["minimum"]))
        if "maximum" in regra and valor > regra["maximum"]:
            erros.append("o campo '%s' precisa ser no máximo %s"
                         % (nome, regra["maximum"]))

    return erros


def validar(argumentos, esquema):
    """Valida `argumentos` contra `esquema` (um JSON Schema de objeto).

    Devolve a **lista de erros**. Lista vazia significa que os argumentos
    cumprem o contrato. Nunca levanta exceção: quem chama decide o que fazer
    com a recusa, e no laboratório essa decisão é registrar em auditoria.
    """
    if not isinstance(esquema, dict) or not esquema:
        return ["o esquema da ferramenta está vazio: a lacuna correspondente "
                "em agente/esquemas.py ainda não foi preenchida"]

    if not isinstance(argumentos, dict):
        return ["os argumentos precisam ser um objeto JSON e vieram como %s"
                % type(argumentos).__name__]

    erros = []
    propriedades = esquema.get("properties") or {}

    for obrigatorio in esquema.get("required") or []:
        valor = argumentos.get(obrigatorio)
        if obrigatorio not in argumentos:
            erros.append("falta o campo obrigatório '%s'" % obrigatorio)
        elif isinstance(valor, str) and not valor.strip():
            erros.append("o campo obrigatório '%s' veio vazio" % obrigatorio)

    if esquema.get("additionalProperties") is False:
        for nome in argumentos:
            if nome not in propriedades:
                erros.append("o campo '%s' não existe no contrato desta "
                             "ferramenta" % nome)

    for nome, valor in argumentos.items():
        regra = propriedades.get(nome)
        if regra is None:
            continue
        if valor is None:
            continue
        erros.extend(_validar_campo(nome, valor, regra))

    return erros
