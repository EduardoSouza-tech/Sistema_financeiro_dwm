# 🔒 REGRAS DE SEGURANÇA OBRIGATÓRIAS - ISOLAMENTO DE EMPRESAS

## ⚠️ LEIA ISTO ANTES DE ESCREVER QUALQUER CÓDIGO

Este documento define **regras de segurança OBRIGATÓRIAS** que **NUNCA** podem ser ignoradas.  
Violações comprometem a segurança do sistema e permitem vazamento de dados entre empresas.

---

## 🚨 REGRA #1: EMPRESA_ID É SEMPRE OBRIGATÓRIO

### ✅ O QUE FAZER:

**TODA função que acessa dados de empresa DEVE:**

1. **Receber `empresa_id` como parâmetro obrigatório**
2. **Passar `empresa_id` explicitamente para `get_db_connection()`**
3. **Validar que `empresa_id` não é None**
4. **Usar decorator `@require_empresa` quando apropriado**

### ❌ PROIBIDO:

```python
# ❌ NUNCA FAÇA ISSO - Depende de sessão implícita
def listar_clientes():
    with get_db_connection() as conn:
        cursor.execute("SELECT * FROM clientes")

# ❌ NUNCA FAÇA ISSO - empresa_id opcional
def listar_clientes(empresa_id=None):
    with get_db_connection(empresa_id) as conn:
        cursor.execute("SELECT * FROM clientes")
```

### ✅ CORRETO:

```python
# ✅ CORRETO - empresa_id obrigatório e explícito
@require_empresa
def listar_clientes(empresa_id: int, ativos: bool = True):
    """
    Lista clientes da empresa
    
    Args:
        empresa_id (int): ID da empresa - OBRIGATÓRIO
        ativos (bool): Filtrar apenas ativos
        
    Raises:
        ValueError: Se empresa_id não fornecido
    """
    if not empresa_id:
        raise ValueError("❌ SEGURANÇA: empresa_id é obrigatório")
    
    with get_db_connection(empresa_id) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE ativo = %s", (ativos,))
        return cursor.fetchall()
```

---

## 🚨 REGRA #2: SEMPRE VALIDAR EMPRESA_ID

### Checklist Obrigatório:

```python
def minha_funcao(empresa_id: int, outros_params):
    # ✅ 1. VALIDAR no início da função
    if not empresa_id:
        raise ValueError("❌ SEGURANÇA: empresa_id é obrigatório")
    
    if not isinstance(empresa_id, int):
        raise TypeError(f"❌ SEGURANÇA: empresa_id deve ser int, recebeu {type(empresa_id)}")
    
    # ✅ 2. PASSAR explicitamente para get_db_connection
    with get_db_connection(empresa_id) as conn:
        cursor = conn.cursor()
        
        # ✅ 3. NUNCA confiar apenas em WHERE - RLS protege
        cursor.execute("SELECT * FROM tabela WHERE empresa_id = %s", (empresa_id,))
```

---

## 🚨 REGRA #3: DOCUMENTAR SEMPRE

### Template Obrigatório de Docstring:

```python
def minha_funcao(empresa_id: int, param1, param2):
    """
    Descrição breve da função
    
    Args:
        empresa_id (int): ⚠️ OBRIGATÓRIO - ID da empresa para isolamento de dados
        param1: Descrição do param1
        param2: Descrição do param2
        
    Returns:
        Tipo: Descrição do retorno
        
    Raises:
        ValueError: Se empresa_id não fornecido ou inválido
        
    Security:
        🔒 Row Level Security ativo - dados filtrados por empresa_id
        
    Example:
        >>> resultado = minha_funcao(empresa_id=18, param1="teste")
    """
```

---

## 🚨 REGRA #4: NUNCA CONFIAR APENAS EM WHERE CLAUSE

### ❌ INSEGURO (Depende apenas do WHERE):

```python
# ❌ Se esquecer WHERE, vaza TODOS os dados
cursor.execute("SELECT * FROM clientes WHERE empresa_id = %s", (empresa_id,))
```

### ✅ SEGURO (RLS + WHERE = Defesa em Profundidade):

```python
# ✅ RLS ativo no banco + WHERE no código = 2 camadas
with get_db_connection(empresa_id) as conn:  # RLS ativo
    cursor = conn.cursor()
    # Mesmo que WHERE falhe, RLS protege
    cursor.execute("SELECT * FROM clientes WHERE empresa_id = %s", (empresa_id,))
```

---

## 🚨 REGRA #5: ENDPOINTS DA API

### ✅ Obter empresa_id da Sessão:

```python
from flask import session, jsonify

@app.route('/api/clientes', methods=['GET'])
@login_required
def api_listar_clientes():
    # ✅ Obter empresa_id da sessão validada
    empresa_id = session.get('empresa_id')
    
    # ✅ Validar SEMPRE
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    # ✅ Passar explicitamente
    try:
        clientes = listar_clientes(empresa_id=empresa_id)
        return jsonify({'clientes': clientes})
    except Exception as e:
        log(f"❌ Erro ao listar clientes empresa {empresa_id}: {e}")
        return jsonify({'erro': 'Erro interno'}), 500
```

---

## 🚨 REGRA #6: TESTES DEVEM PASSAR EMPRESA_ID

### ✅ Testes Corretos:

```python
def test_listar_clientes():
    # ✅ Sempre criar empresa de teste
    empresa_id = criar_empresa_teste()
    
    # ✅ Passar empresa_id explicitamente
    clientes = listar_clientes(empresa_id=empresa_id)
    
    assert len(clientes) > 0
    
    # ✅ Limpar dados de teste
    excluir_empresa_teste(empresa_id)

def test_isolamento_empresas():
    # ✅ Testar isolamento entre empresas
    empresa1 = criar_empresa_teste()
    empresa2 = criar_empresa_teste()
    
    criar_cliente(empresa_id=empresa1, nome="Cliente 1")
    criar_cliente(empresa_id=empresa2, nome="Cliente 2")
    
    clientes_emp1 = listar_clientes(empresa_id=empresa1)
    clientes_emp2 = listar_clientes(empresa_id=empresa2)
    
    # ✅ Garantir isolamento
    assert len(clientes_emp1) == 1
    assert len(clientes_emp2) == 1
    assert clientes_emp1[0]['nome'] != clientes_emp2[0]['nome']
```

---

## 🚨 REGRA #7: SCRIPTS E JOBS

### ✅ Scripts CLI Corretos:

```python
# script_backup.py
import sys

def fazer_backup(empresa_id: int):
    if not empresa_id:
        raise ValueError("❌ empresa_id obrigatório")
    
    with get_db_connection(empresa_id) as conn:
        # Fazer backup...
        pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("❌ Uso: python script_backup.py <empresa_id>")
        sys.exit(1)
    
    empresa_id = int(sys.argv[1])
    fazer_backup(empresa_id)
```

---

## 🚨 REGRA #8: TABELAS GLOBAIS VS ISOLADAS

### Tabelas que NÃO precisam de empresa_id:

```python
# ✅ Tabelas globais (sem empresa_id)
TABELAS_GLOBAIS = [
    'usuarios',           # Usuários podem ter múltiplas empresas
    'empresas',           # Cadastro de empresas
    'permissoes',         # Permissões globais
    'usuario_empresas',   # Vínculo usuário-empresa
    'sessoes_login',      # Sessões de autenticação
]

# Funções para tabelas globais NÃO precisam de empresa_id
def obter_usuario(usuario_id: int):
    with get_db_connection() as conn:  # ✅ OK sem empresa_id
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
```

### Tabelas que SEMPRE precisam de empresa_id:

```python
# ⚠️ Tabelas isoladas (COM empresa_id)
TABELAS_ISOLADAS = [
    'lancamentos',
    'categorias',
    'clientes',
    'fornecedores',
    'contas',
    'contratos',
    'eventos',
    'funcionarios',
    'folha_pagamento',
    'equipamentos',
    'kits_equipamentos',
    'produtos',
    'movimentacoes_estoque',
    'transacoes_extrato',
]

# ⚠️ Funções para estas tabelas SEMPRE precisam empresa_id
def listar_lancamentos(empresa_id: int, mes: int, ano: int):
    if not empresa_id:
        raise ValueError("❌ empresa_id obrigatório")
    # ...
```

---

## 🚨 REGRA #9: CODE REVIEW CHECKLIST

### Antes de Commitar, Verificar:

- [ ] Toda função que acessa dados de empresa recebe `empresa_id`?
- [ ] `empresa_id` é parâmetro obrigatório (não opcional)?
- [ ] Validação de `empresa_id` no início da função?
- [ ] `get_db_connection(empresa_id)` com parâmetro explícito?
- [ ] Docstring documenta empresa_id como obrigatório?
- [ ] Endpoint de API obtém empresa_id da sessão?
- [ ] Testes passam empresa_id explicitamente?
- [ ] Logs incluem empresa_id para auditoria?

---

## 🚨 REGRA #10: TRATAMENTO DE ERROS

### ✅ Sempre Logar empresa_id:

```python
try:
    resultado = processar_dados(empresa_id=empresa_id)
except Exception as e:
    # ✅ Log com empresa_id para auditoria
    log(f"❌ Erro ao processar dados - Empresa: {empresa_id} - Erro: {e}")
    raise

# ✅ Log de sucesso também com empresa_id
log(f"✅ Dados processados - Empresa: {empresa_id} - Registros: {len(resultado)}")
```

---

## 📋 TEMPLATE DE FUNÇÃO SEGURA

### Copy/Paste Este Template:

```python
@require_empresa
def nome_da_funcao(empresa_id: int, param1, param2=None):
    """
    Descrição da função
    
    Args:
        empresa_id (int): ⚠️ OBRIGATÓRIO - ID da empresa
        param1: Descrição
        param2: Descrição (opcional)
        
    Returns:
        tipo: Descrição
        
    Raises:
        ValueError: Se empresa_id inválido
        
    Security:
        🔒 RLS ativo - dados filtrados por empresa_id
    """
    # ✅ 1. VALIDAR empresa_id
    if not empresa_id:
        raise ValueError("❌ SEGURANÇA: empresa_id é obrigatório")
    
    if not isinstance(empresa_id, int) or empresa_id <= 0:
        raise ValueError(f"❌ SEGURANÇA: empresa_id inválido: {empresa_id}")
    
    try:
        # ✅ 2. CONECTAR com empresa_id explícito
        with get_db_connection(empresa_id) as conn:
            cursor = conn.cursor()
            
            # ✅ 3. EXECUTAR query (RLS ativo automaticamente)
            cursor.execute("""
                SELECT * FROM tabela 
                WHERE condicao = %s
            """, (param1,))
            
            resultado = cursor.fetchall()
            
            # ✅ 4. LOGAR operação
            log(f"✅ Função executada - Empresa: {empresa_id} - Resultados: {len(resultado)}")
            
            return resultado
            
    except Exception as e:
        # ✅ 5. LOGAR erro com empresa_id
        log(f"❌ Erro na função - Empresa: {empresa_id} - Erro: {e}")
        raise
```

---

## 🔍 COMO VERIFICAR SEGURANÇA

### Script de Verificação:

```bash
# Procurar funções sem empresa_id
grep -n "def.*get_db_connection()" *.py | grep -v "empresa_id"

# Procurar conexões sem parâmetro
grep -n "get_db_connection()" *.py | grep -v "empresa_id"
```

### Teste de Isolamento:

```python
def testar_isolamento():
    """Testa se empresas estão isoladas"""
    empresa1 = 1
    empresa2 = 18
    
    # Criar dados em empresa 1
    criar_cliente(empresa_id=empresa1, nome="Cliente Empresa 1")
    
    # Criar dados em empresa 2
    criar_cliente(empresa_id=empresa2, nome="Cliente Empresa 2")
    
    # Buscar dados de empresa 1
    clientes1 = listar_clientes(empresa_id=empresa1)
    
    # Buscar dados de empresa 2
    clientes2 = listar_clientes(empresa_id=empresa2)
    
    # Verificar isolamento
    assert "Cliente Empresa 2" not in [c['nome'] for c in clientes1]
    assert "Cliente Empresa 1" not in [c['nome'] for c in clientes2]
    
    print("✅ TESTE DE ISOLAMENTO: PASSOU")
```

---

## ⚠️ VIOLAÇÕES COMUNS E COMO CORRIGIR

### Violação #1: Parâmetro Opcional

```python
# ❌ ERRADO
def listar_clientes(empresa_id=None):
    pass

# ✅ CORRETO
def listar_clientes(empresa_id: int):
    if not empresa_id:
        raise ValueError("empresa_id obrigatório")
```

### Violação #2: Não Validar

```python
# ❌ ERRADO
def listar_clientes(empresa_id):
    with get_db_connection(empresa_id) as conn:
        pass

# ✅ CORRETO
def listar_clientes(empresa_id: int):
    if not empresa_id or not isinstance(empresa_id, int):
        raise ValueError("empresa_id inválido")
    with get_db_connection(empresa_id) as conn:
        pass
```

### Violação #3: Confiar na Sessão

```python
# ❌ ERRADO
def listar_clientes():
    empresa_id = session.get('empresa_id')  # Pode ser None!
    with get_db_connection() as conn:
        pass

# ✅ CORRETO
def listar_clientes(empresa_id: int):
    if not empresa_id:
        raise ValueError("empresa_id obrigatório")
    with get_db_connection(empresa_id) as conn:
        pass

# No endpoint:
@app.route('/clientes')
def endpoint():
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    return jsonify(listar_clientes(empresa_id))
```

---

## 🎓 TREINAMENTO OBRIGATÓRIO

### Novos Desenvolvedores DEVEM:

1. ✅ Ler este documento completo
2. ✅ Executar teste de isolamento
3. ✅ Revisar código existente
4. ✅ Implementar função de exemplo seguindo template
5. ✅ Passar no code review de segurança

---

## 📞 DÚVIDAS?

### Não tem certeza se precisa de empresa_id?

**PERGUNTE:**
- Esta tabela tem coluna `empresa_id`? → SIM: Precisa
- Esta função acessa dados de cliente/empresa? → SIM: Precisa
- Esta tabela está em `TABELAS_ISOLADAS`? → SIM: Precisa
- **Na dúvida? → Sempre use empresa_id**

---

## 🚨 PENALIDADES

### Violações de Segurança:

**NUNCA são aceitáveis porque:**
- ❌ Comprometem privacidade do cliente
- ❌ Violam LGPD
- ❌ Causam perda de confiança
- ❌ Podem resultar em processos judiciais

**Se encontrar violação:**
1. Parar deploy imediatamente
2. Corrigir código
3. Testar isolamento
4. Documentar incidente
5. Revisar código relacionado

---

## ✅ CHECKLIST FINAL

Antes de fazer commit:

- [ ] Todas as funções de dados têm `empresa_id` obrigatório?
- [ ] Validação de `empresa_id` em todas as funções?
- [ ] `get_db_connection(empresa_id)` com parâmetro explícito?
- [ ] Docstrings documentam empresa_id?
- [ ] Logs incluem empresa_id?
- [ ] Testes verificam isolamento?
- [ ] Code review aprovado?

**Apenas commite se TODOS os itens estiverem ✅**

---

**Documento de Segurança v1.0**  
**Criado**: 30 de Janeiro de 2026  
**Status**: OBRIGATÓRIO - NÃO IGNORAR  
**Próxima Revisão**: Mensal
