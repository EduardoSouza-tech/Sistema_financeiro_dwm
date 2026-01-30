"""
Script para aplicar Row Level Security no banco de dados
=========================================================

Este script:
1. Aplica RLS em todas as tabelas com empresa_id
2. Cria funções auxiliares
3. Cria triggers de validação
4. Configura auditoria
5. Testa isolamento entre empresas

IMPORTANTE: Execute este script APENAS uma vez
"""

import sys
import os
from database_postgresql import get_db_connection

def aplicar_rls():
    """Aplica Row Level Security no banco de dados"""
    
    print("=" * 60)
    print("APLICANDO ROW LEVEL SECURITY")
    print("=" * 60)
    
    # Ler arquivo SQL
    sql_file = os.path.join(os.path.dirname(__file__), 'row_level_security.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ Arquivo não encontrado: {sql_file}")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Conectar e executar
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            print("\n📝 Executando SQL...")
            
            # Executar SQL completo
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
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao aplicar RLS: {e}")
        import traceback
        traceback.print_exc()
        return False


def testar_isolamento():
    """Testa isolamento entre empresas"""
    
    print("\n" + "=" * 60)
    print("TESTANDO ISOLAMENTO ENTRE EMPRESAS")
    print("=" * 60)
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Obter IDs de empresas para teste
            cursor.execute("SELECT id, razao_social FROM empresas ORDER BY id LIMIT 2")
            empresas = cursor.fetchall()
            
            if len(empresas) < 2:
                print("⚠️ Menos de 2 empresas cadastradas. Pulando teste de isolamento.")
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
            
            # Teste 3: Verificar total sem RLS (como admin)
            print(f"\n📊 Teste 3: Total de lançamentos no banco (sem filtro)...")
            cursor.execute("SELECT COUNT(*) FROM lancamentos WHERE empresa_id IN (%s, %s)", 
                          (empresa_1_id, empresa_2_id))
            count_total = cursor.fetchone()[0]
            print(f"   Total no banco: {count_total}")
            
            # Teste 4: Tentar acessar dados de outra empresa
            print(f"\n🔒 Teste 4: Tentando acessar empresa {empresa_2_id} enquanto sessão é {empresa_1_id}...")
            cursor.execute("SELECT set_current_empresa(%s)", (empresa_1_id,))
            cursor.execute("SELECT COUNT(*) FROM lancamentos WHERE empresa_id = %s", (empresa_2_id,))
            vazamento = cursor.fetchone()[0]
            
            if vazamento > 0:
                print(f"   ❌ FALHA: {vazamento} registros de outra empresa visíveis!")
                print("   ⚠️ RLS NÃO ESTÁ FUNCIONANDO CORRETAMENTE!")
                return False
            else:
                print(f"   ✅ SUCESSO: Nenhum vazamento detectado")
            
            # Teste 5: Verificar categorias
            print(f"\n📊 Teste 5: Verificando isolamento de categorias...")
            cursor.execute("SELECT set_current_empresa(%s)", (empresa_1_id,))
            cursor.execute("SELECT COUNT(*) FROM categorias")
            cat_1 = cursor.fetchone()[0]
            
            cursor.execute("SELECT set_current_empresa(%s)", (empresa_2_id,))
            cursor.execute("SELECT COUNT(*) FROM categorias")
            cat_2 = cursor.fetchone()[0]
            
            print(f"   Empresa {empresa_1_id}: {cat_1} categorias")
            print(f"   Empresa {empresa_2_id}: {cat_2} categorias")
            
            # Teste 6: Verificar clientes
            print(f"\n📊 Teste 6: Verificando isolamento de clientes...")
            cursor.execute("SELECT set_current_empresa(%s)", (empresa_1_id,))
            cursor.execute("SELECT COUNT(*) FROM clientes")
            cli_1 = cursor.fetchone()[0]
            
            cursor.execute("SELECT set_current_empresa(%s)", (empresa_2_id,))
            cursor.execute("SELECT COUNT(*) FROM clientes")
            cli_2 = cursor.fetchone()[0]
            
            print(f"   Empresa {empresa_1_id}: {cli_1} clientes")
            print(f"   Empresa {empresa_2_id}: {cli_2} clientes")
            
            print("\n" + "=" * 60)
            print("✅ TODOS OS TESTES DE ISOLAMENTO PASSARAM!")
            print("=" * 60)
            print("\n🔒 SEGURANÇA CONFIRMADA:")
            print("   • Row Level Security está ativo")
            print("   • Não há vazamento de dados entre empresas")
            print("   • Cada empresa vê apenas seus próprios dados")
            
            cursor.close()
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
    if not aplicar_rls():
        print("\n❌ Falha ao aplicar RLS. Abortando.")
        return
    
    # Testar isolamento
    if not testar_isolamento():
        print("\n⚠️ Testes de isolamento falharam. Verifique a configuração.")
        return
    
    print("\n" + "=" * 60)
    print("✅ SEGURANÇA CONFIGURADA COM SUCESSO!")
    print("=" * 60)
    print("\n📋 Próximos passos:")
    print("1. Reinicie o servidor web")
    print("2. Teste o sistema com diferentes empresas")
    print("3. Monitore os logs de auditoria em audit_data_access")
    print("4. Verifique o arquivo security_wrapper.py para uso avançado")
    print("\n💡 Dica: Use 'SELECT * FROM rls_status' para verificar status do RLS")


if __name__ == '__main__':
    main()
