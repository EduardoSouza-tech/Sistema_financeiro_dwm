"""
Funções de Autenticação e Autorização
"""
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Importação opcional do bcrypt (para compatibilidade durante deploy)
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
    print("✅ bcrypt disponível - usando hash seguro")
except ImportError:
    BCRYPT_AVAILABLE = False
    print("⚠️ bcrypt não disponível - usando SHA-256 (menos seguro)")


def hash_password(password: str) -> str:
    """
    Gera hash da senha
    Usa bcrypt se disponível, senão SHA-256
    """
    if BCRYPT_AVAILABLE:
        # bcrypt é mais seguro que SHA-256 pois:
        # - Usa salt automático (proteção contra rainbow tables)
        # - É computacionalmente caro (proteção contra brute force)
        # - Especificamente projetado para senhas
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    else:
        # Fallback para SHA-256
        return hashlib.sha256(password.encode()).hexdigest()


def verificar_senha(password: str, password_hash: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    try:
        if BCRYPT_AVAILABLE and len(password_hash) > 64:
            # Hash bcrypt (maior que 64 caracteres)
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        else:
            # Hash SHA-256 (64 caracteres)
            sha256_hash = hashlib.sha256(password.encode()).hexdigest()
            return sha256_hash == password_hash
    except Exception:
        # Fallback para SHA-256
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        return sha256_hash == password_hash


def validar_senha_forte(senha: str) -> tuple[bool, str]:
    """
    Valida se a senha atende aos requisitos de segurança
    
    Returns:
        (bool, str): (válida?, mensagem de erro)
    """
    if len(senha) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres"
    
    if not re.search(r'[A-Z]', senha):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', senha):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not re.search(r'[0-9]', senha):
        return False, "Senha deve conter pelo menos um número"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        return False, "Senha deve conter pelo menos um caractere especial"
    
    return True, "OK"


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
            'empresa_id': int (obrigatório se tipo='cliente'),
            'cliente_id': int (aceito como sinônimo de empresa_id para compatibilidade),
            'created_by': int (id do admin que está criando)
        }
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Validar empresa_id (obrigatório para usuários normais)
    if dados['tipo'] == 'cliente':
        empresa_id = dados.get('empresa_id') or dados.get('cliente_id')
        if not empresa_id:
            raise ValueError("empresa_id é obrigatório para usuários do tipo 'cliente'")
        # Garantir que empresa_id está em dados
        dados['empresa_id'] = empresa_id
    
    # Validações
    if dados['tipo'] not in ['admin', 'cliente']:
        raise ValueError("Tipo de usuário inválido. Use 'admin' ou 'cliente'")
    
    # Nota: cliente_id pode ser NULL inicialmente para usuários tipo 'cliente'
    # Será vinculado automaticamente quando o primeiro cliente for criado por este usuário
    
    # Verificar se username ou email já existem
    cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE username = %s OR email = %s",
                  (dados['username'], dados['email']))
    result = cursor.fetchone()
    if result and result['count'] > 0:
        raise ValueError("Username ou email já cadastrado")
    
    # Hash da senha
    password_hash = hash_password(dados['password'])
    
    # Determinar empresa_id (usar cliente_id como fallback para compatibilidade)
    empresa_id = dados.get('empresa_id') or dados.get('cliente_id')
    
    # Inserir usuário
    cursor.execute("""
        INSERT INTO usuarios 
        (username, password_hash, tipo, nome_completo, email, telefone, empresa_id, ativo, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s)
        RETURNING id
    """, (
        dados['username'],
        password_hash,
        dados['tipo'],
        dados['nome_completo'],
        dados['email'],
        dados.get('telefone'),
        empresa_id,
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
    
    # Verificar se conta está bloqueada por tentativas
    if verificar_conta_bloqueada(username, db):
        conn.close()
        return None
    
    cursor.execute("""
        SELECT id, username, password_hash, tipo, nome_completo, email, telefone, 
               ativo, cliente_id
        FROM usuarios 
        WHERE username = %s AND ativo = TRUE
    """, (username,))
    
    usuario = cursor.fetchone()
    
    if not usuario:
        cursor.close()
        conn.close()
        return None
    
    # Verificar senha
    senha_correta = verificar_senha(password, usuario['password_hash'])
    
    if not senha_correta:
        # Registrar tentativa falha
        registrar_tentativa_login(username, False, db)
        cursor.close()
        conn.close()
        return None
    
    # Senha correta - limpar tentativas falhas
    limpar_tentativas_login(username, db)
    
    # Verificar se é hash antigo (SHA-256) e atualizar para bcrypt (apenas se bcrypt disponível)
    if BCRYPT_AVAILABLE and len(usuario['password_hash']) == 64:  # SHA-256 tem 64 caracteres
        novo_hash = hash_password(password)
        cursor.execute("""
            UPDATE usuarios SET password_hash = %s WHERE id = %s
        """, (novo_hash, usuario['id']))
        conn.commit()
    
    cursor.close()
    conn.close()
    
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
               u.ativo, u.empresa_id, u.ultimo_acesso, u.created_at,
               e.razao_social as empresa_nome
        FROM usuarios u
        LEFT JOIN empresas e ON u.empresa_id = e.id
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
               u.ativo, u.empresa_id, u.ultimo_acesso, u.created_at,
               e.razao_social as empresa_nome
        FROM usuarios u
        LEFT JOIN empresas e ON u.empresa_id = e.id
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


# ==================== CONTROLE DE TENTATIVAS DE LOGIN ====================

def registrar_tentativa_login(username: str, sucesso: bool, db):
    """Registra uma tentativa de login"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Criar tabela se não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            sucesso BOOLEAN NOT NULL,
            tentativa_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(50)
        )
    """)
    
    cursor.execute("""
        INSERT INTO login_attempts (username, sucesso)
        VALUES (%s, %s)
    """, (username, sucesso))
    
    conn.commit()
    cursor.close()
    conn.close()


def verificar_conta_bloqueada(username: str, db) -> bool:
    """
    Verifica se a conta está bloqueada por excesso de tentativas
    Bloqueia após 5 tentativas falhadas em 15 minutos
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Criar tabela se não existir
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                sucesso BOOLEAN NOT NULL,
                tentativa_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(50)
            )
        """)
        conn.commit()
    except Exception:
        pass  # Tabela já existe
    
    # Verificar tentativas nos últimos 15 minutos
    try:
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM login_attempts
            WHERE username = %s 
            AND sucesso = FALSE
            AND tentativa_em > NOW() - INTERVAL '15 minutes'
        """, (username,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result['count'] >= 5:
            return True
    except Exception as e:
        print(f"⚠️ Erro ao verificar bloqueio: {e}")
        cursor.close()
        conn.close()
    
    return False


def limpar_tentativas_login(username: str, db):
    """Limpa as tentativas de login após sucesso"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Criar tabela se não existir
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                sucesso BOOLEAN NOT NULL,
                tentativa_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(50)
            )
        """)
        conn.commit()
    except Exception:
        pass
    
    try:
        cursor.execute("""
            DELETE FROM login_attempts
            WHERE username = %s
        """, (username,))
        
        conn.commit()
    except Exception as e:
        print(f"⚠️ Erro ao limpar tentativas: {e}")
    finally:
        cursor.close()
        conn.close()


# ===================================================================
# FUNÇÕES MULTI-EMPRESA (Usuário com Acesso a Múltiplas Empresas)
# ===================================================================

def listar_empresas_usuario(usuario_id: int, db) -> List[Dict]:
    """
    Lista todas as empresas que um usuário tem acesso
    
    Retorna lista de dicts com:
    - id, razao_social, cnpj, papel, permissoes_empresa, is_empresa_padrao, ativo
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                e.id,
                e.razao_social,
                e.cnpj,
                e.ativo as empresa_ativa,
                ue.papel,
                ue.permissoes_empresa,
                ue.is_empresa_padrao,
                ue.ativo as acesso_ativo,
                ue.criado_em,
                ue.atualizado_em
            FROM empresas e
            JOIN usuario_empresas ue ON e.id = ue.empresa_id
            WHERE ue.usuario_id = %s
            AND ue.ativo = TRUE
            AND e.ativo = TRUE
            ORDER BY ue.is_empresa_padrao DESC, e.razao_social
        """, (usuario_id,))
        
        empresas = cursor.fetchall()
        return [dict(e) for e in empresas]
        
    finally:
        cursor.close()
        conn.close()


def vincular_usuario_empresa(usuario_id: int, empresa_id: int, papel: str, 
                             permissoes: List[str], is_padrao: bool, 
                             criado_por: int, db) -> int:
    """
    Vincula um usuário a uma empresa
    
    Args:
        usuario_id: ID do usuário
        empresa_id: ID da empresa
        papel: 'admin_empresa', 'usuario', 'visualizador'
        permissoes: Lista de códigos de permissões
        is_padrao: Se é a empresa padrão do usuário
        criado_por: ID do admin que está criando
        
    Returns:
        ID do vínculo criado
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Se é empresa padrão, desmarcar outras
        if is_padrao:
            cursor.execute("""
                UPDATE usuario_empresas
                SET is_empresa_padrao = FALSE
                WHERE usuario_id = %s
            """, (usuario_id,))
        
        # Inserir vínculo
        cursor.execute("""
            INSERT INTO usuario_empresas 
                (usuario_id, empresa_id, papel, permissoes_empresa, 
                 is_empresa_padrao, ativo, criado_por)
            VALUES (%s, %s, %s, %s, %s, TRUE, %s)
            ON CONFLICT (usuario_id, empresa_id)
            DO UPDATE SET
                papel = EXCLUDED.papel,
                permissoes_empresa = EXCLUDED.permissoes_empresa,
                is_empresa_padrao = EXCLUDED.is_empresa_padrao,
                ativo = TRUE,
                atualizado_em = CURRENT_TIMESTAMP
            RETURNING id
        """, (usuario_id, empresa_id, papel, 
              str(permissoes).replace("'", '"'),  # Converter para JSON
              is_padrao, criado_por))
        
        result = cursor.fetchone()
        vinculo_id = result['id'] if result else None
        
        conn.commit()
        return vinculo_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def remover_usuario_empresa(usuario_id: int, empresa_id: int, db) -> bool:
    """Remove vínculo de usuário com empresa"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE usuario_empresas
            SET ativo = FALSE,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE usuario_id = %s AND empresa_id = %s
        """, (usuario_id, empresa_id))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao remover vínculo: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def atualizar_usuario_empresa(usuario_id: int, empresa_id: int, 
                              papel: str = None, permissoes: List[str] = None,
                              is_padrao: bool = None, db = None) -> bool:
    """Atualiza dados do vínculo usuário-empresa"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if papel is not None:
            updates.append("papel = %s")
            params.append(papel)
            
        if permissoes is not None:
            updates.append("permissoes_empresa = %s")
            params.append(str(permissoes).replace("'", '"'))
            
        if is_padrao is not None:
            if is_padrao:
                # Desmarcar outras empresas
                cursor.execute("""
                    UPDATE usuario_empresas
                    SET is_empresa_padrao = FALSE
                    WHERE usuario_id = %s
                """, (usuario_id,))
            
            updates.append("is_empresa_padrao = %s")
            params.append(is_padrao)
        
        if not updates:
            return False
        
        updates.append("atualizado_em = CURRENT_TIMESTAMP")
        params.extend([usuario_id, empresa_id])
        
        query = f"""
            UPDATE usuario_empresas
            SET {', '.join(updates)}
            WHERE usuario_id = %s AND empresa_id = %s
        """
        
        cursor.execute(query, params)
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao atualizar vínculo: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def tem_acesso_empresa(usuario_id: int, empresa_id: int, db) -> bool:
    """Verifica se usuário tem acesso à empresa"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM usuario_empresas
            WHERE usuario_id = %s 
            AND empresa_id = %s 
            AND ativo = TRUE
        """, (usuario_id, empresa_id))
        
        result = cursor.fetchone()
        return result['count'] > 0 if result else False
        
    finally:
        cursor.close()
        conn.close()


def obter_empresa_padrao(usuario_id: int, db) -> Optional[int]:
    """Retorna o ID da empresa padrão do usuário"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT empresa_id
            FROM usuario_empresas
            WHERE usuario_id = %s 
            AND is_empresa_padrao = TRUE
            AND ativo = TRUE
            LIMIT 1
        """, (usuario_id,))
        
        result = cursor.fetchone()
        return result['empresa_id'] if result else None
        
    finally:
        cursor.close()
        conn.close()


def obter_permissoes_usuario_empresa(usuario_id: int, empresa_id: int, db) -> List[str]:
    """Retorna lista de permissões do usuário em uma empresa específica"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT permissoes_empresa
            FROM usuario_empresas
            WHERE usuario_id = %s 
            AND empresa_id = %s 
            AND ativo = TRUE
        """, (usuario_id, empresa_id))
        
        result = cursor.fetchone()
        if result and result['permissoes_empresa']:
            # Converter JSONB para lista Python
            import json
            return json.loads(result['permissoes_empresa']) if isinstance(result['permissoes_empresa'], str) else result['permissoes_empresa']
        return []
        
    finally:
        cursor.close()
        conn.close()
