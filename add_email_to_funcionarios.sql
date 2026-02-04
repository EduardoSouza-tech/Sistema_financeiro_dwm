-- Adicionar campo email à tabela funcionarios
ALTER TABLE funcionarios 
ADD COLUMN IF NOT EXISTS email VARCHAR(255);

-- Comentário da coluna
COMMENT ON COLUMN funcionarios.email IS 'Email do funcionário/cooperado';

-- Adicionar colunas de horário à tabela evento_funcionarios
ALTER TABLE evento_funcionarios 
ADD COLUMN IF NOT EXISTS hora_inicio TIME,
ADD COLUMN IF NOT EXISTS hora_fim TIME;

-- Comentários
COMMENT ON COLUMN evento_funcionarios.hora_inicio IS 'Horário de início do funcionário no evento';
COMMENT ON COLUMN evento_funcionarios.hora_fim IS 'Horário de término do funcionário no evento';
