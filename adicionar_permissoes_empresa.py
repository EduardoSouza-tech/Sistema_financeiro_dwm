"""
Script para adicionar permissões de regras de conciliação na tabela usuario_empresas
O sistema multi-empresa armazena permissões em JSONB na coluna permissoes_empresa
"""
import database_postgresql as db
import json

def adicionar_permissoes_regras_empresa():
    """Adiciona permissões de regras aos usuários em suas empresas"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Buscar todos os vínculos usuario-empresa ativos
        cursor.execute("""
            SELECT usuario_id, empresa_id, permissoes_empresa
            FROM usuario_empresas
            WHERE ativo = TRUE
        """)
        vinculos = cursor.fetchall()
        
        print(f"📋 Encontrados {len(vinculos)} vínculo(s) usuário-empresa")
        
        # Permissões a adicionar
        novas_permissoes = [
            'regras_conciliacao_view',
            'regras_conciliacao_create', 
            'regras_conciliacao_edit',
            'regras_conciliacao_delete'
        ]
        
        atualizados = 0
        for vinculo in vinculos:
            usuario_id = vinculo['usuario_id']
            empresa_id = vinculo['empresa_id']
            permissoes_atual = vinculo['permissoes_empresa']
            
            # Converter JSONB para lista Python
            if permissoes_atual:
                if isinstance(permissoes_atual, str):
                    permissoes = json.loads(permissoes_atual)
                else:
                    permissoes = permissoes_atual
            else:
                permissoes = []
            
            print(f"\n👤 Usuário {usuario_id} - Empresa {empresa_id}")
            print(f"   Permissões atuais: {len(permissoes)} itens")
            
            # Adicionar novas permissões se não existirem
            permissoes_adicionadas = []
            for perm in novas_permissoes:
                if perm not in permissoes:
                    permissoes.append(perm)
                    permissoes_adicionadas.append(perm)
            
            if permissoes_adicionadas:
                # Atualizar no banco
                cursor.execute("""
                    UPDATE usuario_empresas
                    SET permissoes_empresa = %s::jsonb
                    WHERE usuario_id = %s AND empresa_id = %s
                """, (json.dumps(permissoes), usuario_id, empresa_id))
                
                print(f"   ✅ Adicionadas {len(permissoes_adicionadas)} permissões:")
                for p in permissoes_adicionadas:
                    print(f"      • {p}")
                print(f"   📊 Total agora: {len(permissoes)} permissões")
                atualizados += 1
            else:
                print(f"   ℹ️  Já possui todas as permissões de regras")
        
        conn.commit()
        print(f"\n{'='*60}")
        print(f"✅ CONCLUÍDO: {atualizados} vínculo(s) atualizado(s)")
        print(f"{'='*60}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    adicionar_permissoes_regras_empresa()
