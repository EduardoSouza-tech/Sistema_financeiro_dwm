#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar migration NFS-e DIRETAMENTE no banco do Railway
Conecta direto via PostgreSQL sem precisar de deploy
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

print("="*80)
print("🚀 MIGRATION NFS-e - EXECUTANDO DIRETO NO RAILWAY")
print("="*80)

# URL de conexão do Railway
# Cole aqui a DATABASE_URL do Railway ou defina como variável de ambiente
DATABASE_URL = os.getenv('DATABASE_URL') or input("\n📝 Cole a DATABASE_URL do Railway: ").strip()

if not DATABASE_URL:
    print("❌ DATABASE_URL não fornecida!")
    sys.exit(1)

try:
    print("\n📡 Conectando ao PostgreSQL do Railway...")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("✅ Conexão estabelecida!")
    
    # Verificar se tabelas já existem
    print("\n🔍 Verificando tabelas NFS-e existentes...")
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('nfse_config', 'nfse_baixadas', 'rps', 'nsu_nfse', 'nfse_certificados', 'nfse_audit_log')
    """)
    
    count = cursor.fetchone()['count']
    print(f"   📊 Encontradas {count}/6 tabelas NFS-e")
    
    if count > 0:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('nfse_config', 'nfse_baixadas', 'rps', 'nsu_nfse', 'nfse_certificados', 'nfse_audit_log')
            ORDER BY table_name
        """)
        existentes = cursor.fetchall()
        print("\n   Tabelas encontradas:")
        for t in existentes:
            print(f"   ✓ {t['table_name']}")
        
        resposta = input("\n⚠️ Deseja recriar/atualizar as tabelas? (s/N): ").lower()
        if resposta != 's':
            print("\n✅ Operação cancelada")
            cursor.close()
            conn.close()
            sys.exit(0)
    
    # Ler arquivo SQL
    print("\n📂 Lendo migration_nfse.sql...")
    sql_file = os.path.join(os.path.dirname(__file__), 'migration_nfse.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ Arquivo não encontrado: {sql_file}")
        sys.exit(1)
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"✅ SQL lido ({len(sql_content)} caracteres)")
    
    # Executar SQL
    print("\n📝 Executando migration NFS-e...")
    cursor.execute(sql_content)
    conn.commit()
    print("✅ SQL executado e commitado!")
    
    # Verificar criação
    print("\n🔍 Verificando resultado...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('nfse_config', 'nfse_baixadas', 'rps', 'nsu_nfse', 'nfse_certificados', 'nfse_audit_log')
        ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    print(f"\n✅ {len(tables)} TABELAS NFS-e CRIADAS:")
    for table in tables:
        # Contar registros
        cursor.execute(f"SELECT COUNT(*) as count FROM {table['table_name']}")
        count = cursor.fetchone()['count']
        print(f"   ✓ {table['table_name']}: {count} registros")
    
    # Verificar views
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'vw_nfse%'
        ORDER BY table_name
    """)
    views = cursor.fetchall()
    
    if views:
        print(f"\n✅ {len(views)} VIEWS CRIADAS:")
        for view in views:
            print(f"   ✓ {view['table_name']}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅ MIGRATION NFS-e CONCLUÍDA COM SUCESSO!")
    print("="*80)
    print("\n📋 Tabelas criadas:")
    print("   • nfse_config - Configurações de municípios")
    print("   • nfse_baixadas - NFS-e consultadas")
    print("   • rps - Recibos Provisórios")
    print("   • nsu_nfse - Controle NSU")
    print("   • nfse_certificados - Certificados digitais")
    print("   • nfse_audit_log - Log de auditoria")
    print("\n🔄 Recarregue a página do sistema (Ctrl + Shift + R)")
    print("✅ O módulo NFS-e está pronto para uso!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
