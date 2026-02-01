"""
Script para aplicar correção de constraint no Railway via web_server
"""
import sys
sys.path.insert(0, 'c:/Users/Nasci/OneDrive/Documents/Programas VS Code/DWM/sistema_financeiro/Sistema_financeiro_dwm')

from database_postgresql import Database

print("\n" + "="*80)
print("🔧 CORRIGINDO CONSTRAINT DE CATEGORIAS NO RAILWAY")
print("="*80)

try:
    # Usar database do projeto
    from config import DATABASE_CONFIG
    db = Database(DATABASE_CONFIG)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 1. Verificar constraints atuais
    print("\n📋 Constraints atuais:")
    cursor.execute("""
        SELECT 
            conname AS constraint_name,
            pg_get_constraintdef(oid) AS constraint_definition
        FROM pg_constraint
        WHERE conrelid = 'categorias'::regclass
        ORDER BY conname
    """)
    constraints = cursor.fetchall()
    for c in constraints:
        print(f"   - {c['constraint_name']}: {c['constraint_definition']}")
    
    # 2. Remover constraint antiga
    print("\n🗑️ Removendo constraint categorias_nome_key...")
    cursor.execute("ALTER TABLE categorias DROP CONSTRAINT IF EXISTS categorias_nome_key")
    print("   ✅ Constraint removida")
    
    # 3. Adicionar constraint composta
    print("\n➕ Adicionando constraint categorias_nome_empresa_unique...")
    cursor.execute("""
        ALTER TABLE categorias 
        ADD CONSTRAINT categorias_nome_empresa_unique 
        UNIQUE (nome, empresa_id)
    """)
    print("   ✅ Constraint adicionada")
    
    # 4. Verificar constraints finais
    print("\n📋 Constraints após correção:")
    cursor.execute("""
        SELECT 
            conname AS constraint_name,
            pg_get_constraintdef(oid) AS constraint_definition
        FROM pg_constraint
        WHERE conrelid = 'categorias'::regclass
        ORDER BY conname
    """)
    constraints = cursor.fetchall()
    for c in constraints:
        print(f"   - {c['constraint_name']}: {c['constraint_definition']}")
    
    # Commit
    conn.commit()
    cursor.close()
    
    print("\n✅ Correção aplicada com sucesso!")
    print("="*80 + "\n")
    
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
