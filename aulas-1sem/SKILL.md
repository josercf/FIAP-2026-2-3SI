---
name: fiap-course-design
description: Metodologia e padrão de arquitetura pedagógica para planejamento e construção de disciplinas de graduação em TI na FIAP (Microservice and Web Engineering, Engenharia de Software, etc.). Inclui Metodologia em Espiral, Aprendizagem por Case (Mini Mundo), Estruturação de Aulas de 3,5h (com intervalo de 30 min às 20h50), Perguntas de Verificação, POO/SOLID, Design Patterns, Pirâmide de Testes, Git Worktrees para Agentes de IA, Perspectiva AI-First, Decks Reveal.js e Lab Starter Kits.
---

# FIAP Course Design Skill — Guia de Arquitetura Pedagógica & Construção de Aulas

Este guia consolida a metodologia pedagógica, a arquitetura de aprendizado e os padrões técnicos desenvolvidos para o planejamento e construção dos materiais de cursos de graduação da FIAP (como *Microservice and Web Engineering & IT Services*).

---

## 1. Visão Geral da Metodologia Pedagógica

A construção de cursos baseia-se em 3 pilares metodológicos integrados:

1. **Metodologia de Aprendizagem em Espiral (Spiral Learning Architecture):**
   - Os tópicos técnicos **nunca se exaurem em uma única aula**.
   - Cada nova aula recupera explicitamente a base teórica e prática das aulas anteriores e adiciona uma nova camada de complexidade (ex.: Sockets L4 na Aula 01 $\rightarrow$ APIs HTTP L7 na Aula 02 $\rightarrow$ Containers Docker na Aula 03 $\rightarrow$ Docker Compose na Aula 07).

2. **Aprendizagem Baseada em Problemas (PBL) por Case ("Mini Mundo"):**
   - Todas as aulas orbitam em torno da evolução incremental de uma plataforma corporativa fictícia realista (ex.: *LogiTech Enterprise AI Platform*).
   - O laboratório de cada aula resolve uma dor específica de negócio dentro do "Mini Mundo", transformando os entregáveis em blocos de montar da solução final da **Global Solution**.

3. **Arquitetura AI-First & Engenharia Enterprise:**
   - Integração transversal de conceitos de IA (AI Gateways, RAG com `pgvector`, Model Context Protocol - MCP, Function Calling, OWASP Top 10 for LLMs) associada às práticas consagradas de engenharia (PRD/SDD, DDD, POO/SOLID, Design Patterns, Pirâmide de Testes e Git Worktrees).

---

## 2. Estrutura Padrão de um Encontro (3,5 Horas)

As aulas ocorrem tipicamente das 19h20 às 22h50 (210 minutos totais), com um **intervalo obrigatório de 30 minutos às 20h50**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ BLOCO 1 (19h20 – 20h50) [90 min]                                                       │
│ ├─ 19h20 - 19h35 [15 min]: Resgate da Espiral (Recap da aula anterior & conexão)        │
│ ├─ 19h35 - 19h55 [20 min]: O Desafio do Mini Mundo (Problema de negócio do case)       │
│ ├─ 19h55 - 20h35 [40 min]: Fundamentação Teórica, Métodos & Padrões                    │
│ └─ 20h35 - 20h50 [15 min]: Pergunta de Verificação #1 & Espaço para Dúvidas I          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ ☕ INTERVALO (20h50 – 21h20) [30 min] - Pausa para Café e Networking                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ BLOCO 2 (21h20 – 22h50) [90 min]                                                       │
│ ├─ 21h20 - 21h35 [15 min]: Perguntas de Verificação #2 e #3 (Fixação dos Padrões)      │
│ ├─ 21h35 - 22h35 [60 min]: Construção Guiada & Atividade Prática (Hands-on Lab)        │
│ └─ 22h35 - 22h50 [15 min]: Espaço para Dúvidas II, Commit no Git & Entregável          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Os 6 Pilares de Conteúdo Técnico

Toda disciplina de Engenharia Web / Microsserviços deve contemplar os seguintes 6 pilares:

1. **Engenharia de Requisitos & DDD:** PRD (*Product Requirement Document*), SDD (*System Design Document*), *Bounded Contexts*, Entidades, Aggregates, Value Objects e Eventos de Domínio.
2. **Git Workflows & Git Worktrees para IA:** GitFlow, Conventional Commits, Pull Requests e **Git Worktrees** (criação de diretórios de trabalho isolados para execução de Agentes de IA em paralelo sem conflito de branches).
3. **Orientação a Objetos & SOLID:** Abstração, Encapsulamento, Herança, Polimorfismo e os 5 princípios SOLID (SRP, OCP, LSP, ISP, DIP) em Java e C#.
4. **Design Patterns (GoF):**
   - *Criacionais:* Factory Method, Builder, Singleton.
   - *Estruturais:* Adapter, Facade, Decorator.
   - *Comportamentais:* Strategy, Observer (RxJS), Command (Function Calling).
5. **Pirâmide de Testes Completa:**
   - *Unidade:* TDD com JUnit, xUnit, PyTest, Vitest e Mocks.
   - *Integração:* Testcontainers (bancos e serviços reais em containers de teste).
   - *Interface / E2E:* Playwright e Cypress.
   - *Carga / Performance:* k6 (instrumentação de SLAs, throughput RPS e latência p95/p99).
6. **Infraestrutura & Ecossistema AI-First:** Sockets TCP/UDP, HTTP/1.1 a 3, SSE, inspeção de tráfego com `cURL`, Docker Multi-stage, Docker Compose, AI Gateways (LiteLLM/Portkey), RAG com `pgvector`, Model Context Protocol (MCP), Keycloak/OAuth2/JWT e OWASP Top 10 for LLMs.

---

## 4. Padrão dos Decks de Slides em Reveal.js (Tema FIAP)

Cada aula deve possuir uma apresentação HTML em Reveal.js salva em `aulas-1sem/aulas/aulaXX.html`.

### Estrutura do Arquivo HTML:
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Aula XX – [Título] | FIAP</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/white.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/highlight/monokai.css">
  <link rel="stylesheet" href="../assets/css/fiap-theme.css">
  <link rel="stylesheet" href="../assets/css/fiap-print.css">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
</head>
<body>
  <div class="reveal">
    <div class="slides">
      <!-- Capa -->
      <section class="cover-slide">...</section>
      <!-- Título -->
      <section class="title-slide">...</section>
      <!-- Agenda com Horários e Intervalo das 20h50 -->
      <section class="content-slide">...</section>
      <!-- Seções Teóricas com Concept Cards & Code Blocks -->
      <section class="content-slide">...</section>
      <!-- Quiz 1 (Antes do Intervalo) -->
      <section class="quiz-slide content-slide">...</section>
      <!-- Pausa do Café (20h50 - 21h20) -->
      <section class="content-slide">...</section>
      <!-- Quizzes 2 e 3 (Retorno do Intervalo) -->
      <section class="quiz-slide content-slide">...</section>
      <!-- Hands-on Lab & Entregável Git -->
      <section class="content-slide">...</section>
      <!-- Encerramento com Copyright -->
      <section class="end-slide">...</section>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
  <script src="../assets/js/fiap-quiz.js"></script>
</body>
</html>
```

### Regras dos Quizzes Interativos:
- Utilizar a classe `.quiz-container` com `<ul class="quiz-options">`.
- Marcar a opção correta com `data-correct="true"` e incluir feedbacks nas propriedades `data-correct-msg` e `data-incorrect-msg`.

---

## 5. Padrão dos Kits de Laboratório Prático (Hands-on Labs)

Cada aula deve possuir um diretório de laboratório em `aulas-1sem/labs/aulaXX-lab/` contendo:

1. **`README.md`:**
   - Desafio de negócio do Mini Mundo.
   - Pré-requisitos e comandos de execução passo a passo.
   - Instrução do commit Git esperado.
2. **Código-Fonte Funcional:**
   - Código completo e testado em Python, Java, C#, Node.js, React, Angular ou Docker.
   - Sem trechos incompletos ou placeholders genéricos.

---

## 6. Fluxo de Geração por Subagentes Paralelos

Ao criar o acervo completo de disciplinas:
1. **Validar a Aula 01** primeiro (Slides HTML + Kit de Lab) para consolidar a identidade visual e o modelo pedagógico.
2. **Definir um Subagente Especializado** com `define_subagent` com permissões de gravação (`enable_write_tools: true`).
3. **Disparar Subagentes Paralelos por Módulos** utilizando `invoke_subagent` (ex.: Subagente 1 para Módulos I e II, Subagente 2 para Módulo III, Subagente 3 para Módulo IV).
4. **Gerar o Dashboard Index (`index.html`):** Criar um portal centralizado conectando os links de todos os slides e laboratórios gerados.
