#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testa a API do Railway DIRETAMENTE para ver o que está retornando
"""

import requests
import json

# URL da API do Railway
API_URL = "https://sistemafinanceirodwm-production.up.railway.app"

print("=" * 80)
print("🧪 TESTE DA API DO RAILWAY - Plano de Contas")
print("=" * 80)

try:
    # Fazer login primeiro
    print("\n🔐 Passo 1: Fazendo login...")
    session = requests.Session()
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    login_response = session.post(f"{API_URL}/api/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login falhou: {login_response.status_code}")
        print(login_response.text)
        exit(1)
    
    print("✅ Login bem-sucedido")
    
    # Buscar contas do plano
    print("\n📊 Passo 2: Buscando contas da versão 1 (empresa 1)...")
    
    api_response = session.get(
        f"{API_URL}/api/contabilidade/plano-contas",
        params={"versao_id": 1}
    )
    
    print(f"📡 Status: {api_response.status_code}")
    
    if api_response.status_code != 200:
        print(f"❌ Requisição falhou: {api_response.text}")
        exit(1)
    
    data = api_response.json()
    
    print(f"✅ Response recebido")
    print(f"\n📦 Total de contas: {data.get('total', 0)}")
    print(f"📦 Sucesso: {data.get('success')}")
    
    if data.get('contas'):
        print(f"\n🔍 PRIMEIRAS 5 CONTAS RETORNADAS PELA API:")
        print("=" * 80)
        
        for i, conta in enumerate(data['contas'][:5], 1):
            print(f"\n{i}. Conta ID: {conta.get('id')}")
            print(f"   Código: '{conta.get('codigo')}'")
            print(f"   Descrição: '{conta.get('descricao')}'")
            print(f"   Classificação: '{conta.get('classificacao')}'")
            print(f"   Tipo: '{conta.get('tipo_conta')}'")
            print(f"   Natureza: '{conta.get('natureza')}'")
        
        # Verificar se há corrupção
        primeira = data['contas'][0]
        if primeira.get('codigo') == 'codigo':
            print("\n" + "=" * 80)
            print("❌ PROBLEMA DETECTADO: API RETORNANDO STRINGS LITERAIS!")
            print("=" * 80)
            print("\n🔴 A API do Railway está retornando dados corruptos:")
            print("   - codigo = 'codigo' (deveria ser '1', '1.1', etc)")
            print("   - descricao = 'descricao' (deveria ser 'ATIVO', etc)")
            print("\n💡 CAUSA PROVÁVEL:")
            print("   - Railway não deployou a última versão do código")
            print("   - Ou há cache no Railway")
            print("\n🔧 SOLUÇÃO:")
            print("   1. Force um redeploy no Railway")
            print("   2. Limpe o cache do Railway")
            print("   3. Verifique se o commit foi deployado")
        else:
            print("\n" + "=" * 80)
            print("✅ API RETORNANDO DADOS CORRETOS!")
            print("=" * 80)
            print("\n💡 Se a interface ainda mostra erro:")
            print("   - Limpe o cache do navegador (Ctrl+Shift+Del)")
            print("   - Faça hard refresh (Ctrl+F5)")
            print("   - Tente em aba anônima")
    else:
        print("\n⚠️ Nenhuma conta retornada")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
