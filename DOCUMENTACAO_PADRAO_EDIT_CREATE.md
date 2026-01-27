# 📋 Documentação: Padrão Edit vs Create - Prevenção de Duplicação

## 🎯 Problema Recorrente

**SINTOMA**: Ao editar um registro e salvar, o sistema **duplica** o registro ao invés de **atualizar**.

**CAUSA RAIZ**: Funções de salvamento não detectam corretamente se é uma edição (UPDATE) ou criação (INSERT).

---

## ✅ Padrão Correto - CHECKLIST OBRIGATÓRIO

### 1️⃣ **Frontend: Modal de Edição**

#### ✅ Campo Hidden ID (OBRIGATÓRIO)
```html
<form id="form-entidade" onsubmit="salvarEntidade(event)">
    <!-- Campo hidden para ID - ESSENCIAL para detectar modo edição -->
    <input type="hidden" id="entidade-id" value="${isEdit ? entidade.id : ''}">
    
    <!-- Campos adicionais que precisam ser preservados -->
    <input type="hidden" id="entidade-numero" value="${isEdit ? entidade.numero : ''}">
    
    <!-- Resto do formulário -->
</form>
```

#### ✅ Forçar Valor do ID Após Criar Modal
```javascript
// CRÍTICO: Forçar valores no setTimeout para garantir que foram setados
setTimeout(() => {
    const entidadeIdField = document.getElementById('entidade-id');
    const entidadeNumeroField = document.getElementById('entidade-numero');
    
    if (isEdit && entidade) {
        if (entidadeIdField && entidade.id) {
            entidadeIdField.value = entidade.id;
            console.log('✅ ID forçado:', entidade.id);
        }
        if (entidadeNumeroField && entidade.numero) {
            entidadeNumeroField.value = entidade.numero;
            console.log('✅ NUMERO forçado:', entidade.numero);
        }
    }
}, 50);
```

### 2️⃣ **Frontend: Função de Salvamento**

#### ✅ Detecção do Modo (Edit vs Create)
```javascript
async function salvarEntidade(event) {
    event.preventDefault();
    
    // PASSO 1: Recuperar ID do campo hidden
    const id = document.getElementById('entidade-id').value;
    
    // PASSO 2: Detectar modo baseado no ID
    const isEdit = id && id.trim() !== '';
    
    console.log('🎯 Modo:', isEdit ? 'EDIÇÃO' : 'CRIAÇÃO');
    console.log('📋 ID:', id);
    
    // PASSO 3: Coletar dados do formulário
    const data = {
        campo1: document.getElementById('entidade-campo1').value,
        campo2: document.getElementById('entidade-campo2').value,
        // ... outros campos
    };
    
    // PASSO 4: Definir URL e método HTTP corretos
    const url = isEdit ? `/api/entidades/${id}` : '/api/entidades';
    const method = isEdit ? 'PUT' : 'POST';
    
    console.log('🌐 URL:', url);
    console.log('📤 Method:', method);
    console.log('📦 Dados:', data);
    
    // PASSO 5: Fazer requisição
    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            console.log('✅ Sucesso!');
            closeModal();
            loadEntidades(); // Recarregar lista
        } else {
            console.error('❌ Erro:', response.status);
        }
    } catch (error) {
        console.error('❌ Exceção:', error);
    }
}
```

### 3️⃣ **Backend: Rotas Flask**

#### ✅ Rotas Separadas (RECOMENDADO)
```python
@app.route('/api/entidades', methods=['POST'])
def criar_entidade():
    """Criar NOVO registro"""
    data = request.json
    novo_id = db.adicionar_entidade(data)
    return jsonify({"success": True, "id": novo_id}), 201

@app.route('/api/entidades/<int:entidade_id>', methods=['PUT'])
def atualizar_entidade(entidade_id):
    """Atualizar registro EXISTENTE"""
    data = request.json
    success = db.atualizar_entidade(entidade_id, data)
    return jsonify({"success": success}), 200 if success else 500
```

### 4️⃣ **Backend: Funções de Banco**

#### ✅ UPDATE com WHERE id = ?
```python
def atualizar_entidade(entidade_id: int, dados: Dict) -> bool:
    """Atualiza entidade existente"""
    cursor.execute("""
        UPDATE entidades
        SET campo1 = %s, campo2 = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('campo1'),
        dados.get('campo2'),
        entidade_id  # ⚠️ CRÍTICO: WHERE id = entidade_id
    ))
    
    conn.commit()  # ⚠️ CRÍTICO: Não esquecer o commit!
    return True
```

---

## 🚨 Erros Comuns que Causam Duplicação

### ❌ Erro 1: Campo ID Vazio
```javascript
// ERRADO: Campo hidden sem value
<input type="hidden" id="entidade-id">

// CERTO: Campo hidden COM value
<input type="hidden" id="entidade-id" value="${isEdit ? entidade.id : ''}">
```

### ❌ Erro 2: Não Verificar se ID Existe
```javascript
// ERRADO: Assumir que sempre é criação
const url = '/api/entidades';
const method = 'POST';

// CERTO: Verificar se é edição
const id = document.getElementById('entidade-id').value;
const isEdit = id && id.trim() !== '';
const url = isEdit ? `/api/entidades/${id}` : '/api/entidades';
const method = isEdit ? 'PUT' : 'POST';
```

### ❌ Erro 3: Backend Sempre Usa INSERT
```python
# ERRADO: Sempre faz INSERT
def salvar_entidade(dados):
    cursor.execute("INSERT INTO entidades (...) VALUES (...)")

# CERTO: Rotas separadas ou verificar se ID existe
@app.route('/api/entidades/<int:id>', methods=['PUT'])
def atualizar(id):
    cursor.execute("UPDATE entidades SET ... WHERE id = %s", (..., id))
```

### ❌ Erro 4: Esquecer conn.commit()
```python
# ERRADO: UPDATE sem commit = rollback silencioso
cursor.execute("UPDATE entidades SET ... WHERE id = %s", (..., id))
# Sem conn.commit() aqui!

# CERTO: Sempre dar commit após UPDATE/INSERT
cursor.execute("UPDATE entidades SET ... WHERE id = %s", (..., id))
conn.commit()  # ✅ ESSENCIAL!
```

---

## 🔍 Debug: Como Identificar o Problema

### Console Logs Obrigatórios
```javascript
console.log('🎯 Modo:', isEdit ? 'EDIÇÃO' : 'CRIAÇÃO');
console.log('📋 ID do campo hidden:', id);
console.log('🌐 URL da requisição:', url);
console.log('📤 Método HTTP:', method);
console.log('📦 Dados enviados:', data);
```

### Verificar no Network Tab (F12)
1. **URL**: Deve ser `/api/entidades/23` (com ID) para edição
2. **Method**: Deve ser `PUT` para edição, `POST` para criação
3. **Request Payload**: Verificar se dados estão corretos
4. **Response Status**: 200 para sucesso, 500 para erro

### Verificar Logs do Railway/Backend
```
🔍 Atualizando entidade 23 com dados: {...}
UPDATE entidades SET ... WHERE id = 23
✅ Entidade 23 atualizada
```

---

## 📋 Checklist de Implementação

### Ao Implementar Qualquer Modal de Edição:

- [ ] Campo hidden `<input type="hidden" id="entidade-id">` no HTML do modal
- [ ] Valor setado no campo hidden: `value="${isEdit ? entidade.id : ''}"`
- [ ] setTimeout para forçar ID após criar modal
- [ ] Detecção de modo: `const isEdit = id && id.trim() !== '';`
- [ ] URL condicional: `isEdit ? '/api/entidades/${id}' : '/api/entidades'`
- [ ] Método condicional: `isEdit ? 'PUT' : 'POST'`
- [ ] Rota PUT separada no backend: `@app.route('/api/entidades/<int:id>', methods=['PUT'])`
- [ ] UPDATE com WHERE no banco: `UPDATE ... WHERE id = %s`
- [ ] conn.commit() após UPDATE
- [ ] Logs de debug para verificar modo, URL e método

---

## 📚 Histórico de Correções

### ✅ Contratos (Corrigido em 2026-01-26)
- **Problema**: Duplicava ao editar
- **Solução**: Adicionado setTimeout para forçar ID no campo hidden
- **Commit**: `fix: Force ID field value after modal creation to prevent duplicates`

### ✅ Sessões (Pendente Correção)
- **Problema**: Duplicando ao editar (identificado em 2026-01-27)
- **Status**: Em análise
- **Próximos passos**: Aplicar mesmo padrão de Contratos

---

## 🎯 Resumo Executivo

**REGRA DE OURO**: 
- **TEM ID no campo hidden?** → PUT para `/api/entidades/ID` → UPDATE no banco
- **NÃO TEM ID?** → POST para `/api/entidades` → INSERT no banco

**NUNCA ESQUECER**:
1. Campo hidden com ID
2. setTimeout para forçar valor
3. Verificar `isEdit` antes de definir URL/método
4. Rotas PUT separadas no backend
5. WHERE id = ? no UPDATE
6. conn.commit() após modificações

---

**Última atualização**: 27/01/2026  
**Versão**: 1.0  
**Responsável**: Sistema de Prevenção de Duplicações
