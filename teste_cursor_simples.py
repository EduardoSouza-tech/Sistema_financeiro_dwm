"""
TESTE RÁPIDO - Verificar se o banco retorna dados corretos
"""
import psycopg2

DATABASE_URL = input("📋 DATABASE_URL: ").strip()

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

print("\n🔍 TESTE 1: SELECT direto")
cursor.execute("""
    SELECT id, nome_versao, exercicio_fiscal, is_ativa
    FROM plano_contas_versao
    WHERE empresa_id = 20
    LIMIT 1
""")

print(f"Descrição: {cursor.description}")
row = cursor.fetchone()
print(f"Row: {row}")
print(f"Tipo: {type(row)}")

if row:
    print(f"\nrow[0] = {row[0]} (tipo: {type(row[0])})")
    print(f"row[1] = {row[1]} (tipo: {type(row[1])})")
    print(f"row[2] = {row[2]} (tipo: {type(row[2])})")
    
    # Criar dict manualmente
    colunas = [desc[0] for desc in cursor.description]
    print(f"\nColunas: {colunas}")
    
    d = dict(zip(colunas, row))
    print(f"\nDict criado: {d}")
    print(f"d['id'] = {d.get('id')}")
    print(f"d['nome_versao'] = {d.get('nome_versao')}")

print("\n🔍 TESTE 2: Contar registros")
cursor.execute("SELECT COUNT(*) FROM plano_contas_versao WHERE empresa_id = 20")
print(f"Total: {cursor.fetchone()[0]}")

print("\n🔍 TESTE 3: Listar TODOS")
cursor.execute("""
    SELECT empresa_id, id, nome_versao
    FROM plano_contas_versao
    ORDER BY id
""")
all_rows = cursor.fetchall()
print(f"Total geral: {len(all_rows)}")
for r in all_rows[:5]:
    print(f"   {r}")

cursor.close()
conn.close()
