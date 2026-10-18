#!/usr/bin/env python3
"""Verificador do laboratório da Aula 06 (Strategy, Adapter e Decorator).

Confere, critério por critério, se as seis lacunas foram de fato preenchidas
e se os dois serviços continuam se comportando como o contrato da ADR-006
manda. Nada aqui confia em "eu fiz": ou o código é importado e executado, ou
a suíte de testes é rodada de verdade, ou o arquivo é lido do disco.

Sem dependências externas: só a biblioteca padrão. O `pytest` e o `vitest`
são chamados como processos, exatamente como você os chamaria à mão.

Uso:
    python3 verificar.py                # roda os oito critérios
    python3 verificar.py --criterio 3   # roda só um critério
    python3 verificar.py --lista        # mostra o que cada critério cobra

Saída: 0 quando todos os critérios pedidos passam, 1 quando algum falha.
"""

import argparse
import hashlib
import importlib
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
FRETE = os.path.join(RAIZ, "servicos", "frete")
NOTIFICACOES = os.path.join(RAIZ, "servicos", "notificacoes")

# Rota de referência do laboratório: SAO -> LDB, 500 km, com 100 kg de carga.
DISTANCIA_REFERENCIA_KM = 500.0
PESO_REFERENCIA_KG = 100.0
VALORES_DE_REFERENCIA = {
    "expresso": (545.00, 1),
    "economico": (265.00, 4),
    "padrao": (380.00, 2),
}
MODALIDADES_ORIGINAIS = set(VALORES_DE_REFERENCIA)

# Piso das suítes. Os números são os da suíte entregue: quem apagar teste
# para "passar mais rápido" reprova o critério 7, e é essa a intenção.
MINIMO_TESTES_PYTEST = 30
MINIMO_TESTES_VITEST = 27

# Impressão digital de `servicos/notificacoes/src/enviadores.ts` como ele foi
# entregue, com espaços à direita e fim de linha normalizados. O critério 6
# reprova se o arquivo mudou: o Decorator existe justamente para não precisar
# tocar no enviador que já está em produção.
HASH_ENVIADORES = "b6da1b7d3470f83e4f4d37781f335becc14291107171420818c28e2706fd0c26"

TEMPO_LIMITE_TESTES = 300   # a primeira execução do vitest compila TypeScript
TEMPO_LIMITE_CURTO = 60


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
    """Tira espaço à direita e uniformiza o fim de linha.

    Sem isso, salvar o arquivo num editor que apara espaços já mudaria a
    impressão digital, e o aluno seria reprovado por algo que não fez.
    """
    return "\n".join(linha.rstrip() for linha in texto.splitlines())


def impressao_digital(texto):
    """SHA-256 do conteúdo normalizado."""
    return hashlib.sha256(normalizar(texto).encode("utf-8")).hexdigest()


def importar_do_frete(modulo):
    """Importa um módulo do serviço de frete sem precisar instalá-lo.

    Devolve (modulo, erro). Nenhum dos módulos importados aqui usa FastAPI
    nem Pydantic de propósito: a regra de negócio do frete é Python puro, e
    é isso que permite este verificador continuar sem dependências.
    """
    if FRETE not in sys.path:
        sys.path.insert(0, FRETE)
    try:
        alvo = importlib.import_module(modulo)
        return importlib.reload(alvo), ""
    except Exception as erro:  # noqa: BLE001  (qualquer erro vira diagnóstico)
        return None, "não foi possível importar %s: %s: %s" % (
            modulo, type(erro).__name__, erro)


def rodar(comando, cwd, tempo_limite=TEMPO_LIMITE_CURTO):
    """Executa um processo e devolve (código, saída combinada).

    Nunca levanta exceção: estouro de tempo devolve o código sentinela 124,
    a mesma convenção do utilitário `timeout` do Unix, para o critério poder
    dizer "demorou demais" em vez de "seu código está errado".
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


def ultimas_linhas(texto, n=12):
    """Corta uma saída longa nas últimas linhas úteis."""
    linhas = [l for l in texto.splitlines() if l.strip()]
    if not linhas:
        return "(o comando não imprimiu nada)"
    return "\n".join("      " + l for l in linhas[-n:])


def valor_do_marcador(marcador, texto):
    """Extrai `MARCADOR: valor` recusando ausência e o esqueleto PREENCHER."""
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
    limpo = re.sub(r"[^0-9,.\-]", "", bruto).replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


def bloco_do_marcador(nome, texto):
    """Extrai o conteúdo entre `NOME_INICIO` e `NOME_FIM`."""
    m = re.search(r"%s_INICIO(.*?)%s_FIM" % (nome, nome), texto, re.DOTALL)
    if not m:
        return ""
    return m.group(1).strip()


def testes_verdes(saida):
    """Lê `N passed` do pytest ou `Tests  N passed` do vitest.

    Devolve (quantidade, houve_falha). Quantidade `None` significa que não
    foi possível reconhecer o formato da saída, e o critério trata isso como
    falha com a saída bruta anexada.

    A linha do vitest é procurada primeiro e de propósito: a saída dele traz
    `Test Files  1 passed (1)` **antes** de `Tests  10 passed (10)`, e um
    regex genérico devolveria 1 em vez de 10.
    """
    falhou = bool(re.search(r"\b(\d+) failed", saida))
    m = re.search(r"^\s*Tests\s+(\d+) passed", saida, re.MULTILINE)
    if m is None:
        m = re.search(r"\b(\d+) passed", saida)
    return (int(m.group(1)) if m else None), falhou


def npm_instalado():
    return os.path.isdir(os.path.join(NOTIFICACOES, "node_modules"))


def rodar_vitest(arquivo):
    """Roda um arquivo de teste do serviço de notificações."""
    if not npm_instalado():
        return None, ("as dependências do serviço de notificações não foram "
                      "instaladas. Rode:\n"
                      "      cd servicos/notificacoes && npm install")
    codigo, saida = rodar(["npx", "vitest", "run", arquivo],
                          cwd=NOTIFICACOES, tempo_limite=TEMPO_LIMITE_TESTES)
    if codigo == 124 or codigo == 127:
        return None, saida
    quantidade, falhou = testes_verdes(saida)
    if codigo != 0 or falhou or quantidade is None:
        return None, "vitest %s não passou:\n%s" % (arquivo, ultimas_linhas(saida))
    return quantidade, ""


# ---------------------------------------------------------------------------
# Critério 1: TODO-1, o protocolo comum das estratégias
# ---------------------------------------------------------------------------
def criterio_1():
    estrategias, erro = importar_do_frete("app.estrategias")
    if erro:
        return False, erro

    protocolo = getattr(estrategias, "EstrategiaFrete", None)
    if protocolo is None:
        return False, "TODO-1: a classe EstrategiaFrete não existe em app/estrategias.py"
    if not hasattr(protocolo, "cotar"):
        return False, ("TODO-1: EstrategiaFrete não declara o método cotar. "
                       "Um Protocol vazio aceita qualquer objeto e não é contrato.")
    if "modalidade" not in getattr(protocolo, "__annotations__", {}):
        return False, ("TODO-1: EstrategiaFrete não declara o atributo "
                       "`modalidade: str`.")
    return True, "EstrategiaFrete declara modalidade e cotar"


# ---------------------------------------------------------------------------
# Critério 2: TODO-2, as três estratégias originais
# ---------------------------------------------------------------------------
def criterio_2():
    estrategias, erro = importar_do_frete("app.estrategias")
    if erro:
        return False, erro

    classes = {
        "expresso": getattr(estrategias, "FreteExpresso", None),
        "economico": getattr(estrategias, "FreteEconomico", None),
        "padrao": getattr(estrategias, "FretePadrao", None),
    }
    faltando = [n for n, c in classes.items() if c is None]
    if faltando:
        return False, "TODO-2: classes ausentes em app/estrategias.py: %s" % (
            ", ".join(sorted(faltando)))

    conferidas = []
    for nome, classe in sorted(classes.items()):
        valor_esperado, prazo_esperado = VALORES_DE_REFERENCIA[nome]
        try:
            cotacao = classe().cotar(DISTANCIA_REFERENCIA_KM, PESO_REFERENCIA_KG)
        except NotImplementedError:
            return False, ("TODO-2: %s.cotar ainda levanta NotImplementedError"
                           % classe.__name__)
        except Exception as e:  # noqa: BLE001
            return False, "TODO-2: %s.cotar quebrou: %s: %s" % (
                classe.__name__, type(e).__name__, e)

        if abs(float(cotacao.valor) - valor_esperado) > 0.01:
            return False, ("TODO-2: %s cobrou %.2f na rota de referência, "
                           "esperado %.2f (confira a tabela de preços na "
                           "docstring de app/estrategias.py)"
                           % (classe.__name__, cotacao.valor, valor_esperado))
        if int(cotacao.prazo_dias) != prazo_esperado:
            return False, ("TODO-2: %s prometeu %d dia(s) na rota de referência, "
                           "esperado %d"
                           % (classe.__name__, cotacao.prazo_dias, prazo_esperado))
        if cotacao.modalidade != nome:
            return False, ("TODO-2: %s devolveu modalidade %r, esperado %r"
                           % (classe.__name__, cotacao.modalidade, nome))
        conferidas.append("%s %.2f/%dd" % (nome, cotacao.valor, cotacao.prazo_dias))

    return True, "as três estratégias batem na rota de referência: %s" % (
        ", ".join(conferidas))


# ---------------------------------------------------------------------------
# Critério 3: TODO-3, o registro e uma rota que não conhece modalidade
# ---------------------------------------------------------------------------
def _rota_limpa():
    """Confere que app/main.py não decide nada por nome de modalidade.

    Devolve (limpa, motivo). É a checagem que dá sentido ao Open/Closed:
    enquanto a rota citar `expresso`, acrescentar modalidade continua sendo
    editar a rota.
    """
    fonte = ler("servicos/frete/app/main.py")
    if not fonte:
        return False, "servicos/frete/app/main.py não foi encontrado"

    citadas = sorted(n for n in MODALIDADES_ORIGINAIS
                     if re.search(r"['\"]%s['\"]" % n, fonte))
    if citadas:
        return False, ("TODO-3: app/main.py ainda cita modalidade pelo nome "
                       "(%s). A rota precisa perguntar ao registro."
                       % ", ".join(citadas))
    if re.search(r"modalidade\s*==", fonte):
        return False, ("TODO-3: app/main.py ainda compara `modalidade ==`. "
                       "A cadeia de if precisa sair da rota.")
    return True, ""


def criterio_3():
    registro, erro = importar_do_frete("app.registro")
    if erro:
        return False, erro

    registradas = set(getattr(registro, "REGISTRO", {}))
    faltando = MODALIDADES_ORIGINAIS - registradas
    if faltando:
        return False, ("TODO-3: modalidades ausentes no registro: %s "
                       "(registradas: %s)"
                       % (", ".join(sorted(faltando)),
                          ", ".join(sorted(registradas)) or "nenhuma"))

    limpa, motivo = _rota_limpa()
    if not limpa:
        return False, motivo

    return True, ("registro com %d modalidade(s) e rota sem nome de modalidade"
                  % len(registradas))


# ---------------------------------------------------------------------------
# Critério 4: TODO-4, o Adapter do rastreamento da parceira
# ---------------------------------------------------------------------------
def criterio_4():
    quantidade, erro = rodar_vitest("tests/adaptador.test.ts")
    if erro:
        return False, erro
    return True, "TODO-4: %d testes do Adapter passaram" % quantidade


# ---------------------------------------------------------------------------
# Critério 5: TODO-5, o Decorator de log
# ---------------------------------------------------------------------------
def criterio_5():
    quantidade, erro = rodar_vitest("tests/decoradores.test.ts")
    if erro:
        return False, erro
    return True, "TODO-5: %d testes do ComLog passaram" % quantidade


# ---------------------------------------------------------------------------
# Critério 6: TODO-6, retentativa empilhada, sem tocar no enviador
# ---------------------------------------------------------------------------
def criterio_6():
    fonte = ler("servicos/notificacoes/src/enviadores.ts")
    if not fonte:
        return False, "servicos/notificacoes/src/enviadores.ts não foi encontrado"

    if HASH_ENVIADORES != "PREENCHIDO_NA_PUBLICACAO":
        atual = impressao_digital(fonte)
        if atual != HASH_ENVIADORES:
            return False, ("TODO-6: src/enviadores.ts foi alterado. O Decorator "
                           "existe justamente para não precisar disso.\n"
                           "      Restaure com: git checkout -- "
                           "servicos/notificacoes/src/enviadores.ts")

    quantidade, erro = rodar_vitest("tests/empilhamento.test.ts")
    if erro:
        return False, erro
    return True, ("TODO-6: %d testes de empilhamento passaram, com "
                  "enviadores.ts intacto" % quantidade)


# ---------------------------------------------------------------------------
# Critério 7: as duas suítes completas, verdes
# ---------------------------------------------------------------------------
def criterio_7():
    # Sem `-q` aqui: o `pytest.ini` já traz `-q` em `addopts`, e um segundo
    # `-q` vira `-qq`, que suprime justamente a linha "N passed" que o
    # verificador precisa ler.
    codigo, saida = rodar([sys.executable, "-m", "pytest"],
                          cwd=RAIZ, tempo_limite=TEMPO_LIMITE_TESTES)
    if codigo == 127:
        return False, saida
    if "No module named pytest" in saida:
        return False, ("pytest não está instalado. Rode:\n"
                       "      pip install -r servicos/frete/requirements.txt")
    passaram, falhou = testes_verdes(saida)
    if codigo != 0 or falhou or passaram is None:
        return False, "a suíte pytest não passou:\n%s" % ultimas_linhas(saida)
    if passaram < MINIMO_TESTES_PYTEST:
        return False, ("a suíte pytest tem %d testes, mínimo de %d. Teste "
                       "apagado não é teste que passa." % (passaram, MINIMO_TESTES_PYTEST))

    if not npm_instalado():
        return False, ("as dependências do serviço de notificações não foram "
                       "instaladas. Rode:\n"
                       "      cd servicos/notificacoes && npm install")
    codigo, saida = rodar(["npx", "vitest", "run"], cwd=NOTIFICACOES,
                          tempo_limite=TEMPO_LIMITE_TESTES)
    vitest_passaram, falhou = testes_verdes(saida)
    if codigo != 0 or falhou or vitest_passaram is None:
        return False, "a suíte vitest não passou:\n%s" % ultimas_linhas(saida)
    if vitest_passaram < MINIMO_TESTES_VITEST:
        return False, ("a suíte vitest tem %d testes, mínimo de %d."
                       % (vitest_passaram, MINIMO_TESTES_VITEST))

    return True, "pytest %d testes, vitest %d testes, tudo verde" % (
        passaram, vitest_passaram)


# ---------------------------------------------------------------------------
# Critério 8: modalidade nova sem tocar na rota, e as evidências preenchidas
# ---------------------------------------------------------------------------
def criterio_8():
    evidencias = ler("docs/EVIDENCIAS.md")
    if not evidencias:
        return False, "docs/EVIDENCIAS.md não foi encontrado"

    for marcador, esperado in (("VALOR_EXPRESSO_500KM", 545.00),
                               ("PRAZO_EXPRESSO_500KM", 1),
                               ("VALOR_ECONOMICO_500KM", 265.00),
                               ("PRAZO_ECONOMICO_500KM", 4)):
        registrado = numero_do_marcador(marcador, evidencias)
        if registrado is None:
            return False, "docs/EVIDENCIAS.md: %s não foi preenchido" % marcador
        if abs(registrado - esperado) > 0.01:
            return False, ("docs/EVIDENCIAS.md: %s registrado como %s, e o "
                           "serviço devolve %s na rota de referência"
                           % (marcador, registrado, esperado))

    nova = valor_do_marcador("MODALIDADE_NOVA", evidencias)
    if nova is None:
        return False, "docs/EVIDENCIAS.md: MODALIDADE_NOVA não foi preenchida"
    if nova in MODALIDADES_ORIGINAIS:
        return False, ("docs/EVIDENCIAS.md: %r é uma das modalidades originais. "
                       "A prova do Open/Closed é acrescentar uma que não existia."
                       % nova)

    registro, erro = importar_do_frete("app.registro")
    if erro:
        return False, erro
    if nova not in getattr(registro, "REGISTRO", {}):
        return False, ("a modalidade %r não está no registro. Ela precisa estar "
                       "registrada, não só declarada nas evidências." % nova)

    valor_registrado = numero_do_marcador("VALOR_MODALIDADE_NOVA_500KM", evidencias)
    if valor_registrado is None:
        return False, "docs/EVIDENCIAS.md: VALOR_MODALIDADE_NOVA_500KM não foi preenchido"
    try:
        cotacao = registro.REGISTRO[nova].cotar(DISTANCIA_REFERENCIA_KM,
                                                PESO_REFERENCIA_KG)
    except Exception as e:  # noqa: BLE001
        return False, "a modalidade %r quebrou ao cotar: %s: %s" % (
            nova, type(e).__name__, e)
    if abs(float(cotacao.valor) - valor_registrado) > 0.01:
        return False, ("docs/EVIDENCIAS.md: VALOR_MODALIDADE_NOVA_500KM diz "
                       "%.2f, e a estratégia devolve %.2f"
                       % (valor_registrado, cotacao.valor))

    tocados = valor_do_marcador("ARQUIVOS_TOCADOS_PELA_MODALIDADE_NOVA", evidencias)
    if tocados is None:
        return False, ("docs/EVIDENCIAS.md: ARQUIVOS_TOCADOS_PELA_MODALIDADE_NOVA "
                       "não foi preenchido (saída de `git diff --name-only`)")
    if "main.py" in tocados:
        return False, ("docs/EVIDENCIAS.md: app/main.py aparece entre os arquivos "
                       "tocados. Acrescentar modalidade não pode exigir editar "
                       "a rota: é esse o critério do Open/Closed.")

    limpa, motivo = _rota_limpa()
    if not limpa:
        return False, motivo

    log = bloco_do_marcador("LOG_DA_RETENTATIVA", evidencias)
    if not log or "PREENCHER" in log:
        return False, ("docs/EVIDENCIAS.md: o bloco entre LOG_DA_RETENTATIVA_INICIO "
                       "e LOG_DA_RETENTATIVA_FIM está vazio")
    sequencia = [linha.split()[0] for linha in log.splitlines()
                 if linha.split() and linha.split()[0] in
                 ("tentativa", "falha", "sucesso")]
    if sequencia[:4] != ["tentativa", "falha", "tentativa", "sucesso"]:
        return False, ("docs/EVIDENCIAS.md: o log colado não mostra a sequência "
                       "tentativa, falha, tentativa, sucesso. Encontrado: %s"
                       % (", ".join(sequencia) or "nada reconhecível"))

    return True, ("modalidade nova %r cotando %.2f sem tocar na rota, "
                  "evidências completas" % (nova, cotacao.valor))


CRITERIOS = [
    (1, "TODO-1: EstrategiaFrete como protocolo comum", criterio_1),
    (2, "TODO-2: FreteExpresso, FreteEconomico e FretePadrao", criterio_2),
    (3, "TODO-3: registro de estratégias e rota sem nome de modalidade", criterio_3),
    (4, "TODO-4: AdaptadorRastreioLegado traduzindo a parceira", criterio_4),
    (5, "TODO-5: ComLog como Decorator do enviador", criterio_5),
    (6, "TODO-6: ComRetentativa empilhável, sem tocar no enviador", criterio_6),
    (7, "Pirâmide de testes: pytest e vitest verdes", criterio_7),
    (8, "Modalidade nova sem tocar na rota e evidências preenchidas", criterio_8),
]


def main():
    analisador = argparse.ArgumentParser(
        description="Verificador do laboratório da Aula 06 (LogiTech Enterprise).")
    analisador.add_argument("--criterio", type=int, choices=[n for n, _, _ in CRITERIOS],
                            help="roda apenas um critério")
    analisador.add_argument("--lista", action="store_true",
                            help="mostra o que cada critério cobra e sai")
    argumentos = analisador.parse_args()

    if argumentos.lista:
        print("Critérios do laboratório da Aula 06:\n")
        for numero, titulo, _ in CRITERIOS:
            print("  %d. %s" % (numero, titulo))
        return 0

    escolhidos = [c for c in CRITERIOS
                  if argumentos.criterio is None or c[0] == argumentos.criterio]

    print("=" * 72)
    print("Laboratório da Aula 06: Strategy, Adapter e Decorator")
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
