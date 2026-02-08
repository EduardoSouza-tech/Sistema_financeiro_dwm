-- ============================================================================
-- MIGRATION: Cadastro de Funções para Responsáveis
-- Data: 2026-02-08
-- Objetivo: Criar tabela de funções e integrar com sessões
-- ============================================================================

-- 1. CRIAR TABELA DE FUNÇÕES
-- ============================================================================

CREATE TABLE IF NOT EXISTS funcoes_responsaveis (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    ativa BOOLEAN DEFAULT true,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nome, empresa_id)
);

COMMENT ON TABLE funcoes_responsaveis IS 'Funções/cargos dos responsáveis por sessões (Fotógrafo, Videomaker, Editor, etc)';
COMMENT ON COLUMN funcoes_responsaveis.nome IS 'Nome da função: Fotógrafo, Videomaker, Editor, Assistente, etc';
COMMENT ON COLUMN funcoes_responsaveis.descricao IS 'Descrição opcional da função';
COMMENT ON COLUMN funcoes_responsaveis.ativa IS 'Se a função está ativa para seleção';
COMMENT ON COLUMN funcoes_responsaveis.empresa_id IS 'ID da empresa (multi-tenancy)';

-- 2. CRIAR ÍNDICES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_funcoes_empresa ON funcoes_responsaveis(empresa_id);
CREATE INDEX IF NOT EXISTS idx_funcoes_ativa ON funcoes_responsaveis(ativa);
CREATE INDEX IF NOT EXISTS idx_funcoes_nome ON funcoes_responsaveis(nome);

-- 3. INSERIR FUNÇÕES PADRÃO (para empresas existentes)
-- ============================================================================

-- Para cada empresa, inserir funções padrão
INSERT INTO funcoes_responsaveis (nome, descricao, empresa_id)
SELECT 
    funcao.nome,
    funcao.descricao,
    e.id as empresa_id
FROM empresas e
CROSS JOIN (
    VALUES 
        ('Fotógrafo', 'Responsável pela captação de fotos'),
        ('Videomaker', 'Responsável pela captação de vídeos'),
        ('Editor de Foto', 'Responsável pela edição de fotos'),
        ('Editor de Vídeo', 'Responsável pela edição de vídeos'),
        ('Assistente', 'Assistente geral de produção'),
        ('Diretor de Arte', 'Responsável pela direção artística'),
        ('Produtor', 'Responsável pela produção geral'),
        ('Cinegrafista', 'Operador de câmera para vídeo'),
        ('Colorista', 'Responsável pela colorização'),
        ('Motion Designer', 'Designer de motion graphics')
) AS funcao(nome, descricao)
ON CONFLICT (nome, empresa_id) DO NOTHING;

-- 4. TRIGGER PARA INSERIR FUNÇÕES PADRÃO EM NOVAS EMPRESAS
-- ============================================================================

CREATE OR REPLACE FUNCTION criar_funcoes_padrao_empresa()
RETURNS TRIGGER AS $$
BEGIN
    -- Inserir funções padrão para nova empresa
    INSERT INTO funcoes_responsaveis (nome, descricao, empresa_id)
    VALUES 
        ('Fotógrafo', 'Responsável pela captação de fotos', NEW.id),
        ('Videomaker', 'Responsável pela captação de vídeos', NEW.id),
        ('Editor de Foto', 'Responsável pela edição de fotos', NEW.id),
        ('Editor de Vídeo', 'Responsável pela edição de vídeos', NEW.id),
        ('Assistente', 'Assistente geral de produção', NEW.id),
        ('Diretor de Arte', 'Responsável pela direção artística', NEW.id),
        ('Produtor', 'Responsável pela produção geral', NEW.id),
        ('Cinegrafista', 'Operador de câmera para vídeo', NEW.id),
        ('Colorista', 'Responsável pela colorização', NEW.id),
        ('Motion Designer', 'Designer de motion graphics', NEW.id)
    ON CONFLICT (nome, empresa_id) DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_criar_funcoes_padrao ON empresas;

CREATE TRIGGER trigger_criar_funcoes_padrao
AFTER INSERT ON empresas
FOR EACH ROW
EXECUTE FUNCTION criar_funcoes_padrao_empresa();

COMMENT ON TRIGGER trigger_criar_funcoes_padrao ON empresas IS 'Cria funções padrão automaticamente para novas empresas';

-- 5. VALIDAÇÃO E ANÁLISE
-- ============================================================================

-- Verificar funções criadas
SELECT 
    e.nome as empresa,
    COUNT(f.id) as total_funcoes,
    COUNT(CASE WHEN f.ativa THEN 1 END) as funcoes_ativas
FROM empresas e
LEFT JOIN funcoes_responsaveis f ON e.id = f.empresa_id
GROUP BY e.id, e.nome
ORDER BY e.nome;

-- Listar funções por empresa
SELECT 
    e.nome as empresa,
    f.nome as funcao,
    f.descricao,
    f.ativa,
    f.created_at
FROM funcoes_responsaveis f
JOIN empresas e ON f.empresa_id = e.id
ORDER BY e.nome, f.nome;

-- ============================================================================
-- MIGRATION COMPLETO ✅
-- ============================================================================
