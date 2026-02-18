# Instruções para Aplicar a Migração: evento_fornecedores

## 📋 O que foi criado

Nova tabela `evento_fornecedores` para vincular fornecedores aos eventos com informações de:
- Fornecedor
- Categoria e Subcategoria do custo
- Valor do serviço
- Observações

## 🚀 Como aplicar a migração

### Opção 1: Via Railway (RECOMENDADO)

1. Acesse o Railway Dashboard
2. Vá em seu projeto > PostgreSQL
3. Clique em "Query"
4. Copie e cole o conteúdo do arquivo `migration_evento_fornecedores.sql`
5. Execute a query
6. Verifique se a tabela foi criada com:
```sql
SELECT * FROM evento_fornecedores LIMIT 1;
```

### Opção 2: Via Script Python (Local ou Railway)

Se você tem acesso ao Python no ambiente:

```bash
python aplicar_migracao_evento_fornecedores.py
```

### Opção 3: Manualmente via psql

```bash
psql -h [HOST] -U [USER] -d [DATABASE] -f migration_evento_fornecedores.sql
```

## ✅ Verificação

Após aplicar a migração, verifique:

```sql
-- Verificar se a tabela existe
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'evento_fornecedores';

-- Verificar estrutura
\d evento_fornecedores

-- Verificar índices
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'evento_fornecedores';
```

## 📊 Como usar o recurso

1. Acesse **Eventos Operacionais** → **Alocar Equipe no Evento**
2. Clique na aba **🏢 Fornecedores** (após "Em Massa")
3. Selecione:
   - Fornecedor (da lista de fornecedores cadastrados)
   - Categoria (opcional)
   - Subcategoria (opcional, depende da categoria)
   - Valor (obrigatório)
   - Observação (opcional)
4. Clique em "Adicionar Fornecedor"

## 💰 Cálculo de Custos

O sistema agora calcula:

**Custo Total do Evento = Custo da Equipe + Custo dos Fornecedores**

**Margem = Valor Líquido NF - Custo Total**

## ⚠️ Observações Importantes

- Fornecedores **NÃO** aparecem nas abas:
  - ✍️ Assinatura
  - 🎫 Credenciamento
  
- Apenas **cooperados da equipe** aparecem nessas abas

- Um fornecedor não pode ser adicionado duas vezes ao mesmo evento (constraint UNIQUE)

## 🔧 Troubleshooting

### Erro: "relation evento_fornecedores does not exist"
→ A migração não foi aplicada. Execute o SQL novamente.

### Erro: "duplicate key value violates unique constraint"
→ Você está tentando adicionar um fornecedor que já está no evento.

### Erro: "foreign key constraint"
→ Certifique-se de que:
  - O evento existe na tabela `eventos`
  - O fornecedor existe na tabela `fornecedores`
  - As categorias/subcategorias existem (se fornecidas)

## 📞 Suporte

Se encontrar problemas, verifique:
1. Logs do servidor (Railway ou local)
2. Console do navegador (F12)
3. Permissões do usuário ('eventos_edit', 'eventos_view')
