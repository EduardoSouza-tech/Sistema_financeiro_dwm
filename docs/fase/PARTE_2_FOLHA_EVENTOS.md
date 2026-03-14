# Parte 2/3 - Interface HTML para Folha de Pagamento e Eventos

## ✅ Implementações Concluídas

### 1. Seção Folha de Pagamento (folha-pagamento-section)

**Localização**: Após extrato-bancario-section em interface_nova.html

**Componentes Criados**:
- ✅ Modal de cadastro/edição de funcionários
- ✅ Formulário com campos:
  - Nome Completo* (obrigatório)
  - CPF* (obrigatório, com máscara 000.000.000-00)
  - Endereço (opcional)
  - Tipo de Chave PIX* (obrigatório: CPF/CNPJ/EMAIL/TELEFONE/ALEATORIA)
  - Chave PIX
  - Data de Admissão
  - Observações
- ✅ Tabela de listagem com colunas:
  - Nome
  - CPF (formatado)
  - Endereço
  - Tipo Chave PIX
  - Chave PIX
  - Status (Ativo/Inativo)
  - Ações (Editar, Ativar/Inativar)

**Funções JavaScript**:
```javascript
- abrirModalFuncionario(funcionario)  // Abre modal para novo ou editar
- fecharModalFuncionario()            // Fecha modal e limpa form
- salvarFuncionario(event)            // POST/PUT para API
- loadFuncionarios()                  // GET lista de funcionários
- toggleAtivoFuncionario(id, ativo)   // Ativar/Inativar
- formatarCPF(cpf)                    // Formata XXX.XXX.XXX-XX
```

**Máscara de CPF**:
- Aplicada automaticamente ao digitar
- Formato: 000.000.000-00

---

### 2. Seção Eventos (eventos-section)

**Localização**: Após folha-pagamento-section em interface_nova.html

**Componentes Criados**:
- ✅ Modal de cadastro/edição de eventos
- ✅ Filtros de busca:
  - Data Início
  - Data Fim
  - Status (PENDENTE/EM_ANDAMENTO/CONCLUIDO/CANCELADO)
- ✅ Formulário com campos:
  - Nome do Evento* (obrigatório)
  - Data do Evento* (obrigatório)
  - NF Associada
  - Valor Líquido NF (R$)
  - Custo do Evento (R$)
  - Margem (calculada automaticamente: Valor Líquido - Custo)
  - Tipo de Evento
  - Status (select)
  - Observações
- ✅ Tabela de listagem com colunas:
  - Nome Evento
  - Data (formatada dd/mm/aaaa)
  - NF Associada
  - Valor Líquido NF (R$)
  - Custo do Evento (R$)
  - Margem (R$)
  - Tipo de Evento
  - Status (com badges coloridos)
  - Ações (Editar, Deletar)

**Funções JavaScript**:
```javascript
- abrirModalEvento(evento)      // Abre modal para novo ou editar
- fecharModalEvento()           // Fecha modal e limpa form
- calcularMargemEvento()        // Calcula margem automaticamente
- salvarEvento(event)           // POST/PUT para API
- loadEventos()                 // GET lista com filtros
- deletarEvento(id)             // DELETE evento
- limparFiltrosEvento()         // Limpa filtros e recarrega
- formatarData(data)            // dd/mm/aaaa
- formatarMoeda(valor)          // R$ X.XXX,XX
```

**Cálculo Automático de Margem**:
- Margem = Valor Líquido NF - Custo do Evento
- Campo somente leitura
- Atualizado em tempo real ao alterar valores

---

### 3. Estilos CSS Adicionados

**Badges de Status**:
```css
.badge                // Badge base
.badge-success        // Verde (Ativo, Concluído)
.badge-danger         // Vermelho (Inativo, Cancelado)
.badge-warning        // Amarelo (Pendente)
.badge-info           // Azul (Em Andamento)
```

**Botões Pequenos**:
```css
.btn-sm               // Botões de ação nas tabelas
- Hover com escala 1.05
- Margin 2px entre botões
```

---

### 4. Integração com showSection()

**Atualizado em interface_nova.html (linha ~4130)**:
```javascript
} else if (sectionId === 'folha-pagamento') {
    if (typeof loadFuncionarios === 'function') loadFuncionarios();
} else if (sectionId === 'eventos') {
    if (typeof loadEventos === 'function') loadEventos();
}
```

---

## 📋 Campos e Validações

### Funcionários
| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| Nome | text | ✅ Sim | - |
| CPF | text | ✅ Sim | Máscara 000.000.000-00 |
| Endereço | textarea | ❌ Não | - |
| Tipo Chave PIX | select | ✅ Sim | CPF/CNPJ/EMAIL/TELEFONE/ALEATORIA |
| Chave PIX | text | ❌ Não | - |
| Data Admissão | date | ❌ Não | - |
| Observações | textarea | ❌ Não | - |

### Eventos
| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| Nome Evento | text | ✅ Sim | - |
| Data Evento | date | ✅ Sim | - |
| NF Associada | text | ❌ Não | - |
| Valor Líquido NF | number | ❌ Não | Step 0.01 |
| Custo do Evento | number | ❌ Não | Step 0.01 |
| Margem | number | ❌ Não | Calculado (read-only) |
| Tipo de Evento | text | ❌ Não | - |
| Status | select | ❌ Não | Default: PENDENTE |
| Observações | textarea | ❌ Não | - |

---

## 🎨 UI/UX Features

### Funcionários
- ➕ Botão "Novo Funcionário" no canto superior direito
- ✏️ Editar: Abre modal preenchido
- 🚫 Inativar: Muda status para Inativo
- ✅ Ativar: Reativa funcionário inativo
- 💾 Salvar: Toast de sucesso/erro
- ❌ Cancelar: Fecha modal sem salvar

### Eventos
- ➕ Botão "Novo Evento" no canto superior direito
- 🔍 Filtros: Data início, Data fim, Status
- 🔄 Limpar: Remove todos os filtros
- ✏️ Editar: Abre modal preenchido
- 🗑️ Deletar: Confirmação antes de excluir
- 💾 Salvar: Toast de sucesso/erro
- ❌ Cancelar: Fecha modal sem salvar
- 📊 Badges coloridos por status
- 💰 Valores monetários formatados

---

## 🔗 Endpoints Necessários (Parte 3)

### Funcionários
```
GET    /api/funcionarios          # Listar todos
POST   /api/funcionarios          # Criar novo
PUT    /api/funcionarios/<id>     # Atualizar
DELETE /api/funcionarios/<id>     # Deletar (não usado, usa ativo=False)
```

### Eventos
```
GET    /api/eventos               # Listar com filtros (?data_inicio&data_fim&status)
POST   /api/eventos               # Criar novo
PUT    /api/eventos/<id>          # Atualizar
DELETE /api/eventos/<id>          # Deletar
```

---

## 📦 Estrutura de Dados

### Request Body - POST/PUT Funcionário
```json
{
  "nome": "João Silva",
  "cpf": "12345678900",
  "endereco": "Rua XYZ, 123",
  "tipo_chave_pix": "CPF",
  "chave_pix": "123.456.789-00",
  "data_admissao": "2024-01-15",
  "observacoes": "Observações...",
  "ativo": true
}
```

### Request Body - POST/PUT Evento
```json
{
  "nome_evento": "Festa Corporativa",
  "data_evento": "2024-12-25",
  "nf_associada": "NF-12345",
  "valor_liquido_nf": 15000.00,
  "custo_evento": 10000.00,
  "margem": 5000.00,
  "tipo_evento": "Corporativo",
  "status": "PENDENTE",
  "observacoes": "Observações..."
}
```

---

## ✅ Checklist Parte 2

- [x] Criar seção HTML folha-pagamento-section
- [x] Criar modal de funcionário
- [x] Criar formulário com todos os campos
- [x] Criar tabela de listagem
- [x] Implementar máscara de CPF
- [x] Criar funções JS de CRUD
- [x] Criar seção HTML eventos-section
- [x] Criar modal de evento
- [x] Criar filtros de busca
- [x] Criar formulário com cálculo de margem
- [x] Criar tabela de listagem com badges
- [x] Implementar funções JS de CRUD
- [x] Adicionar estilos CSS
- [x] Integrar com showSection()
- [x] Testar estrutura HTML

---

## 🚀 Próximos Passos - Parte 3

1. Criar endpoints no web_server.py:
   - /api/funcionarios (GET, POST, PUT)
   - /api/eventos (GET, POST, PUT, DELETE)
2. Implementar validações no backend
3. Testar integração completa
4. Deploy no Railway

---

## 📝 Observações Técnicas

- **Modais**: Usam display: none/block para abrir/fechar
- **Toasts**: Função showToast() já existente no sistema
- **Formatação**: CPF, data e moeda formatados no frontend
- **Validação**: HTML5 required + validação backend (Parte 3)
- **Status**: Badges coloridos por tipo
- **Ações**: Confirmação antes de deletar/inativar
- **Responsivo**: Tabelas com scroll horizontal se necessário

---

**Criado em**: 2024-01-XX  
**Autor**: GitHub Copilot  
**Status**: ✅ Parte 2 COMPLETA - Aguardando Parte 3 (API)
