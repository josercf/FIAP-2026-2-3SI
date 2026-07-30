#!/usr/bin/env python3
"""
Gera a estrutura local dos repositorios de laboratorio da disciplina
Microservice and Web Engineering & IT Services (FIAP, 2026-2).

Cada lab e autocontido: devcontainer proprio, sem imagem base compartilhada.
"""
import json
import os
import shutil
import stat

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "labs")

PREFIX = "mwe-2026-2"
DISCIPLINA = "Microservice and Web Engineering & IT Services"
PROF = "Prof. José Romualdo da Costa Filho"
CASE = "LogiTech Enterprise AI Platform"

# Imagens oficiais de devcontainer da Microsoft
IMG = {
    "python": "mcr.microsoft.com/devcontainers/python:1-3.12-bookworm",
    "node": "mcr.microsoft.com/devcontainers/typescript-node:1-22-bookworm",
    "java": "mcr.microsoft.com/devcontainers/java:1-21-bookworm",
    "dotnet": "mcr.microsoft.com/devcontainers/dotnet:1-8.0-bookworm",
    "universal": "mcr.microsoft.com/devcontainers/universal:2-linux",
}

LABS = [
    {
        "n": "01", "slug": "requisitos", "img": "python", "docker": False,
        "titulo": "Engenharia de Requisitos: PRD e SDD com SLM local",
        "aula": "Aula 01 - SDLC, Git, Requisitos (PRD/SDD), DDD e Modelo OSI",
        "data": "04/08/2026",
        "missao": "Especificar o servico de telemetria de frota da LogiTech: gerar PRD e SDD com apoio de um modelo de IA e revisa-los criticamente.",
        "entrega": ["docs/PRD.md", "docs/SDD.md"],
        "ports": [],
    },
    {
        "n": "02", "slug": "http-sse", "img": "node", "docker": False,
        "titulo": "Sockets L4, HTTP/1.1 a 3 e Server-Sent Events",
        "aula": "Aula 02 - Protocolos de Aplicacao, SSE, Wireshark e Git Workflows",
        "data": "11/08/2026",
        "missao": "Implementar o servidor de telemetria especificado na Aula 01: sockets TCP/UDP em Python e, sobre eles, um feed de rastreamento via SSE em Node.",
        "entrega": ["sockets-l4/server_telemetry.py", "sse/server.js"],
        "ports": [3000, 8080, 8081],
    },
    {
        "n": "03", "slug": "docker", "img": "python", "docker": True,
        "titulo": "Docker I: Dockerfile Multi-Stage, Volumes e Networks",
        "aula": "Aula 03 - Docker I: Engine, Imagens, Multi-Stage e Persistencia",
        "data": "18/08/2026",
        "missao": "Conteinerizar a API de telemetria da LogiTech com Dockerfile multi-stage, reduzindo a imagem final e persistindo dados em volume.",
        "entrega": ["Dockerfile", "docker-compose.yml"],
        "ports": [8000],
    },
    {
        "n": "05", "slug": "solid-patterns", "img": "java", "docker": False,
        "titulo": "POO, SOLID e Design Patterns em Java e C#",
        "aula": "Aula 05 - POO, Principios SOLID e Design Patterns",
        "data": "01/09/2026",
        "missao": "Implementar o calculo de frete da LogiTech com Strategy e injecao de dependencia, em Java (Spring Boot) e C# (.NET), aplicando SOLID.",
        "entrega": ["java/", "csharp/"],
        "ports": [8080],
    },
    {
        "n": "06", "slug": "apis-patterns", "img": "python", "docker": False,
        "titulo": "Adapter, Decorator e Strategy em APIs Node.js e Python",
        "aula": "Aula 06 - Design Patterns Estruturais e Comportamentais",
        "data": "08/09/2026",
        "missao": "Integrar a LogiTech a uma API legada de rastreamento usando Adapter, expondo uma API moderna em FastAPI e em Express/TypeScript.",
        "entrega": ["python-fastapi/", "node-ts/"],
        "ports": [8000, 3000],
    },
    {
        "n": "07", "slug": "compose-gateway", "img": "python", "docker": True,
        "titulo": "Docker Compose Multi-Servico e AI Gateway",
        "aula": "Aula 07 - Docker Compose e AI Gateways (Strategy e Facade)",
        "data": "15/09/2026",
        "missao": "Subir a stack da LogiTech com Docker Compose e construir um AI Gateway (Facade) que roteia para multiplos modelos por tras de uma unica interface.",
        "entrega": ["docker-compose.yml", "gateway/"],
        "ports": [8000, 6379],
    },
    {
        "n": "08", "slug": "agentes-worktrees", "img": "python", "docker": False,
        "titulo": "Function Calling, Command Pattern e Git Worktrees",
        "aula": "Aula 08 - Orquestracao de Agentes e Git Worktrees I",
        "data": "22/09/2026",
        "missao": "Construir um agente de logistica que expoe ferramentas via Function Calling, modeladas com Command Pattern, e paralelizar o trabalho com Git Worktrees.",
        "entrega": ["agent.py", "tools/"],
        "ports": [],
    },
    {
        "n": "10", "slug": "testes-react", "img": "node", "docker": False,
        "titulo": "Testes de Unidade (TDD e Mocks) e Frontend React",
        "aula": "Aula 10 - Testes de Unidade e Frontend Enterprise I",
        "data": "06/10/2026",
        "missao": "Desenvolver a SPA de rastreamento da LogiTech em React com TypeScript, guiada por testes (Vitest e Testing Library).",
        "entrega": ["src/", "src/__tests__/"],
        "ports": [5173],
    },
    {
        "n": "11", "slug": "angular-rxjs", "img": "node", "docker": False,
        "titulo": "Frontend Angular com Observer Pattern e RxJS",
        "aula": "Aula 11 - Frontend Enterprise II: Angular",
        "data": "13/10/2026",
        "missao": "Construir o dashboard administrativo da LogiTech em Angular, consumindo a telemetria em tempo real com RxJS (Observer Pattern).",
        "entrega": ["src/app/"],
        "ports": [4200],
    },
    {
        "n": "12", "slug": "rag-mcp", "img": "python", "docker": True,
        "titulo": "Persistencia Vetorial com pgvector, RAG e MCP",
        "aula": "Aula 12 - pgvector, RAG e Model Context Protocol",
        "data": "20/10/2026",
        "missao": "Indexar os contratos de frete da LogiTech em pgvector, montar um pipeline RAG e expor a busca como um servidor MCP.",
        "entrega": ["src/rag_pgvector.py", "src/mcp_server.py"],
        "ports": [5432, 8000],
    },
    {
        "n": "14", "slug": "oauth-jwt", "img": "node", "docker": True,
        "titulo": "Seguranca Enterprise: OAuth 2.0, OIDC, JWT e RBAC",
        "aula": "Aula 14 - Seguranca Web Enterprise e Git Worktrees II",
        "data": "03/11/2026",
        "missao": "Proteger as APIs da LogiTech com Keycloak: fluxo OIDC, validacao de JWT e autorizacao por papel (RBAC).",
        "entrega": ["app.js", "docker-compose.yml"],
        "ports": [3000, 8080],
    },
    {
        "n": "15", "slug": "owasp-llm", "img": "python", "docker": True,
        "titulo": "Seguranca AI-First (OWASP Top 10 for LLMs) e Trivy",
        "aula": "Aula 15 - Seguranca AI-First e Container Scan",
        "data": "10/11/2026",
        "missao": "Defender o AI Gateway da LogiTech contra Prompt Injection e escanear as imagens Docker com Trivy, corrigindo as vulnerabilidades encontradas.",
        "entrega": ["llm_defense.py", "Dockerfile.vulnerable"],
        "ports": [8000],
    },
    {
        "n": "16", "slug": "integracao-e2e", "img": "universal", "docker": True,
        "titulo": "Integracao Enterprise End-to-End e Simulado da Global Solution",
        "aula": "Aula 16 - Integracao End-to-End e Simulado GS",
        "data": "17/11/2026",
        "missao": "Integrar toda a plataforma LogiTech: frontends, servicos poliglotas, gateway de IA e autenticacao, orquestrados por Docker Compose.",
        "entrega": ["docker-compose.yml", "ai-service/", "auth-service/"],
        "ports": [3000, 8000, 8080],
    },
]


# --------------------------------------------------------------------------
# Helper de IA: GitHub Models (padrao) com fallback para Ollama local
# --------------------------------------------------------------------------
AI_ASK = r'''#!/usr/bin/env python3
"""
Cliente minimo de IA para os laboratorios da disciplina.

Ordem de tentativa:
  1. GitHub Models  - usa o GITHUB_TOKEN, que o Codespaces ja injeta.
                      Nenhuma conta ou cartao adicional e necessario.
  2. Ollama local   - fallback offline, se voce tiver `ollama serve` rodando.

Uso:
    python ai/ask.py "escreva um PRD para o servico de telemetria"
    cat prompt.txt | python ai/ask.py
    MODEL=microsoft/phi-4-mini-instruct python ai/ask.py "..."

Sem dependencias externas: so a biblioteca padrao.
"""
import json
import os
import sys
import urllib.error
import urllib.request

GITHUB_ENDPOINT = "https://models.github.ai/inference/chat/completions"
OLLAMA_ENDPOINT = "http://localhost:11434/api/chat"

# Modelos pequenos, adequados ao uso em sala
DEFAULT_GITHUB_MODEL = os.environ.get("MODEL", "openai/gpt-4o-mini")
DEFAULT_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

TIMEOUT = int(os.environ.get("AI_TIMEOUT", "120"))


def _post(url, payload, headers, timeout=TIMEOUT):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def via_github_models(prompt):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN ausente")

    data = _post(
        GITHUB_ENDPOINT,
        {
            "model": DEFAULT_GITHUB_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        },
        {"Authorization": "Bearer " + token},
    )
    return data["choices"][0]["message"]["content"]


def via_ollama(prompt):
    data = _post(
        OLLAMA_ENDPOINT,
        {
            "model": DEFAULT_OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        {},
        timeout=300,
    )
    return data["message"]["content"]


def main():
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
    if not prompt:
        print(__doc__)
        return 1

    tentativas = [("GitHub Models", via_github_models), ("Ollama local", via_ollama)]
    erros = []

    for nome, fn in tentativas:
        try:
            print("[{}] consultando...".format(nome), file=sys.stderr)
            print(fn(prompt))
            return 0
        except urllib.error.HTTPError as e:
            corpo = e.read().decode("utf-8", "replace")[:300]
            erros.append("{}: HTTP {} {}".format(nome, e.code, corpo))
        except Exception as e:  # noqa: BLE001
            erros.append("{}: {}".format(nome, e))

    print("\nNenhum backend de IA respondeu.\n", file=sys.stderr)
    for e in erros:
        print("  - " + e, file=sys.stderr)
    print(
        "\nDicas:\n"
        "  - No Codespaces o GITHUB_TOKEN e injetado automaticamente.\n"
        "  - Localmente: export GITHUB_TOKEN=$(gh auth token)\n"
        "  - Offline: ollama serve && ollama pull qwen2.5:3b\n",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def devcontainer(lab):
    """devcontainer.json autocontido para o lab."""
    features = {
        "ghcr.io/devcontainers/features/github-cli:1": {},
    }
    if lab["docker"]:
        features["ghcr.io/devcontainers/features/docker-in-docker:2"] = {}
    if lab["img"] == "python" and lab["n"] in ("02",):
        features["ghcr.io/devcontainers/features/node:1"] = {}

    extensions = ["GitHub.copilot", "GitHub.vscode-pull-request-github", "eamodio.gitlens"]
    if lab["img"] in ("python", "universal"):
        extensions += ["ms-python.python", "charliermarsh.ruff"]
    if lab["img"] in ("node", "universal"):
        extensions += ["dbaeumer.vscode-eslint", "esbenp.prettier-vscode"]
    if lab["img"] == "java":
        extensions += ["vscjava.vscode-java-pack"]
    if lab["docker"]:
        extensions += ["ms-azuretools.vscode-docker"]

    cfg = {
        "name": "{}-lab{}-{}".format(PREFIX, lab["n"], lab["slug"]),
        "image": IMG[lab["img"]],
        "features": features,
        "forwardPorts": lab["ports"],
        "postCreateCommand": "bash .devcontainer/post-create.sh",
        "remoteEnv": {
            # No Codespaces esta variavel ja existe; localmente o aluno exporta.
            "GITHUB_TOKEN": "${localEnv:GITHUB_TOKEN}"
        },
        "customizations": {
            "vscode": {
                "extensions": extensions,
                "settings": {
                    "editor.formatOnSave": True,
                    "files.eol": "\n",
                },
            }
        },
    }
    return json.dumps(cfg, indent=2, ensure_ascii=False) + "\n"


POST_CREATE = r'''#!/usr/bin/env bash
# Preparacao do ambiente do laboratorio. Roda uma vez, na criacao do container.
set -euo pipefail

echo "==> Configurando o laboratorio {nome}"

# --- Dependencias da stack -------------------------------------------------
{stack}

# --- Verificacao do backend de IA -----------------------------------------
if [ -n "${{GITHUB_TOKEN:-}}" ]; then
  echo "==> GITHUB_TOKEN presente: GitHub Models disponivel."
  echo "    Teste com: python ai/ask.py \"diga ola\""
else
  echo "==> AVISO: GITHUB_TOKEN ausente."
  echo "    No Codespaces ele e injetado automaticamente."
  echo "    Localmente, rode: export GITHUB_TOKEN=\$(gh auth token)"
  echo "    Ou use Ollama offline: ollama serve && ollama pull qwen2.5:3b"
fi

echo ""
echo "Ambiente pronto. Comece pelo README.md."
'''

STACK_CMDS = {
    "python": 'if [ -f requirements.txt ]; then pip install --user -r requirements.txt; fi',
    "node": 'if [ -f package.json ]; then npm install; fi',
    "java": 'if [ -f pom.xml ]; then mvn -q -B dependency:go-offline || true; fi',
    "dotnet": 'if ls *.csproj >/dev/null 2>&1; then dotnet restore; fi',
    "universal": (
        'if [ -f requirements.txt ]; then pip install --user -r requirements.txt; fi\n'
        'if [ -f package.json ]; then npm install; fi'
    ),
}


def readme(lab):
    nome_repo = "{}-lab{}-{}".format(PREFIX, lab["n"], lab["slug"])
    entregaveis = "\n".join("- `{}`".format(e) for e in lab["entrega"])
    portas = ", ".join(str(p) for p in lab["ports"]) or "nenhuma"

    return """# Lab {n} - {titulo}

**{disciplina}**
{prof} | FIAP Sistemas de Informacao | 1o semestre de 2026-2

> {aula} | {data}

---

## Missao

{missao}

Todos os laboratorios da disciplina evoluem o mesmo case: a **{case}**, uma
transportadora ficticia. O que voce entrega aqui e reaproveitado nas aulas
seguintes e desemboca na Global Solution.

---

## Como comecar

### Opcao 1: GitHub Codespaces (recomendado)

Clique em **Code > Codespaces > Create codespace on main**. O ambiente sobe
pronto, com todas as dependencias e o cliente de IA ja configurado. Nada para
instalar na sua maquina.

### Opcao 2: Local com Dev Container

Requer Docker e a extensao **Dev Containers** no VS Code.

```bash
git clone https://github.com/josercf/{repo}.git
cd {repo}
code .
# VS Code vai sugerir: "Reopen in Container"
```

Localmente, exporte o token para habilitar o assistente de IA:

```bash
export GITHUB_TOKEN=$(gh auth token)
```

---

## Assistente de IA incluso

O laboratorio traz um cliente minimo que fala com **GitHub Models** usando o
token que o Codespaces ja injeta. Voce nao precisa criar conta, gerar chave nem
cadastrar cartao.

```bash
python ai/ask.py "explique a diferenca entre TCP e UDP em duas frases"

# escolher outro modelo pequeno
MODEL=microsoft/phi-4-mini-instruct python ai/ask.py "..."

# usar um arquivo como prompt
cat prompts/prd.md | python ai/ask.py
```

Se o GitHub Models estiver indisponivel ou a cota da sua conta tiver acabado, o
script cai automaticamente para um **Ollama local**:

```bash
ollama serve
ollama pull qwen2.5:3b     # ~2 GB, roda em notebook sem GPU
```

> A cota gratuita do GitHub Models e limitada por dia. Se a turma inteira
> disparar requisicoes ao mesmo tempo, o fallback local resolve.

---

## Entregaveis

{entregaveis}

Portas expostas pelo ambiente: {portas}

---

## Regras de entrega

1. Trabalho em **dupla**. Um repositorio por dupla, gerado a partir deste
   (use **Fork** ou **Use this template**).
2. Commits seguindo [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/):

   ```bash
   git commit -m "feat(telemetria): adiciona listener UDP na porta 8081"
   ```

3. Submeta a URL do repositorio no formulario da disciplina ate o fim da aula.

---

## Estrutura

```
{repo}/
├── .devcontainer/
│   ├── devcontainer.json   # ambiente reproduzivel (Codespaces e local)
│   └── post-create.sh      # instalacao de dependencias
├── ai/
│   └── ask.py              # cliente de IA (GitHub Models -> Ollama)
├── docs/                   # artefatos de especificacao
└── README.md
```

---

## Material da aula

- Slides: <https://josercf.github.io/FIAP-2026-2-3SI/>
- Biblioteca de skills: <https://github.com/josercf/skill-library>
""".format(
        n=lab["n"],
        titulo=lab["titulo"],
        disciplina=DISCIPLINA,
        prof=PROF,
        aula=lab["aula"],
        data=lab["data"],
        missao=lab["missao"],
        case=CASE,
        repo=nome_repo,
        entregaveis=entregaveis,
        portas=portas,
    )


GITIGNORE = """# Dependencias
node_modules/
__pycache__/
*.py[cod]
.venv/
venv/
target/
bin/
obj/

# Ambiente
.env
.env.local

# Editor
.DS_Store
.idea/
*.swp

# Build
dist/
build/
*.log
"""


def write(path, content, executable=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    if executable:
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)

    criados = []
    for lab in LABS:
        nome = "{}-lab{}-{}".format(PREFIX, lab["n"], lab["slug"])
        root = os.path.join(OUT, nome)

        write(os.path.join(root, ".devcontainer", "devcontainer.json"), devcontainer(lab))
        write(
            os.path.join(root, ".devcontainer", "post-create.sh"),
            POST_CREATE.format(nome=nome, stack=STACK_CMDS[lab["img"]]),
            executable=True,
        )
        write(os.path.join(root, "ai", "ask.py"), AI_ASK, executable=True)
        write(os.path.join(root, "README.md"), readme(lab))
        write(os.path.join(root, ".gitignore"), GITIGNORE)
        write(
            os.path.join(root, "docs", ".gitkeep"),
            "",
        )

        criados.append((nome, lab["titulo"]))

    print("Gerados {} laboratorios em {}\n".format(len(criados), OUT))
    for nome, titulo in criados:
        print("  {:42s} {}".format(nome, titulo))


if __name__ == "__main__":
    main()
