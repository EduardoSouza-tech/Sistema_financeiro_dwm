# 🛡️ Guia de CSRF Protection + Mobile Responsivo

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [CSRF Protection](#csrf-protection)
3. [Detecção Mobile](#detecção-mobile)
4. [Configuração](#configuração)
5. [Testes](#testes)

---

## 🎯 Visão Geral

### O que foi implementado

1. **CSRF Protection** - Proteção contra Cross-Site Request Forgery
2. **Mobile Detection** - Detecção básica de dispositivos mobile para interface responsiva

### Arquitetura Simplificada

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA FINANCEIRO                        │
│                                                              │
│  ┌────────────────────┐        ┌──────────────────────┐    │
│  │  CSRF Protection   │        │  Mobile Detection    │    │
│  │  (Flask-WTF)       │        │  (User-Agent)        │    │
│  │                    │        │                      │    │
│  │  • Token único     │        │  • Detecta mobile    │    │
│  │  • Por sessão      │        │  • Web responsivo    │    │
│  │  • Auto-validação  │        │  • Mesma interface   │    │
│  └────────────────────┘        └──────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            WEB SERVER (Flask)                        │  │
│  │  • Todas as rotas protegidas com CSRF                │  │
│  │  • Interface responsiva para mobile/desktop          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ CSRF Protection

### Como Funciona

1. **Geração de Token**
   - Token único gerado para cada sessão
   - Incluído automaticamente em todos os formulários
   - Validado em todas as requisições POST/PUT/DELETE

2. **Validação Automática**
   ```python
   # O token é validado automaticamente pelo Flask-WTF
   # Não precisa fazer nada manualmente!
   ```

3. **Configuração**
   ```python
   # csrf_config.py
   WTF_CSRF_ENABLED = True
   WTF_CSRF_TIME_LIMIT = None  # Token não expira
   WTF_CSRF_SSL_STRICT = False  # Permite HTTP em dev
   WTF_CSRF_METHODS = ['POST', 'PUT', 'DELETE', 'PATCH']
   ```

### Uso nos Templates

#### HTML Forms

```html
<form method="POST" action="/api/lancamentos">
    <!-- Token CSRF inserido automaticamente -->
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    
    <input type="text" name="descricao">
    <button type="submit">Salvar</button>
</form>
```

#### JavaScript / AJAX

```javascript
// Obter token CSRF do meta tag
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

// Incluir em requisições AJAX
fetch('/api/lancamentos', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        descricao: 'Pagamento',
        valor: 100.00
    })
});
```

#### Fetch API Configurado

```javascript
// Função helper para incluir CSRF automaticamente
async function fetchWithCSRF(url, options = {}) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    };
    
    return fetch(url, { ...defaultOptions, ...options });
}

// Usar assim:
await fetchWithCSRF('/api/lancamentos', {
    method: 'POST',
    body: JSON.stringify(data)
});
```

### Rotas Protegidas

Todas as rotas com métodos POST/PUT/DELETE são automaticamente protegidas:

```python
@app.route('/api/lancamentos', methods=['POST'])
def criar_lancamento():
    # CSRF validado automaticamente
    # Se token inválido, retorna 400 Bad Request
    ...
```

### Tratamento de Erros

```python
# Erro CSRF retorna:
{
    "success": false,
    "error": "CSRF token missing or invalid",
    "message": "Token de segurança inválido ou ausente"
}
```

No frontend:
```javascript
fetch('/api/lancamentos', { method: 'POST', ... })
    .then(response => {
        if (!response.ok && response.status === 400) {
            // Possível erro CSRF
            alert('Erro de segurança. Por favor, recarregue a página.');
            location.reload();
        }
        return response.json();
    });
```

---

## 📱 Detecção Mobile

### Como Funciona

Detecção simples baseada em **User-Agent** do navegador:

```python
# mobile_config.py
def is_mobile_device():
    """Detecta se é mobile pelo User-Agent"""
    user_agent = request.headers.get('User-Agent', '')
    
    # Verifica palavras-chave: Android, iPhone, iPad, etc
    if MOBILE_PATTERN.search(user_agent):
        return True
    
    return False
```

### Dispositivos Detectados

- ✅ Android
- ✅ iPhone / iPad / iPod
- ✅ Windows Phone
- ✅ BlackBerry
- ✅ Opera Mini
- ✅ Outros navegadores mobile

### Uso no Backend

```python
from mobile_config import is_mobile_device, get_device_info

@app.route('/alguma-rota')
def minha_rota():
    if is_mobile_device():
        # Usuário está em mobile
        device_info = get_device_info()
        print(f"Dispositivo: {device_info['type']}")
    
    return render_template('template.html')
```

### Uso nos Templates

```html
{% if is_mobile %}
    <div class="mobile-view">
        <!-- Layout simplificado para mobile -->
    </div>
{% else %}
    <div class="desktop-view">
        <!-- Layout completo -->
    </div>
{% endif %}
```

### CSS Responsivo

```css
/* Sempre use media queries para melhor controle */
@media (max-width: 768px) {
    .container {
        padding: 10px;
        font-size: 14px;
    }
    
    .table {
        font-size: 12px;
    }
}

@media (max-width: 480px) {
    .container {
        padding: 5px;
    }
    
    /* Esconder colunas menos importantes em telas pequenas */
    .table th:nth-child(3),
    .table td:nth-child(3) {
        display: none;
    }
}
```

### Meta Tags para Mobile

```html
<!-- Incluir no <head> de todos os templates -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
```

---

## ⚙️ Configuração

### 1. Variáveis de Ambiente

```bash
# .env
SECRET_KEY=seu-secret-key-aqui-muito-seguro-123456
DATABASE_URL=postgresql://usuario:senha@host:5432/banco
FLASK_ENV=development  # ou production
```

### 2. Requirements

```txt
# Instalados via pip install -r requirements.txt
Flask==3.0.0
Flask-WTF==1.2.1      # CSRF Protection
Flask-CORS==4.0.0
psycopg2-binary==2.9.9
```

### 3. Inicialização no web_server.py

```python
from flask import Flask
from csrf_config import init_csrf, register_csrf_error_handlers
from mobile_config import is_mobile_device, get_device_info

app = Flask(__name__)

# Secret key para sessões e CSRF
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Inicializar CSRF
csrf = init_csrf(app)
register_csrf_error_handlers(app)

# Detecção mobile disponível em todos os templates
@app.context_processor
def inject_mobile():
    return {
        'is_mobile': is_mobile_device(),
        'device_info': get_device_info()
    }
```

---

## 🧪 Testes

### Testar CSRF Protection

#### 1. Requisição SEM token (deve falhar)

```bash
curl -X POST http://localhost:5000/api/lancamentos \
  -H "Content-Type: application/json" \
  -d '{"descricao": "Teste", "valor": 100}'

# Esperado: 400 Bad Request
# {"success": false, "error": "CSRF token missing"}
```

#### 2. Requisição COM token (deve funcionar)

```bash
# Primeiro, obter o token (simular navegador)
curl -c cookies.txt http://localhost:5000/

# Extrair token do HTML ou meta tag
TOKEN="obtido-do-html"

# Fazer requisição com token
curl -X POST http://localhost:5000/api/lancamentos \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $TOKEN" \
  -d '{"descricao": "Teste", "valor": 100}'

# Esperado: 200 OK ou 201 Created
```

#### 3. Testar no Browser

```javascript
// Abrir Console do navegador (F12)

// 1. Verificar se token existe
console.log(document.querySelector('meta[name="csrf-token"]').content);

// 2. Fazer requisição de teste
fetch('/api/lancamentos', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
    },
    body: JSON.stringify({
        descricao: 'Teste CSRF',
        valor: 100.00,
        tipo: 'DESPESA'
    })
})
.then(r => r.json())
.then(data => console.log('Sucesso:', data))
.catch(err => console.error('Erro:', err));
```

### Testar Detecção Mobile

#### 1. Simular Mobile no Browser

1. Abrir DevTools (F12)
2. Clicar em "Toggle Device Toolbar" (Ctrl+Shift+M)
3. Selecionar dispositivo (iPhone, iPad, Galaxy, etc)
4. Recarregar página
5. Verificar se layout está responsivo

#### 2. Testar User-Agent

```bash
# Simular iPhone
curl http://localhost:5000/ \
  -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"

# Simular Android
curl http://localhost:5000/ \
  -H "User-Agent: Mozilla/5.0 (Linux; Android 10; SM-G973F)"

# Desktop
curl http://localhost:5000/ \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
```

#### 3. Script de Teste Python

```python
# teste_mobile_detection.py
from mobile_config import is_mobile_device
from flask import Flask, request

app = Flask(__name__)

@app.route('/test')
def test():
    return {
        'is_mobile': is_mobile_device(),
        'user_agent': request.headers.get('User-Agent'),
        'device_info': get_device_info()
    }

if __name__ == '__main__':
    with app.test_request_context(
        headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)'}
    ):
        print("iPhone:", is_mobile_device())  # Deve ser True
    
    with app.test_request_context(
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    ):
        print("Desktop:", is_mobile_device())  # Deve ser False
```

---

## 🔒 Segurança

### Boas Práticas CSRF

✅ **SEMPRE incluir token CSRF em:**
- Formulários HTML
- Requisições AJAX POST/PUT/DELETE
- Chamadas de API que modificam dados

✅ **Usar HTTPS em produção:**
```python
app.config['SESSION_COOKIE_SECURE'] = True  # Apenas HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Não acessível via JS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protege contra CSRF
```

✅ **Regenerar token após login:**
```python
from flask import session

@app.route('/login', methods=['POST'])
def login():
    # ... autenticar usuário ...
    
    # Regenerar sessão (inclui novo token CSRF)
    session.clear()
    session['user_id'] = user.id
    session.modified = True
```

❌ **NUNCA:**
- Incluir token CSRF em URLs (pode vazar em logs)
- Desabilitar CSRF em produção
- Usar tokens fixos ou previsíveis
- Permitir GET para ações que modificam dados

### Limitações da Detecção Mobile

⚠️ **Detecção por User-Agent não é 100% confiável:**
- User-Agents podem ser falsificados
- Alguns dispositivos podem não ser detectados
- **Use apenas para melhorar UX, não para segurança**

✅ **Sempre use CSS Media Queries como principal método:**
```css
@media (max-width: 768px) {
    /* Mobile styles */
}
```

✅ **Detecção server-side é apenas complementar:**
- Para logs/analytics
- Para servir assets diferentes
- Para otimizações de performance

---

## 📚 Referências

- [Flask-WTF Documentation](https://flask-wtf.readthedocs.io/)
- [OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [MDN: Responsive Design](https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design)
- [Can I Use: CSS Media Queries](https://caniuse.com/css-mediaqueries)

---

## 🆘 Troubleshooting

### Erro: "CSRF token missing"

**Causa:** Token não está sendo enviado na requisição

**Solução:**
```javascript
// Incluir token em TODAS as requisições POST/PUT/DELETE
const token = document.querySelector('meta[name="csrf-token"]').content;
fetch('/api/endpoint', {
    method: 'POST',
    headers: { 'X-CSRFToken': token }
});
```

### Erro: "CSRF token invalid"

**Causa:** Token expirado ou sessão perdida

**Solução:**
- Recarregar a página para obter novo token
- Verificar se cookies estão habilitados
- Aumentar tempo de sessão se necessário

### Mobile não está sendo detectado

**Causa:** User-Agent não reconhecido ou bloqueado

**Solução:**
1. Verificar User-Agent: `request.headers.get('User-Agent')`
2. Adicionar padrão ao regex se necessário
3. **Preferir CSS media queries**

### Layout quebrado no mobile

**Causa:** CSS não está responsivo

**Solução:**
```html
<!-- Adicionar meta viewport -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

```css
/* Adicionar media queries */
@media (max-width: 768px) {
    .container { padding: 10px; }
}
```

---

**🎉 Sistema configurado e protegido!**

Para dúvidas ou problemas, consulte os logs do sistema ou a documentação do Flask-WTF.
