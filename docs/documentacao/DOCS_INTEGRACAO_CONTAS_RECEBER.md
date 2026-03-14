# 💰 INTEGRAÇÃO SESSÕES COM CONTAS A RECEBER - PARTE 10

## ✅ Implementação Completa

Sistema automático de geração de lançamentos financeiros a partir de sessões entregues.

---

## 📦 Arquivos Criados/Editados

### 1. Migration SQL
- **Arquivo**: `migration_integracao_contas_receber.sql` (530+ linhas)
- **Conteúdo**:
  - ✅ 3 colunas de vinculação (sessoes.lancamento_id, sessoes.gerar_lancamento_automatico, lancamentos.sessao_id)
  - ✅ 2 funções SQL (gerar_lancamento_sessao, estornar_lancamento_sessao)
  - ✅ 1 trigger automático (trg_sessao_gerar_lancamento)
  - ✅ 2 views de análise (vw_sessoes_lancamentos, vw_sessoes_financeiro)
  - ✅ 4 índices de performance

### 2. Script de Aplicação
- **Arquivo**: `aplicar_migration_integracao.py` (390+ linhas)
- **Funcionalidades**:
  - Validação completa (colunas, funções, trigger, views, índices)
  - 5 testes de integração
  - Relatório detalhado com análise financeira

### 3. Backend REST API
- **Arquivo**: `app/routes/sessoes.py` (+245 linhas)
- **Endpoints criados**:
  ```
  POST   /api/sessoes/<id>/gerar-lancamento                  → Gera lançamento manual
  POST   /api/sessoes/<id>/estornar-lancamento              → Estorna/cancela lançamento
  GET    /api/sessoes/integracao                            → Visualiza relacionamentos
  GET    /api/sessoes/analise-financeira                    → Análise financeira
  PATCH  /api/sessoes/<id>/configurar-lancamento-automatico → Ativa/desativa automação
  ```

### 4. Documentação
- **Arquivo**: `DOCS_INTEGRACAO_CONTAS_RECEBER.md` (este arquivo)

---

## 🔧 Componentes Técnicos

### 1. Colunas de Vinculação

#### sessoes.lancamento_id
- Tipo: `INTEGER`
- FK: `lancamentos(id) ON DELETE SET NULL`
- Nullable: `TRUE`
- Descrição: Aponta para o lançamento gerado automaticamente

#### sessoes.gerar_lancamento_automatico
- Tipo: `BOOLEAN`
- Default: `TRUE`
- Nullable: `FALSE`
- Descrição: Controla se deve gerar automaticamente ao entregar

#### lancamentos.sessao_id
- Tipo: `INTEGER`
- FK: `sessoes(id) ON DELETE SET NULL`
- Nullable: `TRUE`
- Descrição: Relacionamento bidirecional (sessão que originou)

---

### 2. Funções SQL

#### gerar_lancamento_sessao(p_sessao_id, p_usuario_id)
Gera automaticamente um lançamento de receita a partir de uma sessão.

**Lógica**:
1. Verifica se sessão existe
2. Verifica se já tem lançamento vinculado
3. Verifica se tem valor definido
4. Busca nome do cliente
5. Busca/cria categoria apropriada
6. Cria lançamento tipo RECEITA
7. Vincula sessão ← → lançamento
8. Retorna ID do lançamento gerado

**Exemplo de uso**:
```sql
SELECT gerar_lancamento_sessao(123, 1);
-- Retorna: 456 (ID do lançamento criado)
```

#### estornar_lancamento_sessao(p_sessao_id, p_deletar)
Estorna/cancela o lançamento vinculado a uma sessão.

**Parâmetros**:
- `p_sessao_id`: ID da sessão
- `p_deletar`: Se `TRUE` deleta, se `FALSE` apenas cancela

**Lógica**:
1. Busca lançamento vinculado
2. Desvincula sessão (lancamento_id = NULL)
3. Se deletar = TRUE: deleta o lançamento
4. Se deletar = FALSE: marca status = 'CANCELADO'

**Exemplo de uso**:
```sql
-- Cancelar (manter histórico)
SELECT estornar_lancamento_sessao(123, FALSE);

-- Deletar permanentemente
SELECT estornar_lancamento_sessao(123, TRUE);
```

---

### 3. Trigger Automático

#### trg_sessao_gerar_lancamento
Executado: `BEFORE UPDATE ON sessoes`

**Comportamento**:
- **Quando status muda para 'entregue'**:
  - Se `gerar_lancamento_automatico = TRUE`
  - E ainda não tem `lancamento_id`
  - → Chama `gerar_lancamento_sessao()`
  
- **Quando status muda para 'cancelada'**:
  - Se tem `lancamento_id`
  - → Chama `estornar_lancamento_sessao(FALSE)`
  - → Cancela o lançamento (não deleta)

**Exemplo prático**:
```sql
-- Trigger executa automaticamente
UPDATE sessoes SET status = 'entregue' WHERE id = 123;
-- resultado: lançamento criado automaticamente

-- Trigger estorna automaticamente
UPDATE sessoes SET status = 'cancelada' WHERE id = 123;
-- resultado: lançamento cancelado
```

---

### 4. Views de Análise

#### vw_sessoes_lancamentos
Visualiza relacionamento completo entre sessões e lançamentos.

**Colunas principais**:
- Dados da sessão (id, título, data, cliente, valor, status, prazo)
- Dados do lançamento (id, tipo, descrição, valor, vencimento, pagamento, status)
- **Campo calculado `situacao`**:
  - `'SEM LANÇAMENTO'`: Sessão entregue sem lançamento
  - `'PAGO'`: Lançamento já foi pago
  - `'A RECEBER'`: Lançamento pendente
  - `'CANCELADO'`: Lançamento cancelado
  - `'AGUARDANDO ENTREGA'`: Sessão ainda não entregue

**Exemplo de uso**:
```sql
-- Ver todas as sessões entregues sem lançamento
SELECT * FROM vw_sessoes_lancamentos
WHERE situacao = 'SEM LANÇAMENTO';

-- Ver contas a receber
SELECT * FROM vw_sessoes_lancamentos
WHERE situacao = 'A RECEBER'
ORDER BY lancamento_vencimento ASC;
```

#### vw_sessoes_financeiro
Análise financeira agregada por empresa.

**Métricas**:
- Contadores:
  - Total de sessões
  - Sessões entregues
  - Sessões com lançamento
  - Sessões sem lançamento
  
- Valores:
  - Valor total entregue
  - Valor já recebido (status PAGO)
  - Valor a receber (status PENDENTE)
  - Valor não lançado (entregue sem lançamento)
  
- Taxas:
  - Taxa de lançamento (% de sessões com lançamento)
  - Taxa de recebimento (% do valor já recebido)

**Exemplo de uso**:
```sql
-- Análise completa da empresa
SELECT * FROM vw_sessoes_financeiro WHERE empresa_id = 1;

-- Verificar eficiência da integração
SELECT 
    empresa_id,
    taxa_lancamento_pct,
    taxa_recebimento_pct
FROM vw_sessoes_financeiro;
```

---

### 5. Índices de Performance

#### idx_sessoes_lancamento_id
```sql
CREATE INDEX idx_sessoes_lancamento_id 
ON sessoes(lancamento_id) 
WHERE lancamento_id IS NOT NULL;
```
Otimiza busca de sessões por lançamento.

#### idx_lancamentos_sessao_id
```sql
CREATE INDEX idx_lancamentos_sessao_id 
ON lancamentos(sessao_id) 
WHERE sessao_id IS NOT NULL;
```
Otimiza busca de lançamentos por sessão.

#### idx_sessoes_status_lancamento
```sql
CREATE INDEX idx_sessoes_status_lancamento 
ON sessoes(empresa_id, status, lancamento_id);
```
Otimiza filtros combinados (empresa + status + vinculação).

#### idx_sessoes_gerar_lancamento
```sql
CREATE INDEX idx_sessoes_gerar_lancamento 
ON sessoes(gerar_lancamento_automatico) 
WHERE gerar_lancamento_automatico = TRUE;
```
Otimiza busca de sessões com geração automática ativada.

---

## 🚀 Endpoints Backend

### 1. POST /api/sessoes/<id>/gerar-lancamento
Gera manualmente um lançamento para uma sessão.

**Casos de uso**:
- Sessão entregue mas lançamento não foi gerado automaticamente
- Sessão antiga (antes da integração) que precisa de lançamento
- Re-gerar lançamento após estorno

**Resposta de sucesso**:
```json
{
  "success": true,
  "message": "Lançamento gerado com sucesso",
  "lancamento_id": 456
}
```

**Erros possíveis**:
- 404: Sessão não encontrada
- 400: Sessão já possui lançamento vinculado
- 400: Sessão não possui valor definido
- 403: Acesso negado (empresa diferente)

---

### 2. POST /api/sessoes/<id>/estornar-lancamento
Estorna/cancela o lançamento vinculado.

**Body (JSON)**:
```json
{
  "deletar": false  // false = cancelar, true = deletar
}
```

**Casos de uso**:
- Sessão foi cancelada após gerar lançamento
- Lançamento foi gerado por engano
- Necessidade de corrigir valores

**Resposta de sucesso**:
```json
{
  "success": true,
  "message": "Lançamento cancelado com sucesso"
}
```

---

### 3. GET /api/sessoes/integracao?situacao=A%20RECEBER
Visualiza relacionamentos entre sessões e lançamentos.

**Query Parameters**:
- `situacao` (opcional): Filtra por situação
  - `"SEM LANÇAMENTO"`
  - `"PAGO"`
  - `"A RECEBER"`
  - `"CANCELADO"`
  - `"AGUARDANDO ENTREGA"`

**Resposta**:
```json
{
  "success": true,
  "data": [
    {
      "sessao_id": 123,
      "sessao_titulo": "Ensaio Fotográfico",
      "cliente_nome": "João Silva",
      "sessao_valor": 1500.00,
      "lancamento_id": 456,
      "lancamento_status": "PENDENTE",
      "situacao": "A RECEBER",
      ...
    }
  ]
}
```

---

### 4. GET /api/sessoes/analise-financeira
Análise financeira completa da integração.

**Resposta**:
```json
{
  "success": true,
  "analise": {
    "total_sessoes": 150,
    "sessoes_entregues": 120,
    "sessoes_com_lancamento": 115,
    "sessoes_sem_lancamento": 5,
    "valor_total_entregue": 180000.00,
    "valor_ja_recebido": 150000.00,
    "valor_a_receber": 25000.00,
    "valor_nao_lancado": 5000.00,
    "taxa_lancamento_pct": 95.83,
    "taxa_recebimento_pct": 83.33
  }
}
```

---

### 5. PATCH /api/sessoes/<id>/configurar-lancamento-automatico
Ativa/desativa geração automática para sessão específica.

**Body (JSON)**:
```json
{
  "ativar": true  // true = ativar, false = desativar
}
```

**Casos de uso**:
- Desativar para sessões gratuitas
- Desativar para sessões que serão lançadas manualmente
- Ativar para sessões antigas que ficaram sem configuração

**Resposta**:
```json
{
  "success": true,
  "message": "Geração automática ativada com sucesso",
  "ativado": true
}
```

---

## 📝 Fluxos de Uso

### Fluxo Automático (Padrão)
```
1. Usuário cria sessão
   → gerar_lancamento_automatico = TRUE (padrão)

2. Usuário trabalha na sessão
   → Status: pendente → confirmada → em_andamento → concluída

3. Usuário marca como entregue
   → UPDATE sessoes SET status = 'entregue' WHERE id = 123;
   → **TRIGGER EXECUTA AUTOMATICAMENTE**
   → Lançamento é criado
   → Sessão é vinculada ao lançamento

4. Sistema de contas a receber
   → Lançamento aparece em "Contas a Receber"
   → Cliente paga
   → UPDATE lancamentos SET status = 'PAGO' WHERE id = 456;
```

### Fluxo Manual
```
1. Sessão já entregue sem lançamento
   → Visualizar: GET /api/sessoes/integracao?situacao=SEM%20LANÇAMENTO

2. Gerar lançamento manualmente
   → POST /api/sessoes/123/gerar-lancamento

3. Verificar resultado
   → GET /api/sessoes/integracao?situacao=A%20RECEBER
```

### Fluxo de Estorno
```
1. Sessão foi cancelada após entrega
   → UPDATE sessoes SET status = 'cancelada';
   → **TRIGGER CANCELA AUTOMATICAMENTE O LANÇAMENTO**

2. OU estornar manualmente
   → POST /api/sessoes/123/estornar-lancamento
   → Body: {"deletar": false}

3. Verificar resultado
   → GET /api/sessoes/integracao
   → situacao = 'CANCELADO'
```

---

## 🎯 Benefícios

### Automação
- **Geração automática** ao entregar sessão
- **Estorno automático** ao cancelar sessão
- **Zero trabalho manual** para casos padrão
- **Registro auditável** com timestamps

### Integridade
- **Relacionamento bidirecional** (sessoes ← → lancamentos)
- **Foreign Keys** com `ON DELETE SET NULL`
- **Triggers confiáveis** com tratamento de erros
- **Validações** antes de gerar lançamento

### Visibilidade
- **Views pré-calculadas** para análise rápida
- **Situações claras** (SEM LANÇAMENTO, PAGO, A RECEBER)
- **Métricas financeiras** agregadas
- **Taxas de eficiência** (lançamento, recebimento)

### Performance
- **4 índices especializados** para queries comuns
- **Funções SQL** executam no banco (sem roundtrips)
- **Triggers BEFORE** não bloqueiam operações
- **Views** podem usar MATERIALIZED se necessário

---

## 📊 Estatísticas da Implementação

| Item | Quantidade |
|------|-----------|
| **Arquivos Criados** | 3 |
| **Arquivo Editado** | 1 |
| **Linhas de Código** | ~1200 |
| **Colunas Adicionadas** | 3 |
| **Funções SQL** | 2 |
| **Triggers** | 1 |
| **Views** | 2 |
| **Índices** | 4 |
| **Endpoints REST** | 5 |

---

## 🚀 Como Executar

### 1. Aplicar Migration
```bash
python aplicar_migration_integracao.py
```

**Saída esperada**:
```
✅ Conectado ao banco de dados PostgreSQL
🔄 Executando migration...
✅ Migration executada com sucesso!
✅ Colunas adicionadas em sessoes
✅ Coluna sessao_id adicionada em lancamentos
✅ Funções SQL criadas (2)
✅ Trigger criado
✅ Views criadas (2)
✅ Índices criados (4)
✅ COMMIT realizado com sucesso!
🎉 MIGRATION CONCLUÍDA COM SUCESSO!
```

### 2. Testar Geração Manual (SQL)
```sql
-- Testar geração de lançamento
SELECT gerar_lancamento_sessao(123);

-- Ver resultado
SELECT * FROM vw_sessoes_lancamentos WHERE sessao_id = 123;

-- Testar estorno
SELECT estornar_lancamento_sessao(123, FALSE);
```

### 3. Testar via API
```bash
# Gerar lançamento
curl -X POST http://localhost:5000/api/sessoes/123/gerar-lancamento \
  -H "Content-Type: application/json"

# Visualizar integração
curl -X GET "http://localhost:5000/api/sessoes/integracao?situacao=A%20RECEBER"

# Análise financeira
curl -X GET http://localhost:5000/api/sessoes/analise-financeira

# Estornar lançamento
curl -X POST http://localhost:5000/api/sessoes/123/estornar-lancamento \
  -H "Content-Type: application/json" \
  -d '{"deletar": false}'
```

---

## 🔒 Segurança

- ✅ Row Level Security (RLS) ativo em todas as queries
- ✅ Filtro automático por `empresa_id` da sessão
- ✅ CSRF Token em requisições POST/PATCH
- ✅ Validação de propriedade da sessão
- ✅ Tratamento de erros sem expor dados sensíveis
- ✅ Foreign Keys com `ON DELETE SET NULL` (não quebra ao deletar)

---

## 📝 Próximos Passos

### Melhorias Futuras (Opcionais)
- [ ] Frontend: Modal para visualizar lançamento vinculado
- [ ] Frontend: Botão "Gerar Lançamento" em sessões sem lançamento
- [ ] Frontend: Badge indicando se tem lançamento vinculado
- [ ] Notificações: Email ao gerar lançamento automaticamente
- [ ] Relatórios: Gráfico de conversão sessões → lançamentos
- [ ] Integração: Marcar lançamento como PAGO ao receber pagamento PIX

---

**Autor**: Sistema Financeiro DWM  
**Data**: 2026-02-08  
**Status**: ✅ COMPLETO - PRONTO PARA DEPLOY  
**Commit**: Pendente
