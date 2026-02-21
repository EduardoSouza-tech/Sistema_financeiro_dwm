"""
Migration: Criar tabelas funcoes_responsaveis, custos_operacionais
              e corrigir schema da tabela tags (adicionar empresa_id, ativa, icone)

Executar UMA VEZ no banco Railway.
"""

import os
import sys
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get('DATABASE_URL', 
    'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

def run():
    print("🔌 Conectando ao banco...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    print("✅ Conectado!")

    # ─────────────────────────────────────────────
    # 1. Corrigir tabela tags (schema antigo sem empresa_id / ativa / icone)
    # ─────────────────────────────────────────────
    print("\n🔧 Corrigindo tabela tags...")

    cursor.execute("""
        DO $$
        BEGIN
            -- empresa_id
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='tags' AND column_name='empresa_id'
            ) THEN
                ALTER TABLE tags ADD COLUMN empresa_id INTEGER;
                RAISE NOTICE 'tags.empresa_id adicionada';
            END IF;

            -- ativa
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='tags' AND column_name='ativa'
            ) THEN
                ALTER TABLE tags ADD COLUMN ativa BOOLEAN DEFAULT TRUE;
                RAISE NOTICE 'tags.ativa adicionada';
            END IF;

            -- icone
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='tags' AND column_name='icone'
            ) THEN
                ALTER TABLE tags ADD COLUMN icone VARCHAR(50) DEFAULT 'tag';
                RAISE NOTICE 'tags.icone adicionada';
            END IF;

            -- updated_at (pode já existir no schema novo)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='tags' AND column_name='updated_at'
            ) THEN
                ALTER TABLE tags ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                RAISE NOTICE 'tags.updated_at adicionada';
            END IF;
        END $$;
    """)
    print("   ✅ Colunas de tags verificadas/adicionadas")

    # ─────────────────────────────────────────────
    # 2. Criar tabela funcoes_responsaveis
    # ─────────────────────────────────────────────
    print("\n🔧 Criando tabela funcoes_responsaveis...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS funcoes_responsaveis (
            id          SERIAL PRIMARY KEY,
            nome        VARCHAR(100) NOT NULL,
            descricao   TEXT         DEFAULT '',
            ativa       BOOLEAN      DEFAULT TRUE,
            empresa_id  INTEGER      NOT NULL,
            created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✅ funcoes_responsaveis OK")

    # ─────────────────────────────────────────────
    # 3. Criar tabela custos_operacionais
    # ─────────────────────────────────────────────
    print("\n🔧 Criando tabela custos_operacionais...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custos_operacionais (
            id           SERIAL PRIMARY KEY,
            nome         VARCHAR(255) NOT NULL,
            descricao    TEXT         DEFAULT '',
            categoria    VARCHAR(100) NOT NULL,
            valor_padrao DECIMAL(15,2) DEFAULT 0.00,
            unidade      VARCHAR(50)  DEFAULT 'unidade',
            ativo        BOOLEAN      DEFAULT TRUE,
            empresa_id   INTEGER      NOT NULL,
            created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
            updated_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✅ custos_operacionais OK")

    # ─────────────────────────────────────────────
    # Verificação
    # ─────────────────────────────────────────────
    print("\n📋 Verificando tabelas criadas:")
    for tabela in ('tags', 'funcoes_responsaveis', 'custos_operacionais'):
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (tabela,))
        cols = cursor.fetchall()
        print(f"\n  📌 {tabela} ({len(cols)} colunas):")
        for c in cols:
            print(f"     - {c['column_name']}: {c['data_type']}")

    cursor.close()
    conn.close()
    print("\n🎉 Migration concluída com sucesso!")

if __name__ == '__main__':
    run()
