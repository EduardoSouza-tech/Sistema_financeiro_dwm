#!/usr/bin/env python3
"""
Script para testar a descriptografia das senhas dos certificados.
Verifica se a chave FERNET_KEY atual consegue descriptografar.
"""
import sys
import os

# Carrega variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import get_db_connection
from relatorios.nfe import nfe_api

print("🔑 Testando descriptografia das senhas dos certificados...")
print("📡 Conectando ao banco de dados...\n")

# Verifica se FERNET_KEY está configurada
fernet_key = os.environ.get('FERNET_KEY', '').encode('utf-8')
if not fernet_key:
    print("❌ ERRO CRÍTICO: Variável FERNET_KEY não está configurada!")
    print("   Sem esta chave, não é possível descriptografar as senhas.\n")
    print("💡 Solução:")
    print("   1. Configure a variável FERNET_KEY no arquivo .env")
    print("   2. Ou recadastre todos os certificados\n")
    sys.exit(1)

print(f"✅ FERNET_KEY encontrada: {len(fernet_key)} bytes\n")

try:
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.id,
                c.empresa_id,
                c.nome_certificado,
                c.cnpj,
                c.senha_pfx,
                c.ativo
            FROM certificados_digitais c
            WHERE c.ativo = TRUE
            ORDER BY c.empresa_id, c.id
        """)
        
        certificados = cursor.fetchall()
        
        if not certificados:
            print("❌ Nenhum certificado ATIVO cadastrado no sistema!\n")
            sys.exit(0)
        
        print(f"📋 Testando {len(certificados)} certificado(s) ativo(s):\n")
        print("="*80)
        
        erros = 0
        sucessos = 0
        
        for cert in certificados:
            print(f"\n🔐 Certificado ID: {cert['id']} ({cert['nome_certificado']})")
            print(f"   CNPJ: {cert['cnpj']}")
            
            senha_cripto = cert['senha_pfx']
            
            try:
                # Tenta descriptografar
                senha_plana = nfe_api.descriptografar_senha(senha_cripto, fernet_key)
                print(f"   ✅ Descriptografia: SUCESSO")
                print(f"   📏 Senha descriptografada tem {len(senha_plana)} caracteres")
                sucessos += 1
            except ValueError as ve:
                print(f"   ❌ Descriptografia: FALHOU")
                print(f"   ⚠️  Erro: {str(ve)}")
                print(f"   💡 Este certificado precisa ser RECADASTRADO")
                erros += 1
            except Exception as e:
                print(f"   ❌ Descriptografia: ERRO DESCONHECIDO")
                print(f"   ⚠️  Erro: {str(e)}")
                erros += 1
            
            print("-"*80)
        
        print(f"\n📊 RESUMO DOS TESTES:")
        print(f"   ✅ Certificados OK: {sucessos}")
        print(f"   ❌ Certificados com erro: {erros}")
        
        if erros > 0:
            print(f"\n⚠️  AÇÃO NECESSÁRIA:")
            print(f"   {erros} certificado(s) não pode(m) ser descriptografado(s)!")
            print(f"\n🔧 POSSÍVEIS CAUSAS:")
            print(f"   1. FERNET_KEY mudou desde que o certificado foi cadastrado")
            print(f"   2. Certificado foi cadastrado em outro ambiente")
            print(f"   3. Certificado foi cadastrado com senha em texto plano")
            print(f"\n✅ SOLUÇÃO:")
            print(f"   Recadastrar o(s) certificado(s) com problema:")
            print(f"   1. Acesse: Relatórios → 📑 NF-e e CT-e → 🔐 Certificados")
            print(f"   2. Desative o certificado antigo")
            print(f"   3. Cadastre novamente com o arquivo .pfx e senha correta\n")
        else:
            print(f"\n✅ Todos os certificados podem ser descriptografados!")
            print(f"   O sistema está funcionando corretamente.\n")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
