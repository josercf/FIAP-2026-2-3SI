#!/usr/bin/env python3
"""Verificador do laboratório da Aula 14 (OAuth 2.0, OIDC, JWT e RBAC).

Nada aqui confia em "eu fiz". Cada critério é provado contra o que está
rodando: o `docker compose config` é lido do arquivo, os tokens são obtidos
do Keycloak pelo **fluxo Authorization Code + PKCE de verdade**, e o 200, o
401 e o 403 vêm de requisições HTTP reais aos dois serviços.

Uso:
    python3 verificar.py                    # os seis critérios
    python3 verificar.py --criterio 3       # só o critério 3
    python3 verificar.py --compose resgate/docker-compose.yml

Saída: 0 quando tudo que foi pedido passa, 1 quando algum critério falha.

Sem dependências: só a biblioteca padrão.

Endereços podem ser deslocados por variável de ambiente, para quem já tiver
outra coisa ocupando as portas:
    LOGITECH_KEYCLOAK_URL, LOGITECH_PEDIDOS_URL, LOGITECH_NOTIFICACOES_URL
"""

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))

KEYCLOAK = os.environ.get("LOGITECH_KEYCLOAK_URL", "http://localhost:8090")
PEDIDOS = os.environ.get("LOGITECH_PEDIDOS_URL", "http://localhost:8080")
NOTIFICACOES = os.environ.get("LOGITECH_NOTIFICACOES_URL", "http://localhost:3001")

REALM = "logitech"
CLIENT_ID = "logitech-portal"
REDIRECT_URI = "http://localhost:5199/callback"

USUARIOS = {
    "ana.cliente": "CLIENTE",
    "bruno.motorista": "MOTORISTA",
    "carla.admin": "ADMIN",
}
SENHA = "logitech"

TIMEOUT = 10

# Preenchido pelo diagnóstico inicial e reaproveitado pelos critérios.
TOKENS = {}


# ---------------------------------------------------------------------------
# Apoio
# ---------------------------------------------------------------------------


def ler(caminho):
    p = os.path.join(RAIZ, caminho)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


def _valor(marcador, texto):
    """Extrai `MARCADOR: valor`, recusando o esqueleto `PREENCHER`."""
    m = re.search(r"%s:\s*(\S.*)" % re.escape(marcador), texto)
    valor = m.group(1).strip() if m else ""
    if not valor or valor.upper().startswith("PREENCHER"):
        return None
    return valor


def chamar(metodo, url, token=None, corpo=None):
    """Devolve (codigo, corpo_texto). Nunca levanta exceção."""
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    if dados:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as erro:                                # noqa: BLE001
        return 0, "nao respondeu: %s" % erro


def compose_config(arquivo):
    """`docker compose config` já resolvido, como dicionário."""
    try:
        p = subprocess.run(
            ["docker", "compose", "--project-directory", RAIZ, "-f",
             os.path.join(RAIZ, arquivo), "config", "--format", "json"],
            capture_output=True, text=True, timeout=90, cwd=RAIZ)
    except Exception as erro:                                # noqa: BLE001
        return None, "nao foi possivel executar o docker compose: %s" % erro
    if p.returncode != 0:
        return None, (p.stderr.strip().splitlines() or ["erro desconhecido"])[-1]
    try:
        return json.loads(p.stdout), ""
    except ValueError as erro:
        return None, "saida do compose config nao e JSON: %s" % erro


# ---------------------------------------------------------------------------
# O fluxo PKCE, o mesmo que você fez no navegador
# ---------------------------------------------------------------------------


def b64url(dados):
    return base64.urlsafe_b64encode(dados).decode("ascii").rstrip("=")


def decodificar(jwt, parte=1):
    p = jwt.split(".")[parte]
    return json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)))


class _SemRedirecionar(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def token_por_pkce(usuario, senha=SENHA):
    """Executa Authorization Code + PKCE inteiro, sem navegador.

    Preenche o formulário de login do Keycloak por HTTP, exatamente como o
    navegador faria. Existe porque o verificador precisa de três tokens
    válidos para provar o 200, o 401 e o 403, e pedir que você cole três
    tokens que expiram em cinco minutos seria cruel.

    Isso NÃO substitui o Passo 3: lá você vê cada parâmetro do fluxo. Aqui o
    fluxo é meio, não conteúdo.
    """
    verifier = b64url(secrets.token_bytes(48))
    challenge = b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    estado = b64url(secrets.token_bytes(12))

    op = urllib.request.build_opener(_SemRedirecionar)
    biscoitos = {}

    def guardar(resposta):
        for valor in resposta.headers.get_all("Set-Cookie") or []:
            nome, _, resto = valor.partition("=")
            biscoitos[nome.strip()] = resto.split(";")[0]

    def abrir(url, dados=None):
        req = urllib.request.Request(url, data=dados)
        if biscoitos:
            req.add_header("Cookie", "; ".join("%s=%s" % kv for kv in biscoitos.items()))
        try:
            r = op.open(req, timeout=TIMEOUT)
            guardar(r)
            return r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            guardar(e)
            return e.code, e.headers, e.read()

    consulta = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": REDIRECT_URI,
        "state": estado,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    _, _, pagina = abrir("%s/realms/%s/protocol/openid-connect/auth?%s"
                         % (KEYCLOAK, REALM, consulta))

    m = re.search(rb'<form[^>]*id="kc-form-login"[^>]*action="([^"]+)"', pagina)
    if not m:
        raise RuntimeError("a tela de login do Keycloak nao veio como esperado. "
                           "O realm 'logitech' foi importado? Veja `docker compose logs keycloak`.")
    acao = m.group(1).decode().replace("&amp;", "&")

    _, cabecalhos, _ = abrir(acao, urllib.parse.urlencode(
        {"username": usuario, "password": senha, "credentialId": ""}).encode())
    local = cabecalhos.get("Location") or ""
    devolvido = urllib.parse.parse_qs(urllib.parse.urlparse(local).query)
    if "code" not in devolvido:
        raise RuntimeError("login de %s nao devolveu codigo de autorizacao. "
                           "Usuario e senha conferem com o realm importado?" % usuario)
    if devolvido.get("state", [None])[0] != estado:
        raise RuntimeError("state divergente no retorno do Keycloak")

    corpo = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": devolvido["code"][0],
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
    }).encode()
    with urllib.request.urlopen(
            "%s/realms/%s/protocol/openid-connect/token" % (KEYCLOAK, REALM),
            data=corpo, timeout=TIMEOUT) as r:
        return json.loads(r.read())


def obter_tokens():
    """Um token por usuário. Guarda o erro em vez de estourar."""
    for usuario in USUARIOS:
        try:
            TOKENS[usuario] = token_por_pkce(usuario)
        except Exception as erro:                            # noqa: BLE001
            TOKENS[usuario] = {"erro": str(erro)}


def acesso(usuario):
    dado = TOKENS.get(usuario) or {}
    return dado.get("access_token")


# ---------------------------------------------------------------------------
# Critérios
# ---------------------------------------------------------------------------


def criterio_1():
    """TODO-1: o Keycloak no Compose, com realm importado de arquivo."""
    problemas = []
    config, erro = compose_config(ARQUIVO_COMPOSE)
    if config is None:
        if "LOGITECH_KEYCLOAK_ADMIN_PASSWORD" in erro:
            return ["falta o arquivo `.env`. Rode `cp .env.exemplo .env` e troque a senha: "
                    "o Compose lê a senha do admin do Keycloak de lá, e o arquivo está no "
                    ".gitignore de propósito."]
        return ["o `docker compose config` falhou: %s" % erro]

    servicos = config.get("services", {})
    kc = servicos.get("keycloak")
    if not kc:
        return ["nao existe um servico chamado `keycloak` no %s (TODO-1a)" % ARQUIVO_COMPOSE]

    if "keycloak" not in str(kc.get("image", "")):
        problemas.append("a imagem do keycloak deveria ser quay.io/keycloak/keycloak:26.0, "
                         "veio %r" % kc.get("image"))

    comando = " ".join(kc.get("command") or [])
    if "--import-realm" not in comando:
        problemas.append("falta `--import-realm` no `command`: sem ele o realm nao e "
                         "carregado do arquivo e voce cai na configuracao pela interface")

    montagens = [v.get("source", "") for v in kc.get("volumes") or []]
    if not any("keycloak" in str(m) for m in montagens):
        problemas.append("o diretorio `./keycloak` nao esta montado em "
                         "/opt/keycloak/data/import: o realm precisa vir do arquivo versionado")

    portas = [str(p.get("published", "")) for p in kc.get("ports") or []]
    if "8090" not in portas:
        problemas.append("o keycloak precisa publicar a porta 8090 no host (a 8080 e do pedidos)")

    if not kc.get("healthcheck"):
        problemas.append("falta o `healthcheck` do keycloak (TODO-1a)")
    elif "KC_HEALTH_ENABLED" not in json.dumps(kc.get("environment") or {}):
        problemas.append("ha healthcheck, mas falta KC_HEALTH_ENABLED=true: sem ela a porta "
                         "9000 nao serve /health/ready e o container nunca fica healthy")

    for nome in ("pedidos", "notificacoes"):
        servico = servicos.get(nome) or {}
        dependencias = servico.get("depends_on") or {}
        condicao = (dependencias.get("keycloak") or {}).get("condition")
        if condicao != "service_healthy":
            problemas.append("`%s` precisa de `depends_on: keycloak: condition: "
                             "service_healthy` (TODO-1c)" % nome)

    # O realm versionado, e os tres usuarios da ADR-009.
    bruto = ler("keycloak/realm-logitech.json")
    if not bruto:
        problemas.append("keycloak/realm-logitech.json nao existe")
    else:
        try:
            realm = json.loads(bruto)
        except ValueError as erro:
            return problemas + ["realm-logitech.json nao e JSON valido: %s" % erro]
        papeis = {p["name"] for p in realm.get("roles", {}).get("realm", [])}
        if not {"ADMIN", "MOTORISTA", "CLIENTE"} <= papeis:
            problemas.append("o realm precisa dos tres papeis ADMIN, MOTORISTA e CLIENTE")
        usuarios = {u["username"] for u in realm.get("users", [])}
        if not set(USUARIOS) <= usuarios:
            problemas.append("faltam usuarios semeados no realm: %s"
                             % ", ".join(sorted(set(USUARIOS) - usuarios)))

    return problemas


def criterio_2():
    """O interruptor ligado e a rota /health aberta nos dois servicos."""
    problemas = []
    for nome, base in (("pedidos", PEDIDOS), ("notificacoes", NOTIFICACOES)):
        codigo, corpo = chamar("GET", base + "/health")
        if codigo != 200:
            problemas.append("GET %s/health devolveu %s, e precisa ser 200 SEM token: o "
                             "healthcheck do Compose nao carrega credencial" % (base, codigo))
            continue
        try:
            saude = json.loads(corpo)
        except ValueError:
            problemas.append("GET %s/health nao devolveu JSON" % base)
            continue
        if saude.get("autenticacaoAtiva") is not True:
            problemas.append("`%s` esta com LOGITECH_AUTH_ATIVA desligada. O Compose DESTA "
                             "aula liga a autenticacao; sem isso nada aqui esta sendo "
                             "protegido de verdade." % nome)
    return problemas


def criterio_3():
    """Sem token: 401 nas rotas protegidas, nos dois servicos."""
    problemas = []
    alvos = [
        ("GET", PEDIDOS + "/api/v1/pedidos", None),
        ("POST", NOTIFICACOES + "/api/v1/notificacoes",
         {"canal": "sms", "destinatario": "+5511999999999", "mensagem": "teste"}),
    ]
    for metodo, url, corpo in alvos:
        codigo, resposta = chamar(metodo, url, None, corpo)
        if codigo == 403:
            problemas.append("%s %s devolveu 403 sem token nenhum, e o certo e 401: 403 diz "
                             "'sei quem voce e e voce nao pode', e aqui ninguem se "
                             "identificou" % (metodo, url))
        elif codigo != 401:
            problemas.append("%s %s devolveu %s sem token, e precisa devolver 401 (%s)"
                             % (metodo, url, codigo, resposta[:120]))
    return problemas


def criterio_4():
    """Com token válido: 200 para quem tem o papel, 403 para quem não tem."""
    problemas = []
    for usuario, dado in TOKENS.items():
        if "erro" in dado:
            return ["nao foi possivel obter token de %s pelo fluxo PKCE: %s"
                    % (usuario, dado["erro"])]

    casos = [
        # (usuario, metodo, url, corpo, esperado, porque)
        ("ana.cliente", "GET", PEDIDOS + "/api/v1/pedidos", None, 200,
         "CLIENTE pode listar pedidos"),
        ("bruno.motorista", "GET", PEDIDOS + "/api/v1/pedidos", None, 200,
         "MOTORISTA tambem pode listar"),
        ("bruno.motorista", "POST", PEDIDOS + "/api/v1/pedidos",
         {"cliente": "Atacadao Sul"}, 403,
         "MOTORISTA nao cria pedido: o token e valido, o papel e que nao serve"),
        ("ana.cliente", "PATCH", PEDIDOS + "/api/v1/pedidos/PED-1042/endereco",
         {"logradouro": "Avenida Paulista", "numero": "1106", "cidade": "Sao Paulo",
          "uf": "SP", "cep": "01311-000"}, 200,
         "CLIENTE altera o endereco de entrega"),
        ("bruno.motorista", "PATCH", PEDIDOS + "/api/v1/pedidos/PED-1042/endereco",
         {"logradouro": "Rua Qualquer", "numero": "1", "cidade": "Sao Paulo",
          "uf": "SP", "cep": "01000-000"}, 403,
         "e este e o 403 que resolve a dor de negocio da aula"),
        ("bruno.motorista", "GET", PEDIDOS + "/api/v1/pedidos/PED-1042/status", None, 200,
         "qualquer papel autenticado consulta status"),
    ]
    for usuario, metodo, url, corpo, esperado, porque in casos:
        codigo, resposta = chamar(metodo, url, acesso(usuario), corpo)
        if codigo != esperado:
            problemas.append("%s como %s devolveu %s, esperado %s (%s). Resposta: %s"
                             % (metodo, usuario, codigo, esperado, porque, resposta[:140]))
    return problemas


def criterio_5():
    """O mesmo token, o mesmo papel, em outra stack (TODO-4)."""
    problemas = []
    if any("erro" in d for d in TOKENS.values()):
        return ["sem token para testar: veja o criterio 4"]

    carga = {"canal": "sms", "destinatario": "+5511988887777",
             "mensagem": "Sua carga saiu para entrega"}

    codigo, resposta = chamar("POST", NOTIFICACOES + "/api/v1/notificacoes",
                              acesso("carla.admin"), carga)
    if codigo != 201:
        problemas.append("ADMIN em POST /api/v1/notificacoes devolveu %s, esperado 201 (%s)"
                         % (codigo, resposta[:140]))

    codigo, resposta = chamar("POST", NOTIFICACOES + "/api/v1/notificacoes",
                              acesso("bruno.motorista"), carga)
    if codigo != 403:
        problemas.append("MOTORISTA em POST /api/v1/notificacoes devolveu %s, esperado 403. "
                         "O token e o mesmo que passa no servico Java; se aqui ele nao for "
                         "recusado, o papel nao esta sendo lido de realm_access.roles (%s)"
                         % (codigo, resposta[:140]))

    # A prova de que os dois servicos leem do MESMO lugar: o mesmo token
    # de motorista passa numa rota do Java e e recusado numa rota do Node,
    # e a razao e o papel, nao a stack.
    codigo_java, _ = chamar("GET", PEDIDOS + "/api/v1/pedidos", acesso("bruno.motorista"))
    if codigo_java != 200:
        problemas.append("o mesmo token de MOTORISTA precisa continuar valendo 200 em "
                         "GET /api/v1/pedidos, e devolveu %s" % codigo_java)
    return problemas


def criterio_6():
    """As evidências medidas e as duas worktrees."""
    problemas = []
    texto = ler("docs/EVIDENCIAS.md")
    if not texto:
        return ["docs/EVIDENCIAS.md nao existe"]

    # 1. A validade lida do proprio token.
    valor = _valor("TOKEN_EXPIRA_EM_S", texto)
    if valor is None:
        problemas.append("TOKEN_EXPIRA_EM_S nao foi preenchido em docs/EVIDENCIAS.md")
    else:
        try:
            informado = int(re.sub(r"[^\d]", "", valor))
        except ValueError:
            informado = -1
        real = None
        for dado in TOKENS.values():
            if "access_token" in dado:
                conteudo = decodificar(dado["access_token"])
                real = conteudo["exp"] - conteudo["iat"]
                break
        if real is not None and informado != real:
            problemas.append("TOKEN_EXPIRA_EM_S diz %s, e o token que o Keycloak acabou de "
                             "emitir traz exp - iat = %s. O numero sai do token, nao do "
                             "chute." % (informado, real))

    # 2. Os papeis, copiados de realm_access.roles.
    valor = _valor("PAPEIS_NO_TOKEN", texto)
    if valor is None:
        problemas.append("PAPEIS_NO_TOKEN nao foi preenchido em docs/EVIDENCIAS.md")
    else:
        encontrados = set(re.findall(r"[A-Z]{4,}", valor.upper()))
        if not encontrados & set(USUARIOS.values()):
            problemas.append("PAPEIS_NO_TOKEN nao traz nenhum dos papeis do realm "
                             "(%s)" % ", ".join(sorted(set(USUARIOS.values()))))

    # 3. O issuer que veio dentro do token.
    valor = _valor("ISSUER_NO_TOKEN", texto)
    if valor is None:
        problemas.append("ISSUER_NO_TOKEN nao foi preenchido em docs/EVIDENCIAS.md")
    elif "/realms/logitech" not in valor:
        problemas.append("ISSUER_NO_TOKEN deveria terminar em /realms/logitech, veio %r" % valor)

    # 4. As duas worktrees, com a saida real do git.
    valor = _valor("WORKTREE_AUTH", texto)
    outro = _valor("WORKTREE_UI", texto)
    if valor is None or outro is None:
        problemas.append("WORKTREE_AUTH e WORKTREE_UI precisam ser preenchidos com o "
                         "caminho de cada worktree (TODO-6)")

    saida = _valor("SAIDA_DO_GIT_WORKTREE_LIST", texto)
    if saida is None:
        problemas.append("SAIDA_DO_GIT_WORKTREE_LIST nao foi preenchida")

    bloco = texto[texto.find("SAIDA_DO_GIT_WORKTREE_LIST"):] if saida else ""
    if saida and ("agent-auth" not in bloco or "agent-ui" not in bloco):
        problemas.append("a saida de `git worktree list` precisa mostrar as duas worktrees, "
                         "uma com `agent-auth` e outra com `agent-ui` no caminho ou na branch")

    # 5. O 401 e o 403 registrados com o comando que os produziu.
    for marcador in ("CURL_SEM_TOKEN", "CURL_PAPEL_ERRADO"):
        if _valor(marcador, texto) is None:
            problemas.append("%s nao foi preenchido: registre o codigo devolvido pelo curl"
                             % marcador)
    valor = _valor("CURL_SEM_TOKEN", texto) or ""
    if valor and "401" not in valor:
        problemas.append("CURL_SEM_TOKEN precisa registrar 401, e traz %r" % valor[:40])
    valor = _valor("CURL_PAPEL_ERRADO", texto) or ""
    if valor and "403" not in valor:
        problemas.append("CURL_PAPEL_ERRADO precisa registrar 403, e traz %r" % valor[:40])

    return problemas


CRITERIOS = [
    (1, "TODO-1: Keycloak no Compose, com realm importado de arquivo", criterio_1),
    (2, "GET /health aberta nos dois servicos, e LOGITECH_AUTH_ATIVA ligada", criterio_2),
    (3, "TODO-2: sem token, 401 (e nao 403)", criterio_3),
    (4, "TODO-3: com token, 200 para quem tem o papel e 403 para quem nao tem", criterio_4),
    (5, "TODO-4: o mesmo papel, do mesmo lugar do token, em outra stack", criterio_5),
    (6, "TODO-5 e TODO-6: evidencias medidas e as duas worktrees", criterio_6),
]

ARQUIVO_COMPOSE = "docker-compose.yml"


def principal():
    global ARQUIVO_COMPOSE
    p = argparse.ArgumentParser(description="Verificador da Aula 14.")
    p.add_argument("--criterio", type=int, help="roda apenas um criterio (1 a 6)")
    p.add_argument("--compose", default="docker-compose.yml",
                   help="qual arquivo de Compose julgar")
    args = p.parse_args()
    ARQUIVO_COMPOSE = args.compose

    escolhidos = [c for c in CRITERIOS if args.criterio in (None, c[0])]
    if not escolhidos:
        print("criterio %s nao existe: use de 1 a 6" % args.criterio)
        return 1

    # Diagnostico primeiro: um criterio que falha porque o Keycloak nem subiu
    # tem causa e conserto diferentes de um criterio que falha porque o codigo
    # esta incompleto, e misturar os dois manda voce procurar no lugar errado.
    print("Diagnostico do ambiente")
    codigo, _ = chamar("GET", KEYCLOAK + "/realms/logitech/.well-known/openid-configuration")
    print("  keycloak      %s  %s" % (KEYCLOAK, "no ar" if codigo == 200 else "NAO RESPONDEU"))
    for nome, base in (("pedidos", PEDIDOS), ("notificacoes", NOTIFICACOES)):
        c, corpo = chamar("GET", base + "/health")
        extra = ""
        if c == 200:
            try:
                extra = "  auth ativa: %s" % json.loads(corpo).get("autenticacaoAtiva")
            except ValueError:
                pass
        print("  %-13s %s  %s%s" % (nome, base, "no ar" if c == 200 else "NAO RESPONDEU", extra))

    if codigo == 200 and any(c[0] in (4, 5, 6) for c in escolhidos):
        print("  obtendo tokens pelo fluxo Authorization Code + PKCE...")
        obter_tokens()
        for usuario, dado in TOKENS.items():
            if "erro" in dado:
                print("    %-16s FALHOU: %s" % (usuario, dado["erro"]))
            else:
                papeis = decodificar(dado["access_token"]).get("realm_access", {}).get("roles", [])
                print("    %-16s ok, realm_access.roles = %s" % (usuario, papeis))
    print()

    falharam = 0
    for numero, titulo, funcao in escolhidos:
        try:
            problemas = funcao()
        except Exception as erro:                            # noqa: BLE001
            problemas = ["o criterio estourou: %s" % erro]
        if problemas:
            falharam += 1
            print("FALTA  criterio %d: %s" % (numero, titulo))
            for item in problemas:
                print("       - %s" % item)
        else:
            print("OK     criterio %d: %s" % (numero, titulo))

    print()
    total = len(escolhidos)
    print("%d de %d criterios cumpridos." % (total - falharam, total))
    return 1 if falharam else 0


if __name__ == "__main__":
    sys.exit(principal())
