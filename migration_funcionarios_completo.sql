-- Migration: Adicionar campos completos para funcionários (baseado em coop.xlsx)
-- Data: 2026-02-04

-- Remover constraint NOT NULL de tipo_chave_pix
ALTER TABLE funcionarios 
ALTER COLUMN tipo_chave_pix DROP NOT NULL;

-- Adicionar novos campos à tabela funcionarios (se não existirem)
ALTER TABLE funcionarios 
ADD COLUMN IF NOT EXISTS nacionalidade VARCHAR(100),
ADD COLUMN IF NOT EXISTS estado_civil VARCHAR(50),
ADD COLUMN IF NOT EXISTS data_nascimento DATE,
ADD COLUMN IF NOT EXISTS idade INTEGER,
ADD COLUMN IF NOT EXISTS profissao VARCHAR(100),
ADD COLUMN IF NOT EXISTS rua_av VARCHAR(255),
ADD COLUMN IF NOT EXISTS numero_residencia VARCHAR(20),
ADD COLUMN IF NOT EXISTS complemento VARCHAR(100),
ADD COLUMN IF NOT EXISTS bairro VARCHAR(100),
ADD COLUMN IF NOT EXISTS cidade VARCHAR(100),
ADD COLUMN IF NOT EXISTS estado VARCHAR(2),
ADD COLUMN IF NOT EXISTS cep VARCHAR(9),
ADD COLUMN IF NOT EXISTS celular VARCHAR(20),
ADD COLUMN IF NOT EXISTS chave_pix VARCHAR(255),
ADD COLUMN IF NOT EXISTS pis_pasep VARCHAR(20);

-- Criar índices para busca rápida
CREATE INDEX IF NOT EXISTS idx_funcionarios_cpf ON funcionarios(cpf);
CREATE INDEX IF NOT EXISTS idx_funcionarios_nome ON funcionarios(nome);
CREATE INDEX IF NOT EXISTS idx_funcionarios_ativo ON funcionarios(ativo);
CREATE INDEX IF NOT EXISTS idx_funcionarios_pis ON funcionarios(pis_pasep);

-- Adicionar constraint UNIQUE no CPF (ignorar se já existir)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'funcionarios_cpf_key'
    ) THEN
        ALTER TABLE funcionarios ADD CONSTRAINT funcionarios_cpf_key UNIQUE (cpf);
    END IF;
END $$;

-- Adicionar comentários nas colunas
COMMENT ON COLUMN funcionarios.nacionalidade IS 'Nacionalidade do funcionário';
COMMENT ON COLUMN funcionarios.estado_civil IS 'Estado civil: Solteiro, Casado, Divorciado, Viúvo, etc';
COMMENT ON COLUMN funcionarios.data_nascimento IS 'Data de nascimento';
COMMENT ON COLUMN funcionarios.idade IS 'Idade calculada automaticamente';
COMMENT ON COLUMN funcionarios.profissao IS 'Profissão/Cargo do funcionário';
COMMENT ON COLUMN funcionarios.rua_av IS 'Endereço: Rua ou Avenida';
COMMENT ON COLUMN funcionarios.numero_residencia IS 'Número da residência';
COMMENT ON COLUMN funcionarios.complemento IS 'Complemento do endereço';
COMMENT ON COLUMN funcionarios.bairro IS 'Bairro';
COMMENT ON COLUMN funcionarios.cidade IS 'Cidade';
COMMENT ON COLUMN funcionarios.estado IS 'Estado (sigla UF)';
COMMENT ON COLUMN funcionarios.cep IS 'CEP';
COMMENT ON COLUMN funcionarios.celular IS 'Número de celular';
COMMENT ON COLUMN funcionarios.chave_pix IS 'Chave PIX para pagamentos';
COMMENT ON COLUMN funcionarios.pis_pasep IS 'PIS/PASEP';

-- Criar função para calcular idade automaticamente
CREATE OR REPLACE FUNCTION calcular_idade()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.data_nascimento IS NOT NULL THEN
        NEW.idade := EXTRACT(YEAR FROM AGE(CURRENT_DATE, NEW.data_nascimento));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Criar trigger para atualizar idade automaticamente
DROP TRIGGER IF EXISTS trigger_calcular_idade ON funcionarios;
CREATE TRIGGER trigger_calcular_idade
BEFORE INSERT OR UPDATE OF data_nascimento ON funcionarios
FOR EACH ROW
EXECUTE FUNCTION calcular_idade();

-- Verificar estrutura final
SELECT 
    column_name, 
    data_type, 
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'funcionarios'
ORDER BY ordinal_position;
