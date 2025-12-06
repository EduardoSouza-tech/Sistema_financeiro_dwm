import requests

print('\n=== Testando API de Clientes ===')
try:
    response = requests.get('http://127.0.0.1:5000/api/clientes', timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        clientes = response.json()
        print(f"Total de clientes: {len(clientes)}")
        if clientes:
            print(f"\nPrimeiro cliente:")
            import json
            print(json.dumps(clientes[0], indent=2, ensure_ascii=False))
    else:
        print(f"Erro: {response.text}")
except Exception as e:
    print(f"Erro ao conectar: {e}")
    print("O servidor Flask está rodando?")

print('\n=== Testando API de Fornecedores ===')
try:
    response = requests.get('http://127.0.0.1:5000/api/fornecedores', timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        fornecedores = response.json()
        print(f"Total de fornecedores: {len(fornecedores)}")
        if fornecedores:
            print(f"\nPrimeiro fornecedor:")
            import json
            print(json.dumps(fornecedores[0], indent=2, ensure_ascii=False))
    else:
        print(f"Erro: {response.text}")
except Exception as e:
    print(f"Erro ao conectar: {e}")
