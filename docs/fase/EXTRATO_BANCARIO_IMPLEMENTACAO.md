# 🏦 Implementação do Extrato Bancário

## Resumo da Funcionalidade

Sistema completo de importação e conciliação de extratos bancários no formato OFX, com sugestões inteligentes de conciliação baseadas em valor e data.

---

## 📋 Funcionalidades Implementadas

### 1. **Importação de Extratos OFX**
- Upload de arquivos OFX diretamente pela interface
- Seleção da conta bancária associada
- Prevenção automática de duplicatas usando FITID (Financial Transaction ID)
- Feedback detalhado: quantas transações foram inseridas e quantas duplicadas

### 2. **Listagem e Filtros**
- Visualização de todas as transações importadas
- Filtros por:
  - Conta bancária
  - Período (data início e fim)
  - Status de conciliação (Todos/Conciliados/Não Conciliados)
- Exibição de:
  - Data da transação
  - Descrição completa
  - Valor (colorido: verde para créditos, vermelho para débitos)
  - Tipo (CREDITO/DEBITO)
  - Saldo após transação
  - Status de conciliação

### 3. **Conciliação Inteligente**
- **Sugestões Automáticas**: Sistema busca lançamentos similares com base em:
  - Valor (±5% de tolerância)
  - Data (±7 dias de diferença)
  - Mesma conta bancária
- **Match Score**: Exibe percentual de similaridade e diferença de dias
- **Conciliação Manual**: Possibilidade de selecionar qualquer lançamento da lista
- **Desconciliação**: Remover vínculo entre transação e lançamento

### 4. **Segurança Multi-Tenant**
- Todas as operações filtradas por `empresa_id`
- Autenticação via token JWT
- Permissões baseadas em roles

---

## 🗄️ Estrutura do Banco de Dados

### Tabela: `transacoes_extrato`

```sql
CREATE TABLE IF NOT EXISTS transacoes_extrato (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    conta_bancaria VARCHAR(255) NOT NULL,
    data DATE NOT NULL,
    descricao TEXT NOT NULL,
    valor DECIMAL(15,2) NOT NULL,
    tipo VARCHAR(10) NOT NULL,  -- 'CREDITO' ou 'DEBITO'
    saldo DECIMAL(15,2),
    fitid VARCHAR(255),  -- ID único da transação no OFX
    memo TEXT,
    checknum VARCHAR(50),
    conciliado BOOLEAN DEFAULT FALSE,
    lancamento_id INTEGER,
    importacao_id VARCHAR(100),  -- ID do lote de importação
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id) ON DELETE SET NULL
);
```

### Índices de Performance

1. `idx_extrato_empresa_conta` - (empresa_id, conta_bancaria)
2. `idx_extrato_data` - (data)
3. `idx_extrato_conciliado` - (conciliado)
4. `idx_extrato_fitid` - (fitid)

---

## 🔧 Backend - API Endpoints

### 1. **POST** `/api/extratos/upload`
**Descrição**: Importa arquivo OFX e salva transações

**Parâmetros**:
- `arquivo` (file): Arquivo OFX
- `conta_bancaria` (string): Nome da conta bancária

**Resposta**:
```json
{
    "success": true,
    "inseridas": 45,
    "duplicadas": 3,
    "importacao_id": "uuid-123..."
}
```

### 2. **GET** `/api/extratos`
**Descrição**: Lista transações do extrato com filtros

**Query Parameters**:
- `conta` (opcional): Filtrar por conta bancária
- `data_inicio` (opcional): Data inicial (YYYY-MM-DD)
- `data_fim` (opcional): Data final (YYYY-MM-DD)
- `conciliado` (opcional): true/false

**Resposta**:
```json
[
    {
        "id": 1,
        "data": "2024-01-15",
        "descricao": "TED RECEBIDA",
        "valor": 1500.00,
        "tipo": "CREDITO",
        "saldo": 3500.00,
        "conciliado": false,
        "lancamento_id": null,
        "conta_bancaria": "Banco do Brasil - CC"
    }
]
```

### 3. **POST** `/api/extratos/<id>/conciliar`
**Descrição**: Concilia ou desconcilia transação

**Body**:
```json
{
    "lancamento_id": 123  // ou null para desconciliar
}
```

### 4. **GET** `/api/extratos/<id>/sugestoes`
**Descrição**: Busca sugestões inteligentes de conciliação

**Resposta**:
```json
[
    {
        "id": 456,
        "descricao": "Recebimento Cliente XYZ",
        "valor": 1450.00,
        "data_vencimento": "2024-01-14",
        "tipo": "RECEBER",
        "conta_id": 1
    }
]
```

### 5. **DELETE** `/api/extratos/importacao/<importacao_id>`
**Descrição**: Remove todas as transações de uma importação

---

## 💻 Frontend - Interface do Usuário

### Página Principal: `🏦 Extrato Bancário`

#### Card de Importação
- **Select**: Escolher conta bancária
- **Input File**: Selecionar arquivo OFX
- **Botão Importar**: Executa upload e processamento

#### Filtros
- Conta bancária
- Data início
- Data fim
- Status de conciliação
- Botões: Filtrar e Limpar

#### Tabela de Transações
Colunas:
1. **Data**: Formatada (DD/MM/YYYY)
2. **Descrição**: Texto completo da transação
3. **Valor**: Colorido (verde/vermelho)
4. **Tipo**: Badge (CREDITO/DEBITO)
5. **Saldo**: Saldo após transação
6. **Status**: ✅ Conciliado / ⏳ Pendente
7. **Ações**: 
   - 🔗 Conciliar (se pendente)
   - 👁️ Ver (se conciliado)

### Modal de Conciliação

#### Header
- Título: "🔗 Conciliar Transação"
- Botão fechar (X)

#### Body
1. **Card de Informações**: 
   - Data, Conta, Descrição, Valor da transação

2. **Tabela de Sugestões**:
   - Lista de lançamentos compatíveis
   - Match score e diferença de dias
   - Clique na linha para conciliar

3. **Rodapé**:
   - Botão Cancelar
   - Botão Desconciliar (apenas se já conciliado)

---

## 📁 Arquivos Modificados/Criados

### Backend
1. **`database_postgresql.py`** (Linhas 642-688)
   - Criação da tabela `transacoes_extrato`
   - 4 índices de performance

2. **`extrato_functions.py`** (NOVO - 301 linhas)
   - `salvar_transacoes_extrato()`
   - `listar_transacoes_extrato()`
   - `conciliar_transacao()`
   - `sugerir_conciliacoes()`
   - `deletar_transacoes_extrato()`

3. **`web_server.py`** (Linhas 1406-1553)
   - 5 novos endpoints REST

4. **`requirements_web.txt`**
   - Adicionado: `ofxparse==0.21`

### Frontend
1. **`templates/index.html`**
   - Menu item (Linha 25)
   - Página completa (Linhas 175-231)
   - Modal de conciliação (Linhas 628-658)

2. **`static/app.js`**
   - Função `loadContasForExtrato()`
   - Função `importarExtrato()`
   - Função `loadExtratos()`
   - Função `mostrarSugestoesConciliacao()`
   - Função `mostrarDetalheConciliacao()`
   - Função `conciliarTransacao()`
   - Função `desconciliarTransacao()`
   - Função `aplicarFiltrosExtrato()`
   - Função `limparFiltrosExtrato()`
   - Case no `showPage()` para carregar extrato

---

## 🎯 Fluxo de Uso

### 1. Importar Extrato
```
Usuário seleciona conta → Escolhe arquivo OFX → Clica "Importar"
↓
Sistema processa OFX → Verifica duplicatas (FITID) → Salva no banco
↓
Exibe resultado: X inseridas, Y duplicadas
```

### 2. Visualizar e Filtrar
```
Sistema carrega todas as transações → Usuário aplica filtros
↓
Tabela atualizada com transações filtradas
```

### 3. Conciliar Transação
```
Usuário clica "🔗 Conciliar" → Modal abre com sugestões
↓
Sistema busca lançamentos compatíveis (±5% valor, ±7 dias)
↓
Usuário clica em sugestão → Sistema vincula transação ao lançamento
↓
Status muda para "✅ Conciliado"
```

### 4. Desconciliar
```
Usuário clica "👁️ Ver" em transação conciliada
↓
Modal mostra detalhes e botão "❌ Desconciliar"
↓
Usuário confirma → Sistema remove vínculo
↓
Status volta para "⏳ Pendente"
```

---

## 🔒 Segurança

### Autenticação
- Todos os endpoints requerem token JWT válido
- Função `@require_permission()` aplicada

### Autorização
- Permissões necessárias: `lancamentos_view`, `lancamentos_edit`, `lancamentos_delete`

### Multi-Tenant
- Todas as queries incluem filtro por `empresa_id`
- Usuário só vê dados da própria empresa

---

## 🚀 Próximos Passos (Melhorias Futuras)

1. **Exportação para Excel**: Exportar extratos filtrados
2. **Dashboard de Conciliação**: Métricas e gráficos
3. **Regras Automáticas**: Criar regras de conciliação automática
4. **Histórico de Importações**: Listar todas as importações realizadas
5. **Suporte a Outros Formatos**: CSV, QIF, etc.
6. **Reconciliação em Lote**: Conciliar múltiplas transações de uma vez
7. **Notificações**: Alertas sobre transações não conciliadas

---

## 📊 Algoritmo de Sugestão de Conciliação

### Critérios de Match

1. **Valor**: `lancamento.valor BETWEEN extrato.valor * 0.95 AND extrato.valor * 1.05`
   - Tolerância de ±5%

2. **Data**: `ABS(EXTRACT(EPOCH FROM (extrato.data - lancamento.data_vencimento)) / 86400) <= 7`
   - Diferença máxima de 7 dias

3. **Conta**: `extrato.conta_bancaria = conta.nome`
   - Mesma conta bancária

4. **Tipo**: 
   - CREDITO → Lançamentos a RECEBER
   - DEBITO → Lançamentos a PAGAR

5. **Status**: Apenas lançamentos não conciliados (`lancamento_id IS NULL`)

### Ordenação
- Por proximidade de valor (mais próximo primeiro)
- Limite de 10 sugestões

---

## 🧪 Testes Recomendados

### Teste 1: Importação Bem-Sucedida
1. Selecionar conta válida
2. Upload de arquivo OFX válido
3. Verificar mensagem de sucesso
4. Confirmar transações na tabela

### Teste 2: Prevenção de Duplicatas
1. Importar mesmo arquivo OFX duas vezes
2. Verificar que duplicadas são ignoradas

### Teste 3: Conciliação
1. Criar lançamento manual com valor e data similares
2. Importar extrato com transação compatível
3. Clicar em "Conciliar"
4. Verificar que sugestão aparece
5. Conciliar e verificar status

### Teste 4: Filtros
1. Aplicar filtro por conta
2. Aplicar filtro por período
3. Aplicar filtro por status
4. Verificar resultados corretos

### Teste 5: Desconciliação
1. Conciliar uma transação
2. Abrir modal de visualização
3. Clicar em "Desconciliar"
4. Verificar que status volta para Pendente

---

## 📝 Notas de Implementação

### Decisões Técnicas

1. **OFX Parser**: Escolhido `ofxparse` pela simplicidade e estabilidade
2. **FITID**: Usado como chave única para prevenir duplicatas (padrão OFX)
3. **Match Tolerance**: 5% para valor e 7 dias para data (configurável)
4. **Índices**: Criados em campos mais consultados para otimização
5. **Foreign Key**: `lancamento_id` com `ON DELETE SET NULL` para preservar histórico

### Limitações Conhecidas

1. Apenas formato OFX suportado (não CSV, QIF, etc.)
2. Sugestões limitadas a 10 resultados
3. Conciliação 1:1 (uma transação = um lançamento)
4. Sem suporte a transferências entre contas

---

## 🎨 Design UI/UX

### Cores e Ícones
- **Verde (#27ae60)**: Créditos, Conciliado, Sucesso
- **Vermelho (#c0392b)**: Débitos, Erros
- **Laranja (#f39c12)**: Pendente, Avisos
- **Azul (#3498db)**: Ações primárias

### Responsividade
- Layout flex para importação
- Tabela com scroll horizontal em telas pequenas
- Modal adaptável

---

**Implementado por**: GitHub Copilot  
**Data**: Janeiro 2024  
**Status**: ✅ Completo e Funcional
