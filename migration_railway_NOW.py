"""
Executar Migration DRE Mapeamento DIRETAMENTE no Railway
Conexão direta sem depender de DatabaseManager
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# URL de conexão do Railway (hardcoded para garantir funcionamento)
DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("🚀 APLICANDO MIGRATION: DRE - Mapeamento de Subcategorias")
print("=" * 80)
print()

try:
    # Conectar ao Railway
    print("📡 Conectando ao Railway PostgreSQL...")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("   ✅ Conectado com sucesso!")
    print()
    
    # Verificar se tabela já existe
    print("🔍 Verificando se tabela já existe...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_name = 'dre_mapeamento_subcategoria'
        );
    """)
    tabela_existe = cursor.fetchone()['exists']
    
    if tabela_existe:
        print("   ⚠️  Tabela dre_mapeamento_subcategoria JÁ EXISTE!")
        print()
        
        # Mostrar informações da tabela
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM dre_mapeamento_subcategoria;
        """)
        total = cursor.fetchone()['total']
        print(f"   📊 Registros existentes: {total}")
        print()
        print("✅ Migration já foi aplicada anteriormente!")
        print("   A tabela está pronta para uso.")
        cursor.close()
        conn.close()
        exit(0)
    
    print("   ✅ Tabela não existe. Procedendo com criação...")
    print()
    print("⚙️  Criando tabela dre_mapeamento_subcategoria...")
    
    # Criar tabela
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dre_mapeamento_subcategoria (
            id SERIAL PRIMARY KEY,
            empresa_id INTEGER NOT NULL,
            subcategoria_id INTEGER NOT NULL,
            plano_contas_id INTEGER NOT NULL,
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            -- Foreign Keys
            CONSTRAINT fk_dre_map_empresa 
                FOREIGN KEY (empresa_id) 
                REFERENCES empresas(id) 
                ON DELETE CASCADE,
            CONSTRAINT fk_dre_map_subcategoria 
                FOREIGN KEY (subcategoria_id) 
                REFERENCES subcategorias(id) 
                ON DELETE CASCADE,
            CONSTRAINT fk_dre_map_plano_contas 
                FOREIGN KEY (plano_contas_id) 
                REFERENCES plano_contas(id) 
                ON DELETE CASCADE,
            
            -- Constraint: Impedir duplicação de subcategoria para a mesma empresa
            CONSTRAINT uk_dre_map_empresa_sub 
                UNIQUE (empresa_id, subcategoria_id)
        );
    """)
    conn.commit()
    print("   ✅ Tabela criada!")
    
    # Criar índices
    print()
    print("📊 Criando índices para performance...")
    
    indices = [
        ("idx_dre_map_empresa", "empresa_id"),
        ("idx_dre_map_subcategoria", "subcategoria_id"),
        ("idx_dre_map_plano_contas", "plano_contas_id"),
        ("idx_dre_map_ativo", "ativo")
    ]
    
    for idx_name, coluna in indices:
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {idx_name} 
            ON dre_mapeamento_subcategoria({coluna});
        """)
        print(f"   ✅ Índice {idx_name} criado")
    
    conn.commit()
    
    # Criar trigger para updated_at
    print()
    print("🔧 Criando trigger para updated_at...")
    
    cursor.execute("""
        CREATE OR REPLACE FUNCTION update_dre_mapeamento_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    cursor.execute("""
        DROP TRIGGER IF EXISTS trg_dre_mapeamento_updated_at 
        ON dre_mapeamento_subcategoria;
    """)
    
    cursor.execute("""
        CREATE TRIGGER trg_dre_mapeamento_updated_at
        BEFORE UPDATE ON dre_mapeamento_subcategoria
        FOR EACH ROW
        EXECUTE FUNCTION update_dre_mapeamento_updated_at();
    """)
    
    conn.commit()
    print("   ✅ Trigger criado!")
    
    # Adicionar comentários
    print()
    print("📝 Adicionando comentários...")
    
    cursor.execute("""
        COMMENT ON TABLE dre_mapeamento_subcategoria IS 
        'Mapeamento entre subcategorias de lançamentos e contas do plano de contas do DRE';
    """)
    
    cursor.execute("""
        COMMENT ON COLUMN dre_mapeamento_subcategoria.empresa_id IS 
        'Empresa dona do mapeamento (multi-tenant)';
    """)
    
    cursor.execute("""
        COMMENT ON COLUMN dre_mapeamento_subcategoria.subcategoria_id IS 
        'Subcategoria de lançamento financeiro';
    """)
    
    cursor.execute("""
        COMMENT ON COLUMN dre_mapeamento_subcategoria.plano_contas_id IS 
        'Conta do plano de contas do DRE (código 4.x, 5.x, 6.x, 7.x)';
    """)
    
    conn.commit()
    print("   ✅ Comentários adicionados!")
    
    # Verificar resultado final
    print()
    print("🔍 Verificando estrutura criada...")
    print()
    
    # Colunas
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'dre_mapeamento_subcategoria'
        ORDER BY ordinal_position;
    """)
    
    colunas = cursor.fetchall()
    print(f"   📋 Colunas ({len(colunas)}):")
    for col in colunas:
        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
        print(f"      • {col['column_name']:<20} {col['data_type']:<20} {nullable}{default}")
    
    # Índices
    print()
    cursor.execute("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'dre_mapeamento_subcategoria'
        ORDER BY indexname;
    """)
    
    indices_criados = cursor.fetchall()
    print(f"   📊 Índices ({len(indices_criados)}):")
    for idx in indices_criados:
        print(f"      • {idx['indexname']}")
    
    # Constraints
    print()
    cursor.execute("""
        SELECT constraint_name, constraint_type
        FROM information_schema.table_constraints
        WHERE table_name = 'dre_mapeamento_subcategoria'
        ORDER BY constraint_type, constraint_name;
    """)
    
    constraints = cursor.fetchall()
    print(f"   🔒 Constraints ({len(constraints)}):")
    tipo_map = {
        'PRIMARY KEY': 'PK',
        'FOREIGN KEY': 'FK',
        'UNIQUE': 'UK',
        'CHECK': 'CK'
    }
    for const in constraints:
        tipo = tipo_map.get(const['constraint_type'], const['constraint_type'])
        print(f"      • {const['constraint_name']:<45} ({tipo})")
    
    # Triggers
    print()
    cursor.execute("""
        SELECT trigger_name
        FROM information_schema.triggers
        WHERE event_object_table = 'dre_mapeamento_subcategoria';
    """)
    
    triggers = cursor.fetchall()
    print(f"   ⚡ Triggers ({len(triggers)}):")
    for trg in triggers:
        print(f"      • {trg['trigger_name']}")
    
    print()
    print("=" * 80)
    print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
    print("=" * 80)
    print()
    print("📌 Próximos passos:")
    print("   1. Aguardar deploy do Railway (~2-3 minutos)")
    print("   2. Acessar sistema em produção")
    print("   3. Ir em: Relatórios Contábeis > DRE")
    print("   4. Clicar em: ⚙️ Configurar Mapeamento")
    print("   5. Testar criação de mapeamentos")
    print()
    print("📖 Documentação completa: DOCS_CONFIGURACAO_DRE_MAPEAMENTO.md")
    print()
    
    cursor.close()
    conn.close()
    
except psycopg2.Error as e:
    print()
    print("=" * 80)
    print("❌ ERRO DE BANCO DE DADOS")
    print("=" * 80)
    print(f"Erro: {e}")
    print()
    print("💡 Possíveis causas:")
    print("   - Conexão com Railway falhou")
    print("   - Credenciais incorretas")
    print("   - Tabelas referenciadas (empresas, subcategorias, plano_contas) não existem")
    print()
    exit(1)
    
except Exception as e:
    print()
    print("=" * 80)
    print("❌ ERRO GERAL")
    print("=" * 80)
    print(f"Erro: {e}")
    print()
    import traceback
    traceback.print_exc()
    exit(1)
