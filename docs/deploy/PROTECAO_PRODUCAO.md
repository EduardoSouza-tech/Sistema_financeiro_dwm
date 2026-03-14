# 🔐 Proteção de Endpoints de Debug em Produção

## ⚠️ Problema Crítico RESOLVIDO

**ANTES:** Endpoints de debug estavam acessíveis via HTTP em produção
- ❌ `/api/debug/criar-admin` - Criar admin sem autenticação
- ❌ `/api/debug/fix-kits-table` - Executar migrations via HTTP
- ❌ `/api/debug/fix-p1-issues` - Modificar schema via HTTP

**Risco:** Qualquer pessoa com acesso à URL poderia executar operações críticas

## ✅ Solução Implementada

### 1. Detecção de Ambiente
```python
# web_server.py
IS_PRODUCTION = bool(os.getenv('RAILWAY_ENVIRONMENT'))
```

### 2. Endpoints de Debug Bloqueados em Produção
```python
# Endpoints retornam 403 Forbidden em produção
if IS_PRODUCTION:
    return jsonify({
        'success': False,
        'error': 'Endpoints de debug não disponíveis em produção'
    }), 403
```

### 3. CSRF Exempt List Dinâmica
```python
CSRF_EXEMPT_ROUTES = [
    '/api/auth/login',
    '/api/auth/logout',
    '/api/auth/register'
]

# Debug endpoints APENAS em desenvolvimento
if not IS_PRODUCTION:
    CSRF_EXEMPT_ROUTES.extend([
        '/api/debug/fix-kits-table',
        '/api/debug/fix-p1-issues',
        '/api/debug/criar-admin'
    ])
```

## 🛠️ Como Usar em Produção

### Criar Admin (Método Seguro)

**❌ ANTES (Inseguro):**
```bash
curl -X POST https://seu-app.railway.app/api/debug/criar-admin
```

**✅ AGORA (Seguro):**
```bash
# SSH no container Railway
railway run python criar_admin_seguro.py

# Ou localmente com acesso ao banco
python criar_admin_seguro.py --username admin
```

### Exemplos de Uso

```bash
# Modo interativo (recomendado)
python criar_admin_seguro.py

# Especificar username
python criar_admin_seguro.py --username admin

# Listar admins existentes
python criar_admin_seguro.py --list

# Resetar senha de admin existente
python criar_admin_seguro.py --reset admin

# Com senha na linha de comando (menos seguro)
python criar_admin_seguro.py --username admin --password "SenhaForte123!"
```

## 📊 Status dos Endpoints

### ✅ Funcionam em Produção
```
GET  /api/auth/session           - Verificar sessão
POST /api/auth/login             - Login (rate limited)
POST /api/auth/logout            - Logout
POST /api/auth/register          - Registro
GET  /api/admin/passwords/...    - Gestão de senhas (@require_admin)
```

### 🚫 Bloqueados em Produção
```
POST /api/debug/criar-admin      - Usar criar_admin_seguro.py
POST /api/debug/fix-kits-table   - Usar migrations adequadas
POST /api/debug/fix-p1-issues    - Usar migrations adequadas
```

### 💻 Disponíveis em Desenvolvimento
```
Todos os endpoints acima funcionam normalmente em ambiente local
```

## 🔍 Como Verificar o Ambiente

```python
# No código
IS_PRODUCTION = bool(os.getenv('RAILWAY_ENVIRONMENT'))

# No terminal (Railway)
echo $RAILWAY_ENVIRONMENT  # Retorna algo se estiver no Railway

# No terminal (local)
echo $RAILWAY_ENVIRONMENT  # Vazio ou não definido
```

## 📝 Logs

### Em Desenvolvimento
```
⚠️ Endpoints de DEBUG habilitados (ambiente de desenvolvimento)
```

### Em Produção
```
🔒 Endpoints de DEBUG desabilitados (ambiente de produção)
```

### Tentativa de Acesso Bloqueada
```json
{
  "success": false,
  "error": "Endpoints de debug não disponíveis em produção",
  "message": "Use migrations adequadas ou console admin"
}
```

## 🔒 Segurança Adicional

### Validação de Senha Forte
O script `criar_admin_seguro.py` exige:
- ✅ Mínimo 8 caracteres
- ✅ Pelo menos 1 letra maiúscula
- ✅ Pelo menos 1 letra minúscula
- ✅ Pelo menos 1 número
- ✅ Pelo menos 1 caractere especial

### Bcrypt
- ✅ Hashes gerados com bcrypt (não SHA-256)
- ✅ Salt automático
- ✅ Proteção contra brute force

### Confirmação Interativa
```bash
$ python criar_admin_seguro.py --reset admin

⚠️  Usuário 'admin' já existe (ID: 1)
   Deseja RESETAR a senha? [s/N]: s
```

## 🚀 Deploy Checklist

Antes de fazer deploy:

- [x] Verificar que `IS_PRODUCTION` está configurado
- [x] Testar endpoints de debug retornam 403
- [x] Testar `criar_admin_seguro.py` funciona
- [x] Documentar processo para equipe
- [x] Remover senhas hardcoded do código
- [x] Configurar variáveis de ambiente no Railway

## 📚 Referências

- Script: [criar_admin_seguro.py](criar_admin_seguro.py)
- Web Server: [web_server.py](web_server.py#L130-L150)
- Documentação: [GUIA_USO_ATUALIZACOES.md](GUIA_USO_ATUALIZACOES.md)

---

**Data:** 22/01/2026  
**Prioridade:** 🔴 CRÍTICA  
**Status:** ✅ IMPLEMENTADO
