# Documentação: Padrão de Títulos e Cabeçalhos de Tabelas

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Padrão de Títulos de Seção](#padrão-de-títulos-de-seção)
3. [Padrão de Cabeçalhos de Tabela (th)](#padrão-de-cabeçalhos-de-tabela-th)
4. [Especificações Técnicas](#especificações-técnicas)
5. [Exemplos por Seção](#exemplos-por-seção)
6. [CSS Aplicado](#css-aplicado)
7. [Checklist de Implementação](#checklist-de-implementação)

---

## 🎯 Visão Geral

Este documento define o padrão visual para títulos de seções (H2) e cabeçalhos de tabelas (TH) no sistema financeiro, garantindo consistência, legibilidade e acessibilidade em todos os módulos.

### Princípios de Design

1. **Contraste Máximo**: Texto preto em fundo branco (tema claro)
2. **Hierarquia Clara**: Títulos grandes, cabeçalhos médios
3. **Consistência**: Mesmo estilo em todas as seções
4. **Responsividade**: Adaptável a diferentes tamanhos de tela
5. **Acessibilidade**: Legível para todos os usuários

---

## 📝 Padrão de Títulos de Seção (H2)

### Especificações

| Propriedade | Valor | Descrição |
|-------------|-------|-----------|
| **Cor** | `#000000` | Preto puro |
| **Font-weight** | `700` | Negrito |
| **Font-size** | `24px` (desktop) | Grande e destacado |
| **Margin** | `0 0 20px 0` | Espaçamento inferior |
| **Inline style** | `color: #000000 !important;` | Força cor preta |

### Código HTML

```html
<h2 style="color: #000000 !important; font-weight: 700;">Nome da Seção</h2>
```

### Exemplos de Títulos

```html
<!-- Dashboard -->
<h2 style="color: #000000 !important; font-weight: 700;">📊 Dashboard</h2>

<!-- Contas Bancárias -->
<h2 style="color: #000000 !important; font-weight: 700;">🏦 Contas Bancárias</h2>

<!-- Extrato Bancário -->
<h2 style="color: #000000 !important; font-weight: 700;">🏦 Extrato Bancário - Importação OFX</h2>

<!-- Categorias -->
<h2 style="color: #000000 !important; font-weight: 700;">📁 Categorias</h2>

<!-- Contas a Receber -->
<h2 style="color: #000000 !important; font-weight: 700;">💵 Contas a Receber</h2>

<!-- Contas a Pagar -->
<h2 style="color: #000000 !important; font-weight: 700;">💸 Contas a Pagar</h2>

<!-- Fluxo de Caixa -->
<h2 style="color: #000000 !important; font-weight: 700;">📈 Fluxo de Caixa</h2>
```

### ❌ O que NÃO fazer

```html
<!-- ❌ Sem inline style - pode ficar branco/cinza -->
<h2>Título</h2>

<!-- ❌ Cor diferente de preto -->
<h2 style="color: #666666;">Título</h2>

<!-- ❌ Sem !important - pode ser sobrescrito -->
<h2 style="color: #000000;">Título</h2>
```

---

## 📊 Padrão de Cabeçalhos de Tabela (TH)

### Especificações

| Propriedade | Valor | Descrição |
|-------------|-------|-----------|
| **Cor Texto** | `#000000 !important` | Preto puro |
| **Background** | `#e9ecef !important` | Cinza claro |
| **Font-weight** | `700 !important` | Negrito |
| **Font-size** | `14px` (desktop) | Legível |
| **Padding** | `12px 15px` | Espaçamento interno |
| **Text-align** | `left` | Alinhamento à esquerda |
| **Border** | Definido globalmente | Consistente |

### Código CSS Aplicado

```css
/* CABEÇALHOS DE TABELA - PRETO NO TEMA CLARO */
body:not(.dark-mode) th,
body:not(.dark-mode) .table th,
body:not(.dark-mode) table thead th {
    color: #000000 !important;
    background: #e9ecef !important;
    font-weight: 700 !important;
}
```

### Exemplos de Cabeçalhos por Módulo

#### **Extrato Bancário**
```html
<thead>
    <tr>
        <th>DATA</th>
        <th>DESCRIÇÃO</th>
        <th>VALOR</th>
        <th>TIPO</th>
        <th>SALDO</th>
        <th>CONTA</th>
        <th>STATUS</th>
        <th>AÇÕES</th>
    </tr>
</thead>
```

**Características**:
- Texto em MAIÚSCULAS
- Curtos e objetivos
- Ordem lógica (data → descrição → valores → ações)

#### **Contas Bancárias**
```html
<thead>
    <tr>
        <th>Banco</th>
        <th>Agência</th>
        <th>Conta</th>
        <th>Saldo Inicial</th>
        <th>Saldo Atual</th>
        <th>Ações</th>
    </tr>
</thead>
```

**Características**:
- Primeira letra maiúscula
- Descritivos
- Ações sempre por último

#### **Contas a Receber / Pagar**
```html
<thead>
    <tr>
        <th>Vencimento</th>
        <th>Cliente/Fornecedor</th>
        <th>Descrição</th>
        <th>Valor</th>
        <th>Status</th>
        <th>Ações</th>
    </tr>
</thead>
```

**Características**:
- Data de vencimento prioritária
- Nome do cliente/fornecedor em destaque
- Status para filtro visual

#### **Categorias**
```html
<thead>
    <tr>
        <th>Nome</th>
        <th>Tipo</th>
        <th>Subcategorias</th>
        <th>Ações</th>
    </tr>
</thead>
```

**Características**:
- Simples e direto
- Tipo (Receita/Despesa) claramente identificado

#### **Fluxo de Caixa**
```html
<thead>
    <tr>
        <th>Período</th>
        <th>Receitas</th>
        <th>Despesas</th>
        <th>Saldo</th>
        <th>Variação</th>
    </tr>
</thead>
```

**Características**:
- Foco em valores financeiros
- Colunas numéricas alinhadas

---

## 🔧 Especificações Técnicas

### Hierarquia Visual

```
┌─────────────────────────────────────────────────────────┐
│ H2 - Título da Seção (24px, peso 700, preto)           │
├─────────────────────────────────────────────────────────┤
│ Subtítulo ou descrição (16px, peso 400, preto)         │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ TH - Cabeçalho (14px, peso 700, preto, fundo cinza)│ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ TD - Células (14px, peso 500, preto/cores)         │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Responsividade

| Breakpoint | H2 Font-size | TH Font-size | TH Padding |
|------------|--------------|--------------|------------|
| Desktop (>992px) | 24px | 14px | 12px 15px |
| Tablet (768-992px) | 22px | 13px | 10px 12px |
| Mobile (480-768px) | 20px | 12px | 10px 10px |
| Mobile Small (<480px) | 18px | 11px | 8px 8px |

### Código CSS Responsivo

```css
/* Desktop (padrão) */
body:not(.dark-mode) h2 {
    color: #000000 !important;
    font-weight: 700 !important;
    font-size: 24px;
}

/* Tablet */
@media (max-width: 992px) {
    body:not(.dark-mode) h2 {
        font-size: 22px;
    }
    
    body:not(.dark-mode) th {
        font-size: 13px;
        padding: 10px 12px;
    }
}

/* Mobile */
@media (max-width: 768px) {
    body:not(.dark-mode) h2 {
        font-size: 20px;
    }
    
    body:not(.dark-mode) th {
        font-size: 12px;
        padding: 10px 10px;
    }
}

/* Mobile Small */
@media (max-width: 480px) {
    body:not(.dark-mode) h2 {
        font-size: 18px;
    }
    
    body:not(.dark-mode) th {
        font-size: 11px;
        padding: 8px 8px;
    }
}
```

---

## 📐 Exemplos por Seção

### 1. Dashboard

```html
<div id="dashboard-section" class="content-card">
    <h2 style="color: #000000 !important; font-weight: 700;">📊 Dashboard</h2>
    <!-- Cards de resumo -->
    <div class="cards-grid">
        <!-- Conteúdo -->
    </div>
</div>
```

### 2. Contas Bancárias

```html
<div id="contas-bancarias-section" class="content-card hidden">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h2 style="color: #000000 !important; font-weight: 700; margin: 0;">🏦 Contas Bancárias</h2>
        <div class="saldo-total-card">
            💰 SALDO TOTAL: R$ 72.600,00
        </div>
    </div>
    
    <button class="btn btn-primary">➕ Nova Conta</button>
    
    <div class="table-scroll-container">
        <table id="table-contas">
            <thead>
                <tr>
                    <th>Banco</th>
                    <th>Agência</th>
                    <th>Conta</th>
                    <th>Saldo Inicial</th>
                    <th>Saldo Atual</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                <!-- Dados -->
            </tbody>
        </table>
    </div>
</div>
```

### 3. Extrato Bancário

```html
<div id="extrato-bancario-section" class="content-card hidden">
    <h2 style="color: #000000 !important; font-weight: 700;">
        🏦 Extrato Bancário - Importação OFX
    </h2>
    
    <!-- Filtros -->
    <div class="filtros-container">
        <!-- Campos de filtro -->
    </div>
    
    <table class="table table-hover">
        <thead>
            <tr>
                <th>DATA</th>
                <th>DESCRIÇÃO</th>
                <th>VALOR</th>
                <th>TIPO</th>
                <th>SALDO</th>
                <th>CONTA</th>
                <th>STATUS</th>
                <th>AÇÕES</th>
            </tr>
        </thead>
        <tbody id="tbody-extratos">
            <!-- Transações -->
        </tbody>
    </table>
</div>
```

### 4. Categorias (Com Abas)

```html
<div id="categorias-section" class="content-card hidden">
    <h2 style="color: #000000 !important; font-weight: 700;">📁 Categorias</h2>
    
    <button class="btn btn-primary">➕ Nova Categoria</button>
    
    <!-- Abas -->
    <div class="tabs-container">
        <button class="tab-button active">💰 Receitas</button>
        <button class="tab-button">💸 Despesas</button>
    </div>
    
    <!-- Tabela de Receitas -->
    <div id="categorias-receita-container">
        <table id="table-categorias-receita">
            <thead>
                <tr>
                    <th>Nome</th>
                    <th>Subcategorias</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                <!-- Dados -->
            </tbody>
        </table>
    </div>
</div>
```

### 5. Folha de Pagamento - Funcionários

```html
<div id="folha-pagamento-section" class="content-card hidden">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2 style="color: #000000 !important; font-weight: 700;">👥 Folha de Pagamento - Funcionários</h2>
        <button onclick="abrirModalFuncionario()" class="btn btn-primary" style="padding: 10px 20px; background: #3498db;">
            ➕ Novo Funcionário
        </button>
    </div>

    <!-- Tabela de Funcionários -->
    <div class="table-container">
        <table>
            <thead>
                <tr style="background-color: #f5f5f5 !important;">
                    <th style="color: #000000 !important; font-weight: 700; padding: 12px 15px; text-align: left; width: 250px;">Nome</th>
                    <th style="color: #000000 !important; font-weight: 700; padding: 12px 15px; text-align: left; width: 130px;">CPF</th>
                    <th style="color: #000000 !important; font-weight: 700; padding: 12px 15px; text-align: left; width: 250px;">Endereço</th>
                    <th style="color: #000000 !important; font-weight: 700; padding: 12px 15px; text-align: left; width: 120px;">Tipo Chave PIX</th>
                    <th style="color: #000000 !important; font-weight: 700; padding: 12px 15px; text-align: left; width: 200px;">Chave PIX</th>
                    <th style="color: #000000 !important; font-weight: 700; padding: 12px 15px; text-align: left; width: 100px;">Status</th>
                    <th style="color: #000000 !important; font-weight: 700; padding: 12px 15px; text-align: center; width: 150px;">Ações</th>
                </tr>
            </thead>
            <tbody id="tbody-funcionarios">
                <tr><td colspan="7" class="loading">Carregando...</td></tr>
            </tbody>
        </table>
    </div>
</div>
```

**Características desta seção:**
- ✅ Título com padrão preto e negrito
- ✅ Botão de ação alinhado à direita
- ✅ Cabeçalhos da tabela com `background-color: #f5f5f5`
- ✅ Cada `<th>` com `color: #000000 !important; font-weight: 700`
- ✅ Larguras fixas para manter consistência visual
- ✅ Text-align apropriado (left para dados, center para ações)

---

## 🎨 CSS Aplicado

### Regras Globais para H2

```css
/* ============================================================================
   TÍTULOS H2 - TEXTO PRETO NO TEMA CLARO
   ============================================================================ */

body:not(.dark-mode) h2 {
    color: #000000 !important;
    font-weight: 700 !important;
    margin-bottom: 20px;
}

body:not(.dark-mode) h1,
body:not(.dark-mode) h2, 
body:not(.dark-mode) h3,
body:not(.dark-mode) h4,
body:not(.dark-mode) h5,
body:not(.dark-mode) h6 {
    color: #000000 !important;
    font-weight: 700 !important;
}
```

### Regras Globais para TH

```css
/* ============================================================================
   CABEÇALHOS DE TABELA (TH) - PRETO NO TEMA CLARO
   ============================================================================ */

body:not(.dark-mode) th,
body:not(.dark-mode) .table th,
body:not(.dark-mode) table thead th {
    color: #000000 !important;
    background: #e9ecef !important;
    font-weight: 700 !important;
    padding: 12px 15px;
    text-align: left;
    border-bottom: 2px solid #dee2e6;
}

/* Hover em cabeçalhos (se sortable) */
body:not(.dark-mode) th:hover {
    background: #dee2e6 !important;
    cursor: pointer;
}
```

### Inline Styles nos H2 (Reforço)

```css
/* Inline styles sempre têm prioridade */
style="color: #000000 !important; font-weight: 700;"
```

**Por que usar inline?**
- Garante que nenhuma outra regra CSS sobrescreva
- !important inline vence qualquer CSS externo
- Mesmo com lazy loading ou carregamento tardio, funciona
- Não depende de ordem de carregamento de arquivos CSS

---

## ✅ Checklist de Implementação

### Para Adicionar Novo H2

- [ ] Adicionar inline style: `style="color: #000000 !important; font-weight: 700;"`
- [ ] Usar emoji apropriado no início (opcional mas recomendado)
- [ ] Verificar se CSS global está aplicado
- [ ] Testar em tema claro e escuro
- [ ] Verificar responsividade (mobile/tablet/desktop)

### Para Adicionar Nova Tabela

- [ ] Estrutura básica com `<thead>` e `<tbody>`
- [ ] Usar nomes descritivos nos `<th>`
- [ ] Coluna "Ações" sempre por último
- [ ] Verificar se CSS global `th` está aplicado
- [ ] Adicionar classes `.table` se necessário
- [ ] Envolver em `.table-scroll-container` para mobile
- [ ] Testar scroll horizontal em mobile

### Verificação de Qualidade

- [ ] **Contraste**: Texto preto em fundo branco/cinza claro
- [ ] **Legibilidade**: Fonte grande o suficiente (min 11px mobile)
- [ ] **Hierarquia**: H2 > TH > TD em tamanho e peso
- [ ] **Consistência**: Mesmo estilo em todas as seções
- [ ] **Acessibilidade**: Testado com ferramentas de acessibilidade
- [ ] **Responsividade**: Funciona em mobile, tablet e desktop

---

## 🎯 Regras de Ouro

### 1. **SEMPRE use inline style nos H2**
```html
✅ <h2 style="color: #000000 !important; font-weight: 700;">Título</h2>
❌ <h2>Título</h2>
```

### 2. **NUNCA remova !important**
```css
✅ color: #000000 !important;
❌ color: #000000;
```

### 3. **Backgrounds de TH sempre cinza claro**
```css
✅ background: #e9ecef !important;
❌ background: #ffffff;
❌ background: transparent;
```

### 4. **Ordem das colunas: Lógica → Ações**
```html
✅ <th>Data</th><th>Descrição</th><th>Valor</th><th>Ações</th>
❌ <th>Ações</th><th>Data</th><th>Valor</th>
```

### 5. **TH sempre em negrito (700)**
```css
✅ font-weight: 700 !important;
❌ font-weight: 400;
❌ font-weight: normal;
```

---

## 📱 Exemplos de Responsividade

### Desktop (>992px)
```
┌────────────────────────────────────────────────────┐
│ 📊 Dashboard (24px, peso 700)                      │
├────────────────────────────────────────────────────┤
│ Filtros │ Botões │ Saldo Total                     │
├────┬─────┬─────┬─────┬─────┬─────┬─────┬──────────┤
│DATA│DESC │VALOR│TIPO │SALDO│CONTA│STATU│AÇÕES     │
├────┼─────┼─────┼─────┼─────┼─────┼─────┼──────────┤
│    │     │     │     │     │     │     │ Btn Btn  │
└────┴─────┴─────┴─────┴─────┴─────┴─────┴──────────┘
```

### Mobile (<768px)
```
┌─────────────────────────┐
│ 📊 Dashboard (20px)     │
├─────────────────────────┤
│ Filtros (empilhados)    │
│ Botões (largura total)  │
│ Saldo (largura total)   │
├─────────────────────────┤
│ ← Scroll Horizontal →   │
├───┬───┬───┬───┬───┬─────┤
│DA │DE │VA │TI │SA │AÇÕE │
├───┼───┼───┼───┼───┼─────┤
│   │   │   │   │   │ Btn │
└───┴───┴───┴───┴───┴─────┘
```

---

## 🔍 Troubleshooting

### Problema: Título aparece branco ou cinza

**Causa**: Falta inline style ou !important
**Solução**:
```html
<h2 style="color: #000000 !important; font-weight: 700;">Título</h2>
```

### Problema: Cabeçalho (TH) com fundo branco

**Causa**: CSS global não aplicado
**Solução**: Verificar se regra CSS existe em `style.css`:
```css
body:not(.dark-mode) th {
    background: #e9ecef !important;
}
```

### Problema: Tabela não tem scroll em mobile

**Causa**: Falta `.table-scroll-container`
**Solução**:
```html
<div class="table-scroll-container">
    <table>...</table>
</div>
```

### Problema: Texto muito pequeno em mobile

**Causa**: Falta media query responsiva
**Solução**: Adicionar em `style.css`:
```css
@media (max-width: 768px) {
    th { font-size: 12px; }
}
```

---

## 📊 Métricas de Qualidade

### Contraste (WCAG)
- **H2**: Preto (#000000) em branco → Ratio 21:1 ✅ AAA
- **TH**: Preto (#000000) em cinza (#e9ecef) → Ratio 15:1 ✅ AAA

### Tamanhos Mínimos
- **H2**: 18px (mobile small) ✅
- **TH**: 11px (mobile small) ✅ (mínimo recomendado: 11px)

### Performance
- Inline styles: Carregamento imediato ✅
- CSS global: Cache do navegador ✅
- Sem imagens: Renderização rápida ✅

---

## 🎓 Boas Práticas

1. **Consistência é chave**: Use sempre o mesmo padrão
2. **Semântica HTML**: H2 para títulos de seção, TH para cabeçalhos
3. **Acessibilidade**: Alto contraste e fontes legíveis
4. **Performance**: Inline styles para elementos críticos
5. **Manutenibilidade**: Documente desvios do padrão
6. **Testabilidade**: Teste em múltiplos dispositivos
7. **Escalabilidade**: Padrão fácil de replicar em novas seções

---

## 📝 Convenções de Nomenclatura

### Títulos de Seção
```
📊 Dashboard
🏦 Contas Bancárias
🏦 Extrato Bancário
📁 Categorias
👥 Clientes
💵 Contas a Receber
💸 Contas a Pagar
📈 Fluxo de Caixa
📊 Relatórios
⚙️ Configurações
```

### Cabeçalhos de Tabela

**Datas**: DATA, Vencimento, Criado em, Atualizado em
**Identificação**: Banco, Cliente, Fornecedor, Categoria
**Valores**: VALOR, Saldo Inicial, Saldo Atual, Total
**Status**: STATUS, Situação, Estado
**Ações**: AÇÕES (sempre plural, sempre maiúsculo)

---

## 🔗 Referências

- [MDN: Heading Elements](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/Heading_Elements)
- [WCAG 2.1 Contrast Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [CSS Specificity Calculator](https://specificity.keegan.st/)
- [Responsive Typography](https://web.dev/responsive-web-design-basics/)

---

## 📅 Histórico de Versões

| Versão | Data | Alterações |
|--------|------|------------|
| 1.0 | 26/01/2026 | Documento inicial criado |

---

**Última Atualização**: 26/01/2026
**Autor**: Sistema Financeiro DWM Team
**Status**: ✅ Padrão Oficial
