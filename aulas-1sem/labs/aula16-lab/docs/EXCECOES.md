# Vulnerabilidades HIGH aceitas

Uma linha por CVE que a equipe decidiu aceitar, com data e motivo.

O critério do laboratório é **zero CRITICAL**. HIGH é registrado, justificado e
aceito quando vem da imagem base sem correção publicada. Aceitar HIGH com
justificativa escrita é o que times reais fazem; exigir zero HIGH faria alguém
inventar número para fechar a conta, e sumir com o HIGH por
`--ignore-unfixed` silencioso é a pior das três saídas.

| Imagem | CVE | Pacote | Motivo de aceitar | Quem decidiu | Data | Revisar em |
|---|---|---|---|---|---|---|
| PREENCHER | PREENCHER | PREENCHER | PREENCHER | PREENCHER | PREENCHER | PREENCHER |

## O que NÃO é motivo aceitável

- "não deu tempo"
- "o serviço não usa esse pacote" sem dizer como você confirmou
- "a CVE parece exagerada"

## O que é motivo aceitável

- não há versão corrigida publicada para a imagem base, e a troca de base foi
  avaliada e tem custo maior que o risco (diga qual)
- o pacote não é alcançável pelo caminho de execução do serviço, e você
  verificou como (diga como)
- há mitigação em outra camada, e ela está descrita (diga qual)
