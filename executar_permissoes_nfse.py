"""
Script: Adiciona permissões de NFS-e (Notas Fiscais de Serviço Eletrônica) no banco de dados
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL') or 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("📄 ADICIONANDO PERMISSÕES NFS-e")
print("=" * 80)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # 1. Criar permissões NFS-e na tabela permissoes
    print("\n1️⃣ Criando permissões NFS-e...")
    
    sql_permissoes = """
    INSERT INTO permissoes (codigo, nome, descricao, categoria)
    VALUES 
        ('nfse_view', 'Visualizar NFS-e', 'Permite visualizar notas fiscais de serviço eletrônicas', 'NFS-e'),
        ('nfse_buscar', 'Buscar NFS-e via API', 'Permite buscar NFS-e via API SOAP das prefeituras', 'NFS-e'),
        ('nfse_config', 'Configurar Municípios NFS-e', 'Permite configurar municípios para busca de NFS-e', 'NFS-e'),
        ('nfse_export', 'Exportar NFS-e', 'Permite exportar NFS-e para Excel/CSV e XMLs', 'NFS-e'),
        ('nfse_delete', 'Excluir NFS-e', 'Permite excluir notas fiscais de serviço', 'NFS-e')
    ON CONFLICT (codigo) DO NOTHING;
    """
    
    cursor.execute(sql_permissoes)
    rows_permissoes = cursor.rowcount
    conn.commit()
    print(f"   ✅ {rows_permissoes} permissão(ões) criada(s)")

    # 2. Atribuir permissões NFS-e para todos os usuários ativos
    print("\n2️⃣ Atribuindo permissões aos usuários ativos...")
    
    sql_usuarios = """
    INSERT INTO usuario_permissoes (usuario_id, permissao_id)
    SELECT u.id, p.id
    FROM usuarios u
    CROSS JOIN permissoes p
    WHERE u.ativo = TRUE
      AND p.codigo IN ('nfse_view', 'nfse_buscar', 'nfse_config', 'nfse_export', 'nfse_delete')
    ON CONFLICT (usuario_id, permissao_id) DO NOTHING;
    """
    
    cursor.execute(sql_usuarios)
    rows_usuarios = cursor.rowcount
    conn.commit()
    print(f"   ✅ {rows_usuarios} permissão(ões) atribuída(s) aos usuários")

    # 3. Verificar resultado
    print("\n3️⃣ Verificando permissões NFS-e...")
    
    cursor.execute("""
        SELECT id, codigo, nome, categoria
        FROM permissoes 
        WHERE codigo LIKE 'nfse_%'
        ORDER BY id
    """)
    
    permissoes = cursor.fetchall()
    print(f"   ✅ {len(permissoes)} permissão(ões) de NFS-e encontrada(s):")
    for p in permissoes:
        print(f"      - ID {p[0]}: {p[1]} ({p[2]})")

    # 4. Verificar quantos usuários têm as permissões
    cursor.execute("""
        SELECT COUNT(DISTINCT u.id) as qtd_usuarios, COUNT(*) as qtd_total
        FROM usuario_permissoes up
        JOIN usuarios u ON u.id = up.usuario_id
        JOIN permissoes p ON p.id = up.permissao_id
        WHERE p.codigo LIKE 'nfse_%'
    """)
    
    result = cursor.fetchone()
    print(f"\n   📊 {result[0]} usuário(s) com {result[1]} permissão(ões) NFS-e no total")

    cursor.close()

    print("\n" + "=" * 80)
    print("✅ PERMISSÕES NFS-e CONFIGURADAS COM SUCESSO!")
    print("=" * 80)
    print("\n💡 Faça logout e login para atualizar as permissões na sessão")

except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
