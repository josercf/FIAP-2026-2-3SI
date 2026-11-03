import { acumularPorPlaca, ordenarPorPlaca } from './acumulador';
import { Posicao } from './modelos';

function posicao(placa: string, uf = 'SP', velocidade = 60): Posicao {
  return { placa, uf, lat: -23.5, lng: -46.6, velocidade_kmh: velocidade };
}

/**
 * Estes três testes já nascem verdes. Eles existem para provar que a
 * aritmética de acumulação não é o exercício de hoje: se um deles quebrar, o
 * problema está em algo que vocês não deveriam ter tocado.
 */
describe('Acumulador da frota (já vem pronto)', () => {
  it('a posição nova substitui a anterior da mesma placa', () => {
    const primeira = acumularPorPlaca(new Map(), posicao('LGT1A01'));
    const segunda = acumularPorPlaca(primeira, { ...posicao('LGT1A01'), lat: -22.0 });

    expect(segunda.size).toBe(1);
    expect(segunda.get('LGT1A01')?.lat).toBe(-22.0);
  });

  it('devolve um Map novo, sem mutar o anterior', () => {
    const antes = acumularPorPlaca(new Map(), posicao('LGT1A01'));
    const depois = acumularPorPlaca(antes, posicao('LGT2A02'));

    expect(antes.size).toBe(1);
    expect(depois.size).toBe(2);
    expect(depois).not.toBe(antes);
  });

  it('ordena por placa, para a tabela não dançar na tela', () => {
    let frota = acumularPorPlaca(new Map(), posicao('LGT3A03'));
    frota = acumularPorPlaca(frota, posicao('LGT1A01'));
    frota = acumularPorPlaca(frota, posicao('LGT2A02'));

    expect(ordenarPorPlaca(frota).map((p) => p.placa)).toEqual([
      'LGT1A01',
      'LGT2A02',
      'LGT3A03',
    ]);
  });
});
