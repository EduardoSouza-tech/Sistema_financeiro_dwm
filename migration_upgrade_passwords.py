"""
Migration: Upgrade de Senhas SHA-256 para Bcrypt
==================================================

Este script implementa um sistema de upgrade automático de senhas:
1. Detecta senhas com hash SHA-256 (64 caracteres hexadecimais)
2. No próximo login bem-sucedido, atualiza para bcrypt
3. Mantém compatibilidade total durante a transição

IMPORTANTE: Não roda como migration tradicional!
O upgrade acontece automaticamente no login de cada usuário.
"""

import hashlib
import re
from datetime import datetime
from typing import Optional, Tuple

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    print("⚠️ bcrypt não disponível - migration não será efetiva")


def is_sha256_hash(hash_string: str) -> bool:
    """
    Detecta se um hash é SHA-256
    
    SHA-256 tem:
    - Exatamente 64 caracteres
    - Apenas caracteres hexadecimais (0-9, a-f)
    """
    if not hash_string or len(hash_string) != 64:
        return False
    
    return bool(re.match(r'^[a-f0-9]{64}$', hash_string))


def is_bcrypt_hash(hash_string: str) -> bool:
    """
    Detecta se um hash é bcrypt
    
    Bcrypt tem:
    - Começa com $2a$, $2b$, $2x$ ou $2y$
    - ~60 caracteres no total
    """
    if not hash_string:
        return False
    
    return hash_string.startswith(('$2a$', '$2b$', '$2x$', '$2y$'))


def verificar_e_upgrade_senha(
    username: str, 
    password: str, 
    password_hash: str, 
    db
) -> Tuple[bool, Optional[str]]:
    """
    Verifica senha e faz upgrade automático se necessário
    
    Args:
        username: Nome de usuário
        password: Senha em texto plano
        password_hash: Hash atual armazenado
        db: Objeto de conexão com banco
        
    Returns:
        (bool, str): (senha_correta, novo_hash_ou_none)
    """
    
    # 1. Verificar se a senha está correta
    senha_correta = False
    tipo_hash = None
    
    if is_bcrypt_hash(password_hash):
        # Hash já é bcrypt - verificar normalmente
        if BCRYPT_AVAILABLE:
            senha_correta = bcrypt.checkpw(password.encode(), password_hash.encode())
            tipo_hash = 'bcrypt'
        else:
            print(f"⚠️ Hash bcrypt detectado mas bcrypt não disponível para {username}")
            return False, None
            
    elif is_sha256_hash(password_hash):
        # Hash é SHA-256 - verificar e marcar para upgrade
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        senha_correta = (sha256_hash == password_hash)
        tipo_hash = 'sha256'
    else:
        # Hash em formato desconhecido
        print(f"⚠️ Formato de hash desconhecido para usuário {username}: {password_hash[:20]}...")
        return False, None
    
    # 2. Se senha incorreta, não fazer nada
    if not senha_correta:
        return False, None
    
    # 3. Se senha correta e hash é SHA-256, fazer upgrade para bcrypt
    if tipo_hash == 'sha256' and BCRYPT_AVAILABLE:
        try:
            # Gerar novo hash bcrypt
            novo_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            # Atualizar no banco
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE usuarios 
                SET password_hash = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE username = %s
            """, (novo_hash, username))
            
            conn.commit()
            cursor.close()
            
            print(f"✅ Senha de {username} atualizada de SHA-256 para bcrypt")
            return True, novo_hash
            
        except Exception as e:
            print(f"❌ Erro ao fazer upgrade de senha para {username}: {e}")
            # Mesmo com erro no upgrade, a senha estava correta
            return True, None
    
    # 4. Senha correta, sem necessidade de upgrade
    return True, None


def relatorio_hashes_pendentes(db) -> dict:
    """
    Gera relatório de quantos usuários ainda usam SHA-256
    
    Returns:
        {
            'total_usuarios': int,
            'usuarios_bcrypt': int,
            'usuarios_sha256': int,
            'usuarios_desconhecido': int,
            'pendentes': [{'username': str, 'tipo': str}]
        }
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT username, password_hash FROM usuarios WHERE ativo = TRUE")
    usuarios = cursor.fetchall()
    cursor.close()
    
    stats = {
        'total_usuarios': len(usuarios),
        'usuarios_bcrypt': 0,
        'usuarios_sha256': 0,
        'usuarios_desconhecido': 0,
        'pendentes': []
    }
    
    for user in usuarios:
        username = user['username']
        hash_val = user['password_hash']
        
        if is_bcrypt_hash(hash_val):
            stats['usuarios_bcrypt'] += 1
        elif is_sha256_hash(hash_val):
            stats['usuarios_sha256'] += 1
            stats['pendentes'].append({
                'username': username,
                'tipo': 'sha256'
            })
        else:
            stats['usuarios_desconhecido'] += 1
            stats['pendentes'].append({
                'username': username,
                'tipo': 'desconhecido'
            })
    
    return stats


def forcar_upgrade_usuario(username: str, nova_senha: str, db) -> bool:
    """
    Força upgrade de senha para um usuário específico
    Útil para admins que querem forçar reset
    
    Args:
        username: Nome de usuário
        nova_senha: Nova senha em texto plano
        db: Objeto de conexão com banco
        
    Returns:
        bool: Sucesso ou falha
    """
    if not BCRYPT_AVAILABLE:
        print("❌ bcrypt não disponível - upgrade não possível")
        return False
    
    try:
        novo_hash = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE usuarios 
            SET password_hash = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE username = %s
        """, (novo_hash, username))
        
        linhas_afetadas = cursor.rowcount
        conn.commit()
        cursor.close()
        
        if linhas_afetadas > 0:
            print(f"✅ Senha de {username} atualizada com sucesso")
            return True
        else:
            print(f"⚠️ Usuário {username} não encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao atualizar senha de {username}: {e}")
        return False


# ============================================================================
# INTEGRAÇÃO COM auth_functions.py
# ============================================================================

def login_com_upgrade(username: str, password: str, db) -> Tuple[bool, Optional[dict]]:
    """
    Função de login que integra o upgrade automático
    
    Substitui a lógica de login existente para adicionar upgrade automático
    
    Returns:
        (bool, dict): (sucesso, dados_usuario ou None)
    """
    from auth_functions import verificar_senha
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Buscar usuário
        cursor.execute("""
            SELECT id, username, password_hash, tipo, nome_completo, 
                   email, empresa_id, ativo
            FROM usuarios 
            WHERE username = %s AND ativo = TRUE
        """, (username,))
        
        usuario = cursor.fetchone()
        cursor.close()
        
        if not usuario:
            return False, None
        
        # Verificar senha COM upgrade automático
        senha_correta, novo_hash = verificar_e_upgrade_senha(
            username, 
            password, 
            usuario['password_hash'],
            db
        )
        
        if not senha_correta:
            return False, None
        
        # Login bem-sucedido
        return True, {
            'id': usuario['id'],
            'username': usuario['username'],
            'tipo': usuario['tipo'],
            'nome_completo': usuario['nome_completo'],
            'email': usuario['email'],
            'empresa_id': usuario['empresa_id'],
            'hash_atualizado': novo_hash is not None
        }
        
    except Exception as e:
        print(f"❌ Erro no login com upgrade: {e}")
        return False, None


# ============================================================================
# SCRIPT CLI PARA ANÁLISE
# ============================================================================

if __name__ == "__main__":
    """
    Script CLI para analisar status de migração de senhas
    
    Uso:
        python migration_upgrade_passwords.py [relatorio|forcar USERNAME SENHA]
    """
    import sys
    from database_postgresql import DatabasePostgreSQL
    from config import DATABASE_CONFIG
    
    db = DatabasePostgreSQL(DATABASE_CONFIG)
    
    if len(sys.argv) == 1 or sys.argv[1] == 'relatorio':
        # Gerar relatório
        print("\n" + "="*70)
        print("RELATÓRIO DE MIGRAÇÃO DE SENHAS SHA-256 → BCRYPT")
        print("="*70 + "\n")
        
        stats = relatorio_hashes_pendentes(db)
        
        print(f"Total de usuários ativos: {stats['total_usuarios']}")
        print(f"  ✅ Bcrypt (seguro):      {stats['usuarios_bcrypt']}")
        print(f"  ⚠️  SHA-256 (antigo):     {stats['usuarios_sha256']}")
        print(f"  ❓ Desconhecido:         {stats['usuarios_desconhecido']}")
        print()
        
        if stats['pendentes']:
            print(f"Usuários pendentes de upgrade ({len(stats['pendentes'])}):")
            for user in stats['pendentes']:
                print(f"  - {user['username']} (tipo: {user['tipo']})")
        else:
            print("✅ Todos os usuários estão usando bcrypt!")
        
        print("\n" + "="*70)
        print("💡 As senhas serão atualizadas automaticamente no próximo login")
        print("="*70 + "\n")
    
    elif len(sys.argv) == 4 and sys.argv[1] == 'forcar':
        # Forçar upgrade de usuário específico
        username = sys.argv[2]
        nova_senha = sys.argv[3]
        
        print(f"\n🔄 Forçando upgrade de senha para: {username}")
        sucesso = forcar_upgrade_usuario(username, nova_senha, db)
        
        if sucesso:
            print("✅ Upgrade concluído com sucesso\n")
        else:
            print("❌ Falha no upgrade\n")
    
    else:
        print("\nUso:")
        print("  python migration_upgrade_passwords.py                    # Gerar relatório")
        print("  python migration_upgrade_passwords.py relatorio          # Gerar relatório")
        print("  python migration_upgrade_passwords.py forcar USER SENHA  # Forçar upgrade")
        print()
