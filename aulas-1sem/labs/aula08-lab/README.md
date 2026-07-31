# Laboratório Prático - Aula 08

## Disciplina: Microservice and Web Engineering & IT Services
**Prof.º José Romualdo | FIAP Sistemas de Informação**

### Case: LogiTech Enterprise AI Platform (Fase 8, agente com ação no sistema)

O atendimento da LogiTech responde à mão, o dia inteiro, às mesmas duas
perguntas: **"onde está o meu pedido"** e **"muda o endereço de entrega"**. As
duas já existem como rota na API de Pedidos. O agente de IA pode resolver as
duas sozinho, **desde que não ganhe acesso solto ao sistema**.

Na Aula 03 a IA escreveu um arquivo para você conferir. Hoje ela **executa uma
ação no sistema**, e a diferença entre as duas coisas é toda a engenharia
desta noite: a saída de um modelo é **intenção**, não comando. Quem transforma
intenção em ação é uma camada sua, com contrato, autorização e trilha de
auditoria.

**Atividade em dupla**, oito passos. Um commit por passo.

---

## O que já vem pronto, e o que vocês fazem

| Vem pronto, não é tarefa | Vocês escrevem |
|---|---|
| `servicos/pedidos/`, o serviço de Pedidos congelado, no contrato da plataforma | `agente/esquemas.py`: as lacunas `TODO-1` e `TODO-2` |
| `atendente.py` e `agente/laco.py`, o laço de conversa completo | `agente/comandos.py`: as lacunas `TODO-3`, `TODO-4` e `TODO-5` |
| `agente/llm.py`, o cliente do Ollama e o modo `--simular` | As duas worktrees, `../wt-agente-pedidos` e `../wt-agente-atendimento` |
| `agente/validacao.py`, o validador de JSON Schema | `docs/EVIDENCIAS.md`, com os valores medidos por vocês |
| `agente/auditoria.py`, a trilha em `docs/AUDITORIA.md` | Um commit por passo concluído |
| `verificar.py` e a suíte `tests/`, a autoavaliação | |
| `resgate/`, a rede de segurança para quem travar | |

**Não editem `servicos/pedidos/app.py`.** Ele é a implementação provisória, em
Python, do serviço `pedidos` que nasce em Java na Aula 05, com exatamente as
mesmas rotas, porta e payloads do contrato da plataforma. Leiam
`servicos/pedidos/README.md`: entender o contrato dele é metade do trabalho de
hoje.

---

## Pré-requisitos

- Fork do repositório do laboratório (nunca clone direto).
- GitHub Codespaces, ou Python 3.11+ local com o Ollama instalado.
- Ter feito, ou ao menos lido, a Aula 07: o agente de hoje fala com a API de
  Pedidos por HTTP, e o endereço dela vem da variável `LOGITECH_PEDIDOS_URL`.

Nada além da biblioteca padrão é necessário para rodar o agente e o serviço.
Só a suíte de testes precisa do `pytest`, que já vem no devcontainer.

---

## Os oito passos

Cada passo termina com um commit. `python3 verificar.py` roda a qualquer
momento e diz exatamente qual critério está faltando e por quê.

### Passo 1, subir o serviço e ler o contrato

```bash
python3 servicos/pedidos/app.py          # deixe rodando neste terminal
```

Em outro terminal:

```bash
curl -s http://localhost:8080/health
curl -s http://localhost:8080/api/v1/pedidos/PED-1042/status
curl -s -X PATCH http://localhost:8080/api/v1/pedidos/PED-1043/endereco \
     -H 'Content-Type: application/json' \
     -d '{"logradouro":"Rua Bela Cintra","numero":"495","cidade":"São Paulo","uf":"SP"}'
```

A terceira chamada devolve `400` com a lista dos campos ausentes. **Guarde
essa resposta:** o objetivo do laboratório é que o seu agente nunca a provoque.

Deixe este terminal do serviço visível a noite inteira. É nele que você vai
provar, no passo 6, que a chamada malformada não saiu do agente.

### Passo 2, `TODO-1`: o schema da consulta

Em `agente/esquemas.py`, preencha `ESQUEMA_CONSULTAR_STATUS`. O arquivo diz o
que cada requisito significa. Confira com:

```bash
python3 -m pytest tests/test_esquemas.py -q
python3 verificar.py --criterio 1
```

### Passo 3, `TODO-2`: o schema da alteração

Ainda em `agente/esquemas.py`, preencha `ESQUEMA_ALTERAR_ENDERECO`, com os
**seis** campos obrigatórios e o `cep` entre eles. É esse `required` que faz o
passo 6 existir.

### Passo 4, `TODO-3`: o Command de leitura

Em `agente/comandos.py`, implemente `ConsultarStatusPedido.executar`. Depois:

```bash
python3 atendente.py --simular "Onde está o pedido PED-1042?"
python3 verificar.py --criterio 3
```

### Passo 5, `TODO-4`: o Command de escrita

Implemente `AlterarEnderecoEntrega.executar`. A validação acontece **antes**,
no Despachante, e o registro em `docs/AUDITORIA.md` acontece **depois**, com o
resultado real da chamada.

```bash
python3 atendente.py --simular "Mudar o endereço do PED-1044 para Avenida Paulista 1106, CEP 01311-000"
python3 verificar.py --criterio 4
```

Registre `PEDIDO_ALTERADO_ID` e `CEP_NOVO` em `docs/EVIDENCIAS.md`.

### Passo 6, `TODO-5`: a recusa auditada

Este é o passo que separa integração de engenharia. Implemente o bloco da
recusa no `Despachante` e depois **provoque o agente a alterar endereço sem
informar o CEP**:

```bash
python3 atendente.py --simular --roteiro recusa "Mudar o endereço do PED-1043"
```

Três coisas precisam acontecer, e você confere as três:

1. o veredito é `RECUSADO` e o comando **não executa**;
2. `docs/AUDITORIA.md` ganha uma linha `RECUSADO` com o motivo;
3. **nenhum `PATCH` aparece no log do serviço de Pedidos.** Olhe o terminal do
   passo 1. Se aparecer um `PATCH ... 400`, a validação aconteceu tarde demais:
   a chamada malformada saiu do agente e foi o serviço que recusou.

Registre `MOTIVO_DA_RECUSA` e `PATCH_CHEGOU_AO_SERVICO` em
`docs/EVIDENCIAS.md`.

### Passo 7, Git Worktrees: dois agentes ao mesmo tempo

Duas pessoas da dupla, duas linhas de trabalho, **um único clone**:

```bash
git switch -c agente/pedidos
git switch -c agente/atendimento
git switch main

git worktree add ../wt-agente-pedidos      agente/pedidos
git worktree add ../wt-agente-atendimento  agente/atendimento
git worktree list
```

Agora rode o agente **nos dois diretórios ao mesmo tempo**, em dois terminais,
apontando para o mesmo serviço de Pedidos:

```bash
# terminal A
cd ../wt-agente-pedidos     && python3 atendente.py --simular "Onde está o PED-1042?"
# terminal B
cd ../wt-agente-atendimento && python3 atendente.py --simular --roteiro recusa "Mudar o endereço do PED-1043"
```

Cada worktree tem o seu próprio diretório de trabalho e a sua própria branch
com o **mesmo** histórico. Nenhum `git switch` de um lado troca os arquivos
debaixo do processo que está rodando do outro.

Registre `WORKTREE_PEDIDOS`, `WORKTREE_ATENDIMENTO`, as duas branches e a
resposta de `O_QUE_ACONTECERIA_COM_CHECKOUT` em `docs/EVIDENCIAS.md`.

> As worktrees moram **fora** do repositório, um nível acima. Nunca as crie
> dentro da pasta do laboratório: elas virariam arquivos não rastreados do
> próprio repositório, e o `git status` ficaria impossível de ler.
> Para desfazer: `git worktree remove ../wt-agente-pedidos`.

### Passo 8, evidências, verificação e entrega

Complete `docs/EVIDENCIAS.md`, rode a régua inteira e faça o commit final:

```bash
python3 -m pytest -q          # a suíte completa
python3 verificar.py          # os nove critérios
```

---

## O modo `--simular`, dito na cara

`python3 atendente.py --simular ...` injeta uma **resposta de modelo já
formada**, escrita à mão em `agente/llm.py`. Ele existe porque o modelo local
é pequeno e tool calling é justamente a tarefa em que modelo pequeno erra
mais: sem esse modo, uma noite de má sorte com o `qwen3.5:2b` pararia o
laboratório inteiro por um motivo que não tem nada a ver com o que a aula
ensina.

**O que continua real no modo `--simular`:** a validação por JSON Schema, os
seus Commands, a chamada HTTP ao serviço de Pedidos, a trilha de auditoria e
as worktrees. O que vem pronto é apenas a intenção que, no outro modo, sairia
do modelo.

Rode com o Ollama também, pelo menos uma vez, e registre em
`TENTATIVAS_ATE_O_MODELO_ACERTAR` quantas tentativas foram necessárias:

```bash
python3 atendente.py "Onde está o meu pedido PED-1042?"
```

### Os números medidos na construção deste laboratório

Todos com o `qwen3.5:2b` local, `temperature 0.1`, o serviço de Pedidos no ar e
os esquemas de `resgate/` aplicados. São os mesmos números citados nos slides.

| Condição | Pergunta | Resultado |
|---|---|---|
| Descrição completa da ferramenta | "Onde está o meu pedido PED-1042?" | Chamada correta de `consultar_status_pedido` em **3 de 3** execuções |
| Descrição completa | Alterar endereço **sem informar o CEP** | Não chamou a ferramenta: pediu o CEP ao cliente, em **3 de 3** execuções |
| Descrição enfraquecida para `"Altera o endereço de entrega de um pedido."` | A mesma, sem CEP | Nenhuma chamada: resposta **vazia em 3 de 3** execuções, com `num_predict 400` e `num_ctx 8192`. Sem limite de tokens, duas execuções não retornaram em 600 e em 900 segundos, e foram descartadas como inconclusivas |

A leitura honesta desses números: com uma descrição boa, o modelo pequeno se
comportou bem em 6 de 6 execuções, e por isso **a recusa da lacuna `TODO-5`
não se demonstra só conversando com o modelo**. É o roteiro `--roteiro recusa`
e o próprio `verificar.py --criterio 5` que provocam a chamada malformada de
propósito. Prompt é otimização; schema é garantia.

O número de vocês pode ser diferente, e ele é informação útil para a turma.

---

## Critérios de aceitação

A tabela abaixo espelha, critério por critério, o que `verificar.py` confere.

| # | Critério | Verificado por |
|---|---|---|
| CA-01 | `TODO-1` e `TODO-2` preenchidos: as duas ferramentas declaradas, com `type: object`, `properties`, e `required` contendo os campos do contrato | `verificar.py --criterio 1` |
| CA-02 | O serviço de Pedidos responde `/health` e `GET /api/v1/pedidos/{id}/status` | `verificar.py --criterio 2` |
| CA-03 | `TODO-3`: `ConsultarStatusPedido` executa contra a API de verdade | `verificar.py --criterio 3` |
| CA-04 | `TODO-4`: `AlterarEnderecoEntrega` altera de verdade, e o CEP novo é lido de volta do serviço | `verificar.py --criterio 4` |
| CA-05 | `TODO-5`: alteração sem CEP recebe veredito `RECUSADO`, é registrada, e o endereço **não** muda no serviço | `verificar.py --criterio 5` |
| CA-06 | `docs/AUDITORIA.md` com no mínimo **3** execuções `AUTORIZADO` e **1** `RECUSADO` | `verificar.py --criterio 6` |
| CA-07 | `git worktree list` mostrando `wt-agente-pedidos` e `wt-agente-atendimento` | `verificar.py --criterio 7` |
| CA-08 | `docs/EVIDENCIAS.md` com os marcadores preenchidos, `PEDIDO_ALTERADO_ID` no formato `PED-0000` e `CEP_NOVO` no formato `00000-000` | `verificar.py --criterio 8` |
| CA-09 | Suíte de testes de unidade verde: `python3 -m pytest tests -q` | `verificar.py --criterio 9` |

```bash
python3 verificar.py               # roda os nove critérios
python3 verificar.py --criterio 5  # roda só um
```

O verificador sobe o serviço de Pedidos numa porta livre quando não encontra
o serviço deste laboratório no ar, e derruba o processo ao terminar. Ele
confere qual serviço respondeu antes de confiar nele: a porta 8080 é das mais
disputadas de qualquer máquina, e um serviço homônimo de outro projeto
respondendo `{"status":"ok"}` já reprovou critérios que estavam corretos
durante a construção deste laboratório.

### A suíte de testes já vem escrita, e vermelha

`tests/` traz **42 testes**, e 17 deles falham antes de você preencher as
cinco lacunas. Isso é proposital: a suíte descreve o comportamento esperado
antes de ele existir, que é o ciclo que a Aula 10 formaliza como TDD. Cada
lacuna preenchida apaga um bloco de vermelho. Quando o último apagar, o
critério CA-09 fecha.

### O que a máquina prova, e o que fica por sua conta

| Critério | Verificado por máquina | Declarado por você |
|---|---|---|
| CA-01 a CA-05 | Tudo. Os comandos são executados de verdade contra o serviço, e a recusa é provocada pelo próprio verificador | - |
| CA-06 | A contagem de `AUTORIZADO` e `RECUSADO` na trilha, lida do arquivo | Que os eventos vieram de conversas suas, e não de linhas coladas à mão |
| CA-07 | Que as duas worktrees existem e estão ligadas ao repositório, via `git worktree list` | Que você rodou os dois agentes **ao mesmo tempo**: o verificador vê as worktrees, não os processos que já terminaram |
| CA-08 | Formato de `PEDIDO_ALTERADO_ID` e `CEP_NOVO`, contagens mínimas, tamanho mínimo do motivo | `PATCH_CHEGOU_AO_SERVICO` e `O_QUE_ACONTECERIA_COM_CHECKOUT`: são leitura sua do log e raciocínio seu |
| CA-09 | A suíte inteira, executada | - |

Preencher com valor fabricado engana a correção, não o `verificar.py`.

---

## Entregáveis com número

1. As **5 lacunas** `TODO-1` a `TODO-5` preenchidas.
2. `python3 -m pytest -q` verde: **42 testes** em `tests/`, mais os testes do
   próprio verificador em `test_verificar.py`.
3. `docs/AUDITORIA.md` com no mínimo **3 execuções autorizadas** e
   **1 recusa**.
4. `git worktree list` mostrando as **2 worktrees**, cada uma em uma branch.
5. `docs/EVIDENCIAS.md` com `PEDIDO_ALTERADO_ID`, `CEP_NOVO`,
   `MOTIVO_DA_RECUSA`, `PATCH_CHEGOU_AO_SERVICO`, `EXECUCOES_AUTORIZADAS`,
   `RECUSAS_REGISTRADAS`, as duas worktrees, as duas branches, `MODO_USADO`,
   `TENTATIVAS_ATE_O_MODELO_ACERTAR` e `USEI_O_RESGATE`.
6. `python3 verificar.py` imprimindo **9 de 9**.

---

## Ordem de corte, se o tempo apertar

O laboratório cabe em 60 minutos para quem acompanhou as aulas anteriores. Se
faltar tempo, corte **de baixo para cima**:

1. Primeiro: `TENTATIVAS_ATE_O_MODELO_ACERTAR` e a execução com o Ollama. Use
   só o `--simular` e registre `MODO_USADO: simular`.
2. Depois: o passo 7 fica com as worktrees criadas e listadas, sem rodar os
   dois agentes ao mesmo tempo.
3. Por último, e só em emergência: `resgate/`. Copie o arquivo, registre
   `USEI_O_RESGATE`, e **não pule o passo 6**: a recusa auditada é o assunto
   da noite.

Os passos 1 a 6 não se cortam. São o critério CA-01 a CA-06 e o conteúdo do
Checkpoint 2.

---

## Como entregar

**Um commit por passo concluído**, no padrão Conventional Commits:

```bash
git add docs/EVIDENCIAS.md
git commit -m "feat(passo-1): contrato do serviço de Pedidos conferido"

git add agente/esquemas.py
git commit -m "feat(passo-2): schema de consultar_status_pedido"

git add agente/esquemas.py
git commit -m "feat(passo-3): schema de alterar_endereco_entrega"

git add agente/comandos.py
git commit -m "feat(passo-4): Command de consulta de status"

git add agente/comandos.py docs/
git commit -m "feat(passo-5): Command de alteração de endereço"

git add agente/comandos.py docs/
git commit -m "feat(passo-6): recusa auditada de chamada sem CEP"

git add docs/EVIDENCIAS.md
git commit -m "feat(passo-7): worktrees dos dois agentes"

git add docs/
git commit -m "feat(passo-8): evidências e verificação final"
```

Depois envie a URL do **seu fork** no formulário da aula. A atividade de hoje
é em dupla: um envio por dupla, com os dois nomes.

---

## Referências do laboratório

- Ollama, API de tool calling: <https://ollama.readthedocs.io/en/api/>
- JSON Schema, especificação de validação: <https://json-schema.org/>
- Git, `git-worktree`: <https://git-scm.com/docs/git-worktree>
- Contrato da plataforma LogiTech: `docs/adrs/ADR-006` do acervo da disciplina
