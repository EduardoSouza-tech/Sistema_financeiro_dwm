# 📦 Documentação - Kits de Equipamentos

## 🔴 PROBLEMAS IDENTIFICADOS

### ❌ Função `openModalKit()` não existe
**Erro:** Ao clicar em "➕ Novo Kit", JavaScript retorna erro: `openModalKit is not defined`  
**Causa:** A função nunca foi implementada  
**Status:** ⚠️ PRECISA SER CRIADA

### ❌ Função para renderizar tabela não existe
**Erro:** Tabela fica com "Carregando..." infinitamente  
**Causa:** `loadKits()` apenas salva em `window.kits`, mas não renderiza na tabela  
**Status:** ⚠️ PRECISA SER CRIADA

### ❌ POST endpoint chama função inexistente
**Erro:** `db.adicionar_kit(data)` não existe  
**Causa:** Função não implementada no database.py  
**Status:** ⚠️ IMPLEMENTAR DIRETAMENTE NO ENDPOINT

---

## 📊 Estrutura do Banco de Dados

### Tabela: `kits`

```sql
CREATE TABLE IF NOT EXISTS kits (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    empresa_id INTEGER,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### ⚠️ IMPORTANTE - Estrutura Atual:
A tabela existe com apenas **3 colunas principais**:
- ✅ `id` - Identificador único
- ✅ `nome` - Nome do kit
- ✅ `descricao` - Descrição do kit

**Colunas que podem ser adicionadas no futuro:**
- `empresa_id` - Para multi-tenancy
- `itens` - JSON com lista de equipamentos
- `valor_total` - Valor calculado do kit

---

## 🔌 Endpoints da API

### GET `/api/kits`
**Status:** ✅ FUNCIONANDO  
**Uso:** Lista todos os kits cadastrados

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "nome": "Kit Fotografia Básico",
      "descricao": "Câmera + Lente 50mm + Tripé"
    }
  ]
}
```

**Permissão:** Nenhuma (acesso livre)  
**Auto-criação:** Se a tabela não existir, será criada automaticamente

---

### POST `/api/kits`
**Status:** ❌ NÃO FUNCIONA  
**Problema:** Chama `db.adicionar_kit(data)` que não existe

**Body esperado:**
```json
{
  "nome": "Nome do Kit",
  "descricao": "Descrição opcional"
}
```

**Solução necessária:** Implementar query direta no endpoint

---

### PUT `/api/kits/<id>`
**Status:** ❌ NÃO FUNCIONA  
**Problema:** Chama `db.atualizar_kit(kit_id, data)` que não existe  
**Permissão:** `@require_permission('estoque_edit')`

---

### DELETE `/api/kits/<id>`
**Status:** ❌ NÃO FUNCIONA  
**Problema:** Chama `db.deletar_kit(kit_id)` que não existe  
**Permissão:** `@require_permission('estoque_edit')`

---

## 🖥️ Interface Frontend

### Arquivo: `templates/interface_nova.html`

#### Seção HTML (linha ~2888)
```html
<div id="kits-equipamentos-section" class="content-card hidden">
    <h2>Kits de Equipamentos</h2>
    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
        <button class="btn btn-primary" onclick="openModalKit()">➕ Novo Kit</button>
    </div>
    <div class="table-scroll-container">
        <table id="table-kits">
            <thead>
                <tr>
                    <th>Nome</th>
                    <th>Descrição</th>
                    <th>Itens</th>
                    <th>Valor Total</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody id="tbody-kits">
                <tr><td colspan="5" class="loading">Carregando...</td></tr>
            </tbody>
        </table>
    </div>
</div>
```

---

### Arquivo: `static/app.js`

#### Função: `loadKits()` (linha 2868)
**Status:** ✅ FUNCIONA mas não renderiza tabela  

```javascript
async function loadKits() {
    const response = await fetch('/api/kits', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    });
    
    const result = await response.json();
    
    if (result.success && result.data) {
        window.kits = result.data; // ✅ Salva em memória
        console.log('✅ Kits carregados:', window.kits.length);
        // ❌ FALTA: Renderizar na tabela tbody-kits
    }
}
```

---

## 🔧 O que precisa ser implementado

### 1. Modal de Cadastro/Edição (`openModalKit`)
```javascript
function openModalKit(kitEdit = null) {
    const isEdit = kitEdit !== null;
    const modal = createModal(
        isEdit ? 'Editar Kit' : 'Novo Kit',
        `
        <form id="form-kit" onsubmit="salvarKit(event)">
            <input type="hidden" id="kit-id" value="${isEdit ? kitEdit.id : ''}">
            
            <div class="form-group">
                <label>*Nome do Kit:</label>
                <input type="text" id="kit-nome" required 
                    value="${isEdit ? kitEdit.nome : ''}" 
                    placeholder="Ex: Kit Fotografia Básico">
            </div>
            
            <div class="form-group">
                <label>Descrição:</label>
                <textarea id="kit-descricao" rows="3"
                    placeholder="Descreva o que inclui no kit..."
                >${isEdit ? (kitEdit.descricao || '') : ''}</textarea>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button type="button" class="btn" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">
                    ${isEdit ? 'Atualizar' : 'Criar'} Kit
                </button>
            </div>
        </form>
        `
    );
}
```

### 2. Função de Salvar (`salvarKit`)
```javascript
async function salvarKit(event) {
    event.preventDefault();
    
    const id = document.getElementById('kit-id').value;
    const isEdit = id !== '';
    
    const dados = {
        nome: document.getElementById('kit-nome').value,
        descricao: document.getElementById('kit-descricao').value
    };
    
    const url = isEdit ? `/api/kits/${id}` : '/api/kits';
    const method = isEdit ? 'PUT' : 'POST';
    
    const response = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    });
    
    if (response.ok) {
        showToast(isEdit ? '✅ Kit atualizado!' : '✅ Kit criado!', 'success');
        closeModal();
        loadKitsTable(); // Recarrega tabela
    }
}
```

### 3. Renderizar Tabela (`loadKitsTable`)
```javascript
async function loadKitsTable() {
    await loadKits(); // Busca dados
    
    const tbody = document.getElementById('tbody-kits');
    
    if (!window.kits || window.kits.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #999;">Nenhum kit cadastrado</td></tr>';
        return;
    }
    
    tbody.innerHTML = window.kits.map(kit => `
        <tr>
            <td>${kit.nome}</td>
            <td>${kit.descricao || '-'}</td>
            <td>-</td>
            <td>-</td>
            <td>
                <button class="btn-icon" onclick='editarKit(${JSON.stringify(kit).replace(/'/g, "\\'")})'
                    title="Editar">✏️</button>
                <button class="btn-icon" onclick="excluirKit(${kit.id})"
                    title="Excluir" style="color: #e74c3c;">🗑️</button>
            </td>
        </tr>
    `).join('');
}
```

### 4. Corrigir Endpoint POST `/api/kits`
```python
@app.route('/api/kits', methods=['GET', 'POST'])
def kits():
    if request.method == 'GET':
        # ... código atual GET funciona
        
    else:  # POST
        try:
            data = request.json
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO kits (nome, descricao)
                VALUES (%s, %s)
                RETURNING id
            """, (data['nome'], data.get('descricao', '')))
            
            kit_id = cursor.fetchone()
            kit_id = kit_id['id'] if isinstance(kit_id, dict) else kit_id[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Kit criado com sucesso', 'id': kit_id}), 201
        except Exception as e:
            print(f"❌ Erro ao criar kit: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
```

### 5. Corrigir Endpoint PUT `/api/kits/<id>`
```python
@app.route('/api/kits/<int:kit_id>', methods=['PUT', 'DELETE'])
def kit_detalhes(kit_id):
    if request.method == 'PUT':
        try:
            data = request.json
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE kits 
                SET nome = %s, descricao = %s, data_atualizacao = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (data['nome'], data.get('descricao', ''), kit_id))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Kit não encontrado'}), 404
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Kit atualizado com sucesso'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
```

### 6. Corrigir Endpoint DELETE `/api/kits/<id>`
```python
    else:  # DELETE
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM kits WHERE id = %s", (kit_id,))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Kit não encontrado'}), 404
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Kit excluído com sucesso'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
```

---

## 🎯 Checklist de Implementação

- [ ] Criar `openModalKit()` em modals.js
- [ ] Criar `salvarKit()` em modals.js
- [ ] Criar `loadKitsTable()` em app.js para renderizar tabela
- [ ] Criar `editarKit(kit)` para edição
- [ ] Criar `excluirKit(id)` com confirmação
- [ ] Corrigir POST `/api/kits` - implementar query direta
- [ ] Corrigir PUT `/api/kits/<id>` - implementar query direta
- [ ] Corrigir DELETE `/api/kits/<id>` - implementar query direta
- [ ] Chamar `loadKitsTable()` no `showSection('kits-equipamentos')`
- [ ] Remover decorators `@require_permission` dos endpoints PUT/DELETE

---

## 🔄 Fluxo de Uso (Após Implementação)

```
Usuário → Clica "➕ Novo Kit" 
  → openModalKit() → Modal aparece
  → Preenche nome e descrição
  → Clica "Criar Kit" → salvarKit()
  → POST /api/kits → Sucesso
  → loadKitsTable() → Tabela atualizada
```

---

**Última atualização:** 20/01/2026  
**Status:** ⚠️ MÓDULO INCOMPLETO - Precisa implementação
