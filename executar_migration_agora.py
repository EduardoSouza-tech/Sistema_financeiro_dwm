#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXECUTA MIGRATION NO RAILWAY - VERSÃO SIMPLIFICADA
"""
import psycopg2

# URL PÚBLICA DO RAILWAY (com TCP proxy)
DATABASE_URL = "postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway"

print("="*80)
print("🚀 EXECUTANDO MIGRATION NO RAILWAY")
print("="*80)

try:
    print("\n📡 Conectando ao PostgreSQL do Railway...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    print("✅ Conectado!")
    
    # Verificar tabelas
    print("\n🔍 Verificando tabelas...")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_name IN ('funcoes_evento', 'evento_funcionarios')
    """)
    count = cursor.fetchone()[0]
    print(f"   {count}/2 tabelas encontradas")
    
    if count == 2:
        print("\n✅ Tabelas já existem!")
        cursor.execute("SELECT COUNT(*) FROM funcoes_evento")
        total = cursor.fetchone()[0]
        print(f"   📋 {total} funções cadastradas")
        cursor.close()
        conn.close()
        exit(0)
    
    # Ler SQL
    print("\n📂 Lendo migration...")
    with open('migration_evento_funcionarios.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Executar
    print("📝 Executando SQL...")
    cursor.execute(sql)
    conn.commit()
    print("✅ Commitado!")
    
    # Verificar
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name IN ('funcoes_evento', 'evento_funcionarios')
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    print(f"\n✅ {len(tables)} TABELAS CRIADAS:")
    for t in tables:
        print(f"   ✓ {t[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM funcoes_evento")
    total = cursor.fetchone()[0]
    print(f"\n✅ {total} FUNÇÕES INSERIDAS")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅ MIGRATION CONCLUÍDA!")
    print("="*80)
    print("\n🔄 Recarregue a página (F5) - está pronto!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
