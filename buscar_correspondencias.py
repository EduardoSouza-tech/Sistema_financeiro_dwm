import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('🔍 BUSCANDO CORRESPONDÊNCIAS ENTRE RECEITAS MANUAIS E TRANSAÇÕES\n')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Ver exemplos de receitas manuais
cursor.execute("""
    SELECT l.id, l.descricao, l.valor, l.data_vencimento, l.categoria
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
    ORDER BY l.data_vencimento DESC
    LIMIT 10
""")
receitas_manuais = cursor.fetchall()

print(f'📋 Exemplos de receitas MANUAIS (não conciliadas):')
for r in receitas_manuais:
    print(f'\n   ID {r["id"]}: {r["descricao"][:60]}')
    print(f'      Valor: R$ {r["valor"]:.2f} | Data: {r["data_vencimento"]} | Categoria: {r["categoria"]}')

# 2. Ver se há transações no extrato com descrição similar
print(f'\n\n🔎 Buscando transações no extrato com descrições similares...\n')

# Pegar primeira receita e buscar no extrato
if receitas_manuais:
    primeira = receitas_manuais[0]
    # Extrair palavras chave da descrição
    palavras = primeira['descricao'].split()[:3]  # Primeiras 3 palavras
    
    print(f'   Buscando por: {" ".join(palavras)}')
    
    for palavra in palavras:
        if len(palavra) > 3:  # Palavras com mais de 3 letras
            cursor.execute("""
                SELECT id, descricao, tipo, valor, data, categoria, subcategoria, pessoa
                FROM transacoes_extrato
                WHERE UPPER(descricao) LIKE UPPER(%s)
                LIMIT 5
            """, (f'%{palavra}%',))
            
            matches = cursor.fetchall()
            if matches:
                print(f'\n   ✅ Encontradas {len(matches)} transações com "{palavra}":')
                for m in matches[:2]:
                    print(f'      Transação #{m["id"]}: {m["descricao"][:50]}')
                    print(f'         Tipo: {m["tipo"]} | Valor: R$ {m["valor"]}')
                    print(f'         Categoria: {m["categoria"]}')
                    print(f'         Subcategoria: {m["subcategoria"]}')
                    print(f'         Pessoa: {m["pessoa"][:40] if m["pessoa"] else None}')
                break

# 3. Verificar se receitas manuais têm datas que coincidem com transações
cursor.execute("""
    SELECT COUNT(*) as total
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND EXISTS (
          SELECT 1 FROM transacoes_extrato te
          WHERE te.data = l.data_vencimento
            OR te.data = l.data_pagamento
      )
""")
com_data_similar = cursor.fetchone()['total']

print(f'\n\n📊 Receitas manuais com MESMA DATA de transações no extrato: {com_data_similar}')

# 4. Verificar range de datas
cursor.execute("""
    SELECT 
        MIN(data_vencimento) as min_lanc,
        MAX(data_vencimento) as max_lanc
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
""")
range_lanc = cursor.fetchone()

cursor.execute("""
    SELECT 
        MIN(data) as min_trans,
        MAX(data) as max_trans
    FROM transacoes_extrato
""")
range_trans = cursor.fetchone()

print(f'\n📅 Range de datas:')
print(f'   Receitas manuais: {range_lanc["min_lanc"]} → {range_lanc["max_lanc"]}')
print(f'   Transações extrato: {range_trans["min_trans"]} → {range_trans["max_trans"]}')

# 5. Verificar origens das receitas manuais
cursor.execute("""
    SELECT observacoes, COUNT(*) as qtd
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND observacoes IS NOT NULL
    GROUP BY observacoes
    ORDER BY qtd DESC
    LIMIT 5
""")
origens = cursor.fetchall()

if origens:
    print(f'\n💬 Observações nas receitas manuais:')
    for o in origens:
        print(f'   "{o["observacoes"][:60]}": {o["qtd"]} receitas')

cursor.close()
conn.close()

print('\n✅ Análise completa!')
