-- ===============================================
-- MIGRAÇÃO CRÍTICA: Adicionar empresa_id à tabela lancamentos
-- CORREÇÃO DE SEGURANÇA: Bug de vazamento de dados entre empresas
-- ===============================================

-- 1. Adicionar coluna empresa_id se não existir
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='lancamentos' AND column_name='empresa_id'
    ) THEN
        ALTER TABLE lancamentos ADD COLUMN empresa_id INTEGER;
        RAISE NOTICE '✅ Coluna empresa_id adicionada à tabela lancamentos';
    ELSE
        RAISE NOTICE 'ℹ️  Coluna empresa_id já existe na tabela lancamentos';
    END IF;
END $$;

-- 2. Verificar se existe apenas uma empresa e popular automaticamente
DO $$ 
DECLARE
    empresa_count INTEGER;
    primeira_empresa_id INTEGER;
    lancamentos_sem_empresa INTEGER;
BEGIN
    -- Contar empresas
    SELECT COUNT(*) INTO empresa_count FROM empresas;
    
    -- Contar lançamentos sem empresa
    SELECT COUNT(*) INTO lancamentos_sem_empresa 
    FROM lancamentos 
    WHERE empresa_id IS NULL;
    
    RAISE NOTICE 'Total de empresas: %', empresa_count;
    RAISE NOTICE 'Lançamentos sem empresa_id: %', lancamentos_sem_empresa;
    
    -- Se há apenas uma empresa, atribuir todos os lançamentos a ela
    IF empresa_count = 1 AND lancamentos_sem_empresa > 0 THEN
        SELECT id INTO primeira_empresa_id FROM empresas LIMIT 1;
        
        UPDATE lancamentos 
        SET empresa_id = primeira_empresa_id 
        WHERE empresa_id IS NULL;
        
        RAISE NOTICE '✅ Atribuídos % lançamentos à empresa ID %', lancamentos_sem_empresa, primeira_empresa_id;
    ELSIF empresa_count > 1 AND lancamentos_sem_empresa > 0 THEN
        RAISE WARNING '⚠️  AÇÃO MANUAL NECESSÁRIA: Existem % empresas e % lançamentos sem empresa_id', empresa_count, lancamentos_sem_empresa;
        RAISE WARNING '⚠️  Execute manualmente: UPDATE lancamentos SET empresa_id = X WHERE <condição>';
    END IF;
END $$;

-- 3. Criar índice para performance
CREATE INDEX IF NOT EXISTS idx_lancamentos_empresa_id ON lancamentos(empresa_id);
RAISE NOTICE '✅ Índice criado: idx_lancamentos_empresa_id';

-- 4. Adicionar foreign key (comentado por segurança - ative após popular dados)
-- ALTER TABLE lancamentos 
-- ADD CONSTRAINT fk_lancamentos_empresa 
-- FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE;

-- 5. (Opcional) Tornar empresa_id NOT NULL após popular todos os dados
-- ALTER TABLE lancamentos ALTER COLUMN empresa_id SET NOT NULL;

-- ===============================================
-- INSTRUÇÕES PÓS-MIGRAÇÃO:
-- ===============================================
-- 1. Se você tem MÚLTIPLAS empresas, atribua manualmente:
--    UPDATE lancamentos SET empresa_id = 1 WHERE <condição para empresa 1>;
--    UPDATE lancamentos SET empresa_id = 2 WHERE <condição para empresa 2>;
--
-- 2. Após popular TODOS os dados, torne NOT NULL:
--    ALTER TABLE lancamentos ALTER COLUMN empresa_id SET NOT NULL;
--
-- 3. Adicione a foreign key:
--    ALTER TABLE lancamentos 
--    ADD CONSTRAINT fk_lancamentos_empresa 
--    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE;
-- ===============================================

