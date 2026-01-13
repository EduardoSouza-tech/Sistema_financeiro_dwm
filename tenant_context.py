"""
Tenant Context Manager - Sistema Multi-Tenant SaaS
===================================================

Gerencia o contexto da empresa (tenant) atual em toda a aplicação.
Garante isolamento de dados e segurança entre empresas diferentes.

Uso:
    from tenant_context import TenantContext, tenant_required
    
    # Em uma API route:
    @app.route('/api/clientes')
    @tenant_required
    def listar_clientes():
        empresa_id = TenantContext.get_empresa_id()
        # Query automaticamente filtra por empresa_id
"""

from functools import wraps
from flask import g, request, jsonify
import threading

# Thread-local storage para isolamento
_thread_local = threading.local()


class TenantContext:
    """
    Gerencia o contexto da empresa atual na thread/request
    """
    
    @staticmethod
    def set_empresa(empresa_id, usuario_id=None):
        """
        Define a empresa atual no contexto
        
        Args:
            empresa_id: ID da empresa (tenant)
            usuario_id: ID do usuário (opcional, para auditoria)
        """
        if not empresa_id:
            raise ValueError("empresa_id não pode ser None")
        
        g.empresa_id = empresa_id
        g.usuario_id = usuario_id
        _thread_local.empresa_id = empresa_id
        _thread_local.usuario_id = usuario_id
    
    @staticmethod
    def get_empresa_id():
        """
        Obtém o ID da empresa atual
        
        Returns:
            int: ID da empresa ou None se não definido
        """
        # Tentar pegar do Flask g (request context)
        if hasattr(g, 'empresa_id'):
            return g.empresa_id
        
        # Fallback para thread local
        return getattr(_thread_local, 'empresa_id', None)
    
    @staticmethod
    def get_usuario_id():
        """
        Obtém o ID do usuário atual
        
        Returns:
            int: ID do usuário ou None
        """
        if hasattr(g, 'usuario_id'):
            return g.usuario_id
        
        return getattr(_thread_local, 'usuario_id', None)
    
    @staticmethod
    def clear():
        """
        Limpa o contexto atual
        """
        if hasattr(g, 'empresa_id'):
            delattr(g, 'empresa_id')
        if hasattr(g, 'usuario_id'):
            delattr(g, 'usuario_id')
        
        _thread_local.empresa_id = None
        _thread_local.usuario_id = None
    
    @staticmethod
    def is_set():
        """
        Verifica se o contexto está definido
        
        Returns:
            bool: True se empresa_id está definido
        """
        return TenantContext.get_empresa_id() is not None
    
    @staticmethod
    def require():
        """
        Requer que o contexto esteja definido, caso contrário lança exceção
        
        Raises:
            ValueError: Se empresa_id não está definido
        """
        if not TenantContext.is_set():
            raise ValueError("Contexto de tenant não definido. Use TenantContext.set_empresa()")
        
        return TenantContext.get_empresa_id()


def tenant_required(f):
    """
    Decorator que requer autenticação e define o contexto do tenant
    
    Uso:
        @app.route('/api/dados')
        @tenant_required
        def minha_rota():
            empresa_id = TenantContext.get_empresa_id()
            # ... sua lógica
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar se usuário está autenticado
        if not hasattr(g, 'usuario_id'):
            return jsonify({'error': 'Não autenticado'}), 401
        
        usuario_id = g.usuario_id
        
        # Buscar empresa do usuário
        try:
            from database_postgresql import get_db_connection, return_to_pool
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT empresa_id, ativo 
                FROM usuarios 
                WHERE id = %s
            """, (usuario_id,))
            
            resultado = cursor.fetchone()
            cursor.close()
            return_to_pool(conn)
            
            if not resultado:
                return jsonify({'error': 'Usuário não encontrado'}), 404
            
            empresa_id, usuario_ativo = resultado
            
            if not empresa_id:
                return jsonify({'error': 'Usuário não está associado a uma empresa'}), 403
            
            if not usuario_ativo:
                return jsonify({'error': 'Usuário inativo'}), 403
            
            # Verificar se empresa está ativa
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ativo 
                FROM empresas 
                WHERE id = %s
            """, (empresa_id,))
            
            empresa = cursor.fetchone()
            cursor.close()
            return_to_pool(conn)
            
            if not empresa:
                return jsonify({'error': 'Empresa não encontrada'}), 404
            
            if not empresa[0]:
                return jsonify({'error': 'Empresa inativa ou suspensa'}), 403
            
            # Definir contexto
            TenantContext.set_empresa(empresa_id, usuario_id)
            
            # Executar função
            return f(*args, **kwargs)
            
        except Exception as e:
            print(f"❌ Erro ao definir tenant context: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Erro interno ao validar acesso'}), 500
    
    return decorated_function


def add_tenant_filter(query, table_alias=''):
    """
    Adiciona filtro de empresa_id automaticamente em queries
    
    Args:
        query: Query SQL base
        table_alias: Alias da tabela (opcional)
    
    Returns:
        str: Query com filtro de tenant
    
    Exemplo:
        query = "SELECT * FROM clientes"
        query = add_tenant_filter(query)
        # Resultado: "SELECT * FROM clientes WHERE empresa_id = %s"
    """
    empresa_id = TenantContext.get_empresa_id()
    
    if not empresa_id:
        raise ValueError("Tenant context não definido. Use @tenant_required ou TenantContext.set_empresa()")
    
    prefix = f"{table_alias}." if table_alias else ""
    
    # Adicionar WHERE ou AND conforme necessário
    if 'WHERE' in query.upper():
        query += f" AND {prefix}empresa_id = {empresa_id}"
    else:
        query += f" WHERE {prefix}empresa_id = {empresa_id}"
    
    return query


def validate_tenant_access(empresa_id_solicitada):
    """
    Valida se o tenant atual tem acesso ao empresa_id solicitado
    
    Args:
        empresa_id_solicitada: ID da empresa sendo acessada
    
    Returns:
        bool: True se tem acesso, False caso contrário
    
    Raises:
        ValueError: Se contexto não está definido
    """
    empresa_id_atual = TenantContext.require()
    
    # Usuário só pode acessar dados da própria empresa
    if empresa_id_atual != empresa_id_solicitada:
        print(f"⚠️  Tentativa de acesso cross-tenant bloqueada: {empresa_id_atual} → {empresa_id_solicitada}")
        return False
    
    return True


class TenantQueryBuilder:
    """
    Builder para queries com filtro automático de tenant
    """
    
    def __init__(self, table):
        self.table = table
        self.empresa_id = TenantContext.require()
        self.wheres = [f"empresa_id = {self.empresa_id}"]
        self.selects = ["*"]
        self.orders = []
        self.limit_value = None
        self.offset_value = None
    
    def select(self, *campos):
        """Define campos a selecionar"""
        self.selects = list(campos)
        return self
    
    def where(self, condicao):
        """Adiciona condição WHERE"""
        self.wheres.append(condicao)
        return self
    
    def order_by(self, campo, direcao='ASC'):
        """Adiciona ordenação"""
        self.orders.append(f"{campo} {direcao}")
        return self
    
    def limit(self, valor):
        """Define LIMIT"""
        self.limit_value = valor
        return self
    
    def offset(self, valor):
        """Define OFFSET"""
        self.offset_value = valor
        return self
    
    def build(self):
        """Constrói a query SQL"""
        query = f"SELECT {', '.join(self.selects)} FROM {self.table}"
        
        if self.wheres:
            query += f" WHERE {' AND '.join(self.wheres)}"
        
        if self.orders:
            query += f" ORDER BY {', '.join(self.orders)}"
        
        if self.limit_value:
            query += f" LIMIT {self.limit_value}"
        
        if self.offset_value:
            query += f" OFFSET {self.offset_value}"
        
        return query


# ============================================================
# EXEMPLOS DE USO
# ============================================================

"""
# Exemplo 1: Em uma rota Flask
@app.route('/api/clientes', methods=['GET'])
@tenant_required  # Automaticamente define TenantContext
def listar_clientes():
    empresa_id = TenantContext.get_empresa_id()
    
    cursor.execute('''
        SELECT * FROM clientes 
        WHERE empresa_id = %s
    ''', (empresa_id,))
    
    return jsonify(clientes)


# Exemplo 2: Usando QueryBuilder
@app.route('/api/produtos', methods=['GET'])
@tenant_required
def listar_produtos():
    query = TenantQueryBuilder('produtos') \
        .select('id', 'nome', 'preco') \
        .where("ativo = true") \
        .order_by('nome') \
        .limit(50) \
        .build()
    
    cursor.execute(query)
    return jsonify(cursor.fetchall())


# Exemplo 3: Validação manual de acesso
@app.route('/api/cliente/<int:cliente_id>')
@tenant_required
def obter_cliente(cliente_id):
    cursor.execute("SELECT empresa_id FROM clientes WHERE id = %s", (cliente_id,))
    cliente = cursor.fetchone()
    
    if not validate_tenant_access(cliente['empresa_id']):
        return jsonify({'error': 'Acesso negado'}), 403
    
    return jsonify(cliente)


# Exemplo 4: Operações de insert/update
@app.route('/api/clientes', methods=['POST'])
@tenant_required
def criar_cliente():
    empresa_id = TenantContext.get_empresa_id()
    dados = request.json
    
    cursor.execute('''
        INSERT INTO clientes (nome, email, empresa_id)
        VALUES (%s, %s, %s)
    ''', (dados['nome'], dados['email'], empresa_id))
    
    return jsonify({'success': True})
"""
