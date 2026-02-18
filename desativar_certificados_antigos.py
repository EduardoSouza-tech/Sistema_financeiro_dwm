#!/usr/bin/env python3
"""
Script para desativar todos os certificados ativos no banco.
Útil quando a FERNET_KEY mudou e os certificados precisam ser recadastrados.
"""
import sys
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import get_db_connection

print("🔒 Desativando certificados digitais antigos...")
print("📡 Conectando ao banco de dados...\n")

try:
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        
        # Busca certificados ativos
        cursor.execute("""
            SELECT 
                c.id,
                c.empresa_id,
                c.nome_certificado,
                c.cnpj,
                e.razao_social
            FROM certificados_digitais c
            INNER JOIN empresas e ON e.id = c.empresa_id
            WHERE c.ativo = TRUE
            ORDER BY c.empresa_id, c.id
        """)
        
        certificados = cursor.fetchall()
        
        if not certificados:
            print("✅ Nenhum certificado ativo encontrado!")
            print("💡 Todos os certificados já estão desativados.\n")
            sys.exit(0)
        
        print(f"📋 Encontrados {len(certificados)} certificado(s) ativo(s):\n")
        
        for cert in certificados:
            print(f"   🔐 ID {cert['id']} | Empresa {cert['empresa_id']}")
            print(f"      Nome: {cert['nome_certificado']}")
            print(f"      Razão Social: {cert['razao_social']}")
            print(f"      CNPJ: {cert['cnpj']}")
            print()
        
        # Pergunta confirmação
        print("⚠️  Esta operação irá DESATIVAR todos os certificados listados acima.")
        print("   Você precisará recadastrá-los novamente.\n")
        resposta = input("Deseja continuar? (S/N): ").strip().upper()
        
        if resposta != 'S':
            print("❌ Operação cancelada.")
            sys.exit(0)
        
        # Desativa todos os certificados ativos
        print("\n🔧 Desativando certificados...")
        
        cursor.execute("""
            UPDATE certificados_digitais
            SET ativo = FALSE,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE ativo = TRUE
        """)
        
        linhas_afetadas = cursor.rowcount
        conn.commit()
        
        print(f"   ✅ {linhas_afetadas} certificado(s) desativado(s)!")
        
        print(f"\n✅ Todos os certificados foram desativados com sucesso!")
        print(f"\n📋 Próximos passos:")
        print(f"   1. Acesse: Relatórios → 📑 NF-e e CT-e")
        print(f"   2. Clique na aba: 🔐 Certificados Digitais")
        print(f"   3. Clique em: ➕ Novo Certificado")
        print(f"   4. Para cada certificado:")
        print(f"      a) Selecione o arquivo .pfx")
        print(f"      b) Digite a senha")
        print(f"      c) Aguarde extração automática dos dados")
        print(f"      d) Selecione a UF e confirme o ambiente")
        print(f"      e) Salve")
        print(f"\n💡 Após recadastrar, teste a busca automática de documentos!\n")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
