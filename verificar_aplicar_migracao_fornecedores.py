"""
Script para verificar e aplicar migração da tabela evento_fornecedores
"""
import sys
import os

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import Database

def verificar_e_aplicar_migracao():
    """Verifica se a tabela existe e aplica a migração se necessário"""
    print("="*80)
    print("🔍 Verificando tabela evento_fornecedores...")
    print("="*80)
    
    db = Database()
    
    try:
        conn = db.get_connection(allow_global=True)
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'evento_fornecedores'
            );
        """)
        
        tabela_existe = cursor.fetchone()[0]
        
        if tabela_existe:
            print("✅ Tabela evento_fornecedores já existe!")
            
            # Verificar quantos registros existem
            cursor.execute("SELECT COUNT(*) FROM evento_fornecedores")
            count = cursor.fetchone()[0]
            print(f"   📊 {count} fornecedores cadastrados em eventos")
            
        else:
            print("⚠️  Tabela evento_fornecedores NÃO existe!")
            print("📝 Aplicando migração...")
            
            # Ler o arquivo SQL
            script_dir = os.path.dirname(os.path.abspath(__file__))
            migration_file = os.path.join(script_dir, 'migration_evento_fornecedores.sql')
            
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # Executar a migração
            cursor.execute(migration_sql)
            conn.commit()
            
            print("✅ Migração aplicada com sucesso!")
            
            # Verificar novamente
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'evento_fornecedores'
                );
            """)
            
            if cursor.fetchone()[0]:
                print("✅ Tabela evento_fornecedores criada e validada!")
            else:
                print("❌ Erro: Tabela não foi criada corretamente")
                return False
        
        cursor.close()
        print("="*80)
        print("✅ Verificação concluída!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar/aplicar migração: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    verificar_e_aplicar_migracao()
