"""
Script de setup automático do banco de dados
Executa migrações necessárias na primeira vez
"""
import os
import sys
from database_postgresql import get_db_connection

def check_rls_applied():
    """Verifica se RLS já foi aplicado"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar se view rls_status existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_views 
                    WHERE viewname = 'rls_status'
                );
            """)
            
            view_exists = cursor.fetchone()[0]
            cursor.close()
            
            return view_exists
            
    except Exception as e:
        print(f"⚠️ Erro ao verificar RLS: {e}")
        return False


def apply_rls():
    """Aplica Row Level Security se ainda não aplicado"""
    
    print("\n" + "="*60)
    print("🔍 VERIFICANDO ROW LEVEL SECURITY")
    print("="*60)
    
    if check_rls_applied():
        print("✅ RLS já está aplicado. Nada a fazer.")
        return True
    
    print("⚠️ RLS não detectado. Aplicando agora...")
    
    # Ler arquivo SQL
    sql_file = os.path.join(os.path.dirname(__file__), 'row_level_security.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ Arquivo não encontrado: {sql_file}")
        return False
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            print("📝 Executando SQL de RLS...")
            cursor.execute(sql_content)
            conn.commit()
            
            print("✅ Row Level Security aplicado com sucesso!")
            
            # Verificar status
            cursor.execute("SELECT COUNT(*) FROM rls_status WHERE rls_enabled = true")
            count = cursor.fetchone()[0]
            print(f"✅ {count} tabelas com RLS ativo")
            
            cursor.close()
            return True
            
    except Exception as e:
        print(f"❌ Erro ao aplicar RLS: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n🚀 SETUP DO BANCO DE DADOS")
    print("="*60)
    
    success = apply_rls()
    
    if success:
        print("\n✅ Setup concluído com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Falha no setup")
        sys.exit(1)
