"""
Script: Verifica estrutura de permissões do banco
"""
import psycopg2

DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("🔍 VERIFICANDO ESTRUTURA DE PERMISSÕES")
print("=" * 80)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. Verificar tabelas relacionadas a usuários
    print("\n1️⃣ Tabelas relacionadas a usuários:")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%usuario%'
        ORDER BY table_name
    """)
    tabelas = cursor.fetchall()
    for t in tabelas:
        print(f"   - {t[0]}")
    
    # 2. Verificar tabelas relacionadas a permissões
    print("\n2️⃣ Tabelas relacionadas a permissões:")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%permiss%' OR table_name LIKE '%permis%')
        ORDER BY table_name
    """)
    tabelas = cursor.fetchall()
    for t in tabelas:
        print(f"   - {t[0]}")
    
    # 3. Verificar estrutura da tabela usuarios
    print("\n3️⃣ Estrutura da tabela 'usuarios':")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'usuarios'
        ORDER BY ordinal_position
    """)
    colunas = cursor.fetchall()
    for col in colunas:
        print(f"   - {col[0]} ({col[1]})")
    
    # 4. Verificar se tem campo permissoes em usuarios
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'usuarios'
        AND column_name LIKE '%permis%'
    """)
    perm_cols = cursor.fetchall()
    
    if perm_cols:
        print("\n4️⃣ Colunas de permissão em 'usuarios':")
        for col in perm_cols:
            print(f"   - {col[0]} ({col[1]})")
            
        # Verificar conteúdo do campo
        cursor.execute("SELECT id, nome, permissoes FROM usuarios LIMIT 3")
        usuarios = cursor.fetchall()
        print("\n   📊 Exemplo de dados:")
        for u in usuarios:
            print(f"      ID {u[0]}: {u[1]}")
            print(f"         Permissões: {u[2]}")
    
    # 5. Verificar tabela permissoes
    print("\n5️⃣ Total de permissões cadastradas:")
    cursor.execute("SELECT COUNT(*) FROM permissoes")
    total = cursor.fetchone()[0]
    print(f"   - {total} permissão(ões) total")
    
    cursor.execute("""
        SELECT codigo FROM permissoes 
        WHERE codigo LIKE 'regras_conciliacao_%'
        ORDER BY codigo
    """)
    regras_perms = cursor.fetchall()
    print(f"\n   - {len(regras_perms)} permissão(ões) de regras:")
    for p in regras_perms:
        print(f"      • {p[0]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ VERIFICAÇÃO CONCLUÍDA")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
