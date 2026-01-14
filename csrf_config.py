"""
Configuração de CSRF Protection
Protege contra ataques Cross-Site Request Forgery
"""
from flask_wtf.csrf import CSRFProtect, generate_csrf
from functools import wraps
from flask import request, jsonify
import os

# Instância global do CSRFProtect
csrf = CSRFProtect()

def init_csrf(app):
    """
    Inicializa CSRF Protection no Flask app
    
    Args:
        app: Instância do Flask
        
    Returns:
        CSRFProtect: Instância configurada
    """
    # Configurações de CSRF
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # Tokens não expiram
    app.config['WTF_CSRF_SSL_STRICT'] = bool(os.getenv('RAILWAY_ENVIRONMENT'))  # Strict em produção
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    
    # Métodos que requerem CSRF token
    app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Headers permitidos para CSRF (além do padrão X-CSRFToken)
    app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']
    
    # Inicializar CSRF
    csrf.init_app(app)
    
    # Isentar rotas de API mobile (que usam JWT)
    csrf.exempt('api.mobile_login')
    csrf.exempt('api.mobile_refresh_token')
    
    print("✅ CSRF Protection ativado")
    print(f"   - SSL Strict: {app.config['WTF_CSRF_SSL_STRICT']}")
    print(f"   - Métodos protegidos: {app.config['WTF_CSRF_METHODS']}")
    
    return csrf


def csrf_exempt(view_func):
    """
    Decorator para isentar uma rota específica de CSRF
    Usar apenas para APIs públicas que não modificam dados
    
    Exemplo:
        @app.route('/api/public/data')
        @csrf_exempt
        def public_data():
            return jsonify({'data': 'public'})
    """
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Marca função para ser isenta
    wrapped_view._csrf_exempt = True
    return wrapped_view


def get_csrf_token():
    """
    Gera um novo CSRF token
    
    Returns:
        str: CSRF token para uso em formulários
    """
    return generate_csrf()


def inject_csrf_token():
    """
    Injeta CSRF token em todos os templates automaticamente
    Deve ser registrado como context_processor
    
    Uso no Flask:
        @app.context_processor
        def inject_csrf():
            return inject_csrf_token()
    """
    return dict(csrf_token=generate_csrf)


def validate_csrf_ajax(f):
    """
    Decorator customizado para validar CSRF em requisições AJAX
    Verifica o header X-CSRFToken
    
    Uso:
        @app.route('/api/data', methods=['POST'])
        @validate_csrf_ajax
        def ajax_endpoint():
            return jsonify({'success': True})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Se CSRF estiver desabilitado globalmente, pular verificação
        if not csrf._get_config('WTF_CSRF_ENABLED', default=True):
            return f(*args, **kwargs)
        
        # Verificar se é uma requisição que requer CSRF
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Tentar obter token do header
            token = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token')
            
            if not token:
                # Tentar obter do corpo JSON
                if request.is_json:
                    token = request.json.get('csrf_token')
                # Tentar obter de form data
                else:
                    token = request.form.get('csrf_token')
            
            if not token:
                return jsonify({
                    'success': False,
                    'error': 'CSRF token missing',
                    'message': 'Token CSRF ausente. Recarregue a página.'
                }), 400
            
            # Validar token (flask-wtf faz a validação automaticamente)
            # Se chegou aqui e o decorator @csrf.exempt não foi usado,
            # o flask-wtf já validou o token
        
        return f(*args, **kwargs)
    
    return decorated_function


# ============================================================================
# ERROR HANDLERS PARA CSRF
# ============================================================================

def register_csrf_error_handlers(app):
    """
    Registra handlers de erro específicos para CSRF
    
    Args:
        app: Instância do Flask
    """
    from flask_wtf.csrf import CSRFError
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """Handler para erros de CSRF"""
        # Se for requisição AJAX/API
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'CSRF validation failed',
                'message': 'Token CSRF inválido ou expirado. Recarregue a página.',
                'code': 'CSRF_ERROR'
            }), 400
        
        # Se for requisição HTML normal
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Erro de Segurança</title>
            <style>
                body { font-family: Arial; padding: 50px; text-align: center; }
                .error-box { 
                    background: #fee; 
                    border: 2px solid #c00; 
                    padding: 30px; 
                    border-radius: 10px;
                    max-width: 500px;
                    margin: 0 auto;
                }
                h1 { color: #c00; }
                button {
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    margin-top: 20px;
                }
                button:hover { background: #5568d3; }
            </style>
        </head>
        <body>
            <div class="error-box">
                <h1>🛡️ Erro de Segurança</h1>
                <p><strong>Token CSRF inválido ou expirado</strong></p>
                <p>Por favor, recarregue a página e tente novamente.</p>
                <button onclick="window.location.reload()">🔄 Recarregar Página</button>
            </div>
        </body>
        </html>
        ''', 400
    
    print("✅ CSRF error handlers registrados")


# ============================================================================
# UTILITÁRIOS
# ============================================================================

def get_csrf_header_name():
    """Retorna o nome do header CSRF configurado"""
    return 'X-CSRFToken'


def create_csrf_meta_tag():
    """
    Cria uma meta tag HTML com o CSRF token
    Para uso em templates que não usam Jinja2
    
    Returns:
        str: Meta tag HTML
    """
    token = generate_csrf()
    return f'<meta name="csrf-token" content="{token}">'


# ============================================================================
# INFORMAÇÕES
# ============================================================================

def get_csrf_info():
    """
    Retorna informações sobre a configuração de CSRF
    Útil para debugging
    
    Returns:
        dict: Informações de configuração
    """
    return {
        'enabled': csrf._get_config('WTF_CSRF_ENABLED', default=True),
        'ssl_strict': csrf._get_config('WTF_CSRF_SSL_STRICT', default=False),
        'time_limit': csrf._get_config('WTF_CSRF_TIME_LIMIT', default=None),
        'methods': csrf._get_config('WTF_CSRF_METHODS', default=['POST', 'PUT', 'PATCH', 'DELETE']),
        'header_name': get_csrf_header_name()
    }
