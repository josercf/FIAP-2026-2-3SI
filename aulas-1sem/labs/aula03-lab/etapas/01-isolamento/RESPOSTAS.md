# Etapa 1, Isolamento de processos

## Enunciado

O mesmo processo, visto de dois lugares diferentes, tem dois PIDs diferentes.
É essa duplicidade que prova que o namespace de PID está funcionando: de
dentro do container, o processo se enxerga como um dos primeiros processos de
um sistema novo; de fora, o host enxerga o PID real dele na árvore de
processos da máquina.

## Comando

Abra dois terminais.

```bash
# Terminal 1: sobe o container e mantém ele de pé, para dar tempo de olhar de fora
docker run --rm --name isolado alpine sh -c \
  'echo "PID_DENTRO=$$"; hostname; ls /proc | wc -l; sleep 300'
```

```bash
# Terminal 2: o MESMO processo, agora visto do host
docker inspect -f '{{.State.Pid}}' isolado
```

## O que registrar

| Marcador | De onde vem |
|---|---|
| `PID_DENTRO` | A saída de `echo "PID_DENTRO=$$"` no Terminal 1. Vai ser um número baixo. |
| `PID_FORA` | A saída de `docker inspect -f '{{.State.Pid}}' isolado` no Terminal 2. Vai ser um número bem mais alto, o PID real no host. |
| `HOSTNAME_DENTRO` | A saída de `hostname` no Terminal 1: o Docker gera um hostname sozinho, do tamanho do início do ID do container. |
| `MOUNTS_DENTRO` | A saída de `ls /proc \| wc -l` no Terminal 1. |

**Não use `ps aux \| grep -c .` para `PID_FORA`.** Isso conta processos do
host, não é um PID de coisa nenhuma, e o verificador espera o PID real do
processo do container visto de fora.

Depois de anotar os quatro valores, derrube o container com `Ctrl+C` no
Terminal 1 (o `--rm` já cuida da limpeza).

## Resposta

```
PID_DENTRO: PREENCHER
PID_FORA: PREENCHER
HOSTNAME_DENTRO: PREENCHER
MOUNTS_DENTRO: PREENCHER
```
