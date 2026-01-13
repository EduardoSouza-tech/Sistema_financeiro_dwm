"""
Middlewares de Autenticação e Autorização
Otimizado para PostgreSQL
"""
from flask import session, request, jsonify, redirect, url_for
from functools import wraps
import os

# ============================================================================
# IMPORTAÇÃO DO MÓDULO DE AUTENTICAÇÃO - APENAS POSTGRESQL
# ============================================================================
try:
    import database_postgresql as auth_db
    print("✅ auth_middleware: Usando PostgreSQL")
except Exception as e:
    print(f"❌ Erro ao importar database_postgresql em auth_middleware: {e}")
    raise


def get_usuario_logado():
    """
    Retorna dados do usuário logado via session token
    """
    token = session.get('session_token')
    
    if not token:
        return None
    
    usuario = auth_db.validar_sessao(token)
    return usuario


def require_auth(f):
    """
    Decorador que requer autenticação
    Redireciona para login se não autenticado
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"🔐 [require_auth] Verificando autenticação para: {request.path}")
        usuario = get_usuario_logado()
        print(f"🔐 [require_auth] Usuário obtido: {usuario.get('username') if usuario else 'None'}")
        
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
    Para rotas HTML, redireciona. Para API, retorna JSON.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario = get_usuario_logado()
        
        if not usuario:
            # Se for uma requisição HTML, redirecionar para login
            if request.path.startswith('/admin') or not request.path.startswith('/api/'):
                return redirect('/login')
            return jsonify({
                'success': False,
                'error': 'Não autenticado',
                'redirect': '/login'
            }), 401
        
        # Verificar se é admin (normalizado)
        tipo_normalizado = usuario.get('tipo', '').strip().lower()
        
        if tipo_normalizado != 'admin':
            # Se for uma requisição HTML, retornar erro HTML
            if request.path.startswith('/admin') or not request.path.startswith('/api/'):
                return '''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Acesso Negado</title>
                    <style>
                        body { font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }
                        .container { text-align: center; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        h1 { color: #e74c3c; }
                        button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-top: 20px; }
                        button:hover { background: #2980b9; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🚫 Acesso Negado</h1>
                        <p>Apenas administradores podem acessar esta página.</p>
                        <button onclick=\"window.location.href='/'\">Voltar ao Dashboard</button>
                    </div>
                </body>
                </html>
                ''', 403
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
            if usuario.get('tipo') == 'admin':
                request.usuario = usuario
                return f(*args, **kwargs)
            
            # Verificar se o usuário tem a permissão
            permissoes = auth_db.obter_permissoes_usuario(usuario['id'])
            
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
    if usuario.get('tipo') == 'admin':
        return query_result
    
    if not usuario.get('cliente_id'):
        return []  # Cliente sem cliente_id associado não vê nada
    
    # Filtrar apenas registros onde cliente_id corresponde
    return [
        item for item in query_result 
        if item.get('cliente_id') == usuario['cliente_id']
    ]


def aplicar_filtro_cliente(f):
    """
    Decorador que adiciona filtro automático de cliente ao request
    
    - Admin: Sem filtros (vê tudo)
    - Cliente: Filtro automático por cliente_id
    
    Uso:
        @app.route('/api/recurso')
        @require_auth
        @aplicar_filtro_cliente
        def listar_recurso():
            # request.filtro_cliente_id estará disponível
            # None para admin, ID do cliente para clientes
            pass
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
        
        # Definir filtro de cliente
        if usuario['tipo'] == 'admin':
            request.filtro_cliente_id = None  # Admin vê tudo
            print(f"   🔓 Admin: SEM filtros (acesso total)")
        else:
            request.filtro_cliente_id = usuario.get('cliente_id')
            print(f"   🔒 Cliente ID {request.filtro_cliente_id}: Apenas dados próprios")
        
        # Adicionar usuário ao request
        request.usuario = usuario
        
        return f(*args, **kwargs)
    
    return decorated_function
