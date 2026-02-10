-- Adicionar permissões de configuração de extrato aos usuários ativos
-- Data: 2026-02-10

-- 1. Garantir que as permissões existem
INSERT INTO permissoes (codigo, nome, descricao, categoria) VALUES
('config_extrato_bancario_view', 'Visualizar Configurações de Extrato', 'Permite visualizar configurações de extrato bancário', 'configuracoes'),
('config_extrato_bancario_edit', 'Editar Configurações de Extrato', 'Permite editar configurações de extrato bancário', 'configuracoes')
ON CONFLICT (codigo) DO NOTHING;

-- 2. Adicionar permissões a todos os usuários ativos que ainda não as têm
UPDATE usuario_empresas
SET permissoes_empresa = permissoes_empresa || 
    jsonb_build_array('config_extrato_bancario_view', 'config_extrato_bancario_edit')
WHERE ativo = TRUE
  AND NOT (permissoes_empresa @> '["config_extrato_bancario_view"]'::jsonb);

-- 3. Verificar quantos usuários foram atualizados
SELECT 
    COUNT(*) as usuarios_atualizados,
    'Permissões de configuração de extrato adicionadas' as mensagem
FROM usuario_empresas
WHERE ativo = TRUE
  AND permissoes_empresa @> '["config_extrato_bancario_view"]'::jsonb;
