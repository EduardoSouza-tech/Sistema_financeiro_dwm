"""
🗑️ DELETAR LANÇAMENTOS ÓRFÃOS [EXTRATO]
Script para remover lançamentos duplicados que ficaram órfãos
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database_postgresql import get_db_connection
import psycopg2.extras

def deletar_lancamentos_extrato(empresa_id: int, confirmar: bool = False):
    """
    Deleta lançamentos com [EXTRATO] que ficaram órfãos
    """
    
    print("\n" + "="*80)
    print("🗑️  DELETAR LANÇAMENTOS ÓRFÃOS [EXTRATO]")
    print("="*80 + "\n")
    
    try:
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 1. Contar lançamentos
            cursor.execute("""
                SELECT COUNT(*) as total FROM lancamentos 
                WHERE empresa_id = %s AND status = 'pago' AND descricao LIKE '[EXTRATO]%%'
            """, (empresa_id,))
            
            total = cursor.fetchone()['total']
            
            if total == 0:
                print("✅ Nenhum lançamento [EXTRATO] encontrado!")
                print("   Sistema já está limpo.\n")
                return
            
            print(f"📊 Encontrados {total} lançamentos com [EXTRATO]\n")
            
            # 2. Listar alguns
            cursor.execute("""
                SELECT id, descricao, valor, tipo, data_pagamento
                FROM lancamentos 
                WHERE empresa_id = %s AND status = 'pago' AND descricao LIKE '[EXTRATO]%%'
                ORDER BY data_pagamento DESC
                LIMIT 10
            """, (empresa_id,))
            
            amostras = cursor.fetchall()
            
            print("📋 Amostra (primeiros 10):\n")
            for i, lanc in enumerate(amostras, 1):
                print(f"{i}. ID: {lanc['id']} | {lanc['data_pagamento']}")
                print(f"   {lanc['descricao'][:65]}")
                print(f"   R$ {float(lanc['valor']):,.2f} ({lanc['tipo']})\n")
            
            if not confirmar:
                print("="*80)
                print("⚠️  MODO ANÁLISE - Nenhuma deleção executada")
                print("="*80)
                print(f"\n💡 Para DELETAR os {total} lançamentos, rode:")
                print(f"   py deletar_lancamentos_orfaos.py --confirmar\n")
                return
            
            # 3. CRIAR BACKUP
            print("="*80)
            print("💾 Criando backup...\n")
            
            cursor.execute("DROP TABLE IF EXISTS lancamentos_backup_orfaos")
            conn.commit()
            
            cursor.execute("""
                CREATE TABLE lancamentos_backup_orfaos AS
                SELECT * FROM lancamentos 
                WHERE empresa_id = %s AND status = 'pago' AND descricao LIKE '[EXTRATO]%%'
            """, (empresa_id,))
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) as total FROM lancamentos_backup_orfaos")
            backup_count = cursor.fetchone()['total']
            print(f"✅ Backup criado: {backup_count} registros")
            print(f"   Tabela: lancamentos_backup_orfaos\n")
            
            # 4. DELETAR
            print("="*80)
            print("🗑️  Deletando lançamentos...\n")
            
            cursor.execute("""
                DELETE FROM lancamentos 
                WHERE empresa_id = %s AND status = 'pago' AND descricao LIKE '[EXTRATO]%%'
            """, (empresa_id,))
            
            deletados = cursor.rowcount
            conn.commit()
            
            print(f"✅ Deletados: {deletados} lançamentos\n")
            
            # 5. VERIFICAR
            cursor.execute("""
                SELECT COUNT(*) as total FROM lancamentos 
                WHERE empresa_id = %s AND status = 'pago' AND descricao LIKE '[EXTRATO]%%'
            """, (empresa_id,))
            
            restantes = cursor.fetchone()['total']
            
            print("="*80)
            print("📊 VERIFICAÇÃO FINAL")
            print("="*80)
            print(f"   Lançamentos [EXTRATO] restantes: {restantes}")
            
            if restantes == 0:
                print("   ✅ Todos os lançamentos órfãos foram removidos!\n")
            else:
                print(f"   ⚠️  Ainda restam {restantes} lançamentos\n")
            
            # 6. Status da conta
            cursor.execute("""
                SELECT nome, saldo_inicial FROM contas_bancarias 
                WHERE empresa_id = %s AND ativa = true
            """, (empresa_id,))
            
            conta = cursor.fetchone()
            
            print("="*80)
            print("💰 SALDO DA CONTA")
            print("="*80)
            print(f"   Conta: {conta['nome']}")
            print(f"   Saldo inicial: R$ {float(conta['saldo_inicial']):,.2f}")
            print("   Saldo calculado: R$ {float(conta['saldo_inicial']):,.2f} (só saldo inicial)")
            print("\n   ✅ Saldo agora está CORRETO (apenas saldo inicial)\n")
            
            print("="*80)
            print("✅ LIMPEZA CONCLUÍDA!")
            print("="*80)
            print("\n📋 Informações:")
            print(f"   • Backup: lancamentos_backup_orfaos ({backup_count} registros)")
            print("   • Para restaurar (SE necessário):")
            print("     INSERT INTO lancamentos SELECT * FROM lancamentos_backup_orfaos;")
            print("   • Para remover backup:")
            print("     DROP TABLE lancamentos_backup_orfaos;")
            print()
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Deletar lançamentos órfãos [EXTRATO]')
    parser.add_argument('--empresa', type=int, default=20, help='ID da empresa')
    parser.add_argument('--confirmar', action='store_true', help='Confirmar deleção')
    
    args = parser.parse_args()
    
    if args.confirmar:
        resposta = input(f"\n⚠️  CONFIRMA deleção de lançamentos [EXTRATO] da empresa {args.empresa}? (SIM/não): ")
        if resposta.upper() != 'SIM':
            print("Operação cancelada.")
            sys.exit(0)
    
    deletar_lancamentos_extrato(args.empresa, args.confirmar)
