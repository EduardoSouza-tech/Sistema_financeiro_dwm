"""
Migration: Criar tabelas do módulo Contabilidade - Plano de Contas
"""
import psycopg2
import os
import sys

# Carregar variáveis de ambiente do .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def run_migration():
    """Cria as tabelas plano_contas_versao e plano_contas no PostgreSQL"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL não configurada!")
        sys.exit(1)

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        # =====================================================================
        # Tabela: plano_contas_versao (versionamento por exercício fiscal)
        # =====================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plano_contas_versao (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER NOT NULL,
                nome_versao VARCHAR(100) NOT NULL,
                exercicio_fiscal INTEGER NOT NULL,
                data_inicio DATE,
                data_fim DATE,
                is_ativa BOOLEAN DEFAULT FALSE,
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(empresa_id, nome_versao)
            );
        """)
        print("✅ Tabela plano_contas_versao criada/verificada")

        # =====================================================================
        # Tabela: plano_contas (contas do plano)
        # =====================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plano_contas (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER NOT NULL,
                versao_id INTEGER REFERENCES plano_contas_versao(id) ON DELETE CASCADE,
                
                -- Código hierárquico (ex: 1.1.2.03.001)
                codigo VARCHAR(30) NOT NULL,
                descricao VARCHAR(200) NOT NULL,
                
                -- Hierarquia
                parent_id INTEGER REFERENCES plano_contas(id) ON DELETE SET NULL,
                nivel INTEGER NOT NULL DEFAULT 1,
                ordem INTEGER DEFAULT 0,
                
                -- Classificação
                tipo_conta VARCHAR(15) NOT NULL DEFAULT 'analitica'
                    CHECK (tipo_conta IN ('sintetica', 'analitica')),
                classificacao VARCHAR(25) NOT NULL
                    CHECK (classificacao IN (
                        'ativo', 'passivo', 'patrimonio_liquido',
                        'receita', 'despesa', 'compensacao'
                    )),
                natureza VARCHAR(10) NOT NULL DEFAULT 'devedora'
                    CHECK (natureza IN ('devedora', 'credora')),
                
                -- Controle
                is_bloqueada BOOLEAN DEFAULT FALSE,
                requer_centro_custo BOOLEAN DEFAULT FALSE,
                permite_lancamento BOOLEAN DEFAULT TRUE,
                
                -- Soft delete
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- Unicidade: código único por empresa + versão
                UNIQUE(empresa_id, versao_id, codigo)
            );
        """)
        print("✅ Tabela plano_contas criada/verificada")

        # =====================================================================
        # Índices para performance
        # =====================================================================
        indices = [
            ("idx_plano_contas_empresa", "plano_contas", "empresa_id"),
            ("idx_plano_contas_versao", "plano_contas", "versao_id"),
            ("idx_plano_contas_parent", "plano_contas", "parent_id"),
            ("idx_plano_contas_codigo", "plano_contas", "codigo"),
            ("idx_plano_contas_classificacao", "plano_contas", "classificacao"),
            ("idx_plano_contas_deleted", "plano_contas", "deleted_at"),
            ("idx_plano_contas_versao_empresa", "plano_contas_versao", "empresa_id"),
        ]
        
        for idx_name, table, column in indices:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({column});")
            except Exception as e:
                print(f"⚠️ Índice {idx_name}: {e}")

        print("✅ Índices criados/verificados")

        # =====================================================================
        # Habilitar RLS (Row Level Security)
        # =====================================================================
        for table in ['plano_contas', 'plano_contas_versao']:
            try:
                cursor.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
                cursor.execute(f"""
                    DO $$ BEGIN
                        CREATE POLICY {table}_isolation ON {table}
                            USING (empresa_id = current_setting('app.current_empresa_id', true)::INTEGER);
                    EXCEPTION WHEN duplicate_object THEN NULL;
                    END $$;
                """)
            except Exception as e:
                print(f"⚠️ RLS {table}: {e}")

        print("✅ Row Level Security configurado")
        print("\n🎉 Migration do Plano de Contas concluída com sucesso!")

    except Exception as e:
        print(f"❌ Erro na migration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    run_migration()
