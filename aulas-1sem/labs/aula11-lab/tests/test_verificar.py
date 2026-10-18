"""Testes do próprio verificador do laboratório da Aula 11.

O `verificar.py` é a régua da correção: se ele estiver errado, o laboratório
inteiro está. Estes testes cobrem as funções puras que decidem se uma lacuna
foi preenchida, incluindo a regressão que apareceu na construção deste kit.

Rode com:
    python3 -m pytest tests/
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import verificar  # noqa: E402


# ---------------------------------------------------------------------------
# sem_comentarios
# ---------------------------------------------------------------------------
def test_comentario_de_linha_nao_conta_como_codigo():
    codigo = "// use switchMap aqui\nreturn termos.pipe(mergeMap(x));"
    limpo = verificar.sem_comentarios(codigo)
    assert "switchMap" not in limpo
    assert "mergeMap" in limpo


def test_comentario_de_bloco_nao_conta_como_codigo():
    codigo = "/* combineLatest([a, b]) */\nreturn this.frota$;"
    limpo = verificar.sem_comentarios(codigo)
    assert "combineLatest" not in limpo
    assert "frota$" in limpo


def test_enunciado_da_lacuna_nao_aprova_o_criterio():
    """O esqueleto descreve a resposta em comentário. Não pode valer."""
    esqueleto = (
        "  // TODO-3: encadeie scan(acumularPorPlaca, new Map()) e map(ordenarPorPlaca)\n"
        "  private montarFrota(): Observable<Posicao[]> {\n"
        "    return of([]);\n"
        "  }\n"
    )
    corpo = verificar.corpo_do_metodo(verificar.sem_comentarios(esqueleto), "montarFrota")
    assert "scan(" not in corpo
    assert "of([])" in corpo


# ---------------------------------------------------------------------------
# corpo_do_metodo
# ---------------------------------------------------------------------------
def test_corpo_do_metodo_pega_a_declaracao_e_nao_a_chamada():
    """Regressão: a chamada aparece antes da declaração no arquivo real.

    Na primeira versão o verificador ancorava em `nome(` e acabava lendo o
    objeto de opções do `shareReplay` como se fosse o corpo do método,
    reprovando código correto.
    """
    codigo = (
        "readonly frota$ = this.montarFrota().pipe(\n"
        "  shareReplay({ bufferSize: 1, refCount: true }),\n"
        ");\n"
        "private montarFrota(): Observable<Posicao[]> {\n"
        "  return this.eventos$.pipe(scan(acumular, new Map()), map(ordenar));\n"
        "}\n"
    )
    corpo = verificar.corpo_do_metodo(codigo, "montarFrota")
    assert "scan(" in corpo
    assert "bufferSize" not in corpo


def test_corpo_do_metodo_equilibra_chaves_aninhadas():
    codigo = (
        "private criarFluxoDeEventos(): Observable<Posicao> {\n"
        "  return new Observable((i) => {\n"
        "    const f = this.abrirFonte(url);\n"
        "    return () => f.close();\n"
        "  });\n"
        "}\n"
        "private outro(): void { return; }\n"
    )
    corpo = verificar.corpo_do_metodo(codigo, "criarFluxoDeEventos")
    assert "close()" in corpo
    assert "outro" not in corpo


def test_corpo_do_metodo_devolve_vazio_quando_nao_existe():
    assert verificar.corpo_do_metodo("class X {}", "montarFrota") == ""


# ---------------------------------------------------------------------------
# numero_do_marcador
# ---------------------------------------------------------------------------
def test_marcador_preenchido_vira_numero():
    assert verificar.numero_do_marcador("DEPOIS_CANCELADAS: 3\n", "DEPOIS_CANCELADAS") == 3.0


def test_marcador_aceita_decimal_com_virgula():
    assert verificar.numero_do_marcador("BUNDLE_INICIAL_KB: 161,84\n", "BUNDLE_INICIAL_KB") == 161.84


def test_marcador_vazio_nao_passa():
    assert verificar.numero_do_marcador("DEPOIS_CANCELADAS:\n", "DEPOIS_CANCELADAS") is None


def test_marcador_com_texto_na_linha_nao_passa():
    texto = "DEPOIS_CANCELADAS: umas tres\n"
    assert verificar.numero_do_marcador(texto, "DEPOIS_CANCELADAS") is None


def test_marcador_de_outro_nome_nao_e_confundido():
    texto = "ANTES_CANCELADAS: 0\nDEPOIS_CANCELADAS: 3\n"
    assert verificar.numero_do_marcador(texto, "ANTES_CANCELADAS") == 0.0
    assert verificar.numero_do_marcador(texto, "DEPOIS_CANCELADAS") == 3.0


# ---------------------------------------------------------------------------
# Contrato do próprio verificador
# ---------------------------------------------------------------------------
def test_sao_oito_criterios_numerados_de_um_a_oito():
    numeros = [c[0] for c in verificar.CRITERIOS]
    assert numeros == [1, 2, 3, 4, 5, 6, 7, 8]


def test_todo_marcador_cobrado_existe_no_formulario_de_evidencias():
    caminho = os.path.join(RAIZ, "docs", "EVIDENCIAS.md")
    with open(caminho, encoding="utf-8") as arquivo:
        texto = arquivo.read()
    ausentes = [m for m in verificar.MARCADORES if m not in texto]
    assert ausentes == []


def test_o_formulario_entregue_nao_vem_preenchido():
    """O aluno preenche. Se o kit já vier com número, o critério 8 é grátis."""
    caminho = os.path.join(RAIZ, "docs", "EVIDENCIAS.md")
    with open(caminho, encoding="utf-8") as arquivo:
        texto = arquivo.read()
    preenchidos = [m for m in verificar.MARCADORES
                   if verificar.numero_do_marcador(texto, m) is not None]
    assert preenchidos == []
