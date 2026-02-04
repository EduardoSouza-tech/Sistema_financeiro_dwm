"""
Script para corrigir margens dos eventos via conexão direta ao Railway
"""
import psycopg2

# Credenciais Railway
RAILWAY_CONFIG = {
    'host': 'centerbeam.proxy.rlwy.net',
    'port': 12659,
    'user': 'postgres',
    'password': 'JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT',
    'database': 'railway'
}

try:
    print("🔌 Conectando ao Railway PostgreSQL...")
    conn = psycopg2.connect(**RAILWAY_CONFIG)
    cursor = conn.cursor()
    print("✅ Conexão estabelecida!\n")
    
    # Primeiro, mostrar eventos com margem incorreta
    print("📊 Verificando eventos com margem incorreta...")
    cursor.execute("""
        SELECT 
            id,
            nome_evento,
            COALESCE(valor_liquido_nf, 0) as valor_liquido,
            COALESCE(custo_evento, 0) as custo,
            COALESCE(margem, 0) as margem_atual,
            (COALESCE(valor_liquido_nf, 0) - COALESCE(custo_evento, 0)) as margem_correta
        FROM eventos
        WHERE ABS(COALESCE(margem, 0) - (COALESCE(valor_liquido_nf, 0) - COALESCE(custo_evento, 0))) > 0.01
        ORDER BY id
    """)
    
    eventos_incorretos = cursor.fetchall()
    
    if not eventos_incorretos:
        print("✅ Todas as margens já estão corretas!")
    else:
        print(f"\n⚠️  Encontrados {len(eventos_incorretos)} evento(s) com margem incorreta:\n")
        
        for evento in eventos_incorretos:
            evt_id, nome, valor_liq, custo, margem_atual, margem_correta = evento
            print(f"🎉 Evento #{evt_id}: {nome}")
            print(f"   Valor Líquido: R$ {valor_liq:,.2f}")
            print(f"   Custo: R$ {custo:,.2f}")
            print(f"   ❌ Margem Atual: R$ {margem_atual:,.2f}")
            print(f"   ✅ Margem Correta: R$ {margem_correta:,.2f}")
            print(f"   📉 Diferença: R$ {margem_atual - margem_correta:,.2f}\n")
        
        # Atualizar margens
        print("🔧 Atualizando margens...")
        cursor.execute("""
            UPDATE eventos
            SET margem = (COALESCE(valor_liquido_nf, 0) - COALESCE(custo_evento, 0))
            WHERE ABS(COALESCE(margem, 0) - (COALESCE(valor_liquido_nf, 0) - COALESCE(custo_evento, 0))) > 0.01
        """)
        
        linhas_atualizadas = cursor.rowcount
        conn.commit()
        
        print(f"✅ {linhas_atualizadas} margem(ns) atualizada(s) com sucesso!\n")
        
        # Verificar resultado
        print("📊 Verificando resultado final...")
        cursor.execute("""
            SELECT 
                id,
                nome_evento,
                COALESCE(valor_liquido_nf, 0) as valor_liquido,
                COALESCE(custo_evento, 0) as custo,
                COALESCE(margem, 0) as margem
            FROM eventos
            ORDER BY id
        """)
        
        todos_eventos = cursor.fetchall()
        print(f"\n✅ Todos os eventos ({len(todos_eventos)}):\n")
        
        for evento in todos_eventos:
            evt_id, nome, valor_liq, custo, margem = evento
            print(f"🎉 #{evt_id}: {nome}")
            print(f"   💰 Valor: R$ {valor_liq:,.2f} | Custo: R$ {custo:,.2f} | Margem: R$ {margem:,.2f}\n")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*70)
    print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
