#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar migration da associação no Railway
Execute este script após o deploy para criar a coluna associacao
"""

import os
import sys

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("="*80)
    print("🚀 EXECUTANDO MIGRATION NO RAILWAY")
    print("="*80)
    
    # Importar e executar migration
    from migration_add_associacao_lancamentos import executar_migration
    
    sucesso = executar_migration()
    
    if sucesso:
        print("\n✅ Migration executada com sucesso!")
        print("   A coluna 'associacao' foi adicionada à tabela lancamentos")
        sys.exit(0)
    else:
        print("\n❌ Falha ao executar migration")
        sys.exit(1)
