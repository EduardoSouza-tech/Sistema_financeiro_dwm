"""
🧹 LIMPEZA DE DUPLICATAS - EXTRATO BANCÁRIO
Script seguro que lista e remove duplicatas usando database_postgresql.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Carregar .env ANTES de importar database_postgresql
from dotenv import load_dotenv
load_dotenv()

from decimal import Decimal
from database_postgresql import get_db_connection
import psycopg2.extras

def executar_limpeza_duplicatas(empresa_id: int, executar_delete: bool = False):
    """
    Lista e opcionalmente remove duplicatas do extrato
    
    Args:
        empresa_id: ID da empresa
        executar_delete: Se True, executa a deleção. Se False, apenas lista
    """
    
    print("\n" + "="*80)
    print("🔍 ANÁLISE DE DUPLICATAS - EXTRATO BANCÁRIO")
    print("="*80)
    print(f"Empresa ID: {empresa_id}")
    print(f"Modo: {'DELEÇÃO ATIVA' if executar_delete else 'APENAS ANÁLISE'}")
    print("="*80 + "\n")
    
    try:
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 1. ANÁLISE INICIAL
            print("📊 PASSO 1: Contagem de registros\n")
            
            cursor.execute("SELECT COUNT(*) as total FROM lancamentos WHERE empresa_id = %s", (empresa_id,))
            total = cursor.fetchone()['total']
            print(f"   Total de lançamentos: {total:,}")
            
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM lancamentos 
                WHERE empresa_id = %s AND descricao LIKE '[EXTRATO]%%'
            """, (empresa_id,))
            total_extrato = cursor.fetchone()['total']
            print(f"   Lançamentos do [EXTRATO]: {total_extrato:,}\n")
            
            # 2. IDENTIFICAR DUPLICATAS
            print("-"*80)
            print("📋 PASSO 2: Identificar duplicatas\n")
            
            cursor.execute("""
                SELECT 
                    descricao,
                    valor,
                    data_vencimento,
                    tipo,
                    COUNT(*) as quantidade,
                    MIN(id) as id_mais_antigo,
                    MAX(id) as id_mais_recente,
                    ARRAY_AGG(id ORDER BY id) as todos_ids
                FROM lancamentos
                WHERE empresa_id = %s 
                  AND descricao LIKE '[EXTRATO]%%'
                GROUP BY descricao, valor, data_vencimento, tipo
                HAVING COUNT(*) > 1
                ORDER BY quantidade DESC, valor DESC
            """, (empresa_id,))
            
            duplicatas = cursor.fetchall()
            
            if not duplicatas:
                print("   ✅ Nenhuma duplicata encontrada!\n")
                return
            
            print(f"   ⚠️  Encontrados {len(duplicatas)} grupos de duplicatas:\n")
            
            total_registros_duplicados = 0
            
            for i, dup in enumerate(duplicatas[:20], 1):  # Mostrar primeiros 20
                qtd = dup['quantidade']
                total_registros_duplicados += (qtd - 1)  # Conta apenas os que serão deletados
                
                print(f"   {i}. {dup['descricao'][:60]}")
                print(f"      Valor: R$ {float(dup['valor']):,.2f} | Data: {dup['data_vencimento']} | Tipo: {dup['tipo']}")
                print(f"      Quantidade: {qtd}x | IDs: {dup['todos_ids']} → Manter: {dup['id_mais_recente']}")
                print()
            
            if len(duplicatas) > 20:
                restantes = len(duplicatas) - 20
                print(f"   ... e mais {restantes} grupos de duplicatas\n")
            
            # Contar TODOS os registros que serão deletados
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM lancamentos l
                WHERE l.empresa_id = %s
                  AND l.descricao LIKE '[EXTRATO]%%'
                  AND l.id NOT IN (
                    SELECT MAX(id) 
                    FROM lancamentos
                    WHERE empresa_id = %s
                      AND descricao LIKE '[EXTRATO]%%'
                    GROUP BY descricao, valor, data_vencimento, tipo
                  )
            """, (empresa_id, empresa_id))
            registros_para_deletar = cursor.fetchone()['total']
            
            print("-"*80)
            print(f"📊 RESUMO:")
            print(f"   • Grupos duplicados: {len(duplicatas)}")
            print(f"   • Registros a remover: {registros_para_deletar:,} (mantém 1 de cada grupo)")
            print(f"   • Registros a manter: {len(duplicatas)}\n")
            
            if not executar_delete:
                print("="*80)
                print("ℹ️  MODO ANÁLISE - Nenhuma deleção foi executada")
                print("="*80)
                print("\n💡 Para executar a limpeza, rode:")
                print(f"   python executar_limpeza_duplicatas.py --delete --empresa={empresa_id}\n")
                return
            
            # 3. CRIAR BACKUP
            print("="*80)
            print("💾 PASSO 3: Criando backup de segurança\n")
            
            cursor.execute("DROP TABLE IF EXISTS lancamentos_backup_duplicatas")
            conn.commit()
            
            cursor.execute("""
                CREATE TABLE lancamentos_backup_duplicatas AS
                SELECT l.*
                FROM lancamentos l
                WHERE l.empresa_id = %s
                  AND l.descricao LIKE '[EXTRATO]%%'
                  AND l.id NOT IN (
                    SELECT MAX(id) 
                    FROM lancamentos
                    WHERE empresa_id = %s
                      AND descricao LIKE '[EXTRATO]%%'
                    GROUP BY descricao, valor, data_vencimento, tipo
                  )
            """, (empresa_id, empresa_id))
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) as total FROM lancamentos_backup_duplicatas")
            backup_count = cursor.fetchone()['total']
            print(f"   ✅ Backup criado: {backup_count:,} registros salvos")
            print(f"   📁 Tabela: lancamentos_backup_duplicatas\n")
            
            # 4. DELETAR DUPLICATAS
            print("-"*80)
            print("🗑️  PASSO 4: Removendo duplicatas...\n")
            
            cursor.execute("""
                DELETE FROM lancamentos
                WHERE empresa_id = %s
                  AND descricao LIKE '[EXTRATO]%%'
                  AND id NOT IN (
                    SELECT MAX(id) 
                    FROM lancamentos
                    WHERE empresa_id = %s
                      AND descricao LIKE '[EXTRATO]%%'
                    GROUP BY descricao, valor, data_vencimento, tipo
                  )
            """, (empresa_id, empresa_id))
            deletados = cursor.rowcount
            conn.commit()
            
            print(f"   ✅ Removidos: {deletados:,} lançamentos duplicados\n")
            
            # 5. VERIFICAR RESULTADO
            print("="*80)
            print("📊 PASSO 5: Verificação final\n")
            
            cursor.execute("""
                SELECT COUNT(*) as total FROM lancamentos 
                WHERE empresa_id = %s AND descricao LIKE '[EXTRATO]%%'
            """, (empresa_id,))
            total_apos = cursor.fetchone()['total']
            print(f"   Lançamentos [EXTRATO] restantes: {total_apos:,}")
            
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM (
                    SELECT descricao, valor, data_vencimento, tipo
                    FROM lancamentos
                    WHERE empresa_id = %s 
                      AND descricao LIKE '[EXTRATO]%%'
                    GROUP BY descricao, valor, data_vencimento, tipo
                    HAVING COUNT(*) > 1
                ) as dup
            """, (empresa_id,))
            duplicatas_restantes = cursor.fetchone()['total']
            print(f"   Duplicatas restantes: {duplicatas_restantes}")
            
            if duplicatas_restantes == 0:
                print("\n   ✅ Todas as duplicatas foram removidas!")
            else:
                print(f"\n   ⚠️  Ainda há {duplicatas_restantes} duplicatas!")
            
            # 6. SALDO ATUALIZADO
            print("\n" + "="*80)
            print("💰 SALDOS DAS CONTAS BANCÁRIAS")
            print("="*80 + "\n")
            
            cursor.execute("""
                SELECT nome, banco, agencia, conta, saldo_inicial, saldo_atual
                FROM contas_bancarias
                WHERE empresa_id = %s AND ativa = true
                ORDER BY nome
            """, (empresa_id,))
            contas = cursor.fetchall()
            
            for conta in contas:
                print(f"   🏦 {conta['nome']}")
                print(f"      {conta['banco']} - {conta['agencia']}/{conta['conta']}")
                print(f"      Saldo Inicial: R$ {float(conta['saldo_inicial']):,.2f}")
                print(f"      Saldo Atual: R$ {float(conta['saldo_atual']):,.2f}")
                print()
            
            print("="*80)
            print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
            print("="*80)
            print("\n📋 Informações importantes:")
            print(f"   • Backup: lancamentos_backup_duplicatas ({backup_count:,} registros)")
            print("   • Para restaurar backup (se necessário):")
            print("     INSERT INTO lancamentos SELECT * FROM lancamentos_backup_duplicatas;")
            print("   • Para remover backup:")
            print("     DROP TABLE lancamentos_backup_duplicatas;")
            print()
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Limpeza de duplicatas do extrato bancário')
    parser.add_argument('--empresa', type=int, default=20, help='ID da empresa (padrão: 20)')
    parser.add_argument('--delete', action='store_true', help='Executar deleção (sem isso, apenas lista)')
    
    args = parser.parse_args()
    
    if args.delete:
        resposta = input(f"\n⚠️  Tem certeza que deseja DELETAR duplicatas da empresa {args.empresa}? (sim/não): ")
        if resposta.lower() != 'sim':
            print("Operação cancelada.")
            sys.exit(0)
    
    executar_limpeza_duplicatas(args.empresa, args.delete)
