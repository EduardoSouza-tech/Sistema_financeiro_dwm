import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('🔍 INVESTIGANDO CONTAS A RECEBER\n')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Verificar lançamentos tipo RECEITA
cursor.execute("""
    SELECT COUNT(*) as total,
           COUNT(categoria) as com_categoria,
           COUNT(subcategoria) as com_subcategoria,
           COUNT(pessoa) as com_pessoa
    FROM lancamentos
    WHERE UPPER(tipo) = 'RECEITA'
""")
stats_receita = cursor.fetchone()
print(f'📊 Estatísticas RECEITAS:')
print(f'   Total: {stats_receita["total"]}')
print(f'   Com categoria: {stats_receita["com_categoria"]}')
print(f'   Com subcategoria: {stats_receita["com_subcategoria"]}')
print(f'   Com pessoa: {stats_receita["com_pessoa"]}')

# 2. Ver exemplos de receitas
cursor.execute("""
    SELECT id, descricao, categoria, subcategoria, pessoa, valor, status
    FROM lancamentos
    WHERE UPPER(tipo) = 'RECEITA'
    ORDER BY id DESC
    LIMIT 10
""")
receitas = cursor.fetchall()
print(f'\n📝 Exemplos de RECEITAS (últimas 10):')
for r in receitas:
    print(f'\n   ID {r["id"]}: {r["descricao"][:50]}')
    print(f'      Status: {r["status"]} | Valor: R$ {r["valor"]}')
    print(f'      Categoria: {r["categoria"]}')
    print(f'      Subcategoria: {r["subcategoria"]}')
    print(f'      Pessoa: {r["pessoa"][:50] if r["pessoa"] else None}')

# 3. Verificar transações CREDITO
cursor.execute("""
    SELECT id, descricao, categoria, subcategoria, pessoa
    FROM transacoes_extrato
    WHERE tipo = 'CREDITO'
    LIMIT 5
""")
transacoes_credito = cursor.fetchall()
print(f'\n💰 Exemplos de transações CREDITO:')
for t in transacoes_credito:
    print(f'\n   Transação ID {t["id"]}: {t["descricao"][:50]}')
    print(f'      Categoria: {t["categoria"]}')
    print(f'      Subcategoria: {t["subcategoria"]}')
    print(f'      Pessoa: {t["pessoa"][:50] if t["pessoa"] else None}')

# 4. Verificar receitas conciliadas
cursor.execute("""
    SELECT 
        l.id, l.descricao, l.categoria, l.subcategoria, l.pessoa,
        te.categoria as te_cat, te.subcategoria as te_subcat, te.pessoa as te_pessoa
    FROM lancamentos l
    JOIN conciliacoes c ON c.lancamento_id = l.id
    JOIN transacoes_extrato te ON te.id = c.transacao_extrato_id
    WHERE UPPER(l.tipo) = 'RECEITA'
    LIMIT 5
""")
receitas_conc = cursor.fetchall()
print(f'\n🔗 Receitas conciliadas (comparação transação → lançamento):')
for r in receitas_conc:
    print(f'\n   Lançamento #{r["id"]}: {r["descricao"][:50]}')
    print(f'      Lançamento categoria: {r["categoria"]}')
    print(f'      Transação categoria: {r["te_cat"]}')
    print(f'      ---')
    print(f'      Lançamento subcategoria: {r["subcategoria"]}')
    print(f'      Transação subcategoria: {r["te_subcat"]}')
    print(f'      ---')
    print(f'      Lançamento pessoa: {r["pessoa"][:40] if r["pessoa"] else None}')
    print(f'      Transação pessoa: {r["te_pessoa"][:40] if r["te_pessoa"] else None}')

cursor.close()
conn.close()

print('\n✅ Investigação completa!')
