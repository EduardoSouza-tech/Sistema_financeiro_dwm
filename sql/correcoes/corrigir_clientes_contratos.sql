-- ============================================================================
-- CORREÇÃO: Trocar clientes dos contratos 31 e 32
-- ============================================================================

-- VER SITUAÇÃO ANTES
SELECT 
    c.id,
    c.numero,
    c.cliente_id,
    cl.nome as cliente_nome
FROM contratos c
LEFT JOIN clientes cl ON cl.id = c.cliente_id
WHERE c.id IN (31, 32)
ORDER BY c.id;

-- CORREÇÃO: Trocar os clientes
UPDATE contratos SET cliente_id = 44 WHERE id = 31;  -- CONT-2026-0004 → VILA GLOW
UPDATE contratos SET cliente_id = 64 WHERE id = 32;  -- CONT-2026-0005 → CAVALLERI

-- VER RESULTADO DEPOIS
SELECT 
    c.id,
    c.numero,
    c.cliente_id,
    cl.nome as cliente_nome
FROM contratos c
LEFT JOIN clientes cl ON cl.id = c.cliente_id
WHERE c.id IN (31, 32)
ORDER BY c.id;

-- VERIFICAR SESSÕES AGORA COMBINAM
SELECT 
    'Contrato' as tipo,
    c.id,
    c.numero,
    c.cliente_id,
    cl.nome as cliente_nome
FROM contratos c
LEFT JOIN clientes cl ON cl.id = c.cliente_id
WHERE c.id IN (31, 32)

UNION ALL

SELECT 
    'Sessão' as tipo,
    s.id,
    CAST(s.contrato_id AS VARCHAR) as contrato,
    s.cliente_id,
    cl.nome as cliente_nome
FROM sessoes s
LEFT JOIN clientes cl ON cl.id = s.cliente_id
WHERE s.contrato_id IN (31, 32)
ORDER BY tipo DESC, id;
