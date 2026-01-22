#!/usr/bin/env python3
"""
🔐 Script Seguro para Criar/Resetar Usuário Admin
==================================================

Este script substitui o endpoint /api/debug/criar-admin em produção.
Deve ser executado APENAS via terminal com acesso ao servidor.

USO:
    python criar_admin_seguro.py
    python criar_admin_seguro.py --username admin --password "SenhaForte123!"
    python criar_admin_seguro.py --reset admin

SEGURANÇA:
- ✅ Requer senha forte (8+ caracteres, maiúsculas, números, especiais)
- ✅ Usa bcrypt para hash
- ✅ Não expõe endpoint HTTP
- ✅ Requer acesso direto ao servidor/container
"""

import sys
import os
import getpass
from typing import Optional

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def criar_admin_seguro(username: str = 'admin', password: Optional[str] = None):
    """
    Cria ou atualiza usuário admin com segurança
    """
    try:
        from auth_functions import hash_password, validar_senha_forte
        from database_postgresql import DatabasePostgreSQL
        from config import DATABASE_CONFIG
        
        print("\n" + "="*70)
        print("🔐 CRIAÇÃO SEGURA DE USUÁRIO ADMIN")
        print("="*70)
        
        # Solicitar senha se não fornecida
        if not password:
            print(f"\n📝 Digite a senha para o usuário '{username}'")
            print("   (Requisitos: 8+ chars, maiúscula, número, especial)")
            password = getpass.getpass("Senha: ")
            password_confirm = getpass.getpass("Confirmar senha: ")
            
            if password != password_confirm:
                print("\n❌ ERRO: Senhas não conferem!")
                return False
        
        # Validar força da senha
        valida, mensagem = validar_senha_forte(password)
        if not valida:
            print(f"\n❌ ERRO: Senha fraca - {mensagem}")
            return False
        
        print("\n✅ Senha validada com sucesso")
        
        # Conectar ao banco
        print("📡 Conectando ao banco de dados...")
        db = DatabasePostgreSQL(DATABASE_CONFIG)
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Gerar hash
        print("🔐 Gerando hash seguro (bcrypt)...")
        password_hash = hash_password(password)
        
        # Verificar se usuário existe
        cursor.execute(
            "SELECT id, ativo FROM usuarios WHERE username = %s",
            (username,)
        )
        usuario_existente = cursor.fetchone()
        
        if usuario_existente:
            print(f"\n⚠️  Usuário '{username}' já existe (ID: {usuario_existente['id']})")
            resposta = input("   Deseja RESETAR a senha? [s/N]: ").lower()
            
            if resposta != 's':
                print("\n❌ Operação cancelada pelo usuário")
                return False
            
            # Atualizar senha
            cursor.execute("""
                UPDATE usuarios 
                SET password_hash = %s,
                    ativo = TRUE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE username = %s
                RETURNING id
            """, (password_hash, username))
            
            result = cursor.fetchone()
            conn.commit()
            
            print(f"\n✅ Senha do usuário '{username}' resetada com sucesso!")
            print(f"   ID: {result['id']}")
        else:
            # Criar novo usuário
            cursor.execute("""
                INSERT INTO usuarios 
                (username, password_hash, tipo, nome_completo, email, ativo)
                VALUES (%s, %s, 'admin', 'Administrador do Sistema', 
                        'admin@sistema.com', TRUE)
                RETURNING id
            """, (username, password_hash))
            
            result = cursor.fetchone()
            conn.commit()
            
            print(f"\n✅ Usuário admin criado com sucesso!")
            print(f"   Username: {username}")
            print(f"   ID: {result['id']}")
            print(f"   Tipo: admin")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("🎉 OPERAÇÃO CONCLUÍDA COM SUCESSO")
        print("="*70)
        print(f"\n💡 Agora você pode fazer login com:")
        print(f"   Username: {username}")
        print(f"   Senha: [a senha que você definiu]")
        print()
        
        return True
        
    except ImportError as e:
        print(f"\n❌ ERRO: Módulo não encontrado - {e}")
        print("   Certifique-se de estar no diretório correto do projeto")
        return False
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False


def resetar_admin(username: str):
    """
    Reseta senha de um admin existente
    """
    print(f"\n🔄 Resetando senha do usuário: {username}")
    return criar_admin_seguro(username=username)


def listar_admins():
    """
    Lista todos os usuários admin no sistema
    """
    try:
        from database_postgresql import DatabasePostgreSQL
        from config import DATABASE_CONFIG
        
        print("\n" + "="*70)
        print("👥 USUÁRIOS ADMIN NO SISTEMA")
        print("="*70 + "\n")
        
        db = DatabasePostgreSQL(DATABASE_CONFIG)
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, nome_completo, email, ativo, 
                   created_at, updated_at
            FROM usuarios 
            WHERE tipo = 'admin'
            ORDER BY id
        """)
        
        admins = cursor.fetchall()
        
        if not admins:
            print("   Nenhum usuário admin encontrado!")
        else:
            for admin in admins:
                status = "🟢 Ativo" if admin['ativo'] else "🔴 Inativo"
                print(f"ID: {admin['id']}")
                print(f"   Username: {admin['username']}")
                print(f"   Nome: {admin['nome_completo']}")
                print(f"   Email: {admin['email']}")
                print(f"   Status: {status}")
                print(f"   Criado: {admin['created_at']}")
                print()
        
        cursor.close()
        conn.close()
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        return False


def main():
    """
    Função principal com CLI
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Script seguro para gerenciar usuários admin',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python criar_admin_seguro.py                              # Modo interativo
  python criar_admin_seguro.py --list                       # Listar admins
  python criar_admin_seguro.py --username admin             # Criar/resetar admin
  python criar_admin_seguro.py --username admin --password "Senha123!"
  python criar_admin_seguro.py --reset admin                # Resetar senha
        """
    )
    
    parser.add_argument('--username', '-u', 
                       help='Username do admin (padrão: admin)')
    parser.add_argument('--password', '-p', 
                       help='Senha (se omitido, será solicitado interativamente)')
    parser.add_argument('--reset', '-r', metavar='USERNAME',
                       help='Resetar senha de um admin existente')
    parser.add_argument('--list', '-l', action='store_true',
                       help='Listar todos os admins')
    
    args = parser.parse_args()
    
    # Verificar ambiente
    is_production = bool(os.getenv('RAILWAY_ENVIRONMENT'))
    if is_production:
        print("\n🚀 Executando em PRODUÇÃO (Railway)")
    else:
        print("\n💻 Executando em DESENVOLVIMENTO")
    
    # Executar ação
    if args.list:
        return 0 if listar_admins() else 1
    elif args.reset:
        return 0 if resetar_admin(args.reset) else 1
    else:
        username = args.username or 'admin'
        return 0 if criar_admin_seguro(username, args.password) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada pelo usuário (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
