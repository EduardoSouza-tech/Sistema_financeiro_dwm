"""
Script rápido: Executa SQL para adicionar permissões via DatabaseManager
"""
import sys
import os

# Adicionar path
sys.path.insert(0, os.path.dirname(__file__))

from database_postgresql import DatabaseManager

print("=" * 80)
print("🔑 ADICIONANDO PERMISSÕES VIA DATABASE MANAGER")
print("=" * 80)

try:
    db = DatabaseManager()
    
    # SQL para adicionar permissões
    sql = """
    INSERT INTO usuarios_permissoes (usuario_id, permissao_id)
    SELECT u.id, p.id
    FROM usuarios u
    CROSS JOIN permissoes p
    WHERE u.ativo = TRUE
      AND p.codigo IN ('regras_conciliacao_view', 'regras_conciliacao_create', 'regras_conciliacao_edit', 'regras_conciliacao_delete')
    ON CONFLICT (usuario_id, permissao_id) DO NOTHING;
    """
    
    print("\n📝 Executando SQL...")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute(sql)
    rows_affected = cursor.rowcount
    conn.commit()
    
    print(f"✅ {rows_affected} permissão(ões) adicionada(s)")
    
    # Verificar
    cursor.execute("""
        SELECT COUNT(DISTINCT u.id) as qtd_usuarios, COUNT(*) as qtd_permissoes
        FROM usuarios_permissoes up
        JOIN usuarios u ON u.id = up.usuario_id
        JOIN permissoes p ON p.id = up.permissao_id
        WHERE p.codigo LIKE 'regras_conciliacao_%'
    """)
    
    result = cursor.fetchone()
    print(f"✅ {result[0]} usuário(s) com {result[1]} permissão(ões) de regras")
    
    cursor.close()
    
    print("\n" + "=" * 80)
    print("✅ PERMISSÕES CONFIGURADAS!")
    print("=" * 80)
    print("\n💡 Faça logout e login para atualizar as permissões")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
