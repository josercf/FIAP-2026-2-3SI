-- =====================================================================
-- Passo 5: índice e EXPLAIN. O que o banco faz quando ninguém olha.
-- =====================================================================
--
-- Até aqui toda busca varreu a tabela inteira, calculou a distância de cada
-- linha e ordenou. Com 44 trechos isso é instantâneo e ninguém percebe. Com
-- 50.000, que é a ordem de grandeza de um acervo de contratos de verdade, a
-- mesma consulta deixa de responder.
--
-- Este passo tem duas metades, e a primeira vale mais: aprender a **perguntar
-- ao banco o que ele pretende fazer** antes de reclamar do tempo.
--
--     docker compose exec -T postgres psql -U logitech -d logitech < sql/05-indice.sql
-- =====================================================================

\timing on


-- ---------------------------------------------------------------------
-- 5.0  Um vetor real guardado em uma variável do psql
-- ---------------------------------------------------------------------
-- `\gset` guarda o resultado de uma consulta de uma linha em variáveis do
-- cliente, uma por coluna. Depois, `:'alvo'` é substituído pelo valor entre
-- aspas antes de o comando sair do psql.
--
-- Isto não é firula: é o que permite o índice entrar no plano. Um índice de
-- vizinhança precisa de um ponto de partida constante para caminhar no grafo.
-- Se o vetor de comparação vier de uma subconsulta, o planejador não tem esse
-- ponto e cai na varredura sequencial, com índice criado e tudo.

SELECT embedding AS alvo FROM conhecimento.trechos ORDER BY id LIMIT 1
\gset


-- ---------------------------------------------------------------------
-- 5.1  O plano ANTES do índice
-- ---------------------------------------------------------------------
-- `EXPLAIN ANALYZE` executa a consulta de verdade e mostra o plano com os
-- tempos medidos. Sem `ANALYZE` ele mostra apenas a estimativa.
--
-- Procure na saída, nesta ordem:
--
--   Seq Scan on trechos        -> varreu a tabela inteira, linha por linha
--   Sort  /  Top-N heapsort    -> ordenou o resultado em memória
--   Execution Time             -> o número que interessa
--
-- Copie a linha do `Seq Scan` e o `Execution Time` para
-- `EXPLAIN_SEM_INDICE` em docs/EVIDENCIAS.md.

EXPLAIN ANALYZE
SELECT id FROM conhecimento.trechos
ORDER BY embedding <=> :'alvo'::vector
LIMIT 5;


-- ---------------------------------------------------------------------
-- TODO-5: crie o índice de vizinhança aproximada.
-- ---------------------------------------------------------------------
-- Duas lacunas:
--
--   5-1  O método de acesso. O pgvector oferece dois:
--
--          hnsw    grafo navegável em camadas. Constrói mais devagar e ocupa
--                  mais espaço, e é o mais rápido para consultar. É o padrão
--                  quando o acervo cresce e a leitura domina, que é o caso de
--                  um acervo de contratos.
--
--          ivfflat constrói mais rápido e ocupa menos, e exige que a tabela já
--                  tenha dados representativos no momento da criação, porque
--                  particiona o espaço a partir do que existe.
--
--        Use o primeiro. O nome do índice já diz qual é.
--
--   5-2  A classe de operadores. Índice de vetor é criado para um operador
--        específico, e não serve para os outros:
--
--          vector_cosine_ops  serve ao  <=>
--          vector_l2_ops      serve ao  <->
--          vector_ip_ops      serve ao  <#>
--
--        Criar com a classe errada não dá erro: o índice nasce, ocupa espaço e
--        o planejador simplesmente o ignora. É aí que o EXPLAIN deixa de ser
--        curiosidade e vira ferramenta.
--
-- Os dois parâmetros do WITH são o compromisso do HNSW: quanto maiores, melhor
-- a recuperação e mais lenta a construção. Abaixo estão os padrões da extensão.

CREATE INDEX IF NOT EXISTS trechos_embedding_hnsw
    ON conhecimento.trechos
 USING ____ (embedding ____)
  WITH (m = 16, ef_construction = 64);


-- Atualiza as estatísticas da tabela. Sem isso o planejador decide com base em
-- números velhos e pode ignorar um índice recém-criado.
ANALYZE conhecimento.trechos;


-- ---------------------------------------------------------------------
-- 5.2  O plano DEPOIS do índice, com o planejador decidindo sozinho
-- ---------------------------------------------------------------------
-- Surpresa provável: ainda aparece `Seq Scan`.
--
-- Isso não é erro seu e não invalida o índice. Com 44 linhas cabendo em uma
-- página de memória, o planejador calcula que varrer tudo custa menos do que
-- caminhar por um grafo, e ele está certo. Índice não é obrigação: é uma opção
-- que o banco usa quando compensa.

EXPLAIN ANALYZE
SELECT id FROM conhecimento.trechos
ORDER BY embedding <=> :'alvo'::vector
LIMIT 5;


-- ---------------------------------------------------------------------
-- 5.3  O plano DEPOIS do índice, pedindo o outro caminho
-- ---------------------------------------------------------------------
-- `enable_seqscan = off` não proíbe a varredura: ele a encarece o suficiente
-- para o planejador preferir qualquer alternativa. É ferramenta de
-- diagnóstico, e nunca configuração de produção.
--
-- Agora o plano precisa mostrar:
--
--   Index Scan using trechos_embedding_hnsw on trechos
--
-- Se continuar aparecendo `Seq Scan` aqui, o índice não existe ou foi criado
-- com a classe de operadores errada. Copie esta linha e o `Execution Time`
-- para `EXPLAIN_COM_INDICE`.

SET enable_seqscan = off;

EXPLAIN ANALYZE
SELECT id FROM conhecimento.trechos
ORDER BY embedding <=> :'alvo'::vector
LIMIT 5;

RESET enable_seqscan;


-- ---------------------------------------------------------------------
-- 5.4  Quanto o índice custa em disco
-- ---------------------------------------------------------------------
SELECT indexrelname AS indice,
       pg_size_pretty(pg_relation_size(indexrelid)) AS tamanho
FROM pg_stat_user_indexes
WHERE schemaname = 'conhecimento'
ORDER BY indexrelname;


-- ---------------------------------------------------------------------
-- 5.5  A conversa honesta sobre o que você acabou de medir
-- ---------------------------------------------------------------------
-- Com 44 trechos o índice não ganha nada, e ninguém aqui vai fingir que ganha.
-- O que este passo prova é a mudança de plano: o banco deixou de varrer e
-- passou a navegar, e você sabe pedir os dois e comparar.
--
-- O ganho aparece com escala, e foi medido na preparação deste laboratório,
-- nesta mesma imagem, com 50.000 vetores de 768 dimensões:
--
--     sem índice   Seq Scan     Execution Time  389,933 ms
--     com índice   Index Scan   Execution Time    1,005 ms
--     construção do índice                       24,46 s
--     índice em disco                            161 MB
--
-- Registre os SEUS números como eles saíram, inclusive se o segundo for maior
-- que o primeiro. Número medido vale mais do que número esperado.
--
-- Quem quiser reproduzir a medição de escala tem o roteiro na seção
-- "O ganho do índice, medido em escala" do README. Leva cerca de 30 segundos e
-- é leitura de depois do Passo 6.


-- ---------------------------------------------------------------------
-- 5.6  A recuperação aproximada tem preço, e o preço é a exatidão
-- ---------------------------------------------------------------------
-- HNSW é busca de vizinho aproximado: ele pode não devolver o vizinho mais
-- próximo de verdade. O parâmetro abaixo controla quanto o índice explora
-- antes de responder, e é ajustável por sessão.
--
--     SET hnsw.ef_search = 40;    -- padrão
--     SET hnsw.ef_search = 200;   -- mais lento, mais exato
--
-- Não há valor certo: há um compromisso, e ele depende de quanto custa errar
-- na sua aplicação. Em busca de cláusula de contrato, errar custa caro.
