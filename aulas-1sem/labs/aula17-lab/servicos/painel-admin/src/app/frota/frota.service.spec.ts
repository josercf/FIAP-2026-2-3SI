import { TestBed } from '@angular/core/testing';
import { Subscription } from 'rxjs';

import { ABRIR_FONTE_DE_EVENTOS, FonteDeEventos } from '../nucleo/fonte-de-eventos';
import { Alerta, Posicao } from '../nucleo/modelos';
import { FrotaService, LIMITE_VELOCIDADE_KMH, UF_TODAS } from './frota.service';

/**
 * Uma fonte de eventos falsa, no lugar do EventSource do navegador.
 *
 * Esta classe é a resposta prática da Pergunta de Verificação 2: o
 * `FrotaService` não sabe que ela existe. Ele pede a fábrica ao injetor, e o
 * `TestBed` entrega esta aqui em vez da de verdade. Sem Injeção de
 * Dependência, testar este serviço exigiria um servidor SSE no ar.
 */
class FonteFalsa implements FonteDeEventos {
  readonly ouvintes = new Map<string, ((evento: MessageEvent) => void)[]>();
  fechada = false;

  constructor(readonly url: string) {}

  addEventListener(tipo: string, ouvinte: (evento: MessageEvent) => void): void {
    const atuais = this.ouvintes.get(tipo) ?? [];
    atuais.push(ouvinte);
    this.ouvintes.set(tipo, atuais);
  }

  close(): void {
    this.fechada = true;
  }

  /** Simula uma posição chegando do servidor. */
  emitir(posicao: Posicao): void {
    for (const ouvinte of this.ouvintes.get('posicao') ?? []) {
      ouvinte(new MessageEvent('posicao', { data: JSON.stringify(posicao) }));
    }
  }
}

function posicao(placa: string, uf: string, velocidade: number): Posicao {
  return {
    placa,
    uf,
    lat: -23.55,
    lng: -46.63,
    velocidade_kmh: velocidade,
    recebido_em: '2026-10-13T22:00:00+00:00',
  };
}

describe('FrotaService', () => {
  let servico: FrotaService;
  let fontes: FonteFalsa[];
  const inscricoes: Subscription[] = [];

  beforeEach(() => {
    fontes = [];
    TestBed.configureTestingModule({
      providers: [
        FrotaService,
        {
          provide: ABRIR_FONTE_DE_EVENTOS,
          useValue: (url: string) => {
            const fonte = new FonteFalsa(url);
            fontes.push(fonte);
            return fonte;
          },
        },
      ],
    });
    servico = TestBed.inject(FrotaService);
  });

  afterEach(() => {
    while (inscricoes.length) inscricoes.pop()?.unsubscribe();
  });

  // -------------------------------------------------------------------------
  describe('TODO-2: o Observable sobre o SSE', () => {
    it('não abre conexão nenhuma antes de alguém se inscrever', () => {
      expect(fontes.length).toBe(0);
    });

    it('abre a fonte no endereço de eventos do painel ao receber o primeiro inscrito', () => {
      inscricoes.push(servico.eventos$.subscribe());

      expect(fontes.length).toBe(1);
      expect(fontes[0].url).toBe('http://localhost:3000/api/v1/eventos');
    });

    it('emite uma Posicao para cada evento posicao que chega', () => {
      const recebidas: Posicao[] = [];
      inscricoes.push(servico.eventos$.subscribe((p) => recebidas.push(p)));

      fontes[0].emitir(posicao('LGT1A01', 'SP', 42));
      fontes[0].emitir(posicao('LGT2A02', 'PR', 77));

      expect(recebidas.map((p) => p.placa)).toEqual(['LGT1A01', 'LGT2A02']);
      expect(recebidas[1].velocidade_kmh).toBe(77);
    });

    it('fecha a conexão quando o último inscrito cancela a inscrição', () => {
      const inscricao = servico.eventos$.subscribe();
      expect(fontes[0].fechada).toBe(false);

      inscricao.unsubscribe();

      expect(fontes[0].fechada).toBe(true);
    });

    it('dois inscritos dividem uma única conexão', () => {
      inscricoes.push(servico.eventos$.subscribe());
      inscricoes.push(servico.eventos$.subscribe());

      expect(fontes.length).toBe(1);
    });
  });

  // -------------------------------------------------------------------------
  describe('TODO-3: a fotografia da frota com scan e map', () => {
    it('acumula a última posição conhecida de cada placa', () => {
      const fotos: Posicao[][] = [];
      inscricoes.push(servico.frota$.subscribe((f) => fotos.push(f)));

      fontes[0].emitir(posicao('LGT1A01', 'SP', 40));
      fontes[0].emitir(posicao('LGT2A02', 'PR', 50));
      fontes[0].emitir({ ...posicao('LGT1A01', 'SP', 95), lat: -22.9 });

      expect(fotos.length).toBe(3);
      expect(fotos[2].length).toBe(2);
      expect(fotos[2].find((p) => p.placa === 'LGT1A01')?.velocidade_kmh).toBe(95);
    });

    it('reemite a fotografia inteira a cada posição nova', () => {
      const fotos: Posicao[][] = [];
      inscricoes.push(servico.frota$.subscribe((f) => fotos.push(f)));

      fontes[0].emitir(posicao('LGT1A01', 'SP', 40));
      fontes[0].emitir(posicao('LGT2A02', 'PR', 50));

      expect(fotos.map((f) => f.length)).toEqual([1, 2]);
    });

    it('entrega a frota ordenada por placa', () => {
      const fotos: Posicao[][] = [];
      inscricoes.push(servico.frota$.subscribe((f) => fotos.push(f)));

      fontes[0].emitir(posicao('LGT3A03', 'MG', 40));
      fontes[0].emitir(posicao('LGT1A01', 'SP', 50));
      fontes[0].emitir(posicao('LGT2A02', 'PR', 60));

      expect(fotos[2].map((p) => p.placa)).toEqual(['LGT1A01', 'LGT2A02', 'LGT3A03']);
    });
  });

  // -------------------------------------------------------------------------
  describe('TODO-4: o fluxo de alertas com filter e map', () => {
    it('descarta quem está no limite ou abaixo dele', () => {
      const alertas: Alerta[] = [];
      inscricoes.push(servico.alertas$.subscribe((a) => alertas.push(a)));

      fontes[0].emitir(posicao('LGT1A01', 'SP', LIMITE_VELOCIDADE_KMH - 1));
      fontes[0].emitir(posicao('LGT2A02', 'PR', LIMITE_VELOCIDADE_KMH));

      expect(alertas.length).toBe(0);
    });

    it('deixa passar quem ultrapassa o limite', () => {
      const alertas: Alerta[] = [];
      inscricoes.push(servico.alertas$.subscribe((a) => alertas.push(a)));

      fontes[0].emitir(posicao('LGT1A01', 'SP', 30));
      fontes[0].emitir(posicao('LGT2A02', 'PR', LIMITE_VELOCIDADE_KMH + 1));

      expect(alertas.map((a) => a.placa)).toEqual(['LGT2A02']);
    });

    it('traduz o vocabulário do rastreador para o da tela', () => {
      const alertas: Alerta[] = [];
      inscricoes.push(servico.alertas$.subscribe((a) => alertas.push(a)));

      fontes[0].emitir(posicao('LGT7A07', 'RS', 118));

      expect(alertas[0]).toEqual({
        placa: 'LGT7A07',
        uf: 'RS',
        velocidadeKmh: 118,
        em: '2026-10-13T22:00:00+00:00',
      });
    });
  });

  // -------------------------------------------------------------------------
  describe('TODO-5: o filtro de UF com BehaviorSubject e combineLatest', () => {
    it('entrega TODAS a quem se inscreve sem ninguém ter tocado no filtro', async () => {
      const primeiro = await new Promise<string>((resolva) => {
        inscricoes.push(servico.filtroUf$.subscribe((uf) => resolva(uf)));
        setTimeout(() => resolva('nada foi emitido'), 20);
      });

      expect(primeiro).toBe(UF_TODAS);
    });

    it('guarda o último filtro escolhido para quem chegar depois', async () => {
      servico.definirFiltro('PR');

      const atual = await new Promise<string>((resolva) => {
        inscricoes.push(servico.filtroUf$.subscribe((uf) => resolva(uf)));
        setTimeout(() => resolva('nada foi emitido'), 20);
      });

      expect(atual).toBe('PR');
    });

    it('devolve a frota inteira enquanto o filtro estiver em TODAS', () => {
      const fotos: Posicao[][] = [];
      inscricoes.push(servico.frotaFiltrada$.subscribe((f) => fotos.push(f)));

      fontes[0].emitir(posicao('LGT1A01', 'SP', 40));
      fontes[0].emitir(posicao('LGT2A02', 'PR', 50));

      expect(fotos[fotos.length - 1].map((p) => p.placa)).toEqual(['LGT1A01', 'LGT2A02']);
    });

    it('refiltra na hora em que a UF muda, sem esperar caminhão novo', () => {
      const fotos: Posicao[][] = [];
      inscricoes.push(servico.frotaFiltrada$.subscribe((f) => fotos.push(f)));

      fontes[0].emitir(posicao('LGT1A01', 'SP', 40));
      fontes[0].emitir(posicao('LGT2A02', 'PR', 50));
      const antes = fotos.length;

      servico.definirFiltro('PR');

      expect(fotos.length).toBeGreaterThan(antes);
      expect(fotos[fotos.length - 1].map((p) => p.placa)).toEqual(['LGT2A02']);
    });

    it('um caminhão novo respeita a UF já escolhida', () => {
      servico.definirFiltro('MG');

      const fotos: Posicao[][] = [];
      inscricoes.push(servico.frotaFiltrada$.subscribe((f) => fotos.push(f)));

      fontes[0].emitir(posicao('LGT1A01', 'SP', 40));
      fontes[0].emitir(posicao('LGT9A09', 'MG', 55));

      expect(fotos[fotos.length - 1].map((p) => p.placa)).toEqual(['LGT9A09']);
    });
  });
});
