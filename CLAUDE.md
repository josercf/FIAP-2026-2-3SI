# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Retomando o trabalho?** `docs/ANDAMENTO.md` tem o estado atual: o que está pronto, o que está em andamento e as pendências abertas.

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

# Validar os decks: nenhum conteúdo pode estourar 1280x720
python3 tools/check_slides.py                              # todos os decks
python3 tools/check_slides.py aulas-1sem/aulas/aula01.html  # um deck
python3 tools/check_slides.py --shots /tmp/shots            # com screenshots dos problemas

# Regerar o esqueleto dos repositórios de laboratório
LABS_OUT=/tmp/labs python3 tools/scaffold_labs.py

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

- **Slide que estoura os 720px não é detectável por `scrollHeight`.** A `section` tem altura fixa, então o valor vem sempre 720 mesmo com conteúdo vazando. Use `tools/check_slides.py`, que compara o retângulo de cada descendente com a área útil. Um hook `PostToolUse` roda isso automaticamente ao editar qualquer `aulas/aula*.html`.
- **`position: absolute` em slide de blocos empilhados quebra sem estourar.** O elemento cabe nos 720px e mesmo assim cobre o bloco de cima. O `check_slides.py` hoje detecta isso e reporta `SOBREPOSICAO`, mas só entre filhos diretos da `section`. Prefira o fluxo normal: um bloco absoluto ajustado a olho volta a quebrar assim que o texto acima muda de tamanho.
- **Passar no validador não é o mesmo que o slide estar bom.** Ele não vê fonte pequena demais para projetar, figura espremida, nem o slide com os `fragment` revelados, porque mede o estado inicial. Tire screenshot de todo slide que ganhar bloco novo, SVG, `iframe`, `fragment` ou posicionamento absoluto.
- **Rode o `revisor-slides` antes de commitar qualquer deck.** Não é opcional e não precisa ser pedido: é parte do fluxo. A sobreposição do slide 3 da Aula 02 foi publicada porque o agente nunca rodou e o validador da época era cego para aquela classe de defeito.
- **Todo deck carrega `fiap-quiz.js`, `fiap-zoom.js` e `fiap-print.js`, nessa ordem.** Ao criar um deck novo, repetir as três tags. O zoom responde a `+`/`-`/`0` e o print injeta um FAB que reabre o deck com `?print-pdf`. Em modo print o `fiap-print.js` **revela a resposta correta dos quizzes**: PDF exportado por ele não deve ser distribuído antes da aula.
- **Bloco de código em slide que já tem `concept-cards` estoura os 720px.** Use `<pre class="code-compact">` nesse caso, e mantenha o trecho em até ~18 linhas.
- **Maturidade desigual entre decks.** `aula01.html` e `aula02.html` (~1700 linhas cada) são o padrão-ouro, escritos à mão, com diagramas SVG inline. Os decks 03–08 (~140 linhas) são saída crua de scaffolder e ainda são rasos. 10–16 estão no meio do caminho.
- Vários labs (`aula03`, `aula05`, `aula06`, `aula07`, `aula08`, `aula10`, `aula11`, `aula12`) estão sem `README.md`, contrariando o padrão da `SKILL.md`, e alguns têm apenas stubs.

## Automação

- **`tools/check_slides.py`** — validador de layout via Playwright. Serve o repositório, abre cada deck em 1280x720 e reporta qualquer elemento que ultrapasse a área útil. Sai com código 1 se houver problema.
- **Hook `PostToolUse`** (`.claude/settings.json`) — dispara o validador ao editar um deck. Roda em background e só interrompe se encontrar estouro.
- **Agente `construtor-aulas`** (`.claude/agents/`) — constrói ou reformula uma aula inteira (deck + Lab Kit) seguindo a metodologia. Consolida a espiral, o case, a anatomia do deck, o markup de quiz que funciona, os padrões de figura e as convenções editoriais. **Ponto de partida para qualquer aula nova.**
- **Agente `revisor-slides`** (`.claude/agents/`) — revisa um deck contra layout, convenções editoriais, profundidade pedagógica, links e numeração de rodapé. **Rode sempre antes de commitar um deck**, sem esperar que peçam: é a única etapa que olha o material como um todo, e é onde a renumeração de rodapé e os cortes de layout costumam deixar rastro.
- **`tools/scaffold_labs.py`** — gera o esqueleto dos 13 repositórios de laboratório (devcontainer com Ollama, cliente de IA, README). Respeita `LABS_OUT`.

## Laboratórios

Cada aula com lab tem um repositório público próprio em `josercf/mwe-2026-2-labNN-tema`, autocontido e independente dos demais. O aluno faz **fork**, não clone. Cada um traz:

- devcontainer sobre a imagem oficial da stack, com Ollama e `qwen2.5:1.5b` já baixados
- `ai/ask.py`, cliente sem dependências que usa GitHub Models (o `GITHUB_TOKEN` vem injetado no Codespaces) e cai para o Ollama local quando a cota acaba
- README com missão ancorada no case, passo a passo e entregáveis específicos

Os arquivos em `aulas-1sem/labs/` são a referência do professor; o que o aluno abre é o repositório.

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
