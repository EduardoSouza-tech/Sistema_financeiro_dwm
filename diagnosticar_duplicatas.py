"""
Diagnóstico de duplicatas em lançamentos
Verifica se há lançamentos duplicados no banco de dados
"""
import os
from database_postgresql import DatabaseManager

def diagnosticar_duplicatas():
    """Detecta lançamentos duplicados"""
    print("="*80)
    print("🔍 DIAGNÓSTICO DE DUPLICATAS EM LANÇAMENTOS")
    print("="*80)
    
    # Conectar ao banco
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não encontrada!")
        return
    
    db = DatabaseManager(database_url)
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 1. Total de lançamentos
    print("\n📊 1. TOTAL DE LANÇAMENTOS:")
    cursor.execute("SELECT COUNT(*) as total FROM lancamentos")
    total = cursor.fetchone()['total']
    print(f"   Total: {total:,} lançamentos")
    
    # 2. Lançamentos com [EXTRATO]
    print("\n📋 2. LANÇAMENTOS COM [EXTRATO]:")
    cursor.execute("""
        SELECT COUNT(*) as total, tipo, status
        FROM lancamentos
        WHERE descricao LIKE '[EXTRATO]%'
        GROUP BY tipo, status
        ORDER BY tipo, status
    """)
    extrato_rows = cursor.fetchall()
    total_extrato = 0
    for row in extrato_rows:
        print(f"   {row['tipo']:10} {row['status']:10} = {row['total']:,} registros")
        total_extrato += row['total']
    print(f"   Total com [EXTRATO]: {total_extrato:,}")
    
    # 3. Duplicatas potenciais (mesma descrição, valor, data)
    print("\n🔍 3. DUPLICATAS POTENCIAIS (mesma descrição + valor + data):")
    cursor.execute("""
        SELECT descricao, valor, data_vencimento, tipo, COUNT(*) as count
        FROM lancamentos
        WHERE empresa_id = 20  -- COOPSERVICOS
        GROUP BY descricao, valor, data_vencimento, tipo
        HAVING COUNT(*) > 1
        ORDER BY count DESC, data_vencimento DESC
        LIMIT 20
    """)
    duplicatas = cursor.fetchall()
    
    if duplicatas:
        print(f"   ⚠️ Encontradas {len(duplicatas)} grupos de duplicatas:")
        for dup in duplicatas:
            print(f"\n   📌 {dup['count']}x duplicado:")
            print(f"      Descrição: {dup['descricao'][:50]}...")
            print(f"      Valor: R$ {dup['valor']:,.2f}")
            print(f"      Data: {dup['data_vencimento']}")
            print(f"      Tipo: {dup['tipo']}")
            
            # Buscar IDs dos duplicados
            cursor.execute("""
                SELECT id, status, pessoa, data_pagamento
                FROM lancamentos
                WHERE descricao = %s 
                  AND valor = %s 
                  AND data_vencimento = %s
                  AND tipo = %s
                  AND empresa_id = 20
                ORDER BY id
            """, (dup['descricao'], dup['valor'], dup['data_vencimento'], dup['tipo']))
            
            ids_duplicados = cursor.fetchall()
            print(f"      IDs: {', '.join(str(r['id']) for r in ids_duplicados)}")
            for idx, item in enumerate(ids_duplicados, 1):
                print(f"         [{idx}] ID {item['id']} - Status: {item['status']}, "
                      f"Pessoa: {item['pessoa']}, Pago em: {item['data_pagamento'] or 'N/A'}")
    else:
        print("   ✅ Nenhuma duplicata encontrada!")
    
    # 4. Comparar com transações do extrato
    print("\n🏦 4. COMPARAÇÃO COM TRANSACOES_EXTRATO:")
    cursor.execute("SELECT COUNT(*) as total FROM transacoes_extrato WHERE conta_bancaria_id = 6")
    total_extrato_real = cursor.fetchone()['total']
    print(f"   Transações no extrato: {total_extrato_real:,}")
    print(f"   Lançamentos com [EXTRATO]: {total_extrato:,}")
    print(f"   Diferença: {abs(total_extrato_real - total_extrato):,}")
    
    if total_extrato > total_extrato_real:
        print(f"   ⚠️ HÁ {total_extrato - total_extrato_real:,} LANÇAMENTOS [EXTRATO] EXCEDENTES!")
        print(f"   Isso indica duplicação entre extrato importado e lançamentos manuais")
    
    # 5. Sumarização por empresa
    print("\n🏢 5. LANÇAMENTOS POR EMPRESA:")
    cursor.execute("""
        SELECT empresa_id, COUNT(*) as total
        FROM lancamentos
        GROUP BY empresa_id
        ORDER BY total DESC
    """)
    por_empresa = cursor.fetchall()
    for row in por_empresa:
        # Buscar nome da empresa
        cursor.execute("SELECT razao_social FROM empresas WHERE id = %s", (row['empresa_id'],))
        empresa = cursor.fetchone()
        nome = empresa['razao_social'] if empresa else 'Desconhecida'
        print(f"   Empresa {row['empresa_id']} ({nome}): {row['total']:,} lançamentos")
    
    cursor.close()
    db.return_to_pool(conn)
    
    print("\n" + "="*80)
    print("✅ Diagnóstico concluído!")
    print("="*80)

if __name__ == '__main__':
    diagnosticar_duplicatas()
