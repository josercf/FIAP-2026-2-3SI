# Lab Aula 16 - Integração End-to-End (Simulado GS)

Neste simulado final, você colocará no ar a arquitetura base para o Hackathon (Global Solution):

1. **Auth Service (Node.js)** na porta 3000.
2. **AI Service (Python/FastAPI)** na porta 8000.

O AI Service precisa se comunicar com o Auth Service via rede interna do Docker (usando o nome do container `auth-api`) para validar o token do usuário.

## Passo a Passo

### 1. Subindo a infraestrutura E2E
Na raiz onde está o `docker-compose.yml`, rode:
```bash
docker-compose up --build
```
Isso fará o build das duas imagens e as conectará na rede `logitech-net`.

### 2. Testando (Falha de Autenticação)
Tente fazer uma pergunta para a IA sem o token correto:
```bash
curl -X POST "http://localhost:8000/ask-ai?prompt=Status%20dos%20caminhoes" -H "Authorization: Bearer token-falso"
```
Você deverá receber `{"detail":"Invalid Token"}`.

### 3. Testando (Sucesso)
Utilize o token válido (`super-secret-token-123`):
```bash
curl -X POST "http://localhost:8000/ask-ai?prompt=Status%20dos%20caminhoes" -H "Authorization: Bearer super-secret-token-123"
```
A API Python fará um POST interno para o Node.js. Como o token é válido, o Node.js retorna 200, e a Python devolve a resposta da IA!

**Desafio:** Modifique o código para que o AI Service recuse atender usuários que não tenham a role `ANALYST` (que é retornada pelo Node.js).
