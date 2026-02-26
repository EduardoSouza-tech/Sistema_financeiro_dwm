"""
🔍 INVESTIGAÇÃO RÁPIDA - DIFERENÇA DE SALDO
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from decimal import Decimal
from database_postgresql import get_db_connection
import psycopg2.extras

empresa_id = 20

print("\n" + "="*80)
print("🔍 INVESTIG AÇÃO - DIFERENÇA DE SALDO")
print("="*80 + "\n")

try:
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 1. Buscar conta
        cursor.execute("""
            SELECT id, nome, banco, agencia, conta, saldo_inicial
            FROM contas_bancarias
            WHERE empresa_id = %s AND ativa = true
        """, (empresa_id,))
        
        conta = cursor.fetchone()
        conta_nome = conta['nome']
        
        print(f"🏦 CONTA: {conta_nome}")
        print(f"   Banco: {conta['banco']}")
        print(f"   Saldo Inicial: R$ {float(conta['saldo_inicial']):,.2f}\n")
        
        # 2. Saldo do extrato
        cursor.execute("""
            SELECT saldo FROM transacoes_extrato
            WHERE empresa_id = %s AND conta_bancaria = %s
            ORDER BY data DESC, id DESC LIMIT 1
        """, (empresa_id, conta_nome))
        
        saldo_extrato = Decimal(str(cursor.fetchone()['saldo']))
        print(f"📊 Saldo do EXTRATO: R$ {float(saldo_extrato):,.2f}\n")
        
        # 3. Lançamentos manuais
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN tipo = 'receita' THEN valor ELSE 0 END), 0) as receitas,
                COALESCE(SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END), 0) as despesas
            FROM lancamentos
            WHERE empresa_id = %s AND conta_bancaria = %s AND status = 'pago'
        """, (empresa_id, conta_nome))
        
        lanc = cursor.fetchone()
        receitas = Decimal(str(lanc['receitas']))
        despesas = Decimal(str(lanc['despesas']))
        saldo_calculado = Decimal(str(conta['saldo_inicial'])) + receitas - despesas
        
        print(f"📊 Saldo CALCULADO (lançamentos manuais):")
        print(f"   Saldo inicial: R$ {float(conta['saldo_inicial']):,.2f}")
        print(f"   + Receitas: R$ {float(receitas):,.2f}")
        print(f"   - Despesas: R$ {float(despesas):,.2f}")
        print(f"   = Total: R$ {float(saldo_calculado):,.2f}\n")
        
        # 4. Diferença
        diferenca = saldo_extrato - saldo_calculado
        print(f"⚖️  DIFERENÇA:")
        print(f"   Extrato:    R$ {float(saldo_extrato):,.2f}")
        print(f"   Calculado:  R$ {float(saldo_calculado):,.2f}")
        print(f"   Diferença:  R$ {float(diferenca):,.2f}\n")
        
        # 5. Verificar lançamentos [EXTRATO]
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COALESCE(SUM(CASE WHEN tipo = 'receita' THEN valor ELSE 0 END), 0) as receitas_extrato,
                   COALESCE(SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END), 0) as despesas_extrato
            FROM lancamentos
            WHERE empresa_id = %s 
              AND conta_bancaria = %s
              AND status = 'pago'
              AND descricao LIKE '[EXTRATO]%%'
        """, (empresa_id, conta_nome))
        
        extrato_lanc = cursor.fetchone()
        
        print("="*80)
        print("🔍 ANÁLISE DE LANÇAMENTOS [EXTRATO]")
        print("="*80)
        print(f"   Lançamentos manuais com [EXTRATO]: {extrato_lanc['total']}")
        
        if extrato_lanc['total'] > 0:
            rec_ext = Decimal(str(extrato_lanc['receitas_extrato']))
            desp_ext = Decimal(str(extrato_lanc['despesas_extrato']))
            impacto = rec_ext - desp_ext
            
            print(f"   Receitas [EXTRATO]: R$ {float(rec_ext):,.2f}")
            print(f"   Despesas [EXTRATO]: R$ {float(desp_ext):,.2f}")
            print(f"   Impacto no saldo: R$ {float(impacto):,.2f}\n")
            
            print("   ⚠️  PROBLEMA IDENTIFICADO:")
            print("   Lançamentos marcados com [EXTRATO] estão sendo contados")
            print("   DUAS VEZES: uma vez no extrato e outra vez nos lançamentos!")
            print(f"\n   💡 SOLUÇÃO:")
            print(f"   Se removermos os {extrato_lanc['total']} lançamentos [EXTRATO],")
            print(f"   o saldo calculado seria: R$ {float(saldo_calculado - impacto):,.2f}")
            print(f"   Diferença com extrato: R$ {float(saldo_extrato - (saldo_calculado - impacto)):,.2f}")
        else:
            print("   ✅ Nenhum lançamento [EXTRATO] encontrado")
            print("\n   ⚠️  A diferença tem outra causa:")
            print("   - Saldo inicial incorreto?")
            print("   - Transações não conciliadas?")
            print("   - Importações parciais do extrato?")
        
        # 6. Estatísticas do extrato
        cursor.execute("""
            SELECT COUNT(*) as total,
                   MIN(data) as primeira,
                   MAX(data) as ultima
            FROM transacoes_extrato
            WHERE empresa_id = %s AND conta_bancaria = %s
        """, (empresa_id, conta_nome))
        
        stats = cursor.fetchone()
        print(f"\n📋 EXTRATO BANCÁRIO:")
        print(f"   Total de transações: {stats['total']}")
        print(f"   Período: {stats['primeira']} até {stats['ultima']}")
        
        print("\n" + "="*80)
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
