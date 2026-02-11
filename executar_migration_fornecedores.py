#!/usr/bin/env python3
"""
Script para aplicar migration: Schema Completo para Fornecedores
Adiciona todas as colunas faltantes na tabela fornecedores
"""

import os
import sys
import psycopg2
from pathlib import Path

def executar_migration():
    """Executa a migration do schema completo de fornecedores"""
    
    # URL do Railway (produção)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ Variável DATABASE_URL não encontrada!")
        print("💡 Configure com: $env:DATABASE_URL='postgresql://...'")
        return False
    
    print("🚀 Executando migration: Schema Completo para Fornecedores")
    print("=" * 60)
    
    # Ler arquivo SQL
    migration_file = Path(__file__).parent / 'migration_fornecedores_schema_completo.sql'
    
    if not migration_file.exists():
        print(f"❌ Arquivo não encontrado: {migration_file}")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    print(f"📄 Arquivo lido: {migration_file.name}")
    print(f"📊 Tamanho: {len(sql_script)} caracteres")
    print()
    
    try:
        # Conectar ao banco
        print("🔌 Conectando ao banco de dados...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Controlar transação manualmente
        cursor = conn.cursor()
        
        print("✅ Conectado!")
        print()
        
        # Verificar estrutura ANTES
        print("📊 Estrutura ANTES da migration:")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'fornecedores'
            ORDER BY ordinal_position
        """)
        colunas_antes = cursor.fetchall()
        print(f"   Total de colunas: {len(colunas_antes)}")
        for col in colunas_antes:
            print(f"   - {col[0]} ({col[1]})")
        print()
        
        # Executar migration
        print("🔧 Executando migration...")
        cursor.execute(sql_script)
        conn.commit()
        print("✅ Migration executada com sucesso!")
        print()
        
        # Verificar estrutura DEPOIS
        print("📊 Estrutura DEPOIS da migration:")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'fornecedores'
            ORDER BY ordinal_position
        """)
        colunas_depois = cursor.fetchall()
        print(f"   Total de colunas: {len(colunas_depois)}")
        
        # Destacar novas colunas
        colunas_antes_nomes = {c[0] for c in colunas_antes}
        for col in colunas_depois:
            if col[0] not in colunas_antes_nomes:
                print(f"   + {col[0]} ({col[1]}) ← NOVA")
            else:
                print(f"   - {col[0]} ({col[1]})")
        print()
        
        # Verificar índices criados
        print("📇 Índices criados:")
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'fornecedores'
            AND indexname LIKE 'idx_fornecedores_%'
        """)
        indices = cursor.fetchall()
        for idx in indices:
            print(f"   - {idx[0]}")
        print()
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
        print("=" * 60)
        print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
        print()
        print("📋 Novas colunas adicionadas:")
        print("   ✓ razao_social, nome_fantasia")
        print("   ✓ cnpj, documento, ie, im")
        print("   ✓ cep, rua, logradouro, numero, complemento, bairro, cidade, estado")
        print("   ✓ empresa_id, proprietario_id, contato")
        print()
        print("🔄 Próximos passos:")
        print("   1. Faça commit e push do arquivo SQL para o GitHub")
        print("   2. Teste cadastrar um fornecedor no sistema")
        print("   3. Verifique se os dados estruturados aparecem corretamente")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Erro no banco de dados:")
        print(f"   {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False
        
    except Exception as e:
        print(f"❌ Erro inesperado:")
        print(f"   {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   MIGRATION: Schema Completo para Fornecedores           ║")
    print("║   Sistema Financeiro DWM - Railway Database              ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    
    sucesso = executar_migration()
    
    sys.exit(0 if sucesso else 1)
