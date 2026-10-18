-- =====================================================================
-- Passo 4, companheiro: o operador de distância em SQL puro.
-- =====================================================================
--
-- A lacuna avaliada do Passo 4 está em `rag/busca.py`. Este arquivo existe
-- para você ver o mesmo operador funcionando **sem Python, sem FastAPI e sem
-- Ollama no caminho**, e concluir por conta própria que não há mágica nenhuma
-- na busca semântica: é um ORDER BY.
--
-- O truque para dispensar o Ollama aqui é usar, como vetor da pergunta, o
-- vetor de um trecho que já está no banco. A pergunta passa a ser "quais são
-- os trechos mais parecidos com este trecho", que é a mesma operação.
--
--     docker compose exec -T postgres psql -U logitech -d logitech < sql/04-busca.sql
--
-- Este arquivo não tem lacuna.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 4.1  Os três operadores de distância do pgvector
-- ---------------------------------------------------------------------
--     <=>   distância de cosseno       1 menos a similaridade, faixa de 0 a 2
--     <->   distância euclidiana (L2)  o comprimento da reta entre as pontas
--     <#>   produto interno negativo   mais barato, exige vetor normalizado
--
-- Em dois vetores construídos à mão, sem modelo nenhum:

SELECT '[1,0,0]'::vector <=> '[1,0,0]'::vector AS iguais_cosseno,
       '[1,0,0]'::vector <=> '[0,1,0]'::vector AS ortogonais_cosseno,
       '[1,0,0]'::vector <=> '[-1,0,0]'::vector AS opostos_cosseno,
       '[1,0,0]'::vector <=> '[9,0,0]'::vector AS mesma_direcao_outro_tamanho;

-- A última coluna é a razão de o cosseno ser o padrão em busca de texto:
-- `[9,0,0]` é nove vezes maior que `[1,0,0]` e aponta para o mesmo lado, e a
-- distância de cosseno entre os dois é **zero**. O que importa é a direção do
-- significado, não o tamanho do vetor.


-- ---------------------------------------------------------------------
-- 4.2  A mesma comparação pela distância euclidiana
-- ---------------------------------------------------------------------
SELECT '[1,0,0]'::vector <-> '[1,0,0]'::vector AS iguais_l2,
       '[1,0,0]'::vector <-> '[0,1,0]'::vector AS ortogonais_l2,
       '[1,0,0]'::vector <-> '[9,0,0]'::vector AS mesma_direcao_outro_tamanho_l2;

-- Aqui a última coluna vale 8, e não zero. A euclidiana enxerga tamanho.
-- Trocar de operador troca o que a sua busca considera "parecido", e o índice
-- precisa ser criado para o operador que você vai usar.


-- ---------------------------------------------------------------------
-- 4.3  Trechos parecidos com um trecho, sobre o acervo real
-- ---------------------------------------------------------------------
-- O trecho de referência é o primeiro que fala em prazo de reclamação de
-- avaria. A consulta devolve os cinco mais próximos dele, e o `WHERE t.id <>`
-- tira o próprio, que teria distância zero e ocuparia a primeira posição sem
-- informar nada.
--
-- Repare na estrutura: é o SELECT com JOIN, ORDER BY e LIMIT do Passo 3, com
-- uma expressão diferente no ORDER BY. Só isso.

WITH referencia AS (
    SELECT id, embedding
    FROM conhecimento.trechos
    WHERE texto ILIKE '%prazo de reclama%'
    ORDER BY id
    LIMIT 1
)
SELECT c.titulo,
       t.ordem,
       ROUND((t.embedding <=> r.embedding)::numeric, 4) AS distancia,
       left(regexp_replace(t.texto, '\s+', ' ', 'g'), 80) AS inicio
FROM conhecimento.trechos AS t
JOIN conhecimento.contratos AS c ON c.id = t.contrato_id
CROSS JOIN referencia AS r
WHERE t.id <> r.id
ORDER BY t.embedding <=> r.embedding
LIMIT 5;

-- O que você deve ver: as cláusulas de avaria e indenização dos **outros**
-- contratos aparecem no topo, mesmo escritas com palavras diferentes. Nenhuma
-- delas foi encontrada por igualdade de texto.
