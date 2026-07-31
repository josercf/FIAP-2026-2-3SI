# Serviço de Pedidos, congelado

Este diretório **não é tarefa do laboratório**. Ele existe para que o agente de
IA que você escreve hoje tenha uma API real para chamar.

## Por que ele está em Python e não em Java

O contrato da plataforma LogiTech (ADR-006 do acervo da disciplina) define o
serviço `pedidos` como **Java 21 com Spring Boot 3**, nascido na Aula 05, na
porta **8080**. Esta é uma **implementação provisória em Python** do mesmo
contrato, escrita para a Aula 08 por dois motivos:

1. o devcontainer desta aula não precisa carregar JDK, Maven e um build de
   Spring Boot só para o agente ter em quem bater;
2. o laboratório de hoje é sobre o agente, não sobre o serviço.

**As rotas, a porta e os payloads são os mesmos do contrato.** Quando a
plataforma inteira subir no Docker Compose, o agente que você escreve hoje
passa a apontar para o serviço Java sem que uma linha do agente mude, porque
o endereço vem da variável `LOGITECH_PEDIDOS_URL` e o contrato é idêntico.

## Rotas

| Método | Rota | O que faz |
|---|---|---|
| `GET` | `/health` | `{"status": "ok"}`, base do `healthcheck` do Compose |
| `GET` | `/api/v1/pedidos` | Lista resumida dos pedidos |
| `GET` | `/api/v1/pedidos/{id}` | Pedido completo |
| `POST` | `/api/v1/pedidos` | Cria pedido |
| `GET` | `/api/v1/pedidos/{id}/status` | **Consumida pelo agente** |
| `PATCH` | `/api/v1/pedidos/{id}/endereco` | **Consumida pelo agente** |

`PATCH /api/v1/pedidos/{id}/endereco` exige, no corpo, os cinco campos
`logradouro`, `numero`, `cidade`, `uf` e `cep`. `complemento` é opcional.
Faltando qualquer obrigatório, o serviço responde `400` com a lista dos campos
ausentes. É esse `400` que o seu agente **não pode** provocar: a validação por
JSON Schema acontece antes da chamada.

## Como subir

```bash
python3 servicos/pedidos/app.py
# em outro terminal
curl -s http://localhost:8080/health
curl -s http://localhost:8080/api/v1/pedidos/PED-1042/status
```

O estado vive em memória. Reiniciar o processo devolve os quatro pedidos
semente: `PED-1042`, `PED-1043`, `PED-1044` e `PED-2001`. `PED-2001` já está
`ENTREGUE` de propósito, e uma tentativa de mudar o endereço dele recebe `409`.
