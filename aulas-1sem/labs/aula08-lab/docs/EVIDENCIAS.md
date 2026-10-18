# Evidências, Aula 08, Function Calling, Command Pattern e Git Worktrees

Formulário único, preenchido à medida que você cumpre cada passo.
`verificar.py` lê estes marcadores procurando `MARCADOR: valor`. Não apague o
nome do marcador, não mude a grafia, e troque `PREENCHER` pelo valor real
observado na sua máquina. Um `PREENCHER` esquecido reprova o critério 8.

---

## Passo 5, alteração autorizada

O pedido cujo endereço o **seu** agente alterou com sucesso, e o CEP novo que
ficou gravado. Confira com:

```bash
curl -s http://localhost:8080/api/v1/pedidos/PED-1044 | python3 -m json.tool
```

```
PEDIDO_ALTERADO_ID: PREENCHER
CEP_NOVO: PREENCHER
```

---

## Passo 6, recusa auditada

Provoque o agente a alterar o endereço **sem informar o CEP** e copie aqui o
motivo exatamente como o Despachante registrou em `docs/AUDITORIA.md`, coluna
`Resultado` da linha `RECUSADO`.

```
MOTIVO_DA_RECUSA: PREENCHER
```

Responda também, em uma frase, olhando o terminal onde o serviço de Pedidos
está rodando: **apareceu alguma requisição `PATCH` no log do serviço no
momento da recusa?** Se apareceu, a validação aconteceu tarde demais.

```
PATCH_CHEGOU_AO_SERVICO: PREENCHER
```

---

## Passo 7, worktrees

Os dois diretórios de trabalho criados, e as branches ligadas a cada um. Cole
o valor lido de `git worktree list`.

```
WORKTREE_PEDIDOS: PREENCHER
WORKTREE_ATENDIMENTO: PREENCHER
BRANCH_PEDIDOS: PREENCHER
BRANCH_ATENDIMENTO: PREENCHER
```

Responda em uma frase: com os dois agentes rodando ao mesmo tempo, o que
aconteceria se, em vez de worktrees, vocês tivessem usado `git checkout` no
mesmo diretório?

```
O_QUE_ACONTECERIA_COM_CHECKOUT: PREENCHER
```

---

## Passo 8, contagem da trilha

Números lidos de `docs/AUDITORIA.md` depois das suas conversas. O mínimo é
**3 execuções autorizadas** e **1 recusa**.

```
EXECUCOES_AUTORIZADAS: PREENCHER
RECUSAS_REGISTRADAS: PREENCHER
```

---

## Backend usado

`ollama` se o modelo local produziu as chamadas de ferramenta, `simular` se
você usou o modo `--simular`, `os dois` se usou os dois durante a noite. As
três respostas valem: o modo `--simular` existe justamente para o laboratório
não depender do acerto de um modelo de 2 bilhões de parâmetros.

```
MODO_USADO: PREENCHER
```

Se você rodou com o Ollama, registre em quantas tentativas o modelo produziu
a chamada de ferramenta correta. Errar faz parte, e o número é informação útil
para a turma inteira.

```
TENTATIVAS_ATE_O_MODELO_ACERTAR: PREENCHER
```

---

## Uso do resgate

Preencha se você copiou algum arquivo de `resgate/` por cima do seu, em vez de
escrever a lacuna. Usar o resgate não reprova critério nenhum que o
`verificar.py` consiga confirmar por máquina, mas é informação que o professor
precisa ter na correção.

```
USEI_O_RESGATE: PREENCHER
```

Se você não usou o resgate, escreva `USEI_O_RESGATE: não`.
