import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['tests/**/*.test.ts'],
    environment: 'node',
    // Cada arquivo de teste corresponde a uma lacuna do laboratório, e o
    // `verificar.py` roda um arquivo por critério. Manter o relatório por
    // arquivo facilita ler qual lacuna ainda está aberta.
    reporters: ['default'],
  },
});
