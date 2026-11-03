import { Component, signal } from '@angular/core';

import { FaturasComponent } from './faturas/faturas.component';
import { FrotaComponent } from './frota/frota.component';
import { concluirEntrada, entrar, sair, sessaoAtual, type Sessao } from './nucleo/pkce';

/**
 * A casca do painel administrativo da LogiTech.
 *
 * Standalone: nenhum `NgModule`, nenhum `declarations`, nenhum `exports`. O
 * componente diz de quem depende no próprio `imports`, e é isso. Foi essa a
 * troca que o Angular fez, e é o ponto em que ele mais se aproxima do React
 * da Aula 10: a unidade de composição voltou a ser o componente.
 *
 * Novidade da Aula 16: a casca tem sessão. As colunas de frota e de faturas só
 * são montadas depois do login, e isso é conforto de navegação, não
 * autorização: quem recusa um token de CLIENTE nas rotas de fatura é o
 * `faturamento` em C#, com 403.
 */
@Component({
  selector: 'app-root',
  imports: [FrotaComponent, FaturasComponent],
  template: `
    <header class="topo">
      <h1>LogiTech Enterprise <span>Painel administrativo</span></h1>
      <p>
        Frota por SSE do serviço <code class="mono">painel</code> (porta 3000) e faturas
        do serviço <code class="mono">faturamento</code> (porta 5080).
      </p>

      @if (sessao(); as atual) {
        <p>
          <strong>{{ atual.usuario }}</strong> | papéis: {{ atual.papeis.join(', ') || 'nenhum' }}
          <button type="button" (click)="encerrar()">Sair</button>
        </p>
      } @else {
        <p>
          <button type="button" (click)="autenticar()">Entrar com a conta LogiTech</button>
          As rotas de fatura exigem o papel <code class="mono">ADMIN</code>.
        </p>
      }

      @if (erro(); as problema) {
        <p role="alert">Falha no login: {{ problema }}</p>
      }
    </header>

    @if (sessao()) {
      <main>
        <div class="coluna"><app-frota /></div>
        <div class="coluna"><app-faturas /></div>
      </main>
    }
  `,
})
export class App {
  readonly sessao = signal<Sessao | null>(null);
  readonly erro = signal<string | null>(null);

  constructor() {
    // A sessão guardada é lida de forma síncrona, para a tela já nascer
    // certa. A conclusão do PKCE é assíncrona por natureza (ela faz uma
    // chamada de rede ao Keycloak) e apenas atualiza o que já está montado.
    this.sessao.set(sessaoAtual());
    concluirEntrada()
      .then((nova) => {
        if (nova) this.sessao.set(nova);
      })
      .catch((problema: Error) => this.erro.set(problema.message));
  }

  autenticar(): void {
    void entrar();
  }

  encerrar(): void {
    sair();
  }
}
