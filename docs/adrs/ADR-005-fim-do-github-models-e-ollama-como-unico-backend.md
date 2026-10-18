# ADR-005: O GitHub Models foi retirado e o Ollama local vira o único backend de IA dos laboratórios

- **Data:** 2026-07-30
- **Status:** Aceita
- **Decisores:** Prof. José Romualdo da Costa Filho
- **Relacionadas:** ADR-004, que decidiu o modelo local do lab03. Esta ADR
  generaliza aquela decisão para os 13 laboratórios e muda o motivo: lá era
  qualidade de tool calling, aqui é o desaparecimento do caminho primário.

## Contexto

O `ai/ask.py`, presente nos 13 repositórios de laboratório, foi desenhado com
dois caminhos: **GitHub Models** como primário, usando o `GITHUB_TOKEN` que o
Codespaces injeta, e **Ollama local** como plano B para quando a cota do aluno
acabasse. O `docs/ANDAMENTO.md` registrava, até hoje, "verificado nesta sessão: o
GitHub Models responde com o token do professor".

Durante o smoke test do `docker agent` para a Aula 03, o endpoint passou a
responder:

```
HTTP 410
{"error":{"code":"github_models_retirement_brownout",
          "message":"GitHub Models is temporarily unavailable as part of a
                     scheduled retirement brownout."}}
```

Confirmado por chamada direta com `curl`, fora da ferramenta que falhou. O
changelog do GitHub registra a **retirada total em 30/07/2026**, precedida de
brownouts em 16 e 23 de julho. Saem do ar o catálogo, o playground, a API de
inferência e os endpoints BYOK. Os sucessores indicados são o Microsoft Foundry,
que exige conta Azure, e o GitHub Copilot, que é integrado à IDE e não é API
chamável por script.

O caminho primário de IA de toda a disciplina deixou de existir no dia em que
este material estava sendo construído. A primeira aula é em 04/08/2026, então
**nenhum aluno chegou a usar o caminho quebrado**.

## Decisão

O `ai/ask.py` deixa de tentar o GitHub Models e passa a falar somente com o
**Ollama local**, que já está instalado em todos os 13 devcontainers.

O Microsoft Foundry foi descartado: exige conta Azure por aluno e, na prática,
cartão de crédito ou crédito educacional a ser providenciado institucionalmente.
Não é decidível a cinco dias da primeira aula.

## Motivações

- O Ollama **já está nos 13 devcontainers**, então a mudança é de remoção de
  código, não de adição de dependência.
- Funciona **igual em casa e no Codespaces**, sem token injetado e sem cota. Isso
  passou a importar mais depois da ADR-004, que criou uma etapa bônus feita em
  casa.
- Não depende de serviço de terceiro que possa ser descontinuado no meio do
  semestre, que é exatamente o que acabou de acontecer.
- Remove a explicação sobre cota e fallback do material, que existia só por causa
  do caminho que morreu.

## Riscos conhecidos

| Risco | Mitigação |
|---|---|
| O modelo local é pequeno e erra mais. No smoke test da Aula 03, o `qwen3.5:2b` produziu o artefato correto em 1 de 3 execuções | O material passa a tratar a saída do modelo como rascunho a ser conferido, nunca como resposta pronta. Isso já era a intenção pedagógica e agora vira explícito |
| A máquina padrão do Codespaces tem 2 núcleos e responde devagar | Medir na Aula 01 e, se inviável, avaliar modelo menor por laboratório, já que a ADR-004 tornou o modelo configurável por lab |
| O download do modelo pesa na criação do ambiente | Já pesava: o Ollama e o modelo sempre foram baixados no `post-create`. O que muda é que agora eles são o único caminho, não o reserva |
| A demonstração ao vivo da Aula 03 fica frágil com um modelo de 2B | O professor decidiu usar um modelo maior apenas na demonstração. Ver a seção seguinte |

## Consequência específica para a Aula 03

A demonstração de Agent Skills, no encerramento da Aula 03, será feita com um
modelo maior na máquina do professor, enquanto o aluno fica com o `qwen3.5:2b`
na etapa bônus.

Isso é uma escolha consciente com um custo declarado: a turma vê um resultado
melhor do que o que consegue reproduzir. O material precisa **dizer isso na
própria aula**, e não deixar o aluno descobrir sozinho em casa que o resultado
dele é pior. Um slide que mostra IA acertando e esconde que o aluno tem um modelo
menor ensina a coisa errada sobre engenharia com IA.

## Consequências

**Positivas.** Um caminho só, sem ramificação de cota nem de token. O
`ai/ask.py` encolhe. O material deixa de depender de serviço externo. O aluno
reproduz em casa exatamente o que faz em sala.

**Negativas.** A qualidade do assistente cai de forma perceptível em relação ao
que o GitHub Models entregava. Os 13 repositórios precisam ser regenerados e
ressincronizados, e os READMEs, o `aulas-1sem/SKILL.md` e o `docs/ANDAMENTO.md`
carregam texto sobre cota e fallback que deixou de fazer sentido.

## Trabalho que esta decisão gera

1. Reescrever `ai/ask.py` no `tools/scaffold_labs.py`, removendo o caminho do
   GitHub Models.
2. Corrigir o texto sobre backend de IA nos 13 READMEs gerados, no
   `aulas-1sem/SKILL.md` e no `docs/ANDAMENTO.md`, que hoje afirma que o GitHub
   Models foi verificado e funciona.
3. Ressincronizar os 13 repositórios `josercf/mwe-2026-2-labNN-tema`.
