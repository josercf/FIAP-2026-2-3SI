# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é este repositório

Acervo didático da disciplina **Microservice and Web Engineering & IT Services** (Sistemas de Informação, FIAP, 1º semestre de 2026-2, Prof. José Romualdo). Não é uma aplicação: é um site estático de apresentações Reveal.js + kits de laboratório, publicado no GitHub Pages.

Não existe build, bundler, package manager na raiz nem suíte de testes. O que se edita é HTML, CSS, JS puro e Markdown.

## Comandos

```bash
# Preview local (obrigatório servir por HTTP: os decks usam caminhos relativos ../assets/)
python3 -m http.server 8000        # a partir da raiz do repositório
# depois: http://localhost:8000/                    -> redireciona ao portal
#         http://localhost:8000/aulas-1sem/aulas/aula01.html

# Exportar um deck em PDF: abrir a URL do deck com ?print-pdf e imprimir pelo navegador
#         http://localhost:8000/aulas-1sem/aulas/aula01.html?print-pdf

# Push como josercf (o ssh-agent tem várias identidades e o GitHub autentica
# primeiro como canaldoovidio, que não tem permissão de escrita neste repo)
GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519_josercf -o IdentitiesOnly=yes' git push
```

Deploy: `.github/workflows/static.yml` publica **o repositório inteiro** no GitHub Pages a cada push em `main`. Qualquer arquivo commitado fica público.

## Arquitetura do conteúdo

Três camadas que precisam permanecer coerentes entre si. Alterar o conteúdo de uma aula geralmente exige tocar em mais de uma:

1. **Planejamento** (raiz)
   - `PLANO_DE_ENSINO.md` — ementa, matriz de rastreabilidade, cronograma com datas, composição de notas, espiral do 2º semestre.
   - `PLANEJAMENTO_AULA_A_AULA.md` — roteiro minuto a minuto de cada encontro.
   - Ambos são a **fonte da verdade** para datas, títulos e escopo de cada aula. Slides e portal devem seguir o que está aqui.

2. **Metodologia** — `aulas-1sem/SKILL.md`
   Skill `fiap-course-design`: metodologia em espiral, aprendizagem por case (Mini Mundo), estrutura do encontro de 3,5h, os 6 pilares de conteúdo, padrão dos decks e dos lab kits. Ler antes de criar ou reestruturar qualquer aula. Existe também um repositório externo de skills compartilhadas: `git@github.com:josercf/skill-library.git`.

3. **Materiais** — `aulas-1sem/`
   - `index.html` — portal com cards por módulo, ligando cada aula ao deck e ao lab kit. **Precisa ser atualizado à mão** quando uma aula ou lab muda de caminho.
   - `aulas/aulaXX.html` — um deck Reveal.js autocontido por aula.
   - `labs/aulaXX-lab/` — código funcional do hands-on, um diretório por aula.
   - `assets/{css,js,img}/` — tema compartilhado.

Numeração: aulas 04, 09 e 13 são checkpoints (CP1/CP2/CP3) e não têm deck; a 17 é feedback da GS. Por isso a sequência de arquivos pula esses números.

### Case integrador

Todas as aulas e labs orbitam a **LogiTech Enterprise AI Platform**, uma plataforma fictícia de logística. Cada lab resolve uma dor de negócio dessa plataforma e os entregáveis se acumulam até a Global Solution. Ao criar conteúdo novo, ancorá-lo nesse case em vez de inventar exemplos genéricos.

## Anatomia de um deck

Cada `aulaXX.html` é um arquivo único, sem build, que carrega Reveal.js 5.1.0 do jsDelivr, `../assets/css/fiap-theme.css`, `../assets/css/fiap-print.css` e as fontes Montserrat + JetBrains Mono do Google Fonts. Reveal é inicializado inline com `width: 1280, height: 720, center: false, margin: 0` — o tema fixa `section` em 1280x720 absoluto, então **o conteúdo não rola: se não couber, quebra o slide**. Vale conferir visualmente cada slide alterado.

Classes de slide definidas em `fiap-theme.css`: `cover-slide`, `title-slide`, `content-slide`, `section-slide`, `break-slide`, `quiz-slide`, `exercise-slide`. Blocos internos reutilizáveis: `concept-cards`/`concept-card`, `side-by-side`, `slide-title-area` + `accent-bar`, `top-bar`, `slide-footer` (com `footer-bar` e `footer-page`), `fiap-logo-header`. Cor da marca: `--fiap-pink: #ED145B`.

Ordem canônica dos slides (ver `SKILL.md` §4): capa → título → agenda com horários → teoria → Quiz 1 → intervalo → Quizzes 2 e 3 → hands-on lab → encerramento com copyright.

### Armadilhas conhecidas

- **Os quizzes não funcionam.** Os 13 decks marcam a resposta com `<li data-correct="true">` dentro de `ul.quiz-options`, mas `assets/js/fiap-quiz.js` só reconhece dois outros padrões: `label > input[type=radio]` (com `data-correct` na `section`) e `button.quiz-option` legado. Nenhum listener é registrado, e as mensagens em `data-correct-msg`/`data-incorrect-msg` da `div.quiz-feedback` nunca são lidas. Ou o JS ganha suporte ao padrão `li`, ou o markup dos decks migra — escolher um e aplicar aos 13.
- **`fiap-zoom.js` e `fiap-print.js` não são carregados por nenhum deck.** Existem, funcionam (zoom por `+`/`-`/`0`, FAB de impressão), mas nenhum `<script src>` os referencia. `aula01.html` tem um botão "Exportar PDF" inline próprio em vez de usar `fiap-print.js`.
- **`generate_classes.py` é um scaffolder descartável, não um build.** Contém um `base_dir` absoluto hardcoded e **sobrescreve** `aulas/aulaXX.html` e `labs/aulaXX-lab/` das aulas 02, 03, 05, 06, 07 e 08. Rodá-lo hoje destrói qualquer refinamento feito nesses arquivos. Não executar sem intenção explícita.
- **Maturidade desigual entre decks.** `aula01.html` (~1000 linhas) é o padrão-ouro, escrito à mão, com CSS inline próprio. Os decks 02–08 (~140 linhas) são saída crua do scaffolder e ainda são rasos. 10–16 estão no meio do caminho.
- Vários labs (`aula02`, `aula03`, `aula05`, `aula06`, `aula07`, `aula08`, `aula10`, `aula11`, `aula12`) estão sem `README.md`, contrariando o padrão da `SKILL.md`, e alguns têm apenas stubs.

## Convenções editoriais

Regras estabelecidas em revisões anteriores, válidas para todo o material didático:

- **Sem emojis** em slides, títulos ou textos. O tom é corporativo e sênior.
- Português do Brasil **com acentuação completa**. Nunca usar travessão em dash.
- **Não expor pesos de avaliação nem fórmulas de cálculo de nota** nos slides.
- Não inventar "combinados de aula" ou recomendações genéricas: usar o que o professor forneceu.
- Preferir **imagens e diagramas didáticos** a paredes de texto — quando o roteiro pede imagem, entregar imagem.
- Citar referências com numeração ao longo dos slides e consolidá-las em um slide final de referências.
- Todo deck termina com o slide de copyright do Prof. José Romualdo.
- Commits em Conventional Commits, escopo pela aula: `refactor(aula01): ...`, `fix(pages): ...`.
