"""
Script para limpar categorias duplicadas
Mantém apenas a versão com ID menor (mais antiga)
"""
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print('\n' + '='*80)
print('🧹 LIMPANDO CATEGORIAS DUPLICADAS')
print('='*80)

# Listar todas as categorias
cur.execute("""
    SELECT id, nome, tipo, empresa_id 
    FROM categorias 
    ORDER BY empresa_id, nome, id
""")
categorias = cur.fetchall()

print(f'\n📊 Total de categorias: {len(categorias)}')
print('\n📋 Listagem atual:')
for cat in categorias:
    print(f"  ID={cat['id']:<3} | Nome={cat['nome']:<40} | Tipo={cat['tipo']:<10} | Empresa={cat['empresa_id']}")

# Encontrar duplicatas (mesmo nome + empresa_id)
duplicatas = {}
for cat in categorias:
    chave = (cat['nome'].strip().upper(), cat['empresa_id'])
    if chave not in duplicatas:
        duplicatas[chave] = []
    duplicatas[chave].append(cat)

# Filtrar apenas as que têm duplicatas
duplicatas_real = {k: v for k, v in duplicatas.items() if len(v) > 1}

if not duplicatas_real:
    print('\n✅ Nenhuma duplicata encontrada!')
    cur.close()
    conn.close()
    exit(0)

print(f'\n⚠️  Encontradas {len(duplicatas_real)} categorias duplicadas:')
print('='*80)

ids_para_excluir = []

for (nome, empresa), lista in duplicatas_real.items():
    print(f'\n📁 Categoria: {nome} (Empresa: {empresa})')
    print(f'   Total de duplicatas: {len(lista)}')
    
    # Ordenar por ID (manter o menor)
    lista_ordenada = sorted(lista, key=lambda x: x['id'])
    manter = lista_ordenada[0]
    excluir = lista_ordenada[1:]
    
    print(f'   ✅ MANTER: ID={manter["id"]} (mais antiga)')
    
    for cat in excluir:
        print(f'   ❌ EXCLUIR: ID={cat["id"]}')
        ids_para_excluir.append(cat['id'])

print('\n' + '='*80)
print(f'📊 Resumo: {len(ids_para_excluir)} categoria(s) serão excluídas')
print('='*80)

if ids_para_excluir:
    resposta = input('\n⚠️  Confirma exclusão? (s/n): ').strip().lower()
    
    if resposta == 's':
        print('\n🗑️  Excluindo duplicatas...')
        
        for cat_id in ids_para_excluir:
            cur.execute('DELETE FROM categorias WHERE id = %s', (cat_id,))
            print(f'   ❌ Excluído ID={cat_id}')
        
        conn.commit()
        print(f'\n✅ {len(ids_para_excluir)} categoria(s) excluída(s) com sucesso!')
    else:
        print('\n❌ Operação cancelada')
        conn.rollback()
else:
    print('\n✅ Nenhuma duplicata para excluir!')

cur.close()
conn.close()

print('\n' + '='*80)
print('🏁 Script finalizado')
print('='*80 + '\n')
