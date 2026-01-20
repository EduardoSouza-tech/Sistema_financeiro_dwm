# 📋 Documentação - Folha de Pagamento

## 📊 Estrutura do Banco de Dados

### Tabela: `funcionarios`

```sql
CREATE TABLE IF NOT EXISTS funcionarios (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    nome VARCHAR(255) NOT NULL,
    cpf VARCHAR(11) NOT NULL,
    endereco TEXT,
    tipo_chave_pix VARCHAR(50) NOT NULL,
    chave_pix VARCHAR(255),
    ativo BOOLEAN DEFAULT TRUE,
    data_admissao DATE,
    data_demissao DATE,
    observacoes TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_cpf_empresa UNIQUE (cpf, empresa_id)
)
```

#### Índices:
- `idx_funcionarios_empresa` - Busca por empresa
- `idx_funcionarios_cpf` - Busca por CPF
- `idx_funcionarios_ativo` - Filtro por status ativo/inativo

#### ⚠️ IMPORTANTE - Colunas que NÃO existem:
As seguintes colunas **NÃO EXISTEM** na tabela e causarão erro se usadas:
- ❌ `cargo`
- ❌ `departamento`
- ❌ `salario`

## 🔌 Endpoints da API

### GET `/api/funcionarios`
**Uso:** Lista completa de funcionários para a página Folha de Pagamento

**Response:**
```json
{
  "funcionarios": [
    {
      "id": 1,
      "nome": "WALTER MANOEL INACIO DE OLIVEIRA",
      "cpf": "01986543161",
      "endereco": "TESTE",
      "tipo_chave_pix": "CPF",
      "chave_pix": "01986543161",
      "ativo": true,
      "data_admissao": "2024-01-01",
      "observacoes": null
    }
  ]
}
```

**Permissão:** `@require_permission('folha_pagamento_view')`

---

### GET `/api/rh/funcionarios`
**Uso:** Lista simplificada de funcionários ATIVOS para dropdowns em modais

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "nome": "WALTER MANOEL INACIO DE OLIVEIRA"
    }
  ]
}
```

**Filtro:** `WHERE ativo = true`  
**Permissão:** Nenhuma (acesso livre para modais)

---

### POST `/api/funcionarios`
**Uso:** Cadastrar novo funcionário

**Body:**
```json
{
  "nome": "Nome Completo",
  "cpf": "12345678901",
  "endereco": "Endereço completo",
  "tipo_chave_pix": "CPF|EMAIL|TELEFONE|ALEATORIA",
  "chave_pix": "Chave correspondente",
  "data_admissao": "2024-01-01",
  "observacoes": "Observações opcionais"
}
```

**Validações:**
- CPF deve ter 11 dígitos
- CPF + empresa_id devem ser únicos
- `tipo_chave_pix` e `chave_pix` são obrigatórios

---

### PUT `/api/funcionarios/<id>`
**Uso:** Atualizar funcionário existente (incluindo ativar/inativar)

**Body (exemplo - ativar/inativar):**
```json
{
  "ativo": true
}
```

**Body (exemplo - atualização completa):**
```json
{
  "nome": "Nome Atualizado",
  "cpf": "12345678901",
  "endereco": "Novo endereço",
  "tipo_chave_pix": "EMAIL",
  "chave_pix": "email@exemplo.com",
  "ativo": false,
  "data_demissao": "2024-12-31",
  "observacoes": "Demitido"
}
```

---

## 🖥️ Interface Frontend

### Arquivo: `templates/interface_nova.html`

#### Função: `loadFuncionarios()`
**Linha:** ~4961  
**Uso:** Carrega lista completa de funcionários na página Folha de Pagamento

```javascript
async function loadFuncionarios() {
  const response = await fetch('/api/funcionarios', {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' }
  });
  const result = await response.json();
  
  // Renderiza tabela com funcionarios
  const tbody = document.getElementById('tbody-funcionarios');
  // ... código de renderização
}
```

#### Função: `toggleAtivoFuncionario(id, ativoAtual)`
**Uso:** Ativar/Inativar funcionário

```javascript
async function toggleAtivoFuncionario(id, ativoAtual) {
  const response = await fetch(`/api/funcionarios/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ativo: !ativoAtual })
  });
  
  if (response.ok) {
    loadFuncionarios(); // Recarrega lista
  }
}
```

---

## 🔧 Erros Comuns e Soluções

### ❌ Erro: `column "cargo" does not exist`
**Causa:** Query tentando buscar colunas inexistentes  
**Solução:** Usar apenas: `id`, `nome`, `cpf`, `endereco`, `tipo_chave_pix`, `chave_pix`, `ativo`, `data_admissao`, `data_demissao`, `observacoes`

### ❌ Erro: `KeyError: 0`
**Causa:** Cursor configurado como RealDictCursor retorna dict, não tupla  
**Solução:** 
```python
result = cursor.fetchone()
# Acesso seguro:
value = result['coluna'] if isinstance(result, dict) else result[0]
```

### ❌ Erro: Funcionários não aparecem no dropdown
**Causa:** 
1. Endpoint `/api/rh/funcionarios` com erro 500
2. Funcionários com `ativo = false`
3. Decorator `@require_permission` bloqueando acesso

**Solução:**
1. Verificar logs do servidor
2. Confirmar que há funcionários com `ativo = true`
3. Remover decorator de endpoints usados em modais

---

## 🔄 Fluxo de Uso

### 1. Cadastro de Funcionário
```
Usuário → Botão "Novo Funcionário" → Modal 
  → Preenche formulário → Salvar 
  → POST /api/funcionarios → Sucesso 
  → loadFuncionarios() → Tabela atualizada
```

### 2. Ativar/Inativar
```
Usuário → Clica botão "Ativar/Inativar" 
  → toggleAtivoFuncionario(id, ativoAtual) 
  → PUT /api/funcionarios/{id} com {ativo: !ativoAtual}
  → Sucesso → loadFuncionarios() → Badge atualizado
```

### 3. Uso em Dropdowns (Sessões)
```
Usuário → "Nova Sessão" → openModalSessao() 
  → loadFuncionariosRH() 
  → GET /api/rh/funcionarios 
  → Popula dropdowns "Equipe" e "Responsáveis"
```

---

## 📝 Checklist de Manutenção

Ao adicionar/modificar funcionalidades:

- [ ] Verificar se colunas existem na tabela antes de usar em queries
- [ ] Testar com cursor dict E tupla (suporte a ambos)
- [ ] Validar CPF (11 dígitos, único por empresa)
- [ ] Garantir que `tipo_chave_pix` e `chave_pix` estão presentes
- [ ] Testar filtro `ativo = true` em dropdowns
- [ ] Verificar logs do servidor em caso de erro 500
- [ ] Confirmar permissões não bloqueiam endpoints de modal

---

## 🎯 Endpoints Relacionados

- `/api/funcionarios` - CRUD completo (Folha de Pagamento)
- `/api/rh/funcionarios` - Lista simples para dropdowns (Modais)
- `/api/sessoes` - Usa funcionários como Equipe/Responsáveis

---

**Última atualização:** 20/01/2026  
**Versão:** 1.0
