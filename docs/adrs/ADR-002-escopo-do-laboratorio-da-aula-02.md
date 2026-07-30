# ADR-002: Escopo do laboratório da Aula 02

- **Data:** 2026-07-30
- **Status:** Aceita
- **Decisores:** Prof. José Romualdo da Costa Filho

## Contexto

O laboratório da Aula 02 tem **60 minutos** e o entregável previsto no
`PLANEJAMENTO_AULA_A_AULA.md` era um Pull Request aprovado com o servidor
HTTP/SSE em Node.js mais um relatório de captura do Wireshark.

Duas circunstâncias tornaram esse escopo inviável:

1. **O laboratório da Aula 01 não produziu código.** A entrega da Aula 01 foi
   apenas a especificação (`docs/PRD.md` e `docs/SDD.md`). Os arquivos de socket
   (`server_telemetry.py`, `client_telemetry.py`) saíram do lab da Aula 01 e
   foram movidos para `labs/aula02-lab/sockets-l4/`. Sem uma decisão explícita,
   a Aula 02 herdaria a tarefa de implementar os sockets L4 a partir do SDD
   **além de** subir para HTTP/SSE, capturar tráfego e conduzir um Pull Request.
2. **Wireshark tem custo de instalação e de atenção alto.** Instalar, escolher a
   interface de captura (loopback, não Wi-Fi), aprender filtros de exibição e
   redigir um relatório consome facilmente 20 dos 60 minutos, em uma turma onde
   parte das máquinas não terá permissão administrativa para instalar a
   ferramenta.

Somando tudo, o laboratório pedia perto de 100 minutos de trabalho em uma janela
de 60.

## Decisão

O laboratório da Aula 02 passa a ter **três recortes**:

1. **O coletor de sockets L4 é entregue pronto** no Lab Kit, como ponto de
   partida. O aluno escreve apenas a camada HTTP/SSE por cima dele.
2. **O Wireshark sai do programa da disciplina**, não apenas do laboratório. A
   inspeção de tráfego permanece como objetivo de aprendizagem, feita apenas com
   `cURL`, e o relatório de captura é substituído por **três medições numéricas**
   registradas em `docs/OBSERVACOES.md`.
3. **A comunicação entre o coletor L4 e o gateway L7 é por arquivo**
   (`data/telemetria.jsonl`, formato JSON Lines), declarada no material como uma
   simplificação deliberada, a ser substituída na Aula 07.

Divisão dos 60 minutos: 5 para o fork e a branch, 8 para subir o coletor, 27 para
o servidor HTTP/SSE, 10 para as medições com cURL e 10 para o Pull Request com
revisão cruzada entre duplas.

## Motivações

- **O objetivo de aprendizagem da aula é a camada L7 e o fluxo de revisão.**
  Sockets são o objetivo da Aula 01, já avaliado na especificação e cobrado de
  novo no CP1. Gastar 20 minutos reimplementando L4 tira tempo justamente do que
  a Aula 02 quer ensinar.
- **Ler código pronto é competência, não atalho.** O coletor entregue é a
  materialização do diagrama de comunicação L4 do SDD que a dupla escreveu. O
  Passo 2 exige entender o que ele grava para que o Passo 3 funcione.
- **`cURL` cobre o objetivo pedagógico declarado.** "Inspecionar o tráfego"
  significa ver verbo, status, headers e a chegada dos eventos do SSE. O
  `curl -v` mostra os três primeiros com anotação de camada, e o `curl -N` mostra
  o quarto ao vivo. Nada disso exige instalação: o devcontainer já traz o cURL.
- **Exigência numérica preserva o rigor.** Trocar o relatório por três medições
  com valor numérico obrigatório evita o texto genérico que um relatório livre
  costuma produzir, e é verificável em segundos na revisão.
- **Passagem por arquivo é previsível.** Um segundo canal de socket entre Python
  e Node acrescentaria uma fonte de falha (porta ocupada, ordem de inicialização,
  reconexão) que consumiria o tempo do laboratório em depuração de infraestrutura,
  não em protocolo.

## Riscos conhecidos

| Risco | Mitigação |
|---|---|
| O aluno chega ao CP1 sem nunca ter escrito um socket | O CP1 cobre sockets. O coletor entregue é comentado linha a linha e o Passo 2 obriga a lê-lo; a Aula 03 volta a mexer nos dois serviços ao conteinerizá-los |
| A passagem por arquivo passar a impressão de que é assim que se faz em produção | Declarado como simplificação no README, no slide do Passo 2 e nesta ADR, com o ponto de substituição nomeado (Aula 07) |
| Sair o Wireshark e a disciplina perder a leitura de pacote | O objetivo de aprendizagem que ele atendia, inspecionar o tráfego de uma requisição, continua na Aula 02 e é cumprido com `cURL`. A leitura de pacote em si deixa de ser conteúdo da disciplina, e a matriz do `PLANO_DE_ENSINO.md` registra a exceção em vez de afirmar que nada foi removido |
| O aluno completar os TODO sem entender e o PR ser aprovado por camaradagem | `http-l7/verificar.mjs` checa os sete critérios objetivamente e a revisão exige dois comentários em linha com efeito e sugestão |
| Divergência entre o material e os documentos de planejamento | Resolvida em 30/07/2026: `PLANO_DE_ENSINO.md`, `PLANEJAMENTO_AULA_A_AULA.md`, `aulas-1sem/SKILL.md` e `tools/scaffold_labs.py` foram alinhados, e o Wireshark não aparece mais em nenhum documento do acervo |

## Consequências

**Positivas**
- O laboratório cabe em 60 minutos com folga para a revisão cruzada, que é a
  parte mais nova para a turma.
- O entregável fica objetivamente verificável: `verificar.mjs` responde sim ou
  não para sete critérios.
- Nenhuma instalação é necessária além do que o devcontainer já traz.

**Negativas**
- O aluno não escreve socket em nenhum laboratório do Módulo I, apenas lê.
- O acoplamento por arquivo entre os dois serviços precisa ser desfeito na Aula
  07, o que gera trabalho de reescrita no material daquela aula.
- Os documentos de planejamento passam a divergir do material entregue enquanto
  não forem atualizados.

## ADRs relacionadas

- ADR-001: Votação ao vivo nos quizzes em serviço apartado (o serviço proposto
  lá usa SSE, o tema desta aula).
