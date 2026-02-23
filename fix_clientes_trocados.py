"""
Script para CORRIGIR clientes trocados nos contratos
"""
import psycopg2

def log(msg):
    print(msg, flush=True)

def fix_contratos():
    try:
        DATABASE_URL = "postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway"
        
        log("🔗 Conectando ao Railway...")
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        log("✅ Conectado!")
        
        cur = conn.cursor()
        
        log("\n" + "="*80)
        log("🔧 CORRIGINDO CLIENTES DOS CONTRATOS")
        log("="*80)
        
        # ANTES
        log("\n📊 SITUAÇÃO ANTES:")
        cur.execute("""
            SELECT c.id, c.numero, c.cliente_id, cl.nome
            FROM contratos c
            LEFT JOIN clientes cl ON cl.id = c.cliente_id
            WHERE c.id IN (31, 32)
            ORDER BY c.id
        """)
        for row in cur.fetchall():
            log(f"   {row[1]}: Cliente {row[2]} ({row[3]})")
        
        # CORRIGIR
        log("\n🔄 Aplicando correções...")
        cur.execute("UPDATE contratos SET cliente_id = 44 WHERE id = 31")
        log(f"   ✅ CONT-2026-0004 → Cliente 44 (VILA GLOW)")
        
        cur.execute("UPDATE contratos SET cliente_id = 64 WHERE id = 32")
        log(f"   ✅ CONT-2026-0005 → Cliente 64 (CAVALLERI)")
        
        conn.commit()
        log("\n💾 Alterações salvas!")
        
        # DEPOIS
        log("\n📊 SITUAÇÃO DEPOIS:")
        cur.execute("""
            SELECT c.id, c.numero, c.cliente_id, cl.nome
            FROM contratos c
            LEFT JOIN clientes cl ON cl.id = c.cliente_id
            WHERE c.id IN (31, 32)
            ORDER BY c.id
        """)
        for row in cur.fetchall():
            log(f"   {row[1]}: Cliente {row[2]} ({row[3]})")
        
        # VERIFICAR ALINHAMENTO COM SESSÕES
        log("\n✅ VERIFICANDO ALINHAMENTO COM SESSÕES:")
        cur.execute("""
            SELECT 
                c.numero,
                c.cliente_id as contrato_cliente,
                s.cliente_id as sessao_cliente,
                CASE WHEN c.cliente_id = s.cliente_id THEN 'OK' ELSE 'ERRO' END as status
            FROM contratos c
            JOIN sessoes s ON s.contrato_id = c.id
            WHERE c.id IN (31, 32)
        """)
        for row in cur.fetchall():
            status_icon = "✅" if row[3] == "OK" else "❌"
            log(f"   {status_icon} {row[0]}: Contrato={row[1]}, Sessão={row[2]} → {row[3]}")
        
        log("\n" + "="*80)
        log("✅ CORREÇÃO CONCLUÍDA!")
        log("="*80)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        log(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_contratos()
