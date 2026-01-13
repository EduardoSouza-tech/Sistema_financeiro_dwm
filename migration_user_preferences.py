"""
Migração: Criação da tabela user_preferences
"""
import os
import psycopg2
from urllib.parse import urlparse

def executar_migracao():
    """Cria a tabela user_preferences se não existir"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL não configurada")
        return False
    
    # Parse da URL para obter componentes
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    try:
        # Conectar ao banco
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Criar tabela se não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                preferencia_chave VARCHAR(100) NOT NULL,
                preferencia_valor TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(usuario_id, preferencia_chave)
            );
        """)
        
        # Criar índices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_preferences_usuario 
            ON user_preferences(usuario_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_preferences_chave 
            ON user_preferences(preferencia_chave);
        """)
        
        conn.commit()
        print("✅ Migração user_preferences: Tabela criada/verificada com sucesso")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro na migração user_preferences: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    executar_migracao()
