# Etapa 5, Volumes

## Enunciado

Crie o volume nomeado `logitech-telemetria`, suba o coletor com esse volume
montado em `/dados`, mande telemetria de verdade, destrua o container e
suba outro do zero apontando para o mesmo volume. Se as linhas continuarem
lá, o dado sobreviveu ao container que o escreveu, o que a camada gravável
sozinha nunca conseguiria.

## Comando

```bash
# a partir da raiz do laboratório

docker volume create logitech-telemetria

# sobe o coletor buildado na etapa 4 (troque a tag se usou outro nome)
docker run -d --name coletor-vol \
  -v logitech-telemetria:/dados \
  -p 8081:8081/udp \
  coletor:final

# manda telemetria de verdade por UDP
python3 -c "
import socket, json
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for i in range(3):
    msg = json.dumps({'placa': 'LOG000%d' % i, 'lat': -23.5, 'lng': -46.6}).encode()
    s.sendto(msg, ('127.0.0.1', 8081))
"

docker exec coletor-vol wc -l /dados/telemetria.jsonl

# destrói o container
docker rm -f coletor-vol

# sobe outro container, do zero, com o MESMO volume
docker run --rm -v logitech-telemetria:/dados alpine:3.20 wc -l /dados/telemetria.jsonl
```

O número de linhas do último comando precisa bater com o do
`docker exec coletor-vol wc -l ...` de antes da remoção: é essa igualdade
que prova a persistência.

## O que registrar

Registre em `docs/EVIDENCIAS.md`, não aqui: `LINHAS_APOS_RM`, o número de
linhas que sobreviveram, lido do último comando acima. O verificador também
confirma sozinho, no Docker da sua máquina, que o volume
`logitech-telemetria` existe.

## Resposta

```
Valor registrado em docs/EVIDENCIAS.md: PREENCHER (sim/não)
```
