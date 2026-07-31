#!/usr/bin/env python3
"""Verificador do laboratório da Aula 07 (Docker Compose e AI Gateway).

Confere, passo por passo, se a plataforma LogiTech que você orquestrou de
fato cumpre o contrato da ADR-006. Nada aqui confia em "eu fiz": tudo é lido
do `docker compose config`, perguntado ao Docker ou obtido de uma chamada
HTTP de verdade aos serviços rodando. Sem dependências externas: só a
biblioteca padrão.

Uso:
    python3 verificar.py                       # roda os cinco critérios
    python3 verificar.py --criterio 3          # roda só o critério 3
    python3 verificar.py --compose resgate/docker-compose.yml
    python3 verificar.py --sem-saude           # pula a checagem de /health

Saída: 0 quando tudo que foi pedido passa, 1 quando algum critério falha.

Antes de julgar o YAML, o verificador **checa o /health dos oito serviços** e
imprime o resultado. Isso é deliberado: um critério que falha porque o
serviço nem subiu tem causa e conserto diferentes de um critério que falha
porque o YAML está incompleto, e misturar os dois manda o aluno procurar no
lugar errado.

O que ele NÃO consegue provar por máquina está declarado na tabela
"o que a máquina prova" do README, e é conferido pelo professor na correção.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))

TIMEOUT_DOCKER = 60          # consultas rápidas: compose config, compose ps
TIMEOUT_HTTP = 6             # chamadas de saúde aos serviços
TIMEOUT_HTTP_LONGO = 90      # POST de pedido: passa por quatro serviços
ACERTOS_DE_CACHE_MINIMOS = 2 # o roteiro manda repetir a mesma pergunta 3 vezes

# O contrato da plataforma (ADR-006). Nome do serviço -> porta publicada no
# host e rota de saúde. O postgres não publica porta: a saúde dele é lida do
# healthcheck do próprio Compose, não por HTTP.
CONTRATO = {
    "pedidos": (8080, "/health"),
    "faturamento": (5080, "/health"),
    "frete": (8000, "/health"),
    "notificacoes": (3001, "/health"),
    "coletor": (8082, "/health"),
    "painel": (3000, "/health"),
    "ai-gateway": (4000, "/health"),
}
SERVICOS_ESPERADOS = sorted(set(CONTRATO) | {"postgres"})

# Preenchido pelo diagnóstico de saúde no início da execução.
SAUDE = {}


# ---------------------------------------------------------------------------
# Apoio
# ---------------------------------------------------------------------------


def ler(caminho):
    """Lê um arquivo relativo à raiz do laboratório. Devolve string vazia
    quando o arquivo não existe, para os critérios tratarem isso como "ainda
    não preenchido" em vez de estourar exceção."""
    p = os.path.join(RAIZ, caminho)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


def _valor_preenchido(marcador, texto):
    """Extrai o valor de um marcador do tipo 'MARCADOR: valor' e recusa tanto
    ausência quanto o texto de esqueleto 'PREENCHER', que passaria despercebido
    por um regex de presença simples."""
    m = re.search(r"%s:\s*(\S.*)" % re.escape(marcador), texto)
    valor = m.group(1).strip() if m else ""
    if not valor or valor.upper().startswith("PREENCHER"):
        return None
    return valor


def _para_float(texto):
    """Aceita tanto '1632.0' quanto '1632,0', a convenção decimal em
    português usada no restante do material."""
    return float(re.sub(r"[^\d,.-]", "", texto).strip().replace(",", "."))


def _ultimas_linhas(texto, n=6):
    linhas = [l for l in texto.splitlines() if l.strip()]
    if not linhas:
        return "(o Docker não devolveu detalhe nenhum em stderr)"
    return "\n".join(linhas[-n:])


def docker(*args, tempo_limite=TIMEOUT_DOCKER):
    """Executa um comando docker e devolve (código, stdout, stderr).

    Nunca levanta exceção. Estouro de tempo devolve o código sentinela 124 (a
    mesma convenção do utilitário `timeout` do Unix), para quem chamou
    conseguir dizer "o Docker não respondeu a tempo" em vez de "seu YAML está
    errado": são diagnósticos diferentes e pedem ações diferentes.
    """
    try:
        p = subprocess.run(["docker", *args], capture_output=True,
                           text=True, timeout=tempo_limite, cwd=RAIZ)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", ("o comando 'docker %s' não respondeu em %ds."
                         % (" ".join(args), tempo_limite))
    except OSError as erro:
        return 1, "", "não foi possível executar o docker: %s" % erro


def http(url, metodo="GET", corpo=None, tempo_limite=TIMEOUT_HTTP, cabecalhos=None):
    """Chamada HTTP com a biblioteca padrão. Devolve (status, texto, erro).

    Status 0 significa que a conexão nem chegou a acontecer: serviço fora do
    ar, porta não publicada ou nome de host errado.
    """
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    pedido = urllib.request.Request(url, data=dados, method=metodo)
    pedido.add_header("Content-Type", "application/json")
    for chave, valor in (cabecalhos or {}).items():
        pedido.add_header(chave, valor)
    try:
        with urllib.request.urlopen(pedido, timeout=tempo_limite) as resposta:
            return resposta.status, resposta.read().decode("utf-8", "replace"), None
    except urllib.error.HTTPError as erro:
        return erro.code, erro.read().decode("utf-8", "replace"), None
    except Exception as erro:  # noqa: BLE001
        return 0, "", "%s: %s" % (type(erro).__name__, erro)


def json_de(texto):
    try:
        return json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Leitura do docker-compose.yml
# ---------------------------------------------------------------------------

_config_em_cache = {}


def config(arquivo):
    """Devolve o docker-compose.yml já resolvido, como dicionário.

    Usa `docker compose config`, e não um analisador de YAML escrito à mão,
    por três motivos: não acrescenta dependência ao laboratório, resolve as
    variáveis de ambiente e as âncoras YAML exatamente como o Compose vai
    resolver na hora de subir, e recusa arquivo inválido com a mesma
    mensagem que o aluno veria no `up`.

    `--project-directory` fixa a raiz do laboratório como origem dos caminhos
    relativos de `build:`, para que o resgate, que mora em `resgate/`,
    resolva `./servicos/...` no mesmo lugar que o arquivo da raiz.
    """
    if arquivo in _config_em_cache:
        return _config_em_cache[arquivo]

    cod, saida, erro = docker("compose", "-f", arquivo,
                              "--project-directory", RAIZ,
                              "config", "--format", "json")
    if cod != 0:
        _config_em_cache[arquivo] = (None, _ultimas_linhas(erro, 8))
        return _config_em_cache[arquivo]

    dados = json_de(saida)
    if dados is None:
        _config_em_cache[arquivo] = (None, "o Compose não devolveu JSON válido.")
        return _config_em_cache[arquivo]

    _config_em_cache[arquivo] = (dados, None)
    return _config_em_cache[arquivo]


def servico(cfg, nome):
    return (cfg.get("services") or {}).get(nome)


def ambiente(svc):
    """Normaliza o `environment`, que o Compose aceita como dicionário ou como
    lista de "CHAVE=valor"."""
    bruto = svc.get("environment") or {}
    if isinstance(bruto, dict):
        return {k: ("" if v is None else str(v)) for k, v in bruto.items()}
    saida = {}
    for item in bruto:
        chave, _, valor = str(item).partition("=")
        saida[chave] = valor
    return saida


def limite_de_memoria(svc):
    """Devolve o teto de memória em bytes, ou None.

    O Compose aceita duas grafias, `mem_limit` e
    `deploy.resources.limits.memory`, e normaliza de formas diferentes
    conforme a versão. Aceitar as duas evita reprovar quem escreveu a forma
    correta na grafia que o verificador não esperava.
    """
    for valor in (svc.get("mem_limit"),
                  ((svc.get("deploy") or {}).get("resources") or {})
                  .get("limits", {}).get("memory")):
        if valor in (None, ""):
            continue
        if isinstance(valor, (int, float)):
            return int(valor)
        m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*([kmgt]?)b?\s*$", str(valor), re.I)
        if m:
            escala = {"": 1, "k": 1024, "m": 1024 ** 2,
                      "g": 1024 ** 3, "t": 1024 ** 4}[m.group(2).lower()]
            return int(float(m.group(1)) * escala)
    return None


def texto_do_healthcheck(svc):
    hc = svc.get("healthcheck") or {}
    teste = hc.get("test")
    if not teste:
        return ""
    if isinstance(teste, str):
        return teste
    return " ".join(str(p) for p in teste)


def portas_publicadas(svc):
    """Conjunto de portas publicadas no host, na forma (numero, protocolo)."""
    saida = set()
    for porta in svc.get("ports") or []:
        if isinstance(porta, dict):
            alvo = porta.get("published") or porta.get("target")
            protocolo = (porta.get("protocol") or "tcp").lower()
            if alvo:
                saida.add((int(str(alvo).split("-")[0]), protocolo))
        else:
            texto = str(porta)
            protocolo = "udp" if texto.endswith("/udp") else "tcp"
            numeros = re.findall(r"(\d+)", texto)
            if numeros:
                saida.add((int(numeros[0]), protocolo))
    return saida


def volumes_montados(svc):
    saida = []
    for item in svc.get("volumes") or []:
        if isinstance(item, dict):
            saida.append(str(item.get("source") or ""))
        else:
            saida.append(str(item).split(":")[0])
    return [v for v in saida if v]


# ---------------------------------------------------------------------------
# Diagnóstico de saúde, antes de julgar o YAML
# ---------------------------------------------------------------------------


def portas_reais():
    """Onde cada serviço está **de fato** publicado, lido do que está rodando.

    O YAML diz onde o serviço deveria estar; `docker compose ps` diz onde ele
    está. Os dois divergem sempre que o aluno precisou remapear uma porta por
    conflito no host, o que acontece com frequência: a Aula 05 deixa serviços
    de desenvolvimento ocupando 8080 e 5080 na mesma máquina.

    Os critérios continuam exigindo a porta do contrato **no arquivo**; o que
    esta função resolve é só onde bater para conversar com o serviço.
    """
    cod, saida, _ = docker("compose", "ps", "--format", "json")
    if cod != 0:
        return {}
    itens = []
    texto = saida.strip()
    if texto.startswith("["):
        itens = json_de(texto) or []
    else:
        for linha in texto.splitlines():
            item = json_de(linha)
            if item:
                itens.append(item)

    mapa = {}
    for item in itens:
        for publicacao in item.get("Publishers") or []:
            publicada = publicacao.get("PublishedPort")
            if publicada:
                mapa.setdefault(item.get("Service"), {})[
                    (publicacao.get("TargetPort"),
                     (publicacao.get("Protocol") or "tcp"))] = publicada
    return mapa


_portas_reais = {}


def porta_de(nome):
    """A porta do host onde o serviço está publicado agora, ou a do contrato."""
    contratada = CONTRATO[nome][0]
    return (_portas_reais.get(nome) or {}).get((contratada, "tcp"), contratada)


def diagnosticar_saude():
    """Consulta o /health dos sete serviços HTTP e guarda o resultado.

    Roda antes dos critérios de propósito: sem isso, o aluno cujo Compose
    está certo mas cujos containers não subiram receberia cinco mensagens
    sobre YAML, e iria procurar o problema no arquivo errado.
    """
    _portas_reais.update(portas_reais())
    print("  Saúde dos serviços (contrato da ADR-006):")
    for nome in sorted(CONTRATO):
        _, rota = CONTRATO[nome]
        porta = porta_de(nome)
        status, corpo, erro = http("http://localhost:%d%s" % (porta, rota))
        dados = json_de(corpo) or {}
        SAUDE[nome] = {"status": status, "corpo": dados, "erro": erro}
        if status == 200 and dados.get("status") == "ok":
            marca, detalhe = "OK", "porta %d" % porta
        elif status == 0:
            marca, detalhe = "  ", "sem resposta na porta %d (%s)" % (porta, erro)
        else:
            marca, detalhe = "  ", "HTTP %d na porta %d" % (status, porta)
        print("    [%s] %-13s %s" % (marca, nome, detalhe))
    print()


def saude_ok(nome):
    estado = SAUDE.get(nome)
    return bool(estado and estado["status"] == 200
                and estado["corpo"].get("status") == "ok")


def exigir_saude(*nomes):
    """Devolve a mensagem do primeiro serviço que não respondeu, ou None."""
    for nome in nomes:
        if not saude_ok(nome):
            estado = SAUDE.get(nome) or {}
            porta = porta_de(nome)
            return ("o serviço '%s' não respondeu em http://localhost:%d/health "
                    "(%s). Suba o que já escreveu com `docker compose up -d "
                    "--build` antes de rodar este critério."
                    % (nome, porta, estado.get("erro") or
                       "HTTP %s" % estado.get("status")))
    return None


# ---------------------------------------------------------------------------
# Critério 1: Passo 1, o banco e o primeiro serviço que depende dele
# ---------------------------------------------------------------------------


def criterio_1(arquivo):
    cfg, erro = config(arquivo)
    if cfg is None:
        return False, "o Compose recusou %s:\n%s" % (arquivo, erro)

    pg = servico(cfg, "postgres")
    if pg is None:
        return False, "o serviço 'postgres' não existe no docker-compose.yml."

    teste = texto_do_healthcheck(pg)
    if not teste:
        return False, ("TODO-1a: o serviço 'postgres' não declara `healthcheck`. "
                       "Sem ele, `condition: service_healthy` não tem em que se "
                       "apoiar.")
    if "pg_isready" not in teste:
        return False, ("o `healthcheck` do postgres não usa `pg_isready`. "
                       "Testar a porta com wget diria que o container subiu, "
                       "não que o banco aceita conexão, que é justamente a "
                       "diferença desta aula. Comando encontrado: %s" % teste)

    ped = servico(cfg, "pedidos")
    if ped is None:
        return False, "o serviço 'pedidos' não existe no docker-compose.yml."

    dependencias = ped.get("depends_on") or {}
    if isinstance(dependencias, list):
        return False, ("TODO-1b: `depends_on` do 'pedidos' está na forma de "
                       "lista, que só espera o container do banco existir. "
                       "Use a forma longa, com "
                       "`postgres: { condition: service_healthy }`.")
    condicao = (dependencias.get("postgres") or {}).get("condition")
    if condicao != "service_healthy":
        return False, ("TODO-1b: 'pedidos' precisa de "
                       "`depends_on.postgres.condition: service_healthy`. "
                       "Encontrado: %r" % condicao)

    evidencias = ler("docs/EVIDENCIAS.md")
    if _valor_preenchido("PEDIDOS_SEM_HEALTHCHECK", evidencias) is None:
        return False, ("registre PEDIDOS_SEM_HEALTHCHECK em docs/EVIDENCIAS.md "
                       "com o que o `docker compose logs pedidos` mostrou na "
                       "primeira subida, antes de você preencher o TODO-1a.")

    falha = exigir_saude("pedidos")
    if falha:
        return False, falha

    corpo = SAUDE["pedidos"]["corpo"]
    if corpo.get("banco") != "conectado":
        return False, ("'pedidos' respondeu, mas informa banco = %r. O serviço "
                       "não conseguiu falar com o PostgreSQL."
                       % corpo.get("banco"))
    return True, ""


# ---------------------------------------------------------------------------
# Critério 2: Passo 2, os três serviços das Aulas 05 e 06
# ---------------------------------------------------------------------------


def criterio_2(arquivo):
    cfg, erro = config(arquivo)
    if cfg is None:
        return False, "o Compose recusou %s:\n%s" % (arquivo, erro)

    esperado = {"faturamento": 5080, "frete": 8000, "notificacoes": 3001}
    for nome, porta in esperado.items():
        svc = servico(cfg, nome)
        if svc is None:
            return False, ("TODO-2: o serviço '%s' não existe no "
                           "docker-compose.yml." % nome)
        if (porta, "tcp") not in portas_publicadas(svc):
            return False, ("'%s' não publica a porta %d no host, como manda o "
                           "contrato da ADR-006. Publicadas: %s"
                           % (nome, porta, sorted(portas_publicadas(svc)) or "nenhuma"))
        redes = svc.get("networks") or {}
        nomes_de_rede = list(redes) if isinstance(redes, dict) else list(redes)
        if "logitech-net" not in nomes_de_rede:
            return False, ("'%s' não está na rede logitech-net. Sem isso ele "
                           "não resolve o nome dos outros serviços." % nome)
        if limite_de_memoria(svc) is None:
            return False, ("'%s' não declara limite de memória. Oito "
                           "containers sem teto num Codespace de 2 núcleos é "
                           "exatamente o risco que a Aula 03 ensinou a "
                           "controlar." % nome)

    falha = exigir_saude("faturamento", "frete", "notificacoes")
    if falha:
        return False, falha

    evidencias = ler("docs/EVIDENCIAS.md")
    dns = _valor_preenchido("DNS_INTERNO", evidencias)
    if dns is None:
        return False, ("registre DNS_INTERNO em docs/EVIDENCIAS.md com a saída "
                       "de `docker compose exec pedidos wget -qO- "
                       "http://frete:8000/health`.")
    if "frete" not in dns:
        return False, ("DNS_INTERNO não parece a resposta do serviço 'frete' "
                       "(esperava o nome do serviço no JSON). Valor: %s" % dns)

    # Prova de máquina do DNS interno, para não depender só do texto colado.
    cod, saida, erro = docker("compose", "exec", "-T", "pedidos", "wget", "-q",
                              "-O", "-", "http://frete:8000/health")
    if cod != 0:
        return False, ("o container 'pedidos' não conseguiu resolver e chamar "
                       "http://frete:8000/health pela rede interna:\n%s"
                       % _ultimas_linhas(erro))
    if '"servico"' not in saida or "frete" not in saida:
        return False, ("a chamada de 'pedidos' para 'frete' respondeu algo "
                       "inesperado: %s" % saida[:200])
    return True, ""


# ---------------------------------------------------------------------------
# Critério 3: Passo 3, a dívida da ADR-002 paga
# ---------------------------------------------------------------------------


def criterio_3(arquivo):
    cfg, erro = config(arquivo)
    if cfg is None:
        return False, "o Compose recusou %s:\n%s" % (arquivo, erro)

    coletor = servico(cfg, "coletor")
    painel = servico(cfg, "painel")
    if coletor is None or painel is None:
        return False, ("TODO-3: os serviços 'coletor' e 'painel' precisam "
                       "existir no docker-compose.yml.")

    if (8082, "tcp") not in portas_publicadas(coletor):
        return False, ("o 'coletor' não publica a porta 8082/tcp, que é a "
                       "porta nova desta aula: é por ela que o painel lê a "
                       "telemetria.")
    if (8081, "udp") not in portas_publicadas(coletor):
        return False, ("o 'coletor' não publica 8081/udp. Sem ela nenhum "
                       "caminhão consegue mandar posição.")

    url = ambiente(painel).get("LOGITECH_TELEMETRIA_URL", "")
    if "coletor" not in url or "8082" not in url:
        return False, ("o 'painel' precisa de "
                       "LOGITECH_TELEMETRIA_URL apontando para "
                       "http://coletor:8082/telemetria. Encontrado: %r" % url)

    montados = volumes_montados(painel)
    if "logitech-telemetria" in montados:
        return False, ("o 'painel' ainda monta o volume logitech-telemetria. "
                       "A dívida da ADR-002 não foi paga: ele continua "
                       "acoplado ao arquivo do coletor, só que agora com uma "
                       "variável ao lado. Remova o volume do painel.")
    if montados:
        return False, ("o 'painel' não deveria montar volume nenhum nesta "
                       "aula. Encontrados: %s" % ", ".join(montados))

    if "logitech-telemetria" not in volumes_montados(coletor):
        return False, ("o 'coletor' precisa montar o volume "
                       "logitech-telemetria em /dados: o arquivo deixou de ser "
                       "canal de comunicação, mas continua sendo a "
                       "persistência dele.")

    falha = exigir_saude("coletor", "painel")
    if falha:
        return False, falha

    status, corpo, erro_http = http(
        "http://localhost:%d/telemetria" % porta_de("coletor"))
    dados = json_de(corpo)
    if status != 200 or dados is None or "posicoes" not in dados:
        return False, ("GET /telemetria na porta 8082 do coletor não "
                       "respondeu o contrato esperado (HTTP %s, erro %s)." % (status, erro_http))

    saude_painel = SAUDE["painel"]["corpo"]
    if saude_painel.get("fonte") != "http":
        return False, ("o /health do painel informa fonte = %r. Ele deveria "
                       "dizer 'http': é essa a prova de que ele não lê mais "
                       "arquivo." % saude_painel.get("fonte"))
    if "coletor:8082" not in str(saude_painel.get("telemetria_url", "")):
        return False, ("o painel está lendo telemetria de %r, e não de "
                       "http://coletor:8082/telemetria."
                       % saude_painel.get("telemetria_url"))

    evidencias = ler("docs/EVIDENCIAS.md")
    resposta = _valor_preenchido("PAINEL_LE_ARQUIVO", evidencias)
    if resposta is None:
        return False, ("registre PAINEL_LE_ARQUIVO em docs/EVIDENCIAS.md.")
    if not re.match(r"^(n[aã]o|nao)\b", resposta.strip(), re.I):
        return False, ("PAINEL_LE_ARQUIVO deveria ser 'não' depois do Passo 3. "
                       "Valor encontrado: %s" % resposta)
    return True, ""


# ---------------------------------------------------------------------------
# Critério 4: Passo 4, o AI Gateway com fallback e cache
# ---------------------------------------------------------------------------


def criterio_4(arquivo):
    cfg, erro = config(arquivo)
    if cfg is None:
        return False, "o Compose recusou %s:\n%s" % (arquivo, erro)

    gw = servico(cfg, "ai-gateway")
    if gw is None:
        return False, "TODO-4: o serviço 'ai-gateway' não existe no docker-compose.yml."
    if (4000, "tcp") not in portas_publicadas(gw):
        return False, "o 'ai-gateway' não publica a porta 4000 no host."

    hosts = gw.get("extra_hosts") or []
    texto_hosts = " ".join(hosts) if isinstance(hosts, list) else str(hosts)
    if "host.docker.internal" not in texto_hosts:
        return False, ("o 'ai-gateway' precisa de "
                       "`extra_hosts: - \"host.docker.internal:host-gateway\"`. "
                       "Sem isso o container não alcança o Ollama do host no "
                       "Linux, que é o caso do Codespace.")

    falha = exigir_saude("ai-gateway")
    if falha:
        return False, falha

    status, corpo, erro_http = http(
        "http://localhost:%d/v1/metricas" % porta_de("ai-gateway"))
    metricas = json_de(corpo)
    if status != 200 or metricas is None:
        return False, ("GET /v1/metricas na porta 4000 do gateway não "
                       "respondeu (HTTP %s, erro %s)." % (status, erro_http))

    acionado = (metricas.get("fallback") or {}).get("acionado", 0)
    if acionado < 1:
        return False, ("o fallback nunca foi acionado (fallback.acionado = %s). "
                       "Faça pelo menos uma chamada a "
                       "POST /v1/chat/completions: com a estratégia "
                       "preferir-remoto e a chave vazia, o provedor remoto "
                       "falha e o gateway cai no local." % acionado)

    acertos = (metricas.get("cache") or {}).get("acertos", 0)
    if acertos < ACERTOS_DE_CACHE_MINIMOS:
        return False, ("o cache registrou %s acerto(s), e o roteiro pede no "
                       "mínimo %d: repita a mesma pergunta três vezes em "
                       "POST /v1/chat/completions e consulte /v1/metricas de "
                       "novo." % (acertos, ACERTOS_DE_CACHE_MINIMOS))

    evidencias = ler("docs/EVIDENCIAS.md")
    trecho = _valor_preenchido("FALLBACK_ACIONADO", evidencias)
    if trecho is None:
        return False, ("registre FALLBACK_ACIONADO em docs/EVIDENCIAS.md com o "
                       "trecho de `docker compose logs ai-gateway` que mostra "
                       "o gateway caindo do remoto para o local.")
    if "fallback" not in trecho.lower() and "indispon" not in trecho.lower():
        return False, ("FALLBACK_ACIONADO não parece um trecho de log de "
                       "fallback. Valor: %s" % trecho[:120])

    declarado = _valor_preenchido("ACERTOS_DE_CACHE", evidencias)
    if declarado is None:
        return False, ("registre ACERTOS_DE_CACHE em docs/EVIDENCIAS.md com o "
                       "valor lido de GET /v1/metricas.")
    try:
        if _para_float(declarado) < ACERTOS_DE_CACHE_MINIMOS:
            return False, ("ACERTOS_DE_CACHE declarado é %s, abaixo do mínimo "
                           "de %d." % (declarado, ACERTOS_DE_CACHE_MINIMOS))
    except ValueError:
        return False, "ACERTOS_DE_CACHE não é um número válido: %s" % declarado
    return True, ""


# ---------------------------------------------------------------------------
# Critério 5: Passo 5, os oito de pé, saudáveis, e um pedido de ponta a ponta
# ---------------------------------------------------------------------------


def _estado_dos_containers():
    """Lê `docker compose ps` e devolve {serviço: estado de saúde}."""
    cod, saida, erro = docker("compose", "ps", "--format", "json")
    if cod != 0:
        return None, _ultimas_linhas(erro)
    itens = []
    texto = saida.strip()
    if texto.startswith("["):
        itens = json_de(texto) or []
    else:
        for linha in texto.splitlines():
            item = json_de(linha)
            if item:
                itens.append(item)
    return {i.get("Service"): (i.get("Health") or "", i.get("State") or "")
            for i in itens}, None


def criterio_5(arquivo):
    cfg, erro = config(arquivo)
    if cfg is None:
        return False, "o Compose recusou %s:\n%s" % (arquivo, erro)

    declarados = sorted(cfg.get("services") or {})
    faltando = [s for s in SERVICOS_ESPERADOS if s not in declarados]
    if faltando:
        return False, ("faltam serviços no docker-compose.yml: %s"
                       % ", ".join(faltando))
    sobrando = [s for s in declarados if s not in SERVICOS_ESPERADOS]
    if sobrando:
        return False, ("há serviços fora do contrato da ADR-006: %s. A Aula 08 "
                       "depende destes oito nomes exatos."
                       % ", ".join(sobrando))

    sem_healthcheck = [s for s in declarados
                       if not texto_do_healthcheck(cfg["services"][s])]
    if sem_healthcheck:
        return False, ("TODO-5: sem `healthcheck`, o `docker compose ps` mostra "
                       "'Up' e nunca 'healthy'. Faltam em: %s"
                       % ", ".join(sorted(sem_healthcheck)))

    estados, erro_ps = _estado_dos_containers()
    if estados is None:
        return False, "não foi possível ler `docker compose ps`:\n%s" % erro_ps

    doentes = []
    for nome in SERVICOS_ESPERADOS:
        saude, estado = estados.get(nome, ("", "ausente"))
        if saude != "healthy":
            doentes.append("%s (%s)" % (nome, saude or estado))
    if doentes:
        return False, ("o `docker compose ps` não mostra os oito saudáveis. "
                       "Pendentes: %s" % ", ".join(doentes))

    evidencias = ler("docs/EVIDENCIAS.md")
    for marcador in ("TEMPO_ATE_TODOS_SAUDAVEIS_S", "MEMORIA_TOTAL_MB"):
        valor = _valor_preenchido(marcador, evidencias)
        if valor is None:
            return False, "registre %s em docs/EVIDENCIAS.md." % marcador
        try:
            numero = _para_float(valor)
        except ValueError:
            return False, "%s não é um número válido: %s" % (marcador, valor)
        if numero <= 0:
            return False, "%s precisa ser um valor positivo." % marcador

    # A prova final: um pedido percorrendo a plataforma inteira.
    status, corpo, erro_http = http(
        "http://localhost:%d/api/v1/pedidos" % porta_de("pedidos"), metodo="POST",
        tempo_limite=TIMEOUT_HTTP_LONGO,
        corpo={"cliente": "verificador@logitech.com.br",
               "origem": "Guarulhos-SP", "destino": "Betim-MG",
               "pesoKg": 820, "modalidade": "expresso"})
    dados = json_de(corpo)
    if status != 201 or dados is None:
        return False, ("POST /api/v1/pedidos devolveu HTTP %s (erro %s). "
                       "Resposta: %s" % (status, erro_http, corpo[:200]))

    jornada = dados.get("jornada") or {}
    esperadas = ("frete", "pedidos", "faturamento", "notificacoes")
    quebradas = [e for e in esperadas if jornada.get(e) != "ok"]
    if quebradas:
        return False, ("o pedido %s foi gravado, mas não percorreu a "
                       "plataforma inteira. Etapas com problema: %s"
                       % (dados.get("id"),
                          ", ".join("%s=%s" % (e, jornada.get(e, "ausente"))
                                    for e in quebradas)))
    return True, ""


# ---------------------------------------------------------------------------

CRITERIOS = [
    (1, "Passo 1: healthcheck do banco e depends_on com condição", criterio_1),
    (2, "Passo 2: faturamento, frete e notificações na rede", criterio_2),
    (3, "Passo 3: o painel deixa de ler arquivo (ADR-002)", criterio_3),
    (4, "Passo 4: AI Gateway com fallback real e cache", criterio_4),
    (5, "Passo 5: os oito saudáveis e um pedido de ponta a ponta", criterio_5),
]


def main():
    ap = argparse.ArgumentParser(
        description="Verificador do laboratório da Aula 07.")
    ap.add_argument("--criterio", type=int, choices=range(1, 6),
                    help="valida só o critério indicado, em vez dos cinco")
    ap.add_argument("--compose", default="docker-compose.yml",
                    help="arquivo a analisar (padrão: docker-compose.yml)")
    ap.add_argument("--sem-saude", action="store_true",
                    help="pula o diagnóstico de /health do início")
    args = ap.parse_args()

    print()
    print("  LogiTech Enterprise, Aula 07: verificação da orquestração")
    print("  arquivo analisado: %s" % args.compose)
    print()

    if not args.sem_saude:
        diagnosticar_saude()

    alvo = [c for c in CRITERIOS if args.criterio is None or c[0] == args.criterio]
    ok = 0
    for num, nome, fn in alvo:
        passou, motivo = fn(args.compose)
        print("  [%s] Critério %d: %s" % ("OK" if passou else "  ", num, nome))
        if passou:
            ok += 1
        else:
            for linha in motivo.splitlines():
                print("         %s" % linha)
    print("\n  %d de %d\n" % (ok, len(alvo)))
    return 0 if ok == len(alvo) else 1


if __name__ == "__main__":
    sys.exit(main())
