# Evidências da Aula 15

Preencha cada marcador com o que **saiu na sua máquina**, e não com o que
deveria ter saído. Valor fabricado engana a correção, não o `verificar.py`.

Formato: `MARCADOR: valor`, uma linha por marcador. O verificador procura pelo
nome do marcador e recusa a palavra `PREENCHER`.

---

## Passo 1, o reconhecimento

ONDE_MEDI: PREENCHER (máquina, sistema, Codespace ou local, e quanta memória)

MODELO_LOCAL: PREENCHER (o que `ollama list` mostrou, com a tag)

---

## Passo 2, o ataque com o guardrail desligado

Este bloco é o "antes". Ele é preenchido com `LOGITECH_GUARDRAILS_ATIVOS=false`,
e **precisa** ser preenchido antes do Passo 3: defesa sem ataque prévio vira
ritual, e é a razão de o interruptor existir.

INJECAO_ANTES: PREENCHER (cole a resposta que o modelo deu ao ataque 01, na íntegra, em uma linha)

VAZOU_O_CODIGO: PREENCHER (sim ou não, e qual código apareceu)

STATUS_HTTP_ANTES: PREENCHER (o código HTTP que o gateway devolveu ao ataque 01)

INJECAO_INDIRETA_ANTES: PREENCHER (cole a resposta do RAG ao ataque 06, e diga qual instrução do documento ela obedeceu)

DE_QUAL_DOCUMENTO: PREENCHER (qual arquivo de `contratos/` estava envenenado, e qual cláusula)

TENTATIVAS_ATE_A_INJECAO_FUNCIONAR: PREENCHER (quantas vezes você chamou até obter uma resposta comprometida; o ataque não é determinístico)

PII_ANTES: PREENCHER (a resposta ao ataque 07, com os dados sensíveis como saíram)

---

## Passo 3, a defesa ligada

INJECAO_DEPOIS: PREENCHER (o corpo que o gateway devolveu ao ataque 01 com o guardrail ligado)

STATUS_HTTP_DEPOIS: PREENCHER (o código HTTP; a ADR-009 diz qual deve ser)

REGRA_QUE_DISPAROU: PREENCHER (o campo `regra` do corpo do 422)

LEGITIMA_CONTINUA_PASSANDO: PREENCHER (o status HTTP do ataque 05, o de controle, com o guardrail ligado)

PII_DEPOIS: PREENCHER (a resposta ao ataque 07 com o guardrail ligado, com as três máscaras visíveis)

MASCARAMENTOS_NA_METRICA: PREENCHER (o valor de `guardrail.mascaramentos_saida` em `GET /v1/metricas`)

RECUSAS_NA_METRICA: PREENCHER (o valor de `guardrail.recusas_entrada` e o conteúdo de `recusas_por_regra`)

---

## Passo 3, furando o próprio filtro

O item mais importante do laboratório. Um filtro que ninguém tentou furar não
é defesa: é uma opinião sobre ataques.

FORMULACAO_QUE_PASSOU: PREENCHER (uma formulação sua que o SEU filtro deixou passar; escreva-a inteira)

O_QUE_ELA_CONSEGUIU: PREENCHER (o que o modelo respondeu a ela: vazou algo, mudou de comportamento, ou nada)

POR_QUE_O_FILTRO_NAO_PEGOU: PREENCHER (que propriedade do texto fez as suas regras não casarem)

O_QUE_ISSO_PROVA: PREENCHER (em uma frase sua: o que o filtro de entrada protege e o que ele não protege)

---

## Passo 4, a injeção indireta

PARAGRAFOS_REMOVIDOS: PREENCHER (o campo `guardrail.paragrafos_removidos` da resposta do RAG ao ataque 06)

INJECAO_INDIRETA_DEPOIS: PREENCHER (a resposta do RAG ao ataque 06 com a sanitização ligada)

RESPOSTA_LEGITIMA_SOBREVIVEU: PREENCHER (a resposta continuou correta sobre o reajuste? cole a frase que prova)

SO_DELIMITADOR_BASTA: PREENCHER (rode com delimitador e aviso, mas sem remover parágrafo, e diga em quantas de 3 tentativas o modelo ainda obedeceu)

---

## Passo 5, o Trivy

DATA_DA_VARREDURA: PREENCHER (data em que você rodou `./varrer.sh`; o banco de CVE muda toda semana)

CVES_CRITICAL_ANTES: PREENCHER (quantas CRITICAL nas três imagens do projeto, antes de corrigir)

CVES_HIGH_ANTES: PREENCHER (quantas HIGH nas três imagens do projeto, antes de corrigir)

QUAL_ERA_A_CRITICAL: PREENCHER (o identificador CVE, o pacote e a versão)

DE_ONDE_ELA_VEIO: PREENCHER (o `PkgPath` que o relatório mostrou, e o que esse caminho diz)

O_CONTAINER_USA_ESSE_PACOTE: PREENCHER (sim ou não, e como você concluiu)

CVES_CRITICAL_DEPOIS: PREENCHER (precisa ser zero nas três imagens do projeto)

CVES_HIGH_DEPOIS: PREENCHER (quantas HIGH sobraram nas três imagens do projeto)

O_QUE_MUDEI_NO_DOCKERFILE: PREENCHER (em uma frase, o que você fez e por que não foi só trocar a tag da base)

TAMANHO_ANTES_E_DEPOIS: PREENCHER (`docker images` das três imagens, antes e depois)

---

## Passo 6, as exceções

CVES_HIGH_ACEITAS: PREENCHER (quantas exceções você registrou em docs/EXCECOES.md)

IMAGEM_DAS_EXCECOES: PREENCHER (de qual imagem elas vieram, e por que ela é tratada diferente)

DIFERENCA_PARA_IGNORE_UNFIXED: PREENCHER (rode a varredura com `--ignore-unfixed`, compare os totais e diga o que sumiu do relatório e o que sumiu da imagem)

---

## Geral

USEI_O_RESGATE: PREENCHER (não, ou a partir de qual passo. Sem penalidade automática: é informação para a correção)
