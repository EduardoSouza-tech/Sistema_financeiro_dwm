-- Script SQL para recalcular margem de todos os eventos
-- Execute este script no PostgreSQL do Railway

-- Mostrar eventos com margem incorreta
SELECT 
    id,
    nome_evento,
    valor_liquido_nf,
    custo_evento,
    margem AS margem_atual,
    (COALESCE(valor_liquido_nf, 0) - COALESCE(custo_evento, 0)) AS margem_correta,
    (margem - (COALESCE(valor_liquido_nf, 0) - COALESCE(custo_evento, 0))) AS diferenca
FROM eventos
WHERE ABS(COALESCE(margem, 0) - (COALESCE(valor_liquido_nf, 0) - COALESCE(custo_evento, 0))) > 0.01
ORDER BY id;

-- Atualizar todas as margens
UPDATE eventos
SET margem = (COALESCE(valor_liquido_nf, 0) - COALESCE(custo_evento, 0))
WHERE ABS(COALESCE(margem, 0) - (COALESCE(valor_liquido_nf, 0) - COALESCE(custo_evento, 0))) > 0.01;

-- Verificar resultado
SELECT 
    id,
    nome_evento,
    valor_liquido_nf,
    custo_evento,
    margem,
    (COALESCE(valor_liquido_nf, 0) - COALESCE(custo_evento, 0)) AS margem_calculada
FROM eventos
ORDER BY id;
