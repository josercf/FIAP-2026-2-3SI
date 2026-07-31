#!/usr/bin/env python3
"""Verificador do laboratório da Aula 11 (Angular, Observer Pattern e RxJS).

Confere, critério por critério, se as seis lacunas foram de fato preenchidas
e se o painel administrativo continua respeitando o contrato da plataforma
(ADR-006 e ADR-008). Nada aqui confia em "eu fiz": ou o arquivo é lido do
disco, ou a suíte de testes é executada de verdade, ou o serviço é chamado
pela rede.

Sem dependências externas: só a biblioteca padrão. O `ng test` e o `ng build`
são chamados como processos, exatamente como você os chamaria à mão.

Uso:
    python3 verificar.py                # roda os oito critérios
    python3 verificar.py --criterio 6   # roda só um critério
    python3 verificar.py --lista        # mostra o que cada critério cobra

Saída: 0 quando todos os critérios pedidos passam, 1 quando algum falha.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(RAIZ, "painel-admin")

ARQ_APP_CONFIG = "painel-admin/src/app/app.config.ts"
ARQ_FROTA = "painel-admin/src/app/frota/frota.service.ts"
ARQ_FATURAMENTO = "painel-admin/src/app/faturas/faturamento.service.ts"
ARQ_EVIDENCIAS = "docs/EVIDENCIAS.md"

FATURAMENTO_URL = os.environ.get("LOGITECH_FATURAMENTO_URL", "http://localhost:5080")

# Piso da suíte. É o número entregue: quem apagar teste para "passar mais
# rápido" reprova o critério 7, e é essa a intenção.
MINIMO_TESTES = 31

TEMPO_LIMITE_TESTES = 600
TEMPO_LIMITE_BUILD = 600

# Marcadores que docs/EVIDENCIAS.md precisa trazer preenchidos.
MARCADORES = (
    "TESTES_TOTAL",
    "TESTES_VERDES",
    "BUNDLE_INICIAL_KB",
    "PLACAS_NO_PAINEL",
    "PLACAS_APOS_FILTRO_PR",
    "SSE_ASSINANTES_PAINEL_ABERTO",
    "SSE_ASSINANTES_PAINEL_FECHADO",
    "ANTES_RECEBIDAS",
    "ANTES_CONCLUIDAS",
    "ANTES_CANCELADAS",
    "DEPOIS_RECEBIDAS",
    "DEPOIS_CONCLUIDAS",
    "DEPOIS_CANCELADAS",
)


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
    with open(p, encoding="utf-8") as arquivo:
        return arquivo.read()


def sem_comentarios(texto):
    """Tira comentários de linha e de bloco.

    Sem isto, o próprio enunciado da lacuna (que cita `switchMap`,
    `combineLatest` e companhia dentro de comentário) faria o critério passar
    com o código intocado. Já aconteceu em revisão: o verificador precisa
    olhar o que executa, não o que está escrito ao lado.
    """
    sem_bloco = re.sub(r"/\*.*?\*/", " ", texto, flags=re.S)
    return re.sub(r"//[^\n]*", " ", sem_bloco)


def corpo_do_metodo(texto, nome):
    """Devolve o corpo da **declaração** de um método, com chaves equilibradas.

    Procurar só por `nome(` não serve: a primeira ocorrência costuma ser a
    chamada (`this.montarFrota().pipe(...)`), e a primeira chave depois dela é
    a do objeto de opções do operador seguinte. O verificador leria o corpo
    errado e reprovaria código correto, o que aconteceu na construção deste
    kit. A âncora, portanto, é a declaração: o nome não precedido de ponto,
    seguido da lista de parâmetros, do tipo de retorno e da chave de abertura.
    """
    declaracao = re.search(
        r"(?<![.\w])%s\s*\([^)]*\)\s*(?::[^{;=]+)?\{" % re.escape(nome), texto
    )
    if not declaracao:
        return ""
    abre = declaracao.end() - 1
    profundidade = 0
    for posicao in range(abre, len(texto)):
        if texto[posicao] == "{":
            profundidade += 1
        elif texto[posicao] == "}":
            profundidade -= 1
            if profundidade == 0:
                return texto[abre : posicao + 1]
    return texto[abre:]


def node_modules_instalado():
    return os.path.isdir(os.path.join(APP, "node_modules", "@angular", "core"))


_cache_testes = {}


def rodar_suite():
    """Executa `ng test` uma vez e devolve o relatório em JSON.

    O resultado fica em cache no processo: os oito critérios olham a mesma
    execução, e a suíte não roda oito vezes.
    """
    if "relatorio" in _cache_testes:
        return _cache_testes["relatorio"]

    if not node_modules_instalado():
        _cache_testes["relatorio"] = {
            "erro": "as dependências do Angular não estão instaladas. "
                    "Rode `cd painel-admin && npm ci` (ou abra o devcontainer)."
        }
        return _cache_testes["relatorio"]

    saida = os.path.join(tempfile.gettempdir(), "lab11-ng-test.json")
    if os.path.exists(saida):
        os.remove(saida)

    try:
        subprocess.run(
            ["npx", "ng", "test", "--watch=false", "--reporters=json",
             "--output-file=" + saida],
            cwd=APP, capture_output=True, text=True, timeout=TEMPO_LIMITE_TESTES,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as erro:
        _cache_testes["relatorio"] = {"erro": "falha ao executar `ng test`: %s" % erro}
        return _cache_testes["relatorio"]

    if not os.path.exists(saida):
        _cache_testes["relatorio"] = {
            "erro": "o `ng test` não gerou relatório. Rode "
                    "`cd painel-admin && npx ng test --watch=false` para ver o erro."
        }
        return _cache_testes["relatorio"]

    with open(saida, encoding="utf-8") as arquivo:
        relatorio = json.load(arquivo)

    testes = {}
    for arquivo_de_teste in relatorio.get("testResults", []):
        for caso in arquivo_de_teste.get("assertionResults", []):
            nome = " > ".join(list(caso.get("ancestorTitles", [])) + [caso.get("title", "")])
            testes[nome] = caso.get("status")

    _cache_testes["relatorio"] = {
        "erro": None,
        "testes": testes,
        "total": relatorio.get("numTotalTests", 0),
        "verdes": relatorio.get("numPassedTests", 0),
        "vermelhos": relatorio.get("numFailedTests", 0),
    }
    return _cache_testes["relatorio"]


def testes_do_bloco(relatorio, marca):
    """Todos os testes cujo caminho contém a marca do TODO."""
    return {n: s for n, s in relatorio["testes"].items() if marca in n}


def cobrar_bloco(relatorio, marca, minimo):
    """Regra comum dos critérios 1 a 6: o bloco existe e está inteiro verde."""
    if relatorio.get("erro"):
        return False, [relatorio["erro"]]

    bloco = testes_do_bloco(relatorio, marca)
    if len(bloco) < minimo:
        return False, ["esperava ao menos %d testes em '%s', encontrei %d. "
                       "A suíte foi editada?" % (minimo, marca, len(bloco))]

    vermelhos = [n for n, s in bloco.items() if s != "passed"]
    if vermelhos:
        problemas = ["%d de %d testes de '%s' ainda vermelhos:"
                     % (len(vermelhos), len(bloco), marca)]
        problemas += ["    " + n.split(" > ")[-1] for n in vermelhos[:6]]
        return False, problemas

    return True, ["%d testes de '%s' verdes" % (len(bloco), marca)]


def numero_do_marcador(texto, marcador):
    """Lê `MARCADOR: <numero>` de docs/EVIDENCIAS.md."""
    achado = re.search(
        r"^\s*[-*]?\s*`?%s`?\s*[:=]\s*([0-9]+(?:[.,][0-9]+)?)\s*$" % re.escape(marcador),
        texto, re.M,
    )
    if not achado:
        return None
    return float(achado.group(1).replace(",", "."))


def http_json(url, metodo="GET", tempo=8):
    requisicao = urllib.request.Request(url, method=metodo)
    with urllib.request.urlopen(requisicao, timeout=tempo) as resposta:
        return json.load(resposta)


# ---------------------------------------------------------------------------
# Critérios
# ---------------------------------------------------------------------------
def criterio_1():
    """TODO-1: o serviço no injetor raiz e a cadeia HTTP com o interceptador."""
    problemas = []

    faturamento = sem_comentarios(ler(ARQ_FATURAMENTO))
    if not re.search(r"@Injectable\(\s*\{[^}]*providedIn\s*:\s*['\"]root['\"]", faturamento):
        problemas.append("FaturamentoService ainda não declara "
                         "@Injectable({ providedIn: 'root' })")

    config = sem_comentarios(ler(ARQ_APP_CONFIG))
    if "provideHttpClient(" not in config:
        problemas.append("app.config.ts não chama provideHttpClient()")
    if "withInterceptors(" not in config:
        problemas.append("app.config.ts não registra withInterceptors([...])")
    if "interceptadorDeCorrelacao" not in config:
        problemas.append("o interceptadorDeCorrelacao não foi registrado")

    ok, mensagens = cobrar_bloco(rodar_suite(), "TODO-1", 3)
    if not ok:
        problemas += mensagens

    return (not problemas), problemas or ["injeção de dependências no lugar"]


def criterio_2():
    """TODO-2: o Observable escrito à mão sobre o SSE, com teardown."""
    problemas = []
    codigo = sem_comentarios(ler(ARQ_FROTA))
    corpo = corpo_do_metodo(codigo, "criarFluxoDeEventos")

    if "new Observable" not in corpo:
        problemas.append("criarFluxoDeEventos ainda não devolve um new Observable(...)")
    if "abrirFonte(" not in corpo:
        problemas.append("a fonte de eventos não é aberta por this.abrirFonte(...)")
    if "addEventListener(" not in corpo:
        problemas.append("nenhum ouvinte foi inscrito com addEventListener")
    if ".close()" not in corpo:
        problemas.append("falta a função de teardown chamando fonte.close(): "
                         "sem ela cada componente destruído deixa uma conexão SSE viva")
    if "EMPTY" in corpo:
        problemas.append("o EMPTY do esqueleto ainda está no corpo do método")

    ok, mensagens = cobrar_bloco(rodar_suite(), "TODO-2", 5)
    if not ok:
        problemas += mensagens

    return (not problemas), problemas or ["Observable sobre o SSE, com cancelamento"]


def criterio_3():
    """TODO-3: a fotografia da frota com scan e map."""
    problemas = []
    corpo = corpo_do_metodo(sem_comentarios(ler(ARQ_FROTA)), "montarFrota")

    if "scan(" not in corpo:
        problemas.append("montarFrota não usa scan: reduce não serve num fluxo que "
                         "nunca termina")
    if "map(" not in corpo:
        problemas.append("montarFrota não usa map para virar lista")
    if "eventos$" not in corpo:
        problemas.append("montarFrota não parte de this.eventos$")

    ok, mensagens = cobrar_bloco(rodar_suite(), "TODO-3", 3)
    if not ok:
        problemas += mensagens

    return (not problemas), problemas or ["frota acumulada por placa"]


def criterio_4():
    """TODO-4: o fluxo de alertas com filter e map."""
    problemas = []
    corpo = corpo_do_metodo(sem_comentarios(ler(ARQ_FROTA)), "montarAlertas")

    if "filter(" not in corpo:
        problemas.append("montarAlertas não usa filter")
    if "map(" not in corpo:
        problemas.append("montarAlertas não usa map para traduzir Posicao em Alerta")
    if "LIMITE_VELOCIDADE_KMH" not in corpo:
        problemas.append("o limite de velocidade foi cravado no lugar da constante")

    ok, mensagens = cobrar_bloco(rodar_suite(), "TODO-4", 3)
    if not ok:
        problemas += mensagens

    return (not problemas), problemas or ["alertas filtrados e traduzidos"]


def criterio_5():
    """TODO-5: BehaviorSubject e combineLatest."""
    problemas = []
    codigo = sem_comentarios(ler(ARQ_FROTA))

    if not re.search(r"filtroUf\s*=\s*new\s+BehaviorSubject", codigo):
        problemas.append("o filtro de UF ainda não é um BehaviorSubject: com um "
                         "Subject puro o painel abre vazio até o primeiro clique")
    corpo = corpo_do_metodo(codigo, "montarFrotaFiltrada")
    if "combineLatest(" not in corpo:
        problemas.append("montarFrotaFiltrada não cruza os dois fluxos com combineLatest")
    if "filtroUf$" not in corpo:
        problemas.append("montarFrotaFiltrada não combina com this.filtroUf$")

    ok, mensagens = cobrar_bloco(rodar_suite(), "TODO-5", 5)
    if not ok:
        problemas += mensagens

    return (not problemas), problemas or ["filtro de UF cruzando com a frota"]


def criterio_6():
    """TODO-6: a busca em tempo real com debounce, distinct e switchMap."""
    problemas = []
    corpo = corpo_do_metodo(sem_comentarios(ler(ARQ_FATURAMENTO)), "consultar")

    for operador in ("debounceTime(", "distinctUntilChanged(", "switchMap(", "filter("):
        if operador not in corpo:
            problemas.append("consultar não usa %s" % operador.rstrip("("))

    for errado in ("mergeMap(", "concatMap(", "exhaustMap(", "flatMap("):
        if errado in corpo:
            problemas.append("consultar ainda usa %s: só o switchMap cancela a "
                             "inscrição anterior" % errado.rstrip("("))

    ok, mensagens = cobrar_bloco(rodar_suite(), "TODO-6", 8)
    if not ok:
        problemas += mensagens

    return (not problemas), problemas or ["busca em tempo real sem corrida"]


def criterio_7():
    """A suíte inteira verde, e o painel compilando para produção."""
    problemas = []
    relatorio = rodar_suite()

    if relatorio.get("erro"):
        return False, [relatorio["erro"]]

    if relatorio["total"] < MINIMO_TESTES:
        problemas.append("a suíte tem %d testes e o mínimo é %d: algum arquivo de "
                         "teste foi apagado?" % (relatorio["total"], MINIMO_TESTES))
    if relatorio["vermelhos"]:
        problemas.append("%d testes ainda vermelhos de %d"
                         % (relatorio["vermelhos"], relatorio["total"]))

    if not node_modules_instalado():
        problemas.append("dependências ausentes: não dá para rodar `ng build`")
    else:
        try:
            build = subprocess.run(
                ["npx", "ng", "build"], cwd=APP, capture_output=True, text=True,
                timeout=TEMPO_LIMITE_BUILD,
            )
            if build.returncode != 0:
                cauda = (build.stdout + build.stderr).strip().splitlines()[-4:]
                problemas.append("`ng build` falhou: " + " | ".join(cauda))
        except (subprocess.TimeoutExpired, FileNotFoundError) as erro:
            problemas.append("falha ao executar `ng build`: %s" % erro)

    if problemas:
        return False, problemas
    return True, ["%d testes verdes e `ng build` concluído" % relatorio["total"]]


def criterio_8():
    """As evidências medidas, e a prova ao vivo de que o cancelamento existe."""
    problemas = []
    texto = ler(ARQ_EVIDENCIAS)

    if not texto:
        return False, ["docs/EVIDENCIAS.md não existe"]

    valores = {}
    for marcador in MARCADORES:
        valor = numero_do_marcador(texto, marcador)
        if valor is None:
            problemas.append("marcador %s ausente ou não preenchido com número" % marcador)
        else:
            valores[marcador] = valor

    if problemas:
        return False, problemas

    def exigir(condicao, mensagem):
        if not condicao:
            problemas.append(mensagem)

    exigir(valores["TESTES_TOTAL"] >= MINIMO_TESTES,
           "TESTES_TOTAL abaixo de %d" % MINIMO_TESTES)
    exigir(valores["TESTES_VERDES"] == valores["TESTES_TOTAL"],
           "TESTES_VERDES precisa ser igual a TESTES_TOTAL")
    exigir(valores["BUNDLE_INICIAL_KB"] > 0, "BUNDLE_INICIAL_KB precisa ser maior que zero")
    exigir(valores["PLACAS_NO_PAINEL"] >= 1, "PLACAS_NO_PAINEL precisa ser ao menos 1")
    exigir(valores["PLACAS_APOS_FILTRO_PR"] <= valores["PLACAS_NO_PAINEL"],
           "PLACAS_APOS_FILTRO_PR não pode ser maior que PLACAS_NO_PAINEL")
    exigir(valores["SSE_ASSINANTES_PAINEL_ABERTO"] >= 1,
           "com o painel aberto o serviço precisa ver ao menos 1 assinante SSE")
    exigir(valores["SSE_ASSINANTES_PAINEL_FECHADO"] == 0,
           "com o painel fechado o número de assinantes SSE precisa voltar a zero: "
           "se não voltou, falta a função de teardown do TODO-2")

    exigir(valores["ANTES_CANCELADAS"] == 0,
           "no cenário ANTES (mergeMap) nada é cancelado, então ANTES_CANCELADAS é 0")
    exigir(valores["ANTES_RECEBIDAS"] >= 2,
           "o cenário ANTES precisa de ao menos 2 consultas para significar algo")
    exigir(valores["ANTES_RECEBIDAS"] == valores["ANTES_CONCLUIDAS"],
           "no cenário ANTES toda consulta chega ao fim: recebidas e concluídas batem")

    exigir(valores["DEPOIS_CANCELADAS"] >= 1,
           "no cenário DEPOIS (switchMap) ao menos uma consulta precisa ter sido cancelada")
    exigir(valores["DEPOIS_CONCLUIDAS"] >= 1,
           "no cenário DEPOIS a última consulta precisa ter concluído")
    exigir(
        valores["DEPOIS_RECEBIDAS"]
        == valores["DEPOIS_CONCLUIDAS"] + valores["DEPOIS_CANCELADAS"],
        "no cenário DEPOIS recebidas precisa ser concluídas mais canceladas",
    )

    # Prova ao vivo: o verificador aborta uma consulta e confere que o serviço
    # a contabilizou. Sem isto, os números acima seriam só texto digitado.
    try:
        antes = http_json(FATURAMENTO_URL + "/api/v1/metricas")
    except (urllib.error.URLError, OSError, ValueError):
        problemas.append("o serviço de Faturamento não respondeu em %s: suba-o com "
                         "`dotnet run --project servicos/faturamento` antes de rodar "
                         "este critério" % FATURAMENTO_URL)
        return False, problemas

    try:
        urllib.request.urlopen(FATURAMENTO_URL + "/api/v1/faturas/1001", timeout=0.15)
    except Exception:  # noqa: BLE001 - abortar é exatamente o que queremos aqui
        pass
    time.sleep(1.0)

    try:
        depois = http_json(FATURAMENTO_URL + "/api/v1/metricas")
    except (urllib.error.URLError, OSError, ValueError) as erro:
        problemas.append("não consegui reler as métricas do Faturamento: %s" % erro)
        return False, problemas

    if depois["consultasCanceladas"] <= antes["consultasCanceladas"]:
        problemas.append("o serviço de Faturamento não contabilizou o cancelamento da "
                         "sonda: confira se ele está com o atraso deliberado ligado "
                         "(GET /health, campo atrasoMs)")

    if problemas:
        return False, problemas
    return True, ["evidências coerentes e cancelamento confirmado ao vivo no serviço"]


CRITERIOS = (
    (1, "TODO-1: FaturamentoService no injetor raiz e HttpClient com interceptador", criterio_1),
    (2, "TODO-2: Observable sobre o SSE, com função de teardown", criterio_2),
    (3, "TODO-3: fotografia da frota com scan e map", criterio_3),
    (4, "TODO-4: fluxo de alertas com filter e map", criterio_4),
    (5, "TODO-5: filtro de UF com BehaviorSubject e combineLatest", criterio_5),
    (6, "TODO-6: busca em tempo real com debounceTime, distinctUntilChanged e switchMap", criterio_6),
    (7, "A suíte inteira verde (mínimo %d testes) e `ng build` concluído" % MINIMO_TESTES, criterio_7),
    (8, "Evidências medidas em docs/EVIDENCIAS.md e cancelamento provado ao vivo", criterio_8),
)


def main():
    parser = argparse.ArgumentParser(
        description="Verificador do laboratório da Aula 11 (Angular e RxJS)")
    parser.add_argument("--criterio", type=int, help="roda apenas um critério")
    parser.add_argument("--lista", action="store_true", help="lista o que cada critério cobra")
    argumentos = parser.parse_args()

    if argumentos.lista:
        print("Critérios do laboratório da Aula 11\n")
        for numero, titulo, _ in CRITERIOS:
            print("  CA-%02d  %s" % (numero, titulo))
        return 0

    escolhidos = [c for c in CRITERIOS
                  if argumentos.criterio is None or c[0] == argumentos.criterio]
    if not escolhidos:
        print("critério %s não existe. Use --lista." % argumentos.criterio)
        return 1

    print("=== Verificador do laboratório da Aula 11 ===\n")
    aprovados = 0
    for numero, titulo, funcao in escolhidos:
        ok, mensagens = funcao()
        marca = "OK  " if ok else "FALHA"
        print("[%s] CA-%02d  %s" % (marca, numero, titulo))
        for mensagem in mensagens:
            print("        %s" % mensagem)
        print()
        aprovados += 1 if ok else 0

    print("-" * 68)
    print("%d de %d critérios atendidos" % (aprovados, len(escolhidos)))
    return 0 if aprovados == len(escolhidos) else 1


if __name__ == "__main__":
    sys.exit(main())
