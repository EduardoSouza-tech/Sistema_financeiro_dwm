-- =====================================================
-- SCHEMA PARA BANCO DE DADOS DA EMPRESA
-- (Sem campo empresa_id - Isolamento total)
-- =====================================================

-- Categorias
CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(10) CHECK (tipo IN ('receita', 'despesa')),
    ativa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Subcategorias
CREATE TABLE IF NOT EXISTS subcategorias (
    id SERIAL PRIMARY KEY,
    categoria_id INTEGER REFERENCES categorias(id) ON DELETE CASCADE,
    nome VARCHAR(100) NOT NULL,
    ativa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Contas Bancárias
CREATE TABLE IF NOT EXISTS contas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(50),
    banco VARCHAR(100),
    agencia VARCHAR(20),
    conta VARCHAR(30),
    saldo_inicial NUMERIC(15,2) DEFAULT 0,
    saldo_atual NUMERIC(15,2) DEFAULT 0,
    ativa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Clientes
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cpf_cnpj VARCHAR(18),
    email VARCHAR(255),
    telefone VARCHAR(20),
    endereco TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Fornecedores
CREATE TABLE IF NOT EXISTS fornecedores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cpf_cnpj VARCHAR(18),
    email VARCHAR(255),
    telefone VARCHAR(20),
    endereco TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Lançamentos
CREATE TABLE IF NOT EXISTS lancamentos (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(10) CHECK (tipo IN ('RECEITA', 'DESPESA', 'TRANSFERENCIA')),
    descricao TEXT NOT NULL,
    valor NUMERIC(15,2) NOT NULL,
    data_lancamento DATE NOT NULL,
    categoria_id INTEGER REFERENCES categorias(id),
    subcategoria_id INTEGER REFERENCES subcategorias(id),
    conta_id INTEGER REFERENCES contas(id),
    cliente_id INTEGER REFERENCES clientes(id),
    fornecedor_id INTEGER REFERENCES fornecedores(id),
    forma_pagamento VARCHAR(50),
    numero_documento VARCHAR(100),
    observacoes TEXT,
    tags TEXT,
    recorrente BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'pendente',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Contratos
CREATE TABLE IF NOT EXISTS contratos (
    id SERIAL PRIMARY KEY,
    numero VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    cliente_id INTEGER REFERENCES clientes(id),
    tipo VARCHAR(50),
    valor NUMERIC(15,2),
    valor_mensal NUMERIC(15,2),
    data_inicio DATE,
    data_fim DATE,
    quantidade_meses INTEGER,
    quantidade_parcelas INTEGER,
    horas_mensais INTEGER,
    forma_pagamento VARCHAR(50),
    dia_pagamento INTEGER,
    dia_emissao_nf INTEGER,
    imposto NUMERIC(5,2),
    comissoes JSONB,
    observacoes TEXT,
    status VARCHAR(20) DEFAULT 'ativo',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sessões de Fotografia
CREATE TABLE IF NOT EXISTS sessoes_fotografia (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255),
    data_sessao DATE NOT NULL,
    horario VARCHAR(10),
    quantidade_horas INTEGER,
    duracao INTEGER,
    endereco TEXT,
    descricao TEXT,
    contrato_id INTEGER REFERENCES contratos(id),
    cliente_id INTEGER REFERENCES clientes(id),
    tipo_foto BOOLEAN DEFAULT FALSE,
    tipo_video BOOLEAN DEFAULT FALSE,
    tipo_mobile BOOLEAN DEFAULT FALSE,
    equipamentos JSONB,
    equipamentos_alugados JSONB,
    equipe JSONB,
    responsaveis JSONB,
    custos_adicionais JSONB,
    prazo_entrega DATE,
    tags TEXT,
    observacoes TEXT,
    dados_json JSONB,
    valor NUMERIC(15,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Equipamentos
CREATE TABLE IF NOT EXISTS equipamentos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    tipo VARCHAR(100),
    marca VARCHAR(100),
    modelo VARCHAR(100),
    numero_serie VARCHAR(100),
    data_aquisicao DATE,
    valor_aquisicao NUMERIC(15,2),
    status VARCHAR(50) DEFAULT 'disponivel',
    localizacao VARCHAR(255),
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Kits de Equipamentos
CREATE TABLE IF NOT EXISTS kits_equipamentos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    equipamentos JSONB,
    valor_total NUMERIC(15,2),
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Funcionários
CREATE TABLE IF NOT EXISTS funcionarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cpf VARCHAR(14),
    cargo VARCHAR(100),
    email VARCHAR(255),
    telefone VARCHAR(20),
    data_admissao DATE,
    data_demissao DATE,
    salario NUMERIC(15,2),
    tipo_contrato VARCHAR(50),
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Folha de Pagamento
CREATE TABLE IF NOT EXISTS folha_pagamento (
    id SERIAL PRIMARY KEY,
    funcionario_id INTEGER REFERENCES funcionarios(id),
    mes_referencia VARCHAR(7),
    salario_base NUMERIC(15,2),
    horas_extras NUMERIC(15,2) DEFAULT 0,
    bonus NUMERIC(15,2) DEFAULT 0,
    descontos NUMERIC(15,2) DEFAULT 0,
    valor_liquido NUMERIC(15,2),
    data_pagamento DATE,
    status VARCHAR(20) DEFAULT 'pendente',
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Eventos
CREATE TABLE IF NOT EXISTS eventos (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    data_inicio TIMESTAMP NOT NULL,
    data_fim TIMESTAMP,
    tipo VARCHAR(50),
    local VARCHAR(255),
    participantes TEXT,
    status VARCHAR(20) DEFAULT 'confirmado',
    cor VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para Performance
CREATE INDEX idx_lancamentos_data ON lancamentos(data_lancamento);
CREATE INDEX idx_lancamentos_tipo ON lancamentos(tipo);
CREATE INDEX idx_lancamentos_categoria ON lancamentos(categoria_id);
CREATE INDEX idx_lancamentos_conta ON lancamentos(conta_id);
CREATE INDEX idx_contratos_cliente ON contratos(cliente_id);
CREATE INDEX idx_sessoes_data ON sessoes_fotografia(data_sessao);
CREATE INDEX idx_sessoes_contrato ON sessoes_fotografia(contrato_id);
CREATE INDEX idx_folha_mes ON folha_pagamento(mes_referencia);

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para updated_at
CREATE TRIGGER update_lancamentos_updated_at
    BEFORE UPDATE ON lancamentos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contratos_updated_at
    BEFORE UPDATE ON contratos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessoes_updated_at
    BEFORE UPDATE ON sessoes_fotografia
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comentários
COMMENT ON TABLE categorias IS 'Categorias de receitas e despesas';
COMMENT ON TABLE lancamentos IS 'Lançamentos financeiros (receitas, despesas, transferências)';
COMMENT ON TABLE contratos IS 'Contratos de serviços fotográficos';
COMMENT ON TABLE sessoes_fotografia IS 'Sessões de fotografia agendadas';
COMMENT ON TABLE equipamentos IS 'Equipamentos fotográficos';
COMMENT ON TABLE funcionarios IS 'Cadastro de funcionários';
COMMENT ON TABLE folha_pagamento IS 'Folha de pagamento mensal';
