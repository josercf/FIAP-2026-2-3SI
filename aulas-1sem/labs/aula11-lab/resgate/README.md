# Resgate da Aula 11: rede de segurança, não atalho

Aqui estão os três arquivos com as **seis lacunas preenchidas**, e um
`docs/EVIDENCIAS.md` com os números de uma execução de referência.

Eles existem pelo mesmo motivo que o `resgate/` existiu nas Aulas 03 e 07:
travar no TODO-2 não pode matar os TODO-3, TODO-4, TODO-5 e TODO-6. O fluxo
de frota é a base de três lacunas seguidas, e uma dupla presa no
`new Observable` perderia a aula inteira sem isto.

## Se você usar

Registre em `docs/EVIDENCIAS.md`, no topo:

```
USEI_O_RESGATE: sim, a partir do TODO-N
```

Usar o resgate não reprova critério nenhum que o verificador consiga
confirmar por máquina. É informação que o professor precisa ter, não
armadilha. Um `git log` que mostra a dupla travada em uma lacuna por vinte
minutos e depois seguindo em frente é uma história melhor do que um fork
abandonado no meio.

## Como usar

A partir da **raiz do laboratório**, copie só o arquivo da lacuna em que você
travou:

```bash
# TODO-1b (a cadeia HTTP com o interceptador)
cp resgate/painel-admin/src/app/app.config.ts painel-admin/src/app/app.config.ts

# TODO-2, TODO-3, TODO-4 e TODO-5 (o fluxo de frota inteiro)
cp resgate/painel-admin/src/app/frota/frota.service.ts painel-admin/src/app/frota/frota.service.ts

# TODO-1a e TODO-6 (o serviço no injetor raiz e a busca sem corrida)
cp resgate/painel-admin/src/app/faturas/faturamento.service.ts painel-admin/src/app/faturas/faturamento.service.ts
```

Copiar `frota.service.ts` resolve quatro lacunas de uma vez, porque as quatro
moram no mesmo arquivo. Se você travou só no TODO-2, copie, leia o que está
lá, e **apague os outros três métodos de volta** antes de seguir. O objetivo
é destravar, não pular.

## O que o resgate não traz

- Os componentes, o núcleo e as suítes de teste: nada disso é lacuna, e o que
  está no laboratório já é a versão final.
- Os serviços de `servicos/`: eles chegam congelados e prontos.
- Os seus números de `docs/EVIDENCIAS.md`. O arquivo aqui é da execução de
  referência, feita na construção do kit em 31/07/2026, com 12 caminhões no
  simulador. Copiar aqueles números para o seu formulário é declarar uma
  medição que você não fez, e o `verificar.py` prova o cancelamento ao vivo
  contra o serviço que **está** rodando na sua máquina.
