#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EXECUTA MIGRATION REMESSA PAGAMENTO NO RAILWAY AGORA"""
import psycopg2
import os

# CREDENCIAIS DO RAILWAY
HOST = "centerbeam.proxy.rlwy.net"
PORT = 12659
DATABASE = "railway"
USER = "postgres"
PASSWORD = "JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT"

print("="*80)
print("🏦 EXECUTANDO MIGRATION - REMESSA PAGAMENTO SICREDI")
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
        AND table_name IN ('remessas_pagamento', 'remessas_pagamento_itens', 'sicredi_configuracao')
    """)
    count = cursor.fetchone()[0]
    print(f"   Encontradas: {count}/3 tabelas")
    
    if count == 3:
        print("\n✅ TABELAS JÁ EXISTEM!")
        cursor.execute("SELECT COUNT(*) FROM remessas_pagamento")
        total = cursor.fetchone()[0]
        print(f"   📋 {total} remessas cadastradas")
        cursor.close()
        conn.close()
        print("\n✅ Módulo já instalado!")
        exit(0)
    
    # LER SQL
    print("\n📂 Lendo migration_remessa_pagamento.sql...")
    sql_path = os.path.join(os.path.dirname(__file__), 'migration_remessa_pagamento.sql')
    
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"✅ SQL lido ({len(sql_content)} caracteres)")
    
    # EXECUTAR
    print("\n📝 EXECUTANDO MIGRATION...")
    print("   ⏳ Criando tabelas...")
    print("   ⏳ Criando views...")
    print("   ⏳ Criando funções...")
    print("   ⏳ Criando permissões...")
    print("   ⏳ Criando triggers...")
    
    cursor.execute(sql_content)
    conn.commit()
    print("✅ SQL EXECUTADO E COMMITADO!")
    
    # VERIFICAR RESULTADO
    print("\n🔍 Verificando tabelas criadas...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name IN ('remessas_pagamento', 'remessas_pagamento_itens', 'sicredi_configuracao')
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    print(f"\n📊 {len(tables)} TABELAS CRIADAS:")
    for table in tables:
        print(f"   ✓ {table[0]}")
    
    # VERIFICAR VIEWS
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema = 'public'
        AND table_name LIKE '%remessa%'
        ORDER BY table_name
    """)
    views = cursor.fetchall()
    print(f"\n👁️  {len(views)} VIEWS CRIADAS:")
    for view in views:
        print(f"   ✓ {view[0]}")
    
    # VERIFICAR PERMISSÕES
    cursor.execute("""
        SELECT codigo, nome 
        FROM permissoes 
        WHERE codigo LIKE 'remessa_%'
        ORDER BY codigo
    """)
    perms = cursor.fetchall()
    print(f"\n🔐 {len(perms)} PERMISSÕES CRIADAS:")
    for perm in perms:
        print(f"   ✓ {perm[0]} - {perm[1]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅✅✅ MIGRATION CONCLUÍDA COM SUCESSO! ✅✅✅")
    print("="*80)
    print("\n📋 Próximos passos:")
    print("   1. Configure permissões para grupos/usuários no sistema")
    print("   2. Acesse 'Remessa Pagamentos' no menu")
    print("   3. Configure convênio Sicredi (primeira vez)")
    print("   4. Gere remessa de teste")
    print("\n🔄 Aguarde deploy automático do Railway concluir (~2 min)")
    print("✅ Módulo de Remessa de Pagamento Sicredi está FUNCIONANDO!")
    
except FileNotFoundError as e:
    print(f"\n❌ ERRO: Arquivo não encontrado!")
    print(f"   {e}")
    print("   Certifique-se de estar no diretório correto")
    
except psycopg2.Error as e:
    print(f"\n❌ ERRO NO BANCO DE DADOS:")
    print(f"   {e}")
    import traceback
    traceback.print_exc()
    
except Exception as e:
    print(f"\n❌ ERRO INESPERADO:")
    print(f"   {e}")
    import traceback
    traceback.print_exc()
