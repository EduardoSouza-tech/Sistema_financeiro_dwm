"""
Migration: Corrigir tipo da coluna subcategorias
Altera subcategorias de TEXT para VARCHAR(255) na tabela categorias
Data: 26/01/2026
"""

import os
import sys
from database_postgresql import DatabaseManager

def fix_subcategorias_column():
    """
    Altera o tipo da coluna subcategorias de TEXT para VARCHAR(255)
    para manter consistência com outras colunas de texto da tabela
    """
    print("\n" + "="*80)
    print("MIGRATION: Corrigir tipo da coluna subcategorias")
    print("="*80 + "\n")
    
    db = DatabaseManager()
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("📊 Verificando tipo atual da coluna subcategorias...")
        cursor.execute("""
            SELECT data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'categorias'
            AND column_name = 'subcategorias'
        """)
        
        result = cursor.fetchone()
        if result:
            tipo_atual = result[0]
            tamanho_atual = result[1]
            print(f"   Tipo atual: {tipo_atual}" + (f" ({tamanho_atual})" if tamanho_atual else ""))
        else:
            print("   ⚠️  Coluna subcategorias não encontrada!")
            return
        
        # Verificar se já está correto
        if tipo_atual == 'character varying':
            print("   ✅ Coluna já está com o tipo correto (character varying)")
            return
        
        print("\n🔧 Alterando tipo da coluna...")
        cursor.execute("""
            ALTER TABLE categorias
            ALTER COLUMN subcategorias TYPE VARCHAR(255)
            USING subcategorias::VARCHAR(255)
        """)
        
        conn.commit()
        print("   ✅ Coluna subcategorias alterada com sucesso!")
        
        # Verificar resultado
        print("\n🔍 Verificando alteração...")
        cursor.execute("""
            SELECT data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'categorias'
            AND column_name = 'subcategorias'
        """)
        
        result = cursor.fetchone()
        tipo_novo = result[0]
        tamanho_novo = result[1]
        print(f"   Tipo após migration: {tipo_novo} ({tamanho_novo})")
        
        print("\n" + "="*80)
        print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
        print("="*80 + "\n")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ ERRO na migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    fix_subcategorias_column()
