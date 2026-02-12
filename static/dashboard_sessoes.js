/**
 * 📊 DASHBOARD DE SESSÕES - PARTE 9
 * ==================================================
 * Sistema completo de visualização de estatísticas e relatórios de sessões
 * 
 * Funcionalidades:
 * - Cards com métricas principais
 * - Gráficos de pizza (sessões por status)
 * - Tabela de top clientes
 * - Alertas de prazo
 * - Comparativo de períodos
 * 
 * Autor: Sistema Financeiro DWM
 * Data: 2026-02-08
 */

// ============================================================================
// CARREGAMENTO DE DADOS
// ============================================================================

/**
 * Carrega dados completos do dashboard
 */
async function carregarDashboardSessoes() {
    try {
        console.log('📊 [Dashboard Sessões] Carregando dados...');
        
        const response = await fetch('/api/sessoes/dashboard', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Erro ao carregar dashboard');
        }
        
        console.log('✅ Dashboard carregado:', data);
        
        // Renderizar componentes
        renderizarCardsPrincipais(data.estatisticas);
        renderizarGraficoPizza(data.estatisticas);
        renderizarTopClientes(data.top_clientes);
        renderizarAlertasPrazo(data.sessoes_atencao);
        renderizarEstatisticasPeriodo(data.periodo_atual);
        
        return data;
        
    } catch (error) {
        console.error('❌ Erro ao carregar dashboard:', error);
        showToast('Erro ao carregar dashboard de sessões', 'error');
        return null;
    }
}


/**
 * Carrega estatísticas de um período customizado
 */
async function carregarEstatisticasPeriodo(dataInicio, dataFim) {
    try {
        const url = `/api/sessoes/estatisticas?data_inicio=${dataInicio}&data_fim=${dataFim}`;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Erro ao carregar estatísticas');
        }
        
        return data.estatisticas;
        
    } catch (error) {
        console.error('❌ Erro ao carregar estatísticas:', error);
        showToast('Erro ao carregar estatísticas do período', 'error');
        return null;
    }
}


/**
 * Carrega comparativo entre dois períodos
 */
async function carregarComparativoPeriodos(p1Inicio, p1Fim, p2Inicio, p2Fim) {
    try {
        const url = `/api/sessoes/comparativo?p1_inicio=${p1Inicio}&p1_fim=${p1Fim}&p2_inicio=${p2Inicio}&p2_fim=${p2Fim}`;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Erro ao carregar comparativo');
        }
        
        return data;
        
    } catch (error) {
        console.error('❌ Erro ao carregar comparativo:', error);
        showToast('Erro ao carregar comparativo de períodos', 'error');
        return null;
    }
}


// ============================================================================
// RENDERIZAÇÃO - CARDS PRINCIPAIS
// ============================================================================

/**
 * Renderiza cards com métricas principais
 */
function renderizarCardsPrincipais(estatisticas) {
    const container = document.getElementById('dashboard-cards-principais');
    if (!container) return;
    
    const {
        total_geral = 0,
        total_concluidas = 0,
        total_em_andamento = 0,
        total_canceladas = 0,
        valor_total_ativo = 0,
        ticket_medio = 0,
        total_horas = 0,
        prazo_medio_dias = 0
    } = estatisticas;
    
    // Taxa de conclusão
    const taxaConclusao = total_geral > 0 
        ? ((total_concluidas / total_geral) * 100).toFixed(1)
        : 0;
    
    container.innerHTML = `
        <div class="stats-grid">
            <!-- Card 1: Total de Sessões -->
            <div class="stat-card stat-card-primary">
                <div class="stat-icon">📅</div>
                <div class="stat-content">
                    <div class="stat-label">Total de Sessões</div>
                    <div class="stat-value">${total_geral}</div>
                    <div class="stat-detail">${total_em_andamento} em andamento</div>
                </div>
            </div>
            
            <!-- Card 2: Taxa de Conclusão -->
            <div class="stat-card stat-card-success">
                <div class="stat-icon">✅</div>
                <div class="stat-content">
                    <div class="stat-label">Taxa de Conclusão</div>
                    <div class="stat-value">${taxaConclusao}%</div>
                    <div class="stat-detail">${total_concluidas} concluídas</div>
                </div>
            </div>
            
            <!-- Card 3: Faturamento Total -->
            <div class="stat-card stat-card-info">
                <div class="stat-icon">💰</div>
                <div class="stat-content">
                    <div class="stat-label">Faturamento Ativo</div>
                    <div class="stat-value">R$ ${formatarValor(valor_total_ativo)}</div>
                    <div class="stat-detail">Ticket médio: R$ ${formatarValor(ticket_medio)}</div>
                </div>
            </div>
            
            <!-- Card 4: Horas Trabalhadas -->
            <div class="stat-card stat-card-warning">
                <div class="stat-icon">⏱️</div>
                <div class="stat-content">
                    <div class="stat-label">Total de Horas</div>
                    <div class="stat-value">${total_horas || 0}h</div>
                    <div class="stat-detail">Prazo médio: ${Math.round(prazo_medio_dias || 0)} dias</div>
                </div>
            </div>
        </div>
    `;
}


// ============================================================================
// RENDERIZAÇÃO - GRÁFICO DE PIZZA
// ============================================================================

/**
 * Renderiza gráfico de pizza com distribuição por status
 * (Versão simplificada sem biblioteca externa)
 */
function renderizarGraficoPizza(estatisticas) {
    const container = document.getElementById('dashboard-grafico-pizza');
    if (!container) return;
    
    const {
        total_pendentes = 0,
        total_confirmadas = 0,
        total_em_andamento = 0,
        total_concluidas = 0,
        total_entregues = 0,
        total_canceladas = 0
    } = estatisticas;
    
    const dados = [
        { label: 'Pendentes', valor: total_pendentes, cor: '#FFA500', emoji: '⏳' },
        { label: 'Confirmadas', valor: total_confirmadas, cor: '#4169E1', emoji: '✓' },
        { label: 'Em Andamento', valor: total_em_andamento, cor: '#9370DB', emoji: '⚙️' },
        { label: 'Concluídas', valor: total_concluidas, cor: '#32CD32', emoji: '✅' },
        { label: 'Entregues', valor: total_entregues, cor: '#228B22', emoji: '📦' },
        { label: 'Canceladas', valor: total_canceladas, cor: '#DC143C', emoji: '❌' }
    ].filter(item => item.valor > 0);
    
    const total = dados.reduce((sum, item) => sum + item.valor, 0);
    
    if (total === 0) {
        container.innerHTML = '<div class="empty-state">Nenhuma sessão cadastrada</div>';
        return;
    }
    
    // Renderizar legenda com barras
    let html = '<div class="chart-legend">';
    
    dados.forEach(item => {
        const percentual = ((item.valor / total) * 100).toFixed(1);
        html += `
            <div class="legend-item">
                <div class="legend-bar" style="width: ${percentual}%; background-color: ${item.cor};">
                    <span class="legend-emoji">${item.emoji}</span>
                    <span class="legend-label">${item.label}</span>
                    <span class="legend-value">${item.valor} (${percentual}%)</span>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}


// ============================================================================
// RENDERIZAÇÃO - TOP CLIENTES
// ============================================================================

/**
 * Renderiza tabela com top 10 clientes
 */
function renderizarTopClientes(clientes) {
    const container = document.getElementById('dashboard-top-clientes');
    if (!container) return;
    
    if (!clientes || clientes.length === 0) {
        container.innerHTML = '<div class="empty-state">Nenhuma sessão com cliente cadastrada</div>';
        return;
    }
    
    let html = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Cliente</th>
                    <th>Sessões</th>
                    <th>Faturamento</th>
                    <th>Taxa Conclusão</th>
                    <th>Última Sessão</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    clientes.forEach((cliente, index) => {
        const taxaConclusao = cliente.taxa_conclusao_pct || 0;
        const corTaxa = taxaConclusao >= 80 ? 'green' : taxaConclusao >= 50 ? 'orange' : 'red';
        
        html += `
            <tr>
                <td>${index + 1}</td>
                <td><strong>${cliente.cliente_nome}</strong></td>
                <td>${cliente.total_sessoes}</td>
                <td>R$ ${formatarValor(cliente.valor_total)}</td>
                <td><span class="badge badge-${corTaxa}">${taxaConclusao}%</span></td>
                <td>${formatarData(cliente.ultima_sessao)}</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    container.innerHTML = html;
}


// ============================================================================
// RENDERIZAÇÃO - ALERTAS DE PRAZO
// ============================================================================

/**
 * Renderiza alertas de sessões com prazo próximo ou vencido
 */
function renderizarAlertasPrazo(sessoes) {
    const container = document.getElementById('dashboard-alertas-prazo');
    if (!container) return;
    
    if (!sessoes || sessoes.length === 0) {
        container.innerHTML = '<div class="empty-state success">✅ Nenhuma sessão requerendo atenção urgente</div>';
        return;
    }
    
    let html = '<div class="alerts-list">';
    
    sessoes.forEach(sessao => {
        const corUrgencia = sessao.urgencia === 'ATRASADO' ? 'danger' 
                          : sessao.urgencia.includes('HOJE') ? 'danger'
                          : 'warning';
        
        const iconeUrgencia = sessao.urgencia === 'ATRASADO' ? '🚨'
                            : sessao.urgencia.includes('HOJE') ? '⚠️'
                            : '⏰';
        
        html += `
            <div class="alert alert-${corUrgencia}">
                <div class="alert-icon">${iconeUrgencia}</div>
                <div class="alert-content">
                    <div class="alert-title">${sessao.cliente_nome}</div>
                    <div class="alert-details">
                        <span>📅 Data: ${formatarData(sessao.data)}</span>
                        <span>📆 Prazo: ${formatarData(sessao.prazo_entrega)}</span>
                        <span>💰 Valor: R$ ${formatarValor(sessao.valor_total)}</span>
                    </div>
                </div>
                <div class="alert-badge alert-badge-${corUrgencia}">
                    ${sessao.urgencia}
                    <br>
                    <small>(${sessao.dias_ate_prazo} dias)</small>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}


// ============================================================================
// RENDERIZAÇÃO - ESTATÍSTICAS DO PERÍODO
// ============================================================================

/**
 * Renderiza estatísticas detalhadas do período atual
 */
function renderizarEstatisticasPeriodo(periodo) {
    const container = document.getElementById('dashboard-periodo-atual');
    if (!container) return;
    
    if (!periodo || Object.keys(periodo).length === 0) {
        container.innerHTML = '<div class="empty-state">Nenhuma sessão no período</div>';
        return;
    }
    
    const {
        total_sessoes = 0,
        total_concluidas = 0,
        total_canceladas = 0,
        taxa_conclusao = 0,
        faturamento_total = 0,
        faturamento_entregue = 0,
        comissoes_total = 0,
        lucro_liquido = 0,
        ticket_medio = 0,
        total_horas = 0,
        clientes_unicos = 0
    } = periodo;
    
    container.innerHTML = `
        <div class="period-stats-grid">
            <div class="period-stat">
                <div class="period-stat-label">Total de Sessões</div>
                <div class="period-stat-value">${total_sessoes}</div>
            </div>
            <div class="period-stat">
                <div class="period-stat-label">Taxa de Conclusão</div>
                <div class="period-stat-value">${taxa_conclusao}%</div>
            </div>
            <div class="period-stat">
                <div class="period-stat-label">Faturamento Total</div>
                <div class="period-stat-value">R$ ${formatarValor(faturamento_total)}</div>
            </div>
            <div class="period-stat">
                <div class="period-stat-label">Lucro Líquido</div>
                <div class="period-stat-value">R$ ${formatarValor(lucro_liquido)}</div>
            </div>
            <div class="period-stat">
                <div class="period-stat-label">Ticket Médio</div>
                <div class="period-stat-value">R$ ${formatarValor(ticket_medio)}</div>
            </div>
            <div class="period-stat">
                <div class="period-stat-label">Clientes Únicos</div>
                <div class="period-stat-value">${clientes_unicos}</div>
            </div>
        </div>
    `;
}


// ============================================================================
// FUNÇÕES AUXILIARES
// ============================================================================

/**
 * Formata valor monetário
 */
function formatarValor(valor) {
    if (!valor) return '0,00';
    return parseFloat(valor).toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}


/**
 * Formata data no formato brasileiro
 */
function formatarData(data) {
    if (!data) return 'N/A';
    
    try {
        // String YYYY-MM-DD: formatar direto sem Date (evita bug timezone UTC-3)
        if (typeof data === 'string' && data.match(/^\d{4}-\d{2}-\d{2}/)) {
            const parts = data.substring(0, 10).split('-');
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
        const dataObj = new Date(data);
        return dataObj.toLocaleDateString('pt-BR');
    } catch (error) {
        return data;
    }
}


/**
 * Obtém token CSRF
 */
function getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.content : '';
}


// ============================================================================
// INICIALIZAÇÃO
// ============================================================================

/**
 * Inicializa o dashboard quando a seção for aberta
 */
function inicializarDashboardSessoes() {
    console.log('🚀 Inicializando Dashboard de Sessões...');
    carregarDashboardSessoes();
}


// Exportar funções para uso global
window.dashboardSessoes = {
    carregar: carregarDashboardSessoes,
    carregarEstatisticas: carregarEstatisticasPeriodo,
    carregarComparativo: carregarComparativoPeriodos,
    inicializar: inicializarDashboardSessoes
};

console.log('✅ Módulo Dashboard de Sessões carregado');
