"""
Script para testar os endpoints de performance da API
Fase 7 - Performance Testing
"""
import requests
import json
import time
from datetime import datetime

# URL base da API
BASE_URL = "https://sistema-financeiro-dwm-production.up.railway.app"

def fazer_login():
    """Faz login e retorna o token JWT"""
    print("🔐 Fazendo login...")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": "admin@dwm.com",
            "senha": "admin123"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"✅ Login bem-sucedido! Token: {token[:20]}...")
        return token
    else:
        print(f"❌ Erro no login: {response.status_code}")
        print(response.text)
        return None

def testar_endpoint(url, token, metodo="GET", dados=None):
    """Testa um endpoint e retorna tempo de resposta e dados"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    inicio = time.time()
    
    try:
        if metodo == "GET":
            response = requests.get(url, headers=headers)
        elif metodo == "POST":
            response = requests.post(url, headers=headers, json=dados)
        else:
            print(f"❌ Método {metodo} não suportado")
            return None, None
        
        tempo = (time.time() - inicio) * 1000  # Converter para ms
        
        return response, tempo
    
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None, None

def formatar_json(data):
    """Formata JSON para exibição"""
    return json.dumps(data, indent=2, ensure_ascii=False)

def main():
    print("=" * 80)
    print("⚡ TESTE DE PERFORMANCE - FASE 7")
    print("=" * 80)
    print()
    
    # Login
    token = fazer_login()
    if not token:
        print("❌ Não foi possível fazer login. Encerrando.")
        return
    
    print()
    print("=" * 80)
    print("📊 TESTE 1: Performance Stats")
    print("=" * 80)
    
    response, tempo = testar_endpoint(f"{BASE_URL}/api/performance/stats", token)
    
    if response and response.status_code == 200:
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Tempo de resposta: {tempo:.2f}ms")
        print(f"\n📋 Dados retornados:")
        data = response.json()
        
        # Cache stats
        if 'cache' in data:
            cache = data['cache']
            print(f"\n💾 CACHE:")
            print(f"   Total de chaves: {cache.get('total_keys', 0)}")
            print(f"   Chaves válidas: {cache.get('valid_keys', 0)}")
            print(f"   Chaves expiradas: {cache.get('expired_keys', 0)}")
            print(f"   Taxa de hit: {cache.get('hit_rate', 0):.2f}%")
            print(f"   Memória usada: {cache.get('memory_usage', 'N/A')}")
        
        # Query stats
        if 'queries' in data:
            queries = data['queries']
            print(f"\n🔍 QUERIES:")
            print(f"   Total executadas: {queries.get('total_queries', 0)}")
            print(f"   Tempo médio: {queries.get('avg_duration', 0):.2f}ms")
            print(f"   Tempo mínimo: {queries.get('min_duration', 0):.2f}ms")
            print(f"   Tempo máximo: {queries.get('max_duration', 0):.2f}ms")
            print(f"   Queries lentas (>100ms): {queries.get('slow_queries_count', 0)}")
    else:
        print(f"❌ Erro: {response.status_code if response else 'Sem resposta'}")
        if response:
            print(response.text)
    
    print()
    print("=" * 80)
    print("🐌 TESTE 2: Slow Queries")
    print("=" * 80)
    
    response, tempo = testar_endpoint(f"{BASE_URL}/api/performance/slow-queries", token)
    
    if response and response.status_code == 200:
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Tempo de resposta: {tempo:.2f}ms")
        
        data = response.json()
        slow_queries = data.get('slow_queries', [])
        
        if slow_queries:
            print(f"\n⚠️  {len(slow_queries)} queries lentas detectadas:")
            for i, query in enumerate(slow_queries[:5], 1):  # Mostrar top 5
                print(f"\n   [{i}] Duração: {query.get('duration', 0):.2f}ms")
                print(f"       Query: {query.get('query', 'N/A')[:80]}...")
                print(f"       Timestamp: {query.get('timestamp', 'N/A')}")
        else:
            print("\n✅ Nenhuma query lenta detectada!")
    else:
        print(f"❌ Erro: {response.status_code if response else 'Sem resposta'}")
    
    print()
    print("=" * 80)
    print("📈 TESTE 3: Index Suggestions")
    print("=" * 80)
    
    response, tempo = testar_endpoint(f"{BASE_URL}/api/performance/indexes", token)
    
    if response and response.status_code == 200:
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Tempo de resposta: {tempo:.2f}ms")
        
        data = response.json()
        suggestions = data.get('suggestions', [])
        
        if suggestions:
            print(f"\n💡 {len(suggestions)} sugestões de índices:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"\n   [{i}] Tabela: {suggestion.get('table', 'N/A')}")
                print(f"       Colunas: {', '.join(suggestion.get('columns', []))}")
                print(f"       Benefício estimado: {suggestion.get('benefit', 'N/A')}")
                print(f"       Uso: {suggestion.get('usage', 'N/A')}")
    else:
        print(f"❌ Erro: {response.status_code if response else 'Sem resposta'}")
    
    print()
    print("=" * 80)
    print("⚡ TESTE 4: Benchmark de Endpoints Principais")
    print("=" * 80)
    
    endpoints_teste = [
        ("Dashboard", "/api/relatorios/dashboard-completo"),
        ("Lançamentos", "/api/lancamentos"),
        ("Clientes", "/api/clientes"),
        ("Fornecedores", "/api/fornecedores"),
        ("Contratos", "/api/contratos")
    ]
    
    resultados = []
    
    for nome, endpoint in endpoints_teste:
        print(f"\n📊 Testando {nome}...", end=" ")
        response, tempo = testar_endpoint(f"{BASE_URL}{endpoint}", token)
        
        if response and response.status_code == 200:
            status = "✅" if tempo < 200 else "⚠️" if tempo < 500 else "❌"
            print(f"{status} {tempo:.2f}ms")
            resultados.append({
                'nome': nome,
                'tempo': tempo,
                'status': 'OK' if tempo < 200 else 'LENTO' if tempo < 500 else 'CRÍTICO'
            })
        else:
            print(f"❌ Erro {response.status_code if response else 'N/A'}")
    
    print()
    print("=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)
    
    if resultados:
        print("\n⏱️  Tempos de Resposta:")
        print(f"{'Endpoint':<20} {'Tempo':<15} {'Status':<10}")
        print("-" * 45)
        
        for r in resultados:
            print(f"{r['nome']:<20} {r['tempo']:>8.2f}ms     {r['status']:<10}")
        
        tempos = [r['tempo'] for r in resultados]
        print()
        print(f"📈 Estatísticas:")
        print(f"   Média: {sum(tempos)/len(tempos):.2f}ms")
        print(f"   Mínimo: {min(tempos):.2f}ms")
        print(f"   Máximo: {max(tempos):.2f}ms")
        
        # Verificar meta de <200ms (p95)
        abaixo_200 = len([t for t in tempos if t < 200])
        percentual = (abaixo_200 / len(tempos)) * 100
        
        print()
        print(f"🎯 Meta de Performance (<200ms):")
        print(f"   {abaixo_200}/{len(tempos)} endpoints ({percentual:.1f}%)")
        
        if percentual >= 95:
            print(f"   ✅ META ATINGIDA! (>95%)")
        elif percentual >= 80:
            print(f"   ⚠️  Próximo da meta (80-95%)")
        else:
            print(f"   ❌ Abaixo da meta (<80%)")
    
    print()
    print("=" * 80)
    print("🎉 TESTES CONCLUÍDOS!")
    print("=" * 80)
    print()
    print("📌 Próximas ações:")
    print("   1. ✅ Índices aplicados")
    print("   2. ✅ Cache implementado")
    print("   3. ✅ Monitoramento ativo")
    print("   4. 🔄 Continuar monitorando em produção")
    print("   5. 🚀 Implementar lazy loading frontend (Fase 7.5)")
    print()

if __name__ == "__main__":
    main()
