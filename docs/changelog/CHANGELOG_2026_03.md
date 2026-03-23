# 📋 Changelog - Atualizações (Março 2026)

---

## 🔧 FIX — Importação de Clientes/Fornecedores entre Empresas (23/03/2026)

### Commits
- `18a8102` — feat: endpoints de importação de clientes/fornecedores entre empresas
- `2e8b240` — fix: usar SQL direto com allow_global=True (listar_clientes() filtrava por RLS)
- `9cc4b46` — fix: adicionar BEGIN explícito antes de SAVEPOINT (autocommit mode)
- `6b84de8` — fix: usar cur.execute("COMMIT") ao invés de conn.commit() (no-op em autocommit)
- `8d46705` — fix: setar app.current_empresa_id para satisfazer trigger validate_empresa_clientes
- `2b1e6bd` — fix: refatorar para autocommit=False nativo (SET LOCAL + SAVEPOINTs corretos)
- `b1a403d` — fix: converter UNIQUE(cpf_cnpj) global → UNIQUE(cpf_cnpj, empresa_id) por-empresa

### Problema
Botão **"📥 Importar de Outra Empresa"** nas seções de Clientes e Fornecedores não importava nenhum registro — sempre retornava `0 importados`.

### Causa Raiz (cadeia de 5 bugs)

1. `db.listar_clientes()` usa RLS → retornava 0 registros de outra empresa
2. `SAVEPOINT` falhava em modo autocommit sem `BEGIN` explícito
3. `conn.commit()` é no-op com `autocommit=True` — dados nunca persistidos
4. Trigger `validate_empresa_clientes` bloqueava INSERTs sem `app.current_empresa_id` setado
5. Constraint `UNIQUE(cpf_cnpj)` era **global** — mesmo CPF não podia existir em duas empresas

### Solução
- 4 endpoints criados usando SQL direto + `allow_global=True`
- Transação gerenciada com `conn.autocommit = False` nativo
- `set_config('app.current_empresa_id', destino, true)` para satisfazer trigger
- Migration automática no startup: `UNIQUE(cpf_cnpj)` → `UNIQUE(cpf_cnpj, empresa_id)`

**Documentação completa:** `docs/correcoes/FIX_IMPORTACAO_CLIENTES_FORNECEDORES.md`

---
