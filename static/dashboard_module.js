/**
 * =================================================================
 * MÓDULO DASHBOARD GERENCIAL
 * Data: 19/02/2026
 * =================================================================
 */

// ===== VARIÁVEIS GLOBAIS =====
window.dashboardData = null;
window.dashboardCharts = {};

// ===== INICIALIZAÇÃO DO MÓDULO DASHBOARD =====

window.inicializarModuloDashboard = async function() {
    console.log('📊 Inicializando Módulo Dashboard Gerencial...');
    
    // Configurar mês padrão (mês atual)
    const hoje = new Date();
    document.getElementById('dashboardMesReferencia').value = formatarMesInput(hoje);
    
    // Carregar versões do plano de contas
    await carregarVersoesDashboard();
    
    // Carregar dashboard automaticamente
    await carregarDashboardGerencial();
    
    console.log('✅ Módulo Dashboard inicializado');
};

/**
 * Carregar dropdown de versões do plano de contas
 */
async function carregarVersoesDashboard() {
    try {
        const response = await fetch('/api/contabilidade/versoes', { credentials: 'include' });
        const data = await response.json();
        
        if (data.success && data.versoes) {
            const select = document.getElementById('dashboardVersaoPlano');
            select.innerHTML = '<option value="">Todas as versões</option>';
            
            data.versoes.forEach(v => {
                const opt = document.createElement('option');
                opt.value = v.id;
                opt.textContent = `${v.nome_versao} (${v.exercicio_fiscal})${v.is_ativa ? ' ★' : ''}`;
                if (v.is_ativa) opt.selected = true;
                select.appendChild(opt);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar versões:', error);
    }
}

/**
 * Formatar mês para input type="month" (YYYY-MM)
 */
function formatarMesInput(data) {
    const ano = data.getFullYear();
    const mes = String(data.getMonth() + 1).padStart(2, '0');
    return `${ano}-${mes}`;
}

/**
 * Formatar moeda brasileira
 */
function formatarMoeda(valor) {
    if (typeof valor !== 'number' || isNaN(valor)) {
        valor = 0;
    }
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

/**
 * Formatar moeda compacta (K, M)
 */
function formatarMoedaCompacta(valor) {
    if (Math.abs(valor) >= 1000000) {
        return `R$ ${(valor / 1000000).toFixed(1)}M`;
    } else if (Math.abs(valor) >= 1000) {
        return `R$ ${(valor / 1000).toFixed(1)}K`;
    }
    return formatarMoeda(valor);
}

// ===== CARREGAR DASHBOARD =====

window.carregarDashboardGerencial = async function() {
    try {
        // Obter parâmetros
        const mesRef = document.getElementById('dashboardMesReferencia').value;
        const versaoPlanoId = document.getElementById('dashboardVersaoPlano').value || null;
        
        if (!mesRef) {
            showToast('❌ Selecione o mês de referência', 'error');
            return;
        }
        
        // Converter mês para data_referencia (último dia do mês)
        const [ano, mes] = mesRef.split('-');
        const ultimoDiaMes = new Date(ano, mes, 0).getDate();
        const dataReferencia = `${ano}-${mes}-${ultimoDiaMes}`;
        
        // Mostrar loading
        document.getElementById('dashboardResultado').innerHTML = '<div style="text-align:center; padding: 60px;"><div class="spinner"></div><p>Carregando dashboard...</p></div>';
        document.getElementById('dashboardResultado').style.display = 'block';
        
        // Fazer requisição
        const url = new URL('/api/dashboard/gerencial', window.location.origin);
        url.searchParams.append('data_referencia', dataReferencia);
        if (versaoPlanoId) {
            url.searchParams.append('versao_plano_id', versaoPlanoId);
        }
        
        const response = await fetch(url, {
            method: 'GET',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (!data.success) {
            showToast('❌ Erro ao carregar dashboard: ' + (data.error || 'Erro desconhecido'), 'error');
            document.getElementById('dashboardResultado').innerHTML = '<p style="text-align:center; color: #e74c3c; padding: 40px;">Erro ao carregar dados</p>';
            return;
        }
        
        // Armazenar dados
        window.dashboardData = data;
        
        // Renderizar Dashboard
        renderizarDashboard(data);
        
        // Carregar gráficos (com delay para garantir que o DOM foi renderizado)
        setTimeout(() => {
            carregarGraficoEvolucao(data.dashboard.evolucao_mensal);
            carregarGraficoPontoEquilibrio(data.dashboard.ponto_equilibrio, data.dashboard.kpis);
        }, 100);
        
        showToast('✅ Dashboard carregado com sucesso!', 'success');
        
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
        showToast('❌ Erro ao carregar dashboard', 'error');
        document.getElementById('dashboardResultado').innerHTML = '<p style="text-align:center; color: #e74c3c; padding: 40px;">Erro ao conectar com o servidor</p>';
    }
};

// ===== RENDERIZAR DASHBOARD =====

function renderizarDashboard(data) {
    const dashboard = data.dashboard;
    const kpis = dashboard.kpis;
    const pontoEquilibrio = dashboard.ponto_equilibrio;
    
    // Ícones de tendência
    const iconeTendencia = (tendencia) => {
        if (tendencia === 'positiva') return '📈';
        if (tendencia === 'negativa') return '📉';
        return '➡️';
    };
    
    // Cor da tendência
    const corTendencia = (tendencia) => {
        if (tendencia === 'positiva') return '#27ae60';
        if (tendencia === 'negativa') return '#e74c3c';
        return '#95a5a6';
    };
    
    let html = `
        <div class="dashboard-container" style="background: #ecf0f1; padding: 20px; border-radius: 12px;">
            
            <!-- CABEÇALHO -->
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color: #2c3e50; margin: 0;">📊 DASHBOARD GERENCIAL</h2>
                <p style="color: #7f8c8d; margin: 10px 0 0 0;">
                    ${dashboard.mes_referencia}
                </p>
            </div>
            
            <!-- GRID DE KPIs -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px;">
                
                <!-- KPI: RECEITA DO MÊS -->
                <div class="kpi-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <span style="font-size: 16px; opacity: 0.9;">💰 Receita do Mês</span>
                        <span style="font-size: 24px;">${iconeTendencia(kpis.receita_mes.tendencia)}</span>
                    </div>
                    <div style="font-size: 32px; font-weight: bold; margin-bottom: 10px;">
                        ${formatarMoedaCompacta(kpis.receita_mes.valor)}
                    </div>
                    <div style="font-size: 14px; opacity: 0.9;">
                        ${kpis.receita_mes.variacao_percentual >= 0 ? '+' : ''}${kpis.receita_mes.variacao_percentual.toFixed(2)}% vs mês anterior
                    </div>
                </div>
                
                <!-- KPI: DESPESAS DO MÊS -->
                <div class="kpi-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 25px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <span style="font-size: 16px; opacity: 0.9;">💸 Despesas do Mês</span>
                        <span style="font-size: 24px;">📊</span>
                    </div>
                    <div style="font-size: 32px; font-weight: bold; margin-bottom: 10px;">
                        ${formatarMoedaCompacta(kpis.despesas_mes.valor)}
                    </div>
                    <div style="font-size: 14px; opacity: 0.9;">
                        ${kpis.despesas_mes.percentual_receita.toFixed(2)}% da receita
                    </div>
                </div>
                
                <!-- KPI: LUCRO LÍQUIDO -->
                <div class="kpi-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 25px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <span style="font-size: 16px; opacity: 0.9;">${kpis.lucro_liquido_mes.valor >= 0 ? '✅' : '❌'} Lucro Líquido</span>
                        <span style="font-size: 24px;">${iconeTendencia(kpis.lucro_liquido_mes.tendencia)}</span>
                    </div>
                    <div style="font-size: 32px; font-weight: bold; margin-bottom: 10px;">
                        ${formatarMoedaCompacta(kpis.lucro_liquido_mes.valor)}
                    </div>
                    <div style="font-size: 14px; opacity: 0.9;">
                        ${kpis.lucro_liquido_mes.variacao_percentual >= 0 ? '+' : ''}${kpis.lucro_liquido_mes.variacao_percentual.toFixed(2)}% vs mês anterior
                    </div>
                </div>
                
                <!-- KPI: MARGEM LÍQUIDA -->
                <div class="kpi-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 25px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(67, 233, 123, 0.4);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <span style="font-size: 16px; opacity: 0.9;">📊 Margem Líquida</span>
                        <span style="font-size: 24px;">%</span>
                    </div>
                    <div style="font-size: 32px; font-weight: bold; margin-bottom: 10px;">
                        ${kpis.margem_liquida.percentual.toFixed(2)}%
                    </div>
                    <div style="font-size: 14px; opacity: 0.9;">
                        Status: ${kpis.margem_liquida.status === 'excelente' ? '🌟 Excelente' : 
                                 kpis.margem_liquida.status === 'bom' ? '👍 Bom' : 
                                 kpis.margem_liquida.status === 'atencao' ? '⚠️ Atenção' : '🚨 Crítico'}
                    </div>
                </div>
                
            </div>
            
            <!-- GRÁFICOS -->
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 30px;">
                
                <!-- GRÁFICO: EVOLUÇÃO MENSAL -->
                <div style="background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h3 style="color: #2c3e50; margin: 0 0 20px 0; font-size: 18px;">📈 Evolução Mensal (12 meses)</h3>
                    <canvas id="graficoEvolucaoMensal" width="600" height="300"></canvas>
                </div>
                
                <!-- PONTO DE EQUILÍBRIO -->
                <div style="background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h3 style="color: #2c3e50; margin: 0 0 20px 0; font-size: 18px;">⚖️ Ponto de Equilíbrio</h3>
                    
                    <canvas id="graficoPontoEquilibrio" width="250" height="250"></canvas>
                    
                    <div style="margin-top: 20px; font-size: 14px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span style="color: #7f8c8d;">Valor de equilíbrio:</span>
                            <strong>${formatarMoedaCompacta(pontoEquilibrio.valor)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span style="color: #7f8c8d;">Percentual atingido:</span>
                            <strong style="color: ${pontoEquilibrio.atingiu ? '#27ae60' : '#e74c3c'};">
                                ${pontoEquilibrio.percentual_atingido.toFixed(1)}%
                            </strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span style="color: #7f8c8d;">Falta para equilíbrio:</span>
                            <strong>${formatarMoedaCompacta(pontoEquilibrio.falta_para_equilibrio)}</strong>
                        </div>
                        
                        ${pontoEquilibrio.atingiu ? 
                            '<div style="margin-top: 15px; padding: 12px; background: #d5f4e6; border-radius: 8px; color: #27ae60; text-align: center; font-weight: bold;">✅ Ponto de equilíbrio atingido!</div>' :
                            '<div style="margin-top: 15px; padding: 12px; background: #fadbd8; border-radius: 8px; color: #e74c3c; text-align: center; font-weight: bold;">⚠️ Abaixo do ponto de equilíbrio</div>'
                        }
                    </div>
                </div>
                
            </div>
            
            <!-- DETALHES ADICIONAIS -->
            <div style="background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h3 style="color: #2c3e50; margin: 0 0 20px 0; font-size: 18px;">📋 Análise Detalhada</h3>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div style="padding: 15px; background: #f8f9fa; border-radius: 8px;">
                        <div style="font-size: 12px; color: #7f8c8d; margin-bottom: 5px;">Custos Fixos</div>
                        <div style="font-size: 20px; font-weight: bold; color: #e74c3c;">${formatarMoedaCompacta(pontoEquilibrio.custos_fixos)}</div>
                    </div>
                    <div style="padding: 15px; background: #f8f9fa; border-radius: 8px;">
                        <div style="font-size: 12px; color: #7f8c8d; margin-bottom: 5px;">Margem de Contribuição</div>
                        <div style="font-size: 20px; font-weight: bold; color: #3498db;">${pontoEquilibrio.margem_contribuicao_percentual.toFixed(2)}%</div>
                    </div>
                    <div style="padding: 15px; background: #f8f9fa; border-radius: 8px;">
                        <div style="font-size: 12px; color: #7f8c8d; margin-bottom: 5px;">Receita Mês Anterior</div>
                        <div style="font-size: 20px; font-weight: bold; color: #95a5a6;">${formatarMoedaCompacta(dashboard.comparacao.mes_anterior.receita)}</div>
                    </div>
                    <div style="padding: 15px; background: #f8f9fa; border-radius: 8px;">
                        <div style="font-size: 12px; color: #7f8c8d; margin-bottom: 5px;">Lucro Mês Anterior</div>
                        <div style="font-size: 20px; font-weight: bold; color: #95a5a6;">${formatarMoedaCompacta(dashboard.comparacao.mes_anterior.lucro)}</div>
                    </div>
                </div>
            </div>
            
        </div>
    `;
    
    document.getElementById('dashboardResultado').innerHTML = html;
}

// ===== GRÁFICOS COM CHART.JS =====

/**
 * Carregar gráfico de evolução mensal
 */
function carregarGraficoEvolucao(evolucaoMensal) {
    const canvas = document.getElementById('graficoEvolucaoMensal');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destruir gráfico anterior se existir
    if (window.dashboardCharts.evolucao) {
        window.dashboardCharts.evolucao.destroy();
    }
    
    // Verificar se Chart.js está disponível
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js não carregado. Gráfico não será exibido.');
        ctx.fillStyle = '#7f8c8d';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Chart.js não carregado', canvas.width / 2, canvas.height / 2);
        return;
    }
    
    const labels = evolucaoMensal.map(m => m.mes_nome);
    const receitas = evolucaoMensal.map(m => m.receita);
    const despesas = evolucaoMensal.map(m => m.despesas);
    const lucros = evolucaoMensal.map(m => m.lucro_liquido);
    
    window.dashboardCharts.evolucao = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Receita',
                    data: receitas,
                    borderColor: '#27ae60',
                    backgroundColor: 'rgba(39, 174, 96, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Despesas',
                    data: despesas,
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Lucro Líquido',
                    data: lucros,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatarMoeda(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatarMoedaCompacta(value);
                        }
                    }
                }
            }
        }
    });
}

/**
 * Carregar gráfico de ponto de equilíbrio (doughnut)
 */
function carregarGraficoPontoEquilibrio(pontoEquilibrio, kpis) {
    const canvas = document.getElementById('graficoPontoEquilibrio');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destruir gráfico anterior se existir
    if (window.dashboardCharts.pontoEquilibrio) {
        window.dashboardCharts.pontoEquilibrio.destroy();
    }
    
    // Verificar se Chart.js está disponível
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js não carregado. Gráfico não será exibido.');
        ctx.fillStyle = '#7f8c8d';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Chart.js não carregado', canvas.width / 2, canvas.height / 2);
        return;
    }
    
    const receitaAtual = kpis.receita_mes.valor;
    const pontoEq = pontoEquilibrio.valor;
    const percentualAtingido = Math.min(pontoEquilibrio.percentual_atingido, 100);
    const faltante = Math.max(100 - percentualAtingido, 0);
    
    window.dashboardCharts.pontoEquilibrio = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Atingido', 'Faltante'],
            datasets: [{
                data: [percentualAtingido, faltante],
                backgroundColor: [
                    pontoEquilibrio.atingiu ? '#27ae60' : '#f39c12',
                    '#ecf0f1'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '70%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed.toFixed(1) + '%';
                        }
                    }
                }
            }
        }
    });
}

console.log('✅ Módulo Dashboard Gerencial carregado');
