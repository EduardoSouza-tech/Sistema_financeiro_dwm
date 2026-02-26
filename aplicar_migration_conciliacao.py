"""
Aplicar migration de correção de conciliação do extrato
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database_postgresql import get_db_connection
import psycopg2.extras

print("\n" + "="*80)
print("🔧 APLICANDO MIGRATION - CORREÇÃO CONCILIAÇÃO EXTRATO")
print("="*80 + "\n")

try:
    with get_db_connection(empresa_id=20) as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        print("1️⃣  Adicionando colunas categoria, subcategoria, pessoa, observacoes...")
        
        cursor.execute("""
            ALTER TABLE transacoes_extrato 
            ADD COLUMN IF NOT EXISTS categoria VARCHAR(255),
            ADD COLUMN IF NOT EXISTS subcategoria VARCHAR(255),
            ADD COLUMN IF NOT EXISTS pessoa VARCHAR(255),
            ADD COLUMN IF NOT EXISTS observacoes TEXT
        """)
        print("   ✅ Colunas adicionadas\n")
        
        print("2️⃣  Removendo coluna lancamento_id (não mais necessária)...")
        cursor.execute("ALTER TABLE transacoes_extrato DROP COLUMN IF EXISTS lancamento_id")
        print("   ✅ Coluna removida\n")
        
        print("3️⃣  Criando índices para performance...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_conciliado 
            ON transacoes_extrato(conciliado, empresa_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_categoria 
            ON transacoes_extrato(categoria, empresa_id) 
            WHERE categoria IS NOT NULL
        """)
        print("   ✅ Índices criados\n")
        
        conn.commit()
        
        print("4️⃣  Verificando estrutura final...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'transacoes_extrato'
              AND column_name IN ('categoria', 'subcategoria', 'pessoa', 'observacoes', 'conciliado')
            ORDER BY column_name
        """)
        
        colunas = cursor.fetchall()
        print("   Colunas criadas:")
        for col in colunas:
            print(f"      • {col['column_name']} ({col['data_type']}) - Nullable: {col['is_nullable']}")
        
        cursor.close()
        
        print("\n" + "="*80)
        print("✅ MIGRATION APLICADA COM SUCESSO!")
        print("="*80)
        print("\n📋 Próximos passos:")
        print("   1. Código de conciliação será corrigido (não mais cria lançamentos)")
        print("   2. Testes de conciliação devem ser feitos")
        print("   3. Verificar que não há mais lançamentos [EXTRATO] sendo criados")
        print()
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
