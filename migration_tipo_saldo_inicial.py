"""
Migração: Adicionar coluna tipo_saldo_inicial na tabela contas_bancarias
Data: 2024
Descrição: Adiciona campo para indicar se o saldo inicial é credor (positivo) ou devedor (negativo)
"""

def executar_migracao(db_manager=None):
    """Executa a migração para adicionar tipo_saldo_inicial"""
    import psycopg2
    from database_postgresql import get_db_connection
    
    try:
        # Obter conexão
        if db_manager:
            conn = db_manager.get_connection()
        else:
            conn = get_db_connection()
        
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'contas_bancarias' 
            AND column_name = 'tipo_saldo_inicial'
        """)
        
        if cursor.fetchone():
            print("   ℹ️  Coluna tipo_saldo_inicial já existe - migração não necessária")
            cursor.close()
            if db_manager:
                from database_postgresql import return_to_pool
                return_to_pool(conn)
            else:
                conn.close()
            return True
        
        print("   🔄 Adicionando coluna tipo_saldo_inicial...")
        
        # Adicionar a coluna
        cursor.execute("""
            ALTER TABLE contas_bancarias 
            ADD COLUMN tipo_saldo_inicial VARCHAR(10) DEFAULT 'credor' 
            CHECK (tipo_saldo_inicial IN ('credor', 'devedor'))
        """)
        
        conn.commit()
        
        # Verificar se foi adicionada
        cursor.execute("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'contas_bancarias' 
            AND column_name = 'tipo_saldo_inicial'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"   ✅ Coluna tipo_saldo_inicial adicionada com sucesso!")
            print(f"      - Tipo: {result[1]}")
            print(f"      - Default: {result[2]}")
        else:
            print("   ❌ Erro: Coluna não foi adicionada")
            cursor.close()
            if db_manager:
                from database_postgresql import return_to_pool
                return_to_pool(conn)
            else:
                conn.close()
            return False
        
        cursor.close()
        if db_manager:
            from database_postgresql import return_to_pool
            return_to_pool(conn)
        else:
            conn.close()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao executar migração: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Executar migração standalone
    print("\n" + "="*70)
    print("🔄 MIGRAÇÃO: Adicionar tipo_saldo_inicial")
    print("="*70)
    
    resultado = executar_migracao()
    
    if resultado:
        print("\n✅ Migração concluída com sucesso!")
    else:
        print("\n❌ Migração falhou!")
    
    print("="*70 + "\n")
