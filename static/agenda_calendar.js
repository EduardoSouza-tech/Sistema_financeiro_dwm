/**
 * ===============================================
 * AGENDA DE FOTOGRAFIA - SISTEMA DE CALENDÁRIO
 * ===============================================
 * Gerenciamento completo com FullCalendar e Google Calendar
 * Versão: 2.0 - 2026-01-23
 */

let calendar = null;
let currentView = 'calendar'; // 'calendar' ou 'list'
let emailSettings = {
    notification_emails: [],
    google_calendar_enabled: false,
    google_calendar_id: null
};

/**
 * Inicializar calendário
 */
function initAgendaCalendar() {
    console.log('📅 Inicializando Agenda de Fotografia...');
    
    const calendarEl = document.getElementById('calendar-container');
    if (!calendarEl) {
        console.error('❌ Elemento calendar-container não encontrado');
        return;
    }

    // Inicializar FullCalendar com layout compacto estilo Windows
    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'pt-br',
        firstDay: 0, // Domingo como primeiro dia
        dayHeaderFormat: { weekday: 'short' }, // Formato curto dos dias
        headerToolbar: {
            left: 'prev,next',
            center: 'title',
            right: 'today dayGridMonth,timeGridWeek,listMonth'
        },
        buttonText: {
            today: 'Hoje',
            month: 'Mês',
            week: 'Semana',
            list: 'Lista'
        },
        weekNumbers: false,
        navLinks: false,
        editable: false,
        selectable: false,
        dayMaxEvents: 2,
        displayEventTime: false,
        displayEventEnd: false,
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            meridiem: false
        },
        fixedWeekCount: false,
        showNonCurrentDates: true,
        height: 'auto',
        contentHeight: 500,
        aspectRatio: 1.8,
        // Configurações para evitar eventos multi-dia
        nextDayThreshold: '09:00:00',
        defaultAllDay: true,
        forceEventDuration: false,
        eventDisplay: 'block',
        eventClick: function(info) {
            handleEventClick(info.event);
        },
        eventDidMount: function(info) {
            // Adicionar tooltip rico
            const tooltip = info.event.extendedProps.detailedTooltip;
            info.el.title = tooltip;
            
            // Adicionar estilo personalizado
            info.el.style.cursor = 'pointer';
            info.el.style.borderLeft = `4px solid ${info.event.backgroundColor}`;
            info.el.style.fontSize = '12px';
            info.el.style.padding = '4px 6px';
        },
        eventContent: function(arg) {
            // Renderização compacta estilo Windows
            const props = arg.event.extendedProps;
            
            // Ícone baseado no tipo
            let icon = '📷';
            if (props.tipo_video) icon = '🎥';
            else if (props.tipo_mobile) icon = '📱';
            
            // Usar número do contrato ou título da sessão
            let displayText = props.contrato_numero || props.titulo || 'Sessão';
            
            // Truncar se for muito longo (max 12 caracteres + ...)
            if (displayText.length > 12) {
                displayText = displayText.substring(0, 12) + '...';
            }
            
            return {
                html: `<div class="fc-event-main-frame"><div class="fc-event-title-container"><div class="fc-event-title">${icon} ${displayText}</div></div></div>`
            };
        }
    });

    calendar.render();
    console.log('✅ Calendário renderizado');
    
    // Carregar eventos imediatamente após renderizar
    loadCalendarEvents();
    
    // Carregar configurações de e-mail
    loadEmailSettings();
    
    console.log('✅ Calendário totalmente inicializado');
}

/**
 * Carregar eventos do calendário (sessões)
 */
async function loadCalendarEvents() {
    if (!calendar) {
        console.error('❌ Calendário não inicializado!');
        return;
    }
    
    try {
        console.log('📡 Carregando sessões para o calendário...');
        const response = await fetch('/api/sessoes');
        if (!response.ok) {
            throw new Error('Erro ao buscar sessões: ' + response.status);
        }
        const sessoes = await response.json();
        console.log('📦 Sessões recebidas:', sessoes.length);
        
        const events = sessoes.map(sessao => {
            // Determinar cor baseado no status
            const color = getStatusColor(sessao);
            const statusText = getStatusText(sessao);
            const tipos = getTiposCaptacao(sessao);
            
            // Criar título mais informativo
            let title = `${sessao.cliente_nome || 'Cliente'}`;
            if (tipos && tipos !== 'N/A') {
                const tiposArray = tipos.split(', ');
                const icones = {
                    'Foto': '📸',
                    'Vídeo': '🎥',
                    'Mobile': '📱'
                };
                const iconesStr = tiposArray.map(t => icones[t] || '').join('');
                title = `${iconesStr} ${title}`;
            }
            
            // Preparar tooltip detalhado
            const detailedTooltip = `
🎯 SESSÃO DE FOTOGRAFIA

👤 Cliente: ${sessao.cliente_nome || 'Não informado'}
📍 Local: ${sessao.endereco || 'Não informado'}
🎬 Tipo: ${tipos}
📅 Sessão: ${sessao.data ? new Date(sessao.data).toLocaleDateString('pt-BR') : 'N/A'}
⏰ Horário: ${sessao.horario || 'Não definido'}
⏱️ Duração: ${sessao.quantidade_horas ? sessao.quantidade_horas + 'h' : 'N/A'}
📦 Entrega: ${sessao.prazo_entrega ? new Date(sessao.prazo_entrega).toLocaleDateString('pt-BR') : 'Sem prazo'}
🏷️ Status: ${statusText}

💡 Clique para ver detalhes ou editar
            `.trim();
            
            // Criar data do evento - SEMPRE allDay para não se espalhar
            let eventStart = sessao.data;
            
            // Garantir formato correto da data (YYYY-MM-DD) - SEM timezone
            if (sessao.data) {
                if (sessao.data.includes('T')) {
                    // Remove hora e timezone se existir
                    eventStart = sessao.data.split('T')[0];
                } else {
                    // Já está no formato correto
                    eventStart = sessao.data;
                }
            }
            
            console.log('📅 Data processada:', {
                original: sessao.data,
                processada: eventStart,
                cliente: sessao.cliente_nome
            });
            
            
            const eventObj = {
                id: sessao.id,
                title: title,
                start: eventStart,
                allDay: true,
                display: 'block',
                backgroundColor: color,
                borderColor: color,
                textColor: '#ffffff',
                extendedProps: {
                    sessao: sessao,
                    sessao_id: sessao.id,
                    contrato_numero: sessao.contrato_numero,
                    titulo: sessao.titulo,
                    cliente_nome: sessao.cliente_nome,
                    horario: sessao.horario,
                    duracao: sessao.quantidade_horas ? `${sessao.quantidade_horas}h` : null,
                    endereco: sessao.endereco,
                    prazo_entrega: sessao.prazo_entrega,
                    valor: sessao.valor,
                    tipo_foto: sessao.tipo_foto,
                    tipo_video: sessao.tipo_video,
                    tipo_mobile: sessao.tipo_mobile,
                    detailedTooltip: detailedTooltip,
                    statusText: statusText
                }
            }
            
            // Log de debug para verificar datas
            console.log(`📅 Evento criado:`, {
                id: sessao.id,
                cliente: sessao.cliente_nome,
                data_original: sessao.data,
                start: eventStart,
                allDay: true
            });
            
            return eventObj;
        });
        
        console.log(`✅ ${events.length} eventos carregados para o calendário`);
        console.log('📋 Eventos detalhados:', events.map(e => ({
            title: e.title,
            start: e.start,
            end: e.end,
            allDay: e.allDay
        })));
        
        // Atualizar contador no UI
        updateAgendaSummary(events.length);
        
        // Adicionar eventos ao calendário
        calendar.removeAllEvents();
        calendar.addEventSource(events);
        
        console.log('✅ Eventos adicionados ao calendário');
        
        return events;
    } catch (error) {
        console.error('❌ Erro ao carregar eventos:', error);
        showNotification('❌ Erro ao carregar eventos da agenda', 'error');
        return [];
    }
}

/**
 * Determinar cor do status
 */
function getStatusColor(sessao) {
    // Cinza para finalizados
    if (sessao.status === 'finalizado' || sessao.concluido) {
        return '#95a5a6';
    }
    
    // Verificar prazo
    if (sessao.prazo_entrega) {
        const hoje = new Date();
        hoje.setHours(0, 0, 0, 0);
        const prazo = new Date(sessao.prazo_entrega);
        prazo.setHours(0, 0, 0, 0);
        const diffDias = Math.ceil((prazo - hoje) / (1000 * 60 * 60 * 24));
        
        if (diffDias < 0) {
            return '#e74c3c'; // Vermelho - Atrasado
        } else if (diffDias <= 3) {
            return '#f39c12'; // Amarelo - Próximo ao prazo
        }
    }
    
    return '#27ae60'; // Verde - No prazo
}

/**
 * Obter tipos de captação
 */
function getTiposCaptacao(sessao) {
    const tipos = [];
    if (sessao.tipo_foto) tipos.push('Foto');
    if (sessao.tipo_video) tipos.push('Vídeo');
    if (sessao.tipo_mobile) tipos.push('Mobile');
    return tipos.join(', ') || 'N/A';
}

/**
 * Alternar entre visualização calendário e lista
 */
function toggleCalendarView() {
    currentView = currentView === 'calendar' ? 'list' : 'calendar';
    
    const calendarView = document.getElementById('calendar-view');
    const listView = document.getElementById('list-view');
    
    if (currentView === 'calendar') {
        calendarView.style.display = 'block';
        listView.style.display = 'none';
        if (calendar) calendar.refetchEvents();
    } else {
        calendarView.style.display = 'none';
        listView.style.display = 'block';
        loadAgendaListView();
    }
}

/**
 * Carregar visualização em lista
 */
async function loadAgendaListView() {
    try {
        console.log('📋 Carregando visualização em lista...');
        const sessoes = await apiGet('/sessoes');
        const tbody = document.getElementById('tbody-agenda');
        
        if (!tbody) {
            console.error('❌ tbody-agenda não encontrado');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (sessoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">Nenhuma sessão cadastrada</td></tr>';
            return;
        }
        
        // Ordenar por data
        sessoes.sort((a, b) => new Date(b.data) - new Date(a.data));
        
        sessoes.forEach(sessao => {
            const color = getStatusColor(sessao);
            const statusText = getStatusText(sessao);
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${sessao.data ? new Date(sessao.data).toLocaleDateString('pt-BR') : '-'}</td>
                <td>${sessao.horario || '-'}</td>
                <td>${escapeHtml(sessao.cliente_nome || '-')}</td>
                <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(sessao.endereco || '')}">${escapeHtml(sessao.endereco || '-')}</td>
                <td>${getTiposCaptacao(sessao)}</td>
                <td>${sessao.prazo_entrega ? new Date(sessao.prazo_entrega).toLocaleDateString('pt-BR') : '-'}</td>
                <td><span class="badge" style="background: ${color};">${statusText}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="editarSessao(${sessao.id})" title="Editar">✏️</button>
                    <button class="btn btn-sm btn-danger" onclick="excluirSessao(${sessao.id})" title="Excluir">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        console.log('✅ Lista carregada');
    } catch (error) {
        console.error('❌ Erro ao carregar lista:', error);
    }
}

/**
 * Obter texto do status
 */
function getStatusText(sessao) {
    if (sessao.status === 'finalizado' || sessao.concluido) {
        return 'Finalizado';
    }
    
    if (sessao.prazo_entrega) {
        const hoje = new Date();
        hoje.setHours(0, 0, 0, 0);
        const prazo = new Date(sessao.prazo_entrega);
        prazo.setHours(0, 0, 0, 0);
        const diffDias = Math.ceil((prazo - hoje) / (1000 * 60 * 60 * 24));
        
        if (diffDias < 0) return 'Atrasado';
        if (diffDias <= 3) return 'Urgente';
    }
    
    return 'No Prazo';
}

/**
 * Manipular clique em evento
 */
function handleEventClick(event) {
    const sessao = event.extendedProps.sessao;
    editarSessao(sessao.id);
}

/**
 * Sincronizar com Google Calendar
 */
async function syncGoogleCalendar() {
    try {
        if (!emailSettings.google_calendar_enabled) {
            showNotification('⚠️ Google Calendar não configurado. Configure primeiro os e-mails.', 'warning');
            openEmailSettings();
            return;
        }
        
        showNotification('🔄 Sincronizando com Google Calendar...', 'info');
        
        // Implementar sincronização
        const response = await fetch('/api/google-calendar/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            }
        });
        
        if (response.ok) {
            showNotification('✅ Sincronizado com sucesso!', 'success');
            if (calendar) calendar.refetchEvents();
        } else {
            throw new Error('Falha na sincronização');
        }
    } catch (error) {
        console.error('❌ Erro ao sincronizar:', error);
        showNotification('❌ Erro ao sincronizar com Google Calendar', 'error');
    }
}

/**
 * Abrir configurações de e-mail
 */
function openEmailSettings() {
    // Remove modal antigo se existir
    const oldModal = document.getElementById('email-settings-modal');
    if (oldModal) oldModal.remove();
    
    const modal = document.createElement('div');
    modal.id = 'email-settings-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 700px; max-height: 90vh; overflow-y: auto;">
            <div class="modal-header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <h3>⚙️ Configurações de Notificações</h3>
                <button class="modal-close" onclick="closeModal('email-settings-modal')">✕</button>
            </div>
            <div class="modal-body">
                <!-- Seção 1: E-mails de Notificação -->
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: #2c3e50;">📧 E-mails para Notificações</h4>
                    <p style="font-size: 12px; color: #666; margin-bottom: 10px;">
                        Estes e-mails receberão notificações sobre sessões e contratos
                    </p>
                    <div id="email-list" style="margin-bottom: 10px;"></div>
                    <div style="display: flex; gap: 10px;">
                        <input type="email" id="new-email-input" class="form-control" placeholder="email@exemplo.com" style="flex: 1;">
                        <button class="btn btn-primary" onclick="addNotificationEmail()">➕ Adicionar</button>
                    </div>
                </div>
                
                <!-- Seção 2: Configurações SMTP -->
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: #2c3e50;">📮 Servidor SMTP (E-mail)</h4>
                    <div class="form-group">
                        <label style="display: flex; align-items: center; gap: 10px;">
                            <input type="checkbox" id="smtp-enabled" 
                                   ${emailSettings.smtp_enabled ? 'checked' : ''}
                                   onchange="toggleSmtpConfig(this.checked)">
                            Habilitar envio de e-mails
                        </label>
                    </div>
                    
                    <div id="smtp-config" style="display: ${emailSettings.smtp_enabled ? 'block' : 'none'}; margin-top: 15px;">
                        <div class="form-group">
                            <label>Servidor SMTP</label>
                            <input type="text" id="smtp-host" class="form-control" 
                                   value="${emailSettings.smtp_host || 'smtp.gmail.com'}"
                                   placeholder="smtp.gmail.com">
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                            <div class="form-group">
                                <label>Porta</label>
                                <input type="number" id="smtp-port" class="form-control" 
                                       value="${emailSettings.smtp_port || 587}"
                                       placeholder="587">
                            </div>
                            <div class="form-group">
                                <label>Nome do Remetente</label>
                                <input type="text" id="smtp-from-name" class="form-control" 
                                       value="${emailSettings.smtp_from_name || 'Sistema Financeiro DWM'}"
                                       placeholder="Seu Nome">
                            </div>
                        </div>
                        <div class="form-group">
                            <label>E-mail do Remetente</label>
                            <input type="email" id="smtp-from-email" class="form-control" 
                                   value="${emailSettings.smtp_from_email || ''}"
                                   placeholder="seu-email@gmail.com">
                        </div>
                        <div class="form-group">
                            <label>Usuário SMTP</label>
                            <input type="text" id="smtp-user" class="form-control" 
                                   value="${emailSettings.smtp_user || ''}"
                                   placeholder="seu-email@gmail.com">
                        </div>
                        <div class="form-group">
                            <label>Senha / App Password</label>
                            <input type="password" id="smtp-password" class="form-control" 
                                   placeholder="••••••••••••••••">
                            <p style="font-size: 11px; color: #666; margin-top: 5px;">
                                💡 Gmail: Use "Senha de App" gerada em 
                                <a href="https://myaccount.google.com/apppasswords" target="_blank">myaccount.google.com/apppasswords</a>
                            </p>
                        </div>
                        <button class="btn btn-sm" style="background: #3498db; color: white;" onclick="testSmtpConnection()">
                            🧪 Testar Conexão SMTP
                        </button>
                    </div>
                </div>
                
                <!-- Seção 3: Google Calendar -->
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0; color: #2c3e50;">🗓️ Google Calendar</h4>
                    <div class="form-group">
                        <label style="display: flex; align-items: center; gap: 10px;">
                            <input type="checkbox" id="google-calendar-enabled" 
                                   ${emailSettings.google_calendar_enabled ? 'checked' : ''}
                                   onchange="toggleGoogleCalendar(this.checked)">
                            Sincronizar com Google Calendar
                        </label>
                    </div>
                    
                    <div id="google-calendar-config" style="display: ${emailSettings.google_calendar_enabled ? 'block' : 'none'}; margin-top: 15px;">
                        <div class="form-group">
                            <label>ID do Calendário</label>
                            <input type="text" id="google-calendar-id" class="form-control" 
                                   value="${emailSettings.google_calendar_id || ''}"
                                   placeholder="seu-email@gmail.com">
                            <p style="font-size: 11px; color: #666; margin-top: 5px;">
                                Encontre em: Google Calendar → Configurações → ID do calendário
                            </p>
                        </div>
                        <button class="btn" style="background: #DB4437; color: white;" onclick="authorizeGoogleCalendar()">
                            🔐 Autorizar Google Calendar
                        </button>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn" onclick="closeModal('email-settings-modal')">Cancelar</button>
                <button class="btn btn-primary" onclick="saveAllNotificationSettings()">💾 Salvar Todas Configurações</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    renderEmailList();
}

/**
 * Alternar configuração SMTP
 */
function toggleSmtpConfig(enabled) {
    const configEl = document.getElementById('smtp-config');
    if (configEl) {
        configEl.style.display = enabled ? 'block' : 'none';
    }
}

/**
 * Testar conexão SMTP
 */
async function testSmtpConnection() {
    try {
        showNotification('🧪 Testando conexão SMTP...', 'info');
        
        const response = await fetch('/api/notifications/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            }
        });
        
        if (response.ok) {
            showNotification('✅ E-mail de teste enviado! Verifique sua caixa de entrada.', 'success');
        } else {
            throw new Error('Falha no teste');
        }
    } catch (error) {
        console.error('❌ Erro ao testar SMTP:', error);
        showNotification('❌ Erro ao testar conexão SMTP. Verifique as configurações.', 'error');
    }
}

/**
 * Salvar todas as configurações de notificações
 */
async function saveAllNotificationSettings() {
    try {
        // Configurações de e-mail
        emailSettings.notification_emails = emailSettings.notification_emails || [];
        emailSettings.google_calendar_id = document.getElementById('google-calendar-id')?.value || '';
        emailSettings.google_calendar_enabled = document.getElementById('google-calendar-enabled')?.checked || false;
        
        // Configurações SMTP
        emailSettings.smtp_enabled = document.getElementById('smtp-enabled')?.checked || false;
        emailSettings.smtp_host = document.getElementById('smtp-host')?.value || '';
        emailSettings.smtp_port = parseInt(document.getElementById('smtp-port')?.value) || 587;
        emailSettings.smtp_user = document.getElementById('smtp-user')?.value || '';
        emailSettings.smtp_from_email = document.getElementById('smtp-from-email')?.value || '';
        emailSettings.smtp_from_name = document.getElementById('smtp-from-name')?.value || '';
        
        const smtpPassword = document.getElementById('smtp-password')?.value;
        if (smtpPassword) {
            emailSettings.smtp_password = smtpPassword;
        }
        
        // Salvar configurações de e-mail
        const response1 = await fetch('/api/email-settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            },
            body: JSON.stringify(emailSettings)
        });
        
        // Salvar configurações de notificações (SMTP)
        const response2 = await fetch('/api/notifications/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            },
            body: JSON.stringify(emailSettings)
        });
        
        if (response1.ok && response2.ok) {
            showNotification('✅ Todas as configurações salvas com sucesso!', 'success');
            closeModal('email-settings-modal');
        } else {
            throw new Error('Falha ao salvar');
        }
    } catch (error) {
        console.error('❌ Erro ao salvar configurações:', error);
        showNotification('❌ Erro ao salvar configurações', 'error');
    }
}

/**
 * Renderizar lista de e-mails
 */
function renderEmailList() {
    const emailListEl = document.getElementById('email-list');
    if (!emailListEl) return;
    
    if (emailSettings.notification_emails.length === 0) {
        emailListEl.innerHTML = '<p style="color: #999; font-size: 14px;">Nenhum e-mail cadastrado</p>';
        return;
    }
    
    emailListEl.innerHTML = emailSettings.notification_emails.map((email, index) => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: #f8f9fa; border-radius: 4px; margin-bottom: 5px;">
            <span>${email}</span>
            <button class="btn btn-sm btn-danger" onclick="removeNotificationEmail(${index})" style="padding: 2px 8px;">✕</button>
        </div>
    `).join('');
}

/**
 * Adicionar e-mail de notificação
 */
function addNotificationEmail() {
    const input = document.getElementById('new-email-input');
    const email = input.value.trim();
    
    if (!email) {
        showNotification('⚠️ Digite um e-mail válido', 'warning');
        return;
    }
    
    if (!email.includes('@')) {
        showNotification('⚠️ E-mail inválido', 'warning');
        return;
    }
    
    if (emailSettings.notification_emails.includes(email)) {
        showNotification('⚠️ E-mail já cadastrado', 'warning');
        return;
    }
    
    emailSettings.notification_emails.push(email);
    input.value = '';
    renderEmailList();
}

/**
 * Remover e-mail de notificação
 */
function removeNotificationEmail(index) {
    emailSettings.notification_emails.splice(index, 1);
    renderEmailList();
}

/**
 * Alternar Google Calendar
 */
function toggleGoogleCalendar(enabled) {
    emailSettings.google_calendar_enabled = enabled;
    const configEl = document.getElementById('google-calendar-config');
    if (configEl) {
        configEl.style.display = enabled ? 'block' : 'none';
    }
}

/**
 * Autorizar Google Calendar
 */
function authorizeGoogleCalendar() {
    showNotification('🔄 Redirecionando para autorização do Google...', 'info');
    // Implementar OAuth2 do Google
    window.location.href = '/api/google-calendar/authorize';
}

/**
 * Salvar configurações de e-mail
 */
async function saveEmailSettings() {
    try {
        const googleCalendarId = document.getElementById('google-calendar-id')?.value || '';
        
        emailSettings.google_calendar_id = googleCalendarId;
        
        const response = await fetch('/api/email-settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            },
            body: JSON.stringify(emailSettings)
        });
        
        if (response.ok) {
            showNotification('✅ Configurações salvas com sucesso!', 'success');
            closeModal('email-settings-modal');
        } else {
            throw new Error('Falha ao salvar');
        }
    } catch (error) {
        console.error('❌ Erro ao salvar configurações:', error);
        showNotification('❌ Erro ao salvar configurações', 'error');
    }
}

/**
 * Carregar configurações de e-mail
 */
async function loadEmailSettings() {
    try {
        const response = await fetch('/api/email-settings');
        if (response.ok) {
            const data = await response.json();
            emailSettings = data;
            console.log('✅ Configurações de e-mail carregadas');
        }
    } catch (error) {
        console.error('⚠️ Erro ao carregar configurações de e-mail:', error);
    }
}

/**
 * Atualizar resumo da agenda
 */
function updateAgendaSummary(totalSessoes) {
    const summaryEl = document.getElementById('agenda-total-sessoes');
    if (summaryEl) {
        summaryEl.innerHTML = `
            <strong>${totalSessoes}</strong> ${totalSessoes === 1 ? 'sessão agendada' : 'sessões agendadas'}
        `;
    }
}

/**
 * Editar sessão a partir da agenda
 */
function editarSessaoAgenda(sessaoId) {
    console.log('Editando sessão:', sessaoId);
    // Redirecionar para a seção de contratos/sessões com o ID
    showSection('contratos');
    setTimeout(() => {
        // Procurar o botão de edição da sessão
        const editBtn = document.querySelector(`[onclick*="editarSessao(${sessaoId})"]`);
        if (editBtn) {
            editBtn.click();
        } else {
            // Se não encontrar, mostrar detalhes da sessão
            showNotification('📋 Carregando detalhes da sessão...', 'info');
            // Aqui você pode adicionar lógica adicional para abrir modal de edição
        }
    }, 500);
}

/**
 * Funções auxiliares de API
 */
async function apiGet(endpoint) {
    const response = await fetch(`/api${endpoint}`);
    if (!response.ok) {
        throw new Error(`Erro ao buscar ${endpoint}`);
    }
    return await response.json();
}

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

console.log('✅ Módulo agenda_calendar.js carregado');

// Expor funções globalmente
window.initAgendaCalendar = initAgendaCalendar;
window.toggleCalendarView = toggleCalendarView;
window.syncGoogleCalendar = syncGoogleCalendar;
window.openEmailSettings = openEmailSettings;
window.addNotificationEmail = addNotificationEmail;
window.removeNotificationEmail = removeNotificationEmail;
window.toggleGoogleCalendar = toggleGoogleCalendar;
window.toggleSmtpConfig = toggleSmtpConfig;
window.authorizeGoogleCalendar = authorizeGoogleCalendar;
window.saveEmailSettings = saveEmailSettings;
window.saveAllNotificationSettings = saveAllNotificationSettings;
window.testSmtpConnection = testSmtpConnection;

console.log('✅ agenda_calendar.js carregado com funções de notificação');
