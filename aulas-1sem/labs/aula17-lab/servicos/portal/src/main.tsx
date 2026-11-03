/**
 * Ponto de entrada do Portal do Cliente.
 *
 * CONGELADO. Não é tarefa da Aula 10.
 *
 * `createRoot` é a API de raiz do React 18 em diante, e o `StrictMode` é
 * deliberado: em desenvolvimento ele monta cada componente duas vezes de
 * propósito, para expor efeito sem limpeza. Se o seu `useEffect` do TODO-4
 * disparar duas requisições no navegador e uma só nos testes, não é bug do
 * React: é o StrictMode mostrando que falta a função de limpeza.
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import { App } from './App';
import './estilo.css';

createRoot(document.getElementById('raiz')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
