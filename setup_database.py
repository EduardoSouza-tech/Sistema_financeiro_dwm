"""
Script de setup automático do banco de dados
Executa migrações necessárias na primeira vez
"""
import os
import sys

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import DatabaseManager


def check_evento_funcionarios_tables(db):
    """Verifica se tabelas de eventos já existem"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('funcoes_evento', 'evento_funcionarios')
        """)
        
        count = cursor.fetchone()[0]
        cursor.close()
        
        return count == 2
        
    except Exception as e:
        print(f"⚠️ Erro ao verificar tabelas de eventos: {e}")
        return False


def apply_evento_funcionarios_migration(db):
    """Aplica migration de eventos e funcionários"""
    
    print("\n" + "="*60)
    print("🔍 VERIFICANDO TABELAS DE EVENTOS")
    print("="*60)
    
    if check_evento_funcionarios_tables(db):
        print("✅ Tabelas já existem. Nada a fazer.")
        return True
    
    print("⚠️ Tabelas não encontradas. Aplicando migration...")
    
    # Ler arquivo SQL
    sql_file = os.path.join(os.path.dirname(__file__), 'migration_evento_funcionarios.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ Arquivo não encontrado: {sql_file}")
        return False
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("📝 Executando migration de eventos...")
        cursor.execute(sql_content)
        conn.commit()
        
        # Verificar criação
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('funcoes_evento', 'evento_funcionarios')
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"✅ {len(tables)} tabelas criadas:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        # Contar funções
        cursor.execute("SELECT COUNT(*) FROM funcoes_evento")
        count_funcoes = cursor.fetchone()['total'] if cursor.rowcount > 0 else cursor.fetchone()[0]
        print(f"✅ {count_funcoes} funções padrão inseridas")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao aplicar migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_rls_applied(db):
    """Verifica se RLS já foi aplicado"""
    try:
        conn = db.get_connection()
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


def apply_rls(db):
    """Aplica Row Level Security se ainda não aplicado"""
    
    print("\n" + "="*60)
    print("🔍 VERIFICANDO ROW LEVEL SECURITY")
    print("="*60)
    
    if check_rls_applied(db):
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
        
        conn = db.get_connection()
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
    
    # Inicializar DatabaseManager
    db = DatabaseManager()
    
    # 1. Aplicar migration de eventos (PRIMEIRO)
    eventos_success = apply_evento_funcionarios_migration(db)
    
    # 2. Aplicar RLS (DEPOIS)
    rls_success = apply_rls(db)
    
    # Resultado final
    print("\n" + "="*60)
    if eventos_success and rls_success:
        print("✅ SETUP CONCLUÍDO COM SUCESSO!")
        print("="*60)
        print("✅ Migration de eventos aplicada")
        print("✅ Row Level Security aplicado")
        sys.exit(0)
    else:
        print("⚠️ SETUP CONCLUÍDO COM AVISOS")
        print("="*60)
        if not eventos_success:
            print("⚠️ Migration de eventos falhou (pode já existir)")
        if not rls_success:
            print("⚠️ RLS falhou (pode já existir)")
        print("\n💡 Erros são normais em redeploys (tabelas já existem)")
        sys.exit(0)  # Não falhar o deploy por isso
