"""
Script OTIMIZADO para atualizar lançamentos em lote (muito mais rápido)
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import sys

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('🔄 ATUALIZAÇÃO RÁPIDA DE LANÇAMENTOS (em lote)\n')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Identificar lançamentos que precisam ser atualizados
cursor.execute("""
    SELECT 
        l.id as lancamento_id,
        te.categoria,
        te.subcategoria,
        te.pessoa
    FROM lancamentos l
    JOIN conciliacoes c ON c.lancamento_id = l.id
    JOIN transacoes_extrato te ON te.id = c.transacao_extrato_id
    WHERE 
        (te.categoria IS NOT NULL AND (l.categoria IS NULL OR l.categoria = 'Conciliação Bancária'))
        OR (te.subcategoria IS NOT NULL AND l.subcategoria IS NULL)
        OR (te.pessoa IS NOT NULL AND l.pessoa IS NULL)
""")

para_atualizar = cursor.fetchall()
print(f'📋 Encontrados {len(para_atualizar)} lançamentos para atualizar')

if len(para_atualizar) == 0:
    print('✅ Nenhuma atualização necessária!')
    cursor.close()
    conn.close()
    sys.exit(0)

# Atualização em lote usando CASE WHEN
print(f'\n🚀 Atualizando {len(para_atualizar)} lançamentos em LOTE...')

# Preparar IDs e valores
ids = []
categorias = {}
subcategorias = {}
pessoas = {}

for l in para_atualizar:
    lid = l['lancamento_id']
    ids.append(lid)
    if l['categoria']:
        categorias[lid] = l['categoria']
    if l['subcategoria']:
        subcategorias[lid] = l['subcategoria']
    if l['pessoa']:
        pessoas[lid] = l['pessoa']

# Construir query com CASE WHEN
query = "UPDATE lancamentos SET "
updates = []

if categorias:
    case_cat = "categoria = CASE "
    for lid, cat in categorias.items():
        case_cat += f"WHEN id = {lid} THEN %s "
    case_cat += "ELSE categoria END"
    updates.append(case_cat)

if subcategorias:
    case_subcat = "subcategoria = CASE "
    for lid, subcat in subcategorias.items():
        case_subcat += f"WHEN id = {lid} THEN %s "
    case_subcat += "ELSE subcategoria END"
    updates.append(case_subcat)

if pessoas:
    case_pessoa = "pessoa = CASE "
    for lid, pessoa in pessoas.items():
        case_pessoa += f"WHEN id = {lid} THEN %s "
    case_pessoa += "ELSE pessoa END"
    updates.append(case_pessoa)

query += ", ".join(updates)
query += f" WHERE id = ANY(%s)"

# Montar parâmetros
params = []
params.extend(categorias.values())
params.extend(subcategorias.values())
params.extend(pessoas.values())
params.append(ids)

# Executar update em lote
cursor.execute(query, params)
linhas = cursor.rowcount

conn.commit()

print(f'✅ SUCESSO! {linhas} lançamentos atualizados em um único comando!')
print(f'   - Categorias: {len(categorias)}')
print(f'   - Subcategorias: {len(subcategorias)}')
print(f'   - Pessoas: {len(pessoas)}')

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

print(f'\n📊 Estatísticas finais:')
print(f'   Total: {stats["total"]}')
print(f'   Com categoria: {stats["com_categoria"]} ({stats["com_categoria"]*100//stats["total"]}%)')
print(f'   Com subcategoria: {stats["com_subcategoria"]} ({stats["com_subcategoria"]*100//stats["total"]}%)')
print(f'   Com pessoa: {stats["com_pessoa"]} ({stats["com_pessoa"]*100//stats["total"]}%)')

cursor.close()
conn.close()

print('\n✅ Atualização completa!')
