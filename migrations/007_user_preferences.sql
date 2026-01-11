-- Migration: Tabela de Preferências do Usuário
-- Criado em: 2026-01-11
-- Descrição: Armazena preferências personalizadas dos usuários (ordem do menu, temas, configurações)

-- Criar tabela de preferências
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    preferencia_chave VARCHAR(100) NOT NULL,
    preferencia_valor TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índice único: um usuário só pode ter uma preferência por chave
    UNIQUE(usuario_id, preferencia_chave)
);

-- Criar índices para melhorar performance
CREATE INDEX idx_user_preferences_usuario_id ON user_preferences(usuario_id);
CREATE INDEX idx_user_preferences_chave ON user_preferences(preferencia_chave);

-- Comentários
COMMENT ON TABLE user_preferences IS 'Armazena preferências personalizadas dos usuários';
COMMENT ON COLUMN user_preferences.preferencia_chave IS 'Chave da preferência (ex: menu_order, theme, language)';
COMMENT ON COLUMN user_preferences.preferencia_valor IS 'Valor da preferência em formato JSON ou texto';

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_user_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_user_preferences_updated_at();

-- Inserir preferências padrão para usuário admin (exemplo)
-- A ordem padrão será: Dashboard, Financeiro, Relatórios, Cadastros, Operacional
INSERT INTO user_preferences (usuario_id, preferencia_chave, preferencia_valor)
SELECT 
    id,
    'menu_order',
    '["dashboard","financeiro","relatorios","cadastros","operacional"]'
FROM usuarios
WHERE id = 1
ON CONFLICT (usuario_id, preferencia_chave) DO NOTHING;

-- Log de sucesso
DO $$
BEGIN
    RAISE NOTICE 'Migration 007_user_preferences.sql executada com sucesso!';
END $$;
