# 🗺️ MAPA DE DEPENDÊNCIAS CRÍTICAS
## Funções de Alto Risco - Testar TUDO antes de alterar

**Última atualização:** 13/02/2026  
**Objetivo:** Evitar quebrar funcionalidades ao corrigir bugs

---

## 🚨 LEGENDA DE RISCO

- 🔴 **ZONA VERMELHA** - Risco CRÍTICO (afeta 5+ funcionalidades)
- 🟡 **ZONA AMARELA** - Risco ALTO (afeta 2-4 funcionalidades)
- 🟢 **ZONA VERDE** - Risco BAIXO (função isolada)

---

## 🔴 ZONA VERMELHA (Testar TUDO ao alterar)

### 1. `formatarData()` - 5 LOCALIZAÇÕES

**Risco:** 🔴🔴🔴 CRÍTICO  
**Razão:** Usada em 50+ pontos do sistema

**Localizações:**
```
📍 static/utils.js (linha 117)
📍 static/app.js (linha 283)
📍 static/dashboard_sessoes.js (linha 454)
📍 templates/interface_nova.html (linha 9038)
📍 static/contratos.js (linha 1557)
```

**Usado em:**
- ✅ Contas a Receber (lista, modal, edição)
- ✅ Contas a Pagar (lista, modal, edição)
- ✅ Eventos (lista, modal, lista de presença)
- ✅ Dashboard (gráficos, widgets)
- ✅ Contratos (vencimentos)
- ✅ Folha de Pagamento (datas de pagamento)
- ✅ Relatórios (todos)

**Bug histórico:**
- **Feb 2026:** Timezone UTC → -1 dia (2026-02-08 virava 07/02/2026)

**Checklist obrigatório antes de alterar:**
```
[ ] Testar em Contas a Receber → Datas corretas na tabela
[ ] Testar em Contas a Pagar → Datas corretas na tabela
[ ] Testar em Eventos → Data do evento correta
[ ] Testar em Dashboard → Gráficos com datas corretas
[ ] Testar em Relatórios → Fluxo de caixa com datas corretas
[ ] Verificar console: Sem erros "Invalid Date"
[ ] Exportar Excel → Datas corretas no arquivo
```

**Código de teste rápido (console do browser):**
```javascript
// Testar função
console.log(Utils.formatarData('2026-02-08')); // Deve ser "08/02/2026"
console.log(Utils.formatarData('2026-12-31')); // Deve ser "31/12/2026"
console.log(Utils.formatarData('2026-01-01')); // Deve ser "01/01/2026"
```

---

### 2. `window.fornecedores` - VARIÁVEL GLOBAL CRÍTICA

**Risco:** 🔴🔴 ALTO  
**Razão:** Compartilhada entre múltiplos modais

**Onde é DEFINIDA:**
```
📍 static/app.js - loadFornecedores() (linha 5217)
   window.fornecedores = fornecedores;
```

**Onde é USADA:**
```
📍 static/modals.js - openModalDespesa() (linha 335)
📍 static/modals.js - editarDespesa() (linha 450)
📍 static/app.js - Relatórios com filtro de fornecedor
```

**Bug histórico:**
- **Feb 2026:** Fornecedores não apareciam no modal de despesa

**Checklist obrigatório:**
```
[ ] Abrir "Contas a Pagar" → "Nova Despesa"
    → Select de fornecedores DEVE ter opções
[ ] Editar despesa existente
    → Fornecedor atual DEVE aparecer selecionado
[ ] Relatórios → Filtrar por fornecedor
    → Lista de fornecedores disponível
[ ] Console: window.fornecedores DEVE estar definido
    → window.fornecedores.length > 0
```

**Código de teste (console):**
```javascript
// Verificar se está definido
console.log('window.fornecedores:', window.fornecedores);
console.log('Quantidade:', window.fornecedores?.length);

// Se undefined → BUG!
```

---

### 3. `carregarEquipeEvento()` - EVENTOS

**Risco:** 🔴🔴 ALTO  
**Razão:** Atualiza 3 áreas diferentes (equipe, assinatura, credenciamento)

**Localização:**
```
📍 templates/interface_nova.html (linha 7669)
```

**Chamado por:**
```
- Adicionar funcionário individual → carregarEquipeEvento()
- Adicionar funcionários em massa → carregarEquipeEvento()
- Remover funcionário → carregarEquipeEvento()
- Abrir modal de equipe → carregarEquipeEvento()
```

**DEPENDÊNCIAS CRÍTICAS:**
```
carregarEquipeEvento()
  ├─ Atualiza tbody-equipe-evento
  ├─ Recalcula custo total
  ├─ DEVE chamar → carregarListaAssinatura()  ⚠️ OBRIGATÓRIO!
  └─ DEVE chamar → loadEventos() (atualizar tabela principal)
```

**Bug histórico:**
- **Feb 2026:** Lista de assinatura desatualizada (funcionários diferentes da equipe)

**Checklist obrigatório:**
```
[ ] Alocar funcionário → Aparece na tabela "Equipe Alocada"
[ ] Remover funcionário → Some da tabela "Equipe Alocada"
[ ] Clicar aba "✍️ Assinatura"
    → Lista DEVE ter os MESMOS funcionários da equipe
[ ] Exportar PDF → Funcionários CORRETOS
[ ] Exportar Excel → Funcionários CORRETOS
[ ] Custo total atualizado corretamente
```

---

### 4. `atualizar_evento()` - BACKEND

**Risco:** 🔴🔴 CRÍTICO  
**Razão:** Função reescrita múltiplas vezes, propensa a bugs

**Localização:**
```
📍 web_server.py (linhas 5640-5790)
```

**Problemas históricos:**
```
❌ Feb 2026 (1): conn não definido (NameError)
❌ Feb 2026 (2): autocommit=False causava não persistir
❌ Feb 2026 (3): Connection pool leak
```

**Dependências:**
```
- db.get_connection() → DEVE ser chamado
- database.return_to_pool(conn) → DEVE estar no finally
- conn.commit() → DEVE ser explícito (mesmo com autocommit=True)
```

**Checklist obrigatório:**
```
[ ] Criar evento → Sucesso
[ ] Editar nome do evento → Persiste
[ ] Editar data do evento → Persiste (verificar no banco!)
[ ] Editar status → Persiste
[ ] Deletar evento → Não dá erro 500
[ ] Verificar pool de conexões não vaza:
    → SELECT count(*) FROM pg_stat_activity WHERE datname='railway';
    → Não deve crescer infinitamente
```

**Teste SQL direto:**
```sql
-- Após editar evento ID 10, verificar no banco:
SELECT id, nome_evento, data_evento, status 
FROM eventos 
WHERE id = 10;

-- Data DEVE estar atualizada!
```

---

## 🟡 ZONA AMARELA (Testar 3-4 funcionalidades)

### 5. `loadCategorias()` - BACKEND E FRONTEND

**Risco:** 🟡🟡 ALTO  
**Razão:** Usado por múltiplos modais

**Localização:**
```
📍 static/app.js (linha 1337)
```

**Usado por:**
```
- Modal de Nova Receita
- Modal de Nova Despesa
- Modal de Edição de Lançamento
- Relatórios (filtro por categoria)
```

**Checklist:**
```
[ ] Abrir modal de receita → Categorias carregam
[ ] Abrir modal de despesa → Categorias carregam
[ ] Editar lançamento → Categoria atual selecionada
[ ] Window.categorias definido corretamente
```

---

### 6. `salvarDespesa()` / `salvarReceita()` - MODALS.JS

**Risco:** 🟡🟡 ALTO  
**Razão:** Fluxo crítico de criação de lançamentos

**Localização:**
```
📍 static/modals.js (linha 484 - salvarDespesa)
📍 static/modals.js (linha 620 - salvarReceita)
```

**Dependências:**
```
- window.fornecedores (despesa)
- window.clientes (receita)
- window.categorias (ambos)
- window.currentEmpresaId (ambos)
```

**Bug histórico:**
- **Feb 2026:** Erro "No module named 'dateutil'" ao salvar despesa

**Checklist:**
```
[ ] Salvar nova despesa com fornecedor
[ ] Salvar nova receita com cliente
[ ] Datas salvam corretamente (sem -1 dia)
[ ] Valor salva corretamente
[ ] Parcelas funcionam (se houver)
[ ] Console sem erros 400/500
```

---

## 🟢 ZONA VERDE (Seguro alterar)

### 7. Funções de Formatação de Moeda

**Risco:** 🟢 BAIXO  
**Razão:** Funções puras, sem efeitos colaterais

```
- formatarMoeda()
- parseMoeda()
```

**Teste simples:**
```javascript
console.log(formatarMoeda(1500.50)); // "R$ 1.500,50"
console.log(parseMoeda("R$ 1.500,50")); // 1500.50
```

---

### 8. Funções de Validação

**Risco:** 🟢 BAIXO  
**Razão:** Não alteram estado global

```
- validarCPF()
- validarCNPJ()
- validarEmail()
```

---

## 📋 COMO USAR ESTE MAPA

### Antes de alterar QUALQUER função:

1. **Buscar neste arquivo:** Ctrl+F "nome da função"

2. **Se encontrar em ZONA VERMELHA:**
   ```
   ⚠️ ATENÇÃO MÁXIMA!
   └─ Executar TODOS os testes do checklist
   └─ Considerar criar função _v2 temporária
   └─ Validar em staging antes de produção
   ```

3. **Se encontrar em ZONA AMARELA:**
   ```
   ⚠️ CUIDADO!
   └─ Executar checklist básico
   └─ Testar funcionalidades relacionadas
   ```

4. **Se encontrar em ZONA VERDE:**
   ```
   ✅ Seguro alterar
   └─ Teste unitário simples suficiente
   ```

5. **Se NÃO encontrar:**
   ```
   ❓ Função desconhecida
   └─ Pesquisar no código onde é usada:
      grep -r "nomeDaFuncao" .
   └─ Adicionar neste mapa após análise
   ```

---

## 🔄 MANUTENÇÃO DESTE DOCUMENTO

**Este documento DEVE ser atualizado quando:**

- ✅ Nova função crítica identificada
- ✅ Bug causado por alteração em função existente
- ✅ Nova dependência criada entre funções
- ✅ Refatoração move funções de arquivo

**Responsabilidade:** Toda a equipe de desenvolvimento

---

## 📞 CONTATO EM CASO DE DÚVIDA

**Se não souber se pode alterar uma função:**
1. Consultar este mapa
2. Buscar no código onde é usada (grep/busca global)
3. Em caso de dúvida: **NÃO ALTERE** até validar com equipe
4. Sempre melhor perguntar do que quebrar produção

---

**Última revisão:** 13/02/2026  
**Próxima revisão:** Semanalmente (toda segunda-feira)
