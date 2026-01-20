"""
Migration: Corrigir tabela kits
Adiciona colunas 'descricao' e 'empresa_id' que são usadas no código mas não existem no schema
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import database_postgresql as db

def migrate_kits_table():
    """Adiciona colunas faltantes na tabela kits"""
    
    print("\n" + "="*80)
    print("🔧 MIGRATION: Corrigir tabela KITS")
    print("="*80 + "\n")
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 1. Verificar se coluna 'descricao' existe
        print("📋 Verificando coluna 'descricao'...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='kits' AND column_name='descricao'
            ) as existe
        """)
        result = cursor.fetchone()
        descricao_existe = result[0] if isinstance(result, tuple) else result['existe']
        
        if not descricao_existe:
            print("   ➕ Adicionando coluna 'descricao'...")
            cursor.execute("""
                ALTER TABLE kits ADD COLUMN descricao TEXT
            """)
            print("   ✅ Coluna 'descricao' adicionada!")
        else:
            print("   ✅ Coluna 'descricao' já existe")
        
        # 2. Verificar se coluna 'empresa_id' existe
        print("\n📋 Verificando coluna 'empresa_id'...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='kits' AND column_name='empresa_id'
            ) as existe
        """)
        result = cursor.fetchone()
        empresa_id_existe = result[0] if isinstance(result, tuple) else result['existe']
        
        if not empresa_id_existe:
            print("   ➕ Adicionando coluna 'empresa_id'...")
            cursor.execute("""
                ALTER TABLE kits ADD COLUMN empresa_id INTEGER DEFAULT 1
            """)
            print("   ✅ Coluna 'empresa_id' adicionada!")
        else:
            print("   ✅ Coluna 'empresa_id' já existe")
        
        # 3. Migrar dados de 'observacoes' para 'descricao' se necessário
        print("\n📦 Verificando se precisa migrar dados...")
        cursor.execute("""
            SELECT COUNT(*) FROM kits 
            WHERE observacoes IS NOT NULL 
            AND (descricao IS NULL OR descricao = '')
        """)
        result = cursor.fetchone()
        rows_to_migrate = result[0] if isinstance(result, tuple) else result['count']
        
        if rows_to_migrate > 0:
            print(f"   🔄 Migrando {rows_to_migrate} registros de 'observacoes' para 'descricao'...")
            cursor.execute("""
                UPDATE kits 
                SET descricao = observacoes 
                WHERE observacoes IS NOT NULL 
                AND (descricao IS NULL OR descricao = '')
            """)
            print(f"   ✅ {rows_to_migrate} registros migrados!")
        else:
            print("   ✅ Nenhum dado para migrar")
        
        # 4. Verificar estrutura final
        print("\n📊 Verificando estrutura final da tabela...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'kits'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("\n   Colunas da tabela 'kits':")
        for col in columns:
            if isinstance(col, dict):
                print(f"      - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
            else:
                print(f"      - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # Commit das mudanças
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO na migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_kits_table()
    sys.exit(0 if success else 1)
