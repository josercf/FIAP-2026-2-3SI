#!/usr/bin/env python3
"""RESGATE: `agente/esquemas.py` com TODO-1 e TODO-2 preenchidos.

Rede de segurança, igual à da Aula 03. Copie por cima do arquivo original
apenas se você travar e a noite estiver acabando:

    cp resgate/esquemas.py agente/esquemas.py

Quem usar o resgate registra `USEI_O_RESGATE` em `docs/EVIDENCIAS.md`. Usar
não reprova critério nenhum que o `verificar.py` consiga confirmar por
máquina, mas é informação que o professor precisa ter na correção.
"""

# TODO-1 preenchido.
ESQUEMA_CONSULTAR_STATUS = {
    "type": "object",
    "properties": {
        "pedido_id": {
            "type": "string",
            "description": ("Identificador do pedido na LogiTech, no formato "
                            "PED- seguido de quatro dígitos, como PED-1042."),
            "pattern": "^PED-[0-9]{4}$",
        },
    },
    "required": ["pedido_id"],
    "additionalProperties": False,
}

# TODO-2 preenchido. Os seis campos obrigatórios são exatamente os que o
# serviço de Pedidos exige no corpo do PATCH, mais o pedido_id da URL.
ESQUEMA_ALTERAR_ENDERECO = {
    "type": "object",
    "properties": {
        "pedido_id": {
            "type": "string",
            "description": "Identificador do pedido, no formato PED-0000.",
            "pattern": "^PED-[0-9]{4}$",
        },
        "logradouro": {
            "type": "string",
            "description": "Nome da rua, avenida ou rodovia.",
            "minLength": 3,
        },
        "numero": {
            "type": "string",
            "description": "Número do imóvel. Use 's/n' quando não houver.",
            "minLength": 1,
        },
        "complemento": {
            "type": "string",
            "description": "Apartamento, bloco, galpão ou portaria. Opcional.",
        },
        "cidade": {
            "type": "string",
            "description": "Município de entrega.",
            "minLength": 2,
        },
        "uf": {
            "type": "string",
            "description": "Sigla do estado, duas letras maiúsculas.",
            "pattern": "^[A-Z]{2}$",
        },
        "cep": {
            "type": "string",
            "description": ("CEP no formato 00000-000. Obrigatório: sem CEP a "
                            "alteração é recusada. Nunca invente um valor; "
                            "pergunte ao cliente."),
            "pattern": "^[0-9]{5}-[0-9]{3}$",
        },
    },
    "required": ["pedido_id", "logradouro", "numero", "cidade", "uf", "cep"],
    "additionalProperties": False,
}


def ferramentas():
    """Monta a lista de ferramentas no formato que a API de chat espera."""
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
