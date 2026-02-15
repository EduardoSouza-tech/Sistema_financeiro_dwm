#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIGRATION: Adicionar coluna 'associacao' na tabela lancamentos

Data: 2026-02-15
Autor: Sistema Financeiro DWM
Descrição: Adiciona campo para usuário associar observações personalizadas aos lançamentos do fluxo de caixa
"""

import os
import sys
from database_postgresql import get_db_connection

def executar_migration():
    """
    Adiciona coluna 'associacao' à tabela lancamentos
    """
    print("="*80)
    print("🔧 MIGRATION: Adicionar coluna 'associacao' na tabela lancamentos")
    print("="*80)
    
    try:
        # Conectar ao banco (sem empresa_id para operações DDL globais)
        with get_db_connection(allow_global=True) as conn:
            cursor = conn.cursor()
            
            # Verificar se a coluna já existe
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='lancamentos' 
                AND column_name='associacao'
            """)
            
            coluna_existe = cursor.fetchone() is not None
            
            if coluna_existe:
                print("ℹ️  Coluna 'associacao' já existe na tabela lancamentos")
                print("✅ Migration não é necessária")
                cursor.close()
                return True
            
            # Adicionar coluna 'associacao'
            print("\n📝 Adicionando coluna 'associacao' na tabela lancamentos...")
            cursor.execute("""
                ALTER TABLE lancamentos 
                ADD COLUMN associacao TEXT DEFAULT ''
            """)
            
            print("✅ Coluna 'associacao' adicionada com sucesso!")
            
            # Criar índice para melhor performance em buscas
            print("\n📊 Criando índice para coluna 'associacao'...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_lancamentos_associacao 
                ON lancamentos(associacao) 
                WHERE associacao IS NOT NULL AND associacao != ''
            """)
            
            print("✅ Índice criado com sucesso!")
            
            conn.commit()
            cursor.close()
            
            print("\n" + "="*80)
            print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
            print("="*80)
            
            return True
            
    except Exception as e:
        print(f"\n❌ ERRO ao executar migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = executar_migration()
    sys.exit(0 if sucesso else 1)
