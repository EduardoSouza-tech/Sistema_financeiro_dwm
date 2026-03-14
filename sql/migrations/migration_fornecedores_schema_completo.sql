-- ================================================================
-- MIGRATION: Schema Completo para Fornecedores
-- ================================================================
-- Adiciona colunas faltantes na tabela fornecedores para suportar:
-- - Razão Social e Nome Fantasia
-- - CNPJ e Documento separados
-- - IE e IM (Inscrições)
-- - Endereço estruturado (CEP, logradouro, numero, complemento, bairro, cidade, estado)
-- - Multi-tenancy (empresa_id, proprietario_id)
-- ================================================================

BEGIN;

-- 1. Adicionar colunas de identificação
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS razao_social VARCHAR(255);
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS nome_fantasia VARCHAR(255);
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS cnpj VARCHAR(18);
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS documento VARCHAR(18);
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS ie VARCHAR(20);
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS im VARCHAR(20);

-- 2. Adicionar colunas de endereço estruturado
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS cep VARCHAR(10);
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS rua VARCHAR(255);
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS logradouro VARCHAR(255);
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS numero VARCHAR(20);
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS complemento VARCHAR(100);
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS bairro VARCHAR(100);
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS cidade VARCHAR(100);
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS estado VARCHAR(2);

-- 3. Adicionar colunas de multi-tenancy
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS empresa_id INTEGER;
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS proprietario_id INTEGER;

-- 4. Adicionar contato adicional
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS contato VARCHAR(255);

-- 5. Migrar dados existentes
-- Copiar nome para razao_social se estiver vazio
UPDATE fornecedores 
SET razao_social = nome 
WHERE razao_social IS NULL AND nome IS NOT NULL;

-- Copiar cpf_cnpj para cnpj e documento se estiverem vazios
UPDATE fornecedores 
SET cnpj = cpf_cnpj,
    documento = cpf_cnpj
WHERE cpf_cnpj IS NOT NULL 
  AND (cnpj IS NULL OR documento IS NULL);

-- 6. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_fornecedores_empresa_id ON fornecedores(empresa_id);
CREATE INDEX IF NOT EXISTS idx_fornecedores_proprietario_id ON fornecedores(proprietario_id);
CREATE INDEX IF NOT EXISTS idx_fornecedores_razao_social ON fornecedores(razao_social);
CREATE INDEX IF NOT EXISTS idx_fornecedores_cnpj ON fornecedores(cnpj);
CREATE INDEX IF NOT EXISTS idx_fornecedores_cidade ON fornecedores(cidade);

-- 7. Adicionar constraints (somente se as tabelas relacionadas existirem)
DO $$ 
BEGIN
    -- Foreign key para empresa_id (se tabela empresas existir)
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'empresas') THEN
        ALTER TABLE fornecedores 
        ADD CONSTRAINT fk_fornecedores_empresa 
        FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE;
    END IF;

    -- Foreign key para proprietario_id (se tabela usuarios existir)
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'usuarios') THEN
        ALTER TABLE fornecedores 
        ADD CONSTRAINT fk_fornecedores_proprietario 
        FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE SET NULL;
    END IF;
EXCEPTION
    WHEN duplicate_object THEN NULL;  -- Constraint já existe, ignorar
END $$;

-- 8. Adicionar comentários nas colunas
COMMENT ON COLUMN fornecedores.razao_social IS 'Razão social do fornecedor (nome empresarial oficial)';
COMMENT ON COLUMN fornecedores.nome_fantasia IS 'Nome fantasia do fornecedor';
COMMENT ON COLUMN fornecedores.cnpj IS 'CNPJ do fornecedor';
COMMENT ON COLUMN fornecedores.documento IS 'Documento principal (CPF ou CNPJ)';
COMMENT ON COLUMN fornecedores.ie IS 'Inscrição Estadual';
COMMENT ON COLUMN fornecedores.im IS 'Inscrição Municipal';
COMMENT ON COLUMN fornecedores.cep IS 'CEP do endereço';
COMMENT ON COLUMN fornecedores.rua IS 'Rua/Logradouro (campo alternativo)';
COMMENT ON COLUMN fornecedores.logradouro IS 'Logradouro completo';
COMMENT ON COLUMN fornecedores.numero IS 'Número do endereço';
COMMENT ON COLUMN fornecedores.complemento IS 'Complemento do endereço';
COMMENT ON COLUMN fornecedores.bairro IS 'Bairro';
COMMENT ON COLUMN fornecedores.cidade IS 'Cidade';
COMMENT ON COLUMN fornecedores.estado IS 'UF (estado)';
COMMENT ON COLUMN fornecedores.empresa_id IS 'ID da empresa proprietária (multi-tenancy)';
COMMENT ON COLUMN fornecedores.proprietario_id IS 'ID do usuário proprietário';
COMMENT ON COLUMN fornecedores.contato IS 'Nome da pessoa de contato';

COMMIT;

-- ================================================================
-- Verificação pós-migration
-- ================================================================
SELECT 
    'fornecedores' as tabela,
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'fornecedores'
ORDER BY ordinal_position;
