# 📅 Guia de Configuração do Google Calendar

## 🎯 Objetivo
Integrar o sistema com Google Calendar para sincronização automática de sessões de fotografia.

## 📋 Pré-requisitos

### 1. Criar Projeto no Google Cloud Console
1. Acesse: https://console.cloud.google.com/
2. Crie um novo projeto ou selecione um existente
3. Anote o **ID do Projeto**

### 2. Habilitar Google Calendar API
1. No menu lateral, vá em **APIs e Serviços** → **Biblioteca**
2. Busque por "Google Calendar API"
3. Clique em **ATIVAR**

### 3. Criar Credenciais OAuth 2.0
1. Vá em **APIs e Serviços** → **Credenciais**
2. Clique em **+ CRIAR CREDENCIAIS** → **ID do cliente OAuth**
3. Tipo de aplicativo: **Aplicativo da Web**
4. Nome: `Sistema Financeiro DWM`
5. **URIs de redirecionamento autorizados**:
   ```
   https://sistemafinanceirodwm-production.up.railway.app/api/google-calendar/callback
   http://localhost:5000/api/google-calendar/callback
   ```
6. Clique em **CRIAR**
7. **ANOTE AS CREDENCIAIS**:
   - 🔑 **Client ID**: `123456789-abc.apps.googleusercontent.com`
   - 🔐 **Client Secret**: `GOCSPX-abc123...`

### 4. Configurar Variáveis de Ambiente no Railway
1. Acesse o projeto no Railway
2. Vá em **Variables**
3. Adicione as seguintes variáveis:
   ```env
   GOOGLE_CLIENT_ID=seu-client-id-aqui
   GOOGLE_CLIENT_SECRET=seu-client-secret-aqui
   GOOGLE_REDIRECT_URI=https://sistemafinanceirodwm-production.up.railway.app/api/google-calendar/callback
   ```

## 📦 Dependências Necessárias

Adicione ao `requirements.txt`:
```
google-auth==2.27.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.116.0
```

Instalar localmente:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## 🔄 Fluxo de Autenticação

### Passo 1: Usuário clica em "🔐 Autorizar Google Calendar"
- Sistema redireciona para página de autorização do Google
- Usuário faz login e concede permissões

### Passo 2: Callback do Google
- Google redireciona de volta com código de autorização
- Sistema troca código por tokens de acesso
- Tokens são salvos no arquivo `config/google_credentials.json`

### Passo 3: Sincronização
- Sistema usa tokens para criar/atualizar eventos no Google Calendar
- Refresh token permite acesso contínuo sem nova autorização

## 🛠️ Implementação

### Arquivo criado: `app/utils/google_calendar_helper.py`
Funções principais:
- `get_authorization_url()` - Gera URL de autorização
- `exchange_code_for_tokens(code)` - Troca código por tokens
- `create_calendar_event(session_data)` - Cria evento no calendário
- `update_calendar_event(event_id, session_data)` - Atualiza evento
- `delete_calendar_event(event_id)` - Remove evento
- `list_calendar_events(start_date, end_date)` - Lista eventos

### Endpoints da API:
```
GET  /api/google-calendar/authorize     → Redireciona para autorização
GET  /api/google-calendar/callback      → Processa código de autorização
POST /api/google-calendar/sync          → Sincroniza todas as sessões
POST /api/google-calendar/event/create  → Cria evento individual
PUT  /api/google-calendar/event/<id>    → Atualiza evento
DELETE /api/google-calendar/event/<id>  → Remove evento
```

## ✅ Checklist de Configuração

- [ ] Projeto criado no Google Cloud Console
- [ ] Google Calendar API habilitada
- [ ] Credenciais OAuth 2.0 criadas
- [ ] URIs de redirecionamento configuradas
- [ ] Variáveis de ambiente configuradas no Railway
- [ ] Bibliotecas instaladas (`pip install`)
- [ ] Código implementado em `app/routes/agenda.py`
- [ ] Helper criado em `app/utils/google_calendar_helper.py`
- [ ] Teste de autorização realizado
- [ ] Sincronização testada

## 🧪 Como Testar

### 1. Teste Local (antes de fazer deploy)
```bash
# Configure as variáveis de ambiente
export GOOGLE_CLIENT_ID="seu-client-id"
export GOOGLE_CLIENT_SECRET="seu-client-secret"
export GOOGLE_REDIRECT_URI="http://localhost:5000/api/google-calendar/callback"

# Execute o servidor
python iniciar_web.py

# Abra no navegador
http://localhost:5000
```

### 2. Teste de Autorização
1. Vá em **📷 Agenda de Fotografia**
2. Clique em **⚙️ Configurações**
3. Ative **🗓️ Sincronizar com Google Calendar**
4. Clique em **🔐 Autorizar Google Calendar**
5. Deve redirecionar para login do Google
6. Após autorizar, deve voltar com mensagem de sucesso

### 3. Teste de Sincronização
1. Crie uma sessão na agenda
2. Clique em **🔄 Sync Google Calendar**
3. Verifique se o evento aparece no seu Google Calendar

## ⚠️ Troubleshooting

### Erro: "redirect_uri_mismatch"
**Causa**: URI de redirecionamento não configurada no Google Cloud Console  
**Solução**: Adicione a URL exata em **Credenciais** → **URIs de redirecionamento autorizados**

### Erro: "invalid_client"
**Causa**: Client ID ou Secret incorretos  
**Solução**: Verifique as variáveis de ambiente no Railway

### Erro: "access_denied"
**Causa**: Usuário negou permissões  
**Solução**: Clique novamente em autorizar e aceite as permissões

### Tokens expirados
**Causa**: Access token venceu (validade: 1 hora)  
**Solução**: Sistema deve usar refresh token automaticamente. Se persistir, reautorize.

## 🔒 Segurança

1. **NUNCA** commite as credenciais no Git
2. Use variáveis de ambiente (Railway Variables)
3. Tokens são salvos em `config/google_credentials.json` (adicione ao `.gitignore`)
4. Considere criptografar tokens salvos em produção

## 📚 Documentação Oficial

- Google Calendar API: https://developers.google.com/calendar/api/guides/overview
- OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- Python Client: https://github.com/googleapis/google-api-python-client

## 📝 Notas Importantes

1. **Limite de Requisições**: Google Calendar API tem limite de 1.000.000 requisições/dia (quota gratuita)
2. **Refresh Token**: Válido até o usuário revogar o acesso
3. **Access Token**: Expira após 1 hora, deve ser renovado automaticamente
4. **Calendário Padrão**: Eventos são criados no calendário primário do usuário autorizado
5. **Time Zone**: Configure o timezone correto (America/Sao_Paulo)

## 🎨 Melhorias Futuras

- [ ] Suporte a múltiplos calendários
- [ ] Notificações via Google Calendar
- [ ] Sincronização bidirecional (Google → Sistema)
- [ ] Compartilhamento de calendários com equipe
- [ ] Lembretes personalizados via e-mail/SMS
