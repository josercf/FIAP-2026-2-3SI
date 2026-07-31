/**
 * Testes da lacuna TODO-4: o Adapter do rastreamento da parceira.
 *
 * Já vêm escritos e falhando. Cada asserção aqui corresponde a uma linha da
 * especificação escrita na documentação de `AdaptadorRastreioLegado`.
 */

import { describe, expect, it } from 'vitest';

import { AdaptadorRastreioLegado, type RastreioLegado } from '../src/adaptador';

const RESPOSTA_DA_PARCEIRA: RastreioLegado = {
  COD_OBJ: ' BR9912345 ',
  DT_ULT_MOV: '08/09/2026 14:32',
  SIT: 'EM_TRANSITO',
  UF_ULT: 'sp',
  DESC_SIT: 'Objeto em transito para a unidade de destino',
};

describe('AdaptadorRastreioLegado', () => {
  const adaptador = new AdaptadorRastreioLegado();

  it('traduz a resposta da parceira para o formato do case', () => {
    const rastreio = adaptador.adaptar(RESPOSTA_DA_PARCEIRA);

    expect(rastreio).toEqual({
      codigoRastreio: 'BR9912345',
      status: 'em_transito',
      atualizadoEm: '2026-09-08T14:32:00',
      uf: 'SP',
      descricao: 'Objeto em transito para a unidade de destino',
    });
  });

  it('não deixa vazar nenhum campo do vocabulário da parceira', () => {
    const rastreio = adaptador.adaptar(RESPOSTA_DA_PARCEIRA) as Record<string, unknown>;

    for (const campoLegado of ['COD_OBJ', 'DT_ULT_MOV', 'SIT', 'UF_ULT', 'DESC_SIT']) {
      expect(rastreio[campoLegado]).toBeUndefined();
    }
  });

  it.each([
    ['POSTADO', 'postado'],
    ['EM_TRANSITO', 'em_transito'],
    ['SAIU_ENTREGA', 'saiu_para_entrega'],
    ['ENTREGUE', 'entregue'],
    ['DEVOLVIDO_REMETENTE', 'devolvido'],
  ])('traduz a situação %s da parceira para %s', (situacao, esperado) => {
    const rastreio = adaptador.adaptar({ ...RESPOSTA_DA_PARCEIRA, SIT: situacao });
    expect(rastreio.status).toBe(esperado);
  });

  it('trata situação desconhecida sem derrubar a consulta', () => {
    const rastreio = adaptador.adaptar({ ...RESPOSTA_DA_PARCEIRA, SIT: 'EXTRAVIADO_TEMP' });
    expect(rastreio.status).toBe('desconhecido');
  });

  it('devolve data vazia quando a parceira manda formato inesperado', () => {
    const rastreio = adaptador.adaptar({ ...RESPOSTA_DA_PARCEIRA, DT_ULT_MOV: 'ontem à tarde' });
    expect(rastreio.atualizadoEm).toBe('');
  });

  it('tolera descrição ausente', () => {
    const rastreio = adaptador.adaptar({
      ...RESPOSTA_DA_PARCEIRA,
      DESC_SIT: undefined as unknown as string,
    });
    expect(rastreio.descricao).toBe('');
  });
});
