"""
Script para criar as novas tabelas no banco PostgreSQL do Railway
INCLUINDO MIGRATION DE EVENTO_FUNCIONARIOS
"""
import os
import sys

# Importar o database_postgresql
import database_postgresql

def executar_migration_eventos():
    """Executa migration de funcoes_evento e evento_funcionarios"""
    print("\n" + "="*80)
    print("🚀 EXECUTANDO MIGRATION: EVENTO FUNCIONÁRIOS")
    print("="*80)
    
    try:
        db = database_postgresql.DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se tabelas já existem
        print("\n🔍 Verificando tabelas existentes...")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('funcoes_evento', 'evento_funcionarios')
        """)
        
        result = cursor.fetchone()
        count = result['count'] if isinstance(result, dict) else result[0]
        print(f"   📊 Encontradas {count}/2 tabelas")
        
        if count == 2:
            print("\n✅ Tabelas já existem!")
            
            # Contar funções
            cursor.execute("SELECT COUNT(*) as total FROM funcoes_evento")
            result = cursor.fetchone()
            total_funcoes = result['total'] if isinstance(result, dict) else result[0]
            print(f"   📋 {total_funcoes} funções cadastradas\n")
            return True
        
        # Ler arquivo SQL
        print("\n📂 Lendo migration_evento_funcionarios.sql...")
        sql_file = os.path.join(os.path.dirname(__file__), 'migration_evento_funcionarios.sql')
        
        if not os.path.exists(sql_file):
            print(f"❌ Arquivo não encontrado: {sql_file}")
            return False
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"✅ SQL lido ({len(sql_content)} bytes)")
        
        # Executar SQL
        print("\n📝 Executando migration...")
        cursor.execute(sql_content)
        conn.commit()
        print("✅ SQL executado e commitado!")
        
        # Verificar criação
        print("\n🔍 Verificando resultado...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('funcoes_evento', 'evento_funcionarios')
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"\n✅ {len(tables)} TABELAS CRIADAS:")
        for table in tables:
            nome = table['table_name'] if isinstance(table, dict) else table[0]
            print(f"   ✓ {nome}")
        
        # Contar funções
        cursor.execute("SELECT COUNT(*) as total FROM funcoes_evento")
        result = cursor.fetchone()
        count_funcoes = result['total'] if isinstance(result, dict) else result[0]
        print(f"\n✅ {count_funcoes} FUNÇÕES INSERIDAS")
        
        cursor.close()
        
        print("\n" + "="*80)
        print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

def criar_tabelas():
    """Cria todas as tabelas incluindo as novas do menu Operacional"""
    print("🔧 Iniciando criação de tabelas no PostgreSQL...")
    
    try:
        db = database_postgresql.DatabaseManager()
        print("✅ Conexão estabelecida com sucesso!")
        print("✅ Tabelas criadas/verificadas com sucesso!")
        
        # Executar migration de eventos
        if not executar_migration_eventos():
            print("⚠️ Migration de eventos falhou, mas continuando...")
        
        # Testar listando contratos
        contratos = database_postgresql.listar_contratos()
        print(f"✅ Teste de listagem: {len(contratos)} contratos encontrados")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    criar_tabelas()
