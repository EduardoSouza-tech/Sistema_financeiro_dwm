# 📊 Documentação - Dashboard Financeiro

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Estrutura Visual](#estrutura-visual)
3. [Filtros e Períodos](#filtros-e-períodos)
4. [Cards de Indicadores](#cards-de-indicadores)
5. [Gráfico de Evolução](#gráfico-de-evolução)
6. [API e Backend](#api-e-backend)
7. [Como Usar](#como-usar)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O **Dashboard Financeiro** é a tela inicial do sistema que oferece uma visão consolidada e visual da saúde financeira da empresa.

### Objetivo Principal:
Fornecer uma visão rápida e clara da situação financeira através de:
- 📊 Gráfico de evolução de receitas e despesas
- 💰 Cards com valores de contas pendentes
- 📈 Comparação visual entre entradas e saídas
- 🔍 Filtros flexíveis por período

---

## 🎨 Estrutura Visual

### Layout Responsivo

```
┌─────────────────────────────────────────────────┐
│  📊 Dashboard Financeiro                        │
├─────────────────────────────────────────────────┤
│  🔍 FILTROS                                     │
│  [📅 Ano] [📆 Mês] [🔍 Atualizar]              │
├─────────────────────────────────────────────────┤
│  📈 GRÁFICO DE EVOLUÇÃO                         │
│  ┌───────────────────────────────────────────┐ │
│  │     Receitas vs Despesas (12 meses)       │ │
│  │                                            │ │
│  │     [Gráfico de Linhas Chart.js]         │ │
│  └───────────────────────────────────────────┘ │
├─────────────────────────────────────────────────┤
│  💰 CARDS DE INDICADORES                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────┐│
│  │ 💵      │ │ 💸      │ │ ⚠️      │ │ 💰   ││
│  │ Contas  │ │ Contas  │ │ Contas  │ │ Saldo││
│  │ Receber │ │ Pagar   │ │ Vencidas│ │ Total││
│  │R$ X,XX  │ │R$ X,XX  │ │R$ X,XX  │ │R$ X  ││
│  └─────────┘ └─────────┘ └─────────┘ └──────┘│
└─────────────────────────────────────────────────┘
```

### Cores e Estilo

**Paleta de Cores:**
- 🟢 Verde (#27ae60): Receitas / Contas a Receber
- 🔴 Vermelho (#e74c3c): Despesas / Contas a Pagar
- 🟠 Laranja (#f39c12): Contas Vencidas (alerta)
- 🔵 Azul (#3498db): Saldo Total
- 🟣 Roxo (gradiente): Área de filtros

**Gradientes:**
- Filtros: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- Cards: Gradientes suaves com cores correspondentes

---

## 🔍 Filtros e Períodos

### Comportamento Padrão

**Ao abrir o Dashboard:**
- ✅ Campos de filtro **vazios**
- ✅ Mostra automaticamente os **últimos 12 meses**
- ✅ Placeholder: "Últimos 12 meses"

### Opções de Filtro

#### 1. **Últimos 12 Meses** (Padrão)
```
Ano: [vazio]
Mês: Últimos 12 meses
```
- Mostra evolução dos últimos 12 meses
- Ideal para ver tendências
- Melhor visão panorâmica

#### 2. **Ano Específico**
```
Ano: 2025
Mês: Últimos 12 meses
```
- Mostra todos os 12 meses do ano selecionado
- Janeiro a Dezembro do ano escolhido
- Útil para análise anual

#### 3. **Mês Específico**
```
Ano: 2025
Mês: Janeiro
```
- Mostra apenas o mês selecionado
- Análise detalhada de um período curto
- Cards refletem apenas aquele mês

### Como Funciona

**Lógica de Filtros:**
```javascript
if (ano && mes) {
    // Mostra apenas aquele mês específico
    // Ex: Janeiro/2025
} else if (ano) {
    // Mostra todos os meses daquele ano
    // Ex: Jan-Dez/2025
} else {
    // Mostra últimos 12 meses
    // Ex: Fev/2025 a Jan/2026
}
```

**Recarregar Dados:**
- Sempre clique no botão **"🔍 Atualizar"** após alterar filtros
- Os dados são carregados sob demanda
- Previne requisições desnecessárias

---

## 💰 Cards de Indicadores

### 1. Contas a Receber 💵

**Cor:** Verde (`#27ae60`)

**O que mostra:**
- Soma de todas as **RECEITAS PENDENTES**
- Lançamentos com `status = PENDENTE`
- Lançamentos do tipo `RECEITA`

**Exemplo:**
```
💵 Contas a Receber
R$ 15.450,00
```

**Uso:**
- Dinheiro que você **vai receber**
- Clientes que ainda não pagaram
- Entradas futuras confirmadas

---

### 2. Contas a Pagar 💸

**Cor:** Vermelho (`#e74c3c`)

**O que mostra:**
- Soma de todas as **DESPESAS PENDENTES**
- Lançamentos com `status = PENDENTE`
- Lançamentos do tipo `DESPESA`

**Exemplo:**
```
💸 Contas a Pagar
R$ 8.720,00
```

**Uso:**
- Dinheiro que você **precisa pagar**
- Fornecedores aguardando pagamento
- Saídas futuras confirmadas

---

### 3. Contas Vencidas ⚠️

**Cor:** Laranja (`#f39c12`)

**O que mostra:**
- Soma de lançamentos **PENDENTES** com data de vencimento **no passado**
- Inclui receitas e despesas vencidas
- `data_vencimento < data_hoje`

**Exemplo:**
```
⚠️ Contas Vencidas
R$ 2.300,00
```

**Uso:**
- **ALERTA!** Pagamentos atrasados
- Cobranças não recebidas
- Requer ação imediata

---

### 4. Saldo Total 💰

**Cor:** Azul (`#3498db`)

**O que mostra:**
```
Saldo Total = 
  Saldo Inicial das Contas Bancárias
  + Receitas PAGAS
  - Despesas PAGAS
```

**Exemplo:**
```
💰 Saldo Total
R$ 113.600,00
```

**Uso:**
- Situação financeira atual
- Dinheiro disponível + em contas
- Baseado em movimentações **confirmadas** (PAGAS)

**⚠️ Importante:**
- **NÃO** inclui lançamentos pendentes
- Apenas lançamentos com `status = PAGO`
- Transferências são ignoradas (não contam duas vezes)

---

## 📈 Gráfico de Evolução

### Tipo de Gráfico

**Chart.js - Line Chart** (Gráfico de Linhas)

**Características:**
- 📈 Duas linhas: Receitas (verde) e Despesas (vermelho)
- 🎯 Eixo X: Meses (ex: "Jan/2025")
- 💰 Eixo Y: Valores em R$
- 🖱️ Hover: Tooltip mostra valores formatados
- 📊 Área preenchida com transparência

### O que Mostra

**Apenas Lançamentos PAGOS:**
```sql
WHERE status = 'PAGO' 
  AND data_pagamento BETWEEN data_inicio AND data_fim
  AND tipo != 'TRANSFERENCIA'
```

**Por que apenas PAGOS?**
- Mostra realidade financeira **efetiva**
- Não inclui promessas (pendentes)
- Evolução baseada em **fatos** (pagamentos confirmados)

### Interpretação do Gráfico

#### ✅ Situação Saudável
```
Receitas (verde) ──────── acima
                           
Despesas (vermelho) ────── abaixo
```
- Receitas maiores que despesas
- Empresa lucrativa
- Crescimento sustentável

#### ⚠️ Situação de Alerta
```
Receitas (verde) ──────── 
                           se cruzam
Despesas (vermelho) ──────
```
- Receitas e despesas equilibradas
- Margens apertadas
- Requer monitoramento

#### ❌ Situação Crítica
```
Receitas (verde) ──────── abaixo
                           
Despesas (vermelho) ────── acima
```
- Despesas maiores que receitas
- Prejuízo operacional
- Ação corretiva urgente

### Exemplos de Análise

**Crescimento:**
```
Jan  Fev  Mar  Abr  Mai
 ↗    ↗    ↗    ↗    ↗   Receitas subindo
 →    →    →    →    →   Despesas estáveis
= Ótimo! Crescimento com eficiência
```

**Alerta:**
```
Jan  Fev  Mar  Abr  Mai
 →    →    →    →    →   Receitas estagnadas
 ↗    ↗    ↗    ↗    ↗   Despesas subindo
= Perigo! Margem diminuindo
```

---

## 🔌 API e Backend

### Endpoint Principal

**GET** `/api/relatorios/dashboard`

**Permissão Necessária:** `lancamentos_view`

**Query Parameters:**
```
?ano=2025         (opcional - número)
?mes=1            (opcional - 1 a 12)
```

### Response Body

```json
{
  "saldo_total": 113600.00,
  "contas_receber": 15450.00,
  "contas_pagar": 8720.00,
  "contas_vencidas": 2300.00,
  "total_contas": 5,
  "total_lancamentos": 342,
  "meses": [
    "Fev/2025",
    "Mar/2025",
    "Abr/2025",
    "Mai/2025",
    "Jun/2025",
    "Jul/2025",
    "Ago/2025",
    "Set/2025",
    "Out/2025",
    "Nov/2025",
    "Dez/2025",
    "Jan/2026"
  ],
  "receitas": [
    12000.00,
    15000.00,
    18000.00,
    16000.00,
    19000.00,
    21000.00,
    20000.00,
    22000.00,
    24000.00,
    23000.00,
    25000.00,
    27000.00
  ],
  "despesas": [
    8000.00,
    9000.00,
    10000.00,
    9500.00,
    11000.00,
    12000.00,
    11500.00,
    13000.00,
    14000.00,
    13500.00,
    15000.00,
    16000.00
  ]
}
```

### Cálculos no Backend

#### 1. Saldo Total
```python
saldo_total = Decimal('0')

# Saldo inicial das contas
for conta in contas:
    saldo_total += Decimal(str(conta.saldo_inicial))

# Adicionar receitas pagas
for lanc in lancamentos:
    if lanc.status == StatusLancamento.PAGO:
        if lanc.tipo == TipoLancamento.RECEITA:
            saldo_total += Decimal(str(lanc.valor))
        elif lanc.tipo == TipoLancamento.DESPESA:
            saldo_total -= Decimal(str(lanc.valor))
```

#### 2. Contas Pendentes
```python
contas_receber = sum(
    l.valor for l in lancamentos 
    if l.tipo == TipoLancamento.RECEITA 
    and l.status == StatusLancamento.PENDENTE
)

contas_pagar = sum(
    l.valor for l in lancamentos 
    if l.tipo == TipoLancamento.DESPESA 
    and l.status == StatusLancamento.PENDENTE
)
```

#### 3. Contas Vencidas
```python
hoje = date.today()
contas_vencidas = sum(
    l.valor for l in lancamentos 
    if l.status == StatusLancamento.PENDENTE 
    and l.data_vencimento < hoje
)
```

#### 4. Dados do Gráfico
```python
# Para cada mês no período:
for mes in range(12):
    # Filtrar lançamentos PAGOS do mês
    lancamentos_mes = [
        l for l in lancamentos
        if l.status == StatusLancamento.PAGO
        and l.data_pagamento in periodo_mes
        and l.tipo != TipoLancamento.TRANSFERENCIA
    ]
    
    # Somar receitas e despesas
    receitas_mes = sum(l.valor for l in lancamentos_mes if l.tipo == RECEITA)
    despesas_mes = sum(l.valor for l in lancamentos_mes if l.tipo == DESPESA)
    
    meses.append(mes_formatado)
    receitas.append(float(receitas_mes))
    despesas.append(float(despesas_mes))
```

---

## 📖 Como Usar

### Acesso Inicial

1. **Login no sistema**
2. Dashboard é a **primeira tela** exibida
3. Dados carregam automaticamente em 1 segundo

### Visualização Padrão

**Ao abrir:**
```
✅ Últimos 12 meses carregados
✅ Cards mostram valores pendentes atuais
✅ Gráfico mostra evolução mensal
✅ Saldo total calculado
```

### Filtrar por Ano

**Exemplo: Ver 2025 completo**

1. Digite `2025` no campo **📅 Ano**
2. Deixe **📆 Mês** em "Últimos 12 meses"
3. Clique em **🔍 Atualizar**

**Resultado:**
- Gráfico: Janeiro a Dezembro de 2025
- Cards: Todos os pendentes de 2025

### Filtrar por Mês

**Exemplo: Ver apenas Janeiro/2025**

1. Digite `2025` no campo **📅 Ano**
2. Selecione `Janeiro` no campo **📆 Mês**
3. Clique em **🔍 Atualizar**

**Resultado:**
- Gráfico: Apenas Janeiro/2025 (1 ponto)
- Cards: Pendentes daquele mês

### Voltar para Últimos 12 Meses

1. **Limpe** o campo **📅 Ano** (delete)
2. Selecione `Últimos 12 meses` no **📆 Mês**
3. Clique em **🔍 Atualizar**

**Resultado:**
- Voltou ao padrão
- Últimos 12 meses visíveis

---

## 🐛 Troubleshooting

### Problema: Gráfico aparece zerado

**Causas possíveis:**

1. **Nenhum lançamento PAGO no período**
   ```
   Solução: Pague alguns lançamentos em Contas a Pagar/Receber
   ```

2. **Filtro muito restritivo**
   ```
   Solução: Mude para "Últimos 12 meses"
   ```

3. **Empresa sem lançamentos**
   ```
   Solução: Crie lançamentos primeiro
   ```

---

### Problema: Cards mostram R$ 0,00

**Causas possíveis:**

1. **Nenhum lançamento PENDENTE**
   ```
   ✅ Normal! Significa que tudo foi pago
   ```

2. **Filtro de período ativo**
   ```
   Cards sempre mostram TODOS os pendentes, não filtram por período
   ```

3. **Usuário sem permissão**
   ```
   Verifique permissão lancamentos_view
   ```

---

### Problema: "Erro ao carregar dashboard"

**Diagnóstico:**

1. **Abra o Console do navegador** (F12)
2. Veja a aba **Console** e **Network**
3. Procure por erros em vermelho

**Erros comuns:**

```
❌ 403 Forbidden
→ Usuário sem permissão lancamentos_view

❌ 500 Internal Server Error
→ Erro no backend (veja logs do Railway)

❌ TypeError: Cannot read property...
→ Erro no JavaScript (reporte ao dev)
```

---

### Problema: Gráfico não atualiza após filtro

**Solução:**
1. Verifique se clicou em **🔍 Atualizar**
2. Abra Console (F12) e veja se há erros
3. Recarregue a página (F5)

---

### Problema: Saldo Total não bate com expectativa

**Verifique:**

1. **Saldo inicial das contas** em Cadastros → Contas Bancárias
   ```
   Saldo Total começa com soma dos saldos iniciais
   ```

2. **Apenas lançamentos PAGOS contam**
   ```
   Pendentes NÃO afetam saldo total
   ```

3. **Transferências são ignoradas**
   ```
   Transferências entre contas não alteram saldo total
   ```

**Fórmula:**
```
Saldo Total = 
  Σ Saldos Iniciais das Contas
  + Σ Receitas PAGAS
  - Σ Despesas PAGAS
```

---

## 📊 Logs de Debug

O sistema gera logs detalhados:

```javascript
📊 Carregando Dashboard...
📅 Filtros: ano=undefined, mes=undefined
📋 Total de lançamentos: 342
🏦 Total de contas: 5
📊 DADOS DO GRÁFICO:
   Meses: ["Fev/2025", "Mar/2025", ...]
   Receitas: [12000, 15000, 18000, ...]
   Despesas: [8000, 9000, 10000, ...]
💰 CARDS:
   Contas a Receber: R$ 15.450,00
   Contas a Pagar: R$ 8.720,00
   Contas Vencidas: R$ 2.300,00
   Saldo Total: R$ 113.600,00
```

**Como ver:**
1. Abra Console (F12)
2. Vá para aba **Console**
3. Filtre por "Dashboard" ou "📊"

---

## 🎯 Melhores Práticas

### ✅ DO (Faça)

1. **Use filtros para análises específicas**
   - Comparar ano a ano
   - Analisar meses sazonais
   - Identificar tendências

2. **Acompanhe contas vencidas**
   - Card laranja é alerta importante
   - Priorize recebimento/pagamento

3. **Monitore a evolução do gráfico**
   - Linha verde crescendo = bom
   - Linha vermelha crescendo = alerta
   - Distância entre linhas = margem

4. **Atualize após mudanças**
   - Pagou lançamento? Recarregue dashboard
   - Criou novo lançamento? Recarregue dashboard

### ❌ DON'T (Não Faça)

1. **Não confunda saldo com receitas/despesas**
   - Saldo = situação atual (PAGOS)
   - Cards = situação futura (PENDENTES)

2. **Não ignore o gráfico**
   - Ele mostra tendências que cards não mostram

3. **Não use filtros muito restritos**
   - 1 mês pode não dar contexto suficiente

---

## 📝 Changelog

### Versão 2.0 (23/01/2026)
- ✨ **NOVO**: Últimos 12 meses como padrão
- ✨ **NOVO**: Placeholder "Últimos 12 meses"
- 🐛 **FIX**: Rota `/api/relatorios/dashboard` criada (estava faltando)
- 🐛 **FIX**: Filtros vazios por padrão
- 📚 Documentação completa criada

### Versão 1.0 (02/11/2024)
- ✨ Lançamento inicial
- ✨ Cards de indicadores
- ✨ Gráfico Chart.js
- ✨ Filtros de ano/mês

---

## 🤝 Suporte

Dúvidas ou problemas? Entre em contato com a equipe de desenvolvimento.

**Dashboard desenvolvido com ❤️ para facilitar sua gestão financeira!**
