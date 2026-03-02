import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('🔍 VERIFICANDO TRANSAÇÕES NÃO CONCILIADAS\n')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Total de transações vs conciliadas
cursor.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN conciliado THEN 1 END) as conciliadas FROM transacoes_extrato")
stats = cursor.fetchone()
print(f'📊 Transações de extrato:')
print(f'   Total: {stats["total"]}')
print(f'   Conciliadas: {stats["conciliadas"]}')
print(f'   NÃO conciliadas: {stats["total"] - stats["conciliadas"]}')

# 2. Transações não conciliadas por tipo
cursor.execute("""
    SELECT tipo, COUNT(*) as qtd
    FROM transacoes_extrato
    WHERE NOT conciliado
    GROUP BY tipo
    ORDER BY qtd DESC
""")
nao_conc = cursor.fetchall()
print(f'\n📋 Transações NÃO conciliadas por tipo:')
for t in nao_conc:
    print(f'   - {t["tipo"]}: {t["qtd"]}')

# 3. Total de conciliações
cursor.execute("SELECT COUNT(*) as total FROM conciliacoes")
total_conc = cursor.fetchone()['total']
print(f'\n🔗 Total de conciliações registradas: {total_conc}')

# 4. Lançamentos sem conciliação
cursor.execute("""
    SELECT COUNT(*) as total,
           COUNT(CASE WHEN tipo = 'receita' THEN 1 END) as receitas,
           COUNT(CASE WHEN tipo = 'despesa' THEN 1 END) as despesas
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
""")
lanc_sem_conc = cursor.fetchone()
print(f'\n📦 Lançamentos SEM conciliação:')
print(f'   Total: {lanc_sem_conc["total"]}')
print(f'   Receitas manuais: {lanc_sem_conc["receitas"]}')
print(f'   Despesas manuais: {lanc_sem_conc["despesas"]}')

cursor.close()
conn.close()

print('\n✅ Verificação completa!')
