/**
 * Duas implementações de `Registrador`: uma para produção, outra para teste.
 *
 * Não é tarefa. Está aqui para que o Decorator de log da lacuna TODO-5 não
 * precise chamar `console.log` direto: quem escreve no console é uma
 * dependência injetada, e é por isso que o teste consegue ler o log linha a
 * linha em vez de tentar espionar a saída padrão.
 */

import type { Registrador } from './tipos';

/** Escreve no console, com carimbo de hora. Usado pelo servidor. */
export class LogDeConsole implements Registrador {
  registrar(linha: string): void {
    console.log(`[${new Date().toISOString()}] ${linha}`);
  }
}

/** Guarda as linhas em memória. Usado pelos testes de unidade. */
export class LogEmMemoria implements Registrador {
  readonly linhas: string[] = [];

  registrar(linha: string): void {
    this.linhas.push(linha);
  }
}
