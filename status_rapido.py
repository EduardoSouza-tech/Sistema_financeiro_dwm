"""Verificação direta e rápida - sem inicialização do DB"""
import psycopg2

DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("\n🔍 VERIFICANDO STATUS DA MIGRAÇÃO...")
print("="*60)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Contar lançamentos criados
    cursor.execute("SELECT COUNT(*) FROM conciliacoes")
    criados = cursor.fetchone()[0]
    
    # Contar ainda pendentes
    cursor.execute("""
        SELECT COUNT(*) 
        FROM transacoes_extrato te
        LEFT JOIN conciliacoes c ON c.transacao_extrato_id = te.id
        WHERE te.conciliado = TRUE AND c.lancamento_id IS NULL
    """)
    pendentes = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    total = 694
    progresso = (criados / total) * 100
    
    print(f"✅ Lançamentos criados: {criados}/{total} ({progresso:.1f}%)")
    print(f"❌ Ainda pendentes: {pendentes}")
    print()
    
    if pendentes == 0:
        print("🎉 MIGRAÇÃO COMPLETA!")
        print("Todos os lançamentos foram criados com sucesso.")
    else:
        tempo_estimado = pendentes * 2
        print(f"⏱️  Tempo estimado para completar: ~{tempo_estimado//60}min {tempo_estimado%60}s")
        print(f"📝 Execute novamente o script de migração para continuar")
    
    print("="*60 + "\n")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
