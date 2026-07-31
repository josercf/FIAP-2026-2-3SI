/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Porta 5173 fixada pela ADR-008. `strictPort` é deliberado: se a porta
// estiver ocupada o Vite falha em vez de subir em outra, porque o CORS dos
// serviços de backend libera exatamente esta origem.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/preparaTestes.ts'],
    css: false,
  },
});
