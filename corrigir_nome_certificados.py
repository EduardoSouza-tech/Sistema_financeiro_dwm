#!/usr/bin/env python3
"""
Script para corrigir nome_certificado preenchido com "razao_social" literal.
Corrige para usar a razão social real da empresa.
"""
import sys
import os

# Carrega variáveis de ambiente do .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv não instalado, usando variáveis de ambiente do sistema")

# Adiciona o diretório pai ao path para importar database_postgresql
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import get_db_connection

print("🔧 Corrigindo nomes de certificados...")
print("📡 Conectando ao banco de dados...\n")

try:
    # Conecta ao banco usando a função do sistema (allow_global para acessar todas as empresas)
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        
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
            print("💡 Todos os certificados já estão corretos!\n")
            sys.exit(0)
        
        print(f"📋 Encontrados {len(certificados)} certificado(s) com nome incorreto:\n")
        
        for cert in certificados:
            print(f"   ID {cert['id']} | Empresa {cert['empresa_id']}")
            print(f"   ❌ Nome atual: {cert['nome_certificado']}")
            print(f"   ✅ Será corrigido para: {cert['razao_social']}")
            print()
        
        # Pergunta confirmação
        resposta = input("Deseja corrigir esses certificados? (S/N): ").strip().upper()
        
        if resposta != 'S':
            print("❌ Operação cancelada.")
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
        
        print(f"\n✅ {len(certificados)} certificado(s) corrigido(s) com sucesso!")
        print("💡 Recarregue a página para ver as alterações.\n")
        print("⚠️  IMPORTANTE: O certificado ainda precisa ser RECADASTRADO para corrigir a senha!\n")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
