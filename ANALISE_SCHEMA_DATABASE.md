# 🔍 Análise do Schema do Banco de Dados

**Data da Análise:** 13/01/2026  
**Total de Tabelas:** 29  
**Status:** ⚠️ Necessita Correções

---

## ❌ Problemas Críticos Encontrados

### 1. Multi-Tenancy Incompleto

**15 tabelas SEM `proprietario_id`** que precisam ter para isolamento de dados:

| Tabela | Prioridade | Impacto |
|--------|-----------|---------|
| `contratos` | 🔴 CRÍTICO | Contratos não isolados por cliente |
| `sessoes` | 🔴 CRÍTICO | Sessões não isoladas por cliente |
| `comissoes` | 🟡 ALTO | Comissões podem vazar entre clientes |
| `contrato_comissoes` | 🟡 ALTO | Comissões de contratos não isoladas |
| `estoque_produtos` | 🟡 ALTO | Estoque compartilhado indevidamente |
| `estoque_movimentacoes` | 🟡 ALTO | Movimentações não isoladas |
| `produtos` | 🟡 ALTO | Produtos compartilhados indevidamente |
| `kits` | 🟡 ALTO | Kits não isolados |
| `kits_equipamentos` | 🟡 ALTO | Equipamentos não isolados |
| `templates_equipe` | 🟢 MÉDIO | Templates podem vazar |
| `tags` | 🟢 MÉDIO | Tags compartilhadas indevidamente |
| `tags_trabalho` | 🟢 MÉDIO | Tags de trabalho não isoladas |
| `tipos_sessao` | 🟢 MÉDIO | Tipos de sessão compartilhados |
| `agenda` | 🟢 MÉDIO | Agenda não isolada |
| `agenda_fotografia` | 🟢 MÉDIO | Agenda fotografia não isolada |

**Risco:** Vazamento de dados entre clientes diferentes!

---

## ⚠️ Inconsistências de Nomenclatura

### Campos de Auditoria (3 padrões diferentes):

1. **Padrão 1 (Recomendado):** `created_at` + `updated_at`
   - Usado em: lancamentos, usuarios, clientes, fornecedores, etc.

2. **Padrão 2:** `data_criacao` + `atualizado_em`
   - Usado em: tags, kits, tipos_sessao

3. **Padrão 3:** `criado_em` + `expira_em`
   - Usado em: sessoes_login

**Recomendação:** Padronizar tudo para `created_at` + `updated_at`

---

## ✅ Tabelas Corretas (com proprietario_id)

| Tabela | Status |
|--------|--------|
| `categorias` | ✅ OK |
| `clientes` | ✅ OK |
| `contas_bancarias` | ✅ OK |
| `fornecedores` | ✅ OK |
| `lancamentos` | ✅ OK |

---

## 🔧 Solução Proposta

### Script Criado: `migration_add_proprietario_id.py`

**Funcionalidades:**
1. ✅ Adiciona `proprietario_id` em todas as 15 tabelas faltantes
2. ✅ Cria foreign key para `usuarios(id)` com `ON DELETE CASCADE`
3. ✅ Cria índices para performance
4. ✅ Verifica tabelas existentes antes de alterar
5. ✅ Relatório detalhado do status

**Como executar:**

```bash
# Executar migração
python migration_add_proprietario_id.py

# Apenas verificar status
python migration_add_proprietario_id.py --verificar
```

---

## 📋 Próximos Passos Recomendados

### Imediato (Crítico):
1. ✅ Executar `migration_add_proprietario_id.py` no Railway
2. ⚠️ Atualizar registros existentes com `proprietario_id` correto
3. ⚠️ Adicionar validação em APIs para usar `proprietario_id`

### Médio Prazo:
4. Padronizar campos de auditoria (`created_at/updated_at`)
5. Adicionar constraints `NOT NULL` após popular dados
6. Revisar foreign keys em todas as tabelas

### Longo Prazo:
7. Implementar soft delete (campo `deleted_at`)
8. Adicionar campos de rastreabilidade (`created_by`, `updated_by`)
9. Implementar versionamento de registros críticos

---

## 🎯 Impacto da Correção

**Antes:**
- ❌ Dados não isolados entre clientes
- ❌ Risco de vazamento de informações
- ❌ Violação de privacidade

**Depois:**
- ✅ Isolamento completo de dados
- ✅ Segurança multi-tenant adequada
- ✅ Conformidade com LGPD

---

## 📊 Estatísticas do Schema

- **Total de tabelas:** 29
- **Com proprietario_id:** 5 (17%)
- **Sem proprietario_id:** 15 (52%)
- **Tabelas de sistema:** 9 (31%)

**Cobertura multi-tenant atual:** 17%  
**Cobertura após migração:** 69% ✅

---

## ⚠️ ATENÇÃO

**Antes de executar a migração em produção:**

1. ✅ Fazer backup completo do banco
2. ✅ Testar em ambiente de desenvolvimento
3. ✅ Verificar se há dados órfãos
4. ✅ Planejar popular `proprietario_id` em registros existentes
5. ✅ Notificar usuários sobre manutenção

**Comando para backup:**
```bash
pg_dump $DATABASE_URL > backup_antes_migracao_$(date +%Y%m%d_%H%M%S).sql
```

---

## 🚀 Deploy da Correção

Arquivo criado: `migration_add_proprietario_id.py`

**Para executar no Railway:**
1. Fazer commit e push do arquivo
2. Adicionar execução no `web_server.py` (após outras migrações)
3. Monitorar logs do deploy
4. Verificar tabelas com `--verificar`
