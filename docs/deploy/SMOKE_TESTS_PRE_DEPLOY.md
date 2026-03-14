# 🔥 SMOKE TESTS PRE-DEPLOY
## Checklist Obrigatório Antes de Git Push (5 minutos)

**⏱️ Tempo estimado:** 5 minutos  
**🎯 Objetivo:** Detectar bugs ANTES de afetar usuários  
**✅ Meta:** 100% dos deploys testados

---

## 🚨 REGRA DE OURO

```
❌ SE QUALQUER TESTE FALHAR → NÃO FAZER DEPLOY!
✅ TODOS OS TESTES PASSARAM → Deploy liberado
```

---

## ✅ CHECKLIST DE TESTES (Execute em ordem)

### 📋 PRÉ-REQUISITOS

- [ ] Servidor local rodando OU staging environment disponível
- [ ] Usuário de teste criado (não usar admin em produção!)
- [ ] Console do browser aberto (F12)

---

## 1️⃣ AUTENTICAÇÃO (30 segundos)

### Teste 1.1: Login
- [ ] Abrir página de login
- [ ] Inserir credenciais válidas
- [ ] Clicar "Entrar"
- [ ] **Esperado:** Redireciona para dashboard
- [ ] **Esperado:** Nome do usuário aparece no topo

### Teste 1.2: Sessão Persistente
- [ ] Recarregar página (F5)
- [ ] **Esperado:** Continua logado (não volta para login)

### Teste 1.3: Logout
- [ ] Clicar botão "🚪 Sair"
- [ ] **Esperado:** Volta para tela de login
- [ ] **Esperado:** Não mostra mais nome do usuário

**❌ Se falhou:** Problema crítico de autenticação - NÃO DEPLOY!

---

## 2️⃣ DASHBOARD (15 segundos)

### Teste 2.1: Carregamento
- [ ] Dashboard carrega sem erro
- [ ] Widgets aparecem (contas, saldos, gráficos)
- [ ] **Esperado:** Saldo total de bancos exibe valor (não "R$ 0,00" se houver saldo)

### Teste 2.2: Console
- [ ] Abrir console do browser (F12)
- [ ] **Esperado:** ❌ Sem erros vermelhos
- [ ] **Esperado:** ❌ Sem "Failed to load resource"

**❌ Se falhou:** Dashboard quebrado - NÃO DEPLOY!

---

## 3️⃣ CONTAS A RECEBER (1 minuto)

### Teste 3.1: Listar Lançamentos
- [ ] Clicar "💰 Financeiro" → "💵 Contas a Receber"
- [ ] **Esperado:** Tabela carrega (mesmo que vazia)
- [ ] **Esperado:** Datas aparecem no formato DD/MM/YYYY
- [ ] **Esperado:** Sem datas com -1 dia

### Teste 3.2: Abrir Modal Nova Receita
- [ ] Clicar botão "➕ Nova Receita"
- [ ] **Esperado:** Modal abre
- [ ] **Esperado:** Select "Cliente" tem opções (se houver clientes cadastrados)
- [ ] **Esperado:** Select "Categoria" tem opções
- [ ] **Esperado:** Select "Conta Bancária" tem opções

### Teste 3.3: Criar Receita Teste
- [ ] Preencher todos os campos obrigatórios
- [ ] Data: Usar data de hoje
- [ ] Valor: R$ 10,00 (valor teste)
- [ ] Clicar "Salvar"
- [ ] **Esperado:** Toast "✅ Receita criada com sucesso"
- [ ] **Esperado:** Receita aparece na tabela
- [ ] **Esperado:** Data correta (mesmo dia escolhido)

### Teste 3.4: Editar Receita
- [ ] Clicar "✏️ Editar" na receita teste
- [ ] Alterar valor para R$ 15,00
- [ ] Clicar "Salvar"
- [ ] **Esperado:** Toast "✅ Receita atualizada"
- [ ] **Esperado:** Valor alterado aparece na tabela

### Teste 3.5: Deletar Receita Teste
- [ ] Clicar "🗑️ Deletar" na receita teste
- [ ] Confirmar exclusão
- [ ] **Esperado:** Toast "✅ Receita deletada"
- [ ] **Esperado:** Receita some da tabela

**❌ Se falhou:** Problema no módulo financeiro - NÃO DEPLOY!

---

## 4️⃣ CONTAS A PAGAR (1 minuto)

### Teste 4.1: Listar Lançamentos
- [ ] Clicar "💰 Financeiro" → "💳 Contas a Pagar"
- [ ] **Esperado:** Tabela carrega

### Teste 4.2: Abrir Modal Nova Despesa ⚠️ **CRÍTICO**
- [ ] Clicar botão "➕ Nova Despesa"
- [ ] **Esperado:** Modal abre
- [ ] **⚠️ CRÍTICO:** Select "Fornecedor" TEM OPÇÕES (não "Nenhum fornecedor cadastrado")
- [ ] **Esperado:** Select "Categoria" tem opções (apenas despesas)
- [ ] **Esperado:** Select "Conta Bancária" tem opções

### Teste 4.3: Verificar window.fornecedores (Console)
```javascript
// No console do browser:
console.log('window.fornecedores:', window.fornecedores);
console.log('Quantidade:', window.fornecedores?.length);
```
- [ ] **Esperado:** window.fornecedores NÃO é undefined
- [ ] **Esperado:** window.fornecedores.length > 0 (se houver fornecedores cadastrados)

### Teste 4.4: Criar Despesa Teste
- [ ] Selecionar fornecedor
- [ ] Data: Hoje
- [ ] Valor: R$ 5,00
- [ ] Clicar "Salvar"
- [ ] **Esperado:** Toast "✅ Despesa criada com sucesso"
- [ ] **Esperado:** Não aparece erro "No module named 'dateutil'"

### Teste 4.5: Deletar Despesa Teste
- [ ] Deletar despesa criada
- [ ] **Esperado:** Sucesso

**❌ Se falhou:** Problema crítico em despesas - NÃO DEPLOY!

---

## 5️⃣ CADASTROS (30 segundos)

### Teste 5.1: Categorias
- [ ] Clicar "📋 Cadastros" → "📁 Categorias"
- [ ] **Esperado:** Lista de categorias carrega
- [ ] **Esperado:** Separadas em Receitas e Despesas

### Teste 5.2: Clientes
- [ ] Clicar "📋 Cadastros" → "👤 Clientes"
- [ ] **Esperado:** Lista carrega

### Teste 5.3: Fornecedores
- [ ] Clicar "📋 Cadastros" → "🏭 Fornecedores"
- [ ] **Esperado:** Lista carrega
- [ ] **Esperado:** Se houver fornecedores, aparecem na tabela

### Teste 5.4: Contas Bancárias
- [ ] Clicar "📋 Cadastros" → "🏦 Contas Bancárias"
- [ ] **Esperado:** Lista carrega
- [ ] **Esperado:** Saldos aparecem corretamente

**❌ Se falhou:** Problema em cadastros - NÃO DEPLOY!

---

## 6️⃣ EVENTOS (1 minuto 30s)

### Teste 6.1: Listar Eventos
- [ ] Clicar "⚙️ Operacional" → "🎉 Eventos"
- [ ] **Esperado:** Lista de eventos carrega
- [ ] **Esperado:** Datas corretas (sem -1 dia)

### Teste 6.2: Criar Evento Teste
- [ ] Clicar "Novo Evento"
- [ ] Nome: "Teste Deploy"
- [ ] Data: Hoje
- [ ] Tipo: Qualquer
- [ ] Status: Planejamento
- [ ] Clicar "Salvar"
- [ ] **Esperado:** Toast "✅ Evento criado"
- [ ] **Esperado:** Evento aparece na tabela

### Teste 6.3: Editar Evento (⚠️ **BUG HISTÓRICO**)
- [ ] Clicar "✏️ Editar" no evento teste
- [ ] Alterar data para AMANHÃ
- [ ] Alterar status para "EM ANDAMENTO"
- [ ] Clicar "Salvar"
- [ ] **⚠️ CRÍTICO:** NÃO deve dar erro "ERR_CONNECTION_FAILED"
- [ ] **⚠️ CRÍTICO:** Toast "✅ Evento atualizado"
- [ ] **⚠️ CRÍTICO:** Data alterada aparece na tabela

### Teste 6.4: Deletar Evento (⚠️ **BUG HISTÓRICO**)
- [ ] Clicar "🗑️ Deletar" no evento teste
- [ ] Confirmar exclusão
- [ ] **⚠️ CRÍTICO:** NÃO deve dar erro 500
- [ ] **Esperado:** Toast "✅ Evento deletado"
- [ ] **Esperado:** Evento some da tabela

### Teste 6.5: Alocar Equipe (Se houver funcionários)
- [ ] Criar evento "Teste Equipe"
- [ ] Clicar "Alocar Equipe"
- [ ] Adicionar 1 funcionário
- [ ] **Esperado:** Funcionário aparece na tabela "Equipe Alocada"
- [ ] Clicar aba "✍️ Assinatura"
- [ ] **⚠️ CRÍTICO:** Lista de assinatura DEVE TER o mesmo funcionário
- [ ] Remover funcionário da equipe
- [ ] Clicar aba "✍️ Assinatura" novamente
- [ ] **⚠️ CRÍTICO:** Lista de assinatura DEVE estar vazia

**❌ Se falhou:** Problema crítico em eventos - NÃO DEPLOY!

---

## 7️⃣ CONSOLE DO BROWSER (10 segundos) ⚠️ **CRÍTICO**

### Teste 7.1: Verificação Final
- [ ] Abrir console (F12)
- [ ] Navegar por TODAS as abas testadas acima
- [ ] **⚠️ CRÍTICO:** ❌ SEM ERROS VERMELHOS
- [ ] **⚠️ CRÍTICO:** ❌ SEM "Failed to load resource: 500"
- [ ] **⚠️ CRÍTICO:** ❌ SEM "ReferenceError"
- [ ] **⚠️ CRÍTICO:** ❌ SEM "TypeError"
- [ ] **⚠️ CRÍTICO:** ❌ SEM "Uncaught"

### Erros Aceitáveis (podem ignorar):
```
✅ WARN: Service Worker registered (não é erro)
✅ INFO: Logs de debug com ✅ ou 📦 (são intencionais)
✅ 404 em recursos opcionais (ícones, fontes externas)
```

### Erros INACEITÁVEIS (bloqueiam deploy):
```
❌ ReferenceError: variavel is not defined
❌ TypeError: Cannot read property 'x' of undefined
❌ Failed to load resource: 500 (Internal Server Error)
❌ Failed to load resource: 401 (Unauthorized)
❌ Uncaught Error: ...
❌ SyntaxError: ...
```

**❌ Se tiver QUALQUER erro INACEITÁVEL → NÃO DEPLOY!**

---

## 📊 RESULTADO FINAL

### Contabilizar testes:

```
Total de testes: 50+
Passou: ___/50
Falhou: ___/50

✅ Se passou >= 48/50 (96%+) → Deploy LIBERADO
⚠️ Se passou 45-47/50 (90-95%) → Avaliar gravidade das falhas
❌ Se passou < 45/50 (<90%) → NÃO DEPLOY!
```

---

## 🚀 APÓS PASSAR NOS TESTES

### Próximos passos:

1. ✅ **Commit:**
   ```bash
   git add .
   git commit -m "fix: Descrição detalhada da mudança"
   ```

2. ✅ **Push para staging (se disponível):**
   ```bash
   git push origin staging
   # Aguardar deploy (~2 min)
   # Repetir SMOKE TESTS em staging
   ```

3. ✅ **Se staging passou → Push para produção:**
   ```bash
   git push origin main
   ```

4. ✅ **Monitorar produção (primeiros 5 min):**
   - Abrir Railway logs
   - Verificar se deploy completou
   - Acessar sistema em produção
   - Testar funcionalidade alterada novamente

---

## 📝 REGISTRO DE TESTES

### Template de registro (copiar e colar):

```
Data: ___/___/2026
Hora: ___:___
Testador: ___________
Branch: ___________
Commit: ___________

RESULTADO:
[ ] ✅ Autenticação
[ ] ✅ Dashboard
[ ] ✅ Contas a Receber
[ ] ✅ Contas a Pagar
[ ] ✅ Cadastros
[ ] ✅ Eventos
[ ] ✅ Console sem erros

STATUS: [✅ APROVADO | ❌ REPROVADO]

OBSERVAÇÕES:
_________________________________________________
_________________________________________________
```

---

## 🛟 SE ALGO FALHAR

### NÃO entre em pânico!

1. **Identificar o que falhou**
   - Anotar mensagem de erro exata
   - Screenshot se possível
   - Copiar stacktrace do console

2. **Reverter mudança localmente**
   ```bash
   git reset --hard HEAD~1  # Volta commit anterior
   ```

3. **Investigar causa**
   - Consultar MAPA_DEPENDENCIAS_CRITICAS.md
   - Verificar se alterou função em ZONA VERMELHA
   - Testar localmente a correção

4. **Re-testar após correção**
   - Executar SMOKE TESTS novamente
   - Só fazer deploy após 100% passar

---

## 📞 DÚVIDAS FREQUENTES

**P: Posso pular algum teste se estou com pressa?**  
R: ❌ NÃO! Todos os testes são críticos. 5 minutos agora economizam 2 horas corrigindo depois.

**P: E se estou corrigindo apenas um CSS?**  
R: ✅ Pode pular testes de BACKEND (criação/edição), mas DEVE testar navegação e console.

**P: Posso fazer deploy diretamente para produção?**  
R: ⚠️ SIM, mas APENAS se não tiver staging. Ideal é sempre testar em staging primeiro.

**P: O que fazer se houver 1 ou 2 testes falhando?**  
R: ⚠️ Avaliar gravidade. Se for funcionalidade não relacionada à mudança, pode ser bug pré-existente. Documentar e corrigir depois, mas se for algo que você quebrou → NÃO DEPLOY!

---

**Documento criado:** 13/02/2026  
**Próxima revisão:** Semanalmente  
**Responsável:** Toda a equipe
