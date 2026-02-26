"""
Testa o endpoint /api/extratos diretamente
"""

import requests
import json

# URL do endpoint
BASE_URL = "https://sistemafinanceirodwm-production.up.railway.app"
ENDPOINT = "/api/extratos"

# Parâmetros de teste
params = {
    'data_inicio': '2026-01-01',
    'data_fim': '2026-01-31'
}

print("="*80)
print("TESTE DO ENDPOINT /api/extratos")
print("="*80)

print(f"\n🔍 URL: {BASE_URL}{ENDPOINT}")
print(f"📋 Parâmetros: {params}")

try:
    # Fazer requisição
    response = requests.get(
        f"{BASE_URL}{ENDPOINT}",
        params=params,
        # Cookies de sessão se necessário
        headers={
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        },
        timeout=10
    )
    
    print(f"\n📡 Status Code: {response.status_code}")
    print(f"📦 Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Response JSON:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        if 'transacoes' in data:
            print(f"\n📊 Total de transações: {len(data.get('transacoes', []))}")
            print(f"💰 Saldo anterior: {data.get('saldo_anterior', 'N/A')}")
        else:
            print(f"\n⚠️ Formato inesperado: {list(data.keys())}")
    else:
        print(f"\n❌ Erro HTTP {response.status_code}")
        print(f"📄 Response Text:\n{response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ Erro na requisição: {e}")
    
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
