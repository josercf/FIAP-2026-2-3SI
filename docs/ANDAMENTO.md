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

`docs/adrs/ADR-002-escopo-do-laboratorio-da-aula-02.md` — **Aceita.** O laboratório da Aula 02 entrega o coletor de sockets L4 pronto e troca o relatório de captura por três medições numéricas com `cURL`. O **Wireshark saiu do programa da disciplina**, não só do laboratório, por decisão do professor em 30/07/2026. A comunicação entre o coletor e o gateway é por arquivo JSON Lines, simplificação declarada, a ser substituída na Aula 07.

---

### Aula 02 — pronta, publicada e com o repositório de lab sincronizado

35 slides validados em 1280x720, com diagramas SVG inline para a evolução do HTTP,
o handshake TLS e o fluxo do SSE. Lab Kit completo em `aulas-1sem/labs/aula02-lab/`.

O escopo do laboratório está em duas ADRs. A
`ADR-002-escopo-do-laboratorio-da-aula-02.md` tirou o Wireshark e trocou o
relatório de captura por três medições numéricas com `cURL`. A
`ADR-003-o-aluno-escreve-o-coletor-l4-na-aula-02.md` **superou a decisão 1 da
002**: o aluno passou a completar o coletor L4 em vez de recebê-lo pronto.

**Por que a 003 existe:** o slide do Desafio do Mini Mundo afirmava que "depois da
Aula 01 temos um processo Python escutando na 8081", o que era falso, já que a
Aula 01 entregou só PRD e SDD. Corrigir só o texto deixaria de pé o problema
maior, que a própria ADR-002 tinha registrado como risco: o aluno chegaria ao CP1,
uma prova prática individual que cobra Sockets TCP/UDP, sem nunca ter escrito um.
O coletor virou esqueleto com quatro TODO no lado UDP, com o lado TCP pronto como
modelo, e ganhou `sockets-l4/verificar.py` com cinco critérios. O laboratório foi
de 60 para 72 minutos, dentro dos ~75 do Bloco 2.

**Revisão de código assistida por IA.** A skill `code-review` foi importada de
`awesome-skills/code-review-skill` (MIT) para `josercf/skill-library`, com
`ORIGEM.md` registrando procedência, licença e commit. Entrou um slide novo com
instalação e exemplos de uso, e a revisão virou entregável: `docs/CODE_REVIEW.md`
pede qual PR foi revisado, como, o que se encontrou e qual sugestão foi dada,
incluindo o que a IA sugeriu e a dupla **descartou**, com a razão.

Validado de ponta a ponta **dentro da imagem do devcontainer**
(`typescript-node:1-22-bookworm`, que traz Python 3.11, Node 22 e `cURL`), nas
quatro combinações:

| | esqueleto entregue | gabarito |
|---|---|---|
| `sockets-l4/verificar.py` | 0 de 5, sai com 1 | 5 de 5, sai com 0 |
| `http-l7/verificar.mjs` | 1 de 7, sai com 1 | 7 de 7, sai com 0 |

A cadeia completa também roda: coletor do gabarito alimentando o gateway do
gabarito. Os dois verificadores discriminam de verdade.

As animações por clique dos slides 9 e 19 são conferidas em navegador: nada
visível antes do primeiro avanço, e um grupo por vez depois. `fragment` dentro de
SVG funciona, mas não é óbvio, então existe teste.

O formulário de entrega está publicado: <https://forms.cloud.microsoft/r/ykGYKsPAj7>,
embutido no slide 32 e citado no README do lab.

**O repositório que o aluno forka foi sincronizado**, em
<https://github.com/josercf/mwe-2026-2-lab02-http-sse>. Ele tinha só o esqueleto do
scaffolder, com um README que ainda mandava implementar os sockets e capturar
tráfego com Wireshark. Agora traz `sockets-l4/`, `http-l7/`, `docs/OBSERVACOES.md` e
o README real, **sem o `gabarito/`**.

> **Atenção ao publicar qualquer aula:** o repositório de lab é separado do acervo
> e **não é sincronizado por nada automático**. Depois de mexer em
> `aulas-1sem/labs/aulaXX-lab/`, é preciso clonar `josercf/mwe-2026-2-labNN-tema`,
> copiar o conteúdo (nunca o `gabarito/`), preservar `.devcontainer/` e `ai/ask.py`,
> e dar push. Foi assim que a Aula 02 foi sincronizada.

### Saneamento do acervo (30/07/2026)

- **Os 13 decks passam no `check_slides.py`.** Havia 5 slides de hands-on estourando
  (aulas 03, 05, 06, 07 e 08), todos pelo mesmo motivo: bloco de código longo em um
  slide que já trazia `concept-cards`. Resolvido com a classe `code-compact`.
- **`fiap-zoom.js` e `fiap-print.js` foram ligados nos 13 decks.** Verificado em
  navegador: FAB presente e zoom aplicando em todos. Atenção, o `fiap-print.js`
  revela a resposta dos quizzes em modo print.
- **`aulas-1sem/generate_classes.py` foi removido.** Era a armadilha que sobrescrevia
  os decks 02, 03, 05, 06, 07 e 08. Recuperável pelo histórico do git; substituído
  por `tools/scaffold_labs.py`.
- **`PLANO_DE_ENSINO.md` e `PLANEJAMENTO_AULA_A_AULA.md` alinhados com a ADR-002.**
  Corrigida de passagem a sobreposição de horário na agenda da Aula 02, que tinha
  dois blocos começando às 21h20.
- **O Wireshark foi removido de todo o acervo**, por decisão do professor. Saiu da
  ementa, da matriz de rastreabilidade, do `SKILL.md` e do `scaffold_labs.py`. A
  matriz afirmava que nenhum conteúdo original havia sido removido; passou a
  registrar essa exceção em vez de manter a afirmação. O que resta de menção ao
  Wireshark está na ADR-002 e aqui, que são o registro da decisão.

---

## Pendências

### Do professor

- [ ] **Criar o formulário de entrega de cada aula nova** no Microsoft Forms e passar a URL, para que o slide de entrega saia com o embed no lugar do marcador pendente. Os que já existem: Aula 01 em `https://forms.cloud.microsoft/r/sy6dHWsBHJ`, Aula 02 em `https://forms.cloud.microsoft/r/ykGYKsPAj7`.
- [ ] Decidir o subdomínio da votação ao vivo (`vote.jrcf.dev` foi a sugestão).

### Técnicas

- [ ] **Aulas 03 a 16 ainda são rasas.** Decks de ~140 a ~370 linhas, sem figura, quizzes genéricos. Cada uma precisa passar pelo `construtor-aulas`. **A próxima é a Aula 03** (Docker I, 18/08), que empacota justamente o coletor Python e o gateway Node da Aula 02.
- [ ] **Labs 03 a 16 têm só o esqueleto.** Devcontainer e README funcionam; falta o conteúdo de cada laboratório.
- [ ] **Decidir o destino do `gabarito/`.** Agora são dois arquivos, `server.js` e `server_telemetry.py`, commitados em `labs/aula02-lab/gabarito/`, e o workflow publica o repositório inteiro no GitHub Pages: um aluno que navegue pelo acervo acha as duas respostas. Confirmado que o repositório que o aluno forka **não** leva o gabarito, então o risco é só de quem procura no acervo. Avaliar se o gabarito sai do repositório público ou se fica assumido. A ADR-003 lista isto como risco aberto.
- [ ] **Os 72 minutos do lab da Aula 02 deixam só 3 de folga no Bloco 2.** Se a turma atrasar, o corte previsto na ADR-003 é a segunda metade do Passo 4, que são medições independentes, e não o Passo 5. Vale cronometrar na primeira aplicação e ajustar.
- [ ] **Os outros 12 repositórios de lab provavelmente estão como o da Aula 02 estava:** só o esqueleto do scaffolder, com README genérico. Ao construir cada aula, sincronizar o repositório correspondente junto, senão o aluno abre um kit que não bate com o slide.
- [ ] **A passagem por arquivo entre o coletor e o gateway precisa ser desfeita na Aula 07.** Está declarada como simplificação deliberada na ADR-002, no README do lab e no slide do Passo 2, com a Aula 07 nomeada como ponto de substituição. Ao construir a Aula 07, cobrar essa dívida.
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
