# 🔍 DIAGNÓSTICO: Plano de Contas Retornando Nomes de Colunas

## 🚨 Problema Identificado

O backend está retornando **nomes de colunas** em vez de **valores reais**:

```json
{
  "id": "id",
  "nome_versao": "nome_versao",
  "exercicio_fiscal": "exercicio_fiscal"
}
```

Isso indica um dos seguintes problemas:

### 1️⃣ Tabela Vazia (Mais Provável)
- A tabela `plano_contas_versao` existe mas está vazia
- O código tenta processar linhas vazias e cria dict incorreto

### 2️⃣ Dados Corrompidos
- Há uma linha no banco que literalmente contém strings "id", "nome_versao", etc.

### 3️⃣ Bug no Cursor
- O cursor do PostgreSQL está mal configurado

---

## 🛠️ Solução: Executar Scripts de Diagnóstico

### Passo 1: Obter DATABASE_URL do Railway

**No terminal PowerShell:**
```powershell
railway variables --json | ConvertFrom-Json | Select-Object -ExpandProperty DATABASE_URL
```

**Ou acessar Railway Dashboard:**
1. Ir em https://railway.app
2. Selecionar projeto
3. Aba **Variables**
4. Copiar valor de `DATABASE_URL`

---

### Passo 2: Executar Teste Simples

```powershell
python teste_cursor_simples.py
```

**Cole a DATABASE_URL quando solicitado.**

**Resultado Esperado:**
- Se tabela vazia: `Total: 0`
- Se dados corrompidos: Verá linha com strings "id", "nome_versao"
- Se dados corretos: Verá números e textos reais

---

### Passo 3: Diagnóstico Completo

```powershell
python debug_plano_contas_railway.py
```

**Este script vai:**
- ✅ Verificar se tabelas existem
- ✅ Contar registros por empresa
- ✅ Mostrar detalhes dos dados
- ✅ Identificar exatamente onde está o problema

---

### Passo 4: Aplicar Plano Padrão (Se Necessário)

Se a tabela estiver vazia:

```powershell
python aplicar_plano_railway_manual.py
```

**Este script vai:**
1. Listar empresas disponíveis
2. Solicitar qual empresa aplicar
3. Criar versão "Plano Padrão 2026" com 79 contas
4. Confirmar sucesso

---

## 📊 Análise dos Logs

### Logs do Backend (Railway)

Acesse os logs do Railway e procure por:

```
🔍 Colunas retornadas: ['id', 'nome_versao', ...]
🔍 Total de linhas retornadas: X
🔍 Linha 0: (...)
🔍 Dict criado: {...}
```

**Se não aparecer:** O backend não está sendo chamado (problema no frontend)  
**Se aparecer com valores estranhos:** Problema no banco de dados

---

## 🎯 Possíveis Causas e Soluções

### Causa 1: Tabela Realmente Vazia ✅ MAIS PROVÁVEL

**Sintoma:**
```
🔍 Total de linhas retornadas: 0
```

**Solução:**
```powershell
python aplicar_plano_railway_manual.py
```

---

### Causa 2: Linha Corrompida no Banco 🔍

**Sintoma:**
```sql
SELECT * FROM plano_contas_versao WHERE empresa_id = 20;
-- Retorna: | id | nome_versao | exercicio_fiscal |
```

**Solução:**
```sql
-- Conectar ao Railway e executar:
DELETE FROM plano_contas_versao WHERE empresa_id = 20 AND nome_versao = 'nome_versao';
```

Depois aplicar plano padrão via script.

---

### Causa 3: Cache do Backend no Railway 🔄

**Sintoma:**
- Logs antigos ainda aparecem
- Mudanças no código não refletem

**Solução:**
```bash
# No Railway dashboard:
1. Aba "Deployments"
2. Clicar em "Redeploy" no último deployment
3. Aguardar 2-3 minutos
```

---

## 🚀 Ordem de Execução Recomendada

### 1. Diagnóstico Rápido (30 segundos)
```powershell
python teste_cursor_simples.py
```

### 2. Se mostrar tabela vazia: Aplicar Plano (2 minutos)
```powershell
python aplicar_plano_railway_manual.py
```

### 3. Verificar no navegador
1. **Ctrl+Shift+Delete** → Limpar cache
2. **Ctrl+F5** → Hard reload
3. Acessar "Plano de Contas"
4. Verificar logs do console (F12)

### 4. Se ainda não funcionar: Diagnóstico Completo
```powershell
python debug_plano_contas_railway.py
```

**Enviar resultado completo para análise.**

---

## 📋 Checklist de Verificação

- [ ] **Passo 1:** Obter DATABASE_URL do Railway
- [ ] **Passo 2:** Executar `teste_cursor_simples.py`
- [ ] **Passo 3:** Verificar se tabela está vazia
- [ ] **Passo 4:** Aplicar plano padrão se necessário
- [ ] **Passo 5:** Limpar cache do navegador
- [ ] **Passo 6:** Testar interface
- [ ] **Passo 7:** Verificar logs do Railway
- [ ] **Passo 8:** Enviar resultados se problema persistir

---

## 📞 Informações Necessárias para Debug

Se após todos os passos o problema persistir, envie:

1. **Output completo de `teste_cursor_simples.py`**
2. **Output completo de `debug_plano_contas_railway.py`**
3. **Logs do console do navegador (F12) ao acessar Plano de Contas**
4. **Screenshot dos logs do Railway (últimas 50 linhas)**

---

## ⚡ Solução Rápida (TL;DR)

```powershell
# 1. Obter DATABASE_URL
railway variables --json | ConvertFrom-Json | Select DATABASE_URL

# 2. Testar
python teste_cursor_simples.py

# 3. Se vazio, aplicar plano
python aplicar_plano_railway_manual.py

# 4. Limpar cache navegador (Ctrl+Shift+Delete)

# 5. Testar interface
```

---

**Status:** Scripts criados e prontos para uso  
**Próximo passo:** Executar `teste_cursor_simples.py`
