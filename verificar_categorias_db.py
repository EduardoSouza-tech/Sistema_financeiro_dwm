import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print('\n📊 CATEGORIAS NO BANCO:')
print('=' * 80)

cur.execute('SELECT id, nome, tipo, empresa_id FROM categorias ORDER BY id')
rows = cur.fetchall()

for r in rows:
    print(f"  ID={r['id']:<3} | Nome={r['nome']:<30} | Tipo={r['tipo']:<10} | Empresa={r['empresa_id']}")

print('=' * 80)
print(f'✅ Total: {len(rows)} categorias\n')

# Verificar quantas são da empresa 18
cur.execute('SELECT COUNT(*) as total FROM categorias WHERE empresa_id = 18')
total_emp18 = cur.fetchone()['total']
print(f'🏢 Categorias da empresa 18: {total_emp18}')

# Verificar quantas são globais (NULL)
cur.execute('SELECT COUNT(*) as total FROM categorias WHERE empresa_id IS NULL')
total_global = cur.fetchone()['total']
print(f'🌐 Categorias globais (empresa_id IS NULL): {total_global}\n')

cur.close()
conn.close()
