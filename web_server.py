"""
Servidor Web para o Sistema Financeiro
Otimizado para PostgreSQL com pool de conexões
"""
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import os
import sys

# ============================================================================
# LOGGING E MONITORAMENTO
# ============================================================================
from logger_config import setup_logging, get_logger, log_request, log_error
from sentry_config import init_sentry, set_user_context, clear_user_context, add_breadcrumb, capture_exception

# ============================================================================
# CSRF PROTECTION
# ============================================================================
from csrf_config import init_csrf, csrf, inject_csrf_token, register_csrf_error_handlers

# ============================================================================
# MOBILE DETECTION
# ============================================================================
from mobile_config import is_mobile_device, get_device_info

# Configurar logging estruturado
logger = setup_logging(
    app_name='sistema_financeiro',
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
    enable_json=bool(os.getenv('RAILWAY_ENVIRONMENT'))  # JSON em produção
)

# Inicializar Sentry em produção
SENTRY_ENABLED = init_sentry(
    environment='production' if os.getenv('RAILWAY_ENVIRONMENT') else 'development',
    traces_sample_rate=0.1  # 10% das transações
)

logger.info("="*80)
logger.info("Sistema de logging e monitoramento inicializado")
logger.info(f"Sentry: {'✅ Ativo' if SENTRY_ENABLED else '⚠️  Desabilitado'}")
logger.info("="*80)

# Importação opcional do flask-limiter (para compatibilidade durante deploy)
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
    print("✅ Flask-Limiter carregado")
except ImportError:
    LIMITER_AVAILABLE = False
    print("⚠️ Flask-Limiter não disponível - Rate limiting desabilitado")

# ============================================================================
# IMPORTAÇÕES DO BANCO DE DADOS - APENAS POSTGRESQL
# ============================================================================
try:
    import database_postgresql as database
    import database_postgresql as auth_db
    from database_postgresql import DatabaseManager, get_db_connection
    from database_postgresql import pagar_lancamento as db_pagar_lancamento
    from database_postgresql import cancelar_lancamento as db_cancelar_lancamento
    from database_postgresql import obter_lancamento as db_obter_lancamento
    from database_postgresql import atualizar_cliente, atualizar_fornecedor
    print("✅ Módulo PostgreSQL carregado com sucesso")
except Exception as e:
    print(f"❌ ERRO CRÍTICO: Não foi possível carregar o módulo PostgreSQL")
    print(f"   Erro: {e}")
    print(f"   Certifique-se de que DATABASE_URL está configurado")
    raise

from auth_middleware import require_auth, require_admin, require_permission, get_usuario_logado, filtrar_por_cliente, aplicar_filtro_cliente
from database_postgresql import ContaBancaria, Lancamento, Categoria, TipoLancamento, StatusLancamento
from decimal import Decimal
from datetime import datetime, date, timedelta
import json
import os
import secrets
import time

app = Flask(__name__, static_folder='static', template_folder='templates')

# Detectar ambiente de produção
IS_PRODUCTION = bool(os.getenv('RAILWAY_ENVIRONMENT'))

# Build timestamp para cache busting (atualizado a cada restart)
BUILD_TIMESTAMP = str(int(time.time()))

# Configurar secret key para sessões
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = IS_PRODUCTION  # True em produção com HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Configurar CORS - Em produção usa a origem da requisição, em dev permite tudo
if IS_PRODUCTION:
    ALLOWED_ORIGINS = ['https://sistema-financeiro-dwm-production.up.railway.app']
else:
    ALLOWED_ORIGINS = ['*']  # Permitir tudo apenas em desenvolvimento local

CORS(app, 
     resources={r"/api/*": {
         "origins": ALLOWED_ORIGINS,
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
     }}, 
     supports_credentials=True)

# ============================================================================
# INICIALIZAR CSRF PROTECTION
# ============================================================================
csrf_instance = init_csrf(app)
register_csrf_error_handlers(app)

# Injetar CSRF token em todos os templates
@app.context_processor
def inject_csrf():
    return inject_csrf_token()

logger.info("✅ CSRF Protection configurado")

# Configurar Rate Limiting (apenas se disponível)
if LIMITER_AVAILABLE:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    print("✅ Rate Limiting ativado")
else:
    # Criar um decorador dummy se limiter não estiver disponível
    class DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
    limiter = DummyLimiter()
    print("⚠️ Rate Limiting desabilitado (flask-limiter não instalado)")

# ============================================================================
# MANIPULADORES DE ERRO GLOBAIS
# ============================================================================

@app.after_request
def add_no_cache_headers(response):
    """Força navegador a NUNCA cachear HTML, CSS e JS"""
    # Para arquivos estáticos (JS, CSS), desabilita cache agressivamente
    if request.path.startswith('/static/') or request.path.endswith(('.html', '.js', '.css')):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.before_request
def log_request_info():
    """Log de todas as requisições HTTP para auditoria e detecção mobile"""
    # Pular verificações para rotas de API mobile (já autenticadas via JWT)
    if request.path.startswith('/api/mobile/'):
        return None
    
    # Obter usuário se autenticado
    user_id = session.get('usuario_id')
    proprietario_id = session.get('proprietario_id')
    
    # Log estruturado
    log_request(request, user_id=user_id, proprietario_id=proprietario_id)
    
    # Breadcrumb para Sentry
    if SENTRY_ENABLED:
        add_breadcrumb(
            f"{request.method} {request.path}",
            category='http',
            data={
                'url': request.url,
                'method': request.method,
                'ip': request.remote_addr
            }
        )

@app.errorhandler(404)
def handle_404_error(e):
    """Captura erros 404 e loga detalhes"""
    logger.warning(
        f"404 - Rota não encontrada: {request.method} {request.path}",
        extra={'ip': request.remote_addr}
    )
    return jsonify({'error': 'Rota não encontrada', 'path': request.path}), 404

@app.errorhandler(500)
def handle_500_error(e):
    """Captura erros 500 e loga detalhes"""
    error_context = {
        'path': request.path,
        'method': request.method,
        'ip': request.remote_addr,
        'user_id': session.get('usuario_id')
    }
    
    # Log local
    logger.error(f"500 - Erro interno: {str(e)}", extra=error_context, exc_info=True)
    
    # Enviar para Sentry
    if SENTRY_ENABLED:
        capture_exception(e, context=error_context)
    
    return jsonify({'error': 'Erro interno do servidor', 'details': str(e)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Captura TODAS as exceções não tratadas"""
    error_context = {
        'path': request.path,
        'method': request.method,
        'ip': request.remote_addr,
        'user_id': session.get('usuario_id'),
        'proprietario_id': session.get('proprietario_id')
    }
    
    # Log local crítico
    logger.critical(
        f"Exceção não tratada: {type(e).__name__} - {str(e)}",
        extra=error_context,
        exc_info=True
    )
    
    # Enviar para Sentry com alta prioridade
    if SENTRY_ENABLED:
        capture_exception(e, context=error_context, level='fatal')
    print("="*80)
    print(f"Rota: {request.path}")
    print(f"Método: {request.method}")
    print(f"Tipo: {type(e).__name__}")
    print(f"Mensagem: {str(e)}")
    import traceback
    traceback.print_exc()
    print("="*80 + "\n")
    return jsonify({'error': 'Erro interno', 'type': type(e).__name__, 'message': str(e)}), 500

# ============================================================================
# CONFIGURAÇÃO E INICIALIZAÇÃO DO SISTEMA
# ============================================================================
print("\n" + "="*70)
print("🚀 SISTEMA FINANCEIRO - INICIALIZAÇÃO")
print("="*70)
print(f"📊 Banco de Dados: PostgreSQL (Pool de Conexões)")
print(f"🔐 DATABASE_URL: {'✅ Configurado' if os.getenv('DATABASE_URL') else '❌ Não configurado'}")
print(f"🌐 Ambiente: {'Produção (Railway)' if os.getenv('RAILWAY_ENVIRONMENT') else 'Desenvolvimento'}")
print("="*70 + "\n")

# Inicializar banco de dados com pool de conexões
try:
    print("🔄 Inicializando DatabaseManager com pool de conexões...")
    db = DatabaseManager()
    print("DatabaseManager inicializado com sucesso!")
    print(f"   Pool de conexoes: 2-20 conexoes simultaneas")
    
    # Executar migracoes
    try:
        from migration_user_preferences import executar_migracao as migrar_user_preferences
        migrar_user_preferences()
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível executar migração user_preferences: {e}")
    
    try:
        from migration_add_proprietario_id import executar_migracao as migrar_proprietario_id
        migrar_proprietario_id()
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível executar migração proprietario_id: {e}")
    
    try:
        print("\n🏢 Executando migração Multi-Tenant SaaS...")
        from migration_multi_tenant_saas import executar_migracao_completa
        if executar_migracao_completa():
            print("✅ Sistema Multi-Tenant configurado com sucesso!\n")
        else:
            print("⚠️ Migração Multi-Tenant falhou (pode já estar aplicada)\n")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível executar migração multi-tenant: {e}")
    
    # Criar tabela de extratos bancários se não existir
    try:
        print("\n🏦 Verificando tabela de extratos bancários...")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transacoes_extrato (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER NOT NULL,
                    conta_bancaria VARCHAR(255) NOT NULL,
                    data DATE NOT NULL,
                    descricao TEXT,
                    valor DECIMAL(15, 2) NOT NULL,
                    tipo VARCHAR(20) NOT NULL,
                    saldo DECIMAL(15, 2),
                    fitid VARCHAR(255),
                    memo TEXT,
                    checknum VARCHAR(50),
                    importacao_id VARCHAR(100),
                    conciliado BOOLEAN DEFAULT FALSE,
                    lancamento_id INTEGER,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uk_fitid_empresa UNIQUE (fitid, empresa_id)
                )
            """)
            
            # Criar índices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_empresa ON transacoes_extrato(empresa_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_conta ON transacoes_extrato(conta_bancaria)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_data ON transacoes_extrato(data)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_importacao ON transacoes_extrato(importacao_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_conciliado ON transacoes_extrato(conciliado)")
            
            conn.commit()
            cursor.close()
            print("✅ Tabela transacoes_extrato verificada/criada com sucesso!\n")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível criar tabela de extratos: {e}\n")
    
    # Criar tabelas de Funcionários e Eventos
    try:
        print("\n👥 Verificando tabelas de Folha de Pagamento e Eventos...")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de Funcionários
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS funcionarios (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER NOT NULL,
                    nome VARCHAR(255) NOT NULL,
                    cpf VARCHAR(11) NOT NULL,
                    endereco TEXT,
                    tipo_chave_pix VARCHAR(50) NOT NULL,
                    chave_pix VARCHAR(255),
                    ativo BOOLEAN DEFAULT TRUE,
                    data_admissao DATE,
                    data_demissao DATE,
                    observacoes TEXT,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uk_cpf_empresa UNIQUE (cpf, empresa_id)
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_funcionarios_empresa ON funcionarios(empresa_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_funcionarios_cpf ON funcionarios(cpf)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_funcionarios_ativo ON funcionarios(ativo)")
            
            # Migração: Alterar tipo da coluna CPF se necessário
            try:
                cursor.execute("""
                    ALTER TABLE funcionarios 
                    ALTER COLUMN cpf TYPE VARCHAR(11)
                """)
                print("✅ Coluna CPF migrada para VARCHAR(11)")
            except Exception as e:
                # Já está correto ou erro não crítico
                pass
            
            # Tabela de Eventos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS eventos (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER NOT NULL,
                    nome_evento VARCHAR(255) NOT NULL,
                    data_evento DATE NOT NULL,
                    nf_associada VARCHAR(100),
                    valor_liquido_nf DECIMAL(15, 2),
                    custo_evento DECIMAL(15, 2),
                    margem DECIMAL(15, 2),
                    tipo_evento VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'PENDENTE',
                    observacoes TEXT,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_empresa ON eventos(empresa_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_data ON eventos(data_evento)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_status ON eventos(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_tipo ON eventos(tipo_evento)")
            
            conn.commit()
            cursor.close()
            print("✅ Tabelas funcionarios e eventos verificadas/criadas com sucesso!\n")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível criar tabelas de folha/eventos: {e}\n")
        
except Exception as e:
    print(f"❌ ERRO CRÍTICO ao inicializar DatabaseManager: {e}")
    import traceback
    traceback.print_exc()
    raise

# ============================================================================
# ROTAS DE AUTENTICAÇÃO
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # Máximo 5 tentativas por minuto
def login():
    """Endpoint de login com proteção contra brute force"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username e senha são obrigatórios'
            }), 400
        
        # Verificar se conta está bloqueada
        from auth_functions import verificar_conta_bloqueada
        if verificar_conta_bloqueada(username, db):
            return jsonify({
                'success': False,
                'error': 'Conta temporariamente bloqueada por excesso de tentativas. Tente novamente em 15 minutos.'
            }), 429
        
        # Autenticar usuário
        usuario = auth_db.autenticar_usuario(username, password)
        
        if not usuario:
            # Registrar tentativa falha
            auth_db.registrar_log_acesso(
                usuario_id=None,
                acao='login_failed',
                descricao=f'Tentativa de login falhou para username: {username}',
                ip_address=request.remote_addr,
                sucesso=False
            )
            return jsonify({
                'success': False,
                'error': 'Usuário ou senha inválidos'
            }), 401
        
        # Criar sessão
        token = auth_db.criar_sessao(
            usuario['id'],
            request.remote_addr,
            request.headers.get('User-Agent', '')
        )
        
        # Guardar token na sessão do Flask
        session['session_token'] = token
        session.permanent = True
        
        # Registrar login bem-sucedido
        auth_db.registrar_log_acesso(
            usuario_id=usuario['id'],
            acao='login',
            descricao='Login realizado com sucesso',
            ip_address=request.remote_addr,
            sucesso=True
        )
        
        # Obter permissões do usuário
        permissoes = auth_db.obter_permissoes_usuario(usuario['id'])
        
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'usuario': {
                'id': usuario['id'],
                'username': usuario['username'],
                'nome_completo': usuario['nome_completo'],
                'tipo': usuario['tipo'],
                'email': usuario['email'],
                'cliente_id': usuario.get('cliente_id')
            },
            'permissoes': permissoes
        })
        
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Erro ao processar login'
        }), 500


@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Endpoint de logout"""
    try:
        token = session.get('session_token')
        
        if token:
            auth_db.invalidar_sessao(token)
            
            # Registrar logout
            usuario = request.usuario
            auth_db.registrar_log_acesso(
                usuario_id=usuario['id'],
                acao='logout',
                descricao='Logout realizado',
                ip_address=request.remote_addr,
                sucesso=True
            )
        
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Logout realizado com sucesso'
        })
        
    except Exception as e:
        print(f"❌ Erro no logout: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao processar logout'
        }), 500


@app.route('/api/auth/verify', methods=['GET'])
def verify_session():
    """Verifica se a sessão está válida"""
    try:
        usuario = get_usuario_logado()
        
        if not usuario:
            return jsonify({
                'success': False,
                'authenticated': False
            })
        
        # Obter permissões
        permissoes = auth_db.obter_permissoes_usuario(usuario['id'])
        
        return jsonify({
            'success': True,
            'authenticated': True,
            'usuario': {
                'id': usuario['id'],
                'username': usuario['username'],
                'nome_completo': usuario['nome_completo'],
                'tipo': usuario['tipo'],
                'email': usuario['email'],
                'cliente_id': usuario.get('cliente_id'),
                'permissoes': permissoes  # Incluir permissões no objeto usuario
            },
            'permissoes': permissoes
        })
        
    except Exception as e:
        print(f"❌ Erro ao verificar sessão: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao verificar sessão'
        }), 500


@app.route('/api/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    """Alterar senha do usuário logado"""
    try:
        data = request.json
        senha_atual = data.get('senha_atual')
        senha_nova = data.get('senha_nova')
        
        if not senha_atual or not senha_nova:
            return jsonify({
                'success': False,
                'error': 'Senha atual e nova senha são obrigatórias'
            }), 400
        
        # Validar força da nova senha
        from auth_functions import validar_senha_forte
        valida, mensagem = validar_senha_forte(senha_nova)
        if not valida:
            return jsonify({
                'success': False,
                'error': f'Nova senha fraca: {mensagem}'
            }), 400
        
        usuario = request.usuario
        
        # Verificar senha atual
        usuario_verificado = auth_db.autenticar_usuario(
            usuario['username'],
            senha_atual
        )
        
        if not usuario_verificado:
            return jsonify({
                'success': False,
                'error': 'Senha atual incorreta'
            }), 401
        
        # Atualizar senha
        auth_db.atualizar_usuario(
            usuario['id'],
            {'password': senha_nova}
        )
        
        # Registrar alteração
        auth_db.registrar_log_acesso(
            usuario_id=usuario['id'],
            acao='change_password',
            descricao='Senha alterada com sucesso',
            ip_address=request.remote_addr,
            sucesso=True
        )
        
        return jsonify({
            'success': True,
            'message': 'Senha alterada com sucesso'
        })
        
    except Exception as e:
        print(f"❌ Erro ao alterar senha: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao alterar senha'
        }), 500


# ===== ROTAS DE GERENCIAMENTO DE USUÁRIOS (APENAS ADMIN) =====

@app.route('/api/usuarios', methods=['GET', 'POST'])
@require_admin
def gerenciar_usuarios():
    """Listar ou criar usuários"""
    print(f"\n👥 [gerenciar_usuarios] FUNÇÃO CHAMADA - Método: {request.method}")
    if request.method == 'GET':
        try:
            print(f"\n{'='*80}")
            print(f"🔍 GET /api/usuarios - Listando usuários...")
            print(f"{'='*80}")
            
            # Verificar se usuário está autenticado
            usuario = getattr(request, 'usuario', None)
            if not usuario:
                print(f"   ❌ Usuário não autenticado")
                return jsonify({'success': False, 'error': 'Não autenticado'}), 401
            
            print(f"   ✅ Usuário autenticado: {usuario.get('username')} (tipo: {usuario.get('tipo')})")
            
            # Listar usuários
            usuarios = auth_db.listar_usuarios()
            print(f"   📊 Tipo retornado: {type(usuarios)}")
            
            # Garantir que é uma lista
            if not isinstance(usuarios, list):
                print(f"   ⚠️ Não é lista! Convertendo...")
                if usuarios is None:
                    usuarios = []
                else:
                    usuarios = [usuarios] if isinstance(usuarios, dict) else []
            
            # Converter datas para string (JSON serializable)
            usuarios_serializaveis = []
            for user in usuarios:
                user_dict = dict(user) if not isinstance(user, dict) else user
                
                # Converter datetime para string
                if 'created_at' in user_dict and user_dict['created_at']:
                    user_dict['created_at'] = str(user_dict['created_at'])
                if 'ultima_sessao' in user_dict and user_dict['ultima_sessao']:
                    user_dict['ultima_sessao'] = str(user_dict['ultima_sessao'])
                
                usuarios_serializaveis.append(user_dict)
            
            print(f"   ✅ Retornando {len(usuarios_serializaveis)} usuários")
            print(f"{'='*80}\n")
            
            return jsonify({'success': True, 'usuarios': usuarios_serializaveis})
            
        except Exception as e:
            print(f"❌ Erro ao listar usuários: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*80}\n")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:  # POST
        try:
            data = request.json
            admin = request.usuario
            data['created_by'] = admin['id']
            
            # Validar força da senha
            from auth_functions import validar_senha_forte
            if 'password' in data:
                valida, mensagem = validar_senha_forte(data['password'])
                if not valida:
                    return jsonify({
                        'success': False,
                        'error': f'Senha fraca: {mensagem}'
                    }), 400
            
            usuario_id = auth_db.criar_usuario(data)
            
            # Conceder permissões se fornecidas
            if 'permissoes' in data:
                auth_db.sincronizar_permissoes_usuario(
                    usuario_id,
                    data['permissoes'],
                    admin['id']
                )
            
            # Registrar criação
            auth_db.registrar_log_acesso(
                usuario_id=admin['id'],
                acao='create_user',
                descricao=f'Usuário criado: {data["username"]}',
                ip_address=request.remote_addr,
                sucesso=True
            )
            
            return jsonify({
                'success': True,
                'message': 'Usuário criado com sucesso',
                'id': usuario_id
            }), 201
            
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except Exception as e:
            print(f"❌ Erro ao criar usuário: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/usuarios/<int:usuario_id>', methods=['GET', 'PUT', 'DELETE'])
@require_admin
def gerenciar_usuario_especifico(usuario_id):
    """Obter, atualizar ou deletar usuário específico"""
    print(f"\n👤 [gerenciar_usuario_especifico] FUNÇÃO CHAMADA - ID: {usuario_id}, Método: {request.method}")
    if request.method == 'GET':
        try:
            print(f"   🔍 Buscando usuário ID {usuario_id}...")
            usuario = auth_db.obter_usuario(usuario_id)
            print(f"   📊 Resultado: {usuario if usuario else 'NÃO ENCONTRADO'}")
            if not usuario:
                print(f"   ❌ Usuário {usuario_id} não encontrado")
                return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 404
            
            # Incluir permissões
            permissoes = auth_db.obter_permissoes_usuario(usuario_id)
            usuario['permissoes'] = permissoes
            
            return jsonify(usuario)
        except Exception as e:
            print(f"❌ Erro ao obter usuário: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.json
            admin = request.usuario
            
            # Validar força da senha se estiver sendo alterada
            if 'password' in data and data['password']:
                from auth_functions import validar_senha_forte
                valida, mensagem = validar_senha_forte(data['password'])
                if not valida:
                    return jsonify({
                        'success': False,
                        'error': f'Senha fraca: {mensagem}'
                    }), 400
            
            # Atualizar dados do usuário
            success = auth_db.atualizar_usuario(usuario_id, data)
            
            if not success:
                return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 404
            
            # Atualizar permissões se fornecidas
            if 'permissoes' in data:
                auth_db.sincronizar_permissoes_usuario(
                    usuario_id,
                    data['permissoes'],
                    admin['id']
                )
            
            # Registrar atualização
            auth_db.registrar_log_acesso(
                usuario_id=admin['id'],
                acao='update_user',
                descricao=f'Usuário atualizado: ID {usuario_id}',
                ip_address=request.remote_addr,
                sucesso=True
            )
            
            return jsonify({
                'success': True,
                'message': 'Usuário atualizado com sucesso'
            })
            
        except Exception as e:
            print(f"❌ Erro ao atualizar usuário: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:  # DELETE
        try:
            admin = request.usuario
            success = auth_db.deletar_usuario(usuario_id)
            
            if not success:
                return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 404
            
            # Registrar exclusão
            auth_db.registrar_log_acesso(
                usuario_id=admin['id'],
                acao='delete_user',
                descricao=f'Usuário deletado: ID {usuario_id}',
                ip_address=request.remote_addr,
                sucesso=True
            )
            
            return jsonify({
                'success': True,
                'message': 'Usuário deletado com sucesso'
            })
            
        except Exception as e:
            print(f"❌ Erro ao deletar usuário: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/permissoes', methods=['GET'])
@require_admin
def listar_permissoes():
    """Listar todas as permissões disponíveis"""
    print(f"\n🔒 [listar_permissoes] FUNÇÃO CHAMADA")
    try:
        categoria = request.args.get('categoria')
        permissoes = auth_db.listar_permissoes(categoria)
        return jsonify(permissoes)
    except Exception as e:
        print(f"❌ Erro ao listar permissões: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# === ROTAS DE CONTAS BANCÁRIAS ===

@app.route('/api/contas', methods=['GET'])
@require_permission('contas_view')
@aplicar_filtro_cliente
def listar_contas():
    """Lista todas as contas bancárias com saldo real e filtro de multi-tenancy"""
    try:
        filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
        
        contas = db.listar_contas(filtro_cliente_id=filtro_cliente_id)
        lancamentos = db.listar_lancamentos(filtro_cliente_id=filtro_cliente_id)
        
        # Calcular saldo real de cada conta
        contas_com_saldo = []
        for c in contas:
            saldo_real = Decimal(str(c.saldo_inicial))
            
            # Somar/subtrair lançamentos pagos desta conta
            for lanc in lancamentos:
                if lanc.status == StatusLancamento.PAGO:
                    valor_decimal = Decimal(str(lanc.valor))
                    
                    if lanc.tipo == TipoLancamento.TRANSFERENCIA:
                        # Transferência: origem está em conta_bancaria, destino em subcategoria
                        if hasattr(lanc, 'conta_bancaria') and lanc.conta_bancaria == c.nome:
                            # Esta é a conta de origem - subtrai
                            saldo_real -= valor_decimal
                        if hasattr(lanc, 'subcategoria') and lanc.subcategoria == c.nome:
                            # Esta é a conta de destino - adiciona
                            saldo_real += valor_decimal
                    elif hasattr(lanc, 'conta_bancaria') and lanc.conta_bancaria == c.nome:
                        # Receitas e despesas normais
                        if lanc.tipo == TipoLancamento.RECEITA:
                            saldo_real += valor_decimal
                        elif lanc.tipo == TipoLancamento.DESPESA:
                            saldo_real -= valor_decimal
            
            contas_com_saldo.append({
                'nome': c.nome,
                'banco': c.banco,
                'agencia': c.agencia,
                'conta': c.conta,
                'saldo_inicial': float(c.saldo_inicial),
                'saldo': float(saldo_real)  # Saldo real com movimentações
            })
        
        return jsonify(contas_com_saldo)
    except Exception as e:
        print(f"❌ Erro em /api/contas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/contas', methods=['POST'])
@require_permission('contas_create')
@aplicar_filtro_cliente
def adicionar_conta():
    """Adiciona uma nova conta bancária"""
    try:
        data = request.json
        proprietario_id = getattr(request, 'filtro_cliente_id', None)
        
        # Verificar contas existentes antes de adicionar
        contas_existentes = db.listar_contas(filtro_cliente_id=proprietario_id)
        
        # Verificar se já existe
        for c in contas_existentes:
            if c.nome == data['nome']:
                print(f"CONFLITO: Conta '{data['nome']}' já existe!")
                return jsonify({'success': False, 'error': f'Já existe uma conta cadastrada com: Banco: {data["banco"]}, Agência: {data["agencia"]}, Conta: {data["conta"]}'}), 400
        
        conta = ContaBancaria(
            nome=data['nome'],  # type: ignore
            banco=data['banco'],  # type: ignore
            agencia=data['agencia'],  # type: ignore
            conta=data['conta'],  # type: ignore
            saldo_inicial=float(data.get('saldo_inicial', 0) if data else 0)  # type: ignore
        )
        
        conta_id = db.adicionar_conta(conta, proprietario_id=proprietario_id)
        return jsonify({'success': True, 'id': conta_id})
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        if 'UNIQUE constraint' in error_msg:
            error_msg = 'Já existe uma conta com este nome'
        return jsonify({'success': False, 'error': error_msg}), 400


@app.route('/api/contas/<path:nome>', methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])  # type: ignore
@require_permission('contas_view')
def modificar_conta(nome):
    """Busca, atualiza ou remove uma conta bancária"""
    
    # Responder ao preflight OPTIONS
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200
    
    if request.method == 'GET':
        try:
            contas = db.listar_contas()
            for conta in contas:
                if conta.nome == nome:
                    return jsonify({
                        'nome': conta.nome,
                        'banco': conta.banco,
                        'agencia': conta.agencia,
                        'conta': conta.conta,
                        'saldo_inicial': float(conta.saldo_inicial)
                    })
            return jsonify({'success': False, 'error': 'Conta não encontrada'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    elif request.method == 'PUT':
        try:
            data = request.json
            
            conta = ContaBancaria(
                nome=data['nome'],  # type: ignore
                banco=data['banco'],  # type: ignore
                agencia=data['agencia'],  # type: ignore
                conta=data['conta'],  # type: ignore
                saldo_inicial=float(data.get('saldo_inicial', 0) if data else 0)  # type: ignore
            )
            success = db.atualizar_conta(nome, conta)
            return jsonify({'success': success})
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            if 'UNIQUE constraint' in error_msg:
                error_msg = 'Já existe uma conta com este nome'
            return jsonify({'success': False, 'error': error_msg}), 400
    
    elif request.method == 'DELETE':
        try:
            success = db.excluir_conta(nome)
            return jsonify({'success': success})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/transferencias', methods=['POST'])
@require_permission('lancamentos_create')
def criar_transferencia():
    """Cria uma transferência entre contas bancárias"""
    try:
        data = request.json
        
        # Validar dados
        if not data or not data.get('conta_origem') or not data.get('conta_destino'):
            return jsonify({'success': False, 'error': 'Contas de origem e destino são obrigatórias'}), 400
        
        if data['conta_origem'] == data['conta_destino']:
            return jsonify({'success': False, 'error': 'Conta de origem e destino não podem ser iguais'}), 400
        
        valor = float(data.get('valor', 0))
        if valor <= 0:
            return jsonify({'success': False, 'error': 'Valor deve ser maior que zero'}), 400
        
        # Buscar contas
        conta_origem = db.buscar_conta(data['conta_origem'])
        conta_destino = db.buscar_conta(data['conta_destino'])
        
        if not conta_origem:
            return jsonify({'success': False, 'error': 'Conta de origem não encontrada'}), 404
        if not conta_destino:
            return jsonify({'success': False, 'error': 'Conta de destino não encontrada'}), 404
        
        # Criar data da transferência
        data_transferencia = datetime.fromisoformat(data['data']) if data.get('data') else datetime.now()
        
        # Criar lançamento de transferência
        lancamento = Lancamento(
            descricao=f"Transferência: {conta_origem.nome} → {conta_destino.nome}",
            valor=valor,
            tipo=TipoLancamento.TRANSFERENCIA,
            categoria="Transferência Interna",
            data_vencimento=data_transferencia,
            data_pagamento=data_transferencia,
            conta_bancaria=data['conta_origem'],
            pessoa="",
            observacoes=f"Destino: {conta_destino.nome}. {data.get('observacoes', '')}",
            num_documento="",
            subcategoria=data['conta_destino']  # Usar subcategoria para armazenar conta destino
        )
        
        lancamento.status = StatusLancamento.PAGO
        lancamento_id = db.adicionar_lancamento(lancamento)
        
        return jsonify({'success': True, 'id': lancamento_id})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# === ROTAS DE CATEGORIAS ===

@app.route('/api/categorias', methods=['GET'])
@require_permission('categorias_view')
def listar_categorias():
    """Lista todas as categorias"""
    categorias = db.listar_categorias()
    return jsonify([{
        'nome': c.nome,
        'tipo': c.tipo.value,
        'subcategorias': c.subcategorias
    } for c in categorias])


@app.route('/api/categorias', methods=['POST'])
@require_permission('categorias_create')
def adicionar_categoria():
    """Adiciona uma nova categoria"""
    try:
        data = request.json
        
        # Converter tipo para minúscula para compatibilidade com o enum
        tipo_str = data['tipo'].lower() if data and data.get('tipo') else 'receita'  # type: ignore
        
        # Normalizar nome: uppercase e trim
        nome_normalizado = data['nome'].strip().upper() if data and data.get('nome') else ''  # type: ignore
        
        categoria = Categoria(
            nome=nome_normalizado,  # type: ignore
            tipo=TipoLancamento(tipo_str),  # type: ignore
            subcategorias=data.get('subcategorias', []) if data else []  # type: ignore
        )
        categoria_id = db.adicionar_categoria(categoria)
        return jsonify({'success': True, 'id': categoria_id})
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        if 'UNIQUE constraint' in error_msg:
            error_msg = 'Já existe uma categoria com este nome'
        return jsonify({'success': False, 'error': error_msg}), 400


@app.route('/api/categorias/<path:nome>', methods=['PUT', 'DELETE'])  # type: ignore
@require_permission('categorias_edit')
def modificar_categoria(nome):
    """Atualiza ou remove uma categoria"""
    if request.method == 'PUT':
        try:
            data = request.json
            
            # Converter tipo para minúscula para compatibilidade com o enum
            tipo_str = data['tipo'].lower() if data and data.get('tipo') else 'receita'  # type: ignore
            
            # Normalizar nome: uppercase e trim
            nome_normalizado = data['nome'].strip().upper() if data and data.get('nome') else ''  # type: ignore
            
            # Se o nome mudou, precisamos atualizar com atualizar_nome_categoria primeiro
            nome_original_normalizado = nome.strip().upper()
            
            # Se o nome mudou, atualizar o nome primeiro
            if nome_normalizado != nome_original_normalizado:
                db.atualizar_nome_categoria(nome_original_normalizado, nome_normalizado)
            
            categoria = Categoria(
                nome=nome_normalizado,  # type: ignore
                tipo=TipoLancamento(tipo_str),  # type: ignore
                subcategorias=data.get('subcategorias', []) if data else []  # type: ignore
            )
            success = db.atualizar_categoria(categoria)
            return jsonify({'success': success})
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            if 'UNIQUE constraint' in error_msg:
                error_msg = 'Já existe uma categoria com este nome'
            return jsonify({'success': False, 'error': error_msg}), 400
    
    elif request.method == 'DELETE':
        try:
            success = db.excluir_categoria(nome)
            return jsonify({'success': success})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400


# === ROTAS DE CLIENTES ===

@app.route('/api/clientes', methods=['GET'])
@require_permission('clientes_view')
@aplicar_filtro_cliente
def listar_clientes():
    """Lista clientes ativos ou inativos com filtro de multi-tenancy"""
    ativos = request.args.get('ativos', 'true').lower() == 'true'
    filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
    
    clientes = db.listar_clientes(ativos=ativos, filtro_cliente_id=filtro_cliente_id)
    
    # Adicionar cliente_id para cada cliente (usando nome como identificador)
    for cliente in clientes:
        cliente['cliente_id'] = cliente.get('nome')
    
    return jsonify(clientes)


@app.route('/api/clientes', methods=['POST'])
@require_permission('clientes_create')
@aplicar_filtro_cliente
def adicionar_cliente():
    """Adiciona um novo cliente"""
    try:
        data = request.json
        proprietario_id = getattr(request, 'filtro_cliente_id', None)
        
        cliente_id = db.adicionar_cliente(data, proprietario_id=proprietario_id)  # type: ignore
        return jsonify({'success': True, 'id': cliente_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/clientes/<path:nome>', methods=['PUT', 'DELETE'])  # type: ignore
@require_permission('clientes_edit')
@aplicar_filtro_cliente
def modificar_cliente(nome):
    """Atualiza ou remove um cliente com validação de empresa"""
    filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
    
    if request.method == 'PUT':
        try:
            data = request.json
            print(f"\n=== Atualizando cliente ===")
            print(f"URL recebida: {request.url}")
            print(f"Nome da URL (raw): '{nome}'")
            print(f"Dados recebidos: {data}")
            
            # Validar propriedade antes de atualizar (se não for admin)
            if filtro_cliente_id is not None:
                cliente_atual = db.obter_cliente_por_nome(nome)
                if not cliente_atual or cliente_atual.get('proprietario_id') != filtro_cliente_id:
                    return jsonify({'success': False, 'error': 'Cliente não encontrado ou sem permissão'}), 403
            
            success = atualizar_cliente(nome, data)
            print(f"Cliente atualizado: {success}")
            return jsonify({'success': success})
        except Exception as e:
            print(f"ERRO ao atualizar cliente: {str(e)}")
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            if 'UNIQUE constraint' in error_msg:
                error_msg = 'Já existe um cliente com este nome'
            return jsonify({'success': False, 'error': error_msg}), 400
    
    elif request.method == 'DELETE':
        try:
            # Validar propriedade antes de deletar (se não for admin)
            if filtro_cliente_id is not None:
                cliente_atual = db.obter_cliente_por_nome(nome)
                if not cliente_atual or cliente_atual.get('proprietario_id') != filtro_cliente_id:
                    return jsonify({'success': False, 'error': 'Cliente não encontrado ou sem permissão'}), 403
            
            success, mensagem = db.excluir_cliente(nome)
            if success:
                return jsonify({'success': True, 'message': mensagem})
            else:
                return jsonify({'success': False, 'error': mensagem}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400


# === ROTAS DE FORNECEDORES ===

@app.route('/api/fornecedores', methods=['GET'])
@require_permission('fornecedores_view')
@aplicar_filtro_cliente
def listar_fornecedores():
    """Lista fornecedores ativos ou inativos com filtro de multi-tenancy"""
    ativos = request.args.get('ativos', 'true').lower() == 'true'
    filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
    
    fornecedores = db.listar_fornecedores(ativos=ativos, filtro_cliente_id=filtro_cliente_id)
    
    return jsonify(fornecedores)


@app.route('/api/fornecedores', methods=['POST'])
@require_permission('fornecedores_create')
@aplicar_filtro_cliente
def adicionar_fornecedor():
    """Adiciona um novo fornecedor"""
    try:
        data = request.json
        proprietario_id = getattr(request, 'filtro_cliente_id', None)
        
        fornecedor_id = db.adicionar_fornecedor(data, proprietario_id=proprietario_id)  # type: ignore
        return jsonify({'success': True, 'id': fornecedor_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fornecedores/<path:nome>', methods=['PUT', 'DELETE'])  # type: ignore
@require_permission('fornecedores_edit')
@aplicar_filtro_cliente
def modificar_fornecedor(nome):
    """Atualiza ou remove um fornecedor com validação de empresa"""
    filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
    
    if request.method == 'PUT':
        try:
            data = request.json
            
            # Validar propriedade antes de atualizar (se não for admin)
            if filtro_cliente_id is not None:
                fornecedor_atual = db.obter_fornecedor_por_nome(nome)
                if not fornecedor_atual or fornecedor_atual.get('proprietario_id') != filtro_cliente_id:
                    return jsonify({'success': False, 'error': 'Fornecedor não encontrado ou sem permissão'}), 403
            
            success = atualizar_fornecedor(nome, data)
            return jsonify({'success': success})
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            if 'UNIQUE constraint' in error_msg:
                error_msg = 'Já existe um fornecedor com este nome'
            return jsonify({'success': False, 'error': error_msg}), 400
    
    elif request.method == 'DELETE':
        try:
            # Validar propriedade antes de deletar (se não for admin)
            if filtro_cliente_id is not None:
                fornecedor_atual = db.obter_fornecedor_por_nome(nome)
                if not fornecedor_atual or fornecedor_atual.get('proprietario_id') != filtro_cliente_id:
                    return jsonify({'success': False, 'error': 'Fornecedor não encontrado ou sem permissão'}), 403
            
            success, mensagem = db.excluir_fornecedor(nome)
            if success:
                return jsonify({'success': True, 'message': mensagem})
            else:
                return jsonify({'success': False, 'error': mensagem}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/clientes/<path:nome>/inativar', methods=['POST'])
@require_permission('clientes_edit')
def inativar_cliente(nome):
    """Inativa um cliente com motivo"""
    try:
        data = request.json
        motivo = data.get('motivo', '')
        
        if not motivo.strip():
            return jsonify({'success': False, 'error': 'Motivo é obrigatório'}), 400
        
        success, mensagem = db.inativar_cliente(nome, motivo)
        return jsonify({'success': success, 'message': mensagem})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/clientes/<path:nome>/reativar', methods=['POST'])
@require_permission('clientes_edit')
def reativar_cliente(nome):
    """Reativa um cliente"""
    try:
        success = db.reativar_cliente(nome)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fornecedores/<path:nome>/inativar', methods=['POST'])
@require_permission('fornecedores_edit')
def inativar_fornecedor(nome):
    """Inativa um fornecedor com motivo"""
    try:
        data = request.json
        motivo = data.get('motivo', '')
        
        if not motivo.strip():
            return jsonify({'success': False, 'error': 'Motivo é obrigatório'}), 400
        
        success, mensagem = db.inativar_fornecedor(nome, motivo)
        return jsonify({'success': success, 'message': mensagem})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fornecedores/<path:nome>/reativar', methods=['POST'])
@require_permission('fornecedores_edit')
def reativar_fornecedor(nome):
    """Reativa um fornecedor"""
    try:
        success = db.reativar_fornecedor(nome)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# === ROTAS DE LANÇAMENTOS ===

@app.route('/api/lancamentos', methods=['GET'])
@require_permission('lancamentos_view')
@aplicar_filtro_cliente
def listar_lancamentos():
    """Lista todos os lançamentos com filtro de multi-tenancy"""
    try:
        tipo_filtro = request.args.get('tipo')
        filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
        
        lancamentos = database.listar_lancamentos(filtro_cliente_id=filtro_cliente_id)
        
        # Filtrar por tipo se especificado (case-insensitive)
        if tipo_filtro:
            lancamentos = [l for l in lancamentos if l.tipo.value.upper() == tipo_filtro.upper()]
        
        # Converter para lista de dicts e aplicar filtro por cliente
        lancamentos_list = [{
            'id': l.id if hasattr(l, 'id') else None,
            'tipo': l.tipo.value,
            'descricao': l.descricao,
            'valor': float(l.valor),
            'data_vencimento': l.data_vencimento.isoformat() if l.data_vencimento else None,
            'data_pagamento': l.data_pagamento.isoformat() if l.data_pagamento else None,
            'status': l.status.value,
            'categoria': l.categoria,
            'subcategoria': l.subcategoria,
            'conta_bancaria': l.conta_bancaria,
            'pessoa': l.pessoa,
            'observacoes': l.observacoes,
            'num_documento': getattr(l, 'num_documento', ''),
            'recorrente': getattr(l, 'recorrente', False),
            'frequencia_recorrencia': getattr(l, 'frequencia_recorrencia', ''),
            'cliente_id': getattr(l, 'pessoa', None)  # Usar pessoa como referência ao cliente
        } for l in lancamentos]
        
        return jsonify(lancamentos_list)
    except Exception as e:
        print(f"❌ Erro ao listar lançamentos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/lancamentos', methods=['POST'])
@require_permission('lancamentos_create')
@aplicar_filtro_cliente
def adicionar_lancamento():
    """Adiciona um novo lançamento (com suporte a parcelamento)"""
    try:
        data = request.json
        proprietario_id = getattr(request, 'filtro_cliente_id', None)
        
        parcelas = int(data.get('parcelas', 1)) if data else 1
        
        if parcelas > 1:
            # Criar múltiplos lançamentos para parcelas
            from dateutil.relativedelta import relativedelta  # type: ignore
            data_base = datetime.fromisoformat(data['data_vencimento']) if data and data.get('data_vencimento') else datetime.now()
            valor_parcela = float(data['valor']) / parcelas if data else 0.0
            tipo_str = data['tipo'].lower() if data and data.get('tipo') else 'receita'
            
            lancamentos_ids = []
            for i in range(parcelas):
                data_venc = data_base + relativedelta(months=i)
                descricao_parcela = f"{data['descricao']} ({i+1}/{parcelas})" if data else f"Parcela {i+1}/{parcelas}"
                
                lancamento = Lancamento(
                    descricao=descricao_parcela,
                    valor=valor_parcela,
                    tipo=TipoLancamento(tipo_str),
                    categoria=data.get('categoria', '') if data else '',
                    data_vencimento=data_venc,
                    data_pagamento=None,
                    conta_bancaria=data['conta_bancaria'] if data else '',
                    pessoa=data.get('pessoa', '') if data else '',
                    observacoes=data.get('observacoes', '') if data else '',
                    num_documento=data.get('num_documento', '') if data else '',
                    subcategoria=data.get('subcategoria', '') if data else ''
                )
                
                if data and data.get('status'):
                    lancamento.status = StatusLancamento(data['status'])
                
                lancamento_id = db.adicionar_lancamento(lancamento, proprietario_id=proprietario_id)
                lancamentos_ids.append(lancamento_id)
            
            print(f"Lançamentos parcelados adicionados! IDs: {lancamentos_ids}")
            return jsonify({'success': True, 'ids': lancamentos_ids})
        else:
            # Lançamento único (sem parcelamento)
            data_venc = datetime.fromisoformat(data['data_vencimento']) if data and data.get('data_vencimento') else datetime.now()
            data_pag = datetime.fromisoformat(data['data_pagamento']) if data and data.get('data_pagamento') else None
            tipo_str = data['tipo'].lower() if data and data.get('tipo') else 'receita'
            
            lancamento = Lancamento(
                descricao=data['descricao'] if data else '',
                valor=float(data['valor']) if data else 0.0,
                tipo=TipoLancamento(tipo_str),
                categoria=data.get('categoria', '') if data else '',
                data_vencimento=data_venc,
                data_pagamento=data_pag,
                conta_bancaria=data['conta_bancaria'] if data else '',
                pessoa=data.get('pessoa', '') if data else '',
                observacoes=data.get('observacoes', '') if data else '',
                num_documento=data.get('num_documento', '') if data else '',
                subcategoria=data.get('subcategoria', '') if data else ''
            )
            
            if data and data.get('status'):
                lancamento.status = StatusLancamento(data['status'])
            
            lancamento_id = db.adicionar_lancamento(lancamento, proprietario_id=proprietario_id)
            return jsonify({'success': True, 'id': lancamento_id})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/lancamentos/<int:lancamento_id>', methods=['GET'])
@require_permission('lancamentos_view')
def obter_lancamento_route(lancamento_id):
    """Retorna os dados de um lançamento específico"""
    try:
        print(f"\n{'='*80}")
        print(f"🔍 GET /api/lancamentos/{lancamento_id}")
        print(f"{'='*80}")
        
        lancamento = db_obter_lancamento(lancamento_id)
        print(f"Resultado db_obter_lancamento: {lancamento}")
        print(f"Tipo: {type(lancamento)}")
        
        if lancamento:
            # Converter Lancamento para dict
            lancamento_dict = {
                'id': lancamento.id,
                'tipo': lancamento.tipo.value if hasattr(lancamento.tipo, 'value') else str(lancamento.tipo),
                'descricao': lancamento.descricao,
                'valor': float(lancamento.valor),
                'data_vencimento': lancamento.data_vencimento.isoformat() if lancamento.data_vencimento else None,
                'data_pagamento': lancamento.data_pagamento.isoformat() if lancamento.data_pagamento else None,
                'categoria': lancamento.categoria,
                'subcategoria': lancamento.subcategoria,
                'conta_bancaria': lancamento.conta_bancaria,
                'cliente_fornecedor': lancamento.cliente_fornecedor,
                'pessoa': lancamento.pessoa,
                'status': lancamento.status.value if hasattr(lancamento.status, 'value') else str(lancamento.status),
                'observacoes': lancamento.observacoes,
                'anexo': lancamento.anexo,
                'recorrente': lancamento.recorrente,
                'frequencia_recorrencia': lancamento.frequencia_recorrencia,
                'dia_vencimento': lancamento.dia_vencimento,
                'juros': float(getattr(lancamento, 'juros', 0)),
                'desconto': float(getattr(lancamento, 'desconto', 0))
            }
            print(f"✅ Lançamento convertido para dict: {lancamento_dict}")
            print(f"{'='*80}\n")
            return jsonify(lancamento_dict), 200
        else:
            print(f"❌ Lançamento não encontrado")
            print(f"{'='*80}\n")
            return jsonify({'error': 'Lançamento não encontrado'}), 404
    except Exception as e:
        print(f"❌ ERRO ao obter lançamento:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        print(f"{'='*80}\n")
        return jsonify({'error': str(e)}), 500


@app.route('/api/lancamentos/<int:lancamento_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
@require_permission('lancamentos_edit')
def gerenciar_lancamento(lancamento_id):
    """Atualiza ou remove um lançamento"""
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200
    
    if request.method == 'PUT':
        try:
            print(f"\n{'='*80}")
            print(f"🔍 PUT /api/lancamentos/{lancamento_id}")
            print(f"{'='*80}")
            
            data = request.get_json()
            print(f"📥 Dados recebidos: {data}")
            
            # Verificar se lançamento existe
            lancamento_atual = db_obter_lancamento(lancamento_id)
            if not lancamento_atual:
                print("❌ Lançamento não encontrado")
                return jsonify({'success': False, 'error': 'Lançamento não encontrado'}), 404
            
            # Preservar dados de pagamento se já foi pago
            status_atual = lancamento_atual.status.value if hasattr(lancamento_atual.status, 'value') else str(lancamento_atual.status)
            data_pgto_atual = lancamento_atual.data_pagamento
            conta_bancaria_atual = lancamento_atual.conta_bancaria
            juros_atual = getattr(lancamento_atual, 'juros', 0)
            desconto_atual = getattr(lancamento_atual, 'desconto', 0)
            
            print(f"📊 Preservando dados de pagamento:")
            print(f"   - Status: {status_atual}")
            print(f"   - Data pagamento: {data_pgto_atual}")
            print(f"   - Conta: {conta_bancaria_atual}")
            
            # Criar objeto Lancamento atualizado
            from database_postgresql import TipoLancamento, StatusLancamento
            from decimal import Decimal
            
            tipo_enum = TipoLancamento(data['tipo'].lower())
            status_enum = StatusLancamento(status_atual.lower()) if status_atual else StatusLancamento.PENDENTE
            
            lancamento_atualizado = Lancamento(
                id=lancamento_id,
                tipo=tipo_enum,
                descricao=data.get('descricao', ''),
                valor=Decimal(str(data['valor'])),
                data_vencimento=datetime.fromisoformat(data['data_vencimento']),
                data_pagamento=data_pgto_atual,
                categoria=data.get('categoria', ''),
                subcategoria=data.get('subcategoria', ''),
                conta_bancaria=conta_bancaria_atual,
                cliente_fornecedor=data.get('cliente_fornecedor', ''),
                pessoa=data.get('pessoa', ''),
                status=status_enum,
                observacoes=data.get('observacoes', ''),
                anexo=data.get('anexo', ''),
                recorrente=data.get('recorrente', False),
                frequencia_recorrencia=data.get('frequencia_recorrencia', ''),
                dia_vencimento=data.get('dia_vencimento', 0),
                num_documento=data.get('num_documento', ''),
                juros=juros_atual,
                desconto=desconto_atual
            )
            
            # Atualizar no banco
            success = db.atualizar_lancamento(lancamento_atualizado)
            
            print(f"✅ Resultado: {success}")
            print(f"{'='*80}\n")
            
            if success:
                return jsonify({'success': True, 'id': lancamento_id})
            else:
                return jsonify({'success': False, 'error': 'Falha ao atualizar'}), 400
            
        except Exception as e:
            print(f"❌ ERRO ao atualizar lançamento:")
            print(f"   Tipo: {type(e).__name__}")
            print(f"   Mensagem: {str(e)}")
            import traceback
            print(f"   Traceback:\n{traceback.format_exc()}")
            print(f"{'='*80}\n")
            return jsonify({'success': False, 'error': str(e)}), 400
    
    # DELETE
    try:
        print(f"\n=== Excluindo lançamento ID: {lancamento_id} ===")
        success = db.excluir_lancamento(lancamento_id)
        print(f"Resultado da exclusão: {success}")
        
        if not success:
            print("AVISO: Nenhum registro foi excluído (ID não encontrado?)")
            return jsonify({'success': False, 'error': 'Lançamento não encontrado'}), 404
        
        print("Lançamento excluído com sucesso!")
        return jsonify({'success': True})
    except Exception as e:
        print(f"ERRO ao excluir lançamento: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


# ============================================================================
# ROTAS DE EXTRATO BANCARIO (IMPORTACAO OFX)
# ============================================================================

import extrato_functions

@app.route('/api/extratos/upload', methods=['POST'])
@require_permission('lancamentos_edit')
def upload_extrato_ofx():
    """Upload e processamento de arquivo OFX"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        conta_bancaria = request.form.get('conta_bancaria')
        
        if not conta_bancaria:
            return jsonify({'success': False, 'error': 'Conta bancaria e obrigatoria'}), 400
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        
        if not file.filename.lower().endswith('.ofx'):
            return jsonify({'success': False, 'error': 'Apenas arquivos .ofx sao permitidos'}), 400
        
        # Parse OFX
        try:
            import ofxparse
            ofx = ofxparse.OfxParser.parse(file)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Erro ao processar OFX: {str(e)}'}), 400
        
        # Extrair transacoes
        transacoes = []
        for account in ofx.accounts:
            # Obter saldo final e inicial
            saldo_final = float(account.statement.balance) if hasattr(account.statement, 'balance') else None
            
            # Ordenar transações por data (mais antiga primeiro)
            transactions_list = sorted(account.statement.transactions, key=lambda t: t.date)
            
            # Calcular saldo inicial subtraindo todas as transações do saldo final
            if saldo_final is not None:
                soma_transacoes = sum(float(t.amount) for t in transactions_list)
                saldo_atual = saldo_final - soma_transacoes
            else:
                saldo_atual = 0
            
            # Processar cada transação e calcular saldo progressivo
            for trans in transactions_list:
                valor = float(trans.amount)
                saldo_atual += valor  # Atualizar saldo progressivamente
                
                transacoes.append({
                    'data': trans.date.date() if hasattr(trans.date, 'date') else trans.date,
                    'descricao': trans.payee or trans.memo or 'Sem descricao',
                    'valor': valor,
                    'tipo': 'credito' if valor > 0 else 'debito',
                    'saldo': saldo_atual,  # Saldo após esta transação
                    'fitid': trans.id,
                    'memo': trans.memo,
                    'checknum': trans.checknum if hasattr(trans, 'checknum') else None
                })
        
        if not transacoes:
            return jsonify({'success': False, 'error': 'Nenhuma transacao encontrada no arquivo'}), 400
        
        # Salvar no banco
        usuario = get_usuario_logado()
        # Usar cliente_id como empresa_id (multi-tenancy)
        empresa_id = usuario.get('cliente_id') or usuario.get('empresa_id') or 1
        resultado = extrato_functions.salvar_transacoes_extrato(
            database, 
            empresa_id, 
            conta_bancaria, 
            transacoes
        )
        
        if resultado['success']:
            # Formatar resposta para o frontend
            return jsonify({
                'success': True,
                'message': 'Extrato importado com sucesso',
                'transacoes_importadas': resultado.get('inseridas', 0),
                'transacoes_duplicadas': resultado.get('duplicadas', 0),
                'importacao_id': resultado.get('importacao_id')
            }), 200
        else:
            return jsonify(resultado), 400
        
    except Exception as e:
        logger.info(f"Erro ao processar OFX: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/extratos', methods=['GET'])
@require_permission('lancamentos_view')
def listar_extratos():
    """Lista transacoes do extrato com filtros"""
    try:
        usuario = get_usuario_logado()
        # Usar cliente_id como empresa_id (multi-tenancy)
        empresa_id = usuario.get('cliente_id') or usuario.get('empresa_id') or 1
        
        filtros = {
            'conta_bancaria': request.args.get('conta'),
            'data_inicio': request.args.get('data_inicio'),
            'data_fim': request.args.get('data_fim'),
            'conciliado': request.args.get('conciliado')
        }
        
        # Converter conciliado para boolean
        if filtros['conciliado'] is not None:
            filtros['conciliado'] = filtros['conciliado'].lower() == 'true'
        
        transacoes = extrato_functions.listar_transacoes_extrato(
            database,
            empresa_id,
            filtros
        )
        
        return jsonify(transacoes), 200
        
    except Exception as e:
        logger.info(f"Erro ao listar extratos: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/extratos/<int:transacao_id>/conciliar', methods=['POST'])
@require_permission('lancamentos_edit')
def conciliar_extrato(transacao_id):
    """Concilia uma transacao do extrato com um lancamento"""
    try:
        dados = request.json
        lancamento_id = dados.get('lancamento_id')
        
        resultado = extrato_functions.conciliar_transacao(
            database,
            transacao_id,
            lancamento_id
        )
        
        return jsonify(resultado), 200 if resultado['success'] else 400
        
    except Exception as e:
        logger.info(f"Erro ao conciliar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/extratos/<int:transacao_id>/sugestoes', methods=['GET'])
@require_permission('lancamentos_view')
def sugerir_conciliacoes_extrato(transacao_id):
    """Sugere lancamentos para conciliar com uma transacao"""
    try:
        usuario = get_usuario_logado()
        # Usar cliente_id como empresa_id (multi-tenancy)
        empresa_id = usuario.get('cliente_id') or usuario.get('empresa_id') or 1
        
        sugestoes = extrato_functions.sugerir_conciliacoes(
            database,
            empresa_id,
            transacao_id
        )
        
        return jsonify(sugestoes), 200
        
    except Exception as e:
        logger.info(f"Erro ao sugerir conciliacoes: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/extratos/importacao/<importacao_id>', methods=['DELETE'])
@require_permission('lancamentos_delete')
def deletar_importacao_extrato(importacao_id):
    """Deleta todas as transacoes de uma importacao"""
    try:
        resultado = extrato_functions.deletar_transacoes_extrato(
            database,
            importacao_id
        )
        
        return jsonify(resultado), 200 if resultado['success'] else 400
        
    except Exception as e:
        logger.info(f"Erro ao deletar importacao: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/extratos/deletar-filtrado', methods=['DELETE'])
@require_permission('lancamentos_delete')
def deletar_extrato_filtrado():
    """Deleta transacoes do extrato baseado em filtros"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('cliente_id') or usuario.get('empresa_id') or 1
        
        filtros = {
            'conta_bancaria': request.args.get('conta'),
            'data_inicio': request.args.get('data_inicio'),
            'data_fim': request.args.get('data_fim')
        }
        
        # Validar que pelo menos um filtro foi fornecido
        if not any(filtros.values()):
            return jsonify({
                'success': False, 
                'error': 'Pelo menos um filtro deve ser fornecido (conta, data_inicio ou data_fim)'
            }), 400
        
        # Deletar transações que correspondem aos filtros
        with db.get_connection() as conn:
            conn.autocommit = False
            cursor = conn.cursor()
            
            query = "DELETE FROM transacoes_extrato WHERE empresa_id = %s"
            params = [empresa_id]
            
            if filtros['conta_bancaria']:
                query += " AND conta_bancaria = %s"
                params.append(filtros['conta_bancaria'])
            
            if filtros['data_inicio']:
                query += " AND data >= %s"
                params.append(filtros['data_inicio'])
            
            if filtros['data_fim']:
                query += " AND data <= %s"
                params.append(filtros['data_fim'])
            
            cursor.execute(query, params)
            deletados = cursor.rowcount
            
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'deletados': deletados,
                'message': f'{deletados} transação(ões) deletada(s) com sucesso'
            }), 200
        
    except Exception as e:
        logger.info(f"Erro ao deletar extratos filtrados: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)}), 500


# === ROTAS DE FOLHA DE PAGAMENTO (FUNCIONÁRIOS) ===

@app.route('/api/funcionarios', methods=['GET'])
@require_permission('admin')
def listar_funcionarios():
    """Listar todos os funcionários da empresa"""
    try:
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        empresa_id = usuario.get('cliente_id') or usuario.get('empresa_id') or 1
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT id, empresa_id, nome, cpf, endereco, tipo_chave_pix, 
                   chave_pix, ativo, data_admissao, observacoes,
                   data_criacao, data_atualizacao
            FROM funcionarios
            WHERE empresa_id = %s
            ORDER BY nome ASC
        """
        
        cursor.execute(query, (empresa_id,))
        rows = cursor.fetchall()
        cursor.close()
        
        funcionarios = []
        for row in rows:
            # Verifica se row é dict ou tupla
            if isinstance(row, dict):
                funcionarios.append({
                    'id': row['id'],
                    'empresa_id': row['empresa_id'],
                    'nome': row['nome'],
                    'cpf': row['cpf'],
                    'endereco': row['endereco'],
                    'tipo_chave_pix': row['tipo_chave_pix'],
                    'chave_pix': row['chave_pix'],
                    'ativo': row['ativo'],
                    'data_admissao': row['data_admissao'].isoformat() if row['data_admissao'] else None,
                    'observacoes': row['observacoes'],
                    'data_criacao': row['data_criacao'].isoformat() if row['data_criacao'] else None,
                    'data_atualizacao': row['data_atualizacao'].isoformat() if row['data_atualizacao'] else None
                })
            else:
                funcionarios.append({
                    'id': row[0],
                    'empresa_id': row[1],
                    'nome': row[2],
                    'cpf': row[3],
                    'endereco': row[4],
                    'tipo_chave_pix': row[5],
                    'chave_pix': row[6],
                    'ativo': row[7],
                    'data_admissao': row[8].isoformat() if row[8] else None,
                    'observacoes': row[9],
                    'data_criacao': row[10].isoformat() if row[10] else None,
                    'data_atualizacao': row[11].isoformat() if row[11] else None
                })
        
        return jsonify({'funcionarios': funcionarios}), 200
    
    except Exception as e:
        logger.error(f"Erro ao listar funcionários: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/funcionarios', methods=['POST'])
@require_permission('admin')
def criar_funcionario():
    """Criar novo funcionário"""
    try:
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        empresa_id = usuario.get('cliente_id') or usuario.get('empresa_id') or 1
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 400
        
        dados = request.get_json()
        
        # Validações obrigatórias
        if not dados.get('nome'):
            return jsonify({'error': 'Nome é obrigatório'}), 400
        if not dados.get('cpf'):
            return jsonify({'error': 'CPF é obrigatório'}), 400
        if not dados.get('tipo_chave_pix'):
            return jsonify({'error': 'Tipo de chave PIX é obrigatório'}), 400
        
        # Limpar CPF (remover pontuação)
        cpf = dados['cpf'].replace('.', '').replace('-', '').replace('/', '')
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se CPF já existe
        cursor.execute("SELECT id FROM funcionarios WHERE cpf = %s AND empresa_id = %s", (cpf, empresa_id))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'CPF já cadastrado'}), 400
        
        query = """
            INSERT INTO funcionarios 
            (empresa_id, nome, cpf, endereco, tipo_chave_pix, chave_pix, data_admissao, observacoes, ativo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        cursor.execute(query, (
            empresa_id,
            dados['nome'],
            cpf,
            dados.get('endereco'),
            dados['tipo_chave_pix'],
            dados.get('chave_pix'),
            dados.get('data_admissao') if dados.get('data_admissao') else None,
            dados.get('observacoes'),
            dados.get('ativo', True)
        ))
        
        resultado = cursor.fetchone()
        funcionario_id = resultado['id'] if isinstance(resultado, dict) else resultado[0]
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'id': funcionario_id,
            'message': 'Funcionário cadastrado com sucesso'
        }), 201
    
    except Exception as e:
        logger.error(f"Erro ao criar funcionário: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/funcionarios/<int:funcionario_id>', methods=['PUT'])
@require_permission('admin')
def atualizar_funcionario(funcionario_id):
    """Atualizar funcionário existente"""
    try:
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        empresa_id = usuario.get('cliente_id') or usuario.get('empresa_id') or 1
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 400
        
        dados = request.get_json()
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se funcionário existe e pertence à empresa
        cursor.execute("SELECT id FROM funcionarios WHERE id = %s AND empresa_id = %s", (funcionario_id, empresa_id))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Funcionário não encontrado'}), 404
        
        # Construir query dinâmica baseada nos campos fornecidos
        campos_update = []
        valores = []
        
        if 'nome' in dados:
            campos_update.append("nome = %s")
            valores.append(dados['nome'])
        
        if 'cpf' in dados:
            cpf = dados['cpf'].replace('.', '').replace('-', '').replace('/', '')
            # Verificar se CPF já existe em outro funcionário
            cursor.execute("SELECT id FROM funcionarios WHERE cpf = %s AND empresa_id = %s AND id != %s", 
                         (cpf, empresa_id, funcionario_id))
            if cursor.fetchone():
                cursor.close()
                return jsonify({'error': 'CPF já cadastrado para outro funcionário'}), 400
            campos_update.append("cpf = %s")
            valores.append(cpf)
        
        if 'endereco' in dados:
            campos_update.append("endereco = %s")
            valores.append(dados['endereco'])
        
        if 'tipo_chave_pix' in dados:
            campos_update.append("tipo_chave_pix = %s")
            valores.append(dados['tipo_chave_pix'])
        
        if 'chave_pix' in dados:
            campos_update.append("chave_pix = %s")
            valores.append(dados['chave_pix'])
        
        if 'data_admissao' in dados:
            campos_update.append("data_admissao = %s")
            valores.append(dados['data_admissao'])
        
        if 'observacoes' in dados:
            campos_update.append("observacoes = %s")
            valores.append(dados['observacoes'])
        
        if 'ativo' in dados:
            campos_update.append("ativo = %s")
            valores.append(dados['ativo'])
        
        if not campos_update:
            cursor.close()
            return jsonify({'error': 'Nenhum campo para atualizar'}), 400
        
        campos_update.append("data_atualizacao = CURRENT_TIMESTAMP")
        valores.append(funcionario_id)
        
        query = f"UPDATE funcionarios SET {', '.join(campos_update)} WHERE id = %s"
        cursor.execute(query, valores)
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Funcionário atualizado com sucesso'
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao atualizar funcionário: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


# === ROTAS DE EVENTOS ===

@app.route('/api/eventos', methods=['GET'])
@require_permission('admin')
def listar_eventos():
    """Listar eventos com filtros opcionais"""
    try:
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        empresa_id = usuario.get('cliente_id') or usuario.get('empresa_id') or 1
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 400
        
        # Filtros opcionais
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        status = request.args.get('status')
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT id, empresa_id, nome_evento, data_evento, nf_associada,
                   valor_liquido_nf, custo_evento, margem, tipo_evento, status,
                   observacoes, data_criacao, data_atualizacao
            FROM eventos
            WHERE empresa_id = %s
        """
        params = [empresa_id]
        
        if data_inicio:
            query += " AND data_evento >= %s"
            params.append(data_inicio)
        
        if data_fim:
            query += " AND data_evento <= %s"
            params.append(data_fim)
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY data_evento DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        
        eventos = []
        for row in rows:
            # Verifica se row é dict ou tupla
            if isinstance(row, dict):
                eventos.append({
                    'id': row['id'],
                    'empresa_id': row['empresa_id'],
                    'nome_evento': row['nome_evento'],
                    'data_evento': row['data_evento'].isoformat() if row['data_evento'] else None,
                    'nf_associada': row['nf_associada'],
                    'valor_liquido_nf': float(row['valor_liquido_nf']) if row['valor_liquido_nf'] else None,
                    'custo_evento': float(row['custo_evento']) if row['custo_evento'] else None,
                    'margem': float(row['margem']) if row['margem'] else None,
                    'tipo_evento': row['tipo_evento'],
                    'status': row['status'],
                    'observacoes': row['observacoes'],
                    'data_criacao': row['data_criacao'].isoformat() if row['data_criacao'] else None,
                    'data_atualizacao': row['data_atualizacao'].isoformat() if row['data_atualizacao'] else None
                })
            else:
                eventos.append({
                    'id': row[0],
                    'empresa_id': row[1],
                    'nome_evento': row[2],
                    'data_evento': row[3].isoformat() if row[3] else None,
                    'nf_associada': row[4],
                    'valor_liquido_nf': float(row[5]) if row[5] else None,
                    'custo_evento': float(row[6]) if row[6] else None,
                    'margem': float(row[7]) if row[7] else None,
                    'tipo_evento': row[8],
                    'status': row[9],
                    'observacoes': row[10],
                    'data_criacao': row[11].isoformat() if row[11] else None,
                    'data_atualizacao': row[12].isoformat() if row[12] else None
                })
        
        return jsonify({'eventos': eventos}), 200
    
    except Exception as e:
        logger.error(f"Erro ao listar eventos: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/eventos', methods=['POST'])
@require_permission('admin')
def criar_evento():
    """Criar novo evento"""
    try:
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        empresa_id = usuario.get('cliente_id') or usuario.get('empresa_id') or 1
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 400
        
        dados = request.get_json()
        
        # Validações obrigatórias
        if not dados.get('nome_evento'):
            return jsonify({'error': 'Nome do evento é obrigatório'}), 400
        if not dados.get('data_evento'):
            return jsonify({'error': 'Data do evento é obrigatória'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        query = """
            INSERT INTO eventos 
            (empresa_id, nome_evento, data_evento, nf_associada, valor_liquido_nf,
             custo_evento, margem, tipo_evento, status, observacoes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        cursor.execute(query, (
            empresa_id,
            dados['nome_evento'],
            dados['data_evento'],
            dados.get('nf_associada'),
            dados.get('valor_liquido_nf'),
            dados.get('custo_evento'),
            dados.get('margem'),
            dados.get('tipo_evento'),
            dados.get('status', 'PENDENTE'),
            dados.get('observacoes')
        ))
        
        resultado = cursor.fetchone()
        evento_id = resultado['id'] if isinstance(resultado, dict) else resultado[0]
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'id': evento_id,
            'message': 'Evento cadastrado com sucesso'
        }), 201
    
    except Exception as e:
        logger.error(f"Erro ao criar evento: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/eventos/<int:evento_id>', methods=['PUT'])
@require_permission('admin')
def atualizar_evento(evento_id):
    """Atualizar evento existente"""
    try:
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        empresa_id = usuario.get('cliente_id') or usuario.get('empresa_id') or 1
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 400
        
        dados = request.get_json()
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se evento existe e pertence à empresa
        cursor.execute("SELECT id FROM eventos WHERE id = %s AND empresa_id = %s", (evento_id, empresa_id))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Evento não encontrado'}), 404
        
        # Construir query dinâmica baseada nos campos fornecidos
        campos_update = []
        valores = []
        
        if 'nome_evento' in dados:
            campos_update.append("nome_evento = %s")
            valores.append(dados['nome_evento'])
        
        if 'data_evento' in dados:
            campos_update.append("data_evento = %s")
            valores.append(dados['data_evento'])
        
        if 'nf_associada' in dados:
            campos_update.append("nf_associada = %s")
            valores.append(dados['nf_associada'])
        
        if 'valor_liquido_nf' in dados:
            campos_update.append("valor_liquido_nf = %s")
            valores.append(dados['valor_liquido_nf'])
        
        if 'custo_evento' in dados:
            campos_update.append("custo_evento = %s")
            valores.append(dados['custo_evento'])
        
        if 'margem' in dados:
            campos_update.append("margem = %s")
            valores.append(dados['margem'])
        
        if 'tipo_evento' in dados:
            campos_update.append("tipo_evento = %s")
            valores.append(dados['tipo_evento'])
        
        if 'status' in dados:
            campos_update.append("status = %s")
            valores.append(dados['status'])
        
        if 'observacoes' in dados:
            campos_update.append("observacoes = %s")
            valores.append(dados['observacoes'])
        
        if not campos_update:
            cursor.close()
            return jsonify({'error': 'Nenhum campo para atualizar'}), 400
        
        campos_update.append("data_atualizacao = CURRENT_TIMESTAMP")
        valores.append(evento_id)
        
        query = f"UPDATE eventos SET {', '.join(campos_update)} WHERE id = %s"
        cursor.execute(query, valores)
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Evento atualizado com sucesso'
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao atualizar evento: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/eventos/<int:evento_id>', methods=['DELETE'])
@require_permission('admin')
def deletar_evento(evento_id):
    """Deletar evento"""
    try:
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        empresa_id = usuario.get('cliente_id') or usuario.get('empresa_id') or 1
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se evento existe e pertence à empresa
        cursor.execute("SELECT id FROM eventos WHERE id = %s AND empresa_id = %s", (evento_id, empresa_id))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Evento não encontrado'}), 404
        
        # Deletar evento
        cursor.execute("DELETE FROM eventos WHERE id = %s", (evento_id,))
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Evento deletado com sucesso'
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao deletar evento: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


# === ROTAS DE RELATÓRIOS ===

@app.route('/api/relatorios/fluxo-caixa', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_fluxo_caixa():
    """Relatório de fluxo de caixa"""
    data_inicio_str = request.args.get('data_inicio', (date.today() - timedelta(days=30)).isoformat())
    data_fim_str = request.args.get('data_fim', date.today().isoformat())
    
    # Converter strings para date objects
    if isinstance(data_inicio_str, str):
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
    else:
        data_inicio = data_inicio_str
        
    if isinstance(data_fim_str, str):
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    else:
        data_fim = data_fim_str
    
    lancamentos = db.listar_lancamentos()
    
    # Filtrar lançamentos por cliente se necessário
    usuario = request.usuario
    if usuario['tipo'] != 'admin' and usuario.get('cliente_id'):
        lancamentos = [l for l in lancamentos if getattr(l, 'pessoa', None) == usuario['cliente_id']]
    
    lancamentos_periodo = []
    for l in lancamentos:
        if l.status == StatusLancamento.PAGO and l.data_pagamento:
            # Converter data_pagamento para date se for datetime
            if isinstance(l.data_pagamento, datetime):
                data_pgto = l.data_pagamento.date()
            else:
                data_pgto = l.data_pagamento
            
            # Comparar apenas se ambos forem date
            try:
                if data_inicio <= data_pgto <= data_fim:
                    lancamentos_periodo.append(l)
            except TypeError as e:
                print(f"ERRO: tipo data_inicio={type(data_inicio)}, data_pgto={type(data_pgto)}, data_fim={type(data_fim)}")
                print(f"Valores: {data_inicio} <= {data_pgto} <= {data_fim}")
                raise
    
    resultado = []
    for l in lancamentos_periodo:
        data_pgto = l.data_pagamento
        if hasattr(data_pgto, 'date'):
            data_pgto = data_pgto.date()
        
        # Para transferências, criar dois registros: débito na origem e crédito no destino
        if l.tipo == TipoLancamento.TRANSFERENCIA:
            # Débito na conta origem (aparece como DESPESA)
            resultado.append({
                'tipo': 'despesa',
                'descricao': f"{l.descricao} (Saída)",
                'valor': float(l.valor),
                'data_pagamento': data_pgto.isoformat() if data_pgto else None,
                'categoria': l.categoria,
                'subcategoria': l.subcategoria,
                'pessoa': l.pessoa,
                'conta_bancaria': l.conta_bancaria if hasattr(l, 'conta_bancaria') else None
            })
            # Crédito na conta destino (aparece como RECEITA)
            resultado.append({
                'tipo': 'receita',
                'descricao': f"{l.descricao} (Entrada)",
                'valor': float(l.valor),
                'data_pagamento': data_pgto.isoformat() if data_pgto else None,
                'categoria': l.categoria,
                'subcategoria': l.conta_bancaria,  # Inverter: origem vai para subcategoria
                'pessoa': l.pessoa,
                'conta_bancaria': l.subcategoria  # Destino vira a conta bancária
            })
        else:
            # Receitas e despesas normais
            resultado.append({
                'tipo': l.tipo.value,
                'descricao': l.descricao,
                'valor': float(l.valor),
                'data_pagamento': data_pgto.isoformat() if data_pgto else None,
                'categoria': l.categoria,
                'subcategoria': l.subcategoria,
                'pessoa': l.pessoa,
                'conta_bancaria': l.conta_bancaria if hasattr(l, 'conta_bancaria') else None
            })
    return jsonify(resultado)


@app.route('/api/relatorios/dashboard', methods=['GET'])
@require_permission('relatorios_view')
def dashboard():
    """Dados para o dashboard"""
    try:
        # Pegar filtros opcionais
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        
        lancamentos = db.listar_lancamentos()
        contas = db.listar_contas()
        
        # Filtrar lançamentos por cliente se necessário
        usuario = request.usuario
        if usuario['tipo'] != 'admin' and usuario.get('cliente_id'):
            lancamentos = [l for l in lancamentos if getattr(l, 'pessoa', None) == usuario['cliente_id']]
        
        # Calcular saldos
        saldo_total = Decimal('0')
        for c in contas:
            saldo_total += Decimal(str(c.saldo_inicial))
        
        for lanc in lancamentos:
            if lanc.status == StatusLancamento.PAGO and lanc.tipo != TipoLancamento.TRANSFERENCIA:
                valor_decimal = Decimal(str(lanc.valor))
                if lanc.tipo == TipoLancamento.RECEITA:
                    saldo_total += valor_decimal
                else:
                    saldo_total -= valor_decimal
        
        # Contas pendentes
        hoje = date.today()
        contas_receber = Decimal('0')
        contas_pagar = Decimal('0')
        contas_vencidas = Decimal('0')
        
        for l in lancamentos:
            if l.tipo != TipoLancamento.TRANSFERENCIA:
                valor_decimal = Decimal(str(l.valor))
                if l.tipo == TipoLancamento.RECEITA and l.status == StatusLancamento.PENDENTE:
                    contas_receber += valor_decimal
                if l.tipo == TipoLancamento.DESPESA and l.status == StatusLancamento.PENDENTE:
                    contas_pagar += valor_decimal
                # Converter datetime para date se necessário
                data_venc = l.data_vencimento.date() if hasattr(l.data_vencimento, 'date') else l.data_vencimento
                if l.status == StatusLancamento.PENDENTE and data_venc < hoje:
                    contas_vencidas += valor_decimal
        
        # Dados para gráfico - últimos 12 meses ou filtrado por ano/mês
        from calendar import monthrange
        import locale
        
        # Tentar configurar locale para português
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
            except:
                pass
        
        meses_labels = []
        receitas_dados = []
        despesas_dados = []
        
        if ano and mes:
            # Apenas um mês específico
            _, ultimo_dia = monthrange(ano, mes)
            data_inicio = date(ano, mes, 1)
            data_fim = date(ano, mes, ultimo_dia)
            
            lancamentos_periodo = [
                l for l in lancamentos 
                if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA
                and data_inicio <= (l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento) <= data_fim
            ]
            
            receitas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.RECEITA)
            despesas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.DESPESA)
            
            meses_labels = [data_inicio.strftime('%b/%Y')]
            receitas_dados = [float(receitas_mes)]
            despesas_dados = [float(despesas_mes)]
        
        elif ano:
            # Todos os meses do ano
            for m in range(1, 13):
                _, ultimo_dia = monthrange(ano, m)
                data_inicio = date(ano, m, 1)
                data_fim = date(ano, m, ultimo_dia)
                
                lancamentos_periodo = [
                    l for l in lancamentos 
                    if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA
                    and data_inicio <= (l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento) <= data_fim
                ]
                
                receitas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.RECEITA)
                despesas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.DESPESA)
                
                meses_labels.append(data_inicio.strftime('%b/%Y'))
                receitas_dados.append(float(receitas_mes))
                despesas_dados.append(float(despesas_mes))
        
        else:
            # Últimos 12 meses
            data_ref = hoje
            for i in range(11, -1, -1):
                mes_ref = data_ref.month - i
                ano_ref = data_ref.year
                
                while mes_ref <= 0:
                    mes_ref += 12
                    ano_ref -= 1
                
                _, ultimo_dia = monthrange(ano_ref, mes_ref)
                data_inicio = date(ano_ref, mes_ref, 1)
                data_fim = date(ano_ref, mes_ref, ultimo_dia)
                
                lancamentos_periodo = [
                    l for l in lancamentos 
                    if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA
                    and data_inicio <= (l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento) <= data_fim
                ]
                
                receitas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.RECEITA)
                despesas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.DESPESA)
                
                meses_labels.append(data_inicio.strftime('%b/%Y'))
                receitas_dados.append(float(receitas_mes))
                despesas_dados.append(float(despesas_mes))
        
        return jsonify({
            'saldo_total': float(saldo_total),
            'contas_receber': float(contas_receber),
            'contas_pagar': float(contas_pagar),
            'contas_vencidas': float(contas_vencidas),
            'total_contas': len(contas),
            'total_lancamentos': len(lancamentos),
            'meses': meses_labels,
            'receitas': receitas_dados,
            'despesas': despesas_dados
        })
    except Exception as e:
        print(f"Erro no dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/relatorios/dashboard-completo', methods=['GET'])
@require_permission('relatorios_view')
def dashboard_completo():
    """Dashboard completo com análises detalhadas - apenas lançamentos liquidados"""
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        if not data_inicio or not data_fim:
            return jsonify({'error': 'Datas obrigatórias'}), 400
        
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
        
        lancamentos = db.listar_lancamentos()
        
        # Filtrar lançamentos por cliente se necessário
        usuario = request.usuario
        if usuario['tipo'] != 'admin' and usuario.get('cliente_id'):
            lancamentos = [l for l in lancamentos if getattr(l, 'pessoa', None) == usuario['cliente_id']]
        
        # Filtrar apenas lançamentos PAGOS/LIQUIDADOS no período (baseado na data de pagamento)
        # Excluir transferências dos relatórios
        lancamentos_periodo = []
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_inicio_obj <= data_pag <= data_fim_obj:
                    lancamentos_periodo.append(l)
        
        # Evolução mensal (baseado na data de pagamento)
        evolucao = []
        current_date = data_inicio_obj
        
        while current_date <= data_fim_obj:
            mes_inicio = current_date.replace(day=1)
            if current_date.month == 12:
                mes_fim = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                mes_fim = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
            
            # Filtrar por data de pagamento
            lancamentos_mes = [
                l for l in lancamentos_periodo
                if mes_inicio <= (l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento) <= mes_fim
            ]
            
            receitas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_mes if l.tipo == TipoLancamento.RECEITA)
            despesas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_mes if l.tipo == TipoLancamento.DESPESA)
            saldo_mes = receitas_mes - despesas_mes
            
            evolucao.append({
                'periodo': current_date.strftime('%b/%y'),
                'receitas': float(receitas_mes),
                'despesas': float(despesas_mes),
                'saldo': float(saldo_mes)
            })
            
            # Avançar para o próximo mês
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
        
        # Análise de Clientes
        clientes_resumo = {}
        for l in lancamentos_periodo:
            if l.tipo == TipoLancamento.RECEITA and l.pessoa:
                if l.pessoa not in clientes_resumo:
                    clientes_resumo[l.pessoa] = {'total': Decimal('0'), 'quantidade': 0}
                clientes_resumo[l.pessoa]['total'] += Decimal(str(l.valor))
                clientes_resumo[l.pessoa]['quantidade'] += 1
        
        melhor_cliente = None
        pior_cliente = None
        if clientes_resumo:
            melhor_cliente_nome = max(clientes_resumo, key=lambda x: clientes_resumo[x]['total'])
            pior_cliente_nome = min(clientes_resumo, key=lambda x: clientes_resumo[x]['total'])
            
            melhor_cliente = {
                'nome': melhor_cliente_nome,
                'total': float(clientes_resumo[melhor_cliente_nome]['total']),
                'quantidade': clientes_resumo[melhor_cliente_nome]['quantidade']
            }
            pior_cliente = {
                'nome': pior_cliente_nome,
                'total': float(clientes_resumo[pior_cliente_nome]['total']),
                'quantidade': clientes_resumo[pior_cliente_nome]['quantidade']
            }
        
        # Análise de Fornecedores
        fornecedores_resumo = {}
        for l in lancamentos_periodo:
            if l.tipo == TipoLancamento.DESPESA and l.pessoa:
                if l.pessoa not in fornecedores_resumo:
                    fornecedores_resumo[l.pessoa] = {'total': Decimal('0'), 'quantidade': 0}
                fornecedores_resumo[l.pessoa]['total'] += Decimal(str(l.valor))
                fornecedores_resumo[l.pessoa]['quantidade'] += 1
        
        maior_fornecedor = None
        menor_fornecedor = None
        if fornecedores_resumo:
            maior_fornecedor_nome = max(fornecedores_resumo, key=lambda x: fornecedores_resumo[x]['total'])
            menor_fornecedor_nome = min(fornecedores_resumo, key=lambda x: fornecedores_resumo[x]['total'])
            
            maior_fornecedor = {
                'nome': maior_fornecedor_nome,
                'total': float(fornecedores_resumo[maior_fornecedor_nome]['total']),
                'quantidade': fornecedores_resumo[maior_fornecedor_nome]['quantidade']
            }
            menor_fornecedor = {
                'nome': menor_fornecedor_nome,
                'total': float(fornecedores_resumo[menor_fornecedor_nome]['total']),
                'quantidade': fornecedores_resumo[menor_fornecedor_nome]['quantidade']
            }
        
        # Análise de Categorias - Receitas
        categorias_receita = {}
        for l in lancamentos_periodo:
            if l.tipo == TipoLancamento.RECEITA:
                cat = l.categoria or 'Sem categoria'
                subcat = l.subcategoria or 'Sem subcategoria'
                
                if cat not in categorias_receita:
                    categorias_receita[cat] = {}
                if subcat not in categorias_receita[cat]:
                    categorias_receita[cat][subcat] = Decimal('0')
                
                categorias_receita[cat][subcat] += Decimal(str(l.valor))
        
        melhor_categoria_receita = None
        if categorias_receita:
            melhor_cat = max(categorias_receita, key=lambda x: sum(categorias_receita[x].values()))
            melhor_subcat = max(categorias_receita[melhor_cat], key=lambda x: categorias_receita[melhor_cat][x])
            
            melhor_categoria_receita = {
                'categoria': melhor_cat,
                'subcategoria': melhor_subcat if melhor_subcat != 'Sem subcategoria' else None,
                'total': float(categorias_receita[melhor_cat][melhor_subcat])
            }
        
        # Análise de Categorias - Despesas
        categorias_despesa = {}
        for l in lancamentos_periodo:
            if l.tipo == TipoLancamento.DESPESA:
                cat = l.categoria or 'Sem categoria'
                subcat = l.subcategoria or 'Sem subcategoria'
                
                if cat not in categorias_despesa:
                    categorias_despesa[cat] = {}
                if subcat not in categorias_despesa[cat]:
                    categorias_despesa[cat][subcat] = Decimal('0')
                
                categorias_despesa[cat][subcat] += Decimal(str(l.valor))
        
        maior_categoria_despesa = None
        if categorias_despesa:
            maior_cat = max(categorias_despesa, key=lambda x: sum(categorias_despesa[x].values()))
            maior_subcat = max(categorias_despesa[maior_cat], key=lambda x: categorias_despesa[maior_cat][x])
            
            maior_categoria_despesa = {
                'categoria': maior_cat,
                'subcategoria': maior_subcat if maior_subcat != 'Sem subcategoria' else None,
                'total': float(categorias_despesa[maior_cat][maior_subcat])
            }
        
        return jsonify({
            'evolucao': evolucao,
            'melhor_cliente': melhor_cliente,
            'pior_cliente': pior_cliente,
            'maior_fornecedor': maior_fornecedor,
            'menor_fornecedor': menor_fornecedor,
            'melhor_categoria_receita': melhor_categoria_receita,
            'maior_categoria_despesa': maior_categoria_despesa
        })
        
    except Exception as e:
        print(f"Erro no dashboard completo: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/relatorios/fluxo-projetado', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_fluxo_projetado():
    """Relatório de fluxo de caixa PROJETADO (incluindo lançamentos pendentes futuros)"""
    try:
        # Receber filtros - padrão é projetar próximos X dias
        dias = request.args.get('dias')
        dias = int(dias) if dias else 30
        
        hoje = date.today()
        data_inicial = hoje
        data_final = hoje + timedelta(days=dias)
        periodo_texto = f"PROJEÇÃO - PRÓXIMOS {dias} DIAS"
        
        lancamentos = db.listar_lancamentos()
        contas = db.listar_contas()
        
        # Filtrar lançamentos por cliente se necessário
        usuario = request.usuario
        if usuario['tipo'] != 'admin' and usuario.get('cliente_id'):
            lancamentos = [l for l in lancamentos if getattr(l, 'pessoa', None) == usuario['cliente_id']]
        
        # Saldo atual (saldo inicial + todos os lançamentos pagos até hoje)
        saldo_atual = Decimal('0')
        for c in contas:
            saldo_atual += Decimal(str(c.saldo_inicial))
        
        # Adicionar todas as receitas e despesas JÁ PAGAS até hoje (exceto transferências)
        for l in lancamentos:
            # Converter data_pagamento para date se for datetime
            if l.data_pagamento:
                if isinstance(l.data_pagamento, datetime):
                    data_pgto = l.data_pagamento.date()
                else:
                    data_pgto = l.data_pagamento
            else:
                data_pgto = None
            
            if l.status == StatusLancamento.PAGO and data_pgto and data_pgto <= hoje and l.tipo != TipoLancamento.TRANSFERENCIA:
                valor_decimal = Decimal(str(l.valor))
                if l.tipo == TipoLancamento.RECEITA:
                    saldo_atual += valor_decimal
                else:
                    saldo_atual -= valor_decimal
        
        # Buscar lançamentos PENDENTES para projeção (vencidos + futuros)
        lancamentos_futuros = []
        lancamentos_vencidos = []
        receitas_previstas = Decimal('0')
        despesas_previstas = Decimal('0')
        receitas_vencidas = Decimal('0')
        despesas_vencidas = Decimal('0')
        
        for l in lancamentos:
            if l.status == StatusLancamento.PENDENTE and l.tipo != TipoLancamento.TRANSFERENCIA:
                # Converter data_vencimento para date se for datetime
                if isinstance(l.data_vencimento, datetime):
                    data_venc = l.data_vencimento.date()
                else:
                    data_venc = l.data_vencimento
                
                valor_decimal = Decimal(str(l.valor))
                
                # Lançamentos vencidos (já passaram do vencimento)
                if data_venc < hoje:
                    lancamentos_vencidos.append(l)
                    if l.tipo == TipoLancamento.RECEITA:
                        receitas_vencidas += valor_decimal
                    else:
                        despesas_vencidas += valor_decimal
                
                # Lançamentos futuros (dentro do período de projeção)
                elif data_inicial <= data_venc <= data_final:
                    lancamentos_futuros.append(l)
                    if l.tipo == TipoLancamento.RECEITA:
                        receitas_previstas += valor_decimal
                    else:
                        despesas_previstas += valor_decimal
        
        # Calcular saldo projetado (incluindo vencidos)
        saldo_projetado = saldo_atual + (receitas_previstas + receitas_vencidas) - (despesas_previstas + despesas_vencidas)
        
        # Ordenar por data de vencimento
        lancamentos_vencidos.sort(key=lambda x: x.data_vencimento)
        lancamentos_futuros.sort(key=lambda x: x.data_vencimento)
        
        # Montar fluxo projetado dia a dia (VENCIDOS PRIMEIRO, depois futuros)
        fluxo = []
        saldo_acumulado = saldo_atual
        
        # Adicionar vencidos primeiro
        for lanc in lancamentos_vencidos:
            valor_decimal = Decimal(str(lanc.valor))
            if lanc.tipo == TipoLancamento.RECEITA:
                saldo_acumulado += valor_decimal
            else:
                saldo_acumulado -= valor_decimal
            
            # Calcular dias de atraso
            data_venc_date = lanc.data_vencimento.date() if isinstance(lanc.data_vencimento, datetime) else lanc.data_vencimento
            dias_atraso = (hoje - data_venc_date).days
            
            fluxo.append({
                'data_vencimento': lanc.data_vencimento.isoformat(),
                'descricao': lanc.descricao,
                'tipo': lanc.tipo.value,
                'valor': float(lanc.valor),
                'categoria': lanc.categoria,
                'subcategoria': lanc.subcategoria,
                'pessoa': lanc.pessoa,
                'conta_bancaria': lanc.conta_bancaria,
                'saldo_acumulado': float(saldo_acumulado),
                'status': 'VENCIDO',
                'dias_atraso': dias_atraso
            })
        
        # Adicionar lançamentos futuros
        for lanc in lancamentos_futuros:
            valor_decimal = Decimal(str(lanc.valor))
            if lanc.tipo == TipoLancamento.RECEITA:
                saldo_acumulado += valor_decimal
            else:
                saldo_acumulado -= valor_decimal
            
            fluxo.append({
                'data_vencimento': lanc.data_vencimento.isoformat(),
                'descricao': lanc.descricao,
                'tipo': lanc.tipo.value,
                'valor': float(lanc.valor),
                'categoria': lanc.categoria,
                'subcategoria': lanc.subcategoria,
                'pessoa': lanc.pessoa,
                'conta_bancaria': lanc.conta_bancaria,
                'saldo_acumulado': float(saldo_acumulado),
                'status': 'PENDENTE',
                'dias_atraso': 0
            })
        
        return jsonify({
            'periodo_texto': periodo_texto,
            'data_inicial': data_inicial.isoformat(),
            'data_final': data_final.isoformat(),
            'saldo_atual': float(saldo_atual),
            'receitas_previstas': float(receitas_previstas),
            'despesas_previstas': float(despesas_previstas),
            'receitas_vencidas': float(receitas_vencidas),
            'despesas_vencidas': float(despesas_vencidas),
            'saldo_projetado': float(saldo_projetado),
            'total_vencidos': len(lancamentos_vencidos),
            'total_futuros': len(lancamentos_futuros),
            'fluxo': fluxo
        })
    except Exception as e:
        print(f"Erro no fluxo projetado: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/relatorios/analise-contas', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_analise_contas():
    """Relatório de análise de contas a pagar e receber"""
    lancamentos = db.listar_lancamentos()
    hoje = date.today()
    
    # Filtrar lançamentos por cliente se necessário
    usuario = request.usuario
    if usuario['tipo'] != 'admin' and usuario.get('cliente_id'):
        lancamentos = [l for l in lancamentos if getattr(l, 'pessoa', None) == usuario['cliente_id']]
    
    # Função auxiliar para converter datetime para date
    def get_date(data):
        return data.date() if hasattr(data, 'date') else data
    
    # Totais (excluindo transferências)
    total_receber = sum(l.valor for l in lancamentos 
                       if l.tipo == TipoLancamento.RECEITA and l.status == StatusLancamento.PENDENTE)
    total_pagar = sum(l.valor for l in lancamentos 
                     if l.tipo == TipoLancamento.DESPESA and l.status == StatusLancamento.PENDENTE)
    
    receber_vencidos = sum(l.valor for l in lancamentos 
                          if l.tipo == TipoLancamento.RECEITA and 
                          l.status == StatusLancamento.PENDENTE and 
                          get_date(l.data_vencimento) < hoje)
    pagar_vencidos = sum(l.valor for l in lancamentos 
                        if l.tipo == TipoLancamento.DESPESA and 
                        l.status == StatusLancamento.PENDENTE and 
                        get_date(l.data_vencimento) < hoje)
    
    # Aging (análise de vencimento) - excluindo transferências
    pendentes = [l for l in lancamentos if l.status == StatusLancamento.PENDENTE and l.tipo != TipoLancamento.TRANSFERENCIA]
    
    vencidos = sum(l.valor for l in pendentes if (get_date(l.data_vencimento) - hoje).days < 0)  # type: ignore
    ate_7 = sum(l.valor for l in pendentes if 0 <= (get_date(l.data_vencimento) - hoje).days <= 7)  # type: ignore
    ate_15 = sum(l.valor for l in pendentes if 7 < (get_date(l.data_vencimento) - hoje).days <= 15)  # type: ignore
    ate_30 = sum(l.valor for l in pendentes if 15 < (get_date(l.data_vencimento) - hoje).days <= 30)  # type: ignore
    ate_60 = sum(l.valor for l in pendentes if 30 < (get_date(l.data_vencimento) - hoje).days <= 60)  # type: ignore
    ate_90 = sum(l.valor for l in pendentes if 60 < (get_date(l.data_vencimento) - hoje).days <= 90)  # type: ignore
    acima_90 = sum(l.valor for l in pendentes if (get_date(l.data_vencimento) - hoje).days > 90)  # type: ignore
    
    return jsonify({
        'total_receber': float(total_receber),
        'total_pagar': float(total_pagar),
        'receber_vencidos': float(receber_vencidos),
        'pagar_vencidos': float(pagar_vencidos),
        'aging': {
            'vencidos': float(vencidos),
            'ate_7': float(ate_7),
            'ate_15': float(ate_15),
            'ate_30': float(ate_30),
            'ate_60': float(ate_60),
            'ate_90': float(ate_90),
            'acima_90': float(acima_90)
        }
    })


@app.route('/api/lancamentos/<int:lancamento_id>/pagar', methods=['PUT'])
@require_permission('lancamentos_edit')
def pagar_lancamento(lancamento_id):
    """Marca um lançamento como pago"""
    try:
        data = request.json
        conta = data.get('conta_bancaria', '') if data else ''
        data_pagamento = datetime.fromisoformat(data.get('data_pagamento', datetime.now().isoformat())).date() if data else date.today()
        juros = float(data.get('juros', 0)) if data else 0
        desconto = float(data.get('desconto', 0)) if data else 0
        observacoes = data.get('observacoes', '') if data else ''
        
        success = db_pagar_lancamento(lancamento_id, conta, data_pagamento, juros, desconto, observacoes)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/lancamentos/<int:lancamento_id>/liquidar', methods=['POST'])
@require_permission('lancamentos_edit')
def liquidar_lancamento(lancamento_id):
    """Liquida um lançamento (marca como pago com dados completos)"""
    try:
        print("\n" + "="*80)
        print(f"🔍 DEBUG LIQUIDAÇÃO - ID: {lancamento_id}")
        print("="*80)
        
        data = request.json or {}
        print(f"📥 Dados recebidos: {data}")
        
        conta = data.get('conta_bancaria', '')
        data_pagamento_str = data.get('data_pagamento', '')
        juros = float(data.get('juros', 0))
        desconto = float(data.get('desconto', 0))
        observacoes = data.get('observacoes', '')
        
        print(f"📊 Parâmetros extraídos:")
        print(f"   - Conta: {conta}")
        print(f"   - Data: {data_pagamento_str}")
        print(f"   - Juros: {juros}")
        print(f"   - Desconto: {desconto}")
        print(f"   - Observações: {observacoes}")
        
        if not conta:
            print("❌ ERRO: Conta bancária vazia")
            return jsonify({'success': False, 'error': 'Conta bancária é obrigatória'}), 400
        
        if not data_pagamento_str or data_pagamento_str.strip() == '':
            print("❌ ERRO: Data de pagamento vazia")
            return jsonify({'success': False, 'error': 'Data de pagamento é obrigatória'}), 400
        
        data_pagamento = datetime.fromisoformat(data_pagamento_str).date()
        print(f"📅 Data convertida: {data_pagamento} (tipo: {type(data_pagamento)})")
        
        print(f"🔧 Chamando db_pagar_lancamento...")
        print(f"   Argumentos: ({lancamento_id}, {conta}, {data_pagamento}, {juros}, {desconto}, {observacoes})")
        
        success = db_pagar_lancamento(lancamento_id, conta, data_pagamento, juros, desconto, observacoes)
        
        print(f"✅ Resultado: {success}")
        print("="*80 + "\n")
        
        return jsonify({'success': success})
    except Exception as e:
        print(f"❌ EXCEÇÃO CAPTURADA:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        print("="*80 + "\n")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/lancamentos/<int:lancamento_id>/cancelar', methods=['PUT'])
@require_permission('lancamentos_edit')
def cancelar_lancamento_route(lancamento_id):
    """Cancela um lançamento"""
    try:
        success = db_cancelar_lancamento(lancamento_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# === ROTA PRINCIPAL ===

@app.route('/login')
def login_page():
    """Página de login"""
    return render_template('login.html')

@app.route('/admin')
@require_admin
def admin_page():
    """Painel administrativo - apenas para admins"""
    print(f"\n🎯🎯🎯 ROTA /admin ALCANÇADA - Decorador passou! 🎯🎯🎯\n")
    return render_template('admin.html')

# ============================================================================
# ROTAS DE ADMINISTRAÇÃO MOBILE
# ============================================================================

@app.route('/api/admin/mobile/config', methods=['GET'])
@require_admin
def admin_get_mobile_config():
    """
    Obtém informações básicas sobre mobile (apenas detecção de dispositivo)
    
    GET /api/admin/mobile/config
    
    Response: {
        "success": true,
        "device_info": {...}
    }
    """
    try:
        device_info = get_device_info()
        
        return jsonify({
            'success': True,
            'device_info': device_info,
            'message': 'Sistema usa detecção básica de dispositivos mobile'
        }), 200
    except Exception as e:
        logger.error(f"Erro ao obter info mobile: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/mobile/config/<key>', methods=['PUT'])
@require_admin
def admin_update_mobile_config(key):
    """
    Atualiza uma configuração mobile (admin apenas)
    
    PUT /api/admin/mobile/config/mobile_enabled
    Body: {
        "value": "true",
        "description": "Habilitar versão mobile"
    }
    
    Response: {
        "success": false,
        "message": "Configurações mobile simplificadas - não há configurações para atualizar"
    }
    """
    return jsonify({
        'success': False,
        'message': 'Sistema usa detecção básica de mobile - não há configurações dinâmicas',
        'info': 'Mobile detection baseado em User-Agent apenas'
    }), 400


@app.route('/api/device-info', methods=['GET'])
def get_device_info_route():
    """
    Retorna informações sobre o dispositivo atual
    Útil para debug e UI
    
    GET /api/device-info
    
    Response: {
        "is_mobile": true,
        "is_mobile_app": false,
        "platform": "android",
        "os": "Android",
        "user_agent": "..."
    }
    """
    device_info = get_device_info()
    return jsonify(device_info), 200


@app.route('/api/device-preference', methods=['POST'])
@require_auth
def set_device_preference_route():
    """
    Define preferência de dispositivo do usuário
    
    POST /api/device-preference
    Body: {
        "preference": "web" | "mobile"
    }
    
    Response: {
        "success": true,
        "preference": "web"
    }
    """
    try:
        data = request.get_json()
        preference = data.get('preference', 'web')
        
        if preference not in ['web', 'mobile']:
            return jsonify({
                'success': False,
                'error': 'Preferência inválida. Use "web" ou "mobile".'
            }), 400
        
        from mobile_config import store_device_preference
        store_device_preference(preference)
        
        return jsonify({
            'success': True,
            'preference': preference
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/debug-usuario')
def debug_usuario():
    """Rota de debug para verificar dados do usuário atual"""
    usuario = get_usuario_logado()
    
    debug_info = {
        'encontrado': usuario is not None,
        'dados': {}
    }
    
    if usuario:
        debug_info['dados'] = {
            'id': usuario.get('id'),
            'username': usuario.get('username'),
            'tipo': usuario.get('tipo'),
            'tipo_python_type': str(type(usuario.get('tipo'))),
            'tipo_repr': repr(usuario.get('tipo')),
            'tipo_len': len(usuario.get('tipo', '')),
            'tipo_bytes': list(usuario.get('tipo', '').encode()) if usuario.get('tipo') else [],
            'tipo_comparacao_admin': usuario.get('tipo') == 'admin',
            'tipo_comparacao_cliente': usuario.get('tipo') == 'cliente',
            'nome_completo': usuario.get('nome_completo'),
            'email': usuario.get('email'),
            'cliente_id': usuario.get('cliente_id')
        }
    
    return jsonify(debug_info)

@app.route('/')
def index():
    """Página principal - Nova interface moderna"""
    # Verificar se está autenticado
    usuario = get_usuario_logado()
    if not usuario:
        return render_template('login.html')
    
    # Passa o timestamp de build para o template
    return render_template('interface_nova.html', build_timestamp=BUILD_TIMESTAMP)

@app.route('/old')
@require_auth
def old_index():
    """Página antiga (backup)"""
    return render_template('interface.html')

@app.route('/teste')
def teste():
    """Página de teste JavaScript"""
    return render_template('teste.html')

@app.route('/teste-api')
def teste_api():
    """Página de teste API"""
    return render_template('teste_api.html')

# === ENDPOINTS DE RELATÓRIOS ===

@app.route('/api/relatorios/resumo-parceiros', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_resumo_parceiros():
    """Relatório de resumo por cliente/fornecedor"""
    try:
        data_inicio = request.args.get('data_inicio', (date.today() - timedelta(days=30)).isoformat())
        data_fim = request.args.get('data_fim', date.today().isoformat())
        
        data_inicio = datetime.fromisoformat(data_inicio).date()
        data_fim = datetime.fromisoformat(data_fim).date()
        
        lancamentos = db.listar_lancamentos()
        
        # Agrupar por pessoa
        resumo_clientes = {}
        resumo_fornecedores = {}
        
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_inicio <= data_pag <= data_fim and l.pessoa:
                    valor = float(l.valor)
                    categoria = l.categoria or 'Sem categoria'
                    
                    if l.tipo == TipoLancamento.RECEITA:
                        if l.pessoa not in resumo_clientes:
                            resumo_clientes[l.pessoa] = {'total': 0, 'quantidade': 0, 'categorias': {}}
                        resumo_clientes[l.pessoa]['total'] += valor
                        resumo_clientes[l.pessoa]['quantidade'] += 1
                        # Contar por categoria
                        if categoria not in resumo_clientes[l.pessoa]['categorias']:
                            resumo_clientes[l.pessoa]['categorias'][categoria] = 0
                        resumo_clientes[l.pessoa]['categorias'][categoria] += valor
                    else:
                        if l.pessoa not in resumo_fornecedores:
                            resumo_fornecedores[l.pessoa] = {'total': 0, 'quantidade': 0, 'categorias': {}}
                        resumo_fornecedores[l.pessoa]['total'] += valor
                        resumo_fornecedores[l.pessoa]['quantidade'] += 1
                        # Contar por categoria
                        if categoria not in resumo_fornecedores[l.pessoa]['categorias']:
                            resumo_fornecedores[l.pessoa]['categorias'][categoria] = 0
                        resumo_fornecedores[l.pessoa]['categorias'][categoria] += valor
        
        # Adicionar categoria principal para cada cliente/fornecedor
        for pessoa, dados in resumo_clientes.items():
            if dados['categorias']:
                categoria_principal = max(dados['categorias'].items(), key=lambda x: x[1])
                dados['categoria_principal'] = categoria_principal[0]
            else:
                dados['categoria_principal'] = 'Sem categoria'
        
        for pessoa, dados in resumo_fornecedores.items():
            if dados['categorias']:
                categoria_principal = max(dados['categorias'].items(), key=lambda x: x[1])
                dados['categoria_principal'] = categoria_principal[0]
            else:
                dados['categoria_principal'] = 'Sem categoria'
        
        return jsonify({
            'clientes': resumo_clientes,
            'fornecedores': resumo_fornecedores,
            'periodo': {
                'inicio': data_inicio.isoformat(),
                'fim': data_fim.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/relatorios/analise-categorias', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_analise_categorias():
    """Relatório de análise por categorias"""
    try:
        data_inicio = request.args.get('data_inicio', (date.today() - timedelta(days=30)).isoformat())
        data_fim = request.args.get('data_fim', date.today().isoformat())
        
        data_inicio = datetime.fromisoformat(data_inicio).date()
        data_fim = datetime.fromisoformat(data_fim).date()
        
        lancamentos = db.listar_lancamentos()
        
        # Agrupar por categoria e subcategoria
        receitas = {}
        despesas = {}
        
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_inicio <= data_pag <= data_fim:
                    categoria = l.categoria or 'Sem Categoria'
                    subcategoria = l.subcategoria or 'Sem Subcategoria'
                    valor = float(l.valor)
                    
                    if l.tipo == TipoLancamento.RECEITA:
                        if categoria not in receitas:
                            receitas[categoria] = {}
                        if subcategoria not in receitas[categoria]:
                            receitas[categoria][subcategoria] = {'total': 0, 'quantidade': 0}
                        receitas[categoria][subcategoria]['total'] += valor
                        receitas[categoria][subcategoria]['quantidade'] += 1
                    else:
                        if categoria not in despesas:
                            despesas[categoria] = {}
                        if subcategoria not in despesas[categoria]:
                            despesas[categoria][subcategoria] = {'total': 0, 'quantidade': 0}
                        despesas[categoria][subcategoria]['total'] += valor
                        despesas[categoria][subcategoria]['quantidade'] += 1
        
        return jsonify({
            'receitas': receitas,
            'despesas': despesas,
            'periodo': {
                'inicio': data_inicio.isoformat(),
                'fim': data_fim.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/relatorios/comparativo-periodos', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_comparativo_periodos():
    """Relatório comparativo entre períodos"""
    try:
        # Período 1
        data_inicio1 = request.args.get('data_inicio1')
        data_fim1 = request.args.get('data_fim1')
        
        # Período 2
        data_inicio2 = request.args.get('data_inicio2')
        data_fim2 = request.args.get('data_fim2')
        
        if not all([data_inicio1, data_fim1, data_inicio2, data_fim2]):
            return jsonify({'error': 'Parâmetros de datas obrigatórios'}), 400
        
        data_inicio1 = datetime.fromisoformat(data_inicio1).date()
        data_fim1 = datetime.fromisoformat(data_fim1).date()
        data_inicio2 = datetime.fromisoformat(data_inicio2).date()
        data_fim2 = datetime.fromisoformat(data_fim2).date()
        
        lancamentos = db.listar_lancamentos()
        
        def calcular_periodo(data_ini, data_fim):
            receitas = Decimal('0')
            despesas = Decimal('0')
            receitas_por_categoria = {}
            despesas_por_categoria = {}
            receitas_por_subcategoria = {}
            despesas_por_subcategoria = {}
            
            for l in lancamentos:
                if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                    data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                    if data_ini <= data_pag <= data_fim:
                        valor = Decimal(str(l.valor))
                        categoria = l.categoria or 'Sem categoria'
                        subcategoria = l.subcategoria or 'Sem subcategoria'
                        chave_completa = f"{categoria} > {subcategoria}"
                        
                        if l.tipo == TipoLancamento.RECEITA:
                            receitas += valor
                            receitas_por_categoria[categoria] = receitas_por_categoria.get(categoria, Decimal('0')) + valor
                            receitas_por_subcategoria[chave_completa] = receitas_por_subcategoria.get(chave_completa, Decimal('0')) + valor
                        else:
                            despesas += valor
                            despesas_por_categoria[categoria] = despesas_por_categoria.get(categoria, Decimal('0')) + valor
                            despesas_por_subcategoria[chave_completa] = despesas_por_subcategoria.get(chave_completa, Decimal('0')) + valor
            
            # Encontrar maiores por categoria
            maior_receita_cat = max(receitas_por_categoria.items(), key=lambda x: x[1]) if receitas_por_categoria else ('Nenhuma', Decimal('0'))
            maior_despesa_cat = max(despesas_por_categoria.items(), key=lambda x: x[1]) if despesas_por_categoria else ('Nenhuma', Decimal('0'))
            
            # Encontrar maiores por subcategoria
            maior_receita_sub = max(receitas_por_subcategoria.items(), key=lambda x: x[1]) if receitas_por_subcategoria else ('Nenhuma', Decimal('0'))
            maior_despesa_sub = max(despesas_por_subcategoria.items(), key=lambda x: x[1]) if despesas_por_subcategoria else ('Nenhuma', Decimal('0'))
            
            # Top 3 categorias
            top_receitas = sorted(receitas_por_categoria.items(), key=lambda x: x[1], reverse=True)[:3]
            top_despesas = sorted(despesas_por_categoria.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return {
                'receitas': float(receitas),
                'despesas': float(despesas),
                'saldo': float(receitas - despesas),
                'maior_receita': {'categoria': maior_receita_cat[0], 'valor': float(maior_receita_cat[1])},
                'maior_despesa': {'categoria': maior_despesa_cat[0], 'valor': float(maior_despesa_cat[1])},
                'maior_receita_sub': {'subcategoria': maior_receita_sub[0], 'valor': float(maior_receita_sub[1])},
                'maior_despesa_sub': {'subcategoria': maior_despesa_sub[0], 'valor': float(maior_despesa_sub[1])},
                'top_receitas': [{'categoria': k, 'valor': float(v), 'percentual': float(v/receitas*100) if receitas > 0 else 0} for k, v in top_receitas],
                'top_despesas': [{'categoria': k, 'valor': float(v), 'percentual': float(v/despesas*100) if despesas > 0 else 0} for k, v in top_despesas],
                'qtd_categorias_receitas': len(receitas_por_categoria),
                'qtd_categorias_despesas': len(despesas_por_categoria)
            }
        
        periodo1 = calcular_periodo(data_inicio1, data_fim1)
        periodo2 = calcular_periodo(data_inicio2, data_fim2)
        
        # Calcular variações
        variacao_receitas = ((periodo2['receitas'] - periodo1['receitas']) / periodo1['receitas'] * 100) if periodo1['receitas'] > 0 else 0
        variacao_despesas = ((periodo2['despesas'] - periodo1['despesas']) / periodo1['despesas'] * 100) if periodo1['despesas'] > 0 else 0
        variacao_saldo = ((periodo2['saldo'] - periodo1['saldo']) / abs(periodo1['saldo']) * 100) if periodo1['saldo'] != 0 else 0
        
        return jsonify({
            'periodo1': {
                'datas': {'inicio': data_inicio1.isoformat(), 'fim': data_fim1.isoformat()},
                'dados': periodo1
            },
            'periodo2': {
                'datas': {'inicio': data_inicio2.isoformat(), 'fim': data_fim2.isoformat()},
                'dados': periodo2
            },
            'variacoes': {
                'receitas': round(variacao_receitas, 2),
                'despesas': round(variacao_despesas, 2),
                'saldo': round(variacao_saldo, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/relatorios/indicadores', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_indicadores():
    """Relatório de indicadores financeiros"""
    try:
        lancamentos = db.listar_lancamentos()
        contas = db.listar_contas()
        
        # Obter filtros de data
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
        
        hoje = date.today()
        
        if data_inicio_str and data_fim_str:
            inicio_mes = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            fim_periodo = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        else:
            # Padrão: mês atual
            inicio_mes = date(hoje.year, hoje.month, 1)
            fim_periodo = hoje
        
        # Totais do mês atual
        receitas_mes = Decimal('0')
        despesas_mes = Decimal('0')
        
        # Totais a receber/pagar
        total_receber = Decimal('0')
        total_pagar = Decimal('0')
        
        # Vencidos
        vencidos_receber = Decimal('0')
        vencidos_pagar = Decimal('0')
        
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_pag >= inicio_mes and data_pag <= fim_periodo:
                    valor = Decimal(str(l.valor))
                    if l.tipo == TipoLancamento.RECEITA:
                        receitas_mes += valor
                    else:
                        despesas_mes += valor
            
            if l.status == StatusLancamento.PENDENTE:
                valor = Decimal(str(l.valor))
                data_venc = l.data_vencimento.date() if hasattr(l.data_vencimento, 'date') else l.data_vencimento
                
                if l.tipo == TipoLancamento.RECEITA:
                    total_receber += valor
                    if data_venc < hoje:
                        vencidos_receber += valor
                else:
                    total_pagar += valor
                    if data_venc < hoje:
                        vencidos_pagar += valor
        
        # Saldo em caixa
        saldo_caixa = sum(Decimal(str(c.saldo_inicial)) for c in contas)
        
        # Liquidez = (Saldo + A Receber) / A Pagar
        liquidez = float((saldo_caixa + total_receber) / total_pagar) if total_pagar > 0 else 0
        
        # Margem líquida = (Receitas - Despesas) / Receitas * 100
        margem = float((receitas_mes - despesas_mes) / receitas_mes * 100) if receitas_mes > 0 else 0
        
        return jsonify({
            'saldo_caixa': float(saldo_caixa),
            'mes_atual': {
                'receitas': float(receitas_mes),
                'despesas': float(despesas_mes),
                'saldo': float(receitas_mes - despesas_mes)
            },
            'pendentes': {
                'receber': float(total_receber),
                'pagar': float(total_pagar)
            },
            'vencidos': {
                'receber': float(vencidos_receber),
                'pagar': float(vencidos_pagar)
            },
            'indicadores': {
                'liquidez': round(liquidez, 2),
                'margem_liquida': round(margem, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/relatorios/inadimplencia', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_inadimplencia():
    """Relatório de inadimplência"""
    try:
        lancamentos = db.listar_lancamentos()
        hoje = date.today()
        
        inadimplentes = []
        
        for l in lancamentos:
            # Excluir transferências e considerar apenas PENDENTES
            if l.tipo == TipoLancamento.TRANSFERENCIA:
                continue
                
            if l.status == StatusLancamento.PENDENTE:
                # Converter data_vencimento para date se for datetime
                data_venc = l.data_vencimento.date() if hasattr(l.data_vencimento, 'date') else l.data_vencimento
                
                # Verificar se está vencido (data anterior a hoje)
                if data_venc < hoje:
                    dias_atraso = (hoje - data_venc).days
                    inadimplentes.append({
                        'id': l.id,
                        'tipo': l.tipo.value.upper(),
                        'descricao': l.descricao,
                        'valor': float(l.valor),
                        'data_vencimento': data_venc.isoformat(),
                        'dias_atraso': dias_atraso,
                        'pessoa': l.pessoa or 'Não informado',
                        'categoria': l.categoria or 'Sem categoria'
                    })
        
        # Ordenar por dias de atraso (maior para menor)
        inadimplentes.sort(key=lambda x: x['dias_atraso'], reverse=True)
        
        total_inadimplente = sum(i['valor'] for i in inadimplentes)
        
        return jsonify({
            'inadimplentes': inadimplentes,
            'total': total_inadimplente,
            'quantidade': len(inadimplentes)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    """Retorna o favicon"""
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.svg',
        mimetype='image/svg+xml'
    )


# === EXPORTAÇÃO DE CLIENTES E FORNECEDORES ===

@app.route('/api/clientes/exportar/pdf', methods=['GET'])
@require_permission('clientes_view')
def exportar_clientes_pdf():
    """Exporta clientes para PDF"""
    try:
        from reportlab.lib import colors  # type: ignore
        from reportlab.lib.pagesizes import A4, landscape  # type: ignore
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer  # type: ignore
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
        from reportlab.lib.units import cm  # type: ignore
        from reportlab.pdfgen import canvas  # type: ignore
        from io import BytesIO
        
        clientes = db.listar_clientes()
        
        # Criar PDF em memória
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=0.5*cm, leftMargin=0.5*cm, topMargin=1*cm, bottomMargin=1*cm)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#2c3e50'), spaceAfter=15, alignment=1)
        elements.append(Paragraph(f'LISTA DE CLIENTES - {datetime.now().strftime("%d/%m/%Y")}', title_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Estilo de parágrafo para células
        cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=7, leading=9, wordWrap='CJK')
        
        # Dados da tabela com Paragraph para quebra de linha
        data = [['Razão Social', 'Nome Fantasia', 'CNPJ', 'Cidade', 'Est', 'Telefone', 'Email']]
        
        for cli in clientes:
            # Truncar textos longos e usar Paragraph para quebra automática
            razao = cli.get('razao_social', '-') or '-'
            fantasia = cli.get('nome_fantasia', '-') or '-'
            cnpj = cli.get('cnpj', '-') or '-'
            cidade = cli.get('cidade', '-') or '-'
            estado = cli.get('estado', '-') or '-'
            telefone = cli.get('telefone', '-') or '-'
            email = cli.get('email', '-') or '-'
            
            # Limitar tamanho dos textos muito longos
            if len(razao) > 35:
                razao = razao[:32] + '...'
            if len(fantasia) > 30:
                fantasia = fantasia[:27] + '...'
            if len(cidade) > 20:
                cidade = cidade[:17] + '...'
            if len(email) > 25:
                email = email[:22] + '...'
            
            data.append([
                Paragraph(razao, cell_style),
                Paragraph(fantasia, cell_style),
                Paragraph(cnpj, cell_style),
                Paragraph(cidade, cell_style),
                estado,
                Paragraph(telefone, cell_style),
                Paragraph(email, cell_style)
            ])
        
        # Largura disponível: A4 landscape = 29.7cm, menos margens = ~28.7cm
        # Criar tabela com larguras proporcionais
        table = Table(data, colWidths=[6*cm, 5*cm, 3.5*cm, 4*cm, 1.5*cm, 3.5*cm, 4.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'clientes_{datetime.now().strftime("%Y%m%d")}.pdf')
    
    except Exception as e:
        print(f"Erro ao exportar PDF: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/clientes/exportar/excel', methods=['GET'])
@require_permission('clientes_view')
def exportar_clientes_excel():
    """Exporta clientes para Excel"""
    try:
        import openpyxl  # type: ignore
        from openpyxl.styles import Font, Alignment, PatternFill  # type: ignore
        from openpyxl.worksheet.worksheet import Worksheet  # type: ignore
        from io import BytesIO
        
        clientes = db.listar_clientes()
        
        wb = openpyxl.Workbook()
        ws: Worksheet = wb.active  # type: ignore
        ws.title = "Clientes"
        
        headers = ['Razão Social', 'Nome Fantasia', 'CNPJ', 'IE', 'IM', 'Rua', 'Número', 'Complemento', 'Bairro', 'Cidade', 'Estado', 'CEP', 'Telefone', 'Email']
        ws.append(headers)
        
        header_fill = PatternFill(start_color="34495e", end_color="34495e", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for cli in clientes:
            ws.append([
                cli.get('razao_social', ''), cli.get('nome_fantasia', ''), cli.get('cnpj', ''),
                cli.get('ie', ''), cli.get('im', ''), cli.get('rua', ''), cli.get('numero', ''),
                cli.get('complemento', ''), cli.get('bairro', ''), cli.get('cidade', ''),
                cli.get('estado', ''), cli.get('cep', ''), cli.get('telefone', ''), cli.get('email', '')
            ])
        
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter  # type: ignore
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)
        
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return send_file(buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'clientes_{datetime.now().strftime("%Y%m%d")}.xlsx')
    
    except Exception as e:
        print(f"Erro ao exportar Excel: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/fornecedores/exportar/pdf', methods=['GET'])
@require_permission('fornecedores_view')
def exportar_fornecedores_pdf():
    """Exporta fornecedores para PDF"""
    try:
        from reportlab.lib import colors  # type: ignore
        from reportlab.lib.pagesizes import A4, landscape  # type: ignore
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer  # type: ignore
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
        from reportlab.lib.units import cm  # type: ignore
        from reportlab.pdfgen import canvas  # type: ignore
        from io import BytesIO
        
        fornecedores = db.listar_fornecedores()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=0.5*cm, leftMargin=0.5*cm, topMargin=1*cm, bottomMargin=1*cm)
        
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#2c3e50'), spaceAfter=15, alignment=1)
        elements.append(Paragraph(f'LISTA DE FORNECEDORES - {datetime.now().strftime("%d/%m/%Y")}', title_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Estilo de parágrafo para células
        cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=7, leading=9, wordWrap='CJK')
        
        data = [['Razão Social', 'Nome Fantasia', 'CNPJ', 'Cidade', 'Est', 'Telefone', 'Email']]
        
        for forn in fornecedores:
            razao = forn.get('razao_social', '-') or '-'
            fantasia = forn.get('nome_fantasia', '-') or '-'
            cnpj = forn.get('cnpj', '-') or '-'
            cidade = forn.get('cidade', '-') or '-'
            estado = forn.get('estado', '-') or '-'
            telefone = forn.get('telefone', '-') or '-'
            email = forn.get('email', '-') or '-'
            
            # Limitar tamanho dos textos muito longos
            if len(razao) > 35:
                razao = razao[:32] + '...'
            if len(fantasia) > 30:
                fantasia = fantasia[:27] + '...'
            if len(cidade) > 20:
                cidade = cidade[:17] + '...'
            if len(email) > 25:
                email = email[:22] + '...'
            
            data.append([
                Paragraph(razao, cell_style),
                Paragraph(fantasia, cell_style),
                Paragraph(cnpj, cell_style),
                Paragraph(cidade, cell_style),
                estado,
                Paragraph(telefone, cell_style),
                Paragraph(email, cell_style)
            ])
        
        table = Table(data, colWidths=[6*cm, 5*cm, 3.5*cm, 4*cm, 1.5*cm, 3.5*cm, 4.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'fornecedores_{datetime.now().strftime("%Y%m%d")}.pdf')
    
    except Exception as e:
        print(f"Erro ao exportar PDF: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/fornecedores/exportar/excel', methods=['GET'])
@require_permission('fornecedores_view')
def exportar_fornecedores_excel():
    """Exporta fornecedores para Excel"""
    try:
        import openpyxl  # type: ignore
        from openpyxl.styles import Font, Alignment, PatternFill  # type: ignore
        from openpyxl.worksheet.worksheet import Worksheet  # type: ignore
        from io import BytesIO
        
        fornecedores = db.listar_fornecedores()
        
        wb = openpyxl.Workbook()
        ws: Worksheet = wb.active  # type: ignore
        ws.title = "Fornecedores"
        
        headers = ['Razão Social', 'Nome Fantasia', 'CNPJ', 'IE', 'IM', 'Rua', 'Número', 'Complemento', 'Bairro', 'Cidade', 'Estado', 'CEP', 'Telefone', 'Email']
        ws.append(headers)
        
        header_fill = PatternFill(start_color="34495e", end_color="34495e", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for forn in fornecedores:
            ws.append([
                forn.get('razao_social', ''), forn.get('nome_fantasia', ''), forn.get('cnpj', ''),
                forn.get('ie', ''), forn.get('im', ''), forn.get('rua', ''), forn.get('numero', ''),
                forn.get('complemento', ''), forn.get('bairro', ''), forn.get('cidade', ''),
                forn.get('estado', ''), forn.get('cep', ''), forn.get('telefone', ''), forn.get('email', '')
            ])
        
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter  # type: ignore
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)
        
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return send_file(buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'fornecedores_{datetime.now().strftime("%Y%m%d")}.xlsx')
    
    except Exception as e:
        print(f"Erro ao exportar Excel: {e}")
        return jsonify({'error': str(e)}), 500


# === ROTAS DO MENU OPERACIONAL ===

@app.route('/api/contratos', methods=['GET', 'POST'])
@require_permission('contratos_view')
def contratos():
    """Gerenciar contratos"""
    if request.method == 'GET':
        try:
            contratos = db.listar_contratos()
            
            # Adicionar cliente_id para cada contrato
            for contrato in contratos:
                contrato['cliente_id'] = contrato.get('cliente')
            
            # Aplicar filtro por cliente
            contratos_filtrados = filtrar_por_cliente(contratos, request.usuario)
            
            return jsonify(contratos_filtrados)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # POST
        try:
            data = request.json
            print(f"🔍 Criando contrato com dados: {data}")
            
            # Gerar número automaticamente se não fornecido
            if not data.get('numero'):
                data['numero'] = db.gerar_proximo_numero_contrato()
            
            contrato_id = db.adicionar_contrato(data)
            print(f"✅ Contrato criado com ID: {contrato_id}")
            return jsonify({
                'success': True,
                'message': 'Contrato criado com sucesso',
                'id': contrato_id
            }), 201
        except Exception as e:
            print(f"❌ Erro ao criar contrato: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contratos/proximo-numero', methods=['GET'])
@require_permission('contratos_view')
def proximo_numero_contrato():
    """Retorna o próximo número de contrato disponível"""
    try:
        print("🔍 Gerando próximo número de contrato...")
        numero = db.gerar_proximo_numero_contrato()
        print(f"✅ Número gerado: {numero}")
        return jsonify({'numero': numero})
    except Exception as e:
        print(f"❌ Erro ao gerar número: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/contratos/<int:contrato_id>', methods=['PUT', 'DELETE'])
@require_permission('contratos_edit')
def contrato_detalhes(contrato_id):
    """Atualizar ou excluir contrato"""
    if request.method == 'PUT':
        try:
            data = request.json
            print(f"🔍 Atualizando contrato {contrato_id} com dados: {data}")
            success = db.atualizar_contrato(contrato_id, data)
            if success:
                print(f"✅ Contrato {contrato_id} atualizado")
                return jsonify({'success': True, 'message': 'Contrato atualizado com sucesso'})
            print(f"❌ Contrato {contrato_id} não encontrado")
            return jsonify({'success': False, 'error': 'Contrato não encontrado'}), 404
        except Exception as e:
            print(f"❌ Erro ao atualizar contrato {contrato_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    else:  # DELETE
        try:
            print(f"🔍 Deletando contrato {contrato_id}")
            success = db.deletar_contrato(contrato_id)
            if success:
                print(f"✅ Contrato {contrato_id} deletado")
                return jsonify({'success': True, 'message': 'Contrato excluído com sucesso'})
            print(f"❌ Contrato {contrato_id} não encontrado")
            return jsonify({'success': False, 'error': 'Contrato não encontrado'}), 404
        except Exception as e:
            print(f"❌ Erro ao deletar contrato {contrato_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sessoes', methods=['GET', 'POST'])
@require_permission('sessoes_view')
def sessoes():
    """Gerenciar sessões"""
    if request.method == 'GET':
        try:
            sessoes = db.listar_sessoes()
            
            # Adicionar cliente_id para cada sessão
            for sessao in sessoes:
                sessao['cliente_id'] = sessao.get('cliente')
            
            # Aplicar filtro por cliente
            sessoes_filtradas = filtrar_por_cliente(sessoes, request.usuario)
            
            return jsonify(sessoes_filtradas)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # POST
        try:
            data = request.json
            sessao_id = db.adicionar_sessao(data)
            return jsonify({'success': True, 'message': 'Sessão criada com sucesso', 'id': sessao_id}), 201
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sessoes/<int:sessao_id>', methods=['PUT', 'DELETE'])
@require_permission('sessoes_edit')
def sessao_detalhes(sessao_id):
    """Atualizar ou excluir sessão"""
    if request.method == 'PUT':
        try:
            data = request.json
            success = db.atualizar_sessao(sessao_id, data)
            if success:
                return jsonify({'success': True, 'message': 'Sessão atualizada com sucesso'})
            return jsonify({'success': False, 'error': 'Sessão não encontrada'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    else:  # DELETE
        try:
            success = db.deletar_sessao(sessao_id)
            if success:
                return jsonify({'success': True, 'message': 'Sessão excluída com sucesso'})
            return jsonify({'success': False, 'error': 'Sessão não encontrada'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comissoes', methods=['GET', 'POST'])
@require_permission('operacional_view')
def comissoes():
    """Gerenciar comissões"""
    if request.method == 'GET':
        try:
            comissoes = db.listar_comissoes()
            return jsonify(comissoes)
        except Exception as e:
            print(f"❌ [COMISSÃO GET] Erro: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    else:  # POST
        try:
            data = request.json
            print(f"🔍 [COMISSÃO POST] Dados recebidos: {data}")
            comissao_id = db.adicionar_comissao(data)
            print(f"✅ [COMISSÃO POST] Criada com ID: {comissao_id}")
            return jsonify({'success': True, 'message': 'Comissão criada com sucesso', 'id': comissao_id}), 201
        except Exception as e:
            print(f"❌ [COMISSÃO POST] Erro: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comissoes/<int:comissao_id>', methods=['PUT', 'DELETE'])
@require_permission('operacional_edit')
def comissao_detalhes(comissao_id):
    """Atualizar ou excluir comissão"""
    if request.method == 'PUT':
        try:
            data = request.json
            print(f"🔍 [COMISSÃO PUT] ID: {comissao_id}, Dados: {data}")
            success = db.atualizar_comissao(comissao_id, data)
            if success:
                print(f"✅ [COMISSÃO PUT] Atualizada com sucesso")
                return jsonify({'success': True, 'message': 'Comissão atualizada com sucesso'})
            print(f"⚠️ [COMISSÃO PUT] Não encontrada")
            return jsonify({'success': False, 'error': 'Comissão não encontrada'}), 404
        except Exception as e:
            print(f"❌ [COMISSÃO PUT] Erro: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    else:  # DELETE
        try:
            print(f"🔍 [COMISSÃO DELETE] ID: {comissao_id}")
            success = db.deletar_comissao(comissao_id)
            if success:
                print(f"✅ [COMISSÃO DELETE] Excluída com sucesso")
                return jsonify({'success': True, 'message': 'Comissão excluída com sucesso'})
            print(f"⚠️ [COMISSÃO DELETE] Não encontrada")
            return jsonify({'success': False, 'error': 'Comissão não encontrada'}), 404
        except Exception as e:
            print(f"❌ [COMISSÃO DELETE] Erro: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sessao-equipe', methods=['GET', 'POST', 'DELETE'])
@require_permission('operacional_view')
def sessao_equipe():
    """Gerenciar equipe de sessão"""
    if request.method == 'DELETE':
        # Endpoint temporário para FORÇAR limpeza da tabela
        import sys
        print(f"[CLEANUP] INICIANDO LIMPEZA DA TABELA sessao_equipe", flush=True)
        sys.stdout.flush()
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessao_equipe")
            deleted = cursor.rowcount
            print(f"[CLEANUP] Deletando {deleted} registros...", flush=True)
            sys.stdout.flush()
            conn.commit()
            print(f"[CLEANUP] COMMIT executado!", flush=True)
            sys.stdout.flush()
            cursor.close()
            conn.close()
            print(f"[CLEANUP] Tabela limpa! {deleted} registros removidos", flush=True)
            return jsonify({'success': True, 'deleted': deleted})
        except Exception as e:
            print(f"[CLEANUP ERROR] {e}", flush=True)
            sys.stdout.flush()
            return jsonify({'success': False, 'error': str(e)}), 500
    elif request.method == 'GET':
        try:
            print(f"[BACKEND GET] Chamando listar_sessao_equipe()...")
            lista = db.listar_sessao_equipe()
            print(f"[BACKEND GET] Retornou {len(lista)} membros")
            print(f"[BACKEND GET] Dados: {lista}")
            return jsonify(lista)
        except Exception as e:
            print(f"❌ [EQUIPE GET] Erro: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    else:  # POST
        try:
            data = request.json
            print(f"🔍 [EQUIPE POST] Dados recebidos: {data}")
            se_id = db.adicionar_sessao_equipe(data)
            print(f"✅ [EQUIPE POST] Membro adicionado com ID: {se_id}")
            
            # VERIFICACAO IMEDIATA
            print(f"[EQUIPE POST] Verificando se foi salvo...")
            lista = db.listar_sessao_equipe()
            print(f"[EQUIPE POST] Total na tabela agora: {len(lista)}")
            
            return jsonify({'success': True, 'message': 'Membro adicionado com sucesso', 'id': se_id}), 201
        except Exception as e:
            print(f"❌ [EQUIPE POST] Erro: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sessao-equipe/<int:membro_id>', methods=['PUT', 'DELETE'])
@require_permission('operacional_edit')
def sessao_equipe_detalhes(membro_id):
    """Atualizar ou excluir membro da equipe"""
    if request.method == 'PUT':
        try:
            data = request.json
            print(f"🔍 [EQUIPE PUT] ID: {membro_id}, Dados: {data}")
            success = db.atualizar_sessao_equipe(membro_id, data)
            if success:
                print(f"✅ [EQUIPE PUT] Membro atualizado com sucesso")
                return jsonify({'success': True, 'message': 'Membro atualizado com sucesso'})
            print(f"⚠️ [EQUIPE PUT] Membro não encontrado")
            return jsonify({'success': False, 'error': 'Membro não encontrado'}), 404
        except Exception as e:
            print(f"❌ [EQUIPE PUT] Erro: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    else:  # DELETE
        try:
            print(f"🔍 [EQUIPE DELETE] ID: {membro_id}")
            success = db.deletar_sessao_equipe(membro_id)
            if success:
                print(f"✅ [EQUIPE DELETE] Membro removido com sucesso")
                return jsonify({'success': True, 'message': 'Membro removido com sucesso'})
            print(f"⚠️ [EQUIPE DELETE] Membro não encontrado")
            return jsonify({'success': False, 'error': 'Membro não encontrado'}), 404
        except Exception as e:
            print(f"❌ [EQUIPE DELETE] Erro: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tipos-sessao', methods=['GET', 'POST'])
@require_permission('operacional_view')
def tipos_sessao():
    """Listar ou criar tipos de sessão"""
    if request.method == 'GET':
        try:
            tipos = db.listar_tipos_sessao()
            return jsonify(tipos)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # POST
        try:
            data = request.json
            tipo_id = db.adicionar_tipo_sessao(data)
            return jsonify({'success': True, 'id': tipo_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/tipos-sessao/<int:tipo_id>', methods=['PUT', 'DELETE'])
@require_permission('operacional_edit')
def tipos_sessao_detalhes(tipo_id):
    """Atualizar ou excluir tipo de sessão"""
    if request.method == 'PUT':
        try:
            data = request.json
            success = db.atualizar_tipo_sessao(tipo_id, data)
            if success:
                return jsonify({'success': True, 'message': 'Tipo atualizado com sucesso'})
            return jsonify({'error': 'Tipo não encontrado'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # DELETE
        try:
            success = db.deletar_tipo_sessao(tipo_id)
            if success:
                return jsonify({'success': True, 'message': 'Tipo removido com sucesso'})
            return jsonify({'error': 'Tipo não encontrado'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/agenda', methods=['GET', 'POST'])
@require_permission('agenda_view')
def agenda():
    """Gerenciar agenda"""
    if request.method == 'GET':
        try:
            eventos = db.listar_agenda()
            return jsonify(eventos)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # POST
        try:
            data = request.json
            agenda_id = db.adicionar_agenda(data)
            return jsonify({'message': 'Agendamento criado com sucesso', 'id': agenda_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/agenda/<int:agendamento_id>', methods=['PUT', 'DELETE'])
@require_permission('agenda_edit')
def agenda_detalhes(agendamento_id):
    """Atualizar ou excluir agendamento"""
    if request.method == 'PUT':
        try:
            data = request.json
            success = db.atualizar_agenda(agendamento_id, data)
            if success:
                return jsonify({'message': 'Agendamento atualizado com sucesso'})
            return jsonify({'error': 'Agendamento não encontrado'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # DELETE
        try:
            success = db.deletar_agenda(agendamento_id)
            if success:
                return jsonify({'message': 'Agendamento excluído com sucesso'})
            return jsonify({'error': 'Agendamento não encontrado'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/estoque/produtos', methods=['GET', 'POST'])
@require_permission('estoque_view')
def produtos():
    """Gerenciar produtos do estoque"""
    if request.method == 'GET':
        try:
            produtos = db.listar_produtos()
            return jsonify(produtos)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # POST
        try:
            data = request.json
            produto_id = db.adicionar_produto(data)
            return jsonify({'message': 'Produto criado com sucesso', 'id': produto_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/estoque/produtos/<int:produto_id>', methods=['PUT', 'DELETE'])
@require_permission('estoque_edit')
def produto_detalhes(produto_id):
    """Atualizar ou excluir produto"""
    if request.method == 'PUT':
        try:
            data = request.json
            success = db.atualizar_produto(produto_id, data)
            if success:
                return jsonify({'message': 'Produto atualizado com sucesso'})
            return jsonify({'error': 'Produto não encontrado'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # DELETE
        try:
            success = db.deletar_produto(produto_id)
            if success:
                return jsonify({'message': 'Produto excluído com sucesso'})
            return jsonify({'error': 'Produto não encontrado'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/kits', methods=['GET', 'POST'])
@require_permission('estoque_view')
def kits():
    """Gerenciar kits"""
    if request.method == 'GET':
        try:
            kits = db.listar_kits()
            return jsonify(kits)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # POST
        try:
            data = request.json
            kit_id = db.adicionar_kit(data)
            return jsonify({'message': 'Kit criado com sucesso', 'id': kit_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/kits/<int:kit_id>', methods=['PUT', 'DELETE'])
@require_permission('estoque_edit')
def kit_detalhes(kit_id):
    """Atualizar ou excluir kit"""
    if request.method == 'PUT':
        try:
            data = request.json
            success = db.atualizar_kit(kit_id, data)
            if success:
                return jsonify({'message': 'Kit atualizado com sucesso'})
            return jsonify({'error': 'Kit não encontrado'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # DELETE
        try:
            success = db.deletar_kit(kit_id)
            if success:
                return jsonify({'message': 'Kit excluído com sucesso'})
            return jsonify({'error': 'Kit não encontrado'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/tags', methods=['GET', 'POST'])
@require_permission('operacional_view')
def tags():
    """Gerenciar tags"""
    if request.method == 'GET':
        try:
            tags = db.listar_tags()
            return jsonify(tags)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # POST
        try:
            data = request.json
            tag_id = db.adicionar_tag(data)
            return jsonify({'message': 'Tag criada com sucesso', 'id': tag_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/tags/<int:tag_id>', methods=['PUT', 'DELETE'])
@require_permission('operacional_edit')
def tag_detalhes(tag_id):
    """Atualizar ou excluir tag"""
    if request.method == 'PUT':
        try:
            data = request.json
            success = db.atualizar_tag(tag_id, data)
            if success:
                return jsonify({'message': 'Tag atualizada com sucesso'})
            return jsonify({'error': 'Tag não encontrada'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # DELETE
        try:
            success = db.deletar_tag(tag_id)
            if success:
                return jsonify({'message': 'Tag excluída com sucesso'})
            return jsonify({'error': 'Tag não encontrada'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/templates-equipe', methods=['GET', 'POST'])
@require_permission('operacional_view')
def templates_equipe():
    """Gerenciar templates de equipe"""
    if request.method == 'GET':
        try:
            templates = db.listar_templates_equipe()
            return jsonify(templates)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # POST
        try:
            data = request.json
            template_id = db.adicionar_template_equipe(data)
            return jsonify({'message': 'Template criado com sucesso', 'id': template_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/templates-equipe/<int:template_id>', methods=['PUT', 'DELETE'])
@require_permission('operacional_edit')
def template_equipe_detalhes(template_id):
    """Atualizar ou excluir template"""
    if request.method == 'PUT':
        try:
            data = request.json
            success = db.atualizar_template_equipe(template_id, data)
            if success:
                return jsonify({'message': 'Template atualizado com sucesso'})
            return jsonify({'error': 'Template não encontrado'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # DELETE
        try:
            success = db.deletar_template_equipe(template_id)
            if success:
                return jsonify({'message': 'Template excluído com sucesso'})
            return jsonify({'error': 'Template não encontrado'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# ============================================================================
# EXPORTAÇÃO DE DADOS POR CLIENTE (ADMIN)
# ============================================================================

@app.route('/api/admin/debug/schema', methods=['GET'])
@require_admin
def debug_database_schema():
    """
    Mostra todas as tabelas e colunas do banco de dados (DEBUG)
    """
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        schema_info = {}
        
        # Buscar todas as tabelas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tabelas = cursor.fetchall()
        
        # Para cada tabela, buscar colunas
        for tabela_row in tabelas:
            tabela = tabela_row['table_name']
            
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position
            """, (tabela,))
            
            colunas = cursor.fetchall()
            
            schema_info[tabela] = [
                {
                    'nome': col['column_name'],
                    'tipo': col['data_type'],
                    'nullable': col['is_nullable'] == 'YES',
                    'default': col['column_default']
                }
                for col in colunas
            ]
        
        cursor.close()
        database.return_to_pool(conn)
        
        # Imprimir no console também
        print("\n" + "=" * 80)
        print("📊 SCHEMA DO BANCO DE DADOS - TODAS AS TABELAS E COLUNAS")
        print("=" * 80)
        
        for tabela, colunas in sorted(schema_info.items()):
            print(f"\n📋 Tabela: {tabela.upper()}")
            print("-" * 80)
            for col in colunas:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"  • {col['nome']:<30} {col['tipo']:<20} {nullable}")
        
        print("\n" + "=" * 80)
        
        return jsonify({
            'success': True,
            'schema': schema_info,
            'total_tabelas': len(schema_info)
        })
        
    except Exception as e:
        print(f"❌ Erro ao obter schema: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/exportar-cliente/<int:cliente_id>', methods=['GET'])
@require_admin
def exportar_dados_cliente_admin(cliente_id):
    """
    Exporta todos os dados de um cliente específico (apenas admin)
    
    Retorna um arquivo JSON com todos os dados do cliente:
    - Clientes
    - Fornecedores
    - Categorias
    - Contas Bancárias
    - Lançamentos
    """
    try:
        # Verificar se o usuário/cliente existe
        usuario = request.usuario
        usuario_cliente = auth_db.obter_usuario(cliente_id)
        
        if not usuario_cliente:
            return jsonify({
                'success': False,
                'error': f'Usuário com ID {cliente_id} não encontrado'
            }), 404
        
        # Exportar dados
        print(f"\n🔄 Iniciando exportação dos dados do cliente {cliente_id}")
        print(f"   📋 Usuário: {usuario_cliente.get('nome_completo', 'N/A')} ({usuario_cliente.get('email', 'N/A')})")
        export_data = database.exportar_dados_cliente(cliente_id)
        
        # Registrar log de auditoria
        auth_db.registrar_log_acesso(
            usuario_id=usuario['id'],
            acao='exportar_dados_cliente',
            descricao=f'Exportou dados do cliente_id {cliente_id}',
            ip_address=request.remote_addr,
            sucesso=True
        )
        
        print(f"✅ Exportação concluída para cliente {cliente_id}")
        
        # Retornar como arquivo TXT para download
        from flask import make_response
        response = make_response(export_data['texto'])
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=export_cliente_{cliente_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        return response
        
    except Exception as e:
        print(f"❌ Erro ao exportar dados do cliente {cliente_id}: {e}")
        import traceback
        traceback.print_exc()
        
        # Registrar log de erro
        try:
            auth_db.registrar_log_acesso(
                usuario_id=request.usuario['id'],
                acao='exportar_dados_cliente',
                descricao=f'ERRO ao exportar cliente_id {cliente_id}: {str(e)}',
                ip_address=request.remote_addr,
                sucesso=False
            )
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': f'Erro ao exportar dados: {str(e)}'
        }), 500


@app.route('/api/admin/listar-proprietarios', methods=['GET'])
@require_admin
def listar_proprietarios_disponiveis():
    """
    Lista todos os proprietario_id únicos no sistema
    Para o admin selecionar qual cliente exportar
    """
    try:
        # Buscar todos os usuários do tipo 'cliente'
        usuarios = auth_db.listar_usuarios()
        
        proprietarios_info = []
        proprietarios_ids = set()
        
        for usuario in usuarios:
            # Adicionar todos os usuários com tipo 'cliente' ou que tenham cliente_id
            if usuario.get('tipo') == 'cliente' or usuario.get('cliente_id'):
                proprietario_id = usuario.get('cliente_id') or usuario.get('id')
                
                # Evitar duplicatas
                if proprietario_id in proprietarios_ids:
                    continue
                proprietarios_ids.add(proprietario_id)
                
                proprietarios_info.append({
                    'proprietario_id': proprietario_id,
                    'nome': usuario.get('nome_completo') or usuario.get('nome') or f'Usuário {proprietario_id}',
                    'email': usuario.get('email') or 'Sem email',
                    'tipo': usuario.get('tipo', 'cliente'),
                    'usuario_id': usuario.get('id')
                })
        
        # Também buscar proprietario_id únicos das tabelas (para dados órfãos)
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Buscar proprietario_id que não correspondem a usuários
        cursor.execute("""
            SELECT DISTINCT proprietario_id 
            FROM (
                SELECT proprietario_id FROM clientes WHERE proprietario_id IS NOT NULL
                UNION
                SELECT proprietario_id FROM fornecedores WHERE proprietario_id IS NOT NULL
                UNION
                SELECT proprietario_id FROM lancamentos WHERE proprietario_id IS NOT NULL
                UNION
                SELECT proprietario_id FROM contas_bancarias WHERE proprietario_id IS NOT NULL
                UNION
                SELECT proprietario_id FROM categorias WHERE proprietario_id IS NOT NULL
            ) AS todos_proprietarios
            ORDER BY proprietario_id
        """)
        
        proprietarios_db = cursor.fetchall()
        cursor.close()
        database.return_to_pool(conn)
        
        # Adicionar proprietários órfãos (que existem nas tabelas mas não têm usuário)
        for row in proprietarios_db:
            prop_id = row['proprietario_id']
            if prop_id not in proprietarios_ids:
                proprietarios_ids.add(prop_id)
                proprietarios_info.append({
                    'proprietario_id': prop_id,
                    'nome': f'Cliente ID {prop_id} (sem usuário)',
                    'email': 'Não disponível',
                    'tipo': 'orfao'
                })
        
        # Ordenar por nome
        proprietarios_info.sort(key=lambda x: x['nome'])
        
        print(f"✅ Encontrados {len(proprietarios_info)} proprietários únicos")
        
        return jsonify({
            'success': True,
            'proprietarios': proprietarios_info,
            'total': len(proprietarios_info)
        })
        
    except Exception as e:
        print(f"❌ Erro ao listar proprietários: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'Erro ao listar proprietários: {str(e)}'
        }), 500


# ==================== ROTAS DE PREFERÊNCIAS DO USUÁRIO ====================

@app.route('/api/preferencias/menu-order', methods=['GET'])
@require_auth
def obter_ordem_menu():
    """Obtém a ordem personalizada do menu do usuário"""
    try:
        # Usar session ao invés de request.usuario
        usuario_id = session.get('usuario_id')
        
        if not usuario_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado'
            }), 401
        
        print(f"📥 Obtendo ordem do menu para usuario_id={usuario_id}")
        
        # Ordem padrão
        ordem_padrao = '["dashboard","financeiro","relatorios","cadastros","operacional"]'
        
        # Obter preferência do banco
        try:
            ordem = database.obter_preferencia_usuario(
                usuario_id, 
                'menu_order', 
                ordem_padrao
            )
        except Exception as db_error:
            print(f"⚠️ Erro ao buscar preferência, usando padrão: {db_error}")
            ordem = ordem_padrao
        
        # Parsear JSON
        import json
        menu_order = json.loads(ordem) if ordem else json.loads(ordem_padrao)
        
        return jsonify({
            'success': True,
            'menu_order': menu_order
        })
        
    except Exception as e:
        print(f"❌ Erro ao obter ordem do menu: {e}")
        import traceback
        traceback.print_exc()
        # Retornar ordem padrão em caso de erro
        return jsonify({
            'success': True,
            'menu_order': ["dashboard","financeiro","relatorios","cadastros","operacional"]
        })


@app.route('/api/preferencias/menu-order', methods=['POST'])
@require_auth
def salvar_ordem_menu():
    """Salva a ordem personalizada do menu do usuário"""
    try:
        # Usar session ao invés de request.usuario
        usuario_id = session.get('usuario_id')
        
        if not usuario_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado'
            }), 401
        
        print(f"💾 Salvando ordem do menu para usuario_id={usuario_id}")
        
        data = request.json
        if not data:
            print("❌ Dados não fornecidos")
            return jsonify({
                'success': False,
                'error': 'Dados não fornecidos'
            }), 400
        
        menu_order = data.get('menu_order', [])
        print(f"📋 Ordem recebida: {menu_order}")
        
        # Validar formato
        if not isinstance(menu_order, list):
            print("❌ menu_order não é lista")
            return jsonify({
                'success': False,
                'error': 'menu_order deve ser uma lista'
            }), 400
        
        # Validar itens permitidos
        itens_validos = ['dashboard', 'financeiro', 'relatorios', 'cadastros', 'operacional']
        for item in menu_order:
            if item not in itens_validos:
                print(f"❌ Item inválido: {item}")
                return jsonify({
                    'success': False,
                    'error': f'Item inválido: {item}'
                }), 400
        
        # Converter para JSON string
        import json
        menu_order_json = json.dumps(menu_order)
        
        # Salvar no banco
        print(f"💾 Chamando salvar_preferencia_usuario...")
        sucesso = database.salvar_preferencia_usuario(
            usuario_id,
            'menu_order',
            menu_order_json
        )
        
        print(f"{'✅' if sucesso else '❌'} Resultado do save: {sucesso}")
        
        if sucesso:
            # Registrar log
            try:
                auth_db.registrar_log_acesso(
                    usuario_id=usuario_id,
                    acao='update_menu_order',
                    descricao=f'Ordem do menu atualizada: {menu_order}',
                    ip_address=request.remote_addr,
                    sucesso=True
                )
            except Exception as log_error:
                print(f"⚠️ Erro ao registrar log (não crítico): {log_error}")
            
            return jsonify({
                'success': True,
                'message': 'Ordem do menu salva com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao salvar no banco de dados'
            }), 500
        
    except Exception as e:
        print(f"❌ Erro ao salvar ordem do menu: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ROTAS DE GESTÃO DE EMPRESAS (MULTI-TENANT)
# ============================================================================
logger.info("="*80)
logger.info("INICIO DAS ROTAS DE EMPRESAS")
logger.info("="*80)

@app.route('/api/empresas', methods=['GET'])
@require_auth
def listar_empresas_api():
    """Lista todas as empresas (apenas super admin)"""
    logger.info("\n" + "="*80)
    logger.info("[listar_empresas_api] FUNCAO INICIADA")
    logger.info(f"   Path: {request.path}")
    logger.info(f"   Metodo: {request.method}")
    logger.info("="*80)
    
    try:
        logger.info("GET /api/empresas - Iniciando processamento...")
        
        # Usa get_usuario_logado() para pegar usuario do token
        usuario = get_usuario_logado()
        logger.info(f"   Usuario autenticado: {usuario.get('username')} (tipo: {usuario.get('tipo')})")
        
        # Apenas admin do sistema pode listar todas empresas
        if usuario['tipo'] != 'admin':
            logger.info(f"   Acesso negado - usuario nao e admin")
            return jsonify({'error': 'Acesso negado'}), 403
        
        filtros = {}
        if request.args.get('ativo'):
            filtros['ativo'] = request.args.get('ativo') == 'true'
        
        if request.args.get('plano'):
            filtros['plano'] = request.args.get('plano')
        
        logger.info(f"   🔍 Chamando database.listar_empresas(filtros={filtros})...")
        empresas = database.listar_empresas(filtros)
        logger.info(f"   ✅ Empresas carregadas: {len(empresas) if empresas else 0}")
        
        # Garantir que empresas não seja None
        if empresas is None:
            empresas = []
        
        # Retornar apenas dados básicos (sem estatísticas para evitar sobrecarga)
        # As estatísticas podem ser buscadas individualmente se necessário
        
        logger.info(f"   ✅ Retornando {len(empresas)} empresas")
        logger.info("="*80 + "\n")
        
        return jsonify(empresas)
        
    except Exception as e:
        logger.info(f"❌ Erro ao listar empresas: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        logger.info("="*80 + "\n")
        return jsonify({'error': str(e)}), 500

@app.route('/api/empresas/<int:empresa_id>', methods=['GET'])
@require_auth
def obter_empresa_api(empresa_id):
    """Obtém dados de uma empresa específica"""
    logger.info("\n" + "="*80)
    logger.info(f"[obter_empresa_api] FUNCAO CHAMADA - ID: {empresa_id}")
    try:
        logger.info(f"[obter_empresa_api] Obtendo usuario logado...")
        usuario = get_usuario_logado()
        logger.info(f"[obter_empresa_api] Usuario: {usuario.get('username')} (tipo: {usuario.get('tipo')})")
        
        # Admin pode ver qualquer empresa, usuário comum só a própria
        if usuario['tipo'] != 'admin':
            logger.info(f"[obter_empresa_api] Usuario nao e admin - verificando empresa_id...")
            usuario_completo = database.obter_usuario_por_id(usuario['id'])
            if usuario_completo.get('empresa_id') != empresa_id:
                logger.info(f"[obter_empresa_api] Acesso negado - empresa diferente")
                return jsonify({'error': 'Acesso negado'}), 403
        
        logger.info(f"[obter_empresa_api] Chamando database.obter_empresa({empresa_id})...")
        empresa = database.obter_empresa(empresa_id)
        logger.info(f"[obter_empresa_api] Resultado: {empresa is not None}")
        
        if not empresa:
            logger.info(f"[obter_empresa_api] Empresa nao encontrada")
            logger.info("="*80 + "\n")
            return jsonify({'error': 'Empresa não encontrada'}), 404
        
        logger.info(f"[obter_empresa_api] Empresa encontrada: {empresa.get('razao_social')}")
        logger.info(f"[obter_empresa_api] Obtendo estatisticas...")
        
        # Adicionar estatísticas
        try:
            empresa['stats'] = database.obter_estatisticas_empresa(empresa_id)
            logger.info(f"[obter_empresa_api] Estatisticas obtidas")
        except Exception as e:
            logger.info(f"[obter_empresa_api] Erro ao obter stats: {e}")
            empresa['stats'] = {}
        
        logger.info(f"[obter_empresa_api] Retornando sucesso")
        logger.info("="*80 + "\n")
        return jsonify({
            'success': True,
            'empresa': empresa
        })
        
    except Exception as e:
        logger.info(f"[obter_empresa_api] EXCECAO: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        logger.info("="*80 + "\n")
        return jsonify({'error': str(e)}), 500


@app.route('/api/empresas', methods=['POST'])
@require_auth
def criar_empresa_api():
    """Cria uma nova empresa (apenas super admin)"""
    logger.info("\n" + "="*80)
    logger.info("[criar_empresa_api] FUNCAO CHAMADA")
    try:
        usuario = get_usuario_logado()
        logger.info(f"   Usuario: {usuario.get('username')} (tipo: {usuario.get('tipo')})")
        
        if usuario['tipo'] != 'admin':
            logger.info("   Acesso negado - usuario nao e admin")
            return jsonify({'error': 'Acesso negado'}), 403
        
        dados = request.json
        logger.info(f"   Dados recebidos: {dados}")
        
        if not dados:
            logger.info("   Erro: dados nao fornecidos")
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        logger.info("   Chamando database.criar_empresa()...")
        resultado = database.criar_empresa(dados)
        logger.info(f"   Resultado: {resultado}")
        
        if resultado['success']:
            # Registrar log
            try:
                auth_db.registrar_log_acesso(
                    usuario_id=usuario['id'],
                    acao='criar_empresa',
                    descricao=f"Empresa criada: {dados.get('razao_social')}",
                    sucesso=True
                )
            except:
                pass
            
            logger.info("   Empresa criada com sucesso!")
            logger.info("="*80 + "\n")
            return jsonify(resultado), 201
        else:
            logger.info(f"   Erro: {resultado.get('error')}")
            logger.info("="*80 + "\n")
            return jsonify(resultado), 400
        
    except Exception as e:
        logger.info(f"EXCECAO ao criar empresa: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        logger.info("="*80 + "\n")
        return jsonify({'error': str(e)}), 500


@app.route('/api/empresas/<int:empresa_id>', methods=['PUT'])
@require_auth
def atualizar_empresa_api(empresa_id):
    """Atualiza dados de uma empresa"""
    print(f"\n✏️ [atualizar_empresa_api] FUNÇÃO CHAMADA - ID: {empresa_id}")
    try:
        usuario = get_usuario_logado()
        
        # Admin pode editar qualquer empresa
        # Usuário comum não pode editar
        if usuario['tipo'] != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        dados = request.json
        
        if not dados:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        resultado = database.atualizar_empresa(empresa_id, dados)
        
        if resultado['success']:
            # Registrar log
            try:
                auth_db.registrar_log_acesso(
                    usuario_id=usuario['id'],
                    acao='atualizar_empresa',
                    descricao=f"Empresa {empresa_id} atualizada",
                    sucesso=True
                )
            except:
                pass
            
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400
        
    except Exception as e:
        print(f"❌ Erro ao atualizar empresa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/empresas/<int:empresa_id>/suspender', methods=['POST'])
@require_auth
def suspender_empresa_api(empresa_id):
    """Suspende uma empresa"""
    print(f"\n⏸️ [suspender_empresa_api] FUNÇÃO CHAMADA - ID: {empresa_id}")
    try:
        usuario = get_usuario_logado()
        
        if usuario['tipo'] != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        dados = request.json
        motivo = dados.get('motivo', 'Não especificado')
        
        resultado = database.suspender_empresa(empresa_id, motivo)
        
        if resultado['success']:
            # Registrar log
            try:
                auth_db.registrar_log_acesso(
                    usuario_id=usuario['id'],
                    acao='suspender_empresa',
                    descricao=f"Empresa {empresa_id} suspensa: {motivo}",
                    sucesso=True
                )
            except:
                pass
            
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400
        
    except Exception as e:
        print(f"❌ Erro ao suspender empresa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/empresas/<int:empresa_id>/reativar', methods=['POST'])
@require_auth
def reativar_empresa_api(empresa_id):
    """Reativa uma empresa suspensa"""
    print(f"\n▶️ [reativar_empresa_api] FUNÇÃO CHAMADA - ID: {empresa_id}")
    try:
        usuario = get_usuario_logado()
        
        if usuario['tipo'] != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        resultado = database.reativar_empresa(empresa_id)
        
        if resultado['success']:
            # Registrar log
            try:
                auth_db.registrar_log_acesso(
                    usuario_id=usuario['id'],
                    acao='reativar_empresa',
                    descricao=f"Empresa {empresa_id} reativada",
                    sucesso=True
                )
            except:
                pass
            
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400
        
    except Exception as e:
        print(f"❌ Erro ao reativar empresa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/empresas/<int:empresa_id>', methods=['DELETE'])
@require_auth
def deletar_empresa_api(empresa_id):
    """Deleta uma empresa (apenas admin e se não tiver usuários vinculados)"""
    print(f"\n❌ [deletar_empresa_api] FUNÇÃO CHAMADA - ID: {empresa_id}")
    try:
        usuario = get_usuario_logado()
        
        if usuario['tipo'] != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Verificar se tem usuários vinculados
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE empresa_id = %s", (empresa_id,))
            result = cursor.fetchone()
            cursor.close()
        
        if result and result['count'] > 0:
            return jsonify({
                'success': False,
                'error': f'Não é possível excluir. Existem {result["count"]} usuário(s) vinculado(s) a esta empresa.'
            }), 400
        
        # Excluir empresa
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM empresas WHERE id = %s", (empresa_id,))
            conn.commit()
            cursor.close()
        
        # Registrar log
        try:
            auth_db.registrar_log_acesso(
                usuario_id=usuario['id'],
                acao='deletar_empresa',
                descricao=f"Empresa {empresa_id} deletada",
                sucesso=True
            )
        except:
            pass
        
        return jsonify({'success': True, 'message': 'Empresa deletada com sucesso'})
        
    except Exception as e:
        print(f"❌ Erro ao deletar empresa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/empresas/<int:empresa_id>/stats', methods=['GET'])
@require_auth
def estatisticas_empresa_api(empresa_id):
    """Obtém estatísticas de uma empresa"""
    print(f"\n📊 [estatisticas_empresa_api] FUNÇÃO CHAMADA - ID: {empresa_id}")
    try:
        usuario = auth_db.obter_usuario(session.get('usuario_id'))
        
        # Verificar acesso
        if usuario['tipo'] != 'admin':
            usuario_completo = database.obter_usuario_por_id(usuario['id'])
            if usuario_completo.get('empresa_id') != empresa_id:
                return jsonify({'error': 'Acesso negado'}), 403
        
        stats = database.obter_estatisticas_empresa(empresa_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# LISTAR ROTAS (NIVEL DE MODULO - EXECUTA SEMPRE)
# ============================================================================
logger.info("="*80)
logger.info("ROTAS REGISTRADAS:")
logger.info("="*80)
for rule in app.url_map.iter_rules():
    if 'api' in rule.rule and 'static' not in rule.rule:
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        logger.info(f"  {rule.rule:<45} [{methods}]")
logger.info("="*80)


# ============================================================================
# MONITORAMENTO DO POOL DE CONEXÕES
# ============================================================================

@app.route('/api/health/pool', methods=['GET'])
def pool_status():
    """Endpoint para monitorar status do pool de conexões"""
    try:
        pool_obj = database._get_connection_pool()
        # Tentar obter informações do pool
        return jsonify({
            'status': 'healthy',
            'pool_type': 'ThreadedConnectionPool',
            'note': 'Pool configurado para 5-50 conexões'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Ativar logging do Flask/Werkzeug
    import logging
    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)
    
    # Porta configurável (Railway usa variável de ambiente PORT)
    port = int(os.getenv('PORT', 5000))
    
    print("="*60)
    print("Sistema Financeiro - Versão Web")
    print("="*60)
    print(f"Servidor iniciado em: http://0.0.0.0:{port}")
    print(f"Banco de dados: {os.getenv('DATABASE_TYPE', 'sqlite')}")
    
    # Listar TODAS as rotas registradas
    print("\n🔍 TODAS as rotas registradas:")
    total_rotas = 0
    for rule in app.url_map.iter_rules():
        print(f"   • {rule.rule} - Métodos: {', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))}")
        total_rotas += 1
    print(f"\n📊 Total de rotas: {total_rotas}")
    
    print("\n🔍 Rotas de /api/empresas especificamente:")
    empresas_rotas = 0
    for rule in app.url_map.iter_rules():
        if 'empresas' in rule.rule:
            print(f"   ✅ {rule.rule} - Métodos: {', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))}")
            empresas_rotas += 1
    if empresas_rotas == 0:
        print("   ❌ NENHUMA ROTA DE EMPRESAS ENCONTRADA!")
        print("   ⚠️  Possível erro na definição das rotas de empresas")
    else:
        print(f"   ✅ {empresas_rotas} rotas de empresas encontradas")
    
    print("="*60)
    
    logger.info("="*80)
    logger.info("FIM DO ARQUIVO WEB_SERVER.PY - TODAS AS ROTAS CARREGADAS")
    logger.info("="*80)
    
    # Habilitar debug do Flask
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)


