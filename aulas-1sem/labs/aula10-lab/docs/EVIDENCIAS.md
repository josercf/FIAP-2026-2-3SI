# Evidências, Aula 10, Testes de Unidade e Portal do Cliente

Formulário único, preenchido à medida que você fecha cada passo.
`verificar.py` lê estes marcadores procurando `MARCADOR: valor`. Não apague o
nome do marcador, não mude a grafia, e troque `PREENCHER` pelo valor real
medido na sua máquina. Um `PREENCHER` esquecido reprova o critério 8.

São **nove marcadores**. Cinco são números conferidos contra a execução de
verdade: `VALOR_EXPRESSO_PED_1001`, `VALOR_PADRAO_PED_1003`,
`PRAZO_PADRAO_PED_1003`, `TESTES_PYTEST` e `TESTES_VITEST`. Número inventado
não passa: o verificador roda as duas suítes e compara.

---

## Passo 1, a cotação da rota de referência

Depois do `TODO-1`, rode a suíte e confira os números que os seus próprios
testes usam. Eles saem do serviço de Pedidos congelado:

- `PED-1001`: Supermercados Aurora, SAO para LDB, 100 kg;
- `PED-1003`: Metalúrgica Ipiranga, BHZ para SSA, 12500 kg.

Para ver os valores fora do teste, com os dois serviços no ar:

```bash
curl -s -X POST http://localhost:8000/api/v1/frete/cotacao/pedido \
  -H 'Content-Type: application/json' \
  -d '{"pedidoId": "PED-1001", "modalidade": "expresso"}'

curl -s -X POST http://localhost:8000/api/v1/frete/cotacao/pedido \
  -H 'Content-Type: application/json' \
  -d '{"pedidoId": "PED-1003", "modalidade": "padrao"}'
```

```
VALOR_EXPRESSO_PED_1001: PREENCHER
VALOR_PADRAO_PED_1003: PREENCHER
PRAZO_PADRAO_PED_1003: PREENCHER
```

O segundo valor é o que carrega as duas regras comerciais ao mesmo tempo:
desconto de carga fechada e um dia a mais de pernoite. Se ele bater, as duas
estão vivas.

---

## Passo 2, o tamanho e o custo da suíte de unidade

```bash
python3 -m pytest
```

Copie o número de testes que passaram e o tempo que a suíte levou. O tempo é
o argumento da aula: teste de unidade é barato, e é por isso que ele fica na
base da pirâmide. Se a sua suíte demorar segundos, alguma coisa nela está
tocando em disco ou em rede.

```
TESTES_PYTEST: PREENCHER
TEMPO_SUITE_PYTEST_S: PREENCHER
```

---

## Passo 3, a suíte do portal

```bash
cd portal && npx vitest run
```

```
TESTES_VITEST: PREENCHER
```

---

## Passo 4, o portal no navegador

Com `pedidos` na 8080, `frete` na 8000 e o portal na 5173, abra
<http://localhost:5173>, deixe `PED-1001` selecionado e copie **o texto que
aparece na tela** como situação do pedido. Não é o código que a API devolve:
é o rótulo em português que o `TODO-4` monta.

```
STATUS_NA_TELA_PED_1001: PREENCHER
```

---

## Passo 5, o CORS visto de dentro

Este passo existe para você reconhecer o erro quando ele acontecer no seu
projeto, e não em sala com o professor ao lado.

Derrube o serviço de frete e suba de novo com uma origem que não é a do
portal:

```bash
cd servicos/frete
LOGITECH_CORS_ORIGINS=http://localhost:9999 uvicorn app.main:app --port 8000
```

Volte ao portal, aperte **Cotar** e abra o console do navegador. Cole aqui a
mensagem que apareceu, em uma linha.

```
MENSAGEM_DE_CORS: PREENCHER
```

Repare no que aconteceu na tela: nada de diferente, ou quase nada. O serviço
respondeu 200, o navegador leu o cabeçalho, não encontrou a sua origem e
descartou a resposta antes de o React ver. É por isso que a ADR-008 pôs CORS
no contrato da plataforma em vez de deixar para a aula descobrir.

Suba o frete de novo sem a variável antes de seguir.

---

## Passo 6, o resgate

O diretório `resgate/` traz as seis lacunas resolvidas. Usá-lo não reprova
critério nenhum que a máquina consiga conferir: é informação que o professor
precisa ter, não armadilha.

```
USEI_O_RESGATE: PREENCHER (escreva "não", ou "sim, a partir do TODO-N")
```

---

## O que a máquina prova e o que fica por sua conta

| A máquina prova | Fica por sua conta |
|---|---|
| Que os seus testes reprovam código estragado | Que eles têm nome legível e dizem a regra de negócio |
| Que a suíte roda sem rede | Que ela continua rodando sem rede daqui a três meses |
| Que os números batem | Que você entendeu de onde eles vêm |
| Que os componentes atendem à especificação | Que a tela é usável por quem não escreveu o código |
