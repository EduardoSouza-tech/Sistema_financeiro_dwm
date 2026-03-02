import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('🔍 ANALISANDO TRANSAÇÕES DE EXTRATO\n')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Total de transações
cursor.execute("SELECT COUNT(*) as total FROM transacoes_extrato")
total = cursor.fetchone()['total']
print(f'📊 Total de transações extrato: {total}')

# 2. Contagem por tipo
cursor.execute("""
    SELECT tipo, COUNT(*) as qtd 
    FROM transacoes_extrato 
    GROUP BY tipo 
    ORDER BY qtd DESC
""")
tipos = cursor.fetchall()
print(f'\n📈 Transações por tipo:')
for t in tipos:
    print(f'   - {t["tipo"]}: {t["qtd"]}')

# 3. Exemplos de DÉBITO
cursor.execute("""
    SELECT id, tipo, descricao, valor, data
    FROM transacoes_extrato 
    WHERE tipo = 'DÉBITO'
    LIMIT 5
""")
debitos = cursor.fetchall()
print(f'\n❌ Exemplos de DÉBITO (deveria virar DESPESA):')
for d in debitos:
    print(f'   ID {d["id"]}: {d["descricao"][:60]} | R$ {d["valor"]} | {d["data"]}')

# 4. Exemplos de CRÉDITO
cursor.execute("""
    SELECT id, tipo, descricao, valor, data
    FROM transacoes_extrato 
    WHERE tipo = 'CRÉDITO'
    LIMIT 5
""")
creditos = cursor.fetchall()
print(f'\n✅ Exemplos de CRÉDITO (deveria virar RECEITA):')
for c in creditos:
    print(f'   ID {c["id"]}: {c["descricao"][:60]} | R$ {c["valor"]} | {c["data"]}')

# 5. Verificar conciliações
cursor.execute("""
    SELECT 
        te.id, te.tipo as tipo_transacao, l.tipo as tipo_lancamento, te.descricao, te.valor
    FROM transacoes_extrato te
    JOIN conciliacoes c ON c.transacao_extrato_id = te.id
    JOIN lancamentos l ON l.id = c.lancamento_id
    WHERE te.tipo = 'DÉBITO'
    LIMIT 5
""")
conciliados_debito = cursor.fetchall()
print(f'\n🔗 Transações DÉBITO que viraram lançamentos:')
for c in conciliados_debito:
    print(f'   Transação {c["id"]} ({c["tipo_transacao"]}) → Lançamento tipo={c["tipo_lancamento"]}')
    print(f'      Descrição: {c["descricao"][:60]}')
    print(f'      Valor: R$ {c["valor"]}')
    print()

cursor.close()
conn.close()

print('✅ Análise completa!')
