-- ============================================================================
-- MIGRATION: Corrigir tipo da coluna subcategorias
-- Data: 26/01/2026
-- Descrição: Altera subcategorias de TEXT para VARCHAR(255)
-- ============================================================================

-- Verificar tipo atual
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'categorias'
AND column_name = 'subcategorias';

-- Alterar tipo da coluna
ALTER TABLE categorias
ALTER COLUMN subcategorias TYPE VARCHAR(255)
USING subcategorias::VARCHAR(255);

-- Verificar resultado
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'categorias'
AND column_name = 'subcategorias';

-- Resultado esperado: character varying | 255 | NULL
