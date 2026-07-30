const express = require('express');
const app = express();
app.use(express.json());

// Simulando um validador de token (Dummy)
app.post('/validate', (req, res) => {
    const { token } = req.body;
    if (token === 'super-secret-token-123') {
        res.json({ valid: true, role: 'ANALYST' });
    } else {
        res.status(401).json({ valid: false });
    }
});

app.listen(3000, () => {
    console.log('Auth Service running on port 3000');
});
