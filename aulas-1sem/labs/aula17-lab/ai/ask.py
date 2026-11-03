#!/usr/bin/env python3
"""
Cliente mínimo de IA para os laboratórios da disciplina.

Backend único: o servidor Ollama instalado neste devcontainer. O GitHub
Models foi retirado do ar em 30/07/2026, antes da primeira aula, e deixou
de ser uma opção (decisão registrada na ADR-005 do acervo da disciplina).

Uso:
    python ai/ask.py "escreva um PRD para o serviço de telemetria"
    cat prompt.txt | python ai/ask.py
    OLLAMA_MODEL=qwen2.5:3b python ai/ask.py "..."

Sem dependências externas: só a biblioteca padrão.
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODELO = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
TIMEOUT = int(os.environ.get("AI_TIMEOUT", "300"))


def ollama_no_ar():
    """Confirma que o servidor Ollama responde antes de mandar o prompt."""
    try:
        with urllib.request.urlopen(BASE_URL + "/api/tags", timeout=5):
            return True
    except (urllib.error.URLError, OSError):
        return False


def perguntar(prompt):
    req = urllib.request.Request(
        BASE_URL + "/api/chat",
        data=json.dumps(
            {
                "model": MODELO,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["message"]["content"]


def main():
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
    if not prompt:
        print(__doc__)
        return 1

    if not ollama_no_ar():
        sys.stderr.write(
            "O servidor Ollama não está respondendo em %s.\n"
            "Suba com: ollama serve\n"
            "Depois confirme o modelo com: ollama list\n" % BASE_URL
        )
        return 1

    try:
        print("[Ollama] consultando o modelo %s..." % MODELO, file=sys.stderr)
        print(perguntar(prompt))
        return 0
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", "replace")[:300]
        sys.stderr.write(
            "O Ollama respondeu HTTP %d: %s\n"
            "Se o modelo não existe localmente, baixe com: ollama pull %s\n"
            % (e.code, corpo, MODELO)
        )
        return 1
    except (urllib.error.URLError, OSError) as e:
        sys.stderr.write(
            "Falha ao consultar o Ollama: %s\n"
            "Confira o servidor com: ollama list\n" % e
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
