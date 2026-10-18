/**
 * A casca do Portal do Cliente da LogiTech.
 *
 * CONGELADO. Não é tarefa da Aula 10.
 *
 * Só faz duas coisas: guarda qual pedido está sendo rastreado e monta os
 * dois componentes que vocês escrevem. Toda a lógica de rede mora dentro
 * deles, e é por isso que este arquivo não tem teste próprio.
 */

import { useState } from 'react';

import { CotacaoFrete } from './componentes/CotacaoFrete';
import { RastreioPedido } from './componentes/RastreioPedido';

const PEDIDOS_DA_BASE = ['PED-1001', 'PED-1002', 'PED-1003', 'PED-1004'];

export function App() {
  const [pedidoId, setPedidoId] = useState(PEDIDOS_DA_BASE[0]);

  return (
    <main>
      <header>
        <h1>LogiTech | Portal do Cliente</h1>
        <p>Rastreie a sua carga e simule o frete da próxima.</p>
      </header>

      <nav aria-label="Pedidos da sua conta">
        {PEDIDOS_DA_BASE.map((id) => (
          <button
            key={id}
            type="button"
            className={id === pedidoId ? 'aba ativa' : 'aba'}
            onClick={() => setPedidoId(id)}
          >
            {id}
          </button>
        ))}
      </nav>

      <div className="colunas">
        <RastreioPedido pedidoId={pedidoId} />
        <CotacaoFrete />
      </div>

      <footer>
        <p>
          Pedidos em http://localhost:8080 e frete em http://localhost:8000.
          Se a tela ficar vazia, abra o console do navegador: erro de CORS não
          aparece aqui.
        </p>
      </footer>
    </main>
  );
}
