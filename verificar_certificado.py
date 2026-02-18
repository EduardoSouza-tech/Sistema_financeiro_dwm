#!/usr/bin/env python3
"""
Script para verificar o estado atual do certificado digital no banco.
Mostra se a senha está válida ou precisa ser recadastrada.
"""
import sys
import os

# Carrega variáveis de ambiente do .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Adiciona o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import get_db_connection

print("🔍 Verificando estado dos certificados digitais...")
print("📡 Conectando ao banco de dados...\n")

try:
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.id,
                c.empresa_id,
                c.nome_certificado,
                c.cnpj,
                c.cuf,
                c.ambiente,
                c.ativo,
                LENGTH(c.senha_pfx) as tamanho_senha,
                c.valido_de,
                c.valido_ate,
                e.razao_social
            FROM certificados_digitais c
            INNER JOIN empresas e ON e.id = c.empresa_id
            ORDER BY c.empresa_id, c.id
        """)
        
        certificados = cursor.fetchall()
        
        if not certificados:
            print("❌ Nenhum certificado cadastrado no sistema!\n")
            sys.exit(0)
        
        print(f"📋 Encontrados {len(certificados)} certificado(s):\n")
        print("="*80)
        
        for cert in certificados:
            status_ativo = "✅ ATIVO" if cert['ativo'] else "⏸️ INATIVO"
            
            # Verifica se a senha está em formato válido
            tamanho_senha = cert['tamanho_senha'] or 0
            senha_valida = tamanho_senha >= 50
            
            print(f"\n🔐 Certificado ID: {cert['id']} | Empresa: {cert['empresa_id']}")
            print(f"   Nome: {cert['nome_certificado']}")
            print(f"   Razão Social: {cert['razao_social']}")
            print(f"   CNPJ: {cert['cnpj']}")
            print(f"   UF: {cert['cuf']} | Ambiente: {cert['ambiente']}")
            print(f"   Status: {status_ativo}")
            print(f"   Válido de: {cert['valido_de']} até {cert['valido_ate']}")
            print(f"\n   📊 SENHA:")
            print(f"      Tamanho: {tamanho_senha} caracteres")
            
            if senha_valida:
                print(f"      ✅ Senha em formato VÁLIDO (criptografada)")
            else:
                print(f"      ❌ Senha em formato INVÁLIDO (texto plano ou vazia)")
                print(f"      ⚠️  ESTE CERTIFICADO PRECISA SER RECADASTRADO!")
            
            print("-"*80)
        
        # Conta quantos certificados precisam ser recadastrados
        invalidos = sum(1 for cert in certificados if (cert['tamanho_senha'] or 0) < 50)
        
        print(f"\n📊 RESUMO:")
        print(f"   Total de certificados: {len(certificados)}")
        print(f"   Certificados válidos: {len(certificados) - invalidos}")
        print(f"   Certificados que precisam recadastrar: {invalidos}")
        
        if invalidos > 0:
            print(f"\n⚠️  AÇÃO NECESSÁRIA:")
            print(f"   {invalidos} certificado(s) precisa(m) ser recadastrado(s)!")
            print(f"\n📝 Passos para recadastrar:")
            print(f"   1. Acesse: Relatórios → 📑 NF-e e CT-e")
            print(f"   2. Clique na aba: 🔐 Certificados Digitais")
            print(f"   3. Desative o certificado antigo")
            print(f"   4. Cadastre novo certificado:")
            print(f"      - Selecione o arquivo .pfx")
            print(f"      - Digite a senha do certificado")
            print(f"      - Sistema preenche automaticamente os dados")
            print(f"      - Selecione a UF e confirme o ambiente")
            print(f"      - Salve")
            print(f"\n💡 Após recadastrar, execute este script novamente para verificar!\n")
        else:
            print(f"\n✅ Todos os certificados estão válidos e prontos para uso!\n")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
