"""
Script de Migração: Criar tabela conciliacoes no banco de produção
Executa-se uma única vez para criar a estrutura necessária
"""
import os
import sys
import psycopg2
from psycopg2 import sql

def get_database_url():
    """Obtem URL do banco do Railway"""
    # FORÇAR URL correta do Railway (25/02/2026)
    db_url = "postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway"
    
    return db_url

def criar_tabela_conciliacoes():
    """Cria a tabela conciliacoes no banco de dados"""
    
    db_url = get_database_url()
    
    print("=" * 80)
    print("🚀 MIGRAÇÃO: Criar tabela conciliacoes")
    print("=" * 80)
    print(f"📍 Conectando ao banco: {db_url.split('@')[1] if '@' in db_url else 'local'}")
    
    try:
        # Conectar ao banco
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("\n✅ Conexão estabelecida com sucesso!")
        
        # Verificar se a tabela já existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'conciliacoes'
            )
        """)
        
        tabela_existe = cursor.fetchone()[0]
        
        if tabela_existe:
            print("\n⚠️  Tabela conciliacoes já existe!")
            print("Verificando estrutura...")
            
            # Verificar colunas existentes
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'conciliacoes'
                ORDER BY ordinal_position
            """)
            
            colunas = cursor.fetchall()
            print("\n📋 Colunas existentes:")
            for col in colunas:
                print(f"   - {col[0]}: {col[1]}")
            
            cursor.close()
            conn.close()
            return
        
        print("\n🔨 Criando tabela conciliacoes...")
        
        # Criar a tabela
        cursor.execute("""
            CREATE TABLE conciliacoes (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER NOT NULL,
                transacao_extrato_id INTEGER NOT NULL,
                lancamento_id INTEGER NOT NULL,
                data_conciliacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_id INTEGER,
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                CONSTRAINT fk_conciliacoes_empresa 
                    FOREIGN KEY (empresa_id) 
                    REFERENCES empresas(id) ON DELETE CASCADE,
                    
                CONSTRAINT fk_conciliacoes_transacao 
                    FOREIGN KEY (transacao_extrato_id) 
                    REFERENCES transacoes_extrato(id) ON DELETE CASCADE,
                    
                CONSTRAINT fk_conciliacoes_lancamento 
                    FOREIGN KEY (lancamento_id) 
                    REFERENCES lancamentos(id) ON DELETE CASCADE,
                
                -- Garantir uma conciliação única por transação
                CONSTRAINT unique_transacao_conciliacao 
                    UNIQUE (transacao_extrato_id)
            )
        """)
        
        print("✅ Tabela criada com sucesso!")
        
        # Criar índices para performance
        print("\n🔨 Criando índices...")
        
        cursor.execute("""
            CREATE INDEX idx_conciliacoes_empresa 
            ON conciliacoes(empresa_id)
        """)
        print("   ✅ idx_conciliacoes_empresa")
        
        cursor.execute("""
            CREATE INDEX idx_conciliacoes_transacao 
            ON conciliacoes(transacao_extrato_id)
        """)
        print("   ✅ idx_conciliacoes_transacao")
        
        cursor.execute("""
            CREATE INDEX idx_conciliacoes_lancamento 
            ON conciliacoes(lancamento_id)
        """)
        print("   ✅ idx_conciliacoes_lancamento")
        
        cursor.execute("""
            CREATE INDEX idx_conciliacoes_data 
            ON conciliacoes(data_conciliacao)
        """)
        print("   ✅ idx_conciliacoes_data")
        
        # Habilitar Row Level Security (RLS)
        print("\n🔒 Habilitando Row Level Security...")
        
        cursor.execute("""
            ALTER TABLE conciliacoes ENABLE ROW LEVEL SECURITY
        """)
        print("   ✅ RLS habilitado")
        
        cursor.execute("""
            CREATE POLICY conciliacoes_empresa_isolation 
            ON conciliacoes
            FOR ALL
            USING (empresa_id = current_setting('app.empresa_id', TRUE)::INTEGER)
        """)
        print("   ✅ Policy criada: conciliacoes_empresa_isolation")
        
        # Commit
        conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        print("\n📊 Estrutura criada:")
        print("   - Tabela: conciliacoes")
        print("   - Constraints: 3 foreign keys + 1 unique")
        print("   - Índices: 4 índices de performance")
        print("   - Segurança: RLS habilitado com policy")
        
        # Verificar contagem atual
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conciliacoes")
        total = cursor.fetchone()[0]
        print(f"\n📈 Total de registros: {total}")
        
        cursor.close()
        conn.close()
        
        print("\n🎯 Próximos passos:")
        print("   1. Atualizar extrato_functions.py para usar a nova tabela")
        print("   2. Migrar dados antigos (se houver campo lancamento_id em transacoes_extrato)")
        print("   3. Testar conciliação na interface web")
        
    except Exception as e:
        print(f"\n❌ ERRO durante migração: {e}")
        import traceback
        print("\n" + traceback.format_exc())
        
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        
        sys.exit(1)

if __name__ == '__main__':
    criar_tabela_conciliacoes()
