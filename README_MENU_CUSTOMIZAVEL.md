# 📋 Menu Customizável - Documentação

## 🎯 Visão Geral

O Sistema Financeiro agora possui um recurso de **menu customizável** que permite aos usuários reordenar os itens do menu lateral de acordo com suas preferências pessoais. A ordenação é salva automaticamente e persiste entre sessões.

## ✨ Funcionalidades

### Drag and Drop
- **Arrastar**: Clique e segure em qualquer item do menu (Dashboard, Financeiro, Relatórios, Cadastros, Operacional)
- **Reordenar**: Arraste o item para a posição desejada
- **Soltar**: Solte o item na nova posição
- **Salvar Automático**: A nova ordem é salva automaticamente no servidor

### Visual Feedback
- **Cursor grab**: O cursor muda para indicar que o item pode ser arrastado
- **Indicador visual**: Ícone `⋮⋮` à esquerda de cada item indica que é arrastável
- **Destaque durante drag**: Item em movimento fica semi-transparente
- **Drop zone highlight**: O local onde o item será solto fica destacado em verde
- **Notificação**: Toast de sucesso aparece ao reordenar

### Persistência
- A ordem personalizada é salva por usuário
- Sincronização automática entre dispositivos (mesmo login)
- Ordem é restaurada automaticamente ao fazer login

## 🏗️ Arquitetura Técnica

### Backend

#### 1. Tabela de Banco de Dados
```sql
-- Arquivo: migrations/007_user_preferences.sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    preferencia_chave VARCHAR(100) NOT NULL,
    preferencia_valor TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usuario_id, preferencia_chave)
);
```

**Campos:**
- `usuario_id`: ID do usuário dono da preferência
- `preferencia_chave`: Tipo de preferência (ex: 'menu_order', 'theme', 'language')
- `preferencia_valor`: Valor em JSON (ex: `["dashboard","cadastros","financeiro"]`)

#### 2. Funções do Banco (database_postgresql.py)

**`salvar_preferencia_usuario(usuario_id, chave, valor)`**
- Salva ou atualiza preferência do usuário
- Usa `INSERT ... ON CONFLICT UPDATE` (upsert)
- Retorna `bool` indicando sucesso

**`obter_preferencia_usuario(usuario_id, chave, valor_padrao=None)`**
- Obtém preferência específica do usuário
- Retorna valor salvo ou valor_padrao se não existir
- Retorna `Optional[str]`

**`listar_preferencias_usuario(usuario_id)`**
- Lista todas as preferências do usuário
- Retorna `Dict[str, str]` com {chave: valor}

**`deletar_preferencia_usuario(usuario_id, chave)`**
- Remove preferência específica
- Retorna `bool` indicando sucesso

#### 3. Endpoints da API (web_server.py)

**GET `/api/preferencias/menu-order`**
```python
# Request: (autenticado via cookie)
# Response:
{
    "success": true,
    "menu_order": ["dashboard", "financeiro", "relatorios", "cadastros", "operacional"]
}
```
- Retorna ordem atual do menu do usuário
- Se não houver preferência salva, retorna ordem padrão

**POST `/api/preferencias/menu-order`**
```python
# Request Body:
{
    "menu_order": ["dashboard", "cadastros", "financeiro", "relatorios", "operacional"]
}

# Response:
{
    "success": true,
    "message": "Ordem do menu salva com sucesso"
}
```
- Salva nova ordem do menu
- Valida itens permitidos
- Registra log de auditoria

**GET `/api/preferencias`**
```python
# Response:
{
    "success": true,
    "preferencias": {
        "menu_order": ["dashboard", "financeiro", ...],
        "theme": "dark",
        "language": "pt-BR"
    }
}
```
- Lista todas as preferências do usuário
- Parseia valores JSON automaticamente

### Frontend

#### 1. HTML (templates/interface_nova.html)

**Atributos nos Botões:**
```html
<button class="nav-button" 
        onclick="toggleSubmenu('financeiro')" 
        id="btn-financeiro" 
        data-permission="lancamentos_view" 
        draggable="true" 
        data-menu-id="financeiro">
    💰 Financeiro ▼
</button>
```

- `draggable="true"`: Habilita arrastar o elemento
- `data-menu-id`: Identificador único do item do menu

#### 2. CSS

**Estilos Base:**
```css
.nav-button {
    cursor: move;  /* Cursor indica que pode arrastar */
    position: relative;
}

.nav-button::before {
    content: '⋮⋮';  /* Indicador visual de drag */
    position: absolute;
    left: 8px;
    color: rgba(255, 255, 255, 0.3);
}
```

**Estados de Drag:**
```css
.nav-button.dragging {
    opacity: 0.5;
    background: #3498db;
    cursor: grabbing;
}

.nav-button.drag-over {
    background: #27ae60;
    border-top: 3px solid #fff;
    transform: scale(1.05);
}
```

#### 3. JavaScript

**Inicialização:**
```javascript
function initMenuDragAndDrop() {
    loadMenuOrder();  // Carrega ordem salva
    
    const menuButtons = document.querySelectorAll('.nav-button[draggable="true"]');
    menuButtons.forEach(button => {
        button.addEventListener('dragstart', handleDragStart);
        button.addEventListener('dragend', handleDragEnd);
        button.addEventListener('dragover', handleDragOver);
        button.addEventListener('drop', handleDrop);
        button.addEventListener('dragleave', handleDragLeave);
    });
}
```

**Eventos HTML5 Drag & Drop:**

1. **`handleDragStart(e)`**
   - Marca elemento sendo arrastado
   - Adiciona classe `.dragging`
   - Define `dataTransfer`

2. **`handleDragOver(e)`**
   - Permite drop no elemento
   - Adiciona classe `.drag-over` para feedback visual
   - Previne comportamento padrão

3. **`handleDrop(e)`**
   - Reordena elementos no DOM
   - Chama `saveMenuOrder()` para persistir
   - Remove classes de estado

4. **`handleDragEnd(e)`**
   - Limpa classes de estado
   - Remove feedback visual

**Reordenação:**
```javascript
function reorderMenuItems(draggedEl, targetEl) {
    // Remove elemento arrastado do DOM
    draggedEl.remove();
    
    // Pega submenu se existir
    const draggedSubmenu = draggedEl.nextElementSibling;
    if (draggedSubmenu && draggedSubmenu.classList.contains('submenu')) {
        draggedSubmenu.remove();
    }
    
    // Insere na nova posição
    targetEl.before(draggedEl);
    
    // Reinsere submenu logo após
    if (draggedSubmenu) {
        draggedEl.after(draggedSubmenu);
    }
}
```

**Persistência:**
```javascript
async function saveMenuOrder() {
    const menuButtons = document.querySelectorAll('.nav-button[data-menu-id]');
    const menuOrder = Array.from(menuButtons).map(btn => btn.getAttribute('data-menu-id'));
    
    const response = await fetch('/api/preferencias/menu-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ menu_order: menuOrder })
    });
    
    const result = await response.json();
    if (result.success) {
        console.log('✅ Ordem salva');
    }
}
```

## 🔒 Segurança

### Autenticação
- Todos os endpoints requerem autenticação (`@require_auth`)
- Session cookie validado automaticamente
- Cada usuário acessa apenas suas próprias preferências

### Validação
```python
# Validar itens permitidos
itens_validos = ['dashboard', 'financeiro', 'relatorios', 'cadastros', 'operacional']
for item in menu_order:
    if item not in itens_validos:
        return jsonify({'success': False, 'error': f'Item inválido: {item}'}), 400
```

### Auditoria
```python
# Registrar log de alteração
auth_db.registrar_log_acesso(
    usuario_id=usuario_id,
    acao='update_menu_order',
    descricao=f'Ordem do menu atualizada: {menu_order}',
    ip_address=request.remote_addr,
    sucesso=True
)
```

## 📝 Logs e Debug

### Backend
```python
print(f"✅ Preferência '{chave}' salva para usuário {usuario_id}")
print(f"❌ Erro ao salvar preferência: {e}")
```

### Frontend
```javascript
console.log('🎯 Drag iniciado:', draggedMenuId);
console.log('📦 Drop em:', targetMenuId);
console.log('🔄 Reordenando:', draggedEl.getAttribute('data-menu-id'), '→', targetEl.getAttribute('data-menu-id'));
console.log('💾 Salvando ordem do menu:', menuOrder);
console.log('✅ Ordem do menu salva com sucesso');
```

## 🚀 Como Usar

### Para Usuários Finais

1. **Acessar o sistema** e fazer login
2. **Identificar os itens do menu** no sidebar esquerdo (📊 Dashboard, 💰 Financeiro, etc.)
3. **Clicar e segurar** no item que deseja mover
4. **Arrastar** para a nova posição (acima ou abaixo de outro item)
5. **Soltar** o mouse
6. **Verificar** a notificação de sucesso "Menu reordenado! ✨"
7. **Atualizar** a página para confirmar que a ordem foi salva

### Para Desenvolvedores

#### Executar Migration
```bash
# PostgreSQL
psql -h <host> -U <user> -d <database> -f migrations/007_user_preferences.sql

# Railway
# A migration será executada automaticamente no deploy
```

#### Adicionar Novo Item ao Menu
```html
<!-- 1. Adicionar botão com atributos necessários -->
<button class="nav-button" 
        onclick="showSection('novo-item')" 
        data-permission="novo_item_view" 
        draggable="true" 
        data-menu-id="novo-item">
    🆕 Novo Item
</button>
```

```python
# 2. Adicionar à validação no backend (web_server.py)
itens_validos = [
    'dashboard', 'financeiro', 'relatorios', 
    'cadastros', 'operacional', 'novo-item'  # Adicionar aqui
]
```

```javascript
// 3. Incluir na ordem padrão (web_server.py e interface_nova.html)
ordem_padrao = '["dashboard","financeiro","relatorios","cadastros","operacional","novo-item"]'
```

#### Resetar Ordem Padrão
```sql
-- SQL para resetar para todos os usuários
UPDATE user_preferences 
SET preferencia_valor = '["dashboard","financeiro","relatorios","cadastros","operacional"]'
WHERE preferencia_chave = 'menu_order';

-- SQL para resetar para um usuário específico
DELETE FROM user_preferences 
WHERE usuario_id = <ID> AND preferencia_chave = 'menu_order';
```

#### Debugging

**Verificar preferências no banco:**
```sql
SELECT 
    u.username,
    up.preferencia_chave,
    up.preferencia_valor,
    up.updated_at
FROM user_preferences up
JOIN usuarios u ON up.usuario_id = u.id
WHERE up.preferencia_chave = 'menu_order';
```

**Testar endpoint via cURL:**
```bash
# GET - Obter ordem
curl -X GET http://localhost:5000/api/preferencias/menu-order \
  -H "Cookie: session=<token>" \
  -H "Content-Type: application/json"

# POST - Salvar ordem
curl -X POST http://localhost:5000/api/preferencias/menu-order \
  -H "Cookie: session=<token>" \
  -H "Content-Type: application/json" \
  -d '{"menu_order":["cadastros","dashboard","financeiro","relatorios","operacional"]}'
```

## 🐛 Troubleshooting

### Problema: Menu não está arrastável
**Solução:**
1. Verificar se o botão tem `draggable="true"`
2. Verificar se o botão tem `data-menu-id`
3. Verificar console do navegador para erros JavaScript
4. Verificar se `initMenuDragAndDrop()` foi chamado

### Problema: Ordem não está sendo salva
**Solução:**
1. Verificar se usuário está autenticado (cookie válido)
2. Verificar logs do servidor (erros 401, 500)
3. Verificar se tabela `user_preferences` existe
4. Verificar se constraint UNIQUE não está causando conflito

### Problema: Ordem não carrega ao fazer login
**Solução:**
1. Verificar se `loadMenuOrder()` é chamado na inicialização
2. Verificar se função `applyMenuOrder()` está reconstruindo DOM corretamente
3. Verificar se há erros no console do navegador

### Problema: Submenus desaparecem após reordenar
**Solução:**
1. Verificar se `reorderMenuItems()` está movendo tanto o botão quanto o submenu
2. Verificar se os IDs dos submenus seguem padrão `submenu-{menu-id}`
3. Verificar se event listeners são reinicializados após `applyMenuOrder()`

## 🔄 Extensões Futuras

### Possíveis Melhorias
1. **Personalização Visual**: Permitir alterar cores, ícones do menu
2. **Ocultar Itens**: Permitir esconder itens não utilizados
3. **Grupos Customizados**: Criar agrupamentos personalizados de funcionalidades
4. **Favoritos**: Marcar itens favoritos para acesso rápido
5. **Atalhos de Teclado**: Definir teclas de atalho para cada item
6. **Importar/Exportar Configurações**: Compartilhar configurações entre usuários
7. **Presets**: Templates de organização (Contabilista, Gerente, Admin)

### Adição de Novas Preferências
O sistema está preparado para armazenar qualquer tipo de preferência:

```javascript
// Exemplo: Salvar tema escuro
async function saveThemePreference(isDark) {
    await fetch('/api/preferencias', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            chave: 'theme',
            valor: isDark ? 'dark' : 'light'
        })
    });
}
```

## 📄 Arquivos Modificados

### Novos Arquivos
- `migrations/007_user_preferences.sql` - Tabela de preferências
- `README_MENU_CUSTOMIZAVEL.md` - Esta documentação

### Arquivos Modificados
- `database_postgresql.py` - Funções CRUD de preferências
- `web_server.py` - Endpoints da API
- `templates/interface_nova.html` - HTML, CSS e JavaScript do drag-and-drop

## 🎓 Referências

- [HTML5 Drag and Drop API](https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API)
- [PostgreSQL UPSERT (INSERT ON CONFLICT)](https://www.postgresql.org/docs/current/sql-insert.html)
- [Flask Request Context](https://flask.palletsprojects.com/en/2.3.x/reqcontext/)

## ✅ Checklist de Deploy

- [x] Migration SQL criada
- [x] Funções do banco implementadas
- [x] Endpoints da API criados
- [x] Frontend implementado (HTML/CSS/JS)
- [x] Documentação criada
- [ ] Testes locais executados
- [ ] Migration executada no banco de produção
- [ ] Deploy no Railway realizado
- [ ] Testes em produção validados

---

**Desenvolvido para o Sistema Financeiro - 2026**
