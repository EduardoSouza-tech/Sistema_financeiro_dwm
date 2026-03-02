import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('🔍 VERIFICANDO RECEITAS SEM PESSOA/SUBCATEGORIA\n')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Receitas sem pessoa que TÊM conciliação
cursor.execute("""
    SELECT 
        l.id, l.descricao, l.categoria,
        te.categoria as te_cat, 
        te.subcategoria as te_subcat, 
        te.pessoa as te_pessoa
    FROM lancamentos l
    JOIN conciliacoes c ON c.lancamento_id = l.id
    JOIN transacoes_extrato te ON te.id = c.transacao_extrato_id
    WHERE UPPER(l.tipo) = 'RECEITA'
      AND l.pessoa IS NULL
    LIMIT 10
""")
receitas_sem_pessoa = cursor.fetchall()

print(f'📋 Receitas SEM pessoa mas COM conciliação:')
print(f'   Total encontradas: {len(receitas_sem_pessoa)}')
if receitas_sem_pessoa:
    print('\n   Exemplos:')
    for r in receitas_sem_pessoa:
        print(f'\n   Lançamento #{r["id"]}: {r["descricao"][:50]}')
        print(f'      Lançamento: categoria="{r["categoria"]}", pessoa=NULL')
        print(f'      Transação: categoria="{r["te_cat"]}", subcategoria="{r["te_subcat"]}", pessoa="{r["te_pessoa"][:40] if r["te_pessoa"] else None}"')
        if r["te_pessoa"] or r["te_subcat"]:
            print(f'      ⚠️  PODE SER ATUALIZADO!')

# 2. Contar quantas receitas podem ser atualizadas
cursor.execute("""
    SELECT COUNT(*) as total
    FROM lancamentos l
    JOIN conciliacoes c ON c.lancamento_id = l.id
    JOIN transacoes_extrato te ON te.id = c.transacao_extrato_id
    WHERE UPPER(l.tipo) = 'RECEITA'
      AND (
          (te.pessoa IS NOT NULL AND l.pessoa IS NULL)
          OR (te.subcategoria IS NOT NULL AND l.subcategoria IS NULL)
          OR (te.categoria IS NOT NULL AND l.categoria = 'Conciliação Bancária')
      )
""")
pode_atualizar = cursor.fetchone()['total']

print(f'\n📊 DIAGNÓSTICO:')
print(f'   Receitas que PODEM ser atualizadas: {pode_atualizar}')

# 3. Receitas sem conciliação (lançamentos manuais)
cursor.execute("""
    SELECT COUNT(*) as total
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE UPPER(l.tipo) = 'RECEITA'
      AND c.lancamento_id IS NULL
""")
sem_conciliacao = cursor.fetchone()['total']

print(f'   Receitas SEM conciliação (manuais): {sem_conciliacao}')
print(f'   (Essas não podem ser atualizadas automaticamente)')

cursor.close()
conn.close()

print('\n✅ Diagnóstico completo!')
