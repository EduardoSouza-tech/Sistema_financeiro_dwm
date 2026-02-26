"""
Diagnostica conflito de período no OFX
"""

import psycopg2
import psycopg2.extras
from datetime import date

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
    # Dados da tentativa de importação (do console)
    conta_bancaria = "SICREDI COOPERATIVA - 0258/78895-2"
    periodo_inicio = date(2026, 1, 2)  # 02/01/2026
    periodo_fim = date(2026, 1, 30)    # 30/01/2026
    empresa_id = 20  # COOPSERVICOS
    
    separador("DIAGNÓSTICO DE CONFLITO - IMPORTAÇÃO OFX")
    
    log(f"Conta: {conta_bancaria}", 'INFO')
    log(f"Período tentado: {periodo_inicio.strftime('%d/%m/%Y')} até {periodo_fim.strftime('%d/%m/%Y')}", 'INFO')
    log(f"Empresa ID: {empresa_id}", 'INFO')
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        log("Conectado ao banco Railway", 'OK')
        
        separador("1. TRANSAÇÕES ÓRFÃS (sem importacao_id)")
        
        cursor.execute("""
            SELECT 
                id,
                data,
                tipo,
                valor,
                descricao
            FROM transacoes_extrato
            WHERE empresa_id = %s 
            AND conta_bancaria = %s 
            AND (importacao_id IS NULL OR importacao_id = '')
            ORDER BY data DESC
            LIMIT 10
        """, (empresa_id, conta_bancaria))
        
        orfas = cursor.fetchall()
        
        if orfas:
            log(f"⚠️ {len(orfas)} transação(ões) órfã(s) encontrada(s):", 'WARNING')
            for i, t in enumerate(orfas, 1):
                print(f"   [{i}] ID={t['id']} | {t['data']} | {t['tipo']} | R$ {float(t['valor']):,.2f} | {t['descricao'][:50]}")
        else:
            log("✅ Nenhuma transação órfã encontrada", 'OK')
        
        separador("2. IMPORTAÇÕES EXISTENTES (com importacao_id)")
        
        cursor.execute("""
            SELECT 
                importacao_id,
                MIN(data) as inicio,
                MAX(data) as fim,
                COUNT(*) as qtd_transacoes,
                SUM(CASE WHEN tipo = 'CREDITO' THEN valor ELSE 0 END) as total_credito,
                SUM(CASE WHEN tipo = 'DEBITO' THEN ABS(valor) ELSE 0 END) as total_debito
            FROM transacoes_extrato
            WHERE empresa_id = %s 
            AND conta_bancaria = %s
            AND importacao_id IS NOT NULL 
            AND importacao_id != ''
            GROUP BY importacao_id
            ORDER BY MAX(data) DESC
        """, (empresa_id, conta_bancaria))
        
        importacoes = cursor.fetchall()
        
        if importacoes:
            log(f"📋 {len(importacoes)} importação(ões) encontrada(s):", 'INFO')
            for i, imp in enumerate(importacoes, 1):
                inicio = imp['inicio']
                fim = imp['fim']
                
                # Verificar se há sobreposição
                tem_overlap = (periodo_inicio <= fim and periodo_fim >= inicio)
                status = "❌ CONFLITO!" if tem_overlap else "✅ OK"
                
                print(f"\n   [{i}] {status}")
                print(f"       ID Importação: {imp['importacao_id']}")
                print(f"       Período: {inicio.strftime('%d/%m/%Y')} até {fim.strftime('%d/%m/%Y')}")
                print(f"       Transações: {imp['qtd_transacoes']}")
                print(f"       Créditos: R$ {float(imp['total_credito'] or 0):,.2f}")
                print(f"       Débitos: R$ {float(imp['total_debito'] or 0):,.2f}")
                
                if tem_overlap:
                    print(f"       ⚠️ Este período SOBREPÕE ao período que você está tentando importar!")
                    
                    # Mostrar algumas transações desta importação
                    cursor.execute("""
                        SELECT id, data, tipo, valor, descricao
                        FROM transacoes_extrato
                        WHERE importacao_id = %s
                        ORDER BY data ASC
                        LIMIT 5
                    """, (imp['importacao_id'],))
                    
                    amostras = cursor.fetchall()
                    print(f"       📊 Primeiras transações desta importação:")
                    for t in amostras:
                        print(f"          • {t['data']} | {t['tipo']} | R$ {float(t['valor']):,.2f} | {t['descricao'][:40]}")
        else:
            log("✅ Nenhuma importação existente encontrada", 'OK')
        
        separador("3. TOTAL DE TRANSAÇÕES NA CONTA")
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN importacao_id IS NULL OR importacao_id = '' THEN 1 END) as sem_importacao,
                COUNT(CASE WHEN importacao_id IS NOT NULL AND importacao_id != '' THEN 1 END) as com_importacao
            FROM transacoes_extrato
            WHERE empresa_id = %s 
            AND conta_bancaria = %s
        """, (empresa_id, conta_bancaria))
        
        totais = cursor.fetchone()
        
        log(f"Total de transações: {totais['total']}", 'INFO')
        log(f"   Com importacao_id: {totais['com_importacao']}", 'INFO')
        log(f"   Sem importacao_id: {totais['sem_importacao']}", 'WARNING' if totais['sem_importacao'] > 0 else 'OK')
        
        separador("4. ANÁLISE DO CONFLITO")
        
        if totais['total'] == 0:
            log("✅ Banco está limpo! A importação deveria funcionar.", 'OK')
            log("⚠️ Se o erro persistir, pode ser problema de cache ou sessão.", 'WARNING')
        elif totais['com_importacao'] > 0:
            log("❌ Existem importações no banco que estão causando conflito!", 'ERROR')
            log("📋 SOLUÇÃO:", 'INFO')
            
            for imp in importacoes:
                inicio = imp['inicio']
                fim = imp['fim']
                tem_overlap = (periodo_inicio <= fim and periodo_fim >= inicio)
                
                if tem_overlap:
                    print(f"\n   DELETE da importação conflitante:")
                    print(f"   DELETE FROM transacoes_extrato")
                    print(f"   WHERE importacao_id = '{imp['importacao_id']}'")
                    print(f"   AND empresa_id = {empresa_id};")
        elif totais['sem_importacao'] > 0:
            log("⚠️ Existem transações órfãs causando o problema!", 'WARNING')
            log("📋 SOLUÇÃO:", 'INFO')
            print(f"\n   DELETE FROM transacoes_extrato")
            print(f"   WHERE empresa_id = {empresa_id}")
            print(f"   AND conta_bancaria = '{conta_bancaria}'")
            print(f"   AND (importacao_id IS NULL OR importacao_id = '');")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        
    except Exception as e:
        log(f"ERRO: {e}", 'ERROR')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
