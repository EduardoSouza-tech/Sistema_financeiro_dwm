# 📊 Documentação - Comparativo de Períodos

**Versão:** 1.0.0  
**Data:** Janeiro 2025  
**Status:** ✅ Funcional  

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Funcionalidades](#funcionalidades)
3. [Arquitetura](#arquitetura)
4. [API Backend](#api-backend)
5. [Interface Frontend](#interface-frontend)
6. [Uso e Exemplos](#uso-e-exemplos)
7. [Cálculos e Métricas](#cálculos-e-métricas)
8. [Exportação de Dados](#exportação-de-dados)
9. [Responsividade](#responsividade)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O **Comparativo de Períodos** é uma funcionalidade avançada do sistema financeiro que permite comparar dados financeiros entre dois períodos distintos, fornecendo análises detalhadas sobre:

- **Receitas e Despesas**: Valores totais e variações percentuais
- **Saldo Final**: Comparação de resultados líquidos
- **Top Categorias**: Ranking das 3 principais receitas e despesas
- **Maiores Movimentações**: Identificação de categorias de maior impacto
- **Análise Percentual**: Distribuição por categoria em cada período

### 🎨 Características

✅ Comparação período a período (mês vs mês, ano vs ano, etc.)  
✅ Visualização side-by-side com cards coloridos  
✅ Variações percentuais com cores semânticas (verde/vermelho)  
✅ Rankings de top 3 receitas e despesas  
✅ Estatísticas de maior receita/despesa por categoria  
✅ Interface responsiva para mobile/tablet/desktop  
✅ Exportação para PDF e Excel (em desenvolvimento)  

---

## 🚀 Funcionalidades

### 1. Seleção de Períodos

**Período 1 e Período 2:**
- Seleção de **ano** (obrigatório)
- Seleção de **mês** (opcional)
  - Se mês não for selecionado, analisa o ano inteiro
  - Se mês for selecionado, analisa apenas aquele mês

**Exemplos de Comparações:**
- Janeiro 2024 vs Janeiro 2025
- Ano completo 2023 vs Ano completo 2024
- Março 2024 vs Dezembro 2024
- Q1 2024 (jan-mar) vs Q1 2025 (jan-mar)

### 2. Visualização de Dados

#### Cards de Resumo
Cada período é exibido em um card colorido contendo:
- Data de início e fim do período
- Total de receitas
- Total de despesas
- Saldo final (receitas - despesas)

#### Painel de Variações
Mostra a variação percentual entre Período 2 e Período 1:
- **Receitas**: Crescimento/Queda em %
- **Despesas**: Aumento/Redução em %
- **Saldo**: Melhor/Pior em %

Cores:
- 🟢 Verde: Variação positiva (receitas/saldo)
- 🔴 Vermelho: Variação negativa (receitas/saldo)
- 🔴 Vermelho: Aumento despesas
- 🟢 Verde: Redução despesas
- ⚪ Cinza: Sem variação

#### Top 3 Categorias
Exibe lado a lado:
- **Top 3 Receitas** por categoria (ambos períodos)
- **Top 3 Despesas** por categoria (ambos períodos)

Para cada categoria:
- Posição no ranking (#1, #2, #3)
- Nome da categoria
- Valor total
- Percentual do total

#### Resumo Estatístico
- Maior receita de cada período (categoria + valor)
- Maior despesa de cada período (categoria + valor)

---

## 🏗️ Arquitetura

### Stack Tecnológica

**Backend:**
- Flask (Python 3.x)
- PostgreSQL
- SQLAlchemy

**Frontend:**
- HTML5 / CSS3
- Vanilla JavaScript (ES6+)
- Chart.js (gráficos)

### Fluxo de Dados

```
┌─────────────┐
│   Usuário   │
└──────┬──────┘
       │ Seleciona períodos
       ▼
┌─────────────────────────────────┐
│  Frontend (interface_nova.html) │
│  - Validação de inputs          │
│  - Cálculo de datas             │
│  - Chamada API                  │
└──────────┬──────────────────────┘
           │ GET /api/relatorios/comparativo-periodos
           ▼
┌─────────────────────────────────┐
│   Backend (web_server.py)       │
│  - Validação de parâmetros      │
│  - Consultas SQL                │
│  - Cálculo de métricas          │
│  - Ordenação e ranking          │
└──────────┬──────────────────────┘
           │ JSON Response
           ▼
┌─────────────────────────────────┐
│   Frontend - Renderização       │
│  - Parse de dados               │
│  - Geração de HTML              │
│  - Aplicação de estilos         │
└─────────────────────────────────┘
```

---

## 🔌 API Backend

### Endpoint

```http
GET /api/relatorios/comparativo-periodos
```

### Parâmetros (Query String)

| Parâmetro       | Tipo   | Obrigatório | Formato      | Descrição                    |
|-----------------|--------|-------------|--------------|------------------------------|
| `data_inicio1`  | string | Sim         | YYYY-MM-DD   | Data inicial do período 1    |
| `data_fim1`     | string | Sim         | YYYY-MM-DD   | Data final do período 1      |
| `data_inicio2`  | string | Sim         | YYYY-MM-DD   | Data inicial do período 2    |
| `data_fim2`     | string | Sim         | YYYY-MM-DD   | Data final do período 2      |

### Exemplo de Requisição

```javascript
GET /api/relatorios/comparativo-periodos?
    data_inicio1=2024-01-01&
    data_fim1=2024-01-31&
    data_inicio2=2025-01-01&
    data_fim2=2025-01-31
```

### Resposta de Sucesso (200 OK)

```json
{
  "periodo1": {
    "datas": {
      "inicio": "2024-01-01",
      "fim": "2024-01-31"
    },
    "dados": {
      "receitas": 125000.50,
      "despesas": 87500.30,
      "saldo": 37500.20,
      "maior_receita": {
        "categoria": "Vendas",
        "valor": 95000.00
      },
      "maior_despesa": {
        "categoria": "Salários",
        "valor": 45000.00
      },
      "maior_receita_sub": {
        "subcategoria": "Vendas > Produtos",
        "valor": 80000.00
      },
      "maior_despesa_sub": {
        "subcategoria": "Salários > Folha de Pagamento",
        "valor": 40000.00
      },
      "top_receitas": [
        {
          "categoria": "Vendas",
          "valor": 95000.00,
          "percentual": 76.00
        },
        {
          "categoria": "Serviços",
          "valor": 20000.00,
          "percentual": 16.00
        },
        {
          "categoria": "Investimentos",
          "valor": 10000.50,
          "percentual": 8.00
        }
      ],
      "top_despesas": [
        {
          "categoria": "Salários",
          "valor": 45000.00,
          "percentual": 51.43
        },
        {
          "categoria": "Fornecedores",
          "valor": 30000.00,
          "percentual": 34.29
        },
        {
          "categoria": "Impostos",
          "valor": 12500.30,
          "percentual": 14.28
        }
      ],
      "qtd_categorias_receitas": 8,
      "qtd_categorias_despesas": 12
    }
  },
  "periodo2": {
    "datas": {
      "inicio": "2025-01-01",
      "fim": "2025-01-31"
    },
    "dados": {
      "receitas": 145000.00,
      "despesas": 92000.00,
      "saldo": 53000.00,
      "maior_receita": {
        "categoria": "Vendas",
        "valor": 110000.00
      },
      "maior_despesa": {
        "categoria": "Salários",
        "valor": 47000.00
      },
      "maior_receita_sub": {
        "subcategoria": "Vendas > Produtos",
        "valor": 95000.00
      },
      "maior_despesa_sub": {
        "subcategoria": "Salários > Folha de Pagamento",
        "valor": 42000.00
      },
      "top_receitas": [
        {
          "categoria": "Vendas",
          "valor": 110000.00,
          "percentual": 75.86
        },
        {
          "categoria": "Serviços",
          "valor": 25000.00,
          "percentual": 17.24
        },
        {
          "categoria": "Investimentos",
          "valor": 10000.00,
          "percentual": 6.90
        }
      ],
      "top_despesas": [
        {
          "categoria": "Salários",
          "valor": 47000.00,
          "percentual": 51.09
        },
        {
          "categoria": "Fornecedores",
          "valor": 32000.00,
          "percentual": 34.78
        },
        {
          "categoria": "Impostos",
          "valor": 13000.00,
          "percentual": 14.13
        }
      ],
      "qtd_categorias_receitas": 9,
      "qtd_categorias_despesas": 13
    }
  },
  "variacoes": {
    "receitas": 16.00,
    "despesas": 5.14,
    "saldo": 41.33
  }
}
```

### Resposta de Erro (400 Bad Request)

```json
{
  "error": "Parâmetros obrigatórios: data_inicio1, data_fim1, data_inicio2, data_fim2"
}
```

### Implementação Backend (web_server.py)

**Localização:** Linhas 4956-5054

**Lógica Principal:**

1. **Validação de Parâmetros**
   ```python
   data_inicio1 = request.args.get('data_inicio1')
   data_fim1 = request.args.get('data_fim1')
   data_inicio2 = request.args.get('data_inicio2')
   data_fim2 = request.args.get('data_fim2')
   
   if not all([data_inicio1, data_fim1, data_inicio2, data_fim2]):
       return jsonify({'error': 'Parâmetros obrigatórios'}), 400
   ```

2. **Função auxiliar `calcular_periodo()`**
   - Recebe datas de início e fim
   - Consulta banco de dados (tabela `transacoes`)
   - Filtra por `empresa_id` (multi-tenant)
   - Agrupa por categoria
   - Calcula:
     - Total de receitas
     - Total de despesas
     - Saldo (receitas - despesas)
     - Maior receita/despesa (categoria e subcategoria)
     - Top 3 receitas/despesas com percentuais
     - Quantidade de categorias distintas

3. **Cálculo de Variações**
   ```python
   variacoes = {
       'receitas': round(((p2_receitas - p1_receitas) / p1_receitas * 100) if p1_receitas > 0 else 0, 2),
       'despesas': round(((p2_despesas - p1_despesas) / p1_despesas * 100) if p1_despesas > 0 else 0, 2),
       'saldo': round(((p2_saldo - p1_saldo) / abs(p1_saldo) * 100) if p1_saldo != 0 else 0, 2)
   }
   ```

4. **Retorno JSON**
   - Estrutura com `periodo1`, `periodo2`, `variacoes`

---

## 🎨 Interface Frontend

### Localização

**Arquivo:** `templates/interface_nova.html`

**Seções:**

1. **HTML da Interface** (Linhas 1937-2009)
2. **JavaScript Functions** (Linhas 5410-5730)

### Estrutura HTML

```html
<div id="content-comparativo-periodos" class="content-section">
    <h2>📉 Comparativo de Períodos</h2>
    
    <!-- Filtros -->
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">
        <!-- Período 1 -->
        <div>
            <label>Ano (Período 1):</label>
            <select id="filter-ano1">
                <option value="">Selecione</option>
                <option value="2023">2023</option>
                <option value="2024">2024</option>
                <option value="2025">2025</option>
            </select>
        </div>
        <div>
            <label>Mês (Período 1):</label>
            <select id="filter-mes1">
                <option value="">Ano Inteiro</option>
                <option value="1">Janeiro</option>
                <!-- ... demais meses ... -->
            </select>
        </div>
        
        <!-- Período 2 -->
        <div>
            <label>Ano (Período 2):</label>
            <select id="filter-ano2">
                <!-- ... mesma estrutura ... -->
            </select>
        </div>
        <div>
            <label>Mês (Período 2):</label>
            <select id="filter-mes2">
                <!-- ... mesma estrutura ... -->
            </select>
        </div>
    </div>
    
    <!-- Botões -->
    <div style="margin-top: 20px;">
        <button onclick="carregarComparativoPeriodos()">
            🔍 Comparar Períodos
        </button>
        <button onclick="exportarComparativoPDF()">
            📄 Exportar PDF
        </button>
        <button onclick="exportarComparativoExcel()">
            📊 Exportar Excel
        </button>
    </div>
    
    <!-- Área de conteúdo -->
    <div id="comparativo-periodos-content"></div>
</div>
```

### Funções JavaScript

#### 1. `carregarComparativoPeriodos()`

**Responsabilidade:** Buscar dados da API e renderizar comparativo

**Fluxo:**

```javascript
async function carregarComparativoPeriodos() {
    // 1. Coletar valores dos filtros
    const ano1 = document.getElementById('filter-ano1').value;
    const mes1 = document.getElementById('filter-mes1').value;
    const ano2 = document.getElementById('filter-ano2').value;
    const mes2 = document.getElementById('filter-mes2').value;
    
    // 2. Validar inputs
    if (!ano1 || !ano2) {
        showToast('Por favor, preencha os anos', 'error');
        return;
    }
    
    // 3. Calcular datas de início e fim
    let dataInicio1, dataFim1, dataInicio2, dataFim2;
    
    if (mes1) {
        // Mês específico
        dataInicio1 = `${ano1}-${mes1.padStart(2, '0')}-01`;
        const ultimoDia = new Date(parseInt(ano1), parseInt(mes1), 0).getDate();
        dataFim1 = `${ano1}-${mes1.padStart(2, '0')}-${ultimoDia}`;
    } else {
        // Ano inteiro
        dataInicio1 = `${ano1}-01-01`;
        dataFim1 = `${ano1}-12-31`;
    }
    
    // ... mesmo processo para período 2 ...
    
    // 4. Fazer requisição à API
    const params = new URLSearchParams({
        data_inicio1: dataInicio1,
        data_fim1: dataFim1,
        data_inicio2: dataInicio2,
        data_fim2: dataFim2
    });
    
    const response = await fetch(`/api/relatorios/comparativo-periodos?${params}`);
    const data = await response.json();
    
    // 5. Renderizar resultado
    renderizarComparativo(data);
}
```

#### 2. `renderizarComparativo(data)`

**Responsabilidade:** Gerar HTML visual com os dados recebidos

**Componentes Renderizados:**

1. **Cards de Período (Grid 2 colunas)**
   ```html
   <div style="display: grid; grid-template-columns: 1fr 1fr;">
       <!-- Card Período 1 (gradiente roxo) -->
       <div style="background: linear-gradient(135deg, #667eea, #764ba2);">
           <h3>📅 Período 1</h3>
           <p>01/01/2024 até 31/01/2024</p>
           <div>Receitas: R$ 125.000,50</div>
           <div>Despesas: R$ 87.500,30</div>
           <div>Saldo: R$ 37.500,20</div>
       </div>
       
       <!-- Card Período 2 (gradiente rosa) -->
       <div style="background: linear-gradient(135deg, #f093fb, #f5576c);">
           <!-- ... mesma estrutura ... -->
       </div>
   </div>
   ```

2. **Painel de Variações (Grid 3 colunas)**
   ```html
   <div style="display: grid; grid-template-columns: repeat(3, 1fr);">
       <!-- Receitas -->
       <div style="color: #27ae60;">
           📈 +16.00%
           <div>Crescimento</div>
       </div>
       
       <!-- Despesas -->
       <div style="color: #e74c3c;">
           📈 +5.14%
           <div>Aumento</div>
       </div>
       
       <!-- Saldo -->
       <div style="color: #27ae60;">
           📈 +41.33%
           <div>Melhor</div>
       </div>
   </div>
   ```

3. **Top 3 Receitas e Despesas (Grid 2 colunas)**
   - Lista ordenada com ranking
   - Valores formatados em R$
   - Percentuais
   - Cores semânticas (verde para receitas, vermelho para despesas)

4. **Resumo Estatístico (Grid 2x2)**
   - Maior receita de cada período
   - Maior despesa de cada período

**Funções Auxiliares:**

```javascript
// Formatar período legível
const formatarPeriodo = (inicio, fim) => {
    const dtInicio = new Date(inicio);
    const dtFim = new Date(fim);
    return `${dtInicio.toLocaleDateString('pt-BR')} até ${dtFim.toLocaleDateString('pt-BR')}`;
};

// Ícone de variação
const iconeVariacao = (valor) => {
    if (valor > 0) return '📈';
    if (valor < 0) return '📉';
    return '➡️';
};

// Cor de variação
const corVariacao = (valor, invertido = false) => {
    if (invertido) {
        return valor > 0 ? '#e74c3c' : valor < 0 ? '#27ae60' : '#95a5a6';
    }
    return valor > 0 ? '#27ae60' : valor < 0 ? '#e74c3c' : '#95a5a6';
};
```

#### 3. `exportarComparativoPDF()` ⚠️ Em Desenvolvimento

**Objetivo:** Gerar PDF do comparativo

**Planejamento:**
- Usar biblioteca jsPDF
- Incluir logo da empresa
- Títulos e subtítulos
- Tabelas formatadas
- Gráficos (se possível)

#### 4. `exportarComparativoExcel()` ⚠️ Em Desenvolvimento

**Objetivo:** Gerar planilha Excel

**Planejamento:**
- Usar biblioteca SheetJS (xlsx.js)
- Múltiplas abas:
  - "Resumo" com métricas principais
  - "Período 1" com detalhes
  - "Período 2" com detalhes
  - "Variações" com comparativos
  - "Top Categorias" com rankings

---

## 📚 Uso e Exemplos

### Caso de Uso 1: Comparar Janeiro 2024 vs Janeiro 2025

**Objetivo:** Ver crescimento mês a mês

**Passos:**
1. Selecionar Ano (Período 1): **2024**
2. Selecionar Mês (Período 1): **Janeiro**
3. Selecionar Ano (Período 2): **2025**
4. Selecionar Mês (Período 2): **Janeiro**
5. Clicar em **🔍 Comparar Períodos**

**Resultado Esperado:**
- Cards mostrando totais de jan/2024 vs jan/2025
- Variação percentual (ex: Receitas +16%, Despesas +5%, Saldo +41%)
- Top 3 categorias de cada mês
- Identificação de categorias que mais cresceram

---

### Caso de Uso 2: Comparar Ano Completo 2023 vs 2024

**Objetivo:** Análise anual

**Passos:**
1. Selecionar Ano (Período 1): **2023**
2. Deixar Mês (Período 1): **Ano Inteiro**
3. Selecionar Ano (Período 2): **2024**
4. Deixar Mês (Período 2): **Ano Inteiro**
5. Clicar em **🔍 Comparar Períodos**

**Resultado Esperado:**
- Visão macro do desempenho anual
- Crescimento/queda geral
- Mudanças na estrutura de receitas/despesas
- Categorias que mais contribuíram para o resultado

---

### Caso de Uso 3: Comparar Trimestres

**Objetivo:** Avaliar performance trimestral

**Passos:**
1. **Q1 2024** (jan-mar) vs **Q1 2025** (jan-mar)
2. Usar filtros mês a mês ou criar query customizada

**Resultado Esperado:**
- Sazonalidade trimestral
- Tendências de crescimento

---

## 🧮 Cálculos e Métricas

### 1. Variação Percentual

**Fórmula:**
```
Variação % = ((Valor Período 2 - Valor Período 1) / Valor Período 1) × 100
```

**Exemplo:**
- Receitas P1: R$ 100.000
- Receitas P2: R$ 120.000
- Variação: ((120.000 - 100.000) / 100.000) × 100 = **20%**

**Casos Especiais:**
- Se Período 1 = 0: Variação = 0% (evita divisão por zero)
- Saldo negativo: Usa valor absoluto no denominador

### 2. Percentual por Categoria

**Fórmula:**
```
Percentual = (Valor Categoria / Total Receitas ou Despesas) × 100
```

**Exemplo:**
- Categoria "Vendas": R$ 80.000
- Total Receitas: R$ 100.000
- Percentual: (80.000 / 100.000) × 100 = **80%**

### 3. Ranking Top 3

**Algoritmo:**
1. Agrupar transações por categoria
2. Somar valores de cada categoria
3. Ordenar por valor decrescente
4. Selecionar top 3
5. Calcular percentual de cada uma

### 4. Maior Receita/Despesa

**Algoritmo:**
1. Agrupar por categoria
2. Encontrar categoria com maior soma
3. Retornar nome e valor

**Subcategoria:**
- Mesma lógica, mas agrupa por `categoria > subcategoria`

---

## 📤 Exportação de Dados

### PDF (⚠️ Em Desenvolvimento)

**Biblioteca:** jsPDF

**Estrutura Planejada:**

```
┌──────────────────────────────────────┐
│  LOGO     Sistema Financeiro DWM     │
│                                      │
│  COMPARATIVO DE PERÍODOS             │
│                                      │
│  Período 1: 01/01/2024 - 31/01/2024 │
│  Período 2: 01/01/2025 - 31/01/2025 │
├──────────────────────────────────────┤
│  RESUMO EXECUTIVO                    │
│  ┌────────────┬────────────┬────────┐
│  │            │ Período 1  │ P2     │
│  ├────────────┼────────────┼────────┤
│  │ Receitas   │ 125.000,50 │ 145k   │
│  │ Despesas   │  87.500,30 │  92k   │
│  │ Saldo      │  37.500,20 │  53k   │
│  └────────────┴────────────┴────────┘
├──────────────────────────────────────┤
│  VARIAÇÕES                           │
│  • Receitas: +16.00% (↑)            │
│  • Despesas: +5.14% (↑)             │
│  • Saldo: +41.33% (↑)               │
├──────────────────────────────────────┤
│  TOP 3 RECEITAS - PERÍODO 1          │
│  1. Vendas ......... R$ 95.000 (76%)│
│  2. Serviços ....... R$ 20.000 (16%)│
│  3. Investimentos .. R$ 10.000 (8%) │
│  ...                                 │
└──────────────────────────────────────┘
```

**Implementação Futura:**

```javascript
async function exportarComparativoPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    // Adicionar conteúdo
    doc.text('Comparativo de Períodos', 10, 10);
    // ... adicionar tabelas, gráficos ...
    
    doc.save('comparativo-periodos.pdf');
}
```

---

### Excel (⚠️ Em Desenvolvimento)

**Biblioteca:** SheetJS (xlsx.js)

**Estrutura Planejada:**

**Aba 1: Resumo**
| Métrica   | Período 1 | Período 2 | Variação % |
|-----------|-----------|-----------|------------|
| Receitas  | 125.000   | 145.000   | +16.00%    |
| Despesas  | 87.500    | 92.000    | +5.14%     |
| Saldo     | 37.500    | 53.000    | +41.33%    |

**Aba 2: Receitas Detalhadas**
| Categoria     | Período 1 | % P1 | Período 2 | % P2 | Variação |
|---------------|-----------|------|-----------|------|----------|
| Vendas        | 95.000    | 76%  | 110.000   | 76%  | +15.79%  |
| Serviços      | 20.000    | 16%  | 25.000    | 17%  | +25.00%  |
| Investimentos | 10.000    | 8%   | 10.000    | 7%   | 0.00%    |

**Aba 3: Despesas Detalhadas**
| Categoria     | Período 1 | % P1 | Período 2 | % P2 | Variação |
|---------------|-----------|------|-----------|------|----------|
| Salários      | 45.000    | 51%  | 47.000    | 51%  | +4.44%   |
| Fornecedores  | 30.000    | 34%  | 32.000    | 35%  | +6.67%   |
| Impostos      | 12.500    | 14%  | 13.000    | 14%  | +4.00%   |

**Aba 4: Top Categorias**
- Gráfico de barras com top 3 receitas
- Gráfico de barras com top 3 despesas

**Implementação Futura:**

```javascript
async function exportarComparativoExcel() {
    const XLSX = window.XLSX;
    
    // Criar workbook
    const wb = XLSX.utils.book_new();
    
    // Aba Resumo
    const wsResumo = XLSX.utils.json_to_sheet([
        {Métrica: 'Receitas', 'Período 1': 125000, 'Período 2': 145000, 'Variação %': 16.00},
        // ...
    ]);
    XLSX.utils.book_append_sheet(wb, wsResumo, 'Resumo');
    
    // Aba Receitas
    // ...
    
    // Exportar
    XLSX.writeFile(wb, 'comparativo-periodos.xlsx');
}
```

---

## 📱 Responsividade

### Breakpoints

```css
/* Desktop Grande (> 1920px) */
@media (min-width: 1921px) {
    .comparativo-periodos-content {
        max-width: 1800px;
        margin: 0 auto;
    }
}

/* Desktop (1200px - 1920px) */
@media (max-width: 1920px) {
    /* Layout padrão */
}

/* Tablet (768px - 1199px) */
@media (max-width: 1199px) {
    /* Cards de período: Grid 1 coluna */
    #comparativo-periodos-content > div:first-child {
        grid-template-columns: 1fr !important;
    }
    
    /* Variações: Grid 1 coluna */
    .variacoes-grid {
        grid-template-columns: 1fr !important;
    }
}

/* Mobile (< 768px) */
@media (max-width: 767px) {
    /* Filtros: Grid 1 coluna */
    .filtros-comparativo {
        grid-template-columns: 1fr !important;
    }
    
    /* Top categorias: Grid 1 coluna */
    .top-categorias-grid {
        grid-template-columns: 1fr !important;
    }
    
    /* Fonte menor */
    .comparativo-card h3 {
        font-size: 16px;
    }
    
    .comparativo-card .valor {
        font-size: 20px;
    }
}
```

### Testes de Responsividade

✅ Desktop 1920x1080: Layout 2 colunas  
✅ Laptop 1366x768: Layout 2 colunas compacto  
✅ Tablet 768x1024: Layout 1 coluna  
✅ Mobile 375x667: Layout 1 coluna + scroll  

---

## 🔧 Troubleshooting

### Problema 1: "Parâmetros obrigatórios não fornecidos"

**Causa:** Anos não selecionados

**Solução:** Verificar se `filter-ano1` e `filter-ano2` têm valores

**Debug:**
```javascript
console.log('Ano 1:', ano1, 'Ano 2:', ano2);
if (!ano1 || !ano2) {
    console.error('Anos obrigatórios!');
}
```

---

### Problema 2: Valores zerados

**Causa:** Período sem transações no banco de dados

**Solução:** 
1. Verificar se há transações cadastradas naquele período
2. Verificar filtro de `empresa_id` (multi-tenant)
3. Checar status das transações (ativas)

**Query de Verificação:**
```sql
SELECT COUNT(*), SUM(valor), tipo
FROM transacoes
WHERE empresa_id = 1
  AND data BETWEEN '2024-01-01' AND '2024-01-31'
GROUP BY tipo;
```

---

### Problema 3: Variação "Infinito" ou "NaN"

**Causa:** Divisão por zero (Período 1 = 0)

**Solução:** Backend já trata com:
```python
variacao = ((p2 - p1) / p1 * 100) if p1 > 0 else 0
```

Se ainda ocorrer no frontend, adicionar:
```javascript
const variacaoSegura = (p1, p2) => {
    if (p1 === 0) return p2 > 0 ? 100 : 0;
    return ((p2 - p1) / p1) * 100;
};
```

---

### Problema 4: Layout quebrado no mobile

**Causa:** Grid com valores fixos

**Solução:** Usar media queries responsivas (já implementadas)

**CSS Correto:**
```css
@media (max-width: 767px) {
    .comparativo-grid {
        grid-template-columns: 1fr !important;
        gap: 15px;
    }
}
```

---

### Problema 5: Exportação não funciona

**Causa:** Bibliotecas não carregadas

**Solução:** Verificar se jsPDF e SheetJS estão incluídos:
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/xlsx/dist/xlsx.full.min.js"></script>
```

---

## 📈 Roadmap Futuro

### Versão 1.1 (Em Breve)
- ✅ Exportação PDF funcional
- ✅ Exportação Excel funcional
- ⬜ Gráficos de linha (evolução temporal)
- ⬜ Gráficos de pizza (distribuição categorias)

### Versão 1.2
- ⬜ Comparação de múltiplos períodos (3+)
- ⬜ Filtros avançados (por categoria, banco, etc.)
- ⬜ Análise de tendências (regressão linear)
- ⬜ Previsões baseadas em períodos anteriores

### Versão 2.0
- ⬜ Dashboard interativo com drill-down
- ⬜ Exportação automática agendada
- ⬜ Alertas de variações significativas
- ⬜ Integração com IA para insights

---

## 📞 Suporte

**Contato:** [Adicionar informações de suporte]  
**Documentação Relacionada:**
- [DOCS_EXTRATO_BANCARIO.md](./DOCS_EXTRATO_BANCARIO.md)
- [DOCUMENTACAO_EXPORTACAO_DADOS.md](./DOCUMENTACAO_EXPORTACAO_DADOS.md)
- [GUIA_PERMISSOES.md](./GUIA_PERMISSOES.md)

---

## 📝 Changelog

### [1.0.0] - 2025-01-XX
- ✅ Implementação inicial do comparativo de períodos
- ✅ Backend completo com API REST
- ✅ Frontend com interface responsiva
- ✅ Cálculo de variações percentuais
- ✅ Ranking top 3 categorias
- ✅ Resumo estatístico
- ⚠️ Exportação PDF/Excel (em desenvolvimento)

---

**Fim da Documentação**
