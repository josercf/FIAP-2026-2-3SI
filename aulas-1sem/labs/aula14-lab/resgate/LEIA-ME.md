# Resgate

Cópias resolvidas das cinco missões abertas. A orquestração HTTP já vem pronta no kit; aqui estão só as funções que o verificador cobra.

Use isto depois de travar, não no lugar da primeira tentativa.

```bash
cp resgate/validar.js elenco/validar.js
cp resgate/ranking.py motor-ranking/ranking.py
cp resgate/ciclo.py partidas/ciclo.py
cp resgate/serie.py partidas/serie.py
cp resgate/agregar.js placar/agregar.js
python3 verificar.py
```

Se o Compose já estiver no ar, recrie os serviços que você substituiu:

```bash
docker compose up -d --build elenco motor-ranking partidas placar
python3 scripts/boss.py
```
