# 🔍 Debug - Plano de Contas - Interface Não Lista Contas

## ❓ Problema Relatado
- Interface do Plano de Contas não lista as contas
- Logs mostram `versao_id=id` sendo enviado na URL (string literal em vez de número)
- Backend retorna 200 mas não há dados

## ✅ Implementação Correta no Backend
- ✅ Plano de Contas padrão com 79 contas criado
- ✅ Auto-aplicação em novas empresas implementada
- ✅ Todas as empresas existentes já têm plano de contas
- ✅ Rotas de API funcionando corretamente
- ✅ Cursor dict/tuple compatibility corrigido

## 🔧 Mudanças Implementadas (Commit Atual)

### 1. Logs de Debug Adicionados ao app.js

**Na função `carregarVersoesDropdown()` (linhas 8342-8377):**
```javascript
console.log('🔄 Carregando versões do dropdown...')
console.log('📦 Versões recebidas:', data)
console.log('🔍 Valor atual do select:', valorAtual)
console.log('➕ Adicionando versão:', v.id, '-', v.nome_versao)
console.log('⭐ Versão ativa encontrada:', versaoAtiva)
console.log('✅ Selecionada versão ativa:', versaoAtiva)
console.log('🎯 Valor final do select:', select.value)
console.log('🚀 Chamando carregarPlanoContas()...')
```

**Na função `carregarPlanoContas()` (linha 8391):**
```javascript
console.log('🔍 carregarPlanoContas - versaoId:', versaoId, 'tipo:', typeof versaoId)
console.warn('⚠️ versaoId inválido:', versaoId)
console.log('🌐 Fazendo requisição para URL:', url)
```

### 2. Validação Extra
- ✅ Bloqueia requisição se `versaoId === 'id'` (string literal)
- ✅ Verifica tipo do versaoId
- ✅ Mensagem clara se versão inválida

## 📋 Passos para o Usuário Diagnosticar

### Passo 1: Abrir Console do Navegador
1. Pressionar **F12** ou **Ctrl+Shift+I**
2. Ir na aba **Console**

### Passo 2: Acessar a Seção Plano de Contas
1. Fazer login no sistema
2. Clicar em "Plano de Contas" no menu lateral
3. **OBSERVAR OS LOGS NO CONSOLE**

### Passo 3: Verificar Logs Esperados
Você deve ver logs assim:
```
📒 Carregando módulo Plano de Contas...
🔄 Carregando versões do dropdown...
📦 Versões recebidas: {success: true, versoes: [...]}
➕ Adicionando versão: 42 - Plano Padrão 2026
⭐ Versão ativa encontrada: 42
✅ Selecionada versão ativa: 42
🎯 Valor final do select: 42
🚀 Chamando carregarPlanoContas()...
🔍 carregarPlanoContas - versaoId: 42 tipo: string
🌐 Fazendo requisição para URL: /api/contabilidade/plano-contas?versao_id=42
```

### Passo 4: Identificar o Problema

**Se aparecer:** `versaoId: id` ou `versaoId: undefined` → **PROBLEMA ENCONTRADO!**

**Possíveis Causas:**
1. **Cache do Navegador** - JavaScript antigo em cache
2. **Service Worker** - Servindo versão antiga do app.js
3. **CDN/Proxy** - Cache intermediário no servidor

## 🛠️ Soluções

### Solução 1: Limpar Cache do Navegador (RECOMENDADO)
1. Pressionar **Ctrl+Shift+Delete**
2. Selecionar "Últimas 24 horas" ou "Tudo"
3. Marcar:
   - ✅ Cookies e outros dados de sites
   - ✅ Imagens e arquivos em cache
4. Clicar em "Limpar dados"
5. Recarregar a página com **Ctrl+F5**

### Solução 2: Forçar Hard Reload
1. Abrir DevTools (F12)
2. Clicar com botão direito no ícone de **Recarregar** do navegador
3. Selecionar "**Esvaziar cache e recarregar forçadamente**"

### Solução 3: Desativar Service Worker Temporariamente
1. Abrir DevTools (F12)
2. Ir na aba **Application**
3. No menu lateral, clicar em **Service Workers**
4. Marcar "**Bypass for network**" ou "**Unregister**"
5. Recarregar a página

### Solução 4: Modo Anônimo (Teste)
1. Abrir navegador em **Modo Anônimo/Privado** (Ctrl+Shift+N)
2. Acessar o sistema
3. Se funcionar → Confirma que é cache local

### Solução 5: Railway Deploy (Se necessário)
Se nenhuma das soluções acima funcionar:
```bash
git add .
git commit -m "fix: Adicionar logs debug plano de contas"
git push origin main
```
Aguardar deploy no Railway (2-3 minutos)

## 📊 Análise Técnica

### Por que `versao_id=id` aparece nos logs?

**Hipótese mais provável:** JavaScript cacheado no navegador

O código correto está em:
- `static/app.js` linha 8353: `opt.value = v.id;`
- `static/app.js` linha 8392: `const versaoId = document.getElementById('pcVersaoFiltro').value;`

Mas se o navegador está usando uma versão antiga do `app.js`, pode ter um bug antigo que passou literalmente `"id"` como string.

### Por que o backend retorna 200?

No `web_server.py` linha 12814:
```python
versao_id = request.args.get('versao_id', type=int)
```

Flask tenta converter `"id"` para `int`, falha silenciosamente e define `versao_id = None`.

Na linha 12818-12820:
```python
contas = listar_contas(empresa_id, versao_id=None, ...)
return jsonify({'success': True, 'contas': [], 'total': 0})
```

Retorna lista vazia com sucesso (200) → Interface mostra "Nenhuma conta encontrada"

## 🎯 Resultado Esperado Após Correção

**Console do Navegador:**
```
🔍 carregarPlanoContas - versaoId: 42 tipo: string
🌐 Fazendo requisição para URL: /api/contabilidade/plano-contas?versao_id=42
```

**Interface:**
- ✅ Dropdown de versões populado
- ✅ Versão ativa selecionada automaticamente
- ✅ Tabela mostrando 79 contas do plano padrão
- ✅ Estatísticas atualizadas (75 Sintéticas, 4 Analíticas)

## 📞 Se o Problema Persistir

**Envie print ou texto com:**
1. Todos os logs do Console (F12 → Console)
2. Conteúdo da resposta da API: `/api/contabilidade/versoes`
3. Navegador e versão utilizada
4. Se está em produção (Railway) ou desenvolvimento local

**Comando para verificar versões no banco:**
```sql
SELECT id, nome_versao, exercicio_fiscal, is_ativa, empresa_id 
FROM plano_contas_versao 
ORDER BY empresa_id, exercicio_fiscal DESC;
```

---

**Última atualização:** 2026-02-04 18:45  
**Status:** Logs de debug adicionados, aguardando feedback do usuário
