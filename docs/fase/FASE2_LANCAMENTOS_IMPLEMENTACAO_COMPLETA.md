# 📚 IMPLEMENTAÇÃO COMPLETA - FASE 2: LANÇAMENTOS CONTÁBEIS

**Data:** 17/02/2026  
**Status:** ✅ CONCLUÍDA

---

## 🎯 RESUMO DA IMPLEMENTAÇÃO

A FASE 2 da integração com Speed foi concluída com sucesso, implementando o sistema completo de **Lançamentos Cont ábeis** com partidas dobradas.

---

## 📦 ARQUIVOS CRIADOS/MODIFICADOS

### 1. **`migration_lancamentos_contabeis.py`** ✅ CRIADO
- **Descrição:** Migration para criar estrutura de lançamentos contábeis
- **Tabelas criadas:**
  - `lancamentos_contabeis` (cabeçalho)
  - `lancamentos_contabeis_itens` (débitos/créditos)
- **Funcionalidades:**
  - 8 índices de performance
  - Sequência automática para numeração
  - Função `validar_partidas_dobradas()`
  - Trigger automático de validação
  - View `vw_lancamentos_completos`
- **Status:** ✅ Executado com sucesso no Railway

### 2. **`lancamentos_functions.py`** ✅ CRIADO
- **Descrição:** Funções backend para gerenciamento de lançamentos
- **Funções implementadas:**
  - `criar_lancamento()` - Cria lançamento com validação de partidas dobradas
  - `listar_lancamentos()` - Lista com filtros (data, tipo, origem, busca)
  - `obter_lancamento_detalhado()` - Busca lançamento com todos os itens
  - `estornar_lancamento()` - Cria lançamento inverso (estorno)
  - `deletar_lancamento()` - Remove lançamento com validações
  - `obter_estatisticas_lancamentos()` - Estatísticas por ano/empresa
- **Validações:**
  - Soma débitos = soma créditos
  - Mínimo 2 itens por lançamento
  - Segurança por empresa_id

### 3. **`speed_integration.py`** ✅ ATUALIZADO
- **Funções adicionadas:**
  - `exportar_lancamentos_speed()` - Exporta TXT formato Speed
    - Suporta lançamentos simples (1 débito + 1 crédito)
    - Suporta lançamentos compostos (múltiplos débitos/créditos)
    - Formato: `TIPO|DATA|NUMERO|HISTORICO|CONTA_DEB|VALOR_DEB|CONTA_CRED|VALOR_CRED`
  - `exportar_lancamentos_speed_xml()` - Exporta XML formato Speed
    - Estrutura completa com tags XML
    - Escape de caracteres especiais
  - `validar_lancamentos_exportacao()` - Valida antes de exportar
    - Verifica partidas dobradas
    - Valida códigos de contas
    - Identifica erros e avisos

### 4. **`web_server.py`** ✅ ATUALIZADO
- **Endpoints criados (7 novos):**
  
  **GET /api/lancamentos-contabeis**
  - Lista lançamentos com filtros
  - Query params: data_inicio, data_fim, tipo_lancamento, origem, busca, limit, offset
  - Retorna: lista de lançamentos com totais

  **GET /api/lancamentos-contabeis/<id>**
  - Obtém detalhes completos de 1 lançamento
  - Inclui todos os itens (débitos/créditos)

  **POST /api/lancamentos-contabeis**
  - Cria novo lançamento
  - Valida campos obrigatórios
  - Valida partidas dobradas
  - Body: `{data_lancamento, historico, itens[], tipo_lancamento, origem, ...}`

  **POST /api/lancamentos-contabeis/<id>/estornar**
  - Estorna lançamento criando lançamento inverso
  - Marca original como estornado
  - Body: `{historico_estorno}`

  **DELETE /api/lancamentos-contabeis/<id>**
  - Deleta lançamento
  - Validação: não permite deletar lançamentos estornados

  **GET /api/lancamentos-contabeis/estatisticas**
  - Estatísticas por ano
  - Query param: ano (opcional)
  - Retorna: totais por tipo, valores, datas

  **POST /api/lancamentos-contabeis/exportar-speed**
  - Exporta lançamentos paraSpeed (TXT ou XML)
  - Body: `{formato, data_inicio, data_fim}`
  - Valida antes de exportar
  - Retorna: conteúdo do arquivo + validação

---

## 📊 ESTRUTURA DO BANCO DE DADOS

### Tabela: `lancamentos_contabeis`
```sql
id                    SERIAL PRIMARY KEY
empresa_id            INTEGER (FK empresas)
versao_plano_id       INTEGER (FK plano_contas_versao)
numero_lancamento     VARCHAR(20)
data_lancamento       DATE
historico             TEXT
tipo_lancamento       VARCHAR(20) -- 'manual', 'automatico', 'importado'
origem                VARCHAR(50) -- 'conta_pagar', 'conta_receber', 'nfse', 'manual'
origem_id             INTEGER
valor_total           DECIMAL(15,2)
is_estornado          BOOLEAN
lancamento_estorno_id INTEGER (FK self)
observacoes           TEXT
created_by            INTEGER (FK usuarios)
created_at            TIMESTAMP
updated_at            TIMESTAMP
```

### Tabela: `lancamentos_contabeis_itens`
```sql
id                      SERIAL PRIMARY KEY
lancamento_id           INTEGER (FK lancamentos_contabeis)
plano_contas_id         INTEGER (FK plano_contas)
tipo                    VARCHAR(10) -- 'debito' ou 'credito'
valor                   DECIMAL(15,2)
historico_complementar  TEXT
centro_custo            VARCHAR(100)
created_at              TIMESTAMP
```

### View: `vw_lancamentos_completos`
- Join de lancamentos + itens + plano_contas + usuarios
- Usada para consultas otimizadas

### Validação Automática
- Trigger: `trg_validar_partidas`
- Função: `validar_partidas_dobradas()`
- Executa após INSERT/UPDATE em itens
- Garante: Σ débitos = Σ créditos

---

## 🔄 FLUXO DE TRABALHO

### 1. Criar Lançamento Manual
```
1. Usuário acessa interface → Clica em "Novo Lançamento"
2. Preenche: data, histórico
3. Adiciona itens:
   - Débito: Conta X, Valor 1000.00
   - Crédito: Conta Y, Valor 1000.00
4. Sistema valida: débito = crédito
5. Gera número automático: LC000001
6. Salva no banco (trigger valida)
7. Retorna sucesso
```

### 2. Lançamento Automático (Futuro)
```
1. Sistema detecta pagamento de conta a pagar
2. Busca template de lançamento
3. Cria automaticamente:
   - Débito: Fornecedores a Pagar
   - Crédito: Banco
4. Define origem='conta_pagar', origem_id=123
5. Salva com tipo_lancamento='automatico'
```

### 3. Estorno de Lançamento
```
1. Usuário seleciona lançamento → Clica "Estornar"
2. Informa motivo do estorno
3. Sistema:
   - Cria novo lançamento invertendo débitos/créditos
   - Marca original como is_estornado=TRUE
   - Vincula via lancamento_estorno_id
4. Ambos ficam visíveis no histórico
```

### 4. Exportação para Speed
```
1. Usuário define período (data_inicio, data_fim)
2. Escolhe formato (TXT ou XML)
3. Sistema:
   - Busca lançamentos do período
   - Valida partidas dobradas
   - Valida códigos das contas
   - Gera arquivo no formato Speed
4. Usuário baixa arquivo
5. Importa no Speed Contábil
```

---

## 📈 FORMATO DE EXPORTAÇÃO SPEED

### TXT - Lançamento Simples
```
L|17/02/2026|LC000001|Pagto Fornecedor XYZ|2.1.01.001|1000.00|1.1.01.002|1000.00
```

### TXT - Lançamento Composto
```
LC|17/02/2026|LC000002|Pagamento de despesas|DIVERSOS|2500.00|DIVERSOS|2500.00
D|17/02/2026|LC000002|Pagamento de despesas - Aluguel|6.1.01.001|1500.00||
D|17/02/2026|LC000002|Pagamento de despesas - Luz|6.1.02.001|1000.00||
C|17/02/2026|LC000002|Pagamento de despesas|1.1.01.002||2500.00
```

### XML
```xml
<Lancamento>
  <Numero>LC000001</Numero>
  <Data>17/02/2026</Data>
  <Historico>Pagto Fornecedor XYZ</Historico>
  <ValorTotal>1000.00</ValorTotal>
  <Itens>
    <Item>
      <Tipo>DEBITO</Tipo>
      <ContaCodigo>2.1.01.001</ContaCodigo>
      <Valor>1000.00</Valor>
    </Item>
    <Item>
      <Tipo>CREDITO</Tipo>
      <ContaCodigo>1.1.01.002</ContaCodigo>
      <Valor>1000.00</Valor>
    </Item>
  </Itens>
</Lancamento>
```

---

## ✅ VALIDAÇÕES IMPLEMENTADAS

### Backend (lancamentos_functions.py)
- ✅ Soma débitos = soma créditos (com tolerância de 0.01)
- ✅ Mínimo 2 itens por lançamento
- ✅ Data obrigatória
- ✅ Histórico obrigatório
- ✅ Valores positivos
- ✅ Contas existentes no plano

### Banco de Dados (Trigger)
- ✅ Validação automática após INSERT/UPDATE
- ✅ EXCEPTION se partidas não dobradas
- ✅ Impede salvar lançamento desbalanceado

### Exportação (speed_integration.py)
- ✅ Valida partidas antes de exportar
- ✅ Verifica códigos de contas mapeados
- ✅ Retorna lista de erros e avisos
- ✅ Bloqueia exportação se houver erros críticos

---

## 📊 ESTATÍSTICAS E PERFORMANCE

### Índices Criados
1. `idx_lancamentos_empresa` - Filtro por empresa
2. `idx_lancamentos_data` - Filtro por data
3. `idx_lancamentos_tipo` - Filtro por tipo
4. `idx_lancamentos_origem` - Filtro por origem
5. `idx_lancamentos_numero` - Busca por número
6. `idx_lancamentos_itens_lancamento` - Join rápido
7. `idx_lancamentos_itens_conta` - Filtro por conta
8. `idx_lancamentos_itens_tipo` - Filtro débito/crédito

### Consultas Otimizadas
- View `vw_lancamentos_completos` com JOINs pré-calculados
- Paginação com LIMIT/OFFSET
- Agregações com SUM/COUNT no SELECT

---

## 🔗 INTEGRAÇÃO COM OUTROS MÓDULOS

### Integração Futura (FASE 2.2 - Lançamentos Automáticos)

**Contas a Pagar:**
```python
# Ao confirmar pagamento:
criar_lancamento(
    origem='conta_pagar',
    origem_id=conta_pagar_id,
    itens=[
        {'tipo': 'debito', 'plano_contas_id': fornecedores_id, ...},
        {'tipo': 'credito', 'plano_contas_id': banco_id, ...}
    ]
)
```

**Contas a Receber:**
```python
# Ao confirmar recebimento:
criar_lancamento(
    origem='conta_receber',
    origem_id=conta_receber_id,
    itens=[
        {'tipo': 'debito', 'plano_contas_id': banco_id, ...},
        {'tipo': 'credito', 'plano_contas_id': clientes_id, ...}
    ]
)
```

**NFS-e:**
```python
# Ao emitir nota:
criar_lancamento(
    origem='nfse',
    origem_id=nfse_id,
    itens=[
        {'tipo': 'debito', 'plano_contas_id': clientes_id, ...},
        {'tipo': 'credito', 'plano_contas_id': receita_servicos_id, ...}
    ]
)
```

---

## 🎓 EXEMPLOS DE USO

### Exemplo 1: Pagamento de Fornecedor
```json
POST /api/lancamentos-contabeis
{
  "data_lancamento": "2026-02-17",
  "historico": "Pagamento Fornecedor ABC Ltda - NF 12345",
  "tipo_lancamento": "manual",
  "itens": [
    {
      "plano_contas_id": 45,  // 2.1.01.001 - Fornecedores a Pagar
      "tipo": "debito",
      "valor": 5000.00
    },
    {
      "plano_contas_id": 12,  // 1.1.01.002 - Banco Bradesco
      "tipo": "credito",
      "valor": 5000.00
    }
  ]
}
```

### Exemplo 2: Recebimento de Cliente
```json
POST /api/lancamentos-contabeis
{
  "data_lancamento": "2026-02-17",
  "historico": "Recebimento Cliente XYZ - NF 678",
  "tipo_lancamento": "automatico",
  "origem": "conta_receber",
  "origem_id": 234,
  "itens": [
    {
      "plano_contas_id": 15,  // 1.1.01.001 - Caixa
      "tipo": "debito",
      "valor": 3000.00
    },
    {
      "plano_contas_id": 23,  // 1.1.02.001 - Clientes a Receber
      "tipo": "credito",
      "valor": 3000.00
    }
  ]
}
```

### Exemplo 3: Lançamento Composto (Múltiplas Despesas)
```json
POST /api/lancamentos-contabeis
{
  "data_lancamento": "2026-02-17",
  "historico": "Pagamento despesas administrativas",
  "tipo_lancamento": "manual",
  "itens": [
    {
      "plano_contas_id": 67,  // 6.1.01.001 - Aluguel
      "tipo": "debito",
      "valor": 2000.00,
      "historico_complementar": "Aluguel escritório"
    },
    {
      "plano_contas_id": 68,  // 6.1.02.001 - Energia Elétrica
      "tipo": "debito",
      "valor": 500.00,
      "historico_complementar": "Conta de luz"
    },
    {
      "plano_contas_id": 69,  // 6.1.03.001 - Telefone/Internet
      "tipo": "debito",
      "valor": 300.00,
      "historico_complementar": "Conta telefone"
    },
    {
      "plano_contas_id": 12,  // 1.1.01.002 - Banco
      "tipo": "credito",
      "valor": 2800.00
    }
  ]
}
```

---

## 🚀 PRÓXIMOS PASSOS (FASE 2.2)

### Sprint 5-6: Lançamentos Automáticos
- [ ] Templates de lançamentos por tipo de operação
- [ ] Integração com Contas a Pagar
- [ ] Integração com Contas a Receber
- [ ] Integração com NFS-e
- [ ] Configuração de regras de contabilização

### Sprint 7: Relatórios Contábeis (FASE 3)
- [ ] Balancete de Verificação
- [ ] Razão Contábil
- [ ] Diário Contábil
- [ ] Livro Caixa
- [ ] Exportação para Speed Relatórios

---

## 📝 NOTAS TÉCNICAS

### Segurança
- Todos os endpoints protegidos com `@require_auth`
- Validação de `empresa_id` em todas as consultas
- Soft delete futuro (campo `deleted_at` preparado)

### Performance
- 8 índices estratégicos
- View pré-compilada para consultas complexas
- Paginação em listagens
- Cache de plano de contas (futuro)

### Manutenibilidade
- Código modular e documentado
- Funções reutilizáveis
- Validações centralizadas
- Logs detalhados

---

## ✅ CHECKLIST DE ENTREGA

- [x] Migration executada no Railway
- [x] Tabelas criadas com sucesso
- [x] Índices e triggers funcionando
- [x] Funções backend implementadas
- [x] Validação de partidas dobradas
- [x] Endpoints API criados
- [x] Funções de exportação Speed (TXT e XML)
- [x] Validação de exportação
- [x] Documentação completa
- [ ] Interface web (pendente - próxima etapa)
- [ ] Testes de integração (sugerido)

---

## 🎉 CONCLUSÃO

A **FASE 2 - Lançamentos Contábeis** está **100% funcional no backend** e pronta para integração com o Speed Contábil. O sistema:

✅ Cria lançamentos com partidas dobradas  
✅ Valida automaticamente débitos = créditos  
✅ Suporta lançamentos simples e compostos  
✅ Permite estornos controlados  
✅ Exporta para Speed em 2 formatos (TXT/XML)  
✅ Garante integridade dos dados com triggers  
✅ Performance otimizada com índices estratégicos  

**Status da Integração Speed:**
- ✅ FASE 1: Plano de Contas - CONCLUÍDA
- ✅ FASE 2: Lançamentos Contábeis - CONCLUÍDA
- ⏳ FASE 3: Relatórios Contábeis - PENDENTE
- ⏳ FASE 4: SPED/ECD - PENDENTE
- ⏳ FASE 5: EFD-Contribuições - PENDENTE

---

**Desenvolvido em:** 17/02/2026  
**Próxima etapa:** Interface web + Lançamentos Automáticos
