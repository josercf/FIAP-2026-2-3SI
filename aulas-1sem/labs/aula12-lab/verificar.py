#!/usr/bin/env python3
"""Verificador do laboratório da Aula 12 (PostgreSQL: do relacional ao vetorial).

Confere, passo por passo, se o que você escreveu de fato funciona. Nada aqui
confia em "eu fiz": o schema é lido do catálogo do PostgreSQL, as consultas do
Passo 3 são executadas e comparadas com um resultado de referência que o
próprio verificador calcula, a busca do Passo 4 é uma chamada HTTP de verdade
ao serviço `rag`, e a ferramenta do Passo 6 é chamada pelo cliente MCP,
falando stdio com o servidor.

Uso:
    python3 verificar.py                    # roda os sete critérios
    python3 verificar.py --criterio 4       # roda só um
    python3 verificar.py --lista            # mostra o que cada critério cobra

Saída: 0 quando tudo que foi pedido passa, 1 quando algum critério falha.

O que ele NÃO consegue provar por máquina está declarado na tabela "o que a
máquina prova" do README, e é conferido pelo professor na correção.
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

DB_URL = os.environ.get(
    "LOGITECH_DB_URL", "postgresql://logitech:logitech@localhost:5432/logitech"
)
RAG_URL = os.environ.get("LOGITECH_RAG_URL", "http://localhost:8010")

DIMENSAO_ESPERADA = 768
CONTRATOS_ESPERADOS = 4
TRECHOS_MINIMOS = 30
TIMEOUT_HTTP = 8
TIMEOUT_BUSCA = 180
TIMEOUT_MCP = 240

# As quatro perguntas do Critério 5, uma por contrato do acervo. Cada uma traz
# o arquivo esperado e um pedaço do título da cláusula que precisa aparecer
# entre os três primeiros resultados.
#
# Duas propriedades foram exigidas na escolha, e as duas são o que torna o
# critério honesto:
#
# 1. **Nenhuma repete a palavra que está no contrato.** Quem pergunta por
#    "curso especial" recebe a cláusula que fala em "curso MOPP"; quem pergunta
#    por "o custo de esperar parado na doca" recebe a que fala em
#    "sobrestadia"; "época da colheita" encontra "pico de safra" e "caminhões"
#    encontra "veículos". Uma busca por igualdade de texto devolve zero linhas
#    em todas elas.
#
# 2. **Uma por contrato.** Acertar exige distinguir o documento certo entre
#    quatro contratos de transporte que falam do mesmo domínio, e não apenas
#    achar o assunto. Recuperação que traz o assunto certo do contrato errado
#    reprova aqui, que é como deve ser: o prazo de avaria da Frigolar é 120
#    dias e o da Aurora é 90.
#
# As quatro foram medidas na preparação do laboratório e voltam na PRIMEIRA
# posição com o modelo padrão. Exigir top-3 deixa margem para variação de
# versão do modelo sem afrouxar o que está sendo cobrado.
PERGUNTAS_DE_ACEITE = [
    (
        "O motorista precisa de algum curso especial para levar produto inflamável?",
        "petroquimica-litoral.md",
        "Da habilitação e do treinamento",
    ),
    (
        "Quem paga se o equipamento de frio quebrar no meio do caminho?",
        "frigolar-refrigerados.md",
        "Da falha do equipamento",
    ),
    (
        "Quantos caminhões por dia vocês garantem na época da colheita?",
        "nordeste-agro-graneis.md",
        "Da sazonalidade e da capacidade",
    ),
    (
        "Qual o custo de deixar o veículo esperando parado na doca?",
        "aurora-supermercados.md",
        "Das janelas de coleta",
    ),
]

DESCRICOES = {
    1: "Passo 1: você leu a SQL que os ORMs das Aulas 05 e 06 escreveram",
    2: "Passo 2: a DDL à mão criou a extensão, o schema e as duas tabelas",
    3: "Passo 3a: a ingestão vetorizou os contratos",
    4: "Passo 3b: as consultas com JOIN, ORDER BY e LIMIT respondem certo",
    5: "Passo 4: a busca por distância traz o trecho certo",
    6: "Passo 5: o índice HNSW existe e o EXPLAIN foi lido",
    7: "Passo 6: a ferramenta do servidor MCP responde pelo cliente de teste",
}


# ---------------------------------------------------------------------------
# Apoio
# ---------------------------------------------------------------------------


def ler(caminho):
    """Lê um arquivo relativo à raiz do laboratório. Devolve string vazia
    quando não existe, para os critérios tratarem isso como "ainda não feito"
    em vez de estourar exceção."""
    p = os.path.join(RAIZ, caminho)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


def valor_do_marcador(marcador, texto):
    """Extrai o valor de um marcador do tipo 'MARCADOR: valor'.

    Recusa tanto a ausência quanto o texto de esqueleto 'PREENCHER', que
    passaria despercebido por uma checagem de presença simples.
    """
    m = re.search(r"%s:\s*(\S.*)" % re.escape(marcador), texto)
    valor = m.group(1).strip() if m else ""
    if not valor or valor.upper().startswith("PREENCHER"):
        return None
    return valor


def sem_acento(texto):
    """Compara nome de arquivo com texto escrito em português.

    O arquivo é `petroquimica-litoral.md` e o contrato se chama `Petroquímica
    Litoral S.A.`. Comparar os dois sem normalizar reprovaria uma resposta
    correta, que foi o que aconteceu na primeira execução deste verificador.
    """
    import unicodedata

    normalizado = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def consultas_nomeadas(texto):
    """Separa os blocos marcados com `-- consulta: <nome>` em sql/03-consultas.sql.

    Um comando por bloco, terminado em ponto e vírgula. É a convenção declarada
    no cabeçalho daquele arquivo.
    """
    blocos = {}
    partes = re.split(r"^--\s*consulta:\s*(\w+)\s*$", texto, flags=re.M)
    for i in range(1, len(partes), 2):
        nome = partes[i].strip()
        corpo = partes[i + 1]
        # Do início do bloco até o primeiro ponto e vírgula fora de comentário.
        linhas = []
        for linha in corpo.splitlines():
            linhas.append(linha)
            sem_comentario = re.sub(r"--.*$", "", linha)
            if ";" in sem_comentario:
                break
        blocos[nome] = "\n".join(linhas).strip()
    return blocos


def conectar():
    import psycopg  # importado aqui para o --lista funcionar sem o pacote

    return psycopg.connect(DB_URL, connect_timeout=10)


def perguntar_ao_banco(sql, parametros=None):
    with conectar() as conexao, conexao.cursor() as cursor:
        cursor.execute(sql, parametros or ())
        if cursor.description is None:
            return []
        return cursor.fetchall()


def http_post(url, corpo, tempo_limite):
    requisicao = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(requisicao, timeout=tempo_limite) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


class Falha(Exception):
    """Critério reprovado, com o motivo e o conserto na mensagem."""


# ---------------------------------------------------------------------------
# Critério 1: Passo 1, a leitura da SQL que o ORM escreveu
# ---------------------------------------------------------------------------


def criterio_1():
    tabelas = {
        (linha[0], linha[1])
        for linha in perguntar_ao_banco(
            "SELECT schemaname, tablename FROM pg_tables "
            "WHERE schemaname IN ('pedidos','faturamento')"
        )
    }
    faltando = {("pedidos", "pedidos"), ("faturamento", "faturas")} - tabelas
    if faltando:
        raise Falha(
            "não encontrei %s no banco. Elas vêm de servicos/orm-gerado.sql, que o "
            "Compose executa na PRIMEIRA subida de um volume vazio. Se o volume é "
            "antigo, apague e suba de novo: docker compose down -v && docker compose up -d --wait"
            % ", ".join("%s.%s" % t for t in sorted(faltando))
        )

    evidencias = ler("docs/EVIDENCIAS.md")
    for marcador in (
        "SCHEMAS_QUE_O_ORM_CRIOU",
        "TIPO_DA_COLUNA_VALOR",
        "INDICES_QUE_NAO_ESCREVI",
    ):
        if not valor_do_marcador(marcador, evidencias):
            raise Falha(
                "o marcador %s ainda não foi preenchido em docs/EVIDENCIAS.md. "
                "O Passo 1 é leitura, e a evidência dele é o que você anotou." % marcador
            )

    return "2 tabelas de ORM encontradas e 3 marcadores do Passo 1 preenchidos"


# ---------------------------------------------------------------------------
# Critério 2: Passo 2, a DDL à mão
# ---------------------------------------------------------------------------


def criterio_2():
    extensao = perguntar_ao_banco(
        "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
    )
    if not extensao:
        raise Falha(
            "a extensão `vector` não está ativa neste banco. É o TODO-2a: "
            "CREATE EXTENSION IF NOT EXISTS vector. A imagem pgvector/pgvector:pg16 "
            "traz a extensão disponível, e disponível não é instalada."
        )

    tabelas = {
        linha[0]
        for linha in perguntar_ao_banco(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'conhecimento'"
        )
    }
    faltando = {"contratos", "trechos"} - tabelas
    if faltando:
        raise Falha(
            "faltam as tabelas %s no schema conhecimento (TODO-2b e TODO-2c)."
            % ", ".join(sorted(faltando))
        )

    tipo = perguntar_ao_banco(
        """
        SELECT format_type(a.atttypid, a.atttypmod)
        FROM pg_attribute a
        JOIN pg_class c     ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'conhecimento' AND c.relname = 'trechos'
          AND a.attname = 'embedding'
        """
    )
    if not tipo:
        raise Falha("a coluna `embedding` não existe em conhecimento.trechos (TODO-2c).")
    if tipo[0][0] != "vector(%d)" % DIMENSAO_ESPERADA:
        raise Falha(
            "a coluna `embedding` é %s, e o modelo de embedding devolve "
            "vetores de %d dimensões. A dimensão é do modelo, não uma escolha: "
            "com o número errado o INSERT da ingestão falha."
            % (tipo[0][0], DIMENSAO_ESPERADA)
        )

    estrangeira = perguntar_ao_banco(
        """
        SELECT c.confdeltype, ca.attname, cf.relname
        FROM pg_constraint c
        JOIN pg_class      t  ON t.oid = c.conrelid
        JOIN pg_namespace  n  ON n.oid = t.relnamespace
        JOIN pg_class      cf ON cf.oid = c.confrelid
        JOIN pg_attribute  ca ON ca.attrelid = c.conrelid AND ca.attnum = c.conkey[1]
        WHERE c.contype = 'f' AND n.nspname = 'conhecimento' AND t.relname = 'trechos'
        """
    )
    if not estrangeira:
        raise Falha(
            "conhecimento.trechos não tem chave estrangeira (TODO-2c-1). Sem ela, "
            "nada impede um trecho apontar para um contrato que não existe, e a "
            "citação da fonte passa a mentir sem dar erro."
        )
    tipo_delete, coluna, referenciada = estrangeira[0]
    if coluna != "contrato_id" or referenciada != "contratos":
        raise Falha(
            "a chave estrangeira de trechos aponta de `%s` para `%s`, e o esperado "
            "é de `contrato_id` para `contratos`." % (coluna, referenciada)
        )
    if tipo_delete != "c":
        raise Falha(
            "a chave estrangeira existe, mas sem ON DELETE CASCADE. A ingestão "
            "apaga os contratos para reingerir, e sem o cascata isso falha ou "
            "deixa trecho órfão no banco."
        )

    unica = perguntar_ao_banco(
        """
        SELECT COUNT(*)
        FROM pg_constraint c
        JOIN pg_class     t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE c.contype = 'u' AND n.nspname = 'conhecimento'
          AND t.relname = 'trechos' AND array_length(c.conkey, 1) = 2
        """
    )
    if not unica or unica[0][0] == 0:
        raise Falha(
            "falta a restrição única sobre (contrato_id, ordem) em trechos "
            "(TODO-2c-3). Ela é sobre duas colunas juntas: ordem 3 pode existir "
            "em todo contrato, e só uma vez em cada."
        )

    return "extensão vector %s, duas tabelas, FK com CASCADE e coluna vector(%d)" % (
        extensao[0][0],
        DIMENSAO_ESPERADA,
    )


# ---------------------------------------------------------------------------
# Critério 3: Passo 3a, a ingestão
# ---------------------------------------------------------------------------


def criterio_3():
    try:
        contratos = perguntar_ao_banco("SELECT COUNT(*) FROM conhecimento.contratos")[0][0]
    except Exception as erro:  # noqa: BLE001
        if "does not exist" in str(erro):
            raise Falha(
                "as tabelas de conhecimento ainda não existem. O Passo 2 vem antes "
                "deste: rode a sua DDL e volte."
            )
        raise Falha("não consegui contar os contratos: %s" % erro)
    if contratos != CONTRATOS_ESPERADOS:
        raise Falha(
            "há %d linhas em conhecimento.contratos, e a pasta contratos/ tem %d "
            "arquivos. Rode a ingestão: python3 -m rag.ingestao"
            % (contratos, CONTRATOS_ESPERADOS)
        )

    total, vetorizados = perguntar_ao_banco(
        "SELECT COUNT(*), COUNT(embedding) FROM conhecimento.trechos"
    )[0]
    if total < TRECHOS_MINIMOS:
        raise Falha(
            "só há %d trechos em conhecimento.trechos, e o esperado é pelo menos "
            "%d. Rode a ingestão: python3 -m rag.ingestao" % (total, TRECHOS_MINIMOS)
        )
    if vetorizados != total:
        raise Falha(
            "%d dos %d trechos estão com `embedding` nulo. Trecho sem vetor nunca "
            "aparece na busca por distância, e some sem dar erro."
            % (total - vetorizados, total)
        )

    orfaos = perguntar_ao_banco(
        "SELECT COUNT(*) FROM conhecimento.trechos t "
        "LEFT JOIN conhecimento.contratos c ON c.id = t.contrato_id "
        "WHERE c.id IS NULL"
    )[0][0]
    if orfaos:
        raise Falha("há %d trechos apontando para contrato inexistente." % orfaos)

    evidencias = ler("docs/EVIDENCIAS.md")
    for marcador in ("TRECHOS_INGERIDOS", "SEGUNDOS_DE_INGESTAO"):
        if not valor_do_marcador(marcador, evidencias):
            raise Falha(
                "o marcador %s ainda não foi preenchido em docs/EVIDENCIAS.md."
                % marcador
            )

    return "%d contratos, %d trechos, todos vetorizados, nenhum órfão" % (
        contratos,
        total,
    )


# ---------------------------------------------------------------------------
# Critério 4: Passo 3b, as consultas relacionais
# ---------------------------------------------------------------------------


def criterio_4():
    arquivo = ler("sql/03-consultas.sql")
    if not arquivo:
        raise Falha("não encontrei sql/03-consultas.sql.")

    blocos = consultas_nomeadas(arquivo)
    for nome in ("trechos_por_contrato", "origem_do_trecho"):
        if nome not in blocos:
            raise Falha(
                "não achei o bloco `-- consulta: %s` em sql/03-consultas.sql. "
                "O marcador precisa continuar lá: é por ele que o verificador "
                "encontra a sua consulta." % nome
            )
        # A lacuna é procurada dentro do bloco, e não no arquivo inteiro: o
        # texto de apoio fala em `____` e daria falso positivo.
        if "____" in blocos[nome]:
            raise Falha(
                "a consulta `%s` ainda tem lacunas `____` (TODO-3)." % nome
            )

    # --- trechos_por_contrato ---
    referencia = perguntar_ao_banco(
        """
        SELECT c.cliente, COUNT(t.id)
        FROM conhecimento.contratos AS c
        LEFT JOIN conhecimento.trechos AS t ON t.contrato_id = c.id
        GROUP BY c.id, c.cliente
        ORDER BY COUNT(t.id) DESC, c.cliente
        LIMIT 3
        """
    )
    try:
        obtido = perguntar_ao_banco(blocos["trechos_por_contrato"].rstrip(";\n "))
    except Exception as erro:  # noqa: BLE001
        raise Falha("a consulta `trechos_por_contrato` não executou: %s" % erro)

    if len(obtido) != 3:
        raise Falha(
            "a consulta `trechos_por_contrato` devolveu %d linhas, e o pedido eram "
            "as 3 primeiras. Confira o LIMIT (TODO-3a-3)." % len(obtido)
        )
    contagens = [linha[-1] for linha in obtido]
    if contagens != sorted(contagens, reverse=True):
        raise Falha(
            "a consulta `trechos_por_contrato` devolveu %s, fora de ordem "
            "decrescente. Confira o ORDER BY (TODO-3a-2)." % contagens
        )
    if sorted(contagens, reverse=True) != sorted(
        [linha[1] for linha in referencia], reverse=True
    ):
        raise Falha(
            "as contagens de `trechos_por_contrato` são %s e o esperado é %s. "
            "Contagem inflada quase sempre é junção sem condição."
            % (contagens, [linha[1] for linha in referencia])
        )

    # --- origem_do_trecho ---
    esperado = {
        (linha[0], linha[1])
        for linha in perguntar_ao_banco(
            """
            SELECT t.id, c.titulo
            FROM conhecimento.trechos AS t
            JOIN conhecimento.contratos AS c ON c.id = t.contrato_id
            ORDER BY length(t.texto) DESC
            LIMIT 5
            """
        )
    }
    try:
        obtido = perguntar_ao_banco(blocos["origem_do_trecho"].rstrip(";\n "))
    except Exception as erro:  # noqa: BLE001
        raise Falha("a consulta `origem_do_trecho` não executou: %s" % erro)

    if len(obtido) != 5:
        raise Falha(
            "a consulta `origem_do_trecho` devolveu %d linhas, e o pedido eram 5. "
            "Número muito maior que 5 com LIMIT 5 não acontece; número diferente "
            "de 5 costuma ser junção sem condição, que multiplica as linhas antes "
            "do corte." % len(obtido)
        )
    pares = {(linha[0], linha[-1]) for linha in obtido}
    if pares != esperado:
        raise Falha(
            "os pares (id do trecho, título do contrato) de `origem_do_trecho` não "
            "batem com a origem real das linhas. Isso é o sintoma clássico de "
            "junção sem condição: o PostgreSQL aceita, executa e devolve o produto "
            "cartesiano, com todas as linhas plausíveis e quase todas erradas "
            "(TODO-3b-1)."
        )

    return "as duas consultas nomeadas executam e batem com a origem real das linhas"


# ---------------------------------------------------------------------------
# Critério 5: Passo 4, a busca por distância
# ---------------------------------------------------------------------------


def criterio_5():
    # A lacuna do TODO-4 não é procurada no texto do arquivo, e sim no
    # comportamento: `rag/busca.py` levanta NotImplementedError enquanto a
    # consulta tiver `____`, e o serviço traduz isso em 501. Procurar `____` no
    # arquivo daria falso positivo, porque a própria função que detecta a
    # lacuna precisa citar a sequência.
    try:
        with urllib.request.urlopen(RAG_URL + "/health", timeout=TIMEOUT_HTTP) as r:
            saude = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as erro:
        raise Falha(
            "o serviço `rag` não respondeu em %s (%s). Suba com:\n"
            "        uvicorn rag.app:app --host 0.0.0.0 --port 8010" % (RAG_URL, erro)
        )
    if saude.get("extensao_vector") in (None, "ausente"):
        raise Falha(
            "o serviço `rag` está no ar, e informa que a extensão `vector` está "
            "ausente. Volte ao Critério 2."
        )

    acertos = []
    for pergunta, arquivo, marca in PERGUNTAS_DE_ACEITE:
        try:
            resposta = http_post(
                RAG_URL + "/api/v1/busca",
                {"pergunta": pergunta, "k": 3},
                TIMEOUT_BUSCA,
            )
        except urllib.error.HTTPError as erro:
            detalhe = erro.read().decode("utf-8", "replace")[:300]
            if erro.code == 501:
                raise Falha(
                    "o TODO-4 ainda está em aberto: a consulta de busca por "
                    "similaridade em rag/busca.py tem lacunas `____`."
                )
            raise Falha("POST /api/v1/busca respondeu %s: %s" % (erro.code, detalhe))
        except (urllib.error.URLError, TimeoutError, OSError) as erro:
            raise Falha("POST /api/v1/busca falhou: %s" % erro)

        trechos = resposta.get("trechos") or []
        if not trechos:
            raise Falha("a busca não devolveu trecho nenhum para: %s" % pergunta)
        if len(trechos) > 3:
            raise Falha(
                "pedi k=3 e vieram %d trechos. Falta o LIMIT (TODO-4c)." % len(trechos)
            )

        distancias = [t["distancia"] for t in trechos]
        if distancias != sorted(distancias):
            raise Falha(
                "os trechos vieram em %s, fora de ordem crescente de distância. "
                "Distância menor é mais parecido, então a ordenação é ascendente, "
                "que é o padrão do SQL (TODO-4b)." % distancias
            )
        if any(not t.get("contrato") or not t.get("arquivo") for t in trechos):
            raise Falha(
                "algum trecho voltou sem o contrato de origem. É o JOIN do TODO-4a: "
                "sem ele o RAG entrega parágrafo sem procedência."
            )

        certo = any(t["arquivo"] == arquivo and marca in t["texto"] for t in trechos)
        acertos.append((certo, pergunta, arquivo))

    erradas = [(p, a) for certo, p, a in acertos if not certo]
    if erradas:
        linhas = "\n".join(
            "          %s\n            esperava um trecho de %s" % (p, a)
            for p, a in erradas
        )
        raise Falha(
            "%d de %d perguntas não trouxeram o trecho certo entre os 3 primeiros:\n%s"
            % (len(erradas), len(acertos), linhas)
        )

    return "%d de %d perguntas trouxeram o trecho certo entre os 3 primeiros" % (
        len(acertos),
        len(acertos),
    )


# ---------------------------------------------------------------------------
# Critério 6: Passo 5, o índice e o EXPLAIN
# ---------------------------------------------------------------------------


def criterio_6():
    indices = perguntar_ao_banco(
        "SELECT indexname, indexdef FROM pg_indexes "
        "WHERE schemaname = 'conhecimento' AND tablename = 'trechos'"
    )
    vetoriais = [
        (nome, definicao)
        for nome, definicao in indices
        if "hnsw" in definicao.lower() or "ivfflat" in definicao.lower()
    ]
    if not vetoriais:
        encontrados = ", ".join(n for n, _ in indices) or "nenhum"
        raise Falha(
            "não há índice de vetor em conhecimento.trechos (TODO-5). Índices "
            "existentes nessa tabela: %s." % encontrados
        )

    nome, definicao = vetoriais[0]
    if "hnsw" not in definicao.lower():
        raise Falha(
            "o índice `%s` usa ivfflat, e o pedido era hnsw (TODO-5-1)." % nome
        )
    if "vector_cosine_ops" not in definicao:
        raise Falha(
            "o índice `%s` não foi criado com a classe `vector_cosine_ops`, que é a "
            "que serve ao operador `<=>` (TODO-5-2). Índice com a classe errada "
            "nasce, ocupa disco e o planejador o ignora: o plano continua com "
            "Seq Scan mesmo depois de ele existir.\n        Definição atual: %s"
            % (nome, definicao)
        )

    evidencias = ler("docs/EVIDENCIAS.md")
    sem_indice = valor_do_marcador("EXPLAIN_SEM_INDICE", evidencias)
    com_indice = valor_do_marcador("EXPLAIN_COM_INDICE", evidencias)
    if not sem_indice or not com_indice:
        raise Falha(
            "faltam EXPLAIN_SEM_INDICE e EXPLAIN_COM_INDICE em docs/EVIDENCIAS.md. "
            "O índice existir não prova que você leu o plano."
        )
    if "seq scan" not in sem_indice.lower():
        raise Falha(
            "EXPLAIN_SEM_INDICE deveria trazer a linha do `Seq Scan` copiada do "
            "plano, e o que está lá é: %s" % sem_indice[:120]
        )
    if "index scan" not in com_indice.lower():
        raise Falha(
            "EXPLAIN_COM_INDICE deveria trazer a linha do `Index Scan using "
            "trechos_embedding_hnsw`, e o que está lá é: %s" % com_indice[:120]
        )

    return "índice %s com vector_cosine_ops, e os dois planos registrados" % nome


# ---------------------------------------------------------------------------
# Critério 7: Passo 6, a ferramenta MCP
# ---------------------------------------------------------------------------


def criterio_7():
    cliente = os.path.join(RAIZ, "mcp-logitech", "src", "cliente-teste.ts")
    if not os.path.exists(cliente):
        raise Falha("não encontrei mcp-logitech/src/cliente-teste.ts.")

    pergunta = PERGUNTAS_DE_ACEITE[0][0]
    arquivo_esperado = PERGUNTAS_DE_ACEITE[0][1]
    comando = [
        "node",
        "--experimental-strip-types",
        cliente,
        "--json",
        "--pergunta",
        pergunta,
    ]
    try:
        processo = subprocess.run(
            comando, capture_output=True, text=True, timeout=TIMEOUT_MCP, cwd=RAIZ
        )
    except FileNotFoundError:
        raise Falha(
            "não encontrei o `node`. O devcontainer deste laboratório traz o Node 22."
        )
    except subprocess.TimeoutExpired:
        raise Falha(
            "o cliente MCP não respondeu em %ds. O sintoma mais comum é um "
            "`console.log` de depuração no servidor: stdout é o canal do protocolo, "
            "e qualquer coisa escrita lá corrompe o fluxo. Log vai para stderr, com "
            "a função `registrar()`." % TIMEOUT_MCP
        )

    linhas = [l for l in processo.stdout.splitlines() if l.strip().startswith("{")]
    if not linhas:
        raise Falha(
            "o cliente MCP não devolveu JSON.\n        saída: %s\n        erros: %s"
            % (processo.stdout[-400:], processo.stderr[-400:])
        )
    dados = json.loads(linhas[-1])

    if dados.get("servidor") != "mcp-logitech":
        raise Falha(
            "o `initialize` devolveu serverInfo.name = %r, e o esperado era "
            "'mcp-logitech'." % dados.get("servidor")
        )
    if "buscar_em_contratos" not in (dados.get("ferramentas") or []):
        raise Falha(
            "`tools/list` não anunciou a ferramenta `buscar_em_contratos`. É essa "
            "lista que um cliente de IA lê para descobrir o que existe."
        )
    if not dados.get("recursoOk"):
        raise Falha(
            "`resources/read` não devolveu o conteúdo de um contrato. Esse bloco "
            "vem pronto no servidor: confira se a pasta contratos/ está no lugar."
        )
    if dados.get("erro"):
        raise Falha(
            "a ferramenta `buscar_em_contratos` respondeu com isError (TODO-6a).\n"
            "        motivo: %s" % (dados.get("texto") or "(sem texto)")[:300]
        )

    texto = dados.get("texto") or ""
    esperado = sem_acento(arquivo_esperado.replace(".md", "").split("-")[0])
    if esperado not in sem_acento(texto):
        raise Falha(
            "a ferramenta respondeu, e o texto não cita o contrato de onde o trecho "
            "veio. A citação da fonte é o que o JOIN do TODO-4a existe para "
            "permitir.\n        resposta: %s" % texto[:300]
        )

    return "servidor MCP respondeu initialize, tools/list, resources/read e tools/call"


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------

CRITERIOS = {
    1: criterio_1,
    2: criterio_2,
    3: criterio_3,
    4: criterio_4,
    5: criterio_5,
    6: criterio_6,
    7: criterio_7,
}


def diagnostico():
    """Antes de julgar, diz se o banco e o serviço de RAG estão de pé.

    Um critério que falha porque o banco não subiu tem conserto diferente de um
    critério que falha porque falta uma linha na sua SQL, e misturar os dois
    manda você procurar no lugar errado.
    """
    print("Diagnóstico")
    try:
        versao = perguntar_ao_banco("SELECT version()")[0][0].split(",")[0]
        print("  banco   OK    %s" % versao)
    except Exception as erro:  # noqa: BLE001
        print("  banco   FORA  %s" % erro)
        print("          suba com: docker compose up -d --wait")
    try:
        with urllib.request.urlopen(RAG_URL + "/health", timeout=TIMEOUT_HTTP) as r:
            saude = json.loads(r.read().decode("utf-8"))
        print(
            "  rag     OK    extensão vector: %s, modelo: %s"
            % (saude.get("extensao_vector"), saude.get("modelo_embedding"))
        )
    except Exception as erro:  # noqa: BLE001
        print("  rag     FORA  %s" % erro)
        print("          suba com: uvicorn rag.app:app --host 0.0.0.0 --port 8010")
    print()


def main():
    parser = argparse.ArgumentParser(description="Verificador da Aula 12.")
    parser.add_argument("--criterio", type=int, choices=sorted(CRITERIOS))
    parser.add_argument("--lista", action="store_true")
    parser.add_argument("--sem-diagnostico", action="store_true")
    argumentos = parser.parse_args()

    if argumentos.lista:
        for numero, descricao in DESCRICOES.items():
            print("CA-%02d  %s" % (numero, descricao))
        return 0

    numeros = [argumentos.criterio] if argumentos.criterio else sorted(CRITERIOS)

    if not argumentos.sem_diagnostico:
        diagnostico()

    aprovados = 0
    for numero in numeros:
        print("CA-%02d  %s" % (numero, DESCRICOES[numero]))
        try:
            detalhe = CRITERIOS[numero]()
        except Falha as erro:
            print("       REPROVADO: %s\n" % erro)
        except Exception as erro:  # noqa: BLE001
            print("       REPROVADO: erro inesperado: %s\n" % erro)
        else:
            aprovados += 1
            print("       APROVADO: %s\n" % detalhe)

    print("=" * 72)
    print("%d de %d critérios aprovados." % (aprovados, len(numeros)))
    return 0 if aprovados == len(numeros) else 1


if __name__ == "__main__":
    sys.exit(main())
