# 🏦 Documentação - Conciliação Automática de Extrato Bancário

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Como Funciona](#como-funciona)
3. [Matching Inteligente](#matching-inteligente)
4. [Guia de Uso Passo a Passo](#guia-de-uso-passo-a-passo)
5. [Campos Automáticos vs Manuais](#campos-automáticos-vs-manuais)
6. [Regras de Negócio](#regras-de-negócio)
7. [Exemplos Práticos](#exemplos-práticos)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

A **Conciliação Automática de Extrato Bancário** é uma funcionalidade que permite transformar transações importadas do extrato bancário (arquivo OFX) em lançamentos de **Contas a Pagar** ou **Contas a Receber** de forma automática e inteligente.

### Benefícios:
- ✅ **Economia de tempo**: Processa múltiplas transações simultaneamente
- 🧠 **Inteligência artificial**: Detecta CPF/CNPJ e sugere cliente/fornecedor automaticamente
- 📊 **Organização**: Mantém rastreabilidade entre extrato e lançamento
- 🎯 **Precisão**: Valida dados antes de criar lançamentos
- 💰 **Controle financeiro**: Transforma dados bancários em informação gerencial

---

## ⚙️ Como Funciona

### 1. **Importação do Extrato**
```
📤 Usuário importa arquivo OFX
    ↓
💾 Sistema salva transações na tabela transacoes_extrato
    ↓
🔍 Transações ficam disponíveis para conciliação
```

### 2. **Processo de Conciliação**
```
🔄 Clique em "Conciliação Geral"
    ↓
📋 Sistema busca transações não conciliadas
    ↓
🧠 Matching inteligente de CPF/CNPJ
    ↓
👤 Usuário configura categoria/subcategoria
    ↓
✅ Sistema cria lançamentos em Contas a Pagar/Receber
    ↓
✔️ Marca transações como conciliadas
```

### 3. **Resultado Final**
- Lançamento criado com status **PAGO**
- Transação marcada como **CONCILIADA**
- Rastreabilidade mantida (ID do extrato no num_documento)

---

## 🧠 Matching Inteligente

### Como o Sistema Detecta CPF/CNPJ

O sistema analisa a **descrição** de cada transação do extrato e:

1. **Extrai números** da descrição
2. **Identifica padrões**:
   - 11 dígitos consecutivos = **CPF**
   - 14 dígitos consecutivos = **CNPJ**
3. **Busca no cadastro**:
   - **Crédito (dinheiro entrando)** → Busca em **Clientes**
   - **Débito (dinheiro saindo)** → Busca em **Fornecedores**
4. **Preenche automaticamente** se encontrar match

### Exemplos de Detecção

#### ✅ Detecta CPF:
```
Descrição: "PIX RECEBIDO CPF 123.456.789-00 JOAO SILVA"
       ↓
Sistema extrai: 12345678900
       ↓
Busca em clientes com CPF 123.456.789-00
       ↓
Preenche: "João Silva Ltda"
```

#### ✅ Detecta CNPJ:
```
Descrição: "PGTO FORN 12345678000199 ACME CORP"
       ↓
Sistema extrai: 12345678000199
       ↓
Busca em fornecedores com CNPJ 12.345.678/0001-99
       ↓
Preenche: "ACME Corporation"
```

#### ⚠️ Não Detecta (sem CPF/CNPJ):
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
