# 🧪 GUIA DE TESTES

## 📋 Visão Geral

O sistema possui uma suite completa de testes automatizados usando **pytest**.

## 🚀 Instalação

```bash
# Instalar dependências de teste
pip install pytest pytest-flask pytest-cov
```

## ▶️ Executando Testes

### Todos os testes

```bash
pytest tests/
```

### Testes específicos

```bash
# Apenas testes de autenticação
pytest tests/test_auth.py

# Apenas testes de CRUD
pytest tests/test_crud.py

# Apenas testes de relatórios
pytest tests/test_relatorios.py
```

### Com cobertura de código

```bash
# Gerar relatório de cobertura
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Abrir relatório HTML
# O relatório será gerado em htmlcov/index.html
```

### Modo verbose (detalhado)

```bash
pytest tests/ -v
```

### Apenas testes que falharam anteriormente

```bash
pytest tests/ --lf
```

## 📁 Estrutura de Testes

```
tests/
├── __init__.py
├── conftest.py              # Fixtures compartilhadas
├── test_auth.py             # Testes de autenticação
├── test_crud.py             # Testes de CRUD (Contas, Categorias, etc)
└── test_relatorios.py       # Testes de relatórios
```

## 🔧 Fixtures Disponíveis

### Fixtures de Configuração

- `test_app` - Instância do Flask app para testes
- `client` - Cliente HTTP para fazer requisições
- `authenticated_client` - Cliente já autenticado como admin

### Fixtures de Dados

- `conta_bancaria_teste` - Conta bancária de teste
- `categoria_teste` - Categoria de teste
- `cliente_teste` - Cliente de teste
- `fornecedor_teste` - Fornecedor de teste
- `lancamento_teste` - Lançamento de teste

## 📝 Exemplos de Uso

### Testando uma API

```python
def test_criar_cliente(authenticated_client):
    """Teste de criação de cliente"""
    novo_cliente = {
        'nome': 'Cliente Teste',
        'email': 'teste@teste.com',
        'telefone': '11999999999'
    }
    
    response = authenticated_client.post('/api/clientes', json=novo_cliente)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'sucesso' in data
```

### Usando Fixtures

```python
def test_pagar_lancamento(authenticated_client, lancamento_teste, conta_bancaria_teste):
    """Teste de pagamento de lançamento"""
    response = authenticated_client.put(
        f'/api/lancamentos/{lancamento_teste["id"]}/pagar',
        json={'conta': conta_bancaria_teste['nome']}
    )
    
    assert response.status_code == 200
```

## 📊 Cobertura de Testes

### Meta de Cobertura

- **Objetivo**: 80%+ de cobertura
- **Crítico**: 90%+ para módulos de autenticação e segurança

### Visualizar Cobertura

```bash
# Gerar relatório HTML
pytest tests/ --cov=. --cov-report=html

# Abrir no navegador
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

## 🔄 CI/CD

Os testes são executados automaticamente no GitHub Actions a cada push para as branches `main` ou `develop`.

### Workflow

1. **Setup** - Instala Python e dependências
2. **Lint** - Verifica estilo de código (flake8, black)
3. **Tests** - Executa suite de testes completa
4. **Coverage** - Gera relatório de cobertura
5. **Security** - Verifica vulnerabilidades (safety, bandit)

## 🐛 Debug de Testes

### Modo debug

```bash
# Parar no primeiro erro
pytest tests/ -x

# Modo verbose com print()
pytest tests/ -v -s

# Apenas um teste específico
pytest tests/test_auth.py::TestAuthentication::test_login_valido -v
```

### Logs durante testes

```python
def test_exemplo(authenticated_client, caplog):
    """Teste com captura de logs"""
    with caplog.at_level(logging.INFO):
        response = authenticated_client.get('/api/contas')
        
        # Ver logs capturados
        for record in caplog.records:
            print(record.message)
```

## 🎯 Boas Práticas

### 1. Nomear testes descritivamente

```python
# ✅ Bom
def test_login_com_senha_incorreta_deve_retornar_401():
    ...

# ❌ Evitar
def test_login_2():
    ...
```

### 2. Testar casos de sucesso e erro

```python
def test_criar_conta_valida():  # ✅ Caso de sucesso
    ...

def test_criar_conta_sem_nome():  # ✅ Caso de erro
    ...
```

### 3. Usar fixtures para setup/cleanup

```python
@pytest.fixture
def dados_teste():
    # Setup
    dados = criar_dados()
    yield dados
    # Cleanup automático
    limpar_dados(dados)
```

### 4. Testar isoladamente

```python
# Cada teste deve ser independente
# Não depender da ordem de execução
# Usar fixtures para dados necessários
```

## 📚 Referências

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Flask](https://pytest-flask.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Objetivo: Garantir qualidade e confiabilidade do código! 🚀**
