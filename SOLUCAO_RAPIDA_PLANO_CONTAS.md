# 🚨 SOLUÇÃO RÁPIDA - Plano de Contas Corrompido

## ❌ Problema Identificado

O banco de dados contém **2 registros corrompidos** na tabela `plano_contas_versao`:

```json
{
  "id": "id",             ← String literal em vez de número
  "nome_versao": "nome_versao",
  "exercicio_fiscal": "exercicio_fiscal"
}
```

Isso faz com que a interface mostre "id" em vez do número real da versão.

---

## ✅ Solução Aplicada (Commit ca9871c)

### 1. **Validação no Backend** ✅ JÁ DEPLOYADO

O código agora **detecta e pula** linhas corrompidas automaticamente:

```python
# Validação crítica
if v.get('id') == 'id' or v.get('nome_versao') == 'nome_versao':
    logger.error("❌ LINHA CORROMPIDA DETECTADA - Pulando!")
    continue
```

**Status:** ✅ Código em produção (aguardar 2-3 min para Railway deployar)

---

### 2. **Limpar Dados Corrompidos** ⚠️ AÇÃO NECESSÁRIA

Execute o SQL de limpeza no Railway:

#### **Opção A - Railway Dashboard (RECOMENDADO)**

1. Acessar https://railway.app
2. Selecionar projeto
3. Ir na aba **Data** (PostgreSQL)
4. Clicar em **Query**
5. Copiar e colar o conteúdo de: `limpar_dados_corrompidos_plano_contas.sql`
6. Executar (Run Query)

#### **Opção B - Railway CLI**

```powershell
railway connect postgresql
```

Depois copiar e colar o SQL do arquivo `limpar_dados_corrompidos_plano_contas.sql`

---

## 📋 O Que o SQL Faz

```sql
-- 1. Mostra linhas corrompidas
SELECT * FROM plano_contas_versao WHERE nome_versao = 'nome_versao';

-- 2. Deleta linhas corrompidas  
DELETE FROM plano_contas_versao WHERE nome_versao = 'nome_versao';

-- 3. Verifica resultado
SELECT empresa_id, COUNT(*) FROM plano_contas_versao GROUP BY empresa_id;
```

---

## 🔄 Após Executar o SQL

### 1. Aguardar Deploy do Railway (2-3 minutos)

Verificar em: https://railway.app → Deployments

### 2. Limpar Cache do Navegador

- **Ctrl+Shift+Delete**
- Marcar "Imagens e arquivos em cache"
- Limpar dados

### 3. Hard Reload

- **Ctrl+F5**

### 4. Testar Interface

1. Acessar "Plano de Contas"
2. Abrir Console (F12)
3. Verificar logs:

**✅ Correto (se limpeza funcionou):**
```javascript
📦 data.versoes.length: 0  // Ou números reais se houver versões válidas
```

**❌ Ainda errado (se não limpou):**
```javascript
📦 Primeira versão: {"id":"id","nome_versao":"nome_versao"}
```

### 5. Aplicar Plano Padrão

Se após limpar ficou sem versões, clique em:
**"📦 Importar Plano Padrão"** na interface

Ou execute:
```powershell
railway run python aplicar_plano_railway_manual.py
```

---

## 🎯 Resumo das Ações

| # | Ação | Status | Tempo |
|---|------|--------|-------|
| 1 | Código corrigido e deployado | ✅ Feito (commit ca9871c) | 2-3 min |
| 2 | Executar SQL de limpeza | ⚠️ **FAÇA AGORA** | 1 min |
| 3 | Aguardar deploy | 🕐 Aguardando | 2-3 min |
| 4 | Limpar cache navegador | ⏳ Pendente | 10 seg |
| 5 | Testar interface | ⏳ Pendente | 30 seg |
| 6 | Aplicar plano padrão (se necessário) | ⏳ Condicional | 2 min |

---

## 📊 Logs Esperados Após Correção

### Backend (Railway):
```
🔍 Total de linhas retornadas: 2
❌ LINHA CORROMPIDA DETECTADA: {'id': 'id', ...}
❌ LINHA CORROMPIDA DETECTADA: {'id': 'id', ...}
✅ Total de versões processadas (válidas): 0
```

### Frontend (Console):
```javascript
📦 data.versoes.length: 0
⚠️ Nenhuma versão selecionada automaticamente
```

---

## 🆘 Se Problema Persistir

Envie os seguintes logs:

1. **Logs do Railway** (últimas 30 linhas após acessar Plano de Contas)
2. **Console do navegador** (F12 → Console → copiar tudo)
3. **Confirmação de execução do SQL** (print ou cópia do resultado)

---

## 🔍 Causa Raiz (Como isso aconteceu?)

**Possíveis causas:**
- Migração incompleta
- Teste manual que inseriu dados inválidos
- Script de importação com bug
- Problema de RLS (Row Level Security)

**Prevenção futura:**
- ✅ Validação adicionada no código (já implementado)
- 🔜 Script de validação de integridade
- 🔜 Constraint CHECK no banco de dados

---

**Próximo passo:** Execute o SQL de limpeza AGORA!

Arquivo: `limpar_dados_corrompidos_plano_contas.sql`
