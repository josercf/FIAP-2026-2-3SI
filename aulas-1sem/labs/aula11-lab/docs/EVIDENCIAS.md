# Evidências do laboratório da Aula 11

**Dupla:** _(nomes completos)_
**Fork:** _(URL do fork)_

Preencha cada marcador com o número que **a sua execução** devolveu. O
`verificar.py` confere a coerência entre eles e prova o cancelamento ao vivo
contra o serviço de Faturamento: número inventado não passa.

Formato: uma linha por marcador, no padrão `MARCADOR: numero`. Sem unidade,
sem texto na mesma linha.

---

## 1. A suíte de testes

Rode `cd painel-admin && npx ng test --watch=false` e copie os dois números
do rodapé.

```
TESTES_TOTAL:
TESTES_VERDES:
```

## 2. O tamanho do painel compilado

Rode `cd painel-admin && npx ng build` e copie o **Initial total** em kB (só o
número, com uma casa decimal se houver).

```
BUNDLE_INICIAL_KB:
```

## 3. O fluxo de frota chegando na tela

Com o coletor, o simulador e o painel de pé, abra `http://localhost:4200`.

- `PLACAS_NO_PAINEL`: quantas linhas a tabela mostra com o filtro em `TODAS`.
- `PLACAS_APOS_FILTRO_PR`: quantas sobram ao clicar em `PR`.

```
PLACAS_NO_PAINEL:
PLACAS_APOS_FILTRO_PR:
```

## 4. O teardown do TODO-2, visto do outro lado

Consulte `curl -s http://localhost:3000/health` e leia `sse_assinantes`:

- com a aba do painel **aberta**;
- alguns segundos depois de **fechar** a aba.

```
SSE_ASSINANTES_PAINEL_ABERTO:
SSE_ASSINANTES_PAINEL_FECHADO:
```

Se o segundo número não voltar a zero, a função de teardown do `new Observable`
não está fechando o `EventSource`, e cada aba aberta durante a noite deixou
uma conexão viva no servidor.

## 5. A prova do `switchMap`: antes e depois

Este é o número que dá lastro à Pergunta de Verificação 3. São **duas**
medições, com o mesmo roteiro, mudando só o operador.

Roteiro, igual nos dois cenários:

1. `curl -X POST http://localhost:5080/api/v1/metricas/zerar`
2. No campo de busca do painel, digite `1003` **uma tecla por vez, com cerca
   de meio segundo entre elas**. Mais que o debounce de 300 ms, menos que os
   800 ms que o serviço demora para responder.
3. Espere dois segundos e leia
   `curl -s http://localhost:5080/api/v1/metricas`.

**Antes**, com o `mergeMap` do esqueleto ainda no lugar (faça esta medição
antes de fechar o TODO-6):

```
ANTES_RECEBIDAS:
ANTES_CONCLUIDAS:
ANTES_CANCELADAS:
```

**Depois**, com o `switchMap` no lugar:

```
DEPOIS_RECEBIDAS:
DEPOIS_CONCLUIDAS:
DEPOIS_CANCELADAS:
```

Abra também a aba **Rede** do navegador durante a segunda medição: as
requisições canceladas aparecem com status `(canceled)`. É o mesmo fato visto
de dois lugares, e ver dos dois lados é o que fecha o argumento.

---

## 6. O que a máquina prova e o que fica por sua conta

| A máquina prova | Fica por sua conta |
|---|---|
| Que os operadores certos estão no encadeamento certo | Saber explicar por que `debounceTime` vem antes de `distinctUntilChanged` |
| Que a suíte inteira está verde | Saber qual teste quebraria se você trocasse `switchMap` por `mergeMap` |
| Que o serviço contabilizou cancelamento de verdade | Saber por que cancelar a inscrição de um Observable aborta a requisição HTTP |
| Que o número de assinantes SSE volta a zero | Saber onde estaria o vazamento se a função de teardown não existisse |
| Que os números declarados são coerentes entre si | Saber o que aconteceria com 400 caminhões em vez de 12 |
