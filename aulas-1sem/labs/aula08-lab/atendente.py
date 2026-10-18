#!/usr/bin/env python3
"""Atendente virtual da LogiTech Enterprise: ponto de entrada do agente.

PRONTO: não é tarefa. As lacunas estão em `agente/esquemas.py` e
`agente/comandos.py`.

Uso:

    # com o modelo local do devcontainer (Ollama)
    python3 atendente.py "Onde está o pedido PED-1042?"

    # com resposta de modelo já formada, sem depender do acerto do modelo
    python3 atendente.py --simular "Onde está o pedido PED-1042?"
    python3 atendente.py --simular --roteiro recusa "Mudar o endereço do PED-1043"

    # conversa interativa
    python3 atendente.py --interativo

Antes de qualquer coisa, suba o serviço de Pedidos em outro terminal:

    python3 servicos/pedidos/app.py
"""
import argparse
import sys

from agente import api_pedidos, esquemas, laco, llm
from agente.comandos import Despachante


def _narrar(linha):
    print(linha, file=sys.stderr)


def _avisar_lacunas():
    """Diz de cara qual lacuna ainda está aberta, em vez de deixar o aluno
    descobrir por uma recusa genérica no meio da conversa."""
    pendentes = []
    if not esquemas.ESQUEMA_CONSULTAR_STATUS:
        pendentes.append("TODO-1 (esquema de consultar_status_pedido)")
    if not esquemas.ESQUEMA_ALTERAR_ENDERECO:
        pendentes.append("TODO-2 (esquema de alterar_endereco_entrega)")
    if pendentes:
        print("[aviso] lacunas ainda abertas em agente/esquemas.py: %s"
              % "; ".join(pendentes), file=sys.stderr)
        print("[aviso] enquanto o esquema estiver vazio, toda chamada é "
              "recusada pela validação, e isso está correto: sem contrato, "
              "nada executa.", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(
        description="Agente de atendimento da LogiTech (Aula 08).")
    ap.add_argument("pergunta", nargs="*",
                    help="a mensagem do cliente para o atendente virtual")
    ap.add_argument("--simular", action="store_true",
                    help="usa respostas de modelo já formadas, sem chamar o "
                         "Ollama; a validação, os comandos e a auditoria "
                         "continuam reais")
    ap.add_argument("--roteiro", choices=sorted(llm.ROTEIROS),
                    help="força um roteiro do modo --simular")
    ap.add_argument("--interativo", action="store_true",
                    help="conversa em várias mensagens; encerre com 'sair'")
    ap.add_argument("--modelo", default=None,
                    help="modelo do Ollama (padrão: %s)" % llm.MODELO)
    args = ap.parse_args()

    if args.roteiro and not args.simular:
        ap.error("--roteiro só faz sentido junto com --simular")

    pergunta = " ".join(args.pergunta).strip()
    if not pergunta and not args.interativo:
        ap.error("informe a pergunta do cliente, ou use --interativo")

    _avisar_lacunas()

    if not api_pedidos.no_ar():
        print("[erro] o serviço de Pedidos não respondeu em %s.\n"
              "       Suba em outro terminal: python3 servicos/pedidos/app.py"
              % api_pedidos.BASE_URL, file=sys.stderr)
        return 1

    if args.simular:
        cliente = llm.ClienteSimulado(roteiro=args.roteiro)
    else:
        cliente = llm.ClienteOllama(modelo=args.modelo)
        if not cliente.no_ar():
            print("[erro] o Ollama não respondeu em %s.\n"
                  "       Suba com 'ollama serve', ou rode com --simular."
                  % cliente.base_url, file=sys.stderr)
            return 1

    despachante = Despachante()
    print("[agente] backend: %s" % cliente.descricao, file=sys.stderr)

    perguntas = [pergunta] if pergunta else []
    while True:
        if not perguntas:
            if not args.interativo:
                break
            try:
                entrada = input("cliente> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not entrada or entrada.lower() in ("sair", "exit", "quit"):
                break
            perguntas.append(entrada)

        atual = perguntas.pop(0)
        # No modo simulado, cada pergunta reinicia o roteiro: o cliente
        # simulado guarda o passo em que está.
        if args.simular:
            cliente = llm.ClienteSimulado(roteiro=args.roteiro)

        try:
            resposta, eventos = laco.conversar(atual, cliente, despachante,
                                                narrar=_narrar)
        except llm.ErroDoModelo as erro:
            print("[erro] %s" % erro, file=sys.stderr)
            return 1
        except NotImplementedError as erro:
            # Lacuna ainda aberta. Vale uma mensagem dirigida em vez de um
            # traceback: o aluno precisa saber qual TODO abrir, não em que
            # linha do laço a exceção subiu.
            print("[lacuna aberta] %s" % erro, file=sys.stderr)
            print("               Preencha a lacuna indicada e rode de novo. "
                  "Se travar, o roteiro está no README, passo a passo.",
                  file=sys.stderr)
            return 1

        print("\natendente> %s\n" % resposta)
        autorizadas = sum(1 for _, r in eventos if r.autorizado)
        recusadas = len(eventos) - autorizadas
        print("[agente] %d chamada(s) autorizada(s), %d recusada(s); trilha em "
              "docs/AUDITORIA.md" % (autorizadas, recusadas), file=sys.stderr)

        if not args.interativo:
            break

    return 0


if __name__ == "__main__":
    sys.exit(main())
