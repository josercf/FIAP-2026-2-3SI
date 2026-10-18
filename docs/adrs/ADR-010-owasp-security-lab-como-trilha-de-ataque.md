# ADR-010: O OWASP Security Lab entra como trilha de ataque, em repositório apartado

- **Data:** 2026-07-31
- **Status:** Aceita
- **Decisores:** Prof. José Romualdo da Costa Filho

## Contexto

O professor mantém o repositório <https://github.com/josercf/OWASP-Security-Lab>,
uma aplicação ASP.NET Core com vulnerabilidades **intencionais**, baseada no
OWASP Top 10 de 2021, que sobe inteira com um `docker-compose up`.

Ele resolve uma fraqueza real do material atual. A **Aula 15** cobra, na primeira
pergunta de verificação, que o aluno explique como Prompt Injection se assemelha
ao SQL Injection clássico. Hoje essa analogia é **retórica**: o aluno nunca
explorou um SQL Injection. A **Aula 14** constrói RBAC, 401 e 403 sobre uma
plataforma que nunca foi atacada, e portanto ensina a fechar uma porta que o
aluno nunca viu aberta.

A pergunta era se esse lab deveria ser incorporado ao acervo ou permanecer
separado.

## Decisão

**Permanece em repositório próprio**, e é citado pelas Aulas 14 e 15 como
**trilha de ataque**: o aluno explora a vulnerabilidade real lá antes de
construir a defesa no laboratório da aula. Nenhum código é duplicado no acervo.

### O que cada aula usa

| Aula | Módulo do lab | O que o aluno faz antes da defesa |
|---|---|---|
| 14 | `A01 Broken Access Control` | Quebra controle de acesso trocando o identificador do usuário alvo, e escala privilégio, antes de implementar RBAC com 401 e 403 |
| 15 | `A03 Injection`, página de SQL Injection | Explora injeção de SQL de verdade, e só então vê o mesmo mecanismo atacar o LLM |

O lab tem alternância entre modo vulnerável e modo seguro na mesma tela, que é
exatamente o padrão pedagógico que a Aula 15 já adota: **ver o ataque funcionar
antes de ver a defesa**.

### Por que apartado

1. **O acervo publica o repositório inteiro no GitHub Pages** a cada push.
   Trazer código deliberadamente vulnerável para dentro significa servi-lo no
   mesmo domínio do material didático e aumentar a chance de um aluno copiar um
   padrão furado para o entregável da Global Solution.
2. **Conflito de versão.** A `ADR-006` fixou .NET 8 para o serviço de
   Faturamento; o lab usa .NET 10 RC. Fundir criaria uma inconsistência de
   stack que alguém tropeça.
3. **O modelo de fork já é o do acervo.** O lab é autocontido e sobe com um
   comando, igual aos treze lab kits. Não há ganho em mesclar.
4. **Ciclo de vida diferente.** O lab evolui com o OWASP Top 10, não com a
   espiral da disciplina.

### A página de Prompt Injection do lab não é usada

O módulo `A03` também traz uma página de Prompt Injection, e ela **exige chave
da OpenAI** (`gpt-4o-mini`, chave informada pelo usuário). Isso contraria a
`ADR-005`, que tornou o Ollama local o único backend de IA da disciplina
justamente para o aluno não depender de chave, cota nem cartão.

Portanto: a disciplina usa **apenas a página de SQL Injection** do módulo A03. A
parte de Prompt Injection continua sendo feita no laboratório da própria Aula 15,
contra o modelo local, onde o aluno também implementa o guardrail.

Se um dia o lab apontar para um endpoint compatível com OpenAI configurável, o
Ollama serve por ali e essa restrição cai. Fica registrado como melhoria
possível, não como pendência da disciplina.

## Motivações

- Defesa ensinada sem ataque prévio vira ritual, e a Aula 15 já provou que ver o
  ataque primeiro muda o entendimento.
- A analogia entre SQL Injection e Prompt Injection deixa de ser afirmação do
  professor e passa a ser experiência do aluno.
- Aproveita material que já existe e funciona, sem custo de manutenção dobrada.

## Riscos conhecidos

| Risco | Mitigação |
|---|---|
| Aluno copiar padrão vulnerável para a Global Solution | O lab fica fora do acervo, e cada roteiro fecha mostrando o modo seguro e o código corrigido |
| .NET 10 RC deixar de buildar quando a versão final sair | O lab é separado e pode ser atualizado sem tocar em nenhuma aula |
| A trilha virar conteúdo obrigatório sem tempo de aula | O uso é curto e ancorado: um experimento por aula, antes do laboratório principal |
| O lab prometer mais do que entrega | O `README` foi corrigido para separar o que está implementado do que está planejado |

## Consequências

**Positivas**
- As Aulas 14 e 15 ganham o "antes" que lhes faltava, sem inchar o laboratório.
- O repositório do professor passa a ter uso didático definido e roteiros para os
  módulos que só tinham código.

**Negativas**
- Mais um repositório para a turma clonar, e mais um ponto de manutenção.
- A trilha depende de o aluno subir um ambiente extra, com Postgres próprio.

## ADRs relacionadas

- `ADR-005`: Ollama como único backend de IA, que é o motivo de a página de
  Prompt Injection do lab ficar de fora.
- `ADR-006`: contrato da plataforma, incluindo a fixação do .NET 8.
- `ADR-009`: contrato de segurança do Módulo IV, que as Aulas 14 e 15 implementam
  e que esta trilha passa a preceder.
