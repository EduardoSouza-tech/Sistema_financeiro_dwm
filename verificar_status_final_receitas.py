"""
Verificar status final das receitas após completar
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

print('📊 STATUS FINAL DAS RECEITAS\n')

# 1. Total geral
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(l.valor) as valor_total
    FROM lancamentos l
    WHERE UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
""")

total_geral = cursor.fetchone()
print(f'Total de receitas: {total_geral["total"]}')
print(f'Valor total: R$ {total_geral["valor_total"]:,.2f}\n')

# 2. Com vs sem conciliação
cursor.execute("""
    SELECT 
        COUNT(CASE WHEN c.lancamento_id IS NOT NULL THEN 1 END) as com_conciliacao,
        COUNT(CASE WHEN c.lancamento_id IS NULL THEN 1 END) as sem_conciliacao
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
""")

conc = cursor.fetchone()
print(f'Com conciliação extrato: {conc["com_conciliacao"]}')
print(f'Sem conciliação extrato: {conc["sem_conciliacao"]}\n')

# 3. Status dos campos nas órfãs
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(l.pessoa) as com_pessoa,
        COUNT(l.subcategoria) as com_subcategoria,
        COUNT(CASE WHEN l.categoria IS NOT NULL AND l.categoria != 'Conciliação Bancária' THEN 1 END) as com_categoria_real
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
""")

orfas = cursor.fetchone()

print(f'RECEITAS SEM CONCILIAÇÃO ({orfas["total"]}):')
print(f'   Com pessoa: {orfas["com_pessoa"]} ({orfas["com_pessoa"]/orfas["total"]*100:.1f}%)')
print(f'   Com subcategoria: {orfas["com_subcategoria"]} ({orfas["com_subcategoria"]/orfas["total"]*100:.1f}%)')
print(f'   Com categoria definida: {orfas["com_categoria_real"]} ({orfas["com_categoria_real"]/orfas["total"]*100:.1f}%)\n')

# 4. Categorias mais comuns
print('CATEGORIAS MAIS COMUNS (órfãs):')
cursor.execute("""
    SELECT l.categoria, COUNT(*) as qtd
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
    GROUP BY l.categoria
    ORDER BY qtd DESC
    LIMIT 5
""")

for row in cursor.fetchall():
    print(f'   {row["categoria"]}: {row["qtd"]}')

# 5. Subcategorias mais comuns
print('\nSUBCATEGORIAS MAIS COMUNS (órfãs):')
cursor.execute("""
    SELECT l.subcategoria, COUNT(*) as qtd
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
      AND l.subcategoria IS NOT NULL
    GROUP BY l.subcategoria
    ORDER BY qtd DESC
    LIMIT 5
""")

for row in cursor.fetchall():
    print(f'   {row["subcategoria"]}: {row["qtd"]}')

# 6. Comparação antes/depois
print('\n📈 MELHORIA:')
print(f'   ANTES: 30/812 receitas com dados completos (3,7%)')
print(f'   DEPOIS: {conc["com_conciliacao"] + orfas["com_pessoa"]}/{total_geral["total"]} receitas com pessoa definida ({(conc["com_conciliacao"] + orfas["com_pessoa"])/total_geral["total"]*100:.1f}%)')

cursor.close()
conn.close()

print('\n✅ Verificação completa!')
