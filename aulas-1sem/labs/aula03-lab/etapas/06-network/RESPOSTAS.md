# Etapa 6, Network e observação

## Enunciado

Crie a rede `logitech-net`, suba os dois containers nela e prove que o
gateway resolve o coletor **pelo nome**, não por IP fixo, que é o ponto
central de uma rede bridge do Docker: o DNS interno resolve o nome do
container para o IP dele, e esse IP pode mudar a cada `docker run` sem
quebrar nada. Depois, observe o consumo de memória do coletor com
`docker stats`.

## Comando

```bash
# a partir da raiz do laboratório

docker network create logitech-net

docker run -d --name coletor --network logitech-net coletor:final
docker run -d --name gateway --network logitech-net -p 3000:3000 gateway:final

# prova de que o gateway resolve o coletor pelo NOME, não por IP
docker exec gateway node -e "require('dns').lookup('coletor', (e, addr) => console.log(addr))"

# memória do coletor, com o container em regime
docker stats coletor --no-stream --format '{{.Name}}\t{{.MemUsage}}'
```

`docker stats` devolve algo como `coletor   8.79MiB / 7.75GiB`: o número
antes da barra, na mesma unidade de MB (MiB é praticamente MB para este
propósito), é o que vai no formulário.

## O que registrar

Registre em `docs/EVIDENCIAS.md`, não aqui: `MEMORIA_COLETOR_MB`. O
verificador também confirma sozinho, no Docker da sua máquina, que a rede
`logitech-net` existe.

## Resposta

```
Valor registrado em docs/EVIDENCIAS.md: PREENCHER (sim/não)
O gateway resolveu "coletor" pelo nome: PREENCHER (sim/não)
```
