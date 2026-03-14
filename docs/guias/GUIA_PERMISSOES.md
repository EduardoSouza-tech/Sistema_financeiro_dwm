# 🔐 Guia Completo de Permissões - Sistema Financeiro DWM

## 📋 Índice
- [Visão Geral](#visão-geral)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Permissões Disponíveis](#permissões-disponíveis)
- [Boas Práticas](#boas-práticas)
- [Checklist para Novas Funcionalidades](#checklist-para-novas-funcionalidades)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O sistema implementa um **controle de acesso baseado em permissões (RBAC - Role-Based Access Control)** com suporte a **multi-empresa**. Cada usuário pode ter diferentes permissões para diferentes empresas.

### Tipos de Usuário
- **Admin**: Acesso total ao sistema (permissão especial: `*`)
- **Cliente**: Acesso baseado em permissões específicas por empresa

---

## 🏗️ Arquitetura do Sistema

### 1. Tabelas do Banco de Dados

#### `permissoes`
Armazena todas as permissões disponíveis no sistema.
```sql
CREATE TABLE permissoes (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(100) UNIQUE NOT NULL,  -- Ex: 'lancamentos_view'
    nome VARCHAR(255) NOT NULL,           -- Ex: 'Ver Lançamentos'
    descricao TEXT,
    categoria VARCHAR(100),               -- Ex: 'financeiro', 'operacional'
    ativo BOOLEAN DEFAULT TRUE
);
```

#### `usuario_empresas`
Vincula usuários a empresas com permissões específicas.
```sql
CREATE TABLE usuario_empresas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    empresa_id INTEGER REFERENCES empresas(id),
    papel VARCHAR(50),                    -- 'admin_empresa', 'usuario', 'visualizador'
    permissoes_empresa JSONB,             -- Array de códigos de permissão
    is_empresa_padrao BOOLEAN DEFAULT FALSE,
    ativo BOOLEAN DEFAULT TRUE
);
```

### 2. Decoradores de Rota

#### `@require_auth`
Verifica apenas se o usuário está autenticado.
```python
@app.route('/api/exemplo')
@require_auth
def exemplo():
    # Qualquer usuário autenticado pode acessar
    pass
```

#### `@require_admin`
Requer que o usuário seja do tipo 'admin'.
```python
@app.route('/api/admin/usuarios')
@require_admin
def gerenciar_usuarios():
    # Apenas admin pode acessar
    pass
```

#### `@require_permission('permissao_codigo')`
Verifica se o usuário tem a permissão específica.
```python
@app.route('/api/lancamentos', methods=['GET'])
@require_permission('lancamentos_view')
def listar_lancamentos():
    # Usuário precisa ter permissão 'lancamentos_view'
    pass
```

### 3. Fluxo de Autenticação

```
Login → Verificar Credenciais → Criar Sessão → Carregar Empresa
                                                      ↓
                                            Carregar Permissões
                                                      ↓
                                    obter_permissoes_usuario_empresa()
                                                      ↓
                                    Permissões armazenadas em session
```

---

## 📊 Permissões Disponíveis

### Categorias e Códigos

#### 🧭 **Navegação**
| Código | Nome | Descrição |
|--------|------|-----------|
| `dashboard` | Dashboard | Visualizar dashboard principal |
| `relatorios_view` | Relatórios | Acessar menu de relatórios |
| `cadastros_view` | Cadastros | Acessar menu de cadastros |
| `operacional_view` | Operacional | Acessar menu operacional |

#### 💰 **Financeiro**
| Código | Nome | Descrição |
|--------|------|-----------|
| `lancamentos_view` | Ver Lançamentos | Visualizar lançamentos financeiros |
| `lancamentos_create` | Criar Lançamentos | Criar novos lançamentos |
| `lancamentos_edit` | Editar Lançamentos | Editar lançamentos existentes |
| `lancamentos_delete` | Excluir Lançamentos | Excluir lançamentos |
| `contas_view` | Ver Contas | Visualizar contas bancárias |
| `contas_create` | Criar Contas | Criar novas contas bancárias |
| `categorias_view` | Ver Categorias | Visualizar categorias |
| `categorias_create` | Criar Categorias | Criar novas categorias |
| `categorias_edit` | Editar Categorias | Editar categorias existentes |

#### 📋 **Cadastros**
| Código | Nome | Descrição |
|--------|------|-----------|
| `clientes_view` | Ver Clientes | Visualizar clientes |
| `clientes_create` | Criar Clientes | Criar novos clientes |
| `clientes_edit` | Editar Clientes | Editar clientes existentes |
| `clientes_delete` | Excluir Clientes | Excluir clientes |
| `fornecedores_view` | Ver Fornecedores | Visualizar fornecedores |
| `fornecedores_create` | Criar Fornecedores | Criar novos fornecedores |
| `fornecedores_edit` | Editar Fornecedores | Editar fornecedores existentes |
| `fornecedores_delete` | Excluir Fornecedores | Excluir fornecedores |

#### ⚙️ **Operacional**
| Código | Nome | Descrição |
|--------|------|-----------|
| `contratos_view` | Ver Contratos | Visualizar contratos |
| `contratos_create` | Criar Contratos | Criar novos contratos |
| `contratos_edit` | Editar Contratos | Editar contratos existentes |
| `contratos_delete` | Excluir Contratos | Excluir contratos |
| `sessoes_view` | Ver Sessões | Visualizar sessões |
| `sessoes_create` | Criar Sessões | Criar novas sessões |
| `sessoes_edit` | Editar Sessões | Editar sessões existentes |
| `sessoes_delete` | Excluir Sessões | Excluir sessões |
| `agenda_view` | Ver Agenda | Visualizar agenda |
| `agenda_create` | Criar Eventos | Criar eventos na agenda |
| `agenda_edit` | Editar Eventos | Editar eventos da agenda |
| `agenda_delete` | Excluir Eventos | Excluir eventos da agenda |
| `eventos_view` | Ver Eventos | Visualizar eventos |
| `eventos_create` | Criar Eventos | Criar novos eventos |
| `eventos_edit` | Editar Eventos | Editar eventos existentes |
| `eventos_delete` | Excluir Eventos | Excluir eventos |
| `estoque_view` | Ver Estoque | Visualizar estoque |
| `estoque_edit` | Editar Estoque | Editar estoque |

#### 👥 **Recursos Humanos**
| Código | Nome | Descrição |
|--------|------|-----------|
| `folha_pagamento_view` | Ver Folha de Pagamento | Visualizar folha de pagamento |
| `folha_pagamento_create` | Criar Folha de Pagamento | Criar nova folha de pagamento |
| `folha_pagamento_edit` | Editar Folha de Pagamento | Editar folha de pagamento |
| `folha_pagamento_delete` | Excluir Folha de Pagamento | Excluir folha de pagamento |

#### 📈 **Relatórios**
| Código | Nome | Descrição |
|--------|------|-----------|
| `exportar_pdf` | Exportar PDF | Exportar dados em PDF |
| `exportar_excel` | Exportar Excel | Exportar dados em Excel |

#### ⚙️ **Sistema**
| Código | Nome | Descrição |
|--------|------|-----------|
| `configuracoes` | Configurações | Acessar configurações |
| `usuarios_admin` | Gerenciar Usuários | Gerenciar usuários e permissões (apenas admin) |

---

## ✅ Boas Práticas

### 1. **NUNCA use `@require_permission('admin')`**

❌ **ERRADO:**
```python
@app.route('/api/eventos', methods=['GET'])
@require_permission('admin')  # ❌ Requer ser admin
def listar_eventos():
    pass
```

✅ **CORRETO:**
```python
@app.route('/api/eventos', methods=['GET'])
@require_permission('eventos_view')  # ✅ Permissão específica
def listar_eventos():
    pass
```

### 2. **Padrão de Nomenclatura**

Siga o padrão: `<recurso>_<acao>`

| Ação | Sufixo | Exemplo |
|------|--------|---------|
| Visualizar/Listar | `_view` | `eventos_view` |
| Criar | `_create` | `eventos_create` |
| Editar/Atualizar | `_edit` | `eventos_edit` |
| Excluir | `_delete` | `eventos_delete` |

### 3. **Uma Permissão por Rota**

Cada endpoint deve ter apenas uma verificação de permissão.

❌ **EVITE:**
```python
@app.route('/api/exemplo')
@require_permission('permissao1')
@require_permission('permissao2')  # Múltiplas permissões
def exemplo():
    pass
```

✅ **PREFIRA:**
```python
@app.route('/api/exemplo')
@require_permission('exemplo_view')  # Uma permissão específica
def exemplo():
    pass
```

### 4. **Permissões de Menu vs Permissões de API**

O menu deve usar **permissões de visualização**:

```html
<!-- Menu -->
<button data-permission="eventos_view">🎉 Eventos</button>

<!-- Submenu -->
<button data-permission="eventos_view" onclick="showSection('eventos')">
    Ver Eventos
</button>
```

As rotas da API devem usar **permissões específicas**:
```python
GET    /api/eventos       → eventos_view
POST   /api/eventos       → eventos_create
PUT    /api/eventos/<id>  → eventos_edit
DELETE /api/eventos/<id>  → eventos_delete
```

### 5. **Multi-Empresa**

Permissões são específicas por empresa:
- Usuário pode ter `eventos_view` na Empresa A
- Mas NÃO ter `eventos_view` na Empresa B

```python
# As permissões vêm do campo permissoes_empresa da tabela usuario_empresas
permissoes = obter_permissoes_usuario_empresa(usuario_id, empresa_id, auth_db)
```

---

## 📝 Checklist para Novas Funcionalidades

Ao adicionar uma nova funcionalidade, siga este checklist:

### ✅ 1. Adicionar Permissões no Banco

Edite `database_postgresql.py` na lista `permissoes_padrao`:

```python
# Em database_postgresql.py, linha ~1175
permissoes_padrao = [
    # ... outras permissões ...
    
    # Nova funcionalidade
    ('minha_funcao_view', 'Ver Minha Função', 'Visualizar minha função', 'categoria'),
    ('minha_funcao_create', 'Criar Minha Função', 'Criar nova minha função', 'categoria'),
    ('minha_funcao_edit', 'Editar Minha Função', 'Editar minha função', 'categoria'),
    ('minha_funcao_delete', 'Excluir Minha Função', 'Excluir minha função', 'categoria'),
]
```

### ✅ 2. Proteger Rotas da API

Em `web_server.py`:

```python
@app.route('/api/minha-funcao', methods=['GET'])
@require_permission('minha_funcao_view')
def listar_minha_funcao():
    """Listar minha função"""
    # ... código ...

@app.route('/api/minha-funcao', methods=['POST'])
@require_permission('minha_funcao_create')
def criar_minha_funcao():
    """Criar nova minha função"""
    # ... código ...

@app.route('/api/minha-funcao/<int:id>', methods=['PUT'])
@require_permission('minha_funcao_edit')
def editar_minha_funcao(id):
    """Editar minha função"""
    # ... código ...

@app.route('/api/minha-funcao/<int:id>', methods=['DELETE'])
@require_permission('minha_funcao_delete')
def deletar_minha_funcao(id):
    """Deletar minha função"""
    # ... código ...
```

### ✅ 3. Adicionar no Menu (Frontend)

Em `templates/interface_nova.html`:

```html
<!-- Botão do menu -->
<button class="submenu-button" 
        onclick="showSection('minha-funcao')" 
        data-permission="minha_funcao_view">
    🎯 Minha Função
</button>
```

### ✅ 4. Atualizar Documentação

Adicione a nova funcionalidade neste documento na seção [Permissões Disponíveis](#permissões-disponíveis).

### ✅ 5. Testar

1. **Deploy no Railway** (ou restart local)
2. **Login como Admin**
3. **Editar Usuário de Teste**
4. **Marcar as novas permissões**
5. **Login como Usuário de Teste**
6. **Verificar que:**
   - Menu aparece ✅
   - API funciona ✅
   - Sem permissão = erro 403 ✅

---

## 🐛 Troubleshooting

### ❌ Erro: "Permissão negada - Você não tem acesso a: admin"

**Causa:** A rota está usando `@require_permission('admin')` em vez de uma permissão específica.

**Solução:**
1. Identifique a rota no erro
2. Procure no `web_server.py`
3. Substitua por permissão específica

```python
# ANTES
@require_permission('admin')

# DEPOIS
@require_permission('eventos_view')
```

### ❌ Menu não aparece para usuário

**Possíveis causas:**

1. **Permissão não concedida na empresa**
   - Verifique em "Gerenciar Usuários" → Editar → Empresas
   - Marque a permissão correta

2. **Nome da permissão incorreto no menu**
   ```html
   <!-- Verifique se o data-permission corresponde ao código no banco -->
   <button data-permission="eventos_view">🎉 Eventos</button>
   ```

3. **Permissão não criada no banco**
   - Verifique se a permissão está em `permissoes_padrao`
   - Reinicie o servidor para criar permissões

### ❌ API retorna 403 mesmo com permissão

**Debug:**

1. **Verifique os logs do backend:**
   ```
   🔐 Carregando permissões...
   📋 Permissões carregadas: X itens
   ```

2. **Verifique o Console do navegador (F12):**
   ```javascript
   📋 Permissões: Array(26)
   // Deve incluir a permissão necessária
   ```

3. **Verifique se a permissão está no campo `permissoes_empresa`:**
   ```sql
   SELECT permissoes_empresa 
   FROM usuario_empresas 
   WHERE usuario_id = X AND empresa_id = Y;
   ```

### ❌ Permissões desaparecem após logout

**Causa:** As permissões são armazenadas na sessão, que é limpa no logout.

**Comportamento esperado:** Isso é normal. As permissões são recarregadas no próximo login.

---

## 📚 Referências Rápidas

### Arquivos Principais

| Arquivo | Responsabilidade |
|---------|------------------|
| `database_postgresql.py` (linha ~1175) | Define permissões disponíveis |
| `auth_functions.py` (linha 755-900) | Gerencia vínculos usuário-empresa |
| `web_server.py` | Decoradores de proteção de rotas |
| `templates/interface_nova.html` (linha 3994) | Filtro de menu no frontend |

### Funções Importantes

```python
# Obter permissões de um usuário em uma empresa
obter_permissoes_usuario_empresa(usuario_id, empresa_id, db)

# Vincular usuário a empresa com permissões
vincular_usuario_empresa(usuario_id, empresa_id, papel, permissoes, is_padrao, criado_por, db)

# Atualizar permissões de vínculo existente
atualizar_usuario_empresa(usuario_id, empresa_id, papel, permissoes, is_padrao, db)

# Verificar se tem acesso à empresa
tem_acesso_empresa(usuario_id, empresa_id, db)
```

---

## 🚀 Convenções do Projeto

1. **Sempre use permissões específicas**, nunca `'admin'`
2. **Siga o padrão de nomenclatura**: `recurso_acao`
3. **Uma rota = uma permissão**
4. **Teste em ambiente local antes de deploy**
5. **Documente novas permissões neste arquivo**

---

**Última atualização:** 16/01/2026
**Versão:** 2.0
**Mantido por:** Equipe DWM
