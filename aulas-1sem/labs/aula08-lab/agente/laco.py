#!/usr/bin/env python3
"""O laço de conversa do agente.

PRONTO: não é tarefa. É a peça que já vem funcionando para que a aula possa
gastar o tempo dela onde importa, que é o contrato das ferramentas e a camada
de comandos.

O laço é sempre o mesmo, em qualquer agente com tool calling:

    1. manda a conversa e a declaração das ferramentas ao modelo;
    2. se o modelo respondeu texto, acabou: esse texto é a resposta;
    3. se o modelo respondeu uma ou mais intenções de chamada, despacha cada
       uma pelo Command Pattern, acrescenta o resultado à conversa e volta
       ao passo 1.

O limite de rodadas não é decoração: sem ele, um modelo que insiste em chamar
a mesma ferramenta gira para sempre, gastando tempo e, em provedor pago,
dinheiro.
"""
import json

from . import auditoria, esquemas
from .llm import INSTRUCAO_DE_SISTEMA

MAX_RODADAS = 4


def _argumentos(bruto):
    """Normaliza os argumentos de uma chamada de ferramenta.

    O Ollama devolve um objeto JSON já desserializado; a API compatível com
    OpenAI devolve uma **string** com JSON dentro. O agente aceita os dois, e
    trata JSON inválido como dicionário vazio: quem decide o que fazer com
    argumento faltando é a validação, não este utilitário.
    """
    if isinstance(bruto, dict):
        return bruto
    if isinstance(bruto, str):
        try:
            valor = json.loads(bruto)
        except ValueError:
            return {}
        return valor if isinstance(valor, dict) else {}
    return {}


def conversar(pergunta, cliente, despachante, max_rodadas=MAX_RODADAS,
              narrar=None):
    """Roda a conversa até o modelo responder em texto ou estourar o limite.

    Devolve `(resposta_final, eventos)`, onde `eventos` é a lista de
    `(nome_da_ferramenta, Resultado)` na ordem em que foram despachados.
    `narrar` é uma função de uma linha usada para o log de sala; passe `None`
    para rodar em silêncio, como fazem os testes.
    """
    fala = narrar or (lambda _: None)
    ferramentas = esquemas.ferramentas()
    mensagens = [
        {"role": "system", "content": INSTRUCAO_DE_SISTEMA},
        {"role": "user", "content": pergunta},
    ]
    eventos = []

    for rodada in range(1, max_rodadas + 1):
        mensagem = cliente.conversar(mensagens, ferramentas)
        chamadas = mensagem.get("tool_calls") or []

        mensagens.append({
            "role": "assistant",
            "content": mensagem.get("content") or "",
            "tool_calls": chamadas,
        })

        if not chamadas:
            resposta = (mensagem.get("content") or "").strip()
            fala("[agente] resposta final na rodada %d" % rodada)
            return resposta, eventos

        for chamada in chamadas:
            funcao = chamada.get("function") or {}
            nome = funcao.get("name") or "(sem nome)"
            argumentos = _argumentos(funcao.get("arguments"))

            fala("[modelo] intenção: %s %s"
                 % (nome, json.dumps(argumentos, ensure_ascii=False)))
            resultado = despachante.despachar(nome, argumentos)
            eventos.append((nome, resultado))

            if resultado.veredito == auditoria.AUTORIZADO:
                fala("[despachante] AUTORIZADO, executado e auditado")
            else:
                fala("[despachante] %s: %s" % (resultado.veredito, resultado.motivo))

            mensagens.append({
                "role": "tool",
                "tool_name": nome,
                "content": json.dumps(resultado.conteudo, ensure_ascii=False),
            })

    fala("[agente] limite de %d rodadas atingido" % max_rodadas)
    return ("Não consegui concluir o atendimento dentro do limite de %d "
            "rodadas de ferramenta." % max_rodadas), eventos
