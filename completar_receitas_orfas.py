"""
COMPLETAR RECEITAS ÓRFÃS AUTOMATICAMENTE
Extrai pessoa da descrição e define categorias padrão
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import re
import sys

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

AUTO_CONFIRM = '--auto-confirm' in sys.argv

print('='*80)
print('🔧 COMPLETAR RECEITAS ÓRFÃS AUTOMATICAMENTE')
print('='*80)
print()

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Buscar todas as receitas sem conciliação
cursor.execute("""
    SELECT l.id, l.descricao, l.valor, l.categoria, l.subcategoria, l.pessoa
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
    ORDER BY l.id
""")

receitas = cursor.fetchall()

print(f'📋 Total de receitas a processar: {len(receitas)}\n')

if len(receitas) == 0:
    print('✅ Não há receitas para processar!')
    cursor.close()
    conn.close()
    sys.exit(0)

# 2. Categorizar e extrair dados
updates = []
stats = {
    'pix_pagamento': 0,
    'pix_recebimento': 0,
    'resgate': 0,
    'aplicacao': 0,
    'outro': 0,
    'pessoa_extraida': 0,
    'sem_mudanca': 0
}

print('🔍 Analisando descrições...\n')

for receita in receitas:
    desc = receita['descricao'] or ''
    update_data = {
        'id': receita['id'],
        'categoria': receita['categoria'],
        'subcategoria': receita['subcategoria'],
        'pessoa': receita['pessoa']
    }
    
    mudou = False
    
    # PADRÃO 1: PAGAMENTO PIX-PIX_DEB [CPF/CNPJ] [Nome]
    if 'PAGAMENTO PIX-PIX_DEB' in desc:
        # Extrair CPF/CNPJ e nome
        match = re.search(r'(\d{11,14})\s+(.+?)$', desc)
        if match:
            cpf_cnpj = match.group(1)
            nome = match.group(2).strip()
            
            # Definir pessoa
            if not receita['pessoa']:
                update_data['pessoa'] = nome
                stats['pessoa_extraida'] += 1
                mudou = True
            
            # Definir categoria/subcategoria
            if receita['categoria'] == 'Conciliação Bancária' or not receita['categoria']:
                update_data['categoria'] = 'RECEITAS DE EVENTOS'
                update_data['subcategoria'] = 'PAGAMENTOS PIX'
                mudou = True
            
            stats['pix_pagamento'] += 1
        else:
            stats['outro'] += 1
    
    # PADRÃO 2: RECEBIMENTO PIX-PIX_CRED [CPF/CNPJ] [Nome]
    elif 'RECEBIMENTO PIX-PIX_CRED' in desc or 'PIX-PIX_CRED' in desc:
        # Extrair CPF/CNPJ e nome
        match = re.search(r'(\d{11,14})\s+(.+?)$', desc)
        if match:
            cpf_cnpj = match.group(1)
            nome = match.group(2).strip()
            
            if not receita['pessoa']:
                update_data['pessoa'] = nome
                stats['pessoa_extraida'] += 1
                mudou = True
            
            if receita['categoria'] == 'Conciliação Bancária' or not receita['categoria']:
                update_data['categoria'] = 'RECEITAS DE EVENTOS'
                update_data['subcategoria'] = 'RECEBIMENTOS PIX'
                mudou = True
            
            stats['pix_recebimento'] += 1
        else:
            stats['outro'] += 1
    
    # PADRÃO 3: RESGATE APLIC. FINANCEIRA
    elif 'RESGATE APLIC' in desc:
        if not receita['pessoa']:
            update_data['pessoa'] = 'BANCO SICREDI'
            mudou = True
        
        if receita['categoria'] == 'Conciliação Bancária' or not receita['categoria']:
            update_data['categoria'] = 'RECEITAS BANCARIAS'
            update_data['subcategoria'] = 'RESGATE DE APLICACAO'
            mudou = True
        
        stats['resgate'] += 1
    
    # PADRÃO 4: APLICACAO FINANCEIRA
    elif 'APLICACAO FINANCEIRA' in desc or 'APLIC. FINANCEIRA' in desc:
        if not receita['pessoa']:
            update_data['pessoa'] = 'BANCO SICREDI'
            mudou = True
        
        if receita['categoria'] == 'Conciliação Bancária' or not receita['categoria']:
            update_data['categoria'] = 'RECEITAS BANCARIAS'
            update_data['subcategoria'] = 'RENDIMENTO DE APLICACOES'
            mudou = True
        
        stats['aplicacao'] += 1
    
    # PADRÃO 5: TED, DOC, outros
    elif 'TED-' in desc or 'DOC-' in desc or 'TRANSFERENCIA' in desc:
        # Tentar extrair nome/CNPJ
        match = re.search(r'(\d{14})\s+(.+?)$', desc)
        if match:
            cnpj = match.group(1)
            nome = match.group(2).strip()
            
            if not receita['pessoa']:
                update_data['pessoa'] = nome
                stats['pessoa_extraida'] += 1
                mudou = True
        
        if receita['categoria'] == 'Conciliação Bancária' or not receita['categoria']:
            update_data['categoria'] = 'RECEITAS DIVERSAS'
            update_data['subcategoria'] = 'TRANSFERENCIAS RECEBIDAS'
            mudou = True
        
        stats['outro'] += 1
    
    # PADRÃO 6: LIQ.COBRANCA
    elif 'LIQ.COBRANCA' in desc or 'LIQUIDACAO' in desc:
        if receita['categoria'] == 'Conciliação Bancária' or not receita['categoria']:
            update_data['categoria'] = 'RECEITAS DIVERSAS'
            update_data['subcategoria'] = 'LIQUIDACAO DE COBRANCAS'
            mudou = True
        
        stats['outro'] += 1
    
    # Outros casos
    else:
        if receita['categoria'] == 'Conciliação Bancária' or not receita['categoria']:
            update_data['categoria'] = 'RECEITAS DIVERSAS'
            mudou = True
        
        stats['outro'] += 1
    
    if mudou:
        updates.append(update_data)
    else:
        stats['sem_mudanca'] += 1

# 3. Mostrar estatísticas
print('📊 ESTATÍSTICAS:\n')
print(f'   Pagamentos PIX:     {stats["pix_pagamento"]}')
print(f'   Recebimentos PIX:   {stats["pix_recebimento"]}')
print(f'   Resgates:           {stats["resgate"]}')
print(f'   Aplicações:         {stats["aplicacao"]}')
print(f'   Outros:             {stats["outro"]}')
print(f'\n   Pessoas extraídas:  {stats["pessoa_extraida"]}')
print(f'   Sem mudança:        {stats["sem_mudanca"]}')
print(f'\n   Total a atualizar:  {len(updates)}')

# 4. Mostrar exemplos
print('\n\n📝 EXEMPLOS DE ATUALIZAÇÕES:\n')

for i, update in enumerate(updates[:10], 1):
    receita_orig = next(r for r in receitas if r['id'] == update['id'])
    print(f'{i}. ID {update["id"]}: {receita_orig["descricao"][:70]}')
    
    if receita_orig['pessoa'] != update['pessoa']:
        print(f'   Pessoa: "{receita_orig["pessoa"]}" → "{update["pessoa"]}"')
    
    if receita_orig['categoria'] != update['categoria']:
        print(f'   Categoria: "{receita_orig["categoria"]}" → "{update["categoria"]}"')
    
    if receita_orig['subcategoria'] != update['subcategoria']:
        print(f'   Subcategoria: "{receita_orig["subcategoria"]}" → "{update["subcategoria"]}"')
    
    print()

# 5. Confirmar
if not AUTO_CONFIRM:
    print('\n' + '='*80)
    resposta = input(f'\n✅ Atualizar {len(updates)} receitas? (s/n): ')
    if resposta.lower() != 's':
        print('\n⏭️ Cancelado pelo usuário')
        cursor.close()
        conn.close()
        sys.exit(0)

print('\n🔄 Atualizando receitas...\n')

# 6. Executar updates em batch
atualizadas = 0
erros = 0

for update in updates:
    try:
        cursor.execute("""
            UPDATE lancamentos
            SET categoria = %s,
                subcategoria = %s,
                pessoa = %s
            WHERE id = %s AND empresa_id = 20
        """, (
            update['categoria'],
            update['subcategoria'],
            update['pessoa'],
            update['id']
        ))
        atualizadas += 1
        
        # Commit a cada 100 registros para evitar perda de dados
        if atualizadas % 100 == 0:
            conn.commit()
            print(f'   ✅ {atualizadas}/{len(updates)} atualizadas (commit feito)...')
    
    except Exception as e:
        erros += 1
        print(f'   ❌ Erro ao atualizar ID {update["id"]}: {e}')

# 7. Commit final
conn.commit()

print(f'\n✅ Processo concluído!')
print(f'   Atualizadas: {atualizadas}')
print(f'   Erros: {erros}')

# 8. Verificar resultado final
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(l.pessoa) as com_pessoa,
        COUNT(l.subcategoria) as com_subcategoria,
        SUM(CASE WHEN l.categoria = 'Conciliação Bancária' THEN 1 ELSE 0 END) as ainda_conciliacao
    FROM lancamentos l
    LEFT JOIN conciliacoes c ON c.lancamento_id = l.id
    WHERE c.lancamento_id IS NULL
      AND UPPER(l.tipo) = 'RECEITA'
      AND l.empresa_id = 20
""")

final = cursor.fetchone()

print(f'\n📊 RESULTADO FINAL:')
print(f'   Total receitas órfãs: {final["total"]}')
print(f'   Com pessoa: {final["com_pessoa"]} ({final["com_pessoa"]/final["total"]*100:.1f}%)')
print(f'   Com subcategoria: {final["com_subcategoria"]} ({final["com_subcategoria"]/final["total"]*100:.1f}%)')
print(f'   Ainda "Conciliação Bancária": {final["ainda_conciliacao"]}')

cursor.close()
conn.close()

print('\n✅ Finalizado!')
