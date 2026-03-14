-- ============================================================================
-- MIGRATION: Regras de Auto-Conciliação de Extratos Bancários
-- ============================================================================
-- Data: 10/02/2026
-- Descrição: Cria estrutura para configuração automática de conciliação
--            baseada em palavras-chave e integração com Folha de Pagamento
-- ============================================================================

-- 1. Criar tabela de regras de conciliação
CREATE TABLE IF NOT EXISTS regras_conciliacao (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    palavra_chave VARCHAR(255) NOT NULL,
    categoria VARCHAR(255),
    subcategoria VARCHAR(255),
    cliente_padrao VARCHAR(255),
    usa_integracao_folha BOOLEAN DEFAULT FALSE,
    descricao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_regras_conciliacao_empresa_palavra UNIQUE (empresa_id, palavra_chave)
);

-- 2. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_regras_conciliacao_empresa 
    ON regras_conciliacao(empresa_id) 
    WHERE ativo = TRUE;

CREATE INDEX IF NOT EXISTS idx_regras_conciliacao_palavra 
    ON regras_conciliacao(palavra_chave) 
    WHERE ativo = TRUE;

CREATE INDEX IF NOT EXISTS idx_regras_conciliacao_empresa_ativo 
    ON regras_conciliacao(empresa_id, ativo);

-- 3. Comentários nas colunas
COMMENT ON TABLE regras_conciliacao IS 'Regras para auto-conciliação de extratos bancários baseadas em palavras-chave';
COMMENT ON COLUMN regras_conciliacao.palavra_chave IS 'Texto a ser detectado na descrição do extrato (case-insensitive)';
COMMENT ON COLUMN regras_conciliacao.categoria IS 'Categoria a ser preenchida automaticamente';
COMMENT ON COLUMN regras_conciliacao.subcategoria IS 'Subcategoria a ser preenchida automaticamente';
COMMENT ON COLUMN regras_conciliacao.cliente_padrao IS 'Cliente/Fornecedor padrão para esta regra';
COMMENT ON COLUMN regras_conciliacao.usa_integracao_folha IS 'Se TRUE, busca CPF na descrição e vincula com funcionário da folha';
COMMENT ON COLUMN regras_conciliacao.descricao IS 'Descrição opcional da regra para referência do usuário';

-- 4. Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_regras_conciliacao_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_regras_conciliacao_timestamp
    BEFORE UPDATE ON regras_conciliacao
    FOR EACH ROW
    EXECUTE FUNCTION update_regras_conciliacao_timestamp();

-- 5. Função para buscar regras aplicáveis
CREATE OR REPLACE FUNCTION buscar_regras_aplicaveis(
    p_empresa_id INTEGER,
    p_descricao TEXT
) RETURNS TABLE (
    id INTEGER,
    palavra_chave VARCHAR,
    categoria VARCHAR,
    subcategoria VARCHAR,
    cliente_padrao VARCHAR,
    usa_integracao_folha BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.palavra_chave,
        r.categoria,
        r.subcategoria,
        r.cliente_padrao,
        r.usa_integracao_folha
    FROM regras_conciliacao r
    WHERE r.empresa_id = p_empresa_id
      AND r.ativo = TRUE
      AND UPPER(p_descricao) LIKE '%' || UPPER(r.palavra_chave) || '%'
    ORDER BY LENGTH(r.palavra_chave) DESC  -- Regras mais específicas primeiro
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION buscar_regras_aplicaveis IS 'Busca a regra mais específica aplicável a uma descrição de extrato';

-- 6. Inserir permissões
INSERT INTO permissoes (codigo, nome, descricao, categoria)
VALUES 
    ('regras_conciliacao_view', 'Visualizar Regras de Conciliação', 'Permite visualizar regras de auto-conciliação', 'Extratos'),
    ('regras_conciliacao_create', 'Criar Regras de Conciliação', 'Permite criar novas regras de auto-conciliação', 'Extratos'),
    ('regras_conciliacao_edit', 'Editar Regras de Conciliação', 'Permite editar regras de auto-conciliação', 'Extratos'),
    ('regras_conciliacao_delete', 'Excluir Regras de Conciliação', 'Permite excluir regras de auto-conciliação', 'Extratos')
ON CONFLICT (codigo) DO NOTHING;

-- 7. Dar permissões para todos os usuários ativos
INSERT INTO usuario_permissoes (usuario_id, permissao_id)
SELECT u.id, p.id
FROM usuarios u
CROSS JOIN permissoes p
WHERE u.ativo = TRUE
  AND p.codigo IN ('regras_conciliacao_view', 'regras_conciliacao_create', 'regras_conciliacao_edit', 'regras_conciliacao_delete')
ON CONFLICT (usuario_id, permissao_id) DO NOTHING;

-- 8. Exemplo de regras pré-cadastradas (opcional - comentado)
-- INSERT INTO regras_conciliacao (empresa_id, palavra_chave, categoria, subcategoria, cliente_padrao, usa_integracao_folha, descricao)
-- VALUES 
--     (1, 'RESGATE APLIC', 'RECEITAS BANCARIAS', 'RENDIMENTOS BANCARIOS', NULL, FALSE, 'Resgates de aplicações financeiras'),
--     (1, 'PAGAMENTO PIX', 'DESPESAS COM TERCEIROS', 'SERVIÇOS DE TERCEIROS TOMADOS', NULL, TRUE, 'Pagamentos PIX (integração com folha)');

-- ============================================================================
-- VERIFICAÇÃO
-- ============================================================================

-- Verificar estrutura criada
DO $$
BEGIN
    RAISE NOTICE '✅ Tabela regras_conciliacao: %', 
        (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'regras_conciliacao');
    
    RAISE NOTICE '✅ Índices criados: %',
        (SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'regras_conciliacao');
    
    RAISE NOTICE '✅ Função buscar_regras_aplicaveis: %',
        (SELECT COUNT(*) FROM pg_proc WHERE proname = 'buscar_regras_aplicaveis');
    
    RAISE NOTICE '✅ Permissões criadas: %',
        (SELECT COUNT(*) FROM permissoes WHERE codigo LIKE 'regras_conciliacao_%');
END $$;

-- ============================================================================
-- ROLLBACK (se necessário)
-- ============================================================================
-- DROP TRIGGER IF EXISTS trg_update_regras_conciliacao_timestamp ON regras_conciliacao;
-- DROP FUNCTION IF EXISTS update_regras_conciliacao_timestamp();
-- DROP FUNCTION IF EXISTS buscar_regras_aplicaveis(INTEGER, TEXT);
-- DROP TABLE IF EXISTS regras_conciliacao CASCADE;
-- DELETE FROM permissoes WHERE codigo LIKE 'regras_conciliacao_%';
