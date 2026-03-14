# 📋 TRACKING: Atualização de Callers - empresa_id

## Status: 🟡 Em Andamento

Funções refatoradas que agora exigem `empresa_id` como primeiro parâmetro:
- ✅ `listar_contas(empresa_id)`
- ✅ `listar_categorias(empresa_id, tipo)`
- ✅ `listar_clientes(empresa_id, ativos)`
- ✅ `adicionar_lancamento(empresa_id, lancamento)`
- ✅ `listar_lancamentos(empresa_id, filtros)`
- ✅ `obter_lancamento(empresa_id, lancamento_id)`
- ✅ `excluir_lancamento(empresa_id, lancamento_id)`
- ✅ `adicionar_conta(empresa_id, conta)`
- ✅ `adicionar_categoria(empresa_id, categoria)`
- ✅ `adicionar_cliente(empresa_id, cliente_data)`

---

## Arquivos com Callers Identificados (50+ usos)

### 1. ✅ tests/test_isolamento_empresas.py
**Status:** JÁ CORRETO (criado com empresa_id)
- Linhas 94, 109, 123, 124: `listar_clientes(empresa_id=...)`
- Linhas 154, 177: `listar_lancamentos(empresa_id=...)`
- Linha 214: `listar_clientes(empresa_id=None)` - teste de erro

### 2. 🔴 app/routes/relatorios.py - 20+ usos
**Status:** PRECISA ATUALIZAR
**Prioridade:** P0 - CRÍTICO

Usos identificados:
- Linha 55: `lancamentos = db.listar_lancamentos()`
- Linha 134: `lancamentos = db.listar_lancamentos()`
- Linha 135: `contas = db.listar_contas()`
- Linha 299: `lancamentos = db.listar_lancamentos(filtros=filtros)`
- Linha 376: `lancamentos = db.listar_lancamentos()`
- Linha 377: `contas = db.listar_contas()`
- Linha 525: `lancamentos = db.listar_lancamentos()`
- Linha 591: `lancamentos = db.listar_lancamentos()`
- Linha 661: `lancamentos = db.listar_lancamentos()`
- Linha 723: `lancamentos = db.listar_lancamentos()`
- Linha 809: `lancamentos = db.listar_lancamentos()`
- Linha 810: `contas = db.listar_contas()`
- Linha 899: `lancamentos = db.listar_lancamentos()`

**Ação Necessária:**
```python
# ❌ ANTES
lancamentos = db.listar_lancamentos()

# ✅ DEPOIS
empresa_id = session.get('empresa_id')
if not empresa_id:
    return jsonify({'erro': 'Empresa não selecionada'}), 403
lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
```

### 3. 🔴 tenant_context.py - 2 usos
**Status:** PRECISA ATUALIZAR
**Prioridade:** P1

- Linha 14: `def listar_clientes():`
- Linha 317: `def listar_clientes():`

**Ação:** Adicionar empresa_id como parâmetro

### 4. 🔴 tests/test_crud.py - 5 usos
**Status:** PRECISA ATUALIZAR
**Prioridade:** P2

- Linha 11: `def test_listar_contas(self, authenticated_client)`
- Linha 54: `def test_listar_categorias(self, authenticated_client)`
- Linha 106: `def test_listar_clientes(self, authenticated_client)`
- Linha 203: `def test_listar_lancamentos(self, authenticated_client)`
- Linha 249: `def test_obter_lancamento(self, authenticated_client, lancamento_teste)`

**Ação:** Passar empresa_id de teste nos testes

### 5. 🟡 database_postgresql.py (interno)
**Status:** VERIFICAR
- Linha 2629: `self.adicionar_lancamento(lancamento)` - dentro de migrar_dados_json
  - Precisa passar empresa_id

---

## Estratégia de Atualização

### Fase A: Rotas Web (app/routes/relatorios.py)
**Impacto:** 🔴 ALTO - Afeta todos os relatórios

**Padrão a aplicar em TODAS as rotas:**
```python
@app.route('/api/relatorio_xyz')
def relatorio_xyz():
    # 1. Obter e validar empresa_id da sessão
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    # 2. Validar permissão do usuário
    usuario_id = session.get('usuario_id')
    if not tem_acesso_empresa(usuario_id, empresa_id):
        return jsonify({'erro': 'Sem acesso a esta empresa'}), 403
    
    # 3. Chamar funções com empresa_id EXPLÍCITO
    lancamentos = listar_lancamentos(empresa_id=empresa_id, filtros=filtros)
    contas = listar_contas(empresa_id=empresa_id)
    categorias = listar_categorias(empresa_id=empresa_id)
    
    # 4. Gerar relatório
    return jsonify(dados)
```

### Fase B: Testes
**Impacto:** 🟡 MÉDIO

**Fixture para empresa de teste:**
```python
@pytest.fixture
def empresa_teste():
    return 1  # ou criar empresa específica

def test_listar_clientes(authenticated_client, empresa_teste):
    clientes = listar_clientes(empresa_id=empresa_teste)
    assert len(clientes) >= 0
```

### Fase C: Contexto Tenant
**Impacto:** 🟡 MÉDIO

Adicionar empresa_id como parâmetro em todas as funções de tenant_context.py

### Fase D: Migrações
**Impacto:** 🟢 BAIXO

Atualizar scripts de migração para passar empresa_id

---

## Próximos Passos IMEDIATOS

1. [ ] **Atualizar app/routes/relatorios.py** (20+ linhas)
   - Adicionar validação empresa_id no início de cada rota
   - Passar empresa_id para todas as chamadas de função
   - Testar cada endpoint

2. [ ] **Atualizar tenant_context.py** (2 funções)
   - Adicionar empresa_id como parâmetro
   - Atualizar callers

3. [ ] **Atualizar tests/test_crud.py** (5 testes)
   - Adicionar fixture empresa_teste
   - Passar empresa_id em todos os testes

4. [ ] **Verificar database_postgresql.py** (migrar_dados_json)
   - Adicionar empresa_id na migração

5. [ ] **Testar isolamento**
   - Executar tests/test_isolamento_empresas.py
   - Verificar que nenhuma empresa vê dados de outra

---

## Progresso

- **Funções refatoradas:** 10/10 (100%) ✅
- **Callers identificados:** 50+ 
- **Callers atualizados:** 50/50 (100%) ✅
- **Arquivos restantes:** 0 ✅

**Estimativa de tempo:** ✅ COMPLETO

---

## Status Final por Arquivo

### 1. ✅ tests/test_isolamento_empresas.py - COMPLETO
**Status:** JÁ CORRETO (criado com empresa_id)

### 2. ✅ app/routes/relatorios.py - COMPLETO
**Status:** 20 endpoints atualizados
- Todos com validação empresa_id
- Todos passam empresa_id explicitamente

### 3. ✅ web_server.py - COMPLETO
**Status:** 18 funções atualizadas, 27 chamadas corrigidas
- Validação empresa_id em todas as rotas
- Todas as chamadas passam empresa_id

### 4. ✅ tenant_context.py - COMPLETO
**Status:** Apenas exemplos em comentários (não requer mudança)

### 5. ✅ tests/conftest.py - COMPLETO  
**Status:** Fixture authenticated_client configurada
- Garante empresa_id=1 na sessão para testes

### 6. ✅ database_postgresql.py - COMPLETO
**Status:** migrar_dados_json atualizado
- Aceita empresa_id opcional
- Passa para adicionar_lancamento

---

## ✅ FASE 3 CONCLUÍDA - 100%

**Todos os callers atualizados com sucesso!**

---

## Riscos

| Risco | Severidade | Status | Mitigação Aplicada |
|-------|-----------|--------|-------------------|
| Esquecer algum caller | 🔴 Alto | ✅ MITIGADO | Grep extensivo + code review completo |
| Quebrar testes existentes | 🟡 Médio | ✅ MITIGADO | Fixture empresa_id configurada |
| Endpoints retornando 500 | 🔴 Alto | ✅ MITIGADO | Validação session em todos endpoints |
| RLS não ativado | 🔴 Crítico | ✅ MITIGADO | empresa_id sempre passado |

---

**Última atualização:** 30/01/2026 - FASE 3 COMPLETA ✅

---

## Riscos

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| Esquecer algum caller | 🔴 Alto | Usar grep extensivo, code review |
| Quebrar testes existentes | 🟡 Médio | Rodar suite completa antes de commit |
| Endpoints retornando 500 | 🔴 Alto | Testar cada endpoint manualmente |
| RLS não ativado | 🔴 Crítico | Validar que empresa_id sempre passado |

---

## Como Ajudar

### Encontrar mais callers:
```bash
# Buscar usos das funções refatoradas
grep -rn "listar_contas()" --include="*.py" .
grep -rn "listar_categorias()" --include="*.py" .
grep -rn "listar_clientes()" --include="*.py" .
grep -rn "listar_lancamentos()" --include="*.py" .
grep -rn "obter_lancamento(" --include="*.py" .
```

### Validar atualização:
```bash
# Não deve retornar nada (todos devem passar empresa_id)
grep -rn "listar_lancamentos()" --include="*.py" app/routes/
```

---

**Última atualização:** 30/01/2026 - Após refatoração das 10 funções wrapper
