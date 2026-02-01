#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EXECUTA MIGRATION NO RAILWAY AGORA"""
import psycopg2
import os

# CREDENCIAIS DO RAILWAY
HOST = "centerbeam.proxy.rlwy.net"
PORT = 12659
DATABASE = "railway"
USER = "postgres"
PASSWORD = "JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT"

print("="*80)
print("🚀 CONECTANDO AO RAILWAY E EXECUTANDO MIGRATION")
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
    
    # VERIFICAR TABELAS
    print("\n🔍 Verificando tabelas existentes...")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name IN ('funcoes_evento', 'evento_funcionarios')
    """)
    count = cursor.fetchone()[0]
    print(f"   Encontradas: {count}/2 tabelas")
    
    if count == 2:
        print("\n✅ TABELAS JÁ EXISTEM!")
        cursor.execute("SELECT COUNT(*) FROM funcoes_evento")
        total = cursor.fetchone()[0]
        print(f"   📋 {total} funções cadastradas")
        cursor.close()
        conn.close()
        print("\n🔄 Recarregue a página - está pronto!")
        exit(0)
    
    # LER SQL
    print("\n📂 Lendo migration_evento_funcionarios.sql...")
    sql_path = os.path.join(os.path.dirname(__file__), 'migration_evento_funcionarios.sql')
    
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"✅ SQL lido ({len(sql_content)} caracteres)")
    
    # EXECUTAR
    print("\n📝 EXECUTANDO MIGRATION...")
    cursor.execute(sql_content)
    conn.commit()
    print("✅ SQL EXECUTADO E COMMITADO!")
    
    # VERIFICAR RESULTADO
    print("\n🔍 Verificando tabelas criadas...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name IN ('funcoes_evento', 'evento_funcionarios')
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    print(f"\n✅ {len(tables)} TABELAS CRIADAS:")
    for table in tables:
        print(f"   ✓ {table[0]}")
    
    # CONTAR FUNÇÕES
    cursor.execute("SELECT COUNT(*) FROM funcoes_evento")
    total_funcoes = cursor.fetchone()[0]
    print(f"\n✅ {total_funcoes} FUNÇÕES INSERIDAS")
    
    # LISTAR ALGUMAS FUNÇÕES
    cursor.execute("SELECT nome FROM funcoes_evento ORDER BY nome LIMIT 5")
    funcoes = cursor.fetchall()
    print("\n   Exemplos de funções criadas:")
    for func in funcoes:
        print(f"   • {func[0]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅✅✅ MIGRATION CONCLUÍDA COM SUCESSO! ✅✅✅")
    print("="*80)
    print("\n🔄 RECARREGUE A PÁGINA (F5)")
    print("✅ Sistema de alocação de equipe está FUNCIONANDO!")
    print("\n")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
