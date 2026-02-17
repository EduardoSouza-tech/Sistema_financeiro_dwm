-- ============================================================================
-- MIGRATION: Sistema de Busca NF-e e CT-e
-- Descrição: Cria tabelas para gerenciamento de certificados digitais e log
--            de documentos fiscais eletrônicos
-- Data: 2026-02-17
-- Autor: Sistema Financeiro DWM
-- ============================================================================

-- ============================================================================
-- TABELA: certificados_digitais
-- Armazena certificados digitais A1 para busca automática de documentos
-- ============================================================================

CREATE TABLE IF NOT EXISTS certificados_digitais (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    
    -- Dados do certificado
    cnpj VARCHAR(14) NOT NULL,
    nome_certificado VARCHAR(255) NOT NULL,
    caminho_pfx TEXT,                       -- Caminho do arquivo .pfx (opcional se usar base64)
    pfx_base64 TEXT,                        -- Conteúdo do certificado em base64 (opcional)
    senha_pfx TEXT NOT NULL,                -- Senha criptografada (usar Fernet)
    
    -- Configuração SEFAZ
    cuf INTEGER NOT NULL,                   -- Código UF (12=AC, 27=AL, 16=AP, 13=AM, 29=BA, 23=CE, 53=DF, 32=ES, 52=GO, 21=MA, 51=MT, 50=MS, 31=MG, 15=PA, 25=PB, 41=PR, 26=PE, 22=PI, 33=RJ, 24=RN, 43=RS, 11=RO, 14=RR, 42=SC, 35=SP, 28=SE, 17=TO)
    ambiente VARCHAR(10) DEFAULT 'producao', -- 'producao' ou 'homologacao'
    ativo BOOLEAN DEFAULT true,
    
    -- NSU Control (Número Sequencial Único para busca incremental)
    ultimo_nsu VARCHAR(15) DEFAULT '000000000000000',
    max_nsu VARCHAR(15),                    -- NSU máximo conhecido
    data_ultima_busca TIMESTAMP,
    
    -- Validade do certificado
    valido_de DATE,
    valido_ate DATE,
    
    -- Estatísticas
    total_documentos_baixados INTEGER DEFAULT 0,
    total_nfes INTEGER DEFAULT 0,
    total_ctes INTEGER DEFAULT 0,
    total_eventos INTEGER DEFAULT 0,
    
    -- Auditoria
    criado_em TIMESTAMP DEFAULT NOW(),
    criado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    atualizado_em TIMESTAMP DEFAULT NOW(),
    atualizado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT uk_certificado_cnpj_empresa UNIQUE (empresa_id, cnpj),
    CONSTRAINT ck_ambiente CHECK (ambiente IN ('producao', 'homologacao')),
    CONSTRAINT ck_pfx_storage CHECK (caminho_pfx IS NOT NULL OR pfx_base64 IS NOT NULL)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_cert_empresa ON certificados_digitais(empresa_id);
CREATE INDEX IF NOT EXISTS idx_cert_ativo ON certificados_digitais(ativo);
CREATE INDEX IF NOT EXISTS idx_cert_cnpj ON certificados_digitais(cnpj);
CREATE INDEX IF NOT EXISTS idx_cert_validade ON certificados_digitais(valido_ate);

-- Comentários
COMMENT ON TABLE certificados_digitais IS 'Certificados digitais A1 para busca de documentos fiscais via SEFAZ';
COMMENT ON COLUMN certificados_digitais.cuf IS 'Código da UF do certificado (usado para determinar URL SEFAZ)';
COMMENT ON COLUMN certificados_digitais.ultimo_nsu IS 'Último NSU processado. Busca incremental inicia daqui.';
COMMENT ON COLUMN certificados_digitais.senha_pfx IS 'Senha criptografada com Fernet (CERT_ENCRYPTION_KEY)';


-- ============================================================================
-- TABELA: documentos_fiscais_log
-- Log de todos os documentos baixados via DFe Distribution
-- ============================================================================

CREATE TABLE IF NOT EXISTS documentos_fiscais_log (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    certificado_id INTEGER REFERENCES certificados_digitais(id) ON DELETE SET NULL,
    
    -- Identificação do documento
    nsu VARCHAR(15) NOT NULL,               -- NSU único do documento na SEFAZ
    chave VARCHAR(44),                      -- Chave de acesso (44 dígitos)
    tipo_documento VARCHAR(10) NOT NULL,    -- 'NFe', 'CTe', 'NFSe', 'Evento'
    schema_name VARCHAR(50),                -- 'procNFe_v4.00', 'resNFe_v1.01', 'procCTe_v4.00', 'procEventoNFe_v1.00'
    
    -- Status de processamento
    processado BOOLEAN DEFAULT false,
    data_processamento TIMESTAMP,
    erro TEXT,
    tentativas INTEGER DEFAULT 0,
    
    -- Metadados do documento
    numero_documento VARCHAR(20),
    serie VARCHAR(10),
    valor_total DECIMAL(15, 2),
    cnpj_emitente VARCHAR(14),
    nome_emitente VARCHAR(255),
    cnpj_destinatario VARCHAR(14),
    nome_destinatario VARCHAR(255),
    data_emissao TIMESTAMP,
    
    -- Referência ao documento processado
    nota_fiscal_id INTEGER REFERENCES notas_fiscais(id) ON DELETE SET NULL,
    
    -- Armazenamento
    caminho_xml TEXT,                       -- Caminho do arquivo XML salvo
    tamanho_bytes INTEGER,                  -- Tamanho do arquivo
    hash_md5 VARCHAR(32),                   -- Hash MD5 do conteúdo (detecção de duplicatas)
    
    -- Auditoria
    data_busca TIMESTAMP DEFAULT NOW(),
    busca_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT uk_doc_nsu_cert UNIQUE (certificado_id, nsu),
    CONSTRAINT uk_doc_chave_empresa UNIQUE (empresa_id, chave, tipo_documento),
    CONSTRAINT ck_tipo_documento CHECK (tipo_documento IN ('NFe', 'CTe', 'NFSe', 'Evento', 'MDFe'))
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_doc_log_empresa ON documentos_fiscais_log(empresa_id);
CREATE INDEX IF NOT EXISTS idx_doc_log_certificado ON documentos_fiscais_log(certificado_id);
CREATE INDEX IF NOT EXISTS idx_doc_log_chave ON documentos_fiscais_log(chave);
CREATE INDEX IF NOT EXISTS idx_doc_log_nsu ON documentos_fiscais_log(nsu);
CREATE INDEX IF NOT EXISTS idx_doc_log_tipo ON documentos_fiscais_log(tipo_documento);
CREATE INDEX IF NOT EXISTS idx_doc_log_processado ON documentos_fiscais_log(processado);
CREATE INDEX IF NOT EXISTS idx_doc_log_data_busca ON documentos_fiscais_log(data_busca);
CREATE INDEX IF NOT EXISTS idx_doc_log_cnpj_emit ON documentos_fiscais_log(cnpj_emitente);
CREATE INDEX IF NOT EXISTS idx_doc_log_data_emissao ON documentos_fiscais_log(data_emissao);

-- Comentários
COMMENT ON TABLE documentos_fiscais_log IS 'Log de todos os documentos fiscais baixados via API SEFAZ';
COMMENT ON COLUMN documentos_fiscais_log.nsu IS 'Número Sequencial Único atribuído pela SEFAZ';
COMMENT ON COLUMN documentos_fiscais_log.schema_name IS 'Schema do XML (procNFe, resNFe, procCTe, procEventoNFe)';
COMMENT ON COLUMN documentos_fiscais_log.hash_md5 IS 'Hash MD5 do conteúdo para detectar duplicatas';


-- ============================================================================
-- PERMISSÕES
-- ============================================================================

-- Inserir novas permissões para o módulo
INSERT INTO permissoes (codigo, nome, descricao, categoria) VALUES
('REL_NFE_VIS', 'relatorios.nfe.visualizar', 'Visualizar NF-e no sistema', 'relatorios'),
('REL_NFE_BUS', 'relatorios.nfe.buscar', 'Buscar NF-e na SEFAZ', 'relatorios'),
('REL_NFE_EXP', 'relatorios.nfe.exportar', 'Exportar XMLs de NF-e', 'relatorios'),
('REL_NFE_REP', 'relatorios.nfe.reprocessar', 'Reprocessar NF-e existente', 'relatorios'),
('REL_CTE_VIS', 'relatorios.cte.visualizar', 'Visualizar CT-e no sistema', 'relatorios'),
('REL_CTE_BUS', 'relatorios.cte.buscar', 'Buscar CT-e na SEFAZ', 'relatorios'),
('REL_CTE_EXP', 'relatorios.cte.exportar', 'Exportar XMLs de CT-e', 'relatorios'),
('REL_CTE_REP', 'relatorios.cte.reprocessar', 'Reprocessar CT-e existente', 'relatorios'),
('REL_CERT_VIS', 'relatorios.certificados.visualizar', 'Visualizar certificados digitais', 'relatorios'),
('REL_CERT_CRI', 'relatorios.certificados.criar', 'Cadastrar certificados digitais', 'relatorios'),
('REL_CERT_EDI', 'relatorios.certificados.editar', 'Editar certificados digitais', 'relatorios'),
('REL_CERT_DEL', 'relatorios.certificados.excluir', 'Excluir certificados digitais', 'relatorios'),
('REL_LOG_VIS', 'relatorios.log.visualizar', 'Visualizar log de documentos fiscais', 'relatorios')
ON CONFLICT (codigo) DO NOTHING;


-- ============================================================================
-- FUNÇÕES E TRIGGERS
-- ============================================================================

-- Função para atualizar timestamp
CREATE OR REPLACE FUNCTION update_certificado_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar timestamp em certificados_digitais
DROP TRIGGER IF EXISTS trg_certificado_update ON certificados_digitais;
CREATE TRIGGER trg_certificado_update
    BEFORE UPDATE ON certificados_digitais
    FOR EACH ROW
    EXECUTE FUNCTION update_certificado_timestamp();


-- Função para atualizar estatísticas do certificado
CREATE OR REPLACE FUNCTION atualizar_estatisticas_certificado()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE certificados_digitais
    SET 
        total_documentos_baixados = total_documentos_baixados + 1,
        total_nfes = CASE WHEN NEW.tipo_documento = 'NFe' THEN total_nfes + 1 ELSE total_nfes END,
        total_ctes = CASE WHEN NEW.tipo_documento = 'CTe' THEN total_ctes + 1 ELSE total_ctes END,
        total_eventos = CASE WHEN NEW.tipo_documento = 'Evento' THEN total_eventos + 1 ELSE total_eventos END,
        data_ultima_busca = NEW.data_busca
    WHERE id = NEW.certificado_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar estatísticas quando documento é inserido
DROP TRIGGER IF EXISTS trg_doc_log_estatisticas ON documentos_fiscais_log;
CREATE TRIGGER trg_doc_log_estatisticas
    AFTER INSERT ON documentos_fiscais_log
    FOR EACH ROW
    WHEN (NEW.certificado_id IS NOT NULL)
    EXECUTE FUNCTION atualizar_estatisticas_certificado();


-- ============================================================================
-- VIEWS ÚTEIS
-- ============================================================================

-- View: Certificados com estatísticas
CREATE OR REPLACE VIEW v_certificados_stats AS
SELECT 
    c.id,
    c.empresa_id,
    e.nome_fantasia as empresa_nome,
    c.cnpj,
    c.nome_certificado,
    c.ambiente,
    c.ativo,
    c.ultimo_nsu,
    c.max_nsu,
    CAST(c.ultimo_nsu AS BIGINT) as nsu_atual_num,
    CAST(COALESCE(c.max_nsu, c.ultimo_nsu) AS BIGINT) as nsu_max_num,
    CAST(COALESCE(c.max_nsu, c.ultimo_nsu) AS BIGINT) - CAST(c.ultimo_nsu AS BIGINT) as pendentes,
    c.data_ultima_busca,
    c.valido_ate,
    CASE 
        WHEN c.valido_ate < CURRENT_DATE THEN 'Vencido'
        WHEN c.valido_ate < CURRENT_DATE + INTERVAL '30 days' THEN 'A vencer'
        ELSE 'Válido'
    END as status_validade,
    c.total_documentos_baixados,
    c.total_nfes,
    c.total_ctes,
    c.total_eventos,
    c.criado_em,
    u.username as criado_por_nome
FROM certificados_digitais c
JOIN empresas e ON e.id = c.empresa_id
LEFT JOIN usuarios u ON u.id = c.criado_por;

COMMENT ON VIEW v_certificados_stats IS 'View com estatísticas dos certificados digitais';


-- View: Últimos documentos processados
CREATE OR REPLACE VIEW v_documentos_recentes AS
SELECT 
    dl.id,
    dl.empresa_id,
    e.nome_fantasia as empresa_nome,
    dl.nsu,
    dl.chave,
    dl.tipo_documento,
    dl.numero_documento,
    dl.nome_emitente,
    dl.nome_destinatario,
    dl.valor_total,
    dl.data_emissao,
    dl.processado,
    dl.data_busca,
    dl.caminho_xml,
    c.cnpj as certificado_cnpj,
    c.nome_certificado
FROM documentos_fiscais_log dl
JOIN empresas e ON e.id = dl.empresa_id
LEFT JOIN certificados_digitais c ON c.id = dl.certificado_id
ORDER BY dl.data_busca DESC;

COMMENT ON VIEW v_documentos_recentes IS 'View dos documentos fiscais mais recentes';


-- View: Resumo mensal por tipo
CREATE OR REPLACE VIEW v_resumo_mensal_docs AS
SELECT 
    dl.empresa_id,
    e.nome_fantasia as empresa_nome,
    DATE_TRUNC('month', dl.data_emissao) as mes,
    dl.tipo_documento,
    COUNT(*) as quantidade,
    SUM(dl.valor_total) as valor_total,
    COUNT(*) FILTER (WHERE dl.processado = true) as processados,
    COUNT(*) FILTER (WHERE dl.processado = false) as pendentes
FROM documentos_fiscais_log dl
JOIN empresas e ON e.id = dl.empresa_id
WHERE dl.data_emissao IS NOT NULL
GROUP BY dl.empresa_id, e.nome_fantasia, DATE_TRUNC('month', dl.data_emissao), dl.tipo_documento
ORDER BY mes DESC, dl.tipo_documento;

COMMENT ON VIEW v_resumo_mensal_docs IS 'Resumo mensal de documentos fiscais por tipo';


-- ============================================================================
-- DADOS INICIAIS (se necessário)
-- ============================================================================

-- Por segurança, não inserir certificados de exemplo em produção
-- Administradores devem cadastrar os certificados via interface


-- ============================================================================
-- VERIFICAÇÃO FINAL
-- ============================================================================

DO $$
BEGIN
    -- Verificar se as tabelas foram criadas
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'certificados_digitais') THEN
        RAISE NOTICE '✓ Tabela certificados_digitais criada com sucesso';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documentos_fiscais_log') THEN
        RAISE NOTICE '✓ Tabela documentos_fiscais_log criada com sucesso';
    END IF;
    
    -- Verificar permissões
    IF EXISTS (SELECT 1 FROM permissoes WHERE nome LIKE 'relatorios.%') THEN
        RAISE NOTICE '✓ Permissões de relatórios criadas com sucesso';
    END IF;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration concluída com sucesso!';
    RAISE NOTICE 'Próximo passo: Implementar módulos Python';
    RAISE NOTICE '========================================';
END $$;
