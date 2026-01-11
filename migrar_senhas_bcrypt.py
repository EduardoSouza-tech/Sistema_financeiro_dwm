"""
Script para migrar senhas SHA-256 para bcrypt
ATENÇÃO: Este script atualiza o hash de senha do admin para bcrypt
Após executar, use a senha original para fazer login
"""
import os
os.environ['DATABASE_TYPE'] = 'postgresql'

from database_postgresql import DatabaseManager
import bcrypt

def migrar_senha_admin():
    """Atualiza a senha do admin de SHA-256 para bcrypt"""
    print("\n" + "="*70)
    print("🔐 MIGRAÇÃO DE SENHAS: SHA-256 → bcrypt")
    print("="*70)
    
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Senha padrão do admin
        senha_admin = "admin123"
        
        # Gerar novo hash bcrypt
        novo_hash = bcrypt.hashpw(senha_admin.encode(), bcrypt.gensalt()).decode()
        
        print(f"\n1️⃣ Atualizando senha do admin...")
        print(f"   Nova senha: {senha_admin}")
        print(f"   Algoritmo: bcrypt (mais seguro)")
        
        # Atualizar admin
        cursor.execute("""
            UPDATE usuarios 
            SET password_hash = %s 
            WHERE username = 'admin'
        """, (novo_hash,))
        
        if cursor.rowcount > 0:
            print(f"   ✅ Senha do admin atualizada com sucesso!")
        else:
            print(f"   ⚠️ Usuário admin não encontrado")
        
        # Verificar se existem outros usuários com SHA-256 (64 caracteres)
        print(f"\n2️⃣ Verificando outros usuários com SHA-256...")
        cursor.execute("""
            SELECT username, LENGTH(password_hash) as hash_length
            FROM usuarios 
            WHERE LENGTH(password_hash) = 64
            AND username != 'admin'
        """)
        
        usuarios_sha256 = cursor.fetchall()
        
        if usuarios_sha256:
            print(f"   ⚠️ Encontrados {len(usuarios_sha256)} usuários com SHA-256:")
            for user in usuarios_sha256:
                print(f"      - {user['username']}")
            print(f"\n   ℹ️ Estes usuários terão suas senhas migradas automaticamente")
            print(f"      no próximo login (compatibilidade retroativa)")
        else:
            print(f"   ✅ Nenhum outro usuário com SHA-256 encontrado")
        
        conn.commit()
        
        print(f"\n{'='*70}")
        print(f"✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"{'='*70}")
        print(f"\n📋 Próximos passos:")
        print(f"   1. Faça login com: admin / admin123")
        print(f"   2. Altere a senha para uma senha forte")
        print(f"   3. Outros usuários serão migrados automaticamente no login")
        print(f"\n🔐 Segurança aprimorada:")
        print(f"   ✅ bcrypt com salt automático")
        print(f"   ✅ Proteção contra rainbow tables")
        print(f"   ✅ Proteção contra brute force")
        print(f"\n")
        
    except Exception as e:
        print(f"\n❌ Erro durante migração: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    migrar_senha_admin()
