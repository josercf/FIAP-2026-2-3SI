#!/usr/bin/env python3
"""Verificador do laboratório da Aula 08 (agente, Command Pattern, worktrees).

Confere, critério por critério, se o que você entregou de fato funciona: nada
é aceito por declaração. As lacunas são exercitadas de verdade, contra o
serviço de Pedidos rodando, e a recusa da lacuna TODO-5 é provocada de
propósito para conferir que o comando **não** executou.

Uso:
    python3 verificar.py                # roda os nove critérios
    python3 verificar.py --criterio 5   # roda só o critério 5

Saída: 0 quando tudo que foi pedido passa, 1 quando algum critério falha.

Sem dependências externas: só a biblioteca padrão. O serviço de Pedidos é
subido automaticamente numa porta livre quando não estiver no ar, e derrubado
ao final: rodar o verificador nunca deixa processo para trás.
"""
import argparse
import atexit
import os
import re
import socket
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

from agente import api_pedidos, auditoria  # noqa: E402
from agente import comandos as mod_comandos  # noqa: E402
from agente import esquemas  # noqa: E402

MIN_AUTORIZADAS = 3
MIN_RECUSAS = 1
TIMEOUT_SERVICO = 20
TIMEOUT_TESTES = 300

WORKTREES_ESPERADAS = ("wt-agente-pedidos", "wt-agente-atendimento")

PEDIDO_LEITURA = "PED-1042"
PEDIDO_ESCRITA = "PED-1044"
PEDIDO_RECUSA = "PED-1043"

_processo_servico = None
_auditoria_temporaria = None


# ---------------------------------------------------------------------------
# Infraestrutura
# ---------------------------------------------------------------------------
def ler(caminho):
    """Lê um arquivo relativo à raiz do laboratório. String vazia quando não
    existe, para os critérios tratarem isso como 'ainda não feito'."""
    p = os.path.join(RAIZ, caminho)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


def _valor_preenchido(marcador, texto):
    """Extrai 'MARCADOR: valor' e recusa tanto ausência quanto o texto de
    esqueleto 'PREENCHER', que passaria por um regex de presença simples."""
    m = re.search(r"%s:\s*(\S.*)" % re.escape(marcador), texto)
    valor = m.group(1).strip() if m else ""
    if not valor or valor.upper() == "PREENCHER":
        return None
    return valor


def _porta_livre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _encerrar_servico():
    global _processo_servico
    if _processo_servico is not None:
        _processo_servico.terminate()
        try:
            _processo_servico.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _processo_servico.kill()
        _processo_servico = None


atexit.register(_encerrar_servico)


def _e_o_servico_do_laboratorio():
    """Confirma que quem respondeu na porta é o serviço de Pedidos deste lab.

    Responder `/health` com `{"status":"ok"}` não basta: a porta 8080 é uma
    das mais disputadas de qualquer máquina, e durante a construção deste
    laboratório um serviço homônimo de outra aula respondeu exatamente isso e
    reprovou critérios que estavam corretos. A prova é o pedido semente.
    """
    try:
        return api_pedidos.obter_status(PEDIDO_LEITURA).get(
            "pedidoId") == PEDIDO_LEITURA
    except api_pedidos.ErroDeApi:
        return False


def garantir_servico():
    """Garante um serviço de Pedidos respondendo. Devolve (ok, motivo).

    Se já houver o serviço deste laboratório no ar em `LOGITECH_PEDIDOS_URL`,
    usa esse. Se não, sobe um numa porta livre e aponta o cliente para ele.
    Subir aqui evita reprovar o aluno por ter esquecido o outro terminal, que
    é um erro de operação e não de engenharia.
    """
    global _processo_servico
    if api_pedidos.no_ar() and _e_o_servico_do_laboratorio():
        return True, ""
    if _processo_servico is not None:
        if api_pedidos.no_ar():
            return True, ""
        return False, "o serviço de Pedidos subido pelo verificador parou."

    porta = _porta_livre()
    ambiente = dict(os.environ, LOGITECH_PEDIDOS_PORT=str(porta))
    caminho = os.path.join(RAIZ, "servicos", "pedidos", "app.py")
    if not os.path.exists(caminho):
        return False, ("servicos/pedidos/app.py não existe: o serviço "
                        "congelado foi removido do laboratório.")
    try:
        _processo_servico = subprocess.Popen(
            [sys.executable, caminho], env=ambiente,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as erro:
        return False, "não foi possível subir o serviço de Pedidos: %s" % erro

    api_pedidos.BASE_URL = "http://127.0.0.1:%d" % porta
    limite = time.time() + TIMEOUT_SERVICO
    while time.time() < limite:
        if api_pedidos.no_ar():
            return True, ""
        if _processo_servico.poll() is not None:
            return False, ("o serviço de Pedidos morreu ao subir; rode "
                            "'python3 servicos/pedidos/app.py' à mão para ver "
                            "o erro.")
        time.sleep(0.3)
    return False, ("o serviço de Pedidos não respondeu em %ds na porta %d."
                    % (TIMEOUT_SERVICO, porta))


def _despachante():
    """Despachante com a trilha de auditoria redirecionada para um arquivo
    temporário: o verificador exercita os comandos de verdade, e isso não
    pode poluir a trilha que ele mesmo vai contar no critério 6."""
    global _auditoria_temporaria
    if _auditoria_temporaria is None:
        fd, _auditoria_temporaria = tempfile.mkstemp(
            prefix="auditoria-verificador-", suffix=".md")
        os.close(fd)
        atexit.register(lambda: os.path.exists(_auditoria_temporaria)
                        and os.remove(_auditoria_temporaria))
    return mod_comandos.Despachante(caminho_auditoria=_auditoria_temporaria)


def _com_servico(funcao):
    """Roda um critério que precisa do serviço de Pedidos no ar."""
    ok, motivo = garantir_servico()
    if not ok:
        return False, motivo
    return funcao()


# ---------------------------------------------------------------------------
# Critérios
# ---------------------------------------------------------------------------
def criterio_1():
    """TODO-1 e TODO-2: as duas ferramentas declaradas com JSON Schema."""
    esperado = {
        "consultar_status_pedido": (
            esquemas.ESQUEMA_CONSULTAR_STATUS, ["pedido_id"], "TODO-1"),
        "alterar_endereco_entrega": (
            esquemas.ESQUEMA_ALTERAR_ENDERECO,
            ["pedido_id", "logradouro", "numero", "cidade", "uf", "cep"],
            "TODO-2"),
    }

    try:
        declaradas = esquemas.ferramentas()
    except Exception as erro:  # noqa: BLE001
        return False, "esquemas.ferramentas() levantou %s: %s" % (
            type(erro).__name__, erro)

    nomes = {f.get("function", {}).get("name") for f in declaradas}
    faltando = sorted(set(esperado) - nomes)
    if faltando:
        return False, "ferramenta(s) não declarada(s): %s" % ", ".join(faltando)

    for nome, (esquema, obrigatorios, lacuna) in esperado.items():
        if not esquema:
            return False, ("o esquema de %s está vazio: a lacuna %s em "
                            "agente/esquemas.py não foi preenchida."
                            % (nome, lacuna))
        if esquema.get("type") != "object":
            return False, "o esquema de %s precisa ter type 'object'." % nome
        propriedades = esquema.get("properties") or {}
        if not propriedades:
            return False, "o esquema de %s não declara properties." % nome
        requeridos = esquema.get("required") or []
        ausentes = [c for c in obrigatorios if c not in requeridos]
        if ausentes:
            return False, ("o esquema de %s não exige %s em 'required'. Sem "
                            "isso a validação deixa passar chamada incompleta."
                            % (nome, ", ".join(ausentes)))
        sem_propriedade = [c for c in requeridos if c not in propriedades]
        if sem_propriedade:
            return False, ("o esquema de %s exige %s em 'required' mas não "
                            "declara essa(s) propriedade(s)."
                            % (nome, ", ".join(sem_propriedade)))
    return True, ""


def criterio_2():
    """O serviço de Pedidos responde no contrato da plataforma."""
    ok, motivo = garantir_servico()
    if not ok:
        return False, motivo
    try:
        corpo = api_pedidos.saude()
    except api_pedidos.ErroDeApi as erro:
        return False, str(erro)
    if corpo.get("status") != "ok":
        return False, ("GET /health respondeu %r; o contrato da plataforma "
                        "exige {\"status\": \"ok\"}." % corpo)
    try:
        status = api_pedidos.obter_status(PEDIDO_LEITURA)
    except api_pedidos.ErroDeApi as erro:
        return False, str(erro)
    if status.get("pedidoId") != PEDIDO_LEITURA:
        return False, ("GET /api/v1/pedidos/%s/status não devolveu o pedido "
                        "esperado." % PEDIDO_LEITURA)
    return True, ""


def _criterio_3():
    comando = mod_comandos.ConsultarStatusPedido()
    resultado = _despachante().despachar(
        comando.nome, {"pedido_id": PEDIDO_LEITURA})
    if resultado.veredito != auditoria.AUTORIZADO:
        return False, ("a consulta de %s foi %s: %s"
                        % (PEDIDO_LEITURA, resultado.veredito, resultado.motivo))
    conteudo = resultado.conteudo or {}
    if conteudo.get("pedidoId") != PEDIDO_LEITURA or not conteudo.get("status"):
        return False, ("ConsultarStatusPedido devolveu %r; esperado o corpo "
                        "de GET /api/v1/pedidos/{id}/status com pedidoId e "
                        "status." % conteudo)
    return True, ""


def criterio_3():
    """TODO-3: ConsultarStatusPedido executa de verdade contra a API."""
    return _com_servico(_criterio_3)


def _criterio_4():
    novo_cep = "04538-133"
    argumentos = {
        "pedido_id": PEDIDO_ESCRITA,
        "logradouro": "Avenida Brigadeiro Faria Lima",
        "numero": "3477",
        "complemento": "14o andar",
        "cidade": "São Paulo",
        "uf": "SP",
        "cep": novo_cep,
    }
    resultado = _despachante().despachar("alterar_endereco_entrega", argumentos)
    if resultado.veredito != auditoria.AUTORIZADO:
        return False, ("a alteração de endereço de %s foi %s: %s"
                        % (PEDIDO_ESCRITA, resultado.veredito, resultado.motivo))
    try:
        pedido = api_pedidos.obter_pedido(PEDIDO_ESCRITA)
    except api_pedidos.ErroDeApi as erro:
        return False, str(erro)
    gravado = (pedido.get("enderecoEntrega") or {}).get("cep")
    if gravado != novo_cep:
        return False, ("o PATCH não chegou ao serviço: o CEP de %s continua "
                        "%r em vez de %r." % (PEDIDO_ESCRITA, gravado, novo_cep))
    contagem = auditoria.contar(_auditoria_temporaria)
    if contagem[auditoria.AUTORIZADO] < 1:
        return False, ("a execução autorizada não foi registrada na trilha de "
                        "auditoria.")
    return True, ""


def criterio_4():
    """TODO-4: AlterarEnderecoEntrega altera de verdade, validando antes."""
    return _com_servico(_criterio_4)


def _criterio_5():
    # O despachante é construído ANTES de qualquer contagem: é ele quem cria a
    # trilha temporária. Ler a contagem antes disso faria `auditoria.contar`
    # cair no caminho padrão e contar a trilha real do aluno, comparando dois
    # arquivos diferentes e reprovando uma implementação correta.
    despachante = _despachante()

    try:
        antes = api_pedidos.obter_pedido(PEDIDO_RECUSA)
    except api_pedidos.ErroDeApi as erro:
        return False, str(erro)
    cep_antes = (antes.get("enderecoEntrega") or {}).get("cep")

    argumentos = {
        "pedido_id": PEDIDO_RECUSA,
        "logradouro": "Rua Bela Cintra",
        "numero": "495",
        "cidade": "São Paulo",
        "uf": "SP",
        # sem 'cep' de propósito: é a provocação da lacuna TODO-5
    }
    antes_da_recusa = auditoria.contar(_auditoria_temporaria)
    try:
        resultado = despachante.despachar("alterar_endereco_entrega", argumentos)
    except NotImplementedError as erro:
        return False, ("a recusa auditada ainda não foi implementada (%s). "
                        "Preencha a lacuna TODO-5 em agente/comandos.py." % erro)

    if resultado.veredito != auditoria.RECUSADO:
        return False, ("uma alteração de endereço SEM CEP recebeu veredito %s. "
                        "O esperado é RECUSADO, antes de qualquer chamada ao "
                        "serviço." % resultado.veredito)
    if "cep" not in (resultado.motivo or "").lower():
        return False, ("a recusa foi registrada com o motivo %r, que não "
                        "menciona o campo que faltou. O motivo precisa dizer "
                        "ao atendente o que pedir ao cliente."
                        % resultado.motivo)

    depois_da_recusa = auditoria.contar(_auditoria_temporaria)
    if depois_da_recusa[auditoria.RECUSADO] <= antes_da_recusa[auditoria.RECUSADO]:
        return False, ("a recusa não foi registrada na trilha de auditoria: "
                        "recusar em silêncio é tão ruim quanto executar.")

    try:
        depois = api_pedidos.obter_pedido(PEDIDO_RECUSA)
    except api_pedidos.ErroDeApi as erro:
        return False, str(erro)
    cep_depois = (depois.get("enderecoEntrega") or {}).get("cep")
    if cep_depois != cep_antes:
        return False, ("o endereço de %s mudou apesar da recusa: a chamada "
                        "chegou ao serviço." % PEDIDO_RECUSA)
    return True, ""


def criterio_5():
    """TODO-5: alteração sem CEP é recusada, auditada e não executa."""
    return _com_servico(_criterio_5)


def criterio_6():
    """A trilha do aluno tem execuções autorizadas e ao menos uma recusa."""
    caminho = os.path.join(RAIZ, "docs", "AUDITORIA.md")
    if not os.path.exists(caminho):
        return False, ("docs/AUDITORIA.md não existe. Converse com o agente "
                        "(python3 atendente.py ...) para a trilha ser escrita.")
    contagem = auditoria.contar(caminho)
    if contagem[auditoria.AUTORIZADO] < MIN_AUTORIZADAS:
        return False, ("docs/AUDITORIA.md tem %d execução(ões) AUTORIZADO e o "
                        "mínimo é %d." % (contagem[auditoria.AUTORIZADO],
                                          MIN_AUTORIZADAS))
    if contagem[auditoria.RECUSADO] < MIN_RECUSAS:
        return False, ("docs/AUDITORIA.md tem %d recusa(s) e o mínimo é %d. "
                        "Provoque o agente a alterar endereço sem informar o "
                        "CEP." % (contagem[auditoria.RECUSADO], MIN_RECUSAS))
    return True, ""


def _git(*args):
    """Executa um comando git na raiz do laboratório, sem levantar exceção."""
    try:
        p = subprocess.run(["git", "-C", RAIZ, *args], capture_output=True,
                            text=True, timeout=30)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "o comando git não respondeu a tempo."
    except OSError as erro:
        return 1, "", "não foi possível executar o git: %s" % erro


def criterio_7():
    """As duas worktrees do exercício existem e estão ligadas ao repositório."""
    cod, saida, erro = _git("worktree", "list", "--porcelain")
    if cod != 0:
        return False, ("git worktree list falhou: %s"
                        % (erro or "sem detalhe do git"))
    caminhos = [l.split(" ", 1)[1] for l in saida.splitlines()
                if l.startswith("worktree ")]
    nomes = {os.path.basename(c.rstrip("/")) for c in caminhos}
    faltando = [w for w in WORKTREES_ESPERADAS if w not in nomes]
    if faltando:
        return False, ("git worktree list não mostra %s. Crie com: "
                        "git worktree add ../%s <branch>"
                        % (", ".join(faltando), faltando[0]))
    return True, ""


def criterio_8():
    """docs/EVIDENCIAS.md preenchido com o que a aula pede."""
    txt = ler("docs/EVIDENCIAS.md")
    if not txt:
        return False, "docs/EVIDENCIAS.md não existe."
    marcadores = ("PEDIDO_ALTERADO_ID", "CEP_NOVO", "MOTIVO_DA_RECUSA",
                  "EXECUCOES_AUTORIZADAS", "RECUSAS_REGISTRADAS",
                  "MODO_USADO", "USEI_O_RESGATE")
    valores = {m: _valor_preenchido(m, txt) for m in marcadores}
    faltando = sorted(m for m, v in valores.items() if v is None)
    if faltando:
        return False, "sem valor preenchido para: %s" % ", ".join(faltando)

    if not re.match(r"^PED-\d{4}$", valores["PEDIDO_ALTERADO_ID"]):
        return False, ("PEDIDO_ALTERADO_ID precisa ser um identificador real, "
                        "no formato PED-0000.")
    if not re.match(r"^\d{5}-\d{3}$", valores["CEP_NOVO"]):
        return False, "CEP_NOVO precisa estar no formato 00000-000."
    for numerico in ("EXECUCOES_AUTORIZADAS", "RECUSAS_REGISTRADAS"):
        if not valores[numerico].isdigit():
            return False, "%s precisa ser um número inteiro." % numerico
    if int(valores["EXECUCOES_AUTORIZADAS"]) < MIN_AUTORIZADAS:
        return False, ("EXECUCOES_AUTORIZADAS declara %s e o mínimo é %d."
                        % (valores["EXECUCOES_AUTORIZADAS"], MIN_AUTORIZADAS))
    if int(valores["RECUSAS_REGISTRADAS"]) < MIN_RECUSAS:
        return False, ("RECUSAS_REGISTRADAS declara %s e o mínimo é %d."
                        % (valores["RECUSAS_REGISTRADAS"], MIN_RECUSAS))
    if len(valores["MOTIVO_DA_RECUSA"]) < 15:
        return False, ("MOTIVO_DA_RECUSA precisa ser o motivo real que o "
                        "Despachante registrou, não uma palavra solta.")
    if valores["MODO_USADO"].lower() not in ("ollama", "simular", "os dois"):
        return False, ("MODO_USADO precisa ser 'ollama', 'simular' ou "
                        "'os dois'.")
    return True, ""


def criterio_9():
    """A suíte de testes de unidade do laboratório passa."""
    pasta = os.path.join(RAIZ, "tests")
    if not os.path.isdir(pasta):
        return False, "a pasta tests/ não existe no laboratório."
    try:
        p = subprocess.run([sys.executable, "-m", "pytest", pasta, "-q"],
                            cwd=RAIZ, capture_output=True, text=True,
                            timeout=TIMEOUT_TESTES)
    except subprocess.TimeoutExpired:
        return False, "a suíte de testes não terminou em %ds." % TIMEOUT_TESTES
    except OSError as erro:
        return False, "não foi possível rodar o pytest: %s" % erro
    if p.returncode != 0:
        # O pytest ausente reclama em stderr, não em stdout: ler só o stdout
        # devolvia "falhou sem saída" e deixava o aluno sem pista nenhuma.
        saida = (p.stdout or "") + (p.stderr or "")
        if "No module named pytest" in saida:
            return False, ("o pytest não está instalado neste ambiente.\n"
                            "         Instale com: pip install pytest\n"
                            "         No devcontainer do laboratório ele já vem pronto.")
        linhas = [l for l in saida.splitlines() if l.strip()]
        if not linhas:
            return False, ("pytest terminou com código %d sem imprimir nada. "
                            "Rode `python3 -m pytest tests/ -q` à mão para ver o erro."
                            % p.returncode)
        return False, "pytest falhou:\n%s" % "\n".join(linhas[-8:])
    return True, ""


CRITERIOS = [
    (1, "Ferramentas declaradas em JSON Schema (TODO-1, TODO-2)", criterio_1),
    (2, "Serviço de Pedidos respondendo no contrato", criterio_2),
    (3, "ConsultarStatusPedido executa de verdade (TODO-3)", criterio_3),
    (4, "AlterarEnderecoEntrega altera de verdade (TODO-4)", criterio_4),
    (5, "Alteração sem CEP é recusada e auditada (TODO-5)", criterio_5),
    (6, "Trilha docs/AUDITORIA.md com autorizações e recusa", criterio_6),
    (7, "Duas worktrees ligadas ao repositório", criterio_7),
    (8, "docs/EVIDENCIAS.md preenchido", criterio_8),
    (9, "Suíte de testes de unidade verde", criterio_9),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--criterio", type=int, choices=range(1, len(CRITERIOS) + 1),
                    help="valida só o critério indicado, em vez dos nove")
    args = ap.parse_args()
    alvo = [c for c in CRITERIOS if args.criterio is None or c[0] == args.criterio]
    ok = 0
    for num, nome, fn in alvo:
        try:
            passou, motivo = fn()
        except Exception as erro:  # noqa: BLE001
            passou, motivo = False, "%s: %s" % (type(erro).__name__, erro)
        print("  [%s] Critério %d: %s" % ("OK" if passou else "  ", num, nome))
        if passou:
            ok += 1
        else:
            for linha in str(motivo).splitlines():
                print("         %s" % linha)
    print("\n  %d de %d" % (ok, len(alvo)))
    _encerrar_servico()
    return 0 if ok == len(alvo) else 1


if __name__ == "__main__":
    sys.exit(main())
