import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

print('🔍 SIMULANDO RESPOSTA DA API /api/lancamentos\n')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Simular a query que a API faz (similar ao database_postgresql.py)
cursor.execute("""
    SELECT 
        l.id, l.tipo, l.descricao, l.valor, l.data_vencimento, l.data_pagamento,
        l.categoria, l.subcategoria, l.conta_bancaria, l.cliente_fornecedor,
        l.pessoa, l.status, l.observacoes, l.anexo, l.recorrente,
        l.frequencia_recorrencia, l.dia_vencimento, l.associacao, l.numero_documento,
        CASE WHEN c.transacao_extrato_id IS NOT NULL THEN TRUE ELSE FALSE END as conciliado
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id AND c.empresa_id = l.empresa_id
    WHERE l.empresa_id = 20
      AND UPPER(l.tipo) = 'RECEITA'
    ORDER BY l.id DESC
    LIMIT 5
""")

receitas = cursor.fetchall()

print(f'📦 Receitas retornadas pela query (últimas 5):')
print(f'   Total: {len(receitas)}\n')

for i, r in enumerate(receitas, 1):
    print(f'   {i}. ID {r["id"]}: {r["descricao"][:50]}')
    print(f'      📋 Campos importantes:')
    print(f'         pessoa: {r["pessoa"]}')
    print(f'         subcategoria: {r["subcategoria"]}')
    print(f'         categoria: {r["categoria"]}')
    print(f'         numero_documento: {r.get("numero_documento")}')
    print(f'         associacao: {r.get("associacao")}')
    print(f'         conciliado: {r["conciliado"]}')
    
    # Simular o JSON que seria retornado
    json_obj = {
        'id': r['id'],
        'tipo': r['tipo'],
        'descricao': r['descricao'],
        'valor': float(r['valor']) if r['valor'] else 0,
        'data_vencimento': r['data_vencimento'].isoformat() if r['data_vencimento'] else None,
        'status': r['status'],
        'categoria': r['categoria'],
        'subcategoria': r['subcategoria'],
        'pessoa': r['pessoa'],
        'numero_documento': r.get('numero_documento', ''),
        'associacao': r.get('associacao', '')
    }
    
    print(f'\n      📤 JSON que seria retornado:')
    print(f'         {json.dumps(json_obj, indent=10, ensure_ascii=False)}')
    print()

# Agora verificar receitas que TÊM dados
cursor.execute("""
    SELECT 
        l.id, l.tipo, l.descricao, l.valor, l.data_vencimento, l.data_pagamento,
        l.categoria, l.subcategoria, l.conta_bancaria, l.cliente_fornecedor,
        l.pessoa, l.status, l.observacoes, l.anexo, l.recorrente,
        l.frequencia_recorrencia, l.dia_vencimento, l.associacao, l.numero_documento,
        CASE WHEN c.transacao_extrato_id IS NOT NULL THEN TRUE ELSE FALSE END as conciliado
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id AND c.empresa_id = l.empresa_id
    WHERE l.empresa_id = 20
      AND UPPER(l.tipo) = 'RECEITA'
      AND l.pessoa IS NOT NULL
    LIMIT 3
""")

com_dados = cursor.fetchall()

print(f'\n💚 Receitas COM pessoa preenchida:')
print(f'   Total: {len(com_dados)}\n')

for i, r in enumerate(com_dados, 1):
    print(f'   {i}. ID {r["id"]}: {r["descricao"][:50]}')
    print(f'      pessoa: {r["pessoa"][:60]}')
    print(f'      subcategoria: {r["subcategoria"]}')
    print(f'      categoria: {r["categoria"]}')
    print()

cursor.close()
conn.close()

print('✅ Simulação completa!')
