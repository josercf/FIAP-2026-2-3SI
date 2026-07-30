# Observações de tráfego - Aula 02

**Dupla:** (nomes dos dois integrantes)
**Data:** (dd/mm/2026)

Preencha as três observações abaixo com **números medidos por vocês**.
Resposta sem número não conta como resposta.

---

## O-01 - Headers da resposta

**Pergunta:** quantos headers a resposta de `GET /api/v1/posicoes` traz, e quais são?

```bash
curl -i http://localhost:3000/api/v1/posicoes
```

- Quantidade de headers: `___`
- Lista:
  - `___`
  - `___`
- Status devolvido: `___`

---

## O-02 - Tempo de conexão e de resposta

**Pergunta:** quantos milissegundos até a conexão TCP ficar pronta, e quantos até a resposta completa?

```bash
curl -o /dev/null -s -w "conexao: %{time_connect}s total: %{time_total}s\n" \
  http://localhost:3000/api/v1/posicoes
```

- `time_connect`: `___` s
- `time_total`: `___` s
- Diferença entre os dois, em milissegundos: `___` ms
- O que essa diferença representa: `___`

---

## O-03 - Cadência do stream SSE

**Pergunta:** qual o intervalo medido entre dois eventos consecutivos do stream?

```bash
curl -N http://localhost:3000/api/v1/eventos
```

- `id` do primeiro evento observado: `___`
- `id` do segundo evento observado: `___`
- Intervalo medido entre eles: `___` s
- Bate com o intervalo configurado no simulador de frota? `___`

---

## Experimento obrigatório: a linha em branco

Apaguem a linha em branco no fim de cada evento (o `\n\n`), reiniciem o
servidor e observem novamente com `curl -N` e com o painel aberto no navegador.

- O que o `curl -N` continuou mostrando: `___`
- O que o painel do navegador passou a mostrar: `___`
- Por quê: `___`

Devolvam o `\n\n` ao lugar antes de abrir o Pull Request.
