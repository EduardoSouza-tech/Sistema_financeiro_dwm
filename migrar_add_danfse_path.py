#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIGRAÇÃO: Adicionar coluna danfse_path na tabela nfse_baixadas

Esta migração adiciona suporte para armazenar o caminho do PDF oficial (DANFSe)
baixado do Ambiente Nacional.

Quando executar, PDFs oficiais já baixados poderão ser utilizados ao invés de
gerar PDFs genéricos.
"""

import psycopg2
import logging
from database_postgresql import get_nfse_db_params

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def aplicar_migracao():
    """
    Adiciona coluna danfse_path à tabela nfse_baixadas
    """
    db_params = get_nfse_db_params()
    
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        logger.info("🔄 Iniciando migração: adicionar coluna danfse_path...")
        
        # Verificar se coluna já existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'nfse_baixadas' 
            AND column_name = 'danfse_path'
        """)
        
        if cursor.fetchone():
            logger.info("✅ Coluna danfse_path já existe!")
            cursor.close()
            conn.close()
            return True
        
        # Adicionar coluna
        cursor.execute("""
            ALTER TABLE nfse_baixadas 
            ADD COLUMN danfse_path VARCHAR(500);
        """)
        
        conn.commit()
        logger.info("✅ Coluna danfse_path adicionada com sucesso!")
        
        # Adicionar índice para busca rápida
        cursor.execute("""
            CREATE INDEX idx_nfse_baixadas_danfse_path 
            ON nfse_baixadas(danfse_path)
            WHERE danfse_path IS NOT NULL;
        """)
        
        conn.commit()
        logger.info("✅ Índice criado para danfse_path!")
        
        cursor.close()
        conn.close()
        
        logger.info("🎉 Migração concluída com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na migração: {e}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("MIGRAÇÃO: Adicionar suporte para DANFSe oficial")
    print("=" * 70)
    print()
    print("Esta migração adiciona a coluna 'danfse_path' na tabela nfse_baixadas.")
    print("Isso permite armazenar o caminho do PDF oficial baixado do Ambiente Nacional.")
    print()
    input("Pressione ENTER para continuar...")
    print()
    
    if aplicar_migracao():
        print()
        print("✅ Migração aplicada com sucesso!")
        print()
        print("Próximos passos:")
        print("1. Execute uma busca de NFS-e para baixar PDFs oficiais")
        print("2. Os PDFs oficiais serão usados automaticamente ao invés dos genéricos")
    else:
        print()
        print("❌ Erro ao aplicar migração. Verifique os logs acima.")
