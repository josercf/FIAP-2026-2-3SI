# Laboratório Prático - Aula 14

## Disciplina: Microservice and Web Engineering & IT Services
**Prof.º José Romualdo | FIAP Sistemas de Informação**

### Case: LogiTech Enterprise AI Platform (Fase 14, quem é você)

Hoje, qualquer pessoa que alcance a rede da LogiTech muda o endereço de
entrega de qualquer pedido. O `PATCH /api/v1/pedidos/{id}/endereco`, a mesma
rota que o agente de IA da Aula 08 chama, **não pergunta quem está
chamando**. Não é um bug de código: é uma ausência de decisão. Ninguém nunca
disse quem pode alterar endereço, e o serviço faz o que lhe pedem.

Um caminhão desviado por uma requisição de dois segundos é prejuízo com nota
fiscal. E o problema não se resolve com uma senha compartilhada entre os
serviços: senha compartilhada não diz **quem** é o usuário, só que alguém
sabia a senha. Quando vazar, e vai vazar, trocar significa reimplantar todos
os serviços ao mesmo tempo.

A resposta desta noite tem três partes:

1. um **provedor de identidade** que emite tokens assinados, o Keycloak;
2. **dois serviços em stacks diferentes** que validam a assinatura contra a
   chave pública e leem o papel do usuário **do mesmo lugar do token**;
3. um **portal** que faz o login por Authorization Code + PKCE e leva o
   token junto em cada chamada.

**Atividade em dupla**, oito passos. Um commit por passo.

---

## O que já vem pronto, e o que vocês fazem

| Vem pronto, não é tarefa | Vocês escrevem |
|---|---|
| `keycloak/realm-logitech.json`, o realm versionado com 3 papéis, 2 clients e 3 usuários | `docker-compose.yml`: `TODO-1a`, `TODO-1b`, `TODO-1c` |
| `servicos/pedidos/`, o serviço Java, com `Jwt.java` e `Json.java` | `servicos/pedidos/Seguranca.java`: `TODO-2` e `TODO-3` |
| `servicos/notificacoes/`, o serviço Node | `servicos/notificacoes/seguranca.mjs`: `TODO-4` |
| `portal/`, o Portal React da Aula 10, com a tela de sessão | `portal/src/auth/pkce.ts`: `TODO-5` |
| `pkce.py`, o fluxo à mão do Passo 2 | As duas worktrees: `TODO-6` |
| As três suítes de teste, que rodam offline | `docs/EVIDENCIAS.md`, com os valores medidos por vocês |
| `verificar.py`, a autoavaliação | Um commit por passo concluído |
| `resgate/`, a rede de segurança | |

Leia `servicos/LEIA-ME.md`: ele declara as três diferenças entre estes
serviços congelados e os que vocês escreveram nas Aulas 05 e 06.

---

## O contrato desta noite (ADR-009)

Não é sugestão. A Aula 16 testa exatamente isto.

### Provedor de identidade

| Item | Valor |
|---|---|
| Container | `keycloak`, imagem `quay.io/keycloak/keycloak:26.0` |
| Porta | **8090** (a 8080 é do `pedidos` desde a ADR-006) |
| Modo | `start-dev --import-realm`, realm de arquivo versionado |
| Realm | `logitech`, console em http://localhost:8090 com usuário `admin` |

### Clients, papéis e usuários

Os dois clients são **públicos** e usam Authorization Code + **PKCE**. Os
backends **não são clients**: são *resource servers*, não guardam segredo e
não iniciam fluxo nenhum. Só validam assinatura.

| Usuário | Senha | Papel |
|---|---|---|
| `ana.cliente` | `logitech` | `CLIENTE` |
| `bruno.motorista` | `logitech` | `MOTORISTA` |
| `carla.admin` | `logitech` | `ADMIN` |

> Senha fraca, igual para os três e escrita em arquivo versionado. Isso é
> **ambiente de laboratório** e nada disso vai para produção. Está dito com
> todas as letras porque credencial de treinamento que parece de produção
> ensina a coisa errada.

O papel viaja em **`realm_access.roles`**, e é de lá que os dois serviços
leem. Este é o ponto central da noite.

### Que rota exige o quê

```
pedidos       GET   /health                          aberta
              GET   /api/v1/pedidos                  CLIENTE, MOTORISTA ou ADMIN
              GET   /api/v1/pedidos/{id}             qualquer papel autenticado
              POST  /api/v1/pedidos                  CLIENTE ou ADMIN
              PATCH /api/v1/pedidos/{id}/endereco    CLIENTE ou ADMIN
              GET   /api/v1/pedidos/{id}/status      qualquer papel autenticado

notificacoes  GET   /health                          aberta
              POST  /api/v1/notificacoes             ADMIN
```

**`GET /health` fica aberta nos dois.** Não é descuido: o `healthcheck` do
Compose, que a Aula 07 ensinou, não carrega token. Protegê-la deixa os dois
containers `unhealthy` para sempre, e o `depends_on` da plataforma inteira
para de funcionar.

Token ausente devolve **401**. Token válido sem o papel devolve **403**.

### O interruptor

Os dois serviços leem `LOGITECH_AUTH_ATIVA`, padrão **`false`**. Com ela
desligada, eles se comportam como nas Aulas 05 a 12, e os laboratórios
anteriores continuam passando. **O Compose desta aula liga**, e o
`verificar.py` exige ligada. Não é porta dos fundos escondida: aparece no
slide, está aqui, e o próprio `/health` responde qual é o valor.

---

## Pré-requisitos

- Fork do repositório do laboratório (nunca clone direto).
- GitHub Codespaces, ou Docker e Node 22 na máquina.
- Uns 900 MB de memória livre para os três containers. O Keycloak sozinho
  usa quase 500 MB: pare o Ollama antes de começar (`pkill ollama`).
- Ter feito, ou lido, a Aula 07: o Compose de hoje usa `healthcheck`,
  `depends_on` com condição e a rede `logitech-net`.

```bash
docker network create logitech-net    # só na primeira vez
cp .env.exemplo .env                  # e troque a senha do admin
cd portal && cp .env.exemplo .env && npm install && cd ..
```

---

## Os oito passos

Cada passo termina com um commit. `python3 verificar.py` roda a qualquer
momento e diz qual critério está faltando e por quê.

### Passo 1, `TODO-1a`: o Keycloak no Compose

Escreva o serviço `keycloak` no `docker-compose.yml`. O arquivo diz o que
cada linha precisa ter e por quê. Depois:

```bash
docker compose up -d --build
docker compose ps
docker compose logs keycloak | grep -i "imported"
```

A linha `Realm 'logitech' imported` é a prova de que o realm veio do arquivo,
e não de vinte telas de configuração.

Abra http://localhost:8090, entre como `admin` e navegue até Users. Os três
usuários estão lá porque o JSON os semeou.

Registre `TEMPO_ATE_TODOS_SAUDAVEIS_S` e `MEMORIA_KEYCLOAK_MB`.

```bash
python3 verificar.py --criterio 1
```

### Passo 2, o fluxo PKCE pelo navegador

**Antes de qualquer `curl` com token colado.** Esta ordem não é gosto: quem
começa pelo `curl` decora um comando; quem começa pelo navegador entende por
que o comando funciona.

```bash
python3 pkce.py
```

O programa gera o `code_verifier` e o `code_challenge`, imprime os dois,
imprime a URL de autorização inteira e abre o navegador. Entre como
`ana.cliente`, senha `logitech`. Ele captura o retorno, troca o código pelo
token e imprime o token decodificado em três partes.

Leia a saída inteira antes de continuar. Preencha em `docs/EVIDENCIAS.md`:
`TAMANHO_DO_CODE_VERIFIER`, `CODE_CHALLENGE_METHOD`, `TOKEN_EXPIRA_EM_S`,
`PAPEIS_NO_TOKEN`, `ISSUER_NO_TOKEN` e `RESOURCE_ACCESS_NO_TOKEN`.

> O `directAccessGrants` está **desligado** nos dois clients do realm. Ou
> seja: não existe atalho de usuário e senha por `curl`. O único caminho para
> um token é o fluxo pelo navegador. Foi decidido assim de propósito.

### Passo 3, `TODO-2`: o 401

Em `servicos/pedidos/Seguranca.java`, preencha `TODO-2a`, `TODO-2b` e
`TODO-2c`. Confira sem subir nada:

```bash
docker compose up -d --build pedidos
docker compose exec pedidos java -cp /app/classes TestesSeguranca
```

Depois, na mão:

```bash
curl -i http://localhost:8080/api/v1/pedidos
curl -i http://localhost:8080/health          # esta continua 200, sem token
```

Registre `CURL_SEM_TOKEN`, `MOTIVO_DO_401` e
`MOTIVO_DO_401_COM_TOKEN_ADULTERADO`.

```bash
python3 verificar.py --criterio 3
```

### Passo 4, `TODO-1b`: o issuer que não coincide

Agora use um token de verdade:

```bash
export TOKEN=$(python3 pkce.py --so-token)
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/pedidos
```

**Vai dar 401.** O token é perfeitamente válido, a assinatura confere, e
mesmo assim o serviço recusa. Leia o campo `motivo`: o `iss` que veio dentro
do token é `http://localhost:8090/realms/logitech`, e o serviço só confia em
`http://keycloak:8090/realms/logitech`.

É o mesmo Keycloak. O que muda é quem está falando com ele: o **seu
navegador** o alcança por `localhost:8090`, e o **container** o alcança por
`keycloak:8090`. O Keycloak escreve no token o endereço pelo qual foi
chamado.

Registre `MOTIVO_DO_ISSUER`, `ISSUER_QUE_VEIO_NO_TOKEN`,
`ISSUER_QUE_O_SERVICO_ESPERAVA` e `POR_QUE_OS_DOIS_DIFEREM`. Só então
preencha o `TODO-1b`, aceitando os dois endereços, e:

```bash
docker compose up -d pedidos notificacoes
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/pedidos
```

### Passo 5, `TODO-3`: o 403

Ainda em `Seguranca.java`, preencha `TODO-3a` (a tabela de regras), `TODO-3b`
(os papéis vindos de `realm_access.roles`) e `TODO-3c` (a decisão).

```bash
docker compose up -d --build pedidos
docker compose exec pedidos java -cp /app/classes TestesSeguranca   # 26 de 26
```

Entre como `bruno.motorista` e tente alterar um endereço de entrega. É a dor
de negócio da aula, agora resolvida:

```bash
export TOKEN=$(python3 pkce.py --so-token)     # entre como bruno.motorista
curl -i -X PATCH http://localhost:8080/api/v1/pedidos/PED-1042/endereco \
     -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -d '{"logradouro":"Rua Bela Cintra","numero":"495","cidade":"Sao Paulo","uf":"SP","cep":"01415-000"}'
```

Registre `CURL_PAPEL_ERRADO`, `PAPEIS_QUE_O_BRUNO_TEM`,
`PAPEIS_ACEITOS_PELA_ROTA` e `POR_QUE_401_E_403_SAO_DIFERENTES`.

```bash
python3 verificar.py --criterio 4
```

### Passo 6, `TODO-4`: o mesmo papel, em outra stack

Em `servicos/notificacoes/seguranca.mjs`, preencha `TODO-4a` e `TODO-4b`.

```bash
docker compose up -d --build notificacoes
docker compose exec notificacoes node --test seguranca.test.mjs   # 14 de 14
```

Agora o teste que vale a noite: **o mesmo token do Bruno**, sem login novo,
nos dois serviços. 200 no Java, 403 no Node, e a razão é o papel, não a
linguagem.

Registre `STATUS_NO_SERVICO_JAVA`, `STATUS_NO_SERVICO_NODE`,
`DE_ONDE_OS_DOIS_LEEM_O_PAPEL` e `SE_O_NODE_LESSE_DE_RESOURCE_ACCESS`.

```bash
python3 verificar.py --criterio 5
```

### Passo 7, `TODO-5`: o portal faz o mesmo, em TypeScript

Em `portal/src/auth/pkce.ts`, preencha `TODO-5a` a `TODO-5d`. São as quatro
peças que você viu o `pkce.py` fazer no Passo 2.

```bash
cd portal
npm test            # 13 de 13, e um deles usa o vetor da RFC 7636
npm run dev
```

Abra http://localhost:5173, entre como `ana.cliente` e depois como
`carla.admin`. Clique em "Enviar aviso de entrega" com os dois.

Registre `PAPEIS_QUE_O_PORTAL_MOSTROU`, `MENSAGEM_DO_403_NA_TELA`,
`RESULTADO_COMO_ADMIN` e `ESCONDER_O_BOTAO_RESOLVERIA`.

### Passo 8, `TODO-6`: duas worktrees, dois trabalhos ao mesmo tempo

Retomando a Aula 08, agora com um propósito diferente: lá as worktrees
separavam dois agentes; aqui separam **duas naturezas de trabalho** que
avançam na mesma noite, segurança de backend e interface.

```bash
git switch -c seguranca/backend
git switch -c seguranca/portal
git switch main

git worktree add ../agent-auth seguranca/backend
git worktree add ../agent-ui   seguranca/portal
git worktree list
```

E use as duas de verdade, em dois terminais, ao mesmo tempo:

```bash
# terminal A, em ../agent-auth
docker compose exec pedidos java -cp /app/classes TestesSeguranca
# terminal B, em ../agent-ui
cd portal && npm test
```

> As worktrees moram **fora** do repositório, um nível acima. Nunca as crie
> dentro da pasta do laboratório: virariam arquivos não rastreados do próprio
> repositório e o `git status` ficaria impossível de ler.
> Para desfazer: `git worktree remove ../agent-auth`.

Registre `WORKTREE_AUTH`, `WORKTREE_UI`, `SAIDA_DO_GIT_WORKTREE_LIST` e
`O_QUE_ACONTECERIA_COM_SWITCH`.

```bash
python3 verificar.py
```

---

## Critérios de aceitação

| # | Critério | O que a máquina prova |
|---|---|---|
| 1 | `TODO-1`: Keycloak no Compose, realm de arquivo | Lê o `docker compose config`: imagem, `--import-realm`, volume do realm, porta 8090, `healthcheck`, `KC_HEALTH_ENABLED` e `depends_on` com `service_healthy` nos dois serviços. Confere os 3 papéis e os 3 usuários no JSON |
| 2 | `/health` aberta e autenticação ligada | Chama `GET /health` **sem token** nos dois serviços e exige 200 com `autenticacaoAtiva: true` |
| 3 | `TODO-2`: sem token, 401 | Chama duas rotas protegidas sem cabeçalho. Reprova especificamente quem devolve 403 no lugar |
| 4 | `TODO-3`: 200 e 403 conforme o papel | Obtém três tokens por PKCE de verdade e roda seis casos: lista, cria, altera endereço e consulta status, com CLIENTE e MOTORISTA |
| 5 | `TODO-4`: o mesmo papel, do mesmo lugar, em outra stack | O mesmo token de MOTORISTA: 200 no serviço Java e 403 no serviço Node |
| 6 | `TODO-5` e `TODO-6`: evidências e worktrees | Compara `TOKEN_EXPIRA_EM_S` com o `exp - iat` do token recém-emitido, confere `PAPEIS_NO_TOKEN`, `ISSUER_NO_TOKEN`, o 401 e o 403 registrados, e as duas worktrees em `git worktree list` |

As três suítes de teste rodam separadamente e apontam o `TODO` que falta:

```bash
docker compose exec pedidos      java -cp /app/classes TestesSeguranca   # 26 testes
docker compose exec notificacoes node --test seguranca.test.mjs          # 14 testes
cd portal && npm test                                                    # 13 testes
python3 -m pytest -q                                                     # 23 testes
```

O último é a suíte do **próprio verificador**: ela prova que cada critério
reprova o esqueleto e aprova o resgate, sem depender de container no ar. Um
verificador que aprova tudo é pior do que nenhum, porque dá confiança falsa.

## Ordem de corte, se o tempo apertar

Combinada de antemão para ninguém ter de decidir às 22h30:

1. o **Passo 8**, as worktrees, vira tarefa de casa;
2. o **Passo 7**, o portal, também: o `npm test` do TODO-5 prova o fluxo sem
   a tela;
3. o **Passo 6** encolhe para rodar só a suíte do Node, sem o `curl` cruzado.

Os passos 2, 3, 4 e 5 **nunca** saem. O fluxo pelo navegador, o 401, o issuer
divergente e o 403 são a aula.

## Como entregar

1. Um commit por passo, no fork da dupla.
2. `docs/EVIDENCIAS.md` preenchido, sem nenhum `PREENCHER`.
3. `python3 verificar.py` com os 6 critérios cumpridos.
4. A URL do fork no formulário de entrega da aula.

## Se algo der errado

| Sintoma | Causa provável |
|---|---|
| `network logitech-net declared as external, but could not be found` | `docker network create logitech-net` |
| O `keycloak` fica `unhealthy` para sempre | Faltou `KC_HEALTH_ENABLED: "true"`: sem ela a porta 9000 não serve `/health/ready` |
| `Realm 'logitech' imported` não aparece no log | O realm já existia de uma subida anterior. `docker compose down -v` e suba de novo |
| 401 com `issuer ... nao esta na lista de confiaveis` | É o Passo 4. Leia antes de consertar |
| 401 com `kid ... nao existe no JWKS` | O Keycloak foi recriado e girou a chave. Reinicie o serviço de backend |
| 403 em tudo, com token válido | Os papéis estão sendo lidos do lugar errado. Confira o `TODO-3b` e o `TODO-4a` |
| O portal mostra erro de CORS ao chamar com token | O `Access-Control-Allow-Headers` precisa incluir `Authorization`. Já está no `Pedidos.java`; confira se a origem do portal está em `LOGITECH_CORS_ORIGINS` |
| `A porta 5199 ja esta ocupada` | Um `pkce.py` anterior ficou esperando. `lsof -ti tcp:5199 \| xargs kill` |

## Avaliação

| Dimensão | O que se observa |
|---|---|
| Funcionamento | Os 6 critérios do `verificar.py`, e as três suítes verdes |
| Contrato | Papel lido de `realm_access.roles` nos dois serviços; `/health` aberta; 401 e 403 nos lugares certos |
| Reprodutibilidade | Realm importado de arquivo; `docker compose up -d --wait` sobe tudo do zero |
| Evidências | Números medidos na máquina da dupla, não copiados; as respostas escritas em `docs/EVIDENCIAS.md` |
| Processo | Um commit por passo, mensagem que diz o que mudou, uso do resgate declarado |

## Referências

- `ADR-006` e `ADR-008`: o contrato da plataforma que vocês estão protegendo.
- `ADR-009`: o contrato de segurança desta noite, e o motivo de cada decisão.
- RFC 6749 (OAuth 2.0), RFC 7636 (PKCE), RFC 7519 (JWT), RFC 7517 (JWK).
- OpenID Connect Core 1.0.
- Documentação do Keycloak 26, seção *Configuring Keycloak* e *Server Guide*.
