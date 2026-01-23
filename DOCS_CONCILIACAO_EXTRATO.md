# 🏦 Documentação Completa - Extrato Bancário e Conciliação

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Estrutura do Sistema](#estrutura-do-sistema)
3. [Funcionalidades](#funcionalidades)
4. [Processo de Conciliação](#processo-de-conciliação)
5. [Matching Inteligente](#matching-inteligente)
6. [Conciliação Individual](#conciliação-individual)
7. [Desconciliação](#desconciliação)
8. [Regras de Negócio](#regras-de-negócio)
9. [API Endpoints](#api-endpoints)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O **Sistema de Extrato Bancário** é uma solução completa para importar, visualizar e conciliar transações bancárias com o sistema de contas a pagar e receber.

### Principais Recursos:
- 📤 **Importação de OFX**: Carrega extratos bancários diretamente do banco
- 🔍 **Visualização Completa**: Lista todas as transações com filtros e busca
- 🔗 **Conciliação Inteligente**: Transforma transações em lançamentos automaticamente
- 🎯 **Matching de CPF/CNPJ**: Detecta e vincula clientes/fornecedores automaticamente
- 🔙 **Desconciliação**: Desfaz conciliações erradas
- 📊 **Rastreabilidade Total**: Mantém vínculo entre extrato e lançamentos

---

## 🏗️ Estrutura do Sistema

### Banco de Dados

#### Tabela: `transacoes_extrato`
```sql
CREATE TABLE transacoes_extrato (
    id SERIAL PRIMARY KEY,
    conta_bancaria VARCHAR(200) NOT NULL,
    data TIMESTAMP NOT NULL,
    tipo VARCHAR(20) NOT NULL,           -- CREDITO ou DEBITO
    valor DECIMAL(15, 2) NOT NULL,
    descricao TEXT,
    saldo DECIMAL(15, 2),
    conciliado BOOLEAN DEFAULT FALSE,
    lancamento_id INTEGER,               -- FK para lancamentos
    empresa_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Fluxo de Dados

```
┌─────────────────────────┐
│   Arquivo OFX (Banco)   │
└───────────┬─────────────┘
            │
            ↓ Importação
┌─────────────────────────┐
│  transacoes_extrato     │
│  (conciliado = FALSE)   │
└───────────┬─────────────┘
            │
            ↓ Conciliação
┌─────────────────────────┐
│      lancamentos        │
│    (status = PAGO)      │
└───────────┬─────────────┘
            │
            ↓ Atualização
┌─────────────────────────┐
│  transacoes_extrato     │
│  (conciliado = TRUE)    │
│  (lancamento_id = X)    │
└─────────────────────────┘
```

---

## ✨ Funcionalidades

### 1. **Visualização de Transações**
- 📋 Lista todas as transações importadas
- 🔍 Filtros por:
  - Conta bancária
  - Período (data início/fim)
  - Status (conciliado/pendente)
  - Tipo (crédito/débito)
- 🎯 Busca em tempo real
- 💰 Saldo total e por conta

### 2. **Conciliação Individual**
- 🔗 Botão "Conciliar" em cada transação pendente
- 📝 Modal com formulário completo:
  - Categoria (automática por tipo)
  - Subcategoria
  - Razão Social (com matching inteligente)
- ✅ Cria lançamento automaticamente
- 🔒 Marca transação como conciliada

### 3. **Conciliação em Massa**
- ☑️ Seleção múltipla com checkboxes
- ✅ Botão "Conciliar Selecionados"
- 📋 Modal com tabela de configuração:
  - Uma linha por transação
  - Categoria/subcategoria individuais
  - Razão social por transação
- 🚀 Processa todas simultaneamente

### 4. **Desconciliação**
- 🔙 Botão "Desconciliar" em transações conciliadas
- ⚠️ Modal de confirmação com aviso claro
- 🗑️ Exclui lançamento automaticamente
- ♻️ Marca transação como não conciliada
- ✅ Permite corrigir erros

### 5. **Indicadores Visuais**
- ✅ Badge verde "Conciliado" quando já conciliado
- ⏳ Badge laranja "Pendente" quando não conciliado
- 💵 Valores verdes para créditos
- 💸 Valores vermelhos para débitos
- 📊 Saldo da transação exibido

---

## 🔄 Processo de Conciliação

### Passo 1: Importação
```
1. Usuário acessa "Extrato Bancário"
2. Clica em "📤 Importar OFX"
3. Seleciona arquivo do banco
4. Sistema processa e salva transações
5. Transações aparecem na lista como "⏳ Pendente"
```

### Passo 2: Conciliação Individual
```
Descrição: "COMPRA SUPERMERCADO XYZ"
       ↓
Sistema não encontra CPF/CNPJ
       ↓
Campo fica vazio (usuário preenche manualmente)
```

---

## 📖 Guia de Uso Passo a Passo

### **PASSO 1: Importar Extrato OFX**

1. Acesse: **🏦 Extrato Bancário - Importação OFX**
2. Selecione a **Conta Bancária**
3. Escolha o **Arquivo OFX** (baixado do internet banking)
4. Clique em **⬆️ Enviar Arquivo**
5. Aguarde confirmação de importação

### **PASSO 2: Filtrar Transações (Opcional)**

Para conciliar apenas um período específico:

1. **Data Início**: Selecione data inicial
2. **Data Fim**: Selecione data final
3. **Conta**: Escolha conta específica (ou "Todas")
4. **Status**: Selecione "Não conciliados"
5. Clique em **🔍 Pesquisar** (ou deixe em branco para ver tudo)

### **PASSO 3: Abrir Conciliação Geral**

1. Clique no botão **🔄 Conciliação Geral** (canto superior direito)
2. Modal abrirá com todas transações não conciliadas
3. Visualize:
   - Quantidade de transações
   - Período filtrado
   - Conta bancária

### **PASSO 4: Configurar De-Para**

Para cada transação:

#### **A) Razão Social** (quem pagou/recebeu)
- **Automático**: Se houver CPF/CNPJ na descrição, campo já vem preenchido
- **Manual**: Digite ou selecione do autocomplete
- **Crédito**: Normalmente é um Cliente
- **Débito**: Normalmente é um Fornecedor

#### **B) Categoria** (tipo de receita/despesa)
- **Obrigatório**: Selecione uma categoria
- **Filtrada automaticamente**:
  - Crédito → Mostra apenas categorias de RECEITA
  - Débito → Mostra apenas categorias de DESPESA
- Exemplos:
  - Crédito: "Vendas", "Serviços Prestados"
  - Débito: "Despesas com Pessoal", "Fornecedores"

#### **C) Subcategoria** (detalhamento)
- **Opcional**: Selecione se houver subcategorias
- **Dinâmico**: Carrega automaticamente ao selecionar categoria
- Exemplos:
  - Categoria "Despesas com Pessoal" → Subcategoria "Salários"
  - Categoria "Fornecedores" → Subcategoria "Matéria Prima"

### **PASSO 5: Selecionar Transações**

1. **Seleção Individual**: Marque checkbox de cada transação
2. **Seleção em Massa**: Marque "Selecionar Todas" no topo
3. **Dica**: Configure categorias antes de selecionar

### **PASSO 6: Processar Conciliação**

1. Clique em **✅ Conciliar Selecionados**
2. Confirme no pop-up
3. Aguarde processamento
4. Veja resultado:
   - ✅ Quantidade de lançamentos criados
   - ⚠️ Erros (se houver)

### **PASSO 7: Verificar Resultado**

1. Acesse **💰 Lançamentos**
2. Busque por descrição "[EXTRATO]"
3. Confira:
   - Status = **PAGO** ✅
   - Data vencimento = Data do extrato
   - Valor = Valor do extrato
   - Categoria = Configurada por você

---

## 🔄 Campos Automáticos vs Manuais

### ✅ Campos Preenchidos AUTOMATICAMENTE

| Campo | Origem | Exemplo |
|-------|--------|---------|
| **Data de Vencimento** | Data da transação do extrato | 22/01/2026 |
| **Data de Pagamento** | Data da transação do extrato | 22/01/2026 |
| **Valor** | Valor da transação (absoluto) | R$ 1.500,00 |
| **Descrição** | "[EXTRATO] " + descrição original | [EXTRATO] PIX RECEBIDO CPF 12345678900 |
| **Tipo** | RECEITA (crédito) ou DESPESA (débito) | RECEITA |
| **Status** | PAGO (já foi pago/recebido) | PAGO |
| **Conta Bancária** | Conta do extrato | Itaú - Conta Corrente |
| **Num. Documento** | ID da transação do extrato | 12345 |
| **Observações** | Texto padrão + ID | Conciliado automaticamente do extrato. ID: 12345 |
| **Razão Social*** | CPF/CNPJ detectado (se houver) | João Silva Ltda |

\* Preenchido automaticamente apenas se CPF/CNPJ for detectado na descrição

### 👤 Campos Preenchidos MANUALMENTE

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| **Razão Social** | ⚠️ Opcional* | Cliente (crédito) ou Fornecedor (débito) |
| **Categoria** | ✅ Obrigatório | Tipo de receita/despesa |
| **Subcategoria** | ❌ Opcional | Detalhamento da categoria |

\* Se não preencher, lançamento será criado sem pessoa associada

---

## 📜 Regras de Negócio

### 1. **Tipo de Lançamento**

| Tipo Extrato | Tipo Lançamento | Destino |
|--------------|-----------------|---------|
| **CREDITO** (dinheiro entrando) | RECEITA | Contas a Receber |
| **DEBITO** (dinheiro saindo) | DESPESA | Contas a Pagar |

### 2. **Status do Lançamento**

- **SEMPRE** criado com status **PAGO**
- Motivo: A transação já aconteceu (está no extrato bancário)
- Data de vencimento = Data de pagamento

### 3. **Validações**

Antes de criar lançamento, sistema valida:

| Validação | Regra | Mensagem de Erro |
|-----------|-------|------------------|
| Categoria selecionada | Obrigatório | "categoria não selecionada" |
| Transação existe | Deve existir no banco | "Transação X não encontrada" |
| Transação não conciliada | Não pode estar conciliada | (ignora silenciosamente) |

### 4. **Matching CPF/CNPJ**

```python
# Lógica de detecção
numeros = extrair_apenas_numeros(descricao)

if len(numeros) == 11:  # CPF
    tipo_documento = "CPF"
elif len(numeros) == 14:  # CNPJ
    tipo_documento = "CNPJ"
else:
    tipo_documento = None  # Não detectado

# Busca no cadastro
if tipo == CREDITO:
    buscar_em = clientes
else:
    buscar_em = fornecedores

if encontrou:
    preencher_razao_social(nome_encontrado)
```

### 5. **Rastreabilidade**

Sistema mantém vínculo:
```
Transação Extrato (ID: 12345)
        ↕️
   Lançamento
   └── num_documento = "12345"
   └── observacoes = "Conciliado do extrato. ID: 12345"
```

---

## 💡 Exemplos Práticos

### Exemplo 1: Recebimento de Cliente (CRÉDITO)

**Extrato Importado:**
```
Data: 20/01/2026
Tipo: CREDITO
Valor: R$ 5.000,00
Descrição: "PIX RECEBIDO CPF 12345678900 MARIA SANTOS"
Conta: Banco do Brasil - CC 12345-6
```

**Modal de Conciliação:**
```
✓ Selecionada
Data: 20/01/2026
Descrição: PIX RECEBIDO CPF 12345678900 MARIA SANTOS
Valor: R$ 5.000,00
Tipo: 🟢 Crédito

Razão Social: [Maria Santos Fotografia]  ← Preenchido automaticamente
Categoria: [Serviços Prestados ▼]        ← Usuário seleciona
Subcategoria: [Ensaio Newborn ▼]         ← Usuário seleciona (opcional)
```

**Lançamento Criado:**
```
Tipo: RECEITA
Status: PAGO ✅
Descrição: [EXTRATO] PIX RECEBIDO CPF 12345678900 MARIA SANTOS
Valor: R$ 5.000,00
Data Vencimento: 20/01/2026
Data Pagamento: 20/01/2026
Pessoa: Maria Santos Fotografia
Categoria: Serviços Prestados
Subcategoria: Ensaio Newborn
Conta: Banco do Brasil - CC 12345-6
Num. Documento: 12345 (ID do extrato)
Observações: Conciliado automaticamente do extrato bancário. ID Extrato: 12345
```

---

### Exemplo 2: Pagamento a Fornecedor (DÉBITO)

**Extrato Importado:**
```
Data: 21/01/2026
Tipo: DEBITO
Valor: R$ -1.200,00
Descrição: "PGTO BOLETO CNPJ 98765432000100 MATERIAL FOTO"
Conta: Itaú - CC 98765-4
```

**Modal de Conciliação:**
```
✓ Selecionada
Data: 21/01/2026
Descrição: PGTO BOLETO CNPJ 98765432000100 MATERIAL FOTO
Valor: R$ 1.200,00
Tipo: 🔴 Débito

Razão Social: [Material Fotográfico Ltda]  ← Preenchido automaticamente
Categoria: [Fornecedores ▼]                ← Usuário seleciona
Subcategoria: [Equipamentos ▼]             ← Usuário seleciona (opcional)
```

**Lançamento Criado:**
```
Tipo: DESPESA
Status: PAGO ✅
Descrição: [EXTRATO] PGTO BOLETO CNPJ 98765432000100 MATERIAL FOTO
Valor: R$ 1.200,00
Data Vencimento: 21/01/2026
Data Pagamento: 21/01/2026
Pessoa: Material Fotográfico Ltda
Categoria: Fornecedores
Subcategoria: Equipamentos
Conta: Itaú - CC 98765-4
Num. Documento: 12346 (ID do extrato)
```

---

### Exemplo 3: Transação Sem CPF/CNPJ (DÉBITO)

**Extrato Importado:**
```
Data: 22/01/2026
Tipo: DEBITO
Valor: R$ -350,00
Descrição: "COMPRA CARTAO 12345678 SUPERMERCADO ABC"
Conta: Santander - CC 54321-0
```

**Modal de Conciliação:**
```
✓ Selecionada
Data: 22/01/2026
Descrição: COMPRA CARTAO 12345678 SUPERMERCADO ABC
Valor: R$ 350,00
Tipo: 🔴 Débito

Razão Social: [________________]           ← Campo vazio (sem CPF/CNPJ)
                                              Usuário digita: "Supermercado ABC"
Categoria: [Despesas Operacionais ▼]      ← Usuário seleciona
Subcategoria: [Alimentação ▼]             ← Usuário seleciona
```

**Lançamento Criado:**
```
Tipo: DESPESA
Status: PAGO ✅
Descrição: [EXTRATO] COMPRA CARTAO 12345678 SUPERMERCADO ABC
Valor: R$ 350,00
Data Vencimento: 22/01/2026
Data Pagamento: 22/01/2026
Pessoa: Supermercado ABC                   ← Preenchido manualmente
Categoria: Despesas Operacionais
Subcategoria: Alimentação
Conta: Santander - CC 54321-0
```

---

## 🔧 Troubleshooting

### Problema 1: "Nenhuma transação não conciliada encontrada"

**Causa**: Todas transações já foram conciliadas ou não há transações no período

**Solução**:
1. Limpe os filtros (clique em 🔄 Limpar)
2. Verifique se importou o extrato OFX
3. Confira o filtro de Status (deve estar em "Não conciliados" ou "Todos")

---

### Problema 2: Razão Social não é preenchida automaticamente

**Causa**: CPF/CNPJ não foi detectado na descrição OU cliente/fornecedor não está cadastrado

**Solução**:
1. Verifique se a descrição do extrato contém CPF/CNPJ
2. Confira se cliente/fornecedor está cadastrado com CPF/CNPJ correto
3. Preencha manualmente usando o autocomplete
4. Cadastre o cliente/fornecedor antes de conciliar

---

### Problema 3: "Categoria não selecionada"

**Causa**: Tentou conciliar sem selecionar categoria

**Solução**:
1. Selecione uma categoria no dropdown de cada transação selecionada
2. Categoria é **obrigatória** (subcategoria é opcional)

---

### Problema 4: Subcategoria não carrega

**Causa**: Categoria não possui subcategorias cadastradas

**Solução**:
1. Campo fica desabilitado (normal)
2. Se necessário, cadastre subcategorias em **📂 Categorias e Subcategorias**
3. Ou deixe em branco (subcategoria é opcional)

---

### Problema 5: Lançamento criado duplicado

**Causa**: Conciliou a mesma transação duas vezes

**Solução**:
1. Sistema marca transação como conciliada automaticamente
2. Filtre por "Não conciliados" para evitar duplicatas
3. Se criou duplicado, exclua o lançamento manualmente em **💰 Lançamentos**

---

### Problema 6: Valor do lançamento está errado

**Causa**: Valor é extraído diretamente do extrato OFX

**Solução**:
1. Confira se o arquivo OFX está correto
2. Reimporte o extrato se necessário
3. Ou edite o lançamento manualmente após conciliar

---

## 📊 Fluxo Completo Simplificado

```
┌─────────────────────────────────────────────────────────────┐
│  1. IMPORTAR EXTRATO OFX                                    │
│     • Selecionar conta bancária                             │
│     • Escolher arquivo .ofx                                 │
│     • Clicar em "Enviar Arquivo"                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. FILTRAR TRANSAÇÕES (Opcional)                           │
│     • Data inicial / Data final                             │
│     • Conta bancária                                        │
│     • Status: "Não conciliados"                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. ABRIR CONCILIAÇÃO GERAL                                 │
│     • Clicar em botão "🔄 Conciliação Geral"                │
│     • Modal abre com transações não conciliadas             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. CONFIGURAR DE-PARA (para cada transação)                │
│     • Razão Social (automático se tiver CPF/CNPJ)           │
│     • Categoria (obrigatório)                               │
│     • Subcategoria (opcional)                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  5. SELECIONAR TRANSAÇÕES                                   │
│     • Marcar checkboxes individualmente                     │
│     • OU marcar "Selecionar Todas"                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  6. PROCESSAR CONCILIAÇÃO                                   │
│     • Clicar em "✅ Conciliar Selecionados"                 │
│     • Confirmar no pop-up                                   │
│     • Aguardar processamento                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  7. RESULTADO                                               │
│     • ✅ X lançamentos criados                              │
│     • ⚠️ Erros (se houver)                                   │
│     • Lançamentos aparecem em "💰 Lançamentos"              │
│     • Status = PAGO                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎓 Dicas de Uso

### ✅ Boas Práticas

1. **Cadastre clientes/fornecedores com CPF/CNPJ**
   - Facilita matching automático
   - Economiza tempo no preenchimento

2. **Configure categorias antes de importar**
   - Organize suas categorias
   - Crie subcategorias para melhor detalhamento

3. **Importe extratos regularmente**
   - Semanal ou quinzenal
   - Evita acúmulo de transações

4. **Use filtros de período**
   - Concilie por mês
   - Facilita organização contábil

5. **Revise antes de conciliar**
   - Confira valores e datas
   - Valide razão social sugerida
   - Escolha categoria adequada

### ⚠️ Cuidados

1. **Não concilie a mesma transação duas vezes**
   - Use filtro "Não conciliados"
   - Sistema marca automaticamente

2. **Verifique descrições do banco**
   - Nem sempre CPF/CNPJ vem correto
   - Confira se matching encontrou pessoa certa

3. **Categorias devem estar corretas**
   - Crédito = Receita
   - Débito = Despesa
   - Não confunda os tipos

4. **Backup antes de importar volumes grandes**
   - Faça backup do banco
   - Teste com poucos registros primeiro

---

## 🔐 Segurança e Rastreabilidade

### Auditoria

Todos lançamentos criados pela conciliação possuem:

1. **Identificação clara**: "[EXTRATO]" no início da descrição
2. **ID do extrato**: Armazenado no campo `num_documento`
3. **Observações detalhadas**: Texto padrão com ID
4. **Vínculo com extrato**: Coluna `lancamento_id` na tabela `transacoes_extrato`

### Rastreamento

Para encontrar origem de um lançamento:

```sql
-- Buscar lançamento
SELECT * FROM lancamentos WHERE descricao LIKE '[EXTRATO]%';

-- Buscar transação do extrato relacionada
SELECT * FROM transacoes_extrato WHERE id = [num_documento];
```

### Reversão

Se precisar desfazer conciliação:

1. **Excluir lançamento**: Menu 💰 Lançamentos → Botão Excluir
2. **Desmarcar extrato**:
```sql
UPDATE transacoes_extrato 
SET conciliado = FALSE, lancamento_id = NULL 
WHERE id = [ID];
```

---

## 📞 Suporte

Em caso de dúvidas ou problemas:

1. Consulte esta documentação
2. Verifique o [Troubleshooting](#troubleshooting)
3. Entre em contato com o suporte técnico
4. Relate bugs com:
   - Passos para reproduzir
   - Mensagem de erro (se houver)
   - Screenshots (se possível)

---

## 📝 Changelog

### Versão 1.0.0 (22/01/2026)
- ✨ Lançamento inicial da funcionalidade
- 🧠 Matching inteligente de CPF/CNPJ
- 🔄 Conciliação em massa
- 📋 Modal de de-para completo
- ✅ Criação automática de lançamentos
- 📊 Interface responsiva

---

**Última atualização**: 22 de Janeiro de 2026  
**Versão**: 1.0.0  
**Autor**: Sistema Financeiro DWM
