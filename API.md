# 📚 Documentação da API

**Última atualização:** 20/01/2026  
**Versão:** 2.0  
**Base URL:** `https://[SEU-APP].railway.app`

---

## 🔐 Autenticação

### **Login**

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "usuario",
  "password": "senha123"
}
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "message": "Login realizado com sucesso",
  "usuario": {
    "id": 1,
    "username": "usuario",
    "nivel_acesso": "admin",
    "empresa_id": 1
  }
}
```

**Após login:** Sistema cria sessão com cookie `session_token`.

### **Logout**

```http
POST /api/auth/logout
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "message": "Logout realizado com sucesso"
}
```

### **Headers Necessários**

Todas as requisições autenticadas precisam de:

```http
Cookie: session=<session_token>
X-CSRF-Token: <csrf_token>
Content-Type: application/json
```

---

## 📦 Kits API

### **Listar Kits**

```http
GET /api/kits
```

**Query Parameters:**
- `empresa_id` (opcional): Filtrar por empresa

**Resposta (200 OK):**
```json
{
  "success": true,
  "kits": [
    {
      "id": 1,
      "nome": "Kit Básico",
      "descricao": "Kit de serviços básicos",
      "preco": 1500.00,
      "ativo": true,
      "empresa_id": 1,
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

### **Criar Kit**

```http
POST /api/kits
Content-Type: application/json

{
  "nome": "Kit Premium",
  "descricao": "Serviços completos",
  "preco": 2500.00,
  "ativo": true
}
```

**Resposta (201 Created):**
```json
{
  "success": true,
  "message": "Kit criado com sucesso",
  "id": 2
}
```

### **Obter Kit Específico**

```http
GET /api/kits/1
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "kit": {
    "id": 1,
    "nome": "Kit Básico",
    "descricao": "Kit de serviços básicos",
    "preco": 1500.00,
    "ativo": true,
    "empresa_id": 1
  }
}
```

### **Atualizar Kit**

```http
PUT /api/kits/1
Content-Type: application/json

{
  "nome": "Kit Básico Atualizado",
  "preco": 1800.00
}
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "message": "Kit atualizado com sucesso"
}
```

### **Deletar Kit**

```http
DELETE /api/kits/1
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "message": "Kit deletado com sucesso"
}
```

---

## 📋 Contratos API

### **Listar Contratos**

```http
GET /api/contratos?cliente_id=5
```

**Query Parameters:**
- `cliente_id` (opcional): Filtrar por cliente
- `status` (opcional): `ativo` | `inativo`

**Resposta (200 OK):**
```json
{
  "success": true,
  "contratos": [
    {
      "id": 1,
      "numero": "CONT-001",
      "cliente_id": 5,
      "cliente_nome": "João Silva",
      "valor": 5000.00,
      "data_inicio": "2026-01-01",
      "data_fim": "2026-12-31",
      "status": "ativo",
      "empresa_id": 1
    }
  ]
}
```

### **Obter Próximo Número**

```http
GET /api/contratos/proximo-numero
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "numero": "CONT-015"
}
```

### **Criar Contrato**

```http
POST /api/contratos
Content-Type: application/json

{
  "numero": "CONT-015",
  "cliente_id": 5,
  "valor": 5000.00,
  "data_inicio": "2026-02-01",
  "data_fim": "2027-01-31",
  "descricao": "Contrato de manutenção anual"
}
```

**Resposta (201 Created):**
```json
{
  "success": true,
  "message": "Contrato criado com sucesso",
  "id": 15
}
```

### **Atualizar Contrato**

```http
PUT /api/contratos/15
Content-Type: application/json

{
  "valor": 5500.00,
  "status": "ativo"
}
```

### **Deletar Contrato**

```http
DELETE /api/contratos/15
```

---

## 🗓️ Sessões API

### **Listar Sessões**

```http
GET /api/sessoes?contrato_id=15
```

**Query Parameters:**
- `contrato_id` (opcional): Filtrar por contrato
- `cliente_id` (opcional): Filtrar por cliente
- `data_inicio` (opcional): Data início (YYYY-MM-DD)
- `data_fim` (opcional): Data fim (YYYY-MM-DD)

**Resposta (200 OK):**
```json
{
  "success": true,
  "sessoes": [
    {
      "id": 1,
      "titulo": "Manutenção Preventiva",
      "data_sessao": "2026-01-20",
      "duracao_minutos": 240,
      "contrato_id": 15,
      "cliente_id": 5,
      "valor": 800.00,
      "observacoes": "Concluído sem problemas"
    }
  ]
}
```

### **Criar Sessão**

⚠️ **Importante:** Frontend envia `data` e `quantidade_horas`, backend converte para `data_sessao` e `duracao_minutos`.

```http
POST /api/sessoes
Content-Type: application/json

{
  "titulo": "Instalação de Equipamento",
  "data": "2026-01-21",
  "quantidade_horas": 4,
  "contrato_id": 15,
  "cliente_id": 5,
  "valor": 600.00
}
```

**Backend converte:**
- `data` → `data_sessao`
- `quantidade_horas` (4) → `duracao_minutos` (240)

**Resposta (201 Created):**
```json
{
  "success": true,
  "message": "Sessão criada com sucesso",
  "id": 2
}
```

---

## 📊 Relatórios API

### **Dashboard Executivo**

```http
GET /api/relatorios/dashboard
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "saldo_total": 50000.00,
  "contas_receber": 15000.00,
  "contas_pagar": 8000.00,
  "receitas_mes": 25000.00,
  "despesas_mes": 12000.00,
  "saldo_mes": 13000.00,
  "lancamentos_pendentes": 12,
  "ultimos_lancamentos": [...]
}
```

### **Dashboard Completo (com Período)**

```http
GET /api/relatorios/dashboard-completo?data_inicio=2026-01-01&data_fim=2026-01-31
```

**Query Parameters (obrigatórios):**
- `data_inicio`: YYYY-MM-DD
- `data_fim`: YYYY-MM-DD

### **Fluxo de Caixa**

```http
GET /api/relatorios/fluxo-caixa?data_inicio=2026-01-01&data_fim=2026-01-31
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "periodo": {
    "inicio": "2026-01-01",
    "fim": "2026-01-31"
  },
  "saldo_inicial": 40000.00,
  "total_receitas": 25000.00,
  "total_despesas": 12000.00,
  "saldo_final": 53000.00,
  "detalhamento": [
    {
      "data": "2026-01-05",
      "descricao": "Pagamento Cliente X",
      "tipo": "receita",
      "valor": 5000.00,
      "saldo_acumulado": 45000.00
    }
  ]
}
```

### **Fluxo Projetado**

```http
GET /api/relatorios/fluxo-projetado?dias=30
```

**Query Parameters:**
- `dias` (opcional): Número de dias futuros (padrão: 30)

**Resposta (200 OK):**
```json
{
  "success": true,
  "projecao_dias": 30,
  "saldo_atual": 50000.00,
  "receitas_previstas": 18000.00,
  "despesas_previstas": 9000.00,
  "saldo_projetado": 59000.00,
  "detalhes": [...]
}
```

### **Análise por Contas**

```http
GET /api/relatorios/analise-contas
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "contas": [
    {
      "conta_id": 1,
      "conta_nome": "Banco Itaú - Conta Corrente",
      "saldo": 35000.00,
      "total_receitas": 120000.00,
      "total_despesas": 85000.00,
      "quantidade_lancamentos": 245
    }
  ]
}
```

### **Resumo de Parceiros**

```http
GET /api/relatorios/resumo-parceiros?tipo=clientes
```

**Query Parameters:**
- `tipo`: `clientes` | `fornecedores` | `todos`

### **Análise por Categorias**

```http
GET /api/relatorios/analise-categorias?data_inicio=2026-01-01&data_fim=2026-01-31
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "categorias": [
    {
      "categoria_id": 5,
      "categoria_nome": "Serviços",
      "tipo": "receita",
      "total": 45000.00,
      "percentual": 62.5,
      "quantidade": 18
    }
  ]
}
```

### **Comparativo de Períodos**

```http
GET /api/relatorios/comparativo-periodos?periodo1_inicio=2025-12-01&periodo1_fim=2025-12-31&periodo2_inicio=2026-01-01&periodo2_fim=2026-01-31
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "periodo1": {
    "inicio": "2025-12-01",
    "fim": "2025-12-31",
    "receitas": 40000.00,
    "despesas": 18000.00
  },
  "periodo2": {
    "inicio": "2026-01-01",
    "fim": "2026-01-31",
    "receitas": 50000.00,
    "despesas": 20000.00
  },
  "variacao": {
    "receitas_percentual": 25.0,
    "despesas_percentual": 11.1
  }
}
```

### **Indicadores Financeiros**

```http
GET /api/relatorios/indicadores
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "ticket_medio": 2500.00,
  "taxa_conversao": 68.5,
  "margem_liquida": 45.2,
  "roi": 32.1,
  "crescimento_receita": 18.5
}
```

### **Inadimplência**

```http
GET /api/relatorios/inadimplencia
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "total_inadimplente": 12000.00,
  "quantidade_titulos": 8,
  "maior_atraso_dias": 45,
  "detalhamento": [
    {
      "lancamento_id": 123,
      "descricao": "Fatura #001",
      "valor": 3000.00,
      "data_vencimento": "2025-12-15",
      "dias_atraso": 36,
      "cliente_nome": "Empresa ABC"
    }
  ]
}
```

---

## 💰 Lançamentos API

### **Listar Lançamentos**

```http
GET /api/lancamentos?tipo=receita&status=pendente&data_inicio=2026-01-01
```

**Query Parameters:**
- `tipo`: `receita` | `despesa`
- `status`: `pago` | `pendente` | `cancelado`
- `data_inicio`: YYYY-MM-DD
- `data_fim`: YYYY-MM-DD
- `categoria_id`: ID da categoria
- `conta_id`: ID da conta

### **Criar Lançamento**

```http
POST /api/lancamentos
Content-Type: application/json

{
  "descricao": "Pagamento Serviço",
  "valor": 1500.00,
  "data_lancamento": "2026-01-20",
  "data_vencimento": "2026-02-05",
  "tipo": "despesa",
  "status": "pendente",
  "categoria_id": 8,
  "conta_id": 1,
  "observacoes": "Primeira parcela"
}
```

**Resposta (201 Created):**
```json
{
  "success": true,
  "message": "Lançamento criado com sucesso",
  "id": 456
}
```

### **Pagar Lançamento**

```http
POST /api/lancamentos/456/pagar
Content-Type: application/json

{
  "data_pagamento": "2026-01-20",
  "valor_pago": 1500.00
}
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "message": "Lançamento pago com sucesso"
}
```

### **Cancelar Lançamento**

```http
POST /api/lancamentos/456/cancelar
```

---

## 👥 Clientes & Fornecedores API

### **Listar Clientes**

```http
GET /api/clientes
```

### **Criar Cliente**

```http
POST /api/clientes
Content-Type: application/json

{
  "nome": "Empresa ABC Ltda",
  "documento": "12.345.678/0001-90",
  "email": "contato@empresaabc.com",
  "telefone": "(11) 98765-4321",
  "tipo_chave_pix": "cnpj",
  "chave_pix": "12345678000190",
  "endereco": {
    "logradouro": "Rua Exemplo, 123",
    "bairro": "Centro",
    "cidade": "São Paulo",
    "uf": "SP",
    "cep": "01234-567"
  }
}
```

**Resposta (201 Created):**
```json
{
  "success": true,
  "message": "Cliente criado com sucesso",
  "id": 25
}
```

### **Atualizar Cliente**

```http
PUT /api/clientes/25
Content-Type: application/json

{
  "telefone": "(11) 91234-5678",
  "email": "novo@empresaabc.com"
}
```

### **Listar Fornecedores**

```http
GET /api/fornecedores
```

API similar à de clientes.

---

## 🏦 Contas Bancárias API

### **Listar Contas**

```http
GET /api/contas
```

**Resposta (200 OK):**
```json
{
  "success": true,
  "contas": [
    {
      "id": 1,
      "nome": "Banco Itaú - Conta Corrente",
      "banco": "Itaú",
      "agencia": "1234",
      "conta": "56789-0",
      "saldo": 35000.00,
      "ativa": true,
      "tipo": "conta_corrente"
    }
  ]
}
```

### **Criar Conta**

```http
POST /api/contas
Content-Type: application/json

{
  "nome": "Banco Santander - Poupança",
  "banco": "Santander",
  "agencia": "5678",
  "conta": "12345-6",
  "saldo": 10000.00,
  "tipo": "poupanca"
}
```

---

## 📂 Categorias API

### **Listar Categorias**

```http
GET /api/categorias?tipo=receita
```

**Query Parameters:**
- `tipo`: `receita` | `despesa`

**Resposta (200 OK):**
```json
{
  "success": true,
  "categorias": [
    {
      "id": 5,
      "nome": "Serviços",
      "tipo": "receita",
      "icone": "briefcase",
      "cor": "#4CAF50",
      "empresa_id": 1,
      "subcategorias": [
        {
          "id": 12,
          "nome": "Consultoria",
          "categoria_id": 5
        }
      ]
    }
  ]
}
```

### **Criar Categoria**

```http
POST /api/categorias
Content-Type: application/json

{
  "nome": "Marketing",
  "tipo": "despesa",
  "icone": "megaphone",
  "cor": "#FF5722"
}
```

---

## ⚠️ Erros

### **Códigos de Status**

- `200 OK`: Sucesso
- `201 Created`: Recurso criado
- `400 Bad Request`: Dados inválidos
- `401 Unauthorized`: Não autenticado
- `403 Forbidden`: Sem permissão
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro do servidor

### **Formato de Erro**

```json
{
  "success": false,
  "error": "Descrição do erro",
  "code": "ERROR_CODE",
  "details": {
    "field": "campo_invalido",
    "message": "Mensagem detalhada"
  }
}
```

### **Exemplos de Erros**

**401 - Não Autenticado:**
```json
{
  "success": false,
  "error": "Usuário não autenticado",
  "code": "AUTH_REQUIRED"
}
```

**403 - Sem Permissão:**
```json
{
  "success": false,
  "error": "Sem permissão para esta ação",
  "code": "FORBIDDEN"
}
```

**400 - Validação:**
```json
{
  "success": false,
  "error": "Dados inválidos",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "email",
    "message": "Email inválido"
  }
}
```

---

## 🔍 Paginação

Endpoints de listagem suportam paginação:

```http
GET /api/lancamentos?page=2&per_page=50
```

**Query Parameters:**
- `page`: Número da página (começa em 1)
- `per_page`: Items por página (padrão: 50, máximo: 100)

**Resposta com Paginação:**
```json
{
  "success": true,
  "items": [...],
  "pagination": {
    "page": 2,
    "per_page": 50,
    "total_items": 250,
    "total_pages": 5,
    "has_next": true,
    "has_prev": true,
    "next_page": 3,
    "prev_page": 1
  }
}
```

---

## 📝 Notas

### **Datas**
- Formato aceito: `YYYY-MM-DD` (ISO 8601)
- Frontend pode enviar `DD/MM/YYYY`, backend converte automaticamente

### **Valores Monetários**
- Enviar como número: `1500.00`
- Backend formata para moeda brasileira: `R$ 1.500,00`

### **Multi-tenancy**
- Todos os endpoints filtram automaticamente por `empresa_id` do usuário logado
- Não é necessário enviar `empresa_id` nas requisições

### **Cache**
- Dashboard: 5 minutos
- Relatórios: 10 minutos
- Para dados em tempo real, aguardar expiração do cache

---

**Criado por:** Time de Desenvolvimento DWM  
**Última atualização:** 20/01/2026  
**Versão:** 2.0
