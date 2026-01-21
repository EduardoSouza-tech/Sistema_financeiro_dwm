"""
Configuração de fixtures e setup para testes do Sistema Financeiro
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_server import app
import database_postgresql as db

# ============================================================================
# FIXTURES DE CONFIGURAÇÃO
# ============================================================================

@pytest.fixture(scope='session')
def test_app():
    """
    Cria uma instância do Flask app para testes
    """
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Desabilitar CSRF para testes
    return app


@pytest.fixture(scope='function')
def client(test_app):
    """
    Cria um cliente de teste para fazer requisições
    """
    with test_app.test_client() as client:
        yield client


@pytest.fixture(scope='function')
def authenticated_client(client):
    """
    Cliente autenticado como usuário admin
    """
    # Login
    response = client.post('/api/auth/login', json={
        'email': 'admin@sistema.com',
        'senha': 'admin123'
    })
    
    if response.status_code != 200:
        # Se não conseguir logar, criar usuário admin de teste
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios (nome, email, senha_hash, nivel_acesso, ativo, proprietario_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
            """, ('Admin Teste', 'admin@sistema.com', 
                  db.bcrypt.hashpw('admin123'.encode('utf-8'), db.bcrypt.gensalt()).decode('utf-8'),
                  'admin', True, 1))
            conn.commit()
        
        # Tentar logar novamente
        response = client.post('/api/auth/login', json={
            'email': 'admin@sistema.com',
            'senha': 'admin123'
        })
    
    yield client


# ============================================================================
# FIXTURES DE DADOS
# ============================================================================

@pytest.fixture(scope='function')
def conta_bancaria_teste():
    """
    Cria uma conta bancária de teste
    """
    conta = {
        'nome': 'Conta Teste',
        'banco': 'Banco Teste',
        'agencia': '1234',
        'numero': '567890',
        'saldo_inicial': 1000.00,
        'proprietario_id': 1
    }
    
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contas_bancarias (nome, banco, agencia, numero_conta, saldo, proprietario_id)
            VALUES (%(nome)s, %(banco)s, %(agencia)s, %(numero)s, %(saldo_inicial)s, %(proprietario_id)s)
            RETURNING id
        """, conta)
        conta['id'] = cursor.fetchone()[0]
        conn.commit()
    
    yield conta
    
    # Cleanup
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contas_bancarias WHERE id = %s", (conta['id'],))
        conn.commit()


@pytest.fixture(scope='function')
def categoria_teste():
    """
    Cria uma categoria de teste
    """
    categoria = {
        'nome': 'Categoria Teste',
        'tipo': 'RECEITA',
        'cor': '#FF5733',
        'proprietario_id': 1
    }
    
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO categorias (nome, tipo, cor, proprietario_id)
            VALUES (%(nome)s, %(tipo)s, %(cor)s, %(proprietario_id)s)
            RETURNING id
        """, categoria)
        categoria['id'] = cursor.fetchone()[0]
        conn.commit()
    
    yield categoria
    
    # Cleanup
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categorias WHERE id = %s", (categoria['id'],))
        conn.commit()


@pytest.fixture(scope='function')
def cliente_teste():
    """
    Cria um cliente de teste
    """
    cliente = {
        'nome': 'Cliente Teste',
        'email': 'cliente@teste.com',
        'telefone': '11999999999',
        'cpf_cnpj': '12345678900',
        'proprietario_id': 1
    }
    
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clientes (nome, email, telefone, cpf_cnpj, ativo, proprietario_id)
            VALUES (%(nome)s, %(email)s, %(telefone)s, %(cpf_cnpj)s, TRUE, %(proprietario_id)s)
            RETURNING id
        """, cliente)
        cliente['id'] = cursor.fetchone()[0]
        conn.commit()
    
    yield cliente
    
    # Cleanup
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = %s", (cliente['id'],))
        conn.commit()


@pytest.fixture(scope='function')
def fornecedor_teste():
    """
    Cria um fornecedor de teste
    """
    fornecedor = {
        'nome': 'Fornecedor Teste',
        'email': 'fornecedor@teste.com',
        'telefone': '11988888888',
        'cpf_cnpj': '98765432100',
        'proprietario_id': 1
    }
    
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO fornecedores (nome, email, telefone, cpf_cnpj, ativo, proprietario_id)
            VALUES (%(nome)s, %(email)s, %(telefone)s, %(cpf_cnpj)s, TRUE, %(proprietario_id)s)
            RETURNING id
        """, fornecedor)
        fornecedor['id'] = cursor.fetchone()[0]
        conn.commit()
    
    yield fornecedor
    
    # Cleanup
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fornecedores WHERE id = %s", (fornecedor['id'],))
        conn.commit()


@pytest.fixture(scope='function')
def lancamento_teste(conta_bancaria_teste, categoria_teste):
    """
    Cria um lançamento de teste
    """
    data_vencimento = (datetime.now() + timedelta(days=30)).date()
    
    lancamento = {
        'tipo': 'RECEITA',
        'categoria': categoria_teste['nome'],
        'descricao': 'Lançamento Teste',
        'valor': 500.00,
        'data_vencimento': data_vencimento.isoformat(),
        'conta': conta_bancaria_teste['nome'],
        'status': 'PENDENTE',
        'proprietario_id': 1
    }
    
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO lancamentos 
            (tipo, categoria, descricao, valor, data_vencimento, conta, status, proprietario_id)
            VALUES (%(tipo)s, %(categoria)s, %(descricao)s, %(valor)s, 
                    %(data_vencimento)s, %(conta)s, %(status)s, %(proprietario_id)s)
            RETURNING id
        """, lancamento)
        lancamento['id'] = cursor.fetchone()[0]
        conn.commit()
    
    yield lancamento
    
    # Cleanup
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lancamentos WHERE id = %s", (lancamento['id'],))
        conn.commit()


# ============================================================================
# FIXTURES DE LIMPEZA
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """
    Limpa dados de teste após cada teste
    """
    yield
    
    # Cleanup geral (caso algum teste não limpe seus dados)
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        # Limpar apenas dados de teste identificáveis
        cursor.execute("DELETE FROM lancamentos WHERE descricao LIKE '%Teste%'")
        cursor.execute("DELETE FROM clientes WHERE email LIKE '%teste.com%'")
        cursor.execute("DELETE FROM fornecedores WHERE email LIKE '%teste.com%'")
        cursor.execute("DELETE FROM categorias WHERE nome LIKE '%Teste%'")
        cursor.execute("DELETE FROM contas_bancarias WHERE nome LIKE '%Teste%'")
        conn.commit()


# ============================================================================
# FIXTURES PARA TESTES DE INTEGRAÇÃO DOS BLUEPRINTS
# ============================================================================

@pytest.fixture
def auth_headers_admin():
    """Headers com token de autenticação admin"""
    # Token fictício para testes - ajustar conforme sistema de auth
    return {
        'Authorization': 'Bearer admin_token_test',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def auth_headers_user():
    """Headers com token de usuário normal"""
    return {
        'Authorization': 'Bearer user_token_test',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def auth_headers_readonly():
    """Headers com token de usuário read-only"""
    return {
        'Authorization': 'Bearer readonly_token_test',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def sample_kit_id():
    """ID de um kit de exemplo para testes"""
    return 1


@pytest.fixture
def sample_cliente_id():
    """ID de um cliente de exemplo para testes"""
    return 1


@pytest.fixture
def sample_contrato_id():
    """ID de um contrato de exemplo para testes"""
    return 1


@pytest.fixture
def sample_sessao_id():
    """ID de uma sessão de exemplo para testes"""
    return 1


@pytest.fixture
def sample_kit_from_other_empresa():
    """ID de kit de outra empresa (para teste de multi-tenancy)"""
    return 999


@pytest.fixture
def sample_empresa_id():
    """ID da empresa de teste"""
    return 1
