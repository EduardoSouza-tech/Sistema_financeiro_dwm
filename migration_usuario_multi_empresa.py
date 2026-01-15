"""
Migração: Usuário Multi-Empresa
Permite que um usuário tenha acesso a múltiplas empresas

Alterações:
1. Cria tabela usuario_empresas (N:N)
2. Torna usuarios.empresa_id nullable
3. Migra dados existentes
4. Cria índices de performance
"""

import sys
from database_postgresql import DatabaseManager

def executar_migracao(db: DatabaseManager):
    """Executa migração multi-empresa"""
    
    print("\n" + "="*80)
    print("🔄 MIGRAÇÃO: USUÁRIO MULTI-EMPRESA")
    print("="*80)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # ==============================================================
        # ETAPA 1: Criar tabela usuario_empresas
        # ==============================================================
        print("\n📋 Etapa 1: Criando tabela usuario_empresas...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuario_empresas (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                
                -- Papel do usuário nesta empresa específica
                papel VARCHAR(50) DEFAULT 'usuario',
                
                -- Permissões específicas nesta empresa (JSON array)
                permissoes_empresa JSONB DEFAULT '[]',
                
                -- Status do acesso
                ativo BOOLEAN DEFAULT TRUE,
                
                -- Empresa padrão (quando usuário faz login)
                is_empresa_padrao BOOLEAN DEFAULT FALSE,
                
                -- Auditoria
                criado_por INTEGER REFERENCES usuarios(id),
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                UNIQUE(usuario_id, empresa_id)
            )
        """)
        
        print("   ✅ Tabela usuario_empresas criada")
        
        # ==============================================================
        # ETAPA 2: Criar índices
        # ==============================================================
        print("\n📊 Etapa 2: Criando índices...")
        
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_usuario_empresas_usuario ON usuario_empresas(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_usuario_empresas_empresa ON usuario_empresas(empresa_id)",
            "CREATE INDEX IF NOT EXISTS idx_usuario_empresas_ativo ON usuario_empresas(ativo) WHERE ativo = TRUE",
            "CREATE INDEX IF NOT EXISTS idx_usuario_empresas_padrao ON usuario_empresas(is_empresa_padrao) WHERE is_empresa_padrao = TRUE"
        ]
        
        for idx_sql in indices:
            cursor.execute(idx_sql)
            print(f"   ✅ Índice criado")
        
        # ==============================================================
        # ETAPA 3: Tornar usuarios.empresa_id nullable
        # ==============================================================
        print("\n🔧 Etapa 3: Tornando usuarios.empresa_id nullable...")
        
        # Verificar se a coluna existe e se é NOT NULL
        cursor.execute("""
            SELECT is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'usuarios' 
            AND column_name = 'empresa_id'
        """)
        
        result = cursor.fetchone()
        if result and result['is_nullable'] == 'NO':
            cursor.execute("""
                ALTER TABLE usuarios 
                ALTER COLUMN empresa_id DROP NOT NULL
            """)
            print("   ✅ empresa_id agora é nullable")
        else:
            print("   ℹ️ empresa_id já é nullable")
        
        # ==============================================================
        # ETAPA 4: Migrar dados existentes
        # ==============================================================
        print("\n📦 Etapa 4: Migrando dados existentes...")
        
        # Contar usuários com empresa_id
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM usuarios 
            WHERE empresa_id IS NOT NULL 
            AND tipo != 'admin'
        """)
        
        count_result = cursor.fetchone()
        usuarios_para_migrar = count_result['count'] if count_result else 0
        
        print(f"   📊 Encontrados {usuarios_para_migrar} usuários para migrar")
        
        if usuarios_para_migrar > 0:
            # Inserir registros em usuario_empresas
            cursor.execute("""
                INSERT INTO usuario_empresas 
                    (usuario_id, empresa_id, papel, is_empresa_padrao, ativo, criado_por)
                SELECT 
                    u.id as usuario_id,
                    u.empresa_id,
                    CASE 
                        WHEN u.tipo = 'admin' THEN 'admin_empresa'
                        ELSE 'usuario'
                    END as papel,
                    TRUE as is_empresa_padrao,
                    u.ativo as ativo,
                    u.created_by as criado_por
                FROM usuarios u
                WHERE u.empresa_id IS NOT NULL
                AND u.tipo != 'admin'
                ON CONFLICT (usuario_id, empresa_id) DO NOTHING
            """)
            
            migrados = cursor.rowcount
            print(f"   ✅ Migrados {migrados} registros para usuario_empresas")
            
            # Migrar permissões existentes
            print("   🔑 Migrando permissões existentes...")
            
            cursor.execute("""
                UPDATE usuario_empresas ue
                SET permissoes_empresa = COALESCE((
                    SELECT jsonb_agg(p.codigo)
                    FROM usuario_permissoes up
                    JOIN permissoes p ON up.permissao_id = p.id
                    WHERE up.usuario_id = ue.usuario_id
                    AND up.ativo = TRUE
                ), '[]'::jsonb)
                WHERE ue.permissoes_empresa = '[]'::jsonb
            """)
            
            print(f"   ✅ Permissões migradas")
        
        # ==============================================================
        # ETAPA 5: Criar trigger de auditoria
        # ==============================================================
        print("\n⚙️ Etapa 5: Criando trigger de atualização...")
        
        cursor.execute("""
            CREATE OR REPLACE FUNCTION atualizar_usuario_empresas_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.atualizado_em = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        cursor.execute("""
            DROP TRIGGER IF EXISTS trigger_atualizar_usuario_empresas 
            ON usuario_empresas
        """)
        
        cursor.execute("""
            CREATE TRIGGER trigger_atualizar_usuario_empresas
            BEFORE UPDATE ON usuario_empresas
            FOR EACH ROW
            EXECUTE FUNCTION atualizar_usuario_empresas_timestamp()
        """)
        
        print("   ✅ Trigger criado")
        
        # ==============================================================
        # ETAPA 6: Criar views úteis
        # ==============================================================
        print("\n📊 Etapa 6: Criando views de suporte...")
        
        cursor.execute("""
            CREATE OR REPLACE VIEW v_usuarios_empresas AS
            SELECT 
                u.id as usuario_id,
                u.username,
                u.nome_completo,
                u.tipo as tipo_usuario,
                e.id as empresa_id,
                e.razao_social as empresa_nome,
                ue.papel,
                ue.ativo as acesso_ativo,
                ue.is_empresa_padrao,
                ue.permissoes_empresa,
                ue.criado_em,
                ue.atualizado_em
            FROM usuarios u
            LEFT JOIN usuario_empresas ue ON u.id = ue.usuario_id
            LEFT JOIN empresas e ON ue.empresa_id = e.id
            WHERE u.tipo != 'admin'
            ORDER BY u.username, e.razao_social
        """)
        
        print("   ✅ View v_usuarios_empresas criada")
        
        # ==============================================================
        # COMMIT
        # ==============================================================
        conn.commit()
        
        print("\n" + "="*80)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*80)
        
        # Estatísticas finais
        cursor.execute("SELECT COUNT(*) as count FROM usuario_empresas")
        total = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(DISTINCT usuario_id) as count 
            FROM usuario_empresas
        """)
        usuarios = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(DISTINCT empresa_id) as count 
            FROM usuario_empresas
        """)
        empresas = cursor.fetchone()['count']
        
        print(f"\n📊 Estatísticas:")
        print(f"   - Total de vínculos: {total}")
        print(f"   - Usuários com acesso: {usuarios}")
        print(f"   - Empresas vinculadas: {empresas}")
        print("")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERRO na migração: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        cursor.close()
        conn.close()


def reverter_migracao(db: DatabaseManager):
    """Reverte a migração (usar com cuidado!)"""
    
    print("\n" + "="*80)
    print("⚠️ REVERTENDO MIGRAÇÃO: USUÁRIO MULTI-EMPRESA")
    print("="*80)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Deletar view
        print("\n🗑️ Removendo view...")
        cursor.execute("DROP VIEW IF EXISTS v_usuarios_empresas CASCADE")
        
        # Deletar trigger
        print("🗑️ Removendo trigger...")
        cursor.execute("DROP TRIGGER IF EXISTS trigger_atualizar_usuario_empresas ON usuario_empresas")
        cursor.execute("DROP FUNCTION IF EXISTS atualizar_usuario_empresas_timestamp()")
        
        # Deletar tabela
        print("🗑️ Removendo tabela usuario_empresas...")
        cursor.execute("DROP TABLE IF EXISTS usuario_empresas CASCADE")
        
        conn.commit()
        
        print("\n✅ Migração revertida com sucesso!")
        print("⚠️ ATENÇÃO: usuarios.empresa_id ainda está nullable")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERRO ao reverter: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    """Executar migração via linha de comando"""
    
    print("\n🚀 Iniciando sistema de migração...")
    
    try:
        # Inicializar database
        db = DatabaseManager()
        
        # Menu de opções
        print("\n" + "="*80)
        print("MIGRAÇÃO: USUÁRIO MULTI-EMPRESA")
        print("="*80)
        print("\nOpções:")
        print("  1. Executar migração (criar estrutura multi-empresa)")
        print("  2. Reverter migração (CUIDADO: remove dados!)")
        print("  3. Verificar status")
        print("  0. Cancelar")
        print("")
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == '1':
            print("\n⚠️ Esta migração vai:")
            print("  - Criar tabela usuario_empresas")
            print("  - Tornar usuarios.empresa_id nullable")
            print("  - Migrar dados existentes")
            print("")
            confirma = input("Deseja continuar? (sim/não): ").strip().lower()
            
            if confirma in ['sim', 's', 'yes', 'y']:
                sucesso = executar_migracao(db)
                sys.exit(0 if sucesso else 1)
            else:
                print("❌ Operação cancelada")
                sys.exit(0)
                
        elif opcao == '2':
            print("\n⚠️⚠️⚠️ ATENÇÃO ⚠️⚠️⚠️")
            print("Esta operação vai DELETAR a tabela usuario_empresas!")
            print("Todos os vínculos usuário-empresa serão perdidos!")
            print("")
            confirma = input("Digite 'REVERTER' para confirmar: ").strip()
            
            if confirma == 'REVERTER':
                sucesso = reverter_migracao(db)
                sys.exit(0 if sucesso else 1)
            else:
                print("❌ Operação cancelada")
                sys.exit(0)
                
        elif opcao == '3':
            print("\n📊 Verificando status...")
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Verificar se tabela existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'usuario_empresas'
                )
            """)
            
            tabela_existe = cursor.fetchone()['exists']
            
            if tabela_existe:
                print("   ✅ Tabela usuario_empresas: EXISTE")
                
                cursor.execute("SELECT COUNT(*) as count FROM usuario_empresas")
                total = cursor.fetchone()['count']
                print(f"   📊 Total de vínculos: {total}")
            else:
                print("   ❌ Tabela usuario_empresas: NÃO EXISTE")
            
            cursor.close()
            conn.close()
            
        else:
            print("❌ Operação cancelada")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
