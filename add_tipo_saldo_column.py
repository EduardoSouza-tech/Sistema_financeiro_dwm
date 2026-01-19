import psycopg2

# Conectar ao banco
conn = psycopg2.connect(
    dbname='sistema_financeiro',
    user='postgres',
    password='123',
    host='localhost',
    port='5432'
)

try:
    cur = conn.cursor()
    
    # Adicionar a coluna tipo_saldo_inicial
    cur.execute("""
        ALTER TABLE contas_bancarias 
        ADD COLUMN IF NOT EXISTS tipo_saldo_inicial VARCHAR(10) DEFAULT 'credor' 
        CHECK (tipo_saldo_inicial IN ('credor', 'devedor'))
    """)
    
    conn.commit()
    print("✅ Coluna 'tipo_saldo_inicial' adicionada com sucesso!")
    
    # Verificar se foi adicionada
    cur.execute("""
        SELECT column_name, data_type, column_default 
        FROM information_schema.columns 
        WHERE table_name = 'contas_bancarias' AND column_name = 'tipo_saldo_inicial'
    """)
    
    result = cur.fetchone()
    if result:
        print(f"✅ Coluna verificada: {result}")
    else:
        print("❌ Coluna não encontrada")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
