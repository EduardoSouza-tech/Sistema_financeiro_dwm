/**
 * ===============================================
 * SISTEMA DE SUPORTE / CHAMADOS
 * ===============================================
 * Captura automática de console logs do navegador
 * Numeração auditável de chamados e protocolos
 */

// Buffer de logs do console capturados
const _consoleLogs = [];
const _MAX_LOGS = 200;

// Interceptar console.log, console.error, console.warn
(function() {
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;

    function captureLog(level, args) {
        const entry = {
            level: level,
            timestamp: new Date().toISOString(),
            message: Array.from(args).map(a => {
                try {
                    return typeof a === 'object' ? JSON.stringify(a) : String(a);
                } catch { return String(a); }
            }).join(' ')
        };
        _consoleLogs.push(entry);
        if (_consoleLogs.length > _MAX_LOGS) _consoleLogs.shift();
    }

    console.log = function() {
        captureLog('LOG', arguments);
        originalLog.apply(console, arguments);
    };
    console.error = function() {
        captureLog('ERROR', arguments);
        originalError.apply(console, arguments);
    };
    console.warn = function() {
        captureLog('WARN', arguments);
        originalWarn.apply(console, arguments);
    };

    // Capturar erros não tratados
    window.addEventListener('error', function(e) {
        captureLog('UNCAUGHT', [`${e.message} at ${e.filename}:${e.lineno}:${e.colno}`]);
    });
    window.addEventListener('unhandledrejection', function(e) {
        captureLog('PROMISE_REJECT', [e.reason]);
    });
})();


/**
 * Obter informações do navegador
 */
function getNavegadorInfo() {
    return JSON.stringify({
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        screenSize: `${screen.width}x${screen.height}`,
        windowSize: `${window.innerWidth}x${window.innerHeight}`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        cookiesEnabled: navigator.cookieEnabled,
        onLine: navigator.onLine
    });
}


/**
 * Abrir modal de suporte
 */
function abrirModalSuporte() {
    const modal = document.getElementById('modal-suporte');
    if (!modal) return;

    // Limpar formulário
    document.getElementById('suporte-titulo').value = '';
    document.getElementById('suporte-descricao').value = '';
    document.getElementById('suporte-prioridade').value = 'media';
    document.getElementById('suporte-resultado').style.display = 'none';
    document.getElementById('suporte-form-content').style.display = 'block';

    // Atualizar preview dos console logs
    atualizarPreviewLogs();

    modal.style.display = 'flex';
}


/**
 * Fechar modal de suporte
 */
function fecharModalSuporte() {
    const modal = document.getElementById('modal-suporte');
    if (modal) modal.style.display = 'none';
}


/**
 * Atualizar preview dos logs capturados no modal
 */
function atualizarPreviewLogs() {
    const container = document.getElementById('suporte-console-preview');
    if (!container) return;

    const recentLogs = _consoleLogs.slice(-50);
    if (recentLogs.length === 0) {
        container.innerHTML = '<div style="color: #999; text-align: center; padding: 20px;">Nenhum log capturado ainda</div>';
        return;
    }

    container.innerHTML = recentLogs.map(log => {
        let color = '#ccc';
        let icon = '📝';
        if (log.level === 'ERROR' || log.level === 'UNCAUGHT') { color = '#ff6b6b'; icon = '❌'; }
        else if (log.level === 'WARN') { color = '#ffa500'; icon = '⚠️'; }
        else if (log.level === 'PROMISE_REJECT') { color = '#ff4757'; icon = '💥'; }

        const time = log.timestamp.split('T')[1].split('.')[0];
        const msg = log.message.length > 200 ? log.message.substring(0, 200) + '...' : log.message;
        const escapedMsg = msg.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return `<div style="padding: 3px 6px; border-left: 3px solid ${color}; margin-bottom: 2px; font-size: 11px; font-family: monospace; word-break: break-all;">
            <span style="color: #888;">${time}</span> ${icon} <span style="color: ${color};">[${log.level}]</span> ${escapedMsg}
        </div>`;
    }).join('');

    container.scrollTop = container.scrollHeight;
}


/**
 * Enviar chamado de suporte
 */
async function enviarChamadoSuporte() {
    const titulo = document.getElementById('suporte-titulo').value.trim();
    const descricao = document.getElementById('suporte-descricao').value.trim();
    const prioridade = document.getElementById('suporte-prioridade').value;

    if (!titulo || !descricao) {
        showNotification('⚠️ Preencha o título e a descrição do problema', 'warning');
        return;
    }

    const btnEnviar = document.getElementById('btn-enviar-chamado');
    btnEnviar.disabled = true;
    btnEnviar.textContent = '⏳ Enviando...';

    try {
        const consoleLogs = JSON.stringify(_consoleLogs.slice(-100));
        const navegadorInfo = getNavegadorInfo();

        const response = await fetch('/api/suporte/chamados', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                titulo,
                descricao,
                prioridade,
                console_logs: consoleLogs,
                navegador_info: navegadorInfo,
                url_pagina: window.location.href
            })
        });

        const data = await response.json();
        if (data.success) {
            // Mostrar resultado com número e protocolo
            document.getElementById('suporte-form-content').style.display = 'none';
            const resultado = document.getElementById('suporte-resultado');
            resultado.style.display = 'block';
            resultado.innerHTML = `
                <div style="text-align: center; padding: 30px;">
                    <div style="font-size: 60px; margin-bottom: 15px;">✅</div>
                    <h3 style="color: #27ae60; margin-bottom: 20px;">Chamado Aberto com Sucesso!</h3>
                    
                    <div style="background: #f8f9fa; border-radius: 10px; padding: 20px; margin: 15px 0; border: 2px solid #e9ecef;">
                        <div style="margin-bottom: 15px;">
                            <span style="color: #666; font-size: 12px;">NÚMERO DO CHAMADO</span><br>
                            <span style="font-size: 22px; font-weight: bold; color: #2c3e50; letter-spacing: 1px;">${data.chamado.numero_chamado}</span>
                        </div>
                        <div style="border-top: 1px solid #dee2e6; padding-top: 15px;">
                            <span style="color: #666; font-size: 12px;">PROTOCOLO</span><br>
                            <span style="font-size: 22px; font-weight: bold; color: #e74c3c; letter-spacing: 1px;">${data.chamado.protocolo}</span>
                        </div>
                    </div>
                    
                    <p style="color: #666; font-size: 13px; margin-top: 15px;">
                        📋 Guarde o número do protocolo para acompanhamento.<br>
                        Nossa equipe analisará seu chamado em breve.
                    </p>
                    
                    <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: center;">
                        <button onclick="copiarProtocolo('${data.chamado.protocolo}')" 
                            style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">
                            📋 Copiar Protocolo
                        </button>
                        <button onclick="fecharModalSuporte()" 
                            style="padding: 10px 20px; background: #6c757d; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">
                            Fechar
                        </button>
                    </div>
                </div>
            `;
            showNotification('✅ Chamado criado com sucesso!', 'success');
        } else {
            showNotification('❌ ' + (data.error || 'Erro ao criar chamado'), 'error');
        }
    } catch (error) {
        console.error('Erro ao enviar chamado:', error);
        showNotification('❌ Erro ao enviar chamado. Tente novamente.', 'error');
    } finally {
        btnEnviar.disabled = false;
        btnEnviar.textContent = '📨 Enviar Chamado';
    }
}


/**
 * Copiar protocolo para clipboard
 */
function copiarProtocolo(protocolo) {
    navigator.clipboard.writeText(protocolo).then(() => {
        showNotification('📋 Protocolo copiado!', 'success');
    }).catch(() => {
        // Fallback
        const input = document.createElement('input');
        input.value = protocolo;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
        showNotification('📋 Protocolo copiado!', 'success');
    });
}


/**
 * Ver meus chamados (lista para o usuário)
 */
async function verMeusChamados() {
    document.getElementById('suporte-form-content').style.display = 'none';
    document.getElementById('suporte-resultado').style.display = 'block';

    const resultado = document.getElementById('suporte-resultado');
    resultado.innerHTML = '<div style="text-align: center; padding: 30px;"><div class="spinner"></div><p>Carregando chamados...</p></div>';

    try {
        const response = await fetch('/api/suporte/chamados', { credentials: 'include' });
        const data = await response.json();

        if (!data.success || !data.chamados.length) {
            resultado.innerHTML = `
                <div style="text-align: center; padding: 30px; color: #999;">
                    <div style="font-size: 50px; margin-bottom: 10px;">📭</div>
                    <p>Nenhum chamado encontrado</p>
                    <button onclick="voltarFormSuporte()" style="margin-top: 15px; padding: 8px 20px; background: #3498db; color: white; border: none; border-radius: 6px; cursor: pointer;">
                        ← Voltar
                    </button>
                </div>`;
            return;
        }

        let html = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="margin: 0;">📋 Meus Chamados</h3>
                <button onclick="voltarFormSuporte()" style="padding: 6px 15px; background: #6c757d; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 12px;">
                    ← Voltar
                </button>
            </div>
        `;

        data.chamados.forEach(c => {
            const statusConfig = {
                'aberto': { cor: '#ffe0e0', corTexto: '#c0392b', label: '🔴 Aberto', bordaCor: '#e74c3c' },
                'em_andamento': { cor: '#fff3cd', corTexto: '#856404', label: '🟡 Em Andamento', bordaCor: '#f39c12' },
                'resolvido': { cor: '#d4edda', corTexto: '#155724', label: '🟢 Resolvido', bordaCor: '#27ae60' }
            };
            const st = statusConfig[c.status] || statusConfig['aberto'];
            const dataFormatada = new Date(c.created_at).toLocaleDateString('pt-BR') + ' ' + new Date(c.created_at).toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'});

            html += `
                <div style="background: ${st.cor}; border-left: 4px solid ${st.bordaCor}; border-radius: 8px; padding: 15px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <strong style="color: ${st.corTexto};">${c.numero_chamado}</strong>
                            <span style="background: ${st.bordaCor}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-left: 8px;">${st.label}</span>
                            <div style="font-weight: bold; margin-top: 5px; color: #2c3e50;">${c.titulo}</div>
                            <div style="color: #666; font-size: 12px; margin-top: 3px;">Protocolo: <strong>${c.protocolo}</strong></div>
                        </div>
                        <div style="text-align: right; color: #888; font-size: 11px;">
                            ${dataFormatada}
                        </div>
                    </div>
                    ${c.resposta_admin ? `<div style="margin-top: 10px; padding: 10px; background: rgba(255,255,255,0.7); border-radius: 6px; font-size: 12px;">
                        <strong>💬 Resposta:</strong> ${c.resposta_admin}
                    </div>` : ''}
                </div>
            `;
        });

        resultado.innerHTML = html;
    } catch (error) {
        resultado.innerHTML = '<div style="text-align: center; padding: 30px; color: #e74c3c;">❌ Erro ao carregar chamados</div>';
    }
}


/**
 * Voltar para o formulário de suporte
 */
function voltarFormSuporte() {
    document.getElementById('suporte-resultado').style.display = 'none';
    document.getElementById('suporte-form-content').style.display = 'block';
}
