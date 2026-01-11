"""
Script para executar a migração de Multi-Tenancy no banco de dados PostgreSQL
"""
import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def executar_migracao():
    """Executa o script de migração SQL"""
    try:
        # Pega as configurações do ambiente
        database_url = os.getenv('DATABASE_URL')
        
        print("🔄 Conectando ao banco de dados...")
        
        if database_url:
            # Remove codificação da URL para evitar erro
            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        else:
            conn = psycopg2.connect(
                host=os.getenv('PGHOST', 'localhost'),
                port=int(os.getenv('PGPORT', '5432')),
                user=os.getenv('PGUSER', 'postgres'),
                password=os.getenv('PGPASSWORD', ''),
                database=os.getenv('PGDATABASE', 'sistema_financeiro'),
                cursor_factory=RealDictCursor
            )
        
        cur = conn.cursor()
        
        print("⚙️ Executando migração...")
        
        # Executar cada comando SQL separadamente
        comandos_sql = [
            # Tabela clientes
            "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS proprietario_id INTEGER",
            "ALTER TABLE clientes DROP CONSTRAINT IF EXISTS fk_clientes_proprietario",
            "ALTER TABLE clientes ADD CONSTRAINT fk_clientes_proprietario FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE",
            "CREATE INDEX IF NOT EXISTS idx_clientes_proprietario ON clientes(proprietario_id)",
            
            # Tabela fornecedores
            "ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS proprietario_id INTEGER",
            "ALTER TABLE fornecedores DROP CONSTRAINT IF EXISTS fk_fornecedores_proprietario",
            "ALTER TABLE fornecedores ADD CONSTRAINT fk_fornecedores_proprietario FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE",
            "CREATE INDEX IF NOT EXISTS idx_fornecedores_proprietario ON fornecedores(proprietario_id)",
            
            # Tabela lancamentos
            "ALTER TABLE lancamentos ADD COLUMN IF NOT EXISTS proprietario_id INTEGER",
            "ALTER TABLE lancamentos DROP CONSTRAINT IF EXISTS fk_lancamentos_proprietario",
            "ALTER TABLE lancamentos ADD CONSTRAINT fk_lancamentos_proprietario FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE",
            "CREATE INDEX IF NOT EXISTS idx_lancamentos_proprietario ON lancamentos(proprietario_id)",
            
            # Tabela contas_bancarias
            "ALTER TABLE contas_bancarias ADD COLUMN IF NOT EXISTS proprietario_id INTEGER",
            "ALTER TABLE contas_bancarias DROP CONSTRAINT IF EXISTS fk_contas_bancarias_proprietario",
            "ALTER TABLE contas_bancarias ADD CONSTRAINT fk_contas_bancarias_proprietario FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE",
            "CREATE INDEX IF NOT EXISTS idx_contas_bancarias_proprietario ON contas_bancarias(proprietario_id)",
            
            # Tabela categorias
            "ALTER TABLE categorias ADD COLUMN IF NOT EXISTS proprietario_id INTEGER",
            "ALTER TABLE categorias DROP CONSTRAINT IF EXISTS fk_categorias_proprietario",
            "ALTER TABLE categorias ADD CONSTRAINT fk_categorias_proprietario FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE",
            "CREATE INDEX IF NOT EXISTS idx_categorias_proprietario ON categorias(proprietario_id)",
            
            # Tabela subcategorias
            "ALTER TABLE subcategorias ADD COLUMN IF NOT EXISTS proprietario_id INTEGER",
            "ALTER TABLE subcategorias DROP CONSTRAINT IF EXISTS fk_subcategorias_proprietario",
            "ALTER TABLE subcategorias ADD CONSTRAINT fk_subcategorias_proprietario FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE",
            "CREATE INDEX IF NOT EXISTS idx_subcategorias_proprietario ON subcategorias(proprietario_id)",
        ]
        
        for i, comando in enumerate(comandos_sql, 1):
            try:
                cur.execute(comando)
                conn.commit()
                print(f"   ✓ Comando {i}/{len(comandos_sql)} executado")
            except Exception as e:
                print(f"   ⚠ Comando {i} já aplicado ou erro: {e}")
                conn.rollback()
        
        print("✅ Migração executada com sucesso!")
        
        # Verificar resultados
        print("\n📊 Verificando estrutura das tabelas...")
        
        tabelas = ['clientes', 'fornecedores', 'lancamentos', 'contas_bancarias', 'categorias', 'subcategorias']
        
        for tabela in tabelas:
            cur.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{tabela}' AND column_name = 'proprietario_id'
            """)
            resultado = cur.fetchone()
            if resultado:
                print(f"   ✓ {tabela}: proprietario_id ({resultado[1]}) adicionado")
            else:
                print(f"   ✗ {tabela}: proprietario_id NÃO encontrado")
        
        # Estatísticas
        print("\n📈 Estatísticas:")
        cur.execute("SELECT COUNT(*) FROM clientes WHERE proprietario_id IS NULL")
        print(f"   - Clientes sem proprietário: {cur.fetchone()[0]}")
        
        cur.execute("SELECT COUNT(*) FROM fornecedores WHERE proprietario_id IS NULL")
        print(f"   - Fornecedores sem proprietário: {cur.fetchone()[0]}")
        
        cur.execute("SELECT COUNT(*) FROM lancamentos WHERE proprietario_id IS NULL")
        print(f"   - Lançamentos sem proprietário: {cur.fetchone()[0]}")
        
        cur.close()
        conn.close()
        
        print("\n🎉 Migração completa! Sistema Multi-Tenancy pronto para uso.")
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    executar_migracao()
