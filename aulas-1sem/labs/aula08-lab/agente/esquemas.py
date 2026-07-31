#!/usr/bin/env python3
"""Declaração das ferramentas do agente: as lacunas TODO-1 e TODO-2.

Este é o contrato que o modelo enxerga. Ele nunca vê o seu código: vê estes
dicionários, serializados como JSON, e é só a partir deles que decide qual
ferramenta chamar e com quais argumentos.

Duas consequências práticas, e as duas caem na prova:

1. **A descrição é interface, não comentário.** Se a descrição de
   `alterar_endereco_entrega` não disser que o CEP é obrigatório, o modelo vai
   tentar alterar endereço sem CEP, e não é culpa dele.
2. **O schema é o mesmo objeto usado na validação.** O que você declara aqui é
   o que `agente/comandos.py` valida antes de executar. Declarar bonito e
   validar frouxo não protege ninguém.

Formato: o campo `parameters` é um **JSON Schema** de objeto, exatamente como
a API de tool calling do Ollama e a API compatível com OpenAI esperam.
"""

# ---------------------------------------------------------------------------
# TODO-1: JSON Schema de consultar_status_pedido
# ---------------------------------------------------------------------------
# Escreva o JSON Schema dos argumentos da ferramenta de consulta. Requisitos:
#
#   - `type` do esquema: "object"
#   - uma propriedade `pedido_id`, do tipo string, com `description` dizendo o
#     formato ("PED-" seguido de quatro dígitos, como PED-1042)
#   - `pattern` que force esse formato, para o modelo não inventar "1042" nem
#     "pedido 1042"
#   - `pedido_id` na lista `required`
#   - `additionalProperties: false`, para o modelo não conseguir contrabandear
#     um campo que o seu Command não espera
#
# Exemplo de um esquema com a forma certa (de outra ferramenta, não desta):
#
#   {
#       "type": "object",
#       "properties": {
#           "placa": {"type": "string", "description": "Placa do caminhão",
#                      "pattern": "^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$"},
#       },
#       "required": ["placa"],
#       "additionalProperties": False,
#   }
ESQUEMA_CONSULTAR_STATUS = {}


# ---------------------------------------------------------------------------
# TODO-2: JSON Schema de alterar_endereco_entrega, com os campos obrigatórios
# ---------------------------------------------------------------------------
# Escreva o JSON Schema dos argumentos da ferramenta de alteração. Requisitos:
#
#   - `type` do esquema: "object"
#   - propriedades: `pedido_id`, `logradouro`, `numero`, `cidade`, `uf`, `cep`
#     e `complemento`
#   - `uf` com `pattern` de duas letras maiúsculas
#   - `cep` com `pattern` no formato brasileiro `00000-000`
#   - `required` com **seis** campos: `pedido_id`, `logradouro`, `numero`,
#     `cidade`, `uf` e `cep`. `complemento` fica de fora, porque é opcional no
#     contrato do serviço de Pedidos (veja servicos/pedidos/README.md)
#   - `additionalProperties: false`
#
# O `cep` em `required` é o que faz a lacuna TODO-5 existir: sem ele aqui, a
# chamada malformada passa direto e chega ao serviço.
ESQUEMA_ALTERAR_ENDERECO = {}


# ---------------------------------------------------------------------------
# PRONTO: a declaração que vai para o modelo. Não precisa mexer.
# ---------------------------------------------------------------------------
def ferramentas():
    """Monta a lista de ferramentas no formato que a API de chat espera.

    Chamada tanto pelo cliente real do Ollama quanto pelo modo `--simular`,
    para que os dois recebam exatamente a mesma declaração.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "consultar_status_pedido",
                "description": (
                    "Consulta a situação atual de um pedido da LogiTech: "
                    "status, transportadora, última posição conhecida e "
                    "previsão de entrega. Use sempre que o cliente perguntar "
                    "onde está o pedido dele."
                ),
                "parameters": ESQUEMA_CONSULTAR_STATUS,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "alterar_endereco_entrega",
                "description": (
                    "Altera o endereço de entrega de um pedido da LogiTech. "
                    "Exige o endereço COMPLETO: logradouro, número, cidade, "
                    "UF e CEP. Se o cliente não informou o CEP, pergunte a ele "
                    "antes de chamar esta ferramenta, nunca invente um valor."
                ),
                "parameters": ESQUEMA_ALTERAR_ENDERECO,
            },
        },
    ]
