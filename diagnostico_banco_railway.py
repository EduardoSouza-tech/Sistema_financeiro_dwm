"""
Diagnóstico completo do banco Railway - Ver todas as tabelas
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# URL do Railway
DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("🔍 DIAGNÓSTICO COMPLETO DO BANCO RAILWAY")
print("=" * 80)

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    # Listar todas as tabelas
    print("\n📋 TABELAS EXISTENTES:")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    
    tabelas = cursor.fetchall()
    print(f"\nTotal: {len(tabelas)} tabela(s)\n")
    
    for i, tab in enumerate(tabelas, 1):
        print(f"{i:3d}. {tab['table_name']}")
    
    # Verificar se categorias existe
    print("\n" + "=" * 80)
    print("🔍 VERIFICANDO TABELA CATEGORIAS")
    print("=" * 80)
    
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'categorias'
        );
    """)
    
    if cursor.fetchone()['exists']:
        print("✅ Tabela categorias EXISTE")
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'categorias'
            ORDER BY ordinal_position
        """)
        
        colunas = cursor.fetchall()
        print(f"\n📊 Colunas ({len(colunas)}):")
        for col in colunas:
            print(f"   - {col['column_name']:25s} {col['data_type']:20s} NULL={col['is_nullable']}")
        
        cursor.execute("SELECT COUNT(*) as total FROM categorias")
        print(f"\n📊 Total de registros: {cursor.fetchone()['total']}")
    else:
        print("❌ Tabela categorias NÃO EXISTE")
    
    # Verificar fornecedores
    print("\n" + "=" * 80)
    print("🔍 VERIFICANDO TABELA FORNECEDORES")
    print("=" * 80)
    
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'fornecedores'
        );
    """)
    
    if cursor.fetchone()['exists']:
        print("✅ Tabela fornecedores EXISTE")
        cursor.execute("SELECT COUNT(*) as total FROM fornecedores")
        print(f"📊 Total de registros: {cursor.fetchone()['total']}")
    else:
        print("❌ Tabela fornecedores NÃO EXISTE")
    
    # Verificar eventos
    print("\n" + "=" * 80)
    print("🔍 VERIFICANDO TABELA EVENTOS")
    print("=" * 80)
    
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'eventos'
        );
    """)
    
    if cursor.fetchone()['exists']:
        print("✅ Tabela eventos EXISTE")
        cursor.execute("SELECT COUNT(*) as total FROM eventos")
        print(f"📊 Total de registros: {cursor.fetchone()['total']}")
    else:
        print("❌ Tabela eventos NÃO EXISTE")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
