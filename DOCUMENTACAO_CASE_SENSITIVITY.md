# 📋 Documentação: Case Sensitivity - Backend vs Frontend

## 🐛 Problema Identificado

**Data:** 19/01/2026  
**Severidade:** ⚠️ Média/Alta  
**Status:** ✅ Resolvido

### Descrição do Bug

O sistema apresentava inconsistência entre o formato dos dados retornados pelo **backend** (PostgreSQL) e as comparações realizadas no **frontend** (JavaScript).

#### Backend (PostgreSQL + Python)
```python
# Banco de dados armazena em MINÚSCULO
tipo = 'receita'
status = 'pendente'
```

#### Frontend (JavaScript) - ❌ ANTES
```javascript
// Comparação direta falhava
const isReceita = lanc.tipo === 'RECEITA';  // ❌ FALSO sempre!
const isPendente = lanc.status === 'PENDENTE';  // ❌ FALSO sempre!
```

### Impacto

- ❌ Lançamentos não apareciam nas listagens
- ❌ Filtros por tipo (receita/despesa) não funcionavam
- ❌ Badges de status não exibiam cores corretas
- ❌ Relatórios com dados incorretos

---

## ✅ Solução Implementada

### Padrão Correto: Normalizar com `.toUpperCase()`

```javascript
// ✅ CORRETO - Sempre normalizar antes de comparar
const isReceita = lanc.tipo && lanc.tipo.toUpperCase() === 'RECEITA';
const isPago = lanc.status && lanc.status.toUpperCase() === 'PAGO';
```

### Por que adicionar `&& lanc.tipo` ?

```javascript
// Previne erro se o campo for null/undefined
lanc.tipo && lanc.tipo.toUpperCase() === 'RECEITA'
//         ↑
//         Verifica existência antes
```

---

## 🔍 Locais Corrigidos

### 1. **Contas a Receber** (`app.js` - linha ~1728)
```javascript
// ANTES
const isReceita = lanc.tipo === 'RECEITA';

// DEPOIS
const isReceita = lanc.tipo && lanc.tipo.toUpperCase() === 'RECEITA';
```

### 2. **Contas a Pagar** (`app.js` - linha ~1786)
```javascript
// ANTES
const isDespesa = lanc.tipo === 'DESPESA';

// DEPOIS
const isDespesa = lanc.tipo && lanc.tipo.toUpperCase() === 'DESPESA';
```

### 3. **Status Badges** (`app.js` - linhas ~1742, ~1795)
```javascript
// ANTES
const statusClass = lanc.status === 'PAGO' ? 'badge-success' : 
                   lanc.status === 'VENCIDO' ? 'badge-danger' : 'badge-warning';

// DEPOIS
const statusClass = lanc.status && lanc.status.toUpperCase() === 'PAGO' ? 'badge-success' : 
                   lanc.status && lanc.status.toUpperCase() === 'VENCIDO' ? 'badge-danger' : 'badge-warning';
```

---

## 📊 Commits Relacionados

- `6a92370` - fix: Compare tipo with toUpperCase() to handle lowercase types from backend
- `96d4082` - fix: Make filter elements optional in loadContasReceber and loadContasPagar
- `5bb8836` - fix: Remove num_documento parameter from Lancamento constructor calls
- `0680016` - fix: Add empresa_id field to lancamentos INSERT statements

---

## 🎯 Boas Práticas

### ✅ Sempre Fazer

1. **Normalizar strings antes de comparar:**
```javascript
// ✅ BOM
if (tipo && tipo.toUpperCase() === 'RECEITA') { }

// ❌ RUIM
if (tipo === 'RECEITA') { }
```

2. **Verificar existência do campo:**
```javascript
// ✅ BOM - Previne erro se campo for null
lanc.status && lanc.status.toUpperCase()

// ❌ RUIM - Erro se status for null
lanc.status.toUpperCase()
```

3. **Usar constantes para valores fixos:**
```javascript
// ✅ BOM
const TIPO_RECEITA = 'RECEITA';
const TIPO_DESPESA = 'DESPESA';

if (tipo && tipo.toUpperCase() === TIPO_RECEITA) { }
```

### 🔍 Onde Verificar

1. **Comparações de tipo:**
   - `tipo === 'RECEITA'`
   - `tipo === 'DESPESA'`
   - `tipo === 'TRANSFERENCIA'`

2. **Comparações de status:**
   - `status === 'PENDENTE'`
   - `status === 'PAGO'`
   - `status === 'VENCIDO'`
   - `status === 'CANCELADO'`

3. **Comparações de categoria.tipo:**
   - `cat.tipo === 'receita'`
   - `cat.tipo === 'despesa'`

---

## 🛠️ Como Detectar

### Busca no Código

```bash
# Buscar comparações case-sensitive
grep -rn "=== '[A-Z]" static/
grep -rn '=== "[A-Z]' static/

# Buscar sem normalização
grep -rn "\.tipo ===" static/
grep -rn "\.status ===" static/
```

### Checklist de Revisão

- [ ] Todas comparações com `tipo` usam `.toUpperCase()`
- [ ] Todas comparações com `status` usam `.toUpperCase()`
- [ ] Verificação de `null/undefined` antes de `.toUpperCase()`
- [ ] Filtros e relatórios normalizam strings
- [ ] Testes com dados do backend real

---

## 📝 Arquivos Afetados

```
static/
├── app.js              ✅ Corrigido
├── excel_functions.js  ✅ Já usa .toUpperCase()
├── analise_functions.js ✅ Já usa .toUpperCase()
├── modals.js           ✅ Corrigido
└── contratos.js        ⚠️  Verificar se necessário
```

---

## 🧪 Testes de Validação

### Cenário 1: Lista de Receitas
```
1. Criar receita no banco
2. Verificar se aparece em "Contas a Receber"
3. ✅ Deve listar corretamente
```

### Cenário 2: Status de Lançamento
```
1. Marcar lançamento como PAGO
2. Verificar badge na lista
3. ✅ Badge deve ser verde (badge-success)
```

### Cenário 3: Filtro por Tipo
```
1. Filtrar apenas RECEITAS
2. Verificar lista resultante
3. ✅ Deve mostrar apenas receitas
```

---

## 🚀 Prevenção Futura

### Alternativa 1: Padronizar no Backend
```python
# Retornar sempre em MAIÚSCULO do backend
lancamento = {
    'tipo': tipo.upper(),
    'status': status.upper()
}
```

### Alternativa 2: Usar Enums no Frontend
```javascript
const TipoLancamento = {
    RECEITA: 'RECEITA',
    DESPESA: 'DESPESA',
    TRANSFERENCIA: 'TRANSFERENCIA'
};

const StatusLancamento = {
    PENDENTE: 'PENDENTE',
    PAGO: 'PAGO',
    VENCIDO: 'VENCIDO',
    CANCELADO: 'CANCELADO'
};

// Uso
if (tipo && tipo.toUpperCase() === TipoLancamento.RECEITA) { }
```

### Alternativa 3: Função Helper
```javascript
// Criar helper para comparação case-insensitive
function compareIgnoreCase(str1, str2) {
    if (!str1 || !str2) return false;
    return str1.toUpperCase() === str2.toUpperCase();
}

// Uso
if (compareIgnoreCase(lanc.tipo, 'RECEITA')) { }
```

---

## 📚 Referências

- [MDN: String.prototype.toUpperCase()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/toUpperCase)
- [Operadores de Comparação JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Strict_equality)
- Commit principal: `6a92370`

---

**Última atualização:** 19/01/2026  
**Responsável:** Sistema de Documentação Automática  
**Revisão necessária:** Não
