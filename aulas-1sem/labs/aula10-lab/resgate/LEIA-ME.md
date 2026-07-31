# Resgate: rede de segurança, não atalho

Este diretório traz as seis lacunas resolvidas. Ele existe pelo mesmo motivo
que existia na Aula 03 e na Aula 07: travar no `TODO-2` não pode matar os
`TODO-4`, `TODO-5` e `TODO-6`.

Se você usar qualquer arquivo daqui, registre em `docs/EVIDENCIAS.md`:

```
USEI_O_RESGATE: sim, a partir do TODO-N
```

Usar o resgate **não reprova critério nenhum** que o verificador consiga
confirmar por máquina. É informação que o professor precisa ter, não
armadilha.

## Onde vai cada arquivo

| Arquivo do resgate | Destino |
|---|---|
| `frete/tests/test_cotador_stub.py` | `servicos/frete/tests/test_cotador_stub.py` |
| `frete/tests/test_cotador_mock.py` | `servicos/frete/tests/test_cotador_mock.py` |
| `frete/tests/test_cotador_spy.py` | `servicos/frete/tests/test_cotador_spy.py` |
| `portal/src/componentes/RastreioPedido.tsx` | `portal/src/componentes/RastreioPedido.tsx` |
| `portal/src/componentes/CotacaoFrete.tsx` | `portal/src/componentes/CotacaoFrete.tsx` |
| `portal/src/testes/CotacaoFrete.chamada.test.tsx` | `portal/src/componentes/CotacaoFrete.chamada.test.tsx` |

A partir da raiz do laboratório:

```bash
# só o TODO-1
cp resgate/frete/tests/test_cotador_stub.py servicos/frete/tests/

# tudo do bloco de testes de unidade
cp resgate/frete/tests/*.py servicos/frete/tests/

# tudo do portal
cp resgate/portal/src/componentes/*.tsx portal/src/componentes/
cp resgate/portal/src/testes/CotacaoFrete.chamada.test.tsx portal/src/componentes/
```

## Um conselho, e ele não é retórico

Copie o arquivo, rode o verificador para destravar, e **volte a ler o que
você copiou** antes de seguir. Nesta aula em particular, o resgate dos
`TODO-1`, `TODO-2` e `TODO-3` é curto e cada teste tem uma docstring
explicando por que ele existe e o que ele pegaria se o código quebrasse. É
material de estudo, não é código para passar batido.

O CP3 cobra a diferença entre Stub, Mock e Spy escrevendo teste, não
marcando alternativa.
