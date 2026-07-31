/**
 * Resgate do Passo 6: o servidor MCP com as duas ferramentas implementadas.
 *
 *     cp resgate/servidor.ts mcp-logitech/src/servidor.ts
 *
 * O que muda em relação ao arquivo com lacunas são os corpos de
 * `buscarEmContratos` (TODO-6a) e `consultarPedido` (TODO-6b). Todo o resto,
 * inclusive o despacho de JSON-RPC e o Resource, já vinha pronto.
 */

import { readdir, readFile } from "node:fs/promises";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  ERRO_INTERNO,
  ERRO_METODO_INEXISTENTE,
  ERRO_PARAMETRO_INVALIDO,
  enviar,
  postarJson,
  pegarJson,
  receber,
  registrar,
  type Mensagem,
} from "./protocolo.ts";

const AQUI = dirname(fileURLToPath(import.meta.url));
const PASTA_CONTRATOS = resolve(AQUI, "..", "..", "contratos");

const RAG_URL = process.env.LOGITECH_RAG_URL ?? "http://localhost:8010";
const PEDIDOS_URL = process.env.LOGITECH_PEDIDOS_URL ?? "http://localhost:8080";

const VERSAO_PROTOCOLO = "2024-11-05";

interface Ferramenta {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

const FERRAMENTAS: Ferramenta[] = [
  {
    name: "buscar_em_contratos",
    description:
      "Busca por significado nas cláusulas dos contratos de transporte vigentes " +
      "da LogiTech (prazos de entrega, avarias, indenização, temperatura, " +
      "produtos perigosos, reajuste, rescisão). Devolve os trechos mais " +
      "próximos da pergunta, cada um com o contrato de origem. Use sempre que a " +
      "pergunta for sobre o que está escrito em contrato com um cliente.",
    inputSchema: {
      type: "object",
      properties: {
        pergunta: {
          type: "string",
          description: "A pergunta do usuário, em linguagem natural.",
        },
        k: {
          type: "integer",
          description: "Quantos trechos trazer. Padrão 4.",
          minimum: 1,
          maximum: 10,
        },
      },
      required: ["pergunta"],
    },
  },
  {
    name: "consultar_pedido",
    description:
      "Consulta a situação atual de um pedido da LogiTech pelo identificador. " +
      "Use quando a pergunta for sobre uma entrega específica, e não sobre o " +
      "que diz o contrato.",
    inputSchema: {
      type: "object",
      properties: {
        pedidoId: { type: "string", description: "O identificador do pedido." },
      },
      required: ["pedidoId"],
    },
  },
];

async function listarRecursos() {
  const arquivos = (await readdir(PASTA_CONTRATOS)).filter((n) => n.endsWith(".md"));
  return arquivos.map((arquivo) => ({
    uri: `logitech://contratos/${arquivo}`,
    name: arquivo.replace(/\.md$/, "").replace(/-/g, " "),
    description: `Contrato de transporte da LogiTech, arquivo ${arquivo}`,
    mimeType: "text/markdown",
  }));
}

async function lerRecurso(uri: string) {
  const prefixo = "logitech://contratos/";
  if (!uri.startsWith(prefixo)) {
    throw new Error(`URI fora do espaço deste servidor: ${uri}`);
  }
  const arquivo = uri.slice(prefixo.length);
  if (arquivo.includes("/") || arquivo.includes("..")) {
    throw new Error(`nome de arquivo inválido: ${arquivo}`);
  }
  const texto = await readFile(join(PASTA_CONTRATOS, arquivo), "utf8");
  return { contents: [{ uri, mimeType: "text/markdown", text: texto }] };
}

interface TrechoRecuperado {
  contrato: string;
  cliente: string;
  ordem: number;
  texto: string;
  distancia: number;
}

// --- TODO-6a resolvido -----------------------------------------------------
async function buscarEmContratos(argumentos: Record<string, unknown>) {
  const pergunta = String(argumentos.pergunta ?? "").trim();
  if (!pergunta) {
    throw new Error("o argumento `pergunta` é obrigatório");
  }
  const k = Number(argumentos.k ?? 4);

  const resposta = (await postarJson(`${RAG_URL}/api/v1/busca`, {
    pergunta,
    k,
  })) as { trechos?: TrechoRecuperado[] };

  const trechos = resposta.trechos ?? [];
  if (trechos.length === 0) {
    return {
      content: [
        {
          type: "text",
          text: "Nenhum trecho de contrato foi recuperado para essa pergunta.",
        },
      ],
    };
  }

  // Cada bloco carrega a sua procedência. É a citação da fonte, e ela existe
  // porque o TODO-4a juntou `trechos` com `contratos`.
  const texto = trechos
    .map(
      (t, i) =>
        `[${i + 1}] ${t.contrato} (${t.cliente}), trecho ${t.ordem}, ` +
        `distância ${t.distancia}\n${t.texto}`,
    )
    .join("\n\n");

  return {
    content: [
      {
        type: "text",
        text:
          `${trechos.length} trecho(s) recuperado(s) dos contratos da LogiTech ` +
          `para: "${pergunta}"\n\n${texto}`,
      },
    ],
  };
}

// --- TODO-6b resolvido (opcional) ------------------------------------------
async function consultarPedido(argumentos: Record<string, unknown>) {
  const pedidoId = String(argumentos.pedidoId ?? "").trim();
  if (!pedidoId) {
    throw new Error("o argumento `pedidoId` é obrigatório");
  }

  const situacao = await pegarJson(
    `${PEDIDOS_URL}/api/v1/pedidos/${encodeURIComponent(pedidoId)}/status`,
  );

  return {
    content: [
      {
        type: "text",
        text: `Situação do pedido ${pedidoId}:\n${JSON.stringify(situacao, null, 2)}`,
      },
    ],
  };
}

async function chamarFerramenta(parametros: Record<string, unknown>) {
  const nome = String(parametros.name ?? "");
  const argumentos = (parametros.arguments ?? {}) as Record<string, unknown>;

  try {
    if (nome === "buscar_em_contratos") return await buscarEmContratos(argumentos);
    if (nome === "consultar_pedido") return await consultarPedido(argumentos);
    throw new Error(`ferramenta desconhecida: ${nome}`);
  } catch (erro) {
    return {
      content: [{ type: "text", text: `falhou: ${(erro as Error).message}` }],
      isError: true,
    };
  }
}

async function tratar(mensagem: Mensagem): Promise<void> {
  const { id, method, params } = mensagem;

  if (id === undefined || id === null) {
    if (method === "notifications/initialized") registrar("cliente pronto");
    return;
  }

  const responder = (result: unknown) =>
    enviar(process.stdout, { jsonrpc: "2.0", id, result });
  const falhar = (code: number, message: string) =>
    enviar(process.stdout, { jsonrpc: "2.0", id, error: { code, message } });

  try {
    switch (method) {
      case "initialize":
        return responder({
          protocolVersion: VERSAO_PROTOCOLO,
          capabilities: { tools: {}, resources: {}, prompts: {} },
          serverInfo: { name: "mcp-logitech", version: "1.0.0" },
        });

      case "tools/list":
        return responder({ tools: FERRAMENTAS });

      case "tools/call":
        if (!params?.name) return falhar(ERRO_PARAMETRO_INVALIDO, "falta `name`");
        return responder(await chamarFerramenta(params));

      case "resources/list":
        return responder({ resources: await listarRecursos() });

      case "resources/read":
        if (!params?.uri) return falhar(ERRO_PARAMETRO_INVALIDO, "falta `uri`");
        return responder(await lerRecurso(String(params.uri)));

      case "prompts/list":
        return responder({ prompts: [] });

      case "ping":
        return responder({});

      default:
        return falhar(ERRO_METODO_INEXISTENTE, `método não suportado: ${method}`);
    }
  } catch (erro) {
    return falhar(ERRO_INTERNO, (erro as Error).message);
  }
}

registrar(`no ar por stdio. rag=${RAG_URL} pedidos=${PEDIDOS_URL}`);
receber(process.stdin, tratar);
process.stdin.on("end", () => process.exit(0));
