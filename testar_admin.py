"""Script para testar autenticação e tipo de usuário admin"""
import os
os.environ['DATABASE_TYPE'] = 'postgresql'

from database_postgresql import DatabaseManager
import hashlib

def testar_admin():
    """Testa o usuário admin no banco"""
    print("\n" + "="*80)
    print("🔍 TESTE DE USUÁRIO ADMIN NO BANCO DE DADOS")
    print("="*80)
    
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 1. Verificar se usuário admin existe
    print("\n1️⃣ Verificando existência do usuário admin...")
    cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    admin = cursor.fetchone()
    
    if not admin:
        print("❌ Usuário admin NÃO encontrado no banco!")
        cursor.close()
        conn.close()
        return
    
    print("✅ Usuário admin ENCONTRADO")
    print(f"   ID: {admin['id']}")
    print(f"   Username: {admin['username']}")
    print(f"   🎯 TIPO: '{admin['tipo']}' (Python type: {type(admin['tipo'])})")
    print(f"   Tipo repr: {repr(admin['tipo'])}")
    print(f"   Tipo bytes: {admin['tipo'].encode() if admin['tipo'] else 'None'}")
    print(f"   Nome: {admin['nome_completo']}")
    print(f"   Email: {admin['email']}")
    print(f"   Ativo: {admin['ativo']}")
    
    # 2. Testar autenticação
    print("\n2️⃣ Testando autenticação com senha 'admin123'...")
    senha = "admin123"
    password_hash = hashlib.sha256(senha.encode()).hexdigest()
    
    cursor.execute("""
        SELECT * FROM usuarios 
        WHERE username = 'admin' AND password_hash = %s
    """, (password_hash,))
    
    auth = cursor.fetchone()
    if auth:
        print("✅ Autenticação CORRETA")
        print(f"   🎯 TIPO após auth: '{auth['tipo']}' (Python type: {type(auth['tipo'])})")
    else:
        print("❌ Autenticação FALHOU")
        
        # Verificar hash armazenado
        cursor.execute("SELECT password_hash FROM usuarios WHERE username = 'admin'")
        stored = cursor.fetchone()
        print(f"\n   Hash calculado: {password_hash}")
        print(f"   Hash armazenado: {stored['password_hash']}")
        print(f"   Hashes iguais: {password_hash == stored['password_hash']}")
    
    # 3. Verificar sessões ativas
    print("\n3️⃣ Verificando sessões ativas...")
    cursor.execute("""
        SELECT s.*, u.tipo
        FROM sessoes_login s
        JOIN usuarios u ON s.usuario_id = u.id
        WHERE u.username = 'admin' AND s.ativo = TRUE
        ORDER BY s.criado_em DESC
        LIMIT 5
    """)
    
    sessoes = cursor.fetchall()
    print(f"   Total de sessões ativas: {len(sessoes)}")
    
    for i, sessao in enumerate(sessoes, 1):
        print(f"\n   Sessão {i}:")
        print(f"      Token: {sessao['session_token'][:30]}...")
        print(f"      🎯 TIPO na sessão: '{sessao['tipo']}'")
        print(f"      Criado em: {sessao['criado_em']}")
        print(f"      Expira em: {sessao['expira_em']}")
        print(f"      IP: {sessao['ip_address']}")
    
    # 4. Testar comparação de tipo
    print("\n4️⃣ Testando comparações de tipo...")
    tipo_db = admin['tipo']
    print(f"   tipo_db = '{tipo_db}'")
    print(f"   tipo_db == 'admin': {tipo_db == 'admin'}")
    print(f"   tipo_db != 'admin': {tipo_db != 'admin'}")
    print(f"   tipo_db.lower() == 'admin': {tipo_db.lower() == 'admin'}")
    print(f"   tipo_db.strip() == 'admin': {tipo_db.strip() == 'admin'}")
    print(f"   'admin' in tipo_db: {'admin' in tipo_db}")
    
    # 5. Verificar estrutura da tabela
    print("\n5️⃣ Verificando estrutura da tabela usuarios...")
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'usuarios' AND column_name = 'tipo'
    """)
    
    col_info = cursor.fetchone()
    if col_info:
        print(f"   Nome da coluna: {col_info['column_name']}")
        print(f"   Tipo de dados: {col_info['data_type']}")
        print(f"   Tamanho máximo: {col_info['character_maximum_length']}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅ TESTE CONCLUÍDO")
    print("="*80 + "\n")

if __name__ == '__main__':
    testar_admin()
