# 🔐 Documentação do Sistema de Controle de Acesso Multi-Tenancy

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Tipos de Usuários](#tipos-de-usuários)
4. [Modelo de Dados](#modelo-de-dados)
5. [Regras de Acesso](#regras-de-acesso)
6. [Implementação Técnica](#implementação-técnica)
7. [Exemplos de Uso](#exemplos-de-uso)
8. [Segurança](#segurança)

---

## 🎯 Visão Geral

O sistema implementa um modelo de **Multi-Tenancy** onde cada cliente possui seus próprios dados isolados. Nenhum cliente pode visualizar ou manipular dados de outro cliente. Apenas administradores têm acesso global a todos os dados.

### Características Principais
- ✅ **Isolamento Total**: Cada cliente vê apenas seus dados
- ✅ **Segurança por Design**: Filtros aplicados automaticamente no backend
- ✅ **Acesso Administrativo**: Admins têm visão completa do sistema
- ✅ **Auditoria**: Todos os acessos são registrados
- ✅ **Permissões Granulares**: Controle fino de funcionalidades

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE APLICAÇÃO                       │
│  (Web Server - Flask)                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              MIDDLEWARE DE AUTENTICAÇÃO                      │
│  • get_usuario_logado()                                      │
│  • @require_auth                                             │
│  • @require_admin                                            │
│  • @require_permission(permissao)                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│           CAMADA DE CONTROLE DE ACESSO                       │
│  • filtrar_por_cliente()                                     │
│  • verificar_propriedade_recurso()                           │
│  • aplicar_filtros_automaticos()                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  CAMADA DE DADOS                             │
│  PostgreSQL com RLS (Row Level Security)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 👥 Tipos de Usuários

### 1. **Administrador** (`tipo = 'admin'`)

**Características:**
- Acesso total a todos os dados do sistema
- Pode criar, editar e excluir qualquer registro
- Gerencia usuários e permissões
- Acessa painel administrativo
- Visualiza logs de auditoria

**Campo Identificador:**
- `cliente_id = NULL`

**Exemplo:**
```json
{
  "id": 1,
  "username": "admin",
  "tipo": "admin",
  "cliente_id": null,
  "nome_completo": "Administrador do Sistema"
}
```

### 2. **Cliente** (`tipo = 'cliente'`)

**Características:**
- Acesso restrito aos seus próprios dados
- Não vê dados de outros clientes
- Pode ter sub-clientes e fornecedores próprios
- Permissões configuráveis por funcionalidade

**Campo Identificador:**
- `cliente_id = <ID_DO_CLIENTE>`

**Exemplo:**
```json
{
  "id": 5,
  "username": "empresa_abc",
  "tipo": "cliente",
  "cliente_id": 42,
  "nome_completo": "João Silva - Empresa ABC"
}
```

---

## 🗃️ Modelo de Dados

### Tabelas com Isolamento por Cliente

Todas as tabelas principais possuem a coluna `cliente_id` para isolamento:

#### 1. **usuarios**
```sql
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('admin', 'cliente')),
    cliente_id INTEGER REFERENCES clientes(id),  -- NULL para admin
    -- outros campos...
);
```

#### 2. **clientes** (Sub-clientes do sistema)
```sql
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    proprietario_id INTEGER,  -- ID do cliente dono (NULL = global)
    -- outros campos...
);
```

#### 3. **fornecedores**
```sql
CREATE TABLE fornecedores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    proprietario_id INTEGER,  -- ID do cliente dono
    -- outros campos...
);
```

#### 4. **lancamentos**
```sql
CREATE TABLE lancamentos (
    id SERIAL PRIMARY KEY,
    descricao TEXT NOT NULL,
    proprietario_id INTEGER,  -- ID do cliente dono
    -- outros campos...
);
```

#### 5. **contas_bancarias**
```sql
CREATE TABLE contas_bancarias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    proprietario_id INTEGER,  -- ID do cliente dono
    -- outros campos...
);
```

### Índices de Performance
```sql
-- Índices para otimizar filtros por cliente
CREATE INDEX idx_clientes_proprietario ON clientes(proprietario_id);
CREATE INDEX idx_fornecedores_proprietario ON fornecedores(proprietario_id);
CREATE INDEX idx_lancamentos_proprietario ON lancamentos(proprietario_id);
CREATE INDEX idx_contas_proprietario ON contas_bancarias(proprietario_id);
```

---

## 🔒 Regras de Acesso

### Matriz de Permissões

| Recurso | Administrador | Cliente (Próprio) | Cliente (Outros) |
|---------|--------------|-------------------|------------------|
| **Lançamentos** | ✅ Todos | ✅ Próprios | ❌ Bloqueado |
| **Clientes** | ✅ Todos | ✅ Próprios | ❌ Bloqueado |
| **Fornecedores** | ✅ Todos | ✅ Próprios | ❌ Bloqueado |
| **Contas** | ✅ Todas | ✅ Próprias | ❌ Bloqueado |
| **Categorias** | ✅ CRUD | ✅ Leitura | ❌ Bloqueado |
| **Relatórios** | ✅ Globais | ✅ Próprios | ❌ Bloqueado |
| **Usuários** | ✅ Gerenciar | ❌ Bloqueado | ❌ Bloqueado |
| **Permissões** | ✅ Gerenciar | ❌ Bloqueado | ❌ Bloqueado |
| **Logs** | ✅ Ver todos | ❌ Bloqueado | ❌ Bloqueado |

### Regras de Filtragem

#### Para Administradores:
```python
# Nenhum filtro aplicado - vê tudo
if usuario['tipo'] == 'admin':
    return query  # Sem filtros
```

#### Para Clientes:
```python
# Filtro automático por cliente_id
if usuario['tipo'] == 'cliente':
    cliente_id = usuario['cliente_id']
    query += f" WHERE proprietario_id = {cliente_id}"
```

---

## 💻 Implementação Técnica

### 1. Middleware de Autenticação (`auth_middleware.py`)

```python
def get_usuario_logado():
    """Retorna dados do usuário logado com cliente_id"""
    token = session.get('session_token')
    if not token:
        return None
    
    usuario = auth_db.validar_sessao(token)
    # Retorna: {id, username, tipo, cliente_id, ...}
    return usuario
```

### 2. Decorador de Filtro Automático

```python
def filtrar_por_cliente(f):
    """
    Decorador que aplica filtro automático por cliente
    - Admins: Vêem tudo
    - Clientes: Vêem apenas seus dados
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario = get_usuario_logado()
        
        if not usuario:
            return jsonify({'error': 'Não autenticado'}), 401
        
        # Adicionar filtro ao request
        if usuario['tipo'] == 'cliente':
            request.filtro_cliente_id = usuario['cliente_id']
        else:
            request.filtro_cliente_id = None  # Admin vê tudo
        
        return f(*args, **kwargs)
    
    return decorated_function
```

### 3. Aplicação dos Filtros nas Queries

```python
def listar_lancamentos():
    """Lista lançamentos com filtro automático"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Query base
    query = "SELECT * FROM lancamentos WHERE 1=1"
    params = []
    
    # Aplicar filtro de cliente se necessário
    if hasattr(request, 'filtro_cliente_id') and request.filtro_cliente_id:
        query += " AND proprietario_id = %s"
        params.append(request.filtro_cliente_id)
    
    cursor.execute(query, params)
    return cursor.fetchall()
```

### 4. Verificação de Propriedade

```python
def verificar_propriedade(recurso_id, tabela):
    """
    Verifica se o usuário tem permissão para acessar o recurso
    """
    usuario = get_usuario_logado()
    
    # Admin pode tudo
    if usuario['tipo'] == 'admin':
        return True
    
    # Cliente só pode acessar seus próprios recursos
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT proprietario_id 
        FROM {tabela} 
        WHERE id = %s
    """, (recurso_id,))
    
    resultado = cursor.fetchone()
    
    if not resultado:
        return False
    
    return resultado['proprietario_id'] == usuario['cliente_id']
```

---

## 📝 Exemplos de Uso

### Exemplo 1: Listar Lançamentos

**Cenário Admin:**
```python
@app.route('/api/lancamentos')
@require_auth
@filtrar_por_cliente
def listar_lancamentos():
    # Admin: Vê TODOS os lançamentos
    # Cliente ID 42: Vê apenas lançamentos onde proprietario_id = 42
    lancamentos = db.listar_lancamentos()  # Filtro aplicado automaticamente
    return jsonify(lancamentos)
```

**SQL Gerado para Admin:**
```sql
SELECT * FROM lancamentos;
-- Retorna: 1000 registros
```

**SQL Gerado para Cliente ID 42:**
```sql
SELECT * FROM lancamentos WHERE proprietario_id = 42;
-- Retorna: 15 registros (apenas do cliente 42)
```

### Exemplo 2: Criar Lançamento

```python
@app.route('/api/lancamentos', methods=['POST'])
@require_auth
@require_permission('lancamentos_create')
def criar_lancamento():
    usuario = get_usuario_logado()
    data = request.json
    
    # Definir proprietário automaticamente
    if usuario['tipo'] == 'cliente':
        data['proprietario_id'] = usuario['cliente_id']
    else:
        # Admin pode escolher ou deixar global
        data['proprietario_id'] = data.get('proprietario_id', None)
    
    lancamento_id = db.criar_lancamento(data)
    return jsonify({'id': lancamento_id})
```

### Exemplo 3: Editar Lançamento

```python
@app.route('/api/lancamentos/<int:lancamento_id>', methods=['PUT'])
@require_auth
@require_permission('lancamentos_edit')
def editar_lancamento(lancamento_id):
    usuario = get_usuario_logado()
    
    # Verificar propriedade
    if not verificar_propriedade(lancamento_id, 'lancamentos'):
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.json
    db.atualizar_lancamento(lancamento_id, data)
    return jsonify({'success': True})
```

---

## 🔐 Segurança

### Camadas de Segurança

#### 1. **Autenticação**
- Tokens de sessão únicos (SHA-256)
- Expiração automática (24h)
- Invalidação manual (logout)

#### 2. **Autorização**
- Verificação de tipo de usuário
- Controle de permissões granulares
- Validação de propriedade de recursos

#### 3. **Isolamento de Dados**
- Filtros automáticos no backend
- Nunca confiar em filtros do frontend
- Validação em múltiplas camadas

#### 4. **Auditoria**
```sql
CREATE TABLE log_acessos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    acao VARCHAR(100) NOT NULL,
    recurso VARCHAR(100),
    recurso_id INTEGER,
    ip_address VARCHAR(45),
    sucesso BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Práticas de Segurança

#### ✅ **SEMPRE FAZER:**
1. Validar sessão em TODAS as rotas protegidas
2. Aplicar filtros de cliente no BACKEND
3. Verificar propriedade antes de editar/excluir
4. Registrar todas as ações em logs
5. Usar queries parametrizadas (prevenir SQL Injection)

#### ❌ **NUNCA FAZER:**
1. Confiar em filtros do frontend
2. Permitir cliente_id no corpo da requisição
3. Pular verificação de propriedade
4. Expor dados de outros clientes em APIs
5. Usar concatenação de strings em SQL

### Exemplo de Vulnerabilidade Corrigida

**❌ ERRADO (Vulnerável):**
```python
@app.route('/api/lancamentos/<int:id>')
def obter_lancamento(id):
    # PERIGO! Qualquer cliente pode acessar qualquer lançamento
    lancamento = db.obter_lancamento(id)
    return jsonify(lancamento)
```

**✅ CORRETO (Seguro):**
```python
@app.route('/api/lancamentos/<int:id>')
@require_auth
def obter_lancamento(id):
    usuario = get_usuario_logado()
    lancamento = db.obter_lancamento(id)
    
    # Verificar propriedade
    if usuario['tipo'] == 'cliente':
        if lancamento['proprietario_id'] != usuario['cliente_id']:
            return jsonify({'error': 'Acesso negado'}), 403
    
    return jsonify(lancamento)
```

---

## 📊 Fluxo de Acesso Completo

```
┌─────────────────────────────────────────────────────────┐
│ 1. REQUISIÇÃO DO CLIENTE                                │
│    GET /api/lancamentos                                 │
│    Cookie: session_token=abc123...                      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. MIDDLEWARE DE AUTENTICAÇÃO (@require_auth)           │
│    • Valida token                                       │
│    • Busca dados do usuário                             │
│    • Retorna: {id: 5, tipo: 'cliente', cliente_id: 42} │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. MIDDLEWARE DE PERMISSÕES (@require_permission)       │
│    • Verifica permissão 'lancamentos_view'             │
│    • Permite ou bloqueia acesso                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. FILTRO DE CLIENTE (@filtrar_por_cliente)            │
│    • Usuario tipo = 'cliente'                           │
│    • Define: request.filtro_cliente_id = 42            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 5. FUNÇÃO DO CONTROLADOR                                │
│    • Chama: db.listar_lancamentos()                    │
│    • Aplica filtro automaticamente                      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 6. CONSULTA NO BANCO                                    │
│    SELECT * FROM lancamentos                            │
│    WHERE proprietario_id = 42                          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 7. RESPOSTA                                             │
│    [{id: 1, descricao: "...", proprietario_id: 42},    │
│     {id: 2, descricao: "...", proprietario_id: 42}]    │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Resumo Executivo

### Para Desenvolvedores
- Use sempre os decoradores `@require_auth` e `@filtrar_por_cliente`
- Nunca confie em dados do frontend para filtrar por cliente
- Sempre verifique propriedade antes de editar/excluir
- Registre todas as ações sensíveis nos logs

### Para Administradores
- Admins vêem todos os dados sem filtros
- Clientes vêem apenas seus próprios dados
- Sistema de permissões granulares permite controle fino
- Logs de auditoria rastreiam todas as ações

### Para Segurança
- Multi-camadas de proteção
- Isolamento total entre clientes
- Auditoria completa de acessos
- Prevenção de SQL Injection e outras vulnerabilidades comuns

---

**Versão:** 1.0  
**Última Atualização:** 11 de Janeiro de 2026  
**Autor:** Sistema Financeiro DWM
