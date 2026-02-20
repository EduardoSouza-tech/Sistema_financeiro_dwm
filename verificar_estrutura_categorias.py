"""Verificar estrutura da tabela categorias"""
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway"

conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
cursor = conn.cursor()

print("📋 Estrutura da tabela CATEGORIAS:\n")
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'categorias'
    ORDER BY ordinal_position
""")

for col in cursor.fetchall():
    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
    print(f"   {col['column_name']:20s} {col['data_type']:20s} {nullable}")

print("\n📋 Estrutura da tabela SUBCATEGORIAS:\n")
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'subcategorias'
    ORDER BY ordinal_position
""")

for col in cursor.fetchall():
    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
    print(f"   {col['column_name']:20s} {col['data_type']:20s} {nullable}")

print("\n📋 Estrutura da tabela PLANO_CONTAS:\n")
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'plano_contas'
    ORDER BY ordinal_position
""")

for col in cursor.fetchall():
    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
    print(f"   {col['column_name']:20s} {col['data_type']:20s} {nullable}")

cursor.close()
conn.close()
