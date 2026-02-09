-- =====================================================
-- MIGRATION: INTEGRAÇÃO SESSÕES COM CONTAS A RECEBER
-- PARTE 10: Geração Automática de Lançamentos
-- =====================================================
-- 
-- Esta migration implementa:
-- 1. Coluna de vinculação sessoes.lancamento_id
-- 2. Função para gerar lançamento automaticamente
-- 3. Trigger para executar ao mudar status para 'entregue'
-- 4. View para visualizar relacionamento
-- 5. Índices de performance
-- 6. Função para estornar lançamento
--
-- Autor: Sistema Financeiro DWM
-- Data: 2026-02-08
-- =====================================================

BEGIN;

-- ============================================================================
-- 1. ADICIONAR COLUNA DE VINCULAÇÃO
-- ============================================================================

-- Adicionar coluna lancamento_id na tabela sessoes
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='sessoes' AND column_name='lancamento_id'
    ) THEN
        ALTER TABLE sessoes 
        ADD COLUMN lancamento_id INTEGER REFERENCES lancamentos(id) ON DELETE SET NULL;
        
        COMMENT ON COLUMN sessoes.lancamento_id IS 'FK para lançamento gerado automaticamente';
    END IF;
END $$;

-- Adicionar coluna para controlar geração automática
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='sessoes' AND column_name='gerar_lancamento_automatico'
    ) THEN
        ALTER TABLE sessoes 
        ADD COLUMN gerar_lancamento_automatico BOOLEAN DEFAULT TRUE;
        
        COMMENT ON COLUMN sessoes.gerar_lancamento_automatico IS 'Se TRUE, gera lançamento ao entregar';
    END IF;
END $$;

-- Adicionar coluna sessao_id em lancamentos (relacionamento bidirecional)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='lancamentos' AND column_name='sessao_id'
    ) THEN
        ALTER TABLE lancamentos 
        ADD COLUMN sessao_id INTEGER REFERENCES sessoes(id) ON DELETE SET NULL;
        
        COMMENT ON COLUMN lancamentos.sessao_id IS 'FK para sessão que originou este lançamento';
    END IF;
END $$;


-- ============================================================================
-- 2. FUNÇÃO PARA GERAR LANÇAMENTO AUTOMATICAMENTE
-- ============================================================================

CREATE OR REPLACE FUNCTION gerar_lancamento_sessao(
    p_sessao_id INTEGER,
    p_usuario_id INTEGER DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_sessao RECORD;
    v_cliente_nome VARCHAR(255);
    v_lancamento_id INTEGER;
    v_categoria_id INTEGER;
    v_descricao TEXT;
BEGIN
    -- Buscar dados da sessão
    SELECT * INTO v_sessao
    FROM sessoes
    WHERE id = p_sessao_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Sessão % não encontrada', p_sessao_id;
    END IF;
    
    -- Verificar se já tem lançamento vinculado
    IF v_sessao.lancamento_id IS NOT NULL THEN
        RAISE NOTICE 'Sessão % já possui lançamento vinculado (ID: %)', p_sessao_id, v_sessao.lancamento_id;
        RETURN v_sessao.lancamento_id;
    END IF;
    
    -- Verificar se tem valor
    IF v_sessao.valor_total IS NULL OR v_sessao.valor_total <= 0 THEN
        RAISE EXCEPTION 'Sessão % não possui valor definido', p_sessao_id;
    END IF;
    
    -- Buscar nome do cliente
    IF v_sessao.cliente_id IS NOT NULL THEN
        SELECT nome INTO v_cliente_nome FROM clientes WHERE id = v_sessao.cliente_id;
    END IF;
    
    -- Buscar ou criar categoria "Sessões de Fotografia"
    SELECT id INTO v_categoria_id
    FROM categorias
    WHERE UPPER(nome) = 'SESSÕES DE FOTOGRAFIA'
      OR UPPER(nome) = 'SESSOES DE FOTOGRAFIA'
      OR UPPER(nome) = 'SESSÕES'
      OR UPPER(nome) = 'FOTOGRAFIA'
    LIMIT 1;
    
    -- Se não encontrou, usar categoria genérica "Receitas de Serviços"
    IF v_categoria_id IS NULL THEN
        SELECT id INTO v_categoria_id
        FROM categorias
        WHERE tipo = 'receita'
          AND empresa_id = v_sessao.empresa_id
        ORDER BY id
        LIMIT 1;
    END IF;
    
    -- Montar descrição do lançamento
    v_descricao := 'Sessão: ' || COALESCE(v_sessao.titulo, 'Sem título');
    IF v_sessao.descricao IS NOT NULL THEN
        v_descricao := v_descricao || ' - ' || v_sessao.descricao;
    END IF;
    
    -- Criar lançamento
    INSERT INTO lancamentos (
        tipo,
        descricao,
        valor,
        data_vencimento,
        data_pagamento,
        categoria,
        pessoa,
        status,
        observacoes,
        sessao_id,
        created_at,
        updated_at
    ) VALUES (
        'RECEITA',
        v_descricao,
        v_sessao.valor_total,
        COALESCE(v_sessao.prazo_entrega, v_sessao.data, CURRENT_DATE),
        NULL, -- Não marcar como pago automaticamente
        (SELECT nome FROM categorias WHERE id = v_categoria_id),
        COALESCE(v_cliente_nome, 'Cliente não identificado'),
        'PENDENTE',
        'Gerado automaticamente a partir da sessão #' || p_sessao_id,
        p_sessao_id,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
    RETURNING id INTO v_lancamento_id;
    
    -- Atualizar sessão com o ID do lançamento
    UPDATE sessoes
    SET lancamento_id = v_lancamento_id,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_sessao_id;
    
    RAISE NOTICE 'Lançamento % gerado automaticamente para sessão %', v_lancamento_id, p_sessao_id;
    
    RETURN v_lancamento_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION gerar_lancamento_sessao(INTEGER, INTEGER) IS 
'Gera automaticamente um lançamento de receita a partir de uma sessão';


-- ============================================================================
-- 3. FUNÇÃO PARA ESTORNAR/REMOVER LANÇAMENTO
-- ============================================================================

CREATE OR REPLACE FUNCTION estornar_lancamento_sessao(
    p_sessao_id INTEGER,
    p_deletar BOOLEAN DEFAULT FALSE
) RETURNS BOOLEAN AS $$
DECLARE
    v_lancamento_id INTEGER;
BEGIN
    -- Buscar ID do lançamento vinculado
    SELECT lancamento_id INTO v_lancamento_id
    FROM sessoes
    WHERE id = p_sessao_id;
    
    IF v_lancamento_id IS NULL THEN
        RAISE NOTICE 'Sessão % não possui lançamento vinculado', p_sessao_id;
        RETURN FALSE;
    END IF;
    
    -- Desvincular sessão
    UPDATE sessoes
    SET lancamento_id = NULL,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_sessao_id;
    
    -- Deletar ou cancelar lançamento
    IF p_deletar THEN
        DELETE FROM lancamentos WHERE id = v_lancamento_id;
        RAISE NOTICE 'Lançamento % deletado', v_lancamento_id;
    ELSE
        UPDATE lancamentos
        SET status = 'CANCELADO',
            observacoes = COALESCE(observacoes, '') || E'\n[CANCELADO AUTOMATICAMENTE]',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = v_lancamento_id;
        RAISE NOTICE 'Lançamento % cancelado', v_lancamento_id;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION estornar_lancamento_sessao(INTEGER, BOOLEAN) IS 
'Estorna/cancela o lançamento vinculado a uma sessão';


-- ============================================================================
-- 4. TRIGGER PARA GERAÇÃO AUTOMÁTICA
-- ============================================================================

CREATE OR REPLACE FUNCTION trg_sessao_gerar_lancamento()
RETURNS TRIGGER AS $$
BEGIN
    -- Verificar se status mudou para 'entregue'
    IF NEW.status = 'entregue' AND (OLD.status IS NULL OR OLD.status != 'entregue') THEN
        
        -- Verificar se deve gerar automaticamente
        IF NEW.gerar_lancamento_automatico = TRUE THEN
            
            -- Verificar se já não tem lançamento
            IF NEW.lancamento_id IS NULL THEN
                BEGIN
                    -- Tentar gerar lançamento
                    NEW.lancamento_id := gerar_lancamento_sessao(NEW.id);
                    
                    RAISE NOTICE 'Lançamento gerado automaticamente para sessão % (status: %)', NEW.id, NEW.status;
                EXCEPTION
                    WHEN OTHERS THEN
                        -- Log do erro mas não bloqueia a atualização da sessão
                        RAISE WARNING 'Erro ao gerar lançamento automático para sessão %: %', NEW.id, SQLERRM;
                END;
            END IF;
        END IF;
    END IF;
    
    -- Se status mudou para cancelada, estornar lançamento
    IF NEW.status = 'cancelada' AND OLD.status != 'cancelada' THEN
        IF NEW.lancamento_id IS NOT NULL THEN
            PERFORM estornar_lancamento_sessao(NEW.id, FALSE);
            NEW.lancamento_id := NULL;
            RAISE NOTICE 'Lançamento estornado para sessão cancelada %', NEW.id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Criar trigger se não existir
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'trg_sessao_gerar_lancamento'
    ) THEN
        CREATE TRIGGER trg_sessao_gerar_lancamento
            BEFORE UPDATE ON sessoes
            FOR EACH ROW
            EXECUTE FUNCTION trg_sessao_gerar_lancamento();
        
        RAISE NOTICE 'Trigger trg_sessao_gerar_lancamento criado';
    END IF;
END $$;


-- ============================================================================
-- 5. VIEW PARA VISUALIZAR INTEGRAÇÃO
-- ============================================================================

CREATE OR REPLACE VIEW vw_sessoes_lancamentos AS
SELECT 
    s.id as sessao_id,
    s.titulo as sessao_titulo,
    s.data,
    s.cliente_id,
    c.nome as cliente_nome,
    s.valor_total as sessao_valor,
    s.status as sessao_status,
    s.prazo_entrega,
    s.gerar_lancamento_automatico,
    
    -- Dados do lançamento
    s.lancamento_id,
    l.tipo as lancamento_tipo,
    l.descricao as lancamento_descricao,
    l.valor as lancamento_valor,
    l.data_vencimento as lancamento_vencimento,
    l.data_pagamento as lancamento_pagamento,
    l.status as lancamento_status,
    l.categoria as lancamento_categoria,
    
    -- Análise
    CASE 
        WHEN s.lancamento_id IS NULL AND s.status = 'entregue' THEN 'SEM LANÇAMENTO'
        WHEN s.lancamento_id IS NOT NULL AND l.status = 'PAGO' THEN 'PAGO'
        WHEN s.lancamento_id IS NOT NULL AND l.status = 'PENDENTE' THEN 'A RECEBER'
        WHEN s.lancamento_id IS NOT NULL AND l.status = 'CANCELADO' THEN 'CANCELADO'
        WHEN s.status != 'entregue' THEN 'AGUARDANDO ENTREGA'
        ELSE 'INDEFINIDO'
    END as situacao,
    
    -- Timestamps
    s.created_at as sessao_criada_em,
    s.updated_at as sessao_atualizada_em,
    l.created_at as lancamento_criado_em,
    
    s.empresa_id
    
FROM sessoes s
LEFT JOIN clientes c ON s.cliente_id = c.id
LEFT JOIN lancamentos l ON s.lancamento_id = l.id
WHERE s.empresa_id IS NOT NULL
ORDER BY s.data DESC;

COMMENT ON VIEW vw_sessoes_lancamentos IS 
'View para visualizar relacionamento entre sessões e lançamentos';


-- ============================================================================
-- 6. VIEW PARA ANÁLISE FINANCEIRA
-- ============================================================================

CREATE OR REPLACE VIEW vw_sessoes_financeiro AS
SELECT 
    s.empresa_id,
    
    -- Contadores
    COUNT(*) as total_sessoes,
    COUNT(*) FILTER (WHERE s.status = 'entregue') as sessoes_entregues,
    COUNT(*) FILTER (WHERE s.lancamento_id IS NOT NULL) as sessoes_com_lancamento,
    COUNT(*) FILTER (WHERE s.status = 'entregue' AND s.lancamento_id IS NULL) as sessoes_sem_lancamento,
    
    -- Valores
    SUM(s.valor_total) FILTER (WHERE s.status = 'entregue') as valor_total_entregue,
    SUM(l.valor) FILTER (WHERE l.status = 'PAGO') as valor_ja_recebido,
    SUM(l.valor) FILTER (WHERE l.status = 'PENDENTE') as valor_a_receber,
    SUM(s.valor_total) FILTER (WHERE s.status = 'entregue' AND s.lancamento_id IS NULL) as valor_nao_lancado,
    
    -- Taxas
    ROUND(
        (COUNT(*) FILTER (WHERE s.lancamento_id IS NOT NULL)::DECIMAL / 
         NULLIF(COUNT(*) FILTER (WHERE s.status = 'entregue'), 0) * 100), 
        2
    ) as taxa_lancamento_pct,
    
    ROUND(
        (SUM(l.valor) FILTER (WHERE l.status = 'PAGO')::DECIMAL / 
         NULLIF(SUM(s.valor_total) FILTER (WHERE s.status = 'entregue'), 0) * 100), 
        2
    ) as taxa_recebimento_pct
    
FROM sessoes s
LEFT JOIN lancamentos l ON s.lancamento_id = l.id
WHERE s.empresa_id IS NOT NULL
GROUP BY s.empresa_id;

COMMENT ON VIEW vw_sessoes_financeiro IS 
'Análise financeira da integração sessões → contas a receber';


-- ============================================================================
-- 7. ÍNDICES DE PERFORMANCE
-- ============================================================================

-- Índice para buscar sessões por lançamento
CREATE INDEX IF NOT EXISTS idx_sessoes_lancamento_id 
ON sessoes(lancamento_id) 
WHERE lancamento_id IS NOT NULL;

-- Índice para buscar lançamentos por sessão
CREATE INDEX IF NOT EXISTS idx_lancamentos_sessao_id 
ON lancamentos(sessao_id) 
WHERE sessao_id IS NOT NULL;

-- Índice composto para filtros comuns
CREATE INDEX IF NOT EXISTS idx_sessoes_status_lancamento 
ON sessoes(empresa_id, status, lancamento_id);

-- Índice para gerar_lancamento_automatico
CREATE INDEX IF NOT EXISTS idx_sessoes_gerar_lancamento 
ON sessoes(gerar_lancamento_automatico) 
WHERE gerar_lancamento_automatico = TRUE;


-- ============================================================================
-- 8. COMENTÁRIOS FINAIS
-- ============================================================================

COMMENT ON COLUMN sessoes.lancamento_id IS 
'FK para o lançamento de receita gerado automaticamente ao entregar a sessão';

COMMENT ON COLUMN sessoes.gerar_lancamento_automatico IS 
'Se TRUE, trigger gera lançamento automaticamente quando status = entregue';

COMMENT ON COLUMN lancamentos.sessao_id IS 
'FK para a sessão que originou este lançamento (relacionamento bidirecional)';

COMMIT;

-- ============================================================================
-- INSTRUÇÕES DE USO
-- ============================================================================

-- 1. Geração automática (via trigger):
--    UPDATE sessoes SET status = 'entregue' WHERE id = 123;
--    → Lançamento é criado automaticamente

-- 2. Geração manual:
--    SELECT gerar_lancamento_sessao(123);

-- 3. Estornar lançamento:
--    SELECT estornar_lancamento_sessao(123, FALSE); -- Cancela
--    SELECT estornar_lancamento_sessao(123, TRUE);  -- Deleta

-- 4. Consultar situação:
--    SELECT * FROM vw_sessoes_lancamentos WHERE sessao_id = 123;

-- 5. Análise financeira geral:
--    SELECT * FROM vw_sessoes_financeiro WHERE empresa_id = 1;

-- =====================================================
-- FIM DA MIGRATION
-- =====================================================
