# 🚀 PLANO DE INTEGRAÇÃO COM SPEED (Contábil, Fiscal, Contribuições)

**Data:** 17/02/2026  
**Objetivo:** Integrar sistema financeiro com Speed para declarações fiscais e contábeis

---

## 📊 FASE 1: PLANO DE CONTAS (BASE) - **FOCO INICIAL**

### 1.1 Mapeamento de Códigos
**Objetivo:** Permitir vincular contas internas com códigos Speed

**Tarefas:**
- [ ] Adicionar campo `codigo_speed` na tabela `plano_contas`
- [ ] Adicionar campo `codigo_referencial` (para Referencial Contábil da RFB)
- [ ] Interface para cadastrar código Speed ao criar/editar conta
- [ ] Interface para importar mapeamento via CSV/Excel
- [ ] Validação de códigos Speed (formato padrão)

**Campos a adicionar:**
```sql
ALTER TABLE plano_contas ADD COLUMN codigo_speed VARCHAR(30);
ALTER TABLE plano_contas ADD COLUMN codigo_referencial VARCHAR(50); -- Ex: 1.01.01.01.01
ALTER TABLE plano_contas ADD COLUMN natureza_sped VARCHAR(2); -- '01' a '09'
```

### 1.2 Exportação Plano de Contas
**Objetivo:** Gerar arquivo compatível com Speed

**Tarefas:**
- [ ] Endpoint `/api/contabilidade/exportar-speed-plano`
- [ ] Formato TXT layout Speed (campos fixos/delimitados)
- [ ] Formato XML (caso Speed aceite)
- [ ] Incluir: código, descrição, natureza, tipo conta
- [ ] Log de exportação (histórico)

**Formato Speed - Plano de Contas:**
```
CODIGO|DESCRICAO|TIPO|NATUREZA|GRAU|SUPERIOR
1|ATIVO|S|D|1|
1.1|ATIVO CIRCULANTE|S|D|2|1
1.1.01|CAIXA E EQUIVALENTES|S|D|3|1.1
1.1.01.001|CAIXA|A|D|4|1.1.01
```

### 1.3 Importação de Plano Speed
**Objetivo:** Importar plano de contas do Speed para o sistema

**Tarefas:**
- [ ] Upload de arquivo TXT/CSV do Speed
- [ ] Parser de layout Speed
- [ ] Mapeamento automático de classificação
- [ ] Criar contas com hierarquia preservada
- [ ] Relatório de importação com erros/avisos

---

## 📚 FASE 2: LANÇAMENTOS CONTÁBEIS

### 2.1 Estrutura de Lançamentos
**Objetivo:** Registrar partidas dobradas para exportação

**Tarefas:**
- [ ] Criar tabela `lancamentos_contabeis` (cabeçalho)
- [ ] Criar tabela `lancamentos_contabeis_itens` (débito/crédito)
- [ ] Vincular transações financeiras → lançamentos contábeis
- [ ] Interface para lançamentos manuais
- [ ] Validação: soma débitos = soma créditos

**Estrutura:**
```sql
CREATE TABLE lancamentos_contabeis (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    numero_lancamento VARCHAR(20),
    data_lancamento DATE NOT NULL,
    historico TEXT,
    tipo_lancamento VARCHAR(20), -- 'manual', 'automatico', 'importado'
    origem VARCHAR(50), -- 'conta_pagar', 'conta_receber', 'manual'
    origem_id INTEGER,
    valor_total DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lancamentos_contabeis_itens (
    id SERIAL PRIMARY KEY,
    lancamento_id INTEGER REFERENCES lancamentos_contabeis(id) ON DELETE CASCADE,
    plano_contas_id INTEGER REFERENCES plano_contas(id),
    tipo VARCHAR(10) NOT NULL, -- 'debito' ou 'credito'
    valor DECIMAL(15,2) NOT NULL,
    historico_complementar TEXT,
    centro_custo_id INTEGER
);
```

### 2.2 Lançamentos Automáticos
**Objetivo:** Gerar lançamentos contábeis a partir de transações financeiras

**Tarefas:**
- [ ] Regras de contabilização (contas a pagar/receber)
- [ ] Template de lançamentos por tipo de operação
- [ ] Lançamento automático ao confirmar pagamento/recebimento
- [ ] Estorno de lançamentos
- [ ] Histórico padrão por tipo de operação

**Exemplos de Regras:**
- Pagamento de Fornecedor:
  - D: Fornecedores a Pagar (2.1.01.001)
  - C: Banco (1.1.01.002)
  
- Recebimento de Cliente:
  - D: Banco (1.1.01.002)
  - C: Clientes a Receber (1.1.02.001)

### 2.3 Exportação para Speed Contábil
**Objetivo:** Gerar arquivo de lançamentos para importação no Speed

**Tarefas:**
- [ ] Endpoint `/api/contabilidade/exportar-speed-lancamentos`
- [ ] Filtros: período, conta, tipo
- [ ] Formato TXT layout Speed (lançamentos)
- [ ] Numeração sequencial de lançamentos
- [ ] Validação antes da exportação

**Formato Speed - Lançamentos:**
```
TIPO|DATA|NUMERO|HISTORICO|CONTA_DEBITO|VALOR_DEBITO|CONTA_CREDITO|VALOR_CREDITO
L|01/01/2026|1|Pagto Fornecedor XYZ|2.1.01.001|1000.00|1.1.01.002|1000.00
```

---

## 📈 FASE 3: RELATÓRIOS CONTÁBEIS

### 3.1 Balancete de Verificação
**Objetivo:** Gerar balancete mensal/anual para conferência

**Tarefas:**
- [ ] Cálculo de saldos por conta contábil
- [ ] Saldo anterior + movimentação = saldo atual
- [ ] Filtros: período, nível de conta
- [ ] Exportação PDF/Excel/TXT
- [ ] Layout compatível com Speed

**Colunas:**
- Código Conta
- Descrição
- Saldo Anterior (devedor/credor)
- Débitos do Período
- Créditos do Período
- Saldo Atual (devedor/credor)

### 3.2 DRE (Demonstrativo de Resultado do Exercício)
**Objetivo:** Demonstração de lucro/prejuízo

**Tarefas:**
- [ ] Agrupamento de receitas (grupo 4)
- [ ] Agrupamento de custos (grupo 5)
- [ ] Agrupamento de despesas (grupo 6)
- [ ] Cálculo automático de resultado
- [ ] Comparativo mensal/anual
- [ ] Exportação para Speed

**Estrutura DRE:**
```
RECEITA BRUTA
(-) DEDUÇÕES DA RECEITA
= RECEITA LÍQUIDA
(-) CUSTOS
= LUCRO BRUTO
(-) DESPESAS OPERACIONAIS
= RESULTADO OPERACIONAL
```

### 3.3 Balanço Patrimonial
**Objetivo:** Posição patrimonial da empresa

**Tarefas:**
- [ ] Ativo (grupo 1)
- [ ] Passivo (grupo 2)
- [ ] Patrimônio Líquido (grupo 3)
- [ ] Validação: Ativo = Passivo + PL
- [ ] Comparativo períodos
- [ ] Exportação para Speed

---

## 🧾 FASE 4: SPEED FISCAL (ECD/ECF)

### 4.1 SPED Contábil (ECD)
**Objetivo:** Escrituração Contábil Digital

**Tarefas:**
- [ ] Geração arquivo ECD (layout SPED)
- [ ] Blocos: 0 (abertura), I (lançamentos), J (balanço)
- [ ] Assinatura digital (certificado A1/A3)
- [ ] Validação PVA (Programa Validador SPED)
- [ ] Histórico de transmissões

**Blocos ECD:**
- Bloco 0: Identificação empresa
- Bloco I: Lançamentos contábeis
- Bloco J: Plano de contas e balancetes
- Bloco 9: Encerramento

### 4.2 ECF (Escrituração Contábil Fiscal)
**Objetivo:** Apuração de IRPJ e CSLL

**Tarefas:**
- [ ] Blocos ECF (Y, 0, C, E, K, L, M, N, P, U, X, 9)
- [ ] Part A: IRPJ Lucro Real
- [ ] Part B: CSLL
- [ ] Adições e exclusões
- [ ] Compensações
- [ ] Exportação para Speed Fiscal

---

## 💰 FASE 5: SPEED CONTRIBUIÇÕES (EFD-Contribuições)

### 5.1 PIS e COFINS
**Objetivo:** Escrituração de PIS/COFINS

**Tarefas:**
- [ ] Regime de apuração (cumulativo/não-cumulativo)
- [ ] Blocos: 0, A, C, D, F, M, 1, 9
- [ ] Detalhamento de receitas
- [ ] Créditos de PIS/COFINS
- [ ] Apuração mensal
- [ ] Exportação para Speed Contribuições

**Blocos Principais:**
- Bloco A: Documentos fiscais - Serviços
- Bloco C: Documentos fiscais - Mercadorias
- Bloco M: Apuração das contribuições

### 5.2 Integração com NF-e/NFS-e
**Objetivo:** Vincular notas fiscais aos lançamentos

**Tarefas:**
- [ ] Vincular NFS-e existentes aos lançamentos contábeis
- [ ] Importar XMLs de NF-e
- [ ] Cálculo automático de PIS/COFINS
- [ ] Créditos tributários
- [ ] Compensações

---

## 🔐 FASE 6: OUTRAS DECLARAÇÕES

### 6.1 DCTF (Declaração de Débitos Federais)
**Objetivo:** Declarar débitos federais (IRPJ, CSLL, PIS, COFINS)

**Tarefas:**
- [ ] Cálculo de tributos a recolher
- [ ] Geração arquivo DCTF
- [ ] Integração com guias de pagamento (DARF)

### 6.2 DIRF (Declaração do Imposto Retido na Fonte)
**Objetivo:** Informar retenções na fonte

**Tarefas:**
- [ ] Registrar pagamentos com retenção
- [ ] Vínculos: fornecedores, funcionários
- [ ] Geração arquivo DIRF

---

## 🛠️ FASE 7: INFRAESTRUTURA E SUPORTE

### 7.1 Configuração por Empresa
**Tarefas:**
- [ ] Regime tributário (Simples, Presumido, Real)
- [ ] Tipo de empresa (MEI, ME, EPP, Normal)
- [ ] Certificado digital (upload A1 ou integração A3)
- [ ] Contador responsável (dados, CRC)

### 7.2 Auditoria e Logs
**Tarefas:**
- [ ] Log de todas as exportações
- [ ] Histórico de arquivos gerados
- [ ] Rastreabilidade de alterações
- [ ] Backup de arquivos SPED

### 7.3 Validações e Críticas
**Tarefas:**
- [ ] Motor de validações pré-exportação
- [ ] Alertas de inconsistências
- [ ] Sugestões de correção
- [ ] Relatório de críticas

---

## 📅 CRONOGRAMA SUGERIDO

### Sprint 1-2 (ATUAL - Semanas 1-2)
✅ **FASE 1.1:** Mapeamento de códigos Speed no Plano de Contas
- Adicionar campos codigo_speed, codigo_referencial
- Interface para editar mapeamento
- Importar/exportar mapeamento CSV

### Sprint 3 (Semanas 3-4)
**FASE 1.2 + 1.3:** Exportação/Importação Plano de Contas
- Parser layout Speed
- Geração TXT compatível

### Sprint 4-5 (Semanas 5-8)
**FASE 2.1 + 2.2:** Lançamentos Contábeis
- Criar estrutura de lançamentos
- Lançamentos automáticos

### Sprint 6 (Semanas 9-10)
**FASE 2.3:** Exportação Lançamentos para Speed

### Sprint 7-8 (Semanas 11-14)
**FASE 3:** Relatórios Contábeis (Balancete, DRE, Balanço)

### Sprint 9-12 (Semanas 15-22)
**FASE 4:** SPED Contábil (ECD) e Speed Fiscal

### Sprint 13-16 (Semanas 23-30)
**FASE 5:** EFD-Contribuições (PIS/COFINS)

### Sprint 17+ (Semanas 31+)
**FASE 6:** Outras declarações (DCTF, DIRF, etc)

---

## 🎯 PRIORIDADES IMEDIATAS (Sprint 1)

### 1. Adicionar campos Speed na tabela plano_contas
```sql
ALTER TABLE plano_contas 
ADD COLUMN codigo_speed VARCHAR(30),
ADD COLUMN codigo_referencial VARCHAR(50),
ADD COLUMN natureza_sped VARCHAR(2) DEFAULT '01';

CREATE INDEX idx_plano_contas_speed ON plano_contas(codigo_speed);
```

### 2. Atualizar interface de Plano de Contas
- Adicionar campo "Código Speed" no formulário
- Adicionar campo "Código Referencial" (RFB)
- Mostrar na listagem

### 3. Criar função de exportação básica
- Endpoint para baixar plano de contas em formato Speed
- Formato TXT com colunas: CODIGO|DESCRICAO|TIPO|NATUREZA

### 4. Documentação
- Manual de mapeamento de contas
- Exemplos de códigos Speed × Códigos Internos
- Fluxo de exportação

---

## 📚 REFERÊNCIAS E LAYOUTS

### Documentação Speed
- Manual Speed Contábil (verificar versão)
- Layout de importação TXT
- Tabelas de códigos padrão

### Documentação SPED
- Guia Prático ECD (RFB)
- Guia Prático ECF (RFB)
- Manual EFD-Contribuições
- Validador PVA

### Referencial Contábil
- Plano de Contas Referencial (CPC/RFB)
- Mapeamento Simples Nacional × Referencial

---

## ✅ PRÓXIMOS PASSOS (AGORA)

1. **Criar migration** para adicionar campos Speed
2. **Atualizar formulário** de Plano de Contas
3. **Criar endpoint** de exportação básica
4. **Testar** mapeamento com 10 contas
5. **Documentar** fluxo de integração

---

**Observações:**
- Integração Speed é **unidirecional** (exportação)
- Manter sempre **backup** antes de exportar
- Validar com contador antes de transmitir SPED
- Certificado digital obrigatório para transmissão oficial
