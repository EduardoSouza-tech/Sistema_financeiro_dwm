-- COMPLETAR RECEITAS ÓRFÃS COM SQL DIRETO
-- Extrai pessoa, define categoria e subcategoria

-- 1. PAGAMENTOS PIX - Extrair nome e definir categoria
UPDATE lancamentos l
SET 
    pessoa = TRIM(SUBSTRING(descricao FROM '\d{11,14}\s+(.+)$')),
    categoria = 'RECEITAS DE EVENTOS',
    subcategoria = 'PAGAMENTOS PIX'
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND l.descricao LIKE 'PAGAMENTO PIX-PIX_DEB%'
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id);

-- 2. RECEBIMENTOS PIX - Extrair nome e definir categoria  
UPDATE lancamentos l
SET 
    pessoa = TRIM(SUBSTRING(descricao FROM '\d{11,14}\s+(.+)$')),
    categoria = 'RECEITAS DE EVENTOS',
    subcategoria = 'RECEBIMENTOS PIX'
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND (l.descricao LIKE '%RECEBIMENTO PIX%' OR l.descricao LIKE '%PIX-PIX_CRED%')
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id);

-- 3. RESGATES - Definir pessoa e categoria
UPDATE lancamentos l
SET 
    pessoa = COALESCE(pessoa, 'BANCO SICREDI'),
    categoria = 'RECEITAS BANCARIAS',
    subcategoria = 'RESGATE DE APLICACAO'
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND l.descricao LIKE '%RESGATE APLIC%'
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id);

-- 4. APLICAÇÕES - Definir pessoa e categoria
UPDATE lancamentos l
SET 
    pessoa = COALESCE(pessoa, 'BANCO SICREDI'),
    categoria = 'RECEITAS BANCARIAS',
    subcategoria = 'RENDIMENTO DE APLICACOES'
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND (l.descricao LIKE '%APLICACAO FINANCEIRA%' OR l.descricao LIKE '%APLIC. FINANCEIRA%')
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id);

-- 5. TED/DOC/TRANSFERENCIAS - Tentar extrair nome
UPDATE lancamentos l
SET 
    pessoa = COALESCE(TRIM(SUBSTRING(descricao FROM '\d{14}\s+(.+)$')), pessoa),
    categoria = COALESCE(NULLIF(categoria, 'Conciliação Bancária'), 'RECEITAS DIVERSAS'),
    subcategoria = COALESCE(subcategoria, 'TRANSFERENCIAS RECEBIDAS')
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND (l.descricao LIKE '%TED-%' OR l.descricao LIKE '%DOC-%' OR l.descricao LIKE '%TRANSFERENCIA%')
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id);

-- 6. LIQUIDAÇÃO DE COBRANÇAS
UPDATE lancamentos l
SET 
    categoria = 'RECEITAS DIVERSAS',
    subcategoria = 'LIQUIDACAO DE COBRANCAS'
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND (l.descricao LIKE '%LIQ.COBRANCA%' OR l.descricao LIKE '%LIQUIDACAO%')
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id);

-- 7. OUTROS - Pelo menos trocar categoria
UPDATE lancamentos l
SET 
    categoria = 'RECEITAS DIVERSAS'
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND categoria = 'Conciliação Bancária'
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id);

-- VERIFICAR RESULTADO
SELECT 
    'RESULTADO' as status,
    COUNT(*) as total_receitas_orfas,
    COUNT(pessoa) as com_pessoa,
    COUNT(subcategoria) as com_subcategoria,
    SUM(CASE WHEN categoria = 'Conciliação Bancária' THEN 1 ELSE 0 END) as ainda_conciliacao
FROM lancamentos l
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id);
