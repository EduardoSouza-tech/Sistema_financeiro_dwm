-- ============================================================================
-- MIGRAÇÃO: Adicionar constraint UNIQUE em cpf_cnpj
-- ============================================================================
-- Objetivo: Garantir que não haja CPF/CNPJ duplicados no banco de dados
-- Data: 2026-02-24
-- ============================================================================

-- 1. VERIFICAR DUPLICADOS EXISTENTES (antes de adicionar constraint)
-- ============================================================================

DO $$
DECLARE
    v_duplicados_clientes INTEGER;
    v_duplicados_fornecedores INTEGER;
BEGIN
    -- Contar duplicados em clientes
    SELECT COUNT(*) INTO v_duplicados_clientes
    FROM (
        SELECT cpf_cnpj, COUNT(*) as qtd
        FROM clientes
        WHERE cpf_cnpj IS NOT NULL AND cpf_cnpj != ''
        GROUP BY cpf_cnpj
        HAVING COUNT(*) > 1
    ) duplicados;
    
    -- Contar duplicados em fornecedores
    SELECT COUNT(*) INTO v_duplicados_fornecedores
    FROM (
        SELECT cpf_cnpj, COUNT(*) as qtd
        FROM fornecedores
        WHERE cpf_cnpj IS NOT NULL AND cpf_cnpj != ''
        GROUP BY cpf_cnpj
        HAVING COUNT(*) > 1
    ) duplicados;
    
    -- Exibir resultado
    RAISE NOTICE '==================================================';
    RAISE NOTICE 'VERIFICAÇÃO DE CPF/CNPJ DUPLICADOS';
    RAISE NOTICE '==================================================';
    RAISE NOTICE 'Clientes com CPF/CNPJ duplicados: %', v_duplicados_clientes;
    RAISE NOTICE 'Fornecedores com CPF/CNPJ duplicados: %', v_duplicados_fornecedores;
    
    IF v_duplicados_clientes > 0 OR v_duplicados_fornecedores > 0 THEN
        RAISE NOTICE '';
        RAISE NOTICE '⚠️  ATENÇÃO: Existem registros duplicados!';
        RAISE NOTICE '⚠️  Execute as queries abaixo para visualizar:';
    END IF;
END $$;

-- Query para visualizar duplicados em CLIENTES (se houver)
-- EXECUTE MANUALMENTE se a verificação acima indicar duplicados:
/*
SELECT 
    cpf_cnpj,
    COUNT(*) as quantidade,
    STRING_AGG(id::text || ' - ' || nome, ', ') as registros
FROM clientes
WHERE cpf_cnpj IS NOT NULL AND cpf_cnpj != ''
GROUP BY cpf_cnpj
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC;
*/

-- Query para visualizar duplicados em FORNECEDORES (se houver)
-- EXECUTE MANUALMENTE se a verificação acima indicar duplicados:
/*
SELECT 
    cpf_cnpj,
    COUNT(*) as quantidade,
    STRING_AGG(id::text || ' - ' || nome, ', ') as registros
FROM fornecedores
WHERE cpf_cnpj IS NOT NULL AND cpf_cnpj != ''
GROUP BY cpf_cnpj
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC;
*/


-- 2. RESOLVER DUPLICADOS (se houver)
-- ============================================================================
-- IMPORTANTE: Execute manualmente apenas SE houver duplicados
-- Escolha qual registro manter (normalmente o mais antigo - menor ID)
-- ============================================================================

/*
-- Template para remover duplicados em CLIENTES
-- Ajuste conforme necessário após analisar os registros duplicados

-- Exemplo: Manter o registro com menor ID (mais antigo)
DELETE FROM clientes
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (PARTITION BY cpf_cnpj ORDER BY id ASC) as rn
        FROM clientes
        WHERE cpf_cnpj IS NOT NULL AND cpf_cnpj != ''
    ) t
    WHERE rn > 1
);

-- Template para remover duplicados em FORNECEDORES
DELETE FROM fornecedores
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (PARTITION BY cpf_cnpj ORDER BY id ASC) as rn
        FROM fornecedores
        WHERE cpf_cnpj IS NOT NULL AND cpf_cnpj != ''
    ) t
    WHERE rn > 1
);
*/


-- 3. ADICIONAR CONSTRAINT UNIQUE (apenas se não existir duplicados)
-- ============================================================================

DO $$
BEGIN
    -- Adicionar UNIQUE em clientes.cpf_cnpj (se não existir)
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'clientes_cpf_cnpj_key' 
        AND conrelid = 'clientes'::regclass
    ) THEN
        ALTER TABLE clientes 
        ADD CONSTRAINT clientes_cpf_cnpj_key UNIQUE (cpf_cnpj);
        RAISE NOTICE '✅ Constraint UNIQUE adicionada em clientes.cpf_cnpj';
    ELSE
        RAISE NOTICE 'ℹ️  Constraint clientes_cpf_cnpj_key já existe';
    END IF;
    
    -- Adicionar UNIQUE em fornecedores.cpf_cnpj (se não existir)
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fornecedores_cpf_cnpj_key' 
        AND conrelid = 'fornecedores'::regclass
    ) THEN
        ALTER TABLE fornecedores 
        ADD CONSTRAINT fornecedores_cpf_cnpj_key UNIQUE (cpf_cnpj);
        RAISE NOTICE '✅ Constraint UNIQUE adicionada em fornecedores.cpf_cnpj';
    ELSE
        RAISE NOTICE 'ℹ️  Constraint fornecedores_cpf_cnpj_key já existe';
    END IF;
    
EXCEPTION
    WHEN unique_violation THEN
        RAISE EXCEPTION '❌ ERRO: Ainda existem CPF/CNPJ duplicados! Execute as queries de verificação acima primeiro.';
    WHEN OTHERS THEN
        RAISE EXCEPTION '❌ ERRO ao adicionar constraints: %', SQLERRM;
END $$;


-- 4. VERIFICAÇÃO FINAL
-- ============================================================================

DO $$
DECLARE
    v_constraint_clientes BOOLEAN;
    v_constraint_fornecedores BOOLEAN;
BEGIN
    -- Verificar se constraints foram criadas
    SELECT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'clientes_cpf_cnpj_key'
    ) INTO v_constraint_clientes;
    
    SELECT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fornecedores_cpf_cnpj_key'
    ) INTO v_constraint_fornecedores;
    
    RAISE NOTICE '';
    RAISE NOTICE '==================================================';
    RAISE NOTICE 'VERIFICAÇÃO FINAL';
    RAISE NOTICE '==================================================';
    
    IF v_constraint_clientes THEN
        RAISE NOTICE '✅ clientes.cpf_cnpj: UNIQUE constraint ativa';
    ELSE
        RAISE NOTICE '❌ clientes.cpf_cnpj: SEM UNIQUE constraint';
    END IF;
    
    IF v_constraint_fornecedores THEN
        RAISE NOTICE '✅ fornecedores.cpf_cnpj: UNIQUE constraint ativa';
    ELSE
        RAISE NOTICE '❌ fornecedores.cpf_cnpj: SEM UNIQUE constraint';
    END IF;
    
    RAISE NOTICE '==================================================';
    RAISE NOTICE '';
    
    IF v_constraint_clientes AND v_constraint_fornecedores THEN
        RAISE NOTICE '🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!';
        RAISE NOTICE 'CPF/CNPJ duplicados agora são prevenidos pelo banco de dados.';
    ELSE
        RAISE NOTICE '⚠️  MIGRAÇÃO INCOMPLETA - Verifique os erros acima';
    END IF;
END $$;


-- ============================================================================
-- INSTRUÇÕES DE USO:
-- ============================================================================
-- 
-- 1. Execute este script no banco de produção
-- 2. Se houver duplicados, o script vai alertar
-- 3. Use as queries comentadas para visualizar os duplicados
-- 4. Resolva os duplicados manualmente (decida qual manter)
-- 5. Execute o script novamente para adicionar as constraints
-- 
-- IMPORTANTE: 
-- - Faça BACKUP antes de executar
-- - Teste em ambiente de desenvolvimento primeiro
-- - A constraint UNIQUE permite múltiplos registros com cpf_cnpj = NULL
-- ============================================================================
