# 🏢 Arquitetura Multi-Tenant SaaS

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Modelo de Dados](#modelo-de-dados)
3. [Isolamento de Dados](#isolamento-de-dados)
4. [Implementação](#implementação)
5. [Segurança](#segurança)
6. [Exemplos de Uso](#exemplos-de-uso)
7. [Migração](#migração)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

Este sistema implementa **multi-tenancy SaaS** onde:

- **1 EMPRESA** = 1 tenant (inquilino)
- Cada empresa pode ter **N USUÁRIOS**
- **Isolamento completo** de dados entre empresas
- Suporte a **múltiplas empresas** em um único banco de dados

### Antes vs Depois

| Aspecto | ❌ Antes (Errado) | ✅ Depois (Correto) |
|---------|------------------|---------------------|
| **Tenant** | Usuário individual | Empresa/Organização |
| **Coluna** | `proprietario_id` | `empresa_id` |
| **Relacionamento** | Dados → Usuário | Dados → Empresa |
| **Hierarquia** | Plana | Empresa → Usuários → Dados |

---

## 🗂️ Modelo de Dados

### Tabela: `empresas`

```sql
CREATE TABLE empresas (
    id SERIAL PRIMARY KEY,
    
    -- Dados da Empresa
    razao_social VARCHAR(200) NOT NULL,
    nome_fantasia VARCHAR(200),
    cnpj VARCHAR(18) UNIQUE,
    
    -- Contato
    email VARCHAR(100) NOT NULL UNIQUE,
    telefone VARCHAR(20),
    whatsapp VARCHAR(20),
    
    -- Plano e Limites
    plano VARCHAR(50) DEFAULT 'basico',  -- basico, profissional, empresarial
    max_usuarios INTEGER DEFAULT 5,
    max_clientes INTEGER DEFAULT 100,
    max_lancamentos_mes INTEGER DEFAULT 500,
    espaco_storage_mb INTEGER DEFAULT 1024,
    
    -- Status
    ativo BOOLEAN DEFAULT true,
    
    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Tabela: `usuarios`

```sql
ALTER TABLE usuarios 
ADD COLUMN empresa_id INTEGER NOT NULL 
REFERENCES empresas(id) ON DELETE CASCADE;

-- Agora usuários pertencem a uma empresa
CREATE INDEX idx_usuarios_empresa ON usuarios(empresa_id);
```

### Tabelas de Dados

Todas as tabelas de dados têm `empresa_id`:

- ✅ `clientes` → empresa_id
- ✅ `fornecedores` → empresa_id
- ✅ `lancamentos` → empresa_id
- ✅ `contratos` → empresa_id
- ✅ `sessoes` → empresa_id
- ✅ 15+ outras tabelas

---

## 🔒 Isolamento de Dados

### Princípios Fundamentais

1. **Todo dado pertence a uma empresa**
   ```sql
   -- ❌ ERRADO
   SELECT * FROM clientes;
   
   -- ✅ CORRETO
   SELECT * FROM clientes WHERE empresa_id = 123;
   ```

2. **Usuários não podem acessar dados de outras empresas**
   ```python
   empresa_atual = TenantContext.get_empresa_id()  # ID da empresa do usuário
   # Todas queries DEVEM filtrar por empresa_atual
   ```

3. **Validação automática em todas as APIs**
   ```python
   @app.route('/api/clientes')
   @tenant_required  # ← Valida empresa automaticamente
   def listar_clientes():
       empresa_id = TenantContext.get_empresa_id()
       # ...
   ```

### Como Funciona

```
┌─────────────────────────────────────────┐
│  Request do Usuário                     │
└──────────────┬──────────────────────────┘
               │
               ▼
      ┌────────────────┐
      │ @tenant_required│
      └────────┬───────┘
               │
               ├─ Verifica autenticação
               ├─ Busca empresa_id do usuário
               ├─ Valida empresa ativa
               └─ Define TenantContext.empresa_id
               │
               ▼
      ┌────────────────┐
      │ Lógica da API  │
      └────────┬───────┘
               │
               ├─ Obtém empresa_id do contexto
               ├─ Filtra queries por empresa_id
               └─ Retorna apenas dados da empresa
               │
               ▼
      ┌────────────────┐
      │   Resposta     │
      └────────────────┘
```

---

## 💻 Implementação

### 1. TenantContext (Gerenciador de Contexto)

```python
from tenant_context import TenantContext, tenant_required

# Definir empresa atual (feito automaticamente por @tenant_required)
TenantContext.set_empresa(empresa_id, usuario_id)

# Obter empresa atual
empresa_id = TenantContext.get_empresa_id()

# Verificar se está definido
if TenantContext.is_set():
    # Fazer algo
```

### 2. Decorator @tenant_required

```python
@app.route('/api/clientes', methods=['GET'])
@tenant_required  # ← SEMPRE use este decorator
def listar_clientes():
    empresa_id = TenantContext.get_empresa_id()
    
    cursor.execute("""
        SELECT * FROM clientes 
        WHERE empresa_id = %s
        ORDER BY nome
    """, (empresa_id,))
    
    return jsonify(clientes)
```

### 3. QueryBuilder com Filtro Automático

```python
from tenant_context import TenantQueryBuilder

@app.route('/api/produtos')
@tenant_required
def listar_produtos():
    # QueryBuilder adiciona empresa_id automaticamente
    query = TenantQueryBuilder('produtos') \
        .select('id', 'nome', 'preco') \
        .where("ativo = true") \
        .order_by('nome') \
        .limit(50) \
        .build()
    
    # Query gerada: 
    # SELECT id, nome, preco FROM produtos 
    # WHERE empresa_id = 123 AND ativo = true 
    # ORDER BY nome LIMIT 50
```

### 4. Validação de Acesso Cross-Tenant

```python
from tenant_context import validate_tenant_access

@app.route('/api/cliente/<int:cliente_id>')
@tenant_required
def obter_cliente(cliente_id):
    cursor.execute("""
        SELECT * FROM clientes WHERE id = %s
    """, (cliente_id,))
    
    cliente = cursor.fetchone()
    
    # Validar se cliente pertence à empresa do usuário
    if not validate_tenant_access(cliente['empresa_id']):
        return jsonify({'error': 'Acesso negado'}), 403
    
    return jsonify(cliente)
```

---

## 🛡️ Segurança

### Checklist de Segurança

- ✅ **Nunca** fazer query sem filtro `empresa_id`
- ✅ **Sempre** usar `@tenant_required` em rotas protegidas
- ✅ **Validar** empresa_id antes de atualizar/deletar
- ✅ **Logar** tentativas de acesso cross-tenant
- ✅ **Testar** isolamento entre empresas

### Anti-Patterns (NÃO FAÇA)

```python
# ❌ ERRADO - Sem filtro de empresa
cursor.execute("SELECT * FROM clientes")

# ❌ ERRADO - Sem decorator @tenant_required
@app.route('/api/dados')
def pegar_dados():
    # Qualquer um pode acessar!
    pass

# ❌ ERRADO - Empresa_id vindo do client (manipulável)
@app.route('/api/clientes')
def listar():
    empresa_id = request.args.get('empresa_id')  # ← NUNCA!
    # Usar TenantContext.get_empresa_id() sempre!
```

### Patterns Corretos

```python
# ✅ CORRETO
@app.route('/api/clientes')
@tenant_required  # ← Valida e define contexto
def listar_clientes():
    empresa_id = TenantContext.get_empresa_id()  # ← Do contexto, não do request
    
    cursor.execute("""
        SELECT * FROM clientes 
        WHERE empresa_id = %s  -- ← Sempre filtrar
    """, (empresa_id,))
    
    return jsonify(clientes)
```

---

## 📚 Exemplos de Uso

### Exemplo 1: Listar com Paginação

```python
@app.route('/api/clientes')
@tenant_required
def listar_clientes():
    empresa_id = TenantContext.get_empresa_id()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    cursor.execute("""
        SELECT * FROM clientes 
        WHERE empresa_id = %s
        ORDER BY nome
        LIMIT %s OFFSET %s
    """, (empresa_id, per_page, offset))
    
    clientes = cursor.fetchall()
    
    # Total para paginação
    cursor.execute("""
        SELECT COUNT(*) FROM clientes 
        WHERE empresa_id = %s
    """, (empresa_id,))
    total = cursor.fetchone()[0]
    
    return jsonify({
        'clientes': clientes,
        'total': total,
        'page': page,
        'pages': (total + per_page - 1) // per_page
    })
```

### Exemplo 2: Criar Registro

```python
@app.route('/api/clientes', methods=['POST'])
@tenant_required
def criar_cliente():
    empresa_id = TenantContext.get_empresa_id()  # ← Do contexto
    dados = request.json
    
    cursor.execute("""
        INSERT INTO clientes (
            nome, email, telefone, empresa_id
        ) VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        dados['nome'],
        dados['email'],
        dados['telefone'],
        empresa_id  # ← SEMPRE incluir
    ))
    
    cliente_id = cursor.fetchone()[0]
    conn.commit()
    
    return jsonify({'success': True, 'id': cliente_id}), 201
```

### Exemplo 3: Atualizar com Validação

```python
@app.route('/api/clientes/<int:cliente_id>', methods=['PUT'])
@tenant_required
def atualizar_cliente(cliente_id):
    empresa_id = TenantContext.get_empresa_id()
    dados = request.json
    
    # 1. Verificar se cliente existe E pertence à empresa
    cursor.execute("""
        SELECT id FROM clientes 
        WHERE id = %s AND empresa_id = %s
    """, (cliente_id, empresa_id))
    
    if not cursor.fetchone():
        return jsonify({'error': 'Cliente não encontrado'}), 404
    
    # 2. Atualizar (empresa_id já validado)
    cursor.execute("""
        UPDATE clientes 
        SET nome = %s, email = %s, updated_at = NOW()
        WHERE id = %s AND empresa_id = %s
    """, (dados['nome'], dados['email'], cliente_id, empresa_id))
    
    conn.commit()
    return jsonify({'success': True})
```

### Exemplo 4: Deletar com Segurança

```python
@app.route('/api/clientes/<int:cliente_id>', methods=['DELETE'])
@tenant_required
def deletar_cliente(cliente_id):
    empresa_id = TenantContext.get_empresa_id()
    
    # DELETE com filtro de empresa
    cursor.execute("""
        DELETE FROM clientes 
        WHERE id = %s AND empresa_id = %s
    """, (cliente_id, empresa_id))
    
    if cursor.rowcount == 0:
        return jsonify({'error': 'Cliente não encontrado ou sem permissão'}), 404
    
    conn.commit()
    return jsonify({'success': True})
```

---

## 🔄 Migração

### Executar Migração

```bash
# Automática (ao iniciar web_server.py)
python web_server.py

# Manual
python migration_multi_tenant_saas.py
```

### Etapas da Migração

1. ✅ Cria tabela `empresas`
2. ✅ Adiciona `empresa_id` em `usuarios`
3. ✅ Cria empresa padrão
4. ✅ Migra usuários existentes
5. ✅ Renomeia `proprietario_id` → `empresa_id` (20 tabelas)
6. ✅ Popula `empresa_id` em registros órfãos
7. ✅ Torna `empresa_id` NOT NULL

### Verificar Status

```python
from migration_multi_tenant_saas import verificar_migracao
import os

# Conectar e verificar
os.environ['DATABASE_URL'] = 'sua_url'
verificar_migracao(cursor)
```

---

## 🧪 Testing

### Testar Isolamento

```python
# Script de teste
def test_tenant_isolation():
    # Criar 2 empresas
    empresa1_id = database.criar_empresa({
        'razao_social': 'Empresa A',
        'email': 'empresaA@test.com'
    })['empresa_id']
    
    empresa2_id = database.criar_empresa({
        'razao_social': 'Empresa B',
        'email': 'empresaB@test.com'
    })['empresa_id']
    
    # Criar clientes em cada empresa
    cursor.execute("""
        INSERT INTO clientes (nome, email, empresa_id)
        VALUES ('Cliente A', 'a@test.com', %s)
    """, (empresa1_id,))
    
    cursor.execute("""
        INSERT INTO clientes (nome, email, empresa_id)
        VALUES ('Cliente B', 'b@test.com', %s)
    """, (empresa2_id,))
    
    # Verificar isolamento
    cursor.execute("""
        SELECT * FROM clientes WHERE empresa_id = %s
    """, (empresa1_id,))
    
    clientes_empresa_a = cursor.fetchall()
    assert len(clientes_empresa_a) == 1  # Deve ver apenas 1
    assert clientes_empresa_a[0]['nome'] == 'Cliente A'
    
    print("✅ Isolamento funcionando corretamente!")
```

---

## ⚠️ Troubleshooting

### Problema: "Contexto de tenant não definido"

**Erro:**
```
ValueError: Contexto de tenant não definido
```

**Solução:**
```python
# Adicionar @tenant_required no endpoint
@app.route('/api/dados')
@tenant_required  # ← ADICIONAR ISSO
def minha_rota():
    # ...
```

### Problema: Usuário vê dados de outra empresa

**Causa:** Query sem filtro `empresa_id`

**Solução:**
```python
# ❌ ERRADO
cursor.execute("SELECT * FROM clientes")

# ✅ CORRETO
empresa_id = TenantContext.get_empresa_id()
cursor.execute("""
    SELECT * FROM clientes WHERE empresa_id = %s
""", (empresa_id,))
```

### Problema: Migração falha

**Verificar:**
1. `DATABASE_URL` está configurada?
2. Banco tem permissões para ALTER TABLE?
3. Já existe dados conflitantes?

**Rollback:**
```sql
-- Se necessário, reverter manualmente
ALTER TABLE usuarios DROP COLUMN empresa_id;
DROP TABLE empresas CASCADE;
```

---

## 📊 Planos e Limites

### Configuração de Planos

```python
PLANOS = {
    'basico': {
        'max_usuarios': 5,
        'max_clientes': 100,
        'max_lancamentos_mes': 500,
        'espaco_storage_mb': 1024,
        'preco': 49.90
    },
    'profissional': {
        'max_usuarios': 20,
        'max_clientes': 500,
        'max_lancamentos_mes': 2000,
        'espaco_storage_mb': 5120,
        'preco': 149.90
    },
    'empresarial': {
        'max_usuarios': 999,
        'max_clientes': 9999,
        'max_lancamentos_mes': 99999,
        'espaco_storage_mb': 20480,
        'preco': 499.90
    }
}
```

### Validar Limites

```python
def validar_limite_usuarios(empresa_id):
    """Verifica se empresa pode criar mais usuários"""
    empresa = database.obter_empresa(empresa_id)
    stats = database.obter_estatisticas_empresa(empresa_id)
    
    if stats['total_usuarios'] >= empresa['max_usuarios']:
        raise Exception(f"Limite de {empresa['max_usuarios']} usuários atingido")
```

---

## 🎯 Best Practices

1. ✅ **Sempre** use `@tenant_required` em APIs protegidas
2. ✅ **Sempre** filtre por `empresa_id` em queries
3. ✅ **Valide** empresa_id antes de UPDATE/DELETE
4. ✅ **Teste** isolamento entre empresas
5. ✅ **Monitore** tentativas de acesso cross-tenant
6. ✅ **Documente** novas APIs com exemplos tenant-aware

---

## 📞 Suporte

**Dúvidas?** Consulte:
- [tenant_context.py](tenant_context.py) - Context manager
- [migration_multi_tenant_saas.py](migration_multi_tenant_saas.py) - Script de migração
- [database_postgresql.py](database_postgresql.py) - Funções CRUD de empresas

**Criado em:** Janeiro 2026  
**Versão:** 1.0  
**Status:** ✅ Em Produção
