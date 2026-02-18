-- ========================================================================
-- SCRIPT DE CORREÇÃO - SUBCATEGORIAS E EVENTO_FORNECEDORES
-- ========================================================================
-- Execute este script no Railway Query Editor para corrigir os erros 500

-- ========================================================================
-- 1. ADICIONAR COLUNA 'ativa' NA TABELA SUBCATEGORIAS (se não existir)
-- ========================================================================

-- Verificar se a coluna existe antes de adicionar
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'subcategorias' 
        AND column_name = 'ativa'
    ) THEN
        ALTER TABLE subcategorias ADD COLUMN ativa BOOLEAN DEFAULT TRUE;
        
        -- Atualizar todos os registros existentes para ativa=TRUE
        UPDATE subcategorias SET ativa = TRUE WHERE ativa IS NULL;
        
        RAISE NOTICE '✅ Coluna ativa adicionada à tabela subcategorias';
    ELSE
        RAISE NOTICE '✅ Coluna ativa já existe na tabela subcategorias';
    END IF;
END $$;

-- ========================================================================
-- 2. CRIAR TABELA EVENTO_FORNECEDORES (se não existir)
-- ========================================================================

CREATE TABLE IF NOT EXISTS evento_fornecedores (
    id SERIAL PRIMARY KEY,
    evento_id INTEGER NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    fornecedor_id INTEGER NOT NULL REFERENCES fornecedores(id) ON DELETE CASCADE,
    categoria_id INTEGER REFERENCES categorias(id),
    subcategoria_id INTEGER REFERENCES subcategorias(id),
    valor NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    observacao TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES usuarios(id),
    
    -- Evitar duplicatas: mesmo fornecedor não pode ser adicionado duas vezes ao mesmo evento
    UNIQUE(evento_id, fornecedor_id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_evento_fornecedores_evento ON evento_fornecedores(evento_id);
CREATE INDEX IF NOT EXISTS idx_evento_fornecedores_fornecedor ON evento_fornecedores(fornecedor_id);

-- Comentários
COMMENT ON TABLE evento_fornecedores IS 'Relaciona fornecedores com eventos, incluindo custos e categorização';
COMMENT ON COLUMN evento_fornecedores.evento_id IS 'ID do evento';
COMMENT ON COLUMN evento_fornecedores.fornecedor_id IS 'ID do fornecedor contratado';
COMMENT ON COLUMN evento_fornecedores.categoria_id IS 'Categoria do custo (ex: Alimentação, Transporte)';
COMMENT ON COLUMN evento_fornecedores.subcategoria_id IS 'Subcategoria do custo';
COMMENT ON COLUMN evento_fornecedores.valor IS 'Valor cobrado pelo fornecedor';
COMMENT ON COLUMN evento_fornecedores.observacao IS 'Observações adicionais sobre o serviço';

-- ========================================================================
-- 3. VERIFICAÇÃO
-- ========================================================================

-- Verificar se as alterações foram aplicadas
DO $$ 
BEGIN
    -- Verificar coluna ativa
    IF EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'subcategorias' 
        AND column_name = 'ativa'
    ) THEN
        RAISE NOTICE '✅ Coluna subcategorias.ativa - OK';
    ELSE
        RAISE NOTICE '❌ Coluna subcategorias.ativa - NÃO EXISTE';
    END IF;
    
    -- Verificar tabela evento_fornecedores
    IF EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'evento_fornecedores'
    ) THEN
        RAISE NOTICE '✅ Tabela evento_fornecedores - OK';
    ELSE
        RAISE NOTICE '❌ Tabela evento_fornecedores - NÃO EXISTE';
    END IF;
END $$;

-- Listar colunas da tabela subcategorias
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns
WHERE table_name = 'subcategorias'
ORDER BY ordinal_position;

-- Contar registros
SELECT 
    'subcategorias' as tabela,
    COUNT(*) as total_registros
FROM subcategorias
UNION ALL
SELECT 
    'evento_fornecedores' as tabela,
    COUNT(*) as total_registros
FROM evento_fornecedores;

-- ========================================================================
-- FIM DO SCRIPT
-- ========================================================================
