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

# Destino da geracao. Sobrescreva com LABS_OUT para nao sujar a arvore do repo.
OUT = os.environ.get(
    "LABS_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "labs")
)

PREFIX = "mwe-2026-2"
DISCIPLINA = "Microservice and Web Engineering & IT Services"
PROF = "Prof. José Romualdo da Costa Filho"
CASE = "LogiTech Enterprise AI Platform"

# SLM que acompanha o devcontainer. ~1 GB, roda em CPU no Codespaces de 2 nucleos.
MODELO_SLM = "qwen2.5:1.5b"


def modelo_do_lab(lab):
    """Modelo local do laboratório, com o global como padrão."""
    return lab.get("modelo", MODELO_SLM)

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
        "aula": "Aula 02 - Protocolos de Aplicacao, SSE, cURL e Git Workflows",
        "data": "11/08/2026",
        "missao": "Implementar o servidor de telemetria especificado na Aula 01: sockets TCP/UDP em Python e, sobre eles, um feed de rastreamento via SSE em Node.",
        "entrega": ["sockets-l4/server_telemetry.py", "sse/server.js"],
        "ports": [3000, 8080, 8081],
    },
    {
        "n": "03", "slug": "docker", "img": "python", "docker": True,
        "modelo": "qwen3.5:2b", "extras": ["node"],
        "titulo": "Docker I: Dockerfile Multi-Stage, Volumes e Networks",
        "aula": "Aula 03 - Docker I: Engine, Imagens, Multi-Stage e Persistencia",
        "data": "18/08/2026",
        "missao": "Conteinerizar o coletor de telemetria e o gateway HTTP da LogiTech em sete etapas progressivas, do isolamento de processos ate a publicacao da imagem no Docker Hub.",
        "entrega": ["Dockerfile.coletor", "Dockerfile.gateway", "docs/EVIDENCIAS.md"],
        "ports": [3000, 8081],
    },
    {
        "n": "05", "slug": "solid-patterns", "img": "java", "docker": True,
        "preparo": (
            '# Pre-aquece as duas stacks: sem isto a turma perde minutos baixando\n'
            '# Spring Boot e Npgsql no comeco da aula.\n'
            'if [ -f pedidos/pom.xml ]; then mvn -B -q -f pedidos/pom.xml dependency:go-offline || true; fi\n'
            'if [ -f faturamento/Faturamento.sln ]; then dotnet restore faturamento/Faturamento.sln || true; fi\n'
            'pip install --user pytest >/dev/null 2>&1 || true'
        ),
        "extras": ["dotnet"],
        "titulo": "POO, SOLID e Design Patterns em Java e C#",
        "aula": "Aula 05 - POO, Principios SOLID e Design Patterns",
        "data": "01/09/2026",
        "missao": "Implementar os contextos de Pedidos (Java, Spring Boot 3) e Faturamento (C#, .NET 8) da LogiTech aplicando SOLID, Repository, Factory Method e Singleton thread-safe.",
        "entrega": ["servicos/pedidos/", "servicos/faturamento/", "docs/EVIDENCIAS.md"],
        "ports": [8080, 5080, 5432],
    },
    {
        "n": "06", "slug": "apis-patterns", "img": "python", "docker": False,
        "preparo": (
            'if [ -f servicos/frete/requirements.txt ]; then pip install --user -r servicos/frete/requirements.txt; fi\n'
            'if [ -f servicos/notificacoes/package.json ]; then (cd servicos/notificacoes && npm ci); fi'
        ),
        "extras": ["node"],
        "titulo": "Adapter, Decorator e Strategy em APIs Node.js e Python",
        "aula": "Aula 06 - Design Patterns Estruturais e Comportamentais",
        "data": "08/09/2026",
        "missao": "Construir o motor de frete (Python, FastAPI) com Strategy e o servico de notificacoes (Node, TypeScript) com Decorator e Adapter para a API legada de rastreamento.",
        "entrega": ["servicos/frete/", "servicos/notificacoes/", "docs/EVIDENCIAS.md"],
        "ports": [8000, 3001],
    },
    {
        "n": "07", "slug": "compose-gateway", "img": "python", "docker": True,
        "preparo": (
            '# A rede e o volume vem da Aula 03 e entram no Compose como external:\n'
            '# sem eles o compose up falha com mensagem obscura.\n'
            'docker network create logitech-net 2>/dev/null || true\n'
            'docker volume create logitech-telemetria >/dev/null 2>&1 || true\n'
            'if [ -f .env.exemplo ] && [ ! -f .env ]; then cp .env.exemplo .env; fi\n'
            'pip install --user pytest >/dev/null 2>&1 || true'
        ),
        "extras": ["node"],
        "titulo": "Docker Compose Multi-Servico e AI Gateway",
        "aula": "Aula 07 - Docker Compose e AI Gateways (Strategy e Facade)",
        "data": "15/09/2026",
        "missao": "Orquestrar os oito servicos da plataforma LogiTech com Docker Compose e construir um AI Gateway (Facade e Strategy) com fallback real entre provedor remoto e modelo local.",
        "entrega": ["docker-compose.yml", "docs/EVIDENCIAS.md"],
        "ports": [3000, 3001, 4000, 5080, 8000, 8080, 8082],
    },
    {
        "n": "08", "slug": "agentes-worktrees", "img": "python", "docker": True,
        "preparo": (
            'pip install --user pytest >/dev/null 2>&1 || true'
        ),
        "modelo": "qwen3.5:2b",
        "titulo": "Function Calling, Command Pattern e Git Worktrees",
        "aula": "Aula 08 - Orquestracao de Agentes e Git Worktrees I",
        "data": "22/09/2026",
        "missao": "Construir um agente de logistica que executa acoes reais na API de Pedidos via Function Calling, com cada acao modelada como Command validado por JSON Schema, e paralelizar o trabalho com Git Worktrees.",
        "entrega": ["agente/", "docs/AUDITORIA.md", "docs/EVIDENCIAS.md"],
        "ports": [8080],
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
# Helper de IA: Ollama local, o único backend dos laboratórios (ADR-005)
# --------------------------------------------------------------------------
AI_ASK = r'''#!/usr/bin/env python3
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
MODELO = os.environ.get("OLLAMA_MODEL", "__MODELO__")
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
'''


# Stacks que um lab pode pedir além da imagem base, via a chave "extras".
# A imagem base já traz a stack principal; isto é para os labs poliglotas.
EXTRAS = {
    "node": ("ghcr.io/devcontainers/features/node:1",
             ["dbaeumer.vscode-eslint", "esbenp.prettier-vscode"]),
    "dotnet": ("ghcr.io/devcontainers/features/dotnet:2",
               ["ms-dotnettools.csharp"]),
    "java": ("ghcr.io/devcontainers/features/java:1",
             ["vscjava.vscode-java-pack"]),
    "python": ("ghcr.io/devcontainers/features/python:1",
               ["ms-python.python"]),
}


def devcontainer(lab):
    """devcontainer.json autocontido para o lab."""
    features = {
        "ghcr.io/devcontainers/features/github-cli:1": {},
    }
    if lab["docker"]:
        features["ghcr.io/devcontainers/features/docker-in-docker:2"] = {}

    extensions = ["GitHub.copilot", "GitHub.vscode-pull-request-github", "eamodio.gitlens"]
    if lab["img"] in ("python", "universal"):
        extensions += ["ms-python.python", "charliermarsh.ruff"]
    if lab["img"] in ("node", "universal"):
        extensions += ["dbaeumer.vscode-eslint", "esbenp.prettier-vscode"]
    if lab["img"] == "java":
        extensions += ["vscjava.vscode-java-pack"]
    if lab["docker"]:
        extensions += ["ms-azuretools.vscode-docker"]

    for extra in lab.get("extras", []):
        feature, exts = EXTRAS[extra]
        features[feature] = {}
        extensions += [e for e in exts if e not in extensions]

    cfg = {
        "name": "{}-lab{}-{}".format(PREFIX, lab["n"], lab["slug"]),
        "image": IMG[lab["img"]],
        "features": features,
        "forwardPorts": lab["ports"] + [11434],
        "postCreateCommand": "bash .devcontainer/post-create.sh",
        "postStartCommand": "bash .devcontainer/post-start.sh",
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
{stack}{preparo}

# --- Ollama: SLM rodando dentro do proprio container -----------------------
# Backend único de IA dos laboratórios, decisão registrada na ADR-005 do
# acervo: o GitHub Models foi retirado do ar em 30/07/2026.
# O instalador do Ollama extrai com zstd, que a imagem base não traz.
if ! command -v zstd >/dev/null 2>&1; then
  echo "==> Instalando o zstd, exigido pelo instalador do Ollama"
  SUDO=""; command -v sudo >/dev/null 2>&1 && SUDO=sudo
  $SUDO apt-get update -y >/dev/null 2>&1 || true
  $SUDO apt-get install -y zstd \
    || echo "    AVISO: não consegui instalar o zstd; o Ollama pode falhar."
fi
if ! command -v ollama >/dev/null 2>&1; then
  echo "==> Instalando o Ollama"
  curl -fsSL --connect-timeout 10 --max-time 600 https://ollama.com/install.sh | sh
fi

echo "==> Subindo o servidor Ollama"
(ollama serve >/tmp/ollama.log 2>&1 &)

# Espera o servidor aceitar conexao (ate 30s)
for _ in $(seq 1 30); do
  if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then break; fi
  sleep 1
done

echo "==> Baixando o modelo {modelo} (uso unico, fica em cache)"
ollama pull {modelo} || echo "    AVISO: falha ao baixar o modelo. Rode 'ollama pull {modelo}' manualmente."

# --- Verificacao do backend de IA -----------------------------------------
if curl -sf --connect-timeout 5 http://localhost:11434/api/tags >/dev/null 2>&1 \
   && ollama list 2>/dev/null | grep -q "{modelo}"; then
  echo "==> Backend de IA pronto: Ollama respondendo com o modelo {modelo}."
  echo "    Teste com: python ai/ask.py \"diga olá\""
else
  echo "==> AVISO: o Ollama não confirmou o modelo {modelo}."
  echo "    Suba o servidor com: ollama serve"
  echo "    Depois baixe o modelo com: ollama pull {modelo}"
fi

echo ""
echo "Ambiente pronto. Comece pelo README.md."
'''

POST_START = r'''#!/usr/bin/env bash
# Roda a cada inicializacao do container: garante o Ollama no ar.
set -euo pipefail

if command -v ollama >/dev/null 2>&1; then
  if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    (ollama serve >/tmp/ollama.log 2>&1 &)
  fi
fi
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

---

## Assistente de IA incluso

O laboratorio traz um cliente minimo que fala com o **Ollama que ja vem
instalado neste devcontainer**, com o modelo `{modelo}` baixado na criacao
do ambiente. Nenhuma conta, chave ou cartao e necessario, e o prompt nao sai
da sua maquina.

```bash
ollama list                      # o modelo ja deve aparecer aqui
python ai/ask.py "explique a diferenca entre TCP e UDP em duas frases"

# usar um arquivo como prompt
cat prompts/prd.md | python ai/ask.py

# escolher outro modelo local
ollama pull qwen2.5:3b           # modelo maior, se a maquina aguentar
OLLAMA_MODEL=qwen2.5:3b python ai/ask.py "..."
```

> Se o `ai/ask.py` avisar que o servidor nao responde, rode `ollama serve`
> em um terminal separado e tente de novo.

---

## Instalando uma skill da nossa biblioteca

Uma **skill** e um arquivo `SKILL.md` que ensina ao assistente de IA um
procedimento: como escrever um PRD, como padronizar commits, como estruturar
um SDD. Em vez de repetir o mesmo prompt longo toda vez, voce instala a skill
uma vez e passa a invoca-la.

Nossa biblioteca compartilhada fica em
<https://github.com/josercf/skill-library>:

```
skills/
  prd/SKILL.md               como escrever um PRD
  sdd/SKILL.md               Spec Driven Development
  semantic-commits/SKILL.md  Conventional Commits e Git Hooks
  fiap-course-design/SKILL.md
```

### Instalar no seu ambiente

```bash
# 1. Baixe a biblioteca
git clone https://github.com/josercf/skill-library.git /tmp/skill-library

# 2. Copie a skill desejada para o diretorio de skills do projeto
mkdir -p .claude/skills
cp -r /tmp/skill-library/skills/prd .claude/skills/

# 3. Confira
ls .claude/skills/prd/SKILL.md
```

Assistentes que leem `.claude/skills/` (como o Claude Code) passam a
enxergar a skill automaticamente. Para usar com o `ai/ask.py`, basta anexar
o conteudo da skill ao prompt:

```bash
python ai/ask.py "$(cat .claude/skills/prd/SKILL.md)

Agora escreva o PRD do servico de telemetria da LogiTech."
```

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
│   └── ask.py              # cliente de IA (Ollama local)
├── docs/                   # artefatos de especificacao
└── README.md
```

---

## Material da aula

Este laboratorio faz parte do acervo da disciplina:

| | |
|---|---|
| Slides desta aula | <https://josercf.github.io/FIAP-2026-2-3SI/aulas-1sem/aulas/aula{n}.html> |
| Portal da disciplina | <https://josercf.github.io/FIAP-2026-2-3SI/> |
| Repositorio do acervo | <https://github.com/josercf/FIAP-2026-2-3SI> |
| Biblioteca de skills | <https://github.com/josercf/skill-library> |
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
        modelo=modelo_do_lab(lab),
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
            POST_CREATE.format(
                nome=nome, stack=STACK_CMDS[lab["img"]],
                preparo=("\n" + lab["preparo"]) if lab.get("preparo") else "",
                modelo=modelo_do_lab(lab),
            ),
            executable=True,
        )
        write(os.path.join(root, ".devcontainer", "post-start.sh"), POST_START, executable=True)
        write(
            os.path.join(root, "ai", "ask.py"),
            AI_ASK.replace("__MODELO__", modelo_do_lab(lab)),
            executable=True,
        )
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
