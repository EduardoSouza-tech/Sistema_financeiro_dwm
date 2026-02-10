-- ============================================================================
-- MIGRATION: Configuração Global de Integração com Folha de Pagamento
-- ============================================================================
-- Criado em: 2026-02-10
-- Descrição: Move integração de folha das regras para configuração global

-- 1. Criar tabela de configurações de extrato bancário por empresa
CREATE TABLE IF NOT EXISTS config_extrato_bancario (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    integrar_folha_pagamento BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(empresa_id)
);

-- 2. Inserir configurações padrão para empresas existentes
INSERT INTO config_extrato_bancario (empresa_id, integrar_folha_pagamento)
SELECT id, FALSE FROM empresas
ON CONFLICT (empresa_id) DO NOTHING;

-- 3. Remover coluna usa_integracao_folha da tabela regras_conciliacao
ALTER TABLE regras_conciliacao 
DROP COLUMN IF EXISTS usa_integracao_folha;

-- 4. Criar índice para performance
CREATE INDEX IF NOT EXISTS idx_config_extrato_empresa 
ON config_extrato_bancario(empresa_id);

-- 5. Permissões para configuração de extrato
INSERT INTO permissoes (codigo, nome, descricao, categoria) VALUES
('config_extrato_bancario_view', 'Visualizar Configurações de Extrato', 'Permite visualizar configurações de extrato bancário', 'configuracoes'),
('config_extrato_bancario_edit', 'Editar Configurações de Extrato', 'Permite editar configurações de extrato bancário', 'configuracoes')
ON CONFLICT (codigo) DO NOTHING;

-- 6. Adicionar permissões a todos os usuários ativos
UPDATE usuario_empresas
SET permissoes_empresa = permissoes_empresa || 
    jsonb_build_array('config_extrato_bancario_view', 'config_extrato_bancario_edit')
WHERE ativo = TRUE
  AND NOT (permissoes_empresa @> '["config_extrato_bancario_view"]'::jsonb);

COMMENT ON TABLE config_extrato_bancario IS 'Configurações de extrato bancário por empresa';
COMMENT ON COLUMN config_extrato_bancario.integrar_folha_pagamento IS 'Se TRUE, detecta CPF em extratos e busca funcionário automaticamente';
