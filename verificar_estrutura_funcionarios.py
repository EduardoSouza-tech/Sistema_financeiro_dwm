#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificador de estrutura da tabela funcionarios
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

def verificar_estrutura():
    """Verifica a estrutura da tabela funcionarios"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("📋 ESTRUTURA DA TABELA FUNCIONARIOS\n")
        
        cursor.execute("""
            SELECT 
                column_name, 
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'funcionarios'
            ORDER BY ordinal_position
        """)
        
        colunas = cursor.fetchall()
        
        print(f"{'COLUNA':<30} {'TIPO':<20} {'NULL?':<8} {'DEFAULT':<20}")
        print("=" * 90)
        
        for col in colunas:
            nome, tipo, tam, nullable, default = col
            if tam:
                tipo_completo = f"{tipo}({tam})"
            else:
                tipo_completo = tipo
            default_str = str(default)[:20] if default else '-'
            print(f"{nome:<30} {tipo_completo:<20} {nullable:<8} {default_str:<20}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    verificar_estrutura()
