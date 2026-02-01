-- ================================================
-- MIGRATION: Sistema de Alocação de Funcionários em Eventos
-- Data: 2026-01-31
-- Descrição: Cria tabelas para vincular funcionários a eventos
--            com funções específicas e valores
-- ================================================

-- Tabela de funções disponíveis para eventos
CREATE TABLE IF NOT EXISTS funcoes_evento (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índice para busca rápida
CREATE INDEX IF NOT EXISTS idx_funcoes_evento_nome ON funcoes_evento(nome);
CREATE INDEX IF NOT EXISTS idx_funcoes_evento_ativo ON funcoes_evento(ativo);

-- Tabela de alocação de funcionários em eventos
CREATE TABLE IF NOT EXISTS evento_funcionarios (
    id SERIAL PRIMARY KEY,
    evento_id INTEGER NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    funcionario_id INTEGER NOT NULL REFERENCES funcionarios(id) ON DELETE CASCADE,
    funcao_id INTEGER REFERENCES funcoes_evento(id) ON DELETE SET NULL,
    funcao_nome VARCHAR(100), -- Redundância para histórico caso função seja excluída
    valor DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Evita duplicação: mesmo funcionário não pode ter mesma função no mesmo evento
    UNIQUE(evento_id, funcionario_id, funcao_id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_evento_funcionarios_evento ON evento_funcionarios(evento_id);
CREATE INDEX IF NOT EXISTS idx_evento_funcionarios_funcionario ON evento_funcionarios(funcionario_id);
CREATE INDEX IF NOT EXISTS idx_evento_funcionarios_funcao ON evento_funcionarios(funcao_id);

-- Inserir funções padrão
INSERT INTO funcoes_evento (nome, descricao) VALUES
    ('Motorista', 'Responsável pelo transporte da equipe e equipamentos'),
    ('Fotógrafo', 'Responsável pela captura de imagens do evento'),
    ('Assistente de Fotografia', 'Auxilia o fotógrafo principal'),
    ('Cinegrafista', 'Responsável pela filmagem do evento'),
    ('Editor de Vídeo', 'Responsável pela edição e pós-produção'),
    ('Editor de Fotos', 'Responsável pela edição e tratamento de imagens'),
    ('Operador de Drone', 'Responsável pela captação de imagens aéreas'),
    ('Coordenador', 'Coordena a equipe e logística do evento'),
    ('Assistente Geral', 'Apoio geral à equipe durante o evento'),
    ('Maquiador', 'Responsável pela maquiagem dos participantes'),
    ('Produtor', 'Responsável pela produção e planejamento do evento')
ON CONFLICT (nome) DO NOTHING;

-- Comentários nas tabelas
COMMENT ON TABLE funcoes_evento IS 'Funções/cargos disponíveis para alocação em eventos';
COMMENT ON TABLE evento_funcionarios IS 'Relaciona funcionários com eventos, suas funções e valores';

COMMENT ON COLUMN evento_funcionarios.funcao_nome IS 'Cópia do nome da função para manter histórico';
COMMENT ON COLUMN evento_funcionarios.valor IS 'Valor pago ao funcionário por esta função neste evento';
