# 📥 Documentação: Importação de Categorias Entre Empresas

**Data:** 01/02/2026  
**Versão:** 1.0  
**Status:** ✅ Implementado e Funcionando

---

## 📋 Sumário

1. [Visão Geral](#visão-geral)
2. [Funcionalidades](#funcionalidades)
3. [Como Usar](#como-usar)
4. [Arquitetura Técnica](#arquitetura-técnica)
5. [Problema Resolvido](#problema-resolvido)
6. [Arquivos Modificados](#arquivos-modificados)
7. [Testes](#testes)

---

## 🎯 Visão Geral

Funcionalidade que permite aos usuários **importar categorias e subcategorias** de uma empresa para outra dentro do sistema multi-tenant. Elimina a necessidade de recadastrar manualmente as mesmas categorias quando o usuário tem acesso a múltiplas empresas.

### Benefícios

- ⚡ **Economia de tempo**: Importação em lote com um clique
- 🔄 **Consistência**: Mantém os mesmos nomes e estruturas
- 🎯 **Multi-tenant**: Respeita isolamento entre empresas
- 🛡️ **Seguro**: Verifica permissões e evita duplicatas

---

## 🚀 Funcionalidades

### 1. Listagem de Empresas Disponíveis

- Mostra apenas empresas que o usuário tem acesso
- Exclui a empresa atual (destino)
- Lista apenas empresas com categorias cadastradas
- Preview de categorias e subcategorias

### 2. Importação em Lote

- Importa **todas** as categorias de uma empresa de uma vez
- Copia nome, tipo, subcategorias, cor, ícone e descrição
- Vincula automaticamente à empresa destino
- Controle de duplicatas (case insensitive)

### 3. Relatório Detalhado

Após importação, exibe:
- ✅ Quantidade de categorias importadas
- ⏭️ Quantidade de categorias duplicadas (ignoradas)
- ❌ Erros (se houver)

---

## 📖 Como Usar

### Passo 1: Acessar Categorias

1. Faça login no sistema
2. Selecione a **empresa destino** no seletor de empresas
3. Acesse o menu **Cadastros** → **Categorias**

### Passo 2: Importar

1. Clique no botão **"📥 Importar de Outra Empresa"**
2. Um modal será exibido mostrando empresas disponíveis
3. Clique em **"Ver categorias"** para expandir a lista (opcional)
4. Clique em **"📥 Importar Todas"** na empresa desejada
5. Confirme a importação

### Passo 3: Verificar

- As categorias aparecerão automaticamente na lista
- Um alerta de sucesso mostrará o resultado da importação
- A página recarrega as categorias automaticamente

---

## 🏗️ Arquitetura Técnica

### Backend (Flask)

#### Endpoint 1: Listar Empresas Disponíveis

```python
GET /api/categorias/empresas-disponiveis
```

**Autenticação:** Bearer Token  
**Permissão:** `categorias_view`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "empresa_id": 18,
      "razao_social": "CONSERVADORA NEVES ALCANTARA LTDA",
      "total_categorias": 3,
      "categorias": [
        {
          "nome": "DESPESAS COM TERCEIROS",
          "tipo": "despesa",
          "subcategorias": []
        },
        {
          "nome": "PRESTACAO DE SERVIÇOS",
          "tipo": "receita",
          "subcategorias": ["Consultoria", "Treinamento"]
        }
      ]
    }
  ]
}
```

#### Endpoint 2: Importar Categorias

```python
POST /api/categorias/importar-de-empresa
```

**Autenticação:** Bearer Token  
**Permissão:** `categorias_create`

**Request Body:**
```json
{
  "empresa_origem_id": 18
}
```

**Response:**
```json
{
  "success": true,
  "importadas": 3,
  "duplicadas": 0,
  "erros": [],
  "message": "3 categoria(s) importada(s) com sucesso"
}
```

### Frontend (HTML/JavaScript)

**Modal HTML:**
- Localização: `templates/interface_nova.html` (linha ~7750)
- Estilo: Modal centralizado com fundo semi-transparente
- Lista de empresas com preview expandível

**Funções JavaScript:**

1. `abrirModalImportarCategorias()`: Abre modal e carrega empresas
2. `importarCategoriasDeEmpresa()`: Executa importação
3. `fecharModalImportarCategorias()`: Fecha modal

---

## 🐛 Problema Resolvido

### Problema Original

O banco de dados tinha uma **constraint UNIQUE no campo `nome`** da tabela `categorias`:

```sql
CONSTRAINT categorias_nome_key UNIQUE (nome)
```

Isso impedia que empresas diferentes tivessem categorias com o mesmo nome, quebrando o conceito de multi-tenancy.

**Erro:**
```
psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint "categorias_nome_key"
DETAIL: Key (nome)=(DESPESAS COM TERCEIROS) already exists.
```

### Solução Aplicada

**1. Script SQL** (`fix_categorias_unique_constraint.sql`):
```sql
-- Remover constraint antiga
ALTER TABLE categorias DROP CONSTRAINT IF EXISTS categorias_nome_key;

-- Adicionar constraint composta (nome + empresa_id)
ALTER TABLE categorias 
ADD CONSTRAINT categorias_nome_empresa_unique 
UNIQUE (nome, empresa_id);
```

**2. Script Python** (`executar_fix_categorias.py`):
- Conecta no Railway PostgreSQL
- Executa os comandos ALTER TABLE
- Verifica se a correção foi aplicada

**3. Executável** (`EXECUTAR_FIX_CATEGORIAS.bat`):
- Interface simples para executar a correção
- Compatível com ambiente Windows

### Resultado

✅ Agora cada empresa pode ter suas próprias categorias com nomes iguais  
✅ Multi-tenancy respeitado  
✅ Importação funciona perfeitamente

---

## 📁 Arquivos Modificados

### Backend

| Arquivo | Linhas | Descrição |
|---------|--------|-----------|
| `web_server.py` | 2268-2340 | Endpoint GET empresas-disponiveis |
| `web_server.py` | 2343-2450 | Endpoint POST importar-de-empresa |

### Frontend

| Arquivo | Linhas | Descrição |
|---------|--------|-----------|
| `interface_nova.html` | 3033-3038 | Botão de importação |
| `interface_nova.html` | 7750-7900 | Modal e JavaScript |

### Database

| Arquivo | Descrição |
|---------|-----------|
| `fix_categorias_unique_constraint.sql` | Script SQL de correção |
| `executar_fix_categorias.py` | Script Python para aplicar correção |
| `EXECUTAR_FIX_CATEGORIAS.bat` | Executável Windows |

### Commits

```
cbf309f - feat: Adicionar importação de categorias entre empresas
507c2c9 - fix: Remover dependência de getCookie e adicionar fallback para Swal
405757a - debug: Adicionar logs detalhados para importação de categorias
e300dda - Revert "fix: Importar classe Categoria e adicionar logs detalhados"
ed714f0 - fix: Corrigir importação de categorias com getattr e case insensitive
16e1831 - fix: Remover código duplicado que causava IndentationError
cf153ec - debug: Adicionar logs extensivos para rastrear importação de categorias
6317875 - fix: Adicionar scripts para corrigir constraint UNIQUE de categorias
```

---

## ✅ Testes

### Cenário 1: Importação Bem-Sucedida

**Pré-condições:**
- Usuário com acesso a 2 empresas
- Empresa origem tem 3 categorias
- Empresa destino tem 0 categorias

**Passos:**
1. Selecionar empresa destino (ID: 20)
2. Abrir modal de importação
3. Importar categorias da empresa origem (ID: 18)

**Resultado Esperado:**
- ✅ 3 categorias importadas
- ✅ 0 duplicadas
- ✅ 0 erros

**Logs:**
```
📥 IMPORTAR CATEGORIAS - INÍCIO
🏢 Empresa origem: 18
🎯 Empresa destino: 20
📦 Categorias da origem: 3
   - DESPESAS COM TERCEIROS (despesa)
   - PRESTACAO DE SERVIÇOS (receita)
   - RECEITAS BANCARIAS (receita)
📋 Categorias no destino: 0 (set())
🔄 Iniciando loop de importação...
   📌 Processando: DESPESAS COM TERCEIROS
      ✅ Nova categoria - criando...
      ✅ Categoria adicionada com ID: 11
   📌 Processando: PRESTACAO DE SERVIÇOS
      ✅ Nova categoria - criando...
      ✅ Categoria adicionada com ID: 12
   📌 Processando: RECEITAS BANCARIAS
      ✅ Nova categoria - criando...
      ✅ Categoria adicionada com ID: 13
📊 RESULTADO:
   ✅ Importadas: 3
   ⏭️ Duplicadas: 0
   ❌ Erros: 0
```

### Cenário 2: Duplicatas Ignoradas

**Pré-condições:**
- Empresa destino já tem "DESPESAS COM TERCEIROS"
- Empresa origem tem "DESPESAS COM TERCEIROS" + outras

**Resultado Esperado:**
- ✅ Apenas categorias novas importadas
- ⏭️ Duplicatas ignoradas
- ℹ️ Case insensitive ("despesas com terceiros" = "DESPESAS COM TERCEIROS")

### Cenário 3: Sem Permissão

**Pré-condições:**
- Usuário sem permissão `categorias_create`

**Resultado Esperado:**
- ❌ 403 Forbidden
- 🔒 Bloqueio no decorator `@require_permission`

---

## 🔧 Configurações

### Permissões Necessárias

- **Visualizar modal**: `categorias_view`
- **Executar importação**: `categorias_create`

### Validações

1. ✅ Usuário autenticado (Bearer Token)
2. ✅ Empresa destino definida na sessão
3. ✅ Usuário tem acesso à empresa origem
4. ✅ Verificação case insensitive de duplicatas
5. ✅ Tratamento de erros individual por categoria

---

## 📊 Logs e Debugging

### Logs Disponíveis

```python
# Endpoint listar empresas
print(f"🔍 [IMPORTAR CATEGORIAS] Buscando empresas disponíveis")
print(f"   👤 Usuário: {usuario.get('nome')}")
print(f"   🏢 Empresa atual: {empresa_atual_id}")
print(f"   📊 Total de empresas do usuário: {len(empresas)}")

# Endpoint importar
print(f"📥 IMPORTAR CATEGORIAS - INÍCIO")
print(f"🏢 Empresa origem: {empresa_origem_id}")
print(f"🎯 Empresa destino: {empresa_destino_id}")
print(f"📦 Categorias da origem: {len(categorias_origem)}")
print(f"📋 Categorias no destino: {len(categorias_destino)}")
```

### Como Ativar Logs Detalhados

Os logs já estão ativos por padrão. Para ver no Railway:
1. Acesse Railway Dashboard
2. Selecione seu serviço
3. Vá em "Deployments" → "Logs"
4. Filtre por "IMPORTAR CATEGORIAS"

---

## 🚀 Próximos Passos (Opcional)

### Melhorias Futuras

1. **Importação Seletiva**
   - Permitir selecionar categorias específicas (não apenas todas)
   - Checkboxes no modal

2. **Preview de Conflitos**
   - Mostrar quais categorias serão importadas/ignoradas antes de confirmar

3. **Histórico de Importações**
   - Registrar quando/quem importou categorias
   - Auditoria

4. **Importação de Outras Entidades**
   - Replicar funcionalidade para Clientes, Fornecedores, etc.

---

## 📞 Suporte

**Problemas Conhecidos:**
- Nenhum

**Contato:**
- Sistema Financeiro DWM
- Data de criação: 01/02/2026

---

## 📝 Changelog

### [1.0.0] - 01/02/2026

#### Adicionado
- ✅ Endpoint `/api/categorias/empresas-disponiveis`
- ✅ Endpoint `/api/categorias/importar-de-empresa`
- ✅ Modal de importação na interface
- ✅ Botão "Importar de Outra Empresa"
- ✅ Scripts de correção da constraint UNIQUE

#### Corrigido
- ✅ Constraint `categorias_nome_key` removida
- ✅ Constraint `categorias_nome_empresa_unique` adicionada
- ✅ Erro de IndentationError no código duplicado
- ✅ Dependência de `getCookie` removida
- ✅ Fallback para `alert()` quando Swal não disponível

#### Melhorado
- ✅ Logs detalhados para debugging
- ✅ Verificação case insensitive de duplicatas
- ✅ Tratamento robusto de erros
- ✅ Uso de `getattr()` para atributos opcionais

---

**Documento gerado em:** 01/02/2026 23:35:00  
**Última atualização:** 01/02/2026 23:35:00
