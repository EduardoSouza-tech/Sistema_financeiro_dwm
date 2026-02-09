-- ============================================================================
-- MIGRATION: Cadastro de Custos Operacionais
-- Data: 2026-02-08
-- Objetivo: Criar tabela de custos padrão reutilizáveis em sessões
-- ============================================================================

-- 1. CRIAR TABELA DE CUSTOS OPERACIONAIS
-- ============================================================================

CREATE TABLE IF NOT EXISTS custos_operacionais (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    categoria VARCHAR(50) NOT NULL,  -- Transporte, Hospedagem, Alimentação, Equipamento, Outros
    valor_padrao DECIMAL(10,2) DEFAULT 0.00,
    unidade VARCHAR(30) DEFAULT 'unidade',  -- unidade, diária, km, hora
    ativo BOOLEAN DEFAULT true,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nome, empresa_id)
);

COMMENT ON TABLE custos_operacionais IS 'Custos operacionais padrão reutilizáveis em sessões';
COMMENT ON COLUMN custos_operacionais.nome IS 'Nome do custo: Uber, Hotel, Alimentação, etc';
COMMENT ON COLUMN custos_operacionais.categoria IS 'Categoria: Transporte, Hospedagem, Alimentação, Equipamento, Outros';
COMMENT ON COLUMN custos_operacionais.valor_padrao IS 'Valor padrão sugerido';
COMMENT ON COLUMN custos_operacionais.unidade IS 'Unidade de medida: unidade, diária, km, hora';
COMMENT ON COLUMN custos_operacionais.ativo IS 'Se o custo está ativo para seleção';
COMMENT ON COLUMN custos_operacionais.empresa_id IS 'ID da empresa (multi-tenancy)';

-- 2. CRIAR ÍNDICES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_custos_empresa ON custos_operacionais(empresa_id);
CREATE INDEX IF NOT EXISTS idx_custos_ativo ON custos_operacionais(ativo);
CREATE INDEX IF NOT EXISTS idx_custos_categoria ON custos_operacionais(categoria);
CREATE INDEX IF NOT EXISTS idx_custos_nome ON custos_operacionais(nome);

-- 3. INSERIR CUSTOS PADRÃO (para empresas existentes)
-- ============================================================================

INSERT INTO custos_operacionais (nome, descricao, categoria, valor_padrao, unidade, empresa_id)
SELECT 
    custo.nome,
    custo.descricao,
    custo.categoria,
    custo.valor_padrao,
    custo.unidade,
    e.id as empresa_id
FROM empresas e
CROSS JOIN (
    VALUES 
        -- Transporte
        ('Uber/Táxi', 'Transporte por aplicativo ou táxi', 'Transporte', 50.00, 'unidade'),
        ('Pedágio', 'Custo de pedágios', 'Transporte', 20.00, 'unidade'),
        ('Estacionamento', 'Estacionamento no local', 'Transporte', 30.00, 'diária'),
        ('Combustível', 'Gasolina/Diesel', 'Transporte', 6.50, 'litro'),
        
        -- Hospedagem
        ('Hotel', 'Hospedagem em hotel', 'Hospedagem', 200.00, 'diária'),
        ('Airbnb', 'Hospedagem em Airbnb', 'Hospedagem', 150.00, 'diária'),
        
        -- Alimentação
        ('Almoço Equipe', 'Almoço da equipe', 'Alimentação', 40.00, 'pessoa'),
        ('Jantar Equipe', 'Jantar da equipe', 'Alimentação', 50.00, 'pessoa'),
        ('Lanche/Coffee Break', 'Lanches e bebidas', 'Alimentação', 15.00, 'pessoa'),
        
        -- Equipamento
        ('Aluguel de Equipamento', 'Aluguel de equipamento extra', 'Equipamento', 300.00, 'diária'),
        ('Drone', 'Aluguel de drone', 'Equipamento', 500.00, 'diária'),
        ('Iluminação Extra', 'Kit de iluminação adicional', 'Equipamento', 200.00, 'diária'),
        ('Cenário/Decoração', 'Elementos de cenário', 'Equipamento', 150.00, 'unidade'),
        
        -- Outros
        ('Modelo/Figurante', 'Contratação de modelo ou figurante', 'Outros', 300.00, 'hora'),
        ('Maquiagem/Cabelo', 'Serviço de maquiagem e cabelo', 'Outros', 200.00, 'pessoa'),
        ('Autorização de Local', 'Taxa para filmagem em local', 'Outros', 500.00, 'unidade'),
        ('Seguro de Equipamento', 'Seguro para equipamentos', 'Outros', 100.00, 'diária'),
        ('Assistente Extra', 'Assistente adicional', 'Outros', 200.00, 'diária')
) AS custo(nome, descricao, categoria, valor_padrao, unidade)
ON CONFLICT (nome, empresa_id) DO NOTHING;

-- 4. TRIGGER PARA INSERIR CUSTOS PADRÃO EM NOVAS EMPRESAS
-- ============================================================================

CREATE OR REPLACE FUNCTION criar_custos_padrao_empresa()
RETURNS TRIGGER AS $$
BEGIN
    -- Inserir custos padrão para nova empresa
    INSERT INTO custos_operacionais (nome, descricao, categoria, valor_padrao, unidade, empresa_id)
    VALUES 
        -- Transporte
        ('Uber/Táxi', 'Transporte por aplicativo ou táxi', 'Transporte', 50.00, 'unidade', NEW.id),
        ('Pedágio', 'Custo de pedágios', 'Transporte', 20.00, 'unidade', NEW.id),
        ('Estacionamento', 'Estacionamento no local', 'Transporte', 30.00, 'diária', NEW.id),
        ('Combustível', 'Gasolina/Diesel', 'Transporte', 6.50, 'litro', NEW.id),
        
        -- Hospedagem
        ('Hotel', 'Hospedagem em hotel', 'Hospedagem', 200.00, 'diária', NEW.id),
        ('Airbnb', 'Hospedagem em Airbnb', 'Hospedagem', 150.00, 'diária', NEW.id),
        
        -- Alimentação
        ('Almoço Equipe', 'Almoço da equipe', 'Alimentação', 40.00, 'pessoa', NEW.id),
        ('Jantar Equipe', 'Jantar da equipe', 'Alimentação', 50.00, 'pessoa', NEW.id),
        ('Lanche/Coffee Break', 'Lanches e bebidas', 'Alimentação', 15.00, 'pessoa', NEW.id),
        
        -- Equipamento
        ('Aluguel de Equipamento', 'Aluguel de equipamento extra', 'Equipamento', 300.00, 'diária', NEW.id),
        ('Drone', 'Aluguel de drone', 'Equipamento', 500.00, 'diária', NEW.id),
        ('Iluminação Extra', 'Kit de iluminação adicional', 'Equipamento', 200.00, 'diária', NEW.id),
        ('Cenário/Decoração', 'Elementos de cenário', 'Equipamento', 150.00, 'unidade', NEW.id),
        
        -- Outros
        ('Modelo/Figurante', 'Contratação de modelo ou figurante', 'Outros', 300.00, 'hora', NEW.id),
        ('Maquiagem/Cabelo', 'Serviço de maquiagem e cabelo', 'Outros', 200.00, 'pessoa', NEW.id),
        ('Autorização de Local', 'Taxa para filmagem em local', 'Outros', 500.00, 'unidade', NEW.id),
        ('Seguro de Equipamento', 'Seguro para equipamentos', 'Outros', 100.00, 'diária', NEW.id),
        ('Assistente Extra', 'Assistente adicional', 'Outros', 200.00, 'diária', NEW.id)
    ON CONFLICT (nome, empresa_id) DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_criar_custos_padrao ON empresas;

CREATE TRIGGER trigger_criar_custos_padrao
AFTER INSERT ON empresas
FOR EACH ROW
EXECUTE FUNCTION criar_custos_padrao_empresa();

COMMENT ON TRIGGER trigger_criar_custos_padrao ON empresas IS 'Cria custos padrão automaticamente para novas empresas';

-- 5. VALIDAÇÃO E ANÁLISE
-- ============================================================================

-- Verificar custos criados por categoria
SELECT 
    e.nome as empresa,
    c.categoria,
    COUNT(c.id) as total_custos,
    COUNT(CASE WHEN c.ativo THEN 1 END) as custos_ativos
FROM empresas e
LEFT JOIN custos_operacionais c ON e.id = c.empresa_id
GROUP BY e.id, e.nome, c.categoria
ORDER BY e.nome, c.categoria;

-- Listar custos por empresa
SELECT 
    e.nome as empresa,
    c.categoria,
    c.nome as custo,
    c.valor_padrao,
    c.unidade,
    c.ativo
FROM custos_operacionais c
JOIN empresas e ON c.empresa_id = e.id
ORDER BY e.nome, c.categoria, c.nome;

-- ============================================================================
-- MIGRATION COMPLETO ✅
-- ============================================================================
