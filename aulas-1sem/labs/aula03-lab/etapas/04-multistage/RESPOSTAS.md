# Etapa 4, Multi-stage

## Enunciado

Meça o tamanho da imagem ingênua, escreva `Dockerfile.coletor` e
`Dockerfile.gateway` de novo, agora em multi-stage (estágio `builder` +
estágio `runtime`, base alpine no estágio final, usuário não-root criado com
UID acima de 10000), meça de novo e calcule a redução. A baseline não é
escolhida por você: é sempre `baseline/Dockerfile.<servico>.ingenuo`, para o
percentual significar a mesma coisa para a turma inteira.

## Comando

```bash
# a partir da raiz do laboratório

# 1. builda a baseline ingênua e mede
docker build -f baseline/Dockerfile.coletor.ingenuo -t coletor:ingenuo .
docker build -f baseline/Dockerfile.gateway.ingenuo -t gateway:ingenuo .
docker image ls coletor:ingenuo --format '{{.Repository}}:{{.Tag}}   {{.Size}}'
docker image ls gateway:ingenuo --format '{{.Repository}}:{{.Tag}}   {{.Size}}'

# 2. escreva Dockerfile.coletor e Dockerfile.gateway multi-stage na raiz
#    (dois estágios FROM cada um, USER não-root no estágio final)

# 3. builda as versões finais e mede de novo
docker build -f Dockerfile.coletor -t coletor:final .
docker build -f Dockerfile.gateway -t gateway:final .
docker image ls coletor:final --format '{{.Repository}}:{{.Tag}}   {{.Size}}'
docker image ls gateway:final --format '{{.Repository}}:{{.Tag}}   {{.Size}}'
```

**`docker image ls` aceita só um `REPOSITORY:TAG` por chamada**, não uma
lista: rode um comando por imagem, como acima. `docker image ls` mostra o
tamanho em MB (ou GB, para as ingênuas: converta para MB antes de
registrar). O `verificar.py` faz o mesmo build de novo por conta própria,
então o Dockerfile precisa continuar buildando quando ele rodar, não só na
sua máquina agora.

## O que registrar

Registre em `docs/EVIDENCIAS.md`, não aqui: `TAMANHO_COLETOR_INGENUO_MB`,
`TAMANHO_COLETOR_FINAL_MB`, `REDUCAO_COLETOR`, `TAMANHO_GATEWAY_INGENUO_MB`,
`TAMANHO_GATEWAY_FINAL_MB`, `REDUCAO_GATEWAY`.

Redução em percentual:

```
reducao = (1 - tamanho_final / tamanho_ingenuo) * 100
```

O mínimo exigido é 80% para os dois serviços. Se a sua redução ficar abaixo
disso, confira se o estágio final não copiou nada do `builder` sem precisar
(compilador, cache de instalação, `.git`).

## Resposta

```
Valores registrados em docs/EVIDENCIAS.md: PREENCHER (sim/não)
```
