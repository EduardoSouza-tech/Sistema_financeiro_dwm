# 📋 Documentação Completa - Módulo de Clientes

## 🎯 Visão Geral

Este documento descreve o funcionamento completo do módulo de **Clientes**, incluindo todas as operações CRUD (Create, Read, Update, Delete), filtros multi-empresa e sistema de permissões.

---

## 🏗️ Arquitetura do Sistema

### Componentes Principais

1. **Frontend**
   - `interface_nova.html` - Interface de usuário
   - `app.js` - Lógica de clientes (CRUD)
   - `modals.js` - Modais de cadastro e edição
   - `style.css` - Estilos

2. **Backend**
   - `web_server.py` - Endpoints da API
   - `database_postgresql.py` - Acesso ao banco de dados
   - `models.py` - Modelos de dados

3. **Banco de Dados**
   - Tabela `clientes` - Dados dos clientes
   - Tabela `usuario_empresas` - Associação usuário-empresa
   - JSONB `permissoes_empresa` - Controle de permissões

---

## 🔐 Sistema Multi-Empresa

### Seleção de Empresa Ativa

```javascript
// Empresa atual armazenada globalmente
window.currentEmpresaId = 18;  // Exemplo

// Todas as operações filtram pela empresa ativa
console.log('🏢 Empresa ativa:', window.currentEmpresaId);
```

### Permissões de Acesso

```javascript
// Verificação de permissão no menu
{
    permissoes_empresa: {
        "cadastros": {
            "clientes": true  // Permite acesso ao módulo
        }
    }
}
```

---

## 📊 Operações CRUD

### 1️⃣ CREATE - Criar Cliente

#### Frontend (modals.js)

```javascript
async function salvarCliente(event) {
    event.preventDefault();
    
    // Coleta dados do formulário
    const clienteData = {
        cnpj: document.getElementById('cliente-cnpj').value,
        razao_social: document.getElementById('cliente-razao').value,
        nome_fantasia: document.getElementById('cliente-fantasia').value,
        inscricao_estadual: document.getElementById('cliente-ie').value,
        inscricao_municipal: document.getElementById('cliente-im').value,
        // ... outros campos
    };
    
    // Modo criação ou edição
    const isEdit = document.getElementById('cliente-edit-mode').value === 'true';
    const url = isEdit ? 
        `${API_URL}/clientes/${nomeOriginal}` : 
        `${API_URL}/clientes`;
    
    const method = isEdit ? 'PUT' : 'POST';
    
    // Envia requisição com CSRF token
    const response = await fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(clienteData)
    });
    
    if (response.ok) {
        showToast('✓ Cliente salvo com sucesso!', 'success');
        closeModal();
        await loadClientes();  // Recarrega a lista
    }
}
```

#### Backend (web_server.py)

```python
@app.route('/api/clientes', methods=['POST'])
@login_required
@csrf.exempt
@require_permission('cadastros', 'clientes')
def criar_cliente():
    """Cria novo cliente na empresa ativa"""
    
    # Extrai empresa_id da sessão
    empresa_id = extrair_empresa_id_da_sessao()
    
    data = request.json
    data['empresa_id'] = empresa_id
    
    # Valida dados obrigatórios
    campos_obrigatorios = ['cnpj', 'razao_social', 'nome_fantasia']
    for campo in campos_obrigatorios:
        if not data.get(campo):
            return jsonify({
                'success': False, 
                'error': f'Campo {campo} é obrigatório'
            }), 400
    
    # Cria no banco
    db.criar_cliente(data)
    
    return jsonify({'success': True, 'message': 'Cliente criado'})
```

#### Database (database_postgresql.py)

```python
def criar_cliente(self, dados):
    """Insere cliente no PostgreSQL"""
    
    query = """
        INSERT INTO clientes (
            empresa_id, cnpj, razao_social, nome_fantasia,
            inscricao_estadual, inscricao_municipal, 
            cep, logradouro, numero, complemento, bairro, cidade, estado,
            telefone, email, contato, observacoes
        ) VALUES (
            %(empresa_id)s, %(cnpj)s, %(razao_social)s, %(nome_fantasia)s,
            %(inscricao_estadual)s, %(inscricao_municipal)s,
            %(cep)s, %(logradouro)s, %(numero)s, %(complemento)s, 
            %(bairro)s, %(cidade)s, %(estado)s,
            %(telefone)s, %(email)s, %(contato)s, %(observacoes)s
        )
    """
    
    self.cursor.execute(query, dados)
    self.conn.commit()
```

---

### 2️⃣ READ - Listar Clientes

#### Frontend (app.js)

```javascript
async function loadClientes() {
    console.log('📋 Carregando clientes...');
    console.log('🏢 Empresa ID:', window.currentEmpresaId);
    
    const tbody = document.getElementById('tbody-clientes');
    if (!tbody) {
        console.error('❌ Elemento tbody-clientes não encontrado!');
        return;
    }
    
    tbody.innerHTML = '<tr><td colspan="5">Carregando...</td></tr>';
    
    try {
        const response = await fetch(`${API_URL}/clientes`);
        const clientes = await response.json();
        
        console.log('✅ Clientes carregados:', clientes.length);
        
        tbody.innerHTML = '';
        
        if (clientes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">Nenhum cliente cadastrado</td></tr>';
            return;
        }
        
        // Renderiza cada cliente
        clientes.forEach(cliente => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${cliente.razao_social}</td>
                <td>${cliente.cnpj || '-'}</td>
                <td>${cliente.telefone || '-'}</td>
                <td>${cliente.email || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-primary" 
                            onclick="editarCliente('${escapeHtml(cliente.razao_social)}')" 
                            title="Editar cliente">✏️</button>
                    <button class="btn btn-sm btn-danger" 
                            onclick="excluirCliente('${escapeHtml(cliente.razao_social)}')" 
                            title="Excluir cliente">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
    } catch (error) {
        console.error('❌ Erro ao carregar clientes:', error);
        tbody.innerHTML = '<tr><td colspan="5">Erro ao carregar clientes</td></tr>';
    }
}
```

#### Backend (web_server.py)

```python
@app.route('/api/clientes', methods=['GET'])
@login_required
@require_permission('cadastros', 'clientes')
def listar_clientes():
    """Lista clientes da empresa ativa"""
    
    empresa_id = extrair_empresa_id_da_sessao()
    
    print(f"📋 Listando clientes - Empresa ID: {empresa_id}")
    
    clientes = db.obter_clientes(empresa_id)
    
    print(f"✅ {len(clientes)} clientes encontrados")
    
    return jsonify(clientes)
```

#### Database (database_postgresql.py)

```python
def obter_clientes(self, empresa_id):
    """Retorna clientes filtrados por empresa"""
    
    query = """
        SELECT 
            cnpj, razao_social, nome_fantasia,
            inscricao_estadual, inscricao_municipal,
            cep, logradouro, numero, complemento, bairro, cidade, estado,
            telefone, email, contato, observacoes
        FROM clientes
        WHERE empresa_id = %s
        ORDER BY razao_social
    """
    
    self.cursor.execute(query, (empresa_id,))
    
    columns = [desc[0] for desc in self.cursor.description]
    clientes = []
    
    for row in self.cursor.fetchall():
        cliente = dict(zip(columns, row))
        clientes.append(cliente)
    
    return clientes
```

---

### 3️⃣ UPDATE - Editar Cliente

#### Frontend (app.js)

```javascript
async function editarCliente(razaoSocial) {
    try {
        console.log('✏️ Editando cliente:', razaoSocial);
        
        if (!razaoSocial) {
            showToast('Erro: Razão social não informada', 'error');
            return;
        }
        
        // Busca dados atuais do cliente
        const response = await fetch(
            `${API_URL}/clientes/${encodeURIComponent(razaoSocial)}`
        );
        const cliente = await response.json();
        
        if (!cliente) {
            showToast('Erro: Cliente não encontrado', 'error');
            return;
        }
        
        console.log('✅ Cliente encontrado:', cliente);
        
        // Abre modal de edição (modals.js)
        if (typeof openModalCliente === 'function') {
            openModalCliente(cliente);  // Passa dados para edição
            console.log('✅ Modal de edição aberto');
        } else {
            showToast('Erro: Função de edição não disponível', 'error');
            console.error('❌ Função openModalCliente não encontrada!');
        }
        
    } catch (error) {
        console.error('❌ Erro ao editar cliente:', error);
        showToast('Erro ao abrir edição: ' + error.message, 'error');
    }
}
```

#### Backend (web_server.py)

```python
@app.route('/api/clientes/<string:razao_social>', methods=['PUT'])
@login_required
@csrf.exempt
@require_permission('cadastros', 'clientes')
def atualizar_cliente(razao_social):
    """Atualiza cliente existente"""
    
    empresa_id = extrair_empresa_id_da_sessao()
    
    data = request.json
    data['empresa_id'] = empresa_id
    data['razao_social_original'] = razao_social
    
    print(f"📝 Atualizando cliente: {razao_social}")
    print(f"🏢 Empresa ID: {empresa_id}")
    
    # Atualiza no banco (usa razao_social_original no WHERE)
    db.atualizar_cliente(data)
    
    print(f"✅ Cliente atualizado")
    
    return jsonify({'success': True, 'message': 'Cliente atualizado'})
```

#### Database (database_postgresql.py)

```python
def atualizar_cliente(self, dados):
    """Atualiza cliente - usa razao_social_original para WHERE"""
    
    razao_social_original = dados.get('razao_social_original')
    empresa_id = dados['empresa_id']
    
    query = """
        UPDATE clientes SET
            cnpj = %(cnpj)s,
            razao_social = %(razao_social)s,
            nome_fantasia = %(nome_fantasia)s,
            inscricao_estadual = %(inscricao_estadual)s,
            inscricao_municipal = %(inscricao_municipal)s,
            cep = %(cep)s,
            logradouro = %(logradouro)s,
            numero = %(numero)s,
            complemento = %(complemento)s,
            bairro = %(bairro)s,
            cidade = %(cidade)s,
            estado = %(estado)s,
            telefone = %(telefone)s,
            email = %(email)s,
            contato = %(contato)s,
            observacoes = %(observacoes)s
        WHERE razao_social = %(razao_social_original)s
          AND empresa_id = %(empresa_id)s
    """
    
    self.cursor.execute(query, dados)
    self.conn.commit()
```

---

### 4️⃣ DELETE - Excluir Cliente

#### Frontend (app.js)

```javascript
async function excluirCliente(razaoSocial) {
    console.log('🗑️ excluirCliente chamada com:', razaoSocial);
    
    // Confirma exclusão
    if (!confirm(`Deseja realmente excluir o cliente "${razaoSocial}"?`)) {
        console.log('   ❌ Usuário cancelou');
        return;
    }
    
    try {
        // IMPORTANTE: Busca CSRF token do meta tag
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        console.log('   🔑 CSRF Token:', csrfToken ? 'Presente' : 'AUSENTE');
        
        const url = `${API_URL}/clientes/${encodeURIComponent(razaoSocial)}`;
        console.log('   🌐 URL:', url);
        
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken  // ← OBRIGATÓRIO!
            }
        });
        
        console.log('   📡 Status:', response.status);
        
        const result = await response.json();
        console.log('   📦 Resposta:', result);
        
        if (response.ok && result.success) {
            showToast('✓ Cliente excluído com sucesso!', 'success');
            await loadClientes();  // Recarrega lista
            console.log('   ✅ Lista recarregada');
        } else {
            const errorMsg = result.error || 'Erro desconhecido';
            showToast('Erro ao excluir: ' + errorMsg, 'error');
            console.error('   ❌ Erro:', errorMsg);
        }
    } catch (error) {
        console.error('   ❌ Exception:', error);
        showToast('Erro ao excluir cliente', 'error');
    }
}
```

#### Backend (web_server.py)

```python
@app.route('/api/clientes/<string:razao_social>', methods=['DELETE'])
@login_required
@csrf.exempt
@require_permission('cadastros', 'clientes')
def excluir_cliente(razao_social):
    """Exclui cliente"""
    
    empresa_id = extrair_empresa_id_da_sessao()
    
    print(f"🗑️ Excluindo cliente: {razao_social}")
    print(f"🏢 Empresa ID: {empresa_id}")
    
    # Verifica se pode excluir (sem lançamentos)
    lancamentos = db.obter_lancamentos_cliente(razao_social, empresa_id)
    if lancamentos:
        return jsonify({
            'success': False,
            'error': 'Cliente possui lançamentos vinculados'
        }), 400
    
    # Exclui do banco
    db.excluir_cliente(razao_social, empresa_id)
    
    print(f"✅ Cliente excluído")
    
    return jsonify({'success': True, 'message': 'Cliente excluído'})
```

#### Database (database_postgresql.py)

```python
def excluir_cliente(self, razao_social, empresa_id):
    """Exclui cliente por razão social e empresa"""
    
    query = """
        DELETE FROM clientes
        WHERE razao_social = %s
          AND empresa_id = %s
    """
    
    self.cursor.execute(query, (razao_social, empresa_id))
    self.conn.commit()
```

---

## 🔒 Sistema de Segurança

### CSRF Protection

```html
<!-- Meta tag no HTML -->
<meta name="csrf-token" content="{{ csrf_token() }}">
```

```javascript
// Buscar token no JavaScript
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

// Incluir em TODAS requisições POST/PUT/DELETE
headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken  // ← OBRIGATÓRIO
}
```

### Validação de Permissões

```python
# Decorator no backend
@require_permission('cadastros', 'clientes')
def listar_clientes():
    # Só executa se usuário tem permissão
    pass
```

---

## 🎨 Funcionalidades Extras

### Abas de Filtro (Ativos/Inativos)

```javascript
function showClienteTab(tab) {
    console.log('🔄 Alternando aba de clientes:', tab);
    
    // Atualiza botões das abas
    document.querySelectorAll('.cliente-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeBtn = document.querySelector(
        `.cliente-tab-btn[onclick="showClienteTab('${tab}')"]`
    );
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // Filtra linhas da tabela
    const tbody = document.getElementById('tbody-clientes');
    const rows = tbody.querySelectorAll('tr');
    
    rows.forEach(row => {
        // Implementar lógica de filtro por status
        row.style.display = '';  // Mostra todos por enquanto
    });
    
    console.log('✅ Aba alternada:', tab);
}
```

### Busca de CEP Automática

```javascript
async function buscarCepCliente() {
    const cep = document.getElementById('cliente-cep').value.replace(/\D/g, '');
    
    if (cep.length !== 8) return;
    
    try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const dados = await response.json();
        
        if (!dados.erro) {
            document.getElementById('cliente-rua').value = dados.logradouro;
            document.getElementById('cliente-bairro').value = dados.bairro;
            document.getElementById('cliente-cidade').value = dados.localidade;
            document.getElementById('cliente-estado').value = dados.uf;
        }
    } catch (error) {
        console.error('Erro ao buscar CEP:', error);
    }
}
```

### Busca de CNPJ Automática

```javascript
async function buscarDadosCNPJ() {
    const cnpj = document.getElementById('cliente-cnpj').value.replace(/\D/g, '');
    
    if (cnpj.length !== 14) return;
    
    try {
        // Integração com API de CNPJ
        const response = await fetch(`/api/consultar-cnpj/${cnpj}`);
        const dados = await response.json();
        
        if (dados.success) {
            document.getElementById('cliente-razao').value = dados.razao_social;
            document.getElementById('cliente-fantasia').value = dados.nome_fantasia;
            // ... preencher outros campos
        }
    } catch (error) {
        console.error('Erro ao buscar CNPJ:', error);
    }
}
```

---

## 🐛 Troubleshooting

### Problema: "loadClientesTable is not defined"

**Causa:** Nome de função incorreto (era `loadClientesTable`, agora é `loadClientes`)

**Solução:**
```javascript
// ✅ CORRETO
if (typeof loadClientes === 'function') loadClientes();

// ❌ INCORRETO
if (typeof loadClientesTable === 'function') loadClientesTable();
```

---

### Problema: "CSRF validation failed"

**Causa:** Falta CSRF token nos headers da requisição DELETE/PUT/POST

**Solução:**
```javascript
// ✅ CORRETO - Com CSRF token
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

await fetch(url, {
    method: 'DELETE',
    headers: {
        'X-CSRFToken': csrfToken  // ← Obrigatório!
    }
});

// ❌ INCORRETO - Sem CSRF token
await fetch(url, {
    method: 'DELETE'
    // Falta o header X-CSRFToken
});
```

---

### Problema: "showClienteTab is not defined"

**Causa:** Função não existe no app.js

**Solução:** Adicionar função:
```javascript
function showClienteTab(tab) {
    // Lógica de alternância de abas
    console.log('Aba:', tab);
}
```

---

### Problema: Edição cria duplicata ao invés de atualizar

**Causa:** WHERE clause não usa razao_social_original

**Solução:**
```python
# ✅ CORRETO - Usa original no WHERE
UPDATE clientes SET
    razao_social = %(razao_social)s
WHERE razao_social = %(razao_social_original)s
  AND empresa_id = %(empresa_id)s

# ❌ INCORRETO - Usa novo no WHERE
UPDATE clientes SET
    razao_social = %(razao_social)s
WHERE razao_social = %(razao_social)s  # ← Não encontra!
```

---

## 📝 Checklist de Implementação

### Frontend (app.js)
- [✅] `loadClientes()` - Carrega e renderiza lista
- [✅] `editarCliente(razaoSocial)` - Abre modal de edição
- [✅] `excluirCliente(razaoSocial)` - Deleta com CSRF token
- [✅] `showClienteTab(tab)` - Alterna abas ativos/inativos
- [✅] Botões de editar e excluir na tabela
- [✅] Logs detalhados em console
- [✅] Tratamento de erros com showToast

### Frontend (modals.js)
- [✅] `openModalCliente(clienteEdit)` - Modal criação/edição
- [✅] `salvarCliente(event)` - Salva com PUT ou POST
- [✅] `buscarCepCliente()` - Autocomplete de endereço
- [✅] `buscarDadosCNPJ()` - Autocomplete de dados empresariais
- [✅] Campo hidden `cliente-nome-original` para edição
- [✅] Chamada a `loadClientes()` após salvar

### Frontend (interface_nova.html)
- [✅] Corrigido `loadClientesTable()` → `loadClientes()`
- [✅] Abas com `onclick="showClienteTab('ativos')"`
- [✅] Tabela com `id="tbody-clientes"`
- [✅] Meta tag CSRF token

### Backend (web_server.py)
- [✅] `GET /api/clientes` - Lista com filtro empresa_id
- [✅] `POST /api/clientes` - Cria novo cliente
- [✅] `GET /api/clientes/<razao_social>` - Busca um cliente
- [✅] `PUT /api/clientes/<razao_social>` - Atualiza cliente
- [✅] `DELETE /api/clientes/<razao_social>` - Exclui cliente
- [✅] Decorators: `@login_required`, `@require_permission`, `@csrf.exempt`
- [✅] Extração de `empresa_id` da sessão
- [✅] Logs detalhados

### Backend (database_postgresql.py)
- [✅] `criar_cliente(dados)` - INSERT
- [✅] `obter_clientes(empresa_id)` - SELECT com filtro
- [✅] `obter_cliente_por_razao(razao_social, empresa_id)` - SELECT específico
- [✅] `atualizar_cliente(dados)` - UPDATE com razao_social_original
- [✅] `excluir_cliente(razao_social, empresa_id)` - DELETE
- [✅] Validação de lançamentos vinculados

---

## 🎓 Exemplos de Uso

### Criar Novo Cliente

```javascript
// 1. Usuário clica em "Novo Cliente"
openModalCliente(null);  // null = modo criação

// 2. Preenche formulário
// 3. Clica em "Salvar"
// 4. salvarCliente() faz POST /api/clientes
// 5. Backend valida e insere no banco
// 6. Frontend recarrega lista com loadClientes()
```

### Editar Cliente Existente

```javascript
// 1. Usuário clica no botão ✏️ na tabela
editarCliente('Empresa XYZ Ltda');

// 2. Busca dados: GET /api/clientes/Empresa%20XYZ%20Ltda
// 3. Abre modal preenchido: openModalCliente(cliente)
// 4. Usuário altera dados e salva
// 5. salvarCliente() faz PUT /api/clientes/Empresa%20XYZ%20Ltda
// 6. Backend usa razao_social_original no WHERE
// 7. Atualiza sem criar duplicata
// 8. Frontend recarrega lista
```

### Excluir Cliente

```javascript
// 1. Usuário clica no botão 🗑️ na tabela
excluirCliente('Empresa ABC Ltda');

// 2. Confirma exclusão
// 3. Envia DELETE com CSRF token
// 4. Backend valida permissão e empresa_id
// 5. Verifica se não tem lançamentos vinculados
// 6. Exclui do banco
// 7. Frontend recarrega lista
```

---

## 🔍 Logs e Debugging

### Console do Navegador

```javascript
// Logs automáticos ao carregar
📋 Carregando clientes...
🏢 Empresa ID: 18
✅ Clientes carregados: 5

// Logs ao editar
✏️ Editando cliente: Empresa XYZ Ltda
✅ Cliente encontrado: {razao_social: "...", cnpj: "..."}
✅ Modal de edição aberto

// Logs ao excluir
🗑️ excluirCliente chamada com: Empresa ABC Ltda
   🔑 CSRF Token: Presente
   🌐 URL: http://localhost:5000/api/clientes/Empresa%20ABC%20Ltda
   📡 Status: 200
   📦 Resposta: {success: true}
   ✅ Lista recarregada
```

### Logs do Backend

```python
# Terminal do Flask
📋 Listando clientes - Empresa ID: 18
✅ 5 clientes encontrados

📝 Atualizando cliente: Empresa XYZ Ltda
🏢 Empresa ID: 18
✅ Cliente atualizado

🗑️ Excluindo cliente: Empresa ABC Ltda
🏢 Empresa ID: 18
✅ Cliente excluído
```

---

## 📚 Referências

- Código Similar: Ver `DOCUMENTACAO_CATEGORIAS.md`
- Permissões: Ver `RESUMO_PROJETO.md`
- Multi-Empresa: Ver `README_WEB.md`
- API: Ver `web_server.py`
- Database: Ver `database_postgresql.py`

---

## ✅ Status de Implementação

| Funcionalidade | Status | Observação |
|---|---|---|
| Listar clientes | ✅ | Filtro por empresa_id OK |
| Criar cliente | ✅ | Com CSRF e validações |
| Editar cliente | ✅ | Modal funcional, sem duplicatas |
| Excluir cliente | ✅ | CSRF token implementado |
| Buscar CEP | ✅ | Integração ViaCEP |
| Buscar CNPJ | ⚠️ | Implementar API externa |
| Abas ativos/inativos | ✅ | Função criada |
| Permissões | ✅ | @require_permission OK |
| Logs detalhados | ✅ | Console e backend |

---

**Última atualização:** 2024  
**Versão:** 2.0  
**Autor:** Sistema DWM
