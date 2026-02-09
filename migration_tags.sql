-- ============================================================================
-- MIGRATION: Cadastro de Tags
-- Data: 2026-02-08
-- Objetivo: Criar tabela de tags e integrar com sessões
-- ============================================================================

-- 1. CRIAR TABELA DE TAGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    cor VARCHAR(7) DEFAULT '#3b82f6',  -- Cor em hex (ex: #3b82f6)
    icone VARCHAR(50) DEFAULT 'tag',    -- Nome do ícone ou emoji
    ativa BOOLEAN DEFAULT true,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nome, empresa_id)
);

COMMENT ON TABLE tags IS 'Tags para categorização de sessões';
COMMENT ON COLUMN tags.nome IS 'Nome da tag: Urgente, VIP, Comercial, etc';
COMMENT ON COLUMN tags.cor IS 'Cor da tag em hexadecimal (#3b82f6)';
COMMENT ON COLUMN tags.icone IS 'Ícone ou emoji da tag';
COMMENT ON COLUMN tags.ativa IS 'Se a tag está ativa para seleção';
COMMENT ON COLUMN tags.empresa_id IS 'ID da empresa (multi-tenancy)';

-- 2. CRIAR TABELA DE RELACIONAMENTO SESSÃO-TAGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS sessao_tags (
    id SERIAL PRIMARY KEY,
    sessao_id INTEGER NOT NULL REFERENCES sessoes(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sessao_id, tag_id)
);

COMMENT ON TABLE sessao_tags IS 'Relacionamento muitos-para-muitos entre sessões e tags';
COMMENT ON COLUMN sessao_tags.sessao_id IS 'ID da sessão';
COMMENT ON COLUMN sessao_tags.tag_id IS 'ID da tag';

-- 3. CRIAR ÍNDICES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tags_empresa ON tags(empresa_id);
CREATE INDEX IF NOT EXISTS idx_tags_ativa ON tags(ativa);
CREATE INDEX IF NOT EXISTS idx_tags_nome ON tags(nome);
CREATE INDEX IF NOT EXISTS idx_sessao_tags_sessao ON sessao_tags(sessao_id);
CREATE INDEX IF NOT EXISTS idx_sessao_tags_tag ON sessao_tags(tag_id);

-- 4. INSERIR TAGS PADRÃO (para empresas existentes)
-- ============================================================================

INSERT INTO tags (nome, cor, icone, empresa_id)
SELECT 
    tag.nome,
    tag.cor,
    tag.icone,
    e.id as empresa_id
FROM empresas e
CROSS JOIN (
    VALUES 
        ('Urgente', '#ef4444', '🔥'),
        ('VIP', '#fbbf24', '⭐'),
        ('Comercial', '#3b82f6', '💼'),
        ('Social', '#ec4899', '🎉'),
        ('Corporativo', '#6366f1', '🏢'),
        ('Casamento', '#f472b6', '💒'),
        ('Ensaio', '#8b5cf6', '📸'),
        ('Evento', '#10b981', '🎪'),
        ('Externo', '#14b8a6', '🌍'),
        ('Estúdio', '#f59e0b', '🎬'),
        ('Delivery Rápido', '#dc2626', '⚡'),
        ('Pré-Produção', '#06b6d4', '📋'),
        ('Pós-Produção', '#84cc16', '✂️'),
        ('Aprovado Cliente', '#22c55e', '✅'),
        ('Aguardando Aprovação', '#a855f7', '⏳')
) AS tag(nome, cor, icone)
ON CONFLICT (nome, empresa_id) DO NOTHING;

-- 5. TRIGGER PARA INSERIR TAGS PADRÃO EM NOVAS EMPRESAS
-- ============================================================================

CREATE OR REPLACE FUNCTION criar_tags_padrao_empresa()
RETURNS TRIGGER AS $$
BEGIN
    -- Inserir tags padrão para nova empresa
    INSERT INTO tags (nome, cor, icone, empresa_id)
    VALUES 
        ('Urgente', '#ef4444', '🔥', NEW.id),
        ('VIP', '#fbbf24', '⭐', NEW.id),
        ('Comercial', '#3b82f6', '💼', NEW.id),
        ('Social', '#ec4899', '🎉', NEW.id),
        ('Corporativo', '#6366f1', '🏢', NEW.id),
        ('Casamento', '#f472b6', '💒', NEW.id),
        ('Ensaio', '#8b5cf6', '📸', NEW.id),
        ('Evento', '#10b981', '🎪', NEW.id),
        ('Externo', '#14b8a6', '🌍', NEW.id),
        ('Estúdio', '#f59e0b', '🎬', NEW.id),
        ('Delivery Rápido', '#dc2626', '⚡', NEW.id),
        ('Pré-Produção', '#06b6d4', '📋', NEW.id),
        ('Pós-Produção', '#84cc16', '✂️', NEW.id),
        ('Aprovado Cliente', '#22c55e', '✅', NEW.id),
        ('Aguardando Aprovação', '#a855f7', '⏳', NEW.id)
    ON CONFLICT (nome, empresa_id) DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_criar_tags_padrao ON empresas;

CREATE TRIGGER trigger_criar_tags_padrao
AFTER INSERT ON empresas
FOR EACH ROW
EXECUTE FUNCTION criar_tags_padrao_empresa();

COMMENT ON TRIGGER trigger_criar_tags_padrao ON empresas IS 'Cria tags padrão automaticamente para novas empresas';

-- 6. MIGRAR TAGS ANTIGAS DE SESSÕES (se existir coluna tags)
-- ============================================================================

DO $$
BEGIN
    -- Verificar se coluna tags existe em sessoes
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sessoes' 
        AND column_name = 'tags'
    ) THEN
        -- Migrar tags antigas (campo texto separado por vírgula)
        -- Para cada sessão com tags:
        INSERT INTO sessao_tags (sessao_id, tag_id)
        SELECT DISTINCT
            s.id as sessao_id,
            t.id as tag_id
        FROM sessoes s
        CROSS JOIN LATERAL unnest(string_to_array(s.tags, ',')) AS tag_nome
        INNER JOIN tags t ON TRIM(tag_nome) = t.nome AND t.empresa_id = s.empresa_id
        WHERE s.tags IS NOT NULL 
        AND s.tags != ''
        ON CONFLICT (sessao_id, tag_id) DO NOTHING;
        
        RAISE NOTICE 'Tags antigas migradas com sucesso';
    END IF;
END $$;

-- 7. VALIDAÇÃO E ANÁLISE
-- ============================================================================

-- Verificar tags criadas
SELECT 
    e.nome as empresa,
    COUNT(t.id) as total_tags,
    COUNT(CASE WHEN t.ativa THEN 1 END) as tags_ativas
FROM empresas e
LEFT JOIN tags t ON e.id = t.empresa_id
GROUP BY e.id, e.nome
ORDER BY e.nome;

-- Listar tags por empresa
SELECT 
    e.nome as empresa,
    t.nome as tag,
    t.cor,
    t.icone,
    t.ativa
FROM tags t
JOIN empresas e ON t.empresa_id = e.id
ORDER BY e.nome, t.nome;

-- ============================================================================
-- MIGRATION COMPLETO ✅
-- ============================================================================
