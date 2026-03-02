"""Verificar quantos lançamentos foram criados pela migração"""
import os
import sys

if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = input("Digite a DATABASE_URL: ").strip()

from database_postgresql import DatabaseManager

db = DatabaseManager()

with db.get_db_connection(allow_global=True) as conn:
    import psycopg2.extras
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Contar lançamentos criados via conciliação
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM lancamentos l
        INNER JOIN conciliacoes c ON c.lancamento_id = l.id
        WHERE l.status = 'pago'
    """)
    
    result = cursor.fetchone()
    lancamentos_criados = result['total'] if result else 0
    
    # Contar transações conciliadas
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM transacoes_extrato
        WHERE conciliado = TRUE
    """)
    
    result = cursor.fetchone()
    transacoes_conciliadas = result['total'] if result else 0
    
    # Contar transações SEM lançamento
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM transacoes_extrato te
        LEFT JOIN conciliacoes c ON c.transacao_extrato_id = te.id
        WHERE te.conciliado = TRUE AND c.lancamento_id IS NULL
    """)
    
    result = cursor.fetchone()
    sem_lancamento = result['total'] if result else 0
    
    cursor.close()

print("\n" + "="*60)
print("📊 STATUS DA MIGRAÇÃO")
print("="*60)
print(f"✅ Transações conciliadas no total: {transacoes_conciliadas}")
print(f"✅ Lançamentos criados via conciliação: {lancamentos_criados}")
print(f"❌ Transações conciliadas SEM lançamento: {sem_lancamento}")
print()

if sem_lancamento == 0:
    print("🎉 MIGRAÇÃO COMPLETA! Todas as conciliações têm lançamentos.")
else:
    print(f"⚠️  Ainda faltam {sem_lancamento} lançamento(s) para criar.")
    print("   Execute novamente: python migrar_conciliacoes_antigas.py --auto-confirm")

print("="*60)
