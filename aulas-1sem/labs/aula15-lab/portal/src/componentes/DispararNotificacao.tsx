/**
 * O botão que só ADMIN consegue usar.
 *
 * CONGELADO. Não é tarefa da Aula 14.
 *
 * Ele aparece para todo mundo de propósito. Entrando como `ana.cliente` ou
 * `bruno.motorista` e clicando aqui, o serviço Node devolve 403 e a mensagem
 * dele aparece na tela. É a demonstração mais curta da diferença entre 401 e
 * 403 que cabe numa interface: o login funcionou, o token é válido, e mesmo
 * assim a resposta é não.
 */

import { useState } from 'react';

import { notificar } from '../api/logitech';

export function DispararNotificacao({ token }: { token: string | null }) {
  const [resultado, setResultado] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  function disparar() {
    setResultado(null);
    setErro(null);
    notificar(token, {
      canal: 'sms',
      destinatario: '+5511988887777',
      mensagem: 'Sua carga saiu para entrega',
    })
      .then(() => setResultado('Notificação enviada.'))
      .catch((falha: Error) => setErro(falha.message));
  }

  return (
    <section className="cartao" data-testid="notificacao">
      <h2>Avisar o cliente</h2>
      <p>Dispara um SMS pelo serviço de Notificações. Exige o papel ADMIN.</p>
      <button type="button" onClick={disparar} disabled={!token}>
        Enviar aviso de entrega
      </button>
      {resultado !== null && <p role="status">{resultado}</p>}
      {erro !== null && <p role="alert">{erro}</p>}
    </section>
  );
}
