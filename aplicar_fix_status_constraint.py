#!/usr/bin/env python3
"""
Script para aplicar migration de correção da constraint de status em sessões
"""

import psycopg2
import os
import sys
from pathlib import Path

# Carregar .env se existir
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Arquivo .env carregado de: {env_path}")
except ImportError:
    print("⚠️  python-dotenv não instalado, usando variáveis de ambiente do sistema")

from config import POSTGRESQL_CONFIG

def executar_migration():
    """Executa migration para corrigir constraint de status"""
    
    # 1. Conectar ao banco
    database_url = os.environ.get('DATABASE_URL')
    
    # Se não tiver DATABASE_URL, construir a partir das variáveis do config.py
    if not database_url:
        print("ℹ️  DATABASE_URL não encontrada, usando POSTGRESQL_CONFIG...")
        host = POSTGRESQL_CONFIG['host']
        port = POSTGRESQL_CONFIG['port']
        user = POSTGRESQL_CONFIG['user']
        password = POSTGRESQL_CONFIG['password']
        database = POSTGRESQL_CONFIG['database']
        
        if not all([host, user, password, database]):
            print("❌ Configurações PostgreSQL incompletas")
            print(f"   Host: {host}")
            print(f"   User: {user}")
            print(f"   Database: {database}")
            sys.exit(1)
        
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    print("🔌 Conectando ao banco de dados...")
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        print("=" * 80)
        print("🚀 EXECUTANDO MIGRATION: Fix Status Constraint")
        print("=" * 80)
        
        # 2. Dropar constraint existente
        print("\n📋 PASSO 1: Verificando constraint existente...")
        cursor.execute("""
            SELECT 1 
            FROM information_schema.table_constraints 
            WHERE constraint_name = 'sessoes_status_check' 
            AND table_name = 'sessoes'
        """)
        
        if cursor.fetchone():
            print("   🔍 Constraint encontrada, removendo...")
            cursor.execute("ALTER TABLE sessoes DROP CONSTRAINT sessoes_status_check")
            print("   ✅ Constraint removida com sucesso")
        else:
            print("   ℹ️ Constraint não existe, pulando DROP")
        
        # 2. Verificar status inválidos ANTES de criar constraint
        print("\n📋 PASSO 2: Verificando status inválidos...")
        cursor.execute("""
            SELECT status, COUNT(*) as qtd 
            FROM sessoes 
            WHERE status IS NULL 
            OR status NOT IN ('rascunho', 'agendada', 'em_andamento', 'finalizada', 'cancelada', 'reaberta')
            GROUP BY status
        """)
        invalidos = cursor.fetchall()
        
        if invalidos:
            print("   ⚠️ Status inválidos encontrados:")
            for row in invalidos:
                print(f"      - '{row[0]}': {row[1]} sessões")
            
            print("\n   🔧 Corrigindo status inválidos...")
            cursor.execute("""
                UPDATE sessoes 
                SET status = 'agendada' 
                WHERE status IS NULL 
                OR status NOT IN ('rascunho', 'agendada', 'em_andamento', 'finalizada', 'cancelada', 'reaberta')
            """)
            rows_updated = cursor.rowcount
            print(f"   ✅ {rows_updated} sessões corrigidas")
        else:
            print("   ✅ Nenhum status inválido encontrado")
        
        # 3. Criar nova constraint
        print("\n📋 PASSO 3: Criando nova constraint...")
        cursor.execute("""
            ALTER TABLE sessoes 
            ADD CONSTRAINT sessoes_status_check 
            CHECK (status IN (
                'rascunho',
                'agendada',
                'em_andamento',
                'finalizada',
                'cancelada',
                'reaberta'
            ))
        """)
        print("   ✅ Nova constraint criada com sucesso")
        
        # 4. Verificar resultado
        print("\n📋 PASSO 4: Verificando resultado...")
        cursor.execute("SELECT COUNT(*) FROM sessoes")
        total = cursor.fetchone()[0]
        print(f"   📊 Total de sessões: {total}")
        
        cursor.execute("""
            SELECT status, COUNT(*) as qtd 
            FROM sessoes 
            GROUP BY status 
            ORDER BY qtd DESC
        """)
        
        print("   📊 Distribuição por status:")
        for row in cursor.fetchall():
            print(f"      - {row[0]}: {row[1]} sessões")
        
        print("\n" + "=" * 80)
        print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERRO ao executar migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    executar_migration()
