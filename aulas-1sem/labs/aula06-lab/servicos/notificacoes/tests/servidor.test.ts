/**
 * Testes da API HTTP do serviço de notificações.
 *
 * Passam desde o esqueleto e precisam continuar passando depois das lacunas:
 * é a rede de segurança da refatoração, o par do `test_rota.py` do frete.
 *
 * O servidor sobe numa porta efêmera (`listen(0)`), e não na 3001: teste que
 * disputa a porta de produção falha quando alguém deixou o serviço rodando.
 */

import type { AddressInfo } from 'node:net';

import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import { servidor } from '../src/servidor';

let base = '';

beforeAll(async () => {
  await new Promise<void>((resolva) => servidor.listen(0, resolva));
  const { port } = servidor.address() as AddressInfo;
  base = `http://127.0.0.1:${port}`;
});

afterAll(async () => {
  await new Promise<void>((resolva) => servidor.close(() => resolva()));
});

async function postar(corpo: unknown): Promise<Response> {
  return fetch(`${base}/api/v1/notificacoes`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(corpo),
  });
}

describe('API de notificações', () => {
  it('responde ao /health exigido pela ADR-006', async () => {
    const resposta = await fetch(`${base}/health`);
    expect(resposta.status).toBe(200);
    expect(await resposta.json()).toEqual({ status: 'ok' });
  });

  it('aceita uma notificação válida e devolve 202', async () => {
    const resposta = await postar({
      canal: 'email',
      destinatario: 'cliente@logitech.example',
      mensagem: 'Pedido 4471 coletado.',
    });

    expect(resposta.status).toBe(202);
    const corpo = await resposta.json();
    expect(corpo.entregue).toBe(true);
    expect(corpo.canal).toBe('email');
  });

  it('recusa canal fora do contrato Zod com 422', async () => {
    const resposta = await postar({
      canal: 'pombo-correio',
      destinatario: 'cliente@logitech.example',
      mensagem: 'Pedido 4471 coletado.',
    });

    expect(resposta.status).toBe(422);
    const corpo = await resposta.json();
    expect(corpo.canaisDisponiveis).toEqual(['email', 'sms', 'whatsapp']);
  });

  it('recusa corpo sem mensagem com 422', async () => {
    const resposta = await postar({ canal: 'sms', destinatario: '+5511999990000' });
    expect(resposta.status).toBe(422);
  });

  it('recusa corpo que não é JSON com 400', async () => {
    const resposta = await fetch(`${base}/api/v1/notificacoes`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: 'isto não é json',
    });
    expect(resposta.status).toBe(400);
  });

  it('publica o JSON Schema gerado pelo Zod', async () => {
    const resposta = await fetch(`${base}/api/v1/notificacoes/esquema`);
    expect(resposta.status).toBe(200);

    const esquema = await resposta.json();
    expect(Object.keys(esquema.entrada.properties).sort()).toEqual([
      'canal',
      'destinatario',
      'mensagem',
    ]);
  });

  it('devolve 404 em rota inexistente', async () => {
    const resposta = await fetch(`${base}/api/v1/nada`);
    expect(resposta.status).toBe(404);
  });
});
