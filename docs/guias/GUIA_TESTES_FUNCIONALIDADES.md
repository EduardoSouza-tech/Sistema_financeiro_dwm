# 🧪 Guia de Testes - Funcionalidades Corrigidas

## 📋 Checklist de Verificação

Use este documento para testar cada funcionalidade corrigida no sistema.

---

## 🔴 TESTES DE PRIORIDADE ALTA

### ✅ Teste 1: Edição de Fornecedor

**Funcionalidade:** `editarFornecedor()`  
**Arquivo:** `static/app.js`

**Passos:**
1. Faça login no sistema
2. Navegue para a seção "Fornecedores"
3. Clique no botão ✏️ (Editar) de qualquer fornecedor
4. O modal de edição deve abrir com os dados preenchidos
5. Altere algum campo (ex: telefone)
6. Clique em "Salvar"
7. Verifique se a alteração foi salva

**Resultado Esperado:**
- ✅ Modal abre corretamente
- ✅ Dados estão preenchidos
- ✅ Alterações são salvas
- ✅ Tabela é atualizada

**Como Verificar Erros:**
1. Abra o Console do navegador (F12)
2. Procure por: `✏️ Editando fornecedor:`
3. Deve aparecer: `✅ Fornecedor encontrado:`
4. E depois: `✅ Modal de edição aberto`

---

### ✅ Teste 2: API GET Fornecedor

**Funcionalidade:** `GET /api/fornecedores/<nome>`  
**Arquivo:** `web_server.py`

**Teste Manual via Console:**
```javascript
// Abra o Console (F12) e execute:
fetch('/api/fornecedores/NOME_DO_FORNECEDOR')
  .then(r => r.json())
  .then(d => console.log('Dados:', d))
```

**Resultado Esperado:**
```json
{
  "nome": "Fornecedor Teste",
  "cnpj": "12.345.678/0001-90",
  "telefone": "(11) 98765-4321",
  "email": "contato@fornecedor.com",
  "endereco": "Rua Exemplo, 123",
  "ativo": true,
  "proprietario_id": 1
}
```

**Teste de Permissões:**
- ✅ Admin pode ver qualquer fornecedor
- ✅ Usuário comum só vê fornecedores da sua empresa
- ❌ Erro 403 ao tentar ver fornecedor de outra empresa

---

### ✅ Teste 3: Edição de Comissão

**Funcionalidade:** `editarComissao()`  
**Arquivo:** `static/app.js`

**Passos:**
1. Navegue para a seção "Contratos"
2. Entre em um contrato que tenha comissões
3. Clique no botão ✏️ (Editar) de uma comissão
4. **Observe:** Se o modal não abrir, é esperado (modal ainda não criado)
5. Deve aparecer mensagem: "Modal de edição de comissão não implementado ainda"

**Resultado Esperado:**
- ✅ Função busca dados da API corretamente
- ✅ Console mostra: `📋 Dados da comissão:`
- ⚠️ Modal pode não abrir (isso é esperado)
- ✅ Não há erros JavaScript

**Para Criar o Modal (Próximo Passo):**
```javascript
// Em modals.js, adicione:
function openModalComissao(comissao) {
    // TODO: Implementar modal
    console.log('Abrir modal de comissão:', comissao);
}
window.openModalComissao = openModalComissao;
```

---

### ✅ Teste 4: Exclusão de Comissão

**Funcionalidade:** `excluirComissao()`  
**Arquivo:** `static/app.js`

**Passos:**
1. Navegue para a seção "Contratos"
2. Entre em um contrato que tenha comissões
3. Clique no botão 🗑️ (Excluir) de uma comissão
4. Confirme a exclusão
5. Verifique se a comissão foi removida

**Resultado Esperado:**
- ✅ Confirmação é solicitada
- ✅ Comissão é excluída do banco
- ✅ Lista é recarregada
- ✅ Mensagem de sucesso aparece

**Console deve mostrar:**
```
🗑️ Excluindo comissão ID: 123
   📡 Status: 200
   📦 Resposta: {success: true, message: "..."}
   ✅ Lista recarregada
```

---

## 🟡 TESTES DE PRIORIDADE MÉDIA

### ✅ Teste 5: Exportação de Clientes - PDF

**Funcionalidade:** `exportarClientesPDF()`  
**Arquivo:** `static/pdf_functions.js`

**Passos:**
1. Navegue para a seção "Clientes"
2. Clique no botão "📄 Exportar PDF"
3. Uma nova aba deve abrir com o PDF

**Resultado Esperado:**
- ✅ PDF é gerado e aberto em nova aba
- ✅ Contém todos os clientes ativos
- ✅ Formatação profissional
- ✅ Dados corretos

**Se Não Funcionar:**
1. Verifique se o endpoint existe: `GET /api/clientes/exportar/pdf`
2. Teste diretamente: Abra `http://localhost:5000/api/clientes/exportar/pdf`
3. Verifique permissões: Você tem `clientes_view`?

---

### ✅ Teste 6: Exportação de Clientes - Excel

**Funcionalidade:** `exportarClientesExcel()`  
**Arquivo:** `static/excel_functions.js`

**Passos:**
1. Navegue para a seção "Clientes"
2. Clique no botão "📊 Exportar Excel"
3. Arquivo .xlsx deve ser baixado

**Resultado Esperado:**
- ✅ Arquivo Excel é baixado
- ✅ Contém planilha "Clientes"
- ✅ Colunas: Nome, CNPJ, Telefone, Email, Cidade, Status
- ✅ Dados corretos e formatados

---

### ✅ Teste 7: Exportação de Fornecedores - PDF

**Funcionalidade:** `exportarFornecedoresPDF()`  
**Arquivo:** `static/pdf_functions.js`

**Passos:**
1. Navegue para a seção "Fornecedores"
2. Clique no botão "📄 Exportar PDF"
3. Uma nova aba deve abrir com o PDF

**Resultado Esperado:**
- ✅ PDF é gerado e aberto em nova aba
- ✅ Contém todos os fornecedores ativos
- ✅ Formatação profissional
- ✅ Dados corretos

---

### ✅ Teste 8: Exportação de Fornecedores - Excel

**Funcionalidade:** `exportarFornecedoresExcel()`  
**Arquivo:** `static/excel_functions.js`

**Passos:**
1. Navegue para a seção "Fornecedores"
2. Clique no botão "📊 Exportar Excel"
3. Arquivo .xlsx deve ser baixado

**Resultado Esperado:**
- ✅ Arquivo Excel é baixado
- ✅ Contém planilha "Fornecedores"
- ✅ Colunas: Razão Social, CNPJ, Telefone, Email, Cidade
- ✅ Dados corretos e formatados

---

## 🧪 TESTES AUTOMATIZADOS (OPCIONAL)

### Teste Jest - Frontend

Crie arquivo `tests/app.test.js`:

```javascript
describe('Funções de Edição', () => {
    test('editarFornecedor deve fazer fetch correto', async () => {
        global.fetch = jest.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({
                    nome: 'Teste',
                    cnpj: '12.345.678/0001-90'
                })
            })
        );
        
        await editarFornecedor('Teste');
        
        expect(fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/fornecedores/Teste')
        );
    });
});
```

### Teste Pytest - Backend

Crie arquivo `tests/test_fornecedores.py`:

```python
def test_obter_fornecedor(client, auth_header):
    """Testa GET /api/fornecedores/<nome>"""
    # Criar fornecedor teste
    response = client.post('/api/fornecedores', 
        json={'nome': 'Teste', 'cnpj': '12345678000190'},
        headers=auth_header
    )
    
    # Buscar fornecedor
    response = client.get('/api/fornecedores/Teste', headers=auth_header)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['nome'] == 'Teste'
    assert data['cnpj'] == '12345678000190'
```

---

## 📊 CHECKLIST GERAL

### Antes de Liberar para Produção

- [ ] Todos os 8 testes principais passaram
- [ ] Console não mostra erros JavaScript
- [ ] Logs do servidor não mostram erros Python
- [ ] Permissões multi-tenant funcionam
- [ ] CSRF tokens estão sendo enviados
- [ ] Modais abrem e fecham corretamente
- [ ] Dados são salvos no banco
- [ ] Exportações geram arquivos corretos

### Testes de Permissões

- [ ] Admin pode editar tudo
- [ ] Usuário comum só edita da sua empresa
- [ ] Erro 403 aparece quando sem permissão
- [ ] Logs registram tentativas não autorizadas

### Testes de Performance

- [ ] Edição de fornecedor < 500ms
- [ ] Exclusão de comissão < 300ms
- [ ] Exportação PDF < 3s
- [ ] Exportação Excel < 2s

---

## 🐛 DEBUGGING

### Problema: Modal não abre

**Verificar:**
1. Console JavaScript: `openModalFornecedor is not a function`?
2. Arquivo modals.js está carregado?
3. Verificar ordem de carregamento de scripts no HTML
4. Verificar se `window.openModalFornecedor` está definido

**Solução:**
```javascript
// No console:
console.log(typeof openModalFornecedor);
// Deve retornar: "function"

// Se retornar "undefined":
console.log(Object.keys(window).filter(k => k.includes('Modal')));
// Verifica quais modais estão disponíveis
```

---

### Problema: Erro 403 ao editar

**Verificar:**
1. Usuário tem permissão `fornecedores_edit`?
2. Fornecedor pertence à empresa do usuário?
3. Token CSRF está sendo enviado?

**Solução:**
```javascript
// No console:
fetch('/api/usuario/permissoes')
  .then(r => r.json())
  .then(d => console.log('Permissões:', d));

// Verificar CSRF:
console.log('CSRF Token:', document.querySelector('meta[name="csrf-token"]')?.content);
```

---

### Problema: Exportação não funciona

**Verificar:**
1. Endpoint retorna 200?
2. Biblioteca (SheetJS) está carregada?
3. Popup blocker está ativo?

**Teste Manual:**
```javascript
// Testar endpoint diretamente:
window.open('/api/clientes/exportar/pdf', '_blank');

// Se não abrir, verificar popup blocker
```

---

## ✅ RESULTADO FINAL

Após completar todos os testes, você deve ter:

| Funcionalidade | Status | Observação |
|----------------|--------|------------|
| Editar Fornecedor | ✅ | Completo |
| API GET Fornecedor | ✅ | Completo |
| Editar Comissão | 🟡 | Falta criar modal |
| Excluir Comissão | ✅ | Completo |
| Exportar Clientes PDF | ✅ | Completo |
| Exportar Clientes Excel | ✅ | Completo |
| Exportar Fornecedores PDF | ✅ | Completo |
| Exportar Fornecedores Excel | ✅ | Completo |

**Taxa de Sucesso Esperada:** 87.5% (7/8 completo, 1 aguardando modal)

---

## 📝 RELATÓRIO DE TESTES

Após completar, preencha:

**Data do Teste:** _________________  
**Testador:** _________________  
**Ambiente:** ___ Desenvolvimento ___ Produção  

**Resultados:**
- Testes Passados: ___/8
- Testes Falhados: ___/8
- Bugs Encontrados: _______________________
- Sugestões de Melhoria: _______________________

**Aprovação Final:**
- [ ] Aprovar para produção
- [ ] Necessita correções

**Assinatura:** _________________

---

**Última Atualização:** 2026-01-15  
**Versão:** 1.0  
**Desenvolvido por:** GitHub Copilot (Claude Sonnet 4.5)
