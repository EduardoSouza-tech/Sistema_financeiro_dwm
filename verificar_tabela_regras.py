"""
Script de diagnóstico: Verifica se tabela regras_conciliacao existe
"""
import os
import psycopg2

# URL do Railway
DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("🔍 DIAGNÓSTICO: Tabela regras_conciliacao")
print("=" * 80)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Verificar se tabela existe
    print("\n1️⃣ Verificando se tabela existe...")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'regras_conciliacao'
    """)
    existe = cursor.fetchone()[0]
    
    if existe:
        print("   ✅ Tabela regras_conciliacao EXISTE!")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM regras_conciliacao")
        qtd = cursor.fetchone()[0]
        print(f"   📊 {qtd} regra(s) cadastrada(s)")
        
        # Verificar estrutura
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'regras_conciliacao'
            ORDER BY ordinal_position
        """)
        colunas = cursor.fetchall()
        print(f"\n   📋 Estrutura da tabela ({len(colunas)} colunas):")
        for col in colunas:
            print(f"      - {col[0]} ({col[1]})")
        
    else:
        print("   ❌ Tabela regras_conciliacao NÃO EXISTE!")
        print("\n   🔧 A migration precisa ser executada manualmente!")
        print("\n   Execute no Railway CLI ou crie a tabela manualmente:")
        print("   railway run python setup_database.py")
    
    # Verificar função
    print("\n2️⃣ Verificando função buscar_regras_aplicaveis...")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM pg_proc 
        WHERE proname = 'buscar_regras_aplicaveis'
    """)
    func_existe = cursor.fetchone()[0]
    
    if func_existe:
        print("   ✅ Função buscar_regras_aplicaveis EXISTE!")
    else:
        print("   ❌ Função buscar_regras_aplicaveis NÃO EXISTE!")
    
    # Verificar permissões
    print("\n3️⃣ Verificando permissões...")
    cursor.execute("""
        SELECT codigo, nome 
        FROM permissoes 
        WHERE codigo LIKE 'regras_conciliacao_%'
        ORDER BY codigo
    """)
    permissoes = cursor.fetchall()
    
    if permissoes:
        print(f"   ✅ {len(permissoes)} permissão(ões) encontrada(s):")
        for perm in permissoes:
            print(f"      - {perm[0]}: {perm[1]}")
    else:
        print("   ❌ Nenhuma permissão de regras encontrada!")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    if existe and func_existe and permissoes:
        print("✅ TUDO OK! Sistema pronto para usar.")
    else:
        print("⚠️ MIGRATION INCOMPLETA! Execute setup_database.py")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
