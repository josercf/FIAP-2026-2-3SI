# Etapa 3, Dockerfile e build

## Enunciado

Escreva `Dockerfile.coletor` do zero, na **raiz do laboratório**
(`aula03-lab/`, não dentro de `baseline/` nem de `resgate/`). Um único
estágio já basta para esta etapa: o multi-stage é o assunto da etapa 4. O
que importa aqui é a mecânica do build: `FROM`, `WORKDIR`, `COPY`, `CMD`, e o
Dockerfile buildando sem erro.

Use como referência a estrutura do `baseline/Dockerfile.coletor.ingenuo`
(sem copiar ele: é a baseline ingênua, o ponto de comparação da etapa 4, não
a resposta desta etapa) e o comentário de `servicos/coletor/server_telemetry.py`
sobre o caminho de dados: o padrão do código é relativo,
`dados/telemetria.jsonl`; é o Dockerfile quem fixa o caminho absoluto dentro
do container, com `ENV LOGITECH_DADOS=/dados/telemetria.jsonl`.

## Comando

```bash
# a partir da raiz do laboratório
docker build -f Dockerfile.coletor -t verificar-coletor:etapa3 .
docker run --rm verificar-coletor:etapa3 python -c "print('build ok')"
```

O verificador roda esse mesmo `docker build`, com um timeout de 5 minutos,
para confirmar que o Dockerfile builda de verdade, não só que o arquivo
existe.

## O que registrar

Esta etapa não tem marcador numérico: não há campo para preencher em
`docs/EVIDENCIAS.md`. O `verificar.py` confirma sozinho que
`Dockerfile.coletor` existe na raiz e builda sem erro.

Se você travou aqui e precisou usar o Dockerfile de `resgate/`, registre isso
em `docs/EVIDENCIAS.md`, no campo `USEI_O_RESGATE`.

## Resposta

```
Build executado com sucesso: PREENCHER (sim/não)
```
