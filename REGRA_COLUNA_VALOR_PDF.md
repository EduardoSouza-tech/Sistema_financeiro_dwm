# ⚠️ REGRA CRÍTICA: Coluna "Valor (R$)" em Exportações

## 📋 REGRA OBRIGATÓRIA

### 🚫 PDF - NUNCA mostre "Valor (R$)"
### ✅ Excel - SEMPRE mostre "Valor (R$)"

---

## 📍 Locais Afetados

### 1. 👥 Alocar Equipe no Evento

**Arquivo:** `templates/interface_nova.html`

#### ✍️ Aba "Assinatura" (📄 PDF)
- **Função:** `exportarAssinaturaPDF()` (linha ~7523)
- **❌ NÃO DEVE TER:** Coluna "Valor (R$)"
- **✅ Colunas corretas:** 
  - #
  - Funcionário
  - Função
  - Setor
  - Assinatura

```javascript
// ⚠️ IMPORTANTE: PDF NÃO TEM COLUNA "VALOR (R$)"
head: [['#', 'Funcionário', 'Função', 'Setor', 'Assinatura']]
```

#### ✍️ Aba "Assinatura" (📊 Excel)
- **Função:** `exportarAssinaturaExcel()` (linha ~7630)
- **✅ DEVE TER:** Coluna "Valor (R$)"
- **Colunas corretas:**
  - #
  - Funcionário
  - Função
  - Setor
  - **Valor (R$)** ← OBRIGATÓRIO no Excel!

```javascript
// ✅ IMPORTANTE: Excel DEVE TER coluna "Valor (R$)"
dados.push(['#', 'Funcionário', 'Função', 'Setor', 'Valor (R$)']);
```

#### 👁️ Preview Visual (Tabela HTML)
- **Elemento:** `tbody-assinatura-evento` (linha ~2785)
- **❌ NÃO MOSTRE:** Coluna "Valor (R$)" na tabela de preview
- **Motivo:** Preview deve refletir o que será exportado no PDF
- **Colunas corretas:**
  - #
  - Funcionário
  - Função
  - Setor
  - Assinatura

---

## 🎯 Motivo da Regra

**Sigilo Financeiro:**
- O PDF de assinatura é usado para **coleta de assinaturas** dos funcionários
- Não deve expor valores individuais de pagamento
- Apenas confirma presença e função no evento

**Controle Financeiro:**
- O Excel é usado internamente para **controle administrativo**
- Contém informações financeiras completas
- Usado para conferência de pagamentos

---

## 🔍 Como Identificar

### Em código JavaScript:
```javascript
// ❌ ERRADO para PDF
head: [['#', 'Funcionário', 'Função', 'Setor', 'Valor (R$)', 'Assinatura']]

// ✅ CORRETO para PDF
head: [['#', 'Funcionário', 'Função', 'Setor', 'Assinatura']]

// ✅ CORRETO para Excel
dados.push(['#', 'Funcionário', 'Função', 'Setor', 'Valor (R$)']);
```

### Em tabelas HTML:
```html
<!-- ❌ ERRADO para preview de assinatura -->
<th>Valor (R$)</th>

<!-- ✅ CORRETO para tabela de equipe alocada -->
<table id="tbody-equipe-evento">
  <th>Valor</th> <!-- Só aparece na aba Individual -->
</table>

<!-- ✅ CORRETO para preview de assinatura -->
<table id="tbody-assinatura-evento">
  <!-- NÃO tem coluna Valor -->
</table>
```

---

## 📝 Comentários Obrigatórios no Código

Sempre adicione comentários explícitos onde a regra se aplica:

```javascript
// ⚠️ IMPORTANTE: PDF NÃO DEVE TER COLUNA "VALOR (R$)" - Apenas Excel deve ter!
// ✅ IMPORTANTE: Excel DEVE TER coluna "Valor (R$)" - Apenas PDF não tem!
// ⚠️ REMOVIDA coluna Valor (R$) - Só no Excel!
```

---

## ✅ Checklist de Implementação

Quando trabalhar com exportações de equipe/assinatura:

- [ ] Verificar se é exportação PDF → **REMOVER** coluna Valor
- [ ] Verificar se é exportação Excel → **MANTER** coluna Valor
- [ ] Atualizar preview HTML para refletir PDF (sem Valor)
- [ ] Adicionar comentários explicativos no código
- [ ] Testar ambas exportações (PDF e Excel)
- [ ] Conferir colspan em mensagens de erro

---

## 📅 Data da Regra
**Implementado em:** 11/02/2026  
**Commit:** `0709481`  
**Arquivo:** `templates/interface_nova.html`

---

## 🚨 MEMORIZE

> **Em 👥 Alocar Equipe no Evento e ✍️ Assinatura:**
> - **PDF = SEM Valor (R$)**
> - **Excel = COM Valor (R$)**

**Nunca esqueça esta regra!** 🔴
