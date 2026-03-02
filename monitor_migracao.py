"""Monitor de progresso da migração em tempo real"""
import os
import sys
import time

os.environ['DATABASE_URL'] = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

from database_postgresql import DatabaseManager

print("🔄 MONITORANDO MIGRAÇÃO EM TEMPO REAL...")
print("="*60)

db = DatabaseManager()
transacoes_total = 694
anterior = 0

while True:
    try:
        with db.get_db_connection(allow_global=True) as conn:
            cursor = conn.cursor()
            
            # Contar lançamentos criados
            cursor.execute("""
                SELECT COUNT(*) 
                FROM conciliacoes
            """)
            criados = cursor.fetchone()[0]
            
            # Contar pendentes
            cursor.execute("""
                SELECT COUNT(*) 
                FROM transacoes_extrato te
                LEFT JOIN conciliacoes c ON c.transacao_extrato_id = te.id
                WHERE te.conciliado = TRUE AND c.lancamento_id IS NULL
            """)
            pendentes = cursor.fetchone()[0]
            
            cursor.close()
        
        if criados != anterior:
            progresso = (criados / transacoes_total) * 100
            restantes = pendentes
            tempo_estimado = restantes * 2  # ~2 segundos por lançamento
            
            print(f"\r✅ Criados: {criados}/{transacoes_total} ({progresso:.1f}%) | "
                  f"❌ Pendentes: {restantes} | "
                  f"⏱️  Tempo estimado: {tempo_estimado//60}min {tempo_estimado%60}s", 
                  end='', flush=True)
            
            anterior = criados
            
            if restantes == 0:
                print("\n\n🎉 MIGRAÇÃO COMPLETA!")
                print(f"✅ {criados} lançamentos criados com sucesso")
                break
        
        time.sleep(3)  # Atualizar a cada 3 segundos
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Monitoramento interrompido pelo usuário")
        print(f"📊 Último status: {criados}/{transacoes_total} criados")
        break
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        time.sleep(5)
