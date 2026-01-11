#!/usr/bin/env python3
"""
Script para executar migrations do banco de dados
Executa automaticamente no startup do Railway
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Obtém conexão com o banco PostgreSQL"""
    return psycopg2.connect(
        host=os.getenv('PGHOST'),
        database=os.getenv('PGDATABASE'),
        user=os.getenv('PGUSER'),
        password=os.getenv('PGPASSWORD'),
        port=os.getenv('PGPORT', 5432)
    )

def run_migration_user_preferences():
    """Executa migration 007 - user_preferences"""
    
    sql = """
    -- Criar tabela de preferências se não existir
    CREATE TABLE IF NOT EXISTS user_preferences (
        id SERIAL PRIMARY KEY,
        usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        preferencia_chave VARCHAR(100) NOT NULL,
        preferencia_valor TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Índice único: um usuário só pode ter uma preferência por chave
        UNIQUE(usuario_id, preferencia_chave)
    );
    
    -- Criar índices para melhorar performance
    CREATE INDEX IF NOT EXISTS idx_user_preferences_usuario_id ON user_preferences(usuario_id);
    CREATE INDEX IF NOT EXISTS idx_user_preferences_chave ON user_preferences(preferencia_chave);
    
    -- Criar função para atualizar updated_at
    CREATE OR REPLACE FUNCTION update_user_preferences_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    -- Criar trigger se não existir
    DROP TRIGGER IF EXISTS trigger_update_user_preferences_updated_at ON user_preferences;
    CREATE TRIGGER trigger_update_user_preferences_updated_at
        BEFORE UPDATE ON user_preferences
        FOR EACH ROW
        EXECUTE FUNCTION update_user_preferences_updated_at();
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("🔧 Executando migration: user_preferences...")
        
        cursor.execute(sql)
        conn.commit()
        
        print("✅ Migration user_preferences executada com sucesso!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao executar migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_migrations():
    """Executa todas as migrations pendentes"""
    
    print("="*60)
    print("🚀 Executando Migrations do Banco de Dados")
    print("="*60)
    
    migrations = [
        ("user_preferences", run_migration_user_preferences),
    ]
    
    for nome, funcao in migrations:
        print(f"\n📋 Migration: {nome}")
        sucesso = funcao()
        if sucesso:
            print(f"   ✅ {nome} OK")
        else:
            print(f"   ❌ {nome} FALHOU")
    
    print("\n" + "="*60)
    print("✅ Migrations concluídas!")
    print("="*60 + "\n")

if __name__ == '__main__':
    run_all_migrations()
