#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpar registros corruptos do Plano de Contas
Deleta TODOS os registros da versão 4 que possuem dados literais ('codigo', 'descricao', etc)
e reimporta o plano padrão corretamente.
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def conectar_railway():
    """Conecta ao banco de dados Railway"""
    # Tenta obter da variável de ambiente ou solicita ao usuário
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("\n📋 Cole a DATABASE_URL do Railway:")
        print("   (pode obter em: https://railway.app/project/...")
        database_url = input("👉 DATABASE_URL: ").strip()
        
        if not database_url:
            # Fallback para URL padrão mais recente
            database_url = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'
            print(f"⚠️ Usando URL padrão do banco")
    
    print(f"🔌 Conectando ao Railway...")
    url = urlparse(database_url)
    
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port,
        user=url.username,
        password=url.password,
        database=url.path[1:]
    )
    
    print(f"✅ Conectado: {url.hostname}:{url.port}/{url.path[1:]}")
    return conn


def limpar_plano_corrupto(empresa_id=20, versao_id=4):
    """
    Deleta TODOS os registros da versão 4 da empresa 20
    """
    conn = conectar_railway()
    cursor = conn.cursor()
    
    try:
        # 1. Verificar quantos registros existem
        cursor.execute("""
            SELECT COUNT(*) FROM plano_contas 
            WHERE empresa_id = %s AND versao_id = %s
        """, (empresa_id, versao_id))
        
        total = cursor.fetchone()[0]
        print(f"\n📊 Encontrados {total} registros na versão {versao_id}")
        
        if total == 0:
            print("⚠️ Não há registros para limpar!")
            return
        
        # 2. Mostrar amostra dos dados corruptos
        cursor.execute("""
            SELECT id, codigo, descricao, classificacao, tipo_conta
            FROM plano_contas 
            WHERE empresa_id = %s AND versao_id = %s
            LIMIT 3
        """, (empresa_id, versao_id))
        
        print(f"\n🔍 Amostra dos dados atuais:")
        for row in cursor.fetchall():
            print(f"   ID: {row[0]} | Código: '{row[1]}' | Descrição: '{row[2]}' | Class: '{row[3]}' | Tipo: '{row[4]}'")
        
        # 3. Confirmar se os dados estão corruptos
        cursor.execute("""
            SELECT COUNT(*) FROM plano_contas 
            WHERE empresa_id = %s AND versao_id = %s 
              AND codigo = 'codigo' AND descricao = 'descricao'
        """, (empresa_id, versao_id))
        
        corruptos = cursor.fetchone()[0]
        print(f"\n⚠️ Registros corruptos detectados: {corruptos}/{total}")
        
        if corruptos == 0:
            print("✅ Dados não estão corruptos! Abortando limpeza.")
            return
        
        # 4. DELETAR TODOS OS REGISTROS da versão
        print(f"\n🗑️ DELETANDO {total} registros da versão {versao_id}...")
        
        cursor.execute("""
            DELETE FROM plano_contas 
            WHERE empresa_id = %s AND versao_id = %s
        """, (empresa_id, versao_id))
        
        conn.commit()
        print(f"✅ {cursor.rowcount} registros deletados com sucesso!")
        
        # 5. Verificar limpeza
        cursor.execute("""
            SELECT COUNT(*) FROM plano_contas 
            WHERE empresa_id = %s AND versao_id = %s
        """, (empresa_id, versao_id))
        
        restantes = cursor.fetchone()[0]
        print(f"📊 Registros restantes: {restantes}")
        
        if restantes == 0:
            print("\n✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
            print("\n📌 PRÓXIMO PASSO:")
            print("   1. Abra o sistema no navegador")
            print("   2. Vá em 'Plano de Contas'")
            print("   3. Clique em '📦 Importar Plano Padrão'")
            print("   4. Aguarde a importação das 106 contas")
        else:
            print(f"\n⚠️ ATENÇÃO: Ainda restam {restantes} registros!")
        
    except Exception as e:
        print(f"\n❌ Erro durante limpeza: {e}")
        conn.rollback()
        raise
    
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    print("=" * 70)
    print("🧹 LIMPEZA DE PLANO DE CONTAS CORRUPTO")
    print("=" * 70)
    print("\n⚠️ Este script irá DELETAR todos os registros da versão 4")
    print("   que contêm dados literais ('codigo', 'descricao', etc)")
    print()
    
    try:
        limpar_plano_corrupto(empresa_id=20, versao_id=4)
        print("\n" + "=" * 70)
        print("✅ Script concluído!")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Falha: {e}")
        sys.exit(1)
