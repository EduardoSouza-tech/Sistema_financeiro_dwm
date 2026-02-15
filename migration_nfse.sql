-- ============================================================================
-- MIGRAÇÃO: SISTEMA NFS-e (Nota Fiscal de Serviço Eletrônica)
-- Data: 2026-02-13
-- Descrição: Sistema de consulta e armazenamento de NFS-e via APIs SOAP municipais
-- ============================================================================

-- TABELA 1: Configurações de Municípios
-- Armazena as configurações de cada município onde a empresa presta serviços
CREATE TABLE IF NOT EXISTS nfse_config (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    cnpj_cpf VARCHAR(14) NOT NULL,
    provedor VARCHAR(50) NOT NULL,              -- GINFES, ISS.NET, BETHA, EISS, WEBISS, SIMPLISS
    codigo_municipio VARCHAR(7) NOT NULL,       -- Código IBGE (7 dígitos)
    nome_municipio VARCHAR(100),
    uf VARCHAR(2),
    inscricao_municipal VARCHAR(50) NOT NULL,   -- IM da empresa neste município
    url_customizada VARCHAR(255),               -- URL específica se diferente do padrão
    ativo BOOLEAN DEFAULT TRUE,
    testado_em TIMESTAMP,
    status_conexao VARCHAR(20) DEFAULT 'NAO_TESTADO',  -- OK, ERRO, NAO_TESTADO
    mensagem_erro TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    CONSTRAINT uk_nfse_config_empresa_municipio UNIQUE (empresa_id, codigo_municipio)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_nfse_config_empresa ON nfse_config(empresa_id);
CREATE INDEX IF NOT EXISTS idx_nfse_config_provedor ON nfse_config(provedor);
CREATE INDEX IF NOT EXISTS idx_nfse_config_municipio ON nfse_config(codigo_municipio);
CREATE INDEX IF NOT EXISTS idx_nfse_config_ativo ON nfse_config(ativo) WHERE ativo = TRUE;

-- Comentários
COMMENT ON TABLE nfse_config IS 'Configurações de municípios para busca de NFS-e';
COMMENT ON COLUMN nfse_config.provedor IS 'Provedor SOAP: GINFES, ISS.NET, BETHA, EISS, WEBISS, SIMPLISS';
COMMENT ON COLUMN nfse_config.codigo_municipio IS 'Código IBGE com 7 dígitos';
COMMENT ON COLUMN nfse_config.inscricao_municipal IS 'Inscrição Municipal da empresa neste município';

-- ============================================================================

-- TABELA 2: NFS-e Baixadas
-- Armazena todas as NFS-e consultadas e baixadas
CREATE TABLE IF NOT EXISTS nfse_baixadas (
    id SERIAL PRIMARY KEY,
    numero_nfse VARCHAR(50) NOT NULL,
    empresa_id INTEGER NOT NULL,
    cnpj_prestador VARCHAR(14) NOT NULL,
    cnpj_tomador VARCHAR(14),
    razao_social_tomador VARCHAR(255),
    data_emissao TIMESTAMP NOT NULL,
    data_competencia DATE,
    valor_servico NUMERIC(15, 2) NOT NULL,
    valor_deducoes NUMERIC(15, 2) DEFAULT 0,
    valor_iss NUMERIC(15, 2) DEFAULT 0,
    aliquota_iss NUMERIC(5, 2),
    valor_liquido NUMERIC(15, 2),
    codigo_servico VARCHAR(10),                 -- Código de serviço LC 116/2003
    discriminacao TEXT,                          -- Descrição dos serviços
    provedor VARCHAR(50),
    codigo_municipio VARCHAR(7),
    nome_municipio VARCHAR(100),
    uf VARCHAR(2),
    situacao VARCHAR(20) DEFAULT 'NORMAL',       -- NORMAL, CANCELADA, SUBSTITUIDA
    numero_rps VARCHAR(50),
    serie_rps VARCHAR(5),
    protocolo VARCHAR(50),
    codigo_verificacao VARCHAR(50),
    xml_content TEXT,                            -- XML completo da NFS-e
    xml_path VARCHAR(500),                       -- Caminho do arquivo XML no storage
    data_download TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_cancelamento TIMESTAMP,
    motivo_cancelamento TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    CONSTRAINT uk_nfse_numero_municipio UNIQUE (numero_nfse, codigo_municipio),
    CONSTRAINT ck_nfse_valor_positivo CHECK (valor_servico >= 0),
    CONSTRAINT ck_nfse_situacao CHECK (situacao IN ('NORMAL', 'CANCELADA', 'SUBSTITUIDA'))
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_nfse_empresa ON nfse_baixadas(empresa_id);
CREATE INDEX IF NOT EXISTS idx_nfse_prestador ON nfse_baixadas(cnpj_prestador);
CREATE INDEX IF NOT EXISTS idx_nfse_tomador ON nfse_baixadas(cnpj_tomador);
CREATE INDEX IF NOT EXISTS idx_nfse_data_emissao ON nfse_baixadas(data_emissao DESC);
CREATE INDEX IF NOT EXISTS idx_nfse_data_competencia ON nfse_baixadas(data_competencia DESC);
CREATE INDEX IF NOT EXISTS idx_nfse_provedor ON nfse_baixadas(provedor);
CREATE INDEX IF NOT EXISTS idx_nfse_municipio ON nfse_baixadas(codigo_municipio);
CREATE INDEX IF NOT EXISTS idx_nfse_situacao ON nfse_baixadas(situacao);
CREATE INDEX IF NOT EXISTS idx_nfse_numero ON nfse_baixadas(numero_nfse);

-- Índices compostos para consultas comuns
CREATE INDEX IF NOT EXISTS idx_nfse_empresa_competencia ON nfse_baixadas(empresa_id, data_competencia DESC);
CREATE INDEX IF NOT EXISTS idx_nfse_empresa_valor ON nfse_baixadas(empresa_id, valor_servico, data_emissao);

-- Comentários
COMMENT ON TABLE nfse_baixadas IS 'NFS-e consultadas e baixadas do sistema';
COMMENT ON COLUMN nfse_baixadas.situacao IS 'NORMAL: ativa, CANCELADA: cancelada, SUBSTITUIDA: substituída por outra';
COMMENT ON COLUMN nfse_baixadas.xml_content IS 'XML completo da NFS-e (compactado com gzip se necessário)';

-- ============================================================================

-- TABELA 3: RPS (Recibo Provisório de Serviços)
-- Armazena RPS que ainda não foram convertidos em NFS-e
CREATE TABLE IF NOT EXISTS rps (
    id SERIAL PRIMARY KEY,
    numero_rps VARCHAR(50) NOT NULL,
    serie_rps VARCHAR(5) DEFAULT '1' NOT NULL,
    empresa_id INTEGER NOT NULL,
    cnpj_prestador VARCHAR(14) NOT NULL,
    cnpj_tomador VARCHAR(14),
    data_emissao TIMESTAMP NOT NULL,
    valor_servico NUMERIC(15, 2) NOT NULL,
    discriminacao TEXT,
    status VARCHAR(20) DEFAULT 'PENDENTE',       -- PENDENTE, CONVERTIDO, ERRO, CANCELADO
    numero_nfse VARCHAR(50),                     -- Número da NFS-e quando convertido
    codigo_municipio VARCHAR(7),
    lote_id VARCHAR(50),
    protocolo VARCHAR(50),
    mensagem_retorno TEXT,
    xml_rps TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enviado_em TIMESTAMP,
    convertido_em TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    CONSTRAINT uk_rps_numero_serie_cnpj UNIQUE (numero_rps, serie_rps, cnpj_prestador),
    CONSTRAINT ck_rps_status CHECK (status IN ('PENDENTE', 'CONVERTIDO', 'ERRO', 'CANCELADO'))
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_rps_empresa ON rps(empresa_id);
CREATE INDEX IF NOT EXISTS idx_rps_status ON rps(status);
CREATE INDEX IF NOT EXISTS idx_rps_nfse ON rps(numero_nfse);
CREATE INDEX IF NOT EXISTS idx_rps_municipio ON rps(codigo_municipio);

-- Comentários
COMMENT ON TABLE rps IS 'Recibos Provisórios de Serviços pendentes de conversão';
COMMENT ON COLUMN rps.status IS 'PENDENTE: aguardando conversão, CONVERTIDO: virou NFS-e, ERRO: erro na conversão';

-- ============================================================================

-- TABELA 4: Controle NSU (Número Sequencial Único)
-- Para sincronização incremental quando o provedor suporta
CREATE TABLE IF NOT EXISTS nsu_nfse (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    informante VARCHAR(14) NOT NULL,             -- CNPJ/CPF
    codigo_municipio VARCHAR(7),                 -- NULL = todos os municípios
    ult_nsu BIGINT DEFAULT 0,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    CONSTRAINT uk_nsu_empresa_informante_municipio UNIQUE (empresa_id, informante, codigo_municipio)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_nsu_empresa ON nsu_nfse(empresa_id);
CREATE INDEX IF NOT EXISTS idx_nsu_informante ON nsu_nfse(informante);

-- Comentários
COMMENT ON TABLE nsu_nfse IS 'Controle de NSU para sincronização incremental de NFS-e';
COMMENT ON COLUMN nsu_nfse.ult_nsu IS 'Último NSU processado para este informante/município';

-- ============================================================================

-- TABELA 5: Certificados Digitais A1
-- Armazena certificados digitais das empresas para assinatura de NFS-e
CREATE TABLE IF NOT EXISTS nfse_certificados (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    pfx_data BYTEA NOT NULL,                     -- Binário do arquivo .pfx/.p12
    senha_certificado VARCHAR(255) NOT NULL,     -- Senha criptografada (base64)
    cnpj_extraido VARCHAR(14),                   -- CNPJ extraído do certificado
    razao_social VARCHAR(255),                   -- Razão social extraída
    emitente VARCHAR(255),                       -- AC emissora do certificado
    serial_number VARCHAR(100),                  -- Número de série do certificado
    validade_inicio TIMESTAMP,                   -- Data início validade
    validade_fim TIMESTAMP,                      -- Data fim validade
    codigo_municipio VARCHAR(7),                 -- Município identificado pelo CNPJ
    nome_municipio VARCHAR(100),
    uf VARCHAR(2),
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    CONSTRAINT ck_cert_validade CHECK (validade_fim > validade_inicio)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_cert_empresa ON nfse_certificados(empresa_id);
CREATE INDEX IF NOT EXISTS idx_cert_ativo ON nfse_certificados(ativo) WHERE ativo = TRUE;
CREATE INDEX IF NOT EXISTS idx_cert_validade_fim ON nfse_certificados(validade_fim);
CREATE INDEX IF NOT EXISTS idx_cert_cnpj ON nfse_certificados(cnpj_extraido);

-- Comentários
COMMENT ON TABLE nfse_certificados IS 'Certificados digitais A1 para assinatura de NFS-e';
COMMENT ON COLUMN nfse_certificados.pfx_data IS 'Binário completo do certificado .pfx ou .p12';
COMMENT ON COLUMN nfse_certificados.senha_certificado IS 'Senha do certificado codificada em base64';
COMMENT ON COLUMN nfse_certificados.ativo IS 'Apenas um certificado ativo por empresa';

-- ============================================================================

-- VIEWS ÚTEIS
-- View: Resumo de NFS-e por empresa
CREATE OR REPLACE VIEW vw_nfse_resumo_empresa AS
SELECT 
    e.id AS empresa_id,
    e.razao_social,
    COUNT(n.id) AS total_nfse,
    COUNT(DISTINCT n.codigo_municipio) AS total_municipios,
    SUM(CASE WHEN n.situacao = 'NORMAL' THEN 1 ELSE 0 END) AS nfse_ativas,
    SUM(CASE WHEN n.situacao = 'CANCELADA' THEN 1 ELSE 0 END) AS nfse_canceladas,
    SUM(n.valor_servico) AS valor_total_servicos,
    SUM(n.valor_iss) AS valor_total_iss,
    MIN(n.data_emissao) AS primeira_nfse,
    MAX(n.data_emissao) AS ultima_nfse
FROM empresas e
LEFT JOIN nfse_baixadas n ON n.empresa_id = e.id
GROUP BY e.id, e.razao_social;

-- View: Resumo mensal de NFS-e
CREATE OR REPLACE VIEW vw_nfse_resumo_mensal AS
SELECT 
    empresa_id,
    DATE_TRUNC('month', data_competencia) AS mes_referencia,
    COUNT(*) AS total_nfse,
    COUNT(DISTINCT codigo_municipio) AS total_municipios,
    SUM(valor_servico) AS valor_servicos,
    SUM(valor_deducoes) AS valor_deducoes,
    SUM(valor_iss) AS valor_iss,
    SUM(valor_liquido) AS valor_liquido,
    AVG(aliquota_iss) AS aliquota_media
FROM nfse_baixadas
WHERE situacao = 'NORMAL'
GROUP BY empresa_id, DATE_TRUNC('month', data_competencia);

-- View: RPS pendentes de conversão
CREATE OR REPLACE VIEW vw_rps_pendentes AS
SELECT 
    r.*,
    e.razao_social AS empresa_nome,
    EXTRACT(DAY FROM (CURRENT_TIMESTAMP - r.criado_em)) AS dias_pendente
FROM rps r
JOIN empresas e ON e.id = r.empresa_id
WHERE r.status = 'PENDENTE'
ORDER BY r.criado_em ASC;

-- ============================================================================

-- TRIGGERS
-- Trigger para atualizar timestamp de atualização
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar triggers
DROP TRIGGER IF EXISTS update_nfse_config_updated_at ON nfse_config;
CREATE TRIGGER update_nfse_config_updated_at
    BEFORE UPDATE ON nfse_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_nfse_baixadas_updated_at ON nfse_baixadas;
CREATE TRIGGER update_nfse_baixadas_updated_at
    BEFORE UPDATE ON nfse_baixadas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_rps_updated_at ON rps;
CREATE TRIGGER update_rps_updated_at
    BEFORE UPDATE ON rps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_nsu_updated_at ON nsu_nfse;
CREATE TRIGGER update_nsu_updated_at
    BEFORE UPDATE ON nsu_nfse
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_nfse_certificados_updated_at ON nfse_certificados;
CREATE TRIGGER update_nfse_certificados_updated_at
    BEFORE UPDATE ON nfse_certificados
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================

-- FUNÇÕES ÚTEIS
-- Função: Buscar NFS-e por período
CREATE OR REPLACE FUNCTION buscar_nfse_periodo(
    p_empresa_id INTEGER,
    p_data_inicial DATE,
    p_data_final DATE,
    p_municipio VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    id INTEGER,
    numero_nfse VARCHAR,
    data_emissao TIMESTAMP,
    cnpj_tomador VARCHAR,
    razao_social_tomador VARCHAR,
    valor_servico NUMERIC,
    valor_iss NUMERIC,
    municipio VARCHAR,
    situacao VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        n.id,
        n.numero_nfse,
        n.data_emissao,
        n.cnpj_tomador,
        n.razao_social_tomador,
        n.valor_servico,
        n.valor_iss,
        n.nome_municipio,
        n.situacao
    FROM nfse_baixadas n
    WHERE n.empresa_id = p_empresa_id
    AND n.data_competencia BETWEEN p_data_inicial AND p_data_final
    AND (p_municipio IS NULL OR n.codigo_municipio = p_municipio)
    ORDER BY n.data_emissao DESC;
END;
$$ LANGUAGE plpgsql;

-- Função: Total de NFS-e por mês
CREATE OR REPLACE FUNCTION total_nfse_mensal(
    p_empresa_id INTEGER,
    p_ano INTEGER,
    p_mes INTEGER
)
RETURNS TABLE (
    total_notas BIGINT,
    valor_total NUMERIC,
    iss_total NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT,
        COALESCE(SUM(valor_servico), 0),
        COALESCE(SUM(valor_iss), 0)
    FROM nfse_baixadas
    WHERE empresa_id = p_empresa_id
    AND EXTRACT(YEAR FROM data_competencia) = p_ano
    AND EXTRACT(MONTH FROM data_competencia) = p_mes
    AND situacao = 'NORMAL';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================

-- PERMISSÕES (adicionar às tabelas de permissões existentes)
-- Nota: É necessário adicionar essas permissões manualmente no sistema

-- Permissões sugeridas:
-- nfse_view: Visualizar NFS-e
-- nfse_buscar: Buscar novas NFS-e
-- nfse_config: Configurar municípios
-- nfse_export: Exportar dados
-- nfse_delete: Excluir NFS-e

-- ============================================================================

-- AUDITORIA
-- Tabela de log de operações (opcional, para rastreabilidade)
CREATE TABLE IF NOT EXISTS nfse_audit_log (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER,
    usuario_id INTEGER,
    operacao VARCHAR(50) NOT NULL,              -- BUSCA, CONFIG, EXCLUSAO, EXPORT
    detalhes JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE SET NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);

-- Índice
CREATE INDEX IF NOT EXISTS idx_audit_log_empresa ON nfse_audit_log(empresa_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_usuario ON nfse_audit_log(usuario_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_operacao ON nfse_audit_log(operacao);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON nfse_audit_log(created_at DESC);

COMMENT ON TABLE nfse_audit_log IS 'Log de auditoria de operações no sistema NFS-e';

-- ============================================================================

-- DADOS INICIAIS (Provedores conhecidos)
-- Inserir mapeamento de cidades principais (opcional)

-- ============================================================================

COMMENT ON DATABASE postgres IS 'Sistema Financeiro DWM - Com módulo NFS-e';

-- ✅ Migração concluída com sucesso!
-- Total de tabelas criadas: 6 (nfse_config, nfse_baixadas, rps, nsu_nfse, nfse_certificados, nfse_audit_log)
-- Total de views: 3
-- Total de funções: 2
-- Total de triggers: 5
