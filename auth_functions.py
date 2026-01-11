"""
Funções de Autenticação e Autorização
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


def hash_password(password: str) -> str:
    """Gera hash SHA-256 da senha"""
    return hashlib.sha256(password.encode()).hexdigest()


def verificar_senha(password: str, password_hash: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    return hash_password(password) == password_hash


def gerar_token_sessao() -> str:
    """Gera um token aleatório para sessão"""
    return secrets.token_urlsafe(64)


# ==================== FUNÇÕES DE USUÁRIOS ====================

def criar_usuario(dados: Dict, db) -> int:
    """
    Cria um novo usuário
    
    Args:
        dados: {
            'username': str,
            'password': str,
            'tipo': 'admin' | 'cliente',
            'nome_completo': str,
            'email': str,
            'telefone': str (opcional),
            'cliente_id': int (opcional, obrigatório se tipo='cliente'),
            'created_by': int (id do admin que está criando)
        }
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Validações
    if dados['tipo'] not in ['admin', 'cliente']:
        raise ValueError("Tipo de usuário inválido. Use 'admin' ou 'cliente'")
    
    if dados['tipo'] == 'cliente' and not dados.get('cliente_id'):
        raise ValueError("cliente_id é obrigatório para usuários do tipo 'cliente'")
    
    # Verificar se username ou email já existem
    cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE username = %s OR email = %s",
                  (dados['username'], dados['email']))
    result = cursor.fetchone()
    if result and result['count'] > 0:
        raise ValueError("Username ou email já cadastrado")
    
    # Hash da senha
    password_hash = hash_password(dados['password'])
    
    # Inserir usuário
    cursor.execute("""
        INSERT INTO usuarios 
        (username, password_hash, tipo, nome_completo, email, telefone, cliente_id, ativo, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s)
        RETURNING id
    """, (
        dados['username'],
        password_hash,
        dados['tipo'],
        dados['nome_completo'],
        dados['email'],
        dados.get('telefone'),
        dados.get('cliente_id'),
        dados.get('created_by')
    ))
    
    result = cursor.fetchone()
    usuario_id = result['id'] if result else None
    if not usuario_id:
        raise ValueError("Erro ao criar usuário")
    conn.commit()
    cursor.close()
    conn.close()
    
    return usuario_id


def autenticar_usuario(username: str, password: str, db) -> Optional[Dict]:
    """
    Autentica um usuário
    
    Returns:
        Dict com dados do usuário se autenticado, None caso contrário
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, password_hash, tipo, nome_completo, email, telefone, 
               ativo, cliente_id
        FROM usuarios 
        WHERE username = %s AND ativo = TRUE
    """, (username,))
    
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not usuario:
        return None
    
    # Verificar senha
    if not verificar_senha(password, usuario['password_hash']):
        return None
    
    # Retornar dados do usuário (sem o hash da senha)
    return {
        'id': usuario['id'],
        'username': usuario['username'],
        'tipo': usuario['tipo'],
        'nome_completo': usuario['nome_completo'],
        'email': usuario['email'],
        'telefone': usuario['telefone'],
        'cliente_id': usuario['cliente_id']
    }


def criar_sessao(usuario_id: int, ip_address: str, user_agent: str, db) -> str:
    """
    Cria uma sessão de login para o usuário
    
    Returns:
        Token da sessão
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Gerar token
    token = gerar_token_sessao()
    
    # Definir expiração (24 horas)
    expira_em = datetime.now() + timedelta(hours=24)
    
    # Inserir sessão
    cursor.execute("""
        INSERT INTO sessoes_login 
        (usuario_id, session_token, ip_address, user_agent, expira_em)
        VALUES (%s, %s, %s, %s, %s)
    """, (usuario_id, token, ip_address, user_agent, expira_em))
    
    # Atualizar último acesso
    cursor.execute("""
        UPDATE usuarios 
        SET ultimo_acesso = CURRENT_TIMESTAMP 
        WHERE id = %s
    """, (usuario_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return token


def validar_sessao(token: str, db) -> Optional[Dict]:
    """
    Valida uma sessão e retorna os dados do usuário
    
    Returns:
        Dict com dados do usuário se sessão válida, None caso contrário
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.usuario_id, s.expira_em, s.ativo,
               u.username, u.tipo, u.nome_completo, u.email, u.cliente_id
        FROM sessoes_login s
        JOIN usuarios u ON s.usuario_id = u.id
        WHERE s.session_token = %s AND s.ativo = TRUE AND u.ativo = TRUE
    """, (token,))
    
    sessao = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not sessao:
        return None
    
    # Verificar expiração
    if sessao['expira_em'] < datetime.now():
        # Sessão expirada - desativar
        invalidar_sessao(token, db)
        return None
    
    return {
        'id': sessao['usuario_id'],
        'username': sessao['username'],
        'tipo': sessao['tipo'],
        'nome_completo': sessao['nome_completo'],
        'email': sessao['email'],
        'cliente_id': sessao['cliente_id']
    }


def invalidar_sessao(token: str, db) -> bool:
    """Invalida uma sessão (logout)"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE sessoes_login 
        SET ativo = FALSE 
        WHERE session_token = %s
    """, (token,))
    
    sucesso = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    
    return sucesso


def listar_usuarios(db, apenas_ativos: bool = True) -> List[Dict]:
    """Lista todos os usuários"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT u.id, u.username, u.tipo, u.nome_completo, u.email, u.telefone,
               u.ativo, u.cliente_id, u.ultimo_acesso, u.created_at,
               c.nome as cliente_nome
        FROM usuarios u
        LEFT JOIN clientes c ON u.cliente_id = c.id
    """
    
    if apenas_ativos:
        query += " WHERE u.ativo = TRUE"
    
    query += " ORDER BY u.tipo, u.nome_completo"
    
    cursor.execute(query)
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(u) for u in usuarios]


def obter_usuario(usuario_id: int, db) -> Optional[Dict]:
    """Obtém dados de um usuário específico"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.id, u.username, u.tipo, u.nome_completo, u.email, u.telefone,
               u.ativo, u.cliente_id, u.ultimo_acesso, u.created_at,
               c.nome as cliente_nome
        FROM usuarios u
        LEFT JOIN clientes c ON u.cliente_id = c.id
        WHERE u.id = %s
    """, (usuario_id,))
    
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return dict(usuario) if usuario else None


def atualizar_usuario(usuario_id: int, dados: Dict, db) -> bool:
    """Atualiza dados de um usuário"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Construir query dinâmica
    campos = []
    valores = []
    
    if 'nome_completo' in dados:
        campos.append("nome_completo = %s")
        valores.append(dados['nome_completo'])
    
    if 'email' in dados:
        campos.append("email = %s")
        valores.append(dados['email'])
    
    if 'telefone' in dados:
        campos.append("telefone = %s")
        valores.append(dados['telefone'])
    
    if 'ativo' in dados:
        campos.append("ativo = %s")
        valores.append(dados['ativo'])
    
    if 'password' in dados:
        campos.append("password_hash = %s")
        valores.append(hash_password(dados['password']))
    
    if not campos:
        return False
    
    campos.append("updated_at = CURRENT_TIMESTAMP")
    valores.append(usuario_id)
    
    query = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = %s"
    cursor.execute(query, valores)
    
    sucesso = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    
    return sucesso


def deletar_usuario(usuario_id: int, db) -> bool:
    """Deleta um usuário (soft delete - apenas desativa)"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE usuarios 
        SET ativo = FALSE, updated_at = CURRENT_TIMESTAMP 
        WHERE id = %s
    """, (usuario_id,))
    
    sucesso = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    
    return sucesso


# ==================== FUNÇÕES DE PERMISSÕES ====================

def listar_permissoes(db, categoria: Optional[str] = None) -> List[Dict]:
    """Lista todas as permissões disponíveis"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    if categoria:
        cursor.execute("""
            SELECT id, codigo, nome, descricao, categoria, ativo
            FROM permissoes
            WHERE categoria = %s AND ativo = TRUE
            ORDER BY categoria, nome
        """, (categoria,))
    else:
        cursor.execute("""
            SELECT id, codigo, nome, descricao, categoria, ativo
            FROM permissoes
            WHERE ativo = TRUE
            ORDER BY categoria, nome
        """)
    
    permissoes = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(p) for p in permissoes]


def obter_permissoes_usuario(usuario_id: int, db) -> List[str]:
    """Retorna lista de códigos de permissões de um usuário"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.codigo
        FROM usuario_permissoes up
        JOIN permissoes p ON up.permissao_id = p.id
        WHERE up.usuario_id = %s AND p.ativo = TRUE
    """, (usuario_id,))
    
    permissoes = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [p['codigo'] for p in permissoes]


def conceder_permissao(usuario_id: int, permissao_codigo: str, concedido_por: int, db) -> bool:
    """Concede uma permissão a um usuário"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Obter ID da permissão
    cursor.execute("SELECT id FROM permissoes WHERE codigo = %s", (permissao_codigo,))
    permissao = cursor.fetchone()
    
    if not permissao:
        cursor.close()
        conn.close()
        return False
    
    # Inserir permissão (ignorar se já existir)
    cursor.execute("""
        INSERT INTO usuario_permissoes (usuario_id, permissao_id, concedido_por)
        VALUES (%s, %s, %s)
        ON CONFLICT (usuario_id, permissao_id) DO NOTHING
    """, (usuario_id, permissao['id'], concedido_por))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return True


def revogar_permissao(usuario_id: int, permissao_codigo: str, db) -> bool:
    """Revoga uma permissão de um usuário"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM usuario_permissoes
        WHERE usuario_id = %s 
        AND permissao_id = (SELECT id FROM permissoes WHERE codigo = %s)
    """, (usuario_id, permissao_codigo))
    
    sucesso = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    
    return sucesso


def sincronizar_permissoes_usuario(usuario_id: int, codigos_permissoes: List[str], concedido_por: int, db) -> bool:
    """
    Sincroniza permissões de um usuário
    Remove permissões não listadas e adiciona novas
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Remover todas as permissões atuais
    cursor.execute("DELETE FROM usuario_permissoes WHERE usuario_id = %s", (usuario_id,))
    
    # Adicionar novas permissões
    for codigo in codigos_permissoes:
        cursor.execute("SELECT id FROM permissoes WHERE codigo = %s", (codigo,))
        permissao = cursor.fetchone()
        
        if permissao:
            cursor.execute("""
                INSERT INTO usuario_permissoes (usuario_id, permissao_id, concedido_por)
                VALUES (%s, %s, %s)
            """, (usuario_id, permissao['id'], concedido_por))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return True


def registrar_log_acesso(usuario_id: int, acao: str, descricao: str, ip_address: str, sucesso: bool, db):
    """Registra um log de acesso/ação do usuário"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO log_acessos (usuario_id, acao, descricao, ip_address, sucesso)
        VALUES (%s, %s, %s, %s, %s)
    """, (usuario_id, acao, descricao, ip_address, sucesso))
    
    conn.commit()
    cursor.close()
    conn.close()
