-- ============================================================================
-- MIGRATION: Controle de Horas em Contratos
-- Data: 2026-02-08
-- Objetivo: Adicionar colunas para rastreamento de horas em contratos
-- ============================================================================

-- 1. ADICIONAR COLUNAS NA TABELA CONTRATOS
-- ============================================================================

ALTER TABLE contratos 
ADD COLUMN IF NOT EXISTS horas_totais DECIMAL(10,2) DEFAULT 0 COMMENT 'Total de horas contratadas (calculado ou fixo)',
ADD COLUMN IF NOT EXISTS horas_utilizadas DECIMAL(10,2) DEFAULT 0 COMMENT 'Horas já consumidas em sessões finalizadas',
ADD COLUMN IF NOT EXISTS horas_extras DECIMAL(10,2) DEFAULT 0 COMMENT 'Horas trabalhadas além do contratado',
ADD COLUMN IF NOT EXISTS controle_horas_ativo BOOLEAN DEFAULT false COMMENT 'Se o contrato tem controle de horas ativo';

COMMENT ON COLUMN contratos.horas_totais IS 'Total de horas contratadas. Para Mensal/Único: horas_mensais × qtd_meses. Para Pacote: qtd_pacotes × horas_pacote';
COMMENT ON COLUMN contratos.horas_utilizadas IS 'Horas consumidas em sessões finalizadas. Deduzido automaticamente.';
COMMENT ON COLUMN contratos.horas_extras IS 'Horas trabalhadas além do saldo. Só acumula quando horas_utilizadas > horas_totais';
COMMENT ON COLUMN contratos.controle_horas_ativo IS 'Define se o contrato tem controle de horas. Tipo Pacote sempre true.';

-- 2. ADICIONAR COLUNAS NA TABELA SESSOES
-- ============================================================================

ALTER TABLE sessoes
ADD COLUMN IF NOT EXISTS horas_trabalhadas DECIMAL(10,2) DEFAULT 0 COMMENT 'Horas efetivamente trabalhadas na sessão',
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'rascunho' COMMENT 'Status da sessão: rascunho, agendada, em_andamento, finalizada, cancelada, reaberta',
ADD COLUMN IF NOT EXISTS finalizada_em TIMESTAMP COMMENT 'Data/hora de finalização da sessão',
ADD COLUMN IF NOT EXISTS finalizada_por INTEGER REFERENCES usuarios(id) COMMENT 'Usuário que finalizou a sessão';

COMMENT ON COLUMN sessoes.horas_trabalhadas IS 'Horas trabalhadas na sessão. Usado para deduzir do contrato. Padrão = duracao se não informado.';
COMMENT ON COLUMN sessoes.status IS 'Status: rascunho (criando), agendada (confirmada), em_andamento (iniciada), finalizada (concluída), cancelada, reaberta (reabriu após finalizar)';
COMMENT ON COLUMN sessoes.finalizada_em IS 'Timestamp de quando a sessão foi marcada como finalizada';
COMMENT ON COLUMN sessoes.finalizada_por IS 'ID do usuário que finalizou a sessão';

-- 3. CRIAR ÍNDICES PARA PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_contratos_controle_horas ON contratos(controle_horas_ativo, horas_utilizadas, horas_totais);
CREATE INDEX IF NOT EXISTS idx_sessoes_status ON sessoes(status);
CREATE INDEX IF NOT EXISTS idx_sessoes_contrato_status ON sessoes(contrato_id, status);

-- 4. FUNÇÃO PARA CALCULAR HORAS TOTAIS BASEADO NO TIPO
-- ============================================================================

CREATE OR REPLACE FUNCTION calcular_horas_totais_contrato(contrato_id_param INTEGER)
RETURNS DECIMAL(10,2) AS $$
DECLARE
    obs_json JSONB;
    tipo_contrato VARCHAR(20);
    horas_mensais DECIMAL(10,2);
    qtd_meses INTEGER;
    qtd_pacotes INTEGER;
    horas_pacote DECIMAL(10,2);
    horas_calculadas DECIMAL(10,2);
BEGIN
    -- Buscar observações do contrato
    SELECT observacoes::JSONB INTO obs_json
    FROM contratos
    WHERE id = contrato_id_param;
    
    IF obs_json IS NULL THEN
        RETURN 0;
    END IF;
    
    -- Extrair dados do JSON
    tipo_contrato := obs_json->>'tipo';
    horas_mensais := COALESCE((obs_json->>'horas_mensais')::DECIMAL, 0);
    qtd_meses := COALESCE((obs_json->>'quantidade_meses')::INTEGER, 1);
    qtd_pacotes := COALESCE((obs_json->>'quantidade_meses')::INTEGER, 1); -- Reutiliza campo
    horas_pacote := COALESCE((obs_json->>'horas_mensais')::DECIMAL, 0); -- Reutiliza campo
    
    -- Calcular baseado no tipo
    IF tipo_contrato = 'Pacote' THEN
        horas_calculadas := qtd_pacotes * horas_pacote;
    ELSE
        -- Mensal ou Único
        horas_calculadas := horas_mensais * qtd_meses;
    END IF;
    
    RETURN COALESCE(horas_calculadas, 0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calcular_horas_totais_contrato(INTEGER) IS 'Calcula total de horas do contrato baseado no tipo e dados no JSON observacoes';

-- 5. FUNÇÃO PARA DEDUZIR HORAS AO FINALIZAR SESSÃO
-- ============================================================================

CREATE OR REPLACE FUNCTION deduzir_horas_sessao()
RETURNS TRIGGER AS $$
DECLARE
    horas_sessao DECIMAL(10,2);
    contrato_horas_totais DECIMAL(10,2);
    contrato_horas_utilizadas DECIMAL(10,2);
    contrato_horas_extras DECIMAL(10,2);
    saldo_atual DECIMAL(10,2);
    horas_a_utilizar DECIMAL(10,2);
    horas_a_extra DECIMAL(10,2);
BEGIN
    -- Só processar se mudou de outro status para 'finalizada'
    IF NEW.status = 'finalizada' AND (OLD.status IS NULL OR OLD.status != 'finalizada') THEN
        
        -- Pegar horas trabalhadas (se não informado, usar duracao)
        horas_sessao := COALESCE(NEW.horas_trabalhadas, NEW.duracao, 0);
        
        -- Buscar dados do contrato
        SELECT 
            horas_totais, 
            horas_utilizadas, 
            horas_extras
        INTO 
            contrato_horas_totais,
            contrato_horas_utilizadas,
            contrato_horas_extras
        FROM contratos
        WHERE id = NEW.contrato_id
          AND controle_horas_ativo = true;
        
        -- Se contrato não tem controle de horas ativo, não fazer nada
        IF NOT FOUND THEN
            RETURN NEW;
        END IF;
        
        -- Calcular saldo atual
        saldo_atual := contrato_horas_totais - contrato_horas_utilizadas;
        
        -- Se saldo suficiente, deduzir normalmente
        IF saldo_atual >= horas_sessao THEN
            horas_a_utilizar := horas_sessao;
            horas_a_extra := 0;
        ELSE
            -- Saldo insuficiente: usar o que resta e o restante vai para extras
            horas_a_utilizar := GREATEST(saldo_atual, 0);
            horas_a_extra := horas_sessao - horas_a_utilizar;
        END IF;
        
        -- Atualizar contrato
        UPDATE contratos
        SET 
            horas_utilizadas = horas_utilizadas + horas_a_utilizar,
            horas_extras = horas_extras + horas_a_extra,
            updated_at = NOW()
        WHERE id = NEW.contrato_id;
        
        RAISE NOTICE 'Sessão % finalizada: % horas trabalhadas | Saldo anterior: % | Deduzido: % | Extras: %', 
            NEW.id, horas_sessao, saldo_atual, horas_a_utilizar, horas_a_extra;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 6. CRIAR TRIGGER PARA DEDUÇÃO AUTOMÁTICA
-- ============================================================================

DROP TRIGGER IF EXISTS trigger_deduzir_horas_sessao ON sessoes;

CREATE TRIGGER trigger_deduzir_horas_sessao
AFTER INSERT OR UPDATE OF status ON sessoes
FOR EACH ROW
EXECUTE FUNCTION deduzir_horas_sessao();

COMMENT ON TRIGGER trigger_deduzir_horas_sessao ON sessoes IS 'Deduz automaticamente horas do contrato quando sessão é finalizada';

-- 7. ATUALIZAR CONTRATOS EXISTENTES COM HORAS CALCULADAS
-- ============================================================================

-- Ativar controle de horas para contratos tipo Pacote
UPDATE contratos
SET 
    controle_horas_ativo = true,
    horas_totais = calcular_horas_totais_contrato(id)
WHERE (observacoes::JSONB->>'tipo') = 'Pacote';

-- Ativar controle de horas para contratos Mensal/Único que tem horas_mensais definido
UPDATE contratos
SET 
    controle_horas_ativo = true,
    horas_totais = calcular_horas_totais_contrato(id)
WHERE (observacoes::JSONB->>'tipo') IN ('Mensal', 'Único')
  AND COALESCE((observacoes::JSONB->>'horas_mensais')::DECIMAL, 0) > 0;

-- 8. VALIDAÇÃO E ANÁLISE
-- ============================================================================

-- Verificar contratos com controle de horas ativo
SELECT 
    c.id,
    c.numero,
    c.observacoes::JSONB->>'tipo' as tipo,
    c.observacoes::JSONB->>'nome' as nome,
    c.horas_totais,
    c.horas_utilizadas,
    c.horas_extras,
    (c.horas_totais - c.horas_utilizadas) as horas_restantes,
    CASE 
        WHEN c.horas_totais > 0 THEN 
            ROUND(((c.horas_utilizadas * 100.0) / c.horas_totais), 2)
        ELSE 0 
    END as percentual_utilizado
FROM contratos c
WHERE c.controle_horas_ativo = true
ORDER BY c.id DESC
LIMIT 10;

-- Verificar sessões com status
SELECT 
    s.id,
    s.titulo,
    s.status,
    s.horas_trabalhadas,
    s.duracao,
    s.finalizada_em,
    c.numero as contrato_numero
FROM sessoes s
LEFT JOIN contratos c ON s.contrato_id = c.id
ORDER BY s.id DESC
LIMIT 10;

-- ============================================================================
-- MIGRATION COMPLETO ✅
-- ============================================================================
