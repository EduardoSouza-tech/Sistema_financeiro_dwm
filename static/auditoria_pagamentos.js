/**
 * Auditoria de Pagamentos - Detecção de Pagamentos Duplicados
 * v1.0 - 24/02/2026
 */

// Estado global da auditoria
let auditoriaAtual = {
    extrato: [],
    lancamentos: [],
    abaAtiva: 'extrato'
};

/**
 * Trocar entre abas (Extrato / Lançamentos)
 */
function trocarAbaAuditoria(aba) {
    // Atualizar estado
    auditoriaAtual.abaAtiva = aba;
    
    // Atualizar visual das tabs
    const tabExtrato = document.getElementById('tab-auditoria-extrato');
    const tabLancamentos = document.getElementById('tab-auditoria-lancamentos');
    
   if (aba === 'extrato') {
        tabExtrato.classList.add('active');
        tabExtrato.style.borderBottom = '3px solid #3498db';
        tabExtrato.style.color = '#3498db';
        tabLancamentos.classList.remove('active');
        tabLancamentos.style.borderBottom = 'none';
        tabLancamentos.style.color = '#7f8c8d';
    } else {
        tabLancamentos.classList.add('active');
        tabLancamentos.style.borderBottom = '3px solid #3498db';
        tabLancamentos.style.color = '#3498db';
        tabExtrato.classList.remove('active');
        tabExtrato.style.borderBottom = 'none';
        tabExtrato.style.color = '#7f8c8d';
    }
    
    // Mostrar/ocultar conteúdo
    document.getElementById('auditoria-tab-extrato').style.display = aba === 'extrato' ? 'block' : 'none';
    document.getElementById('auditoria-tab-lancamentos').style.display = aba === 'lancamentos' ? 'block' : 'none';
}

/**
 * Carregar auditoria de pagamentos duplicados
 */
async function carregarAuditoriaPagamentos() {
    try {
        console.log('🔍 Carregando auditoria de pagamentos...');
        
        // Obter filtros
        const dataInicio = document.getElementById('auditoria-data-inicio').value;
        const dataFim = document.getElementById('auditoria-data-fim').value;
        const conta = document.getElementById('auditoria-conta').value;
        
        // Construir query params
        const params = new URLSearchParams();
        if (dataInicio) params.append('data_inicio', dataInicio);
        if (dataFim) params.append('data_fim', dataFim);
        if (conta) params.append('conta', conta);
        
        const url = `${API_URL}/auditoria/pagamentos-duplicados?${params.toString()}`;
        console.log('📡 Requisição:', url);
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) throw new Error('Erro ao carregar auditoria');
        
        const data = await response.json();
        console.log('✅ Auditoria recebida:', data);
        
        // Armazenar dados
        auditoriaAtual.extrato = data.duplicatas_extrato || [];
        auditoriaAtual.lancamentos = data.duplicatas_lancamentos || [];
        
        // Exibir resumo
        exibirResumoAuditoria(data.resumo);
        
        // Renderizar listas
        renderizarDuplicatasExtrato(auditoriaAtual.extrato);
        renderizarDuplicatasLancamentos(auditoriaAtual.lancamentos);
        
        // Atualizar badges
        document.getElementById('badge-duplicatas-extrato').textContent = auditoriaAtual.extrato.length;
        const badgeLancamentos = document.getElementById('badge-duplicatas-lancamentos');
        badgeLancamentos.textContent = auditoriaAtual.lancamentos.length;
        badgeLancamentos.style.display = auditoriaAtual.lancamentos.length > 0 ? 'inline' : 'none';
        
        showToast('✅ Auditoria concluída!', 'success');
        
    } catch (error) {
        console.error('❌ Erro na auditoria:', error);
        showToast('Erro ao carregar auditoria: ' + error.message, 'error');
    }
}

/**
 * Exibir resumo da auditoria
 */
function exibirResumoAuditoria(resumo) {
    const resumoDiv = document.getElementById('auditoria-resumo');
    resumoDiv.style.display = 'block';
    
    const totalGrupos = resumo.total_grupos_extrato + resumo.total_grupos_lancamentos;
    const valorTotal = resumo.total_valor_duplicado || 0;
    
    document.getElementById('auditoria-total-grupos').textContent = totalGrupos;
    document.getElementById('auditoria-valor-duplicado').textContent = 
        `R$ ${Math.abs(valorTotal).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Renderizar duplicatas do extrato bancário
 */
function renderizarDuplicatasExtrato(duplicatas) {
    const vazioDiv = document.getElementById('auditoria-extrato-vazio');
    const listaDiv = document.getElementById('auditoria-extrato-lista');
    
    if (duplicatas.length === 0) {
        vazioDiv.style.display = 'block';
        listaDiv.style.display = 'none';
        vazioDiv.innerHTML = `
            <div style="text-align: center; padding: 60px 20px; color: #7f8c8d;">
                <div style="font-size: 48px; margin-bottom: 20px;">✅</div>
                <h3 style="color: #27ae60; margin-bottom: 10px;">Nenhuma Duplicata Encontrada!</h3>
                <p style="margin: 0; font-size: 14px;">Não há pagamentos duplicados no extrato bancário para o período selecionado.</p>
            </div>
        `;
        return;
    }
    
    vazioDiv.style.display = 'none';
    listaDiv.style.display = 'block';
    
    let html = '';
    
    duplicatas.forEach((dup, index) => {
        const valor = Math.abs(parseFloat(dup.valor));
        const quantidade = parseInt(dup.quantidade);
        const valorTotalDuplicado = valor * (quantidade - 1);
        const ids = dup.ids.split(', ');
        
        html += `
            <div style="background: white; border: 2px solid #e74c3c; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <span style="background: #e74c3c; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                                ${quantidade}x DUPLICADO
                            </span>
                            <span style="color: #7f8c8d; font-size: 13px;">📅 ${formatarData(dup.data)}</span>
                        </div>
                        <div style="font-size: 16px; font-weight: 600; color: #2c3e50; margin-bottom: 8px;">
                            ${dup.descricao}
                        </div>
                        <div style="color: #7f8c8d; font-size: 13px;">
                            🏦 Conta: ${dup.conta_bancaria}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 24px; font-weight: bold; color: #e74c3c;">
                            R$ ${valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </div>
                        <div style="font-size: 13px; color: #7f8c8d; margin-top: 5px;">
                            💰 Total duplicado: R$ ${valorTotalDuplicado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </div>
                    </div>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; font-size: 13px; color: #34495e;">
                    <strong>IDs das transações:</strong> ${ids.join(', ')}
                </div>
            </div>
        `;
    });
    
    listaDiv.innerHTML = html;
}

/**
 * Renderizar duplicatas dos lançamentos
 */
function renderizarDuplicatasLancamentos(duplicatas) {
    const listaDiv = document.getElementById('auditoria-lancamentos-lista');
    
    if (duplicatas.length === 0) {
        listaDiv.innerHTML = `
            <div style="text-align: center; padding: 60px 20px; color: #7f8c8d;">
                <div style="font-size: 48px; margin-bottom: 20px;">✅</div>
                <h3 style="color: #27ae60; margin-bottom: 10px;">Nenhuma Duplicata Encontrada!</h3>
                <p style="margin: 0; font-size: 14px;">Não há lançamentos duplicados para o período selecionado.</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    duplicatas.forEach((dup, index) => {
        const valor = Math.abs(parseFloat(dup.valor));
        const quantidade = parseInt(dup.quantidade);
        const valorTotalDuplicado = valor * (quantidade - 1);
        const ids = dup.ids.split(', ');
        
        html += `
            <div style="background: white; border: 2px solid #e74c3c; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <span style="background: #e74c3c; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                                ${quantidade}x DUPLICADO
                            </span>
                            <span style="color: #7f8c8d; font-size: 13px;">📅 ${formatarData(dup.data)}</span>
                        </div>
                        <div style="font-size: 16px; font-weight: 600; color: #2c3e50; margin-bottom: 8px;">
                            ${dup.beneficiario}
                        </div>
                        <div style="color: #7f8c8d; font-size: 13px; margin-bottom: 4px;">
                            ${dup.cpf_cnpj ? `📄 CPF/CNPJ: ${dup.cpf_cnpj}` : ''}
                        </div>
                        <div style="color: #7f8c8d; font-size: 13px;">
                            📁 Categoria: ${dup.categoria_nome || 'Sem categoria'} • 🏦 ${dup.conta_bancaria}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 24px; font-weight: bold; color: #e74c3c;">
                            R$ ${valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </div>
                        <div style="font-size: 13px; color: #7f8c8d; margin-top: 5px;">
                            💰 Total duplicado: R$ ${valorTotalDuplicado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </div>
                    </div>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; font-size: 13px; color: #34495e;">
                    <strong>IDs dos lançamentos:</strong> ${ids.join(', ')}
                </div>
            </div>
        `;
    });
    
    listaDiv.innerHTML = html;
}

/**
 * Formatar data para exibição
 */
function formatarData(data) {
    if (!data) return '-';
    const d = new Date(data + 'T00:00:00');
    return d.toLocaleDateString('pt-BR');
}

/**
 * Carregar contas bancárias no select da auditoria
 */
async function carregarContasAuditoria() {
    try {
        const response = await fetch(`${API_URL}/contas`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) return;
        
        let data = await response.json();
        
        // Verificar se precisa extrair 'data' do wrapper
        if (data.data && Array.isArray(data.data)) {
            data = data.data;
        }
        
        const select = document.getElementById('auditoria-conta');
        select.innerHTML = '<option value="">Todas as contas</option>';
        
        data.forEach(conta => {
            const option = document.createElement('option');
            option.value = conta.nome;
            option.textContent = conta.nome;
            select.appendChild(option);
        });
        
    } catch (error) {
        console.error('Erro ao carregar contas para auditoria:', error);
    }
}

// Expor funções globalmente
window.trocarAbaAuditoria = trocarAbaAuditoria;
window.carregarAuditoriaPagamentos = carregarAuditoriaPagamentos;
window.carregarContasAuditoria = carregarContasAuditoria;

console.log('✅ Módulo de Auditoria de Pagamentos carregado');
