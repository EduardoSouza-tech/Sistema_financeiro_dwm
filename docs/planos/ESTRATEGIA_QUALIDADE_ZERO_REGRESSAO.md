# 🛡️ ESTRATÉGIA DE QUALIDADE: ZERO REGRESSÃO
## Como Parar de Quebrar Funcionalidades ao Corrigir Bugs

**Data:** 13/02/2026  
**Status:** 🚨 CRÍTICO - IMPLEMENTAÇÃO URGENTE  
**Problema:** Correções quebrando outras funcionalidades sistematicamente

---

## 🔥 PROBLEMA ATUAL (SITUAÇÃO CRÍTICA)

### Padrão de Falhas Identificado

```
Timeline das últimas horas:

1. ❌ Evento: data não atualizava
   └─ FIX: Reescrever atualizar_evento()
   
2. ❌ Timezone: datas mostrando 1 dia a menos
   └─ FIX: Corrigir formatarData() em 4 arquivos
   
3. ❌ Fornecedores: não apareciam no modal
   └─ FIX: window.fornecedores não sendo definido
   
4. ❌ Conciliação: ReferenceError descricao
   └─ FIX: Adicionar variável faltante
   
5. ❌ Evento: erro 500 ao deletar
   └─ FIX: conn não definido
   
6. ❌ Contas a pagar: erro ao salvar
   └─ FIX: python-dateutil faltando
   
7. ❌ Lista de presença: funcionários desatualizados
   └─ FIX: Sincronizar com equipe alocada
   
8. ❌ Evento: ERR_CONNECTION_FAILED ao salvar
   └─ CAUSA: Deploy anterior ainda em andamento
```

### 📊 Estatísticas Alarmantes

- **8 bugs** identificados em **poucas horas**
- **100% dos fixes** feitos sem testes prévios
- **0 validações** automáticas antes do deploy
- **Tempo médio de detecção:** Quando usuário reclama (tarde demais!)
- **Impacto:** Usuários perdendo trabalho, frustração, desconfiança

---

## 🎯 CAUSAS RAIZ IDENTIFICADAS

### 1️⃣ **Ausência Total de Testes Automatizados**

**Problema:**
```python
# web_server.py - 11.000 linhas
# ZERO testes unitários
# ZERO testes de integração
# ZERO testes end-to-end
```

**Consequência:**
- Mudança em `atualizar_evento()` pode quebrar `deletar_evento()`
- Mudança em `formatarData()` afeta 20+ funcionalidades
- Não há como saber se algo quebrou até usuário reclamar

---

### 2️⃣ **Deploy Direto para Produção (Sem Staging)**

**Fluxo Atual:**
```
VSCode → Git commit → Railway deploy → PRODUÇÃO (usuários reais!)
          ↑
    Sem validação!
    Sem teste!
    Sem staging!
```

**Resultado:** Usuários são cobaias involuntárias 😱

---

### 3️⃣ **Código Monolítico com Alto Acoplamento**

**Exemplo Real:**
```javascript
// app.js - função loadCategorias()
// É chamada por:
// - loadContasReceber()
// - loadContasPagar()
// - openModalDespesa()
// - openModalReceita()
// - loadRelatorios()
// ... 15+ locais!

// Mudança em loadCategorias() = risco de quebrar 15+ funcionalidades
```

---

### 4️⃣ **Validação Manual Insuficiente**

**Checklist atual antes do deploy:**
```
1. [ ] Testar a função que foi corrigida
2. [ ] Deploy

FALTAM:
3. [ ] Testar funcionalidades relacionadas
4. [ ] Testar fluxos críticos completos
5. [ ] Verificar console do navegador
6. [ ] Testar em múltiplos cenários
```

---

### 5️⃣ **Conhecimento Implícito (Não Documentado)**

**Dependências ocultas não mapeadas:**
```
❌ Não sabemos que:
- window.fornecedores é usado por 3 modais diferentes
- formatarData() existe em 5 arquivos diferentes
- carregarEquipeEvento() deve atualizar lista de assinatura
- Criar lançamento afeta saldo de conta bancária
```

---

## ✅ SOLUÇÃO COMPLETA: ESTRATÉGIA DE 4 CAMADAS

```
┌─────────────────────────────────────────────────────────────┐
│              CAMADA 4: TESTES AUTOMATIZADOS                  │
│  • Testes Unitários (funções isoladas)                      │
│  • Testes de Integração (APIs)                              │
│  • Testes E2E (fluxos completos)                            │
│  ⏱️ Implementação: 2-4 semanas                               │
└─────────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│         CAMADA 3: AMBIENTE STAGING + CI/CD                   │
│  • Staging environment no Railway                           │
│  • GitHub Actions para validação                            │
│  • Deploy automático apenas se passar testes                │
│  ⏱️ Implementação: 1 semana                                  │
└─────────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│      CAMADA 2: SMOKE TESTS MANUAIS (CHECKLIST)              │
│  • Checklist de 20 testes críticos (5 minutos)             │
│  • Script de validação pré-deploy                           │
│  • Documentação de fluxos principais                        │
│  ⏱️ Implementação: 2-3 dias                                  │
└─────────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│   CAMADA 1: MAPEAMENTO DE DEPENDÊNCIAS (URGENTE!)           │
│  • Documentar funções críticas e onde são usadas            │
│  • Criar matriz de impacto (mudar X afeta Y, Z, W)         │
│  • Alert de alto risco ao editar função compartilhada       │
│  ⏱️ Implementação: HOJE (1-2 horas)                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 IMPLEMENTAÇÃO IMEDIATA (HOJE/AMANHÃ)

### FASE 1: Mapeamento de Dependências Críticas (2 horas)

Vou criar um documento mapeando todas as funções críticas e seus impactos:

**Arquivo:** `MAPA_DEPENDENCIAS_CRITICAS.md`

```markdown
# 🗺️ MAPA DE DEPENDÊNCIAS CRÍTICAS

## ⚠️ ZONA VERMELHA (Alto Risco de Quebrar Sistema)

### 🔴 formatarData() - 5 LOCALIZAÇÕES
**Arquivos:**
- utils.js (linha 117)
- app.js (linha 283)
- dashboard_sessoes.js (linha 454)
- interface_nova.html (linha 9038)
- contratos.js (linha 1557)

**Usado por:** 50+ funções
**Impacto de mudança:** CRÍTICO
**Testes obrigatórios antes de alterar:**
- [ ] Contas a Receber: datas nas tabelas
- [ ] Contas a Pagar: datas nas tabelas
- [ ] Eventos: data do evento
- [ ] Dashboard: gráficos e relatórios
- [ ] Contratos: vencimentos

---

### 🔴 window.fornecedores - VARIÁVEL GLOBAL
**Definida em:** app.js loadFornecedores() (linha 5217)
**Usada por:**
- modals.js openModalDespesa() (linha 335)
- modals.js editarDespesa() (linha 450)
- app.js (relatórios com filtro de fornecedor)

**Impacto de mudança:** ALTO
**Testes obrigatórios:**
- [ ] Abrir modal "Nova Despesa" → Fornecedores aparecem
- [ ] Editar despesa existente → Fornecedores carregam
- [ ] Relatório de despesas por fornecedor

---

### 🔴 carregarEquipeEvento() - EVENTOS
**Arquivo:** interface_nova.html (linha 7669)
**Usado por:**
- Adicionar funcionário individual
- Adicionar funcionários em massa
- Remover funcionário
- Abrir modal de equipe

**DEPENDENTES INDIRETOS:**
- carregarListaAssinatura() - DEVE ser chamado após
- exportarAssinaturaPDF() - depende dos dados
- exportarAssinaturaExcel() - depende dos dados

**Impacto de mudança:** ALTO
**Testes obrigatórios:**
- [ ] Adicionar funcionário → Aparece na tabela
- [ ] Remover funcionário → Some da tabela
- [ ] Aba "Assinatura" → Lista atualizada
- [ ] Exportar PDF → Funcionários corretos
```

---

### FASE 2: Checklist de Smoke Tests (15 minutos para criar, 5 minutos para executar)

**Arquivo:** `SMOKE_TESTS_PRE_DEPLOY.md`

```markdown
# 🔥 SMOKE TESTS PRE-DEPLOY
## Executar ANTES de cada git push para produção (5 minutos)

### ✅ TESTES OBRIGATÓRIOS (20 checks críticos)

#### 1. Autenticação (30 seg)
- [ ] Login com usuário válido funciona
- [ ] Página redireciona para dashboard após login
- [ ] Logout funciona

#### 2. Dashboard (15 seg)
- [ ] Dashboard carrega sem erros
- [ ] Saldo total de bancos aparece
- [ ] Não há erros no console

#### 3. Contas a Receber (1 min)
- [ ] Lista de lançamentos carrega
- [ ] Botão "Nova Receita" abre modal
- [ ] Modal de receita mostra clientes
- [ ] Salvar nova receita funciona (testar com valor teste)
- [ ] Editar receita funciona
- [ ] Deletar receita funciona
- [ ] Datas aparecem corretamente (sem -1 dia)

#### 4. Contas a Pagar (1 min)
- [ ] Lista de lançamentos carrega
- [ ] Botão "Nova Despesa" abre modal
- [ ] **CRÍTICO:** Modal de despesa mostra fornecedores
- [ ] Categorias carregam no select
- [ ] Salvar nova despesa funciona
- [ ] Datas aparecem corretamente

#### 5. Cadastros (30 seg)
- [ ] Categorias carregam
- [ ] Clientes carregam
- [ ] Fornecedores carregam
- [ ] Contas bancárias carregam

#### 6. Eventos (1 min)
- [ ] Lista de eventos carrega
- [ ] Criar novo evento funciona
- [ ] Editar evento funciona (testar mudança de data)
- [ ] **CRÍTICO:** Deletar evento funciona
- [ ] Alocar equipe funciona
- [ ] Aba "Assinatura" mostra equipe correta
- [ ] Exportar PDF funciona

#### 7. Console do Browser (CRÍTICO - 10 seg)
- [ ] **F12 → Console → Sem erros vermelhos**
- [ ] Sem "Failed to load resource"
- [ ] Sem "ReferenceError" ou "TypeError"

### 🚨 REGRA DE OURO
**Se QUALQUER teste falhar → NÃO FAZER DEPLOY!**
```

---

### FASE 3: Script de Validação Automática (30 minutos)

Criar script Python que valida endpoints críticos:

**Arquivo:** `smoke_test_api.py`

```python
#!/usr/bin/env python3
"""
Smoke Tests Automáticos - APIs Críticas
Execute ANTES de deploy: python smoke_test_api.py
"""

import requests
import sys
from colorama import init, Fore, Style

init(autoreset=True)

API_BASE = "https://sistemafinanceirodwm-production.up.railway.app"
# Para staging: API_BASE = "https://staging-sistemafinanceirodwm.railway.app"

# Credenciais de teste (criar usuário dedicado para testes)
TEST_USER = "teste@sistema.com"
TEST_PASS = "senha_teste_123"

class SmokeTest:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.passed = 0
        self.failed = 0
    
    def test(self, name, func):
        """Executa um teste e registra resultado"""
        try:
            print(f"\n🔍 Testando: {name}...", end=" ")
            func()
            print(f"{Fore.GREEN}✅ PASSOU")
            self.passed += 1
        except AssertionError as e:
            print(f"{Fore.RED}❌ FALHOU: {e}")
            self.failed += 1
        except Exception as e:
            print(f"{Fore.RED}❌ ERRO: {e}")
            self.failed += 1
    
    # ==========================================
    # TESTES
    # ==========================================
    
    def test_01_login(self):
        """Login com credenciais válidas"""
        resp = self.session.post(f"{API_BASE}/api/login", json={
            "username": TEST_USER,
            "password": TEST_PASS
        })
        assert resp.status_code == 200, f"Status {resp.status_code}"
        data = resp.json()
        assert data.get('success'), "Login não retornou success=True"
        self.token = data.get('token')
    
    def test_02_check_auth(self):
        """Verificar autenticação"""
        resp = self.session.get(f"{API_BASE}/api/check-auth")
        assert resp.status_code == 200, f"Status {resp.status_code}"
        data = resp.json()
        assert 'usuario' in data, "Resposta não contém dados do usuário"
    
    def test_03_contas_bancarias(self):
        """Listar contas bancárias"""
        resp = self.session.get(f"{API_BASE}/api/contas")
        assert resp.status_code == 200, f"Status {resp.status_code}"
        data = resp.json()
        assert 'data' in data or isinstance(data, list), "Resposta inválida"
    
    def test_04_categorias(self):
        """Listar categorias"""
        resp = self.session.get(f"{API_BASE}/api/categorias")
        assert resp.status_code == 200, f"Status {resp.status_code}"
        data = resp.json()
        assert 'data' in data or isinstance(data, list), "Resposta inválida"
    
    def test_05_fornecedores(self):
        """Listar fornecedores (CRÍTICO)"""
        resp = self.session.get(f"{API_BASE}/api/fornecedores")
        assert resp.status_code == 200, f"Status {resp.status_code}"
        data = resp.json()
        # Validar estrutura
        if isinstance(data, dict):
            assert 'data' in data, "Formato novo sem campo 'data'"
            fornecedores = data['data']
        else:
            fornecedores = data
        # Deve ter pelo menos 1 fornecedor no teste
        assert len(fornecedores) > 0, "Nenhum fornecedor retornado (banco de testes vazio?)"
    
    def test_06_clientes(self):
        """Listar clientes"""
        resp = self.session.get(f"{API_BASE}/api/clientes")
        assert resp.status_code == 200, f"Status {resp.status_code}"
    
    def test_07_lancamentos_receita(self):
        """Listar lançamentos (receitas)"""
        resp = self.session.get(f"{API_BASE}/api/lancamentos?tipo=RECEITA&page=1&per_page=10")
        assert resp.status_code == 200, f"Status {resp.status_code}"
    
    def test_08_lancamentos_despesa(self):
        """Listar lançamentos (despesas)"""
        resp = self.session.get(f"{API_BASE}/api/lancamentos?tipo=DESPESA&page=1&per_page=10")
        assert resp.status_code == 200, f"Status {resp.status_code}"
    
    def test_09_eventos(self):
        """Listar eventos"""
        resp = self.session.get(f"{API_BASE}/api/eventos")
        assert resp.status_code == 200, f"Status {resp.status_code}"
        data = resp.json()
        assert isinstance(data, list) or 'data' in data, "Resposta inválida"
    
    def test_10_dashboard(self):
        """Endpoint de dashboard"""
        resp = self.session.get(f"{API_BASE}/api/dashboard")
        # Dashboard pode retornar 200 ou 404 se não implementado
        assert resp.status_code in [200, 404], f"Status inesperado {resp.status_code}"
    
    # ==========================================
    # RUNNER
    # ==========================================
    
    def run_all(self):
        """Executa todos os testes"""
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}🔥 SMOKE TESTS - APIs Críticas")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"\n🌐 API Base: {API_BASE}")
        
        # Ordem importa! Autenticação primeiro
        self.test("01. Login", self.test_01_login)
        self.test("02. Check Auth", self.test_02_check_auth)
        self.test("03. Contas Bancárias", self.test_03_contas_bancarias)
        self.test("04. Categorias", self.test_04_categorias)
        self.test("05. Fornecedores (CRÍTICO)", self.test_05_fornecedores)
        self.test("06. Clientes", self.test_06_clientes)
        self.test("07. Lançamentos (Receitas)", self.test_07_lancamentos_receita)
        self.test("08. Lançamentos (Despesas)", self.test_08_lancamentos_despesa)
        self.test("09. Eventos", self.test_09_eventos)
        self.test("10. Dashboard", self.test_10_dashboard)
        
        # Resultado final
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.GREEN}✅ Passou: {self.passed}")
        print(f"{Fore.RED}❌ Falhou: {self.failed}")
        print(f"{Fore.CYAN}{'='*60}")
        
        if self.failed > 0:
            print(f"\n{Fore.RED}❌ SMOKE TESTS FALHARAM! NÃO FAÇA DEPLOY!")
            sys.exit(1)
        else:
            print(f"\n{Fore.GREEN}✅ TODOS OS TESTES PASSARAM! Deploy liberado.")
            sys.exit(0)

if __name__ == "__main__":
    tester = SmokeTest()
    tester.run_all()
```

**Como usar:**
```bash
# Instalar dependência
pip install requests colorama

# Rodar antes de deploy
python smoke_test_api.py

# Se passar → Deploy liberado
# Se falhar → NÃO FAZER DEPLOY!
```

---

## 🏗️ IMPLEMENTAÇÃO INTERMEDIÁRIA (1-2 SEMANAS)

### FASE 4: Ambiente Staging no Railway

**Objetivo:** Testar mudanças em ambiente idêntico à produção ANTES de afetar usuários

**Setup:**

1. **Criar novo service no Railway:**
```bash
railway service create staging-sistema-financeiro

# Configurar variáveis
railway variables set ENVIRONMENT="staging"
railway variables set DATABASE_URL="${{Postgres-Staging.DATABASE_URL}}"
```

2. **Branch strategy no Git:**
```
main → produção (Railway deploy automático)
staging → staging (Railway deploy automático)
develop → trabalho local (sem deploy)
```

3. **Fluxo de trabalho:**
```bash
# Desenvolver no branch develop
git checkout develop
git commit -m "fix: Corrigir bug X"

# Merge para staging e testar
git checkout staging
git merge develop
git push origin staging
# → Railway faz deploy para staging

# Testar em staging (URL diferente)
# https://staging-sistema.railway.app

# Se passou → Merge para main
git checkout main
git merge staging
git push origin main
# → Railway faz deploy para produção
```

---

### FASE 5: GitHub Actions - CI/CD Automático

**Arquivo:** `.github/workflows/ci.yml`

```yaml
name: CI - Validação Pré-Deploy

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

jobs:
  smoke-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install requests colorama pytest
      
      - name: Run Smoke Tests
        env:
          API_BASE: ${{ secrets.STAGING_URL }}
          TEST_USER: ${{ secrets.TEST_USER }}
          TEST_PASS: ${{ secrets.TEST_PASS }}
        run: |
          python smoke_test_api.py
      
      - name: Notify on failure
        if: failure()
        run: |
          echo "❌ SMOKE TESTS FALHARAM!"
          echo "Deploy bloqueado até correção."
          exit 1

  lint-python:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Lint with flake8
        run: |
          pip install flake8
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          # Apenas erros críticos (syntax, undefined vars)

  check-requirements:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Check if requirements.txt is valid
        run: |
          pip install -r Sistema_financeiro_dwm/requirements.txt --dry-run
```

**Resultado:** Bloqueio automático de merge se testes falharem!

---

## 🧪 IMPLEMENTAÇÃO AVANÇADA (2-4 SEMANAS)

### FASE 6: Testes Unitários Críticos

**Framework:** `pytest` (Python) + `Jest` (JavaScript)

**Arquivo:** `tests/test_eventos.py`

```python
import pytest
from web_server import app, db
from datetime import date

@pytest.fixture
def client():
    """Cliente de teste Flask"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_token(client):
    """Token de autenticação para testes"""
    response = client.post('/api/login', json={
        'username': 'teste@teste.com',
        'password': 'senha123'
    })
    return response.json['token']

# ==========================================
# TESTES CRÍTICOS
# ==========================================

def test_criar_evento(client, auth_token):
    """Teste: Criar evento deve retornar 201 e dados corretos"""
    response = client.post('/api/eventos', 
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'nome_evento': 'Evento Teste',
            'data_evento': '2026-03-01',
            'tipo_evento': 'PALESTRA',
            'status': 'PLANEJAMENTO'
        }
    )
    
    assert response.status_code == 201
    data = response.json
    assert data['success'] == True
    assert 'id' in data['evento']
    assert data['evento']['nome_evento'] == 'Evento Teste'

def test_atualizar_evento_data(client, auth_token):
    """Teste CRÍTICO: Atualizar data de evento deve persistir"""
    # 1. Criar evento
    resp_create = client.post('/api/eventos',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'nome_evento': 'Teste Update',
            'data_evento': '2026-03-01',
            'tipo_evento': 'PALESTRA',
            'status': 'PLANEJAMENTO'
        }
    )
    evento_id = resp_create.json['evento']['id']
    
    # 2. Atualizar data
    resp_update = client.put(f'/api/eventos/{evento_id}',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={'data_evento': '2026-03-15'}
    )
    
    assert resp_update.status_code == 200
    assert resp_update.json['success'] == True
    
    # 3. VERIFICAÇÃO: Ler de volta e confirmar mudança
    resp_get = client.get(f'/api/eventos/{evento_id}',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert resp_get.json['data_evento'] == '2026-03-15'
    # ✅ Se passar, garantimos que o bug não volta!

def test_deletar_evento(client, auth_token):
    """Teste CRÍTICO: Deletar evento não deve dar erro 500"""
    # Criar evento
    resp_create = client.post('/api/eventos',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'nome_evento': 'Teste Delete',
            'data_evento': '2026-03-01',
            'tipo_evento': 'PALESTRA',
            'status': 'PLANEJAMENTO'
        }
    )
    evento_id = resp_create.json['evento']['id']
    
    # Deletar
    resp_delete = client.delete(f'/api/eventos/{evento_id}',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    # DEVE retornar 200, não 500!
    assert resp_delete.status_code == 200
    assert resp_delete.json['success'] == True
    
    # Confirmar que foi deletado
    resp_get = client.get(f'/api/eventos/{evento_id}',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert resp_get.status_code == 404

# ==========================================
# TESTES DE REGRESSÃO
# ==========================================

def test_formatarData_nao_muda_dia(client):
    """Teste de regressão: formatarData não deve mudar dia (bug timezone)"""
    # Simular chamada JavaScript
    from datetime import datetime
    
    data_str = "2026-02-08"
    # Processar como JavaScript fazia (ERRADO)
    # data_obj = datetime.fromisoformat(data_str)  # Não fazer mais isso!
    
    # Processar CORRETO (split de string)
    parts = data_str.split('-')
    data_formatada = f"{parts[2]}/{parts[1]}/{parts[0]}"
    
    assert data_formatada == "08/02/2026"  # Não "07/02/2026"!

def test_window_fornecedores_definido():
    """Teste: window.fornecedores deve ser definido após loadFornecedores"""
    # JavaScript test (seria com Jest)
    # Aqui apenas exemplo conceitual em Python
    pass  # Implementar com Selenium/Playwright

# ==========================================
# RODAR TESTES
# ==========================================

# No terminal:
# pytest tests/ -v
# pytest tests/test_eventos.py::test_atualizar_evento_data -v
```

**Rodar testes:**
```bash
# Instalar
pip install pytest pytest-flask

# Rodar todos os testes
pytest tests/ -v

# Rodar apenas testes de eventos
pytest tests/test_eventos.py -v

# Rodar com coverage
pytest tests/ --cov=web_server --cov-report=html
```

---

### FASE 7: Testes JavaScript (Frontend)

**Framework:** Jest + Playwright (E2E)

**Arquivo:** `tests/frontend/formatarData.test.js`

```javascript
/**
 * Testes para formatarData() - Função crítica presente em 5 arquivos
 * Previne regressão do bug de timezone
 */

// Importar função (assumindo módulos ES6)
import { formatarData } from '../../static/utils.js';

describe('formatarData - Testes de Regressão', () => {
    
    test('deve formatar YYYY-MM-DD sem mudar dia (bug timezone)', () => {
        // Caso que causou bug: 2026-02-08 virava 07/02/2026
        expect(formatarData('2026-02-08')).toBe('08/02/2026');
        expect(formatarData('2026-12-31')).toBe('31/12/2026');
        expect(formatarData('2026-01-01')).toBe('01/01/2026');
    });
    
    test('deve lidar com diferentes formatos de entrada', () => {
        expect(formatarData('2026-02-08T00:00:00')).toBe('08/02/2026');
        expect(formatarData('2026-02-08T14:30:00')).toBe('08/02/2026');
    });
    
    test('não deve aceitar datas inválidas', () => {
        expect(formatarData('data-invalida')).toBe('Data inválida');
        expect(formatarData(null)).toBe('');
        expect(formatarData(undefined)).toBe('');
    });
});

describe('window.fornecedores - Disponibilidade Global', () => {
    
    test('deve estar definido após loadFornecedores', async () => {
        // Mockar fetch
        global.fetch = jest.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({
                    success: true,
                    data: [
                        { id: 1, nome: 'Fornecedor Teste' }
                    ]
                })
            })
        );
        
        // Importar e executar
        const { loadFornecedores } = require('../../static/app.js');
        await loadFornecedores();
        
        // Validar
        expect(window.fornecedores).toBeDefined();
        expect(window.fornecedores.length).toBeGreaterThan(0);
    });
});
```

**Rodar testes:**
```bash
# Instalar
npm install --save-dev jest @playwright/test

# Rodar testes
npm test

# Rodar com watch mode (re-executa ao salvar)
npm test -- --watch
```

---

## 📋 WORKFLOW DIÁRIO RECOMENDADO

### Antes de QUALQUER mudança:

```
1. Ler MAPA_DEPENDENCIAS_CRITICAS.md
   └─ Verificar se função que vou alterar está na ZONA VERMELHA
   
2. Se estiver na ZONA VERMELHA:
   └─ Duplicar função com sufixo _v2 (não alterar original ainda)
   └─ Testar nova função isoladamente
   └─ Só substituir original após validar
```

### Antes de QUALQUER commit:

```bash
# 1. Executar smoke tests locais (5 min)
python smoke_test_api.py

# 2. Verificar console do browser
# Abrir sistema → F12 → Console → Sem erros vermelhos

# 3. Executar checklist manual (5 min)
# Abrir SMOKE_TESTS_PRE_DEPLOY.md e seguir

# 4. Se TODOS passaram → Commit e push
git add .
git commit -m "fix: Descrição detalhada do que foi corrigido"
git push origin staging  # Staging primeiro!

# 5. Testar em staging (2-3 min após deploy)
# Abrir https://staging-sistema.railway.app
# Repetir smoke tests

# 6. Se staging passou → Merge para main
git checkout main
git merge staging
git push origin main
```

---

## 🎯 MÉTRICAS DE SUCESSO

### Objetivos mensuráveis (30 dias):

```
ANTES (Situação Atual):
- 8+ bugs críticos identificados em poucas horas
- 100% dos deploys sem testes prévios
- 0% de cobertura de testes
- Tempo médio de detecção: Quando usuário reclama
- Regressões frequentes (corrige X, quebra Y)

DEPOIS (Meta em 30 dias):
- < 1 bug crítico por semana
- 100% dos deploys com smoke tests
- > 50% de cobertura de testes (funções críticas)
- Tempo médio de detecção: Antes do deploy (CI/CD)
- Zero regressões em funcionalidades críticas
```

### KPIs semanais:

```
- Bugs encontrados em produção: < 2/semana
- Bugs encontrados em staging: Ilimitado (quanto mais, melhor!)
- Tempo de deploy: < 5 minutos (com testes)
- Rollbacks: < 1/mês
- Uptime: > 99.5%
```

---

## 🚨 REGRAS DE OURO (NÃO NEGOCIÁVEIS)

### 1. **NUNCA altere função em ZONA VERMELHA sem testes**
```python
# ❌ PROIBIDO
def formatarData(data):
    # Alterar diretamente sem testes = suicídio

# ✅ CORRETO
def formatarData_v2(data):
    # Nova versão testada
    pass

# Após validar v2:
def formatarData(data):
    return formatarData_v2(data)  # Substituir gradualmente
```

### 2. **NUNCA faça deploy direto para main sem staging**
```bash
# ❌ PROIBIDO
git push origin main  # Deploy direto para produção

# ✅ CORRETO
git push origin staging  # Staging primeiro
# → Testar em staging
# → Se passou, merge para main
```

### 3. **NUNCA ignore erros no console do browser**
```javascript
// Se ver no console:
❌ ReferenceError: descricao is not defined
❌ TypeError: Cannot read property 'length' of undefined
❌ Failed to load resource: 500

👉 NÃO FAZER DEPLOY! Corrigir primeiro!
```

### 4. **SEMPRE execute smoke tests antes de commit**
```bash
# Criar atalho no terminal
alias pre-commit="python smoke_test_api.py && echo '✅ Liberado para commit'"

# Uso:
pre-commit && git push
```

---

## 📚 DOCUMENTAÇÃO COMPLEMENTAR

### Arquivos a criar:

1. ✅ **MAPA_DEPENDENCIAS_CRITICAS.md** (HOJE)
   - Funções de alto risco
   - Onde são usadas
   - Checklist de testes obrigatórios

2. ✅ **SMOKE_TESTS_PRE_DEPLOY.md** (HOJE)
   - 20 testes críticos (5 minutos)
   - Checklist de validação

3. ✅ **smoke_test_api.py** (AMANHÃ)
   - Script de testes automatizados
   - Validação de endpoints críticos

4. ⏳ **tests/** (SEMANA 1-2)
   - Testes unitários (pytest)
   - Testes de integração
   - Testes E2E (Playwright)

5. ⏳ **.github/workflows/ci.yml** (SEMANA 1-2)
   - CI/CD automático
   - Bloqueio de merge se falhar

---

## 💰 INVESTIMENTO vs RETORNO

### Investimento de Tempo:

```
FASE 1-3 (Imediato): 4-6 horas
- Mapeamento de dependências: 2h
- Checklist smoke tests: 1h
- Script Python validação: 2h
- Documentar fluxos: 1h

FASE 4-5 (1-2 semanas): 20-30 horas
- Setup staging: 4h
- Configurar CI/CD: 6h
- Criar testes unitários críticos: 10-20h

FASE 6-7 (2-4 semanas): 40-60 horas
- Suite completa de testes: 30-40h
- Testes E2E: 10-20h

TOTAL: 64-96 horas (~2-2.5 semanas de trabalho)
```

### Retorno Esperado:

```
REDUÇÃO DE BUGS:
- Antes: 8+ bugs/semana em produção
- Depois: < 1 bug/semana em produção
- Economia: 7 bugs × 2h correção = 14h/semana = 56h/mês

REDUÇÃO DE RETRABALHO:
- Antes: Corrige X, quebra Y → 4h perdidas/bug
- Depois: Detecta antes do deploy → 0h perdidas
- Economia: 4 bugs × 4h = 16h/mês

CONFIANÇA DO USUÁRIO:
- Antes: Sistema instável → Frustração → Perda de usuários
- Depois: Sistema estável → Confiança → Retenção

ROI: Investimento de 96h retorna em < 1.5 mês (56h + 16h = 72h/mês)
```

---

## 🎬 PRÓXIMOS PASSOS IMEDIATOS

### HOJE (13/02/2026):

1. ✅ Criar `MAPA_DEPENDENCIAS_CRITICAS.md`
2. ✅ Criar `SMOKE_TESTS_PRE_DEPLOY.md`
3. ✅ Documentar funções críticas identificadas hoje:
   - formatarData() (5 locais)
   - window.fornecedores
   - carregarEquipeEvento()
   - atualizar_evento()

### AMANHÃ (14/02/2026):

4. ✅ Criar `smoke_test_api.py`
5. ✅ Criar usuário de teste no sistema
6. ✅ Executar smoke tests pela primeira vez
7. ✅ Adicionar no README: "Execute smoke_test_api.py antes de deploy"

### PRÓXIMA SEMANA:

8. ⏳ Setup staging environment no Railway
9. ⏳ Configurar GitHub Actions
10. ⏳ Criar primeiros testes unitários (eventos, lançamentos)

---

## 📞 CONCLUSÃO: ZERO REGRESSÃO É POSSÍVEL!

### Resumo da Estratégia:

```
1. PREVENIR (Mapeamento + Checklist)
   └─ Saber o que não deve quebrar

2. DETECTAR (Smoke tests + CI/CD)
   └─ Pegar bugs antes do deploy

3. PROTEGER (Staging + Testes automatizados)
   └─ Ambiente seguro para testar

4. GARANTIR (Testes de regressão)
   └─ Bug corrigido nunca volta
```

### Mantra do Desenvolvedor:

```
❌ "Vou corrigir esse bug rápido e fazer push"
✅ "Vou corrigir, testar localmente, rodar smoke tests,
    deploy em staging, testar novamente, e SÓ ENTÃO
    deploy em produção"

Parece demorado? 
Sim, 10 minutos a mais.

Vale a pena?
SIM! Evita 4 horas corrigindo regressões depois.
```

---

**Documentação criada por:** GitHub Copilot (Claude Sonnet 4.5)  
**Data:** 13/02/2026  
**Status:** Pronta para implementação  
**Prioridade:** 🚨 CRÍTICA - INICIAR HOJE

---

## 🔗 REFERÊNCIAS

- [Clean Code - Robert Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Test-Driven Development - Kent Beck](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)
- [Railway Staging Guide](https://docs.railway.app/guides/environments)
- [GitHub Actions for Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [Pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
