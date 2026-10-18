---
name: logitech-dockerfile
description: Escreve Dockerfiles multi-stage para os servicos da plataforma LogiTech, em Python e Node
---

# Dockerfile da LogiTech

## Regras que não se negociam

1. Sempre dois estágios nomeados, `builder` e `runtime`.
2. Base alpine no estágio final. Nunca base full em produção.
3. Usuário não-root criado no estágio final, com UID acima de 10000.
4. Nunca `COPY . .`. Nomear cada arquivo ou diretório que entra.
5. `EXPOSE` declarando a porta real do serviço: 8081/udp no coletor, 3000 no gateway.
6. O caminho de dados vem de `LOGITECH_DADOS` e cai para `/dados/telemetria.jsonl`.

## Ordem das instruções

Instalar dependências antes de copiar código, para o cache de camadas
sobreviver a mudança de código.

## O que nunca entra na imagem final

Compilador, gerenciador de pacote, teste, `.git`, `node_modules` de
desenvolvimento e o próprio Dockerfile.
