"""
Remove lançamentos duplicados [EXTRATO]
Mantém apenas o registro mais recente de cada duplicata
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time

def remover_duplicatas():
    """Remove duplicatas mantendo o mais recente"""
    
    # URL do banco Railway
    database_url = "postgresql://postgres:McRKKZdnRLbPqMDkkslqzTjSgTBMLSUJ@junction.proxy.rlwy.net:29725/railway"
    
    # Tentar conectar com retry
    max_tentativas = 5
    for tentativa in range(1, max_tentativas + 1):
        try:
            # Conectar ao banco
            print(f"🔌 Tentativa {tentativa}/{max_tentativas} - Conectando ao banco de dados...")
            conn = psycopg2.connect(
                database_url,
                connect_timeout=10,
                options='-c statement_timeout=300000',
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            conn.set_session(autocommit=False)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            print("✅ Conectado com sucesso!\n")
            break
            
        except psycopg2.OperationalError as e:
            if tentativa < max_tentativas:
                wait_time = tentativa * 2
                print(f"⚠️  Falha na conexão. Aguardando {wait_time}s antes de tentar novamente...")
                time.sleep(wait_time)
            else:
                print(f"❌ Erro de conexão após {max_tentativas} tentativas: {e}")
                print("\n💡 Possíveis soluções:")
                print("   1. Verifique se o servidor web_server.py está rodando (ele pode estar usando todas as conexões)")
                print("   2. Tente parar o web_server.py temporariamente")
                print("   3. Execute o script SQL manualmente no painel do Railway")
                return
    
    try:
        
        # 1. ANÁLISE INICIAL
        print("="*80)
        print("📊 ANÁLISE ANTES DA LIMPEZA")
        print("="*80)
        
        cursor.execute("SELECT COUNT(*) as total FROM lancamentos")
        total = cursor.fetchone()['total']
        print(f"Total de lançamentos: {total:,}")
        
        cursor.execute("SELECT COUNT(*) as total FROM lancamentos WHERE descricao LIKE '[EXTRATO]%'")
        total_extrato = cursor.fetchone()['total']
        print(f"Lançamentos com [EXTRATO]: {total_extrato:,}")
        
        # Contar duplicatas
        cursor.execute("""
            SELECT COUNT(*) as total_duplicatas
            FROM (
                SELECT descricao, valor, data_vencimento, tipo, empresa_id
                FROM lancamentos
                WHERE descricao LIKE '[EXTRATO]%'
                GROUP BY descricao, valor, data_vencimento, tipo, empresa_id
                HAVING COUNT(*) > 1
            ) as duplicatas
        """)
        total_grupos_duplicados = cursor.fetchone()['total_duplicatas']
        print(f"Grupos de duplicatas encontrados: {total_grupos_duplicados:,}")
        
        # Contar registros duplicados (exceto o que será mantido)
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM lancamentos l
            WHERE l.descricao LIKE '[EXTRATO]%'
              AND l.id NOT IN (
                SELECT MAX(id) 
                FROM lancamentos
                WHERE descricao LIKE '[EXTRATO]%'
                GROUP BY descricao, valor, data_vencimento, tipo, empresa_id
              )
        """)
        registros_para_deletar = cursor.fetchone()['total']
        print(f"Registros duplicados a serem removidos: {registros_para_deletar:,}\n")
        
        if registros_para_deletar == 0:
            print("✅ Não há duplicatas para remover!")
            conn.close()
            return
        
        # 2. BACKUP
        print("="*80)
        print("💾 CRIANDO BACKUP")
        print("="*80)
        
        # Apagar tabela de backup anterior se existir
        cursor.execute("DROP TABLE IF EXISTS lancamentos_backup_duplicatas")
        conn.commit()
        
        # Criar backup
        cursor.execute("""
            CREATE TABLE lancamentos_backup_duplicatas AS
            SELECT l.*
            FROM lancamentos l
            WHERE l.descricao LIKE '[EXTRATO]%'
              AND l.id NOT IN (
                SELECT MAX(id) 
                FROM lancamentos
                WHERE descricao LIKE '[EXTRATO]%'
                GROUP BY descricao, valor, data_vencimento, tipo, empresa_id
              )
        """)
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) as total FROM lancamentos_backup_duplicatas")
        backup_count = cursor.fetchone()['total']
        print(f"✅ Backup criado: {backup_count:,} registros salvos\n")
        
        # 3. DELETAR DUPLICATAS
        print("="*80)
        print("🗑️  REMOVENDO DUPLICATAS")
        print("="*80)
        
        cursor.execute("""
            DELETE FROM lancamentos
            WHERE descricao LIKE '[EXTRATO]%'
              AND id NOT IN (
                SELECT MAX(id) 
                FROM lancamentos
                WHERE descricao LIKE '[EXTRATO]%'
                GROUP BY descricao, valor, data_vencimento, tipo, empresa_id
              )
        """)
        deletados = cursor.rowcount
        conn.commit()
        
        print(f"✅ Removidos {deletados:,} lançamentos duplicados\n")
        
        # 4. ANÁLISE FINAL
        print("="*80)
        print("📊 ANÁLISE APÓS A LIMPEZA")
        print("="*80)
        
        cursor.execute("SELECT COUNT(*) as total FROM lancamentos")
        total_apos = cursor.fetchone()['total']
        print(f"Total de lançamentos: {total_apos:,}")
        
        cursor.execute("SELECT COUNT(*) as total FROM lancamentos WHERE descricao LIKE '[EXTRATO]%'")
        total_extrato_apos = cursor.fetchone()['total']
        print(f"Lançamentos com [EXTRATO]: {total_extrato_apos:,}")
        
        # Verificar se ainda há duplicatas
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM (
                SELECT descricao, valor, data_vencimento, tipo, empresa_id
                FROM lancamentos
                WHERE descricao LIKE '[EXTRATO]%'
                GROUP BY descricao, valor, data_vencimento, tipo, empresa_id
                HAVING COUNT(*) > 1
            ) as duplicatas
        """)
        duplicatas_restantes = cursor.fetchone()['total']
        print(f"Grupos de duplicatas restantes: {duplicatas_restantes:,}")
        
        # Verificar saldo da conta
        print("\n" + "="*80)
        print("💰 SALDO ATUALIZADO DA CONTA BANCÁRIA")
        print("="*80)
        
        cursor.execute("""
            SELECT banco, agencia, conta, saldo_inicial, saldo_atual
            FROM contas_bancarias
            WHERE id = 6
        """)
        conta = cursor.fetchone()
        if conta:
            print(f"Banco: {conta['banco']}")
            print(f"Agência/Conta: {conta['agencia']}/{conta['conta']}")
            print(f"Saldo Inicial: R$ {float(conta['saldo_inicial']):,.2f}")
            print(f"Saldo Atual: R$ {float(conta['saldo_atual']):,.2f}")
        
        print("\n" + "="*80)
        print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
        print("="*80)
        print(f"📌 Backup disponível na tabela: lancamentos_backup_duplicatas")
        print(f"📌 Para restaurar (se necessário): INSERT INTO lancamentos SELECT * FROM lancamentos_backup_duplicatas;")
        
        cursor.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"❌ Erro de conexão: {e}")
        print("\n💡 Tente novamente em alguns segundos...")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    remover_duplicatas()
