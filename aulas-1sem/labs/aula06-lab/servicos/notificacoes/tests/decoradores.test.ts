/**
 * Testes da lacuna TODO-5: o Decorator de log.
 *
 * O enviador usado aqui é um dublê de teste, não um dos enviadores de
 * produção: a suíte de unidade não fala com provedor de verdade. O que
 * importa é que ele cumpre a mesma interface `Enviador`, e é essa interface
 * comum que torna o Decorator possível.
 */

import { describe, expect, it } from 'vitest';

import { ComLog } from '../src/decoradores';
import { LogEmMemoria } from '../src/log';
import type { Enviador, Notificacao, ResultadoEnvio } from '../src/tipos';

const NOTIFICACAO: Notificacao = {
  canal: 'email',
  destinatario: 'operacao@logitech.example',
  mensagem: 'Pedido 4471 saiu para entrega.',
};

/** Dublê que sempre entrega. */
class CanalConfiavel implements Enviador {
  readonly canal = 'email';
  async enviar(): Promise<ResultadoEnvio> {
    return { entregue: true, canal: this.canal, tentativas: 1, identificador: 'EML-TESTE01' };
  }
}

/** Dublê que sempre falha, com um motivo reconhecível no log. */
class CanalQuebrado implements Enviador {
  readonly canal = 'email';
  async enviar(): Promise<ResultadoEnvio> {
    throw new Error('provedor fora do ar');
  }
}

describe('ComLog', () => {
  it('registra tentativa e sucesso, nessa ordem', async () => {
    const log = new LogEmMemoria();
    const resultado = await new ComLog(new CanalConfiavel(), log).enviar(NOTIFICACAO);

    expect(log.linhas).toHaveLength(2);
    expect(log.linhas[0]).toMatch(/^tentativa\b/);
    expect(log.linhas[1]).toMatch(/^sucesso\b/);
    expect(resultado.entregue).toBe(true);
  });

  it('põe canal e destinatário na linha de tentativa', async () => {
    const log = new LogEmMemoria();
    await new ComLog(new CanalConfiavel(), log).enviar(NOTIFICACAO);

    expect(log.linhas[0]).toContain('canal=email');
    expect(log.linhas[0]).toContain('destinatario=operacao@logitech.example');
  });

  it('põe o identificador do provedor na linha de sucesso', async () => {
    const log = new LogEmMemoria();
    await new ComLog(new CanalConfiavel(), log).enviar(NOTIFICACAO);

    expect(log.linhas[1]).toContain('identificador=EML-TESTE01');
  });

  it('registra a falha e relança o erro, em vez de engoli-lo', async () => {
    const log = new LogEmMemoria();
    const enviador = new ComLog(new CanalQuebrado(), log);

    await expect(enviador.enviar(NOTIFICACAO)).rejects.toThrow('provedor fora do ar');
    expect(log.linhas).toHaveLength(2);
    expect(log.linhas[1]).toMatch(/^falha\b/);
    expect(log.linhas[1]).toContain('motivo=provedor fora do ar');
  });

  it('não altera o resultado devolvido pelo enviador embrulhado', async () => {
    const log = new LogEmMemoria();
    const semLog = await new CanalConfiavel().enviar(NOTIFICACAO);
    const comLog = await new ComLog(new CanalConfiavel(), log).enviar(NOTIFICACAO);

    expect(comLog).toEqual(semLog);
  });

  it('se passa pelo enviador embrulhado, inclusive no canal', () => {
    const decorado = new ComLog(new CanalConfiavel(), new LogEmMemoria());
    expect(decorado.canal).toBe('email');
  });
});
