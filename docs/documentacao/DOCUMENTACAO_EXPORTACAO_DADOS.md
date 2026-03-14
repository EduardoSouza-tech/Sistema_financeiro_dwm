# 📦 Documentação - Exportação de Dados por Cliente

**Data:** 11 de Janeiro de 2026  
**Funcionalidade:** Exportação completa de dados de um cliente específico  
**Acesso:** Apenas Administrador

---

## 🎯 OBJETIVO

Permitir que o administrador exporte todos os dados de um cliente específico em formato JSON, útil para:
- **Backup de dados** de um cliente específico
- **Migração de dados** para outro sistema
- **Auditoria** e análise de dados
- **Conformidade** com LGPD (direito à portabilidade)

---

## 🔐 SEGURANÇA

### Proteções Implementadas

1. **Apenas Administrador:** Rota protegida com `@require_admin`
2. **Isolamento Completo:** Exporta APENAS dados com `proprietario_id` = cliente selecionado
3. **Auditoria:** Registra log de acesso com IP e timestamp
4. **Validação:** Verifica se cliente existe antes de exportar
5. **Sem Senhas:** Não exporta dados sensíveis (senhas, tokens, etc.)

---

## 🏗️ ARQUITETURA

### 1. Backend - Função de Exportação

**Arquivo:** `database_postgresql.py`  
**Função:** `exportar_dados_cliente(cliente_id: int) -> dict`

```python
def exportar_dados_cliente(cliente_id: int) -> dict:
    """
    Exporta todos os dados de um cliente específico
    
    Args:
        cliente_id: ID do cliente proprietário dos dados
        
    Returns:
        dict: Dicionário com todos os dados em JSON
    """
```

**Dados Exportados:**
- ✅ Clientes (registrados pelo proprietário)
- ✅ Fornecedores
- ✅ Categorias
- ✅ Contas Bancárias
- ✅ Lançamentos Financeiros

**Metadados Incluídos:**
- Data de exportação
- ID do cliente
- Versão do sistema
- Estatísticas (totais de cada tipo de dado)

---

### 2. Backend - Rotas API

**Arquivo:** `web_server.py`

#### Rota 1: Listar Proprietários

```python
GET /api/admin/listar-proprietarios
```

**Acesso:** Apenas admin  
**Resposta:**
```json
{
  "success": true,
  "proprietarios": [
    {
      "proprietario_id": 10,
      "nome": "João Silva",
      "email": "joao@example.com",
      "tipo": "cliente"
    }
  ],
  "total": 1
}
```

#### Rota 2: Exportar Dados do Cliente

```python
GET /api/admin/exportar-cliente/<cliente_id>
```

**Acesso:** Apenas admin  
**Parâmetros:** `cliente_id` (int) - ID do proprietário  
**Resposta:** Arquivo JSON para download

**Exemplo de resposta:**
```json
{
  "metadata": {
    "cliente_id": 10,
    "data_exportacao": "2026-01-11T10:30:00",
    "versao_sistema": "1.0",
    "estatisticas": {
      "total_clientes": 5,
      "total_fornecedores": 3,
      "total_categorias": 8,
      "total_contas": 2,
      "total_lancamentos": 150
    }
  },
  "clientes": [...],
  "fornecedores": [...],
  "categorias": [...],
  "contas_bancarias": [...],
  "lancamentos": [...]
}
```

---

### 3. Frontend - Interface Admin

**Arquivo:** `templates/admin.html`

#### Nova Aba: "📦 Exportar Dados"

**Elementos da Interface:**
1. **Seletor de Cliente:** Dropdown com lista de proprietários
2. **Informações do Cliente:** Mostra nome, email, tipo
3. **Botão de Exportação:** Inicia download do arquivo JSON
4. **Status de Exportação:** Feedback visual do processo

---

## 📋 COMO USAR

### Passo a Passo (Admin)

1. **Acessar Painel Admin**
   - URL: `http://localhost:5000/admin`
   - Fazer login como administrador

2. **Acessar Aba "Exportar Dados"**
   - Clicar na aba "📦 Exportar Dados"
   - Sistema carrega lista de proprietários automaticamente

3. **Selecionar Cliente**
   - No dropdown, selecionar o cliente desejado
   - Visualizar informações do cliente selecionado

4. **Exportar Dados**
   - Clicar no botão "📦 Exportar Dados do Cliente"
   - Aguardar processamento
   - Arquivo JSON será baixado automaticamente

5. **Verificar Arquivo**
   - Nome do arquivo: `export_cliente_<ID>_<DATA>.json`
   - Exemplo: `export_cliente_10_2026-01-11.json`
   - Abrir no editor de texto ou JSON viewer

---

## 📊 FORMATO DO ARQUIVO EXPORTADO

### Estrutura JSON

```json
{
  "metadata": {
    "cliente_id": 10,
    "data_exportacao": "2026-01-11T10:30:00",
    "versao_sistema": "1.0",
    "estatisticas": {
      "total_clientes": 5,
      "total_fornecedores": 3,
      "total_categorias": 8,
      "total_contas": 2,
      "total_lancamentos": 150
    }
  },
  "clientes": [
    {
      "id": 1,
      "nome": "Cliente A",
      "cpf_cnpj": "12345678900",
      "tipo_pessoa": "fisica",
      "email": "clientea@example.com",
      "telefone": "(11) 98765-4321",
      "endereco": "Rua A, 123",
      "cidade": "São Paulo",
      "estado": "SP",
      "cep": "01234-567",
      "observacoes": "",
      "ativo": true,
      "data_cadastro": "2026-01-01T10:00:00",
      "data_atualizacao": "2026-01-05T15:30:00"
    }
  ],
  "fornecedores": [
    {
      "id": 1,
      "nome": "Fornecedor X",
      "cpf_cnpj": "12345678000190",
      "tipo_pessoa": "juridica",
      "email": "fornecedor@example.com",
      "telefone": "(11) 3456-7890",
      "ativo": true
    }
  ],
  "categorias": [
    {
      "id": 1,
      "nome": "Alimentação",
      "tipo": "despesa",
      "descricao": "Gastos com alimentação",
      "cor": "#FF5733",
      "icone": "restaurant",
      "subcategorias": ["Mercado", "Restaurante"]
    }
  ],
  "contas_bancarias": [
    {
      "id": 1,
      "nome": "Conta Corrente",
      "banco": "Banco do Brasil",
      "agencia": "1234",
      "conta": "12345-6",
      "saldo_inicial": 1000.0,
      "tipo_conta": "corrente",
      "moeda": "BRL",
      "ativa": true,
      "data_criacao": "2026-01-01T00:00:00"
    }
  ],
  "lancamentos": [
    {
      "id": 1,
      "tipo": "despesa",
      "descricao": "Compra de material",
      "valor": 150.50,
      "data_lancamento": "2026-01-10",
      "data_vencimento": "2026-01-15",
      "data_pagamento": null,
      "status": "pendente",
      "categoria_id": 1,
      "subcategoria": "Material de Escritório",
      "conta_id": 1,
      "cliente_id": null,
      "fornecedor_id": 1,
      "forma_pagamento": "boleto",
      "parcela_numero": 1,
      "parcela_total": 1,
      "observacoes": "",
      "anexos": [],
      "tags": ["escritorio"],
      "recorrente": false,
      "recorrencia_tipo": null,
      "recorrencia_fim": null,
      "criado_em": "2026-01-10T09:00:00",
      "atualizado_em": "2026-01-10T09:00:00"
    }
  ]
}
```

---

## 🔍 QUERIES SQL EXECUTADAS

### 1. Clientes
```sql
SELECT id, nome, cpf_cnpj, tipo_pessoa, email, telefone, endereco, 
       cidade, estado, cep, observacoes, ativo, data_cadastro, 
       data_atualizacao, proprietario_id
FROM clientes 
WHERE proprietario_id = %s
ORDER BY nome
```

### 2. Fornecedores
```sql
SELECT id, nome, cpf_cnpj, tipo_pessoa, email, telefone, endereco,
       cidade, estado, cep, observacoes, ativo, data_cadastro,
       data_atualizacao, proprietario_id
FROM fornecedores
WHERE proprietario_id = %s
ORDER BY nome
```

### 3. Categorias
```sql
SELECT id, nome, tipo, descricao, cor, icone, subcategorias, proprietario_id
FROM categorias
WHERE proprietario_id = %s
ORDER BY nome
```

### 4. Contas Bancárias
```sql
SELECT id, nome, banco, agencia, conta, saldo_inicial, tipo_conta,
       moeda, ativa, data_criacao, proprietario_id
FROM contas_bancarias
WHERE proprietario_id = %s
ORDER BY nome
```

### 5. Lançamentos
```sql
SELECT id, tipo, descricao, valor, data_lancamento, data_vencimento,
       data_pagamento, status, categoria_id, subcategoria, conta_id,
       cliente_id, fornecedor_id, forma_pagamento, parcela_numero,
       parcela_total, observacoes, anexos, tags, recorrente,
       recorrencia_tipo, recorrencia_fim, criado_em, atualizado_em,
       proprietario_id
FROM lancamentos
WHERE proprietario_id = %s
ORDER BY data_lancamento DESC
```

---

## 📝 LOGS DE AUDITORIA

### Exportação Bem-Sucedida

```
🔄 Iniciando exportação dos dados do cliente 10
✅ Exportados 5 clientes
✅ Exportados 3 fornecedores
✅ Exportadas 8 categorias
✅ Exportadas 2 contas bancárias
✅ Exportados 150 lançamentos

📦 Exportação concluída:
   - 5 clientes
   - 3 fornecedores
   - 8 categorias
   - 2 contas bancárias
   - 150 lançamentos
✅ Exportação concluída para cliente 10
```

### Log no Banco de Dados

```sql
INSERT INTO log_acessos (usuario_id, acao, descricao, ip_address, sucesso)
VALUES (
  1,  -- Admin ID
  'exportar_dados_cliente',
  'Exportou dados do cliente_id 10',
  '192.168.1.100',
  true
)
```

---

## ⚠️ CONSIDERAÇÕES IMPORTANTES

### 1. Desempenho
- **Clientes com muitos dados:** Exportação pode demorar alguns segundos
- **Tamanho do arquivo:** Varia conforme quantidade de lançamentos
- **Timeout:** Aumentar se necessário (padrão: 30s)

### 2. Segurança
- ✅ Apenas admin pode exportar
- ✅ Logs registrados para auditoria
- ✅ Sem dados sensíveis (senhas, tokens)
- ✅ Filtro garante isolamento por `proprietario_id`

### 3. LGPD - Conformidade
- ✅ **Direito à Portabilidade:** Cliente pode solicitar seus dados
- ✅ **Formato Estruturado:** JSON é legível e portável
- ✅ **Dados Completos:** Todas as informações do cliente incluídas
- ✅ **Auditoria:** Logs registram quando dados foram exportados

### 4. Limitações
- ❌ Não exporta dados de outros usuários (tabela `usuarios`)
- ❌ Não exporta logs de sistema globais
- ❌ Não exporta permissões (são do sistema)
- ❌ Não exporta anexos/arquivos (apenas metadados)

---

## 🛠️ TESTES

### Teste 1: Exportar Cliente Existente

**Entrada:** cliente_id = 10  
**Esperado:** Arquivo JSON com todos os dados  
**Resultado:** ✅ Sucesso

### Teste 2: Exportar Cliente Inexistente

**Entrada:** cliente_id = 999  
**Esperado:** Erro 404 "Nenhum dado encontrado"  
**Resultado:** ✅ Erro tratado corretamente

### Teste 3: Acesso Sem Ser Admin

**Entrada:** Usuário tipo "cliente" tenta acessar  
**Esperado:** Erro 403 "Acesso negado"  
**Resultado:** ✅ Bloqueado pelo `@require_admin`

### Teste 4: Cliente Sem Dados

**Entrada:** cliente_id válido mas sem dados cadastrados  
**Esperado:** Arquivo JSON com arrays vazios  
**Resultado:** ✅ Exporta estrutura vazia

---

## 📖 EXEMPLOS DE USO

### 1. Backup Antes de Migração
```
Admin precisa migrar dados do cliente 10 para novo sistema
1. Exportar dados do cliente 10
2. Revisar arquivo JSON
3. Importar no novo sistema
```

### 2. Auditoria de Dados
```
Auditor precisa analisar dados do cliente 20
1. Exportar dados do cliente 20
2. Analisar lançamentos financeiros
3. Gerar relatório de auditoria
```

### 3. LGPD - Direito à Portabilidade
```
Cliente solicita cópia de seus dados
1. Admin exporta dados do cliente
2. Entrega arquivo JSON ao cliente
3. Registra log de portabilidade
```

---

## 🔧 MANUTENÇÃO

### Adicionar Nova Tabela à Exportação

**Exemplo:** Exportar tabela "contratos"

```python
# Em database_postgresql.py - função exportar_dados_cliente()

# 6. Exportar Contratos
cursor.execute("""
    SELECT * FROM contratos
    WHERE proprietario_id = %s
    ORDER BY data_criacao
""", (cliente_id,))

contratos = cursor.fetchall()
for contrato in contratos:
    export_data['contratos'].append({
        'id': contrato['id'],
        'numero': contrato['numero'],
        # ... outros campos
    })

# Adicionar ao metadata
export_data['metadata']['estatisticas']['total_contratos'] = len(contratos)
```

---

## ✅ CONCLUSÃO

A funcionalidade de exportação de dados por cliente está **completa e segura**, permitindo que administradores:
- ✅ Exportem dados de clientes específicos
- ✅ Façam backup seletivo
- ✅ Cumpram LGPD (portabilidade)
- ✅ Auditem dados
- ✅ Migrem dados para outros sistemas

**Isolamento Garantido:** Exporta APENAS dados do cliente selecionado, sem vazamento para outros clientes.

---

**Documentação criada em:** 11 de Janeiro de 2026  
**Autor:** Sistema de Documentação Automática  
**Versão:** 1.0
