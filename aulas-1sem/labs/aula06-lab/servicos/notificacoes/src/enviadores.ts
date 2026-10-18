/**
 * CONGELADO. NÃO ALTERE ESTE ARQUIVO.
 *
 * Os três enviadores de notificação da LogiTech, um por canal. Este arquivo
 * representa o código que já está em produção, com fornecedor homologado e
 * contrato assinado: em um serviço real, mexer aqui exige janela de mudança,
 * aprovação e reteste do canal inteiro.
 *
 * É exatamente essa restrição que dá sentido ao laboratório. Log e
 * retentativa entram por fora, com Decorator, sem que uma linha aqui mude.
 * O `verificar.py` compara este arquivo com o original e reprova o critério
 * do Decorator se ele tiver sido tocado: passar por dentro resolveria o
 * sintoma e perderia a aula.
 *
 * Se alterou por engano, restaure com:
 *     git checkout -- servicos/notificacoes/src/enviadores.ts
 */

import type { Enviador, Notificacao, ResultadoEnvio } from './tipos';

/** Protocolo simulado do provedor, no formato que a LogiTech arquiva. */
function protocolo(prefixo: string): string {
  const sufixo = Math.random().toString(36).slice(2, 10).toUpperCase();
  return `${prefixo}-${sufixo}`;
}

export class EnviadorEmail implements Enviador {
  readonly canal = 'email';

  async enviar(notificacao: Notificacao): Promise<ResultadoEnvio> {
    if (!notificacao.destinatario.includes('@')) {
      throw new Error(`destinatário de e-mail inválido: ${notificacao.destinatario}`);
    }
    return { entregue: true, canal: this.canal, tentativas: 1, identificador: protocolo('EML') };
  }
}

export class EnviadorSms implements Enviador {
  readonly canal = 'sms';

  async enviar(notificacao: Notificacao): Promise<ResultadoEnvio> {
    if (notificacao.mensagem.length > 160) {
      throw new Error('mensagem de SMS acima de 160 caracteres');
    }
    return { entregue: true, canal: this.canal, tentativas: 1, identificador: protocolo('SMS') };
  }
}

export class EnviadorWhatsapp implements Enviador {
  readonly canal = 'whatsapp';

  async enviar(_notificacao: Notificacao): Promise<ResultadoEnvio> {
    return { entregue: true, canal: this.canal, tentativas: 1, identificador: protocolo('WPP') };
  }
}

const CANAIS = new Map<string, Enviador>([
  ['email', new EnviadorEmail()],
  ['sms', new EnviadorSms()],
  ['whatsapp', new EnviadorWhatsapp()],
]);

/** Devolve o enviador de um canal. Lança se o canal não existir. */
export function enviadorPara(canal: string): Enviador {
  const enviador = CANAIS.get(canal);
  if (enviador === undefined) {
    throw new Error(`canal não suportado: ${canal}. Disponíveis: ${[...CANAIS.keys()].join(', ')}`);
  }
  return enviador;
}

/** Os canais que o serviço conhece, em ordem alfabética. */
export function canaisDisponiveis(): string[] {
  return [...CANAIS.keys()].sort();
}
