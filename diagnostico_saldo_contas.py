"""
Script de Diagnóstico - Análise de Saldos por Conta Bancária
Verifica de onde vem cada saldo (extrato ou cálculo manual)
"""
import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import get_db_connection

def diagnosticar_saldos(empresa_id: int):
    """Diagnostica os saldos de todas as contas da empresa"""
    print("\n" + "="*80)
    print("🔍 DIAGNÓSTICO DE SALDOS - ANÁLISE POR CONTA")
    print("="*80 + "\n")
    
    try:
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            # 1. Listar todas as contas da empresa
            print("📋 CONTAS BANCÁRIAS DA EMPRESA:\n")
            cursor.execute("""
                SELECT id, nome, banco, saldo_inicial, ativa
                FROM contas_bancarias
                WHERE empresa_id = %s
                ORDER BY nome
            """, (empresa_id,))
            
            contas = cursor.fetchall()
            
            if not contas:
                print("❌ Nenhuma conta encontrada para esta empresa!\n")
                return
            
            print(f"✅ Total de contas: {len(contas)}\n")
            
            saldo_total = Decimal('0')
            
            for conta in contas:
                conta_id = conta['id']
                nome = conta['nome']
                banco = conta['banco']
                saldo_inicial = Decimal(str(conta['saldo_inicial']))
                ativa = conta['ativa']
                
                print("-" * 80)
                print(f"🏦 Conta: {nome}")
                print(f"   Banco: {banco}")
                print(f"   Saldo Inicial: R$ {saldo_inicial:,.2f}")
                print(f"   Status: {'✅ Ativa' if ativa else '❌ Inativa'}")
                
                # 2. Verificar se tem extrato importado
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_transacoes,
                        MIN(data) as primeira_data,
                        MAX(data) as ultima_data,
                        (SELECT saldo FROM transacoes_extrato 
                         WHERE empresa_id = %s AND conta_bancaria = %s 
                         ORDER BY data DESC, id DESC LIMIT 1) as saldo_atual_extrato
                    FROM transacoes_extrato
                    WHERE empresa_id = %s
                    AND conta_bancaria = %s
                """, (empresa_id, nome, empresa_id, nome))
                
                extrato_info = cursor.fetchone()
                total_transacoes = extrato_info['total_transacoes']
                
                if total_transacoes > 0:
                    print(f"\n   📊 EXTRATO BANCÁRIO:")
                    print(f"      ✅ {total_transacoes} transações importadas")
                    print(f"      📅 Período: {extrato_info['primeira_data']} a {extrato_info['ultima_data']}")
                    print(f"      💰 Saldo Atual (OFX): R$ {Decimal(str(extrato_info['saldo_atual_extrato'])):,.2f}")
                    
                    saldo_conta = Decimal(str(extrato_info['saldo_atual_extrato']))
                    fonte = "🏦 EXTRATO"
                else:
                    print(f"\n   ⚠️ SEM EXTRATO IMPORTADO")
                    print(f"      Usando cálculo manual (lançamentos)")
                    
                    # Calcular com lançamentos
                    cursor.execute("""
                        SELECT COALESCE(SUM(valor), 0) as total_receitas
                        FROM lancamentos
                        WHERE empresa_id = %s
                        AND conta_bancaria = %s
                        AND tipo = 'receita'
                        AND status = 'pago'
                    """, (empresa_id, nome))
                    total_receitas = Decimal(str(cursor.fetchone()['total_receitas']))
                    
                    cursor.execute("""
                        SELECT COALESCE(SUM(valor), 0) as total_despesas
                        FROM lancamentos
                        WHERE empresa_id = %s
                        AND conta_bancaria = %s
                        AND tipo = 'despesa'
                        AND status = 'pago'
                    """, (empresa_id, nome))
                    total_despesas = Decimal(str(cursor.fetchone()['total_despesas']))
                    
                    saldo_conta = saldo_inicial + total_receitas - total_despesas
                    
                    print(f"      💰 Receitas Pagas: R$ {total_receitas:,.2f}")
                    print(f"      💸 Despesas Pagas: R$ {total_despesas:,.2f}")
                    print(f"      💰 Saldo Calculado: R$ {saldo_conta:,.2f}")
                    
                    fonte = "💰 LANÇAMENTOS"
                
                print(f"\n   🎯 SALDO FINAL ({fonte}): R$ {saldo_conta:,.2f}")
                saldo_total += saldo_conta
            
            print("\n" + "="*80)
            print(f"💵 SALDO TOTAL DE TODAS AS CONTAS: R$ {saldo_total:,.2f}")
            print("="*80 + "\n")
            
            # 3. Mostrar resumo
            print("📊 RESUMO:\n")
            cursor.execute("""
                SELECT COUNT(DISTINCT conta_bancaria) as contas_com_extrato
                FROM transacoes_extrato
                WHERE empresa_id = %s
            """, (empresa_id,))
            contas_com_extrato = cursor.fetchone()['contas_com_extrato']
            
            print(f"   ✅ Total de contas: {len(contas)}")
            print(f"   🏦 Contas com extrato: {contas_com_extrato}")
            print(f"   💰 Contas sem extrato: {len(contas) - contas_com_extrato}")
            print(f"   💵 Saldo total somado: R$ {saldo_total:,.2f}")
            
            # 4. Verificar se o saldo total bate com o que o sistema mostra
            print(f"\n⚠️ IMPORTANTE:")
            print(f"   - Na tela 'Contas a Pagar/Receber', você vê: 'Saldo Total dos Bancos'")
            print(f"   - Esse valor é a SOMA de todas as contas acima")
            print(f"   - No 'Extrato Bancário', você vê o saldo de UMA CONTA específica")
            print(f"   - Por isso os valores podem ser diferentes!\n")
            
            cursor.close()
            
    except Exception as e:
        print(f"❌ Erro ao diagnosticar saldos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🔍 Script de Diagnóstico de Saldos\n")
    
    # Usar empresa padrão (COOPSERVICOS)
    empresa_id = 20
    print(f"📌 Analisando empresa ID: {empresa_id}\n")
    
    diagnosticar_saldos(empresa_id)
    
    print("\n✅ Diagnóstico concluído!\n")
