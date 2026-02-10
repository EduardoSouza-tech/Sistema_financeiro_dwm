"""
Script para executar migration de Regras de Auto-Conciliação
Executa migration_regras_conciliacao.sql no banco PostgreSQL
"""
import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import get_from_pool, return_to_pool, get_connection_pool

def executar_migration():
    """Executa a migration de regras de conciliação"""
    print("="*80)
    print("🚀 EXECUTANDO MIGRATION: Regras de Auto-Conciliação")
    print("="*80)
    
    # Ler arquivo SQL
    sql_file = 'migration_regras_conciliacao.sql'
    
    if not os.path.exists(sql_file):
        print(f"❌ Arquivo {sql_file} não encontrado!")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"\n📄 Arquivo lido: {len(sql)} caracteres")
    
    # Executar no banco
    conn = None
    cursor = None
    
    try:
        # Obter pool
        pool = get_connection_pool()
        conn = get_from_pool(pool)
        conn.autocommit = False  # Usar transação
        cursor = conn.cursor()
        
        print("\n🔌 Conectado ao banco de dados")
        print("⚙️  Executando SQL...")
        
        # Executar SQL
        cursor.execute(sql)
        
        # Commit
        conn.commit()
        
        print("\n✅ Migration executada com sucesso!")
        print("\n📊 Verificando estrutura criada...")
        
        # Verificar tabela
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'regras_conciliacao'
        """)
        tem_tabela = cursor.fetchone()[0]
        print(f"   ✅ Tabela regras_conciliacao: {'OK' if tem_tabela else 'NÃO ENCONTRADA'}")
        
        # Verificar função
        cursor.execute("""
            SELECT COUNT(*) FROM pg_proc 
            WHERE proname = 'buscar_regras_aplicaveis'
        """)
        tem_funcao = cursor.fetchone()[0]
        print(f"   ✅ Função buscar_regras_aplicaveis: {'OK' if tem_funcao else 'NÃO ENCONTRADA'}")
        
        # Verificar permissões
        cursor.execute("""
            SELECT COUNT(*) FROM permissoes 
            WHERE codigo LIKE 'regras_conciliacao_%'
        """)
        qtd_permissoes = cursor.fetchone()[0]
        print(f"   ✅ Permissões criadas: {qtd_permissoes}")
        
        print("\n" + "="*80)
        print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO ao executar migration:")
        print(f"   {str(e)}")
        
        if conn:
            conn.rollback()
            print("   🔄 Rollback executado")
        
        import traceback
        traceback.print_exc()
        
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_to_pool(conn)
        print("\n🔌 Conexão fechada")


if __name__ == '__main__':
    sucesso = executar_migration()
    sys.exit(0 if sucesso else 1)
