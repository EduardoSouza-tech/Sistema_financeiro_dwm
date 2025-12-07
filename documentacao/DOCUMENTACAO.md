# 📊 Sistema Financeiro DWM - Documentação Completa

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Tecnologias Utilizadas](#tecnologias-utilizadas)
4. [Estrutura de Diretórios](#estrutura-de-diretórios)
5. [Funcionalidades](#funcionalidades)
6. [Modelos de Dados](#modelos-de-dados)
7. [API REST](#api-rest)
8. [Interface Web](#interface-web)
9. [Banco de Dados](#banco-de-dados)
10. [Deploy e Produção](#deploy-e-produção)
11. [Configuração Local](#configuração-local)
12. [Integrações Externas](#integrações-externas)
13. [Manutenção e Troubleshooting](#manutenção-e-troubleshooting)

---

## 🎯 Visão Geral

Sistema completo de gestão financeira desenvolvido para controle de receitas, despesas, contas bancárias, clientes e fornecedores. Oferece dashboards interativos, relatórios analíticos e integração com APIs externas para automação de cadastros.

### Objetivos do Sistema

- **Controle Financeiro**: Gestão completa de receitas, despesas e transferências
- **Multi-contas**: Suporte a múltiplas contas bancárias com saldo real
- **Análise de Inadimplência**: Acompanhamento de contas vencidas e a vencer
- **Relatórios Gerenciais**: Indicadores financeiros, fluxo de caixa e evolução temporal
- **Integração Automática**: Busca automática de dados via CNPJ (BrasilAPI)

### Público-Alvo

- Pequenas e médias empresas
- Profissionais autônomos
- Gestores financeiros
- Contadores e escritórios contábeis

---

## 🏗️ Arquitetura do Sistema

### Modelo Cliente-Servidor

```
┌─────────────────┐
│   Cliente Web   │
│  (Browser)      │
└────────┬────────┘
         │ HTTP/AJAX
         │
┌────────▼────────┐
│  Flask Server   │
│  (web_server.py)│
├─────────────────┤
│  API REST       │
│  /api/*         │
└────────┬────────┘
         │
┌────────▼────────┐
│ DatabaseManager │
│  (database.py)  │
├─────────────────┤
│  SQLite         │
│  PostgreSQL     │
└─────────────────┘
```

### Camadas da Aplicação

1. **Camada de Apresentação**
   - `templates/interface_nova.html` - Interface principal
   - `static/app.js` - Lógica de negócio do cliente
   - `static/modals.js` - Modais de cadastro/edição
   - `static/style.css` - Estilização

2. **Camada de Aplicação**
   - `web_server.py` - API REST Flask
   - `models.py` - Modelos de dados
   - `config.py` - Configurações

3. **Camada de Dados**
   - `database.py` - Gerenciador universal
   - `database_postgresql.py` - Implementação PostgreSQL
   - `database_mysql.py` - Implementação MySQL
   - SQLite para desenvolvimento local

---

## 💻 Tecnologias Utilizadas

### Backend

| Tecnologia | Versão | Finalidade |
|-----------|--------|------------|
| **Python** | 3.11+ | Linguagem principal |
| **Flask** | 3.0.0 | Framework web |
| **Flask-CORS** | 4.0.0 | Cross-Origin Resource Sharing |
| **psycopg2-binary** | 2.9.9 | Driver PostgreSQL |
| **SQLite** | 3.x | Banco de dados local |

### Frontend

| Tecnologia | Versão | Finalidade |
|-----------|--------|------------|
| **JavaScript** | ES6+ | Lógica cliente |
| **Chart.js** | 4.x | Gráficos interativos |
| **CSS3** | - | Estilização responsiva |
| **HTML5** | - | Estrutura da interface |

### Infraestrutura

| Serviço | Finalidade |
|---------|------------|
| **Railway** | Hospedagem e deploy automático |
| **PostgreSQL (Railway)** | Banco de dados produção |
| **GitHub** | Controle de versão |
| **BrasilAPI** | Consulta de CNPJ |

---

## 📁 Estrutura de Diretórios

```
Sistema_financeiro_dwm/
│
├── 📄 web_server.py              # Servidor Flask principal
├── 📄 database.py                # Gerenciador de banco de dados
├── 📄 database_postgresql.py     # Implementação PostgreSQL
├── 📄 models.py                  # Modelos de dados
├── 📄 config.py                  # Configurações do sistema
├── 📄 main.py                    # Ponto de entrada CLI
│
├── 📁 templates/
│   └── interface_nova.html       # Interface web principal (2608 linhas)
│
├── 📁 static/
│   ├── app.js                    # Lógica principal (4618 linhas)
│   ├── modals.js                 # Sistema de modais (1508 linhas)
│   └── style.css                 # Estilos CSS
│
├── 📁 backups/                   # Backups automáticos
├── 📁 .vscode/                   # Configurações VS Code
│
├── 📄 requirements_web.txt       # Dependências Python
├── 📄 Procfile                   # Configuração Railway
├── 📄 runtime.txt                # Versão Python
├── 📄 .railwayignore            # Arquivos ignorados deploy
├── 📄 pyrightconfig.json         # Configuração Pyright
│
└── 📄 sistema_financeiro.db      # Banco SQLite local
```

### Arquivos de Utilitários

```
├── analisar_banco.py             # Análise do banco de dados
├── limpar_banco.py               # Limpeza de dados
├── verificar_instalacao.py       # Verificação de dependências
├── testar_api.py                 # Testes de API
├── migrar_para_railway.py        # Scripts de migração
└── iniciar_web.bat               # Inicializador Windows
```

---

## ⚙️ Funcionalidades

### 1. Dashboard Financeiro

**Localização**: `interface_nova.html` + `app.js` (função `carregarDashboard()`)

- **Evolução Financeira**: Gráfico de linha com receitas, despesas e saldo acumulado
- **Indicadores do Período**: 
  - Total de Receitas
  - Total de Despesas  
  - Saldo do Período
  - Saldo Acumulado
- **Período Configurável**: Seleção de ano e mês
- **Atualização Automática**: Recarrega ao mudar período

**Código-chave**:
```javascript
// app.js - linha 4079
async function carregarDashboard() {
    const ano = document.getElementById('periodo-ano').value;
    const mes = document.getElementById('periodo-mes').value;
    // Carrega dados do período...
}
```

### 2. Contas a Receber

**Localização**: `app.js` (função `carregarContasReceber()`)

- Listagem de receitas pendentes e pagas
- Filtros por cliente, categoria, período
- Ações: Visualizar, Editar, Pagar, Excluir
- Indicador de vencimento (vermelho para vencidas)
- Somatório de valores pendentes/pagos

### 3. Contas a Pagar

**Localização**: `app.js` (função `carregarContasPagar()`)

- Listagem de despesas pendentes e pagas
- Filtros por fornecedor, categoria, período
- Ações: Visualizar, Editar, Pagar, Excluir
- Indicador de vencimento
- Somatório de valores pendentes/pagos

### 4. Inadimplência

**Localização**: `app.js` (função `carregarInadimplencia()`)

- **Cards Resumo**:
  - 0-30 dias vencidos
  - 31-60 dias vencidos
  - 61-90 dias vencidos
  - Mais de 90 dias vencidos
- **Tabela Detalhada**: Cliente, valor, dias vencidos, data vencimento
- **Badge no Menu**: Quantidade total de inadimplentes

**Lógica de Cálculo**:
```javascript
// app.js - linha 4461
function carregarInadimplencia() {
    const hoje = new Date();
    lancamentos.forEach(lanc => {
        const diasVencidos = Math.floor((hoje - dataVenc) / (1000*60*60*24));
        if (diasVencidos <= 30) faixas.ate30++;
        // ...classificação por faixa
    });
}
```

### 5. Fluxo de Caixa

**Localização**: `app.js` (função `carregarFluxoCaixa()`)

- Visão mensal consolidada
- Receitas previstas vs realizadas
- Despesas previstas vs realizadas
- Saldo inicial e final por mês
- Colunas: Mês, Receita Prevista, Receita Realizada, Despesa Prevista, Despesa Realizada, Saldo

**Otimizações**:
- Fontes reduzidas (11-13px) para melhor leitura
- Header com gradiente roxo
- Responsivo

### 6. Cadastros

#### 6.1 Clientes

**Localização**: `modals.js` (função `openModalCliente()`)

**Campos**:
- CNPJ (com busca automática BrasilAPI)
- Nome/Razão Social
- Telefone
- Email
- Endereço completo
- Status (Ativo/Inativo)

**Auto-fill CNPJ**:
```javascript
// modals.js - linha 1365
async function buscarDadosCNPJ() {
    const cnpj = document.getElementById('clienteCnpj').value.replace(/\D/g, '');
    const response = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpj}`);
    const data = await response.json();
    // Preenche campos automaticamente
}
```

#### 6.2 Fornecedores

**Localização**: `modals.js` (função `openModalFornecedor()`)

- Mesma estrutura de Clientes
- Integração BrasilAPI com `buscarDadosCNPJFornecedor()`
- Modal de carregamento animado

#### 6.3 Categorias

**Localização**: `modals.js` (função `openModalCategoria()`)

- Nome da categoria
- Tipo (Receita/Despesa/Transferência)
- Descrição
- Subcategorias dinâmicas
- Cor e ícone personalizados

#### 6.4 Contas Bancárias

**Localização**: `modals.js` (função `openModalConta()`)

- Nome da conta
- Banco
- Agência
- Número da conta
- Saldo inicial
- Cálculo automático de saldo real

### 7. Relatórios

#### 7.1 Indicadores Financeiros

**Localização**: `app.js` (função `carregarIndicadores()`)

**Cards Exibidos**:
- 💰 Receitas Totais
- 💸 Despesas Totais
- 📊 Saldo Atual
- ⚖️ Margem de Lucro (%)
- 📈 Ticket Médio
- 🔄 Total de Transações

**Gráficos**:
- Pizza: Receitas por categoria
- Pizza: Despesas por categoria
- Barras: Comparativo mensal

**Correção Importante**:
```javascript
// app.js - linha 4232
// CORREÇÃO: Comparação case-insensitive
if (lanc.tipo.toLowerCase() === 'receita') {
    totalReceitas += parseFloat(lanc.valor);
}
```

#### 7.2 Relatório de Crescimento

**Localização**: `app.js` (função `carregarRelatorioCrescimento()`)

- Gráfico de linha anual
- Comparação mês a mês
- Identificação de tendências
- Salvo em `window.graficoCrescimento`

### 8. Sistema de Navegação

#### 8.1 Sidebar Responsiva

**Localização**: `interface_nova.html` (função `toggleSidebar()`)

- Botão de toggle (« / »)
- Transição CSS suave (300ms)
- Redimensionamento automático de gráficos

**Código**:
```javascript
// interface_nova.html - linha 2191
function toggleSidebar() {
    sidebar.classList.toggle('hidden');
    mainContent.classList.toggle('expanded');
    
    // Aguarda transição CSS (350ms)
    setTimeout(() => {
        if (window.graficoCrescimento) {
            window.graficoCrescimento.resize();
        }
        // Redimensiona todos os Chart.js
        Object.keys(Chart.instances).forEach(key => {
            Chart.instances[key]?.resize();
        });
    }, 350);
}
```

#### 8.2 Navegação Entre Seções

**Localização**: `interface_nova.html` (função `showSection()`)

- Oculta todas as seções
- Mostra seção selecionada
- Atualiza botão ativo
- Carrega dados específicos da seção

---

## 📊 Modelos de Dados

### 1. ContaBancaria

**Arquivo**: `models.py`

```python
class ContaBancaria:
    def __init__(self, nome, banco, agencia, conta, 
                 saldo_inicial=0.0, id=None, ativa=True):
        self.id = id
        self.nome = nome
        self.banco = banco
        self.agencia = agencia
        self.conta = conta
        self.saldo_inicial = saldo_inicial
        self.saldo_atual = saldo_inicial
        self.ativa = ativa
```

**Tabela**: `contas_bancarias`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER | Chave primária |
| nome | TEXT | Nome da conta |
| banco | TEXT | Nome do banco |
| agencia | TEXT | Número da agência |
| conta | TEXT | Número da conta |
| saldo_inicial | REAL | Saldo inicial |
| ativa | BOOLEAN | Status da conta |

### 2. Lancamento

**Arquivo**: `models.py`

```python
class Lancamento:
    def __init__(self, descricao, valor, data, tipo, 
                 categoria, status, conta_bancaria,
                 cliente=None, fornecedor=None, 
                 subcategoria=None, observacoes=None):
        self.id = None
        self.descricao = descricao
        self.valor = valor
        self.data = data  # datetime ou string
        self.tipo = tipo  # TipoLancamento
        self.categoria = categoria
        self.status = status  # StatusLancamento
        self.conta_bancaria = conta_bancaria
        self.cliente = cliente
        self.fornecedor = fornecedor
        self.subcategoria = subcategoria
        self.observacoes = observacoes
```

**Tabela**: `lancamentos`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER | Chave primária |
| descricao | TEXT | Descrição do lançamento |
| valor | REAL | Valor |
| data | DATE | Data do lançamento |
| tipo | TEXT | receita/despesa/transferencia |
| categoria | TEXT | Categoria |
| subcategoria | TEXT | Subcategoria ou conta destino |
| status | TEXT | pendente/pago/cancelado/vencido |
| conta_bancaria | TEXT | Conta origem |
| cliente | TEXT | Nome do cliente (opcional) |
| fornecedor | TEXT | Nome do fornecedor (opcional) |
| observacoes | TEXT | Observações adicionais |

### 3. Categoria

**Arquivo**: `models.py`

```python
class Categoria:
    def __init__(self, nome, tipo, descricao="", 
                 subcategorias=None, id=None, 
                 cor="#000000", icone="📊"):
        self.id = id
        self.nome = nome
        self.tipo = tipo  # TipoLancamento
        self.descricao = descricao
        self.subcategorias = subcategorias or []
        self.cor = cor
        self.icone = icone
```

**Tabela**: `categorias`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER | Chave primária |
| nome | TEXT UNIQUE | Nome da categoria |
| tipo | TEXT | receita/despesa/transferencia |
| descricao | TEXT | Descrição |
| subcategorias | TEXT | JSON array de subcategorias |
| cor | TEXT | Código hexadecimal |
| icone | TEXT | Emoji do ícone |

### 4. Cliente

**Arquivo**: `models.py`

```python
class Cliente:
    def __init__(self, nome, cnpj, telefone, email,
                 endereco, status="ativo", id=None):
        self.id = id
        self.nome = nome
        self.cnpj = cnpj
        self.telefone = telefone
        self.email = email
        self.endereco = endereco
        self.status = status
```

**Tabela**: `clientes`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER | Chave primária |
| nome | TEXT | Nome/Razão Social |
| cnpj | TEXT | CNPJ |
| telefone | TEXT | Telefone |
| email | TEXT | Email |
| endereco | TEXT | Endereço completo |
| status | TEXT | ativo/inativo |

### 5. Fornecedor

**Arquivo**: `models.py`

Estrutura idêntica a Cliente, tabela `fornecedores`.

### Enums

```python
class TipoLancamento(Enum):
    RECEITA = "receita"
    DESPESA = "despesa"
    TRANSFERENCIA = "transferencia"

class StatusLancamento(Enum):
    PENDENTE = "pendente"
    PAGO = "pago"
    CANCELADO = "cancelado"
    VENCIDO = "vencido"
```

---

## 🌐 API REST

### Base URL

- **Desenvolvimento**: `http://localhost:5000`
- **Produção**: `https://sistema-financeiro-dwm.up.railway.app`

### Endpoints de Contas Bancárias

#### GET /api/contas
Lista todas as contas bancárias com saldo real calculado.

**Response**:
```json
[
  {
    "nome": "Conta Corrente Principal",
    "banco": "Banco do Brasil",
    "agencia": "1234-5",
    "conta": "12345-6",
    "saldo_inicial": 5000.00,
    "saldo": 7500.50
  }
]
```

#### POST /api/contas
Adiciona uma nova conta bancária.

**Request**:
```json
{
  "nome": "Conta Poupança",
  "banco": "Caixa Econômica",
  "agencia": "0001",
  "conta": "98765-4",
  "saldo_inicial": 1000.00
}
```

**Response**:
```json
{
  "success": true,
  "id": 3
}
```

#### PUT /api/contas/<nome>
Atualiza uma conta existente.

#### DELETE /api/contas/<nome>
Remove uma conta bancária.

### Endpoints de Lançamentos

#### GET /api/lancamentos
Lista todos os lançamentos.

**Query Parameters**:
- `tipo`: receita/despesa/transferencia
- `status`: pendente/pago/cancelado/vencido
- `data_inicio`: YYYY-MM-DD
- `data_fim`: YYYY-MM-DD
- `categoria`: nome da categoria
- `conta`: nome da conta

**Response**:
```json
[
  {
    "id": 1,
    "descricao": "Venda de produto",
    "valor": 1500.00,
    "data": "2025-12-01",
    "tipo": "receita",
    "categoria": "Vendas",
    "subcategoria": "Produtos",
    "status": "pago",
    "conta_bancaria": "Conta Corrente",
    "cliente": "Cliente ABC Ltda",
    "observacoes": null
  }
]
```

#### POST /api/lancamentos
Adiciona um novo lançamento.

**Request**:
```json
{
  "descricao": "Pagamento de fornecedor",
  "valor": 800.00,
  "data": "2025-12-07",
  "tipo": "despesa",
  "categoria": "Fornecedores",
  "subcategoria": "Matéria-prima",
  "status": "pendente",
  "conta_bancaria": "Conta Corrente",
  "fornecedor": "Fornecedor XYZ",
  "observacoes": "Nota fiscal 12345"
}
```

#### PUT /api/lancamentos/<id>
Atualiza um lançamento.

#### DELETE /api/lancamentos/<id>
Remove um lançamento.

#### POST /api/lancamentos/<id>/pagar
Marca um lançamento como pago.

**Request**:
```json
{
  "data_pagamento": "2025-12-07"
}
```

#### POST /api/lancamentos/<id>/cancelar
Cancela um lançamento.

### Endpoints de Categorias

#### GET /api/categorias
Lista todas as categorias.

**Response**:
```json
[
  {
    "id": 1,
    "nome": "Vendas",
    "tipo": "receita",
    "descricao": "Receitas de vendas",
    "subcategorias": ["Produtos", "Serviços"],
    "cor": "#27ae60",
    "icone": "💰"
  }
]
```

#### POST /api/categorias
Adiciona uma nova categoria.

#### PUT /api/categorias/<id>
Atualiza uma categoria.

#### DELETE /api/categorias/<id>
Remove uma categoria.

### Endpoints de Clientes

#### GET /api/clientes
Lista todos os clientes.

#### POST /api/clientes
Adiciona um novo cliente.

#### PUT /api/clientes/<id>
Atualiza um cliente.

#### DELETE /api/clientes/<id>
Remove um cliente.

### Endpoints de Fornecedores

#### GET /api/fornecedores
Lista todos os fornecedores.

#### POST /api/fornecedores
Adiciona um novo fornecedor.

#### PUT /api/fornecedores/<id>
Atualiza um fornecedor.

#### DELETE /api/fornecedores/<id>
Remove um fornecedor.

### Tratamento de Erros

Todos os endpoints retornam erros no formato:

```json
{
  "success": false,
  "error": "Mensagem de erro descritiva"
}
```

**Códigos HTTP**:
- `200`: Sucesso
- `201`: Criado
- `400`: Requisição inválida
- `404`: Não encontrado
- `500`: Erro interno do servidor

---

## 🎨 Interface Web

### Estrutura HTML

**Arquivo**: `templates/interface_nova.html` (2608 linhas)

#### Componentes Principais

1. **Sidebar** (Menu Lateral)
```html
<aside class="sidebar">
    <div class="sidebar-header">
        <span>💰 Sistema Financeiro</span>
    </div>
    <nav class="sidebar-nav">
        <button class="nav-button active" onclick="showSection('dashboard')">
            📊 Dashboard
        </button>
        <!-- Mais botões... -->
    </nav>
</aside>
```

2. **Main Content** (Conteúdo Principal)
```html
<main class="main-content">
    <button class="toggle-sidebar-btn" onclick="toggleSidebar()">«</button>
    
    <div id="dashboard-section" class="content-card">
        <!-- Conteúdo do Dashboard -->
    </div>
    <!-- Mais seções... -->
</main>
```

3. **Modais** (Dialogs)
```html
<div id="modal-cliente" class="modal">
    <div class="modal-content">
        <span class="modal-close" onclick="closeModal('modal-cliente')">&times;</span>
        <h2>Cadastrar Cliente</h2>
        <form><!-- Campos --></form>
    </div>
</div>
```

### Estilos CSS

**Arquivo**: `static/style.css`

#### Variáveis CSS
```css
:root {
    --primary-color: #6c5ce7;
    --secondary-color: #a29bfe;
    --success-color: #00b894;
    --danger-color: #d63031;
    --warning-color: #fdcb6e;
    --dark-bg: #2d3436;
    --sidebar-width: 280px;
}
```

#### Responsividade
```css
@media (max-width: 768px) {
    .sidebar {
        transform: translateX(-280px);
    }
    
    .main-content {
        margin-left: 0;
    }
}
```

#### Animações
```css
.sidebar {
    transition: transform 0.3s ease;
}

.modal {
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
```

### JavaScript Frontend

#### Arquivo app.js (4618 linhas)

**Estrutura**:
```javascript
// ===== VARIÁVEIS GLOBAIS =====
let contasBancarias = [];
let lancamentos = [];
let categorias = [];
let clientes = [];
let fornecedores = [];

// ===== INICIALIZAÇÃO =====
document.addEventListener('DOMContentLoaded', function() {
    inicializarApp();
});

// ===== FUNÇÕES DE CARGA =====
async function carregarDashboard() { /* ... */ }
async function carregarContasReceber() { /* ... */ }
async function carregarContasPagar() { /* ... */ }
async function carregarInadimplencia() { /* ... */ }
async function carregarFluxoCaixa() { /* ... */ }
async function carregarIndicadores() { /* ... */ }

// ===== FUNÇÕES DE CADASTRO =====
async function salvarCliente() { /* ... */ }
async function salvarFornecedor() { /* ... */ }
async function salvarCategoria() { /* ... */ }
async function salvarConta() { /* ... */ }
async function salvarLancamento() { /* ... */ }

// ===== FUNÇÕES DE AÇÃO =====
async function pagarLancamento(id) { /* ... */ }
async function cancelarLancamento(id) { /* ... */ }
async function excluirLancamento(id) { /* ... */ }

// ===== UTILITÁRIOS =====
function formatarMoeda(valor) { /* ... */ }
function formatarData(data) { /* ... */ }
function calcularDiasVencidos(dataVenc) { /* ... */ }
```

#### Arquivo modals.js (1508 linhas)

**Funções principais**:
```javascript
function openModalCliente(id = null) { /* ... */ }
function openModalFornecedor(id = null) { /* ... */ }
function openModalCategoria(id = null) { /* ... */ }
function openModalConta(nome = null) { /* ... */ }
function openModalLancamento(id = null) { /* ... */ }

function closeModal(modalId) { /* ... */ }

async function buscarDadosCNPJ() { /* ... */ }
async function buscarDadosCNPJFornecedor() { /* ... */ }

function showLoadingModal() { /* ... */ }
function hideLoadingModal() { /* ... */ }
```

### Fluxo de Interação

1. **Carregar Página**
   - `DOMContentLoaded` → `inicializarApp()`
   - Carrega dados iniciais (contas, categorias, etc.)
   - Exibe Dashboard por padrão

2. **Navegar Entre Seções**
   - Usuário clica em botão do menu
   - `showSection('nome-secao')`
   - Oculta seções antigas, mostra nova
   - Carrega dados específicos da seção

3. **Abrir Modal de Cadastro**
   - Usuário clica em "Novo Cliente"
   - `openModalCliente()`
   - Exibe modal vazio ou com dados (se edição)
   - Aguarda entrada do usuário

4. **Buscar CNPJ (BrasilAPI)**
   - Usuário digita CNPJ e sai do campo (`onblur`)
   - `buscarDadosCNPJ()`
   - Mostra modal de loading
   - Faz requisição à BrasilAPI
   - Preenche campos automaticamente
   - Oculta modal de loading

5. **Salvar Dados**
   - Usuário clica em "Salvar"
   - `salvarCliente()` (ou outra função)
   - Valida campos obrigatórios
   - Envia POST/PUT para API
   - Fecha modal e recarrega lista

6. **Alternar Menu (Sidebar)**
   - Usuário clica em botão «/»
   - `toggleSidebar()`
   - Adiciona/remove classe 'hidden'
   - Aguarda 350ms (transição CSS)
   - Redimensiona gráficos Chart.js

---

## 🗄️ Banco de Dados

### Gerenciador Universal

**Arquivo**: `database.py`

Classe `DatabaseManager` que detecta e usa o banco apropriado:

```python
class DatabaseManager:
    def __init__(self):
        self.db_type = os.getenv('DATABASE_TYPE', 'sqlite')
        
        if self.db_type == 'postgresql':
            from database_postgresql import DatabasePostgreSQL
            self.db = DatabasePostgreSQL()
        elif self.db_type == 'mysql':
            from database_mysql import DatabaseMySQL
            self.db = DatabaseMySQL()
        else:
            # SQLite padrão
            self.db_file = 'sistema_financeiro.db'
            self._inicializar_banco()
```

### Schemas das Tabelas

#### contas_bancarias
```sql
CREATE TABLE IF NOT EXISTS contas_bancarias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    banco TEXT NOT NULL,
    agencia TEXT NOT NULL,
    conta TEXT NOT NULL,
    saldo_inicial REAL DEFAULT 0,
    ativa BOOLEAN DEFAULT 1
)
```

#### lancamentos
```sql
CREATE TABLE IF NOT EXISTS lancamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL,
    data DATE NOT NULL,
    tipo TEXT NOT NULL,
    categoria TEXT NOT NULL,
    subcategoria TEXT,
    status TEXT DEFAULT 'pendente',
    conta_bancaria TEXT NOT NULL,
    cliente TEXT,
    fornecedor TEXT,
    observacoes TEXT,
    FOREIGN KEY (conta_bancaria) REFERENCES contas_bancarias(nome)
)
```

#### categorias
```sql
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    tipo TEXT NOT NULL,
    descricao TEXT,
    subcategorias TEXT,
    cor TEXT DEFAULT '#000000',
    icone TEXT DEFAULT '📊'
)
```

#### clientes
```sql
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cnpj TEXT,
    telefone TEXT,
    email TEXT,
    endereco TEXT,
    status TEXT DEFAULT 'ativo'
)
```

#### fornecedores
```sql
CREATE TABLE IF NOT EXISTS fornecedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cnpj TEXT,
    telefone TEXT,
    email TEXT,
    endereco TEXT,
    status TEXT DEFAULT 'ativo'
)
```

### Índices

```sql
CREATE INDEX IF NOT EXISTS idx_lancamentos_data ON lancamentos(data);
CREATE INDEX IF NOT EXISTS idx_lancamentos_tipo ON lancamentos(tipo);
CREATE INDEX IF NOT EXISTS idx_lancamentos_status ON lancamentos(status);
CREATE INDEX IF NOT EXISTS idx_lancamentos_conta ON lancamentos(conta_bancaria);
```

### Migração de Dados

**Script**: `migrar_para_railway.py`

Migra dados de SQLite local para PostgreSQL no Railway:

```python
def migrar_dados():
    # Conecta em ambos os bancos
    sqlite_conn = sqlite3.connect('sistema_financeiro.db')
    pg_conn = psycopg2.connect(DATABASE_URL)
    
    # Migra tabela por tabela
    tabelas = ['contas_bancarias', 'categorias', 'clientes', 
               'fornecedores', 'lancamentos']
    
    for tabela in tabelas:
        cursor_sqlite = sqlite_conn.execute(f'SELECT * FROM {tabela}')
        # INSERT INTO pg_conn...
```

### Backup Automático

**Localização**: `backups/`

Estratégia:
- Backup diário automático
- Formato: `backup_YYYYMMDD_HHMMSS.db`
- Retenção: 30 dias

---

## 🚀 Deploy e Produção

### Railway (Plataforma de Deploy)

#### Configuração

**Arquivo**: `Procfile`
```
web: python web_server.py
```

**Arquivo**: `runtime.txt`
```
python-3.11.6
```

**Arquivo**: `.railwayignore`
```
*.db
__pycache__/
.vscode/
backups/
*.pyc
```

#### Variáveis de Ambiente

No painel do Railway, configurar:

```bash
DATABASE_TYPE=postgresql
PGHOST=<railway-host>.railway.app
PGPORT=5432
PGDATABASE=railway
PGUSER=postgres
PGPASSWORD=<senha-gerada>
DATABASE_URL=postgresql://postgres:<senha>@<host>:5432/railway
PORT=5000
```

#### Deploy Automático

1. **Commit no GitHub**:
```bash
git add .
git commit -m "Feature: Nova funcionalidade"
git push origin main
```

2. **Railway detecta push**:
   - Baixa código do GitHub
   - Instala dependências (`requirements_web.txt`)
   - Executa `Procfile` (inicia `web_server.py`)
   - Expõe na URL pública

3. **Logs de Deploy**:
```
Building...
Installing dependencies from requirements_web.txt
Starting web server...
✅ Sistema iniciado na porta 5000
```

#### Monitoramento

- **Logs**: Disponíveis no painel Railway em tempo real
- **Métricas**: CPU, memória, requisições
- **Uptime**: 99.9% de disponibilidade

### Configuração PostgreSQL

**Arquivo**: `database_postgresql.py`

```python
class DatabasePostgreSQL:
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('PGHOST'),
            'port': os.getenv('PGPORT', 5432),
            'database': os.getenv('PGDATABASE'),
            'user': os.getenv('PGUSER'),
            'password': os.getenv('PGPASSWORD')
        }
        self._inicializar_banco()
```

#### Diferenças SQLite → PostgreSQL

| Aspecto | SQLite | PostgreSQL |
|---------|--------|------------|
| **AUTO_INCREMENT** | `AUTOINCREMENT` | `SERIAL` |
| **BOOLEAN** | INTEGER 0/1 | BOOLEAN true/false |
| **DATE** | TEXT | DATE nativo |
| **Tipos numéricos** | REAL | NUMERIC, DECIMAL |

**Ajustes no código**:
```python
# SQLite
CREATE TABLE contas (id INTEGER PRIMARY KEY AUTOINCREMENT, ...)

# PostgreSQL
CREATE TABLE contas (id SERIAL PRIMARY KEY, ...)
```

### Troubleshooting de Deploy

#### Erro: "frontend grpc server closed unexpectedly"

**Causa**: Problema de infraestrutura do Railway

**Solução**: 
- Aguardar alguns minutos
- Fazer novo push vazio: `git commit --allow-empty -m "Rebuild"`
- Reiniciar serviço no painel Railway

#### Erro: "Module not found"

**Causa**: Dependência faltando no `requirements_web.txt`

**Solução**:
```bash
# Adicionar dependência
echo "nome-pacote==versao" >> requirements_web.txt
git add requirements_web.txt
git commit -m "Add missing dependency"
git push
```

#### Erro: "Database connection failed"

**Causa**: Variáveis de ambiente não configuradas

**Solução**:
1. Verificar no painel Railway: Settings → Variables
2. Confirmar que `PGHOST`, `PGDATABASE`, etc. estão definidos
3. Reiniciar serviço

---

## 💻 Configuração Local

### Requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)
- Git
- Navegador web moderno

### Instalação

1. **Clonar Repositório**:
```bash
git clone https://github.com/EduardoSouza-tech/Sistema_financeiro_dwm.git
cd Sistema_financeiro_dwm
```

2. **Criar Ambiente Virtual**:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. **Instalar Dependências**:
```bash
pip install -r requirements_web.txt
```

**Conteúdo do requirements_web.txt**:
```
flask==3.0.0
flask-cors==4.0.0
psycopg2-binary==2.9.9
```

4. **Inicializar Banco de Dados**:
```bash
python -c "from database import DatabaseManager; db = DatabaseManager()"
```

Isso cria o arquivo `sistema_financeiro.db` (SQLite).

### Executar Localmente

#### Método 1: Python direto
```bash
python web_server.py
```

#### Método 2: Script batch (Windows)
```bash
iniciar_web.bat
```

**Conteúdo do iniciar_web.bat**:
```batch
@echo off
echo Iniciando Sistema Financeiro DWM...
call .venv\Scripts\activate
python web_server.py
pause
```

#### Método 3: Flask CLI
```bash
set FLASK_APP=web_server.py
set FLASK_ENV=development
flask run
```

### Acessar Sistema

Abra o navegador em: **http://localhost:5000**

### Configurar VS Code

**Arquivo**: `.vscode/settings.json`
```json
{
    "python.defaultInterpreterPath": ".venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "editor.formatOnSave": true
}
```

**Arquivo**: `pyrightconfig.json`
```json
{
    "include": ["*.py"],
    "exclude": ["**/__pycache__", ".venv"],
    "reportMissingImports": true,
    "reportMissingTypeStubs": false,
    "pythonVersion": "3.11"
}
```

### Testes

#### Verificar Instalação
```bash
python verificar_instalacao.py
```

Verifica:
- Versão do Python
- Pacotes instalados
- Conexão com banco de dados

#### Testar API
```bash
python testar_api.py
```

Testa todos os endpoints REST.

#### Testar Endpoints Específicos
```bash
python testar_endpoints.py
```

---

## 🔌 Integrações Externas

### BrasilAPI

**Documentação**: https://brasilapi.com.br/docs

#### Endpoint CNPJ

**URL**: `https://brasilapi.com.br/api/cnpj/v1/{cnpj}`

**Método**: GET

**Exemplo de Request**:
```javascript
const cnpj = '00000000000191'; // Apenas números
const response = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpj}`);
const data = await response.json();
```

**Exemplo de Response**:
```json
{
  "cnpj": "00.000.000/0001-91",
  "razao_social": "EMPRESA EXEMPLO LTDA",
  "nome_fantasia": "EXEMPLO",
  "logradouro": "RUA EXEMPLO",
  "numero": "123",
  "complemento": "SALA 1",
  "bairro": "CENTRO",
  "municipio": "SAO PAULO",
  "uf": "SP",
  "cep": "01000-000",
  "telefone": "(11) 1234-5678",
  "email": "contato@exemplo.com.br",
  "situacao_cadastral": "ATIVA",
  "data_inicio_atividade": "2020-01-01"
}
```

#### Implementação no Sistema

**Localização**: `static/modals.js` - linha 1365

```javascript
async function buscarDadosCNPJ() {
    const cnpjInput = document.getElementById('clienteCnpj');
    const cnpj = cnpjInput.value.replace(/\D/g, ''); // Remove formatação
    
    if (cnpj.length !== 14) {
        alert('CNPJ inválido. Digite 14 dígitos.');
        return;
    }
    
    // Exibe modal de carregamento
    showLoadingModal('Buscando dados do CNPJ...');
    
    try {
        const response = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpj}`);
        
        if (!response.ok) {
            throw new Error('CNPJ não encontrado');
        }
        
        const data = await response.json();
        
        // Preenche campos automaticamente
        document.getElementById('clienteNome').value = data.razao_social;
        document.getElementById('clienteTelefone').value = data.telefone || '';
        document.getElementById('clienteEmail').value = data.email || '';
        
        const endereco = `${data.logradouro}, ${data.numero} - ${data.bairro}, ${data.municipio}/${data.uf} - CEP: ${data.cep}`;
        document.getElementById('clienteEndereco').value = endereco;
        
        hideLoadingModal();
        console.log('✅ Dados do CNPJ carregados com sucesso!');
        
    } catch (error) {
        hideLoadingModal();
        alert('Erro ao buscar CNPJ: ' + error.message);
        console.error('❌ Erro BrasilAPI:', error);
    }
}
```

#### Modal de Loading

**HTML**:
```html
<div id="loading-modal" class="modal" style="display: none;">
    <div class="modal-backdrop"></div>
    <div class="loading-content">
        <div class="spinner"></div>
        <p id="loading-text">Carregando...</p>
    </div>
</div>
```

**CSS**:
```css
.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #6c5ce7;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
```

**JavaScript**:
```javascript
function showLoadingModal(text = 'Carregando...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-modal').style.display = 'flex';
}

function hideLoadingModal() {
    document.getElementById('loading-modal').style.display = 'none';
}
```

#### Limitações da API

- **Rate Limit**: ~300 requisições/minuto
- **Timeout**: 10 segundos
- **Disponibilidade**: Dependente da Receita Federal
- **CNPJ Inválidos**: Retorna 404

#### Tratamento de Erros

```javascript
try {
    // Requisição...
} catch (error) {
    if (error.message.includes('404')) {
        alert('CNPJ não encontrado na base da Receita Federal');
    } else if (error.message.includes('timeout')) {
        alert('Tempo esgotado. Tente novamente.');
    } else {
        alert('Erro ao consultar CNPJ: ' + error.message);
    }
}
```

---

## 🔧 Manutenção e Troubleshooting

### Problemas Comuns

#### 1. Indicadores mostrando R$ 0,00

**Sintoma**: Dashboard exibe valores zerados mesmo com lançamentos

**Causa**: Comparação de tipos case-sensitive

**Diagnóstico**:
```javascript
console.log('Tipos encontrados:', [...new Set(lancamentos.map(l => l.tipo))]);
// Output: ['receita', 'despesa'] (lowercase)

// Código errado:
if (lanc.tipo === 'RECEITA') // Nunca é true
```

**Solução**:
```javascript
// app.js - linha 4232
if (lanc.tipo.toLowerCase() === 'receita') {
    totalReceitas += parseFloat(lanc.valor);
}
```

**Commit**: `Fix: Corrigir comparacao case-insensitive de tipo e status`

#### 2. Gráficos não redimensionam

**Sintoma**: Após alternar sidebar, gráfico fica com largura fixa

**Causa**: Chart.js não detecta mudança de dimensão do container

**Diagnóstico**:
```javascript
console.log('Chart instance:', window.graficoCrescimento);
// undefined ou objeto sem resize()
```

**Solução**:
```javascript
// interface_nova.html - linha 2191
function toggleSidebar() {
    sidebar.classList.toggle('hidden');
    mainContent.classList.toggle('expanded');
    
    // Aguardar transição CSS (300ms) + buffer
    setTimeout(() => {
        if (window.graficoCrescimento) {
            window.graficoCrescimento.resize();
        }
        
        // Redimensionar todos os Chart.js
        Object.keys(Chart.instances).forEach(key => {
            Chart.instances[key]?.resize();
        });
    }, 350);
}
```

**Commits**:
- `Fix: Redimensionar graficos Chart.js ao alternar visibilidade do menu`
- `Fix: Corrigir referencia do grafico para window.graficoCrescimento`

#### 3. Sidebar não oculta

**Sintoma**: Botão de toggle não funciona

**Causa**: Incompatibilidade entre classe JavaScript e CSS

**Diagnóstico**:
```javascript
// JavaScript usava:
sidebar.classList.toggle('collapsed');

// CSS esperava:
.sidebar.hidden { transform: translateX(-280px); }
```

**Solução**:
```javascript
// Mudar JavaScript para usar 'hidden'
sidebar.classList.toggle('hidden');
```

**Commit**: `Fix: Corrigir toggle do menu lateral`

#### 4. CNPJ não preenche campos

**Sintoma**: Busca CNPJ não auto-completa formulário

**Causas Possíveis**:
1. CNPJ inválido
2. API BrasilAPI fora do ar
3. IDs dos campos HTML incorretos
4. CORS bloqueado

**Diagnóstico**:
```javascript
// Console do navegador:
console.log('CNPJ digitado:', cnpj);
console.log('Response:', data);
console.log('Campo nome:', document.getElementById('clienteNome'));
```

**Soluções**:

**a) Verificar CNPJ**:
```javascript
if (cnpj.length !== 14) {
    alert('CNPJ deve ter 14 dígitos');
    return;
}
```

**b) Testar API manualmente**:
```bash
curl https://brasilapi.com.br/api/cnpj/v1/00000000000191
```

**c) Verificar IDs HTML**:
```html
<!-- Modal de Cliente -->
<input type="text" id="clienteNome" name="nome">
<input type="text" id="clienteTelefone" name="telefone">
<!-- IDs devem coincidir com JavaScript -->
```

**d) Adicionar timeout**:
```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 10000);

const response = await fetch(url, { signal: controller.signal });
clearTimeout(timeoutId);
```

#### 5. Deploy falha no Railway

**Sintomas**:
- "frontend grpc server closed unexpectedly"
- "Build failed"
- "Application crashed"

**Soluções**:

**a) Problema de Infraestrutura**:
```bash
# Fazer rebuild
git commit --allow-empty -m "chore: trigger rebuild"
git push origin main
```

**b) Dependências Faltando**:
```bash
# Verificar requirements_web.txt
cat requirements_web.txt

# Adicionar dependência
echo "nome-pacote==versao" >> requirements_web.txt
git add requirements_web.txt
git commit -m "Add missing dependency"
git push
```

**c) Variáveis de Ambiente**:
- Acessar Railway Dashboard
- Settings → Variables
- Verificar `DATABASE_TYPE`, `PGHOST`, `DATABASE_URL`, etc.

**d) Logs de Deploy**:
- Railway Dashboard → Deployments → View Logs
- Procurar por mensagens de erro específicas

#### 6. Banco de dados não atualiza

**Sintoma**: Alterações não persistem após reiniciar

**Causa**: Usando SQLite local em produção

**Solução**:
```python
# database.py
db_type = os.getenv('DATABASE_TYPE', 'sqlite')

# No Railway, definir:
DATABASE_TYPE=postgresql
```

**Migrar dados**:
```bash
python migrar_para_railway.py
```

#### 7. Dados JSON não migrados

**Sintoma**: Sistema vazio após primeira inicialização

**Verificação**:
```python
# web_server.py
if os.path.exists('dados_financeiros.json'):
    print("Migrando dados do JSON...")
    db.migrar_dados_json('dados_financeiros.json')
```

**Solução**:
```bash
# Se arquivo JSON existe localmente
python -c "from database import DatabaseManager; db = DatabaseManager(); db.migrar_dados_json('dados_financeiros.json')"
```

### Logs e Debugging

#### Ativar Logs Detalhados

```python
# web_server.py
import logging

logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

@app.route('/api/lancamentos', methods=['POST'])
def adicionar_lancamento():
    app.logger.debug(f'Request data: {request.json}')
    # ...
```

#### Console do Navegador

```javascript
// Ativar logs detalhados
localStorage.setItem('debug', 'true');

// No código:
if (localStorage.getItem('debug')) {
    console.log('Debug:', variavel);
}
```

#### Verificar Estado do Banco

```bash
# SQLite
sqlite3 sistema_financeiro.db
.tables
SELECT * FROM lancamentos LIMIT 5;

# PostgreSQL (Railway)
psql $DATABASE_URL
\dt
SELECT * FROM lancamentos LIMIT 5;
```

### Backup e Restore

#### Backup SQLite

```bash
# Manual
cp sistema_financeiro.db backups/backup_$(date +%Y%m%d).db

# Automático (cron job)
0 2 * * * cp /path/to/sistema_financeiro.db /path/to/backups/backup_$(date +\%Y\%m\%d).db
```

#### Backup PostgreSQL

```bash
# Via Railway CLI
railway backup create

# Via pg_dump
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

### Performance

#### Otimizar Consultas

```python
# Usar índices
db.execute('CREATE INDEX idx_lancamentos_data ON lancamentos(data)')

# Limitar resultados
SELECT * FROM lancamentos WHERE data >= ? ORDER BY data DESC LIMIT 100
```

#### Cache no Frontend

```javascript
// Cachear dados que não mudam frequentemente
let categoriasCache = null;
let cacheTimestamp = null;

async function carregarCategorias() {
    const agora = Date.now();
    
    // Cache válido por 5 minutos
    if (categoriasCache && (agora - cacheTimestamp) < 300000) {
        return categoriasCache;
    }
    
    const response = await fetch('/api/categorias');
    categoriasCache = await response.json();
    cacheTimestamp = agora;
    
    return categoriasCache;
}
```

#### Lazy Loading

```javascript
// Carregar dados sob demanda
function showSection(sectionId) {
    // Só carregar quando seção é exibida
    if (sectionId === 'inadimplencia') {
        carregarInadimplencia();
    }
}
```

---

## 📚 Referências

### Documentação Oficial

- **Flask**: https://flask.palletsprojects.com/
- **Chart.js**: https://www.chartjs.org/docs/
- **BrasilAPI**: https://brasilapi.com.br/docs
- **Railway**: https://docs.railway.app/
- **PostgreSQL**: https://www.postgresql.org/docs/

### Tutoriais

- Python Flask REST API: https://realpython.com/flask-connexion-rest-api/
- Chart.js Responsive: https://www.chartjs.org/docs/latest/configuration/responsive.html
- Deploy Flask Railway: https://docs.railway.app/tutorials/deploy-a-flask-app

### Ferramentas

- **VS Code**: https://code.visualstudio.com/
- **Postman**: https://www.postman.com/ (testar API)
- **DB Browser for SQLite**: https://sqlitebrowser.org/
- **pgAdmin**: https://www.pgadmin.org/ (PostgreSQL GUI)

---

## 📞 Suporte

### Issues no GitHub

Para reportar bugs ou solicitar funcionalidades:
https://github.com/EduardoSouza-tech/Sistema_financeiro_dwm/issues

### Contato

- **Desenvolvedor**: Eduardo Souza
- **Email**: eduardo@exemplo.com
- **GitHub**: https://github.com/EduardoSouza-tech

---

## 📝 Changelog

### Versão 2.1 (Dezembro 2025)

#### Adicionado
- ✅ Integração com BrasilAPI para auto-fill de CNPJ
- ✅ Modal de loading animado durante busca de CNPJ
- ✅ Seção de Inadimplência com cards e tabela detalhada
- ✅ Badge de inadimplentes no menu lateral
- ✅ Sidebar responsiva com toggle suave

#### Corrigido
- ✅ Indicadores financeiros mostrando R$ 0,00 (comparação case-insensitive)
- ✅ Gráficos Chart.js não redimensionando ao alternar sidebar
- ✅ Sidebar toggle usando classe incorreta
- ✅ CNPJ em Fornecedores não buscando dados

#### Otimizado
- ✅ Fontes da tabela Fluxo de Caixa (11-13px)
- ✅ Header de tabelas com gradiente roxo
- ✅ Redimensionamento de gráficos com setTimeout adequado

### Versão 2.0 (Novembro 2025)

#### Adicionado
- ✅ Deploy no Railway com PostgreSQL
- ✅ Migração automática SQLite → PostgreSQL
- ✅ Interface web completamente redesenhada
- ✅ Dashboard com gráfico de evolução financeira
- ✅ Relatório de indicadores financeiros
- ✅ Fluxo de caixa mensal

#### Corrigido
- ✅ Cálculo de saldo real das contas bancárias
- ✅ Transferências entre contas
- ✅ Validação de CNPJ duplicado

### Versão 1.0 (Outubro 2025)

- ✅ Versão inicial com interface GUI Tkinter
- ✅ Cadastros básicos (Contas, Categorias, Clientes, Fornecedores)
- ✅ Lançamentos financeiros
- ✅ Banco de dados SQLite

---

## 📄 Licença

Este projeto é de propriedade privada e não possui licença open source.

**Todos os direitos reservados © 2025 DWM Sistemas**

---

## 🎉 Agradecimentos

- Equipe de desenvolvimento DWM
- Comunidade Python/Flask
- Desenvolvedores do Chart.js
- BrasilAPI pela API gratuita
- Railway pela infraestrutura

---

**Documentação gerada em**: 07/12/2025  
**Versão do Sistema**: 2.1  
**Última atualização**: 07/12/2025  
**Autor**: Eduardo Souza - DWM Sistemas

---

## 🔄 Atualizações Futuras

### Roadmap

#### Versão 2.2 (Planejado)
- [ ] Exportação de relatórios em PDF
- [ ] Exportação de dados em Excel
- [ ] Gráficos adicionais (pizza, rosca)
- [ ] Filtros avançados com múltiplos critérios
- [ ] Busca global no sistema

#### Versão 2.3 (Planejado)
- [ ] Autenticação de usuários
- [ ] Múltiplos perfis (Admin, Operador, Visualizador)
- [ ] Auditoria de alterações
- [ ] Notificações de vencimento (email/push)

#### Versão 3.0 (Futuro)
- [ ] App mobile (React Native)
- [ ] API GraphQL
- [ ] Integração com bancos (Open Banking)
- [ ] IA para previsão de fluxo de caixa
- [ ] Dashboard customizável

---

*Esta documentação é mantida atualizada a cada release. Para a versão mais recente, consulte o repositório no GitHub.*
