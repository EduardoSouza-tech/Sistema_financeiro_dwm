"""
Investigação de Lançamentos Manuais vs Extrato
Verifica se há lançamentos manuais interferindo no cálculo do saldo
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import psycopg2.extras
from decimal import Decimal
from database_postgresql import get_db_connection

def investigar_lancamentos_manuais():
    print("\n" + "="*80)
    print("🔍 INVESTIGAÇÃO: LANÇAMENTOS MANUAIS vs EXTRATO")
    print("="*80)
    print("\n❓ PROBLEMA:")
    print("   Saldo correto do extrato:  -R$ 40.810,10")
    print("   Saldo mostrado no sistema: -R$ 41.872,18")
    print("   Diferença:                -R$  1.062,08")
    print("\n   💡 HIPÓTESE: Há lançamentos manuais sendo somados junto com o extrato!")
    print("="*80 + "\n")
    
    empresa_id = 20
    conta_nome = "SICREDI COOPERATIVA - 0258/78895-2"
    
    try:
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 1. Verificar lançamentos manuais na conta
            print("📋 PASSO 1: Buscar lançamentos manuais na conta\n")
            
            cursor.execute("""
                SELECT 
                    id,
                    descricao,
                    tipo,
                    valor,
                    data_vencimento,
                    data_pagamento,
                    status,
                    categoria,
                    subcategoria
                FROM lancamentos
                WHERE empresa_id = %s
                AND conta_bancaria = %s
                AND status = 'pago'
                ORDER BY data_pagamento DESC, id DESC
            """, (empresa_id, conta_nome))
            
            lancamentos = cursor.fetchall()
            
            print(f"   Total de lançamentos manuais PAGOS: {len(lancamentos)}\n")
            
            if len(lancamentos) == 0:
                print("   ✅ Nenhum lançamento manual encontrado!")
                print("   ⚠️ O problema não é lançamento manual duplicado.\n")
            else:
                print("   ⚠️ ENCONTRADOS LANÇAMENTOS MANUAIS!\n")
                
                # Calcular total de receitas e despesas
                total_receitas = sum(Decimal(str(l['valor'])) for l in lancamentos if l['tipo'] == 'receita')
                total_despesas = sum(Decimal(str(l['valor'])) for l in lancamentos if l['tipo'] == 'despesa')
                impacto_saldo = total_receitas - total_despesas
                
                print(f"   💰 Receitas manuais: R$ {total_receitas:,.2f}")
                print(f"   💸 Despesas manuais: R$ {total_despesas:,.2f}")
                print(f"   📊 Impacto no saldo: R$ {impacto_saldo:,.2f}")
                print(f"\n   🔍 Comparando com a diferença:")
                print(f"      Diferença esperada: -R$ 1.062,08")
                print(f"      Impacto lançamentos: R$ {impacto_saldo:,.2f}")
                
                if abs(impacto_saldo - Decimal('-1062.08')) < Decimal('0.01'):
                    print(f"\n   ✅ BINGO! Os lançamentos manuais explicam a diferença!")
                else:
                    print(f"\n   ⚠️ Diferença não bate exatamente...")
                
                # Mostrar primeiros 10 lançamentos
                print(f"\n   📝 Primeiros 10 lançamentos (mais recentes):")
                for i, l in enumerate(lancamentos[:10], 1):
                    tipo_emoji = "💰" if l['tipo'] == 'receita' else "💸"
                    print(f"      {i}. {tipo_emoji} ID:{l['id']} | {l['descricao'][:40]:40} | R$ {float(l['valor']):,.2f} | {l['data_pagamento']}")
                
                if len(lancamentos) > 10:
                    print(f"      ... e mais {len(lancamentos) - 10} lançamentos")
            
            print("\n" + "-"*80 + "\n")
            
            # 2. Verificar se o endpoint /api/contas está somando lançamentos manuais
            print("🔍 PASSO 2: Como o endpoint /api/contas calcula o saldo?\n")
            
            # Simular lógica do endpoint
            cursor.execute("""
                SELECT saldo, data, id
                FROM transacoes_extrato
                WHERE empresa_id = %s
                AND conta_bancaria = %s
                ORDER BY data DESC, id DESC
                LIMIT 1
            """, (empresa_id, conta_nome))
            
            ultima_extrato = cursor.fetchone()
            
            if ultima_extrato:
                saldo_extrato = Decimal(str(ultima_extrato['saldo']))
                print(f"   🏦 Saldo do extrato (última transação): R$ {saldo_extrato:,.2f}")
                print(f"      Data: {ultima_extrato['data']}, ID: {ultima_extrato['id']}")
                print(f"\n   ✅ O endpoint /api/contas retorna: R$ {saldo_extrato:,.2f}")
                print(f"      (Não soma lançamentos quando há extrato)")
            
            print("\n" + "-"*80 + "\n")
            
            # 3. Verificar compatibilidade: transações do extrato vs lançamentos manuais
            print("🔍 PASSO 3: Verificar se há duplicação (extrato + manual)\n")
            
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM transacoes_extrato
                WHERE empresa_id = %s
                AND conta_bancaria = %s
            """, (empresa_id, conta_nome))
            total_extrato = cursor.fetchone()['total']
            
            print(f"   📊 Transações no extrato: {total_extrato}")
            print(f"   📝 Lançamentos manuais pagos: {len(lancamentos)}")
            
            if len(lancamentos) > 0:
                print(f"\n   ⚠️ PROBLEMA IDENTIFICADO:")
                print(f"   Você tem {len(lancamentos)} lançamentos manuais na mesma conta do extrato!")
                print(f"\n   🔧 SOLUÇÃO:")
                print(f"   1. Os lançamentos manuais podem estar duplicando transações do extrato")
                print(f"   2. Recomendado: Deletar os lançamentos manuais OU")
                print(f"   3. Mover lançamentos manuais para outra conta (sem extrato)")
            
            print("\n" + "-"*80 + "\n")
            
            # 4. Mostrar qual seria o saldo correto
            print("📊 PASSO 4: Cálculo do saldo CORRETO\n")
            
            cursor.execute("""
                SELECT saldo_inicial
                FROM contas_bancarias
                WHERE empresa_id = %s AND nome = %s
            """, (empresa_id, conta_nome))
            conta_info = cursor.fetchone()
            saldo_inicial = Decimal(str(conta_info['saldo_inicial']))
            
            print(f"   Saldo inicial da conta: R$ {saldo_inicial:,.2f}")
            print(f"   Saldo do extrato (final): R$ {saldo_extrato:,.2f}")
            print(f"\n   ✅ Saldo CORRETO a ser exibido: R$ {saldo_extrato:,.2f}")
            print(f"      (Não deve somar lançamentos manuais quando há extrato)")
            
            # Verificar data_inicio da conta
            cursor.execute("""
                SELECT data_inicio, tipo_saldo_inicial
                FROM contas_bancarias
                WHERE empresa_id = %s AND nome = %s
            """, (empresa_id, conta_nome))
            conta_config = cursor.fetchone()
            
            if conta_config['data_inicio']:
                print(f"\n   📅 Data início configurada: {conta_config['data_inicio']}")
                print(f"   📌 Tipo saldo inicial: {conta_config['tipo_saldo_inicial']}")
            else:
                print(f"\n   ⚠️ Data início NÃO configurada")
            
            print("\n" + "-"*80 + "\n")
            
            # 5. Verificar se problema está no frontend somando lançamentos
            print("🔍 PASSO 5: Verificar se frontend soma lançamentos + extrato\n")
            print("   📍 Função: atualizarSaldoTotalBancos() em static/app.js")
            print("   📍 Endpoint: GET /api/contas")
            print("\n   ✅ Endpoint retorna apenas saldo do extrato")
            print("   ✅ Frontend não deveria somar lançamentos manuais")
            
            if len(lancamentos) > 0:
                print(f"\n   ❓ PERGUNTA: Por que há {len(lancamentos)} lançamentos manuais?")
                print(f"   - Foram criados ANTES da importação do extrato?")
                print(f"   - São duplicatas das transações do extrato?")
                print(f"   - Deveriam estar em outra conta?")
            
            cursor.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigar_lancamentos_manuais()
    print("\n✅ Investigação concluída!\n")
