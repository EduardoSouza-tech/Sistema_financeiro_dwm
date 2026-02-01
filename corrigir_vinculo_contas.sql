-- ============================================================================
-- CORREÇÃO DE VÍNCULO: CONTAS BANCÁRIAS ↔ EMPRESAS
-- ============================================================================
-- Este script atualiza o campo proprietario_id das contas bancárias
-- para vinculá-las corretamente à empresa COOPSERVICOS (ID 20)
-- ============================================================================

-- 1. Verificar contas atuais
SELECT 
    '📋 CONTAS ANTES DA CORREÇÃO:' as info,
    id, 
    nome, 
    banco, 
    proprietario_id 
FROM contas_bancarias 
ORDER BY nome;

-- 2. Verificar empresas disponíveis
SELECT 
    '🏢 EMPRESAS DISPONÍVEIS:' as info,
    id, 
    razao_social 
FROM empresas 
ORDER BY id;

-- 3. Atualizar todas as contas para a empresa COOPSERVICOS (ID 20)
UPDATE contas_bancarias 
SET proprietario_id = 20 
WHERE proprietario_id IS NULL OR proprietario_id != 20;

-- 4. Verificar resultado
SELECT 
    '✅ CONTAS APÓS CORREÇÃO:' as info,
    c.id,
    c.nome, 
    c.banco, 
    c.proprietario_id,
    e.razao_social as empresa
FROM contas_bancarias c
LEFT JOIN empresas e ON c.proprietario_id = e.id
ORDER BY c.nome;

-- 5. Confirmar
SELECT 
    '📊 RESUMO:' as info,
    COUNT(*) as total_contas,
    COUNT(DISTINCT proprietario_id) as empresas_com_contas
FROM contas_bancarias;
