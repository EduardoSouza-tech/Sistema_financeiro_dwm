"""
DATABASE MANAGER - Multi-Database Architecture
Gerencia conexões separadas por empresa
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os
from cryptography.fernet import Fernet
import json

# =====================================================
# CONFIGURAÇÃO DO BANCO ADMIN (Controle Central)
# =====================================================
ADMIN_DB_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': int(os.getenv('PGPORT', '5432')),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', ''),
    'database': os.getenv('PGDATABASE_ADMIN', os.getenv('PGDATABASE', 'sistema_financeiro'))
}

# Chave de criptografia para senhas de banco
# Em produção, usar variável de ambiente
ENCRYPTION_KEY = os.getenv('DB_ENCRYPTION_KEY', Fernet.generate_key())
cipher = Fernet(ENCRYPTION_KEY)

# =====================================================
# POOLS DE CONEXÃO
# =====================================================
# Pool para banco admin (sempre ativo)
admin_pool = None

# Cache de pools por empresa {empresa_id: pool}
empresa_pools = {}

def initialize_admin_pool():
    """Inicializa pool de conexões para banco admin"""
    global admin_pool
    try:
        admin_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            **ADMIN_DB_CONFIG
        )
        print(f"✅ Pool admin inicializado: {ADMIN_DB_CONFIG['database']}")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar pool admin: {e}")
        return False

@contextmanager
def get_admin_connection():
    """
    Obter conexão do pool admin (context manager)
    
    Uso:
        with get_admin_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios")
    """
    global admin_pool
    
    if admin_pool is None:
        initialize_admin_pool()
    
    conn = None
    try:
        conn = admin_pool.getconn()
        yield conn
    finally:
        if conn:
            admin_pool.putconn(conn)

def get_empresa_db_config(empresa_id):
    """
    Buscar configuração de banco da empresa no banco admin
    
    Args:
        empresa_id: ID da empresa
    
    Returns:
        dict com configuração ou None
    """
    try:
        with get_admin_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    db_host, db_port, db_name, 
                    db_user, db_password_encrypted, 
                    db_ready
                FROM empresas 
                WHERE id = %s AND db_ready = TRUE
            """, (empresa_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if not result:
                print(f"⚠️ Configuração de banco não encontrada para empresa {empresa_id}")
                return None
            
            # Descriptografar senha
            password = cipher.decrypt(result['db_password_encrypted'].encode()).decode()
            
            return {
                'host': result['db_host'],
                'port': result['db_port'],
                'database': result['db_name'],
                'user': result['db_user'],
                'password': password
            }
    except Exception as e:
        print(f"❌ Erro ao buscar config da empresa {empresa_id}: {e}")
        return None

def initialize_empresa_pool(empresa_id):
    """
    Inicializa pool de conexões para uma empresa
    
    Args:
        empresa_id: ID da empresa
    
    Returns:
        bool: True se sucesso
    """
    try:
        config = get_empresa_db_config(empresa_id)
        if not config:
            return False
        
        pool_obj = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            **config
        )
        
        empresa_pools[empresa_id] = pool_obj
        print(f"✅ Pool empresa {empresa_id} inicializado: {config['database']}")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar pool empresa {empresa_id}: {e}")
        return False

@contextmanager
def get_empresa_connection(empresa_id):
    """
    Obter conexão do pool da empresa (context manager)
    
    Args:
        empresa_id: ID da empresa
    
    Uso:
        with get_empresa_connection(18) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lancamentos")
    """
    # Verificar se pool já existe
    if empresa_id not in empresa_pools:
        if not initialize_empresa_pool(empresa_id):
            raise Exception(f"Não foi possível conectar ao banco da empresa {empresa_id}")
    
    pool_obj = empresa_pools[empresa_id]
    conn = None
    try:
        conn = pool_obj.getconn()
        yield conn
    finally:
        if conn:
            pool_obj.putconn(conn)

# =====================================================
# CRIAÇÃO E MIGRAÇÃO DE BANCOS
# =====================================================

def create_empresa_database(empresa_id, razao_social, config=None):
    """
    Criar novo banco de dados para empresa
    
    Args:
        empresa_id: ID da empresa
        razao_social: Nome da empresa
        config: Configuração customizada (opcional)
    
    Returns:
        dict com resultado
    """
    try:
        # Usar configuração padrão se não fornecida
        if not config:
            db_name = f"empresa_{empresa_id}"
            db_user = f"user_empresa_{empresa_id}"
            db_password = Fernet.generate_key().decode()[:32]  # Senha aleatória
            
            config = {
                'host': ADMIN_DB_CONFIG['host'],
                'port': ADMIN_DB_CONFIG['port'],
                'database': db_name,
                'user': db_user,
                'password': db_password
            }
        
        # Conectar ao postgres (database padrão) para criar novo database
        postgres_config = ADMIN_DB_CONFIG.copy()
        postgres_config['database'] = 'postgres'
        
        conn = psycopg2.connect(**postgres_config)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Criar database
        print(f"📦 Criando database: {config['database']}")
        cursor.execute(f"CREATE DATABASE {config['database']}")
        
        # Criar usuário
        print(f"👤 Criando usuário: {config['user']}")
        cursor.execute(f"""
            CREATE USER {config['user']} 
            WITH PASSWORD '{config['password']}'
        """)
        
        # Conceder permissões
        print(f"🔐 Concedendo permissões...")
        cursor.execute(f"""
            GRANT ALL PRIVILEGES ON DATABASE {config['database']} 
            TO {config['user']}
        """)
        
        cursor.close()
        conn.close()
        
        # Aplicar schema no novo banco
        print(f"📋 Aplicando schema...")
        apply_empresa_schema(config)
        
        # Salvar configuração no banco admin
        password_encrypted = cipher.encrypt(config['password'].encode()).decode()
        
        with get_admin_connection() as admin_conn:
            admin_cursor = admin_conn.cursor()
            admin_cursor.execute("""
                UPDATE empresas SET
                    db_host = %s,
                    db_port = %s,
                    db_name = %s,
                    db_user = %s,
                    db_password_encrypted = %s,
                    db_ready = TRUE
                WHERE id = %s
            """, (
                config['host'],
                config['port'],
                config['database'],
                config['user'],
                password_encrypted,
                empresa_id
            ))
            admin_conn.commit()
            admin_cursor.close()
        
        print(f"✅ Banco da empresa {empresa_id} criado com sucesso!")
        return {
            'success': True,
            'database': config['database'],
            'user': config['user']
        }
        
    except Exception as e:
        print(f"❌ Erro ao criar banco da empresa {empresa_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def apply_empresa_schema(db_config):
    """
    Aplicar schema completo no banco da empresa
    
    Args:
        db_config: Configuração do banco
    """
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Ler schema do arquivo
        schema_file = 'schema_empresa.sql'
        
        if os.path.exists(schema_file):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            cursor.execute(schema_sql)
            conn.commit()
            print(f"✅ Schema aplicado em {db_config['database']}")
        else:
            print(f"⚠️ Arquivo schema_empresa.sql não encontrado")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao aplicar schema: {e}")
        raise

# =====================================================
# MIGRAÇÃO DE DADOS EXISTENTES
# =====================================================

def migrate_existing_data(empresa_id):
    """
    Migrar dados existentes do banco único para banco da empresa
    
    Args:
        empresa_id: ID da empresa
    """
    try:
        print(f"🔄 Migrando dados da empresa {empresa_id}...")
        
        # Lista de tabelas a migrar (sem empresa_id nas novas tabelas)
        tables = [
            'categorias', 'subcategorias', 'contas', 'lancamentos',
            'clientes', 'fornecedores', 'contratos', 'sessoes_fotografia',
            'equipamentos', 'kits_equipamentos', 'funcionarios',
            'folha_pagamento', 'eventos'
        ]
        
        with get_admin_connection() as source_conn:
            with get_empresa_connection(empresa_id) as dest_conn:
                source_cursor = source_conn.cursor(cursor_factory=RealDictCursor)
                dest_cursor = dest_conn.cursor()
                
                for table in tables:
                    print(f"  📋 Migrando tabela: {table}")
                    
                    # Buscar dados da empresa no banco antigo
                    source_cursor.execute(f"""
                        SELECT * FROM {table} 
                        WHERE empresa_id = %s
                    """, (empresa_id,))
                    
                    rows = source_cursor.fetchall()
                    print(f"     → {len(rows)} registros encontrados")
                    
                    if rows:
                        # Remover empresa_id dos dados (não existe mais no novo schema)
                        columns = [col for col in rows[0].keys() if col != 'empresa_id']
                        
                        # Inserir no banco novo
                        for row in rows:
                            values = [row[col] for col in columns]
                            placeholders = ', '.join(['%s'] * len(columns))
                            cols_str = ', '.join(columns)
                            
                            dest_cursor.execute(f"""
                                INSERT INTO {table} ({cols_str})
                                VALUES ({placeholders})
                            """, values)
                        
                        dest_conn.commit()
                        print(f"     ✅ {len(rows)} registros migrados")
                
                source_cursor.close()
                dest_cursor.close()
        
        print(f"✅ Migração da empresa {empresa_id} concluída!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na migração da empresa {empresa_id}: {e}")
        return False

# =====================================================
# INICIALIZAÇÃO
# =====================================================

# Inicializar pool admin ao importar módulo
initialize_admin_pool()

print("""
╔═══════════════════════════════════════════════════════════╗
║  🏗️  DATABASE MANAGER - Multi-Database Architecture     ║
║                                                           ║
║  ✅ Pool Admin inicializado                              ║
║  📦 Pools de Empresa: sob demanda                        ║
╚═══════════════════════════════════════════════════════════╝
""")
