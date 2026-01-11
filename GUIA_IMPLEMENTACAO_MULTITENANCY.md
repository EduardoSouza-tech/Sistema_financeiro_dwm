# 🔧 Guia de Implementação - Controle de Acesso Multi-Tenancy

## ⚡ Quick Start

### 1. Adicionar Filtro em uma Rota Existente

**ANTES (Sem filtro):**
```python
@app.route('/api/clientes')
@require_auth
def listar_clientes():
    clientes = db.listar_clientes()
    return jsonify(clientes)
```

**DEPOIS (Com filtro):**
```python
@app.route('/api/clientes')
@require_auth
@aplicar_filtro_cliente
def listar_clientes():
    # request.filtro_cliente_id está disponível
    clientes = db.listar_clientes(filtro_cliente_id=request.filtro_cliente_id)
    return jsonify(clientes)
```

---

## 📝 Checklist de Implementação

### Passo 1: Adicionar Coluna nas Tabelas

```sql
-- Para cada tabela que precisa de isolamento:
ALTER TABLE clientes ADD COLUMN proprietario_id INTEGER;
ALTER TABLE fornecedores ADD COLUMN proprietario_id INTEGER;
ALTER TABLE lancamentos ADD COLUMN proprietario_id INTEGER;
ALTER TABLE contas_bancarias ADD COLUMN proprietario_id INTEGER;

-- Adicionar índices para performance:
CREATE INDEX idx_clientes_proprietario ON clientes(proprietario_id);
CREATE INDEX idx_fornecedores_proprietario ON fornecedores(proprietario_id);
CREATE INDEX idx_lancamentos_proprietario ON lancamentos(proprietario_id);
CREATE INDEX idx_contas_proprietario ON contas_bancarias(proprietario_id);
```

### Passo 2: Atualizar Funções do Banco de Dados

**Exemplo: listar_clientes()**

```python
def listar_clientes(filtro_cliente_id=None, ativos=True):
    """
    Lista clientes com filtro opcional por proprietário
    
    Args:
        filtro_cliente_id: ID do cliente dono (None = todos, para admin)
        ativos: Apenas clientes ativos
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM clientes WHERE 1=1"
    params = []
    
    # Filtro de ativo
    if ativos:
        query += " AND ativo = TRUE"
    
    # Filtro de proprietário (multi-tenancy)
    if filtro_cliente_id is not None:
        query += " AND proprietario_id = %s"
        params.append(filtro_cliente_id)
    
    query += " ORDER BY nome"
    
    cursor.execute(query, params)
    clientes = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return clientes
```

### Passo 3: Atualizar Rotas da API

**Exemplo Completo: CRUD de Clientes**

```python
# ========== LISTAR ==========
@app.route('/api/clientes', methods=['GET'])
@require_auth
@require_permission('clientes_view')
@aplicar_filtro_cliente
def api_listar_clientes():
    """Lista clientes com filtro automático"""
    try:
        # request.filtro_cliente_id já está disponível
        clientes = db.listar_clientes(
            filtro_cliente_id=request.filtro_cliente_id,
            ativos=True
        )
        return jsonify({'success': True, 'clientes': clientes})
    except Exception as e:
        print(f"Erro ao listar clientes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== CRIAR ==========
@app.route('/api/clientes', methods=['POST'])
@require_auth
@require_permission('clientes_create')
@aplicar_filtro_cliente
def api_criar_cliente():
    """Cria cliente com proprietário automático"""
    try:
        data = request.json
        usuario = request.usuario
        
        # Definir proprietário automaticamente
        if usuario['tipo'] == 'cliente':
            data['proprietario_id'] = usuario['cliente_id']
        else:
            # Admin pode escolher ou deixar None (global)
            data['proprietario_id'] = data.get('proprietario_id', None)
        
        cliente_id = db.adicionar_cliente(data)
        
        # Log de auditoria
        auth_db.registrar_log_acesso(
            usuario_id=usuario['id'],
            acao='create_cliente',
            descricao=f'Cliente criado: {data["nome"]}',
            recurso='clientes',
            recurso_id=cliente_id,
            ip_address=request.remote_addr,
            sucesso=True
        )
        
        return jsonify({'success': True, 'id': cliente_id}), 201
    except Exception as e:
        print(f"Erro ao criar cliente: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== ATUALIZAR ==========
@app.route('/api/clientes/<int:cliente_id>', methods=['PUT'])
@require_auth
@require_permission('clientes_edit')
def api_atualizar_cliente(cliente_id):
    """Atualiza cliente com verificação de propriedade"""
    try:
        usuario = get_usuario_logado()
        
        # Verificar propriedade do recurso
        cliente_atual = db.obter_cliente(cliente_id)
        
        if not cliente_atual:
            return jsonify({'success': False, 'error': 'Cliente não encontrado'}), 404
        
        # Cliente só pode editar seus próprios recursos
        if usuario['tipo'] == 'cliente':
            if cliente_atual.get('proprietario_id') != usuario['cliente_id']:
                return jsonify({'success': False, 'error': 'Acesso negado'}), 403
        
        # Atualizar
        data = request.json
        sucesso = db.atualizar_cliente(cliente_id, data)
        
        # Log de auditoria
        auth_db.registrar_log_acesso(
            usuario_id=usuario['id'],
            acao='update_cliente',
            descricao=f'Cliente atualizado: {data.get("nome", "N/A")}',
            recurso='clientes',
            recurso_id=cliente_id,
            ip_address=request.remote_addr,
            sucesso=sucesso
        )
        
        return jsonify({'success': sucesso})
    except Exception as e:
        print(f"Erro ao atualizar cliente: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== EXCLUIR ==========
@app.route('/api/clientes/<int:cliente_id>', methods=['DELETE'])
@require_auth
@require_permission('clientes_delete')
def api_excluir_cliente(cliente_id):
    """Exclui cliente com verificação de propriedade"""
    try:
        usuario = get_usuario_logado()
        
        # Verificar propriedade
        cliente_atual = db.obter_cliente(cliente_id)
        
        if not cliente_atual:
            return jsonify({'success': False, 'error': 'Cliente não encontrado'}), 404
        
        if usuario['tipo'] == 'cliente':
            if cliente_atual.get('proprietario_id') != usuario['cliente_id']:
                return jsonify({'success': False, 'error': 'Acesso negado'}), 403
        
        # Excluir
        sucesso = db.inativar_cliente(cliente_id)
        
        # Log de auditoria
        auth_db.registrar_log_acesso(
            usuario_id=usuario['id'],
            acao='delete_cliente',
            descricao=f'Cliente excluído: {cliente_atual.get("nome", "N/A")}',
            recurso='clientes',
            recurso_id=cliente_id,
            ip_address=request.remote_addr,
            sucesso=sucesso
        )
        
        return jsonify({'success': sucesso})
    except Exception as e:
        print(f"Erro ao excluir cliente: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

## 🧪 Testes

### Teste 1: Admin Vê Tudo

```bash
# Login como admin
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Listar clientes (deve retornar TODOS)
curl http://localhost:8080/api/clientes \
  -H "Cookie: session=..."

# Resultado esperado:
{
  "success": true,
  "clientes": [
    {"id": 1, "nome": "Cliente A", "proprietario_id": 10},
    {"id": 2, "nome": "Cliente B", "proprietario_id": 20},
    {"id": 3, "nome": "Cliente C", "proprietario_id": 10}
  ]
}
```

### Teste 2: Cliente Vê Apenas Seus Dados

```bash
# Login como cliente (cliente_id = 10)
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "cliente10", "password": "senha123"}'

# Listar clientes (deve retornar apenas proprietario_id = 10)
curl http://localhost:8080/api/clientes \
  -H "Cookie: session=..."

# Resultado esperado:
{
  "success": true,
  "clientes": [
    {"id": 1, "nome": "Cliente A", "proprietario_id": 10},
    {"id": 3, "nome": "Cliente C", "proprietario_id": 10}
  ]
}
```

### Teste 3: Cliente Não Pode Editar Dados de Outro

```bash
# Cliente 10 tentando editar cliente que pertence a 20
curl -X PUT http://localhost:8080/api/clientes/2 \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"nome": "Tentando Editar"}'

# Resultado esperado:
{
  "success": false,
  "error": "Acesso negado"
}
# Status: 403 Forbidden
```

---

## 📋 Tabelas a Serem Atualizadas

| Tabela | Coluna a Adicionar | Índice | Prioridade |
|--------|-------------------|--------|------------|
| `clientes` | `proprietario_id` | ✅ | Alta |
| `fornecedores` | `proprietario_id` | ✅ | Alta |
| `lancamentos` | `proprietario_id` | ✅ | Alta |
| `contas_bancarias` | `proprietario_id` | ✅ | Alta |
| `contratos` | `proprietario_id` | ✅ | Média |
| `sessoes` | `proprietario_id` | ✅ | Média |
| `agenda` | `proprietario_id` | ✅ | Baixa |
| `produtos` | `proprietario_id` | ✅ | Baixa |
| `kits` | `proprietario_id` | ✅ | Baixa |

---

## 🚨 Problemas Comuns e Soluções

### Problema 1: "Nenhum dado aparece para cliente"

**Causa:** Dados antigos não têm `proprietario_id`

**Solução:**
```sql
-- Atribuir dados antigos ao primeiro cliente ou admin
UPDATE clientes SET proprietario_id = 1 WHERE proprietario_id IS NULL;
UPDATE fornecedores SET proprietario_id = 1 WHERE proprietario_id IS NULL;
UPDATE lancamentos SET proprietario_id = 1 WHERE proprietario_id IS NULL;
```

### Problema 2: "Admin não vê nada"

**Causa:** Filtro sendo aplicado para admin

**Solução:** Verificar se `filtro_cliente_id` é `None` para admin:
```python
if usuario['tipo'] == 'admin':
    request.filtro_cliente_id = None  # ✅ CORRETO
```

### Problema 3: "Cliente vê dados de outro cliente"

**Causa:** Filtro não está sendo aplicado na query

**Solução:** Sempre usar o filtro nas queries:
```python
query = "SELECT * FROM tabela WHERE 1=1"
if filtro_cliente_id is not None:
    query += " AND proprietario_id = %s"
    params.append(filtro_cliente_id)
```

---

## 📊 Métricas de Sucesso

### Implementação Completa Quando:

- ✅ Todas as tabelas têm coluna `proprietario_id`
- ✅ Todos os índices estão criados
- ✅ Todas as funções do banco aceitam `filtro_cliente_id`
- ✅ Todas as rotas usam `@aplicar_filtro_cliente`
- ✅ Verificação de propriedade em edições/exclusões
- ✅ Logs de auditoria em ações sensíveis
- ✅ Testes passando para admin e cliente
- ✅ Documentação atualizada

---

**Próximos Passos:**
1. Executar migrations do banco de dados
2. Atualizar funções do `database_postgresql.py`
3. Atualizar rotas em `web_server.py`
4. Testar cada funcionalidade
5. Deploy em produção

**Tempo Estimado:** 4-6 horas de desenvolvimento + 2 horas de testes
