# PLANO DE MELHORIAS - CONTRATOS E SESSÕES
**Data**: 2026-02-08  
**Solicitação**: Reforma completa do módulo de contratos e sessões

---

## 🔴 PRIORIDADE CRÍTICA - BUGS (EM ANDAMENTO)

### ✅ FASE 1: Correção de Bugs de Listagem
- [x] **Bug**: Funcionários limitados a 1 item
- [x] **Bug**: Equipe só puxa 1 membro
- [x] **Bug**: Comissões limitadas a 1

**Status**: Investigando código...

---

## 🟡 PRIORIDADE ALTA - TIPOS DE CONTRATO

### ✅ FASE 2: Novos Tipos de Contrato
- [ ] Alterar tipos para: **Mensal**, **Único**, **Pacote**
- [ ] Remover tipo atual "Por Hora"

### ✅ FASE 3: Formulários Dinâmicos por Tipo

#### 📋 Tipo: MENSAL (Mantém atual)
```
*Cliente:
*Tipo: Mensal
*Nome do Contrato:
Descrição:
*Valor Mensal:
*Qtd. Meses:
Valor Total: (calculado)
Horas Mensais:
*Forma Pagamento:
*Qtd. Parcelas:
*Data Contrato:
Dia Pagamento:
Dia Emissão NF:
Imposto (%):
Comissões:
```

#### 📋 Tipo: ÚNICO (Igual Mensal)
- Mesmos campos
- Lógica idêntica

#### 📋 Tipo: PACOTE (Cálculo diferente)
```
*Cliente:
*Tipo: Pacote
*Nome do Contrato:
Descrição:
*Valor por Hora:
*Qtd. Pacotes: (ex: 5 pacotes)
*Horas por Pacote: (ex: 8 horas)
Valor Total: (valor_hora × qtd_pacotes × horas_pacote)
*Forma Pagamento:
*Qtd. Parcelas:
*Data Contrato:
Dia Pagamento:
Dia Emissão NF:
Imposto (%):
Comissões:
```

**Fórmula Pacote**: `Valor Total = Valor por Hora × Qtd Pacotes × Horas por Pacote`

---

## 🔵 PRIORIDADE MÉDIA - FUNCIONALIDADES AVANÇADAS

### FASE 4: Controle de Horas em Sessões
- [ ] **Saldo de Horas**: Deduzir do contrato ao finalizar sessão
- [ ] **Horas Negativas**: Criar campo "Horas Extras"
- [ ] **Lógica**:
  - Contrato tem 80 horas
  - Sessão 1: 10 horas → Saldo: 70h
  - Sessão 2: 15 horas → Saldo: 55h
  - ...
  - Se saldo < 0 → Zerado + Horas Extras começam

### FASE 5: Status de Sessão
- [ ] Adicionar controles de status:
  - [x] **Rascunho** (atual)
  - [ ] **Agendada**
  - [ ] **Em Andamento**
  - [ ] **Finalizada**
  - [ ] **Cancelada**
  - [ ] **Reaberta**
- [ ] Botões de ação:
  - [ ] Iniciar Sessão
  - [ ] Finalizar Sessão
  - [ ] Reabrir Sessão
  - [ ] Cancelar Sessão

### FASE 6: Responsáveis - Cadastro de Funções
- [ ] Criar CRUD de Funções (Fotógrafo, Videomaker, etc)
- [ ] Botão **+ Adicionar Função** ao lado do select
- [ ] Modal rápido para criar função nova

### FASE 7: Aba de Custos (Operacional)
- [ ] Criar nova aba "Custos" em Operacional
- [ ] CRUD de Custos:
  - Nome
  - Descrição
  - Valor Padrão (opcional)
  - Categoria
- [ ] Integrar com "Custos Adicionais" em Sessões (select em vez de digitar)

### FASE 8: Cadastro de Tags
- [ ] Criar aba "Tags" em Operacional
- [ ] CRUD de Tags:
  - Nome
  - Cor
  - Ícone (opcional)
- [ ] Substituir campo texto em Sessões por **select múltiplo** de tags

### FASE 9: Endereço Automático
- [ ] Ao selecionar Cliente em Sessão:
  - Puxar endereço do cliente
  - Pré-preencher campo "Endereço"
  - Permitir edição manual

### FASE 10: Comissões - Mostrar Valor
- [ ] Ao lado de "%", mostrar valor calculado:
  ```
  Funcionário: João Silva
  Comissão: 10% → R$ 500,00 (de R$ 5.000)
  ```

---

## 🟢 PRIORIDADE BAIXA - RELATÓRIOS E INTEGRAÇÕES

### FASE 11: Relatório de Sessões
- [ ] Nova aba "Relatórios" ao lado de Sessões
- [ ] **Filtros**:
  - Nome da Pessoa
  - Data Inicial
  - Data Final
- [ ] **Métricas**:
  - Quem recebeu mais (total)
  - Horas trabalhadas por pessoa
  - Comissões pagas
  - Campo "NF" (Nota Fiscal) editável
- [ ] **Tabelas**:
  1. Comissões por Pessoa
  2. Equipe por Pessoa (nome + valor)

### FASE 12: Integração Contas a Receber
- [ ] Ao clicar "Finalizar Sessão":
  - Perguntar: "Gerar lançamento em Contas a Receber?"
  - Criar lançamento automático:
    - Tipo: Receita
    - Valor: Valor da sessão
    - Cliente: Cliente da sessão
    - Contrato: Contrato vinculado
    - Data: Data da sessão
    - Status: Pendente

---

## 📊 ESTIMATIVA DE TEMPO

| Fase | Descrição | Tempo Estimado | Prioridade |
|------|-----------|----------------|-----------|
| 1 | Bugs de listagem | 30 min | 🔴 AGORA |
| 2 | Tipos de contrato | 15 min | 🟡 HOJE |
| 3 | Formulários dinâmicos | 2 horas | 🟡 HOJE |
| 4 | Controle de horas | 3 horas | 🔵 AMANHÃ |
| 5 | Status de sessão | 2 horas | 🔵 AMANHÃ |
| 6 | Funções de responsáveis | 1 hora | 🔵 PRÓXIMA |
| 7 | Aba de custos | 2 horas | 🔵 PRÓXIMA |
| 8 | Cadastro de tags | 1 hora | 🔵 PRÓXIMA |
| 9 | Endereço automático | 30 min | 🔵 PRÓXIMA |
| 10 | Comissões com valor | 1 hora | 🔵 PRÓXIMA |
| 11 | Relatórios | 4 horas | 🟢 FUTURO |
| 12 | Integração contas | 2 horas | 🟢 FUTURO |

**TOTAL**: ~19 horas de desenvolvimento

---

## 🚀 PLANO DE EXECUÇÃO

### HOJE (2026-02-08)
1. ✅ Corrigir bugs de listagem (30 min)
2. ✅ Implementar tipos de contrato (15 min)
3. ✅ Formulários dinâmicos básicos (2h)

### AMANHÃ (2026-02-09)
4. Controle de horas (3h)
5. Status de sessão (2h)

### SEMANA SEGUINTE
6-10. Funcionalidades complementares (6h)

### FUTURO (A definir)
11-12. Relatórios e integrações (6h)

---

## 📝 NOTAS TÉCNICAS

### Impactos no Banco de Dados
- [ ] Adicionar coluna `tipo` em contratos (ENUM: mensal, unico, pacote)
- [ ] Adicionar coluna `horas_restantes` em contratos
- [ ] Adicionar coluna `horas_extras` em contratos
- [ ] Adicionar coluna `status` em sessoes (ENUM)
- [ ] Criar tabela `funcoes_responsaveis`
- [ ] Criar tabela `custos`
- [ ] Criar tabela `tags`
- [ ] Adicionar coluna `nota_fiscal` em sessoes

### Alterações no Frontend
- [ ] Modal de contrato: formulário dinâmico com `v-if` ou display/hide
- [ ] Sessões: adicionar botões de ação de status
- [ ] Criar novos modals para Tags, Custos, Funções
- [ ] Adicionar aba Relatórios em Contratos

---

## ⚠️ AVISOS

1. **Backup**: Fazer backup antes de implementar controle de horas
2. **Testes**: Testar exaustivamente cálculos de pacotes
3. **Migração**: Contratos existentes precisam ter tipo definido (padrão: mensal)
4. **Performance**: Relatórios podem ser pesados com muitos dados

---

**Status**: 🔴 EM ANDAMENTO - Fase 1  
**Última atualização**: 2026-02-08 00:00
