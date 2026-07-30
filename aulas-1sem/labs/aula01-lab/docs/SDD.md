# SDD - LogiTech Enterprise AI Platform
## System Design Document

### 1. Arquitetura Geral do Sistema
A plataforma adota uma arquitetura em camadas orientada a microsserviços poliglotas e componentes conteinerizados.

### 2. Mapeamento de Bounded Contexts (DDD)
- **Contexto de Telemetria & Frota:** Captura dados brutos na camada L4 (Sockets TCP/UDP) e expõe streaming HTTP/SSE.
- **Contexto de Pedidos & Estoque:** Desenvolvido em Java (Spring Boot) com persistência em banco relacional.
- **Contexto de Faturamento & Notas:** Desenvolvido em C# (.NET Core) focado em regras fiscais.
- **Contexto de Notificações & Cálculo:** Desenvolvido em Node.js e Python (FastAPI).
- **Contexto de Atendimento AI (AI Gateway & MCP):** Roteador de LLMs, busca RAG e Servidor MCP.

### 3. Diagrama de Comunicação L4 (Aula 01)
```
[Sensores de GPS (UDP)] ──> Porta 8081 ──> [server_telemetry.py]
[App do Motorista (TCP)] ──> Porta 8080 ──> [server_telemetry.py]
```
