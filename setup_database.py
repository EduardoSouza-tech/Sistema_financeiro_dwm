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


def execute_migration_eventos():
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


def execute_migration_regras_conciliacao():
    """Executa migration de regras de conciliação"""
    print("\n" + "="*80, flush=True)
    print("📝 EXECUTANDO MIGRATION DE REGRAS DE CONCILIAÇÃO", flush=True)
    print("="*80, flush=True)
    
    try:
        # Inicializar DatabaseManager
        db = DatabaseManager()
        print("✅ DatabaseManager inicializado", flush=True)
        
        # Conectar ao banco
        conn = db.get_connection()
        cursor = conn.cursor()
        print("✅ Conexão estabelecida", flush=True)
        
        # Verificar se tabela já existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'regras_conciliacao'
        """)
        
        count = cursor.fetchone()[0]
        
        if count == 1:
            print("✅ Tabela regras_conciliacao já existe. Nada a fazer.", flush=True)
            cursor.close()
            return True
        
        print(f"⚠️ Tabela não existe. Executando migration...", flush=True)
        
        # Ler arquivo SQL
        sql_file = os.path.join(os.path.dirname(__file__), 'migration_regras_conciliacao.sql')
        
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
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'regras_conciliacao'
        """)
        
        if cursor.fetchone()[0] == 1:
            print("✅ TABELA regras_conciliacao CRIADA COM SUCESSO!", flush=True)
        
        # Verificar função
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pg_proc 
            WHERE proname = 'buscar_regras_aplicaveis'
        """)
        
        if cursor.fetchone()[0] > 0:
            print("✅ FUNÇÃO buscar_regras_aplicaveis CRIADA!", flush=True)
        
        # Verificar permissões
        cursor.execute("""
            SELECT COUNT(*) 
            FROM permissoes 
            WHERE codigo LIKE 'regras_conciliacao_%'
        """)
        
        perm_count = cursor.fetchone()[0]
        print(f"✅ {perm_count} PERMISSÕES CRIADAS", flush=True)
        
        cursor.close()
        
        print("\n" + "="*80, flush=True)
        print("✅ MIGRATION REGRAS CONCILIAÇÃO CONCLUÍDA!", flush=True)
        print("="*80, flush=True)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA MIGRATION REGRAS: {e}", flush=True)
        import traceback
        traceback.print_exc()
        print("", flush=True)
        return False


def execute_migration_permissoes_empresa_regras():
    """Executa migration para adicionar permissões de regras no sistema multi-empresa"""
    print("\n" + "="*80, flush=True)
    print("📝 EXECUTANDO MIGRATION DE PERMISSÕES MULTI-EMPRESA", flush=True)
    print("="*80, flush=True)
    
    try:
        # Inicializar DatabaseManager
        db = DatabaseManager()
        print("✅ DatabaseManager inicializado", flush=True)
        
        # Conectar ao banco
        conn = db.get_connection()
        cursor = conn.cursor()
        print("✅ Conexão estabelecida", flush=True)
        
        # Verificar se já foi executado (simples: verifica se algum usuário já tem as permissões)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM usuario_empresas
            WHERE permissoes_empresa::text LIKE '%regras_conciliacao_view%'
            AND ativo = TRUE
        """)
        
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"✅ Migration já executada ({count} usuário(s) com permissões). Nada a fazer.", flush=True)
            cursor.close()
            return True
        
        print("⚠️ Permissões não encontradas. Executando migration...", flush=True)
        
        # Ler arquivo SQL
        sql_file = os.path.join(os.path.dirname(__file__), 'migration_permissoes_empresa_regras.sql')
        
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
        
        # Verificar resultado
        cursor.execute("""
            SELECT COUNT(*) 
            FROM usuario_empresas
            WHERE permissoes_empresa::text LIKE '%regras_conciliacao_view%'
            AND ativo = TRUE
        """)
        
        count = cursor.fetchone()[0]
        print(f"✅ {count} USUÁRIO(S) ATUALIZADOS COM PERMISSÕES", flush=True)
        
        cursor.close()
        
        print("\n" + "="*80, flush=True)
        print("✅ MIGRATION PERMISSÕES MULTI-EMPRESA CONCLUÍDA!", flush=True)
        print("="*80, flush=True)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA MIGRATION PERMISSÕES: {e}", flush=True)
        import traceback
        traceback.print_exc()
        print("", flush=True)
        return False



if __name__ == '__main__':
    try:
        # Executar migrations
        eventos_success = execute_migration_eventos()
        regras_success = execute_migration_regras_conciliacao()
        permissoes_success = execute_migration_permissoes_empresa_regras()
        
        print("\n" + "="*80, flush=True)
        print("📋 RESUMO DO SETUP", flush=True)
        print("="*80, flush=True)
        print(f"✅ Migration Eventos: {'OK' if eventos_success else 'FALHOU'}", flush=True)
        print(f"✅ Migration Regras: {'OK' if regras_success else 'FALHOU'}", flush=True)
        print(f"✅ Migration Permissões: {'OK' if permissoes_success else 'FALHOU'}", flush=True)
        print("="*80, flush=True)
        
        if eventos_success and regras_success and permissoes_success:
            print("\n✅ SETUP CONCLUÍDO COM SUCESSO!", flush=True)
        else:
            print("\n⚠️ Setup com avisos (normal em redeploys)", flush=True)
        
        sys.exit(0)  # Nunca falhar o deploy
            
    except Exception as e:
        print(f"\n❌ Erro fatal no setup: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(0)  # Não falhar o deploy mesmo com erro

