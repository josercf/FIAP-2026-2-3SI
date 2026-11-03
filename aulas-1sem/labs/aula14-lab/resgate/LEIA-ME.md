# Resgate

Cópias resolvidas das cinco funções. O mesmo código está nos slides, uma missão por slide, e no README, um passo por seção.

Use isto só depois de ler a linha `FAIL` ou `not ok` e de tentar de novo. Abrir antes da primeira tentativa queima a história de que a mesa resolveu.

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
