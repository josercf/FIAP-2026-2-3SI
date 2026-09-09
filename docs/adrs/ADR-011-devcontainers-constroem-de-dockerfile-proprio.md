# ADR-011: Os devcontainers dos laboratórios constroem de Dockerfile próprio

- **Data:** 2026-09-08
- **Status:** Aceita
- **Decisores:** Prof. José Romualdo da Costa Filho

## Contexto

Em 08/09/2026, durante a aplicação da Aula 05, a turma não conseguiu rodar o
laboratório: `docker` não existia no Codespace. O log de criação mostrou que o
build do devcontainer havia falhado inteiro, e que o Codespaces tinha entregue
um **container de recuperação** (`base:alpine`), sem Docker, sem Java e sem
.NET.

A causa não estava no repositório. A imagem oficial
`mcr.microsoft.com/devcontainers/java:1-21-bookworm` traz o repositório apt do
Yarn pré-configurado em `/etc/apt/sources.list.d/yarn.list`, e a chave GPG desse
repositório expirou (`NO_PUBKEY 62D54FD4003F6525`). Como todo feature do
devcontainer começa por um `apt-get update`, o apt passou a sair com código 100,
o primeiro feature abortou e derrubou o build.

A verificação das demais imagens do acervo mostrou o mesmo repositório quebrado
em `devcontainers/python:1-3.12-bookworm` e em `devcontainers/universal:2-linux`.
Nove dos onze laboratórios estavam na mesma condição: 03, 05, 06, 07, 08, 10,
12, 14, 15 e 16. Apenas a Aula 11, em `typescript-node:1-22-bookworm`, escapou,
porque essa imagem já havia sido corrigida na origem.

Nenhuma linha dos laboratórios tinha mudado. O que apodreceu foi uma dependência
transitiva das imagens base, fora do repositório e sem aviso.

A investigação com build real expôs, junto, quatro defeitos que o `devcontainer.json`
declarativo não conseguia expressar nem revelar:

| Defeito | Onde | Como se manifestava |
|---|---|---|
| Chave GPG do Yarn expirada | 10 labs | build do devcontainer falha inteiro |
| Maven ausente na imagem base de Java | Aula 05 | `mvn spring-boot:run` do Passo 1 impossível |
| Feature `dotnet` sem versão instalando o SDK 10 | Aula 05 | `global.json` pede 8.0.0 e o build aborta |
| Python sem biblioteca padrão (`python3-minimal`) | Aula 05 | `verificar.py` morre em `import json` |
| Feature `postgresql-client:1` inexistente no registro | Aula 12 | build falha sozinho, com 403 |

## Decisão

Todo laboratório cuja imagem base carregue repositório apt quebrado passa a
declarar `build.dockerfile` em vez de `image`, e o Dockerfile sanea a base antes
que os features rodem.

```dockerfile
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

RUN rm -f /etc/apt/sources.list.d/yarn.list \
 && apt-get update \
 && rm -rf /var/lib/apt/lists/*
```

Junto, três regras que decorrem dos outros defeitos:

1. **Todo feature declara versão explícita** quando o laboratório depende de
   uma. O `dotnet` da Aula 05 está fixado em `8.0`.
2. **Ferramenta que o laboratório usa no passo a passo é verificada dentro do
   container**, e não presumida a partir do nome da imagem.
3. **O `devcontainer-lock.json` é versionado**, fixando por digest os features
   efetivamente validados.

A verificação é automatizada em `tools/check_devcontainers.py`.

## Motivações

**Por que Dockerfile e não reimportar a chave do Yarn.** Reimportar dependeria
de um servidor de chaves respondendo durante o build de cada aluno, o que troca
uma dependência frágil por outra. Remover o repositório é determinístico, e
nenhum laboratório usa Yarn.

**Por que não trocar a imagem base.** Trocar mexeria nas versões de Java, Python
e .NET que os laboratórios assumem, e os testes de cada lab dependem delas.

**Por que a correção não pode viver só no `postCreateCommand`.** Os features são
aplicados durante o build, antes de qualquer comando de pós-criação. Quando o
`postCreate` roda, o build já falhou.

**Por que instalar o Maven pelo tarball, e não pelo feature `java`.** Com o JDK
já presente na imagem, esse feature reaponta o `JAVA_HOME` para um diretório do
SDKMAN que fica vazio, e o Maven recusa a execução com `JAVA_HOME is not
defined correctly`. O tarball oficial não toca no JDK da imagem.

## Riscos conhecidos

| Risco | Mitigação |
|---|---|
| Outra dependência transitiva das imagens base apodrecer do mesmo jeito | `tools/check_devcontainers.py` roda `apt-get update` na base e falha antes da aula |
| O Dockerfile diverge entre os onze repositórios publicados | O acervo é a fonte, e o validador roda sobre todos de uma vez |
| Fixar `dotnet` em 8.0 congela o laboratório numa versão que envelhece | A versão é a que o `global.json` do lab exige; mudar as duas juntas é uma decisão consciente |
| O aluno com Codespace já criado continua no container de recuperação | Sincronizar o fork e rodar o Full Rebuild Container, documentado no slide 43 da Aula 05 |
| Remover o `yarn.list` quebraria um lab que viesse a usar Yarn | Nenhum usa; o binário do Yarn continua instalado, só não se atualiza por apt |

## Consequências

**Positivas**

- Os onze devcontainers constroem, e as ferramentas prometidas foram conferidas
  dentro de cada container.
- O acervo passa a ter uma verificação executável para uma classe de falha que
  antes só aparecia com a turma na sala.
- O `devcontainer-lock.json` torna reproduzível o ambiente que foi validado.

**Negativas**

- Cada lab ganha um arquivo a mais para manter, e o build fica alguns segundos
  mais lento por causa da camada extra.
- O saneamento é um remendo sobre um defeito de terceiro. Quando a Microsoft
  corrigir as imagens, as linhas continuarão lá sem efeito, e removê-las exige
  uma passada deliberada.
- O validador depende de Docker e, na checagem de build, de rede, o que o torna
  lento demais para um hook de edição.

## ADRs relacionadas

- **ADR-005**, que tornou o Ollama local o único backend de IA dos laboratórios
  e definiu o que o `postCreateCommand` instala.
