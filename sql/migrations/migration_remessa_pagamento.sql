-- ============================================================================
-- MÓDULO DE REMESSA DE PAGAMENTOS - SICREDI
-- Sistema Financeiro DWM
-- ============================================================================

-- Tabela de Remessas
CREATE TABLE IF NOT EXISTS remessas_pagamento (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    numero_sequencial INTEGER NOT NULL,
    tipo_arquivo VARCHAR(10) NOT NULL DEFAULT 'CNAB240', -- CNAB240, CNAB400, API
    data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_arquivo DATE NOT NULL,
    
    -- Identificação do arquivo
    nome_arquivo VARCHAR(255),
    hash_arquivo VARCHAR(64),  -- SHA-256
    caminho_arquivo TEXT,
    
    -- Estatísticas
    quantidade_pagamentos INTEGER DEFAULT 0,
    quantidade_ted INTEGER DEFAULT 0,
    quantidade_pix INTEGER DEFAULT 0,
    quantidade_boleto INTEGER DEFAULT 0,
    quantidade_tributo INTEGER DEFAULT 0,
    valor_total DECIMAL(15,2) DEFAULT 0.00,
    
    -- Status do processamento
    status VARCHAR(20) DEFAULT 'GERADO', -- GERADO, ENVIADO, PROCESSADO, ERRO
    data_envio TIMESTAMP,
    data_processamento TIMESTAMP,
    
    -- Retorno bancário
    arquivo_retorno TEXT,
    data_retorno TIMESTAMP,
    quantidade_efetuados INTEGER DEFAULT 0,
    quantidade_rejeitados INTEGER DEFAULT 0,
    quantidade_agendados INTEGER DEFAULT 0,
    
    -- Auditoria
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Observações
    observacoes TEXT,
    erros_processamento TEXT,
    
    CONSTRAINT fk_remessa_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_remessa_usuario FOREIGN KEY (created_by) REFERENCES usuarios(id),
    CONSTRAINT uk_remessa_sequencial UNIQUE (empresa_id, numero_sequencial)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_remessa_empresa ON remessas_pagamento(empresa_id);
CREATE INDEX IF NOT EXISTS idx_remessa_status ON remessas_pagamento(status);
CREATE INDEX IF NOT EXISTS idx_remessa_data ON remessas_pagamento(data_arquivo);
CREATE INDEX IF NOT EXISTS idx_remessa_created_by ON remessas_pagamento(created_by);

-- Comentários
COMMENT ON TABLE remessas_pagamento IS 'Registro de remessas de pagamento enviadas ao banco';
COMMENT ON COLUMN remessas_pagamento.numero_sequencial IS 'Número sequencial da remessa por empresa (auto-incremento)';
COMMENT ON COLUMN remessas_pagamento.hash_arquivo IS 'Hash SHA-256 do arquivo para validação de integridade';
COMMENT ON COLUMN remessas_pagamento.status IS 'GERADO = arquivo criado, ENVIADO = enviado ao banco, PROCESSADO = retorno recebido e processado';

-- ============================================================================

-- Tabela de Itens da Remessa (Detalhamento)
CREATE TABLE IF NOT EXISTS remessas_pagamento_itens (
    id SERIAL PRIMARY KEY,
    remessa_id INTEGER NOT NULL,
    lancamento_id INTEGER,  -- FK para lancamentos (contas a pagar)
    
    -- Dados do pagamento
    tipo_pagamento VARCHAR(20) NOT NULL, -- TED, PIX, BOLETO, TRIBUTO
    sequencial_lote INTEGER,
    sequencial_registro INTEGER,
    
    -- Favorecido
    nome_favorecido VARCHAR(100) NOT NULL,
    cpf_cnpj_favorecido VARCHAR(18),
    
    -- Dados bancários (TED/PIX)
    banco_favorecido VARCHAR(3),
    agencia_favorecido VARCHAR(5),
    conta_favorecido VARCHAR(15),
    tipo_conta VARCHAR(2), -- CC, CP, PG
    
    -- PIX
    chave_pix VARCHAR(100),
    tipo_chave_pix VARCHAR(10), -- CPF, CNPJ, EMAIL, TELEFONE, ALEATORIA
    
    -- Boleto
    codigo_barras VARCHAR(47),
    
    -- Tributo
    codigo_receita VARCHAR(4),  -- Para DARF, GPS, etc.
    periodo_apuracao DATE,
    numero_referencia VARCHAR(17),
    
    -- Valores
    valor_principal DECIMAL(15,2) NOT NULL,
    valor_desconto DECIMAL(15,2) DEFAULT 0.00,
    valor_mora DECIMAL(15,2) DEFAULT 0.00,
    valor_multa DECIMAL(15,2) DEFAULT 0.00,
    valor_total DECIMAL(15,2) NOT NULL,
    
    -- Datas
    data_vencimento DATE,
    data_pagamento DATE NOT NULL,
    
    -- Identificação
    seu_numero VARCHAR(20),  -- Número de controle da empresa
    nosso_numero VARCHAR(20), -- Número de controle do banco
    
    -- Status e retorno
    status VARCHAR(20) DEFAULT 'PENDENTE', -- PENDENTE, EFETUADO, REJEITADO, AGENDADO
    codigo_ocorrencia VARCHAR(10),
    descricao_ocorrencia VARCHAR(255),
    data_efetivacao DATE,
    valor_efetivado DECIMAL(15,2),
    
    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_remessa_item_remessa FOREIGN KEY (remessa_id) REFERENCES remessas_pagamento(id) ON DELETE CASCADE,
    CONSTRAINT fk_remessa_item_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_remessa_item_remessa ON remessas_pagamento_itens(remessa_id);
CREATE INDEX IF NOT EXISTS idx_remessa_item_lancamento ON remessas_pagamento_itens(lancamento_id);
CREATE INDEX IF NOT EXISTS idx_remessa_item_status ON remessas_pagamento_itens(status);
CREATE INDEX IF NOT EXISTS idx_remessa_item_tipo ON remessas_pagamento_itens(tipo_pagamento);
CREATE INDEX IF NOT EXISTS idx_remessa_item_data_pagamento ON remessas_pagamento_itens(data_pagamento);

COMMENT ON TABLE remessas_pagamento_itens IS 'Detalhamento de cada pagamento incluído na remessa';
COMMENT ON COLUMN remessas_pagamento_itens.seu_numero IS 'Número de controle interno da empresa';
COMMENT ON COLUMN remessas_pagamento_itens.nosso_numero IS 'Número atribuído pelo banco após processamento';

-- ============================================================================

-- Tabela de Configurações Sicredi (Convênio)
CREATE TABLE IF NOT EXISTS sicredi_configuracao (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    
    -- Identificação no Sicredi
    codigo_beneficiario VARCHAR(20) NOT NULL,
    codigo_convenio VARCHAR(20) NOT NULL,
    posto VARCHAR(2),
    codigo_cedente VARCHAR(5),
    
    -- Dados bancários da empresa
    banco VARCHAR(3) DEFAULT '748', -- Sicredi
    agencia VARCHAR(5) NOT NULL,
    agencia_dv VARCHAR(1),
    conta VARCHAR(12) NOT NULL,
    conta_dv VARCHAR(1),
    
    -- Carteiras e modalidades
    carteira_ted VARCHAR(3) DEFAULT '01',
    carteira_pix VARCHAR(3) DEFAULT '45',
    carteira_boleto VARCHAR(3) DEFAULT '31',
    carteira_tributo VARCHAR(3) DEFAULT '17',
    
    -- Controle de sequenciais
    ultimo_sequencial_remessa INTEGER DEFAULT 0,
    ultimo_sequencial_lote INTEGER DEFAULT 0,
    
    -- Integração API (futuro)
    api_habilitada BOOLEAN DEFAULT FALSE,
    api_client_id VARCHAR(100),
    api_client_secret VARCHAR(100),
    api_endpoint TEXT,
    
    -- Status
    ativo BOOLEAN DEFAULT TRUE,
    
    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    
    CONSTRAINT fk_sicredi_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT fk_sicredi_usuario FOREIGN KEY (created_by) REFERENCES usuarios(id),
    CONSTRAINT uk_sicredi_empresa UNIQUE (empresa_id)
);

CREATE INDEX IF NOT EXISTS idx_sicredi_empresa ON sicredi_configuracao(empresa_id);

COMMENT ON TABLE sicredi_configuracao IS 'Configurações de convênio Sicredi por empresa';
COMMENT ON COLUMN sicredi_configuracao.codigo_beneficiario IS 'Código identificador da empresa no Sicredi';
COMMENT ON COLUMN sicredi_configuracao.ultimo_sequencial_remessa IS 'Controle automático de numeração de arquivos';

-- ============================================================================

-- Adicionar campos em lancamentos para suportar remessa
ALTER TABLE lancamentos 
ADD COLUMN IF NOT EXISTS remessa_id INTEGER,
ADD COLUMN IF NOT EXISTS remessa_item_id INTEGER,
ADD COLUMN IF NOT EXISTS data_remessa TIMESTAMP,
ADD COLUMN IF NOT EXISTS status_remessa VARCHAR(20), -- PENDENTE, INCLUIDO, EFETUADO, REJEITADO
ADD COLUMN IF NOT EXISTS codigo_barras VARCHAR(47),
ADD COLUMN IF NOT EXISTS chave_pix VARCHAR(100),
ADD COLUMN IF NOT EXISTS tipo_chave_pix VARCHAR(10);

-- FK para remessa
ALTER TABLE lancamentos
ADD CONSTRAINT fk_lancamento_remessa FOREIGN KEY (remessa_id) REFERENCES remessas_pagamento(id),
ADD CONSTRAINT fk_lancamento_remessa_item FOREIGN KEY (remessa_item_id) REFERENCES remessas_pagamento_itens(id);

CREATE INDEX IF NOT EXISTS idx_lancamento_remessa ON lancamentos(remessa_id);
CREATE INDEX IF NOT EXISTS idx_lancamento_status_remessa ON lancamentos(status_remessa);

COMMENT ON COLUMN lancamentos.remessa_id IS 'Remessa que incluiu este lançamento';
COMMENT ON COLUMN lancamentos.status_remessa IS 'Status do pagamento na remessa bancária';

-- ============================================================================

-- View para facilitar consultas de remessas
CREATE OR REPLACE VIEW v_remessas_resumo AS
SELECT 
    r.id,
    r.empresa_id,
    e.razao_social AS empresa_nome,
    r.numero_sequencial,
    r.tipo_arquivo,
    r.nome_arquivo,
    r.data_geracao,
    r.data_arquivo,
    r.quantidade_pagamentos,
    r.quantidade_ted,
    r.quantidade_pix,
    r.quantidade_boleto,
    r.quantidade_tributo,
    r.valor_total,
    r.status,
    r.data_envio,
    r.data_retorno,
    r.quantidade_efetuados,
    r.quantidade_rejeitados,
    r.quantidade_agendados,
    u.username AS criado_por,
    r.created_at,
    r.observacoes
FROM remessas_pagamento r
JOIN empresas e ON r.empresa_id = e.id
LEFT JOIN usuarios u ON r.created_by = u.id
ORDER BY r.created_at DESC;

COMMENT ON VIEW v_remessas_resumo IS 'Visão resumida das remessas com informações consolidadas';

-- ============================================================================

-- View para facilitar consultas de itens pendentes de pagamento
CREATE OR REPLACE VIEW v_contas_pagar_pendentes_remessa AS
SELECT 
    l.id,
    l.empresa_id,
    l.descricao,
    l.valor,
    l.data_vencimento,
    l.tipo,
    c.nome AS categoria,
    f.nome AS fornecedor,
    f.cpf_cnpj,
    f.banco,
    f.agencia,
    f.conta,
    l.codigo_barras,
    l.chave_pix,
    l.tipo_chave_pix,
    l.status AS status_lancamento,
    l.status_remessa,
    l.remessa_id,
    CASE 
        WHEN l.codigo_barras IS NOT NULL AND l.codigo_barras != '' THEN 'BOLETO'
        WHEN l.chave_pix IS NOT NULL AND l.chave_pix != '' THEN 'PIX'
        WHEN f.banco IS NOT NULL AND f.agencia IS NOT NULL AND f.conta IS NOT NULL THEN 'TED'
        ELSE 'INDEFINIDO'
    END AS tipo_pagamento_sugerido,
    CASE 
        WHEN l.data_vencimento < CURRENT_DATE THEN 'VENCIDO'
        WHEN l.data_vencimento = CURRENT_DATE THEN 'VENCE_HOJE'
        WHEN l.data_vencimento <= CURRENT_DATE + INTERVAL '7 days' THEN 'VENCE_SEMANA'
        ELSE 'A_VENCER'
    END AS status_vencimento
FROM lancamentos l
LEFT JOIN categorias c ON l.categoria_id = c.id
LEFT JOIN fornecedores f ON l.fornecedor_id = f.id
WHERE l.tipo = 'despesa'
  AND l.pago = FALSE
  AND (l.status_remessa IS NULL OR l.status_remessa NOT IN ('INCLUIDO', 'EFETUADO'))
ORDER BY l.data_vencimento ASC;

COMMENT ON VIEW v_contas_pagar_pendentes_remessa IS 'Lista de contas a pagar pendentes para inclusão em remessa';

-- ============================================================================

-- Função para obter próximo número sequencial de remessa
CREATE OR REPLACE FUNCTION obter_proximo_sequencial_remessa(p_empresa_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_proximo INTEGER;
BEGIN
    -- Atualizar e retornar próximo sequencial
    UPDATE sicredi_configuracao
    SET ultimo_sequencial_remessa = ultimo_sequencial_remessa + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE empresa_id = p_empresa_id
    RETURNING ultimo_sequencial_remessa INTO v_proximo;
    
    -- Se não existe configuração, criar
    IF v_proximo IS NULL THEN
        INSERT INTO sicredi_configuracao (empresa_id, ultimo_sequencial_remessa, created_at)
        VALUES (p_empresa_id, 1, CURRENT_TIMESTAMP)
        ON CONFLICT (empresa_id) DO UPDATE
        SET ultimo_sequencial_remessa = 1
        RETURNING ultimo_sequencial_remessa INTO v_proximo;
    END IF;
    
    RETURN v_proximo;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION obter_proximo_sequencial_remessa IS 'Obtém e incrementa número sequencial de remessa';

-- ============================================================================

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION atualizar_timestamp_remessa()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_remessa_updated_at
BEFORE UPDATE ON remessas_pagamento
FOR EACH ROW
EXECUTE FUNCTION atualizar_timestamp_remessa();

CREATE TRIGGER trigger_remessa_item_updated_at
BEFORE UPDATE ON remessas_pagamento_itens
FOR EACH ROW
EXECUTE FUNCTION atualizar_timestamp_remessa();

CREATE TRIGGER trigger_sicredi_updated_at
BEFORE UPDATE ON sicredi_configuracao
FOR EACH ROW
EXECUTE FUNCTION atualizar_timestamp_remessa();

-- ============================================================================

-- Permissões para módulo de remessa
INSERT INTO permissoes (codigo, nome, descricao, categoria, ativo)
VALUES 
    ('remessa_view', 'Ver Remessas', 'Visualizar remessas de pagamento', 'remessa', TRUE),
    ('remessa_criar', 'Criar Remessa', 'Gerar nova remessa de pagamento', 'remessa', TRUE),
    ('remessa_processar', 'Processar Retorno', 'Processar arquivo de retorno bancário', 'remessa', TRUE),
    ('remessa_excluir', 'Excluir Remessa', 'Excluir remessa (apenas não enviadas)', 'remessa', TRUE),
    ('remessa_config', 'Configurar Sicredi', 'Gerenciar configurações de convênio Sicredi', 'remessa', TRUE)
ON CONFLICT (codigo) DO NOTHING;

COMMENT ON TABLE permissoes IS 'Permissões de acesso ao sistema (atualizado com módulo remessa)';

-- ============================================================================
-- DADOS DE EXEMPLO (apenas para desenvolvimento)
-- ============================================================================

-- Configuração Sicredi exemplo (descomentar para usar)
/*
INSERT INTO sicredi_configuracao (
    empresa_id, codigo_beneficiario, codigo_convenio, agencia, conta, created_at
) VALUES (
    1, '0123456', 'CONV001', '1234', '123456789', CURRENT_TIMESTAMP
) ON CONFLICT (empresa_id) DO NOTHING;
*/

-- ============================================================================

-- Verificar estrutura criada
DO $$
BEGIN
    RAISE NOTICE '✅ Tabelas de Remessa de Pagamento criadas com sucesso';
    RAISE NOTICE '📋 Tabelas: remessas_pagamento, remessas_pagamento_itens, sicredi_configuracao';
    RAISE NOTICE '👁️ Views: v_remessas_resumo, v_contas_pagar_pendentes_remessa';
    RAISE NOTICE '⚙️ Funções: obter_proximo_sequencial_remessa()';
    RAISE NOTICE '🔐 Permissões: remessa_view, remessa_criar, remessa_processar, remessa_excluir, remessa_config';
END $$;
