"""
Executar SQL direto para completar receitas
"""
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('='*80)
print('SQL DIRETO - Completar Receitas Órfãs')
print('='*80)
print()

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# 1. PAGAMENTOS PIX
print('1. Atualizando PAGAMENTOS PIX...')
cursor.execute("""
UPDATE lancamentos l
SET 
    pessoa = TRIM(SUBSTRING(descricao FROM '\\d{11,14}\\s+(.+)$')),
    categoria = 'RECEITAS DE EVENTOS',
    subcategoria = 'PAGAMENTOS PIX'
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND l.descricao LIKE 'PAGAMENTO PIX-PIX_DEB%'
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id)
""")
print(f'   ✅ {cursor.rowcount} registros atualizados')
conn.commit()

# 2. RECEBIMENTOS PIX
print('\n2. Atualizando RECEBIMENTOS PIX...')
cursor.execute("""
UPDATE lancamentos l
SET 
    pessoa = TRIM(SUBSTRING(descricao FROM '\\d{11,14}\\s+(.+)$')),
    categoria = 'RECEITAS DE EVENTOS',
    subcategoria = 'RECEBIMENTOS PIX'
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND (l.descricao LIKE '%RECEBIMENTO PIX%' OR l.descricao LIKE '%PIX-PIX_CRED%')
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id)
""")
print(f'   ✅ {cursor.rowcount} registros atualizados')
conn.commit()

# 3. RESGATES
print('\n3. Atualizando RESGATES...')
cursor.execute("""
UPDATE lancamentos l
SET 
    pessoa = COALESCE(pessoa, 'BANCO SICREDI'),
    categoria = 'RECEITAS BANCARIAS',
    subcategoria = 'RESGATE DE APLICACAO'
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND l.descricao LIKE '%RESGATE APLIC%'
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id)
""")
print(f'   ✅ {cursor.rowcount} registros atualizados')
conn.commit()

# 4. APLICAÇÕES
print('\n4. Atualizando APLICAÇÕES...')
cursor.execute("""
UPDATE lancamentos l
SET 
    pessoa = COALESCE(pessoa, 'BANCO SICREDI'),
    categoria = 'RECEITAS BANCARIAS',
    subcategoria = 'RENDIMENTO DE APLICACOES'
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND (l.descricao LIKE '%APLICACAO FINANCEIRA%' OR l.descricao LIKE '%APLIC. FINANCEIRA%')
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id)
""")
print(f'   ✅ {cursor.rowcount} registros atualizados')
conn.commit()

# 5. TED/DOC
print('\n5. Atualizando TED/DOC/TRANSFERENCIAS...')
cursor.execute("""
UPDATE lancamentos l
SET 
    pessoa = COALESCE(TRIM(SUBSTRING(descricao FROM '\\d{14}\\s+(.+)$')), pessoa),
    categoria = COALESCE(NULLIF(categoria, 'Conciliação Bancária'), 'RECEITAS DIVERSAS'),
    subcategoria = COALESCE(subcategoria, 'TRANSFERENCIAS RECEBIDAS')
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND (l.descricao LIKE '%TED-%' OR l.descricao LIKE '%DOC-%' OR l.descricao LIKE '%TRANSFERENCIA%')
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id)
""")
print(f'   ✅ {cursor.rowcount} registros atualizados')
conn.commit()

# 6. LIQUIDAÇÃO
print('\n6. Atualizando LIQUIDAÇÃO DE COBRANÇAS...')
cursor.execute("""
UPDATE lancamentos l
SET 
    categoria = 'RECEITAS DIVERSAS',
    subcategoria = 'LIQUIDACAO DE COBRANCAS'
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND (l.descricao LIKE '%LIQ.COBRANCA%' OR l.descricao LIKE '%LIQUIDACAO%')
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id)
""")
print(f'   ✅ {cursor.rowcount} registros atualizados')
conn.commit()

# 7. OUTROS
print('\n7. Atualizando OUTROS...')
cursor.execute("""
UPDATE lancamentos l
SET 
    categoria = 'RECEITAS DIVERSAS'
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND categoria = 'Conciliação Bancária'
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id)
""")
print(f'   ✅ {cursor.rowcount} registros atualizados')
conn.commit()

# VERIFICAR RESULTADO
print('\n' + '='*80)
print('RESULTADO FINAL')
print('='*80)

cursor.execute("""
SELECT 
    COUNT(*) as total_receitas_orfas,
    COUNT(pessoa) as com_pessoa,
    COUNT(subcategoria) as com_subcategoria,
    SUM(CASE WHEN categoria = 'Conciliação Bancária' THEN 1 ELSE 0 END) as ainda_conciliacao
FROM lancamentos l
WHERE l.empresa_id = 20
  AND UPPER(l.tipo) = 'RECEITA'
  AND NOT EXISTS (SELECT 1 FROM conciliacoes c WHERE c.lancamento_id = l.id)
""")

resultado = cursor.fetchone()

print(f'\nReceitas órfãs: {resultado[0]}')
print(f'Com pessoa: {resultado[1]} ({resultado[1]/resultado[0]*100:.1f}%)')
print(f'Com subcategoria: {resultado[2]} ({resultado[2]/resultado[0]*100:.1f}%)')
print(f'Ainda "Conciliação Bancária": {resultado[3]}')

cursor.close()
conn.close()

print('\n✅ Processo completo!')
