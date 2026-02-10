"""
Script para verificar se os métodos de regras_conciliacao foram carregados corretamente
"""
import requests
import json

BASE_URL = "https://sistemafinanceirodwm-production.up.railway.app"

print("\n" + "="*70)
print("VERIFICAÇÃO DE DEPLOY - MÉTODOS REGRAS_CONCILIACAO")
print("="*70 + "\n")

# 1. Verificar se servidor está online
print("1️⃣  Verificando se servidor está online...")
try:
    response = requests.head(BASE_URL, timeout=10)
    print(f"   ✅ Servidor online! Status: {response.status_code}\n")
except Exception as e:
    print(f"   ❌ Servidor offline: {e}\n")
    exit(1)

# 2. Verificar endpoint de debug
print("2️⃣  Verificando tabela regras_conciliacao...")
try:
    response = requests.get(f"{BASE_URL}/api/debug/verificar-tabela-regras", timeout=10)
    data = response.json()
    
    if data.get('success'):
        print(f"   ✅ Tabela existe: {data['data']['tabela_existe']}")
        print(f"   ✅ Query funciona: {data['data']['query_ok']}")
        print(f"   ✅ Total de regras: {data['data']['total_regras']}")
        print(f"   ✅ Colunas: {len(data['data']['colunas'])} encontradas\n")
    else:
        print(f"   ❌ Erro: {data.get('error')}\n")
except Exception as e:
    print(f"   ❌ Erro ao verificar tabela: {e}\n")

# 3. Informações para o usuário
print("="*70)
print("PRÓXIMOS PASSOS:")
print("="*70)
print()
print("✅ Se todas as verificações passaram, o deploy está correto!")
print()
print("🧪 TESTE FINAL:")
print("   1. Abra: https://sistemafinanceirodwm-production.up.railway.app")
print("   2. Faça login")
print("   3. Vá em: Financeiro → Extrato Bancário → Configurações")
print("   4. Clique em 'Nova Regra'")
print("   5. Preencha e salve")
print()
print("📋 LOGS ESPERADOS NO CONSOLE (F12):")
print("   🔍 [DEBUG] Iniciando criar_regra_conciliacao")
print("   🔍 [DEBUG] empresa_id: 20")
print("   🔍 [DEBUG] Dados recebidos: {...}")
print("   🔍 [DEBUG] Chamando db.criar_regra_conciliacao")
print("   ✅ [DEBUG] Regra criada: {...}")
print()
print("❌ Se ainda der erro 'has no attribute criar_regra_conciliacao':")
print("   Envie uma captura do erro completo do Railway!")
print()
print("="*70 + "\n")
