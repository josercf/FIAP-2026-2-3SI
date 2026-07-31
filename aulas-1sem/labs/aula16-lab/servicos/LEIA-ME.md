# `servicos/` - a plataforma congelada

**Nada aqui é tarefa da Aula 16.** Não editem estes arquivos.

Os treze serviços chegam prontos e funcionando, para que ninguém dependa de ter
concluído os doze laboratórios anteriores. É a mesma regra desde a `ADR-006`: o
lab kit da aula N traz o que as aulas anteriores entregaram.

O artefato de hoje é o `docker-compose.yml` da raiz, mais os três documentos em
`docs/`.

## O que mudou em relação ao que vocês receberam nas aulas anteriores

| Serviço | Mudança | Por quê |
|---|---|---|
| `pedidos` | `Seguranca.java`: valida JWT pelo JWKS e aplica RBAC; CORS; propaga o token nas chamadas aos vizinhos | ADR-008 e ADR-009 |
| `faturamento` | `Seguranca.cs`: o mesmo em C#. Rotas de fatura exigem ADMIN | ADR-009 |
| `frete` e `rag` | `seguranca.py`: o mesmo em Python | ADR-009 |
| `notificacoes` | `seguranca.ts`: o mesmo em Node. Rota exige ADMIN | ADR-009 |
| `ai-gateway` | `guardrails.py`: recusa de injeção com 422 e mascaramento de dado sensível | ADR-009, seção 6 |
| `rag` | `sanitizar_trecho` em `busca.py`: neutraliza instrução plantada em documento (injeção indireta) | Aula 15 |
| `portal` | `src/auth/pkce.ts`: login por Authorization Code com PKCE | ADR-009 |
| `painel-admin` | `src/app/nucleo/pkce.ts` e o interceptador de autorização | ADR-009 |
| Dockerfiles Node | removem o `npm` da imagem final | zero CRITICAL no Trivy |
| Dockerfile do `rag` | remove `perl-base` | quatro CVEs CRITICAL sem correção publicada |

## A mesma validação, quatro vezes

`Seguranca.java`, `Seguranca.cs`, `seguranca.py` e `seguranca.ts` fazem a mesma
coisa em quatro linguagens, e nenhum deles usa biblioteca de terceiro: cada
plataforma já traz o que é preciso para verificar uma assinatura RS256 e ler um
JSON.

Vale abrir os quatro lado a lado. É a demonstração mais direta de por que a
`ADR-009` precisou fixar **onde o papel mora dentro do token**: os quatro leem
de `realm_access.roles`, e se um deles lesse de `resource_access.<client>.roles`
o mesmo token autorizaria numa stack e seria recusado na outra.

## Os serviços mínimos, e a promessa que fica

`pedidos`, `faturamento`, `frete` e `notificacoes` são as versões **mínimas**
que a Aula 07 escreveu, agora com segurança e CORS. Elas cumprem o contrato da
`ADR-006`, e não têm os padrões de projeto que as Aulas 05 e 06 ensinam.

Na Global Solution, o que vocês apresentam é o **código de vocês**. O contrato
existe justamente para isso: trocar esta pasta pela implementação do grupo não
muda uma linha do `docker-compose.yml`.
