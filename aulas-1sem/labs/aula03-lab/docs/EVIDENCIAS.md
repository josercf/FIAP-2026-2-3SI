# Evidências, Aula 03, Docker I

Formulário único, preenchido à medida que você cumpre cada etapa. `verificar.py`
lê estes marcadores em busca de `MARCADOR: valor`. Não apague o nome do
marcador, não mude a grafia, e troque `PREENCHER` pelo valor real medido na sua
máquina. Um `PREENCHER` esquecido reprova a etapa correspondente.

Sete dos campos abaixo são valores numéricos, conforme o entregável do
laboratório: os quatro tamanhos de imagem, os dois percentuais de redução e a
memória do coletor. `LINHAS_APOS_RM` e `IMAGEM_PUBLICA` são prova de execução,
não entram nessa contagem.

---

## Etapa 4, Multi-stage

Meça o tamanho de cada imagem em megabytes com `docker image ls` (coluna
`SIZE`), uma vez com o Dockerfile ingênuo de `baseline/` e outra vez com o
Dockerfile multi-stage que você escreveu na raiz do laboratório. O comando e o
passo a passo completo estão em `etapas/04-multistage/RESPOSTAS.md`.

```
TAMANHO_COLETOR_INGENUO_MB: PREENCHER
TAMANHO_COLETOR_FINAL_MB: PREENCHER
REDUCAO_COLETOR: PREENCHER %

TAMANHO_GATEWAY_INGENUO_MB: PREENCHER
TAMANHO_GATEWAY_FINAL_MB: PREENCHER
REDUCAO_GATEWAY: PREENCHER %
```

O verificador exige que os dois percentuais de redução sejam de no mínimo
80%, o mesmo mínimo confirmado por medição real na Tarefa 1 deste plano
(coletor: 95,2%; gateway: 86,2%, os dois em arm64).

---

## Etapa 5, Volumes

Quantas linhas do arquivo de telemetria sobreviveram depois que você destruiu
o container e leu o mesmo volume de outro container, do zero. Comando
completo em `etapas/05-volumes/RESPOSTAS.md`.

```
LINHAS_APOS_RM: PREENCHER
```

---

## Etapa 6, Network e observação

Memória do coletor em megabytes, lida de um `docker stats --no-stream` com o
coletor rodando na rede `logitech-net`. Comando completo em
`etapas/06-network/RESPOSTAS.md`.

```
MEMORIA_COLETOR_MB: PREENCHER
```

---

## Etapa 7, Registry e Docker Hub

A imagem que você publicou, pública, no formato `usuario/imagem:tag`. O
verificador chama `docker manifest inspect` nesse valor de verdade: precisa
responder no registry, não basta o texto estar aqui. Comando completo em
`etapas/07-registry/RESPOSTAS.md`.

```
IMAGEM_PUBLICA: PREENCHER
```

---

## Uso do resgate

Preencha em qualquer momento em que tiver copiado um Dockerfile de
`resgate/` para a raiz do laboratório, em vez de escrever o seu. Usar o
resgate não reprova nenhuma etapa que o `verificar.py` consiga confirmar por
máquina (o Dockerfile de resgate builda, tem multi-stage e usuário não-root
de verdade), mas é informação que o professor precisa ter na correção.

```
USEI_O_RESGATE: PREENCHER
```

Se você não usou o resgate em etapa nenhuma, escreva `USEI_O_RESGATE: não`.
