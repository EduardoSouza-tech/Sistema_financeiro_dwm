-- ============================================================================
-- MIGRAÇÃO: Certificados Digitais A1 para NFS-e
-- Data: 2026-02-14
-- Descrição: Armazena certificados .pfx para consulta automática de NFS-e
-- ============================================================================

-- TABELA: Certificados Digitais A1
CREATE TABLE IF NOT EXISTS nfse_certificados (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    pfx_data BYTEA NOT NULL,                     -- Conteúdo binário do arquivo .pfx
    senha_certificado TEXT NOT NULL,              -- Senha do certificado (base64)
    cnpj_extraido VARCHAR(14),                   -- CNPJ extraído do certificado
    razao_social VARCHAR(255),                   -- Razão social extraída
    emitente VARCHAR(255),                       -- Autoridade certificadora
    serial_number VARCHAR(100),                  -- Número serial do certificado
    validade_inicio TIMESTAMP,                   -- Início da validade
    validade_fim TIMESTAMP,                      -- Fim da validade
    codigo_municipio VARCHAR(7),                 -- Código IBGE do município (auto-lookup)
    nome_municipio VARCHAR(100),                 -- Nome do município
    uf VARCHAR(2),                               -- UF do município
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_nfse_cert_empresa ON nfse_certificados(empresa_id);
CREATE INDEX IF NOT EXISTS idx_nfse_cert_cnpj ON nfse_certificados(cnpj_extraido);
CREATE INDEX IF NOT EXISTS idx_nfse_cert_ativo ON nfse_certificados(ativo) WHERE ativo = TRUE;

-- Trigger para atualizar timestamp
CREATE OR REPLACE FUNCTION update_nfse_certificado_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_nfse_certificado ON nfse_certificados;
CREATE TRIGGER trg_update_nfse_certificado
    BEFORE UPDATE ON nfse_certificados
    FOR EACH ROW
    EXECUTE FUNCTION update_nfse_certificado_timestamp();

-- Comentários
COMMENT ON TABLE nfse_certificados IS 'Certificados digitais A1 (.pfx) para autenticação SOAP NFS-e';
COMMENT ON COLUMN nfse_certificados.pfx_data IS 'Conteúdo binário do arquivo .pfx (PKCS#12)';
COMMENT ON COLUMN nfse_certificados.senha_certificado IS 'Senha do certificado codificada em base64';
COMMENT ON COLUMN nfse_certificados.cnpj_extraido IS 'CNPJ extraído automaticamente do certificado';
COMMENT ON COLUMN nfse_certificados.codigo_municipio IS 'Código IBGE do município obtido via consulta CNPJ';
