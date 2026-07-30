# Lab Aula 15 - Segurança AI-First & Trivy

Neste laboratório, atacaremos dois problemas modernos:
1. Imagens Docker vulneráveis
2. Prompt Injections em aplicações LLM (OWASP Top 10 for LLMs)

## Parte 1: Trivy Scanner

1. Certifique-se de ter o `trivy` instalado no seu computador.
   - Mac: `brew install aquasecurity/trivy/trivy`
   - Linux: `sudo apt-get install trivy`
2. Escaneie o arquivo `Dockerfile.vulnerable` fornecido:
   ```bash
   trivy config ./Dockerfile.vulnerable
   ```
3. Observe os erros críticos (`CRITICAL`). A versão do Node.js usada é extremamente antiga e roda como `root`.
4. **Desafio:** Crie um novo `Dockerfile.secure` utilizando `node:18-alpine` (ou `20-alpine`) e adicione instruções para rodar com o usuário `node` não-privilegiado. Rode o Trivy nele e garanta que está limpo!

## Parte 2: Defesa de Prompt Injection

1. Certifique-se de ter Python instalado (`python3`).
2. Execute o script de simulação:
   ```bash
   python llm_defense.py
   ```
3. Observe como o "Teste 1" falha miseravelmente, pois o LLM não consegue separar o que é Instrução do Desenvolvedor vs Comando do Usuário.
4. No "Teste 2", utilizamos a técnica de **Delimitadores**. Ao colocar o input do usuário entre ` ``` `, o LLM entende que aquilo são dados, e não comandos de sistema. 
5. **Desafio:** Altere o código `llm_defense.py` para incluir uma nova estratégia defensiva (ex: avaliar a intenção da mensagem com outro prompt menor antes de mandar para o fluxo principal).
