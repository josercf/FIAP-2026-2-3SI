# `resgate/`: rede de segurança, não atalho

Cada arquivo aqui é a versão **completa** de uma lacuna do laboratório.

Use quando travar de verdade, e não para pular etapa. O laboratório tem oito
passos e cada um depende do anterior: ficar parado no `TODO-2` até as 22h30
custa os passos 5 a 8 inteiros, e são eles que fecham a história da noite.

Quando usar:

1. copie o arquivo por cima do original;
2. **leia o que copiou** e compare com o que você tinha escrito;
3. registre `USEI_O_RESGATE: sim` e `QUAL_RESGATE` em `docs/EVIDENCIAS.md`;
4. siga para o passo seguinte.

O critério não é reprovado por usar o resgate. É reprovado por não registrar
que usou: o professor precisa saber onde a turma travou para ajustar a
próxima aula.

| Arquivo | Substitui | Lacunas |
|---|---|---|
| `docker-compose.yml` | `docker-compose.yml` | `TODO-1a`, `TODO-1b`, `TODO-1c` |
| `pedidos/Seguranca.java` | `servicos/pedidos/Seguranca.java` | `TODO-2`, `TODO-3` |
| `notificacoes/seguranca.mjs` | `servicos/notificacoes/seguranca.mjs` | `TODO-4` |
| `portal/pkce.ts` | `portal/src/auth/pkce.ts` | `TODO-5` |

```bash
cp resgate/docker-compose.yml            docker-compose.yml
cp resgate/pedidos/Seguranca.java        servicos/pedidos/Seguranca.java
cp resgate/notificacoes/seguranca.mjs    servicos/notificacoes/seguranca.mjs
cp resgate/portal/pkce.ts                portal/src/auth/pkce.ts

docker compose up -d --build
```

Não há resgate para o `TODO-6`, as worktrees: são quatro comandos de `git`, e
o README traz os quatro.
