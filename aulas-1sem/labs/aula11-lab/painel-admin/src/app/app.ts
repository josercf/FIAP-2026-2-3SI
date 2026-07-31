import { Component } from '@angular/core';

import { FaturasComponent } from './faturas/faturas.component';
import { FrotaComponent } from './frota/frota.component';

/**
 * A casca do painel administrativo da LogiTech.
 *
 * Standalone: nenhum `NgModule`, nenhum `declarations`, nenhum `exports`. O
 * componente diz de quem depende no próprio `imports`, e é isso. Foi essa a
 * troca que o Angular fez, e é o ponto em que ele mais se aproxima do React
 * da Aula 10: a unidade de composição voltou a ser o componente.
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
    </header>

    <main>
      <div class="coluna"><app-frota /></div>
      <div class="coluna"><app-faturas /></div>
    </main>
  `,
})
export class App {}
