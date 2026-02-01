#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar migration de evento_funcionarios
Cria tabelas para sistema de alocação de equipe em eventos
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import DatabaseManager

def main():
    print("="*80)
    print("🚀 MIGRATION: Sistema de Alocação de Equipe em Eventos")
    print("="*80)
    
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Ler arquivo SQL
        sql_file = os.path.join(os.path.dirname(__file__), 'migration_evento_funcionarios.sql')
        print(f"\n📂 Lendo arquivo: {sql_file}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("\n📝 Executando migration...")
        
        # Executar script
        cursor.execute(sql_script)
        conn.commit()
        
        print("\n✅ Migration executada com sucesso!")
        
        # Verificar tabelas criadas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('funcoes_evento', 'evento_funcionarios')
            ORDER BY table_name
        """)
        
        tabelas = cursor.fetchall()
        print(f"\n📊 Tabelas criadas ({len(tabelas)}):")
        for tabela in tabelas:
            print(f"   ✓ {tabela['table_name']}")
        
        # Verificar funções inseridas
        cursor.execute("SELECT COUNT(*) as total FROM funcoes_evento")
        total_funcoes = cursor.fetchone()['total']
        print(f"\n👷 Funções padrão inseridas: {total_funcoes}")
        
        if total_funcoes > 0:
            cursor.execute("SELECT nome FROM funcoes_evento ORDER BY nome LIMIT 5")
            funcoes = cursor.fetchall()
            print("\n   Exemplos:")
            for func in funcoes:
                print(f"   - {func['nome']}")
        
        print("\n" + "="*80)
        print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERRO ao executar migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)
    
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
