"""
Verifica se a última importação OFX foi salva no banco
"""

import psycopg2
import psycopg2.extras
from datetime import datetime

# Credenciais Railway
DB_CONFIG = {
    'host': 'centerbeam.proxy.rlwy.net',
    'port': 12659,
    'database': 'railway',
    'user': 'postgres',
    'password': 'JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT'
}

def log(msg, tipo='INFO'):
    simbolos = {'INFO': 'ℹ️', 'OK': '✅', 'WARNING': '⚠️', 'ERROR': '❌', 'SEARCH': '🔍'}
    print(f"{simbolos.get(tipo, 'ℹ️')} {msg}")

def separador(titulo=""):
    print("\n" + "="*80)
    if titulo:
        print(f"  {titulo}")
        print("="*80)

def main():
    conta_bancaria = "SICREDI COOPERATIVA - 0258/78895-2"
    empresa_id = 20  # COOPSERVICOS
    
    separador("VERIFICAÇÃO DE IMPORTAÇÕES NO BANCO")
    
    log(f"Conta: {conta_bancaria}", 'INFO')
    log(f"Empresa ID: {empresa_id}", 'INFO')
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        log("Conectado ao banco Railway", 'OK')
        
        separador("1. IMPORTAÇÕES RECENTES (últimas 24h)")
        
        cursor.execute("""
            SELECT 
                importacao_id,
                COUNT(*) as qtd_transacoes,
                MIN(data) as data_inicio,
                MAX(data) as data_fim,
                empresa_id,
                conta_bancaria,
                MIN(created_at) as importado_em
            FROM transacoes_extrato
            WHERE conta_bancaria = %s
            AND created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY importacao_id, empresa_id, conta_bancaria
            ORDER BY MIN(created_at) DESC
            LIMIT 5
        """, (conta_bancaria,))
        
        importacoes_recentes = cursor.fetchall()
        
        if importacoes_recentes:
            log(f"📋 {len(importacoes_recentes)} importação(ões) encontrada(s) nas últimas 24h:", 'OK')
            for i, imp in enumerate(importacoes_recentes, 1):
                print(f"\n   [{i}] IMPORTAÇÃO")
                print(f"       ID: {imp['importacao_id']}")
                print(f"       Empresa ID: {imp['empresa_id']}")
                print(f"       Conta: {imp['conta_bancaria']}")
                print(f"       Transações: {imp['qtd_transacoes']}")
                print(f"       Período: {imp['data_inicio']} a {imp['data_fim']}")
                print(f"       Importado em: {imp['importado_em']}")
                
                # Verificar se a empresa_id está correta
                if imp['empresa_id'] != empresa_id:
                    print(f"       ⚠️ ATENÇÃO: empresa_id {imp['empresa_id']} diferente do esperado ({empresa_id})!")
        else:
            log("⚠️ Nenhuma importação encontrada nas últimas 24h", 'WARNING')
        
        separador("2. TODAS AS IMPORTAÇÕES DESTA CONTA")
        
        cursor.execute("""
            SELECT 
                importacao_id,
                COUNT(*) as qtd_transacoes,
                MIN(data) as data_inicio,
                MAX(data) as data_fim,
                empresa_id,
                conta_bancaria
            FROM transacoes_extrato
            WHERE conta_bancaria = %s
            GROUP BY importacao_id, empresa_id, conta_bancaria
            ORDER BY MAX(data) DESC
        """, (conta_bancaria,))
        
        todas_importacoes = cursor.fetchall()
        
        if todas_importacoes:
            log(f"📊 Total de importações históricas: {len(todas_importacoes)}", 'INFO')
            for imp in todas_importacoes:
                empresa_match = "✅" if imp['empresa_id'] == empresa_id else "❌ DIFERENTE!"
                print(f"   • {imp['data_inicio']} a {imp['data_fim']} | {imp['qtd_transacoes']} trans. | Empresa {imp['empresa_id']} {empresa_match}")
        else:
            log("❌ Nenhuma transação encontrada para esta conta!", 'ERROR')
        
        separador("3. TOTAL POR EMPRESA_ID")
        
        cursor.execute("""
            SELECT 
                empresa_id,
                COUNT(*) as total_transacoes,
                COUNT(DISTINCT importacao_id) as total_importacoes,
                MIN(data) as data_inicio,
                MAX(data) as data_fim
            FROM transacoes_extrato
            WHERE conta_bancaria = %s
            GROUP BY empresa_id
        """, (conta_bancaria,))
        
        por_empresa = cursor.fetchall()
        
        if por_empresa:
            log("📊 Transações agrupadas por empresa:", 'INFO')
            for emp in por_empresa:
                status = "✅ CORRETA" if emp['empresa_id'] == empresa_id else "❌ EMPRESA ERRADA!"
                print(f"   Empresa {emp['empresa_id']}: {emp['total_transacoes']} transações, {emp['total_importacoes']} importações {status}")
        
        separador("4. FILTRO SIMULADO DO FRONTEND")
        
        # Simular a query que o frontend está fazendo
        data_inicio = '2026-01-01'
        data_fim = '2026-01-31'
        
        log(f"Simulando query: empresa_id={empresa_id}, data_inicio={data_inicio}, data_fim={data_fim}", 'SEARCH')
        
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM transacoes_extrato
            WHERE empresa_id = %s
            AND data >= %s
            AND data <= %s
        """, (empresa_id, data_inicio, data_fim))
        
        resultado = cursor.fetchone()
        
        if resultado['total'] > 0:
            log(f"✅ Query retornou {resultado['total']} transação(ões)", 'OK')
        else:
            log(f"❌ Query retornou 0 transações - PROBLEMA CONFIRMADO!", 'ERROR')
            
            # Verificar sem filtro de empresa
            cursor.execute("""
                SELECT COUNT(*) as total, empresa_id
                FROM transacoes_extrato
                WHERE data >= %s
                AND data <= %s
                GROUP BY empresa_id
            """, (data_inicio, data_fim))
            
            todas = cursor.fetchall()
            if todas:
                log("📊 Transações existem mas em outras empresas:", 'WARNING')
                for t in todas:
                    print(f"   • Empresa {t['empresa_id']}: {t['total']} transações")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        
    except Exception as e:
        log(f"ERRO: {e}", 'ERROR')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
