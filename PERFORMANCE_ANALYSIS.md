# ⚡ Análise de Performance - Sistema Financeiro DWM

## 🎯 Objetivo Fase 7
Otimizar performance do sistema através de:
1. Cache inteligente
2. Paginação de queries
3. Índices otimizados
4. Eliminação de N+1 queries

---

## 🔍 Análise Atual - Gargalos Identificados

### 1. **Queries sem Paginação** ⚠️ CRÍTICO

**Problema**: `db.listar_lancamentos()` retorna TODOS os lançamentos sem limite

**Locais afetados** (25+ ocorrências):
- `/api/relatorios/dashboard-completo` - Linha 3567
- `/api/relatorios/dashboard` - Linha 3412  
- `/api/relatorios/categoria` - Linha 3750
- `/api/relatorios/por-categoria` - Linha 3899
- `/api/relatorios/fluxo-caixa` - Linha 4236
- `/api/relatorios/dre` - Linha 4305
- `/api/relatorios/resumo-anual` - Linha 4366
- `/api/relatorios/inadimplencia` - Linha 4451
- `/api/relatorios/previsao` - Linha 4540
- Todos os endpoints do blueprint relatorios.py

**Impacto**:
- Com 10.000 lançamentos: ~2-5 segundos de resposta
- Com 50.000+ lançamentos: timeout (>30s)
- Alto uso de memória (carrega tudo na RAM)

**Solução**:
```python
# ANTES
lancamentos = db.listar_lancamentos()

# DEPOIS
page = request.args.get('page', 1, type=int)
per_page = request.args.get('per_page', 50, type=int)
lancamentos = db.listar_lancamentos_paginado(page=page, per_page=per_page)
```

---

### 2. **N+1 Queries em Loops** ⚠️ ALTO IMPACTO

**Problema**: Processar lançamentos em loops sem otimização

**Exemplo detectado**:
```python
# dashboard_completo - Linha 3621
for l in lancamentos:  # 10.000 iterações
    if l.tipo == TipoLancamento.RECEITA and l.pessoa:
        if l.pessoa not in clientes_resumo:
            clientes_resumo[l.pessoa] = {'total': Decimal('0'), 'quantidade': 0}
        clientes_resumo[l.pessoa]['total'] += Decimal(str(l.valor))
```

**Impacto**:
- Python loop em 10k+ registros: lento
- Sem agregação SQL: processamento ineficiente

**Solução**:
```sql
-- Usar GROUP BY direto no SQL
SELECT 
    pessoa,
    SUM(valor) as total,
    COUNT(*) as quantidade
FROM lancamentos
WHERE tipo = 'receita' AND status = 'pago'
GROUP BY pessoa
```

---

### 3. **SELECT * Desnecessário** ⚠️ MÉDIO IMPACTO

**Problema**: Queries retornam todas as colunas quando precisam de poucas

**Exemplo**:
```python
# Linha 2107
query = "SELECT * FROM lancamentos WHERE 1=1"
```

**Impacto**:
- Transfere dados desnecessários (anexos, observações grandes)
- Aumenta tempo de serialização JSON
- Maior uso de banda

**Solução**:
```python
# Apenas colunas necessárias
query = """
SELECT id, tipo, descricao, valor, data_vencimento, status
FROM lancamentos WHERE 1=1
"""
```

---

### 4. **Sem Cache em Relatórios** ⚠️ ALTO IMPACTO

**Problema**: Dashboard recalculado a cada refresh (1-3 segundos)

**Endpoints sem cache**:
- `/api/relatorios/dashboard-completo` 
- `/api/relatorios/dashboard`
- `/api/relatorios/dre`
- `/api/relatorios/fluxo-caixa`

**Solução**:
```python
from app.utils.cache_manager import cached

@cached(ttl=300, prefix="dashboard")
def dashboard_completo():
    # Query pesada...
    return data
```

---

### 5. **Índices Faltando** ⚠️ CRÍTICO

**Análise dos índices atuais**:
```sql
✅ idx_lancamentos_empresa (empresa_id)
✅ idx_lancamentos_proprietario (proprietario_id)
❌ FALTAM: Índices compostos para queries complexas
```

**Índices necessários**:
```sql
-- Query comum: WHERE proprietario_id = X AND status = 'pago' AND data_pagamento BETWEEN A AND B
CREATE INDEX idx_lancamentos_filtros 
ON lancamentos(proprietario_id, status, data_pagamento);

-- Query comum: WHERE tipo = 'receita' AND status = 'pago' ORDER BY data_pagamento DESC
CREATE INDEX idx_lancamentos_tipo_status_data 
ON lancamentos(tipo, status, data_pagamento DESC);

-- Query comum: WHERE conta_bancaria = X AND data_vencimento BETWEEN A AND B
CREATE INDEX idx_lancamentos_conta_data 
ON lancamentos(conta_bancaria, data_vencimento);
```

---

## 📊 Benchmarks Estimados

### Dashboard Completo (endpoint mais crítico)

| Cenário | Tempo Atual | Tempo Otimizado | Melhoria |
|---------|-------------|-----------------|----------|
| 1.000 lançamentos | 0.5s | 0.1s | **80%** |
| 10.000 lançamentos | 3.2s | 0.3s | **91%** |
| 50.000 lançamentos | timeout | 0.8s | **97%** |
| 100.000 lançamentos | timeout | 1.5s | **95%** |

### Lista de Lançamentos com Paginação

| Cenário | Tempo Atual | Tempo Otimizado | Melhoria |
|---------|-------------|-----------------|----------|
| Página 1 (50 registros) | 2.1s | 0.05s | **98%** |
| Página 100 (50 registros) | 2.1s | 0.06s | **97%** |

### Cache Hit Rate Esperado

| Endpoint | Cache TTL | Hit Rate Estimado |
|----------|-----------|-------------------|
| Dashboard | 5 min | 85-95% |
| Relatórios | 10 min | 70-80% |
| Listas de categorias | 30 min | 95-99% |

---

## 🎯 Plano de Implementação

### Fase 7.1: Paginação ✅ EM ANDAMENTO
- [x] Criar query_optimizer.py
- [ ] Adicionar paginação em listar_lancamentos()
- [ ] Atualizar endpoints de relatórios
- [ ] Atualizar frontend para paginação

### Fase 7.2: Cache
- [x] Criar cache_manager.py
- [ ] Aplicar cache em dashboard
- [ ] Aplicar cache em relatórios
- [ ] Endpoint de limpeza de cache

### Fase 7.3: Índices
- [ ] Analisar EXPLAIN ANALYZE de queries críticas
- [ ] Criar índices compostos
- [ ] Validar melhoria de performance

### Fase 7.4: Queries Otimizadas
- [ ] Substituir loops Python por GROUP BY SQL
- [ ] Usar SELECT específico (não SELECT *)
- [ ] Adicionar EXPLAIN para queries lentas

### Fase 7.5: Lazy Loading Frontend
- [ ] Virtual scrolling em tabelas grandes
- [ ] Infinite scroll em listas
- [ ] Debounce em filtros

---

## 🧪 Testes de Performance

### Setup de Teste
```python
# popular_dados_teste.py
def gerar_massa_dados(num_lancamentos=10000):
    """Gera dados para teste de performance"""
    # Criar 10k lançamentos
    # 5 contas bancárias
    # 50 clientes
    # 30 fornecedores
```

### Métricas a Monitorar
- **Tempo de resposta**: < 200ms (p95), < 500ms (p99)
- **Taxa de cache hit**: > 80%
- **Uso de memória**: < 500MB por worker
- **Queries por request**: < 10

---

## 🚀 Quick Wins (30 minutos)

### 1. Adicionar paginação básica (10 min)
```python
# database_postgresql.py
def listar_lancamentos_paginado(page=1, per_page=50, filtros=None):
    offset = (page - 1) * per_page
    query += f" LIMIT {per_page} OFFSET {offset}"
```

### 2. Cache no dashboard (10 min)
```python
# app/routes/relatorios.py
from app.utils.cache_manager import cached

@cached(ttl=300)
def dashboard_completo():
    # ...
```

### 3. Índice composto principal (5 min)
```sql
CREATE INDEX idx_lancamentos_principais 
ON lancamentos(proprietario_id, status, data_pagamento);
```

### 4. SELECT específico (5 min)
```python
# Trocar SELECT * por colunas específicas em queries críticas
```

---

## 📈 Resultados Esperados

### Performance
- ✅ **5-10x** mais rápido em listagens
- ✅ **20-50x** mais rápido em dashboards (com cache)
- ✅ **Suporte a 100k+** lançamentos sem timeout

### Escalabilidade
- ✅ 10 usuários simultâneos → 100+ usuários
- ✅ Uso de memória estável
- ✅ Menos carga no banco de dados

### Experiência do Usuário
- ✅ Dashboard carrega em < 300ms
- ✅ Scroll infinito fluido
- ✅ Sem timeouts em relatórios grandes

---

## 🔧 Ferramentas de Monitoramento

### Query Profiler
```python
from app.utils.query_optimizer import profiler

# Após requisições
stats = profiler.get_stats()
print(f"Queries lentas: {stats['slow_queries']}")
```

### Cache Stats
```python
from app.utils.cache_manager import get_cache_stats

stats = get_cache_stats()
print(f"Cache hit rate: {stats['valid_keys'] / stats['total_keys'] * 100}%")
```

---

**Status**: 🚧 Fase 7.1 em andamento  
**Próximo passo**: Implementar paginação em listar_lancamentos()
