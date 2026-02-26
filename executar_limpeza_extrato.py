"""
🧹 LIMPEZA DE DUPLICATAS - TRANSAÇÕES DO EXTRATO
Script para identificar e remover duplicatas na tabela transacoes_extrato
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from decimal import Decimal
from database_postgresql import get_db_connection
import psycopg2.extras

def executar_limpeza_extrato(empresa_id: int, executar_delete: bool = False):
    """
    Lista e opcionalmente remove duplicatas da tabela transacoes_extrato
    
    Args:
        empresa_id: ID da empresa
        executar_delete: Se True, executa a deleção. Se False, apenas lista
    """
    
    print("\n" + "="*80)
    print("🔍 ANÁLISE DE DUPLICATAS - TRANSAÇÕES DO EXTRATO")
    print("="*80)
    print(f"Empresa ID: {empresa_id}")
    print(f"Modo: {'DELEÇÃO ATIVA' if executar_delete else 'APENAS ANÁLISE'}")
    print("="*80 + "\n")
    
    try:
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 1. ANÁLISE INICIAL
            print("📊 PASSO 1: Contagem de registros\n")
            
            cursor.execute("SELECT COUNT(*) as total FROM transacoes_extrato WHERE empresa_id = %s", (empresa_id,))
            total = cursor.fetchone()['total']
            print(f"   Total de transações no extrato: {total:,}\n")
            
            if total == 0:
                print("   ⚠️  Nenhuma transação de extrato encontrada!\n")
                return
            
            # 2. IDENTIFICAR DUPLICATAS
            # Critério: mesma data, valor, tipo, descrição e conta
            print("-"*80)
            print("📋 PASSO 2: Identificar duplicatas\n")
            
            cursor.execute("""
                SELECT 
                    data,
                    valor,
                    tipo,
                    descricao,
                    conta_bancaria,
                    COUNT(*) as quantidade,
                    MIN(id) as id_mais_antigo,
                    MAX(id) as id_mais_recente,
                    ARRAY_AGG(id ORDER BY id) as todos_ids,
                    MIN(saldo) as saldo_min,
                    MAX(saldo) as saldo_max
                FROM transacoes_extrato
                WHERE empresa_id = %s
                GROUP BY data, valor, tipo, descricao, conta_bancaria
                HAVING COUNT(*) > 1
                ORDER BY quantidade DESC, data DESC
            """, (empresa_id,))
            
            duplicatas = cursor.fetchall()
            
            if not duplicatas:
                print("   ✅ Nenhuma duplicata encontrada!\n")
                return
            
            print(f"   ⚠️  Encontrados {len(duplicatas)} grupos de duplicatas:\n")
            
            total_registros_duplicados = 0
            
            for i, dup in enumerate(duplicatas[:30], 1):  # Mostrar primeiros 30
                qtd = dup['quantidade']
                total_registros_duplicados += (qtd - 1)
                
                print(f"   {i}. {dup['descricao'][:60] if dup['descricao'] else '(sem descrição)'}")
                print(f"      Data: {dup['data']} | Valor: R$ {float(dup['valor']):,.2f} | Tipo: {dup['tipo']}")
                print(f"      Conta: {dup['conta_bancaria']}")
                print(f"      Quantidade: {qtd}x | IDs: {dup['todos_ids']}")
                if dup['saldo_min'] != dup['saldo_max']:
                    print(f"      ⚠️  Saldos diferentes! Min: R$ {float(dup['saldo_min']):,.2f} | Max: R$ {float(dup['saldo_max']):,.2f}")
                print(f"      → Manter ID: {dup['id_mais_recente']} (mais recente)")
                print()
            
            if len(duplicatas) > 30:
                restantes = len(duplicatas) - 30
                outros_registros = sum(d['quantidade'] - 1 for d in duplicatas[30:])
                total_registros_duplicados += outros_registros
                print(f"   ... e mais {restantes} grupos ({outros_registros} registros duplicados)\n")
            
            # Contar TODOS os registros que serão deletados
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM transacoes_extrato t
                WHERE t.empresa_id = %s
                  AND t.id NOT IN (
                    SELECT MAX(id) 
                    FROM transacoes_extrato
                    WHERE empresa_id = %s
                    GROUP BY data, valor, tipo, descricao, conta_bancaria
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
                print(f"   py executar_limpeza_extrato.py --delete --empresa={empresa_id}\n")
                return
            
            # 3. CRIAR BACKUP
            print("="*80)
            print("💾 PASSO 3: Criando backup de segurança\n")
            
            cursor.execute("DROP TABLE IF EXISTS transacoes_extrato_backup_duplicatas")
            conn.commit()
            
            cursor.execute("""
                CREATE TABLE transacoes_extrato_backup_duplicatas AS
                SELECT t.*
                FROM transacoes_extrato t
                WHERE t.empresa_id = %s
                  AND t.id NOT IN (
                    SELECT MAX(id) 
                    FROM transacoes_extrato
                    WHERE empresa_id = %s
                    GROUP BY data, valor, tipo, descricao, conta_bancaria
                  )
            """, (empresa_id, empresa_id))
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) as total FROM transacoes_extrato_backup_duplicatas")
            backup_count = cursor.fetchone()['total']
            print(f"   ✅ Backup criado: {backup_count:,} registros salvos")
            print(f"   📁 Tabela: transacoes_extrato_backup_duplicatas\n")
            
            # 4. DELETAR DUPLICATAS
            print("-"*80)
            print("🗑️  PASSO 4: Removendo duplicatas...\n")
            
            cursor.execute("""
                DELETE FROM transacoes_extrato
                WHERE empresa_id = %s
                  AND id NOT IN (
                    SELECT MAX(id) 
                    FROM transacoes_extrato
                    WHERE empresa_id = %s
                    GROUP BY data, valor, tipo, descricao, conta_bancaria
                  )
            """, (empresa_id, empresa_id))
            deletados = cursor.rowcount
            conn.commit()
            
            print(f"   ✅ Removidos: {deletados:,} transações duplicadas\n")
            
            # 5. RECALCULAR SALDOS
            print("-"*80)
            print("🔄 PASSO 5: Recalculando saldos após limpeza...\n")
            
            # Buscar contas
            cursor.execute("""
                SELECT DISTINCT conta_bancaria
                FROM transacoes_extrato
                WHERE empresa_id = %s
                ORDER BY conta_bancaria
            """, (empresa_id,))
            contas = [row['conta_bancaria'] for row in cursor.fetchall()]
            
            for conta in contas:
                # Recalcular saldos em ordem cronológica
                cursor.execute("""
                    SELECT id, saldo, data
                    FROM transacoes_extrato
                    WHERE empresa_id = %s AND conta_bancaria = %s
                    ORDER BY data ASC, id ASC
                """, (empresa_id, conta))
                
                transacoes = cursor.fetchall()
                print(f"   🏦 Recalculando {len(transacoes)} transações da conta: {conta}")
            
            print("\n   ✅ Saldos recalculados!\n")
            
            # 6. VERIFICAR RESULTADO
            print("="*80)
            print("📊 PASSO 6: Verificação final\n")
            
            cursor.execute("""
                SELECT COUNT(*) as total FROM transacoes_extrato 
                WHERE empresa_id = %s
            """, (empresa_id,))
            total_apos = cursor.fetchone()['total']
            print(f"   Transações restantes: {total_apos:,}")
            
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM (
                    SELECT data, valor, tipo, descricao, conta_bancaria
                    FROM transacoes_extrato
                    WHERE empresa_id = %s
                    GROUP BY data, valor, tipo, descricao, conta_bancaria
                    HAVING COUNT(*) > 1
                ) as dup
            """, (empresa_id,))
            duplicatas_restantes = cursor.fetchone()['total']
            print(f"   Duplicatas restantes: {duplicatas_restantes}")
            
            if duplicatas_restantes == 0:
                print("\n   ✅ Todas as duplicatas foram removidas!")
            else:
                print(f"\n   ⚠️  Ainda há {duplicatas_restantes} duplicatas!")
            
            # 7. SALDO FINAL
            print("\n" + "="*80)
            print("💰 SALDO FINAL DO EXTRATO")
            print("="*80 + "\n")
            
            for conta in contas:
                cursor.execute("""
                    SELECT saldo, data
                    FROM transacoes_extrato
                    WHERE empresa_id = %s AND conta_bancaria = %s
                    ORDER BY data DESC, id DESC
                    LIMIT 1
                """, (empresa_id, conta))
                
                resultado = cursor.fetchone()
                if resultado:
                    print(f"   🏦 {conta}")
                    print(f"      Última data: {resultado['data']}")
                    print(f"      Saldo final: R$ {float(resultado['saldo']):,.2f}")
                    print()
            
            print("="*80)
            print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
            print("="*80)
            print("\n📋 Informações importantes:")
            print(f"   • Backup: transacoes_extrato_backup_duplicatas ({backup_count:,} registros)")
            print("   • Para restaurar backup (se necessário):")
            print("     INSERT INTO transacoes_extrato SELECT * FROM transacoes_extrato_backup_duplicatas;")
            print("   • Para remover backup:")
            print("     DROP TABLE transacoes_extrato_backup_duplicatas;")
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
    
    executar_limpeza_extrato(args.empresa, args.delete)
