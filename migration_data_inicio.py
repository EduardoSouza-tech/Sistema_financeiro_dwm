"""
Migração: Adicionar coluna data_inicio na tabela contas_bancarias
Data: 2026-01-19
Descrição: Adiciona campo obrigatório para data de início do saldo inicial da conta
"""

def executar_migracao(db_manager=None):
    """Executa a migração para adicionar data_inicio"""
    import psycopg2
    from datetime import date
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
            AND column_name = 'data_inicio'
        """)
        
        if cursor.fetchone():
            print("   ℹ️  Coluna data_inicio já existe - migração não necessária")
            cursor.close()
            if db_manager:
                from database_postgresql import return_to_pool
                return_to_pool(conn)
            else:
                conn.close()
            return True
        
        print("   🔄 Adicionando coluna data_inicio...")
        
        # Adicionar a coluna com valor padrão temporário
        cursor.execute("""
            ALTER TABLE contas_bancarias 
            ADD COLUMN data_inicio DATE DEFAULT CURRENT_DATE
        """)
        
        # Atualizar contas existentes para usar data_criacao como data_inicio
        cursor.execute("""
            UPDATE contas_bancarias 
            SET data_inicio = CAST(data_criacao AS DATE)
            WHERE data_inicio IS NULL
        """)
        
        # Tornar a coluna NOT NULL
        cursor.execute("""
            ALTER TABLE contas_bancarias 
            ALTER COLUMN data_inicio SET NOT NULL
        """)
        
        # Remover default (novos registros devem especificar a data)
        cursor.execute("""
            ALTER TABLE contas_bancarias 
            ALTER COLUMN data_inicio DROP DEFAULT
        """)
        
        conn.commit()
        
        # Verificar se foi adicionada
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'contas_bancarias' 
            AND column_name = 'data_inicio'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"   ✅ Coluna data_inicio adicionada com sucesso!")
            print(f"      - Tipo: {result[1]}")
            print(f"      - Nullable: {result[2]}")
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
    print("🔄 MIGRAÇÃO: Adicionar data_inicio em contas_bancarias")
    print("="*70)
    
    resultado = executar_migracao()
    
    if resultado:
        print("\n✅ Migração concluída com sucesso!")
    else:
        print("\n❌ Migração falhou!")
    
    print("="*70 + "\n")
