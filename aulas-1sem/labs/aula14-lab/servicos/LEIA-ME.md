# O que há em `servicos/`, e por que nada aqui é tarefa

Regra herdada da `ADR-006` e mantida por todo o semestre: o kit da aula N traz
os serviços das aulas anteriores **prontos e congelados**. Quem faltou a uma
aula consegue fazer a seguinte.

Nesta noite há **duas exceções** dentro de arquivos congelados, e as duas
estão marcadas com `TODO`:

| Arquivo | O que é |
|---|---|
| `pedidos/Seguranca.java` | **Seu.** As lacunas `TODO-2` e `TODO-3` |
| `notificacoes/seguranca.mjs` | **Seu.** A lacuna `TODO-4` |

Todo o resto é para ler, não para editar.

## As três diferenças em relação ao que você escreveu antes

Declaradas aqui porque diferença escondida vira dúvida em sala.

**1. O `pedidos` guarda estado em memória, sem PostgreSQL.**
Na Aula 05 ele persiste em banco, e continua sendo assim no contrato. Aqui um
banco a mais seria um container a mais para subir sem ensinar nada sobre
autenticação. Reiniciar o serviço devolve os três pedidos semente, o que é
uma vantagem: dá para repetir o exercício quantas vezes for preciso.

**2. O `pedidos` não usa Spring Boot: é o servidor HTTP da própria JDK.**
Numa aula sobre validar token, ver a validação linha a linha vale mais do que
a comodidade de uma anotação. `Jwt.java` tem noventa linhas e faz exatamente
o que o `spring-boot-starter-oauth2-resource-server` faz: baixa o JWKS, acha
a chave pelo `kid`, confere a assinatura, e só então olha `exp` e `iss`.
Quando você usar a biblioteca de verdade, vai saber o que ela está fazendo.

**3. O `notificacoes` não tem uma única dependência.**
`node:crypto` verifica RS256 a partir de uma chave em formato JWK desde o
Node 16. Não há `npm install` no build da imagem.

O que **não** muda: porta, rotas, formato de JSON e nomes de campo. Isso é
contrato (`ADR-006`), e é o que permite o portal da Aula 10 e o agente da
Aula 08 continuarem falando com estes serviços.

## Como rodar cada suíte sem subir nada

```bash
# Java, com o serviço já construído
docker compose up -d --build pedidos
docker compose exec pedidos java -cp /app/classes TestesSeguranca

# Node
docker compose exec notificacoes node --test seguranca.test.mjs
```

As duas geram um par de chaves RSA na hora, sobem um JWKS de mentira em
`127.0.0.1` e assinam os próprios tokens. Rodam offline, em menos de um
segundo, e dizem exatamente qual `TODO` está faltando.
