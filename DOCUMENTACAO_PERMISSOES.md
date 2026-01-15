# 🔐 Documentação Completa do Sistema de Permissões

**Data:** 15 de Janeiro de 2026  
**Versão:** 1.0  
**Total de Permissões:** 30

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Lista Completa de Permissões](#lista-completa-de-permissões)
3. [Como Atribuir Permissões](#como-atribuir-permissões)
4. [Verificação Técnica](#verificação-técnica)

---

## 🎯 Visão Geral

O sistema possui **30 permissões granulares** organizadas em **8 categorias** principais. O administrador pode atribuir permissões individuais a cada usuário, controlando exatamente quais funcionalidades ele pode acessar.

### Regras Importantes

- ✅ **Admin**: Tem TODAS as permissões automaticamente (bypass)
- ✅ **Usuário Normal**: Só acessa funcionalidades com permissão concedida
- ✅ **Painel Admin**: Permite atribuir/remover permissões em tempo real
- ✅ **Validação Backend**: Decorador `@require_permission('codigo')` valida antes de executar

---

## 📚 Lista Completa de Permissões

### 1. 📊 Dashboard (1 permissão)

| Código | Nome | Descrição |
|--------|------|-----------|
| `dashboard` | Visualizar Dashboard | Acesso ao painel principal com métricas e gráficos |

**Uso:**
```python
@app.route('/api/dashboard')
@require_permission('dashboard')
def dashboard():
    # Retorna dados do dashboard
```

---

### 2. 💰 Lançamentos Financeiros (4 permissões)

| Código | Nome | Descrição |
|--------|------|-----------|
| `lancamentos_view` | Visualizar Lançamentos | Ver lista de receitas e despesas |
| `lancamentos_create` | Criar Lançamentos | Adicionar novas receitas/despesas |
| `lancamentos_edit` | Editar Lançamentos | Modificar lançamentos existentes |
| `lancamentos_delete` | Deletar Lançamentos | Remover lançamentos |

**Uso:**
```python
@app.route('/api/lancamentos', methods=['GET'])
@require_permission('lancamentos_view')
def listar_lancamentos():
    # Retorna lançamentos

@app.route('/api/lancamentos', methods=['POST'])
@require_permission('lancamentos_create')
def criar_lancamento():
    # Cria novo lançamento
```

---

### 3. 👤 Clientes (4 permissões)

| Código | Nome | Descrição |
|--------|------|-----------|
| `clientes_view` | Visualizar Clientes | Ver lista de clientes |
| `clientes_create` | Criar Clientes | Cadastrar novos clientes |
| `clientes_edit` | Editar Clientes | Modificar dados de clientes |
| `clientes_delete` | Deletar Clientes | Remover clientes |

**Uso:**
```python
@app.route('/api/clientes', methods=['GET'])
@require_permission('clientes_view')
def listar_clientes():
    # Retorna clientes
```

---

### 4. 🏭 Fornecedores (4 permissões)

| Código | Nome | Descrição |
|--------|------|-----------|
| `fornecedores_view` | Visualizar Fornecedores | Ver lista de fornecedores |
| `fornecedores_create` | Criar Fornecedores | Cadastrar novos fornecedores |
| `fornecedores_edit` | Editar Fornecedores | Modificar dados de fornecedores |
| `fornecedores_delete` | Deletar Fornecedores | Remover fornecedores |

---

### 5. 🏦 Contas Bancárias (3 permissões)

| Código | Nome | Descrição |
|--------|------|-----------|
| `contas_bancarias_view` | Visualizar Contas | Ver contas bancárias cadastradas |
| `contas_bancarias_create` | Criar Contas | Adicionar novas contas |
| `contas_bancarias_edit` | Editar Contas | Modificar dados de contas |

---

### 6. 📁 Categorias (4 permissões)

| Código | Nome | Descrição |
|--------|------|-----------|
| `categorias_view` | Visualizar Categorias | Ver categorias de lançamentos |
| `categorias_create` | Criar Categorias | Adicionar novas categorias |
| `categorias_edit` | Editar Categorias | Modificar categorias existentes |
| `categorias_delete` | Deletar Categorias | Remover categorias |

---

### 7. 📊 Relatórios (3 permissões)

| Código | Nome | Descrição |
|--------|------|-----------|
| `relatorios_view` | Visualizar Relatórios | Acesso aos relatórios gerais |
| `relatorios_financeiros` | Relatórios Financeiros | Relatórios de fluxo de caixa, DRE, etc |
| `relatorios_clientes` | Relatórios de Clientes | Relatórios de inadimplência, análise de clientes |

**Uso:**
```python
@app.route('/api/relatorios/fluxo-caixa')
@require_permission('relatorios_financeiros')
def relatorio_fluxo_caixa():
    # Gera relatório
```

---

### 8. 📋 Contratos e Operacional (7 permissões)

| Código | Nome | Descrição |
|--------|------|-----------|
| `contratos_view` | Visualizar Contratos | Ver contratos e sessões de fotografia |
| `contratos_create` | Criar Contratos | Adicionar novos contratos |
| `contratos_edit` | Editar Contratos | Modificar contratos existentes |
| `contratos_delete` | Deletar Contratos | Remover contratos |
| `agenda_view` | Visualizar Agenda | Acesso à agenda de fotografia |
| `estoque_view` | Visualizar Estoque | Ver gestão de equipamentos |
| `operacional_view` | Operações Gerais | Acesso a kits, tags, templates |

---

## 🎯 Como Atribuir Permissões

### No Painel Admin

1. **Acesse o Painel Admin** (apenas usuários com `tipo='admin'`)
   ```
   https://seu-dominio.railway.app/admin
   ```

2. **Clique na aba "Usuários"**

3. **Criar Novo Usuário:**
   - Clique em "➕ Novo Usuário"
   - Preencha os dados:
     * Username
     * Nome Completo
     * Senha
     * Tipo: `cliente` (usuários normais)
     * Empresa: Selecione a empresa do usuário
   
4. **Selecionar Permissões:**
   - Marque as caixas das permissões desejadas
   - As permissões são organizadas por categoria
   - Você pode selecionar quantas quiser

5. **Salvar:**
   - Clique em "Salvar"
   - As permissões são aplicadas imediatamente

### Exemplo: Usuário Financeiro

Um usuário que trabalha apenas com finanças poderia ter:

```
✅ dashboard
✅ lancamentos_view
✅ lancamentos_create
✅ lancamentos_edit
✅ contas_bancarias_view
✅ categorias_view
✅ relatorios_view
✅ relatorios_financeiros
```

### Exemplo: Usuário Operacional

Um fotógrafo que gerencia sessões e equipamentos:

```
✅ dashboard
✅ clientes_view
✅ contratos_view
✅ contratos_create
✅ contratos_edit
✅ agenda_view
✅ estoque_view
✅ operacional_view
```

---

## 🔍 Verificação Técnica

### Listar Todas as Permissões (SQL)

```sql
SELECT 
    codigo, 
    nome, 
    descricao, 
    categoria, 
    ativo 
FROM permissoes 
WHERE ativo = TRUE 
ORDER BY categoria, codigo;
```

**Resultado esperado:** 30 linhas

### Verificar Permissões de um Usuário (SQL)

```sql
SELECT 
    p.codigo, 
    p.nome, 
    p.categoria
FROM permissoes p
JOIN usuario_permissoes up ON p.id = up.permissao_id
WHERE up.usuario_id = 5  -- ID do usuário
AND p.ativo = TRUE;
```

### Endpoint API: Listar Permissões

```bash
GET /api/permissoes
```

**Resposta:**
```json
[
  {
    "id": 1,
    "codigo": "dashboard",
    "nome": "Visualizar Dashboard",
    "descricao": "Acesso ao painel principal",
    "categoria": "Geral",
    "ativo": true
  },
  {
    "id": 2,
    "codigo": "lancamentos_view",
    "nome": "Visualizar Lançamentos",
    "descricao": "Ver lista de lançamentos",
    "categoria": "Financeiro",
    "ativo": true
  },
  ...
]
```

### Script de Verificação (Python)

```python
import database_postgresql as db

# Listar todas as permissões
permissoes = db.listar_permissoes()
print(f"Total de permissões: {len(permissoes)}")

# Verificar se tem 30
assert len(permissoes) == 30, "Deveria ter 30 permissões!"

# Agrupar por categoria
from collections import defaultdict
categorias = defaultdict(list)

for p in permissoes:
    categorias[p['categoria']].append(p['codigo'])

for cat, perms in categorias.items():
    print(f"\n{cat}: {len(perms)} permissões")
    for p in perms:
        print(f"  - {p}")
```

---

## ⚠️ Problema Conhecido: Modal Não Carrega Permissões

### Sintoma

Ao abrir o modal de criar/editar usuário, a área de permissões aparece vazia.

### Causa

O endpoint `/api/permissoes` não está retornando os dados corretamente OU o JavaScript não está processando a resposta.

### Solução

1. **Verificar endpoint:**
```python
@app.route('/api/permissoes', methods=['GET'])
@require_admin
def listar_permissoes_api():
    try:
        permissoes = auth_db.listar_permissoes()
        return jsonify(permissoes), 200  # ✅ Retornar array direto
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

2. **Verificar JavaScript (admin.html):**
```javascript
async function loadPermissions() {
    const response = await fetch('/api/permissoes', {
        credentials: 'include'
    });
    
    if (!response.ok) {
        console.error('Erro ao carregar permissões');
        return;
    }
    
    const data = await response.json();
    
    // Verificar se é array ou objeto com propriedade
    allPermissions = Array.isArray(data) ? data : data.permissoes || [];
    
    console.log(`✅ ${allPermissions.length} permissões carregadas`);
    renderPermissionsGrid();
}
```

3. **Testar manualmente:**
```bash
# No navegador, console F12:
fetch('/api/permissoes', {credentials: 'include'})
  .then(r => r.json())
  .then(d => console.log('Permissões:', d))
```

---

## 🎓 Conclusão

O sistema possui **30 permissões granulares** que permitem controle fino sobre o que cada usuário pode fazer. O administrador global pode:

- ✅ Ver todas as 30 permissões no painel
- ✅ Atribuir permissões individuais a cada usuário
- ✅ Modificar permissões a qualquer momento
- ✅ Criar usuários vinculados a empresas específicas

**Próximos passos:**
1. Verificar se `/api/permissoes` retorna 30 itens
2. Verificar se JavaScript carrega e renderiza corretamente
3. Testar criação de usuário com permissões selecionadas

---

**Documento criado por:** GitHub Copilot  
**Data:** 15/01/2026  
**Versão:** 1.0
