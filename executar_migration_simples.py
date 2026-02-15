import psycopg2
import sys
import os

# Obter DATABASE_URL do ambiente ou usar padrão
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway')

sql = """
DO $$
BEGIN
    -- Adicionar coluna numero_documento se não existir
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='lancamentos' AND column_name='numero_documento'
    ) THEN
        ALTER TABLE lancamentos ADD COLUMN numero_documento TEXT DEFAULT '';
        RAISE NOTICE 'Coluna numero_documento adicionada';
    END IF;
    
    -- Adicionar coluna associacao se não existir
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='lancamentos' AND column_name='associacao'
    ) THEN
        ALTER TABLE lancamentos ADD COLUMN associacao TEXT DEFAULT '';
        RAISE NOTICE 'Coluna associacao adicionada';
    END IF;
    
    -- Sincronizar valores (se um tiver valor e outro não, copiar)
    UPDATE lancamentos 
    SET associacao = numero_documento 
    WHERE (associacao = '' OR associacao IS NULL) 
    AND numero_documento IS NOT NULL AND numero_documento != '';
    
    UPDATE lancamentos 
    SET numero_documento = associacao 
    WHERE (numero_documento = '' OR numero_documento IS NULL) 
    AND associacao IS NOT NULL AND associacao != '';
    
    -- Criar índices
    CREATE INDEX IF NOT EXISTS idx_lancamentos_associacao 
    ON lancamentos(associacao) 
    WHERE associacao IS NOT NULL AND associacao != '';
    
    CREATE INDEX IF NOT EXISTS idx_lancamentos_numero_documento 
    ON lancamentos(numero_documento) 
    WHERE numero_documento IS NOT NULL AND numero_documento != '';
    
    RAISE NOTICE 'Migration concluída!';
END
$$;
"""

print("=" * 80)
print("🔧 MIGRATION: Adicionar coluna 'associacao'")
print("=" * 80)
print()

try:
    print("📡 Conectando ao banco de dados...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("⚙️  Executando SQL...")
    cursor.execute(sql)
    
    # Mostrar avisos/notices do PostgreSQL
    if conn.notices:
        for notice in conn.notices:
            print(f"   {notice.strip()}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print()
    print("=" * 80)
    print("✅ MIGRATION EXECUTADA COM SUCESSO!")
    print("=" * 80)
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
