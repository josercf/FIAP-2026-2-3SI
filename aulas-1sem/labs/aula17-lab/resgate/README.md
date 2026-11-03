# `resgate/` - a rede de segurança

Duas coisas moram aqui, e as duas existem para ninguém travar:

| Arquivo | O que é |
|---|---|
| `docker-compose.yml` | A plataforma com as **seis falhas corrigidas**, cada uma explicada no lugar onde estava |
| `docs/EVIDENCIAS.md` | As evidências **medidas na preparação** deste laboratório, em 31/07/2026 |

## Como usar

```bash
cp resgate/docker-compose.yml docker-compose.yml
docker compose up -d --wait
```

Registre em `docs/EVIDENCIAS.md`, no marcador `USEI_O_RESGATE`, em qual falha
você recorreu. Não há penalidade automática por isso.

## O que o resgate não resolve

Ele deixa a Frente 1 verde e deixa vocês sem resposta na banca.

A pergunta que a banca faz não é "a plataforma sobe?". É **"por que o serviço X
ficou unhealthy, e como vocês descobriram?"**. Essa resposta não está no arquivo
corrigido: está no caminho até ele, no `docker inspect` que mostrou
"Connection refused" com o serviço no ar, no `Exited (0)` sem erro no log.

Se for usar, use assim: corrija uma falha pelo resgate, entenda por que aquela
linha muda o desfecho, e volte a diagnosticar as outras sozinho.

## E o `docs/EVIDENCIAS.md` daqui, não é gabarito?

Não, e copiá-lo é a pior ideia possível.

Os números ali são da máquina de preparação: um M4 com 16 GB. Se o
`docs/EVIDENCIAS.md` de vocês disser `806 MB` e a máquina de vocês for outra, a
primeira pergunta da banca derruba a apresentação inteira. Ele está aqui para
mostrar **como um registro completo se parece**, não o que ele deve dizer.
