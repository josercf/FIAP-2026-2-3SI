# Os sete payloads

Cada arquivo é o corpo de uma requisição, pronto para `curl -d @arquivo`.

| Arquivo | Vai para | Família OWASP | O que exercita |
|---|---|---|---|
| `01-direto-revogacao.json` | gateway | LLM01 | A forma clássica: mandar esquecer as instruções |
| `02-direto-exfiltracao.json` | gateway | LLM01 e LLM02 | Pedir o próprio prompt de sistema de volta |
| `03-direto-troca-de-papel.json` | gateway | LLM01 | Fingir um marcador de sistema e redefinir o papel |
| `04-direto-em-ingles.json` | gateway | LLM01 | O mesmo ataque em outro idioma, contra filtro escrito só em português |
| `05-legitima-de-controle.json` | gateway | nenhuma | **O controle.** Pergunta honesta de cliente, que precisa continuar respondida |
| `06-indireto-pelo-rag.json` | rag | LLM01 indireta | Pergunta legítima cuja resposta atravessa um documento envenenado |
| `07-pii-pelo-rag.json` | rag | LLM02 | Pergunta legítima cuja resposta carrega CPF, cartão e placa |

## O quinto arquivo é o mais importante

`05-legitima-de-controle.json` não é ataque, e é o que separa um guardrail de
um teatro de segurança. Filtro que recusa tudo tem taxa de detecção perfeita e
serventia zero.

O `verificar.py` roda **oito** perguntas legítimas contra o seu filtro e reprova
o critério se qualquer uma for recusada. Isso é deliberado: numa operação real,
o custo de recusar cliente honesto é maior do que o de deixar passar a
milésima variação de um ataque, porque o primeiro derruba o número de
atendimento resolvido e o segundo tem a segunda camada, o mascaramento de
saída, atrás dele.

## Os dois últimos não têm nada de malicioso

`06` e `07` são perguntas que qualquer atendente da LogiTech faria em um dia
comum. Não há ataque nelas. O ataque está **no acervo**, e chegou lá antes.

É isso que separa a injeção indireta da direta: na direta você inspeciona a
entrada e pode recusar. Na indireta a entrada é irrepreensível, e quem carrega
a carga é o documento que o seu próprio sistema foi buscar.

## Como usar

```bash
# direto no gateway
curl -s --connect-timeout 5 --max-time 180 -X POST http://localhost:4000/v1/chat/completions \
  -H 'Content-Type: application/json' -H 'X-Servico: laboratorio' \
  -d @ataques/01-direto-revogacao.json | python3 -m json.tool

# pelo RAG
curl -s --connect-timeout 5 --max-time 180 -X POST http://localhost:8010/api/v1/rag/perguntar \
  -H 'Content-Type: application/json' \
  -d @ataques/06-indireto-pelo-rag.json | python3 -m json.tool
```

## Escreva o oitavo

O Passo 3 pede que você invente uma formulação que **passe** pelo seu próprio
filtro e ainda assim consiga alguma coisa. Grave-a aqui como
`08-formulacao-que-passou.json` e registre em `docs/EVIDENCIAS.md`.

Um filtro que ninguém tentou furar não é defesa: é uma opinião sobre ataques.
