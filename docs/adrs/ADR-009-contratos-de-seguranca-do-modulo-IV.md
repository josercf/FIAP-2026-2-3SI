# ADR-009: Contratos de segurança da plataforma no Módulo IV

- **Data:** 2026-07-31
- **Status:** Aceita
- **Decisores:** Prof. José Romualdo da Costa Filho

## Contexto

O Módulo IV não acrescenta serviços de negócio: ele **muda o comportamento dos
doze que já existem**. A Aula 14 põe autenticação na frente de rotas que hoje
respondem a qualquer um, a Aula 15 endurece o AI Gateway da Aula 07 e varre as
imagens construídas desde a Aula 03, e a Aula 16 sobe tudo junto e ensaia a
banca da Global Solution.

Isso cria um risco diferente do que a `ADR-006` e a `ADR-008` trataram. Lá o
perigo era o nome do serviço não casar. Aqui é pior: **se cada aula escolher o
seu próprio nome de papel, o seu próprio lugar para o papel dentro do token ou
a sua própria regra de qual rota exige o quê, o aluno termina o semestre com
uma plataforma que não autentica de ponta a ponta** e a Aula 16 vira noite de
depuração de token, não de integração.

Existe ainda uma assimetria a resolver: os laboratórios das Aulas 05 a 12 foram
escritos **sem** autenticação. Ligar segurança agora não pode invalidar o que o
aluno já entregou.

## Decisão

Fixar o contrato de segurança antes de escrever as três aulas.

### 1. O provedor de identidade

| Item | Valor |
|---|---|
| Container | `keycloak` |
| Imagem | `quay.io/keycloak/keycloak:26.0` |
| Porta | **8090** no host e na rede |
| Modo | `start-dev` com realm **importado de arquivo**, nunca configurado pela interface |
| Realm | `logitech` |
| Console | `http://localhost:8090`, usuário `admin` |

A porta 8090 existe porque a 8080 é do `pedidos` desde a `ADR-006`. Keycloak em
`start-dev` com `--import-realm` é decisão pedagógica: configurar realm clicando
em vinte telas não é reproduzível, não entra no Git e não sobrevive a um
`compose down -v`. O realm é um JSON versionado no repositório.

### 2. Clients

| Client | Tipo | Quem usa | Fluxo |
|---|---|---|---|
| `logitech-portal` | público | Portal React, porta 5173 | Authorization Code + **PKCE** |
| `logitech-painel-admin` | público | Painel Angular, porta 4200 | Authorization Code + **PKCE** |

Os backends **não são clients**: eles são *resource servers*. Não guardam
segredo, não iniciam fluxo, apenas validam a assinatura do token pelo JWKS. É o
que a pergunta de verificação 1 da Aula 14 cobra, e o motivo de nenhum serviço
de backend aparecer nesta tabela.

### 3. Papéis e onde eles moram no token

Três **realm roles**: `ADMIN`, `MOTORISTA`, `CLIENTE`.

O papel viaja em `realm_access.roles`, e é **daí** que todo serviço lê. Fixar
isso é o ponto central desta ADR: metade dos exemplos da internet lê de
`resource_access.<client>.roles`, e um serviço lendo de um lugar e outro do
outro produz autorização que funciona no Java e falha no Node, com o mesmo token.

Usuários semeados no realm importado, para a aula ter com o que trabalhar:

| Usuário | Senha | Papéis |
|---|---|---|
| `ana.cliente` | `logitech` | `CLIENTE` |
| `bruno.motorista` | `logitech` | `MOTORISTA` |
| `carla.admin` | `logitech` | `ADMIN` |

Senha fraca e igual para os três é deliberado, é ambiente de laboratório, e o
README diz isso com todas as letras. Credencial de laboratório que parece de
produção ensina a coisa errada.

### 4. Que rota passa a exigir o quê

Contrato mínimo, verificável, que a Aula 14 implementa e a Aula 16 testa:

```
pedidos      GET   /health                          aberta
             GET   /api/v1/pedidos                  CLIENTE, MOTORISTA ou ADMIN
             POST  /api/v1/pedidos                  CLIENTE ou ADMIN
             PATCH /api/v1/pedidos/{id}/endereco    CLIENTE ou ADMIN
             GET   /api/v1/pedidos/{id}/status      qualquer papel autenticado

faturamento  GET   /health                          aberta
             POST  /api/v1/faturas                  ADMIN
             GET   /api/v1/faturas/{pedidoId}       ADMIN

frete        GET   /health                          aberta
             POST  /api/v1/frete/cotacao            qualquer papel autenticado

notificacoes POST  /api/v1/notificacoes             ADMIN

rag          POST  /api/v1/perguntar            qualquer papel autenticado

ai-gateway   POST  /v1/chat/completions             qualquer papel autenticado
             GET   /v1/metricas                     ADMIN
```

**`GET /health` fica aberta em todos.** Não é descuido: o `healthcheck` do
Compose, que a Aula 07 ensinou, não carrega token. Proteger `/health` quebraria
a orquestração inteira, e essa é uma boa história para contar em sala.

Token ausente devolve **401**; token válido sem o papel devolve **403**. A
diferença entre os dois é conteúdo da aula e critério do verificador.

### 5. O que acontece com quem não fez as aulas anteriores

Cada serviço lê `LOGITECH_AUTH_ATIVA`, padrão **`false`**. Com a variável
desligada, o serviço se comporta como nas Aulas 05 a 12 e os laboratórios
anteriores continuam passando. A Aula 14 liga a variável no Compose dela.

Isso não é porta dos fundos escondida: é declarada no README, aparece no slide,
e o verificador da Aula 14 **exige que ela esteja ligada** para dar o critério
por cumprido. Sem esse interruptor, ligar segurança quebraria retroativamente
quatro laboratórios já publicados.

### 6. Guardrails do AI Gateway, na Aula 15

O gateway ganha uma camada de sanitização com contrato próprio:

- **Entrada:** detecta tentativa de sobrescrever a instrução de sistema e
  recusa, devolvendo **422** com `{"recusado": true, "motivo": "..."}`.
- **Saída:** mascara dado sensível antes de devolver, com formato fixo:
  CPF vira `***.***.***-**`, cartão vira `**** **** **** 1234`, placa vira
  `AAA*****`.
- **Métricas:** `GET /v1/metricas` ganha `guardrail.recusas_entrada` e
  `guardrail.mascaramentos_saida`.
- Liga e desliga por `LOGITECH_GUARDRAILS_ATIVOS`, padrão **`true`** a partir da
  Aula 15. O laboratório manda desligar para ver o ataque funcionar, e ligar
  para ver a defesa.

O aluno precisa **ver a injeção dar certo antes de ver a defesa funcionar**, ou
a defesa vira ritual.

### 7. Corte do Trivy

- Varredura com `trivy image --severity HIGH,CRITICAL`.
- Critério do entregável: **zero CRITICAL** nas imagens do projeto. HIGH é
  registrado, justificado e aceito quando vem da imagem base sem correção
  publicada.
- Vulnerabilidade aceita vai para um arquivo de exceções versionado, com data e
  motivo, e não some por `--ignore-unfixed` silencioso.

Aceitar HIGH com justificativa escrita é o que times reais fazem; exigir zero
HIGH faria o aluno inventar número para fechar a conta.

### 6.1 Propagação de credencial entre serviços

Decisão que faltava e que a construção da Aula 16 expôs: como os backends **não
são clients** (seção 2), quando um serviço chama outro ele **propaga o token do
usuário**, em vez de usar credencial própria de serviço.

A consequência é boa de ensinar: o `pedidos` chama o `faturamento` carregando o
token de quem pediu, então um usuário `CLIENTE` que cria pedido recebe
`faturamento: "recusado: HTTP 403"`, porque emitir fatura exige `ADMIN`. O papel
do usuário atravessa a cadeia inteira, e a autorização não se perde no meio.

A alternativa, que **não** adotamos, seria dar credencial de serviço ao
`pedidos`: resolveria o 403, e ao custo de o `faturamento` deixar de saber em
nome de quem age. Para uma disciplina que acabou de ensinar RBAC, o primeiro
comportamento vale mais.

### 6.2 Direct access grant: desligado na Aula 14, ligado na Aula 16

Os dois realms divergem **de propósito**, e cada um está certo no seu contexto:

- **Aula 14** entrega o realm com `directAccessGrantsEnabled: false`. A aula é
  sobre o fluxo PKCE, e desligar o atalho de pegar token por usuário e senha
  impede estruturalmente o aluno de pular justamente o que está sendo ensinado.
- **Aula 16** liga. Ali o token é obtido por script, pelo `verificar.py` e pelo
  cliente MCP, sem navegador no meio, e a aula não é mais sobre o fluxo.

Cada kit declara a escolha no README e no slide. Divergir sem declarar seria
defeito; divergir por motivo explícito é ensino.

### 7.1 Serviços congelados continuam mínimos

Vale para este módulo o mesmo que a `ADR-007` estabeleceu na Aula 07: o que cada
lab kit congela em `servicos/` são versões **mínimas**, que obedecem ao contrato
de rotas e portas mas não carregam os padrões de projeto das aulas em que
nasceram. O `pedidos` congelado da Aula 14, por exemplo, é Java em memória, sem
Spring e sem PostgreSQL, porque a aula é sobre validar token, não sobre JPA, e
um build de Maven dentro do laboratório de segurança comeria o tempo da aula.
Cada kit declara isso em `servicos/LEIA-ME.md` e no slide correspondente.

### 8. Variáveis novas

```
LOGITECH_AUTH_ATIVA          <- padrão false; a Aula 14 liga
LOGITECH_OIDC_ISSUER         <- http://localhost:8090/realms/logitech
LOGITECH_OIDC_JWKS_URL       <- http://keycloak:8090/realms/logitech/protocol/openid-connect/certs
LOGITECH_OIDC_CLIENT_ID      <- por frontend
LOGITECH_GUARDRAILS_ATIVOS   <- padrão true a partir da Aula 15
```

**Emenda de 31/07/2026, e ela corrige um erro desta ADR.** A primeira versão
mandava esperar `http://keycloak:8090/realms/logitech` no `LOGITECH_OIDC_ISSUER`.
Isso **derruba toda validação de token**, e as construções das Aulas 14 e 16
descobriram executando. O motivo: o `iss` que o Keycloak grava dentro do token é
o endereço pelo qual o **navegador** falou com ele, ou seja `localhost:8090`. O
backend precisa esperar exatamente esse valor.

Os dois endereços continuam existindo, com papéis distintos:

- `LOGITECH_OIDC_ISSUER` usa o endereço **do navegador**, porque é o que está
  gravado no token.
- `LOGITECH_OIDC_JWKS_URL` usa o endereço **da rede interna**, porque quem baixa
  a chave é o serviço, de dentro do Compose.

A Aula 14 adota a variante tolerante, aceitando os dois `issuer` numa lista
separada por vírgula, para o serviço funcionar tanto rodando solto quanto dentro
do Compose. A Aula 16 espera só o do navegador. As duas formas são válidas, e a
divergência entre elas é conteúdo: é o slide que explica por que um mesmo
Keycloak tem dois nomes.

Essa divergência derruba a validação com uma mensagem péssima, e por isso o
tratamento dela é conteúdo de aula, não nota de rodapé.

## Motivações

- Papel lido de dois lugares diferentes é o erro que faz autorização funcionar
  numa stack e falhar em outra com o mesmo token.
- Sem o interruptor `LOGITECH_AUTH_ATIVA`, ligar segurança quebraria quatro
  laboratórios publicados e o aluno que faltou não conseguiria seguir.
- Realm importado de arquivo é a diferença entre ambiente reproduzível e vinte
  telas de configuração que ninguém repete igual.

## Riscos conhecidos

| Risco | Mitigação |
|---|---|
| Treze containers na Aula 16 não caberem no Codespace | O roteiro sobe por grupos e mede; a Aula 07 já estabeleceu limites de memória por serviço |
| O aluno decorar o `curl` com token e não entender o fluxo | A Aula 14 obriga o fluxo PKCE pelo navegador antes de qualquer `curl` |
| Guardrail virar filtro de palavra proibida | O laboratório exige que o aluno **quebre** o próprio filtro e registre o que passou |
| Trivy mudar de resultado com o tempo, invalidando o número do slide | O slide cita a data da varredura e o critério é "zero CRITICAL", não um total fixo |
| A Aula 16 depender de doze laboratórios alheios | O kit da 16 traz a plataforma inteira congelada, como as aulas anteriores fizeram |

## Consequências

**Positivas**
- As três aulas podem ser construídas em paralelo sem divergir.
- A plataforma termina o semestre autenticando de ponta a ponta, com o mesmo
  papel valendo em Java, C#, Python e Node.
- O interruptor preserva tudo o que já foi publicado.

**Negativas**
- Mais uma variável de ambiente para explicar, e um caminho desligado que
  precisa continuar funcionando.
- O contrato de rotas engessa decisões que, num projeto real, o time discutiria.

## ADRs relacionadas

- `ADR-006`: contrato original da plataforma, que esta ADR estende.
- `ADR-007`: decisões de orquestração da Aula 07, incluindo o AI Gateway que a
  Aula 15 endurece.
- `ADR-008`: contrato do Módulo III, que trouxe os dois frontends e o RAG, agora
  protegidos.
