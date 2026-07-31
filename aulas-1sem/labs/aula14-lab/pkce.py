#!/usr/bin/env python3
"""O fluxo Authorization Code + PKCE, feito a mao, pelo seu navegador.

CONGELADO: não é tarefa do laboratório. É o instrumento do Passo 3.

Este programa não esconde nada. Ele imprime o `code_verifier`, o
`code_challenge`, a URL de autorização inteira com todos os parâmetros, o
código que voltou e o token decodificado em três partes. Você faz o login
**no navegador**, como um usuário faria, e vê cada peça do fluxo aparecer.

Só depois disto o roteiro libera `curl` com token colado. A ordem é
deliberada: quem começa pelo `curl` decora um comando; quem começa pelo
navegador entende por que o comando funciona.

    python3 pkce.py                      # entra como ana.cliente
    python3 pkce.py --usuario carla.admin
    python3 pkce.py --so-token           # imprime só o access_token, para
                                         # usar em: TOKEN=$(python3 pkce.py --so-token)

Sem dependência nenhuma além da biblioteca padrão.
"""
import argparse
import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

# O endereço pelo qual o SEU NAVEGADOR alcança o Keycloak. Note que não é o
# mesmo pelo qual os serviços o alcançam de dentro da rede do Compose
# (`http://keycloak:8090`), e essa diferença é o assunto do Passo 4.
KEYCLOAK = os.environ.get("LOGITECH_KEYCLOAK_URL", "http://localhost:8090")
REALM = "logitech"
CLIENT_ID = "logitech-portal"

# A porta 5199, e não a 5173, para este exercício não disputar o servidor de
# desenvolvimento do portal. As duas estão registradas no realm: URI de
# retorno precisa ser cadastrada ANTES, e é isso que impede um atacante de
# mandar o código de autorização para o servidor dele.
PORTA_RETORNO = 5199
REDIRECT_URI = "http://localhost:%d/callback" % PORTA_RETORNO


def b64url(dados: bytes) -> str:
    """base64url sem o preenchimento `=`, como manda a RFC 7636."""
    return base64.urlsafe_b64encode(dados).decode("ascii").rstrip("=")


def decodificar(parte: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(parte + "=" * (-len(parte) % 4)))


class Retorno(http.server.BaseHTTPRequestHandler):
    """Servidor de uma requisição só: recebe o redirecionamento do Keycloak."""

    recebido = {}

    def do_GET(self):  # noqa: N802
        Retorno.recebido = dict(urllib.parse.parse_qsl(
            urllib.parse.urlparse(self.path).query))
        corpo = ("<html><meta charset='utf-8'><body style='font-family:sans-serif;"
                 "padding:40px'><h2>Pode fechar esta aba.</h2>"
                 "<p>O codigo de autorizacao voltou para o terminal.</p>"
                 "</body></html>").encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass


def esperar_codigo(estado: str, segundos: int = 180) -> str:
    try:
        servidor = http.server.HTTPServer(("127.0.0.1", PORTA_RETORNO), Retorno)
    except OSError:
        raise SystemExit(
            "A porta %d ja esta ocupada. Quase sempre e uma execucao anterior deste\n"
            "mesmo programa que ficou esperando um login que nunca chegou.\n"
            "Encerre com:  lsof -ti tcp:%d | xargs kill"
            % (PORTA_RETORNO, PORTA_RETORNO))
    servidor.timeout = segundos
    t = threading.Thread(target=servidor.handle_request, daemon=True)
    t.start()
    t.join(segundos)
    servidor.server_close()

    dados = Retorno.recebido
    if not dados:
        raise SystemExit("Nada voltou em %ds. O login foi concluido no navegador?" % segundos)
    if "error" in dados:
        raise SystemExit("O Keycloak recusou: %s - %s"
                         % (dados.get("error"), dados.get("error_description", "")))
    if dados.get("state") != estado:
        # O `state` existe para isto: casar a resposta com a requisição que
        # você mesmo iniciou. Sem ele, um terceiro consegue empurrar um
        # código de autorização dele para a sua sessão (CSRF de login).
        raise SystemExit("state divergente: esperava %r, veio %r"
                         % (estado, dados.get("state")))
    return dados["code"]


def principal():
    p = argparse.ArgumentParser(description="Fluxo PKCE a mao, pelo navegador.")
    p.add_argument("--usuario", default="ana.cliente",
                   help="so para lembrar voce de quem entrar (o login e no navegador)")
    p.add_argument("--so-token", action="store_true",
                   help="imprime apenas o access_token, sem explicacao")
    p.add_argument("--sem-navegador", action="store_true",
                   help="nao tenta abrir o navegador, so imprime a URL")
    args = p.parse_args()
    falar = not args.so_token

    def diga(*a):
        if falar:
            print(*a)

    # -------------------------------------------------------------------
    # 1. O segredo que nunca sai da sua maquina
    # -------------------------------------------------------------------
    verifier = b64url(secrets.token_bytes(48))          # 64 caracteres
    challenge = b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    estado = b64url(secrets.token_bytes(12))

    diga("\n1) PKCE: o par que so voce conhece")
    diga("   code_verifier  (%d caracteres, FICA AQUI, nunca vai pela rede agora)" % len(verifier))
    diga("       %s" % verifier)
    diga("   code_challenge = base64url(SHA-256(verifier))  ->  vai na URL")
    diga("       %s" % challenge)
    diga("   state          = %s" % estado)
    diga("\n   O navegador leva o DESAFIO. O verificador so aparece no ultimo passo,")
    diga("   direto do seu processo para o Keycloak. Quem interceptar o codigo de")
    diga("   autorizacao no meio do caminho nao consegue troca-lo por token, porque")
    diga("   nao tem o verificador. E para isso que o PKCE existe.")

    # -------------------------------------------------------------------
    # 2. A URL de autorizacao
    # -------------------------------------------------------------------
    parametros = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": REDIRECT_URI,
        "state": estado,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    url = "%s/realms/%s/protocol/openid-connect/auth?%s" % (
        KEYCLOAK, REALM, urllib.parse.urlencode(parametros))

    diga("\n2) Abra esta URL no navegador e entre como %s (senha: logitech)" % args.usuario)
    diga("   %s\n" % url)
    diga("   Repare: nao ha senha nenhuma nesta URL, e nao ha segredo de cliente.")
    diga("   O portal e um client PUBLICO: qualquer segredo embutido nele estaria")
    diga("   visivel na aba de rede do navegador.\n")

    if not args.sem_navegador:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    codigo = esperar_codigo(estado)
    diga("3) O Keycloak redirecionou para %s com:" % REDIRECT_URI)
    diga("   code  = %s" % codigo)
    diga("   state = confere com o que enviamos\n")
    diga("   Este codigo vale UMA vez e por poucos segundos. Sozinho ele nao serve")
    diga("   para nada: falta o verificador.\n")

    # -------------------------------------------------------------------
    # 3. A troca
    # -------------------------------------------------------------------
    corpo = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": codigo,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
    }).encode("utf-8")

    endereco = "%s/realms/%s/protocol/openid-connect/token" % (KEYCLOAK, REALM)
    with urllib.request.urlopen(endereco, data=corpo, timeout=15) as r:
        resposta = json.loads(r.read())

    acesso = resposta["access_token"]

    if args.so_token:
        print(acesso)
        return

    cabecalho, conteudo, assinatura = acesso.split(".")
    print("4) Troca do codigo pelo token, com o code_verifier junto")
    print("   POST %s" % endereco)
    print("   expires_in = %s segundos" % resposta["expires_in"])
    print("   o access_token tem %d caracteres, em tres partes\n" % len(acesso))

    print("   CABECALHO")
    print("   " + json.dumps(decodificar(cabecalho), indent=2, ensure_ascii=False).replace("\n", "\n   "))

    dados = decodificar(conteudo)
    print("\n   CONTEUDO (os campos que importam hoje)")
    for campo in ("iss", "sub", "azp", "typ", "preferred_username", "iat", "exp"):
        print("     %-20s %s" % (campo, dados.get(campo)))
    print("     %-20s %s" % ("realm_access.roles", dados.get("realm_access", {}).get("roles")))
    print("     %-20s %s" % ("resource_access", dados.get("resource_access", {})
                             or "{}   <- vazio, e e por isso que ninguem le daqui"))
    print("     %-20s %s segundos" % ("exp - iat", dados["exp"] - dados["iat"]))

    print("\n   ASSINATURA (%d caracteres, base64url, NAO e criptografia:" % len(assinatura))
    print("   qualquer um le o conteudo acima; o que ninguem consegue e altera-lo")
    print("   sem invalidar estes bytes)")
    print("   %s..." % assinatura[:64])

    print("\n5) Agora sim, o curl. O token expira em %s segundos." % resposta["expires_in"])
    print("   export TOKEN='%s'" % acesso)
    print("   curl -i -H \"Authorization: Bearer $TOKEN\" http://localhost:8080/api/v1/pedidos")


if __name__ == "__main__":
    try:
        principal()
    except KeyboardInterrupt:
        sys.exit(130)
