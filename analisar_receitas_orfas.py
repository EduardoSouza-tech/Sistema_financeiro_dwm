"""
Análise detalhada das 782 receitas órfãs para decidir estratégia
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import re

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

print('🔍 ANÁLISE DETALHADA DAS 782 RECEITAS ÓRFÃS\n')

# 1. Buscar todas as receitas sem conciliação
cursor.execute("""
    SELECT l.id, l.descricao, l.valor, l.data_vencimento, l.data_pagamento, 
           l.categoria, l.subcategoria, l.pessoa, l.status
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
    ORDER BY l.data_vencimento
    LIMIT 20
""")

receitas = cursor.fetchall()

print('📋 AMOSTRA DE 20 RECEITAS:\n')
for r in receitas:
    print(f'ID {r["id"]}: {r["descricao"][:80]}')
    print(f'   Valor: R$ {r["valor"]} | Data: {r["data_vencimento"]} | Status: {r["status"]}')
    print(f'   Categoria: {r["categoria"]} | Subcategoria: {r["subcategoria"]} | Pessoa: {r["pessoa"]}')
    print()

# 2. Analisar padrões de descrição PIX
print('\n🎯 ANÁLISE DE PADRÕES PIX:\n')

cursor.execute("""
    SELECT l.descricao, l.valor, l.data_vencimento
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
      AND l.descricao LIKE 'PAGAMENTO PIX%'
    LIMIT 10
""")

pix_examples = cursor.fetchall()

print('Exemplos de descrições PIX:')
for p in pix_examples:
    desc = p['descricao']
    print(f'\n   "{desc}"')
    
    # Tentar extrair CPF e nome
    # Padrão: PAGAMENTO PIX-PIX_DEB   [CPF 11 dígitos] [Nome]
    match = re.search(r'(\d{11})\s+(.+?)$', desc)
    if match:
        cpf = match.group(1)
        nome = match.group(2).strip()
        print(f'   → CPF: {cpf}')
        print(f'   → Nome extraído: "{nome}"')
    else:
        print(f'   → ❌ Não consegui extrair CPF/Nome')

# 3. Verificar se essas descrições existem no extrato
print('\n\n🔎 VERIFICANDO SE EXISTEM NO EXTRATO:\n')

cursor.execute("""
    SELECT te.id, te.descricao, te.valor, te.data, te.tipo
    FROM transacoes_extrato te
    WHERE te.empresa_id = 20
      AND te.descricao LIKE 'PAGAMENTO PIX%'
    LIMIT 5
""")

extrato_pix = cursor.fetchall()

if extrato_pix:
    print(f'✅ Encontradas {len(extrato_pix)} transações PIX no extrato:')
    for t in extrato_pix:
        print(f'   ID {t["id"]}: {t["descricao"][:80]}')
        print(f'   Tipo: {t["tipo"]} | Valor: R$ {t["valor"]} | Data: {t["data"]}')
else:
    print('❌ NÃO há transações "PAGAMENTO PIX" no extrato!')
    print('   (Só há DEBITO e CREDITO já conciliados)')

# 4. Estatísticas de valores
print('\n\n📊 ESTATÍSTICAS DAS 782 RECEITAS:\n')

cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(l.valor) as soma_total,
        AVG(l.valor) as valor_medio,
        MIN(l.valor) as valor_minimo,
        MAX(l.valor) as valor_maximo,
        MIN(l.data_vencimento) as primeira_data,
        MAX(l.data_vencimento) as ultima_data
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
""")

stats = cursor.fetchone()

print(f'Total: {stats["total"]} receitas')
print(f'Valor total: R$ {stats["soma_total"]:,.2f}')
print(f'Valor médio: R$ {stats["valor_medio"]:,.2f}')
print(f'Valor mínimo: R$ {stats["valor_minimo"]:,.2f}')
print(f'Valor máximo: R$ {stats["valor_maximo"]:,.2f}')
print(f'Período: {stats["primeira_data"]} até {stats["ultima_data"]}')

# 5. Comparar com volume financeiro total
cursor.execute("""
    SELECT 
        SUM(CASE WHEN c.lancamento_id IS NOT NULL THEN l.valor ELSE 0 END) as receitas_conciliadas,
        SUM(CASE WHEN c.lancamento_id IS NULL THEN l.valor ELSE 0 END) as receitas_orfas
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
""")

comparacao = cursor.fetchone()

print(f'\n💰 IMPACTO FINANCEIRO:')
print(f'   Receitas conciliadas: R$ {comparacao["receitas_conciliadas"]:,.2f}')
print(f'   Receitas órfãs: R$ {comparacao["receitas_orfas"]:,.2f}')
pct = (comparacao["receitas_orfas"] / (comparacao["receitas_conciliadas"] + comparacao["receitas_orfas"])) * 100
print(f'   Órfãs representam: {pct:.1f}% do total')

# 6. Verificar de onde vieram (observações, created_at)
print('\n\n📝 ORIGEM DOS DADOS:\n')

cursor.execute("""
    SELECT l.observacoes, COUNT(*) as qtd
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
      AND l.observacoes IS NOT NULL
    GROUP BY l.observacoes
    ORDER BY qtd DESC
    LIMIT 5
""")

obs = cursor.fetchall()

if obs:
    print('Observações mais comuns:')
    for o in obs:
        print(f'   "{o["observacoes"][:80]}" ({o["qtd"]} vezes)')
else:
    print('❌ Nenhuma receita tem observações')

# 7. Decisão
print('\n\n' + '='*80)
print('🎯 ANÁLISE DE DECISÃO')
print('='*80)

print('\n📌 SITUAÇÃO:')
print('   • 782 receitas sem conciliação com extrato')
print('   • Descrições no formato "PAGAMENTO PIX-PIX_DEB [CPF] [Nome]"')
print('   • NÃO existem no extrato bancário (extrato só tem 694 transações)')
print(f'   • Representam {pct:.1f}% do volume financeiro total')
print(f'   • Total: R$ {comparacao["receitas_orfas"]:,.2f}')

print('\n🔧 OPÇÕES:')
print('\n   A) EXCLUIR os 782 lançamentos')
print('      ✅ Limpa dados inconsistentes')
print('      ❌ PERDE dados financeiros reais')
print(f'      ❌ Perde R$ {comparacao["receitas_orfas"]:,.2f}')

print('\n   B) COMPLETAR automaticamente extraindo dados da descrição')
print('      ✅ Mantém histórico financeiro')
print('      ✅ Aproveita CPF e nome já presentes')
print('      ✅ Define categorias padrão')
print('      ⚠️  Nome pode estar truncado')

print('\n   C) AGUARDAR dados da fonte original')
print('      ⚠️  Pode não ter fonte disponível')
print('      ⚠️  Dados ficam incompletos indefinidamente')

cursor.close()
conn.close()

print('\n✅ Análise completa!')
print('\n💡 RECOMENDAÇÃO: Opção B - Completar automaticamente')
print('   Razão: Preserva informações financeiras importantes e utiliza dados já disponíveis')
