-- ============================================================================
-- LIMPEZA DE DADOS CORROMPIDOS - PLANO DE CONTAS
-- Execute este SQL diretamente no Railway (aba "Data" ou via CLI)
-- ============================================================================

-- 1. Verificar linhas corrompidas
SELECT 
    id, 
    empresa_id, 
    nome_versao, 
    exercicio_fiscal,
    is_ativa,
    created_at
FROM plano_contas_versao
WHERE nome_versao = 'nome_versao'  -- Linha corrompida (valor = nome da coluna)
   OR id::text = 'id'                -- Cast para comparar se id é literal 'id'
   OR exercicio_fiscal::text = 'exercicio_fiscal'
ORDER BY id;

-- 2. Deletar linhas corrompidas
DELETE FROM plano_contas_versao
WHERE nome_versao = 'nome_versao'
   OR exercicio_fiscal::text = 'exercicio_fiscal';

-- 3. Verificar total de registros restantes
SELECT 
    empresa_id,
    COUNT(*) as total_versoes,
    COUNT(*) FILTER (WHERE is_ativa = true) as ativas
FROM plano_contas_versao
GROUP BY empresa_id
ORDER BY empresa_id;

-- 4. Listar todas as versões válidas
SELECT 
    id,
    empresa_id,
    nome_versao,
    exercicio_fiscal,
    is_ativa,
    created_at
FROM plano_contas_versao
ORDER BY empresa_id, exercicio_fiscal DESC, created_at DESC;

-- ============================================================================
-- VERIFICAÇÃO FINAL
-- ============================================================================

-- Se alguma empresa ficou sem versões, você pode aplicar o plano padrão
-- usando o botão "📦 Importar Plano Padrão" na interface

-- Ou executar via Python:
-- python aplicar_plano_railway_manual.py
