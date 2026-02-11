#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EXECUTA MIGRATION DE FORNECEDORES NO RAILWAY AGORA"""
import psycopg2
import os

# CREDENCIAIS DO RAILWAY
HOST = "centerbeam.proxy.rlwy.net"
PORT = 12659
DATABASE = "railway"
USER = "postgres"
PASSWORD = "JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT"

print("="*80)
print("🚀 MIGRATION: SCHEMA COMPLETO FORNECEDORES")
print("="*80)

try:
    # CONECTAR
    print(f"\n📡 Conectando a {HOST}:{PORT}...")
    conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        database=DATABASE,
        user=USER,
        password=PASSWORD
    )
    cursor = conn.cursor()
    print("✅ CONECTADO!")
    
    # VERIFICAR ESTRUTURA ATUAL
    print("\n🔍 Verificando estrutura atual da tabela fornecedores...")
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'fornecedores'
        ORDER BY ordinal_position
    """)
    colunas_antes = cursor.fetchall()
    print(f"   📊 Colunas atuais: {len(colunas_antes)}")
    for col in colunas_antes[:5]:  # Mostrar apenas primeiras 5
        print(f"      - {col[0]} ({col[1]})")
    if len(colunas_antes) > 5:
        print(f"      ... e mais {len(colunas_antes) - 5} colunas")
    
    # Verificar se já tem razao_social
    colunas_nomes = [col[0] for col in colunas_antes]
    if 'razao_social' in colunas_nomes:
        print("\n✅ MIGRATION JÁ FOI APLICADA!")
        print("   Tabela fornecedores já tem schema completo")
        cursor.close()
        conn.close()
        print("\n🔄 Recarregue a página - está pronto!")
        exit(0)
    
    # LER SQL
    print("\n📂 Lendo migration_fornecedores_schema_completo.sql...")
    sql_path = os.path.join(os.path.dirname(__file__), 'migration_fornecedores_schema_completo.sql')
    
    if not os.path.exists(sql_path):
        print(f"❌ Arquivo não encontrado: {sql_path}")
        exit(1)
    
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"✅ SQL lido ({len(sql_content)} caracteres)")
    
    # EXECUTAR
    print("\n📝 EXECUTANDO MIGRATION...")
    print("   ⏳ Aguarde... (adicionando colunas)")
    cursor.execute(sql_content)
    conn.commit()
    print("✅ SQL EXECUTADO E COMMITADO!")
    
    # VERIFICAR RESULTADO
    print("\n🔍 Verificando estrutura APÓS migration...")
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'fornecedores'
        ORDER BY ordinal_position
    """)
    colunas_depois = cursor.fetchall()
    print(f"   📊 Colunas agora: {len(colunas_depois)}")
    
    # Encontrar novas colunas
    novas_colunas = [col for col in colunas_depois if col[0] not in colunas_nomes]
    if novas_colunas:
        print(f"\n✅ {len(novas_colunas)} NOVAS COLUNAS ADICIONADAS:")
        for col in novas_colunas:
            tipo = f"{col[1]}"
            if col[2]:
                tipo += f"({col[2]})"
            print(f"   + {col[0]} ({tipo})")
    
    # VERIFICAR ÍNDICES
    print("\n🔍 Verificando índices criados...")
    cursor.execute("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'fornecedores'
        AND indexname LIKE 'idx_fornecedores_%'
    """)
    indices = cursor.fetchall()
    if indices:
        print(f"   ✅ {len(indices)} índices criados:")
        for idx in indices[:5]:  # Mostrar apenas primeiros 5
            print(f"      - {idx[0]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅✅✅ MIGRATION CONCLUÍDA COM SUCESSO! ✅✅✅")
    print("="*80)
    print("\n📋 Novas colunas disponíveis:")
    print("   ✓ razao_social, nome_fantasia")
    print("   ✓ cnpj, documento, ie, im")
    print("   ✓ cep, rua, logradouro, numero, complemento, bairro, cidade, estado")
    print("   ✓ empresa_id, proprietario_id, contato")
    print("\n🔄 RECARREGUE A PÁGINA (F5)")
    print("✅ Agora você pode cadastrar fornecedores com dados completos!")
    print("\n")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
