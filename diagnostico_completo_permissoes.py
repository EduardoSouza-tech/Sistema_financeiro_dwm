"""
DIAGNÓSTICO COMPLETO: Sistema de Permissões e Regras de Conciliação
"""
import psycopg2

DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("🔍 DIAGNÓSTICO COMPLETO: REGRAS DE CONCILIAÇÃO")
print("=" * 80)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. Verificar permissões cadastradas
    print("\n1️⃣ PERMISSÕES CADASTRADAS:")
    cursor.execute("""
        SELECT id, codigo, nome, categoria 
        FROM permissoes 
        WHERE codigo LIKE 'regras_conciliacao_%'
        ORDER BY codigo
    """)
    permissoes = cursor.fetchall()
    
    if permissoes:
        print(f"   ✅ {len(permissoes)} permissão(ões) cadastrada(s):")
        perm_ids = []
        for p in permissoes:
            print(f"      • ID {p[0]}: {p[1]}")
            print(f"        Nome: {p[2]}")
            print(f"        Categoria: {p[3]}")
            perm_ids.append(p[0])
    else:
        print("   ❌ NENHUMA PERMISSÃO DE REGRAS CADASTRADA!")
    
    # 2. Verificar usuário Matheus
    print("\n2️⃣ USUÁRIO MATHEUS ALCANTRA:")
    cursor.execute("""
        SELECT id, username, nome_completo, tipo, ativo 
        FROM usuarios 
        WHERE nome_completo LIKE '%Matheus%'
    """)
    usuario = cursor.fetchone()
    
    if usuario:
        user_id = usuario[0]
        print(f"   ✅ Usuário encontrado:")
        print(f"      ID: {user_id}")
        print(f"      Username: {usuario[1]}")
        print(f"      Nome: {usuario[2]}")
        print(f"      Tipo: {usuario[3]}")
        print(f"      Ativo: {usuario[4]}")
        
        # 3. Verificar permissões do usuário
        print("\n3️⃣ PERMISSÕES DO USUÁRIO NO BANCO:")
        cursor.execute("""
            SELECT p.id, p.codigo, p.nome
            FROM usuario_permissoes up
            JOIN permissoes p ON p.id = up.permissao_id
            WHERE up.usuario_id = %s
            ORDER BY p.codigo
        """, (user_id,))
        user_perms = cursor.fetchall()
        
        print(f"   📊 Total: {len(user_perms)} permissão(ões)")
        
        # Verificar permissões de regras
        regras_perms = [p for p in user_perms if 'regras_conciliacao' in p[1]]
        
        if regras_perms:
            print(f"\n   ✅ {len(regras_perms)} permissão(ões) de REGRAS:")
            for p in regras_perms:
                print(f"      • {p[1]}: {p[2]}")
        else:
            print("\n   ❌ NENHUMA PERMISSÃO DE REGRAS!")
            print("   🔧 Adicionando agora...")
            
            # Adicionar permissões
            for perm_id in perm_ids:
                try:
                    cursor.execute("""
                        INSERT INTO usuario_permissoes (usuario_id, permissao_id)
                        VALUES (%s, %s)
                    """, (user_id, perm_id))
                    print(f"      ✅ Permissão ID {perm_id} adicionada")
                except Exception as e:
                    print(f"      ⚠️ Permissão ID {perm_id}: {e}")
            
            conn.commit()
            print("\n   ✅ Permissões adicionadas! FAÇA LOGOUT E LOGIN!")
    else:
        print("   ❌ USUÁRIO NÃO ENCONTRADO!")
    
    # 4. Verificar todas as permissões de lancamentos que o usuário tem
    print("\n4️⃣ PERMISSÕES DE LANÇAMENTOS (para comparação):")
    cursor.execute("""
        SELECT p.codigo
        FROM usuario_permissoes up
        JOIN permissoes p ON p.id = up.permissao_id
        WHERE up.usuario_id = %s
        AND p.codigo LIKE 'lancamentos_%'
        ORDER BY p.codigo
    """, (user_id,))
    lanc_perms = cursor.fetchall()
    
    if lanc_perms:
        print(f"   ✅ {len(lanc_perms)} permissão(ões) de lançamentos:")
        for p in lanc_perms:
            print(f"      • {p[0]}")
    
    # 5. Verificar estrutura do endpoint
    print("\n5️⃣ ESTRUTURA ESPERADA:")
    print("   📋 Endpoints de regras e suas permissões:")
    print("      • GET /api/regras-conciliacao → regras_conciliacao_view")
    print("      • POST /api/regras-conciliacao → regras_conciliacao_create")
    print("      • PUT /api/regras-conciliacao/<id> → regras_conciliacao_edit")
    print("      • DELETE /api/regras-conciliacao/<id> → regras_conciliacao_delete")
    
    # 6. Verificar total de permissões
    print("\n6️⃣ RESUMO COMPLETO:")
    cursor.execute("""
        SELECT COUNT(*) FROM usuario_permissoes WHERE usuario_id = %s
    """, (user_id,))
    total = cursor.fetchone()[0]
    print(f"   📊 Total de permissões do usuário: {total}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ DIAGNÓSTICO CONCLUÍDO")
    print("=" * 80)
    print("\n🚨 AÇÃO NECESSÁRIA:")
    print("   Se as permissões foram adicionadas agora, você DEVE:")
    print("   1. Clicar em 'Sair' no sistema")
    print("   2. Fazer login novamente")
    print("   3. As permissões serão recarregadas na sessão")
    print("\n💡 O erro 403 é porque a SESSÃO ainda tem as permissões antigas!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
