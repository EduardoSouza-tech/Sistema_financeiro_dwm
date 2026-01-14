"""
Integração com Sentry para monitoramento de erros em produção
"""
import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging


def init_sentry(app=None, dsn=None, environment='production', traces_sample_rate=0.1):
    """
    Inicializa o Sentry para monitoramento de erros
    
    Args:
        app: Instância do Flask app (opcional)
        dsn: Sentry DSN (obtém de variável de ambiente se None)
        environment: Ambiente (production, staging, development)
        traces_sample_rate: Taxa de amostragem para performance monitoring (0.0 a 1.0)
    
    Returns:
        True se inicializado com sucesso, False caso contrário
    """
    
    # Obter DSN da variável de ambiente se não fornecido
    if dsn is None:
        dsn = os.getenv('SENTRY_DSN')
    
    # Não inicializar se não houver DSN
    if not dsn:
        print("⚠️  Sentry DSN não configurado - Monitoramento desabilitado")
        return False
    
    # Detectar se está em produção
    is_production = os.getenv('RAILWAY_ENVIRONMENT') or environment == 'production'
    
    # Configurar integração com logging
    logging_integration = LoggingIntegration(
        level=logging.INFO,        # Captura logs INFO e acima
        event_level=logging.ERROR  # Envia como evento apenas ERROR e acima
    )
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FlaskIntegration(),
                logging_integration
            ],
            
            # Configurações de performance
            traces_sample_rate=traces_sample_rate,  # 10% das transações por padrão
            
            # Ambiente
            environment=environment,
            
            # Informações de release (útil para tracking de deploys)
            release=os.getenv('RAILWAY_GIT_COMMIT_SHA', 'unknown'),
            
            # Configurações de dados sensíveis
            send_default_pii=False,  # Não enviar PII por padrão
            
            # Before send hook para filtrar dados sensíveis
            before_send=before_send_filter,
            
            # Configurações de rede
            max_breadcrumbs=50,
            attach_stacktrace=True,
            
            # Debug (apenas em desenvolvimento)
            debug=not is_production
        )
        
        print(f"✅ Sentry inicializado - Ambiente: {environment}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inicializar Sentry: {e}")
        return False


def before_send_filter(event, hint):
    """
    Filtrar dados sensíveis antes de enviar ao Sentry
    
    Args:
        event: Evento do Sentry
        hint: Informações adicionais sobre o evento
    
    Returns:
        Evento modificado ou None para não enviar
    """
    
    # Lista de campos sensíveis para remover
    sensitive_fields = [
        'senha', 'password', 'senha_hash', 'token', 'secret',
        'api_key', 'authorization', 'cookie', 'session'
    ]
    
    # Função recursiva para limpar dados
    def clean_data(data):
        if isinstance(data, dict):
            for key in list(data.keys()):
                # Remover campos sensíveis
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    data[key] = '[FILTERED]'
                else:
                    # Recursão para objetos aninhados
                    clean_data(data[key])
        elif isinstance(data, list):
            for item in data:
                clean_data(item)
        
        return data
    
    # Limpar request data
    if 'request' in event:
        event['request'] = clean_data(event['request'])
    
    # Limpar extra data
    if 'extra' in event:
        event['extra'] = clean_data(event['extra'])
    
    # Limpar contexts
    if 'contexts' in event:
        event['contexts'] = clean_data(event['contexts'])
    
    return event


def capture_exception(error, context=None, level='error'):
    """
    Captura uma exceção e envia ao Sentry com contexto adicional
    
    Args:
        error: Exception ou mensagem de erro
        context: Dicionário com contexto adicional
        level: Nível de severidade (fatal, error, warning, info, debug)
    """
    
    with sentry_sdk.push_scope() as scope:
        # Adicionar nível de severidade
        scope.level = level
        
        # Adicionar contexto se fornecido
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        
        # Capturar exceção
        if isinstance(error, Exception):
            sentry_sdk.capture_exception(error)
        else:
            sentry_sdk.capture_message(str(error), level=level)


def set_user_context(user_id, email=None, username=None, proprietario_id=None):
    """
    Define contexto do usuário para rastreamento
    
    Args:
        user_id: ID do usuário
        email: Email do usuário (opcional)
        username: Nome do usuário (opcional)
        proprietario_id: ID do proprietário/tenant (opcional)
    """
    
    user_data = {
        'id': user_id
    }
    
    if email:
        user_data['email'] = email
    
    if username:
        user_data['username'] = username
    
    sentry_sdk.set_user(user_data)
    
    # Adicionar proprietario_id como tag para multi-tenancy
    if proprietario_id:
        sentry_sdk.set_tag('proprietario_id', proprietario_id)


def clear_user_context():
    """
    Limpa o contexto do usuário (útil no logout)
    """
    sentry_sdk.set_user(None)


def add_breadcrumb(message, category='custom', level='info', data=None):
    """
    Adiciona um breadcrumb para rastreamento de fluxo
    
    Args:
        message: Mensagem do breadcrumb
        category: Categoria (auth, database, api, custom, etc)
        level: Nível (debug, info, warning, error, critical)
        data: Dados adicionais (dict)
    """
    
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


def set_transaction_name(name):
    """
    Define o nome da transação para performance monitoring
    
    Args:
        name: Nome da transação (ex: 'POST /api/lancamentos')
    """
    
    with sentry_sdk.configure_scope() as scope:
        scope.transaction = name


def measure_performance(operation_name):
    """
    Decorator para medir performance de operações
    
    Args:
        operation_name: Nome da operação
    
    Usage:
        @measure_performance('database.query')
        def buscar_lancamentos():
            ...
    """
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            with sentry_sdk.start_span(op=operation_name) as span:
                span.set_data('function', func.__name__)
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Exemplo de uso
def exemplo_uso_sentry():
    """Exemplos de uso do Sentry"""
    
    # 1. Capturar exceção
    try:
        resultado = 1 / 0
    except Exception as e:
        capture_exception(e, context={
            'operacao': 'divisao',
            'dividendo': 1,
            'divisor': 0
        })
    
    # 2. Definir contexto do usuário
    set_user_context(
        user_id=123,
        email='usuario@exemplo.com',
        username='Usuario Teste',
        proprietario_id=1
    )
    
    # 3. Adicionar breadcrumbs
    add_breadcrumb('Usuário iniciou login', category='auth')
    add_breadcrumb('Credenciais validadas', category='auth', level='info')
    add_breadcrumb('Sessão criada', category='auth', data={'user_id': 123})
    
    # 4. Medir performance
    @measure_performance('database.query')
    def buscar_dados():
        # Simulação de query
        import time
        time.sleep(0.1)
        return []
    
    # 5. Capturar mensagem personalizada
    sentry_sdk.capture_message('Operação crítica executada', level='warning')
