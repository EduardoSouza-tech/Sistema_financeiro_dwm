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

    // Verificar mensagem de retorno do OAuth do Google
    _handleGoogleAuthMessage();
    
    console.log('✅ Calendário totalmente inicializado');
}

/**
 * Lê o parâmetro ?message da URL e exibe feedback do OAuth do Google
 */
function _handleGoogleAuthMessage() {
    const params = new URLSearchParams(window.location.search);
    const message = params.get('message');
    if (!message) return;

    if (message === 'google_auth_success') {
        showNotification('✅ Google Calendar autorizado com sucesso! Agora você pode sincronizar suas sessões.', 'success');
        // Recarregar configurações para refletir google_calendar_enabled = true
        loadEmailSettings();
    } else if (message === 'google_auth_failed' || message === 'google_auth_error') {
        const error = params.get('error') || 'Erro desconhecido';
        showNotification(`❌ Falha na autorização do Google Calendar: ${error}`, 'error');
    }

    // Limpar o parâmetro da URL sem recarregar a página
    const cleanUrl = window.location.pathname + window.location.hash;
    window.history.replaceState({}, '', cleanUrl);
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
        if (calendar) loadCalendarEvents();
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
                <td style="text-align: center;">
                    <button onclick="editarSessao(${sessao.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar">✏️</button>
                    <button onclick="excluirSessao(${sessao.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
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
        
        const response = await fetch('/api/google-calendar/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            }
        });

        let data = {};
        try { data = await response.json(); } catch(e) {}

        if (response.ok && data.success) {
            const criados   = data.events_created  ?? 0;
            const atualizados = data.events_updated ?? 0;
            const detalhes = criados + atualizados === 0
                ? 'Nenhuma alteração necessária — tudo já está sincronizado.'
                : `${criados} evento(s) criado(s), ${atualizados} atualizado(s).`;
            showNotification(`✅ Sincronização concluída! ${detalhes}`, 'success');
            if (calendar) loadCalendarEvents();
        } else if (response.status === 401) {
            showNotification('⚠️ Google Calendar não autorizado. Clique em "🔐 Autorizar Google Calendar" primeiro.', 'warning');
            openEmailSettings();
        } else {
            const errMsg = data.error || 'Falha na sincronização';
            throw new Error(errMsg);
        }
    } catch (error) {
        console.error('❌ Erro ao sincronizar:', error);
        showNotification(`❌ Erro ao sincronizar com Google Calendar: ${error.message}`, 'error');
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
                                Encontre em: <a href="https://calendar.google.com/calendar/r/settings" target="_blank" rel="noopener noreferrer" style="color: #4285F4;">calendar.google.com → Configurações → seu calendário → ID do calendário</a>
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
    modal.classList.add('show'); // tornar visível (modal-overlay é display:none por padrão)
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

        const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token') || '';
        const empresaId = window.currentEmpresaId || '';

        const response = await fetch('/api/notifications/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken(),
                ...(token    ? { 'Authorization': `Bearer ${token}` } : {}),
                ...(empresaId ? { 'X-Empresa-ID': String(empresaId) }  : {})
            }
        });

        const data = await response.json().catch(() => ({}));

        if (data.success) {
            showNotification(data.message || '✅ E-mail enviado! Verifique sua caixa de entrada.', 'success');
        } else {
            const msg = data.message || data.error || 'Falha ao enviar e-mail. Verifique as configurações.';
            showNotification(`❌ ${msg}`, 'error');
            if (data.log) console.warn('📋 Log do servidor:', data.log);
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
 * Enviar lembretes de sessões próximas (com deduplicação)
 */
async function testSendReminders() {
    showNotification('📬 Enviando lembretes de sessões próximas...', 'info');
    try {
        const resp = await fetch('/api/notifications/send-reminders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken(),
            },
            body: JSON.stringify({ days_ahead: 3 }),
        });
        const data = await resp.json().catch(() => ({}));
        if (data.success) {
            showNotification(data.message || '✅ Lembretes enviados!', 'success');
        } else {
            showNotification(`❌ ${data.message || data.error || 'Falha ao enviar lembretes'}`, 'error');
        }
    } catch (err) {
        console.error('❌ Erro ao enviar lembretes:', err);
        showNotification('❌ Erro de conexão ao enviar lembretes.', 'error');
    }
}

/**
 * Exibir modal com histórico de e-mails enviados
 */
async function viewNotificationsLog() {
    const oldModal = document.getElementById('notifications-log-modal');
    if (oldModal) oldModal.remove();

    const modal = document.createElement('div');
    modal.id = 'notifications-log-modal';
    modal.className = 'modal-overlay';
    modal.style.cssText = 'display:flex; align-items:center; justify-content:center; z-index:9999;';
    modal.innerHTML = `
        <div style="
            background:#f8fafc;
            border-radius:20px;
            width:100%;
            max-width:900px;
            max-height:88vh;
            display:flex;
            flex-direction:column;
            box-shadow:0 24px 64px rgba(30,41,59,0.28);
            overflow:hidden;
            animation: modalFadeIn 0.2s ease;
        ">
            <!-- Header -->
            <div style="
                background: linear-gradient(135deg, #1a1f3a 0%, #2c3e50 100%);
                padding: 20px 24px;
                display:flex;
                align-items:center;
                justify-content:space-between;
                border-bottom: 3px solid #3498db;
                flex-shrink:0;
            ">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="background:rgba(52,152,219,0.25); width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px;">📬</div>
                    <div>
                        <div style="color:#fff; font-size:16px; font-weight:700; line-height:1.2;">Histórico de E-mails</div>
                        <div style="color:#94a3b8; font-size:12px; margin-top:2px;">Registro de todas as notificações enviadas</div>
                    </div>
                </div>
                <button onclick="closeModal('notifications-log-modal')" style="
                    background:rgba(255,255,255,0.1);
                    border:none; cursor:pointer; color:#fff;
                    width:32px; height:32px; border-radius:50%;
                    font-size:14px; font-weight:700;
                    display:flex; align-items:center; justify-content:center;
                    transition:background 0.2s;
                " onmouseover="this.style.background='rgba(239,68,68,0.7)'" onmouseout="this.style.background='rgba(255,255,255,0.1)'">✕</button>
            </div>

            <!-- Body -->
            <div style="overflow-y:auto; flex:1; padding:20px 24px;">
                <div id="notif-log-content" style="min-height:120px; display:flex; align-items:center; justify-content:center;">
                    <div style="text-align:center; color:#94a3b8;">
                        <div style="font-size:28px; margin-bottom:8px;">⏳</div>
                        <div style="font-size:14px;">Carregando histórico...</div>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <div style="
                padding:14px 24px;
                background:#fff;
                border-top:1px solid #e2e8f0;
                display:flex;
                justify-content:flex-end;
                flex-shrink:0;
            ">
                <button onclick="closeModal('notifications-log-modal')" style="
                    background: linear-gradient(135deg, #1a1f3a, #2c3e50);
                    color:white; border:none; padding:9px 22px;
                    border-radius:8px; cursor:pointer; font-size:13px; font-weight:600;
                    transition: opacity 0.2s;
                " onmouseover="this.style.opacity='0.85'" onmouseout="this.style.opacity='1'">Fechar</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.classList.add('show');

    // Fechar ao clicar fora
    modal.addEventListener('click', e => { if (e.target === modal) closeModal('notifications-log-modal'); });

    try {
        const resp = await fetch('/api/notifications/log?limit=50');
        const data = await resp.json().catch(() => ({}));
        const container = document.getElementById('notif-log-content');

        if (!data.success) {
            container.innerHTML = `<div style="text-align:center;padding:30px;color:#ef4444;">❌ ${data.error || 'Erro ao carregar histórico'}</div>`;
            return;
        }

        const logs = data.logs || [];
        if (logs.length === 0) {
            container.innerHTML = `
                <div style="text-align:center; padding:40px 20px; color:#94a3b8;">
                    <div style="font-size:40px; margin-bottom:12px;">📭</div>
                    <div style="font-size:15px; font-weight:600; color:#64748b;">Nenhum e-mail registrado ainda</div>
                    <div style="font-size:13px; margin-top:4px;">Envie lembretes para que apareçam aqui.</div>
                </div>`;
            return;
        }

        const tipoMeta = {
            lembrete_sessao:  { label: 'Lembrete',       icon: '📅', bg: '#eff6ff', color: '#3b82f6' },
            sessao_atrasada:  { label: 'Atrasada',        icon: '🚨', bg: '#fef2f2', color: '#ef4444' },
            sessoes_abertas:  { label: 'Em Aberto',       icon: '📝', bg: '#fff7ed', color: '#f59e0b' },
            contrato_proximo: { label: 'Ctr. Próximo',    icon: '📄', bg: '#f0fdf4', color: '#10b981' },
            contrato_vencido: { label: 'Ctr. Vencido',    icon: '🚨', bg: '#fef2f2', color: '#ef4444' },
        };

        const total   = logs.length;
        const enviados = logs.filter(l => l.status === 'enviado').length;
        const erros    = total - enviados;

        container.innerHTML = `
            <!-- Stats -->
            <div style="display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap;">
                <div style="flex:1; min-width:120px; background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:14px 18px; display:flex; align-items:center; gap:12px; box-shadow:0 1px 4px rgba(30,41,59,0.06);">
                    <div style="background:#eff6ff; width:36px; height:36px; border-radius:9px; display:flex; align-items:center; justify-content:center; font-size:18px;">📨</div>
                    <div><div style="font-size:20px; font-weight:800; color:#1e293b;">${total}</div><div style="font-size:11px; color:#64748b; font-weight:500;">Total</div></div>
                </div>
                <div style="flex:1; min-width:120px; background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:14px 18px; display:flex; align-items:center; gap:12px; box-shadow:0 1px 4px rgba(30,41,59,0.06);">
                    <div style="background:#f0fdf4; width:36px; height:36px; border-radius:9px; display:flex; align-items:center; justify-content:center; font-size:18px;">✅</div>
                    <div><div style="font-size:20px; font-weight:800; color:#10b981;">${enviados}</div><div style="font-size:11px; color:#64748b; font-weight:500;">Enviados</div></div>
                </div>
                ${erros > 0 ? `
                <div style="flex:1; min-width:120px; background:#fff; border:1px solid #fecaca; border-radius:12px; padding:14px 18px; display:flex; align-items:center; gap:12px; box-shadow:0 1px 4px rgba(30,41,59,0.06);">
                    <div style="background:#fef2f2; width:36px; height:36px; border-radius:9px; display:flex; align-items:center; justify-content:center; font-size:18px;">❌</div>
                    <div><div style="font-size:20px; font-weight:800; color:#ef4444;">${erros}</div><div style="font-size:11px; color:#64748b; font-weight:500;">Erros</div></div>
                </div>` : ''}
            </div>

            <!-- Table -->
            <div style="background:#fff; border-radius:14px; border:1px solid #e2e8f0; overflow:hidden; box-shadow:0 1px 4px rgba(30,41,59,0.06);">
                <table style="width:100%; border-collapse:collapse; font-size:13px;">
                    <thead>
                        <tr style="background:linear-gradient(135deg,#1a1f3a,#2c3e50); color:#fff;">
                            <th style="padding:11px 14px; font-weight:600; text-align:left; white-space:nowrap;">🕐 Data/Hora</th>
                            <th style="padding:11px 14px; font-weight:600; text-align:left;">Tipo</th>
                            <th style="padding:11px 14px; font-weight:600; text-align:left;">Assunto</th>
                            <th style="padding:11px 14px; font-weight:600; text-align:left;">Destinatário(s)</th>
                            <th style="padding:11px 14px; font-weight:600; text-align:center;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${logs.map((log, i) => {
                            const dest = Array.isArray(log.destinatarios)
                                ? log.destinatarios.join(', ')
                                : (log.destinatarios || '—');
                            const m = tipoMeta[log.tipo] || { label: log.tipo, icon: '📧', bg: '#f8fafc', color: '#64748b' };
                            const ok = log.status === 'enviado';
                            const rowBg = i % 2 === 0 ? '#fff' : '#f8fafc';
                            return `
                                <tr style="background:${rowBg}; border-bottom:1px solid #f1f5f9; transition:background 0.12s;"
                                    onmouseover="this.style.background='#eff6ff'"
                                    onmouseout="this.style.background='${rowBg}'">
                                    <td style="padding:10px 14px; white-space:nowrap; color:#64748b; font-size:12px;">${log.enviado_em}</td>
                                    <td style="padding:10px 14px; white-space:nowrap;">
                                        <span style="background:${m.bg}; color:${m.color}; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700; display:inline-flex; align-items:center; gap:4px;">${m.icon} ${m.label}</span>
                                    </td>
                                    <td style="padding:10px 14px; color:#1e293b; max-width:260px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${log.assunto}">${log.assunto}</td>
                                    <td style="padding:10px 14px; color:#475569; font-size:12px; max-width:180px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${dest}">${dest}</td>
                                    <td style="padding:10px 14px; text-align:center;">
                                        ${ok
                                            ? '<span style="background:#dcfce7;color:#16a34a;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;">✓ Enviado</span>'
                                            : '<span style="background:#fee2e2;color:#dc2626;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;">✗ Erro</span>'}
                                        ${log.erro_detalhe ? `<div style="color:#dc2626;font-size:10px;margin-top:3px;">${log.erro_detalhe}</div>` : ''}
                                    </td>
                                </tr>`;
                        }).join('')}
                    </tbody>
                </table>
            </div>
            <div style="text-align:right; margin-top:8px; color:#94a3b8; font-size:11px;">Exibindo os ${total} registros mais recentes</div>
        `;
    } catch (err) {
        const container = document.getElementById('notif-log-content');
        if (container) container.innerHTML = `<div style="text-align:center;padding:30px;color:#ef4444;">❌ Erro de conexão: ${err.message}</div>`;
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

/**
 * Atualiza a Agenda de Fotografia após mudanças em sessões.
 * Chamado por modals.js quando uma sessão é criada/editada/status alterado.
 */
function refreshAgendaFotografia() {
    if (calendar) loadCalendarEvents();
    if (currentView === 'list') loadAgendaListView();
}

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
window.testSendReminders = testSendReminders;
window.viewNotificationsLog = viewNotificationsLog;
window.refreshAgendaFotografia = refreshAgendaFotografia;

console.log('✅ agenda_calendar.js carregado com funções de notificação');
