# Laboratório Prático - Aula 01
## Discipline: Microservice and Web Engineering & IT Services
**Prof.º José Romualdo | FIAP Sistemas de Informação**

### Case: LogiTech Enterprise AI Platform (Fase 1 - Requisitos & Telemetria L4)

Neste laboratório, a sua dupla irá configurar a governança de requisitos do produto (**PRD** e **SDD**) e construir o primeiro serviço de telemetria em Python operando na camada de transporte L4 (Sockets TCP e UDP).

---

### Passo a Passo da Atividade Prática

#### Passo 1: Configuração do GitHub & Repositório
1. Caso ainda não possuam, crie uma conta em [github.com](https://github.com).
2. Um dos integrantes da dupla deve criar um repositório público ou privado com o nome:
   `fiap-2026-2-3si-duplaXX` (substitua XX pelo número da sua dupla).
3. Adicionar o colega de dupla e o professor como colaboradores no repositório.

#### Passo 2: Construção do PRD & SDD usando IA / SLM Local
1. Utilizar um modelo local de IA (ex: **Qwen** via Ollama ou LM Studio) ou a skill da nossa biblioteca `skills/prd/SKILL.md` (disponível em `https://github.com/josercf/skill-library.git`).
2. Criar a pasta `docs/` e gerar os artefatos:
   - `docs/PRD.md`: Visão do produto, casos de uso de telemetria e requisitos não-funcionais.
   - `docs/SDD.md`: Mapeamento do Bounded Context de Telemetria e modelo de comunicação L4.

#### Passo 3: Desenvolvimento do Servidor de Sockets (L4 OSI)
1. Escrever o arquivo `server_telemetry.py` em Python:
   - **Porta 8080 (TCP):** Recepção de confirmações de entregas de frete (garantia de entrega).
   - **Porta 8081 (UDP):** Recepção de datagramas de GPS e velocidade de caminhões (alta velocidade).
2. Escrever o cliente `client_telemetry.py` para simular os envios do caminhão.

#### Passo 4: Git Commits & Submissão
1. Fazer o commit seguindo a convenção de **Conventional Commits**:
   ```bash
   git add .
   git commit -m "feat(telemetry): add TCP/UDP socket server and PRD/SDD documentation"
   git push origin main
   ```
2. Submeter a URL do repositório no formulário institucional de entregas (Microsoft Forms).

---

### Estrutura dos Arquivos do Laboratório

```
aula01-lab/
├── docs/
│   ├── PRD.md            # Product Requirement Document (Gerado via Skill/SLM)
│   └── SDD.md            # System Design Document (DDD Bounded Context)
├── server_telemetry.py   # Servidor Sockets TCP (porta 8080) e UDP (porta 8081)
├── client_telemetry.py   # Cliente simulador de envio de GPS/temperatura
└── README.md
```
