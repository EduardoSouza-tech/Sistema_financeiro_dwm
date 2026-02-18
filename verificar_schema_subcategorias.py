"""
Script para verificar schema da tabela subcategorias
"""
import sys
import os

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import Database

def verificar_schema():
    """Verifica o schema das tabelas subcategorias e evento_fornecedores"""
    print("="*80)
    print("🔍 Verificando schema das tabelas...")
    print("="*80)
    
    db = Database()
    
    try:
        conn = db.get_connection(allow_global=True)
        cursor = conn.cursor()
        
        # 1. Verificar se a tabela subcategorias existe
        print("\n📋 TABELA: subcategorias")
        print("-"*80)
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'subcategorias'
            );
        """)
        
        if cursor.fetchone()[0]:
            print("✅ Tabela subcategorias existe")
            
            # Listar colunas
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'subcategorias'
                ORDER BY ordinal_position;
            """)
            
            colunas = cursor.fetchall()
            print(f"   📊 Colunas ({len(colunas)}):")
            for col in colunas:
                print(f"      - {col[0]:20s} {col[1]:15s} NULL={col[2]:3s} DEFAULT={col[3]}")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM subcategorias")
            count = cursor.fetchone()[0]
            print(f"   📊 Total de registros: {count}")
            
            # Verificar se tem coluna 'ativa'
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'subcategorias' 
                    AND column_name = 'ativa'
                );
            """)
            
            if cursor.fetchone()[0]:
                print("   ✅ Coluna 'ativa' existe")
            else:
                print("   ❌ Coluna 'ativa' NÃO existe - PRECISA SER ADICIONADA")
                print("   💡 Execute: ALTER TABLE subcategorias ADD COLUMN ativa BOOLEAN DEFAULT TRUE;")
            
        else:
            print("❌ Tabela subcategorias NÃO existe")
            print("   💡 Execute o schema_empresa.sql")
        
        # 2. Verificar se a tabela evento_fornecedores existe
        print("\n📋 TABELA: evento_fornecedores")
        print("-"*80)
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'evento_fornecedores'
            );
        """)
        
        if cursor.fetchone()[0]:
            print("✅ Tabela evento_fornecedores existe")
            
            # Listar colunas
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'evento_fornecedores'
                ORDER BY ordinal_position;
            """)
            
            colunas = cursor.fetchall()
            print(f"   📊 Colunas ({len(colunas)}):")
            for col in colunas:
                print(f"      - {col[0]:20s} {col[1]:15s} NULL={col[2]:3s} DEFAULT={col[3]}")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM evento_fornecedores")
            count = cursor.fetchone()[0]
            print(f"   📊 Total de registros: {count}")
            
        else:
            print("❌ Tabela evento_fornecedores NÃO existe - PRECISA SER CRIADA")
            print("   💡 Execute o arquivo migration_evento_fornecedores.sql")
        
        cursor.close()
        print("\n" + "="*80)
        print("✅ Verificação concluída!")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Erro ao verificar schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verificar_schema()
