# Laboratório Prático - Aula 01
## Discipline: Microservice and Web Engineering & IT Services
**Prof. José Romualdo | FIAP Systems of Information**

### Case: LogiTech Enterprise AI Platform (Fase 1 - Telemetria de Frota)

Neste laboratório, a sua dupla irá configurar os documentos de requisitos (**PRD** e **SDD**) e construir um serviço de recepção de telemetria em Python operando na camada de transporte L4 (Sockets TCP e UDP).

---

### Estrutura do Laboratório

```
aula01-lab/
├── docs/
│   ├── PRD.md            # Product Requirement Document (Visão e Casos de Uso)
│   └── SDD.md            # System Design Document (DDD Bounded Contexts & Arquitetura)
├── server_telemetry.py   # Servidor de Sockets TCP (porta 8080) e UDP (porta 8081)
├── client_telemetry.py   # Script cliente simulando envio de GPS/temperatura de um caminhão
└── README.md
```

---

### Como Executar

1. **Iniciar o Servidor de Telemetria:**
```bash
python3 server_telemetry.py
```

2. **Em outro terminal, simular o envio de dados via cliente:**
```bash
python3 client_telemetry.py
```

3. **Verificar os commits no Git:**
```bash
git add .
git commit -m "feat(telemetry): add TCP/UDP socket server and PRD/SDD docs"
```
