#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de execução de migration: Sistema NF-e/CT-e
Executa migration_nfe_cte_relatorios.sql

Uso:
    python executar_migration_nfe_cte.py

Autor: Sistema Financeiro DWM
Data: 2026-02-17
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from database_postgresql import get_connection


def executar_migration():
    """Executa a migration para criar tabelas de NF-e/CT-e"""
    
    print("=" * 70)
    print("MIGRATION: Sistema de Busca NF-e/CT-e")
    print("=" * 70)
    print()
    
    # Verificar se DATABASE_URL está configurada
    if not os.getenv('DATABASE_URL'):
        print("❌ ERRO: DATABASE_URL não configurada!")
        print("Configure a variável de ambiente DATABASE_URL no arquivo .env")
        return False
    
    # Ler arquivo SQL
    migration_file = Path(__file__).parent / 'migration_nfe_cte_relatorios.sql'
    
    if not migration_file.exists():
        print(f"❌ ERRO: Arquivo {migration_file} não encontrado!")
        return False
    
    print(f"📄 Lendo migration: {migration_file.name}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"✓ Migration lida com sucesso ({len(sql_content)} caracteres)")
    print()
    
    # Conectar ao banco
    print("🔌 Conectando ao banco de dados...")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        print("✓ Conexão estabelecida")
        print()
        
        # Executar migration
        print("⚙️  Executando migration...")
        print()
        
        cursor.execute(sql_content)
        conn.commit()
        
        print()
        print("=" * 70)
        print("✅ MIGRATION EXECUTADA COM SUCESSO!")
        print("=" * 70)
        print()
        print("Tabelas criadas:")
        print("  ✓ certificados_digitais")
        print("  ✓ documentos_fiscais_log")
        print()
        print("Views criadas:")
        print("  ✓ v_certificados_stats")
        print("  ✓ v_documentos_recentes")
        print("  ✓ v_resumo_mensal_docs")
        print()
        print("Permissões criadas:")
        print("  ✓ relatorios.nfe.*")
        print("  ✓ relatorios.cte.*")
        print("  ✓ relatorios.certificados.*")
        print()
        print("Próximos passos:")
        print("  1. Implementar módulos Python (nfe_busca, nfe_processor, nfe_storage)")
        print("  2. Criar endpoints da API")
        print("  3. Criar interface web")
        print()
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERRO AO EXECUTAR MIGRATION")
        print("=" * 70)
        print(f"Erro: {str(e)}")
        print()
        
        if 'conn' in locals():
            conn.rollback()
            if 'cursor' in locals():
                cursor.close()
            conn.close()
        
        return False


if __name__ == '__main__':
    print()
    sucesso = executar_migration()
    print()
    
    if sucesso:
        sys.exit(0)
    else:
        sys.exit(1)
