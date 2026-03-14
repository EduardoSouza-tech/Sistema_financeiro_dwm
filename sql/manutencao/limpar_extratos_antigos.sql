-- ============================================================================
-- LIMPEZA DE EXTRATOS OFX DA EMPRESA ERRADA
-- ============================================================================
-- Este script remove transações de extrato que foram salvas na empresa errada
-- Para executar após fazer novo upload com a empresa correta
-- ============================================================================

-- 1. Ver extratos atuais e suas empresas
SELECT 
    '📋 EXTRATOS ATUAIS:' as info,
    empresa_id,
    conta_bancaria,
    COUNT(*) as total_transacoes,
    MIN(data) as data_inicio,
    MAX(data) as data_fim
FROM extratos
GROUP BY empresa_id, conta_bancaria
ORDER BY empresa_id, conta_bancaria;

-- 2. DELETAR extratos da empresa 18 (se existirem)
-- Descomente a linha abaixo para executar a limpeza:
-- DELETE FROM extratos WHERE empresa_id = 18;

-- 3. DELETAR extratos da empresa 1 (se existirem)
-- Descomente a linha abaixo para executar a limpeza:
-- DELETE FROM extratos WHERE empresa_id = 1;

-- 4. MANTER apenas extratos da empresa 20 (COOPSERVICOS)
-- Esta é uma opção mais segura - remove tudo EXCETO empresa 20:
-- DELETE FROM extratos WHERE empresa_id != 20;

-- 5. Verificar resultado após limpeza
SELECT 
    '✅ EXTRATOS APÓS LIMPEZA:' as info,
    empresa_id,
    conta_bancaria,
    COUNT(*) as total_transacoes
FROM extratos
GROUP BY empresa_id, conta_bancaria
ORDER BY empresa_id, conta_bancaria;
