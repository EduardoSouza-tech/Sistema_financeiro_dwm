"""
🚨 ANÁLISE RÁPIDA - LANÇAMENTOS FANTASMA
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from decimal import Decimal
from database_postgresql import get_db_connection
import psycopg2.extras

print("\n" + "="*80)
print("🚨 ANÁLISE URGENTE - LANÇAMENTOS FANTASMA")
print("="*80 + "\n")

try:
    with get_db_connection(empresa_id=20) as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 1. Conta
        cursor.execute("SELECT nome, saldo_inicial FROM contas_bancarias WHERE empresa_id = 20 AND ativa = true")
        conta = cursor.fetchone()
        conta_nome = conta['nome']
        
        print(f"🏦 CONTA: {conta_nome}")
        print(f"   Saldo Inicial: R$ {float(conta['saldo_inicial']):,.2f}\n")
        
        # 2. Extrato
        cursor.execute("SELECT COUNT(*) as total FROM transacoes_extrato WHERE empresa_id = 20")
        total_extrato = cursor.fetchone()['total']
        
        print("="*80)
        print("EXTRATO BANCÁRIO (transacoes_extrato)")
        print("="*80)
        print(f"Total de transações: {total_extrato}")
        if total_extrato == 0:
            print("✅ Extrato foi DELETADO\n")
        else:
            print(f"⚠️  Extrato ainda tem {total_extrato} transações\n")
        
        # 3. Lançamentos TOTAIS
        cursor.execute("SELECT COUNT(*) as total FROM lancamentos WHERE empresa_id = 20 AND status = 'pago'")
        total_lanc = cursor.fetchone()['total']
        
        print("="*80)
        print("LANÇAMENTOS (tabela lancamentos)")
        print("="*80)
        print(f"Total de lançamentos PAGOS: {total_lanc}\n")
        
        # 4. Lançamentos com [EXTRATO] - query separada
        cursor.execute("""
            SELECT id, descricao, valor, tipo 
            FROM lancamentos 
            WHERE empresa_id = 20 AND status = 'pago' AND descricao LIKE '[EXTRATO]%'
            LIMIT 5
        """)
        amostras = cursor.fetchall()
        
        cursor.execute("""
            SELECT COUNT(*) as total FROM lancamentos 
            WHERE empresa_id = 20 AND status = 'pago' AND descricao LIKE '[EXTRATO]%'
        """)
        total_extrato_lanc = cursor.fetchone()['total']
        
        print(f"Lançamentos com tag [EXTRATO]: {total_extrato_lanc}")
        
        if total_extrato_lanc > 0:
            print(f"\n🚨 PROBLEMA CRÍTICO CONFIRMADO!")
            print(f"   • Extrato deletado: {total_extrato} transações")
            print(f"   • Lançamentos [EXTRATO] órfãos: {total_extrato_lanc}")
            print(f"\n   ⚠️  Esses {total_extrato_lanc} lançamentos estão causando:")
            print("   • Saldo incorreto")
            print("   • Transações fantasma em Contas a Pagar/Receber")
            print("   • Relatórios duplicados")
            
            # Calcular impacto
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN tipo = 'receita' THEN valor ELSE 0 END) as receitas,
                    SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END) as despesas
                FROM lancamentos 
                WHERE empresa_id = 20 AND status = 'pago' AND descricao LIKE '[EXTRATO]%'
            """)
            valores = cursor.fetchone()
            receitas = Decimal(str(valores['receitas'] or 0))
            despesas = Decimal(str(valores['despesas'] or 0))
            
            print(f"\n   💰 Valores afetados:")
            print(f"   Receitas fantasma: R$ {float(receitas):,.2f}")
            print(f"   Despesas fantasma: R$ {float(despesas):,.2f}")
            
            saldo_com_fantasma = Decimal(str(conta['saldo_inicial'])) + receitas - despesas
            print(f"\n   Saldo inicial correto: R$ {float(conta['saldo_inicial']):,.2f}")
            print(f"   Saldo sendo mostrado: R$ {float(saldo_com_fantasma):,.2f}")
            print(f"   ERRO: R$ {float(saldo_com_fantasma - Decimal(str(conta['saldo_inicial']))):,.2f}")
            
            print(f"\n📋 Amostra (primeiros 5):")
            for i, lanc in enumerate(amostras, 1):
                print(f"\n{i}. ID: {lanc['id']}")
                print(f"   {lanc['descricao'][:60]}")
                print(f"   R$ {float(lanc['valor']):,.2f} ({lanc['tipo']})")
        else:
            print("✅ Nenhum lançamento [EXTRATO] encontrado")
        
        # 5. Lançamentos sem [EXTRATO]
        cursor.execute("""
            SELECT COUNT(*) as total FROM lancamentos 
            WHERE empresa_id = 20 AND status = 'pago' AND descricao NOT LIKE '[EXTRATO]%'
        """)
        total_sem = cursor.fetchone()['total']
        print(f"\nLançamentos manuais legítimos: {total_sem}")
        
        print("\n" + "="*80)
        print("CONCLUSÃO")
        print("="*80)
        
        if total_extrato == 0 and total_extrato_lanc > 0:
            print("\n⛔ BUG CRÍTICO CONFIRMADO:")
            print("   Sistema cria lançamentos duplicados durante importação OFX")
            print("   Quando extrato é deletado, lançamentos ficam órfãos\n")
            print("🔧 AÇÕES NECESSÁRIAS:")
            print(f"   1. URGENTE: Deletar {total_extrato_lanc} lançamentos [EXTRATO]")
            print("   2. CRÍTICO: Corrigir código de importação OFX")
            print("   3. RECOMENDADO: Adicionar CASCADE DELETE ou trigger")
        
        print()
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
