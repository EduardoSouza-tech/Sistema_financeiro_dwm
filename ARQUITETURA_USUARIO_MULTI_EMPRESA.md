# Arquitetura: Usuário Multi-Empresa

## 📋 Visão Geral

Sistema onde **um usuário pode ter acesso a múltiplas empresas**, com controle granular de permissões por empresa.

### Modelo Atual vs Novo Modelo

**ATUAL (1:1):**
```
Usuario → empresa_id → 1 Empresa
```

**NOVO (N:N):**
```
Usuario → usuario_empresas → N Empresas
                ↓
        Permissões por Empresa
```

---

## 🗄️ Estrutura de Banco de Dados

### Nova Tabela: `usuario_empresas`

Relacionamento N:N entre usuários e empresas com permissões específicas.

```sql
CREATE TABLE usuario_empresas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    
    -- Papel do usuário nesta empresa específica
    papel VARCHAR(50) DEFAULT 'usuario', -- 'admin_empresa', 'usuario', 'visualizador'
    
    -- Permissões específicas nesta empresa (JSON array)
    permissoes_empresa JSONB DEFAULT '[]',
    
    -- Status do acesso
    ativo BOOLEAN DEFAULT TRUE,
    
    -- Empresa padrão (quando usuário faz login)
    is_empresa_padrao BOOLEAN DEFAULT FALSE,
    
    -- Auditoria
    criado_por INTEGER REFERENCES usuarios(id),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(usuario_id, empresa_id)
);

CREATE INDEX idx_usuario_empresas_usuario ON usuario_empresas(usuario_id);
CREATE INDEX idx_usuario_empresas_empresa ON usuario_empresas(empresa_id);
CREATE INDEX idx_usuario_empresas_ativo ON usuario_empresas(ativo) WHERE ativo = TRUE;
```

### Migração da Tabela `usuarios`

A coluna `empresa_id` se torna **NULLABLE** e será descontinuada gradualmente:

```sql
-- Tornar empresa_id nullable (compatibilidade temporária)
ALTER TABLE usuarios ALTER COLUMN empresa_id DROP NOT NULL;

-- Criar índice para performance
CREATE INDEX idx_usuarios_empresa_id ON usuarios(empresa_id) WHERE empresa_id IS NOT NULL;
```

---

## 🔄 Fluxo de Autenticação

### 1. Login Inicial

```
1. Usuário faz login (username + password)
2. Sistema valida credenciais
3. Sistema busca todas as empresas do usuário:
   SELECT e.* 
   FROM empresas e
   JOIN usuario_empresas ue ON e.id = ue.empresa_id
   WHERE ue.usuario_id = ? AND ue.ativo = TRUE
4. Se múltiplas empresas: Exibe seletor de empresa
5. Se uma empresa: Seleciona automaticamente
6. Armazena empresa_id na sessão
```

### 2. Troca de Empresa (Context Switch)

```
POST /api/auth/switch-empresa
Body: { empresa_id: 18 }

1. Valida se usuário tem acesso à empresa solicitada
2. Atualiza sessão com nova empresa_id
3. Recarrega permissões específicas da empresa
4. Retorna sucesso + dados da nova empresa
```

### 3. Estrutura da Sessão

```python
session = {
    'usuario_id': 5,
    'username': 'matheus',
    'tipo': 'cliente',
    'empresa_id': 18,  # Empresa atualmente selecionada
    'empresas_disponiveis': [1, 18, 25],  # IDs de todas empresas com acesso
    'permissoes': ['lanc_view', 'lanc_create'],  # Permissões na empresa atual
    'papel_empresa': 'admin_empresa'  # Papel na empresa atual
}
```

---

## 🎯 Níveis de Acesso

### 1. Super Admin (tipo='admin')
- Acesso total ao sistema
- Gerencia todas as empresas
- Cria/edita/deleta usuários de qualquer empresa
- **NÃO precisa de registro em usuario_empresas**

### 2. Admin de Empresa (papel='admin_empresa')
- Acesso total à sua(s) empresa(s)
- Gerencia usuários da sua empresa
- Configura permissões de outros usuários da empresa
- Visualiza todos os dados da empresa

### 3. Usuário Regular (papel='usuario')
- Acesso conforme permissões específicas
- Pode ter diferentes permissões em cada empresa
- Exemplo: Admin em Empresa A, apenas visualizador em Empresa B

### 4. Visualizador (papel='visualizador')
- Acesso somente leitura
- Não pode criar/editar/deletar dados
- Útil para contadores, auditores externos

---

## 📊 Interface do Usuário

### 1. Tela de Login

```
┌─────────────────────────────────┐
│  🔐 Login                       │
├─────────────────────────────────┤
│  Username: [________________]  │
│  Password: [________________]  │
│                                 │
│  [        Entrar        ]       │
└─────────────────────────────────┘
```

### 2. Seletor de Empresa (Após Login)

```
┌─────────────────────────────────────────┐
│  🏢 Selecione a Empresa                │
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐ │
│  │ 🏢 DWM Sistemas                   │ │
│  │ Papel: Admin da Empresa           │ │
│  │ [      Acessar      ]             │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ 🏢 Cliente ABC Ltda               │ │
│  │ Papel: Usuário                    │ │
│  │ [      Acessar      ]             │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 3. Barra Superior (Empresa Selecionada)

```
┌──────────────────────────────────────────────────┐
│ 🏢 DWM Sistemas ▼  |  👤 Matheus  |  🚪 Sair   │
└──────────────────────────────────────────────────┘
       ↓
   Dropdown para trocar empresa
   ┌─────────────────────────┐
   │ ✓ DWM Sistemas         │
   │   Cliente ABC Ltda     │
   │   Fornecedor XYZ       │
   └─────────────────────────┘
```

---

## 🛠️ API Endpoints

### Gestão de Empresas do Usuário

#### 1. Listar Empresas Disponíveis
```http
GET /api/auth/minhas-empresas
Response: {
  "empresas": [
    {
      "id": 18,
      "razao_social": "DWM Sistemas",
      "papel": "admin_empresa",
      "is_padrao": true,
      "permissoes": ["lanc_view", "lanc_create", ...]
    }
  ]
}
```

#### 2. Trocar Empresa Atual
```http
POST /api/auth/switch-empresa
Body: { "empresa_id": 18 }
Response: {
  "success": true,
  "empresa": {
    "id": 18,
    "razao_social": "DWM Sistemas",
    "papel": "admin_empresa"
  }
}
```

#### 3. Definir Empresa Padrão
```http
PUT /api/auth/empresa-padrao
Body: { "empresa_id": 18 }
Response: { "success": true }
```

### Gestão de Acessos (Admin)

#### 4. Vincular Usuário à Empresa
```http
POST /api/admin/usuario-empresas
Body: {
  "usuario_id": 5,
  "empresa_id": 18,
  "papel": "usuario",
  "permissoes": ["lanc_view", "lanc_create"]
}
```

#### 5. Atualizar Acesso
```http
PUT /api/admin/usuario-empresas/{id}
Body: {
  "papel": "admin_empresa",
  "permissoes": [...]
}
```

#### 6. Remover Acesso
```http
DELETE /api/admin/usuario-empresas/{id}
```

#### 7. Listar Acessos de um Usuário
```http
GET /api/admin/usuarios/{usuario_id}/empresas
Response: {
  "empresas": [...]
}
```

---

## 🔐 Middleware de Autenticação

### Decorador Atualizado: `@require_auth`

```python
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('session_token')
        
        # Validar token
        usuario = validar_token(token)
        
        # Carregar empresa atual da sessão
        empresa_id = session.get('empresa_id')
        
        # Validar acesso à empresa
        if usuario['tipo'] != 'admin':
            if not tem_acesso_empresa(usuario['id'], empresa_id):
                return jsonify({'error': 'Acesso negado à empresa'}), 403
        
        # Carregar permissões da empresa atual
        if usuario['tipo'] != 'admin':
            permissoes = obter_permissoes_usuario_empresa(
                usuario['id'], 
                empresa_id
            )
            usuario['permissoes'] = permissoes
            usuario['empresa_id'] = empresa_id
        
        request.usuario = usuario
        return f(*args, **kwargs)
    
    return decorated
```

### Nova Função: `tem_acesso_empresa`

```python
def tem_acesso_empresa(usuario_id: int, empresa_id: int) -> bool:
    """Verifica se usuário tem acesso à empresa"""
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM usuario_empresas
        WHERE usuario_id = %s 
        AND empresa_id = %s 
        AND ativo = TRUE
    """, (usuario_id, empresa_id))
    
    result = cursor.fetchone()
    return result['count'] > 0
```

---

## 📦 Migração de Dados

### Script de Migração: `migration_usuario_multi_empresa.py`

```python
def migrar_usuarios_para_multi_empresa(db):
    """
    Migra dados existentes de usuarios.empresa_id 
    para usuario_empresas
    """
    
    print("🔄 Iniciando migração multi-empresa...")
    
    # 1. Criar tabela usuario_empresas
    db.execute("""
        CREATE TABLE IF NOT EXISTS usuario_empresas (...)
    """)
    
    # 2. Migrar dados existentes
    db.execute("""
        INSERT INTO usuario_empresas 
            (usuario_id, empresa_id, papel, is_empresa_padrao, ativo)
        SELECT 
            u.id as usuario_id,
            u.empresa_id,
            CASE 
                WHEN u.tipo = 'admin' THEN 'admin_empresa'
                ELSE 'usuario'
            END as papel,
            TRUE as is_empresa_padrao,
            TRUE as ativo
        FROM usuarios u
        WHERE u.empresa_id IS NOT NULL
        AND u.tipo != 'admin'  -- Super admins não precisam
        ON CONFLICT (usuario_id, empresa_id) DO NOTHING
    """)
    
    # 3. Migrar permissões existentes
    db.execute("""
        UPDATE usuario_empresas ue
        SET permissoes_empresa = (
            SELECT COALESCE(
                json_agg(p.codigo), 
                '[]'::json
            )
            FROM usuario_permissoes up
            JOIN permissoes p ON up.permissao_id = p.id
            WHERE up.usuario_id = ue.usuario_id
        )
    """)
    
    print("✅ Migração concluída!")
```

---

## 🎨 Componentes Frontend

### 1. Seletor de Empresa (React-like)

```javascript
function EmpresaSelector({ empresas, empresaAtual, onSwitch }) {
    return (
        <div className="empresa-selector">
            <button className="empresa-atual">
                🏢 {empresaAtual.razao_social} ▼
            </button>
            
            <div className="empresa-dropdown">
                {empresas.map(emp => (
                    <div 
                        key={emp.id}
                        className={emp.id === empresaAtual.id ? 'active' : ''}
                        onClick={() => onSwitch(emp.id)}
                    >
                        <span className="empresa-nome">
                            {emp.razao_social}
                        </span>
                        <span className="empresa-papel">
                            {emp.papel}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}
```

### 2. Modal de Empresas (Plain JS)

```javascript
async function mostrarSeletorEmpresas() {
    const response = await fetch('/api/auth/minhas-empresas');
    const data = await response.json();
    
    if (data.empresas.length === 1) {
        // Seleciona automaticamente
        await selecionarEmpresa(data.empresas[0].id);
    } else {
        // Mostra modal de seleção
        renderizarModalEmpresas(data.empresas);
    }
}

async function selecionarEmpresa(empresaId) {
    const response = await fetch('/api/auth/switch-empresa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ empresa_id: empresaId })
    });
    
    if (response.ok) {
        window.location.href = '/dashboard';
    }
}
```

---

## 📝 Casos de Uso

### Caso 1: Contador com Múltiplos Clientes

```yaml
Usuário: João (contador)
Empresas:
  - Empresa A: papel=visualizador, permissoes=[rel_view]
  - Empresa B: papel=visualizador, permissoes=[rel_view]
  - Empresa C: papel=usuario, permissoes=[rel_view, lanc_view]

Fluxo:
1. João faz login
2. Sistema lista 3 empresas disponíveis
3. João seleciona "Empresa A"
4. Acessa apenas relatórios (visualizador)
5. Troca para "Empresa C" via dropdown
6. Pode visualizar lançamentos (mais permissões)
```

### Caso 2: Empresa com Filiais

```yaml
Usuário: Maria (gerente)
Empresas:
  - Matriz: papel=admin_empresa, permissoes=[TODAS]
  - Filial SP: papel=admin_empresa, permissoes=[TODAS]
  - Filial RJ: papel=usuario, permissoes=[lanc_view, lanc_create]

Fluxo:
1. Maria faz login
2. Empresa padrão: Matriz (is_empresa_padrao=TRUE)
3. Trabalha na Matriz com acesso total
4. Troca para Filial RJ via dropdown
5. Acesso limitado (apenas lançamentos)
```

### Caso 3: Super Admin

```yaml
Usuário: admin (tipo=admin)
Empresas: TODAS (não precisa de usuario_empresas)

Fluxo:
1. Admin faz login
2. Vê todas as empresas no sistema
3. Pode criar/editar/deletar qualquer dado
4. Pode vincular usuários a empresas
5. Não está sujeito a filtros de empresa_id
```

---

## 🔧 Configurações

### Variáveis de Ambiente

```bash
# Habilitar multi-empresa
MULTI_EMPRESA_ENABLED=true

# Forçar seleção de empresa (mesmo com 1 empresa)
FORCE_EMPRESA_SELECTION=false

# Permitir usuário sem empresa (desenvolvimento)
ALLOW_USER_WITHOUT_EMPRESA=false
```

### Configuração no Admin

```python
MULTI_EMPRESA_CONFIG = {
    'enabled': True,
    'max_empresas_por_usuario': 50,
    'require_empresa_padrao': True,
    'auto_select_single_empresa': True,
    'show_empresa_selector': True
}
```

---

## 📊 Relatórios e Analytics

### Dashboard Multi-Empresa

```sql
-- Visão consolidada de múltiplas empresas
SELECT 
    e.razao_social,
    COUNT(l.id) as total_lancamentos,
    SUM(CASE WHEN l.tipo = 'receita' THEN l.valor ELSE 0 END) as total_receitas,
    SUM(CASE WHEN l.tipo = 'despesa' THEN l.valor ELSE 0 END) as total_despesas
FROM empresas e
JOIN usuario_empresas ue ON e.id = ue.empresa_id
LEFT JOIN lancamentos l ON l.proprietario_id = e.id
WHERE ue.usuario_id = :usuario_id
AND ue.ativo = TRUE
GROUP BY e.id, e.razao_social
ORDER BY e.razao_social
```

---

## ✅ Checklist de Implementação

### Fase 1: Banco de Dados
- [ ] Criar tabela `usuario_empresas`
- [ ] Tornar `usuarios.empresa_id` nullable
- [ ] Criar índices de performance
- [ ] Script de migração de dados existentes

### Fase 2: Backend
- [ ] Funções CRUD para `usuario_empresas`
- [ ] Atualizar middleware de autenticação
- [ ] Endpoints de gestão de empresas
- [ ] Endpoint de switch de empresa
- [ ] Atualizar filtros de dados

### Fase 3: Frontend
- [ ] Modal de seleção de empresa (login)
- [ ] Dropdown de troca de empresa (header)
- [ ] Atualizar interface de gestão de usuários
- [ ] Indicador visual de empresa atual
- [ ] Testes de troca de contexto

### Fase 4: Testes
- [ ] Teste de acesso multi-empresa
- [ ] Teste de isolamento de dados
- [ ] Teste de switch de empresa
- [ ] Teste de permissões por empresa
- [ ] Teste de usuário sem empresa

### Fase 5: Documentação
- [ ] Atualizar README
- [ ] Documentar API de multi-empresa
- [ ] Criar guia de migração
- [ ] Vídeo tutorial para usuários

---

## 🚀 Roadmap Futuro

### v2.0 - Multi-Empresa
- ✅ Relacionamento N:N usuário-empresa
- ✅ Seletor de empresa no login
- ✅ Permissões por empresa

### v2.1 - Recursos Avançados
- [ ] Grupos de empresas (holdings)
- [ ] Relatórios consolidados multi-empresa
- [ ] Hierarquia de empresas (matriz/filiais)
- [ ] Compartilhamento de recursos entre empresas

### v2.2 - White Label
- [ ] Branding por empresa
- [ ] Domínios personalizados
- [ ] Configurações visuais por empresa

---

## 📞 Suporte

Para dúvidas sobre multi-empresa:
- Documentação: `/docs/multi-empresa`
- Email: suporte@dwmsistemas.com
- Issues: GitHub Issues

---

**Versão:** 1.0  
**Data:** Janeiro 2026  
**Autor:** Sistema DWM  
**Status:** 🚧 Em Implementação
