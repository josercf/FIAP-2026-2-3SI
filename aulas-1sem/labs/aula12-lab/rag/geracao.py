"""Geração: o A e o G de RAG, aumento do prompt e resposta do modelo.

Esta é a etapa **menos** importante do laboratório, e a ordem em que ela
aparece no arquivo não é acidente. O que a Aula 12 cobra é a **recuperação**:
se o trecho certo do contrato foi trazido. A redação da resposta varia com o
modelo local que a sua máquina aguenta, e não entra nos critérios.

O modelo recebe uma instrução dura: responder só com o que está no contexto e
dizer que não sabe quando o contexto não cobre a pergunta. Isso não elimina a
alucinação, apenas reduz. O que de fato protege o usuário é a **citação da
fonte**, que sai do JOIN do TODO-4a e permite conferir.

Não é tarefa. Este arquivo vem pronto.
"""

import json
import os
import urllib.error
import urllib.request

OLLAMA_URL = os.environ.get("LOGITECH_OLLAMA_URL", "http://localhost:11434")
MODELO_CONVERSA = os.environ.get("LOGITECH_MODELO", "qwen2.5:1.5b")
TEMPO_LIMITE_S = 240

INSTRUCAO = (
    "Você é o assistente de contratos da LogiTech Enterprise, uma transportadora "
    "de cargas. Responda à pergunta usando EXCLUSIVAMENTE o contexto abaixo, que "
    "foi extraído dos contratos vigentes. Cite o contrato de origem entre "
    "colchetes, no formato [1], [2]. Se o contexto não responder à pergunta, diga "
    "exatamente: não encontrei essa informação nos contratos indexados. Nunca "
    "invente prazo, valor ou percentual que não esteja no contexto. Responda em "
    "português do Brasil, em no máximo cinco frases."
)


def responder(pergunta: str, contexto: str) -> str:
    corpo = {
        "model": MODELO_CONVERSA,
        "stream": False,
        "options": {"temperature": 0.1},
        "messages": [
            {"role": "system", "content": INSTRUCAO},
            {
                "role": "user",
                "content": "CONTEXTO:\n%s\n\nPERGUNTA: %s" % (contexto, pergunta),
            },
        ],
    }
    requisicao = urllib.request.Request(
        OLLAMA_URL.rstrip("/") + "/api/chat",
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=TEMPO_LIMITE_S) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
        return (dados.get("message") or {}).get("content", "").strip()
    except (urllib.error.URLError, TimeoutError, OSError) as erro:
        return (
            "não consegui falar com o modelo de conversa (%s). A recuperação "
            "acima continua válida: os trechos são o que a aula cobra." % erro
        )
