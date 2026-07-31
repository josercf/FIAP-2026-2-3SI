#!/usr/bin/env python3
"""Verificador do laboratório da Aula 05 (POO, SOLID e Design Patterns).

Confere os onze critérios de aceitação do laboratório: as seis lacunas
(TODO-1 a TODO-6), as duas suítes de teste, a saúde dos dois serviços, o
caminho ponta a ponta entre Pedidos (Java) e Faturamento (C#) e o formulário
de evidências. Sem dependências externas: só a biblioteca padrão.

Uso:
    python3 verificar.py                 # roda os onze critérios
    python3 verificar.py --criterio 5    # roda só o critério 5
    python3 verificar.py --sem-testes    # pula mvn test e dotnet test

Saída: 0 quando tudo que foi pedido passa, 1 quando algum critério falha.

Variáveis de ambiente reconhecidas:
    LOGITECH_MVN               comando do Maven (padrão: mvn)
    LOGITECH_DOTNET            comando do .NET  (padrão: dotnet)
    LOGITECH_PEDIDOS_URL       padrão: http://localhost:8080
    LOGITECH_FATURAMENTO_URL   padrão: http://localhost:5080

Limite conhecido, documentado no README: parte dos critérios é leitura
estrutural do código-fonte. O verificador confere que a abstração existe, que
a implementação a declara e que a regra de negócio não cita mais o tipo
concreto. Ele não julga se o nome ficou bom nem se a modelagem é a melhor
possível: isso é a correção do professor.
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

MVN = os.environ.get("LOGITECH_MVN", "mvn")
DOTNET = os.environ.get("LOGITECH_DOTNET", "dotnet")
URL_PEDIDOS = os.environ.get("LOGITECH_PEDIDOS_URL", "http://localhost:8080").rstrip("/")
URL_FATURAMENTO = os.environ.get("LOGITECH_FATURAMENTO_URL", "http://localhost:5080").rstrip("/")

TIMEOUT_TESTES = 900     # mvn e dotnet baixam dependência na primeira execução
TIMEOUT_HTTP = 15        # a primeira chamada ao Spring passa pela inicialização do JPA

MINIMO_TESTES_JAVA = 15
MINIMO_TESTES_CSHARP = 10

JAVA = "pedidos/src/main/java/br/com/fiap/logitech/pedidos"
JAVA_TESTE = "pedidos/src/test/java/br/com/fiap/logitech/pedidos"
CSHARP = "faturamento/src/Faturamento.Api"
CSHARP_TESTE = "faturamento/tests/Faturamento.Tests"


# ----------------------------------------------------------------------------
# Utilitários
# ----------------------------------------------------------------------------

def ler(caminho):
    """Lê um arquivo relativo à raiz do laboratório. Devolve string vazia
    quando o arquivo não existe, para os critérios tratarem isso como "ainda
    não feito" em vez de estourar exceção."""
    p = os.path.join(RAIZ, caminho)
    if not os.path.isfile(p):
        return ""
    with open(p, encoding="utf-8") as arquivo:
        return arquivo.read()


def ler_todos(subdiretorio, extensao):
    """Devolve {caminho relativo: conteúdo} de todos os arquivos com aquela
    extensão dentro do subdiretório. Usado quando o aluno escolhe o nome do
    arquivo, como no conector novo do TODO-3."""
    base = os.path.join(RAIZ, subdiretorio)
    encontrados = {}
    for pasta, _, arquivos in os.walk(base):
        # bin/ e obj/ do .NET e target/ do Maven guardam cópias geradas do
        # código: lê-las faria o verificador aprovar um build antigo.
        if any(parte in pasta.split(os.sep) for parte in ("bin", "obj", "target")):
            continue
        for nome in arquivos:
            if nome.endswith(extensao):
                caminho = os.path.join(pasta, nome)
                with open(caminho, encoding="utf-8") as arquivo:
                    encontrados[os.path.relpath(caminho, RAIZ)] = arquivo.read()
    return encontrados


def sem_comentarios_java(texto):
    """Remove comentários de bloco e de linha. Sem isto, o Javadoc do próprio
    esqueleto (que cita JpaPedidoRepository para explicar o problema) faria o
    critério reprovar código já corrigido."""
    texto = re.sub(r"/\*.*?\*/", "", texto, flags=re.S)
    return re.sub(r"//[^\n]*", "", texto)


def sem_comentarios_csharp(texto):
    return sem_comentarios_java(texto)


def executar(comando, diretorio, tempo_limite=TIMEOUT_TESTES):
    """Executa um comando externo e devolve (código, saída combinada).

    Nunca levanta exceção: comando ausente vira código 127 com uma mensagem
    que diz o que instalar, e estouro de tempo vira 124, a mesma convenção do
    utilitário `timeout` do Unix. São diagnósticos diferentes e pedem ações
    diferentes do aluno."""
    try:
        processo = subprocess.run(comando, cwd=os.path.join(RAIZ, diretorio),
                                  capture_output=True, text=True, timeout=tempo_limite)
        return processo.returncode, (processo.stdout or "") + (processo.stderr or "")
    except FileNotFoundError:
        return 127, ("não encontrei o comando '%s'. Rode dentro do devcontainer do "
                     "laboratório, ou aponte para outro executável pela variável de "
                     "ambiente correspondente." % comando[0])
    except subprocess.TimeoutExpired:
        return 124, ("o comando '%s' não terminou em %ds. Isso não significa "
                     "necessariamente que o seu código está errado: pode ser download "
                     "de dependência na primeira execução." % (" ".join(comando), tempo_limite))


def ultimas_linhas(texto, quantidade=8):
    linhas = [l for l in texto.splitlines() if l.strip()]
    if not linhas:
        return "(o comando não devolveu nenhuma saída)"
    return "\n".join(linhas[-quantidade:])


def http_json(url, metodo="GET", corpo=None):
    """Faz uma chamada HTTP e devolve (status, objeto). Status 0 significa que
    o serviço não respondeu, o que é diferente de responder errado."""
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    requisicao = urllib.request.Request(url, data=dados, method=metodo)
    if dados is not None:
        requisicao.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(requisicao, timeout=TIMEOUT_HTTP) as resposta:
            texto = resposta.read().decode("utf-8")
            try:
                return resposta.status, json.loads(texto)
            except json.JSONDecodeError:
                return resposta.status, texto
    except urllib.error.HTTPError as erro:
        try:
            return erro.code, json.loads(erro.read().decode("utf-8"))
        except Exception:
            return erro.code, None
    except Exception as erro:
        return 0, str(erro)


def valor_marcado(marcador, texto):
    """Extrai 'MARCADOR: valor' e recusa o texto de esqueleto PREENCHER, que
    passaria despercebido por um regex de presença simples."""
    achado = re.search(r"%s:\s*(\S.*)" % re.escape(marcador), texto)
    valor = achado.group(1).strip() if achado else ""
    if not valor or valor.upper() == "PREENCHER":
        return None
    return valor


# ----------------------------------------------------------------------------
# Critérios
# ----------------------------------------------------------------------------

def criterio_1():
    """TODO-1, Inversão de Dependência no serviço de Pedidos."""
    interfaces = {c: t for c, t in ler_todos(JAVA, ".java").items()
                  if re.search(r"\binterface\s+PedidoRepository\b", t)}
    if not interfaces:
        return False, ("não encontrei a interface PedidoRepository. Crie-a em "
                       "%s/dominio/PedidoRepository.java com salvar, porId e todos." % JAVA)
    corpo = list(interfaces.values())[0]
    for metodo in ("salvar", "porId", "todos"):
        if metodo not in corpo:
            return False, "a interface PedidoRepository não declara o método %s." % metodo

    jpa = ler("%s/infra/JpaPedidoRepository.java" % JAVA)
    if not re.search(r"class\s+JpaPedidoRepository\s+implements\s+[\w.]*PedidoRepository", jpa):
        return False, ("JpaPedidoRepository precisa declarar "
                       "'implements PedidoRepository'.")

    servico = sem_comentarios_java(ler("%s/aplicacao/PedidoService.java" % JAVA))
    if not servico:
        return False, "PedidoService.java não existe."
    if "JpaPedidoRepository" in servico:
        return False, ("PedidoService ainda cita JpaPedidoRepository. A regra de negócio "
                       "precisa depender da abstração, não da implementação JPA.")
    if re.search(r"import\s+br\.com\.fiap\.logitech\.pedidos\.infra\.", servico):
        return False, ("PedidoService ainda importa do pacote infra. Depois do DIP, "
                       "a camada de negócio não conhece a infraestrutura.")
    if "PedidoRepository" not in servico:
        return False, "PedidoService não usa PedidoRepository."

    teste = sem_comentarios_java(ler("%s/aplicacao/PedidoServiceTest.java" % JAVA_TESTE))
    if "extends JpaPedidoRepository" in teste:
        return False, ("o dublê de teste ainda herda de JpaPedidoRepository. Troque por "
                       "'implements PedidoRepository' e apague o super(null).")
    return True, ""


def criterio_2():
    """TODO-2, Factory Method escolhendo o conector de faturamento."""
    fabrica = ler("%s/faturamento/ConectorFaturamentoFactory.java" % JAVA)
    if not fabrica:
        return False, "ConectorFaturamentoFactory.java não existe."
    limpa = sem_comentarios_java(fabrica)
    if "UnsupportedOperationException" in limpa:
        return False, ("ConectorFaturamentoFactory ainda lança UnsupportedOperationException: "
                       "a fábrica não foi implementada.")
    if not re.search(r"ConectorFaturamentoFactory\s*\(\s*List\s*<\s*ConectorFaturamento\s*>",
                     limpa):
        return False, ("a fábrica precisa receber List<ConectorFaturamento> no construtor. "
                       "É assim que o Spring entrega todos os conectores sem que ninguém "
                       "os registre à mão.")
    if not re.search(r"\bpara\s*\(", limpa):
        return False, "a fábrica precisa expor o método para(String tipoCliente)."

    servico = sem_comentarios_java(ler("%s/aplicacao/PedidoService.java" % JAVA))
    if "ConectorFaturamentoFactory" not in servico:
        return False, "PedidoService não usa a fábrica de conectores."
    if re.search(r"new\s+Conector", servico):
        return False, ("PedidoService ainda instancia conector com 'new'. Quem cria o "
                       "conector agora é a fábrica.")
    if "escolherConector" in servico:
        return False, ("o método escolherConector continua em PedidoService. A decisão "
                       "mudou de lugar: apague o método antigo.")
    return True, ""


def criterio_3():
    """TODO-3, Aberto/Fechado: tipo de cliente novo sem tocar em PedidoService."""
    conectores = {c: t for c, t in ler_todos("%s/faturamento" % JAVA, ".java").items()
                  if re.search(r"implements\s+ConectorFaturamento", t)}
    com_contrato = [c for c, t in conectores.items()
                    if "CONTRATO" in t and "FATURA_MENSAL" in t]
    if not com_contrato:
        return False, ("não encontrei o conector do tipo de cliente CONTRATO. Crie uma "
                       "classe que implemente ConectorFaturamento, atenda o tipo CONTRATO "
                       "e monte a solicitação com meio de pagamento FATURA_MENSAL.")
    corpo = ler(com_contrato[0])
    if "@Component" not in corpo:
        return False, ("%s precisa de @Component para o Spring colocá-lo na lista que a "
                       "fábrica recebe. Sem isso o tipo novo não é registrado." %
                       os.path.basename(com_contrato[0]))
    if not re.search(r"\b30\b", corpo):
        return False, ("o conector do cliente CONTRATO precisa conceder prazo de 30 dias, e "
                       "não encontrei esse valor em %s." % os.path.basename(com_contrato[0]))

    servico = sem_comentarios_java(ler("%s/aplicacao/PedidoService.java" % JAVA))
    for literal in ('"PADRAO"', '"OURO"', '"CONTRATO"'):
        if literal in servico:
            return False, ("PedidoService ainda cita o literal %s. Enquanto a regra de "
                           "negócio conhecer os tipos de cliente pelo nome, cada contrato "
                           "novo obriga a editar esta classe." % literal)
    for classe in ("ConectorBoleto", "ConectorCartaoCorporativo"):
        if classe in servico:
            return False, ("PedidoService ainda cita %s. Ele só deve conhecer a "
                           "abstração ConectorFaturamento." % classe)

    teste = ler("%s/aplicacao/PedidoServiceTest.java" % JAVA_TESTE)
    if "CONTRATO" not in teste:
        return False, ("falta o teste que prova o Aberto/Fechado: um pedido de cliente "
                       "CONTRATO faturado com FATURA_MENSAL, em PedidoServiceTest.")
    return True, ""


def criterio_4():
    """TODO-4, Repository e injeção por construtor no serviço de Faturamento."""
    interfaces = {c: t for c, t in ler_todos(CSHARP, ".cs").items()
                  if re.search(r"\binterface\s+IFaturaRepository\b", t)}
    if not interfaces:
        return False, ("não encontrei a interface IFaturaRepository. Crie-a em "
                       "%s/Dominio/IFaturaRepository.cs." % CSHARP)
    corpo = list(interfaces.values())[0]
    for metodo in ("Salvar", "PorPedido", "Todas"):
        if metodo not in corpo:
            return False, "a interface IFaturaRepository não declara o método %s." % metodo

    repositorio = ler("%s/Infraestrutura/EfFaturaRepository.cs" % CSHARP)
    if not re.search(r"class\s+EfFaturaRepository\s*:\s*IFaturaRepository", repositorio):
        return False, "EfFaturaRepository precisa declarar ': IFaturaRepository'."

    servico = sem_comentarios_csharp(ler("%s/Aplicacao/FaturaService.cs" % CSHARP))
    if not servico:
        return False, "FaturaService.cs não existe."
    if "EfFaturaRepository" in servico:
        return False, ("FaturaService ainda cita EfFaturaRepository. A regra de negócio "
                       "precisa depender de IFaturaRepository.")
    if not re.search(r"FaturaService\s*\(\s*IFaturaRepository", servico):
        return False, "FaturaService precisa receber IFaturaRepository no construtor."

    programa = sem_comentarios_csharp(ler("%s/Program.cs" % CSHARP))
    if not re.search(r"AddScoped\s*<\s*IFaturaRepository\s*,\s*EfFaturaRepository\s*>", programa):
        return False, ("registre a implementação no contêiner de injeção de dependência: "
                       "builder.Services.AddScoped<IFaturaRepository, EfFaturaRepository>();")

    teste = sem_comentarios_csharp(ler("%s/FaturaServiceTests.cs" % CSHARP_TESTE))
    if re.search(r":\s*EfFaturaRepository", teste):
        return False, ("o dublê de teste ainda herda de EfFaturaRepository. Troque por "
                       "': IFaturaRepository' e apague o base(null!).")
    return True, ""


def criterio_5():
    """TODO-5, Singleton thread-safe do numerador de nota fiscal."""
    fonte = ler("%s/Dominio/NumeradorNotaFiscal.cs" % CSHARP)
    if not fonte:
        return False, "NumeradorNotaFiscal.cs não existe."
    limpa = sem_comentarios_csharp(fonte)

    if re.search(r"_instancia\s*\?\?=", limpa):
        return False, ("a criação da instância continua sem sincronização (o '??=' do "
                       "esqueleto). Use Lazy<T> ou um campo static readonly.")
    if not re.search(r"Lazy\s*<|static\s+readonly\s+NumeradorNotaFiscal", limpa):
        return False, ("a instância única precisa ser criada de forma segura entre "
                       "threads: Lazy<NumeradorNotaFiscal> ou campo static readonly.")

    tem_lock = re.search(r"\block\s*\(", limpa) is not None
    tem_interlocked = "Interlocked." in limpa
    if not (tem_lock or tem_interlocked):
        return False, ("o incremento do contador continua sem proteção. Use lock ou "
                       "Interlocked.Increment: ler, somar e gravar em três passos "
                       "separados é o que permite duas threads devolverem o mesmo número.")

    if re.search(r"^\s*int\s+atual\s*=\s*_ultimo\s*;", limpa, re.M) and not tem_lock:
        return False, ("a leitura de _ultimo ficou fora de qualquer região protegida. "
                       "Se optou por Interlocked, o contador não deve mais ser lido e "
                       "gravado em passos separados.")
    if 'NF-' not in fonte:
        return False, "o formato do número (NF-000001) precisa continuar o mesmo."
    return True, ""


def criterio_6():
    """TODO-6, teste xUnit de 100 emissões concorrentes."""
    arquivos = ler_todos(CSHARP_TESTE, ".cs")
    for caminho, texto in arquivos.items():
        limpa = sem_comentarios_csharp(texto)
        tem_concorrencia = ("Task.Run" in limpa or "Parallel.For" in limpa
                            or "Task.WhenAll" in limpa)
        tem_cem = re.search(r"\b100\b", limpa) is not None
        tem_duplicata = "Distinct" in limpa
        if tem_concorrencia and tem_cem and tem_duplicata and "Assert" in limpa:
            return True, ""
    return False, ("não encontrei o teste de concorrência. Ele precisa disparar 100 "
                   "emissões concorrentes (Task.Run com Task.WhenAll, ou Parallel.For), "
                   "contar as repetições com Distinct e exigir zero duplicatas com "
                   "Assert. Procurei em %s." % CSHARP_TESTE)


def criterio_7():
    """A suíte JUnit do serviço de Pedidos passa inteira."""
    codigo, saida = executar([MVN, "-B", "test"], "pedidos")
    if codigo == 127 or codigo == 124:
        return False, saida
    if codigo != 0:
        return False, "mvn test falhou:\n%s" % ultimas_linhas(saida)
    achado = re.findall(r"Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+)", saida)
    if not achado:
        return False, "não consegui ler o resumo do Surefire na saída do Maven."
    total, falhas, erros = (int(x) for x in achado[-1])
    if falhas or erros:
        return False, "mvn test terminou com %d falha(s) e %d erro(s)." % (falhas, erros)
    if total < MINIMO_TESTES_JAVA:
        return False, ("a suíte Java tem %d testes e o laboratório pede pelo menos %d: "
                       "faltam os testes do tipo de cliente CONTRATO (TODO-3)."
                       % (total, MINIMO_TESTES_JAVA))
    return True, ""


def criterio_8():
    """A suíte xUnit do serviço de Faturamento passa inteira."""
    codigo, saida = executar([DOTNET, "test"], "faturamento")
    if codigo == 127 or codigo == 124:
        return False, saida
    achado = re.findall(r"Failed:\s*(\d+),\s*Passed:\s*(\d+)", saida)
    if codigo != 0:
        if achado and int(achado[-1][0]) > 0:
            return False, ("dotnet test terminou com %s teste(s) falhando. Se a falha é "
                           "número de nota duplicado, é a corrida do TODO-5 acontecendo: "
                           "registre a quantidade em NOTAS_DUPLICADAS_ANTES antes de "
                           "corrigir.\n%s" % (achado[-1][0], ultimas_linhas(saida)))
        return False, "dotnet test falhou:\n%s" % ultimas_linhas(saida)
    if not achado:
        return False, "não consegui ler o resumo do xUnit na saída do dotnet test."
    aprovados = int(achado[-1][1])
    if aprovados < MINIMO_TESTES_CSHARP:
        return False, ("a suíte C# tem %d testes verdes e o laboratório pede pelo menos "
                       "%d: falta o teste de concorrência do TODO-6."
                       % (aprovados, MINIMO_TESTES_CSHARP))
    return True, ""


def criterio_9():
    """Os dois serviços respondem em /health, como o contrato da plataforma exige."""
    for nome, url in (("pedidos", URL_PEDIDOS), ("faturamento", URL_FATURAMENTO)):
        status, corpo = http_json(url + "/health")
        if status == 0:
            return False, ("o serviço de %s não respondeu em %s/health. Suba-o antes de "
                           "verificar (detalhe: %s)." % (nome, url, corpo))
        if status != 200:
            return False, "%s/health respondeu HTTP %d, e o contrato pede 200." % (nome, status)
        if not isinstance(corpo, dict) or corpo.get("status") != "ok":
            return False, ('%s/health precisa devolver {"status":"ok"}, e devolveu %s.'
                           % (nome, corpo))
    return True, ""


def criterio_10():
    """Ponta a ponta: um pedido criado em Java vira fatura emitida em C#."""
    novo = {
        "cliente": "Distribuidora Sul",
        "tipoCliente": "CONTRATO",
        "origem": "São Paulo/SP",
        "destino": "Curitiba/PR",
        "enderecoEntrega": "Rua das Araucárias, 480",
        "pesoKg": 120.0,
        "valor": 1000.00,
    }
    status, pedido = http_json(URL_PEDIDOS + "/api/v1/pedidos", "POST", novo)
    if status == 0:
        return False, ("o serviço de pedidos não respondeu em %s (detalhe: %s)."
                       % (URL_PEDIDOS, pedido))
    if status != 201:
        return False, ("POST /api/v1/pedidos respondeu HTTP %d, e o esperado é 201. "
                       "Resposta: %s" % (status, pedido))
    if not isinstance(pedido, dict) or not pedido.get("id"):
        return False, "a resposta do POST não trouxe o id do pedido: %s" % pedido
    if pedido.get("status") != "FATURADO":
        return False, ("o pedido ficou com status %s. Para faturar de verdade, o serviço "
                       "de Faturamento precisa estar no ar e alcançável pela variável "
                       "LOGITECH_FATURAMENTO_URL. Se você acabou de rodar 'dotnet test' "
                       "com o serviço rodando, os binários dele foram reconstruídos por "
                       "baixo do processo: pare e suba o serviço de novo antes de "
                       "verificar." % pedido.get("status"))

    pedido_id = pedido["id"]
    status, fatura = http_json("%s/api/v1/faturas/%s" % (URL_FATURAMENTO, pedido_id))
    if status != 200:
        return False, ("GET /api/v1/faturas/%s respondeu HTTP %d: a fatura do pedido não "
                       "foi encontrada no serviço de Faturamento." % (pedido_id, status))
    if fatura.get("numeroNotaFiscal") != pedido.get("numeroNotaFiscal"):
        return False, ("a nota fiscal do pedido (%s) e a da fatura (%s) não conferem."
                       % (pedido.get("numeroNotaFiscal"), fatura.get("numeroNotaFiscal")))
    if fatura.get("meioPagamento") != "FATURA_MENSAL":
        return False, ("o cliente CONTRATO deveria ser cobrado com FATURA_MENSAL, e a "
                       "fatura veio com %s." % fatura.get("meioPagamento"))
    return True, ""


def criterio_11():
    """docs/EVIDENCIAS.md preenchido, com a corrida provada por número."""
    texto = ler("docs/EVIDENCIAS.md")
    if not texto:
        return False, "docs/EVIDENCIAS.md não existe."

    obrigatorios = ("NOTAS_DUPLICADAS_ANTES", "NOTAS_DUPLICADAS_DEPOIS",
                    "TESTES_JAVA", "TESTES_CSHARP", "PEDIDO_ID", "NUMERO_NOTA_FISCAL")
    valores = {marcador: valor_marcado(marcador, texto) for marcador in obrigatorios}
    faltando = [m for m, v in valores.items() if v is None]
    if faltando:
        return False, "sem valor preenchido para: %s" % ", ".join(faltando)

    try:
        antes = int(valores["NOTAS_DUPLICADAS_ANTES"])
        depois = int(valores["NOTAS_DUPLICADAS_DEPOIS"])
        java = int(valores["TESTES_JAVA"])
        csharp = int(valores["TESTES_CSHARP"])
    except ValueError:
        return False, ("NOTAS_DUPLICADAS_ANTES, NOTAS_DUPLICADAS_DEPOIS, TESTES_JAVA e "
                       "TESTES_CSHARP precisam ser números inteiros.")

    if antes <= 0:
        return False, ("NOTAS_DUPLICADAS_ANTES é %d. O teste do TODO-6 precisa ter falhado "
                       "de verdade antes da correção: rode-o com o Singleton ainda "
                       "quebrado e registre quantas notas vieram repetidas." % antes)
    if depois != 0:
        return False, ("NOTAS_DUPLICADAS_DEPOIS precisa ser 0: com o Singleton "
                       "sincronizado não pode sobrar nenhuma nota duplicada.")
    if java < MINIMO_TESTES_JAVA:
        return False, "TESTES_JAVA declarado como %d, e o mínimo é %d." % (java, MINIMO_TESTES_JAVA)
    if csharp < MINIMO_TESTES_CSHARP:
        return False, ("TESTES_CSHARP declarado como %d, e o mínimo é %d."
                       % (csharp, MINIMO_TESTES_CSHARP))
    if not re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                    valores["PEDIDO_ID"], re.I):
        return False, ("PEDIDO_ID precisa ser o identificador devolvido pelo POST, no "
                       "formato UUID.")
    if not re.match(r"^NF-\d{6}$", valores["NUMERO_NOTA_FISCAL"]):
        return False, "NUMERO_NOTA_FISCAL precisa estar no formato NF-000001."
    return True, ""


# A ordem importa: os critérios que chamam os serviços no ar vêm ANTES dos que
# rodam mvn e dotnet. Rodar as suítes reconstrói os binários por baixo dos
# processos que estão executando, e a chamada ponta a ponta feita depois disso
# falharia por um motivo que não é o do aluno.
CRITERIOS = [
    (1, "TODO-1  Inversão de Dependência em Pedidos (Java)", criterio_1, False),
    (2, "TODO-2  Factory Method dos conectores (Java)", criterio_2, False),
    (3, "TODO-3  Aberto/Fechado com o cliente CONTRATO (Java)", criterio_3, False),
    (4, "TODO-4  Repository e injeção por construtor (C#)", criterio_4, False),
    (5, "TODO-5  Singleton thread-safe do numerador (C#)", criterio_5, False),
    (6, "TODO-6  Teste de 100 emissões concorrentes (C#)", criterio_6, False),
    (7, "GET /health nos dois serviços", criterio_9, False),
    (8, "Ponta a ponta: pedido em Java vira fatura em C#", criterio_10, False),
    (9, "Suíte JUnit do serviço de Pedidos verde", criterio_7, True),
    (10, "Suíte xUnit do serviço de Faturamento verde", criterio_8, True),
    (11, "docs/EVIDENCIAS.md preenchido", criterio_11, False),
]


def main():
    analisador = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    analisador.add_argument("--criterio", type=int, choices=range(1, len(CRITERIOS) + 1),
                            help="valida só o critério indicado, em vez dos onze")
    analisador.add_argument("--sem-testes", action="store_true",
                            help="pula os critérios que rodam mvn test e dotnet test")
    argumentos = analisador.parse_args()

    alvo = [c for c in CRITERIOS
            if argumentos.criterio is None or c[0] == argumentos.criterio]
    if argumentos.sem_testes:
        alvo = [c for c in alvo if not c[3]]

    aprovados = 0
    for numero, nome, funcao, _ in alvo:
        passou, motivo = funcao()
        print("  [%s] CA-%02d  %s" % ("OK" if passou else "  ", numero, nome))
        if passou:
            aprovados += 1
        else:
            for linha in motivo.splitlines():
                print("          %s" % linha)

    print("\n  %d de %d" % (aprovados, len(alvo)))
    return 0 if aprovados == len(alvo) else 1


if __name__ == "__main__":
    sys.exit(main())
