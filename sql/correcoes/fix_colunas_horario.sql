-- ============================================================================
-- FIX: Adicionar colunas hora_inicio e hora_fim na tabela evento_funcionarios
-- ============================================================================

-- Adicionar coluna hora_inicio
ALTER TABLE evento_funcionarios 
ADD COLUMN IF NOT EXISTS hora_inicio TIME;

-- Adicionar coluna hora_fim
ALTER TABLE evento_funcionarios 
ADD COLUMN IF NOT EXISTS hora_fim TIME;

-- Verificar se as colunas foram criadas
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'evento_funcionarios' 
AND column_name IN ('hora_inicio', 'hora_fim')
ORDER BY column_name;
