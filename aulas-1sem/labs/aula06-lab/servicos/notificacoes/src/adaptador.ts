/**
 * Adapter do rastreamento da transportadora parceira.
 *
 * Aqui mora a lacuna TODO-4.
 *
 * A parceira responde num formato legado que ninguém na LogiTech controla:
 * campos abreviados em maiúsculas, data em `dd/MM/aaaa HH:mm` e um vocabulário
 * de situação próprio. O resto do serviço não pode conhecer nada disso. O
 * Adapter é a **única** classe do sistema autorizada a saber que esse formato
 * existe: se a parceira mudar o contrato amanhã, muda este arquivo e mais
 * nenhum.
 *
 * Exemplo de resposta da parceira (serviço congelado em
 * `servicos/parceira-rastreio/`):
 *
 *     {
 *       "COD_OBJ": "BR9912345",
 *       "DT_ULT_MOV": "08/09/2026 14:32",
 *       "SIT": "EM_TRANSITO",
 *       "UF_ULT": "SP",
 *       "DESC_SIT": "Objeto em transito para a unidade de destino"
 *     }
 */

/** O formato que a parceira devolve. Vocabulário dela, não nosso. */
export interface RastreioLegado {
  COD_OBJ: string;
  DT_ULT_MOV: string;
  SIT: string;
  UF_ULT: string;
  DESC_SIT: string;
}

/** O formato do case: é este que o resto da LogiTech conhece. */
export interface Rastreio {
  codigoRastreio: string;
  status: StatusRastreio;
  atualizadoEm: string;
  uf: string;
  descricao: string;
}

export type StatusRastreio =
  | 'postado'
  | 'em_transito'
  | 'saiu_para_entrega'
  | 'entregue'
  | 'devolvido'
  | 'desconhecido';

/**
 * De/para entre o vocabulário da parceira e o da LogiTech.
 *
 * Já vem pronto: traduzir tabela não ensina padrão nenhum. O que a lacuna
 * exercita é onde essa tradução mora.
 */
export const MAPA_DE_SITUACAO: Record<string, StatusRastreio> = {
  POSTADO: 'postado',
  EM_TRANSITO: 'em_transito',
  SAIU_ENTREGA: 'saiu_para_entrega',
  ENTREGUE: 'entregue',
  DEVOLVIDO_REMETENTE: 'devolvido',
};

/**
 * Traduz a resposta da parceira para o formato do case.
 *
 * TODO-4: hoje o método devolve o objeto legado como se fosse nosso, e o
 * vocabulário da parceira vaza para dentro do sistema. Implemente a tradução:
 *
 *   - `codigoRastreio` recebe `COD_OBJ` sem espaços nas pontas;
 *   - `status` sai de `MAPA_DE_SITUACAO`, com `'desconhecido'` para situação
 *     que não estiver na tabela (a parceira acrescenta status sem avisar, e
 *     derrubar a consulta por causa disso seria pior);
 *   - `atualizadoEm` converte `dd/MM/aaaa HH:mm` para o ISO
 *     `aaaa-MM-ddTHH:mm:00`; data em formato inesperado vira string vazia;
 *   - `uf` recebe `UF_ULT` em maiúsculas;
 *   - `descricao` recebe `DESC_SIT`, ou string vazia quando vier ausente.
 *
 * Nenhum outro arquivo do serviço pode citar `COD_OBJ`, `SIT` ou `DT_ULT_MOV`.
 */
export class AdaptadorRastreioLegado {
  adaptar(bruto: RastreioLegado): Rastreio {
    // TODO-4: troque este repasse pela tradução descrita acima.
    return bruto as unknown as Rastreio;
  }
}
