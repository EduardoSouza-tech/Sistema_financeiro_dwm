/**
 * =================================================================
 * MÓDULO DRE (Demonstração do Resultado do Exercício)
 * Data: 19/02/2026
 * =================================================================
 */

// ===== VARIÁVEIS GLOBAIS =====
window.dreData = null;
window.drePeriodoAtual = null;

// ===== FUNÇÕES AUXILIARES =====

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
 * Formatar percentual
 */
function formatarPercentual(valor) {
    if (typeof valor !== 'number' || isNaN(valor)) {
        valor = 0;
    }
    const sinal = valor >= 0 ? '+' : '';
    return `${sinal}${valor.toFixed(2)}%`;
}

// ===== INICIALIZAÇÃO DO MÓDULO DRE =====

window.inicializarModuloDRE = async function() {
    console.log('📈 Inicializando Módulo DRE...');
    
    // Configurar período padrão (mês atual)
    const hoje = new Date();
    const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    const ultimoDia = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0);
    
    document.getElementById('dreDataInicio').value = formatarDataInput(primeiroDia);
    document.getElementById('dreDataFim').value = formatarDataInput(ultimoDia);
    
    // Carregar versões do plano de contas
    await carregarVersoesDRE();
    
    // Configurar botões de período rápido
    configurarBotoesPeriodoDRE();
    
    console.log('✅ Módulo DRE inicializado');
};

/**
 * Carregar dropdown de versões do plano de contas
 */
async function carregarVersoesDRE() {
    try {
        const response = await fetch('/api/contabilidade/versoes', { credentials: 'include' });
        const data = await response.json();
        
        if (data.success && data.versoes) {
            const select = document.getElementById('dreVersaoPlano');
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
 * Configurar botões de seleção rápida de período
 */
function configurarBotoesPeriodoDRE() {
    // Mês atual
    document.getElementById('drePeriodoMesAtual')?.addEventListener('click', () => {
        const hoje = new Date();
        const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
        const ultimoDia = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0);
        
        document.getElementById('dreDataInicio').value = formatarDataInput(primeiroDia);
        document.getElementById('dreDataFim').value = formatarDataInput(ultimoDia);
    });
    
    // Mês anterior
    document.getElementById('drePeriodoMesAnterior')?.addEventListener('click', () => {
        const hoje = new Date();
        const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth() - 1, 1);
        const ultimoDia = new Date(hoje.getFullYear(), hoje.getMonth(), 0);
        
        document.getElementById('dreDataInicio').value = formatarDataInput(primeiroDia);
        document.getElementById('dreDataFim').value = formatarDataInput(ultimoDia);
    });
    
    // Trimestre atual
    document.getElementById('drePeriodoTrimestre')?.addEventListener('click', () => {
        const hoje = new Date();
        const mesAtual = hoje.getMonth();
        const trimestreInicio = Math.floor(mesAtual / 3) * 3;
        
        const primeiroDia = new Date(hoje.getFullYear(), trimestreInicio, 1);
        const ultimoDia = new Date(hoje.getFullYear(), trimestreInicio + 3, 0);
        
        document.getElementById('dreDataInicio').value = formatarDataInput(primeiroDia);
        document.getElementById('dreDataFim').value = formatarDataInput(ultimoDia);
    });
    
    // Ano atual
    document.getElementById('drePeriodoAnoAtual')?.addEventListener('click', () => {
        const hoje = new Date();
        const primeiroDia = new Date(hoje.getFullYear(), 0, 1);
        const ultimoDia = new Date(hoje.getFullYear(), 11, 31);
        
        document.getElementById('dreDataInicio').value = formatarDataInput(primeiroDia);
        document.getElementById('dreDataFim').value = formatarDataInput(ultimoDia);
    });
}

/**
 * Formatar data para input type="date"
 */
function formatarDataInput(data) {
    const ano = data.getFullYear();
    const mes = String(data.getMonth() + 1).padStart(2, '0');
    const dia = String(data.getDate()).padStart(2, '0');
    return `${ano}-${mes}-${dia}`;
}

// ===== GERAR DRE =====

window.gerarDRECompleta = async function() {
    try {
        // Obter parâmetros
        const dataInicio = document.getElementById('dreDataInicio').value;
        const dataFim = document.getElementById('dreDataFim').value;
        const versaoPlanoId = document.getElementById('dreVersaoPlano').value || null;
        const comparar = document.getElementById('dreCompararPeriodo')?.checked || false;
        
        if (!dataInicio || !dataFim) {
            showToast('❌ Selecione o período', 'error');
            return;
        }
        
        // Mostrar loading
        document.getElementById('dreResultado').innerHTML = '<div style="text-align:center; padding: 40px;"><div class="spinner"></div><p>Gerando DRE...</p></div>';
        document.getElementById('dreResultado').style.display = 'block';
        
        // Fazer requisição
        const response = await fetch('/api/relatorios/dre', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                data_inicio: dataInicio,
                data_fim: dataFim,
                versao_plano_id: versaoPlanoId ? parseInt(versaoPlanoId) : null,
                comparar_periodo_anterior: comparar
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            showToast('❌ Erro ao gerar DRE: ' + (data.error || 'Erro desconhecido'), 'error');
            document.getElementById('dreResultado').innerHTML = '';
            return;
        }
        
        // Armazenar dados
        window.dreData = data;
        window.drePeriodoAtual = { dataInicio, dataFim };
        
        // Renderizar DRE
        renderizarDRE(data);
        
        showToast('✅ DRE gerada com sucesso!', 'success');
        
    } catch (error) {
        console.error('Erro ao gerar DRE:', error);
        showToast('❌ Erro ao gerar DRE', 'error');
        document.getElementById('dreResultado').innerHTML = '';
    }
};

// ===== RENDERIZAR DRE =====

function renderizarDRE(data) {
    const dre = data.dre;
    const periodo = data.periodo;
    const indicadores = data.indicadores;
    const temComparativo = !!data.dre_anterior;
    
    let html = `
        <div class="dre-container" style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            
            <!-- CABEÇALHO -->
            <div style="text-align: center; margin-bottom: 30px; border-bottom: 3px solid #3498db; padding-bottom: 20px;">
                <h2 style="color: #2c3e50; margin: 0;">📈 DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO</h2>
                <p style="color: #7f8c8d; margin: 10px 0 0 0;">
                    Período: ${formatarDataBR(periodo.data_inicio)} a ${formatarDataBR(periodo.data_fim)}
                </p>
            </div>
            
            <!-- INDICADORES RESUMO -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px;">
                <div class="kpi-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">Margem Bruta</div>
                    <div style="font-size: 28px; font-weight: bold;">${indicadores.margem_bruta.toFixed(2)}%</div>
                </div>
                <div class="kpi-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">Margem Operacional</div>
                    <div style="font-size: 28px; font-weight: bold;">${indicadores.margem_operacional.toFixed(2)}%</div>
                </div>
                <div class="kpi-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">Margem Líquida</div>
                    <div style="font-size: 28px; font-weight: bold;">${indicadores.margem_liquida.toFixed(2)}%</div>
                </div>
            </div>
            
            <!-- TABELA DRE -->
            <table class="dre-table" style="width: 100%; border-collapse: collapse; font-family: 'Courier New', monospace; font-size: 13px;">
                <thead>
                    <tr style="background: #ecf0f1; border-bottom: 2px solid #bdc3c7;">
                        <th style="text-align: left; padding: 12px; font-weight: bold;">DESCRIÇÃO</th>
                        <th style="text-align: right; padding: 12px; font-weight: bold; width: 150px;">VALOR (R$)</th>
                        <th style="text-align: right; padding: 12px; font-weight: bold; width: 100px;">% RECEITA</th>
                        ${temComparativo ? '<th style="text-align: right; padding: 12px; font-weight: bold; width: 100px;">VARIAÇÃO</th>' : ''}
                    </tr>
                </thead>
                <tbody>`;
    
    // 1. RECEITA BRUTA
    html += renderizarLinhaDRE('RECEITA BRUTA', dre.receita_bruta.total, dre.receita_bruta.percentual, true, '#27ae60');
    if (dre.receita_bruta.itens && dre.receita_bruta.itens.length > 0) {
        dre.receita_bruta.itens.forEach(item => {
            html += renderizarLinhaDetalheDRE(item.descricao, item.valor);
        });
    }
    
    // 2. DEDUÇÕES
    html += renderizarLinhaDRE('(-) DEDUÇÕES DA RECEITA', dre.deducoes.total, dre.deducoes.percentual, false, '#e74c3c');
    if (dre.deducoes.itens && dre.deducoes.itens.length > 0) {
        dre.deducoes.itens.forEach(item => {
            html += renderizarLinhaDetalheDRE(item.descricao, item.valor);
        });
    }
    
    // 3. RECEITA LÍQUIDA
    html += renderizarLinhaDRE('= RECEITA LÍQUIDA', dre.receita_liquida.total, dre.receita_liquida.percentual, true, '#16a085', true);
    
    // 4. CUSTOS
    html += renderizarLinhaDRE('(-) CUSTOS', dre.custos.total, dre.custos.percentual, false, '#e74c3c');
    if (dre.custos.itens && dre.custos.itens.length > 0) {
        dre.custos.itens.forEach(item => {
            html += renderizarLinhaDetalheDRE(item.descricao, item.valor);
        });
    }
    
    // 5. LUCRO BRUTO
    html += renderizarLinhaDRE('= LUCRO BRUTO', dre.lucro_bruto.total, dre.lucro_bruto.percentual, true, '#2980b9', true);
    
    // 6. DESPESAS OPERACIONAIS
    html += renderizarLinhaDRE('(-) DESPESAS OPERACIONAIS', dre.despesas_operacionais.total, dre.despesas_operacionais.percentual, false, '#e74c3c');
    if (dre.despesas_operacionais.itens && dre.despesas_operacionais.itens.length > 0) {
        dre.despesas_operacionais.itens.forEach(item => {
            html += renderizarLinhaDetalheDRE(item.descricao, item.valor);
        });
    }
    
    // 7. RESULTADO OPERACIONAL
    html += renderizarLinhaDRE('= RESULTADO OPERACIONAL', dre.resultado_operacional.total, dre.resultado_operacional.percentual, true, '#8e44ad', true);
    
    // 8. RESULTADO FINANCEIRO
    html += renderizarLinhaDRE('(+/-) RESULTADO FINANCEIRO', dre.resultado_financeiro.total, dre.resultado_financeiro.percentual, true, dre.resultado_financeiro.total >= 0 ? '#27ae60' : '#e74c3c');
    if (dre.resultado_financeiro.receitas_financeiras.itens.length > 0) {
        html += `<tr><td colspan="4" style="padding: 5px 12px; font-size: 11px; color: #7f8c8d;">(+) Receitas Financeiras</td></tr>`;
        dre.resultado_financeiro.receitas_financeiras.itens.forEach(item => {
            html += renderizarLinhaDetalheDRE(item.descricao, item.valor);
        });
    }
    if (dre.resultado_financeiro.despesas_financeiras.itens.length > 0) {
        html += `<tr><td colspan="4" style="padding: 5px 12px; font-size: 11px; color: #7f8c8d;">(-) Despesas Financeiras</td></tr>`;
        dre.resultado_financeiro.despesas_financeiras.itens.forEach(item => {
            html += renderizarLinhaDetalheDRE(item.descricao, item.valor);
        });
    }
    
    // 9. LUCRO/PREJUÍZO LÍQUIDO
    const corLucro = dre.lucro_liquido.total >= 0 ? '#27ae60' : '#c0392b';
    const textoLucro = dre.lucro_liquido.total >= 0 ? '✅ LUCRO LÍQUIDO DO EXERCÍCIO' : '❌ PREJUÍZO LÍQUIDO DO EXERCÍCIO';
    html += renderizarLinhaDRE(textoLucro, dre.lucro_liquido.total, dre.lucro_liquido.percentual, true, corLucro, true, true);
    
    html += `
                </tbody>
            </table>
            
            <!-- BOTÕES DE AÇÃO -->
            <div style="margin-top: 30px; text-align: center; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                <button onclick="exportarDREPDF()" class="btn-primary" style="padding: 12px 24px; background: #e74c3c; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                    📄 Exportar PDF
                </button>
                <button onclick="exportarDREExcel()" class="btn-primary" style="padding: 12px 24px; background: #27ae60; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                    📊 Exportar Excel
                </button>
                <button onclick="imprimirDRE()" class="btn-secondary" style="padding: 12px 24px; background: #3498db; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                    🖨️ Imprimir
                </button>
            </div>
            
        </div>
    `;
    
    document.getElementById('dreResultado').innerHTML = html;
}

/**
 * Renderizar linha da DRE
 */
function renderizarLinhaDRE(descricao, valor, percentual, positivo, cor, destaque = false, final = false) {
    const estilo = destaque ? 'font-weight: bold; font-size: 14px; background: #f8f9fa;' : '';
    const estiloFinal = final ? 'border-top: 3px double #2c3e50; border-bottom: 3px double #2c3e50; font-size: 16px;' : '';
    
    return `
        <tr style="${estilo} ${estiloFinal}">
            <td style="padding: 10px 12px; color: ${cor};">${descricao}</td>
            <td style="padding: 10px 12px; text-align: right; color: ${cor};">${formatarMoeda(Math.abs(valor))}</td>
            <td style="padding: 10px 12px; text-align: right; color: ${cor};">${percentual.toFixed(2)}%</td>
        </tr>
    `;
}

/**
 * Renderizar linha de detalhe (subconta)
 */
function renderizarLinhaDetalheDRE(descricao, valor) {
    return `
        <tr style="font-size: 11px; color: #7f8c8d;">
            <td style="padding: 4px 12px 4px 30px;">${descricao}</td>
            <td style="padding: 4px 12px; text-align: right;">${formatarMoeda(Math.abs(valor))}</td>
            <td style="padding: 4px 12px;"></td>
        </tr>
    `;
}

/**
 * Formatar data para exibição (DD/MM/YYYY)
 */
function formatarDataBR(dataISO) {
    const [ano, mes, dia] = dataISO.split('-');
    return `${dia}/${mes}/${ano}`;
}

// ===== EXPORTAÇÕES =====

window.exportarDREPDF = async function() {
    if (!window.dreData) {
        showToast('❌ Nenhuma DRE gerada', 'error');
        return;
    }
    
    try {
        showToast('📄 Gerando PDF...', 'info');
        
        // Obter parâmetros da DRE atual
        const dataInicio = document.getElementById('dreDataInicio').value;
        const dataFim = document.getElementById('dreDataFim').value;
        const versaoPlanoId = document.getElementById('dreVersaoPlano').value || null;
        const comparar = document.getElementById('dreCompararPeriodo')?.checked || false;
        
        // Chamar API de exportação PDF
        const response = await fetch('/api/relatorios/dre/pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                data_inicio: dataInicio,
                data_fim: dataFim,
                versao_plano_id: versaoPlanoId ? parseInt(versaoPlanoId) : null,
                comparar_periodo_anterior: comparar
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao gerar PDF');
        }
        
        // Obter blob do PDF
        const blob = await response.blob();
        
        // Criar URL temporária para download
        const url = window.URL.createObjectURL(blob);
        
        // Criar link de download
        const link = document.createElement('a');
        link.href = url;
        link.download = `DRE_${dataInicio.replace(/-/g, '')}_${dataFim.replace(/-/g, '')}.pdf`;
        document.body.appendChild(link);
        link.click();
        
        // Limpar
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        showToast('✅ PDF exportado com sucesso!', 'success');
        
    } catch (error) {
        console.error('Erro ao exportar PDF:', error);
        showToast(`❌ Erro ao exportar PDF: ${error.message}`, 'error');
    }
};

window.exportarDREExcel = async function() {
    if (!window.dreData) {
        showToast('❌ Nenhuma DRE gerada', 'error');
        return;
    }
    
    try {
        showToast('📊 Gerando Excel...', 'info');
        
        // Obter parâmetros da DRE atual
        const dataInicio = document.getElementById('dreDataInicio').value;
        const dataFim = document.getElementById('dreDataFim').value;
        const versaoPlanoId = document.getElementById('dreVersaoPlano').value || null;
        const comparar = document.getElementById('dreCompararPeriodo')?.checked || false;
        
        // Chamar API de exportação Excel
        const response = await fetch('/api/relatorios/dre/excel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                data_inicio: dataInicio,
                data_fim: dataFim,
                versao_plano_id: versaoPlanoId ? parseInt(versaoPlanoId) : null,
                comparar_periodo_anterior: comparar
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao gerar Excel');
        }
        
        // Obter blob do Excel
        const blob = await response.blob();
        
        // Criar URL temporária para download
        const url = window.URL.createObjectURL(blob);
        
        // Criar link de download
        const link = document.createElement('a');
        link.href = url;
        link.download = `DRE_${dataInicio.replace(/-/g, '')}_${dataFim.replace(/-/g, '')}.xlsx`;
        document.body.appendChild(link);
        link.click();
        
        // Limpar
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        showToast('✅ Excel exportado com sucesso!', 'success');
        
    } catch (error) {
        console.error('Erro ao exportar Excel:', error);
        showToast(`❌ Erro ao exportar Excel: ${error.message}`, 'error');
    }
};

window.imprimirDRE = function() {
    if (!window.dreData) {
        showToast('❌ Nenhuma DRE gerada', 'error');
        return;
    }
    
    window.print();
};

console.log('✅ Módulo DRE carregado');
