# Rastreamento da transportadora parceira (congelado)

**Este serviço não é tarefa do laboratório. Não edite nada aqui dentro.**

Ele faz o papel do sistema de uma empresa de fora: a transportadora parceira
que leva a carga da LogiTech no trecho final. O formato de resposta dela é
legado, abreviado e diferente do nosso, e é assim de propósito.

## Subir

```bash
python3 servicos/parceira-rastreio/servidor.py
```

Fica na porta `9090`. Sem dependências: só a biblioteca padrão do Python.

## Consultar

```bash
curl "http://localhost:9090/consulta?objeto=BR9912345"
```

```json
{
  "COD_OBJ": "BR9912345",
  "DT_ULT_MOV": "08/09/2026 14:32",
  "SIT": "EM_TRANSITO",
  "UF_ULT": "SP",
  "DESC_SIT": "Objeto em transito para a unidade de destino"
}
```

## Por que ele existe

Sem um formato alheio de verdade, o Adapter da lacuna `TODO-4` vira exercício
de tradução de dicionário. Com ele, a pergunta certa aparece sozinha: quantos
arquivos do serviço de notificações podem saber que existe um campo chamado
`COD_OBJ`? A resposta é um: `src/adaptador.ts`.

O serviço de notificações fala com este endereço pela variável
`LOGITECH_RASTREIO_PARCEIRA_URL`, com padrão `http://localhost:9090`, como
manda a ADR-006. Na Aula 07 o valor dessa variável muda para o nome do
serviço dentro da rede `logitech-net`, e nenhuma linha de código muda junto.
