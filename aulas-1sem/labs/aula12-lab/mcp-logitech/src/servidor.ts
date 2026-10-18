/**
 * Servidor MCP da LogiTech: `mcp-logitech`.
 *
 * Expõe para qualquer cliente de IA duas coisas que a plataforma já tem:
 *
 *   Resource  logitech://contratos/<arquivo>   os contratos em Markdown
 *   Tool      buscar_em_contratos              a busca semântica do serviço rag
 *   Tool      consultar_pedido                 o status de um pedido (opcional)
 *
 * A distinção entre Resource e Tool é a decisão de projeto mais importante
 * deste arquivo, e não é sinônimo:
 *
 *   Resource  é dado que o cliente **lê**. Identificado por URI, sem efeito
 *             colateral, e é o **cliente** que decide quando buscar. Serve ao
 *             que o usuário pode querer anexar à conversa.
 *
 *   Tool      é função que o modelo **executa**, com argumentos e com efeito
 *             possível. Quem decide chamar é o modelo, e por isso a descrição
 *             e o schema de entrada são conteúdo de verdade: são eles que o
 *             modelo lê para escolher.
 *
 *   Prompt    é um modelo de instrução pronto, oferecido ao usuário. Este
 *             servidor não expõe nenhum, e a lista vazia é resposta legítima.
 *
 * Por que a busca é Tool e não Resource: o resultado depende de um argumento
 * que só existe no momento da conversa, a pergunta. Não há URI estável para
 * "o trecho que responde ao que o usuário acabou de digitar".
 *
 * Rode assim, para conversar com ele na mão:
 *     node --experimental-strip-types src/servidor.ts
 *
 * E assim, para o teste automatizado:
 *     npm test
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

// Endereço nunca cravado no código: contrato da plataforma (ADR-006 e ADR-008).
const RAG_URL = process.env.LOGITECH_RAG_URL ?? "http://localhost:8010";
const PEDIDOS_URL = process.env.LOGITECH_PEDIDOS_URL ?? "http://localhost:8080";

// Versão do protocolo que este servidor fala. O cliente manda a dele no
// `initialize` e as duas partes trabalham na maior versão em comum.
const VERSAO_PROTOCOLO = "2024-11-05";

interface Ferramenta {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

/**
 * O catálogo que o cliente recebe em `tools/list`.
 *
 * Este texto é lido por um modelo de linguagem, não por uma pessoa. Descrição
 * vaga produz ferramenta chamada na hora errada, e a culpa costuma cair no
 * modelo. "Busca coisas" e "busca por significado nas cláusulas dos contratos
 * de transporte vigentes" levam a comportamentos diferentes.
 */
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

// ---------------------------------------------------------------------------
// Resource: os contratos em Markdown. Este bloco vem PRONTO, e serve de
// exemplo trabalhado. Leia antes de escrever o TODO-6a.
// ---------------------------------------------------------------------------

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
  // Sem esta linha, `logitech://contratos/../../.env` sairia daqui com o seu
  // arquivo de senhas dentro. Servidor MCP é superfície de ataque como
  // qualquer outra, e travessia de caminho é a falha mais fácil de cometer.
  const arquivo = uri.slice(prefixo.length);
  if (arquivo.includes("/") || arquivo.includes("..")) {
    throw new Error(`nome de arquivo inválido: ${arquivo}`);
  }
  const texto = await readFile(join(PASTA_CONTRATOS, arquivo), "utf8");
  return { contents: [{ uri, mimeType: "text/markdown", text: texto }] };
}

// ---------------------------------------------------------------------------
// TODO-6a: implemente a ferramenta de busca nos contratos.
//
// Ela é uma casca fina sobre o serviço `rag` que você acabou de fazer
// funcionar. O trabalho de verdade é do PostgreSQL; o que o MCP acrescenta é
// **descoberta e padronização**: qualquer cliente de IA que fale MCP passa a
// enxergar essa busca sem uma linha de código de integração.
//
//   6a-1  Chame `POST {RAG_URL}/api/v1/busca` com o corpo
//         `{ pergunta, k }`. Use a função `postarJson` de `./protocolo.ts`,
//         que já trata tempo limite e erro de HTTP.
//
//   6a-2  Monte o texto da resposta com um bloco por trecho, e **cada bloco
//         precisa dizer de qual contrato ele veio**. É a citação da fonte, e
//         ela sai do JOIN do TODO-4a. Sem ela, o modelo recebe parágrafos sem
//         procedência e o usuário não tem como conferir nada.
//
//   6a-3  Devolva no formato de conteúdo do MCP:
//         `{ content: [{ type: "text", text: <o texto montado> }] }`
//
// Falha vira `isError: true` com o motivo no texto, e não exceção. Quem trata
// isso é o `chamarFerramenta` mais abaixo, que já está pronto: da sua função
// basta deixar o erro subir.
// ---------------------------------------------------------------------------

interface TrechoRecuperado {
  contrato: string;
  cliente: string;
  ordem: number;
  texto: string;
  distancia: number;
}

async function buscarEmContratos(argumentos: Record<string, unknown>) {
  const pergunta = String(argumentos.pergunta ?? "").trim();
  if (!pergunta) {
    throw new Error("o argumento `pergunta` é obrigatório");
  }
  const k = Number(argumentos.k ?? 4);

  throw new Error(
    "TODO-6a ainda em aberto em mcp-logitech/src/servidor.ts: a ferramenta " +
      "buscar_em_contratos não foi implementada.",
  );
}

// ---------------------------------------------------------------------------
// TODO-6b: a segunda ferramenta. OPCIONAL.
//
// Esta é a primeira coisa a cortar se o tempo apertar, e o README diz isso na
// ordem de corte. Ela consome `GET {PEDIDOS_URL}/api/v1/pedidos/{id}/status`,
// a mesma rota que o agente da Aula 08 chamava por Function Calling.
//
// O paralelo vale ser pensado: lá, a integração era escrita à mão, para aquele
// agente, naquele formato. Aqui, a mesma rota vira uma ferramenta que qualquer
// cliente MCP descobre sozinho. É a diferença entre integração ponto a ponto e
// protocolo, e é a resposta da Pergunta de Verificação 2.
// ---------------------------------------------------------------------------

async function consultarPedido(argumentos: Record<string, unknown>) {
  const pedidoId = String(argumentos.pedidoId ?? "").trim();
  if (!pedidoId) {
    throw new Error("o argumento `pedidoId` é obrigatório");
  }

  throw new Error(
    "TODO-6b ainda em aberto: a ferramenta consultar_pedido é opcional e não " +
      "foi implementada. Ela não entra nos critérios de aceitação.",
  );
}

// ---------------------------------------------------------------------------
// Despacho. Deste ponto para baixo está tudo pronto.
// ---------------------------------------------------------------------------

async function chamarFerramenta(parametros: Record<string, unknown>) {
  const nome = String(parametros.name ?? "");
  const argumentos = (parametros.arguments ?? {}) as Record<string, unknown>;

  try {
    if (nome === "buscar_em_contratos") return await buscarEmContratos(argumentos);
    if (nome === "consultar_pedido") return await consultarPedido(argumentos);
    throw new Error(`ferramenta desconhecida: ${nome}`);
  } catch (erro) {
    // Erro de ferramenta NÃO é erro de protocolo. Ele volta como resultado
    // com `isError`, para o modelo poder ler o motivo e tentar outro caminho.
    // Devolver erro de JSON-RPC aqui derrubaria a conversa inteira por causa
    // de um serviço fora do ar.
    return {
      content: [{ type: "text", text: `falhou: ${(erro as Error).message}` }],
      isError: true,
    };
  }
}

async function tratar(mensagem: Mensagem): Promise<void> {
  const { id, method, params } = mensagem;

  // Notificação não tem id e não recebe resposta. Responder a uma delas é o
  // erro que faz o cliente fechar a conexão sem explicar por quê.
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
