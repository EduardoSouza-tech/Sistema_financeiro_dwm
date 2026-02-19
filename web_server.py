"""
Servidor Web para o Sistema Financeiro
Otimizado para PostgreSQL com pool de conexões

Deploy: 2026-02-15 16:40 - Fix campos associacao e numero_documento no GET
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
# FORÇA REIMPORT DO MÓDULO database_postgresql
# Remove do cache para garantir que métodos novos sejam carregados
if 'database_postgresql' in sys.modules:
    print("🔄 Forçando reimport de database_postgresql...")
    del sys.modules['database_postgresql']
    
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
import psycopg2
import psycopg2.extras

# ============================================================================
# VALIDAÇÃO DE DOCUMENTOS
# ============================================================================
# IMPORTS COMENTADOS - movidos para dentro das funções específicas
# from cpf_validator import CPFValidator
# from cpf_corrector import CPFCorrector

# ============================================================================
# UTILITÁRIOS COMPARTILHADOS (FASE 4)
# ============================================================================
from app.utils import (
    parse_date,
    format_date_br,
    format_date_iso,
    get_current_date_br,
    get_current_date_filename,
    format_currency,
    parse_currency
)

app = Flask(__name__, static_folder='static', template_folder='templates')

# ============================================================================
# AUTO-EXECUTAR MIGRATION DE EVENTOS (STARTUP)
# ============================================================================
def auto_execute_migrations():
    """Executa migrations automaticamente no startup"""
    try:
        logger.info("="*80)
        logger.info("🚀 AUTO-EXECUTANDO MIGRATIONS DE EVENTOS")
        logger.info("="*80)
        
        # Verificar se tabelas já existem
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('funcoes_evento', 'evento_funcionarios')
        """)
        
        count = cursor.fetchone()[0]
        
        if count == 2:
            logger.info("✅ Tabelas já existem. Verificando colunas adicionais...")
            
            # Adicionar colunas de horário se não existirem
            try:
                cursor.execute("""
                    ALTER TABLE evento_funcionarios 
                    ADD COLUMN IF NOT EXISTS hora_inicio TIME
                """)
                conn.commit()
                logger.info("✅ Coluna hora_inicio adicionada/verificada em evento_funcionarios")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao adicionar coluna hora_inicio: {e}")
                conn.rollback()
            
            try:
                cursor.execute("""
                    ALTER TABLE evento_funcionarios 
                    ADD COLUMN IF NOT EXISTS hora_fim TIME
                """)
                conn.commit()
                logger.info("✅ Coluna hora_fim adicionada/verificada em evento_funcionarios")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao adicionar coluna hora_fim: {e}")
                conn.rollback()
            
            cursor.close()
            return
        
        logger.info(f"⚠️ Encontradas {count}/2 tabelas. Executando migration...")
        
        # Ler e executar SQL
        sql_file = os.path.join(os.path.dirname(__file__), 'migration_evento_funcionarios.sql')
        
        if not os.path.exists(sql_file):
            logger.error(f"❌ Arquivo SQL não encontrado: {sql_file}")
            return
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        logger.info("📝 Executando SQL...")
        cursor.execute(sql_content)
        conn.commit()
        logger.info("✅ SQL executado e commitado")
        
        # Verificar criação
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('funcoes_evento', 'evento_funcionarios')
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        logger.info(f"✅ {len(tables)} TABELAS CRIADAS")
        
        # Contar funções
        cursor.execute("SELECT COUNT(*) as total FROM funcoes_evento")
        result = cursor.fetchone()
        count_funcoes = result['total'] if isinstance(result, dict) else result[0]
        logger.info(f"✅ {count_funcoes} FUNÇÕES INSERIDAS")
        
        # Adicionar colunas de horário se não existirem
        try:
            cursor.execute("""
                ALTER TABLE evento_funcionarios 
                ADD COLUMN IF NOT EXISTS hora_inicio TIME
            """)
            conn.commit()
            logger.info("✅ Coluna hora_inicio adicionada/verificada em evento_funcionarios")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao adicionar coluna hora_inicio: {e}")
            conn.rollback()
        
        try:
            cursor.execute("""
                ALTER TABLE evento_funcionarios 
                ADD COLUMN IF NOT EXISTS hora_fim TIME
            """)
            conn.commit()
            logger.info("✅ Coluna hora_fim adicionada/verificada em evento_funcionarios")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao adicionar coluna hora_fim: {e}")
            conn.rollback()
        
        cursor.close()
        
        logger.info("="*80)
        logger.info("✅ MIGRATION CONCLUÍDA!")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ Erro na auto-migration: {e}")
        import traceback
        traceback.print_exc()

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
# AUTO-RENOVAÇÃO DE SESSÃO (KEEP-ALIVE)
# ============================================================================
@app.before_request
def renovar_sessao():
    """
    Renova a sessão automaticamente a cada requisição para evitar timeout
    durante uso ativo do sistema. A sessão é marcada como modificada para
    forçar o Flask a atualizar o cookie de sessão.
    
    IMPORTANTE: Verifica 'session_token' que é a chave usada pelo sistema
    de autenticação (não 'user_id' nem 'usuario_id').
    """
    # Verificar se há token de sessão ativo (chave correta do sistema)
    if 'session_token' in session:
        session.modified = True  # Força renovação do cookie de sessão
        # O Flask automaticamente atualiza o timestamp da sessão
        logger.debug(f"♻️ [SESSÃO] Renovada automaticamente para token: {session.get('session_token', '')[:20]}...")

# ============================================================================
# INICIALIZAR CSRF PROTECTION
# ============================================================================
csrf_instance = init_csrf(app)
register_csrf_error_handlers(app)

# NOTA: Isenções CSRF são aplicadas via decorador @csrf_instance.exempt
# diretamente nas view functions (não na lista de rotas)
# Ver exemplos: /api/auth/login, /api/admin/import/upload

# Injetar CSRF token em todos os templates
@app.context_processor
def inject_csrf():
    return inject_csrf_token()

logger.info("✅ CSRF Protection configurado")

# ============================================================================
# REGISTRAR BLUEPRINTS (ARQUITETURA MODULAR)
# ============================================================================
from app.routes import register_blueprints
register_blueprints(app)
logger.info("✅ Blueprints registrados")

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

@app.before_request
def log_request_info():
    """Log de todas as requisições para debug - DESABILITADO para reduzir poluição"""
    # Logs comentados - descomentar apenas para debug profundo
    # if request.path.startswith('/api/'):
    #     print(f"\n{'🔵'*40}")
    #     print(f"📥 REQUISIÇÃO: {request.method} {request.path}")
    #     print(f"   Session token: {'Presente' if session.get('session_token') else 'AUSENTE'}")
    #     print(f"   Cookies: {list(request.cookies.keys())}")
    #     print(f"   Headers Authorization: {request.headers.get('Authorization', 'Não presente')}")
    #     print(f"   CSRF Token no header: {request.headers.get('X-CSRFToken', 'AUSENTE')}")
        
    # Gerar CSRF token automaticamente se não existir na sessão
    from flask_wtf.csrf import generate_csrf
    if '_csrf_token' not in session and request.path.startswith('/api/'):
        generate_csrf()
        # print(f"   🔑 CSRF Token gerado automaticamente: {token[:20]}...")
    # else:
    #     print(f"   🔑 CSRF Token já existe na sessão")
    # print(f"{'🔵'*40}")

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
    
    # Executar migrações necessárias
    try:
        print("\n👥 Executando migração Usuário Multi-Empresa...")
        from migration_usuario_multi_empresa import executar_migracao as migrar_usuario_multi_empresa
        if migrar_usuario_multi_empresa(db):
            print("✅ Sistema Usuário Multi-Empresa configurado com sucesso!\n")
        else:
            print("⚠️ Migração Usuário Multi-Empresa falhou (pode já estar aplicada)\n")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível executar migração usuário multi-empresa: {e}")
    
    try:
        print("\n💰 Executando migração Tipo Saldo Inicial...")
        from migration_tipo_saldo_inicial import executar_migracao as migrar_tipo_saldo
        if migrar_tipo_saldo(db):
            print("✅ Coluna tipo_saldo_inicial adicionada com sucesso!\n")
        else:
            print("⚠️ Migração tipo_saldo_inicial falhou (pode já estar aplicada)\n")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível executar migração tipo_saldo_inicial: {e}")
    
    # 🚀 AUTO-EXECUTAR MIGRATIONS DE EVENTOS (após db estar pronto)
    try:
        print("\n🎉 Executando migração de Eventos...")
        auto_execute_migrations()
        print("✅ Migration de eventos verificada!\n")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível executar auto-migration de eventos: {e}")
    
    try:
        print("\n📅 Executando migração Data de Início...")
        from migration_data_inicio import executar_migracao as migrar_data_inicio
        if migrar_data_inicio(db):
            print("✅ Coluna data_inicio adicionada com sucesso!\n")
        else:
            print("⚠️ Migração data_inicio falhou (pode já estar aplicada)\n")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível executar migração data_inicio: {e}")
    
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
            
            # Adicionar coluna email se não existir
            try:
                cursor.execute("""
                    ALTER TABLE funcionarios 
                    ADD COLUMN IF NOT EXISTS email VARCHAR(255)
                """)
                logger.info("✅ Coluna email adicionada/verificada em funcionarios")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao adicionar coluna email: {e}")
            
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
@csrf_instance.exempt
@limiter.limit("5 per minute")  # Máximo 5 tentativas por minuto
def login():
    """Endpoint de login com proteção contra brute force"""
    try:
        print(f"\n{'='*80}")
        print(f"🔐 [LOGIN] Iniciando processo de login...")
        print(f"{'='*80}")
        
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        print(f"📝 Dados recebidos:")
        print(f"   - username: {username}")
        print(f"   - password: {'***' if password else 'VAZIO'}")
        
        if not username or not password:
            print(f"❌ Username ou senha vazios")
            return jsonify({
                'success': False,
                'error': 'Username e senha são obrigatórios'
            }), 400
        
        # Verificar se conta está bloqueada
        print(f"🔍 Verificando se conta está bloqueada...")
        from auth_functions import verificar_conta_bloqueada
        if verificar_conta_bloqueada(username, db):
            print(f"🚫 Conta bloqueada!")
            return jsonify({
                'success': False,
                'error': 'Conta temporariamente bloqueada por excesso de tentativas. Tente novamente em 15 minutos.'
            }), 429
        print(f"✅ Conta não bloqueada")
        
        # Autenticar usuário
        print(f"🔑 Chamando auth_db.autenticar_usuario('{username}', '***')...")
        usuario = auth_db.autenticar_usuario(username, password)
        print(f"📊 Resultado autenticação: {usuario if usuario else 'FALHOU'}")
        
        if not usuario:
            print(f"❌ Autenticação falhou!")
            # Registrar tentativa falha
            auth_db.registrar_log_acesso(
                usuario_id=None,
                acao='login_failed',
                descricao=f'Tentativa de login falhou para username: {username}',
                ip_address=request.remote_addr,
                sucesso=False
            )
            print(f"{'='*80}\n")
            return jsonify({
                'success': False,
                'error': 'Usuário ou senha inválidos'
            }), 401
        
        print(f"✅ Usuário autenticado:")
        print(f"   - id: {usuario.get('id')}")
        print(f"   - username: {usuario.get('username')}")
        print(f"   - tipo: {usuario.get('tipo')}")
        
        # Criar sessão
        print(f"🎫 Criando sessão...")
        token = auth_db.criar_sessao(
            usuario['id'],
            request.remote_addr,
            request.headers.get('User-Agent', '')
        )
        print(f"✅ Sessão criada: {token[:20]}...")
        
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
        
        # ============================================================
        # MULTI-EMPRESA: Carregar empresas do usuário
        # ============================================================
        empresas_disponiveis = []
        empresa_selecionada = None
        
        if usuario['tipo'] == 'admin':
            # Super admin tem acesso a todas as empresas
            empresas_disponiveis = database.listar_empresas({})
            # Não selecionar empresa automaticamente para super admin
        else:
            # Carregar empresas que o usuário tem acesso
            from auth_functions import listar_empresas_usuario, obter_empresa_padrao
            empresas_disponiveis = listar_empresas_usuario(usuario['id'], auth_db)
            
            if empresas_disponiveis:
                # Buscar empresa padrão
                empresa_padrao_id = obter_empresa_padrao(usuario['id'], auth_db)
                
                if empresa_padrao_id:
                    empresa_selecionada = next((e for e in empresas_disponiveis if e.get('empresa_id') == empresa_padrao_id), None)
                else:
                    # Se não tem padrão, selecionar a primeira
                    empresa_selecionada = empresas_disponiveis[0]
                
                if empresa_selecionada:
                    session['empresa_id'] = empresa_selecionada.get('empresa_id')
                    print(f"✅ Empresa selecionada no login: {empresa_selecionada.get('razao_social')}")
        
        # Obter permissões do usuário
        if usuario['tipo'] == 'admin':
            permissoes = ['*']  # Super admin tem todas as permissões
        elif empresa_selecionada:
            from auth_functions import obter_permissoes_usuario_empresa
            permissoes = obter_permissoes_usuario_empresa(usuario['id'], empresa_selecionada.get('empresa_id'), auth_db)
        else:
            permissoes = auth_db.obter_permissoes_usuario(usuario['id'])
        
        # Preparar resposta
        response_data = {
            'success': True,
            'message': 'Login realizado com sucesso',
            'usuario': {
                'id': usuario['id'],
                'username': usuario['username'],
                'nome_completo': usuario['nome_completo'],
                'tipo': usuario['tipo'],
                'email': usuario['email']
            },
            'permissoes': permissoes,
            'empresas_disponiveis': [{
                'id': e.get('empresa_id'),
                'razao_social': e.get('razao_social'),
                'is_padrao': e.get('is_empresa_padrao', False)
            } for e in empresas_disponiveis] if empresas_disponiveis else []
        }
        
        # Adicionar empresa selecionada se houver
        if empresa_selecionada:
            response_data['empresa_selecionada'] = {
                'id': empresa_selecionada.get('empresa_id'),
                'razao_social': empresa_selecionada.get('razao_social')
            }
        
        # Se usuário tem múltiplas empresas, indicar que precisa escolher
        if len(empresas_disponiveis) > 1 and usuario['tipo'] != 'admin':
            response_data['require_empresa_selection'] = True
        
        return jsonify(response_data)
        
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
        print(f"\n{'='*80}")
        print(f"🔍 [VERIFY] Verificando sessão...")
        print(f"{'='*80}")
        
        usuario = get_usuario_logado()
        print(f"📊 Usuário logado: {usuario if usuario else 'NENHUM'}")
        
        if not usuario:
            print(f"❌ Usuário não autenticado - retornando False")
            print(f"{'='*80}\n")
            return jsonify({
                'success': False,
                'authenticated': False
            })
        
        print(f"✅ Usuário autenticado:")
        print(f"   - id: {usuario.get('id')}")
        print(f"   - username: {usuario.get('username')}")
        print(f"   - tipo: {usuario.get('tipo')}")
        
        # ============================================================
        # MULTI-EMPRESA: Carregar empresa atual e empresas disponíveis
        # ============================================================
        empresa_atual = None
        empresas_disponiveis = []
        
        if usuario['tipo'] == 'admin':
            print(f"👑 Tipo: Admin")
            # Super admin
            permissoes = ['*']
            empresas_disponiveis = database.listar_empresas({})
            print(f"   - Empresas disponíveis: {len(empresas_disponiveis)}")
            empresa_id = session.get('empresa_id')
            print(f"   - empresa_id na sessão: {empresa_id}")
            if empresa_id:
                empresa_atual = database.obter_empresa(empresa_id)
                print(f"   - Empresa atual: {empresa_atual.get('razao_social') if empresa_atual else 'Não encontrada'}")
        else:
            print(f"👤 Tipo: Cliente")
            # Usuário normal
            from auth_functions import listar_empresas_usuario
            empresas_disponiveis = listar_empresas_usuario(usuario['id'], auth_db)
            print(f"   - Empresas disponíveis: {len(empresas_disponiveis)}")
            print(f"   - IDs: {[e.get('empresa_id') for e in empresas_disponiveis]}")
            
            empresa_id = session.get('empresa_id')
            print(f"   - empresa_id na sessão: {empresa_id}")
            
            if empresa_id:
                # Carregar permissões específicas da empresa
                from auth_functions import obter_permissoes_usuario_empresa
                permissoes = obter_permissoes_usuario_empresa(usuario['id'], empresa_id, auth_db)
                print(f"   - Permissões da empresa: {len(permissoes)} itens")
                
                # Buscar dados da empresa atual
                empresa_atual = next((e for e in empresas_disponiveis if e.get('empresa_id') == empresa_id), None)
                print(f"   - Empresa atual: {empresa_atual.get('razao_social') if empresa_atual else 'Não encontrada'}")
            else:
                # Sem empresa selecionada
                print(f"   ⚠️ Sem empresa na sessão - usando permissões globais")
                permissoes = auth_db.obter_permissoes_usuario(usuario['id'])
                print(f"   - Permissões globais: {len(permissoes)} itens")
        
        response = {
            'success': True,
            'authenticated': True,
            'usuario': {
                'id': usuario['id'],
                'username': usuario['username'],
                'nome_completo': usuario['nome_completo'],
                'tipo': usuario['tipo'],
                'email': usuario['email'],
                'permissoes': permissoes
            },
            'permissoes': permissoes,
            'empresas_disponiveis': [{
                'id': e.get('empresa_id') if usuario['tipo'] != 'admin' else e.get('id'),
                'razao_social': e.get('razao_social'),
                'is_padrao': e.get('is_empresa_padrao', False)
            } for e in empresas_disponiveis] if empresas_disponiveis else []
        }
        
        # Adicionar empresa atual se houver
        if empresa_atual:
            response['empresa_atual'] = {
                'id': empresa_atual.get('empresa_id') if usuario['tipo'] != 'admin' else empresa_atual.get('id'),
                'razao_social': empresa_atual.get('razao_social')
            }
        
        print(f"✅ Sessão válida - retornando dados")
        print(f"{'='*80}\n")
        return jsonify(response)
        
    except Exception as e:
        print(f"\n❌ ERRO ao verificar sessão:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*80}\n")
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


# ===================================================================
# ROTAS DE GESTÃO MULTI-EMPRESA (Usuário com Acesso a Múltiplas Empresas)
# ===================================================================

@app.route('/api/auth/minhas-empresas', methods=['GET'])
@require_auth
def minhas_empresas():
    """Lista todas as empresas que o usuário tem acesso"""
    try:
        usuario = request.usuario
        
        # Super admin tem acesso a todas as empresas
        if usuario['tipo'] == 'admin':
            empresas = database.listar_empresas({})
            return jsonify({
                'success': True,
                'empresas': [{
                    'id': e['id'],
                    'razao_social': e['razao_social'],
                    'cnpj': e.get('cnpj'),
                    'papel': 'admin',
                    'is_padrao': False,
                    'permissoes': ['*']  # Todas as permissões
                } for e in empresas]
            })
        
        # Usuários normais: buscar empresas vinculadas
        from auth_functions import listar_empresas_usuario
        empresas = listar_empresas_usuario(usuario['id'], auth_db)
        
        if not empresas:
            return jsonify({
                'success': True,
                'empresas': [],
                'message': 'Usuário não está vinculado a nenhuma empresa'
            })
        
        return jsonify({
            'success': True,
            'empresas': empresas
        })
        
    except Exception as e:
        print(f"❌ Erro ao listar empresas do usuário: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/auth/switch-empresa', methods=['POST'])
@require_auth
def switch_empresa():
    """Troca a empresa atual do usuário na sessão"""
    print(f"\n{'='*80}")
    print(f"🔄 [SWITCH-EMPRESA] Requisição recebida")
    try:
        data = request.json
        print(f"📦 Dados recebidos: {data}")
        empresa_id = data.get('empresa_id')
        print(f"🏢 Empresa ID: {empresa_id}")
        
        if not empresa_id:
            print(f"❌ empresa_id não fornecido")
            return jsonify({
                'success': False,
                'error': 'empresa_id é obrigatório'
            }), 400
        
        usuario = request.usuario
        print(f"👤 Usuário: {usuario['username']} (tipo: {usuario['tipo']})")
        
        # Super admin pode acessar qualquer empresa
        if usuario['tipo'] != 'admin':
            # Validar se usuário tem acesso à empresa
            from auth_functions import tem_acesso_empresa
            print(f"🔐 Validando acesso do usuário à empresa...")
            if not tem_acesso_empresa(usuario['id'], empresa_id, auth_db):
                print(f"❌ Acesso negado")
                return jsonify({
                    'success': False,
                    'error': 'Acesso negado a esta empresa'
                }), 403
            print(f"✅ Acesso validado")
        else:
            print(f"👑 Admin - acesso total")
        
        # Buscar dados da empresa
        print(f"🔍 Buscando dados da empresa {empresa_id}...")
        empresa = database.obter_empresa(empresa_id)
        print(f"📊 Resultado da busca: {empresa}")
        if not empresa:
            print(f"❌ Empresa {empresa_id} não encontrada no banco de dados")
            return jsonify({
                'success': False,
                'error': 'Empresa não encontrada'
            }), 404
        
        print(f"✅ Empresa encontrada: {empresa.get('razao_social')}")
        
        # Atualizar sessão - PRESERVANDO TODOS OS DADOS EXISTENTES
        print(f"💾 Atualizando sessão com empresa_id={empresa_id}")
        print(f"🔍 Sessão ANTES do switch: {dict(session)}")
        
        # Verificar se o token ainda está na sessão
        if 'token' not in session:
            print(f"⚠️ AVISO: Token não encontrado na sessão durante switch!")
            print(f"⚠️ Dados disponíveis: {list(session.keys())}")
        
        session['empresa_id'] = empresa_id
        session.modified = True
        
        print(f"🔍 Sessão DEPOIS do switch: {dict(session)}")
        print(f"✅ Sessão atualizada (empresa_id={session.get('empresa_id')})")
        
        # Registrar troca de empresa
        print(f"📝 Registrando log de troca de empresa...")
        auth_db.registrar_log_acesso(
            usuario_id=usuario['id'],
            acao='switch_empresa',
            descricao=f'Trocou para empresa: {empresa["razao_social"]}',
            ip_address=request.remote_addr,
            sucesso=True
        )
        print(f"✅ Log registrado")
        
        # Carregar permissões da nova empresa
        print(f"🔐 Carregando permissões...")
        if usuario['tipo'] != 'admin':
            from auth_functions import obter_permissoes_usuario_empresa
            permissoes = obter_permissoes_usuario_empresa(usuario['id'], empresa_id, auth_db)
        else:
            permissoes = ['*']  # Super admin tem todas as permissões
        print(f"📋 Permissões carregadas: {len(permissoes)}")
        
        print(f"✅ Troca de empresa concluída com sucesso")
        print(f"{'='*80}\n")
        return jsonify({
            'success': True,
            'message': 'Empresa alterada com sucesso',
            'empresa': {
                'id': empresa['id'],
                'razao_social': empresa['razao_social'],
                'cnpj': empresa.get('cnpj')
            },
            'permissoes': permissoes
        })
        
    except Exception as e:
        print(f"❌ ERRO em switch-empresa: {e}")
        print(f"❌ Tipo do erro: {type(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*80}\n")
        return jsonify({
            'success': False,
            'error': 'Erro ao trocar empresa'
        }), 500


@app.route('/api/auth/empresa-padrao', methods=['PUT'])
@require_auth
def definir_empresa_padrao():
    """Define a empresa padrão do usuário (selecionada automaticamente no login)"""
    try:
        data = request.json
        empresa_id = data.get('empresa_id')
        
        if not empresa_id:
            return jsonify({
                'success': False,
                'error': 'empresa_id é obrigatório'
            }), 400
        
        usuario = request.usuario
        
        # Super admin não precisa de empresa padrão
        if usuario['tipo'] == 'admin':
            return jsonify({
                'success': False,
                'error': 'Super admin não precisa de empresa padrão'
            }), 400
        
        # Validar acesso à empresa
        from auth_functions import tem_acesso_empresa, atualizar_usuario_empresa
        if not tem_acesso_empresa(usuario['id'], empresa_id, auth_db):
            return jsonify({
                'success': False,
                'error': 'Acesso negado a esta empresa'
            }), 403
        
        # Atualizar empresa padrão
        sucesso = atualizar_usuario_empresa(
            usuario['id'], 
            empresa_id,
            is_padrao=True,
            db=auth_db
        )
        
        if not sucesso:
            return jsonify({
                'success': False,
                'error': 'Erro ao definir empresa padrão'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Empresa padrão definida com sucesso'
        })
        
    except Exception as e:
        print(f"❌ Erro ao definir empresa padrão: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/usuario-empresas', methods=['POST'])
@require_admin
def vincular_usuario_empresa_admin():
    """Vincula um usuário a uma empresa (apenas admin)"""
    try:
        data = request.json
        usuario_id = data.get('usuario_id')
        empresa_id = data.get('empresa_id')
        papel = data.get('papel', 'usuario')
        permissoes = data.get('permissoes', [])
        is_padrao = data.get('is_padrao', False)
        
        if not usuario_id or not empresa_id:
            return jsonify({
                'success': False,
                'error': 'usuario_id e empresa_id são obrigatórios'
            }), 400
        
        if papel not in ['admin_empresa', 'usuario', 'visualizador']:
            return jsonify({
                'success': False,
                'error': 'Papel inválido. Use: admin_empresa, usuario ou visualizador'
            }), 400
        
        admin = request.usuario
        
        # Vincular usuário à empresa
        from auth_functions import vincular_usuario_empresa
        vinculo_id = vincular_usuario_empresa(
            usuario_id=usuario_id,
            empresa_id=empresa_id,
            papel=papel,
            permissoes=permissoes,
            is_padrao=is_padrao,
            criado_por=admin['id'],
            db=auth_db
        )
        
        # Registrar ação
        auth_db.registrar_log_acesso(
            usuario_id=admin['id'],
            acao='vincular_usuario_empresa',
            descricao=f'Vinculou usuário {usuario_id} à empresa {empresa_id}',
            ip_address=request.remote_addr,
            sucesso=True
        )
        
        return jsonify({
            'success': True,
            'message': 'Usuário vinculado à empresa com sucesso',
            'id': vinculo_id
        }), 201
        
    except Exception as e:
        print(f"❌ Erro ao vincular usuário à empresa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/usuario-empresas/<int:usuario_id>/<int:empresa_id>', methods=['PUT'])
@require_admin
def atualizar_usuario_empresa_admin(usuario_id: int, empresa_id: int):
    """Atualiza o vínculo de um usuário com uma empresa (apenas admin)"""
    try:
        data = request.json
        papel = data.get('papel')
        permissoes = data.get('permissoes')
        is_padrao = data.get('is_padrao')
        
        from auth_functions import atualizar_usuario_empresa
        sucesso = atualizar_usuario_empresa(
            usuario_id=usuario_id,
            empresa_id=empresa_id,
            papel=papel,
            permissoes=permissoes,
            is_padrao=is_padrao,
            db=auth_db
        )
        
        if not sucesso:
            return jsonify({
                'success': False,
                'error': 'Erro ao atualizar vínculo'
            }), 500
        
        # Registrar ação
        admin = request.usuario
        auth_db.registrar_log_acesso(
            usuario_id=admin['id'],
            acao='atualizar_usuario_empresa',
            descricao=f'Atualizou vínculo do usuário {usuario_id} com empresa {empresa_id}',
            ip_address=request.remote_addr,
            sucesso=True
        )
        
        return jsonify({
            'success': True,
            'message': 'Vínculo atualizado com sucesso'
        })
        
    except Exception as e:
        print(f"❌ Erro ao atualizar vínculo: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/usuario-empresas/<int:usuario_id>/<int:empresa_id>', methods=['DELETE'])
@require_admin
def remover_usuario_empresa_admin(usuario_id: int, empresa_id: int):
    """Remove o vínculo de um usuário com uma empresa (apenas admin)"""
    try:
        from auth_functions import remover_usuario_empresa
        sucesso = remover_usuario_empresa(usuario_id, empresa_id, auth_db)
        
        if not sucesso:
            return jsonify({
                'success': False,
                'error': 'Erro ao remover vínculo'
            }), 500
        
        # Registrar ação
        admin = request.usuario
        auth_db.registrar_log_acesso(
            usuario_id=admin['id'],
            acao='remover_usuario_empresa',
            descricao=f'Removeu vínculo do usuário {usuario_id} com empresa {empresa_id}',
            ip_address=request.remote_addr,
            sucesso=True
        )
        
        return jsonify({
            'success': True,
            'message': 'Vínculo removido com sucesso'
        })
        
    except Exception as e:
        print(f"❌ Erro ao remover vínculo: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/usuarios/<int:usuario_id>/empresas', methods=['GET'])
@require_admin
def listar_empresas_do_usuario_admin(usuario_id: int):
    """Lista todas as empresas que um usuário tem acesso (apenas admin)"""
    try:
        from auth_functions import listar_empresas_usuario
        empresas = listar_empresas_usuario(usuario_id, auth_db)
        
        return jsonify({
            'success': True,
            'empresas': empresas
        })
        
    except Exception as e:
        print(f"❌ Erro ao listar empresas do usuário: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== FIM DAS ROTAS MULTI-EMPRESA =====

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
            
            print(f"📥 Dados recebidos do frontend: {data}")
            print(f"   - empresas_ids: {data.get('empresas_ids')}")
            print(f"   - empresa_id_padrao: {data.get('empresa_id_padrao')}")
            print(f"   - tipo: {data.get('tipo')}")
            
            # Validar empresas
            empresas_ids = data.get('empresas_ids', [])
            if not empresas_ids or len(empresas_ids) == 0:
                return jsonify({
                    'success': False,
                    'error': 'Selecione ao menos uma empresa'
                }), 400
            
            # Validar força da senha
            from auth_functions import validar_senha_forte
            if 'password' in data:
                valida, mensagem = validar_senha_forte(data['password'])
                if not valida:
                    return jsonify({
                        'success': False,
                        'error': f'Senha fraca: {mensagem}'
                    }), 400
            
            # 🏢 MULTI-EMPRESA: Usar primeira empresa para criação (compatibilidade)
            data['empresa_id'] = empresas_ids[0]
            
            print(f"📝 Dados para criar_usuario: {data}")
            usuario_id = auth_db.criar_usuario(data)
            print(f"✅ Usuário criado com ID: {usuario_id}")
            
            # 🏢 MULTI-EMPRESA: Criar vínculos na tabela usuario_empresas
            from auth_functions import vincular_usuario_empresa
            empresa_id_padrao = data.get('empresa_id_padrao')
            
            for empresa_id in empresas_ids:
                is_padrao = (empresa_id == empresa_id_padrao)
                
                print(f"🔗 Vinculando usuário {usuario_id} à empresa {empresa_id} (padrão: {is_padrao})")
                
                vincular_usuario_empresa(
                    usuario_id=usuario_id,
                    empresa_id=empresa_id,
                    papel='usuario',  # Papel padrão
                    permissoes=data.get('permissoes', []),
                    is_padrao=is_padrao,
                    criado_por=admin['id'],
                    db=auth_db
                )
            
            # Conceder permissões globais se fornecidas (legado)
            if 'permissoes' in data:
                print(f"🔑 Concedendo {len(data['permissoes'])} permissões")
                auth_db.sincronizar_permissoes_usuario(
                    usuario_id,
                    data['permissoes'],
                    admin['id']
                )
            
            # Registrar criação
            auth_db.registrar_log_acesso(
                usuario_id=admin['id'],
                acao='create_user',
                descricao=f'Usuário criado: {data["username"]} com {len(empresas_ids)} empresa(s)',
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
            print(f"\n{'='*80}")
            print(f"   🔍 GET /api/usuarios/{usuario_id}")
            print(f"{'='*80}")
            print(f"   🔍 Buscando usuário ID {usuario_id}...")
            
            usuario = auth_db.obter_usuario(usuario_id)
            print(f"   📊 Tipo do resultado: {type(usuario)}")
            print(f"   📊 Resultado: {usuario if usuario else 'NÃO ENCONTRADO'}")
            
            if not usuario:
                print(f"   ❌ Usuário {usuario_id} não encontrado")
                return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 404
            
            print(f"   🔄 Convertendo para dict...")
            # Converter para dict se necessário
            usuario_dict = dict(usuario) if not isinstance(usuario, dict) else usuario.copy()
            print(f"   ✅ Dict criado. Keys: {list(usuario_dict.keys())}")
            
            print(f"   🔄 Serializando campos datetime...")
            # Converter datetime para string (JSON serializable)
            datetime_fields = ['created_at', 'ultima_sessao', 'updated_at', 'ultimo_acesso']
            for field in datetime_fields:
                if field in usuario_dict and usuario_dict[field]:
                    try:
                        print(f"      - {field}: {type(usuario_dict[field])} → str")
                        usuario_dict[field] = str(usuario_dict[field])
                    except Exception as e:
                        print(f"      ⚠️ Erro ao serializar {field}: {e}")
                        usuario_dict[field] = None
            
            # Garantir que empresa_id é int ou None
            if 'empresa_id' in usuario_dict and usuario_dict['empresa_id']:
                try:
                    usuario_dict['empresa_id'] = int(usuario_dict['empresa_id'])
                except:
                    usuario_dict['empresa_id'] = None
            
            print(f"   🔄 Obtendo permissões...")
            # Incluir permissões
            permissoes = auth_db.obter_permissoes_usuario(usuario_id)
            print(f"   📊 Permissões: {permissoes}")
            usuario_dict['permissoes'] = permissoes
            
            print(f"   🔄 Serializando para JSON...")
            result = jsonify(usuario_dict)
            print(f"   ✅ JSON criado com sucesso")
            print(f"{'='*80}\n")
            return result
            
        except Exception as e:
            print(f"\n{'='*80}")
            print(f"❌ ERRO ao obter usuário {usuario_id}")
            print(f"❌ Tipo do erro: {type(e).__name__}")
            print(f"❌ Mensagem: {e}")
            print(f"❌ Stacktrace:")
            import traceback
            traceback.print_exc()
            print(f"{'='*80}\n")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.json
            admin = request.usuario
            
            print(f"\n{'='*80}")
            print(f"📝 PUT /api/usuarios/{usuario_id} - INICIANDO")
            print(f"{'='*80}")
            print(f"📥 DADOS RECEBIDOS DO FRONTEND:")
            print(f"   - Tipo de data: {type(data)}")
            print(f"   - Keys presentes: {list(data.keys()) if data else 'NENHUMA'}")
            print(f"   - JSON completo: {json.dumps(data, indent=2, default=str)}")
            print(f"\n🔍 CAMPOS ESPECÍFICOS:")
            print(f"   - username: {data.get('username')} (tipo: {type(data.get('username'))})")
            print(f"   - nome_completo: {data.get('nome_completo')} (tipo: {type(data.get('nome_completo'))})")
            print(f"   - email: {data.get('email')} (tipo: {type(data.get('email'))})")
            print(f"   - telefone: {data.get('telefone')} (tipo: {type(data.get('telefone'))})")
            print(f"   - tipo: {data.get('tipo')} (tipo: {type(data.get('tipo'))})")
            print(f"   - ativo: {data.get('ativo')} (tipo: {type(data.get('ativo'))})")
            print(f"   - empresa_id: {data.get('empresa_id')} (tipo: {type(data.get('empresa_id'))})")
            print(f"   - empresas_ids: {data.get('empresas_ids')} (tipo: {type(data.get('empresas_ids'))})")
            print(f"   - empresa_id_padrao: {data.get('empresa_id_padrao')} (tipo: {type(data.get('empresa_id_padrao'))})")
            print(f"   - permissoes: {data.get('permissoes')} (tipo: {type(data.get('permissoes'))})")
            print(f"   - password presente: {'Sim' if 'password' in data else 'Não'}")
            
            # Validar força da senha se estiver sendo alterada
            if 'password' in data and data['password']:
                print(f"\n🔐 Validando senha...")
                from auth_functions import validar_senha_forte
                valida, mensagem = validar_senha_forte(data['password'])
                if not valida:
                    print(f"❌ Senha fraca: {mensagem}")
                    print(f"{'='*80}\n")
                    return jsonify({
                        'success': False,
                        'error': f'Senha fraca: {mensagem}'
                    }), 400
                print(f"✅ Senha válida")
            
            print(f"\n🔄 Chamando auth_db.atualizar_usuario({usuario_id}, data)...")
            print(f"   Função: {auth_db.atualizar_usuario}")
            # Atualizar dados do usuário
            success = auth_db.atualizar_usuario(usuario_id, data)
            print(f"   Resultado: {success} (tipo: {type(success)})")
            
            if not success:
                print(f"❌ Usuário {usuario_id} não encontrado")
                return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 404
            
            print(f"✅ Dados do usuário atualizados")
            
            # 🏢 MULTI-EMPRESA: Atualizar vínculos se empresas_ids fornecido
            if 'empresas_ids' in data:
                print(f"🏢 Atualizando vínculos multi-empresa...")
                from auth_functions import (
                    vincular_usuario_empresa,
                    remover_usuario_empresa,
                    listar_empresas_usuario
                )
                
                empresas_ids = data['empresas_ids']
                empresa_id_padrao = data.get('empresa_id_padrao')
                
                print(f"   - Empresas selecionadas: {empresas_ids}")
                print(f"   - Empresa padrão: {empresa_id_padrao}")
                
                # Obter empresas atuais
                print(f"   🔍 Obtendo empresas atuais...")
                empresas_atuais = listar_empresas_usuario(usuario_id, auth_db)
                empresas_atuais_ids = [e['empresa_id'] for e in empresas_atuais]
                print(f"   - Empresas atuais: {empresas_atuais_ids}")
                
                # Remover vínculos que não estão mais selecionados
                for empresa_id_atual in empresas_atuais_ids:
                    if empresa_id_atual not in empresas_ids:
                        print(f"🗑️ Removendo vínculo com empresa {empresa_id_atual}")
                        remover_usuario_empresa(usuario_id, empresa_id_atual, auth_db)
                
                # Adicionar novos vínculos
                for empresa_id in empresas_ids:
                    if empresa_id not in empresas_atuais_ids:
                        is_padrao = (empresa_id == empresa_id_padrao)
                        permissoes_para_empresa = data.get('permissoes', [])
                        print(f"➕ Adicionando vínculo com empresa {empresa_id} (padrão: {is_padrao})")
                        print(f"   📋 Permissões a serem salvas: {permissoes_para_empresa}")
                        
                        vincular_usuario_empresa(
                            usuario_id=usuario_id,
                            empresa_id=empresa_id,
                            papel='usuario',
                            permissoes=permissoes_para_empresa,
                            is_padrao=is_padrao,
                            criado_por=admin['id'],
                            db=auth_db
                        )
                    else:
                        # Atualizar empresa padrão se necessário
                        from auth_functions import atualizar_usuario_empresa
                        is_padrao = (empresa_id == empresa_id_padrao)
                        permissoes_para_empresa = data.get('permissoes', [])
                        
                        # Obter vínculo atual
                        vinculo_atual = next((e for e in empresas_atuais if e['empresa_id'] == empresa_id), None)
                        
                        print(f"🔄 Atualizando vínculo com empresa {empresa_id} (padrão: {is_padrao})")
                        print(f"   📋 Permissões a serem salvas: {permissoes_para_empresa}")
                        
                        atualizar_usuario_empresa(
                            usuario_id=usuario_id,
                            empresa_id=empresa_id,
                            papel=vinculo_atual.get('papel', 'usuario') if vinculo_atual else 'usuario',
                            permissoes=permissoes_para_empresa,
                            is_padrao=is_padrao,
                            db=auth_db
                        )
            
            # Atualizar permissões globais se fornecidas (legado)
            if 'permissoes' in data:
                print(f"🔑 Atualizando permissões globais...")
                print(f"   - Permissões: {data['permissoes']}")
                auth_db.sincronizar_permissoes_usuario(
                    usuario_id,
                    data['permissoes'],
                    admin['id']
                )
                print(f"   ✅ Permissões atualizadas")
            
            # Registrar atualização
            auth_db.registrar_log_acesso(
                usuario_id=admin['id'],
                acao='update_user',
                descricao=f'Usuário atualizado: ID {usuario_id}',
                ip_address=request.remote_addr,
                sucesso=True
            )
            
            print(f"✅ Usuário {usuario_id} atualizado com sucesso!")
            print(f"{'='*80}\n")
            
            return jsonify({
                'success': True,
                'message': 'Usuário atualizado com sucesso'
            })
            
        except Exception as e:
            print(f"\n{'='*80}")
            print(f"❌ ERRO ao atualizar usuário {usuario_id}")
            print(f"❌ Tipo do erro: {type(e).__name__}")
            print(f"❌ Mensagem: {e}")
            print(f"❌ Stacktrace:")
            import traceback
            traceback.print_exc()
            print(f"{'='*80}\n")
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


@app.route('/api/usuarios/<int:usuario_id>/permissoes', methods=['PUT'])
@require_admin
def atualizar_permissoes_usuario(usuario_id):
    """Atualizar apenas as permissões de um usuário"""
    print(f"\n🔐 [atualizar_permissoes_usuario] FUNÇÃO CHAMADA - ID: {usuario_id}")
    try:
        data = request.json
        permissoes = data.get('permissoes', [])
        
        print(f"📋 Permissões recebidas: {permissoes}")
        
        # Verificar se usuário existe
        usuario = auth_db.obter_usuario(usuario_id)
        if not usuario:
            print(f"❌ Usuário {usuario_id} não encontrado")
            return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 404
        
        # Atualizar permissões
        print(f"🔄 Atualizando permissões...")
        success = auth_db.atualizar_permissoes_usuario(usuario_id, permissoes)
        
        if success:
            print(f"✅ Permissões atualizadas com sucesso!")
            return jsonify({
                'success': True,
                'message': 'Permissões atualizadas com sucesso'
            })
        else:
            print(f"❌ Falha ao atualizar permissões")
            return jsonify({'success': False, 'error': 'Falha ao atualizar permissões'}), 500
            
    except Exception as e:
        print(f"❌ Erro ao atualizar permissões: {e}")
        import traceback
        traceback.print_exc()
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
        # 🔒 CORREÇÃO: Usar empresa_id da sessão ao invés de proprietario_id
        from flask import session
        empresa_id = session.get('empresa_id')
        
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        contas = db.listar_contas_por_empresa(empresa_id=empresa_id)
        
        # Preparar resposta - CALCULAR saldo real com base nos lançamentos pagos
        contas_com_saldo = []
        for c in contas:
            # Calcular saldo real = saldo_inicial + receitas pagas - despesas pagas
            saldo_real = float(c.saldo_inicial)
            
            try:
                # Buscar lançamentos PAGOS desta conta
                with get_db_connection(empresa_id=empresa_id) as conn:
                    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                    
                    # Somar receitas pagas
                    cursor.execute("""
                        SELECT COALESCE(SUM(valor), 0) as total_receitas
                        FROM lancamentos
                        WHERE empresa_id = %s
                        AND conta_bancaria = %s
                        AND tipo = 'receita'
                        AND status = 'pago'
                    """, (empresa_id, c.nome))
                    resultado_receitas = cursor.fetchone()
                    total_receitas = float(resultado_receitas['total_receitas'] or 0)
                    
                    # Somar despesas pagas
                    cursor.execute("""
                        SELECT COALESCE(SUM(valor), 0) as total_despesas
                        FROM lancamentos
                        WHERE empresa_id = %s
                        AND conta_bancaria = %s
                        AND tipo = 'despesa'
                        AND status = 'pago'
                    """, (empresa_id, c.nome))
                    resultado_despesas = cursor.fetchone()
                    total_despesas = float(resultado_despesas['total_despesas'] or 0)
                    
                    cursor.close()
                    
                    # Calcular saldo real
                    saldo_real = float(c.saldo_inicial) + total_receitas - total_despesas
                    
            except Exception as e:
                print(f"⚠️ Erro ao calcular saldo real da conta {c.nome}: {e}")
                import traceback
                traceback.print_exc()
                # Em caso de erro, usar saldo_inicial
                saldo_real = float(c.saldo_inicial)
            
            contas_com_saldo.append({
                'nome': c.nome,
                'banco': c.banco,
                'agencia': c.agencia,
                'conta': c.conta,
                'saldo_inicial': float(c.saldo_inicial),
                'saldo': saldo_real,  # Saldo real calculado
                'saldo_real': saldo_real,  # Alias para compatibilidade
                'ativa': c.ativa if hasattr(c, 'ativa') else True
            })
        
        return jsonify({
            'success': True,
            'data': contas_com_saldo,
            'total': len(contas_com_saldo),
            'message': 'Nenhuma conta cadastrada' if len(contas_com_saldo) == 0 else None
        })
    except Exception as e:
        print(f"❌ Erro em /api/contas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/api/contas', methods=['POST'])
@require_permission('contas_create')
@aplicar_filtro_cliente
def adicionar_conta():
    """Adiciona uma nova conta bancária"""
    try:
        from flask import session
        
        # 🔒 Obter empresa_id da sessão (OBRIGATÓRIO)
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        data = request.json
        
        # Validar campos obrigatórios
        if not data.get('nome'):
            return jsonify({'success': False, 'error': 'Nome da conta é obrigatório'}), 400
        if not data.get('banco'):
            return jsonify({'success': False, 'error': 'Banco é obrigatório'}), 400
        
        # 👥 proprietario_id = ID do USUÁRIO logado (se aplicável), não empresa_id!
        usuario = get_usuario_logado()
        proprietario_id = usuario.get('id') if usuario.get('tipo') == 'cliente' else None
        
        print(f"\n🔍 [POST /api/contas] Adicionando conta:")
        print(f"   - empresa_id: {empresa_id}")
        print(f"   - proprietario_id (usuario): {proprietario_id}")
        print(f"   - nome: {data.get('nome')}")
        print(f"   - banco: {data.get('banco')}")
        
        # Verificar contas existentes da mesma empresa antes de adicionar
        contas_existentes = db.listar_contas_por_empresa(empresa_id=empresa_id)
        
        # Verificar se já existe conta com mesmo nome na mesma empresa
        for c in contas_existentes:
            if c.nome == data['nome']:
                print(f"   ❌ CONFLITO: Conta '{data['nome']}' já existe na empresa {empresa_id}!")
                return jsonify({'success': False, 'error': f'Já existe uma conta cadastrada com: Banco: {data["banco"]}, Agência: {data["agencia"]}, Conta: {data["conta"]}'}), 400
        
        conta = ContaBancaria(
            nome=data['nome'],  # type: ignore
            banco=data['banco'],  # type: ignore
            agencia=data['agencia'],  # type: ignore
            conta=data['conta'],  # type: ignore
            saldo_inicial=float(data.get('saldo_inicial', 0) if data else 0),  # type: ignore
            tipo_saldo_inicial=data.get('tipo_saldo_inicial', 'credor'),  # type: ignore
            data_inicio=data.get('data_inicio')  # type: ignore
        )
        
        conta_id = db.adicionar_conta(conta, proprietario_id=proprietario_id, empresa_id=empresa_id)
        print(f"   ✅ Conta criada com ID: {conta_id}")
        return jsonify({'success': True, 'id': conta_id})
    except Exception as e:
        print(f"   ❌ Erro ao criar conta: {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        if 'UNIQUE constraint' in error_msg:
            error_msg = 'Já existe uma conta com este nome'
        elif 'foreign key constraint' in error_msg.lower():
            error_msg = 'Erro ao vincular conta: proprietario_id inválido'
        return jsonify({'success': False, 'error': error_msg}), 400


@app.route('/api/contas/<path:nome>', methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])  # type: ignore
@require_permission('contas_view')
def modificar_conta(nome):
    """Busca, atualiza ou remove uma conta bancária"""
    
    # 🔒 VALIDAÇÃO DE SEGURANÇA
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    # Decode do nome que vem URL-encoded
    from urllib.parse import unquote
    nome = unquote(nome)
    
    # Responder ao preflight OPTIONS
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200
    
    if request.method == 'GET':
        try:
            contas = db.listar_contas_por_empresa(empresa_id=empresa_id)
            for conta in contas:
                if conta.nome == nome:
                    return jsonify({
                        'nome': conta.nome,
                        'banco': conta.banco,
                        'agencia': conta.agencia,
                        'conta': conta.conta,
                        'saldo_inicial': float(conta.saldo_inicial),
                        'tipo_saldo_inicial': conta.tipo_saldo_inicial,
                        'data_inicio': conta.data_inicio.isoformat() if hasattr(conta.data_inicio, 'isoformat') else str(conta.data_inicio)
                    })
            return jsonify({'success': False, 'error': 'Conta não encontrada'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    elif request.method == 'PUT':
        try:
            data = request.json
            
            print(f"\n{'='*80}")
            print(f"🔧 PUT /api/contas/{nome}")
            print(f"{'='*80}")
            print(f"📥 Nome da conta a atualizar (parâmetro URL): {nome}")
            print(f"📦 Dados recebidos: {data}")
            print(f"   - Nome novo: {data.get('nome')}")
            print(f"   - Banco: {data.get('banco')}")
            print(f"   - Agência: {data.get('agencia')}")
            print(f"   - Conta: {data.get('conta')}")
            print(f"   - Saldo inicial: {data.get('saldo_inicial')}")
            print(f"   - Data início: {data.get('data_inicio')}")
            print(f"   - Tipo saldo: {data.get('tipo_saldo_inicial')}")
            
            conta = ContaBancaria(
                nome=data['nome'],  # type: ignore
                banco=data['banco'],  # type: ignore
                agencia=data['agencia'],  # type: ignore
                conta=data['conta'],  # type: ignore
                saldo_inicial=float(data.get('saldo_inicial', 0) if data else 0),  # type: ignore
                tipo_saldo_inicial=data.get('tipo_saldo_inicial', 'credor'),  # type: ignore
                data_inicio=data.get('data_inicio')  # type: ignore
            )
            
            print(f"✅ Objeto ContaBancaria criado:")
            print(f"   - Nome: {conta.nome}")
            print(f"📤 Chamando db.atualizar_conta(nome_original='{nome}', conta={conta.nome})")
            
            success = db.atualizar_conta(nome, conta)
            
            print(f"📡 Resultado: success={success}")
            print(f"{'='*80}\n")
            
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
            print(f"\n{'='*80}")
            print(f"🗑️ DELETE /api/contas/{nome}")
            print(f"{'='*80}")
            
            # Verificar se há lançamentos vinculados
            lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
            lancamentos_conta = [l for l in lancamentos if l.conta_bancaria == nome]
            
            print(f"📊 Lançamentos vinculados à conta: {len(lancamentos_conta)}")
            
            if lancamentos_conta:
                print(f"❌ Exclusão bloqueada: conta possui {len(lancamentos_conta)} lançamento(s)")
                print(f"{'='*80}\n")
                return jsonify({
                    'success': False, 
                    'error': f'Não é possível excluir esta conta. Ela possui {len(lancamentos_conta)} lançamento(s) vinculado(s). Use "Inativar" em vez de excluir.'
                }), 400
            
            # Verificar se há transações de extrato vinculadas
            import psycopg2.extras
            
            conn = db.get_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Contar transações de extrato vinculadas à conta
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM transacoes_extrato 
                WHERE conta_bancaria LIKE %s
            """, (f'%{nome}%',))
            
            result = cursor.fetchone()
            total_extratos = result['total'] if result else 0
            
            cursor.close()
            conn.close()
            
            print(f"📊 Transações de extrato vinculadas: {total_extratos}")
            
            if total_extratos > 0:
                print(f"❌ Exclusão bloqueada: conta possui {total_extratos} transação(ões) de extrato")
                print(f"{'='*80}\n")
                return jsonify({
                    'success': False,
                    'error': f'Não é possível excluir esta conta. Ela possui {total_extratos} transação(ões) de extrato importada(s). Use "Inativar" em vez de excluir.'
                }), 400
            
            # Se não há movimentações, pode excluir
            print(f"✅ Nenhuma movimentação encontrada. Excluindo conta...")
            success = db.excluir_conta(nome)
            print(f"📡 Resultado: success={success}")
            print(f"{'='*80}\n")
            
            return jsonify({'success': success})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/contas/<path:nome>/toggle-ativo', methods=['POST'])
@require_permission('contas_edit')
def toggle_ativo_conta(nome):
    """Ativa ou inativa uma conta bancária"""
    # 🔒 VALIDAÇÃO DE SEGURANÇA
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        from urllib.parse import unquote
        nome = unquote(nome)
        
        print(f"\n{'='*80}")
        print(f"🔄 POST /api/contas/{nome}/toggle-ativo")
        print(f"{'='*80}")
        
        # Buscar conta atual
        contas = db.listar_contas_por_empresa(empresa_id=empresa_id)
        conta_atual = None
        for c in contas:
            if c.nome == nome:
                conta_atual = c
                break
        
        if not conta_atual:
            print(f"❌ Conta não encontrada")
            print(f"{'='*80}\n")
            return jsonify({'success': False, 'error': 'Conta não encontrada'}), 404
        
        # Inverter status
        novo_status = not conta_atual.ativa
        print(f"📊 Status atual: {conta_atual.ativa}")
        print(f"📊 Novo status: {novo_status}")
        
        # Atualizar conta com novo status
        conta_atual.ativa = novo_status
        success = db.atualizar_conta(nome, conta_atual)
        
        acao = "ativada" if novo_status else "inativada"
        print(f"✅ Conta {acao} com sucesso")
        print(f"{'='*80}\n")
        
        return jsonify({
            'success': success,
            'ativa': novo_status,
            'message': f'Conta {acao} com sucesso'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/transferencias', methods=['POST'])
@require_permission('lancamentos_create')
def criar_transferencia():
    """Cria uma transferência entre contas bancárias"""
    try:
        data = request.json
        empresa_id = data.get('empresa_id') if data else None
        
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
        
        # Validar se as contas estão ativas
        if hasattr(conta_origem, 'ativa') and not conta_origem.ativa:
            print(f"❌ Tentativa de criar transferência com conta origem inativa: {conta_origem.nome}")
            return jsonify({
                'success': False,
                'error': f'Não é possível criar transferência. A conta de origem "{conta_origem.nome}" está inativa. Reative a conta antes de criar transferências.'
            }), 400
        
        if hasattr(conta_destino, 'ativa') and not conta_destino.ativa:
            print(f"❌ Tentativa de criar transferência com conta destino inativa: {conta_destino.nome}")
            return jsonify({
                'success': False,
                'error': f'Não é possível criar transferência. A conta de destino "{conta_destino.nome}" está inativa. Reative a conta antes de criar transferências.'
            }), 400
        
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
        lancamento_id = db.adicionar_lancamento(lancamento, empresa_id=empresa_id)
        
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
    try:
        print('\n' + '='*80)
        print('🔍 GET /api/categorias - Iniciando listagem de categorias')
        print(f'   📍 Empresa na sessão: {session.get("empresa_id")}')
        print(f'   👤 Usuário na sessão: {session.get("usuario_id")}')
        print(f'   🔑 Session completa: {dict(session)}')
        
        # Filtrar por empresa_id da sessão
        empresa_id = session.get('empresa_id')
        
        # PRIMEIRO: Listar TODAS sem filtro para debug
        todas_categorias = db.listar_categorias(empresa_id=None)
        print(f'   📊 Total de categorias SEM filtro: {len(todas_categorias)}')
        
        # DEPOIS: Listar com filtro
        categorias = db.listar_categorias(empresa_id=empresa_id)
        
        print(f'   📊 Total de categorias COM filtro (empresa_id={empresa_id}): {len(categorias)}')
        for i, c in enumerate(categorias):
            print(f'   [{i+1}] {c.nome} (tipo: {c.tipo.value}, empresa_id: {getattr(c, "empresa_id", "N/A")})')
        
        resultado = [{
            'id': c.id,  # ✅ Adicionar ID da categoria
            'nome': c.nome,
            'tipo': c.tipo.value,
            'subcategorias': c.subcategorias,
            'empresa_id': getattr(c, 'empresa_id', None)
        } for c in categorias]
        
        print(f'   ✅ Retornando {len(resultado)} categorias')
        print('='*80 + '\n')
        return jsonify({
            'success': True,
            'data': resultado,
            'total': len(resultado),
            'message': 'Nenhuma categoria cadastrada. Adicione categorias para organizar suas transações.' if len(resultado) == 0 else None
        })
    except Exception as e:
        print(f'   ❌ Erro ao listar categorias: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/categorias', methods=['POST'])
@require_permission('categorias_create')
def adicionar_categoria():
    """Adiciona uma nova categoria"""
    try:
        print('\n' + '='*80)
        print('🆕 POST /api/categorias - NOVA CATEGORIA')
        print(f'   📍 Headers: {dict(request.headers)}')
        print(f'   🔑 CSRF Token no header: {request.headers.get("X-CSRFToken", "AUSENTE")}')
        print(f'   🏢 Empresa na sessão: {session.get("empresa_id")}')
        print(f'   👤 Usuário na sessão: {session.get("usuario_id")}')
        
        data = request.json
        print(f'   📦 Dados recebidos: {data}')
        
        # Extrair empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            print('   ❌ ERRO: Empresa não identificada na sessão!')
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 400
        
        # Converter tipo para minúscula para compatibilidade com o enum
        tipo_str = data['tipo'].lower() if data and data.get('tipo') else 'receita'  # type: ignore
        
        # Normalizar nome: uppercase e trim
        nome_normalizado = data['nome'].strip().upper() if data and data.get('nome') else ''  # type: ignore
        
        print(f'   📝 Nome normalizado: {nome_normalizado}')
        print(f'   📊 Tipo: {tipo_str}')
        print(f'   🏢 Empresa ID: {empresa_id}')
        
        categoria = Categoria(
            nome=nome_normalizado,  # type: ignore
            tipo=TipoLancamento(tipo_str),  # type: ignore
            subcategorias=data.get('subcategorias', []) if data else [],  # type: ignore
            empresa_id=empresa_id  # type: ignore
        )
        categoria_id = db.adicionar_categoria(categoria)
        
        print(f'   ✅ Categoria criada com ID: {categoria_id}')
        print('='*80 + '\n')
        
        return jsonify({'success': True, 'id': categoria_id})
    except Exception as e:
        import traceback
        print('   ❌ ERRO ao adicionar categoria:')
        traceback.print_exc()
        print('='*80 + '\n')
        
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
            
            print('\n' + '='*80)
            print('✏️ PUT /api/categorias - ATUALIZAR CATEGORIA')
            print(f'   📍 Nome original (URL): {nome}')
            print(f'   🔑 CSRF Token no header: {request.headers.get("X-CSRFToken", "AUSENTE")}')
            print(f'   📦 Dados recebidos: {data}')
            print(f'   🏢 Empresa na sessão: {session.get("empresa_id")}')
            print(f'   👤 Usuário na sessão: {session.get("usuario_id")}')
            
            # Extrair empresa_id do request ou sessão
            empresa_id = data.get('empresa_id') if data else None
            if not empresa_id:
                empresa_id = session.get('empresa_id')
            
            print(f'   🏢 empresa_id a ser usado: {empresa_id}')
            
            # Converter tipo para minúscula para compatibilidade com o enum
            tipo_str = data['tipo'].lower() if data and data.get('tipo') else 'receita'  # type: ignore
            
            # Normalizar nome: uppercase e trim
            nome_normalizado = data['nome'].strip().upper() if data and data.get('nome') else ''  # type: ignore
            
            # Se o nome mudou, precisamos atualizar com atualizar_nome_categoria primeiro
            nome_original_normalizado = nome.strip().upper()
            
            print(f'   📝 Nome original normalizado: {nome_original_normalizado}')
            print(f'   📝 Nome novo normalizado: {nome_normalizado}')
            print(f'   🔄 Nome mudou? {nome_normalizado != nome_original_normalizado}')
            
            # Criar objeto categoria com os novos dados
            categoria = Categoria(
                nome=nome_normalizado,  # type: ignore
                tipo=TipoLancamento(tipo_str),  # type: ignore
                subcategorias=data.get('subcategorias', []) if data else [],  # type: ignore
                empresa_id=empresa_id  # type: ignore
            )
            
            print(f'   💾 Atualizando categoria: {categoria.nome} (tipo: {categoria.tipo.value}, empresa: {categoria.empresa_id})')
            print(f'   🔍 Usando nome_original para localizar: {nome_original_normalizado}')
            
            # Passar nome_original para a função UPDATE usar no WHERE
            success = db.atualizar_categoria(categoria, nome_original=nome_original_normalizado)
            
            print(f'   {"✅" if success else "❌"} Resultado: {success}')
            print('='*80 + '\n')
            
            return jsonify({'success': success})
        except Exception as e:
            import traceback
            print('   ❌ ERRO ao atualizar categoria:')
            traceback.print_exc()
            print('='*80 + '\n')
            
            error_msg = str(e)
            if 'UNIQUE constraint' in error_msg:
                error_msg = 'Já existe uma categoria com este nome'
            return jsonify({'success': False, 'error': error_msg}), 400
    
    elif request.method == 'DELETE':
        try:
            print('\n' + '='*80)
            print('🗑️ DELETE /api/categorias - EXCLUIR CATEGORIA')
            print(f'   📍 Nome (URL): {nome}')
            print(f'   🔑 CSRF Token no header: {request.headers.get("X-CSRFToken", "AUSENTE")}')
            print(f'   👤 Usuário: {session.get("usuario_id")}')
            print(f'   🏢 Empresa: {session.get("empresa_id")}')
            
            # Normalizar nome
            nome_normalizado = nome.strip().upper()
            print(f'   📝 Nome normalizado: {nome_normalizado}')
            
            success = db.excluir_categoria(nome)
            
            print(f'   {"✅" if success else "❌"} Resultado: {success}')
            print('='*80 + '\n')
            
            return jsonify({'success': success})
        except Exception as e:
            print('   ❌ ERRO ao excluir categoria:')
            print(f'   Mensagem: {str(e)}')
            import traceback
            traceback.print_exc()
            print('='*80 + '\n')
            
            return jsonify({'success': False, 'error': str(e)}), 400


# === IMPORTAÇÃO DE CATEGORIAS ENTRE EMPRESAS ===

@app.route('/api/categorias/empresas-disponiveis', methods=['GET'])
@require_permission('categorias_view')
def listar_empresas_com_categorias():
    """Lista empresas do usuário com suas categorias para importação"""
    try:
        usuario = get_usuario_logado()
        empresa_atual_id = session.get('empresa_id')
        
        print(f"\n🔍 [IMPORTAR CATEGORIAS] Buscando empresas disponíveis")
        print(f"   👤 Usuário: {usuario.get('nome')}")
        print(f"   🏢 Empresa atual: {empresa_atual_id}")
        
        # Buscar empresas do usuário
        from auth_functions import listar_empresas_usuario
        empresas = listar_empresas_usuario(usuario.get('id'), auth_db)
        print(f"   📊 Total de empresas do usuário: {len(empresas)}")
        
        empresas_com_categorias = []
        for empresa in empresas:
            empresa_id = empresa.get('empresa_id')
            razao_social = empresa.get('razao_social')
            
            print(f"\n   🔍 Analisando empresa: {razao_social} (ID: {empresa_id})")
            
            # Não listar a empresa atual
            if empresa_id == empresa_atual_id:
                print(f"      ⏭️ Pulando (é a empresa atual)")
                continue
            
            # Buscar categorias desta empresa
            categorias = db.listar_categorias(empresa_id=empresa_id)
            print(f"      📂 Categorias encontradas: {len(categorias)}")
            
            if categorias:  # Só incluir empresas que têm categorias
                categorias_list = []
                for cat in categorias:
                    # Verificar se é objeto ou dicionário
                    if hasattr(cat, 'nome'):
                        cat_dict = {
                            'nome': cat.nome,
                            'tipo': cat.tipo.value if hasattr(cat.tipo, 'value') else cat.tipo,
                            'subcategorias': cat.subcategorias if hasattr(cat, 'subcategorias') else []
                        }
                    else:
                        cat_dict = {
                            'nome': cat.get('nome', 'Sem nome'),
                            'tipo': cat.get('tipo', 'despesa'),
                            'subcategorias': cat.get('subcategorias', [])
                        }
                    categorias_list.append(cat_dict)
                
                empresas_com_categorias.append({
                    'empresa_id': empresa_id,
                    'razao_social': razao_social,
                    'total_categorias': len(categorias),
                    'categorias': categorias_list
                })
                print(f"      ✅ Empresa incluída com {len(categorias)} categoria(s)")
        
        print(f"\n✅ Total de empresas disponíveis para importação: {len(empresas_com_categorias)}")
        
        return jsonify({
            'success': True,
            'data': empresas_com_categorias
        })
        
    except Exception as e:
        print(f"❌ Erro ao listar empresas com categorias: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/categorias/importar-de-empresa', methods=['POST'])
@require_permission('categorias_create')
def importar_categorias_de_empresa():
    """Importa categorias de outra empresa do usuário"""
    print("\n" + "="*80)
    print("📥 IMPORTAR CATEGORIAS - INÍCIO")
    print("="*80)
    
    try:
        data = request.json
        empresa_origem_id = data.get('empresa_origem_id')
        categorias_ids = data.get('categorias')  # Lista de nomes de categorias para importar
        
        print(f"📋 Request data: {data}")
        print(f"🏢 Empresa origem: {empresa_origem_id}")
        print(f"📂 Categorias específicas: {categorias_ids}")
        
        if not empresa_origem_id:
            return jsonify({'success': False, 'error': 'empresa_origem_id é obrigatório'}), 400
        
        usuario = get_usuario_logado()
        empresa_destino_id = session.get('empresa_id')
        
        print(f"👤 Usuário: {usuario.get('nome')}")
        print(f"🎯 Empresa destino: {empresa_destino_id}")
        
        if not empresa_destino_id:
            return jsonify({'success': False, 'error': 'Empresa destino não identificada'}), 400
        
        # Verificar se usuário tem acesso à empresa origem
        from auth_functions import listar_empresas_usuario
        empresas_usuario = listar_empresas_usuario(usuario.get('id'), auth_db)
        tem_acesso = any(e.get('empresa_id') == empresa_origem_id for e in empresas_usuario)
        
        print(f"✅ Tem acesso à empresa origem? {tem_acesso}")
        
        if not tem_acesso:
            return jsonify({'success': False, 'error': 'Sem permissão para acessar empresa origem'}), 403
        
        # Buscar categorias da empresa origem
        categorias_origem = db.listar_categorias(empresa_id=empresa_origem_id)
        print(f"📦 Categorias da origem: {len(categorias_origem)}")
        for cat in categorias_origem:
            print(f"   - {cat.nome} ({cat.tipo.value if hasattr(cat.tipo, 'value') else cat.tipo})")
        
        # Filtrar categorias selecionadas (se especificado)
        if categorias_ids:
            categorias_origem = [c for c in categorias_origem if c.nome in categorias_ids]
            print(f"🔍 Após filtro: {len(categorias_origem)} categorias")
        
        # Buscar categorias já existentes na empresa destino
        categorias_destino = db.listar_categorias(empresa_id=empresa_destino_id)
        nomes_existentes = {c.nome.upper() for c in categorias_destino}
        print(f"📋 Categorias no destino: {len(categorias_destino)} ({nomes_existentes})")
        
        importadas = 0
        duplicadas = 0
        erros = []
        
        print(f"\n🔄 Iniciando loop de importação...")
        for cat_origem in categorias_origem:
            try:
                print(f"\n   📌 Processando: {cat_origem.nome}")
                
                # Verificar se já existe (case insensitive)
                if cat_origem.nome.upper() in nomes_existentes:
                    print(f"      ⏭️ Duplicada")
                    duplicadas += 1
                    continue
                
                print(f"      ✅ Nova categoria - criando...")
                
                # Criar nova categoria na empresa destino
                nova_categoria = Categoria(
                    nome=cat_origem.nome,
                    tipo=cat_origem.tipo,
                    descricao=getattr(cat_origem, 'descricao', ''),
                    subcategorias=getattr(cat_origem, 'subcategorias', []),
                    cor=getattr(cat_origem, 'cor', '#000000'),
                    icone=getattr(cat_origem, 'icone', 'folder'),
                    empresa_id=empresa_destino_id
                )
                
                print(f"      📝 Objeto Categoria criado: nome={nova_categoria.nome}, tipo={nova_categoria.tipo}, empresa_id={nova_categoria.empresa_id}")
                
                categoria_id = db.adicionar_categoria(nova_categoria)
                print(f"      ✅ Categoria adicionada com ID: {categoria_id}")
                importadas += 1
                
            except Exception as e:
                print(f"      ❌ ERRO ao processar {cat_origem.nome}: {e}")
                import traceback
                traceback.print_exc()
                erros.append(f"{cat_origem.nome}: {str(e)}")
        
        print(f"\n📊 RESULTADO:")
        print(f"   ✅ Importadas: {importadas}")
        print(f"   ⏭️ Duplicadas: {duplicadas}")
        print(f"   ❌ Erros: {len(erros)}")
        if erros:
            for erro in erros:
                print(f"      - {erro}")
        
        print("="*80)
        print("📥 IMPORTAR CATEGORIAS - FIM")
        print("="*80 + "\n")
        
        return jsonify({
            'success': True,
            'importadas': importadas,
            'duplicadas': duplicadas,
            'erros': erros,
            'message': f'{importadas} categoria(s) importada(s) com sucesso'
        })
        
    except Exception as e:
        print(f"❌ ERRO FATAL ao importar categorias: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# === ROTAS DE CLIENTES ===

@app.route('/api/clientes', methods=['GET'])
@require_permission('clientes_view')
@aplicar_filtro_cliente
def listar_clientes():
    """Lista clientes ativos ou inativos com filtro de multi-tenancy"""
    ativos = request.args.get('ativos', 'true').lower() == 'true'
    
    # ✅ CORREÇÃO: Usar filtro do decorator (empresa_id do usuário)
    # O decorator @aplicar_filtro_cliente seta request.filtro_cliente_id = empresa_id
    # As funções de DB agora filtram por empresa_id (não mais proprietario_id)
    filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
    
    usuario = get_usuario_logado()
    print(f"\n🔍 [GET /api/clientes]")
    print(f"   - ativos: {ativos}")
    print(f"   - usuario.id: {usuario.get('id') if usuario else None}")
    print(f"   - usuario.tipo: {usuario.get('tipo') if usuario else None}")
    print(f"   - empresa_id (via session): {session.get('empresa_id')}")
    print(f"   - filtro_cliente_id (empresa_id do decorator): {filtro_cliente_id}")
    
    clientes = db.listar_clientes(ativos=ativos, filtro_cliente_id=filtro_cliente_id)
    
    # Adicionar cliente_id para cada cliente (usando nome como identificador)
    for cliente in clientes:
        cliente['cliente_id'] = cliente.get('nome')
    
    return jsonify({
        'success': True,
        'data': clientes,
        'total': len(clientes),
        'message': 'Nenhum cliente cadastrado' if len(clientes) == 0 else None
    })


@app.route('/api/clientes', methods=['POST'])
@require_permission('clientes_create')
@aplicar_filtro_cliente
def adicionar_cliente():
    """Adiciona um novo cliente"""
    try:
        from flask import session
        from app.utils.validators import validate_cpf, validate_cnpj, validate_email
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        data = request.json
        
        # Validar campos obrigatórios
        if not data.get('nome'):
            return jsonify({'success': False, 'error': 'Nome do cliente é obrigatório'}), 400
        
        # 🔐 Validar CPF/CNPJ se fornecido
        if data.get('cpf_cnpj'):
            cpf_cnpj = data['cpf_cnpj'].strip()
            # Remover formatação para detectar se é CPF (11) ou CNPJ (14)
            import re
            numeros = re.sub(r'[^0-9]', '', cpf_cnpj)
            
            if len(numeros) == 11:
                is_valid, error_msg = validate_cpf(cpf_cnpj)
                if not is_valid:
                    return jsonify({'success': False, 'error': f'CPF inválido: {error_msg}'}), 400
            elif len(numeros) == 14:
                is_valid, error_msg = validate_cnpj(cpf_cnpj)
                if not is_valid:
                    return jsonify({'success': False, 'error': f'CNPJ inválido: {error_msg}'}), 400
            elif numeros:  # Se tem algum número mas não é 11 nem 14
                return jsonify({'success': False, 'error': 'CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos'}), 400
        
        # 🔐 Validar email se fornecido
        if data.get('email'):
            is_valid, error_msg = validate_email(data['email'])
            if not is_valid:
                return jsonify({'success': False, 'error': f'Email inválido: {error_msg}'}), 400
        
        # 🔒 Garantir que empresa_id está nos dados
        data['empresa_id'] = empresa_id
        
        # 🔒 Obter proprietario_id do usuário logado (ID na tabela usuarios)
        usuario = get_usuario_logado()
        proprietario_id = None
        if usuario and usuario.get('tipo') == 'cliente':
            proprietario_id = usuario.get('id')  # ID do usuário, NÃO empresa_id
        
        print(f"\n🔍 [POST /api/clientes] Adicionando cliente:")
        print(f"   - empresa_id: {empresa_id}")
        print(f"   - usuario.id: {usuario.get('id') if usuario else None}")
        print(f"   - usuario.tipo: {usuario.get('tipo') if usuario else None}")
        print(f"   - proprietario_id: {proprietario_id}")
        print(f"   - nome: {data.get('nome')}")
        
        cliente_id = db.adicionar_cliente(data, proprietario_id=proprietario_id)  # type: ignore
        print(f"   ✅ Cliente criado com ID: {cliente_id}")
        return jsonify({'success': True, 'id': cliente_id})
    except Exception as e:
        print(f"   ❌ Erro ao criar cliente: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/clientes/<path:nome>', methods=['GET'])
@require_permission('clientes_view')
@aplicar_filtro_cliente
def obter_cliente(nome):
    """Busca um cliente específico pelo nome"""
    try:
        # Decode do nome que vem URL-encoded
        from urllib.parse import unquote
        nome = unquote(nome)
        
        filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
        
        print(f"\n=== Buscando cliente ===")
        print(f"Nome: {nome}")
        print(f"Filtro cliente ID (empresa_id): {filtro_cliente_id}")
        
        cliente = db.obter_cliente_por_nome(nome)
        
        if not cliente:
            return jsonify({'success': False, 'error': 'Cliente não encontrado'}), 404
        
        # ✅ CORREÇÃO: Validar por empresa_id (não mais proprietario_id)
        # filtro_cliente_id contém o empresa_id do usuário logado
        if filtro_cliente_id is not None:
            cliente_empresa_id = cliente.get('empresa_id')
            if cliente_empresa_id != filtro_cliente_id:
                print(f"❌ Acesso negado: cliente.empresa_id={cliente_empresa_id}, filtro={filtro_cliente_id}")
                return jsonify({'success': False, 'error': 'Cliente não encontrado ou sem permissão'}), 403
        
        print(f"✅ Cliente encontrado: {cliente.get('nome')}")
        print(f"   - empresa_id: {cliente.get('empresa_id')}")
        print(f"   - cpf_cnpj: {cliente.get('cpf_cnpj')}")
        return jsonify(cliente)
    except Exception as e:
        print(f"❌ ERRO ao buscar cliente: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/clientes/<path:nome>', methods=['PUT', 'DELETE'])  # type: ignore
@require_permission('clientes_edit')
@aplicar_filtro_cliente
def modificar_cliente(nome):
    """Atualiza ou remove um cliente com validação de empresa"""
    # Decode do nome que vem URL-encoded
    from urllib.parse import unquote
    nome = unquote(nome)
    
    filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
    
    if request.method == 'PUT':
        try:
            from app.utils.validators import validate_cpf, validate_cnpj, validate_email
            import re
            
            data = request.json
            print(f"\n=== Atualizando cliente ===")
            print(f"URL recebida: {request.url}")
            print(f"Nome da URL (raw): '{nome}'")
            print(f"Dados recebidos: {data}")
            
            # 🔐 Validar CPF/CNPJ se fornecido
            if data.get('cpf_cnpj'):
                cpf_cnpj = data['cpf_cnpj'].strip()
                numeros = re.sub(r'[^0-9]', '', cpf_cnpj)
                
                if len(numeros) == 11:
                    is_valid, error_msg = validate_cpf(cpf_cnpj)
                    if not is_valid:
                        return jsonify({'success': False, 'error': f'CPF inválido: {error_msg}'}), 400
                elif len(numeros) == 14:
                    is_valid, error_msg = validate_cnpj(cpf_cnpj)
                    if not is_valid:
                        return jsonify({'success': False, 'error': f'CNPJ inválido: {error_msg}'}), 400
                elif numeros:
                    return jsonify({'success': False, 'error': 'CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos'}), 400
            
            # 🔐 Validar email se fornecido
            if data.get('email'):
                is_valid, error_msg = validate_email(data['email'])
                if not is_valid:
                    return jsonify({'success': False, 'error': f'Email inválido: {error_msg}'}), 400
            
            # Validar propriedade antes de atualizar (se não for admin)
            if filtro_cliente_id is not None:
                cliente_atual = db.obter_cliente_por_nome(nome)
                if not cliente_atual or cliente_atual.get('empresa_id') != filtro_cliente_id:
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
                if not cliente_atual or cliente_atual.get('empresa_id') != filtro_cliente_id:
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
    
    # ✅ CORREÇÃO: Usar filtro do decorator (empresa_id do usuário)
    # O decorator @aplicar_filtro_cliente seta request.filtro_cliente_id = empresa_id
    # As funções de DB agora filtram por empresa_id (não mais proprietario_id)
    filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
    
    fornecedores = db.listar_fornecedores(ativos=ativos, filtro_cliente_id=filtro_cliente_id)
    
    return jsonify({
        'success': True,
        'data': fornecedores,
        'total': len(fornecedores),
        'message': 'Nenhum fornecedor cadastrado' if len(fornecedores) == 0 else None
    })


@app.route('/api/fornecedores', methods=['POST'])
@require_permission('fornecedores_create')
@aplicar_filtro_cliente
def adicionar_fornecedor():
    """Adiciona um novo fornecedor"""
    try:
        from app.utils.validators import validate_cpf, validate_cnpj, validate_email
        import re
        
        # 🔒 VALIDAÇÃO DE SEGURANÇA
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.json
        
        # 🔒 Validar campo obrigatório
        if not data.get('nome'):
            return jsonify({'success': False, 'error': 'Nome do fornecedor é obrigatório'}), 400
        
        # 🔐 Validar CPF/CNPJ se fornecido
        if data.get('cpf_cnpj'):
            cpf_cnpj = data['cpf_cnpj'].strip()
            numeros = re.sub(r'[^0-9]', '', cpf_cnpj)
            
            if len(numeros) == 11:
                is_valid, error_msg = validate_cpf(cpf_cnpj)
                if not is_valid:
                    return jsonify({'success': False, 'error': f'CPF inválido: {error_msg}'}), 400
            elif len(numeros) == 14:
                is_valid, error_msg = validate_cnpj(cpf_cnpj)
                if not is_valid:
                    return jsonify({'success': False, 'error': f'CNPJ inválido: {error_msg}'}), 400
            elif numeros:
                return jsonify({'success': False, 'error': 'CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos'}), 400
        
        # 🔐 Validar email se fornecido
        if data.get('email'):
            is_valid, error_msg = validate_email(data['email'])
            if not is_valid:
                return jsonify({'success': False, 'error': f'Email inválido: {error_msg}'}), 400
        
        # 🔒 Adicionar empresa_id aos dados
        data['empresa_id'] = empresa_id
        
        # 🔒 Obter proprietario_id do usuário logado (ID na tabela usuarios)
        usuario = get_usuario_logado()
        proprietario_id = None
        if usuario and usuario.get('tipo') == 'cliente':
            proprietario_id = usuario.get('id')  # ID do usuário, NÃO empresa_id
        
        print(f"\n🔍 [POST /api/fornecedores]")
        print(f"   - empresa_id: {empresa_id}")
        print(f"   - usuario.id: {usuario.get('id') if usuario else None}")
        print(f"   - usuario.tipo: {usuario.get('tipo') if usuario else None}")
        print(f"   - proprietario_id: {proprietario_id}")
        print(f"   - nome: {data.get('nome')}")
        
        fornecedor_id = db.adicionar_fornecedor(data, proprietario_id=proprietario_id)  # type: ignore
        print(f"   ✅ Fornecedor criado com ID: {fornecedor_id}")
        return jsonify({'success': True, 'id': fornecedor_id})
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fornecedores/<path:nome>', methods=['GET'])
@require_permission('fornecedores_view')
@aplicar_filtro_cliente
def obter_fornecedor(nome):
    """Obtém dados de um fornecedor específico"""
    try:
        # Decode do nome que vem URL-encoded
        from urllib.parse import unquote
        nome = unquote(nome)
        
        filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
        
        print(f"\n=== Buscando fornecedor ===")
        print(f"Nome: {nome}")
        print(f"Filtro cliente ID (empresa_id): {filtro_cliente_id}")
        
        # Buscar fornecedor
        fornecedor = db.obter_fornecedor_por_nome(nome)
        
        if not fornecedor:
            return jsonify({'error': 'Fornecedor não encontrado'}), 404
        
        # ✅ CORREÇÃO: Validar por empresa_id (não mais proprietario_id)
        # filtro_cliente_id contém o empresa_id do usuário logado
        if filtro_cliente_id is not None:
            fornecedor_empresa_id = fornecedor.get('empresa_id')
            if fornecedor_empresa_id != filtro_cliente_id:
                print(f"❌ Acesso negado: fornecedor.empresa_id={fornecedor_empresa_id}, filtro={filtro_cliente_id}")
                return jsonify({'error': 'Sem permissão para visualizar este fornecedor'}), 403
        
        print(f"✅ Fornecedor encontrado: {fornecedor.get('nome')}")
        print(f"   - empresa_id: {fornecedor.get('empresa_id')}")
        print(f"   - cpf_cnpj: {fornecedor.get('cpf_cnpj')}")
        
        # Retornar dados completos do fornecedor
        return jsonify(fornecedor)
        
    except Exception as e:
        print(f"❌ ERRO ao obter fornecedor {nome}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/fornecedores/<path:nome>', methods=['PUT', 'DELETE'])  # type: ignore
@require_permission('fornecedores_edit')
@aplicar_filtro_cliente
def modificar_fornecedor(nome):
    """Atualiza ou remove um fornecedor com validação de empresa"""
    # Decode do nome que vem URL-encoded
    from urllib.parse import unquote
    nome = unquote(nome)
    
    filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
    
    if request.method == 'PUT':
        try:
            from app.utils.validators import validate_cpf, validate_cnpj, validate_email
            import re
            
            data = request.json
            
            # 🔐 Validar CPF/CNPJ se fornecido
            if data.get('cpf_cnpj'):
                cpf_cnpj = data['cpf_cnpj'].strip()
                numeros = re.sub(r'[^0-9]', '', cpf_cnpj)
                
                if len(numeros) == 11:
                    is_valid, error_msg = validate_cpf(cpf_cnpj)
                    if not is_valid:
                        return jsonify({'success': False, 'error': f'CPF inválido: {error_msg}'}), 400
                elif len(numeros) == 14:
                    is_valid, error_msg = validate_cnpj(cpf_cnpj)
                    if not is_valid:
                        return jsonify({'success': False, 'error': f'CNPJ inválido: {error_msg}'}), 400
                elif numeros:
                    return jsonify({'success': False, 'error': 'CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos'}), 400
            
            # 🔐 Validar email se fornecido
            if data.get('email'):
                is_valid, error_msg = validate_email(data['email'])
                if not is_valid:
                    return jsonify({'success': False, 'error': f'Email inválido: {error_msg}'}), 400
            
            # Validar propriedade antes de atualizar (se não for admin)
            if filtro_cliente_id is not None:
                fornecedor_atual = db.obter_fornecedor_por_nome(nome)
                if not fornecedor_atual or fornecedor_atual.get('empresa_id') != filtro_cliente_id:
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
                if not fornecedor_atual or fornecedor_atual.get('empresa_id') != filtro_cliente_id:
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
        # Decode do nome que vem URL-encoded
        from urllib.parse import unquote
        nome = unquote(nome)
        
        data = request.json or {}
        motivo = data.get('motivo', 'Inativado pelo usuário')
        
        success, mensagem = db.inativar_cliente(nome, motivo)
        return jsonify({'success': success, 'message': mensagem})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/clientes/<path:nome>/reativar', methods=['POST'])
@require_permission('clientes_edit')
def reativar_cliente(nome):
    """Reativa um cliente"""
    try:
        # Decode do nome que vem URL-encoded
        from urllib.parse import unquote
        nome = unquote(nome)
        
        success = db.reativar_cliente(nome)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fornecedores/<path:nome>/inativar', methods=['POST'])
@require_permission('fornecedores_edit')
def inativar_fornecedor(nome):
    """Inativa um fornecedor com motivo"""
    try:
        # Decode do nome que vem URL-encoded
        from urllib.parse import unquote
        nome = unquote(nome)
        
        data = request.json or {}
        motivo = data.get('motivo', 'Inativado pelo usuário')
        
        success, mensagem = db.inativar_fornecedor(nome, motivo)
        return jsonify({'success': success, 'message': mensagem})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fornecedores/<path:nome>/reativar', methods=['POST'])
@require_permission('fornecedores_edit')
def reativar_fornecedor(nome):
    """Reativa um fornecedor"""
    try:
        # Decode do nome que vem URL-encoded
        from urllib.parse import unquote
        nome = unquote(nome)
        
        success = db.reativar_fornecedor(nome)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# === ROTAS DE LANÇAMENTOS ===

@app.route('/api/lancamentos', methods=['GET'])
@require_permission('lancamentos_view')
@aplicar_filtro_cliente
def listar_lancamentos():
    """Lista todos os lançamentos com filtro de multi-tenancy e paginação"""
    try:
        print("\n" + "="*80)
        print("🚀 ROTA /api/lancamentos chamada")
        
        # Obter empresa_id da sessão
        empresa_id = session.get('empresa_id')
        
        # Parâmetros de filtro
        tipo_filtro = request.args.get('tipo')
        filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
        
        # Parâmetros de paginação
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', default=50, type=int)
        
        print(f"📋 Parâmetros recebidos:")
        print(f"   - empresa_id: {empresa_id}")
        print(f"   - tipo_filtro: {tipo_filtro}")
        print(f"   - filtro_cliente_id: {filtro_cliente_id}")
        print(f"   - page: {page}")
        print(f"   - per_page: {per_page}")
        
        # Criar dicionário de filtros
        filtros = {}
        if tipo_filtro:
            filtros['tipo'] = tipo_filtro.upper()
        
        print(f"🔍 Filtros montados: {filtros}")
        
        # Chamar método com todos os parâmetros
        print(f"📞 Chamando database.listar_lancamentos()...")
        lancamentos = database.listar_lancamentos(
            empresa_id=empresa_id,
            filtros=filtros,
            filtro_cliente_id=filtro_cliente_id,
            page=page,
            per_page=per_page
        )
        
        print(f"✅ Retornaram {len(lancamentos)} lançamentos")
        
        # Converter para lista de dicts
        lancamentos_list = []
        for idx, l in enumerate(lancamentos):
            try:
                item = {
                    'id': l.id if hasattr(l, 'id') else None,
                    'tipo': l.tipo.value if hasattr(l.tipo, 'value') else str(l.tipo),
                    'descricao': l.descricao,
                    'valor': float(l.valor),
                    'data_vencimento': l.data_vencimento.isoformat() if l.data_vencimento else None,
                    'data_pagamento': l.data_pagamento.isoformat() if l.data_pagamento else None,
                    'status': l.status.value if hasattr(l.status, 'value') else str(l.status),
                    'categoria': l.categoria,
                    'subcategoria': l.subcategoria,
                    'conta_bancaria': l.conta_bancaria,
                    'pessoa': l.pessoa,
                    'observacoes': l.observacoes,
                    'num_documento': getattr(l, 'num_documento', ''),
                    'associacao': getattr(l, 'associacao', ''),
                    'numero_documento': getattr(l, 'numero_documento', ''),
                    'recorrente': getattr(l, 'recorrente', False),
                    'frequencia_recorrencia': getattr(l, 'frequencia_recorrencia', ''),
                    'cliente_id': getattr(l, 'pessoa', None)
                }
                lancamentos_list.append(item)
            except Exception as e:
                print(f"⚠️ Erro ao converter lançamento {idx} (ID: {getattr(l, 'id', '?')}): {e}")
                continue
        
        print(f"📦 Retornando {len(lancamentos_list)} lançamentos no JSON")
        print("="*80 + "\n")
        
        return jsonify({
            'success': True,
            'data': lancamentos_list,
            'total': len(lancamentos_list),
            'message': 'Nenhum lançamento encontrado' if len(lancamentos_list) == 0 else None
        })
    except Exception as e:
        print(f"❌ ERRO CRÍTICO em listar_lancamentos: {e}")
        import traceback
        traceback.print_exc()
        print("="*80 + "\n")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/lancamentos', methods=['POST'])
@require_permission('lancamentos_create')
@aplicar_filtro_cliente
def adicionar_lancamento():
    """Adiciona um novo lançamento (com suporte a parcelamento)"""
    try:
        # 🔒 VALIDAÇÃO DE SEGURANÇA
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.json
        
        # 🔒 Obter proprietario_id do usuário logado (ID na tabela usuarios)
        usuario = get_usuario_logado()
        proprietario_id = None
        if usuario and usuario.get('tipo') == 'cliente':
            proprietario_id = usuario.get('id')  # ID do usuário, NÃO empresa_id
        
        print(f"\n🔍 [POST /api/lancamentos]")
        print(f"   - empresa_id: {empresa_id}")
        print(f"   - usuario.id: {usuario.get('id') if usuario else None}")
        print(f"   - usuario.tipo: {usuario.get('tipo') if usuario else None}")
        print(f"   - proprietario_id: {proprietario_id}")
        
        # Validar se a conta bancária está ativa
        if data and data.get('conta_bancaria'):
            conta_nome = data['conta_bancaria']
            contas = db.listar_contas_bancarias()
            conta = next((c for c in contas if c.nome == conta_nome), None)
            
            if conta:
                # Verificar se a conta está inativa
                if hasattr(conta, 'ativa') and not conta.ativa:
                    print(f"❌ Tentativa de criar lançamento em conta inativa: {conta_nome}")
                    return jsonify({
                        'success': False,
                        'error': f'Não é possível criar lançamento. A conta bancária "{conta_nome}" está inativa. Reative a conta antes de criar novos lançamentos.'
                    }), 400
        
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
                    subcategoria=data.get('subcategoria', '') if data else '',
                    associacao=data.get('associacao', '') if data else ''
                )
                
                if data and data.get('status'):
                    lancamento.status = StatusLancamento(data['status'])
                
                lancamento_id = db.adicionar_lancamento(lancamento, proprietario_id=proprietario_id, empresa_id=empresa_id)
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
                subcategoria=data.get('subcategoria', '') if data else '',
                associacao=data.get('associacao', '') if data else ''
            )
            
            if data and data.get('status'):
                lancamento.status = StatusLancamento(data['status'])
            
            lancamento_id = db.adicionar_lancamento(lancamento, proprietario_id=proprietario_id, empresa_id=empresa_id)
            return jsonify({'success': True, 'id': lancamento_id})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/lancamentos/<int:lancamento_id>', methods=['GET'])
@aplicar_filtro_cliente
@require_permission('lancamentos_view')
def obter_lancamento_route(lancamento_id):
    """Retorna os dados de um lançamento específico"""
    # 🔒 VALIDAÇÃO DE SEGURANÇA
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        print(f"\n{'='*80}")
        print(f"🔍 GET /api/lancamentos/{lancamento_id}")
        print(f"{'='*80}")
        
        lancamento = db_obter_lancamento(empresa_id=empresa_id, lancamento_id=lancamento_id)
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
                'desconto': float(getattr(lancamento, 'desconto', 0)),
                'associacao': getattr(lancamento, 'associacao', ''),
                'numero_documento': getattr(lancamento, 'numero_documento', '')
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
            print(f"🔍 CAMPO CRÍTICO - associacao recebido: '{data.get('associacao', '')}' (tipo: {type(data.get('associacao', ''))})")
            
            # 🔒 VALIDAÇÃO DE SEGURANÇA
            empresa_id = session.get('empresa_id')
            if not empresa_id:
                return jsonify({'erro': 'Empresa não selecionada'}), 403
            
            # Verificar se lançamento existe
            lancamento_atual = db_obter_lancamento(empresa_id=empresa_id, lancamento_id=lancamento_id)
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
                juros=juros_atual,
                desconto=desconto_atual,
                associacao=data.get('associacao', '')
            )
            
            print(f"✅ Objeto Lancamento criado:")
            print(f"   - ID: {lancamento_atualizado.id}")
            print(f"   - associacao: '{lancamento_atualizado.associacao}' (tipo: {type(lancamento_atualizado.associacao)})")
            
            # Atualizar no banco COM empresa_id para RLS
            success = db.atualizar_lancamento(lancamento_atualizado, empresa_id=empresa_id)
            
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
        print(f"\n{'='*60}")
        print(f"📤 UPLOAD DE EXTRATO OFX INICIADO")
        print(f"{'='*60}")
        
        # Log dos arquivos recebidos
        print(f"📋 Arquivos em request.files: {list(request.files.keys())}")
        print(f"📋 Dados em request.form: {dict(request.form)}")
        
        if 'file' not in request.files:
            print(f"❌ Erro: Nenhum arquivo enviado")
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        conta_bancaria = request.form.get('conta_bancaria')
        
        print(f"📁 Arquivo: {file.filename}")
        print(f"🏦 Conta bancária: {conta_bancaria}")
        
        if not conta_bancaria:
            print(f"❌ Erro: Conta bancária não informada")
            return jsonify({'success': False, 'error': 'Conta bancaria e obrigatoria'}), 400
        
        if file.filename == '':
            print(f"❌ Erro: Nome do arquivo vazio")
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        
        if not file.filename.lower().endswith('.ofx'):
            print(f"❌ Erro: Extensão inválida: {file.filename}")
            return jsonify({'success': False, 'error': 'Apenas arquivos .ofx sao permitidos'}), 400
        
        # Buscar informações da conta bancária cadastrada
        usuario = get_usuario_logado()
        
        # 🔒 SEGURANÇA MULTI-TENANT: Usar empresa_id da sessão (empresa selecionada)
        empresa_id = session.get('empresa_id')
        
        if not empresa_id:
            print(f"❌ Erro: Empresa não identificada na sessão")
            return jsonify({'success': False, 'error': 'Empresa não identificada. Faça login novamente.'}), 403
        
        print(f"🔒 EMPRESA ATUAL (sessão): {empresa_id}")
        print(f"📊 Transações serão salvas APENAS para empresa: {empresa_id}")
        
        # 🔒 Buscar APENAS contas da empresa atual (isolamento multi-tenant)
        from database_postgresql import DatabaseManager
        db_manager = DatabaseManager()
        
        try:
            contas_cadastradas = db_manager.listar_contas_por_empresa(empresa_id=empresa_id)
            print(f"📊 Total de contas da empresa {empresa_id}: {len(contas_cadastradas)}")
            print(f"📋 Nomes das contas: {[c.nome for c in contas_cadastradas]}")
        except Exception as e:
            print(f"❌ Erro ao buscar contas da empresa {empresa_id}: {e}")
            return jsonify({'success': False, 'error': f'Erro ao buscar contas bancárias: {str(e)}'}), 500
        
        conta_info = next((c for c in contas_cadastradas if c.nome == conta_bancaria), None)
        
        if not conta_info:
            print(f"❌ Erro: Conta '{conta_bancaria}' não encontrada na lista")
            return jsonify({'success': False, 'error': f'Conta bancária "{conta_bancaria}" não encontrada'}), 400
        
        print(f"✅ Conta encontrada: {conta_info.nome}")
        
        # Validar se a conta está ativa
        if hasattr(conta_info, 'ativa') and not conta_info.ativa:
            print(f"❌ Tentativa de importar extrato para conta inativa: {conta_bancaria}")
            return jsonify({
                'success': False,
                'error': f'Não é possível importar extrato. A conta bancária "{conta_bancaria}" está inativa. Reative a conta antes de importar extratos.'
            }), 400
        
        print(f"✅ Conta está ativa, prosseguindo com o upload...")
        
        # Parse OFX
        try:
            import ofxparse
            ofx = ofxparse.OfxParser.parse(file)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Erro ao processar OFX: {str(e)}'}), 400
        
        # Extrair transacoes
        transacoes = []
        for account in ofx.accounts:
            # Obter saldo final do OFX
            saldo_final = float(account.statement.balance) if hasattr(account.statement, 'balance') else None
            
            print(f"\n{'='*60}")
            print(f"📊 ANÁLISE DO ARQUIVO OFX")
            print(f"{'='*60}")
            print(f"🏦 Conta: {account.number if hasattr(account, 'number') else 'N/A'}")
            print(f"📅 Período: {account.statement.start_date} a {account.statement.end_date}")
            print(f"💰 Saldo Final (OFX): R$ {saldo_final:,.2f}" if saldo_final else "💰 Saldo Final: NÃO INFORMADO")
            print(f"📋 Total de transações: {len(account.statement.transactions)}")
            
            # Ordenar transações por data (mais antiga primeiro)
            transactions_list = sorted(account.statement.transactions, key=lambda t: t.date)
            
            # PRIMEIRO: processar transações para corrigir sinais
            transacoes_processadas = []
            for trans in transactions_list:
                valor_ofx = float(trans.amount)
                trans_type = getattr(trans, 'type', None)
                
                # Determinar tipo e corrigir sinal
                if trans_type:
                    if trans_type.upper() in ['DEBIT', 'DÉBITO', 'DEB', 'DEBIT', 'PAYMENT', 'ATM']:
                        tipo = 'debito'
                        valor_correto = -abs(valor_ofx)  # DÉBITO sempre negativo
                    else:
                        tipo = 'credito'
                        valor_correto = abs(valor_ofx)  # CRÉDITO sempre positivo
                else:
                    # Usar sinal do valor
                    if valor_ofx < 0:
                        tipo = 'debito'
                        valor_correto = valor_ofx  # Já é negativo
                    else:
                        tipo = 'credito'
                        valor_correto = valor_ofx  # Já é positivo
                
                transacoes_processadas.append({
                    'trans': trans,
                    'valor_ofx': valor_ofx,
                    'valor_correto': valor_correto,
                    'tipo': tipo
                })
            
            # Calcular saldo inicial baseado no saldo final e soma correta das transações
            # OU usar saldo_inicial da conta se data_inicio for anterior às transações
            if saldo_final is not None:
                soma_transacoes = sum(t['valor_correto'] for t in transacoes_processadas)
                saldo_inicial_calculado_ofx = saldo_final - soma_transacoes
                
                # Verificar se temos data_inicio configurada e se é anterior às transações
                data_primeira_transacao = transactions_list[0].date.date() if hasattr(transactions_list[0].date, 'date') else transactions_list[0].date
                
                usar_saldo_conta = False
                if hasattr(conta_info, 'data_inicio') and conta_info.data_inicio:
                    data_inicio_conta = conta_info.data_inicio.date() if hasattr(conta_info.data_inicio, 'date') else conta_info.data_inicio
                    
                    # Se data_inicio da conta for anterior ou igual à primeira transação, usar saldo_inicial da conta
                    if data_inicio_conta <= data_primeira_transacao:
                        usar_saldo_conta = True
                        saldo_atual = float(conta_info.saldo_inicial)
                        print(f"\n✅ USANDO SALDO INICIAL DA CONTA:")
                        print(f"   Data de início da conta: {data_inicio_conta}")
                        print(f"   Primeira transação OFX: {data_primeira_transacao}")
                        print(f"   Saldo inicial da conta: R$ {saldo_atual:,.2f}")
                        print(f"   (Saldo calculado pelo OFX seria: R$ {saldo_inicial_calculado_ofx:,.2f})")
                
                if not usar_saldo_conta:
                    saldo_atual = saldo_inicial_calculado_ofx
                    print(f"\n📊 CÁLCULOS (Saldo calculado pelo OFX):")
                    print(f"   Soma de todas transações (corrigida): R$ {soma_transacoes:+,.2f}")
                    print(f"   Saldo Final (OFX): R$ {saldo_final:,.2f}")
                    print(f"   Saldo Inicial calculado: R$ {saldo_inicial_calculado_ofx:,.2f}")
                    print(f"   Fórmula: {saldo_final:,.2f} - ({soma_transacoes:+,.2f}) = {saldo_inicial_calculado_ofx:,.2f}")
            else:
                print(f"\n⚠️ AVISO: Saldo final não informado no OFX")
                # Usar saldo_inicial da conta se disponível
                if hasattr(conta_info, 'saldo_inicial'):
                    saldo_atual = float(conta_info.saldo_inicial)
                    print(f"   Usando saldo inicial da conta: R$ {saldo_atual:,.2f}")
                else:
                    saldo_atual = 0
                    print(f"   Iniciando em R$ 0,00")
            
            print(f"\n📋 PROCESSANDO TRANSAÇÕES (cronológica):")
            print(f"{'Data':<12} {'Tipo':<15} {'Valor OFX':>15} {'Valor Correto':>15} {'Saldo Após':>15}")
            print(f"{'-'*72}")
            
            # Processar cada transação já calculada e atualizar saldo
            for t_proc in transacoes_processadas:
                trans = t_proc['trans']
                valor_ofx = t_proc['valor_ofx']
                valor_correto = t_proc['valor_correto']
                tipo = t_proc['tipo']
                
                # Atualizar saldo: saldo += valor (negativo diminui, positivo aumenta)
                saldo_atual += valor_correto
                
                data_str = str(trans.date.date() if hasattr(trans.date, 'date') else trans.date)
                tipo_label = '🔴 DÉBITO' if tipo == 'debito' else '🟢 CRÉDITO'
                print(f"{data_str:<12} {tipo_label:<15} {valor_ofx:>+15.2f} {valor_correto:>+15.2f} {saldo_atual:>15.2f}")
                
                transacoes.append({
                    'data': trans.date.date() if hasattr(trans.date, 'date') else trans.date,
                    'descricao': trans.payee or trans.memo or 'Sem descricao',
                    'valor': valor_correto,  # Guardar valor com sinal (negativo para débito, positivo para crédito)
                    'tipo': tipo.upper(),  # DEBITO ou CREDITO (maiúsculo)
                    'saldo': saldo_atual,  # Saldo após esta transação
                    'fitid': trans.id,
                    'memo': trans.memo,
                    'checknum': trans.checknum if hasattr(trans, 'checknum') else None
                })
        
        if not transacoes:
            return jsonify({'success': False, 'error': 'Nenhuma transacao encontrada no arquivo'}), 400
        
        # Salvar no banco (empresa_id já foi obtido no início da função)
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
        
        # Usar empresa_id da sessão (empresa selecionada pelo usuário)
        empresa_id = session.get('empresa_id') or usuario.get('cliente_id') or usuario.get('empresa_id') or 1
        
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
    """
    Concilia uma transacao do extrato com um lancamento
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    try:
        # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'erro': 'Empresa não selecionada'}), 403
        
        dados = request.json
        lancamento_id = dados.get('lancamento_id')
        
        # 🔒 Passar empresa_id explicitamente
        resultado = extrato_functions.conciliar_transacao(
            database,
            empresa_id,
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
        
        # 🔒 SEGURANÇA MULTI-TENANT: Usar empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
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
    """
    Deleta todas as transacoes de uma importacao
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    try:
        # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'erro': 'Empresa não selecionada'}), 403
        
        # 🔒 Passar empresa_id explicitamente
        resultado = extrato_functions.deletar_transacoes_extrato(
            database,
            empresa_id,
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
        
        # 🔒 SEGURANÇA MULTI-TENANT: Usar empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
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


print("🔧 Registrando rota: /api/extratos/conciliacao-geral")

@app.route('/api/extratos/conciliacao-geral', methods=['POST'])
@require_permission('lancamentos_create')
def conciliacao_geral_extrato():
    """Conciliação automática em massa de transações do extrato para contas a pagar/receber"""
    # Logs reduzidos para evitar poluição
    try:
        logger.info("🚀 CONCILIAÇÃO GERAL INICIADA")
        usuario = get_usuario_logado()
        
        # 🔒 SEGURANÇA MULTI-TENANT: Usar empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        logger.info(f"👤 Usuário: {usuario.get('username')} | Empresa ID: {empresa_id}")
        
        dados = request.json
        transacoes = dados.get('transacoes', [])
        print(f"📦 Recebidas {len(transacoes)} transação(ões) para conciliar")
        logger.info(f"📦 Recebidas {len(transacoes)} transação(ões) para conciliar")
        print(f"📋 Dados: {dados}")
        logger.info(f"📋 Dados recebidos: {dados}")
        
        if not transacoes:
            return jsonify({'success': False, 'error': 'Nenhuma transação selecionada'}), 400
        
        # Buscar clientes e fornecedores para matching de CPF/CNPJ
        clientes = db.listar_clientes(ativos=True)
        fornecedores = db.listar_fornecedores(ativos=True)
        
        # Criar dicionários de busca rápida por CPF/CNPJ
        clientes_dict = {}
        for cliente in clientes:
            cpf_cnpj = cliente.get('cpf') or cliente.get('cnpj')
            if cpf_cnpj:
                # Normalizar (remover pontos, traços, barras)
                cpf_cnpj_limpo = ''.join(filter(str.isdigit, str(cpf_cnpj)))
                clientes_dict[cpf_cnpj_limpo] = cliente['nome']
        
        fornecedores_dict = {}
        for fornecedor in fornecedores:
            cpf_cnpj = fornecedor.get('cpf') or fornecedor.get('cnpj')
            if cpf_cnpj:
                cpf_cnpj_limpo = ''.join(filter(str.isdigit, str(cpf_cnpj)))
                fornecedores_dict[cpf_cnpj_limpo] = fornecedor['nome']
        
        criados = 0
        erros = []
        
        for item in transacoes:
            try:
                transacao_id = item.get('transacao_id')
                categoria = item.get('categoria')
                subcategoria = item.get('subcategoria', '')
                razao_social = item.get('razao_social', '')
                descricao_personalizada = item.get('descricao', '')
                
                # Buscar transação do extrato
                with db.get_connection() as conn:
                    import psycopg2.extras
                    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                    cursor.execute(
                        "SELECT * FROM transacoes_extrato WHERE id = %s AND empresa_id = %s",
                        (transacao_id, empresa_id)
                    )
                    transacao = cursor.fetchone()
                    cursor.close()
                
                if not transacao:
                    erros.append(f"Transação {transacao_id} não encontrada")
                    continue
                
                # Validar se a conta bancária está ativa
                conta_bancaria = transacao['conta_bancaria']
                print(f"🔍 Validando conta bancária: {conta_bancaria}")
                contas = db.listar_contas_por_empresa(empresa_id=empresa_id)
                print(f"📊 Total de contas encontradas: {len(contas)}")
                
                # Debug: listar todas as contas
                for c in contas:
                    print(f"   - Conta cadastrada: '{c.nome}' (ativa={c.ativa if hasattr(c, 'ativa') else 'N/A'})")
                
                conta = next((c for c in contas if c.nome == conta_bancaria), None)
                
                if not conta:
                    erros.append(f"Transação {transacao_id}: A conta bancária '{conta_bancaria}' não está cadastrada no sistema ou o nome não corresponde exatamente. Verifique o cadastro de contas.")
                    print(f"❌ Conciliação bloqueada: conta '{conta_bancaria}' não encontrada")
                    logger.warning(f"❌ Tentativa de conciliar com conta não cadastrada: {conta_bancaria}")
                    continue
                
                print(f"✅ Conta encontrada: {conta.nome}")
                print(f"📊 Campo ativa existe? {hasattr(conta, 'ativa')}")
                print(f"📊 Valor do campo ativa: {conta.ativa if hasattr(conta, 'ativa') else 'N/A'}")
                
                if hasattr(conta, 'ativa') and not conta.ativa:
                    erros.append(f"Transação {transacao_id}: A conta bancária '{conta_bancaria}' está inativa. Reative a conta antes de conciliar.")
                    print(f"❌ Conciliação bloqueada: conta {conta_bancaria} está inativa")
                    logger.warning(f"❌ Tentativa de conciliar com conta inativa: {conta_bancaria}")
                    continue
                
                # Detectar CPF/CNPJ na descrição (regex simples)
                import re
                descricao = transacao['descricao']
                cpf_cnpj_encontrado = None
                
                # Buscar CPF (11 dígitos) ou CNPJ (14 dígitos)
                numeros = ''.join(filter(str.isdigit, descricao))
                if len(numeros) == 11 or len(numeros) == 14:
                    cpf_cnpj_encontrado = numeros
                
                # Tentar matching automático se não foi fornecida razão social
                if not razao_social and cpf_cnpj_encontrado:
                    if transacao['tipo'].upper() == 'CREDITO':
                        razao_social = clientes_dict.get(cpf_cnpj_encontrado, '')
                    else:
                        razao_social = fornecedores_dict.get(cpf_cnpj_encontrado, '')
                
                # Determinar tipo de lançamento
                tipo = TipoLancamento.RECEITA if transacao['tipo'].upper() == 'CREDITO' else TipoLancamento.DESPESA
                
                # Criar lançamento
                from datetime import datetime
                data_transacao = transacao['data']
                if isinstance(data_transacao, str):
                    data_transacao = datetime.fromisoformat(data_transacao.replace('Z', '+00:00')).date()
                
                # Transação do extrato já foi paga/recebida (já passou pelo banco)
                # Usar descrição personalizada se fornecida, senão usar a original do extrato
                descricao_final = descricao_personalizada if descricao_personalizada else descricao
                
                lancamento = Lancamento(
                    descricao=f"[EXTRATO] {descricao_final}",
                    valor=abs(float(transacao['valor'])),
                    tipo=tipo,
                    categoria=categoria,
                    subcategoria=subcategoria,
                    data_vencimento=data_transacao,
                    data_pagamento=data_transacao,  # PAGO - transação já aconteceu no banco
                    conta_bancaria=transacao['conta_bancaria'],
                    pessoa=razao_social,
                    observacoes=f"Conciliado do extrato bancário. ID Extrato: {transacao_id}",
                    status=StatusLancamento.PAGO  # PAGO porque já passou pelo banco
                )
                
                lancamento_id = db.adicionar_lancamento(lancamento, empresa_id=empresa_id)
                print(f"✅ Lançamento criado: ID={lancamento_id} para transação {transacao_id}")
                logger.info(f"✅ Lançamento criado: ID={lancamento_id} para transação {transacao_id}")
                
                # 🔥 FIX CRÍTICO: Usar conexão direta sem context manager
                # porque adicionar_lancamento já fez commit e devolveu ao pool
                print(f"🔄 Executando UPDATE: transacao_id={transacao_id}, lancamento_id={lancamento_id}")
                logger.info(f"🔄 Executando UPDATE em transacoes_extrato: transacao_id={transacao_id}, lancamento_id={lancamento_id}")
                conn_update = db.get_connection()
                cursor_update = conn_update.cursor()
                
                # Verificar se transação existe ANTES do UPDATE
                cursor_update.execute("SELECT id, conciliado, empresa_id FROM transacoes_extrato WHERE id = %s", (transacao_id,))
                trans_antes = cursor_update.fetchone()
                print(f"📊 ANTES UPDATE: {trans_antes}")
                logger.info(f"📊 Transação ANTES do UPDATE: {trans_antes}")
                
                cursor_update.execute(
                    "UPDATE transacoes_extrato SET conciliado = TRUE, lancamento_id = %s WHERE id = %s",
                    (lancamento_id, transacao_id)
                )
                affected_rows = cursor_update.rowcount
                print(f"📝 UPDATE: {affected_rows} linha(s) afetada(s)")
                logger.info(f"📝 UPDATE executado: {affected_rows} linha(s) afetada(s)")
                
                # Forçar commit explícito (mesmo com autocommit=True, garantir)
                try:
                    conn_update.commit()
                    print(f"✅ COMMIT OK")
                    logger.info(f"✅ COMMIT executado com sucesso")
                except Exception as commit_err:
                    print(f"⚠️ Erro no commit: {commit_err}")
                    logger.warning(f"⚠️ Erro no commit (pode ser normal com autocommit): {commit_err}")
                
                # Verificar se transação foi atualizada DEPOIS do UPDATE
                cursor_update.execute("SELECT id, conciliado, lancamento_id, empresa_id FROM transacoes_extrato WHERE id = %s", (transacao_id,))
                trans_depois = cursor_update.fetchone()
                print(f"📊 DEPOIS UPDATE: {trans_depois}")
                print("="*80 + "\n")
                logger.info(f"📊 Transação DEPOIS do UPDATE: {trans_depois}")
                
                cursor_update.close()
                from database_postgresql import return_to_pool
                return_to_pool(conn_update)
                
                criados += 1
                
            except Exception as e:
                erro_msg = f"Erro na transação {item.get('transacao_id')}: {str(e)}"
                print(f"❌ {erro_msg}")
                erros.append(erro_msg)
                logger.error(f"Erro ao conciliar transação {item.get('transacao_id')}: {e}")
                import traceback
                print(traceback.format_exc())
                traceback.print_exc()
        
        # Determinar status de sucesso
        success = criados > 0
        status_code = 200 if success else 400
        
        if not success and erros:
            # Se nenhuma transação foi conciliada e há erros, retornar erro
            return jsonify({
                'success': False,
                'criados': 0,
                'erros': erros,
                'message': erros[0] if len(erros) == 1 else f'{len(erros)} erro(s) encontrado(s)'
            }), 400
        
        return jsonify({
            'success': success,
            'criados': criados,
            'erros': erros,
            'message': f'{criados} lançamento(s) criado(s) com sucesso' + (f'. {len(erros)} erro(s).' if erros else '')
        }), status_code
        
    except Exception as e:
        logger.error(f"Erro na conciliação geral: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/extratos/<int:transacao_id>/desconciliar', methods=['POST'])
@require_permission('lancamentos_delete')
def desconciliar_extrato(transacao_id):
    """Desfaz a conciliação de uma transação do extrato e exclui o lançamento"""
    try:
        print("\n" + "="*80)
        print(f"🔙 DESCONCILIAÇÃO INICIADA - Transação ID: {transacao_id}")
        
        usuario = get_usuario_logado()
        
        # 🔒 SEGURANÇA MULTI-TENANT: Usar empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        # Buscar transação do extrato
        with db.get_connection() as conn:
            import psycopg2.extras
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                "SELECT * FROM transacoes_extrato WHERE id = %s AND empresa_id = %s",
                (transacao_id, empresa_id)
            )
            transacao = cursor.fetchone()
            cursor.close()
        
        if not transacao:
            return jsonify({'success': False, 'error': 'Transação não encontrada'}), 404
        
        if not transacao['conciliado']:
            return jsonify({'success': False, 'error': 'Transação não está conciliada'}), 400
        
        lancamento_id = transacao['lancamento_id']
        
        print(f"📌 Transação: ID={transacao_id}, Conciliado={transacao['conciliado']}, Lançamento ID={lancamento_id}")
        
        # Excluir lançamento se existir
        if lancamento_id:
            print(f"🗑️ Excluindo lançamento ID={lancamento_id}")
            db.excluir_lancamento(lancamento_id)
            print(f"✅ Lançamento {lancamento_id} excluído")
        
        # Atualizar transação: desconciliar
        conn_update = db.get_connection()
        cursor_update = conn_update.cursor()
        
        print(f"🔄 Desconciliando transação {transacao_id}")
        cursor_update.execute(
            "UPDATE transacoes_extrato SET conciliado = FALSE, lancamento_id = NULL WHERE id = %s",
            (transacao_id,)
        )
        affected_rows = cursor_update.rowcount
        print(f"📝 UPDATE executado: {affected_rows} linha(s) afetada(s)")
        
        try:
            conn_update.commit()
            print("✅ COMMIT OK")
        except Exception as commit_err:
            print(f"⚠️ Erro no commit: {commit_err}")
        
        cursor_update.close()
        from database_postgresql import return_to_pool
        return_to_pool(conn_update)
        
        print(f"✅ Desconciliação concluída com sucesso!")
        print("="*80 + "\n")
        
        return jsonify({
            'success': True,
            'message': 'Desconciliação realizada com sucesso'
        }), 200
        
    except Exception as e:
        print(f"❌ Erro na desconciliação: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROTAS DE REGRAS DE AUTO-CONCILIAÇÃO
# ============================================================================

@app.route('/api/regras-conciliacao', methods=['GET'])
@require_permission('regras_conciliacao_view')
def listar_regras_conciliacao():
    """Lista todas as regras de auto-conciliação da empresa"""
    try:
        print("🔍 [DEBUG] Iniciando listar_regras_conciliacao")
        
        empresa_id = session.get('empresa_id')
        print(f"🔍 [DEBUG] empresa_id: {empresa_id}")
        
        if not empresa_id:
            print("❌ [DEBUG] Empresa não selecionada")
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        print(f"🔍 [DEBUG] Chamando db.listar_regras_conciliacao(empresa_id={empresa_id})")
        regras = db.listar_regras_conciliacao(empresa_id=empresa_id)
        print(f"✅ [DEBUG] Regras retornadas: {len(regras) if regras else 0}")
        
        return jsonify({
            'success': True,
            'data': regras
        }), 200
        
    except Exception as e:
        print(f"❌ [DEBUG] ERRO: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Erro ao listar regras de conciliação: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/regras-conciliacao', methods=['POST'])
@require_permission('regras_conciliacao_create')
def criar_regra_conciliacao():
    """Cria nova regra de auto-conciliação"""
    try:
        print("🔍 [DEBUG] Iniciando criar_regra_conciliacao")
        
        empresa_id = session.get('empresa_id')
        print(f"🔍 [DEBUG] empresa_id: {empresa_id}")
        
        if not empresa_id:
            print("❌ [DEBUG] Empresa não selecionada")
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        dados = request.json
        print(f"🔍 [DEBUG] Dados recebidos: {dados}")
        
        # Validar campos obrigatórios
        if not dados.get('palavra_chave'):
            print("❌ [DEBUG] Palavra-chave não fornecida")
            return jsonify({'success': False, 'error': 'Palavra-chave é obrigatória'}), 400
        
        print(f"🔍 [DEBUG] Chamando db.criar_regra_conciliacao")
        regra = db.criar_regra_conciliacao(
            empresa_id=empresa_id,
            palavra_chave=dados.get('palavra_chave'),
            categoria=dados.get('categoria'),
            subcategoria=dados.get('subcategoria'),
            cliente_padrao=dados.get('cliente_padrao'),
            descricao=dados.get('descricao')
        )
        print(f"✅ [DEBUG] Regra criada: {regra}")
        
        return jsonify({
            'success': True,
            'message': 'Regra criada com sucesso',
            'data': regra
        }), 201
        
    except ValueError as e:
        # Erro de validação (ex: regra duplicada)
        print(f"⚠️ [DEBUG] ERRO DE VALIDAÇÃO: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
        
    except Exception as e:
        print(f"❌ [DEBUG] ERRO: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Erro ao criar regra de conciliação: {e}")
        return jsonify({'success': False, 'error': 'Erro interno ao criar regra'}), 500


@app.route('/api/regras-conciliacao/<int:regra_id>', methods=['PUT'])
@require_permission('regras_conciliacao_edit')
def atualizar_regra_conciliacao(regra_id):
    """Atualiza uma regra de auto-conciliação"""
    try:
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        dados = request.json
        
        sucesso = db.atualizar_regra_conciliacao(
            regra_id=regra_id,
            empresa_id=empresa_id,
            **dados
        )
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': 'Regra atualizada com sucesso'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Regra não encontrada ou sem permissão'}), 404
        
    except Exception as e:
        logger.error(f"Erro ao atualizar regra de conciliação: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/regras-conciliacao/<int:regra_id>', methods=['DELETE'])
@require_permission('regras_conciliacao_delete')
def excluir_regra_conciliacao(regra_id):
    """Exclui uma regra de auto-conciliação"""
    try:
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        sucesso = db.excluir_regra_conciliacao(
            regra_id=regra_id,
            empresa_id=empresa_id
        )
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': 'Regra excluída com sucesso'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Regra não encontrada ou sem permissão'}), 404
        
    except Exception as e:
        logger.error(f"Erro ao excluir regra de conciliação: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# CONFIGURAÇÕES DE EXTRATO BANCÁRIO
# ============================================================================

@app.route('/api/config-extrato', methods=['GET'])
@require_permission('config_extrato_bancario_view')
def obter_config_extrato():
    """
    Obtém configurações de extrato bancário da empresa
    """
    try:
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        config = db.obter_config_extrato(empresa_id)
        
        return jsonify({
            'success': True,
            'data': config
        }), 200
    except Exception as e:
        logger.error(f"Erro ao obter configuração de extrato: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config-extrato', methods=['PUT'])
@require_permission('config_extrato_bancario_edit')
def atualizar_config_extrato():
    """
    Atualiza configurações de extrato bancário
    """
    try:
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        dados = request.json
        integrar_folha = dados.get('integrar_folha_pagamento', False)
        
        sucesso = db.atualizar_config_extrato(
            empresa_id=empresa_id,
            integrar_folha=integrar_folha
        )
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': 'Configuração atualizada com sucesso'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Erro ao atualizar configuração'}), 500
    except Exception as e:
        logger.error(f"Erro ao atualizar configuração de extrato: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/regras-conciliacao/detectar', methods=['POST'])
@require_permission('lancamentos_view')
def detectar_regra_conciliacao():
    """
    Detecta regra aplicável e funcionário (se integração folha ativa)
    para uma descrição de extrato
    """
    try:
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        dados = request.json
        descricao = dados.get('descricao', '')
        
        if not descricao:
            return jsonify({'success': False, 'error': 'Descrição é obrigatória'}), 400
        
        # Buscar regra aplicável
        regra = db.buscar_regra_aplicavel(empresa_id=empresa_id, descricao=descricao)
        
        resultado = {
            'success': True,
            'regra_encontrada': regra is not None,
            'regra': regra,
            'funcionario': None
        }
        
        # Se regra tem integração com folha, buscar CPF na descrição
        if regra and regra.get('usa_integracao_folha'):
            import re
            # Buscar CPF na descrição (11 dígitos consecutivos)
            cpf_match = re.search(r'\b(\d{11})\b', descricao)
            
            if cpf_match:
                cpf = cpf_match.group(1)
                funcionario = db.buscar_funcionario_por_cpf(empresa_id=empresa_id, cpf=cpf)
                
                if funcionario:
                    resultado['funcionario'] = {
                        'nome': funcionario.get('nome'),
                        'cpf': funcionario.get('cpf'),
                        'cargo': funcionario.get('cargo')
                    }
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Erro ao detectar regra de conciliação: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# === ROTAS DE FOLHA DE PAGAMENTO (FUNCIONÁRIOS) ===

@app.route('/api/funcionarios', methods=['GET'])
@require_permission('folha_pagamento_view')
def listar_funcionarios():
    """Listar todos os funcionários da empresa"""
    try:
        print("\n🔍 [FUNCIONARIOS GET] Iniciando...")
        usuario = get_usuario_logado()
        print(f"   Usuario logado: {usuario.get('username') if usuario else 'NENHUM'}")
        
        if not usuario:
            print("❌ [FUNCIONARIOS GET] Usuario não autenticado!")
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        logger.info(f"🔍 [FUNCIONARIOS] Usuario: {usuario.get('username')}")
        logger.info(f"   cliente_id: {usuario.get('cliente_id')}")
        logger.info(f"   empresa_id: {usuario.get('empresa_id')}")
        logger.info(f"   empresas: {usuario.get('empresas', [])}")
        
        # 🔒 SEGURANÇA MULTI-TENANT: Usar empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 403
        logger.info(f"   ➡️ empresa_id final: {empresa_id}")
        
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT id, empresa_id, nome, cpf, email, celular, ativo, data_admissao, 
                   data_demissao, observacoes, nacionalidade, estado_civil, data_nascimento, 
                   idade, profissao, rua_av, numero_residencia, complemento, bairro, cidade, 
                   estado, cep, chave_pix, pis_pasep, data_criacao, data_atualizacao
            FROM funcionarios
            WHERE empresa_id = %s
            ORDER BY nome ASC
        """
        
        logger.info(f"🔍 [FUNCIONARIOS] Executando query com empresa_id = {empresa_id}")
        cursor.execute(query, (empresa_id,))
        rows = cursor.fetchall()
        logger.info(f"✅ [FUNCIONARIOS] Encontrados {len(rows)} funcionários")
        
        # Debug: Log primeiro funcionário
        if rows:
            logger.info(f"📊 [DEBUG] Primeiro funcionário (tipo: {type(rows[0])})")
            if isinstance(rows[0], dict):
                logger.info(f"   Dict keys: {list(rows[0].keys())}")
            else:
                logger.info(f"   Tupla length: {len(rows[0])}")
        
        cursor.close()
        
        funcionarios = []
        for row in rows:
            # Verifica se row é dict ou tupla
            if isinstance(row, dict):
                funcionarios.append({
                    'id': row['id'],
                    'empresa_id': row['empresa_id'],
                    'nome': row['nome'],
                    'cpf': row.get('cpf'),
                    'email': row.get('email'),
                    'celular': row.get('celular'),
                    'ativo': row.get('ativo', True),
                    'data_admissao': row['data_admissao'].isoformat() if row.get('data_admissao') else None,
                    'data_demissao': row['data_demissao'].isoformat() if row.get('data_demissao') else None,
                    'observacoes': row.get('observacoes'),
                    'nacionalidade': row.get('nacionalidade'),
                    'estado_civil': row.get('estado_civil'),
                    'data_nascimento': row['data_nascimento'].isoformat() if row.get('data_nascimento') else None,
                    'idade': row.get('idade'),
                    'profissao': row.get('profissao'),
                    'rua_av': row.get('rua_av'),
                    'numero_residencia': row.get('numero_residencia'),
                    'complemento': row.get('complemento'),
                    'bairro': row.get('bairro'),
                    'cidade': row.get('cidade'),
                    'estado': row.get('estado'),
                    'cep': row.get('cep'),
                    'chave_pix': row.get('chave_pix'),
                    'pis_pasep': row.get('pis_pasep'),
                    'data_criacao': row['data_criacao'].isoformat() if row.get('data_criacao') else None,
                    'data_atualizacao': row['data_atualizacao'].isoformat() if row.get('data_atualizacao') else None
                })
            else:
                funcionarios.append({
                    'id': row[0],
                    'empresa_id': row[1],
                    'nome': row[2],
                    'cpf': row[3],
                    'email': row[4],
                    'celular': row[5],
                    'ativo': row[6] if row[6] is not None else True,
                    'data_admissao': row[7].isoformat() if row[7] else None,
                    'data_demissao': row[8].isoformat() if row[8] else None,
                    'observacoes': row[9],
                    'nacionalidade': row[10],
                    'estado_civil': row[11],
                    'data_nascimento': row[12].isoformat() if row[12] else None,
                    'idade': row[13],
                    'profissao': row[14],
                    'rua_av': row[15],
                    'numero_residencia': row[16],
                    'complemento': row[17],
                    'bairro': row[18],
                    'cidade': row[19],
                    'estado': row[20],
                    'cep': row[21],
                    'chave_pix': row[22],
                    'pis_pasep': row[23],
                    'data_criacao': row[24].isoformat() if row[24] else None,
                    'data_atualizacao': row[25].isoformat() if row[25] else None
                })
        
        # Log primeiro funcionário completo para debug
        if funcionarios:
            logger.info(f"📤 [DEBUG] Primeiro funcionário sendo enviado:")
            logger.info(f"   Nome: {funcionarios[0].get('nome')}")
            logger.info(f"   CPF: {funcionarios[0].get('cpf')}")
            logger.info(f"   Nacionalidade: {funcionarios[0].get('nacionalidade')}")
            logger.info(f"   Estado Civil: {funcionarios[0].get('estado_civil')}")
            logger.info(f"   Email: {funcionarios[0].get('email')}")
        
        return jsonify({'funcionarios': funcionarios}), 200
    
    except Exception as e:
        logger.error(f"Erro ao listar funcionários: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/funcionarios/cpf/relatorio', methods=['GET'])
@require_permission('folha_pagamento_view')
def relatorio_cpfs_invalidos():
    """
    🔐 Relatório de CPFs Inválidos
    ================================
    
    Retorna lista de funcionários com CPFs inválidos ou ausentes.
    
    Resposta:
        - total_funcionarios: total de funcionários da empresa
        - total_cpfs_invalidos: quantidade de CPFs inválidos
        - total_cpfs_ausentes: quantidade de CPFs não informados
        - taxa_erro: percentual de erros (%)
        - funcionarios_invalidos: lista detalhada com erros
    """
    # Import local para evitar falha de carregamento do módulo
    from cpf_validator import CPFValidator
    
    try:
        print("\n🔍 [CPF RELATORIO] Iniciando análise...")
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 403
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Buscar todos os funcionários da empresa
        query = """
            SELECT id, nome, cpf, email, celular, ativo, data_admissao, data_demissao
            FROM funcionarios
            WHERE empresa_id = %s
            ORDER BY nome ASC
        """
        
        cursor.execute(query, (empresa_id,))
        rows = cursor.fetchall()
        cursor.close()
        
        # Análise de CPFs
        total_funcionarios = len(rows)
        funcionarios_invalidos = []
        funcionarios_ausentes = []
        
        for row in rows:
            if isinstance(row, dict):
                func_id = row['id']
                nome = row['nome']
                cpf = row.get('cpf')
                email = row.get('email')
                celular = row.get('celular')
                ativo = row.get('ativo', True)
                data_admissao = row['data_admissao'].isoformat() if row.get('data_admissao') else None
                data_demissao = row['data_demissao'].isoformat() if row.get('data_demissao') else None
            else:
                func_id, nome, cpf, email, celular, ativo, data_admissao, data_demissao = row[:8]
                data_admissao = data_admissao.isoformat() if data_admissao else None
                data_demissao = data_demissao.isoformat() if data_demissao else None
            
            # Validar CPF
            if not cpf or cpf.strip() == '':
                funcionarios_ausentes.append({
                    'id': func_id,
                    'nome': nome,
                    'cpf': None,
                    'email': email,
                    'celular': celular,
                    'ativo': ativo,
                    'data_admissao': data_admissao,
                    'data_demissao': data_demissao,
                    'erro': 'CPF não informado',
                    'tipo_erro': 'ausente'
                })
            else:
                validacao = CPFValidator.validar_com_detalhes(cpf)
                if not validacao['valido']:
                    funcionarios_invalidos.append({
                        'id': func_id,
                        'nome': nome,
                        'cpf': cpf,
                        'cpf_formatado': CPFValidator.formatar(cpf) if len(CPFValidator.limpar(cpf)) == 11 else cpf,
                        'email': email,
                        'celular': celular,
                        'ativo': ativo,
                        'data_admissao': data_admissao,
                        'data_demissao': data_demissao,
                        'erro': validacao['erro'],
                        'tipo_erro': 'invalido'
                    })
        
        # Calcular estatísticas
        total_invalidos = len(funcionarios_invalidos)
        total_ausentes = len(funcionarios_ausentes)
        total_problemas = total_invalidos + total_ausentes
        taxa_erro = round((total_problemas / total_funcionarios * 100), 2) if total_funcionarios > 0 else 0
        taxa_validos = round(((total_funcionarios - total_problemas) / total_funcionarios * 100), 2) if total_funcionarios > 0 else 0
        
        # Combinar listas
        todos_problemas = funcionarios_invalidos + funcionarios_ausentes
        
        print(f"✅ [CPF RELATORIO] Análise concluída:")
        print(f"   Total: {total_funcionarios} funcionários")
        print(f"   Inválidos: {total_invalidos}")
        print(f"   Ausentes: {total_ausentes}")
        print(f"   Taxa de erro: {taxa_erro}%")
        
        return jsonify({
            'success': True,
            'total_funcionarios': total_funcionarios,
            'total_cpfs_validos': total_funcionarios - total_problemas,
            'total_cpfs_invalidos': total_invalidos,
            'total_cpfs_ausentes': total_ausentes,
            'total_cpfs_problemas': total_problemas,
            'taxa_erro': taxa_erro,
            'taxa_validos': taxa_validos,
            'funcionarios_com_problemas': todos_problemas,
            'data_analise': time.strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar relatório de CPFs: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/funcionarios/cpf/correcao', methods=['GET'])
@require_permission('folha_pagamento_edit')
def gerar_correcoes_cpf():
    """Gera sugestões de correção automática para CPFs inválidos"""
    import traceback
    import sys
    
    # IMPORTAR MÓDULOS CPF DENTRO DA FUNÇÃO (para debug)
    try:
        logger.info("🔧 [CPF] Importando CPFValidator...")
        from cpf_validator import CPFValidator as CPFVal
        logger.info("✅ [CPF] CPFValidator importado com sucesso")
    except Exception as import_error:
        logger.error(f"❌ [CPF] ERRO AO IMPORTAR CPFValidator: {import_error}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Erro ao importar CPFValidator: {str(import_error)}',
            'traceback': traceback.format_exc()
        }), 500
    
    try:
        logger.info("🔧 [CPF] Importando CPFCorrector...")
        from cpf_corrector import CPFCorrector as CPFCorr
        logger.info("✅ [CPF] CPFCorrector importado com sucesso")
    except Exception as import_error:
        logger.error(f"❌ [CPF] ERRO AO IMPORTAR CPFCorrector: {import_error}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Erro ao importar CPFCorrector: {str(import_error)}',
            'traceback': traceback.format_exc()
        }), 500
    
    try:
        logger.info("=" * 80)
        logger.info("🔧 [CPF CORRETOR] === INÍCIO DA EXECUÇÃO ===")
        logger.info("=" * 80)
        
        # Obter empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            logger.error("❌ [CPF CORRETOR] Empresa não selecionada")
            return jsonify({'error': 'Empresa não selecionada'}), 403
        
        logger.info(f"✅ [CPF CORRETOR] Empresa ID: {empresa_id}")
        
        # Buscar funcionários da empresa
        conn = None
        cursor = None
        try:
            logger.info("🔧 [CPF CORRETOR] Conectando ao banco de dados...")
            conn = db.get_connection()
            cursor = conn.cursor()
            
            logger.info("🔧 [CPF CORRETOR] Executando query...")
            query = """
                SELECT id, nome, cpf
                FROM funcionarios
                WHERE empresa_id = %s
                ORDER BY nome ASC
            """
            
            cursor.execute(query, (empresa_id,))
            rows = cursor.fetchall()
            
            logger.info(f"✅ [CPF CORRETOR] Encontrados {len(rows)} funcionários no banco")
            
        except Exception as db_error:
            logger.error(f"❌ [CPF CORRETOR] Erro na consulta ao banco: {db_error}")
            logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': f'Erro ao acessar banco de dados: {str(db_error)}'
            }), 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            logger.info("🔧 [CPF CORRETOR] Conexão com banco fechada")
        
        # Converter para lista de dicionários
        logger.info("🔧 [CPF CORRETOR] Convertendo dados...")
        funcionarios = []
        for row in rows:
            funcionarios.append({
                'id': row['id'],
                'nome': row['nome'],
                'cpf': row['cpf'] or ''
            })
        
        logger.info(f"✅ [CPF CORRETOR] {len(funcionarios)} funcionários convertidos")
        
        # Filtrar apenas funcionários com CPF inválido
        logger.info("🔧 [CPF CORRETOR] Iniciando validação de CPFs...")
        funcionarios_invalidos = []
        
        for i, func in enumerate(funcionarios):
            cpf = func.get('cpf', '')
            
            if not cpf:
                continue
                
            try:
                is_valid = CPFVal.validar(cpf)
                if not is_valid:
                    funcionarios_invalidos.append(func)
                    if len(funcionarios_invalidos) <= 5:  # Log apenas os 5 primeiros
                        logger.info(f"   ❌ CPF inválido [{i+1}]: {func['nome'][:30]} - '{cpf}'")
            except Exception as val_error:
                logger.error(f"❌ [CPF CORRETOR] Erro ao validar CPF de {func['nome']}: {val_error}")
                logger.error(traceback.format_exc())
        
        logger.info(f"✅ [CPF CORRETOR] Validação concluída: {len(funcionarios_invalidos)} CPFs inválidos")
        
        # Se não há funcionários com CPF inválido, retornar resultado vazio
        if len(funcionarios_invalidos) == 0:
            logger.info("✅ [CPF CORRETOR] Nenhum CPF inválido - retornando sucesso")
            return jsonify({
                'success': True,
                'total_funcionarios': len(funcionarios),
                'total_cpfs_invalidos': 0,
                'total_corrigidos': 0,
                'total_nao_corrigidos': 0,
                'taxa_correcao': 0,
                'correcoes_por_tipo': {},
                'correcoes_sugeridas': []
            })
        
        # Aplicar correção automática
        logger.info("🔧 [CPF CORRETOR] Iniciando correção automática...")
        try:
            resultado_correcao = CPFCorr.corrigir_lista_funcionarios(funcionarios_invalidos)
            logger.info(f"✅ [CPF CORRETOR] Correção concluída: {resultado_correcao['total_corrigidos']}/{len(funcionarios_invalidos)}")
        except Exception as corrector_error:
            logger.error(f"❌ [CPF CORRETOR] ERRO NO CORRETOR: {corrector_error}")
            logger.error(f"Tipo do erro: {type(corrector_error).__name__}")
            logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': f'Erro no sistema de correção: {str(corrector_error)}',
                'error_type': type(corrector_error).__name__,
                'traceback': traceback.format_exc()
            }), 500
        
        # Preparar resposta
        logger.info("🔧 [CPF CORRETOR] Preparando resposta...")
        resposta = {
            'success': True,
            'total_funcionarios': len(funcionarios),
            'total_cpfs_invalidos': len(funcionarios_invalidos),
            'total_corrigidos': resultado_correcao['total_corrigidos'],
            'total_nao_corrigidos': resultado_correcao['total_nao_corrigidos'],
            'taxa_correcao': round(resultado_correcao['total_corrigidos'] / len(funcionarios_invalidos) * 100, 1) if funcionarios_invalidos else 0,
            'correcoes_por_tipo': resultado_correcao['correcoes_por_tipo'],
            'correcoes_sugeridas': resultado_correcao['correcoes_sugeridas']
        }
        
        logger.info(f"✅ [CPF CORRETOR] === CONCLUSÃO: {resultado_correcao['total_corrigidos']} correções ===")
        logger.info("=" * 80)
        
        return jsonify(resposta)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌❌❌ [CPF CORRETOR] ERRO CRÍTICO NÃO TRATADO: {e}")
        logger.error(f"Tipo do erro: {type(e).__name__}")
        logger.error(f"Args: {e.args}")
        logger.error("TRACEBACK COMPLETO:")
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        
        # Print para stderr também
        print("=" * 80, file=sys.stderr)
        print(f"ERRO CRÍTICO CPF CORRETOR: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        
        return jsonify({
            'success': False, 
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/funcionarios/cpf/ping', methods=['GET'])
def ping_cpf_correcao():
    """Endpoint de teste puro - sem decorator, sem dependências"""
    return jsonify({
        'success': True,
        'message': 'Endpoint CPF funcionando',
        'timestamp': str(datetime.now())
    })


@app.route('/api/funcionarios/cpf/corrigir-lote', methods=['PUT'])
@require_permission('folha_pagamento_edit')
def corrigir_cpf_lote():
    """
    🚀 Correção em Lote de CPFs
    ============================
    
    Aplica correções de CPF em múltiplos funcionários de uma vez.
    Evita problemas de rate limit e melhora performance.
    
    Body:
        {
            "correcoes": [
                {"funcionario_id": 123, "cpf": "12345678901"},
                {"funcionario_id": 456, "cpf": "98765432100"}
            ]
        }
    
    Resposta:
        {
            "success": true,
            "total_processados": 2,
            "total_sucesso": 2,
            "total_falhas": 0,
            "resultados": [...]
        }
    """
    from cpf_validator import CPFValidator
    
    try:
        dados = request.get_json()
        correcoes = dados.get('correcoes', [])
        
        if not correcoes or not isinstance(correcoes, list):
            return jsonify({'error': 'Lista de correções não informada'}), 400
        
        if len(correcoes) > 500:
            return jsonify({'error': 'Máximo de 500 correções por lote'}), 400
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não selecionada'}), 403
        
        logger.info(f"🔧 [LOTE CPF] Processando {len(correcoes)} correções para empresa {empresa_id}")
        
        resultados = []
        total_sucesso = 0
        total_falhas = 0
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            for i, correcao in enumerate(correcoes):
                funcionario_id = correcao.get('funcionario_id')
                novo_cpf = correcao.get('cpf', '').strip()
                
                if not funcionario_id or not novo_cpf:
                    resultados.append({
                        'funcionario_id': funcionario_id,
                        'success': False,
                        'error': 'Dados incompletos'
                    })
                    total_falhas += 1
                    continue
                
                # Validar novo CPF
                validacao = CPFValidator.validar_com_detalhes(novo_cpf)
                if not validacao['valido']:
                    resultados.append({
                        'funcionario_id': funcionario_id,
                        'success': False,
                        'error': f'CPF inválido: {validacao["erro"]}'
                    })
                    total_falhas += 1
                    continue
                
                # Atualizar CPF no banco
                cpf_limpo = CPFValidator.limpar(novo_cpf)
                
                cursor.execute("""
                    UPDATE funcionarios 
                    SET cpf = %s, data_atualizacao = CURRENT_TIMESTAMP
                    WHERE id = %s AND empresa_id = %s
                """, (cpf_limpo, funcionario_id, empresa_id))
                
                if cursor.rowcount > 0:
                    resultados.append({
                        'funcionario_id': funcionario_id,
                        'success': True,
                        'cpf_atualizado': CPFValidator.formatar(cpf_limpo)
                    })
                    total_sucesso += 1
                else:
                    resultados.append({
                        'funcionario_id': funcionario_id,
                        'success': False,
                        'error': 'Funcionário não encontrado ou sem permissão'
                    })
                    total_falhas += 1
                
                # Log a cada 50 correções
                if (i + 1) % 50 == 0:
                    logger.info(f"✅ [LOTE CPF] Processados {i + 1}/{len(correcoes)}")
            
            conn.commit()
            logger.info(f"✅ [LOTE CPF] Concluído: {total_sucesso} sucesso, {total_falhas} falhas")
            
            return jsonify({
                'success': True,
                'total_processados': len(correcoes),
                'total_sucesso': total_sucesso,
                'total_falhas': total_falhas,
                'resultados': resultados
            })
            
        except Exception as db_error:
            conn.rollback()
            logger.error(f"❌ [LOTE CPF] Erro no banco: {db_error}")
            raise db_error
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        logger.error(f"❌ [LOTE CPF] Erro geral: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/funcionarios/<int:funcionario_id>/cpf', methods=['PUT'])
@require_permission('folha_pagamento_edit')
def corrigir_cpf_funcionario(funcionario_id):
    """Aplica correção de CPF em um funcionário específico"""
    # Import local para evitar falha de carregamento do módulo
    from cpf_validator import CPFValidator
    
    try:
        dados = request.get_json()
        novo_cpf = dados.get('cpf', '').strip()
        
        if not novo_cpf:
            return jsonify({'error': 'CPF não informado'}), 400
        
        # Validar novo CPF
        validacao = CPFValidator.validar_com_detalhes(novo_cpf)
        if not validacao['valido']:
            return jsonify({'error': f'CPF inválido: {validacao["erro"]}'}), 400
        
        # Obter empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não selecionada'}), 403
        
        # Atualizar CPF no banco
        cpf_formatado = validacao['cpf_formatado']
        
        # Fazer update direto no banco
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE funcionarios 
            SET cpf = %s, 
                data_atualizacao = CURRENT_TIMESTAMP
            WHERE id = %s 
              AND empresa_id = %s
              AND ativo = TRUE
        """, (cpf_formatado, funcionario_id, empresa_id))
        
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        success = rows_affected > 0
        
        if success:
            logger.info(f"✅ [CPF CORRETOR] CPF do funcionário {funcionario_id} atualizado para: {cpf_formatado}")
            return jsonify({
                'success': True,
                'cpf_novo': cpf_formatado,
                'message': 'CPF atualizado com sucesso'
            })
        else:
            return jsonify({'error': 'Funcionário não encontrado ou sem permissão'}), 404
        
    except Exception as e:
        logger.error(f"❌ Erro ao corrigir CPF: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/funcionarios', methods=['POST'])
@require_permission('folha_pagamento_create')
def criar_funcionario():
    """Criar novo funcionário"""
    # Import local para evitar falha de carregamento do módulo
    from cpf_validator import CPFValidator
    
    try:
        import re
        
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        # 🔒 SEGURANÇA MULTI-TENANT: Usar empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 403
        
        dados = request.get_json()
        
        # Validações obrigatórias
        if not dados.get('nome'):
            return jsonify({'error': 'Nome é obrigatório'}), 400
        if not dados.get('cpf'):
            return jsonify({'error': 'CPF é obrigatório'}), 400
        
        # 🔐 NOVO: Validar CPF com CPFValidator
        validacao_cpf = CPFValidator.validar_com_detalhes(dados['cpf'])
        if not validacao_cpf['valido']:
            return jsonify({'error': f'CPF inválido: {validacao_cpf["erro"]}'}), 400
        
        # 🔐 Validar email se fornecido
        if dados.get('email'):
            try:
                from app.utils.validators import validate_email
                is_valid, error_msg = validate_email(dados['email'])
                if not is_valid:
                    return jsonify({'error': f'Email inválido: {error_msg}'}), 400
            except ImportError:
                # Validação simples caso validators não esteja disponível
                import re
                email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_regex, dados['email']):
                    return jsonify({'error': 'Email inválido'}), 400
        
        # Limpar e formatar CPF
        cpf = CPFValidator.limpar(dados['cpf'])
        
        print(f"\n🔍 [POST /api/funcionarios]")
        print(f"   - empresa_id: {empresa_id}")
        print(f"   - nome: {dados.get('nome')}")
        print(f"   - cpf: {cpf}")
        print(f"   - cpf_formatado: {validacao_cpf['cpf_formatado']}")
        
        # 🔒 Usar get_db_connection com empresa_id para aplicar RLS
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            # Verificar se CPF já existe
            cursor.execute("SELECT id FROM funcionarios WHERE cpf = %s AND empresa_id = %s", (cpf, empresa_id))
            if cursor.fetchone():
                cursor.close()
                return jsonify({'error': 'CPF já cadastrado'}), 400
            
            query = """
                INSERT INTO funcionarios 
                (empresa_id, nome, cpf, email, celular, ativo, data_admissao, data_demissao, observacoes,
                 nacionalidade, estado_civil, data_nascimento, profissao, 
                 rua_av, numero_residencia, complemento, bairro, cidade, estado, cep, 
                 chave_pix, pis_pasep)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            cursor.execute(query, (
                empresa_id,
                dados['nome'],
                cpf,
                dados.get('email'),
                dados.get('celular'),
                dados.get('ativo', True),
                dados.get('data_admissao') if dados.get('data_admissao') else None,
                dados.get('data_demissao') if dados.get('data_demissao') else None,
                dados.get('observacoes'),
                dados.get('nacionalidade'),
                dados.get('estado_civil'),
                dados.get('data_nascimento') if dados.get('data_nascimento') else None,
                dados.get('profissao'),
                dados.get('rua_av'),
                dados.get('numero_residencia'),
                dados.get('complemento'),
                dados.get('bairro'),
                dados.get('cidade'),
                dados.get('estado'),
                dados.get('cep'),
                dados.get('chave_pix'),
                dados.get('pis_pasep')
            ))
            
            resultado = cursor.fetchone()
            funcionario_id = resultado['id'] if isinstance(resultado, dict) else resultado[0]
            conn.commit()
            cursor.close()
            
            print(f"   ✅ Funcionário criado com ID: {funcionario_id}")
            
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
@require_permission('folha_pagamento_edit')
def atualizar_funcionario(funcionario_id):
    """Atualizar funcionário existente"""
    try:
        from app.utils.validators import validate_cpf, validate_email
        import re
        
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        # 🔒 SEGURANÇA MULTI-TENANT: Usar empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 403
        
        dados = request.get_json()
        
        # 🔐 Validar CPF se fornecido
        if dados.get('cpf'):
            is_valid, error_msg = validate_cpf(dados['cpf'])
            if not is_valid:
                return jsonify({'error': f'CPF inválido: {error_msg}'}), 400
        
        # 🔐 Validar email se fornecido
        if dados.get('email'):
            is_valid, error_msg = validate_email(dados['email'])
            if not is_valid:
                return jsonify({'error': f'Email inválido: {error_msg}'}), 400
        
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
        
        campos_permitidos = [
            'nome', 'email', 'celular', 'ativo', 'data_admissao', 'data_demissao', 'observacoes',
            'nacionalidade', 'estado_civil', 'data_nascimento', 'profissao',
            'rua_av', 'numero_residencia', 'complemento', 'bairro', 'cidade', 'estado', 'cep',
            'chave_pix', 'pis_pasep'
        ]
        
        for campo in campos_permitidos:
            if campo in dados:
                campos_update.append(f"{campo} = %s")
                valores.append(dados[campo])
        
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


@app.route('/api/funcionarios/<int:funcionario_id>', methods=['GET'])
@require_permission('folha_pagamento_view')
def obter_funcionario(funcionario_id):
    """Obter detalhes de um funcionário específico"""
    try:
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        # 🔒 SEGURANÇA MULTI-TENANT: Usar empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 403
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Buscar funcionário da empresa
        cursor.execute("""
            SELECT id, empresa_id, nome, cpf, endereco, tipo_chave_pix, 
                   chave_pix, data_admissao, observacoes, ativo,
                   data_criacao, data_atualizacao
            FROM funcionarios 
            WHERE id = %s AND empresa_id = %s
        """, (funcionario_id, empresa_id))
        
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return jsonify({'error': 'Funcionário não encontrado'}), 404
        
        # Verifica se row é dict ou tupla
        if isinstance(row, dict):
            funcionario = {
                'id': row['id'],
                'empresa_id': row['empresa_id'],
                'nome': row['nome'],
                'cpf': row['cpf'],
                'endereco': row['endereco'],
                'tipo_chave_pix': row['tipo_chave_pix'],
                'chave_pix': row['chave_pix'],
                'data_admissao': row['data_admissao'].isoformat() if row['data_admissao'] else None,
                'observacoes': row['observacoes'],
                'ativo': row['ativo'],
                'data_criacao': row['data_criacao'].isoformat() if row['data_criacao'] else None,
                'data_atualizacao': row['data_atualizacao'].isoformat() if row['data_atualizacao'] else None
            }
        else:
            funcionario = {
                'id': row[0],
                'empresa_id': row[1],
                'nome': row[2],
                'cpf': row[3],
                'endereco': row[4],
                'tipo_chave_pix': row[5],
                'chave_pix': row[6],
                'data_admissao': row[7].isoformat() if row[7] else None,
                'observacoes': row[8],
                'ativo': row[9],
                'data_criacao': row[10].isoformat() if row[10] else None,
                'data_atualizacao': row[11].isoformat() if row[11] else None
            }
        
        return jsonify(funcionario), 200
    
    except Exception as e:
        logger.error(f"Erro ao obter funcionário: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/funcionarios/<int:funcionario_id>', methods=['DELETE'])
@require_permission('folha_pagamento_edit')
def deletar_funcionario(funcionario_id):
    """Deletar um funcionário"""
    try:
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        # 🔒 SEGURANÇA MULTI-TENANT: Usar empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 403
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se funcionário existe e pertence à empresa
        cursor.execute("SELECT id FROM funcionarios WHERE id = %s AND empresa_id = %s", 
                      (funcionario_id, empresa_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Funcionário não encontrado'}), 404
        
        # Deletar funcionário
        cursor.execute("DELETE FROM funcionarios WHERE id = %s AND empresa_id = %s", 
                      (funcionario_id, empresa_id))
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Funcionário deletado com sucesso'
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao deletar funcionário: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


# === ROTAS DE EVENTOS ===

@app.route('/api/eventos', methods=['GET'])
@require_permission('eventos_view')
def listar_eventos():
    """Listar eventos com filtros opcionais"""
    try:
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        # SEGURANCA MULTI-TENANT: Usar empresa_id da sessao
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa nao identificada'}), 403
        
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
        
        logger.info(f"🔍 [DEBUG LOAD] Query SQL: {query}")
        logger.info(f"🔍 [DEBUG LOAD] Params: {params}")
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        logger.info(f"🔍 [DEBUG LOAD] Linhas retornadas do DB: {len(rows)}")
        if rows:
            logger.info(f"🔍 [DEBUG LOAD] Primeira linha - data_evento: {rows[0].get('data_evento') if isinstance(rows[0], dict) else rows[0][3]}")
        
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
        
        logger.info(f"[EVENTOS LIST] Total eventos: {len(eventos)}")
        for ev in eventos:
            logger.info(f"[EVENTOS LIST] id={ev['id']}, nome={ev['nome_evento']}, data={ev['data_evento']}")
        
        return jsonify({'eventos': eventos}), 200
    
    except Exception as e:
        logger.error(f"Erro ao listar eventos: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                database.return_to_pool(conn)
        except:
            pass


@app.route('/api/eventos', methods=['POST'])
@require_permission('eventos_create')
def criar_evento():
    """Criar novo evento"""
    try:
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        # 🔒 SEGURANÇA MULTI-TENANT: Usar empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 403
        
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
@require_permission('eventos_edit')
def atualizar_evento(evento_id):
    """Atualizar evento existente - usa autocommit=True para garantir persistencia"""
    conn = None
    cursor = None
    try:
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuario nao autenticado'}), 401
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa nao identificada'}), 403
        
        dados = request.get_json()
        
        logger.info(f"[EVENTO UPDATE] === INICIO === evento_id={evento_id}, empresa_id={empresa_id}")
        logger.info(f"[EVENTO UPDATE] Dados recebidos: {dados}")
        
        # Usar autocommit=True (padrao do pool) - cada statement comita automaticamente
        conn = db.get_connection()
        # NAO alterar autocommit - manter True (padrao do pool)
        cursor = conn.cursor()
        
        # 1. Verificar se evento existe e pertence a empresa
        cursor.execute(
            "SELECT id, data_evento, nome_evento FROM eventos WHERE id = %s AND empresa_id = %s",
            (evento_id, empresa_id)
        )
        evento_atual = cursor.fetchone()
        if not evento_atual:
            logger.warning(f"[EVENTO UPDATE] Evento {evento_id} NAO encontrado para empresa {empresa_id}")
            return jsonify({'error': 'Evento nao encontrado'}), 404
        
        data_antes = evento_atual['data_evento'] if isinstance(evento_atual, dict) else evento_atual[1]
        nome_antes = evento_atual['nome_evento'] if isinstance(evento_atual, dict) else evento_atual[2]
        logger.info(f"[EVENTO UPDATE] Evento encontrado: '{nome_antes}', data_antes={data_antes}")
        
        # 2. Construir query dinamica
        campos_update = []
        valores = []
        
        campos_possiveis = [
            'nome_evento', 'data_evento', 'nf_associada', 'valor_liquido_nf',
            'custo_evento', 'margem', 'tipo_evento', 'status', 'observacoes'
        ]
        
        for campo in campos_possiveis:
            if campo in dados:
                campos_update.append(f"{campo} = %s")
                valores.append(dados[campo])
        
        if not campos_update:
            return jsonify({'error': 'Nenhum campo para atualizar'}), 400
        
        campos_update.append("data_atualizacao = CURRENT_TIMESTAMP")
        valores.append(evento_id)
        valores.append(empresa_id)
        
        query = f"UPDATE eventos SET {', '.join(campos_update)} WHERE id = %s AND empresa_id = %s"
        
        logger.info(f"[EVENTO UPDATE] SQL: {query}")
        logger.info(f"[EVENTO UPDATE] Valores: {valores}")
        
        # 3. Executar UPDATE (autocommit=True => commit automatico)
        cursor.execute(query, valores)
        linhas_afetadas = cursor.rowcount
        logger.info(f"[EVENTO UPDATE] Linhas afetadas pelo UPDATE: {linhas_afetadas}")
        
        if linhas_afetadas == 0:
            logger.error(f"[EVENTO UPDATE] NENHUMA LINHA AFETADA! UPDATE falhou silenciosamente.")
            return jsonify({'error': 'Falha ao atualizar evento - nenhuma linha afetada'}), 500
        
        # 4. Recalcular margem se necessario
        if 'valor_liquido_nf' in dados or 'custo_evento' in dados:
            cursor.execute(
                "SELECT valor_liquido_nf, custo_evento FROM eventos WHERE id = %s",
                (evento_id,)
            )
            evt = cursor.fetchone()
            if evt:
                vl_raw = evt['valor_liquido_nf'] if isinstance(evt, dict) else evt[0]
                ct_raw = evt['custo_evento'] if isinstance(evt, dict) else evt[1]
                vl = float(vl_raw) if vl_raw else 0
                ct = float(ct_raw) if ct_raw else 0
                margem_calc = vl - ct
                cursor.execute("UPDATE eventos SET margem = %s WHERE id = %s", (margem_calc, evento_id))
                logger.info(f"[EVENTO UPDATE] Margem recalculada: {margem_calc}")
        
        # 5. Commit explicito por seguranca (com autocommit=True eh redundante mas seguro)
        conn.commit()
        
        # 6. Verificacao pos-commit - ler de volta do banco
        cursor.execute(
            """SELECT id, nome_evento, data_evento, nf_associada, valor_liquido_nf,
                      custo_evento, margem, tipo_evento, status, observacoes
               FROM eventos WHERE id = %s""",
            (evento_id,)
        )
        evento_atualizado = cursor.fetchone()
        
        if evento_atualizado:
            if isinstance(evento_atualizado, dict):
                data_depois = evento_atualizado['data_evento']
                evento_resp = {
                    'id': evento_atualizado['id'],
                    'nome_evento': evento_atualizado['nome_evento'],
                    'data_evento': evento_atualizado['data_evento'].isoformat() if evento_atualizado['data_evento'] else None,
                    'nf_associada': evento_atualizado['nf_associada'],
                    'valor_liquido_nf': float(evento_atualizado['valor_liquido_nf']) if evento_atualizado['valor_liquido_nf'] else None,
                    'custo_evento': float(evento_atualizado['custo_evento']) if evento_atualizado['custo_evento'] else None,
                    'margem': float(evento_atualizado['margem']) if evento_atualizado['margem'] else None,
                    'tipo_evento': evento_atualizado['tipo_evento'],
                    'status': evento_atualizado['status'],
                    'observacoes': evento_atualizado['observacoes']
                }
            else:
                data_depois = evento_atualizado[2]
                evento_resp = {'id': evento_atualizado[0], 'data_evento': str(evento_atualizado[2])}
            
            logger.info(f"[EVENTO UPDATE] Data ANTES={data_antes} => DEPOIS={data_depois}")
            logger.info(f"[EVENTO UPDATE] === SUCESSO ===")
        else:
            evento_resp = {}
            logger.warning(f"[EVENTO UPDATE] Evento nao encontrado na verificacao pos-commit!")
        
        return jsonify({
            'success': True,
            'message': 'Evento atualizado com sucesso',
            'evento': evento_resp,
            'data_antes': str(data_antes),
            'data_depois': str(data_depois) if evento_atualizado else None
        }), 200
    
    except Exception as e:
        logger.error(f"[EVENTO UPDATE] ERRO: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                database.return_to_pool(conn)
            except:
                pass


@app.route('/api/eventos/<int:evento_id>', methods=['DELETE'])
@require_permission('eventos_delete')
def deletar_evento(evento_id):
    """Deletar evento"""
    conn = None
    try:
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        # 🔒 SEGURANÇA MULTI-TENANT: Usar empresa_id da sessão
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 403
        
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
    
    finally:
        if conn:
            database.return_to_pool(conn)


# === ROTAS DE ALOCAÇÃO DE EQUIPE EM EVENTOS ===

@app.route('/api/funcoes-evento', methods=['GET'])
@require_permission('eventos_view')
def listar_funcoes_evento():
    """Listar funções disponíveis para eventos"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nome, descricao, ativo
            FROM funcoes_evento
            WHERE ativo = TRUE
            ORDER BY nome
        """)
        
        funcoes = []
        for row in cursor.fetchall():
            funcoes.append({
                'id': row['id'],
                'nome': row['nome'],
                'descricao': row['descricao'],
                'ativo': row['ativo']
            })
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'funcoes': funcoes
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao listar funções: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/funcoes-evento', methods=['POST'])
@require_permission('eventos_create')
def criar_funcao_evento():
    """Cadastrar nova função para eventos"""
    try:
        dados = request.get_json()
        
        print(f"\n🔍 [POST /api/funcoes-evento] Dados recebidos:")
        print(f"   - Raw JSON: {dados}")
        print(f"   - Tipo: {type(dados)}")
        print(f"   - Keys: {dados.keys() if dados else 'None'}")
        
        nome = dados.get('nome', '').strip() if dados else ''
        descricao = dados.get('descricao', '').strip() if dados else ''
        
        print(f"   - nome extraído: '{nome}'")
        print(f"   - descricao extraída: '{descricao}'")
        print(f"   - nome vazio? {not nome}")
        
        if not nome:
            print(f"   ❌ Rejeitando: nome vazio")
            return jsonify({'error': 'Nome da função é obrigatório'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se já existe
        cursor.execute("SELECT id FROM funcoes_evento WHERE UPPER(nome) = UPPER(%s)", (nome,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Já existe uma função com este nome'}), 400
        
        # Inserir nova função
        cursor.execute("""
            INSERT INTO funcoes_evento (nome, descricao, ativo)
            VALUES (%s, %s, TRUE)
            RETURNING id
        """, (nome, descricao))
        
        funcao_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Função cadastrada com sucesso',
            'funcao_id': funcao_id
        }), 201
    
    except Exception as e:
        logger.error(f"Erro ao criar função: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/funcoes-evento/<int:funcao_id>', methods=['PUT'])
@require_permission('eventos_edit')
def atualizar_funcao_evento(funcao_id):
    """Atualizar função de evento existente"""
    try:
        dados = request.get_json()
        nome = dados.get('nome', '').strip()
        descricao = dados.get('descricao', '').strip()
        ativo = dados.get('ativo', True)
        
        if not nome:
            return jsonify({'error': 'Nome da função é obrigatório'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se função existe
        cursor.execute("SELECT id FROM funcoes_evento WHERE id = %s", (funcao_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Função não encontrada'}), 404
        
        # Verificar se nome já existe em outra função
        cursor.execute(
            "SELECT id FROM funcoes_evento WHERE UPPER(nome) = UPPER(%s) AND id != %s",
            (nome, funcao_id)
        )
        if cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Já existe outra função com este nome'}), 400
        
        # Atualizar função
        cursor.execute("""
            UPDATE funcoes_evento 
            SET nome = %s, descricao = %s, ativo = %s
            WHERE id = %s
        """, (nome, descricao, ativo, funcao_id))
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Função atualizada com sucesso'
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao atualizar função: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/funcoes-evento/<int:funcao_id>', methods=['DELETE'])
@require_permission('eventos_edit')
def deletar_funcao_evento(funcao_id):
    """Deletar função de evento"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se função existe
        cursor.execute("SELECT id FROM funcoes_evento WHERE id = %s", (funcao_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Função não encontrada'}), 404
        
        # Verificar se há funcionários usando esta função
        cursor.execute(
            "SELECT COUNT(*) as total FROM evento_funcionarios WHERE funcao_id = %s",
            (funcao_id,)
        )
        result = cursor.fetchone()
        total = result['total'] if isinstance(result, dict) else result[0]
        
        if total > 0:
            cursor.close()
            return jsonify({
                'error': f'Não é possível excluir. Esta função está sendo usada por {total} alocação(ões) de funcionários.'
            }), 400
        
        # Deletar função
        cursor.execute("DELETE FROM funcoes_evento WHERE id = %s", (funcao_id,))
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Função deletada com sucesso'
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao deletar função: {e}")
        return jsonify({'error': str(e)}), 500


# ========================================
# ENDPOINTS: SETORES
# ========================================

@app.route('/api/setores', methods=['GET'])
@require_permission('eventos_view')
def listar_setores():
    """Listar setores cadastrados"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nome, ativo, created_at
            FROM setores
            ORDER BY nome
        """)
        
        setores = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'success': True,
            'setores': setores
        })
    
    except Exception as e:
        logger.error(f"Erro ao listar setores: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/setores', methods=['POST'])
@require_permission('eventos_create')
def criar_setor():
    """Cadastrar novo setor"""
    try:
        dados = request.get_json()
        nome = dados.get('nome', '').strip()
        
        if not nome:
            return jsonify({'error': 'Nome do setor é obrigatório'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se já existe
        cursor.execute("SELECT id FROM setores WHERE UPPER(nome) = UPPER(%s)", (nome,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Já existe um setor com este nome'}), 400
        
        # Inserir novo setor
        cursor.execute("""
            INSERT INTO setores (nome, ativo, created_at)
            VALUES (%s, TRUE, NOW())
            RETURNING id
        """, (nome,))
        
        setor_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Setor cadastrado com sucesso',
            'setor_id': setor_id
        }), 201
    
    except Exception as e:
        logger.error(f"Erro ao criar setor: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/setores/<int:setor_id>', methods=['PATCH'])
@require_permission('eventos_edit')
def atualizar_setor(setor_id):
    """Atualizar status do setor (ativar/desativar)"""
    try:
        dados = request.get_json()
        ativo = dados.get('ativo')
        
        if ativo is None:
            return jsonify({'error': 'Status ativo é obrigatório'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE setores
            SET ativo = %s
            WHERE id = %s
            RETURNING id
        """, (ativo, setor_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Setor não encontrado'}), 404
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': f'Setor {"ativado" if ativo else "desativado"} com sucesso'
        })
    
    except Exception as e:
        logger.error(f"Erro ao criar função: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/setores/<int:setor_id>', methods=['DELETE'])
@require_permission('eventos_edit')
def excluir_setor(setor_id):
    """Excluir um setor"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se o setor existe
        cursor.execute("SELECT nome FROM setores WHERE id = %s", (setor_id,))
        setor = cursor.fetchone()
        
        if not setor:
            cursor.close()
            return jsonify({'error': 'Setor não encontrado'}), 404
        
        # Excluir o setor
        cursor.execute("DELETE FROM setores WHERE id = %s", (setor_id,))
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Setor excluído com sucesso'
        })
    
    except Exception as e:
        logger.error(f"Erro ao excluir setor: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/eventos/<int:evento_id>/equipe', methods=['GET'])
@require_permission('eventos_view')
def listar_equipe_evento(evento_id):
    """Listar equipe alocada em um evento"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ef.id,
                ef.funcionario_id,
                f.nome as funcionario_nome,
                f.cpf as funcionario_cpf,
                f.email as funcionario_email,
                f.chave_pix as funcionario_chave_pix,
                ef.funcao_id,
                ef.funcao_nome,
                ef.setor_id,
                s.nome as setor_nome,
                ef.valor,
                ef.hora_inicio,
                ef.hora_fim,
                ef.observacoes
            FROM evento_funcionarios ef
            INNER JOIN funcionarios f ON f.id = ef.funcionario_id
            LEFT JOIN setores s ON s.id = ef.setor_id
            WHERE ef.evento_id = %s
            ORDER BY f.nome
        """, (evento_id,))
        
        equipe = []
        for row in cursor.fetchall():
            equipe.append({
                'id': row['id'],
                'funcionario_id': row['funcionario_id'],
                'funcionario_nome': row['funcionario_nome'],
                'funcionario_cpf': row['funcionario_cpf'],
                'funcionario_email': row['funcionario_email'],
                'funcionario_chave_pix': row['funcionario_chave_pix'],
                'funcao_id': row['funcao_id'],
                'funcao_nome': row['funcao_nome'],
                'setor_id': row['setor_id'],
                'setor_nome': row['setor_nome'],
                'valor': float(row['valor']) if row['valor'] else 0.0,
                'hora_inicio': str(row['hora_inicio']) if row['hora_inicio'] else None,
                'hora_fim': str(row['hora_fim']) if row['hora_fim'] else None,
                'observacoes': row['observacoes']
            })
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'equipe': equipe
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao listar equipe: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/eventos/<int:evento_id>/equipe', methods=['POST'])
@require_permission('eventos_create')
def adicionar_funcionario_evento(evento_id):
    """Adicionar funcionário à equipe do evento"""
    try:
        dados = request.get_json()
        print(f"[EQUIPE MASSA] Dados recebidos: {dados}", flush=True)  # DEBUG
        
        funcionario_id = dados.get('funcionario_id')
        funcao_id = dados.get('funcao_id')
        setor_id = dados.get('setor_id')  # Opcional
        valor = dados.get('valor', 0)
        hora_inicio = dados.get('hora_inicio')  # Opcional
        hora_fim = dados.get('hora_fim')  # Opcional
        
        print(f"[EQUIPE MASSA] funcionario_id={funcionario_id}, funcao_id={funcao_id}, valor={valor}", flush=True)  # DEBUG
        
        if not funcionario_id or not funcao_id:
            print(f"[EQUIPE MASSA] ❌ ERRO: Campos obrigatórios ausentes", flush=True)  # DEBUG
            return jsonify({'error': 'Funcionário e função são obrigatórios'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Buscar nome da função para histórico
        cursor.execute("SELECT nome FROM funcoes_evento WHERE id = %s", (funcao_id,))
        funcao_row = cursor.fetchone()
        if not funcao_row:
            print(f"[EQUIPE MASSA] ❌ ERRO: Função {funcao_id} não encontrada", flush=True)  # DEBUG
            cursor.close()
            return jsonify({'error': 'Função não encontrada'}), 404
        
        funcao_nome = funcao_row['nome']
        print(f"[EQUIPE MASSA] Função encontrada: {funcao_nome}", flush=True)  # DEBUG
        
        # Verificar se já existe alocação
        cursor.execute("""
            SELECT id FROM evento_funcionarios 
            WHERE evento_id = %s AND funcionario_id = %s AND funcao_id = %s
        """, (evento_id, funcionario_id, funcao_id))
        
        if cursor.fetchone():
            print(f"[EQUIPE MASSA] ⚠️ DUPLICADO: Funcionário {funcionario_id} já alocado no evento {evento_id} com função {funcao_id}", flush=True)  # DEBUG
            cursor.close()
            return jsonify({'error': 'Este funcionário já está alocado com esta função neste evento'}), 400
        
        # Inserir alocação (com setor_id, hora_inicio e hora_fim se fornecidos)
        cursor.execute("""
            INSERT INTO evento_funcionarios 
            (evento_id, funcionario_id, funcao_id, funcao_nome, setor_id, valor, hora_inicio, hora_fim)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (evento_id, funcionario_id, funcao_id, funcao_nome, setor_id, valor, hora_inicio, hora_fim))
        
        alocacao_id = cursor.fetchone()['id']
        
        # Calcular novo custo total do evento
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) as total
            FROM evento_funcionarios
            WHERE evento_id = %s
        """, (evento_id,))
        
        custo_total = cursor.fetchone()['total']
        
        # Buscar valor_liquido_nf para recalcular margem
        cursor.execute("""
            SELECT valor_liquido_nf
            FROM eventos
            WHERE id = %s
        """, (evento_id,))
        
        evento_row = cursor.fetchone()
        valor_liquido = evento_row['valor_liquido_nf'] if evento_row and evento_row['valor_liquido_nf'] else 0
        
        # Calcular margem: Valor Líquido - Custo
        margem = float(valor_liquido) - float(custo_total)
        
        # Atualizar custo do evento E margem
        cursor.execute("""
            UPDATE eventos
            SET custo_evento = %s, margem = %s
            WHERE id = %s
        """, (custo_total, margem, evento_id))
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Funcionário adicionado à equipe',
            'alocacao_id': alocacao_id,
            'custo_total': float(custo_total)
        }), 201
    
    except Exception as e:
        logger.error(f"Erro ao adicionar funcionário: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/eventos/equipe/<int:alocacao_id>', methods=['DELETE'])
@require_permission('eventos_delete')
def remover_funcionario_evento(alocacao_id):
    """Remover funcionário da equipe do evento"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Buscar evento_id antes de deletar
        cursor.execute("SELECT evento_id FROM evento_funcionarios WHERE id = %s", (alocacao_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return jsonify({'error': 'Alocação não encontrada'}), 404
        
        evento_id = row['evento_id']
        
        # Deletar alocação
        cursor.execute("DELETE FROM evento_funcionarios WHERE id = %s", (alocacao_id,))
        
        # Recalcular custo total do evento
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) as total
            FROM evento_funcionarios
            WHERE evento_id = %s
        """, (evento_id,))
        
        custo_total = cursor.fetchone()['total']
        
        # Buscar valor_liquido_nf para recalcular margem
        cursor.execute("""
            SELECT valor_liquido_nf
            FROM eventos
            WHERE id = %s
        """, (evento_id,))
        
        evento_row = cursor.fetchone()
        valor_liquido = evento_row['valor_liquido_nf'] if evento_row and evento_row['valor_liquido_nf'] else 0
        
        # Calcular margem: Valor Líquido - Custo
        margem = float(valor_liquido) - float(custo_total)
        
        # Atualizar custo do evento E margem
        cursor.execute("""
            UPDATE eventos
            SET custo_evento = %s, margem = %s
            WHERE id = %s
        """, (custo_total, margem, evento_id))
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Funcionário removido da equipe',
            'custo_total': float(custo_total)
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao remover funcionário: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ROTAS DE FORNECEDORES DO EVENTO
# ============================================================================

@app.route('/api/eventos/<int:evento_id>/fornecedores', methods=['GET'])
@require_permission('eventos_view')
def listar_fornecedores_evento(evento_id):
    """Listar fornecedores vinculados ao evento"""
    try:
        from psycopg2.extras import RealDictCursor
        
        logger.info(f"🏢 GET /api/eventos/{evento_id}/fornecedores")
        
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verificar se a tabela existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'evento_fornecedores'
            );
        """)
        
        tabela_existe = cursor.fetchone()['exists']
        
        if not tabela_existe:
            logger.warning("   ⚠️  Tabela evento_fornecedores não existe - Retornando lista vazia")
            cursor.close()
            return jsonify({
                'success': True,
                'fornecedores': [],
                'warning': 'Tabela evento_fornecedores não existe. Execute a migração.'
            }), 200
        
        cursor.execute("""
            SELECT 
                ef.id,
                ef.fornecedor_id,
                f.nome as fornecedor_nome,
                ef.categoria_id,
                c.nome as categoria_nome,
                ef.subcategoria_id,
                sc.nome as subcategoria_nome,
                ef.valor,
                ef.observacao,
                ef.created_at
            FROM evento_fornecedores ef
            JOIN fornecedores f ON ef.fornecedor_id = f.id
            LEFT JOIN categorias c ON ef.categoria_id = c.id
            LEFT JOIN subcategorias sc ON ef.subcategoria_id = sc.id
            WHERE ef.evento_id = %s
            ORDER BY ef.created_at DESC
        """, (evento_id,))
        
        fornecedores = cursor.fetchall()
        cursor.close()
        
        logger.info(f"   📊 Retornando {len(fornecedores)} fornecedores")
        
        return jsonify({
            'success': True,
            'fornecedores': fornecedores
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Erro ao listar fornecedores do evento: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/eventos/<int:evento_id>/fornecedores', methods=['POST'])
@require_permission('eventos_edit')
def adicionar_fornecedor_evento(evento_id):
    """Adicionar fornecedor ao evento"""
    try:
        dados = request.json
        fornecedor_id = dados.get('fornecedor_id')
        categoria_id = dados.get('categoria_id')
        subcategoria_id = dados.get('subcategoria_id')
        valor = dados.get('valor', 0)
        observacao = dados.get('observacao')
        
        if not fornecedor_id:
            return jsonify({'error': 'fornecedor_id é obrigatório'}), 400
        
        usuario = get_usuario_logado()
        usuario_id = usuario.get('id') if usuario else None
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se fornecedor já está vinculado ao evento
        cursor.execute("""
            SELECT id FROM evento_fornecedores
            WHERE evento_id = %s AND fornecedor_id = %s
        """, (evento_id, fornecedor_id))
        
        if cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Fornecedor já está vinculado a este evento'}), 400
        
        # Inserir fornecedor no evento
        cursor.execute("""
            INSERT INTO evento_fornecedores 
            (evento_id, fornecedor_id, categoria_id, subcategoria_id, valor, observacao, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (evento_id, fornecedor_id, categoria_id, subcategoria_id, valor, observacao, usuario_id))
        
        fornecedor_evento_id = cursor.fetchone()['id']
        
        # Recalcular custo total do evento (equipe + fornecedores)
        cursor.execute("""
            SELECT 
                COALESCE(SUM(ef.valor), 0) as custo_equipe,
                COALESCE((SELECT SUM(valor) FROM evento_fornecedores WHERE evento_id = %s), 0) as custo_fornecedores
            FROM evento_funcionarios ef
            WHERE ef.evento_id = %s
        """, (evento_id, evento_id))
        
        custos = cursor.fetchone()
        custo_equipe = float(custos['custo_equipe'])
        custo_fornecedores = float(custos['custo_fornecedores'])
        custo_total = custo_equipe + custo_fornecedores
        
        # Buscar valor_liquido_nf para recalcular margem
        cursor.execute("""
            SELECT valor_liquido_nf
            FROM eventos
            WHERE id = %s
        """, (evento_id,))
        
        evento_row = cursor.fetchone()
        valor_liquido = evento_row['valor_liquido_nf'] if evento_row and evento_row['valor_liquido_nf'] else 0
        
        # Calcular margem: Valor Líquido - Custo Total (Equipe + Fornecedores)
        margem = float(valor_liquido) - custo_total
        
        # Atualizar custo do evento E margem
        cursor.execute("""
            UPDATE eventos
            SET custo_evento = %s, margem = %s
            WHERE id = %s
        """, (custo_total, margem, evento_id))
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Fornecedor adicionado ao evento',
            'id': fornecedor_evento_id,
            'custo_total': custo_total
        }), 201
    
    except Exception as e:
        logger.error(f"Erro ao adicionar fornecedor: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/eventos/fornecedores/<int:fornecedor_evento_id>', methods=['DELETE'])
@require_permission('eventos_delete')
def remover_fornecedor_evento(fornecedor_evento_id):
    """Remover fornecedor do evento"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Buscar evento_id antes de deletar
        cursor.execute("SELECT evento_id FROM evento_fornecedores WHERE id = %s", (fornecedor_evento_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return jsonify({'error': 'Vínculo não encontrado'}), 404
        
        evento_id = row['evento_id']
        
        # Deletar vínculo
        cursor.execute("DELETE FROM evento_fornecedores WHERE id = %s", (fornecedor_evento_id,))
        
        # Recalcular custo total do evento (equipe + fornecedores)
        cursor.execute("""
            SELECT 
                COALESCE(SUM(ef.valor), 0) as custo_equipe,
                COALESCE((SELECT SUM(valor) FROM evento_fornecedores WHERE evento_id = %s), 0) as custo_fornecedores
            FROM evento_funcionarios ef
            WHERE ef.evento_id = %s
        """, (evento_id, evento_id))
        
        custos = cursor.fetchone()
        custo_equipe = float(custos['custo_equipe'])
        custo_fornecedores = float(custos['custo_fornecedores'])
        custo_total = custo_equipe + custo_fornecedores
        
        # Buscar valor_liquido_nf para recalcular margem
        cursor.execute("""
            SELECT valor_liquido_nf
            FROM eventos
            WHERE id = %s
        """, (evento_id,))
        
        evento_row = cursor.fetchone()
        valor_liquido = evento_row['valor_liquido_nf'] if evento_row and evento_row['valor_liquido_nf'] else 0
        
        # Calcular margem: Valor Líquido - Custo Total (Equipe + Fornecedores)
        margem = float(valor_liquido) - custo_total
        
        # Atualizar custo do evento E margem
        cursor.execute("""
            UPDATE eventos
            SET custo_evento = %s, margem = %s
            WHERE id = %s
        """, (custo_total, margem, evento_id))
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Fornecedor removido do evento',
            'custo_total': custo_total
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao remover fornecedor: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/subcategorias', methods=['GET'])
@require_permission('categorias_view')
def listar_subcategorias():
    """Lista subcategorias de uma categoria específica"""
    try:
        from psycopg2.extras import RealDictCursor
        
        categoria_id = request.args.get('categoria_id')
        
        logger.info(f"📋 GET /api/subcategorias - categoria_id={categoria_id}")
        
        if not categoria_id:
            return jsonify({'success': False, 'error': 'categoria_id é obrigatório'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verificar se a coluna 'ativa' existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'subcategorias' 
                AND column_name = 'ativa'
            );
        """)
        
        coluna_ativa_existe = cursor.fetchone()['exists']
        
        if coluna_ativa_existe:
            logger.info("   ✅ Coluna 'ativa' existe, filtrando por ativa=TRUE")
            cursor.execute("""
                SELECT id, nome, categoria_id, ativa
                FROM subcategorias
                WHERE categoria_id = %s AND ativa = TRUE
                ORDER BY nome
            """, (int(categoria_id),))
        else:
            logger.warning("   ⚠️  Coluna 'ativa' não existe, listando todas")
            cursor.execute("""
                SELECT id, nome, categoria_id
                FROM subcategorias
                WHERE categoria_id = %s
                ORDER BY nome
            """, (int(categoria_id),))
        
        subcategorias = cursor.fetchall()
        cursor.close()
        
        logger.info(f"   📊 Retornando {len(subcategorias)} subcategorias")
        
        return jsonify({
            'success': True,
            'subcategorias': subcategorias
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Erro ao listar subcategorias: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# === ROTAS DE RELATÓRIOS ===
# Todos os relatórios movidos para app/routes/relatorios.py
# - dashboard, dashboard-completo, fluxo-projetado
# - analise-contas, resumo-parceiros, analise-categorias  
# - comparativo-periodos, indicadores, inadimplencia

@app.route('/api/relatorios/dashboard', methods=['GET'])
@require_permission('lancamentos_view')
def dashboard():
    """Dados para o dashboard - versão simplificada"""
    # 🔒 VALIDAÇÃO DE SEGURANÇA
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        print("=" * 80)
        print("📊 DASHBOARD - Iniciando carregamento...")
        
        # Pegar filtros opcionais
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        print(f"📅 Filtros: ano={ano}, mes={mes}")
        
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        contas = db.listar_contas_por_empresa(empresa_id=empresa_id)
        print(f"📋 Total de lançamentos: {len(lancamentos)}")
        print(f"🏦 Total de contas: {len(contas)}")
        
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
        
        print(f"📊 DADOS DO GRÁFICO:")
        print(f"   Meses: {meses_labels}")
        print(f"   Receitas: {receitas_dados}")
        print(f"   Despesas: {despesas_dados}")
        print(f"💰 CARDS:")
        print(f"   Contas a Receber: R$ {float(contas_receber):,.2f}")
        print(f"   Contas a Pagar: R$ {float(contas_pagar):,.2f}")
        print(f"   Contas Vencidas: R$ {float(contas_vencidas):,.2f}")
        print(f"   Saldo Total: R$ {float(saldo_total):,.2f}")
        print("=" * 80)
        
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
    # 🔒 VALIDAÇÃO DE SEGURANÇA
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        if not data_inicio or not data_fim:
            return jsonify({'error': 'Datas obrigatórias'}), 400
        
        data_inicio_obj = parse_date(data_inicio)
        data_fim_obj = parse_date(data_fim)
        
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        
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
    # 🔒 VALIDAÇÃO DE SEGURANÇA
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        # Receber filtros - padrão é projetar próximos X dias
        dias = request.args.get('dias')
        dias = int(dias) if dias else 30
        
        hoje = date.today()
        data_inicial = hoje
        data_final = hoje + timedelta(days=dias)
        periodo_texto = f"PROJEÇÃO - PRÓXIMOS {dias} DIAS"
        
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        contas = db.listar_contas_por_empresa(empresa_id=empresa_id)
        
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
    # 🔒 VALIDAÇÃO DE SEGURANÇA
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
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


@app.route('/api/lancamentos/<int:lancamento_id>/associacao', methods=['PATCH'])
@require_permission('lancamentos_edit')
def atualizar_associacao_lancamento(lancamento_id):
    """
    Atualiza apenas o campo de associação de um lançamento (salvamento automático)
    
    Security:
        🔒 Validado empresa_id da sessão
        🔒 Verifica permissão lancamentos_edit
    """
    try:
        # 🔒 VALIDAÇÃO DE SEGURANÇA
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        data = request.get_json()
        nova_associacao = data.get('associacao', '')
        
        # 🔗 Atualizar associacao E numero_documento simultaneamente (sincronização bidirecional)
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE lancamentos 
                SET associacao = %s, numero_documento = %s
                WHERE id = %s AND empresa_id = %s
                RETURNING id
            """, (nova_associacao, nova_associacao, lancamento_id, empresa_id))
            
            resultado = cursor.fetchone()
            conn.commit()
            cursor.close()
            
            if not resultado:
                return jsonify({'success': False, 'error': 'Lançamento não encontrado'}), 404
            
            return jsonify({'success': True, 'id': lancamento_id, 'associacao': nova_associacao})
            
    except Exception as e:
        print(f"❌ Erro ao atualizar associação: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


# === ROTA PRINCIPAL ===

@app.route('/login')
def login_page():
    """Página de login"""
    return render_template('login.html')

@app.route('/api/csrf-token', methods=['GET'])
def get_csrf_token_endpoint():
    """
    Endpoint para obter CSRF token via API
    Gera e retorna um token CSRF válido
    """
    from flask_wtf.csrf import generate_csrf
    token = generate_csrf()
    print(f"🔑 CSRF Token gerado via API: {token[:20]}...")
    return jsonify({
        'csrf_token': token,
        'success': True
    })

@app.route('/admin')
@require_admin
def admin_page():
    """Painel administrativo - apenas para admins"""
    print(f"\n🎯🎯🎯 ROTA /admin ALCANÇADA - Decorador passou! 🎯🎯🎯\n")
    return render_template('admin.html')

@app.route('/admin/fix-empresa-id', methods=['GET', 'POST'])
@require_admin
def admin_fix_empresa_id():
    """
    Rota administrativa para corrigir empresa_id em registros antigos
    
    ATENCAO: Esta rota atualiza TODOS os registros sem empresa_id!
    Use com cuidado!
    """
    from database_postgresql import get_db_connection
    
    if request.method == 'GET':
        # Mostrar página de confirmação
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Corrigir empresa_id</title>
            <style>
                body { font-family: Arial; padding: 40px; max-width: 800px; margin: 0 auto; }
                .warning { background: #fff3cd; border: 2px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 8px; }
                .btn { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
                .btn:hover { background: #0056b3; }
                .danger { background: #dc3545; }
                .danger:hover { background: #c82333; }
                pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }
            </style>
        </head>
        <body>
            <h1>🔧 Corrigir empresa_id em Registros Antigos</h1>
            
            <div class="warning">
                <h3>⚠️ ATENÇÃO</h3>
                <p>Esta ação irá atualizar TODOS os registros sem <code>empresa_id</code> nas seguintes tabelas:</p>
                <ul>
                    <li>contratos</li>
                    <li>sessoes</li>
                    <li>lancamentos</li>
                    <li>clientes</li>
                    <li>fornecedores</li>
                    <li>categorias</li>
                </ul>
                <p><strong>Os registros serão associados à empresa ID 19.</strong></p>
            </div>
            
            <h3>O que será feito:</h3>
            <pre>
UPDATE contratos SET empresa_id = 19 WHERE empresa_id IS NULL;
UPDATE sessoes SET empresa_id = 19 WHERE empresa_id IS NULL;
UPDATE lancamentos SET empresa_id = 19 WHERE empresa_id IS NULL;
...
            </pre>
            
            <form method="POST" onsubmit="return confirm('Tem certeza? Esta ação não pode ser desfeita!');">
                <button type="submit" class="btn danger">✅ Executar Correção</button>
                <a href="/admin" style="margin-left: 20px;">❌ Cancelar</a>
            </form>
        </body>
        </html>
        """
    
    # POST - Executar correção
    try:
        with get_db_connection(allow_global=True) as conn:
            cursor = conn.cursor()
            
            resultados = []
            
            # Análise inicial
            tabelas = ['contratos', 'sessoes', 'lancamentos', 'clientes', 'fornecedores', 'categorias']
            analise_inicial = {}
            
            for tabela in tabelas:
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id
                    FROM {tabela}
                """)
                result = cursor.fetchone()
                analise_inicial[tabela] = {
                    'total': result['total'],
                    'sem_empresa_id': result['sem_empresa_id']
                }
            
            # Executar correções
            updates = {
                'contratos': "UPDATE contratos SET empresa_id = 19 WHERE empresa_id IS NULL",
                'sessoes': "UPDATE sessoes SET empresa_id = 19 WHERE empresa_id IS NULL",
                'lancamentos': "UPDATE lancamentos SET empresa_id = 19 WHERE empresa_id IS NULL",
                'clientes': "UPDATE clientes SET empresa_id = 19 WHERE empresa_id IS NULL",
                'fornecedores': "UPDATE fornecedores SET empresa_id = 19 WHERE empresa_id IS NULL",
                'categorias': "UPDATE categorias SET empresa_id = 19 WHERE empresa_id IS NULL"
            }
            
            for tabela, sql in updates.items():
                cursor.execute(sql)
                count = cursor.rowcount
                resultados.append(f"✅ {tabela}: {count} registro(s) atualizado(s)")
            
            conn.commit()
            cursor.close()
            
            # Retornar resultado
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Correção Concluída</title>
                <style>
                    body {{ font-family: Arial; padding: 40px; max-width: 800px; margin: 0 auto; }}
                    .success {{ background: #d4edda; border: 2px solid #28a745; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                    .resultado {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <h1>✅ Correção Concluída com Sucesso!</h1>
                
                <div class="success">
                    <h3>Resultados:</h3>
                    {''.join(f'<div class="resultado">{r}</div>' for r in resultados)}
                </div>
                
                <a href="/admin">← Voltar ao Admin</a>
            </body>
            </html>
            """
            
            return html
            
    except Exception as e:
        return f"""
        <h1>❌ Erro ao executar correção</h1>
        <pre>{str(e)}</pre>
        <a href="/admin">← Voltar</a>
        """, 500

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

@app.route('/admin/import')
@require_permission('admin')
def admin_import_page():
    """Página de importação de banco de dados"""
    return render_template('admin_import.html')

# ============================================================================
# ROTAS DE IMPORTAÇÃO DE BANCO DE DADOS
# ============================================================================
from werkzeug.utils import secure_filename
from database_import_manager import DatabaseImportManager
import tempfile
import csv

ALLOWED_EXTENSIONS = {'sql', 'dump', 'backup', 'csv', 'json', 'db', 'db-shm', 'db-wal', 'sqlite', 'sqlite3'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/admin/import/upload', methods=['POST'])
@csrf.exempt
@require_permission('admin')
def upload_import_file():
    """Upload e processamento de arquivo para importação"""
    logger.info("🚀 [IMPORT] Função upload_import_file() chamada")
    logger.info(f"🚀 [IMPORT] Request method: {request.method}")
    logger.info(f"🚀 [IMPORT] Content-Type: {request.content_type}")
    try:
        logger.info("📥 Upload de arquivo iniciado")
        
        # Verificar se é upload múltiplo
        multiple_files = request.files.getlist('files[]')
        
        if multiple_files:
            logger.info(f"📁 Upload múltiplo: {len(multiple_files)} arquivos")
            temp_dir = tempfile.gettempdir()
            db_file_path = None
            
            for file in multiple_files:
                if file.filename == '':
                    continue
                
                if not allowed_file(file.filename):
                    return jsonify({'error': f'Formato não suportado: {file.filename}'}), 400
                
                filename = secure_filename(file.filename)
                temp_path = os.path.join(temp_dir, f"import_{session.get('usuario_id')}_{filename}")
                file.save(temp_path)
                
                if filename.endswith('.db') or filename.endswith('.sqlite') or filename.endswith('.sqlite3'):
                    db_file_path = temp_path
                
                logger.info(f"✅ Arquivo salvo: {temp_path}")
            
            if not db_file_path:
                return jsonify({'error': 'Arquivo .db principal não encontrado'}), 400
            
            manager = DatabaseImportManager()
            schema = manager.parse_sqlite_database(db_file_path)
            
            return jsonify({
                'success': True,
                'schema': schema,
                'temp_file': db_file_path,
                'total_tabelas': len(schema),
                'total_registros': sum(t.get('total_registros', 0) for t in schema.values())
            })
        
        # Upload único
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'Formato não suportado. Use: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Validar tamanho
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'Arquivo muito grande (máx: 100MB)'}), 400
        
        filename = secure_filename(file.filename)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"import_{session.get('usuario_id')}_{filename}")
        file.save(temp_path)
        
        logger.info(f"✅ Arquivo salvo: {temp_path}")
        
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        manager = DatabaseImportManager()
        
        if file_ext in ['sql', 'dump', 'backup']:
            schema = manager.parse_sql_dump(temp_path)
        elif file_ext == 'csv':
            schema = manager.parse_csv_file(temp_path)
        elif file_ext == 'json':
            schema = manager.parse_json_file(temp_path)
        elif file_ext in ['db', 'db-shm', 'db-wal', 'sqlite', 'sqlite3']:
            schema = manager.parse_sqlite_database(temp_path)
        else:
            return jsonify({'error': 'Formato não reconhecido'}), 400
        
        return jsonify({
            'success': True,
            'schema': schema,
            'temp_file': temp_path,
            'total_tabelas': len(schema),
            'total_registros': sum(t.get('total_registros', 0) for t in schema.values())
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no upload: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/import/schema/interno', methods=['GET'])
@csrf.exempt
@require_permission('admin')
def get_internal_schema():
    """Obtém schema do banco interno usando a mesma conexão do sistema"""
    try:
        db_instance = DatabaseManager()
        conn = db_instance.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Buscar todas as tabelas do schema public
        cursor.execute("""
            SELECT 
                table_name,
                (SELECT COUNT(*) FROM information_schema.columns 
                 WHERE table_schema = 'public' AND table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        schema = {}
        
        for table in tables:
            table_name = table['table_name']
            
            # Buscar colunas da tabela
            cursor.execute("""
                SELECT 
                    column_name as name,
                    data_type as type,
                    is_nullable,
                    column_default as default_value
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            # Contar registros (com timeout de 5 segundos)
            try:
                cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
                count_result = cursor.fetchone()
                total_registros = count_result['total'] if count_result else 0
            except:
                total_registros = 0
            
            schema[table_name] = {
                'columns': [dict(col) for col in columns],
                'total_registros': total_registros
            }
        
        conn.close()
        
        logger.info(f"✅ Schema interno carregado: {len(schema)} tabelas")
        
        return jsonify({
            'success': True,
            'schema': schema,
            'total_tabelas': len(schema)
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter schema interno: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/import/sugestao-mapeamento', methods=['POST'])
@csrf.exempt
@require_permission('admin')
def suggest_mapping():
    """Gera sugestões de mapeamento entre tabelas"""
    try:
        data = request.json
        schema_externo = data.get('schema_externo')
        schema_interno = data.get('schema_interno')
        
        if not schema_externo or not schema_interno:
            return jsonify({'error': 'Schemas externo e interno são obrigatórios'}), 400
        
        manager = DatabaseImportManager()
        sugestoes = manager.suggest_table_mapping(schema_externo, schema_interno)
        
        return jsonify({
            'success': True,
            'sugestoes': sugestoes,
            'total_mapeamentos': len(sugestoes)
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar sugestões: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/import/criar', methods=['POST'])
@csrf.exempt
@require_permission('admin')
def create_import():
    """Cria registro de importação com mapeamentos"""
    try:
        data = request.json
        empresa_id = data.get('empresa_id')
        mapeamentos = data.get('mapeamentos')
        schema_externo = data.get('schema_externo')
        
        if not empresa_id or not mapeamentos:
            return jsonify({'error': 'empresa_id e mapeamentos são obrigatórios'}), 400
        
        manager = DatabaseImportManager()
        manager.connect()
        
        # Criar registro na tabela import_historico
        import_id = manager.create_import_record(
            empresa_id=empresa_id,
            usuario_id=session.get('usuario_id'),
            fonte_tipo='sqlite',
            mapeamentos=mapeamentos,
            schema_externo=schema_externo
        )
        
        manager.close()
        
        return jsonify({
            'success': True,
            'import_id': import_id,
            'message': 'Importação criada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar importação: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/import/executar/<int:import_id>', methods=['POST'])
@csrf.exempt
@require_permission('admin')
def execute_import(import_id):
    """Executa a importação de dados"""
    try:
        data = request.json
        arquivo_path = data.get('arquivo_path')
        
        if not arquivo_path:
            return jsonify({'error': 'arquivo_path é obrigatório'}), 400
        
        manager = DatabaseImportManager()
        manager.connect()
        
        resultado = manager.execute_import(import_id, arquivo_path)
        
        manager.close()
        
        return jsonify({
            'success': True,
            'resultado': resultado,
            'message': 'Importação executada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao executar importação: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/import/reverter/<int:import_id>', methods=['POST'])
@csrf.exempt
@require_permission('admin')
def rollback_import(import_id):
    """Reverte uma importação (rollback)"""
    try:
        manager = DatabaseImportManager()
        manager.connect()
        
        resultado = manager.rollback_import(import_id)
        
        manager.close()
        
        return jsonify({
            'success': True,
            'resultado': resultado,
            'message': 'Importação revertida com sucesso'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao reverter importação: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================

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
    # 🔒 VALIDAÇÃO DE SEGURANÇA
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        data_inicio = request.args.get('data_inicio', (date.today() - timedelta(days=30)).isoformat())
        data_fim = request.args.get('data_fim', date.today().isoformat())
        
        data_inicio = datetime.fromisoformat(data_inicio).date()
        data_fim = datetime.fromisoformat(data_fim).date()
        
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        
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
    # 🔒 VALIDAÇÃO DE SEGURANÇA
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        data_inicio = request.args.get('data_inicio', (date.today() - timedelta(days=30)).isoformat())
        data_fim = request.args.get('data_fim', date.today().isoformat())
        
        data_inicio = datetime.fromisoformat(data_inicio).date()
        data_fim = datetime.fromisoformat(data_fim).date()
        
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        
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
        print(f"[COMPARATIVO] Iniciando comparativo de períodos")
        
        # Período 1
        data_inicio1 = request.args.get('data_inicio1')
        data_fim1 = request.args.get('data_fim1')
        
        # Período 2
        data_inicio2 = request.args.get('data_inicio2')
        data_fim2 = request.args.get('data_fim2')
        
        print(f"[COMPARATIVO] Parâmetros recebidos:")
        print(f"  Período 1: {data_inicio1} até {data_fim1}")
        print(f"  Período 2: {data_inicio2} até {data_fim2}")
        
        if not all([data_inicio1, data_fim1, data_inicio2, data_fim2]):
            return jsonify({'error': 'Parâmetros de datas obrigatórios'}), 400
        
        # 🔒 VALIDAÇÃO DE SEGURANÇA
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'erro': 'Empresa não selecionada'}), 403
        
        print(f"[COMPARATIVO] Empresa ID: {empresa_id}")
        
        try:
            data_inicio1 = datetime.fromisoformat(data_inicio1).date()
            data_fim1 = datetime.fromisoformat(data_fim1).date()
            data_inicio2 = datetime.fromisoformat(data_inicio2).date()
            data_fim2 = datetime.fromisoformat(data_fim2).date()
        except ValueError as e:
            print(f"[COMPARATIVO] Erro ao converter datas: {e}")
            return jsonify({'error': 'Formato de data inválido'}), 400
        
        print(f"[COMPARATIVO] Buscando lançamentos...")
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        print(f"[COMPARATIVO] Total de lançamentos: {len(lancamentos)}")
        
        def calcular_periodo(data_ini, data_fim):
            print(f"[COMPARATIVO] Calculando período: {data_ini} até {data_fim}")
            receitas = Decimal('0')
            despesas = Decimal('0')
            receitas_por_categoria = {}
            despesas_por_categoria = {}
            receitas_por_subcategoria = {}
            despesas_por_subcategoria = {}
            
            for l in lancamentos:
                try:
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
                except Exception as e:
                    print(f"[COMPARATIVO] Erro ao processar lançamento {l.id}: {e}")
                    continue
            
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
        
        print(f"[COMPARATIVO] Calculando período 1...")
        periodo1 = calcular_periodo(data_inicio1, data_fim1)
        print(f"[COMPARATIVO] Período 1 calculado - Receitas: {periodo1['receitas']}, Despesas: {periodo1['despesas']}")
        
        print(f"[COMPARATIVO] Calculando período 2...")
        periodo2 = calcular_periodo(data_inicio2, data_fim2)
        print(f"[COMPARATIVO] Período 2 calculado - Receitas: {periodo2['receitas']}, Despesas: {periodo2['despesas']}")
        
        # Calcular variações
        variacao_receitas = ((periodo2['receitas'] - periodo1['receitas']) / periodo1['receitas'] * 100) if periodo1['receitas'] > 0 else 0
        variacao_despesas = ((periodo2['despesas'] - periodo1['despesas']) / periodo1['despesas'] * 100) if periodo1['despesas'] > 0 else 0
        variacao_saldo = ((periodo2['saldo'] - periodo1['saldo']) / abs(periodo1['saldo']) * 100) if periodo1['saldo'] != 0 else 0
        
        print(f"[COMPARATIVO] Variações calculadas - Receitas: {variacao_receitas}%, Despesas: {variacao_despesas}%, Saldo: {variacao_saldo}%")
        
        resultado = {
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
        }
        
        print(f"[COMPARATIVO] Retornando resultado com sucesso")
        return jsonify(resultado)
        
    except Exception as e:
        print(f"[COMPARATIVO] ERRO CRÍTICO: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/relatorios/indicadores', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_indicadores():
    """Relatório de indicadores financeiros"""
    # 🔒 VALIDAÇÃO DE SEGURANÇA
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        contas = db.listar_contas_por_empresa(empresa_id=empresa_id)
        
        # Obter filtros de data
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
        
        hoje = date.today()
        
        if data_inicio_str and data_fim_str:
            inicio_mes = parse_date(data_inicio_str)
            fim_periodo = parse_date(data_fim_str)
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
    # 🔒 VALIDAÇÃO DE SEGURANÇA
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
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
    # 🔒 VALIDAÇÃO DE SEGURANÇA
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        from reportlab.lib import colors  # type: ignore
        from reportlab.lib.pagesizes import A4, landscape  # type: ignore
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer  # type: ignore
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
        from reportlab.lib.units import cm  # type: ignore
        from reportlab.pdfgen import canvas  # type: ignore
        from io import BytesIO
        
        clientes = db.listar_clientes(empresa_id=empresa_id)
        
        # Criar PDF em memória
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=0.5*cm, leftMargin=0.5*cm, topMargin=1*cm, bottomMargin=1*cm)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#2c3e50'), spaceAfter=15, alignment=1)
        elements.append(Paragraph(f'LISTA DE CLIENTES - {get_current_date_br()}', title_style))
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
        
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'clientes_{get_current_date_filename()}.pdf')
    
    except Exception as e:
        print(f"Erro ao exportar PDF: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/clientes/exportar/excel', methods=['GET'])
@require_permission('clientes_view')
def exportar_clientes_excel():
    """Exporta clientes para Excel"""
    # 🔒 VALIDAÇÃO DE SEGURANÇA
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        import openpyxl  # type: ignore
        from openpyxl.styles import Font, Alignment, PatternFill  # type: ignore
        from openpyxl.worksheet.worksheet import Worksheet  # type: ignore
        from io import BytesIO
        
        clientes = db.listar_clientes(empresa_id=empresa_id)
        
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
        
        return send_file(buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'clientes_{get_current_date_filename()}.xlsx')
    
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
        elements.append(Paragraph(f'LISTA DE FORNECEDORES - {get_current_date_br()}', title_style))
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
        
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'fornecedores_{get_current_date_filename()}.pdf')
    
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
        
        return send_file(buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'fornecedores_{get_current_date_filename()}.xlsx')
    
    except Exception as e:
        print(f"Erro ao exportar Excel: {e}")
        return jsonify({'error': str(e)}), 500


# === ROTAS DO MENU OPERACIONAL ===
# Rotas de Contratos movidas para app/routes/contratos.py
# Rotas de Sessões movidas para app/routes/sessoes.py

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


# ============================================================================
# RECURSOS HUMANOS - FUNCIONÁRIOS
# ============================================================================

@app.route('/api/rh/funcionarios', methods=['GET'])
def listar_funcionarios_rh():
    """Listar funcionários para uso em dropdowns (sem require_permission para permitir uso em modais)"""
    print("=" * 80)
    print("🔥 REQUISIÇÃO RECEBIDA: /api/rh/funcionarios")
    print("=" * 80)
    try:
        print("📡 Obtendo conexão com banco...")
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("🔍 Verificando total de funcionários na tabela...")
        # Primeiro, verificar se a tabela existe e tem dados
        cursor.execute("SELECT COUNT(*) as total FROM funcionarios")
        result = cursor.fetchone()
        total = result['total'] if isinstance(result, dict) else (result[0] if result else 0)
        print(f"🔍 Total de funcionários na tabela: {total}")
        
        # Buscar apenas colunas que existem (id, nome, ativo)
        cursor.execute("""
            SELECT id, nome, ativo
            FROM funcionarios
            WHERE ativo = true
            ORDER BY nome
        """)
        
        rows = cursor.fetchall()
        
        print(f"🔍 Total de funcionários ativos encontrados: {len(rows)}")
        
        # Converter para dicionários (apenas id e nome para dropdown)
        funcionarios = []
        for row in rows:
            if isinstance(row, dict):
                funcionario = {
                    'id': row['id'],
                    'nome': row['nome']
                }
                print(f"  ✅ Funcionário: {row['nome']} (ID: {row['id']}, Ativo: {row.get('ativo', True)})")
            else:
                funcionario = {
                    'id': row[0],
                    'nome': row[1]
                }
                print(f"  ✅ Funcionário: {row[1]} (ID: {row[0]}, Ativo: {row[2] if len(row) > 2 else True})")
            funcionarios.append(funcionario)
        
        cursor.close()
        conn.close()
        
        print(f"✅ Retornando {len(funcionarios)} funcionários")
        return jsonify({'success': True, 'data': funcionarios})
    except Exception as e:
        print(f"❌ Erro ao listar funcionários RH: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROTAS DE KITS - MOVIDAS PARA app/routes/kits.py
# ============================================================================
# As rotas de Kits foram extraídas para o Blueprint em app/routes/kits.py
# como parte da Fase 2 de otimização (refatoração modular)


# ============================================================================
# ENDPOINTS TEMPORÁRIOS PARA DEBUG E MIGRATIONS
# ⚠️ ESTES ENDPOINTS SÓ FUNCIONAM EM DESENVOLVIMENTO
# ============================================================================

def _check_debug_endpoint_allowed():
    """Verifica se endpoints de debug podem ser executados"""
    if IS_PRODUCTION:
        return jsonify({
            'success': False,
            'error': 'Endpoints de debug não disponíveis em produção',
            'message': 'Use migrations adequadas ou console admin'
        }), 403
    return None

@app.route('/api/debug/fix-kits-table', methods=['POST'])
@csrf_instance.exempt
def fix_kits_table():
    """
    Migration: Adiciona colunas 'descricao' e 'empresa_id' na tabela kits
    Bug descoberto na Fase 3 - código usa campos que não existem
    
    ATENCAO: DISPONÍVEL APENAS EM DESENVOLVIMENTO
    """
    # Bloquear em produção
    check = _check_debug_endpoint_allowed()
    if check:
        return check
    
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        results = {'steps': []}
        
        # 1. Adicionar coluna 'descricao'
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='kits' AND column_name='descricao'
            ) as existe
        """)
        result = cursor.fetchone()
        descricao_existe = result[0] if isinstance(result, tuple) else result['existe']
        
        if not descricao_existe:
            cursor.execute("ALTER TABLE kits ADD COLUMN descricao TEXT")
            results['steps'].append('✅ Coluna descricao adicionada')
        else:
            results['steps'].append('ℹ️ Coluna descricao já existe')
        
        # 2. Adicionar coluna 'empresa_id'
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='kits' AND column_name='empresa_id'
            ) as existe
        """)
        result = cursor.fetchone()
        empresa_id_existe = result[0] if isinstance(result, tuple) else result['existe']
        
        if not empresa_id_existe:
            cursor.execute("ALTER TABLE kits ADD COLUMN empresa_id INTEGER DEFAULT 1")
            results['steps'].append('✅ Coluna empresa_id adicionada')
        else:
            results['steps'].append('ℹ️ Coluna empresa_id já existe')
        
        # 3. Migrar dados de observacoes para descricao
        cursor.execute("""
            SELECT COUNT(*) FROM kits 
            WHERE observacoes IS NOT NULL 
            AND (descricao IS NULL OR descricao = '')
        """)
        result = cursor.fetchone()
        rows_to_migrate = result[0] if isinstance(result, tuple) else result['count']
        
        if rows_to_migrate > 0:
            cursor.execute("""
                UPDATE kits 
                SET descricao = observacoes 
                WHERE observacoes IS NOT NULL 
                AND (descricao IS NULL OR descricao = '')
            """)
            results['steps'].append(f'✅ {rows_to_migrate} registros migrados de observacoes → descricao')
        else:
            results['steps'].append('ℹ️ Nenhum dado para migrar')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Migration executada com sucesso',
            'results': results
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/debug/fix-p1-issues', methods=['POST'])
@csrf_instance.exempt
def fix_p1_issues():
    """
    Migration P1: Corrige bugs prioritários
    
    Funcionalidades:
    1. Adiciona empresa_id em todas as tabelas (multi-tenancy)
    2. Cria indexes para empresa_id
    3. Reporta campos que precisam de conversão manual (VARCHAR → FK)
    
    ATENCAO: DISPONÍVEL APENAS EM DESENVOLVIMENTO
    
    Returns:
        JSON com resultados detalhados da migration
    """
    # Bloquear em produção
    check = _check_debug_endpoint_allowed()
    if check:
        return check
    
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        results = {
            'multi_tenancy': [],
            'indexes': [],
            'warnings': []
        }
        
        # Lista de tabelas que precisam de empresa_id
        tables_to_fix = [
            'lancamentos',
            'categorias', 
            'subcategorias',
            'clientes',
            'fornecedores',
            'contratos',
            'sessoes',
            'produtos',
            'contas_bancarias',
            'usuarios',
            'equipamentos',
            'projetos'
        ]
        
        # 1. Adicionar empresa_id em todas as tabelas
        for table_name in tables_to_fix:
            try:
                # Verifica se coluna já existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = 'empresa_id'
                    ) as existe
                """, (table_name,))
                
                result = cursor.fetchone()
                # Tenta diferentes formas de acessar o resultado
                if isinstance(result, dict):
                    empresa_id_existe = result['existe']
                elif isinstance(result, tuple):
                    empresa_id_existe = result[0]
                else:
                    empresa_id_existe = bool(result)
                
                if not empresa_id_existe:
                    # Adiciona coluna empresa_id
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN empresa_id INTEGER NOT NULL DEFAULT 1")
                    results['multi_tenancy'].append(f'✅ {table_name}: empresa_id adicionado')
                else:
                    results['multi_tenancy'].append(f'ℹ️ {table_name}: empresa_id já existe')
                
                # Cria index para performance
                index_name = f'idx_{table_name}_empresa'
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = %s
                    ) as existe
                """, (index_name,))
                
                result = cursor.fetchone()
                if isinstance(result, dict):
                    index_existe = result['existe']
                elif isinstance(result, tuple):
                    index_existe = result[0]
                else:
                    index_existe = bool(result)
                
                if not index_existe:
                    cursor.execute(f"CREATE INDEX {index_name} ON {table_name}(empresa_id)")
                    results['indexes'].append(f'✅ Index {index_name} criado')
                else:
                    results['indexes'].append(f'ℹ️ Index {index_name} já existe')
                    
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                results['warnings'].append(f'⚠️ {table_name}: {type(e).__name__} - {str(e)}')
        
        # 2. Avisos sobre conversões VARCHAR → FK que precisam ser manuais
        fk_conversions_needed = [
            {
                'table': 'lancamentos',
                'column': 'categoria',
                'target': 'categorias',
                'reason': 'Campo VARCHAR precisa ser convertido para INTEGER FK'
            },
            {
                'table': 'lancamentos', 
                'column': 'subcategoria',
                'target': 'subcategorias',
                'reason': 'Campo VARCHAR precisa ser convertido para INTEGER FK'
            },
            {
                'table': 'lancamentos',
                'column': 'conta_bancaria', 
                'target': 'contas_bancarias',
                'reason': 'Campo VARCHAR precisa ser convertido para INTEGER FK'
            }
        ]
        
        results['warnings'].append('⚠️ CONVERSÕES MANUAIS NECESSÁRIAS:')
        for fk in fk_conversions_needed:
            results['warnings'].append(
                f"   • {fk['table']}.{fk['column']} → {fk['target']}.id: {fk['reason']}"
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Migration P1 executada com sucesso',
            'results': results,
            'summary': {
                'tables_updated': len([x for x in results['multi_tenancy'] if '✅' in x]),
                'tables_skipped': len([x for x in results['multi_tenancy'] if 'ℹ️' in x]),
                'indexes_created': len([x for x in results['indexes'] if '✅' in x]),
                'warnings': len(results['warnings'])
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/debug/extrair-schema', methods=['GET'])
def extrair_schema_debug():
    """
    Endpoint temporário para extrair schema do banco de dados
    Usado na Fase 3 da otimização para documentar o banco
    """
    try:
        import json
        from datetime import datetime
        
        conn = database.get_connection()
        cursor = conn.cursor()
        
        schema_info = {
            'data_extracao': datetime.now().isoformat(),
            'tabelas': []
        }
        
        # 1. Obter lista de todas as tabelas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tabelas = cursor.fetchall()
        
        for tabela_row in tabelas:
            tabela_nome = tabela_row[0] if isinstance(tabela_row, tuple) else tabela_row['table_name']
            
            tabela_info = {
                'nome': tabela_nome,
                'colunas': [],
                'constraints': [],
                'foreign_keys': [],
                'indexes': []
            }
            
            # 2. Obter colunas da tabela
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (tabela_nome,))
            
            colunas = cursor.fetchall()
            
            for coluna in colunas:
                if isinstance(coluna, dict):
                    col_info = {
                        'nome': coluna['column_name'],
                        'tipo': coluna['data_type'],
                        'tamanho': coluna.get('character_maximum_length'),
                        'nullable': coluna['is_nullable'] == 'YES',
                        'default': coluna.get('column_default')
                    }
                else:
                    col_info = {
                        'nome': coluna[0],
                        'tipo': coluna[1],
                        'tamanho': coluna[2],
                        'nullable': coluna[3] == 'YES',
                        'default': coluna[4]
                    }
                
                tabela_info['colunas'].append(col_info)
            
            # 3. Obter constraints
            cursor.execute("""
                SELECT 
                    tc.constraint_name,
                    tc.constraint_type,
                    kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = %s
                AND tc.constraint_type IN ('PRIMARY KEY', 'UNIQUE', 'CHECK')
            """, (tabela_nome,))
            
            constraints = cursor.fetchall()
            
            for constraint in constraints:
                if isinstance(constraint, dict):
                    const_info = {
                        'nome': constraint['constraint_name'],
                        'tipo': constraint['constraint_type'],
                        'coluna': constraint['column_name']
                    }
                else:
                    const_info = {
                        'nome': constraint[0],
                        'tipo': constraint[1],
                        'coluna': constraint[2]
                    }
                
                tabela_info['constraints'].append(const_info)
            
            # 4. Obter Foreign Keys
            cursor.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
            """, (tabela_nome,))
            
            fks = cursor.fetchall()
            
            for fk in fks:
                if isinstance(fk, dict):
                    fk_info = {
                        'coluna': fk['column_name'],
                        'referencia_tabela': fk['foreign_table_name'],
                        'referencia_coluna': fk['foreign_column_name']
                    }
                else:
                    fk_info = {
                        'coluna': fk[0],
                        'referencia_tabela': fk[1],
                        'referencia_coluna': fk[2]
                    }
                
                tabela_info['foreign_keys'].append(fk_info)
            
            schema_info['tabelas'].append(tabela_info)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'schema': schema_info
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        db_temp = DatabaseManager()
        conn = db_temp.get_connection()
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
        
        cursor.close()
        db_temp.return_to_pool(conn)
        
        # Ordenar por nome
        proprietarios_info.sort(key=lambda x: x['nome'])
        
        print(f"📋 Encontrados {len(proprietarios_info)} proprietários únicos")
        
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


@app.route('/api/admin/limpar-duplicatas-categorias', methods=['POST'])
@require_admin
def limpar_duplicatas_categorias():
    """
    Remove categorias duplicadas mantendo apenas a mais antiga (menor ID)
    Duplicata = mesmo nome + mesma empresa_id
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print('\n' + '='*80)
        print('🧹 ADMIN: Limpando categorias duplicadas')
        print('='*80)
        
        # Buscar todas as categorias
        cursor.execute("""
            SELECT id, nome, tipo, empresa_id 
            FROM categorias 
            ORDER BY empresa_id, nome, id
        """)
        categorias = cursor.fetchall()
        
        print(f'📊 Total de categorias no banco: {len(categorias)}')
        
        # Agrupar por (nome normalizado, empresa_id)
        grupos = {}
        for cat in categorias:
            chave = (cat['nome'].strip().upper(), cat['empresa_id'])
            if chave not in grupos:
                grupos[chave] = []
            grupos[chave].append(cat)
        
        # Filtrar apenas grupos com duplicatas
        duplicatas = {k: v for k, v in grupos.items() if len(v) > 1}
        
        if not duplicatas:
            print('✅ Nenhuma duplicata encontrada!')
            cursor.close()
            db.return_to_pool(conn)
            return jsonify({
                'success': True,
                'message': 'Nenhuma duplicata encontrada',
                'removidas': 0
            })
        
        print(f'⚠️  Encontradas {len(duplicatas)} categorias com duplicatas')
        
        ids_removidos = []
        detalhes = []
        
        for (nome, empresa), lista in duplicatas.items():
            # Ordenar por ID (manter o menor = mais antigo)
            lista_ordenada = sorted(lista, key=lambda x: x['id'])
            manter = lista_ordenada[0]
            excluir = lista_ordenada[1:]
            
            print(f'\n📁 {nome} (Empresa: {empresa})')
            print(f'   ✅ MANTER: ID={manter["id"]}')
            
            for cat in excluir:
                print(f'   ❌ EXCLUIR: ID={cat["id"]}')
                cursor.execute('DELETE FROM categorias WHERE id = %s', (cat['id'],))
                ids_removidos.append(cat['id'])
            
            detalhes.append({
                'nome': nome,
                'empresa_id': empresa,
                'mantido': manter['id'],
                'removidos': [c['id'] for c in excluir]
            })
        
        conn.commit()
        cursor.close()
        db.return_to_pool(conn)
        
        print(f'\n✅ Removidas {len(ids_removidos)} duplicatas!')
        print('='*80 + '\n')
        
        return jsonify({
            'success': True,
            'message': f'{len(ids_removidos)} categoria(s) duplicada(s) removida(s)',
            'removidas': len(ids_removidos),
            'detalhes': detalhes
        })
        
    except Exception as e:
        print(f'❌ Erro ao limpar duplicatas: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
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
    """Lista empresas - admin vê todas, outros usuários vêem apenas as suas"""
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
        
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Admin pode listar todas as empresas
        if usuario['tipo'] == 'admin':
            logger.info("   👑 Admin: listando TODAS as empresas")
            
            query = "SELECT id, razao_social, cnpj, plano, ativo FROM empresas"
            params = []
            
            # Filtros opcionais
            filtros = []
            if request.args.get('ativo'):
                filtros.append("ativo = %s")
                params.append(request.args.get('ativo') == 'true')
            
            if request.args.get('plano'):
                filtros.append("plano = %s")
                params.append(request.args.get('plano'))
            
            if filtros:
                query += " WHERE " + " AND ".join(filtros)
            
            query += " ORDER BY razao_social"
            
            logger.info(f"   🔍 Query: {query}")
            logger.info(f"   🔍 Params: {params}")
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            empresas = []
            for row in rows:
                empresas.append({
                    'id': row['id'],
                    'razao_social': row['razao_social'],
                    'cnpj': row['cnpj'],
                    'plano': row['plano'],
                    'ativo': row['ativo']
                })
            
            cursor.close()
            
            logger.info(f"   ✅ Retornando {len(empresas)} empresas")
            logger.info("="*80 + "\n")
            
            return jsonify(empresas)
        
        # Usuários não-admin veem apenas empresas às quais têm acesso
        else:
            logger.info("   👤 Usuário: listando apenas empresas vinculadas")
            usuario_id = usuario.get('id')
            
            cursor.execute("""
                SELECT DISTINCT
                    e.id,
                    e.razao_social,
                    e.cnpj,
                    e.plano,
                    e.ativo,
                    e.criado_em,
                    ue.is_empresa_padrao
                FROM empresas e
                INNER JOIN usuario_empresas ue ON ue.empresa_id = e.id
                WHERE ue.usuario_id = %s AND ue.acesso_ativo = TRUE
                ORDER BY e.razao_social
            """, (usuario_id,))
            
            rows = cursor.fetchall()
            empresas = []
            for row in rows:
                empresas.append({
                    'id': row['id'],
                    'razao_social': row['razao_social'],
                    'cnpj': row['cnpj'],
                    'plano': row['plano'],
                    'ativo': row['ativo'],
                    'criado_em': row['criado_em'].isoformat() if row['criado_em'] else None,
                    'is_empresa_padrao': row['is_empresa_padrao']
                })
            
            cursor.close()
            
            logger.info(f"   ✅ Retornando {len(empresas)} empresas vinculadas")
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
        
        # Admin pode ver qualquer empresa, usuário comum só se tiver vínculo ativo
        if usuario['tipo'] != 'admin':
            logger.info(f"[obter_empresa_api] Usuario nao e admin - verificando acesso...")
            from auth_functions import verificar_acesso_empresa
            tem_acesso = verificar_acesso_empresa(usuario['id'], empresa_id, auth_db)
            logger.info(f"[obter_empresa_api] Usuario tem acesso? {tem_acesso}")
            if not tem_acesso:
                logger.info(f"[obter_empresa_api] Acesso negado - sem vinculo ativo com empresa")
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
        dados = request.json
        
        if not dados:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # 🔒 POLÍTICA DE ACESSO:
        # - Admin pode editar QUALQUER campo de QUALQUER empresa
        # - Usuário comum pode editar APENAS o campo 'estado' da PRÓPRIA empresa
        
        if usuario['tipo'] != 'admin':
            # Verifica se tem acesso à empresa
            from auth_functions import verificar_acesso_empresa
            tem_acesso = verificar_acesso_empresa(usuario['id'], empresa_id, auth_db)
            
            if not tem_acesso:
                return jsonify({'error': 'Acesso negado'}), 403
            
            # Permite editar APENAS o campo 'estado' (UF)
            campos_permitidos = ['estado']
            campos_enviados = set(dados.keys())
            campos_proibidos = campos_enviados - set(campos_permitidos)
            
            if campos_proibidos:
                return jsonify({
                    'error': f'Usuário comum só pode editar os campos: {", ".join(campos_permitidos)}. ' +
                             f'Campos não permitidos: {", ".join(campos_proibidos)}'
                }), 403
            
            print(f"✅ [atualizar_empresa_api] Usuário comum editando campo permitido: {list(dados.keys())}")
        
        resultado = database.atualizar_empresa(empresa_id, dados)
        
        if resultado['success']:
            # Registrar log
            try:
                campos_alterados = ', '.join(dados.keys())
                auth_db.registrar_log_acesso(
                    usuario_id=usuario['id'],
                    acao='atualizar_empresa',
                    descricao=f"Empresa {empresa_id} - campos atualizados: {campos_alterados}",
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
        
        # Verificar acesso - admin ou usuário com vínculo ativo
        if usuario['tipo'] != 'admin':
            from auth_functions import verificar_acesso_empresa
            tem_acesso = verificar_acesso_empresa(usuario['id'], empresa_id, auth_db)
            if not tem_acesso:
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


# ============================================================================
# ENDPOINT TEMPORÁRIO PARA CRIAR USUÁRIO ADMIN (RAILWAY)
# ============================================================================
@app.route('/api/debug/criar-admin', methods=['POST'])
@csrf_instance.exempt
def criar_admin_inicial():
    """
    Endpoint temporário para criar usuário admin no Railway
    
    ATENCAO: DISPONÍVEL APENAS EM DESENVOLVIMENTO
    Em produção, use: python criar_admin_railway.py
    """
    # Bloquear em produção
    check = _check_debug_endpoint_allowed()
    if check:
        return check
    
    try:
        from auth_functions import hash_password, verificar_senha
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        senha = "admin123"
        password_hash = hash_password(senha)
        
        # Testar se o hash funciona
        teste_verificacao = verificar_senha(senha, password_hash)
        
        # Atualizar ou criar admin
        cursor.execute("""
            INSERT INTO usuarios (username, password_hash, tipo, nome_completo, email, ativo)
            VALUES ('admin', %s, 'admin', 'Administrador do Sistema', 'admin@sistema.com', TRUE)
            ON CONFLICT (username) DO UPDATE 
            SET password_hash = EXCLUDED.password_hash, ativo = TRUE
            RETURNING id
        """, (password_hash,))
        
        result = cursor.fetchone()
        admin_id = result['id'] if result else None
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Admin atualizado com sucesso',
            'admin_id': admin_id,
            'username': 'admin',
            'senha': senha,
            'hash_preview': password_hash[:50],
            'teste_verificacao_interna': teste_verificacao
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# ENDPOINT TEMPORÁRIO PARA ADICIONAR PERMISSÕES DE REGRAS (RAILWAY)
# ============================================================================
@app.route('/api/debug/adicionar-permissoes-regras', methods=['POST'])
@csrf_instance.exempt
def adicionar_permissoes_regras():
    """
    Endpoint temporário para adicionar permissões de regras de conciliação
    no campo JSONB permissoes_empresa da tabela usuario_empresas
    
    ATENCAO: DISPONÍVEL APENAS EM DESENVOLVIMENTO
    """
    # Bloquear em produção
    check = _check_debug_endpoint_allowed()
    if check:
        return check
    
    try:
        import json
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Buscar todos os vínculos usuario-empresa ativos
        cursor.execute("""
            SELECT usuario_id, empresa_id, permissoes_empresa
            FROM usuario_empresas
            WHERE ativo = TRUE
        """)
        vinculos = cursor.fetchall()
        
        # Permissões a adicionar
        novas_permissoes = [
            'regras_conciliacao_view',
            'regras_conciliacao_create', 
            'regras_conciliacao_edit',
            'regras_conciliacao_delete'
        ]
        
        atualizados = 0
        detalhes = []
        
        for vinculo in vinculos:
            usuario_id = vinculo['usuario_id']
            empresa_id = vinculo['empresa_id']
            permissoes_atual = vinculo['permissoes_empresa']
            
            # Converter JSONB para lista Python
            if permissoes_atual:
                if isinstance(permissoes_atual, str):
                    permissoes = json.loads(permissoes_atual)
                else:
                    permissoes = permissoes_atual
            else:
                permissoes = []
            
            # Adicionar novas permissões se não existirem
            permissoes_adicionadas = []
            for perm in novas_permissoes:
                if perm not in permissoes:
                    permissoes.append(perm)
                    permissoes_adicionadas.append(perm)
            
            if permissoes_adicionadas:
                # Atualizar no banco
                cursor.execute("""
                    UPDATE usuario_empresas
                    SET permissoes_empresa = %s::jsonb
                    WHERE usuario_id = %s AND empresa_id = %s
                """, (json.dumps(permissoes), usuario_id, empresa_id))
                
                atualizados += 1
                detalhes.append({
                    'usuario_id': usuario_id,
                    'empresa_id': empresa_id,
                    'permissoes_adicionadas': permissoes_adicionadas,
                    'total_permissoes': len(permissoes)
                })
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{atualizados} vínculo(s) atualizado(s)',
            'vinculos_total': len(vinculos),
            'vinculos_atualizados': atualizados,
            'detalhes': detalhes
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# ENDPOINT TEMPORÁRIO PARA FIX SUBCATEGORIAS (RAILWAY)
# ============================================================================
@app.route('/api/debug/fix-subcategorias-type', methods=['POST'])
@csrf.exempt
def fix_subcategorias_type():
    """
    Endpoint temporário para corrigir tipo da coluna subcategorias
    Altera de TEXT para VARCHAR(255)
    """
    try:
        db_instance = DatabaseManager()
        conn = db_instance.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Verificar tipo atual
        cursor.execute("""
            SELECT data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'categorias'
            AND column_name = 'subcategorias'
        """)
        
        result = cursor.fetchone()
        tipo_antes = result['data_type'] if result else 'não encontrado'
        tamanho_antes = result['character_maximum_length'] if result else None
        
        if tipo_antes == 'character varying':
            return jsonify({
                'success': True,
                'message': 'Coluna já está correta (character varying)',
                'tipo_atual': tipo_antes,
                'tamanho': tamanho_antes
            })
        
        # Alterar tipo
        cursor.execute("""
            ALTER TABLE categorias
            ALTER COLUMN subcategorias TYPE VARCHAR(255)
            USING subcategorias::VARCHAR(255)
        """)
        
        conn.commit()
        
        # Verificar resultado
        cursor.execute("""
            SELECT data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'categorias'
            AND column_name = 'subcategorias'
        """)
        
        result = cursor.fetchone()
        tipo_depois = result['data_type']
        tamanho_depois = result['character_maximum_length']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Coluna subcategorias alterada com sucesso!',
            'tipo_antes': tipo_antes,
            'tamanho_antes': tamanho_antes,
            'tipo_depois': tipo_depois,
            'tamanho_depois': tamanho_depois
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# ENDPOINT TEMPORÁRIO PARA VERIFICAR TABELA REGRAS_CONCILIACAO
# ============================================================================
@app.route('/api/debug/verificar-tabela-regras', methods=['GET'])
@csrf.exempt
def verificar_tabela_regras():
    """
    Endpoint temporário para diagnosticar tabela regras_conciliacao
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 1. Verificar se tabela existe
        cursor.execute("""
            SELECT COUNT(*) as existe
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'regras_conciliacao'
        """)
        tabela_existe = cursor.fetchone()['existe'] > 0
        
        resultado = {
            'tabela_existe': tabela_existe
        }
        
        if tabela_existe:
            # 2. Verificar estrutura da tabela
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'regras_conciliacao'
                ORDER BY ordinal_position
            """)
            colunas = cursor.fetchall()
            resultado['colunas'] = [dict(c) for c in colunas]
            
            # 3. Contar registros
            cursor.execute("SELECT COUNT(*) as total FROM regras_conciliacao")
            resultado['total_regras'] = cursor.fetchone()['total']
            
            # 4. Testar query simples
            try:
                cursor.execute("""
                    SELECT id, empresa_id, palavra_chave, ativo
                    FROM regras_conciliacao
                    LIMIT 5
                """)
                resultado['amostra'] = [dict(r) for r in cursor.fetchall()]
                resultado['query_ok'] = True
            except Exception as e:
                resultado['query_ok'] = False
                resultado['query_erro'] = str(e)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': resultado
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# ENDPOINT TEMPORÁRIO PARA VERIFICAR MÉTODOS DO DatabaseManager
# ============================================================================
@app.route('/api/debug/verificar-metodos-db', methods=['GET'])
@csrf.exempt
def verificar_metodos_db():
    """
    Endpoint temporário para verificar quais métodos o objeto db possui
    """
    try:
        # Listar todos os métodos do objeto db
        metodos_db = [m for m in dir(db) if not m.startswith('_')]
        
        # Verificar especificamente os métodos de regras
        metodos_regras = {
            'listar_regras_conciliacao': hasattr(db, 'listar_regras_conciliacao'),
            'criar_regra_conciliacao': hasattr(db, 'criar_regra_conciliacao'),
            'atualizar_regra_conciliacao': hasattr(db, 'atualizar_regra_conciliacao'),
            'excluir_regra_conciliacao': hasattr(db, 'excluir_regra_conciliacao'),
        }
        
        # Informações sobre o objeto db
        info_db = {
            'tipo': str(type(db)),
            'modulo': db.__class__.__module__,
            'classe': db.__class__.__name__,
        }
        
        return jsonify({
            'success': True,
            'data': {
                'info_db': info_db,
                'total_metodos': len(metodos_db),
                'metodos_regras': metodos_regras,
                'sample_metodos': metodos_db[:50]  # Primeiros 50 métodos
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# ENDPOINT TEMPORÁRIO PARA FORÇAR ATUALIZAÇÃO DE PERMISSÕES
# ============================================================================
@app.route('/api/debug/adicionar-permissoes-config-extrato', methods=['POST'])
@csrf.exempt
def adicionar_permissoes_config_extrato():
    """
    Endpoint temporário para forçar adição de permissões de config_extrato
    """
    try:
        from database_postgresql import execute_query
        
        # 1. Garantir que as permissões existem
        execute_query("""
            INSERT INTO permissoes (codigo, nome, descricao, categoria) VALUES
            ('config_extrato_bancario_view', 'Visualizar Configurações de Extrato', 'Permite visualizar configurações de extrato bancário', 'configuracoes'),
            ('config_extrato_bancario_edit', 'Editar Configurações de Extrato', 'Permite editar configurações de extrato bancário', 'configuracoes')
            ON CONFLICT (codigo) DO NOTHING
        """, fetch_all=False, allow_global=True)
        
        # 2. Adicionar permissões aos usuários ativos e contar
        result = execute_query("""
            WITH atualizar AS (
                UPDATE usuario_empresas
                SET permissoes_empresa = permissoes_empresa || 
                    jsonb_build_array('config_extrato_bancario_view', 'config_extrato_bancario_edit')
                WHERE ativo = TRUE
                  AND NOT (permissoes_empresa @> '["config_extrato_bancario_view"]'::jsonb)
                RETURNING id
            )
            SELECT COUNT(*) as atualizados FROM atualizar
        """, fetch_one=True, allow_global=True)
        
        rows_updated = result['atualizados'] if result else 0
        
        # 3. Verificar total
        result_total = execute_query("""
            SELECT COUNT(*) as total
            FROM usuario_empresas
            WHERE ativo = TRUE
              AND permissoes_empresa @> '["config_extrato_bancario_view"]'::jsonb
        """, fetch_one=True, allow_global=True)
        
        total = result_total['total'] if result_total else 0
        
        return jsonify({
            'success': True,
            'message': 'Permissões adicionadas com sucesso',
            'data': {
                'usuarios_atualizados': rows_updated,
                'total_com_permissoes': total
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# ENDPOINT PARA EXECUTAR MIGRATION DE CONFIG EXTRATO
# ============================================================================
@app.route('/api/debug/executar-migration-config-extrato', methods=['POST'])
@csrf.exempt
def executar_migration_config_extrato():
    """
    Endpoint para forçar execução da migration de config_extrato_bancario
    """
    try:
        from database_postgresql import execute_query
        import os
        
        # Ler arquivo SQL
        sql_file = os.path.join(os.path.dirname(__file__), 'migration_config_integracao_folha.sql')
        
        if not os.path.exists(sql_file):
            return jsonify({
                'success': False,
                'error': f'Arquivo não encontrado: {sql_file}'
            }), 404
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Executar SQL
        execute_query(sql_content, fetch_all=False, allow_global=True)
        
        # Verificar se tabela foi criada
        result = execute_query("""
            SELECT COUNT(*) as existe
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'config_extrato_bancario'
        """, fetch_one=True, allow_global=True)
        
        tabela_criada = result['existe'] == 1 if result else False
        
        # Verificar se coluna foi removida
        result_coluna = execute_query("""
            SELECT COUNT(*) as existe
            FROM information_schema.columns 
            WHERE table_name = 'regras_conciliacao' 
            AND column_name = 'usa_integracao_folha'
        """, fetch_one=True, allow_global=True)
        
        coluna_removida = result_coluna['existe'] == 0 if result_coluna else False
        
        # Contar registros criados
        result_config = execute_query("""
            SELECT COUNT(*) as total
            FROM config_extrato_bancario
        """, fetch_one=True, allow_global=True)
        
        configs_criadas = result_config['total'] if result_config else 0
        
        return jsonify({
            'success': True,
            'message': 'Migration executada com sucesso',
            'data': {
                'tabela_criada': tabela_criada,
                'coluna_removida': coluna_removida,
                'configs_criadas': configs_criadas,
                'sql_size': len(sql_content)
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/debug/listar-regras-raw', methods=['GET'])
@csrf.exempt
def listar_regras_raw():
    """
    Endpoint de debug para listar todas as regras diretamente do banco
    """
    try:
        from database_postgresql import execute_query
        
        empresa_id = request.args.get('empresa_id', type=int)
        
        if not empresa_id:
            return jsonify({
                'success': False,
                'error': 'empresa_id é obrigatório'
            }), 400
        
        # Query direta no banco
        query = """
            SELECT 
                id,
                empresa_id,
                palavra_chave,
                categoria,
                subcategoria,
                cliente_padrao,
                descricao,
                ativo,
                created_at,
                updated_at
            FROM regras_conciliacao
            WHERE empresa_id = %s
            ORDER BY id
        """
        
        regras = execute_query(query, (empresa_id,), fetch_all=True, allow_global=True)
        
        return jsonify({
            'success': True,
            'empresa_id': empresa_id,
            'total': len(regras) if regras else 0,
            'regras': regras or []
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# ENDPOINT DE STATUS DA MIGRAÇÃO DE SENHAS
# ============================================================================
@app.route('/api/admin/passwords/migration-status', methods=['GET'])
@require_admin
def password_migration_status():
    """Retorna status da migração de senhas SHA-256 → bcrypt"""
    try:
        from migration_upgrade_passwords import relatorio_hashes_pendentes
        
        stats = relatorio_hashes_pendentes(db)
        
        return jsonify({
            'success': True,
            'data': {
                'total_usuarios': stats['total_usuarios'],
                'usuarios_bcrypt': stats['usuarios_bcrypt'],
                'usuarios_sha256': stats['usuarios_sha256'],
                'usuarios_desconhecido': stats['usuarios_desconhecido'],
                'percentual_migrado': round(
                    (stats['usuarios_bcrypt'] / stats['total_usuarios'] * 100) 
                    if stats['total_usuarios'] > 0 else 100, 
                    2
                ),
                'pendentes': stats['pendentes']
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/admin/passwords/force-upgrade', methods=['POST'])
@require_admin
def force_password_upgrade():
    """Força upgrade de senha para um usuário específico"""
    try:
        from migration_upgrade_passwords import forcar_upgrade_usuario
        
        data = request.json
        username = data.get('username')
        nova_senha = data.get('nova_senha')
        
        if not username or not nova_senha:
            return jsonify({
                'success': False,
                'error': 'username e nova_senha são obrigatórios'
            }), 400
        
        sucesso = forcar_upgrade_usuario(username, nova_senha, db)
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': f'Senha de {username} atualizada com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Usuário não encontrado ou erro ao atualizar'
            }), 404
    
    except Exception as e:
        logger.error(f"Erro ao forçar upgrade de senha: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ENDPOINT PARA EXECUTAR MIGRATIONS
# ============================================================================
@app.route('/api/admin/migrations/evento-funcionarios', methods=['POST'])
@require_admin
def execute_migration_evento_funcionarios():
    """Executa migration para criar tabelas funcoes_evento e evento_funcionarios"""
    try:
        logger.info("🚀 Iniciando migration evento_funcionarios...")
        
        # Ler arquivo SQL
        sql_file = os.path.join(os.path.dirname(__file__), 'migration_evento_funcionarios.sql')
        
        if not os.path.exists(sql_file):
            return jsonify({
                'success': False,
                'error': f'Arquivo migration não encontrado: {sql_file}'
            }), 404
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Executar script
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql_script)
            conn.commit()
            
            # Verificar tabelas criadas
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('funcoes_evento', 'evento_funcionarios')
                ORDER BY table_name
            """)
            tabelas = cursor.fetchall()
            
            # Verificar funções inseridas
            cursor.execute("SELECT COUNT(*) as total FROM funcoes_evento")
            total_funcoes = cursor.fetchone()['total']
            
            logger.info(f"✅ Migration executada: {len(tabelas)} tabelas, {total_funcoes} funções")
            
            return jsonify({
                'success': True,
                'message': 'Migration executada com sucesso',
                'data': {
                    'tabelas_criadas': [t['table_name'] for t in tabelas],
                    'funcoes_inseridas': total_funcoes
                }
            })
            
        except Exception as e:
            conn.rollback()
            raise e
        
        finally:
            cursor.close()
            conn.close()
    
    except Exception as e:
        logger.error(f"❌ Erro ao executar migration: {e}")
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# ENDPOINT DE ANALYTICS - PERFORMANCE MONITORING
# ============================================================================
@app.route('/api/analytics/lazy-loading', methods=['POST'])
@require_auth
def log_lazy_loading_performance():
    """Recebe e armazena métricas de performance do lazy loading"""
    try:
        data = request.json
        usuario_id = get_usuario_logado()['id']
        
        # Log estruturado das métricas
        logger.info("lazy_loading_metrics", extra={
            'usuario_id': usuario_id,
            'session_duration': data.get('summary', {}).get('sessionDuration'),
            'total_pages': data.get('summary', {}).get('totalPagesLoaded'),
            'cache_hit_rate': data.get('cache', {}).get('hitRate'),
            'avg_load_time': data.get('performance', {}).get('avgLoadTime'),
            'errors': len(data.get('errors', []))
        })
        
        # Opcionalmente, armazenar em tabela de métricas
        # (se quiser análise histórica mais complexa)
        
        return jsonify({
            'success': True,
            'message': 'Métricas recebidas'
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar métricas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/lazy-loading/summary', methods=['GET'])
@require_admin
def get_lazy_loading_summary():
    """Retorna resumo de métricas de performance do lazy loading (admin only)"""
    try:
        # Aqui você pode implementar agregação de métricas
        # Por enquanto, retorna instruções de uso
        return jsonify({
            'success': True,
            'message': 'Métricas disponíveis nos logs estruturados',
            'instructions': {
                'log_query': 'Buscar por "lazy_loading_metrics" nos logs',
                'console_usage': [
                    'window.lazyLoadMonitors.default.printReport()',
                    'window.lazyLoadMonitors.default.sendToBackend()'
                ]
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# ROTAS NFS-e (Nota Fiscal de Serviço Eletrônica)
# ============================================================================

@app.route('/api/nfse/config', methods=['GET'])
@require_auth
def get_config_nfse():
    """Lista configurações de municípios da empresa"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({
                'success': False,
                'error': 'Empresa não selecionada'
            }), 400
        
        from nfse_functions import listar_municipios
        from database_postgresql import get_nfse_db_params
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()
        
        configs = listar_municipios(db_params, empresa_id)
        
        return jsonify({
            'success': True,
            'configs': configs
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar configs NFS-e: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nfse/config', methods=['POST'])
@require_auth
@require_permission('nfse_config')
def add_config_nfse():
    """Adiciona configuração de município"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({
                'success': False,
                'error': 'Empresa não selecionada'
            }), 400
        
        data = request.json
        
        # Validar campos obrigatórios
        required_fields = ['cnpj_cpf', 'codigo_municipio', 'nome_municipio', 
                          'uf', 'inscricao_municipal']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {field}'
                }), 400
        
        from nfse_functions import adicionar_municipio
        from database_postgresql import get_nfse_db_params
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()
        
        sucesso, config_id, erro = adicionar_municipio(
            db_params=db_params,
            empresa_id=empresa_id,
            cnpj_cpf=data['cnpj_cpf'],
            codigo_municipio=data['codigo_municipio'],
            nome_municipio=data['nome_municipio'],
            uf=data['uf'],
            inscricao_municipal=data['inscricao_municipal'],
            provedor=data.get('provedor'),
            url_customizada=data.get('url_customizada')
        )
        
        if sucesso:
            # Log de auditoria
            from nfse_functions import registrar_operacao
            registrar_operacao(
                db_params=db_params,
                empresa_id=empresa_id,
                usuario_id=usuario['id'],
                operacao='CONFIG',
                detalhes={'municipio': data['nome_municipio']},
                ip_address=request.remote_addr
            )
            
            return jsonify({
                'success': True,
                'config_id': config_id,
                'message': 'Município configurado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': erro
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao adicionar config NFS-e: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nfse/config/<int:config_id>', methods=['PUT'])
@require_auth
@require_permission('nfse_config')
def update_config_nfse(config_id):
    """Atualiza configuração de município"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({
                'success': False,
                'error': 'Empresa não selecionada'
            }), 400
        
        data = request.json
        
        # Validar campos obrigatórios
        required_fields = ['cnpj_cpf', 'codigo_municipio', 'nome_municipio', 
                          'uf', 'inscricao_municipal']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {field}'
                }), 400
        
        from nfse_functions import atualizar_municipio
        from database_postgresql import get_nfse_db_params
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()
        
        sucesso, erro = atualizar_municipio(
            db_params=db_params,
            empresa_id=empresa_id,
            config_id=config_id,
            cnpj_cpf=data['cnpj_cpf'],
            codigo_municipio=data['codigo_municipio'],
            nome_municipio=data['nome_municipio'],
            uf=data['uf'],
            inscricao_municipal=data['inscricao_municipal'],
            provedor=data.get('provedor'),
            url_customizada=data.get('url_customizada')
        )
        
        if sucesso:
            # Log de auditoria
            from nfse_functions import registrar_operacao
            registrar_operacao(
                db_params=db_params,
                empresa_id=empresa_id,
                usuario_id=usuario['id'],
                operacao='CONFIG_UPDATE',
                detalhes={'municipio': data['nome_municipio'], 'config_id': config_id},
                ip_address=request.remote_addr
            )
            
            return jsonify({
                'success': True,
                'config_id': config_id,
                'message': 'Município atualizado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': erro
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao atualizar config NFS-e: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nfse/config/<int:config_id>', methods=['DELETE'])
@require_auth
@require_permission('nfse_config')
def delete_config_nfse(config_id):
    """Remove configuração de município"""
    try:
        from nfse_functions import excluir_municipio
        from database_postgresql import get_nfse_db_params
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()
        
        sucesso, erro = excluir_municipio(db_params, config_id)
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': 'Configuração excluída'
            })
        else:
            return jsonify({
                'success': False,
                'error': erro
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao excluir config NFS-e: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nfse/buscar', methods=['POST'])
@require_auth
@require_permission('nfse_buscar')
def buscar_nfse():
    """Busca NFS-e via API SOAP municipal"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({
                'success': False,
                'error': 'Empresa não selecionada'
            }), 400
        
        data = request.json
        
        # Validar campos obrigatórios
        if not data.get('data_inicial') or not data.get('data_final'):
            return jsonify({
                'success': False,
                'error': 'Datas inicial e final são obrigatórias'
            }), 400
        
        # Buscar CNPJ da empresa
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT cnpj FROM empresas WHERE id = %s", (empresa_id,))
            empresa = cursor.fetchone()
            cursor.close()
        
        if not empresa:
            return jsonify({
                'success': False,
                'error': 'Empresa não encontrada'
            }), 404
        
        cnpj_prestador = empresa['cnpj'].replace('.', '').replace('/', '').replace('-', '')
        
        # Buscar certificado da empresa do banco de dados
        from nfse_functions import get_certificado_para_soap
        from database_postgresql import get_nfse_db_params
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()
        
        cert_data = get_certificado_para_soap(db_params, empresa_id)
        
        if cert_data:
            # Certificado do banco - salvar temporariamente para uso SOAP
            import tempfile
            pfx_bytes, cert_senha = cert_data
            temp_cert = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
            temp_cert.write(pfx_bytes)
            temp_cert.close()
            certificado_path = temp_cert.name
            certificado_senha = cert_senha
        else:
            # Fallback para variáveis de ambiente
            certificado_path = os.getenv('CERTIFICADO_A1_PATH', '/app/certificados/certificado.pfx')
            certificado_senha = os.getenv('CERTIFICADO_A1_SENHA', '')
            
            if not os.path.exists(certificado_path):
                return jsonify({
                    'success': False,
                    'error': 'Certificado A1 não configurado. Faça o upload do certificado digital nas Configurações da NFS-e.'
                }), 400
        
        # Converter datas
        data_inicial = datetime.strptime(data['data_inicial'], '%Y-%m-%d').date()
        data_final = datetime.strptime(data['data_final'], '%Y-%m-%d').date()
        
        # Municípios específicos ou todos
        codigos_municipios = data.get('codigos_municipios')
        
        # Verificar método de busca (SOAP municipal ou Ambiente Nacional)
        metodo = data.get('metodo', 'soap')  # Padrão: SOAP municipal
        
        if metodo == 'ambiente_nacional':
            # 🌐 BUSCA VIA AMBIENTE NACIONAL (API REST)
            # Usa consulta incremental por NSU, similar a NF-e e CT-e
            # Vantagem: uma única API para todos os municípios
            from nfse_functions import buscar_nfse_ambiente_nacional
            
            logger.info("🌐 Usando Ambiente Nacional (API REST) para busca de NFS-e")
            
            resultado = buscar_nfse_ambiente_nacional(
                db_params=db_params,
                empresa_id=empresa_id,
                cnpj_informante=cnpj_prestador,
                certificado_path=certificado_path,
                certificado_senha=certificado_senha,
                ambiente=data.get('ambiente', 'producao'),
                busca_completa=data.get('busca_completa', False),
                max_documentos=data.get('max_documentos', 50)
            )
        else:
            # 📡 BUSCA VIA SOAP MUNICIPAL (método tradicional)
            # Requer configuração de URL para cada município
            from nfse_functions import buscar_nfse_periodo
            
            logger.info("📡 Usando APIs SOAP municipais para busca de NFS-e")
            
            resultado = buscar_nfse_periodo(
                db_params=db_params,
                empresa_id=empresa_id,
                cnpj_prestador=cnpj_prestador,
                data_inicial=data_inicial,
                data_final=data_final,
                certificado_path=certificado_path,
                certificado_senha=certificado_senha,
                codigos_municipios=codigos_municipios
            )
        
        # Limpar arquivo temporário de certificado se foi criado
        if cert_data and os.path.exists(certificado_path):
            try:
                os.unlink(certificado_path)
            except:
                pass
        
        # Log de auditoria
        from nfse_functions import registrar_operacao
        registrar_operacao(
            db_params=db_params,
            empresa_id=empresa_id,
            usuario_id=usuario['id'],
            operacao='BUSCA',
            detalhes={
                'data_inicial': data['data_inicial'],
                'data_final': data['data_final'],
                'total_nfse': resultado['total_nfse']
            },
            ip_address=request.remote_addr
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao buscar NFS-e: {e}")
        capture_exception(e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nfse/consultar', methods=['POST'])
@require_auth
@require_permission('nfse_view')
def consultar_nfse():
    """Consulta NFS-e armazenadas localmente (sem buscar via API)"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({
                'success': False,
                'error': 'Empresa não selecionada'
            }), 400
        
        data = request.json
        
        from nfse_functions import consultar_nfse_periodo
        from datetime import datetime
        from database_postgresql import get_nfse_db_params
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()
        
        # Converter datas
        data_inicial = datetime.strptime(data['data_inicial'], '%Y-%m-%d').date()
        data_final = datetime.strptime(data['data_final'], '%Y-%m-%d').date()
        
        # Parâmetros de paginação (None = sem limite)
        limit = data.get('limit')  # None por padrão = busca todos
        offset = data.get('offset', 0)
        
        # Consultar banco local
        nfses = consultar_nfse_periodo(
            db_params=db_params,
            empresa_id=empresa_id,
            data_inicial=data_inicial,
            data_final=data_final,
            codigo_municipio=data.get('codigo_municipio'),
            limit=limit,
            offset=offset
        )
        
        # Converter objetos datetime para string (JSON serialization)
        for nfse in nfses:
            for key, value in nfse.items():
                if isinstance(value, (datetime, date)):
                    nfse[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    nfse[key] = float(value)
        
        return jsonify({
            'success': True,
            'nfses': nfses,
            'total': len(nfses)
        })
        
    except Exception as e:
        logger.error(f"Erro ao consultar NFS-e: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nfse/diagnostico', methods=['POST'])
@require_auth
@require_permission('nfse_view')
def diagnostico_nfse():
    """Diagnóstico detalhado de NFS-e para identificar omissões"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({
                'success': False,
                'error': 'Empresa não selecionada'
            }), 400
        
        data = request.json
        
        from datetime import datetime
        from database_postgresql import get_nfse_db_params
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        db_params = get_nfse_db_params()
        
        # Converter datas
        data_inicial = datetime.strptime(data['data_inicial'], '%Y-%m-%d').date()
        data_final = datetime.strptime(data['data_final'], '%Y-%m-%d').date()
        codigo_municipio = data.get('codigo_municipio')
        
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Total por situação
        sql = """
            SELECT 
                situacao,
                COUNT(*) as total,
                SUM(valor_servico) as valor_total,
                SUM(valor_iss) as iss_total
            FROM nfse_baixadas
            WHERE empresa_id = %s
            AND data_competencia BETWEEN %s AND %s
        """
        params = [empresa_id, data_inicial, data_final]
        
        if codigo_municipio:
            sql += " AND codigo_municipio = %s"
            params.append(codigo_municipio)
        
        sql += " GROUP BY situacao ORDER BY total DESC"
        
        cursor.execute(sql, tuple(params))
        por_situacao = [dict(row) for row in cursor.fetchall()]
        
        # 2. Total geral SEM filtro de situação
        sql_total = """
            SELECT 
                COUNT(*) as total,
                SUM(valor_servico) as valor_total,
                SUM(valor_iss) as iss_total
            FROM nfse_baixadas
            WHERE empresa_id = %s
            AND data_competencia BETWEEN %s AND %s
        """
        params_total = [empresa_id, data_inicial, data_final]
        
        if codigo_municipio:
            sql_total += " AND codigo_municipio = %s"
            params_total.append(codigo_municipio)
        
        cursor.execute(sql_total, tuple(params_total))
        total_geral = dict(cursor.fetchone())
        
        # 3. Total APENAS NORMAL (o que a interface mostra)
        sql_normal = """
            SELECT 
                COUNT(*) as total,
                SUM(valor_servico) as valor_total,
                SUM(valor_iss) as iss_total
            FROM nfse_baixadas
            WHERE empresa_id = %s
            AND data_competencia BETWEEN %s AND %s
            AND situacao = 'NORMAL'
        """
        params_normal = [empresa_id, data_inicial, data_final]
        
        if codigo_municipio:
            sql_normal += " AND codigo_municipio = %s"
            params_normal.append(codigo_municipio)
        
        cursor.execute(sql_normal, tuple(params_normal))
        total_normal = dict(cursor.fetchone())
        
        # 4. Mostrar notas CANCELADAS/SUBSTITUÍDAS se houver
        sql_outras = """
            SELECT 
                numero_nfse,
                data_emissao,
                razao_social_tomador,
                valor_servico,
                situacao
            FROM nfse_baixadas
            WHERE empresa_id = %s
            AND data_competencia BETWEEN %s AND %s
            AND situacao != 'NORMAL'
            ORDER BY data_emissao DESC
            LIMIT 20
        """
        params_outras = [empresa_id, data_inicial, data_final]
        
        if codigo_municipio:
            sql_outras += " AND codigo_municipio = %s"
            params_outras.append(codigo_municipio)
        
        cursor.execute(sql_outras, tuple(params_outras))
        notas_outras_situacoes = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        # Converter valores Decimal para float
        for item in por_situacao:
            for key, value in item.items():
                if isinstance(value, Decimal):
                    item[key] = float(value)
        
        for key, value in total_geral.items():
            if isinstance(value, Decimal):
                total_geral[key] = float(value)
        
        for key, value in total_normal.items():
            if isinstance(value, Decimal):
                total_normal[key] = float(value)
        
        for nota in notas_outras_situacoes:
            for key, value in nota.items():
                if isinstance(value, (datetime, date)):
                    nota[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    nota[key] = float(value)
        
        omitidas = total_geral['total'] - total_normal['total']
        
        resultado = {
            'success': True,
            'total_banco': total_geral['total'],
            'total_interface': total_normal['total'],
            'total_omitidas': omitidas,
            'por_situacao': por_situacao,
            'total_geral': total_geral,
            'total_normal': total_normal,
            'exemplos_omitidas': notas_outras_situacoes if omitidas > 0 else []
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro no diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nfse/<int:nfse_id>', methods=['GET'])
@require_auth
@require_permission('nfse_view')
def get_nfse_detalhes(nfse_id):
    """Retorna detalhes completos de uma NFS-e"""
    try:
        from nfse_functions import get_detalhes_nfse
        from database_postgresql import get_nfse_db_params
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()
        
        nfse = get_detalhes_nfse(db_params, nfse_id)
        
        if not nfse:
            return jsonify({
                'success': False,
                'error': 'NFS-e não encontrada'
            }), 404
        
        # Converter objetos datetime para string
        for key, value in nfse.items():
            if isinstance(value, (datetime, date)):
                nfse[key] = value.isoformat()
            elif isinstance(value, Decimal):
                nfse[key] = float(value)
        
        return jsonify({
            'success': True,
            'nfse': nfse
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar detalhes NFS-e: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nfse/<int:nfse_id>', methods=['DELETE'])
@require_auth
@require_permission('nfse_delete')
def excluir_nfse(nfse_id):
    """Exclui uma NFS-e (banco de dados + arquivos XML e PDF)"""
    try:
        from nfse_database import NFSeDatabase
        from database_postgresql import get_nfse_db_params
        import os
        
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({
                'success': False,
                'error': 'Empresa não selecionada'
            }), 403
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()
        
        with NFSeDatabase(db_params) as db:
            # Buscar informações da NFS-e antes de excluir (para deletar arquivos)
            sql_select = """
                SELECT xml_path, numero_nfse, cnpj_prestador, codigo_municipio, data_emissao
                FROM nfse_baixadas 
                WHERE id = %s AND empresa_id = %s
            """
            
            with db.conn.cursor() as cursor:
                cursor.execute(sql_select, (nfse_id, empresa_id))
                nfse_data = cursor.fetchone()
                
                if not nfse_data:
                    return jsonify({
                        'success': False,
                        'error': 'NFS-e não encontrada ou não pertence à empresa atual'
                    }), 404
                
                xml_path, numero_nfse, cnpj_prestador, codigo_municipio, data_emissao = nfse_data
                
                # Excluir do banco de dados
                success = db.excluir_nfse(nfse_id, empresa_id)
                
                if not success:
                    return jsonify({
                        'success': False,
                        'error': 'Erro ao excluir NFS-e do banco de dados'
                    }), 500
                
                # Tentar excluir arquivos XML e PDF
                arquivos_excluidos = []
                arquivos_nao_encontrados = []
                
                # Montar caminhos dos arquivos
                # Formato: storage/nfse/{CNPJ}/{CODIGO_MUNICIPIO}/{ANO}/{MES}/
                if data_emissao:
                    ano = data_emissao.year if hasattr(data_emissao, 'year') else data_emissao[:4]
                    mes = f"{data_emissao.month:02d}" if hasattr(data_emissao, 'month') else data_emissao[5:7]
                    
                    base_dir = f"storage/nfse/{cnpj_prestador}/{codigo_municipio}/{ano}/{mes}"
                    
                    # Nome dos arquivos
                    xml_filename = f"NFS-e_{numero_nfse}.xml"
                    pdf_filename = f"NFS-e_{numero_nfse}.pdf"
                    
                    xml_full_path = os.path.join(base_dir, xml_filename)
                    pdf_full_path = os.path.join(base_dir, pdf_filename)
                    
                    # Tentar excluir XML
                    if os.path.exists(xml_full_path):
                        try:
                            os.remove(xml_full_path)
                            arquivos_excluidos.append(xml_filename)
                            logger.info(f"🗑️ XML excluído: {xml_full_path}")
                        except Exception as e:
                            logger.warning(f"⚠️ Erro ao excluir XML: {e}")
                    else:
                        arquivos_nao_encontrados.append(xml_filename)
                        logger.warning(f"⚠️ XML não encontrado: {xml_full_path}")
                    
                    # Tentar excluir PDF
                    if os.path.exists(pdf_full_path):
                        try:
                            os.remove(pdf_full_path)
                            arquivos_excluidos.append(pdf_filename)
                            logger.info(f"🗑️ PDF excluído: {pdf_full_path}")
                        except Exception as e:
                            logger.warning(f"⚠️ Erro ao excluir PDF: {e}")
                    else:
                        arquivos_nao_encontrados.append(pdf_filename)
                        logger.warning(f"⚠️ PDF não encontrado: {pdf_full_path}")
        
        mensagem = f"NFS-e {numero_nfse} excluída com sucesso!"
        if arquivos_excluidos:
            mensagem += f" Arquivos removidos: {', '.join(arquivos_excluidos)}."
        if arquivos_nao_encontrados:
            mensagem += f" Arquivos não encontrados: {', '.join(arquivos_nao_encontrados)}."
        
        logger.info(f"✅ {mensagem}")
        
        return jsonify({
            'success': True,
            'message': mensagem,
            'arquivos_excluidos': arquivos_excluidos,
            'arquivos_nao_encontrados': arquivos_nao_encontrados
        })
        
    except Exception as e:
        logger.error(f"Erro ao excluir NFS-e: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nfse/all', methods=['DELETE'])
@require_auth
@require_permission('nfse_delete')
def apagar_todas_nfse():
    """Apaga TODAS as NFS-e do período selecionado (banco de dados + arquivos)"""
    try:
        from nfse_database import NFSeDatabase
        from database_postgresql import get_nfse_db_params
        import os
        from datetime import datetime
        
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({
                'success': False,
                'error': 'Empresa não selecionada'
            }), 403
        
        # Pegar parâmetros
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        codigo_municipio = request.args.get('codigo_municipio', '')
        
        if not data_inicial or not data_final:
            return jsonify({
                'success': False,
                'error': 'Data inicial e final são obrigatórias'
            }), 400
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()
        
        with NFSeDatabase(db_params) as db:
            # Buscar TODAS as NFS-e do período
            sql_select = """
                SELECT id, xml_path, numero_nfse, cnpj_prestador, codigo_municipio, data_emissao
                FROM nfse_baixadas 
                WHERE empresa_id = %s 
                AND data_emissao >= %s 
                AND data_emissao <= %s
            """
            params = [empresa_id, data_inicial, data_final]
            
            if codigo_municipio:
                sql_select += " AND codigo_municipio = %s"
                params.append(codigo_municipio)
            
            with db.conn.cursor() as cursor:
                cursor.execute(sql_select, params)
                nfse_list = cursor.fetchall()
                
                if not nfse_list:
                    return jsonify({
                        'success': True,
                        'message': 'Nenhuma NFS-e encontrada no período',
                        'total_excluidas': 0,
                        'total_arquivos_excluidos': 0
                    })
                
                total_excluidas = 0
                total_arquivos_excluidos = 0
                erros = []
                
                logger.info(f"🗑️ Iniciando exclusão de {len(nfse_list)} NFS-e(s) do período {data_inicial} a {data_final}")
                
                # Excluir cada NFS-e
                for nfse_data in nfse_list:
                    nfse_id, xml_path, numero_nfse, cnpj_prestador, codigo_mun, data_emissao = nfse_data
                    
                    try:
                        # Excluir do banco
                        success = db.excluir_nfse(nfse_id, empresa_id)
                        
                        if success:
                            total_excluidas += 1
                            
                            # Tentar excluir arquivos
                            if data_emissao:
                                ano = data_emissao.year if hasattr(data_emissao, 'year') else data_emissao[:4]
                                mes = f"{data_emissao.month:02d}" if hasattr(data_emissao, 'month') else data_emissao[5:7]
                                
                                base_dir = f"storage/nfse/{cnpj_prestador}/{codigo_mun}/{ano}/{mes}"
                                xml_full_path = os.path.join(base_dir, f"NFS-e_{numero_nfse}.xml")
                                pdf_full_path = os.path.join(base_dir, f"NFS-e_{numero_nfse}.pdf")
                                
                                # Excluir XML
                                if os.path.exists(xml_full_path):
                                    try:
                                        os.remove(xml_full_path)
                                        total_arquivos_excluidos += 1
                                    except Exception as e:
                                        logger.warning(f"⚠️ Erro ao excluir XML {numero_nfse}: {e}")
                                
                                # Excluir PDF
                                if os.path.exists(pdf_full_path):
                                    try:
                                        os.remove(pdf_full_path)
                                        total_arquivos_excluidos += 1
                                    except Exception as e:
                                        logger.warning(f"⚠️ Erro ao excluir PDF {numero_nfse}: {e}")
                        
                    except Exception as e:
                        erro_msg = f"NFS-e {numero_nfse}: {str(e)}"
                        erros.append(erro_msg)
                        logger.error(f"❌ Erro ao excluir NFS-e {numero_nfse}: {e}")
                
                mensagem = f"{total_excluidas} NFS-e(s) excluída(s) com sucesso! {total_arquivos_excluidos} arquivo(s) removido(s)."
                
                if erros:
                    mensagem += f" Erros: {len(erros)}"
                
                logger.info(f"✅ {mensagem}")
                
                return jsonify({
                    'success': True,
                    'message': mensagem,
                    'total_excluidas': total_excluidas,
                    'total_arquivos_excluidos': total_arquivos_excluidos,
                    'erros': erros if erros else []
                })
        
    except Exception as e:
        logger.error(f"Erro ao apagar todas as NFS-e: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nfse/resumo-mensal', methods=['POST'])
@require_auth
@require_permission('nfse_view')
def get_resumo_mensal_nfse():
    """Retorna resumo mensal de NFS-e"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({
                'success': False,
                'error': 'Empresa não selecionada'
            }), 400
        
        data = request.json
        ano = data.get('ano')
        mes = data.get('mes')
        
        if not ano or not mes:
            return jsonify({
                'success': False,
                'error': 'Ano e mês são obrigatórios'
            }), 400
        
        from nfse_functions import get_resumo_mensal
        
        from database_postgresql import get_nfse_db_params
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()
        
        resumo = get_resumo_mensal(db_params, empresa_id, ano, mes)
        
        # Converter Decimal para float
        for key, value in resumo.items():
            if isinstance(value, Decimal):
                resumo[key] = float(value)
        
        return jsonify({
            'success': True,
            'resumo': resumo
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar resumo mensal: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nfse/export/excel', methods=['POST'])
@require_auth
@require_permission('nfse_export')
def export_nfse_excel():
    """Exporta NFS-e para Excel/CSV"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({
                'success': False,
                'error': 'Empresa não selecionada'
            }), 400
        
        data = request.json
        
        from nfse_functions import exportar_nfse_excel
        from datetime import datetime
        from database_postgresql import get_nfse_db_params
        import tempfile
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()
        
        # Converter datas
        data_inicial = datetime.strptime(data['data_inicial'], '%Y-%m-%d').date()
        data_final = datetime.strptime(data['data_final'], '%Y-%m-%d').date()
        
        # Criar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        caminho_arquivo = temp_file.name
        temp_file.close()
        
        # Exportar
        sucesso, erro = exportar_nfse_excel(
            db_params=db_params,
            empresa_id=empresa_id,
            data_inicial=data_inicial,
            data_final=data_final,
            caminho_arquivo=caminho_arquivo
        )
        
        if sucesso:
            # Log de auditoria
            from nfse_functions import registrar_operacao
            registrar_operacao(
                db_params=db_params,
                empresa_id=empresa_id,
                usuario_id=usuario['id'],
                operacao='EXPORT',
                detalhes={'formato': 'CSV'},
                ip_address=request.remote_addr
            )
            
            return send_file(
                caminho_arquivo,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'nfse_{data_inicial}_{data_final}.csv'
            )
        else:
            return jsonify({
                'success': False,
                'error': erro
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao exportar NFS-e: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nfse/export/xml', methods=['POST'])
@require_auth
@require_permission('nfse_export')
def export_nfse_xml():
    """Exporta XMLs de NFS-e para arquivo ZIP"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({
                'success': False,
                'error': 'Empresa não selecionada'
            }), 400
        
        data = request.json
        
        from nfse_functions import exportar_xmls_zip
        from datetime import datetime
        from database_postgresql import get_nfse_db_params
        import tempfile
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()
        
        # Converter datas
        data_inicial = datetime.strptime(data['data_inicial'], '%Y-%m-%d').date()
        data_final = datetime.strptime(data['data_final'], '%Y-%m-%d').date()
        
        # Criar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        caminho_arquivo = temp_file.name
        temp_file.close()
        
        # Exportar
        sucesso, erro = exportar_xmls_zip(
            db_params=db_params,
            empresa_id=empresa_id,
            data_inicial=data_inicial,
            data_final=data_final,
            caminho_arquivo=caminho_arquivo
        )
        
        if sucesso:
            # Log de auditoria
            from nfse_functions import registrar_operacao
            registrar_operacao(
                db_params=db_params,
                empresa_id=empresa_id,
                usuario_id=usuario['id'],
                operacao='EXPORT',
                detalhes={'formato': 'XML_ZIP'},
                ip_address=request.remote_addr
            )
            
            return send_file(
                caminho_arquivo,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f'nfse_xmls_{data_inicial}_{data_final}.zip'
            )
        else:
            return jsonify({
                'success': False,
                'error': erro
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao exportar XMLs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ROTAS NFS-e - CERTIFICADO DIGITAL A1
# ============================================================================

@app.route('/api/nfse/certificado/upload', methods=['POST'])
@require_auth
@require_permission('nfse_config')
def upload_certificado_nfse():
    """Upload de certificado digital A1 (.pfx/.p12)"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        # Verificar se o arquivo foi enviado
        if 'certificado' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo de certificado enviado'}), 400
        
        arquivo = request.files['certificado']
        senha = request.form.get('senha', '')
        
        if not arquivo.filename:
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        
        if not senha:
            return jsonify({'success': False, 'error': 'Senha do certificado é obrigatória'}), 400
        
        # Validar extensão
        extensao = arquivo.filename.rsplit('.', 1)[-1].lower() if '.' in arquivo.filename else ''
        if extensao not in ('pfx', 'p12'):
            return jsonify({'success': False, 'error': 'Formato inválido. Use arquivo .pfx ou .p12'}), 400
        
        # Ler bytes do arquivo
        pfx_bytes = arquivo.read()
        
        if len(pfx_bytes) == 0:
            return jsonify({'success': False, 'error': 'Arquivo vazio'}), 400
        
        if len(pfx_bytes) > 10 * 1024 * 1024:  # 10MB max
            return jsonify({'success': False, 'error': 'Arquivo muito grande (máximo 10MB)'}), 400
        
        from nfse_functions import upload_certificado, registrar_operacao
        from database_postgresql import get_nfse_db_params
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()
        # Remover 'dsn' se existir (NFSeDatabase espera parâmetros individuais)
        
        sucesso, info, erro = upload_certificado(db_params, empresa_id, pfx_bytes, senha)
        
        if sucesso:
            # Log de auditoria
            registrar_operacao(
                db_params=db_params,
                empresa_id=empresa_id,
                usuario_id=usuario['id'],
                operacao='CONFIG',
                detalhes={
                    'acao': 'upload_certificado',
                    'cnpj': info.get('cnpj'),
                    'municipio': info.get('nome_municipio'),
                    'validade_fim': info.get('validade_fim'),
                    'config_criada': info.get('config_criada', False)
                },
                ip_address=request.remote_addr
            )
            
            # Mensagem personalizada se criou configuração automaticamente
            message = 'Certificado carregado com sucesso!'
            if info.get('config_criada'):
                message += f' Município {info.get("nome_municipio")} configurado automaticamente. Complete a Inscrição Municipal em Configurações.'
            elif info.get('codigo_municipio'):
                message += ' Lembre-se de configurar o município em Configurações.'
            
            return jsonify({
                'success': True,
                'message': message,
                'certificado': {
                    'id': info.get('cert_id'),
                    'cnpj': info.get('cnpj'),
                    'razao_social': info.get('razao_social'),
                    'emitente': info.get('emitente'),
                    'validade_inicio': info.get('validade_inicio'),
                    'validade_fim': info.get('validade_fim'),
                    'codigo_municipio': info.get('codigo_municipio'),
                    'nome_municipio': info.get('nome_municipio'),
                    'uf': info.get('uf'),
                    'config_criada': info.get('config_criada', False),
                    'config_id': info.get('config_id')
                }
            })
        else:
            return jsonify({'success': False, 'error': erro}), 400
        
    except Exception as e:
        logger.error(f"Erro ao fazer upload de certificado: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/nfse/certificado', methods=['GET'])
@require_auth
def get_certificado_nfse():
    """Retorna informações do certificado ativo da empresa"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        from nfse_functions import get_certificado_info
        from database_postgresql import get_nfse_db_params
        
        # Usar configuração centralizada do banco
        db_params = get_nfse_db_params()  # Remover DSN se existir
        
        cert = get_certificado_info(db_params, empresa_id)
        
        return jsonify({
            'success': True,
            'certificado': cert
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar certificado: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/nfse/certificado/<int:cert_id>', methods=['DELETE'])
@require_auth
@require_permission('nfse_config')
def delete_certificado_nfse(cert_id):
    """Remove certificado digital"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        from nfse_functions import excluir_certificado_empresa, registrar_operacao
        from database_postgresql import get_nfse_db_params
        
        db_params = get_nfse_db_params()
        
        sucesso = excluir_certificado_empresa(db_params, cert_id)
        
        if sucesso:
            registrar_operacao(
                db_params=db_params,
                empresa_id=empresa_id,
                usuario_id=usuario['id'],
                operacao='CONFIG',
                detalhes={'acao': 'excluir_certificado', 'cert_id': cert_id},
                ip_address=request.remote_addr
            )
            return jsonify({'success': True, 'message': 'Certificado removido'})
        else:
            return jsonify({'success': False, 'error': 'Certificado não encontrado'}), 404
        
    except Exception as e:
        logger.error(f"Erro ao excluir certificado: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROTAS NFS-e - GERAÇÃO DE PDF (DANFSE)
# ============================================================================

@app.route('/api/nfse/<int:nfse_id>/pdf', methods=['GET'])
@require_auth
@require_permission('nfse_view')
def gerar_pdf_nfse_route(nfse_id):
    """Gera e retorna o PDF (DANFSE) de uma NFS-e"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        from nfse_functions import gerar_pdf_nfse
        from database_postgresql import get_nfse_db_params
        
        db_params = get_nfse_db_params()
        
        pdf_bytes = gerar_pdf_nfse(db_params, nfse_id)
        
        if pdf_bytes:
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(pdf_bytes)
            temp_file.close()
            
            return send_file(
                temp_file.name,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'nfse_{nfse_id}.pdf'
            )
        else:
            return jsonify({
                'success': False,
                'error': 'Não foi possível gerar o PDF desta NFS-e'
            }), 400
        
    except Exception as e:
        logger.error(f"Erro ao gerar PDF NFS-e: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ROTAS CONTABILIDADE - PLANO DE CONTAS
# ============================================================================

@app.route('/api/contabilidade/versoes', methods=['GET'])
@require_auth
def listar_versoes_plano():
    """Lista versões do plano de contas"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        from contabilidade_functions import listar_versoes
        versoes = listar_versoes(empresa_id)
        return jsonify({'success': True, 'versoes': versoes})
    except Exception as e:
        logger.error(f"Erro ao listar versões: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/versoes', methods=['POST'])
@require_auth
def criar_versao_plano():
    """Cria nova versão do plano de contas"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        dados = request.get_json()
        if not dados or not dados.get('nome_versao') or not dados.get('exercicio_fiscal'):
            return jsonify({'success': False, 'error': 'nome_versao e exercicio_fiscal são obrigatórios'}), 400
        
        from contabilidade_functions import criar_versao
        versao_id = criar_versao(empresa_id, dados)
        return jsonify({'success': True, 'id': versao_id, 'message': 'Versão criada com sucesso'})
    except Exception as e:
        logger.error(f"Erro ao criar versão: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/versoes/<int:versao_id>', methods=['PUT'])
@require_auth
def atualizar_versao_plano(versao_id):
    """Atualiza versão do plano de contas"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        dados = request.get_json()
        from contabilidade_functions import atualizar_versao
        atualizar_versao(empresa_id, versao_id, dados)
        return jsonify({'success': True, 'message': 'Versão atualizada'})
    except Exception as e:
        logger.error(f"Erro ao atualizar versão: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/versoes/<int:versao_id>', methods=['DELETE'])
@require_auth
def excluir_versao_plano(versao_id):
    """Exclui versão do plano de contas"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        from contabilidade_functions import excluir_versao
        excluir_versao(empresa_id, versao_id)
        return jsonify({'success': True, 'message': 'Versão excluída'})
    except Exception as e:
        logger.error(f"Erro ao excluir versão: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/plano-contas', methods=['GET'])
@require_auth
def listar_plano_contas():
    """Lista contas do plano com filtros"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        versao_id = request.args.get('versao_id', type=int)
        classificacao = request.args.get('classificacao')
        tipo_conta = request.args.get('tipo_conta')
        busca = request.args.get('busca')
        
        from contabilidade_functions import listar_contas
        contas = listar_contas(empresa_id, versao_id=versao_id, classificacao=classificacao,
                               tipo_conta=tipo_conta, busca=busca)
        return jsonify({'success': True, 'contas': contas, 'total': len(contas)})
    except Exception as e:
        logger.error(f"Erro ao listar plano de contas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/plano-contas/tree', methods=['GET'])
@require_auth
def arvore_plano_contas():
    """Retorna plano de contas em estrutura de árvore"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        versao_id = request.args.get('versao_id', type=int)
        if not versao_id:
            # Tentar versão ativa
            from contabilidade_functions import obter_versao_ativa
            versao_ativa = obter_versao_ativa(empresa_id)
            if versao_ativa:
                versao_id = versao_ativa['id']
            else:
                return jsonify({'success': True, 'tree': [], 'message': 'Nenhuma versão encontrada'})
        
        from contabilidade_functions import obter_arvore_contas
        tree = obter_arvore_contas(empresa_id, versao_id)
        return jsonify({'success': True, 'tree': tree, 'versao_id': versao_id})
    except Exception as e:
        logger.error(f"Erro ao obter árvore: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/plano-contas', methods=['POST'])
@require_auth
def criar_conta_plano():
    """Cria nova conta no plano"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        dados = request.get_json()
        if not dados or not dados.get('codigo') or not dados.get('descricao'):
            return jsonify({'success': False, 'error': 'código e descrição são obrigatórios'}), 400
        if not dados.get('versao_id'):
            return jsonify({'success': False, 'error': 'versao_id é obrigatório'}), 400
        if not dados.get('classificacao'):
            return jsonify({'success': False, 'error': 'classificacao é obrigatória'}), 400
        
        from contabilidade_functions import criar_conta
        conta_id = criar_conta(empresa_id, dados)
        return jsonify({'success': True, 'id': conta_id, 'message': 'Conta criada com sucesso'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao criar conta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/plano-contas/<int:conta_id>', methods=['PUT'])
@require_auth
def atualizar_conta_plano(conta_id):
    """Atualiza conta do plano"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        dados = request.get_json()
        from contabilidade_functions import atualizar_conta
        atualizar_conta(empresa_id, conta_id, dados)
        return jsonify({'success': True, 'message': 'Conta atualizada'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao atualizar conta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/plano-contas/<int:conta_id>', methods=['DELETE'])
@require_auth
def excluir_conta_plano(conta_id):
    """Soft delete da conta e subcontas"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        from contabilidade_functions import excluir_conta
        deleted = excluir_conta(empresa_id, conta_id)
        return jsonify({'success': True, 'message': f'{deleted} conta(s) excluída(s)'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao excluir conta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/plano-contas/mover', methods=['POST'])
@require_auth
def mover_conta_plano():
    """Move conta para outro pai (drag-and-drop)"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        dados = request.get_json()
        conta_id = dados.get('conta_id')
        novo_parent_id = dados.get('novo_parent_id')  # None = raiz
        
        from contabilidade_functions import mover_conta
        mover_conta(empresa_id, conta_id, novo_parent_id)
        return jsonify({'success': True, 'message': 'Conta movida com sucesso'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao mover conta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/plano-contas/import', methods=['POST'])
@require_auth
def importar_plano_contas():
    """Importa contas de CSV"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        dados = request.get_json()
        versao_id = dados.get('versao_id')
        linhas = dados.get('linhas', [])
        
        if not versao_id or not linhas:
            return jsonify({'success': False, 'error': 'versao_id e linhas são obrigatórios'}), 400
        
        from contabilidade_functions import importar_contas_csv
        resultado = importar_contas_csv(empresa_id, versao_id, linhas)
        return jsonify({'success': True, **resultado})
    except Exception as e:
        logger.error(f"Erro ao importar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/plano-contas/export', methods=['GET'])
@require_auth
def exportar_plano_contas():
    """Exporta contas em JSON (para CSV/Excel no frontend)"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        versao_id = request.args.get('versao_id', type=int)
        if not versao_id:
            return jsonify({'success': False, 'error': 'versao_id é obrigatório'}), 400
        
        from contabilidade_functions import exportar_contas
        contas = exportar_contas(empresa_id, versao_id)
        return jsonify({'success': True, 'contas': contas})
    except Exception as e:
        logger.error(f"Erro ao exportar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/plano-contas/importar-padrao', methods=['POST'])
@require_auth
def importar_plano_padrao_route():
    """Importa o plano de contas padrão para a empresa"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        dados = request.get_json() or {}
        ano_fiscal = dados.get('ano_fiscal')
        
        from contabilidade_functions import importar_plano_padrao
        resultado = importar_plano_padrao(empresa_id, ano_fiscal)
        
        # Se a função já retorna success, apenas retornar o resultado
        if resultado.get('success'):
            return jsonify(resultado)
        
        # Formato antigo (retrocompatibilidade)
        return jsonify({
            'success': True,
            'versao_id': resultado.get('versao_id'),
            'contas_importadas': resultado.get('contas_importadas', resultado.get('contas_criadas', 0)),
            'erros': resultado.get('erros', []),
            'message': resultado.get('message')
        })
    except Exception as e:
        logger.error(f"Erro ao importar plano padrão: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/plano-contas/exportar-speed', methods=['GET'])
@require_auth
def exportar_plano_speed():
    """Exporta plano de contas no formato Speed (TXT)"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        versao_id = request.args.get('versao_id', type=int)
        if not versao_id:
            return jsonify({'success': False, 'error': 'versao_id é obrigatório'}), 400
        
        from contabilidade_functions import listar_contas
        from speed_integration import exportar_plano_contas_speed, estatisticas_mapeamento
        
        contas = listar_contas(empresa_id, versao_id=versao_id)
        
        if not contas:
            return jsonify({'success': False, 'error': 'Nenhuma conta encontrada'}), 404
        
        # Gerar arquivo TXT
        conteudo_txt = exportar_plano_contas_speed(contas)
        
        # Estatísticas
        stats = estatisticas_mapeamento(contas)
        
        return jsonify({
            'success': True,
            'conteudo': conteudo_txt,
            'formato': 'txt',
            'total_contas': len(contas),
            'estatisticas': stats
        })
    except Exception as e:
        logger.error(f"Erro ao exportar para Speed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contabilidade/plano-contas/mapeamento-referencial', methods=['GET'])
@require_auth
def exportar_mapeamento_referencial():
    """Exporta mapeamento com Referencial Contábil (CSV)"""
    try:
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 400
        
        versao_id = request.args.get('versao_id', type=int)
        if not versao_id:
            return jsonify({'success': False, 'error': 'versao_id é obrigatório'}), 400
        
        from contabilidade_functions import listar_contas
        from speed_integration import exportar_plano_contas_referencial
        
        contas = listar_contas(empresa_id, versao_id=versao_id)
        
        if not contas:
            return jsonify({'success': False, 'error': 'Nenhuma conta encontrada'}), 404
        
        # Gerar CSV com mapeamento
        conteudo_csv = exportar_plano_contas_referencial(contas)
        
        return jsonify({
            'success': True,
            'conteudo': conteudo_csv,
            'formato': 'csv'
        })
    except Exception as e:
        logger.error(f"Erro ao exportar mapeamento: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# LANÇAMENTOS CONTÁBEIS - FASE 2 SPEED
# =============================================================================

@app.route('/api/lancamentos-contabeis', methods=['GET'])
@require_auth
def listar_lancamentos_contabeis():
    """Lista lançamentos contábeis com filtros"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        
        # Parâmetros de filtro
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        tipo_lancamento = request.args.get('tipo_lancamento')
        origem = request.args.get('origem')
        busca = request.args.get('busca')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Converter datas
        from datetime import datetime
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        
        # Importar função
        from lancamentos_functions import listar_lancamentos
        
        conn = get_db_connection()
        resultado = listar_lancamentos(
            conn=conn,
            empresa_id=empresa_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            tipo_lancamento=tipo_lancamento,
            origem=origem,
            busca=busca,
            limit=limit,
            offset=offset
        )
        conn.close()
        
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Erro ao listar lançamentos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/lancamentos-contabeis/<int:lancamento_id>', methods=['GET'])
@require_auth
def obter_lancamento_detalhado_api(lancamento_id):
    """Obtém detalhes completos de um lançamento"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        
        from lancamentos_functions import obter_lancamento_detalhado
        
        conn = get_db_connection()
        resultado = obter_lancamento_detalhado(conn, lancamento_id, empresa_id)
        conn.close()
        
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Erro ao obter lançamento: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/lancamentos-contabeis', methods=['POST'])
@require_auth
def criar_lancamento_api():
    """Cria novo lançamento contábil"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        user_id = user.get('id')
        
        data = request.get_json()
        
        # Validar campos obrigatórios
        if not data.get('data_lancamento'):
            return jsonify({'success': False, 'error': 'Data do lançamento é obrigatória'}), 400
        if not data.get('historico'):
            return jsonify({'success': False, 'error': 'Histórico é obrigatório'}), 400
        if not data.get('itens') or len(data['itens']) < 2:
            return jsonify({'success': False, 'error': 'Lançamento deve ter pelo menos 2 itens'}), 400
        
        # Converter data
        from datetime import datetime
        data_lancamento = datetime.strptime(data['data_lancamento'], '%Y-%m-%d').date()
        
        from lancamentos_functions import criar_lancamento
        
        conn = get_db_connection()
        resultado = criar_lancamento(
            conn=conn,
            empresa_id=empresa_id,
            data_lancamento=data_lancamento,
            historico=data['historico'],
            itens=data['itens'],
            tipo_lancamento=data.get('tipo_lancamento', 'manual'),
            origem=data.get('origem'),
            origem_id=data.get('origem_id'),
            versao_plano_id=data.get('versao_plano_id'),
            observacoes=data.get('observacoes'),
            created_by=user_id
        )
        conn.close()
        
        if resultado['success']:
            return jsonify(resultado), 201
        else:
            return jsonify(resultado), 400
    except Exception as e:
        logger.error(f"Erro ao criar lançamento: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/lancamentos-contabeis/<int:lancamento_id>/estornar', methods=['POST'])
@require_auth
def estornar_lancamento_api(lancamento_id):
    """Estorna um lançamento criando lançamento inverso"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        user_id = user.get('id')
        
        data = request.get_json()
        historico_estorno = data.get('historico_estorno', 'Estorno de lançamento')
        
        from lancamentos_functions import estornar_lancamento
        
        conn = get_db_connection()
        resultado = estornar_lancamento(
            conn=conn,
            lancamento_id=lancamento_id,
            empresa_id=empresa_id,
            historico_estorno=historico_estorno,
            created_by=user_id
        )
        conn.close()
        
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Erro ao estornar lançamento: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/lancamentos-contabeis/<int:lancamento_id>', methods=['DELETE'])
@require_auth
def deletar_lancamento_api(lancamento_id):
    """Deleta um lançamento contábil"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        
        from lancamentos_functions import deletar_lancamento
        
        conn = get_db_connection()
        resultado = deletar_lancamento(conn, lancamento_id, empresa_id)
        conn.close()
        
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Erro ao deletar lançamento: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/lancamentos-contabeis/estatisticas', methods=['GET'])
@require_auth
def estatisticas_lancamentos_api():
    """Obtém estatísticas dos lançamentos"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        ano = request.args.get('ano', type=int)
        
        from lancamentos_functions import obter_estatisticas_lancamentos
        
        conn = get_db_connection()
        resultado = obter_estatisticas_lancamentos(conn, empresa_id, ano)
        conn.close()
        
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/lancamentos-contabeis/exportar-speed', methods=['POST'])
@require_auth
def exportar_lancamentos_speed_api():
    """Exporta lançamentos para formato Speed (TXT ou XML)"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        
        data = request.get_json()
        formato = data.get('formato', 'txt')  # 'txt' ou 'xml'
        data_inicio = data.get('data_inicio')
        data_fim = data.get('data_fim')
        
        # Converter datas
        from datetime import datetime
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        
        # Buscar lançamentos com itens detalhados
        from lancamentos_functions import listar_lancamentos, obter_lancamento_detalhado
        
        conn = get_db_connection()
        
        # Listar todos os lançamentos do período
        resultado_lista = listar_lancamentos(
            conn=conn,
            empresa_id=empresa_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            limit=10000  # Limite alto para exportação
        )
        
        if not resultado_lista['success']:
            conn.close()
            return jsonify(resultado_lista), 400
        
        # Buscar detalhes de cada lançamento (incluindo itens)
        lancamentos_completos = []
        for lanc in resultado_lista['lancamentos']:
            detalhe = obter_lancamento_detalhado(conn, lanc['id'], empresa_id)
            if detalhe['success']:
                lancamentos_completos.append(detalhe['lancamento'])
        
        conn.close()
        
        # Validar antes de exportar
        from speed_integration import validar_lancamentos_exportacao, exportar_lancamentos_speed, exportar_lancamentos_speed_xml
        
        validacao = validar_lancamentos_exportacao(lancamentos_completos)
        
        if not validacao['valido']:
            return jsonify({
                'success': False,
                'error': 'Validação falhou',
                'validacao': validacao
            }), 400
        
        # Exportar no formato escolhido
        if formato == 'xml':
            conteudo = exportar_lancamentos_speed_xml(lancamentos_completos)
        else:
            conteudo = exportar_lancamentos_speed(lancamentos_completos)
        
        return jsonify({
            'success': True,
            'conteudo': conteudo,
            'formato': formato,
            'total_lancamentos': len(lancamentos_completos),
            'validacao': validacao
        })
        
    except Exception as e:
        logger.error(f"Erro ao exportar lançamentos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# RELATÓRIOS CONTÁBEIS - FASE 3 SPEED
# =============================================================================

@app.route('/api/relatorios/balancete', methods=['POST'])
@require_auth
def gerar_balancete_api():
    """Gera Balancete de Verificação"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        
        data = request.get_json()
        
        # Validar campos obrigatórios
        if not data.get('data_inicio') or not data.get('data_fim'):
            return jsonify({'success': False, 'error': 'Período é obrigatório'}), 400
        
        # Converter datas
        from datetime import datetime
        data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%d').date()
        data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d').date()
        
        from relatorios_contabeis_functions import gerar_balancete_verificacao
        
        conn = get_db_connection()
        resultado = gerar_balancete_verificacao(
            conn=conn,
            empresa_id=empresa_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            versao_plano_id=data.get('versao_plano_id'),
            nivel_minimo=data.get('nivel_minimo'),
            nivel_maximo=data.get('nivel_maximo'),
            classificacao=data.get('classificacao'),
            apenas_com_movimento=data.get('apenas_com_movimento', False)
        )
        conn.close()
        
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Erro ao gerar balancete: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relatorios/dre', methods=['POST'])
@require_auth
def gerar_dre_api():
    """Gera DRE (Demonstrativo de Resultado do Exercício)"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        
        data = request.get_json()
        
        # Validar campos obrigatórios
        if not data.get('data_inicio') or not data.get('data_fim'):
            return jsonify({'success': False, 'error': 'Período é obrigatório'}), 400
        
        # Converter datas
        from datetime import datetime
        data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%d').date()
        data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d').date()
        
        from relatorios_contabeis_functions import gerar_dre
        
        conn = get_db_connection()
        resultado = gerar_dre(
            conn=conn,
            empresa_id=empresa_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            versao_plano_id=data.get('versao_plano_id')
        )
        conn.close()
        
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Erro ao gerar DRE: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relatorios/balanco-patrimonial', methods=['POST'])
@require_auth
def gerar_balanco_patrimonial_api():
    """Gera Balanço Patrimonial"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        
        data = request.get_json()
        
        # Validar campos obrigatórios
        if not data.get('data_referencia'):
            return jsonify({'success': False, 'error': 'Data de referência é obrigatória'}), 400
        
        # Converter data
        from datetime import datetime
        data_referencia = datetime.strptime(data['data_referencia'], '%Y-%m-%d').date()
        
        from relatorios_contabeis_functions import gerar_balanco_patrimonial
        
        conn = get_db_connection()
        resultado = gerar_balanco_patrimonial(
            conn=conn,
            empresa_id=empresa_id,
            data_referencia=data_referencia,
            versao_plano_id=data.get('versao_plano_id')
        )
        conn.close()
        
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Erro ao gerar balanço patrimonial: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relatorios/razao-contabil', methods=['POST'])
@require_auth
def gerar_razao_contabil_api():
    """Gera Razão Contábil (extrato de uma conta)"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        
        data = request.get_json()
        
        # Validar campos obrigatórios
        if not data.get('conta_id'):
            return jsonify({'success': False, 'error': 'ID da conta é obrigatório'}), 400
        if not data.get('data_inicio') or not data.get('data_fim'):
            return jsonify({'success': False, 'error': 'Período é obrigatório'}), 400
        
        # Converter datas
        from datetime import datetime
        data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%d').date()
        data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d').date()
        
        from relatorios_contabeis_functions import gerar_razao_contabil
        
        conn = get_db_connection()
        resultado = gerar_razao_contabil(
            conn=conn,
            empresa_id=empresa_id,
            conta_id=data['conta_id'],
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        conn.close()
        
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Erro ao gerar razão contábil: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relatorios/balancete/exportar', methods=['POST'])
@require_auth
def exportar_balancete_api():
    """Exporta Balancete em TXT ou CSV"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        
        data = request.get_json()
        formato = data.get('formato', 'txt')  # 'txt' ou 'csv'
        
        # Gerar balancete
        from datetime import datetime
        data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%d').date()
        data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d').date()
        
        from relatorios_contabeis_functions import gerar_balancete_verificacao
        from speed_integration import exportar_balancete_speed_txt, exportar_balancete_speed_csv
        
        conn = get_db_connection()
        balancete = gerar_balancete_verificacao(
            conn=conn,
            empresa_id=empresa_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            versao_plano_id=data.get('versao_plano_id'),
            nivel_minimo=data.get('nivel_minimo'),
            nivel_maximo=data.get('nivel_maximo'),
            classificacao=data.get('classificacao'),
            apenas_com_movimento=data.get('apenas_com_movimento', False)
        )
        conn.close()
        
        if not balancete['success']:
            return jsonify(balancete), 400
        
        # Exportar no formato escolhido
        if formato == 'csv':
            conteudo = exportar_balancete_speed_csv(balancete)
        else:
            conteudo = exportar_balancete_speed_txt(balancete)
        
        return jsonify({
            'success': True,
            'conteudo': conteudo,
            'formato': formato,
            'total_contas': balancete.get('total_contas', 0)
        })
    except Exception as e:
        logger.error(f"Erro ao exportar balancete: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relatorios/dre/exportar', methods=['POST'])
@require_auth
def exportar_dre_api():
    """Exporta DRE em TXT"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        
        data = request.get_json()
        
        # Gerar DRE
        from datetime import datetime
        data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%d').date()
        data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d').date()
        
        from relatorios_contabeis_functions import gerar_dre
        from speed_integration import exportar_dre_speed_txt
        
        conn = get_db_connection()
        dre = gerar_dre(
            conn=conn,
            empresa_id=empresa_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            versao_plano_id=data.get('versao_plano_id')
        )
        conn.close()
        
        if not dre['success']:
            return jsonify(dre), 400
        
        # Exportar em TXT
        conteudo = exportar_dre_speed_txt(dre)
        
        return jsonify({
            'success': True,
            'conteudo': conteudo,
            'formato': 'txt',
            'resultado_liquido': dre.get('dre', {}).get('resultado_liquido', 0)
        })
    except Exception as e:
        logger.error(f"Erro ao exportar DRE: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relatorios/balanco-patrimonial/exportar', methods=['POST'])
@require_auth
def exportar_balanco_patrimonial_api():
    """Exporta Balanço Patrimonial em TXT"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        
        data = request.get_json()
        
        # Gerar Balanço
        from datetime import datetime
        data_referencia = datetime.strptime(data['data_referencia'], '%Y-%m-%d').date()
        
        from relatorios_contabeis_functions import gerar_balanco_patrimonial
        from speed_integration import exportar_balanco_patrimonial_speed_txt
        
        conn = get_db_connection()
        balanco = gerar_balanco_patrimonial(
            conn=conn,
            empresa_id=empresa_id,
            data_referencia=data_referencia,
            versao_plano_id=data.get('versao_plano_id')
        )
        conn.close()
        
        if not balanco['success']:
            return jsonify(balanco), 400
        
        # Exportar em TXT
        conteudo = exportar_balanco_patrimonial_speed_txt(balanco)
        
        return jsonify({
            'success': True,
            'conteudo': conteudo,
            'formato': 'txt',
            'balanco_fechado': balanco.get('validacao', {}).get('balanco_fechado', False)
        })
    except Exception as e:
        logger.error(f"Erro ao exportar balanço: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relatorios/razao-contabil/exportar', methods=['POST'])
@require_auth
def exportar_razao_contabil_api():
    """Exporta Razão Contábil em TXT"""
    try:
        user = request.user
        empresa_id = user['empresa_id']
        
        data = request.get_json()
        
        # Gerar Razão
        from datetime import datetime
        data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%d').date()
        data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d').date()
        
        from relatorios_contabeis_functions import gerar_razao_contabil
        from speed_integration import exportar_razao_contabil_speed_txt
        
        conn = get_db_connection()
        razao = gerar_razao_contabil(
            conn=conn,
            empresa_id=empresa_id,
            conta_id=data['conta_id'],
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        conn.close()
        
        if not razao['success']:
            return jsonify(razao), 400
        
        # Exportar em TXT
        conteudo = exportar_razao_contabil_speed_txt(razao)
        
        return jsonify({
            'success': True,
            'conteudo': conteudo,
            'formato': 'txt',
            'total_movimentacoes': razao.get('total_movimentacoes', 0)
        })
    except Exception as e:
        logger.error(f"Erro ao exportar razão: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# SPED ECD - FASE 4 SPEED
# =============================================================================

@app.route('/api/sped/ecd/gerar', methods=['POST'])
@require_auth
def sped_ecd_gerar():
    """
    Gera arquivo SPED ECD (Escrituração Contábil Digital)
    
    Body:
    {
        "data_inicio": "YYYY-MM-DD",
        "data_fim": "YYYY-MM-DD",
        "versao_plano_id": <opcional>
    }
    
    Returns:
    {
        "success": true,
        "total_linhas": 1234,
        "hash": "ABC123...",
        "data_geracao": "17/02/2026 10:30:00",
        "periodo": "01012026 a 31122026",
        "preview": "primeiras 50 linhas do arquivo"
    }
    """
    try:
        from sped_ecd_functions import gerar_arquivo_ecd
        
        data = request.get_json()
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        # Validações
        data_inicio = data.get('data_inicio')
        data_fim = data.get('data_fim')
        versao_plano_id = data.get('versao_plano_id')
        
        if not data_inicio or not data_fim:
            return jsonify({
                'success': False,
                'error': 'data_inicio e data_fim são obrigatórios'
            }), 400
        
        # Gerar ECD
        resultado = gerar_arquivo_ecd(
            empresa_id=empresa_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            versao_plano_id=versao_plano_id
        )
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        # Retornar preview (primeiras 50 linhas)
        linhas = resultado['conteudo'].split('\n')
        preview = '\n'.join(linhas[:50])
        if len(linhas) > 50:
            preview += f"\n\n... (mais {len(linhas) - 50} linhas)"
        
        return jsonify({
            'success': True,
            'total_linhas': resultado['total_linhas'],
            'hash': resultado['hash'],
            'data_geracao': resultado['data_geracao'],
            'periodo': resultado['periodo'],
            'preview': preview
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar ECD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sped/ecd/exportar', methods=['POST'])
@require_auth
def sped_ecd_exportar():
    """
    Exporta arquivo SPED ECD completo
    
    Body:
    {
        "data_inicio": "YYYY-MM-DD",
        "data_fim": "YYYY-MM-DD",
        "versao_plano_id": <opcional>
    }
    
    Returns:
    {
        "success": true,
        "conteudo": "conteúdo completo do arquivo TXT",
        "total_linhas": 1234,
        "hash": "ABC123...",
        "nome_arquivo": "ECD_CNPJ_AAAAMMDD.txt"
    }
    """
    try:
        from sped_ecd_functions import gerar_arquivo_ecd
        from database_postgresql import get_connection
        
        data = request.get_json()
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        # Validações
        data_inicio = data.get('data_inicio')
        data_fim = data.get('data_fim')
        versao_plano_id = data.get('versao_plano_id')
        
        if not data_inicio or not data_fim:
            return jsonify({
                'success': False,
                'error': 'data_inicio e data_fim são obrigatórios'
            }), 400
        
        # Gerar ECD
        resultado = gerar_arquivo_ecd(
            empresa_id=empresa_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            versao_plano_id=versao_plano_id
        )
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        # Buscar CNPJ para nome do arquivo
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT cnpj FROM empresas WHERE id = %s", (empresa_id,))
            empresa = cursor.fetchone()
            cnpj_limpo = ''.join(filter(str.isdigit, empresa[0] if empresa and empresa[0] else '00000000000000'))
        finally:
            cursor.close()
            conn.close()
        
        # Nome do arquivo: ECD_CNPJ_AAAAMMDD.txt
        data_ref = data_fim.replace('-', '')[:8]  # AAAAMMDD
        nome_arquivo = f"ECD_{cnpj_limpo}_{data_ref}.txt"
        
        return jsonify({
            'success': True,
            'conteudo': resultado['conteudo'],
            'total_linhas': resultado['total_linhas'],
            'hash': resultado['hash'],
            'nome_arquivo': nome_arquivo,
            'data_geracao': resultado['data_geracao']
        })
        
    except Exception as e:
        logger.error(f"Erro ao exportar ECD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# SPED EFD-CONTRIBUIÇÕES - FASE 5 SPEED
# =============================================================================

@app.route('/api/sped/efd-contribuicoes/calcular', methods=['POST'])
@require_auth
def sped_efd_contribuicoes_calcular():
    """
    Calcula apuração mensal de PIS/COFINS sem gerar arquivo
    
    Body:
    {
        "mes": 1-12,
        "ano": 2026
    }
    
    Returns:
    {
        "success": true,
        "periodo": "01/2026",
        "regime": "Lucro Presumido (Cumulativo)",
        "receitas": {
            "total": 100000.00,
            "tributavel": 100000.00
        },
        "pis": {
            "aliquota": 0.65,
            "base_calculo": 100000.00,
            "valor": 650.00
        },
        "cofins": {
            "aliquota": 3.0,
            "base_calculo": 100000.00,
            "valor": 3000.00
        },
        "total_tributos": 3650.00
    }
    """
    try:
        from sped_efd_contribuicoes_functions import calcular_apuracao_mensal
        
        data = request.get_json()
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        # Validações
        mes = data.get('mes')
        ano = data.get('ano')
        
        if not mes or not ano:
            return jsonify({
                'success': False,
                'error': 'mes e ano são obrigatórios'
            }), 400
        
        if not isinstance(mes, int) or mes < 1 or mes > 12:
            return jsonify({
                'success': False,
                'error': 'mes deve estar entre 1 e 12'
            }), 400
        
        if not isinstance(ano, int) or ano < 2000 or ano > 2100:
            return jsonify({
                'success': False,
                'error': 'ano inválido'
            }), 400
        
        # Calcular apuração
        resultado = calcular_apuracao_mensal(
            empresa_id=empresa_id,
            mes=mes,
            ano=ano
        )
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao calcular PIS/COFINS: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sped/efd-contribuicoes/gerar', methods=['POST'])
@require_auth
def sped_efd_contribuicoes_gerar():
    """
    Gera arquivo EFD-Contribuições com preview
    
    Body:
    {
        "mes": 1-12,
        "ano": 2026,
        "usar_creditos_reais": true  # Opcional, padrão: true
    }
    
    Returns:
    {
        "success": true,
        "total_linhas": 450,
        "hash": "ABC123...",
        "data_geracao": "17/02/2026 14:30:00",
        "periodo": "01/2026",
        "modo": "creditos_reais" ou "simplificado",
        "totais": {
            "receitas": 100000.00,
            "pis": 650.00,
            "cofins": 3000.00,
            "total_tributos": 3650.00,
            "credito_pis": 150.00,
            "credito_cofins": 690.00
        },
        "preview": "primeiras 50 linhas do arquivo"
    }
    """
    try:
        from sped_efd_contribuicoes_functions import gerar_arquivo_efd_contribuicoes
        
        data = request.get_json()
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        # Validações
        mes = data.get('mes')
        ano = data.get('ano')
        usar_creditos_reais = data.get('usar_creditos_reais', True)
        
        if not mes or not ano:
            return jsonify({
                'success': False,
                'error': 'mes e ano são obrigatórios'
            }), 400
        
        if not isinstance(mes, int) or mes < 1 or mes > 12:
            return jsonify({
                'success': False,
                'error': 'mes deve estar entre 1 e 12'
            }), 400
        
        if not isinstance(ano, int) or ano < 2000 or ano > 2100:
            return jsonify({
                'success': False,
                'error': 'ano inválido'
            }), 400
        
        # Gerar EFD-Contribuições
        resultado = gerar_arquivo_efd_contribuicoes(
            empresa_id=empresa_id,
            mes=mes,
            ano=ano,
            usar_creditos_reais=usar_creditos_reais
        )
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        # Retornar preview (primeiras 50 linhas)
        linhas = resultado['conteudo'].split('\n')
        preview = '\n'.join(linhas[:50])
        if len(linhas) > 50:
            preview += f"\n\n... (mais {len(linhas) - 50} linhas)"
        
        return jsonify({
            'success': True,
            'total_linhas': resultado['total_linhas'],
            'hash': resultado['hash'],
            'data_geracao': resultado['data_geracao'],
            'periodo': resultado['periodo'],
            'modo': resultado.get('modo', 'simplificado'),
            'totais': resultado['totais'],
            'preview': preview
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar EFD-Contribuições: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sped/efd-contribuicoes/exportar', methods=['POST'])
@require_auth
def sped_efd_contribuicoes_exportar():
    """
    Exporta arquivo EFD-Contribuições completo
    
    Body:
    {
        "mes": 1-12,
        "ano": 2026,
        "usar_creditos_reais": true  # Opcional, padrão: true
    }
    
    Returns:
    {
        "success": true,
        "conteudo": "conteúdo completo do arquivo TXT",
        "total_linhas": 450,
        "hash": "ABC123...",
        "nome_arquivo": "EFD_Contribuicoes_CNPJ_AAAAMM.txt",
        "modo": "creditos_reais" ou "simplificado",
        "totais": {
            "receitas": 100000.00,
            "pis": 650.00,
            "cofins": 3000.00
        }
    }
    """
    try:
        from sped_efd_contribuicoes_functions import gerar_arquivo_efd_contribuicoes
        from database_postgresql import get_connection
        
        data = request.get_json()
        usuario = get_usuario_logado()
        empresa_id = usuario.get('empresa_id')
        
        # Validações
        mes = data.get('mes')
        ano = data.get('ano')
        usar_creditos_reais = data.get('usar_creditos_reais', True)
        
        if not mes or not ano:
            return jsonify({
                'success': False,
                'error': 'mes e ano são obrigatórios'
            }), 400
        
        if not isinstance(mes, int) or mes < 1 or mes > 12:
            return jsonify({
                'success': False,
                'error': 'mes deve estar entre 1 e 12'
            }), 400
        
        if not isinstance(ano, int) or ano < 2000 or ano > 2100:
            return jsonify({
                'success': False,
                'error': 'ano inválido'
            }), 400
        
        # Gerar EFD-Contribuições
        resultado = gerar_arquivo_efd_contribuicoes(
            empresa_id=empresa_id,
            mes=mes,
            ano=ano,
            usar_creditos_reais=usar_creditos_reais
        )
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        # Buscar CNPJ para nome do arquivo
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT cnpj FROM empresas WHERE id = %s", (empresa_id,))
            empresa = cursor.fetchone()
            cnpj_limpo = ''.join(filter(str.isdigit, empresa[0] if empresa and empresa[0] else '00000000000000'))
        finally:
            cursor.close()
            conn.close()
        
        # Nome do arquivo: EFD_Contribuicoes_CNPJ_AAAAMM.txt
        nome_arquivo = f"EFD_Contribuicoes_{cnpj_limpo}_{ano}{mes:02d}.txt"
        
        return jsonify({
            'success': True,
            'conteudo': resultado['conteudo'],
            'total_linhas': resultado['total_linhas'],
            'hash': resultado['hash'],
            'nome_arquivo': nome_arquivo,
            'data_geracao': resultado['data_geracao'],
            'modo': resultado.get('modo', 'simplificado'),
            'totais': resultado['totais']
        })
        
    except Exception as e:
        logger.error(f"Erro ao exportar EFD-Contribuições: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# INTEGRA CONTADOR - API SERPRO
# =============================================================================

@app.route('/api/integra-contador/enviar', methods=['POST'])
@require_auth
def integra_contador_enviar():
    """Envia requisição para a API Integra Contador do SERPRO"""
    try:
        data = request.get_json()
        
        tipo_operacao = data.get('tipoOperacao')
        payload = data.get('payload')
        
        if not tipo_operacao or not payload:
            return jsonify({
                'success': False,
                'error': 'tipoOperacao e payload são obrigatórios'
            }), 400
        
        # Importar funções
        from integra_contador_functions import enviar_requisicao, validar_payload
        
        # Validar payload
        valido, mensagem = validar_payload(payload)
        if not valido:
            return jsonify({
                'success': False,
                'error': f'Validação falhou: {mensagem}'
            }), 400
        
        # Enviar requisição
        resultado = enviar_requisicao(tipo_operacao, payload)
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao enviar requisição Integra Contador: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/integra-contador/testar', methods=['GET'])
@require_auth
def integra_contador_testar():
    """Testa conexão com a API Integra Contador"""
    try:
        from integra_contador_functions import testar_conexao
        resultado = testar_conexao()
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Erro ao testar conexão: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/integra-contador/token', methods=['GET'])
@require_auth
def integra_contador_token():
    """Obtém token de acesso (apenas para debug)"""
    try:
        from integra_contador_functions import obter_token
        token = obter_token()
        return jsonify({
            'success': True,
            'token': token[:50] + '...',  # Mostrar apenas primeiros 50 caracteres
            'message': 'Token obtido com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao obter token: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== NOTAS FISCAIS (NF-e / NFS-e) =====

@app.route('/api/notas-fiscais/importar', methods=['POST'])
@require_auth
def importar_nota_fiscal():
    """
    Importa XML de NF-e ou NFS-e
    
    Body: {
        "tipo": "NFE" ou "NFSE",
        "xml_content": "conteúdo do XML"
    }
    """
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        tipo = data.get('tipo', '').upper()
        xml_content = data.get('xml_content', '')
        
        if not xml_content:
            return jsonify({
                'success': False,
                'error': 'XML não fornecido'
            }), 400
        
        # Importar função apropriada
        from nfe_import_functions import importar_xml_nfe, importar_xml_nfse
        
        if tipo == 'NFE':
            resultado = importar_xml_nfe(empresa_id, xml_content, usuario['id'])
        elif tipo == 'NFSE':
            resultado = importar_xml_nfse(empresa_id, xml_content, usuario['id'])
        else:
            return jsonify({
                'success': False,
                'error': 'Tipo inválido. Use NFE ou NFSE'
            }), 400
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao importar nota fiscal: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/notas-fiscais/upload', methods=['POST'])
@require_auth
def upload_xml_nota_fiscal():
    """
    Upload de arquivo XML de NF-e ou NFS-e
    
    Form-data:
        file: arquivo XML
        tipo: NFE ou NFSE
    """
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        # Verificar se foi enviado arquivo
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo enviado'
            }), 400
        
        file = request.files['file']
        tipo = request.form.get('tipo', '').upper()
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nome de arquivo vazio'
            }), 400
        
        # Ler conteúdo do XML
        xml_content = file.read().decode('utf-8')
        
        # Importar função apropriada
        from nfe_import_functions import importar_xml_nfe, importar_xml_nfse
        
        if tipo == 'NFE':
            resultado = importar_xml_nfe(empresa_id, xml_content, usuario['id'])
        elif tipo == 'NFSE':
            resultado = importar_xml_nfse(empresa_id, xml_content, usuario['id'])
        else:
            # Tentar detectar automaticamente
            if 'NFe' in xml_content or 'nfe:' in xml_content:
                resultado = importar_xml_nfe(empresa_id, xml_content, usuario['id'])
            else:
                resultado = importar_xml_nfse(empresa_id, xml_content, usuario['id'])
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao fazer upload de nota fiscal: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/notas-fiscais/listar', methods=['POST'])
@require_auth
def listar_notas_fiscais():
    """
    Lista notas fiscais da empresa
    
    Body: {
        "tipo": "NFE" ou "NFSE" (opcional),
        "data_inicio": "2026-01-01" (opcional),
        "data_fim": "2026-01-31" (opcional),
        "limit": 100 (opcional)
    }
    """
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        tipo = data.get('tipo')
        data_inicio = data.get('data_inicio')
        data_fim = data.get('data_fim')
        limit = data.get('limit', 100)
        
        from nfe_import_functions import listar_notas_fiscais
        notas = listar_notas_fiscais(empresa_id, tipo, data_inicio, data_fim, limit)
        
        return jsonify({
            'success': True,
            'notas': notas,
            'quantidade': len(notas)
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar notas fiscais: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/notas-fiscais/<int:nota_id>', methods=['GET'])
@require_auth
def obter_nota_fiscal(nota_id):
    """Obtém detalhes completos de uma nota fiscal"""
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        from nfe_import_functions import obter_detalhes_nota_fiscal
        detalhes = obter_detalhes_nota_fiscal(nota_id)
        
        if not detalhes:
            return jsonify({
                'success': False,
                'error': 'Nota fiscal não encontrada'
            }), 404
        
        # Verificar se a nota pertence à empresa
        if detalhes['nota']['empresa_id'] != empresa_id:
            return jsonify({
                'success': False,
                'error': 'Acesso negado'
            }), 403
        
        return jsonify({
            'success': True,
            **detalhes
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter detalhes da nota fiscal: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/notas-fiscais/totais', methods=['POST'])
@require_auth
def calcular_totais_notas():
    """
    Calcula totais de notas fiscais no período
    
    Body: {
        "data_inicio": "2026-01-01",
        "data_fim": "2026-01-31"
    }
    """
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        data_inicio = data.get('data_inicio')
        data_fim = data.get('data_fim')
        
        if not data_inicio or not data_fim:
            return jsonify({
                'success': False,
                'error': 'data_inicio e data_fim são obrigatórios'
            }), 400
        
        from nfe_import_functions import calcular_totais_periodo
        totais = calcular_totais_periodo(empresa_id, data_inicio, data_fim)
        
        return jsonify({
            'success': True,
            'periodo': {
                'data_inicio': data_inicio,
                'data_fim': data_fim
            },
            'totais': totais
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular totais de notas: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


# ===== CRÉDITOS TRIBUTÁRIOS =====

@app.route('/api/creditos-tributarios/calcular', methods=['POST'])
@require_auth
def calcular_creditos_tributarios():
    """
    Calcula créditos tributários de PIS/COFINS
    
    Body: {
        "mes": 1,
        "ano": 2026,
        "tipos": ["INSUMOS", "ENERGIA", "ALUGUEL"] (opcional - calcula todos se não informado)
    }
    """
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        mes = data.get('mes')
        ano = data.get('ano')
        tipos = data.get('tipos', [])
        
        if not mes or not ano:
            return jsonify({
                'success': False,
                'error': 'mes e ano são obrigatórios'
            }), 400
        
        from creditos_tributarios_functions import (
            calcular_todos_creditos,
            calcular_creditos_insumos,
            calcular_creditos_energia,
            calcular_creditos_aluguel
        )
        
        # Se não especificou tipos, calcular todos
        if not tipos:
            resultado = calcular_todos_creditos(empresa_id, mes, ano)
        else:
            # Calcular apenas os tipos especificados
            resultados = {}
            total_pis = 0
            total_cofins = 0
            
            if 'INSUMOS' in tipos:
                r = calcular_creditos_insumos(empresa_id, mes, ano)
                if r.get('success'):
                    resultados['insumos'] = r
                    total_pis += r.get('credito_pis', 0)
                    total_cofins += r.get('credito_cofins', 0)
            
            if 'ENERGIA' in tipos:
                r = calcular_creditos_energia(empresa_id, mes, ano)
                if r.get('success'):
                    resultados['energia'] = r
                    total_pis += r.get('credito_pis', 0)
                    total_cofins += r.get('credito_cofins', 0)
            
            if 'ALUGUEL' in tipos:
                r = calcular_creditos_aluguel(empresa_id, mes, ano)
                if r.get('success'):
                    resultados['aluguel'] = r
                    total_pis += r.get('credito_pis', 0)
                    total_cofins += r.get('credito_cofins', 0)
            
            resultado = {
                'success': True,
                'mes': mes,
                'ano': ano,
                'detalhamento': resultados,
                'resumo': {
                    'total_credito_pis': total_pis,
                    'total_credito_cofins': total_cofins,
                    'total_geral': total_pis + total_cofins
                }
            }
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao calcular créditos tributários: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/creditos-tributarios/listar', methods=['POST'])
@require_auth
def listar_creditos_tributarios():
    """
    Lista créditos tributários calculados
    
    Body: {
        "mes": 1,
        "ano": 2026,
        "tributo": "PIS" ou "COFINS" (opcional)
    }
    """
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        mes = data.get('mes')
        ano = data.get('ano')
        tributo = data.get('tributo')
        
        if not mes or not ano:
            return jsonify({
                'success': False,
                'error': 'mes e ano são obrigatórios'
            }), 400
        
        from creditos_tributarios_functions import listar_creditos_periodo
        creditos = listar_creditos_periodo(empresa_id, mes, ano, tributo)
        
        return jsonify({
            'success': True,
            'mes': mes,
            'ano': ano,
            'creditos': creditos,
            'quantidade': len(creditos)
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar créditos tributários: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/creditos-tributarios/resumo', methods=['POST'])
@require_auth
def resumo_creditos_tributarios():
    """
    Obtém resumo dos créditos tributários
    
    Body: {
        "mes": 1,
        "ano": 2026
    }
    """
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        mes = data.get('mes')
        ano = data.get('ano')
        
        if not mes or not ano:
            return jsonify({
                'success': False,
                'error': 'mes e ano são obrigatórios'
            }), 400
        
        from creditos_tributarios_functions import obter_resumo_creditos
        resumo = obter_resumo_creditos(empresa_id, mes, ano)
        
        return jsonify({
            'success': True,
            'mes': mes,
            'ano': ano,
            **resumo
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter resumo de créditos: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


# ===== DCTF (Declaração de Débitos Federais) =====

@app.route('/api/dctf/gerar', methods=['POST'])
@require_auth
def gerar_dctf():
    """
    Gera arquivo DCTF mensal
    
    Body: {
        "mes": 1,
        "ano": 2026
    }
    """
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        mes = data.get('mes')
        ano = data.get('ano')
        
        if not mes or not ano:
            return jsonify({
                'success': False,
                'error': 'mes e ano são obrigatórios'
            }), 400
        
        from dctf_functions import gerar_arquivo_dctf
        resultado = gerar_arquivo_dctf(empresa_id, mes, ano)
        
        if resultado.get('success'):
            logger.info(f"DCTF gerado para empresa {empresa_id}: {mes}/{ano}")
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao gerar DCTF: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


# ===== DIRF (Declaração de IR Retido na Fonte) =====

@app.route('/api/dirf/gerar', methods=['POST'])
@require_auth
def gerar_dirf():
    """
    Gera arquivo DIRF anual
    
    Body: {
        "ano": 2025
    }
    """
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        ano = data.get('ano')
        
        if not ano:
            return jsonify({
                'success': False,
                'error': 'ano é obrigatório'
            }), 400
        
        from dirf_functions import gerar_arquivo_dirf
        resultado = gerar_arquivo_dirf(empresa_id, ano)
        
        if resultado.get('success'):
            logger.info(f"DIRF gerado para empresa {empresa_id}: {ano}")
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao gerar DIRF: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/dirf/resumo', methods=['POST'])
@require_auth
def resumo_dirf():
    """
    Obtém resumo da DIRF antes de gerar
    
    Body: {
        "ano": 2025
    }
    """
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        ano = data.get('ano')
        
        if not ano:
            return jsonify({
                'success': False,
                'error': 'ano é obrigatório'
            }), 400
        
        from dirf_functions import obter_resumo_dirf
        resultado = obter_resumo_dirf(empresa_id, ano)
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao obter resumo DIRF: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


# ============================================================================
# RELATÓRIOS FISCAIS - NF-e / CT-e
# ============================================================================

@app.route('/relatorios/fiscal')
@require_auth
@require_permission('relatorios.nfe.visualizar')
def relatorios_fiscal():
    """Dashboard de relatórios fiscais (NF-e, CT-e)"""
    return render_template('relatorios_fiscais.html')


# ===== GERENCIAMENTO DE CERTIFICADOS DIGITAIS =====

@app.route('/api/relatorios/certificados', methods=['GET'])
@require_auth
@require_permission('relatorios.certificados.visualizar')
def listar_certificados():
    """Lista todos os certificados digitais da empresa"""
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    id, cnpj, nome_certificado, cuf, ambiente, ativo,
                    ultimo_nsu, max_nsu, data_ultima_busca,
                    valido_de, valido_ate,
                    total_documentos_baixados, total_nfes, total_ctes, total_eventos,
                    criado_em, atualizado_em, senha_pfx
                FROM certificados_digitais
                WHERE empresa_id = %s
                ORDER BY ativo DESC, criado_em DESC
            """, (empresa_id,))
            
            certificados = cursor.fetchall()
            
            # ✅ Valida se a senha pode ser descriptografada
            from relatorios.nfe import nfe_api
            import os
            chave_cripto = os.environ.get('FERNET_KEY', '').encode('utf-8')
            
            for cert in certificados:
                # Verifica se a senha está em formato válido
                senha_cripto = cert.get('senha_pfx', '')
                if len(senha_cripto) < 50:
                    cert['senha_valida'] = False
                    cert['erro_senha'] = 'Certificado precisa ser recadastrado (senha em formato inválido)'
                else:
                    try:
                        # Tenta descriptografar para validar
                        if chave_cripto:
                            nfe_api.descriptografar_senha(senha_cripto, chave_cripto)
                            cert['senha_valida'] = True
                        else:
                            cert['senha_valida'] = False
                            cert['erro_senha'] = 'Chave de criptografia não configurada'
                    except Exception as e:
                        cert['senha_valida'] = False
                        cert['erro_senha'] = 'Certificado precisa ser recadastrado'
                
                # Remove senha_pfx do retorno (segurança)
                cert.pop('senha_pfx', None)
        
        return jsonify({
            'success': True,
            'certificados': certificados
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar certificados: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/certificado/validar', methods=['POST'])
@require_auth
def validar_certificado():
    """Valida e extrai informações de um certificado digital"""
    try:
        dados = request.get_json()
        pfx_base64 = dados.get('pfx_base64')
        senha = dados.get('senha')
        
        if not pfx_base64 or not senha:
            return jsonify({
                'sucesso': False,
                'erro': 'Arquivo e senha são obrigatórios'
            })
        
        # Decodificar base64
        import base64
        pfx_bytes = base64.b64decode(pfx_base64)
        
        # Processar certificado usando função do NFS-e
        from nfse_functions import processar_certificado
        info = processar_certificado(pfx_bytes, senha)
        
        if not info.get('success'):
            return jsonify({
                'sucesso': False,
                'erro': info.get('error', 'Erro ao processar certificado')
            })
        
        # Se não conseguiu extrair UF do certificado, tentar consultar ReceitaWS
        if not info.get('uf') and info.get('cnpj'):
            try:
                logger.info(f"🔍 UF não encontrada no certificado, consultando ReceitaWS para CNPJ {info['cnpj']}")
                import requests
                cnpj_limpo = info['cnpj'].replace('.', '').replace('/', '').replace('-', '')
                url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj_limpo}"
                
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    dados_empresa = response.json()
                    if dados_empresa.get('status') == 'OK':
                        uf = dados_empresa.get('uf', '').strip().upper()
                        if len(uf) == 2 and uf.isalpha():
                            info['uf'] = uf
                            logger.info(f"✅ UF obtida via ReceitaWS: {uf}")
                        else:
                            logger.warning(f"⚠️ UF inválida retornada pela ReceitaWS: {uf}")
                    else:
                        logger.warning(f"⚠️ ReceitaWS retornou status: {dados_empresa.get('status')}")
                else:
                    logger.warning(f"⚠️ ReceitaWS retornou status code: {response.status_code}")
            except requests.Timeout:
                logger.warning("⚠️ Timeout ao consultar ReceitaWS (5s)")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao consultar ReceitaWS: {str(e)}")
        
        # Retornar informações extraídas
        return jsonify({
            'sucesso': True,
            'certificado': {
                'cnpj': info.get('cnpj'),
                'razao_social': info.get('razao_social'),
                'emitente': info.get('emitente'),
                'validade_inicio': info.get('validade_inicio'),
                'validade_fim': info.get('validade_fim'),
                'serial_number': info.get('serial_number'),
                'uf': info.get('uf')
            }
        })
        
    except ValueError as e:
        return jsonify({
            'sucesso': False,
            'erro': 'Senha incorreta ou arquivo inválido'
        })
    except Exception as e:
        print(f"Erro ao validar certificado: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao processar certificado: {str(e)}'
        })


@app.route('/api/relatorios/certificados/extrair-dados', methods=['POST'])
@require_auth
@require_permission('relatorios.certificados.criar')
def extrair_dados_certificado():
    """Extrai dados automaticamente do arquivo .pfx (CNPJ, nome, validades)"""
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'sucesso': False, 'erro': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        
        if not data.get('pfx_base64') or not data.get('senha'):
            return jsonify({
                'sucesso': False,
                'erro': 'PFX e senha são obrigatórios'
            }), 400
        
        # Importa módulo de busca (onde está CertificadoA1)
        from relatorios.nfe import nfe_busca
        
        # Tenta carregar o certificado
        try:
            cert = nfe_busca.CertificadoA1(
                pfx_base64=data['pfx_base64'],
                senha=data['senha']
            )
            
            if not cert.esta_valido():
                return jsonify({
                    'sucesso': False,
                    'erro': 'Certificado fora do prazo de validade',
                    'valido_de': cert.cert_data.get('valido_de').isoformat() if cert.cert_data.get('valido_de') else None,
                    'valido_ate': cert.cert_data.get('valido_ate').isoformat() if cert.cert_data.get('valido_ate') else None
                })
            
            # Busca dados da empresa para preencher campos (incluindo estado/UF)
            with get_db_connection(empresa_id=empresa_id) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT razao_social, cnpj, estado
                    FROM empresas
                    WHERE id = %s
                """, (empresa_id,))
                empresa = cursor.fetchone()
            
            empresa_dict = dict(zip(['razao_social', 'cnpj', 'estado'], empresa)) if empresa else {}
            
            # 🔍 DEBUG: Log dos dados da empresa
            logger.info(f"[CERTIFICADO DEBUG] Empresa ID: {empresa_id}")
            logger.info(f"[CERTIFICADO DEBUG] Dados empresa: {empresa_dict}")
            logger.info(f"[CERTIFICADO DEBUG] Estado bruto: '{empresa_dict.get('estado')}'")
            
            # Extrai CNPJ do certificado (subject DN geralmente contém)
            cnpj_cert = cert.cert_data.get('cnpj', '')
            
            # CNPJ do certificado tem prioridade; se não extrair, usa o da empresa
            cnpj_final = cnpj_cert if cnpj_cert else (empresa_dict.get('cnpj', '').replace('.', '').replace('/', '').replace('-', ''))
            
            # Mapa de UF (sigla) para código IBGE (cUF)
            uf_para_codigo = {
                'AC': '12', 'AL': '27', 'AP': '16', 'AM': '13', 'BA': '29',
                'CE': '23', 'DF': '53', 'ES': '32', 'GO': '52', 'MA': '21',
                'MT': '51', 'MS': '50', 'MG': '31', 'PA': '15', 'PB': '25',
                'PR': '41', 'PE': '26', 'PI': '22', 'RJ': '33', 'RN': '24',
                'RS': '43', 'RO': '11', 'RR': '14', 'SC': '42', 'SP': '35',
                'SE': '28', 'TO': '17'
            }
            
            # Busca UF da empresa e converte para código IBGE
            estado_empresa = (empresa_dict.get('estado') or '').strip().upper()
            cuf_empresa = uf_para_codigo.get(estado_empresa, '31')  # Default MG se não encontrar
            
            # 🔍 DEBUG: Log do mapeamento
            logger.info(f"[CERTIFICADO DEBUG] Estado normalizado: '{estado_empresa}'")
            logger.info(f"[CERTIFICADO DEBUG] Código UF mapeado: {cuf_empresa}")
            
            resultado = {
                'sucesso': True,
                'dados': {
                    'cnpj': cnpj_final,
                    'nome_certificado': empresa_dict.get('razao_social', 'Certificado Digital'),
                    'valido_de': cert.cert_data.get('valido_de').isoformat() if cert.cert_data.get('valido_de') else None,
                    'valido_ate': cert.cert_data.get('valido_ate').isoformat() if cert.cert_data.get('valido_ate') else None,
                    'cuf': cuf_empresa,  # UF da empresa convertido para código IBGE
                    'uf_sigla': estado_empresa,  # Sigla do estado para referência
                    'subject': cert.cert_data.get('subject', ''),
                    'issuer': cert.cert_data.get('issuer', '')
                }
            }
            
            return jsonify(resultado)
            
        except Exception as e:
            return jsonify({
                'sucesso': False,
                'erro': f'Erro ao ler certificado: {str(e)}'
            })
        
    except Exception as e:
        logger.error(f"Erro ao extrair dados do certificado: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'sucesso': False,
            'erro': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/relatorios/certificados/novo', methods=['POST'])
@require_auth
@require_permission('relatorios.certificados.criar')
def cadastrar_certificado():
    """Cadastra um novo certificado digital"""
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        
        # Validação
        required = ['cnpj', 'nome_certificado', 'pfx_base64', 'senha', 'cuf']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({
                'success': False,
                'error': f'Campos obrigatórios faltando: {", ".join(missing)}'
            }), 400
        
        # Importa módulo de API
        from relatorios.nfe import nfe_api
        
        # Salva certificado
        logger.info(f"[CERTIFICADO] Salvando certificado para empresa {empresa_id}, CNPJ {data['cnpj']}")
        resultado = nfe_api.salvar_certificado(
            empresa_id=empresa_id,
            cnpj=data['cnpj'],
            nome_certificado=data['nome_certificado'],
            pfx_base64=data['pfx_base64'],
            senha=data['senha'],
            cuf=int(data['cuf']),
            ambiente=data.get('ambiente', 'producao'),
            usuario_id=usuario['id']
        )
        
        logger.info(f"[CERTIFICADO] Resultado: {resultado}")
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao cadastrar certificado: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/relatorios/certificados/<int:certificado_id>/desativar', methods=['POST'])
@require_auth
@require_permission('relatorios.certificados.editar')
def desativar_certificado(certificado_id):
    """Desativa um certificado digital"""
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE certificados_digitais
                SET ativo = FALSE,
                    atualizado_em = NOW(),
                    atualizado_por = %s
                WHERE id = %s AND empresa_id = %s
            """, (usuario['id'], certificado_id, empresa_id))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Certificado desativado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao desativar certificado: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


# ===== BUSCA E PROCESSAMENTO DE DOCUMENTOS =====

@app.route('/api/relatorios/buscar-documentos', methods=['POST'])
@require_auth
@require_permission('relatorios.nfe.buscar')
def buscar_documentos():
    """Inicia busca automática de documentos na SEFAZ"""
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        certificado_id = data.get('certificado_id')
        
        if not certificado_id:
            return jsonify({
                'success': False,
                'error': 'certificado_id é obrigatório'
            }), 400
        
        # Importa módulo de API
        from relatorios.nfe import nfe_api
        
        # Executa busca (sem limite: SEFAZ define quantos documentos retornar)
        resultado = nfe_api.buscar_e_processar_novos_documentos(
            certificado_id=certificado_id,
            usuario_id=usuario['id']
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao buscar documentos: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/relatorios/consultar-chave', methods=['POST'])
@require_auth
@require_permission('relatorios.nfe.buscar')
def consultar_por_chave():
    """Consulta uma NF-e específica por chave de acesso"""
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        chave = data.get('chave')
        certificado_id = data.get('certificado_id')
        
        if not chave or not certificado_id:
            return jsonify({
                'success': False,
                'error': 'chave e certificado_id são obrigatórios'
            }), 400
        
        # Importa módulos
        from relatorios.nfe import nfe_api, nfe_busca
        
        # Carrega certificado
        cert = nfe_api.obter_certificado(certificado_id)
        if not cert:
            return jsonify({
                'success': False,
                'error': 'Certificado não encontrado ou inválido'
            }), 404
        
        # Consulta por chave (auto-detecta NF-e/CT-e pelo modelo na chave)
        resultado = nfe_busca.consultar_documento_por_chave(
            certificado=cert,
            chave=chave,
            ambiente=data.get('ambiente', 'producao')
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao consultar chave: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


# ===== LISTAGEM E CONSULTA DE DOCUMENTOS =====

@app.route('/api/relatorios/documentos', methods=['GET'])
@require_auth
@require_permission('relatorios.nfe.visualizar')
def listar_documentos():
    """Lista documentos fiscais com filtros"""
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        # Parâmetros de filtro
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        tipo = request.args.get('tipo')  # NFe, CTe, Evento
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Query base
            sql = """
                SELECT 
                    id, nsu, chave, tipo_documento, schema_name,
                    numero_documento, serie, valor_total,
                    cnpj_emitente, nome_emitente,
                    cnpj_destinatario, nome_destinatario,
                    data_emissao, data_busca, processado
                FROM documentos_fiscais_log
                WHERE empresa_id = %s
            """
            
            params = [empresa_id]
            
            # Filtros opcionais
            if data_inicio:
                sql += " AND data_busca >= %s"
                params.append(data_inicio)
            
            if data_fim:
                sql += " AND data_busca <= %s"
                params.append(data_fim)
            
            if tipo:
                sql += " AND tipo_documento = %s"
                params.append(tipo)
            
            # Paginação
            sql += " ORDER BY data_busca DESC"
            sql += " LIMIT %s OFFSET %s"
            params.extend([per_page, (page - 1) * per_page])
            
            cursor.execute(sql, params)
            documentos = cursor.fetchall()
            
            # Total de registros
            sql_count = """
                SELECT COUNT(*) as total
                FROM documentos_fiscais_log
                WHERE empresa_id = %s
            """
            count_params = [empresa_id]
            
            if data_inicio:
                sql_count += " AND data_busca >= %s"
                count_params.append(data_inicio)
            
            if data_fim:
                sql_count += " AND data_busca <= %s"
                count_params.append(data_fim)
            
            if tipo:
                sql_count += " AND tipo_documento = %s"
                count_params.append(tipo)
            
            cursor.execute(sql_count, count_params)
            total = cursor.fetchone()['total']
        
        return jsonify({
            'success': True,
            'documentos': documentos,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar documentos: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/relatorios/documento/<int:doc_id>', methods=['GET'])
@require_auth
@require_permission('relatorios.nfe.visualizar')
def obter_documento(doc_id):
    """Obtém detalhes de um documento específico"""
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute("""
                SELECT *
                FROM documentos_fiscais_log
                WHERE id = %s AND empresa_id = %s
            """, (doc_id, empresa_id))
            
            documento = cursor.fetchone()
        
        if not documento:
            return jsonify({
                'success': False,
                'error': 'Documento não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'documento': documento
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter documento: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/relatorios/documento/<int:doc_id>/xml', methods=['GET'])
@require_auth
@require_permission('relatorios.nfe.visualizar')
def download_xml(doc_id):
    """Download do XML de um documento"""
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT chave, caminho_xml, tipo_documento
                FROM documentos_fiscais_log
                WHERE id = %s AND empresa_id = %s
            """, (doc_id, empresa_id))
            
            row = cursor.fetchone()
        
        if not row:
            return jsonify({
                'success': False,
                'error': 'Documento não encontrado'
            }), 404
        
        chave, caminho_xml, tipo_doc = row
        
        # Lê o arquivo XML
        if os.path.exists(caminho_xml):
            from flask import send_file
            return send_file(
                caminho_xml,
                mimetype='application/xml',
                as_attachment=True,
                download_name=f'{tipo_doc}_{chave}.xml'
            )
        else:
            return jsonify({
                'success': False,
                'error': 'Arquivo XML não encontrado no storage'
            }), 404
        
    except Exception as e:
        logger.error(f"Erro ao fazer download do XML: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


# ===== ESTATÍSTICAS E DASHBOARDS =====

@app.route('/api/relatorios/estatisticas', methods=['GET'])
@require_auth
@require_permission('relatorios.nfe.visualizar')
def obter_estatisticas():
    """Obtém estatísticas de documentos fiscais da empresa"""
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        from relatorios.nfe import nfe_api
        
        stats = nfe_api.obter_estatisticas_empresa(empresa_id)
        
        return jsonify({
            'success': True,
            'estatisticas': stats
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/relatorios/nsu-status', methods=['GET'])
@require_auth
@require_permission('relatorios.nfe.visualizar')
def obter_nsu_status():
    """Obtém status dos NSUs de todos os certificados"""
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    id, nome_certificado, cnpj, ambiente,
                    ultimo_nsu, max_nsu, data_ultima_busca,
                    total_documentos_baixados,
                    CASE 
                        WHEN max_nsu IS NOT NULL AND ultimo_nsu::BIGINT < max_nsu::BIGINT 
                        THEN (max_nsu::BIGINT - ultimo_nsu::BIGINT)
                        ELSE 0
                    END as nsus_pendentes
                FROM certificados_digitais
                WHERE empresa_id = %s AND ativo = TRUE
                ORDER BY data_ultima_busca DESC NULLS LAST
            """, (empresa_id,))
            
            certificados = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'certificados': certificados
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter status NSU: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


# ===== EXPORTAÇÃO =====

@app.route('/api/relatorios/exportar-excel', methods=['POST'])
@require_auth
@require_permission('relatorios.nfe.exportar')
def exportar_excel():
    """Exporta documentos fiscais para Excel"""
    try:
        usuario = get_usuario_logado()
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        data = request.get_json()
        data_inicio = data.get('data_inicio')
        data_fim = data.get('data_fim')
        tipo = data.get('tipo')
        
        from relatorios.nfe import nfe_api
        
        # Lista documentos
        documentos = nfe_api.listar_documentos_periodo(
            empresa_id=empresa_id,
            data_inicio=datetime.fromisoformat(data_inicio) if data_inicio else datetime.now() - timedelta(days=30),
            data_fim=datetime.fromisoformat(data_fim) if data_fim else datetime.now(),
            tipo=tipo
        )
        
        # Gera Excel
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        from io import BytesIO
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Documentos Fiscais"
        
        # Cabeçalho
        headers = ['NSU', 'Chave', 'Tipo', 'Número', 'Série', 'Valor', 
                  'Emitente CNPJ', 'Emitente Nome', 'Destinatário CNPJ', 
                  'Destinatário Nome', 'Data Emissão', 'Data Busca']
        
        ws.append(headers)
        
        # Estilos do cabeçalho
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        header_font = Font(color='FFFFFF', bold=True)
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
        
        # Dados
        for doc in documentos:
            ws.append([
                doc.get('nsu'),
                doc.get('chave'),
                doc.get('tipo'),
                doc.get('numero'),
                doc.get('serie'),
                doc.get('valor'),
                doc.get('emitente_cnpj'),
                doc.get('emitente_nome'),
                doc.get('destinatario_cnpj'),
                doc.get('destinatario_nome'),
                doc.get('data_emissao'),
                doc.get('data_busca')
            ])
        
        # Ajusta largura das colunas
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width
        
        # Salva em BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Envia arquivo
        from flask import send_file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'documentos_fiscais_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        logger.error(f"Erro ao exportar Excel: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no servidor: {str(e)}'
        }), 500


# ===== INTERFACE WEB SPED =====

@app.route('/sped')
@require_auth
def sped_interface():
    """Interface web para geração de arquivos SPED"""
    return render_template('sped_interface.html')


if __name__ == '__main__':
    # Inicializar tabelas de importação
    try:
        from database_import_manager import DatabaseImportManager
        import_manager = DatabaseImportManager()
        import_manager.create_import_tables()
        print("✅ Tabelas de importação inicializadas")
    except Exception as e:
        print(f"⚠️ Erro ao inicializar tabelas de importação: {e}")
    
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


