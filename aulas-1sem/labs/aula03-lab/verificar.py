#!/usr/bin/env python3
"""Verificador progressivo do laboratório da Aula 03 (Docker, LogiTech Enterprise).

Confere, etapa por etapa, se o que o aluno entregou de fato cumpre o critério
daquele ciclo: nada de confiar em "eu fiz", tudo é lido do disco ou perguntado
direto ao Docker. Sem dependências externas: só a biblioteca padrão.

Uso:
    python3 verificar.py             # roda as sete etapas
    python3 verificar.py --etapa 4   # roda só a etapa 4

Saída: 0 quando tudo que foi pedido passa, 1 quando alguma etapa falha.
"""
import argparse
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))

LIMITE_REDUCAO = 80.0   # confirmado por medição real na Tarefa 1: 95,2% e 86,2%


def docker(*args):
    """Executa o comando docker e devolve (código, saída). Nunca levanta
    exceção, mesmo se o Docker não estiver instalado, não responder ou
    travar: o pior caso vira uma falha reportada normalmente pela etapa."""
    try:
        p = subprocess.run(["docker", *args], capture_output=True,
                            text=True, timeout=60)
        return p.returncode, p.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def ler(caminho):
    """Lê um arquivo relativo à raiz do laboratório. Devolve string vazia
    quando o arquivo não existe, para as etapas tratarem isso como "ainda
    não preenchido" em vez de estourar exceção."""
    p = os.path.join(RAIZ, caminho)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


def _valor_preenchido(marcador, texto):
    """Extrai o valor de um marcador do tipo 'MARCADOR: valor' e recusa
    tanto ausência quanto o texto de esqueleto 'PREENCHER', que passaria
    despercebido por um regex de presença simples."""
    m = re.search(r"%s:\s*(\S.*)" % re.escape(marcador), texto)
    valor = m.group(1).strip() if m else ""
    if not valor or valor.upper() == "PREENCHER":
        return None
    return valor


def etapa_1():
    """Isolamento de processos: PID visto de dentro do container tem que
    ser diferente do PID visto de fora, senão não prova isolamento nenhum."""
    txt = ler("etapas/01-isolamento/RESPOSTAS.md")
    if not txt:
        return False, "etapas/01-isolamento/RESPOSTAS.md não existe."
    marcadores = ("PID_DENTRO", "PID_FORA", "HOSTNAME_DENTRO", "MOUNTS_DENTRO")
    valores = {m: _valor_preenchido(m, txt) for m in marcadores}
    faltando = [m for m, v in valores.items() if v is None]
    if faltando:
        return False, "Sem valor preenchido para: %s" % ", ".join(faltando)
    if not valores["PID_DENTRO"].isdigit() or not valores["PID_FORA"].isdigit():
        return False, "PID_DENTRO e PID_FORA precisam ser números."
    if valores["PID_DENTRO"] == valores["PID_FORA"]:
        return False, ("PID_DENTRO e PID_FORA iguais: isso não comprova "
                        "isolamento de processos.")
    return True, ""


def etapa_2():
    """Imagem, camadas e efemeridade: o coletor rodou sobre a imagem base
    pedida, e o aluno provou que o container é descartável (o arquivo some
    junto com o container removido)."""
    txt = ler("etapas/02-imagem/RESPOSTAS.md")
    if not txt:
        return False, "etapas/02-imagem/RESPOSTAS.md não existe."
    if "python:3.12-alpine" not in txt:
        return False, ("Registre em etapas/02-imagem/RESPOSTAS.md o docker ps "
                        "do coletor rodando sobre python:3.12-alpine.")
    if not re.search(r"ARQUIVO_APOS_RM:\s*(sumiu|ausente)", txt, re.I):
        return False, ("Falta a prova da efemeridade: ARQUIVO_APOS_RM deve "
                        "dizer que o arquivo sumiu depois do docker rm.")
    return True, ""


def etapa_3():
    """Dockerfile e build: existe um Dockerfile.coletor na raiz do laboratório
    e ele builda de verdade, sem erro."""
    if not ler("Dockerfile.coletor"):
        return False, "Dockerfile.coletor não existe na raiz do laboratório."
    cod, _ = docker("build", "-f", os.path.join(RAIZ, "Dockerfile.coletor"),
                     "-t", "verificar-coletor:etapa3", RAIZ)
    if cod != 0:
        return False, "docker build do Dockerfile.coletor falhou."
    return True, ""


def _estagios_e_usuario(caminho):
    """Conta estágios nomeados (FROM ... AS ...) e verifica se existe um
    USER declarado que não seja root, sem executar o build: é leitura de
    texto do próprio Dockerfile."""
    txt = ler(caminho)
    estagios = len(re.findall(r"^\s*FROM\s+\S+\s+AS\s+\S+", txt, re.M | re.I))
    tem_user = bool(re.search(r"^\s*USER\s+(?!root\b)\S+", txt, re.M | re.I))
    return estagios, tem_user


def etapa_4():
    """Multi-stage: os dois Dockerfiles finais têm ao menos dois estágios
    nomeados, rodam com usuário não-root, e a redução de tamanho medida
    bate o mínimo estabelecido na Tarefa 1."""
    for arq in ("Dockerfile.coletor", "Dockerfile.gateway"):
        est, user = _estagios_e_usuario(arq)
        if est < 2:
            return False, "%s tem %d estágio nomeado, precisa de 2." % (arq, est)
        if not user:
            return False, "%s não declara USER não-root." % arq
    txt = ler("docs/EVIDENCIAS.md")
    if not txt:
        return False, "docs/EVIDENCIAS.md não existe."
    reducoes = [float(x) for x in re.findall(r"REDUCAO_\w+:\s*([\d.]+)\s*%", txt)]
    if len(reducoes) < 2:
        return False, ("docs/EVIDENCIAS.md precisa de REDUCAO_COLETOR e "
                        "REDUCAO_GATEWAY, em percentual.")
    if min(reducoes) < LIMITE_REDUCAO:
        return False, "Redução de %.1f%% abaixo do mínimo de %.1f%%." % (
            min(reducoes), LIMITE_REDUCAO)
    return True, ""


def etapa_5():
    """Volumes: o volume nomeado existe de verdade no Docker, e o aluno
    provou que os dados sobrevivem à remoção do container."""
    cod, out = docker("volume", "ls", "--format", "{{.Name}}")
    if cod != 0 or "logitech-telemetria" not in out.split():
        return False, "O volume logitech-telemetria não existe."
    txt = ler("docs/EVIDENCIAS.md")
    if not re.search(r"LINHAS_APOS_RM:\s*[1-9]\d*", txt):
        return False, ("Registre LINHAS_APOS_RM em docs/EVIDENCIAS.md com o "
                        "número de linhas que sobreviveram ao docker rm.")
    return True, ""


def etapa_6():
    """Network e observação: a rede nomeada existe, e o aluno registrou o
    consumo de memória do coletor visto pelo docker stats."""
    cod, out = docker("network", "ls", "--format", "{{.Name}}")
    if cod != 0 or "logitech-net" not in out.split():
        return False, "A rede logitech-net não existe."
    txt = ler("docs/EVIDENCIAS.md")
    if not re.search(r"MEMORIA_COLETOR_MB:\s*[\d.]+", txt):
        return False, ("Registre MEMORIA_COLETOR_MB em docs/EVIDENCIAS.md, "
                        "lido do docker stats.")
    return True, ""


def etapa_7():
    """Registry e Docker Hub: a imagem publicada pelo aluno responde de
    verdade num registry público, não é só um nome anotado no documento."""
    txt = ler("docs/EVIDENCIAS.md")
    m = re.search(r"IMAGEM_PUBLICA:\s*(\S+/\S+:\S+)", txt)
    if not m:
        return False, ("Registre IMAGEM_PUBLICA em docs/EVIDENCIAS.md no "
                        "formato usuario/logitech-coletor:1.0")
    cod, _ = docker("manifest", "inspect", m.group(1))
    if cod != 0:
        return False, "A imagem %s não responde no registry." % m.group(1)
    return True, ""


ETAPAS = [
    (1, "Isolamento de processos", etapa_1),
    (2, "Imagem, camadas e efemeridade", etapa_2),
    (3, "Dockerfile e build", etapa_3),
    (4, "Multi-stage", etapa_4),
    (5, "Volumes", etapa_5),
    (6, "Network e observação", etapa_6),
    (7, "Registry e Docker Hub", etapa_7),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--etapa", type=int, choices=range(1, 8),
                     help="valida só a etapa indicada, em vez das sete")
    args = ap.parse_args()
    alvo = [e for e in ETAPAS if args.etapa is None or e[0] == args.etapa]
    ok = 0
    for num, nome, fn in alvo:
        passou, motivo = fn()
        print("  [%s] Etapa %d: %s" % ("OK" if passou else "  ", num, nome))
        if passou:
            ok += 1
        else:
            print("         %s" % motivo)
    print("\n  %d de %d" % (ok, len(alvo)))
    return 0 if ok == len(alvo) else 1


if __name__ == "__main__":
    sys.exit(main())
