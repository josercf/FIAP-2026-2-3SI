import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
// `provideHttpClient` e `withInterceptors` já estão importados: é o TODO-1b
// que os coloca em serviço.
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { interceptadorDeCorrelacao } from './nucleo/correlacao';

/**
 * A configuração do injetor raiz da aplicação.
 *
 * Em Angular standalone não existe mais `AppModule`: este array é o
 * equivalente ao contêiner de injeção de dependências que vocês configuraram
 * em Java e em C# na Aula 05. Cada `provideXxx()` é uma linha do contrato de
 * "quem entrega o quê" para o `inject()` dos serviços.
 */
export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),

    // TODO-1b ---------------------------------------------------------------
    // O painel precisa carimbar toda requisição HTTP com o cabeçalho de
    // correlação, para que um erro visto aqui seja rastreável no log do
    // serviço de Faturamento em C#. O interceptador já está escrito em
    // `nucleo/correlacao.ts`; falta dizer ao injetor que ele existe.
    //
    // Acrescente a esta lista:
    //   provideHttpClient(withInterceptors([interceptadorDeCorrelacao]))
    //
    // Sem esta linha o painel continua funcionando, e é justamente por isso
    // que o defeito é traiçoeiro: as requisições saem, só que anônimas.
  ],
};
