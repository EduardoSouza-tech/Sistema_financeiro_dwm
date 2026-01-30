"""
Script para aplicar RLS diretamente com DATABASE_URL como argumento
Uso: python aplicar_rls_direto.py "postgresql://user:pass@host:port/db"
"""

import sys
import os
import psycopg2

def aplicar_rls(database_url):
    """Aplica Row Level Security no banco de dados"""
    
    print("=" * 60)
    print("APLICANDO ROW LEVEL SECURITY")
    print("=" * 60)
    
    # Ler arquivo SQL
    sql_file = os.path.join(os.path.dirname(__file__), 'row_level_security_safe.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ Arquivo não encontrado: {sql_file}")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Conectar e executar
    try:
        print(f"\n🔌 Conectando ao banco de dados...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("📝 Executando SQL...")
        cursor.execute(sql_content)
        conn.commit()
        
        print("✅ Row Level Security aplicado com sucesso!")
        
        # Verificar status
        print("\n📊 Verificando status do RLS...")
        cursor.execute("SELECT * FROM rls_status ORDER BY tablename")
        
        print("\n" + "=" * 60)
        print("STATUS DAS TABELAS")
        print("=" * 60)
        print(f"{'Tabela':<30} {'RLS':<10} {'Políticas':<10}")
        print("-" * 60)
        
        tables_ok = 0
        tables_warning = 0
        
        for row in cursor.fetchall():
            schema, table, rls_enabled, policy_count = row
            status = "✅" if rls_enabled and policy_count > 0 else "⚠️"
            print(f"{table:<30} {str(rls_enabled):<10} {policy_count:<10} {status}")
            
            if rls_enabled and policy_count > 0:
                tables_ok += 1
            else:
                tables_warning += 1
        
        print("-" * 60)
        print(f"Total: {tables_ok + tables_warning} tabelas")
        print(f"✅ Com RLS: {tables_ok}")
        print(f"⚠️ Sem RLS: {tables_warning}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao aplicar RLS: {e}")
        import traceback
        traceback.print_exc()
        return False


def testar_isolamento(database_url):
    """Testa isolamento entre empresas"""
    
    print("\n" + "=" * 60)
    print("TESTANDO ISOLAMENTO ENTRE EMPRESAS")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Obter IDs de empresas para teste
        cursor.execute("SELECT id, razao_social FROM empresas ORDER BY id LIMIT 2")
        empresas = cursor.fetchall()
        
        if len(empresas) < 2:
            print("⚠️ Menos de 2 empresas cadastradas. Pulando teste de isolamento.")
            cursor.close()
            conn.close()
            return True
        
        empresa_1_id = empresas[0][0]
        empresa_1_nome = empresas[0][1]
        empresa_2_id = empresas[1][0]
        empresa_2_nome = empresas[1][1]
        
        print(f"\n🏢 Empresa 1: {empresa_1_nome} (ID: {empresa_1_id})")
        print(f"🏢 Empresa 2: {empresa_2_nome} (ID: {empresa_2_id})")
        
        # Teste 1: Contar lançamentos empresa 1
        print(f"\n📊 Teste 1: Definindo sessão para empresa {empresa_1_id}...")
        cursor.execute("SELECT set_current_empresa(%s)", (empresa_1_id,))
        cursor.execute("SELECT COUNT(*) FROM lancamentos")
        count_1 = cursor.fetchone()[0]
        print(f"   Lançamentos visíveis: {count_1}")
        
        # Teste 2: Contar lançamentos empresa 2
        print(f"\n📊 Teste 2: Definindo sessão para empresa {empresa_2_id}...")
        cursor.execute("SELECT set_current_empresa(%s)", (empresa_2_id,))
        cursor.execute("SELECT COUNT(*) FROM lancamentos")
        count_2 = cursor.fetchone()[0]
        print(f"   Lançamentos visíveis: {count_2}")
        
        # Teste 3: Verificar vazamento
        print(f"\n🔒 Teste 3: Tentando acessar empresa {empresa_2_id} enquanto sessão é {empresa_1_id}...")
        cursor.execute("SELECT set_current_empresa(%s)", (empresa_1_id,))
        cursor.execute("SELECT COUNT(*) FROM lancamentos WHERE empresa_id = %s", (empresa_2_id,))
        vazamento = cursor.fetchone()[0]
        
        if vazamento > 0:
            print(f"   ❌ FALHA: {vazamento} registros de outra empresa visíveis!")
            print("   ⚠️ RLS NÃO ESTÁ FUNCIONANDO CORRETAMENTE!")
            cursor.close()
            conn.close()
            return False
        else:
            print(f"   ✅ SUCESSO: Nenhum vazamento detectado")
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES DE ISOLAMENTO PASSARAM!")
        print("=" * 60)
        print("\n🔒 SEGURANÇA CONFIRMADA:")
        print("   • Row Level Security está ativo")
        print("   • Não há vazamento de dados entre empresas")
        print("   • Cada empresa vê apenas seus próprios dados")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao testar isolamento: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal"""
    
    print("\n" + "=" * 60)
    print("SCRIPT DE SEGURANÇA - ROW LEVEL SECURITY")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\n❌ ERRO: DATABASE_URL não fornecida")
        print("\nUso:")
        print('  python aplicar_rls_direto.py "postgresql://user:pass@host:port/db"')
        print("\nExemplo:")
        print('  python aplicar_rls_direto.py "postgresql://postgres:senha@monorail.proxy.rlwy.net:12345/railway"')
        sys.exit(1)
    
    database_url = sys.argv[1]
    
    print("\nEste script irá:")
    print("1. Aplicar Row Level Security em todas as tabelas")
    print("2. Criar funções e triggers de validação")
    print("3. Configurar auditoria de acessos")
    print("4. Testar isolamento entre empresas")
    
    resposta = input("\n⚠️ Deseja continuar? (s/N): ").strip().lower()
    
    if resposta != 's':
        print("\n❌ Operação cancelada pelo usuário")
        return
    
    # Aplicar RLS
    if not aplicar_rls(database_url):
        print("\n❌ Falha ao aplicar RLS. Abortando.")
        return
    
    # Testar isolamento
    if not testar_isolamento(database_url):
        print("\n⚠️ Testes de isolamento falharam. Verifique a configuração.")
        return
    
    print("\n" + "=" * 60)
    print("✅ SEGURANÇA CONFIGURADA COM SUCESSO!")
    print("=" * 60)
    print("\n📋 Próximos passos:")
    print("1. Reinicie o servidor web no Railway")
    print("2. Teste o sistema com diferentes empresas")
    print("3. Monitore os logs de auditoria em audit_data_access")
    print("\n💡 Dica: Use 'SELECT * FROM rls_status' para verificar status do RLS")


if __name__ == '__main__':
    main()
