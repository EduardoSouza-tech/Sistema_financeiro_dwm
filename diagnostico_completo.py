import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('🔍 DIAGNÓSTICO COMPLETO DO PROBLEMA\n')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Verificar tipos distintos em transacoes_extrato
cursor.execute("""
    SELECT DISTINCT tipo, COUNT(*) as qtd
    FROM transacoes_extrato
    GROUP BY tipo
""")
tipos_extrato = cursor.fetchall()
print(f'📋 Tipos em transacoes_extrato:')
for t in tipos_extrato:
    print(f'   - "{t["tipo"]}" (length={len(t["tipo"] or "")}, ASCII={[ord(c) for c in (t["tipo"] or "")[:10]]}): {t["qtd"]}')

# 2. Exemplos de cada tipo
for tipo_row in tipos_extrato:
    tipo_val = tipo_row['tipo']
    cursor.execute("""
        SELECT id, tipo, descricao, valor, data
        FROM transacoes_extrato
        WHERE tipo = %s
        LIMIT 3
    """, (tipo_val,))
    exemplos = cursor.fetchall()
    print(f'\n📝 Exemplos de tipo="{tipo_val}":')
    for ex in exemplos:
        print(f'   ID {ex["id"]}: R$ {ex["valor"]:,.2f} | {ex["descricao"][:50]}')

# 3. Verificar tipos em lancamentos
cursor.execute("""
    SELECT DISTINCT tipo, COUNT(*) as qtd
    FROM lancamentos
    GROUP BY tipo
""")
tipos_lanc = cursor.fetchall()
print(f'\n\n📋 Tipos em lancamentos:')
for t in tipos_lanc:
    print(f'   - "{t["tipo"]}": {t["qtd"]}')

# 4. Cross-check: transação → lançamento
cursor.execute("""
    SELECT 
        te.tipo as tipo_transacao, 
        l.tipo as tipo_lancamento,
        COUNT(*) as qtd
    FROM transacoes_extrato te
    JOIN conciliacoes c ON c.transacao_extrato_id = te.id
    JOIN lancamentos l ON l.id = c.lancamento_id
    GROUP BY te.tipo, l.tipo
    ORDER BY qtd DESC
""")
mapping = cursor.fetchall()
print(f'\n🔗 Mapeamento transação → lançamento:')
for m in mapping:
    print(f'   {m["tipo_transacao"]} → {m["tipo_lancamento"]}: {m["qtd"]} registros')

# 5. Ver se há lançamentos não conciliados
cursor.execute("""
    SELECT COUNT(*) as qtd
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
""")
nao_conciliados = cursor.fetchone()['qtd']
print(f'\n❓ Lançamentos NÃO conciliados: {nao_conciliados}')

cursor.close()
conn.close()

print('\n✅ Diagnóstico completo!')
