# Etapa 2, Imagem, camadas e efemeridade

## Enunciado

Rode o coletor sem escrever Dockerfile nenhum: sobre a imagem pública
`python:3.12-alpine`, com o código-fonte entrando por bind mount, exatamente
como ele já está em `servicos/coletor/`. Escreva um arquivo dentro do
container, destrua o container, e prove que o arquivo sumiu. É a camada
gravável do container que guarda tudo que ele escreve em tempo de execução, e
ela morre junto com o container.

## Comando

```bash
# a partir da raiz do laboratório

# sobe o coletor de verdade, sem Dockerfile, com bind mount do fonte
docker run -d --name coletor-etapa2 \
  -v "$(pwd)/servicos/coletor:/app:ro" -w /app \
  python:3.12-alpine python server_telemetry.py

# pega o ID real do container: é o CONTAINER_ID do formulário
docker inspect -f '{{.Id}}' coletor-etapa2

# escreve um arquivo na camada gravável (fora do bind mount, que é :ro)
docker exec coletor-etapa2 sh -c "echo evidencia > /tmp/arquivo-teste.txt"
docker exec coletor-etapa2 cat /tmp/arquivo-teste.txt

# destrói o container: a camada gravável vai junto
docker rm -f coletor-etapa2

# sobe outro container do zero, sobre a MESMA imagem, e tenta ler o mesmo caminho
docker run --rm python:3.12-alpine cat /tmp/arquivo-teste.txt
```

O último comando deve terminar com um erro do tipo `No such file or
directory`. É essa mensagem que prova a efemeridade.

## O que registrar

| Marcador | De onde vem |
|---|---|
| `CONTAINER_ID` | O ID hexadecimal completo, ou os primeiros 12 caracteres, devolvido por `docker inspect -f '{{.Id}}' coletor-etapa2`. |
| `ARQUIVO_APOS_RM` | `sumiu` ou `ausente`, conforme o erro do último comando. |

O verificador também confere, sozinho, que a imagem `python:3.12-alpine`
está presente na sua máquina (`docker image inspect`). Isso acontece
automaticamente ao rodar o `docker run` acima, sem passo extra.

## Resposta

```
CONTAINER_ID: PREENCHER

ARQUIVO_APOS_RM: PREENCHER
```
