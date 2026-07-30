const express = require('express');
const jwt = require('jsonwebtoken');

const app = express();
app.use(express.json());

const SECRET_KEY = 'super-secret-logitech-key-do-not-share';

// Fake Database de Usuários (Mini Mundo)
const users = [
  { id: 1, username: 'driver_joao', password: '123', role: 'DRIVER' },
  { id: 2, username: 'analyst_maria', password: '123', role: 'ANALYST' }
];

// Rota de Login (Gera JWT)
app.post('/login', (req, res) => {
  const { username, password } = req.body;
  const user = users.find(u => u.username === username && u.password === password);

  if (!user) {
    return res.status(401).json({ error: 'Credenciais inválidas' });
  }

  // Gera o token JWT com payload { id, username, role }
  const token = jwt.sign(
    { id: user.id, username: user.username, role: user.role },
    SECRET_KEY,
    { expiresIn: '1h' }
  );

  res.json({ token });
});

// Middleware de Autenticação (Verifica JWT)
function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Formato: Bearer <token>

  if (!token) return res.status(401).json({ error: 'Acesso negado: Token não fornecido.' });

  jwt.verify(token, SECRET_KEY, (err, user) => {
    if (err) return res.status(403).json({ error: 'Acesso negado: Token inválido ou expirado.' });
    req.user = user; // Salva infos do user na req
    next();
  });
}

// Middleware de Autorização (RBAC - Verifica Role)
function requireRole(role) {
  return (req, res, next) => {
    if (req.user.role !== role) {
      return res.status(403).json({ error: `Acesso negado: Necessário perfil de ${role}.` });
    }
    next();
  };
}

// Rota Pública
app.get('/', (req, res) => {
  res.send('API LogiTech - Bem-vindo!');
});

// Rota Restrita (Qualquer usuário logado)
app.get('/me', authenticateToken, (req, res) => {
  res.json({ message: 'Seus dados', user: req.user });
});

// Rota RBAC: Apenas ANALYST
app.get('/admin/dashboard', authenticateToken, requireRole('ANALYST'), (req, res) => {
  res.json({ message: 'Dashboard da Frota Inteira - Acesso concedido!' });
});

app.listen(3000, () => {
  console.log('Servidor rodando em http://localhost:3000');
});
