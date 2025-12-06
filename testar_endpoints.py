"""Script para testar endpoints do sistema financeiro"""
import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:5000"

def testar_endpoint(nome, url):
    """Testa um endpoint específico"""
    print(f"\n{'='*60}")
    print(f"Testando: {nome}")
    print(f"URL: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Tipo de resposta: {type(data)}")
            
            if isinstance(data, list):
                print(f"Total de itens: {len(data)}")
                if len(data) > 0:
                    print(f"\nPrimeiro item:")
                    print(json.dumps(data[0], indent=2, ensure_ascii=False))
            elif isinstance(data, dict):
                print(f"Chaves: {list(data.keys())}")
                print(f"\nDados:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"Erro: {response.text}")
            
    except Exception as e:
        print(f"ERRO: {str(e)}")

# Calcular datas
hoje = date.today()
trinta_dias_atras = hoje - timedelta(days=30)

# Testar endpoints
print("\n" + "="*60)
print("TESTE DE ENDPOINTS - SISTEMA FINANCEIRO")
print("="*60)

endpoints = [
    ("Fluxo de Caixa", f"{BASE_URL}/api/relatorios/fluxo-caixa?data_inicio={trinta_dias_atras}&data_fim={hoje}"),
    ("Fluxo Projetado", f"{BASE_URL}/api/relatorios/fluxo-projetado?dias=30"),
    ("Dashboard", f"{BASE_URL}/api/relatorios/dashboard"),
    ("Resumo Parceiros", f"{BASE_URL}/api/relatorios/resumo-parceiros?data_inicio={trinta_dias_atras}&data_fim={hoje}"),
    ("Análise Categorias", f"{BASE_URL}/api/relatorios/analise-categorias?data_inicio={trinta_dias_atras}&data_fim={hoje}"),
    ("Indicadores", f"{BASE_URL}/api/relatorios/indicadores"),
    ("Inadimplência", f"{BASE_URL}/api/relatorios/inadimplencia"),
]

for nome, url in endpoints:
    testar_endpoint(nome, url)

print("\n" + "="*60)
print("TESTE CONCLUÍDO")
print("="*60)
