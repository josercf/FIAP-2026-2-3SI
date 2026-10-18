# Evidências, Aula 14, OAuth 2.0, OIDC, JWT e RBAC

Formulário único, preenchido à medida que você fecha cada passo.
`verificar.py` lê estes marcadores procurando `MARCADOR: valor`. Não apague o
nome do marcador, não mude a grafia, e troque `PREENCHER` pelo valor real
medido na sua máquina. Um `PREENCHER` esquecido reprova o critério
correspondente.

Três campos são conferidos contra o Keycloak que está rodando na sua
máquina, e não apenas contra a presença de texto: `TOKEN_EXPIRA_EM_S`,
`PAPEIS_NO_TOKEN` e `ISSUER_NO_TOKEN`. Número inventado reprova.

---

## Passo 1, o Keycloak no Compose

Depois de escrever o `TODO-1a`, meça quanto tempo a plataforma leva do
comando até os três containers ficarem saudáveis:

```bash
docker compose down
time docker compose up -d --wait
```

```
TEMPO_ATE_TODOS_SAUDAVEIS_S: PREENCHER
```

E o consumo de memória do provedor de identidade, que é o container mais
pesado da noite:

```bash
docker stats --no-stream --format "{{.Name}} {{.MemUsage}}"
```

```
MEMORIA_KEYCLOAK_MB: PREENCHER
```

---

## Passo 2, o fluxo PKCE pelo navegador

Rode `python3 pkce.py`, entre como `ana.cliente` e responda com o que
apareceu na tela, não com o que você imagina.

Quantos caracteres tinha o `code_verifier` gerado:

```
TAMANHO_DO_CODE_VERIFIER: PREENCHER
```

O valor de `code_challenge_method` que foi na URL de autorização:

```
CODE_CHALLENGE_METHOD: PREENCHER
```

O que veio dentro do token, lido da saída do próprio `pkce.py`:

```
TOKEN_EXPIRA_EM_S: PREENCHER
PAPEIS_NO_TOKEN: PREENCHER
ISSUER_NO_TOKEN: PREENCHER
```

E a pergunta que separa quem leu de quem copiou: o que havia em
`resource_access` no token da Ana?

```
RESOURCE_ACCESS_NO_TOKEN: PREENCHER
```

---

## Passo 3, o 401

Com o `TODO-2` preenchido e o serviço reconstruído, chame uma rota protegida
**sem token nenhum** e registre o código de status e o campo `motivo` da
resposta:

```bash
curl -i http://localhost:8080/api/v1/pedidos
```

```
CURL_SEM_TOKEN: PREENCHER
MOTIVO_DO_401: PREENCHER
```

Agora repita com um token propositalmente estragado, trocando um caractere
do meio dele. O status é o mesmo, o motivo muda:

```
MOTIVO_DO_401_COM_TOKEN_ADULTERADO: PREENCHER
```

---

## Passo 4, o issuer divergente

Antes de preencher o `TODO-1b`, use um token de verdade, obtido pelo
navegador, contra o serviço:

```bash
export TOKEN=$(python3 pkce.py --so-token)
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/pedidos
```

Registre o motivo do 401, que é a frase inteira, e os dois endereços que
aparecem nela:

```
MOTIVO_DO_ISSUER: PREENCHER
ISSUER_QUE_VEIO_NO_TOKEN: PREENCHER
ISSUER_QUE_O_SERVICO_ESPERAVA: PREENCHER
```

Em uma frase sua: por que os dois não coincidem, se é o mesmo Keycloak?

```
POR_QUE_OS_DOIS_DIFEREM: PREENCHER
```

---

## Passo 5, o 403

Com o `TODO-3` preenchido, entre como `bruno.motorista` e tente alterar o
endereço de entrega de um pedido:

```bash
export TOKEN=$(python3 pkce.py --so-token)   # entre como bruno.motorista
curl -i -X PATCH http://localhost:8080/api/v1/pedidos/PED-1042/endereco \
     -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -d '{"logradouro":"Rua Bela Cintra","numero":"495","cidade":"Sao Paulo","uf":"SP","cep":"01415-000"}'
```

```
CURL_PAPEL_ERRADO: PREENCHER
PAPEIS_QUE_O_BRUNO_TEM: PREENCHER
PAPEIS_ACEITOS_PELA_ROTA: PREENCHER
```

Em uma frase sua: por que repetir o login não resolve este caso, e resolveria
o do Passo 3?

```
POR_QUE_401_E_403_SAO_DIFERENTES: PREENCHER
```

---

## Passo 6, o mesmo papel em outra stack

Com o `TODO-4` preenchido, use **o mesmo token do Bruno** nos dois serviços,
sem fazer login de novo:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" \
     http://localhost:8080/api/v1/pedidos
curl -s -o /dev/null -w '%{http_code}\n' -X POST \
     -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -d '{"canal":"sms","destinatario":"+5511988887777","mensagem":"teste"}' \
     http://localhost:3001/api/v1/notificacoes
```

```
STATUS_NO_SERVICO_JAVA: PREENCHER
STATUS_NO_SERVICO_NODE: PREENCHER
```

De qual campo do token os **dois** serviços leram o papel? Escreva o caminho
completo:

```
DE_ONDE_OS_DOIS_LEEM_O_PAPEL: PREENCHER
```

E o que aconteceria se o serviço Node lesse de `resource_access` em vez
disso, com este mesmo token?

```
SE_O_NODE_LESSE_DE_RESOURCE_ACCESS: PREENCHER
```

---

## Passo 7, o portal

Com o `TODO-5` preenchido, `cd portal && npm run dev`, abra
http://localhost:5173 e entre como `ana.cliente`.

```
PAPEIS_QUE_O_PORTAL_MOSTROU: PREENCHER
```

Clique em "Enviar aviso de entrega" logada como Ana. O que a tela mostrou:

```
MENSAGEM_DO_403_NA_TELA: PREENCHER
```

Saia, entre como `carla.admin` e clique de novo:

```
RESULTADO_COMO_ADMIN: PREENCHER
```

Uma pergunta de projeto, e a resposta não é "sim": esconder esse botão para
quem não é ADMIN resolveria o problema de segurança?

```
ESCONDER_O_BOTAO_RESOLVERIA: PREENCHER
```

---

## Passo 8, as duas worktrees

```bash
git switch -c seguranca/backend
git switch -c seguranca/portal
git switch main
git worktree add ../agent-auth seguranca/backend
git worktree add ../agent-ui   seguranca/portal
git worktree list
```

```
WORKTREE_AUTH: PREENCHER
WORKTREE_UI: PREENCHER
```

Cole abaixo a saída literal de `git worktree list`. As duas worktrees
precisam aparecer nela:

```
SAIDA_DO_GIT_WORKTREE_LIST: PREENCHER
```

Rode a suíte de um lado e o `npm test` do outro, ao mesmo tempo, em dois
terminais. O que aconteceria se, em vez de worktree, você usasse
`git switch` no mesmo diretório com os dois processos rodando?

```
O_QUE_ACONTECERIA_COM_SWITCH: PREENCHER
```

---

## Fecho

```
USEI_O_RESGATE: PREENCHER
QUAL_RESGATE: PREENCHER
O_QUE_CUSTOU_MAIS_TEMPO: PREENCHER
```
