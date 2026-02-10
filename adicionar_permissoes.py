#!/usr/bin/env python3
"""
Script para adicionar permissões de configuração de extrato aos usuários
Data: 2026-02-10
"""

import psycopg2
import os
import sys

def main():
    print("=" * 80)
    print("ADICIONANDO PERMISSOES DE CONFIGURACAO DE EXTRATO")
    print("=" * 80)
    print()
    
    # Obter DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("ERRO: DATABASE_URL nao encontrada!")
        print("Configure a variavel de ambiente")
        return 1
    
    print("Conectando ao banco...")
    
    try:
        # Conectar ao banco
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("Conectado com sucesso!")
        print()
        
        # 1. Garantir que as permissões existem
        print("1. Adicionando permissoes na tabela...")
        cursor.execute("""
            INSERT INTO permissoes (codigo, nome, descricao, categoria) VALUES
            ('config_extrato_bancario_view', 'Visualizar Configuracoes de Extrato', 'Permite visualizar configuracoes de extrato bancario', 'configuracoes'),
            ('config_extrato_bancario_edit', 'Editar Configuracoes de Extrato', 'Permite editar configuracoes de extrato bancario', 'configuracoes')
            ON CONFLICT (codigo) DO NOTHING
        """)
        conn.commit()
        print("   OK")
        
        # 2. Adicionar permissões aos usuários
        print("2. Adicionando permissoes aos usuarios ativos...")
        cursor.execute("""
            UPDATE usuario_empresas
            SET permissoes_empresa = permissoes_empresa || 
                jsonb_build_array('config_extrato_bancario_view', 'config_extrato_bancario_edit')
            WHERE ativo = TRUE
              AND NOT (permissoes_empresa @> '["config_extrato_bancario_view"]'::jsonb)
        """)
        conn.commit()
        rows_updated = cursor.rowcount
        print(f"   {rows_updated} usuario(s) atualizado(s)")
        
        # 3. Verificar total
        print("3. Verificando total de usuarios com permissoes...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM usuario_empresas
            WHERE ativo = TRUE
              AND permissoes_empresa @> '["config_extrato_bancario_view"]'::jsonb
        """)
        
        total = cursor.fetchone()[0]
        print(f"   {total} usuario(s) com permissoes de config extrato")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 80)
        print("CONCLUIDO COM SUCESSO!")
        print("=" * 80)
        print()
        print("Faca LOGOUT e LOGIN novamente para carregar as novas permissoes")
        
        return 0
        
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
