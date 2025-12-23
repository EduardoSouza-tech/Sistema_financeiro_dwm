"""
Script para criar as novas tabelas no banco PostgreSQL do Railway
"""
import os
import sys

# Importar o database_postgresql
import database_postgresql

def criar_tabelas():
    """Cria todas as tabelas incluindo as novas do menu Operacional"""
    print("🔧 Iniciando criação de tabelas no PostgreSQL...")
    
    try:
        db = database_postgresql.DatabaseManager()
        print("✅ Conexão estabelecida com sucesso!")
        print("✅ Tabelas criadas/verificadas com sucesso!")
        
        # Testar listando contratos
        contratos = database_postgresql.listar_contratos()
        print(f"✅ Teste de listagem: {len(contratos)} contratos encontrados")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    criar_tabelas()
