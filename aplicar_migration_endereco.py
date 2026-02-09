#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar migration de endereço completo em clientes
PARTE 7: Sistema de busca automática via CEP

Este script:
1. Adiciona 7 campos estruturados de endereço na tabela clientes
2. Cria índices para otimizar buscas por CEP e localização
3. Adiciona constraints de validação (formato CEP e Estado)
4. Cria função auxiliar get_endereco_completo()
5. Cria view vw_clientes_com_endereco
6. Migra CEPs do campo "endereco" legado

Autor: Sistema Financeiro DWM
Data: 2026-02-08
"""

import sys
import os
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import DATABASE_CONFIG
except ImportError:
    print("⚠️  ERRO: Arquivo config.py não encontrado!")
    print("   Certifique-se de que DATABASE_CONFIG está configurado")
    sys.exit(1)


def conectar_banco():
    """Conecta ao banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        print("✅ Conectado ao banco de dados PostgreSQL")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        sys.exit(1)


def verificar_campos_existentes(cursor):
    """Verifica se os campos de endereço já existem"""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'clientes' 
          AND column_name IN ('cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado')
        ORDER BY column_name
    """)
    campos_existentes = [row[0] for row in cursor.fetchall()]
    return campos_existentes


def verificar_clientes_sem_endereco(cursor):
    """Conta clientes sem endereço estruturado"""
    cursor.execute("""
        SELECT COUNT(*) 
        FROM clientes 
        WHERE cep IS NULL 
          AND logradouro IS NULL 
          AND cidade IS NULL
    """)
    return cursor.fetchone()[0]


def contar_clientes_por_empresa(cursor):
    """Conta total de clientes por empresa"""
    cursor.execute("""
        SELECT 
            empresa_id,
            COUNT(*) as total,
            COUNT(CASE WHEN ativo THEN 1 END) as ativos,
            COUNT(CASE WHEN cep IS NOT NULL THEN 1 END) as com_cep
        FROM clientes
        WHERE empresa_id IS NOT NULL
        GROUP BY empresa_id
        ORDER BY empresa_id
    """)
    return cursor.fetchall()


def aplicar_migration(cursor):
    """Aplica a migration de endereço completo"""
    
    # Ler arquivo SQL
    sql_file = os.path.join(os.path.dirname(__file__), 'migration_endereco_clientes.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ Arquivo não encontrado: {sql_file}")
        return False
    
    print(f"\n📄 Lendo arquivo: {sql_file}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    try:
        print("\n🔄 Executando migration...")
        cursor.execute(sql_content)
        print("✅ Migration executada com sucesso!")
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Erro ao executar migration: {e}")
        print(f"   Detalhes: {e.pgerror}")
        return False


def validar_migration(cursor):
    """Valida se a migration foi aplicada corretamente"""
    print("\n🔍 Validando migration...")
    
    erros = []
    
    # 1. Verificar se os campos foram criados
    campos_esperados = ['cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado']
    campos_existentes = verificar_campos_existentes(cursor)
    
    campos_faltando = set(campos_esperados) - set(campos_existentes)
    if campos_faltando:
        erros.append(f"Campos faltando: {', '.join(campos_faltando)}")
    else:
        print(f"   ✅ Todos os {len(campos_esperados)} campos foram criados")
    
    # 2. Verificar se os índices foram criados
    cursor.execute("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename = 'clientes' 
          AND indexname IN ('idx_clientes_cep', 'idx_clientes_cidade_estado', 'idx_clientes_empresa_cidade')
    """)
    indices = [row[0] for row in cursor.fetchall()]
    
    if len(indices) == 3:
        print(f"   ✅ Todos os 3 índices foram criados")
    else:
        erros.append(f"Apenas {len(indices)}/3 índices criados")
    
    # 3. Verificar se a função foi criada
    cursor.execute("""
        SELECT COUNT(*) 
        FROM pg_proc 
        WHERE proname = 'get_endereco_completo'
    """)
    if cursor.fetchone()[0] > 0:
        print("   ✅ Função get_endereco_completo() criada")
    else:
        erros.append("Função get_endereco_completo() não encontrada")
    
    # 4. Verificar se a view foi criada
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.views 
        WHERE table_name = 'vw_clientes_com_endereco'
    """)
    if cursor.fetchone()[0] > 0:
        print("   ✅ View vw_clientes_com_endereco criada")
    else:
        erros.append("View vw_clientes_com_endereco não encontrada")
    
    # 5. Verificar constraints
    cursor.execute("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name = 'clientes' 
          AND constraint_name IN ('chk_cep_formato', 'chk_estado_valido')
    """)
    constraints = [row[0] for row in cursor.fetchall()]
    
    if len(constraints) == 2:
        print(f"   ✅ Todas as 2 constraints criadas")
    else:
        erros.append(f"Apenas {len(constraints)}/2 constraints criadas")
    
    return len(erros) == 0, erros


def gerar_relatorio(cursor):
    """Gera relatório pós-migration"""
    print("\n" + "="*60)
    print("📊 RELATÓRIO DA MIGRATION")
    print("="*60)
    
    # Estatísticas por empresa
    print("\n🏢 Clientes por Empresa:")
    print(f"{'Empresa':<10} {'Total':<10} {'Ativos':<10} {'Com CEP':<10}")
    print("-" * 60)
    
    stats = contar_clientes_por_empresa(cursor)
    total_geral = 0
    total_ativos = 0
    total_com_cep = 0
    
    for empresa_id, total, ativos, com_cep in stats:
        print(f"{empresa_id:<10} {total:<10} {ativos:<10} {com_cep:<10}")
        total_geral += total
        total_ativos += ativos
        total_com_cep += com_cep
    
    print("-" * 60)
    print(f"{'TOTAL':<10} {total_geral:<10} {total_ativos:<10} {total_com_cep:<10}")
    
    # Clientes sem endereço
    sem_endereco = verificar_clientes_sem_endereco(cursor)
    print(f"\n📋 Clientes sem endereço estruturado: {sem_endereco}")
    
    if sem_endereco > 0:
        percentual = (sem_endereco / total_geral * 100) if total_geral > 0 else 0
        print(f"   ({percentual:.1f}% do total)")
        print("   💡 Estes clientes precisarão ter o CEP preenchido manualmente")
    
    # Testar função get_endereco_completo
    print("\n🧪 Teste da função get_endereco_completo():")
    cursor.execute("""
        SELECT get_endereco_completo(
            'Rua das Flores',
            '123',
            'Apto 45',
            'Centro',
            'São Paulo',
            'SP',
            '01234-567'
        ) AS endereco_exemplo
    """)
    exemplo = cursor.fetchone()[0]
    print(f"   {exemplo}")


def main():
    """Função principal"""
    print("\n" + "="*60)
    print("🚀 APLICANDO MIGRATION: ENDEREÇO COMPLETO")
    print("="*60)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Arquivo: migration_endereco_clientes.sql")
    
    # Conectar ao banco
    conn = conectar_banco()
    cursor = conn.cursor()
    
    try:
        # Verificar estado atual
        print("\n🔍 Verificando estado atual...")
        campos_existentes = verificar_campos_existentes(cursor)
        
        if campos_existentes:
            print(f"⚠️  Atenção: {len(campos_existentes)} campos já existem:")
            for campo in campos_existentes:
                print(f"   • {campo}")
            
            resposta = input("\n❓ Deseja continuar mesmo assim? (s/N): ").strip().lower()
            if resposta != 's':
                print("❌ Operação cancelada pelo usuário")
                return
        
        # Aplicar migration
        if not aplicar_migration(cursor):
            print("\n❌ Migration falhou!")
            conn.rollback()
            return
        
        # Validar
        sucesso, erros = validar_migration(cursor)
        
        if not sucesso:
            print("\n⚠️  AVISOS durante validação:")
            for erro in erros:
                print(f"   • {erro}")
            
            resposta = input("\n❓ Deseja fazer COMMIT mesmo assim? (s/N): ").strip().lower()
            if resposta != 's':
                print("❌ Rollback realizado")
                conn.rollback()
                return
        
        # Commit
        conn.commit()
        print("\n✅ COMMIT realizado com sucesso!")
        
        # Gerar relatório
        gerar_relatorio(cursor)
        
        print("\n" + "="*60)
        print("🎉 MIGRATION CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print("\n📝 Próximos passos:")
        print("   1. Atualizar backend (database_postgresql.py)")
        print("   2. Criar função de busca CEP via ViaCEP no frontend")
        print("   3. Atualizar formulário de clientes para usar novos campos")
        print("   4. Testar preenchimento automático ao digitar CEP")
        print("")
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        conn.rollback()
        raise
        
    finally:
        cursor.close()
        conn.close()
        print("🔌 Conexão fechada")


if __name__ == "__main__":
    main()
