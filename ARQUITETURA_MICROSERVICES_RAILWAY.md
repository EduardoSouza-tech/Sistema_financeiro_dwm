# 🏗️ ARQUITETURA MICROSERVICES - RAILWAY
## Planejamento de Migração: Monolito → Microserviços Modulares

**Data:** 13/02/2026  
**Status:** 📋 PLANEJAMENTO (NÃO IMPLEMENTADO)  
**Objetivo:** Separar sistema monolítico em módulos independentes para melhorar disponibilidade, manutenibilidade e isolamento de falhas

---

## 📊 SITUAÇÃO ATUAL (MONOLITO)

### Arquitetura Existente
```
┌─────────────────────────────────────────────────────────────┐
│                   Railway Service (ÚNICO)                    │
│                 sistemafinanceirodwm-production              │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              web_server.py (11.000 linhas)          │   │
│  │                                                       │   │
│  │  • Interface (HTML/JS)                               │   │
│  │  • Dashboard                                         │   │
│  │  • Financeiro (Receitas/Despesas/Extratos)          │   │
│  │  • Relatórios (Fluxo/Análises/Indicadores)          │   │
│  │  • Cadastros (Contas/Categorias/Clientes)           │   │
│  │  • Operacional (Contratos/Agenda/Kits/Eventos)      │   │
│  │  • Recursos Humanos (Folha de Pagamento)            │   │
│  │  • Autenticação & Sessões                           │   │
│  │  • Admin & Usuários                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            PostgreSQL (Banco Único)                  │   │
│  │         postgres-volume (dados persistentes)         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### ❌ PROBLEMAS IDENTIFICADOS

1. **Indisponibilidade Total em Deploys**
   - Qualquer mudança causa redeploy completo (~2-3 minutos offline)
   - Todos os usuários perdem conexão simultaneamente
   - Sessões ativas são perdidas
   - Trabalho em andamento pode ser perdido

2. **Falhas em Cascata**
   - Bug em uma funcionalidade derruba o sistema inteiro
   - Erro em "Eventos" afeta usuários em "Financeiro"
   - Não há isolamento de falhas

3. **Manutenção Complexa**
   - 11.000+ linhas em um único arquivo
   - Difícil testar mudanças isoladamente
   - Alto risco em cada deploy
   - Logs misturados de todos os módulos

4. **Escalabilidade Limitada**
   - Impossível escalar módulos específicos
   - Dashboard pesado consome recursos de todos os outros módulos
   - Não há priorização de recursos

5. **Desenvolvimento Serial**
   - Múltiplos desenvolvedores causam conflitos Git
   - Deploys frequentes impactam todos
   - Testes de módulos novos afetam produção

---

## ✅ SOLUÇÃO PROPOSTA: ARQUITETURA MODULAR

### Visão Geral
```
                        ┌──────────────────────────────────────┐
                        │      RAILWAY PROJECT: ERP_WEB        │
                        └──────────────────────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
┌───────────────────┐          ┌───────────────────┐          ┌───────────────────┐
│   SERVICE #1      │          │   SERVICE #2      │          │   SERVICE #3      │
│   🎨 FRONTEND     │          │   🔐 AUTH-API     │          │   💰 FINANCEIRO   │
│                   │          │                   │          │      API          │
│  • interface.html │◄────────►│  • Login/Logout   │◄────────►│  • Receitas       │
│  • app.js         │   JWT    │  • Sessões        │   Auth   │  • Despesas       │
│  • utils.js       │  Token   │  • Permissões     │  Check   │  • Extratos       │
│  • modals.js      │          │  • Multi-Tenant   │          │  • Remessas       │
│  • CSS/Assets     │          │  • Heartbeat      │          │                   │
│                   │          │                   │          │  PORT: 5002       │
│  PORT: 5000       │          │  PORT: 5001       │          └───────────────────┘
└───────────────────┘          └───────────────────┘                    │
        │                                                                │
        │          ┌───────────────────┐          ┌───────────────────┐
        └─────────►│   SERVICE #4      │          │   SERVICE #5      │
                   │   📊 RELATORIOS   │          │   📋 CADASTROS    │
                   │      API          │          │      API          │
                   │                   │          │                   │
                   │  • Fluxo Caixa    │          │  • Contas Banc.   │
                   │  • Análises       │          │  • Categorias     │
                   │  • Comparativos   │          │  • Clientes       │
                   │  • Indicadores    │          │  • Fornecedores   │
                   │  • Inadimplência  │          │                   │
                   │                   │          │  PORT: 5004       │
                   │  PORT: 5003       │          └───────────────────┘
                   └───────────────────┘                    │
                             │                              │
        ┌────────────────────┼──────────────────────────────┘
        │                    │                              
        ▼                    ▼                              
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│   SERVICE #6      │  │   SERVICE #7      │  │   SERVICE #8      │
│  ⚙️ OPERACIONAL   │  │  👥 RH API        │  │  📊 DASHBOARD     │
│      API          │  │                   │  │      API          │
│                   │  │  • Folha Pgto     │  │                   │
│  • Contratos      │  │  • Funcionários   │  │  • Métricas       │
│  • Agenda Foto    │  │  • Eventos RH     │  │  • Widgets        │
│  • Kits/Estoque   │  │                   │  │  • Gráficos       │
│  • Eventos        │  │  PORT: 5006       │  │  • Cache Redis    │
│                   │  └───────────────────┘  │                   │
│  PORT: 5005       │                         │  PORT: 5007       │
└───────────────────┘                         └───────────────────┘
        │                                               │
        └───────────────────────┬───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │     PostgreSQL DB      │
                    │   (Compartilhado)      │
                    │                        │
                    │  • Multi-Tenant RLS    │
                    │  • Connection Pooling  │
                    │  • Volume Persistente  │
                    └───────────────────────┘
```

---

## 🎯 DETALHAMENTO DOS SERVIÇOS

### 🎨 **SERVICE #1: FRONTEND (Interface)**
**Responsabilidade:** Servir interface estática  
**Tecnologia:** Flask + Static Files  
**Porta:** 5000 (pública)  
**Uptime Crítico:** ⭐⭐⭐⭐⭐

**Conteúdo:**
```
frontend/
├── app.py (Flask simples, só serve arquivos)
├── templates/
│   └── interface_nova.html
├── static/
│   ├── app.js
│   ├── utils.js
│   ├── modals.js
│   ├── lazy-loader.js
│   ├── regras_conciliacao.js
│   ├── agenda_calendar.js
│   └── css/
└── requirements.txt (Flask, Flask-CORS, Flask-Compress)
```

**Vantagens:**
- ✅ Deploy não afeta usuários já logados
- ✅ Cache agressivo (Service Worker)
- ✅ Pode usar CDN futuramente
- ✅ Atualização de layout sem derrubar APIs

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
```

---

### 🔐 **SERVICE #2: AUTH-API (Autenticação)**
**Responsabilidade:** Gerenciar autenticação, permissões e sessões  
**Tecnologia:** Flask + JWT + PostgreSQL  
**Porta:** 5001 (interna)  
**Uptime Crítico:** ⭐⭐⭐⭐⭐

**Endpoints:**
```
POST   /api/login                    # Login de usuário
POST   /api/logout                   # Logout
GET    /api/check-auth               # Verificar autenticação
POST   /api/renovar-sessao           # Renovar sessão/heartbeat
GET    /api/permissoes               # Listar permissões do usuário
GET    /api/usuarios                 # Listar usuários (admin)
POST   /api/usuarios                 # Criar usuário (admin)
PUT    /api/usuarios/<id>            # Editar usuário (admin)
DELETE /api/usuarios/<id>            # Deletar usuário (admin)
GET    /api/empresas                 # Listar empresas (multi-tenant)
POST   /api/empresas                 # Criar empresa (admin)
```

**Conteúdo:**
```
auth-api/
├── app.py (rotas de autenticação)
├── auth_middleware.py
├── auth_functions.py
├── config.py
├── database_postgresql.py
├── logger_config.py
└── requirements.txt
```

**Segurança:**
- JWT com expiração de 12 horas
- Refresh tokens opcionais
- Rate limiting (5 tentativas/min)
- Logs de auditoria
- Session tokens em Redis (cache distribuído)

---

### 💰 **SERVICE #3: FINANCEIRO-API**
**Responsabilidade:** Gestão financeira completa  
**Tecnologia:** Flask + PostgreSQL  
**Porta:** 5002 (interna)  
**Uptime Crítico:** ⭐⭐⭐⭐⭐

**Endpoints:**
```
# Lançamentos
GET    /api/lancamentos              # Listar (com lazy loading)
POST   /api/lancamentos              # Criar
PUT    /api/lancamentos/<id>         # Editar
DELETE /api/lancamentos/<id>         # Deletar
GET    /api/lancamentos/<id>         # Detalhes

# Extratos Bancários
GET    /api/extratos                 # Listar extratos
POST   /api/extratos/upload          # Upload OFX
POST   /api/extratos/conciliacao     # Conciliar transações

# Remessas
GET    /api/remessas                 # Listar remessas
POST   /api/remessas/gerar           # Gerar arquivo CNAB
```

**Conteúdo:**
```
financeiro-api/
├── app.py
├── lancamentos_routes.py
├── extratos_routes.py
├── remessas_routes.py
├── database_postgresql.py
├── ofx_processor.py
└── requirements.txt
```

---

### 📊 **SERVICE #4: RELATORIOS-API**
**Responsabilidade:** Geração de relatórios e análises  
**Tecnologia:** Flask + PostgreSQL + Cache  
**Porta:** 5003 (interna)  
**Uptime Crítico:** ⭐⭐⭐

**Endpoints:**
```
GET /api/relatorios/fluxo-caixa      # Fluxo de caixa
GET /api/relatorios/analise          # Análise detalhada
GET /api/relatorios/comparativo      # Comparativo de períodos
GET /api/relatorios/indicadores      # Indicadores financeiros
GET /api/relatorios/inadimplencia    # Relatório de inadimplência
POST /api/relatorios/export          # Exportar para Excel/PDF
```

**Otimizações:**
- Cache de 5 minutos para relatórios pesados
- Queries otimizadas com índices
- Processamento assíncrono para exports

---

### 📋 **SERVICE #5: CADASTROS-API**
**Responsabilidade:** Gestão de cadastros mestres  
**Tecnologia:** Flask + PostgreSQL  
**Porta:** 5004 (interna)  
**Uptime Crítico:** ⭐⭐⭐⭐

**Endpoints:**
```
# Contas Bancárias
GET    /api/contas                   # Listar
POST   /api/contas                   # Criar
PUT    /api/contas/<id>              # Editar
DELETE /api/contas/<id>              # Deletar

# Categorias
GET    /api/categorias               # Listar
POST   /api/categorias               # Criar
PUT    /api/categorias/<id>          # Editar
DELETE /api/categorias/<id>          # Deletar

# Clientes
GET    /api/clientes                 # Listar
POST   /api/clientes                 # Criar
PUT    /api/clientes/<id>            # Editar
DELETE /api/clientes/<id>            # Deletar

# Fornecedores
GET    /api/fornecedores             # Listar
POST   /api/fornecedores             # Criar
PUT    /api/fornecedores/<id>        # Editar
DELETE /api/fornecedores/<id>        # Deletar
```

---

### ⚙️ **SERVICE #6: OPERACIONAL-API**
**Responsabilidade:** Gestão operacional (contratos, agenda, kits, eventos)  
**Tecnologia:** Flask + PostgreSQL + Google Calendar  
**Porta:** 5005 (interna)  
**Uptime Crítico:** ⭐⭐⭐

**Endpoints:**
```
# Contratos
GET    /api/contratos                # Listar
POST   /api/contratos                # Criar
PUT    /api/contratos/<id>           # Editar
DELETE /api/contratos/<id>           # Deletar

# Agenda de Fotografia
GET    /api/agenda                   # Listar sessões
POST   /api/agenda                   # Criar sessão
PUT    /api/agenda/<id>              # Editar sessão
DELETE /api/agenda/<id>              # Deletar sessão
POST   /api/agenda/sync-calendar     # Sincronizar Google Calendar

# Kits de Equipamentos
GET    /api/kits                     # Listar kits
POST   /api/kits                     # Criar kit
PUT    /api/kits/<id>                # Editar kit
DELETE /api/kits/<id>                # Deletar kit
POST   /api/kits/alocar              # Alocar kit para sessão

# Eventos
GET    /api/eventos                  # Listar
POST   /api/eventos                  # Criar
PUT    /api/eventos/<id>             # Editar
DELETE /api/eventos/<id>             # Deletar
```

---

### 👥 **SERVICE #7: RH-API**
**Responsabilidade:** Recursos Humanos e Folha de Pagamento  
**Tecnologia:** Flask + PostgreSQL  
**Porta:** 5006 (interna)  
**Uptime Crítico:** ⭐⭐⭐

**Endpoints:**
```
# Funcionários
GET    /api/funcionarios             # Listar
POST   /api/funcionarios             # Criar
PUT    /api/funcionarios/<id>        # Editar
DELETE /api/funcionarios/<id>        # Deletar

# Folha de Pagamento
GET    /api/folha/calcular           # Calcular folha do mês
POST   /api/folha/processar          # Gerar folha
GET    /api/folha/historico          # Histórico de folhas
POST   /api/folha/export             # Exportar para SEFIP
```

---

### 📊 **SERVICE #8: DASHBOARD-API**
**Responsabilidade:** Agregação de dados e métricas em tempo real  
**Tecnologia:** Flask + PostgreSQL + Redis (cache)  
**Porta:** 5007 (interna)  
**Uptime Crítico:** ⭐⭐⭐⭐

**Endpoints:**
```
GET /api/dashboard                   # Dados completos do dashboard
GET /api/dashboard/metrics           # Métricas agregadas
GET /api/dashboard/widgets           # Widgets individuais
```

**Features:**
- Cache de 1 minuto em Redis
- Consultas agregadas otimizadas
- SSE (Server-Sent Events) para atualizações em tempo real

---

## 🛠️ CONFIGURAÇÃO NO RAILWAY

### Estrutura de Repositórios

**Opção A: Monorepo (Recomendado para inicio)**
```
sistema_financeiro_dwm/
├── frontend/                    # SERVICE #1
│   ├── Dockerfile
│   ├── app.py
│   ├── templates/
│   └── static/
├── auth-api/                    # SERVICE #2
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── financeiro-api/              # SERVICE #3
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── relatorios-api/              # SERVICE #4
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── cadastros-api/               # SERVICE #5
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── operacional-api/             # SERVICE #6
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── rh-api/                      # SERVICE #7
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── dashboard-api/               # SERVICE #8
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── shared/                      # Código compartilhado
│   ├── database_postgresql.py
│   ├── auth_middleware.py
│   ├── logger_config.py
│   └── config.py
└── docker-compose.yml          # Para desenvolvimento local
```

**Opção B: Multi-Repo (Para produção escalável)**
- Cada serviço em repositório separado
- Deploy independente total
- CI/CD isolado por serviço

---

### Railway Services Configuration

Para cada serviço, criar no Railway Dashboard:

#### 1️⃣ **FRONTEND Service**
```yaml
# railway.toml (na pasta frontend/)
[build]
  dockerfilePath = "frontend/Dockerfile"

[deploy]
  startCommand = "gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app"
  
[env]
  PORT = "5000"
  AUTH_API_URL = "${{AUTH_API.RAILWAY_PRIVATE_DOMAIN}}"
  FINANCEIRO_API_URL = "${{FINANCEIRO_API.RAILWAY_PRIVATE_DOMAIN}}"
  # ... outras APIs
```

#### 2️⃣ **AUTH-API Service**
```yaml
[build]
  dockerfilePath = "auth-api/Dockerfile"

[deploy]
  startCommand = "gunicorn --bind 0.0.0.0:$PORT --workers 4 app:app"
  
[env]
  PORT = "5001"
  DATABASE_URL = "${{Postgres.DATABASE_URL}}"
  JWT_SECRET = "${{JWT_SECRET}}"  # Variável de ambiente compartilhada
  REDIS_URL = "${{Redis.REDIS_URL}}" (opcional)
```

#### 3️⃣ **FINANCEIRO-API Service**
```yaml
[build]
  dockerfilePath = "financeiro-api/Dockerfile"

[deploy]
  startCommand = "gunicorn --bind 0.0.0.0:$PORT --workers 4 app:app"
  
[env]
  PORT = "5002"
  DATABASE_URL = "${{Postgres.DATABASE_URL}}"
  AUTH_API_URL = "${{AUTH_API.RAILWAY_PRIVATE_DOMAIN}}"
```

*Repetir padrão para Services #4, #5, #6, #7, #8...*

---

### Comunicação Entre Serviços

#### Railway Private Networking
```python
# No frontend (app.js):
const API_URLS = {
    auth: 'https://auth-api.railway.internal',      // rede privada Railway
    financeiro: 'https://financeiro-api.railway.internal',
    relatorios: 'https://relatorios-api.railway.internal',
    cadastros: 'https://cadastros-api.railway.internal',
    operacional: 'https://operacional-api.railway.internal',
    rh: 'https://rh-api.railway.internal',
    dashboard: 'https://dashboard-api.railway.internal'
};

// Chamada com autenticação
async function callAPI(service, endpoint, options = {}) {
    const token = sessionStorage.getItem('jwt_token');
    const response = await fetch(`${API_URLS[service]}${endpoint}`, {
        ...options,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
    
    if (response.status === 401) {
        // Token expirado, renovar ou redirecionar para login
        window.location.href = '/login';
    }
    
    return response.json();
}

// Exemplo de uso
const lancamentos = await callAPI('financeiro', '/api/lancamentos?tipo=RECEITA');
```

#### Middleware de Autenticação Compartilhado
```python
# shared/auth_middleware.py
import requests
from functools import wraps
from flask import request, jsonify
import os

AUTH_API_URL = os.getenv('AUTH_API_URL', 'http://auth-api.railway.internal')

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extrair token do header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token não fornecido'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Validar token com AUTH-API
        try:
            response = requests.post(
                f'{AUTH_API_URL}/api/validate-token',
                json={'token': token},
                timeout=2
            )
            
            if response.status_code != 200:
                return jsonify({'error': 'Token inválido'}), 401
            
            # Anexar dados do usuário ao request
            request.user = response.json()['user']
            
        except requests.exceptions.RequestException as e:
            return jsonify({'error': 'Erro ao validar token'}), 500
        
        return f(*args, **kwargs)
    
    return decorated_function

# Uso em cada API
from shared.auth_middleware import require_auth

@app.route('/api/lancamentos', methods=['GET'])
@require_auth
def listar_lancamentos():
    usuario = request.user  # Dados do usuário já validados
    empresa_id = usuario['empresa_id']
    # ... lógica do endpoint
```

---

## 🚀 ESTRATÉGIA DE MIGRAÇÃO

### Fase 1: Preparação (Semana 1)
**Objetivo:** Estruturar repositório e configurar Railway

✅ **Tarefas:**
1. Criar estrutura de pastas no repositório
2. Criar Dockerfiles para cada serviço
3. Extrair código compartilhado para `/shared`
4. Configurar Railway com 8 services (inicialmente desabilitados)
5. Configurar rede privada Railway
6. Criar variáveis de ambiente compartilhadas

**Sem impacto em produção** ✨

---

### Fase 2: Migração do AUTH-API (Semana 2)
**Objetivo:** Separar autenticação (mais crítico)

✅ **Tarefas:**
1. Criar `auth-api/` com endpoints de login/logout/sessão
2. Implementar JWT tokens
3. Deploy paralelo no Railway (novo service)
4. Configurar Redis para session storage
5. Testar autenticação no novo service
6. Atualizar frontend para usar AUTH-API
7. Monitorar por 3 dias

**Rollback:** Frontend pode voltar a chamar monolito se der problema

---

### Fase 3: Migração do FRONTEND (Semana 3)
**Objetivo:** Separar interface estática

✅ **Tarefas:**
1. Criar `frontend/` com app.py minimalista
2. Copiar templates/ e static/
3. Configurar Service Worker para cache
4. Deploy paralelo no Railway
5. Testar carregamento de todos os módulos
6. Apontar DNS para novo frontend
7. Manter monolito como fallback

**Vantagem:** Atualizações de interface não derrubam APIs

---

### Fase 4: Migração FINANCEIRO-API (Semana 4)
**Objetivo:** Separar módulo mais usado

✅ **Tarefas:**
1. Criar `financeiro-api/` com rotas de lançamentos/extratos/remessas
2. Copiar funções relacionadas do monolito
3. Adaptar para usar AUTH-API
4. Deploy paralelo
5. Testar CRUD completo
6. Feature flag no frontend para usar novo endpoint
7. Monitorar performance e erros

**Rollback:** Feature flag volta para monolito

---

### Fase 5: Migração dos Demais Módulos (Semanas 5-8)
**Ordem sugerida:**
1. CADASTROS-API (semana 5) - usado por todos os outros
2. DASHBOARD-API (semana 6) - leitura assíncrona
3. OPERACIONAL-API (semana 7) - menos crítico
4. RH-API (semana 7) - menos crítico
5. RELATORIOS-API (semana 8) - pode ser assíncrono

**Para cada módulo:**
- Deploy paralelo
- Feature flag no frontend
- Teste por 2-3 dias
- Rollback se necessário

---

### Fase 6: Desativação do Monolito (Semana 9)
**Objetivo:** Remover código legado

✅ **Tarefas:**
1. Confirmar que todos os módulos migraram
2. Verificar logs de acesso ao monolito (deve ser zero)
3. Desabilitar service do monolito no Railway
4. Aguardar 1 semana para problemas
5. Deletar service do monolito
6. Limpar repositório

🎉 **Migração completa!**

---

## 📈 BENEFÍCIOS DA ARQUITETURA MODULAR

### 1. **Zero Downtime em Deploys**
```
ANTES (Monolito):
Deploy financeiro → Sistema TODO cai por 2-3 min

DEPOIS (Microserviços):
Deploy financeiro-api → Só o módulo Financeiro fica 10 seg offline
Outros módulos: 100% operacionais
```

### 2. **Isolamento de Falhas**
```
ANTES:
Bug em Eventos → Sistema TODO retorna erro 500

DEPOIS:
Bug em Eventos → Só aba "Eventos" afetada
Dashboard, Financeiro, RH: funcionando normalmente
```

### 3. **Deploys Independentes**
```
ANTES:
1 deploy/dia (risco alto, demora para todos os módulos)

DEPOIS:
N deploys/dia (1 por módulo, sem afetar outros)
```

### 4. **Escalabilidade Seletiva**
```
ANTES:
1 instância Flask com 4 workers = 4 requests simultâneos para TODO o sistema

DEPOIS:
- FRONTEND: 2 workers (servir HTML/JS)
- AUTH-API: 4 workers (muitas validações)
- FINANCEIRO-API: 6 workers (módulo mais usado)
- RELATORIOS-API: 2 workers (menos uso)
- Outros: 2 workers cada

TOTAL: 20 workers especializados!
```

### 5. **Desenvolvimento Paralelo**
```
ANTES:
Dev A edita web_server.py → Conflito Git com Dev B

DEPOIS:
Dev A trabalha em financeiro-api/
Dev B trabalha em rh-api/
Sem conflitos! Deploys independentes!
```

### 6. **Logs Estruturados**
```
ANTES:
[ERROR] Line 3261 - dateutil not found (qual módulo?)

DEPOIS:
[FINANCEIRO-API] [ERROR] dateutil not found
[RH-API] [INFO] Folha processada com sucesso
```

### 7. **Custos Otimizados**
```
Railway cobra por uso de CPU/RAM/Rede

ANTES:
1 service grande sempre com CPU alta

DEPOIS:
- FRONTEND: ~5 MB RAM, 0.1 CPU (cache)
- AUTH-API: ~50 MB RAM, 0.2 CPU (validações rápidas)
- FINANCEIRO-API: ~100 MB RAM, 0.5 CPU (queries pesadas)
- RELATORIOS-API: ~200 MB RAM, 0.8 CPU (agregações)

Sleep automático dos services pouco usados = economia!
```

### 8. **Testes Isolados**
```
ANTES:
Testar função de relatórios = rodar todos os testes

DEPOIS:
pytest relatorios-api/tests/ (só testes do módulo)
CI/CD roda testes apenas do serviço alterado
```

---

## ⚠️ DESAFIOS E SOLUÇÕES

### Desafio 1: Latência de Rede
**Problema:** Chamadas entre services adicionam 10-50ms  
**Solução:**
- Railway Private Network (latência < 5ms dentro do datacenter)
- Cache com Redis para dados frequentes
- GraphQL Federation (opcional, para agregar dados)

### Desafio 2: Transações Distribuídas
**Problema:** Criar lançamento + atualizar saldo banco (2 APIs)  
**Solução:**
- Pattern SAGA (orquestração de transações)
- Event Sourcing (opcional, para auditoria)
- Rollback manual com compensação

Exemplo:
```python
# financeiro-api/app.py
@app.route('/api/lancamentos', methods=['POST'])
@require_auth
def criar_lancamento():
    data = request.json
    
    try:
        # 1. Criar lançamento no DB
        lancamento_id = criar_lancamento_db(data)
        
        # 2. Atualizar saldo em CADASTROS-API (chamada HTTP)
        response = requests.post(
            f'{CADASTROS_API_URL}/api/contas/{data["conta_id"]}/atualizar-saldo',
            json={'valor': data['valor'], 'tipo': data['tipo']},
            headers={'Authorization': request.headers.get('Authorization')}
        )
        
        if response.status_code != 200:
            # Compensação: deletar lançamento criado
            deletar_lancamento_db(lancamento_id)
            return jsonify({'error': 'Erro ao atualizar saldo'}), 500
        
        return jsonify({'success': True, 'id': lancamento_id}), 201
    
    except Exception as e:
        logger.error(f'Erro ao criar lançamento: {e}')
        return jsonify({'error': str(e)}), 500
```

### Desafio 3: Debugging Distribuído
**Problema:** Erro em uma API afeta outra, difícil rastrear  
**Solução:**
- Correlation IDs (UUID propagado em headers)
- Distributed Tracing (Sentry, Datadog)
- Logs estruturados JSON

```python
# Middleware para adicionar correlation_id
import uuid

@app.before_request
def add_correlation_id():
    # Obter ou criar correlation ID
    correlation_id = request.headers.get('X-Correlation-Id') or str(uuid.uuid4())
    g.correlation_id = correlation_id
    
    # Propagar para próximas chamadas
    logger.info(f'[{correlation_id}] Request: {request.method} {request.path}')

# Ao chamar outro service
headers = {'X-Correlation-Id': g.correlation_id}
```

### Desafio 4: Consistência de Dados
**Problema:** Categorias atualizadas em CADASTROS mas cache desatualizado em FINANCEIRO  
**Solução:**
- Redis Pub/Sub para invalidação de cache
- Webhooks entre services
- Polling periódico (simples, mas menos eficiente)

```python
# CADASTROS-API publica evento
redis_client.publish('categorias:updated', json.dumps({'empresa_id': 20}))

# FINANCEIRO-API subscrito ao canal
def on_categoria_updated(message):
    data = json.loads(message['data'])
    cache.delete(f'categorias:{data["empresa_id"]}')
```

---

## 💰 ANÁLISE DE CUSTOS - RAILWAY

### Cenário Atual: Monolito
```
1 Service (web_server):
- Memory: ~200 MB
- CPU: ~0.5 vCPU
- Network: ~50 GB/mês
- Custo: ~$5-7/mês

1 PostgreSQL:
- Memory: ~50 MB
- Storage: 1 GB
- Custo: ~$5/mês

TOTAL: ~$10-12/mês
```

### Cenário Futuro: Microserviços
```
8 Services:
1. FRONTEND: ~20 MB RAM, 0.05 CPU = $1/mês
2. AUTH-API: ~50 MB RAM, 0.1 CPU = $2/mês
3. FINANCEIRO-API: ~100 MB RAM, 0.3 CPU = $4/mês
4. RELATORIOS-API: ~150 MB RAM, 0.4 CPU = $5/mês
5. CADASTROS-API: ~50 MB RAM, 0.1 CPU = $2/mês
6. OPERACIONAL-API: ~50 MB RAM, 0.1 CPU = $2/mês
7. RH-API: ~50 MB RAM, 0.1 CPU = $2/mês
8. DASHBOARD-API: ~80 MB RAM, 0.2 CPU = $3/mês

PostgreSQL (compartilhado): $5/mês
Redis (cache): $5/mês

TOTAL: ~$31/mês
```

**Aumento de ~$20/mês (~R$ 100/mês)**

### ROI (Retorno sobre Investimento)
```
Benefícios mensuráveis:

1. Redução de Downtime: 
   - ANTES: 10 deploys/mês × 3 min = 30 min offline/mês
   - DEPOIS: 10 deploys/mês × 10 seg = 1.6 min offline/mês
   - Economia: 28.4 min/mês × 10 usuários = 284 min produtivos salvos
   
2. Bugs Isolados:
   - ANTES: 1 bug/semana derruba tudo por 15 min = 60 min/mês
   - DEPOIS: Bug afeta só 1 módulo (20% dos usuários) = 12 min/mês
   - Economia: 48 min/mês × 10 usuários = 480 min produtivos salvos

3. Desenvolvimento Mais Rápido:
   - Menos conflitos Git = -30% tempo de merge
   - Testes isolados = -50% tempo de CI/CD
   - Deploy fearless = +50% velocidade de iteração

TOTAL: ~764 min salvos/mês = 12.7 horas/mês
Se hora de trabalho = R$ 50, economia mensal = R$ 635

ROI = (R$ 635 - R$ 100) / R$ 100 = 535% 🚀
```

---

## 🔐 SEGURANÇA NA ARQUITETURA DISTRIBUÍDA

### 1. Autenticação JWT
```python
# AUTH-API gera token
import jwt
import datetime

def gerar_token(usuario_id, empresa_id):
    payload = {
        'usuario_id': usuario_id,
        'empresa_id': empresa_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
```

### 2. Validação em Cada API
```python
# Middleware compartilhado
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            request.user_id = payload['usuario_id']
            request.empresa_id = payload['empresa_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(*args, **kwargs)
    return decorated
```

### 3. Row-Level Security (RLS)
```sql
-- Aplicado em TODAS as tabelas
ALTER TABLE lancamentos ENABLE ROW LEVEL SECURITY;

CREATE POLICY lancamentos_multi_tenant ON lancamentos
USING (empresa_id = current_setting('app.current_empresa_id')::INTEGER);

-- Cada API define empresa_id na conexão
SET app.current_empresa_id = 20;
```

### 4. Rate Limiting por Service
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.headers.get('Authorization'),  # Por token
    default_limits=["100 per minute"]
)

@app.route('/api/lancamentos', methods=['POST'])
@limiter.limit("10 per minute")  # Limite mais restritivo para POST
@require_auth
def criar_lancamento():
    # ...
```

### 5. CORS Restrito
```python
from flask_cors import CORS

# Só permite frontend oficial
CORS(app, origins=[
    'https://sistema.seudominio.com',
    'http://localhost:5000'  # Desenvolvimento
])
```

---

## 📊 MONITORAMENTO E OBSERVABILIDADE

### 1. Health Checks
```python
# Em CADA API
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'FINANCEIRO-API',
        'version': '1.2.0',
        'timestamp': datetime.utcnow().isoformat(),
        'dependencies': {
            'database': 'ok',
            'auth_api': 'ok'
        }
    }), 200

# Railway faz ping /health a cada 30 segundos
# Se falhar 3 vezes seguidas → restart automático
```

### 2. Métricas Centralizadas
```python
# Sentry para erros
import sentry_sdk
sentry_sdk.init(
    dsn="https://...",
    environment="production",
    traces_sample_rate=0.1  # 10% das transações trackeadas
)

# Logs estruturados
import logging
import json

logger = logging.getLogger(__name__)
logger.info(json.dumps({
    'event': 'lancamento_criado',
    'usuario_id': request.user_id,
    'empresa_id': request.empresa_id,
    'valor': 1500.00,
    'timestamp': datetime.utcnow().isoformat()
}))
```

### 3. Dashboard Railway
```
Railway fornece automaticamente:
- CPU Usage por service
- Memory Usage por service
- Network I/O
- Request Count
- Error Rate (5xx)
- P50/P95/P99 Latency
```

### 4. Alertas
```yaml
# railway.toml
[alerts]
  [[alerts.rule]]
    type = "memory"
    threshold = 90  # Alerta se RAM > 90%
    
  [[alerts.rule]]
    type = "error_rate"
    threshold = 5  # Alerta se error rate > 5%
    
  [[alerts.rule]]
    type = "latency"
    threshold = 2000  # Alerta se P95 > 2s
```

---

## 🧪 ESTRATÉGIA DE TESTES

### 1. Testes Unitários (por service)
```bash
# Executar testes de um módulo específico
cd financeiro-api/
pytest tests/ --cov=app --cov-report=html

# CI/CD roda apenas testes do service modificado
```

### 2. Testes de Integração
```python
# Mockar chamadas entre APIs
import responses

@responses.activate
def test_criar_lancamento_atualiza_saldo():
    # Mock AUTH-API
    responses.add(
        responses.POST,
        'http://auth-api/api/validate-token',
        json={'user': {'id': 1, 'empresa_id': 20}},
        status=200
    )
    
    # Mock CADASTROS-API
    responses.add(
        responses.POST,
        'http://cadastros-api/api/contas/1/atualizar-saldo',
        json={'success': True},
        status=200
    )
    
    # Testar endpoint
    response = client.post('/api/lancamentos', json={...})
    assert response.status_code == 201
```

### 3. Testes End-to-End (Staging)
```python
# Ambiente staging com todos os services
# Playwright/Selenium para testes de UI
from playwright.sync_api import sync_playwright

def test_fluxo_completo_lancamento():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # 1. Login
        page.goto('https://staging.sistema.com/login')
        page.fill('#username', 'teste@email.com')
        page.fill('#password', 'senha123')
        page.click('#btn-login')
        
        # 2. Criar lançamento
        page.click('#btn-financeiro')
        page.click('#btn-novo-lancamento')
        # ...
        
        # 3. Verificar se apareceu na tabela
        assert page.inner_text('#tabela-lancamentos tr:first-child')
```

---

## 🚦 COMO COMEÇAR (PASSO A PASSO)

### Semana 1: Setup Inicial

#### Dia 1-2: Estrutura de Repositório
```bash
cd Sistema_financeiro_dwm/

# Criar estrutura de pastas
mkdir -p frontend/{templates,static}
mkdir -p auth-api
mkdir -p financeiro-api
mkdir -p relatorios-api
mkdir -p cadastros-api
mkdir -p operacional-api
mkdir -p rh-api
mkdir -p dashboard-api
mkdir -p shared

# Criar Dockerfiles básicos
cat > frontend/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "2", "app:app"]
EOF

# Replicar para outros services
cp frontend/Dockerfile auth-api/
cp frontend/Dockerfile financeiro-api/
# ... etc
```

#### Dia 3-4: Railway Setup
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Criar projeto
railway init

# Adicionar PostgreSQL
railway add --plugin postgres

# Adicionar Redis (opcional)
railway add --plugin redis

# Criar services
railway service create frontend
railway service create auth-api
railway service create financeiro-api
# ... etc (7 services no total)
```

#### Dia 5: Configuração de Variáveis
```bash
# Definir variáveis compartilhadas
railway variables set JWT_SECRET="sua-chave-secreta-aqui"
railway variables set DATABASE_URL="${{Postgres.DATABASE_URL}}"

# Por service
railway service frontend variables set AUTH_API_URL="http://auth-api.railway.internal"
railway service auth-api variables set PORT="5001"
# ... etc
```

---

### Semana 2-3: Primeiro Deploy (AUTH + FRONTEND)

#### Extrair código AUTH
```bash
# Copiar funções de autenticação para auth-api/
cp auth_functions.py auth-api/
cp auth_middleware.py auth-api/

# Criar app.py minimalista
cat > auth-api/app.py << 'EOF'
from flask import Flask, jsonify, request, session
from auth_functions import validar_usuario, criar_sessao
from database_postgresql import DatabaseManager
import os

app = Flask(__name__)
app.secret_key = os.getenv('JWT_SECRET')
db = DatabaseManager()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    usuario = validar_usuario(data['username'], data['password'])
    if usuario:
        token = criar_sessao(usuario['id'])
        return jsonify({'success': True, 'token': token})
    return jsonify({'error': 'Credenciais inválidas'}), 401

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001)))
EOF
```

#### Deploy AUTH-API
```bash
cd auth-api/
railway up
railway logs  # Verificar se subiu corretamente
```

#### Testar
```bash
curl -X POST https://auth-api-production.up.railway.app/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "senha123"}'
```

---

## 📚 REFERÊNCIAS E RECURSOS

### Documentação Railway
- [Railway Docs](https://docs.railway.app/)
- [Private Networking](https://docs.railway.app/guides/private-networking)
- [Service Variables](https://docs.railway.app/guides/variables)
- [Monorepo Support](https://docs.railway.app/guides/monorepo)

### Padrões de Microserviços
- [Microsoft - Microservices Architecture](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices)
- [Martin Fowler - Microservices](https://martinfowler.com/articles/microservices.html)
- [SAGA Pattern](https://microservices.io/patterns/data/saga.html)
- [API Gateway Pattern](https://microservices.io/patterns/apigateway.html)

### Ferramentas
- **Docker:** Containerização
- **Gunicorn:** WSGI server Python
- **Redis:** Cache e session storage
- **Sentry:** Error tracking
- **Pytest:** Testes unitários
- **Locust:** Load testing

---

## 🎯 DECISÃO FINAL: VALE A PENA?

### ✅ **SIM, se:**
1. Sistema tem > 10 usuários ativos simultâneos
2. Deploys frequentes (> 2/semana)
3. Múltiplos desenvolvedores trabalhando
4. Necessidade de alta disponibilidade (99.5%+)
5. Planejamento de escalar para 100+ usuários

### ❌ **NÃO, se:**
1. Sistema tem < 5 usuários
2. Deploys raros (< 1/mês)
3. 1 desenvolvedor apenas
4. Budget apertado (< $20/mês)
5. Não há necessidade de alta disponibilidade

### 🤔 **DECISÃO PARA SEU CASO:**
Com base no que você descreveu:
- ✅ Usuários reclamando de desconexões (problema real)
- ✅ Sistema maduro com múltiplos módulos
- ✅ Necessidade de manutenção frequente
- ✅ Planejamento de crescimento

**RECOMENDAÇÃO: MIGRAR GRADUALMENTE** 🚀

Comece pela **Fase 1-3** (AUTH + FRONTEND) nas próximas 2-3 semanas.  
Avalie os resultados e depois decida sobre migrar os demais módulos.

---

## 📞 PRÓXIMOS PASSOS

1. **Revisar esta documentação** com a equipe
2. **Definir timeline** de migração
3. **Começar Fase 1** (Setup de estrutura)
4. **Deploy paralelo** de AUTH-API (sem afetar produção)
5. **Monitorar métricas** e ajustar conforme necessário

---

**Documentação criada por:** GitHub Copilot (Claude Sonnet 4.5)  
**Data:** 13/02/2026  
**Versão:** 1.0  
**Status:** Planejamento aprovado, aguardando implementação

---

## 💬 DÚVIDAS FREQUENTES

**P: E se um service cair, o sistema todo para?**  
R: Não! Cada service é independente. Se RELATORIOS-API cair, o usuário ainda pode criar lançamentos, ver dashboard, etc. Só a aba "Relatórios" ficará indisponível.

**P: Como fazer backup se são vários services?**  
R: O banco PostgreSQL continua único e compartilhado. 1 backup = todos os dados. Os services são stateless (sem dados persistidos neles).

**P: Dá para fazer aos poucos?**  
R: SIM! A estratégia de migração gradual (Fases 1-6) foi desenhada exatamente para isso. Você pode parar em qualquer fase se quiser.

**P: E se Railway ficar caro demais?**  
R: A arquitetura é portável. Você pode migrar para AWS, Google Cloud, Azure ou até VPS próprio com Docker Compose. O investimento em modularização não é perdido!

**P: Preciso reescrever o frontend?**  
R: Não! Só precisa trocar as URLs das APIs de `/api/...` para `${API_URL}/api/...`. Mudança de ~50 linhas no app.js.

---

**FIM DA DOCUMENTAÇÃO** 🎉
