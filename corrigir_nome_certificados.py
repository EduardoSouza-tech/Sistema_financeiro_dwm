#!/usr/bin/env python3
"""
Script para corrigir nome_certificado preenchido com "razao_social" literal.
Corrige para usar a razão social real da empresa.
"""
import psycopg2
import psycopg2.extras
import os
import sys

# Database URL
DATABASE_URL = os.environ.get('DATABASE_URL', '')

if not DATABASE_URL:
    print("❌ DATABASE_URL não configurada!")
    sys.exit(1)

print("🔧 Corrigindo nomes de certificados...")

try:
    # Conecta ao banco
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Busca certificados com nome "razao_social" (literal)
    cursor.execute("""
        SELECT c.id, c.empresa_id, c.nome_certificado, e.razao_social
        FROM certificados_digitais c
        INNER JOIN empresas e ON e.id = c.empresa_id
        WHERE c.nome_certificado = 'razao_social'
    """)
    
    certificados = cursor.fetchall()
    
    if not certificados:
        print("✅ Nenhum certificado com nome incorreto encontrado!")
        conn.close()
        sys.exit(0)
    
    print(f"\n📋 Encontrados {len(certificados)} certificado(s) com nome incorreto:\n")
    
    for cert in certificados:
        print(f"   ID {cert['id']} | Empresa {cert['empresa_id']}")
        print(f"   ❌ Nome atual: {cert['nome_certificado']}")
        print(f"   ✅ Será corrigido para: {cert['razao_social']}")
        print()
    
    # Pergunta confirmação
    resposta = input("Deseja corrigir esses certificados? (S/N): ").strip().upper()
    
    if resposta != 'S':
        print("❌ Operação cancelada.")
        conn.close()
        sys.exit(0)
    
    # Corrige os certificados
    print("\n🔧 Aplicando correções...")
    
    for cert in certificados:
        cursor.execute("""
            UPDATE certificados_digitais
            SET nome_certificado = %s,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (cert['razao_social'], cert['id']))
        
        print(f"   ✅ Certificado ID {cert['id']} corrigido!")
    
    # Commit
    conn.commit()
    conn.close()
    
    print(f"\n✅ {len(certificados)} certificado(s) corrigido(s) com sucesso!")
    print("💡 Recarregue a página para ver as alterações.\n")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
