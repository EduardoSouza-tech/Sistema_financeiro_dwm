// ========== SISTEMA DE CONTRATOS E SESSÕES ==========

// Inicialização
console.log('📋 Módulo de Contratos e Sessões carregado');

// ===== NAVEGAÇÃO ENTRE TABS =====
function switchTabContratos(tabName) {
    console.log(`🔄 Alternando para aba: ${tabName}`);
    console.log(`📊 Total de botões de tab:`, document.querySelectorAll('#contratos-section .tab-button').length);
    console.log(`📊 Total de tab-content:`, document.querySelectorAll('#contratos-section .tab-content').length);
    
    // Desativar todas as tabs
    const allButtons = document.querySelectorAll('#contratos-section .tab-button');
    const allContents = document.querySelectorAll('#contratos-section .tab-content');
    
    console.log(`🔄 Desativando ${allButtons.length} botões e ${allContents.length} conteúdos`);
    
    allButtons.forEach(btn => {
        btn.classList.remove('active');
    });
    allContents.forEach(content => {
        content.classList.remove('active');
    });

    // Ativar a tab selecionada
    const clickedButton = event.target;
    clickedButton.classList.add('active');
    console.log(`✅ Botão ativado:`, clickedButton.textContent.trim());
    
    const tabElement = document.getElementById(`tab-${tabName}`);
    if (!tabElement) {
        console.error(`❌ Tab não encontrada: tab-${tabName}`);
        return;
    }
    
    tabElement.classList.add('active');
    console.log(`✅ Tab ativada: ${tabName}`, {
        height: tabElement.offsetHeight,
        display: window.getComputedStyle(tabElement).display,
        innerHTML_length: tabElement.innerHTML.length
    });

    // Carregar dados conforme a tab
    if (tabName === 'acompanhamento-sessoes') {
        carregarSessoes();
    } else if (tabName === 'acompanhamento-contratos') {
        carregarContratos();
    } else if (tabName === 'fornecedores-contratos') {
        carregarFornecedoresContratos();
    }
}

// ===== CONTRATOS - CRUD =====

async function novoContrato() {
    console.log('🆕 novoContrato() chamada');
    
    const container = document.getElementById('form-contrato-container');
    console.log('📦 Container encontrado:', container);
    
    if (!container) {
        console.error('❌ Container form-contrato-container não encontrado!');
        showToast('Erro: formulário não encontrado', 'error');
        return;
    }
    
    container.classList.remove('hidden');
    console.log('✅ Classe hidden removida');
    
    const form = document.getElementById('form-contrato');
    if (form) {
        form.reset();
        console.log('✅ Formulário resetado');
    } else {
        console.error('❌ Formulário form-contrato não encontrado!');
    }
    
    document.getElementById('contrato-id').value = '';
    
    // Gerar número automaticamente
    try {
        const response = await fetch('/api/contratos/proximo-numero');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('contrato-numero').value = data.numero;
            console.log('✅ Número gerado automaticamente:', data.numero);
        }
    } catch (error) {
        console.error('❌ Erro ao gerar número:', error);
    }
    
    // Carregar dropdowns
    console.log('🔄 Carregando dropdowns...');
    await carregarClientesDropdown('contrato-cliente');
    await carregarFornecedoresComissao();
    
    // Limpar comissões extras
    const comissoesContainer = document.getElementById('comissoes-container');
    if (comissoesContainer) {
        const primeiraComissao = comissoesContainer.querySelector('.comissao-item');
        comissoesContainer.innerHTML = '';
        if (primeiraComissao) {
            comissoesContainer.appendChild(primeiraComissao);
        }
    }
    
    // Aplicar máscara de moeda
    aplicarMascaraMoeda('contrato-valor');
    aplicarMascaraMoeda('contrato-imposto');
    
    console.log('✅ novoContrato() concluído');
}

function cancelarContrato() {
    document.getElementById('form-contrato-container').classList.add('hidden');
    document.getElementById('form-contrato').reset();
}

document.getElementById('form-contrato').addEventListener('submit', async (e) => {
    e.preventDefault();
    await salvarContrato();
});

async function salvarContrato() {
    const id = document.getElementById('contrato-id').value;
    
    // Coletar comissões
    const comissoes = [];
    document.querySelectorAll('.comissao-item').forEach(item => {
        const fornecedor = item.querySelector('.comissao-fornecedor').value;
        const tipo = item.querySelector('.comissao-tipo').value;
        const porcentagem = item.querySelector('.comissao-porcentagem').value;
        
        if (fornecedor && porcentagem) {
            comissoes.push({
                fornecedor_id: parseInt(fornecedor),
                tipo_fornecedor: tipo,
                porcentagem: parseFloat(porcentagem)
            });
        }
    });
    
    const data = {
        cliente_id: parseInt(document.getElementById('contrato-cliente').value),
        tipo_contrato: document.getElementById('contrato-tipo').value,
        descricao: document.getElementById('contrato-descricao').value,
        valor_contrato: parseFloat(document.getElementById('contrato-valor').value.replace(/\D/g, '')) / 100,
        valor_imposto: parseFloat(document.getElementById('contrato-imposto').value.replace(/\D/g, '')) / 100 || 0,
        data_vigencia_inicio: document.getElementById('contrato-vigencia-inicio').value,
        data_vigencia_fim: document.getElementById('contrato-vigencia-fim').value || null,
        forma_pagamento: document.getElementById('contrato-forma-pagamento').value || null,
        parcelamento: parseInt(document.getElementById('contrato-parcelamento').value) || 1,
        data_pagamento: document.getElementById('contrato-data-pagamento').value || null,
        status_pagamento: document.getElementById('contrato-status-pagamento').value,
        status_nf: document.getElementById('contrato-status-nf').value,
        numero_nf: document.getElementById('contrato-numero-nf').value || null,
        crm_id: document.getElementById('contrato-crm-id').value || null,
        observacoes: document.getElementById('contrato-observacoes').value || null,
        comissoes: comissoes
    };
    
    try {
        const url = id ? `/api/contratos/${id}` : '/api/contratos';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast(id ? 'Contrato atualizado com sucesso!' : 'Contrato criado com sucesso!', 'success');
            cancelarContrato();
            carregarContratos();
        } else {
            const error = await response.json();
            showToast('Erro ao salvar contrato: ' + (error.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro ao salvar contrato', 'error');
    }
}

async function editarContrato(id) {
    try {
        const response = await fetch(`/api/contratos/${id}`);
        if (!response.ok) throw new Error('Erro ao carregar contrato');
        
        const contrato = await response.json();
        
        document.getElementById('form-contrato-container').classList.remove('hidden');
        document.getElementById('contrato-id').value = contrato.id;
        document.getElementById('contrato-cliente').value = contrato.cliente_id;
        document.getElementById('contrato-tipo').value = contrato.tipo_contrato;
        document.getElementById('contrato-descricao').value = contrato.descricao;
        document.getElementById('contrato-valor').value = formatarMoeda(contrato.valor_contrato);
        document.getElementById('contrato-imposto').value = formatarMoeda(contrato.valor_imposto || 0);
        document.getElementById('contrato-vigencia-inicio').value = contrato.data_vigencia_inicio;
        document.getElementById('contrato-vigencia-fim').value = contrato.data_vigencia_fim || '';
        document.getElementById('contrato-forma-pagamento').value = contrato.forma_pagamento || '';
        document.getElementById('contrato-parcelamento').value = contrato.parcelamento || 1;
        document.getElementById('contrato-data-pagamento').value = contrato.data_pagamento || '';
        document.getElementById('contrato-status-pagamento').value = contrato.status_pagamento;
        document.getElementById('contrato-status-nf').value = contrato.status_nf;
        document.getElementById('contrato-numero-nf').value = contrato.numero_nf || '';
        document.getElementById('contrato-crm-id').value = contrato.crm_id || '';
        document.getElementById('contrato-observacoes').value = contrato.observacoes || '';
        
        // Carregar comissões
        if (contrato.comissoes && contrato.comissoes.length > 0) {
            const container = document.getElementById('comissoes-container');
            container.innerHTML = '';
            
            for (const comissao of contrato.comissoes) {
                await adicionarComissao(comissao);
            }
        }
        
        await carregarClientesDropdown('contrato-cliente');
        
        // Scroll para o formulário
        document.getElementById('form-contrato-container').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro ao carregar contrato', 'error');
    }
}

async function excluirContrato(id) {
    if (!confirm('Deseja realmente excluir este contrato?')) return;
    
    try {
        const response = await fetch(`/api/contratos/${id}`, { method: 'DELETE' });
        
        if (response.ok) {
            showToast('Contrato excluído com sucesso!', 'success');
            carregarContratos();
        } else {
            showToast('Erro ao excluir contrato', 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro ao excluir contrato', 'error');
    }
}

// ===== COMISSÕES =====

async function adicionarComissao(dadosComissao = null) {
    const container = document.getElementById('comissoes-container');
    const novaComissao = document.createElement('div');
    novaComissao.className = 'comissao-item';
    novaComissao.style.cssText = 'background: white; padding: 15px; border-radius: 5px; margin-bottom: 10px;';
    
    novaComissao.innerHTML = `
        <div class="form-row">
            <div class="form-group">
                <label>Fornecedor:</label>
                <select class="comissao-fornecedor"></select>
            </div>
            
            <div class="form-group">
                <label>Tipo:</label>
                <select class="comissao-tipo">
                    <option value="sdr">SDR</option>
                    <option value="closer">Closer</option>
                    <option value="outro">Outro</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Porcentagem (%):</label>
                <input type="number" class="comissao-porcentagem" step="0.01" min="0" max="100">
            </div>
            
            <div class="form-group" style="align-self: flex-end;">
                <button type="button" class="btn btn-danger" onclick="removerComissao(this)">🗑️</button>
            </div>
        </div>
    `;
    
    container.appendChild(novaComissao);
    
    // Carregar fornecedores no novo dropdown
    await carregarFornecedoresComissao(novaComissao.querySelector('.comissao-fornecedor'));
    
    // Se tiver dados, preencher
    if (dadosComissao) {
        novaComissao.querySelector('.comissao-fornecedor').value = dadosComissao.fornecedor_id;
        novaComissao.querySelector('.comissao-tipo').value = dadosComissao.tipo_fornecedor;
        novaComissao.querySelector('.comissao-porcentagem').value = dadosComissao.porcentagem;
    }
}

function removerComissao(btn) {
    const container = document.getElementById('comissoes-container');
    if (container.querySelectorAll('.comissao-item').length > 1) {
        btn.closest('.comissao-item').remove();
    } else {
        showToast('Deve haver pelo menos uma comissão', 'warning');
    }
}

async function carregarFornecedoresComissao(selectElement = null) {
    try {
        const response = await fetch('/api/fornecedores');
        if (!response.ok) throw new Error('Erro ao carregar fornecedores');
        
        const fornecedores = await response.json();
        
        const selects = selectElement ? [selectElement] : document.querySelectorAll('.comissao-fornecedor');
        
        selects.forEach(select => {
            select.innerHTML = '<option value="">Selecione...</option>';
            fornecedores.forEach(f => {
                const option = document.createElement('option');
                option.value = f.id;
                option.textContent = f.nome || f.razao_social || 'Sem nome';
                select.appendChild(option);
            });
        });
    } catch (error) {
        console.error('Erro ao carregar fornecedores:', error);
    }
}

// ===== SESSÕES - CRUD =====

async function novaSessao() {
    console.log('🆕 novaSessao() chamada');
    
    const container = document.getElementById('form-sessao-container');
    console.log('📦 Container encontrado:', container);
    
    if (!container) {
        console.error('❌ Container form-sessao-container não encontrado!');
        showToast('Erro: formulário não encontrado', 'error');
        return;
    }
    
    container.classList.remove('hidden');
    console.log('✅ Classe hidden removida');
    
    const form = document.getElementById('form-sessao');
    if (form) {
        form.reset();
        console.log('✅ Formulário resetado');
    } else {
        console.error('❌ Formulário form-sessao não encontrado!');
    }
    
    document.getElementById('sessao-id').value = '';
    
    // Carregar dropdowns
    console.log('🔄 Carregando dropdowns...');
    await carregarClientesDropdown('sessao-cliente');
    await carregarFornecedoresEquipe();
    await carregarKitsEquipamentos();
    
    // Limpar seções dinâmicas
    const equipeContainer = document.getElementById('equipe-container');
    if (equipeContainer) {
        const primeiraEquipe = equipeContainer.querySelector('.equipe-item');
        equipeContainer.innerHTML = '';
        if (primeiraEquipe) {
            equipeContainer.appendChild(primeiraEquipe);
        }
    }
    
    const equipamentosContainer = document.getElementById('equipamentos-alugados-container');
    if (equipamentosContainer) equipamentosContainer.innerHTML = '';
    
    const custosContainer = document.getElementById('custos-adicionais-container');
    if (custosContainer) custosContainer.innerHTML = '';
    
    const tagsContainer = document.getElementById('sessao-tags-container');
    if (tagsContainer) tagsContainer.innerHTML = '';
    
    // Event listener para tags
    const tagInput = document.getElementById('sessao-tag-input');
    if (tagInput) {
        tagInput.onkeypress = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                adicionarTag(tagInput.value.trim());
                tagInput.value = '';
            }
        };
    }
    
    console.log('✅ novaSessao() concluído');
}

function cancelarSessao() {
    document.getElementById('form-sessao-container').classList.add('hidden');
    document.getElementById('form-sessao').reset();
}

document.getElementById('form-sessao').addEventListener('submit', async (e) => {
    e.preventDefault();
    await salvarSessao();
});

async function salvarSessao() {
    const id = document.getElementById('sessao-id').value;
    
    // Coletar tipos de captação
    const tiposCaptacao = [];
    document.querySelectorAll('.tipo-captacao:checked').forEach(checkbox => {
        tiposCaptacao.push(checkbox.value);
    });
    
    // Coletar tags
    const tags = [];
    document.querySelectorAll('#sessao-tags-container .tag-badge').forEach(tag => {
        tags.push(tag.textContent.replace('×', '').trim());
    });
    
    // Coletar equipe
    const equipe = [];
    document.querySelectorAll('.equipe-item').forEach(item => {
        const fornecedor = item.querySelector('.equipe-fornecedor').value;
        const funcao = item.querySelector('.equipe-funcao').value;
        const valor = item.querySelector('.equipe-valor').value;
        
        if (fornecedor) {
            equipe.push({
                fornecedor_id: parseInt(fornecedor),
                funcao: funcao,
                valor_combinado: parseFloat(valor.replace(/\D/g, '')) / 100 || 0
            });
        }
    });
    
    // Coletar kits selecionados
    const kits = [];
    document.querySelectorAll('#kits-equipamentos input:checked').forEach(checkbox => {
        kits.push(parseInt(checkbox.value));
    });
    
    // Coletar equipamentos alugados
    const equipamentosAlugados = [];
    document.querySelectorAll('.equipamento-alugado-item').forEach(item => {
        const descricao = item.querySelector('.equipamento-descricao').value;
        const valor = item.querySelector('.equipamento-valor').value;
        
        if (descricao && valor) {
            equipamentosAlugados.push({
                descricao: descricao,
                valor: parseFloat(valor.replace(/\D/g, '')) / 100
            });
        }
    });
    
    // Coletar custos adicionais
    const custosAdicionais = [];
    document.querySelectorAll('.custo-adicional-item').forEach(item => {
        const descricao = item.querySelector('.custo-descricao').value;
        const valor = item.querySelector('.custo-valor').value;
        
        if (descricao && valor) {
            custosAdicionais.push({
                descricao: descricao,
                valor: parseFloat(valor.replace(/\D/g, '')) / 100
            });
        }
    });
    
    const data = {
        cliente_id: parseInt(document.getElementById('sessao-cliente').value),
        contrato_id: document.getElementById('sessao-contrato').value ? parseInt(document.getElementById('sessao-contrato').value) : null,
        tipo_sessao: document.getElementById('sessao-tipo').value,
        data_sessao: document.getElementById('sessao-data').value,
        horario: document.getElementById('sessao-horario').value,
        endereco: document.getElementById('sessao-endereco').value || null,
        tipo_captacao: tiposCaptacao,
        descricao: document.getElementById('sessao-descricao').value || null,
        tags: tags,
        horas_captacao: parseFloat(document.getElementById('sessao-horas').value) || null,
        prazo_entrega: document.getElementById('sessao-prazo').value || null,
        equipe: equipe,
        kits_equipamentos: kits,
        equipamentos_alugados: equipamentosAlugados,
        custos_adicionais: custosAdicionais,
        observacoes: document.getElementById('sessao-observacoes').value || null
    };
    
    try {
        const url = id ? `/api/sessoes/${id}` : '/api/sessoes';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast(id ? 'Sessão atualizada com sucesso!' : 'Sessão criada com sucesso!', 'success');
            cancelarSessao();
            carregarSessoes();
        } else {
            const error = await response.json();
            showToast('Erro ao salvar sessão: ' + (error.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro ao salvar sessão', 'error');
    }
}

async function editarSessao(id) {
    try {
        console.log(`✏️ Editando sessão ID ${id}...`);
        const response = await fetch(`/api/sessoes/${id}`);
        if (!response.ok) throw new Error('Erro ao carregar sessão');
        
        const sessao = await response.json();
        console.log('Dados da sessão:', sessao);
        
        // Mostrar formulário
        document.getElementById('form-sessao-container').classList.remove('hidden');
        document.getElementById('form-sessao').reset();
        
        // Preencher campos básicos
        document.getElementById('sessao-id').value = sessao.id;
        document.getElementById('sessao-cliente').value = sessao.cliente_id;
        document.getElementById('sessao-contrato').value = sessao.contrato_id || '';
        document.getElementById('sessao-tipo').value = sessao.tipo_sessao;
        document.getElementById('sessao-data').value = sessao.data_sessao;
        document.getElementById('sessao-horario').value = sessao.horario;
        document.getElementById('sessao-endereco').value = sessao.endereco || '';
        document.getElementById('sessao-descricao').value = sessao.descricao || '';
        document.getElementById('sessao-horas').value = sessao.horas_captacao || '';
        document.getElementById('sessao-prazo').value = sessao.prazo_entrega || '';
        document.getElementById('sessao-observacoes').value = sessao.observacoes || '';
        
        // Carregar dropdowns
        await carregarClientesDropdown('sessao-cliente');
        await carregarFornecedoresEquipe();
        await carregarKitsEquipamentos();
        
        // Preencher tipos de captação
        if (sessao.tipo_captacao) {
            sessao.tipo_captacao.forEach(tipo => {
                const checkbox = document.querySelector(`.tipo-captacao[value="${tipo}"]`);
                if (checkbox) checkbox.checked = true;
            });
        }
        
        // Preencher tags
        const tagsContainer = document.getElementById('sessao-tags-container');
        tagsContainer.innerHTML = '';
        if (sessao.tags) {
            sessao.tags.forEach(tag => adicionarTag(tag));
        }
        
        // Scroll para o formulário
        document.getElementById('form-sessao-container').scrollIntoView({ behavior: 'smooth' });
        
        showToast('Sessão carregada para edição', 'info');
        
    } catch (error) {
        console.error('❌ Erro ao editar sessão:', error);
        showToast('Erro ao carregar sessão para edição', 'error');
    }
}

async function excluirSessao(id) {
    if (!confirm('Tem certeza que deseja excluir esta sessão?')) return;
    
    try {
        console.log(`🗑️ Excluindo sessão ID ${id}...`);
        const response = await fetch(`/api/sessoes/${id}`, { method: 'DELETE' });
        
        if (response.ok) {
            showToast('Sessão excluída com sucesso!', 'success');
            carregarSessoes();
        } else {
            const error = await response.json();
            showToast('Erro ao excluir sessão: ' + (error.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao excluir sessão:', error);
        showToast('Erro ao excluir sessão', 'error');
    }
}

// ===== TAGS =====

function adicionarTag(texto) {
    if (!texto) return;
    
    const container = document.getElementById('sessao-tags-container');
    
    const tag = document.createElement('span');
    tag.className = 'tag-badge';
    tag.style.cssText = 'background: #3498db; color: white; padding: 5px 10px; border-radius: 15px; cursor: pointer;';
    tag.innerHTML = `${texto} <span onclick="this.parentElement.remove()">×</span>`;
    
    container.appendChild(tag);
}

// ===== EQUIPE =====

async function adicionarEquipe(dadosEquipe = null) {
    const container = document.getElementById('equipe-container');
    const novaEquipe = document.createElement('div');
    novaEquipe.className = 'equipe-item';
    novaEquipe.style.cssText = 'background: white; padding: 15px; border-radius: 5px; margin-bottom: 10px;';
    
    novaEquipe.innerHTML = `
        <div class="form-row">
            <div class="form-group">
                <label>Fornecedor:</label>
                <select class="equipe-fornecedor"></select>
            </div>
            
            <div class="form-group">
                <label>Função:</label>
                <select class="equipe-funcao">
                    <option value="captacao">Captação</option>
                    <option value="entrega">Entrega</option>
                    <option value="assistente">Assistente</option>
                    <option value="outro">Outro</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Valor:</label>
                <input type="text" class="equipe-valor" placeholder="R$ 0,00">
            </div>
            
            <div class="form-group" style="align-self: flex-end;">
                <button type="button" class="btn btn-danger" onclick="removerEquipe(this)">🗑️</button>
            </div>
        </div>
    `;
    
    container.appendChild(novaEquipe);
    
    // Carregar fornecedores
    await carregarFornecedoresEquipe(novaEquipe.querySelector('.equipe-fornecedor'));
    
    // Aplicar máscara
    aplicarMascaraMoeda(novaEquipe.querySelector('.equipe-valor'));
    
    // Se tiver dados, preencher
    if (dadosEquipe) {
        novaEquipe.querySelector('.equipe-fornecedor').value = dadosEquipe.fornecedor_id;
        novaEquipe.querySelector('.equipe-funcao').value = dadosEquipe.funcao;
        novaEquipe.querySelector('.equipe-valor').value = formatarMoeda(dadosEquipe.valor_combinado);
    }
}

function removerEquipe(btn) {
    const container = document.getElementById('equipe-container');
    if (container.querySelectorAll('.equipe-item').length > 1) {
        btn.closest('.equipe-item').remove();
    } else {
        showToast('Deve haver pelo menos um membro na equipe', 'warning');
    }
}

async function carregarFornecedoresEquipe(selectElement = null) {
    try {
        const response = await fetch('/api/fornecedores');
        if (!response.ok) throw new Error('Erro ao carregar fornecedores');
        
        const fornecedores = await response.json();
        
        const selects = selectElement ? [selectElement] : document.querySelectorAll('.equipe-fornecedor');
        
        selects.forEach(select => {
            select.innerHTML = '<option value="">Selecione...</option>';
            fornecedores.forEach(f => {
                const option = document.createElement('option');
                option.value = f.id;
                option.textContent = f.nome || f.razao_social || 'Sem nome';
                select.appendChild(option);
            });
        });
    } catch (error) {
        console.error('Erro ao carregar fornecedores:', error);
    }
}

async function aplicarTemplateEquipe() {
    try {
        const response = await fetch('/api/templates-equipe');
        if (!response.ok) throw new Error('Erro ao carregar templates');
        
        const templates = await response.json();
        
        if (templates.length === 0) {
            showToast('Nenhum template de equipe salvo', 'warning');
            return;
        }
        
        // Criar modal de seleção
        const modal = document.createElement('div');
        modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10000; display: flex; align-items: center; justify-content: center;';
        modal.innerHTML = `
            <div style="background: white; padding: 30px; border-radius: 10px; max-width: 500px; width: 90%;">
                <h3 style="margin: 0 0 20px 0;">📋 Selecionar Template de Equipe</h3>
                <select id="template-select" style="width: 100%; padding: 10px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <option value="">Selecione um template...</option>
                    ${templates.map(t => `<option value="${t.id}">${t.nome}</option>`).join('')}
                </select>
                <div id="template-preview" style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; display: none;">
                    <h4 style="margin: 0 0 10px 0;">Equipe:</h4>
                    <div id="preview-content"></div>
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" class="btn btn-secondary">Cancelar</button>
                    <button id="btn-aplicar-template" class="btn btn-primary" disabled>Aplicar Template</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const select = document.getElementById('template-select');
        const preview = document.getElementById('template-preview');
        const previewContent = document.getElementById('preview-content');
        const btnAplicar = document.getElementById('btn-aplicar-template');
        
        select.onchange = () => {
            const templateId = parseInt(select.value);
            if (!templateId) {
                preview.style.display = 'none';
                btnAplicar.disabled = true;
                return;
            }
            
            const template = templates.find(t => t.id === templateId);
            if (template && template.membros) {
                preview.style.display = 'block';
                btnAplicar.disabled = false;
                previewContent.innerHTML = template.membros.map(m => 
                    `<div style="padding: 5px 0;">• ${m.fornecedor_nome || 'Fornecedor #' + m.fornecedor_id} - ${m.funcao} - R$ ${parseFloat(m.valor || 0).toFixed(2)}</div>`
                ).join('');
            }
        };
        
        btnAplicar.onclick = () => {
            const templateId = parseInt(select.value);
            const template = templates.find(t => t.id === templateId);
            
            if (template && template.membros) {
                // Limpar equipe atual
                const container = document.getElementById('equipe-container');
                container.innerHTML = '';
                
                // Adicionar cada membro do template
                template.membros.forEach(membro => {
                    adicionarEquipe(membro);
                });
                
                showToast(`Template "${template.nome}" aplicado com sucesso!`, 'success');
                modal.remove();
            }
        };
        
    } catch (error) {
        console.error('Erro ao aplicar template:', error);
        showToast('Erro ao carregar templates de equipe', 'error');
    }
}

// ===== EQUIPAMENTOS =====

async function carregarKitsEquipamentos() {
    try {
        const response = await fetch('/api/kits-equipamentos');
        if (!response.ok) return;
        
        const kits = await response.json();
        const container = document.getElementById('kits-equipamentos');
        container.innerHTML = '';
        
        kits.forEach(kit => {
            const label = document.createElement('label');
            label.style.cssText = 'display: flex; align-items: center; gap: 5px;';
            label.innerHTML = `
                <input type="checkbox" value="${kit.id}">
                ${kit.nome}
            `;
            container.appendChild(label);
        });
    } catch (error) {
        console.error('Erro ao carregar kits:', error);
    }
}

function adicionarKit() {
    // Função placeholder - kits são adicionados via checkbox no formulário
    console.log('✅ adicionarKit chamada (gerenciado via checkboxes)');
}

function removerKit() {
    // Função placeholder - kits são removidos desmarcando checkbox
    console.log('✅ removerKit chamada (gerenciado via checkboxes)');
}

function adicionarEquipamentoAlugado(dados = null) {
    const container = document.getElementById('equipamentos-alugados-container');
    const novoEquip = document.createElement('div');
    novoEquip.className = 'equipamento-alugado-item';
    novoEquip.style.cssText = 'background: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;';
    
    novoEquip.innerHTML = `
        <div class="form-row">
            <div class="form-group">
                <label>Descrição:</label>
                <input type="text" class="equipamento-descricao" placeholder="Ex: Câmera Sony A7III">
            </div>
            
            <div class="form-group">
                <label>Valor:</label>
                <input type="text" class="equipamento-valor" placeholder="R$ 0,00">
            </div>
            
            <div class="form-group" style="align-self: flex-end;">
                <button type="button" class="btn btn-danger" onclick="this.parentElement.parentElement.parentElement.remove()">🗑️</button>
            </div>
        </div>
    `;
    
    container.appendChild(novoEquip);
    
    // Aplicar máscara
    aplicarMascaraMoeda(novoEquip.querySelector('.equipamento-valor'));
    
    // Se tiver dados, preencher
    if (dados) {
        novoEquip.querySelector('.equipamento-descricao').value = dados.descricao;
        novoEquip.querySelector('.equipamento-valor').value = formatarMoeda(dados.valor);
    }
}

// ===== CUSTOS ADICIONAIS =====

function adicionarCustoAdicional(dados = null) {
    const container = document.getElementById('custos-adicionais-container');
    const novoCusto = document.createElement('div');
    novoCusto.className = 'custo-adicional-item';
    novoCusto.style.cssText = 'background: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;';
    
    novoCusto.innerHTML = `
        <div class="form-row">
            <div class="form-group">
                <label>Descrição:</label>
                <input type="text" class="custo-descricao" placeholder="Ex: Transporte">
            </div>
            
            <div class="form-group">
                <label>Valor:</label>
                <input type="text" class="custo-valor" placeholder="R$ 0,00">
            </div>
            
            <div class="form-group" style="align-self: flex-end;">
                <button type="button" class="btn btn-danger" onclick="this.parentElement.parentElement.parentElement.remove()">🗑️</button>
            </div>
        </div>
    `;
    
    container.appendChild(novoCusto);
    
    // Aplicar máscara
    aplicarMascaraMoeda(novoCusto.querySelector('.custo-valor'));
    
    // Se tiver dados, preencher
    if (dados) {
        novoCusto.querySelector('.custo-descricao').value = dados.descricao;
        novoCusto.querySelector('.custo-valor').value = formatarMoeda(dados.valor);
    }
}

function removerEquipamentoAlugado(elemento) {
    if (elemento && elemento.parentElement) {
        elemento.parentElement.parentElement.remove();
    }
}

function removerCustoAdicional(elemento) {
    if (elemento && elemento.parentElement) {
        elemento.parentElement.parentElement.remove();
    }
}

// ===== CONTRATOS DA SESSÃO =====

async function carregarContratosCliente() {
    const clienteId = document.getElementById('sessao-cliente').value;
    const tipoSessao = document.getElementById('sessao-tipo').value;
    
    if (!clienteId || tipoSessao === 'avulso') {
        document.getElementById('div-selecao-contrato').style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch(`/api/contratos?cliente_id=${clienteId}&tipo=${tipoSessao === 'pacote' ? 'pacote' : 'mensal'}`);
        if (!response.ok) return;
        
        const contratos = await response.json();
        const select = document.getElementById('sessao-contrato');
        select.innerHTML = '<option value="">Selecione...</option>';
        
        contratos.forEach(c => {
            const option = document.createElement('option');
            option.value = c.id;
            option.textContent = `${c.descricao} - ${formatarMoeda(c.valor_contrato)}`;
            // Armazenar cliente_id como data attribute
            option.dataset.clienteId = c.cliente_id;
            select.appendChild(option);
        });
        
    } catch (error) {
        console.error('Erro ao carregar contratos:', error);
    }
}

// Função para preencher cliente quando contrato for selecionado
async function preencherClienteDoContrato() {
    const contratoSelect = document.getElementById('sessao-contrato');
    const contratoId = contratoSelect.value;
    
    if (!contratoId) return;
    
    try {
        const response = await fetch(`/api/contratos/${contratoId}`);
        if (!response.ok) {
            console.error('Erro ao buscar contrato');
            return;
        }
        
        const contrato = await response.json();
        
        // Preencher o select de cliente
        const clienteSelect = document.getElementById('sessao-cliente');
        if (contrato.cliente_id) {
            clienteSelect.value = contrato.cliente_id;
            console.log(`✅ Cliente ${contrato.cliente_id} preenchido automaticamente do contrato`);
        }
        
    } catch (error) {
        console.error('Erro ao preencher cliente do contrato:', error);
    }
}

function mostrarSelecaoContrato() {
    const tipo = document.getElementById('sessao-tipo').value;
    const div = document.getElementById('div-selecao-contrato');
    
    if (tipo === 'pacote' || tipo === 'mensal') {
        div.style.display = 'block';
        carregarContratosCliente();
    } else {
        div.style.display = 'none';
    }
}

// ===== LISTAGENS E CARDS =====

async function carregarContratos() {
    try {
        console.log('🔄 Carregando contratos...');
        const response = await fetch('/api/contratos');
        if (!response.ok) throw new Error('Erro ao carregar contratos');
        
        const contratos = await response.json();
        console.log(`✅ ${contratos.length} contratos carregados`);
        
        // Renderizar na lista da tab de cadastro
        renderListaContratos(contratos);
        
        // Renderizar nos cards da tab de acompanhamento
        renderCardsContratos(contratos);
        
    } catch (error) {
        console.error('❌ Erro ao carregar contratos:', error);
        showToast('Erro ao carregar contratos', 'error');
    }
}

function renderListaContratos(contratos) {
    const container = document.getElementById('lista-contratos');
    if (!container) {
        console.error('❌ Container lista-contratos não encontrado!');
        return;
    }
    
    container.innerHTML = '';
    
    if (contratos.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;"><h3>📋 Nenhum contrato cadastrado</h3><p>Clique em "➕ Novo Contrato" acima para começar.</p></div>';
        return;
    }
    
    const tabela = document.createElement('table');
    tabela.style.cssText = 'width: 100%; border-collapse: collapse; background: white;';
    tabela.innerHTML = `
        <thead>
            <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <th style="padding: 12px; text-align: left; width: 30%;">Cliente</th>
                <th style="padding: 12px; text-align: left;">Tipo</th>
                <th style="padding: 12px; text-align: right;">Valor</th>
                <th style="padding: 12px; text-align: center;">Status</th>
                <th style="padding: 12px; text-align: center;">Vigência</th>
                <th style="padding: 12px; text-align: center;">Ações</th>
            </tr>
        </thead>
        <tbody>
            ${contratos.map(contrato => `
                <tr style="border-bottom: 1px solid #e0e0e0;">
                    <td style="padding: 12px;">${contrato.cliente_nome || 'Cliente não encontrado'}</td>
                    <td style="padding: 12px;">${contrato.tipo_contrato}</td>
                    <td style="padding: 12px; text-align: right; font-weight: bold;">${formatarMoeda(contrato.valor_contrato)}</td>
                    <td style="padding: 12px; text-align: center;">
                        <span style="padding: 4px 12px; border-radius: 12px; font-size: 12px; background: ${getCorStatusContrato(contrato.status_pagamento)}; color: white;">
                            ${contrato.status_pagamento}
                        </span>
                    </td>
                    <td style="padding: 12px; text-align: center; font-size: 13px;">
                        ${formatarData(contrato.data_vigencia_inicio)}<br>até ${contrato.data_vigencia_fim ? formatarData(contrato.data_vigencia_fim) : 'Indeterminado'}
                    </td>
                    <td style="padding: 12px; text-align: center;">
                        <button class="btn-icon" onclick="editarContrato(${contrato.id})" title="Editar">✏️</button>
                        <button class="btn-icon" onclick="excluirContrato(${contrato.id})" title="Excluir">🗑️</button>
                    </td>
                </tr>
            `).join('')}
        </tbody>
    `;
    
    container.appendChild(tabela);
}

function renderCardsContratos(contratos) {
    const container = document.getElementById('cards-contratos');
    if (!container) {
        console.error('❌ Container cards-contratos não encontrado!');
        return;
    }
    
    container.innerHTML = '';
    
    if (contratos.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;"><h3>📋 Nenhum contrato cadastrado</h3><p>Clique em "➕ Novo Contrato" na aba "Cadastro de Contrato" para começar.</p></div>';
        return;
    }
    
    contratos.forEach(contrato => {
        const statusCor = getCorStatusContrato(contrato.status_pagamento);
        
        const card = document.createElement('div');
        card.style.cssText = `background: ${statusCor}; color: white; padding: 20px; border-radius: 10px; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.15);`;
        card.innerHTML = `
            <h3 style="margin: 0 0 10px 0;">${contrato.cliente_nome || 'Cliente não encontrado'}</h3>
            <p style="margin: 5px 0;"><strong>Tipo:</strong> ${contrato.tipo_contrato}</p>
            <p style="margin: 5px 0;"><strong>Valor:</strong> ${formatarMoeda(contrato.valor_contrato)}</p>
            <p style="margin: 5px 0;"><strong>Status:</strong> ${contrato.status_pagamento}</p>
            <p style="margin: 5px 0;"><strong>Vigência:</strong> ${formatarData(contrato.data_vigencia_inicio)} - ${contrato.data_vigencia_fim ? formatarData(contrato.data_vigencia_fim) : 'Indeterminado'}</p>
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <button class="btn btn-sm" onclick="event.stopPropagation(); editarContrato(${contrato.id})" style="background: white; color: #333;">✏️ Editar</button>
                <button class="btn btn-sm" onclick="event.stopPropagation(); excluirContrato(${contrato.id})" style="background: #e74c3c; color: white;">🗑️ Excluir</button>
            </div>
        `;
        
        container.appendChild(card);
    });
}

async function carregarSessoes() {
    try {
        console.log('🔄 Carregando sessões...');
        const response = await fetch('/api/sessoes');
        if (!response.ok) throw new Error('Erro ao carregar sessões');
        
        const sessoes = await response.json();
        console.log(`✅ ${sessoes.length} sessões carregadas`);
        
        // Renderizar na lista da tab de cadastro
        renderListaSessoes(sessoes);
        
        // Renderizar nos cards da tab de acompanhamento
        renderCardsSessoes(sessoes);
        
    } catch (error) {
        console.error('❌ Erro ao carregar sessões:', error);
        showToast('Erro ao carregar sessões', 'error');
    }
}

function renderListaSessoes(sessoes) {
    const container = document.getElementById('lista-sessoes-cadastro');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (sessoes.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;"><h3>📅 Nenhuma sessão cadastrada</h3><p>Clique em "➕ Nova Sessão" acima para começar.</p></div>';
        return;
    }
    
    const tabela = document.createElement('table');
    tabela.style.cssText = 'width: 100%; border-collapse: collapse; background: white;';
    tabela.innerHTML = `
        <thead>
            <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <th style="padding: 12px; text-align: left;">Cliente</th>
                <th style="padding: 12px; text-align: left;">Data/Hora</th>
                <th style="padding: 12px; text-align: left;">Tipo</th>
                <th style="padding: 12px; text-align: center;">Status</th>
                <th style="padding: 12px; text-align: center;">Ações</th>
            </tr>
        </thead>
        <tbody>
            ${sessoes.map(sessao => `
                <tr style="border-bottom: 1px solid #e0e0e0;">
                    <td style="padding: 12px;">${sessao.cliente_nome || 'Cliente não encontrado'}</td>
                    <td style="padding: 12px;">${formatarData(sessao.data_sessao)}<br>${sessao.horario}</td>
                    <td style="padding: 12px;">${sessao.tipo_sessao}</td>
                    <td style="padding: 12px; text-align: center;">
                        <span style="padding: 4px 12px; border-radius: 12px; font-size: 12px; background: ${getCorStatusSessao(sessao.status)}; color: white;">
                            ${sessao.status}
                        </span>
                    </td>
                    <td style="padding: 12px; text-align: center;">
                        <button class="btn-icon" onclick="editarSessao(${sessao.id})" title="Editar">✏️</button>
                        <button class="btn-icon" onclick="excluirSessao(${sessao.id})" title="Excluir">🗑️</button>
                    </td>
                </tr>
            `).join('')}
        </tbody>
    `;
    
    container.appendChild(tabela);
}

function renderCardsSessoes(sessoes) {
    const container = document.getElementById('cards-sessoes');
    if (!container) {
        console.error('❌ Container cards-sessoes não encontrado!');
        return;
    }
    
    container.innerHTML = '';
    
    if (sessoes.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;"><h3>📅 Nenhuma sessão cadastrada</h3><p>Clique em "➕ Nova Sessão" na aba "Cadastro de Sessão" para começar.</p></div>';
        return;
    }
    
    sessoes.forEach(sessao => {
        const statusCor = getCorStatusSessao(sessao.status);
        
        const card = document.createElement('div');
        card.style.cssText = `background: ${statusCor}; color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);`;
        card.innerHTML = `
            <h3 style="margin: 0 0 10px 0;">${sessao.cliente_nome || 'Cliente não encontrado'}</h3>
            <p style="margin: 5px 0;"><strong>Data:</strong> ${formatarData(sessao.data_sessao)} às ${sessao.horario}</p>
            <p style="margin: 5px 0;"><strong>Tipo:</strong> ${sessao.tipo_sessao}</p>
            <p style="margin: 5px 0;"><strong>Status:</strong> ${sessao.status}</p>
            ${sessao.descricao ? `<p style="margin: 5px 0;">${sessao.descricao}</p>` : ''}
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <button class="btn btn-sm" onclick="editarSessao(${sessao.id})" style="background: white; color: #333;">✏️ Editar</button>
                <button class="btn btn-sm" onclick="excluirSessao(${sessao.id})" style="background: #e74c3c; color: white;">🗑️ Excluir</button>
                <button class="btn btn-sm" onclick="atualizarStatusSessao(${sessao.id})" style="background: rgba(255,255,255,0.2); color: white;">🔄 Status</button>
            </div>
        `;
        
        container.appendChild(card);
    });
}

async function carregarFornecedoresContratos() {
    try {
        console.log('🔄 Carregando fornecedores...');
        const mes = document.getElementById('filtro-mes-fornecedores').value;
        const url = mes ? `/api/fornecedores-contratos?mes=${mes}` : '/api/fornecedores-contratos';
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Erro ao carregar fornecedores');
        
        const fornecedores = await response.json();
        console.log(`✅ ${fornecedores.length} fornecedores carregados`);
        renderCardsFornecedores(fornecedores);
        
    } catch (error) {
        console.error('❌ Erro ao carregar fornecedores:', error);
        showToast('Erro ao carregar fornecedores', 'error');
    }
}

function renderCardsFornecedores(fornecedores) {
    const container = document.getElementById('cards-fornecedores-contratos');
    if (!container) {
        console.error('❌ Container cards-fornecedores-contratos não encontrado!');
        return;
    }
    
    container.innerHTML = '';
    
    if (fornecedores.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;"><h3>👥 Nenhum fornecedor com valores a receber</h3><p>Cadastre contratos e sessões para começar.</p></div>';
        return;
    }
    
    fornecedores.forEach(fornecedor => {
        const card = document.createElement('div');
        card.style.cssText = 'background: #2c3e50; color: white; padding: 20px; border-radius: 10px;';
        card.innerHTML = `
            <h3 style="margin: 0 0 10px 0;">${fornecedor.nome || 'Fornecedor não encontrado'}</h3>
            <p style="margin: 5px 0; font-size: 24px; font-weight: bold;">Total: ${formatarMoeda(fornecedor.total_a_receber || 0)}</p>
            <p style="margin: 5px 0;"><strong>Trabalhos:</strong> ${fornecedor.quantidade_trabalhos || 0}</p>
            <button class="btn btn-sm btn-light" onclick="verDetalhesFornecedor(${fornecedor.id})" style="margin-top: 10px;">📋 Ver Detalhes</button>
        `;
        
        container.appendChild(card);
    });
}

// ===== FILTROS =====

function filtrarSessoes() {
    const status = document.getElementById('filtro-status-sessoes').value;
    const mes = document.getElementById('filtro-mes-sessoes').value;
    
    let url = '/api/sessoes?';
    if (status) url += `status=${status}&`;
    if (mes) url += `mes=${mes}`;
    
    fetch(url)
        .then(r => r.json())
        .then(sessoes => renderCardsSessoes(sessoes))
        .catch(error => console.error('Erro:', error));
}

function filtrarContratos() {
    const status = document.getElementById('filtro-status-contratos').value;
    
    let url = '/api/contratos';
    if (status) url += `?status=${status}`;
    
    fetch(url)
        .then(r => r.json())
        .then(contratos => renderCardsContratos(contratos))
        .catch(error => console.error('Erro:', error));
}

// ===== STATUS E CORES =====

function getCorStatusContrato(status) {
    const cores = {
        'ativo': '#3498db',
        'pago': '#27ae60',
        'atrasado': '#e67e22',
        'cancelado': '#e74c3c',
        'pendente': '#95a5a6',
        'encerrado': '#7f8c8d'
    };
    return cores[status] || '#95a5a6';
}

function getCorStatusSessao(status) {
    const cores = {
        'marcada': '#95a5a6',
        'reagendada': '#7f8c8d',
        'realizada': '#3498db',
        'entrega_parcial': '#f39c12',
        'entrega_completa': '#27ae60',
        'entrega_atrasada': '#e67e22',
        'cancelada': '#e74c3c'
    };
    return cores[status] || '#95a5a6';
}

async function atualizarStatusSessao(id) {
    try {
        // Buscar dados atuais da sessão
        const response = await fetch(`/api/sessoes/${id}`);
        if (!response.ok) throw new Error('Erro ao carregar sessão');
        
        const sessao = await response.json();
        
        // Opções de status disponíveis
        const statusOptions = [
            { value: 'marcada', label: 'Marcada' },
            { value: 'reagendada', label: 'Reagendada' },
            { value: 'realizada', label: 'Realizada' },
            { value: 'entrega_parcial', label: 'Entrega Parcial' },
            { value: 'entrega_completa', label: 'Entrega Completa' },
            { value: 'entrega_atrasada', label: 'Entrega Atrasada' },
            { value: 'cancelada', label: 'Cancelada' }
        ];
        
        // Criar modal
        const modal = document.createElement('div');
        modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10000; display: flex; align-items: center; justify-content: center;';
        modal.innerHTML = `
            <div style="background: white; padding: 30px; border-radius: 10px; max-width: 450px; width: 90%;">
                <h3 style="margin: 0 0 20px 0;">🔄 Atualizar Status da Sessão</h3>
                <div style="margin-bottom: 20px;">
                    <p style="margin: 0 0 10px 0; color: #666;"><strong>Cliente:</strong> ${sessao.cliente_nome}</p>
                    <p style="margin: 0 0 10px 0; color: #666;"><strong>Data:</strong> ${formatarData(sessao.data_sessao)}</p>
                    <p style="margin: 0 0 10px 0; color: #666;"><strong>Status Atual:</strong> <span style="background: ${getCorStatusSessao(sessao.status)}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px;">${sessao.status}</span></p>
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; font-weight: bold;">Novo Status:</label>
                    <select id="novo-status" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                        ${statusOptions.map(opt => 
                            `<option value="${opt.value}" ${opt.value === sessao.status ? 'selected' : ''}>${opt.label}</option>`
                        ).join('')}
                    </select>
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; font-weight: bold;">Observação (opcional):</label>
                    <textarea id="status-observacao" rows="3" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px;" placeholder="Motivo da mudança de status..."></textarea>
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" class="btn btn-secondary">Cancelar</button>
                    <button id="btn-salvar-status" class="btn btn-primary">💾 Salvar</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        document.getElementById('btn-salvar-status').onclick = async () => {
            const novoStatus = document.getElementById('novo-status').value;
            const observacao = document.getElementById('status-observacao').value;
            
            try {
                const updateData = {
                    status: novoStatus
                };
                
                // Adicionar observação se fornecida
                if (observacao) {
                    const obsAtual = sessao.observacoes || '';
                    const timestamp = new Date().toLocaleString('pt-BR');
                    updateData.observacoes = obsAtual + `\n[${timestamp}] Status alterado para "${novoStatus}": ${observacao}`;
                }
                
                const response = await fetch(`/api/sessoes/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updateData)
                });
                
                if (response.ok) {
                    showToast('Status atualizado com sucesso!', 'success');
                    modal.remove();
                    carregarSessoes();
                } else {
                    throw new Error('Erro ao atualizar status');
                }
            } catch (error) {
                console.error('Erro:', error);
                showToast('Erro ao atualizar status', 'error');
            }
        };
        
    } catch (error) {
        console.error('Erro ao atualizar status:', error);
        showToast('Erro ao carregar dados da sessão', 'error');
    }
}

// ===== RELATÓRIOS =====

async function gerarRelatorioFornecedores() {
    const mes = document.getElementById('filtro-mes-fornecedores').value;
    if (!mes) {
        showToast('Selecione um mês para gerar o relatório', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/relatorio-fornecedores?mes=${mes}`);
        if (!response.ok) throw new Error('Erro ao gerar relatório');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `relatorio_fornecedores_${mes}.pdf`;
        a.click();
        
        showToast('Relatório gerado com sucesso!', 'success');
        
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro ao gerar relatório', 'error');
    }
}

async function verDetalhesFornecedor(id) {
    try {
        // Buscar dados do fornecedor
        const response = await fetch(`/api/fornecedores/${id}`);
        if (!response.ok) throw new Error('Erro ao carregar fornecedor');
        
        const fornecedor = await response.json();
        
        // Buscar histórico de trabalhos (sessões)
        const sessoesResponse = await fetch(`/api/sessoes?fornecedor_id=${id}`);
        const sessoes = sessoesResponse.ok ? await sessoesResponse.json() : [];
        
        // Calcular estatísticas
        const totalSessoes = sessoes.length;
        const totalPago = sessoes.reduce((sum, s) => {
            const equipeMembro = s.equipe?.find(e => e.fornecedor_id === id);
            return sum + (parseFloat(equipeMembro?.valor_combinado || 0));
        }, 0);
        
        const sessoesRealizadas = sessoes.filter(s => s.status === 'realizada' || s.status.startsWith('entrega'));
        
        // Criar modal
        const modal = document.createElement('div');
        modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10000; display: flex; align-items: center; justify-content: center; overflow-y: auto;';
        modal.innerHTML = `
            <div style="background: white; padding: 30px; border-radius: 10px; max-width: 700px; width: 90%; max-height: 90vh; overflow-y: auto; margin: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 25px;">
                    <div>
                        <h2 style="margin: 0 0 5px 0;">👤 ${fornecedor.nome || fornecedor.razao_social}</h2>
                        <p style="margin: 0; color: #666;">${fornecedor.tipo || 'Fornecedor'}</p>
                    </div>
                    <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #999;">&times;</button>
                </div>
                
                <!-- Informações de Contato -->
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 15px 0; font-size: 16px;">📞 Informações de Contato</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                        ${fornecedor.email ? `<div><strong>Email:</strong> ${fornecedor.email}</div>` : ''}
                        ${fornecedor.telefone ? `<div><strong>Telefone:</strong> ${fornecedor.telefone}</div>` : ''}
                        ${fornecedor.celular ? `<div><strong>Celular:</strong> ${fornecedor.celular}</div>` : ''}
                        ${fornecedor.cpf_cnpj ? `<div><strong>CPF/CNPJ:</strong> ${fornecedor.cpf_cnpj}</div>` : ''}
                    </div>
                </div>
                
                <!-- Estatísticas -->
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 28px; font-weight: bold;">${totalSessoes}</div>
                        <div style="font-size: 14px; opacity: 0.9;">Total de Sessões</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 28px; font-weight: bold;">${sessoesRealizadas.length}</div>
                        <div style="font-size: 14px; opacity: 0.9;">Realizadas</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 20px; font-weight: bold;">R$ ${totalPago.toFixed(2)}</div>
                        <div style="font-size: 14px; opacity: 0.9;">Total Pago</div>
                    </div>
                </div>
                
                <!-- Histórico de Trabalhos -->
                <div style="margin-bottom: 20px;">
                    <h3 style="margin: 0 0 15px 0; font-size: 16px;">📋 Histórico de Trabalhos</h3>
                    <div style="max-height: 300px; overflow-y: auto; border: 1px solid #e0e0e0; border-radius: 5px;">
                        ${sessoes.length === 0 ? 
                            '<div style="padding: 20px; text-align: center; color: #999;">Nenhuma sessão registrada</div>' :
                            sessoes.map(s => {
                                const equipeMembro = s.equipe?.find(e => e.fornecedor_id === id);
                                return `
                                    <div style="padding: 15px; border-bottom: 1px solid #e0e0e0;">
                                        <div style="display: flex; justify-content: space-between; align-items: start;">
                                            <div>
                                                <div style="font-weight: bold;">${s.cliente_nome}</div>
                                                <div style="font-size: 14px; color: #666;">${formatarData(s.data_sessao)} - ${s.tipo_sessao}</div>
                                                <div style="font-size: 13px; color: #999;">Função: ${equipeMembro?.funcao || 'N/A'}</div>
                                            </div>
                                            <div style="text-align: right;">
                                                <div style="background: ${getCorStatusSessao(s.status)}; color: white; padding: 3px 8px; border-radius: 10px; font-size: 11px; margin-bottom: 5px;">
                                                    ${s.status}
                                                </div>
                                                <div style="font-weight: bold; color: #27ae60;">R$ ${parseFloat(equipeMembro?.valor_combinado || 0).toFixed(2)}</div>
                                            </div>
                                        </div>
                                    </div>
                                `;
                            }).join('')
                        }
                    </div>
                </div>
                
                <!-- Observações -->
                ${fornecedor.observacoes ? `
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
                        <strong>📝 Observações:</strong><br>
                        ${fornecedor.observacoes}
                    </div>
                ` : ''}
                
                <div style="margin-top: 25px; display: flex; gap: 10px; justify-content: flex-end;">
                    <button onclick="window.open('/fornecedor/${id}/editar', '_blank')" class="btn btn-secondary">✏️ Editar Fornecedor</button>
                    <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" class="btn btn-primary">Fechar</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
    } catch (error) {
        console.error('Erro ao carregar detalhes:', error);
        showToast('Erro ao carregar detalhes do fornecedor', 'error');
    }
}

// ===== HELPERS =====

async function carregarClientesDropdown(selectId) {
    try {
        const response = await fetch('/api/clientes');
        if (!response.ok) throw new Error('Erro ao carregar clientes');
        
        const clientes = await response.json();
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">Selecione...</option>';
        
        clientes.forEach(c => {
            const option = document.createElement('option');
            option.value = c.id;
            option.textContent = c.nome || c.razao_social || 'Sem nome';
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Erro ao carregar clientes:', error);
    }
}

function aplicarMascaraMoeda(elementOrId) {
    const element = typeof elementOrId === 'string' ? document.getElementById(elementOrId) : elementOrId;
    if (!element) return;
    
    element.addEventListener('input', function(e) {
        let value = e.target.value.replace(/\D/g, '');
        value = (parseInt(value) / 100).toFixed(2);
        e.target.value = formatarMoeda(value);
    });
}

function formatarMoeda(valor) {
    if (!valor && valor !== 0) return 'R$ 0,00';
    const numero = typeof valor === 'string' ? parseFloat(valor) : valor;
    return 'R$ ' + numero.toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

function formatarData(data) {
    if (!data) return '';
    const partes = data.split('-');
    return `${partes[2]}/${partes[1]}/${partes[0]}`;
}

// ===== EXPORTAR FUNÇÕES PARA O ESCOPO GLOBAL =====
// Garantir que as funções estejam disponíveis globalmente para os botões HTML
window.novoContrato = novoContrato;
window.cancelarContrato = cancelarContrato;
window.editarContrato = editarContrato;
window.excluirContrato = excluirContrato;
window.adicionarComissao = adicionarComissao;
window.removerComissao = removerComissao;

window.novaSessao = novaSessao;
window.cancelarSessao = cancelarSessao;
window.editarSessao = editarSessao;
window.excluirSessao = excluirSessao;
window.adicionarEquipe = adicionarEquipe;
window.removerEquipe = removerEquipe;
window.aplicarTemplateEquipe = aplicarTemplateEquipe;
window.adicionarKit = adicionarKit;
window.removerKit = removerKit;
window.adicionarEquipamentoAlugado = adicionarEquipamentoAlugado;
window.removerEquipamentoAlugado = removerEquipamentoAlugado;
window.adicionarCustoAdicional = adicionarCustoAdicional;
window.removerCustoAdicional = removerCustoAdicional;
window.adicionarTag = adicionarTag;

window.switchTabContratos = switchTabContratos;
window.filtrarContratos = filtrarContratos;
window.filtrarSessoes = filtrarSessoes;
window.atualizarStatusSessao = atualizarStatusSessao;
window.carregarContratosCliente = carregarContratosCliente;
window.preencherClienteDoContrato = preencherClienteDoContrato;
window.mostrarSelecaoContrato = mostrarSelecaoContrato;

window.gerarRelatorioFornecedores = gerarRelatorioFornecedores;
window.verDetalhesFornecedor = verDetalhesFornecedor;

console.log('✅ Funções de Contratos e Sessões exportadas para window');
console.log('📋 Funções disponíveis:', {
    novoContrato: typeof window.novoContrato,
    novaSessao: typeof window.novaSessao,
    editarContrato: typeof window.editarContrato,
    editarSessao: typeof window.editarSessao
});
