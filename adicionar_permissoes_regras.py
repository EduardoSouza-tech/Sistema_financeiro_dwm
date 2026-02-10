"""
Script: Adiciona permissões de regras_conciliacao para todos os usuários
"""
import os
import psycopg2

# URL do Railway
DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("🔑 ADICIONANDO PERMISSÕES: regras_conciliacao")
print("=" * 80)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. Buscar IDs das permissões
    print("\n1️⃣ Buscando IDs das permissões...")
    cursor.execute("""
        SELECT id, codigo, nome 
        FROM permissoes 
        WHERE codigo LIKE 'regras_conciliacao_%'
        ORDER BY codigo
    """)
    permissoes = cursor.fetchall()
    
    print(f"   ✅ {len(permissoes)} permissão(ões) encontrada(s):")
    for perm in permissoes:
        print(f"      - ID {perm[0]}: {perm[1]}")
    
    # 2. Buscar usuários
    print("\n2️⃣ Buscando usuários...")
    cursor.execute("""
        SELECT id, nome, tipo 
        FROM usuarios 
        ORDER BY id
    """)
    usuarios = cursor.fetchall()
    
    print(f"   ✅ {len(usuarios)} usuário(s) encontrado(s):")
    for user in usuarios:
        print(f"      - ID {user[0]}: {user[1]} ({user[2]})")
    
    # 3. Adicionar permissões para cada usuário
    print("\n3️⃣ Adicionando permissões aos usuários...")
    
    adicionadas = 0
    ja_existentes = 0
    
    for usuario in usuarios:
        user_id = usuario[0]
        user_nome = usuario[1]
        
        for permissao in permissoes:
            perm_id = permissao[0]
            perm_codigo = permissao[1]
            
            try:
                # Tentar inserir
                cursor.execute("""
                    INSERT INTO usuarios_permissoes (usuario_id, permissao_id)
                    VALUES (%s, %s)
                """, (user_id, perm_id))
                
                print(f"      ✅ {user_nome} → {perm_codigo}")
                adicionadas += 1
                
            except psycopg2.IntegrityError:
                # Já existe
                conn.rollback()
                ja_existentes += 1
                continue
    
    # Commit das mudanças
    conn.commit()
    
    print(f"\n📊 Resumo:")
    print(f"   ✅ {adicionadas} permissão(ões) adicionada(s)")
    print(f"   ℹ️ {ja_existentes} permissão(ões) já existiam")
    
    # 4. Verificar permissões do usuário específico
    print("\n4️⃣ Verificando permissões do usuário 'Matheus Alcantra'...")
    cursor.execute("""
        SELECT p.codigo, p.nome
        FROM usuarios_permissoes up
        JOIN permissoes p ON p.id = up.permissao_id
        JOIN usuarios u ON u.id = up.usuario_id
        WHERE u.nome LIKE '%Matheus%'
        AND p.codigo LIKE 'regras_conciliacao_%'
        ORDER BY p.codigo
    """)
    perms_usuario = cursor.fetchall()
    
    if perms_usuario:
        print(f"   ✅ {len(perms_usuario)} permissão(ões) de regras:")
        for perm in perms_usuario:
            print(f"      - {perm[0]}: {perm[1]}")
    else:
        print("   ⚠️ Nenhuma permissão de regras encontrada!")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ PERMISSÕES CONFIGURADAS COM SUCESSO!")
    print("=" * 80)
    print("\n💡 PRÓXIMO PASSO: Faça logout e login novamente para atualizar as permissões")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
