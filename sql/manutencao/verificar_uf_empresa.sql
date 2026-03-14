-- Script SQL para verificar dados das empresas e certificados
-- Execute este script no PostgreSQL para ver os dados atuais

-- ============================================================
-- 1. VERIFICAR EMPRESAS CADASTRADAS
-- ============================================================
SELECT 
    id,
    razao_social,
    nome_fantasia,
    cnpj,
    estado AS "UF_CADASTRADO",
    cidade,
    CASE 
        WHEN estado = 'SP' THEN '35 (São Paulo) ⚠️ MUDARÁ PARA SP'
        WHEN estado = 'MG' THEN '31 (Minas Gerais) ✅ CORRETO'
        WHEN estado = 'RJ' THEN '33 (Rio de Janeiro)'
        WHEN estado IS NULL THEN 'NULL ❌ PROBLEMA!'
        ELSE estado || ' (verificar)'
    END AS "CÓDIGO_QUE_SERÁ_USADO",
    ativo
FROM empresas
ORDER BY id;

-- ============================================================
-- 2. VERIFICAR CERTIFICADOS DIGITAIS JÁ CADASTRADOS
-- ============================================================
SELECT 
    c.id AS "cert_id",
    c.empresa_id,
    e.razao_social AS "empresa",
    e.estado AS "uf_empresa",
    c.nome_certificado,
    c.cnpj AS "cnpj_cert",
    c.cuf AS "código_uf_cert",
    CASE c.cuf
        WHEN 35 THEN 'SP (São Paulo)'
        WHEN 31 THEN 'MG (Minas Gerais)'
        WHEN 33 THEN 'RJ (Rio de Janeiro)'
        ELSE 'Código ' || c.cuf
    END AS "estado_cert",
    c.ativo
FROM certificados_digitais c
LEFT JOIN empresas e ON e.id = c.empresa_id
ORDER BY c.id;

-- ============================================================
-- 3. ANÁLISE: EMPRESAS COM UF INCORRETO
-- ============================================================
SELECT 
    '⚠️ PROBLEMA ENCONTRADO!' AS "status",
    id,
    razao_social,
    cnpj,
    estado AS "uf_atual",
    'Essa empresa está cadastrada como ' || COALESCE(estado, 'NULL') || 
    ' mas deveria ser MG para o certificado funcionar corretamente!' AS "problema"
FROM empresas
WHERE estado != 'MG' OR estado IS NULL;

-- ============================================================
-- 4. SUGESTÃO DE CORREÇÃO (NÃO EXECUTE AINDA!)
-- ============================================================
-- Se identificar que a empresa está com UF errado, você pode corrigir com:
-- 
-- UPDATE empresas 
-- SET estado = 'MG'
-- WHERE id = [ID_DA_EMPRESA];
-- 
-- Substitua [ID_DA_EMPRESA] pelo ID correto antes de executar!

-- ============================================================
-- 5. VERIFICAR SESSÕES ATIVAS (qual empresa está sendo usada)
-- ============================================================
SELECT 
    s.id AS session_id,
    s.usuario_id,
    u.username,
    s.empresa_id,
    e.razao_social AS empresa_nome,
    e.estado AS empresa_uf,
    s.ip_address,
    s.criado_em,
    s.ativo
FROM sessoes_login s
LEFT JOIN usuarios u ON u.id = s.usuario_id
LEFT JOIN empresas e ON e.id = s.empresa_id
WHERE s.ativo = true
ORDER BY s.criado_em DESC
LIMIT 5;
