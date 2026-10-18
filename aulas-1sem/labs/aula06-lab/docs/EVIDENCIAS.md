# Evidências, Aula 06, Strategy, Adapter e Decorator

Formulário único, preenchido à medida que você fecha cada lacuna.
`verificar.py --criterio 8` lê estes marcadores procurando `MARCADOR: valor`.
Não apague o nome do marcador, não mude a grafia, e troque `PREENCHER` pelo
valor que a sua máquina devolveu.

Os quatro primeiros marcadores são conferidos contra o que o seu próprio
código calcula: número inventado aqui não passa, porque o verificador executa
a estratégia e compara. Preencher sem ter rodado engana a correção, não o
`verificar.py`.

---

## 1. A rota de referência do laboratório

Todos os valores desta seção saem da mesma cotação: origem `SAO`, destino
`LDB` (500 km), carga de `100` kg.

Com o serviço de frete no ar (`uvicorn app.main:app --port 8000`, a partir de
`servicos/frete`):

```bash
curl -s -X POST http://localhost:8000/api/v1/frete/cotacao \
  -H 'content-type: application/json' \
  -d '{"origem":"SAO","destino":"LDB","pesoKg":100,"modalidade":"expresso"}'

curl -s -X POST http://localhost:8000/api/v1/frete/cotacao \
  -H 'content-type: application/json' \
  -d '{"origem":"SAO","destino":"LDB","pesoKg":100,"modalidade":"economico"}'
```

Copie os campos `valor` e `prazoDias` de cada resposta:

```
VALOR_EXPRESSO_500KM: PREENCHER
PRAZO_EXPRESSO_500KM: PREENCHER
VALOR_ECONOMICO_500KM: PREENCHER
PRAZO_ECONOMICO_500KM: PREENCHER
```

---

## 2. A modalidade nova, acrescentada sem tocar na rota

Este é o critério que prova o Open/Closed. Acrescente uma quarta modalidade
de frete (por exemplo `refrigerado`, `carga_perigosa` ou a campanha comercial
que você quiser), registre-a e cote a mesma rota de referência.

Depois, rode `git diff --name-only` e cole a lista de arquivos que a mudança
tocou. Se `app/main.py` aparecer nessa lista, o critério reprova: era
exatamente isso que o Strategy tinha que evitar.

```
MODALIDADE_NOVA: PREENCHER
VALOR_MODALIDADE_NOVA_500KM: PREENCHER
ARQUIVOS_TOCADOS_PELA_MODALIDADE_NOVA: PREENCHER
```

Exemplo de preenchimento do último marcador, tudo em uma linha:
`servicos/frete/app/estrategias.py, servicos/frete/app/registro.py`

---

## 3. O log da retentativa empilhada

Rode a prova do Decorator empilhado e cole, entre os dois marcadores abaixo,
as quatro linhas de log que ela produz:

```bash
cd servicos/notificacoes
npx vitest run tests/empilhamento.test.ts --reporter=verbose
```

Se preferir ver o log com os seus próprios olhos em vez de confiar no teste,
suba o serviço (`npm run dev`) e mande uma notificação para um destinatário
de e-mail inválido: o `ComLog` registra a falha e o `ComRetentativa` repete.

A sequência esperada é `tentativa`, `falha`, `tentativa`, `sucesso`, nessa
ordem. O verificador lê a primeira palavra de cada linha.

```
LOG_DA_RETENTATIVA_INICIO
PREENCHER
LOG_DA_RETENTATIVA_FIM
```

---

## 4. As duas suítes de teste

Números lidos da saída dos comandos, para o seu próprio controle. O
verificador roda as duas suítes por conta própria no critério 7; estes
marcadores existem para você registrar o que viu.

```bash
python3 -m pytest                      # da raiz do laboratório
cd servicos/notificacoes && npx vitest run
```

```
TESTES_PYTEST: PREENCHER
TESTES_VITEST: PREENCHER
```

---

## 5. O Adapter em funcionamento (opcional, sem checagem de máquina)

Com o rastreamento da parceira no ar
(`python3 servicos/parceira-rastreio/servidor.py`) e o serviço de
notificações rodando:

```bash
curl -s http://localhost:9090/consulta?objeto=BR9912345   # formato da parceira
curl -s http://localhost:3001/api/v1/rastreio/BR9912345   # formato da LogiTech
```

Cole o `status` traduzido que a segunda chamada devolveu:

```
STATUS_ADAPTADO: PREENCHER
```

---

## O que a máquina prova, e o que fica por sua conta

| Marcador | Verificado por máquina | Declarado por você |
|---|---|---|
| `VALOR_*` e `PRAZO_*` | Sim: o verificador executa a sua estratégia e compara com o valor registrado | - |
| `MODALIDADE_NOVA` | Sim: precisa estar no registro e não pode ser uma das três originais | - |
| `VALOR_MODALIDADE_NOVA_500KM` | Sim: comparado com o que a sua estratégia devolve | - |
| `ARQUIVOS_TOCADOS_PELA_MODALIDADE_NOVA` | Parcial: o verificador recusa a presença de `main.py` e confere que a rota não cita modalidade | Que a lista corresponde ao `git diff` real |
| `LOG_DA_RETENTATIVA` | Parcial: a ordem das quatro linhas é conferida | Que o log foi copiado de uma execução sua |
| `TESTES_PYTEST` e `TESTES_VITEST` | O verificador roda as duas suítes sozinho no critério 7 | Os números que você anotou |
| `STATUS_ADAPTADO` | Não | Sim, é registro de execução |
