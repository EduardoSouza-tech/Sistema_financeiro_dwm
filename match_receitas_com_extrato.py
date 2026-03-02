"""
Script para fazer match de receitas "manuais" com transações do extrato
e copiar categoria/subcategoria/pessoa das transações
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
from datetime import timedelta

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('🔄 FAZENDO MATCH DE RECEITAS COM TRANSAÇÕES DO EXTRATO\n')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Buscar receitas não conciliadas
cursor.execute("""
    SELECT l.id, l.descricao, l.valor, l.data_vencimento, l.data_pagamento
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
    ORDER BY l.id
""")

receitas_sem_conc = cursor.fetchall()
print(f'📋 Receitas sem conciliação: {len(receitas_sem_conc)}')

if len(receitas_sem_conc) == 0:
    print('✅ Não há receitas para processar!')
    cursor.close()
    conn.close()
    sys.exit(0)

# 2. Para cada receita, tentar achar transação correspondente
matches = []
nao_encontradas = []

print(f'\n🔎 Buscando transações correspondentes...')

for receita in receitas_sem_conc:
    # Tentar match por:
    # 1. Descrição exata + data
    # 2. Descrição similar (primeiras 50 chars) + data +/- 2 dias
    # 3. Valor exato + data +/- 2 dias
    
    # Match 1: Descrição exata + data exata
    cursor.execute("""
        SELECT id, categoria, subcategoria, pessoa
        FROM transacoes_extrato
        WHERE descricao = %s
          AND (data = %s OR data = %s)
          AND NOT conciliado
        LIMIT 1
    """, (receita['descricao'], receita['data_vencimento'], receita['data_pagamento']))
    
    trans = cursor.fetchone()
    
    if not trans:
        # Match 2: Descrição similar (primeiras 50 chars) + valor + data próxima
        descricao_curta = receita['descricao'][:50] if receita['descricao'] else ''
        
        cursor.execute("""
            SELECT id, categoria, subcategoria, pessoa
            FROM transacoes_extrato
            WHERE SUBSTRING(descricao, 1, 50) = %s
              AND ABS(valor) = %s
              AND data BETWEEN %s - INTERVAL '2 days' AND %s + INTERVAL '2 days'
              AND NOT conciliado
            LIMIT 1
        """, (descricao_curta, abs(float(receita['valor'])),
              receita['data_vencimento'] or receita['data_pagamento'],
              receita['data_vencimento'] or receita['data_pagamento']))
        
        trans = cursor.fetchone()
    
    if trans:
        matches.append({
            'lancamento_id': receita['id'],
            'transacao_id': trans['id'],
            'categoria': trans['categoria'],
            'subcategoria': trans['subcategoria'],
            'pessoa': trans['pessoa']
        })
    else:
        nao_encontradas.append(receita['id'])

print(f'\n📊 Resultados:')
print(f'   ✅ Matches encontrados: {len(matches)}')
print(f'   ❌ Não encontrados: {len(nao_encontradas)}')

if len(matches) == 0:
    print('\n⚠️  Nenhum match encontrado!')
    cursor.close()
    conn.close()
    sys.exit(0)

# Mostrar exemplos
print(f'\n📝 Exemplos de matches (5 primeiros):')
for i, m in enumerate(matches[:5], 1):
    print(f'   {i}. Lançamento #{m["lancamento_id"]} ↔ Transação #{m["transacao_id"]}')
    print(f'      Categoria: {m["categoria"]}')
    print(f'      Subcategoria: {m["subcategoria"]}')
    if m["pessoa"]:
        print(f'      Pessoa: {m["pessoa"][:50]}...')

# Confirmar
if '--auto-confirm' not in sys.argv:
    resposta = input(f'\n⚠️  Atualizar {len(matches)} receitas com dados das transações? (s/N): ')
    if resposta.lower() != 's':
        print('❌ Operação cancelada!')
        cursor.close()
        conn.close()
        sys.exit(0)

# 3. Atualizar em lote
print(f'\n🚀 Atualizando {len(matches)} receitas...')

for match in matches:
    # Atualizar lançamento
    updates = []
    params = []
    
    if match['categoria']:
        updates.append("categoria = %s")
        params.append(match['categoria'])
    
    if match['subcategoria']:
        updates.append("subcategoria = %s")
        params.append(match['subcategoria'])
    
    if match['pessoa']:
        updates.append("pessoa = %s")
        params.append(match['pessoa'])
    
    if updates:
        params.append(match['lancamento_id'])
        query = f"UPDATE lancamentos SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, params)

conn.commit()

print(f'\n✅ SUCESSO! {len(matches)} receitas atualizadas!')

# Verificar resultado
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(categoria) as com_categoria,
        COUNT(subcategoria) as com_subcategoria,
        COUNT(pessoa) as com_pessoa
    FROM lancamentos
    WHERE UPPER(tipo) = 'RECEITA'
""")
stats = cursor.fetchone()

print(f'\n📊 Estatísticas finais RECEITAS:')
print(f'   Total: {stats["total"]}')
print(f'   Com categoria: {stats["com_categoria"]} ({stats["com_categoria"]*100//stats["total"]}%)')
print(f'   Com subcategoria: {stats["com_subcategoria"]} ({stats["com_subcategoria"]*100//stats["total"]}%)')
print(f'   Com pessoa: {stats["com_pessoa"]} ({stats["com_pessoa"]*100//stats["total"]}%)')

cursor.close()
conn.close()

print('\n✅ Atualização completa!')
