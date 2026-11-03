/**
 * A casca do Portal do Cliente da LogiTech.
 *
 * CONGELADO. Não é tarefa da Aula 16.
 *
 * O que mudou em relação à Aula 10: a casca passou a ter sessão. Ela conclui o
 * fluxo PKCE na volta do Keycloak, mostra quem entrou e com que papéis, e só
 * monta as telas de negócio depois disso.
 *
 * Repare no que a guarda de rota daqui **não** é: ela não autoriza nada. Se
 * alguém apagar este `if` pelo console do navegador, as telas aparecem e as
 * chamadas continuam voltando 401, porque quem autoriza é o backend conferindo
 * a assinatura do token. Guarda de rota no frontend é conforto de navegação.
 */

import { useEffect, useState } from 'react';

import { CotacaoFrete } from './componentes/CotacaoFrete';
import { RastreioPedido } from './componentes/RastreioPedido';
import { concluirEntrada, entrar, sair, sessaoAtual, type Sessao } from './auth/pkce';

const PEDIDOS_DA_BASE = ['1001', '1002', '1003', '1004'];

export function App() {
  const [pedidoId, setPedidoId] = useState(PEDIDOS_DA_BASE[0]);
  const [sessao, setSessao] = useState<Sessao | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    concluirEntrada()
      .then((nova) => setSessao(nova ?? sessaoAtual()))
      .catch((problema: Error) => setErro(problema.message))
      .finally(() => setCarregando(false));
  }, []);

  if (carregando) {
    return (
      <main>
        <p>Conferindo a sessão...</p>
      </main>
    );
  }

  return (
    <main>
      <header>
        <h1>LogiTech | Portal do Cliente</h1>
        <p>Rastreie a sua carga e simule o frete da próxima.</p>

        <div className="sessao">
          {sessao ? (
            <>
              <span>
                <strong>{sessao.usuario}</strong> | papéis:{' '}
                {sessao.papeis.join(', ') || 'nenhum'}
              </span>
              <button type="button" onClick={() => sair()}>
                Sair
              </button>
            </>
          ) : (
            <button type="button" onClick={() => void entrar()}>
              Entrar com a conta LogiTech
            </button>
          )}
        </div>

        {erro && <p role="alert">Falha no login: {erro}</p>}
      </header>

      {!sessao ? (
        <p>
          Entre para consultar os seus pedidos. Sem sessão, o serviço de Pedidos
          devolve <code>401</code> e esta tela não teria o que mostrar.
        </p>
      ) : (
        <>
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
        </>
      )}

      <footer>
        <p>
          Pedidos em http://localhost:8080, frete em http://localhost:8000 e
          identidade em http://localhost:8090. Se a tela ficar vazia, abra o
          console do navegador: erro de CORS não aparece aqui.
        </p>
      </footer>
    </main>
  );
}
