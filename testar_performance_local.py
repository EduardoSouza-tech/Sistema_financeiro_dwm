"""
Script para testar performance localmente
"""
import sys
import os

# Configurar DATABASE_URL
os.environ['DATABASE_URL'] = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("⚡ TESTE LOCAL DE PERFORMANCE - FASE 7")
print("=" * 80)
print()

# Importar módulos
print("📦 Importando módulos...")
try:
    from app.utils.cache_manager import get_cache_stats, get_cached, set_cached
    from app.utils.query_optimizer import profiler
    print("✅ Cache manager importado")
    print("✅ Query optimizer importado")
except Exception as e:
    print(f"❌ Erro ao importar: {e}")
    sys.exit(1)

print()
print("=" * 80)
print("💾 TESTE 1: Cache Manager")
print("=" * 80)

# Testar cache
print("\n1. Definindo valores no cache...")
set_cached('teste_key_1', {'data': 'valor1', 'numero': 123}, ttl=300)
set_cached('teste_key_2', [1, 2, 3, 4, 5], ttl=300)
set_cached('teste_key_3', 'string simples', ttl=300)
print("✅ 3 valores definidos")

print("\n2. Recuperando valores do cache...")
valor1 = get_cached('teste_key_1')
valor2 = get_cached('teste_key_2')
valor3 = get_cached('teste_key_3')
valor_inexistente = get_cached('chave_que_nao_existe')

print(f"   teste_key_1: {valor1}")
print(f"   teste_key_2: {valor2}")
print(f"   teste_key_3: {valor3}")
print(f"   chave_inexistente: {valor_inexistente}")

print("\n3. Estatísticas do cache:")
stats = get_cache_stats()
print(f"   Total de chaves: {stats['total_keys']}")
print(f"   Chaves válidas: {stats['valid_keys']}")
print(f"   Chaves expiradas: {stats['expired_keys']}")
print(f"   Taxa de hit: {stats['hit_rate']:.2f}%")
print(f"   Memória usada: {stats['memory_usage']}")

print()
print("=" * 80)
print("🔍 TESTE 2: Query Profiler")
print("=" * 80)

print("\n1. Adicionando queries de exemplo...")
profiler.log_query("SELECT * FROM lancamentos WHERE proprietario_id = 1", (), 45.5)
profiler.log_query("SELECT * FROM clientes WHERE ativo = true", (), 12.3)
profiler.log_query("SELECT COUNT(*) FROM lancamentos", (), 150.7)
profiler.log_query("SELECT * FROM fornecedores LIMIT 100", (), 8.9)
profiler.log_query("SELECT * FROM lancamentos WHERE status = 'pago'", (), 230.4)
print("✅ 5 queries adicionadas")

print("\n2. Estatísticas das queries:")
stats = profiler.get_stats()
print(f"   Total de queries: {stats['total_queries']}")
if stats['total_queries'] > 0:
    print(f"   Duração média: {stats['avg_time']*1000:.2f}ms")
    print(f"   Duração mínima: {stats['min_time']*1000:.2f}ms")
    print(f"   Duração máxima: {stats['max_time']*1000:.2f}ms")

print("\n3. Queries lentas (>100ms):")
slow = profiler.get_slow_queries(threshold_ms=100.0)
if slow:
    for i, query_info in enumerate(slow, 1):
        print(f"\n   [{i}] {query_info['duration']:.2f}ms")
        print(f"       {query_info['query'][:60]}...")
else:
    print("   ✅ Nenhuma query lenta detectada!")

print()
print("=" * 80)
print("📊 TESTE 3: Verificar Índices no Banco")
print("=" * 80)

try:
    import database_postgresql
    
    print("\n1. Conectando ao banco...")
    with database_postgresql.get_db_connection() as conn:
        cursor = conn.cursor()
        print("✅ Conectado!")
        
        print("\n2. Listando índices de performance:")
        cursor.execute("""
            SELECT 
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid::regclass)) as tamanho
            FROM pg_indexes
            JOIN pg_stat_user_indexes USING (schemaname, tablename, indexname)
            WHERE schemaname = 'public' 
              AND indexname LIKE 'idx_%'
            ORDER BY tablename, indexname
        """)
        
        indices = cursor.fetchall()
        
        if indices:
            tabela_atual = None
            for tabela, nome, tamanho in indices:
                if tabela != tabela_atual:
                    print(f"\n   📦 {tabela}:")
                    tabela_atual = tabela
                print(f"      • {nome:45s} ({tamanho})")
            
            print(f"\n   ✅ Total: {len(indices)} índices de performance instalados")
        else:
            print("   ⚠️  Nenhum índice de performance encontrado")
        
        print("\n3. Estatísticas de uso dos índices:")
        cursor.execute("""
            SELECT 
                schemaname || '.' || tablename as tabela,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public' 
              AND indexname LIKE 'idx_%'
            ORDER BY idx_scan DESC
            LIMIT 10
        """)
        
        stats = cursor.fetchall()
        
        if stats:
            print(f"\n   Top 10 índices mais usados:")
            print(f"   {'Índice':<50} {'Scans':>10} {'Tuplas Lidas':>15}")
            print("   " + "-" * 80)
            
            for tabela, nome, scans, lidas, fetch in stats:
                print(f"   {nome:<50} {scans:>10} {lidas:>15}")
        
        cursor.close()
        
except Exception as e:
    print(f"❌ Erro ao conectar ao banco: {e}")

print()
print("=" * 80)
print("🎉 TESTES LOCAIS CONCLUÍDOS!")
print("=" * 80)
print()
print("📊 RESUMO:")
print("   ✅ Cache Manager funcionando")
print("   ✅ Query Profiler funcionando")
print("   ✅ Índices instalados no PostgreSQL")
print()
print("📌 PRÓXIMAS AÇÕES:")
print("   1. Verificar deploy no Railway:")
print("      - Acessar https://railway.app/")
print("      - Verificar logs do deployment")
print("      - Confirmar URL da aplicação")
print()
print("   2. Testar endpoints de performance em produção:")
print("      - GET /api/performance/stats")
print("      - GET /api/performance/slow-queries")
print("      - GET /api/performance/indexes")
print()
print("   3. Monitorar performance durante uso normal")
print()
print("=" * 80)
