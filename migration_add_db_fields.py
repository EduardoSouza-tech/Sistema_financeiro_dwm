"""
Script para adicionar campos de configuração de banco na tabela empresas
Execute este script NO BANCO ADMIN
"""

import psycopg2
import os

# Configuração do banco admin
ADMIN_DB_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': int(os.getenv('PGPORT', '5432')),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', ''),
    'database': os.getenv('PGDATABASE', 'sistema_financeiro')
}

def migrate_empresas_table():
    """Adiciona campos de configuração de banco na tabela empresas"""
    try:
        conn = psycopg2.connect(**ADMIN_DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔄 Adicionando campos de configuração de banco...")
        
        # SQL para adicionar campos
        sql = """
        -- Adicionar campos de configuração do banco separado
        ALTER TABLE empresas 
        ADD COLUMN IF NOT EXISTS db_host VARCHAR(255),
        ADD COLUMN IF NOT EXISTS db_port INTEGER DEFAULT 5432,
        ADD COLUMN IF NOT EXISTS db_name VARCHAR(100),
        ADD COLUMN IF NOT EXISTS db_user VARCHAR(100),
        ADD COLUMN IF NOT EXISTS db_password_encrypted TEXT,
        ADD COLUMN IF NOT EXISTS db_ready BOOLEAN DEFAULT FALSE;
        
        -- Adicionar índice
        CREATE INDEX IF NOT EXISTS idx_empresas_db_ready ON empresas(db_ready);
        
        -- Adicionar comentários
        COMMENT ON COLUMN empresas.db_host IS 'Host do banco de dados da empresa';
        COMMENT ON COLUMN empresas.db_port IS 'Porta do banco de dados da empresa';
        COMMENT ON COLUMN empresas.db_name IS 'Nome do database da empresa';
        COMMENT ON COLUMN empresas.db_user IS 'Usuário do banco da empresa';
        COMMENT ON COLUMN empresas.db_password_encrypted IS 'Senha criptografada do banco';
        COMMENT ON COLUMN empresas.db_ready IS 'Indica se o banco está pronto para uso';
        """
        
        cursor.execute(sql)
        conn.commit()
        
        print("✅ Campos adicionados com sucesso!")
        
        # Verificar colunas
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'empresas'
            AND column_name LIKE 'db_%'
            ORDER BY column_name
        """)
        
        print("\n📋 Colunas adicionadas:")
        for row in cursor.fetchall():
            print(f"   • {row[0]}: {row[1]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        return False

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║  📦 MIGRAÇÃO: Adicionar campos DB na tabela empresas     ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    print(f"🔗 Conectando ao banco: {ADMIN_DB_CONFIG['database']}")
    print(f"🏢 Host: {ADMIN_DB_CONFIG['host']}")
    
    if migrate_empresas_table():
        print("\n✅ Migração concluída com sucesso!")
        print("\n📝 Próximos passos:")
        print("   1. Configure DATABASE_ADMIN_URL no Railway")
        print("   2. Crie databases separados para cada empresa")
        print("   3. Use database_manager.py para gerenciar conexões")
    else:
        print("\n❌ Migração falhou!")
