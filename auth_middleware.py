"""
Middlewares de Autenticação e Autorização
"""
from flask import session, request, jsonify, redirect, url_for
from functools import wraps
import os

# Importar módulo de autenticação dinamicamente baseado no DATABASE_TYPE
USE_POSTGRESQL = os.getenv('DATABASE_TYPE', 'sqlite').lower() == 'postgresql'
if USE_POSTGRESQL:
    import database_postgresql as auth_db
else:
    import auth_functions as auth_db


def get_usuario_logado():
    """
    Retorna dados do usuário logado via session token
    """
    print(f"\n🔍 DEBUG - get_usuario_logado() CHAMADA")
    token = session.get('session_token')
    print(f"   Token na sessão: {'✅ SIM' if token else '❌ NÃO'}")
    
    if not token:
        print(f"   ❌ Sem token na sessão, retornando None\n")
        return None
    
    print(f"   Chamando auth_db.validar_sessao()...")
    usuario = auth_db.validar_sessao(token)
    
    if usuario:
        print(f"   ✅ Usuário retornado de auth_db.validar_sessao():")
        print(f"      - ID: {usuario.get('id')}")
        print(f"      - Username: {usuario.get('username')}")
        print(f"      - 🎯 TIPO: '{usuario.get('tipo')}' (tipo: {type(usuario.get('tipo'))})")
    else:
        print(f"   ❌ auth_db.validar_sessao() retornou None")
    print(f"")
    
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
    Para rotas HTML, redireciona. Para API, retorna JSON.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"\n{'='*80}")
        print(f"🚨 DEBUG - @require_admin DECORADOR ATIVADO")
        print(f"{'='*80}")
        print(f"📍 Rota acessada: {request.path}")
        print(f"📍 Método: {request.method}")
        
        usuario = get_usuario_logado()
        
        print(f"\n👤 Resultado de get_usuario_logado():")
        if usuario:
            print(f"   ✅ Usuário ENCONTRADO:")
            print(f"      - ID: {usuario.get('id')}")
            print(f"      - Username: {usuario.get('username')}")
            print(f"      - 🎯 TIPO: '{usuario.get('tipo')}' (Python type: {type(usuario.get('tipo'))})")
            print(f"      - Nome: {usuario.get('nome_completo')}")
            print(f"\n🔍 Verificação de tipo:")
            print(f"   usuario.get('tipo') = '{usuario.get('tipo')}'")
            print(f"   usuario.get('tipo') != 'admin' = {usuario.get('tipo') != 'admin'}")
            print(f"   usuario.get('tipo') == 'admin' = {usuario.get('tipo') == 'admin'}")
            print(f"   Comparação bytes: {repr(usuario.get('tipo'))} vs {repr('admin')}")
        else:
            print(f"   ❌ Usuário NÃO ENCONTRADO (None)")
        
        if not usuario:
            print(f"\n❌ SEM USUÁRIO - Redirecionando/Retornando erro")
            print(f"{'='*80}\n")
            # Se for uma requisição HTML, redirecionar para login
            if request.path.startswith('/admin') or not request.path.startswith('/api/'):
                return redirect('/login')
            return jsonify({
                'success': False,
                'error': 'Não autenticado',
                'redirect': '/login'
            }), 401
        
        tipo_usuario = usuario.get('tipo')
        print(f"\n🎯 VERIFICAÇÃO CRÍTICA DE ADMIN:")
        print(f"   tipo_usuario = {repr(tipo_usuario)}")
        print(f"   tipo_usuario != 'admin' = {tipo_usuario != 'admin'}")
        
        if tipo_usuario != 'admin':
            print(f"\n🚫 ACESSO NEGADO!")
            print(f"   Tipo do usuário: '{tipo_usuario}' NÃO é 'admin'")
            print(f"   Retornando erro 403")
            print(f"{'='*80}\n")
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
                        <button onclick="window.location.href='/'">Voltar ao Dashboard</button>
                    </div>
                </body>
                </html>
                ''', 403
            return jsonify({
                'success': False,
                'error': 'Acesso negado - Apenas administradores'
            }), 403
        
        print(f"\n✅ ACESSO PERMITIDO!")
        print(f"   Usuário '{usuario.get('username')}' é ADMIN")
        print(f"   Prosseguindo para a função...")
        print(f"{'='*80}\n")
        
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
