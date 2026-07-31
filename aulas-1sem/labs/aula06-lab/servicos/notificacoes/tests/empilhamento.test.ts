/**
 * Testes da lacuna TODO-6: retentativa empilhada sobre o log.
 *
 * Este é o teste que fecha o laboratório. Ele prova a tese do Decorator com
 * três asserções que, juntas, não deixam saída pelo caminho fácil:
 *
 *   1. um canal que falha uma vez e depois funciona produz, no log, a
 *      sequência tentativa, falha, tentativa, sucesso;
 *   2. o resultado devolvido diz que foram necessárias 2 tentativas;
 *   3. `src/enviadores.ts` continua sem uma linha de log ou de retentativa,
 *      lido do disco pelo próprio teste.
 *
 * A asserção 3 é o que impede a solução preguiçosa: dá para fazer o log e a
 * retentativa aparecerem editando o enviador, e isso passaria em 1 e 2. O
 * ponto da aula é justamente que não se toca no que já está em produção.
 */

import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { ComLog, ComRetentativa } from '../src/decoradores';
import { EnviadorEmail } from '../src/enviadores';
import { LogEmMemoria } from '../src/log';
import type { Enviador, Notificacao, ResultadoEnvio } from '../src/tipos';

const NOTIFICACAO: Notificacao = {
  canal: 'email',
  destinatario: 'sac@logitech.example',
  mensagem: 'Sua entrega foi reagendada para amanhã.',
};

/**
 * Canal instável: falha nas primeiras `falhasAte` chamadas e funciona depois.
 * É o comportamento real de um provedor de e-mail sob rajada.
 */
class CanalInstavel implements Enviador {
  readonly canal = 'email';
  chamadas = 0;

  constructor(private readonly falhasAte: number) {}

  async enviar(): Promise<ResultadoEnvio> {
    this.chamadas += 1;
    if (this.chamadas <= this.falhasAte) {
      throw new Error(`timeout do provedor na chamada ${this.chamadas}`);
    }
    return { entregue: true, canal: this.canal, tentativas: 1, identificador: 'EML-OK9' };
  }
}

describe('ComRetentativa empilhado sobre ComLog', () => {
  it('registra tentativa, falha, nova tentativa e sucesso', async () => {
    const log = new LogEmMemoria();
    const instavel = new CanalInstavel(1);
    const enviador = new ComRetentativa(new ComLog(instavel, log), 3, 0);

    const resultado = await enviador.enviar(NOTIFICACAO);

    expect(log.linhas.map((linha) => linha.split(' ')[0])).toEqual([
      'tentativa',
      'falha',
      'tentativa',
      'sucesso',
    ]);
    expect(log.linhas[1]).toContain('motivo=timeout do provedor na chamada 1');
    expect(resultado.entregue).toBe(true);
    expect(instavel.chamadas).toBe(2);
  });

  it('devolve o número da tentativa que funcionou', async () => {
    const log = new LogEmMemoria();
    const enviador = new ComRetentativa(new ComLog(new CanalInstavel(1), log), 3, 0);

    const resultado = await enviador.enviar(NOTIFICACAO);

    expect(resultado.tentativas).toBe(2);
  });

  it('desiste depois do limite e relança o último erro', async () => {
    const log = new LogEmMemoria();
    const instavel = new CanalInstavel(99);
    const enviador = new ComRetentativa(new ComLog(instavel, log), 3, 0);

    await expect(enviador.enviar(NOTIFICACAO)).rejects.toThrow('timeout do provedor');
    expect(instavel.chamadas).toBe(3);
    expect(log.linhas.filter((linha) => linha.startsWith('falha'))).toHaveLength(3);
  });

  it('espera entre as tentativas, sem bloquear o event loop', async () => {
    const enviador = new ComRetentativa(new CanalInstavel(1), 3, 60);

    const comeco = Date.now();
    await enviador.enviar(NOTIFICACAO);

    expect(Date.now() - comeco).toBeGreaterThanOrEqual(50);
  });

  it('funciona sobre o enviador de produção, sem adaptação nenhuma', async () => {
    const log = new LogEmMemoria();
    const enviador = new ComRetentativa(new ComLog(new EnviadorEmail(), log), 3, 0);

    const resultado = await enviador.enviar(NOTIFICACAO);

    expect(resultado.entregue).toBe(true);
    expect(resultado.identificador).toMatch(/^EML-/);
    expect(log.linhas).toHaveLength(2);
  });

  it('prova que enviadores.ts continua sem log e sem retentativa', () => {
    const fonte = readFileSync(join(import.meta.dirname, '..', 'src', 'enviadores.ts'), 'utf-8');
    const codigo = fonte.slice(fonte.indexOf('import type'));

    expect(codigo).not.toContain('decoradores');
    expect(codigo).not.toContain('Registrador');
    expect(codigo).not.toMatch(/retentativa|tentar novamente|registrar\(/i);
    expect(codigo).not.toMatch(/console\.log/);
  });
});
