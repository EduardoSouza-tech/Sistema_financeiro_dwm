"""
Módulo de gerenciamento do banco de dados PostgreSQL
Otimizado com pool de conexões para máxima performance
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
from contextlib import contextmanager


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
                 cor: str = "#000000", icone: str = "folder"):
        self.id = id
        self.nome = nome
        self.tipo = tipo
        self.descricao = descricao
        self.subcategorias = subcategorias if subcategorias is not None else []
        self.cor = cor
        self.icone = icone
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nome': self.nome,
            'tipo': self.tipo.value if isinstance(self.tipo, TipoLancamento) else self.tipo,
            'descricao': self.descricao,
            'subcategorias': self.subcategorias,
            'cor': self.cor,
            'icone': self.icone
        }


class ContaBancaria:
    """Conta bancaria"""
    def __init__(self, nome: str, banco: str, agencia: str, conta: str, 
                 saldo_inicial: float = 0.0, id: Optional[int] = None, 
                 tipo_conta: str = "corrente", moeda: str = "BRL",
                 ativa: bool = True, proprietario_id: Optional[int] = None,
                 data_criacao: Optional[datetime] = None):
        self.id = id
        self.nome = nome
        self.banco = banco
        self.agencia = agencia
        self.conta = conta
        self.saldo_inicial = saldo_inicial
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
# CONFIGURAÇÃO E POOL DE CONEXÕES
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
    # Novas funções do menu Operacional
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
    'deletar_sessao_equipe',
    'adicionar_tipo_sessao',
    'listar_tipos_sessao',
    'atualizar_tipo_sessao',
    'deletar_tipo_sessao'
]

# ============================================================================
# CONFIGURAÇÃO OTIMIZADA DO POSTGRESQL COM POOL DE CONEXÕES
# ============================================================================

def _get_postgresql_config():
    """Configuração do PostgreSQL com prioridade para DATABASE_URL"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        return {'dsn': database_url}
    
    # Fallback para variáveis individuais (desenvolvimento local)
    host = os.getenv('PGHOST', 'localhost')
    if not host or host == 'localhost':
        raise ValueError(
            "❌ ERRO: DATABASE_URL não configurado. "
            "Configure a variável de ambiente DATABASE_URL para conectar ao PostgreSQL."
        )
    
    return {
        'host': host,
        'port': int(os.getenv('PGPORT', '5432')),
        'user': os.getenv('PGUSER', 'postgres'),
        'password': os.getenv('PGPASSWORD', ''),
        'database': os.getenv('PGDATABASE', 'sistema_financeiro')
    }

POSTGRESQL_CONFIG = _get_postgresql_config()

# Pool de conexões global para reutilização eficiente
_connection_pool = None
_database_initialized = False  # Flag para controlar inicialização única

def _get_connection_pool():
    """Obtém ou cria o pool de conexões"""
    global _connection_pool
    
    if _connection_pool is None:
        try:
            if 'dsn' in POSTGRESQL_CONFIG:
                _connection_pool = pool.ThreadedConnectionPool(
                    minconn=2,
                    maxconn=20,
                    dsn=POSTGRESQL_CONFIG['dsn'],
                    cursor_factory=RealDictCursor
                )
            else:
                _connection_pool = pool.ThreadedConnectionPool(
                    minconn=2,
                    maxconn=20,
                    cursor_factory=RealDictCursor,
                    **POSTGRESQL_CONFIG
                )
            print("✅ Pool de conexões PostgreSQL criado (2-20 conexões)")
        except Exception as e:
            print(f"❌ Erro ao criar pool de conexões: {e}")
            raise
    
    return _connection_pool

@contextmanager
def get_db_connection():
    """Context manager para obter conexão do pool"""
    pool_obj = _get_connection_pool()
    conn = pool_obj.getconn()
    try:
        conn.autocommit = True
        yield conn
    finally:
        pool_obj.putconn(conn)


def return_to_pool(conn):
    """Devolve uma conexão ao pool manualmente"""
    try:
        pool_obj = _get_connection_pool()
        pool_obj.putconn(conn)
    except Exception as e:
        print(f"⚠️ Erro ao devolver conexão ao pool: {e}")


# ============================================================================
# FUNÇÕES AUXILIARES OTIMIZADAS
# ============================================================================

def execute_query(query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = True):
    """
    Executa query otimizada usando pool de conexões
    
    Args:
        query: Query SQL
        params: Parâmetros da query
        fetch_one: Retornar apenas um resultado
        fetch_all: Retornar todos os resultados
    
    Returns:
        Resultado da query ou None
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.rowcount


def execute_many(query: str, params_list: list):
    """Executa múltiplas queries em batch para performance"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount


# Cache simples para permissões (evita consultas repetidas)
_permissions_cache = {}
_cache_timeout = 300  # 5 minutos

def get_cached_permissions(usuario_id: int):
    """Obtém permissões do usuário com cache"""
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
    """Limpa cache de permissões"""
    if usuario_id:
        _permissions_cache.pop(usuario_id, None)
    else:
        _permissions_cache.clear()


class DatabaseManager:
    """Gerenciador otimizado do banco de dados PostgreSQL com pool de conexões"""
    
    def __init__(self, config: Dict = None):
        global _database_initialized
        
        self.config = config or POSTGRESQL_CONFIG
        # Inicializar pool
        _get_connection_pool()
        
        # Criar tabelas e executar migrações APENAS UMA VEZ
        if not _database_initialized:
            print("🔄 Inicializando banco de dados (primeira vez)...")
            self.criar_tabelas()
            _database_initialized = True
            print("✅ Banco de dados inicializado!")
    
    def get_connection(self):
        """
        Obtém uma conexão do pool
        IMPORTANTE: SEMPRE devolva ao pool com return_to_pool(conn) quando terminar!
        Ou use o context manager get_db_connection() preferencialmente.
        """
        try:
            pool_obj = _get_connection_pool()
            conn = pool_obj.getconn()
            conn.autocommit = True
            return conn
        except Error as e:
            print(f"❌ Erro ao obter conexão do pool: {e}")
            raise
    
    def criar_tabelas(self):
        """Cria as tabelas no banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de contas bancárias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contas_bancarias (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL,
                banco VARCHAR(255) NOT NULL,
                agencia VARCHAR(50) NOT NULL,
                conta VARCHAR(50) NOT NULL,
                saldo_inicial DECIMAL(15,2) NOT NULL,
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
                subcategorias TEXT,
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
        
        # ===== TABELAS DE AUTENTICAÇÃO E AUTORIZAÇÃO =====
        
        # Tabela de usuários
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
        
        # Tabela de permissões (funcionalidades do sistema)
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
        
        # Tabela de relação usuário-permissões
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
        
        # Tabela de sessões de login (para controle de autenticação)
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
        
        # Tabela de lançamentos
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
        
        # Adicionar colunas juros e desconto se não existirem (migration)
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
            print("✅ Migração: Colunas juros e desconto adicionadas/verificadas")
        except Exception as e:
            print(f"⚠️  Aviso na migração de colunas: {e}")
        
        # Sincronizar sequências de auto-incremento com valores máximos atuais
        try:
            cursor.execute("""
                DO $$ 
                DECLARE
                    max_id INTEGER;
                BEGIN
                    -- Sincronizar sequência de categorias
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM categorias;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''categorias_id_seq'', ' || max_id || ')';
                    END IF;
                    
                    -- Sincronizar sequência de contas_bancarias
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM contas_bancarias;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''contas_bancarias_id_seq'', ' || max_id || ')';
                    END IF;
                    
                    -- Sincronizar sequência de clientes
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM clientes;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''clientes_id_seq'', ' || max_id || ')';
                    END IF;
                    
                    -- Sincronizar sequência de fornecedores
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM fornecedores;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''fornecedores_id_seq'', ' || max_id || ')';
                    END IF;
                    
                    -- Sincronizar sequência de lancamentos
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM lancamentos;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''lancamentos_id_seq'', ' || max_id || ')';
                    END IF;
                END $$;
            """)
            print("✅ Migração: Sequências de ID sincronizadas com sucesso")
        except Exception as e:
            print(f"⚠️  Aviso na sincronização de sequências: {e}")
        
        # Tabela de contratos
        # Primeiro, dropar tabela antiga se existir com estrutura incompatível
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
            print(f"⚠️  Aviso ao verificar tabela contratos: {e}")
        
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
        
        # Tabela de sessões
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
        
        # Adicionar coluna contrato_id se não existir
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
        
        # Migração: Adicionar colunas que podem faltar em sessoes
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar titulo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='titulo'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN titulo VARCHAR(255) NOT NULL DEFAULT 'Sessão';
                END IF;
                
                -- Adicionar data_sessao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='data_sessao'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN data_sessao DATE NOT NULL DEFAULT CURRENT_DATE;
                END IF;
                
                -- Adicionar duracao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='duracao'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN duracao INTEGER;
                END IF;
                
                -- Adicionar cliente_id se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='cliente_id'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN cliente_id INTEGER REFERENCES clientes(id);
                END IF;
                
                -- Adicionar valor se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='valor'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN valor DECIMAL(15,2);
                END IF;
                
                -- Adicionar observacoes se não existir
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
        
        # Tabela de tipos de sessão
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
        
        # Migração: Adicionar colunas que podem faltar em tipos_sessao
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar descricao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='descricao'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN descricao TEXT;
                END IF;
                
                -- Adicionar duracao_padrao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='duracao_padrao'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN duracao_padrao INTEGER;
                END IF;
                
                -- Adicionar valor_padrao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='valor_padrao'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN valor_padrao DECIMAL(15,2);
                END IF;
                
                -- Adicionar ativo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='ativo'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN ativo BOOLEAN DEFAULT TRUE;
                END IF;
                
                -- Adicionar created_at se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='created_at'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
                
                -- Adicionar updated_at se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='updated_at'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Migração: Adicionar colunas que podem faltar em produtos
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar descricao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='descricao'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN descricao TEXT;
                END IF;
                
                -- Adicionar unidade se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='unidade'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN unidade VARCHAR(20) DEFAULT 'UN';
                END IF;
                
                -- Adicionar quantidade_minima se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='quantidade_minima'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN quantidade_minima DECIMAL(15,3) DEFAULT 0;
                END IF;
                
                -- Adicionar ativo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='ativo'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN ativo BOOLEAN DEFAULT TRUE;
                END IF;
                
                -- Adicionar data_criacao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='data_criacao'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Migração: Adicionar colunas que podem faltar em kits
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar descricao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='kits' AND column_name='descricao'
                ) THEN
                    ALTER TABLE kits ADD COLUMN descricao TEXT;
                END IF;
                
                -- Adicionar ativo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='kits' AND column_name='ativo'
                ) THEN
                    ALTER TABLE kits ADD COLUMN ativo BOOLEAN DEFAULT TRUE;
                END IF;
                
                -- Adicionar data_criacao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='kits' AND column_name='data_criacao'
                ) THEN
                    ALTER TABLE kits ADD COLUMN data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Migração: Adicionar colunas que podem faltar em tags
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar data_criacao se não existir  
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tags' AND column_name='data_criacao'
                ) THEN
                    ALTER TABLE tags ADD COLUMN data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Migração: Adicionar colunas que podem faltar em templates_equipe
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar conteudo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='conteudo'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN conteudo TEXT;
                END IF;
                
                -- Adicionar tipo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='tipo'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN tipo VARCHAR(50);
                END IF;
                
                -- Adicionar descricao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='descricao'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN descricao TEXT;
                END IF;
                
                -- Adicionar ativo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='ativo'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN ativo BOOLEAN DEFAULT TRUE;
                END IF;
                
                -- Adicionar data_criacao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='data_criacao'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Tabela de comissões
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
        
        # Migração: adicionar campos faltantes em comissoes
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
        
        # Migração: tornar campos nullable em comissoes
        cursor.execute("""
            DO $$
            BEGIN
                ALTER TABLE comissoes ALTER COLUMN descricao DROP NOT NULL;
                ALTER TABLE comissoes ALTER COLUMN valor DROP NOT NULL;
            EXCEPTION WHEN OTHERS THEN
                NULL;
            END $$;
        """)
        
        # Tabela de equipe de sessão
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
        
        # ===== INICIALIZAÇÃO DE DADOS PADRÃO =====
        
        # Inserir permissões padrão
        permissoes_padrao = [
            # Navegação
            ('dashboard', 'Dashboard', 'Visualizar dashboard principal', 'navegacao'),
            ('relatorios_view', 'Relatórios', 'Acessar menu de relatórios', 'navegacao'),
            ('cadastros_view', 'Cadastros', 'Acessar menu de cadastros', 'navegacao'),
            ('operacional_view', 'Operacional', 'Acessar menu operacional', 'navegacao'),
            
            # Financeiro
            ('lancamentos_view', 'Ver Lançamentos', 'Visualizar lançamentos financeiros', 'financeiro'),
            ('lancamentos_create', 'Criar Lançamentos', 'Criar novos lançamentos', 'financeiro'),
            ('lancamentos_edit', 'Editar Lançamentos', 'Editar lançamentos existentes', 'financeiro'),
            ('lancamentos_delete', 'Excluir Lançamentos', 'Excluir lançamentos', 'financeiro'),
            
            # Cadastros
            ('clientes_view', 'Ver Clientes', 'Visualizar clientes', 'cadastros'),
            ('clientes_create', 'Criar Clientes', 'Criar novos clientes', 'cadastros'),
            ('clientes_edit', 'Editar Clientes', 'Editar clientes existentes', 'cadastros'),
            ('clientes_delete', 'Excluir Clientes', 'Excluir clientes', 'cadastros'),
            ('fornecedores_view', 'Ver Fornecedores', 'Visualizar fornecedores', 'cadastros'),
            ('fornecedores_create', 'Criar Fornecedores', 'Criar novos fornecedores', 'cadastros'),
            ('fornecedores_edit', 'Editar Fornecedores', 'Editar fornecedores existentes', 'cadastros'),
            ('fornecedores_delete', 'Excluir Fornecedores', 'Excluir fornecedores', 'cadastros'),
            
            # Operacional
            ('contratos_view', 'Ver Contratos', 'Visualizar contratos', 'operacional'),
            ('contratos_create', 'Criar Contratos', 'Criar novos contratos', 'operacional'),
            ('contratos_edit', 'Editar Contratos', 'Editar contratos existentes', 'operacional'),
            ('contratos_delete', 'Excluir Contratos', 'Excluir contratos', 'operacional'),
            ('sessoes_view', 'Ver Sessões', 'Visualizar sessões', 'operacional'),
            ('sessoes_create', 'Criar Sessões', 'Criar novas sessões', 'operacional'),
            ('sessoes_edit', 'Editar Sessões', 'Editar sessões existentes', 'operacional'),
            ('sessoes_delete', 'Excluir Sessões', 'Excluir sessões', 'operacional'),
            ('agenda_view', 'Ver Agenda', 'Visualizar agenda', 'operacional'),
            ('agenda_create', 'Criar Eventos', 'Criar eventos na agenda', 'operacional'),
            ('agenda_edit', 'Editar Eventos', 'Editar eventos da agenda', 'operacional'),
            ('agenda_delete', 'Excluir Eventos', 'Excluir eventos da agenda', 'operacional'),
            
            # Relatórios
            ('exportar_pdf', 'Exportar PDF', 'Exportar dados em PDF', 'relatorios'),
            ('exportar_excel', 'Exportar Excel', 'Exportar dados em Excel', 'relatorios'),
            
            # Sistema
            ('configuracoes', 'Configurações', 'Acessar configurações', 'sistema'),
            ('usuarios_admin', 'Gerenciar Usuários', 'Gerenciar usuários e permissões (apenas admin)', 'sistema')
        ]
        
        for codigo, nome, descricao, categoria in permissoes_padrao:
            cursor.execute("""
                INSERT INTO permissoes (codigo, nome, descricao, categoria, ativo)
                VALUES (%s, %s, %s, %s, TRUE)
                ON CONFLICT (codigo) DO NOTHING
            """, (codigo, nome, descricao, categoria))
        
        # Criar usuário admin padrão se não existir
        cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE tipo = 'admin'")
        admin_count = cursor.fetchone()['count']
        
        if admin_count == 0:
            import hashlib
            # Senha padrão: "admin123" (deve ser alterada no primeiro login)
            senha_padrao = "admin123"
            password_hash = hashlib.sha256(senha_padrao.encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, tipo, nome_completo, email, ativo)
                VALUES ('admin', %s, 'admin', 'Administrador do Sistema', 'admin@sistema.com', TRUE)
                RETURNING id
            """, (password_hash,))
            
            admin_id = cursor.fetchone()['id']
            
            # Conceder todas as permissões ao admin
            cursor.execute("""
                INSERT INTO usuario_permissoes (usuario_id, permissao_id, concedido_por)
                SELECT %s, id, %s FROM permissoes
            """, (admin_id, admin_id))
            
            print("✅ Usuário admin criado com sucesso!")
            print("   Username: admin")
            print("   Senha: admin123")
        
        # ================================================================
        # MIGRAÇÃO: Multi-Tenancy - Adicionar proprietario_id
        # ================================================================
        try:
            print("🔄 Verificando migração Multi-Tenancy...")
            
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
                    print(f"   ⚠️  Tabela '{tabela}' não existe, pulando...")
                    continue
                
                # Adicionar coluna se não existir
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
                
                # Criar índice
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {idx_name} 
                    ON {tabela}(proprietario_id);
                """)
            
            print("✅ Migração Multi-Tenancy: Colunas proprietario_id adicionadas/verificadas")
            print("   - Tabelas processadas: clientes, fornecedores, lancamentos, contas_bancarias, categorias")
            
        except Exception as e:
            print(f"⚠️  Aviso na migração Multi-Tenancy: {e}")
            import traceback
            traceback.print_exc()
        
        print("   ⚠️  ALTERE A SENHA DO ADMIN NO PRIMEIRO LOGIN!")
        
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
    
    def adicionar_conta(self, conta: ContaBancaria, proprietario_id: int = None) -> int:
        """Adiciona uma nova conta bancária"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO contas_bancarias 
            (nome, banco, agencia, conta, saldo_inicial, ativa, data_criacao, proprietario_id)
            VALUES (%s, %s, %s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP), %s)
            RETURNING id
        """, (
            conta.nome,
            conta.banco,
            conta.agencia,
            conta.conta,
            float(conta.saldo_inicial),
            conta.ativa,
            conta.data_criacao,
            proprietario_id
        ))
        
        conta_id = cursor.fetchone()['id']
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return conta_id
    
    def listar_contas(self, filtro_cliente_id: int = None) -> List[ContaBancaria]:
        """Lista todas as contas bancárias com suporte a multi-tenancy"""
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
                ativa=row['ativa'],
                data_criacao=row['data_criacao']
            )
            contas.append(conta)
        
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return contas
    
    def atualizar_conta(self, nome_antigo: str, conta: ContaBancaria) -> bool:
        """Atualiza uma conta bancária"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Se o nome mudou, verificar se o novo nome já existe
        if nome_antigo != conta.nome:
            cursor.execute("SELECT COUNT(*) as count FROM contas_bancarias WHERE nome = %s AND nome != %s", 
                         (conta.nome, nome_antigo))
            if cursor.fetchone()['count'] > 0:
                cursor.close()
                return_to_pool(conn)  # Devolver ao pool
                raise ValueError("Já existe uma conta com este nome")
        
        cursor.execute("""
            UPDATE contas_bancarias
            SET nome = %s, banco = %s, agencia = %s, conta = %s, saldo_inicial = %s
            WHERE nome = %s
        """, (conta.nome, conta.banco, conta.agencia, conta.conta,
              float(conta.saldo_inicial), nome_antigo))
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return success
    
    def excluir_conta(self, nome: str) -> bool:
        """Exclui uma conta bancária pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM contas_bancarias WHERE nome = %s", (nome,))
        sucesso = cursor.rowcount > 0
        
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def adicionar_categoria(self, categoria: Categoria) -> int:
        """Adiciona uma nova categoria"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        subcategorias_json = json.dumps(categoria.subcategorias) if categoria.subcategorias else None
        
        cursor.execute("""
            INSERT INTO categorias 
            (nome, tipo, subcategorias, cor, icone, descricao)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            categoria.nome,
            categoria.tipo.value,
            subcategorias_json,
            categoria.cor,
            categoria.icone,
            categoria.descricao
        ))
        
        categoria_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return categoria_id
    
    def listar_categorias(self, tipo: Optional[TipoLancamento] = None) -> List[Categoria]:
        """Lista todas as categorias, opcionalmente filtradas por tipo"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if tipo:
            cursor.execute(
                "SELECT * FROM categorias WHERE tipo = %s ORDER BY nome",
                (tipo.value,)
            )
        else:
            cursor.execute("SELECT * FROM categorias ORDER BY nome")
        
        rows = cursor.fetchall()
        
        categorias = []
        for row in rows:
            subcategorias = json.loads(row['subcategorias']) if row['subcategorias'] else []  # type: ignore
            
            categoria = Categoria(
                id=row['id'],
                nome=row['nome'],
                tipo=TipoLancamento(row['tipo']),
                subcategorias=subcategorias,
                cor=row['cor'],
                icone=row['icone'],
                descricao=row['descricao']
            )
            categorias.append(categoria)
        
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
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
    
    def atualizar_categoria(self, categoria: Categoria) -> bool:
        """Atualiza uma categoria pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        subcategorias_json = json.dumps(categoria.subcategorias) if categoria.subcategorias else None
        
        # Normalizar nome
        nome_normalizado = categoria.nome.strip().upper()
        
        cursor.execute("""
            UPDATE categorias 
            SET tipo = %s, subcategorias = %s
            WHERE UPPER(TRIM(nome)) = %s
        """, (
            categoria.tipo.value,
            subcategorias_json,
            nome_normalizado
        ))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def atualizar_nome_categoria(self, nome_antigo: str, nome_novo: str) -> bool:
        """Atualiza o nome de uma categoria e suas referências"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Atualizar nome da categoria
            cursor.execute(
                "UPDATE categorias SET nome = %s WHERE nome = %s",
                (nome_novo, nome_antigo)
            )
            
            # Atualizar referências nos lançamentos
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
                         endereco: str = None, proprietario_id: int = None) -> int:
        """Adiciona um novo cliente (aceita dict ou parâmetros individuais)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Aceitar dict ou parâmetros individuais
        if isinstance(cliente_data, dict):
            nome = cliente_data.get('nome')
            cpf_cnpj = cliente_data.get('cpf', cliente_data.get('cpf_cnpj'))
            email = cliente_data.get('email')
            telefone = cliente_data.get('telefone')
            endereco = cliente_data.get('endereco')
            proprietario_id = cliente_data.get('proprietario_id', proprietario_id)
        else:
            nome = cliente_data
        
        cursor.execute("""
            INSERT INTO clientes (nome, cpf_cnpj, email, telefone, endereco, proprietario_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (nome, cpf_cnpj, email, telefone, endereco, proprietario_id))
        
        cliente_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return cliente_id
    
    def listar_clientes(self, ativos: bool = True, filtro_cliente_id: int = None) -> List[Dict]:
        """Lista todos os clientes com suporte a multi-tenancy"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Construir query com filtro de multi-tenancy
        if filtro_cliente_id is not None:
            # Cliente específico: ver apenas seus próprios clientes
            if ativos:
                cursor.execute(
                    "SELECT * FROM clientes WHERE ativo = TRUE AND proprietario_id = %s ORDER BY nome",
                    (filtro_cliente_id,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM clientes WHERE proprietario_id = %s ORDER BY nome",
                    (filtro_cliente_id,)
                )
        else:
            # Admin: ver todos os clientes
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
        cursor.execute("""
            UPDATE clientes 
            SET nome = %s, cpf_cnpj = %s, email = %s, 
                telefone = %s, endereco = %s, updated_at = CURRENT_TIMESTAMP
            WHERE UPPER(TRIM(nome)) = %s
        """, (
            dados.get('nome'),
            dados.get('cpf', dados.get('cpf_cnpj')),
            dados.get('email'),
            dados.get('telefone'),
            dados.get('endereco'),
            nome_normalizado
        ))
        
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
        return (sucesso, "Cliente inativado com sucesso" if sucesso else "Cliente não encontrado")
    
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
    
    def adicionar_fornecedor(self, fornecedor_data, cpf_cnpj: str = None,
                           email: str = None, telefone: str = None,
                           endereco: str = None, proprietario_id: int = None) -> int:
        """Adiciona um novo fornecedor (aceita dict ou parâmetros individuais)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Aceitar dict ou parâmetros individuais
        if isinstance(fornecedor_data, dict):
            nome = fornecedor_data.get('nome')
            cpf_cnpj = fornecedor_data.get('cnpj', fornecedor_data.get('cpf_cnpj'))
            email = fornecedor_data.get('email')
            telefone = fornecedor_data.get('telefone')
            endereco = fornecedor_data.get('endereco')
            proprietario_id = fornecedor_data.get('proprietario_id', proprietario_id)
        else:
            nome = fornecedor_data
        
        cursor.execute("""
            INSERT INTO fornecedores (nome, cpf_cnpj, email, telefone, endereco, proprietario_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (nome, cpf_cnpj, email, telefone, endereco, proprietario_id))
        
        fornecedor_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return fornecedor_id
    
    def listar_fornecedores(self, ativos: bool = True, filtro_cliente_id: int = None) -> List[Dict]:
        """Lista todos os fornecedores com suporte a multi-tenancy"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Construir query com filtro de multi-tenancy
        if filtro_cliente_id is not None:
            # Cliente específico: ver apenas seus próprios fornecedores
            if ativos:
                cursor.execute(
                    "SELECT * FROM fornecedores WHERE ativo = TRUE AND proprietario_id = %s ORDER BY nome",
                    (filtro_cliente_id,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM fornecedores WHERE proprietario_id = %s ORDER BY nome",
                    (filtro_cliente_id,)
                )
        else:
            # Admin: ver todos os fornecedores
            if ativos:
                cursor.execute("SELECT * FROM fornecedores WHERE ativo = TRUE ORDER BY nome")
            else:
                cursor.execute("SELECT * FROM fornecedores ORDER BY nome")
        rows = cursor.fetchall()
        
        fornecedores = [dict(row) for row in rows]
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return fornecedores
    
    def atualizar_fornecedor(self, nome_antigo: str, dados: Dict) -> bool:
        """Atualiza os dados de um fornecedor pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome_antigo.upper().strip()
        cursor.execute("""
            UPDATE fornecedores 
            SET nome = %s, cpf_cnpj = %s, email = %s, 
                telefone = %s, endereco = %s, updated_at = CURRENT_TIMESTAMP
            WHERE UPPER(TRIM(nome)) = %s
        """, (
            dados.get('nome'),
            dados.get('cnpj', dados.get('cpf_cnpj')),
            dados.get('email'),
            dados.get('telefone'),
            dados.get('endereco'),
            nome_normalizado
        ))
        
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
        return (sucesso, "Fornecedor inativado com sucesso" if sucesso else "Fornecedor não encontrado")
    
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
    
    def adicionar_lancamento(self, lancamento: Lancamento, proprietario_id: int = None) -> int:
        """Adiciona um novo lançamento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO lancamentos 
            (tipo, descricao, valor, data_vencimento, data_pagamento,
             categoria, subcategoria, conta_bancaria, cliente_fornecedor, pessoa,
             status, observacoes, anexo, recorrente, frequencia_recorrencia, dia_vencimento, proprietario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            proprietario_id
        ))
        
        lancamento_id = cursor.fetchone()['id']
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return lancamento_id
    
    def listar_lancamentos(self, filtros: Dict[str, Any] = None, filtro_cliente_id: int = None) -> List[Lancamento]:
        """Lista lançamentos com filtros opcionais e suporte a multi-tenancy"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM lancamentos WHERE 1=1"
        params = []
        
        # Filtro de multi-tenancy
        if filtro_cliente_id is not None:
            query += " AND proprietario_id = %s"
            params.append(filtro_cliente_id)
        
        if filtros:
            if 'tipo' in filtros:
                query += " AND tipo = %s"
                params.append(filtros['tipo'])
            if 'status' in filtros:
                query += " AND status = %s"
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
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
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
                print(f"❌ Erro ao processar lançamento ID {row.get('id', 'unknown')}: {e}")
                continue
        
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return lancamentos
    
    def obter_lancamento(self, lancamento_id: int) -> Optional[Lancamento]:
        """Obtém um lançamento específico por ID"""
        print(f"\n🔍 obter_lancamento() chamado com ID: {lancamento_id}")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM lancamentos WHERE id = %s"
        print(f"📝 Query: {query}")
        print(f"📝 Params: ({lancamento_id},)")
        
        try:
            cursor.execute(query, (lancamento_id,))
            row = cursor.fetchone()
            print(f"✅ Row encontrada: {row is not None}")
        except Exception as e:
            print(f"❌ ERRO ao executar query: {e}")
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
        
        print(f"📊 Construindo Lancamento com:")
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
        
        print(f"✅ Lancamento criado com sucesso\n")
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return lancamento
    
    def excluir_lancamento(self, lancamento_id: int) -> bool:
        """Exclui um lançamento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM lancamentos WHERE id = %s", (lancamento_id,))
        sucesso = cursor.rowcount > 0
        
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def atualizar_lancamento(self, lancamento: Lancamento) -> bool:
        """Atualiza um lançamento existente"""
        print(f"\n🔍 DatabaseManager.atualizar_lancamento() chamada:")
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
        
        print(f"📝 Query: {query}")
        print(f"📝 Params: {params}")
        
        cursor.execute(query, params)
        sucesso = cursor.rowcount > 0
        
        print(f"✅ Linhas afetadas: {cursor.rowcount}, Sucesso: {sucesso}\n")
        
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def pagar_lancamento(self, lancamento_id: int, conta: str = '', data_pagamento: date = None,
                        juros: float = 0, desconto: float = 0, observacoes: str = '',
                        valor_pago: Optional[Decimal] = None) -> bool:
        """Marca um lançamento como pago"""
        print(f"\n🔍 DatabaseManager.pagar_lancamento() chamada:")
        print(f"   - lancamento_id: {lancamento_id} (tipo: {type(lancamento_id)})")
        print(f"   - conta: {conta} (tipo: {type(conta)})")
        print(f"   - data_pagamento: {data_pagamento} (tipo: {type(data_pagamento)})")
        print(f"   - juros: {juros} (tipo: {type(juros)})")
        print(f"   - desconto: {desconto} (tipo: {type(desconto)})")
        print(f"   - observacoes: {observacoes} (tipo: {type(observacoes)})")
        print(f"   - valor_pago: {valor_pago} (tipo: {type(valor_pago)})")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Se não passar data_pagamento, usar a data atual
        if not data_pagamento:
            data_pagamento = date.today()
            print(f"⚠️  Data não fornecida, usando hoje: {data_pagamento}")
        
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
            print(f"📝 Query COM valor_pago:")
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
            print(f"📝 Query SEM valor_pago:")
            print(f"   SQL: {query}")
            print(f"   Params: {params}")
            cursor.execute(query, params)
        
        sucesso = cursor.rowcount > 0
        print(f"✅ Linhas afetadas: {cursor.rowcount}, Sucesso: {sucesso}")
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool
        return sucesso
    
    def cancelar_lancamento(self, lancamento_id: int) -> bool:
        """Cancela um lançamento"""
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
    
    def migrar_dados_json(self, json_path: str):
        """Migra dados de um arquivo JSON para o banco"""
        if not os.path.exists(json_path):
            print(f"Arquivo {json_path} não encontrado")
            return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Migrar contas
        for conta_data in dados.get('contas', []):
            conta = ContaBancaria(**conta_data)
            try:
                self.adicionar_conta(conta)
            except Exception as e:
                print(f"Erro ao migrar conta {conta.nome}: {e}")
        
        # Migrar categorias
        for cat_data in dados.get('categorias', []):
            categoria = Categoria(**cat_data)
            try:
                self.adicionar_categoria(categoria)
            except Exception as e:
                print(f"Erro ao migrar categoria {categoria.nome}: {e}")
        
        # Migrar lançamentos
        for lanc_data in dados.get('lancamentos', []):
            lancamento = Lancamento(**lanc_data)
            try:
                self.adicionar_lancamento(lancamento)
            except Exception as e:
                print(f"Erro ao migrar lançamento: {e}")
        
        print("Migração concluída!")
    
    # === MÉTODOS DO MENU OPERACIONAL ===
    
    def gerar_proximo_numero_contrato(self) -> str:
        """Gera o próximo número de contrato"""
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
        """Adiciona uma nova sessão"""
        return adicionar_sessao(dados)
    
    def listar_sessoes(self) -> List[Dict]:
        """Lista todas as sessões"""
        return listar_sessoes()
    
    def atualizar_sessao(self, sessao_id: int, dados: Dict) -> bool:
        """Atualiza uma sessão"""
        return atualizar_sessao(sessao_id, dados)
    
    def deletar_sessao(self, sessao_id: int) -> bool:
        """Deleta uma sessão"""
        return deletar_sessao(sessao_id)
    
    def adicionar_comissao(self, dados: Dict) -> int:
        """Adiciona uma nova comissão"""
        return adicionar_comissao(dados)
    
    def listar_comissoes(self) -> List[Dict]:
        """Lista todas as comissões"""
        return listar_comissoes()
    
    def atualizar_comissao(self, comissao_id: int, dados: Dict) -> bool:
        """Atualiza uma comissão"""
        return atualizar_comissao(comissao_id, dados)
    
    def deletar_comissao(self, comissao_id: int) -> bool:
        """Deleta uma comissão"""
        return deletar_comissao(comissao_id)
    
    def adicionar_sessao_equipe(self, dados: Dict) -> int:
        """Adiciona um membro à equipe de sessão"""
        return adicionar_sessao_equipe(dados)
    
    def listar_sessao_equipe(self, sessao_id: int = None) -> List[Dict]:
        """Lista membros da equipe de sessão"""
        return listar_sessao_equipe(sessao_id)
    
    def atualizar_sessao_equipe(self, membro_id: int, dados: Dict) -> bool:
        """Atualiza um membro da equipe"""
        return atualizar_sessao_equipe(membro_id, dados)
    
    def deletar_sessao_equipe(self, membro_id: int) -> bool:
        """Deleta um membro da equipe"""
        return deletar_sessao_equipe(membro_id)
    
    def adicionar_tipo_sessao(self, dados: Dict) -> int:
        """Adiciona um novo tipo de sessão"""
        return adicionar_tipo_sessao(dados)
    
    def listar_tipos_sessao(self) -> List[Dict]:
        """Lista todos os tipos de sessão"""
        return listar_tipos_sessao()
    
    def atualizar_tipo_sessao(self, tipo_id: int, dados: Dict) -> bool:
        """Atualiza um tipo de sessão"""
        return atualizar_tipo_sessao(tipo_id, dados)
    
    def deletar_tipo_sessao(self, tipo_id: int) -> bool:
        """Deleta um tipo de sessão"""
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


# Funções standalone para compatibilidade
def criar_tabelas():
    db = DatabaseManager()
    db.criar_tabelas()

def get_connection():
    db = DatabaseManager()
    return db.get_connection()

def adicionar_conta(conta: ContaBancaria) -> int:
    db = DatabaseManager()
    return db.adicionar_conta(conta)

def listar_contas() -> List[ContaBancaria]:
    db = DatabaseManager()
    return db.listar_contas()

def atualizar_conta(nome_antigo: str, conta: ContaBancaria) -> bool:
    db = DatabaseManager()
    return db.atualizar_conta(nome_antigo, conta)

def excluir_conta(nome: str) -> bool:
    db = DatabaseManager()
    return db.excluir_conta(nome)

def adicionar_categoria(categoria: Categoria) -> int:
    db = DatabaseManager()
    return db.adicionar_categoria(categoria)

def listar_categorias(tipo: Optional[TipoLancamento] = None) -> List[Categoria]:
    db = DatabaseManager()
    return db.listar_categorias(tipo)

def excluir_categoria(nome: str) -> bool:
    db = DatabaseManager()
    return db.excluir_categoria(nome)

def atualizar_categoria(categoria: Categoria) -> bool:
    db = DatabaseManager()
    return db.atualizar_categoria(categoria)

def atualizar_nome_categoria(nome_antigo: str, nome_novo: str) -> bool:
    db = DatabaseManager()
    return db.atualizar_nome_categoria(nome_antigo, nome_novo)

def adicionar_cliente(cliente_data, cpf_cnpj: str = None, email: str = None,
                     telefone: str = None, endereco: str = None) -> int:
    db = DatabaseManager()
    return db.adicionar_cliente(cliente_data, cpf_cnpj, email, telefone, endereco)

def listar_clientes(ativos: bool = True) -> List[Dict]:
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

def adicionar_lancamento(lancamento: Lancamento) -> int:
    db = DatabaseManager()
    return db.adicionar_lancamento(lancamento)

def listar_lancamentos(filtros: Dict[str, Any] = None, filtro_cliente_id: int = None) -> List[Lancamento]:
    """Lista lançamentos com suporte a filtros e multi-tenancy"""
    db = DatabaseManager()
    return db.listar_lancamentos(filtros, filtro_cliente_id)

def obter_lancamento(lancamento_id: int) -> Optional[Lancamento]:
    db = DatabaseManager()
    return db.obter_lancamento(lancamento_id)

def excluir_lancamento(lancamento_id: int) -> bool:
    db = DatabaseManager()
    return db.excluir_lancamento(lancamento_id)

def pagar_lancamento(lancamento_id: int, conta: str = '', data_pagamento: date = None,
                    juros: float = 0, desconto: float = 0, observacoes: str = '',
                    valor_pago: Optional[Decimal] = None) -> bool:
    print(f"\n🔍 pagar_lancamento() wrapper chamada:")
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


# ==================== FUNÇÕES CRUD - CONTRATOS ====================
def gerar_proximo_numero_contrato() -> str:
    """Gera o próximo número de contrato no formato CONT-YYYY-NNNN"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        ano_atual = datetime.now().year
        
        # Buscar o último número de contrato do ano atual
        cursor.execute("""
            SELECT numero FROM contratos 
            WHERE numero LIKE %s
            ORDER BY numero DESC 
            LIMIT 1
        """, (f'CONT-{ano_atual}-%',))
        
        resultado = cursor.fetchone()
        
        if resultado:
            # Extrair o número sequencial do último contrato
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
        print(f"❌ Erro ao gerar número do contrato: {e}")
        # Em caso de erro, retornar um número padrão
        ano_atual = datetime.now().year
        return f'CONT-{ano_atual}-0001'

def adicionar_contrato(dados: Dict) -> int:
    """Adiciona um novo contrato"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO contratos (numero, cliente_id, descricao, valor, data_inicio, data_fim, status, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        dados.get('numero'),
        dados.get('cliente_id'),
        dados.get('descricao'),
        dados.get('valor'),
        dados.get('data_inicio'),
        dados.get('data_fim'),
        dados.get('status', 'ativo'),
        dados.get('observacoes')
    ))
    
    contrato_id = cursor.fetchone()['id']
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return contrato_id

def listar_contratos() -> List[Dict]:
    """Lista todos os contratos"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, cl.nome as cliente_nome
        FROM contratos c
        LEFT JOIN clientes cl ON c.cliente_id = cl.id
        ORDER BY c.created_at DESC
    """)
    
    contratos = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return contratos

def atualizar_contrato(contrato_id: int, dados: Dict) -> bool:
    """Atualiza um contrato existente"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE contratos
        SET numero = %s, cliente_id = %s, descricao = %s, valor = %s,
            data_inicio = %s, data_fim = %s, status = %s, observacoes = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('numero'),
        dados.get('cliente_id'),
        dados.get('descricao'),
        dados.get('valor'),
        dados.get('data_inicio'),
        dados.get('data_fim'),
        dados.get('status'),
        dados.get('observacoes'),
        contrato_id
    ))
    
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


# ==================== FUNÇÕES CRUD - AGENDA ====================
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


# ==================== FUNÇÕES CRUD - PRODUTOS ====================
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


# ==================== FUNÇÕES CRUD - KITS ====================
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


# ==================== FUNÇÕES CRUD - TAGS ====================
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


# ==================== FUNÇÕES CRUD - TEMPLATES DE EQUIPE ====================
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


# ==================== FUNÇÕES CRUD - SESSÕES ====================
def adicionar_sessao(dados: Dict) -> int:
    """Adiciona uma nova sessão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sessoes (titulo, data_sessao, duracao, contrato_id, cliente_id, valor, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        dados.get('titulo'),
        dados.get('data_sessao'),
        dados.get('duracao'),
        dados.get('contrato_id'),
        dados.get('cliente_id'),
        dados.get('valor'),
        dados.get('observacoes')
    ))
    
    sessao_id = cursor.fetchone()['id']
    
    # Adicionar membros da equipe se fornecidos
    if 'equipe' in dados and dados['equipe']:
        for membro in dados['equipe']:
            cursor.execute("""
                INSERT INTO sessao_equipe (sessao_id, membro_nome, funcao)
                VALUES (%s, %s, %s)
            """, (sessao_id, membro['nome'], membro.get('funcao')))
    
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sessao_id

def listar_sessoes() -> List[Dict]:
    """Lista todas as sessões"""
    import datetime
    import decimal
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.*, c.nome as cliente_nome, ct.numero as contrato_numero
        FROM sessoes s
        LEFT JOIN clientes c ON s.cliente_id = c.id
        LEFT JOIN contratos ct ON s.contrato_id = ct.id
        ORDER BY s.data_sessao DESC
    """)
    sessoes = []
    for row in cursor.fetchall():
        sessao = {}
        for key, value in dict(row).items():
            # Converter tipos não-serializáveis para JSON
            if isinstance(value, (datetime.time, datetime.datetime, datetime.date)):
                sessao[key] = value.isoformat()
            elif isinstance(value, decimal.Decimal):
                sessao[key] = float(value)
            else:
                sessao[key] = value
        sessoes.append(sessao)
    
    # Buscar equipe de cada sessão
    for sessao in sessoes:
        cursor.execute("""
            SELECT * FROM sessao_equipe WHERE sessao_id = %s
        """, (sessao['id'],))
        sessao['equipe'] = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sessoes

def atualizar_sessao(sessao_id: int, dados: Dict) -> bool:
    """Atualiza uma sessão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE sessoes
        SET titulo = %s, data_sessao = %s, duracao = %s, contrato_id = %s, cliente_id = %s,
            valor = %s, observacoes = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('titulo'),
        dados.get('data_sessao'),
        dados.get('duracao'),
        dados.get('contrato_id'),
        dados.get('cliente_id'),
        dados.get('valor'),
        dados.get('observacoes'),
        sessao_id
    ))
    
    # Atualizar equipe se fornecida
    if 'equipe' in dados:
        cursor.execute("DELETE FROM sessao_equipe WHERE sessao_id = %s", (sessao_id,))
        for membro in dados['equipe']:
            cursor.execute("""
                INSERT INTO sessao_equipe (sessao_id, membro_nome, funcao)
                VALUES (%s, %s, %s)
            """, (sessao_id, membro['nome'], membro.get('funcao')))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso

def deletar_sessao(sessao_id: int) -> bool:
    """Deleta uma sessão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM sessoes WHERE id = %s", (sessao_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso


# ==================== FUNÇÕES CRUD - COMISSÕES ====================
def adicionar_comissao(dados: Dict) -> int:
    """Adiciona uma nova comissão"""
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
    
    cursor.execute("""
        INSERT INTO comissoes (contrato_id, cliente_id, tipo, descricao, valor, percentual)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        contrato_id,
        cliente_id,
        dados.get('tipo', 'percentual'),
        dados.get('descricao'),
        dados.get('valor', 0),
        dados.get('percentual', 0)
    ))
    
    comissao_id = cursor.fetchone()['id']
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return comissao_id

def listar_comissoes() -> List[Dict]:
    """Lista todas as comissões com informações de contrato e cliente"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            com.*,
            ct.numero as contrato_numero,
            ct.valor as contrato_valor,
            cl.nome as cliente_nome
        FROM comissoes com
        LEFT JOIN contratos ct ON com.contrato_id = ct.id
        LEFT JOIN clientes cl ON com.cliente_id = cl.id
        ORDER BY com.created_at DESC
    """)
    
    comissoes = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return comissoes

def atualizar_comissao(comissao_id: int, dados: Dict) -> bool:
    """Atualiza uma comissão"""
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
    
    cursor.execute("""
        UPDATE comissoes
        SET contrato_id = %s, cliente_id = %s, tipo = %s, 
            descricao = %s, valor = %s, percentual = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        contrato_id,
        cliente_id,
        dados.get('tipo', 'percentual'),
        dados.get('descricao'),
        dados.get('valor', 0),
        dados.get('percentual', 0),
        comissao_id
    ))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso

def deletar_comissao(comissao_id: int) -> bool:
    """Deleta uma comissão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM comissoes WHERE id = %s", (comissao_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso


# ==================== FUNÇÕES CRUD - SESSÃO EQUIPE ====================
def adicionar_sessao_equipe(dados: Dict) -> int:
    """Adiciona um membro à equipe de uma sessão"""
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
    """Lista membros da equipe de sessão"""
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
            membro['sessao_info'] = f"Sessão #{membro.get('sessao_id', '?')}"
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

# ==================== TIPOS DE SESSÃO ====================

def adicionar_tipo_sessao(dados: Dict) -> int:
    """Adiciona um novo tipo de sessão"""
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
    """Lista todos os tipos de sessão"""
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
    """Atualiza um tipo de sessão"""
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
    """Deleta um tipo de sessão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tipos_sessao WHERE id = %s", (tipo_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    return_to_pool(conn)  # Devolver ao pool
    return sucesso


# ==================== FUNÇÕES DE AUTENTICAÇÃO E USUÁRIOS ====================

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
        
        usuario_retorno = {
            'id': sessao['usuario_id'],
            'username': sessao['username'],
            'tipo': sessao['tipo'],
            'nome_completo': sessao['nome_completo'],
            'email': sessao['email'],
            'cliente_id': sessao['cliente_id']
        }
        
        return usuario_retorno
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def invalidar_sessao(token: str) -> bool:
    """Invalida uma sessão (logout)"""
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
        print(f"Erro ao invalidar sessão: {e}")
        return False
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def listar_usuarios(apenas_ativos: bool = True) -> List[Dict]:
    """Lista todos os usuários do sistema"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        filtro = "WHERE u.ativo = TRUE" if apenas_ativos else ""
        cursor.execute(f"""
            SELECT u.id, u.username, u.tipo, u.nome_completo, u.email, 
                   u.cliente_id, u.ativo, u.created_at,
                   c.nome as cliente_nome,
                   (SELECT MAX(sl.criado_em) FROM sessoes_login sl WHERE sl.usuario_id = u.id) as ultima_sessao
            FROM usuarios u
            LEFT JOIN clientes c ON u.cliente_id = c.id
            {filtro}
            ORDER BY u.created_at DESC
        """)
        rows = cursor.fetchall()
        
        # Converter RealDictRow para dict padrão
        usuarios = [dict(row) for row in rows]
        
        print(f"   📊 listar_usuarios() retornando {len(usuarios)} usuários")
        return usuarios
    except Exception as e:
        print(f"   ❌ Erro em listar_usuarios(): {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def obter_usuario(usuario_id: int) -> Optional[Dict]:
    """Obtém dados de um usuário específico"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT u.id, u.username, u.tipo, u.nome_completo, u.email, 
                   u.cliente_id, u.ativo, u.created_at,
                   c.nome as cliente_nome
            FROM usuarios u
            LEFT JOIN clientes c ON u.cliente_id = c.id
            WHERE u.id = %s
        """, (usuario_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def atualizar_usuario(usuario_id: int, dados: Dict) -> bool:
    """Atualiza dados de um usuário"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        campos = []
        valores = []
        
        if 'username' in dados:
            campos.append("username = %s")
            valores.append(dados['username'])
        if 'nome_completo' in dados:
            campos.append("nome_completo = %s")
            valores.append(dados['nome_completo'])
        if 'nome' in dados:  # Aceita também 'nome'
            campos.append("nome_completo = %s")
            valores.append(dados['nome'])
        if 'email' in dados:
            campos.append("email = %s")
            valores.append(dados['email'])
        if 'tipo' in dados:
            campos.append("tipo = %s")
            valores.append(dados['tipo'])
        if 'cliente_id' in dados:
            campos.append("cliente_id = %s")
            valores.append(dados['cliente_id'])
        if 'ativo' in dados:
            campos.append("ativo = %s")
            valores.append(dados['ativo'])
        if 'password' in dados and dados['password']:  # Só atualiza se senha não vazia
            import hashlib
            password_hash = hashlib.sha256(dados['password'].encode()).hexdigest()
            campos.append("password_hash = %s")
            valores.append(password_hash)
        
        if not campos:
            return False
        
        valores.append(usuario_id)
        query = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = %s"
        cursor.execute(query, valores)
        affected = cursor.rowcount
        return affected > 0
    except Exception as e:
        print(f"❌ Erro ao atualizar usuário: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def deletar_usuario(usuario_id: int) -> bool:
    """Deleta um usuário (não permite deletar admin principal ID=1)"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se não é o admin principal (ID = 1)
        if usuario_id == 1:
            print("❌ Não é possível deletar o administrador principal (ID=1)")
            return False
        
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        affected = cursor.rowcount
        
        if affected > 0:
            print(f"✅ Usuário {usuario_id} deletado com sucesso")
        else:
            print(f"⚠️ Usuário {usuario_id} não encontrado")
        
        return affected > 0
    except Exception as e:
        print(f"❌ Erro ao deletar usuário: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def listar_permissoes(categoria: Optional[str] = None) -> List[Dict]:
    """Lista todas as permissões do sistema"""
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
    """Obtém lista de códigos de permissão de um usuário"""
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
    """Concede uma permissão a um usuário"""
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
        print(f"Erro ao conceder permissão: {e}")
        return False
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def revogar_permissao(usuario_id: int, permissao_codigo: str) -> bool:
    """Revoga uma permissão de um usuário"""
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
        print(f"Erro ao revogar permissão: {e}")
        return False
    finally:
        cursor.close()
        return_to_pool(conn)  # Devolver ao pool

def sincronizar_permissoes_usuario(usuario_id: int, codigos_permissoes: List[str], concedido_por: int) -> bool:
    """Sincroniza as permissões de um usuário (remove antigas e adiciona novas)"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Remover todas as permissões atuais
        cursor.execute("DELETE FROM usuario_permissoes WHERE usuario_id = %s", (usuario_id,))
        print(f"🔄 Removidas permissões antigas do usuário {usuario_id}")
        
        # Adicionar novas permissões
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
        
        print(f"✅ {permissoes_adicionadas} permissões sincronizadas para usuário {usuario_id}")
        return True
    except Exception as e:
        print(f"❌ Erro ao sincronizar permissões: {e}")
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


