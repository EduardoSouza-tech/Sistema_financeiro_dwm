# 🚀 Como Executar a Migration no Railway

## Opção 1: Via Browser (Mais Fácil)

1. Faça login como **admin** no sistema
2. Abra o Console do Navegador (F12)
3. Cole e execute este comando:

```javascript
fetch('https://sistema-financeiro-dwm-production.up.railway.app/api/admin/migrations/evento-funcionarios', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + localStorage.getItem('token')
    }
})
.then(r => r.json())
.then(data => {
    console.log('✅ Migration executada:', data);
    alert('Migration concluída! Tabelas criadas: ' + data.data.tabelas_criadas.join(', '));
})
.catch(err => {
    console.error('❌ Erro:', err);
    alert('Erro ao executar migration: ' + err);
});
```

## Opção 2: Via Curl (Terminal)

```bash
# Primeiro faça login e pegue o token
curl -X POST https://sistema-financeiro-dwm-production.up.railway.app/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","senha":"sua_senha"}'

# Copie o token retornado e execute:
curl -X POST https://sistema-financeiro-dwm-production.up.railway.app/api/admin/migrations/evento-funcionarios \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## Opção 3: Via PowerShell

```powershell
# Login
$login = Invoke-RestMethod -Uri "https://sistema-financeiro-dwm-production.up.railway.app/api/login" `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{username="admin"; senha="sua_senha"} | ConvertTo-Json)

# Executar migration
$result = Invoke-RestMethod -Uri "https://sistema-financeiro-dwm-production.up.railway.app/api/admin/migrations/evento-funcionarios" `
    -Method Post `
    -ContentType "application/json" `
    -Headers @{Authorization="Bearer $($login.token)"}

Write-Host "✅ Migration executada com sucesso!"
Write-Host "Tabelas criadas: $($result.data.tabelas_criadas -join ', ')"
Write-Host "Funções inseridas: $($result.data.funcoes_inseridas)"
```

## O que Acontece

A migration irá:

1. ✅ Criar tabela `funcoes_evento`
2. ✅ Criar tabela `evento_funcionarios`
3. ✅ Inserir 11 funções padrão:
   - Motorista
   - Fotógrafo
   - Assistente de Fotografia
   - Cinegrafista
   - Editor de Vídeo
   - Editor de Fotos
   - Operador de Drone
   - Iluminador
   - Sonoplasta
   - Coordenador de Evento
   - Assistente Geral

4. ✅ Criar índices para performance
5. ✅ Adicionar constraints de integridade

## Verificação

Após executar, teste:

1. Acesse: 🎉 Eventos Operacionais
2. Clique em "👥 Alocar Equipe" em qualquer evento
3. Deve carregar:
   - Lista de funcionários disponíveis
   - Lista de funções (Motorista, Fotógrafo, etc.)
   - Formulário para adicionar membros da equipe

## Resposta Esperada

```json
{
  "success": true,
  "message": "Migration executada com sucesso",
  "data": {
    "tabelas_criadas": ["evento_funcionarios", "funcoes_evento"],
    "funcoes_inseridas": 11
  }
}
```

## Troubleshooting

### Erro: "Arquivo migration não encontrado"
- O arquivo `migration_evento_funcionarios.sql` não está no Railway
- Verifique se o push foi feito corretamente

### Erro: "relation already exists"
- As tabelas já foram criadas anteriormente
- Tudo certo, pode usar normalmente!

### Erro 401: Unauthorized
- Token inválido ou expirado
- Faça login novamente e pegue novo token

### Erro 403: Forbidden
- Usuário não é admin
- Faça login com usuário admin
