import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'
conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
cur = conn.cursor()

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='contratos' ORDER BY ordinal_position")
cols = [r['column_name'] for r in cur.fetchall()]
print('Colunas:', cols)

cur.execute('SELECT id, numero, descricao, empresa_id, status, observacoes FROM contratos ORDER BY empresa_id, id')
rows = cur.fetchall()
print(f'Total de contratos no banco (TODOS): {len(rows)}')
for r in rows:
    obs = r['observacoes'] or ''
    nome = ''
    try:
        import json
        d = json.loads(obs)
        nome = d.get('nome', '')
    except:
        pass
    print(f"  id={r['id']} numero={r['numero']} empresa_id={r['empresa_id']} status={r['status']} nome={nome}")

cur.close()
conn.close()
