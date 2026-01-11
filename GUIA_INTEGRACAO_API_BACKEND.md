# 📘 Guia Completo de Integração API + Backend + Banco de Dados

## 🎯 Objetivo
Este guia documenta a arquitetura e o fluxo correto para integrar frontend, API, backend e banco de dados, evitando erros comuns.

---

## 📐 Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (HTML/JS)                       │
│                      (admin.html, app.js)                        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ HTTP Requests (fetch/axios)
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                      API LAYER (Flask)                           │
│                      (web_server.py)                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Decorators (@require_auth, @require_admin, etc.)          │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Routes (@app.route('/api/...'))                           │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ Function Calls
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                           │
│              (database_postgresql.py, database.py)               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  DatabaseManager Class                                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  CRUD Functions (adicionar_*, listar_*, etc.)              │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ SQL Queries (psycopg2)
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                   DATABASE LAYER (PostgreSQL)                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Tables: usuarios, clientes, fornecedores, lancamentos,    │ │
│  │          contas_bancarias, categorias, etc.                │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo Correto de Requisição

### **Exemplo: Listar Clientes**

#### **1. Frontend → API** 
```javascript
// admin.html ou app.js
async function loadClientes() {
    try {
        const response = await fetch('/api/clientes', {
            method: 'GET',
            credentials: 'include'  // ✅ IMPORTANTE: Enviar cookies
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // ✅ SEMPRE verificar estrutura de resposta
        if (Array.isArray(data)) {
            return data;
        } else if (data.clientes && Array.isArray(data.clientes)) {
            return data.clientes;
        } else if (data.success && data.clientes) {
            return data.clientes;
        }
        
        console.error('Formato inesperado:', data);
        return [];
    } catch (error) {
        console.error('Erro ao carregar clientes:', error);
        return [];
    }
}
```

#### **2. API Layer → Decorator**
```python
# web_server.py
@app.route('/api/clientes', methods=['GET'])
@require_permission('clientes_view')  # ✅ Verifica permissão
@aplicar_filtro_cliente                # ✅ Aplica filtro multi-tenancy
def listar_clientes():
    """Lista clientes ativos ou inativos com filtro de multi-tenancy"""
    try:
        # ✅ Obter parâmetros da query string
        ativos = request.args.get('ativos', 'true').lower() == 'true'
        
        # ✅ Obter filtro de multi-tenancy (setado pelo decorator)
        filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
```

#### **3. API Layer → Business Logic**
```python
        # ✅ Chamar função do banco com parâmetros corretos
        clientes = db.listar_clientes(
            ativos=ativos,
            filtro_cliente_id=filtro_cliente_id
        )
        
        # ✅ SEMPRE retornar estrutura padronizada
        return jsonify(clientes)  # ou jsonify({'success': True, 'clientes': clientes})
        
    except Exception as e:
        # ✅ SEMPRE capturar e logar exceções
        print(f"❌ Erro em /api/clientes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
```

#### **4. Business Logic → Database**
```python
# database_postgresql.py
def listar_clientes(self, ativos: bool = True, filtro_cliente_id: int = None) -> List[Dict]:
    """Lista todos os clientes com suporte a multi-tenancy"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    try:
        # ✅ Construir query com filtros condicionais
        if filtro_cliente_id is not None:
            # Cliente específico: ver apenas seus próprios clientes
            if ativos:
                cursor.execute(
                    "SELECT * FROM clientes WHERE ativo = TRUE AND proprietario_id = %s ORDER BY nome",
                    (filtro_cliente_id,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM clientes WHERE proprietario_id = %s ORDER BY nome",
                    (filtro_cliente_id,)
                )
        else:
            # Admin: ver todos os clientes
            if ativos:
                cursor.execute("SELECT * FROM clientes WHERE ativo = TRUE ORDER BY nome")
            else:
                cursor.execute("SELECT * FROM clientes ORDER BY nome")
        
        rows = cursor.fetchall()
        
        # ✅ Converter RealDictRow para dict
        clientes = [dict(row) for row in rows]
        
        return clientes
        
    finally:
        # ✅ SEMPRE fechar cursor e conexão
        cursor.close()
        conn.close()
```

---

## ✅ Checklist de Implementação

### **Ao Criar Nova Funcionalidade**

#### **1. Banco de Dados (database_postgresql.py)**
- [ ] Criar/atualizar tabela no método `criar_tabelas()`
- [ ] Adicionar coluna `proprietario_id` se for recurso com multi-tenancy
- [ ] Criar função `adicionar_*()` com parâmetro `proprietario_id`
- [ ] Criar função `listar_*()` com parâmetro `filtro_cliente_id`
- [ ] Criar funções `atualizar_*()` e `excluir_*()`
- [ ] SEMPRE usar `try/finally` para fechar conexões
- [ ] SEMPRE usar consultas parametrizadas (evitar SQL injection)

```python
# ✅ CORRETO
cursor.execute("SELECT * FROM clientes WHERE nome = %s", (nome,))

# ❌ ERRADO (SQL Injection!)
cursor.execute(f"SELECT * FROM clientes WHERE nome = '{nome}'")
```

#### **2. API Layer (web_server.py)**
- [ ] Criar rota com `@app.route('/api/recurso', methods=['GET', 'POST'])`
- [ ] Adicionar decorators apropriados:
  - `@require_auth` - Requer login
  - `@require_admin` - Apenas admin
  - `@require_permission('permissao_view')` - Requer permissão específica
  - `@aplicar_filtro_cliente` - Aplica filtro multi-tenancy
- [ ] Validar entrada (request.json, request.args)
- [ ] Chamar função do banco com parâmetros corretos
- [ ] Capturar exceções com try/except
- [ ] Retornar JSON padronizado: `{'success': True, 'data': ...}`
- [ ] Logar erros com traceback

```python
@app.route('/api/recurso', methods=['GET'])
@require_permission('recurso_view')
@aplicar_filtro_cliente
def listar_recurso():
    try:
        # Obter parâmetros
        filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
        
        # Chamar banco
        dados = db.listar_recurso(filtro_cliente_id=filtro_cliente_id)
        
        # Retornar
        return jsonify(dados)
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
```

#### **3. Frontend (admin.html, app.js)**
- [ ] Usar `fetch()` com `credentials: 'include'`
- [ ] Verificar `response.ok` antes de processar
- [ ] Tratar múltiplos formatos de resposta (array direto ou objeto wrapper)
- [ ] Capturar e exibir erros para o usuário
- [ ] Mostrar loading/spinner durante requisições

```javascript
async function loadData() {
    try {
        const response = await fetch('/api/recurso', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Tratar diferentes formatos
        let items = [];
        if (Array.isArray(data)) {
            items = data;
        } else if (data.items) {
            items = data.items;
        } else if (data.success && data.data) {
            items = data.data;
        }
        
        return items;
    } catch (error) {
        console.error('Erro:', error);
        alert(`Erro ao carregar dados: ${error.message}`);
        return [];
    }
}
```

---

## 🔐 Autenticação e Sessão

### **Problema Comum: Session Token Não Encontrado**

**Causa:** Cookie está com nome "session" mas Flask busca `session.get('session_token')`

**Solução:**
```python
# auth_middleware.py
def get_usuario_logado():
    # Primeiro: tentar session dict
    token = session.get('session_token')
    
    if not token:
        # Fallback: tentar cookie direto
        session_cookie = request.cookies.get('session')
        if session_cookie:
            # Decodificar cookie do Flask (é JSON em base64)
            try:
                import json, base64
                decoded = json.loads(base64.b64decode(session_cookie))
                token = decoded.get('session_token')
            except:
                pass
    
    if not token:
        return None
    
    return auth_db.validar_sessao(token)
```

### **Fluxo de Login**
```python
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Validar credenciais
    usuario = auth_db.validar_login(username, password)
    if not usuario:
        return jsonify({'success': False, 'error': 'Credenciais inválidas'}), 401
    
    # Criar sessão
    token = auth_db.criar_sessao(usuario['id'])
    
    # ✅ Salvar token na session
    session['session_token'] = token
    session.permanent = True
    
    return jsonify({
        'success': True,
        'usuario': {
            'id': usuario['id'],
            'username': usuario['username'],
            'tipo': usuario['tipo'],
            'nome_completo': usuario['nome_completo']
        }
    })
```

---

## 🐛 Debugging e Logs

### **Estrutura de Logs**
```python
# No início da função
print(f"\n{'='*80}")
print(f"🔍 DEBUG - {request.method} {request.path}")
print(f"{'='*80}")

# Durante processamento
print(f"   Parâmetro X: {valor_x}")
print(f"   ✅ Sucesso na etapa Y")
print(f"   ⚠️ Aviso: Condição Z")

# Ao capturar erro
print(f"❌ Erro em {request.path}: {e}")
import traceback
traceback.print_exc()

# No final
print(f"{'='*80}\n")
```

### **Frontend Debug**
```javascript
console.log('🔍 DEBUG - Chamando API:', url);
console.log('   Parâmetros:', params);
console.log('   Resposta:', response);
console.log('   Dados:', data);
```

---

## 🚫 Erros Comuns e Como Evitar

### **1. Erro 500 - Internal Server Error**
**Causa:** Exceção não tratada no backend
**Solução:** SEMPRE usar try/except e logar traceback

### **2. Erro 401 - Unauthorized**
**Causa:** Token de sessão inválido ou ausente
**Solução:** Verificar `credentials: 'include'` no fetch e implementar refresh de token

### **3. Erro 404 - Not Found**
**Causa:** Rota não existe ou URL errada
**Solução:** Verificar exatamente o caminho da rota no `@app.route()`

### **4. TypeError: Cannot read properties of null**
**Causa:** Elemento HTML não existe quando JavaScript tenta acessá-lo
**Solução:** Verificar se elemento existe antes de usar
```javascript
const element = document.getElementById('myElement');
if (element) {
    element.value = 'teste';
} else {
    console.warn('Elemento não encontrado: myElement');
}
```

### **5. IndentationError**
**Causa:** Mistura de tabs e espaços ou indentação incorreta
**Solução:** Configurar editor para usar 4 espaços, nunca tabs

### **6. Relation "tabela" does not exist**
**Causa:** Tabela não foi criada no banco
**Solução:** Adicionar criação da tabela em `criar_tabelas()`

---

## 📊 Padrões de Resposta da API

### **Sucesso (200 OK)**
```json
{
  "success": true,
  "data": [...],
  "message": "Operação realizada com sucesso"
}
```

### **Erro do Cliente (400 Bad Request)**
```json
{
  "success": false,
  "error": "Parâmetro 'nome' é obrigatório"
}
```

### **Não Autorizado (401 Unauthorized)**
```json
{
  "success": false,
  "error": "Sessão expirada",
  "redirect": "/login"
}
```

### **Proibido (403 Forbidden)**
```json
{
  "success": false,
  "error": "Você não tem permissão para acessar este recurso"
}
```

### **Erro do Servidor (500 Internal Server Error)**
```json
{
  "success": false,
  "error": "Erro interno do servidor. Contate o administrador."
}
```

---

## 🔧 Ferramentas de Debug

### **1. Logs do Railway**
```bash
railway logs -f
```

### **2. Console do Navegador**
```javascript
// F12 → Console
console.table(data);  // Exibir dados em tabela
console.trace();      // Rastrear chamadas
```

### **3. Breakpoints no Código**
```python
# Adicionar para pausar execução
import pdb; pdb.set_trace()
```

### **4. Teste de Endpoints com cURL**
```bash
# Testar GET
curl -X GET http://localhost:5000/api/clientes \
  -H "Cookie: session=..." \
  -v

# Testar POST
curl -X POST http://localhost:5000/api/clientes \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"nome": "Teste"}' \
  -v
```

---

## 📝 Template de Nova Funcionalidade

### **1. database_postgresql.py**
```python
def adicionar_recurso(self, dados: Dict, proprietario_id: int = None) -> int:
    """Adiciona novo recurso"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO recursos (campo1, campo2, proprietario_id)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (dados['campo1'], dados['campo2'], proprietario_id))
        
        recurso_id = cursor.fetchone()['id']
        conn.commit()
        return recurso_id
    finally:
        cursor.close()
        conn.close()

def listar_recursos(self, filtro_cliente_id: int = None) -> List[Dict]:
    """Lista recursos com multi-tenancy"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    try:
        if filtro_cliente_id is not None:
            cursor.execute(
                "SELECT * FROM recursos WHERE proprietario_id = %s ORDER BY id",
                (filtro_cliente_id,)
            )
        else:
            cursor.execute("SELECT * FROM recursos ORDER BY id")
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()
```

### **2. web_server.py**
```python
@app.route('/api/recursos', methods=['GET', 'POST'])
@require_permission('recursos_view')
@aplicar_filtro_cliente
def gerenciar_recursos():
    """Listar ou criar recursos"""
    filtro_cliente_id = getattr(request, 'filtro_cliente_id', None)
    
    if request.method == 'GET':
        try:
            recursos = db.listar_recursos(filtro_cliente_id=filtro_cliente_id)
            return jsonify(recursos)
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            dados = request.json
            recurso_id = db.adicionar_recurso(dados, proprietario_id=filtro_cliente_id)
            return jsonify({'success': True, 'id': recurso_id})
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 400
```

### **3. admin.html / app.js**
```javascript
async function loadRecursos() {
    try {
        const response = await fetch('/api/recursos', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        return Array.isArray(data) ? data : (data.recursos || []);
    } catch (error) {
        console.error('Erro ao carregar recursos:', error);
        alert(`Erro: ${error.message}`);
        return [];
    }
}

async function createRecurso(dados) {
    try {
        const response = await fetch('/api/recursos', {
            method: 'POST',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(dados)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            alert('Recurso criado com sucesso!');
            await loadRecursos();
        } else {
            throw new Error(result.error || 'Erro desconhecido');
        }
    } catch (error) {
        console.error('Erro ao criar recurso:', error);
        alert(`Erro: ${error.message}`);
    }
}
```

---

## 🎓 Conclusão

**Regras de Ouro:**

1. ✅ **SEMPRE** fechar conexões do banco
2. ✅ **SEMPRE** usar try/except e logar erros
3. ✅ **SEMPRE** validar entrada do usuário
4. ✅ **SEMPRE** usar consultas parametrizadas
5. ✅ **SEMPRE** retornar JSON padronizado
6. ✅ **SEMPRE** aplicar decorators de segurança
7. ✅ **SEMPRE** testar com admin E cliente
8. ✅ **SEMPRE** verificar logs após deploy

**Em caso de dúvida, siga este guia passo a passo!**
