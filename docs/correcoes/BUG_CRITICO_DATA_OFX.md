# 🐛 BUG CRÍTICO: Data do Extrato OFX -1 Dia (Railway)

**Data:** 24/02/2026  
**Severidade:** 🔴 CRÍTICA  
**Status:** 🔍 INVESTIGANDO

---

## 📋 Relato do Problema

### Sintoma
- **OFX diz:** `<DTPOSTED>20260223000000[-3:GMT]</DTPOSTED>` = 23/02/2026
- **Sistema mostra:** 22/02/2026 ❌
- **Diferença:** -1 dia

### Transação Afetada
```xml
<STMTTRN>
<TRNTYPE>CREDIT</TRNTYPE>
<DTPOSTED>20260223000000[-3:GMT]</DTPOSTED>
<TRNAMT>5279.00</TRNAMT>
<FITID>21230742427</FITID>
<MEMO>RECEBIMENTO PIX-PIX_CRED 35696831000124 CAIO J H TENORIO</MEMO>
</STMTTRN>
```

---

## 🔬 Investigação

### Teste Local (Windows)
```
ofxparse retorna: datetime.datetime(2026, 2, 23, 3, 0)  # naive
trans.date.date(): 2026-02-23
Resultado: ✅ 23/02/2026 CORRETO
```

### Produção (Railway - Linux/UTC)
```
Data exibida: ❌ 22/02/2026 ERRADO
```

---

## 🎯 Causa Raiz Identificada

### Problema: Timezone do Servidor
Railway roda em **Linux com timezone UTC**. O `ofxparse` se comporta diferente dependendo do timezone do sistema.

**Cenário 1 (Windows local - OK):**
```python
# ofxparse: 20260223000000[-3:GMT] → datetime(2026, 2, 23, 3, 0)
# Sistema entende: "3h da manhã do dia 23" (naive)
# .date() retorna: 2026-02-23 ✅
```

**Cenário 2 (Railway/UTC - BUG):**
```python
# ofxparse no UTC: 20260223000000[-3:GMT] → datetime(2026, 2, 23, 0, 0, tzinfo=UTC)
# Sistema converte 00:00 GMT-3 para UTC = 03:00 UTC dia 23
# MAS pode estar interpretando como "00:00 local" que em GMT-3 seria 21:00 do dia 22
# .date() retorna: 2026-02-22 ❌
```

### Onde Está o Bug
**Arquivo:** `web_server.py` linha 3695  
**Código atual:**
```python
'data': trans.date.date() if hasattr(trans.date, 'date') else trans.date
```

**Problema:**
- Se `trans.date` é **timezone-aware** (tem tzinfo)
- E o servidor está em **UTC**
- Ao fazer `.date()`, Python pode estar usando o timezone local do servidor
- Resultado: perde 1 dia quando hora < 03:00 GMT

---

## ✅ Solução

### Opção 1: Extrair Componentes Direto (RECOMENDADA)
```python
from datetime import date

# Ignora completamente timezone e hora, usa apenas ano/mês/dia
if hasattr(trans.date, 'year'):
    data_correta = date(trans.date.year, trans.date.month, trans.date.day)
else:
    data_correta = trans.date
```

**Vantagens:**
- ✅ Funciona independente de timezone do servidor
- ✅ Funciona com datetime aware ou naive
- ✅ Simples e direto
- ✅ Não depende de conversão de timezone

### Opção 2: Converter para GMT-3 Antes
```python
from datetime import timezone, timedelta

tz_brasil = timezone(timedelta(hours=-3))

if hasattr(trans.date, 'astimezone') and trans.date.tzinfo:
    # Se é aware, converter para GMT-3 primeiro
    dt_brasil = trans.date.astimezone(tz_brasil)
    data_correta = dt_brasil.date()
elif hasattr(trans.date, 'date'):
    # Se é naive, assumir que já está correto
    data_correta = trans.date.date()
else:
    data_correta = trans.date
```

**Vantagens:**
- ✅ Explicitamente converte para timezone correto
- ✅ Funciona com ambos aware/naive

**Desvantagens:**
- ⚠️ Mais complexo
- ⚠️ Depende de conversão de timezone

---

## 🔧 Implementação da Correção

### Localização
**Arquivo:** `web_server.py`  
**Linha:** 3695  
**Função:** `upload_extrato_ofx()`

### Código Atual (BUGADO)
```python
transacoes.append({
    'data': trans.date.date() if hasattr(trans.date, 'date') else trans.date,
    'descricao': trans.payee or trans.memo or 'Sem descricao',
    # ...
})
```

### Código Corrigido (OPÇÃO 1 - RECOMENDADA)
```python
from datetime import date

# Extrair data ignorando timezone/hora completamente
if hasattr(trans.date, 'year'):
    # Usar componentes year/month/day direto (ignora timezone)
    data_transacao = date(trans.date.year, trans.date.month, trans.date.day)
elif hasattr(trans.date, 'date'):
    # Fallback para .date() se não tiver year
    data_transacao = trans.date.date()
else:
    # Já é date object
    data_transacao = trans.date

transacoes.append({
    'data': data_transacao,
    'descricao': trans.payee or trans.memo or 'Sem descricao',
    # ...
})
```

### Código Corrigido (OPÇÃO 2 - COM TIMEZONE)
```python
from datetime import date, timezone, timedelta

# Timezone Brasil (GMT-3)
tz_brasil = timezone(timedelta(hours=-3))

# Extrair data com conversão de timezone
if hasattr(trans.date, 'astimezone') and trans.date.tzinfo is not None:
    # datetime timezone-aware: converter para GMT-3 primeiro
    dt_brasil = trans.date.astimezone(tz_brasil)
    data_transacao = dt_brasil.date()
elif hasattr(trans.date, 'year'):
    # datetime naive: usar componentes direto
    data_transacao = date(trans.date.year, trans.date.month, trans.date.day)
elif hasattr(trans.date, 'date'):
    # Fallback
    data_transacao = trans.date.date()
else:
    # Já é date
    data_transacao = trans.date

transacoes.append({
    'data': data_transacao,
    'descricao': trans.payee or trans.memo or 'Sem descricao',
    # ...
})
```

---

## 🧪 Como Testar

### Teste 1: Verificar Data Atual no Banco
```sql
SELECT id, data, descricao, valor
FROM transacoes_extrato
WHERE fitid = '21230742427';
```

**Esperado:**
- data = `2026-02-23` ✅

**Se mostrar:**
- data = `2026-02-22` ❌ → Bug confirmado

### Teste 2: Após Deploy da Correção
1. Deletar transação antiga (data errada)
2. Reimportar arquivo OFX
3. Verificar se data veio correta (23/02/2026)

### Teste 3: Teste de Borda
Importar OFX com transações:
- 00:00 do dia (primeira hora)
- 23:59 do dia (última hora)
- Meia-noite (transição de dia)

---

## 📊 Impacto

### Afetados
- ✅ Todos os extratos OFX já importados
- ✅ Todas as datas de transações bancárias
- ✅ Conciliações que dependem de match por data

### Não Afetados
- ✅ Lançamentos manuais (não usam ofxparse)
- ✅ Contas a pagar/receber (não usam ofxparse)
- ✅ Outros módulos do sistema

### Correção Necessária
- 🔧 Atualizar código (web_server.py)
- 🔄 Reimportar extratos já importados
- 🗑️ Deletar registros com data errada
- ✅ Verificar conciliações existentes

---

## 📝 Checklist de Deploy

- [ ] Implementar correção (Opção 1 ou 2)
- [ ] Testar localmente com arquivo OFX real
- [ ] Fazer commit
- [ ] Deploy no Railway
- [ ] Aguardar build (2-3 min)
- [ ] Deletar extratos com data errada
- [ ] Reimportar arquivos OFX
- [ ] Verificar datas corretas
- [ ] Revalidar conciliações
- [ ] Documentar correção

---

## 🚨 Urgência

**CRÍTICO** porque:
1. Afeta **todas** as importações OFX
2. Datas erradas comprometem **conciliação**
3. Relatórios ficam **inconsistentes**
4. Usuário perde **confiança** no sistema

**Action Required:** Implementar correção IMEDIATAMENTE

---

## 📚 Referências

- [Documentação ofxparse](https://github.com/jseutter/ofxparse)
- [Python datetime timezone](https://docs.python.org/3/library/datetime.html#timezone-objects)
- [Railway timezone config](https://docs.railway.app/reference/environment-variables)

---

**Investigado por:** Sistema de Análise Automatizada  
**Data:** 24/02/2026  
**Status:** 🔍 Solução identificada, aguardando implementação
