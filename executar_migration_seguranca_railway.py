#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar migration de SEGURANÇA CRÍTICA no Railway
Adiciona coluna empresa_id à tabela lancamentos para corrigir vazamento de dados

VULNERABILIDADE CORRIGIDA:
- Usuários podiam ver lançamentos de outras empresas
- Faltava coluna empresa_id na tabela lancamentos
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

print("="*80)
print("🔐 MIGRATION DE SEGURANÇA CRÍTICA - RAILWAY")
print("="*80)
print("\n⚠️  CORRIGINDO: Vazamento de dados entre empresas")
print("📋 AÇÃO: Adicionar empresa_id à tabela lancamentos\n")

# Tentar construir DATABASE_URL a partir das variáveis individuais do Railway
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    # Tentar construir a partir das variáveis individuais
    pg_user = os.getenv('POSTGRES_USER') or os.getenv('PGUSER')
    pg_password = os.getenv('POSTGRES_PASSWORD') or os.getenv('PGPASSWORD')
    pg_database = os.getenv('POSTGRES_DB') or os.getenv('PGDATABASE')
    pg_host = os.getenv('PGHOST')
    pg_port = os.getenv('PGPORT', '5432')
    
    if all([pg_user, pg_password, pg_database, pg_host]):
        DATABASE_URL = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
        print(f"🔧 DATABASE_URL construída a partir das variáveis:")
        print(f"   User: {pg_user}")
        print(f"   Database: {pg_database}")
        print(f"   Host: {pg_host}")
        print(f"   Port: {pg_port}\n")
    else:
        print("📝 DATABASE_URL não encontrada nas variáveis de ambiente")
        print("\n   Forneça a URL completa do Railway PostgreSQL")
        print("   Formato: postgresql://user:password@host:port/database\n")
        DATABASE_URL = input("   Cole a DATABASE_URL: ").strip()

if not DATABASE_URL:
    print("❌ DATABASE_URL não fornecida!")
    sys.exit(1)

try:
    print("\n📡 Conectando ao PostgreSQL do Railway...")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    conn.autocommit = False  # Usar transação
    cursor = conn.cursor()
    print("✅ Conexão estabelecida!")
    
    # Verificar se coluna já existe
    print("\n🔍 Verificando estado atual da tabela lancamentos...")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'lancamentos' AND column_name = 'empresa_id'
    """)
    
    coluna_existe = cursor.fetchone()
    
    if coluna_existe:
        print(f"✅ Coluna empresa_id JÁ EXISTE!")
        print(f"   Tipo: {coluna_existe['data_type']}")
        print(f"   Nullable: {coluna_existe['is_nullable']}")
        
        # Verificar estatísticas
        cursor.execute("SELECT COUNT(*) as total FROM lancamentos")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as sem_empresa FROM lancamentos WHERE empresa_id IS NULL")
        sem_empresa = cursor.fetchone()['sem_empresa']
        
        print(f"\n📊 Estatísticas:")
        print(f"   Total de lançamentos: {total}")
        print(f"   Com empresa_id: {total - sem_empresa}")
        print(f"   Sem empresa_id: {sem_empresa}")
        
        if sem_empresa > 0:
            print(f"\n⚠️  ATENÇÃO: {sem_empresa} lançamentos sem empresa_id!")
            
            # Verificar número de empresas
            cursor.execute("SELECT COUNT(*) as count FROM empresas")
            num_empresas = cursor.fetchone()['count']
            
            if num_empresas == 1:
                cursor.execute("SELECT id, nome FROM empresas LIMIT 1")
                empresa = cursor.fetchone()
                print(f"\n   Existe apenas 1 empresa: {empresa['nome']} (ID: {empresa['id']})")
                
                resposta = input(f"   Atribuir todos os {sem_empresa} lançamentos à empresa ID {empresa['id']}? (S/N): ")
                
                if resposta.upper() == 'S':
                    cursor.execute(f"UPDATE lancamentos SET empresa_id = {empresa['id']} WHERE empresa_id IS NULL")
                    print(f"   ✅ {cursor.rowcount} lançamentos atualizados!")
                    conn.commit()
                else:
                    print("   ⏭️  Pulando atribuição automática")
            else:
                print(f"\n   Existem {num_empresas} empresas cadastradas")
                print("   Você precisa atribuir manualmente cada lançamento")
        else:
            print("\n   ✅ Todos os lançamentos têm empresa_id!")
        
        print("\n🎉 Migração já foi aplicada anteriormente!")
        cursor.close()
        conn.close()
        sys.exit(0)
    
    print("❌ Coluna empresa_id NÃO EXISTE - Executando migração...\n")
    
    # Ler o script SQL
    script_path = os.path.join(os.path.dirname(__file__), 'migration_add_empresa_id_lancamentos.sql')
    
    if not os.path.exists(script_path):
        print(f"❌ Arquivo SQL não encontrado: {script_path}")
        cursor.close()
        conn.close()
        sys.exit(1)
    
    print(f"📄 Lendo script: migration_add_empresa_id_lancamentos.sql")
    
    with open(script_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # Executar o script
    print("\n⚙️  Executando migração SQL...")
    print("-" * 80)
    
    cursor.execute(sql_script)
    
    # Buscar mensagens de retorno da função DO
    messages = cursor.fetchall()
    if messages:
        for msg in messages:
            if isinstance(msg, dict):
                print(f"   {msg.get('message', msg)}")
            else:
                print(f"   {msg}")
    
    print("-" * 80)
    
    # Commit da transação
    conn.commit()
    print("\n✅ Migração executada com sucesso!")
    
    # Verificar resultados
    print("\n📊 Verificando resultados...")
    
    # Verificar se a coluna foi criada
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'lancamentos' AND column_name = 'empresa_id'
    """)
    
    coluna = cursor.fetchone()
    if coluna:
        print(f"   ✅ Coluna empresa_id criada!")
        print(f"      Tipo: {coluna['data_type']}")
        print(f"      Nullable: {coluna['is_nullable']}")
    else:
        print("   ❌ ERRO: Coluna empresa_id não foi criada!")
        cursor.close()
        conn.close()
        sys.exit(1)
    
    # Contar lançamentos
    cursor.execute("SELECT COUNT(*) as total FROM lancamentos")
    total = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as sem_empresa FROM lancamentos WHERE empresa_id IS NULL")
    sem_empresa = cursor.fetchone()['sem_empresa']
    
    print(f"\n📈 Estatísticas:")
    print(f"   Total de lançamentos: {total}")
    print(f"   Com empresa_id: {total - sem_empresa}")
    print(f"   Sem empresa_id: {sem_empresa}")
    
    if sem_empresa > 0:
        print(f"\n⚠️  ATENÇÃO: {sem_empresa} lançamentos ainda sem empresa_id!")
        
        # Verificar número de empresas
        cursor.execute("SELECT COUNT(*) as count FROM empresas")
        num_empresas = cursor.fetchone()['count']
        
        if num_empresas == 1:
            cursor.execute("SELECT id, nome FROM empresas LIMIT 1")
            empresa = cursor.fetchone()
            print(f"\n   ✨ Auto-atribuição disponível!")
            print(f"   Empresa: {empresa['nome']} (ID: {empresa['id']})")
            
            resposta = input(f"\n   Atribuir todos à empresa {empresa['id']}? (S/N): ")
            
            if resposta.upper() == 'S':
                cursor.execute(f"UPDATE lancamentos SET empresa_id = {empresa['id']} WHERE empresa_id IS NULL")
                linhas = cursor.rowcount
                conn.commit()
                print(f"   ✅ {linhas} lançamentos atualizados!")
            else:
                print("   ⏭️  Pulando atribuição")
        else:
            print(f"\n   Existem {num_empresas} empresas - atribuição manual necessária")
    else:
        print("\n   ✅ Todos os lançamentos têm empresa_id!")
    
    # Verificar índice
    cursor.execute("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'lancamentos' AND indexname = 'idx_lancamentos_empresa_id'
    """)
    
    indice = cursor.fetchone()
    if indice:
        print(f"\n   ✅ Índice criado: {indice['indexname']}")
    else:
        print("\n   ⚠️  Índice não encontrado (será criado automaticamente)")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*80)
    print("\n🔒 O sistema agora isola lançamentos por empresa")
    print("\n✅ Próximos passos:")
    print("   1. Verificar que usuários veem apenas seus lançamentos")
    print("   2. Testar com múltiplas empresas")
    print("   3. Considerar adicionar NOT NULL constraint após validação")
    print("\n")
    
except psycopg2.Error as e:
    print(f"\n❌ ERRO NO BANCO DE DADOS:")
    print(f"   {e}")
    if conn:
        conn.rollback()
        print("\n🔄 Rollback executado - nenhuma alteração foi feita")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ ERRO INESPERADO:")
    print(f"   {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    if conn:
        conn.rollback()
        print("\n🔄 Rollback executado - nenhuma alteração foi feita")
    sys.exit(1)
