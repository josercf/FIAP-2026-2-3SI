#!/usr/bin/env python3
"""Command Pattern: a camada entre a intenção do modelo e a ação no sistema.

Aqui moram as lacunas TODO-3, TODO-4 e TODO-5.

A saída de um modelo com tool calling **não é um comando**: é uma intenção,
um texto que diz "eu chamaria a ferramenta X com estes argumentos". Quem
transforma intenção em ação é este módulo, e ele o faz em três etapas que
nunca mudam de ordem:

    intenção do modelo  ->  validar contra o JSON Schema
                        ->  autorizar (ou recusar)
                        ->  executar e auditar

O `Despachante` é o *invoker* do padrão: ele não sabe o que cada comando faz,
sabe apenas que todo comando se valida, se executa e se audita do mesmo jeito.
Acrescentar uma ferramenta nova não muda uma linha do Despachante.
"""
from . import api_pedidos, auditoria, esquemas
from . import validacao


class Resultado:
    """O que o Despachante devolve ao laço de conversa.

    `conteudo` é o que volta para o modelo como resultado da ferramenta. Note
    que **uma recusa também volta para o modelo**: é assim que ele consegue
    pedir o CEP que faltava, em vez de simplesmente travar.
    """

    def __init__(self, veredito, conteudo, motivo=""):
        self.veredito = veredito
        self.conteudo = conteudo
        self.motivo = motivo

    @property
    def autorizado(self):
        return self.veredito == auditoria.AUTORIZADO

    def __repr__(self):
        return "Resultado(%s, %r)" % (self.veredito, self.motivo or self.conteudo)


class Comando:
    """Base de todo comando do agente. PRONTO: não é tarefa.

    Cada subclasse declara o nome exato da ferramenta (o mesmo string que o
    modelo recebe em `agente/esquemas.py`) e o esquema contra o qual os
    argumentos são validados.
    """

    nome = ""
    esquema = {}

    def validar(self, argumentos):
        """Devolve a lista de erros dos argumentos contra o JSON Schema.

        Lista vazia significa autorizado. Este método é chamado pelo
        Despachante **antes** de `executar`, sempre, sem exceção.
        """
        return validacao.validar(argumentos, self.esquema)

    def executar(self, argumentos):
        """Executa a ação de verdade. Só é chamado com argumentos válidos."""
        raise NotImplementedError

    def descrever(self, argumentos):
        """Frase curta para o log de sala, no formato que um auditor leria."""
        return "%s(%s)" % (self.nome, ", ".join(
            "%s=%s" % (k, v) for k, v in sorted(argumentos.items())))


class ConsultarStatusPedido(Comando):
    """Consulta o status de um pedido. Comando de leitura, sem efeito colateral."""

    nome = "consultar_status_pedido"
    esquema = esquemas.ESQUEMA_CONSULTAR_STATUS

    def executar(self, argumentos):
        # -------------------------------------------------------------------
        # TODO-3: implemente a execução deste comando.
        #
        # O que fazer:
        #   1. tirar `pedido_id` de `argumentos`;
        #   2. chamar `api_pedidos.obter_status(pedido_id)`, que faz o
        #      GET /api/v1/pedidos/{id}/status do contrato da plataforma;
        #   3. devolver o dicionário que a API respondeu.
        #
        # O que NÃO fazer:
        #   - não valide nada aqui: quando este método roda, o Despachante já
        #     validou. Validar duas vezes esconde de quem lê o código onde a
        #     autorização realmente acontece;
        #   - não capture ErroDeApi: o Despachante já trata, e registra
        #     FALHOU na auditoria com o motivo real.
        # -------------------------------------------------------------------
        raise NotImplementedError(
            "TODO-3: implemente ConsultarStatusPedido.executar em "
            "agente/comandos.py")


class AlterarEnderecoEntrega(Comando):
    """Altera o endereço de entrega. Comando de escrita: muda o sistema."""

    nome = "alterar_endereco_entrega"
    esquema = esquemas.ESQUEMA_ALTERAR_ENDERECO

    # Os campos que compõem o endereço no corpo do PATCH. `pedido_id` não
    # entra: ele vai na URL, não no corpo.
    CAMPOS_DO_ENDERECO = ("logradouro", "numero", "cidade", "uf", "cep",
                          "complemento")

    def executar(self, argumentos):
        # -------------------------------------------------------------------
        # TODO-4: implemente a execução deste comando.
        #
        # O que fazer:
        #   1. tirar `pedido_id` de `argumentos`;
        #   2. montar o dicionário do endereço com os campos de
        #      CAMPOS_DO_ENDERECO que vieram em `argumentos` (o `complemento`
        #      pode não vir: não o invente, apenas não o inclua);
        #   3. chamar `api_pedidos.alterar_endereco(pedido_id, endereco)`, que
        #      faz o PATCH /api/v1/pedidos/{id}/endereco;
        #   4. devolver o dicionário que a API respondeu.
        #
        # A validação acontece ANTES desta chamada, no Despachante, e é o que
        # garante que nenhum PATCH incompleto sai daqui. O registro em
        # docs/AUDITORIA.md acontece DEPOIS, também no Despachante, com o
        # resultado real da chamada.
        # -------------------------------------------------------------------
        raise NotImplementedError(
            "TODO-4: implemente AlterarEnderecoEntrega.executar em "
            "agente/comandos.py")


class Despachante:
    """O *invoker* do Command Pattern: valida, autoriza, executa e audita.

    Este é o único ponto do agente com permissão de agir sobre o sistema. O
    laço de conversa não chama comando nenhum diretamente: ele entrega o nome
    e os argumentos que o modelo produziu e recebe um `Resultado`.
    """

    def __init__(self, comandos=None, caminho_auditoria=None):
        lista = comandos if comandos is not None else [
            ConsultarStatusPedido(),
            AlterarEnderecoEntrega(),
        ]
        self.comandos = {c.nome: c for c in lista}
        self.caminho_auditoria = caminho_auditoria

    def _auditar(self, ferramenta, veredito, argumentos, resultado):
        return auditoria.registrar(ferramenta, veredito, argumentos, resultado,
                                    caminho=self.caminho_auditoria)

    def despachar(self, nome, argumentos):
        """Recebe a intenção do modelo e devolve um `Resultado` auditado."""
        argumentos = argumentos or {}
        comando = self.comandos.get(nome)

        # Caso 1, PRONTO e resolvido: o modelo inventou uma ferramenta que não
        # existe. Isso acontece na prática, e a resposta certa é a mesma de
        # qualquer outra recusa: não executar, registrar e devolver o motivo
        # para o modelo. Use este bloco como modelo do TODO-5.
        if comando is None:
            motivo = ("a ferramenta '%s' não existe neste agente; disponíveis: %s"
                      % (nome, ", ".join(sorted(self.comandos)) or "nenhuma"))
            self._auditar(nome, auditoria.RECUSADO, argumentos, motivo)
            return Resultado(auditoria.RECUSADO, {"erro": motivo}, motivo)

        erros = comando.validar(argumentos)

        # Caso 2: os argumentos não cumprem o JSON Schema.
        if erros:
            # ---------------------------------------------------------------
            # TODO-5: recusa auditada.
            #
            # Este é o critério que separa integração de engenharia. O que
            # tem que acontecer aqui, nesta ordem:
            #   1. montar um `motivo` legível a partir da lista `erros`
            #      (junte as mensagens com "; ");
            #   2. registrar o evento com `self._auditar(...)`, veredito
            #      `auditoria.RECUSADO`, guardando os argumentos exatamente
            #      como o modelo os pediu;
            #   3. devolver um `Resultado(auditoria.RECUSADO, {...}, motivo)`
            #      cujo `conteudo` explique ao modelo o que faltou, para ele
            #      conseguir pedir o dado ao cliente.
            #
            # O que NÃO pode acontecer, em hipótese nenhuma:
            #   - chamar `comando.executar(...)` mesmo assim;
            #   - "completar" o campo que faltou com um valor padrão;
            #   - devolver sucesso silencioso.
            #
            # Prove no laboratório: peça ao agente para mudar o endereço SEM
            # informar o CEP. O esperado é uma linha RECUSADO na trilha de
            # auditoria e NENHUM PATCH chegando ao serviço de Pedidos. Se o
            # log do serviço mostrar um 400, a recusa aconteceu tarde demais.
            # ---------------------------------------------------------------
            raise NotImplementedError(
                "TODO-5: implemente a recusa auditada em "
                "agente/comandos.py, classe Despachante")

        # Caso 3, PRONTO: argumentos válidos. Executa e audita o resultado.
        try:
            saida = comando.executar(argumentos)
        except api_pedidos.ErroDeApi as erro:
            motivo = str(erro)
            self._auditar(nome, auditoria.FALHOU, argumentos, motivo)
            return Resultado(auditoria.FALHOU, {"erro": motivo}, motivo)
        except NotImplementedError as erro:
            motivo = str(erro)
            self._auditar(nome, auditoria.FALHOU, argumentos, motivo)
            return Resultado(auditoria.FALHOU, {"erro": motivo}, motivo)

        self._auditar(nome, auditoria.AUTORIZADO, argumentos, saida)
        return Resultado(auditoria.AUTORIZADO, saida)
