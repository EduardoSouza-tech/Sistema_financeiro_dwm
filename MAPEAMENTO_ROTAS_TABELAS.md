# Mapeamento de Rotas → Tabelas do Sistema Financeiro

> **Arquivo de referência obrigatório.**  
> Toda nova rota adicionada ao sistema **deve** ser registrada aqui e no dicionário `ROTA_TABELA_MAP` em [`startup_health_check.py`](startup_health_check.py).

---

## Por que este mapeamento existe?

A ausência de uma tabela no banco de dados faz com que rotas lancam `500 Internal Server Error` em produção.
Este mapa serve como:

1. **Documentação** para a equipe entender quais tabelas cada rota consome.  
2. **Fonte da verdade** para o sistema de health check que verifica e auto-cria tabelas faltantes no startup.  
3. **Guia de troubleshooting** quando uma rota falha com erro de banco.

---

## Como o Health Check funciona

Ao iniciar (`web_server.py`, após `db = DatabaseManager()`), o sistema executa:

```python
from startup_health_check import verificar_saude_startup
verificar_saude_startup(db)
```

Este processo:
1. Consulta `pg_tables` para listar todas as tabelas existentes.
2. Compara com a lista `TABELAS_CRITICAS` definida em `startup_health_check.py`.
3. Se houver tabelas faltando, chama `db.criar_tabelas()` para auto-criar.
4. Varre colunas `DATE` nas tabelas críticas procurando anos fora do range Python (1–9999).
5. Loga alertas para qualquer anomalia — **sem modificar dados automaticamente**.

---

## Tabelas Críticas

| Tabela | Criada em | Módulo |
|--------|-----------|--------|
| `empresas` | `criar_tabelas()` | Multi-empresa |
| `usuarios` | `criar_tabelas()` | Autenticação |
| `permissoes` | `criar_tabelas()` | Autenticação |
| `usuario_permissoes` | `criar_tabelas()` | Autenticação |
| `sessoes_login` | `criar_tabelas()` | Autenticação |
| `log_acessos` | `criar_tabelas()` | Auditoria |
| `contas_bancarias` | `criar_tabelas()` | Financeiro |
| `categorias` | `criar_tabelas()` | Financeiro |
| `clientes` | `criar_tabelas()` | Cadastro |
| `fornecedores` | `criar_tabelas()` | Cadastro |
| `lancamentos` | `criar_tabelas()` | Financeiro |
| `transacoes_extrato` | `criar_tabelas()` | OFX/Extrato |
| `conciliacoes` | `criar_tabelas()` | Conciliação |
| `contratos` | `criar_tabelas()` | Contratos |
| `agenda` | `criar_tabelas()` | Agenda |
| `produtos` | `criar_tabelas()` | Estoque |
| `kits` | `criar_tabelas()` | Estoque |
| `kit_itens` | `criar_tabelas()` | Estoque |
| `tags` | `criar_tabelas()` | Tags |
| `templates_equipe` | `criar_tabelas()` | RH/Eventos |
| `sessoes` | `criar_tabelas()` | Sessões |
| `tipos_sessao` | `criar_tabelas()` | Sessões |
| `comissoes` | `criar_tabelas()` | Comissões |
| `sessao_equipe` | `criar_tabelas()` | Sessões |
| `funcionarios` | `criar_tabelas()` | RH |
| `eventos` | `criar_tabelas()` | Eventos |
| `funcoes_evento` | `criar_tabelas()` | Eventos |
| `evento_funcionarios` | `criar_tabelas()` | Eventos |
| `compensacoes_horas` | `criar_tabelas()` | RH |
| `ofx_filtros_memo` | inline startup | OFX |
| `google_calendar_credentials` | inline startup | Google Calendar |
| `logs_fiscais` | inline startup | Fiscal |

---

## Mapeamento Rota → Tabelas

### Autenticação & Usuários

| Rota | Método | Tabelas | Observação |
|------|--------|---------|------------|
| `/api/auth/login` | POST | `usuarios`, `sessoes_login`, `log_acessos` | |
| `/api/auth/logout` | POST | `sessoes_login` | |
| `/api/auth/verify` | GET | `sessoes_login`, `usuarios` | |
| `/api/auth/change-password` | PUT | `usuarios` | |
| `/api/auth/minhas-empresas` | GET | `usuarios`, `empresas` | |
| `/api/usuarios` | GET/POST | `usuarios`, `permissoes`, `usuario_permissoes` | |
| `/api/permissoes` | GET | `permissoes` | |

### Empresas

| Rota | Método | Tabelas |
|------|--------|---------|
| `/api/empresas` | GET/POST | `empresas` |
| `/api/empresas/<id>` | GET/PUT/DELETE | `empresas` |

### Financeiro Core

| Rota | Método | Tabelas |
|------|--------|---------|
| `/api/contas` | GET/POST | `contas_bancarias` |
| `/api/categorias` | GET/POST | `categorias` |
| `/api/lancamentos` | GET/POST | `lancamentos`, `categorias`, `contas_bancarias` |
| `/api/lancamentos/<id>` | GET/PUT/DELETE | `lancamentos` |
| `/api/transferencias` | POST | `lancamentos`, `contas_bancarias` |

### Clientes & Fornecedores

| Rota | Método | Tabelas |
|------|--------|---------|
| `/api/clientes` | GET/POST | `clientes` |
| `/api/clientes/<id>` | GET/PUT/DELETE | `clientes` |
| `/api/fornecedores` | GET/POST | `fornecedores` |
| `/api/fornecedores/<id>` | GET/PUT/DELETE | `fornecedores` |

### Extratos & Conciliação

| Rota | Método | Tabelas |
|------|--------|---------|
| `/api/extratos` | GET | `transacoes_extrato`, `contas_bancarias` |
| `/api/extratos/upload` | POST | `transacoes_extrato`, `contas_bancarias` |
| `/api/extratos/<id>/conciliar` | POST | `transacoes_extrato`, `conciliacoes`, `lancamentos` |
| `/api/regras-conciliacao` | GET/POST | `conciliacoes` |
| `/api/ofx-filtros` | GET/POST | `ofx_filtros_memo` |
| `/api/config-extrato` | GET/PUT | `contas_bancarias` |

### RH & Eventos ⚠️ (área com histórico de erros)

| Rota | Método | Tabelas | Notas |
|------|--------|---------|-------|
| `/api/funcionarios` | GET/POST | `funcionarios` | |
| `/api/funcionarios/<id>` | GET/PUT/DELETE | `funcionarios` | |
| `/api/eventos` | GET | `eventos`, `funcionarios` | ⚠️ Dados com datas inválidas causam 500 → coberto por `safe_isoformat()` |
| `/api/eventos` | POST | `eventos` | |
| `/api/eventos/<id>` | GET/PUT/DELETE | `eventos` | |
| `/api/funcoes-evento` | GET/POST | `funcoes_evento` | |
| `/api/eventos/<id>/equipe` | GET/POST | `evento_funcionarios`, `funcionarios`, `funcoes_evento` | |
| `/api/eventos/<id>/fornecedores` | GET/POST | `eventos`, `fornecedores` | |

### Comissões & Sessões

| Rota | Método | Tabelas |
|------|--------|---------|
| `/api/comissoes` | GET/POST | `comissoes` |
| `/api/sessao-equipe` | GET/POST | `sessao_equipe`, `sessoes` |
| `/api/agenda` | GET/POST | `agenda` |

### Estoque

| Rota | Método | Tabelas |
|------|--------|---------|
| `/api/estoque/produtos` | GET/POST | `produtos` |
| `/api/tags` | GET/POST | `tags` |
| `/api/templates-equipe` | GET/POST | `templates_equipe` |

### Relatórios

| Rota | Método | Tabelas |
|------|--------|---------|
| `/api/relatorios/dashboard` | GET | `lancamentos`, `contas_bancarias`, `categorias` |
| `/api/relatorios/fluxo-projetado` | GET | `lancamentos` |
| `/api/relatorios/analise-contas` | GET | `contas_bancarias`, `lancamentos` |
| `/api/relatorios/inadimplencia` | GET | `lancamentos`, `clientes` |

### NFS-e / Fiscal

| Rota | Método | Tabelas |
|------|--------|---------|
| `/api/nfse/config` | GET/POST | `nfse_config` |
| `/api/nfse/buscar` | GET | `lancamentos` |
| `/api/nfse/<id>` | GET/DELETE | `lancamentos` |

---

## Problemas Históricos e Soluções

### 1. Tabela inexistente → 500 `relation "X" does not exist`

**Causa:** Nova funcionalidade deployada sem aplicar a migration.  
**Solução automática:** O health check chama `criar_tabelas()` no startup.  
**Solução manual:** Adicionar `CREATE TABLE IF NOT EXISTS` à `criar_tabelas()` em `database_postgresql.py`.

### 2. Data com ano inválido → 500 `year XXXXX is out of range`

**Causa:** Registro inserido com data incorreta (ex: `22/02/26` interpretado como ano 22026).  
**Solução automática:** Função `safe_isoformat(d)` em `web_server.py` captura `ValueError`/`OverflowError` e retorna `str(d)`.  
**Solução manual:** Corrigir o registro no banco:
```sql
UPDATE eventos
SET data_evento = '2026-02-22'  -- corrigir para o valor correto
WHERE EXTRACT(YEAR FROM data_evento::timestamp) > 9999;
```

### 3. Rota nova retorna 500 logo após deploy

**Checklist:**
1. A tabela existe? → `SELECT * FROM pg_tables WHERE tablename = 'X';`
2. A tabela tem as colunas esperadas? → `\d nome_tabela`
3. O health check do startup logou algum erro? → Ver logs do Railway
4. A migration foi adicionada ao `criar_tabelas()` em `database_postgresql.py`?
5. A rota foi adicionada ao `ROTA_TABELA_MAP` em `startup_health_check.py`?

---

## Como adicionar uma nova rota com tabela nova

1. Adicionar `CREATE TABLE IF NOT EXISTS nova_tabela (...)` em `database_postgresql.py → criar_tabelas()`.
2. Adicionar a tabela em `TABELAS_CRITICAS` em `startup_health_check.py`.
3. Adicionar a rota em `ROTA_TABELA_MAP` em `startup_health_check.py`.
4. Registrar aqui no `MAPEAMENTO_ROTAS_TABELAS.md`.
5. Commitar antes de fazer deploy — as tabelas serão criadas automaticamente no startup.

---

*Última atualização automática: gerado via GitHub Copilot — manter atualizado a cada nova rota.*
