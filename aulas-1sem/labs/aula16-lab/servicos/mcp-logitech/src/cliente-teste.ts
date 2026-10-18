/**
 * Cliente de teste do `mcp-logitech`, falando stdio.
 *
 * Existe por um motivo prático: não dá para a aula depender de qual ferramenta
 * de IA cada pessoa tem instalada. Este cliente sobe o servidor como processo
 * filho, cumpre o aperto de mão do MCP e exercita o que o servidor expõe.
 * Funciona em qualquer máquina com Node, sem conta, sem chave e sem instalar
 * nada.
 *
 * Ele também é a melhor forma de entender o protocolo: são cinco mensagens, e
 * dá para ler todas com `--verboso`.
 *
 *     npm test                                  # o roteiro completo
 *     npm test -- --verboso                     # mostrando as mensagens cruas
 *     npm test -- --pergunta "prazo de avaria"  # com outra pergunta
 *     npm test -- --json                        # saída para o verificar.py
 *
 * Não é tarefa. Este arquivo vem pronto.
 */

import { spawn } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { enviar, receber, type Mensagem } from "./protocolo.ts";

const AQUI = dirname(fileURLToPath(import.meta.url));
const SERVIDOR = join(AQUI, "servidor.ts");

const argumentos = process.argv.slice(2);
const verboso = argumentos.includes("--verboso");
const saidaJson = argumentos.includes("--json");
// `--sem-busca` para no aperto de mão e na descoberta, sem chamar a ferramenta.
// É o modo que o healthcheck do Compose usa: ele precisa responder "o servidor
// MCP está de pé e anuncia as ferramentas", e não "o RAG achou o trecho certo".
// Misturar as duas perguntas faria o container do MCP ficar unhealthy por causa
// de uma ingestão que ainda não rodou, mandando quem depura para o lugar errado.
const semBusca = argumentos.includes("--sem-busca");
const PERGUNTA =
  valorDe("--pergunta") ??
  "quanto tempo o cliente tem para pedir ressarcimento de mercadoria danificada";

function valorDe(bandeira: string): string | undefined {
  const i = argumentos.indexOf(bandeira);
  return i >= 0 ? argumentos[i + 1] : undefined;
}

function dizer(...partes: unknown[]): void {
  if (!saidaJson) console.log(...partes);
}

const filho = spawn(process.execPath, ["--experimental-strip-types", SERVIDOR], {
  stdio: ["pipe", "pipe", "inherit"],
  env: process.env,
});

const pendentes = new Map<number, (m: Mensagem) => void>();
let proximoId = 1;

receber(filho.stdout, (mensagem) => {
  if (verboso) console.error("<<", JSON.stringify(mensagem));
  const resolver = pendentes.get(Number(mensagem.id));
  if (resolver) {
    pendentes.delete(Number(mensagem.id));
    resolver(mensagem);
  }
});

function pedir(method: string, params: Record<string, unknown> = {}): Promise<Mensagem> {
  const id = proximoId++;
  const mensagem: Mensagem = { jsonrpc: "2.0", id, method, params };
  if (verboso) console.error(">>", JSON.stringify(mensagem));
  return new Promise((resolver, rejeitar) => {
    const relogio = setTimeout(
      () => rejeitar(new Error(`sem resposta para ${method} em 180 s`)),
      180000,
    );
    pendentes.set(id, (m) => {
      clearTimeout(relogio);
      resolver(m);
    });
    enviar(filho.stdin, mensagem);
  });
}

function notificar(method: string): void {
  enviar(filho.stdin, { jsonrpc: "2.0", method });
}

async function principal(): Promise<number> {
  // 1. Aperto de mão. O cliente diz qual versão do protocolo fala e o que ele
  //    sabe fazer; o servidor responde com as capacidades dele.
  const inicio = await pedir("initialize", {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "cliente-teste-logitech", version: "1.0.0" },
  });
  const servidor = (inicio.result as any)?.serverInfo?.name ?? "(desconhecido)";
  dizer(`1. initialize        servidor: ${servidor}`);

  // 2. Notificação: sem id, sem resposta. Marca o fim do aperto de mão.
  notificar("notifications/initialized");

  // 3. Descoberta das ferramentas. É esta lista que o modelo lê para decidir
  //    o que chamar, e é o que torna o MCP um protocolo e não uma integração.
  const listaFerramentas = await pedir("tools/list");
  const ferramentas = ((listaFerramentas.result as any)?.tools ?? []) as {
    name: string;
  }[];
  dizer(`2. tools/list        ${ferramentas.map((f) => f.name).join(", ")}`);

  // 4. Descoberta dos recursos.
  const listaRecursos = await pedir("resources/list");
  const recursos = ((listaRecursos.result as any)?.resources ?? []) as {
    uri: string;
  }[];
  dizer(`3. resources/list    ${recursos.length} contratos`);

  let recursoOk = false;
  if (recursos.length > 0) {
    const leitura = await pedir("resources/read", { uri: recursos[0].uri });
    const texto = ((leitura.result as any)?.contents ?? [{}])[0]?.text ?? "";
    recursoOk = texto.length > 200;
    dizer(`4. resources/read    ${recursos[0].uri}: ${texto.length} caracteres`);
  }

  if (semBusca) {
    const bastante = ferramentas.length >= 1 && recursos.length >= 1;
    if (saidaJson) {
      console.log(
        JSON.stringify({
          servidor,
          ferramentas: ferramentas.map((f) => f.name),
          recursos: recursos.length,
          recursoOk,
          modo: "sem-busca",
        }),
      );
    }
    return bastante && recursoOk ? 0 : 1;
  }

  // 5. Chamada da ferramenta.
  const chamada = await pedir("tools/call", {
    name: "buscar_em_contratos",
    arguments: { pergunta: PERGUNTA, k: 4 },
  });
  const resultado = chamada.result as any;
  const texto: string = (resultado?.content ?? [{}])[0]?.text ?? "";
  const deuErro = Boolean(resultado?.isError) || Boolean(chamada.error);

  dizer("");
  dizer(`5. tools/call buscar_em_contratos`);
  dizer(`   pergunta: ${PERGUNTA}`);
  dizer("");
  dizer(texto || `(sem texto) ${JSON.stringify(chamada.error ?? {})}`);

  if (saidaJson) {
    console.log(
      JSON.stringify({
        servidor,
        ferramentas: ferramentas.map((f) => f.name),
        recursos: recursos.length,
        recursoOk,
        erro: deuErro,
        texto,
      }),
    );
  }

  return deuErro ? 1 : 0;
}

principal()
  .then((codigo) => {
    filho.stdin.end();
    filho.kill();
    process.exit(codigo);
  })
  .catch((erro) => {
    console.error("cliente-teste falhou:", erro.message);
    filho.stdin.end();
    filho.kill();
    process.exit(1);
  });
