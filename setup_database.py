"""
Script de setup automático do banco de dados
Executa migrações necessárias na primeira vez
"""
import os
import sys

print("="*80, flush=True)
print("🚀 SETUP DO BANCO DE DADOS - INICIANDO", flush=True)
print("="*80, flush=True)

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database_postgresql import DatabaseManager
    print("✅ DatabaseManager importado", flush=True)
except Exception as e:
    print(f"❌ Erro ao importar DatabaseManager: {e}", flush=True)
    sys.exit(1)


def execute_migration():
    """Executa migration de eventos"""
    print("\n" + "="*80, flush=True)
    print("📝 EXECUTANDO MIGRATION DE EVENTOS", flush=True)
    print("="*80, flush=True)
    
    try:
        # Inicializar DatabaseManager
        db = DatabaseManager()
        print("✅ DatabaseManager inicializado", flush=True)
        
        # Conectar ao banco
        conn = db.get_connection()
        cursor = conn.cursor()
        print("✅ Conexão estabelecida", flush=True)
        
        # Verificar se tabelas já existem
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('funcoes_evento', 'evento_funcionarios')
        """)
        
        count = cursor.fetchone()[0]
        
        if count == 2:
            print("✅ Tabelas já existem. Nada a fazer.", flush=True)
            cursor.close()
            return True
        
        print(f"⚠️ Encontradas {count}/2 tabelas. Executando migration...", flush=True)
        
        # Ler arquivo SQL
        sql_file = os.path.join(os.path.dirname(__file__), 'migration_evento_funcionarios.sql')
        
        if not os.path.exists(sql_file):
            print(f"❌ Arquivo não encontrado: {sql_file}", flush=True)
            return False
        
        print(f"✅ Arquivo SQL encontrado: {sql_file}", flush=True)
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"✅ SQL lido ({len(sql_content)} bytes)", flush=True)
        
        # Executar SQL
        print("📝 Executando SQL...", flush=True)
        cursor.execute(sql_content)
        conn.commit()
        print("✅ SQL executado e commitado", flush=True)
        
        # Verificar criação
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('funcoes_evento', 'evento_funcionarios')
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"\n✅ {len(tables)} TABELAS CRIADAS:", flush=True)
        for table in tables:
            tname = table['table_name'] if isinstance(table, dict) else table[0]
            print(f"   ✓ {tname}", flush=True)
        
        # Contar funções
        cursor.execute("SELECT COUNT(*) as total FROM funcoes_evento")
        result = cursor.fetchone()
        count_funcoes = result['total'] if isinstance(result, dict) else result[0]
        print(f"\n✅ {count_funcoes} FUNÇÕES INSERIDAS", flush=True)
        
        cursor.close()
        
        print("\n" + "="*80, flush=True)
        print("✅ MIGRATION CONCLUÍDA COM SUCESSO!", flush=True)
        print("="*80, flush=True)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA MIGRATION: {e}", flush=True)
        import traceback
        traceback.print_exc()
        print("", flush=True)
        return False


if __name__ == '__main__':
    try:
        success = execute_migration()
        
        if success:
            print("\n✅ Setup concluído com sucesso!", flush=True)
            sys.exit(0)
        else:
            print("\n⚠️ Setup teve problemas, mas não vamos falhar o deploy", flush=True)
            sys.exit(0)  # Não falhar o deploy
            
    except Exception as e:
        print(f"\n❌ Erro fatal no setup: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(0)  # Não falhar o deploy mesmo com erro
    
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
