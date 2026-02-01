#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar migration DIRETAMENTE no banco do Railway
Conecta direto via PostgreSQL sem precisar de deploy
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

print("="*80)
print("🚀 EXECUTANDO MIGRATION DIRETO NO RAILWAY")
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
    print("\n🔍 Verificando tabelas existentes...")
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('funcoes_evento', 'evento_funcionarios')
    """)
    
    count = cursor.fetchone()['count']
    print(f"   📊 Encontradas {count}/2 tabelas")
    
    if count == 2:
        print("\n✅ Tabelas já existem!")
        
        # Contar funções
        cursor.execute("SELECT COUNT(*) as total FROM funcoes_evento")
        total_funcoes = cursor.fetchone()['total']
        print(f"   📋 {total_funcoes} funções cadastradas")
        
        resposta = input("\n⚠️ Deseja recriar as tabelas? (s/N): ").lower()
        if resposta != 's':
            print("\n✅ Operação cancelada")
            cursor.close()
            conn.close()
            sys.exit(0)
        
        print("\n🗑️ Removendo tabelas antigas...")
        cursor.execute("DROP TABLE IF EXISTS evento_funcionarios CASCADE")
        cursor.execute("DROP TABLE IF EXISTS funcoes_evento CASCADE")
        conn.commit()
        print("✅ Tabelas removidas")
    
    # Ler arquivo SQL
    print("\n📂 Lendo arquivo SQL...")
    sql_file = os.path.join(os.path.dirname(__file__), 'migration_evento_funcionarios.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ Arquivo não encontrado: {sql_file}")
        sys.exit(1)
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"✅ SQL lido ({len(sql_content)} bytes)")
    
    # Executar SQL
    print("\n📝 Executando migration...")
    cursor.execute(sql_content)
    conn.commit()
    print("✅ SQL executado e commitado!")
    
    # Verificar criação
    print("\n🔍 Verificando resultado...")
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
        print(f"   ✓ {table['table_name']}")
    
    # Contar funções
    cursor.execute("SELECT COUNT(*) as total FROM funcoes_evento")
    count_funcoes = cursor.fetchone()['total']
    print(f"\n✅ {count_funcoes} FUNÇÕES INSERIDAS")
    
    # Listar algumas funções
    cursor.execute("SELECT nome FROM funcoes_evento ORDER BY nome LIMIT 5")
    funcoes = cursor.fetchall()
    print("\n   Exemplos:")
    for func in funcoes:
        print(f"   • {func['nome']}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
    print("="*80)
    print("\n🔄 Recarregue a página do sistema (F5)")
    print("✅ O sistema de alocação de equipe está pronto!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
