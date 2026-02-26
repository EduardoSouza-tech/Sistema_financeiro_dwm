"""
Investigação da diferença entre Saldo Total e Saldo do Extrato
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Carregar .env ANTES de importar database_postgresql
from dotenv import load_dotenv
load_dotenv()

import psycopg2.extras
from decimal import Decimal
from database_postgresql import get_db_connection

def investigar_diferenca():
    print("\n" + "="*80)
    print("🔍 INVESTIGAÇÃO: DIFERENÇA DE SALDO")
    print("="*80)
    print("\n❓ PROBLEMA:")
    print("   Saldo Total dos Bancos: -R$ 41.872,18")
    print("   Saldo final do extrato: -R$ 40.810,10")
    print("   Diferença:              -R$  1.062,08")
    print("\n" + "="*80 + "\n")
    
    empresa_id = 20  # COOPSERVICOS
    
    try:
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 1. Verificar quantas contas existem
            print("📋 PASSO 1: Verificar contas cadastradas\n")
            cursor.execute("""
                SELECT id, nome, banco, saldo_inicial, ativa
                FROM contas_bancarias
                WHERE empresa_id = %s
                ORDER BY nome
            """, (empresa_id,))
            contas = cursor.fetchall()
            
            print(f"   Total de contas: {len(contas)}")
            for conta in contas:
                print(f"   - ID: {conta['id']}, Nome: {conta['nome']}, Banco: {conta['banco']}, Ativa: {conta['ativa']}")
            
            print("\n" + "-"*80 + "\n")
            
            # 2. Para cada conta, verificar o saldo
            print("💰 PASSO 2: Calcular saldo de cada conta\n")
            
            total_somado = Decimal('0')
            
            for conta in contas:
                nome = conta['nome']
                saldo_inicial = Decimal(str(conta['saldo_inicial']))
                
                print(f"🏦 Conta: {nome}")
                print(f"   Saldo inicial: R$ {saldo_inicial:,.2f}")
                
                # a) Verificar extrato
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        MIN(data) as primeira_data,
                        MAX(data) as ultima_data
                    FROM transacoes_extrato
                    WHERE empresa_id = %s AND conta_bancaria = %s
                """, (empresa_id, nome))
                extrato_resumo = cursor.fetchone()
                
                if extrato_resumo['total'] > 0:
                    print(f"   📊 Extrato: {extrato_resumo['total']} transações")
                    print(f"   📅 Período: {extrato_resumo['primeira_data']} a {extrato_resumo['ultima_data']}")
                    
                    # Buscar saldo da última transação
                    cursor.execute("""
                        SELECT saldo, data, id
                        FROM transacoes_extrato
                        WHERE empresa_id = %s AND conta_bancaria = %s
                        ORDER BY data DESC, id DESC
                        LIMIT 1
                    """, (empresa_id, nome))
                    ultima = cursor.fetchone()
                    
                    saldo_extrato = Decimal(str(ultima['saldo']))
                    print(f"   💰 Saldo do extrato (última transação): R$ {saldo_extrato:,.2f}")
                    print(f"      Data: {ultima['data']}, ID: {ultima['id']}")
                    
                    saldo_usado = saldo_extrato
                    fonte = "EXTRATO"
                else:
                    print(f"   ⚠️ SEM EXTRATO")
                    
                    # Calcular com lançamentos
                    cursor.execute("""
                        SELECT COALESCE(SUM(valor), 0) as total
                        FROM lancamentos
                        WHERE empresa_id = %s
                        AND conta_bancaria = %s
                        AND tipo = 'receita'
                        AND status = 'pago'
                    """, (empresa_id, nome))
                    receitas = Decimal(str(cursor.fetchone()['total']))
                    
                    cursor.execute("""
                        SELECT COALESCE(SUM(valor), 0) as total
                        FROM lancamentos
                        WHERE empresa_id = %s
                        AND conta_bancaria = %s
                        AND tipo = 'despesa'
                        AND status = 'pago'
                    """, (empresa_id, nome))
                    despesas = Decimal(str(cursor.fetchone()['total']))
                    
                    saldo_usado = saldo_inicial + receitas - despesas
                    print(f"   💰 Receitas: R$ {receitas:,.2f}")
                    print(f"   💸 Despesas: R$ {despesas:,.2f}")
                    print(f"   💰 Saldo calculado: R$ {saldo_usado:,.2f}")
                    
                    fonte = "LANÇAMENTOS"
                
                print(f"   🎯 SALDO USADO ({fonte}): R$ {saldo_usado:,.2f}")
                total_somado += saldo_usado
                print()
            
            print("-"*80 + "\n")
            
            # 3. Mostrar total
            print("📊 PASSO 3: Saldo total somado\n")
            print(f"   💵 Total calculado: R$ {total_somado:,.2f}")
            print(f"   📱 Valor na tela:   -R$ 41.872,18")
            
            diferenca = total_somado - Decimal('-41872.18')
            print(f"   ➖ Diferença:       R$ {diferenca:,.2f}")
            
            print("\n" + "-"*80 + "\n")
            
            # 4. Verificar o que o endpoint /api/contas retorna
            print("🔍 PASSO 4: Simular resposta do endpoint /api/contas\n")
            
            for conta in contas:
                nome = conta['nome']
                
                # Mesma lógica do endpoint
                cursor.execute("""
                    SELECT saldo, data, id
                    FROM transacoes_extrato
                    WHERE empresa_id = %s
                    AND conta_bancaria = %s
                    ORDER BY data DESC, id DESC
                    LIMIT 1
                """, (empresa_id, nome))
                
                ultima_transacao_extrato = cursor.fetchone()
                
                if ultima_transacao_extrato and ultima_transacao_extrato['saldo'] is not None:
                    saldo_real = float(ultima_transacao_extrato['saldo'])
                    print(f"   🏦 {nome}: R$ {saldo_real:,.2f} (do extrato)")
                else:
                    # Calcular
                    cursor.execute("""
                        SELECT COALESCE(SUM(valor), 0) as total_receitas
                        FROM lancamentos
                        WHERE empresa_id = %s
                        AND conta_bancaria = %s
                        AND tipo = 'receita'
                        AND status = 'pago'
                    """, (empresa_id, nome))
                    total_receitas = float(cursor.fetchone()['total_receitas'] or 0)
                    
                    cursor.execute("""
                        SELECT COALESCE(SUM(valor), 0) as total_despesas
                        FROM lancamentos
                        WHERE empresa_id = %s
                        AND conta_bancaria = %s
                        AND tipo = 'despesa'
                        AND status = 'pago'
                    """, (empresa_id, nome))
                    total_despesas = float(cursor.fetchone()['total_despesas'] or 0)
                    
                    saldo_real = float(conta['saldo_inicial']) + total_receitas - total_despesas
                    print(f"   💰 {nome}: R$ {saldo_real:,.2f} (calculado)")
            
            print("\n" + "-"*80 + "\n")
            
            # 5. Verificar se há contas inativas sendo somadas
            print("🔍 PASSO 5: Verificar contas inativas\n")
            cursor.execute("""
                SELECT COUNT(*) as total, COUNT(CASE WHEN ativa = false THEN 1 END) as inativas
                FROM contas_bancarias
                WHERE empresa_id = %s
            """, (empresa_id,))
            resumo = cursor.fetchone()
            print(f"   Total de contas: {resumo['total']}")
            print(f"   Contas inativas: {resumo['inativas']}")
            
            if resumo['inativas'] > 0:
                print(f"\n   ⚠️ ATENÇÃO: Existem {resumo['inativas']} conta(s) inativa(s)")
                print(f"   ❓ O sistema pode estar somando conta inativa no total!")
            
            print("\n" + "-"*80 + "\n")
            
            # 6. Verificar se atualizarSaldoTotalBancos filtra por ativa
            print("🔍 PASSO 6: Verificar se frontend filtra por conta ativa\n")
            print("   📝 Função JavaScript: atualizarSaldoTotalBancos()")
            print("   📍 Arquivo: static/app.js")
            print("   ❓ Verifica se filtra contas inativas antes de somar?")
            
            cursor.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigar_diferenca()
    print("\n✅ Investigação concluída!\n")
