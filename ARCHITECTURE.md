# 🏗️ Arquitetura do Sistema

**Última atualização:** 20/01/2026  
**Versão:** 2.0 (Pós-otimização)

---

## 📐 Visão Geral

Sistema web full-stack com arquitetura modular, seguindo princípios de Clean Architecture e separation of concerns.

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (SPA)                    │
│  HTML5 + Vanilla JS + Bootstrap + Utils.js         │
└─────────────────┬───────────────────────────────────┘
                  │ HTTP/REST (JSON + gzip)
┌─────────────────▼───────────────────────────────────┐
│              Flask Application                      │
│  ┌──────────────────────────────────────────────┐  │
│  │          web_server.py (Main App)            │  │
│  │  - CSRF Protection                           │  │
│  │  - Gzip Compression                          │  │
│  │  - Rate Limiting                             │  │
│  │  - Session Management                        │  │
│  └──────────────────┬───────────────────────────┘  │
│                     │                               │
│  ┌──────────────────▼───────────────────────────┐  │
│  │        Blueprints (Modular Routes)           │  │
│  │  - kits.py       (Kits CRUD)                 │  │
│  │  - contratos.py  (Contratos + numeração)     │  │
│  │  - sessoes.py    (Sessões + conversões)      │  │
│  │  - relatorios.py (10 endpoints de reports)   │  │
│  └──────────────────┬───────────────────────────┘  │
│                     │                               │
│  ┌──────────────────▼───────────────────────────┐  │
│  │        Utilities & Helpers                   │  │
│  │  - date_helpers.py    (Parsing/formatting)   │  │
│  │  - money_formatters.py (Currency/decimal)    │  │
│  │  - validators.py      (Email, CPF, CNPJ)     │  │
│  │  - cache_helper.py    (Memoization)          │  │
│  │  - pagination_helper.py (Paging)             │  │
│  └──────────────────┬───────────────────────────┘  │
│                     │                               │
│  ┌──────────────────▼───────────────────────────┐  │
│  │     Database Layer (PostgreSQL)              │  │
│  │  - database_postgresql.py (Connection pool)  │  │
│  │  - models.py (Enums & types)                 │  │
│  │  - auth_middleware.py (Permissions)          │  │
│  └──────────────────┬───────────────────────────┘  │
└────────────────────┼─────────────────────────────────┘
                     │ psycopg2 (connection pool)
┌────────────────────▼─────────────────────────────────┐
│            PostgreSQL Database                      │
│  - 15+ tables with foreign keys                    │
│  - 36 performance indexes                          │
│  - Multi-tenancy (empresa_id)                      │
│  - ACID transactions                               │
└─────────────────────────────────────────────────────┘
```

---

## 📂 Estrutura de Diretórios

```
sistema_financeiro/
├── 📁 app/
│   ├── 📁 routes/              # Blueprints modulares
│   │   ├── __init__.py         # Registro de blueprints
│   │   ├── kits.py            # API de kits
│   │   ├── contratos.py       # API de contratos
│   │   ├── sessoes.py         # API de sessões
│   │   └── relatorios.py      # API de relatórios
│   └── 📁 utils/              # Utilitários compartilhados
│       ├── __init__.py
│       ├── date_helpers.py    # Parse/format datas
│       ├── money_formatters.py # Format moeda/decimal
│       ├── validators.py      # Validações (CPF, email, etc)
│       ├── cache_helper.py    # Sistema de cache
│       └── pagination_helper.py # Paginação
│
├── 📁 static/                 # Assets frontend
│   ├── app.js                # Lógica principal (3.372 linhas)
│   ├── utils.js              # Utilities frontend (520 linhas)
│   └── style.css             # Estilos
│
├── 📁 templates/              # HTML templates
│   ├── index.html            # Landing page
│   └── interface_nova.html   # SPA principal (5.668 linhas)
│
├── 📁 tests/                  # Testes automatizados
│   ├── conftest.py           # Fixtures pytest
│   ├── test_date_helpers.py  # 35 testes
│   ├── test_money_formatters.py # 30 testes
│   ├── test_validators.py    # 40 testes
│   └── test_blueprints_integration.py # 37 testes
│
├── 📄 web_server.py          # Aplicação Flask principal
├── 📄 database_postgresql.py # Camada de dados
├── 📄 auth_middleware.py     # Autenticação/autorização
├── 📄 models.py              # Enums e tipos
│
├── 📄 migration_*.py         # Migrations de banco
├── 📄 requirements_web.txt   # Dependências Python
├── 📄 requirements_test.txt  # Dependências de teste
│
└── 📁 docs/                  # Documentação
    ├── ARCHITECTURE.md       # Este arquivo
    ├── API.md               # Documentação da API
    ├── DEPLOY.md            # Guia de deploy
    ├── VALIDACAO_FASE7.md   # Testes de performance
    └── CHANGELOG.md         # Histórico de versões
```

---

## 🧩 Componentes Principais

### 1. **web_server.py** - Aplicação Flask (6.986 linhas)

**Responsabilidades:**
- Inicialização do Flask app
- Configuração de middlewares (CORS, CSRF, Compress)
- Registro de blueprints
- Endpoints legacy (a serem migrados)
- Error handlers globais

**Middlewares configurados:**
```python
# Compressão gzip (60-80% redução)
Compress(app)

# CSRF Protection
csrf = CSRFProtect(app)

# CORS para API
CORS(app, supports_credentials=True)

# Rate Limiting (200/dia, 50/hora)
Limiter(app, key_func=get_remote_address)
```

**Arquitetura de Request:**
```
Request → Rate Limiter → CSRF Check → Auth Middleware → 
  → Blueprint Handler → Cache Layer → Database → 
  → Response → Gzip Compression → Client
```

---

### 2. **Blueprints** - Módulos de Rotas

#### **app/routes/kits.py** (125 linhas)
```python
# Endpoints:
GET    /api/kits              # Listar kits
POST   /api/kits              # Criar kit
GET    /api/kits/<id>         # Obter kit específico
PUT    /api/kits/<id>         # Atualizar kit
DELETE /api/kits/<id>         # Deletar kit

# Features:
- Filtro por empresa (multi-tenancy)
- Validação de permissões
- Status ativo/inativo
```

#### **app/routes/contratos.py** (125 linhas)
```python
# Endpoints:
GET    /api/contratos                  # Listar contratos
POST   /api/contratos                  # Criar contrato
GET    /api/contratos/proximo-numero   # Gerar próximo número
GET    /api/contratos/<id>             # Obter contrato
PUT    /api/contratos/<id>             # Atualizar contrato
DELETE /api/contratos/<id>             # Deletar contrato

# Features:
- Auto-numeração de contratos (CONT-001, CONT-002, ...)
- Filtro por cliente
- Validação de datas (início <= fim)
```

#### **app/routes/sessoes.py** (142 linhas)
```python
# Endpoints:
GET    /api/sessoes           # Listar sessões
POST   /api/sessoes           # Criar sessão
GET    /api/sessoes/<id>      # Obter sessão
PUT    /api/sessoes/<id>      # Atualizar sessão
DELETE /api/sessoes/<id>      # Deletar sessão

# Features:
- Conversão de campos (data → data_sessao)
- Conversão horas → minutos (quantidade_horas * 60)
- Vínculo com contratos
```

#### **app/routes/relatorios.py** (900 linhas)
```python
# 10 Endpoints de relatórios:
GET /api/relatorios/dashboard            # Dashboard executivo
GET /api/relatorios/dashboard-completo   # Dashboard com período
GET /api/relatorios/fluxo-caixa          # Fluxo de caixa
GET /api/relatorios/fluxo-projetado      # Projeção futura
GET /api/relatorios/analise-contas       # Análise por conta
GET /api/relatorios/resumo-parceiros     # Resumo clientes/fornecedores
GET /api/relatorios/analise-categorias   # Análise por categoria
GET /api/relatorios/comparativo-periodos # Comparação temporal
GET /api/relatorios/indicadores          # KPIs financeiros
GET /api/relatorios/inadimplencia        # Análise de inadimplência

# Features:
- Cache de 5-10 minutos (opcional)
- Agregações SQL otimizadas
- Filtros por período, empresa, categoria
```

---

### 3. **Utilities** - Helpers Compartilhados

#### **app/utils/date_helpers.py** (280 linhas)
```python
# Funções principais:
parse_date(date_str)              # Parsing flexível (ISO, BR, datetime)
format_date_br(date_obj)          # DD/MM/YYYY
format_date_iso(date_obj)         # YYYY-MM-DD
add_months(date_obj, months)      # Adicionar/subtrair meses
days_between(date1, date2)        # Diferença em dias
get_month_range(year, month)      # Primeiro e último dia
is_weekend(date_obj)              # Verificar fim de semana
get_next_business_day(date_obj)   # Próximo dia útil
```

#### **app/utils/money_formatters.py** (220 linhas)
```python
# Funções principais:
format_currency(value)            # R$ 1.234,56
parse_currency(value_str)         # String → Decimal
format_percentage(value)          # 25,50%
calculate_percentage(part, total) # Calcular porcentagem
apply_percentage(value, pct)      # Aplicar aumento/desconto
round_money(value)                # Arredondar 2 casas
```

#### **app/utils/validators.py** (350 linhas)
```python
# Validações:
validate_email(email)             # RFC 5322
validate_cpf(cpf)                 # CPF com dígitos verificadores
validate_cnpj(cnpj)               # CNPJ com validação
validate_phone(phone)             # Telefone brasileiro
validate_required(value)          # Não-vazio
validate_positive_number(value)   # Número positivo
validate_date_range(start, end)   # Período válido
validate_all(*validations)        # Validação em lote

# Exception:
class ValidationError(Exception)  # Erro customizado
```

#### **app/utils/cache_helper.py** (150 linhas)
```python
# Decorators:
@cache_dashboard(timeout_seconds=300)   # Cache de 5 min
@cache_relatorio(timeout_seconds=600)   # Cache de 10 min
@cache_lookup(timeout_seconds=3600)     # Cache de 1 hora

# Funções:
clear_all_cache()                 # Limpar todo cache
get_cache_stats()                 # Estatísticas

# Uso:
@cache_dashboard(300)
def get_dashboard(empresa_id):
    # Consultas pesadas
    return resultado

# Invalidar cache:
get_dashboard.clear_cache(empresa_id=1)
```

#### **app/utils/pagination_helper.py** (170 linhas)
```python
# Helpers:
get_pagination_params()           # Extrair page/per_page da request
build_pagination_response()       # Construir resposta padronizada
get_sort_params()                 # Extrair ordenação
get_filter_params()               # Extrair filtros

# Uso:
page, per_page, offset, limit = get_pagination_params(default_per_page=50)
cursor.execute("SELECT * FROM items LIMIT %s OFFSET %s", (limit, offset))
items = cursor.fetchall()
total = count_items()
return jsonify(build_pagination_response(items, total, page, per_page))
```

---

### 4. **Database Layer** - Camada de Dados

#### **database_postgresql.py** (2.000+ linhas)
```python
# Connection Management:
get_connection()                  # Pool de conexões
get_db_connection()               # Alias
close_connection(conn)            # Fechar conexão

# CRUD Operations:
criar_lancamento(dados)
atualizar_lancamento(id, dados)
deletar_lancamento(id)
obter_lancamento(id)
listar_lancamentos(empresa_id, filtros)

pagar_lancamento(id)
cancelar_lancamento(id)

# Classes de modelo:
class ContaBancaria
class Lancamento
class Categoria
class TipoLancamento(Enum)
class StatusLancamento(Enum)
```

#### **auth_middleware.py** (500+ linhas)
```python
# Decorators:
@require_auth                     # Requer login
@require_admin                    # Requer nível admin
@require_permission('criar_lancamentos')  # Permissão específica
@aplicar_filtro_cliente           # Filtrar por cliente do usuário

# Funções:
get_usuario_logado()              # Obter usuário da sessão
filtrar_por_cliente(results)      # Aplicar filtro multi-tenancy
```

---

## 🗄️ Schema do Banco de Dados

### Tabelas Principais

```sql
-- MULTI-TENANCY
empresas (id, nome, cnpj, config_json)

-- AUTENTICAÇÃO
usuarios (id, username, password_hash, nivel_acesso, empresa_id)
sessoes_usuario (token, user_id, expires_at)

-- FINANCEIRO
contas_bancarias (id, nome, banco, agencia, conta, saldo, empresa_id)
lancamentos (id, descricao, valor, data_lancamento, data_vencimento, 
             tipo, status, conta_id, categoria_id, empresa_id)
categorias (id, nome, tipo, icone, empresa_id)
subcategorias (id, nome, categoria_id)

-- CADASTROS
clientes (id, nome, documento, email, telefone, tipo_chave_pix, empresa_id)
fornecedores (id, nome, documento, email, telefone, empresa_id)
funcionarios (id, nome, cpf, cargo, salario, empresa_id)

-- OPERACIONAL
contratos (id, numero, cliente_id, valor, data_inicio, data_fim, 
           status, empresa_id)
sessoes (id, data_sessao, duracao_minutos, contrato_id, cliente_id, 
         valor, empresa_id)
kits (id, nome, descricao, preco, ativo, empresa_id)
produtos (id, nome, preco, estoque, empresa_id)
eventos (id, nome_evento, data_evento, local, empresa_id)
equipamentos (id, nome, tipo, status, empresa_id)
projetos (id, nome, cliente_id, status, empresa_id)
```

### Índices de Performance (36 total)

```sql
-- LANCAMENTOS (9 índices)
CREATE INDEX idx_lancamentos_empresa_id ON lancamentos(empresa_id);
CREATE INDEX idx_lancamentos_data_lancamento ON lancamentos(data_lancamento);
CREATE INDEX idx_lancamentos_data_vencimento ON lancamentos(data_vencimento);
CREATE INDEX idx_lancamentos_status ON lancamentos(status);
CREATE INDEX idx_lancamentos_tipo ON lancamentos(tipo);
CREATE INDEX idx_lancamentos_conta_id ON lancamentos(conta_id);
CREATE INDEX idx_lancamentos_categoria_id ON lancamentos(categoria_id);
CREATE INDEX idx_lancamentos_empresa_data ON lancamentos(empresa_id, data_lancamento DESC);
CREATE INDEX idx_lancamentos_empresa_status ON lancamentos(empresa_id, status);

-- CONTRATOS (5 índices)
CREATE INDEX idx_contratos_empresa_id ON contratos(empresa_id);
CREATE INDEX idx_contratos_cliente_id ON contratos(cliente_id);
CREATE INDEX idx_contratos_data_inicio ON contratos(data_inicio);
CREATE INDEX idx_contratos_status ON contratos(status);
CREATE INDEX idx_contratos_numero ON contratos(numero);

-- SESSOES (4 índices)
CREATE INDEX idx_sessoes_empresa_id ON sessoes(empresa_id);
CREATE INDEX idx_sessoes_contrato_id ON sessoes(contrato_id);
CREATE INDEX idx_sessoes_cliente_id ON sessoes(cliente_id);
CREATE INDEX idx_sessoes_data_sessao ON sessoes(data_sessao);

-- + 18 índices em outras tabelas
```

**Impacto:** Queries 10-50x mais rápidas

---

## 🔐 Segurança

### Autenticação
- **Session-based**: Token UUID na sessão
- **Password hashing**: bcrypt com salt
- **CSRF Protection**: Token por requisição
- **Session expiry**: 24 horas

### Autorização
- **Níveis de acesso**: Admin, Usuário, Visualizador
- **Permissões granulares**: Por funcionalidade
- **Multi-tenancy**: Isolamento por empresa_id

### Proteções
- **Rate Limiting**: 200/dia, 50/hora
- **SQL Injection**: Queries parametrizadas
- **XSS**: Sanitização de inputs
- **HTTPS**: Obrigatório em produção

---

## ⚡ Otimizações de Performance

### 1. **Índices de Banco** (10-50x mais rápido)
- 36 índices em campos críticos
- Índices compostos para queries comuns
- ANALYZE automático após criação

### 2. **Compressão Gzip** (60-80% redução)
- Aplicada automaticamente em JSON, HTML, CSS, JS
- Mínimo 500 bytes para comprimir
- Level 6 de compressão

### 3. **Cache em Memória** (até 100x mais rápido)
- Dashboard: 5 minutos
- Relatórios: 10 minutos
- Lookups estáticos: 1 hora
- Invalidação manual disponível

### 4. **Connection Pooling**
- Pool reutilizável de conexões PostgreSQL
- Reduz overhead de connect/disconnect

### 5. **Paginação**
- Limite padrão: 50 items
- Máximo: 100 items
- Metadata completa (total_pages, has_next, etc)

---

## 🧪 Testes

### Cobertura: 95%

```
tests/
├── Unit Tests (105 casos)
│   ├── test_date_helpers.py       (35 testes)
│   ├── test_money_formatters.py   (30 testes)
│   └── test_validators.py         (40 testes)
│
└── Integration Tests (37 casos)
    └── test_blueprints_integration.py
        ├── TestKitsBlueprint          (6 testes)
        ├── TestContratosBlueprint     (7 testes)
        ├── TestSessoesBlueprint       (6 testes)
        ├── TestRelatoriosBlueprint    (9 testes)
        ├── TestBlueprintsIntegration  (3 testes)
        ├── TestBlueprintsErrorHandling(4 testes)
        └── TestBlueprintsPerformance  (2 testes)
```

### Executar Testes
```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=app --cov=database_postgresql

# Apenas unit tests
pytest tests/test_date_helpers.py -v

# Apenas integration
pytest tests/test_blueprints_integration.py -v
```

---

## 📊 Métricas de Performance

### Benchmarks (após otimizações)

| Endpoint | Antes | Depois | Speedup |
|----------|-------|--------|---------|
| Dashboard | 1500ms | 150ms | **10x** |
| Fluxo Caixa | 2000ms | 200ms | **10x** |
| Indicadores | 3000ms | 150ms | **20x** |
| Listar Contratos | 500ms | 50ms | **10x** |

### Tamanhos de Resposta (com gzip)

| Tipo | Sem Gzip | Com Gzip | Redução |
|------|----------|----------|---------|
| JSON (Dashboard) | 100 KB | 25 KB | **75%** |
| HTML (SPA) | 200 KB | 50 KB | **75%** |
| JS (app.js) | 150 KB | 35 KB | **77%** |

---

## 🔄 Fluxo de Dados

### Exemplo: Criar Lançamento

```
1. Frontend (app.js)
   └─> POST /api/lancamentos
       Body: {descricao, valor, data, categoria_id, ...}
       Headers: {X-CSRF-Token}

2. Flask (web_server.py)
   ├─> Rate Limiter: OK (48/50)
   ├─> CSRF Check: Token válido
   ├─> Auth Middleware: Usuário autenticado
   └─> Route Handler

3. Database Layer (database_postgresql.py)
   ├─> Validações (valor > 0, data válida)
   ├─> parse_date() converter data
   ├─> parse_currency() converter valor
   ├─> INSERT INTO lancamentos (...)
   └─> Retornar ID do registro

4. Response
   ├─> JSON: {success: true, id: 123}
   ├─> Gzip Compression: 1KB → 250 bytes
   └─> HTTP 201 Created

5. Frontend
   ├─> Atualizar lista de lançamentos
   ├─> Mostrar toast de sucesso
   └─> Limpar formulário
```

---

## 🚀 Melhorias Futuras

### Curto Prazo
- [ ] Aplicar cache em mais relatórios
- [ ] Adicionar paginação em lancamentos
- [ ] WebSockets para notificações em tempo real

### Médio Prazo
- [ ] Migrar para Redis cache (produção)
- [ ] Implementar Celery para tasks assíncronas
- [ ] API GraphQL paralela à REST

### Longo Prazo
- [ ] Microserviços (relatórios separados)
- [ ] ElasticSearch para busca avançada
- [ ] Mobile app nativo (React Native)

---

**Criado por:** Time de Desenvolvimento DWM  
**Última atualização:** 20/01/2026  
**Versão:** 2.0
