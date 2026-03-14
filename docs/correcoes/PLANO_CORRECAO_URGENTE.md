# 🚨 PLANO DE CORREÇÃO URGENTE - Sistema Multi-Tenancy

**Data:** 2026-02-04  
**Prioridade:** 🔴 CRÍTICA  
**Prazo:** 24 horas

---

## 📋 CHECKLIST DE CORREÇÕES

### ✅ JÁ CORRIGIDO (2 de 8)

- [x] **Clientes** - `adicionar_cliente()` com RLS e validações
- [x] **Contas Bancárias** - `adicionar_conta()` com RLS e validações

### 🔴 PENDENTE CRÍTICO (6 de 8)

- [ ] **Lançamentos** - `adicionar_lancamento()`, `atualizar_lancamento()`
- [ ] **Fornecedores** - `adicionar_fornecedor()`, `atualizar_fornecedor()`
- [ ] **Categorias** - `adicionar_categoria()`, `atualizar_categoria()`
- [ ] **Contratos** - `adicionar_contrato()`, `atualizar_contrato()`
- [ ] **Sessões (fotografia)** - `adicionar_sessao()`, `atualizar_sessao()`
- [ ] **Funcionários/Folha** - `adicionar_funcionario()`, `adicionar_folha()`

---

## 🎯 ESTRATÉGIA DE CORREÇÃO

### Padrão a Aplicar em TODAS as Funções:

```python
# ❌ PADRÃO ANTIGO (INSEGURO)
def adicionar_X(self, dados, proprietario_id=None):
    conn = self.get_connection()  # ❌ Sem RLS!
    cursor = conn.cursor()
    
    INSERT INTO tabela (nome, ..., proprietario_id)
    VALUES (%s, ..., %s)  # ❌ Sem empresa_id!

# ✅ PADRÃO NOVO (SEGURO)
def adicionar_X(self, dados, proprietario_id=None):
    # 1. Extrair empresa_id dos dados
    empresa_id = dados.get('empresa_id')
    
    # 2. Validar empresa_id obrigatório
    if not empresa_id:
        from flask import session
        empresa_id = session.get('empresa_id')
    if not empresa_id:
        raise ValueError("empresa_id é obrigatório para adicionar_X")
    
    # 3. Validar proprietario_id (se fornecido)
    if proprietario_id:
        conn_check = self.get_connection()
        cursor_check = conn_check.cursor()
        cursor_check.execute("SELECT id FROM usuarios WHERE id = %s", (proprietario_id,))
        if not cursor_check.fetchone():
            cursor_check.close()
            return_to_pool(conn_check)
            raise ValueError(f"proprietario_id={proprietario_id} não existe")
        cursor_check.close()
        return_to_pool(conn_check)
    
    # 4. Usar get_db_connection com RLS
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # 5. INSERT com empresa_id
        INSERT INTO tabela (nome, ..., proprietario_id, empresa_id)
        VALUES (%s, ..., %s, %s)
        
        conn.commit()
    
    return id
```

### Padrão para Rotas Web:

```python
# ❌ PADRÃO ANTIGO
@app.route('/api/X', methods=['POST'])
@require_permission('X_create')
def adicionar_X():
    data = request.json
    proprietario_id = getattr(request, 'filtro_cliente_id', None)  # ❌ Errado!
    x_id = db.adicionar_X(data, proprietario_id=proprietario_id)

# ✅ PADRÃO NOVO
@app.route('/api/X', methods=['POST'])
@require_permission('X_create')
def adicionar_X():
    # 1. Validar sessão e empresa
    from flask import session
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'error': 'Empresa não selecionada'}), 403
    
    data = request.json
    
    # 2. Validar campos obrigatórios
    if not data.get('nome'):  # Ajustar campo conforme necessidade
        return jsonify({'error': 'Nome é obrigatório'}), 400
    
    # 3. Adicionar empresa_id aos dados
    data['empresa_id'] = empresa_id
    
    # 4. proprietario_id = usuario.id (se cliente)
    usuario = get_usuario_logado()
    proprietario_id = usuario.get('id') if usuario.get('tipo') == 'cliente' else None
    
    # 5. Logs
    print(f"\n🔍 [POST /api/X] Adicionando:")
    print(f"   - empresa_id: {empresa_id}")
    print(f"   - proprietario_id: {proprietario_id}")
    
    # 6. Executar
    x_id = db.adicionar_X(data, proprietario_id=proprietario_id)
    
    print(f"   ✅ Criado com ID: {x_id}")
    return jsonify({'success': True, 'id': x_id})
```

---

## 📝 SCRIPT DE CORREÇÃO AUTOMÁTICA

### 1. Auditoria Rápida

Execute este SQL no banco para identificar registros sem `empresa_id`:

```sql
-- Verificar quantos registros estão sem empresa_id
SELECT 
    'clientes' as tabela, 
    COUNT(*) as sem_empresa_id 
FROM clientes 
WHERE empresa_id IS NULL

UNION ALL

SELECT 'fornecedores', COUNT(*) 
FROM fornecedores 
WHERE empresa_id IS NULL

UNION ALL

SELECT 'lancamentos', COUNT(*) 
FROM lancamentos 
WHERE empresa_id IS NULL

UNION ALL

SELECT 'contas_bancarias', COUNT(*) 
FROM contas_bancarias 
WHERE empresa_id IS NULL

UNION ALL

SELECT 'categorias', COUNT(*) 
FROM categorias 
WHERE empresa_id IS NULL

UNION ALL

SELECT 'contratos', COUNT(*) 
FROM contratos 
WHERE empresa_id IS NULL

UNION ALL

SELECT 'sessoes', COUNT(*) 
FROM sessoes 
WHERE empresa_id IS NULL

UNION ALL

SELECT 'funcionarios', COUNT(*) 
FROM funcionarios 
WHERE empresa_id IS NULL;
```

### 2. Limpeza de Dados

Se houver registros sem `empresa_id`, decidir:

**Opção A: Atribuir empresa padrão**
```sql
-- Atribuir à primeira empresa disponível
UPDATE clientes SET empresa_id = 1 WHERE empresa_id IS NULL;
UPDATE fornecedores SET empresa_id = 1 WHERE empresa_id IS NULL;
UPDATE lancamentos SET empresa_id = 1 WHERE empresa_id IS NULL;
UPDATE contas_bancarias SET empresa_id = 1 WHERE empresa_id IS NULL;
UPDATE categorias SET empresa_id = 1 WHERE empresa_id IS NULL;
UPDATE contratos SET empresa_id = 1 WHERE empresa_id IS NULL;
UPDATE sessoes SET empresa_id = 1 WHERE empresa_id IS NULL;
UPDATE funcionarios SET empresa_id = 1 WHERE empresa_id IS NULL;
```

**Opção B: Deletar (cuidado!)**
```sql
-- BACKUP PRIMEIRO!
DELETE FROM clientes WHERE empresa_id IS NULL;
DELETE FROM fornecedores WHERE empresa_id IS NULL;
-- ... etc
```

### 3. Adicionar Constraints NOT NULL

Depois de limpar dados:

```sql
-- Tornar empresa_id obrigatório
ALTER TABLE clientes ALTER COLUMN empresa_id SET NOT NULL;
ALTER TABLE fornecedores ALTER COLUMN empresa_id SET NOT NULL;
ALTER TABLE lancamentos ALTER COLUMN empresa_id SET NOT NULL;
ALTER TABLE contas_bancarias ALTER COLUMN empresa_id SET NOT NULL;
ALTER TABLE categorias ALTER COLUMN empresa_id SET NOT NULL;
ALTER TABLE contratos ALTER COLUMN empresa_id SET NOT NULL;
ALTER TABLE sessoes ALTER COLUMN empresa_id SET NOT NULL;
ALTER TABLE funcionarios ALTER COLUMN empresa_id SET NOT NULL;
```

### 4. Trigger de Validação Global

```sql
-- Criar função de validação
CREATE OR REPLACE FUNCTION validate_empresa_id()
RETURNS TRIGGER AS $$
BEGIN
    -- Validar empresa_id não é NULL
    IF NEW.empresa_id IS NULL THEN
        RAISE EXCEPTION 'empresa_id é obrigatório para tabela %', TG_TABLE_NAME;
    END IF;
    
    -- Validar que empresa existe
    IF NOT EXISTS (SELECT 1 FROM empresas WHERE id = NEW.empresa_id AND ativo = TRUE) THEN
        RAISE EXCEPTION 'empresa_id=% não existe ou está inativa', NEW.empresa_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar em todas as tabelas
CREATE TRIGGER validate_empresa_trigger
BEFORE INSERT OR UPDATE ON clientes
FOR EACH ROW EXECUTE FUNCTION validate_empresa_id();

CREATE TRIGGER validate_empresa_trigger
BEFORE INSERT OR UPDATE ON fornecedores
FOR EACH ROW EXECUTE FUNCTION validate_empresa_id();

CREATE TRIGGER validate_empresa_trigger
BEFORE INSERT OR UPDATE ON lancamentos
FOR EACH ROW EXECUTE FUNCTION validate_empresa_id();

CREATE TRIGGER validate_empresa_trigger
BEFORE INSERT OR UPDATE ON contas_bancarias
FOR EACH ROW EXECUTE FUNCTION validate_empresa_id();

CREATE TRIGGER validate_empresa_trigger
BEFORE INSERT OR UPDATE ON categorias
FOR EACH ROW EXECUTE FUNCTION validate_empresa_id();

CREATE TRIGGER validate_empresa_trigger
BEFORE INSERT OR UPDATE ON contratos
FOR EACH ROW EXECUTE FUNCTION validate_empresa_id();

CREATE TRIGGER validate_empresa_trigger
BEFORE INSERT OR UPDATE ON sessoes
FOR EACH ROW EXECUTE FUNCTION validate_empresa_id();

CREATE TRIGGER validate_empresa_trigger
BEFORE INSERT OR UPDATE ON funcionarios
FOR EACH ROW EXECUTE FUNCTION validate_empresa_id();
```

---

## 🔍 ORDEM DE CORREÇÃO RECOMENDADA

### Prioridade 1 (Mais Usadas):
1. ✅ **Clientes** (FEITO)
2. ✅ **Contas Bancárias** (FEITO)
3. **Lançamentos** ← Próximo
4. **Fornecedores**

### Prioridade 2 (Médio Uso):
5. **Categorias**
6. **Contratos**

### Prioridade 3 (Menos Usadas):
7. **Sessões (fotografia)**
8. **Funcionários/Folha**

---

## ⚠️ PONTOS DE ATENÇÃO

### 1. Testes Após Cada Correção

Para cada função corrigida, testar:

```python
# Teste manual via Railway logs
# 1. Criar registro
POST /api/X
{
    "nome": "Teste",
    ...
}

# Verificar logs:
# - "empresa_id: 19" (da sessão)
# - "proprietario_id: 9" (usuario.id)
# - "✅ Criado com ID: X"

# 2. Verificar no banco
SELECT * FROM tabela WHERE id = X;
-- Deve ter empresa_id preenchido!

# 3. Tentar ver de outra empresa
# Logar com empresa_id=20
GET /api/X
-- NÃO deve ver o registro criado por empresa_id=19
```

### 2. Rollback Plan

Se algo der errado:

```bash
# 1. Reverter último commit
git revert HEAD

# 2. Push
git push

# 3. Railway faz deploy automático

# OU manual:
git reset --hard HEAD~1
git push --force
```

### 3. Backup Antes de Migrations

```bash
# No Railway, fazer backup do banco:
# Settings > Database > Create Backup
```

---

## 📊 MÉTRICAS DE PROGRESSO

### Situação Atual:
- ✅ 2/8 funções corrigidas (25%)
- ⚠️ 6/8 ainda vulneráveis (75%)
- 🔴 Zero testes automatizados

### Meta Fase 1 (24h):
- 🎯 8/8 funções corrigidas (100%)
- 🎯 Constraints NOT NULL aplicadas
- 🎯 Triggers de validação ativos

### Meta Fase 2 (48h):
- 🎯 Testes automatizados (50% coverage)
- 🎯 CI/CD com validação automática

### Meta Fase 3 (72h):
- 🎯 Auditoria completa
- 🎯 Documentação atualizada
- 🎯 Zero vulnerabilidades conhecidas

---

## 🚀 PRÓXIMA AÇÃO

**AGORA:** Vou corrigir `adicionar_lancamento()` e `adicionar_fornecedor()` seguindo o padrão estabelecido.

**Deseja que eu prossiga com as correções?**

Digite:
- ✅ "SIM" - Para corrigir TODAS as 6 funções restantes agora
- 📝 "REVISAR" - Para revisar o plano primeiro
- ⏸️ "PAUSAR" - Para pausar e testar as 2 já corrigidas primeiro

---

**IMPORTANTE:** Cada correção será commitada individualmente para facilitar rollback se necessário.
