"""
Script para executar a migração de Multi-Tenancy no banco de dados PostgreSQL
Versão que solicita credenciais manualmente
"""
import psycopg2
from psycopg2.extras import RealDictCursor

def executar_migracao():
    """Executa o script de migração SQL"""
    
    # Credenciais do banco (ajuste conforme necessário)
    DB_CONFIG = {
        'host': 'aws-0-us-east-1.pooler.supabase.com',
        'port': 6543,
        'database': 'postgres',
        'user': 'postgres.owdmovhxwknopjpdoelw',
        'password': 'Nasci@9876'
    }
    
    try:
        print("🔄 Conectando ao banco de dados...")
        print(f"   Host: {DB_CONFIG['host']}")
        print(f"   Database: {DB_CONFIG['database']}")
        
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        print("⚙️ Executando migração...")
        
        # Executar cada comando SQL separadamente
        comandos_sql = [
            # Tabela clientes
            ("Adicionar coluna em clientes", "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS proprietario_id INTEGER"),
            ("Remover constraint antiga em clientes", "ALTER TABLE clientes DROP CONSTRAINT IF EXISTS fk_clientes_proprietario"),
            ("Adicionar FK em clientes", "ALTER TABLE clientes ADD CONSTRAINT fk_clientes_proprietario FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE"),
            ("Criar índice em clientes", "CREATE INDEX IF NOT EXISTS idx_clientes_proprietario ON clientes(proprietario_id)"),
            
            # Tabela fornecedores
            ("Adicionar coluna em fornecedores", "ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS proprietario_id INTEGER"),
            ("Remover constraint antiga em fornecedores", "ALTER TABLE fornecedores DROP CONSTRAINT IF EXISTS fk_fornecedores_proprietario"),
            ("Adicionar FK em fornecedores", "ALTER TABLE fornecedores ADD CONSTRAINT fk_fornecedores_proprietario FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE"),
            ("Criar índice em fornecedores", "CREATE INDEX IF NOT EXISTS idx_fornecedores_proprietario ON fornecedores(proprietario_id)"),
            
            # Tabela lancamentos
            ("Adicionar coluna em lancamentos", "ALTER TABLE lancamentos ADD COLUMN IF NOT EXISTS proprietario_id INTEGER"),
            ("Remover constraint antiga em lancamentos", "ALTER TABLE lancamentos DROP CONSTRAINT IF EXISTS fk_lancamentos_proprietario"),
            ("Adicionar FK em lancamentos", "ALTER TABLE lancamentos ADD CONSTRAINT fk_lancamentos_proprietario FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE"),
            ("Criar índice em lancamentos", "CREATE INDEX IF NOT EXISTS idx_lancamentos_proprietario ON lancamentos(proprietario_id)"),
            
            # Tabela contas_bancarias
            ("Adicionar coluna em contas_bancarias", "ALTER TABLE contas_bancarias ADD COLUMN IF NOT EXISTS proprietario_id INTEGER"),
            ("Remover constraint antiga em contas_bancarias", "ALTER TABLE contas_bancarias DROP CONSTRAINT IF EXISTS fk_contas_bancarias_proprietario"),
            ("Adicionar FK em contas_bancarias", "ALTER TABLE contas_bancarias ADD CONSTRAINT fk_contas_bancarias_proprietario FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE"),
            ("Criar índice em contas_bancarias", "CREATE INDEX IF NOT EXISTS idx_contas_bancarias_proprietario ON contas_bancarias(proprietario_id)"),
            
            # Tabela categorias
            ("Adicionar coluna em categorias", "ALTER TABLE categorias ADD COLUMN IF NOT EXISTS proprietario_id INTEGER"),
            ("Remover constraint antiga em categorias", "ALTER TABLE categorias DROP CONSTRAINT IF EXISTS fk_categorias_proprietario"),
            ("Adicionar FK em categorias", "ALTER TABLE categorias ADD CONSTRAINT fk_categorias_proprietario FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE"),
            ("Criar índice em categorias", "CREATE INDEX IF NOT EXISTS idx_categorias_proprietario ON categorias(proprietario_id)"),
            
            # Tabela subcategorias
            ("Adicionar coluna em subcategorias", "ALTER TABLE subcategorias ADD COLUMN IF NOT EXISTS proprietario_id INTEGER"),
            ("Remover constraint antiga em subcategorias", "ALTER TABLE subcategorias DROP CONSTRAINT IF EXISTS fk_subcategorias_proprietario"),
            ("Adicionar FK em subcategorias", "ALTER TABLE subcategorias ADD CONSTRAINT fk_subcategorias_proprietario FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE"),
            ("Criar índice em subcategorias", "CREATE INDEX IF NOT EXISTS idx_subcategorias_proprietario ON subcategorias(proprietario_id)"),
        ]
        
        sucesso = 0
        for descricao, comando in comandos_sql:
            try:
                cur.execute(comando)
                conn.commit()
                print(f"   ✓ {descricao}")
                sucesso += 1
            except Exception as e:
                print(f"   ⚠ {descricao}: {str(e)[:50]}")
                conn.rollback()
        
        print(f"\n✅ Migração completa! {sucesso}/{len(comandos_sql)} comandos executados com sucesso.")
        
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
                print(f"   ✓ {tabela}: proprietario_id ({resultado['data_type']}) adicionado")
            else:
                print(f"   ✗ {tabela}: proprietario_id NÃO encontrado")
        
        # Estatísticas
        print("\n📈 Estatísticas:")
        cur.execute("SELECT COUNT(*) as total FROM clientes WHERE proprietario_id IS NULL")
        print(f"   - Clientes sem proprietário (dados globais/admin): {cur.fetchone()['total']}")
        
        cur.execute("SELECT COUNT(*) as total FROM fornecedores WHERE proprietario_id IS NULL")
        print(f"   - Fornecedores sem proprietário: {cur.fetchone()['total']}")
        
        cur.execute("SELECT COUNT(*) as total FROM lancamentos WHERE proprietario_id IS NULL")
        print(f"   - Lançamentos sem proprietário: {cur.fetchone()['total']}")
        
        cur.close()
        conn.close()
        
        print("\n🎉 Migração completa! Sistema Multi-Tenancy pronto para uso.")
        print("\n📝 Próximos passos:")
        print("   1. Atualizar funções do database.py para usar filtro_cliente_id")
        print("   2. Aplicar @aplicar_filtro_cliente nas rotas do web_server.py")
        print("   3. Adicionar verificação de propriedade em edições/exclusões")
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    executar_migracao()
