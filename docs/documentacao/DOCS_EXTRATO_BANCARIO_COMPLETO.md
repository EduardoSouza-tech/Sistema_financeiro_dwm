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
1. Transação aparece na lista como "⏳ Pendente"
2. Usuário clica no botão "🔗 Conciliar"
3. Modal abre com dados pré-preenchidos:
   - Descrição da transação
   - Valor (já formatado)
   - Tipo (Despesa/Receita)
   - Categoria (filtrada por tipo)
   - Razão Social (matching automático se tiver CPF/CNPJ)
4. Usuário ajusta categoria/subcategoria/razão social
5. Clica em "✅ Conciliar"
6. Sistema:
   - Cria lançamento com status PAGO
   - data_pagamento = data da transação
   - Marca transação como conciliada (TRUE)
   - Vincula IDs (lancamento_id)
7. Badge muda para "✅ Conciliado" (verde)
```

### Passo 3: Desconciliação (se necessário)
```
1. Transação aparece como "✅ Conciliado"
2. Usuário clica no botão "🔙 Desconciliar"
3. Modal de confirmação:
   "⚠️ Deseja realmente desconciliar esta transação?
    
    Isso irá:
    - Marcar a transação como NÃO conciliada
    - EXCLUIR o lançamento criado em Contas a Pagar/Receber
    
    Esta ação não pode ser desfeita!"
4. Usuário confirma
5. Sistema:
   - Exclui lançamento (DELETE FROM lancamentos)
   - Marca transação como NÃO conciliada (FALSE)
   - Limpa lancamento_id (NULL)
6. Badge volta para "⏳ Pendente"
7. Transação pode ser conciliada novamente
```

---

## 🧠 Matching Inteligente

### Como Funciona a Detecção de CPF/CNPJ

O sistema analisa a **descrição** de cada transação e:

#### 1. **Extração de Números**
```javascript
const descricao = "PIX RECEBIDO CPF 123.456.789-00 JOAO";
const numeros = descricao.replace(/\D/g, ''); // "12345678900"
```

#### 2. **Identificação de Padrão**
```javascript
if (numeros.length === 11) {
    // É CPF
} else if (numeros.length === 14) {
    // É CNPJ
}
```

#### 3. **Busca no Cadastro**
```python
if transacao['tipo'] == 'CREDITO':
    # Busca em clientes
    razao_social = clientes_dict.get(cpf_cnpj_limpo, '')
else:
    # Busca em fornecedores
    razao_social = fornecedores_dict.get(cpf_cnpj_limpo, '')
```

### Exemplos de Detecção

#### ✅ Exemplo 1: PIX com CPF
```
Descrição: "PIX RECEBIDO CPF 123.456.789-00 JOAO SILVA"
       ↓
Sistema extrai: "12345678900" (11 dígitos = CPF)
       ↓
Tipo: CREDITO → Busca em clientes
       ↓
Encontra: "João Silva Ltda"
       ↓
Preenche automaticamente no campo "Razão Social"
```

#### ✅ Exemplo 2: TED com CNPJ
```
Descrição: "TED ENVIADA CNPJ 12.345.678/0001-99 ACME CORP"
       ↓
Sistema extrai: "12345678000199" (14 dígitos = CNPJ)
       ↓
Tipo: DEBITO → Busca em fornecedores
       ↓
Encontra: "ACME Corporation LTDA"
       ↓
Preenche automaticamente no campo "Razão Social"
```

#### ⚠️ Exemplo 3: Sem CPF/CNPJ
```
Descrição: "PAGAMENTO DE CONTA DE LUZ"
       ↓
Nenhum número encontrado ou não bate com padrão
       ↓
Campo "Razão Social" fica VAZIO
       ↓
Usuário precisa preencher manualmente
```

---

## 🔗 Conciliação Individual

### Interface do Modal

```
┌─────────────────────────────────────────────────┐
│  🔄 Conciliar Transação                         │
├─────────────────────────────────────────────────┤
│  Configure categoria/subcategoria e razão       │
│  social para conciliar                          │
├─────────────────────────────────────────────────┤
│                                                 │
│  💰 Valor: R$ -4.500,00                        │
│  📝 Descrição: PAGAMENTO PIX CPF 12345...      │
│                                                 │
│  📂 Categoria: [Dropdown]                       │
│     ├─ DESPESAS DE ESCRITÓRIO                  │
│     ├─ DESPESAS PROCESSUAIS                    │
│     └─ ...                                      │
│                                                 │
│  📁 Subcategoria: [Dropdown]                    │
│     ├─ UNIFORME E EPI                          │
│     ├─ MATERIAL DE LIMPEZA                     │
│     └─ ...                                      │
│                                                 │
│  🏢 Razão Social: [Input]                      │
│     └─ EVERLIMP PRODUTOS DE LIMPEZA            │
│        (preenchido automaticamente)            │
│                                                 │
│  [Cancelar]  [✅ Conciliar]                    │
└─────────────────────────────────────────────────┘
```

### Validações

Antes de criar o lançamento, o sistema valida:

✅ **Categoria**: Obrigatória
✅ **Subcategoria**: Obrigatória
✅ **Valor**: Deve ser válido e não zero
⚠️ **Razão Social**: Opcional (mas recomendado)

---

## 🔙 Desconciliação

### Quando Usar

Use a desconciliação quando:
- ❌ Conciliou com categoria errada
- ❌ Conciliou com subcategoria errada
- ❌ Vinculou ao cliente/fornecedor errado
- ❌ Duplicou lançamento por engano

### O Que Acontece

1. **Exclusão do Lançamento**
   ```sql
   DELETE FROM lancamentos WHERE id = {lancamento_id};
   ```

2. **Atualização da Transação**
   ```sql
   UPDATE transacoes_extrato 
   SET conciliado = FALSE, lancamento_id = NULL 
   WHERE id = {transacao_id};
   ```

3. **Resultado**
   - ✅ Transação volta para "⏳ Pendente"
   - ✅ Lançamento é removido de Contas a Pagar/Receber
   - ✅ Pode ser conciliada novamente

### Interface de Confirmação

```
┌─────────────────────────────────────────────────┐
│  ⚠️ CONFIRMAÇÃO DE DESCONCILIAÇÃO               │
├─────────────────────────────────────────────────┤
│                                                 │
│  Deseja realmente desconciliar esta transação?  │
│                                                 │
│  Isso irá:                                      │
│  • Marcar a transação como NÃO conciliada      │
│  • EXCLUIR o lançamento criado em Contas a     │
│    Pagar/Receber                                │
│                                                 │
│  ⚠️ Esta ação não pode ser desfeita!           │
│                                                 │
│  [Cancelar]  [🔙 Sim, Desconciliar]           │
└─────────────────────────────────────────────────┘
```

---

## 📐 Regras de Negócio

### Tipo de Lançamento

| Tipo no Extrato | Tipo de Lançamento | Onde Aparece          |
|-----------------|--------------------|-----------------------|
| CREDITO (+)     | RECEITA           | Contas a Receber      |
| DEBITO (-)      | DESPESA           | Contas a Pagar        |

### Status do Lançamento

**Sempre PAGO** porque a transação já aconteceu no banco:
```python
status = StatusLancamento.PAGO
data_pagamento = data_transacao  # Data que passou no banco
```

### Categorias Filtradas

O sistema filtra as categorias disponíveis baseado no tipo:

**DEBITO** → Mostra apenas categorias tipo **DESPESA**
**CREDITO** → Mostra apenas categorias tipo **RECEITA**

### Valores

- **Sempre positivos** nos lançamentos (usa `abs()`)
- **Cores na interface**:
  - 💵 Verde: Créditos (dinheiro entrando)
  - 💸 Vermelho: Débitos (dinheiro saindo)

---

## 🔌 API Endpoints

### GET `/api/extratos`
**Descrição**: Lista todas as transações do extrato

**Permissão**: `lancamentos_view`

**Query Parameters**:
- `conta_bancaria` (opcional): Filtrar por conta
- `data_inicio` (opcional): Data inicial
- `data_fim` (opcional): Data final
- `conciliado` (opcional): true/false

**Response 200**:
```json
[
  {
    "id": 3529,
    "conta_bancaria": "ITAU-CONSERVADORA NEVES ALCANTARA - 9012/12311-4",
    "data": "2024-11-02T00:00:00",
    "tipo": "DEBITO",
    "valor": -4500.00,
    "descricao": "PAGAMENTO PIX CPF 12345678900",
    "saldo": 52500.00,
    "conciliado": false,
    "lancamento_id": null,
    "empresa_id": 1
  }
]
```

### POST `/api/extratos/conciliacao-geral`
**Descrição**: Concilia uma ou mais transações do extrato

**Permissão**: `lancamentos_create`

**Request Body**:
```json
{
  "transacoes": [
    {
      "transacao_id": 3529,
      "razao_social": "EVERLIMP PRODUTOS DE LIMPEZA",
      "categoria": "DESPESAS PROCESSUAIS",
      "subcategoria": "PROCESSOS JUDICIAIS"
    }
  ]
}
```

**Response 200**:
```json
{
  "success": true,
  "criados": 1,
  "erros": [],
  "message": "1 lançamento(s) criado(s) com sucesso"
}
```

**Response 400/500**:
```json
{
  "success": false,
  "error": "Mensagem de erro"
}
```

### POST `/api/extratos/<id>/desconciliar`
**Descrição**: Desfaz a conciliação de uma transação

**Permissão**: `lancamentos_delete`

**Path Parameter**:
- `id`: ID da transação do extrato

**Response 200**:
```json
{
  "success": true,
  "message": "Desconciliação realizada com sucesso"
}
```

**Response 404**:
```json
{
  "success": false,
  "error": "Transação não encontrada"
}
```

**Response 400**:
```json
{
  "success": false,
  "error": "Transação não está conciliada"
}
```

---

## 🐛 Troubleshooting

### Problema: Botão "Conciliar" não aparece

**Causa**: Transação já está conciliada

**Solução**: Verifique o badge. Se estiver "✅ Conciliado", use "🔙 Desconciliar" primeiro.

---

### Problema: Razão Social não preenche automaticamente

**Causa**: CPF/CNPJ não encontrado na descrição ou não cadastrado

**Solução**:
1. Verifique se a descrição tem CPF/CNPJ
2. Verifique se cliente/fornecedor está cadastrado
3. Preencha manualmente se necessário

---

### Problema: Categoria não aparece no dropdown

**Causa**: Categoria é do tipo errado (Despesa vs Receita)

**Solução**:
- **DEBITO** → Cadastre categoria tipo DESPESA
- **CREDITO** → Cadastre categoria tipo RECEITA

---

### Problema: Lançamento não aparece em Contas a Pagar/Receber

**Causa 1**: Status PENDENTE (versão antiga - corrigido)

**Solução**: Lançamentos agora são criados com status **PAGO**

**Causa 2**: Filtros ativos na tela

**Solução**: Limpe os filtros de data/status

---

### Problema: Erro "dictionary is an invalid keyword argument"

**Causa**: Bug no cursor do PostgreSQL (corrigido)

**Solução**: Atualizar para versão mais recente (usa `psycopg2.extras.RealDictCursor`)

---

### Problema: Erro "Lancamento.__init__() got unexpected keyword 'num_documento'"

**Causa**: Parâmetro inválido (corrigido)

**Solução**: Removido parâmetro `num_documento` da criação do lançamento

---

## 📊 Logs de Debug

O sistema gera logs detalhados para debug:

### Conciliação
```
🚀 ========== CONCILIAÇÃO GERAL INICIADA ==========
👤 Usuário: admin | Empresa ID: 1
📦 Recebidas 1 transação(ões) para conciliar
📋 Dados: {'transacoes': [{'transacao_id': 3529, ...}]}
✅ Lançamento criado: ID=79 para transação 3529
🔄 Executando UPDATE: transacao_id=3529, lancamento_id=79
📊 ANTES UPDATE: RealDictRow([('id', 3529), ('conciliado', False), ...])
📝 UPDATE: 1 linha(s) afetada(s)
✅ COMMIT OK
📊 DEPOIS UPDATE: RealDictRow([('id', 3529), ('conciliado', True), ...])
================================================================================
```

### Desconciliação
```
================================================================================
🔙 DESCONCILIAÇÃO INICIADA - Transação ID: 3529
📌 Transação: ID=3529, Conciliado=True, Lançamento ID=78
🗑️ Excluindo lançamento ID=78
✅ Lançamento 78 excluído
🔄 Desconciliando transação 3529
📝 UPDATE executado: 1 linha(s) afetada(s)
✅ COMMIT OK
✅ Desconciliação concluída com sucesso!
================================================================================
```

---

## 🎓 Melhores Práticas

### ✅ DO (Faça)

1. **Cadastre CPF/CNPJ completos** em clientes/fornecedores
2. **Verifique a categoria** antes de conciliar
3. **Use desconciliação** para corrigir erros
4. **Importe extratos regularmente** (mensal)
5. **Confira os valores** antes de confirmar

### ❌ DON'T (Não Faça)

1. **Não concilie transações duplicadas** (verifique antes)
2. **Não ignore erros de categoria** (pode atrapalhar relatórios)
3. **Não exclua transações manualmente** no banco (use desconciliar)
4. **Não concilie sem verificar** o cliente/fornecedor

---

## 📈 Estatísticas e Indicadores

O sistema rastreia:
- ✅ Total de transações importadas
- ✅ Total de transações conciliadas
- ✅ Total de transações pendentes
- ✅ Valor total conciliado
- ✅ Valor total pendente

---

## 🔐 Permissões Necessárias

| Ação                    | Permissão Necessária    |
|-------------------------|-------------------------|
| Ver extratos            | `lancamentos_view`      |
| Conciliar               | `lancamentos_create`    |
| Desconciliar            | `lancamentos_delete`    |
| Importar OFX            | `lancamentos_create`    |

---

## 📝 Changelog

### Versão 2.1 (23/01/2026)
- 🐛 **FIX**: Agora é possível **copiar texto e valores** das tabelas
  - Antes: `user-select: none` bloqueava toda seleção de texto
  - Depois: Células permitem cópia (CPF/CNPJ, valores, descrições)
  - Botões ainda não permitem seleção (comportamento correto)

### Versão 2.0 (23/01/2026)
- ✨ **NOVO**: Botão "Desconciliar" para desfazer conciliações
- ✨ **NOVO**: Modal de confirmação ao desconciliar
- 🐛 **FIX**: Status agora é PAGO (antes era PENDENTE)
- 🐛 **FIX**: Correção do método `excluir_lancamento`
- 🐛 **FIX**: Correção do cursor PostgreSQL (RealDictCursor)
- 🐛 **FIX**: Remoção do parâmetro `num_documento`
- 📚 Documentação completa atualizada

### Versão 1.0 (02/11/2024)
- ✨ Lançamento inicial
- ✨ Importação de OFX
- ✨ Conciliação individual
- ✨ Matching inteligente de CPF/CNPJ

---

## 🤝 Suporte

Dúvidas ou problemas? Entre em contato com a equipe de desenvolvimento.

**Sistema desenvolvido com ❤️ para otimizar sua gestão financeira!**
