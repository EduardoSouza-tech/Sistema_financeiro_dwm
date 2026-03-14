# 📦 Documentação Completa - Kits de Equipamentos

**Módulo:** Operacional > Kits de Equipamentos  
**Versão:** 1.0  
**Data:** 20/01/2026  
**Status:** ✅ FUNCIONAL

---

## 📋 Sumário

1. [Visão Geral](#visão-geral)
2. [Como Usar](#como-usar)
3. [Estrutura do Banco de Dados](#estrutura-do-banco-de-dados)
4. [API - Endpoints](#api---endpoints)
5. [Problemas Comuns e Soluções](#problemas-comuns-e-soluções)
6. [Checklist de Teste](#checklist-de-teste)

---

## 🎯 Visão Geral

O módulo **Kits de Equipamentos** permite gerenciar conjuntos de equipamentos utilizados em sessões fotográficas ou filmagens.

### Funcionalidades

✅ Criar kits com nome, descrição, itens e valor  
✅ Editar kits existentes sem duplicar  
✅ Excluir kits com confirmação  
✅ Visualizar lista completa com itens e valores separados  
✅ Código único gerado automaticamente  

### Campos do Kit

| Campo | Descrição | Obrigatório |
|-------|-----------|-------------|
| **Nome** | Nome identificador do kit | ✅ Sim |
| **Descrição** | Detalhes sobre o kit | ❌ Não |
| **Itens** | Lista de equipamentos incluídos | ❌ Não |
| **Valor Total** | Preço do kit | ❌ Não (padrão: R$ 0,00) |

---

## 🚀 Como Usar

### 1️⃣ Criar Novo Kit

1. Acesse: **Operacional > Kits de Equipamentos**
2. Clique no botão **➕ Novo Kit**
3. Preencha:
   - **Nome do Kit:** (obrigatório) "Kit Fotografia Básico"
   - **Descrição:** "Kit para ensaios externos"
   - **Itens do Kit:** "Câmera Canon EOS R, Tripé Manfrotto, Lentes 50mm"
   - **Valor Total:** "1500.00"
4. Clique em **Criar Kit**

### 2️⃣ Editar Kit

1. Clique no botão **✏️ Editar**
2. Modal abre com campos preenchidos
3. Altere o que precisar
4. Clique em **Atualizar Kit**
5. ✅ Kit é atualizado (NÃO duplica)

### 3️⃣ Excluir Kit

1. Clique no botão **🗑️ Excluir**
2. Confirme
3. Kit removido permanentemente

### 4️⃣ Visualizar Tabela

| Nome | Descrição | Itens | Valor Total | Ações |
|------|-----------|-------|-------------|-------|
| Kit Fotografia Básico | Para ensaios simples | Câmera Canon, Tripé | R$ 1500.00 | ✏️ 🗑️ |

---

## 🗄️ Estrutura do Banco de Dados

### Tabela: `kits`

```sql
CREATE TABLE kits (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    preco DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    empresa_id INTEGER NOT NULL,
    ativo BOOLEAN DEFAULT TRUE
);
```

### Campos Importantes

- **`codigo`**: Gerado automaticamente (Ex: `KIT-1768930171-9749`)
- **`descricao`**: Armazena descrição + itens concatenados
- **`preco`**: Valor com 2 casas decimais
- **Nota:** NÃO existe coluna `data_atualizacao` no Railway

### Formato da Descrição

```
Descrição original do kit

Itens incluídos:
Lista de equipamentos
```

---

## 🔌 API - Endpoints

### GET `/api/kits`

Lista todos os kits cadastrados.

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "nome": "Kit Fotografia Básico",
      "descricao": "Kit completo\n\nItens incluídos:\nCâmera Canon, Tripé",
      "preco": 1500.00
    }
  ]
}
```

### POST `/api/kits`

Cria novo kit.

**Request:**
```json
{
  "nome": "Kit Fotografia Avançado",
  "descricao": "Kit profissional",
  "itens": "Câmera Full Frame, Tripé Manfrotto",
  "preco": 3000.00
}
```

**Processamento:**
1. Gera código único
2. Concatena itens na descrição
3. Define empresa_id = 1

**Response (201):**
```json
{
  "success": true,
  "message": "Kit criado com sucesso",
  "id": 6,
  "codigo": "KIT-1768930171-5432"
}
```

### PUT `/api/kits/<id>`

Atualiza kit existente (NÃO duplica).

**Request:**
```json
{
  "nome": "Kit Fotografia Premium",
  "descricao": "Kit atualizado",
  "itens": "Câmera R5, Tripé",
  "preco": 5000.00
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Kit atualizado com sucesso"
}
```

### DELETE `/api/kits/<id>`

Exclui kit permanentemente.

**Response (200):**
```json
{
  "success": true,
  "message": "Kit excluído com sucesso"
}
```

---

## 🐛 Problemas Comuns e Soluções

### ❌ Problema 1: Edição duplica kit

**Causa:** Campo `id` não estava sendo capturado

**Solução:**
```javascript
// ERRADO:
const id = document.getElementById('kit-id').value;

// CORRETO:
const idInput = form.elements['kit-id'];
const id = idInput?.value || '';
```

**Verificar:**
- Console mostra: `🔑 ID capturado: 8 | Modo: EDIÇÃO`
- Response status: `200` (não `201`)

---

### ❌ Problema 2: Campos aparecem vazios ao editar

**Causa:** Faltava atributo `name` nos inputs

**Solução:**
```html
<input type="text" id="kit-nome" name="kit-nome">
<textarea id="kit-descricao" name="kit-descricao"></textarea>
<textarea id="kit-itens" name="kit-itens"></textarea>
<input type="number" id="kit-preco" name="kit-preco">
```

**Verificar:**
- Campos aparecem preenchidos ao editar
- Console mostra valores corretos

---

### ❌ Problema 3: Tabela mostra "-" em Itens e Valor

**Causa:** Código não extraía dados reais

**Solução:**
```javascript
// Separar descrição e itens
const partes = kit.descricao.split('\n\nItens incluídos:\n');
const descricaoLimpa = partes[0];
const itensExtraidos = partes[1] || '';

// Formatar preço
const precoFormatado = kit.preco ? `R$ ${parseFloat(kit.preco).toFixed(2)}` : '-';
```

**Verificar:**
- Coluna Itens mostra: "Câmera Canon, Tripé"
- Coluna Valor Total mostra: "R$ 1500.00"

---

### ❌ Problema 4: Erro "column data_atualizacao does not exist"

**Causa:** Coluna não existe na tabela do Railway

**Solução:**
```python
# Remover referência à coluna
UPDATE kits SET nome = %s, descricao = %s, preco = %s WHERE id = %s
```

**Verificar:**
- PUT retorna status `200`
- Sem erros de coluna inexistente

---

### ❌ Problema 5: GET não retorna preço

**Causa:** SELECT não incluía o campo

**Solução:**
```python
SELECT id, nome, descricao, preco FROM kits
```

**Verificar:**
- API retorna campo `preco`
- Tabela mostra valores

---

## ✅ Checklist de Teste

### Criar Kit
- [ ] Preencher apenas nome → Cria com sucesso
- [ ] Preencher todos os campos → Cria com sucesso
- [ ] Tabela atualiza automaticamente
- [ ] Coluna Itens mostra equipamentos
- [ ] Coluna Valor Total mostra "R$ X.XX"

### Editar Kit
- [ ] Clicar em ✏️ → Modal abre
- [ ] Campo Nome preenchido
- [ ] Campo Descrição preenchido (sem itens)
- [ ] Campo Itens preenchido (separado)
- [ ] Campo Valor Total preenchido
- [ ] Alterar e salvar → Atualiza (NÃO duplica)

### Excluir Kit
- [ ] Clicar em 🗑️ → Confirmação
- [ ] Confirmar → Kit removido
- [ ] Tabela atualiza

### Console
- [ ] Criar: `➕ Criando kit...` → `✅ Kit criado`
- [ ] Editar: `✏️ Atualizando kit...` → `✅ Kit atualizado`
- [ ] Sem erros 500

---

## 📊 Fluxo de Dados

### Criar

```
Formulário → form.elements → POST /api/kits → 
Gera código → Concatena itens → INSERT → 
Retorna ID → Fecha modal → Recarrega tabela
```

### Editar

```
Clica ✏️ → Separa descrição/itens → Preenche campos →
form.elements (com ID) → PUT /api/kits/{id} → 
Concatena itens → UPDATE → Retorna success → 
Fecha modal → Recarrega tabela
```

---

## 📝 Exemplos

### Exemplo 1: Kit Básico

**Cadastro:**
- Nome: "Kit Fotografia Básica"
- Descrição: "Para ensaios simples"
- Itens: "Câmera Canon T7, Tripé Básico"
- Valor: R$ 800,00

**Tabela:**
| Nome | Descrição | Itens | Valor |
|------|-----------|-------|-------|
| Kit Fotografia Básica | Para ensaios simples | Câmera Canon T7, Tripé Básico | R$ 800.00 |

---

### Exemplo 2: Kit Premium

**Cadastro:**
- Nome: "Kit Filmagem Premium"
- Descrição: "Produção profissional"
- Itens: "Sony A7S III, Gimbal DJI RS3, Rode"
- Valor: R$ 15000,00

**Tabela:**
| Nome | Descrição | Itens | Valor |
|------|-----------|-------|-------|
| Kit Filmagem Premium | Produção profissional | Sony A7S III, Gimbal DJI RS3, Rode | R$ 15000.00 |

---

## 🎓 Boas Práticas

✅ Use nomes descritivos e únicos  
✅ Liste TODOS os itens incluídos  
✅ Sempre informe o valor (facilita orçamentos)  
✅ Confirme sempre antes de excluir  
✅ Mantenha backup do banco de dados  

---

## 📞 Suporte

**Logs importantes no console (F12):**
- `📦 openModalKit chamada MODO EDIÇÃO` - Modal aberto
- `🔑 ID capturado: 8 | Modo: EDIÇÃO` - ID detectado
- `✏️ Atualizando kit...` - PUT iniciado
- `✅ Kit atualizado com sucesso` - Operação OK

**Em caso de erro:**
1. Verifique console (F12)
2. Procure logs com 📦, ✏️, 🔑, ❌
3. Revise "Problemas Comuns"
4. Confirme Railway online

---

**Última Atualização:** 20/01/2026  
**Versão:** 1.0  
**Status:** ✅ PRODUÇÃO  
**Desenvolvido por:** Sistema Financeiro DWM
