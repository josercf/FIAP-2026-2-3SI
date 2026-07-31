#!/usr/bin/env python3
"""Verificador progressivo do laboratório da Aula 03 (Docker, LogiTech Enterprise).

Confere, etapa por etapa, se o que o aluno entregou de fato cumpre o critério
daquele ciclo: nada de confiar em "eu fiz", tudo é lido do disco ou perguntado
direto ao Docker. Sem dependências externas: só a biblioteca padrão.

Uso:
    python3 verificar.py             # roda as sete etapas
    python3 verificar.py --etapa 4   # roda só a etapa 4

Saída: 0 quando tudo que foi pedido passa, 1 quando alguma etapa falha.

Limite conhecido, e por isso documentado à parte no relatório da Tarefa 4:
nem tudo aqui é verificação de máquina. Algumas etapas conferem, na medida
do possível, a plausibilidade do que o aluno declarou, mas não recriam o
container que já foi destruído para gerar aquela evidência. A tabela
"o que é verificado por máquina e o que é declarado pelo aluno" está no
relatório da Tarefa 4 e deve migrar para o README numa tarefa futura.
"""
import argparse
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))

LIMITE_REDUCAO = 80.0     # confirmado por medição real na Tarefa 1: 95,2% e 86,2%
TIMEOUT_PADRAO = 60       # consultas rápidas: volume ls, network ls, manifest inspect
TIMEOUT_BUILD = 300       # docker build: com trinta alunos baixando imagem base junto,
                          # 60s estoura por motivo nenhum relacionado ao Dockerfile
LIMITE_PID_DENTRO = 50    # PID visto de dentro de um container recém-criado é baixo
LIMITE_PID_FORA = 100     # PID visto do host quase nunca é este baixo


def docker(*args, tempo_limite=TIMEOUT_PADRAO):
    """Executa um comando docker e devolve (código, stdout, stderr).

    Nunca levanta exceção. Estouro de tempo devolve o código sentinela 124
    (a mesma convenção do utilitário `timeout` do Unix) com uma mensagem
    própria em stderr, para quem chamou conseguir dizer ao aluno "o Docker
    não respondeu a tempo" em vez de "seu Dockerfile está errado": são
    diagnósticos diferentes e pedem ações diferentes."""
    comando = " ".join(args)
    try:
        p = subprocess.run(["docker", *args], capture_output=True,
                            text=True, timeout=tempo_limite)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", (
            "o comando 'docker %s' não respondeu em %ds (tempo esgotado; "
            "isso não significa necessariamente que o Dockerfile está "
            "errado, só que o Docker demorou mais do que o esperado)."
            % (comando, tempo_limite))
    except OSError as erro:
        return 1, "", "não foi possível executar o docker: %s" % erro


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


def _para_float(texto):
    """Converte um número em texto para float aceitando tanto '95.2' quanto
    '95,2', a convenção decimal em português usada no restante do material.
    Sem isso, a vírgula corta o número no meio silenciosamente."""
    return float(texto.strip().replace(",", "."))


def _ultimas_linhas(texto, n=6):
    """Corta uma saída de erro longa para as últimas linhas, que costumam
    conter o motivo real da falha (o BuildKit imprime o log inteiro do
    build antes de reportar onde quebrou)."""
    linhas = [l for l in texto.splitlines() if l.strip()]
    if not linhas:
        return "(o Docker não devolveu detalhe nenhum em stderr)"
    return "\n".join(linhas[-n:])


def _builda(dockerfile, tag):
    """Roda um docker build de verdade para o Dockerfile indicado. Devolve
    (passou, motivo). Usa TIMEOUT_BUILD, bem mais folgado que o timeout
    padrão, porque build baixa imagem base e instala dependência, coisa
    que uma consulta como 'docker volume ls' nunca precisa fazer."""
    caminho = os.path.join(RAIZ, dockerfile)
    cod, _, erro = docker("build", "-f", caminho, "-t", tag, RAIZ,
                           tempo_limite=TIMEOUT_BUILD)
    if cod == 124:
        return False, erro
    if cod != 0:
        return False, "docker build de %s falhou:\n%s" % (
            dockerfile, _ultimas_linhas(erro))
    return True, ""


def etapa_1():
    """Isolamento de processos: PID visto de dentro do container tem que
    ser plausivelmente diferente do PID visto de fora (não só diferente:
    baixo dentro, alto fora, como um container recém-criado de verdade
    produz), e o hostname precisa ter o formato que o Docker gera sozinho.
    MOUNTS_DENTRO continua sem checagem de máquina possível: ver a tabela
    de limites no relatório da Tarefa 4."""
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
    pid_dentro, pid_fora = int(valores["PID_DENTRO"]), int(valores["PID_FORA"])
    if pid_dentro == pid_fora:
        return False, ("PID_DENTRO e PID_FORA iguais: isso não comprova "
                        "isolamento de processos.")
    if pid_dentro > LIMITE_PID_DENTRO:
        return False, (
            "PID_DENTRO = %d parece alto demais para o início da árvore de "
            "processos de um container recém-criado (esperado até %d)." %
            (pid_dentro, LIMITE_PID_DENTRO))
    if pid_fora < LIMITE_PID_FORA:
        return False, (
            "PID_FORA = %d parece baixo demais para um processo visto do "
            "host (esperado pelo menos %d); confira se não trocou "
            "PID_DENTRO com PID_FORA." % (pid_fora, LIMITE_PID_FORA))
    if not re.match(r"^[0-9a-f]{12}$", valores["HOSTNAME_DENTRO"], re.I):
        return False, (
            "HOSTNAME_DENTRO não tem o formato que o Docker gera sozinho "
            "(12 caracteres hexadecimais, o início do ID do container).")
    return True, ""


def etapa_2():
    """Imagem, camadas e efemeridade: exige o ID real do container (não uma
    frase qualquer) e a linha de 'docker image ls' mostrando a imagem base,
    porque quando o aluno roda o verificador o container já foi destruído
    de propósito (a etapa é sobre isso) e não há mais estado para reabrir e
    conferir. É o limite descrito na tabela do relatório da Tarefa 4."""
    txt = ler("etapas/02-imagem/RESPOSTAS.md")
    if not txt:
        return False, "etapas/02-imagem/RESPOSTAS.md não existe."
    if not re.search(r"CONTAINER_ID:\s*[0-9a-f]{12,64}\b", txt, re.I):
        return False, (
            "Registre CONTAINER_ID em etapas/02-imagem/RESPOSTAS.md com o ID "
            "hexadecimal real do container (de docker ps ou docker inspect), "
            "não uma frase solta.")
    if not re.search(r"^\s*python\s+3\.12-alpine\s+[0-9a-f]{6,64}",
                      txt, re.M | re.I):
        return False, (
            "Cole a linha de docker image ls mostrando a imagem "
            "python:3.12-alpine (repositório, tag e IMAGE ID), não só o "
            "nome da imagem citado em texto corrido.")
    if not re.search(r"ARQUIVO_APOS_RM:\s*(sumiu|ausente)", txt, re.I):
        return False, ("Falta a prova da efemeridade: ARQUIVO_APOS_RM deve "
                        "dizer que o arquivo sumiu depois do docker rm.")
    return True, ""


def etapa_3():
    """Dockerfile e build: existe um Dockerfile.coletor na raiz do
    laboratório e ele builda de verdade, sem erro."""
    if not ler("Dockerfile.coletor"):
        return False, "Dockerfile.coletor não existe na raiz do laboratório."
    return _builda("Dockerfile.coletor", "verificar-coletor:etapa3")


def _estagios_e_usuario(caminho):
    """Conta estágios de build (qualquer FROM, nomeado ou não: o Docker não
    exige nome no estágio final, e não nomeá-lo é prática comum e correta)
    e verifica se existe um USER declarado que não seja root. É leitura de
    texto do próprio Dockerfile, sem executar build."""
    txt = ler(caminho)
    estagios = len(re.findall(r"^\s*FROM\s+\S+", txt, re.M | re.I))
    tem_user = bool(re.search(r"^\s*USER\s+(?!root\b)\S+", txt, re.M | re.I))
    return estagios, tem_user


def etapa_4():
    """Multi-stage: os dois Dockerfiles finais têm ao menos dois estágios,
    rodam com usuário não-root, buildam de verdade (os dois, não só o
    coletor) e a redução de tamanho medida bate o mínimo da Tarefa 1."""
    for arq in ("Dockerfile.coletor", "Dockerfile.gateway"):
        if not ler(arq):
            return False, "%s não existe na raiz do laboratório." % arq
        est, user = _estagios_e_usuario(arq)
        if est < 2:
            return False, "%s tem %d estágio(s) FROM, precisa de 2." % (arq, est)
        if not user:
            return False, "%s não declara USER não-root." % arq

    passou, motivo = _builda("Dockerfile.coletor", "verificar-coletor:etapa4")
    if not passou:
        return False, motivo
    passou, motivo = _builda("Dockerfile.gateway", "verificar-gateway:etapa4")
    if not passou:
        return False, motivo

    txt = ler("docs/EVIDENCIAS.md")
    if not txt:
        return False, "docs/EVIDENCIAS.md não existe."
    brutos = re.findall(r"REDUCAO_\w+:\s*([\d,.]+)\s*%", txt)
    if len(brutos) < 2:
        return False, ("docs/EVIDENCIAS.md precisa de REDUCAO_COLETOR e "
                        "REDUCAO_GATEWAY, em percentual.")
    try:
        reducoes = [_para_float(x) for x in brutos]
    except ValueError:
        return False, "Algum valor de REDUCAO_* não é um número válido."
    if min(reducoes) < LIMITE_REDUCAO:
        return False, "Redução de %.1f%% abaixo do mínimo de %.1f%%." % (
            min(reducoes), LIMITE_REDUCAO)
    return True, ""


def etapa_5():
    """Volumes: o volume nomeado existe de verdade no Docker, e o aluno
    provou que os dados sobrevivem à remoção do container."""
    cod, out, erro = docker("volume", "ls", "--format", "{{.Name}}")
    if cod == 124:
        return False, erro
    if cod != 0 or "logitech-telemetria" not in out.split():
        return False, "O volume logitech-telemetria não existe."
    txt = ler("docs/EVIDENCIAS.md")
    if not re.search(r"LINHAS_APOS_RM:\s*[1-9]\d*", txt):
        return False, ("Registre LINHAS_APOS_RM em docs/EVIDENCIAS.md com o "
                        "número de linhas que sobreviveram ao docker rm.")
    return True, ""


def etapa_6():
    """Network e observação: a rede nomeada existe, e o aluno registrou um
    consumo de memória plausível do coletor, lido do docker stats."""
    cod, out, erro = docker("network", "ls", "--format", "{{.Name}}")
    if cod == 124:
        return False, erro
    if cod != 0 or "logitech-net" not in out.split():
        return False, "A rede logitech-net não existe."
    txt = ler("docs/EVIDENCIAS.md")
    m_mem = re.search(r"MEMORIA_COLETOR_MB:\s*([\d,.]+)", txt)
    if not m_mem:
        return False, ("Registre MEMORIA_COLETOR_MB em docs/EVIDENCIAS.md, "
                        "lido do docker stats.")
    try:
        memoria = _para_float(m_mem.group(1))
    except ValueError:
        return False, "MEMORIA_COLETOR_MB não parece um número válido."
    if memoria <= 0:
        return False, "MEMORIA_COLETOR_MB precisa ser um valor positivo."
    return True, ""


def etapa_7():
    """Registry e Docker Hub: a imagem publicada pelo aluno responde de
    verdade num registry público. Distingue "não foi possível alcançar o
    registry" (sem rede, DNS ou o registry fora do ar) de "a imagem em si
    tem problema" (não existe, está privada sem login, ou nome/tag errados):
    são dois problemas diferentes e pedem ações diferentes do aluno.

    Atenção ao classificar: o Docker Hub devolve a mesma mensagem de acesso
    negado ('denied: requested access to the resource is denied') tanto
    para uma imagem que nunca existiu quanto para uma privada sem login,
    por desenho (evita revelar quais repositórios privados existem). Por
    isso o bucket "sem rede" é o específico (procura assinatura de falha de
    conexão/DNS) e o de "problema na imagem" é o padrão: cobre esse caso
    de acesso negado, que na prática é o mais comum quando o aluno erra o
    nome, a tag, ou esquece o push."""
    txt = ler("docs/EVIDENCIAS.md")
    m = re.search(r"IMAGEM_PUBLICA:\s*(\S+/\S+:\S+)", txt)
    if not m:
        return False, ("Registre IMAGEM_PUBLICA em docs/EVIDENCIAS.md no "
                        "formato usuario/logitech-coletor:1.0")
    imagem = m.group(1)
    cod, _, erro = docker("manifest", "inspect", imagem)
    if cod == 124:
        return False, erro
    if cod != 0:
        padrao_rede = (r"dial tcp|no such host|i/o timeout|"
                        r"context deadline exceeded|connection refused|"
                        r"tls handshake|network is unreachable")
        if re.search(padrao_rede, erro, re.I):
            return False, (
                "Não foi possível alcançar o registry para verificar %s "
                "(sem rede, DNS ou o registry fora do ar). Detalhe do "
                "Docker:\n%s" % (imagem, _ultimas_linhas(erro)))
        return False, (
            "A imagem %s não existe nesse registry, está privada sem "
            "login, ou o nome/tag estão errados. Detalhe do Docker:\n%s" %
            (imagem, _ultimas_linhas(erro)))
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
