# 📋 Changelog - Atualizações (Fevereiro 2026)

---

## 🎨 UI - Seletor de Registros por Página em Contas a Receber/Pagar (27/02/2026)

### Commits
- `75042b0` — feat: add per-page selector for Contas a Receber and Contas a Pagar
- `8b59491` — fix: extract .data from API envelope and pass page=1
- `c58ba86` — fix: lazy-loader reads per_page from select element
- `f8d5fc8` — ui: move counter and per-page select into filter row
- `71b4d2a` — ui: remove counter badge, style per-page select as standard form-group

### Problema
Contas a Receber e Contas a Pagar exibiam no máximo **50 registros** sem nenhuma opção para o usuário alterar esse limite.

### Causa Raiz (três camadas)
1. **Backend** (`web_server.py`): `per_page` com `default=50`
2. **Lazy Loader** (`lazy-loader.js`): `PAGE_SIZE: 50` hardcoded — este arquivo **substitui** as funções `loadContasReceber()` e `loadContasPagar()` do `app.js` via `lazy-integration.js`
3. **Frontend** (`app.js`): chamada sem `per_page` na URL e sem extrair `.data` do envelope JSON retornado pela API (`{success, data, total}`)

### Solução Implementada

#### Backend — `web_server.py`
```python
# ANTES
per_page = request.args.get('per_page', default=50, type=int)

# DEPOIS
per_page = request.args.get('per_page', default=300, type=int)
per_page = min(per_page, 300)  # Máximo de 300 registros por página
```

#### Lazy Loader — `static/lazy-loader.js`
```javascript
// ANTES: PAGE_SIZE hardcoded
_buildUrl(page) {
    const params = new URLSearchParams({
        page: page,
        per_page: LazyLoadConfig.PAGE_SIZE,  // sempre 50
        ...this.filters
    });
}

// DEPOIS: usa per_page dos filtros se disponível
_buildUrl(page) {
    const perPage = this.filters.per_page || LazyLoadConfig.PAGE_SIZE;
    const { per_page: _removed, ...otherFilters } = this.filters;
    const params = new URLSearchParams({
        page: page,
        per_page: perPage,
        ...otherFilters
    });
}
```

#### Integração Lazy — `static/lazy-integration.js`
```javascript
// Adicionado ao montar filtros de Receber e Pagar:
const perPageSelect = document.getElementById('per-page-receber');
filters.per_page = perPageSelect ? parseInt(perPageSelect.value) || 300 : 300;
```

#### Frontend — `static/app.js`
```javascript
// ANTES: não extraía .data do envelope e não passava page
const response = await fetch(`${API_URL}/lancamentos`);
const todosLancamentos = await response.json(); // era o objeto {success, data, total}

// DEPOIS
const response = await fetch(`${API_URL}/lancamentos?per_page=${perPage}&page=1`);
const responseData = await response.json();
const todosLancamentos = Array.isArray(responseData) ? responseData : (responseData.data || []);
```

#### HTML — `templates/interface_nova.html`
Adicionado campo `📋 Exibir:` como `form-group` padrão (mesmo visual de Ano/Mês/Data) na segunda linha de filtros, ao lado de "Data Final", para Contas a Receber e Contas a Pagar:

```html
<div class="form-group">
    <label>📋 Exibir:</label>
    <select id="per-page-receber" onchange="loadContasReceber()">
        <option value="25">25</option>
        <option value="50">50</option>
        <option value="100">100</option>
        <option value="150">150</option>
        <option value="200">200</option>
        <option value="300" selected>300</option>
    </select>
</div>
```

### Resultado
- ✅ Usuário pode escolher entre 25 / 50 / 100 / 150 / 200 / **300** registros
- ✅ Padrão visual idêntico aos demais filtros (Ano, Mês, Data Inicial, Data Final)
- ✅ Ao trocar o valor, a lista recarrega automaticamente
- ✅ O limite máximo permitido pela API é 300

---

## 🐛 Fix - Erro de Login `empresa_id é obrigatório` (27/02/2026)

### Commit `18ad5e5`

### Problema
Login falhava com `ValueError: ❌ SEGURANÇA: empresa_id é obrigatório para acessar dados de empresa!`

### Causa
`auth_functions.py` chamava `db.get_db_connection()` sem `allow_global=True` em funções que acessam tabelas globais (não específicas de empresa).

### Correção
Adicionado `allow_global=True` em 5 funções:

| Função | Linha |
|--------|-------|
| `autenticar_usuario()` | 176 |
| `validar_sessao()` | 278 |
| `listar_empresas_usuario()` | 761 |
| `obter_empresa_padrao()` | 955 |
| `obter_permissoes_usuario_empresa()` | 977 |

```python
# ANTES
conn = db.get_db_connection()

# DEPOIS
conn = db.get_db_connection(allow_global=True)
```

---

## 🗄️ Dados - Completar 782 Receitas Sem Pessoa/Categoria (27/02/2026)

### Problema
782 lançamentos do tipo RECEITA importados via script direto (fora do sistema de conciliação) estavam sem `pessoa`, `subcategoria` e `categoria`.

### Análise
- Todos os 694 registros do extrato já estavam 100% conciliados
- As 782 receitas vieram de importação direta no banco (`popular_direto_railway.py`)
- Representavam R$ 702.418,25 — 72,2% do volume financeiro total

### Solução
Script SQL com `UPDATE` usando regex para extrair nomes de CPF/descrições PIX:

```sql
-- Extrair nome do pagador de descrições como:
-- "PAGAMENTO PIX-PIX_DEB   01234567890 João da Silva"
UPDATE lancamentos SET
    pessoa = TRIM(SUBSTRING(descricao FROM '\d{11,14}\s+(.+)$')),
    categoria = 'RECEITAS DE EVENTOS',
    subcategoria = 'PAGAMENTOS PIX'
WHERE tipo = 'RECEITA'
  AND (pessoa IS NULL OR pessoa = '')
  AND descricao ILIKE '%PIX%';
```

### Resultados por tipo
| Tipo | Qtd | Pessoa | Categoria atribuída |
|------|-----|--------|---------------------|
| PAGAMENTOS PIX | 727 | Extraída da descrição | RECEITAS DE EVENTOS |
| RECEBIMENTOS PIX | 13 | Extraída da descrição | RECEITAS DE EVENTOS |
| RESGATES | 13 | BANCO SICREDI | RECEITAS BANCARIAS |
| APLICAÇÕES | 20 | BANCO SICREDI | RECEITAS BANCARIAS |
| LIQUIDAÇÃO DE COBRANÇAS | 6 | — | RECEITAS DIVERSAS |
| OUTROS | 4 | — | RECEITAS DIVERSAS |

### Resultado Final
- ✅ **97,2%** dos lançamentos com `pessoa` preenchida
- ✅ **98,0%** com `subcategoria` preenchida
- ✅ **100%** com `categoria` preenchida

---
