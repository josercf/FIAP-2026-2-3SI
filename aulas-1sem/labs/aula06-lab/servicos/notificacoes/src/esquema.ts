/**
 * Contrato HTTP do serviço de notificações, descrito com Zod.
 *
 * É o par do Pydantic do serviço de frete: um único lugar declara o formato,
 * e dele saem a validação em tempo de execução, o tipo em tempo de compilação
 * (`z.infer`) e o JSON Schema publicado em
 * `GET /api/v1/notificacoes/esquema`.
 *
 * Não é tarefa: está aqui para vocês compararem as duas abordagens no mesmo
 * laboratório. Os nomes dos campos são os da ADR-006 e não se traduzem.
 */

import { z } from 'zod';

export const EsquemaNotificacao = z.object({
  canal: z.enum(['email', 'sms', 'whatsapp']),
  destinatario: z.string().min(3).max(120),
  mensagem: z.string().min(1).max(1000),
});

export const EsquemaResultadoEnvio = z.object({
  entregue: z.boolean(),
  canal: z.string(),
  tentativas: z.number().int().min(1),
  identificador: z.string(),
});

/** O tipo TypeScript sai do esquema, não o contrário. */
export type NotificacaoValidada = z.infer<typeof EsquemaNotificacao>;

/** JSON Schema publicado pela rota de esquema, gerado pelo próprio Zod. */
export function jsonSchemaDoContrato(): Record<string, unknown> {
  return {
    entrada: z.toJSONSchema(EsquemaNotificacao),
    saida: z.toJSONSchema(EsquemaResultadoEnvio),
  };
}
