"""
Modulo de gerenciamento do banco de dados PostgreSQL
Otimizado com pool de conexoes para maxima performance
COM ROW LEVEL SECURITY PARA ISOLAMENTO 100% ENTRE EMPRESAS
"""
import psycopg2  # type: ignore
from psycopg2 import Error, sql, pool  # type: ignore
from psycopg2.extras import RealDictCursor  # type: ignore
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal
from enum import Enum
import json
import os
import sys
from contextlib import contextmanager

# Importar session do Flask para obter empresa_id automaticamente
try:
    from flask import session, has_request_context
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    has_request_context = lambda: False
    session = {}

# IMPORTAR SECURITY WRAPPER PARA ISOLAMENTO DE EMPRESAS
try:
    from security_wrapper import secure_connection, require_empresa, EmpresaNotSetError
    SECURITY_ENABLED = True
    print("🔒 Security Wrapper carregado - Row Level Security ATIVO", file=sys.stderr, flush=True)
except ImportError:
    SECURITY_ENABLED = False
    print("⚠️ Security Wrapper não encontrado - Funcionando SEM RLS", file=sys.stderr, flush=True)
    # Fallback para não quebrar o sistema
    def secure_connection(conn, empresa_id):
        from contextlib import contextmanager
        @contextmanager
        def _fallback():
            yield conn
        return _fallback()
    def require_empresa(func):
        return func

# Forcar saida imediata de logs (importante para Railway/gunicorn)
def log(msg):
    """Print que forca flush imediato"""
    print(msg, file=sys.stderr, flush=True)


# 🚀 FASE 5: Sistema de cache com isolamento por empresa
try:
    from cache_manager import cached, invalidate_cache
    CACHE_ENABLED = True
    log("✅ Cache Manager carregado - Cache inteligente ATIVO")
except ImportError:
    CACHE_ENABLED = False
    log("ℹ️  Cache Manager não encontrado - Funcionando SEM cache")
    # Fallback decorators se cache não disponível
    def cached(ttl=300, cache_instance=None):
        def decorator(func):
            return func
        return decorator
    def invalidate_cache(empresa_id):
        pass


# ============================================================================
# MODELOS DE DADOS
# ============================================================================
class TipoLancamento(Enum):
    """Tipos de lancamento financeiro"""
    RECEITA = "receita"
    DESPESA = "despesa"
    TRANSFERENCIA = "transferencia"


class StatusLancamento(Enum):
    """Status do lancamento"""
    PENDENTE = "pendente"
    PAGO = "pago"
    CANCELADO = "cancelado"
    VENCIDO = "vencido"


class Categoria:
    """Categoria de lancamento financeiro"""
    def __init__(self, nome: str, tipo: TipoLancamento, descricao: str = "", 
                 subcategorias: Optional[List[str]] = None, id: Optional[int] = None, 
                 cor: str = "#000000", icone: str = "folder", empresa_id: Optional[int] = None):
        self.id = id
        self.nome = nome
        self.tipo = tipo
        self.descricao = descricao
        self.subcategorias = subcategorias if subcategorias is not None else []
        self.cor = cor
        self.icone = icone
        self.empresa_id = empresa_id
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nome': self.nome,
            'tipo': self.tipo.value if isinstance(self.tipo, TipoLancamento) else self.tipo,
            'descricao': self.descricao,
            'subcategorias': self.subcategorias,
            'cor': self.cor,
            'icone': self.icone,
            'empresa_id': self.empresa_id
        }


class ContaBancaria:
    """Conta bancaria"""
    def __init__(self, nome: str, banco: str, agencia: str, conta: str, 
                 saldo_inicial: float = 0.0, id: Optional[int] = None, 
                 tipo_conta: str = "corrente", moeda: str = "BRL",
                 ativa: bool = True, proprietario_id: Optional[int] = None,
                 data_criacao: Optional[datetime] = None, 
                 tipo_saldo_inicial: str = "credor",
                 data_inicio: Optional[datetime] = None):
        self.id = id
        self.nome = nome
        self.banco = banco
        self.agencia = agencia
        self.conta = conta
        self.saldo_inicial = saldo_inicial
        self.tipo_saldo_inicial = tipo_saldo_inicial
        self.data_inicio = data_inicio or datetime.now().date()
        self.tipo_conta = tipo_conta
        self.moeda = moeda
        self.ativa = ativa
        self.proprietario_id = proprietario_id
        self.data_criacao = data_criacao
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nome': self.nome,
            'banco': self.banco,
            'agencia': self.agencia,
            'conta': self.conta,
            'saldo_inicial': float(self.saldo_inicial),
            'tipo_saldo_inicial': self.tipo_saldo_inicial,
            'data_inicio': self.data_inicio.isoformat() if isinstance(self.data_inicio, (date, datetime)) else self.data_inicio,
            'tipo_conta': self.tipo_conta,
            'moeda': self.moeda
        }


class Lancamento:
    """Lancamento financeiro"""
    def __init__(self, tipo: TipoLancamento, valor: float = 0.0, data_lancamento: Optional[datetime] = None,
                 categoria: str = "", subcategoria: str = "", conta_bancaria: str = "",
                 cliente_fornecedor: str = "", pessoa: str = "", descricao: str = "",
                 status: StatusLancamento = StatusLancamento.PENDENTE,
                 data_vencimento: Optional[datetime] = None,
                 data_pagamento: Optional[datetime] = None,
                 observacoes: str = "", anexo: str = "",
                 recorrente: bool = False, frequencia_recorrencia: str = "",
                 dia_vencimento: Optional[int] = None,
                 juros: float = 0.0, desconto: float = 0.0,
                 id: Optional[int] = None, proprietario_id: Optional[int] = None):
        self.id = id
        self.tipo = tipo
        self.valor = valor
        self.data_lancamento = data_lancamento
        self.data_vencimento = data_vencimento
        self.data_pagamento = data_pagamento
        self.categoria = categoria
        self.subcategoria = subcategoria
        self.conta_bancaria = conta_bancaria
        self.cliente_fornecedor = cliente_fornecedor
        self.pessoa = pessoa
        self.descricao = descricao
        self.status = status
        self.observacoes = observacoes
        self.anexo = anexo
        self.recorrente = recorrente
        self.frequencia_recorrencia = frequencia_recorrencia
        self.dia_vencimento = dia_vencimento
        self.juros = juros
        self.desconto = desconto
        self.proprietario_id = proprietario_id
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'tipo': self.tipo.value if isinstance(self.tipo, TipoLancamento) else self.tipo,
            'valor': float(self.valor),
            'data_lancamento': self.data_lancamento.isoformat() if isinstance(self.data_lancamento, datetime) else self.data_lancamento,
            'data_vencimento': self.data_vencimento.isoformat() if isinstance(self.data_vencimento, datetime) else self.data_vencimento,
            'data_pagamento': self.data_pagamento.isoformat() if isinstance(self.data_pagamento, datetime) else self.data_pagamento,
            'categoria': self.categoria,
            'subcategoria': self.subcategoria,
            'conta_bancaria': self.conta_bancaria,
            'cliente_fornecedor': self.cliente_fornecedor,
            'pessoa': self.pessoa,
            'descricao': self.descricao,
            'status': self.status.value if isinstance(self.status, StatusLancamento) else self.status,
            'observacoes': self.observacoes,
            'anexo': self.anexo,
            'recorrente': self.recorrente,
            'frequencia_recorrencia': self.frequencia_recorrencia,
            'proprietario_id': self.proprietario_id
        }


# ============================================================================
# CONFIGURAi?i?O E POOL DE CONEXi?ES
# ============================================================================

__all__ = [
    'criar_tabelas',
    'get_connection',
    'adicionar_conta',
    'listar_contas',
    'excluir_conta',
    'adicionar_categoria',
    'listar_categorias',
    'excluir_categoria',
    'atualizar_categoria',
    'atualizar_nome_categoria',
    'adicionar_cliente',
    'listar_clientes',
    'adicionar_fornecedor',
    'listar_fornecedores',
    'adicionar_lancamento',
    'listar_lancamentos',
    'excluir_lancamento',
    'pagar_lancamento',
    'cancelar_lancamento',
    'migrar_dados_json',
    'obter_lancamento',
    'atualizar_cliente',
    'atualizar_fornecedor',
    # Novas funi?i?es do menu Operacional
    'adicionar_contrato',
    'listar_contratos',
    'atualizar_contrato',
    'deletar_contrato',
    'adicionar_agenda',
    'listar_agenda',
    'atualizar_agenda',
    'deletar_agenda',
    'adicionar_produto',
    'listar_produtos',
    'atualizar_produto',
    'deletar_produto',
    'adicionar_kit',
    'listar_kits',
    'atualizar_kit',
    'deletar_kit',
    'adicionar_tag',
    'listar_tags',
    'atualizar_tag',
    'deletar_tag',
    'adicionar_template',
    'listar_templates_equipe',
    'atualizar_template',
    'deletar_template',
    'adicionar_sessao',
    'listar_sessoes',
    'atualizar_sessao',
    'deletar_sessao',
    'adicionar_comissao',
    'listar_comissoes',
    'atualizar_comissao',
    'deletar_comissao',
    'adicionar_sessao_equipe',
    'listar_sessao_equipe',
    'atualizar_sessao_equipe',
    'deletar_sessao_equipe'
]

# ============================================================================
# CONFIGURAi?i?O OTIMIZADA DO POSTGRESQL COM POOL DE CONEXi?ES
# ============================================================================

def _get_postgresql_config():
    """Configurai?i?o do PostgreSQL com prioridade para DATABASE_URL"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        return {'dsn': database_url}
    
    # Fallback para varii?veis individuais (desenvolvimento local)
    host = os.getenv('PGHOST', 'localhost')
    if not host or host == 'localhost':
        raise ValueError(
            "? ERRO: DATABASE_URL ni?o configurado. "
            "Configure a varii?vel de ambiente DATABASE_URL para conectar ao PostgreSQL."
        )
    
    return {
        'host': host,
        'port': int(os.getenv('PGPORT', '5432')),
        'user': os.getenv('PGUSER', 'postgres'),
        'password': os.getenv('PGPASSWORD', ''),
        'database': os.getenv('PGDATABASE', 'sistema_financeiro')
    }

POSTGRESQL_CONFIG = _get_postgresql_config()

# Pool de conexi?es global para reutilizai?i?o eficiente
_connection_pool = None
_database_initialized = False  # Flag para controlar inicializai?i?o i?nica

def _get_connection_pool():
    """Obti?m ou cria o pool de conexi?es"""
    global _connection_pool
    
    if _connection_pool is None:
        try:
            if 'dsn' in POSTGRESQL_CONFIG:
                _connection_pool = pool.ThreadedConnectionPool(
                    minconn=5,
                    maxconn=50,
                    dsn=POSTGRESQL_CONFIG['dsn'],
                    cursor_factory=RealDictCursor
                )
            else:
                _connection_pool = pool.ThreadedConnectionPool(
                    minconn=5,
                    maxconn=50,
                    cursor_factory=RealDictCursor,
                    **POSTGRESQL_CONFIG
                )
            print("? Pool de conexi?es PostgreSQL criado (5-50 conexi?es)")
        except Exception as e:
            print(f"? Erro ao criar pool de conexi?es: {e}")
            raise
    
    return _connection_pool

def _get_empresa_id_from_session():
    """
    Obtém empresa_id da sessão Flask automaticamente
    
    Returns:
        int ou None: ID da empresa da sessão ou None
        
    Warning:
        ⚠️ Este método existe apenas para compatibilidade temporária.
        SEMPRE passe empresa_id explicitamente quando possível.
    """
    if not FLASK_AVAILABLE or not has_request_context():
        return None
    
    try:
        return session.get('empresa_id')
    except:
        return None

@contextmanager
def get_db_connection(empresa_id=None, allow_global=False):
    """
    Context manager para obter conexão do pool com Row Level Security
    
    ⚠️ REGRA DE SEGURANÇA OBRIGATÓRIA:
    - Para acessar dados de empresa: empresa_id é OBRIGATÓRIO
    - Para acessar tabelas globais: use allow_global=True
    
    Args:
        empresa_id (int): ID da empresa para ativar Row Level Security
                         Se None, tenta obter automaticamente da sessão Flask
                         ⚠️ SEMPRE passe explicitamente quando possível!
        allow_global (bool): Se True, permite conexão sem empresa_id
                            Use APENAS para tabelas globais (usuarios, empresas)
                            
    Raises:
        ValueError: Se empresa_id não fornecido e not allow_global
    
    Example:
        # ✅ CORRETO - Acesso a dados de empresa
        with get_db_connection(empresa_id=18) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lancamentos")
        
        # ✅ CORRETO - Acesso a tabelas globais
        with get_db_connection(allow_global=True) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios")
        
        # ❌ ERRADO - Vai dar erro
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lancamentos")
    
    Security:
        🔒 Row Level Security é aplicado automaticamente quando empresa_id fornecido
        🔒 Conexões sem empresa_id são bloqueadas por padrão (segurança)
    """
    pool_obj = _get_connection_pool()
    conn = pool_obj.getconn()
    
    # Se empresa_id não fornecido, tentar obter da sessão Flask
    if empresa_id is None and not allow_global:
        empresa_id = _get_empresa_id_from_session()
        
        # ⚠️ VALIDAÇÃO DE SEGURANÇA CRÍTICA
        if empresa_id is None:
            pool_obj.putconn(conn)
            raise ValueError(
                "❌ SEGURANÇA: empresa_id é obrigatório para acessar dados de empresa!\n"
                "   Soluções:\n"
                "   1. Passar empresa_id explicitamente: get_db_connection(empresa_id=18)\n"
                "   2. Para tabelas globais: get_db_connection(allow_global=True)\n"
                "   3. Ver: REGRAS_SEGURANCA_OBRIGATORIAS.md"
            )
    
    try:
        conn.autocommit = True
        
        # ✅ ATIVAR RLS SE EMPRESA_ID DISPONÍVEL
        if empresa_id is not None and SECURITY_ENABLED:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT set_current_empresa(%s)", (empresa_id,))
                log(f"🔒 RLS ativado para empresa {empresa_id}")
            except Exception as e:
                log(f"⚠️ Erro ao configurar RLS: {e}")
            finally:
                cursor.close()
        elif allow_global:
            log(f"⚪ Conexão global (sem RLS) - Tabelas: usuarios, empresas, permissoes")
        
        yield conn
    finally:
        # Limpar configuração RLS
        if empresa_id is not None and SECURITY_ENABLED:
            try:
                cursor = conn.cursor()
                cursor.execute("RESET app.current_empresa_id")
                cursor.close()
            except:
                pass
        
        pool_obj.putconn(conn)


def return_to_pool(conn):
    """Devolve uma conexi?o ao pool manualmente"""
    try:
        pool_obj = _get_connection_pool()
        pool_obj.putconn(conn)
    except Exception as e:
        print(f"?? Erro ao devolver conexi?o ao pool: {e}")


# ============================================================================
# FUNi?i?ES AUXILIARES OTIMIZADAS
# ============================================================================

def execute_query(query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = True, empresa_id: int = None, allow_global: bool = False):
    """
    Executa query otimizada usando pool de conexões
    
    ⚠️ SEGURANÇA: empresa_id obrigatório para tabelas isoladas
    
    Args:
        query (str): Query SQL
        params (tuple): Parâmetros da query
        fetch_one (bool): Retornar apenas um resultado
        fetch_all (bool): Retornar todos os resultados
        empresa_id (int): ID da empresa [OBRIGATÓRIO para tabelas isoladas]
        allow_global (bool): Se True, permite query em tabelas globais sem empresa_id
    
    Returns:
        Resultado da query ou None
        
    Raises:
        ValueError: Se empresa_id não fornecido e not allow_global
        
    Example:
        # ✅ Query em tabela isolada
        result = execute_query(
            "SELECT * FROM clientes WHERE id = %s",
            params=(1,),
            empresa_id=18,
            fetch_one=True
        )
        
        # ✅ Query em tabela global
        result = execute_query(
            "SELECT * FROM usuarios WHERE id = %s",
            params=(1,),
            allow_global=True,
            fetch_one=True
        )
    """
    if not allow_global and not empresa_id:
        raise ValueError(
            "empresa_id é obrigatório para execute_query em tabelas isoladas. "
            "Use allow_global=True apenas para tabelas globais (usuarios, empresas)."
        )
    
    # ⚡ PERFORMANCE: Log de queries lentas (>500ms)
    import time
    start_time = time.time()
    
    with get_db_connection(empresa_id=empresa_id, allow_global=allow_global) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            
            # Medir tempo de execução
            execution_time = (time.time() - start_time) * 1000  # em milliseconds
            
            # Log queries lentas
            if execution_time > 500:  # > 500ms
                logger.warning(
                    f"⚠️  QUERY LENTA ({execution_time:.0f}ms): "
                    f"empresa_id={empresa_id}, "
                    f"query={query[:100]}..."  # Primeiros 100 caracteres
                )
            elif execution_time > 200:  # > 200ms
                logger.info(
                    f"⏱️  Query moderada ({execution_time:.0f}ms): "
                    f"empresa_id={empresa_id}"
                )
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.rowcount


def execute_many(query: str, params_list: list, empresa_id=None, allow_global=False):
    """
    Executa múltiplas queries em batch para performance
    
    ⚠️ SEGURANÇA: empresa_id obrigatório para tabelas isoladas
    
    Args:
        query (str): Query SQL
        params_list (list): Lista de tuplas com parâmetros
        empresa_id (int): ID da empresa [OBRIGATÓRIO para tabelas isoladas]
        allow_global (bool): Se True, permite query em tabelas globais sem empresa_id
        
    Returns:
        int: Número de registros afetados
        
    Raises:
        ValueError: Se empresa_id não fornecido e not allow_global
        
    Example:
        # ✅ Inserir múltiplos clientes
        execute_many(
            "INSERT INTO clientes (nome, empresa_id) VALUES (%s, %s)",
            [("Cliente 1", 18), ("Cliente 2", 18)],
            empresa_id=18
        )
    """
    if not allow_global and not empresa_id:
        raise ValueError(
            "empresa_id é obrigatório para execute_many em tabelas isoladas. "
            "Use allow_global=True apenas para tabelas globais (usuarios, empresas)."
        )
    
    with get_db_connection(empresa_id=empresa_id, allow_global=allow_global) as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount


# Cache simples para permissi?es (evita consultas repetidas)
_permissions_cache = {}
_cache_timeout = 300  # 5 minutos

def get_cached_permissions(usuario_id: int):
    """Obti?m permissi?es do usui?rio com cache"""
    import time
    current_time = time.time()
    
    if usuario_id in _permissions_cache:
        cached_data, timestamp = _permissions_cache[usuario_id]
        if current_time - timestamp < _cache_timeout:
            return cached_data
    
    # Cache miss ou expirado - buscar do banco
    query = """
        SELECT p.codigo 
        FROM permissoes p
        JOIN usuario_permissoes up ON up.permissao_id = p.id
        WHERE up.usuario_id = %s AND p.ativo = TRUE
    """
    permissions = execute_query(query, (usuario_id,), fetch_all=True)
    result = [p['codigo'] for p in permissions] if permissions else []
    
    _permissions_cache[usuario_id] = (result, current_time)
    return result


def clear_permissions_cache(usuario_id: int = None):
    """Limpa cache de permissi?es"""
    if usuario_id:
        _permissions_cache.pop(usuario_id, None)
    else:
        _permissions_cache.clear()


class DatabaseManager:
    """Gerenciador otimizado do banco de dados PostgreSQL com pool de conexi?es"""
    
    def __init__(self, config: Dict = None):
        global _database_initialized
        
        self.config = config or POSTGRESQL_CONFIG
        # Inicializar pool
        _get_connection_pool()
        
        # Criar tabelas e executar migrai?i?es APENAS UMA VEZ
        if not _database_initialized:
            print("?? Inicializando banco de dados (primeira vez)...")
            self.criar_tabelas()
            _database_initialized = True
            print("? Banco de dados inicializado!")
    
    def get_connection(self):
        """
        Obti?m uma conexi?o do pool
        IMPORTANTE: SEMPRE devolva ao pool com return_to_pool(conn) quando terminar!
        Ou use o context manager get_db_connection() preferencialmente.
        """
        try:
            pool_obj = _get_connection_pool()
            # Tentar obter conexão com timeout de 30 segundos
            conn = pool_obj.getconn()
            if conn:
                conn.autocommit = True
                # Verificar se a conexão está funcionando
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            return conn
        except pool.PoolError as e:
            print(f"⚠️ Pool esgotado! Tentando limpar conexões travadas...")
            # Tentar fechar todas as conexões e recriar o pool
            try:
                pool_obj.closeall()
            except:
                pass
            global _connection_pool
            _connection_pool = None
            # Tentar novamente
            pool_obj = _get_connection_pool()
            conn = pool_obj.getconn()
            conn.autocommit = True
            return conn
        except Error as e:
            print(f"❌ Erro ao obter conexi?o do pool: {e}")
            raise
    
    def criar_tabelas(self):
        """Cria as tabelas no banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de contas banci?rias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contas_bancarias (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL,
                banco VARCHAR(255) NOT NULL,
                agencia VARCHAR(50) NOT NULL,
                conta VARCHAR(50) NOT NULL,
                saldo_inicial DECIMAL(15,2) NOT NULL,
                tipo_saldo_inicial VARCHAR(10) DEFAULT 'credor' CHECK (tipo_saldo_inicial IN ('credor', 'devedor')),
                data_inicio DATE NOT NULL,
                ativa BOOLEAN DEFAULT TRUE,
                data_criacao TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de categorias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL,
                tipo VARCHAR(50) NOT NULL,
                subcategorias VARCHAR(255),
                cor VARCHAR(7),
                icone VARCHAR(50),
                descricao TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                cpf_cnpj VARCHAR(18) UNIQUE,
                email VARCHAR(255),
                telefone VARCHAR(20),
                endereco TEXT,
                ativo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de fornecedores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fornecedores (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                cpf_cnpj VARCHAR(18) UNIQUE,
                email VARCHAR(255),
                telefone VARCHAR(20),
                endereco TEXT,
                ativo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ===== TABELAS DE AUTENTICAi?i?O E AUTORIZAi?i?O =====
        
        # Tabela de usui?rios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('admin', 'cliente')),
                nome_completo VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                telefone VARCHAR(20),
                ativo BOOLEAN DEFAULT TRUE,
                cliente_id INTEGER REFERENCES clientes(id),
                ultimo_acesso TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES usuarios(id)
            )
        """)
        
        # Tabela de permissi?es (funcionalidades do sistema)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permissoes (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(50) UNIQUE NOT NULL,
                nome VARCHAR(100) NOT NULL,
                descricao TEXT,
                categoria VARCHAR(50),
                ativo BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Tabela de relai?i?o usui?rio-permissi?es
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuario_permissoes (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
                permissao_id INTEGER REFERENCES permissoes(id) ON DELETE CASCADE,
                concedido_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                concedido_por INTEGER REFERENCES usuarios(id),
                UNIQUE(usuario_id, permissao_id)
            )
        """)
        
        # Tabela de sessi?es de login (para controle de autenticai?i?o)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessoes_login (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expira_em TIMESTAMP NOT NULL,
                ativo BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Tabela de log de acessos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_acessos (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES usuarios(id),
                acao VARCHAR(100) NOT NULL,
                descricao TEXT,
                ip_address VARCHAR(45),
                sucesso BOOLEAN DEFAULT TRUE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de lani?amentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos (
                id SERIAL PRIMARY KEY,
                tipo VARCHAR(50) NOT NULL,
                descricao TEXT NOT NULL,
                valor DECIMAL(15,2) NOT NULL,
                data_vencimento DATE NOT NULL,
                data_pagamento DATE,
                categoria VARCHAR(255),
                subcategoria VARCHAR(255),
                conta_bancaria VARCHAR(255),
                cliente_fornecedor VARCHAR(255),
                pessoa VARCHAR(255),
                status VARCHAR(50) NOT NULL,
                observacoes TEXT,
                anexo TEXT,
                recorrente BOOLEAN DEFAULT FALSE,
                frequencia_recorrencia VARCHAR(50),
                dia_vencimento INTEGER,
                juros DECIMAL(15,2) DEFAULT 0,
                desconto DECIMAL(15,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Adicionar colunas juros e desconto se ni?o existirem (migration)
        try:
            cursor.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='lancamentos' AND column_name='juros'
                    ) THEN
                        ALTER TABLE lancamentos ADD COLUMN juros DECIMAL(15,2) DEFAULT 0;
                    END IF;
                    
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='lancamentos' AND column_name='desconto'
                    ) THEN
                        ALTER TABLE lancamentos ADD COLUMN desconto DECIMAL(15,2) DEFAULT 0;
                    END IF;
                END $$;
            """)
            print("? Migrai?i?o: Colunas juros e desconto adicionadas/verificadas")
        except Exception as e:
            print(f"??  Aviso na migrai?i?o de colunas: {e}")
        
        # Sincronizar sequi?ncias de auto-incremento com valores mi?ximos atuais
        try:
            cursor.execute("""
                DO $$ 
                DECLARE
                    max_id INTEGER;
                BEGIN
                    -- Sincronizar sequi?ncia de categorias
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM categorias;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''categorias_id_seq'', ' || max_id || ')';
                    END IF;
                    
                    -- Sincronizar sequi?ncia de contas_bancarias
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM contas_bancarias;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''contas_bancarias_id_seq'', ' || max_id || ')';
                    END IF;
                    
                    -- Sincronizar sequi?ncia de clientes
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM clientes;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''clientes_id_seq'', ' || max_id || ')';
                    END IF;
                    
                    -- Sincronizar sequi?ncia de fornecedores
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM fornecedores;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''fornecedores_id_seq'', ' || max_id || ')';
                    END IF;
                    
                    -- Sincronizar sequi?ncia de lancamentos
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM lancamentos;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''lancamentos_id_seq'', ' || max_id || ')';
                    END IF;
                END $$;
            """)
            print("? Migrai?i?o: Sequi?ncias de ID sincronizadas com sucesso")
        except Exception as e:
            print(f"??  Aviso na sincronizai?i?o de sequi?ncias: {e}")
        
        # Tabela de transacoes de extrato bancario (OFX)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacoes_extrato (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER NOT NULL,
                conta_bancaria VARCHAR(255) NOT NULL,
                data DATE NOT NULL,
                descricao TEXT NOT NULL,
                valor DECIMAL(15,2) NOT NULL,
                tipo VARCHAR(10) NOT NULL,
                saldo DECIMAL(15,2),
                fitid VARCHAR(255),
                memo TEXT,
                checknum VARCHAR(50),
                conciliado BOOLEAN DEFAULT FALSE,
                lancamento_id INTEGER,
                importacao_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id) ON DELETE SET NULL
            )
        """)
        
        # Indices para melhor performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_extrato_empresa_conta 
            ON transacoes_extrato(empresa_id, conta_bancaria)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_extrato_data 
            ON transacoes_extrato(data)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_extrato_conciliado 
            ON transacoes_extrato(conciliado)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_extrato_fitid 
            ON transacoes_extrato(fitid)
        """)
        
        # Tabela de contratos
        # Primeiro, dropar tabela antiga se existir com estrutura incompati?vel
        try:
            cursor.execute("""
                DO $$ 
                BEGIN
                    -- Verificar se existe coluna numero_nf (estrutura antiga)
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='contratos' AND column_name='numero_nf'
                    ) THEN
                        -- Dropar tabela antiga
                        DROP TABLE IF EXISTS contratos CASCADE;
                    END IF;
                END $$;
            """)
        except Exception as e:
            print(f"??  Aviso ao verificar tabela contratos: {e}")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contratos (
                id SERIAL PRIMARY KEY,
                numero VARCHAR(100) UNIQUE NOT NULL,
                cliente_id INTEGER REFERENCES clientes(id),
                descricao TEXT NOT NULL,
                valor DECIMAL(15,2) NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE,
                status VARCHAR(50) DEFAULT 'ativo',
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de agenda
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agenda (
                id SERIAL PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                data_evento DATE NOT NULL,
                hora_inicio TIME,
                hora_fim TIME,
                local VARCHAR(255),
                tipo VARCHAR(50),
                status VARCHAR(50) DEFAULT 'agendado',
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de produtos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(100) UNIQUE NOT NULL,
                nome VARCHAR(255) NOT NULL,
                categoria VARCHAR(100),
                quantidade DECIMAL(15,3) DEFAULT 0,
                preco_custo DECIMAL(15,2),
                preco_venda DECIMAL(15,2),
                fornecedor_id INTEGER REFERENCES fornecedores(id),
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de kits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kits (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(100) UNIQUE NOT NULL,
                nome VARCHAR(255) NOT NULL,
                preco DECIMAL(15,2) NOT NULL,
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de itens dos kits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kit_itens (
                id SERIAL PRIMARY KEY,
                kit_id INTEGER REFERENCES kits(id) ON DELETE CASCADE,
                produto_id INTEGER REFERENCES produtos(id),
                quantidade DECIMAL(15,3) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de tags
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) UNIQUE NOT NULL,
                cor VARCHAR(7) DEFAULT '#007bff',
                descricao TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de templates de equipe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates_equipe (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                tipo VARCHAR(50),
                conteudo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de sessi?es
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessoes (
                id SERIAL PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                data_sessao DATE NOT NULL,
                duracao INTEGER,
                contrato_id INTEGER REFERENCES contratos(id),
                cliente_id INTEGER REFERENCES clientes(id),
                valor DECIMAL(15,2),
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Adicionar coluna contrato_id se ni?o existir
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='contrato_id'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN contrato_id INTEGER REFERENCES contratos(id);
                END IF;
            END $$;
        """)
        
        # Migrai?i?o: Adicionar colunas que podem faltar em sessoes
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar titulo se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='titulo'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN titulo VARCHAR(255) NOT NULL DEFAULT 'Sessi?o';
                END IF;
                
                -- Adicionar data_sessao se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='data_sessao'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN data_sessao DATE NOT NULL DEFAULT CURRENT_DATE;
                END IF;
                
                -- Adicionar duracao se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='duracao'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN duracao INTEGER;
                END IF;
                
                -- Adicionar cliente_id se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='cliente_id'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN cliente_id INTEGER REFERENCES clientes(id);
                END IF;
                
                -- Adicionar valor se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='valor'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN valor DECIMAL(15,2);
                END IF;
                
                -- Adicionar observacoes se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='observacoes'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN observacoes TEXT;
                END IF;
                
                -- Alterar horario para aceitar NULL se existir
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='horario'
                ) THEN
                    ALTER TABLE sessoes ALTER COLUMN horario DROP NOT NULL;
                END IF;
            END $$;
        """)
        
        # Migração: Adicionar novos campos para estrutura completa de sessões (2026)
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar data se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='data'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN data DATE;
                END IF;
                
                -- Adicionar endereco se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='endereco'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN endereco TEXT;
                END IF;
                
                -- Adicionar descricao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='descricao'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN descricao TEXT;
                END IF;
                
                -- Adicionar prazo_entrega se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='prazo_entrega'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN prazo_entrega DATE;
                END IF;
                
                -- Adicionar dados_json se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='dados_json'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN dados_json JSONB;
                END IF;
                
                -- Adicionar empresa_id se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='empresa_id'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN empresa_id INTEGER REFERENCES empresas(id);
                END IF;
            END $$;
        """)
        
        # Tabela de tipos de sessi?o - DEPRECATED (removida da interface em 2026-01-23)
        # Mantida apenas para preservar dados existentes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipos_sessao (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                descricao TEXT,
                duracao_padrao INTEGER,
                valor_padrao DECIMAL(15,2),
                ativo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migrai?i?o: Adicionar colunas que podem faltar em tipos_sessao
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar descricao se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='descricao'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN descricao TEXT;
                END IF;
                
                -- Adicionar duracao_padrao se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='duracao_padrao'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN duracao_padrao INTEGER;
                END IF;
                
                -- Adicionar valor_padrao se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='valor_padrao'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN valor_padrao DECIMAL(15,2);
                END IF;
                
                -- Adicionar ativo se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='ativo'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN ativo BOOLEAN DEFAULT TRUE;
                END IF;
                
                -- Adicionar created_at se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='created_at'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
                
                -- Adicionar updated_at se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='updated_at'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Migrai?i?o: Adicionar colunas que podem faltar em produtos
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar descricao se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='descricao'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN descricao TEXT;
                END IF;
                
                -- Adicionar unidade se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='unidade'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN unidade VARCHAR(20) DEFAULT 'UN';
                END IF;
                
                -- Adicionar quantidade_minima se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='quantidade_minima'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN quantidade_minima DECIMAL(15,3) DEFAULT 0;
                END IF;
                
                -- Adicionar ativo se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='ativo'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN ativo BOOLEAN DEFAULT TRUE;
                END IF;
                
                -- Adicionar data_criacao se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='data_criacao'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Migrai?i?o: Adicionar colunas que podem faltar em kits
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar descricao se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='kits' AND column_name='descricao'
                ) THEN
                    ALTER TABLE kits ADD COLUMN descricao TEXT;
                END IF;
                
                -- Adicionar ativo se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='kits' AND column_name='ativo'
                ) THEN
                    ALTER TABLE kits ADD COLUMN ativo BOOLEAN DEFAULT TRUE;
                END IF;
                
                -- Adicionar data_criacao se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='kits' AND column_name='data_criacao'
                ) THEN
                    ALTER TABLE kits ADD COLUMN data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Migrai?i?o: Adicionar colunas que podem faltar em tags
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar data_criacao se ni?o existir  
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tags' AND column_name='data_criacao'
                ) THEN
                    ALTER TABLE tags ADD COLUMN data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Migrai?i?o: Adicionar colunas que podem faltar em templates_equipe
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar conteudo se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='conteudo'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN conteudo TEXT;
                END IF;
                
                -- Adicionar tipo se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='tipo'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN tipo VARCHAR(50);
                END IF;
                
                -- Adicionar descricao se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='descricao'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN descricao TEXT;
                END IF;
                
                -- Adicionar ativo se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='ativo'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN ativo BOOLEAN DEFAULT TRUE;
                END IF;
                
                -- Adicionar data_criacao se ni?o existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='data_criacao'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Tabela de comissi?es
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comissoes (
                id SERIAL PRIMARY KEY,
                contrato_id INTEGER REFERENCES contratos(id) ON DELETE CASCADE,
                cliente_id INTEGER REFERENCES clientes(id) ON DELETE CASCADE,
                tipo VARCHAR(50) DEFAULT 'percentual',
                descricao TEXT,
                valor DECIMAL(15,2) DEFAULT 0,
                percentual DECIMAL(5,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migrai?i?o: adicionar campos faltantes em comissoes
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='comissoes' AND column_name='contrato_id') THEN
                    ALTER TABLE comissoes ADD COLUMN contrato_id INTEGER REFERENCES contratos(id) ON DELETE CASCADE;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='comissoes' AND column_name='cliente_id') THEN
                    ALTER TABLE comissoes ADD COLUMN cliente_id INTEGER REFERENCES clientes(id) ON DELETE CASCADE;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='comissoes' AND column_name='tipo') THEN
                    ALTER TABLE comissoes ADD COLUMN tipo VARCHAR(50) DEFAULT 'percentual';
                END IF;
            END $$;
        """)
        
        # Migrai?i?o: tornar campos nullable em comissoes
        cursor.execute("""
            DO $$
            BEGIN
                ALTER TABLE comissoes ALTER COLUMN descricao DROP NOT NULL;
                ALTER TABLE comissoes ALTER COLUMN valor DROP NOT NULL;
            EXCEPTION WHEN OTHERS THEN
                NULL;
            END $$;
        """)
        
        # Tabela de equipe de sessi?o
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessao_equipe (
                id SERIAL PRIMARY KEY,
                sessao_id INTEGER NOT NULL REFERENCES sessoes(id) ON DELETE CASCADE,
                membro_nome VARCHAR(255) NOT NULL,
                funcao VARCHAR(100),
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ===== INICIALIZAi?i?O DE DADOS PADRi?O =====
        
        # Inserir permissi?es padri?o
        permissoes_padrao = [
            # Navegai?i?o
            ('dashboard', 'Dashboard', 'Visualizar dashboard principal', 'navegacao'),
            ('relatorios_view', 'Relati?rios', 'Acessar menu de relati?rios', 'navegacao'),
            ('cadastros_view', 'Cadastros', 'Acessar menu de cadastros', 'navegacao'),
            ('operacional_view', 'Operacional', 'Acessar menu operacional', 'navegacao'),
            
            # Financeiro
            ('lancamentos_view', 'Ver Lani?amentos', 'Visualizar lani?amentos financeiros', 'financeiro'),
            ('lancamentos_create', 'Criar Lani?amentos', 'Criar novos lani?amentos', 'financeiro'),
            ('lancamentos_edit', 'Editar Lani?amentos', 'Editar lani?amentos existentes', 'financeiro'),
            ('lancamentos_delete', 'Excluir Lani?amentos', 'Excluir lani?amentos', 'financeiro'),
            
            # Cadastros
            ('clientes_view', 'Ver Clientes', 'Visualizar clientes', 'cadastros'),
            ('clientes_create', 'Criar Clientes', 'Criar novos clientes', 'cadastros'),
            ('clientes_edit', 'Editar Clientes', 'Editar clientes existentes', 'cadastros'),
            ('clientes_delete', 'Excluir Clientes', 'Excluir clientes', 'cadastros'),
            ('fornecedores_view', 'Ver Fornecedores', 'Visualizar fornecedores', 'cadastros'),
            ('fornecedores_create', 'Criar Fornecedores', 'Criar novos fornecedores', 'cadastros'),
            ('fornecedores_edit', 'Editar Fornecedores', 'Editar fornecedores existentes', 'cadastros'),
            ('fornecedores_delete', 'Excluir Fornecedores', 'Excluir fornecedores', 'cadastros'),
            ('categorias_view', 'Ver Categorias', 'Visualizar categorias', 'cadastros'),
            ('categorias_create', 'Criar Categorias', 'Criar novas categorias', 'cadastros'),
            ('categorias_edit', 'Editar Categorias', 'Editar categorias existentes', 'cadastros'),
            ('categorias_delete', 'Excluir Categorias', 'Excluir categorias', 'cadastros'),
            ('contas_view', 'Ver Contas Bancárias', 'Visualizar contas bancárias', 'cadastros'),
            ('contas_create', 'Criar Contas Bancárias', 'Criar novas contas bancárias', 'cadastros'),
            ('contas_edit', 'Editar Contas Bancárias', 'Editar contas bancárias existentes', 'cadastros'),
            ('contas_delete', 'Excluir Contas Bancárias', 'Excluir contas bancárias', 'cadastros'),
            ('contas_bancarias_view', 'Ver Contas Bancárias', 'Visualizar contas bancárias', 'cadastros'),
            ('contas_bancarias_create', 'Criar Contas Bancárias', 'Criar novas contas bancárias', 'cadastros'),
            ('contas_bancarias_edit', 'Editar Contas Bancárias', 'Editar contas bancárias existentes', 'cadastros'),
            ('contas_bancarias_delete', 'Excluir Contas Bancárias', 'Excluir contas bancárias', 'cadastros'),
            
            # Operacional
            ('contratos_view', 'Ver Contratos', 'Visualizar contratos', 'operacional'),
            ('contratos_create', 'Criar Contratos', 'Criar novos contratos', 'operacional'),
            ('contratos_edit', 'Editar Contratos', 'Editar contratos existentes', 'operacional'),
            ('contratos_delete', 'Excluir Contratos', 'Excluir contratos', 'operacional'),
            ('sessoes_view', 'Ver Sessi?es', 'Visualizar sessi?es', 'operacional'),
            ('sessoes_create', 'Criar Sessi?es', 'Criar novas sessi?es', 'operacional'),
            ('sessoes_edit', 'Editar Sessi?es', 'Editar sessi?es existentes', 'operacional'),
            ('sessoes_delete', 'Excluir Sessi?es', 'Excluir sessi?es', 'operacional'),
            ('agenda_view', 'Ver Agenda', 'Visualizar agenda', 'operacional'),
            ('agenda_create', 'Criar Eventos (Agenda)', 'Criar eventos na agenda', 'operacional'),
            ('agenda_edit', 'Editar Eventos (Agenda)', 'Editar eventos da agenda', 'operacional'),
            ('agenda_delete', 'Excluir Eventos (Agenda)', 'Excluir eventos da agenda', 'operacional'),
            ('eventos_view', 'Ver Eventos Operacionais', 'Visualizar eventos operacionais', 'operacional'),
            ('eventos_create', 'Criar Eventos Operacionais', 'Criar novos eventos operacionais', 'operacional'),
            ('eventos_edit', 'Editar Eventos Operacionais', 'Editar eventos operacionais existentes', 'operacional'),
            ('eventos_delete', 'Excluir Eventos Operacionais', 'Excluir eventos operacionais', 'operacional'),
            ('estoque_view', 'Ver Estoque', 'Visualizar estoque e produtos', 'operacional'),
            ('estoque_create', 'Criar Produtos', 'Criar novos produtos no estoque', 'operacional'),
            ('estoque_edit', 'Editar Estoque', 'Editar produtos e movimentações de estoque', 'operacional'),
            ('estoque_delete', 'Excluir Produtos', 'Excluir produtos do estoque', 'operacional'),
            
            # Relati?rios
            ('exportar_pdf', 'Exportar PDF', 'Exportar dados em PDF', 'relatorios'),
            ('exportar_excel', 'Exportar Excel', 'Exportar dados em Excel', 'relatorios'),
            
            # Recursos Humanos
            ('folha_pagamento_view', 'Ver Folha de Pagamento', 'Visualizar folha de pagamento', 'recursos_humanos'),
            ('folha_pagamento_create', 'Criar Folha de Pagamento', 'Criar nova folha de pagamento', 'recursos_humanos'),
            ('folha_pagamento_edit', 'Editar Folha de Pagamento', 'Editar folha de pagamento', 'recursos_humanos'),
            ('folha_pagamento_delete', 'Excluir Folha de Pagamento', 'Excluir folha de pagamento', 'recursos_humanos'),
            
            # Sistema
            ('configuracoes', 'Configurai?i?es', 'Acessar configurai?i?es', 'sistema'),
            ('usuarios_admin', 'Gerenciar Usui?rios', 'Gerenciar usui?rios e permissi?es (apenas admin)', 'sistema')
        ]
        
        for codigo, nome, descricao, categoria in permissoes_padrao:
            cursor.execute("""
                INSERT INTO permissoes (codigo, nome, descricao, categoria, ativo)
                VALUES (%s, %s, %s, %s, TRUE)
                ON CONFLICT (codigo) DO NOTHING
            """, (codigo, nome, descricao, categoria))
        
        # Criar usui?rio admin padri?o se ni?o existir
        cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE tipo = 'admin'")
        admin_count = cursor.fetchone()['count']
        
        if admin_count == 0:
            import hashlib
            # Senha padri?o: "admin123" (deve ser alterada no primeiro login)
            senha_padrao = "admin123"
            password_hash = hashlib.sha256(senha_padrao.encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, tipo, nome_completo, email, ativo)
                VALUES ('admin', %s, 'admin', 'Administrador do Sistema', 'admin@sistema.com', TRUE)
                RETURNING id
            """, (password_hash,))
            
            admin_id = cursor.fetchone()['id']
            
            # Conceder todas as permissi?es ao admin
            cursor.execute("""
                INSERT INTO usuario_permissoes (usuario_id, permissao_id, concedido_por)
                SELECT %s, id, %s FROM permissoes
            """, (admin_id, admin_id))
            
            print("? Usui?rio admin criado com sucesso!")
            print("   Username: admin")
            print("   Senha: admin123")
        
        # ================================================================
        # MIGRAi?i?O: Multi-Tenancy - Adicionar proprietario_id
        # ================================================================
        try:
            print("?? Verificando migrai?i?o Multi-Tenancy...")
            
            # Lista de tabelas que precisam da coluna proprietario_id
            tabelas_multitenancy = [
                ('clientes', 'fk_clientes_proprietario', 'idx_clientes_proprietario'),
                ('fornecedores', 'fk_fornecedores_proprietario', 'idx_fornecedores_proprietario'),
                ('lancamentos', 'fk_lancamentos_proprietario', 'idx_lancamentos_proprietario'),
                ('contas_bancarias', 'fk_contas_bancarias_proprietario', 'idx_contas_bancarias_proprietario'),
                ('categorias', 'fk_categorias_proprietario', 'idx_categorias_proprietario'),
            ]
            
            for tabela, fk_name, idx_name in tabelas_multitenancy:
                # Verificar se a tabela existe antes de tentar modificar
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = %s
                    ) as table_exists
                """, (tabela,))
                
                result = cursor.fetchone()
                table_exists = result['table_exists'] if result else False
                
                if not table_exists:
                    print(f"   ??  Tabela '{tabela}' ni?o existe, pulando...")
                    continue
                
                # Adicionar coluna se ni?o existir
                cursor.execute(f"""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='{tabela}' AND column_name='proprietario_id'
                        ) THEN
                            ALTER TABLE {tabela} ADD COLUMN proprietario_id INTEGER;
                        END IF;
                    END $$;
                """)
                
                # Remover constraint antiga se existir (para recriar)
                cursor.execute(f"""
                    ALTER TABLE {tabela} DROP CONSTRAINT IF EXISTS {fk_name};
                """)
                
                # Adicionar foreign key
                cursor.execute(f"""
                    ALTER TABLE {tabela} 
                    ADD CONSTRAINT {fk_name} 
                    FOREIGN KEY (proprietario_id) 
                    REFERENCES usuarios(id) 
                    ON DELETE CASCADE;
                """)
                
                # Criar i?ndice
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {idx_name} 
                    ON {tabela}(proprietario_id);
                """)
            
            print("? Migrai?i?o Multi-Tenancy: Colunas proprietario_id adicionadas/verificadas")
            print("   - Tabelas processadas: clientes, fornecedores, lancamentos, contas_bancarias, categorias")
            
        except Exception as e:
            print(f"??  Aviso na migrai?i?o Multi-Tenancy: {e}")
            import traceback
            traceback.print_exc()
        
        print("   ??  ALTERE A SENHA DO ADMIN NO PRIMEIRO LOGIN!")
        
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
    
    def adicionar_conta(self, conta: ContaBancaria, proprietario_id: int = None, empresa_id: int = None) -> int:
        """Adiciona uma nova conta bancária"""
        # 🔒 empresa_id é obrigatório
        if not empresa_id:
            from flask import session
            empresa_id = session.get('empresa_id')
        if not empresa_id:
            raise ValueError("empresa_id é obrigatório para adicionar conta")
        
        # 👥 proprietario_id é OPCIONAL (ID do usuário, não empresa)
        # Se fornecido, validar que existe na tabela usuarios
        if proprietario_id:
            conn_check = self.get_connection()
            cursor_check = conn_check.cursor()
            cursor_check.execute("SELECT id FROM usuarios WHERE id = %s", (proprietario_id,))
            if not cursor_check.fetchone():
                cursor_check.close()
                return_to_pool(conn_check)
                raise ValueError(f"proprietario_id={proprietario_id} não existe na tabela usuarios. Use NULL ou um ID válido de usuário.")
            cursor_check.close()
            return_to_pool(conn_check)
        
        # 🔒 Usar get_db_connection com empresa_id para aplicar RLS
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO contas_bancarias 
                (nome, banco, agencia, conta, saldo_inicial, tipo_saldo_inicial, data_inicio, ativa, data_criacao, proprietario_id, empresa_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP), %s, %s)
                RETURNING id
            """, (
                conta.nome,
                conta.banco,
                conta.agencia,
                conta.conta,
                float(conta.saldo_inicial),
                conta.tipo_saldo_inicial,
                conta.data_inicio,
                conta.ativa,
                conta.data_criacao,
                proprietario_id,  # Pode ser None
                empresa_id  # OBRIGATÓRIO
            ))
            
            conta_id = cursor.fetchone()['id']
            conn.commit()
        
        return conta_id
        
        conta_id = cursor.fetchone()['id']
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return conta_id
    
    def listar_contas(self, filtro_cliente_id: int = None) -> List[ContaBancaria]:
        """Lista todas as contas bancárias (DEPRECATED - use listar_contas_por_empresa)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if filtro_cliente_id is not None:
            cursor.execute(
                "SELECT * FROM contas_bancarias WHERE proprietario_id = %s ORDER BY nome",
                (filtro_cliente_id,)
            )
        else:
            cursor.execute("SELECT * FROM contas_bancarias ORDER BY nome")
        rows = cursor.fetchall()
        
        contas = []
        for row in rows:
            conta = ContaBancaria(
                id=row['id'],
                nome=row['nome'],
                banco=row['banco'],
                agencia=row['agencia'],
                conta=row['conta'],
                saldo_inicial=Decimal(str(row['saldo_inicial'])),
                tipo_saldo_inicial=row.get('tipo_saldo_inicial', 'credor'),
                data_inicio=row.get('data_inicio'),
                ativa=row['ativa'],
                data_criacao=row['data_criacao']
            )
            contas.append(conta)
        
        cursor.close()
        return_to_pool(conn)
        return contas
    
    def listar_contas_por_empresa(self, empresa_id: int) -> List[ContaBancaria]:
        """Lista todas as contas bancárias de uma empresa (multi-tenancy correto)"""
        if not empresa_id:
            raise ValueError("empresa_id é obrigatório para listar contas")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM contas_bancarias WHERE empresa_id = %s ORDER BY nome",
            (empresa_id,)
        )
        rows = cursor.fetchall()
        
        contas = []
        for row in rows:
            conta = ContaBancaria(
                id=row['id'],
                nome=row['nome'],
                banco=row['banco'],
                agencia=row['agencia'],
                conta=row['conta'],
                saldo_inicial=Decimal(str(row['saldo_inicial'])),
                tipo_saldo_inicial=row.get('tipo_saldo_inicial', 'credor'),
                data_inicio=row.get('data_inicio'),
                ativa=row['ativa'],
                data_criacao=row['data_criacao']
            )
            contas.append(conta)
        
        cursor.close()
        return_to_pool(conn)
        return contas

        
        contas = []
        for row in rows:
            conta = ContaBancaria(
                id=row['id'],
                nome=row['nome'],
                banco=row['banco'],
                agencia=row['agencia'],
                conta=row['conta'],
                saldo_inicial=Decimal(str(row['saldo_inicial'])),
                tipo_saldo_inicial=row.get('tipo_saldo_inicial', 'credor'),
                data_inicio=row.get('data_inicio'),
                ativa=row['ativa'],
                data_criacao=row['data_criacao']
            )
            contas.append(conta)
        
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return contas
    
    def atualizar_conta(self, nome_antigo: str, conta: ContaBancaria) -> bool:
        """Atualiza uma conta banci?ria"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Se o nome mudou, verificar se o novo nome ji? existe
        if nome_antigo != conta.nome:
            cursor.execute("SELECT COUNT(*) as count FROM contas_bancarias WHERE nome = %s AND nome != %s", 
                         (conta.nome, nome_antigo))
            if cursor.fetchone()['count'] > 0:
                cursor.close()
                return_to_pool(conn)  # Devolver ao pool
                raise ValueError("Ji? existe uma conta com este nome")
        
        cursor.execute("""
            UPDATE contas_bancarias
            SET nome = %s, banco = %s, agencia = %s, conta = %s, saldo_inicial = %s, tipo_saldo_inicial = %s, data_inicio = %s, ativa = %s
            WHERE nome = %s
        """, (conta.nome, conta.banco, conta.agencia, conta.conta,
              float(conta.saldo_inicial), conta.tipo_saldo_inicial, conta.data_inicio, conta.ativa, nome_antigo))
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return success
    
    def excluir_conta(self, nome: str) -> bool:
        """Exclui uma conta banci?ria pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM contas_bancarias WHERE nome = %s", (nome,))
        sucesso = cursor.rowcount > 0
        
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def adicionar_categoria(self, categoria: Categoria) -> int:
        """Adiciona uma nova categoria com multi-tenancy"""
        # 🔒 Validar empresa_id obrigatório
        if not categoria.empresa_id:
            from flask import session
            categoria.empresa_id = session.get('empresa_id')
        if not categoria.empresa_id:
            raise ValueError("empresa_id é obrigatório para adicionar categoria")
        
        print(f"\n🔍 [adicionar_categoria]")
        print(f"   - empresa_id: {categoria.empresa_id}")
        print(f"   - nome: {categoria.nome}")
        print(f"   - tipo: {categoria.tipo.value}")
        
        # 🔒 Usar get_db_connection com empresa_id para aplicar RLS
        with get_db_connection(empresa_id=categoria.empresa_id) as conn:
            cursor = conn.cursor()
            
            subcategorias_json = json.dumps(categoria.subcategorias) if categoria.subcategorias else None
            
            cursor.execute("""
                INSERT INTO categorias 
                (nome, tipo, subcategorias, cor, icone, descricao, empresa_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                categoria.nome,
                categoria.tipo.value,
                subcategorias_json,
                categoria.cor,
                categoria.icone,
                categoria.descricao,
                categoria.empresa_id
            ))
            
            categoria_id = cursor.fetchone()['id']
            conn.commit()
            cursor.close()
            
            print(f"   ✅ Categoria criada com ID: {categoria_id}")
            return categoria_id
    
    def listar_categorias(self, tipo: Optional[TipoLancamento] = None, empresa_id: Optional[int] = None) -> List[Categoria]:
        """Lista todas as categorias, opcionalmente filtradas por tipo e empresa"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print('\n' + '='*80)
        print('🔍 DATABASE: listar_categorias() iniciada')
        print(f'   📍 Filtro por tipo: {tipo.value if tipo else "Nenhum (todos os tipos)"}')
        print(f'   🏢 Filtro por empresa_id: {empresa_id if empresa_id else "Nenhum (todas as empresas)"}')
        
        # Construir query com filtros
        query = "SELECT * FROM categorias WHERE 1=1"
        params = []
        
        if tipo:
            query += " AND tipo = %s"
            params.append(tipo.value)
        
        if empresa_id is not None:
            query += " AND (empresa_id = %s OR empresa_id IS NULL)"
            params.append(empresa_id)
        
        query += " ORDER BY nome"
        
        print(f'   📝 Query SQL: {query}')
        print(f'   📝 Params: {params}')
        
        cursor.execute(query, tuple(params))
        
        rows = cursor.fetchall()
        print(f'   📊 Rows retornadas do banco: {len(rows)}')
        
        categorias = []
        for row in rows:
            print(f'   🔎 Row: id={row["id"]}, nome={row["nome"]}, tipo={row["tipo"]}, empresa_id={row.get("empresa_id", "N/A")}')
            subcategorias = json.loads(row['subcategorias']) if row['subcategorias'] else []  # type: ignore
            
            categoria = Categoria(
                id=row['id'],
                nome=row['nome'],
                tipo=TipoLancamento(row['tipo']),
                subcategorias=subcategorias,
                cor=row['cor'],
                icone=row['icone'],
                descricao=row['descricao'],
                empresa_id=row.get('empresa_id')
            )
            categorias.append(categoria)
        
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        print(f'   ✅ Retornando {len(categorias)} categorias')
        print('='*80 + '\n')
        return categorias
    
    def excluir_categoria(self, nome: str) -> bool:
        """Exclui uma categoria pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Normalizar nome
        nome_normalizado = nome.upper().strip()
        cursor.execute("DELETE FROM categorias WHERE UPPER(TRIM(nome)) = %s", (nome_normalizado,))
        sucesso = cursor.rowcount > 0
        conn.commit()
        
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def atualizar_categoria(self, categoria: Categoria, nome_original: Optional[str] = None) -> bool:
        """Atualiza uma categoria pelo nome original
        
        Args:
            categoria: Objeto Categoria com os novos dados
            nome_original: Nome original da categoria (para localizar no banco)
                          Se None, usa categoria.nome como original
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print('🔄 DATABASE: atualizar_categoria() iniciada')
        print(f'   📝 Nome novo: {categoria.nome}')
        print(f'   📝 Nome original: {nome_original or categoria.nome}')
        print(f'   🏷️ Tipo: {categoria.tipo.value}')
        print(f'   🏢 Empresa ID: {getattr(categoria, "empresa_id", "N/A")}')
        
        subcategorias_json = json.dumps(categoria.subcategorias) if categoria.subcategorias else None
        
        # Normalizar nomes
        nome_novo_normalizado = categoria.nome.strip().upper()
        nome_busca = (nome_original or categoria.nome).strip().upper()
        
        print(f'   🔍 Buscando por (WHERE): {nome_busca}')
        print(f'   💾 Atualizando para (SET nome): {nome_novo_normalizado}')
        
        # Incluir empresa_id no UPDATE se estiver presente
        empresa_id = getattr(categoria, 'empresa_id', None)
        
        if empresa_id is not None:
            print(f'   ➡️ Atualizando COM empresa_id = {empresa_id}')
            cursor.execute("""
                UPDATE categorias 
                SET nome = %s, tipo = %s, subcategorias = %s, 
                    cor = %s, icone = %s, descricao = %s, empresa_id = %s
                WHERE UPPER(TRIM(nome)) = %s
            """, (
                nome_novo_normalizado,
                categoria.tipo.value,
                subcategorias_json,
                categoria.cor,
                categoria.icone,
                categoria.descricao,
                empresa_id,
                nome_busca
            ))
        else:
            print('   ➡️ Atualizando SEM empresa_id (mantém valor existente)')
            cursor.execute("""
                UPDATE categorias 
                SET nome = %s, tipo = %s, subcategorias = %s,
                    cor = %s, icone = %s, descricao = %s
                WHERE UPPER(TRIM(nome)) = %s
            """, (
                nome_novo_normalizado,
                categoria.tipo.value,
                subcategorias_json,
                categoria.cor,
                categoria.icone,
                categoria.descricao,
                nome_busca
            ))
        
        linhas_afetadas = cursor.rowcount
        sucesso = linhas_afetadas > 0
        
        # Se mudou o nome, também atualizar referências nos lançamentos
        if sucesso and nome_busca != nome_novo_normalizado:
            print(f'   🔄 Nome mudou! Atualizando referências nos lançamentos...')
            cursor.execute("""
                UPDATE lancamentos 
                SET categoria = %s 
                WHERE UPPER(TRIM(categoria)) = %s
            """, (nome_novo_normalizado, nome_busca))
            lancamentos_atualizados = cursor.rowcount
            print(f'   📊 {lancamentos_atualizados} lançamento(s) atualizado(s)')
        
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        
        print(f'   {"✅" if sucesso else "❌"} Linhas afetadas: {linhas_afetadas}')
        return sucesso
    
    def atualizar_nome_categoria(self, nome_antigo: str, nome_novo: str) -> bool:
        """Atualiza o nome de uma categoria e suas referi?ncias"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Atualizar nome da categoria
            cursor.execute(
                "UPDATE categorias SET nome = %s WHERE nome = %s",
                (nome_novo, nome_antigo)
            )
            
            # Atualizar referi?ncias nos lani?amentos
            cursor.execute(
                "UPDATE lancamentos SET categoria = %s WHERE categoria = %s",
                (nome_novo, nome_antigo)
            )
            
            cursor.close()
            return_to_pool(conn)  # Devolver ao pool
            return True
        except Exception as e:
            print(f"Erro ao atualizar categoria: {e}")
            cursor.close()
            return_to_pool(conn)  # Devolver ao pool
            return False
    
    def adicionar_cliente(self, cliente_data, cpf_cnpj: str = None, 
                         email: str = None, telefone: str = None,
                         endereco: str = None, proprietario_id: int = None,
                         cep: str = None, logradouro: str = None, numero: str = None,
                         complemento: str = None, bairro: str = None, 
                         cidade: str = None, estado: str = None) -> int:
        """Adiciona um novo cliente (aceita dict ou parâmetros individuais)"""
        # Aceitar dict ou parâmetros individuais
        if isinstance(cliente_data, dict):
            nome = cliente_data.get('nome')
            razao_social = cliente_data.get('razao_social', cliente_data.get('nome'))
            nome_fantasia = cliente_data.get('nome_fantasia')
            cpf_cnpj = cliente_data.get('cpf', cliente_data.get('cpf_cnpj'))
            cnpj = cliente_data.get('cnpj', cliente_data.get('cpf_cnpj'))
            documento = cliente_data.get('documento', cliente_data.get('cpf_cnpj'))
            ie = cliente_data.get('ie')
            im = cliente_data.get('im')
            email = cliente_data.get('email')
            telefone = cliente_data.get('telefone')
            endereco = cliente_data.get('endereco')
            # 🌐 Campos de endereço estruturado (PARTE 7)
            cep = cliente_data.get('cep')
            logradouro = cliente_data.get('logradouro')
            numero = cliente_data.get('numero')
            complemento = cliente_data.get('complemento')
            bairro = cliente_data.get('bairro')
            cidade = cliente_data.get('cidade')
            estado = cliente_data.get('estado')
            proprietario_id = cliente_data.get('proprietario_id', proprietario_id)
            empresa_id = cliente_data.get('empresa_id')  # 🔒 Pegar empresa_id
        else:
            nome = cliente_data
            razao_social = cliente_data
            nome_fantasia = None
            cnpj = cpf_cnpj
            documento = cpf_cnpj
            ie = None
            im = None
            empresa_id = None
        
        # 🔒 Validar empresa_id obrigatório
        if not empresa_id:
            from flask import session
            empresa_id = session.get('empresa_id')
        if not empresa_id:
            raise ValueError("empresa_id é obrigatório para adicionar cliente")
        
        # 🔒 Usar get_db_connection com empresa_id para aplicar RLS
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            # 🔄 Tentar inserir com campos estruturados (migration aplicada)
            # Se falhar, fazer fallback para apenas campo 'endereco' TEXT
            try:
                cursor.execute("""
                    INSERT INTO clientes (
                        nome, razao_social, nome_fantasia, cpf_cnpj, cnpj, documento, ie, im,
                        email, telefone, endereco, 
                        cep, logradouro, numero, complemento, bairro, cidade, estado,
                        proprietario_id, empresa_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (nome, razao_social, nome_fantasia, cpf_cnpj, cnpj, documento, ie, im,
                      email, telefone, endereco, 
                      cep, logradouro, numero, complemento, bairro, cidade, estado,
                      proprietario_id, empresa_id))
                
            except Exception as e:
                # ⚠️ Fallback: Se colunas estruturadas não existem, usar apenas 'endereco'
                if 'does not exist' in str(e) and 'cep' in str(e):
                    print(f"⚠️ Colunas de endereço estruturado não existem. Usando fallback...")
                    conn.rollback()
                    
                    # Montar endereço completo no campo TEXT
                    endereco_completo = endereco or ""
                    if cep or logradouro or numero:
                        partes = []
                        if logradouro: partes.append(logradouro)
                        if numero: partes.append(f"nº {numero}")
                        if complemento: partes.append(complemento)
                        if bairro: partes.append(bairro)
                        if cidade: partes.append(cidade)
                        if estado: partes.append(estado)
                        if cep: partes.append(f"CEP: {cep}")
                        endereco_completo = ", ".join(partes) if partes else endereco
                    
                    cursor.execute("""
                        INSERT INTO clientes (
                            nome, razao_social, nome_fantasia, cpf_cnpj, cnpj, documento, ie, im,
                            email, telefone, endereco,
                            proprietario_id, empresa_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (nome, razao_social, nome_fantasia, cpf_cnpj, cnpj, documento, ie, im,
                          email, telefone, endereco_completo,
                          proprietario_id, empresa_id))
                else:
                    raise  # Re-lançar outros erros
            
            cliente_id = cursor.fetchone()['id']
            conn.commit()
        
        return cliente_id
    
    def listar_clientes(self, ativos: bool = True, filtro_cliente_id: int = None) -> List[Dict]:
        """Lista todos os clientes com suporte a multi-tenancy
        
        Args:
            ativos: Se True, retorna apenas clientes ativos
            filtro_cliente_id: ID da empresa para filtrar (None = admin vê tudo)
        
        Note:
            filtro_cliente_id é na verdade o empresa_id do usuário logado,
            usado para garantir isolamento multi-tenant
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Construir query com filtro de multi-tenancy por EMPRESA
        if filtro_cliente_id is not None:
            # Usuário comum: ver apenas clientes da sua empresa
            if ativos:
                cursor.execute(
                    "SELECT * FROM clientes WHERE ativo = TRUE AND empresa_id = %s ORDER BY nome",
                    (filtro_cliente_id,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM clientes WHERE empresa_id = %s ORDER BY nome",
                    (filtro_cliente_id,)
                )
        else:
            # Admin: ver todos os clientes de todas as empresas
            if ativos:
                cursor.execute("SELECT * FROM clientes WHERE ativo = TRUE ORDER BY nome")
            else:
                cursor.execute("SELECT * FROM clientes ORDER BY nome")
        rows = cursor.fetchall()
        
        clientes = [dict(row) for row in rows]
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return clientes
    
    def atualizar_cliente(self, nome_antigo: str, dados: Dict) -> bool:
        """Atualiza os dados de um cliente pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome_antigo.upper().strip()
        
        # 🔄 Tentar atualizar com campos estruturados (migration aplicada)
        # Se falhar, fazer fallback para apenas campo 'endereco' TEXT
        try:
            cursor.execute("""
                UPDATE clientes 
                SET nome = %s, razao_social = %s, nome_fantasia = %s,
                    cpf_cnpj = %s, cnpj = %s, documento = %s, ie = %s, im = %s,
                    email = %s, telefone = %s, endereco = %s,
                    cep = %s, logradouro = %s, numero = %s,
                    complemento = %s, bairro = %s, cidade = %s, estado = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE UPPER(TRIM(nome)) = %s OR UPPER(TRIM(razao_social)) = %s
            """, (
                dados.get('nome'),
                dados.get('razao_social', dados.get('nome')),
                dados.get('nome_fantasia'),
                dados.get('cpf', dados.get('cpf_cnpj')),
                dados.get('cnpj', dados.get('cpf_cnpj')),
                dados.get('documento', dados.get('cpf_cnpj')),
                dados.get('ie'),
                dados.get('im'),
                dados.get('email'),
                dados.get('telefone'),
                dados.get('endereco'),
                # 🌐 Campos de endereço estruturado (PARTE 7)
                dados.get('cep'),
                dados.get('logradouro'),
                dados.get('numero'),
                dados.get('complemento'),
                dados.get('bairro'),
                dados.get('cidade'),
                dados.get('estado'),
                nome_normalizado,
                nome_normalizado
            ))
            
        except Exception as e:
            # ⚠️ Fallback: Se colunas estruturadas não existem, usar apenas 'endereco'
            if 'does not exist' in str(e) and 'cep' in str(e):
                print(f"⚠️ Colunas de endereço estruturado não existem. Usando fallback...")
                conn.rollback()
                
                # Montar endereço completo no campo TEXT
                endereco = dados.get('endereco') or ""
                cep = dados.get('cep')
                logradouro = dados.get('logradouro')
                numero = dados.get('numero')
                complemento = dados.get('complemento')
                bairro = dados.get('bairro')
                cidade = dados.get('cidade')
                estado = dados.get('estado')
                
                if cep or logradouro or numero:
                    partes = []
                    if logradouro: partes.append(logradouro)
                    if numero: partes.append(f"nº {numero}")
                    if complemento: partes.append(complemento)
                    if bairro: partes.append(bairro)
                    if cidade: partes.append(cidade)
                    if estado: partes.append(estado)
                    if cep: partes.append(f"CEP: {cep}")
                    endereco = ", ".join(partes) if partes else endereco
                
                cursor.execute("""
                    UPDATE clientes 
                    SET nome = %s, razao_social = %s, nome_fantasia = %s,
                        cpf_cnpj = %s, cnpj = %s, documento = %s, ie = %s, im = %s,
                        email = %s, telefone = %s, endereco = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE UPPER(TRIM(nome)) = %s OR UPPER(TRIM(razao_social)) = %s
                """, (
                    dados.get('nome'),
                    dados.get('razao_social', dados.get('nome')),
                    dados.get('nome_fantasia'),
                    dados.get('cpf', dados.get('cpf_cnpj')),
                    dados.get('cnpj', dados.get('cpf_cnpj')),
                    dados.get('documento', dados.get('cpf_cnpj')),
                    dados.get('ie'),
                    dados.get('im'),
                    dados.get('email'),
                    dados.get('telefone'),
                    endereco,
                    nome_normalizado,
                    nome_normalizado
                ))
            else:
                raise  # Re-lançar outros erros
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def inativar_cliente(self, nome: str, motivo: str = "") -> tuple[bool, str]:
        """Inativa um cliente pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome.upper().strip()
        cursor.execute("""
            UPDATE clientes 
            SET ativo = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE UPPER(TRIM(nome)) = %s
        """, (nome_normalizado,))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return (sucesso, "Cliente inativado com sucesso" if sucesso else "Cliente ni?o encontrado")
    
    def reativar_cliente(self, nome: str) -> bool:
        """Reativa um cliente pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome.upper().strip()
        cursor.execute("""
            UPDATE clientes 
            SET ativo = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE UPPER(TRIM(nome)) = %s
        """, (nome_normalizado,))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def obter_cliente_por_nome(self, nome: str) -> Dict | None:
        """Busca um cliente pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome.upper().strip()
        cursor.execute("""
            SELECT * FROM clientes 
            WHERE UPPER(TRIM(nome)) = %s
        """, (nome_normalizado,))
        
        row = cursor.fetchone()
        cursor.close()
        return_to_pool(conn)
        
        return dict(row) if row else None
    
    def excluir_cliente(self, nome: str) -> tuple[bool, str]:
        """Exclui um cliente pelo nome (verifica se não tem lançamentos ou contratos vinculados)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome.upper().strip()
        
        # Primeiro, buscar o ID do cliente pelo nome
        cursor.execute("""
            SELECT id FROM clientes 
            WHERE UPPER(TRIM(nome)) = %s
        """, (nome_normalizado,))
        
        cliente_row = cursor.fetchone()
        if not cliente_row:
            cursor.close()
            return_to_pool(conn)
            return (False, "Cliente não encontrado")
        
        cliente_id = cliente_row['id']
        
        # Verificar se tem lançamentos vinculados (pelo nome)
        cursor.execute("""
            SELECT COUNT(*) as total FROM lancamentos 
            WHERE UPPER(TRIM(cliente_fornecedor)) = %s
        """, (nome_normalizado,))
        
        result = cursor.fetchone()
        if result and result['total'] > 0:
            cursor.close()
            return_to_pool(conn)
            return (False, f"Cliente possui {result['total']} lançamento(s) vinculado(s)")
        
        # Verificar se tem contratos vinculados (pelo ID)
        cursor.execute("""
            SELECT COUNT(*) as total FROM contratos 
            WHERE cliente_id = %s
        """, (cliente_id,))
        
        result_contratos = cursor.fetchone()
        if result_contratos and result_contratos['total'] > 0:
            cursor.close()
            return_to_pool(conn)
            return (False, f"Cliente possui {result_contratos['total']} contrato(s) vinculado(s)")
        
        # Verificar se tem sessões vinculadas
        cursor.execute("""
            SELECT COUNT(*) as total FROM sessoes 
            WHERE cliente_id = %s
        """, (cliente_id,))
        
        result_sessoes = cursor.fetchone()
        if result_sessoes and result_sessoes['total'] > 0:
            cursor.close()
            return_to_pool(conn)
            return (False, f"Cliente possui {result_sessoes['total']} sessão(ões) vinculada(s)")
        
        # Se não tem vínculos, pode excluir
        cursor.execute("""
            DELETE FROM clientes 
            WHERE id = %s
        """, (cliente_id,))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        
        return (sucesso, "Cliente excluído com sucesso" if sucesso else "Cliente não encontrado")
    
    def adicionar_fornecedor(self, fornecedor_data, cpf_cnpj: str = None,
                           email: str = None, telefone: str = None,
                           endereco: str = None, proprietario_id: int = None,
                           cep: str = None, logradouro: str = None, numero: str = None,
                           complemento: str = None, bairro: str = None, 
                           cidade: str = None, estado: str = None) -> int:
        """Adiciona um novo fornecedor com multi-tenancy"""
        # Aceitar dict ou parâmetros individuais
        if isinstance(fornecedor_data, dict):
            nome = fornecedor_data.get('nome')
            razao_social = fornecedor_data.get('razao_social', fornecedor_data.get('nome'))
            nome_fantasia = fornecedor_data.get('nome_fantasia')
            cpf_cnpj = fornecedor_data.get('cnpj', fornecedor_data.get('cpf_cnpj'))
            cnpj = fornecedor_data.get('cnpj', fornecedor_data.get('cpf_cnpj'))
            documento = fornecedor_data.get('documento', fornecedor_data.get('cpf_cnpj'))
            ie = fornecedor_data.get('ie')
            im = fornecedor_data.get('im')
            email = fornecedor_data.get('email')
            telefone = fornecedor_data.get('telefone')
            endereco = fornecedor_data.get('endereco')
            # 🌐 Campos de endereço estruturado
            cep = fornecedor_data.get('cep')
            logradouro = fornecedor_data.get('logradouro')
            numero = fornecedor_data.get('numero')
            complemento = fornecedor_data.get('complemento')
            bairro = fornecedor_data.get('bairro')
            cidade = fornecedor_data.get('cidade')
            estado = fornecedor_data.get('estado')
            proprietario_id = fornecedor_data.get('proprietario_id', proprietario_id)
            empresa_id = fornecedor_data.get('empresa_id')
        else:
            nome = fornecedor_data
            razao_social = fornecedor_data
            nome_fantasia = None
            cnpj = cpf_cnpj
            documento = cpf_cnpj
            ie = None
            im = None
            empresa_id = None
        
        # 🔒 Validar empresa_id obrigatório
        if not empresa_id:
            from flask import session
            empresa_id = session.get('empresa_id')
        if not empresa_id:
            raise ValueError("empresa_id é obrigatório para adicionar fornecedor")
        
        # 🔒 Validar proprietario_id se fornecido
        if proprietario_id:
            with get_db_connection(empresa_id=empresa_id) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM usuarios WHERE id = %s", (proprietario_id,))
                if not cursor.fetchone():
                    cursor.close()
                    raise ValueError(f"proprietario_id {proprietario_id} não existe na tabela usuarios")
                cursor.close()
        
        print(f"\n🔍 [adicionar_fornecedor]")
        print(f"   - empresa_id: {empresa_id}")
        print(f"   - nome: {nome}")
        print(f"   - proprietario_id: {proprietario_id}")
        
        # 🔒 Usar get_db_connection com empresa_id para aplicar RLS
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            # 🔄 Tentar inserir com campos estruturados (migration aplicada)
            try:
                cursor.execute("""
                    INSERT INTO fornecedores (
                        nome, razao_social, nome_fantasia, cpf_cnpj, cnpj, documento, ie, im,
                        email, telefone, endereco,
                        cep, logradouro, numero, complemento, bairro, cidade, estado,
                        proprietario_id, empresa_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (nome, razao_social, nome_fantasia, cpf_cnpj, cnpj, documento, ie, im,
                      email, telefone, endereco,
                      cep, logradouro, numero, complemento, bairro, cidade, estado,
                      proprietario_id, empresa_id))
            
            except Exception as e:
                # ⚠️ Fallback: Se colunas estruturadas não existem
                if 'does not exist' in str(e):
                    print(f"⚠️ Colunas estruturadas não existem. Usando fallback...")
                    conn.rollback()
                    
                    # Montar endereço completo no campo TEXT
                    endereco_completo = endereco or ""
                    if cep or logradouro or numero:
                        partes = []
                        if logradouro: partes.append(logradouro)
                        if numero: partes.append(f"nº {numero}")
                        if complemento: partes.append(complemento)
                        if bairro: partes.append(bairro)
                        if cidade: partes.append(cidade)
                        if estado: partes.append(estado)
                        if cep: partes.append(f"CEP: {cep}")
                        endereco_completo = ", ".join(partes) if partes else endereco
                    
                    cursor.execute("""
                        INSERT INTO fornecedores (
                            nome, razao_social, nome_fantasia, cpf_cnpj, cnpj, documento, ie, im,
                            email, telefone, endereco, proprietario_id, empresa_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (nome, razao_social, nome_fantasia, cpf_cnpj, cnpj, documento, ie, im,
                          email, telefone, endereco_completo, proprietario_id, empresa_id))
                else:
                    raise  # Re-lançar outros erros
            
            fornecedor_id = cursor.fetchone()['id']
            conn.commit()
            cursor.close()
            
            print(f"   ✅ Fornecedor criado com ID: {fornecedor_id}")
            return fornecedor_id
    
    def listar_fornecedores(self, ativos: bool = True, filtro_cliente_id: int = None) -> List[Dict]:
        """Lista todos os fornecedores com suporte a multi-tenancy
        
        Args:
            ativos: Se True, retorna apenas fornecedores ativos
            filtro_cliente_id: ID da empresa para filtrar (None = admin vê tudo)
        
        Note:
            filtro_cliente_id é na verdade o empresa_id do usuário logado,
            usado para garantir isolamento multi-tenant
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Construir query com filtro de multi-tenancy por EMPRESA
        if filtro_cliente_id is not None:
            # Usuário comum: ver apenas fornecedores da sua empresa
            if ativos:
                cursor.execute(
                    "SELECT * FROM fornecedores WHERE ativo = TRUE AND empresa_id = %s ORDER BY nome",
                    (filtro_cliente_id,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM fornecedores WHERE empresa_id = %s ORDER BY nome",
                    (filtro_cliente_id,)
                )
        else:
            # Admin: ver todos os fornecedores de todas as empresas
            if ativos:
                cursor.execute("SELECT * FROM fornecedores WHERE ativo = TRUE ORDER BY nome")
            else:
                cursor.execute("SELECT * FROM fornecedores ORDER BY nome")
        rows = cursor.fetchall()
        
        fornecedores = [dict(row) for row in rows]
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return fornecedores
    
    def obter_fornecedor_por_nome(self, nome: str) -> Dict | None:
        """Busca um fornecedor pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome.upper().strip()
        cursor.execute("""
            SELECT * FROM fornecedores 
            WHERE UPPER(TRIM(nome)) = %s
        """, (nome_normalizado,))
        
        row = cursor.fetchone()
        cursor.close()
        return_to_pool(conn)
        
        return dict(row) if row else None
    
    def atualizar_fornecedor(self, nome_antigo: str, dados: Dict) -> bool:
        """Atualiza os dados de um fornecedor pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome_antigo.upper().strip()
        
        # 🔄 Tentar atualizar com campos estruturados
        try:
            cursor.execute("""
                UPDATE fornecedores 
                SET nome = %s, razao_social = %s, nome_fantasia = %s,
                    cpf_cnpj = %s, cnpj = %s, documento = %s, ie = %s, im = %s,
                    email = %s, telefone = %s, endereco = %s,
                    cep = %s, logradouro = %s, numero = %s,
                    complemento = %s, bairro = %s, cidade = %s, estado = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE UPPER(TRIM(nome)) = %s OR UPPER(TRIM(razao_social)) = %s
            """, (
                dados.get('nome'),
                dados.get('razao_social', dados.get('nome')),
                dados.get('nome_fantasia'),
                dados.get('cnpj', dados.get('cpf_cnpj')),
                dados.get('cnpj', dados.get('cpf_cnpj')),
                dados.get('documento', dados.get('cpf_cnpj')),
                dados.get('ie'),
                dados.get('im'),
                dados.get('email'),
                dados.get('telefone'),
                dados.get('endereco'),
                dados.get('cep'),
                dados.get('logradouro'),
                dados.get('numero'),
                dados.get('complemento'),
                dados.get('bairro'),
                dados.get('cidade'),
                dados.get('estado'),
                nome_normalizado,
                nome_normalizado
            ))
        
        except Exception as e:
            # ⚠️ Fallback: Se colunas estruturadas não existem
            if 'does not exist' in str(e):
                print(f"⚠️ Colunas de endereço estruturado não existem. Usando fallback...")
                conn.rollback()
                
                # Montar endereço completo
                endereco = dados.get('endereco') or ""
                cep = dados.get('cep')
                logradouro = dados.get('logradouro')
                numero = dados.get('numero')
                complemento = dados.get('complemento')
                bairro = dados.get('bairro')
                cidade = dados.get('cidade')
                estado = dados.get('estado')
                
                if cep or logradouro or numero:
                    partes = []
                    if logradouro: partes.append(logradouro)
                    if numero: partes.append(f"nº {numero}")
                    if complemento: partes.append(complemento)
                    if bairro: partes.append(bairro)
                    if cidade: partes.append(cidade)
                    if estado: partes.append(estado)
                    if cep: partes.append(f"CEP: {cep}")
                    endereco = ", ".join(partes) if partes else endereco
                
                cursor.execute("""
                    UPDATE fornecedores 
                    SET nome = %s, razao_social = %s, nome_fantasia = %s,
                        cpf_cnpj = %s, cnpj = %s, documento = %s, ie = %s, im = %s,
                        email = %s, telefone = %s, endereco = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE UPPER(TRIM(nome)) = %s OR UPPER(TRIM(razao_social)) = %s
                """, (
                    dados.get('nome'),
                    dados.get('razao_social', dados.get('nome')),
                    dados.get('nome_fantasia'),
                    dados.get('cnpj', dados.get('cpf_cnpj')),
                    dados.get('cnpj', dados.get('cpf_cnpj')),
                    dados.get('documento', dados.get('cpf_cnpj')),
                    dados.get('ie'),
                    dados.get('im'),
                    dados.get('email'),
                    dados.get('telefone'),
                    endereco,
                    nome_normalizado,
                    nome_normalizado
                ))
            else:
                raise  # Re-lançar outros erros
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def inativar_fornecedor(self, nome: str, motivo: str = "") -> tuple[bool, str]:
        """Inativa um fornecedor pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome.upper().strip()
        cursor.execute("""
            UPDATE fornecedores 
            SET ativo = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE UPPER(TRIM(nome)) = %s
        """, (nome_normalizado,))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return (sucesso, "Fornecedor inativado com sucesso" if sucesso else "Fornecedor ni?o encontrado")
    
    def reativar_fornecedor(self, nome: str) -> bool:
        """Reativa um fornecedor pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome.upper().strip()
        cursor.execute("""
            UPDATE fornecedores 
            SET ativo = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE UPPER(TRIM(nome)) = %s
        """, (nome_normalizado,))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def adicionar_lancamento(self, lancamento: Lancamento, proprietario_id: int = None, empresa_id: int = None) -> int:
        """Adiciona um novo lançamento com multi-tenancy"""
        # 🔒 Validar empresa_id obrigatório
        if not empresa_id:
            from flask import session
            empresa_id = session.get('empresa_id')
        if not empresa_id:
            raise ValueError("empresa_id é obrigatório para adicionar lançamento")
        
        # 🔒 Validar proprietario_id se fornecido
        if proprietario_id:
            with get_db_connection(empresa_id=empresa_id) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM usuarios WHERE id = %s", (proprietario_id,))
                if not cursor.fetchone():
                    cursor.close()
                    raise ValueError(f"proprietario_id {proprietario_id} não existe na tabela usuarios")
                cursor.close()
        
        print(f"\n🔍 [adicionar_lancamento]")
        print(f"   - empresa_id: {empresa_id}")
        print(f"   - proprietario_id: {proprietario_id}")
        print(f"   - descrição: {lancamento.descricao}")
        print(f"   - valor: {lancamento.valor}")
        
        # 🔒 Usar get_db_connection com empresa_id para aplicar RLS
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO lancamentos 
                (tipo, descricao, valor, data_vencimento, data_pagamento,
                 categoria, subcategoria, conta_bancaria, cliente_fornecedor, pessoa,
                 status, observacoes, anexo, recorrente, frequencia_recorrencia, dia_vencimento, proprietario_id, empresa_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                lancamento.tipo.value,
                lancamento.descricao,
                float(lancamento.valor),
                lancamento.data_vencimento,
                lancamento.data_pagamento,
                lancamento.categoria,
                lancamento.subcategoria,
                lancamento.conta_bancaria,
                lancamento.cliente_fornecedor,
                lancamento.pessoa,
                lancamento.status.value,
                lancamento.observacoes,
                lancamento.anexo,
                lancamento.recorrente,
                lancamento.frequencia_recorrencia,
                lancamento.dia_vencimento,
                proprietario_id,
                empresa_id
            ))
            
            lancamento_id = cursor.fetchone()['id']
            conn.commit()
            cursor.close()
            
            print(f"   ✅ Lançamento criado com ID: {lancamento_id}")
            return lancamento_id
    
    def listar_lancamentos(self, empresa_id: int = None, filtros: Dict[str, Any] = None, 
                          filtro_cliente_id: int = None, page: int = None, per_page: int = 50) -> List[Lancamento]:
        """
        Lista lani?amentos com filtros opcionais, multi-tenancy e pagina??o
        
        Args:
            empresa_id: ID da empresa para filtro (opcional)
            filtros: Dicionário com filtros (tipo, status, datas, etc)
            filtro_cliente_id: ID do cliente para multi-tenancy
            page: Número da página (1-indexed). Se None, retorna todos.
            per_page: Itens por página (padrão: 50, máx: 500)
        
        Returns:
            Lista de objetos Lancamento
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Colunas específicas (otimização: evitar SELECT *)
        columns = """
            id, tipo, descricao, valor, data_vencimento, data_pagamento,
            categoria, subcategoria, conta_bancaria, cliente_fornecedor,
            pessoa, status, observacoes, anexo, recorrente,
            frequencia_recorrencia, dia_vencimento
        """
        
        query = f"SELECT {columns} FROM lancamentos WHERE 1=1"
        params = []
        
        # NOTA: Tabela lancamentos ainda não tem coluna proprietario_id ou empresa_id
        # Filtro de multi-tenancy temporariamente desabilitado até migração
        # TODO: Adicionar coluna empresa_id à tabela lancamentos
        # if empresa_id is not None:
        #     query += " AND empresa_id = %s"
        #     params.append(empresa_id)
        # if filtro_cliente_id is not None:
        #     query += " AND empresa_id = %s"
        #     params.append(filtro_cliente_id)
        
        if filtros:
            if 'tipo' in filtros:
                query += " AND UPPER(tipo) = UPPER(%s)"
                params.append(filtros['tipo'])
            if 'status' in filtros:
                query += " AND UPPER(status) = UPPER(%s)"
                params.append(filtros['status'])
            if 'data_inicio' in filtros:
                query += " AND data_vencimento >= %s"
                params.append(filtros['data_inicio'])
            if 'data_fim' in filtros:
                query += " AND data_vencimento <= %s"
                params.append(filtros['data_fim'])
            if 'categoria' in filtros:
                query += " AND categoria = %s"
                params.append(filtros['categoria'])
            if 'conta_bancaria' in filtros:
                query += " AND conta_bancaria = %s"
                params.append(filtros['conta_bancaria'])
        
        query += " ORDER BY data_vencimento DESC"
        
        # Adicionar paginação se especificado
        if page is not None:
            per_page = min(per_page, 500)  # Máximo 500 por página
            offset = (page - 1) * per_page
            query += f" LIMIT {per_page} OFFSET {offset}"
        
        print(f"🔍 SQL Query: {query}")
        print(f"📋 Params: {params}")
        print(f"📄 Page: {page}, Per Page: {per_page}")
        
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            print(f"✅ Query executada com sucesso! Rows: {len(rows)}")
        except Exception as e:
            print(f"❌ Erro ao executar query: {e}")
            import traceback
            traceback.print_exc()
            cursor.close()
            return_to_pool(conn)
            raise
        
        lancamentos = []
        for row in rows:
            try:
                # Tratar valores que podem ser None
                tipo_value = row['tipo'].lower() if row['tipo'] else 'receita'
                status_value = row['status'].lower() if row['status'] else 'pendente'
                
                lancamento = Lancamento(
                    id=row['id'],
                    tipo=TipoLancamento(tipo_value),
                    descricao=row['descricao'],
                    valor=Decimal(str(row['valor'])),
                    data_vencimento=row['data_vencimento'],
                    data_pagamento=row['data_pagamento'],
                    categoria=row['categoria'] or '',
                    subcategoria=row['subcategoria'] or '',
                    conta_bancaria=row['conta_bancaria'] or '',
                    cliente_fornecedor=row['cliente_fornecedor'] or '',
                    pessoa=row['pessoa'] or '',
                    status=StatusLancamento(status_value),
                    observacoes=row['observacoes'] or '',
                    anexo=row['anexo'] or '',
                    recorrente=row['recorrente'] or False,
                    frequencia_recorrencia=row['frequencia_recorrencia'] or '',
                    dia_vencimento=row['dia_vencimento'] or 0
                )
                lancamentos.append(lancamento)
            except Exception as e:
                print(f"? Erro ao processar lani?amento ID {row.get('id', 'unknown')}: {e}")
                continue
        
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return lancamentos
    
    def obter_lancamento(self, lancamento_id: int) -> Optional[Lancamento]:
        """Obti?m um lani?amento especi?fico por ID"""
        print(f"\n?? obter_lancamento() chamado com ID: {lancamento_id}")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM lancamentos WHERE id = %s"
        print(f"?? Query: {query}")
        print(f"?? Params: ({lancamento_id},)")
        
        try:
            cursor.execute(query, (lancamento_id,))
            row = cursor.fetchone()
            print(f"? Row encontrada: {row is not None}")
        except Exception as e:
            print(f"? ERRO ao executar query: {e}")
            cursor.close()
            return_to_pool(conn)  # Devolver ao pool
            raise
        
        if not row:
            cursor.close()
            return_to_pool(conn)  # Devolver ao pool
            return None
        
        # Tratar valores que podem ser None
        tipo_value = row['tipo'].lower() if row['tipo'] else 'receita'
        status_value = row['status'].lower() if row['status'] else 'pendente'
        
        print(f"?? Construindo Lancamento com:")
        print(f"   - juros: {row.get('juros', 0)}")
        print(f"   - desconto: {row.get('desconto', 0)}")
        
        lancamento = Lancamento(
            id=row['id'],
            tipo=TipoLancamento(tipo_value),
            descricao=row['descricao'],
            valor=Decimal(str(row['valor'])),
            data_vencimento=row['data_vencimento'],
            data_pagamento=row['data_pagamento'],
            categoria=row['categoria'] or '',
            subcategoria=row['subcategoria'] or '',
            conta_bancaria=row['conta_bancaria'] or '',
            cliente_fornecedor=row['cliente_fornecedor'] or '',
            pessoa=row['pessoa'] or '',
            status=StatusLancamento(status_value),
            observacoes=row['observacoes'] or '',
            anexo=row['anexo'] or '',
            recorrente=row['recorrente'] or False,
            frequencia_recorrencia=row['frequencia_recorrencia'] or '',
            dia_vencimento=row['dia_vencimento'] or 0,
            juros=float(row.get('juros', 0)) if row.get('juros') is not None else 0,
            desconto=float(row.get('desconto', 0)) if row.get('desconto') is not None else 0
        )
        
        print(f"? Lancamento criado com sucesso\n")
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return lancamento
    
    def excluir_lancamento(self, lancamento_id: int) -> bool:
        """Exclui um lani?amento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM lancamentos WHERE id = %s", (lancamento_id,))
        sucesso = cursor.rowcount > 0
        
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def atualizar_lancamento(self, lancamento: Lancamento) -> bool:
        """Atualiza um lani?amento existente"""
        print(f"\n?? DatabaseManager.atualizar_lancamento() chamada:")
        print(f"   ID: {lancamento.id}")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            UPDATE lancamentos 
            SET tipo = %s, descricao = %s, valor = %s, data_vencimento = %s,
                data_pagamento = %s, categoria = %s, subcategoria = %s,
                conta_bancaria = %s, cliente_fornecedor = %s, pessoa = %s,
                status = %s, observacoes = %s, anexo = %s,
                recorrente = %s, frequencia_recorrencia = %s, dia_vencimento = %s,
                juros = %s, desconto = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        params = (
            lancamento.tipo.value if hasattr(lancamento.tipo, 'value') else str(lancamento.tipo),
            lancamento.descricao,
            float(lancamento.valor),
            lancamento.data_vencimento,
            lancamento.data_pagamento,
            lancamento.categoria,
            lancamento.subcategoria,
            lancamento.conta_bancaria or '',
            lancamento.cliente_fornecedor or '',
            lancamento.pessoa or '',
            lancamento.status.value if hasattr(lancamento.status, 'value') else str(lancamento.status),
            lancamento.observacoes or '',
            lancamento.anexo or '',
            lancamento.recorrente,
            lancamento.frequencia_recorrencia or '',
            lancamento.dia_vencimento or 0,
            getattr(lancamento, 'juros', 0),
            getattr(lancamento, 'desconto', 0),
            lancamento.id
        )
        
        print(f"?? Query: {query}")
        print(f"?? Params: {params}")
        
        cursor.execute(query, params)
        sucesso = cursor.rowcount > 0
        
        print(f"? Linhas afetadas: {cursor.rowcount}, Sucesso: {sucesso}\n")
        
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def pagar_lancamento(self, lancamento_id: int, conta: str = '', data_pagamento: date = None,
                        juros: float = 0, desconto: float = 0, observacoes: str = '',
                        valor_pago: Optional[Decimal] = None) -> bool:
        """Marca um lani?amento como pago"""
        print(f"\n?? DatabaseManager.pagar_lancamento() chamada:")
        print(f"   - lancamento_id: {lancamento_id} (tipo: {type(lancamento_id)})")
        print(f"   - conta: {conta} (tipo: {type(conta)})")
        print(f"   - data_pagamento: {data_pagamento} (tipo: {type(data_pagamento)})")
        print(f"   - juros: {juros} (tipo: {type(juros)})")
        print(f"   - desconto: {desconto} (tipo: {type(desconto)})")
        print(f"   - observacoes: {observacoes} (tipo: {type(observacoes)})")
        print(f"   - valor_pago: {valor_pago} (tipo: {type(valor_pago)})")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Se ni?o passar data_pagamento, usar a data atual
        if not data_pagamento:
            data_pagamento = date.today()
            print(f"??  Data ni?o fornecida, usando hoje: {data_pagamento}")
        
        if valor_pago:
            query = """
                UPDATE lancamentos 
                SET status = %s, data_pagamento = %s, valor = %s, 
                    conta_bancaria = %s, juros = %s, desconto = %s, observacoes = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            params = (StatusLancamento.PAGO.value, data_pagamento, float(valor_pago), 
                  conta, juros, desconto, observacoes, lancamento_id)
            print(f"?? Query COM valor_pago:")
            print(f"   SQL: {query}")
            print(f"   Params: {params}")
            cursor.execute(query, params)
        else:
            query = """
                UPDATE lancamentos 
                SET status = %s, data_pagamento = %s,
                    conta_bancaria = %s, juros = %s, desconto = %s, observacoes = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            params = (StatusLancamento.PAGO.value, data_pagamento, 
                  conta, juros, desconto, observacoes, lancamento_id)
            print(f"?? Query SEM valor_pago:")
            print(f"   SQL: {query}")
            print(f"   Params: {params}")
            cursor.execute(query, params)
        
        sucesso = cursor.rowcount > 0
        print(f"? Linhas afetadas: {cursor.rowcount}, Sucesso: {sucesso}")
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def cancelar_lancamento(self, lancamento_id: int) -> bool:
        """Cancela um lani?amento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE lancamentos 
            SET status = %s, data_pagamento = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (StatusLancamento.PENDENTE.value, lancamento_id))
        
        sucesso = cursor.rowcount > 0
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def migrar_dados_json(self, json_path: str, empresa_id: int = None):
        """
        Migra dados de um arquivo JSON para o banco
        
        Args:
            json_path (str): Caminho do arquivo JSON
            empresa_id (int): ID da empresa para vincular os dados [RECOMENDADO]
            
        Warning:
            Se empresa_id não fornecido, dados serão criados sem vínculo de empresa
            
        Security:
            🔒 Recomendado passar empresa_id para garantir isolamento
        """
        if not os.path.exists(json_path):
            print(f"Arquivo {json_path} ni?o encontrado")
            return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Migrar contas
        for conta_data in dados.get('contas', []):
            conta = ContaBancaria(**conta_data)
            try:
                if empresa_id:
                    # Se tiver empresa_id, usar wrapper que exige empresa_id
                    # TODO: Implementar adicionar_conta com empresa_id no wrapper
                    self.adicionar_conta(conta)
                else:
                    self.adicionar_conta(conta)
            except Exception as e:
                print(f"Erro ao migrar conta {conta.nome}: {e}")
        
        # Migrar categorias
        for cat_data in dados.get('categorias', []):
            categoria = Categoria(**cat_data)
            try:
                if empresa_id:
                    # Se tiver empresa_id, usar wrapper que exige empresa_id
                    # TODO: Implementar adicionar_categoria com empresa_id no wrapper
                    self.adicionar_categoria(categoria)
                else:
                    self.adicionar_categoria(categoria)
            except Exception as e:
                print(f"Erro ao migrar categoria {categoria.nome}: {e}")
        
        # Migrar lani?amentos
        for lanc_data in dados.get('lancamentos', []):
            lancamento = Lancamento(**lanc_data)
            try:
                if empresa_id:
                    # Usar método interno com empresa_id
                    self.adicionar_lancamento(lancamento, proprietario_id=empresa_id, empresa_id=empresa_id)
                else:
                    print(f"⚠️  AVISO: Lançamento sem empresa_id - não recomendado!")
                    self.adicionar_lancamento(lancamento)
            except Exception as e:
                print(f"Erro ao migrar lani?amento: {e}")
        
        print("Migrai?i?o conclui?da!")
    
    # === Mi?TODOS DO MENU OPERACIONAL ===
    
    def gerar_proximo_numero_contrato(self) -> str:
        """Gera o pri?ximo ni?mero de contrato"""
        return gerar_proximo_numero_contrato()
    
    def adicionar_contrato(self, dados: Dict) -> int:
        """Adiciona um novo contrato"""
        return adicionar_contrato(dados)
    
    def listar_contratos(self) -> List[Dict]:
        """Lista todos os contratos"""
        return listar_contratos()
    
    def atualizar_contrato(self, contrato_id: int, dados: Dict) -> bool:
        """Atualiza um contrato"""
        return atualizar_contrato(contrato_id, dados)
    
    def deletar_contrato(self, contrato_id: int) -> bool:
        """Deleta um contrato"""
        return deletar_contrato(contrato_id)
    
    def adicionar_sessao(self, dados: Dict) -> int:
        """Adiciona uma nova sessi?o"""
        return adicionar_sessao(dados)
    
    def listar_sessoes(self, empresa_id: int = None) -> List[Dict]:
        """Lista todas as sessões da empresa"""
        if not empresa_id:
            from flask import session
            empresa_id = session.get('empresa_id')
        if not empresa_id:
            raise ValueError("empresa_id é obrigatório")
        return listar_sessoes(empresa_id=empresa_id)
    
    def atualizar_sessao(self, sessao_id: int, dados: Dict) -> bool:
        """Atualiza uma sessi?o"""
        return atualizar_sessao(sessao_id, dados)
    
    def deletar_sessao(self, sessao_id: int) -> bool:
        """Deleta uma sessi?o"""
        return deletar_sessao(sessao_id)
    
    def adicionar_comissao(self, dados: Dict) -> int:
        """Adiciona uma nova comissi?o"""
        return adicionar_comissao(dados)
    
    def listar_comissoes(self) -> List[Dict]:
        """Lista todas as comissi?es"""
        return listar_comissoes()
    
    def atualizar_comissao(self, comissao_id: int, dados: Dict) -> bool:
        """Atualiza uma comissi?o"""
        return atualizar_comissao(comissao_id, dados)
    
    def deletar_comissao(self, comissao_id: int) -> bool:
        """Deleta uma comissi?o"""
        return deletar_comissao(comissao_id)
    
    def adicionar_sessao_equipe(self, dados: Dict) -> int:
        """Adiciona um membro i? equipe de sessi?o"""
        return adicionar_sessao_equipe(dados)
    
    def listar_sessao_equipe(self, sessao_id: int = None) -> List[Dict]:
        """Lista membros da equipe de sessi?o"""
        return listar_sessao_equipe(sessao_id)
    
    def atualizar_sessao_equipe(self, membro_id: int, dados: Dict) -> bool:
        """Atualiza um membro da equipe"""
        return atualizar_sessao_equipe(membro_id, dados)
    
    def deletar_sessao_equipe(self, membro_id: int) -> bool:
        """Deleta um membro da equipe"""
        return deletar_sessao_equipe(membro_id)
    
    def adicionar_tipo_sessao(self, dados: Dict) -> int:
        """Adiciona um novo tipo de sessi?o"""
        return adicionar_tipo_sessao(dados)
    
    def listar_tipos_sessao(self) -> List[Dict]:
        """Lista todos os tipos de sessi?o"""
        return listar_tipos_sessao()
    
    def atualizar_tipo_sessao(self, tipo_id: int, dados: Dict) -> bool:
        """Atualiza um tipo de sessi?o"""
        return atualizar_tipo_sessao(tipo_id, dados)
    
    def deletar_tipo_sessao(self, tipo_id: int) -> bool:
        """Deleta um tipo de sessi?o"""
        return deletar_tipo_sessao(tipo_id)
    
    def adicionar_agenda(self, dados: Dict) -> int:
        """Adiciona um novo agendamento"""
        return adicionar_agenda(dados)
    
    def listar_agenda(self) -> List[Dict]:
        """Lista todos os agendamentos"""
        return listar_agenda()
    
    def atualizar_agenda(self, agenda_id: int, dados: Dict) -> bool:
        """Atualiza um agendamento"""
        return atualizar_agenda(agenda_id, dados)
    
    def deletar_agenda(self, agenda_id: int) -> bool:
        """Deleta um agendamento"""
        return deletar_agenda(agenda_id)
    
    # ========================================================================
    # MÉTODOS PARA REGRAS DE AUTO-CONCILIAÇÃO
    # ========================================================================
    
    def listar_regras_conciliacao(self, empresa_id: int) -> List[Dict]:
        """
        Lista todas as regras de auto-conciliação de uma empresa
        
        Args:
            empresa_id: ID da empresa
            
        Returns:
            Lista de regras
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    id, 
                    empresa_id,
                    palavra_chave,
                    categoria,
                    subcategoria,
                    cliente_padrao,
                    usa_integracao_folha,
                    descricao,
                    ativo,
                    created_at,
                    updated_at
                FROM regras_conciliacao
                WHERE empresa_id = %s
                ORDER BY ativo DESC, palavra_chave ASC
            """, (empresa_id,))
            
            regras = cursor.fetchall()
            return [dict(r) for r in regras]
            
        except Exception as e:
            print(f"❌ Erro ao listar regras de conciliação: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                return_to_pool(conn)

    def criar_regra_conciliacao(self, empresa_id: int, palavra_chave: str, 
                               categoria: str = None, subcategoria: str = None,
                               cliente_padrao: str = None, usa_integracao_folha: bool = False,
                               descricao: str = None) -> Optional[Dict]:
        """
        Cria nova regra de auto-conciliação
        
        Args:
            empresa_id: ID da empresa
            palavra_chave: Texto a ser detectado na descrição
            categoria: Categoria a ser preenchida automaticamente
            subcategoria: Subcategoria a ser preenchida automaticamente
            cliente_padrao: Cliente/Fornecedor padrão
            usa_integracao_folha: Se TRUE, busca CPF e vincula com funcionário
            descricao: Descrição opcional da regra
            
        Returns:
            Dicionário com a regra criada ou None se erro
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                INSERT INTO regras_conciliacao (
                    empresa_id, palavra_chave, categoria, subcategoria,
                    cliente_padrao, usa_integracao_folha, descricao, ativo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                RETURNING *
            """, (empresa_id, palavra_chave.upper(), categoria, subcategoria,
                  cliente_padrao, usa_integracao_folha, descricao))
            
            conn.commit()
            regra = cursor.fetchone()
            return dict(regra) if regra else None
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ Erro ao criar regra de conciliação: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                return_to_pool(conn)

    def atualizar_regra_conciliacao(self, regra_id: int, empresa_id: int, **campos) -> bool:
        """
        Atualiza uma regra de auto-conciliação
        
        Args:
            regra_id: ID da regra
            empresa_id: ID da empresa (segurança)
            **campos: Campos a atualizar
            
        Returns:
            True se sucesso, False caso contrário
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Construir SQL dinâmico apenas com campos válidos
            campos_validos = ['palavra_chave', 'categoria', 'subcategoria', 
                             'cliente_padrao', 'usa_integracao_folha', 'descricao', 'ativo']
            
            sets = []
            valores = []
            for campo, valor in campos.items():
                if campo in campos_validos:
                    sets.append(f"{campo} = %s")
                    # Normalizar palavra_chave para uppercase
                    if campo == 'palavra_chave' and isinstance(valor, str):
                        valor = valor.upper()
                    valores.append(valor)
            
            if not sets:
                return False
            
            valores.extend([regra_id, empresa_id])
            
            cursor.execute(f"""
                UPDATE regras_conciliacao 
                SET {', '.join(sets)}
                WHERE id = %s AND empresa_id = %s
            """, valores)
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ Erro ao atualizar regra de conciliação: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                return_to_pool(conn)

    def excluir_regra_conciliacao(self, regra_id: int, empresa_id: int) -> bool:
        """
        Exclui uma regra de auto-conciliação
        
        Args:
            regra_id: ID da regra
            empresa_id: ID da empresa (segurança)
            
        Returns:
            True se sucesso, False caso contrário
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM regras_conciliacao 
                WHERE id = %s AND empresa_id = %s
            """, (regra_id, empresa_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ Erro ao excluir regra de conciliação: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                return_to_pool(conn)


# Funi?i?es standalone para compatibilidade
def criar_tabelas():
    db = DatabaseManager()
    db.criar_tabelas()

def get_connection():
    db = DatabaseManager()
    return db.get_connection()

def adicionar_conta(empresa_id: int, conta: ContaBancaria) -> int:
    """
    Adiciona uma conta bancária
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        conta (ContaBancaria): Dados da conta
    
    Raises:
        ValueError: Se empresa_id não fornecido
        
    Security:
        🔒 RLS aplicado - conta vinculada à empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para adicionar_conta")
    db = DatabaseManager()
    result = db.adicionar_conta(conta)
    # 🔥 Invalidar cache da empresa
    invalidate_cache(empresa_id)
    return result

@cached(ttl=600)  # Cache por 10 minutos
def listar_contas(empresa_id: int) -> List[ContaBancaria]:
    """
    Lista contas bancárias da empresa
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
    
    Returns:
        List[ContaBancaria]: Lista de contas da empresa
        
    Raises:
        ValueError: Se empresa_id não fornecido
        
    Security:
        🔒 RLS aplicado - retorna apenas contas da empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para listar_contas")
    db = DatabaseManager()
    return db.listar_contas_por_empresa(empresa_id=empresa_id)

def atualizar_conta(nome_antigo: str, conta: ContaBancaria) -> bool:
    db = DatabaseManager()
    return db.atualizar_conta(nome_antigo, conta)

def excluir_conta(nome: str) -> bool:
    db = DatabaseManager()
    return db.excluir_conta(nome)

def adicionar_categoria(empresa_id: int, categoria: Categoria) -> int:
    """
    Adiciona uma categoria
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        categoria (Categoria): Dados da categoria
    
    Raises:
        ValueError: Se empresa_id não fornecido
        
    Security:
        🔒 RLS aplicado - categoria vinculada à empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para adicionar_categoria")
    db = DatabaseManager()
    result = db.adicionar_categoria(categoria)
    # 🔥 Invalidar cache da empresa
    invalidate_cache(empresa_id)
    return result

@cached(ttl=600)  # Cache por 10 minutos
def listar_categorias(empresa_id: int, tipo: Optional[TipoLancamento] = None) -> List[Categoria]:
    """
    Lista categorias da empresa
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        tipo (Optional[TipoLancamento]): Filtro por tipo (receita/despesa)
    
    Returns:
        List[Categoria]: Lista de categorias da empresa
        
    Raises:
        ValueError: Se empresa_id não fornecido
        
    Security:
        🔒 RLS aplicado - retorna apenas categorias da empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para listar_categorias")
    db = DatabaseManager()
    return db.listar_categorias(tipo=tipo, empresa_id=empresa_id)

def excluir_categoria(nome: str) -> bool:
    db = DatabaseManager()
    return db.excluir_categoria(nome)

def atualizar_categoria(categoria: Categoria) -> bool:
    db = DatabaseManager()
    return db.atualizar_categoria(categoria)

def atualizar_nome_categoria(nome_antigo: str, nome_novo: str) -> bool:
    db = DatabaseManager()
    return db.atualizar_nome_categoria(nome_antigo, nome_novo)

def adicionar_cliente(empresa_id: int, cliente_data, cpf_cnpj: str = None, email: str = None,
                     telefone: str = None, endereco: str = None,
                     cep: str = None, logradouro: str = None, numero: str = None,
                     complemento: str = None, bairro: str = None, 
                     cidade: str = None, estado: str = None) -> int:
    """
    Adiciona um cliente
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        cliente_data: Dados do cliente
        cpf_cnpj (str): CPF/CNPJ
        email (str): Email
        telefone (str): Telefone
        endereco (str): Endereço (campo legado)
        cep (str): CEP no formato 00000-000
        logradouro (str): Rua, Avenida, etc
        numero (str): Número do imóvel
        complemento (str): Apto, Sala, Bloco, etc
        bairro (str): Bairro
        cidade (str): Cidade
        estado (str): UF (SP, RJ, etc)
    
    Raises:
        ValueError: Se empresa_id não fornecido
        
    Security:
        🔒 RLS aplicado - cliente vinculado à empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para adicionar_cliente")
    db = DatabaseManager()
    result = db.adicionar_cliente(
        cliente_data, cpf_cnpj, email, telefone, endereco,
        cep, logradouro, numero, complemento, bairro, cidade, estado
    )
    # 🔥 Invalidar cache da empresa
    invalidate_cache(empresa_id)
    return result

@cached(ttl=300)  # Cache por 5 minutos
def listar_clientes(empresa_id: int, ativos: bool = True) -> List[Dict]:
    """
    Lista clientes da empresa
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        ativos (bool): Se True, retorna apenas clientes ativos
    
    Returns:
        List[Dict]: Lista de clientes da empresa
        
    Raises:
        ValueError: Se empresa_id não fornecido
        
    Security:
        🔒 RLS aplicado - retorna apenas clientes da empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para listar_clientes")
    db = DatabaseManager()
    return db.listar_clientes(ativos)

def atualizar_cliente(nome_antigo: str, dados: Dict) -> bool:
    db = DatabaseManager()
    return db.atualizar_cliente(nome_antigo, dados)

def inativar_cliente(nome: str, motivo: str = "") -> tuple[bool, str]:
    db = DatabaseManager()
    return db.inativar_cliente(nome, motivo)

def reativar_cliente(nome: str) -> bool:
    db = DatabaseManager()
    return db.reativar_cliente(nome)

def adicionar_fornecedor(fornecedor_data, cpf_cnpj: str = None, email: str = None,
                        telefone: str = None, endereco: str = None) -> int:
    db = DatabaseManager()
    return db.adicionar_fornecedor(fornecedor_data, cpf_cnpj, email, telefone, endereco)

def listar_fornecedores(ativos: bool = True) -> List[Dict]:
    db = DatabaseManager()
    return db.listar_fornecedores(ativos)

def atualizar_fornecedor(nome_antigo: str, dados: Dict) -> bool:
    db = DatabaseManager()
    return db.atualizar_fornecedor(nome_antigo, dados)

def inativar_fornecedor(nome: str, motivo: str = "") -> tuple[bool, str]:
    db = DatabaseManager()
    return db.inativar_fornecedor(nome, motivo)

def reativar_fornecedor(nome: str) -> bool:
    db = DatabaseManager()
    return db.reativar_fornecedor(nome)

def adicionar_lancamento(empresa_id: int, lancamento: Lancamento) -> int:
    """
    Adiciona um lançamento financeiro
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        lancamento (Lancamento): Dados do lançamento
    
    Returns:
        int: ID do lançamento criado
        
    Raises:
        ValueError: Se empresa_id não fornecido
        
    Security:
        🔒 RLS aplicado - lançamento vinculado à empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para adicionar_lancamento")
    db = DatabaseManager()
    return db.adicionar_lancamento(lancamento, proprietario_id=empresa_id, empresa_id=empresa_id)

def listar_lancamentos(empresa_id: int, filtros: Dict[str, Any] = None, filtro_cliente_id: int = None, 
                      page: int = None, per_page: int = 50) -> List[Lancamento]:
    """
    Lista lançamentos com suporte a filtros, multi-tenancy e paginação
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        filtros (Dict): Dicionário com filtros (tipo, status, datas)
        filtro_cliente_id (int): ID do cliente para filtro adicional
        page (int): Número da página (1-indexed). Se None, retorna todos
        per_page (int): Itens por página (padrão: 50)
    
    Returns:
        List[Lancamento]: Lista de lançamentos da empresa
        
    Raises:
        ValueError: Se empresa_id não fornecido
        
    Security:
        🔒 RLS aplicado - retorna apenas lançamentos da empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para listar_lancamentos")
    db = DatabaseManager()
    # Usar empresa_id como filtro_cliente_id se não fornecido
    cliente_id = filtro_cliente_id if filtro_cliente_id else empresa_id
    return db.listar_lancamentos(empresa_id=empresa_id, filtros=filtros, filtro_cliente_id=cliente_id, page=page, per_page=per_page)

def obter_lancamento(empresa_id: int, lancamento_id: int) -> Optional[Lancamento]:
    """
    Obtém um lançamento específico por ID
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        lancamento_id (int): ID do lançamento
    
    Returns:
        Optional[Lancamento]: Lançamento encontrado ou None
        
    Raises:
        ValueError: Se empresa_id não fornecido
        
    Security:
        🔒 RLS aplicado - retorna apenas se lançamento pertence à empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para obter_lancamento")
    db = DatabaseManager()
    return db.obter_lancamento(lancamento_id)

def excluir_lancamento(empresa_id: int, lancamento_id: int) -> bool:
    """
    Exclui um lançamento
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        lancamento_id (int): ID do lançamento a excluir
    
    Returns:
        bool: True se excluído com sucesso
        
    Raises:
        ValueError: Se empresa_id não fornecido
        
    Security:
        🔒 RLS aplicado - exclui apenas se lançamento pertence à empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para excluir_lancamento")
    db = DatabaseManager()
    return db.excluir_lancamento(lancamento_id)

def pagar_lancamento(lancamento_id: int, conta: str = '', data_pagamento: date = None,
                    juros: float = 0, desconto: float = 0, observacoes: str = '',
                    valor_pago: Optional[Decimal] = None) -> bool:
    print(f"\n?? pagar_lancamento() wrapper chamada:")
    print(f"   Args: ({lancamento_id}, {conta}, {data_pagamento}, {juros}, {desconto}, {observacoes}, {valor_pago})")
    db = DatabaseManager()
    print(f"   DatabaseManager criado: {type(db)}")
    resultado = db.pagar_lancamento(lancamento_id, conta, data_pagamento, juros, desconto, observacoes, valor_pago)
    print(f"   Resultado: {resultado}\n")
    return resultado

def cancelar_lancamento(lancamento_id: int) -> bool:
    db = DatabaseManager()
    return db.cancelar_lancamento(lancamento_id)

def migrar_dados_json(json_path: str):
    db = DatabaseManager()
    return db.migrar_dados_json(json_path)


# ==================== FUNi?i?ES CRUD - CONTRATOS ====================
def gerar_proximo_numero_contrato() -> str:
    """Gera o pri?ximo ni?mero de contrato no formato CONT-YYYY-NNNN"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        ano_atual = datetime.now().year
        
        # Buscar o i?ltimo ni?mero de contrato do ano atual
        cursor.execute("""
            SELECT numero FROM contratos 
            WHERE numero LIKE %s
            ORDER BY numero DESC 
            LIMIT 1
        """, (f'CONT-{ano_atual}-%',))
        
        resultado = cursor.fetchone()
        
        if resultado:
            # Extrair o ni?mero sequencial do i?ltimo contrato
            ultimo_numero = resultado['numero']
            try:
                sequencial = int(ultimo_numero.split('-')[-1])
                proximo_numero = sequencial + 1
            except (ValueError, IndexError):
                proximo_numero = 1
        else:
            proximo_numero = 1
        
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        
        # Formatar: CONT-2025-0001
        return f'CONT-{ano_atual}-{proximo_numero:04d}'
    except Exception as e:
        print(f"? Erro ao gerar ni?mero do contrato: {e}")
        # Em caso de erro, retornar um ni?mero padri?o
        ano_atual = datetime.now().year
        return f'CONT-{ano_atual}-0001'

def adicionar_contrato(empresa_id: int, dados: Dict) -> int:
    """
    Adiciona um novo contrato
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        dados (Dict): Dados do contrato
    
    Returns:
        int: ID do contrato criado
        
    Raises:
        ValueError: Se empresa_id não fornecido
        
    Security:
        🔒 RLS aplicado - contrato vinculado à empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para adicionar_contrato")
    
    # 🔒 Usar get_db_connection com empresa_id
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
    
    # Mapear dados do frontend para os campos do banco
    # Frontend: nome, tipo, valor_mensal, quantidade_meses, valor_total, data_contrato, etc
    # Banco: numero, cliente_id, descricao, valor, data_inicio, data_fim, status, observacoes
    
    # Preparar observações com todos os dados adicionais
    observacoes_dict = {
        'tipo': dados.get('tipo'),
        'nome': dados.get('nome'),
        'valor_mensal': dados.get('valor_mensal'),
        'quantidade_meses': dados.get('quantidade_meses'),
        'horas_mensais': dados.get('horas_mensais'),
        'forma_pagamento': dados.get('forma_pagamento'),
        'quantidade_parcelas': dados.get('quantidade_parcelas'),
        'dia_pagamento': dados.get('dia_pagamento'),
        'dia_emissao_nf': dados.get('dia_emissao_nf'),
        'imposto': dados.get('imposto'),
        'comissoes': dados.get('comissoes', [])
    }
    
    import json
    observacoes_json = json.dumps(observacoes_dict)
    
    # � Calcular horas totais baseado no tipo
    tipo = dados.get('tipo', 'Mensal')
    horas_mensais = float(dados.get('horas_mensais') or 0)
    qtd_meses = int(dados.get('quantidade_meses') or 1)
    
    horas_totais = 0
    controle_horas_ativo = False
    
    if tipo == 'Pacote':
        # Pacote: qtd_pacotes × horas_pacote
        qtd_pacotes = qtd_meses  # Reutiliza campo quantidade_meses
        horas_pacote = horas_mensais  # Reutiliza campo horas_mensais
        horas_totais = qtd_pacotes * horas_pacote
        controle_horas_ativo = True if horas_totais > 0 else False
    elif horas_mensais > 0:
        # Mensal/Único com horas definidas: horas_mensais × qtd_meses
        horas_totais = horas_mensais * qtd_meses
        controle_horas_ativo = True
    
    # 🔒 INCLUIR empresa_id, horas_totais e controle_horas_ativo no INSERT
    cursor.execute("""
        INSERT INTO contratos (
            numero, cliente_id, descricao, valor, data_inicio, data_fim, 
            status, observacoes, empresa_id, 
            horas_totais, horas_utilizadas, horas_extras, controle_horas_ativo
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        dados.get('numero'),
        dados.get('cliente_id'),
        dados.get('descricao', dados.get('nome')),  # usar 'nome' se 'descricao' não existir
        dados.get('valor_total', dados.get('valor')),  # usar 'valor_total' ou 'valor'
        dados.get('data_contrato', dados.get('data_inicio')),  # usar 'data_contrato' ou 'data_inicio'
        dados.get('data_fim'),
        dados.get('status', 'ativo'),
        observacoes_json,
        empresa_id,  # 🔒 Adicionar empresa_id
        horas_totais,  # 📊 Total de horas
        0,  # horas_utilizadas inicial
        0,  # horas_extras inicial
        controle_horas_ativo  # 📊 Controle ativo
    ))
    
    contrato_id = cursor.fetchone()['id']
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return contrato_id

def listar_contratos(empresa_id: int) -> List[Dict]:
    """
    Lista todos os contratos da empresa
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
    
    Returns:
        List[Dict]: Lista de contratos
        
    Raises:
        ValueError: Se empresa_id não fornecido
        
    Security:
        🔒 RLS aplicado - retorna apenas contratos da empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para listar_contratos")
    
    # 🔒 Usar get_db_connection com empresa_id
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.*, cl.nome as cliente_nome
            FROM contratos c
            LEFT JOIN clientes cl ON c.cliente_id = cl.id
            ORDER BY c.created_at DESC
        """)
    
    contratos = []
    for row in cursor.fetchall():
        contrato = dict(row)
        
        # Preservar campos importantes da tabela ANTES de mesclar com JSON
        campos_preservar = {
            'descricao': contrato.get('descricao'),
            'numero': contrato.get('numero'),
            'valor': contrato.get('valor'),
            'data_inicio': contrato.get('data_inicio'),
            'imposto': contrato.get('imposto')
        }
        
        # Extrair dados do JSON de observações
        if contrato.get('observacoes'):
            try:
                import json
                obs_data = json.loads(contrato['observacoes'])
                contrato.update(obs_data)  # Adicionar campos extras ao contrato
            except:
                pass
        
        # Restaurar campos da tabela se JSON não tem valor ou tem valor vazio
        for campo, valor_tabela in campos_preservar.items():
            valor_json = contrato.get(campo)
            # Se JSON não tem valor OU tem string vazia, mas tabela tem valor preenchido
            if valor_tabela and (valor_json is None or (isinstance(valor_json, str) and valor_json.strip() == '')):
                contrato[campo] = valor_tabela
        
        # 📊 Calcular horas restantes (campo virtual)
        if contrato.get('controle_horas_ativo'):
            horas_totais = float(contrato.get('horas_totais', 0))
            horas_utilizadas = float(contrato.get('horas_utilizadas', 0))
            horas_restantes = horas_totais - horas_utilizadas
            contrato['horas_restantes'] = horas_restantes
            
            # Calcular percentual utilizado
            if horas_totais > 0:
                contrato['percentual_utilizado'] = round((horas_utilizadas / horas_totais) * 100, 2)
            else:
                contrato['percentual_utilizado'] = 0
        else:
            contrato['horas_restantes'] = None
            contrato['percentual_utilizado'] = None
        
        contratos.append(contrato)
    
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return contratos

def atualizar_contrato(contrato_id: int, dados: Dict) -> bool:
    """Atualiza um contrato existente"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Preparar observações com todos os dados adicionais
    observacoes_dict = {
        'tipo': dados.get('tipo'),
        'nome': dados.get('nome'),
        'valor_mensal': dados.get('valor_mensal'),
        'quantidade_meses': dados.get('quantidade_meses'),
        'horas_mensais': dados.get('horas_mensais'),
        'forma_pagamento': dados.get('forma_pagamento'),
        'quantidade_parcelas': dados.get('quantidade_parcelas'),
        'dia_pagamento': dados.get('dia_pagamento'),
        'dia_emissao_nf': dados.get('dia_emissao_nf'),
        'imposto': dados.get('imposto'),
        'comissoes': dados.get('comissoes', [])
    }
    
    import json
    observacoes_json = json.dumps(observacoes_dict)
    
    cursor.execute("""
        UPDATE contratos
        SET numero = %s, cliente_id = %s, descricao = %s, valor = %s,
            data_inicio = %s, data_fim = %s, status = %s, observacoes = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('numero'),
        dados.get('cliente_id'),
        dados.get('descricao', dados.get('nome')),
        dados.get('valor_total', dados.get('valor')),
        dados.get('data_contrato', dados.get('data_inicio')),
        dados.get('data_fim'),
        dados.get('status'),
        observacoes_json,
        contrato_id
    ))
    
    conn.commit()  # Confirmar transação
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso

def deletar_contrato(contrato_id: int) -> bool:
    """Deleta um contrato"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM contratos WHERE id = %s", (contrato_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso


# ==================== FUNÇÕES CRUD - SESSÕES ====================
def adicionar_sessao(dados: Dict) -> int:
    """Adiciona uma nova sessão com multi-tenancy"""
    import json
    
    # 🔒 Validar empresa_id obrigatório
    empresa_id = dados.get('empresa_id')
    if not empresa_id:
        from flask import session
        empresa_id = session.get('empresa_id')
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para adicionar sessão")
    
    print(f"\n🔍 [adicionar_sessao]")
    print(f"   - empresa_id: {empresa_id}")
    print(f"   - cliente_id: {dados.get('cliente_id')}")
    print(f"   - data: {dados.get('data')}")
    
    # 🔒 Usar get_db_connection com empresa_id para aplicar RLS
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # Preparar dados JSON para campos complexos
        dados_json = {
            'horario': dados.get('horario'),
            'quantidade_horas': dados.get('quantidade_horas'),
            'tipo_foto': dados.get('tipo_foto', False),
            'tipo_video': dados.get('tipo_video', False),
            'tipo_mobile': dados.get('tipo_mobile', False),
            'tags': dados.get('tags'),
            'equipe': dados.get('equipe', []),
            'responsaveis': dados.get('responsaveis', []),
            'equipamentos': dados.get('equipamentos', []),
            'equipamentos_alugados': dados.get('equipamentos_alugados', []),
            'custos_adicionais': dados.get('custos_adicionais', [])
        }
        
        cursor.execute("""
            INSERT INTO sessoes 
            (cliente_id, contrato_id, data, endereco, descricao, prazo_entrega, 
             observacoes, dados_json, empresa_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
        """, (
            dados.get('cliente_id'),
            dados.get('contrato_id'),
            dados.get('data'),
            dados.get('endereco'),
            dados.get('descricao'),
            dados.get('prazo_entrega'),
            dados.get('observacoes'),
            json.dumps(dados_json),
            empresa_id
        ))
        
        sessao_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        
        print(f"   ✅ Sessão criada com ID: {sessao_id}")
        return sessao_id


def listar_sessoes(empresa_id: int) -> List[Dict]:
    """
    Lista todas as sessões da empresa
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
    
    Returns:
        List[Dict]: Lista de sessões
        
    Raises:
        ValueError: Se empresa_id não fornecido
        
    Security:
        🔒 RLS aplicado - retorna apenas sessões da empresa
    """
    import json
    
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para listar_sessoes")
    
    # 🔒 Usar get_db_connection com empresa_id (retorna context manager)
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT 
                s.id, s.cliente_id, s.contrato_id, s.data, s.endereco,
                s.descricao, s.prazo_entrega, s.observacoes, s.dados_json,
                s.created_at, s.updated_at,
                c.nome AS cliente_nome,
                ct.numero AS contrato_numero, ct.descricao AS contrato_nome
            FROM sessoes s
            LEFT JOIN clientes c ON s.cliente_id = c.id
            LEFT JOIN contratos ct ON s.contrato_id = ct.id
            ORDER BY s.data DESC, s.id DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        sessoes = []
        for row in rows:
            # Trata dados_json que pode vir como dict ou string
            if row['dados_json']:
                if isinstance(row['dados_json'], dict):
                    dados_json = row['dados_json']  # Já é dict
                else:
                    dados_json = json.loads(row['dados_json'])  # Parse string
            else:
                dados_json = {}
            
            sessao = {
                'id': row['id'],
                'cliente_id': row['cliente_id'],
                'cliente_nome': row['cliente_nome'] or '-',
                'contrato_id': row['contrato_id'],
                'contrato_numero': row['contrato_numero'],
                'contrato_nome': row['contrato_nome'],
                'data': row['data'].isoformat() if row['data'] else None,
                'horario': dados_json.get('horario'),
                'quantidade_horas': dados_json.get('quantidade_horas'),
                'endereco': row['endereco'],
                'tipo_foto': dados_json.get('tipo_foto', False),
                'tipo_video': dados_json.get('tipo_video', False),
                'tipo_mobile': dados_json.get('tipo_mobile', False),
                'descricao': row['descricao'],
                'tags': dados_json.get('tags'),
                'prazo_entrega': row['prazo_entrega'].isoformat() if row['prazo_entrega'] else None,
                'equipe': dados_json.get('equipe', []),
                'responsaveis': dados_json.get('responsaveis', []),
                'equipamentos': dados_json.get('equipamentos', []),
                'equipamentos_alugados': dados_json.get('equipamentos_alugados', []),
                'custos_adicionais': dados_json.get('custos_adicionais', []),
                'observacoes': row['observacoes']
            }
            
            sessoes.append(sessao)
    
    return sessoes


def buscar_sessao(sessao_id: int) -> Dict:
    """Busca uma sessão específica"""
    import json
    
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            s.id, s.cliente_id, s.contrato_id, s.data, s.endereco,
            s.descricao, s.prazo_entrega, s.observacoes, s.dados_json,
            c.nome AS cliente_nome,
            ct.numero AS contrato_numero, ct.descricao AS contrato_nome
        FROM sessoes s
        LEFT JOIN clientes c ON s.cliente_id = c.id
        LEFT JOIN contratos ct ON s.contrato_id = ct.id
        WHERE s.id = %s
    """, (sessao_id,))
    
    row = cursor.fetchone()
    cursor.close()
    return_to_pool(conn)
    
    if not row:
        return None
    
    # Trata dados_json que pode vir como dict ou string
    if row['dados_json']:
        if isinstance(row['dados_json'], dict):
            dados_json = row['dados_json']  # Já é dict
        else:
            dados_json = json.loads(row['dados_json'])  # Parse string
    else:
        dados_json = {}
    
    return {
        'id': row['id'],
        'cliente_id': row['cliente_id'],
        'cliente_nome': row['cliente_nome'] or row['cliente_razao_social'],
        'contrato_id': row['contrato_id'],
        'contrato_numero': row['contrato_numero'],
        'contrato_nome': row['contrato_nome'],
        'data': row['data'].isoformat() if row['data'] else None,
        'horario': dados_json.get('horario'),
        'quantidade_horas': dados_json.get('quantidade_horas'),
        'endereco': row['endereco'],
        'tipo_foto': dados_json.get('tipo_foto', False),
        'tipo_video': dados_json.get('tipo_video', False),
        'tipo_mobile': dados_json.get('tipo_mobile', False),
        'descricao': row['descricao'],
        'tags': dados_json.get('tags'),
        'prazo_entrega': row['prazo_entrega'].isoformat() if row['prazo_entrega'] else None,
        'equipe': dados_json.get('equipe', []),
        'responsaveis': dados_json.get('responsaveis', []),
        'equipamentos': dados_json.get('equipamentos', []),
        'equipamentos_alugados': dados_json.get('equipamentos_alugados', []),
        'custos_adicionais': dados_json.get('custos_adicionais', []),
        'observacoes': row['observacoes']
    }


def atualizar_sessao(sessao_id: int, dados: Dict) -> bool:
    """Atualiza uma sessão existente"""
    import json
    
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Preparar dados JSON
    dados_json = {
        'horario': dados.get('horario'),
        'quantidade_horas': dados.get('quantidade_horas'),
        'tipo_foto': dados.get('tipo_foto', False),
        'tipo_video': dados.get('tipo_video', False),
        'tipo_mobile': dados.get('tipo_mobile', False),
        'tags': dados.get('tags'),
        'equipe': dados.get('equipe', []),
        'responsaveis': dados.get('responsaveis', []),
        'equipamentos': dados.get('equipamentos', []),
        'equipamentos_alugados': dados.get('equipamentos_alugados', []),
        'custos_adicionais': dados.get('custos_adicionais', [])
    }
    
    cursor.execute("""
        UPDATE sessoes
        SET cliente_id = %s, contrato_id = %s, data = %s, endereco = %s,
            descricao = %s, prazo_entrega = %s, observacoes = %s, dados_json = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('cliente_id'),
        dados.get('contrato_id'),
        dados.get('data'),
        dados.get('endereco'),
        dados.get('descricao'),
        dados.get('prazo_entrega'),
        dados.get('observacoes'),
        json.dumps(dados_json),
        sessao_id
    ))
    
    conn.commit()  # Commit da transação
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)
    return sucesso


def finalizar_sessao(empresa_id: int, sessao_id: int, usuario_id: int, horas_trabalhadas: float = None) -> Dict:
    """
    Finaliza uma sessão e deduz horas do contrato vinculado
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO para RLS]
        sessao_id (int): ID da sessão a finalizar
        usuario_id (int): ID do usuário que finalizou
        horas_trabalhadas (float, optional): Horas trabalhadas. Se None, usa duracao da sessão
    
    Returns:
        Dict: Resultado da operação com detalhes
        {
            'success': bool,
            'message': str,
            'horas_deduzidas': float,
            'horas_extras': float,
            'saldo_restante': float
        }
    
    Raises:
        ValueError: Se empresa_id não fornecido ou sessão não encontrada
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para finalizar_sessao")
    
    # 🔒 Usar get_db_connection com empresa_id
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # 1. Buscar dados da sessão
        cursor.execute("""
            SELECT s.*, c.controle_horas_ativo, c.horas_totais, c.horas_utilizadas, c.horas_extras, c.id as contrato_id
            FROM sessoes s
            LEFT JOIN contratos c ON s.contrato_id = c.id
            WHERE s.id = %s
        """, (sessao_id,))
        
        sessao = cursor.fetchone()
        if not sessao:
            cursor.close()
            return_to_pool(conn)
            raise ValueError(f"Sessão {sessao_id} não encontrada")
        
        # Se já finalizada, retornar erro
        if sessao['status'] == 'finalizada':
            cursor.close()
            return_to_pool(conn)
            return {
                'success': False,
                'message': 'Sessão já está finalizada',
                'horas_deduzidas': 0,
                'horas_extras': 0,
                'saldo_restante': 0
            }
        
        # 2. Determinar horas trabalhadas
        if horas_trabalhadas is None:
            horas_trabalhadas = float(sessao.get('duracao') or 0)
        else:
            horas_trabalhadas = float(horas_trabalhadas)
        
        # 3. Atualizar status da sessão
        cursor.execute("""
            UPDATE sessoes
            SET status = 'finalizada',
                horas_trabalhadas = %s,
                finalizada_em = CURRENT_TIMESTAMP,
                finalizada_por = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (horas_trabalhadas, usuario_id, sessao_id))
        
        # 4. Se contrato TEM controle de horas, deduzir
        horas_deduzidas = 0
        horas_extras_adicional = 0
        saldo_restante = 0
        
        if sessao.get('contrato_id') and sessao.get('controle_horas_ativo'):
            contrato_id = sessao['contrato_id']
            horas_totais = float(sessao.get('horas_totais', 0))
            horas_utilizadas = float(sessao.get('horas_utilizadas', 0))
            horas_extras_atual = float(sessao.get('horas_extras', 0))
            
            # Calcular saldo atual
            saldo_atual = horas_totais - horas_utilizadas
            
            # Se saldo suficiente, deduzir normalmente
            if saldo_atual >= horas_trabalhadas:
                horas_deduzidas = horas_trabalhadas
                horas_extras_adicional = 0
            else:
                # Saldo insuficiente: usar o que resta + adicionar extras
                horas_deduzidas = max(saldo_atual, 0)
                horas_extras_adicional = horas_trabalhadas - horas_deduzidas
            
            # Atualizar contrato
            cursor.execute("""
                UPDATE contratos
                SET horas_utilizadas = horas_utilizadas + %s,
                    horas_extras = horas_extras + %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (horas_deduzidas, horas_extras_adicional, contrato_id))
            
            # Calcular saldo final
            saldo_restante = horas_totais - (horas_utilizadas + horas_deduzidas)
        
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        
        return {
            'success': True,
            'message': 'Sessão finalizada com sucesso',
            'horas_trabalhadas': horas_trabalhadas,
            'horas_deduzidas': horas_deduzidas,
            'horas_extras': horas_extras_adicional,
            'saldo_restante': max(saldo_restante, 0),
            'controle_horas_ativo': bool(sessao.get('controle_horas_ativo'))
        }


def atualizar_status_sessao(empresa_id: int, sessao_id: int, novo_status: str, usuario_id: int = None) -> Dict:
    """
    Atualiza o status de uma sessão com validações de transição
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO para RLS]
        sessao_id (int): ID da sessão
        novo_status (str): Novo status (rascunho, agendada, em_andamento, finalizada, cancelada, reaberta)
        usuario_id (int, optional): ID do usuário que fez a mudança
    
    Returns:
        Dict: Resultado da operação
        {
            'success': bool,
            'message': str,
            'status_anterior': str,
            'status_novo': str
        }
    
    Raises:
        ValueError: Se empresa_id não fornecido, sessão não encontrada ou transição inválida
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    # Status válidos
    STATUS_VALIDOS = ['rascunho', 'agendada', 'em_andamento', 'finalizada', 'cancelada', 'reaberta']
    
    if novo_status not in STATUS_VALIDOS:
        raise ValueError(f"Status inválido: {novo_status}. Valores aceitos: {', '.join(STATUS_VALIDOS)}")
    
    # 🔒 Usar get_db_connection com empresa_id
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # Buscar sessão atual
        cursor.execute("""
            SELECT id, status, titulo
            FROM sessoes
            WHERE id = %s
        """, (sessao_id,))
        
        sessao = cursor.fetchone()
        if not sessao:
            cursor.close()
            return_to_pool(conn)
            raise ValueError(f"Sessão {sessao_id} não encontrada")
        
        status_anterior = sessao.get('status', 'rascunho')
        
        # Validar transições (regras de negócio)
        transicoes_invalidas = [
            (status_anterior == 'finalizada' and novo_status not in ['reaberta', 'cancelada']),
            (status_anterior == 'cancelada' and novo_status != 'reaberta'),
        ]
        
        if any(transicoes_invalidas):
            cursor.close()
            return_to_pool(conn)
            return {
                'success': False,
                'message': f'Transição inválida: {status_anterior} → {novo_status}',
                'status_anterior': status_anterior,
                'status_novo': novo_status
            }
        
        # Atualizar status
        cursor.execute("""
            UPDATE sessoes
            SET status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (novo_status, sessao_id))
        
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        
        return {
            'success': True,
            'message': f'Status alterado: {status_anterior} → {novo_status}',
            'status_anterior': status_anterior,
            'status_novo': novo_status
        }


def cancelar_sessao(empresa_id: int, sessao_id: int, usuario_id: int, motivo: str = None) -> Dict:
    """
    Cancela uma sessão (não deleta, apenas muda status)
    
    Args:
        empresa_id (int): ID da empresa
        sessao_id (int): ID da sessão
        usuario_id (int): ID do usuário que cancelou
        motivo (str, optional): Motivo do cancelamento
    
    Returns:
        Dict: Resultado da operação com detalhes
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # Buscar sessão
        cursor.execute("""
            SELECT id, status, titulo
            FROM sessoes
            WHERE id = %s
        """, (sessao_id,))
        
        sessao = cursor.fetchone()
        if not sessao:
            cursor.close()
            return_to_pool(conn)
            raise ValueError(f"Sessão {sessao_id} não encontrada")
        
        status_anterior = sessao.get('status', 'rascunho')
        
        # Atualizar para cancelada
        observacoes_cancelamento = f"\n[CANCELADA em {datetime.now().strftime('%Y-%m-%d %H:%M')} por usuário {usuario_id}]"
        if motivo:
            observacoes_cancelamento += f"\nMotivo: {motivo}"
        
        cursor.execute("""
            UPDATE sessoes
            SET status = 'cancelada',
                observacoes = COALESCE(observacoes, '') || %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (observacoes_cancelamento, sessao_id))
        
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        
        return {
            'success': True,
            'message': 'Sessão cancelada com sucesso',
            'status_anterior': status_anterior,
            'status_novo': 'cancelada'
        }


def reabrir_sessao(empresa_id: int, sessao_id: int, usuario_id: int) -> Dict:
    """
    Reabre uma sessão finalizada ou cancelada
    
    Args:
        empresa_id (int): ID da empresa
        sessao_id (int): ID da sessão
        usuario_id (int): ID do usuário que reabriu
    
    Returns:
        Dict: Resultado da operação
    
    Note:
        ⚠️ Se sessão foi finalizada, as horas NÃO são devolvidas automaticamente ao contrato.
        Isso deve ser feito manualmente se necessário.
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # Buscar sessão
        cursor.execute("""
            SELECT id, status, titulo
            FROM sessoes
            WHERE id = %s
        """, (sessao_id,))
        
        sessao = cursor.fetchone()
        if not sessao:
            cursor.close()
            return_to_pool(conn)
            raise ValueError(f"Sessão {sessao_id} não encontrada")
        
        status_anterior = sessao.get('status', 'rascunho')
        
        # Só pode reabrir se estiver finalizada ou cancelada
        if status_anterior not in ['finalizada', 'cancelada']:
            cursor.close()
            return_to_pool(conn)
            return {
                'success': False,
                'message': f'Apenas sessões finalizadas ou canceladas podem ser reabertas. Status atual: {status_anterior}'
            }
        
        # Atualizar para reaberta
        observacoes_reabertura = f"\n[REABERTA em {datetime.now().strftime('%Y-%m-%d %H:%M')} por usuário {usuario_id}]"
        
        cursor.execute("""
            UPDATE sessoes
            SET status = 'reaberta',
                observacoes = COALESCE(observacoes, '') || %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (observacoes_reabertura, sessao_id))
        
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        
        aviso = ""
        if status_anterior == 'finalizada':
            aviso = "⚠️ As horas deduzidas do contrato NÃO foram devolvidas automaticamente."
        
        return {
            'success': True,
            'message': f'Sessão reaberta com sucesso. {aviso}',
            'status_anterior': status_anterior,
            'status_novo': 'reaberta'
        }


def deletar_sessao(sessao_id: int) -> bool:
    """Deleta uma sessão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM sessoes WHERE id = %s", (sessao_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)
    return sucesso


# ==================== FUNi?i?ES CRUD - AGENDA ====================
def adicionar_agenda(dados: Dict) -> int:
    """Adiciona um novo evento na agenda"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO agenda (titulo, data_evento, hora_inicio, hora_fim, local, tipo, status, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        dados.get('titulo'),
        dados.get('data_evento'),
        dados.get('hora_inicio'),
        dados.get('hora_fim'),
        dados.get('local'),
        dados.get('tipo'),
        dados.get('status', 'agendado'),
        dados.get('observacoes')
    ))
    
    agenda_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return agenda_id

def listar_agenda() -> List[Dict]:
    """Lista todos os eventos da agenda"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM agenda ORDER BY data_evento DESC, hora_inicio DESC")
    
    eventos = []
    for row in cursor.fetchall():
        evento = dict(row)
        # Converter objetos time para string (JSON serializable)
        if evento.get('hora_inicio'):
            evento['hora_inicio'] = str(evento['hora_inicio'])
        if evento.get('hora_fim'):
            evento['hora_fim'] = str(evento['hora_fim'])
        # Converter data para string
        if evento.get('data_evento'):
            evento['data_evento'] = str(evento['data_evento'])
        eventos.append(evento)
    
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return eventos

def atualizar_agenda(agenda_id: int, dados: Dict) -> bool:
    """Atualiza um evento da agenda"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE agenda
        SET titulo = %s, data_evento = %s, hora_inicio = %s, hora_fim = %s,
            local = %s, tipo = %s, status = %s, observacoes = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('titulo'),
        dados.get('data_evento'),
        dados.get('hora_inicio'),
        dados.get('hora_fim'),
        dados.get('local'),
        dados.get('tipo'),
        dados.get('status'),
        dados.get('observacoes'),
        agenda_id
    ))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso

def deletar_agenda(agenda_id: int) -> bool:
    """Deleta um evento da agenda"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM agenda WHERE id = %s", (agenda_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso


# ==================== FUNi?i?ES CRUD - PRODUTOS ====================
def adicionar_produto(dados: Dict) -> int:
    """Adiciona um novo produto"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO produtos (codigo, nome, categoria, quantidade, preco_custo, preco_venda, fornecedor_id, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        dados.get('codigo'),
        dados.get('nome'),
        dados.get('categoria'),
        dados.get('quantidade', 0),
        dados.get('preco_custo'),
        dados.get('preco_venda'),
        dados.get('fornecedor_id'),
        dados.get('observacoes')
    ))
    
    produto_id = cursor.fetchone()['id']
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return produto_id

def listar_produtos() -> List[Dict]:
    """Lista todos os produtos"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.id, p.codigo, p.nome, p.categoria, p.quantidade, 
               p.preco_custo, p.preco_venda, p.fornecedor_id, p.observacoes,
               p.created_at, p.updated_at, f.nome as fornecedor_nome
        FROM produtos p
        LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
        ORDER BY p.nome
    """)
    
    produtos = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return produtos

def atualizar_produto(produto_id: int, dados: Dict) -> bool:
    """Atualiza um produto"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE produtos
        SET codigo = %s, nome = %s, categoria = %s, quantidade = %s,
            preco_custo = %s, preco_venda = %s, fornecedor_id = %s, observacoes = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('codigo'),
        dados.get('nome'),
        dados.get('categoria'),
        dados.get('quantidade'),
        dados.get('preco_custo'),
        dados.get('preco_venda'),
        dados.get('fornecedor_id'),
        dados.get('observacoes'),
        produto_id
    ))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso

def deletar_produto(produto_id: int) -> bool:
    """Deleta um produto"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM produtos WHERE id = %s", (produto_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso


# ==================== FUNi?i?ES CRUD - KITS ====================
def adicionar_kit(dados: Dict) -> int:
    """Adiciona um novo kit"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO kits (codigo, nome, preco, observacoes)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        dados.get('codigo'),
        dados.get('nome'),
        dados.get('preco'),
        dados.get('observacoes')
    ))
    
    kit_id = cursor.fetchone()['id']
    
    # Adicionar itens do kit se fornecidos
    if 'itens' in dados and dados['itens']:
        for item in dados['itens']:
            cursor.execute("""
                INSERT INTO kit_itens (kit_id, produto_id, quantidade)
                VALUES (%s, %s, %s)
            """, (kit_id, item['produto_id'], item['quantidade']))
    
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return kit_id

def listar_kits() -> List[Dict]:
    """Lista todos os kits"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, codigo, nome, preco, observacoes, created_at, updated_at FROM kits ORDER BY nome")
    kits = [dict(row) for row in cursor.fetchall()]
    
    # Buscar itens de cada kit
    for kit in kits:
        cursor.execute("""
            SELECT ki.*, p.nome as produto_nome, p.codigo as produto_codigo
            FROM kit_itens ki
            JOIN produtos p ON ki.produto_id = p.id
            WHERE ki.kit_id = %s
        """, (kit['id'],))
        kit['itens'] = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return kits

def atualizar_kit(kit_id: int, dados: Dict) -> bool:
    """Atualiza um kit"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE kits
        SET codigo = %s, nome = %s, preco = %s, observacoes = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('codigo'),
        dados.get('nome'),
        dados.get('preco'),
        dados.get('observacoes'),
        kit_id
    ))
    
    # Atualizar itens se fornecidos
    if 'itens' in dados:
        cursor.execute("DELETE FROM kit_itens WHERE kit_id = %s", (kit_id,))
        for item in dados['itens']:
            cursor.execute("""
                INSERT INTO kit_itens (kit_id, produto_id, quantidade)
                VALUES (%s, %s, %s)
            """, (kit_id, item['produto_id'], item['quantidade']))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso

def deletar_kit(kit_id: int) -> bool:
    """Deleta um kit"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM kits WHERE id = %s", (kit_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso


# ==================== FUNi?i?ES CRUD - TAGS ====================
def adicionar_tag(dados: Dict) -> int:
    """Adiciona uma nova tag"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO tags (nome, cor, descricao)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (
        dados.get('nome'),
        dados.get('cor', '#007bff'),
        dados.get('descricao')
    ))
    
    tag_id = cursor.fetchone()['id']
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return tag_id

def listar_tags() -> List[Dict]:
    """Lista todas as tags"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nome, cor, descricao, created_at, updated_at FROM tags ORDER BY nome")
    
    tags = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return tags

def atualizar_tag(tag_id: int, dados: Dict) -> bool:
    """Atualiza uma tag"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE tags
        SET nome = %s, cor = %s, descricao = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('nome'),
        dados.get('cor'),
        dados.get('descricao'),
        tag_id
    ))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso

def deletar_tag(tag_id: int) -> bool:
    """Deleta uma tag"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tags WHERE id = %s", (tag_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso


# ==================== FUNi?i?ES CRUD - TEMPLATES DE EQUIPE ====================
def adicionar_template(dados: Dict) -> int:
    """Adiciona um novo template de equipe"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO templates_equipe (nome, tipo, conteudo)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (
        dados.get('nome'),
        dados.get('tipo'),
        dados.get('conteudo')
    ))
    
    template_id = cursor.fetchone()['id']
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return template_id

def listar_templates_equipe() -> List[Dict]:
    """Lista todos os templates de equipe"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nome, tipo, conteudo, created_at, updated_at FROM templates_equipe ORDER BY nome")
    
    templates = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return templates

def atualizar_template(template_id: int, dados: Dict) -> bool:
    """Atualiza um template de equipe"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE templates_equipe
        SET nome = %s, tipo = %s, conteudo = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('nome'),
        dados.get('tipo'),
        dados.get('conteudo'),
        template_id
    ))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso

def deletar_template(template_id: int) -> bool:
    """Deleta um template de equipe"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM templates_equipe WHERE id = %s", (template_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso


# ==================== FUNi?i?ES CRUD - SESSi?ES ====================
def adicionar_sessao(dados: Dict) -> int:
    """Adiciona uma nova sessi?o"""
    import json
    
    # 🔒 Obter empresa_id (obrigatório para RLS)
    empresa_id = dados.get('empresa_id')
    if not empresa_id:
        from flask import session
        empresa_id = session.get('empresa_id')
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para adicionar sessão")
    
    # 🔒 Usar get_db_connection com empresa_id para RLS
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # Preparar dados_json com campos adicionais
        dados_json = {
            'horario': dados.get('horario'),
            'quantidade_horas': dados.get('quantidade_horas'),
            'tipo_foto': dados.get('tipo_foto', False),
            'tipo_video': dados.get('tipo_video', False),
            'tipo_mobile': dados.get('tipo_mobile', False),
            'tags': dados.get('tags', ''),
            'equipe': dados.get('equipe', []),
            'responsaveis': dados.get('responsaveis', []),
            'equipamentos': dados.get('equipamentos', []),
            'equipamentos_alugados': dados.get('equipamentos_alugados', []),
            'custos_adicionais': dados.get('custos_adicionais', [])
        }
        
        # 🔒 INCLUIR empresa_id no INSERT
        cursor.execute("""
            INSERT INTO sessoes (
                titulo, data, data_sessao, duracao, contrato_id, cliente_id, 
                valor, observacoes, endereco, descricao, prazo_entrega, dados_json, empresa_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            dados.get('titulo'),
            dados.get('data_sessao'),  # Campo 'data' na tabela
            dados.get('data_sessao'),  # Campo 'data_sessao' para compatibilidade
            dados.get('duracao'),
            dados.get('contrato_id'),
            dados.get('cliente_id'),
            dados.get('valor'),
            dados.get('observacoes', ''),
            dados.get('endereco', ''),
            dados.get('descricao', ''),
            dados.get('prazo_entrega'),
            json.dumps(dados_json),
            empresa_id  # 🔒 Adicionar empresa_id
        ))
        
        sessao_id = cursor.fetchone()['id']
        
        # Adicionar membros da equipe se fornecidos
        if 'equipe' in dados and dados['equipe']:
            for membro in dados['equipe']:
                cursor.execute("""
                    INSERT INTO sessao_equipe (sessao_id, membro_nome, funcao)
                    VALUES (%s, %s, %s)
                """, (sessao_id, membro['nome'], membro.get('funcao')))
        
        conn.commit()
        cursor.close()
        
        return sessao_id

def listar_sessoes_OLD_DEPRECATED() -> List[Dict]:
    """⚠️ DEPRECATED - Use listar_sessoes(empresa_id) com RLS"""
    raise DeprecationWarning("Use listar_sessoes(empresa_id: int) instead")
    import datetime
    import decimal
    import json
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            s.id, s.titulo, s.data, s.data_sessao, s.duracao, s.contrato_id, s.cliente_id,
            s.valor, s.observacoes, s.endereco, s.descricao, s.prazo_entrega, s.dados_json,
            s.created_at, s.updated_at,
            c.nome as cliente_nome, 
            ct.numero as contrato_numero, ct.descricao as contrato_nome
        FROM sessoes s
        LEFT JOIN clientes c ON s.cliente_id = c.id
        LEFT JOIN contratos ct ON s.contrato_id = ct.id
        ORDER BY COALESCE(s.data, s.data_sessao, s.created_at) DESC
    """)
    sessoes = []
    for row in cursor.fetchall():
        sessao = {}
        for key, value in dict(row).items():
            # Converter tipos ni?o-serializi?veis para JSON
            if isinstance(value, (datetime.time, datetime.datetime, datetime.date)):
                sessao[key] = value.isoformat()
            elif isinstance(value, decimal.Decimal):
                sessao[key] = float(value)
            else:
                sessao[key] = value
        
        # Extrair dados do dados_json para facilitar acesso no frontend
        if sessao.get('dados_json'):
            try:
                dados_json = json.loads(sessao['dados_json']) if isinstance(sessao['dados_json'], str) else sessao['dados_json']
                # Não sobrescrever se já existem no nível raiz
                if not sessao.get('horario'):
                    sessao['horario'] = dados_json.get('horario')
                if not sessao.get('tipo_foto'):
                    sessao['tipo_foto'] = dados_json.get('tipo_foto', False)
                if not sessao.get('tipo_video'):
                    sessao['tipo_video'] = dados_json.get('tipo_video', False)
                if not sessao.get('tipo_mobile'):
                    sessao['tipo_mobile'] = dados_json.get('tipo_mobile', False)
            except:
                pass
        
        sessoes.append(sessao)
    
    # Buscar equipe de cada sessi?o
    for sessao in sessoes:
        cursor.execute("""
            SELECT * FROM sessao_equipe WHERE sessao_id = %s
        """, (sessao['id'],))
        sessao['equipe'] = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sessoes

# Função atualizar_sessao já definida na linha 3057 (versão correta)
# Removida duplicata antiga que causava erro de data_sessao NULL

def deletar_sessao(sessao_id: int) -> bool:
    """Deleta uma sessi?o"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM sessoes WHERE id = %s", (sessao_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso


# ==================== FUNi?i?ES CRUD - COMISSi?ES ====================
def adicionar_comissao(dados: Dict) -> int:
    """Adiciona uma nova comissão com suporte a cálculo automático (PARTE 8)"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Buscar cliente_id do contrato se não fornecido
    cliente_id = dados.get('cliente_id')
    contrato_id = dados.get('contrato_id')
    
    if not cliente_id and contrato_id:
        cursor.execute("SELECT cliente_id FROM contratos WHERE id = %s", (contrato_id,))
        result = cursor.fetchone()
        if result:
            cliente_id = result['cliente_id']
    
    # 💰 PARTE 8: Campos de cálculo automático
    sessao_id = dados.get('sessao_id')
    calculo_automatico = dados.get('calculo_automatico', True)
    base_calculo = dados.get('base_calculo', 'sessao')  # 'sessao', 'contrato', 'fixo'
    
    cursor.execute("""
        INSERT INTO comissoes (
            contrato_id, cliente_id, sessao_id, tipo, descricao, 
            valor, percentual, calculo_automatico, base_calculo
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, valor_calculado
    """, (
        contrato_id,
        cliente_id,
        sessao_id,
        dados.get('tipo', 'percentual'),
        dados.get('descricao'),
        dados.get('valor', 0),
        dados.get('percentual', 0),
        calculo_automatico,
        base_calculo
    ))
    
    result = cursor.fetchone()
    comissao_id = result['id']
    valor_calculado = result['valor_calculado']
    
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    
    # Retornar ID e valor calculado para exibição
    return comissao_id

def listar_comissoes() -> List[Dict]:
    """Lista todas as comissões com informações de contrato, cliente e sessão (PARTE 8)"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            com.*,
            ct.numero as contrato_numero,
            ct.valor as contrato_valor,
            cl.nome as cliente_nome,
            s.data as sessao_data,
            s.valor_total as sessao_valor,
            -- 💰 PARTE 8: Exibir valor calculado e formatação
            CASE 
                WHEN com.tipo = 'percentual' THEN 
                    com.percentual::TEXT || '% = R$ ' || COALESCE(com.valor_calculado, 0)::TEXT
                ELSE 
                    'R$ ' || COALESCE(com.valor_calculado, com.valor, 0)::TEXT
            END as comissao_formatada
        FROM comissoes com
        LEFT JOIN contratos ct ON com.contrato_id = ct.id
        LEFT JOIN clientes cl ON com.cliente_id = cl.id
        LEFT JOIN sessoes s ON com.sessao_id = s.id
        ORDER BY com.created_at DESC
    """)
    
    comissoes = []
    for row in cursor.fetchall():
        comissao = dict(row)
        # Converter Decimal para float para JSON
        if comissao.get('valor_calculado'):
            comissao['valor_calculado'] = float(comissao['valor_calculado'])
        if comissao.get('contrato_valor'):
            comissao['contrato_valor'] = float(comissao['contrato_valor'])
        if comissao.get('sessao_valor'):
            comissao['sessao_valor'] = float(comissao['sessao_valor'])
        comissoes.append(comissao)
    
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return comissoes

def atualizar_comissao(comissao_id: int, dados: Dict) -> bool:
    """Atualiza uma comissão com suporte a cálculo automático (PARTE 8)"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Buscar cliente_id do contrato se não fornecido
    cliente_id = dados.get('cliente_id')
    contrato_id = dados.get('contrato_id')
    
    if not cliente_id and contrato_id:
        cursor.execute("SELECT cliente_id FROM contratos WHERE id = %s", (contrato_id,))
        result = cursor.fetchone()
        if result:
            cliente_id = result['cliente_id']
    
    # 💰 PARTE 8: Campos de cálculo automático
    sessao_id = dados.get('sessao_id')
    calculo_automatico = dados.get('calculo_automatico', True)
    base_calculo = dados.get('base_calculo', 'sessao')
    
    cursor.execute("""
        UPDATE comissoes
        SET contrato_id = %s, cliente_id = %s, sessao_id = %s, tipo = %s, 
            descricao = %s, valor = %s, percentual = %s,
            calculo_automatico = %s, base_calculo = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING valor_calculado
    """, (
        contrato_id,
        cliente_id,
        sessao_id,
        dados.get('tipo', 'percentual'),
        dados.get('descricao'),
        dados.get('valor', 0),
        dados.get('percentual', 0),
        calculo_automatico,
        base_calculo,
        comissao_id
    ))
    
    sucesso = cursor.rowcount > 0
    
    # Obter valor recalculado
    if sucesso:
        result = cursor.fetchone()
        if result:
            valor_calculado = result['valor_calculado']
            print(f"   💰 Comissão {comissao_id} atualizada: valor_calculado = R$ {valor_calculado}")
    
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso

def deletar_comissao(comissao_id: int) -> bool:
    """Deleta uma comissi?o"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM comissoes WHERE id = %s", (comissao_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso


# ==================== FUNi?i?ES CRUD - SESSi?O EQUIPE ====================
def adicionar_sessao_equipe(dados: Dict) -> int:
    """Adiciona um membro i? equipe de uma sessi?o"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print(f"[DB] Inserindo membro: {dados}")
    
    cursor.execute("""
        INSERT INTO sessao_equipe (sessao_id, membro_nome, funcao, observacoes)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        dados.get('sessao_id'),
        dados.get('membro_nome'),
        dados.get('funcao'),
        dados.get('observacoes', '')
    ))
    
    se_id = cursor.fetchone()['id']
    print(f"[DB] Membro inserido com ID: {se_id}")
    
    conn.commit()  # COMMIT ESQUECIDO!
    print(f"[DB] COMMIT executado")
    
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return se_id

def listar_sessao_equipe(sessao_id: int = None) -> List[Dict]:
    """Lista membros da equipe de sessi?o"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    if sessao_id:
        cursor.execute("""
            SELECT se.*, 
                   s.titulo as sessao_titulo,
                   s.data_sessao,
                   c.nome as cliente_nome
            FROM sessao_equipe se
            LEFT JOIN sessoes s ON se.sessao_id = s.id
            LEFT JOIN contratos ct ON s.contrato_id = ct.id
            LEFT JOIN clientes c ON ct.cliente_id = c.id
            WHERE se.sessao_id = %s
            ORDER BY se.created_at
        """, (sessao_id,))
    else:
        cursor.execute("""
            SELECT se.*, 
                   s.titulo as sessao_titulo,
                   s.data_sessao,
                   c.nome as cliente_nome
            FROM sessao_equipe se
            LEFT JOIN sessoes s ON se.sessao_id = s.id
            LEFT JOIN contratos ct ON s.contrato_id = ct.id
            LEFT JOIN clientes c ON ct.cliente_id = c.id
            ORDER BY se.created_at DESC
        """)
    
    membros = []
    for row in cursor.fetchall():
        membro = dict(row)
        # Criar sessao_info formatada
        if membro.get('sessao_titulo'):
            info_parts = [membro['sessao_titulo']]
            if membro.get('data_sessao'):
                info_parts.append(str(membro['data_sessao']))
            if membro.get('cliente_nome'):
                info_parts.append(membro['cliente_nome'])
            membro['sessao_info'] = ' - '.join(info_parts)
        else:
            membro['sessao_info'] = f"Sessi?o #{membro.get('sessao_id', '?')}"
        membros.append(membro)
    
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return membros

def atualizar_sessao_equipe(membro_id: int, dados: Dict) -> bool:
    """Atualiza um membro da equipe"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE sessao_equipe
        SET sessao_id = %s, membro_nome = %s, funcao = %s, observacoes = %s
        WHERE id = %s
    """, (
        dados.get('sessao_id'),
        dados.get('membro_nome'),
        dados.get('funcao'),
        dados.get('observacoes', ''),
        membro_id
    ))
    
    sucesso = cursor.rowcount > 0
    conn.commit()  # COMMIT ESQUECIDO!
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso

def deletar_sessao_equipe(membro_id: int) -> bool:
    """Deleta um membro da equipe"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM sessao_equipe WHERE id = %s", (membro_id,))
    
    sucesso = cursor.rowcount > 0
    conn.commit()  # COMMIT ESQUECIDO!
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso

# ==================== TIPOS DE SESSi?O ====================

def adicionar_tipo_sessao(dados: Dict) -> int:
    """Adiciona um novo tipo de sessi?o"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO tipos_sessao (nome, descricao, duracao_padrao, valor_padrao, ativo)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (
        dados['nome'],
        dados.get('descricao'),
        dados.get('duracao_padrao'),
        dados.get('valor_padrao'),
        dados.get('ativo', True)
    ))
    
    tipo_id = cursor.fetchone()['id']
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return tipo_id

def listar_tipos_sessao() -> List[Dict]:
    """Lista todos os tipos de sessi?o"""
    import datetime
    import decimal
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, nome, descricao, duracao_padrao, valor_padrao, ativo, created_at, updated_at
        FROM tipos_sessao
        ORDER BY nome
    """)
    
    tipos = []
    for row in cursor.fetchall():
        tipo = {}
        for key, value in dict(row).items():
            if isinstance(value, (datetime.time, datetime.datetime, datetime.date)):
                tipo[key] = value.isoformat()
            elif isinstance(value, decimal.Decimal):
                tipo[key] = float(value)
            else:
                tipo[key] = value
        tipos.append(tipo)
    
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return tipos

def atualizar_tipo_sessao(tipo_id: int, dados: Dict) -> bool:
    """Atualiza um tipo de sessi?o"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE tipos_sessao 
        SET nome = %s, descricao = %s, duracao_padrao = %s, valor_padrao = %s, ativo = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados['nome'],
        dados.get('descricao'),
        dados.get('duracao_padrao'),
        dados.get('valor_padrao'),
        dados.get('ativo', True),
        tipo_id
    ))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso

def deletar_tipo_sessao(tipo_id: int) -> bool:
    """Deleta um tipo de sessi?o"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tipos_sessao WHERE id = %s", (tipo_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso


# ==================== FUNÇÕES DE RESPONSÁVEIS (CARGOS/FUNÇÕES) ====================

def adicionar_funcao_responsavel(empresa_id: int, dados: Dict) -> int:
    """
    Adiciona uma nova função/cargo para responsáveis
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        dados (Dict): {'nome': str, 'descricao': str (opcional)}
    
    Returns:
        int: ID da função criada
        
    Security:
        🔒 RLS aplicado - função vinculada à empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO funcoes_responsaveis (nome, descricao, empresa_id)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (
            dados['nome'],
            dados.get('descricao', ''),
            empresa_id
        ))
        
        funcao_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        return funcao_id


def listar_funcoes_responsaveis(empresa_id: int, apenas_ativas: bool = True) -> List[Dict]:
    """
    Lista todas as funções de responsáveis da empresa
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        apenas_ativas (bool): Se True, retorna apenas funções ativas
    
    Returns:
        List[Dict]: Lista de funções
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        sql = "SELECT * FROM funcoes_responsaveis WHERE empresa_id = %s"
        params = [empresa_id]
        
        if apenas_ativas:
            sql += " AND ativa = true"
        
        sql += " ORDER BY nome"
        
        cursor.execute(sql, params)
        
        funcoes = []
        for row in cursor.fetchall():
            funcao = dict(row)
            funcoes.append(funcao)
        
        cursor.close()
        return_to_pool(conn)
        return funcoes


def obter_funcao_responsavel(empresa_id: int, funcao_id: int) -> Dict:
    """
    Busca uma função específica
    
    Args:
        empresa_id (int): ID da empresa
        funcao_id (int): ID da função
    
    Returns:
        Dict: Dados da função ou None
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM funcoes_responsaveis
            WHERE id = %s AND empresa_id = %s
        """, (funcao_id, empresa_id))
        
        row = cursor.fetchone()
        funcao = dict(row) if row else None
        
        cursor.close()
        return_to_pool(conn)
        return funcao


def atualizar_funcao_responsavel(empresa_id: int, funcao_id: int, dados: Dict) -> bool:
    """
    Atualiza uma função existente
    
    Args:
        empresa_id (int): ID da empresa
        funcao_id (int): ID da função
        dados (Dict): Dados a atualizar
    
    Returns:
        bool: True se atualizado com sucesso
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE funcoes_responsaveis
            SET nome = %s,
                descricao = %s,
                ativa = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
        """, (
            dados['nome'],
            dados.get('descricao', ''),
            dados.get('ativa', True),
            funcao_id,
            empresa_id
        ))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        return sucesso


def deletar_funcao_responsavel(empresa_id: int, funcao_id: int) -> bool:
    """
    Deleta (ou desativa) uma função
    
    Args:
        empresa_id (int): ID da empresa
        funcao_id (int): ID da função
    
    Returns:
        bool: True se deletado com sucesso
        
    Note:
        Por segurança, pode-se preferir desativar em vez de deletar
        para preservar histórico de sessões antigas.
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # Opção 1: Desativar (recomendado)
        cursor.execute("""
            UPDATE funcoes_responsaveis
            SET ativa = false,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
        """, (funcao_id, empresa_id))
        
        # Opção 2: Deletar permanentemente (descomentar se preferir)
        # cursor.execute("""
        #     DELETE FROM funcoes_responsaveis
        #     WHERE id = %s AND empresa_id = %s
        # """, (funcao_id, empresa_id))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        return sucesso


# ==================== CUSTOS OPERACIONAIS ====================

def adicionar_custo_operacional(empresa_id: int, dados: Dict) -> int:
    """
    Adiciona um novo custo operacional
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        dados (Dict): {
            'nome': str,
            'descricao': str (opcional),
            'categoria': str,
            'valor_padrao': float,
            'unidade': str (opcional, default 'unidade')
        }
    
    Returns:
        int: ID do custo criado
        
    Security:
        🔒 RLS aplicado - custo vinculado à empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO custos_operacionais (nome, descricao, categoria, valor_padrao, unidade, empresa_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            dados['nome'],
            dados.get('descricao', ''),
            dados['categoria'],
            dados.get('valor_padrao', 0.00),
            dados.get('unidade', 'unidade'),
            empresa_id
        ))
        
        custo_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        return custo_id


def listar_custos_operacionais(empresa_id: int, apenas_ativos: bool = True, categoria: str = None) -> List[Dict]:
    """
    Lista todos os custos operacionais da empresa
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        apenas_ativos (bool): Se True, retorna apenas custos ativos
        categoria (str): Filtro opcional por categoria
    
    Returns:
        List[Dict]: Lista de custos
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        sql = "SELECT * FROM custos_operacionais WHERE empresa_id = %s"
        params = [empresa_id]
        
        if apenas_ativos:
            sql += " AND ativo = true"
        
        if categoria:
            sql += " AND categoria = %s"
            params.append(categoria)
        
        sql += " ORDER BY categoria, nome"
        
        cursor.execute(sql, params)
        
        custos = []
        for row in cursor.fetchall():
            custo = dict(row)
            # Converter Decimal para float
            if custo.get('valor_padrao'):
                custo['valor_padrao'] = float(custo['valor_padrao'])
            custos.append(custo)
        
        cursor.close()
        return_to_pool(conn)
        return custos


def obter_custo_operacional(empresa_id: int, custo_id: int) -> Dict:
    """
    Busca um custo específico
    
    Args:
        empresa_id (int): ID da empresa
        custo_id (int): ID do custo
    
    Returns:
        Dict: Dados do custo ou None
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM custos_operacionais
            WHERE id = %s AND empresa_id = %s
        """, (custo_id, empresa_id))
        
        row = cursor.fetchone()
        custo = dict(row) if row else None
        
        if custo and custo.get('valor_padrao'):
            custo['valor_padrao'] = float(custo['valor_padrao'])
        
        cursor.close()
        return_to_pool(conn)
        return custo


def atualizar_custo_operacional(empresa_id: int, custo_id: int, dados: Dict) -> bool:
    """
    Atualiza um custo existente
    
    Args:
        empresa_id (int): ID da empresa
        custo_id (int): ID do custo
        dados (Dict): Dados a atualizar
    
    Returns:
        bool: True se atualizado com sucesso
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE custos_operacionais
            SET nome = %s,
                descricao = %s,
                categoria = %s,
                valor_padrao = %s,
                unidade = %s,
                ativo = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
        """, (
            dados['nome'],
            dados.get('descricao', ''),
            dados['categoria'],
            dados.get('valor_padrao', 0.00),
            dados.get('unidade', 'unidade'),
            dados.get('ativo', True),
            custo_id,
            empresa_id
        ))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        return sucesso


def deletar_custo_operacional(empresa_id: int, custo_id: int) -> bool:
    """
    Deleta (ou desativa) um custo operacional
    
    Args:
        empresa_id (int): ID da empresa
        custo_id (int): ID do custo
    
    Returns:
        bool: True se deletado com sucesso
        
    Note:
        Por segurança, desativa em vez de deletar para preservar histórico.
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # Desativar (recomendado)
        cursor.execute("""
            UPDATE custos_operacionais
            SET ativo = false,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
        """, (custo_id, empresa_id))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        return sucesso


# ==================== TAGS ====================

def adicionar_tag(empresa_id: int, dados: Dict) -> int:
    """
    Adiciona uma nova tag
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        dados (Dict): {
            'nome': str,
            'cor': str (opcional, default '#3b82f6'),
            'icone': str (opcional, default 'tag')
        }
    
    Returns:
        int: ID da tag criada
        
    Security:
        🔒 RLS aplicado - tag vinculada à empresa
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tags (nome, cor, icone, empresa_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            dados['nome'],
            dados.get('cor', '#3b82f6'),
            dados.get('icone', 'tag'),
            empresa_id
        ))
        
        tag_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        return tag_id


def listar_tags(empresa_id: int, apenas_ativas: bool = True) -> List[Dict]:
    """
    Lista todas as tags da empresa
    
    Args:
        empresa_id (int): ID da empresa [OBRIGATÓRIO]
        apenas_ativas (bool): Se True, retorna apenas tags ativas
    
    Returns:
        List[Dict]: Lista de tags
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        sql = "SELECT * FROM tags WHERE empresa_id = %s"
        params = [empresa_id]
        
        if apenas_ativas:
            sql += " AND ativa = true"
        
        sql += " ORDER BY nome"
        
        cursor.execute(sql, params)
        
        tags = []
        for row in cursor.fetchall():
            tag = dict(row)
            tags.append(tag)
        
        cursor.close()
        return_to_pool(conn)
        return tags


def obter_tag(empresa_id: int, tag_id: int) -> Dict:
    """
    Busca uma tag específica
    
    Args:
        empresa_id (int): ID da empresa
        tag_id (int): ID da tag
    
    Returns:
        Dict: Dados da tag ou None
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM tags
            WHERE id = %s AND empresa_id = %s
        """, (tag_id, empresa_id))
        
        row = cursor.fetchone()
        tag = dict(row) if row else None
        
        cursor.close()
        return_to_pool(conn)
        return tag


def atualizar_tag(empresa_id: int, tag_id: int, dados: Dict) -> bool:
    """
    Atualiza uma tag existente
    
    Args:
        empresa_id (int): ID da empresa
        tag_id (int): ID da tag
        dados (Dict): Dados a atualizar
    
    Returns:
        bool: True se atualizado com sucesso
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tags
            SET nome = %s,
                cor = %s,
                icone = %s,
                ativa = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
        """, (
            dados['nome'],
            dados.get('cor', '#3b82f6'),
            dados.get('icone', 'tag'),
            dados.get('ativa', True),
            tag_id,
            empresa_id
        ))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        return sucesso


def deletar_tag(empresa_id: int, tag_id: int) -> bool:
    """
    Deleta (ou desativa) uma tag
    
    Args:
        empresa_id (int): ID da empresa
        tag_id (int): ID da tag
    
    Returns:
        bool: True se deletado com sucesso
        
    Note:
        Por segurança, desativa em vez de deletar para preservar histórico.
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # Desativar (recomendado)
        cursor.execute("""
            UPDATE tags
            SET ativa = false,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
        """, (tag_id, empresa_id))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        return sucesso


def adicionar_tags_sessao(empresa_id: int, sessao_id: int, tag_ids: List[int]) -> bool:
    """
    Adiciona múltiplas tags a uma sessão
    
    Args:
        empresa_id (int): ID da empresa
        sessao_id (int): ID da sessão
        tag_ids (List[int]): IDs das tags
    
    Returns:
        bool: True se adicionado com sucesso
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # Remover tags antigas
        cursor.execute("""
            DELETE FROM sessao_tags
            WHERE sessao_id = %s
        """, (sessao_id,))
        
        # Adicionar novas tags
        if tag_ids:
            for tag_id in tag_ids:
                cursor.execute("""
                    INSERT INTO sessao_tags (sessao_id, tag_id)
                    VALUES (%s, %s)
                    ON CONFLICT (sessao_id, tag_id) DO NOTHING
                """, (sessao_id, tag_id))
        
        conn.commit()
        cursor.close()
        return_to_pool(conn)
        return True


def listar_tags_sessao(empresa_id: int, sessao_id: int) -> List[Dict]:
    """
    Lista tags de uma sessão
    
    Args:
        empresa_id (int): ID da empresa
        sessao_id (int): ID da sessão
    
    Returns:
        List[Dict]: Lista de tags
        
    Security:
        🔒 RLS aplicado
    """
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.*
            FROM tags t
            INNER JOIN sessao_tags st ON st.tag_id = t.id
            WHERE st.sessao_id = %s AND t.empresa_id = %s
            ORDER BY t.nome
        """, (sessao_id, empresa_id))
        
        tags = []
        for row in cursor.fetchall():
            tag = dict(row)
            tags.append(tag)
        
        cursor.close()
        return_to_pool(conn)
        return tags


# ==================== FUNi?i?ES DE AUTENTICAi?i?O E USUi?RIOS ====================

from auth_functions import (
    criar_usuario as _criar_usuario,
    autenticar_usuario as _autenticar_usuario,
    criar_sessao as _criar_sessao,
    validar_sessao as _validar_sessao,
    invalidar_sessao as _invalidar_sessao,
    listar_usuarios as _listar_usuarios,
    obter_usuario as _obter_usuario,
    atualizar_usuario as _atualizar_usuario,
    deletar_usuario as _deletar_usuario,
    listar_permissoes as _listar_permissoes,
    obter_permissoes_usuario as _obter_permissoes_usuario,
    conceder_permissao as _conceder_permissao,
    revogar_permissao as _revogar_permissao,
    sincronizar_permissoes_usuario as _sincronizar_permissoes_usuario,
    registrar_log_acesso as _registrar_log_acesso
)

def criar_usuario(dados: Dict) -> int:
    """Wrapper para criar_usuario"""
    db = DatabaseManager()
    return _criar_usuario(dados, db)

def autenticar_usuario(username: str, password: str) -> Optional[Dict]:
    """Wrapper para autenticar_usuario"""
    db = DatabaseManager()
    return _autenticar_usuario(username, password, db)

def criar_sessao(usuario_id: int, ip_address: str, user_agent: str) -> str:
    """Wrapper para criar_sessao"""
    db = DatabaseManager()
    return _criar_sessao(usuario_id, ip_address, user_agent, db)

def validar_sessao(token: str) -> Optional[Dict]:
    """
    Valida uma sessão e retorna os dados do usuário
    ATUALIZADO: 2026-02-04 18:30 - Incluir empresas associadas
    
    Returns:
        Dict com dados do usuário se sessão válida, None caso contrário
    """
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT s.usuario_id, s.expira_em, s.ativo,
                   u.username, u.tipo, u.nome_completo, u.email, u.cliente_id
            FROM sessoes_login s
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE s.session_token = %s AND s.ativo = TRUE AND u.ativo = TRUE
        """, (token,))
        
        sessao = cursor.fetchone()
        
        if not sessao:
            return None
        
        # Verificar expiração
        from datetime import datetime
        if sessao['expira_em'] < datetime.now():
            # Sessão expirada - desativar
            cursor.execute("""
                UPDATE sessoes_login SET ativo = FALSE WHERE session_token = %s
            """, (token,))
            conn.commit()
            return None
        
        # 🔥 NOVO: Buscar empresas associadas ao usuário
        cursor.execute("""
            SELECT empresa_id
            FROM usuario_empresas
            WHERE usuario_id = %s
            ORDER BY empresa_id
        """, (sessao['usuario_id'],))
        
        empresas_rows = cursor.fetchall()
        empresas = [row['empresa_id'] if isinstance(row, dict) else row[0] for row in empresas_rows]
        
        print(f"🔍 [validar_sessao DB] Usuario {sessao['username']} tem empresas: {empresas}")
        
        # Determinar empresa_id (da sessão ou primeira disponível)
        from flask import session as flask_session
        empresa_id = flask_session.get('empresa_id')
        print(f"🔍 [validar_sessao DB] empresa_id da sessão Flask: {empresa_id}")
        
        if not empresa_id and empresas:
            empresa_id = empresas[0]
            flask_session['empresa_id'] = empresa_id
            print(f"🔍 [validar_sessao DB] Definindo empresa_id como: {empresa_id}")
        
        usuario_retorno = {
            'id': sessao['usuario_id'],
            'username': sessao['username'],
            'tipo': sessao['tipo'],
            'nome_completo': sessao['nome_completo'],
            'email': sessao['email'],
            'cliente_id': sessao['cliente_id'],
            'empresa_id': empresa_id,
            'empresas': empresas
        }
        
        print(f"✅ [validar_sessao DB] Retornando: empresa_id={empresa_id}, empresas={empresas}")
        return usuario_retorno
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def invalidar_sessao(token: str) -> bool:
    """Invalida uma sessi?o (logout)"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE sessoes_login SET ativo = FALSE WHERE session_token = %s
        """, (token,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao invalidar sessi?o: {e}")
        return False
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def listar_usuarios(apenas_ativos: bool = True) -> List[Dict]:
    """Lista todos os usui?rios do sistema"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        filtro = "WHERE u.ativo = TRUE" if apenas_ativos else ""
        cursor.execute(f"""
            SELECT u.id, u.username, u.tipo, u.nome_completo, u.email, u.telefone,
                   u.ativo, u.empresa_id, u.ultimo_acesso, u.created_at,
                   COALESCE(
                       (SELECT e.razao_social 
                        FROM usuario_empresas ue 
                        JOIN empresas e ON ue.empresa_id = e.id 
                        WHERE ue.usuario_id = u.id 
                          AND ue.ativo = TRUE 
                          AND ue.is_empresa_padrao = TRUE 
                        LIMIT 1),
                       (SELECT e.razao_social 
                        FROM usuario_empresas ue 
                        JOIN empresas e ON ue.empresa_id = e.id 
                        WHERE ue.usuario_id = u.id 
                          AND ue.ativo = TRUE 
                        ORDER BY ue.id ASC 
                        LIMIT 1),
                       'Não atribuída'
                   ) as empresa_nome,
                   (SELECT MAX(sl.criado_em) FROM sessoes_login sl WHERE sl.usuario_id = u.id) as ultima_sessao
            FROM usuarios u
            {filtro}
            ORDER BY u.tipo, u.nome_completo
        """)
        rows = cursor.fetchall()
        
        # Converter RealDictRow para dict padri?o
        usuarios = [dict(row) for row in rows]
        
        print(f"   ?? listar_usuarios() retornando {len(usuarios)} usui?rios")
        return usuarios
    except Exception as e:
        print(f"   ? Erro em listar_usuarios(): {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def obter_usuario(usuario_id: int) -> Optional[Dict]:
    """Obtem dados de um usuario especifico"""
    log(f"\n[obter_usuario] Buscando usuario ID: {usuario_id}")
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT u.id, u.username, u.tipo, u.nome_completo, u.email, u.telefone,
                   u.ativo, u.empresa_id, u.ultimo_acesso, u.created_at,
                   COALESCE(
                       (SELECT e.razao_social 
                        FROM usuario_empresas ue 
                        JOIN empresas e ON ue.empresa_id = e.id 
                        WHERE ue.usuario_id = u.id 
                          AND ue.ativo = TRUE 
                          AND ue.is_empresa_padrao = TRUE 
                        LIMIT 1),
                       (SELECT e.razao_social 
                        FROM usuario_empresas ue 
                        JOIN empresas e ON ue.empresa_id = e.id 
                        WHERE ue.usuario_id = u.id 
                          AND ue.ativo = TRUE 
                        ORDER BY ue.id ASC 
                        LIMIT 1),
                       'Não atribuída'
                   ) as empresa_nome
            FROM usuarios u
            WHERE u.id = %s
        """
        log(f"   Query: {query.strip()}")
        log(f"   Parametro: usuario_id={usuario_id}")
        cursor.execute(query, (usuario_id,))
        resultado = cursor.fetchone()
        log(f"   Resultado: {dict(resultado) if resultado else 'NENHUM REGISTRO ENCONTRADO'}")
        return dict(resultado) if resultado else None
    except Exception as e:
        log(f"   Erro ao buscar usuario: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
def atualizar_usuario(usuario_id: int, dados: Dict) -> bool:
    """Atualiza dados de um usui?rio"""
    print(f"\n{'='*80}")
    print(f"[database_postgresql.atualizar_usuario] INICIANDO")
    print(f"   - usuario_id: {usuario_id} (tipo: {type(usuario_id)})")
    print(f"   - dados: {dados}")
    print(f"   - Keys em dados: {list(dados.keys())}")
    print(f"{'='*80}")
    
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        campos = []
        valores = []
        
        print(f"🔍 Processando campos...")
        
        if 'username' in dados:
            print(f"   ✅ username: {dados['username']}")
            campos.append("username = %s")
            valores.append(dados['username'])
        if 'nome_completo' in dados:
            print(f"   ✅ nome_completo: {dados['nome_completo']}")
            campos.append("nome_completo = %s")
            valores.append(dados['nome_completo'])
        if 'nome' in dados:  # Aceita tambi?m 'nome'
            print(f"   ✅ nome: {dados['nome']}")
            campos.append("nome_completo = %s")
            valores.append(dados['nome'])
        if 'email' in dados:
            print(f"   ✅ email: {dados['email']}")
            campos.append("email = %s")
            valores.append(dados['email'])
        if 'telefone' in dados:
            print(f"   ✅ telefone: {dados['telefone']}")
            campos.append("telefone = %s")
            valores.append(dados['telefone'])
        if 'tipo' in dados:
            print(f"   ✅ tipo: {dados['tipo']}")
            campos.append("tipo = %s")
            valores.append(dados['tipo'])
        if 'empresa_id' in dados:
            print(f"   ✅ empresa_id: {dados['empresa_id']} (tipo: {type(dados['empresa_id'])})")
            # Validar se é None ou int válido
            empresa_id_val = dados['empresa_id']
            if empresa_id_val is None or empresa_id_val == '':
                print(f"      ⚠️ empresa_id é None/vazio - setando NULL")
                campos.append("empresa_id = NULL")
            else:
                print(f"      ✅ empresa_id válido: {empresa_id_val}")
                campos.append("empresa_id = %s")
                valores.append(int(empresa_id_val))
        if 'ativo' in dados:
            print(f"   ✅ ativo: {dados['ativo']}")
            campos.append("ativo = %s")
            valores.append(dados['ativo'])
        if 'password' in dados and dados['password']:  # Si? atualiza se senha ni?o vazia
            print(f"   ✅ password: *** (hash será gerado)")
            import hashlib
            password_hash = hashlib.sha256(dados['password'].encode()).hexdigest()
            campos.append("password_hash = %s")
            valores.append(password_hash)
        
        if not campos:
            print(f"   ⚠️ Nenhum campo para atualizar!")
            print(f"{'='*80}\n")
            return False
        
        valores.append(usuario_id)
        query = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = %s"
        print(f"\n📝 Query SQL:")
        print(f"   {query}")
        print(f"   Valores: {valores}")
        
        cursor.execute(query, valores)
        affected = cursor.rowcount
        conn.commit()
        
        print(f"\n✅ UPDATE executado com sucesso!")
        print(f"   Linhas afetadas: {affected}")
        print(f"{'='*80}\n")
        
        return affected > 0
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERRO em atualizar_usuario!")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {e}")
        print(f"   Query tentada: {query if 'query' in locals() else 'Query não construída'}")
        print(f"   Valores: {valores if 'valores' in locals() else 'Valores não definidos'}")
        import traceback
        traceback.print_exc()
        print(f"{'='*80}\n")
        return False
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def deletar_usuario(usuario_id: int) -> bool:
    """Deleta um usui?rio (ni?o permite deletar admin principal ID=1)"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se nao e o admin principal (ID = 1)
        if usuario_id == 1:
            log("Nao e possivel deletar o administrador principal (ID=1)")
            return False
        
        # Deletar registros relacionados ANTES de deletar o usuario (foreign keys)
        log(f"Deletando registros relacionados do usuario {usuario_id}...")
        
        # 1. Deletar log_acessos
        cursor.execute("DELETE FROM log_acessos WHERE usuario_id = %s", (usuario_id,))
        log(f"  - log_acessos: {cursor.rowcount} registros deletados")
        
        # 2. Deletar sessoes_login
        cursor.execute("DELETE FROM sessoes_login WHERE usuario_id = %s", (usuario_id,))
        log(f"  - sessoes_login: {cursor.rowcount} registros deletados")
        
        # 3. Deletar usuario_permissoes
        cursor.execute("DELETE FROM usuario_permissoes WHERE usuario_id = %s", (usuario_id,))
        log(f"  - usuario_permissoes: {cursor.rowcount} registros deletados")
        
        # 4. Deletar login_attempts (se houver)
        cursor.execute("DELETE FROM login_attempts WHERE username = (SELECT username FROM usuarios WHERE id = %s)", (usuario_id,))
        log(f"  - login_attempts: {cursor.rowcount} registros deletados")
        
        # Agora deletar o usuario
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        affected = cursor.rowcount
        
        if affected > 0:
            log(f"Usuario {usuario_id} deletado com sucesso")
        else:
            log(f"Usuario {usuario_id} nao encontrado")
        
        return affected > 0
    except Exception as e:
        log(f"Erro ao deletar usuario: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def listar_permissoes(categoria: Optional[str] = None) -> List[Dict]:
    """Lista todas as permissi?es do sistema"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        filtro = "WHERE categoria = %s" if categoria else ""
        params = (categoria,) if categoria else ()
        cursor.execute(f"""
            SELECT id, codigo, nome, descricao, categoria
            FROM permissoes
            {filtro}
            ORDER BY categoria, nome
        """, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def obter_permissoes_usuario(usuario_id: int) -> List[str]:
    """Obti?m lista de ci?digos de permissi?o de um usui?rio"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT p.codigo
            FROM usuario_permissoes up
            JOIN permissoes p ON up.permissao_id = p.id
            WHERE up.usuario_id = %s
        """, (usuario_id,))
        return [row['codigo'] for row in cursor.fetchall()]
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def conceder_permissao(usuario_id: int, permissao_codigo: str, concedido_por: int) -> bool:
    """Concede uma permissi?o a um usui?rio"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM permissoes WHERE codigo = %s", (permissao_codigo,))
        permissao = cursor.fetchone()
        if not permissao:
            return False
        
        cursor.execute("""
            INSERT INTO usuario_permissoes (usuario_id, permissao_id, concedido_por)
            VALUES (%s, %s, %s)
            ON CONFLICT (usuario_id, permissao_id) DO NOTHING
        """, (usuario_id, permissao['id'], concedido_por))
        return True
    except Exception as e:
        print(f"Erro ao conceder permissi?o: {e}")
        return False
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def revogar_permissao(usuario_id: int, permissao_codigo: str) -> bool:
    """Revoga uma permissi?o de um usui?rio"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM usuario_permissoes
            WHERE usuario_id = %s AND permissao_id = (
                SELECT id FROM permissoes WHERE codigo = %s
            )
        """, (usuario_id, permissao_codigo))
        return True
    except Exception as e:
        print(f"Erro ao revogar permissi?o: {e}")
        return False
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def sincronizar_permissoes_usuario(usuario_id: int, codigos_permissoes: List[str], concedido_por: int) -> bool:
    """Sincroniza as permissi?es de um usui?rio (remove antigas e adiciona novas)"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Remover todas as permissi?es atuais
        cursor.execute("DELETE FROM usuario_permissoes WHERE usuario_id = %s", (usuario_id,))
        print(f"?? Removidas permissi?es antigas do usui?rio {usuario_id}")
        
        # Adicionar novas permissi?es
        permissoes_adicionadas = 0
        for codigo in codigos_permissoes:
            cursor.execute("SELECT id FROM permissoes WHERE codigo = %s", (codigo,))
            permissao = cursor.fetchone()
            if permissao:
                cursor.execute("""
                    INSERT INTO usuario_permissoes (usuario_id, permissao_id, concedido_por)
                    VALUES (%s, %s, %s)
                """, (usuario_id, permissao['id'], concedido_por))
                permissoes_adicionadas += 1
        
        print(f"? {permissoes_adicionadas} permissi?es sincronizadas para usui?rio {usuario_id}")
        return True
    except Exception as e:
        print(f"? Erro ao sincronizar permissi?es: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def registrar_log_acesso(usuario_id: int, acao: str, descricao: str, ip_address: str, sucesso: bool):
    """Registra um log de acesso"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO log_acessos (usuario_id, acao, descricao, ip_address, sucesso)
            VALUES (%s, %s, %s, %s, %s)
        """, (usuario_id, acao, descricao, ip_address, sucesso))
        conn.commit()
    except Exception as e:
        print(f"Erro ao registrar log: {e}")
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool


def exportar_dados_cliente(cliente_id: int) -> dict:
    """
    Exporta todos os dados de um cliente especi?fico
    
    Args:
        cliente_id: ID do cliente proprieti?rio dos dados
        
    Returns:
        dict: Dicioni?rio com todos os dados do cliente em formato texto
    """
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Gerar relati?rio em texto
        linhas = []
        linhas.append("=" * 80)
        linhas.append(f"EXPORTAi?i?O DE DADOS - CLIENTE ID: {cliente_id}")
        linhas.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        linhas.append("=" * 80)
        linhas.append("")
        
        # Contadores
        stats = {
            'clientes': 0,
            'fornecedores': 0,
            'categorias': 0,
            'contas': 0,
            'lancamentos': 0
        }
        
        # 1. Exportar Clientes
        linhas.append("-" * 80)
        linhas.append("CLIENTES CADASTRADOS")
        linhas.append("-" * 80)
        
        cursor.execute("""
            SELECT id, nome, cpf_cnpj, email, telefone, endereco, ativo, 
                   created_at, updated_at, proprietario_id
            FROM clientes 
            WHERE proprietario_id = %s
            ORDER BY nome
        """, (cliente_id,))
        
        clientes = cursor.fetchall()
        stats['clientes'] = len(clientes)
        
        if clientes:
            for cliente in clientes:
                linhas.append(f"\nID: {cliente['id']}")
                linhas.append(f"Nome: {cliente['nome']}")
                linhas.append(f"CPF/CNPJ: {cliente['cpf_cnpj'] or 'Ni?o informado'}")
                linhas.append(f"Email: {cliente['email'] or 'Ni?o informado'}")
                linhas.append(f"Telefone: {cliente['telefone'] or 'Ni?o informado'}")
                linhas.append(f"Enderei?o: {cliente['endereco'] or 'Ni?o informado'}")
                linhas.append(f"Ativo: {'Sim' if cliente['ativo'] else 'Ni?o'}")
                linhas.append(f"Cadastrado em: {cliente['created_at'].strftime('%d/%m/%Y') if cliente['created_at'] else 'N/A'}")
                linhas.append("-" * 40)
        else:
            linhas.append("Nenhum cliente cadastrado.")
        
        linhas.append("")
        
        # 2. Exportar Fornecedores
        linhas.append("-" * 80)
        linhas.append("FORNECEDORES CADASTRADOS")
        linhas.append("-" * 80)
        
        cursor.execute("""
            SELECT id, nome, cpf_cnpj, email, telefone, endereco, ativo,
                   created_at, updated_at, proprietario_id
            FROM fornecedores
            WHERE proprietario_id = %s
            ORDER BY nome
        """, (cliente_id,))
        
        fornecedores = cursor.fetchall()
        stats['fornecedores'] = len(fornecedores)
        
        if fornecedores:
            for fornecedor in fornecedores:
                linhas.append(f"\nID: {fornecedor['id']}")
                linhas.append(f"Nome: {fornecedor['nome']}")
                linhas.append(f"CPF/CNPJ: {fornecedor['cpf_cnpj'] or 'Ni?o informado'}")
                linhas.append(f"Email: {fornecedor['email'] or 'Ni?o informado'}")
                linhas.append(f"Telefone: {fornecedor['telefone'] or 'Ni?o informado'}")
                linhas.append(f"Enderei?o: {fornecedor['endereco'] or 'Ni?o informado'}")
                linhas.append(f"Ativo: {'Sim' if fornecedor['ativo'] else 'Ni?o'}")
                linhas.append(f"Cadastrado em: {fornecedor['created_at'].strftime('%d/%m/%Y') if fornecedor['created_at'] else 'N/A'}")
                linhas.append("-" * 40)
        else:
            linhas.append("Nenhum fornecedor cadastrado.")
        
        linhas.append("")
        
        # 3. Exportar Categorias
        linhas.append("-" * 80)
        linhas.append("CATEGORIAS")
        linhas.append("-" * 80)
        
        cursor.execute("""
            SELECT id, nome, tipo, descricao, cor, icone, subcategorias, proprietario_id
            FROM categorias
            WHERE proprietario_id = %s
            ORDER BY tipo, nome
        """, (cliente_id,))
        
        categorias = cursor.fetchall()
        stats['categorias'] = len(categorias)
        
        if categorias:
            for categoria in categorias:
                linhas.append(f"\nID: {categoria['id']}")
                linhas.append(f"Nome: {categoria['nome']}")
                linhas.append(f"Tipo: {categoria['tipo'].upper()}")
                linhas.append(f"Descrii?i?o: {categoria['descricao'] or 'Sem descrii?i?o'}")
                if categoria['subcategorias']:
                    linhas.append(f"Subcategorias: {', '.join(categoria['subcategorias'])}")
                linhas.append("-" * 40)
        else:
            linhas.append("Nenhuma categoria cadastrada.")
        
        linhas.append("")
        
        # 4. Exportar Contas Banci?rias
        linhas.append("-" * 80)
        linhas.append("CONTAS BANCi?RIAS")
        linhas.append("-" * 80)
        
        cursor.execute("""
            SELECT id, nome, banco, agencia, conta, saldo_inicial, 
                   ativa, data_criacao, proprietario_id
            FROM contas_bancarias
            WHERE proprietario_id = %s
            ORDER BY nome
        """, (cliente_id,))
        
        contas = cursor.fetchall()
        stats['contas'] = len(contas)
        
        if contas:
            for conta in contas:
                linhas.append(f"\nID: {conta['id']}")
                linhas.append(f"Nome: {conta['nome']}")
                linhas.append(f"Banco: {conta['banco']}")
                linhas.append(f"Agi?ncia: {conta['agencia']}")
                linhas.append(f"Conta: {conta['conta']}")
                linhas.append(f"Saldo Inicial: R$ {float(conta['saldo_inicial']) if conta['saldo_inicial'] else 0:.2f}")
                linhas.append(f"Ativa: {'Sim' if conta['ativa'] else 'Ni?o'}")
                linhas.append("-" * 40)
        else:
            linhas.append("Nenhuma conta banci?ria cadastrada.")
        
        linhas.append("")
        
        # 5. Exportar Lani?amentos
        linhas.append("-" * 80)
        linhas.append("LANi?AMENTOS FINANCEIROS")
        linhas.append("-" * 80)
        
        cursor.execute("""
            SELECT id, tipo, descricao, valor, data_vencimento,
                   data_pagamento, status, categoria, subcategoria, conta_bancaria,
                   cliente_fornecedor, observacoes, recorrente, 
                   created_at, proprietario_id, juros, desconto
            FROM lancamentos
            WHERE proprietario_id = %s
            ORDER BY data_vencimento DESC
            LIMIT 1000
        """, (cliente_id,))
        
        lancamentos = cursor.fetchall()
        stats['lancamentos'] = len(lancamentos)
        
        if lancamentos:
            # Agrupar por tipo
            receitas = [l for l in lancamentos if l['tipo'] == 'receita']
            despesas = [l for l in lancamentos if l['tipo'] == 'despesa']
            
            linhas.append(f"\nTotal de lani?amentos: {len(lancamentos)}")
            linhas.append(f"  - Receitas: {len(receitas)}")
            linhas.append(f"  - Despesas: {len(despesas)}")
            linhas.append("")
            
            for lanc in lancamentos[:100]:  # Limitar a 100 para ni?o ficar muito grande
                linhas.append(f"\nID: {lanc['id']} | Tipo: {lanc['tipo'].upper()}")
                linhas.append(f"Descrii?i?o: {lanc['descricao']}")
                linhas.append(f"Valor: R$ {float(lanc['valor']) if lanc['valor'] else 0:.2f}")
                if lanc['juros'] and float(lanc['juros']) > 0:
                    linhas.append(f"Juros: R$ {float(lanc['juros']):.2f}")
                if lanc['desconto'] and float(lanc['desconto']) > 0:
                    linhas.append(f"Desconto: R$ {float(lanc['desconto']):.2f}")
                linhas.append(f"Data Vencimento: {lanc['data_vencimento'].strftime('%d/%m/%Y') if lanc['data_vencimento'] else 'N/A'}")
                linhas.append(f"Status: {lanc['status'].upper()}")
                if lanc['data_pagamento']:
                    linhas.append(f"Data Pagamento: {lanc['data_pagamento'].strftime('%d/%m/%Y')}")
                if lanc['categoria']:
                    linhas.append(f"Categoria: {lanc['categoria']}")
                if lanc['subcategoria']:
                    linhas.append(f"Subcategoria: {lanc['subcategoria']}")
                if lanc['conta_bancaria']:
                    linhas.append(f"Conta: {lanc['conta_bancaria']}")
                if lanc['cliente_fornecedor']:
                    linhas.append(f"Cliente/Fornecedor: {lanc['cliente_fornecedor']}")
                if lanc['observacoes']:
                    linhas.append(f"Observai?i?es: {lanc['observacoes']}")
                linhas.append("-" * 40)
            
            if len(lancamentos) > 100:
                linhas.append(f"\n... e mais {len(lancamentos) - 100} lani?amentos ni?o exibidos ...")
        else:
            linhas.append("Nenhum lani?amento cadastrado.")
        
        linhas.append("")
        
        # Resumo Final
        linhas.append("=" * 80)
        linhas.append("RESUMO DA EXPORTAi?i?O")
        linhas.append("=" * 80)
        linhas.append(f"Clientes: {stats['clientes']}")
        linhas.append(f"Fornecedores: {stats['fornecedores']}")
        linhas.append(f"Categorias: {stats['categorias']}")
        linhas.append(f"Contas Banci?rias: {stats['contas']}")
        linhas.append(f"Lani?amentos: {stats['lancamentos']}")
        linhas.append("=" * 80)
        
        print(f"? Exportai?i?o conclui?da: {stats['clientes']} clientes, {stats['fornecedores']} fornecedores, {stats['categorias']} categorias, {stats['contas']} contas, {stats['lancamentos']} lani?amentos")
        
        # Retornar dados estruturados
        return {
            'texto': '\n'.join(linhas),
            'estatisticas': stats,
            'cliente_id': cliente_id,
            'data_exportacao': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"? Erro ao exportar dados do cliente {cliente_id}: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        cursor.close()
        return_to_pool(conn)


# ========================================
# FUNi?i?ES DE PREFERi?NCIAS DO USUi?RIO
# ========================================

def salvar_preferencia_usuario(usuario_id, chave, valor):
    """
    Salva ou atualiza uma preferi?ncia do usui?rio.
    
    Args:
        usuario_id: ID do usui?rio
        chave: Chave da preferi?ncia (ex: 'menu_order')
        valor: Valor da preferi?ncia (seri? convertido para JSON se ni?o for string)
    
    Returns:
        bool: True se salvo com sucesso, False caso contri?rio
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Converter valor para JSON se ni?o for string
        if not isinstance(valor, str):
            import json
            valor = json.dumps(valor)
        
        # INSERT ... ON CONFLICT UPDATE (upsert)
        cursor.execute("""
            INSERT INTO user_preferences (usuario_id, preferencia_chave, preferencia_valor, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (usuario_id, preferencia_chave)
            DO UPDATE SET
                preferencia_valor = EXCLUDED.preferencia_valor,
                updated_at = NOW()
        """, (usuario_id, chave, valor))
        
        conn.commit()
        print(f"? Preferi?ncia salva: usuario={usuario_id}, chave={chave}")
        return True
        
    except Exception as e:
        print(f"? Erro ao salvar preferi?ncia: {e}")
        if conn:
            conn.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_to_pool(conn)


def obter_preferencia_usuario(usuario_id, chave, padrao=None):
    """
    Obti?m uma preferi?ncia do usui?rio.
    
    Args:
        usuario_id: ID do usui?rio
        chave: Chave da preferi?ncia
        padrao: Valor padri?o se ni?o encontrado
    
    Returns:
        str|None: Valor da preferi?ncia ou valor padri?o
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT preferencia_valor
            FROM user_preferences
            WHERE usuario_id = %s AND preferencia_chave = %s
        """, (usuario_id, chave))
        
        resultado = cursor.fetchone()
        
        if resultado:
            return resultado[0]
        return padrao
        
    except Exception as e:
        print(f"? Erro ao obter preferi?ncia: {e}")
        import traceback
        traceback.print_exc()
        return padrao
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_to_pool(conn)


def listar_preferencias_usuario(usuario_id):
    """
    Lista todas as preferi?ncias de um usui?rio.
    
    Args:
        usuario_id: ID do usui?rio
    
    Returns:
        dict: Dicioni?rio com chave -> valor
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT preferencia_chave, preferencia_valor
            FROM user_preferences
            WHERE usuario_id = %s
        """, (usuario_id,))
        
        resultados = cursor.fetchall()
        
        # Converter para dicioni?rio
        preferencias = {}
        for chave, valor in resultados:
            preferencias[chave] = valor
        
        return preferencias
        
    except Exception as e:
        print(f"? Erro ao listar preferi?ncias: {e}")
        import traceback
        traceback.print_exc()
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_to_pool(conn)


def deletar_preferencia_usuario(usuario_id, chave):
    """
    Deleta uma preferi?ncia do usui?rio.
    
    Args:
        usuario_id: ID do usui?rio
        chave: Chave da preferi?ncia a deletar
    
    Returns:
        bool: True se deletado com sucesso, False caso contri?rio
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM user_preferences
            WHERE usuario_id = %s AND preferencia_chave = %s
        """, (usuario_id, chave))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"? Preferi?ncia deletada: usuario={usuario_id}, chave={chave}")
            return True
        else:
            print(f"?? Preferi?ncia ni?o encontrada: usuario={usuario_id}, chave={chave}")
            return False
        
    except Exception as e:
        print(f"? Erro ao deletar preferi?ncia: {e}")
        if conn:
            conn.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_to_pool(conn)


# ========================================
# FUNi?i?ES DE GESTi?O DE EMPRESAS (TENANTS)
# ========================================

def criar_empresa(dados):
    """
    Cria uma nova empresa (tenant) no sistema
    
    Args:
        dados: dict com razao_social, cnpj, email, etc.
    
    Returns:
        dict: {'success': True, 'empresa_id': id} ou {'success': False, 'error': msg}
    """
    try:
        with get_db_connection() as conn:
            conn.autocommit = False  # Desligar autocommit para transacao
            cursor = conn.cursor()
            
            # Validar campos obrigati?rios
            if not dados.get('razao_social'):
                return {'success': False, 'error': 'Razi?o social i? obrigati?ria'}
            
            if not dados.get('email'):
                return {'success': False, 'error': 'Email i? obrigati?rio'}
            
            # Verificar se email ji? existe
            cursor.execute("SELECT id FROM empresas WHERE email = %s", (dados['email'],))
            if cursor.fetchone():
                return {'success': False, 'error': 'Email ji? cadastrado'}
            
            # Verificar se CNPJ ji? existe (se fornecido)
            if dados.get('cnpj'):
                cursor.execute("SELECT id FROM empresas WHERE cnpj = %s", (dados['cnpj'],))
                if cursor.fetchone():
                    return {'success': False, 'error': 'CNPJ ji? cadastrado'}
            
            # Inserir empresa
            cursor.execute("""
                INSERT INTO empresas (
                    razao_social, nome_fantasia, cnpj, email, telefone, whatsapp,
                    endereco, cidade, estado, cep, plano, 
                    max_usuarios, max_clientes, max_lancamentos_mes, espaco_storage_mb,
                    observacoes, ativo
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id
            """, (
                dados['razao_social'],
                dados.get('nome_fantasia'),
                dados.get('cnpj'),
                dados['email'],
                dados.get('telefone'),
                dados.get('whatsapp'),
                dados.get('endereco'),
                dados.get('cidade'),
                dados.get('estado'),
                dados.get('cep'),
                dados.get('plano', 'basico'),
                dados.get('max_usuarios', 5),
                dados.get('max_clientes', 100),
                dados.get('max_lancamentos_mes', 500),
                dados.get('espaco_storage_mb', 1024),
                dados.get('observacoes'),
                dados.get('ativo', True)
            ))
            
            resultado = cursor.fetchone()
            empresa_id = resultado['id'] if isinstance(resultado, dict) else resultado[0]
            conn.commit()
            cursor.close()
            conn.autocommit = True  # Religar autocommit
            
            log(f"Empresa criada: ID={empresa_id}, Razao Social={dados['razao_social']}")
            return {'success': True, 'empresa_id': empresa_id}
        
    except Exception as e:
        log(f"Erro ao criar empresa: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {'success': False, 'error': str(e)}


def atualizar_empresa(empresa_id, dados):
    """
    Atualiza dados de uma empresa
    
    Args:
        empresa_id: ID da empresa
        dados: dict com campos a atualizar
    
    Returns:
        dict: {'success': True/False, 'error': msg}
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar se empresa existe
            cursor.execute("SELECT id FROM empresas WHERE id = %s", (empresa_id,))
            if not cursor.fetchone():
                return {'success': False, 'error': 'Empresa ni?o encontrada'}
            
            # Construir query de update dinamicamente
            campos_atualizacao = []
            valores = []
            
            campos_permitidos = [
                'razao_social', 'nome_fantasia', 'cnpj', 'email', 'telefone', 'whatsapp',
                'endereco', 'cidade', 'estado', 'cep', 'plano',
                'max_usuarios', 'max_clientes', 'max_lancamentos_mes', 'espaco_storage_mb',
                'observacoes', 'ativo'
            ]
            
            for campo in campos_permitidos:
                if campo in dados:
                    campos_atualizacao.append(f"{campo} = %s")
                    valores.append(dados[campo])
            
            if not campos_atualizacao:
                return {'success': False, 'error': 'Nenhum campo para atualizar'}
            
            # Adicionar updated_at
            campos_atualizacao.append("updated_at = NOW()")
            valores.append(empresa_id)
            
            query = f"UPDATE empresas SET {', '.join(campos_atualizacao)} WHERE id = %s"
            cursor.execute(query, valores)
            
            conn.commit()
            cursor.close()
            
            log(f"Empresa {empresa_id} atualizada")
            return {'success': True}
        
    except Exception as e:
        log(f"Erro ao atualizar empresa: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {'success': False, 'error': str(e)}


def obter_empresa(empresa_id):
    """
    Obti?m dados de uma empresa
    
    Args:
        empresa_id: ID da empresa
    
    Returns:
        dict: Dados da empresa ou None
    """
    log(f"[obter_empresa] INICIO - empresa_id={empresa_id}")
    try:
        log(f"[obter_empresa] Chamando get_db_connection()...")
        with get_db_connection() as conn:
            log(f"[obter_empresa] Conexao obtida: {type(conn)}")
            log(f"[obter_empresa] Criando cursor com RealDictCursor...")
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            log(f"[obter_empresa] Cursor criado: {type(cursor)}")
            
            query = "SELECT * FROM empresas WHERE id = %s"
            log(f"[obter_empresa] Executando query: {query} com id={empresa_id}")
            cursor.execute(query, (empresa_id,))
            log(f"[obter_empresa] Query executada")
            
            empresa = cursor.fetchone()
            log(f"[obter_empresa] Fetchone concluido: {empresa is not None}")
            cursor.close()
            log(f"[obter_empresa] Cursor fechado")
            
            if empresa:
                resultado = dict(empresa)
                log(f"[obter_empresa] Retornando empresa: {resultado.get('razao_social')}")
                return resultado
            
            log(f"[obter_empresa] Empresa nao encontrada")
            return None
        
    except Exception as e:
        log(f"[obter_empresa] ERRO: {e}")
        log(f"[obter_empresa] Tipo do erro: {type(e)}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def listar_empresas(filtros=None):
    """
    Lista todas as empresas com filtros opcionais
    
    Args:
        filtros: dict opcional {'ativo': True, 'plano': 'basico', etc}
    
    Returns:
        list: Lista de empresas
    """
    try:
        log(f"   [listar_empresas] Iniciando...")
        log(f"   [listar_empresas] Filtros: {filtros}")
        
        with get_db_connection() as conn:
            log(f"   [listar_empresas] Conexao obtida")
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            log(f"   [listar_empresas] Cursor criado")
            
            query = "SELECT * FROM empresas"
            valores = []
            
            if filtros:
                condicoes = []
                if 'ativo' in filtros:
                    condicoes.append("ativo = %s")
                    valores.append(filtros['ativo'])
                
                if 'plano' in filtros:
                    condicoes.append("plano = %s")
                    valores.append(filtros['plano'])
                
                if condicoes:
                    query += " WHERE " + " AND ".join(condicoes)
            
            query += " ORDER BY razao_social"
            
            log(f"   [listar_empresas] Query: {query}")
            log(f"   [listar_empresas] Valores: {valores}")
            
            cursor.execute(query, valores)
            log(f"   [listar_empresas] Query executada")
            
            empresas = cursor.fetchall()
            log(f"   [listar_empresas] Fetchall concluido: {len(empresas) if empresas else 0} empresas")
            
            cursor.close()
            resultado = [dict(e) for e in empresas]
            log(f"   [listar_empresas] Conversao para dict concluida")
            
            return resultado
        
    except Exception as e:
        log(f"[listar_empresas] Erro: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return []


def suspender_empresa(empresa_id, motivo):
    """
    Suspende uma empresa (desativa)
    
    Args:
        empresa_id: ID da empresa
        motivo: Motivo da suspensi?o
    
    Returns:
        dict: {'success': True/False, 'error': msg}
    """
    return atualizar_empresa(empresa_id, {
        'ativo': False,
        'data_suspensao': datetime.now(),
        'motivo_suspensao': motivo
    })


def reativar_empresa(empresa_id):
    """
    Reativa uma empresa suspensa
    
    Args:
        empresa_id: ID da empresa
    
    Returns:
        dict: {'success': True/False, 'error': msg}
    """
    return atualizar_empresa(empresa_id, {
        'ativo': True,
        'data_suspensao': None,
        'motivo_suspensao': None
    })


def obter_estatisticas_empresa(empresa_id):
    """
    Obti?m estati?sticas de uso de uma empresa
    
    Args:
        empresa_id: ID da empresa
    
    Returns:
        dict: Estati?sticas de uso
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Usui?rios
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE empresa_id = %s", (empresa_id,))
        stats['total_usuarios'] = cursor.fetchone()[0]
        
        # Clientes
        cursor.execute("SELECT COUNT(*) FROM clientes WHERE empresa_id = %s", (empresa_id,))
        stats['total_clientes'] = cursor.fetchone()[0]
        
        # Fornecedores
        cursor.execute("SELECT COUNT(*) FROM fornecedores WHERE empresa_id = %s", (empresa_id,))
        stats['total_fornecedores'] = cursor.fetchone()[0]
        
        # Lani?amentos
        cursor.execute("SELECT COUNT(*) FROM lancamentos WHERE empresa_id = %s", (empresa_id,))
        stats['total_lancamentos'] = cursor.fetchone()[0]
        
        # Lani?amentos no mi?s atual
        cursor.execute("""
            SELECT COUNT(*) FROM lancamentos 
            WHERE empresa_id = %s 
            AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE)
            AND EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
        """, (empresa_id,))
        stats['lancamentos_mes_atual'] = cursor.fetchone()[0]
        
        return stats
        
    except Exception as e:
        print(f"? Erro ao obter estati?sticas: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_to_pool(conn)


# ============================================================================
# REGRAS DE AUTO-CONCILIAÇÃO (FUNÇÕES AUXILIARES STANDALONE)
# ============================================================================
# NOTA: Métodos principais (listar, criar, atualizar, excluir) estão
# na classe DatabaseManager. Estas são funções auxiliares standalone.


def buscar_regra_aplicavel(pool, empresa_id: int, descricao: str) -> Optional[Dict]:
    """
    Busca a regra mais específica aplicável a uma descrição de extrato
    
    Args:
        pool: Pool de conexões
        empresa_id: ID da empresa
        descricao: Descrição da transação do extrato
        
    Returns:
        Dicionário com a regra encontrada ou None
    """
    conn = None
    cursor = None
    try:
        conn = get_from_pool(pool)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM buscar_regras_aplicaveis(%s, %s)
        """, (empresa_id, descricao))
        
        regra = cursor.fetchone()
        return dict(regra) if regra else None
        
    except Exception as e:
        print(f"❌ Erro ao buscar regra aplicável: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_to_pool(conn)


def buscar_funcionario_por_cpf(pool, empresa_id: int, cpf: str) -> Optional[Dict]:
    """
    Busca funcionário da folha de pagamento pelo CPF
    
    Args:
        pool: Pool de conexões
        empresa_id: ID da empresa
        cpf: CPF do funcionário (apenas números)
        
    Returns:
        Dicionário com dados do funcionário ou None
    """
    conn = None
    cursor = None
    try:
        conn = get_from_pool(pool)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Remover qualquer formatação do CPF
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        
        cursor.execute("""
            SELECT 
                id,
                nome,
                cpf,
                cargo,
                salario,
                ativo
            FROM funcionarios
            WHERE empresa_id = %s 
              AND REPLACE(REPLACE(REPLACE(cpf, '.', ''), '-', ''), ' ', '') = %s
              AND ativo = TRUE
        """, (empresa_id, cpf_limpo))
        
        funcionario = cursor.fetchone()
        return dict(funcionario) if funcionario else None
        
    except Exception as e:
        print(f"❌ Erro ao buscar funcionário por CPF: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_to_pool(conn)


