#!/usr/bin/env python3
"""RESGATE: `agente/comandos.py` com TODO-3, TODO-4 e TODO-5 preenchidos.

Rede de segurança, igual à da Aula 03. Copie por cima do arquivo original
apenas se você travar e a noite estiver acabando:

    cp resgate/comandos.py agente/comandos.py

Quem usar o resgate registra `USEI_O_RESGATE` em `docs/EVIDENCIAS.md`.
"""
from . import api_pedidos, auditoria, esquemas
from . import validacao


class Resultado:
    """O que o Despachante devolve ao laço de conversa."""

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
    """Base de todo comando do agente."""

    nome = ""
    esquema = {}

    def validar(self, argumentos):
        return validacao.validar(argumentos, self.esquema)

    def executar(self, argumentos):
        raise NotImplementedError

    def descrever(self, argumentos):
        return "%s(%s)" % (self.nome, ", ".join(
            "%s=%s" % (k, v) for k, v in sorted(argumentos.items())))


class ConsultarStatusPedido(Comando):
    """Consulta o status de um pedido. Comando de leitura, sem efeito colateral."""

    nome = "consultar_status_pedido"
    esquema = esquemas.ESQUEMA_CONSULTAR_STATUS

    def executar(self, argumentos):
        # TODO-3 preenchido.
        pedido_id = argumentos["pedido_id"]
        return api_pedidos.obter_status(pedido_id)


class AlterarEnderecoEntrega(Comando):
    """Altera o endereço de entrega. Comando de escrita: muda o sistema."""

    nome = "alterar_endereco_entrega"
    esquema = esquemas.ESQUEMA_ALTERAR_ENDERECO

    CAMPOS_DO_ENDERECO = ("logradouro", "numero", "cidade", "uf", "cep",
                          "complemento")

    def executar(self, argumentos):
        # TODO-4 preenchido. O complemento só entra no corpo se veio: campo
        # opcional ausente não vira string vazia inventada pelo agente.
        pedido_id = argumentos["pedido_id"]
        endereco = {campo: argumentos[campo]
                    for campo in self.CAMPOS_DO_ENDERECO
                    if campo in argumentos}
        return api_pedidos.alterar_endereco(pedido_id, endereco)


class Despachante:
    """O *invoker* do Command Pattern: valida, autoriza, executa e audita."""

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
        argumentos = argumentos or {}
        comando = self.comandos.get(nome)

        if comando is None:
            motivo = ("a ferramenta '%s' não existe neste agente; disponíveis: %s"
                      % (nome, ", ".join(sorted(self.comandos)) or "nenhuma"))
            self._auditar(nome, auditoria.RECUSADO, argumentos, motivo)
            return Resultado(auditoria.RECUSADO, {"erro": motivo}, motivo)

        erros = comando.validar(argumentos)

        if erros:
            # TODO-5 preenchido: recusa auditada. O comando NÃO é executado,
            # o evento entra na trilha, e o motivo volta ao modelo para ele
            # conseguir pedir ao cliente o dado que faltou.
            motivo = "; ".join(erros)
            self._auditar(nome, auditoria.RECUSADO, argumentos, motivo)
            return Resultado(auditoria.RECUSADO, {
                "erro": "argumentos recusados pela validação",
                "detalhes": erros,
                "orientacao": ("peça ao cliente os dados que faltaram e chame "
                                "a ferramenta de novo com o conjunto completo"),
            }, motivo)

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
