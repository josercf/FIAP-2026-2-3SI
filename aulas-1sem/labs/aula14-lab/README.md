# Lab Aula 14 - Segurança Web Enterprise (JWT & RBAC)

Neste laboratório, você implementará um fluxo de Autenticação (JWT) e Autorização (RBAC) para a API da LogiTech.

## Passo a Passo

### 1. Preparação (Git Worktrees)
Para não misturar código de segurança inacabado na `main`, usaremos worktrees:

```bash
# Na pasta do seu projeto principal
git worktree add ../logitech-security feature/auth-jwt
cd ../logitech-security
```

### 2. Instalação e Execução
Na pasta onde estão os arquivos deste lab:

```bash
npm install
npm start
```
O servidor iniciará na porta 3000.

### 3. Testando as Rotas

**A. Sem Token (Erro 401)**
```bash
curl http://localhost:3000/me
```

**B. Fazendo Login como Motorista**
```bash
curl -X POST http://localhost:3000/login -H "Content-Type: application/json" -d '{"username":"driver_joao","password":"123"}'
```
Copie o `token` retornado.

**C. Acessando Perfil**
```bash
curl http://localhost:3000/me -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**D. Acessando Rota de Analista (RBAC - Erro 403)**
Como `driver_joao`, você NÃO pode acessar o dashboard:
```bash
curl http://localhost:3000/admin/dashboard -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**E. Fazendo Login como Analista**
Faça login com `analyst_maria` (senha `123`), pegue o novo token e tente a rota `/admin/dashboard` novamente. O acesso será concedido!
