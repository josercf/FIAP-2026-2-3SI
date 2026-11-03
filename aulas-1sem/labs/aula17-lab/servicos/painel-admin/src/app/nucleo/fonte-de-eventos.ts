import { InjectionToken } from '@angular/core';

/**
 * O mínimo que o painel precisa de uma fonte de eventos do servidor.
 *
 * Note o que **não** está aqui: nada do `EventSource` do navegador além de
 * inscrever um ouvinte e fechar a conexão. Depender da interface mínima, e
 * não da classe concreta, é o que permite trocar a fonte real por uma falsa
 * no teste sem tocar em uma linha do serviço.
 */
export interface FonteDeEventos {
  addEventListener(tipo: string, ouvinte: (evento: MessageEvent) => void): void;
  close(): void;
}

/** Como se abre uma fonte de eventos a partir de uma URL. */
export type AbrirFonteDeEventos = (url: string) => FonteDeEventos;

/**
 * O token de injeção da fonte de eventos.
 *
 * Este é o Dependency Injection da Aula 05 reaparecendo com suporte do
 * framework. Lá, em Java e em C#, o construtor recebia a interface e um
 * contêiner decidia qual implementação entregar. Aqui o contêiner é o
 * injetor do Angular, e a "interface" é este token: um objeto com identidade
 * própria, que sobrevive à minificação e não depende do nome da classe.
 *
 * `providedIn: 'root'` com `factory` significa: se ninguém disser o
 * contrário, entregue o `EventSource` de verdade. No `TestBed`, um
 * `useValue` diferente substitui a fábrica sem que o `FrotaService` saiba.
 */
export const ABRIR_FONTE_DE_EVENTOS = new InjectionToken<AbrirFonteDeEventos>(
  'ABRIR_FONTE_DE_EVENTOS',
  {
    providedIn: 'root',
    factory: () => (url: string) => new EventSource(url) as FonteDeEventos,
  },
);
