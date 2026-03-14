-- =====================================================
-- DIAGNÓSTICO DE SALDOS POR CONTA BANCÁRIA
-- =====================================================
-- Execute esta query no seu banco de dados PostgreSQL
-- =====================================================

-- 1. Listar todas as contas e seus saldos
SELECT 
    cb.id,
    cb.nome AS conta,
    cb.banco,
    cb.saldo_inicial,
    cb.ativa,
    -- Verificar se tem extrato
    (SELECT COUNT(*) 
     FROM transacoes_extrato te 
     WHERE te.empresa_id = 20 AND te.conta_bancaria = cb.nome
    ) AS total_transacoes_extrato,
    -- Saldo do extrato (última transação)
    (SELECT saldo 
     FROM transacoes_extrato te 
     WHERE te.empresa_id = 20 AND te.conta_bancaria = cb.nome 
     ORDER BY te.data DESC, te.id DESC 
     LIMIT 1
    ) AS saldo_extrato,
    -- Receitas pagas
    (SELECT COALESCE(SUM(valor), 0)
     FROM lancamentos l
     WHERE l.empresa_id = 20 
     AND l.conta_bancaria = cb.nome
     AND l.tipo = 'receita'
     AND l.status = 'pago'
    ) AS receitas_pagas,
    -- Despesas pagas
    (SELECT COALESCE(SUM(valor), 0)
     FROM lancamentos l
     WHERE l.empresa_id = 20 
     AND l.conta_bancaria = cb.nome
     AND l.tipo = 'despesa'
     AND l.status = 'pago'
    ) AS despesas_pagas,
    -- Saldo calculado (saldo_inicial + receitas - despesas)
    cb.saldo_inicial + 
    (SELECT COALESCE(SUM(valor), 0)
     FROM lancamentos l
     WHERE l.empresa_id = 20 
     AND l.conta_bancaria = cb.nome
     AND l.tipo = 'receita'
     AND l.status = 'pago'
    ) - 
    (SELECT COALESCE(SUM(valor), 0)
     FROM lancamentos l
     WHERE l.empresa_id = 20 
     AND l.conta_bancaria = cb.nome
     AND l.tipo = 'despesa'
     AND l.status = 'pago'
    ) AS saldo_calculado,
    -- Saldo que o sistema usa (prioriza extrato)
    COALESCE(
        (SELECT saldo 
         FROM transacoes_extrato te 
         WHERE te.empresa_id = 20 AND te.conta_bancaria = cb.nome 
         ORDER BY te.data DESC, te.id DESC 
         LIMIT 1
        ),
        cb.saldo_inicial + 
        (SELECT COALESCE(SUM(valor), 0)
         FROM lancamentos l
         WHERE l.empresa_id = 20 
         AND l.conta_bancaria = cb.nome
         AND l.tipo = 'receita'
         AND l.status = 'pago'
        ) - 
        (SELECT COALESCE(SUM(valor), 0)
         FROM lancamentos l
         WHERE l.empresa_id = 20 
         AND l.conta_bancaria = cb.nome
         AND l.tipo = 'despesa'
         AND l.status = 'pago'
        )
    ) AS saldo_usado_sistema
FROM contas_bancarias cb
WHERE cb.empresa_id = 20
ORDER BY cb.nome;

-- 2. Soma total (igual ao "Saldo Total dos Bancos")
SELECT 
    SUM(
        COALESCE(
            (SELECT saldo 
             FROM transacoes_extrato te 
             WHERE te.empresa_id = 20 AND te.conta_bancaria = cb.nome 
             ORDER BY te.data DESC, te.id DESC 
             LIMIT 1
            ),
            cb.saldo_inicial + 
            (SELECT COALESCE(SUM(valor), 0)
             FROM lancamentos l
             WHERE l.empresa_id = 20 
             AND l.conta_bancaria = cb.nome
             AND l.tipo = 'receita'
             AND l.status = 'pago'
            ) - 
            (SELECT COALESCE(SUM(valor), 0)
             FROM lancamentos l
             WHERE l.empresa_id = 20 
             AND l.conta_bancaria = cb.nome
             AND l.tipo = 'despesa'
             AND l.status = 'pago'
            )
        )
    ) AS saldo_total_todos_bancos
FROM contas_bancarias cb
WHERE cb.empresa_id = 20;

-- 3. Resumo simplificado
SELECT 
    COUNT(*) AS total_contas,
    COUNT(CASE WHEN (
        SELECT COUNT(*) 
        FROM transacoes_extrato te 
        WHERE te.empresa_id = 20 AND te.conta_bancaria = cb.nome
    ) > 0 THEN 1 END) AS contas_com_extrato,
    COUNT(CASE WHEN (
        SELECT COUNT(*) 
        FROM transacoes_extrato te 
        WHERE te.empresa_id = 20 AND te.conta_bancaria = cb.nome
    ) = 0 THEN 1 END) AS contas_sem_extrato
FROM contas_bancarias cb
WHERE cb.empresa_id = 20;
