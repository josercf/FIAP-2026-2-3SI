/**
 * Os dois decoradores do serviço de notificações.
 *
 * Aqui moram as lacunas TODO-5 e TODO-6.
 *
 * As duas classes já cumprem `Enviador` e já **funcionam**: elas repassam a
 * chamada para o objeto embrulhado. O serviço sobe e responde do jeito que
 * está. O que falta é o comportamento que cada decorador deveria acrescentar.
 *
 * A regra da noite: nenhuma linha de `enviadores.ts` pode mudar.
 */

import type { Enviador, Notificacao, Registrador, ResultadoEnvio } from './tipos';

/**
 * Decorator de log: registra tentativa, sucesso e falha ao redor do envio.
 *
 * TODO-5: hoje `enviar` só repassa. Faça o método:
 *
 *   1. registrar `tentativa canal=<canal> destinatario=<destinatario>`
 *      **antes** de chamar o objeto embrulhado;
 *   2. chamar `this.interno.enviar(notificacao)`;
 *   3. em caso de sucesso, registrar
 *      `sucesso canal=<canal> identificador=<identificador do resultado>`
 *      e devolver o resultado sem alterá-lo;
 *   4. em caso de exceção, registrar
 *      `falha canal=<canal> motivo=<mensagem do erro>` e **relançar** o erro.
 *
 * O passo 4 é o que separa um decorador de um remendo: o decorador observa,
 * não engole. Quem decide o que fazer com a falha é a camada de cima, que
 * neste laboratório é o `ComRetentativa`.
 *
 * As três palavras iniciais (`tentativa`, `sucesso`, `falha`) são o contrato
 * que o teste lê. O resto da linha é livre.
 */
export class ComLog implements Enviador {
  constructor(
    private readonly interno: Enviador,
    private readonly log: Registrador,
  ) {}

  get canal(): string {
    return this.interno.canal;
  }

  async enviar(notificacao: Notificacao): Promise<ResultadoEnvio> {
    // TODO-5: envolva a chamada abaixo com as quatro etapas da documentação.
    return this.interno.enviar(notificacao);
  }
}

/**
 * Decorator de retentativa: repete o envio quando o canal falha.
 *
 * TODO-6: hoje `enviar` tenta uma vez só. Faça o método:
 *
 *   1. tentar até `this.maxTentativas` vezes;
 *   2. na primeira que der certo, devolver o resultado com o campo
 *      `tentativas` igual ao número da tentativa que funcionou
 *      (`{ ...resultado, tentativas: numero }`);
 *   3. esperar `this.esperaMs` milissegundos entre uma tentativa e a
 *      seguinte, usando o `espere` que já está pronto no fim do arquivo;
 *   4. esgotadas as tentativas, relançar o último erro.
 *
 * Este decorador precisa funcionar empilhado sobre o `ComLog`:
 *
 *     const enviador = new ComRetentativa(new ComLog(base, log), 3);
 *
 * Nessa ordem, o log registra `tentativa`, `falha`, `tentativa`, `sucesso`,
 * porque a retentativa está por fora e chama o log duas vezes. Inverter a
 * ordem produz outro log, e é um bom exercício de dois minutos depois que o
 * teste passar.
 */
export class ComRetentativa implements Enviador {
  constructor(
    private readonly interno: Enviador,
    private readonly maxTentativas: number = 3,
    private readonly esperaMs: number = 0,
  ) {
    if (maxTentativas < 1) {
      throw new Error('maxTentativas precisa ser no mínimo 1');
    }
  }

  get canal(): string {
    return this.interno.canal;
  }

  async enviar(notificacao: Notificacao): Promise<ResultadoEnvio> {
    // TODO-6: transforme a chamada única abaixo no laço descrito na
    // documentação da classe.
    return this.interno.enviar(notificacao);
  }
}

/** Espera assíncrona, sem bloquear o event loop. Já vem pronta. */
export function espere(ms: number): Promise<void> {
  return new Promise((resolva) => setTimeout(resolva, ms));
}
