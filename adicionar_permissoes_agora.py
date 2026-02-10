"""
Script rápido: Adiciona permissões de regras_conciliacao diretamente
"""
import psycopg2

# URL do Railway
DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("🔑 ADICIONANDO PERMISSÕES DE REGRAS DE CONCILIAÇÃO")
print("=" * 80)

try:
    print("\n📡 Conectando ao banco...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    print("✅ Conectado!")
    
    # SQL para adicionar permissões
    sql = """
    INSERT INTO usuario_permissoes (usuario_id, permissao_id)
    SELECT u.id, p.id
    FROM usuarios u
    CROSS JOIN permissoes p
    WHERE u.ativo = TRUE
      AND p.codigo IN ('regras_conciliacao_view', 'regras_conciliacao_create', 'regras_conciliacao_edit', 'regras_conciliacao_delete')
    ON CONFLICT (usuario_id, permissao_id) DO NOTHING
    RETURNING usuario_id, permissao_id;
    """
    
    print("\n📝 Executando SQL...")
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.commit()
    
    print(f"✅ {len(rows)} nova(s) permissão(ões) adicionada(s)")
    
    # Verificar total
    print("\n📊 Verificando totais...")
    cursor.execute("""
        SELECT 
            u.nome_completo,
            COUNT(p.id) as qtd_permissoes
        FROM usuario_permissoes up
        JOIN usuarios u ON u.id = up.usuario_id
        JOIN permissoes p ON p.id = up.permissao_id
        WHERE p.codigo LIKE 'regras_conciliacao_%'
        GROUP BY u.id, u.nome_completo
        ORDER BY u.nome_completo
    """)
    
    usuarios = cursor.fetchall()
    
    if usuarios:
        print(f"\n✅ {len(usuarios)} usuário(s) com permissões de regras:")
        for user in usuarios:
            print(f"   - {user[0]}: {user[1]} permissão(ões)")
    else:
        print("\n⚠️ Nenhum usuário com permissões de regras!")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ PERMISSÕES CONFIGURADAS COM SUCESSO!")
    print("=" * 80)
    print("\n💡 IMPORTANTE: Faça logout e login novamente para atualizar")
    print("   as permissões na sessão do usuário!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
