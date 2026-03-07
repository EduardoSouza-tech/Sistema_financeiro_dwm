"""
Middlewares de Autenticacao e Autorizacao
Otimizado para PostgreSQL
"""
from flask import session, request, jsonify, redirect, url_for
from functools import wraps
import os
import sys

# Forcar saida imediata de logs
def log(msg):
    """Print que forca flush imediato"""
    print(msg, file=sys.stderr, flush=True)

# ============================================================================
# IMPORTACAO DO MODULO DE AUTENTICACAO - APENAS POSTGRESQL
# ============================================================================
try:
    import database_postgresql as auth_db
    log("auth_middleware: Usando PostgreSQL")
except Exception as e:
    log(f"Erro ao importar database_postgresql em auth_middleware: {e}")
    raise


def get_usuario_logado():
    """
    Retorna dados do usuario logado via session token
    """
    try:
        token = session.get('session_token')
        
        if not token:
            log("[get_usuario_logado] Sem token na sessao")
            return None
        
        log(f"[get_usuario_logado] Validando token: {token[:20]}...")
        usuario = auth_db.validar_sessao(token)
        log(f"[get_usuario_logado] Usuario validado: {usuario.get('username') if usuario else 'None'}")
        return usuario
    except Exception as e:
        log(f"[get_usuario_logado] Erro: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def require_auth(f):
    """
    Decorador que requer autenticacao
    Redireciona para login se nao autenticado
    
    Multi-Empresa:
    - Valida empresa_id na sessão
    - Verifica se usuário tem acesso à empresa
    - Carrega permissões específicas da empresa
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            log(f"[require_auth] Verificando autenticacao para: {request.path}")
            usuario = get_usuario_logado()
            log(f"[require_auth] Usuario obtido: {usuario.get('username') if usuario else 'None'}")
            
            if not usuario:
                log("[require_auth] Acesso negado - sem usuario")
                return jsonify({
                    'success': False,
                    'error': 'Nao autenticado',
                    'redirect': '/login'
                }), 401
            
            # ============================================================
            # VALIDAÇÃO MULTI-EMPRESA
            # ============================================================
            # MULTI-ABA: Ler empresa_id do header X-Empresa-ID enviado pelo frontend
            # (cada aba do browser mantém seu próprio empresa_id no sessionStorage e
            # envia via header, evitando que uma aba sobrescreva o estado de outra via
            # o cookie de sessão compartilhado).  Fallback para session cookie.
            _header_empresa = request.headers.get('X-Empresa-ID')
            _empresa_id_header = int(_header_empresa) if _header_empresa and _header_empresa.isdigit() else None

            if usuario['tipo'] != 'admin':
                # Usuários normais precisam ter empresa selecionada
                # Prioridade: header da aba → session cookie → empresa padrão
                empresa_id = _empresa_id_header or session.get('empresa_id')

                if not empresa_id:
                    log(f"[require_auth] Usuario {usuario['username']} sem empresa na sessao")
                    # Tentar obter empresa padrão
                    from auth_functions import obter_empresa_padrao
                    empresa_id = obter_empresa_padrao(usuario['id'], auth_db)

                    if empresa_id:
                        session['empresa_id'] = empresa_id
                        log(f"[require_auth] Empresa padrao definida na sessao: {empresa_id}")
                    else:
                        log("[require_auth] Usuario nao possui empresa - precisa selecionar")
                        return jsonify({
                            'success': False,
                            'error': 'Selecione uma empresa para continuar',
                            'requireEmpresaSelection': True
                        }), 403

                # Validar se usuário tem acesso à empresa
                from auth_functions import tem_acesso_empresa
                if not tem_acesso_empresa(usuario['id'], empresa_id, auth_db):
                    log(f"[require_auth] Usuario {usuario['username']} sem acesso a empresa {empresa_id}")
                    # NÃO apagar da sessão: pode ser só esta aba com empresa_id inválido
                    return jsonify({
                        'success': False,
                        'error': 'Acesso negado a esta empresa',
                        'requireEmpresaSelection': True
                    }), 403

                # Carregar permissões específicas da empresa
                from auth_functions import obter_permissoes_usuario_empresa
                permissoes = obter_permissoes_usuario_empresa(usuario['id'], empresa_id, auth_db)
                usuario['permissoes'] = permissoes
                usuario['empresa_id'] = empresa_id

                log(f"[require_auth] Empresa validada: {empresa_id} (via {'header' if _empresa_id_header else 'session'}), Permissoes: {len(permissoes)}")
            else:
                # Super admin tem acesso a todas as empresas
                usuario['permissoes'] = ['*']  # Todas as permissões
                empresa_id = _empresa_id_header or session.get('empresa_id')
                if empresa_id:
                    usuario['empresa_id'] = empresa_id
                log(f"[require_auth] Super admin com acesso total")
            
            # ============================================================
            # Adicionar dados do usuario ao request
            request.usuario = usuario
            log(f"[require_auth] Autenticacao OK - Chamando {f.__name__}")
            return f(*args, **kwargs)
        except Exception as e:
            log(f"[require_auth] EXCECAO: {e}")
            import traceback
            traceback.print_exc(file=sys.stderr)
            return jsonify({'error': 'Erro de autenticação', 'details': str(e)}), 500
    
    return decorated_function


def require_admin(f):
    """
    Decorador que requer permissões de administrador
    Para rotas HTML, redireciona. Para API, retorna JSON.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            print(f"\n🔒 [require_admin] Verificando acesso admin para {request.path}")
            
            usuario = get_usuario_logado()
            
            if not usuario:
                print(f"   ❌ Usuário não autenticado")
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
            print(f"   👤 Usuário: {usuario.get('username')} - Tipo: {tipo_normalizado}")
            
            if tipo_normalizado != 'admin':
                print(f"   ❌ Acesso negado - não é admin")
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
            print(f"   ✅ Acesso autorizado - chamando função...")
            request.usuario = usuario
            result = f(*args, **kwargs)
            print(f"   ✅ Função executada com sucesso")
            return result
            
        except Exception as e:
            print(f"\n❌ ERRO em require_admin:")
            print(f"   Tipo: {type(e).__name__}")
            print(f"   Mensagem: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500
    
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
            print(f"🔒 [PERMISSION CHECK] Verificando permissão: {permission_code}")
            print(f"🔒 [PERMISSION CHECK] Função: {f.__name__}")
            usuario = get_usuario_logado()
            print(f"🔒 [PERMISSION CHECK] Usuário: {usuario.get('username') if usuario else 'NENHUM'}")
            
            if not usuario:
                print(f"❌ [PERMISSION CHECK] Usuário não autenticado!")
                return jsonify({
                    'success': False,
                    'error': 'Não autenticado',
                    'redirect': '/login'
                }), 401
            
            # Admin tem todas as permissões
            if usuario.get('tipo') == 'admin':
                print(f"✅ [PERMISSION CHECK] Admin - permissão concedida!")
                request.usuario = usuario
                return f(*args, **kwargs)
            
            # 🔒 MULTI-TENANT: Verificar permissões da empresa
            empresa_id = session.get('empresa_id')
            print(f"🔒 [PERMISSION CHECK] empresa_id da sessão: {empresa_id}")
            
            if not empresa_id:
                print(f"❌ [PERMISSION CHECK] Empresa não selecionada!")
                return jsonify({
                    'success': False,
                    'error': 'Empresa não selecionada'
                }), 403
            
            # Buscar permissões da empresa (não permissões globais)
            from auth_functions import obter_permissoes_usuario_empresa
            permissoes = obter_permissoes_usuario_empresa(usuario['id'], empresa_id, auth_db)
            print(f"🔒 [PERMISSION CHECK] Permissões da empresa {empresa_id}: {len(permissoes)} itens")
            print(f"🔒 [PERMISSION CHECK] Verificando se '{permission_code}' está em: {permissoes[:10]}..." if len(permissoes) > 10 else f"🔒 [PERMISSION CHECK] Permissões: {permissoes}")
            
            if permission_code not in permissoes:
                print(f"❌ [PERMISSION CHECK] Permissão negada!")
                return jsonify({
                    'success': False,
                    'error': f'Permissão negada - Você não tem acesso a: {permission_code}'
                }), 403
            
            print(f"✅ [PERMISSION CHECK] Permissão concedida!")
            
            request.usuario = usuario
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def filtrar_por_cliente(query_result, usuario):
    """
    Filtra resultados de query para mostrar apenas dados da empresa do usuário
    Admin vê tudo, usuário normal vê apenas dados da sua empresa
    
    Args:
        query_result: Lista de dicts com resultados da query
        usuario: Dict com dados do usuário logado
    
    Returns:
        Lista filtrada
    """
    if usuario.get('tipo') == 'admin':
        return query_result
    
    if not usuario.get('empresa_id'):
        return []  # Usuário sem empresa_id associado não vê nada
    
    # Filtrar apenas registros onde empresa_id corresponde
    return [
        item for item in query_result 
        if item.get('empresa_id') == usuario['empresa_id']
    ]


def aplicar_filtro_cliente(f):
    """
    Decorador que adiciona filtro automático de empresa ao request
    
    - Admin: Sem filtros (vê tudo)
    - Usuário: Filtro automático por empresa_id
    
    Uso:
        @app.route('/api/recurso')
        @require_auth
        @aplicar_filtro_cliente
        def listar_recurso():
            # request.filtro_cliente_id estará disponível
            # None para admin, ID da empresa para usuários normais
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
        
        # Definir filtro de empresa
        if usuario['tipo'] == 'admin':
            request.filtro_cliente_id = None  # Admin vê tudo
            print(f"   🔓 Admin: SEM filtros (acesso total)")
        else:
            request.filtro_cliente_id = usuario.get('empresa_id') or usuario.get('cliente_id')  # Fallback temporário
            print(f"   🔒 Empresa ID {request.filtro_cliente_id}: Apenas dados próprios")
        
        # Adicionar usuário ao request
        request.usuario = usuario
        
        return f(*args, **kwargs)
    
    return decorated_function
