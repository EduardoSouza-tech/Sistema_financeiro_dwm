-- Criação das tabelas para Folha de Pagamento e Eventos

-- Tabela de Funcionários
CREATE TABLE IF NOT EXISTS funcionarios (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    nome VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) NOT NULL,
    endereco TEXT,
    tipo_chave_pix VARCHAR(50) NOT NULL,
    chave_pix VARCHAR(255),
    ativo BOOLEAN DEFAULT TRUE,
    data_admissao DATE,
    data_demissao DATE,
    observacoes TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices
    CONSTRAINT uk_cpf_empresa UNIQUE (cpf, empresa_id)
);

CREATE INDEX IF NOT EXISTS idx_funcionarios_empresa ON funcionarios(empresa_id);
CREATE INDEX IF NOT EXISTS idx_funcionarios_cpf ON funcionarios(cpf);
CREATE INDEX IF NOT EXISTS idx_funcionarios_ativo ON funcionarios(ativo);

COMMENT ON TABLE funcionarios IS 'Cadastro de funcionários para folha de pagamento';
COMMENT ON COLUMN funcionarios.tipo_chave_pix IS 'Tipo: CPF, CNPJ, EMAIL, TELEFONE, ALEATORIA';

-- Tabela de Eventos
CREATE TABLE IF NOT EXISTS eventos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    nome_evento VARCHAR(255) NOT NULL,
    data_evento DATE NOT NULL,
    nf_associada VARCHAR(100),
    valor_liquido_nf DECIMAL(15, 2),
    custo_evento DECIMAL(15, 2),
    margem DECIMAL(15, 2),
    tipo_evento VARCHAR(100),
    status VARCHAR(50) DEFAULT 'PENDENTE',
    observacoes TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_eventos_empresa ON eventos(empresa_id);
CREATE INDEX IF NOT EXISTS idx_eventos_data ON eventos(data_evento);
CREATE INDEX IF NOT EXISTS idx_eventos_status ON eventos(status);
CREATE INDEX IF NOT EXISTS idx_eventos_tipo ON eventos(tipo_evento);

COMMENT ON TABLE eventos IS 'Registro de eventos operacionais com custos e margens';
COMMENT ON COLUMN eventos.margem IS 'Margem calculada: Valor Líquido - Custo';
COMMENT ON COLUMN eventos.status IS 'Status: PENDENTE, EM_ANDAMENTO, CONCLUIDO, CANCELADO';
