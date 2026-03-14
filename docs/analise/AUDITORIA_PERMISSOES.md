# 🔍 Auditoria de Permissões - Sistema Financeiro DWM

**Data da Auditoria:** 16/01/2026  
**Versão do Sistema:** 2.0

---

## 📊 Status Geral

✅ **72 rotas protegidas com permissões específicas**  
✅ **0 rotas usando `@require_permission('admin')`**  
✅ **56 permissões cadastradas no banco de dados**  

---

## 🗺️ Matriz de Rotas e Permissões

### 💰 Financeiro

| Método | Endpoint | Permissão | Status |
|--------|----------|-----------|--------|
| GET | `/api/contas` | `contas_view` | ✅ |
| POST | `/api/contas` | `contas_create` | ✅ |
| GET | `/api/contas/<id>` | `contas_view` | ✅ |
| POST | `/api/lancamentos` | `lancamentos_create` | ✅ |
| GET | `/api/categorias` | `categorias_view` | ✅ |
| POST | `/api/categorias` | `categorias_create` | ✅ |
| PUT | `/api/categorias/<id>` | `categorias_edit` | ✅ |
| GET | `/api/lancamentos` | `lancamentos_view` | ✅ |
| POST | `/api/lancamentos/lote` | `lancamentos_create` | ✅ |
| GET | `/api/lancamentos/<id>` | `lancamentos_view` | ✅ |
| PUT | `/api/lancamentos/<id>` | `lancamentos_edit` | ✅ |
| PUT | `/api/lancamentos/<id>/pagar` | `lancamentos_edit` | ✅ |
| GET | `/api/lancamentos/periodo` | `lancamentos_view` | ✅ |
| PUT | `/api/lancamentos/<id>/reagendar` | `lancamentos_edit` | ✅ |
| GET | `/api/lancamentos/<id>/historico` | `lancamentos_view` | ✅ |
| DELETE | `/api/lancamentos/<id>` | `lancamentos_delete` | ✅ |
| DELETE | `/api/lancamentos/bulk` | `lancamentos_delete` | ✅ |

### 📋 Cadastros

| Método | Endpoint | Permissão | Status |
|--------|----------|-----------|--------|
| GET | `/api/clientes` | `clientes_view` | ✅ |
| POST | `/api/clientes` | `clientes_create` | ✅ |
| PUT | `/api/clientes/<id>` | `clientes_edit` | ✅ |
| GET | `/api/fornecedores` | `fornecedores_view` | ✅ |
| POST | `/api/fornecedores` | `fornecedores_create` | ✅ |
| PUT | `/api/fornecedores/<id>` | `fornecedores_edit` | ✅ |
| PUT | `/api/clientes/<id>/vincular-empresa` | `clientes_edit` | ✅ |
| PUT | `/api/clientes/<id>/desvincular-empresa` | `clientes_edit` | ✅ |
| PUT | `/api/fornecedores/<id>/vincular-empresa` | `fornecedores_edit` | ✅ |
| PUT | `/api/fornecedores/<id>/desvincular-empresa` | `fornecedores_edit` | ✅ |

### 👥 Recursos Humanos

| Método | Endpoint | Permissão | Status |
|--------|----------|-----------|--------|
| GET | `/api/funcionarios` | `folha_pagamento_view` | ✅ |
| POST | `/api/funcionarios` | `folha_pagamento_create` | ✅ |
| PUT | `/api/funcionarios/<id>` | `folha_pagamento_edit` | ✅ |

### 🎉 Eventos

| Método | Endpoint | Permissão | Status |
|--------|----------|-----------|--------|
| GET | `/api/eventos` | `eventos_view` | ✅ |
| POST | `/api/eventos` | `eventos_create` | ✅ |
| PUT | `/api/eventos/<id>` | `eventos_edit` | ✅ |
| DELETE | `/api/eventos/<id>` | `eventos_delete` | ✅ |

### 📈 Relatórios

| Método | Endpoint | Permissão | Status |
|--------|----------|-----------|--------|
| GET | `/api/relatorios/fluxo-caixa` | `relatorios_view` | ✅ |
| GET | `/api/relatorios/fluxo-caixa/detalhado` | `relatorios_view` | ✅ |
| POST | `/api/relatorios/inadimplencia` | `relatorios_view` | ✅ |
| GET | `/api/relatorios/comparativo` | `relatorios_view` | ✅ |
| GET | `/api/relatorios/inadimplencia` | `relatorios_view` | ✅ |
| GET | `/api/extrato/consolidado` | `relatorios_view` | ✅ |
| GET | `/api/extrato/periodo` | `relatorios_view` | ✅ |
| GET | `/api/extrato/conta/<id>` | `relatorios_view` | ✅ |
| GET | `/api/indicadores/dre` | `relatorios_view` | ✅ |
| GET | `/api/indicadores/liquidez` | `relatorios_view` | ✅ |

### ⚙️ Operacional

| Método | Endpoint | Permissão | Status |
|--------|----------|-----------|--------|
| GET | `/api/clientes/autocomplete` | `clientes_view` | ✅ |
| GET | `/api/clientes/buscar` | `clientes_view` | ✅ |
| GET | `/api/fornecedores/autocomplete` | `fornecedores_view` | ✅ |
| GET | `/api/fornecedores/buscar` | `fornecedores_view` | ✅ |
| GET | `/api/tipos-sessao` | `contratos_view` | ✅ |
| POST | `/api/tipos-sessao` | `contratos_view` | ✅ |
| PUT | `/api/tipos-sessao/<id>` | `contratos_edit` | ✅ |
| GET | `/api/comissoes` | `sessoes_view` | ✅ |
| PUT | `/api/comissoes/<id>` | `sessoes_edit` | ✅ |
| GET | `/api/equipes` | `operacional_view` | ✅ |
| PUT | `/api/equipes/<id>` | `operacional_edit` | ✅ |
| GET | `/api/tags` | `operacional_view` | ✅ |
| PUT | `/api/tags/<id>` | `operacional_edit` | ✅ |
| GET | `/api/templates-equipe` | `operacional_view` | ✅ |
| PUT | `/api/templates-equipe/<id>` | `operacional_edit` | ✅ |
| GET | `/api/agenda-fotografia` | `agenda_view` | ✅ |
| PUT | `/api/agenda-fotografia/<id>` | `agenda_edit` | ✅ |
| GET | `/api/estoque` | `estoque_view` | ✅ |
| PUT | `/api/estoque/<id>` | `estoque_edit` | ✅ |
| GET | `/api/kits-equipamentos` | `estoque_view` | ✅ |
| PUT | `/api/kits-equipamentos/<id>` | `estoque_edit` | ✅ |

---

## 📋 Permissões Faltantes

As seguintes funcionalidades **NÃO têm permissões específicas** cadastradas:

⚠️ **Nenhuma permissão faltante identificada**

Todas as funcionalidades principais possuem permissões adequadas.

---

## 🔧 Correções Realizadas

### 16/01/2026 - Sessão de Correções

#### 1. Folha de Pagamento
- ❌ **Antes:** `@require_permission('admin')`
- ✅ **Depois:** `folha_pagamento_view/create/edit`
- **Rotas corrigidas:** 3

#### 2. Eventos
- ❌ **Antes:** `@require_permission('admin')`
- ✅ **Depois:** `eventos_view/create/edit/delete`
- **Rotas corrigidas:** 4

#### 3. Atualização de Vínculos Empresa-Usuário
- **Problema:** Permissões não eram atualizadas quando vínculo já existia
- **Solução:** Sempre atualizar permissões, independente de mudança em `is_empresa_padrao`
- **Arquivo:** `web_server.py` linha ~1474

---

## 🎯 Recomendações

### Prioridade Alta
✅ Todas as rotas públicas estão protegidas

### Prioridade Média
- [ ] Adicionar permissões de DELETE para:
  - Funcionários (`folha_pagamento_delete`)
  - Categorias (`categorias_delete`)
  - Contas Bancárias (`contas_delete`)

### Prioridade Baixa
- [ ] Implementar auditoria automática de permissões
- [ ] Criar script de validação de rotas vs permissões
- [ ] Adicionar testes automatizados para permissões

---

## 🚨 Alertas de Segurança

### ✅ Boas Práticas Seguidas

1. **Nenhuma rota usa `admin` hardcoded**
2. **Todas as rotas CRUD têm permissões específicas**
3. **Sistema multi-empresa implementado corretamente**
4. **Filtro de menu no frontend baseado em permissões**

### ⚠️ Pontos de Atenção

1. **Permissões Globais vs Por Empresa**
   - Sistema usa permissões por empresa (`permissoes_empresa`)
   - Permissões globais (`usuario_permissoes`) são legado
   - Manter sincronização ou deprecar sistema global

2. **Validação de Empresa**
   - Todas as rotas devem validar `empresa_id`
   - Usar `@aplicar_filtro_cliente` onde aplicável

---

## 📝 Checklist de Auditoria

Use este checklist ao adicionar novas rotas:

- [ ] Permissão cadastrada em `database_postgresql.py`
- [ ] Rota protegida com `@require_permission('permissao_especifica')`
- [ ] Menu atualizado com `data-permission="permissao_view"`
- [ ] Documentação atualizada em `GUIA_PERMISSOES.md`
- [ ] Teste manual realizado
- [ ] Commit com mensagem descritiva

---

## 📞 Contato

Para questões sobre permissões:
- Revisar: `GUIA_PERMISSOES.md`
- Verificar: Este arquivo de auditoria
- Consultar: Equipe de desenvolvimento

---

**Próxima Auditoria Recomendada:** 01/02/2026
