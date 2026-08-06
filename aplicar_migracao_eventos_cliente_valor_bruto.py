#!/usr/bin/env python3
"""
Script para aplicar migração: coluna cliente e valor_bruto_nf em eventos
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import get_db_connection


def aplicar_migracao():
    """Aplica migração das colunas cliente e valor_bruto_nf em eventos"""
    print("🔧 Aplicando migração: eventos.cliente / eventos.valor_bruto_nf...")

    sql_file = os.path.join(os.path.dirname(__file__), 'sql', 'migrations', 'migration_eventos_cliente_valor_bruto.sql')

    if not os.path.exists(sql_file):
        print(f"❌ Arquivo {sql_file} não encontrado!")
        return False

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    try:
        with get_db_connection(allow_global=True) as conn:
            cursor = conn.cursor()
            cursor.execute(sql_content)
            conn.commit()

            print("✅ Migração aplicada com sucesso!")

            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'eventos' AND column_name IN ('cliente', 'valor_bruto_nf')
            """)
            colunas = [row[0] if not isinstance(row, dict) else row['column_name'] for row in cursor.fetchall()]

            if 'cliente' in colunas and 'valor_bruto_nf' in colunas:
                print("✅ Verificação: colunas 'cliente' e 'valor_bruto_nf' existem em 'eventos'")
            else:
                print(f"⚠️ Aviso: colunas encontradas = {colunas}")

            cursor.close()
            return True

    except Exception as e:
        print(f"❌ Erro ao aplicar migração: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 70)
    print("MIGRAÇÃO: eventos.cliente + eventos.valor_bruto_nf")
    print("=" * 70)
    print()

    sucesso = aplicar_migracao()

    print()
    print("=" * 70)
    if sucesso:
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    else:
        print("❌ MIGRAÇÃO FALHOU - Verifique os erros acima")
    print("=" * 70)

    sys.exit(0 if sucesso else 1)
