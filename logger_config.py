"""
Sistema de Logging Estruturado para o Sistema Financeiro
"""
import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """
    Formatter que gera logs em formato JSON para melhor parsing
    """
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Adicionar informações extras se existirem
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        if hasattr(record, 'proprietario_id'):
            log_data['proprietario_id'] = record.proprietario_id
        
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        if hasattr(record, 'ip'):
            log_data['ip'] = record.ip
        
        # Adicionar exception info se existir
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Formatter com cores para output em console
    """
    
    # Cores ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        # Adicionar cor ao nível do log
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging(app_name='sistema_financeiro', log_level='INFO', enable_json=False):
    """
    Configura o sistema de logging
    
    Args:
        app_name: Nome da aplicação
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: Se True, usa formato JSON para logs
    
    Returns:
        Logger configurado
    """
    
    # Criar diretório de logs se não existir
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Obter logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remover handlers existentes para evitar duplicação
    logger.handlers.clear()
    
    # ========================================================================
    # HANDLER 1: Console (desenvolvimento)
    # ========================================================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if enable_json:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
    
    logger.addHandler(console_handler)
    
    # ========================================================================
    # HANDLER 2: Arquivo geral (rotativo)
    # ========================================================================
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / f'{app_name}.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    if enable_json:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
    
    logger.addHandler(file_handler)
    
    # ========================================================================
    # HANDLER 3: Arquivo de erros (apenas ERROR e CRITICAL)
    # ========================================================================
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / f'{app_name}_errors.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    
    if enable_json:
        error_handler.setFormatter(JSONFormatter())
    else:
        error_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d\n'
            'MESSAGE: %(message)s\n'
            '%(pathname)s\n'
            '%(exc_info)s\n'
            '─' * 80 + '\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
    
    logger.addHandler(error_handler)
    
    # ========================================================================
    # HANDLER 4: Arquivo de acesso (para auditoria)
    # ========================================================================
    access_handler = logging.handlers.TimedRotatingFileHandler(
        log_dir / f'{app_name}_access.log',
        when='midnight',
        interval=1,
        backupCount=30,  # 30 dias de histórico
        encoding='utf-8'
    )
    access_handler.setLevel(logging.INFO)
    
    if enable_json:
        access_handler.setFormatter(JSONFormatter())
    else:
        access_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        access_handler.setFormatter(access_formatter)
    
    # Criar logger separado para acesso
    access_logger = logging.getLogger(f'{app_name}.access')
    access_logger.setLevel(logging.INFO)
    access_logger.handlers.clear()
    access_logger.addHandler(access_handler)
    access_logger.propagate = False
    
    # Log inicial
    logger.info(f'Sistema de logging configurado - Nível: {log_level}')
    
    return logger


def get_logger(name=None):
    """
    Retorna um logger com o nome especificado
    
    Args:
        name: Nome do logger (usa o módulo chamador se None)
    
    Returns:
        Logger configurado
    """
    if name is None:
        # Obter nome do módulo chamador
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'sistema_financeiro')
    
    return logging.getLogger(name)


def log_request(request, user_id=None, proprietario_id=None):
    """
    Log de requisição HTTP para auditoria
    
    Args:
        request: Objeto Flask request
        user_id: ID do usuário (se autenticado)
        proprietario_id: ID do proprietário (multi-tenancy)
    """
    access_logger = logging.getLogger('sistema_financeiro.access')
    
    log_data = {
        'method': request.method,
        'path': request.path,
        'ip': request.remote_addr,
        'user_agent': request.user_agent.string,
        'user_id': user_id,
        'proprietario_id': proprietario_id
    }
    
    access_logger.info(
        f"{request.method} {request.path} | IP: {request.remote_addr} | "
        f"User: {user_id or 'anonymous'} | Proprietario: {proprietario_id or 'N/A'}",
        extra=log_data
    )


def log_error(error, request=None, user_id=None, context=None):
    """
    Log detalhado de erro
    
    Args:
        error: Exception ou mensagem de erro
        request: Objeto Flask request (opcional)
        user_id: ID do usuário (opcional)
        context: Contexto adicional (dict)
    """
    logger = get_logger()
    
    error_data = {
        'error_type': type(error).__name__ if isinstance(error, Exception) else 'Error',
        'error_message': str(error),
        'user_id': user_id
    }
    
    if request:
        error_data.update({
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr
        })
    
    if context:
        error_data['context'] = context
    
    logger.error(
        f"Erro: {error}",
        extra=error_data,
        exc_info=isinstance(error, Exception)
    )


# Exemplo de uso em diferentes níveis
def log_examples():
    """Exemplos de uso do logger"""
    logger = get_logger()
    
    # Debug (desenvolvimento)
    logger.debug("Informação detalhada para debugging")
    
    # Info (operação normal)
    logger.info("Operação realizada com sucesso")
    
    # Warning (algo inesperado mas não crítico)
    logger.warning("Recurso próximo do limite")
    
    # Error (erro que precisa atenção)
    logger.error("Falha ao processar requisição")
    
    # Critical (erro grave que afeta o sistema)
    logger.critical("Sistema fora do ar")
    
    # Com contexto adicional
    logger.info(
        "Usuário logado",
        extra={
            'user_id': 123,
            'proprietario_id': 1,
            'ip': '192.168.1.1'
        }
    )
