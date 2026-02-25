"""
🔧 Migration: Adicionar coluna usa_integracao_folha
====================================================

Adiciona a coluna usa_integracao_folha na tabela regras_conciliacao
se ela não existir.

Execução: python migration_add_usa_integracao_folha.py
"""

import psycopg2
import os
import sys
from datetime import datetime


def executar_migration():
    """Adiciona coluna usa_integracao_folha se não existir"""
    
    conn = None
    cursor = None
    
    try:
        # Conectar ao banco
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL não encontrada")
            return False
        
        print("🔌 Conectando ao banco...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        print("✅ Conectado!")
        
        # Verificar se a coluna já existe
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.columns 
            WHERE table_name = 'regras_conciliacao' 
            AND column_name = 'usa_integracao_folha'
        """)
        
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            print("✅ Coluna 'usa_integracao_folha' já existe!")
            return True
        
        print("⚙️  Adicionando coluna 'usa_integracao_folha'...")
        
        # Adicionar coluna
        cursor.execute("""
            ALTER TABLE regras_conciliacao 
            ADD COLUMN IF NOT EXISTS usa_integracao_folha BOOLEAN DEFAULT FALSE
        """)
        
        # Atualizar comment
        cursor.execute("""
            COMMENT ON COLUMN regras_conciliacao.usa_integracao_folha 
            IS 'Se TRUE, busca CPF na descrição e vincula com funcionário da folha'
        """)
        
        conn.commit()
        
        print("✅ Coluna adicionada com sucesso!")
        print("📊 Estrutura atualizada:")
        print("   - usa_integracao_folha BOOLEAN DEFAULT FALSE")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        if conn:
            conn.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("🔌 Conexão fechada")


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 MIGRATION: Adicionar usa_integracao_folha")
    print("=" * 70)
    print()
    
    success = executar_migration()
    
    print()
    print("=" * 70)
    if success:
        print("✅ Migration concluída com sucesso!")
    else:
        print("❌ Migration falhou!")
        sys.exit(1)
    print("=" * 70)
