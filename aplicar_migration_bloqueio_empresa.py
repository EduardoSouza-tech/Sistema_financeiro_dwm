#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: Bloqueio de empresa (falta de pagamento / contrato encerrado)

Adiciona à tabela `empresas` os campos necessários para registrar o motivo
e os metadados de um bloqueio de acesso, complementando a coluna `ativo`
já existente:

- motivo_bloqueio      VARCHAR(30)  ('pagamento_atrasado' | 'contrato_encerrado' | 'outro')
- observacao_bloqueio  TEXT
- data_bloqueio        TIMESTAMP
- bloqueado_por        VARCHAR(150)

Idempotente (ADD COLUMN IF NOT EXISTS) - seguro para rodar mais de uma vez.

Autor: Sistema Financeiro DWM
Data: 2026-08-11
"""

import sys
import os
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import POSTGRESQL_CONFIG
    DB_KWARGS = POSTGRESQL_CONFIG
except ImportError:
    DB_KWARGS = None


def conectar_banco():
    """Conecta ao banco. Usa DATABASE_URL se definida, senão POSTGRESQL_CONFIG do config.py"""
    database_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_PUBLIC_URL')
    try:
        if database_url:
            conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(**DB_KWARGS)
        print("[OK] Conectado ao banco de dados PostgreSQL")
        return conn
    except Exception as e:
        print(f"[ERRO] Erro ao conectar ao banco: {e}")
        sys.exit(1)


SQL_MIGRATION = """
ALTER TABLE empresas
    ADD COLUMN IF NOT EXISTS motivo_bloqueio VARCHAR(30),
    ADD COLUMN IF NOT EXISTS observacao_bloqueio TEXT,
    ADD COLUMN IF NOT EXISTS data_bloqueio TIMESTAMP,
    ADD COLUMN IF NOT EXISTS bloqueado_por VARCHAR(150);

COMMENT ON COLUMN empresas.motivo_bloqueio IS 'Motivo do bloqueio de acesso: pagamento_atrasado | contrato_encerrado | outro';
COMMENT ON COLUMN empresas.observacao_bloqueio IS 'Observacao livre sobre o bloqueio (obrigatoria quando motivo = outro)';
COMMENT ON COLUMN empresas.data_bloqueio IS 'Data/hora em que o bloqueio foi aplicado';
COMMENT ON COLUMN empresas.bloqueado_por IS 'Usuario admin que aplicou o bloqueio';
"""


def aplicar_migration(cursor):
    print("\n[MIGRATION] Adicionando colunas de bloqueio na tabela empresas...")
    cursor.execute(SQL_MIGRATION)
    print("[OK] Migration executada com sucesso!")


def validar_migration(cursor):
    print("\n[VALIDACAO] Verificando colunas criadas...")
    colunas_esperadas = {
        'motivo_bloqueio', 'observacao_bloqueio', 'data_bloqueio', 'bloqueado_por'
    }
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'empresas'
        AND column_name = ANY(%s)
    """, (list(colunas_esperadas),))

    encontradas = {row[0] for row in cursor.fetchall()}
    faltando = colunas_esperadas - encontradas

    if not faltando:
        print(f"   [OK] Todas as {len(colunas_esperadas)} colunas foram criadas")
        return True
    else:
        print(f"   [ERRO] Colunas faltando: {', '.join(faltando)}")
        return False


def main():
    print("\n" + "=" * 60)
    print("MIGRATION: BLOQUEIO DE EMPRESA (pagamento/contrato)")
    print("=" * 60)

    conn = conectar_banco()
    cursor = conn.cursor()

    try:
        aplicar_migration(cursor)
        conn.commit()
        print("\n[OK] COMMIT realizado com sucesso!")

        ok = validar_migration(cursor)
        if not ok:
            print("\n[AVISO] Validacao encontrou problemas - verifique manualmente.")
        else:
            print("\n[SUCESSO] Migration concluida e validada!")

    except Exception as e:
        print(f"\n[ERRO] Erro inesperado: {e}")
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()
        print("Conexao fechada")


if __name__ == "__main__":
    main()
