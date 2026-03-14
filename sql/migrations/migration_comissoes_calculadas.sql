-- ============================================
-- MIGRATION: Comissões Calculadas Automaticamente
-- PARTE 8: Sistema de cálculo automático de comissões
-- ============================================
-- Descrição: Adiciona campo valor_calculado e sistema de cálculo automático
--            baseado em valor da sessão, percentual ou valor fixo
-- Autor: Sistema Financeiro DWM
-- Data: 2026-02-08
-- Dependências: Tabela comissoes, sessoes e contratos já existentes
-- ============================================

-- 1️⃣ ADICIONAR CAMPOS PARA CÁLCULO AUTOMÁTICO
-- =============================================

ALTER TABLE comissoes 
    ADD COLUMN IF NOT EXISTS sessao_id INTEGER REFERENCES sessoes(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS valor_calculado DECIMAL(10,2),
    ADD COLUMN IF NOT EXISTS calculo_automatico BOOLEAN DEFAULT true,
    ADD COLUMN IF NOT EXISTS base_calculo VARCHAR(20) DEFAULT 'sessao';  -- 'sessao', 'contrato', 'fixo'

-- 📝 COMENTÁRIOS
COMMENT ON COLUMN comissoes.sessao_id IS 'Referência à sessão para cálculo automático';
COMMENT ON COLUMN comissoes.valor_calculado IS 'Valor calculado automaticamente (percentual × base)';
COMMENT ON COLUMN comissoes.calculo_automatico IS 'Se true, recalcula quando base muda';
COMMENT ON COLUMN comissoes.base_calculo IS 'Base: sessao (valor da sessão), contrato (valor do contrato), fixo (usar campo valor)';

-- 2️⃣ CRIAR FUNÇÃO DE CÁLCULO DE COMISSÃO
-- ========================================

CREATE OR REPLACE FUNCTION calcular_valor_comissao(
    p_comissao_id INTEGER
) RETURNS DECIMAL(10,2) AS $$
DECLARE
    v_tipo VARCHAR(20);
    v_percentual DECIMAL(5,2);
    v_valor_fixo DECIMAL(10,2);
    v_base_calculo VARCHAR(20);
    v_sessao_id INTEGER;
    v_contrato_id INTEGER;
    v_valor_base DECIMAL(10,2);
    v_resultado DECIMAL(10,2);
BEGIN
    -- Buscar dados da comissão
    SELECT tipo, percentual, valor, base_calculo, sessao_id, contrato_id
    INTO v_tipo, v_percentual, v_valor_fixo, v_base_calculo, v_sessao_id, v_contrato_id
    FROM comissoes
    WHERE id = p_comissao_id;
    
    -- Se não encontrou, retornar NULL
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    
    -- Se tipo é 'fixo' ou 'valor', retornar valor fixo
    IF v_tipo IN ('fixo', 'valor') THEN
        RETURN COALESCE(v_valor_fixo, 0);
    END IF;
    
    -- Se tipo é 'percentual', calcular baseado na base
    IF v_tipo = 'percentual' THEN
        -- Determinar valor base
        IF v_base_calculo = 'sessao' AND v_sessao_id IS NOT NULL THEN
            -- Usar valor da sessão
            SELECT COALESCE(valor_total, 0) INTO v_valor_base
            FROM sessoes
            WHERE id = v_sessao_id;
            
        ELSIF v_base_calculo = 'contrato' AND v_contrato_id IS NOT NULL THEN
            -- Usar valor do contrato
            SELECT COALESCE(valor, 0) INTO v_valor_base
            FROM contratos
            WHERE id = v_contrato_id;
            
        ELSE
            -- Sem base definida, retornar 0
            v_valor_base := 0;
        END IF;
        
        -- Calcular percentual
        v_resultado := (v_valor_base * COALESCE(v_percentual, 0)) / 100;
        RETURN ROUND(v_resultado, 2);
    END IF;
    
    -- Tipo desconhecido, retornar valor fixo ou 0
    RETURN COALESCE(v_valor_fixo, 0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calcular_valor_comissao IS 'Calcula valor da comissão baseado em tipo, percentual e base (sessão ou contrato)';

-- 3️⃣ TRIGGER PARA ATUALIZAR VALOR_CALCULADO AUTOMATICAMENTE
-- ===========================================================

CREATE OR REPLACE FUNCTION trigger_atualizar_comissao_calculada()
RETURNS TRIGGER AS $$
BEGIN
    -- Apenas se cálculo automático estiver ativo
    IF NEW.calculo_automatico IS TRUE THEN
        NEW.valor_calculado := calcular_valor_comissao(NEW.id);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger ao inserir/atualizar comissão
CREATE TRIGGER trg_comissao_calculada_insert_update
    BEFORE INSERT OR UPDATE ON comissoes
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_comissao_calculada();

COMMENT ON TRIGGER trg_comissao_calculada_insert_update ON comissoes IS 'Atualiza valor_calculado automaticamente ao inserir/atualizar comissão';

-- 4️⃣ TRIGGER PARA ATUALIZAR QUANDO SESSÃO MUDA
-- ==============================================

CREATE OR REPLACE FUNCTION trigger_atualizar_comissoes_sessao()
RETURNS TRIGGER AS $$
BEGIN
    -- Quando valor da sessão muda, recalcular comissões vinculadas
    IF (TG_OP = 'UPDATE' AND OLD.valor_total IS DISTINCT FROM NEW.valor_total)
       OR TG_OP = 'INSERT' THEN
        
        UPDATE comissoes
        SET valor_calculado = calcular_valor_comissao(id),
            updated_at = CURRENT_TIMESTAMP
        WHERE sessao_id = NEW.id
          AND calculo_automatico = true
          AND base_calculo = 'sessao';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger na tabela sessoes
DROP TRIGGER IF EXISTS trg_sessao_atualiza_comissoes ON sessoes;
CREATE TRIGGER trg_sessao_atualiza_comissoes
    AFTER INSERT OR UPDATE OF valor_total ON sessoes
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_comissoes_sessao();

COMMENT ON TRIGGER trg_sessao_atualiza_comissoes ON sessoes IS 'Recalcula comissões quando valor da sessão muda';

-- 5️⃣ TRIGGER PARA ATUALIZAR QUANDO CONTRATO MUDA
-- ================================================

CREATE OR REPLACE FUNCTION trigger_atualizar_comissoes_contrato()
RETURNS TRIGGER AS $$
BEGIN
    -- Quando valor do contrato muda, recalcular comissões vinculadas
    IF (TG_OP = 'UPDATE' AND OLD.valor IS DISTINCT FROM NEW.valor)
       OR TG_OP = 'INSERT' THEN
        
        UPDATE comissoes
        SET valor_calculado = calcular_valor_comissao(id),
            updated_at = CURRENT_TIMESTAMP
        WHERE contrato_id = NEW.id
          AND calculo_automatico = true
          AND base_calculo = 'contrato';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger na tabela contratos
DROP TRIGGER IF EXISTS trg_contrato_atualiza_comissoes ON contratos;
CREATE TRIGGER trg_contrato_atualiza_comissoes
    AFTER INSERT OR UPDATE OF valor ON contratos
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_comissoes_contrato();

COMMENT ON TRIGGER trg_contrato_atualiza_comissoes ON contratos IS 'Recalcula comissões quando valor do contrato muda';

-- 6️⃣ FUNÇÃO AUXILIAR: FORMATAR VALOR DE COMISSÃO
-- ================================================

CREATE OR REPLACE FUNCTION formatar_comissao(
    p_comissao_id INTEGER
) RETURNS TEXT AS $$
DECLARE
    v_tipo VARCHAR(20);
    v_percentual DECIMAL(5,2);
    v_valor_calculado DECIMAL(10,2);
    v_resultado TEXT;
BEGIN
    SELECT tipo, percentual, valor_calculado
    INTO v_tipo, v_percentual, v_valor_calculado
    FROM comissoes
    WHERE id = p_comissao_id;
    
    IF NOT FOUND THEN
        RETURN 'Comissão não encontrada';
    END IF;
    
    IF v_tipo = 'percentual' THEN
        v_resultado := v_percentual::TEXT || '% = R$ ' || 
                      TO_CHAR(COALESCE(v_valor_calculado, 0), 'FM999G999G999D00');
    ELSE
        v_resultado := 'R$ ' || TO_CHAR(COALESCE(v_valor_calculado, 0), 'FM999G999G999D00');
    END IF;
    
    RETURN v_resultado;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION formatar_comissao IS 'Retorna comissão formatada: "10% = R$ 150,00" ou "R$ 200,00"';

-- 7️⃣ VIEW: COMISSÕES COM VALORES CALCULADOS
-- ===========================================

CREATE OR REPLACE VIEW vw_comissoes_calculadas AS
SELECT 
    c.id,
    c.contrato_id,
    c.sessao_id,
    c.cliente_id,
    c.tipo,
    c.descricao,
    c.valor,
    c.percentual,
    c.valor_calculado,
    c.calculo_automatico,
    c.base_calculo,
    -- Informações do contrato
    ct.numero as contrato_numero,
    ct.valor as contrato_valor,
    -- Informações da sessão
    s.data as sessao_data,
    s.valor_total as sessao_valor,
    -- Informações do cliente
    cl.nome as cliente_nome,
    -- Formatação
    formatar_comissao(c.id) as comissao_formatada,
    -- Cálculos
    CASE 
        WHEN c.base_calculo = 'sessao' THEN s.valor_total
        WHEN c.base_calculo = 'contrato' THEN ct.valor
        ELSE NULL
    END as valor_base_usado,
    c.created_at,
    c.updated_at
FROM comissoes c
LEFT JOIN contratos ct ON c.contrato_id = ct.id
LEFT JOIN sessoes s ON c.sessao_id = s.id
LEFT JOIN clientes cl ON c.cliente_id = cl.id
ORDER BY c.created_at DESC;

COMMENT ON VIEW vw_comissoes_calculadas IS 'View com comissões e valores calculados automaticamente';

-- 8️⃣ ATUALIZAR COMISSÕES EXISTENTES
-- ===================================

DO $$
DECLARE
    total_atualizado INTEGER := 0;
    comissao_rec RECORD;
BEGIN
    -- Calcular valor para comissões existentes
    FOR comissao_rec IN SELECT id FROM comissoes WHERE valor_calculado IS NULL
    LOOP
        UPDATE comissoes
        SET valor_calculado = calcular_valor_comissao(comissao_rec.id)
        WHERE id = comissao_rec.id;
        
        total_atualizado := total_atualizado + 1;
    END LOOP;
    
    IF total_atualizado > 0 THEN
        RAISE NOTICE '✅ Migração: % comissões tiveram valor_calculado preenchido', total_atualizado;
    ELSE
        RAISE NOTICE 'ℹ️ Nenhuma comissão existente para atualizar';
    END IF;
END $$;

-- 9️⃣ CRIAR ÍNDICES PARA PERFORMANCE
-- ===================================

-- Índice para comissões por sessão
CREATE INDEX IF NOT EXISTS idx_comissoes_sessao 
    ON comissoes(sessao_id) 
    WHERE sessao_id IS NOT NULL;

-- Índice para comissões por contrato
CREATE INDEX IF NOT EXISTS idx_comissoes_contrato 
    ON comissoes(contrato_id) 
    WHERE contrato_id IS NOT NULL;

-- Índice para comissões calculáveis automaticamente
CREATE INDEX IF NOT EXISTS idx_comissoes_auto_calculo 
    ON comissoes(calculo_automatico, base_calculo) 
    WHERE calculo_automatico = true;

-- ============================================
-- 📋 RESUMO DA MIGRATION
-- ============================================
-- ✅ 4 novos campos adicionados à tabela comissoes
-- ✅ 1 função de cálculo (calcular_valor_comissao)
-- ✅ 1 função de formatação (formatar_comissao)
-- ✅ 3 triggers automáticos (comissão, sessão, contrato)
-- ✅ 1 view (vw_comissoes_calculadas)
-- ✅ 3 índices de performance
-- ✅ Comissões existentes atualizadas
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '🎉 ============================================';
    RAISE NOTICE '✅ Migration: Comissões Calculadas - CONCLUÍDA';
    RAISE NOTICE '🎉 ============================================';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Campos adicionados:';
    RAISE NOTICE '   • sessao_id (INTEGER) - vínculo com sessão';
    RAISE NOTICE '   • valor_calculado (DECIMAL) - valor auto-calculado';
    RAISE NOTICE '   • calculo_automatico (BOOLEAN) - ativar/desativar';
    RAISE NOTICE '   • base_calculo (VARCHAR) - sessao/contrato/fixo';
    RAISE NOTICE '';
    RAISE NOTICE '🔧 Funções criadas:';
    RAISE NOTICE '   • calcular_valor_comissao() - calcula baseado em tipo/base';
    RAISE NOTICE '   • formatar_comissao() - formata para exibição';
    RAISE NOTICE '';
    RAISE NOTICE '⚡ Triggers criados:';
    RAISE NOTICE '   • trg_comissao_calculada_insert_update';
    RAISE NOTICE '   • trg_sessao_atualiza_comissoes';
    RAISE NOTICE '   • trg_contrato_atualiza_comissoes';
    RAISE NOTICE '';
    RAISE NOTICE '🎯 Como funciona:';
    RAISE NOTICE '   1. Crie comissão com tipo=percentual e percentual=10';
    RAISE NOTICE '   2. Vincule à sessão (sessao_id) com base_calculo=sessao';
    RAISE NOTICE '   3. Quando sessão.valor_total = R$ 1.000,00';
    RAISE NOTICE '   4. valor_calculado atualiza automaticamente para R$ 100,00';
    RAISE NOTICE '   5. Mude sessão.valor_total → comissão recalcula sozinha!';
    RAISE NOTICE '';
END $$;
