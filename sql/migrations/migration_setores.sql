-- ================================================================================
-- MIGRATION: Tabela de Setores para Eventos
-- ================================================================================
-- Data de Criação: 2026-02-01
-- Versão: 1.0
--
-- DESCRIÇÃO:
--   Cria tabela de setores para categorizar eventos operacionais
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS setores CASCADE;
-- ================================================================================

-- Tabela de setores
CREATE TABLE IF NOT EXISTS setores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_setores_nome UNIQUE (nome)
);

COMMENT ON TABLE setores IS 'Setores para categorização de eventos (Fotografia, Filmagem, Produção, etc.)';
COMMENT ON COLUMN setores.id IS 'Identificador único do setor';
COMMENT ON COLUMN setores.nome IS 'Nome do setor';
COMMENT ON COLUMN setores.ativo IS 'Se o setor está ativo para uso';
COMMENT ON COLUMN setores.created_at IS 'Data de criação do registro';
COMMENT ON COLUMN setores.updated_at IS 'Data da última atualização';

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION atualizar_setores_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_setores_updated_at
    BEFORE UPDATE ON setores
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_setores_updated_at();

-- Setores padrão
INSERT INTO setores (nome, ativo) VALUES
    ('Fotografia', TRUE),
    ('Filmagem', TRUE),
    ('Produção', TRUE),
    ('Edição', TRUE),
    ('Drone', TRUE),
    ('Som/Áudio', TRUE),
    ('Iluminação', TRUE),
    ('Transporte/Logística', TRUE)
ON CONFLICT (nome) DO NOTHING;

-- Índice para performance
CREATE INDEX IF NOT EXISTS idx_setores_ativo ON setores(ativo) WHERE ativo = TRUE;
CREATE INDEX IF NOT EXISTS idx_setores_nome ON setores(nome);
