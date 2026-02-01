#!/usr/bin/env python3
"""
Script para corrigir constraint UNIQUE de categorias
Permite que empresas diferentes tenham categorias com mesmo nome
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

# Conectar ao banco
conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME', 'railway'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432')
)
conn.autocommit = False
cursor = conn.cursor(cursor_factory=RealDictCursor)

try:
    print("\n" + "="*80)
    print("🔧 CORRIGINDO CONSTRAINT DE CATEGORIAS")
    print("="*80)
    
    # 1. Verificar constraints atuais
    print("\n📋 Constraints atuais:")
    cursor.execute("""
        SELECT 
            conname AS constraint_name,
            contype AS constraint_type,
            pg_get_constraintdef(oid) AS constraint_definition
        FROM pg_constraint
        WHERE conrelid = 'categorias'::regclass
        ORDER BY conname
    """)
    constraints = cursor.fetchall()
    for c in constraints:
        print(f"   - {c['constraint_name']}: {c['constraint_definition']}")
    
    # 2. Remover constraint antiga
    print("\n🗑️ Removendo constraint categorias_nome_key...")
    cursor.execute("ALTER TABLE categorias DROP CONSTRAINT IF EXISTS categorias_nome_key")
    print("   ✅ Constraint removida")
    
    # 3. Adicionar constraint composta
    print("\n➕ Adicionando constraint categorias_nome_empresa_unique...")
    cursor.execute("""
        ALTER TABLE categorias 
        ADD CONSTRAINT categorias_nome_empresa_unique 
        UNIQUE (nome, empresa_id)
    """)
    print("   ✅ Constraint adicionada")
    
    # 4. Verificar constraints finais
    print("\n📋 Constraints após correção:")
    cursor.execute("""
        SELECT 
            conname AS constraint_name,
            contype AS constraint_type,
            pg_get_constraintdef(oid) AS constraint_definition
        FROM pg_constraint
        WHERE conrelid = 'categorias'::regclass
        ORDER BY conname
    """)
    constraints = cursor.fetchall()
    for c in constraints:
        print(f"   - {c['constraint_name']}: {c['constraint_definition']}")
    
    # Commit
    conn.commit()
    print("\n✅ Correção aplicada com sucesso!")
    print("="*80 + "\n")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    cursor.close()
    conn.close()
