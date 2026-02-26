"""
🔍 INVESTIGAÇÃO COMPLETA - DIFERENÇA DE SALDO
Analisa por que o saldo está -R$ 1.062,08 diferente do esperado
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from decimal import Decimal
from database_postgresql import get_db_connection
import psycopg2.extras

def investigar_diferenca_completa(empresa_id: int, conta_id: int = None):
    """
    Investiga a diferença de saldo completa
    """
    
    print("\n" + "="*80)
    print("🔍 INVESTIGAÇÃO COMPLETA - DIFERENÇA DE SALDO")
    print("="*80)
    print(f"Empresa ID: {empresa_id}")
    print("="*80 + "\n")
    
    try:
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 1. BUSCAR CONTAS BANCÁRIAS
            print("🏦 PASSO 1: Identificar contas bancárias\n")
            
            if conta_id:
                cursor.execute("""
                    SELECT id, nome, banco, agencia, conta, saldo_inicial
                    FROM contas_bancarias
                    WHERE empresa_id = %s AND id = %s
                """, (empresa_id, conta_id))
            else:
                cursor.execute("""
                    SELECT id, nome, banco, agencia, conta, saldo_inicial
                    FROM contas_bancarias
                    WHERE empresa_id = %s AND ativa = true
                    ORDER BY nome
                """, (empresa_id,))
            
            contas = cursor.fetchall()
            
            if not contas:
                print("❌ Nenhuma conta encontrada!\n")
                return
            
            print(f"   Total de contas: {len(contas)}\n")
            
            diferenca_total = Decimal('0')
            
            for conta in contas:
                print("-"*80)
                print(f"🏦 CONTA: {conta['nome']}")
                print(f"   Banco: {conta['banco']} | Ag/Conta: {conta['agencia']}/{conta['conta']}")
                print(f"   Saldo Inicial: R$ {float(conta['saldo_inicial']):,.2f}")
                print()
                
                conta_nome = conta['nome']
                conta_id_atual = conta['id']
                
                # 2. SALDO DO EXTRATO (última transação)
                print("   📊 Método 1: SALDO DO EXTRATO (última transação)\n")
                
                cursor.execute("""
                    SELECT saldo, data, id, descricao, valor, tipo
                    FROM transacoes_extrato
                    WHERE empresa_id = %s AND conta_bancaria = %s
                    ORDER BY data DESC, id DESC
                    LIMIT 1
                """, (empresa_id, conta_nome))
                
                ultima_transacao = cursor.fetchone()
                
                if ultima_transacao:
                    saldo_extrato = Decimal(str(ultima_transacao['saldo']))
                    print(f"      Última transação ID: {ultima_transacao['id']}")
                    print(f"      Data: {ultima_transacao['data']}")
                    print(f"      Descrição: {ultima_transacao['descricao'][:60]}")
                    print(f"      Valor: R$ {float(ultima_transacao['valor']):,.2f} ({ultima_transacao['tipo']})")
                    print(f"      ➜ Saldo do extrato: R$ {float(saldo_extrato):,.2f}")
                else:
                    saldo_extrato = None
                    print("      ⚠️  Nenhuma transação de extrato encontrada!")
                
                print()
                
                # 3. SALDO CALCULADO (saldo_inicial + receitas - despesas manuais)
                print("   📊 Método 2: SALDO CALCULADO (lançamentos manuais)\n")
                
                # Receitas pagas
                cursor.execute("""
                    SELECT COALESCE(SUM(valor), 0) as total
                    FROM lancamentos
                    WHERE empresa_id = %s 
                      AND conta_bancaria = %s
                      AND tipo = 'receita'
                      AND status = 'pago'
                """, (empresa_id, conta_nome))
                receitas = Decimal(str(cursor.fetchone()['total']))
                
                # Despesas pagas
                cursor.execute("""
                    SELECT COALESCE(SUM(valor), 0) as total
                    FROM lancamentos
                    WHERE empresa_id = %s 
                      AND conta_bancaria = %s
                      AND tipo = 'despesa'
                      AND status = 'pago'
                """, (empresa_id, conta_nome))
                despesas = Decimal(str(cursor.fetchone()['total']))
                
                saldo_calculado = Decimal(str(conta['saldo_inicial'])) + receitas - despesas
                
                print(f"      Saldo Inicial: R$ {float(conta['saldo_inicial']):,.2f}")
                print(f"      + Receitas pagas: R$ {float(receitas):,.2f}")
                print(f"      - Despesas pagas: R$ {float(despesas):,.2f}")
                print(f"      ➜ Saldo calculado: R$ {float(saldo_calculado):,.2f}")
                print()
                
                # 4. SALDO QUE O SISTEMA USA (prioriza extrato)
                print("   📊 Método 3: SALDO QUE O SISTEMA USA\n")
                
                if saldo_extrato is not None:
                    saldo_usado = saldo_extrato
                    metodo = "Extrato (prioritário)"
                else:
                    saldo_usado = saldo_calculado
                    metodo = "Calculado (fallback)"
                
                print(f"      Método usado: {metodo}")
                print(f"      ➜ Saldo usado pelo sistema: R$ {float(saldo_usado):,.2f}")
                print()
                
                # 5. COMPARAÇÃO
                print("   ⚖️  COMPARAÇÃO:\n")
                
                if saldo_extrato is not None:
                    diferenca = saldo_extrato - saldo_calculado
                    print(f"      Saldo do extrato: R$ {float(saldo_extrato):,.2f}")
                    print(f"      Saldo calculado:  R$ {float(saldo_calculado):,.2f}")
                    print(f"      Diferença:        R$ {float(diferenca):,.2f}")
                    
                    if abs(diferenca) > Decimal('0.01'):
                        print(f"\n      ⚠️  DIFERENÇA DETECTADA: R$ {float(diferenca):,.2f}")
                        diferenca_total += diferenca
                    else:
                        print("\n      ✅ Saldos conferem!")
                else:
                    print("      ℹ️  Sem extrato para comparar")
                
                print()
                
                # 6. ANÁLISE DE LANÇAMENTOS MANUAIS
                print("   🔍 ANÁLISE: Lançamentos manuais nesta conta\n")
                
                cursor.execute("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN tipo = 'receita' THEN valor ELSE 0 END) as total_receitas,
                           SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END) as total_despesas
                    FROM lancamentos
                    WHERE empresa_id = %s 
                      AND conta_bancaria = %s
                      AND status = 'pago'
                """, (empresa_id, conta_nome))
                
                stats = cursor.fetchone()
                print(f"      Total de lançamentos PAGOS: {stats['total']}")
                print(f"      Total receitas: R$ {float(stats['total_receitas'] or 0):,.2f}")
                print(f"      Total despesas: R$ {float(stats['total_despesas'] or 0):,.2f}")
                
                # Verificar lançamentos com [EXTRATO]
                cursor.execute("""
                    SELECT COUNT(*) as total
                    FROM lancamentos
                    WHERE empresa_id = %s 
                      AND conta_bancaria = %s
                      AND status = 'pago'
                      AND descricao LIKE '[EXTRATO]%'
                """, (empresa_id, conta_nome))
                
                lancamentos_extrato = cursor.fetchone()['total']
                print(f"      Lançamentos com [EXTRATO]: {lancamentos_extrato}")
                
                if lancamentos_extrato > 0:
                    print("\n      ⚠️  ALERTA: Há lançamentos manuais marcados como [EXTRATO]!")
                    print("      Isso pode causar contagem dupla (extrato + lançamento manual)\n")
                
                print()
                
                # 7. TRANSAÇÕES DO EXTRATO
                print("   📋 ANÁLISE: Transações do extrato\n")
                
                cursor.execute("""
                    SELECT COUNT(*) as total,
                           MIN(data) as primeira_data,
                           MAX(data) as ultima_data,
                           SUM(CASE WHEN tipo = 'CREDITO' THEN valor ELSE 0 END) as total_creditos,
                           SUM(CASE WHEN tipo = 'DEBITO' THEN ABS(valor) ELSE 0 END) as total_debitos
                    FROM transacoes_extrato
                    WHERE empresa_id = %s AND conta_bancaria = %s
                """, (empresa_id, conta_nome))
                
                stats_extrato = cursor.fetchone()
                print(f"      Total de transações: {stats_extrato['total']}")
                print(f"      Período: {stats_extrato['primeira_data']} até {stats_extrato['ultima_data']}")
                print(f"      Total créditos: R$ {float(stats_extrato['total_creditos'] or 0):,.2f}")
                print(f"      Total débitos: R$ {float(stats_extrato['total_debitos'] or 0):,.2f}")
                print()
            
            # RESUMO FINAL
            print("="*80)
            print("📊 RESUMO GERAL")
            print("="*80)
            print(f"   Diferença total detectada: R$ {float(diferenca_total):,.2f}")
            
            if abs(diferenca_total - Decimal('-1062.08')) < Decimal('1.00'):
                print("\n   ✅ Esta diferença BATE com os R$ -1.062,08 esperados!")
                print("\n   💡 PROVÁVEL CAUSA:")
                print("      Lançamentos manuais com [EXTRATO] estão sendo contados")
                print("      duas vezes: uma no extrato e outra nos lançamentos manuais.")
                print("\n   🔧 SOLUÇÃO:")
                print("      Remover ou marcar como 'conciliado' os lançamentos manuais")
                print("      que já estão no extrato bancário.")
            elif abs(diferenca_total) < Decimal('0.01'):
                print("\n   ✅ Saldos estão corretos!")
            else:
                print(f"\n   ⚠️  Diferença encontrada: R$ {float(diferenca_total):,.2f}")
                print("      Mas não bate exatamente com os R$ -1.062,08 esperados.")
                print("      Investigação adicional necessária.")
            
            print()
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Investigação completa de diferença de saldo')
    parser.add_argument('--empresa', type=int, default=20, help='ID da empresa (padrão: 20)')
    parser.add_argument('--conta', type=int, help='ID da conta específica (opcional)')
    
    args = parser.parse_args()
    
    investigar_diferenca_completa(args.empresa, args.conta)
