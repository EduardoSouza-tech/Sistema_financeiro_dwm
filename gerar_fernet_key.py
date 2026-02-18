#!/usr/bin/env python3
"""
Script para gerar e adicionar FERNET_KEY ao arquivo .env
"""
from cryptography.fernet import Fernet
import os

print("🔑 Gerando FERNET_KEY para criptografia de senhas...\n")

# Gera uma nova chave Fernet
nova_chave = Fernet.generate_key()
print(f"✅ Chave gerada: {nova_chave.decode()}\n")

# Caminho do arquivo .env
env_path = os.path.join(os.path.dirname(__file__), '.env')

# Lê o conteúdo atual do .env
with open(env_path, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

# Verifica se já existe FERNET_KEY
tem_fernet = any('FERNET_KEY' in linha for linha in linhas)

if tem_fernet:
    print("⚠️  FERNET_KEY já existe no .env!")
    print("   Se você substituir, os certificados antigos não funcionarão mais.\n")
    resposta = input("Deseja substituir a chave existente? (S/N): ").strip().upper()
    if resposta != 'S':
        print("❌ Operação cancelada.")
        exit(0)
    
    # Remove linha antiga
    linhas = [l for l in linhas if 'FERNET_KEY' not in l]

# Adiciona a nova chave
linhas.append(f'\n# Chave para criptografia de senhas de certificados digitais\n')
linhas.append(f'FERNET_KEY={nova_chave.decode()}\n')

# Salva o arquivo
with open(env_path, 'w', encoding='utf-8') as f:
    f.writelines(linhas)

print("✅ FERNET_KEY adicionada ao arquivo .env com sucesso!")
print(f"\n📄 Arquivo: {env_path}")
print(f"\n⚠️  IMPORTANTE:")
print(f"   1. Esta chave foi adicionada ao .env (NÃO está versionada no Git)")
print(f"   2. TODOS os certificados precisam ser RECADASTRADOS")
print(f"   3. Guarde esta chave em local seguro (backup)")
print(f"\n📋 Próximos passos:")
print(f"   1. Reinicie o servidor Flask")
print(f"   2. Acesse: Relatórios → NF-e e CT-e → Certificados Digitais")
print(f"   3. Desative os certificados antigos")
print(f"   4. Cadastre novamente com arquivo .pfx e senha\n")
