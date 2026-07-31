# `servicos/`: o que veio das aulas anteriores

**Nada aqui é tarefa da Aula 05.** Este diretório existe para que a plataforma
LogiTech continue completa no seu fork, mesmo que você tenha faltado a alguma
aula, e para que a Aula 07 tenha o que orquestrar.

| Diretório | O que é | Nasceu na |
|---|---|---|
| `coletor/` | Coletor de telemetria em Python, escuta UDP na 8081 | Aula 02, conteinerizado na Aula 03 |
| `painel/` | Painel de rastreamento em Node, HTTP e SSE na 3000 | Aula 02, conteinerizado na Aula 03 |

Os dois estão **congelados**: não edite, não refatore, não aplique SOLID neles
hoje. O laboratório desta noite acontece em `pedidos/` (Java) e `faturamento/`
(C#).

O painel aparece aqui com o nome `painel`, que é o nome do serviço no contrato
da plataforma (ADR-006). Na Aula 03 ele se chamava `gateway`: é o mesmo código.

Na Aula 07, os quatro serviços mais o cálculo de frete, as notificações, o
PostgreSQL e o AI Gateway sobem juntos por um único `docker compose up`. É lá
também que o painel deixa de ler o arquivo compartilhado e passa a consumir
`GET /telemetria` na porta 8082 do coletor.
