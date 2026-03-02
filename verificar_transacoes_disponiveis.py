"""
Verificar transações disponíveis para matching
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

print('🔍 VERIFICANDO TRANSAÇÕES DO EXTRATO\n')

# 1. Total de transações
cursor.execute("SELECT COUNT(*) as total FROM transacoes_extrato WHERE empresa_id = 20")
total = cursor.fetchone()['total']
print(f'📊 Total de transações no extrato: {total}')

# 2. Transações conciliadas
cursor.execute("SELECT COUNT(*) as total FROM transacoes_extrato WHERE empresa_id = 20 AND conciliado = TRUE")
conciliadas = cursor.fetchone()['total']
print(f'   ✅ Conciliadas: {conciliadas}')

# 3. Transações NÃO conciliadas
cursor.execute("SELECT COUNT(*) as total FROM transacoes_extrato WHERE empresa_id = 20 AND conciliado = FALSE")
nao_conciliadas = cursor.fetchone()['total']
print(f'   ❌ NÃO Conciliadas: {nao_conciliadas}')

# 4. Por tipo
print('\n📈 Por tipo de transação:')
cursor.execute("""
    SELECT tipo, COUNT(*) as qtd, 
           SUM(CASE WHEN conciliado THEN 1 ELSE 0 END) as conciliadas
    FROM transacoes_extrato
    WHERE empresa_id = 20
    GROUP BY tipo
    ORDER BY tipo
""")
for row in cursor.fetchall():
    print(f'   {row["tipo"]}: {row["qtd"]} total ({row["conciliadas"]} conciliadas)')

# 5. Verificar se há transações com tipo CREDITO não conciliadas
print('\n💰 Transações CREDITO:')
cursor.execute("""
    SELECT id, descricao, valor, data, conciliado, categoria, subcategoria, pessoa
    FROM transacoes_extrato
    WHERE empresa_id = 20 AND tipo = 'CREDITO'
    ORDER BY data DESC
    LIMIT 10
""")
creditos = cursor.fetchall()
for trans in creditos:
    status = '✅' if trans['conciliado'] else '❌'
    print(f'   {status} ID {trans["id"]}: {trans["descricao"][:50]}')
    print(f'      Valor: R$ {trans["valor"]} | Data: {trans["data"]} | Conciliado: {trans["conciliado"]}')

# 6. Comparar com receitas não conciliadas
print('\n🔗 COMPARAÇÃO COM RECEITAS:')
cursor.execute("""
    SELECT COUNT(*) as total
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
""")
receitas_sem_conc = cursor.fetchone()['total']
print(f'   Receitas sem conciliação: {receitas_sem_conc}')

cursor.execute("""
    SELECT COUNT(*) as total
    FROM lancamentos l
    INNER JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
""")
receitas_com_conc = cursor.fetchone()['total']
print(f'   Receitas com conciliação: {receitas_com_conc}')

# 7. Análise especial: Origem das 782 receitas
print('\n🎯 ORIGEM DAS 782 RECEITAS:')
cursor.execute("""
    SELECT 
        CASE 
            WHEN descricao LIKE 'PAGAMENTO PIX%' THEN 'PIX'
            WHEN descricao LIKE 'RESGATE APLIC%' THEN 'RESGATE'
            WHEN descricao LIKE 'TED%' THEN 'TED'
            ELSE 'OUTRO'
        END as tipo_descricao,
        COUNT(*) as qtd,
        MIN(data_vencimento) as primeira_data,
        MAX(data_vencimento) as ultima_data
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
    GROUP BY tipo_descricao
    ORDER BY qtd DESC
""")

for row in cursor.fetchall():
    print(f'\n   📌 {row["tipo_descricao"]}:')
    print(f'      Quantidade: {row["qtd"]}')
    print(f'      Período: {row["primeira_data"]} → {row["ultima_data"]}')

# 8. Comparar descrições
print('\n📝 DESCRIÇÕES - Receitas vs Transações:')
print('\n   Receitas não conciliadas (primeiras 5):')
cursor.execute("""
    SELECT descricao, valor, data_vencimento
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
    ORDER BY id
    LIMIT 5
""")
for r in cursor.fetchall():
    print(f'      "{r["descricao"][:70]}" | R$ {r["valor"]} | {r["data_vencimento"]}')

print('\n   Transações CREDITO (primeiras 5):')
cursor.execute("""
    SELECT descricao, valor, data
    FROM transacoes_extrato
    WHERE empresa_id = 20 AND tipo = 'CREDITO'
    ORDER BY id
    LIMIT 5
""")
for t in cursor.fetchall():
    print(f'      "{t["descricao"][:70]}" | R$ {t["valor"]} | {t["data"]}')

cursor.close()
conn.close()

print('\n✅ Análise completa!')
