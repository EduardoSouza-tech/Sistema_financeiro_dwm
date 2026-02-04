"""
Script para adicionar colunas hora_inicio e hora_fim na tabela evento_funcionarios
Executa diretamente no banco PostgreSQL do Railway
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Configurações do PostgreSQL (Railway)
POSTGRESQL_CONFIG = {
    'host': os.getenv('PGHOST', 'centerbeam.proxy.rlwy.net'),
    'port': int(os.getenv('PGPORT', '12659')),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', 'JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT'),
    'database': os.getenv('PGDATABASE', 'railway')
}

def executar_migration():
    """Adiciona colunas hora_inicio e hora_fim"""
    try:
        print("="*80)
        print("🔧 CONECTANDO AO POSTGRESQL DO RAILWAY")
        print("="*80)
        print(f"Host: {POSTGRESQL_CONFIG['host']}")
        print(f"Database: {POSTGRESQL_CONFIG['database']}")
        print(f"User: {POSTGRESQL_CONFIG['user']}")
        
        # Conectar ao banco
        conn = psycopg2.connect(**POSTGRESQL_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✅ Conectado com sucesso!")
        print("")
        
        # Verificar se as colunas já existem
        print("🔍 Verificando colunas existentes...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'evento_funcionarios' 
            AND column_name IN ('hora_inicio', 'hora_fim')
        """)
        colunas_existentes = [row['column_name'] for row in cursor.fetchall()]
        print(f"   Colunas encontradas: {colunas_existentes}")
        print("")
        
        # Adicionar hora_inicio
        if 'hora_inicio' not in colunas_existentes:
            print("➕ Adicionando coluna hora_inicio...")
            cursor.execute("""
                ALTER TABLE evento_funcionarios 
                ADD COLUMN hora_inicio TIME
            """)
            conn.commit()
            print("   ✅ Coluna hora_inicio adicionada!")
        else:
            print("   ⏭️  Coluna hora_inicio já existe")
        
        # Adicionar hora_fim
        if 'hora_fim' not in colunas_existentes:
            print("➕ Adicionando coluna hora_fim...")
            cursor.execute("""
                ALTER TABLE evento_funcionarios 
                ADD COLUMN hora_fim TIME
            """)
            conn.commit()
            print("   ✅ Coluna hora_fim adicionada!")
        else:
            print("   ⏭️  Coluna hora_fim já existe")
        
        print("")
        print("🔍 Verificando resultado final...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'evento_funcionarios' 
            AND column_name IN ('hora_inicio', 'hora_fim')
            ORDER BY column_name
        """)
        
        resultado = cursor.fetchall()
        if resultado:
            print("   ✅ SUCESSO! Colunas criadas:")
            for row in resultado:
                print(f"      - {row['column_name']} ({row['data_type']}) - Nullable: {row['is_nullable']}")
        else:
            print("   ❌ ERRO: Nenhuma coluna encontrada")
        
        cursor.close()
        conn.close()
        
        print("")
        print("="*80)
        print("✅ MIGRATION CONCLUÍDA!")
        print("="*80)
        print("")
        print("Agora você pode:")
        print("1. Recarregar a página do sistema")
        print("2. Abrir 'Alocar Equipe' em um evento")
        print("3. Ver a lista de equipe alocada funcionando")
        print("4. Adicionar funcionários com horários")
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    executar_migration()
