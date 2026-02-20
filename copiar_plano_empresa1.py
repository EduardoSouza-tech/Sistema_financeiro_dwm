#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copia o Plano de Contas da empresa 20 para a empresa 1
"""

import psycopg2
from urllib.parse import urlparse

DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("📋 COPIAR PLANO DE CONTAS: Empresa 20 → Empresa 1")
print("=" * 80)

try:
    url = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port,
        user=url.username,
        password=url.password,
        database=url.path[1:]
    )
    cursor = conn.cursor()
    
    print("\n🔌 Conectado ao Railway")
    
    # 1. Verificar versão na empresa 1
    cursor.execute("""
        SELECT id, nome_versao FROM plano_contas_versao 
        WHERE empresa_id = 1 AND nome_versao = 'Plano Padrão 2026'
    """)
    versao_emp1 = cursor.fetchone()
    
    if not versao_emp1:
        print("\n📦 Criando versão na empresa 1...")
        cursor.execute("""
            INSERT INTO plano_contas_versao 
                (empresa_id, nome_versao, exercicio_fiscal, data_inicio, data_fim, is_ativa)
            VALUES (1, 'Plano Padrão 2026', 2026, '2026-01-01', '2026-12-31', true)
            RETURNING id
        """)
        versao_id_emp1 = cursor.fetchone()[0]
        print(f"✅ Versão criada: ID {versao_id_emp1}")
    else:
        versao_id_emp1 = versao_emp1[0]
        print(f"\n✅ Versão já existe na empresa 1: ID {versao_id_emp1}")
    
    # 2. Verificar se já tem contas
    cursor.execute("""
        SELECT COUNT(*) FROM plano_contas 
        WHERE empresa_id = 1 AND versao_id = %s
    """, (versao_id_emp1,))
    
    contas_existentes = cursor.fetchone()[0]
    if contas_existentes > 0:
        print(f"\n⚠️ Empresa 1 já tem {contas_existentes} contas nesta versão!")
        print("   Deletando contas antigas...")
        cursor.execute("""
            DELETE FROM plano_contas 
            WHERE empresa_id = 1 AND versao_id = %s
        """, (versao_id_emp1,))
        print(f"✅ {cursor.rowcount} contas antigas deletadas")
    
    # 3. Copiar contas da empresa 20
    print("\n📋 Copiando contas da empresa 20 para empresa 1...")
    
    cursor.execute("""
        INSERT INTO plano_contas 
            (empresa_id, versao_id, codigo, descricao, parent_id, nivel, ordem,
             tipo_conta, classificacao, natureza, is_bloqueada, 
             requer_centro_custo, permite_lancamento)
        SELECT 
            1 as empresa_id,
            %s as versao_id,
            codigo, descricao, parent_id, nivel, ordem,
            tipo_conta, classificacao, natureza, is_bloqueada,
            requer_centro_custo, permite_lancamento
        FROM plano_contas
        WHERE empresa_id = 20 AND versao_id = 4
          AND deleted_at IS NULL
        ORDER BY codigo
    """, (versao_id_emp1,))
    
    copiadas = cursor.rowcount
    conn.commit()
    
    print(f"✅ {copiadas} contas copiadas com sucesso!")
    
    # 4. Verificar
    cursor.execute("""
        SELECT codigo, descricao, classificacao 
        FROM plano_contas 
        WHERE empresa_id = 1 AND versao_id = %s
        ORDER BY codigo
        LIMIT 5
    """, (versao_id_emp1,))
    
    print("\n🔍 Primeiras 5 contas na empresa 1:")
    for row in cursor.fetchall():
        print(f"   {row[0]:15} | {row[1]:30} | {row[2]}")
    
    print("\n" + "=" * 80)
    print("✅ CÓPIA CONCLUÍDA COM SUCESSO!")
    print("=" * 80)
    print("\n📌 AGORA:")
    print("   1. Abra o sistema (empresa 1 já está selecionada)")
    print("   2. Vá em: Contabilidade → Plano de Contas")
    print("   3. As 102 contas devem aparecer corretamente!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
