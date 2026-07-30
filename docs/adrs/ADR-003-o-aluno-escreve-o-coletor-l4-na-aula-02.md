# ADR-003: O aluno escreve o coletor L4 na Aula 02

- **Data:** 2026-07-30
- **Status:** Aceita
- **Decisores:** Prof. José Romualdo da Costa Filho
- **Supersede:** a **decisão 1** da ADR-002. As demais decisões da ADR-002 seguem válidas.

## Contexto

Dois problemas apareceram na revisão do material da Aula 02, e o segundo estava
escondido atrás do primeiro.

**1. O material afirmava algo falso.** O slide do Desafio do Mini Mundo trazia um
quadro intitulado "O que temos depois da Aula 01" dizendo que existia "um
processo Python escutando datagramas na porta 8081". Não existia: a Aula 01
entregou apenas `docs/PRD.md` e `docs/SDD.md`. O erro contradizia o slide
anterior do próprio deck, que dizia corretamente que a entrega da Aula 01 foi a
especificação, e apareceria em sala.

**2. O aluno chegaria ao CP1 sem nunca ter escrito um socket.** Isso já estava
registrado como risco conhecido na ADR-002, com a mitigação "o CP1 cobre
sockets". A mitigação não se sustenta: o CP1, em 25/08, é uma **avaliação prática
individual** cujo escopo declarado inclui Sockets TCP/UDP. Cobrar em prova o que
nunca foi praticado não é mitigação, é o próprio risco.

Corrigir só o texto do slide resolveria o problema visível e deixaria o segundo
de pé.

## Decisão

O aluno passa a **completar** o coletor de sockets L4 a partir de um esqueleto
com TODO, em vez de recebê-lo pronto.

O esqueleto segue o mesmo contrato pedagógico que já funciona em
`http-l7/server.js`: parte pronta como modelo, parte como tarefa.

- **Pronto:** o listener **TCP 8080** inteiro, que é o modelo; o simulador da
  frota; os utilitários `agora_iso`, `anexar` e `validar_posicao`; o `main` com
  encerramento limpo.
- **Tarefa:** os quatro TODO de `escutar_udp`, que são criar o socket UDP e fazer
  bind, o laço com `recvfrom`, a decodificação do datagrama e a gravação em
  `data/telemetria.jsonl`.

Entra `sockets-l4/verificar.py`, sem dependências, com cinco critérios
(CA-L4-01 a CA-L4-05), para que o Passo 2 não seja o único do laboratório sem
verificação objetiva.

## Motivações

- **A correção honesta do slide exige a mudança.** Dizer "a Aula 01 entregou só a
  especificação" e em seguida entregar o coletor pronto deixaria a pergunta óbvia
  no ar: então quem escreveu isto? A coerência da espiral pede que o que foi
  especificado seja implementado por quem especificou.
- **O CP1 cobra socket em prova individual.** Praticar antes deixa de ser
  desejável e passa a ser condição.
- **Completar não é o mesmo que escrever do zero.** Escrever do zero custaria
  cerca de 25 minutos e estouraria a janela. Completar quatro TODO com um modelo
  ao lado custa cerca de 12, e ainda obriga a ler o código pronto para imitá-lo,
  que era o valor que a ADR-002 buscava ao entregar o coletor.
- **UDP é a tarefa e TCP é o modelo, de propósito.** O UDP alimenta o Passo 3:
  um TODO malfeito aparece na hora como painel vazio, e não como erro silencioso.

## Orçamento de tempo

O Bloco 2 vai de 21h20 a 22h50, 90 minutos, dos quais cerca de 15 são dos
Quizzes #2 e #3. Restam cerca de 75 minutos.

| Passo | ADR-002 | Agora |
|---|---|---|
| 1. Fork e branch | 5 | 5 |
| 2. Coletor L4 | 8, só subir | **12, completar e subir** |
| 3. Servidor HTTP/SSE | 27 | 27 |
| 4. Medições com cURL | 10 | 10 |
| 5. Pull Request cruzado | 10 | 10 |
| **Total** | **60** | **72** |

## Riscos conhecidos

| Risco | Mitigação |
|---|---|
| A dupla travar no TODO 1 e perder o Passo 3 inteiro | O TCP pronto é o modelo linha a linha, e a diferença é nomeada no comentário: `SOCK_DGRAM` no lugar de `SOCK_STREAM`, sem `listen`. O `verificar.py` diz qual critério falhou em vez de deixar a dupla adivinhando |
| Os 72 minutos estourarem na prática | Sobram 3 minutos dos 75, o que é pouco. Se a turma atrasar, o corte previsto é a segunda metade do Passo 4, que são medições independentes entre si, e não o Passo 5 |
| O aluno copiar o TCP sem entender e o UDP não funcionar | O `verificar.py` manda datagrama corrompido de propósito: quem só copiou o TCP não trata a exceção e reprova no CA-L4-04 e no CA-L4-05 |
| O gabarito do coletor vazar para o aluno | `gabarito/` fica só na cópia do professor, em `aulas-1sem/labs/`, e não vai para o repositório que o aluno forka. Continua exposto a quem navegue pelo acervo, o que é a pendência já aberta sobre o gabarito |

## Consequências

**Positivas**
- O material deixa de afirmar algo falso, e a espiral fica coerente: especifica na
  01, implementa na 02.
- O aluno escreve socket antes de ser avaliado em socket.
- O Passo 2 ganha verificação objetiva, que antes não tinha.

**Negativas**
- O laboratório passa de 60 para 72 minutos, e a folga do Bloco 2 cai para 3
  minutos.
- O material da Aula 02 precisou ser retrabalhado depois de pronto e publicado.
- O `gabarito/` cresce e passa a conter também o coletor, aumentando o que estaria
  exposto caso a pendência do gabarito não seja resolvida.

## ADRs relacionadas

- **ADR-002**, cuja decisão 1 esta ADR supersede. Seguem válidas dela: a saída do
  Wireshark, a troca do relatório de captura por três medições numéricas com
  `cURL`, e a passagem por arquivo entre o coletor e o gateway como simplificação
  a ser desfeita na Aula 07.
- **ADR-001**, votação ao vivo nos quizzes.
