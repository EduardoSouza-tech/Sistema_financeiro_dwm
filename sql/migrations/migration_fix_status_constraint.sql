-- ============================================================================
-- MIGRATION: Fix Status Constraint na tabela sessoes
-- Data: 2026-02-22
-- Objetivo: Atualizar constraint para aceitar valor 'agendada'
-- ============================================================================

-- 1. DROPAR CONSTRAINT EXISTENTE (se existir)
-- ============================================================================

DO $$ 
BEGIN
    -- Tentar dropar a constraint se ela existir
    IF EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'sessoes_status_check' 
        AND table_name = 'sessoes'
    ) THEN
        ALTER TABLE sessoes DROP CONSTRAINT sessoes_status_check;
        RAISE NOTICE '✅ Constraint sessoes_status_check removida';
    ELSE
        RAISE NOTICE 'ℹ️ Constraint sessoes_status_check não existe, pulando DROP';
    END IF;
END $$;


-- 2. CRIAR NOVA CONSTRAINT COM VALORES CORRETOS
-- ============================================================================

ALTER TABLE sessoes 
ADD CONSTRAINT sessoes_status_check 
CHECK (status IN (
    'rascunho',      -- Criando a sessão
    'agendada',      -- Sessão confirmada/agendada ✅ NOVO VALOR
    'em_andamento',  -- Sessão iniciada
    'finalizada',    -- Sessão concluída
    'cancelada',     -- Sessão cancelada
    'reaberta'       -- Sessão reaberta após finalizar
));

COMMENT ON CONSTRAINT sessoes_status_check ON sessoes IS 
'Valores permitidos: rascunho, agendada, em_andamento, finalizada, cancelada, reaberta';


-- 3. ATUALIZAR STATUS INVÁLIDOS (se houver)
-- ============================================================================

-- Corrigir possíveis status inválidos existentes
UPDATE sessoes 
SET status = 'agendada' 
WHERE status IS NULL OR status NOT IN ('rascunho', 'agendada', 'em_andamento', 'finalizada', 'cancelada', 'reaberta');


-- 4. RECRIAR ÍNDICES (garantir performance)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_sessoes_status ON sessoes(status);
CREATE INDEX IF NOT EXISTS idx_sessoes_contrato_status ON sessoes(contrato_id, status);
CREATE INDEX IF NOT EXISTS idx_sessoes_empresa_data_status ON sessoes(empresa_id, data, status);


-- 5. VERIFICAÇÃO FINAL
-- ============================================================================

DO $$ 
DECLARE
    total_sessoes INTEGER;
    sessoes_status_counts RECORD;
BEGIN
    -- Contar total de sessões
    SELECT COUNT(*) INTO total_sessoes FROM sessoes;
    RAISE NOTICE '📊 Total de sessões na base: %', total_sessoes;
    
    -- Contar por status
    FOR sessoes_status_counts IN 
        SELECT status, COUNT(*) as qtd 
        FROM sessoes 
        GROUP BY status 
        ORDER BY qtd DESC
    LOOP
        RAISE NOTICE '   - Status "%": % sessões', sessoes_status_counts.status, sessoes_status_counts.qtd;
    END LOOP;
    
    RAISE NOTICE '✅ Migration concluída com sucesso!';
END $$;
