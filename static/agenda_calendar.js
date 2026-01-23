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

    // Inicializar FullCalendar
    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'pt-br',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listMonth'
        },
        buttonText: {
            today: 'Hoje',
            month: 'Mês',
            week: 'Semana',
            day: 'Dia',
            list: 'Lista'
        },
        firstDay: 0, // Domingo
        weekNumbers: false,
        navLinks: true,
        editable: false,
        dayMaxEvents: 3,
        displayEventTime: true,
        displayEventEnd: false,
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            meridiem: false
        },
        height: 'auto',
        contentHeight: 650,
        aspectRatio: 2,
        // IMPORTANTE: Configurações para evitar eventos multi-dia incorretos
        nextDayThreshold: '00:00:00', // Eventos não se estendem para o próximo dia
        defaultAllDay: false,
        forceEventDuration: true,
        defaultTimedEventDuration: '01:00', // 1 hora por padrão
        events: loadCalendarEvents,
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
            // Renderização customizada do evento com informações mais claras
            const props = arg.event.extendedProps;
            const horario = props.horario || '';
            
            // Ícone baseado no tipo
            let icon = '📷';
            if (props.tipo_video) icon = '🎥';
            else if (props.tipo_mobile) icon = '📱';
            
            // HTML compacto mas informativo
            let html = '<div class="agenda-event-content">';
            
            if (horario && !arg.event.allDay) {
                html += `<div class="agenda-event-time">${horario}</div>`;
            }
            
            html += `<div class="agenda-event-title">${icon} ${props.cliente_nome || 'Cliente'}</div>`;
            
            if (props.endereco && arg.view.type === 'timeGridDay') {
                html += `<div class="agenda-event-location">📍 ${props.endereco.substring(0, 30)}...</div>`;
            }
            
            html += '</div>';
            
            return { html: html };
        },
        dayCellDidMount: function(info) {
            // Adicionar estilo aos dias
            if (info.isToday) {
                info.el.style.backgroundColor = '#fff9e6';
            }
        }
    });

    calendar.render();
    console.log('✅ Calendário inicializado');
    
    // Carregar configurações de e-mail
    loadEmailSettings();
}

/**
 * Carregar eventos do calendário (sessões)
 */
async function loadCalendarEvents(fetchInfo, successCallback, failureCallback) {
    try {
        console.log('📡 Carregando sessões para o calendário...');
        const sessoes = await apiGet('/sessoes');
        
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
            
            // Criar data/hora do evento - FIXO para aparecer apenas no dia correto
            let eventStart, eventEnd = null;
            let allDay = true; // Padrão: dia inteiro
            
            // Se tiver horário específico, criar evento com hora
            if (sessao.horario && sessao.horario !== 'None' && sessao.horario !== '') {
                try {
                    const [hora, minuto] = sessao.horario.split(':').map(n => parseInt(n) || 0);
                    const dataEvento = new Date(sessao.data + 'T00:00:00');
                    dataEvento.setHours(hora, minuto, 0, 0);
                    eventStart = dataEvento.toISOString();
                    allDay = false;
                    
                    // Adicionar duração se tiver (para mostrar bloco de tempo)
                    if (sessao.quantidade_horas && parseFloat(sessao.quantidade_horas) > 0) {
                        const dataFim = new Date(dataEvento);
                        dataFim.setHours(dataFim.getHours() + parseFloat(sessao.quantidade_horas));
                        eventEnd = dataFim.toISOString();
                    } else {
                        // Se não tiver duração, adicionar 1 hora por padrão
                        const dataFim = new Date(dataEvento);
                        dataFim.setHours(dataFim.getHours() + 1);
                        eventEnd = dataFim.toISOString();
                    }
                } catch (e) {
                    console.warn('⚠️ Erro ao processar horário:', e, sessao);
                    // Fallback: evento de dia inteiro
                    eventStart = sessao.data;
                    allDay = true;
                }
            } else {
                // Sem horário = evento de dia inteiro (apenas a data, sem hora)
                eventStart = sessao.data;
                allDay = true;
                // NÃO definir eventEnd para eventos allDay - isso causa o espalhamento!
            }
            
            
            const eventObj = {
                id: sessao.id,
                title: title,
                start: eventStart,
                allDay: allDay,
                backgroundColor: color,
                borderColor: color,
                textColor: '#ffffff',
                extendedProps: {
                    sessao: sessao,
                    sessao_id: sessao.id,
                    cliente_nome: sessao.cliente_nome,
                    horario: sessao.horario,
                    duracao: sessao.quantidade_horas ? `${sessao.quantidade_horas}h` : null,
                    endereco: sessao.endereco,
                    prazo_entrega: sessao.prazo_entrega ? new Date(sessao.prazo_entrega).toLocaleDateString('pt-BR') : null,
                    valor: sessao.valor,
                    tipo_foto: sessao.tipo_foto,
                    tipo_video: sessao.tipo_video,
                    tipo_mobile: sessao.tipo_mobile,
                    tooltip: `${sessao.cliente_nome} - ${tipos}`,
                    detailedTooltip: detailedTooltip,
                    statusText: statusText
                }
            };
            
            // Adicionar eventEnd apenas se tiver
            if (eventEnd) {
                eventObj.end = eventEnd;
            }
            
            // Log de debug para verificar datas
            console.log(`📅 Evento criado:`, {
                id: sessao.id,
                cliente: sessao.cliente_nome,
                data_original: sessao.data,
                start: eventStart,
                end: eventEnd,
                allDay: allDay,
                horario: sessao.horario
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
        
        if (successCallback) {
            successCallback(events);
        }
        return events;
    } catch (error) {
        console.error('❌ Erro ao carregar eventos:', error);
        if (failureCallback) {
            failureCallback(error);
        }
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
    const modal = document.createElement('div');
    modal.id = 'email-settings-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <h3>⚙️ Configurações de E-mail e Notificações</h3>
                <button class="modal-close" onclick="closeModal('email-settings-modal')">✕</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>📧 E-mails para Notificações</label>
                    <p style="font-size: 12px; color: #666; margin-bottom: 10px;">Adicione os e-mails que receberão notificações sobre sessões</p>
                    <div id="email-list" style="margin-bottom: 10px;"></div>
                    <div style="display: flex; gap: 10px;">
                        <input type="email" id="new-email-input" class="form-control" placeholder="email@exemplo.com">
                        <button class="btn btn-primary" onclick="addNotificationEmail()">➕ Adicionar</button>
                    </div>
                </div>
                
                <hr style="margin: 20px 0;">
                
                <div class="form-group">
                    <label style="display: flex; align-items: center; gap: 10px;">
                        <input type="checkbox" id="google-calendar-enabled" 
                               ${emailSettings.google_calendar_enabled ? 'checked' : ''}
                               onchange="toggleGoogleCalendar(this.checked)">
                        🗓️ Sincronizar com Google Calendar
                    </label>
                </div>
                
                <div id="google-calendar-config" style="display: ${emailSettings.google_calendar_enabled ? 'block' : 'none'}; margin-top: 15px;">
                    <div class="form-group">
                        <label>ID do Calendário do Google</label>
                        <input type="text" id="google-calendar-id" class="form-control" 
                               value="${emailSettings.google_calendar_id || ''}"
                               placeholder="seu-email@gmail.com ou ID do calendário">
                        <p style="font-size: 12px; color: #666; margin-top: 5px;">
                            Encontre em: Google Calendar → Configurações → ID do calendário
                        </p>
                    </div>
                    <button class="btn" style="background: #DB4437; color: white;" onclick="authorizeGoogleCalendar()">
                        🔐 Autorizar Google Calendar
                    </button>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn" onclick="closeModal('email-settings-modal')">Cancelar</button>
                <button class="btn btn-primary" onclick="saveEmailSettings()">💾 Salvar Configurações</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    renderEmailList();
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

console.log('✅ Módulo agenda_calendar.js carregado');// Expor funções globalmente
window.initAgendaCalendar = initAgendaCalendar;
window.toggleCalendarView = toggleCalendarView;
window.syncGoogleCalendar = syncGoogleCalendar;
window.openEmailSettings = openEmailSettings;
window.addNotificationEmail = addNotificationEmail;
window.removeNotificationEmail = removeNotificationEmail;
window.toggleGoogleCalendar = toggleGoogleCalendar;
window.authorizeGoogleCalendar = authorizeGoogleCalendar;
window.saveEmailSettings = saveEmailSettings;

console.log('✅ agenda_calendar.js carregado');
