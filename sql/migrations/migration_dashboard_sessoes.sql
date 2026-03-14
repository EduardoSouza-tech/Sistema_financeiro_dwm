-- ============================================
-- MIGRATION: Dashboard e Relatórios de Sessões Operacionais
-- PARTE 9: Sistema completo de análise e métricas
-- ============================================
-- Descrição: Cria views, funções e índices para relatórios de sessões
-- Autor: Sistema Financeiro DWM
-- Data: 2026-02-08
-- Dependências: Tabelas sessoes, contratos, clientes, comissoes
-- ============================================

-- 1️⃣ VIEW: ESTATÍSTICAS GERAIS DE SESSÕES
-- =========================================

CREATE OR REPLACE VIEW vw_sessoes_estatisticas AS
SELECT 
    s.empresa_id,
    -- Contadores por status
    COUNT(*) FILTER (WHERE s.status = 'pendente') as total_pendentes,
    COUNT(*) FILTER (WHERE s.status = 'confirmada') as total_confirmadas,
    COUNT(*) FILTER (WHERE s.status = 'em_andamento') as total_em_andamento,
    COUNT(*) FILTER (WHERE s.status = 'concluida') as total_concluidas,
    COUNT(*) FILTER (WHERE s.status = 'entregue') as total_entregues,
    COUNT(*) FILTER (WHERE s.status = 'cancelada') as total_canceladas,
    COUNT(*) as total_geral,
    
    -- Valores financeiros
    SUM(s.valor_total) FILTER (WHERE s.status NOT IN ('cancelada')) as valor_total_ativo,
    SUM(s.valor_total) FILTER (WHERE s.status = 'concluida') as valor_concluido,
    SUM(s.valor_total) FILTER (WHERE s.status = 'entregue') as valor_entregue,
    AVG(s.valor_total) FILTER (WHERE s.status NOT IN ('cancelada')) as ticket_medio,
    
    -- Horas trabalhadas
    SUM(s.quantidade_horas) FILTER (WHERE s.status NOT IN ('cancelada')) as total_horas,
    AVG(s.quantidade_horas) FILTER (WHERE s.status NOT IN ('cancelada')) as media_horas,
    
    -- Prazos
    AVG(
        CASE 
            WHEN s.prazo_entrega IS NOT NULL AND s.data IS NOT NULL 
            THEN EXTRACT(DAY FROM (s.prazo_entrega - s.data))
            ELSE NULL 
        END
    ) as prazo_medio_dias,
    
    -- Por tipo de captação
    COUNT(*) FILTER (WHERE s.tipo_foto) as total_com_foto,
    COUNT(*) FILTER (WHERE s.tipo_video) as total_com_video,
    COUNT(*) FILTER (WHERE s.tipo_mobile) as total_com_mobile
FROM sessoes s
GROUP BY s.empresa_id;

COMMENT ON VIEW vw_sessoes_estatisticas IS 'Estatísticas gerais de sessões por empresa (contadores, valores, horas, prazos)';

-- 2️⃣ VIEW: SESSÕES POR PERÍODO
-- ==============================

CREATE OR REPLACE VIEW vw_sessoes_por_periodo AS
SELECT 
    s.empresa_id,
    DATE_TRUNC('month', s.data) as mes,
    DATE_TRUNC('week', s.data) as semana,
    DATE_TRUNC('day', s.data) as dia,
    
    COUNT(*) as total_sessoes,
    COUNT(*) FILTER (WHERE s.status = 'concluida' OR s.status = 'entregue') as sessoes_finalizadas,
    SUM(s.valor_total) as faturamento_bruto,
    SUM(s.valor_total) FILTER (WHERE s.status = 'entregue') as faturamento_entregue,
    AVG(s.valor_total) as ticket_medio,
    SUM(s.quantidade_horas) as horas_trabalhadas
FROM sessoes s
WHERE s.status NOT IN ('cancelada')
GROUP BY s.empresa_id, mes, semana, dia;

COMMENT ON VIEW vw_sessoes_por_periodo IS 'Métricas de sessões agregadas por mês, semana e dia';

-- 3️⃣ VIEW: TOP CLIENTES
-- =======================

CREATE OR REPLACE VIEW vw_top_clientes_sessoes AS
SELECT 
    s.empresa_id,
    s.cliente_id,
    c.nome as cliente_nome,
    c.razao_social as cliente_razao_social,
    
    COUNT(*) as total_sessoes,
    COUNT(*) FILTER (WHERE s.status = 'entregue') as sessoes_entregues,
    SUM(s.valor_total) as valor_total,
    AVG(s.valor_total) as ticket_medio,
    SUM(s.quantidade_horas) as total_horas,
    
    MAX(s.data) as ultima_sessao,
    MIN(s.data) as primeira_sessao,
    
    -- Taxa de conclusão
    ROUND(
        (COUNT(*) FILTER (WHERE s.status IN ('concluida', 'entregue'))::DECIMAL / 
        NULLIF(COUNT(*), 0) * 100), 
        2
    ) as taxa_conclusao_pct
FROM sessoes s
INNER JOIN clientes c ON s.cliente_id = c.id
WHERE s.status NOT IN ('cancelada')
GROUP BY s.empresa_id, s.cliente_id, c.nome, c.razao_social
ORDER BY valor_total DESC;

COMMENT ON VIEW vw_top_clientes_sessoes IS 'Ranking de clientes por faturamento e volume de sessões';

-- 4️⃣ VIEW: COMISSÕES POR SESSÃO
-- ===============================

CREATE OR REPLACE VIEW vw_comissoes_por_sessao AS
SELECT 
    s.empresa_id,
    s.id as sessao_id,
    s.data as sessao_data,
    s.valor_total as sessao_valor,
    s.cliente_id,
    c.nome as cliente_nome,
    
    COUNT(com.id) as total_comissoes,
    SUM(com.valor_calculado) as total_comissoes_valor,
    
    -- Percentual de comissões sobre valor da sessão
    ROUND(
        (SUM(com.valor_calculado) / NULLIF(s.valor_total, 0) * 100), 
        2
    ) as comissoes_pct,
    
    -- Lucro líquido (valor - comissões)
    (s.valor_total - COALESCE(SUM(com.valor_calculado), 0)) as lucro_liquido
FROM sessoes s
LEFT JOIN comissoes com ON s.id = com.sessao_id
LEFT JOIN clientes c ON s.cliente_id = c.id
WHERE s.status NOT IN ('cancelada')
GROUP BY s.empresa_id, s.id, s.data, s.valor_total, s.cliente_id, c.nome;

COMMENT ON VIEW vw_comissoes_por_sessao IS 'Análise de comissões e margem de lucro por sessão';

-- 5️⃣ VIEW: SESSÕES PRÓXIMAS AO PRAZO
-- ====================================

CREATE OR REPLACE VIEW vw_sessoes_atencao AS
SELECT 
    s.empresa_id,
    s.id,
    s.data,
    s.prazo_entrega,
    s.status,
    s.cliente_id,
    c.nome as cliente_nome,
    s.descricao,
    s.valor_total,
    
    -- Dias até o prazo
    EXTRACT(DAY FROM (s.prazo_entrega - CURRENT_DATE))::INTEGER as dias_ate_prazo,
    
    -- Classificação de urgência
    CASE 
        WHEN s.prazo_entrega < CURRENT_DATE THEN 'ATRASADO'
        WHEN s.prazo_entrega = CURRENT_DATE THEN 'URGENTE - HOJE'
        WHEN EXTRACT(DAY FROM (s.prazo_entrega - CURRENT_DATE)) <= 3 THEN 'URGENTE - 3 DIAS'
        WHEN EXTRACT(DAY FROM (s.prazo_entrega - CURRENT_DATE)) <= 7 THEN 'ATENÇÃO - 1 SEMANA'
        ELSE 'NO PRAZO'
    END as urgencia
FROM sessoes s
INNER JOIN clientes c ON s.cliente_id = c.id
WHERE s.status IN ('confirmada', 'em_andamento', 'concluida')
  AND s.prazo_entrega IS NOT NULL
ORDER BY s.prazo_entrega ASC;

COMMENT ON VIEW vw_sessoes_atencao IS 'Sessões que requerem atenção por prazo (atrasadas, urgentes, próximas)';

-- 6️⃣ FUNÇÃO: ESTATÍSTICAS POR PERÍODO CUSTOMIZADO
-- =================================================

CREATE OR REPLACE FUNCTION obter_estatisticas_periodo(
    p_empresa_id INTEGER,
    p_data_inicio DATE,
    p_data_fim DATE
) RETURNS TABLE (
    total_sessoes BIGINT,
    sessoes_concluidas BIGINT,
    sessoes_canceladas BIGINT,
    taxa_conclusao NUMERIC,
    faturamento_total NUMERIC,
    faturamento_entregue NUMERIC,
    comissoes_total NUMERIC,
    lucro_liquido NUMERIC,
    ticket_medio NUMERIC,
    horas_trabalhadas NUMERIC,
    clientes_unicos BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_sessoes,
        COUNT(*) FILTER (WHERE s.status IN ('concluida', 'entregue'))::BIGINT as sessoes_concluidas,
        COUNT(*) FILTER (WHERE s.status = 'cancelada')::BIGINT as sessoes_canceladas,
        ROUND(
            (COUNT(*) FILTER (WHERE s.status IN ('concluida', 'entregue'))::DECIMAL / 
            NULLIF(COUNT(*), 0) * 100), 
            2
        ) as taxa_conclusao,
        
        COALESCE(SUM(s.valor_total), 0)::NUMERIC as faturamento_total,
        COALESCE(SUM(s.valor_total) FILTER (WHERE s.status = 'entregue'), 0)::NUMERIC as faturamento_entregue,
        COALESCE(SUM(com.valor_calculado), 0)::NUMERIC as comissoes_total,
        COALESCE(SUM(s.valor_total), 0) - COALESCE(SUM(com.valor_calculado), 0) as lucro_liquido,
        COALESCE(AVG(s.valor_total), 0)::NUMERIC as ticket_medio,
        COALESCE(SUM(s.quantidade_horas), 0)::NUMERIC as horas_trabalhadas,
        COUNT(DISTINCT s.cliente_id)::BIGINT as clientes_unicos
    FROM sessoes s
    LEFT JOIN comissoes com ON s.id = com.sessao_id AND com.calculo_automatico = true
    WHERE s.empresa_id = p_empresa_id
      AND s.data BETWEEN p_data_inicio AND p_data_fim;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION obter_estatisticas_periodo IS 'Retorna estatísticas detalhadas de sessões para período customizado';

-- 7️⃣ FUNÇÃO: COMPARATIVO ENTRE PERÍODOS
-- =======================================

CREATE OR REPLACE FUNCTION comparativo_periodos(
    p_empresa_id INTEGER,
    p_periodo1_inicio DATE,
    p_periodo1_fim DATE,
    p_periodo2_inicio DATE,
    p_periodo2_fim DATE
) RETURNS TABLE (
    metrica TEXT,
    periodo1_valor NUMERIC,
    periodo2_valor NUMERIC,
    variacao_absoluta NUMERIC,
    variacao_percentual NUMERIC
) AS $$
DECLARE
    p1_sessoes BIGINT;
    p2_sessoes BIGINT;
    p1_faturamento NUMERIC;
    p2_faturamento NUMERIC;
    p1_horas NUMERIC;
    p2_horas NUMERIC;
    p1_ticket NUMERIC;
    p2_ticket NUMERIC;
BEGIN
    -- Período 1
    SELECT 
        COUNT(*),
        COALESCE(SUM(s.valor_total), 0),
        COALESCE(SUM(s.quantidade_horas), 0),
        COALESCE(AVG(s.valor_total), 0)
    INTO p1_sessoes, p1_faturamento, p1_horas, p1_ticket
    FROM sessoes s
    WHERE s.empresa_id = p_empresa_id
      AND s.data BETWEEN p_periodo1_inicio AND p_periodo1_fim
      AND s.status NOT IN ('cancelada');
    
    -- Período 2
    SELECT 
        COUNT(*),
        COALESCE(SUM(s.valor_total), 0),
        COALESCE(SUM(s.quantidade_horas), 0),
        COALESCE(AVG(s.valor_total), 0)
    INTO p2_sessoes, p2_faturamento, p2_horas, p2_ticket
    FROM sessoes s
    WHERE s.empresa_id = p_empresa_id
      AND s.data BETWEEN p_periodo2_inicio AND p_periodo2_fim
      AND s.status NOT IN ('cancelada');
    
    -- Retornar métricas com variações
    RETURN QUERY
    SELECT 
        'Total de Sessões'::TEXT,
        p1_sessoes::NUMERIC,
        p2_sessoes::NUMERIC,
        (p2_sessoes - p1_sessoes)::NUMERIC,
        CASE WHEN p1_sessoes > 0 
            THEN ROUND((p2_sessoes - p1_sessoes)::DECIMAL / p1_sessoes * 100, 2)
            ELSE NULL 
        END
    UNION ALL
    SELECT 
        'Faturamento Total'::TEXT,
        p1_faturamento,
        p2_faturamento,
        (p2_faturamento - p1_faturamento),
        CASE WHEN p1_faturamento > 0 
            THEN ROUND((p2_faturamento - p1_faturamento) / p1_faturamento * 100, 2)
            ELSE NULL 
        END
    UNION ALL
    SELECT 
        'Horas Trabalhadas'::TEXT,
        p1_horas,
        p2_horas,
        (p2_horas - p1_horas),
        CASE WHEN p1_horas > 0 
            THEN ROUND((p2_horas - p1_horas) / p1_horas * 100, 2)
            ELSE NULL 
        END
    UNION ALL
    SELECT 
        'Ticket Médio'::TEXT,
        p1_ticket,
        p2_ticket,
        (p2_ticket - p1_ticket),
        CASE WHEN p1_ticket > 0 
            THEN ROUND((p2_ticket - p1_ticket) / p1_ticket * 100, 2)
            ELSE NULL 
        END;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION comparativo_periodos IS 'Compara métricas entre dois períodos com cálculo de variação percentual';

-- 8️⃣ ÍNDICES PARA PERFORMANCE DE RELATÓRIOS
-- ===========================================

-- Índice composto para queries de período
CREATE INDEX IF NOT EXISTS idx_sessoes_empresa_data_status 
    ON sessoes(empresa_id, data, status);

-- Índice para relatórios de cliente
CREATE INDEX IF NOT EXISTS idx_sessoes_cliente_data 
    ON sessoes(cliente_id, data) 
    WHERE status NOT IN ('cancelada');

-- Índice para sessões próximas ao prazo
CREATE INDEX IF NOT EXISTS idx_sessoes_prazo_status 
    ON sessoes(prazo_entrega, status) 
    WHERE prazo_entrega IS NOT NULL 
      AND status IN ('confirmada', 'em_andamento', 'concluida');

-- Índice para análise de comissões
CREATE INDEX IF NOT EXISTS idx_comissoes_sessao_empresa 
    ON comissoes(sessao_id, empresa_id) 
    WHERE sessao_id IS NOT NULL;

-- ============================================
-- 📋 RESUMO DA MIGRATION
-- ============================================
-- ✅ 5 views criadas (estatísticas gerais, por período, top clientes, comissões, atenção)
-- ✅ 2 funções criadas (estatísticas período, comparativo períodos)
-- ✅ 4 índices criados para otimizar consultas de relatórios
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '🎉 ============================================';
    RAISE NOTICE '✅ Migration: Dashboard Sessões - CONCLUÍDA';
    RAISE NOTICE '🎉 ============================================';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Views criadas:';
    RAISE NOTICE '   • vw_sessoes_estatisticas - métricas gerais';
    RAISE NOTICE '   • vw_sessoes_por_periodo - análise temporal';
   RAISE NOTICE '   • vw_top_clientes_sessoes - ranking de clientes';
    RAISE NOTICE '   • vw_comissoes_por_sessao - análise de margem';
    RAISE NOTICE '   • vw_sessoes_atencao - alertas de prazo';
    RAISE NOTICE '';
    RAISE NOTICE '🔧 Funções criadas:';
    RAISE NOTICE '   • obter_estatisticas_periodo() - métricas customizadas';
    RAISE NOTICE '   • comparativo_periodos() - análise de crescimento';
    RAISE NOTICE '';
    RAISE NOTICE '⚡ 4 índices criados para performance';
    RAISE NOTICE '';
    RAISE NOTICE '🎯 Próximos passos:';
    RAISE NOTICE '   1. Criar endpoint GET /api/sessoes/dashboard';
    RAISE NOTICE '   2. Implementar frontend com gráficos';
    RAISE NOTICE '   3. Adicionar filtros de período';
    RAISE NOTICE '';
END $$;
