/**
 * RESGATE do TODO-5: o formulário de cotação, resolvido.
 *
 * Rede de segurança, não atalho. Leia `resgate/LEIA-ME.md` antes de copiar.
 */

import { useState, type FormEvent } from 'react';

import { cotarFrete } from '../api/logitech';
import type { Cotacao } from '../api/tipos';

const MODALIDADES = ['expresso', 'padrao', 'economico'];

export function CotacaoFrete() {
  const [origem, setOrigem] = useState('SAO');
  const [destino, setDestino] = useState('LDB');
  const [peso, setPeso] = useState('100');
  const [modalidade, setModalidade] = useState('padrao');

  const [cotacao, setCotacao] = useState<Cotacao | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [cotando, setCotando] = useState(false);

  async function aoEnviar(evento: FormEvent<HTMLFormElement>) {
    // Sem esta linha o formulário recarrega a página e o resultado some.
    evento.preventDefault();

    setCotando(true);
    setErro(null);
    setCotacao(null);
    try {
      const resultado = await cotarFrete({
        origem: origem.toUpperCase(),
        destino: destino.toUpperCase(),
        // O valor de um input é sempre string, inclusive com type="number".
        pesoKg: Number(peso),
        modalidade,
      });
      setCotacao(resultado);
    } catch (falha) {
      setErro((falha as Error).message);
    } finally {
      setCotando(false);
    }
  }

  return (
    <section className="cartao">
      <h2>Cotação de frete</h2>

      <form onSubmit={aoEnviar}>
        <label htmlFor="origem">Origem</label>
        <input
          id="origem"
          value={origem}
          onChange={(e) => setOrigem(e.target.value)}
        />

        <label htmlFor="destino">Destino</label>
        <input
          id="destino"
          value={destino}
          onChange={(e) => setDestino(e.target.value)}
        />

        <label htmlFor="peso">Peso (kg)</label>
        <input
          id="peso"
          type="number"
          value={peso}
          onChange={(e) => setPeso(e.target.value)}
        />

        <label htmlFor="modalidade">Modalidade</label>
        <select
          id="modalidade"
          value={modalidade}
          onChange={(e) => setModalidade(e.target.value)}
        >
          {MODALIDADES.map((nome) => (
            <option key={nome} value={nome}>
              {nome}
            </option>
          ))}
        </select>

        <button type="submit" disabled={cotando}>
          Cotar
        </button>
      </form>

      {erro !== null && <p role="alert">{erro}</p>}

      {cotacao !== null && (
        <div data-testid="cotacao">
          <p className="destaque">
            R$ {cotacao.valor.toFixed(2).replace('.', ',')}
          </p>
          <p>
            {cotacao.prazoDias} dia(s) na modalidade {cotacao.modalidade}
          </p>
        </div>
      )}
    </section>
  );
}
