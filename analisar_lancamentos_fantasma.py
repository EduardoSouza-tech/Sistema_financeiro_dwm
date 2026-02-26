"""
🚨 ANÁLISE URGENTE - LANÇAMENTOS FANTASMA
Investiga lançamentos que não deveriam existir após deleção do extrato
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
print("🚨 ANÁLISE URGENTE - LANÇAMENTOS FANTASMA")
print("="*80 + "\n")

try:
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 1. Verificar conta bancária
        cursor.execute("""
            SELECT id, nome, banco, saldo_inicial
            FROM contas_bancarias
            WHERE empresa_id = %s AND ativa = true
        """, (empresa_id,))
        
        conta = cursor.fetchone()
        conta_nome = conta['nome']
        
        print(f"🏦 CONTA: {conta_nome}")
        print(f"   Saldo Inicial: R$ {float(conta['saldo_inicial']):,.2f}\n")
        
        # 2. Verificar transacoes_extrato
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM transacoes_extrato
            WHERE empresa_id = %s AND conta_bancaria = %s
        """, (empresa_id, conta_nome))
        
        total_extrato = cursor.fetchone()['total']
        
        print("="*80)
        print("📊 STATUS DO EXTRATO BANCÁRIO")
        print("="*80)
        print(f"   Transações no extrato (transacoes_extrato): {total_extrato}")
        
        if total_extrato == 0:
            print("   ✅ Extrato foi deletado com sucesso!\n")
        else:
            print(f"   ⚠️  Ainda há {total_extrato} transações no extrato\n")
        
        # 3. Verificar lançamentos
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM lancamentos
            WHERE empresa_id = %s 
              AND conta_bancaria = %s
              AND status = 'pago'
        """, (empresa_id, conta_nome))
        
        total_lancamentos = cursor.fetchone()['total']
        
        print("="*80)
        print("📊 STATUS DOS LANÇAMENTOS")
        print("="*80)
        print(f"   Total de lançamentos PAGOS: {total_lancamentos}")
        
        # 4. Lançamentos com [EXTRATO]
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COALESCE(SUM(CASE WHEN tipo = 'receita' THEN valor ELSE 0 END), 0) as receitas,
                   COALESCE(SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END), 0) as despesas
            FROM lancamentos
            WHERE empresa_id = %s 
              AND conta_bancaria = %s
              AND status = 'pago'
              AND descricao LIKE '[EXTRATO]%'
        """, (empresa_id, conta_nome))
        
        extrato_lanc = cursor.fetchone()
        
        print(f"   Lançamentos com [EXTRATO]: {extrato_lanc['total']}")
        
        if extrato_lanc['total'] > 0:
            receitas = Decimal(str(extrato_lanc['receitas']))
            despesas = Decimal(str(extrato_lanc['despesas']))
            
            print(f"   Receitas [EXTRATO]: R$ {float(receitas):,.2f}")
            print(f"   Despesas [EXTRATO]: R$ {float(despesas):,.2f}")
            
            saldo_fantasma = Decimal(str(conta['saldo_inicial'])) + receitas - despesas
            
            print(f"\n   🚨 PROBLEMA CRÍTICO:")
            print(f"   Você deletou o extrato, mas {extrato_lanc['total']} lançamentos")
            print(f"   marcados como [EXTRATO] PERMANECERAM na tabela lancamentos!")
            print(f"\n   💰 IMPACTO NO SALDO:")
            print(f"   Saldo inicial: R$ {float(conta['saldo_inicial']):,.2f}")
            print(f"   Saldo mostrado: R$ {float(saldo_fantasma):,.2f}")
            print(f"   ERRO: Lançamentos fantasma alterando o saldo!\n")
        else:
            print("   ✅ Nenhum lançamento [EXTRATO] encontrado\n")
        
        # 5. Verificar lançamentos sem [EXTRATO]
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM lancamentos
            WHERE empresa_id = %s 
              AND conta_bancaria = %s
              AND status = 'pago'
              AND descricao NOT LIKE '[EXTRATO]%'
        """, (empresa_id, conta_nome))
        
        total_sem_extrato = cursor.fetchone()['total']
        print(f"   Lançamentos manuais (sem [EXTRATO]): {total_sem_extrato}")
        
        # 6. Listar alguns lançamentos [EXTRATO]
        if extrato_lanc['total'] > 0:
            print("\n" + "="*80)
            print("📋 AMOSTRA DE LANÇAMENTOS [EXTRATO] (primeiros 10)")
            print("="*80 + "\n")
            
            cursor.execute("""
                SELECT id, descricao, valor, tipo, data_vencimento, data_pagamento, 
                       categoria, subcategoria
                FROM lancamentos
                WHERE empresa_id = %s 
                  AND conta_bancaria = %s
                  AND status = 'pago'
                  AND descricao LIKE '[EXTRATO]%'
                ORDER BY data_pagamento DESC, id DESC
                LIMIT 10
            """, (empresa_id, conta_nome))
            
            amostras = cursor.fetchall()
            
            for i, lanc in enumerate(amostras, 1):
                print(f"{i}. ID: {lanc['id']}")
                print(f"   Descrição: {lanc['descricao'][:70]}")
                print(f"   Valor: R$ {float(lanc['valor']):,.2f} ({lanc['tipo']})")
                print(f"   Vencimento: {lanc['data_vencimento']} | Pagamento: {lanc['data_pagamento']}")
                print(f"   Categoria: {lanc['categoria']} > {lanc.get('subcategoria', 'N/A')}")
                print()
        
        # 7. DIAGNÓSTICO FINAL
        print("="*80)
        print("🔍 DIAGNÓSTICO")
        print("="*80)
        
        if total_extrato == 0 and extrato_lanc['total'] > 0:
            print("\n⛔ PROBLEMA CONFIRMADO:")
            print(f"   • Extrato deletado: SIM ({total_extrato} transações)")
            print(f"   • Lançamentos [EXTRATO] deletados: NÃO ({extrato_lanc['total']} restantes)")
            print("\n🔧 CAUSA:")
            print("   • Sistema importa OFX criando registros em DUAS tabelas:")
            print("     1. transacoes_extrato (correto)")
            print("     2. lancamentos com [EXTRATO] (ERRADO - causa duplicação)")
            print("   • Ao deletar extrato, apenas transacoes_extrato é limpo")
            print("   • Lançamentos [EXTRATO] ficam órfãos, criando 'fantasmas'")
            print("\n⚠️  IMPACTO:")
            print("   • Saldo exibido INCORRETO")
            print("   • Contas a Pagar/Receber mostram transações fantasma")
            print("   • Relatórios financeiros com dados duplicados")
            print("\n💾 SOLUÇÃO URGENTE:")
            print(f"   Deletar os {extrato_lanc['total']} lançamentos [EXTRATO] órfãos")
            
        elif total_extrato > 0 and extrato_lanc['total'] > 0:
            print("\n⚠️  DUPLICAÇÃO ATIVA:")
            print(f"   • Extrato: {total_extrato} transações")
            print(f"   • Lançamentos [EXTRATO]: {extrato_lanc['total']}")
            print("   • Dados sendo contados DUAS VEZES no sistema!")
            
        else:
            print("\n✅ Sistema limpo (por enquanto)")
            print("   • Mas o BUG de duplicação ainda existe no código de importação!")
        
        print("\n" + "="*80)
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
