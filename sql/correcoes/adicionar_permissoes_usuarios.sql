-- ============================================================================
-- SQL: Adiciona permissões de regras_conciliacao para todos os usuários
-- ============================================================================
-- Execute este SQL no Railway para dar acesso às regras de conciliação
-- ============================================================================

-- Adicionar permissões para todos os usuários ativos
INSERT INTO usuarios_permissoes (usuario_id, permissao_id)
SELECT u.id, p.id
FROM usuarios u
CROSS JOIN permissoes p
WHERE u.ativo = TRUE
  AND p.codigo IN ('regras_conciliacao_view', 'regras_conciliacao_create', 'regras_conciliacao_edit', 'regras_conciliacao_delete')
ON CONFLICT (usuario_id, permissao_id) DO NOTHING;

-- Verificar permissões adicionadas
SELECT 
    u.nome AS usuario,
    p.codigo AS permissao,
    p.nome AS descricao
FROM usuarios_permissoes up
JOIN usuarios u ON u.id = up.usuario_id
JOIN permissoes p ON p.id = up.permissao_id
WHERE p.codigo LIKE 'regras_conciliacao_%'
ORDER BY u.nome, p.codigo;
