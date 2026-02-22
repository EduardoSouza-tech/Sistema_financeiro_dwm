"""
Script para corrigir cliente_id NULL nos contratos do Railway
Conecta diretamente ao PostgreSQL do Railway
"""
import os
import psycopg2
from urllib.parse import urlparse

def log(msg):
    print(msg, flush=True)

def connect_railway():
    """Conecta ao PostgreSQL do Railway"""
    # URL do Railway (substitua pela sua)
    DATABASE_URL = "postgresql://postgres:ASTMobXdYFHDZDFqcXlCmWdSXiSGsAWp@junction.proxy.rlwy.net:47187/railway"
    
    log(f"🔗 Conectando ao Railway...")
    conn = psycopg2.connect(DATABASE_URL)
    log(f"✅ Conectado com sucesso!")
    return conn

def fix_contratos():
    """Corrige os contratos com cliente_id NULL"""
    try:
        conn = connect_railway()
        cur = conn.cursor()
        
        log("\n" + "="*80)
        log("🔧 INICIANDO CORREÇÃO DE CLIENTE_ID")
        log("="*80)
        
        # 1. Verificar situação atual
        log("\n📊 SITUAÇÃO ATUAL:")
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(cliente_id) as com_cliente,
                COUNT(*) - COUNT(cliente_id) as sem_cliente
            FROM contratos
        """)
        stats = cur.fetchone()
        log(f"   Total de contratos: {stats[0]}")
        log(f"   Com cliente_id: {stats[1]}")
        log(f"   Sem cliente_id (NULL): {stats[2]} ⚠️")
        
        if stats[2] == 0:
            log("\n✅ Todos os contratos já têm cliente_id!")
            return
        
        # 2. Corrigir baseado nas sessões
        log("\n🔄 Corrigindo contratos baseado nas sessões...")
        cur.execute("""
            UPDATE contratos c
            SET cliente_id = s.cliente_id
            FROM (
                SELECT DISTINCT ON (contrato_id) 
                    contrato_id, 
                    cliente_id
                FROM sessoes
                WHERE cliente_id IS NOT NULL
            ) s
            WHERE c.id = s.contrato_id
              AND c.cliente_id IS NULL
        """)
        corrigidos_sessao = cur.rowcount
        log(f"   ✅ {corrigidos_sessao} contratos corrigidos via sessões")
        
        # 3. Corrigir baseado no nome do cliente
        log("\n🔍 Corrigindo contratos baseado no cliente_nome...")
        cur.execute("""
            UPDATE contratos c
            SET cliente_id = cl.id
            FROM clientes cl
            WHERE c.cliente_id IS NULL
              AND c.cliente_nome IS NOT NULL
              AND cl.razao_social ILIKE c.cliente_nome
        """)
        corrigidos_nome = cur.rowcount
        log(f"   ✅ {corrigidos_nome} contratos corrigidos via nome")
        
        # 4. Commit
        conn.commit()
        log("\n💾 Alterações salvas no banco!")
        
        # 5. Verificar resultado final
        log("\n📊 SITUAÇÃO FINAL:")
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(cliente_id) as com_cliente,
                COUNT(*) - COUNT(cliente_id) as sem_cliente
            FROM contratos
        """)
        stats = cur.fetchone()
        log(f"   Total de contratos: {stats[0]}")
        log(f"   Com cliente_id: {stats[1]} ✅")
        log(f"   Sem cliente_id (NULL): {stats[2]}")
        
        # 6. Mostrar contratos que não puderam ser corrigidos
        if stats[2] > 0:
            log(f"\n⚠️ CONTRATOS QUE PRECISAM DE ATENÇÃO MANUAL:")
            cur.execute("""
                SELECT id, numero, nome, cliente_nome
                FROM contratos
                WHERE cliente_id IS NULL
                ORDER BY id
            """)
            for row in cur.fetchall():
                log(f"   📋 ID {row[0]} - {row[1]} - {row[2]}")
                log(f"      Cliente Nome: {row[3]}")
        
        log("\n" + "="*80)
        log("✅ CORREÇÃO CONCLUÍDA!")
        log(f"   Total corrigido: {corrigidos_sessao + corrigidos_nome}")
        log("="*80)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        log(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_contratos()
