-- ================================================
-- FIX: Remover constraint UNIQUE do nome de categorias
-- E adicionar constraint composta (nome + empresa_id)
-- ================================================

-- 1. Remover constraint antiga (nome único)
ALTER TABLE categorias 
DROP CONSTRAINT IF EXISTS categorias_nome_key;

-- 2. Adicionar constraint composta (nome + empresa_id devem ser únicos juntos)
-- Isso permite que empresas diferentes tenham categorias com mesmo nome
ALTER TABLE categorias 
ADD CONSTRAINT categorias_nome_empresa_unique 
UNIQUE (nome, empresa_id);

-- 3. Verificar constraints
SELECT 
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'categorias'::regclass
ORDER BY conname;
