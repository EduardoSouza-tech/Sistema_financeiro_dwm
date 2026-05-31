# ⏱️ Documentação Completa — Controle de Horas

**Última atualização:** 2026-05-31  
**Stack:** Flask + PostgreSQL (Railway) + JavaScript

---

## 1. Visão Geral

O **Controle de Horas** rastreia o consumo de horas contratadas por cliente ao longo do tempo. Cada contrato que possui `horas_mensais > 0` ativa automaticamente o controle, acumulando horas à medida que sessões são concluídas ou finalizadas.

### Conceito Central

```
Contrato (horas_totais)
   │
   ├── Sessão concluída → deduz horas_utilizadas
   ├── Sessão finalizada → deduz horas_utilizadas
   └── Horas extras → acumulam em horas_extras (quando utilizado > total)
```

O saldo em tempo real é sempre:

$$\text{horas\_restantes} = \text{horas\_totais} - \text{horas\_utilizadas}$$

$$\text{percentual\_utilizado} = \frac{\text{horas\_utilizadas}}{\text{horas\_totais}} \times 100$$

---

## 2. Como o Controle é Ativado por Tipo de Contrato

### 2.1 Contrato Mensal

- `horas_totais = horas_mensais × quantidade_meses`
- `controle_horas_ativo = True` se `horas_mensais > 0`

**Exemplo:** 8h/mês × 12 meses = **96h contratadas**

### 2.2 Contrato Único

- `horas_totais = horas_mensais × quantidade_meses` (mesma lógica)
- `controle_horas_ativo = True` se `horas_mensais > 0`

### 2.3 Contrato Pacote

- `horas_totais = quantidade_pacotes × horas_por_pacote`
- `controle_horas_ativo = True` **sempre** que `horas_totais > 0`
- Campos reutilizados: `quantidade_meses` = quantidade de pacotes; `horas_mensais` = horas por pacote

```
Tipo Pacote: 3 pacotes × 20h = 60h total
```

---

## 3. Banco de Dados

### 3.1 Colunas da Tabela `contratos` (Controle de Horas)

| Coluna | Tipo | Default | Descrição |
|---|---|---|---|
| `horas_totais` | DECIMAL(10,2) | 0 | Total de horas contratadas (calculado na criação/edição) |
| `horas_utilizadas` | DECIMAL(10,2) | 0 | Horas consumidas por sessões finalizadas/concluídas |
| `horas_extras` | DECIMAL(10,2) | 0 | Horas trabalhadas acima do saldo disponível |
| `controle_horas_ativo` | BOOLEAN | false | Se o contrato tem controle de horas ativo |

> Campos virtuais calculados no Python (não persistidos): `horas_restantes`, `percentual_utilizado`

### 3.2 Tabela `compensacoes_horas` (Auditoria de Transferências)

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | SERIAL PK | Identificador |
| `empresa_id` | INTEGER | FK empresa |
| `contrato_origem_id` | INTEGER FK | Contrato que doou as horas |
| `contrato_destino_id` | INTEGER FK | Contrato que recebeu as horas |
| `quantidade_horas` | DECIMAL(10,2) | Quantidade transferida |
| `observacao` | TEXT | Motivo da compensação |
| `usuario_id` | INTEGER FK | Usuário que executou |
| `created_at` | TIMESTAMP | Data/hora da operação |

### 3.3 Campos Relevantes na Tabela `sessoes`

| Coluna | Tipo | Descrição |
|---|---|---|
| `duracao` | INTEGER | Duração em **minutos** (`quantidade_horas × 60`) |
| `horas_trabalhadas` | DECIMAL(10,2) | Horas confirmadas ao finalizar (opcional — usa `duracao` se null) |
| `finalizada_em` | TIMESTAMP | Momento da finalização |
| `status` | VARCHAR | Status atual (controla quando deduzir horas) |

### 3.4 `observacoes` JSON do Contrato — Campos Relacionados

O campo `contratos.observacoes` é um JSON com metadados. Os campos relacionados ao controle de horas são:

```json
{
  "tipo": "Mensal",
  "horas_mensais": 8,
  "quantidade_meses": 12,
  "horas_acumuladas_inicial": 0,
  "horas_acumuladas_atual": 0,
  "historico_mensal": {
    "2026-03": {
      "nf_emitida": true,
      "pago": false,
      "pulado": false,
      "horas_ajuste": 10.0,
      "valor_mes": 3500.0,
      "nf_status": "emitida",
      "pagamento_status": "pago",
      "entrega_status": "entregue",
      "data_pagamento": "2026-03-15",
      "sessoes_entrega": {
        "42": "entregue",
        "43": "parcial"
      }
    }
  },
  "historico_pacote": {
    "42": {
      "nf_status": "emitida",
      "pagamento_status": "pago",
      "horas_ajuste": 8.0,
      "data_pagamento": "2026-03-20"
    }
  }
}
```

---

## 4. Lógica de Dedução de Horas

### 4.1 Ao Concluir Sessão (`status → 'concluida'`)

Executada em `atualizar_status_sessao()` (`database_postgresql.py`):

```python
saldo_atual = horas_totais - horas_utilizadas

if saldo_atual >= horas_trabalhadas:
    horas_deduzidas = horas_trabalhadas
    horas_extras_adicional = 0
else:
    horas_deduzidas = max(saldo_atual, 0)
    horas_extras_adicional = horas_trabalhadas - horas_deduzidas

UPDATE contratos SET
    horas_utilizadas = horas_utilizadas + horas_deduzidas,
    horas_extras     = horas_extras + horas_extras_adicional
WHERE id = contrato_id
```

Horas utilizadas na dedução = `dados_json.quantidade_horas` da sessão.

**Retorno para o frontend:**
```json
{
  "success": true,
  "controle_horas_ativo": true,
  "horas_deduzidas": 8.0,
  "horas_extras": 0.0,
  "saldo_restante": 24.0
}
```

### 4.2 Ao Finalizar Sessão (`POST /api/sessoes/<id>/finalizar`)

Executada em `finalizar_sessao()` (`database_postgresql.py`). Mesma lógica de dedução, mas:
- Aceita `horas_trabalhadas` no body (override manual das horas)
- Aceita `numero_nf` no body
- Salva `finalizada_em = CURRENT_TIMESTAMP` e `numero_nf`

### 4.3 Sincronização por Recálculo (`_sincronizar_horas_contrato`)

Chamada ao criar ou deletar sessão. Recalcula do zero:

```sql
UPDATE contratos
SET horas_utilizadas = (
    SELECT COALESCE(SUM(duracao) / 60.0, 0)
    FROM sessoes
    WHERE contrato_id = %s AND status != 'cancelada'
)
WHERE id = %s
```

> ⚠️ Esta sincronização substitui o valor acumulado — não soma incrementalmente.

### 4.4 Trigger SQL (Migration)

O arquivo `migration_controle_horas.sql` cria um trigger `trigger_deduzir_horas_sessao` que dispara quando `sessoes.status` muda para `'finalizada'`. Este trigger é **legado** — a lógica atual está em Python (`atualizar_status_sessao` para `'concluida'` e `finalizar_sessao`).

---

## 5. API REST — Rotas Relacionadas

### 5.1 Contratos

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| GET | `/api/contratos` | `contratos_view` | Lista contratos com `horas_totais`, `horas_utilizadas`, `horas_restantes`, `percentual_utilizado` |
| POST | `/api/contratos` | `contratos_edit` | Cria contrato — calcula e salva `horas_totais` e `controle_horas_ativo` |
| PUT | `/api/contratos/<id>` | `contratos_edit` | Atualiza contrato — preserva `historico_mensal` existente |
| POST | `/api/contratos/<origem_id>/compensar-horas` | `contratos_edit` | Transfere horas entre contratos do mesmo cliente |
| GET | `/api/contratos/compensacoes-horas` | `contratos_view` | Histórico de compensações |
| PATCH | `/api/contratos/<id>/historico-mes` | — | Atualiza estado de um mês (NF, pagamento, `horas_ajuste`) |
| PATCH | `/api/contratos/<id>/observacoes` | — | Atualiza `horas_acumuladas_inicial` / `horas_acumuladas_atual` |
| PATCH | `/api/contratos/<id>/historico-sessao` | — | Atualiza estado de uma sessão no histórico do Pacote |

### 5.2 Sessões (dedução de horas)

| Método | Rota | Deduz Horas? | Observação |
|---|---|---|---|
| PUT | `/api/sessoes/<id>/status` com `status=concluida` | ✅ Sim | Via `atualizar_status_sessao` |
| POST | `/api/sessoes/<id>/finalizar` | ✅ Sim | Aceita `horas_trabalhadas` override |
| DELETE | `/api/sessoes/<id>` | 🔄 Recalcula | Chama `_sincronizar_horas_contrato` |
| POST | `/api/sessoes` | 🔄 Recalcula | Chama `_sincronizar_horas_contrato` |

### 5.3 Relatórios

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| GET | `/api/relatorios/controle-horas` | `contratos_view` | Resumo + detalhamento por contrato com sessões |
| GET | `/api/relatorios/controle-horas/exportar/pdf` | `contratos_view` | Exportar PDF |
| GET | `/api/relatorios/controle-horas/exportar/excel` | `contratos_view` | Exportar Excel (.xlsx) |

---

## 6. Detalhes dos Endpoints

### 6.1 `POST /api/contratos/<origem_id>/compensar-horas`

Transfere horas de um contrato para outro do **mesmo cliente**.

**Body:**
```json
{
  "contrato_destino_id": 33,
  "quantidade_horas": 10.5,
  "observacao": "Excesso de horas em eventos de março"
}
```

**Validações:**
- `quantidade_horas > 0`
- `origem_id != destino_id`
- Ambos contratos pertencem ao mesmo `cliente_id`
- `saldo_disponível_origem >= quantidade_horas` (saldo = `horas_totais - horas_utilizadas`)

**Operação:**
1. `contratos.horas_totais -= quantidade_horas` (origem)
2. `contratos.horas_totais += quantidade_horas` (destino)
3. Insere registro em `compensacoes_horas`

**Response (200):**
```json
{
  "success": true,
  "message": "Compensadas 10.5h com sucesso",
  "data": {
    "compensacao_id": 7,
    "origem": {
      "contrato_id": 32,
      "numero": "2025/01",
      "horas_totais": 85.5,
      "horas_utilizadas": 72.0,
      "horas_extras": 0,
      "horas_restantes": 13.5
    },
    "destino": {
      "contrato_id": 33,
      "numero": "2025/02",
      "horas_totais": 50.5,
      "horas_utilizadas": 20.0,
      "horas_extras": 0,
      "horas_restantes": 30.5
    },
    "quantidade_compensada": 10.5
  }
}
```

---

### 6.2 `GET /api/relatorios/controle-horas`

**Response (200):**
```json
{
  "success": true,
  "dados": {
    "resumo": {
      "total_contratos": 15,
      "contratos_ativos": 12,
      "contratos_com_controle_horas": 8,
      "total_sessoes": 47,
      "total_horas_contratadas": 640.0,
      "total_horas_utilizadas": 423.5,
      "total_horas_restantes": 216.5,
      "total_horas_extras": 0.0
    },
    "contratos": [
      {
        "id": 32,
        "numero": "2025/01",
        "descricao": "Mensal Fotografia 2025",
        "valor_contrato": 3500.0,
        "data_vigencia_inicio": "2025-01-01",
        "data_vigencia_fim": "2025-12-31",
        "status_pagamento": "ativo",
        "horas_totais": 96.0,
        "horas_utilizadas": 72.0,
        "horas_extras": 0.0,
        "horas_restantes": 24.0,
        "percentual_utilizado": 75.0,
        "controle_horas_ativo": true,
        "cliente_nome": "Studio XYZ",
        "total_sessoes": 9,
        "sessoes": [
          {
            "id": 42,
            "data": "2025-03-15",
            "descricao": "Ensaio casamento",
            "status": "concluida",
            "horas_trabalhadas": 8.0,
            "horario": "09:00 AS 17:00",
            "cliente_nome": "Studio XYZ"
          }
        ]
      }
    ]
  }
}
```

> **Nota:** `horas_utilizadas` no relatório é calculado em tempo real somando `sessoes.duracao / 60.0` (não usa `contratos.horas_utilizadas`). Isso garante dados precisos mesmo que a coluna esteja desatualizada.

---

### 6.3 `PATCH /api/contratos/<id>/historico-mes`

Atualiza o estado de um mês no histórico do contrato.

**Body:**
```json
{ "mes": "2026-03", "campo": "horas_ajuste", "valor": 10.5 }
```

**Campos permitidos:**

| Campo | Tipo | Valores aceitos | Descrição |
|---|---|---|---|
| `nf_emitida` | bool | `true`/`false` | NF emitida no mês |
| `pago` | bool | `true`/`false` | Pagamento recebido |
| `pulado` | bool | `true`/`false` | Mês pulado (sem faturamento) |
| `nf_status` | string | `emitida`, `no_prazo`, `atrasada`, `na`, `` | Status da NF |
| `pagamento_status` | string | `pago`, `parcial`, `atrasado`, `nao_pago`, `` | Status do pagamento |
| `entrega_status` | string | `entregue`, `parcial`, `atrasada`, `nao_realizada`, `` | Status de entrega |
| `horas_ajuste` | float | qualquer número | Override manual das horas daquele mês |
| `valor_mes` | float | qualquer número | Override do valor/NF daquele mês |
| `data_pagamento` | string | data `YYYY-MM-DD` ou `` | Data do pagamento |
| `sessao_entrega` | JSON | `{"sessao_id": "42", "status": "entregue"}` | Estado de entrega por sessão |

> `mes = "unico"` é aceito para contratos do tipo Único (sem controle mensal).

---

## 7. Frontend

### 7.1 Aba "Controle de Horas" (`static/app.js`)

Tela acessível pela navegação principal (`tab: controle-horas`).

**Funções principais:**

| Função | Linha aprox. | Descrição |
|---|---|---|
| `loadControleHoras()` | 2970 | Carrega e renderiza o relatório completo |
| `abrirCompensacaoHoras(contratoId)` | 3146 | Abre modal para transferir horas |
| `executarCompensacaoHoras(contratoId)` | 3339 | Executa a transferência via API |
| `fecharCompensacaoHoras()` | 3411 | Fecha modal de compensação |
| `exportarControleHorasPDF()` | 3128 | Download do PDF |
| `exportarControleHorasExcel()` | 3136 | Download do Excel |

**Cards do resumo:**
1. Total de Contratos (contratos ativos)
2. Com Controle de Horas (total de sessões vinculadas)
3. Horas Contratadas
4. Horas Utilizadas (% usado)
5. Horas Restantes
6. Horas Extras

**Tabela de contratos — indicadores visuais:**

| Condição | Ícone | Cor | Texto |
|---|---|---|---|
| `horas_extras > 0` | ⚠️ | Vermelho | Extras |
| `horas_restantes ≤ 5` | ⚡ | Laranja | Baixo |
| Normal | ✅ | Verde | OK |

**Barra de progresso:**
- Verde: `percentual_utilizado ≤ 75%`
- Laranja: `75% < percentual ≤ 90%`
- Vermelho: `percentual > 90%`

### 7.2 Modal de Compensação

Acessível pelo botão **🔄 Compensar** em cada linha da tabela.

**Campos:**
- `tipo-compensacao`: `"doar"` (este → outro) ou `"receber"` (outro → este)
- `outro-contrato`: select com contratos do **mesmo cliente** que têm `controle_horas_ativo`
- `quantidade-horas-compensacao`: float — validado > 0
- `observacao-compensacao`: texto obrigatório

> O saldo disponível do contrato atual é exibido no header do modal como informação.

### 7.3 Modal de Edição de Contrato (`static/modals.js`)

Quando editando um contrato com `controle_horas_ativo = true`, exibe um painel informativo:

```
⏱️ Controle de Horas
┌──────────────┬─────────────────┬──────────────────┬──────────────┐
│ Total        │ Horas Utilizadas│ Horas Restantes  │ Horas Extras │
│ 96.0h        │ 72.0h           │ 24.0h (verde)    │ 0.0h         │
└──────────────┴─────────────────┴──────────────────┴──────────────┘
Progresso: ████████████░░░ 75.0%
```

### 7.4 Dedução ao Concluir/Finalizar Sessão (`static/modals.js`)

**Concluir (`concluirSessaoModal`):**
- Chama `PUT /api/sessoes/<id>/status` com `status: 'concluida'`
- Se contrato tem controle de horas, mostra:
  - Horas aplicadas
  - Horas extras (se houver)
  - Saldo restante

**Finalizar (`finalizarSessaoModal` + `executarFinalizarSessao`):**
- Pede número da NF (opcional)
- Chama `POST /api/sessoes/<id>/finalizar`
- Exibe detalhamento igual ao concluir

---

## 8. Cálculo de `horas_totais` ao Criar/Editar Contrato

### Python (`adicionar_contrato` / `atualizar_contrato`)

```python
tipo = dados.get('tipo', 'Mensal')
horas_mensais = float(dados.get('horas_mensais') or 0)
qtd_meses = int(dados.get('quantidade_meses') or 1)

if tipo == 'Pacote':
    qtd_pacotes = qtd_meses         # reusa campo quantidade_meses
    horas_pacote = horas_mensais    # reusa campo horas_mensais
    horas_totais = qtd_pacotes * horas_pacote
    controle_horas_ativo = horas_totais > 0

elif horas_mensais > 0:
    horas_totais = horas_mensais * qtd_meses
    controle_horas_ativo = True

else:
    horas_totais = 0
    controle_horas_ativo = False
```

### Função SQL `calcular_horas_totais_contrato(id)` (Migration)

Lê diretamente do `observacoes::JSONB`. Usada para backfill de contratos existentes.

---

## 9. Cálculo de `horas_restantes` e `percentual_utilizado`

Campos virtuais calculados em `listar_contratos()` — **nunca persistidos**:

```python
if contrato.get('controle_horas_ativo'):
    horas_totais = float(contrato.get('horas_totais', 0))
    horas_utilizadas = float(contrato.get('horas_utilizadas', 0))
    contrato['horas_restantes'] = horas_totais - horas_utilizadas
    if horas_totais > 0:
        contrato['percentual_utilizado'] = round(horas_utilizadas / horas_totais * 100, 2)
    else:
        contrato['percentual_utilizado'] = 0
else:
    contrato['horas_restantes'] = None
    contrato['percentual_utilizado'] = None
```

> Ao duplicar um contrato no frontend, `horas_restantes` e `percentual_utilizado` são deletados do objeto cópia antes do POST (`app.js` linha ~6270).

---

## 10. Relatório — Como `horas_utilizadas` é Calculado

No endpoint `GET /api/relatorios/controle-horas`, o valor **não usa** `contratos.horas_utilizadas` (que pode estar desatualizado). Recalcula em tempo real:

**Resumo global:**
```sql
SELECT COALESCE(SUM(s.duracao) / 60.0, 0)
FROM sessoes s
WHERE s.empresa_id = %s
  AND s.contrato_id IS NOT NULL
  AND s.status != 'cancelada'
```

**Por contrato:**
```sql
COALESCE((
    SELECT SUM(s.duracao) / 60.0
    FROM sessoes s
    WHERE s.contrato_id = c.id
      AND s.status != 'cancelada'
), 0) AS horas_utilizadas
```

`horas_extras` e `horas_restantes` são derivados desse valor, não das colunas do banco.

---

## 11. Histórico Mensal e por Pacote

Armazenado no JSON `contratos.observacoes` — não é uma tabela separada.

### 11.1 Para Contratos Mensais (`historico_mensal`)

```json
"historico_mensal": {
  "2026-03": {
    "nf_emitida": true,
    "pago": true,
    "pulado": false,
    "horas_ajuste": 10.0,
    "nf_status": "emitida",
    "pagamento_status": "pago",
    "entrega_status": "entregue",
    "data_pagamento": "2026-03-15",
    "sessoes_entrega": { "42": "entregue", "43": "parcial" }
  }
}
```

`horas_ajuste` sobrepõe o cálculo automático das horas para aquele mês.

### 11.2 Para Contratos Pacote (`historico_pacote`)

Indexado por `sessao_id` (string):

```json
"historico_pacote": {
  "42": {
    "nf_status": "emitida",
    "pagamento_status": "pago",
    "horas_ajuste": 8.0,
    "data_pagamento": "2026-03-20",
    "entrega_status": "entregue"
  }
}
```

### 11.3 Horas Acumuladas (Campos Raiz)

| Campo | Endpoint | Descrição |
|---|---|---|
| `horas_acumuladas_inicial` | `PATCH /observacoes` | Horas do período anterior ao sistema (migração) |
| `horas_acumuladas_atual` | `PATCH /observacoes` | Horas acumuladas no período vigente |

---

## 12. Migração do Banco (`migration_controle_horas.sql`)

**O que a migration faz:**

1. Adiciona colunas na tabela `contratos`: `horas_totais`, `horas_utilizadas`, `horas_extras`, `controle_horas_ativo`
2. Adiciona colunas na tabela `sessoes`: `horas_trabalhadas`, `status`, `finalizada_em`, `finalizada_por`
3. Cria índices: `idx_contratos_controle_horas`, `idx_sessoes_status`, `idx_sessoes_contrato_status`
4. Cria função SQL `calcular_horas_totais_contrato(id)`
5. Cria função/trigger `deduzir_horas_sessao` (legado — deduz ao mudar para `'finalizada'`)
6. Faz backfill nos contratos existentes: ativa controle e calcula `horas_totais`

**Aplicar (se necessário):**
```bash
python aplicar_migration_controle_horas.py
```

---

## 13. Segurança

| Mecanismo | Onde |
|---|---|
| RLS via `empresa_id` em todas as queries | `get_db_connection(empresa_id=...)` |
| `@require_permission('contratos_view')` | Rotas de leitura |
| `@require_permission('contratos_edit')` | Compensação de horas |
| Validação de mesmo `cliente_id` | `compensar_horas_contratos()` antes de executar |
| Validação de saldo antes de transferir | `saldo_origem >= quantidade_horas` |
| `usuario_id` registrado em `compensacoes_horas` | Auditoria completa |

---

## 14. Fluxo Completo — Exemplo

```
1. Criar contrato Mensal (8h/mês × 12 = 96h):
   → horas_totais = 96, controle_horas_ativo = true

2. Criar sessão (quantidade_horas = 8h):
   → duracao = 480 min
   → _sincronizar_horas_contrato → recalcula horas_utilizadas

3. Arrastar sessão para "Concluída" no Kanban:
   → PUT /api/sessoes/<id>/status {status: "concluida"}
   → atualizar_status_sessao() → deduz 8h
   → contratos.horas_utilizadas += 8 → agora = 8h
   → horas_restantes = 88h (calculado)

4. Após 11 sessões de 8h (total = 88h):
   → horas_utilizadas = 88h, horas_restantes = 8h

5. Última sessão de 10h (2h a mais):
   → saldo_atual = 8h < 10h
   → horas_deduzidas = 8h (zera o saldo)
   → horas_extras = 2h
   → contratos.horas_utilizadas = 96, horas_extras = 2

6. Compensar 5h de outro contrato do mesmo cliente:
   → POST /api/contratos/<outro>/compensar-horas
   → outro.horas_totais -= 5h
   → este.horas_totais += 5h → agora = 101h
   → compensacoes_horas: log da operação

7. Relatório:
   → GET /api/relatorios/controle-horas
   → horas_utilizadas recalculado das sessoes.duracao (tempo real)
   → percentual_utilizado = 96/101 = 95%
   → status: ⚠️ Extras (mas após compensação fica com saldo)
```

---

## 15. Funções e Símbolos Chave

| Símbolo | Arquivo | Linha | Descrição |
|---|---|---|---|
| `adicionar_contrato(empresa_id, dados)` | database_postgresql.py | 4880 | Calcula e persiste horas_totais |
| `atualizar_contrato(contrato_id, dados)` | database_postgresql.py | 5072 | Preserva historico_mensal existente |
| `listar_contratos(empresa_id)` | database_postgresql.py | ~4990 | Calcula horas_restantes e percentual_utilizado |
| `atualizar_status_sessao(empresa_id, sessao_id, ...)` | database_postgresql.py | 5684 | Deduz horas ao concluir |
| `finalizar_sessao(empresa_id, sessao_id, ...)` | database_postgresql.py | ~5550 | Deduz horas ao finalizar |
| `_sincronizar_horas_contrato(contrato_id, empresa_id)` | app/routes/sessoes.py | ~30 | Recalcula horas_utilizadas do contrato |
| `compensar_horas_contratos(empresa_id, ...)` | database_postgresql.py | 9427 | Transfere horas entre contratos |
| `listar_compensacoes_horas(empresa_id, ...)` | database_postgresql.py | 9586 | Histórico de transferências |
| `gerar_relatorio_controle_horas(empresa_id)` | database_postgresql.py | 9234 | Dados completos para o relatório |
| `loadControleHoras()` | static/app.js | 2970 | Renderiza tela de controle de horas |
| `abrirCompensacaoHoras(contratoId)` | static/app.js | 3146 | Modal de transferência de horas |
| `executarCompensacaoHoras(id)` | static/app.js | 3339 | Executa a transferência via API |
| `concluirSessaoModal(sessaoId)` | static/modals.js | 3932 | Conclui sessão e exibe resumo de horas |
| `finalizarSessaoModal(sessaoId)` | static/modals.js | 3974 | Finaliza sessão com NF |
| `exportarControleHorasPDF()` | static/app.js | 3128 | Download PDF |
| `exportarControleHorasExcel()` | static/app.js | 3136 | Download Excel |
