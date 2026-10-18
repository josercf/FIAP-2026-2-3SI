-- Resgate do Passo 3: as duas consultas completas.
--
--     cp resgate/03-consultas.sql sql/03-consultas.sql
--
-- O LEFT JOIN do primeiro bloco é deliberado: a pergunta é "quantos trechos
-- cada contrato gerou", e um contrato ainda sem trechos é uma resposta
-- legítima com o valor zero. Com INNER JOIN essa linha desaparece do
-- relatório, e some sem erro nenhum, que é o pior jeito de sumir.

-- consulta: trechos_por_contrato
SELECT c.cliente,
       c.titulo,
       COUNT(t.id) AS trechos
FROM conhecimento.contratos AS c
LEFT JOIN conhecimento.trechos AS t ON t.contrato_id = c.id
GROUP BY c.id, c.cliente, c.titulo
ORDER BY trechos DESC
LIMIT 3;

-- consulta: origem_do_trecho
SELECT t.id,
       t.ordem,
       length(t.texto) AS tamanho,
       c.cliente,
       c.titulo
FROM conhecimento.trechos AS t
JOIN conhecimento.contratos AS c ON c.id = t.contrato_id
ORDER BY length(t.texto) DESC
LIMIT 5;

SELECT COUNT(*) AS trechos,
       MIN(length(texto)) AS menor,
       ROUND(AVG(length(texto))) AS medio,
       MAX(length(texto)) AS maior
FROM conhecimento.trechos;

SELECT c.titulo, t.ordem, left(t.texto, 90) AS inicio
FROM conhecimento.trechos AS t
JOIN conhecimento.contratos AS c ON c.id = t.contrato_id
WHERE t.texto ILIKE '%avaria%'
ORDER BY c.titulo, t.ordem;
