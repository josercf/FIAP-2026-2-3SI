-- =====================================================================
-- Passo 3: SELECT, JOIN, ORDER BY e LIMIT. Ainda sem vetor nenhum.
-- =====================================================================
--
-- As tabelas já existem e a ingestão já rodou. Antes de qualquer busca
-- semântica, o acervo é consultado como qualquer acervo relacional: junte as
-- duas tabelas, agrupe, ordene, corte.
--
-- Isto não é aquecimento. As duas consultas deste arquivo são a **mesma
-- estrutura** da busca semântica do Passo 4. Lá muda uma coisa só: a expressão
-- que vai no ORDER BY.
--
-- Cada consulta abaixo tem um nome, na linha `-- consulta: <nome>`. O
-- `verificar.py` procura por esses nomes, executa o comando que vem logo
-- abaixo e compara com o resultado que ele mesmo calcula. **Um comando por
-- bloco**, terminado em ponto e vírgula.
--
-- Para rodar o arquivo inteiro e ver as duas saídas:
--
--     docker compose exec -T postgres psql -U logitech -d logitech < sql/03-consultas.sql
-- =====================================================================


-- ---------------------------------------------------------------------
-- TODO-3a: quantos trechos cada contrato gerou, do maior para o menor,
--          e só os três primeiros.
-- ---------------------------------------------------------------------
-- Três lacunas, e cada uma é uma decisão:
--
--   3a-1  O tipo de junção. Aqui a pergunta é "quantos trechos cada contrato
--         gerou", e um contrato recém-cadastrado, ainda sem trechos, é uma
--         resposta legítima com o valor zero. Pense em qual junção preserva
--         essa linha e qual a descarta. Com o acervo já ingerido as duas
--         devolvem o mesmo, e é justamente por isso que a escolha precisa
--         ser pensada, e não testada por tentativa.
--
--   3a-2  A expressão de ordenação. Você quer o contrato mais fatiado no topo.
--
--   3a-3  O corte. Três linhas.
--
-- consulta: trechos_por_contrato
SELECT c.cliente,
       c.titulo,
       COUNT(t.id) AS trechos
FROM conhecimento.contratos AS c
____ conhecimento.trechos AS t ON t.contrato_id = c.id
GROUP BY c.id, c.cliente, c.titulo
ORDER BY ____ DESC
LIMIT ____;


-- ---------------------------------------------------------------------
-- TODO-3b: os cinco maiores trechos do acervo, cada um com o contrato
--          de onde ele veio.
-- ---------------------------------------------------------------------
-- Esta é a consulta que responde **de qual contrato veio este trecho**. Ela
-- parece trivial e é o coração do laboratório: sem ela, o RAG do Passo 4
-- entrega um parágrafo sem procedência, e um parágrafo de contrato sem
-- procedência não serve para decidir nada.
--
--   3b-1  A junção e a condição dela. Junção sem condição não é erro de
--         sintaxe: o PostgreSQL aceita, executa, e devolve o produto
--         cartesiano. Com 4 contratos e algumas dezenas de trechos, isso são
--         centenas de linhas, todas plausíveis e quase todas erradas. É o tipo
--         de defeito que passa despercebido até alguém conferir a fonte.
--
--   3b-2  A expressão de ordenação: o tamanho do texto, do maior para o menor.
--         A função `length()` faz o cálculo, e ela pode aparecer tanto na lista
--         de colunas quanto no ORDER BY.
--
-- consulta: origem_do_trecho
SELECT t.id,
       t.ordem,
       length(t.texto) AS tamanho,
       c.cliente,
       c.titulo
FROM conhecimento.trechos AS t
____ conhecimento.contratos AS c ____
ORDER BY ____ DESC
LIMIT 5;


-- ---------------------------------------------------------------------
-- Duas consultas de leitura, já prontas, que valem rodar antes de seguir.
-- Elas não são verificadas: são para você ver o acervo com os próprios olhos.
-- ---------------------------------------------------------------------

-- Tamanho do acervo, em números.
SELECT COUNT(*) AS trechos,
       MIN(length(texto)) AS menor,
       ROUND(AVG(length(texto))) AS medio,
       MAX(length(texto)) AS maior
FROM conhecimento.trechos;


-- A busca por palavra-chave, a que você já sabia fazer. Guarde este resultado:
-- no Passo 4 você vai comparar com o da busca por significado.
--
-- Repare no que ela exige: a palavra que você digitou precisa estar escrita,
-- daquele jeito, no texto. Quem procurar por "mercadoria estragada" não
-- encontra a cláusula que fala em "avaria não aparente", ainda que seja
-- exatamente a cláusula certa.
SELECT c.titulo, t.ordem, left(t.texto, 90) AS inicio
FROM conhecimento.trechos AS t
JOIN conhecimento.contratos AS c ON c.id = t.contrato_id
WHERE t.texto ILIKE '%avaria%'
ORDER BY c.titulo, t.ordem;
