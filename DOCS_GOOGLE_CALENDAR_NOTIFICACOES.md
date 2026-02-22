# 📅 Sistema de Notificações e Google Calendar

## Visão Geral

O sistema implementa notificações automáticas por e-mail e integração com Google Calendar para alertar sobre:

- ⏰ **Sessões Próximas** (≤ 3 dias)
- 🚨 **Sessões Atrasadas**
- 📝 **Sessões em Aberto** (muitas pendentes)
- 📄 **Contratos Próximos do Vencimento** (≤ 30 dias)
- ❌ **Contratos Vencidos**

---

## 🚀 Configuração Inicial

### 1. Instalar Dependências

```bash
pip install -r requirements_notifications.txt
```

Ou instalar manualmente:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client schedule
```

---

## 📧 Configuração de E-mail (SMTP)

### Opção 1: Via Interface Web

1. Acesse **Agenda de Fotografia** → Botão **⚙️ Configurações**
2. Preencha os campos na seção **📮 Servidor SMTP**:
   - **Servidor SMTP**: `smtp.gmail.com` (para Gmail)
   - **Porta**: `587`
   - **E-mail do Remetente**: seu e-mail
   - **Usuário SMTP**: seu e-mail
   - **Senha / App Password**: senha de aplicativo (veja abaixo)

3. **Adicione e-mails** que receberão notificações na seção **📧 E-mails para Notificações**

4. Clique em **💾 Salvar Todas Configurações**

5. Teste a conexão clicando em **🧪 Testar Conexão SMTP**

### Opção 2: Via Variáveis de Ambiente (.env)

```env
# SMTP Configuration
EMAIL_NOTIFICATIONS_ENABLED=True
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=True
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua_senha_de_app
SMTP_FROM_EMAIL=seu-email@gmail.com
SMTP_FROM_NAME=Sistema Financeiro DWM
```

### Como Gerar Senha de App (Gmail)

1. Acesse sua conta Google: [myaccount.google.com](https://myaccount.google.com)
2. Vá em **Segurança** → **Verificação em duas etapas** (ativar se necessário)
3. Role até **Senhas de app**: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. Selecione **App**: **E-mail** | **Dispositivo**: **Outro** (digite "Sistema DWM")
5. Clique em **Gerar** e copie a senha de 16 caracteres
6. Use essa senha no campo **Senha / App Password**

### Outros Provedores

**Outlook/Hotmail:**
```
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=seu-email@outlook.com
```

**SendGrid:**
```
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=sua_api_key_sendgrid
```

---

## 🗓️ Configuração do Google Calendar

### 1. Criar Projeto no Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie um novo projeto chamado "Sistema Financeiro DWM"
3. Ative a **Google Calendar API**:
   - Menu → **APIs e Serviços** → **Biblioteca**
   - Pesquise "Google Calendar API"
   - Clique em **Ativar**

### 2. Criar Credenciais OAuth 2.0

1. Menu → **APIs e Serviços** → **Credenciais**
2. Clique em **Criar Credenciais** → **ID do cliente OAuth**
3. Escolha **Aplicativo da Web**
4. Configure:
   - **Nome**: Sistema DWM
   - **URIs de redirecionamento autorizados**:
     - `https://sistemafinanceirodwm-production.up.railway.app/api/google-calendar/callback`
     - `http://localhost:5000/api/google-calendar/callback` (desenvolvimento)

5. Após criar, copie:
   - **ID do cliente**
   - **Chave secreta do cliente**

### 3. Configurar Variáveis de Ambiente

Adicione ao arquivo `.env` ou configure no Railway:

```env
GOOGLE_CLIENT_ID=seu_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=sua_secret_key
GOOGLE_REDIRECT_URI=https://sistemafinanceirodwm-production.up.railway.app/api/google-calendar/callback
```

### 4. Autorizar no Sistema

1. Acesse **Agenda de Fotografia** → **⚙️ Configurações**
2. Marque a opção **🗓️ Sincronizar com Google Calendar**
3. Clique em **🔐 Autorizar Google Calendar**
4. Você será redirecionado para o Google
5. Faça login e autorize o aplicativo
6. Após autorização, você será redirecionado de volta ao sistema

---

## 🔔 Scheduler de Notificações Automáticas

O scheduler verifica automaticamente sessões e contratos **3 vezes por dia**:
- **08:00** - Manhã
- **14:00** - Tarde
- **18:00** - Final do dia

### Iniciar Scheduler

**Opção 1: Via Interface (Futuro)**
```
Implementar botão na interface para iniciar/parar scheduler
```

**Opção 2: Via Linha de Comando**
```bash
# Iniciar scheduler (modo daemon)
python notification_scheduler.py start

# Testar notificações manualmente
python notification_scheduler.py test

# Ver status
python notification_scheduler.py status
```

**Opção 3: Integrar ao iniciar_web.py**

Adicione ao final do `iniciar_web.py`:

```python
# Iniciar scheduler de notificações
try:
    import notification_scheduler
    notification_scheduler.start_scheduler()
    print("✅ Scheduler de notificações iniciado")
except Exception as e:
    print(f"⚠️ Scheduler de notificações não iniciado: {e}")
```

---

## 📡 API Endpoints

### Notificações

**Teste de notificações (manual)**
```http
POST /api/notifications/test
```

**Configurações de notificações**
```http
GET /api/notifications/settings
POST /api/notifications/settings
```

**Status do scheduler**
```http
GET /api/scheduler/status
POST /api/scheduler/start
POST /api/scheduler/stop
```

### Google Calendar

**Autorização**
```http
GET /api/google-calendar/authorize
GET /api/google-calendar/callback
GET /api/google-calendar/status
```

**Sincronização**
```http
POST /api/google-calendar/sync
```

**Eventos**
```http
POST /api/google-calendar/event/create
PUT /api/google-calendar/event/<event_id>
DELETE /api/google-calendar/event/<event_id>
```

---

## 🧪 Testando o Sistema

### 1. Testar SMTP

Na interface:
1. Configure SMTP
2. Clique em **🧪 Testar Conexão SMTP**
3. Verifique se o e-mail chegou na caixa de entrada

Via terminal:
```bash
python notification_service.py 1
```
*(1 = ID da empresa)*

### 2. Testar Google Calendar

1. Crie uma sessão com data futura
2. Clique em **🔄 Sync Google Calendar**
3. Verifique se o evento apareceu no Google Calendar

### 3. Testar Scheduler

```bash
python notification_scheduler.py test
```

---

## 📊 Estrutura de Arquivos Criados

```
Sistema_financeiro_dwm/
├── notification_service.py           # Serviço de notificações
├── notification_scheduler.py         # Scheduler automático
├── requirements_notifications.txt    # Dependências
├── config.py                          # ✅ Atualizado com configs SMTP
├── app/
│   ├── routes/
│   │   └── agenda.py                 # ✅ Atualizado com endpoints
│   └── utils/
│       └── google_calendar_helper.py # ✅ Já existia, completo
├── static/
│   └── agenda_calendar.js            # ✅ Atualizado com SMTP
└── config/
    ├── email_settings.json           # Configurações salvas
    └── google_credentials.json       # Tokens OAuth (NÃO comitar!)
```

---

## 🔒 Segurança

### Arquivos a NÃO Comitar no Git

Adicione ao `.gitignore`:

```gitignore
# Configurações sensíveis
config/email_settings.json
config/google_credentials.json

# Variáveis de ambiente
.env
```

### Variáveis de Ambiente no Railway

Configure no Railway → Projeto → Variables:

```
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://sistemafinanceirodwm-production.up.railway.app/api/google-calendar/callback

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=senha_de_app
SMTP_FROM_EMAIL=seu-email@gmail.com
EMAIL_NOTIFICATIONS_ENABLED=True
```

---

## 🎯 Exemplos de E-mails Enviados

### Sessões Próximas
```
Assunto: ⚠️ 3 Sessão(ões) nos Próximos 3 Dias

📅 2026-02-24 - 14:00
👤 Cliente: João Silva
📍 Local: Av. Paulista, 1000
📝 Tipo: Casamento
```

### Contratos Vencidos
```
Assunto: 🚨 2 Contrato(s) Vencido(s)

📄 Contrato Nº 2024-001
👤 Cliente: Maria Santos
📅 Validade: 2026-01-15
⏱️ Horas: 45 / 50
```

---

## 🛠️ Troubleshooting

### E-mails não estão sendo enviados

1. **Verifique as credenciais SMTP**:
   ```python
   python -c "import notification_service; notification_service.send_notification_batch(1)"
   ```

2. **Gmail**: Use senha de app, não a senha normal

3. **Porta bloqueada**: Alguns hosts bloqueiam porta 587, tente 465 com SSL

4. **Firewall**: Verifique se o firewall permite conexões SMTP

### Google Calendar não autoriza

1. **URI de redirecionamento**: Verifique se está exatamente igual no Google Console

2. **Escopo incorreto**: Garanta que os scopes estão corretos no `config.py`

3. **Credenciais expiradas**: Delete `config/google_credentials.json` e autorize novamente

### Scheduler não está rodando

1. **Verificar status**:
   ```bash
   python notification_scheduler.py status
   ```

2. **Ver logs**:
   ```bash
   python notification_scheduler.py start
   ```
   (mantenha o terminal aberto para ver logs)

3. **Integrar ao app**: Adicione ao `iniciar_web.py` conforme documentado acima

---

## ✅ Checklist de Implementação

- [x] Criar `notification_service.py`
- [x] Criar `notification_scheduler.py`
- [x] Atualizar `config.py` com configurações SMTP
- [x] Atualizar `app/routes/agenda.py` com endpoints
- [x] Atualizar `static/agenda_calendar.js` com SMTP
- [x] Criar `requirements_notifications.txt`
- [ ] Configurar credenciais do Google Cloud
- [ ] Adicionar variáveis de ambiente no Railway
- [ ] Testar envio de e-mails
- [ ] Testar autorização Google Calendar
- [ ] Iniciar scheduler em produção

---

## 📞 Suporte

Para problemas ou dúvidas, revise:

1. Esta documentação
2. Logs do console (F12 no navegador)
3. Logs do servidor Python
4. Verifique as configurações em **Agenda → Configurações**

---

**Desenvolvido para Sistema Financeiro DWM**  
*Documentação criada em 22/02/2026*
