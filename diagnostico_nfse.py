"""
Diagnóstico: Verificar se há notas NFS-e sendo omitidas na interface

Compara:
1. Total no banco de dados (data_competencia entre 2020-01-01 e 2026-02-28)
2. Total exibido na interface (79 notas)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from database_postgresql import get_nfse_db_params
from datetime import date

def diagnosticar_nfse():
    """Verifica se há omissões de NFS-e"""
    
    db_params = get_nfse_db_params()
    
    print("=" * 80)
    print("🔍 DIAGNÓSTICO DE NFS-e")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Parâmetros da consulta (igual à interface)
        data_inicial = date(2020, 1, 1)
        data_final = date(2026, 2, 28)
        
        # 1. Total de notas no banco (todas as empresas)
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT empresa_id) as total_empresas,
                SUM(valor_servico) as valor_total,
                SUM(valor_iss) as iss_total
            FROM nfse_baixadas
            WHERE data_competencia BETWEEN %s AND %s
        """, (data_inicial, data_final))
        
        geral = cursor.fetchone()
        
        print(f"\n📊 TOTAL NO BANCO (TODAS AS EMPRESAS):")
        print(f"   Notas: {geral['total']}")
        print(f"   Empresas: {geral['total_empresas']}")
        print(f"   Valor Total: R$ {float(geral['valor_total'] or 0):,.2f}")
        print(f"   ISS Total: R$ {float(geral['iss_total'] or 0):,.2f}")
        
        # 2. Total por empresa
        cursor.execute("""
            SELECT 
                empresa_id,
                COUNT(*) as total,
                SUM(valor_servico) as valor_total,
                SUM(valor_iss) as iss_total,
                MIN(data_emissao) as primeira_nota,
                MAX(data_emissao) as ultima_nota
            FROM nfse_baixadas
            WHERE data_competencia BETWEEN %s AND %s
            GROUP BY empresa_id
            ORDER BY total DESC
        """, (data_inicial, data_final))
        
        empresas = cursor.fetchall()
        
        print(f"\n📋 DETALHAMENTO POR EMPRESA:")
        for emp in empresas:
            print(f"\n   🏢 Empresa ID: {emp['empresa_id']}")
            print(f"      Total de Notas: {emp['total']}")
            print(f"      Valor Total: R$ {float(emp['valor_total'] or 0):,.2f}")
            print(f"      ISS Total: R$ {float(emp['iss_total'] or 0):,.2f}")
            print(f"      Período: {emp['primeira_nota']} a {emp['ultima_nota']}")
            
            # Verificar se é a empresa com 79 notas
            if emp['total'] == 79:
                print(f"      ⚠️ ESTA EMPRESA TEM AS 79 NOTAS EXIBIDAS NA INTERFACE")
        
        # 3. Verificar notas por situação
        cursor.execute("""
            SELECT 
                situacao,
                COUNT(*) as total,
                SUM(valor_servico) as valor_total
            FROM nfse_baixadas
            WHERE data_competencia BETWEEN %s AND %s
            GROUP BY situacao
            ORDER BY total DESC
        """, (data_inicial, data_final))
        
        situacoes = cursor.fetchall()
        
        print(f"\n📊 NOTAS POR SITUAÇÃO:")
        for sit in situacoes:
            print(f"   {sit['situacao']}: {sit['total']} notas (R$ {float(sit['valor_total'] or 0):,.2f})")
        
        # 4. Verificar se há notas de outras situações além de NORMAL na empresa principal
        if empresas:
            empresa_principal = empresas[0]['empresa_id']
            
            cursor.execute("""
                SELECT 
                    situacao,
                    COUNT(*) as total
                FROM nfse_baixadas
                WHERE empresa_id = %s
                AND data_competencia BETWEEN %s AND %s
                GROUP BY situacao
            """, (empresa_principal, data_inicial, data_final))
            
            sit_empresa = cursor.fetchall()
            
            print(f"\n🔍 SITUAÇÕES NA EMPRESA PRINCIPAL (ID {empresa_principal}):")
            for sit in sit_empresa:
                print(f"   {sit['situacao']}: {sit['total']} notas")
            
            # Verificar se há CANCELADAS ou SUBSTITUIDAS sendo filtradas
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM nfse_baixadas
                WHERE empresa_id = %s
                AND data_competencia BETWEEN %s AND %s
                AND situacao != 'NORMAL'
            """, (empresa_principal, data_inicial, data_final))
            
            outras = cursor.fetchone()
            
            if outras['total'] > 0:
                print(f"\n   ⚠️ HÁ {outras['total']} NOTAS NÃO-NORMAIS SENDO FILTRADAS!")
                print(f"      (A interface só mostra notas com situacao='NORMAL')")
            else:
                print(f"\n   ✅ Todas as notas da empresa são NORMAIS")
        
        # 5. Checar se data_competencia != data_emissao está causando filtros
        cursor.execute("""
            SELECT 
                COUNT(*) as total_competencia,
                COUNT(*) FILTER (WHERE data_competencia != data_emissao) as datas_diferentes
            FROM nfse_baixadas
            WHERE data_competencia BETWEEN %s AND %s
        """, (data_inicial, data_final))
        
        datas = cursor.fetchone()
        
        print(f"\n📅 ANÁLISE DE DATAS:")
        print(f"   Total de notas: {datas['total_competencia']}")
        print(f"   Notas com data_competencia ≠ data_emissao: {datas['datas_diferentes']}")
        
        if datas['datas_diferentes'] > 0:
            print(f"   ℹ️ O filtro da interface usa data_competencia, não data_emissao")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("✅ DIAGNÓSTICO CONCLUÍDO")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    diagnosticar_nfse()
