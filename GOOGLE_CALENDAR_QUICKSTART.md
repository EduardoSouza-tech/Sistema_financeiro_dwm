# 🚀 QUICK START: Configurar Google Calendar (5 minutos)

## ✅ PASSO 1: Google Cloud Console (2 min)

1. Acesse: https://console.cloud.google.com/
2. Crie novo projeto: **Sistema Financeiro DWM**
3. Menu lateral → **APIs e Serviços** → **Biblioteca**
4. Busque e **ATIVE**: "Google Calendar API"

## 🔑 PASSO 2: Criar Credenciais OAuth 2.0 (2 min)

1. **APIs e Serviços** → **Credenciais**
2. **+ CRIAR CREDENCIAIS** → **ID do cliente OAuth**
3. Configurar:
   - Tipo: **Aplicativo da Web**
   - Nome: **Sistema Financeiro DWM**
   - **URIs de redirecionamento autorizados**:
     ```
     https://sistemafinanceirodwm-production.up.railway.app/api/google-calendar/callback
     ```
4. **COPIE**:
   - ✅ Client ID: `123456789-abc...apps.googleusercontent.com`
   - ✅ Client Secret: `GOCSPX-abc123...`

## ⚙️ PASSO 3: Configurar Railway (1 min)

1. Acesse: https://railway.app/ (seu projeto)
2. Aba **Variables**
3. Adicione (clique em **+ New Variable**):
   ```
   GOOGLE_CLIENT_ID=COLE_SEU_CLIENT_ID_AQUI
   GOOGLE_CLIENT_SECRET=COLE_SEU_CLIENT_SECRET_AQUI
   GOOGLE_REDIRECT_URI=https://sistemafinanceirodwm-production.up.railway.app/api/google-calendar/callback
   ```
4. Clique em **Deploy** (ou espere auto-deploy)

## ✅ PRONTO! Teste Agora:

1. Aguarde 1 minuto para Railway fazer deploy
2. Abra o sistema: https://sistemafinanceirodwm-production.up.railway.app
3. Vá em **📷 Agenda de Fotografia**
4. Clique em **⚙️ Configurações**
5. Ative: **🗓️ Sincronizar com Google Calendar**
6. Clique em **🔐 Autorizar Google Calendar**
7. Faça login com sua conta Google
8. Conceda as permissões
9. ✅ Deve voltar para o sistema com mensagem de sucesso!

## 🧪 Testar Sincronização:

1. Crie uma sessão na agenda
2. Clique em **🔄 Sync Google Calendar**
3. Abra https://calendar.google.com
4. ✅ O evento deve aparecer!

## ❌ Problemas?

### "redirect_uri_mismatch"
- Verifique se a URL no Google Cloud Console é **EXATAMENTE**:
  ```
  https://sistemafinanceirodwm-production.up.railway.app/api/google-calendar/callback
  ```

### "invalid_client"
- Verifique as variáveis no Railway
- Client ID deve começar com números e terminar em `.apps.googleusercontent.com`
- Client Secret deve começar com `GOCSPX-`

### "access_denied"
- Você negou as permissões
- Clique novamente em **Autorizar** e aceite

## 📞 Suporte

Se der erro, me envie:
1. Screenshot da tela de erro
2. URL que aparece no navegador
3. Console do navegador (F12 → Console)

---

**Tempo total**: ~5 minutos  
**Custo**: Gratuito (até 1 milhão de requisições/dia)
