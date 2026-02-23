"""
Script para corrigir cliente_id NULL nos contratos do Railway
Conecta diretamente ao PostgreSQL do Railway
"""
import os
import sys
import psycopg2
from urllib.parse import urlparse

def log(msg):
    print(msg, flush=True)

def connect_railway():
    """Conecta ao PostgreSQL do Railway"""
    # Tentar obter URL das variáveis de ambiente primeiro
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        log("⚠️ DATABASE_URL não encontrada nas variáveis de ambiente")
        log("📋 Por favor, forneça a URL de conexão do Railway:")
        log("   Formato: postgresql://user:password@host:port/database")
        log("")
        
        # Tentar URLs conhecidas
        urls_tentativas = [
            "postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway",
        ]
        
        for idx, url in enumerate(urls_tentativas, 1):
            log(f"\n🔄 Tentativa {idx}: Testando conexão...")
            try:
                # Configurações de conexão mais robustas
                conn = psycopg2.connect(
                    url,
                    connect_timeout=10,
                    options='-c statement_timeout=30000'
                )
                log(f"✅ Conectado com sucesso!")
                return conn
            except psycopg2.OperationalError as e:
                log(f"❌ Falhou: {str(e)[:100]}")
                continue
            except Exception as e:
                log(f"❌ Erro inesperado: {str(e)[:100]}")
                continue
        
        log("\n❌ Não foi possível conectar automaticamente")
        log("\n💡 Solução alternativa:")
        log("   1. Acesse Railway Dashboard")
        log("   2. PostgreSQL → Connect → Copy Database URL")
        log("   3. Execute o SQL manualmente na interface do Railway")
        sys.exit(1)
    else:
        log(f"🔗 Conectando ao Railway usando DATABASE_URL...")
        conn = psycopg2.connect(
            DATABASE_URL,
            connect_timeout=10,
            options='-c statement_timeout=30000'
        )
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
        
        # Mostrar detalhes dos contratos
        log("\n📋 DETALHES DOS CONTRATOS:")
        cur.execute("""
            SELECT 
                c.id,
                c.numero,
                c.cliente_id
            FROM contratos c
            ORDER BY c.id
        """)
        contratos = cur.fetchall()
        for contrato in contratos:
            log(f"\n   📋 Contrato ID {contrato[0]} - {contrato[1]}")
            log(f"      Cliente ID: {contrato[2]}")
        
        # Mostrar clientes
        log("\n👥 CLIENTES:")
        cur.execute("""
            SELECT id, nome FROM clientes ORDER BY id
        """)
        clientes = cur.fetchall()
        for cliente in clientes:
            log(f"   Cliente ID {cliente[0]}: {cliente[1]}")
        
        # Mostrar sessões por contrato (simplificado)
        log("\n📸 SESSÕES:")
        cur.execute("""
            SELECT 
                s.id,
                s.contrato_id,
                s.cliente_id
            FROM sessoes s
            ORDER BY s.contrato_id, s.id
        """)
        sessoes = cur.fetchall()
        
        contrato_clientes = {}
        for sessao in sessoes:
            log(f"   Sessão {sessao[0]}: Contrato {sessao[1]}, Cliente {sessao[2]}")
            
            # Agrupar por contrato
            if sessao[1] not in contrato_clientes:
                contrato_clientes[sessao[1]] = set()
            contrato_clientes[sessao[1]].add(sessao[2])
        
        # Verificar incompatibilidades
        log("\n⚠️ VERIFICANDO INCOMPATIBILIDADES:")
        for contrato in contratos:
            contrato_id = contrato[0]
            cliente_id_contrato = contrato[2]
            
            if contrato_id in contrato_clientes:
                clientes_sessoes = contrato_clientes[contrato_id]
                
                if len(clientes_sessoes) > 1:
                    log(f"\n   ❌ Contrato {contrato[1]} tem sessões de múltiplos clientes!")
                    log(f"      Cliente do contrato: {cliente_id_contrato}")
                    log(f"      Clientes nas sessões: {clientes_sessoes}")
                elif cliente_id_contrato not in clientes_sessoes:
                    log(f"\n   ⚠️ Contrato {contrato[1]}")
                    log(f"      Cliente do contrato: {cliente_id_contrato}")
                    log(f"      Cliente nas sessões: {clientes_sessoes}")
                    log(f"      RECOMENDAÇÃO: Corrigir contrato para ter cliente_id = {list(clientes_sessoes)[0]}")
                else:
                    log(f"\n   ✅ Contrato {contrato[1]} - OK")
        
        cur.close()
        conn.close()
        
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
