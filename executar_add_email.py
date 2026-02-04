#!/usr/bin/env python3
"""
Script para adicionar campo email e colunas de horário
"""
import psycopg2
import sys

# Configuração do banco (Railway)
DB_CONFIG = {
    'host': 'centerbeam.proxy.rlwy.net',
    'port': 12659,
    'database': 'railway',
    'user': 'postgres',
    'password': 'FElbHLOzxDdRvmOCMWewNYBxhxjNNvDC'
}

def executar_migration():
    try:
        print("🔄 Conectando ao banco de dados...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("📝 Executando migration...")
        
        # Ler e executar o SQL
        with open('add_email_to_funcionarios.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
        
        cursor.execute(sql)
        conn.commit()
        
        print("✅ Migration executada com sucesso!")
        print("\n📊 Verificando estrutura:")
        
        # Verificar funcionarios
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'funcionarios' 
            AND column_name IN ('email')
            ORDER BY ordinal_position
        """)
        print("\n📋 Tabela funcionarios:")
        for row in cursor.fetchall():
            print(f"   - {row[0]}: {row[1]}")
        
        # Verificar evento_funcionarios
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'evento_funcionarios' 
            AND column_name IN ('hora_inicio', 'hora_fim')
            ORDER BY ordinal_position
        """)
        print("\n📋 Tabela evento_funcionarios:")
        for row in cursor.fetchall():
            print(f"   - {row[0]}: {row[1]}")
        
        cursor.close()
        conn.close()
        
        print("\n✨ Concluído!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = executar_migration()
    sys.exit(0 if success else 1)
