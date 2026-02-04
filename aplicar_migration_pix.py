#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplicar migration apenas - remover NOT NULL de tipo_chave_pix
"""

import psycopg2

# Configurações do banco Railway
DB_CONFIG = {
    'host': 'centerbeam.proxy.rlwy.net',
    'port': 12659,
    'database': 'railway',
    'user': 'postgres',
    'password': 'JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT'
}

def aplicar_migration():
    """Aplicar migration para remover NOT NULL de tipo_chave_pix"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔧 Removendo constraint NOT NULL de tipo_chave_pix...")
        
        cursor.execute("""
            ALTER TABLE funcionarios 
            ALTER COLUMN tipo_chave_pix DROP NOT NULL;
        """)
        
        conn.commit()
        print("✅ Migration aplicada com sucesso!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    aplicar_migration()
