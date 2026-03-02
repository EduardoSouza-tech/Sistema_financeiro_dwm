import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('🔍 ANALISANDO LANÇAMENTOS NO BANCO DE DADOS\n')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Total de lançamentos
cursor.execute("SELECT COUNT(*) as total FROM lancamentos")
total = cursor.fetchone()['total']
print(f'📊 Total de lançamentos: {total}')

# 2. Contagem por tipo
cursor.execute("""
    SELECT tipo, COUNT(*) as qtd 
    FROM lancamentos 
    GROUP BY tipo 
    ORDER BY qtd DESC
""")
tipos = cursor.fetchall()
print(f'\n📈 Lançamentos por tipo:')
for t in tipos:
    print(f'   - {t["tipo"]}: {t["qtd"]}')

# 3. Contagem por status
cursor.execute("""
    SELECT status, COUNT(*) as qtd 
    FROM lancamentos 
    GROUP BY status 
    ORDER BY qtd DESC
""")
statuses = cursor.fetchall()
print(f'\n🔖 Lançamentos por status:')
for s in statuses:
    print(f'   - {s["status"]}: {s["qtd"]}')

# 4. Exemplo de lançamento tipo despesa
cursor.execute("""
    SELECT id, tipo, descricao, valor, data_vencimento, status, 
           pessoa, categoria, subcategoria, numero_documento
    FROM lancamentos 
    WHERE UPPER(tipo) = 'DESPESA'
    LIMIT 3
""")
despesas = cursor.fetchall()
print(f'\n💳 Exemplos de DESPESAS:')
for d in despesas:
    print(f'   ID {d["id"]}: {d["descricao"]} | R$ {d["valor"]} | Status: {d["status"]}')
    print(f'      - Pessoa: {d["pessoa"]}')
    print(f'      - Categoria: {d["categoria"]} > {d["subcategoria"]}')
    print(f'      - Nº Doc: {d["numero_documento"]}')
    print(f'      - Vencimento: {d["data_vencimento"]}')
    print()

# 5. Exemplo de lançamento tipo receita
cursor.execute("""
    SELECT id, tipo, descricao, valor, data_vencimento, status, 
           pessoa, categoria, subcategoria, numero_documento
    FROM lancamentos 
    WHERE UPPER(tipo) = 'RECEITA'
    LIMIT 3
""")
receitas = cursor.fetchall()
print(f'💰 Exemplos de RECEITAS:')
for r in receitas:
    print(f'   ID {r["id"]}: {r["descricao"]} | R$ {r["valor"]} | Status: {r["status"]}')
    print(f'      - Pessoa: {r["pessoa"]}')
    print(f'      - Categoria: {r["categoria"]} > {r["subcategoria"]}')
    print(f'      - Nº Doc: {r["numero_documento"]}')
    print(f'      - Vencimento: {r["data_vencimento"]}')
    print()

# 6. Lançamentos recentes (últimos 10)
cursor.execute("""
    SELECT id, tipo, descricao, data_vencimento, status
    FROM lancamentos 
    ORDER BY id DESC
    LIMIT 10
""")
recentes = cursor.fetchall()
print(f'🕐 Últimos 10 lançamentos criados:')
for r in recentes:
    print(f'   ID {r["id"]}: [{r["tipo"]}] {r["descricao"][:50]} | {r["data_vencimento"]} | {r["status"]}')

# 7. Range de datas
cursor.execute("""
    SELECT 
        MIN(data_vencimento) as data_min,
        MAX(data_vencimento) as data_max
    FROM lancamentos
""")
datas = cursor.fetchone()
print(f'\n📅 Range de datas de vencimento:')
print(f'   Mais antiga: {datas["data_min"]}')
print(f'   Mais recente: {datas["data_max"]}')

cursor.close()
conn.close()

print('\n✅ Análise completa!')
