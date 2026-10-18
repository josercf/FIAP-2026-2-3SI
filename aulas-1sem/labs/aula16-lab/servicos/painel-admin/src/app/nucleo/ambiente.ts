/**
 * Endereços dos serviços da plataforma LogiTech consumidos por este painel.
 *
 * A ADR-006 manda que endereço de serviço nunca apareça cravado no meio do
 * código, e a ADR-008 registra a consequência prática no Angular: aqui a
 * configuração de ambiente é **arquivo**, não variável de processo. O
 * navegador não tem `process.env`, e o que existisse ali estaria no bundle de
 * qualquer forma. Por isso os nomes canônicos do contrato viram campos deste
 * objeto, e é este arquivo que muda quando o painel sai do `localhost` e
 * entra no Compose da Aula 07.
 *
 * | Nome no contrato (ADR-006) | Campo aqui        | Serviço      | Porta |
 * |----------------------------|-------------------|--------------|-------|
 * | LOGITECH_FATURAMENTO_URL   | faturamentoUrl    | faturamento  | 5080  |
 * | LOGITECH_PAINEL_URL        | painelUrl         | painel       | 3000  |
 * | LOGITECH_OIDC_ISSUER       | oidcAutoridade    | keycloak     | 8090  |
 * | LOGITECH_OIDC_CLIENT_ID    | oidcClientId      | keycloak     | 8090  |
 *
 * Nada de segredo entra aqui. Tudo neste arquivo é público por construção:
 * ele vai inteiro para dentro do JavaScript que o navegador baixa.
 */
export const AMBIENTE = {
  /** Serviço de Faturamento, C#/.NET, nascido na Aula 05. */
  faturamentoUrl: 'http://localhost:5080',

  /** Painel de rastreamento, Node, nascido na Aula 02. */
  painelUrl: 'http://localhost:3000',

  /**
   * Provedor de identidade, Keycloak, nascido na Aula 14 (ADR-009).
   *
   * O endereço é o do NAVEGADOR (`localhost:8090`), e é ele que acaba dentro
   * do `iss` do token. Os serviços de backend buscam o JWKS por outro
   * endereço, o da rede interna do Compose (`keycloak:8090`). Os dois não
   * coincidem, e é por isso que o contrato tem duas variáveis em vez de uma.
   */
  oidcAutoridade: 'http://localhost:8090/realms/logitech',
  oidcClientId: 'logitech-painel-admin',
} as const;
