-- =================================================================================
-- MIGRATION - Correção do Bug de Arrays Limitados (PARTE 11)
-- =================================================================================
-- Data: 2026-02-08
-- Problema: Funcionários, Equipes e Comissões limitados a 1 item ao editar
-- 
-- CAUSA RAIZ IDENTIFICADA:
-- - Campos JSON podem estar como TEXT ao invés de JSONB
-- - JSONB não tem limite de tamanho e tem melhor performance
-- - TEXT pode estar truncando ou tendo problemas de escape
--
-- SOLUÇÃO:
-- 1. Converter campos TEXT/JSON para JSONB
-- 2. Garantir que arrays não são truncados
-- 3. Adicionar índices GIN para performance em queries JSONB
-- =================================================================================

BEGIN;

-- =================================================================================
-- 1. VERIFICAR E CONVERTER CAMPOS PARA JSONB
-- =================================================================================

DO $$
BEGIN
    RAISE NOTICE '🔧 Iniciando correção de campos JSON...';
END $$;

-- 1.1 Tabela CONTRATOS: campo observacoes deve ser JSONB
DO $$
BEGIN
    -- Verificar tipo atual
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'contratos'
        AND column_name = 'observacoes'
        AND data_type != 'jsonb'
    ) THEN
        RAISE NOTICE '  📝 Convertendo contratos.observacoes para JSONB...';
        
        -- Converter TEXT/JSON para JSONB
        ALTER TABLE contratos 
        ALTER COLUMN observacoes TYPE JSONB USING observacoes::jsonb;
        
        RAISE NOTICE '  ✅ contratos.observacoes convertido para JSONB';
    ELSE
        RAISE NOTICE '  ℹ️  contratos.observacoes já é JSONB';
    END IF;
END $$;

-- 1.2 Tabela SESSOES: campo dados_json deve ser JSONB
DO $$
BEGIN
    -- Verificar se coluna existe
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sessoes'
        AND column_name = 'dados_json'
    ) THEN
        -- Verificar tipo atual
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'sessoes'
            AND column_name = 'dados_json'
            AND data_type != 'jsonb'
        ) THEN
            RAISE NOTICE '  📝 Convertendo sessoes.dados_json para JSONB...';
            
            ALTER TABLE sessoes 
            ALTER COLUMN dados_json TYPE JSONB USING dados_json::jsonb;
            
            RAISE NOTICE '  ✅ sessoes.dados_json convertido para JSONB';
        ELSE
            RAISE NOTICE '  ℹ️  sessoes.dados_json já é JSONB';
        END IF;
    ELSE
        RAISE NOTICE '  ⚠️  sessoes.dados_json não existe (pode ser novo schema)';
    END IF;
END $$;

-- 1.3 Tabela SESSOES: campos JSONB individuais (se existirem)
DO $$
DECLARE
    campo TEXT;
    campos_json TEXT[] := ARRAY['equipe', 'responsaveis', 'equipamentos', 'equipamentos_alugados', 'custos_adicionais'];
BEGIN
    FOREACH campo IN ARRAY campos_json
    LOOP
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'sessoes'
            AND column_name = campo  
            AND data_type != 'jsonb'
        ) THEN
            RAISE NOTICE '  📝 Convertendo sessoes.% para JSONB...', campo;
            
            EXECUTE format('ALTER TABLE sessoes ALTER COLUMN %I TYPE JSONB USING %I::jsonb', campo, campo);
            
            RAISE NOTICE '  ✅ sessoes.% convertido para JSONB', campo;
        END IF;
    END LOOP;
END $$;

-- =================================================================================
-- 2. CRIAR ÍNDICES GIN PARA PERFORMANCE EM QUERIES JSONB
-- =================================================================================

-- 2.1 Índice para queries em contratos.observacoes
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'contratos'
        AND indexname = 'idx_contratos_observacoes_gin'
    ) THEN
        RAISE NOTICE '  📊 Criando índice GIN em contratos.observacoes...';
        CREATE INDEX idx_contratos_observacoes_gin ON contratos USING GIN (observacoes);
        RAISE NOTICE '  ✅ Índice criado';
    ELSE
        RAISE NOTICE '  ℹ️  Índice contratos.observacoes já existe';
    END IF;
END $$;

-- 2.2 Índice para queries em sessoes.dados_json
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sessoes'
        AND column_name = 'dados_json'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE tablename = 'sessoes'
            AND indexname = 'idx_sessoes_dados_json_gin'
        ) THEN
            RAISE NOTICE '  📊 Criando índice GIN em sessoes.dados_json...';
            CREATE INDEX idx_sessoes_dados_json_gin ON sessoes USING GIN (dados_json);
            RAISE NOTICE '  ✅ Índice criado';
        ELSE
            RAISE NOTICE '  ℹ️  Índice sessoes.dados_json já existe';
        END IF;
    END IF;
END $$;

-- =================================================================================
-- 3. FUNÇÃO DE VALIDAÇÃO - Verificar integridade dos arrays JSON
-- =================================================================================

CREATE OR REPLACE FUNCTION validar_arrays_json()
RETURNS TABLE (
    tabela TEXT,
    registro_id INTEGER,
    campo TEXT,
    tipo_array TEXT,
    quantidade INTEGER,
    tem_bug BOOLEAN
) AS $$
BEGIN
    -- Validar comissões em contratos
    RETURN QUERY
    SELECT 
        'contratos'::TEXT as tabela,
        c.id as registro_id,
        'comissoes'::TEXT as campo,
        jsonb_typeof(c.observacoes->'comissoes')::TEXT as tipo_array,
        CASE 
            WHEN jsonb_typeof(c.observacoes->'comissoes') = 'array' 
            THEN jsonb_array_length(c.observacoes->'comissoes')
            ELSE 0
        END as quantidade,
        CASE 
            WHEN jsonb_typeof(c.observacoes->'comissoes') = 'array' 
                AND jsonb_array_length(c.observacoes->'comissoes') = 1
            THEN TRUE
            ELSE FALSE
        END as tem_bug
    FROM contratos c
    WHERE c.observacoes IS NOT NULL
    AND c.observacoes ? 'comissoes';
    
    -- Validar equipe em sessões (se dados_json existe)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sessoes'
        AND column_name = 'dados_json'
    ) THEN
        RETURN QUERY
        SELECT 
            'sessoes'::TEXT as tabela,
            s.id as registro_id,
            'equipe'::TEXT as campo,
            jsonb_typeof(s.dados_json->'equipe')::TEXT as tipo_array,
            CASE 
                WHEN jsonb_typeof(s.dados_json->'equipe') = 'array' 
                THEN jsonb_array_length(s.dados_json->'equipe')
                ELSE 0
            END as quantidade,
            CASE 
                WHEN jsonb_typeof(s.dados_json->'equipe') = 'array' 
                    AND jsonb_array_length(s.dados_json->'equipe') = 1
                THEN TRUE
                ELSE FALSE
            END as tem_bug
        FROM sessoes s
        WHERE s.dados_json IS NOT NULL
        AND s.dados_json ? 'equipe';
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION validar_arrays_json() IS 
'Valida integridade de arrays JSON em contratos e sessões. 
Retorna registros com apenas 1 item (possível bug).';

-- =================================================================================
-- 4. VIEW DE MONITORAMENTO
-- =================================================================================

CREATE OR REPLACE VIEW vw_status_arrays_json AS
SELECT 
    tabela,
    campo,
    COUNT(*) as total_registros,
    COUNT(*) FILTER (WHERE quantidade = 0) as arrays_vazios,
    COUNT(*) FILTER (WHERE quantidade = 1) as arrays_com_1_item,
    COUNT(*) FILTER (WHERE quantidade >= 2) as arrays_com_multiplos,
    ROUND(AVG(quantidade), 2) as media_itens,
    MAX(quantidade) as max_itens
FROM validar_arrays_json()
GROUP BY tabela, campo;

COMMENT ON VIEW vw_status_arrays_json IS
'View de monitoramento para identificar registros com arrays limitados.
Use para detectar quando o bug de "1 item" aparece.';

-- =================================================================================
-- 5. FUNÇÃO UTILITÁRIA - Adicionar logs de debug em operações JSON
-- =================================================================================

CREATE OR REPLACE FUNCTION log_operacao_json(
    p_tabela TEXT,
    p_registro_id INTEGER,
    p_campo TEXT,
    p_operacao TEXT,
    p_quantidade_antes INTEGER DEFAULT NULL,
    p_quantidade_depois INTEGER DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    -- Criar tabela de log se não existir
    CREATE TABLE IF NOT EXISTS log_operacoes_json (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        tabela TEXT NOT NULL,
        registro_id INTEGER NOT NULL,
        campo TEXT NOT NULL,
        operacao TEXT NOT NULL,
        quantidade_antes INTEGER,
        quantidade_depois INTEGER
    );
    
    -- Inserir log
    INSERT INTO log_operacoes_json (
        tabela, registro_id, campo, operacao,
        quantidade_antes, quantidade_depois
    )
    VALUES (
        p_tabela, p_registro_id, p_campo, p_operacao,
        p_quantidade_antes, p_quantidade_depois
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION log_operacao_json IS
'Função auxiliar para logar operações em campos JSON.
Use para rastrear quando arrays são modificados.';

-- =================================================================================
-- 6. EXECUTAR VALIDAÇÃO INICIAL
-- =================================================================================

DO $$
DECLARE
    resultado RECORD;
    total_bugs INTEGER := 0;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '🔍 EXECUTANDO VALIDAÇÃO INICIAL...';
    RAISE NOTICE '';
    
    -- Contar registros com possível bug
    FOR resultado IN 
        SELECT * FROM validar_arrays_json() WHERE tem_bug = TRUE
    LOOP
        total_bugs := total_bugs + 1;
        RAISE NOTICE '  ⚠️  Registro com apenas 1 item: %.% (ID: %)', 
            resultado.tabela, resultado.campo, resultado.registro_id;
    END LOOP;
    
    IF total_bugs > 0 THEN
        RAISE NOTICE '';
        RAISE NOTICE '  ❌ Encontrados % registros com possível bug!', total_bugs;
        RAISE NOTICE '  💡 Execute: SELECT * FROM vw_status_arrays_json;';
    ELSE
        RAISE NOTICE '  ✅ Nenhum registro com bug detectado!';
    END IF;
    
    RAISE NOTICE '';
END $$;

-- =================================================================================
-- 7. INSTRUÇÕES DE USO
-- =================================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '='.repeat(80);
    RAISE NOTICE '✅ MIGRATION APLICADA COM SUCESSO';
    RAISE NOTICE '='.repeat(80);
    RAISE NOTICE '';
    RAISE NOTICE '📋 PRÓXIMOS PASSOS:';
    RAISE NOTICE '';
    RAISE NOTICE '1. Verificar status dos arrays:';
    RAISE NOTICE '   SELECT * FROM vw_status_arrays_json;';
    RAISE NOTICE '';
    RAISE NOTICE '2. Listar registros problemáticos:';
    RAISE NOTICE '   SELECT * FROM validar_arrays_json() WHERE tem_bug = TRUE;';
    RAISE NOTICE '';
    RAISE NOTICE '3. Testar criação/edição de contratos com múltiplas comissões';
    RAISE NOTICE '';
    RAISE NOTICE '4. Monitorar logs (se necessário):';
    RAISE NOTICE '   SELECT * FROM log_operacoes_json ORDER BY timestamp DESC LIMIT 50;';
    RAISE NOTICE '';
    RAISE NOTICE '💡 CORREÇÕES APLICADAS:';
    RAISE NOTICE '   - Campos TEXT/JSON convertidos para JSONB';
    RAISE NOTICE '   - Índices GIN criados para performance';
    RAISE NOTICE '   - Funções de validação e monitoramento adicionadas';
    RAISE NOTICE '';
END $$;

COMMIT;
