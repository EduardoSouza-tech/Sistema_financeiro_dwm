# 🔧 FIX — Importação de Clientes/Fornecedores entre Empresas

**Data:** 23/03/2026  
**Gravidade:** 🟠 ALTA — Feature inutilizável  
**Status:** ✅ Resolvido  
**Commits:** `18a8102` → `2e8b240` → `9cc4b46` → `6b84de8` → `8d46705` → `2b1e6bd` → `b1a403d`

---

## 📋 Descrição da Feature

Implementação de botão **"📥 Importar de Outra Empresa"** nas seções de Clientes e Fornecedores, permitindo copiar cadastros de uma empresa do mesmo usuário para a empresa atual, sem precisar recadastrá-los manualmente.

### Endpoints criados
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/clientes/empresas-disponiveis` | Lista empresas com clientes disponíveis para importação |
| POST | `/api/clientes/importar-de-empresa` | Importa clientes de uma empresa origem para a destino |
| GET | `/api/fornecedores/empresas-disponiveis` | Lista empresas com fornecedores disponíveis |
| POST | `/api/fornecedores/importar-de-empresa` | Importa fornecedores entre empresas |

---

## 🐛 Bugs encontrados e corrigidos (em ordem cronológica)

---

### Bug 1 — `db.listar_clientes()` retornava 0 registros de outra empresa

**Commit:** `2e8b240`

**Causa:** A implementação inicial usava `db.listar_clientes()` com `filtro_cliente_id` da sessão atual. Isso aplica RLS (Row Level Security) filtrado pela empresa logada — nunca retorna dados de outra empresa.

**Correção:** Reescrita dos 4 endpoints usando SQL direto via `get_db_connection(allow_global=True)` (sem RLS).

---

### Bug 2 — `SAVEPOINT can only be used in transaction blocks`

**Commit:** `9cc4b46`

**Causa:** `get_db_connection(allow_global=True)` retorna conexão com `conn.autocommit = True`. Em autocommit, não há bloco de transação ativo — o PostgreSQL rejeita `SAVEPOINT`.

**Correção inicial:** Adicionado `cur.execute("BEGIN")` antes do loop de SAVEPOINTs.

---

### Bug 3 — `conn.commit()` não persistia os dados (no-op)

**Commit:** `6b84de8`

**Causa:** Com `conn.autocommit = True`, o psycopg2 delega cada statement diretamente ao banco. `conn.commit()` é ignorado silenciosamente — os INSERTs caíam no bloco `BEGIN` manual mas nunca eram confirmados, sendo revertidos ao devolver a conexão ao pool.

**Correção:** Substituído `conn.commit()` por `cur.execute("COMMIT")` — commit enviado diretamente via SQL.

---

### Bug 4 — Trigger `validate_empresa_clientes` bloqueava todos os INSERTs

**Commit:** `8d46705`

**Causa:** O banco possui um trigger BEFORE INSERT em `clientes`:

```sql
CREATE FUNCTION validate_empresa_id() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.empresa_id != current_setting('app.current_empresa_id')::integer THEN
        RAISE EXCEPTION 'empresa_id (%) não corresponde à empresa da sessão (%)',
            NEW.empresa_id, current_setting('app.current_empresa_id')::integer;
    END IF;
END;
```

Com `allow_global=True`, `app.current_empresa_id` nunca é definido → exception em cada INSERT. Os erros eram capturados pelo SAVEPOINT silenciosamente — `importados=0`, `erros=[...]` internamente, mas sem log visível.

Fornecedores **não** tem esse trigger → por isso fornecedores funcionava e clientes não.

**Correção:** Adicionado `set_config('app.current_empresa_id', empresa_destino_id, true)` após `BEGIN`.

---

### Bug 5 — `UNIQUE(cpf_cnpj)` global impedia importação quando CPF já existia em qualquer empresa

**Commits:** `2b1e6bd` + `b1a403d`

**Causa:** A constraint criada pela migration `migration_cpf_cnpj_unique.sql` era:

```sql
ALTER TABLE clientes ADD CONSTRAINT clientes_cpf_cnpj_key UNIQUE (cpf_cnpj);
```

Constraint **global** — o mesmo CPF/CNPJ não podia existir em duas empresas diferentes. Resultado: ao importar 8 clientes da CONSERVADORA NEVES para ALVES E SOUZA, todos tinham CPF já presente no banco (vindos da outra empresa) → todos caíam no SAVEPOINT rollback → `importados=0, duplicados=0, erros=8` (silenciosos).

Na tentativa anterior (`2b1e6bd`) a solução foi checar CPFs globalmente antes de inserir, mas isso tratava o sintoma — os clientes eram marcados como "já existiam" (8 já existiam) mas não eram importados.

**Correção definitiva (`b1a403d`):** Migration automática no startup (`criar_tabelas()`):

```python
# Remove constraint global
ALTER TABLE clientes DROP CONSTRAINT IF EXISTS clientes_cpf_cnpj_key;
# Adiciona constraint por-empresa (multi-tenant correto)
ALTER TABLE clientes ADD CONSTRAINT clientes_cpf_cnpj_empresa_key UNIQUE (cpf_cnpj, empresa_id);
# Idem para fornecedores
ALTER TABLE fornecedores DROP CONSTRAINT IF EXISTS fornecedores_cpf_cnpj_key;
ALTER TABLE fornecedores ADD CONSTRAINT fornecedores_cpf_cnpj_empresa_key UNIQUE (cpf_cnpj, empresa_id);
```

A lógica de checagem de duplicados no import foi simplificada de volta para verificar apenas dentro da empresa destino.

---

## 🏗️ Arquitetura final do endpoint de importação

```python
@app.route('/api/clientes/importar-de-empresa', methods=['POST'])
@require_permission('clientes_create')
def importar_clientes_de_empresa():
    with get_db_connection(allow_global=True) as conn:
        cur = conn.cursor()

        # 1. Buscar clientes da origem (autocommit=True, sem RLS → acessa outra empresa)
        cur.execute("SELECT * FROM clientes WHERE ativo=TRUE AND empresa_id=%s", (origem,))
        clientes_origem = cur.fetchall()

        # 2. Desativar autocommit para usar transação nativa do psycopg2
        conn.autocommit = False
        try:
            # 3. SET LOCAL: satisfaz trigger validate_empresa_clientes
            cur.execute("SELECT set_config('app.current_empresa_id', %s, true)", (str(destino),))

            # 4. Checar duplicados na empresa destino
            cur.execute("SELECT cpf_cnpj, nome FROM clientes WHERE empresa_id=%s", (destino,))
            cpfs_destino = {r['cpf_cnpj'] for r in cur.fetchall() if r.get('cpf_cnpj')}

            # 5. Inserir com SAVEPOINT por linha (isolação de erros individuais)
            for cli in clientes_origem:
                if cli['cpf_cnpj'] in cpfs_destino:
                    duplicados += 1; continue
                cur.execute("SAVEPOINT sp_cli")
                cur.execute("INSERT INTO clientes (...) VALUES (...)", (...))
                cur.execute("RELEASE SAVEPOINT sp_cli")
                importados += 1

            conn.commit()           # commit real (autocommit=False)
        except:
            conn.rollback()
            raise
        finally:
            conn.autocommit = True  # restaurar para o pool
```

---

## ⚠️ Lição aprendida

### `get_db_connection(allow_global=True)` = autocommit mode

| Comportamento | Com autocommit=True | Com autocommit=False |
|---|---|---|
| `conn.commit()` | **no-op** (ignorado) | Envia COMMIT real |
| `conn.rollback()` | **no-op** (ignorado) | Envia ROLLBACK real |
| `SAVEPOINT` | Requer `BEGIN` manual | Funciona nativamente |
| `SET LOCAL` / `set_config(..., true)` | Escopo imprevisível | Válido até o commit/rollback |

**Regra prática:** Uso de SAVEPOINTs + transações manuais com `allow_global=True` deve sempre fazer:
```python
conn.autocommit = False
try:
    # operações...
    conn.commit()
except:
    conn.rollback()
    raise
finally:
    conn.autocommit = True  # restaurar para o pool
```

### Constraint UNIQUE deve ser por-empresa em sistema multi-tenant

`UNIQUE(cpf_cnpj)` global é correto apenas se o sistema tiver **uma única empresa**. Em multi-tenant, a constraint deve ser `UNIQUE(cpf_cnpj, empresa_id)`.

---

## 📂 Arquivos modificados

| Arquivo | Tipo de mudança |
|---------|----------------|
| `web_server.py` | 4 novos endpoints + lógica de importação corrigida |
| `templates/interface_nova.html` | Botões + modais + funções JS de importação |
| `database_postgresql.py` | Migration automática: UNIQUE global → UNIQUE por-empresa |
