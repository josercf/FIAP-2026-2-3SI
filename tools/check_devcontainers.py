#!/usr/bin/env python3
"""
Valida os devcontainers dos laboratorios contra o apodrecimento da imagem base.

O defeito que motivou esta ferramenta apareceu em sala, na Aula 05 de
08/09/2026: as imagens oficiais devcontainers/java, devcontainers/python e
devcontainers/universal trazem o repositorio apt do Yarn pre-configurado, e a
chave GPG dele expirou (NO_PUBKEY 62D54FD4003F6525). Como todo feature do
devcontainer comeca por um apt-get update, o apt passou a sair com codigo 100,
o feature abortava, o build caia inteiro e o Codespaces entregava um container
de recuperacao sem Docker, sem Java e sem .NET. Nenhuma linha do laboratorio
tinha mudado.

Tres checagens, porque sao tres defeitos diferentes:

1. APT SAO. Roda apt-get update dentro da imagem base de cada lab e exige
   codigo 0. Pega repositorio com chave expirada, removida ou fora do ar, que e
   a classe de falha acima. E a checagem barata: nao constroi nada.

2. FEATURE RESOLVIVEL. Confere que cada feature declarado existe no registro.
   O lab 12 declarava ghcr.io/devcontainers/features/postgresql-client:1, que
   nao existe e devolve 403, derrubando o build sozinho.

3. BUILD E FERRAMENTAS (--build). Constroi o devcontainer de verdade, com os
   features, e confere dentro do container que os binarios prometidos existem.
   E a unica checagem que pega o que passou pelas duas primeiras: na Aula 05, a
   imagem nao trazia Maven, o feature dotnet sem versao instalava o SDK 10
   contra um global.json que pedia 8, e o Python vinha sem a biblioteca padrao.

Uso:
    python3 tools/check_devcontainers.py                 # checagens 1 e 2, rapido
    python3 tools/check_devcontainers.py --build         # inclui a checagem 3
    python3 tools/check_devcontainers.py aula05-lab      # um lab so

Requer: docker. A checagem 3 requer tambem npx (@devcontainers/cli).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABS = os.path.join(RAIZ, "aulas-1sem", "labs")

# Plataforma fixa: o Codespaces roda amd64, e varias imagens do acervo nao tem
# variante arm64. Sem isto, a checagem passaria no Mac e mentiria sobre a aula.
PLATAFORMA = "linux/amd64"

VERDE, VERMELHO, AMARELO, FIM = "\033[92m", "\033[91m", "\033[93m", "\033[0m"


def cor(texto, c):
    return f"{c}{texto}{FIM}" if sys.stdout.isatty() else texto


def labs_do_acervo(filtro=None):
    achados = []
    for nome in sorted(os.listdir(LABS)):
        caminho = os.path.join(LABS, nome, ".devcontainer", "devcontainer.json")
        if os.path.isfile(caminho) and (filtro is None or nome in filtro):
            achados.append((nome, caminho))
    return achados


def ler_config(caminho):
    """Le o devcontainer.json tolerando comentarios, que a spec permite."""
    with open(caminho, encoding="utf-8") as arq:
        bruto = arq.read()
    bruto = re.sub(r"^\s*//.*$", "", bruto, flags=re.M)
    return json.loads(bruto)


def imagem_efetiva(nome, config, caminho):
    """
    Devolve a imagem sobre a qual os features vao rodar, e um rotulo para exibir.

    Quando o lab declara "image", e ela mesma. Quando declara "build", os
    features rodam sobre o resultado do Dockerfile, e nao sobre o FROM: e
    exatamente ali que mora o saneamento do apt. Checar o FROM reprovaria a
    correcao correta, entao construimos o estagio do usuario, que e barato.
    """
    if config.get("image"):
        return config["image"], config["image"].split("/")[-1]

    build = config.get("build") or {}
    dockerfile = build.get("dockerfile")
    if not dockerfile:
        return None, None
    contexto = os.path.dirname(caminho)
    alvo = os.path.join(contexto, dockerfile)
    if not os.path.isfile(alvo):
        return None, None

    origem = "?"
    with open(alvo, encoding="utf-8") as arq:
        for linha in arq:
            achado = re.match(r"\s*FROM\s+(\S+)", linha)
            if achado:
                origem = achado.group(1).split("/")[-1]
                break

    tag = "checkdc-base-%s:validacao" % nome
    proc = subprocess.run(
        ["docker", "build", "--platform", PLATAFORMA, "-f", alvo, "-t", tag, contexto],
        capture_output=True, text=True, timeout=3600)
    if proc.returncode != 0:
        return None, "%s (Dockerfile nao construiu)" % origem
    return tag, "%s, saneada pelo Dockerfile" % origem


def apt_sao(imagem):
    """Checagem 1: apt-get update precisa sair com zero na imagem base."""
    proc = subprocess.run(
        ["docker", "run", "--rm", "--platform", PLATAFORMA, "--user", "root", imagem,
         "bash", "-c", "apt-get update >/dev/null 2>/tmp/e; echo EXIT=$?; "
                       "grep -E '^E:' /tmp/e | head -2 || true"],
        capture_output=True, text=True, timeout=900)
    saida = proc.stdout + proc.stderr
    achado = re.search(r"EXIT=(\d+)", saida)
    if not achado:
        return False, "nao consegui rodar o apt-get update: %s" % saida.strip()[:200]
    codigo = int(achado.group(1))
    if codigo != 0:
        erros = [l for l in saida.splitlines() if l.startswith("E:")]
        return False, ("apt-get update saiu com %d na imagem base. %s "
                       "Todo feature comeca por um apt-get update: com o apt "
                       "quebrado, o build inteiro do devcontainer falha e o "
                       "Codespaces entrega um container de recuperacao."
                       % (codigo, " ".join(erros)[:200]))
    return True, ""


def feature_resolvivel(referencia):
    """Checagem 2: o feature declarado precisa existir no registro."""
    limpa = referencia.split("://")[-1]
    if not limpa.startswith("ghcr.io/"):
        return True, ""  # so sabemos consultar o ghcr
    corpo, _, tag = limpa[len("ghcr.io/"):].rpartition(":")
    if not corpo:
        corpo, tag = limpa[len("ghcr.io/"):], "latest"
    try:
        with urllib.request.urlopen(
                "https://ghcr.io/token?scope=repository:%s:pull" % corpo, timeout=30) as resp:
            token = json.load(resp).get("token", "")
        req = urllib.request.Request(
            "https://ghcr.io/v2/%s/manifests/%s" % (corpo, tag),
            headers={"Authorization": "Bearer %s" % token,
                     "Accept": "application/vnd.oci.image.manifest.v1+json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                return True, ""
    except Exception as erro:
        return False, ("o feature %s nao pode ser resolvido no registro (%s). "
                       "Um feature inexistente derruba o build do devcontainer "
                       "sozinho." % (referencia, getattr(erro, "code", erro)))
    return False, "o feature %s nao pode ser resolvido no registro." % referencia


def binarios_esperados(config):
    """Os binarios que os features declarados prometem entregar."""
    features = list(config.get("features", {}).keys())
    esperados = []
    for feature, binario in (("docker-in-docker", "docker"), ("docker-outside", "docker"),
                             ("/node", "node"), ("/java", "java"), ("/dotnet", "dotnet"),
                             ("github-cli", "gh"), ("/python", "python3")):
        if any(feature in f for f in features) and binario not in esperados:
            esperados.append(binario)
    return esperados


def build_e_ferramentas(nome, config):
    """Checagem 3: constroi de verdade e confere as ferramentas dentro."""
    tag = "checkdc-%s:validacao" % nome
    proc = subprocess.run(
        ["npx", "--yes", "@devcontainers/cli@latest", "build",
         "--workspace-folder", os.path.join(LABS, nome),
         "--platform", PLATAFORMA, "--image-name", tag],
        capture_output=True, text=True, timeout=3600)
    if '"outcome":"success"' not in (proc.stdout + proc.stderr):
        erro = re.search(r'"message":"([^"]{0,300})', proc.stdout + proc.stderr)
        return False, "o build do devcontainer falhou. %s" % (erro.group(1) if erro else "")

    esperados = binarios_esperados(config)
    if not esperados:
        return True, ""
    script = "; ".join("command -v %s >/dev/null || echo FALTA=%s" % (b, b) for b in esperados)
    proc = subprocess.run(
        ["docker", "run", "--rm", "--platform", PLATAFORMA, tag, "bash", "-lc", script],
        capture_output=True, text=True, timeout=600)
    faltando = re.findall(r"FALTA=(\S+)", proc.stdout + proc.stderr)
    if faltando:
        return False, ("o build passou, mas faltam no container: %s. Feature "
                       "declarado nao garante binario no PATH."
                       % ", ".join(faltando))
    return True, ""


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("labs", nargs="*", help="labs a checar (padrao: todos)")
    parser.add_argument("--build", action="store_true",
                        help="constroi cada devcontainer e confere as ferramentas dentro")
    args = parser.parse_args()

    alvos = labs_do_acervo(set(args.labs) if args.labs else None)
    if not alvos:
        print("nenhum lab encontrado em %s" % LABS)
        return 1

    problemas = 0
    for nome, caminho in alvos:
        config = ler_config(caminho)
        print("\n%s" % nome)
        imagem, rotulo = imagem_efetiva(nome, config, caminho)

        if not imagem:
            print("  %s nao consegui preparar a imagem base%s"
                  % (cor("FALHA", VERMELHO), ": " + rotulo if rotulo else ""))
            problemas += 1
            continue

        ok, motivo = apt_sao(imagem)
        print("  %s apt da base (%s)%s" % (cor("OK", VERDE) if ok else cor("FALHA", VERMELHO),
                                           rotulo,
                                           "" if ok else "\n       " + motivo))
        problemas += 0 if ok else 1

        quebrados = 0
        for feature in config.get("features", {}):
            ok, motivo = feature_resolvivel(feature)
            if not ok:
                print("  %s %s\n       %s" % (cor("FALHA", VERMELHO),
                                              feature.split("/")[-1], motivo))
                problemas += 1
                quebrados += 1
        if config.get("features") and not quebrados:
            print("  %s features resolvem no registro (%d)"
                  % (cor("OK", VERDE), len(config["features"])))

        if args.build:
            ok, motivo = build_e_ferramentas(nome, config)
            print("  %s build e ferramentas%s"
                  % (cor("OK", VERDE) if ok else cor("FALHA", VERMELHO),
                     "" if ok else "\n       " + motivo))
            problemas += 0 if ok else 1

    print("\n" + "=" * 62)
    if problemas:
        print(cor("%d problema(s). Um devcontainer quebrado so aparece quando a "
                  "turma abre o Codespace." % problemas, VERMELHO))
        return 1
    print(cor("Todos os devcontainers estao sãos.", VERDE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
