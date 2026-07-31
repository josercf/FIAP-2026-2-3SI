# Etapa 8, bônus: Agent Skill

## Enunciado

Etapa bônus, feita em casa, sem prazo de aula. Peça para o agente escrever
um Dockerfile usando a skill `logitech-dockerfile`, cole o que ele gerou, e
depois **confira e corrija**. O ponto pedagógico não é o agente acertar de
primeira: é você saber reconhecer o que ele errou, porque a saída de um
modelo pequeno é rascunho a conferir, nunca resposta pronta.

## Comando

```bash
# a partir da raiz do laboratório, dentro do devcontainer do lab
docker-agent run agente.yaml
```

No prompt do agente, peça, por exemplo:

```
Escreva o Dockerfile do gateway usando a skill logitech-dockerfile.
```

A skill que o agente carrega sob demanda está em
`.agents/skills/logitech-dockerfile/SKILL.md`. Ela lista as regras que não
se negociam: dois estágios nomeados (`builder` e `runtime`), base alpine no
estágio final, usuário não-root com UID acima de 10000, nunca `COPY . .`, e
o caminho de dados vindo de `LOGITECH_DADOS`.

**Atenção:** o modelo local do laboratório (`qwen3.5:2b`) é bem menor que o
modelo usado na demonstração do professor em sala. Não é incomum ele
esquecer alguma das regras da skill, errar a ordem das instruções, ou copiar
mais do que devia para o estágio final. É exatamente isso que este exercício
pede para você registrar.

## O que registrar

Cole o Dockerfile exatamente como o agente gerou (sem corrigir nada ainda),
e depois escreva, em pelo menos duas frases, o que ele errou e como você
corrigiu. Frases genéricas como "o agente errou algumas coisas" não contam:
aponte a instrução ou a regra específica da skill que ficou de fora.

## Resposta

```
DOCKERFILE_GERADO_PELA_SKILL:
PREENCHER (cole aqui o Dockerfile completo que o agente devolveu)

O_QUE_O_AGENTE_ERROU:
PREENCHER (no mínimo duas frases, cada uma apontando um erro concreto e a
correção que você aplicou)
```
