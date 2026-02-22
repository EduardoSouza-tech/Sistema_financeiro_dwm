"""
Script para executar a migração de segurança crítica:
Adiciona coluna empresa_id à tabela lancamentos para corrigir vazamento de dados entre empresas
"""
import psycopg2
import os
import sys
from config import POSTGRESQL_CONFIG, DATABASE_TYPE

def executar_migracao():
    """Executa o script SQL de migração"""
    
    print("\n" + "="*80)
    print("🔐 MIGRAÇÃO DE SEGURANÇA CRÍTICA")
    print("="*80)
    print("\nADICIONANDO COLUNA empresa_id À TABELA lancamentos")
    print("Isso corrige vulnerabilidade de vazamento de dados entre empresas\n")
    
    # Verificar se estamos usando PostgreSQL
    if DATABASE_TYPE != 'postgresql':
        print(f"❌ ERRO: Este script é para PostgreSQL, mas DATABASE_TYPE = '{DATABASE_TYPE}'")
        print("\nPara executar a migração:")
        print("1. Configure DATABASE_TYPE='postgresql' em config.py ou variáveis de ambiente")
        print("2. Execute novamente este script")
        return False
    
    # Conectar ao banco de dados
    try:
        print("🔌 Conectando ao banco de dados...")
        print(f"   Host: {POSTGRESQL_CONFIG['host']}")
        print(f"   Port: {POSTGRESQL_CONFIG['port']}")
        print(f"   Database: {POSTGRESQL_CONFIG['database']}")
        print(f"   User: {POSTGRESQL_CONFIG['user']}\n")
        
        conn = psycopg2.connect(
            host=POSTGRESQL_CONFIG['host'],
            port=POSTGRESQL_CONFIG['port'],
            user=POSTGRESQL_CONFIG['user'],
            password=POSTGRESQL_CONFIG['password'],
            dbname=POSTGRESQL_CONFIG['database']
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("✅ Conectado com sucesso!\n")
        
        # Ler o script SQL
        script_path = os.path.join(os.path.dirname(__file__), 'migration_add_empresa_id_lancamentos.sql')
        
        if not os.path.exists(script_path):
            print(f"❌ ERRO: Arquivo de migração não encontrado: {script_path}")
            return False
        
        print(f"📄 Lendo script: {os.path.basename(script_path)}\n")
        
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Executar o script
        print("⚙️  Executando migração...")
        print("-" * 80)
        
        cursor.execute(sql_script)
        
        # Buscar mensagens de retorno
        messages = cursor.fetchall()
        for msg in messages:
            print(f"   {msg[0]}")
        
        print("-" * 80)
        
        # Commit da transação
        conn.commit()
        print("\n✅ Migração executada com sucesso!")
        
        # Verificar resultados
        print("\n📊 Verificando resultados...")
        
        # Verificar se a coluna foi criada
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'lancamentos' AND column_name = 'empresa_id'
        """)
        
        coluna = cursor.fetchone()
        if coluna:
            print(f"   ✅ Coluna empresa_id criada: {coluna[1]} (Nullable: {coluna[2]})")
        else:
            print("   ❌ ERRO: Coluna empresa_id não foi criada!")
            return False
        
        # Contar lançamentos sem empresa_id
        cursor.execute("SELECT COUNT(*) FROM lancamentos WHERE empresa_id IS NULL")
        sem_empresa = cursor.fetchone()[0]
        
        # Contar total de lançamentos
        cursor.execute("SELECT COUNT(*) FROM lancamentos")
        total = cursor.fetchone()[0]
        
        print(f"\n📈 Estatísticas:")
        print(f"   Total de lançamentos: {total}")
        print(f"   Lançamentos com empresa_id: {total - sem_empresa}")
        print(f"   Lançamentos sem empresa_id: {sem_empresa}")
        
        if sem_empresa > 0:
            print("\n⚠️  AVISO: Existem lançamentos sem empresa_id!")
            print("\nPróximos passos:")
            
            # Verificar se há apenas uma empresa
            cursor.execute("SELECT COUNT(*) FROM empresas")
            num_empresas = cursor.fetchone()[0]
            
            if num_empresas == 1:
                cursor.execute("SELECT id, nome FROM empresas LIMIT 1")
                empresa = cursor.fetchone()
                print(f"\n   Existe apenas 1 empresa cadastrada: {empresa[1]} (ID: {empresa[0]})")
                print(f"\n   ✨ Você pode atribuir automaticamente executando:")
                print(f"      UPDATE lancamentos SET empresa_id = {empresa[0]} WHERE empresa_id IS NULL;")
            else:
                print(f"\n   Existem {num_empresas} empresas cadastradas")
                print("\n   Você precisa atribuir manualmente cada lançamento à empresa correta:")
                print("      UPDATE lancamentos SET empresa_id = <ID_EMPRESA> WHERE <CONDIÇÃO>;")
        else:
            print("\n   ✅ Todos os lançamentos têm empresa_id atribuído!")
        
        # Verificar índice
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'lancamentos' AND indexname = 'idx_lancamentos_empresa_id'
        """)
        
        indice = cursor.fetchone()
        if indice:
            print(f"\n   ✅ Índice criado: {indice[0]}")
        else:
            print("\n   ⚠️  AVISO: Índice idx_lancamentos_empresa_id não foi criado")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*80)
        print("\n🔒 SEGURANÇA: O sistema agora filtra lançamentos por empresa")
        print("\nPróximos passos:")
        print("1. Se houver lançamentos sem empresa_id, atribua-os manualmente")
        print("2. Teste o sistema com múltiplas empresas")
        print("3. Commit e deploy das mudanças no código")
        print("\n")
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ ERRO NO BANCO DE DADOS:")
        print(f"   {e}")
        if conn:
            conn.rollback()
            print("\n🔄 Rollback executado - nenhuma alteração foi feita")
        return False
        
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO:")
        print(f"   {e}")
        if conn:
            conn.rollback()
            print("\n🔄 Rollback executado - nenhuma alteração foi feita")
        return False


if __name__ == "__main__":
    sucesso = executar_migracao()
    sys.exit(0 if sucesso else 1)
