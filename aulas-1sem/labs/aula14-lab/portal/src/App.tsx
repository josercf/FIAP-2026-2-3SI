/**
 * A casca do Portal do Cliente da LogiTech, agora com login.
 *
 * CONGELADO. Não é tarefa da Aula 14: o que você escreve está em
 * `auth/pkce.ts`.
 *
 * A tela mostra as três coisas que a aula quer tornar visíveis:
 *   1. quem está logado e com que papéis, lidos de `realm_access.roles`;
 *   2. a lista de pedidos, que só carrega com token;
 *   3. um botão que dispara notificação e que só ADMIN consegue usar. Para
 *      Ana e Bruno ele aparece e devolve 403, de propósito: esconder o botão
 *      seria mais bonito e ensinaria menos.
 */

import { useEffect, useState } from 'react';

import { ListaDePedidos } from './componentes/ListaDePedidos';
import { DispararNotificacao } from './componentes/DispararNotificacao';
import { concluirRetorno, entrar, sair } from './auth/sessao';
import type { Sessao } from './auth/pkce';

export function App() {
  const [sessao, setSessao] = useState<Sessao | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    concluirRetorno()
      .then((nova) => {
        if (nova) setSessao(nova);
      })
      .catch((falha: Error) => setErro(falha.message));
  }, []);

  const expiraEm = sessao
    ? Math.max(0, sessao.expiraEm - Math.floor(Date.now() / 1000))
    : 0;

  return (
    <main>
      <header>
        <h1>LogiTech | Portal do Cliente</h1>
        <p>Rastreie a sua carga. Agora só depois de dizer quem você é.</p>
      </header>

      <section className="cartao" data-testid="sessao">
        {sessao === null ? (
          <>
            <p>Você não está autenticado. Nenhuma rota da plataforma responde assim.</p>
            <button
              type="button"
              onClick={() => {
                entrar().catch((falha: Error) => setErro(falha.message));
              }}
            >
              Entrar com a conta LogiTech
            </button>
          </>
        ) : (
          <>
            <p className="destaque">{sessao.usuario}</p>
            <dl>
              <dt>Papéis (realm_access.roles)</dt>
              <dd>{sessao.papeis.join(', ') || '(nenhum)'}</dd>
              <dt>O token expira em</dt>
              <dd>{expiraEm} segundos</dd>
            </dl>
            <button type="button" onClick={sair}>
              Sair
            </button>
          </>
        )}
        {erro !== null && <p role="alert">{erro}</p>}
      </section>

      <div className="colunas">
        <ListaDePedidos token={sessao?.accessToken ?? null} />
        <DispararNotificacao token={sessao?.accessToken ?? null} />
      </div>

      <footer>
        <p>
          Pedidos em http://localhost:8080 (Java) e notificações em
          http://localhost:3001 (Node). Os dois leem o papel do mesmo lugar do
          mesmo token.
        </p>
      </footer>
    </main>
  );
}
