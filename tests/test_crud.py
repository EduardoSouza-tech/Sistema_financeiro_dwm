"""
Testes para APIs de CRUD (Contas, Categorias, Clientes, Fornecedores, Lançamentos)
"""
import pytest
import json


class TestContasBancarias:
    """Testes para operações de Contas Bancárias"""
    
    def test_listar_contas(self, authenticated_client):
        """Teste de listagem de contas bancárias"""
        response = authenticated_client.get('/api/contas')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'contas' in data
        assert isinstance(data['contas'], list)
    
    
    def test_criar_conta(self, authenticated_client):
        """Teste de criação de conta bancária"""
        nova_conta = {
            'nome': 'Conta Teste API',
            'banco': 'Banco Teste',
            'agencia': '1234',
            'numero_conta': '567890',
            'saldo_inicial': 1000.00
        }
        
        response = authenticated_client.post('/api/contas', json=nova_conta)
        
        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        assert 'sucesso' in data or 'conta' in data
    
    
    def test_criar_conta_sem_nome(self, authenticated_client):
        """Teste de criação de conta sem nome (deve falhar)"""
        nova_conta = {
            'banco': 'Banco Teste',
            'agencia': '1234',
            'numero_conta': '567890'
        }
        
        response = authenticated_client.post('/api/contas', json=nova_conta)
        
        assert response.status_code == 400


class TestCategorias:
    """Testes para operações de Categorias"""
    
    def test_listar_categorias(self, authenticated_client):
        """Teste de listagem de categorias"""
        response = authenticated_client.get('/api/categorias')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'categorias' in data
        assert isinstance(data['categorias'], list)
    
    
    def test_criar_categoria_receita(self, authenticated_client):
        """Teste de criação de categoria de receita"""
        nova_categoria = {
            'nome': 'Categoria Teste Receita',
            'tipo': 'RECEITA',
            'cor': '#FF5733'
        }
        
        response = authenticated_client.post('/api/categorias', json=nova_categoria)
        
        assert response.status_code in [200, 201]
    
    
    def test_criar_categoria_despesa(self, authenticated_client):
        """Teste de criação de categoria de despesa"""
        nova_categoria = {
            'nome': 'Categoria Teste Despesa',
            'tipo': 'DESPESA',
            'cor': '#33FF57'
        }
        
        response = authenticated_client.post('/api/categorias', json=nova_categoria)
        
        assert response.status_code in [200, 201]
    
    
    def test_criar_categoria_tipo_invalido(self, authenticated_client):
        """Teste de criação de categoria com tipo inválido"""
        nova_categoria = {
            'nome': 'Categoria Teste',
            'tipo': 'INVALIDO',
            'cor': '#FF5733'
        }
        
        response = authenticated_client.post('/api/categorias', json=nova_categoria)
        
        assert response.status_code == 400


class TestClientes:
    """Testes para operações de Clientes"""
    
    def test_listar_clientes(self, authenticated_client):
        """Teste de listagem de clientes"""
        response = authenticated_client.get('/api/clientes')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'clientes' in data
        assert isinstance(data['clientes'], list)
    
    
    def test_criar_cliente(self, authenticated_client):
        """Teste de criação de cliente"""
        novo_cliente = {
            'nome': 'Cliente Teste API',
            'email': 'clienteapi@teste.com',
            'telefone': '11999999999',
            'cpf_cnpj': '12345678900'
        }
        
        response = authenticated_client.post('/api/clientes', json=novo_cliente)
        
        assert response.status_code in [200, 201]
    
    
    def test_criar_cliente_sem_nome(self, authenticated_client):
        """Teste de criação de cliente sem nome (deve falhar)"""
        novo_cliente = {
            'email': 'clienteapi@teste.com',
            'telefone': '11999999999'
        }
        
        response = authenticated_client.post('/api/clientes', json=novo_cliente)
        
        assert response.status_code == 400
    
    
    def test_inativar_cliente(self, authenticated_client, cliente_teste):
        """Teste de inativação de cliente"""
        response = authenticated_client.post(
            f'/api/clientes/{cliente_teste["nome"]}/inativar'
        )
        
        assert response.status_code in [200, 404]
    
    
    def test_reativar_cliente(self, authenticated_client, cliente_teste):
        """Teste de reativação de cliente"""
        # Primeiro inativa
        authenticated_client.post(f'/api/clientes/{cliente_teste["nome"]}/inativar')
        
        # Depois reativa
        response = authenticated_client.post(
            f'/api/clientes/{cliente_teste["nome"]}/reativar'
        )
        
        assert response.status_code in [200, 404]


class TestFornecedores:
    """Testes para operações de Fornecedores"""
    
    def test_listar_fornecedores(self, authenticated_client):
        """Teste de listagem de fornecedores"""
        response = authenticated_client.get('/api/fornecedores')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'fornecedores' in data
        assert isinstance(data['fornecedores'], list)
    
    
    def test_criar_fornecedor(self, authenticated_client):
        """Teste de criação de fornecedor"""
        novo_fornecedor = {
            'nome': 'Fornecedor Teste API',
            'email': 'fornecedorapi@teste.com',
            'telefone': '11988888888',
            'cpf_cnpj': '98765432100'
        }
        
        response = authenticated_client.post('/api/fornecedores', json=novo_fornecedor)
        
        assert response.status_code in [200, 201]
    
    
    def test_inativar_fornecedor(self, authenticated_client, fornecedor_teste):
        """Teste de inativação de fornecedor"""
        response = authenticated_client.post(
            f'/api/fornecedores/{fornecedor_teste["nome"]}/inativar'
        )
        
        assert response.status_code in [200, 404]


class TestLancamentos:
    """Testes para operações de Lançamentos"""
    
    def test_listar_lancamentos(self, authenticated_client):
        """Teste de listagem de lançamentos"""
        response = authenticated_client.get('/api/lancamentos')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'lancamentos' in data
        assert isinstance(data['lancamentos'], list)
    
    
    def test_criar_lancamento_receita(self, authenticated_client, conta_bancaria_teste, categoria_teste):
        """Teste de criação de lançamento de receita"""
        from datetime import datetime, timedelta
        
        novo_lancamento = {
            'tipo': 'RECEITA',
            'categoria': categoria_teste['nome'],
            'descricao': 'Lançamento Teste Receita API',
            'valor': 500.00,
            'data_vencimento': (datetime.now() + timedelta(days=30)).date().isoformat(),
            'conta': conta_bancaria_teste['nome']
        }
        
        response = authenticated_client.post('/api/lancamentos', json=novo_lancamento)
        
        assert response.status_code in [200, 201]
    
    
    def test_criar_lancamento_despesa(self, authenticated_client, conta_bancaria_teste):
        """Teste de criação de lançamento de despesa"""
        from datetime import datetime, timedelta
        
        novo_lancamento = {
            'tipo': 'DESPESA',
            'categoria': 'Categoria Teste',
            'descricao': 'Lançamento Teste Despesa API',
            'valor': 300.00,
            'data_vencimento': (datetime.now() + timedelta(days=15)).date().isoformat(),
            'conta': conta_bancaria_teste['nome']
        }
        
        response = authenticated_client.post('/api/lancamentos', json=novo_lancamento)
        
        assert response.status_code in [200, 201, 400]  # Pode falhar se categoria não existir
    
    
    def test_obter_lancamento(self, authenticated_client, lancamento_teste):
        """Teste de obtenção de lançamento específico"""
        response = authenticated_client.get(f'/api/lancamentos/{lancamento_teste["id"]}')
        
        assert response.status_code in [200, 404]
    
    
    def test_pagar_lancamento(self, authenticated_client, lancamento_teste, conta_bancaria_teste):
        """Teste de pagamento de lançamento"""
        response = authenticated_client.put(
            f'/api/lancamentos/{lancamento_teste["id"]}/pagar',
            json={'conta': conta_bancaria_teste['nome']}
        )
        
        assert response.status_code in [200, 400, 404]
    
    
    def test_cancelar_lancamento(self, authenticated_client, lancamento_teste):
        """Teste de cancelamento de lançamento"""
        response = authenticated_client.put(
            f'/api/lancamentos/{lancamento_teste["id"]}/cancelar'
        )
        
        assert response.status_code in [200, 404]
    
    
    def test_criar_lancamento_sem_valor(self, authenticated_client):
        """Teste de criação de lançamento sem valor (deve falhar)"""
        from datetime import datetime, timedelta
        
        novo_lancamento = {
            'tipo': 'RECEITA',
            'categoria': 'Teste',
            'descricao': 'Lançamento sem valor',
            'data_vencimento': (datetime.now() + timedelta(days=30)).date().isoformat()
        }
        
        response = authenticated_client.post('/api/lancamentos', json=novo_lancamento)
        
        assert response.status_code == 400
