#!/usr/bin/env python3
"""
Script para aplicar migração da tabela evento_fornecedores
"""

import sys
import os

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import get_db_connection

def aplicar_migracao():
    """Aplica migração da tabela evento_fornecedores"""
    print("🔧 Aplicando migração: evento_fornecedores...")
    
    # Ler arquivo SQL
    sql_file = os.path.join(os.path.dirname(__file__), 'migration_evento_fornecedores.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ Arquivo {sql_file} não encontrado!")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    try:
        # Executar migração (usar allow_global=True pois é uma tabela do sistema)
        with get_db_connection(allow_global=True) as conn:
            cursor = conn.cursor()
            
            # Executar SQL
            cursor.execute(sql_content)
            
            # Commit
            conn.commit()
            
            print("✅ Migração aplicada com sucesso!")
            print("📋 Tabela 'evento_fornecedores' criada/verificada")
            print("📋 Índices criados para performance")
            
            # Verificar se tabela existe
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'evento_fornecedores'
            """)
            
            if cursor.fetchone():
                print("✅ Verificação: Tabela 'evento_fornecedores' existe no banco")
            else:
                print("⚠️ Aviso: Tabela 'evento_fornecedores' não foi encontrada após migração")
            
            cursor.close()
            return True
            
    except Exception as e:
        print(f"❌ Erro ao aplicar migração: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 70)
    print("MIGRAÇÃO: Adicionar tabela de fornecedores por evento")
    print("=" * 70)
    print()
    
    sucesso = aplicar_migracao()
    
    print()
    print("=" * 70)
    if sucesso:
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print()
        print("Próximos passos:")
        print("1. Verifique a aba 'Fornecedores' em Eventos Operacionais")
        print("2. Adicione fornecedores aos eventos")
        print("3. Monitore o cálculo automático de custos")
    else:
        print("❌ MIGRAÇÃO FALHOU - Verifique os erros acima")
    print("=" * 70)
    
    sys.exit(0 if sucesso else 1)
