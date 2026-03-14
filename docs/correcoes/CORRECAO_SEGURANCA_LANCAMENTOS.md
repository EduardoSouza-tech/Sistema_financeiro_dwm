# 🔐 CORREÇÃO DE SEGURANÇA CRÍTICA - VAZAMENTO DE DADOS ENTRE EMPRESAS

**Data**: 2024
**Severidade**: 🔴 CRÍTICA
**Status**: ✅ CORRIGIDO

---

## 📋 Resumo Executivo

Foi identificada e corrigida uma **vulnerabilidade crítica de segurança** que permitia que usuários de uma empresa visualizassem, editassem e excluíssem lançamentos financeiros de outras empresas.

### Impacto
- **Confidencialidade**: 🔴 ALTO - Dados financeiros expostos entre empresas
- **Integridade**: 🔴 ALTO - Possibilidade de modificar/excluir dados de outras empresas  
- **Disponibilidade**: 🟡 MÉDIO - Risco de exclusão acidental/maliciosa de dados

---

## 🔍 Descrição da Vulnerabilidade

### Root Cause
A tabela `lancamentos` **não possuía a coluna `empresa_id`**, quebrando o modelo de multi-tenancy do sistema. Consequentemente:

1. A filtragem por empresa estava **intencionalmente desabilitada** com um comentário TODO
2. Todas as operações CRUD operavam sem isolamento entre empresas
3. Qualquer usuário autenticado podia acessar lançamentos de qualquer empresa

### Código Vulnerável

**database_postgresql.py - Linha 2734-2744 (ANTES DA CORREÇÃO):**
```python
# NOTA: Tabela lancamentos ainda não tem coluna proprietario_id ou empresa_id
# Filtro de multi-tenancy temporariamente desabilitado até migração
# TODO: Adicionar coluna empresa_id à tabela lancamentos
# if empresa_id is not None:
#     query += " AND empresa_id = %s"
#     params.append(empresa_id)
```

### Operações Afetadas

| Operação | Rota | Vulnerável? |
|----------|------|-------------|
| Listar lançamentos | `GET /api/lancamentos` | ✅ Filtrava corretamente |
| Obter lançamento | `GET /api/lancamentos/<id>` | ✅ Filtrava corretamente |
| Criar lançamento | `POST /api/lancamentos` | ✅ Não afetado (cria para empresa do usuário) |
| Atualizar lançamento | `PUT /api/lancamentos/<id>` | ✅ Filtrava corretamente |
| Excluir lançamento | `DELETE /api/lancamentos/<id>` | ❌ **VULNERÁVEL** |
| Pagar lançamento | `PUT /api/lancamentos/<id>/pagar` | ❌ **VULNERÁVEL** |
| Liquidar lançamento | `POST /api/lancamentos/<id>/liquidar` | ❌ **VULNERÁVEL** |
| Cancelar lançamento | `PUT /api/lancamentos/<id>/cancelar` | ❌ **VULNERÁVEL** |

---

## 🛠️ Correções Implementadas

### 1. Database Schema (`database_postgresql.py`)

#### ✅ CREATE TABLE
**Linha 889-910**: Adicionado coluna `empresa_id INTEGER`

```sql
CREATE TABLE IF NOT EXISTS lancamentos (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(10) NOT NULL,
    descricao TEXT NOT NULL,
    valor DECIMAL(15, 2) NOT NULL,
    -- ... outras colunas ...
    empresa_id INTEGER  -- 🆕 NOVA COLUNA
)
```

#### ✅ Método `listar_lancamentos()`
**Linha 2712-2850**: Filtro de empresa **REATIVADO** e **OBRIGATÓRIO**

```python
# 🔒 FILTRO CRÍTICO DE SEGURANÇA: Isolamento por empresa
# OBRIGATÓRIO: Sempre filtrar por empresa_id para evitar vazamento de dados
if empresa_id is not None:
    query += " AND empresa_id = %s"
    params.append(empresa_id)
elif filtro_cliente_id is not None:
    query += " AND empresa_id = %s"
    params.append(filtro_cliente_id)
else:
    # ⚠️ SEGURANÇA: Se não houver empresa_id, não retornar nada
    log("⚠️ AVISO: listar_lancamentos chamado sem empresa_id - retornando lista vazia")
    return []
```

#### ✅ Método `obter_lancamento()`
**Linha 2838-2900**: Adicionado parâmetro `empresa_id` + filtro WHERE

```python
def obter_lancamento(self, lancamento_id: int, empresa_id: int = None) -> Optional[Lancamento]:
    if empresa_id:
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM lancamentos WHERE id = %s AND empresa_id = %s"  # 🔒 FILTRO
            cursor.execute(query, (lancamento_id, empresa_id))
```

#### ✅ Método `excluir_lancamento()`
**Linha 2914-2940**: Adicionado parâmetro `empresa_id` + filtro WHERE

```python
def excluir_lancamento(self, lancamento_id: int, empresa_id: int = None) -> bool:
    if empresa_id:
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM lancamentos WHERE id = %s AND empresa_id = %s",  # 🔒 FILTRO
                         (lancamento_id, empresa_id))
```

#### ✅ Método `pagar_lancamento()`
**Linha 3026-3115**: Adicionado parâmetro `empresa_id` + filtro WHERE

Refatorado com método auxiliar `_executar_pagamento()` para suportar RLS:

```python
def pagar_lancamento(self, lancamento_id: int, ..., empresa_id: int = None) -> bool:
    if empresa_id:
        conn_context = get_db_connection(empresa_id=empresa_id)
        where_clause = "WHERE id = %s AND empresa_id = %s"  # 🔒 FILTRO
```

#### ✅ Método `cancelar_lancamento()`
**Linha 3116-3150**: Adicionado parâmetro `empresa_id` + filtro WHERE

```python
def cancelar_lancamento(self, lancamento_id: int, empresa_id: int = None) -> bool:
    if empresa_id:
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE lancamentos 
                SET status = %s, data_pagamento = NULL
                WHERE id = %s AND empresa_id = %s  -- 🔒 FILTRO
            """, (StatusLancamento.PENDENTE.value, lancamento_id, empresa_id))
```

---

### 2. Funções Wrapper (`database_postgresql.py`)

#### ✅ `obter_lancamento()` - Linha 3912
```python
def obter_lancamento(empresa_id: int, lancamento_id: int) -> Optional[Lancamento]:
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    db = DatabaseManager()
    return db.obter_lancamento(lancamento_id, empresa_id)  # 🔒 Passa empresa_id
```

#### ✅ `excluir_lancamento()` - Linha 3934
```python
def excluir_lancamento(empresa_id: int, lancamento_id: int) -> bool:
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    db = DatabaseManager()
    return db.excluir_lancamento(lancamento_id, empresa_id)  # 🔒 Passa empresa_id
```

#### ✅ `pagar_lancamento()` - Linha 3956
```python
def pagar_lancamento(empresa_id: int, lancamento_id: int, ...) -> bool:
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    db = DatabaseManager()
    return db.pagar_lancamento(lancamento_id, ..., empresa_id)  # 🔒 Passa empresa_id
```

#### ✅ `cancelar_lancamento()` - Linha 3993
```python
def cancelar_lancamento(empresa_id: int, lancamento_id: int) -> bool:
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório")
    db = DatabaseManager()
    return db.cancelar_lancamento(lancamento_id, empresa_id)  # 🔒 Passa empresa_id
```

---

### 3. Rotas API (`web_server.py`)

#### ✅ `DELETE /api/lancamentos/<id>` - Linha 3527
**ANTES:**
```python
success = db.excluir_lancamento(lancamento_id)  # ❌ SEM empresa_id
```

**DEPOIS:**
```python
# 🔒 VALIDAÇÃO DE SEGURANÇA
empresa_id = session.get('empresa_id')
if not empresa_id:
    return jsonify({'erro': 'Empresa não selecionada'}), 403

success = db_excluir_lancamento(empresa_id, lancamento_id)  # ✅ COM empresa_id
```

#### ✅ `PUT /api/lancamentos/<id>/pagar` - Linha 7347
```python
# 🔒 Obter empresa_id da sessão
empresa_id = session.get('empresa_id')
if not empresa_id:
    return jsonify({'success': False, 'error': 'empresa_id não encontrado na sessão'}), 403

success = db_pagar_lancamento(empresa_id, lancamento_id, ...)  # ✅ COM empresa_id
```

#### ✅ `POST /api/lancamentos/<id>/liquidar` - Linha 7370
```python
# 🔒 Obter empresa_id da sessão
empresa_id = session.get('empresa_id')
if not empresa_id:
    return jsonify({'success': False, 'error': 'empresa_id não encontrado na sessão'}), 403
print(f"🏢 Empresa ID: {empresa_id}")

success = db_pagar_lancamento(empresa_id, lancamento_id, ...)  # ✅ COM empresa_id
```

#### ✅ `PUT /api/lancamentos/<id>/cancelar` - Linha 7432
```python
# 🔒 Obter empresa_id da sessão
empresa_id = session.get('empresa_id')
if not empresa_id:
    return jsonify({'success': False, 'error': 'empresa_id não encontrado na sessão'}), 403

success = db_cancelar_lancamento(empresa_id, lancamento_id)  # ✅ COM empresa_id
```

---

### 4. Migração de Banco de Dados

#### 📄 `migration_add_empresa_id_lancamentos.sql`

Script PL/pgSQL completo que:

1. ✅ Adiciona coluna `empresa_id INTEGER` se não existir
2. ✅ Auto-atribui lançamentos à empresa única (se aplicável)
3. ✅ Cria índice `idx_lancamentos_empresa_id` para performance
4. ✅ Inclui instruções para adicionar FK e NOT NULL após validação
5. ✅ Fornece avisos e instruções de pós-migração

#### 🐍 `executar_migracao_seguranca.py`

Script Python para executar a migração com:

- ✅ Validação de pré-requisitos (PostgreSQL, conexão)
- ✅ Execução transacional (rollback automático em caso de erro)
- ✅ Verificação pós-migração (coluna criada, índice, estatísticas)
- ✅ Relatório detalhado com próximos passos

**Execução:**
```bash
python executar_migracao_seguranca.py
```

---

## 📊 Resumo de Mudanças

| Arquivo | Linhas Alteradas | Funções Afetadas |
|---------|------------------|------------------|
| `database_postgresql.py` | ~400 | 9 funções corrigidas |
| `web_server.py` | ~40 | 4 rotas corrigidas |
| **NOVOS ARQUIVOS** | | |
| `migration_add_empresa_id_lancamentos.sql` | 85 | Script de migração |
| `executar_migracao_seguranca.py` | 180 | Executor de migração |
| `CORRECAO_SEGURANCA_LANCAMENTOS.md` | 500+ | Esta documentação |

---

## ✅ Checklist de Verificação

### Código Corrigido
- [x] Coluna `empresa_id` adicionada ao CREATE TABLE
- [x] Filtro reativado em `listar_lancamentos()`
- [x] Parâmetro `empresa_id` adicionado em `obter_lancamento()`
- [x] Parâmetro `empresa_id` adicionado em `excluir_lancamento()`
- [x] Parâmetro `empresa_id` adicionado em `pagar_lancamento()`
- [x] Parâmetro `empresa_id` adicionado em `cancelar_lancamento()`
- [x] Funções wrapper atualizadas para passar `empresa_id`
- [x] Rotas API validam e passam `empresa_id`

### Migração de Banco
- [ ] Script SQL executado em desenvolvimento
- [ ] Lançamentos órfãos atribuídos a empresas
- [ ] Índice criado para performance
- [ ] Script SQL executado em produção (Railway)
- [ ] Verificação de dados pós-migração

### Testes
- [ ] Teste com 2 empresas diferentes
- [ ] Verificar isolamento em listagem
- [ ] Verificar isolamento em edição
- [ ] Verificar isolamento em exclusão
- [ ] Verificar isolamento em pagamento/cancelamento
- [ ] Testar tentativa de acesso cross-empresa (deve falhar)

### Deploy
- [ ] Código comitado no Git
- [ ] Push para repositório remoto
- [ ] Deploy em produção (Railway)
- [ ] Verificação pós-deploy

---

## 🚀 Instruções de Deploy

### 1. Preparação

```bash
# Verificar mudanças
git status

# Verificar diferenças
git diff database_postgresql.py
git diff web_server.py
```

### 2. Execução da Migração (OBRIGATÓRIO!)

**DESENVOLVIMENTO (Local):**
```bash
python executar_migracao_seguranca.py
```

**PRODUÇÃO (Railway):**
```bash
# Opção 1: Via Railway CLI
railway run python executar_migracao_seguranca.py

# Opção 2: Via psql direct
railway connect PostgreSQL
\i migration_add_empresa_id_lancamentos.sql
```

### 3. Validação Pós-Migração

```sql
-- Verificar coluna criada
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'lancamentos' AND column_name = 'empresa_id';

-- Verificar lançamentos sem empresa
SELECT COUNT(*) FROM lancamentos WHERE empresa_id IS NULL;

-- Se necessário, atribuir manualmente
UPDATE lancamentos SET empresa_id = <ID> WHERE <CONDIÇÃO>;
```

### 4. Commit e Deploy

```bash
# Adicionar arquivos
git add database_postgresql.py
git add web_server.py
git add migration_add_empresa_id_lancamentos.sql
git add executar_migracao_seguranca.py
git add CORRECAO_SEGURANCA_LANCAMENTOS.md

# Commit
git commit -m "fix: CRITICAL - patch data leak between companies in lancamentos

SECURITY VULNERABILITY FIXED:
- Users could view/edit/delete lancamentos from other companies
- Root cause: lancamentos table lacked empresa_id column
- Filtering was disabled with TODO comment

CHANGES:
- Added empresa_id column to lancamentos table schema
- Created SQL migration script for existing databases
- Enforced empresa_id filtering in 9 database functions
- Fixed 4 API routes to require empresa_id from session
- Added security validation warnings

MIGRATION REQUIRED:
Execute: python executar_migracao_seguranca.py

BREAKING CHANGE: All lancamento operations now require empresa_id

Refs: #SECURITY-001"

# Push
git push origin main

# Deploy automático via Railway
```

### 5. Verificação Pós-Deploy

1. Fazer login com 2 usuários de empresas diferentes
2. Criar lançamentos em cada empresa
3. Verificar que cada usuário vê APENAS seus próprios lançamentos
4. Tentar acessar URL direta de lançamento de outra empresa (deve falhar)
5. Verificar logs para erros

---

## 🔒 Medidas de Segurança Adicionais

### Recomendações Futuras

1. **Adicionar Foreign Key Constraint**
   ```sql
   ALTER TABLE lancamentos 
   ADD CONSTRAINT fk_lancamentos_empresa 
   FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE;
   ```

2. **Tornar empresa_id NOT NULL**
   ```sql
   -- Após garantir que TODOS os lançamentos têm empresa_id
   ALTER TABLE lancamentos 
   ALTER COLUMN empresa_id SET NOT NULL;
   ```

3. **Implementar Row Level Security (RLS)**
   ```sql
   ALTER TABLE lancamentos ENABLE ROW LEVEL SECURITY;
   
   CREATE POLICY lancamentos_isolation ON lancamentos
   USING (empresa_id = current_setting('app.current_empresa_id')::INTEGER);
   ```

4. **Auditoria de Acesso**
   - Logar todas as tentativas de acesso cross-empresa
   - Alertar administradores sobre acessos suspeitos

5. **Testes de Segurança Automatizados**
   - Adicionar testes unitários para isolamento multi-tenancy
   - Adicionar testes de integração com múltiplas empresas

---

## 📝 Lições Aprendidas

1. **Multi-Tenancy Precisa Ser Consistent**
   - TODAS as tabelas devem ter `empresa_id`
   - TODAS as queries devem filtrar por empresa
   - Sem exceções ou "TODOs temporários"

2. **Segurança Não Pode Ser "Para Depois"**
   - O TODO comment existia há muito tempo
   - Dados de múltiplas empresas estavam expostos

3. **Validação em Múltiplas Camadas**
   - Banco de dados: RLS + Foreign Keys
   - ORM/DAO: Filtros obrigatórios
   - API: Validação de sessão
   - Frontend: UI apropriada (último nível)

4. **Testes de Segurança São Críticos**
   - Testar isolamento entre empresas
   - Testar tentativas de acesso não autorizado
   - Automatizar esses testes

---

## 👥 Contato e Suporte

Para dúvidas sobre esta correção:
- **Documentação**: `CORRECAO_SEGURANCA_LANCAMENTOS.md`
- **Script de Migração**: `executar_migracao_seguranca.py`
- **Testes**: Executar suite de testes multi-tenancy

---

## 📅 Histórico de Versões

| Versão | Data | Descrição |
|--------|------|-----------|
| 1.0 | 2024 | Correção inicial implementada |

---

**STATUS: ✅ CORREÇÃO COMPLETA - PENDENTE MIGRAÇÃO EM PRODUÇÃO**
