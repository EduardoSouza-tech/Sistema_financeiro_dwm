# 📚 Guia para Preservar Histórico do Chat no VS Code

## 🎯 Problema
Perda de histórico de conversas do GitHub Copilot Chat no VS Code.

## ✅ Soluções Implementadas

### 1. Configurações do Workspace
As seguintes configurações foram adicionadas ao `.vscode/settings.json`:

```json
{
    "github.copilot.chat.history.maximumNumberOfMessages": 1000,
    "github.copilot.chat.history.enabled": true,
    "github.copilot.chat.persistHistory": true,
    "workbench.localHistory.enabled": true,
    "workbench.localHistory.maxFileSize": 4096,
    "workbench.localHistory.maxFileEntries": 100
}
```

### 2. Configurações Globais do VS Code

Para aplicar essas configurações em todos os seus projetos:

1. Pressione `Ctrl + Shift + P`
2. Digite "Preferences: Open User Settings (JSON)"
3. Adicione as mesmas configurações acima

### 3. Localização do Histórico

O histórico do Copilot Chat é armazenado em:
```
Windows: %APPDATA%\Code\User\globalStorage\github.copilot-chat
```

## 🔧 Dicas Adicionais

### Exportar Conversas Importantes
Para salvar conversas importantes manualmente:

1. **Durante a conversa:**
   - Clique nos três pontos (...) no canto superior direito do painel de chat
   - Selecione "Export Chat"
   - Salve como arquivo `.md` ou `.txt`

2. **Copiar para arquivo:**
   - Selecione o conteúdo da conversa
   - Copie e cole em um arquivo `.md` na pasta `docs/` do projeto

### Backup Automático com Git

Crie uma pasta para históricos:
```bash
mkdir -p docs/chat_history
```

Salve conversas importantes:
```bash
docs/chat_history/
  ├── 2026-01-22_implementacao_feature_x.md
  ├── 2026-01-20_correcao_bugs.md
  └── 2026-01-15_analise_performance.md
```

### Aumentar Limite de Histórico

Se ainda estiver perdendo histórico, aumente os limites:

```json
{
    "github.copilot.chat.history.maximumNumberOfMessages": 2000,
    "workbench.localHistory.maxFileEntries": 200
}
```

## 📝 Melhores Práticas

### 1. Documentar Decisões Importantes
Após conversas importantes, crie documentação:
```markdown
# Decisão: Nome da Feature
Data: 2026-01-22
Contexto: [Resumo da discussão]
Decisão: [O que foi decidido]
Implementação: [Como foi implementado]
```

### 2. Usar Issues/Tickets
Para decisões de arquitetura ou features grandes:
- Crie issues no seu sistema de gestão
- Documente as decisões do chat lá
- Mantenha histórico versionado

### 3. Commits Descritivos
Use mensagens de commit detalhadas:
```
feat: implementar autenticação multi-tenant

Baseado na discussão do chat sobre arquitetura multi-tenant:
- Adicionar suporte para múltiplas empresas por usuário
- Implementar contexto de empresa ativa
- Adicionar validações de acesso por empresa
```

### 4. Criar ADRs (Architecture Decision Records)
Para decisões arquiteturais:
```
docs/adr/
  ├── 001-escolha-postgresql.md
  ├── 002-arquitetura-multi-tenant.md
  └── 003-sistema-permissoes.md
```

## 🛠️ Troubleshooting

### Histórico não está sendo salvo?

1. **Verificar extensão do Copilot:**
   ```
   Ctrl + Shift + X → buscar "GitHub Copilot"
   Verificar se está atualizada
   ```

2. **Recarregar VS Code:**
   ```
   Ctrl + Shift + P → "Developer: Reload Window"
   ```

3. **Limpar cache (último recurso):**
   ```powershell
   # Fechar VS Code primeiro
   Remove-Item -Path "$env:APPDATA\Code\Cache" -Recurse -Force
   Remove-Item -Path "$env:APPDATA\Code\CachedData" -Recurse -Force
   ```

4. **Verificar espaço em disco:**
   - O VS Code precisa de espaço livre para armazenar histórico
   - Verifique se há pelo menos 1GB livre

### Histórico corrompido?

Se o histórico parecer corrompido:
```powershell
# Backup do histórico atual
Copy-Item -Path "$env:APPDATA\Code\User\globalStorage\github.copilot-chat" `
          -Destination "$env:APPDATA\Code\User\globalStorage\github.copilot-chat.backup" `
          -Recurse

# Limpar histórico
Remove-Item -Path "$env:APPDATA\Code\User\globalStorage\github.copilot-chat" -Recurse -Force
```

## 📊 Monitoramento

### Verificar tamanho do histórico:
```powershell
# Ver tamanho da pasta de histórico
Get-ChildItem "$env:APPDATA\Code\User\globalStorage\github.copilot-chat" -Recurse | 
    Measure-Object -Property Length -Sum | 
    Select-Object @{Name="SizeMB";Expression={$_.Sum / 1MB}}
```

## 🎓 Resumo

**O que foi configurado:**
✅ Histórico de chat aumentado para 1000 mensagens
✅ Persistência de histórico habilitada
✅ Histórico local de arquivos habilitado

**O que você deve fazer:**
📝 Exportar conversas importantes manualmente
📁 Criar documentação para decisões críticas
🔄 Fazer backup regular de históricos importantes
📊 Monitorar periodicamente o tamanho do histórico

## 🆘 Suporte

Se o problema persistir:
1. Verificar atualizações do VS Code
2. Verificar atualizações da extensão GitHub Copilot
3. Reportar issue no repositório do Copilot
4. Considerar usar o chat através do GitHub.com como alternativa

---
**Última atualização:** 22/01/2026
