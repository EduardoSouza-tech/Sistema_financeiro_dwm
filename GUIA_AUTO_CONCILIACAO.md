# 🚀 EXECUTAR MIGRATION: Regras de Auto-Conciliação

## ✅ Código Deploy fiado no Railway

**Commit:** `fb7847d`  
**Mensagem:** feat: Sistema de Auto-Conciliação Inteligente com Integração de Folha de Pagamento

O Railway está re-deployando automaticamente! (~2-3 minutos)

---

## 📋 PASSO 1: Executar Migration no Banco

Você precisa executar o script SQL para criar a estrutura no banco:

```powershell
py executar_migration_regras.py
```

### O que será criado:
✅ Tabela `regras_conciliacao`  
✅ Função `buscar_regras_aplicaveis()`  
✅ Função `buscar_funcionario_por_cpf()`  
✅ 4 Permissões (view/create/edit/delete)  
✅ Triggers e índices

---

## 🎯 PASSO 2: Como Usar o Sistema

### 1️⃣ Acessar Configuração
1. Entre em **🏦 Extrato Bancário**
2. Clique no botão **⚙️ Configuração de Extrato** (roxo, ao lado de "Conciliação Geral")

### 2️⃣ Criar Regra Simples
**Exemplo 1: Resgates de Aplicação**

Clique em "➕ Nova Regra" e preencha:
- **Palavra-chave:** `RESGATE APLIC`
- **Descrição:** Resgates de aplicações financeiras
- **Categoria:** RECEITAS BANCARIAS
- **Subcategoria:** RENDIMENTOS BANCARIOS
- **Cliente Padrão:** _(deixar vazio)_
- **Integração Folha:** ❌ Desativada

**Resultado:**  
Quando o extrato tiver "RESGATE APLIC. FINANCEIRA-CAPTACAO", o sistema vai:
- ✅ Preencher categoria automaticamente
- ✅ Preencher subcategoria automaticamente

---

### 3️⃣ Criar Regra com Integração de Folha
**Exemplo 2: Pagamentos PIX para Funcionários**

Clique em "➕ Nova-Regra" e preencha:
- **Palavra-chave:** `PAGAMENTO PIX`
- **Descrição:** Pagamentos PIX (detecta funcionários)
- **Categoria:** DESPESAS COM TERCEIROS
- **Subcategoria:** SERVIÇOS DE TERCEIROS TOMADOS
- **Cliente Padrão:** _(deixar vazio)_
- **Integração Folha:** ✅ **ATIVA** ← IMPORTANTE!

**Resultado:**  
Quando o extrato tiver "PAGAMENTO PIX 02141584620 EMILLY THAYNA DE JESUS":
- ✅ Detecta palavra "PAGAMENTO PIX"
- ✅ Extrai CPF "02141584620" da descrição
- ✅ Busca funcionário "EMILLY THAYNA DE JESUS" na folha
- ✅ Preenche categoria, subcategoria E nome automaticamente!

---

## 🔍 PASSO 3: Testar a Detecção

1. Vá em **🏦 Extrato Bancário**
2. Clique em **🔗 Conciliar** em qualquer transação
3. **Sistema detecta automaticamente:**
   - Se a descrição contém uma palavra-chave cadastrada
   - Preenche os campos automaticamente
   - Mostra badges **"✅ Auto-selecionado pela regra"**
   - Exibe toast: **"🤖 Auto-conciliação: RESGATE APLIC detectado"**

4. Se integração folha ativa E CPF detectado:
   - Toast: **"✅ Funcionário detectado: EMILLY THAYNA DE JESUS"**
   - Campo "Fornecedor" já preenchido!

---

## 📊 Exemplos Práticos

### Caso 1: Rendimentos Bancários
**Descrição do Extrato:**  
`RESGATE APLIC. FINANCEIRA-CAPTACAO`

**Regra cadastrada:**  
- Palavra: `RESGATE APLIC`
- Categoria: RECEITAS BANCARIAS
- Subcategoria: RENDIMENTOS BANCARIOS

**Resultado:**  
✅ Categoria e subcategoria preenchidas  
⚠️ Usuário precisa apenas confirmar!

---

### Caso 2: Pagamento a Funcionário (COM CPF)
**Descrição do Extrato:**  
`PAGAMENTO PIX-PIX_DEB 02141584620 EMILLY THAYNA DE JESUS`

**Regra cadastrada:**  
- Palavra: `PAGAMENTO PIX`
- Categoria: DESPESAS COM TERCEIROS
- Subcategoria: SERVIÇOS DE TERCEIROS TOMADOS
- Integração Folha: ✅ ATIVA

**Funcionário na folha:**  
- Nome: EMILLY THAYNA DE JESUS
- CPF: 021.415.846-20

**Resultado:**  
✅ Categoria: DESPESAS COM TERCEIROS  
✅ Subcategoria: SERVIÇOS DE TERCEIROS TOMADOS  
✅ Fornecedor: EMILLY THAYNA DE JESUS _(buscado da folha!)_  
⚠️ Usuário apenas confirma!

---

### Caso 3: Pagamento a Funcionário (SEM CPF visível)
**Descrição do Extrato:**  
`PAGAMENTO PIX-PIX_DEB 04393524608 JACIENE...`

**Se não houver o CPF completo:**  
✅ Categoria e subcategoria preenchidas  
❌ Nome NÃO detectado (CPF incompleto)  
⚠️ Usuário precisa selecionar o fornecedor manualmente

---

## 🔐 Permissões

Para usar o sistema, o usuário precisa de:
- ✅ `lancamentos_view` - Ver extratos
- ✅ `lancamentos_create` - Criar regras
- ✅ `lancamentos_edit` - Editar regras
- ✅ `lancamentos_delete` - Excluir regras

_(Administradores já têm tudo isso automaticamente)_

---

## ⚙️ Gerenciamento de Regras

### Editar Regra
1. Clique no botão **✏️** na linha da regra
2. Modifique os campos desejados
3. Clique em **💾 Salvar Regra**

### Excluir Regra
1. Clique no botão **🗑️** na linha da regra
2. Confirme a exclusão

### Desativar Temporariamente
_(Recurso para versão futura: campo "ativo" já existe no banco)_

---

## 🎨 Interface Visual

A interface mostra:
- 📋 Lista de todas as regras cadastradas
- 🟢 Badge "✅ ATIVA" se integração folha ativa
- ⚪ Badge "DESATIVADA" se integração folha desativada
- ✏️ Botão editar (azul)
- 🗑️ Botão excluir (vermelho)

---

## 🔧 Solução de Problemas

### Regra não está detectando
✅ Verifique se o texto da palavra-chave está na descrição  
✅ Palavra-chave é case-insensitive ("PIX" = "pix" = "Pix")  
✅ Verifique se a regra está para a empresa correta  

### CPF não está sendo detectado
✅ Verifique se o CPF tem 11 dígitos na descrição  
✅ Verifique se o CPF está cadastrado na folha com mesma formatação  
✅ Verifique se a flag "Integração Folha" está ATIVA  
✅ Verifique se o funcionário está ATIVO na folha  

### Funcionário não aparece
✅ Verifique se o CPF na folha está sem formatação (só números)  
✅ Verifique se o funcionário pertence à mesma empresa  
✅ Verifique se ativo = TRUE na tabela funcionarios  

---

## 📱 Responsivo

A interface funciona em:
✅ Desktop (tela completa)  
✅ Tablet (redimensionado)  
✅ Mobile (scroll horizontal na tabela)  

---

## 🚀 Próximos Passos

Após executar a migration (`py executar_migration_regras.py`):

1. ✅ Recarregue a página (Ctrl+F5)
2. ✅ Vá em Extrato Bancário
3. ✅ Clique em "⚙️ Configuração de Extrato"
4. ✅ Cadastre suas primeiras regras
5. ✅ Teste conciliando uma transação!

---

## 💡 Dicas de Uso

**🎯 Priorize regras específicas:**  
- "PAGAMENTO PIX" é genérico
- "PAGAMENTO PIX-PIX_DEB" é mais específico
- Sistema aplica a regra MAIS ESPECÍFICA (maior tamanho)

**👥 Use integração folha apenas se:**  
- O CPF SEMPRE aparece na descrição
- Os funcionários estão TODOS cadastrados na folha
- Você quer automatização 100%

**📂 Organize por tipo:**  
- Regras de receita (RESGATE, TED RECEBIDO, PIX RECEBIDO)
- Regras de despesa (PAGAMENTO, DEBITO AUTO, TARIFA)

---

## 📞 Suporte

Caso precise de ajuda:
1. Console do navegador (F12) - ver logs
2. Railway logs - ver erros do backend
3. PostgreSQL - verificar se migration rodou (`SELECT COUNT(*) FROM regras_conciliacao`)

---

**Sistema pronto para uso! 🚀**
