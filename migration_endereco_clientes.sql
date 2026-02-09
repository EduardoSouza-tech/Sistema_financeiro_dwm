-- ============================================
-- MIGRATION: Endereço Completo para Clientes
-- PARTE 7: Sistema de busca automática via CEP
-- ============================================
-- Descrição: Adiciona campos estruturados de endereço na tabela clientes
-- Autor: Sistema Financeiro DWM
-- Data: 2026-02-08
-- Dependências: Tabela clientes já existente
-- ============================================

-- 1️⃣ ADICIONAR CAMPOS DE ENDEREÇO ESTRUTURADOS
-- =============================================

ALTER TABLE clientes 
    ADD COLUMN IF NOT EXISTS cep VARCHAR(9),           -- CEP no formato 00000-000
    ADD COLUMN IF NOT EXISTS logradouro VARCHAR(200),   -- Rua, Av, Travessa, etc
    ADD COLUMN IF NOT EXISTS numero VARCHAR(20),        -- Número do imóvel
    ADD COLUMN IF NOT EXISTS complemento VARCHAR(100),  -- Apto, Sala, Bloco, etc
    ADD COLUMN IF NOT EXISTS bairro VARCHAR(100),       -- Bairro/Distrito
    ADD COLUMN IF NOT EXISTS cidade VARCHAR(100),       -- Cidade/Município
    ADD COLUMN IF NOT EXISTS estado VARCHAR(2);         -- UF (SP, RJ, MG, etc)

-- 📝 NOTA: O campo "endereco" TEXT existente é mantido para retrocompatibilidade
-- e pode ser usado como campo livre caso o CEP não seja preenchido

-- 2️⃣ CRIAR ÍNDICES PARA PERFORMANCE
-- ===================================

-- Índice para busca por CEP (consultas frequentes)
CREATE INDEX IF NOT EXISTS idx_clientes_cep 
    ON clientes(cep) 
    WHERE cep IS NOT NULL;

-- Índice para busca por cidade/estado (relatórios regionais)
CREATE INDEX IF NOT EXISTS idx_clientes_cidade_estado 
    ON clientes(cidade, estado) 
    WHERE cidade IS NOT NULL;

-- Índice composto para busca de clientes por empresa + cidade (multi-tenant)
CREATE INDEX IF NOT EXISTS idx_clientes_empresa_cidade 
    ON clientes(empresa_id, cidade) 
    WHERE empresa_id IS NOT NULL;

-- 3️⃣ COMENTÁRIOS PARA DOCUMENTAÇÃO
-- ==================================

COMMENT ON COLUMN clientes.cep IS 'CEP no formato 00000-000, preenchido automaticamente via API ViaCEP';
COMMENT ON COLUMN clientes.logradouro IS 'Tipo e nome da via (Rua, Avenida, Travessa, etc)';
COMMENT ON COLUMN clientes.numero IS 'Número do imóvel (pode conter letras: 123-A, S/N)';
COMMENT ON COLUMN clientes.complemento IS 'Complemento: Apartamento, Sala, Bloco, Andar, etc';
COMMENT ON COLUMN clientes.bairro IS 'Bairro, Distrito ou Região';
COMMENT ON COLUMN clientes.cidade IS 'Cidade/Município';
COMMENT ON COLUMN clientes.estado IS 'Sigla do Estado (UF) com 2 caracteres';

-- 4️⃣ VALIDAÇÃO E CONSTRAINTS
-- ============================

-- Constraint para validar formato do CEP (apenas dígitos e hífen)
ALTER TABLE clientes 
    ADD CONSTRAINT chk_cep_formato 
    CHECK (cep IS NULL OR cep ~ '^[0-9]{5}-[0-9]{3}$');

-- Constraint para validar estado (deve ser sigla válida com 2 letras)
ALTER TABLE clientes
    ADD CONSTRAINT chk_estado_valido
    CHECK (estado IS NULL OR (LENGTH(estado) = 2 AND estado ~ '^[A-Z]{2}$'));

-- 5️⃣ MIGRAÇÃO DE DADOS LEGADOS (OPCIONAL)
-- =========================================
-- Tenta extrair CEP do campo de endereço legado (se existir padrão)

DO $$
DECLARE
    total_migrado INTEGER := 0;
BEGIN
    -- Extrair CEPs no formato 00000-000 do campo "endereco" antigo
    UPDATE clientes
    SET cep = (regexp_matches(endereco, '\d{5}-\d{3}'))[1]
    WHERE endereco IS NOT NULL 
      AND endereco ~ '\d{5}-\d{3}'
      AND cep IS NULL;
    
    GET DIAGNOSTICS total_migrado = ROW_COUNT;
    
    IF total_migrado > 0 THEN
        RAISE NOTICE '✅ Migração: % CEPs extraídos do campo endereco legado', total_migrado;
    ELSE
        RAISE NOTICE 'ℹ️ Nenhum CEP encontrado no campo endereco legado para migração';
    END IF;
END $$;

-- 6️⃣ FUNÇÃO AUXILIAR: ENDEREÇO COMPLETO
-- =======================================
-- Retorna endereço formatado para exibição

CREATE OR REPLACE FUNCTION get_endereco_completo(
    p_logradouro VARCHAR,
    p_numero VARCHAR,
    p_complemento VARCHAR,
    p_bairro VARCHAR,
    p_cidade VARCHAR,
    p_estado VARCHAR,
    p_cep VARCHAR
) RETURNS TEXT AS $$
DECLARE
    v_endereco TEXT := '';
BEGIN
    -- Logradouro + Número
    IF p_logradouro IS NOT NULL THEN
        v_endereco := p_logradouro;
        IF p_numero IS NOT NULL THEN
            v_endereco := v_endereco || ', ' || p_numero;
        END IF;
    END IF;
    
    -- Complemento
    IF p_complemento IS NOT NULL THEN
        IF v_endereco = '' THEN
            v_endereco := p_complemento;
        ELSE
            v_endereco := v_endereco || ' - ' || p_complemento;
        END IF;
    END IF;
    
    -- Bairro
    IF p_bairro IS NOT NULL THEN
        IF v_endereco = '' THEN
            v_endereco := p_bairro;
        ELSE
            v_endereco := v_endereco || ' - ' || p_bairro;
        END IF;
    END IF;
    
    -- Cidade/Estado
    IF p_cidade IS NOT NULL THEN
        IF v_endereco = '' THEN
            v_endereco := p_cidade;
        ELSE
            v_endereco := v_endereco || ', ' || p_cidade;
        END IF;
        
        IF p_estado IS NOT NULL THEN
            v_endereco := v_endereco || '/' || p_estado;
        END IF;
    END IF;
    
    -- CEP
    IF p_cep IS NOT NULL THEN
        IF v_endereco = '' THEN
            v_endereco := 'CEP: ' || p_cep;
        ELSE
            v_endereco := v_endereco || ' - CEP: ' || p_cep;
        END IF;
    END IF;
    
    RETURN NULLIF(TRIM(v_endereco), '');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION get_endereco_completo IS 'Retorna endereço formatado para exibição: "Rua X, 123 - Apto 45 - Bairro Y, Cidade/UF - CEP: 00000-000"';

-- 7️⃣ VIEW: CLIENTES COM ENDEREÇO COMPLETO
-- =========================================

CREATE OR REPLACE VIEW vw_clientes_com_endereco AS
SELECT 
    c.*,
    get_endereco_completo(
        c.logradouro, 
        c.numero, 
        c.complemento, 
        c.bairro, 
        c.cidade, 
        c.estado, 
        c.cep
    ) AS endereco_completo,
    CASE 
        WHEN c.cep IS NOT NULL THEN true
        ELSE false
    END AS tem_cep
FROM clientes c;

COMMENT ON VIEW vw_clientes_com_endereco IS 'View com endereço formatado para facilitar consultas e relatórios';

-- ============================================
-- 📋 RESUMO DA MIGRATION
-- ============================================
-- ✅ 7 novos campos adicionados à tabela clientes
-- ✅ 3 índices criados para otimizar buscas
-- ✅ 2 constraints de validação (CEP e Estado)
-- ✅ 1 função auxiliar (get_endereco_completo)
-- ✅ 1 view (vw_clientes_com_endereco)
-- ✅ Migração automática de CEPs do campo legado
-- ✅ Campo "endereco" mantido para retrocompatibilidade
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '🎉 ============================================';
    RAISE NOTICE '✅ Migration: Endereço Completo - CONCLUÍDA';
    RAISE NOTICE '🎉 ============================================';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Campos adicionados:';
    RAISE NOTICE '   • cep (VARCHAR 9)';
    RAISE NOTICE '   • logradouro (VARCHAR 200)';
    RAISE NOTICE '   • numero (VARCHAR 20)';
    RAISE NOTICE '   • complemento (VARCHAR 100)';
    RAISE NOTICE '   • bairro (VARCHAR 100)';
    RAISE NOTICE '   • cidade (VARCHAR 100)';
    RAISE NOTICE '   • estado (VARCHAR 2)';
    RAISE NOTICE '';
    RAISE NOTICE '🔍 Recursos criados:';
    RAISE NOTICE '   • 3 índices de performance';
    RAISE NOTICE '   • 2 constraints de validação';
    RAISE NOTICE '   • 1 função get_endereco_completo()';
    RAISE NOTICE '   • 1 view vw_clientes_com_endereco';
    RAISE NOTICE '';
    RAISE NOTICE '🌐 Integração ViaCEP pronta!';
    RAISE NOTICE '   Digite o CEP → Campos preenchidos automaticamente';
    RAISE NOTICE '';
END $$;
