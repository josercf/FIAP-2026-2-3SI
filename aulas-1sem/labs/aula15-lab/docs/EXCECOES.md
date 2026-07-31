# Exceções de segurança aceitas

TODO-6. Este arquivo é o entregável do Passo 6.

## Para que ele existe

A ADR-009, seção 7, fixa o critério do laboratório: **zero CRITICAL nas imagens
que o projeto constrói**. HIGH é outra história. Parte tem correção publicada, e
essa você aplica no Passo 5. Parte não tem, e aí só existem três caminhos:

| Caminho | O que acontece |
|---|---|
| Esconder com `--ignore-unfixed` | O relatório fica verde e a imagem continua igual. Ninguém mais volta ao assunto, porque não há registro de que houve assunto |
| Bloquear a esteira até alguém corrigir | A esteira fica vermelha por semanas, o time aprende a ignorar vermelho, e o próximo achado real passa junto |
| **Aceitar por escrito, com prazo** | O risco fica nomeado, com dono e data de reavaliação. É o que times reais fazem, e é o que este arquivo é |

A diferença entre o primeiro e o terceiro não é técnica: o comando até pode ser
o mesmo. A diferença é que aqui existe um texto que alguém assinou, com uma data
em que ele volta à mesa.

## Regra deste laboratório

Registre **no mínimo três** exceções, e só de achados que o relatório do Trivy
marca **sem versão corrigida publicada** (`FixedVersion` vazio, ou `Status`
`affected` ou `fix_deferred`). Rode `python3 resumo_trivy.py` para vê-los na
coluna `S/COR`.

Achado com correção publicada **não** entra aqui. Ele entra no Passo 5. Aceitar
por escrito o que você poderia ter corrigido em duas linhas é a forma educada de
não corrigir, e o `verificar.py` reprova essa tentativa: ele confere no relatório
se o CVE que você registrou tem mesmo `FixedVersion` vazio.

## Formato

Um bloco por CVE, com os sete campos. O verificador lê estes nomes exatos.

```
## CVE-0000-00000

IMAGEM: nome:tag exatamente como aparece no relatório
PACOTE: nome e versão instalada
SEVERIDADE: HIGH
STATUS_NO_TRIVY: affected, fix_deferred ou will_not_fix
DATA_DA_ACEITACAO: AAAA-MM-DD
MOTIVO: por que esta plataforma não é exposta por este achado, ou por que a
        correção não está ao alcance do time. Uma frase técnica, não "risco
        baixo"
REAVALIAR_EM: AAAA-MM-DD, depois da data de aceitação
```

O `MOTIVO` é o campo que separa análise de carimbo. Duas perguntas que ajudam a
escrevê-lo:

- O caminho vulnerável é alcançável a partir de alguma entrada da plataforma? Um
  utilitário de linha de comando que nenhum processo do container executa é
  diferente de uma biblioteca no caminho da requisição.
- Se não é alcançável hoje, o que precisaria mudar para passar a ser? Essa
  resposta é o que a reavaliação vai conferir.

---

## Exemplo preenchido, para você ver o nível esperado

Este bloco é modelo e **não conta** para o mínimo de três. Apague-o ou deixe-o:
o verificador ignora exceções cujo CVE não aparece nos seus relatórios.

```
## CVE-0000-00000

IMAGEM: exemplo/base:1.0
PACOTE: libexemplo 1.2.3-r0
SEVERIDADE: HIGH
STATUS_NO_TRIVY: fix_deferred
DATA_DA_ACEITACAO: 2026-11-10
MOTIVO: a falha exige que um processo do container abra arquivo comprimido
        recebido pela rede. Nenhum dos três serviços descomprime entrada de
        usuário, e a biblioteca só é carregada pelo gerenciador de pacotes do
        sistema, que não roda em tempo de execução. A distribuição marcou a
        correção como adiada e não há versão publicada.
REAVALIAR_EM: 2026-12-10
```

---

## As suas exceções

<!-- TODO-6: escreva os seus blocos abaixo desta linha. -->
