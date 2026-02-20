#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIMPEZA IMEDIATA - Deleta registros corruptos do Plano de Contas versão 4
"""

import psycopg2
from urllib.parse import urlparse

# URL DO RAILWAY - HARDCODED
DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("🧹 LIMPEZA DE PLANO DE CONTAS CORRUPTO - VERSÃO 4")
print("=" * 80)
print(f"\n🎯 Empresa ID: 20 (COOPSERVICOS)")
print(f"🎯 Versão ID: 4 (Plano Padrão 2026)")
print()

try:
    # Conectar
    print("🔌 Conectando ao Railway...")
    url = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port,
        user=url.username,
        password=url.password,
        database=url.path[1:]
    )
    cursor = conn.cursor()
    print(f"✅ Conectado: {url.hostname}:{url.port}")
    
    # 1. Contar registros atuais
    cursor.execute("""
        SELECT COUNT(*) FROM plano_contas 
        WHERE empresa_id = 20 AND versao_id = 4
    """)
    total = cursor.fetchone()[0]
    print(f"\n📊 Registros encontrados: {total}")
    
    if total == 0:
        print("✅ Não há registros para limpar!")
        exit(0)
    
    # 2. Verificar se estão corruptos
    cursor.execute("""
        SELECT id, codigo, descricao, classificacao 
        FROM plano_contas 
        WHERE empresa_id = 20 AND versao_id = 4
        LIMIT 3
    """)
    
    print(f"\n🔍 Amostra dos dados:")
    for row in cursor.fetchall():
        print(f"   ID: {row[0]} | Código: '{row[1]}' | Descrição: '{row[2]}' | Class: '{row[3]}'")
    
    cursor.execute("""
        SELECT COUNT(*) FROM plano_contas 
        WHERE empresa_id = 20 AND versao_id = 4 
          AND codigo = 'codigo' AND descricao = 'descricao'
    """)
    corruptos = cursor.fetchone()[0]
    print(f"\n⚠️ Registros corruptos: {corruptos}/{total}")
    
    if corruptos == 0:
        print("✅ Dados não estão corruptos! Nada a fazer.")
        exit(0)
    
    # 3. DELETAR
    print(f"\n🗑️ DELETANDO {total} registros...")
    print("   ⏳ Aguarde...")
    
    cursor.execute("""
        DELETE FROM plano_contas 
        WHERE empresa_id = 20 AND versao_id = 4
    """)
    
    conn.commit()
    deletados = cursor.rowcount
    print(f"✅ {deletados} registros deletados!")
    
    # 4. Verificar
    cursor.execute("""
        SELECT COUNT(*) FROM plano_contas 
        WHERE empresa_id = 20 AND versao_id = 4
    """)
    restantes = cursor.fetchone()[0]
    
    print(f"📊 Registros restantes: {restantes}")
    
    if restantes == 0:
        print("\n" + "=" * 80)
        print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        print("\n📌 PRÓXIMOS PASSOS:")
        print("   1. Abra o sistema no navegador:")
        print("      https://sistemafinanceirodwm-production.up.railway.app/")
        print("   2. Vá em: Contabilidade → Plano de Contas")
        print("   3. Clique em: '📦 Importar Plano Padrão'")
        print("   4. Aguarde: Deve importar 106 contas corretamente")
        print("\n💡 Se ainda importar dados corruptos, avise!")
    else:
        print(f"\n⚠️ ATENÇÃO: Ainda restam {restantes} registros!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    print(f"   Tipo: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 80)
