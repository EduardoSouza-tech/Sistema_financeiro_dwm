-- ================================================
-- MIGRATION: Adicionar coluna setor_id em evento_funcionarios
-- Data: 2026-02-01
-- Descrição: Permite associar funcionários a setores ao alocá-los em eventos
-- ================================================

-- 1. Adicionar coluna setor_id (nullable para não quebrar dados existentes)
ALTER TABLE evento_funcionarios 
ADD COLUMN IF NOT EXISTS setor_id INTEGER;

-- 2. Criar foreign key para setores
ALTER TABLE evento_funcionarios 
ADD CONSTRAINT fk_evento_funcionarios_setor 
FOREIGN KEY (setor_id) REFERENCES setores(id) 
ON DELETE SET NULL;

-- 3. Criar índice para melhorar performance
CREATE INDEX IF NOT EXISTS idx_evento_funcionarios_setor 
ON evento_funcionarios(setor_id);

-- 4. Adicionar comentário na coluna
COMMENT ON COLUMN evento_funcionarios.setor_id IS 'Setor ao qual o funcionário está alocado no evento (FK para setores)';

-- ================================================
-- FIM DA MIGRATION
-- ================================================
