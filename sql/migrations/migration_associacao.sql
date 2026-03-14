-- ================================================================================
-- MIGRATION: Adicionar coluna 'associacao' na tabela lancamentos
-- Data: 2026-02-15
-- Descrição: Sincroniza campo associacao com numero_documento
-- ================================================================================

-- Verificar se coluna existe e criar se necessário
DO $$
BEGIN
    -- Verificar se a coluna já existe
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'lancamentos' 
        AND column_name = 'associacao'
    ) THEN
        -- Adicionar coluna associacao
        ALTER TABLE lancamentos 
        ADD COLUMN associacao TEXT DEFAULT '';
        
        RAISE NOTICE '✅ Coluna associacao adicionada';
        
        -- Copiar valores de numero_documento para associacao (sincronização inicial)
        UPDATE lancamentos 
        SET associacao = COALESCE(numero_documento, '') 
        WHERE associacao = '' OR associacao IS NULL;
        
        RAISE NOTICE '✅ Valores sincronizados de numero_documento';
        
        -- Criar índice parcial para melhor performance
        CREATE INDEX IF NOT EXISTS idx_lancamentos_associacao 
        ON lancamentos(associacao) 
        WHERE associacao IS NOT NULL AND associacao != '';
        
        RAISE NOTICE '✅ Índice criado';
        
    ELSE
        RAISE NOTICE 'ℹ️  Coluna associacao já existe';
    END IF;
END
$$;

-- Verificação final
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'lancamentos' 
AND column_name IN ('associacao', 'numero_documento')
ORDER BY column_name;

-- Estatísticas
SELECT 
    COUNT(*) as total_lancamentos,
    COUNT(CASE WHEN associacao IS NOT NULL AND associacao != '' THEN 1 END) as com_associacao,
    COUNT(CASE WHEN numero_documento IS NOT NULL AND numero_documento != '' THEN 1 END) as com_numero_documento
FROM lancamentos;
