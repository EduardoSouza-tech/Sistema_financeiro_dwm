# 📅 Agenda de Fotografia - Documentação

## Visão Geral

Sistema completo de agenda de fotografia com calendário interativo, status coloridos e integração com Google Calendar.

## Funcionalidades Implementadas

### ✅ 1. Calendário Interativo (FullCalendar)

- **Visualizações**: Mês, Semana, Dia, Lista
- **Navegação**: Botões prev/next e "Hoje"
- **Idioma**: Português (PT-BR)
- **Eventos**: Clique para editar sessão
- **Tooltips**: Informações completas ao passar o mouse

### ✅ 2. Status Coloridos

| Cor | Status | Descrição |
|-----|--------|-----------|
| 🟢 Verde (#27ae60) | No Prazo | Mais de 3 dias até o prazo de entrega |
| 🟡 Amarelo (#f39c12) | Próximo ao Prazo | 3 dias ou menos até o prazo |
| 🔴 Vermelho (#e74c3c) | Atrasado | Prazo de entrega vencido |
| ⚪ Cinza (#95a5a6) | Finalizado | Sessão concluída |

### ✅ 3. Visualizações

- **Calendário**: Visualização em grade com eventos
- **Lista**: Tabela detalhada com todas as sessões
- **Alternância**: Botão para alternar entre visualizações

### ✅ 4. Integração Google Calendar

- **Sincronização**: Exportar sessões para Google Calendar
- **OAuth2**: Autorização segura (em desenvolvimento)
- **Configuração**: ID do calendário personalizável

### ✅ 5. Notificações por E-mail

- **Múltiplos E-mails**: Adicionar vários destinatários
- **CRUD Completo**: Adicionar/remover e-mails
- **Persistência**: Salvo em arquivo JSON

## Como Usar

### Acessar a Agenda

1. Menu **Operacional** → **Agenda de Fotografia**
2. O calendário será carregado automaticamente

### Criar Nova Sessão

1. Clique em **Nova Sessão** (redireciona para Contratos e Sessões)
2. Preencha os dados da sessão
3. A sessão aparecerá automaticamente no calendário

### Configurar E-mails

1. Clique em **⚙️ Configurar E-mails**
2. Digite o e-mail e clique em **Adicionar**
3. Repita para adicionar mais e-mails
4. Clique em **Salvar Configurações**

### Configurar Google Calendar

1. Acesse **⚙️ Configurar E-mails**
2. Marque **Sincronizar com Google Calendar**
3. Digite o ID do seu calendário do Google
   - Encontre em: Google Calendar → Configurações → ID do calendário
4. Clique em **Autorizar Google Calendar**
5. Complete o fluxo OAuth2
6. Clique em **Salvar Configurações**

### Sincronizar com Google

1. Clique em **🔄 Sincronizar Google Calendar**
2. Aguarde a confirmação
3. Verifique no Google Calendar

## Estrutura de Arquivos

```
Sistema_financeiro_dwm/
├── static/
│   └── agenda_calendar.js          # Lógica do calendário
├── app/
│   └── routes/
│       └── agenda.py                # Endpoints de configuração
├── config/
│   └── email_settings.json          # Configurações salvas
└── templates/
    └── interface_nova.html          # Seção de agenda
```

## Endpoints API

### GET /api/email-settings
Retorna configurações de e-mail

**Resposta:**
```json
{
  "notification_emails": ["email1@example.com", "email2@example.com"],
  "google_calendar_enabled": true,
  "google_calendar_id": "seu-email@gmail.com"
}
```

### POST /api/email-settings
Salva configurações de e-mail

**Body:**
```json
{
  "notification_emails": ["email@example.com"],
  "google_calendar_enabled": true,
  "google_calendar_id": "calendario-id"
}
```

### GET /api/google-calendar/authorize
Inicia fluxo OAuth2 do Google Calendar

### GET /api/google-calendar/callback
Callback do OAuth2 (recebe código de autorização)

### POST /api/google-calendar/sync
Sincroniza sessões com Google Calendar

**Resposta:**
```json
{
  "success": true,
  "message": "Sincronização iniciada"
}
```

## Tecnologias Utilizadas

- **FullCalendar 6.1.10**: Biblioteca de calendário
- **Google Calendar API**: Integração com Google
- **Flask Blueprint**: Arquitetura modular do backend
- **JSON File Storage**: Armazenamento de configurações

## Próximos Passos

### Em Desenvolvimento:

1. **OAuth2 Completo**: Implementação completa do fluxo Google
2. **Envio de E-mails**: Sistema de notificações automáticas
3. **Lembretes**: Notificar antes de sessões e prazos
4. **Exportação ICS**: Download de eventos no formato iCalendar
5. **Webhooks**: Notificações em tempo real

## Debugging

### Logs do Calendário

O sistema gera logs detalhados no console:

```javascript
📅 Inicializando Agenda de Fotografia...
✅ Calendário inicializado
📡 Carregando sessões para o calendário...
✅ 5 eventos carregados
```

### Verificar Configurações

```bash
# Ver arquivo de configurações
cat config/email_settings.json
```

### Problemas Comuns

**Calendário não aparece:**
- Verifique se FullCalendar foi carregado (F12 → Console)
- Confirme que `calendar-container` existe no DOM

**Sincronização falha:**
- Verifique credenciais do Google Calendar
- Confirme que OAuth2 foi autorizado
- Veja logs do backend

**E-mails não salvam:**
- Verifique permissões da pasta `config/`
- Confirme que o servidor tem acesso de escrita

## Segurança

- ✅ CSRF Protection em todos os endpoints
- ✅ Credenciais OAuth2 não expostas no frontend
- ✅ Validação de e-mails no backend
- ✅ Armazenamento seguro de configurações

## Suporte

Para issues ou dúvidas, consulte o repositório do projeto.

---

**Versão**: 2.0  
**Data**: 2026-01-23  
**Autor**: Sistema Financeiro DWM
