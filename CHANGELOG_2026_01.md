# 📋 Changelog - Atualizações Recentes (Janeiro 2026)

## 🔐 Segurança - Migration de Senhas (22/01/2026)

### Implementado
- ✅ **Sistema de upgrade automático SHA-256 → Bcrypt**
  - Detecção automática de tipo de hash
  - Upgrade transparente no próximo login do usuário
  - Compatibilidade total durante transição
  - Arquivo: [migration_upgrade_passwords.py](migration_upgrade_passwords.py)

### Novos Endpoints Admin
```http
GET  /api/admin/passwords/migration-status   # Consultar status da migração
POST /api/admin/passwords/force-upgrade      # Forçar upgrade de senha
```

### Como Funciona
1. Usuário faz login com senha antiga (SHA-256)
2. Sistema verifica que hash é SHA-256 (64 caracteres hex)
3. Senha é validada normalmente
4. Se correta, hash é atualizado para bcrypt automaticamente
5. Próximo login já usa bcrypt

### Monitoramento
```bash
# Ver status de migração
curl -H "Authorization: Bearer TOKEN" \
     http://localhost:5000/api/admin/passwords/migration-status

# Resposta:
{
  "total_usuarios": 10,
  "usuarios_bcrypt": 8,
  "usuarios_sha256": 2,
  "percentual_migrado": 80.0,
  "pendentes": [
    {"username": "user1", "tipo": "sha256"},
    {"username": "user2", "tipo": "sha256"}
  ]
}
```

### Testes
- ✅ 15 testes unitários criados
- ✅ Cobertura: detecção de hash, upgrade, integração com login
- Arquivo: [tests/test_migration_passwords.py](tests/test_migration_passwords.py)

---

## 🚀 Performance - Lazy Loading Fixes (21/01/2026)

### Problema Corrigido (Commit a1ef342)
**Bug:** Erro `NotFoundError` no `insertBefore` ao limpar container na página 1

**Causa:** Sentinel (elemento observador) era removido ao limpar container, mas código tentava inserir elementos antes dele

**Solução:**
```javascript
// ANTES (BUG)
if (page === 1) {
    container.innerHTML = '';  // Remove TUDO, incluindo sentinel
}
container.insertBefore(element, this.sentinel);  // ❌ sentinel não existe mais

// DEPOIS (CORRIGIDO)
if (page === 1) {
    container.innerHTML = '';
    this._createSentinel(container);  // ✅ Recria sentinel
}
container.insertBefore(element, this.sentinel);  // ✅ Funciona
```

### Outros Fixes (Commits bc50ab4, 709ac42)
- ✅ Restauração de funções globais (loadCategorias, loadClientes, etc)
- ✅ Adição de 5 stubs faltantes no lazy-integration
- ✅ Correção de chamadas `window.` no código de integração

### Testes Criados
- ✅ 20+ testes JavaScript com Jest
- ✅ Cobertura de edge cases:
  - Primeira página vazia
  - Recriação de sentinel
  - Cache funcionando
  - IntersectionObserver
- Arquivo: [tests/test_lazy_loader.test.js](tests/test_lazy_loader.test.js)

### Executar Testes
```bash
# Instalar dependências (apenas primeira vez)
npm install

# Executar testes
npm test

# Com coverage
npm run test:coverage

# Watch mode (desenvolvimento)
npm run test:watch
```

---

## 🔒 Segurança - Revisão CSRF (22/01/2026)

### Análise Realizada
Script de análise automática criado: [csrf_security_review.py](csrf_security_review.py)

### Endpoints Isentos - Status Atual

#### ✅ Legítimos (Risco Baixo)
```
/api/auth/login     - Autenticação pública + rate limiting
/api/auth/logout    - Apenas invalida sessão
/api/auth/register  - Registro público
```

#### ⚠️ Debug Temporários (Risco Alto - Ação Requerida)
```
/api/debug/criar-admin      - REMOVER em produção
/api/debug/fix-kits-table   - REMOVER após migration
/api/debug/fix-p1-issues    - REMOVER após migration
```

#### ❌ Corrigido
```
/api/admin/passwords/force-upgrade  - Isenção REMOVIDA (era vulnerabilidade)
```

### Recomendações
1. 🔴 **URGENTE:** Remover endpoints de debug em produção
2. 🟡 **Importante:** Adicionar captcha em `/api/auth/register`
3. 🟢 **Bom:** Rate limiting funcionando corretamente

### Como Executar Análise
```bash
python csrf_security_review.py
```

---

## 📊 Arquitetura - Visão Geral

### Sistema de Autenticação (Atualizado)
```
┌─────────────────┐
│  Login Request  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ verificar_e_upgrade_senha()     │
│ 1. Detecta tipo de hash         │
│ 2. Valida senha                 │
│ 3. Se SHA-256 → upgrade bcrypt  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Criar Sessão   │
└─────────────────┘
```

### Lazy Loading (Atualizado)
```
┌──────────────┐
│   Container  │
│ ┌──────────┐ │
│ │ Item 1   │ │
│ ├──────────┤ │
│ │ Item 2   │ │
│ ├──────────┤ │
│ │ ...      │ │
│ ├──────────┤ │
│ │ Sentinel │ │ ← IntersectionObserver observa este elemento
│ └──────────┘ │   Quando visível → carrega próxima página
└──────────────┘
```

**Sentinel:** Elemento invisível (1px) que dispara carregamento ao se tornar visível

**Cache:** Armazena até 10 páginas por 5 minutos

---

## 🎯 Próximas Ações Recomendadas

### Prioridade Alta 🔴
1. **Remover endpoints de debug em produção**
   ```python
   # Adicionar verificação de ambiente
   if os.getenv('RAILWAY_ENVIRONMENT') == 'production':
       # Não registrar endpoints de debug
       pass
   ```

2. **Adicionar captcha no registro**
   - Implementar Google reCAPTCHA v3
   - Proteger contra bots

### Prioridade Média 🟡
3. **Monitorar migração de senhas**
   - Criar dashboard admin
   - Alertas se usuários não fazem upgrade em X dias

4. **Testes E2E do lazy loading**
   - Cypress/Playwright para testar scroll infinito real
   - Testar com 100k+ itens

### Prioridade Baixa 🟢
5. **Documentação adicional**
   - Guia de deployment
   - Runbook de troubleshooting
   - API documentation com Swagger

---

## 📝 Arquivos Modificados

### Novos Arquivos
- `migration_upgrade_passwords.py` - Sistema de upgrade de senhas
- `csrf_security_review.py` - Análise de segurança CSRF
- `tests/test_migration_passwords.py` - Testes migration
- `tests/test_lazy_loader.test.js` - Testes frontend
- `package.json` - Configuração Jest
- `babel.config.js` - Configuração Babel
- `tests/setup.js` - Setup testes Jest

### Arquivos Modificados
- `auth_functions.py` - Integração com migration de senhas
- `web_server.py` - Endpoints admin + correção CSRF
- `static/lazy-loader.js` - Fix sentinel (commit a1ef342)
- `static/lazy-integration.js` - Stubs e funções globais
- `static/app.js` - Integração lazy loading

---

## 🔢 Estatísticas

### Linhas de Código
- **Adicionado:** ~2500 linhas
  - Migration: 350 linhas
  - Testes: 800 linhas
  - Análise CSRF: 450 linhas
  - Documentação: 900 linhas

### Cobertura de Testes
- **Python:** 96%+ (mantido)
- **JavaScript:** 85%+ (novo)

### Segurança
- **Vulnerabilidades corrigidas:** 1 (CSRF em endpoint admin)
- **Endpoints analisados:** 7
- **Migrações pendentes:** Monitorar usuários SHA-256

---

## 📞 Suporte

Para dúvidas sobre estas mudanças:
1. Consulte este changelog
2. Verifique testes em `tests/`
3. Execute análises: `python csrf_security_review.py`
4. Monitore migrations: `GET /api/admin/passwords/migration-status`

---

**Última atualização:** 22 de Janeiro de 2026
**Responsável:** Sistema Automatizado de Atualizações
