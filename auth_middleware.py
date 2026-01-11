"""
Middlewares de Autenticação e Autorização
"""
from flask import session, request, jsonify
from functools import wraps
import database_postgresql


def get_usuario_logado():
    """
    Retorna dados do usuário logado via session token
    """
    token = session.get('session_token')
    if not token:
        return None
    
    usuario = database_postgresql.validar_sessao(token)
    return usuario


def require_auth(f):
    """
    Decorador que requer autenticação
    Redireciona para login se não autenticado
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario = get_usuario_logado()
        
        if not usuario:
            return jsonify({
                'success': False,
                'error': 'Não autenticado',
                'redirect': '/login'
            }), 401
        
        # Adicionar dados do usuário ao request
        request.usuario = usuario
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """
    Decorador que requer permissões de administrador
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario = get_usuario_logado()
        
        if not usuario:
            return jsonify({
                'success': False,
                'error': 'Não autenticado',
                'redirect': '/login'
            }), 401
        
        if usuario['tipo'] != 'admin':
            return jsonify({
                'success': False,
                'error': 'Acesso negado - Apenas administradores'
            }), 403
        
        # Adicionar dados do usuário ao request
        request.usuario = usuario
        return f(*args, **kwargs)
    
    return decorated_function


def require_permission(permission_code: str):
    """
    Decorador que requer uma permissão específica
    
    Uso:
        @require_permission('lancamentos_create')
        def criar_lancamento():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            usuario = get_usuario_logado()
            
            if not usuario:
                return jsonify({
                    'success': False,
                    'error': 'Não autenticado',
                    'redirect': '/login'
                }), 401
            
            # Admin tem todas as permissões
            if usuario['tipo'] == 'admin':
                request.usuario = usuario
                return f(*args, **kwargs)
            
            # Verificar se o usuário tem a permissão
            permissoes = database_postgresql.obter_permissoes_usuario(usuario['id'])
            
            if permission_code not in permissoes:
                return jsonify({
                    'success': False,
                    'error': f'Permissão negada - Você não tem acesso a: {permission_code}'
                }), 403
            
            request.usuario = usuario
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def filtrar_por_cliente(query_result, usuario):
    """
    Filtra resultados de query para mostrar apenas dados do cliente logado
    Admin vê tudo, cliente vê apenas seus dados
    
    Args:
        query_result: Lista de dicts com resultados da query
        usuario: Dict com dados do usuário logado
    
    Returns:
        Lista filtrada
    """
    if usuario['tipo'] == 'admin':
        return query_result
    
    if not usuario.get('cliente_id'):
        return []  # Cliente sem cliente_id associado não vê nada
    
    # Filtrar apenas registros onde cliente_id corresponde
    return [
        item for item in query_result 
        if item.get('cliente_id') == usuario['cliente_id']
    ]
