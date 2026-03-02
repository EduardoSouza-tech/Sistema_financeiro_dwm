import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('🔍 ANALISANDO CAMPOS VAZIOS EM LANÇAMENTOS\n')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Verificar schema da tabela transacoes_extrato
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'transacoes_extrato'
    ORDER BY ordinal_position
""")
colunas_extrato = cursor.fetchall()
print('📋 Colunas em TRANSACOES_EXTRATO:')
for col in colunas_extrato:
    print(f'   - {col["column_name"]}: {col["data_type"]}')

# 2. Ver exemplo de transação com mais campos
cursor.execute("""
    SELECT *
    FROM transacoes_extrato
    LIMIT 3
""")
exemplos = cursor.fetchall()
print(f'\n📝 Exemplos de transações (todas as colunas):')
for i, ex in enumerate(exemplos, 1):
    print(f'\n   Exemplo {i}:')
    for key, value in ex.items():
        if value:  # Só mostrar campos com valor
            print(f'      {key}: {value}')

# 3. Verificar se há alguma informação útil que possamos usar
cursor.execute("""
    SELECT COUNT(*) as total,
           COUNT(categoria) as com_categoria,
           COUNT(subcategoria) as com_subcategoria,
           COUNT(pessoa) as com_pessoa,
           COUNT(numero_documento) as com_num_doc
    FROM transacoes_extrato
""")
stats_extrato = cursor.fetchone()
print(f'\n📊 Estatísticas TRANSACOES_EXTRATO:')
print(f'   Total: {stats_extrato["total"]}')
print(f'   Com categoria: {stats_extrato["com_categoria"]}')
print(f'   Com subcategoria: {stats_extrato["com_subcategoria"]}')
print(f'   Com pessoa: {stats_extrato["com_pessoa"]}')
print(f'   Com número documento: {stats_extrato["com_num_doc"]}')

# 4. Verificar lançamentos
cursor.execute("""
    SELECT COUNT(*) as total,
           COUNT(pessoa) as com_pessoa,
           COUNT(subcategoria) as com_subcategoria,
           COUNT(numero_documento) as com_num_doc
    FROM lancamentos
""")
stats_lanc = cursor.fetchone()
print(f'\n📊 Estatísticas LANÇAMENTOS:')
print(f'   Total: {stats_lanc["total"]}')
print(f'   Com pessoa: {stats_lanc["com_pessoa"]}')
print(f'   Com subcategoria: {stats_lanc["com_subcategoria"]}')
print(f'   Com número documento: {stats_lanc["com_num_doc"]}')

# 5. Verificar se podemos copiar dados de transacao → lancamento
cursor.execute("""
    SELECT 
        te.id as transacao_id,
        te.categoria as te_categoria,
        te.subcategoria as te_subcategoria,
        te.pessoa as te_pessoa,
        l.id as lancamento_id,
        l.categoria as l_categoria,
        l.subcategoria as l_subcategoria,
        l.pessoa as l_pessoa
    FROM transacoes_extrato te
    JOIN conciliacoes c ON c.transacao_extrato_id = te.id
    JOIN lancamentos l ON l.id = c.lancamento_id
    WHERE te.categoria IS NOT NULL OR te.subcategoria IS NOT NULL OR te.pessoa IS NOT NULL
    LIMIT 5
""")
transferiveis = cursor.fetchall()
if transferiveis:
    print(f'\n✅ Encontradas {len(transferiveis)} transações com dados para transferir:')
    for t in transferiveis:
        print(f'   Transação {t["transacao_id"]} → Lançamento {t["lancamento_id"]}')
        if t["te_categoria"]:
            print(f'      Categoria: {t["te_categoria"]}')
        if t["te_subcategoria"]:
            print(f'      Subcategoria: {t["te_subcategoria"]}')
        if t["te_pessoa"]:
            print(f'      Pessoa: {t["te_pessoa"]}')
else:
    print('\n❌ Não há dados para transferir de transações para lançamentos')

cursor.close()
conn.close()

print('\n✅ Análise completa!')
