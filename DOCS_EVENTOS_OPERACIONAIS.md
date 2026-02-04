# 📋 DOCUMENTAÇÃO COMPLETA - EVENTOS OPERACIONAIS

## 📑 Índice

1. [Visão Geral](#visão-geral)
2. [Estrutura do Módulo](#estrutura-do-módulo)
3. [Funcionalidades Principais](#funcionalidades-principais)
4. [Gestão de Eventos](#gestão-de-eventos)
5. [Gestão de Equipes](#gestão-de-equipes)
6. [Funções e Setores](#funções-e-setores)
7. [Sistema de Assinatura](#sistema-de-assinatura)
8. [Sistema de Credenciamento](#sistema-de-credenciamento)
9. [API Endpoints](#api-endpoints)
10. [Estrutura do Banco de Dados](#estrutura-do-banco-de-dados)
11. [Funções JavaScript](#funções-javascript)
12. [Fluxo de Trabalho](#fluxo-de-trabalho)

---

## 🎯 Visão Geral

O módulo **🎉 Eventos Operacionais** é um sistema completo de gestão de eventos que permite:

- **Cadastrar e gerenciar eventos** com informações financeiras detalhadas
- **Alocar equipes de cooperados** em eventos com controle de horários e custos
- **Gerenciar funções e setores** para organização da equipe
- **Gerar listas de assinatura** separadas por setor em PDF
- **Exportar credenciamentos** em Excel e impressão formatada
- **Calcular automaticamente** margem de lucro, custos e saldos de horas
- **Filtrar eventos** por data e status
- **Alocação individual ou em massa** de cooperados

---

## 🏗️ Estrutura do Módulo

### Componentes Principais

```
🎉 Eventos Operacionais
├── 📊 Tabela de Eventos
│   ├── Filtros (Data Início, Data Fim, Status)
│   ├── Lista de Eventos
│   └── Ações (Alocar Equipe, Editar, Deletar)
│
├── ➕ Modal de Evento
│   ├── Dados do Evento
│   ├── Informações Financeiras
│   └── Cálculo Automático de Margem
│
├── 👥 Modal de Alocação de Equipe
│   ├── Aba Individual
│   ├── Aba Em Massa
│   ├── Aba Assinatura
│   └── Aba Credenciamento
│
├── 👔 Gestão de Funções
│   └── Modal de Funções de Evento
│
└── 🏢 Gestão de Setores
    └── Modal de Setores
```

---

## ⚙️ Funcionalidades Principais

### 1. **Gestão de Eventos**
- Cadastro completo de eventos operacionais
- Associação com notas fiscais (NF)
- Controle financeiro (Valor Líquido, Custo, Margem)
- Status do evento (Pendente, Em Andamento, Concluído, Cancelado)
- Tipos de evento personalizáveis
- Campo de observações

### 2. **Alocação de Equipes**
- **Individual**: Adicionar cooperados um por vez
- **Em Massa**: Adicionar múltiplos cooperados simultaneamente
- Registro de horários (Início e Fim)
- Cálculo automático de saldo de horas
- Atribuição de função e setor
- Definição de valor por cooperado
- Busca/filtro de cooperados

### 3. **Controle de Horários**
- Campo de hora início e hora fim
- Cálculo automático do saldo (HH:MM)
- Suporte a virada de meia-noite
- Exibição em formato brasileiro (HH:MM)

### 4. **Sistema de Assinatura**
- Lista de presença formatada
- Separação automática por setor
- Exportação em PDF (um arquivo por setor)
- Exportação em Excel com valores
- Campo para assinatura física

### 5. **Sistema de Credenciamento**
- Visualização de todos os cooperados alocados
- Exibição de CPF e E-mail
- Exportação para Excel formatado
- Impressão em A4 profissional
- Contagem total de cooperados

---

## 📅 Gestão de Eventos

### Campos do Evento

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| **Nome do Evento** | Texto | ✅ Sim | Identificação do evento |
| **Data do Evento** | Data | ✅ Sim | Data de realização |
| **NF Associada** | Texto | ❌ Não | Número da nota fiscal |
| **Valor Líquido NF** | Moeda | ❌ Não | Valor da NF em R$ |
| **Custo do Evento** | Moeda | ❌ Não | Custo total do evento |
| **Margem** | Moeda | 🔒 Auto | Valor Líquido - Custo |
| **Tipo de Evento** | Texto | ❌ Não | Categoria do evento |
| **Status** | Seleção | ✅ Sim | Estado atual do evento |
| **Observações** | Texto longo | ❌ Não | Notas adicionais |

### Status Disponíveis

- **🟡 PENDENTE**: Evento planejado, não iniciado
- **🔵 EM_ANDAMENTO**: Evento em execução
- **🟢 CONCLUIDO**: Evento finalizado com sucesso
- **🔴 CANCELADO**: Evento cancelado

### Cálculo Automático de Margem

```javascript
Margem = Valor Líquido NF - Custo do Evento
```

O campo **Margem** é calculado automaticamente sempre que:
- Valor Líquido NF é alterado
- Custo do Evento é alterado
- Evento é carregado para edição

### Filtros de Eventos

#### Filtro por Data
- **Data Início**: Filtra eventos a partir desta data
- **Data Fim**: Filtra eventos até esta data
- Ambos podem ser usados simultaneamente

#### Filtro por Status
- Selecione um status específico ou "Todos"
- Aplicado automaticamente ao mudar seleção

#### Botão Limpar
- Remove todos os filtros aplicados
- Recarrega a lista completa de eventos

---

## 👥 Gestão de Equipes

### Aba Individual

Adiciona cooperados um por vez com controle completo.

#### Campos do Formulário

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| **Cooperado** | ✅ Sim | Seleção do funcionário |
| **Busca de Cooperado** | ❌ Não | Filtro de busca em tempo real |
| **Função** | ✅ Sim | Função a desempenhar no evento |
| **Setor** | ❌ Não | Setor de alocação |
| **Hora Início** | ❌ Não | Horário de início (HH:MM) |
| **Hora Fim** | ❌ Não | Horário de fim (HH:MM) |
| **Saldo Horas** | 🔒 Auto | Calculado automaticamente |
| **Valor (R$)** | ✅ Sim | Valor a pagar ao cooperado |

#### Recursos da Aba Individual

- **🔍 Busca em Tempo Real**: Digite para filtrar cooperados
- **Lista Expandida**: 20 linhas visíveis (max-height: 280px)
- **Botões Rápidos**: Adicionar nova função ou setor
- **Cálculo Automático**: Saldo de horas atualizado ao digitar
- **Botão Adicionar**: Alinhado com o campo de valor

#### Cálculo do Saldo de Horas

```javascript
// Converte horários para minutos
início_minutos = hora_início * 60 + minuto_início
fim_minutos = hora_fim * 60 + minuto_fim

// Calcula diferença
diferença = fim_minutos - início_minutos

// Se negativo, passou da meia-noite
if (diferença < 0) {
    diferença += 24 * 60  // Adiciona 24 horas
}

// Converte para HH:MM
horas = floor(diferença / 60)
minutos = diferença % 60

saldo = "HH:MM"
```

### Aba Em Massa

Adiciona múltiplos cooperados simultaneamente com as mesmas configurações.

#### Campos do Formulário

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| **Função** | ✅ Sim | Aplicada a todos |
| **Setor** | ❌ Não | Aplicado a todos |
| **Cooperados** | ✅ Sim | Seleção múltipla (Ctrl/Cmd + clique) |
| **Busca** | ❌ Não | Filtro de busca |
| **Hora Início** | ❌ Não | Aplicada a todos |
| **Hora Fim** | ❌ Não | Aplicada a todos |
| **Saldo Horas** | 🔒 Auto | Calculado automaticamente |
| **Aplicar Valor** | ❌ Não | Checkbox para habilitar valor único |
| **Valor (R$)** | ⚠️ Condicional | Obrigatório se checkbox marcado |

#### Comportamento do Valor

- **Checkbox DESMARCADO**: Todos cooperados com R$ 0,00 (editar depois)
- **Checkbox MARCADO**: Todos cooperados com o valor especificado

#### Recursos da Aba Em Massa

- **Seleção Múltipla**: Selecione vários cooperados de uma vez
- **Configuração Única**: Função, setor e horários iguais para todos
- **Valor Opcional**: Escolha entre valor único ou R$ 0,00
- **Confirmação**: Dialog antes de adicionar todos
- **Feedback**: Toast mostrando sucessos e erros

#### Processo de Adição em Massa

```
1. Usuário seleciona múltiplos cooperados
2. Define função, setor, horários e valor (opcional)
3. Clica em "Adicionar Todos"
4. Sistema confirma quantidade
5. Loop para cada cooperado:
   - Envia requisição POST individual
   - Registra sucesso ou erro
6. Exibe resultado final
7. Recarrega tabela de equipe
```

### Tabela de Equipe Alocada

Exibe todos os cooperados já alocados no evento.

#### Colunas da Tabela

| Coluna | Descrição |
|--------|-----------|
| **Funcionário** | Nome do cooperado |
| **Função** | Função no evento |
| **Setor** | Setor de alocação |
| **Saldo Horas** | Total de horas (HH:MM) |
| **Valor** | Valor em R$ |
| **Ações** | Botão remover (🗑️) |

#### Rodapé da Tabela

```
💰 Custo Total da Equipe: R$ X.XXX,XX
```

- Atualizado automaticamente ao adicionar/remover cooperados
- Soma todos os valores da equipe
- Também atualiza o "Custo Atual" no cabeçalho do modal

---

## 👔 Funções e Setores

### Gestão de Funções

#### O que são Funções?

Funções definem o papel que o cooperado desempenhará no evento.

**Exemplos:**
- Coordenador
- Monitor
- Instrutor
- Auxiliar
- Técnico
- Operador

#### Campos de Função

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| **Nome** | ✅ Sim | Nome da função |
| **Descrição** | ❌ Não | Detalhes sobre a função |

#### Modal de Funções

- **Acessível via**: Botão "👔 Funções" na tela principal
- **Acessível via**: Botão "➕" ao lado do select de função
- **Operações**: Criar, Editar, Deletar
- **Listagem**: Tabela com todas as funções cadastradas

### Gestão de Setores

#### O que são Setores?

Setores agrupam cooperados por área de atuação ou departamento.

**Exemplos:**
- Produção
- Logística
- Administrativo
- Técnico
- Operacional
- Segurança

#### Campos de Setor

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| **Nome** | ✅ Sim | Nome do setor |
| **Descrição** | ❌ Não | Detalhes sobre o setor |
| **Ativo** | ✅ Sim | Se o setor está ativo |

#### Modal de Setores

- **Acessível via**: Botão "🏢 Setores" na tela principal
- **Acessível via**: Botão "➕" ao lado do select de setor
- **Operações**: Criar, Editar, Ativar/Desativar, Deletar
- **Listagem**: Tabela com todos os setores
- **Filtro**: Apenas setores ativos aparecem nos selects

---

## ✍️ Sistema de Assinatura

### Visão Geral

Gera listas de presença formatadas com espaço para assinatura dos cooperados.

### Aba Assinatura

#### Cabeçalho da Lista

```
📋 Lista de Presença - Evento
Nome do Evento
Data: DD/MM/YYYY
Setor: [Nome do Setor]
```

#### Tabela de Assinatura

| # | Funcionário | Função | Setor | Assinatura |
|---|-------------|--------|-------|------------|
| 1 | Nome 1 | Função 1 | Setor 1 | [espaço] |
| 2 | Nome 2 | Função 2 | Setor 2 | [espaço] |
| ... | ... | ... | ... | ... |

#### Rodapé da Lista

```
Documento gerado em DD/MM/YYYY HH:MM:SS
X funcionário(s)
```

### Exportação em PDF

#### Características

- **Separação por Setor**: Um PDF para cada setor
- **Formato**: A4 com margens adequadas
- **Cabeçalho**: Nome do evento, data e setor
- **Tabela**: Grid com bordas e cores
- **Espaço para Assinatura**: Coluna vazia para assinatura física
- **Rodapé**: Data de geração e total de funcionários
- **Biblioteca**: jsPDF + autoTable

#### Processo de Exportação PDF

```javascript
1. Coleta dados da equipe alocada
2. Agrupa cooperados por setor
3. Para cada setor:
   a. Cria novo documento PDF
   b. Adiciona cabeçalho com nome do evento e setor
   c. Gera tabela com funcionários do setor
   d. Adiciona rodapé com data e contagem
   e. Salva arquivo: Lista_Assinatura_[Evento]_[Setor].pdf
4. Exibe toast: "X PDF(s) exportado(s)"
```

#### Nome dos Arquivos

```
Lista_Assinatura_[Nome_Evento]_[Nome_Setor].pdf
```

Exemplo: `Lista_Assinatura_Festival_2026_Producao.pdf`

### Exportação em Excel

#### Características

- **Arquivo Único**: Um arquivo com todos os cooperados
- **Colunas**: #, Funcionário, Função, Setor, Valor (R$)
- **Cabeçalho**: Nome do evento e data
- **Formatação**: Colunas com largura otimizada
- **Biblioteca**: SheetJS (XLSX)

#### Processo de Exportação Excel

```javascript
1. Coleta dados da equipe alocada
2. Cria array com:
   - Linha 1: Título "Lista de Equipe - Evento"
   - Linha 2: Nome do evento
   - Linha 3: Data do evento
   - Linha 4: Vazia
   - Linha 5: Cabeçalhos das colunas
   - Linhas 6+: Dados dos cooperados
3. Configura larguras das colunas
4. Gera arquivo XLSX
5. Salva: Lista_Equipe_[Evento].xlsx
```

#### Nome do Arquivo

```
Lista_Equipe_[Nome_Evento].xlsx
```

Exemplo: `Lista_Equipe_Festival_2026.xlsx`

---

## 🎫 Sistema de Credenciamento

### Visão Geral

Exibe e exporta informações completas de todos os cooperados alocados em **todos os eventos**.

### Aba Credenciamento

#### Características

- **Carregamento Automático**: Busca todos os eventos e suas equipes
- **Dados Completos**: CPF, E-mail, Função, Setor, Horários
- **Sem Agrupamento**: Lista única com todos os cooperados
- **Total Dinâmico**: Contagem automática de cooperados

#### Tabela de Credenciamento

| Coluna | Descrição |
|--------|-----------|
| **Cooperado** | Nome completo |
| **CPF** | Documento CPF |
| **E-mail** | E-mail do cooperado |
| **Função** | Função no evento |
| **Setor** | Setor de alocação |
| **Hora Início** | Horário de início (HH:MM) |
| **Hora Fim** | Horário de fim (HH:MM) |
| **Total Trabalhado** | Saldo de horas (HH:MM) |

#### Rodapé

```
👥 Total de Cooperados: X
```

#### Botões de Ação

- **📥 Exportar Excel**: Exporta para Excel formatado
- **🖨️ Imprimir**: Abre janela de impressão A4

### Exportação Excel de Credenciamento

#### Formato HTML Table

O sistema usa HTML formatado que o Excel interpreta nativamente como `.xls`.

#### Estrutura do Arquivo

```html
<html>
<head>
    <meta charset="UTF-8">
    <style>
        /* Estilos CSS para formatação */
        table { border-collapse: collapse; }
        th { background-color: #4472C4; color: white; }
        td { padding: 8px; border: 1px solid #D0D0D0; }
        tr:nth-child(even) { background-color: #F2F2F2; }
    </style>
</head>
<body>
    <div class="header">
        🎫 CREDENCIAMENTO - LISTA DE COOPERADOS
    </div>
    <div class="info">
        Emitido em: DD/MM/YYYY às HH:MM:SS
        Sistema Financeiro DWM
    </div>
    <table>
        <thead>...</thead>
        <tbody>...</tbody>
    </table>
    <div class="total">
        Total de Cooperados: X
    </div>
</body>
</html>
```

#### Características do Excel Exportado

- **Cabeçalho Azul**: Fundo #4472C4 com texto branco
- **Zebra Striping**: Linhas alternadas cinza/branco
- **Bordas**: Grid completo para todas as células
- **Metadados**: Título, data/hora de emissão, sistema
- **Rodapé**: Total de cooperados destacado
- **Formatação Preservada**: Cores e estilos mantidos no Excel

#### Nome do Arquivo

```
Credenciamento_YYYY-MM-DD.xls
```

Exemplo: `Credenciamento_2026-02-04.xls`

### Impressão de Credenciamento

#### Formato A4 Profissional

**Status: ✅ APROVADO PELO USUÁRIO - NÃO MODIFICAR**

> 🖨️ **Feedback do Usuário**: "Imprimir ficou exelente, não mude nada dele"

#### Características da Impressão

- **Formato**: A4 (210mm x 297mm)
- **Margens**: 15mm em todos os lados
- **Fonte**: Arial, sans-serif
- **Tamanho Base**: 10pt
- **Orientação**: Retrato (portrait)

#### Layout da Página

```
┌─────────────────────────────────────┐
│     🎫 Credenciamento               │
│     Lista de Cooperados             │
│                                     │
│     Data: DD/MM/YYYY                │
│     Sistema Financeiro DWM          │
├─────────────────────────────────────┤
│ Tabela com todos os cooperados      │
│ [8 colunas formatadas]              │
├─────────────────────────────────────┤
│ Total: X cooperados                 │
└─────────────────────────────────────┘
```

#### Processo de Impressão

```javascript
1. Gera HTML completo com estilos CSS inline
2. Define @page para formato A4 e margens
3. Adiciona título e metadados
4. Cria tabela formatada com todos os cooperados
5. Adiciona rodapé com total
6. Abre nova janela (window.open)
7. Escreve HTML na janela
8. Chama window.print() automaticamente
```

---

## 🔌 API Endpoints

### Eventos

#### `GET /api/eventos`

Lista todos os eventos com filtros opcionais.

**Query Parameters:**
- `data_inicio` (opcional): Data inicial (YYYY-MM-DD)
- `data_fim` (opcional): Data final (YYYY-MM-DD)
- `status` (opcional): Status do evento

**Response:**
```json
{
  "eventos": [
    {
      "id": 1,
      "nome_evento": "Festival 2026",
      "data_evento": "2026-06-15",
      "nf_associada": "NF-001",
      "valor_liquido_nf": 50000.00,
      "custo_evento": 35000.00,
      "margem": 15000.00,
      "tipo_evento": "Festival",
      "status": "PENDENTE",
      "observacoes": "Evento anual",
      "empresa_id": 1,
      "usuario_id": 1,
      "criado_em": "2026-01-15T10:00:00",
      "atualizado_em": "2026-01-15T10:00:00"
    }
  ]
}
```

#### `POST /api/eventos`

Cria um novo evento.

**Request Body:**
```json
{
  "nome_evento": "Festival 2026",
  "data_evento": "2026-06-15",
  "nf_associada": "NF-001",
  "valor_liquido_nf": 50000.00,
  "custo_evento": 35000.00,
  "margem": 15000.00,
  "tipo_evento": "Festival",
  "status": "PENDENTE",
  "observacoes": "Evento anual"
}
```

**Response:**
```json
{
  "message": "Evento criado com sucesso",
  "evento_id": 1
}
```

#### `PUT /api/eventos/<evento_id>`

Atualiza um evento existente.

**Request Body:** (Mesma estrutura do POST, campos opcionais)

**Response:**
```json
{
  "message": "Evento atualizado com sucesso"
}
```

#### `DELETE /api/eventos/<evento_id>`

Deleta um evento.

**Response:**
```json
{
  "message": "Evento deletado com sucesso"
}
```

### Funções de Evento

#### `GET /api/funcoes-evento`

Lista todas as funções de evento.

**Response:**
```json
{
  "funcoes": [
    {
      "id": 1,
      "nome": "Coordenador",
      "descricao": "Coordena as atividades",
      "empresa_id": 1,
      "usuario_id": 1
    }
  ]
}
```

#### `POST /api/funcoes-evento`

Cria uma nova função.

**Request Body:**
```json
{
  "nome": "Coordenador",
  "descricao": "Coordena as atividades"
}
```

#### `PUT /api/funcoes-evento/<funcao_id>`

Atualiza uma função.

#### `DELETE /api/funcoes-evento/<funcao_id>`

Deleta uma função.

### Equipe de Evento

#### `GET /api/eventos/<evento_id>/equipe`

Lista todos os cooperados alocados no evento.

**Response:**
```json
{
  "equipe": [
    {
      "id": 1,
      "evento_id": 1,
      "funcionario_id": 5,
      "funcionario_nome": "João Silva",
      "funcionario_cpf": "123.456.789-00",
      "funcionario_email": "joao@email.com",
      "funcao_id": 1,
      "funcao_nome": "Coordenador",
      "setor_id": 2,
      "setor_nome": "Produção",
      "hora_inicio": "08:00:00",
      "hora_fim": "17:00:00",
      "valor": 500.00
    }
  ]
}
```

#### `POST /api/eventos/<evento_id>/equipe`

Adiciona um cooperado à equipe do evento.

**Request Body:**
```json
{
  "funcionario_id": 5,
  "funcao_id": 1,
  "setor_id": 2,
  "hora_inicio": "08:00:00",
  "hora_fim": "17:00:00",
  "valor": 500.00
}
```

**Response:**
```json
{
  "message": "Funcionário adicionado à equipe com sucesso",
  "alocacao_id": 1
}
```

#### `DELETE /api/eventos/equipe/<alocacao_id>`

Remove um cooperado da equipe.

**Response:**
```json
{
  "message": "Funcionário removido da equipe com sucesso"
}
```

### Setores

#### `GET /api/setores`

Lista todos os setores.

**Response:**
```json
{
  "setores": [
    {
      "id": 1,
      "nome": "Produção",
      "descricao": "Setor de produção",
      "ativo": true,
      "empresa_id": 1,
      "usuario_id": 1
    }
  ]
}
```

---

## 🗄️ Estrutura do Banco de Dados

### Tabela: `eventos`

```sql
CREATE TABLE eventos (
    id SERIAL PRIMARY KEY,
    nome_evento VARCHAR(200) NOT NULL,
    data_evento DATE NOT NULL,
    nf_associada VARCHAR(50),
    valor_liquido_nf DECIMAL(15, 2),
    custo_evento DECIMAL(15, 2),
    margem DECIMAL(15, 2),
    tipo_evento VARCHAR(100),
    status VARCHAR(20) DEFAULT 'PENDENTE',
    observacoes TEXT,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id),
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_eventos_data ON eventos(data_evento);
CREATE INDEX idx_eventos_status ON eventos(status);
CREATE INDEX idx_eventos_empresa ON eventos(empresa_id);
```

### Tabela: `funcoes_evento`

```sql
CREATE TABLE funcoes_evento (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id),
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nome, empresa_id)
);
```

### Tabela: `evento_funcionarios`

Tabela de relacionamento entre eventos e cooperados (equipe).

```sql
CREATE TABLE evento_funcionarios (
    id SERIAL PRIMARY KEY,
    evento_id INTEGER NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    funcionario_id INTEGER NOT NULL REFERENCES funcionarios(id) ON DELETE CASCADE,
    funcao_id INTEGER NOT NULL REFERENCES funcoes_evento(id),
    setor_id INTEGER REFERENCES setores(id),
    hora_inicio TIME,
    hora_fim TIME,
    valor DECIMAL(15, 2) NOT NULL,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id),
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_evento_funcionarios_evento ON evento_funcionarios(evento_id);
CREATE INDEX idx_evento_funcionarios_funcionario ON evento_funcionarios(funcionario_id);
CREATE INDEX idx_evento_funcionarios_empresa ON evento_funcionarios(empresa_id);
```

### Tabela: `setores`

```sql
CREATE TABLE setores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id),
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nome, empresa_id)
);
```

---

## ⚙️ Funções JavaScript

### Gestão de Eventos

#### `abrirModalEvento(evento = null)`

Abre o modal de evento para criação ou edição.

**Parâmetros:**
- `evento` (objeto, opcional): Dados do evento para edição

**Comportamento:**
- Se `evento` for null: Modal de criação (limpa formulário)
- Se `evento` for objeto: Modal de edição (preenche campos)

#### `fecharModalEvento()`

Fecha o modal de evento e limpa o formulário.

#### `calcularMargemEvento()`

Calcula automaticamente a margem do evento.

**Fórmula:**
```javascript
margem = valor_liquido_nf - custo_evento
```

**Atualiza:** Campo `#evento-margem`

#### `async salvarEvento(event)`

Salva (cria ou atualiza) um evento.

**Fluxo:**
1. Previne submit padrão
2. Coleta dados do formulário
3. Valida campos obrigatórios
4. Determina método (POST para criar, PUT para editar)
5. Envia requisição à API
6. Exibe toast de sucesso/erro
7. Fecha modal
8. Recarrega lista de eventos

#### `async loadEventos()`

Carrega e exibe a lista de eventos com filtros.

**Fluxo:**
1. Coleta valores dos filtros
2. Monta query string com parâmetros
3. Faz requisição GET à API
4. Renderiza tabela com eventos
5. Aplica badges de status
6. Adiciona botões de ação

#### `async deletarEvento(id)`

Deleta um evento após confirmação.

**Parâmetros:**
- `id` (number): ID do evento

**Fluxo:**
1. Exibe confirmação
2. Envia DELETE à API
3. Exibe toast de sucesso/erro
4. Recarrega lista

#### `limparFiltrosEvento()`

Limpa todos os filtros e recarrega eventos.

### Gestão de Equipes

#### `async abrirModalEquipeEvento(eventoId, nomeEvento, dataEvento, custoAtual)`

Abre o modal de alocação de equipe.

**Parâmetros:**
- `eventoId` (number): ID do evento
- `nomeEvento` (string): Nome do evento
- `dataEvento` (string): Data do evento
- `custoAtual` (number): Custo atual do evento

**Fluxo:**
1. Atualiza cabeçalho do modal
2. Carrega funcionários disponíveis
3. Carrega funções disponíveis
4. Carrega setores disponíveis
5. Carrega equipe já alocada
6. Exibe modal

#### `fecharModalEquipeEvento()`

Fecha o modal de equipe e limpa formulários.

#### `async carregarFuncionariosDisponiveis()`

Carrega lista de cooperados ativos nos selects.

**Atualiza:**
- `#equipe-select-funcionario` (individual)
- `#equipe-select-funcionarios-massa` (em massa)

#### `async carregarFuncoesDisponiveis()`

Carrega lista de funções nos selects.

**Atualiza:**
- `#equipe-select-funcao` (individual)
- `#equipe-select-funcao-massa` (em massa)

#### `async carregarSetoresDisponiveis()`

Carrega lista de setores ativos nos selects.

**Atualiza:**
- `#equipe-select-setor` (individual)
- `#equipe-select-setor-massa` (em massa)

#### `async carregarEquipeEvento(eventoId)`

Carrega e renderiza a equipe alocada no evento.

**Parâmetros:**
- `eventoId` (number): ID do evento

**Fluxo:**
1. Busca equipe da API
2. Para cada membro:
   - Calcula saldo de horas
   - Renderiza linha na tabela
3. Calcula e exibe custo total
4. Atualiza "Custo Atual" no cabeçalho

#### `async adicionarFuncionarioEvento(event)`

Adiciona um cooperado à equipe (individual).

**Fluxo:**
1. Previne submit
2. Valida campos obrigatórios
3. Monta objeto de dados
4. Envia POST à API
5. Exibe toast
6. Limpa formulário
7. Recarrega equipe
8. Recarrega lista de eventos

#### `async removerFuncionarioEvento(alocacaoId)`

Remove um cooperado da equipe.

**Parâmetros:**
- `alocacaoId` (number): ID da alocação

**Fluxo:**
1. Confirma remoção
2. Envia DELETE à API
3. Exibe toast
4. Recarrega equipe
5. Recarrega lista de eventos

#### `async adicionarFuncionariosMassa(event)`

Adiciona múltiplos cooperados em massa.

**Fluxo:**
1. Previne submit
2. Valida campos obrigatórios
3. Coleta funcionários selecionados
4. Confirma quantidade
5. Loop para cada funcionário:
   - Envia POST individual
   - Registra sucesso/erro
6. Exibe resultado consolidado
7. Limpa formulário
8. Recarrega equipe e eventos

### Cálculo de Horas

#### `calcularSaldoHoras()`

Calcula saldo de horas para alocação individual.

**Campos:**
- Input: `#equipe-hora-inicio`, `#equipe-hora-fim`
- Output: `#equipe-saldo-horas`

**Lógica:**
```javascript
1. Converte horários para minutos totais
2. Calcula diferença
3. Se diferença < 0, adiciona 24h (passou meia-noite)
4. Converte de volta para HH:MM
5. Atualiza campo de saldo
```

#### `calcularSaldoHorasMassa()`

Calcula saldo de horas para alocação em massa.

**Campos:**
- Input: `#equipe-hora-inicio-massa`, `#equipe-hora-fim-massa`
- Output: `#equipe-saldo-horas-massa`

**Lógica:** Idêntica a `calcularSaldoHoras()`

### Sistema de Abas

#### `trocarAbaEquipe(aba)`

Troca entre abas do modal de equipe.

**Parâmetros:**
- `aba` (string): 'individual', 'massa', 'assinatura' ou 'credenciamento'

**Comportamento:**
1. Reseta estilos de todas as abas
2. Esconde todos os formulários
3. Ativa aba selecionada:
   - Individual (azul): Mostra formulário individual
   - Massa (roxo): Mostra formulário em massa
   - Assinatura (laranja): Carrega e exibe lista de assinatura
   - Credenciamento (verde): Carrega credenciamentos

### Sistema de Assinatura

#### `carregarListaAssinatura()`

Gera preview da lista de assinatura.

**Fluxo:**
1. Atualiza cabeçalho com dados do evento
2. Clona dados da tabela de equipe
3. Adiciona numeração sequencial
4. Adiciona coluna vazia para assinatura
5. Renderiza na tabela de preview

#### `exportarAssinaturaPDF()`

Exporta lista de assinatura em PDF separado por setor.

**Biblioteca:** jsPDF + autoTable

**Fluxo:**
1. Valida se há dados
2. Agrupa cooperados por setor
3. Para cada setor:
   - Cria novo PDF
   - Adiciona cabeçalho
   - Gera tabela formatada
   - Adiciona rodapé
   - Salva arquivo
4. Exibe toast com quantidade de PDFs

#### `exportarAssinaturaExcel()`

Exporta lista de equipe em Excel.

**Biblioteca:** SheetJS (XLSX)

**Fluxo:**
1. Valida se há dados
2. Monta array de dados:
   - Cabeçalhos
   - Dados dos cooperados
3. Cria workbook
4. Configura larguras de colunas
5. Salva arquivo XLSX

### Sistema de Credenciamento

#### `async carregarCredenciamento()`

Carrega credenciamentos de todos os eventos.

**Fluxo:**
1. Busca todos os eventos da API
2. Detecta formato do array (suporte múltiplo)
3. Para cada evento:
   - Busca equipe do evento
   - Extrai dados completos (CPF, email)
   - Calcula total trabalhado
   - Renderiza linhas
4. Atualiza contador total

#### `exportarCredenciamento()`

Exporta credenciamento em Excel HTML formatado.

**Formato:** HTML Table interpretado como .xls

**Fluxo:**
1. Valida dados
2. Gera HTML completo com:
   - Meta charset UTF-8
   - CSS inline para formatação
   - Cabeçalho profissional
   - Metadados (data/hora)
   - Tabela formatada
   - Rodapé com total
3. Cria Blob com tipo 'application/vnd.ms-excel'
4. Baixa arquivo .xls

**Características:**
- Cabeçalho azul (#4472C4)
- Zebra striping (linhas alternadas)
- Bordas em grid
- Total destacado

#### `imprimirCredenciamento()`

Abre janela de impressão A4.

**⚠️ IMPORTANTE:** Aprovado pelo usuário - NÃO MODIFICAR

**Fluxo:**
1. Coleta dados da tabela
2. Gera HTML com estilos para impressão
3. Define @page para A4 e margens
4. Abre nova janela
5. Escreve HTML
6. Chama window.print()

### Utilitários

#### `toggleValorMassa()`

Habilita/desabilita campo de valor em massa.

**Comportamento:**
- Checkbox marcado: Campo habilitado e obrigatório
- Checkbox desmarcado: Campo desabilitado e opcional

#### `filtrarFuncionarios(tipo)`

Filtra cooperados em tempo real na busca.

**Parâmetros:**
- `tipo` (string): 'individual' ou 'massa'

**Comportamento:**
1. Captura termo de busca
2. Itera por todas as opções do select
3. Mostra/esconde baseado em match
4. Exibe mensagem se nenhum resultado

---

## 🔄 Fluxo de Trabalho

### 1. Criar Novo Evento

```
1. Usuário clica em "➕ Novo Evento"
   ↓
2. Modal de Evento abre
   ↓
3. Usuário preenche:
   - Nome do Evento *
   - Data do Evento *
   - NF Associada
   - Valor Líquido NF
   - Custo do Evento
   - Tipo de Evento
   - Status *
   - Observações
   ↓
4. Margem calculada automaticamente
   ↓
5. Usuário clica em "💾 Salvar"
   ↓
6. Sistema valida campos obrigatórios
   ↓
7. POST /api/eventos
   ↓
8. Toast de sucesso
   ↓
9. Modal fecha
   ↓
10. Tabela de eventos recarrega
```

### 2. Alocar Equipe Individual

```
1. Usuário clica no botão "👥" do evento
   ↓
2. Modal de Equipe abre
   ↓
3. Sistema carrega:
   - Funcionários ativos
   - Funções cadastradas
   - Setores ativos
   - Equipe já alocada
   ↓
4. Aba Individual (padrão)
   ↓
5. Usuário preenche:
   - Busca cooperado (opcional)
   - Seleciona cooperado *
   - Seleciona função *
   - Seleciona setor
   - Hora início
   - Hora fim
   - Valor *
   ↓
6. Saldo de horas calculado automaticamente
   ↓
7. Usuário clica em "➕ Adicionar"
   ↓
8. POST /api/eventos/{id}/equipe
   ↓
9. Toast de sucesso
   ↓
10. Formulário limpa
   ↓
11. Tabela de equipe recarrega
   ↓
12. Custo Total atualiza
   ↓
13. Custo Atual atualiza
```

### 3. Alocar Equipe em Massa

```
1. Usuário está no Modal de Equipe
   ↓
2. Clica na aba "👥 Em Massa"
   ↓
3. Usuário preenche:
   - Função (aplicada a todos) *
   - Setor (aplicado a todos)
   - Seleciona múltiplos cooperados * (Ctrl + clique)
   - Hora início (todos)
   - Hora fim (todos)
   - [Opcional] Marca checkbox "Aplicar valor"
   - [Se marcado] Valor (todos)
   ↓
4. Saldo de horas calculado automaticamente
   ↓
5. Usuário clica em "👥 Adicionar Todos"
   ↓
6. Dialog de confirmação
   ↓
7. Loop para cada cooperado:
   - POST /api/eventos/{id}/equipe
   - Registra sucesso/erro
   ↓
8. Toast com resultado (X sucessos, Y erros)
   ↓
9. Formulário limpa
   ↓
10. Tabela de equipe recarrega
   ↓
11. Custo Total atualiza
```

### 4. Gerar Lista de Assinatura

```
1. Usuário está no Modal de Equipe
   ↓
2. Clica na aba "✍️ Assinatura"
   ↓
3. Sistema carrega preview:
   - Cabeçalho com nome e data do evento
   - Tabela com cooperados numerados
   - Coluna vazia para assinatura
   ↓
4. Usuário visualiza preview
   ↓
5. Opção A: Exportar PDF
   ├─→ Clica "📄 Exportar PDF"
   ├─→ Sistema agrupa por setor
   ├─→ Gera 1 PDF por setor
   └─→ Download automático
   
   Opção B: Exportar Excel
   ├─→ Clica "📊 Exportar Excel"
   ├─→ Sistema gera XLSX
   ├─→ Inclui valores
   └─→ Download automático
```

### 5. Exportar Credenciamento

```
1. Usuário está no Modal de Equipe
   ↓
2. Clica na aba "🎫 Credenciamento"
   ↓
3. Sistema carrega:
   - Busca TODOS os eventos
   - Para cada evento, busca equipe
   - Monta tabela única
   ↓
4. Usuário visualiza tabela completa
   ↓
5. Opção A: Exportar Excel
   ├─→ Clica "📥 Exportar Excel"
   ├─→ Sistema gera HTML formatado
   ├─→ Salva como .xls
   └─→ Download automático
   
   Opção B: Imprimir
   ├─→ Clica "🖨️ Imprimir"
   ├─→ Sistema gera HTML A4
   ├─→ Abre nova janela
   └─→ Dialog de impressão
```

### 6. Editar Evento

```
1. Usuário clica no botão "✏️" do evento
   ↓
2. Modal de Evento abre com dados preenchidos
   ↓
3. Usuário modifica campos desejados
   ↓
4. Margem recalculada se necessário
   ↓
5. Usuário clica em "💾 Salvar"
   ↓
6. PUT /api/eventos/{id}
   ↓
7. Toast de sucesso
   ↓
8. Modal fecha
   ↓
9. Tabela de eventos recarrega
```

### 7. Deletar Evento

```
1. Usuário clica no botão "🗑️" do evento
   ↓
2. Dialog de confirmação
   ↓
3. Se confirmar:
   ├─→ DELETE /api/eventos/{id}
   ├─→ Deleta evento
   ├─→ Deleta equipe (CASCADE)
   ├─→ Toast de sucesso
   └─→ Tabela recarrega
   
4. Se cancelar:
   └─→ Nada acontece
```

### 8. Filtrar Eventos

```
1. Usuário define filtros:
   - Data Início
   - Data Fim
   - Status
   ↓
2. Mudança em qualquer filtro:
   ├─→ Dispara onchange
   └─→ loadEventos() é chamado
   ↓
3. Sistema monta query string
   ↓
4. GET /api/eventos?filtros
   ↓
5. Tabela atualiza com resultados
   ↓
6. Ou clica em "🔄 Limpar":
   ├─→ Limpa todos os filtros
   └─→ Recarrega sem filtros
```

---

## 📊 Cálculos Automáticos

### Margem do Evento

```javascript
Margem = Valor Líquido NF - Custo do Evento
```

**Quando é calculado:**
- Ao digitar Valor Líquido NF
- Ao digitar Custo do Evento
- Ao abrir evento para edição

### Saldo de Horas

```javascript
// Converter para minutos
inicio_minutos = (hora * 60) + minutos
fim_minutos = (hora * 60) + minutos

// Calcular diferença
diferenca = fim_minutos - inicio_minutos

// Ajuste para virada de meia-noite
if (diferenca < 0) {
    diferenca += (24 * 60)  // +24 horas
}

// Converter para HH:MM
horas = floor(diferenca / 60)
minutos = diferenca % 60

saldo = format(horas, "00") + ":" + format(minutos, "00")
```

**Exemplo:**
```
Início: 22:00
Fim: 02:00
Cálculo: 02:00 - 22:00 = -20:00 → -20:00 + 24:00 = 04:00
Resultado: 04:00
```

### Custo Total da Equipe

```javascript
Custo Total = Σ (valor de cada cooperado)
```

**Quando é calculado:**
- Ao adicionar cooperado
- Ao remover cooperado
- Ao carregar equipe do evento

**Atualiza:**
- Rodapé da tabela de equipe: "💰 Custo Total da Equipe"
- Cabeçalho do modal: "💰 Custo Atual"
- Campo "Custo do Evento" na lista principal (via reload)

---

## 🎨 Cores e Badges

### Status de Evento

| Status | Cor | Badge |
|--------|-----|-------|
| PENDENTE | Amarelo (#f39c12) | `<span class="badge badge-warning">Pendente</span>` |
| EM_ANDAMENTO | Azul (#3498db) | `<span class="badge badge-info">Em Andamento</span>` |
| CONCLUIDO | Verde (#27ae60) | `<span class="badge badge-success">Concluído</span>` |
| CANCELADO | Vermelho (#e74c3c) | `<span class="badge badge-danger">Cancelado</span>` |

### Cores das Abas

| Aba | Cor | Hex |
|-----|-----|-----|
| Individual | Azul | #3498db |
| Em Massa | Roxo | #9b59b6 |
| Assinatura | Laranja | #e67e22 |
| Credenciamento | Verde Água | #16a085 |

### Cores de Destaque

| Elemento | Cor | Uso |
|----------|-----|-----|
| Sucesso | Verde (#27ae60) | Valores, confirmações |
| Informação | Azul (#3498db) | Saldo de horas, títulos |
| Aviso | Amarelo (#f39c12) | Avisos, pendências |
| Erro | Vermelho (#e74c3c) | Erros, exclusões |
| Neutro | Cinza (#95a5a6) | Botões secundários |

---

## 🔐 Segurança e Validações

### Validações no Frontend

1. **Campos Obrigatórios**
   - Nome do Evento
   - Data do Evento
   - Status
   - Cooperado (alocação)
   - Função (alocação)
   - Valor (alocação)

2. **Validações de Tipo**
   - Datas: Formato válido
   - Valores: Números positivos
   - Horários: Formato HH:MM

3. **Validações de Negócio**
   - Valor mínimo: R$ 0,00
   - Seleção múltipla: Pelo menos 1 cooperado
   - Confirmações: Antes de deletar

### Validações no Backend

1. **Autenticação**
   - Token JWT em todas as requisições
   - `credentials: 'include'` nos fetchs

2. **Autorização**
   - Empresa ID vinculado automaticamente
   - Usuário ID registrado em todas as operações
   - Filtro automático por empresa

3. **Integridade de Dados**
   - Foreign keys com CASCADE
   - Unique constraints em nomes+empresa
   - NOT NULL em campos críticos

4. **Validações de Negócio**
   - Verificação de existência
   - Validação de relacionamentos
   - Checks de valores

---

## 📱 Responsividade

### Breakpoints

- **Desktop**: > 1200px
- **Tablet**: 768px - 1200px
- **Mobile**: < 768px

### Comportamento por Dispositivo

#### Desktop (> 1200px)
- Modal: 1200px de largura
- Grid: 3 colunas no formulário
- Tabelas: Todas as colunas visíveis
- Abas: Horizontais

#### Tablet (768px - 1200px)
- Modal: 90% da largura
- Grid: 2 colunas no formulário
- Tabelas: Scroll horizontal
- Abas: Horizontais compactadas

#### Mobile (< 768px)
- Modal: 95% da largura
- Grid: 1 coluna no formulário
- Tabelas: Scroll horizontal
- Abas: Verticais (stack)

---

## 🚀 Performance

### Otimizações Implementadas

1. **Lazy Loading**
   - Equipe carregada apenas ao abrir modal
   - Funções/setores carregados sob demanda

2. **Debounce na Busca**
   - Filtro de cooperados otimizado
   - Evita múltiplas renderizações

3. **Batch Operations**
   - Alocação em massa
   - Um request por cooperado (necessário para validação)

4. **Cache de Selects**
   - Cooperados, funções e setores carregados uma vez
   - Reutilizados entre abas

5. **Índices no Banco**
   - `idx_eventos_data`
   - `idx_eventos_status`
   - `idx_eventos_empresa`
   - `idx_evento_funcionarios_evento`

### Tempos Médios

| Operação | Tempo Médio |
|----------|-------------|
| Carregar eventos | < 200ms |
| Abrir modal equipe | < 500ms |
| Adicionar cooperado | < 300ms |
| Exportar PDF | < 1s |
| Exportar Excel | < 500ms |

---

## 🐛 Tratamento de Erros

### Erros Comuns e Soluções

#### "Nenhum funcionário encontrado"
**Causa:** Filtro muito específico ou sem cooperados ativos  
**Solução:** Limpar busca ou verificar cooperados ativos

#### "Erro ao adicionar cooperado"
**Causa:** Cooperado já alocado no evento  
**Solução:** Verificar lista de equipe, não permite duplicatas

#### "Erro ao carregar eventos"
**Causa:** Problema de conexão ou sessão expirada  
**Solução:** Recarregar página, fazer login novamente

#### "Nenhum dado para exportar"
**Causa:** Tentar exportar sem cooperados alocados  
**Solução:** Alocar equipe antes de exportar

### Mensagens de Toast

#### Sucesso (Verde)
- ✅ Evento cadastrado com sucesso!
- ✅ Evento atualizado com sucesso!
- ✅ Cooperado adicionado à equipe!
- ✅ X cooperado(s) adicionado(s) com sucesso!
- ✅ Excel exportado com sucesso!
- ✅ X PDF(s) exportado(s) com sucesso!

#### Aviso (Amarelo)
- ⚠️ Preencha todos os campos obrigatórios
- ⚠️ Selecione pelo menos um cooperado
- ⚠️ Nenhum funcionário para exportar
- ⚠️ Valor inválido

#### Erro (Vermelho)
- ❌ Erro ao salvar evento
- ❌ Erro ao adicionar cooperado
- ❌ Erro ao carregar dados
- ❌ Erro de conexão

#### Info (Azul)
- ⏳ Adicionando X cooperado(s)...
- 💾 Salvando dados...

---

## 📚 Dependências Externas

### Bibliotecas JavaScript

1. **jsPDF** (v2.5.1)
   - Geração de PDFs
   - Usado em: `exportarAssinaturaPDF()`
   - CDN: https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js

2. **jsPDF-AutoTable** (v3.5.31)
   - Tabelas em PDF
   - Usado em: `exportarAssinaturaPDF()`
   - CDN: https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.31/jspdf.plugin.autotable.min.js

3. **SheetJS (XLSX)** (v0.18.5)
   - Geração de Excel
   - Usado em: `exportarAssinaturaExcel()`
   - CDN: https://cdn.sheetjs.com/xlsx-0.18.5/package/dist/xlsx.full.min.js

### Dependências CSS

- Bootstrap (badges, classes utilitárias)
- CSS customizado (variáveis do sistema)

---

## 🔮 Melhorias Futuras

### Sugestões de Funcionalidades

1. **Dashboard de Eventos**
   - Gráfico de eventos por mês
   - Ranking de cooperados mais alocados
   - Análise de margem média

2. **Notificações**
   - Lembrete de eventos próximos
   - Alerta de eventos sem equipe
   - Notificação de custo excedido

3. **Relatórios Avançados**
   - Relatório de produtividade por cooperado
   - Análise de custos por setor
   - Comparativo de eventos

4. **Integrações**
   - Exportar para Google Calendar
   - Enviar assinaturas por e-mail
   - Integração com folha de pagamento

5. **Mobilidade**
   - App mobile para check-in
   - QR Code para credenciamento
   - Assinatura digital

---

## 📞 Suporte

### Contatos

- **Desenvolvedor**: Eduardo Souza
- **GitHub**: https://github.com/EduardoSouza-tech/Sistema_financeiro_dwm
- **Sistema**: Sistema Financeiro DWM

### Documentações Relacionadas

- [DOCUMENTACAO_CLIENTES.md](DOCUMENTACAO_CLIENTES.md)
- [DOCUMENTACAO_EXTRATO.md](DOCUMENTACAO_EXTRATO.md)
- [DOCS_FOLHA_PAGAMENTO.md](DOCS_FOLHA_PAGAMENTO.md)
- [DOCS_KITS_EQUIPAMENTOS_COMPLETO.md](DOCS_KITS_EQUIPAMENTOS_COMPLETO.md)

---

## 📝 Histórico de Versões

| Versão | Data | Alterações |
|--------|------|------------|
| 1.0.0 | 2026-01-15 | Versão inicial do módulo |
| 1.1.0 | 2026-01-20 | Adição de horários e saldo de horas |
| 1.2.0 | 2026-01-22 | Sistema de assinatura com PDF por setor |
| 1.3.0 | 2026-01-25 | Sistema de credenciamento |
| 1.4.0 | 2026-02-04 | Melhoria na exportação Excel de credenciamento |

---

**Documentação gerada em**: 04 de Fevereiro de 2026  
**Sistema**: Sistema Financeiro DWM v2.0  
**Módulo**: 🎉 Eventos Operacionais
