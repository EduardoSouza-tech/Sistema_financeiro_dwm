-- ================================================================================
-- SCRIPT DE CORREÇÃO: Adicionar empresa_id em registros antigos
-- ================================================================================
-- 
-- PROBLEMA: Registros criados antes da implementação de RLS não têm empresa_id
-- SOLUÇÃO: Atualizar registros órfãos com empresa_id baseado no contexto
--
-- DATA: 2026-02-08
-- AUTOR: Sistema Automático
-- ================================================================================

-- 🔍 ANÁLISE: Verificar quantos registros estão sem empresa_id
SELECT 
    'contratos' as tabela,
    COUNT(*) as total,
    COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id
FROM contratos
UNION ALL
SELECT 
    'sessoes' as tabela,
    COUNT(*) as total,
    COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id
FROM sessoes
UNION ALL
SELECT 
    'lancamentos' as tabela,
    COUNT(*) as total,
    COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id
FROM lancamentos
UNION ALL
SELECT 
    'clientes' as tabela,
    COUNT(*) as total,
    COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id
FROM clientes
UNION ALL
SELECT 
    'fornecedores' as tabela,
    COUNT(*) as total,
    COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id
FROM fornecedores
UNION ALL
SELECT 
    'categorias' as tabela,
    COUNT(*) as total,
    COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id
FROM categorias;

-- ================================================================================
-- 🔧 CORREÇÃO: Atualizar contratos sem empresa_id
-- ================================================================================
-- Estratégia: Pegar empresa_id do cliente associado, ou usar 19 como fallback

UPDATE contratos
SET empresa_id = COALESCE(
    (SELECT empresa_id FROM clientes WHERE clientes.id = contratos.cliente_id LIMIT 1),
    19  -- Fallback: empresa padrão
)
WHERE empresa_id IS NULL;

-- ================================================================================
-- 🔧 CORREÇÃO: Atualizar sessões sem empresa_id
-- ================================================================================
-- Estratégia: 
-- 1. Pegar empresa_id do contrato vinculado
-- 2. Se não tiver, pegar do cliente
-- 3. Fallback: usar 19

UPDATE sessoes
SET empresa_id = COALESCE(
    (SELECT empresa_id FROM contratos WHERE contratos.id = sessoes.contrato_id LIMIT 1),
    (SELECT empresa_id FROM clientes WHERE clientes.id = sessoes.cliente_id LIMIT 1),
    19  -- Fallback: empresa padrão
)
WHERE empresa_id IS NULL;

-- ================================================================================
-- 🔧 CORREÇÃO: Atualizar lançamentos sem empresa_id
-- ================================================================================
-- Estratégia: Usar empresa padrão 19

UPDATE lancamentos
SET empresa_id = 19
WHERE empresa_id IS NULL;

-- ================================================================================
-- 🔧 CORREÇÃO: Atualizar clientes sem empresa_id
-- ================================================================================

UPDATE clientes
SET empresa_id = 19
WHERE empresa_id IS NULL;

-- ================================================================================
-- 🔧 CORREÇÃO: Atualizar fornecedores sem empresa_id
-- ================================================================================

UPDATE fornecedores
SET empresa_id = 19
WHERE empresa_id IS NULL;

-- ================================================================================
-- 🔧 CORREÇÃO: Atualizar categorias sem empresa_id
-- ================================================================================

UPDATE categorias
SET empresa_id = 19
WHERE empresa_id IS NULL;

-- ================================================================================
-- ✅ VERIFICAÇÃO FINAL: Confirmar que não há mais registros órfãos
-- ================================================================================

SELECT 
    'contratos' as tabela,
    COUNT(*) as total,
    COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id_apos_fix
FROM contratos
UNION ALL
SELECT 
    'sessoes' as tabela,
    COUNT(*) as total,
    COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id_apos_fix
FROM sessoes
UNION ALL
SELECT 
    'lancamentos' as tabela,
    COUNT(*) as total,
    COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id_apos_fix
FROM lancamentos
UNION ALL
SELECT 
    'clientes' as tabela,
    COUNT(*) as total,
    COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id_apos_fix
FROM clientes
UNION ALL
SELECT 
    'fornecedores' as tabela,
    COUNT(*) as total,
    COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id_apos_fix
FROM fornecedores
UNION ALL
SELECT 
    'categorias' as tabela,
    COUNT(*) as total,
    COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id_apos_fix
FROM categorias;

-- ================================================================================
-- 📊 RESULTADO ESPERADO: sem_empresa_id_apos_fix = 0 em todas as tabelas
-- ================================================================================
