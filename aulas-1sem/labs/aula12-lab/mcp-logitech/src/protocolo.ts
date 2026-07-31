/**
 * Transporte stdio e enquadramento JSON-RPC 2.0 do Model Context Protocol.
 *
 * O MCP não inventou um formato de mensagem: ele é JSON-RPC 2.0, que existe
 * desde 2010, sobre um transporte. O transporte padrão é o **stdio**: o
 * cliente sobe o servidor como processo filho e conversa com ele pela entrada
 * e pela saída padrão, uma mensagem JSON por linha.
 *
 * É por isso que este é o único serviço da plataforma LogiTech **sem porta e
 * sem GET /health**: não há socket para escutar. Quem o inicia é o cliente,
 * quem o encerra é o cliente, e não existe endereço para um terceiro chamar.
 *
 * Consequência prática que morde na primeira execução: **nada pode ser escrito
 * em stdout além de mensagens do protocolo**. Um `console.log` de depuração no
 * meio do servidor corrompe o fluxo e o cliente desconecta com um erro de
 * parse que não menciona o seu log. Log vai para `stderr`, e a função
 * `registrar()` abaixo existe para tornar isso difícil de errar.
 *
 * Não é tarefa. Este arquivo vem pronto.
 */

export type Id = string | number | null;

export interface Mensagem {
  jsonrpc: "2.0";
  id?: Id;
  method?: string;
  params?: Record<string, unknown>;
  result?: unknown;
  error?: { code: number; message: string; data?: unknown };
}

/** Códigos de erro do JSON-RPC 2.0 que o MCP reaproveita sem alteração. */
export const ERRO_METODO_INEXISTENTE = -32601;
export const ERRO_PARAMETRO_INVALIDO = -32602;
export const ERRO_INTERNO = -32603;

/** Log do servidor. Sempre em stderr, nunca em stdout. */
export function registrar(...partes: unknown[]): void {
  process.stderr.write("[mcp-logitech] " + partes.map(String).join(" ") + "\n");
}

/** Escreve uma mensagem no fluxo de saída, uma linha por mensagem. */
export function enviar(fluxo: NodeJS.WritableStream, mensagem: Mensagem): void {
  fluxo.write(JSON.stringify(mensagem) + "\n");
}

/**
 * Lê mensagens de um fluxo e entrega uma a uma ao tratador.
 *
 * O buffer existe porque stdin não respeita fronteira de mensagem: uma linha
 * pode chegar partida em dois pedaços, e dois pedidos podem chegar juntos no
 * mesmo pedaço. Quem escreve protocolo sobre fluxo de bytes sempre precisa
 * deste laço, e vocês já viram esse mesmo problema nos sockets da Aula 02.
 */
export function receber(
  fluxo: NodeJS.ReadableStream,
  tratar: (mensagem: Mensagem) => void | Promise<void>,
): void {
  let acumulado = "";
  fluxo.setEncoding("utf8");
  fluxo.on("data", (pedaco: string) => {
    acumulado += pedaco;
    let quebra = acumulado.indexOf("\n");
    while (quebra >= 0) {
      const linha = acumulado.slice(0, quebra).trim();
      acumulado = acumulado.slice(quebra + 1);
      if (linha.length > 0) {
        try {
          void tratar(JSON.parse(linha) as Mensagem);
        } catch (erro) {
          registrar("linha ilegível descartada:", String(erro));
        }
      }
      quebra = acumulado.indexOf("\n");
    }
  });
}

/** GET com tempo limite, sem dependência externa. */
export async function pegarJson(
  url: string,
  tempoLimiteMs = 15000,
): Promise<unknown> {
  return chamarJson(url, { method: "GET" }, tempoLimiteMs);
}

/** POST de JSON com tempo limite, sem dependência externa. */
export async function postarJson(
  url: string,
  corpo: unknown,
  tempoLimiteMs = 120000,
): Promise<unknown> {
  return chamarJson(
    url,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    },
    tempoLimiteMs,
  );
}

async function chamarJson(
  url: string,
  opcoes: RequestInit,
  tempoLimiteMs: number,
): Promise<unknown> {
  const cancelador = new AbortController();
  const relogio = setTimeout(() => cancelador.abort(), tempoLimiteMs);
  try {
    const resposta = await fetch(url, { ...opcoes, signal: cancelador.signal });
    const texto = await resposta.text();
    if (!resposta.ok) {
      throw new Error(`${url} respondeu ${resposta.status}: ${texto.slice(0, 300)}`);
    }
    return texto ? JSON.parse(texto) : null;
  } finally {
    clearTimeout(relogio);
  }
}
