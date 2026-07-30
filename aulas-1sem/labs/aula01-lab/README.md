# Laboratório Prático - Aula 01

## Disciplina: Microservice and Web Engineering & IT Services
**Prof.º José Romualdo | FIAP Sistemas de Informação**

### Case: LogiTech Enterprise AI Platform (Fase 1 - Especificação)

A LogiTech Enterprise precisa rastrear a frota em tempo real. Antes de escrever uma linha de código, a engenharia precisa responder **o que** será construído e **por quê** (PRD), e **como** o sistema se organizará (SDD).

O entregável de hoje é a **especificação**, não o código. Na Aula 02 vocês implementam exatamente o que especificaram aqui, e vão descobrir na prática o que uma especificação vaga custa.

**Duração:** 60 minutos, em dupla.

---

## Pré-requisitos

- Conta no GitHub (criada no Passo 1, se ainda não tiverem).
- Git instalado e configurado com `user.name` e `user.email`.
- [Ollama](https://ollama.com/download) instalado, para rodar o modelo localmente.

---

## Passo 1: Repositório (10 min)

1. Se ainda não tiver, crie a conta em [github.com](https://github.com).
2. Um integrante da dupla cria o repositório **público** com o nome exato:

   ```
   fiap-2026-2-3si-duplaXX
   ```

   Substitua `XX` pelo número da sua dupla, com dois dígitos (`dupla07`, não `dupla7`).

3. Em **Settings → Collaborators**, adicione o colega de dupla e o professor.
4. Clone o repositório na sua máquina:

   ```bash
   git clone https://github.com/SEU-USUARIO/fiap-2026-2-3si-duplaXX.git
   cd fiap-2026-2-3si-duplaXX
   ```

---

## Passo 2: Subir o modelo local (10 min)

Usamos um SLM (Small Language Model) rodando **na sua máquina**: nada é enviado para a nuvem, não há chave de API e não há custo.

```bash
ollama pull qwen2.5:3b     # ~2 GB, roda bem em notebook sem GPU dedicada
ollama run qwen2.5:3b      # teste rápido, digite /bye para sair
```

> **Notebook com pouca memória?** Use `qwen2.5:1.5b`.
> **Sem conseguir instalar a tempo?** Faça o laboratório com o assistente de IA que preferir e registre no PRD qual usou. O ponto pedagógico é a revisão crítica, não a ferramenta.

---

## Passo 3: Gerar e revisar o PRD e o SDD (30 min)

### 3.1 Criar a estrutura

```bash
mkdir -p docs
```

### 3.2 Gerar o PRD

Use como base a skill de PRD da nossa biblioteca compartilhada:
`https://github.com/josercf/skill-library` → `skills/prd/SKILL.md`

Prompt sugerido para o modelo:

```
Você é um Product Manager sênior. Escreva um PRD para o serviço de
telemetria de frota da LogiTech Enterprise, uma transportadora com 400
caminhões que hoje não sabe onde a carga está entre a coleta e a entrega.

Estruture em: Visão do Produto, Problema, Personas, Casos de Uso,
Requisitos Funcionais, Requisitos Não Funcionais e Métricas de Sucesso.

Cada requisito deve ser verificável e ter um identificador (RF-01, RNF-01).
Não proponha solução técnica: o PRD descreve o problema, não a arquitetura.
```

Salve a saída em `docs/PRD.md`.

### 3.3 Gerar o SDD

```
Com base no PRD acima, escreva um System Design Document.

Inclua: Bounded Contexts identificados, a Linguagem Ubíqua (glossário dos
termos do domínio), escolha da camada de transporte para cada fluxo de
dados com justificativa, e o desenho dos componentes.

Para cada decisão de protocolo, justifique a escolha entre TCP e UDP em
função do requisito não funcional que a motiva.
```

Salve a saída em `docs/SDD.md`.

### 3.4 Revisar criticamente (esta é a parte avaliada)

O modelo **vai errar**. Leia os dois documentos e corrija à mão:

- [ ] Algum requisito é vago a ponto de não dar para testar? ("o sistema deve ser rápido" não é requisito)
- [ ] Os termos do domínio estão consistentes entre PRD e SDD, ou o mesmo conceito aparece com dois nomes? (Linguagem Ubíqua)
- [ ] O SDD justificou TCP e UDP a partir de um requisito real, ou apenas repetiu a definição dos protocolos?
- [ ] Há requisito inventado que ninguém pediu?
- [ ] Os Bounded Contexts refletem áreas de negócio, ou viraram só camadas técnicas?

Ao final do `PRD.md`, acrescente uma seção **"Revisão da Dupla"** listando o que vocês corrigiram na saída do modelo e por quê. Sem essa seção, a entrega fica incompleta.

---

## Passo 4: Commit e entrega (10 min)

```bash
git add docs/
git commit -m "docs(telemetria): adiciona PRD e SDD do servico de rastreamento de frota"
git push origin main
```

Submeta a URL do repositório no formulário da disciplina.

---

## Critérios de aceitação

| # | Critério |
|---|---|
| 1 | Repositório com o nome no padrão, colega e professor como colaboradores |
| 2 | `docs/PRD.md` presente, com requisitos identificados e verificáveis |
| 3 | `docs/SDD.md` presente, com Bounded Contexts e glossário da Linguagem Ubíqua |
| 4 | Escolha de TCP/UDP justificada por requisito não funcional, não por definição de livro |
| 5 | Seção "Revisão da Dupla" descrevendo as correções feitas na saída do modelo |
| 6 | Ao menos um commit seguindo Conventional Commits |

---

## Estrutura esperada da entrega

```
fiap-2026-2-3si-duplaXX/
├── docs/
│   ├── PRD.md      # Product Requirements Document (gerado + revisado)
│   └── SDD.md      # System Design Document (gerado + revisado)
└── README.md
```

Os arquivos em `docs/` deste diretório são **exemplos de referência** do formato esperado. Não copiem: o conteúdo de vocês deve sair da revisão de vocês.

---

## Na próxima aula

A Aula 02 implementa o servidor de telemetria em Python (Sockets TCP e UDP) a partir do SDD que vocês escreveram hoje, e sobe para HTTP e SSE. O código de partida está em `../aula02-lab/sockets-l4/`.
