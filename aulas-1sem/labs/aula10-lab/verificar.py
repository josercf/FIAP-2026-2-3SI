#!/usr/bin/env python3
"""Verificador do laboratório da Aula 10 (testes de unidade e React).

O que ele faz de diferente dos verificadores das aulas anteriores: nas aulas
passadas a régua era o **código** do aluno, e bastava executá-lo. Hoje o
entregável é o **teste**, e teste se avalia de um jeito só, que é vendo se
ele reprova código errado.

Então este verificador estraga o código de propósito. Ele copia o serviço de
frete e o portal para um diretório temporário, aplica um defeito conhecido na
cópia, roda a **sua** suíte contra ela e exige que ela fique vermelha. A
técnica tem nome, teste de mutação, e o defeito plantado se chama mutante.
Suíte que continua verde contra um mutante é suíte que não protege nada.

Os mutantes de interação são os interessantes: eles não mudam **nenhum**
número devolvido, só a colaboração entre os objetos. Nenhuma asserção sobre
resultado os pega. É essa a diferença entre Stub e Mock, medida por máquina.

Nada aqui confia em "eu fiz": ou a suíte é executada de verdade, ou o
arquivo é lido do disco.

Sem dependências externas: só a biblioteca padrão. O `pytest` e o `vitest`
são chamados como processos, exatamente como você os chamaria à mão.

Uso:
    python3 verificar.py                # roda os oito critérios
    python3 verificar.py --criterio 2   # roda só um critério
    python3 verificar.py --lista        # mostra o que cada critério cobra

Saída: 0 quando todos os critérios pedidos passam, 1 quando algum falha.
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.abspath(__file__))
FRETE = os.path.join(RAIZ, "servicos", "frete")
PORTAL = os.path.join(RAIZ, "portal")
EVIDENCIAS = os.path.join("docs", "EVIDENCIAS.md")

TEMPO_LIMITE_CURTO = 120
TEMPO_LIMITE_TESTES = 420   # a primeira execução do vitest compila TypeScript

# Piso de cada arquivo de teste. Os números são os do enunciado de cada
# lacuna: quem escrever menos do que foi pedido reprova aqui, e é essa a
# intenção.
MINIMO_STUB = 4
MINIMO_MOCK = 3
MINIMO_SPY = 3
MINIMO_CHAMADA = 2

# Piso das suítes inteiras. Dez testes já vêm prontos no `test_estrategias.py`
# e sete nos dois arquivos de tela do portal.
MINIMO_TESTES_PYTEST = 20
MINIMO_TESTES_VITEST = 9

# Impressão digital de `servicos/frete/tests/conftest.py` como ele foi
# entregue, com espaços à direita e fim de linha normalizados. É o arquivo
# que bloqueia a rede durante os testes; desligar o bloqueio para "fazer o
# teste passar" reprova o critério 4.
HASH_CONFTEST = "03e9c5ed21d847e80c9d187e5165a27a25161ecbd90b0789bbb0800166465fa6"

# Valores de referência da plataforma, conferidos contra `docs/EVIDENCIAS.md`.
VALOR_EXPRESSO_PED_1001 = 545.00      # SAO -> LDB, 500 km, 100 kg
VALOR_PADRAO_PED_1003 = 9956.24       # BHZ -> SSA, 1370 km, 12500 kg, com desconto
PRAZO_PADRAO_PED_1003 = 5             # 4 dias de tabela mais 1 de pernoite


# ---------------------------------------------------------------------------
# Os mutantes
# ---------------------------------------------------------------------------
# Cada entrada é (arquivo relativo, trecho original, trecho estragado).
# `estado` muda o número devolvido; `interacao` não muda número nenhum, só a
# colaboração entre os objetos.
MUTANTES_FRETE = {
    "M1": ("estado", "app/estrategias.py",
           "    custo_por_km = 0.85\n",
           "    custo_por_km = 0.95\n",
           "a tabela de preços do expresso subiu de 0,85 para 0,95 por km"),

    "M2": ("estado", "app/cotador.py",
           "DESCONTO_CARGA_FECHADA = 0.08\n",
           "DESCONTO_CARGA_FECHADA = 0.0\n",
           "o desconto de carga fechada foi zerado"),

    "M3": ("interacao", "app/cotador.py",
           "        if pedido_id not in self._cache:\n"
           "            self._cache[pedido_id] = self._cliente.buscar(pedido_id)\n"
           "        return self._cache[pedido_id]\n",
           "        return self._cliente.buscar(pedido_id)\n",
           "a memória de pedido sumiu: cada cotação bate de novo no serviço vizinho"),

    "M4": ("interacao", "app/cotador.py",
           '        identificador = (pedido_id or "").strip().upper()\n'
           "        if not FORMATO_PEDIDO.match(identificador):\n"
           "            raise PedidoInvalido(\n"
           '                "identificador fora do formato PED-0000: %r" % pedido_id)\n'
           "\n"
           "        pedido = self._buscar_pedido(identificador)\n",
           '        identificador = (pedido_id or "").strip().upper()\n'
           "        pedido = self._buscar_pedido(identificador)\n"
           "        if not FORMATO_PEDIDO.match(identificador):\n"
           "            raise PedidoInvalido(\n"
           '                "identificador fora do formato PED-0000: %r" % pedido_id)\n',
           "o fail fast inverteu: o serviço de Pedidos é chamado antes da validação"),

    "M5": ("interacao", "app/cotador.py",
           "        distancia = self._tabela.km(pedido.origem, pedido.destino)\n",
           "        distancia = self._tabela.km(pedido.destino, pedido.origem)\n",
           "a tabela de distâncias passou a ser consultada com origem e destino trocados"),
}

MUTANTES_PORTAL = {
    "M6": ("interacao", "src/componentes/CotacaoFrete.tsx",
           "        modalidade,\n",
           "        modalidade: 'padrao',\n",
           "a modalidade enviada foi cravada em padrao, ignorando a escolha do cliente"),

    "M7": ("interacao", "src/componentes/CotacaoFrete.tsx",
           "        pesoKg: Number(peso),\n",
           "        pesoKg: peso,\n",
           "o peso passou a ser enviado como texto, e não como número"),
}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def ler(caminho):
    """Lê um arquivo relativo à raiz do laboratório.

    Devolve string vazia quando o arquivo não existe, para os critérios
    tratarem isso como "ainda não entregue" em vez de estourar exceção no
    meio do placar.
    """
    p = os.path.join(RAIZ, caminho)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


def normalizar(texto):
    """Tira espaço à direita e uniformiza o fim de linha."""
    return "\n".join(linha.rstrip() for linha in texto.splitlines())


def impressao_digital(texto):
    """SHA-256 do conteúdo normalizado."""
    return hashlib.sha256(normalizar(texto).encode("utf-8")).hexdigest()


def rodar(comando, cwd, tempo_limite=TEMPO_LIMITE_CURTO):
    """Executa um processo e devolve (código, saída combinada).

    Nunca levanta exceção: estouro de tempo devolve o código sentinela 124,
    a mesma convenção do utilitário `timeout` do Unix.
    """
    try:
        p = subprocess.run(comando, cwd=cwd, capture_output=True, text=True,
                           timeout=tempo_limite)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, ("o comando %s não respondeu em %ds"
                     % (" ".join(comando), tempo_limite))
    except OSError as erro:
        return 127, "não foi possível executar %s: %s" % (comando[0], erro)


def ultimas_linhas(texto, n=10):
    """Corta uma saída longa nas últimas linhas úteis."""
    linhas = [l for l in texto.splitlines() if l.strip()]
    if not linhas:
        return "(o comando não imprimiu nada)"
    return "\n".join("      " + l for l in linhas[-n:])


def contar_pytest(saida):
    """Lê `N passed` do pytest. Devolve (quantidade, houve_falha)."""
    falhou = bool(re.search(r"\b(\d+) (failed|error)", saida))
    m = re.search(r"\b(\d+) passed", saida)
    return (int(m.group(1)) if m else None), falhou


def contar_vitest(saida):
    """Lê `Tests  N passed` do vitest. Devolve (quantidade, houve_falha).

    A linha `Tests` é procurada primeiro e de propósito: a saída do vitest
    traz `Test Files  1 passed (1)` **antes** de `Tests  9 passed (9)`, e um
    regex genérico devolveria 1 em vez de 9.
    """
    falhou = bool(re.search(r"\b(\d+) failed", saida))
    m = re.search(r"^\s*Tests\s+(\d+) passed", saida, re.MULTILINE)
    if m is None:
        m = re.search(r"\b(\d+) passed", saida)
    return (int(m.group(1)) if m else None), falhou


# ---------------------------------------------------------------------------
# Execução das suítes
# ---------------------------------------------------------------------------
def pytest_em(diretorio, alvo):
    """Roda o pytest em `diretorio`, sobre `alvo`. Devolve (quantidade, falhou, saida).

    Sem `-q` de propósito. O `pytest.ini` do laboratório já traz `-q` em
    `addopts`, e o pytest entende dois `-q` como "mais quieto ainda": ele
    deixa de imprimir a linha `N passed`, que é justamente a que este
    verificador lê. Defeito encontrado durante a construção do laboratório.
    """
    codigo, saida = rodar([sys.executable, "-m", "pytest",
                           "-p", "no:cacheprovider", alvo],
                          cwd=diretorio, tempo_limite=TEMPO_LIMITE_CURTO)
    if codigo in (124, 127):
        return None, True, saida
    quantidade, falhou = contar_pytest(saida)
    return quantidade, (falhou or codigo != 0), saida


def npm_instalado():
    return os.path.isdir(os.path.join(PORTAL, "node_modules"))


def vitest_em(diretorio, alvo):
    """Roda o vitest em `diretorio`, sobre `alvo`. Devolve (quantidade, falhou, saida)."""
    codigo, saida = rodar(["npx", "vitest", "run", alvo],
                          cwd=diretorio, tempo_limite=TEMPO_LIMITE_TESTES)
    if codigo in (124, 127):
        return None, True, saida
    quantidade, falhou = contar_vitest(saida)
    return quantidade, (falhou or codigo != 0), saida


# ---------------------------------------------------------------------------
# Cópias temporárias para os mutantes
# ---------------------------------------------------------------------------
def copia_do_frete():
    """Copia o serviço de frete inteiro, com os seus testes junto."""
    destino = os.path.join(tempfile.mkdtemp(prefix="lab10-frete-"), "frete")
    shutil.copytree(FRETE, destino,
                    ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    return destino


def copia_do_portal():
    """Copia o portal, ligando `node_modules` por atalho em vez de duplicar.

    Duplicar `node_modules` custaria centenas de megabytes e dezenas de
    segundos por mutante. O atalho simbólico é lido, nunca escrito.
    """
    destino = os.path.join(tempfile.mkdtemp(prefix="lab10-portal-"), "portal")
    shutil.copytree(PORTAL, destino,
                    ignore=shutil.ignore_patterns("node_modules", "dist",
                                                  ".vitest", "coverage"))
    os.symlink(os.path.join(PORTAL, "node_modules"),
               os.path.join(destino, "node_modules"))
    return destino


def aplicar_mutante(diretorio, mutante):
    """Aplica o defeito na cópia. Devolve "" quando deu certo, ou o motivo."""
    _, arquivo, de, para, _ = mutante
    caminho = os.path.join(diretorio, arquivo)
    if not os.path.exists(caminho):
        return "o arquivo %s não existe na cópia" % arquivo
    with open(caminho, encoding="utf-8") as f:
        conteudo = f.read()
    if de not in conteudo:
        return ("não encontrei o trecho a estragar em %s. O arquivo é "
                "congelado e não deveria ter sido editado." % arquivo)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo.replace(de, para, 1))
    return ""


def suite_pega_os_mutantes(alvo_relativo, minimo, nomes, copiar, mutantes, executar):
    """Roda um arquivo de teste limpo e depois contra cada mutante.

    Devolve (passou, detalhe). A ordem das conferências é deliberada:

    1. o arquivo precisa passar no código correto (teste que reprova código
       certo é ruído, não proteção);
    2. o arquivo precisa ter pelo menos `minimo` testes (um `assert False`
       solitário reprovaria todo mutante e não provaria nada);
    3. o arquivo precisa reprovar em cada mutante.
    """
    limpo = copiar()
    try:
        quantidade, falhou, saida = executar(limpo, alvo_relativo)
        if quantidade is None and re.search(
                r"no tests ran|collected 0 items|No test found", saida):
            return False, ("%s ainda não tem teste nenhum. A lacuna está "
                           "aberta." % alvo_relativo)
        if falhou or quantidade is None:
            return False, ("%s não passa nem contra o código correto:\n%s"
                           % (alvo_relativo, ultimas_linhas(saida)))
        if quantidade < minimo:
            return False, ("%s tem %d teste(s) e o enunciado pede no mínimo %d"
                           % (alvo_relativo, quantidade, minimo))
    finally:
        shutil.rmtree(os.path.dirname(limpo), ignore_errors=True)

    sobreviventes = []
    for nome in nomes:
        mutante = mutantes[nome]
        copia = copiar()
        try:
            erro = aplicar_mutante(copia, mutante)
            if erro:
                return False, erro
            _, falhou, _ = executar(copia, alvo_relativo)
            if not falhou:
                sobreviventes.append("%s (%s: %s)"
                                     % (nome, mutante[0], mutante[4]))
        finally:
            shutil.rmtree(os.path.dirname(copia), ignore_errors=True)

    if sobreviventes:
        return False, ("os seus testes continuaram verdes com o código "
                       "estragado. Mutante(s) que sobreviveram: %s"
                       % "; ".join(sobreviventes))

    return True, ("%d teste(s) em %s, e todos os %d mutante(s) foram pegos"
                  % (quantidade, alvo_relativo, len(nomes)))


# ---------------------------------------------------------------------------
# Critério 1: TODO-1, o Stub
# ---------------------------------------------------------------------------
def criterio_1():
    return suite_pega_os_mutantes(
        os.path.join("tests", "test_cotador_stub.py"), MINIMO_STUB,
        ["M1", "M2"], copia_do_frete, MUTANTES_FRETE, pytest_em)


# ---------------------------------------------------------------------------
# Critério 2: TODO-2, o Mock
# ---------------------------------------------------------------------------
def criterio_2():
    return suite_pega_os_mutantes(
        os.path.join("tests", "test_cotador_mock.py"), MINIMO_MOCK,
        ["M3", "M4"], copia_do_frete, MUTANTES_FRETE, pytest_em)


# ---------------------------------------------------------------------------
# Critério 3: TODO-3, o Spy
# ---------------------------------------------------------------------------
def criterio_3():
    return suite_pega_os_mutantes(
        os.path.join("tests", "test_cotador_spy.py"), MINIMO_SPY,
        ["M5"], copia_do_frete, MUTANTES_FRETE, pytest_em)


# ---------------------------------------------------------------------------
# Critério 4: a suíte inteira do frete, verde e sem rede
# ---------------------------------------------------------------------------
def criterio_4():
    conftest = ler(os.path.join("servicos", "frete", "tests", "conftest.py"))
    if not conftest:
        return False, "servicos/frete/tests/conftest.py não existe"
    if impressao_digital(conftest) != HASH_CONFTEST:
        return False, ("servicos/frete/tests/conftest.py foi editado. É ele "
                       "que bloqueia a rede durante os testes: desligar o "
                       "bloqueio para fazer um teste passar troca o problema "
                       "de lugar em vez de resolvê-lo.")

    quantidade, falhou, saida = pytest_em(FRETE, "tests")
    if falhou or quantidade is None:
        return False, "a suíte do frete não está verde:\n%s" % ultimas_linhas(saida)
    if quantidade < MINIMO_TESTES_PYTEST:
        return False, ("a suíte do frete tem %d teste(s) e o laboratório pede "
                       "no mínimo %d" % (quantidade, MINIMO_TESTES_PYTEST))
    return True, "%d testes verdes, com a rede bloqueada pelo conftest" % quantidade


# ---------------------------------------------------------------------------
# Critério 5: TODO-4, a tela de rastreamento
# ---------------------------------------------------------------------------
def criterio_5():
    if not npm_instalado():
        return False, ("as dependências do portal não foram instaladas. "
                       "Rode:\n      cd portal && npm install")
    alvo = os.path.join("src", "componentes", "RastreioPedido.test.tsx")
    quantidade, falhou, saida = vitest_em(PORTAL, alvo)
    if falhou or quantidade is None:
        return False, ("os testes da tela de rastreamento não passaram:\n%s"
                       % ultimas_linhas(saida))
    return True, "%d testes verdes em RastreioPedido.test.tsx" % quantidade


# ---------------------------------------------------------------------------
# Critério 6: TODO-5, o formulário de cotação
# ---------------------------------------------------------------------------
def criterio_6():
    if not npm_instalado():
        return False, ("as dependências do portal não foram instaladas. "
                       "Rode:\n      cd portal && npm install")
    alvo = os.path.join("src", "componentes", "CotacaoFrete.tela.test.tsx")
    quantidade, falhou, saida = vitest_em(PORTAL, alvo)
    if falhou or quantidade is None:
        return False, ("os testes de tela da cotação não passaram:\n%s"
                       % ultimas_linhas(saida))
    return True, "%d testes verdes em CotacaoFrete.tela.test.tsx" % quantidade


# ---------------------------------------------------------------------------
# Critério 7: TODO-6, o teste de chamada que você escreveu
# ---------------------------------------------------------------------------
def criterio_7():
    if not npm_instalado():
        return False, ("as dependências do portal não foram instaladas. "
                       "Rode:\n      cd portal && npm install")
    return suite_pega_os_mutantes(
        os.path.join("src", "componentes", "CotacaoFrete.chamada.test.tsx"),
        MINIMO_CHAMADA, ["M6", "M7"], copia_do_portal, MUTANTES_PORTAL,
        vitest_em)


# ---------------------------------------------------------------------------
# Critério 8: as evidências medidas na sua máquina
# ---------------------------------------------------------------------------
def valor_do_marcador(marcador, texto):
    """Extrai `MARCADOR: valor`, recusando ausência e o esqueleto PREENCHER."""
    m = re.search(r"^%s:\s*(\S.*)$" % re.escape(marcador), texto, re.MULTILINE)
    valor = m.group(1).strip() if m else ""
    if not valor or valor.upper().startswith("PREENCHER"):
        return None
    return valor


def numero_do_marcador(marcador, texto):
    """Extrai um marcador numérico, aceitando vírgula decimal."""
    bruto = valor_do_marcador(marcador, texto)
    if bruto is None:
        return None
    limpo = re.sub(r"[^0-9,.\-]", "", bruto)
    # "9.956,24" escrito à brasileira vira "9956.24"; "9956.24" fica igual.
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


NUMERICOS = [
    ("VALOR_EXPRESSO_PED_1001", VALOR_EXPRESSO_PED_1001, 0.01),
    ("VALOR_PADRAO_PED_1003", VALOR_PADRAO_PED_1003, 0.01),
    ("PRAZO_PADRAO_PED_1003", PRAZO_PADRAO_PED_1003, 0.001),
]

TEXTUAIS = [
    "STATUS_NA_TELA_PED_1001",
    "MENSAGEM_DE_CORS",
    "TEMPO_SUITE_PYTEST_S",
    "USEI_O_RESGATE",
]


def criterio_8():
    evidencias = ler(EVIDENCIAS)
    if not evidencias:
        return False, "docs/EVIDENCIAS.md não existe"

    for marcador, esperado, tolerancia in NUMERICOS:
        obtido = numero_do_marcador(marcador, evidencias)
        if obtido is None:
            return False, "docs/EVIDENCIAS.md: %s não foi preenchido" % marcador
        if abs(obtido - esperado) > tolerancia:
            return False, ("docs/EVIDENCIAS.md: %s vale %s e a plataforma "
                           "devolve %s. Rode de novo e cole o que saiu."
                           % (marcador, obtido, esperado))

    for marcador in TEXTUAIS:
        if valor_do_marcador(marcador, evidencias) is None:
            return False, "docs/EVIDENCIAS.md: %s não foi preenchido" % marcador

    # Os dois contadores são conferidos contra a execução de verdade.
    pytest_declarado = numero_do_marcador("TESTES_PYTEST", evidencias)
    if pytest_declarado is None:
        return False, "docs/EVIDENCIAS.md: TESTES_PYTEST não foi preenchido"
    quantidade, falhou, _ = pytest_em(FRETE, "tests")
    if falhou or quantidade is None:
        return False, ("a suíte do frete precisa estar verde para conferir "
                       "TESTES_PYTEST. Resolva o critério 4 primeiro.")
    if int(pytest_declarado) != quantidade:
        return False, ("docs/EVIDENCIAS.md: TESTES_PYTEST diz %d e a suíte "
                       "tem %d" % (int(pytest_declarado), quantidade))

    vitest_declarado = numero_do_marcador("TESTES_VITEST", evidencias)
    if vitest_declarado is None:
        return False, "docs/EVIDENCIAS.md: TESTES_VITEST não foi preenchido"
    if not npm_instalado():
        return False, ("as dependências do portal não foram instaladas. "
                       "Rode:\n      cd portal && npm install")
    quantidade_vitest, falhou_vitest, saida = vitest_em(PORTAL, "src")
    if falhou_vitest or quantidade_vitest is None:
        return False, ("a suíte do portal precisa estar verde:\n%s"
                       % ultimas_linhas(saida))
    if quantidade_vitest < MINIMO_TESTES_VITEST:
        return False, ("a suíte do portal tem %d teste(s) e o laboratório "
                       "pede no mínimo %d"
                       % (quantidade_vitest, MINIMO_TESTES_VITEST))
    if int(vitest_declarado) != quantidade_vitest:
        return False, ("docs/EVIDENCIAS.md: TESTES_VITEST diz %d e a suíte "
                       "tem %d" % (int(vitest_declarado), quantidade_vitest))

    return True, ("evidências completas: %d testes em PyTest e %d no Vitest, "
                  "com os valores de referência batendo"
                  % (quantidade, quantidade_vitest))


CRITERIOS = [
    (1, "TODO-1: o Stub pega os mutantes de valor", criterio_1),
    (2, "TODO-2: o Mock pega os mutantes de interação", criterio_2),
    (3, "TODO-3: o Spy pega a troca de argumentos na tabela", criterio_3),
    (4, "A suíte do frete verde, com a rede bloqueada", criterio_4),
    (5, "TODO-4: a tela de rastreamento em React", criterio_5),
    (6, "TODO-5: o formulário de cotação em React", criterio_6),
    (7, "TODO-6: o teste que olha para a chamada", criterio_7),
    (8, "Evidências medidas na sua máquina", criterio_8),
]


def main():
    analisador = argparse.ArgumentParser(
        description="Verificador do laboratório da Aula 10 (LogiTech Enterprise).")
    analisador.add_argument("--criterio", type=int,
                            choices=[n for n, _, _ in CRITERIOS],
                            help="roda apenas um critério")
    analisador.add_argument("--lista", action="store_true",
                            help="mostra o que cada critério cobra e sai")
    argumentos = analisador.parse_args()

    if argumentos.lista:
        print("Critérios do laboratório da Aula 10:\n")
        for numero, titulo, _ in CRITERIOS:
            print("  %d. %s" % (numero, titulo))
        print("\nMutantes usados nos critérios 1, 2, 3 e 7:\n")
        for nome, dados in list(MUTANTES_FRETE.items()) + list(MUTANTES_PORTAL.items()):
            print("  %s (%s) %s" % (nome, dados[0], dados[4]))
        return 0

    escolhidos = [c for c in CRITERIOS
                  if argumentos.criterio is None or c[0] == argumentos.criterio]

    print("=" * 72)
    print("Laboratório da Aula 10: testes de unidade e Portal do Cliente")
    print("=" * 72)

    aprovados = 0
    for numero, titulo, funcao in escolhidos:
        print("\n[%d] %s" % (numero, titulo))
        try:
            passou, detalhe = funcao()
        except Exception as erro:  # noqa: BLE001
            passou, detalhe = False, "o critério quebrou: %s: %s" % (
                type(erro).__name__, erro)
        if passou:
            aprovados += 1
            print("    APROVADO   %s" % detalhe)
        else:
            print("    REPROVADO  %s" % detalhe)

    print("\n" + "=" * 72)
    print("Placar: %d de %d critério(s)" % (aprovados, len(escolhidos)))
    print("=" * 72)

    if aprovados == len(escolhidos):
        print("Tudo o que foi pedido passou. Faça o commit e envie o fork.")
        return 0
    print("Ainda falta critério. Rode `python3 verificar.py --criterio N` "
          "para focar em um só.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
