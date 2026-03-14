# 📊 PLANO DE CONTAS - GUIA RÁPIDO

## ✅ SOLUÇÃO PARA VERSÃO 4 VAZIA (AGORA)

Se a versão 4 está vazia (0 contas), use o script:

```powershell
python aplicar_plano_railway_manual.py
```

**O que ele faz:**
1. Conecta ao banco Railway
2. Lista todas as empresas
3. Mostra versões existentes e quantas contas cada uma tem
4. ⚠️ **DETECTA VERSÕES VAZIAS** automaticamente
5. Oferece opção de POPULAR versão vazia OU criar nova
6. Insere ~79 contas do plano padrão brasileiro

**Tempo:** 30 segundos

---

## 🔄 CRIAÇÃO AUTOMÁTICA (NOVAS EMPRESAS)

### ✅ SIM! Após deploy do commit `88c2a0a`, funciona automaticamente:

**Correção implementada em `contabilidade_functions.py`:**

```python
# ANTES (BUG):
if versao_existente:
    return  # ❌ Retornava sem verificar se tinha contas

# AGORA (CORRIGIDO):
if versao_existente:
    total_contas = contar_contas(versao_id)
    
    if total_contas > 0:
        return  # ✅ Só retorna se JÁ TEM contas
    
    # ✅ Se está vazia, POPULA automaticamente
    popular_versao(versao_id)
```

### 📋 Fluxo automático para novas empresas:

1. Usuário acessa "📊 Plano de Contas"
2. Clica no botão **"📦 Importar Plano Padrão"**
3. Sistema verifica:
   - ❌ Versão não existe? → Cria nova + insere 79 contas
   - ✅ Versão existe MAS vazia? → Popula ela com 79 contas
   - ✅ Versão existe COM contas? → Não faz nada
4. **Resultado:** Plano sempre populado corretamente!

---

## 🐛 PROBLEMA QUE HAVIA

### Situação anterior:
```
1. Sistema criava versão "Plano Padrão 2026" (ID 4)
2. Algum erro ocorria antes de inserir as contas
3. Versão ficava VAZIA (0 contas)
4. Usuário clicava "Importar Plano Padrão" de novo
5. Sistema via que versão existia e NÃO fazia nada
6. ❌ Interface permanecia vazia
```

### Solução implementada:
```
1. Sistema verifica versão existente
2. 📊 CONTA quantas contas ela tem
3. Se COUNT = 0 → ✅ POPULA automaticamente
4. Se COUNT > 0 → ⏭️ Ignora (já está OK)
```

---

## 🚀 COMANDOS ÚTEIS

### Verificar quantas contas uma versão tem:
```sql
SELECT COUNT(*) 
FROM plano_contas 
WHERE versao_id = 4 AND deleted_at IS NULL;
```

### Listar versões vazias:
```sql
SELECT v.id, v.nome_versao, COUNT(c.id) as total_contas
FROM plano_contas_versao v
LEFT JOIN plano_contas c ON c.versao_id = v.id AND c.deleted_at IS NULL
WHERE v.empresa_id = 20
GROUP BY v.id, v.nome_versao
HAVING COUNT(c.id) = 0;
```

### Popular manualmente via console do navegador:
```javascript
importarPlanoPadrao()
```

---

## 📦 ESTRUTURA DO PLANO PADRÃO

São criadas **~79 contas** seguindo estrutura brasileira:

- **1.** ATIVO (8 contas)
  - 1.1 Ativo Circulante
  - 1.2 Ativo Não Circulante

- **2.** PASSIVO (6 contas)
  - 2.1 Passivo Circulante
  - 2.2 Passivo Não Circulante

- **3.** PATRIMÔNIO LÍQUIDO (5 contas)
  - 3.1 Capital Social
  - 3.2 Reservas
  - 3.3 Lucros/Prejuízos

- **4.** RECEITAS (25 contas)
  - 4.1 Receita Operacional
  - 4.2 Receita Não Operacional

- **5.** DESPESAS (35 contas)
  - 5.1 Despesas Operacionais
  - 5.2 Despesas Não Operacionais

**Tipos:**
- 🏢 **Sintéticas:** Agrupadores (não permitem lançamento)
- 📝 **Analíticas:** Contas de movimento (permitem lançamento)

---

## 🔧 ARQUIVOS RELACIONADOS

- `contabilidade_functions.py` - Lógica de negócio (✅ corrigido)
- `plano_contas_padrao.py` - Dados do plano padrão (79 contas)
- `aplicar_plano_railway_manual.py` - Script manual para popular
- `web_server.py` - Rota API `/api/contabilidade/plano-contas/importar-padrao`
- `static/app.js` - Frontend (função `importarPlanoPadrao()`)

---

## ✅ STATUS ATUAL

- ✅ Bug identificado e corrigido (commit `88c2a0a`)
- ✅ Script manual criado para resolver AGORA
- ✅ Criação automática funcionará após deploy Railway
- ⏳ Deploy em andamento (2-3 minutos)

**Para resolver IMEDIATAMENTE:**
```powershell
python aplicar_plano_railway_manual.py
```

**Depois do deploy:**
- Apenas clique "📦 Importar Plano Padrão" na interface
- Sistema detecta versão vazia e popula automaticamente
