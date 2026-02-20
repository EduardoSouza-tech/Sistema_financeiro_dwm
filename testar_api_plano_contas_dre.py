"""Testar API de plano de contas DRE diretamente no Railway"""
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway"

print("="*80)
print("TESTANDO QUERY: PLANO DE CONTAS DRE")
print("="*80)

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    empresa_id = 20
    
    print(f"\n🔍 Executando query para empresa_id = {empresa_id}...\n")
    
    query = """
        SELECT 
            id,
            codigo,
            descricao,
            classificacao,
            nivel
        FROM plano_contas
        WHERE empresa_id = %s
          AND tipo_conta = 'analitica'
          AND (codigo LIKE '4%%' OR codigo LIKE '5%%' OR codigo LIKE '6%%' OR codigo LIKE '7%%')
          AND deleted_at IS NULL
        ORDER BY codigo
    """
    
    cursor.execute(query, (empresa_id,))
    
    results = cursor.fetchall()
    
    print(f"✅ Query executada com sucesso!")
    print(f"📊 Resultado: {len(results)} contas encontradas\n")
    
    if results:
        print("Primeiros 10 resultados:")
        for i, row in enumerate(results[:10]):
            codigo = row['codigo']
            
            # Determinar grupo (mesma lógica do backend)
            if codigo.startswith('4.9'):
                grupo_dre = 'Deduções da Receita'
            elif codigo.startswith('4'):
                grupo_dre = 'Receita Bruta'
            elif codigo.startswith('5'):
                grupo_dre = 'Custos'
            elif codigo.startswith('6'):
                grupo_dre = 'Despesas Operacionais'
            elif codigo.startswith('7.1'):
                grupo_dre = 'Receitas Financeiras'
            elif codigo.startswith('7.2'):
                grupo_dre = 'Despesas Financeiras'
            else:
                grupo_dre = 'Outros'
            
            print(f"   {i+1}. {row['codigo']:10s} - {row['descricao'][:50]:50s} ({grupo_dre})")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Teste concluído - Query funciona perfeitamente!")
    
except Exception as e:
    print(f"\n❌ ERRO: {str(e)}")
    print(f"   Tipo: {type(e).__name__}")
    import traceback
    traceback.print_exc()
