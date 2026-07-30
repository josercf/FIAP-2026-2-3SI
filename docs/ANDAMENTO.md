# Andamento do acervo

Estado do trabalho para retomar em uma sessão nova. Atualize este arquivo ao fim de cada sessão.

**Última atualização:** 30/07/2026

---

## Primeiro: leia isto ao abrir a sessão

1. `CLAUDE.md` — comandos, arquitetura do acervo e armadilhas conhecidas.
2. `.claude/agents/construtor-aulas.md` — metodologia consolidada para construir aula.
3. Este arquivo.

Push do acervo **exige a chave do josercf**, senão o GitHub autentica como `canaldoovidio` e nega:

```bash
GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519_josercf -o IdentitiesOnly=yes' git push
```

---

## Onde está cada coisa

| | |
|---|---|
| Acervo | <https://github.com/josercf/FIAP-2026-2-3SI> |
| Portal publicado | <https://josercf.github.io/FIAP-2026-2-3SI/> |
| Labs | `josercf/mwe-2026-2-labNN-tema`, 13 repositórios públicos |
| Skills compartilhadas | <https://github.com/josercf/skill-library> |
| Lab interno | `ssh josercf@home01`, domínio `jrcf.dev` |

---

## Concluído

### Aula 01 — pronta e publicada

41 slides, validados em 1280x720, no ar em
<https://josercf.github.io/FIAP-2026-2-3SI/aulas-1sem/aulas/aula01.html>.

Foi refeita a partir do feedback do professor: foto real de família no slide de apresentação, texto oficial da FIAP no objetivo, slide de SDD corrigido para **Spec Driven Development**, Bounded Contexts dividido em dois com diagramas, o Multiverso do Git dividido em três (analogia, anatomia de um commit, o que é uma branch), atividade prática em cinco slides começando por fork do Lab Kit, e slide de entrega com o Microsoft Forms embedado.

### Infraestrutura de laboratório

13 repositórios públicos criados, um por aula com lab, autocontidos:

- devcontainer sobre a imagem oficial da stack, com **Ollama e `qwen2.5:1.5b` já baixados** na criação
- `ai/ask.py` sem dependências: usa **GitHub Models** com o `GITHUB_TOKEN` que o Codespaces injeta, e cai para o Ollama local quando a cota acaba
- README com missão no case LogiTech, passo a passo e entregáveis com valor numérico
- fluxo por **fork**, não clone

Gerados por `tools/scaffold_labs.py` (respeita `LABS_OUT`).

Verificado nesta sessão: o GitHub Models responde com o token do professor. Atenção, os limites medidos (20k req / 2M tokens) são da conta dele, que tem Copilot. Conta de aluno no free tier tem cota bem menor, e é por isso que o fallback local existe.

### Automação

- **`tools/check_slides.py`** — validador Playwright. Compara o retângulo de cada descendente com a área útil do slide. Achou 6 slides estourando na Aula 01 que passavam despercebidos.
- **Hook `PostToolUse`** em `.claude/settings.json` — roda o validador ao editar qualquer `aulas/aula*.html`.
- **Agente `construtor-aulas`** — constrói aula inteira seguindo a metodologia.
- **Agente `revisor-slides`** — revisa deck de forma independente.

### Decisões registradas

`docs/adrs/ADR-001-votacao-ao-vivo-nos-quizzes.md` — a votação ao vivo dos quizzes será um produto separado, fora do contexto FIAP, hospedado no `home01` sob `jrcf.dev`, atrás do nginx-proxy-manager e usando o PostgreSQL que já rodam lá. Sugestão de subdomínio: `vote.jrcf.dev`. Nada foi implementado ainda; o QR nos slides é placeholder tracejado escrito "em breve".

---

## Em andamento

### Aula 02 — sendo construída por agente

Um agente foi disparado para construir deck e Lab Kit da Aula 02 (HTTP/1.1 a 3, SSE, Git Workflows). **Se a sessão terminou antes de ele reportar, verifique `git status` e o conteúdo de `aulas-1sem/aulas/aula02.html`** para ver o que ficou.

O que foi instruído:

- Refazer o deck do zero. O atual tem 137 linhas de saída de scaffolder, sem figura.
- **Nunca rodar `aulas-1sem/generate_classes.py`**: ele sobrescreve decks e labs das aulas 02, 03, 05, 06, 07 e 08.
- Amarrar a espiral: na Aula 01 as duplas entregaram só `docs/PRD.md` e `docs/SDD.md`, sem código. A Aula 02 implementa o que foi especificado.
- **Wireshark foi removido do escopo** por decisão do professor: não gera valor suficiente para o tempo que consome. A inspeção de tráfego fica só com `cURL` (`curl -v` para headers e handshake, `curl -N` para o stream do SSE).
- Reaproveitar o material existente em `aulas-1sem/labs/aula02-lab/`: `server.js` (15 linhas, SSE antigo) e `sockets-l4/` (66 linhas, vindas da Aula 01).
- Não commitar nem dar push: o professor revisa antes.

**Problema de escopo que o agente foi encarregado de resolver:** como os sockets saíram do lab da Aula 01, o lab da 02 acumulou implementar sockets a partir do SDD, subir para HTTP/SSE e abrir PR em 60 minutos. A remoção do Wireshark abriu folga. A decisão dele deve estar no relatório.

---

## Pendências

### Do professor

- [ ] **Criar o formulário de entrega da Aula 02** no Microsoft Forms e passar a URL. O da Aula 01 é `https://forms.cloud.microsoft/r/sy6dHWsBHJ`. O slide da Aula 02 fica com marcador de URL pendente até lá.
- [ ] Decidir o subdomínio da votação ao vivo (`vote.jrcf.dev` foi a sugestão).

### Técnicas

- [ ] **Validar os 11 decks restantes.** Só a Aula 01 passou pelo `check_slides.py`. Os decks 02 a 16 são saída de scaffolder e provavelmente têm estouro. Rode `python3 tools/check_slides.py` sem argumento para o mapa completo.
- [ ] **Aulas 03 a 16 ainda são rasas.** Decks de ~140 a ~370 linhas, sem figura, quizzes genéricos. Cada uma precisa passar pelo `construtor-aulas`.
- [ ] **Labs 03 a 16 têm só o esqueleto.** Devcontainer e README funcionam; falta o conteúdo de cada laboratório.
- [ ] `fiap-zoom.js` e `fiap-print.js` existem e funcionam, mas nenhum deck os carrega. Decidir se entram ou se saem do repositório.
- [ ] `aulas-1sem/generate_classes.py` é uma armadilha: caminho absoluto hardcoded e sobrescreve trabalho refinado. Considerar remover, já que `tools/scaffold_labs.py` o substituiu.
- [ ] Duplicação no `home01`: `~/infra/docker-compose.yml` e `~/homelab/docker-compose.yml` **definem os dois o nginx-proxy-manager e o n8n**. Parece migração inacabada. Resolver antes de subir serviço novo, senão um `compose up` pode derrubar o proxy no meio de uma aula.

---

## Convenções que já custaram retrabalho

Estão no `CLAUDE.md` e no agente construtor, mas repetindo o essencial:

- Sem emojis. Português com acentuação. Nunca travessão em dash.
- Nunca expor peso de avaliação nem fórmula de nota nos slides.
- Não inventar conteúdo institucional: perguntar.
- Conceito visual pede figura, não dois cards de texto.
- Preferir SVG inline a imagem de terceiro, que é risco de licença em site público.
- **`scrollHeight` da `section` não detecta estouro**, porque a altura é fixa em 720. Use o validador.
- Nunca afirmar que validou sem ter validado.
