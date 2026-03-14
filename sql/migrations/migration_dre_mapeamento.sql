-- ============================================================================
-- MIGRATION: DRE - Mapeamento de Subcategorias para Plano de Contas
-- ============================================================================
-- Descrição: Cria tabela para vincular subcategorias ao plano de contas do DRE
-- Data: 19/02/2026
-- Autor: Sistema
-- ============================================================================

-- 1. CRIAR TABELA DE MAPEAMENTO
-- ============================================================================

CREATE TABLE IF NOT EXISTS dre_mapeamento_subcategoria (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    subcategoria_id INTEGER NOT NULL,
    plano_contas_id INTEGER NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Foreign Keys
    CONSTRAINT fk_dre_map_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    CONSTRAINT fk_dre_map_subcategoria FOREIGN KEY (subcategoria_id) REFERENCES subcategorias(id) ON DELETE CASCADE,
    CONSTRAINT fk_dre_map_plano_contas FOREIGN KEY (plano_contas_id) REFERENCES plano_contas(id) ON DELETE CASCADE,
    
    -- Constraint: Impedir duplicação de subcategoria para a mesma empresa
    CONSTRAINT uk_dre_map_empresa_sub UNIQUE (empresa_id, subcategoria_id)
);

-- 2. CRIAR ÍNDICES PARA PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_dre_map_empresa ON dre_mapeamento_subcategoria(empresa_id);
CREATE INDEX IF NOT EXISTS idx_dre_map_subcategoria ON dre_mapeamento_subcategoria(subcategoria_id);
CREATE INDEX IF NOT EXISTS idx_dre_map_plano_contas ON dre_mapeamento_subcategoria(plano_contas_id);
CREATE INDEX IF NOT EXISTS idx_dre_map_ativo ON dre_mapeamento_subcategoria(ativo);

-- 3. COMENTÁRIOS NA TABELA
-- ============================================================================

COMMENT ON TABLE dre_mapeamento_subcategoria IS 'Mapeamento entre subcategorias de lançamentos e contas do plano de contas do DRE';
COMMENT ON COLUMN dre_mapeamento_subcategoria.empresa_id IS 'Empresa dona do mapeamento (multi-tenant)';
COMMENT ON COLUMN dre_mapeamento_subcategoria.subcategoria_id IS 'Subcategoria de lançamento financeiro';
COMMENT ON COLUMN dre_mapeamento_subcategoria.plano_contas_id IS 'Conta do plano de contas do DRE (código 4.x, 5.x, 6.x, 7.x)';
COMMENT ON COLUMN dre_mapeamento_subcategoria.ativo IS 'Se o mapeamento está ativo';

-- 4. TRIGGER PARA ATUALIZAR updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_dre_mapeamento_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_dre_mapeamento_updated_at
BEFORE UPDATE ON dre_mapeamento_subcategoria
FOR EACH ROW
EXECUTE FUNCTION update_dre_mapeamento_updated_at();

-- 5. VERIFICAÇÃO FINAL
-- ============================================================================

DO $$
BEGIN
    -- Verificar se a tabela foi criada
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dre_mapeamento_subcategoria') THEN
        RAISE NOTICE '✅ Tabela dre_mapeamento_subcategoria criada com sucesso';
        
        -- Verificar colunas
        RAISE NOTICE '📋 Colunas:';
        FOR rec IN 
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'dre_mapeamento_subcategoria'
            ORDER BY ordinal_position
        LOOP
            RAISE NOTICE '   - % (%, nullable: %)', rec.column_name, rec.data_type, rec.is_nullable;
        END LOOP;
        
        -- Verificar índices
        RAISE NOTICE '📊 Índices criados:';
        FOR rec IN 
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'dre_mapeamento_subcategoria'
        LOOP
            RAISE NOTICE '   - %', rec.indexname;
        END LOOP;
        
        -- Verificar constraints
        RAISE NOTICE '🔒 Constraints:';
        FOR rec IN 
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'dre_mapeamento_subcategoria'
        LOOP
            RAISE NOTICE '   - % (%)', rec.constraint_name, rec.constraint_type;
        END LOOP;
        
    ELSE
        RAISE EXCEPTION '❌ Tabela dre_mapeamento_subcategoria não foi criada';
    END IF;
END $$;

-- ============================================================================
-- MIGRATION COMPLETO ✅
-- ============================================================================

RAISE NOTICE '';
RAISE NOTICE '==========================================';
RAISE NOTICE '✅ MIGRATION CONCLUÍDA COM SUCESSO!';
RAISE NOTICE '==========================================';
RAISE NOTICE 'Tabela: dre_mapeamento_subcategoria';
RAISE NOTICE 'Finalidade: Vincular subcategorias ao DRE';
RAISE NOTICE 'Multi-tenant: SIM (empresa_id)';
RAISE NOTICE '==========================================';
