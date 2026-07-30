# Aula 02: o aluno passa a escrever o coletor L4

- **Data:** 2026-07-30
- **Autor:** Prof. José Romualdo da Costa Filho
- **Estado:** aprovado, em implementação

## Problema

O slide 5 do deck da Aula 02 traz um quadro vermelho intitulado "O QUE TEMOS
DEPOIS DA AULA 01" afirmando que existe "um processo Python escutando datagramas
na porta 8081". Isso não é verdade: a Aula 01 entregou apenas `docs/PRD.md` e
`docs/SDD.md`, sem uma linha de código.

O erro é visível em sala e contradiz o próprio slide 4 do mesmo deck, que diz
corretamente que "na Aula 01 a entrega foi a especificação, não o código".

Há um segundo problema por trás do primeiro, já registrado como risco conhecido
na ADR-002: com o coletor entregue pronto, o aluno chega ao **CP1 em 25/08**, uma
avaliação prática individual cujo escopo inclui Sockets TCP/UDP, sem nunca ter
escrito um socket.

## Decisão

O aluno passa a **completar** o coletor de sockets, a partir de um esqueleto com
TODO, e não a recebê-lo pronto.

Isso reverte a decisão 1 da ADR-002. As outras decisões dela continuam valendo: o
Wireshark segue fora, as medições numéricas com `cURL` seguem, e a passagem por
arquivo entre coletor e gateway segue como simplificação a ser desfeita na Aula
07. A reversão é registrada na ADR-003.

## Orçamento de tempo

O Bloco 2 vai de 21h20 a 22h50, 90 minutos, dos quais cerca de 15 são dos Quizzes
#2 e #3. Restam cerca de **75 minutos** para o laboratório.

| Passo | Antes | Depois |
|---|---|---|
| 1. Fork e branch | 5 | 5 |
| 2. Coletor L4 | 8 (só subir) | **12 (completar e subir)** |
| 3. Servidor HTTP/SSE | 27 | 27 |
| 4. Medições com cURL | 10 | 10 |
| 5. Pull Request cruzado | 10 | 10 |
| **Total** | **60** | **64** |

Cabe nos 75 disponíveis. A escolha por "completar esqueleto" e não "escrever do
zero" é o que faz caber: do zero custaria cerca de 25 minutos no Passo 2 e levaria
o total a 85, exigindo cortar as medições com `cURL` ou a revisão cruzada, que são
justamente as novidades desta aula.

## Desenho do esqueleto do coletor

`sockets-l4/server_telemetry.py` segue o mesmo contrato pedagógico que já funciona
em `http-l7/server.js`: uma parte pronta serve de modelo, o resto é TODO.

**Entregue pronto:**

- constantes, portas, caminhos de `data/telemetria.jsonl` e `data/entregas.jsonl`
- `agora_iso()`, `anexar()` e `validar_posicao()`, que são utilitários e não
  conteúdo de socket
- **o listener TCP 8080 completo** (`escutar_tcp` e `atender_conexao`), que é o
  modelo a ser imitado, exatamente como `GET /health` é o modelo dos TODO do HTTP
- o `main()` com o encerramento limpo e o resumo de contadores
- `client_telemetry.py`, o simulador da frota, inteiro

**Vira TODO, na função `escutar_udp`:**

1. criar o socket UDP e fazer bind na porta 8081
2. o laço de recepção com `recvfrom`
3. decodificar o datagrama em `dict`, descartando o ilegível
4. validar e anexar a linha em `data/telemetria.jsonl`

A escolha de deixar o UDP como tarefa e o TCP como modelo é deliberada: o UDP é o
que alimenta o Passo 3, então um TODO malfeito aparece imediatamente como painel
vazio, e não como erro silencioso.

## Verificação do Passo 2

O `http-l7/verificar.mjs` é Node e não alcança o coletor. Sem verificação própria,
o Passo 2 seria o único do laboratório sem critério objetivo.

Entra `sockets-l4/verificar.py`, sem dependências, que sobe uma frota curta contra
o coletor no ar e confere:

- `data/telemetria.jsonl` existe e **cresce** entre duas leituras
- cada linha é JSON válido
- cada linha tem `placa`, `lat`, `lng` e `recebido_em`
- datagrama inválido é descartado, e não gravado

Sai com código 1 se algo falhar, no mesmo padrão do `verificar.mjs`.

Os critérios de aceitação do README passam a incluir o coletor, e a numeração é
refeita.

## Coerência narrativa no deck

| Slide | Mudança |
|---|---|
| 4, Resgate da Espiral | ganha nota de rodapé com o caminho exato do PRD e do SDD da dupla |
| 5, Desafio do Mini Mundo | o quadro vermelho deixa de afirmar que existe processo rodando |
| Passo 2 do lab | deixa de dizer "o coletor vem pronto" e passa a apresentar os TODO |
| Divisão de tempo | de 60 para 64 minutos |

## Resgate do PRD e do SDD

Nota no rodapé do slide 4, onde o resgate da espiral acontece: os artefatos estão
no fork da dupla da Aula 01, em `github.com/SEU-USUARIO/mwe-2026-2-lab01-duplaXX`,
arquivos `docs/PRD.md` e `docs/SDD.md`. Quem não achar o fork, procura pelo Lab
Kit original em `josercf/mwe-2026-2-lab01-requisitos` e pela lista de forks.

## Slide 9: status codes

Duas mudanças, medidas antes: a figura ocupa 259px e sobram 240px até o rodapé.

1. **Animação.** Cada família vira `<g class="fragment">` e entra a um clique, para
   o professor conduzir uma de cada vez em vez de mostrar as cinco de uma só vez.
2. **Mais exemplos.** O `viewBox` cresce de `1120x250` para cerca de `1120x400`, e
   cada família ganha códigos adicionais e uma linha de uso concreto na API de
   telemetria da LogiTech: `409` em conflito de ocorrência, `422` em payload válido
   mas sem sentido de negócio, `429` quando a frota satura o gateway, `504` quando
   o coletor não responde a tempo.

## Como isto será validado

1. `python3 tools/check_slides.py` continua limpo nos 13 decks.
2. Os fragments do slide 9 são conferidos em navegador: cinco passos, um por
   família, e nenhuma família visível antes do primeiro avanço.
3. O laboratório roda **dentro da imagem do devcontainer**, não no macOS:
   - com o esqueleto do coletor, `sockets-l4/verificar.py` falha e sai com 1
   - com o gabarito do coletor, passa e sai com 0
   - a cadeia inteira (coletor do gabarito mais gateway do gabarito) mantém os 7
     critérios do `verificar.mjs`
4. O repositório que o aluno forka é sincronizado, e se confirma que ele **não**
   leva o `gabarito/`.

## Fora de escopo

- Reescrever a Aula 01 para produzir código. A espiral continua sendo
  especificação na 01 e implementação na 02.
- Mexer nas aulas 03 a 16.
