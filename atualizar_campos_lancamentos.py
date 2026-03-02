"""
Script para atualizar lançamentos existentes com dados das transações de extrato
(categoria, subcategoria, pessoa)
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('🔄 ATUALIZANDO LANÇAMENTOS COM DADOS DAS TRANSAÇÕES\n')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Identificar lançamentos que precisam ser atualizados
cursor.execute("""
    SELECT 
        l.id as lancamento_id,
        l.categoria as l_categoria,
        l.subcategoria as l_subcategoria,
        l.pessoa as l_pessoa,
        te.categoria as te_categoria,
        te.subcategoria as te_subcategoria,
        te.pessoa as te_pessoa,
        te.descricao
    FROM lancamentos l
    JOIN conciliacoes c ON c.lancamento_id = l.id
    JOIN transacoes_extrato te ON te.id = c.transacao_extrato_id
    WHERE 
        (te.categoria IS NOT NULL AND (l.categoria IS NULL OR l.categoria = 'Conciliação Bancária'))
        OR (te.subcategoria IS NOT NULL AND l.subcategoria IS NULL)
        OR (te.pessoa IS NOT NULL AND l.pessoa IS NULL)
""")

para_atualizar = cursor.fetchall()
print(f'📋 Encontrados {len(para_atualizar)} lançamentos para atualizar\n')

if len(para_atualizar) == 0:
    print('✅ Nenhuma atualização necessária!')
    cursor.close()
    conn.close()
    sys.exit(0)

# Estatísticas
com_categoria = sum(1 for l in para_atualizar if l['te_categoria'])
com_subcategoria = sum(1 for l in para_atualizar if l['te_subcategoria'])
com_pessoa = sum(1 for l in para_atualizar if l['te_pessoa'])

print(f'📊 Campos a atualizar:')
print(f'   - Categoria: {com_categoria}')
print(f'   - Subcategoria: {com_subcategoria}')
print(f'   - Pessoa: {com_pessoa}')

# Mostrar exemplos
print(f'\n📝 Exemplos (5 primeiros):')
for i, l in enumerate(para_atualizar[:5], 1):
    print(f'\n   {i}. Lançamento #{l["lancamento_id"]}:')
    print(f'      Descrição: {l["descricao"][:50]}...')
    if l['te_categoria']:
        print(f'      ✅ Categoria: "{l["l_categoria"]}" → "{l["te_categoria"]}"')
    if l['te_subcategoria']:
        print(f'      ✅ Subcategoria: {l["l_subcategoria"]} → "{l["te_subcategoria"]}"')
    if l['te_pessoa']:
        print(f'      ✅ Pessoa: {l["l_pessoa"]} → "{l["te_pessoa"][:50]}..."')

# Confirmar
if '--auto-confirm' not in sys.argv:
    resposta = input(f'\n⚠️  Atualizar {len(para_atualizar)} lançamentos? (s/N): ')
    if resposta.lower() != 's':
        print('❌ Operação cancelada!')
        cursor.close()
        conn.close()
        sys.exit(0)

# Executar atualização
print(f'\n🔄 Atualizando {len(para_atualizar)} lançamentos...\n')

atualizados_cat = 0
atualizados_subcat = 0
atualizados_pessoa = 0

for l in para_atualizar:
    lancamento_id = l['lancamento_id']
    updates = []
    params = []
    
    # Categoria
    if l['te_categoria'] and (not l['l_categoria'] or l['l_categoria'] == 'Conciliação Bancária'):
        updates.append("categoria = %s")
        params.append(l['te_categoria'])
        atualizados_cat += 1
    
    # Subcategoria
    if l['te_subcategoria'] and not l['l_subcategoria']:
        updates.append("subcategoria = %s")
        params.append(l['te_subcategoria'])
        atualizados_subcat += 1
    
    # Pessoa
    if l['te_pessoa'] and not l['l_pessoa']:
        updates.append("pessoa = %s")
        params.append(l['te_pessoa'])
        atualizados_pessoa += 1
    
    if updates:
        params.append(lancamento_id)
        query = f"UPDATE lancamentos SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, params)

conn.commit()

print(f'✅ SUCESSO! Lançamentos atualizados:')
print(f'   - Categoria: {atualizados_cat}')
print(f'   - Subcategoria: {atualizados_subcat}')
print(f'   - Pessoa: {atualizados_pessoa}')

# Verificar resultado
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(categoria) as com_categoria,
        COUNT(subcategoria) as com_subcategoria,
        COUNT(pessoa) as com_pessoa
    FROM lancamentos
""")
stats = cursor.fetchone()

print(f'\n📊 Estatísticas finais em LANÇAMENTOS:')
print(f'   Total: {stats["total"]}')
print(f'   Com categoria: {stats["com_categoria"]} ({stats["com_categoria"]*100//stats["total"]}%)')
print(f'   Com subcategoria: {stats["com_subcategoria"]} ({stats["com_subcategoria"]*100//stats["total"]}%)')
print(f'   Com pessoa: {stats["com_pessoa"]} ({stats["com_pessoa"]*100//stats["total"]}%)')

cursor.close()
conn.close()

print('\n✅ Atualização completa!')
