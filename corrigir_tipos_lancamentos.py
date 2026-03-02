"""
Script para corrigir lançamentos criados incorretamente como 'receita' 
quando deveriam ser 'despesa' (transações DEBITO).
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('🔧 CORREÇÃO DE LANÇAMENTOS COM TIPO ERRADO\n')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Identificar lançamentos que precisam ser corrigidos
cursor.execute("""
    SELECT 
        l.id as lancamento_id,
        l.tipo as tipo_atual,
        te.tipo as tipo_transacao,
        l.descricao,
        l.valor
    FROM lancamentos l
    JOIN conciliacoes c ON c.lancamento_id = l.id
    JOIN transacoes_extrato te ON te.id = c.transacao_extrato_id
    WHERE te.tipo = 'DEBITO' AND l.tipo = 'receita'
""")

errados = cursor.fetchall()
print(f'❌ Encontrados {len(errados)} lançamentos com tipo ERRADO:')
print(f'   Transação DEBITO → Lançamento tipo=receita (deveria ser despesa)\n')

if len(errados) == 0:
    print('✅ Nenhuma correção necessária!')
    cursor.close()
    conn.close()
    sys.exit(0)

# Mostrar exemplos
print('📋 Exemplos:')
for i, e in enumerate(errados[:5]):
    print(f'   {i+1}. Lançamento #{e["lancamento_id"]}: {e["descricao"][:50]} | R$ {e["valor"]:,.2f}')
    print(f'      Transação: {e["tipo_transacao"]} → Lançamento: {e["tipo_atual"]} (❌ ERRADO!)')
    print()

# Confirmar
if '--auto-confirm' not in sys.argv:
    resposta = input(f'\n⚠️  Corrigir {len(errados)} lançamentos de "receita" para "despesa"? (s/N): ')
    if resposta.lower() != 's':
        print('❌ Operação cancelada!')
        cursor.close()
        conn.close()
        sys.exit(0)

# Executar correção
print(f'\n🔄 Corrigindo {len(errados)} lançamentos...\n')

ids_para_corrigir = [e['lancamento_id'] for e in errados]

cursor.execute("""
    UPDATE lancamentos
    SET tipo = 'despesa'
    WHERE id = ANY(%s)
""", (ids_para_corrigir,))

linhas_afetadas = cursor.rowcount
conn.commit()

print(f'✅ SUCESSO! {linhas_afetadas} lançamentos corrigidos de "receita" → "despesa"')

# Verificar resultado
cursor.execute("""
    SELECT 
        te.tipo as tipo_transacao, 
        l.tipo as tipo_lancamento,
        COUNT(*) as qtd
    FROM transacoes_extrato te
    JOIN conciliacoes c ON c.transacao_extrato_id = te.id
    JOIN lancamentos l ON l.id = c.lancamento_id
    GROUP BY te.tipo, l.tipo
    ORDER BY qtd DESC
""")
mapping = cursor.fetchall()

print(f'\n📊 Mapeamento após correção:')
for m in mapping:
    status = '✅' if (m['tipo_transacao'] == 'DEBITO' and m['tipo_lancamento'] == 'despesa') or \
                     (m['tipo_transacao'] == 'CREDITO' and m['tipo_lancamento'] == 'receita') else '❌'
    print(f'   {status} {m["tipo_transacao"]} → {m["tipo_lancamento"]}: {m["qtd"]} registros')

# Contar totais
cursor.execute("SELECT tipo, COUNT(*) as qtd FROM lancamentos GROUP BY tipo ORDER BY qtd DESC")
totais = cursor.fetchall()
print(f'\n📈 Totais por tipo em lancamentos:')
for t in totais:
    print(f'   - {t["tipo"]}: {t["qtd"]}')

cursor.close()
conn.close()

print('\n✅ Correção completa!')
