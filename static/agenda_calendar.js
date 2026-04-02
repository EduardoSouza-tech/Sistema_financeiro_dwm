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
    
    // CORREÇÃO: Verificar se FullCalendar está carregado
    if (typeof FullCalendar === 'undefined') {
        console.error('❌ FullCalendar não carregado. Aguardando...');
        setTimeout(initAgendaCalendar, 500);
        return;
    }
    
    const calendarEl = document.getElementById('calendar-container');
    if (!calendarEl) {
        console.error('❌ Elemento calendar-container não encontrado');
        return;
    }

    // Limpar calendário anterior se existir (prevenir duplicação)
    if (calendar) {
        console.log('🔄 Destruindo calendário anterior...');
        calendar.destroy();
        calendar = null;
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
        
        // CORREÇÃO: Limpar TODAS as event sources antes de adicionar (prevenir duplicação)
        const allEventSources = calendar.getEventSources();
        allEventSources.forEach(source => source.remove());
        calendar.removeAllEvents();
        
        // Adicionar eventos ao calendário
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
    const toggleIcon = document.getElementById('toggle-view-icon');
    const toggleText = document.getElementById('toggle-view-text');
    
    if (currentView === 'calendar') {
        calendarView.style.display = 'block';
        listView.style.display = 'none';
        // Atualizar botão para modo lista
        if (toggleIcon) toggleIcon.textContent = '📋';
        if (toggleText) toggleText.textContent = 'Ver Lista';
        if (calendar) loadCalendarEvents();
    } else {
        calendarView.style.display = 'none';
        listView.style.display = 'block';
        // Atualizar botão para modo calendário
        if (toggleIcon) toggleIcon.textContent = '📅';
        if (toggleText) toggleText.textContent = 'Ver Calendário';
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
            if (data.google_oauth_expired) {
                showGoogleTokenExpiredWarning();
            }
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
                    
                    <!-- Instruções de configuração -->
                    <div style="background: #e8f4fd; border-left: 4px solid #4285F4; border-radius: 6px; padding: 14px; margin-bottom: 16px;">
                        <p style="font-weight: 700; color: #1a237e; margin: 0 0 8px 0;">📋 Como configurar:</p>
                        <p style="font-size: 12px; color: #333; margin: 0 0 6px 0;"><strong>Requisitos:</strong> Ter uma conta Google e habilitar integração com o Google Agenda em sua conta.</p>
                        <ol style="font-size: 12px; color: #333; margin: 8px 0 8px 16px; padding: 0; line-height: 1.8;">
                            <li>Acesse o link: <a href="https://developers.google.com/workspace/guides/create-project" target="_blank" rel="noopener noreferrer" style="color: #1565C0;">developers.google.com/workspace/guides/create-project</a></li>
                            <li>Crie um projeto. Após isso, habilite <strong>API e serviços</strong> deste projeto.</li>
                            <li>Ao habilitar API e serviços, busque por <strong>Google Calendar API</strong>.</li>
                            <li>Ao habilitar a Google Calendar API, clique em <strong>"Criar credenciais"</strong> para gerar os arquivos necessários.</li>
                            <li>Preencha as informações conforme solicitado.</li>
                            <li>Clique em baixar as credenciais geradas. Após baixar, clique em <strong>"Concluir"</strong>.</li>
                            <li>Envie o arquivo baixado através do formulário abaixo.</li>
                        </ol>
                    </div>
                    
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
            background:#f1f5f9;
            border-radius:20px;
            width:95%;
            max-width:1060px;
            max-height:90vh;
            display:flex;
            flex-direction:column;
            box-shadow:0 28px 72px rgba(15,23,42,0.35);
            overflow:hidden;
            animation: modalFadeIn 0.22s ease;
        ">
            <!-- Header -->
            <div style="
                background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
                padding: 22px 28px;
                display:flex;
                align-items:center;
                justify-content:space-between;
                border-bottom: 3px solid #3b82f6;
                flex-shrink:0;
            ">
                <div style="display:flex; align-items:center; gap:14px;">
                    <div style="background:rgba(59,130,246,0.22); width:46px; height:46px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:22px; border:1px solid rgba(59,130,246,0.3); flex-shrink:0;">📬</div>
                    <div>
                        <div class="notif-hdr-title" style="color:#f8fafc; font-size:17px; font-weight:700; line-height:1.2;">Histórico de E-mails</div>
                        <div id="notif-log-subtitle" class="notif-hdr-sub" style="color:#94a3b8; font-size:12px; margin-top:3px;">Carregando registros...</div>
                    </div>
                </div>
                <button onclick="closeModal('notifications-log-modal')" style="
                    background:rgba(255,255,255,0.08);
                    border:1px solid rgba(255,255,255,0.12); cursor:pointer; color:#cbd5e1;
                    width:34px; height:34px; border-radius:50%;
                    font-size:15px; font-weight:700;
                    display:flex; align-items:center; justify-content:center;
                    transition:all 0.2s; flex-shrink:0;
                " onmouseover="this.style.background='rgba(239,68,68,0.65)';this.style.color='#fff'" onmouseout="this.style.background='rgba(255,255,255,0.08)';this.style.color='#cbd5e1'">✕</button>
            </div>

            <!-- Body -->
            <div style="overflow-y:auto; flex:1; padding:20px 24px; display:flex; flex-direction:column; gap:14px;">
                <div id="notif-log-content" style="min-height:140px; display:flex; align-items:center; justify-content:center;">
                    <div style="text-align:center; color:#94a3b8;">
                        <div style="font-size:32px; margin-bottom:10px;">⏳</div>
                        <div style="font-size:14px; font-weight:500;">Carregando histórico...</div>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <div style="
                padding:14px 24px;
                background:#fff;
                border-top:1px solid #e2e8f0;
                display:flex;
                align-items:center;
                justify-content:space-between;
                flex-shrink:0;
            ">
                <span id="notif-log-footer-count" style="color:#94a3b8; font-size:12px;"></span>
                <button onclick="closeModal('notifications-log-modal')" style="
                    background: linear-gradient(135deg, #0f172a, #1e3a5f);
                    color:white; border:none; padding:9px 24px;
                    border-radius:8px; cursor:pointer; font-size:13px; font-weight:600;
                    transition: opacity 0.2s;
                " onmouseover="this.style.opacity='0.85'" onmouseout="this.style.opacity='1'">Fechar</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.classList.add('show');

    // Forçar cores do cabeçalho (override da regra global !important do style.css)
    const _hdrTitle = modal.querySelector('.notif-hdr-title');
    const _hdrSub   = modal.querySelector('.notif-hdr-sub');
    if (_hdrTitle) _hdrTitle.style.setProperty('color', '#f8fafc', 'important');
    if (_hdrSub)   _hdrSub.style.setProperty('color',   '#94a3b8', 'important');

    // Fechar ao clicar fora
    modal.addEventListener('click', e => { if (e.target === modal) closeModal('notifications-log-modal'); });

    try {
        const resp = await fetch('/api/notifications/log?limit=100');
        const data = await resp.json().catch(() => ({}));
        const container = document.getElementById('notif-log-content');

        if (!data.success) {
            container.innerHTML = `<div style="text-align:center;padding:40px;color:#ef4444;"><div style="font-size:32px;margin-bottom:10px;">❌</div><div>${data.error || 'Erro ao carregar histórico'}</div></div>`;
            return;
        }

        const logs = data.logs || [];
        const subtitle = document.getElementById('notif-log-subtitle');

        if (logs.length === 0) {
            if (subtitle) subtitle.textContent = 'Nenhum registro encontrado';
            container.innerHTML = `
                <div style="text-align:center; padding:50px 20px; color:#94a3b8;">
                    <div style="font-size:48px; margin-bottom:14px;">📭</div>
                    <div style="font-size:15px; font-weight:600; color:#64748b;">Nenhum e-mail registrado ainda</div>
                    <div style="font-size:13px; margin-top:5px;">Envie lembretes para que apareçam aqui.</div>
                </div>`;
            return;
        }

        const tipoMeta = {
            lembrete_sessao:  { label: 'Lembrete de Sessão', icon: '📅', bg: '#eff6ff', color: '#2563eb', border: '#bfdbfe' },
            sessao_atrasada:  { label: 'Sessão Atrasada',    icon: '🚨', bg: '#fef2f2', color: '#dc2626', border: '#fecaca' },
            sessoes_abertas:  { label: 'Sessões em Aberto',  icon: '📝', bg: '#fff7ed', color: '#d97706', border: '#fed7aa' },
            contrato_proximo: { label: 'Contrato Próximo',   icon: '📄', bg: '#f0fdf4', color: '#16a34a', border: '#bbf7d0' },
            contrato_vencido: { label: 'Contrato Vencido',   icon: '⚠️', bg: '#fef3c7', color: '#b45309', border: '#fde68a' },
        };

        const esc = s => String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

        const total    = logs.length;
        const enviados = logs.filter(l => l.status === 'enviado').length;
        const erros    = total - enviados;

        if (subtitle) subtitle.textContent = `${total} registro${total !== 1 ? 's' : ''} · ${enviados} enviado${enviados !== 1 ? 's' : ''}${erros > 0 ? ` · ${erros} com erro` : ''}`;

        const footerCount = document.getElementById('notif-log-footer-count');
        if (footerCount) footerCount.textContent = `Exibindo ${total} registro${total !== 1 ? 's' : ''} mais recentes`;

        // ── Stats ──────────────────────────────────────────────────────────
        const statsHtml = `
            <div style="display:flex; gap:12px; flex-wrap:wrap;">
                <div style="flex:1; min-width:120px; background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:14px 16px; display:flex; align-items:center; gap:12px; box-shadow:0 1px 3px rgba(15,23,42,0.07);">
                    <div style="background:#eff6ff; width:38px; height:38px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0;">📨</div>
                    <div><div style="font-size:22px; font-weight:800; color:#0f172a; line-height:1;">${total}</div><div style="font-size:11px; color:#64748b; font-weight:500; margin-top:3px;">Total</div></div>
                </div>
                <div style="flex:1; min-width:120px; background:#fff; border:1px solid #bbf7d0; border-radius:12px; padding:14px 16px; display:flex; align-items:center; gap:12px; box-shadow:0 1px 3px rgba(15,23,42,0.07);">
                    <div style="background:#f0fdf4; width:38px; height:38px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0;">✅</div>
                    <div><div style="font-size:22px; font-weight:800; color:#16a34a; line-height:1;">${enviados}</div><div style="font-size:11px; color:#64748b; font-weight:500; margin-top:3px;">Enviados</div></div>
                </div>
                ${erros > 0 ? `
                <div style="flex:1; min-width:120px; background:#fff; border:1px solid #fecaca; border-radius:12px; padding:14px 16px; display:flex; align-items:center; gap:12px; box-shadow:0 1px 3px rgba(15,23,42,0.07);">
                    <div style="background:#fef2f2; width:38px; height:38px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0;">❌</div>
                    <div><div style="font-size:22px; font-weight:800; color:#dc2626; line-height:1;">${erros}</div><div style="font-size:11px; color:#64748b; font-weight:500; margin-top:3px;">Com Erro</div></div>
                </div>` : ''}
            </div>`;

        // ── Filter bar ─────────────────────────────────────────────────────
        const filterHtml = `
            <div style="background:#fff; border-radius:12px; padding:12px 16px; border:1px solid #e2e8f0; display:flex; align-items:center; gap:12px; flex-wrap:wrap; box-shadow:0 1px 3px rgba(15,23,42,0.05);">
                <div style="position:relative; flex:1; min-width:180px;">
                    <span style="position:absolute; left:10px; top:50%; transform:translateY(-50%); font-size:13px; pointer-events:none;">🔍</span>
                    <input id="notif-log-search" type="text" placeholder="Buscar por assunto ou destinatário..."
                        style="width:100%; padding:7px 10px 7px 32px; border:1px solid #e2e8f0; border-radius:8px; font-size:13px; color:#334155; outline:none; box-sizing:border-box; transition:border-color 0.15s;"
                        onfocus="this.style.borderColor='#3b82f6'" onblur="this.style.borderColor='#e2e8f0'"
                        oninput="window._filterNotifLog()">
                </div>
                <div style="display:flex; gap:6px; flex-wrap:wrap;">
                    <button class="notif-filter-btn" data-filter="all" onclick="window._notifLogFilter('all',this)"
                        style="padding:6px 14px; border-radius:20px; border:1px solid #3b82f6; background:#3b82f6; color:#fff; font-size:12px; font-weight:600; cursor:pointer; transition:all 0.15s;">
                        Todos (${total})</button>
                    <button class="notif-filter-btn" data-filter="enviado" onclick="window._notifLogFilter('enviado',this)"
                        style="padding:6px 14px; border-radius:20px; border:1px solid #e2e8f0; background:#fff; color:#64748b; font-size:12px; font-weight:600; cursor:pointer; transition:all 0.15s;">
                        ✅ Enviados (${enviados})</button>
                    ${erros > 0 ? `<button class="notif-filter-btn" data-filter="erro" onclick="window._notifLogFilter('erro',this)"
                        style="padding:6px 14px; border-radius:20px; border:1px solid #e2e8f0; background:#fff; color:#64748b; font-size:12px; font-weight:600; cursor:pointer; transition:all 0.15s;">
                        ❌ Erros (${erros})</button>` : ''}
                </div>
            </div>`;

        // ── Table ──────────────────────────────────────────────────────────
        const rowsHtml = logs.map((log, i) => {
            const dest = Array.isArray(log.destinatarios)
                ? log.destinatarios.join(', ')
                : (log.destinatarios || '—');
            const m = tipoMeta[log.tipo] || { label: log.tipo, icon: '📧', bg: '#f8fafc', color: '#64748b', border: '#e2e8f0' };
            const ok = log.status === 'enviado';
            const rowBg = ok ? (i % 2 === 0 ? '#fff' : '#f8fafc') : '#fff7f7';
            const searchData = esc((log.assunto || '') + ' ' + dest).toLowerCase();
            return `
                <tr class="notif-log-row" data-status="${log.status}" data-search="${searchData}"
                    style="background:${rowBg}; border-bottom:1px solid #f1f5f9; cursor:pointer;"
                    onclick="window._toggleNotifLogRow(this)"
                    onmouseover="this.style.background='${ok ? '#eff6ff' : '#fff1f1'}'"
                    onmouseout="this.style.background='${rowBg}'">
                    <td style="padding:11px 16px; white-space:nowrap; color:#64748b; font-size:12px; font-family:monospace;">${esc(log.enviado_em)}</td>
                    <td style="padding:11px 16px; white-space:nowrap;">
                        <span style="background:${m.bg}; color:${m.color}; border:1px solid ${m.border}; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700; display:inline-flex; align-items:center; gap:4px; white-space:nowrap;">${m.icon} ${m.label}</span>
                    </td>
                    <td style="padding:11px 16px; color:#1e293b; max-width:0; width:36%;">
                        <div style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${esc(log.assunto)}">${esc(log.assunto)}</div>
                    </td>
                    <td style="padding:11px 16px; color:#475569; font-size:12px; max-width:0; width:22%;">
                        <div style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${esc(dest)}">${esc(dest)}</div>
                    </td>
                    <td style="padding:11px 10px; text-align:center; white-space:nowrap;">
                        ${ok
                            ? '<span style="background:#dcfce7;color:#16a34a;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;display:inline-flex;align-items:center;gap:3px;">✓ Enviado</span>'
                            : '<span style="background:#fee2e2;color:#dc2626;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;display:inline-flex;align-items:center;gap:3px;">✗ Erro</span>'}
                    </td>
                </tr>
                <tr class="notif-log-expand" style="display:none; background:${ok ? '#f8fafc' : '#fff5f5'}; border-bottom:1px solid #e2e8f0;">
                    <td colspan="5" style="padding:12px 16px 14px 44px;">
                        <div style="display:grid; grid-template-columns:max-content 1fr; gap:6px 12px; align-items:start;">
                            <span style="color:#94a3b8; font-size:11px; font-weight:700; text-transform:uppercase; padding-top:2px;">Assunto:</span>
                            <span style="color:#334155; font-size:13px; line-height:1.5;">${esc(log.assunto)}</span>
                            <span style="color:#94a3b8; font-size:11px; font-weight:700; text-transform:uppercase; padding-top:2px;">Destinatários:</span>
                            <span style="color:#334155; font-size:13px; line-height:1.5;">${esc(dest)}</span>
                            ${log.referencia_data ? `
                            <span style="color:#94a3b8; font-size:11px; font-weight:700; text-transform:uppercase; padding-top:2px;">Referência:</span>
                            <span style="color:#334155; font-size:13px;">${esc(log.referencia_data)}</span>` : ''}
                            ${log.erro_detalhe ? `
                            <span style="color:#94a3b8; font-size:11px; font-weight:700; text-transform:uppercase; padding-top:4px;">Erro:</span>
                            <span style="color:#dc2626; font-size:12px; font-family:monospace; background:#fef2f2; padding:5px 10px; border-radius:6px; border:1px solid #fecaca; line-height:1.5;">${esc(log.erro_detalhe)}</span>` : ''}
                        </div>
                    </td>
                </tr>`;
        }).join('');

        const tableHtml = `
            <div style="background:#fff; border-radius:14px; border:1px solid #e2e8f0; overflow:hidden; box-shadow:0 1px 4px rgba(15,23,42,0.07);">
                <table style="width:100%; border-collapse:collapse; font-size:13px; table-layout:fixed;">
                    <colgroup>
                        <col style="width:130px">
                        <col style="width:175px">
                        <col>
                        <col style="width:200px">
                        <col style="width:110px">
                    </colgroup>
                    <thead>
                        <tr style="background:linear-gradient(135deg,#0f172a,#1e3a5f); color:#e2e8f0;">
                            <th style="padding:12px 16px; font-weight:600; text-align:left; font-size:12px; letter-spacing:0.04em;">🕐 Data/Hora</th>
                            <th style="padding:12px 16px; font-weight:600; text-align:left; font-size:12px; letter-spacing:0.04em;">Tipo</th>
                            <th style="padding:12px 16px; font-weight:600; text-align:left; font-size:12px; letter-spacing:0.04em;">Assunto</th>
                            <th style="padding:12px 16px; font-weight:600; text-align:left; font-size:12px; letter-spacing:0.04em;">Destinatário(s)</th>
                            <th style="padding:12px 10px; font-weight:600; text-align:center; font-size:12px; letter-spacing:0.04em;">Status</th>
                        </tr>
                    </thead>
                    <tbody id="notif-log-tbody">${rowsHtml}</tbody>
                </table>
                <div id="notif-log-empty-filter" style="display:none; text-align:center; padding:32px; color:#94a3b8;">
                    <div style="font-size:28px; margin-bottom:8px;">🔍</div>
                    <div style="font-size:13px;">Nenhum resultado para essa busca</div>
                </div>
            </div>`;

        container.style.cssText = 'display:flex; flex-direction:column; gap:14px;';
        container.innerHTML = statsHtml + filterHtml + tableHtml;

        // ── Interactivity helpers (closure over `logs`, `total`) ───────────
        let _currentFilter = 'all';

        function _applyFilters() {
            const tbody = document.getElementById('notif-log-tbody');
            if (!tbody) return;
            const searchVal = (document.getElementById('notif-log-search')?.value || '').toLowerCase().trim();
            const dataRows   = tbody.querySelectorAll('.notif-log-row');
            const expandRows = tbody.querySelectorAll('.notif-log-expand');
            let visible = 0;
            dataRows.forEach((r, i) => {
                const statusOk = _currentFilter === 'all' || r.dataset.status === _currentFilter;
                const searchOk = !searchVal || r.dataset.search.includes(searchVal);
                const show = statusOk && searchOk;
                r.style.display = show ? 'table-row' : 'none';
                if (expandRows[i]) expandRows[i].style.display = 'none';
                if (show) visible++;
            });
            const emptyEl   = document.getElementById('notif-log-empty-filter');
            const footerEl  = document.getElementById('notif-log-footer-count');
            if (emptyEl)  emptyEl.style.display  = visible === 0 ? 'block' : 'none';
            if (footerEl) footerEl.textContent    = `Exibindo ${visible} de ${total} registro${total !== 1 ? 's' : ''}`;
        }

        window._toggleNotifLogRow = function(row) {
            const tbody = document.getElementById('notif-log-tbody');
            if (!tbody) return;
            const dataRows   = Array.from(tbody.querySelectorAll('.notif-log-row'));
            const expandRows = tbody.querySelectorAll('.notif-log-expand');
            const idx = dataRows.indexOf(row);
            if (idx < 0 || !expandRows[idx]) return;
            const isOpen = expandRows[idx].style.display !== 'none';
            // Collapse all first, then open this one if it was closed
            expandRows.forEach(r => { r.style.display = 'none'; });
            if (!isOpen) expandRows[idx].style.display = 'table-row';
        };

        window._notifLogFilter = function(filter, btn) {
            _currentFilter = filter;
            document.querySelectorAll('.notif-filter-btn').forEach(b => {
                const active = b.dataset.filter === filter;
                b.style.background   = active ? '#3b82f6' : '#fff';
                b.style.borderColor  = active ? '#3b82f6' : '#e2e8f0';
                b.style.color        = active ? '#fff'    : '#64748b';
            });
            _applyFilters();
        };

        window._filterNotifLog = _applyFilters;

    } catch (err) {
        const container = document.getElementById('notif-log-content');
        if (container) container.innerHTML = `<div style="text-align:center;padding:40px;color:#ef4444;"><div style="font-size:32px;margin-bottom:10px;">❌</div><div>Erro de conexão: ${err.message}</div></div>`;
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
 * Editar sessão a partir da agenda (renomeado para evitar conflito com app.js e contratos.js)
 */
function editarSessaoAgenda(sessaoId) {
    console.log('📅 [Agenda] Editando sessão:', sessaoId);
    
    // Verificar se existe função global editarSessao (de modals.js ou app.js)
    if (typeof window.editarSessao === 'function') {
        window.editarSessao(sessaoId);
    } else if (typeof window.openModalSessao === 'function') {
        // Fallback: abrir modal de sessão com ID
        window.openModalSessao(sessaoId);
    } else {
        // Último recurso: redirecionar para a seção de contratos/sessões
        console.log('⚠️ Função de edição não encontrada, redirecionando...');
        showSection('contratos');
        setTimeout(() => {
            // Procurar o botão de edição da sessão
            const editBtn = document.querySelector(`[onclick*="editarSessao(${sessaoId})"]`);
            if (editBtn) {
                editBtn.click();
            } else {
                showNotification('📋 Carregando detalhes da sessão...', 'info');
            }
        }, 500);
    }
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
