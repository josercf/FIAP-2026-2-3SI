# Etapa 7, Registry e Docker Hub

## Enunciado

Publique a imagem final do coletor no Docker Hub, pública, e confirme que
ela responde sem estar logado. É essa resposta pública que fecha o ciclo:
uma imagem só é útil em produção quando outra máquina, sem as suas
credenciais nem o seu histórico de build, consegue puxar ela.

Este é o único ciclo com pré-requisito fora do laboratório: a **conta no
Docker Hub**, criada e verificada antes da aula.

## Comando

```bash
docker login

# troque SEU_USUARIO pelo seu usuário real do Docker Hub
docker tag coletor:final SEU_USUARIO/logitech-coletor:1.0
docker push SEU_USUARIO/logitech-coletor:1.0

# confirme que responde publicamente, sem sessão aberta
docker logout
docker manifest inspect SEU_USUARIO/logitech-coletor:1.0
```

O `docker manifest inspect` precisa devolver o manifesto (JSON com
`schemaVersion`), não um erro de acesso negado. Se der erro, confira se o
repositório está marcado como público nas configurações do Docker Hub.

## O que registrar

Registre em `docs/EVIDENCIAS.md`, não aqui: `IMAGEM_PUBLICA`, no formato
`usuario/imagem:tag`. O verificador chama `docker manifest inspect` nesse
valor de verdade: o texto sozinho não basta, a imagem precisa responder no
registry.

## Resposta

```
Valor registrado em docs/EVIDENCIAS.md: PREENCHER (sim/não)
```
