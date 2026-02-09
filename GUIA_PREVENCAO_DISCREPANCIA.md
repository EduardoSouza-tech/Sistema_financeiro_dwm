# 🛡️ GUIA DE PREVENÇÃO: Discrepância Backend vs Frontend

**Objetivo**: Prevenir inconsistências entre Frontend e Backend  
**Público-alvo**: Desenvolvedores, Tech Leads, Revisores de Código  
**Status**: 📋 **CHECKLIST OBRIGATÓRIO**

---

## ⚠️ O QUE É ESTE ERRO?

**Nome**: Split-Brain Data Source (Discrepância de Fonte de Dados)

**Definição**: Quando **Frontend** e **Backend** tomam a **mesma decisão** consultando **fontes diferentes**.

**Exemplo Real (Este Projeto)**:
```
Frontend: "Usuário tem permissão 'contas_view'" ✅
            ↓ (lê de: usuario_empresas.permissoes_empresa)
            
Backend:  "Usuário NÃO tem permissão 'contas_view'" ❌
            ↓ (lê de: usuario_permissoes)
            
Resultado: Usuário vê botão, mas não consegue clicar 💥
```

---

## 🚨 POR QUE É CRÍTICO?

| Impacto | Descrição |
|---------|-----------|
| **UX Ruim** | Sistema "mente" para o usuário (nível 4/5 de frustração) |
| **Confiança Quebrada** | Usuário perde confiança no sistema |
| **Suporte Sobrecarregado** | Chamados desnecessários de "sistema não funciona" |
| **Manutenção Cara** | Difícil de debugar, requer análise profunda |
| **Segurança** | Pode expor ou bloquear dados incorretamente |

---

## ✅ PRINCÍPIO FUNDAMENTAL

### Single Source of Truth (SSOT)

> **Para cada decisão lógica, deve existir EXATAMENTE UMA fonte autoritativa de dados.**
> 
> Frontend e Backend devem consultar a MESMA fonte.

**✅ CORRETO**:
```
┌──────────┐     ┌─────────────────┐     ┌──────────┐
│ Frontend │────→│ Service Layer   │←────│ Backend  │
└──────────┘     │ (SSOT)          │     └──────────┘
                 └─────────────────┘
                          ↓
                 ┌─────────────────┐
                 │    Database     │
                 └─────────────────┘
```

**❌ ERRADO**:
```
┌──────────┐     ┌─────────────────┐
│ Frontend │────→│  Tabela A       │
└──────────┘     └─────────────────┘

┌──────────┐     ┌─────────────────┐
│ Backend  │────→│  Tabela B       │  ← INCONSISTÊNCIA!
└──────────┘     └─────────────────┘
```

---

## 📋 CHECKLIST DE PREVENÇÃO

### 1️⃣ DURANTE DESENVOLVIMENTO

#### ✅ Antes de Implementar Nova Feature

- [ ] **Identificar a decisão lógica**: O que estou validando? (ex: permissões, acesso, status)
- [ ] **Definir fonte autoritativa**: Qual tabela/campo é a verdade? (ex: `usuario_empresas.permissoes_empresa`)
- [ ] **Documentar a decisão**: Comentar no código qual é a SSOT
- [ ] **Criar função centralizada**: Não espalhar lógica de consulta
- [ ] **Validar Frontend E Backend**: Ambos usam mesma função/endpoint

#### ✅ Ao Adicionar Validação

**❌ NÃO FAÇA**:
```python
# Backend
if database.check_permission(user_id):  # Lê do banco
    allow()

# Frontend
if localStorage.has_permission:  # Lê do cache local
    show_button()
```

**✅ FAÇA**:
```python
# Backend - Função centralizada
class PermissionService:
    def has_permission(user_id, permission):
        return database.check_permission(user_id, permission)

# Backend - Usa serviço
if PermissionService.has_permission(user_id, 'x'):
    allow()

# Frontend - Chama API (mesma fonte)
fetch('/api/permissions/check?permission=x')
    .then(response => show_button())
```

---

### 2️⃣ DURANTE MIGRAÇÃO DE ARQUITETURA

#### ✅ Antes de Começar

- [ ] **Mapear TODOS os pontos**: Onde a estrutura antiga é usada?
  ```bash
  # Exemplo: Buscar todas as referências
  git grep "usuario_permissoes" --name-only
  git grep "obter_permissoes_usuario" --name-only
  ```

- [ ] **Criar planilha de mapeamento**:
  ```
  | Arquivo | Linha | Função | Status |
  |---------|-------|--------|--------|
  | web_server.py | 713 | login | ⚠️ Fallback antigo |
  | auth_middleware.py | 244 | decorator | ❌ Usa antigo |
  | app.js | 594 | menu | ✅ Usa novo |
  ```

- [ ] **Planejar ordem de refatoração**: Começar por pontos críticos (decorators, middlewares)

- [ ] **Definir período de transição**: Dual-write (se necessário), NUNCA dual-read inconsistente

#### ✅ Durante Implementação

- [ ] **Refatorar TODOS os pontos**: Sem exceções
- [ ] **Remover fallbacks para sistema antigo**: Rejeitar explicitamente
- [ ] **Adicionar logs temporários**: Detectar uso acidental do sistema antigo
  ```python
  def funcao_antiga():
      logger.warning("⚠️ DEPRECATED: funcao_antiga() ainda em uso!")
      # ...
  ```

- [ ] **Criar testes de regressão**: Para cada ponto refatorado

#### ✅ Após Implementação

- [ ] **Validar que sistema antigo não é mais usado**:
  ```bash
  git grep "funcao_antiga" | grep -v "test" | grep -v "deprecated"
  # Resultado esperado: nenhum match
  ```

- [ ] **Deprecar estrutura antiga**:
  ```sql
  ALTER TABLE tabela_antiga RENAME TO tabela_antiga_deprecated;
  -- Adicionar trigger para prevenir inserções
  ```

- [ ] **Monitorar logs**: Procurar por warnings de uso da estrutura antiga

- [ ] **Remover após período de segurança** (30-60 dias):
  ```sql
  DROP TABLE tabela_antiga_deprecated CASCADE;
  ```

---

### 3️⃣ DURANTE CODE REVIEW

#### ✅ Checklist do Revisor

**Para TODA mudança em lógica de validação**:

- [ ] Frontend e Backend usam mesma fonte de dados?
  ```python
  # Verificar se ambos consultam:
  # - Mesmo endpoint API
  # - Mesma tabela/campo
  # - Mesma função de serviço
  ```

- [ ] Não há código condicional que pode divergir?
  ```python
  # ❌ PERIGOSO:
  if ENV == 'dev':
      check_permissions_from_file()
  else:
      check_permissions_from_db()
  
  # ✅ SEGURO:
  check_permissions_from_db()  # Sempre o mesmo
  ```

- [ ] Não há fallback silencioso para fonte antiga?
  ```python
  # ❌ PERIGOSO:
  try:
      perms = get_new_permissions()
  except:
      perms = get_old_permissions()  # Fallback silencioso!
  
  # ✅ SEGURO:
  perms = get_new_permissions()
  if not perms:
      raise Exception("Permissões não encontradas")
  ```

- [ ] Logs indicam claramente qual fonte está sendo usada?
  ```python
  # ✅ SEGURO:
  logger.info(f"Consultando permissões de: usuario_empresas.permissoes_empresa")
  perms = get_permissions_from_empresa_table()
  ```

- [ ] Testes E2E validam consistência Frontend-Backend?
  ```python
  def test_permission_consistency():
      # 1. Frontend mostra funcionalidade
      # 2. Backend permite acesso
      # Ambos devem ser True ou False juntos
  ```

---

### 4️⃣ DURANTE TESTES

#### ✅ Testes Obrigatórios

**1. Teste Unitário** (fonte de dados):
```python
def test_permission_service_uses_correct_table():
    """Valida que serviço usa tabela correta"""
    with mock.patch('database.query') as mock_query:
        PermissionService.get_permissions(user_id=1, empresa_id=1)
        
        # Verifica que consultou tabela correta
        call_args = mock_query.call_args[0][0]
        assert 'usuario_empresas' in call_args
        assert 'usuario_permissoes' not in call_args  # Tabela antiga
```

**2. Teste de Integração** (fluxo Backend):
```python
def test_permission_decorator_allows_access():
    """Valida que decorator permite acesso correto"""
    # Setup: Usuário com permissão 'x'
    set_permission(user_id=1, empresa_id=1, permission='x')
    login_as(user_id=1, empresa_id=1)
    
    # Test: Acessar rota protegida
    response = client.get('/api/protected-route')
    
    # Assert: Deve permitir
    assert response.status_code == 200
```

**3. Teste E2E** (Frontend + Backend):
```python
def test_frontend_backend_consistency():
    """Valida consistência completa"""
    # Setup: Usuário SEM permissão 'contas_view'
    user = create_user_without_permission('contas_view')
    login_as(user)
    
    # Frontend: GET /api/auth/verify
    verify = client.get('/api/auth/verify').json()
    frontend_shows_button = 'contas_view' in verify['permissoes']
    
    # Backend: GET /api/contas
    response = client.get('/api/contas')
    backend_allows_access = (response.status_code == 200)
    
    # Consistência: Ambos devem ser False
    assert frontend_shows_button == False, "Frontend não deve mostrar botão"
    assert backend_allows_access == False, "Backend não deve permitir acesso"
    
    # ✅ TESTE PASSOU: Frontend e Backend consistentes
```

**4. Teste de Regressão** (após migração):
```python
def test_old_table_not_used():
    """Valida que tabela antiga não é mais consultada"""
    with monitor_database_queries() as queries:
        # Executar fluxo completo
        user = login()
        client.get('/api/contas')
        
        # Verificar queries executadas
        for query in queries:
            assert 'usuario_permissoes' not in query.lower(), \
                "Sistema não deve consultar tabela antiga!"
```

---

## 🔧 FERRAMENTAS DE PREVENÇÃO

### 1. Função de Busca de Inconsistências

```bash
#!/bin/bash
# check_consistency.sh - Buscar possíveis inconsistências

echo "🔍 Buscando uso de tabelas antigas..."

# Buscar referências a tabela antiga
OLD_TABLE_REFS=$(git grep -n "usuario_permissoes" --exclude-dir=tests)

if [ -n "$OLD_TABLE_REFS" ]; then
    echo "⚠️ AVISO: Referências a tabela antiga encontradas:"
    echo "$OLD_TABLE_REFS"
    exit 1
else
    echo "✅ Nenhuma referência a tabela antiga"
fi

# Buscar funções antigas
OLD_FUNCTIONS=$(git grep -n "obter_permissoes_usuario\(" --exclude-dir=tests | grep -v "obter_permissoes_usuario_empresa")

if [ -n "$OLD_FUNCTIONS" ]; then
    echo "⚠️ AVISO: Uso de função antiga encontrado:"
    echo "$OLD_FUNCTIONS"
    exit 1
else
    echo "✅ Nenhuma função antiga em uso"
fi

echo "✅ Sistema limpo!"
```

### 2. Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit - Executar antes de cada commit

# Executar checagem de consistência
./check_consistency.sh

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ COMMIT BLOQUEADO: Inconsistências detectadas"
    echo "Por favor, corrija antes de commitar."
    exit 1
fi
```

### 3. CI/CD Pipeline Check

```yaml
# .github/workflows/checks.yml
name: Consistency Checks

on: [push, pull_request]

jobs:
  check-consistency:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Check for old table references
        run: |
          if git grep "usuario_permissoes" --exclude-dir=tests; then
            echo "❌ Referências a tabela antiga encontradas!"
            exit 1
          fi
      
      - name: Check for old function usage
        run: |
          if git grep "obter_permissoes_usuario(" --exclude-dir=tests | grep -v "obter_permissoes_usuario_empresa"; then
            echo "❌ Uso de função antiga encontrado!"
            exit 1
          fi
      
      - name: Run E2E consistency tests
        run: pytest tests/test_consistency_e2e.py -v
```

---

## 📊 TEMPLATE DE ANÁLISE DE IMPACTO

**Use ao fazer mudanças em lógica de validação**:

```markdown
## Análise de Impacto - [Nome da Mudança]

### 1. Fonte de Dados
- [ ] Fonte Antiga: [nome da tabela/campo]
- [ ] Fonte Nova: [nome da tabela/campo]
- [ ] Justificativa da mudança: [explicação]

### 2. Pontos Afetados
- [ ] Frontend: [listar arquivos e linhas]
- [ ] Backend: [listar arquivos e linhas]
- [ ] Total de pontos: [número]

### 3. Estratégia de Migração
- [ ] Refatoração simultânea de todos os pontos: Sim/Não
- [ ] Período de transição: [dias] ou N/A
- [ ] Dual-write necessário: Sim/Não
- [ ] Rollback plan: [descrever]

### 4. Testes
- [ ] Testes unitários criados: [quantidade]
- [ ] Testes de integração criados: [quantidade]
- [ ] Testes E2E criados: [quantidade]
- [ ] Cobertura: [porcentagem]%

### 5. Validação
- [ ] Code review completo: Sim/Não
- [ ] Testes em staging: Sim/Não
- [ ] Aprovação de: [nome do revisor]

### 6. Deprecação
- [ ] Código antigo marcado como deprecated: Sim/Não
- [ ] Data de remoção planejada: [data]
- [ ] Comunicação para equipe: Sim/Não
```

---

## 🎯 CASOS DE USO COMUNS

### Caso 1: Adicionar Nova Feature com Validação

**Cenário**: Adicionar funcionalidade "Exportar Relatórios" com validação de permissão.

**✅ Processo Correto**:

1. **Definir permissão**:
   ```sql
   INSERT INTO permissoes (codigo, nome, descricao) 
   VALUES ('relatorios_exportar', 'Exportar Relatórios', 'Permite exportar relatórios');
   ```

2. **Criar endpoint de validação**:
   ```python
   # Backend - auth_service.py
   class AuthService:
       def has_permission(self, user_id, empresa_id, permission):
           # SSOT: usuario_empresas.permissoes_empresa
           return permission in self.get_permissions(user_id, empresa_id)
   ```

3. **Proteger rota Backend**:
   ```python
   @app.route('/api/relatorios/exportar', methods=['POST'])
   @require_permission('relatorios_exportar')
   def exportar_relatorio():
       # ...
   ```

4. **Validar no Frontend** (via API):
   ```javascript
   // Frontend
   const permissions = await fetch('/api/auth/verify').then(r => r.json()).permissoes;
   
   if (permissions.includes('relatorios_exportar')) {
       showExportButton();
   }
   ```

5. **Testar E2E**:
   ```python
   def test_export_permission_consistency():
       # Usuário COM permissão
       user_with_perm = create_user_with_permission('relatorios_exportar')
       login_as(user_with_perm)
       
       # Frontend mostra botão
       verify = client.get('/api/auth/verify').json()
       assert 'relatorios_exportar' in verify['permissoes']
       
       # Backend permite exportar
       response = client.post('/api/relatorios/exportar', json={...})
       assert response.status_code == 200
   ```

---

### Caso 2: Migrar Sistema de Single-Tenant para Multi-Tenant

**Cenário**: Sistema atualmente valida por usuário, precisa validar por usuário+empresa.

**✅ Processo Correto**:

**FASE 1: Planejamento**
```bash
# 1. Mapear todos os pontos de validação
git grep "validate_user(" > migration_points.txt
git grep "check_access(" >> migration_points.txt

# 2. Criar planilha
# migration_plan.xlsx com colunas:
# - Arquivo
# - Linha
# - Função
# - Usa empresa_id? (Sim/Não)
# - Prioridade (P0/P1/P2)
```

**FASE 2: Implementação**
```python
# 1. Criar nova estrutura
ALTER TABLE usuarios ADD COLUMN empresa_id INT;
CREATE TABLE usuario_empresas (
    usuario_id INT,
    empresa_id INT,
    permissoes JSONB,
    PRIMARY KEY (usuario_id, empresa_id)
);

# 2. Migrar dados
INSERT INTO usuario_empresas (usuario_id, empresa_id, permissoes)
SELECT u.id, 1, u.permissoes_antigas 
FROM usuarios u;

# 3. Criar funções novas
def validate_user_multi_tenant(user_id, empresa_id):
    # Nova validação com empresa_id obrigatória
    ...

# 4. Refatorar TODOS os pontos (baseado na planilha)
# Não deixar nenhum ponto usando função antiga

# 5. Deprecar funções antigas
def validate_user(user_id):
    warnings.warn("DEPRECATED: Use validate_user_multi_tenant", DeprecationWarning)
    ...
```

**FASE 3: Validação**
```python
# Testes E2E de isolamento
def test_multi_tenant_isolation():
    # Usuário com acesso a Empresa 1
    user = create_user(empresas=[1])
    login_as(user, empresa_id=1)
    
    # Dados visíveis da Empresa 1
    data_1 = client.get('/api/data').json()
    assert len(data_1) > 0
    
    # Switch para Empresa 2 (sem acesso)
    client.post('/api/switch-empresa', json={'empresa_id': 2})
    
    # Dados NÃO visíveis da Empresa 2
    data_2 = client.get('/api/data').json()
    assert len(data_2) == 0 or response.status_code == 403
```

**FASE 4: Limpeza**
```python
# Após 30 dias em produção sem erros:

# 1. Verificar uso
SELECT COUNT(*) FROM usuarios_old_table;  # Deve ser 0

# 2. Remover fallbacks
# (remover código condicional que usa sistema antigo)

# 3. Dropar tabela antiga
DROP TABLE usuarios_old_table CASCADE;

# 4. Remover funções antigas
git grep "validate_user(" | grep -v "validate_user_multi_tenant"
# Remover todas as referências encontradas
```

---

## 🆘 TROUBLESHOOTING

### Problema: "Frontend mostra, Backend bloqueia"

**Diagnóstico**:
```python
# 1. Verificar que fontes são usadas
print("[Frontend] Permissões de:", inspect_frontend_permission_source())
print("[Backend] Permissões de:", inspect_backend_permission_source())

# 2. Comparar valores
frontend_perms = get_frontend_permissions(user_id)
backend_perms = get_backend_permissions(user_id)

print("Diff:", set(frontend_perms) - set(backend_perms))
```

**Solução**:
1. Identificar qual fonte é correta (geralmente a mais recente)
2. Refatorar a fonte incorreta para usar a correta
3. Adicionar teste E2E para prevenir regressão

---

### Problema: "Sistema funcionava antes da migração"

**Diagnóstico**:
```bash
# 1. Verificar histórico git
git log --all --full-history --oneline -- "*permission*"

# 2. Encontrar commit que quebrou
git bisect start
git bisect bad HEAD
git bisect good <ultimo-commit-funcionando>

# 3. Executar testes em cada commit
git bisect run pytest tests/test_permissions.py
```

**Solução**:
1. Identificar commit que introduziu inconsistência
2. Reverter ou corrigir a mudança
3. Adicionar testes que teriam detectado o problema

---

## ✅ CHECKLIST FINAL (Resume Tudo)

**Antes de Commitar**:
- [ ] Frontend e Backend usam mesma fonte? (SSOT)
- [ ] Não há fallback para fonte antiga?
- [ ] Logs indicam qual fonte está sendo usada?
- [ ] Testes E2E validam consistência?
- [ ] Code review focou em consistência?

**Antes de Migrar Arquitetura**:
- [ ] Mapeamento completo de pontos afetados?
- [ ] Refatoração total (100% dos pontos)?
- [ ] Testes de regressão criados?
- [ ] Período de transição planejado?
- [ ] Plano de deprecação da estrutura antiga?

**Antes de Deploy**:
- [ ] Testes E2E passando?
- [ ] Staging validado manualmente?
- [ ] Rollback plan documentado?
- [ ] Monitoramento configurado?
- [ ] Equipe comunicada sobre a mudança?

---

## 📚 RECURSOS ADICIONAIS

### Documentos Relacionados
- `ANALISE_TECNICA_DISCREPANCIA_BACKEND_FRONTEND.md` - Análise técnica completa
- `HOTFIX_PERMISSOES_MULTI_TENANT.md` - Caso real deste projeto

### Leitura Recomendada
- Martin Fowler: "Patterns of Enterprise Application Architecture" (Service Layer)
- Eric Evans: "Domain-Driven Design" (Single Source of Truth)
- Sam Newman: "Building Microservices" (Data Consistency)

---

**Versão**: 1.0  
**Data**: 09/02/2026  
**Autor**: GitHub Copilot (Claude Sonnet 4.5)  
**Status**: ✅ ATIVO - USO OBRIGATÓRIO
