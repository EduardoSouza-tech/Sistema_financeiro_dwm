// Sistema Financeiro - v20251223debug
// Gerenciamento completo do sistema financeiro
console.log('%c ✓ Sistema Financeiro - app.js v20251223debug carregado ', 'background: #4CAF50; color: white; font-size: 16px; font-weight: bold');
console.log('%c 🔍 Iniciando carregamento de funções... ', 'background: #FF9800; color: white; font-weight: bold');

// Suprimir erros de extensões do navegador
window.addEventListener('error', function(e) {
    if (e.message.includes('message channel closed')) {
        console.log('⚠️ Erro de extensão suprimido:', e.message);
        e.preventDefault();
        return;
    }
});

// Inicialização ao carregar a página
document.addEventListener('DOMContentLoaded', function() {
    // Preencher anos no Comparativo de Períodos
    const anoAtual = new Date().getFullYear();
    const anoAnterior = anoAtual - 1;
    
    const filterAno1 = document.getElementById('filter-ano1');
    const filterAno2 = document.getElementById('filter-ano2');
    
    if (filterAno1) {
        filterAno1.value = anoAnterior;
        console.log(`✓ Período 1 preenchido com ano ${anoAnterior}`);
    }
    if (filterAno2) {
        filterAno2.value = anoAtual;
        console.log(`✓ Período 2 preenchido com ano ${anoAtual}`);
    }
});

// Função auxiliar para mostrar mensagens
function showToast(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Implementação simples - pode ser melhorada com UI toast real
    if (type === 'error') {
        console.error(message);
    }
}

// Estados das tabs
window.clienteTabAtiva = 'ativos';
window.fornecedorTabAtiva = 'ativos';

// === FUNÇÕES DE TABS ===

function showClienteTab(tipo) {
    window.clienteTabAtiva = tipo;
    
    const btnAtivos = document.getElementById('tab-clientes-ativos');
    const btnInativos = document.getElementById('tab-clientes-inativos');
    
    if (tipo === 'ativos') {
        btnAtivos.classList.add('active');
        btnAtivos.style.background = '#9b59b6';
        btnAtivos.style.color = 'white';
        btnAtivos.style.fontWeight = 'bold';
        
        btnInativos.classList.remove('active');
        btnInativos.style.background = '#bdc3c7';
        btnInativos.style.color = '#555';
        btnInativos.style.fontWeight = 'normal';
    } else {
        btnInativos.classList.add('active');
        btnInativos.style.background = '#9b59b6';
        btnInativos.style.color = 'white';
        btnInativos.style.fontWeight = 'bold';
        
        btnAtivos.classList.remove('active');
        btnAtivos.style.background = '#bdc3c7';
        btnAtivos.style.color = '#555';
        btnAtivos.style.fontWeight = 'normal';
    }
    
    loadClientesTable();
}

function showFornecedorTab(tipo) {
    window.fornecedorTabAtiva = tipo;
    
    const btnAtivos = document.getElementById('tab-fornecedores-ativos');
    const btnInativos = document.getElementById('tab-fornecedores-inativos');
    
    if (tipo === 'ativos') {
        btnAtivos.classList.add('active');
        btnAtivos.style.background = '#9b59b6';
        btnAtivos.style.color = 'white';
        btnAtivos.style.fontWeight = 'bold';
        
        btnInativos.classList.remove('active');
        btnInativos.style.background = '#bdc3c7';
        btnInativos.style.color = '#555';
        btnInativos.style.fontWeight = 'normal';
    } else {
        btnInativos.classList.add('active');
        btnInativos.style.background = '#9b59b6';
        btnInativos.style.color = 'white';
        btnInativos.style.fontWeight = 'bold';
        
        btnAtivos.classList.remove('active');
        btnAtivos.style.background = '#bdc3c7';
        btnAtivos.style.color = '#555';
        btnAtivos.style.fontWeight = 'normal';
    }
    
    loadFornecedoresTable();
}

// === FUNÇÕES DE ABAS - CONTRATOS E ESTOQUE ===

function showContratoTab(tipo) {
    const btnContratos = document.getElementById('tab-contratos');
    const btnSessoes = document.getElementById('tab-sessoes');
    const btnComissoes = document.getElementById('tab-comissoes');
    const btnEquipe = document.getElementById('tab-equipe');
    const contentContratos = document.getElementById('tab-content-contratos');
    const contentSessoes = document.getElementById('tab-content-sessoes');
    const contentComissoes = document.getElementById('tab-content-comissoes');
    const contentEquipe = document.getElementById('tab-content-equipe');
    
    // Reset all buttons
    [btnContratos, btnSessoes, btnComissoes, btnEquipe].forEach(btn => {
        if (btn) {
            btn.classList.remove('active');
            btn.style.background = '#bdc3c7';
            btn.style.color = '#555';
            btn.style.fontWeight = 'normal';
        }
    });
    
    // Hide all content
    [contentContratos, contentSessoes, contentComissoes, contentEquipe].forEach(content => {
        if (content) content.style.display = 'none';
    });
    
    // Show selected tab
    if (tipo === 'contratos') {
        btnContratos.classList.add('active');
        btnContratos.style.background = '#9b59b6';
        btnContratos.style.color = 'white';
        btnContratos.style.fontWeight = 'bold';
        contentContratos.style.display = 'block';
        // if (typeof loadContratos === 'function') loadContratos(); // DESATIVADO - endpoint não existe
    } else if (tipo === 'sessoes') {
        btnSessoes.classList.add('active');
        btnSessoes.style.background = '#9b59b6';
        btnSessoes.style.color = 'white';
        btnSessoes.style.fontWeight = 'bold';
        contentSessoes.style.display = 'block';
        if (typeof loadSessoes === 'function') loadSessoes();
    } else if (tipo === 'comissoes') {
        btnComissoes.classList.add('active');
        btnComissoes.style.background = '#9b59b6';
        btnComissoes.style.color = 'white';
        btnComissoes.style.fontWeight = 'bold';
        contentComissoes.style.display = 'block';
        if (typeof loadComissoes === 'function') loadComissoes();
    } else if (tipo === 'equipe') {
        btnEquipe.classList.add('active');
        btnEquipe.style.background = '#9b59b6';
        btnEquipe.style.color = 'white';
        btnEquipe.style.fontWeight = 'bold';
        contentEquipe.style.display = 'block';
        if (typeof loadSessaoEquipe === 'function') loadSessaoEquipe();
    }
}

function showEstoqueTab(tipo) {
    const btnProdutos = document.getElementById('tab-produtos');
    const btnMovimentacoes = document.getElementById('tab-movimentacoes');
    const contentProdutos = document.getElementById('tab-content-produtos');
    const contentMovimentacoes = document.getElementById('tab-content-movimentacoes');
    
    if (tipo === 'produtos') {
        btnProdutos.classList.add('active');
        btnProdutos.style.background = '#9b59b6';
        btnProdutos.style.color = 'white';
        btnProdutos.style.fontWeight = 'bold';
        
        btnMovimentacoes.classList.remove('active');
        btnMovimentacoes.style.background = '#bdc3c7';
        btnMovimentacoes.style.color = '#555';
        btnMovimentacoes.style.fontWeight = 'normal';
        
        contentProdutos.style.display = 'block';
        contentMovimentacoes.style.display = 'none';
        
        // if (typeof loadProdutos === 'function') loadProdutos(); // DESATIVADO - endpoint não existe
    } else {
        btnMovimentacoes.classList.add('active');
        btnMovimentacoes.style.background = '#9b59b6';
        btnMovimentacoes.style.color = 'white';
        btnMovimentacoes.style.fontWeight = 'bold';
        
        btnProdutos.classList.remove('active');
        btnProdutos.style.background = '#bdc3c7';
        btnProdutos.style.color = '#555';
        btnProdutos.style.fontWeight = 'normal';
        
        contentMovimentacoes.style.display = 'block';
        contentProdutos.style.display = 'none';
        
        if (typeof loadMovimentacoes === 'function') loadMovimentacoes();
    }
}

// === FUNÇÕES MODAL - TIPOS DE SESSÃO ===

function openModalTipoSessao(tipoSessao = null) {
    document.getElementById('tipo-sessao-id').value = '';
    document.getElementById('tipo-sessao-nome').value = '';
    document.getElementById('tipo-sessao-ativa').checked = true;
    
    if (tipoSessao) {
        document.getElementById('tipo-sessao-id').value = tipoSessao.id || '';
        document.getElementById('tipo-sessao-nome').value = tipoSessao.nome || '';
        document.getElementById('tipo-sessao-ativa').checked = tipoSessao.ativa !== false;
    }
    
    document.getElementById('modal-tipo-sessao').style.display = 'flex';
}

function closeModalTipoSessao() {
    document.getElementById('modal-tipo-sessao').style.display = 'none';
}

async function salvarTipoSessao() {
    const id = document.getElementById('tipo-sessao-id').value;
    const nome = document.getElementById('tipo-sessao-nome').value.trim();
    const ativa = document.getElementById('tipo-sessao-ativa').checked;
    
    if (!nome) {
        alert('Por favor, preencha o nome do tipo de sessão');
        return;
    }
    
    const dados = { nome, ativa };
    
    try {
        const url = id ? `/api/tipos-sessao/${id}` : '/api/tipos-sessao';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(id ? 'Tipo de sessão atualizado com sucesso!' : 'Tipo de sessão cadastrado com sucesso!');
            closeModalTipoSessao();
            if (typeof loadTiposSessao === 'function') loadTiposSessao();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao salvar tipo de sessão:', error);
        alert('Erro ao salvar tipo de sessão');
    }
}

// === FUNÇÕES MODAL - CONTRATOS ===

function openModalContrato(contrato = null) {
    document.getElementById('contrato-id').value = '';
    document.getElementById('contrato-numero').value = '';
    document.getElementById('contrato-cliente-id').value = '';
    document.getElementById('contrato-valor-total').value = '';
    document.getElementById('contrato-data-assinatura').value = '';
    document.getElementById('contrato-status').value = 'ativo';
    document.getElementById('contrato-observacoes').value = '';
    
    if (contrato) {
        document.getElementById('contrato-id').value = contrato.id || '';
        document.getElementById('contrato-numero').value = contrato.numero || '';
        document.getElementById('contrato-cliente-id').value = contrato.cliente_id || '';
        document.getElementById('contrato-valor-total').value = contrato.valor_total || '';
        document.getElementById('contrato-data-assinatura').value = contrato.data_assinatura || '';
        document.getElementById('contrato-status').value = contrato.status || 'ativo';
        document.getElementById('contrato-observacoes').value = contrato.observacoes || '';
    }
    
    // Carregar clientes no select
    if (typeof loadClientes === 'function') {
        loadClientes().then(clientes => {
            const select = document.getElementById('contrato-cliente-id');
            select.innerHTML = '<option value="">Selecione o cliente</option>';
            clientes.forEach(cli => {
                const option = document.createElement('option');
                option.value = cli.id;
                option.textContent = cli.razao_social || cli.nome || '-';
                select.appendChild(option);
            });
            if (contrato && contrato.cliente_id) {
                select.value = contrato.cliente_id;
            }
        });
    }
    
    document.getElementById('modal-contrato').style.display = 'flex';
}

function closeModalContrato() {
    document.getElementById('modal-contrato').style.display = 'none';
}

async function salvarContrato() {
    const id = document.getElementById('contrato-id').value;
    const numero = document.getElementById('contrato-numero').value.trim();
    const cliente_id = document.getElementById('contrato-cliente-id').value;
    const valor_total = parseFloat(document.getElementById('contrato-valor-total').value);
    const data_assinatura = document.getElementById('contrato-data-assinatura').value;
    const status = document.getElementById('contrato-status').value;
    const observacoes = document.getElementById('contrato-observacoes').value.trim();
    
    if (!numero || !cliente_id || !valor_total || !data_assinatura) {
        alert('Por favor, preencha todos os campos obrigatórios');
        return;
    }
    
    const dados = {
        numero,
        cliente_id: parseInt(cliente_id),
        valor_total,
        data_assinatura,
        status,
        observacoes
    };
    
    try {
        const url = id ? `/api/contratos/${id}` : '/api/contratos';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(id ? 'Contrato atualizado com sucesso!' : 'Contrato cadastrado com sucesso!');
            closeModalContrato();
            if (typeof loadContratos === 'function') loadContratos();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao salvar contrato:', error);
        alert('Erro ao salvar contrato');
    }
}

// === FUNÇÕES MODAL - SESSÕES ===

function openModalSessao(sessao = null) {
    document.getElementById('sessao-id').value = '';
    document.getElementById('sessao-contrato-id').value = '';
    document.getElementById('sessao-tipo-sessao-id').value = '';
    document.getElementById('sessao-data-prevista').value = '';
    document.getElementById('sessao-data-realizada').value = '';
    document.getElementById('sessao-status').value = 'agendada';
    
    if (sessao) {
        document.getElementById('sessao-id').value = sessao.id || '';
        document.getElementById('sessao-contrato-id').value = sessao.contrato_id || '';
        document.getElementById('sessao-tipo-sessao-id').value = sessao.tipo_sessao_id || '';
        document.getElementById('sessao-data-prevista').value = sessao.data_prevista || '';
        document.getElementById('sessao-data-realizada').value = sessao.data_realizada || '';
        document.getElementById('sessao-status').value = sessao.status || 'agendada';
    }
    
    document.getElementById('modal-sessao').style.display = 'flex';
}

function closeModalSessao() {
    document.getElementById('modal-sessao').style.display = 'none';
}

async function salvarSessao() {
    const id = document.getElementById('sessao-id').value;
    const contrato_id = document.getElementById('sessao-contrato-id').value;
    const tipo_sessao_id = document.getElementById('sessao-tipo-sessao-id').value;
    const data_prevista = document.getElementById('sessao-data-prevista').value;
    const data_realizada = document.getElementById('sessao-data-realizada').value;
    const status = document.getElementById('sessao-status').value;
    
    if (!contrato_id || !tipo_sessao_id || !data_prevista) {
        alert('Por favor, preencha todos os campos obrigatórios');
        return;
    }
    
    const dados = {
        contrato_id: parseInt(contrato_id),
        tipo_sessao_id: parseInt(tipo_sessao_id),
        data_prevista,
        data_realizada: data_realizada || null,
        status
    };
    
    try {
        const url = id ? `/api/sessoes/${id}` : '/api/sessoes';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(id ? 'Sessão atualizada com sucesso!' : 'Sessão cadastrada com sucesso!');
            closeModalSessao();
            if (typeof loadSessoes === 'function') loadSessoes();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao salvar sessão:', error);
        alert('Erro ao salvar sessão');
    }
}

// === FUNÇÕES MODAL - AGENDA ===

function openModalAgenda(agenda = null) {
    document.getElementById('agenda-id').value = '';
    document.getElementById('agenda-cliente-id').value = '';
    document.getElementById('agenda-data-hora').value = '';
    document.getElementById('agenda-local').value = '';
    document.getElementById('agenda-tipo').value = '';
    document.getElementById('agenda-status').value = 'confirmado';
    document.getElementById('agenda-observacoes').value = '';
    
    if (agenda) {
        document.getElementById('agenda-id').value = agenda.id || '';
        document.getElementById('agenda-cliente-id').value = agenda.cliente_id || '';
        document.getElementById('agenda-data-hora').value = agenda.data_hora || '';
        document.getElementById('agenda-local').value = agenda.local || '';
        document.getElementById('agenda-tipo').value = agenda.tipo || '';
        document.getElementById('agenda-status').value = agenda.status || 'confirmado';
        document.getElementById('agenda-observacoes').value = agenda.observacoes || '';
    }
    
    // Carregar clientes no select
    if (typeof loadClientes === 'function') {
        loadClientes().then(clientes => {
            const select = document.getElementById('agenda-cliente-id');
            select.innerHTML = '<option value="">Selecione o cliente</option>';
            clientes.forEach(cli => {
                const option = document.createElement('option');
                option.value = cli.id;
                option.textContent = cli.razao_social || cli.nome || '-';
                select.appendChild(option);
            });
            if (agenda && agenda.cliente_id) {
                select.value = agenda.cliente_id;
            }
        });
    }
    
    document.getElementById('modal-agenda').style.display = 'flex';
}

function closeModalAgenda() {
    document.getElementById('modal-agenda').style.display = 'none';
}

async function salvarAgenda() {
    const id = document.getElementById('agenda-id').value;
    const cliente_id = document.getElementById('agenda-cliente-id').value;
    const data_hora = document.getElementById('agenda-data-hora').value;
    const local = document.getElementById('agenda-local').value.trim();
    const tipo = document.getElementById('agenda-tipo').value.trim();
    const status = document.getElementById('agenda-status').value;
    const observacoes = document.getElementById('agenda-observacoes').value.trim();
    
    if (!cliente_id || !data_hora) {
        alert('Por favor, preencha os campos obrigatórios (cliente e data/hora)');
        return;
    }
    
    const dados = {
        cliente_id: parseInt(cliente_id),
        data_hora,
        local,
        tipo,
        status,
        observacoes
    };
    
    try {
        const url = id ? `/api/agenda/${id}` : '/api/agenda';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(id ? 'Agendamento atualizado com sucesso!' : 'Agendamento cadastrado com sucesso!');
            closeModalAgenda();
            if (typeof loadAgenda === 'function') loadAgenda();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao salvar agendamento:', error);
        alert('Erro ao salvar agendamento');
    }
}

// === FUNÇÕES MODAL - PRODUTOS ===

function openModalProduto(produto = null) {
    document.getElementById('produto-id').value = '';
    document.getElementById('produto-nome').value = '';
    document.getElementById('produto-codigo').value = '';
    document.getElementById('produto-quantidade').value = '';
    document.getElementById('produto-unidade').value = 'un';
    document.getElementById('produto-valor-unitario').value = '';
    
    if (produto) {
        document.getElementById('produto-id').value = produto.id || '';
        document.getElementById('produto-nome').value = produto.nome || '';
        document.getElementById('produto-codigo').value = produto.codigo || '';
        document.getElementById('produto-quantidade').value = produto.quantidade || '';
        document.getElementById('produto-unidade').value = produto.unidade || 'un';
        document.getElementById('produto-valor-unitario').value = produto.valor_unitario || '';
    }
    
    document.getElementById('modal-produto').style.display = 'flex';
}

function closeModalProduto() {
    document.getElementById('modal-produto').style.display = 'none';
}

async function salvarProduto() {
    const id = document.getElementById('produto-id').value;
    const nome = document.getElementById('produto-nome').value.trim();
    const codigo = document.getElementById('produto-codigo').value.trim();
    const quantidade = parseInt(document.getElementById('produto-quantidade').value);
    const unidade = document.getElementById('produto-unidade').value;
    const valor_unitario = parseFloat(document.getElementById('produto-valor-unitario').value) || 0;
    
    if (!nome || isNaN(quantidade)) {
        alert('Por favor, preencha os campos obrigatórios (nome e quantidade)');
        return;
    }
    
    const dados = {
        nome,
        codigo,
        quantidade,
        unidade,
        valor_unitario
    };
    
    try {
        const url = id ? `/api/estoque/produtos/${id}` : '/api/estoque/produtos';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(id ? 'Produto atualizado com sucesso!' : 'Produto cadastrado com sucesso!');
            closeModalProduto();
            if (typeof loadProdutos === 'function') loadProdutos();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao salvar produto:', error);
        alert('Erro ao salvar produto');
    }
}

// === FUNÇÕES MODAL - MOVIMENTAÇÕES ===

function openModalMovimentacao(movimentacao = null) {
    document.getElementById('movimentacao-id').value = '';
    document.getElementById('movimentacao-produto-id').value = '';
    document.getElementById('movimentacao-tipo').value = 'entrada';
    document.getElementById('movimentacao-quantidade').value = '';
    document.getElementById('movimentacao-data').value = new Date().toISOString().split('T')[0];
    document.getElementById('movimentacao-observacoes').value = '';
    
    if (movimentacao) {
        document.getElementById('movimentacao-id').value = movimentacao.id || '';
        document.getElementById('movimentacao-produto-id').value = movimentacao.produto_id || '';
        document.getElementById('movimentacao-tipo').value = movimentacao.tipo || 'entrada';
        document.getElementById('movimentacao-quantidade').value = movimentacao.quantidade || '';
        document.getElementById('movimentacao-data').value = movimentacao.data || '';
        document.getElementById('movimentacao-observacoes').value = movimentacao.observacoes || '';
    }
    
    document.getElementById('modal-movimentacao').style.display = 'flex';
}

function closeModalMovimentacao() {
    document.getElementById('modal-movimentacao').style.display = 'none';
}

async function salvarMovimentacao() {
    const id = document.getElementById('movimentacao-id').value;
    const produto_id = document.getElementById('movimentacao-produto-id').value;
    const tipo = document.getElementById('movimentacao-tipo').value;
    const quantidade = parseInt(document.getElementById('movimentacao-quantidade').value);
    const data = document.getElementById('movimentacao-data').value;
    const observacoes = document.getElementById('movimentacao-observacoes').value.trim();
    
    if (!produto_id || isNaN(quantidade) || quantidade <= 0 || !data) {
        alert('Por favor, preencha todos os campos obrigatórios corretamente');
        return;
    }
    
    const dados = {
        produto_id: parseInt(produto_id),
        tipo,
        quantidade,
        data,
        observacoes
    };
    
    try {
        const url = id ? `/api/estoque/movimentacoes/${id}` : '/api/estoque/movimentacoes';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(id ? 'Movimentação atualizada com sucesso!' : 'Movimentação cadastrada com sucesso!');
            closeModalMovimentacao();
            if (typeof loadMovimentacoes === 'function') loadMovimentacoes();
            if (typeof loadProdutos === 'function') loadProdutos(); // Atualizar estoque
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao salvar movimentação:', error);
        alert('Erro ao salvar movimentação');
    }
}

// === FUNÇÕES MODAL - KITS ===

function openModalKit(kit = null) {
    document.getElementById('kit-id').value = '';
    document.getElementById('kit-nome').value = '';
    document.getElementById('kit-descricao').value = '';
    document.getElementById('kit-itens').value = '';
    document.getElementById('kit-valor-total').value = '';
    
    if (kit) {
        document.getElementById('kit-id').value = kit.id || '';
        document.getElementById('kit-nome').value = kit.nome || '';
        document.getElementById('kit-descricao').value = kit.descricao || '';
        document.getElementById('kit-itens').value = kit.itens ? kit.itens.join('\n') : '';
        document.getElementById('kit-valor-total').value = kit.valor_total || '';
    }
    
    document.getElementById('modal-kit').style.display = 'flex';
}

function closeModalKit() {
    document.getElementById('modal-kit').style.display = 'none';
}

async function salvarKit() {
    const id = document.getElementById('kit-id').value;
    const nome = document.getElementById('kit-nome').value.trim();
    const descricao = document.getElementById('kit-descricao').value.trim();
    const itensTexto = document.getElementById('kit-itens').value.trim();
    const valor_total = parseFloat(document.getElementById('kit-valor-total').value) || 0;
    
    if (!nome) {
        alert('Por favor, preencha o nome do kit');
        return;
    }
    
    const itens = itensTexto.split('\n').map(i => i.trim()).filter(i => i.length > 0);
    
    const dados = {
        nome,
        descricao,
        itens,
        valor_total
    };
    
    try {
        const url = id ? `/api/kits/${id}` : '/api/kits';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(id ? 'Kit atualizado com sucesso!' : 'Kit cadastrado com sucesso!');
            closeModalKit();
            if (typeof loadKits === 'function') loadKits();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao salvar kit:', error);
        alert('Erro ao salvar kit');
    }
}

// === FUNÇÕES MODAL - COMISSÕES ===

function openModalComissao(comissao = null) {
    document.getElementById('comissao-id').value = '';
    document.getElementById('comissao-contrato-id').value = '';
    document.getElementById('comissao-pessoa').value = '';
    document.getElementById('comissao-tipo').value = 'percentual';
    document.getElementById('comissao-valor').value = '';
    document.getElementById('comissao-percentual').value = '';
    
    if (comissao) {
        document.getElementById('comissao-id').value = comissao.id || '';
        document.getElementById('comissao-contrato-id').value = comissao.contrato_id || '';
        document.getElementById('comissao-pessoa').value = comissao.pessoa || '';
        document.getElementById('comissao-tipo').value = comissao.tipo || 'percentual';
        document.getElementById('comissao-valor').value = comissao.valor || '';
        document.getElementById('comissao-percentual').value = comissao.percentual || '';
    }
    
    document.getElementById('modal-comissao').style.display = 'flex';
}

function closeModalComissao() {
    document.getElementById('modal-comissao').style.display = 'none';
}

async function salvarComissao() {
    const id = document.getElementById('comissao-id').value;
    const contrato_id = document.getElementById('comissao-contrato-id').value;
    const pessoa = document.getElementById('comissao-pessoa').value.trim();
    const tipo = document.getElementById('comissao-tipo').value;
    const valor = parseFloat(document.getElementById('comissao-valor').value) || 0;
    const percentual = parseFloat(document.getElementById('comissao-percentual').value) || 0;
    
    if (!contrato_id || !pessoa) {
        alert('Por favor, preencha os campos obrigatórios (contrato e pessoa)');
        return;
    }
    
    const dados = {
        contrato_id: parseInt(contrato_id),
        pessoa,
        tipo,
        valor,
        percentual
    };
    
    try {
        const url = id ? `/api/comissoes/${id}` : '/api/comissoes';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(id ? 'Comissão atualizada com sucesso!' : 'Comissão cadastrada com sucesso!');
            closeModalComissao();
            if (typeof loadComissoes === 'function') loadComissoes();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao salvar comissão:', error);
        alert('Erro ao salvar comissão');
    }
}

// === FUNÇÕES MODAL - SESSÃO EQUIPE ===

function openModalSessaoEquipe(sessaoEquipe = null) {
    document.getElementById('sessao-equipe-id').value = '';
    document.getElementById('sessao-equipe-sessao-id').value = '';
    document.getElementById('sessao-equipe-membro').value = '';
    document.getElementById('sessao-equipe-funcao').value = '';
    document.getElementById('sessao-equipe-observacoes').value = '';
    
    if (sessaoEquipe) {
        document.getElementById('sessao-equipe-id').value = sessaoEquipe.id || '';
        document.getElementById('sessao-equipe-sessao-id').value = sessaoEquipe.sessao_id || '';
        document.getElementById('sessao-equipe-membro').value = sessaoEquipe.membro || '';
        document.getElementById('sessao-equipe-funcao').value = sessaoEquipe.funcao || '';
        document.getElementById('sessao-equipe-observacoes').value = sessaoEquipe.observacoes || '';
    }
    
    document.getElementById('modal-sessao-equipe').style.display = 'flex';
}

function closeModalSessaoEquipe() {
    document.getElementById('modal-sessao-equipe').style.display = 'none';
}

async function salvarSessaoEquipe() {
    const id = document.getElementById('sessao-equipe-id').value;
    const sessao_id = document.getElementById('sessao-equipe-sessao-id').value;
    const membro = document.getElementById('sessao-equipe-membro').value.trim();
    const funcao = document.getElementById('sessao-equipe-funcao').value.trim();
    const observacoes = document.getElementById('sessao-equipe-observacoes').value.trim();
    
    if (!sessao_id || !membro) {
        alert('Por favor, preencha os campos obrigatórios (sessão e membro)');
        return;
    }
    
    const dados = {
        sessao_id: parseInt(sessao_id),
        membro,
        funcao,
        observacoes
    };
    
    try {
        const url = id ? `/api/sessao-equipe/${id}` : '/api/sessao-equipe';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(id ? 'Membro atualizado com sucesso!' : 'Membro adicionado com sucesso!');
            closeModalSessaoEquipe();
            if (typeof loadSessaoEquipe === 'function') loadSessaoEquipe();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao salvar membro da equipe:', error);
        alert('Erro ao salvar membro da equipe');
    }
}

// === FUNÇÕES MODAL - TAGS ===

function openModalTag(tag = null) {
    document.getElementById('tag-id').value = '';
    document.getElementById('tag-nome').value = '';
    document.getElementById('tag-cor').value = '#9b59b6';
    
    if (tag) {
        document.getElementById('tag-id').value = tag.id || '';
        document.getElementById('tag-nome').value = tag.nome || '';
        document.getElementById('tag-cor').value = tag.cor || '#9b59b6';
    }
    
    document.getElementById('modal-tag').style.display = 'flex';
}

function closeModalTag() {
    document.getElementById('modal-tag').style.display = 'none';
}

async function salvarTag() {
    const id = document.getElementById('tag-id').value;
    const nome = document.getElementById('tag-nome').value.trim();
    const cor = document.getElementById('tag-cor').value;
    
    if (!nome) {
        alert('Por favor, preencha o nome da tag');
        return;
    }
    
    const dados = { nome, cor };
    
    try {
        const url = id ? `/api/tags/${id}` : '/api/tags';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(id ? 'Tag atualizada com sucesso!' : 'Tag cadastrada com sucesso!');
            closeModalTag();
            if (typeof loadTags === 'function') loadTags();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao salvar tag:', error);
        alert('Erro ao salvar tag');
    }
}

// === FUNÇÕES MODAL - TEMPLATES ===

function openModalTemplate(template = null) {
    document.getElementById('template-id').value = '';
    document.getElementById('template-nome').value = '';
    document.getElementById('template-descricao').value = '';
    document.getElementById('template-membros').value = '';
    
    if (template) {
        document.getElementById('template-id').value = template.id || '';
        document.getElementById('template-nome').value = template.nome || '';
        document.getElementById('template-descricao').value = template.descricao || '';
        document.getElementById('template-membros').value = template.membros ? template.membros.join('\n') : '';
    }
    
    document.getElementById('modal-template').style.display = 'flex';
}

function closeModalTemplate() {
    document.getElementById('modal-template').style.display = 'none';
}

async function salvarTemplate() {
    const id = document.getElementById('template-id').value;
    const nome = document.getElementById('template-nome').value.trim();
    const descricao = document.getElementById('template-descricao').value.trim();
    const membrosTexto = document.getElementById('template-membros').value.trim();
    
    if (!nome) {
        alert('Por favor, preencha o nome do template');
        return;
    }
    
    const membros = membrosTexto.split('\n').map(m => m.trim()).filter(m => m.length > 0);
    
    const dados = {
        nome,
        descricao,
        membros
    };
    
    try {
        const url = id ? `/api/templates-equipe/${id}` : '/api/templates-equipe';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(id ? 'Template atualizado com sucesso!' : 'Template cadastrado com sucesso!');
            closeModalTemplate();
            if (typeof loadTemplates === 'function') loadTemplates();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao salvar template:', error);
        alert('Erro ao salvar template');
    }
}

// === FUNÇÕES DE CARREGAMENTO ===

// Função auxiliar para carregar categorias no array global
async function loadCategorias() {
    try {
        const response = await fetch('/api/categorias');
        const categoriasList = await response.json();
        
        // Armazenar no objeto global
        window.categorias = categoriasList;
        return categoriasList;
    } catch (error) {
        console.error('Erro ao carregar categorias:', error);
        window.categorias = [];
        return [];
    }
}

// Função auxiliar para carregar clientes no array global
async function loadClientes() {
    try {
        const response = await fetch('/api/clientes?ativos=true');
        const clientesList = await response.json();
        
        // Armazenar no objeto global
        window.clientes = clientesList;
        // Clientes carregados
        return clientesList;
    } catch (error) {
        console.error('Erro ao carregar clientes:', error);
        window.clientes = [];
        return [];
    }
}

// Função auxiliar para carregar fornecedores no array global
async function loadFornecedores() {
    try {
        const response = await fetch('/api/fornecedores?ativos=true');
        const fornecedoresList = await response.json();
        
        // Armazenar no objeto global
        window.fornecedores = fornecedoresList;
        // Fornecedores carregados
        return fornecedoresList;
    } catch (error) {
        console.error('Erro ao carregar fornecedores:', error);
        window.fornecedores = [];
        return [];
    }
}

async function loadClientesTable() {
    const ativos = window.clienteTabAtiva === 'ativos';
    
    try {
        const response = await fetch(`/api/clientes?ativos=${ativos}`);
        const clientesList = await response.json();
        
        const tbody = document.getElementById('tbody-clientes');
        const thDataInativacao = document.getElementById('th-data-inativacao-cliente');
        if (!tbody) return;
        
        // Mostrar/ocultar coluna de data de inativação
        if (thDataInativacao) {
            thDataInativacao.style.display = ativos ? 'none' : 'table-cell';
        }
        
        tbody.innerHTML = '';
        
        const colspan = ativos ? '6' : '7';
        if (clientesList.length === 0) {
            tbody.innerHTML = `<tr><td colspan="${colspan}" class="empty-state">Nenhum cliente ${ativos ? 'ativo' : 'inativo'} cadastrado</td></tr>`;
            return;
        }
        
        window.clientesData = {};
        
        clientesList.forEach((cli, index) => {
            const tr = document.createElement('tr');
            const nome = cli.nome || cli.razao_social || '';
            
            window.clientesData[index] = cli;
            
            let acoesBtns = '';
            let dataInativacaoCell = '';
            
            if (ativos) {
                acoesBtns = `
                    <button class="btn btn-primary btn-small btn-editar-cliente" data-index="${index}" title="Editar">✏️</button>
                    <button class="btn btn-warning btn-small" onclick="openModalInativarCliente('${nome}')" title="Inativar" style="background: #f39c12;">🔒</button>
                    <button class="btn btn-danger btn-small" onclick="excluirCliente('${nome}')" title="Excluir">🗑️</button>
                `;
            } else {
                const dataFormatada = cli.data_inativacao ? new Date(cli.data_inativacao).toLocaleDateString('pt-BR') : '-';
                dataInativacaoCell = `<td>${dataFormatada}</td>`;
                
                acoesBtns = `
                    <button class="btn btn-success btn-small" onclick="reativarCliente('${nome}')" title="Reativar">✅</button>
                    <button class="btn btn-info btn-small" onclick="verMotivoInativacao('${nome}', '${cli.motivo_inativacao || 'Sem motivo'}', '${cli.data_inativacao || ''}')" title="Ver Motivo">ℹ️</button>
                    <button class="btn btn-danger btn-small" onclick="excluirCliente('${nome}')" title="Excluir">🗑️</button>
                `;
            }
            
            tr.innerHTML = `
                <td>${cli.razao_social || cli.nome || '-'}</td>
                <td>${cli.nome_fantasia || '-'}</td>
                <td>${cli.cnpj || '-'}</td>
                <td>${cli.cidade || '-'}</td>
                <td>${cli.telefone || cli.contato || '-'}</td>
                ${dataInativacaoCell}
                <td>${acoesBtns}</td>
            `;
            tbody.appendChild(tr);
        });
        
        if (ativos) {
            document.querySelectorAll('.btn-editar-cliente').forEach(btn => {
                btn.addEventListener('click', function() {
                    const index = parseInt(this.getAttribute('data-index'));
                    const cliente = window.clientesData[index];
                    if (cliente) {
                        openModalCliente(cliente);
                    }
                });
            });
        }
    } catch (error) {
        console.error('Erro ao carregar clientes:', error);
    }
}

async function loadFornecedoresTable() {
    const ativos = window.fornecedorTabAtiva === 'ativos';
    
    try {
        const response = await fetch(`/api/fornecedores?ativos=${ativos}`);
        const fornecedoresList = await response.json();
        
        const tbody = document.getElementById('tbody-fornecedores');
        const thDataInativacao = document.getElementById('th-data-inativacao-fornecedor');
        if (!tbody) return;
        
        // Mostrar/ocultar coluna de data de inativação
        if (thDataInativacao) {
            thDataInativacao.style.display = ativos ? 'none' : 'table-cell';
        }
        
        tbody.innerHTML = '';
        
        const colspan = ativos ? '6' : '7';
        if (fornecedoresList.length === 0) {
            tbody.innerHTML = `<tr><td colspan="${colspan}" class="empty-state">Nenhum fornecedor ${ativos ? 'ativo' : 'inativo'} cadastrado</td></tr>`;
            return;
        }
        
        window.fornecedoresData = {};
        
        fornecedoresList.forEach((forn, index) => {
            const tr = document.createElement('tr');
            const nome = forn.nome || forn.razao_social || '';
            
            window.fornecedoresData[index] = forn;
            
            let acoesBtns = '';
            let dataInativacaoCell = '';
            
            if (ativos) {
                acoesBtns = `
                    <button class="btn btn-primary btn-small btn-editar-fornecedor" data-index="${index}" title="Editar">✏️</button>
                    <button class="btn btn-warning btn-small" onclick="openModalInativarFornecedor('${nome}')" title="Inativar" style="background: #f39c12;">🔒</button>
                    <button class="btn btn-danger btn-small" onclick="excluirFornecedor('${nome}')" title="Excluir">🗑️</button>
                `;
            } else {
                const dataFormatada = forn.data_inativacao ? new Date(forn.data_inativacao).toLocaleDateString('pt-BR') : '-';
                dataInativacaoCell = `<td>${dataFormatada}</td>`;
                
                acoesBtns = `
                    <button class="btn btn-success btn-small" onclick="reativarFornecedor('${nome}')" title="Reativar">✅</button>
                    <button class="btn btn-info btn-small" onclick="verMotivoInativacao('${nome}', '${forn.motivo_inativacao || 'Sem motivo'}', '${forn.data_inativacao || ''}')" title="Ver Motivo">ℹ️</button>
                    <button class="btn btn-danger btn-small" onclick="excluirFornecedor('${nome}')" title="Excluir">🗑️</button>
                `;
            }
            
            tr.innerHTML = `
                <td>${forn.razao_social || forn.nome || '-'}</td>
                <td>${forn.nome_fantasia || '-'}</td>
                <td>${forn.cnpj || '-'}</td>
                <td>${forn.cidade || '-'}</td>
                <td>${forn.telefone || forn.contato || '-'}</td>
                ${dataInativacaoCell}
                <td>${acoesBtns}</td>
            `;
            tbody.appendChild(tr);
        });
        
        if (ativos) {
            document.querySelectorAll('.btn-editar-fornecedor').forEach(btn => {
                btn.addEventListener('click', function() {
                    const index = parseInt(this.getAttribute('data-index'));
                    const fornecedor = window.fornecedoresData[index];
                    if (fornecedor) {
                        openModalFornecedor(fornecedor);
                    }
                });
            });
        }
    } catch (error) {
        console.error('Erro ao carregar fornecedores:', error);
    }
}

// === FUNÇÕES DE INATIVAÇÃO ===

let clienteParaInativar = null;
let fornecedorParaInativar = null;

function openModalInativarCliente(nome) {
    clienteParaInativar = nome;
    document.getElementById('inativar-cliente-nome').textContent = nome;
    document.getElementById('inativar-cliente-motivo').value = '';
    document.getElementById('modal-inativar-cliente').style.display = 'flex';
}

function closeModalInativarCliente() {
    clienteParaInativar = null;
    document.getElementById('modal-inativar-cliente').style.display = 'none';
}

async function confirmarInativarCliente() {
    if (!clienteParaInativar) return;
    
    const motivo = document.getElementById('inativar-cliente-motivo').value.trim();
    
    if (!motivo) {
        alert('Por favor, informe o motivo da inativação');
        return;
    }
    
    try {
        const response = await fetch(`/api/clientes/${encodeURIComponent(clienteParaInativar)}/inativar`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({motivo: motivo})
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Cliente inativado com sucesso!');
            closeModalInativarCliente();
            loadClientesTable();
        } else {
            alert('Erro: ' + (result.error || result.message || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao inativar cliente:', error);
        alert('Erro ao inativar cliente');
    }
}

async function reativarCliente(nome) {
    if (!confirm(`Deseja realmente reativar o cliente ${nome}?`)) return;
    
    try {
        const response = await fetch(`/api/clientes/${encodeURIComponent(nome)}/reativar`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Cliente reativado com sucesso!');
            loadClientesTable();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao reativar cliente:', error);
        alert('Erro ao reativar cliente');
    }
}

async function excluirCliente(nome) {
    if (!confirm(`Deseja realmente EXCLUIR o cliente ${nome}?\n\nATENÇÃO: Esta ação é permanente e só será permitida se não houver lançamentos vinculados.`)) return;
    
    try {
        const response = await fetch(`/api/clientes/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Cliente excluído com sucesso!');
            loadClientesTable();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao excluir cliente:', error);
        alert('Erro ao excluir cliente');
    }
}

function openModalInativarFornecedor(nome) {
    fornecedorParaInativar = nome;
    document.getElementById('inativar-fornecedor-nome').textContent = nome;
    document.getElementById('inativar-fornecedor-motivo').value = '';
    document.getElementById('modal-inativar-fornecedor').style.display = 'flex';
}

function closeModalInativarFornecedor() {
    fornecedorParaInativar = null;
    document.getElementById('modal-inativar-fornecedor').style.display = 'none';
}

async function confirmarInativarFornecedor() {
    if (!fornecedorParaInativar) return;
    
    const motivo = document.getElementById('inativar-fornecedor-motivo').value.trim();
    
    if (!motivo) {
        alert('Por favor, informe o motivo da inativação');
        return;
    }
    
    try {
        const response = await fetch(`/api/fornecedores/${encodeURIComponent(fornecedorParaInativar)}/inativar`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({motivo: motivo})
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Fornecedor inativado com sucesso!');
            closeModalInativarFornecedor();
            loadFornecedoresTable();
        } else {
            alert('Erro: ' + (result.error || result.message || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao inativar fornecedor:', error);
        alert('Erro ao inativar fornecedor');
    }
}

async function reativarFornecedor(nome) {
    if (!confirm(`Deseja realmente reativar o fornecedor ${nome}?`)) return;
    
    try {
        const response = await fetch(`/api/fornecedores/${encodeURIComponent(nome)}/reativar`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Fornecedor reativado com sucesso!');
            loadFornecedoresTable();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao reativar fornecedor:', error);
        alert('Erro ao reativar fornecedor');
    }
}

async function excluirFornecedor(nome) {
    if (!confirm(`Deseja realmente EXCLUIR o fornecedor ${nome}?\n\nATENÇÃO: Esta ação é permanente e só será permitida se não houver lançamentos vinculados.`)) return;
    
    try {
        const response = await fetch(`/api/fornecedores/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Fornecedor excluído com sucesso!');
            loadFornecedoresTable();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao excluir fornecedor:', error);
        alert('Erro ao excluir fornecedor');
    }
}

function verMotivoInativacao(nome, motivo, data) {
    document.getElementById('motivo-nome').textContent = nome;
    document.getElementById('motivo-texto').textContent = motivo || 'Nenhum motivo informado';
    
    const dataFormatada = data ? new Date(data).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }) : 'Data não disponível';
    
    document.getElementById('motivo-data').textContent = dataFormatada;
    document.getElementById('modal-motivo-inativacao').style.display = 'flex';
}

function closeModalMotivoInativacao() {
    document.getElementById('modal-motivo-inativacao').style.display = 'none';
}

// === FUNÇÕES DE CONTAS BANCÁRIAS ===

// Armazenar todas as contas para filtragem
let todasAsContas = [];

async function loadContasBancarias() {
    try {
        const response = await fetch('/api/contas');
        const contas = await response.json();
        
        // Armazenar contas para filtro
        todasAsContas = contas;
        
        // Atualizar select de bancos
        atualizarFiltroBancos(contas);
        
        // Calcular e exibir saldo total
        const saldoTotal = contas.reduce((total, conta) => {
            return total + parseFloat(conta.saldo || conta.saldo_atual || 0);
        }, 0);
        
        const saldoTotalDisplay = document.getElementById('saldo-total-display');
        if (saldoTotalDisplay) {
            saldoTotalDisplay.textContent = `R$ ${saldoTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        }
        
        // Exibir contas
        exibirContas(contas);
    } catch (error) {
        console.error('Erro ao carregar contas bancárias:', error);
        showToast('Erro ao carregar contas bancárias', 'error');
    }
}

function atualizarFiltroBancos(contas) {
    const selectBanco = document.getElementById('filtro-banco');
    if (!selectBanco) return;
    
    // Extrair bancos únicos
    const bancosUnicos = [...new Set(contas.map(c => c.banco))].filter(b => b).sort();
    
    // Manter o valor selecionado atual
    const valorAtual = selectBanco.value;
    
    // Limpar e recriar opções
    selectBanco.innerHTML = '<option value="">Todos os Bancos</option>';
    bancosUnicos.forEach(banco => {
        const option = document.createElement('option');
        option.value = banco;
        option.textContent = banco;
        selectBanco.appendChild(option);
    });
    
    // Restaurar valor se ainda existir
    if (valorAtual && bancosUnicos.includes(valorAtual)) {
        selectBanco.value = valorAtual;
    }
}

function exibirContas(contas) {
    const tbody = document.getElementById('tbody-contas');
    if (!tbody) {
        console.error('Tabela de contas não encontrada');
        return;
    }
    
    tbody.innerHTML = '';
    
    if (contas.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhuma conta bancária encontrada</td></tr>';
        return;
    }
    
    contas.forEach(conta => {
        const tr = document.createElement('tr');
        const saldoInicial = parseFloat(conta.saldo_inicial || 0);
        const saldoAtual = parseFloat(conta.saldo || conta.saldo_atual || 0);
        
        tr.innerHTML = `
            <td>${conta.banco || '-'}</td>
            <td>${conta.agencia || '-'}</td>
            <td>${conta.conta || '-'}</td>
            <td>R$ ${saldoInicial.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            <td>R$ ${saldoAtual.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            <td>
                <button class="btn btn-warning btn-small" onclick="editarConta('${conta.nome.replace(/'/g, "\\'")}')">✏️</button>
                <button class="btn btn-danger btn-small" onclick="excluirConta('${conta.nome.replace(/'/g, "\\'")}')">🗑️</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filtrarPorBanco() {
    const selectBanco = document.getElementById('filtro-banco');
    if (!selectBanco) return;
    
    const bancoSelecionado = selectBanco.value;
    
    // Filtrar contas
    let contasFiltradas = todasAsContas;
    if (bancoSelecionado) {
        contasFiltradas = todasAsContas.filter(c => c.banco === bancoSelecionado);
    }
    
    // Atualizar saldo total filtrado
    const saldoTotal = contasFiltradas.reduce((total, conta) => {
        return total + parseFloat(conta.saldo || conta.saldo_atual || 0);
    }, 0);
    
    const saldoTotalDisplay = document.getElementById('saldo-total-display');
    if (saldoTotalDisplay) {
        saldoTotalDisplay.textContent = `R$ ${saldoTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    }
    
    // Exibir contas filtradas
    exibirContas(contasFiltradas);
}

async function editarConta(nome) {
    try {
        const response = await fetch(`/api/contas/${encodeURIComponent(nome)}`);
        const conta = await response.json();
        
        if (conta && typeof openModalConta === 'function') {
            openModalConta(conta);
        }
    } catch (error) {
        console.error('Erro ao carregar conta para edição:', error);
        showToast('Erro ao carregar conta', 'error');
    }
}

async function excluirConta(nome) {
    if (!confirm(`Deseja realmente excluir a conta bancária "${nome}"?\n\nAtenção: Esta ação não pode ser desfeita!`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/contas/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('✓ Conta bancária excluída com sucesso!', 'success');
            loadContasBancarias();
            if (typeof loadContas === 'function') loadContas();
        } else {
            showToast('Erro: ' + (result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro ao excluir conta:', error);
        showToast('Erro ao excluir conta bancária', 'error');
    }
}

// === FUNÇÕES DE CATEGORIAS ===

async function loadCategoriasTable() {
    try {
        const response = await fetch('/api/categorias');
        const categoriasList = await response.json();
        
        const tbodyReceita = document.getElementById('tbody-categorias-receita');
        const tbodyDespesa = document.getElementById('tbody-categorias-despesa');
        
        if (!tbodyReceita || !tbodyDespesa) {
            console.error('Tabelas de categorias não encontradas');
            return;
        }
        
        // Limpar tabelas
        tbodyReceita.innerHTML = '';
        tbodyDespesa.innerHTML = '';
        
        // Separar categorias por tipo
        const receitas = categoriasList.filter(c => c.tipo === 'receita');
        const despesas = categoriasList.filter(c => c.tipo === 'despesa');
        
        // Preencher tabela de receitas
        if (receitas.length === 0) {
            tbodyReceita.innerHTML = '<tr><td colspan="2" class="empty-state">Nenhuma categoria de receita cadastrada</td></tr>';
        } else {
            receitas.forEach(cat => {
                const tr = document.createElement('tr');
                const numSubcats = cat.subcategorias && cat.subcategorias.length > 0 ? cat.subcategorias.length : 0;
                const subcatsBadge = numSubcats > 0 ? `<span class="subcategoria-badge">${numSubcats}</span>` : '';
                const nomeEscaped = cat.nome.replace(/'/g, "\\'");
                
                tr.innerHTML = `
                    <td>${cat.nome}</td>
                    <td>
                        ${subcatsBadge}
                        <button class="btn btn-info btn-small" data-categoria="${nomeEscaped}" title="Ver subcategorias">🔍</button>
                        <button class="btn btn-warning btn-small" onclick="editarCategoria('${nomeEscaped}', '${cat.tipo}')" title="Editar categoria">✏️</button>
                        <button class="btn btn-danger btn-small" onclick="excluirCategoria('${nomeEscaped}')" title="Excluir categoria">🗑️</button>
                    </td>
                `;
                
                // Adicionar evento de click ao botão de subcategorias
                const btnSubcat = tr.querySelector('.btn-info');
                if (btnSubcat) {
                    btnSubcat.addEventListener('click', () => {
                        verSubcategorias(cat.nome, cat.subcategorias || []);
                    });
                }
                
                tbodyReceita.appendChild(tr);
            });
        }
        
        // Preencher tabela de despesas
        if (despesas.length === 0) {
            tbodyDespesa.innerHTML = '<tr><td colspan="2" class="empty-state">Nenhuma categoria de despesa cadastrada</td></tr>';
        } else {
            despesas.forEach(cat => {
                const tr = document.createElement('tr');
                const numSubcats = cat.subcategorias && cat.subcategorias.length > 0 ? cat.subcategorias.length : 0;
                const subcatsBadge = numSubcats > 0 ? `<span class="subcategoria-badge">${numSubcats}</span>` : '';
                const nomeEscaped = cat.nome.replace(/'/g, "\\'");
                
                tr.innerHTML = `
                    <td>${cat.nome}</td>
                    <td>
                        ${subcatsBadge}
                        <button class="btn btn-info btn-small" data-categoria="${nomeEscaped}" title="Ver subcategorias">🔍</button>
                        <button class="btn btn-warning btn-small" onclick="editarCategoria('${nomeEscaped}', '${cat.tipo}')" title="Editar categoria">✏️</button>
                        <button class="btn btn-danger btn-small" onclick="excluirCategoria('${nomeEscaped}')" title="Excluir categoria">🗑️</button>
                    </td>
                `;
                
                // Adicionar evento de click ao botão de subcategorias
                const btnSubcat = tr.querySelector('.btn-info');
                if (btnSubcat) {
                    btnSubcat.addEventListener('click', () => {
                        verSubcategorias(cat.nome, cat.subcategorias || []);
                    });
                }
                
                tbodyDespesa.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar categorias:', error);
    }
}

async function editarCategoria(nome, tipo) {
    try {
        const response = await fetch('/api/categorias');
        const categorias = await response.json();
        const categoria = categorias.find(c => c.nome === nome);
        
        if (categoria && typeof openModalCategoria === 'function') {
            openModalCategoria(categoria);
        }
    } catch (error) {
        console.error('Erro ao carregar categoria para edição:', error);
        showToast('Erro ao carregar categoria', 'error');
    }
}

function verSubcategorias(nomeCategoria, subcategorias) {
    const modal = document.getElementById('modal-subcategorias');
    const titulo = document.getElementById('modal-subcategorias-titulo');
    const lista = document.getElementById('modal-subcategorias-lista');
    
    if (!modal || !titulo || !lista) {
        console.error('Elementos do modal de subcategorias não encontrados');
        return;
    }
    
    // Atualizar título
    titulo.textContent = `📋 Subcategorias de "${nomeCategoria}"`;
    
    // Limpar e preencher lista
    lista.innerHTML = '';
    
    if (subcategorias && subcategorias.length > 0) {
        subcategorias.forEach(sub => {
            const li = document.createElement('li');
            li.textContent = sub;
            lista.appendChild(li);
        });
    } else {
        lista.innerHTML = `
            <div class="subcategorias-empty">
                <div class="subcategorias-empty-icon">📭</div>
                <div class="subcategorias-empty-text">Nenhuma subcategoria cadastrada</div>
            </div>
        `;
    }
    
    // Mostrar modal
    modal.classList.add('active');
}

function fecharModalSubcategorias() {
    const modal = document.getElementById('modal-subcategorias');
    if (modal) {
        modal.classList.remove('active');
    }
}

async function excluirCategoria(nome) {
    if (!confirm(`Deseja realmente excluir a categoria "${nome}"?\n\nAtenção: Esta ação não pode ser desfeita!`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/categorias/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('✓ Categoria excluída com sucesso!', 'success');
            if (typeof loadCategoriasTable === 'function') loadCategoriasTable();
        } else {
            showToast('Erro: ' + (result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro ao excluir categoria:', error);
        showToast('Erro ao excluir categoria', 'error');
    }
}

// === FUNÇÕES DE CARREGAMENTO DAS NOVAS SEÇÕES ===

async function loadTiposSessao() {
    const tbody = document.getElementById('tbody-tipos-sessao');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/tipos-sessao');
        const tipos = await response.json();
        
        tbody.innerHTML = '';
        
        if (tipos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="empty-state">Nenhum tipo de sessão cadastrado</td></tr>';
            return;
        }
        
        tipos.forEach(tipo => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${tipo.nome}</td>
                <td>${tipo.ativa ? '<span style="color: #27ae60;">✓ Ativa</span>' : '<span style="color: #e74c3c;">✗ Inativa</span>'}</td>
                <td>
                    <button class="btn btn-warning btn-small" onclick='editarTipoSessao(${JSON.stringify(tipo)})'>✏️</button>
                    <button class="btn btn-danger btn-small" onclick="excluirTipoSessao(${tipo.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar tipos de sessão:', error);
        tbody.innerHTML = '<tr><td colspan="3" class="empty-state">Erro ao carregar dados</td></tr>';
    }
}

function editarTipoSessao(tipo) {
    openModalTipoSessao(tipo);
}

async function excluirTipoSessao(id) {
    if (!confirm('Deseja realmente excluir este tipo de sessão?')) return;
    
    try {
        const response = await fetch(`/api/tipos-sessao/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            alert('Tipo de sessão excluído com sucesso!');
            loadTiposSessao();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao excluir tipo:', error);
        alert('Erro ao excluir tipo de sessão');
    }
}

// FUNÇÃO DESATIVADA - Endpoint /api/contratos não existe mais
// async function loadContratos() {
//     const tbody = document.getElementById('tbody-contratos');
//     if (!tbody) return;
//     
//     try {
//         const response = await fetch('/api/contratos');
//         const contratos = await response.json();
//         
//         tbody.innerHTML = '';
//         
//         if (contratos.length === 0) {
//             tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhum contrato cadastrado</td></tr>';
//             return;
//         }
//         
//         contratos.forEach(contrato => {
//             const tr = document.createElement('tr');
//             const valorFormatado = parseFloat(contrato.valor_total || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2});
//             const dataFormatada = contrato.data_assinatura ? new Date(contrato.data_assinatura).toLocaleDateString('pt-BR') : '-';
//             
//             tr.innerHTML = `
//                 <td>${contrato.numero}</td>
//                 <td>${contrato.cliente_nome || '-'}</td>
//                 <td>R$ ${valorFormatado}</td>
//                 <td>${dataFormatada}</td>
//                 <td>${contrato.status}</td>
//                 <td>
//                     <button class="btn btn-warning btn-small" onclick='editarContrato(${JSON.stringify(contrato)})'>✏️</button>
//                     <button class="btn btn-danger btn-small" onclick="excluirContrato(${contrato.id})">🗑️</button>
//                 </td>
//             `;
//             tbody.appendChild(tr);
//         });
//     } catch (error) {
//         console.error('Erro ao carregar contratos:', error);
//         tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Erro ao carregar dados</td></tr>';
//     }
// }

function editarContrato(contrato) {
    openModalContrato(contrato);
}

async function excluirContrato(id) {
    if (!confirm('Deseja realmente excluir este contrato?')) return;
    
    try {
        const response = await fetch(`/api/contratos/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            alert('Contrato excluído com sucesso!');
            loadContratos();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao excluir contrato:', error);
        alert('Erro ao excluir contrato');
    }
}

async function loadSessoes() {
    const tbody = document.getElementById('tbody-sessoes');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/sessoes');
        const sessoes = await response.json();
        
        tbody.innerHTML = '';
        
        if (sessoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhuma sessão cadastrada</td></tr>';
            return;
        }
        
        sessoes.forEach(sessao => {
            const tr = document.createElement('tr');
            const dataPrevista = sessao.data_prevista ? new Date(sessao.data_prevista).toLocaleString('pt-BR') : '-';
            const dataRealizada = sessao.data_realizada ? new Date(sessao.data_realizada).toLocaleString('pt-BR') : '-';
            
            tr.innerHTML = `
                <td>${sessao.contrato_numero || '-'}</td>
                <td>${sessao.tipo_sessao_nome || '-'}</td>
                <td>${dataPrevista}</td>
                <td>${dataRealizada}</td>
                <td>${sessao.status}</td>
                <td>
                    <button class="btn btn-warning btn-small" onclick='editarSessao(${JSON.stringify(sessao)})'>✏️</button>
                    <button class="btn btn-danger btn-small" onclick="excluirSessao(${sessao.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar sessões:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Erro ao carregar dados</td></tr>';
    }
}

function editarSessao(sessao) {
    openModalSessao(sessao);
}

async function excluirSessao(id) {
    if (!confirm('Deseja realmente excluir esta sessão?')) return;
    
    try {
        const response = await fetch(`/api/sessoes/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            alert('Sessão excluída com sucesso!');
            loadSessoes();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao excluir sessão:', error);
        alert('Erro ao excluir sessão');
    }
}

async function loadAgenda() {
    const tbody = document.getElementById('tbody-agenda');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/agenda');
        const agendamentos = await response.json();
        
        tbody.innerHTML = '';
        
        if (agendamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhum agendamento cadastrado</td></tr>';
            return;
        }
        
        agendamentos.forEach(agenda => {
            const tr = document.createElement('tr');
            const dataHora = agenda.data_hora ? new Date(agenda.data_hora).toLocaleString('pt-BR') : '-';
            
            tr.innerHTML = `
                <td>${dataHora}</td>
                <td>${agenda.cliente_nome || '-'}</td>
                <td>${agenda.local || '-'}</td>
                <td>${agenda.tipo || '-'}</td>
                <td>${agenda.status}</td>
                <td>
                    <button class="btn btn-warning btn-small" onclick='editarAgenda(${JSON.stringify(agenda)})'>✏️</button>
                    <button class="btn btn-danger btn-small" onclick="excluirAgenda(${agenda.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar agenda:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Erro ao carregar dados</td></tr>';
    }
}

function editarAgenda(agenda) {
    openModalAgenda(agenda);
}

async function excluirAgenda(id) {
    if (!confirm('Deseja realmente excluir este agendamento?')) return;
    
    try {
        const response = await fetch(`/api/agenda/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            alert('Agendamento excluído com sucesso!');
            loadAgenda();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao excluir agendamento:', error);
        alert('Erro ao excluir agendamento');
    }
}

function visualizarCalendario() {
    alert('Visualização de calendário será implementada em breve!');
}

// FUNÇÃO DESATIVADA - Endpoint /api/estoque/produtos não existe mais
// async function loadProdutos() {
//     const tbody = document.getElementById('tbody-produtos');
//     if (!tbody) return;
//     
//     try {
//         const response = await fetch('/api/estoque/produtos');
//         const produtos = await response.json();
//         
//         // Armazenar produtos para uso em movimentações
//         window.produtosEstoque = produtos;
//         
//         // Atualizar select de produtos no modal de movimentação
//         const selectProduto = document.getElementById('movimentacao-produto-id');
//         if (selectProduto) {
//             selectProduto.innerHTML = '<option value="">Selecione o produto</option>';
//             produtos.forEach(prod => {
//                 const option = document.createElement('option');
//                 option.value = prod.id;
//                 option.textContent = prod.nome;
//                 selectProduto.appendChild(option);
//             });
//         }
//         
//         tbody.innerHTML = '';
//         
//         if (produtos.length === 0) {
//             tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhum produto cadastrado</td></tr>';
//             return;
//         }
//         
//         produtos.forEach(prod => {
//             const tr = document.createElement('tr');
//             const valorFormatado = parseFloat(prod.valor_unitario || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2});
//             
//             tr.innerHTML = `
//                 <td>${prod.nome}</td>
//                 <td>${prod.codigo || '-'}</td>
//                 <td>${prod.quantidade}</td>
//                 <td>${prod.unidade}</td>
//                 <td>R$ ${valorFormatado}</td>
//                 <td>
//                     <button class="btn btn-warning btn-small" onclick='editarProduto(${JSON.stringify(prod)})'>✏️</button>
//                     <button class="btn btn-danger btn-small" onclick="excluirProduto(${prod.id})">🗑️</button>
//                 </td>
//             `;
//             tbody.appendChild(tr);
//         });
//     } catch (error) {
//         console.error('Erro ao carregar produtos:', error);
//         tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Erro ao carregar dados</td></tr>';
//     }
// }

function editarProduto(produto) {
    openModalProduto(produto);
}

async function excluirProduto(id) {
    if (!confirm('Deseja realmente excluir este produto?')) return;
    
    try {
        const response = await fetch(`/api/estoque/produtos/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            alert('Produto excluído com sucesso!');
            loadProdutos();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao excluir produto:', error);
        alert('Erro ao excluir produto');
    }
}

async function loadMovimentacoes() {
    const tbody = document.getElementById('tbody-movimentacoes');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/estoque/movimentacoes');
        const movimentacoes = await response.json();
        
        tbody.innerHTML = '';
        
        if (movimentacoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhuma movimentação cadastrada</td></tr>';
            return;
        }
        
        movimentacoes.forEach(mov => {
            const tr = document.createElement('tr');
            const dataFormatada = mov.data ? new Date(mov.data).toLocaleDateString('pt-BR') : '-';
            const tipoColor = mov.tipo === 'entrada' ? '#27ae60' : '#e74c3c';
            
            tr.innerHTML = `
                <td>${dataFormatada}</td>
                <td>${mov.produto_nome || '-'}</td>
                <td><span style="color: ${tipoColor};">${mov.tipo}</span></td>
                <td>${mov.quantidade}</td>
                <td>${mov.observacoes || '-'}</td>
                <td>
                    <button class="btn btn-danger btn-small" onclick="excluirMovimentacao(${mov.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar movimentações:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Erro ao carregar dados</td></tr>';
    }
}

async function excluirMovimentacao(id) {
    if (!confirm('Deseja realmente excluir esta movimentação?')) return;
    
    try {
        const response = await fetch(`/api/estoque/movimentacoes/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            alert('Movimentação excluída com sucesso!');
            loadMovimentacoes();
            loadProdutos(); // Atualizar estoque
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao excluir movimentação:', error);
        alert('Erro ao excluir movimentação');
    }
}

function exportarEstoquePDF() {
    alert('Exportação PDF será implementada em breve!');
}

async function loadKits() {
    const tbody = document.getElementById('tbody-kits');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/kits');
        const kits = await response.json();
        
        tbody.innerHTML = '';
        
        if (kits.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Nenhum kit cadastrado</td></tr>';
            return;
        }
        
        kits.forEach(kit => {
            const tr = document.createElement('tr');
            const valorFormatado = parseFloat(kit.valor_total || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2});
            const numItens = kit.itens ? kit.itens.length : 0;
            
            tr.innerHTML = `
                <td>${kit.nome}</td>
                <td>${kit.descricao || '-'}</td>
                <td>${numItens} ${numItens === 1 ? 'item' : 'itens'}</td>
                <td>R$ ${valorFormatado}</td>
                <td>
                    <button class="btn btn-warning btn-small" onclick='editarKit(${JSON.stringify(kit)})'>✏️</button>
                    <button class="btn btn-danger btn-small" onclick="excluirKit(${kit.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar kits:', error);
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Erro ao carregar dados</td></tr>';
    }
}

function editarKit(kit) {
    openModalKit(kit);
}

async function excluirKit(id) {
    if (!confirm('Deseja realmente excluir este kit?')) return;
    
    try {
        const response = await fetch(`/api/kits/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            alert('Kit excluído com sucesso!');
            loadKits();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao excluir kit:', error);
        alert('Erro ao excluir kit');
    }
}

// === CARREGAMENTO - COMISSÕES ===

async function loadComissoes() {
    const tbody = document.getElementById('tbody-comissoes');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/comissoes');
        const comissoes = await response.json();
        
        tbody.innerHTML = '';
        
        if (comissoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhuma comissão cadastrada</td></tr>';
            return;
        }
        
        comissoes.forEach(comissao => {
            const tr = document.createElement('tr');
            const valorFormatado = parseFloat(comissao.valor || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2});
            
            tr.innerHTML = `
                <td>${comissao.contrato_numero || '-'}</td>
                <td>${comissao.pessoa}</td>
                <td>${comissao.tipo}</td>
                <td>R$ ${valorFormatado}</td>
                <td>${comissao.percentual || 0}%</td>
                <td>
                    <button class="btn btn-warning btn-small" onclick='editarComissao(${JSON.stringify(comissao)})'>✏️</button>
                    <button class="btn btn-danger btn-small" onclick="excluirComissao(${comissao.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar comissões:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Erro ao carregar dados</td></tr>';
    }
}

function editarComissao(comissao) {
    openModalComissao(comissao);
}

async function excluirComissao(id) {
    if (!confirm('Deseja realmente excluir esta comissão?')) return;
    
    try {
        const response = await fetch(`/api/comissoes/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            alert('Comissão excluída com sucesso!');
            loadComissoes();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao excluir comissão:', error);
        alert('Erro ao excluir comissão');
    }
}

// === CARREGAMENTO - SESSÃO EQUIPE ===

async function loadSessaoEquipe() {
    const tbody = document.getElementById('tbody-sessao-equipe');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/sessao-equipe');
        const membros = await response.json();
        
        tbody.innerHTML = '';
        
        if (membros.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Nenhum membro cadastrado</td></tr>';
            return;
        }
        
        membros.forEach(membro => {
            const tr = document.createElement('tr');
            
            tr.innerHTML = `
                <td>${membro.sessao_info || '-'}</td>
                <td>${membro.membro}</td>
                <td>${membro.funcao || '-'}</td>
                <td>${membro.observacoes || '-'}</td>
                <td>
                    <button class="btn btn-warning btn-small" onclick='editarSessaoEquipe(${JSON.stringify(membro)})'>✏️</button>
                    <button class="btn btn-danger btn-small" onclick="excluirSessaoEquipe(${membro.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar equipe:', error);
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Erro ao carregar dados</td></tr>';
    }
}

function editarSessaoEquipe(membro) {
    openModalSessaoEquipe(membro);
}

async function excluirSessaoEquipe(id) {
    if (!confirm('Deseja realmente remover este membro?')) return;
    
    try {
        const response = await fetch(`/api/sessao-equipe/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            alert('Membro removido com sucesso!');
            loadSessaoEquipe();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao remover membro:', error);
        alert('Erro ao remover membro');
    }
}

// === CARREGAMENTO - TAGS ===

async function loadTags() {
    const tbody = document.getElementById('tbody-tags');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/tags');
        const tags = await response.json();
        
        tbody.innerHTML = '';
        
        if (tags.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="empty-state">Nenhuma tag cadastrada</td></tr>';
            return;
        }
        
        tags.forEach(tag => {
            const tr = document.createElement('tr');
            
            tr.innerHTML = `
                <td>${tag.nome}</td>
                <td><span style="display: inline-block; width: 30px; height: 20px; background: ${tag.cor}; border-radius: 3px;"></span> ${tag.cor}</td>
                <td>
                    <button class="btn btn-warning btn-small" onclick='editarTag(${JSON.stringify(tag)})'>✏️</button>
                    <button class="btn btn-danger btn-small" onclick="excluirTag(${tag.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar tags:', error);
        tbody.innerHTML = '<tr><td colspan="3" class="empty-state">Erro ao carregar dados</td></tr>';
    }
}

function editarTag(tag) {
    openModalTag(tag);
}

async function excluirTag(id) {
    if (!confirm('Deseja realmente excluir esta tag?')) return;
    
    try {
        const response = await fetch(`/api/tags/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            alert('Tag excluída com sucesso!');
            loadTags();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao excluir tag:', error);
        alert('Erro ao excluir tag');
    }
}

// === CARREGAMENTO - TEMPLATES ===

async function loadTemplates() {
    const tbody = document.getElementById('tbody-templates');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/templates-equipe');
        const templates = await response.json();
        
        tbody.innerHTML = '';
        
        if (templates.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-state">Nenhum template cadastrado</td></tr>';
            return;
        }
        
        templates.forEach(template => {
            const tr = document.createElement('tr');
            const numMembros = template.membros ? template.membros.length : 0;
            
            tr.innerHTML = `
                <td>${template.nome}</td>
                <td>${template.descricao || '-'}</td>
                <td>${numMembros} ${numMembros === 1 ? 'membro' : 'membros'}</td>
                <td>
                    <button class="btn btn-warning btn-small" onclick='editarTemplate(${JSON.stringify(template)})'>✏️</button>
                    <button class="btn btn-danger btn-small" onclick="excluirTemplate(${template.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar templates:', error);
        tbody.innerHTML = '<tr><td colspan="4" class="empty-state">Erro ao carregar dados</td></tr>';
    }
}

function editarTemplate(template) {
    openModalTemplate(template);
}

async function excluirTemplate(id) {
    if (!confirm('Deseja realmente excluir este template?')) return;
    
    try {
        const response = await fetch(`/api/templates-equipe/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            alert('Template excluído com sucesso!');
            loadTemplates();
        } else {
            alert('Erro: ' + (result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao excluir template:', error);
        alert('Erro ao excluir template');
    }
}

function exportarContratosPDF() {
    alert('Exportação PDF de contratos será implementada em breve!');
}

// Tornar funções globais
window.showClienteTab = showClienteTab;
window.showFornecedorTab = showFornecedorTab;
window.loadCategorias = loadCategorias;
window.loadClientes = loadClientes;
window.loadFornecedores = loadFornecedores;
window.loadClientesTable = loadClientesTable;
window.loadFornecedoresTable = loadFornecedoresTable;
window.openModalInativarCliente = openModalInativarCliente;
window.closeModalInativarCliente = closeModalInativarCliente;
window.confirmarInativarCliente = confirmarInativarCliente;
window.reativarCliente = reativarCliente;
window.excluirCliente = excluirCliente;
window.openModalInativarFornecedor = openModalInativarFornecedor;
window.closeModalInativarFornecedor = closeModalInativarFornecedor;
window.confirmarInativarFornecedor = confirmarInativarFornecedor;
window.reativarFornecedor = reativarFornecedor;
window.excluirFornecedor = excluirFornecedor;
window.verMotivoInativacao = verMotivoInativacao;
window.closeModalMotivoInativacao = closeModalMotivoInativacao;

// Novas funcionalidades operacionais
window.showContratoTab = showContratoTab;
window.showEstoqueTab = showEstoqueTab;

// Tipos de Sessão
window.openModalTipoSessao = openModalTipoSessao;
window.closeModalTipoSessao = closeModalTipoSessao;
window.salvarTipoSessao = salvarTipoSessao;

// Contratos
window.openModalContrato = openModalContrato;
window.closeModalContrato = closeModalContrato;
window.salvarContrato = salvarContrato;

// Sessões
window.openModalSessao = openModalSessao;
window.closeModalSessao = closeModalSessao;
window.salvarSessao = salvarSessao;

// Agenda
window.openModalAgenda = openModalAgenda;
window.closeModalAgenda = closeModalAgenda;
window.salvarAgenda = salvarAgenda;

// Estoque - Produtos
window.openModalProduto = openModalProduto;
window.closeModalProduto = closeModalProduto;
window.salvarProduto = salvarProduto;

// Estoque - Movimentações
window.openModalMovimentacao = openModalMovimentacao;
window.closeModalMovimentacao = closeModalMovimentacao;
window.salvarMovimentacao = salvarMovimentacao;

// Kits
window.openModalKit = openModalKit;
window.closeModalKit = closeModalKit;
window.salvarKit = salvarKit;

// Comissões
window.openModalComissao = openModalComissao;
window.closeModalComissao = closeModalComissao;
window.salvarComissao = salvarComissao;

// Sessão Equipe
window.openModalSessaoEquipe = openModalSessaoEquipe;
window.closeModalSessaoEquipe = closeModalSessaoEquipe;
window.salvarSessaoEquipe = salvarSessaoEquipe;

// Tags
window.openModalTag = openModalTag;
window.closeModalTag = closeModalTag;
window.salvarTag = salvarTag;

// Templates
window.openModalTemplate = openModalTemplate;
window.closeModalTemplate = closeModalTemplate;
window.salvarTemplate = salvarTemplate;

// Funções de carregamento
window.loadTiposSessao = loadTiposSessao;
window.loadContratos = loadContratos;
window.loadSessoes = loadSessoes;
window.loadComissoes = loadComissoes;
window.loadSessaoEquipe = loadSessaoEquipe;
window.loadAgenda = loadAgenda;
window.loadProdutos = loadProdutos;
window.loadMovimentacoes = loadMovimentacoes;
window.loadKits = loadKits;
window.loadTags = loadTags;
window.loadTemplates = loadTemplates;

// Funções de exportação
window.exportarContratosPDF = exportarContratosPDF;
window.exportarEstoquePDF = exportarEstoquePDF;
window.visualizarCalendario = visualizarCalendario;

// Debug: Verificar se funções foram exportadas corretamente
console.log('%c 🔍 DEBUG - Funções Operacionais Exportadas: ', 'background: #2196F3; color: white; font-weight: bold');
console.log('  ✓ showContratoTab:', typeof window.showContratoTab);
console.log('  ✓ showEstoqueTab:', typeof window.showEstoqueTab);
console.log('  ✓ openModalContrato:', typeof window.openModalContrato);
console.log('  ✓ exportarContratosPDF:', typeof window.exportarContratosPDF);
console.log('  ✓ openModalAgenda:', typeof window.openModalAgenda);
console.log('  ✓ visualizarCalendario:', typeof window.visualizarCalendario);
console.log('  ✓ openModalProduto:', typeof window.openModalProduto);
console.log('  ✓ exportarEstoquePDF:', typeof window.exportarEstoquePDF);
console.log('  ✓ openModalKit:', typeof window.openModalKit);
console.log('  ✓ openModalTag:', typeof window.openModalTag);
console.log('  ✓ openModalTemplate:', typeof window.openModalTemplate);

// === FUNÇÕES DE CONTAS A RECEBER/PAGAR ===

// Função auxiliar para formatar data no padrão brasileiro
function formatarDataBR(dataISO) {
    if (!dataISO || dataISO === '-') return '-';
    
    try {
        // Extrair YYYY-MM-DD sem considerar fuso horário
        const partes = dataISO.split('T')[0].split('-');
        if (partes.length === 3) {
            const ano = partes[0];
            const mes = partes[1];
            const dia = partes[2];
            return `${dia}/${mes}/${ano}`;
        }
        
        // Fallback para método antigo
        const data = new Date(dataISO + 'T00:00:00');
        const d = String(data.getDate()).padStart(2, '0');
        const m = String(data.getMonth() + 1).padStart(2, '0');
        const a = data.getFullYear();
        return `${d}/${m}/${a}`;
    } catch (e) {
        return dataISO;
    }
}

// Função para carregar saldos dos bancos
async function carregarSaldosBancos(tipo) {
    try {
        const response = await fetch('/api/contas');
        const contas = await response.json();
        
        // Calcular saldo total
        const saldoTotal = contas.reduce((total, conta) => {
            return total + parseFloat(conta.saldo || conta.saldo_atual || 0);
        }, 0);
        
        // Atualizar saldo total
        const saldoTotalEl = document.getElementById(`saldo-total-bancos-${tipo}`);
        if (saldoTotalEl) {
            saldoTotalEl.textContent = `R$ ${saldoTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        }
        
        // Popular select de bancos
        const selectBanco = document.getElementById(`select-banco-${tipo}`);
        if (selectBanco) {
            const valorAtual = selectBanco.value;
            selectBanco.innerHTML = '<option value="">Selecione um banco</option>';
            
            contas.forEach(conta => {
                const option = document.createElement('option');
                option.value = conta.id;
                option.textContent = `${conta.banco} - ${conta.conta}`;
                option.dataset.saldo = conta.saldo || conta.saldo_atual || 0;
                selectBanco.appendChild(option);
            });
            
            if (valorAtual) {
                selectBanco.value = valorAtual;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar saldos dos bancos:', error);
    }
}

// Função para atualizar saldo do banco selecionado
function atualizarSaldoBanco(tipo) {
    const selectBanco = document.getElementById(`select-banco-${tipo}`);
    const saldoBancoEl = document.getElementById(`saldo-banco-selecionado-${tipo}`);
    
    if (!selectBanco || !saldoBancoEl) return;
    
    const selectedOption = selectBanco.options[selectBanco.selectedIndex];
    
    if (selectBanco.value && selectedOption.dataset.saldo) {
        const saldo = parseFloat(selectedOption.dataset.saldo);
        saldoBancoEl.textContent = `R$ ${saldo.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        saldoBancoEl.style.display = 'block';
    } else {
        saldoBancoEl.style.display = 'none';
    }
}

async function loadContasReceber() {
    try {
        const response = await fetch('/api/lancamentos?tipo=RECEITA');
        const lancamentos = await response.json();
        
        const tbody = document.querySelector('#contas-receber-section tbody');
        if (!tbody) {
            console.error('Tabela de contas a receber não encontrada');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (lancamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="empty-state">Nenhuma conta a receber cadastrada</td></tr>';
            return;
        }
        
        // Aplicar filtros se necessário
        let lancamentosFiltrados = lancamentos;
        
        // Filtro de status
        const filterStatus = document.getElementById('filter-status-receber');
        if (filterStatus && filterStatus.value) {
            lancamentosFiltrados = lancamentosFiltrados.filter(l => 
                (l.status || '').toUpperCase() === filterStatus.value.toUpperCase()
            );
        }
        
        // Filtro de categoria
        const filterCategoria = document.getElementById('filter-categoria-receber');
        if (filterCategoria && filterCategoria.value) {
            lancamentosFiltrados = lancamentosFiltrados.filter(l => l.categoria === filterCategoria.value);
        }
        
        // Filtro de cliente
        const filterCliente = document.getElementById('filter-cliente');
        if (filterCliente && filterCliente.value) {
            lancamentosFiltrados = lancamentosFiltrados.filter(l => l.pessoa === filterCliente.value);
        }
        
        if (lancamentosFiltrados.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="empty-state">Nenhuma conta encontrada com os filtros aplicados</td></tr>';
            return;
        }
        
        // Ordenar por data de vencimento (crescente - mais antigas primeiro)
        lancamentosFiltrados.sort((a, b) => {
            const dataA = new Date(a.data_vencimento);
            const dataB = new Date(b.data_vencimento);
            return dataA - dataB;
        });
        
        lancamentosFiltrados.forEach(lanc => {
            const tr = document.createElement('tr');
            const valor = parseFloat(lanc.valor || 0);
            const dataVencimento = formatarDataBR(lanc.data_vencimento);
            let status = (lanc.status || 'PENDENTE').toUpperCase();
            
            // Verificar se está vencido
            if (status === 'PENDENTE' && lanc.data_vencimento) {
                const hoje = new Date();
                hoje.setHours(0, 0, 0, 0);
                const vencimento = new Date(lanc.data_vencimento + 'T00:00:00');
                if (vencimento < hoje) {
                    status = 'VENCIDO';
                }
            }
            
            let statusClass = '';
            let statusText = status;
            if (status === 'PAGO') {
                statusClass = 'status-pago';
                statusText = '✓ Pago';
            } else if (status === 'VENCIDO') {
                statusClass = 'status-vencido';
                statusText = '⚠️ Vencido';
            } else if (status === 'PENDENTE') {
                statusClass = 'status-pendente';
                statusText = '⏳ Pendente';
            } else if (status === 'CANCELADO') {
                statusClass = 'status-cancelado';
                statusText = '✖ Cancelado';
            }
            
            const btnLiquidar = (status === 'PENDENTE' || status === 'VENCIDO')
                ? `<button class="btn btn-success btn-small" onclick="liquidarLancamento(${lanc.id}, 'RECEITA')" title="Liquidar">💰</button>` 
                : '';
            
            tr.innerHTML = `
                <td><input type="checkbox" class="checkbox-lancamento" data-id="${lanc.id || ''}" data-valor="${valor}" onchange="atualizarSomaSelecionados('receber')"></td>
                <td>${dataVencimento}</td>
                <td>${lanc.pessoa || '-'}</td>
                <td>${lanc.num_documento || '-'}</td>
                <td>${lanc.descricao || '-'}</td>
                <td>${lanc.categoria || '-'}</td>
                <td>${lanc.subcategoria || '-'}</td>
                <td>R$ ${valor.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                <td><span class="${statusClass}">${statusText}</span></td>
                <td>
                    ${btnLiquidar}
                    <button class="btn btn-warning btn-small" onclick="editarLancamento(${lanc.id}, 'RECEITA')" title="Editar">✏️</button>
                    <button class="btn btn-danger btn-small" onclick="excluirLancamento(${lanc.id}, 'RECEITA')" title="Excluir">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        // Adicionar listeners aos checkboxes
        adicionarListenersCheckbox('receber');
        
        // Carregar saldos dos bancos
        await carregarSaldosBancos('receber');
    } catch (error) {
        console.error('Erro ao carregar contas a receber:', error);
        showToast('Erro ao carregar contas a receber', 'error');
    }
}

async function loadContasPagar() {
    try {
        const response = await fetch('/api/lancamentos?tipo=DESPESA');
        const lancamentos = await response.json();
        
        const tbody = document.querySelector('#contas-pagar-section tbody');
        if (!tbody) {
            console.error('Tabela de contas a pagar não encontrada');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (lancamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="empty-state">Nenhuma conta a pagar cadastrada</td></tr>';
            return;
        }
        
        // Aplicar filtros se necessário
        let lancamentosFiltrados = lancamentos;
        
        // Filtro de status
        const filterStatus = document.getElementById('filter-status-pagar');
        if (filterStatus && filterStatus.value) {
            lancamentosFiltrados = lancamentosFiltrados.filter(l => 
                (l.status || '').toUpperCase() === filterStatus.value.toUpperCase()
            );
        }
        
        // Filtro de categoria
        const filterCategoria = document.getElementById('filter-categoria-pagar');
        if (filterCategoria && filterCategoria.value) {
            lancamentosFiltrados = lancamentosFiltrados.filter(l => l.categoria === filterCategoria.value);
        }
        
        // Filtro de fornecedor
        const filterFornecedor = document.getElementById('filter-fornecedor');
        if (filterFornecedor && filterFornecedor.value) {
            lancamentosFiltrados = lancamentosFiltrados.filter(l => l.pessoa === filterFornecedor.value);
        }
        
        if (lancamentosFiltrados.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="empty-state">Nenhuma conta encontrada com os filtros aplicados</td></tr>';
            return;
        }
        
        // Ordenar por data de vencimento (crescente - mais antigas primeiro)
        lancamentosFiltrados.sort((a, b) => {
            const dataA = new Date(a.data_vencimento);
            const dataB = new Date(b.data_vencimento);
            return dataA - dataB;
        });
        
        lancamentosFiltrados.forEach(lanc => {
            const tr = document.createElement('tr');
            const valor = parseFloat(lanc.valor || 0);
            const dataVencimento = formatarDataBR(lanc.data_vencimento);
            let status = (lanc.status || 'PENDENTE').toUpperCase();
            
            // Verificar se está vencido
            if (status === 'PENDENTE' && lanc.data_vencimento) {
                const hoje = new Date();
                hoje.setHours(0, 0, 0, 0);
                const vencimento = new Date(lanc.data_vencimento + 'T00:00:00');
                if (vencimento < hoje) {
                    status = 'VENCIDO';
                }
            }
            
            let statusClass = '';
            let statusText = status;
            if (status === 'PAGO') {
                statusClass = 'status-pago';
                statusText = '✓ Pago';
            } else if (status === 'VENCIDO') {
                statusClass = 'status-vencido';
                statusText = '⚠️ Vencido';
            } else if (status === 'PENDENTE') {
                statusClass = 'status-pendente';
                statusText = '⏳ Pendente';
            } else if (status === 'CANCELADO') {
                statusClass = 'status-cancelado';
                statusText = '✖ Cancelado';
            }
            
            const btnLiquidar = (status === 'PENDENTE' || status === 'VENCIDO')
                ? `<button class="btn btn-success btn-small" onclick="liquidarLancamento(${lanc.id}, 'DESPESA')" title="Liquidar">💰</button>` 
                : '';
            
            tr.innerHTML = `
                <td><input type="checkbox" class="checkbox-lancamento" data-id="${lanc.id || ''}" data-valor="${valor}" onchange="atualizarSomaSelecionados('pagar')"></td>
                <td>${dataVencimento}</td>
                <td>${lanc.pessoa || '-'}</td>
                <td>${lanc.num_documento || '-'}</td>
                <td>${lanc.descricao || '-'}</td>
                <td>${lanc.categoria || '-'}</td>
                <td>${lanc.subcategoria || '-'}</td>
                <td>R$ ${valor.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                <td><span class="${statusClass}">${statusText}</span></td>
                <td>
                    ${btnLiquidar}
                    <button class="btn btn-warning btn-small" onclick="editarLancamento(${lanc.id}, 'DESPESA')" title="Editar">✏️</button>
                    <button class="btn btn-danger btn-small" onclick="excluirLancamento(${lanc.id}, 'DESPESA')" title="Excluir">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        // Adicionar listeners aos checkboxes
        adicionarListenersCheckbox('pagar');
        
        // Carregar saldos dos bancos
        await carregarSaldosBancos('pagar');
    } catch (error) {
        console.error('Erro ao carregar contas a pagar:', error);
        showToast('Erro ao carregar contas a pagar', 'error');
    }
}

// === FUNÇÕES DE GERENCIAMENTO DE LANÇAMENTOS ===

// Variáveis globais para liquidação
let lancamentoParaLiquidar = null;
let tipoLancamentoParaLiquidar = null;
let tipoLiquidacaoEmMassa = null;

async function liquidarLancamento(id, tipo) {
    // Armazenar dados do lançamento
    lancamentoParaLiquidar = id;
    tipoLancamentoParaLiquidar = tipo;
    
    // Carregar contas bancárias
    try {
        const response = await fetch('/api/contas');
        const contas = await response.json();
        
        const opcoesContas = contas.map(c => 
            `<option value="${c.nome}">${c.banco} - ${c.agencia}/${c.conta}</option>`
        ).join('');
        
        // Criar modal de liquidação
        const modal = createModal('💰 Liquidar Lançamento', `
            <form id="form-liquidacao" onsubmit="confirmarLiquidacao(event)">
                <div class="form-group">
                    <label>*Data de Liquidação:</label>
                    <input type="date" id="liquidacao-data" value="${new Date().toISOString().split('T')[0]}" required>
                </div>
                
                <div class="form-group">
                    <label>*Conta Bancária:</label>
                    <select id="liquidacao-conta" required>
                        <option value="">Selecione a conta...</option>
                        ${opcoesContas}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Juros (R$):</label>
                    <input type="number" id="liquidacao-juros" step="0.01" min="0" value="0" placeholder="0,00">
                </div>
                
                <div class="form-group">
                    <label>Desconto (R$):</label>
                    <input type="number" id="liquidacao-desconto" step="0.01" min="0" value="0" placeholder="0,00">
                </div>
                
                <div class="form-group">
                    <label>Observações:</label>
                    <textarea id="liquidacao-observacoes" rows="3" placeholder="Opcional"></textarea>
                </div>
                
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                    <button type="button" onclick="closeModal()" style="padding: 10px 20px; background: #95a5a6; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">Cancelar</button>
                    <button type="submit" style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold;">💰 Liquidar</button>
                </div>
            </form>
        `);
        
        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('active'), 10);
        
    } catch (error) {
        console.error('Erro ao abrir modal de liquidação:', error);
        showToast('Erro ao carregar contas bancárias', 'error');
    }
}

async function confirmarLiquidacao(event) {
    event.preventDefault();
    
    const data = document.getElementById('liquidacao-data')?.value;
    const conta = document.getElementById('liquidacao-conta')?.value;
    const juros = parseFloat(document.getElementById('liquidacao-juros')?.value) || 0;
    const desconto = parseFloat(document.getElementById('liquidacao-desconto')?.value) || 0;
    const observacoes = document.getElementById('liquidacao-observacoes')?.value || '';
    
    // Validação
    if (!data) {
        showToast('❌ Data de pagamento é obrigatória', 'error');
        return;
    }
    
    if (!conta) {
        showToast('❌ Conta bancária é obrigatória', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/lancamentos/${lancamentoParaLiquidar}/liquidar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                data_pagamento: data,
                conta_bancaria: conta,
                juros: juros,
                desconto: desconto,
                observacoes: observacoes
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('✓ Lançamento liquidado com sucesso!', 'success');
            closeModal();
            
            if (tipoLancamentoParaLiquidar === 'RECEITA') {
                loadContasReceber();
            } else {
                loadContasPagar();
            }
            if (typeof loadDashboard === 'function') loadDashboard();
        } else {
            showToast('Erro: ' + (result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro ao liquidar lançamento:', error);
        showToast('Erro ao liquidar lançamento', 'error');
    }
}

async function editarLancamento(id, tipo) {
    try {
        const response = await fetch(`/api/lancamentos/${id}`);
        const lancamento = await response.json();
        
        if (!lancamento || lancamento.error) {
            showToast('Lançamento não encontrado', 'error');
            return;
        }
        
        // Editando lançamento
        
        // Abrir modal apropriado e aguardar carregamento
        if (tipo === 'RECEITA') {
            if (typeof openModalReceita === 'function') {
                await openModalReceita();
                
                // Aguardar um momento para o modal ser renderizado
                await new Promise(resolve => setTimeout(resolve, 300));
                
                // Preencher campos
                const idField = document.getElementById('receita-id');
                const descricao = document.getElementById('receita-descricao');
                const valor = document.getElementById('receita-valor');
                const vencimento = document.getElementById('receita-vencimento');
                const categoria = document.getElementById('receita-categoria');
                const cliente = document.getElementById('receita-cliente');
                const observacoes = document.getElementById('receita-observacoes');
                const numDocumento = document.getElementById('receita-documento');
                
                if (idField) idField.value = id; // PREENCHER O ID PARA EDIÇÃO
                if (descricao) descricao.value = lancamento.descricao || '';
                if (valor) valor.value = lancamento.valor || '';
                if (vencimento) vencimento.value = lancamento.data_vencimento ? lancamento.data_vencimento.split('T')[0] : '';
                if (categoria) {
                    categoria.value = lancamento.categoria || '';
                    // Disparar evento change para carregar subcategorias
                    if (typeof atualizarSubcategoriasReceita === 'function') {
                        atualizarSubcategoriasReceita();
                        // Aguardar subcategorias carregarem e selecionar
                        await new Promise(resolve => setTimeout(resolve, 100));
                        const subcategoria = document.getElementById('receita-subcategoria');
                        if (subcategoria && lancamento.subcategoria) {
                            subcategoria.value = lancamento.subcategoria;
                        }
                    }
                }
                if (cliente) cliente.value = lancamento.pessoa || '';
                if (observacoes) observacoes.value = lancamento.observacoes || '';
                if (numDocumento) numDocumento.value = lancamento.num_documento || '';
                
                // Mudar título do modal
                const modalTitle = document.querySelector('#dynamic-modal h2');
                if (modalTitle) modalTitle.textContent = '✏️ Editar Receita';
            }
        } else {
            if (typeof openModalDespesa === 'function') {
                await openModalDespesa();
                
                // Aguardar um momento para o modal ser renderizado
                await new Promise(resolve => setTimeout(resolve, 300));
                
                // Preencher campos
                const idField = document.getElementById('despesa-id');
                const descricao = document.getElementById('despesa-descricao');
                const valor = document.getElementById('despesa-valor');
                const vencimento = document.getElementById('despesa-vencimento');
                const categoria = document.getElementById('despesa-categoria');
                const fornecedor = document.getElementById('despesa-fornecedor');
                const observacoes = document.getElementById('despesa-observacoes');
                const numDocumento = document.getElementById('despesa-documento');
                
                if (idField) idField.value = id; // PREENCHER O ID PARA EDIÇÃO
                if (descricao) descricao.value = lancamento.descricao || '';
                if (valor) valor.value = lancamento.valor || '';
                if (vencimento) vencimento.value = lancamento.data_vencimento ? lancamento.data_vencimento.split('T')[0] : '';
                if (categoria) {
                    categoria.value = lancamento.categoria || '';
                    // Disparar evento change para carregar subcategorias
                    if (typeof atualizarSubcategoriasDespesa === 'function') {
                        atualizarSubcategoriasDespesa();
                        // Aguardar subcategorias carregarem e selecionar
                        await new Promise(resolve => setTimeout(resolve, 100));
                        const subcategoria = document.getElementById('despesa-subcategoria');
                        if (subcategoria && lancamento.subcategoria) {
                            subcategoria.value = lancamento.subcategoria;
                        }
                    }
                }
                if (fornecedor) fornecedor.value = lancamento.pessoa || '';
                if (observacoes) observacoes.value = lancamento.observacoes || '';
                if (numDocumento) numDocumento.value = lancamento.num_documento || '';
                
                // Mudar título do modal
                const modalTitle = document.querySelector('#dynamic-modal h2');
                if (modalTitle) modalTitle.textContent = '✏️ Editar Despesa';
            }
        }
        
    } catch (error) {
        console.error('Erro ao editar lançamento:', error);
        showToast('Erro ao carregar lançamento', 'error');
    }
}

async function excluirLancamento(id, tipo) {
    if (!confirm('Deseja realmente excluir este lançamento?\n\nAtenção: Esta ação não pode ser desfeita!')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/lancamentos/${id}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('✓ Lançamento excluído com sucesso!', 'success');
            if (tipo === 'RECEITA') {
                loadContasReceber();
            } else {
                loadContasPagar();
            }
            if (typeof loadDashboard === 'function') loadDashboard();
        } else {
            showToast('Erro: ' + (result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro ao excluir lançamento:', error);
        showToast('Erro ao excluir lançamento', 'error');
    }
}

// Função para adicionar listeners aos checkboxes
function adicionarListenersCheckbox(tipo) {
    const checkboxes = document.querySelectorAll(`#contas-${tipo}-section .checkbox-lancamento`);
    const checkboxAll = document.getElementById(`select-all-${tipo}`);
    
    checkboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            atualizarVisibilidadeBotoesEmMassa(tipo);
        });
    });
    
    if (checkboxAll) {
        checkboxAll.addEventListener('change', () => {
            toggleSelectAll(tipo);
        });
    }
    
    // Atualizar visibilidade inicial
    atualizarVisibilidadeBotoesEmMassa(tipo);
}

// Função para atualizar visibilidade dos botões de ação em massa
function atualizarVisibilidadeBotoesEmMassa(tipo) {
    const checkboxes = document.querySelectorAll(`#contas-${tipo}-section .checkbox-lancamento:checked`);
    const btnLiquidar = document.getElementById(`btn-liquidar-massa-${tipo}`);
    const btnExcluir = document.getElementById(`btn-excluir-massa-${tipo}`);
    
    if (checkboxes.length > 0) {
        if (btnLiquidar) btnLiquidar.style.display = 'inline-block';
        if (btnExcluir) btnExcluir.style.display = 'inline-block';
    } else {
        if (btnLiquidar) btnLiquidar.style.display = 'none';
        if (btnExcluir) btnExcluir.style.display = 'none';
    }
}

// Função para seleção em massa
function toggleSelectAll(tipo) {
    const checkboxAll = document.getElementById(`select-all-${tipo}`);
    const checkboxes = document.querySelectorAll(`#contas-${tipo}-section .checkbox-lancamento`);
    
    checkboxes.forEach(cb => {
        cb.checked = checkboxAll.checked;
    });
    
    // Atualizar visibilidade dos botões
    atualizarVisibilidadeBotoesEmMassa(tipo);
    // Atualizar soma dos selecionados
    atualizarSomaSelecionados(tipo);
}

function atualizarSomaSelecionados(tipo) {
    const checkboxes = document.querySelectorAll(`#contas-${tipo}-section .checkbox-lancamento:checked`);
    const divSoma = document.getElementById(`soma-selecionados-${tipo}`);
    const spanValor = document.getElementById(`valor-soma-${tipo}`);
    
    if (checkboxes.length === 0) {
        divSoma.style.display = 'none';
        return;
    }
    
    let soma = 0;
    checkboxes.forEach(cb => {
        const valor = parseFloat(cb.dataset.valor) || 0;
        soma += valor;
    });
    
    spanValor.textContent = soma.toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    });
    
    divSoma.style.display = 'block';
}

async function liquidarEmMassa(tipoOriginal) {
    // Converter RECEITA/DESPESA para receber/pagar
    const tipo = tipoOriginal === 'RECEITA' ? 'receber' : 'pagar';
    const checkboxes = document.querySelectorAll(`#contas-${tipo}-section .checkbox-lancamento:checked`);
    
    if (checkboxes.length === 0) {
        showToast('Selecione pelo menos um lançamento', 'warning');
        return;
    }
    
    // Armazenar tipo para uso na confirmação
    tipoLiquidacaoEmMassa = tipoOriginal;
    
    // Carregar contas bancárias
    try {
        const response = await fetch('/api/contas');
        const contas = await response.json();
        
        const opcoesContas = contas.map(c => 
            `<option value="${c.nome}">${c.banco} - ${c.agencia}/${c.conta}</option>`
        ).join('');
        
        // Criar modal de liquidação em massa
        const modal = createModal(`💰 Liquidar ${checkboxes.length} Lançamento(s)`, `
            <form id="form-liquidacao-massa" onsubmit="return confirmarLiquidacaoEmMassa(event)">
                <div class="form-group">
                    <label>*Data de Liquidação:</label>
                    <input type="date" id="liquidacao-massa-data" value="${new Date().toISOString().split('T')[0]}" required>
                </div>
                
                <div class="form-group">
                    <label>*Conta Bancária:</label>
                    <select id="liquidacao-massa-conta" required>
                        <option value="">Selecione a conta...</option>
                        ${opcoesContas}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Observações:</label>
                    <textarea id="liquidacao-massa-observacoes" rows="3" placeholder="Opcional"></textarea>
                </div>
                
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                    <button type="button" onclick="closeModal()" style="padding: 10px 20px; background: #95a5a6; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">Cancelar</button>
                    <button type="submit" style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold;">💰 Liquidar Todos</button>
                </div>
            </form>
        `);
        
        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('active'), 10);
        
    } catch (error) {
        console.error('Erro ao abrir modal de liquidação em massa:', error);
        showToast('Erro ao carregar contas bancárias', 'error');
    }
}

async function confirmarLiquidacaoEmMassa(event) {
    event.preventDefault();
    
    const tipoOriginal = tipoLiquidacaoEmMassa;
    const tipo = tipoOriginal === 'RECEITA' ? 'receber' : 'pagar';
    const checkboxes = document.querySelectorAll(`#contas-${tipo}-section .checkbox-lancamento:checked`);
    
    const data = document.getElementById('liquidacao-massa-data').value;
    const conta = document.getElementById('liquidacao-massa-conta').value;
    const observacoes = document.getElementById('liquidacao-massa-observacoes').value;
    
    let sucesso = 0;
    let erro = 0;
    
    for (const checkbox of checkboxes) {
        const id = checkbox.getAttribute('data-id');
        try {
            const response = await fetch(`/api/lancamentos/${id}/liquidar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    data_pagamento: data,
                    conta_bancaria: conta,
                    observacoes: observacoes
                })
            });
            
            const result = await response.json();
            if (result.success) {
                sucesso++;
            } else {
                erro++;
            }
        } catch (e) {
            erro++;
        }
    }
    
    closeModal();
    showToast(`✓ ${sucesso} lançamento(s) liquidado(s)${erro > 0 ? `, ${erro} erro(s)` : ''}`, sucesso > 0 ? 'success' : 'error');
    
    if (tipoOriginal === 'RECEITA') {
        loadContasReceber();
    } else {
        loadContasPagar();
    }
    if (typeof loadDashboard === 'function') loadDashboard();
}

async function excluirEmMassa(tipoOriginal) {
    // Converter RECEITA/DESPESA para receber/pagar
    const tipo = tipoOriginal === 'RECEITA' ? 'receber' : 'pagar';
    const checkboxes = document.querySelectorAll(`#contas-${tipo}-section .checkbox-lancamento:checked`);
    
    if (checkboxes.length === 0) {
        showToast('Selecione pelo menos um lançamento', 'warning');
        return;
    }
    
    if (!confirm(`Deseja realmente excluir ${checkboxes.length} lançamento(s)?\n\nAtenção: Esta ação não pode ser desfeita!`)) {
        return;
    }
    
    let sucesso = 0;
    let erro = 0;
    
    for (const checkbox of checkboxes) {
        const id = checkbox.getAttribute('data-id');
        try {
            const response = await fetch(`/api/lancamentos/${id}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            if (result.success) {
                sucesso++;
            } else {
                erro++;
            }
        } catch (e) {
            erro++;
        }
    }
    
    showToast(`✓ ${sucesso} lançamento(s) excluído(s)${erro > 0 ? `, ${erro} erro(s)` : ''}`, sucesso > 0 ? 'success' : 'error');
    
    if (tipoOriginal === 'RECEITA') {
        loadContasReceber();
    } else {
        loadContasPagar();
    }
    if (typeof loadDashboard === 'function') loadDashboard();
}

// === FLUXO DE CAIXA ===

async function carregarFluxoCaixa() {
    try {
        // Obter filtros
        const ano = document.getElementById('filter-ano-fluxo').value;
        const mes = document.getElementById('filter-mes-fluxo').value;
        const dataInicial = document.getElementById('filter-data-inicial-fluxo').value;
        const dataFinal = document.getElementById('filter-data-final-fluxo').value;
        const banco = document.getElementById('filter-banco-fluxo').value;
        
        // Filtros do fluxo de caixa
        
        // Determinar período
        let data_inicio, data_fim;
        
        if (dataInicial && dataFinal) {
            // Usar período personalizado (prioridade máxima)
            data_inicio = dataInicial;
            data_fim = dataFinal;
            // Período personalizado
        } else if (ano && ano.trim() !== '' && mes && mes.trim() !== '') {
            // Usar ano/mês específico (ambos preenchidos)
            const anoNum = parseInt(ano);
            const mesNum = parseInt(mes);
            const mesPadded = mes.length === 1 ? '0' + mes : mes;
            
            // Calcular último dia do mês corretamente
            const ultimoDia = new Date(anoNum, mesNum, 0).getDate();
            const diaPadded = String(ultimoDia).padStart(2, '0');
            
            data_inicio = `${anoNum}-${mesPadded}-01`;
            data_fim = `${anoNum}-${mesPadded}-${diaPadded}`;
            // Ano/mês
        } else if (ano && ano.trim() !== '') {
            // Usar ano inteiro (só ano preenchido)
            data_inicio = `${ano}-01-01`;
            data_fim = `${ano}-12-31`;
            // Ano inteiro
        } else if (mes && mes.trim() !== '') {
            // Usar mês do ano atual (só mês preenchido)
            const hoje = new Date();
            const anoAtual = hoje.getFullYear();
            const mesNum = parseInt(mes);
            const mesPadded = mes.length === 1 ? '0' + mes : mes;
            const ultimoDia = new Date(anoAtual, mesNum, 0).getDate();
            const diaPadded = String(ultimoDia).padStart(2, '0');
            
            data_inicio = `${anoAtual}-${mesPadded}-01`;
            data_fim = `${anoAtual}-${mesPadded}-${diaPadded}`;
            // Mês do ano atual
        } else {
            // Usar mês atual (padrão - nada preenchido)
            const hoje = new Date();
            const anoAtual = hoje.getFullYear();
            const mesAtual = hoje.getMonth() + 1; // 0-11 -> 1-12
            const mesPadded = String(mesAtual).padStart(2, '0');
            const ultimoDia = new Date(anoAtual, mesAtual, 0).getDate();
            const diaPadded = String(ultimoDia).padStart(2, '0');
            
            data_inicio = `${anoAtual}-${mesPadded}-01`;
            data_fim = `${anoAtual}-${mesPadded}-${diaPadded}`;
            // Mês atual (padrão)
        }
        
        // Período calculado
        
        // Buscar lançamentos liquidados
        const response = await fetch(`/api/relatorios/fluxo-caixa?data_inicio=${data_inicio}&data_fim=${data_fim}`);
        const lancamentos = await response.json();
        
        // Lançamentos carregados
        
        // Filtrar por banco se selecionado
        let lancamentosFiltrados = lancamentos;
        if (banco) {
            // Filtrar por banco
            lancamentosFiltrados = lancamentos.filter(l => l.conta_bancaria === banco);
        }
        
        // Calcular totais
        let totalReceitas = 0;
        let totalDespesas = 0;
        
        lancamentosFiltrados.forEach(l => {
            if (l.tipo.toLowerCase() === 'receita') {
                totalReceitas += l.valor;
            } else if (l.tipo.toLowerCase() === 'despesa') {
                totalDespesas += l.valor;
            }
        });
        
        const saldoPeriodo = totalReceitas - totalDespesas;
        
        // Buscar dados dos bancos
        const responseBanco = await fetch('/api/contas');
        const contas = await responseBanco.json();
        
        // Gerar HTML
        let html = '';
        
        // Mostrar informativo dos bancos
        if (banco) {
            // Banco específico filtrado
            const contaFiltrada = contas.find(c => c.nome === banco);
            if (contaFiltrada) {
                const cor = contaFiltrada.saldo >= 0 ? '#27ae60' : '#e74c3c';
                html += `
                    <div style="background: white; padding: 12px 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <div style="font-size: 11px; color: #7f8c8d; margin-bottom: 2px;">🏦 BANCO FILTRADO</div>
                            <div style="font-size: 14px; font-weight: 600; color: #2c3e50;">${contaFiltrada.nome}</div>
                            <div style="font-size: 11px; color: #95a5a6;">${contaFiltrada.banco} • Ag: ${contaFiltrada.agencia} • Conta: ${contaFiltrada.conta}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 11px; color: #7f8c8d; margin-bottom: 2px;">SALDO REAL</div>
                            <div style="font-size: 18px; font-weight: bold; color: ${cor};">
                                R$ ${contaFiltrada.saldo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                            </div>
                        </div>
                    </div>
                `;
            }
        } else {
            // Calcular saldo total de todas as contas
            const saldoTotal = contas.reduce((total, conta) => total + conta.saldo, 0);
            const corTotal = saldoTotal >= 0 ? '#27ae60' : '#e74c3c';
            
            html += `
                <div style="background: white; padding: 12px 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <div style="font-size: 11px; color: #7f8c8d; margin-bottom: 2px;">💰 TODAS AS CONTAS</div>
                        <div style="font-size: 14px; font-weight: 600; color: #2c3e50;">${contas.length} conta${contas.length > 1 ? 's' : ''} bancária${contas.length > 1 ? 's' : ''}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 11px; color: #7f8c8d; margin-bottom: 2px;">SALDO TOTAL</div>
                        <div style="font-size: 18px; font-weight: bold; color: ${corTotal};">
                            R$ ${saldoTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                        </div>
                    </div>
                </div>
            `;
        }
        
        html += `
            <div style="background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <thead>
                        <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                            <th style="padding: 10px 12px; text-align: left; color: #ffffff; font-weight: 600; font-size: 12px;">Data Pagamento</th>
                            <th style="padding: 10px 12px; text-align: left; color: #ffffff; font-weight: 600; font-size: 12px;">Tipo</th>
                            <th style="padding: 10px 12px; text-align: left; color: #ffffff; font-weight: 600; font-size: 12px;">Razão Social</th>
                            <th style="padding: 10px 12px; text-align: left; color: #ffffff; font-weight: 600; font-size: 12px;">Categoria</th>
                            <th style="padding: 10px 12px; text-align: left; color: #ffffff; font-weight: 600; font-size: 12px;">Subcategoria</th>
                            <th style="padding: 10px 12px; text-align: left; color: #ffffff; font-weight: 600; font-size: 12px;">Descrição</th>
                            <th style="padding: 10px 12px; text-align: left; color: #ffffff; font-weight: 600; font-size: 12px;">Banco</th>
                            <th style="padding: 10px 12px; text-align: right; color: #ffffff; font-weight: 600; font-size: 12px;">Valor</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        if (lancamentosFiltrados.length === 0) {
            html += `
                <tr>
                    <td colspan="8" style="padding: 40px; text-align: center; color: #95a5a6;">
                        Nenhum lançamento liquidado encontrado no período
                    </td>
                </tr>
            `;
        } else {
            // Ordenar por data de pagamento (crescente - mais antiga para mais recente)
            lancamentosFiltrados.sort((a, b) => new Date(a.data_pagamento) - new Date(b.data_pagamento));
            
            lancamentosFiltrados.forEach(l => {
                const dataPagamento = l.data_pagamento ? new Date(l.data_pagamento + 'T00:00:00').toLocaleDateString('pt-BR') : '-';
                const tipo = l.tipo.toLowerCase() === 'receita' ? '💰 Receita' : '💸 Despesa';
                const cor = l.tipo.toLowerCase() === 'receita' ? '#27ae60' : '#e74c3c';
                
                html += `
                    <tr style="border-bottom: 1px solid #ecf0f1;">
                        <td style="padding: 10px 12px; color: #2c3e50; font-size: 12px;">${dataPagamento}</td>
                        <td style="padding: 10px 12px;"><span style="color: ${cor}; font-weight: 600; font-size: 12px;">${tipo}</span></td>
                        <td style="padding: 10px 12px; color: #2c3e50; font-size: 12px;">${l.pessoa || '-'}</td>
                        <td style="padding: 10px 12px; color: #2c3e50; font-size: 12px;">${l.categoria || '-'}</td>
                        <td style="padding: 10px 12px; color: #2c3e50; font-size: 12px;">${l.subcategoria || '-'}</td>
                        <td style="padding: 10px 12px; color: #7f8c8d; font-size: 11px;">${l.descricao || '-'}</td>
                        <td style="padding: 10px 12px; color: #34495e; font-size: 11px;">${l.conta_bancaria || '-'}</td>
                        <td style="padding: 10px 12px; text-align: right; font-weight: bold; color: ${cor}; font-size: 13px;">R$ ${l.valor.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    </tr>
                `;
            });
        }
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        document.getElementById('fluxo-caixa-content').innerHTML = html;
        
    } catch (error) {
        console.error('Erro ao carregar fluxo de caixa:', error);
        document.getElementById('fluxo-caixa-content').innerHTML = `
            <div style="padding: 40px; text-align: center; color: #e74c3c;">
                ❌ Erro ao carregar fluxo de caixa
            </div>
        `;
    }
}

async function limparFiltrosFluxo() {
    document.getElementById('filter-ano-fluxo').value = '';
    document.getElementById('filter-mes-fluxo').value = '';
    document.getElementById('filter-data-inicial-fluxo').value = '';
    document.getElementById('filter-data-final-fluxo').value = '';
    document.getElementById('filter-banco-fluxo').value = '';
    await carregarFluxoCaixa();
}

// Carregar bancos no filtro de fluxo de caixa
async function carregarBancosFluxo() {
    try {
        const response = await fetch('/api/contas');
        const contas = await response.json();
        
        const select = document.getElementById('filter-banco-fluxo');
        select.innerHTML = '<option value="">Todos</option>';
        
        contas.forEach(c => {
            const option = document.createElement('option');
            option.value = c.nome;
            option.textContent = `${c.banco} - ${c.agencia}/${c.conta}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Erro ao carregar bancos:', error);
    }
}

// Exportar funções
window.loadCategoriasTable = loadCategoriasTable;
window.editarCategoria = editarCategoria;
window.excluirCategoria = excluirCategoria;
window.loadContasBancarias = loadContasBancarias;
window.editarConta = editarConta;
window.excluirConta = excluirConta;
window.filtrarPorBanco = filtrarPorBanco;
window.loadContasReceber = loadContasReceber;
window.loadContasPagar = loadContasPagar;
window.liquidarLancamento = liquidarLancamento;
window.confirmarLiquidacao = confirmarLiquidacao;
window.editarLancamento = editarLancamento;
window.excluirLancamento = excluirLancamento;
window.toggleSelectAll = toggleSelectAll;
window.liquidarEmMassa = liquidarEmMassa;
window.confirmarLiquidacaoEmMassa = confirmarLiquidacaoEmMassa;
window.excluirEmMassa = excluirEmMassa;
window.carregarFluxoCaixa = carregarFluxoCaixa;
window.limparFiltrosFluxo = limparFiltrosFluxo;
window.carregarBancosFluxo = carregarBancosFluxo;

// Função para exportar Fluxo de Caixa em PDF
async function exportarFluxoPDF() {
    try {
        // Obter filtros
        const ano = document.getElementById('filter-ano-fluxo').value;
        const mes = document.getElementById('filter-mes-fluxo').value;
        const dataInicial = document.getElementById('filter-data-inicial-fluxo').value;
        const dataFinal = document.getElementById('filter-data-final-fluxo').value;
        const bancoFiltro = document.getElementById('filter-banco-fluxo').value;
        
        // Determinar período
        let data_inicio, data_fim, periodoTexto;
        
        if (dataInicial && dataFinal) {
            data_inicio = dataInicial;
            data_fim = dataFinal;
            periodoTexto = `${new Date(dataInicial).toLocaleDateString('pt-BR')} a ${new Date(dataFinal).toLocaleDateString('pt-BR')}`;
        } else if (ano && mes) {
            const anoNum = parseInt(ano);
            const mesNum = parseInt(mes);
            const mesPadded = mes.length === 1 ? '0' + mes : mes;
            const ultimoDia = new Date(anoNum, mesNum, 0).getDate();
            data_inicio = `${anoNum}-${mesPadded}-01`;
            data_fim = `${anoNum}-${mesPadded}-${String(ultimoDia).padStart(2, '0')}`;
            const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
            periodoTexto = `${meses[mesNum - 1]}/${ano}`;
        } else if (ano) {
            data_inicio = `${ano}-01-01`;
            data_fim = `${ano}-12-31`;
            periodoTexto = ano;
        } else {
            const hoje = new Date();
            const anoAtual = hoje.getFullYear();
            const mesAtual = hoje.getMonth() + 1;
            const mesPadded = String(mesAtual).padStart(2, '0');
            const ultimoDia = new Date(anoAtual, mesAtual, 0).getDate();
            data_inicio = `${anoAtual}-${mesPadded}-01`;
            data_fim = `${anoAtual}-${mesPadded}-${String(ultimoDia).padStart(2, '0')}`;
            const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
            periodoTexto = `${meses[mesAtual - 1]}/${anoAtual}`;
        }
        
        // Buscar lançamentos
        const response = await fetch(`/api/relatorios/fluxo-caixa?data_inicio=${data_inicio}&data_fim=${data_fim}`);
        const lancamentos = await response.json();
        
        // Filtrar por banco
        let lancamentosFiltrados = lancamentos;
        let bancoTexto = 'Todos os Bancos';
        if (bancoFiltro) {
            lancamentosFiltrados = lancamentos.filter(l => l.conta_bancaria === bancoFiltro);
            bancoTexto = bancoFiltro;
        }
        
        // Calcular totais
        let totalReceitas = 0;
        let totalDespesas = 0;
        
        lancamentosFiltrados.forEach(l => {
            if (l.tipo.toLowerCase() === 'receita') {
                totalReceitas += l.valor;
            } else if (l.tipo.toLowerCase() === 'despesa') {
                totalDespesas += l.valor;
            }
        });
        
        const saldo = totalReceitas - totalDespesas;
        const dataAtual = new Date().toLocaleDateString('pt-BR');
        
        // Gerar HTML do PDF
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Fluxo de Caixa - ${periodoTexto}</title>
                <style>
                    @page { size: landscape; margin: 12mm; }
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        padding: 20px;
                        background: white;
                        color: #1a252f;
                    }
                    .header {
                        margin-bottom: 30px;
                        padding: 25px;
                        background: #2c3e50;
                        border-radius: 8px;
                        color: white;
                        border: 3px solid #1a252f;
                    }
                    .header h1 {
                        font-size: 22px;
                        margin-bottom: 12px;
                        letter-spacing: 3px;
                        text-align: center;
                        font-weight: 700;
                    }
                    .header .info {
                        font-size: 13px;
                        margin: 6px 0;
                        opacity: 0.95;
                        text-align: center;
                        font-weight: 500;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 25px;
                        font-size: 11px;
                        border: 2px solid #2c3e50;
                    }
                    th {
                        background: #34495e;
                        color: white;
                        padding: 12px 10px;
                        text-align: left;
                        font-weight: 700;
                        border: 1px solid #2c3e50;
                        font-size: 11px;
                        letter-spacing: 0.5px;
                        text-transform: uppercase;
                    }
                    td {
                        padding: 10px;
                        border: 1px solid #d5d8dc;
                        font-size: 11px;
                    }
                    tbody tr:nth-child(odd) {
                        background: white;
                    }
                    tbody tr:nth-child(even) {
                        background: #f8f9fa;
                    }
                    tbody tr:hover {
                        background: #ecf0f1;
                    }
                    .receita {
                        color: #27ae60;
                        font-weight: 700;
                    }
                    .despesa {
                        color: #e74c3c;
                        font-weight: 700;
                    }
                    .totais {
                        background: white;
                        padding: 20px;
                        border: 2px solid #2c3e50;
                        border-radius: 4px;
                        margin-top: 25px;
                        display: flex;
                        justify-content: space-around;
                        align-items: center;
                    }
                    .total-item {
                        text-align: center;
                        padding: 0 20px;
                    }
                    .total-item:not(:last-child) {
                        border-right: 2px solid #ecf0f1;
                    }
                    .total-label {
                        font-size: 11px;
                        color: #7f8c8d;
                        font-weight: 600;
                        text-transform: uppercase;
                        margin-bottom: 8px;
                        letter-spacing: 0.8px;
                    }
                    .total-valor {
                        font-size: 16px;
                        font-weight: 700;
                    }
                    .total-entrada { color: #27ae60; }
                    .total-saida { color: #e74c3c; }
                    .total-saldo { color: ${saldo >= 0 ? '#27ae60' : '#e74c3c'}; }
                    .rodape {
                        margin-top: 30px;
                        padding: 12px;
                        border-top: 2px solid #bdc3c7;
                        text-align: center;
                        font-size: 9px;
                        color: #7f8c8d;
                        background: #f8f9fa;
                        border-radius: 4px;
                    }
                    @media print {
                        body { background: white; }
                        .header { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        th { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        .totais { page-break-inside: avoid; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        .total-item { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        .rodape { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        tbody tr:hover { background: inherit; }
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>FLUXO DE CAIXA</h1>
                    <div class="info">Período: ${periodoTexto}</div>
                    <div class="info">Banco: ${bancoTexto}</div>
                    <div class="info">Emitido em: ${dataAtual}</div>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th style="width: 80px;">Data</th>
                            <th style="width: 140px;">Categoria</th>
                            <th style="width: 120px;">Subcategoria</th>
                            <th style="width: 180px;">Razão Social</th>
                            <th style="width: 140px;">Conta Bancária</th>
                            <th style="width: 100px; text-align: center;">Entrada</th>
                            <th style="width: 100px; text-align: center;">Saída</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${lancamentosFiltrados.map(l => `
                            <tr>
                                <td style="text-align: center;">${new Date(l.data_pagamento).toLocaleDateString('pt-BR')}</td>
                                <td>${l.categoria || '-'}</td>
                                <td>${l.subcategoria || '-'}</td>
                                <td>${l.pessoa || l.cliente_fornecedor || '-'}</td>
                                <td>${l.conta_bancaria || '-'}</td>
                                <td style="text-align: right;" class="receita">${l.tipo.toLowerCase() === 'receita' ? 'R$ ' + l.valor.toLocaleString('pt-BR', {minimumFractionDigits: 2}) : '-'}</td>
                                <td style="text-align: right;" class="despesa">${l.tipo.toLowerCase() === 'despesa' ? 'R$ ' + l.valor.toLocaleString('pt-BR', {minimumFractionDigits: 2}) : '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                
                <div class="totais">
                    <div class="total-item">
                        <div class="total-label">Entradas</div>
                        <div class="total-valor total-entrada">R$ ${totalReceitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    </div>
                    <div class="total-item">
                        <div class="total-label">Saídas</div>
                        <div class="total-valor total-saida">R$ ${totalDespesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    </div>
                    <div class="total-item">
                        <div class="total-label">Saldo</div>
                        <div class="total-valor total-saldo">R$ ${saldo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    </div>
                </div>
                
                <div class="rodape">
                    <p>Sistema de Gestão Financeira • Fluxo de Caixa • Gerado automaticamente</p>
                </div>
            </body>
            </html>
        `);
        
        printWindow.document.close();
        setTimeout(() => printWindow.print(), 500);
        
    } catch (error) {
        console.error('Erro ao exportar PDF:', error);
        alert('Erro ao gerar PDF. Verifique o console para detalhes.');
    }
}

// Função para exportar Fluxo de Caixa em Excel
async function exportarFluxoExcel() {
    try {
        // Obter filtros
        const ano = document.getElementById('filter-ano-fluxo').value;
        const mes = document.getElementById('filter-mes-fluxo').value;
        const dataInicial = document.getElementById('filter-data-inicial-fluxo').value;
        const dataFinal = document.getElementById('filter-data-final-fluxo').value;
        const bancoFiltro = document.getElementById('filter-banco-fluxo').value;
        
        // Determinar período
        let data_inicio, data_fim, periodoTexto;
        
        if (dataInicial && dataFinal) {
            data_inicio = dataInicial;
            data_fim = dataFinal;
            periodoTexto = `${new Date(dataInicial).toLocaleDateString('pt-BR')} a ${new Date(dataFinal).toLocaleDateString('pt-BR')}`;
        } else if (ano && mes) {
            const anoNum = parseInt(ano);
            const mesNum = parseInt(mes);
            const mesPadded = mes.length === 1 ? '0' + mes : mes;
            const ultimoDia = new Date(anoNum, mesNum, 0).getDate();
            data_inicio = `${anoNum}-${mesPadded}-01`;
            data_fim = `${anoNum}-${mesPadded}-${String(ultimoDia).padStart(2, '0')}`;
            const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
            periodoTexto = `${meses[mesNum - 1]}/${ano}`;
        } else if (ano) {
            data_inicio = `${ano}-01-01`;
            data_fim = `${ano}-12-31`;
            periodoTexto = ano;
        } else {
            const hoje = new Date();
            const anoAtual = hoje.getFullYear();
            const mesAtual = hoje.getMonth() + 1;
            const mesPadded = String(mesAtual).padStart(2, '0');
            const ultimoDia = new Date(anoAtual, mesAtual, 0).getDate();
            data_inicio = `${anoAtual}-${mesPadded}-01`;
            data_fim = `${anoAtual}-${mesPadded}-${String(ultimoDia).padStart(2, '0')}`;
            const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
            periodoTexto = `${meses[mesAtual - 1]}/${anoAtual}`;
        }
        
        // Buscar lançamentos
        const response = await fetch(`/api/relatorios/fluxo-caixa?data_inicio=${data_inicio}&data_fim=${data_fim}`);
        const lancamentos = await response.json();
        
        // Filtrar por banco
        let lancamentosFiltrados = lancamentos;
        let bancoTexto = 'Todos os Bancos';
        if (bancoFiltro) {
            lancamentosFiltrados = lancamentos.filter(l => l.conta_bancaria === bancoFiltro);
            bancoTexto = bancoFiltro;
        }
        
        // Calcular totais
        let totalReceitas = 0;
        let totalDespesas = 0;
        
        lancamentosFiltrados.forEach(l => {
            if (l.tipo.toLowerCase() === 'receita') {
                totalReceitas += l.valor;
            } else if (l.tipo.toLowerCase() === 'despesa') {
                totalDespesas += l.valor;
            }
        });
        
        const saldo = totalReceitas - totalDespesas;
        
        // Preparar dados para Excel
        const dadosExcel = [
            ['FLUXO DE CAIXA'],
            [`Período: ${periodoTexto}`],
            [`Banco: ${bancoTexto}`],
            [`Emitido em: ${new Date().toLocaleDateString('pt-BR')}`],
            [],
            ['Data', 'Tipo', 'Descrição', 'Categoria', 'Cliente/Fornecedor', 'Conta Bancária', 'Valor']
        ];
        
        // Adicionar lançamentos
        lancamentosFiltrados.forEach(l => {
            dadosExcel.push([
                new Date(l.data_pagamento).toLocaleDateString('pt-BR'),
                l.tipo,
                l.descricao,
                l.categoria || '-',
                l.cliente_fornecedor || '-',
                l.conta_bancaria || '-',
                l.valor
            ]);
        });
        
        // Adicionar totais
        dadosExcel.push([]);
        dadosExcel.push(['', '', '', '', '', 'Total de Entradas:', totalReceitas]);
        dadosExcel.push(['', '', '', '', '', 'Total de Saídas:', totalDespesas]);
        dadosExcel.push(['', '', '', '', '', 'Saldo do Período:', saldo]);
        
        // Criar workbook
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.aoa_to_sheet(dadosExcel);
        
        // Configurar larguras das colunas
        ws['!cols'] = [
            { wch: 12 },  // Data
            { wch: 10 },  // Tipo
            { wch: 30 },  // Descrição
            { wch: 20 },  // Categoria
            { wch: 25 },  // Cliente/Fornecedor
            { wch: 20 },  // Conta Bancária
            { wch: 15 }   // Valor
        ];
        
        XLSX.utils.book_append_sheet(wb, ws, 'Fluxo de Caixa');
        XLSX.writeFile(wb, `Fluxo_de_Caixa_${periodoTexto.replace(/\//g, '_')}.xlsx`);
        
    } catch (error) {
        console.error('Erro ao exportar Excel:', error);
        alert('Erro ao gerar Excel. Verifique o console para detalhes.');
    }
}

window.exportarFluxoPDF = exportarFluxoPDF;
window.exportarFluxoExcel = exportarFluxoExcel;

// Função para carregar Comparativo de Períodos
async function carregarComparativoPeriodos() {
    try {
        const ano1 = document.getElementById('filter-ano1').value;
        const mes1 = document.getElementById('filter-mes1').value;
        const ano2 = document.getElementById('filter-ano2').value;
        const mes2 = document.getElementById('filter-mes2').value;
        
        if (!ano1 || !ano2) {
            alert('Por favor, preencha os anos dos dois períodos.');
            return;
        }
        
        // Calcular datas do período 1
        let data_inicio1, data_fim1, periodo1Texto;
        if (mes1) {
            const mesNum1 = parseInt(mes1);
            const ultimoDia1 = new Date(ano1, mesNum1, 0).getDate();
            data_inicio1 = `${ano1}-${String(mesNum1).padStart(2, '0')}-01`;
            data_fim1 = `${ano1}-${String(mesNum1).padStart(2, '0')}-${String(ultimoDia1).padStart(2, '0')}`;
            const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
            periodo1Texto = `${meses[mesNum1 - 1]}/${ano1}`;
        } else {
            data_inicio1 = `${ano1}-01-01`;
            data_fim1 = `${ano1}-12-31`;
            periodo1Texto = ano1;
        }
        
        // Calcular datas do período 2
        let data_inicio2, data_fim2, periodo2Texto;
        if (mes2) {
            const mesNum2 = parseInt(mes2);
            const ultimoDia2 = new Date(ano2, mesNum2, 0).getDate();
            data_inicio2 = `${ano2}-${String(mesNum2).padStart(2, '0')}-01`;
            data_fim2 = `${ano2}-${String(mesNum2).padStart(2, '0')}-${String(ultimoDia2).padStart(2, '0')}`;
            const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
            periodo2Texto = `${meses[mesNum2 - 1]}/${ano2}`;
        } else {
            data_inicio2 = `${ano2}-01-01`;
            data_fim2 = `${ano2}-12-31`;
            periodo2Texto = ano2;
        }
        
        // Buscar lançamentos dos dois períodos
        const [response1, response2] = await Promise.all([
            fetch(`/api/relatorios/fluxo-caixa?data_inicio=${data_inicio1}&data_fim=${data_fim1}`),
            fetch(`/api/relatorios/fluxo-caixa?data_inicio=${data_inicio2}&data_fim=${data_fim2}`)
        ]);
        
        const lancamentos1 = await response1.json();
        const lancamentos2 = await response2.json();
        
        // Calcular totais por categoria para cada período
        const categorias1 = {};
        const categorias2 = {};
        let totalReceitas1 = 0, totalDespesas1 = 0;
        let totalReceitas2 = 0, totalDespesas2 = 0;
        
        lancamentos1.forEach(l => {
            const cat = l.categoria || 'Não Categorizado';
            if (!categorias1[cat]) {
                categorias1[cat] = { receitas: 0, despesas: 0 };
            }
            if (l.tipo.toLowerCase() === 'receita') {
                categorias1[cat].receitas += l.valor;
                totalReceitas1 += l.valor;
            } else if (l.tipo.toLowerCase() === 'despesa') {
                categorias1[cat].despesas += l.valor;
                totalDespesas1 += l.valor;
            }
        });
        
        lancamentos2.forEach(l => {
            const cat = l.categoria || 'Não Categorizado';
            if (!categorias2[cat]) {
                categorias2[cat] = { receitas: 0, despesas: 0 };
            }
            if (l.tipo.toLowerCase() === 'receita') {
                categorias2[cat].receitas += l.valor;
                totalReceitas2 += l.valor;
            } else if (l.tipo.toLowerCase() === 'despesa') {
                categorias2[cat].despesas += l.valor;
                totalDespesas2 += l.valor;
            }
        });
        
        const saldo1 = totalReceitas1 - totalDespesas1;
        const saldo2 = totalReceitas2 - totalDespesas2;
        
        // Unir todas as categorias
        const todasCategorias = new Set([...Object.keys(categorias1), ...Object.keys(categorias2)]);
        
        // Gerar HTML
        let html = `
            <div style="margin-bottom: 30px;">
                <h3 style="margin-bottom: 20px; color: #2c3e50;">Comparativo: ${periodo1Texto} vs ${periodo2Texto}</h3>
                
                <!-- Cards de Resumo -->
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px;">
                    <div style="background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); padding: 20px; border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px;">Receitas</div>
                        <div style="font-size: 18px; font-weight: 700; margin-bottom: 5px;">${periodo1Texto}: R$ ${totalReceitas1.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div style="font-size: 18px; font-weight: 700; margin-bottom: 10px;">${periodo2Texto}: R$ ${totalReceitas2.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div style="font-size: 13px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.3);">
                            Variação: ${totalReceitas1 > 0 ? ((totalReceitas2 - totalReceitas1) / totalReceitas1 * 100).toFixed(1) : '0.0'}%
                            ${totalReceitas2 >= totalReceitas1 ? '📈' : '📉'}
                        </div>
                    </div>
                    
                    <div style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); padding: 20px; border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px;">Despesas</div>
                        <div style="font-size: 18px; font-weight: 700; margin-bottom: 5px;">${periodo1Texto}: R$ ${totalDespesas1.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div style="font-size: 18px; font-weight: 700; margin-bottom: 10px;">${periodo2Texto}: R$ ${totalDespesas2.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div style="font-size: 13px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.3);">
                            Variação: ${totalDespesas1 > 0 ? ((totalDespesas2 - totalDespesas1) / totalDespesas1 * 100).toFixed(1) : '0.0'}%
                            ${totalDespesas2 >= totalDespesas1 ? '📈' : '📉'}
                        </div>
                    </div>
                    
                    <div style="background: linear-gradient(135deg, ${saldo2 >= 0 ? '#27ae60' : '#e67e22'} 0%, ${saldo2 >= 0 ? '#229954' : '#d35400'} 100%); padding: 20px; border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px;">Saldo</div>
                        <div style="font-size: 18px; font-weight: 700; margin-bottom: 5px;">${periodo1Texto}: R$ ${saldo1.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div style="font-size: 18px; font-weight: 700; margin-bottom: 10px;">${periodo2Texto}: R$ ${saldo2.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div style="font-size: 13px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.3);">
                            ${saldo2 >= saldo1 ? 'Melhor resultado' : 'Resultado inferior'}
                        </div>
                    </div>
                </div>
                
                <!-- Tabela Comparativa por Categoria -->
                <div style="background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #34495e; color: white;">
                                <th style="padding: 12px; text-align: left; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Categoria</th>
                                <th style="padding: 12px; text-align: right; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">${periodo1Texto}<br>Receitas</th>
                                <th style="padding: 12px; text-align: right; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">${periodo1Texto}<br>Despesas</th>
                                <th style="padding: 12px; text-align: right; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">${periodo2Texto}<br>Receitas</th>
                                <th style="padding: 12px; text-align: right; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">${periodo2Texto}<br>Despesas</th>
                                <th style="padding: 12px; text-align: center; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Variação</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        Array.from(todasCategorias).sort().forEach((cat, index) => {
            const cat1 = categorias1[cat] || { receitas: 0, despesas: 0 };
            const cat2 = categorias2[cat] || { receitas: 0, despesas: 0 };
            const saldoCat1 = cat1.receitas - cat1.despesas;
            const saldoCat2 = cat2.receitas - cat2.despesas;
            const variacao = saldoCat1 !== 0 ? ((saldoCat2 - saldoCat1) / Math.abs(saldoCat1) * 100).toFixed(1) : '0.0';
            
            html += `
                <tr style="background: ${index % 2 === 0 ? '#f8f9fa' : 'white'};">
                    <td style="padding: 12px; font-weight: 600; color: #2c3e50; border-bottom: 1px solid #ecf0f1;">${cat}</td>
                    <td style="padding: 12px; text-align: right; color: #27ae60; font-weight: 600; border-bottom: 1px solid #ecf0f1;">R$ ${cat1.receitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td style="padding: 12px; text-align: right; color: #e74c3c; font-weight: 600; border-bottom: 1px solid #ecf0f1;">R$ ${cat1.despesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td style="padding: 12px; text-align: right; color: #27ae60; font-weight: 600; border-bottom: 1px solid #ecf0f1;">R$ ${cat2.receitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td style="padding: 12px; text-align: right; color: #e74c3c; font-weight: 600; border-bottom: 1px solid #ecf0f1;">R$ ${cat2.despesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td style="padding: 12px; text-align: center; font-weight: 700; color: ${parseFloat(variacao) >= 0 ? '#27ae60' : '#e74c3c'}; border-bottom: 1px solid #ecf0f1;">${variacao}% ${parseFloat(variacao) >= 0 ? '📈' : '📉'}</td>
                </tr>
            `;
        });
        
        html += `
                            <tr style="background: #34495e; color: white; font-weight: 700;">
                                <td style="padding: 14px; text-transform: uppercase; letter-spacing: 0.5px;">TOTAL</td>
                                <td style="padding: 14px; text-align: right;">R$ ${totalReceitas1.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                                <td style="padding: 14px; text-align: right;">R$ ${totalDespesas1.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                                <td style="padding: 14px; text-align: right;">R$ ${totalReceitas2.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                                <td style="padding: 14px; text-align: right;">R$ ${totalDespesas2.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                                <td style="padding: 14px; text-align: center;">-</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        document.getElementById('comparativo-periodos-content').innerHTML = html;
        
    } catch (error) {
        console.error('Erro ao carregar comparativo:', error);
        document.getElementById('comparativo-periodos-content').innerHTML = '<p style="color: red;">Erro ao carregar comparativo. Verifique o console.</p>';
    }
}

// Função para exportar comparativo de períodos em PDF
async function exportarComparativoPDF() {
    try {
        // Obter filtros dos períodos
        const ano1 = document.getElementById('filter-ano1').value;
        const mes1 = document.getElementById('filter-mes1').value;
        const ano2 = document.getElementById('filter-ano2').value;
        const mes2 = document.getElementById('filter-mes2').value;
        
        if (!ano1 || !mes1 || !ano2 || !mes2) {
            alert('Selecione os dois períodos para comparar.');
            return;
        }
        
        // Calcular datas de início e fim para cada período
        const data_inicio1 = `${ano1}-${mes1.padStart(2, '0')}-01`;
        const ultimoDia1 = new Date(ano1, parseInt(mes1), 0).getDate();
        const data_fim1 = `${ano1}-${mes1.padStart(2, '0')}-${ultimoDia1}`;
        
        const data_inicio2 = `${ano2}-${mes2.padStart(2, '0')}-01`;
        const ultimoDia2 = new Date(ano2, parseInt(mes2), 0).getDate();
        const data_fim2 = `${ano2}-${mes2.padStart(2, '0')}-${ultimoDia2}`;
        
        // Buscar dados dos dois períodos
        const [response1, response2] = await Promise.all([
            fetch(`/api/relatorios/fluxo-caixa?data_inicio=${data_inicio1}&data_fim=${data_fim1}`),
            fetch(`/api/relatorios/fluxo-caixa?data_inicio=${data_inicio2}&data_fim=${data_fim2}`)
        ]);
        
        if (!response1.ok || !response2.ok) throw new Error('Erro ao buscar dados');
        
        const lancamentos1 = await response1.json();
        const lancamentos2 = await response2.json();
        
        // Processar categorias período 1
        const categorias1 = {};
        let totalReceitas1 = 0;
        let totalDespesas1 = 0;
        
        lancamentos1.forEach(l => {
            const cat = l.categoria || 'Não Categorizado';
            if (!categorias1[cat]) categorias1[cat] = { receitas: 0, despesas: 0 };
            
            if (l.tipo === 'receita') {
                categorias1[cat].receitas += parseFloat(l.valor);
                totalReceitas1 += parseFloat(l.valor);
            } else {
                categorias1[cat].despesas += parseFloat(l.valor);
                totalDespesas1 += parseFloat(l.valor);
            }
        });
        
        // Processar categorias período 2
        const categorias2 = {};
        let totalReceitas2 = 0;
        let totalDespesas2 = 0;
        
        lancamentos2.forEach(l => {
            const cat = l.categoria || 'Não Categorizado';
            if (!categorias2[cat]) categorias2[cat] = { receitas: 0, despesas: 0 };
            
            if (l.tipo === 'receita') {
                categorias2[cat].receitas += parseFloat(l.valor);
                totalReceitas2 += parseFloat(l.valor);
            } else {
                categorias2[cat].despesas += parseFloat(l.valor);
                totalDespesas2 += parseFloat(l.valor);
            }
        });
        
        const saldo1 = totalReceitas1 - totalDespesas1;
        const saldo2 = totalReceitas2 - totalDespesas2;
        const todasCategorias = new Set([...Object.keys(categorias1), ...Object.keys(categorias2)]);
        
        // Nomes dos meses
        const meses = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
        
        // Criar janela de impressão
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Comparativo de Períodos</title>
                <style>
                    @media print {
                        * {
                            -webkit-print-color-adjust: exact !important;
                            print-color-adjust: exact !important;
                            color-adjust: exact !important;
                        }
                    }
                    body {
                        font-family: 'Segoe UI', Arial, sans-serif;
                        margin: 20px;
                        color: #2c3e50;
                    }
                    h1 {
                        text-align: center;
                        color: #2c3e50;
                        font-size: 24px;
                        margin-bottom: 10px;
                    }
                    .subtitle {
                        text-align: center;
                        color: #7f8c8d;
                        font-size: 14px;
                        margin-bottom: 20px;
                    }
                    .cards {
                        display: flex;
                        justify-content: space-around;
                        margin-bottom: 25px;
                        gap: 15px;
                    }
                    .card {
                        flex: 1;
                        padding: 15px;
                        border-radius: 8px;
                        text-align: center;
                    }
                    .card-receitas {
                        background: linear-gradient(135deg, #27ae60, #2ecc71);
                        color: white;
                    }
                    .card-despesas {
                        background: linear-gradient(135deg, #e74c3c, #c0392b);
                        color: white;
                    }
                    .card-saldo {
                        background: linear-gradient(135deg, #3498db, #2980b9);
                        color: white;
                    }
                    .card h3 {
                        margin: 0 0 8px 0;
                        font-size: 14px;
                        opacity: 0.9;
                    }
                    .card .value {
                        font-size: 20px;
                        font-weight: 700;
                        margin: 5px 0;
                    }
                    .card .variation {
                        font-size: 12px;
                        margin-top: 5px;
                        opacity: 0.95;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 20px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    th {
                        background: #34495e;
                        color: white;
                        padding: 12px;
                        text-align: left;
                        font-weight: 600;
                        font-size: 13px;
                    }
                    th.right {
                        text-align: right;
                    }
                    th.center {
                        text-align: center;
                    }
                    td {
                        padding: 10px 12px;
                        border-bottom: 1px solid #ecf0f1;
                        font-size: 12px;
                    }
                    td.right {
                        text-align: right;
                    }
                    td.center {
                        text-align: center;
                    }
                    tr:nth-child(even) {
                        background: #f8f9fa;
                    }
                    tr.total {
                        background: #34495e !important;
                        color: white;
                        font-weight: 700;
                    }
                    .receita {
                        color: #27ae60;
                        font-weight: 600;
                    }
                    .despesa {
                        color: #e74c3c;
                        font-weight: 600;
                    }
                    .variacao-positiva {
                        color: #27ae60;
                        font-weight: 700;
                    }
                    .variacao-negativa {
                        color: #e74c3c;
                        font-weight: 700;
                    }
                </style>
            </head>
            <body>
                <h1>COMPARATIVO DE PERÍODOS</h1>
                <div class="subtitle">
                    ${meses[parseInt(mes1)]}/${ano1} vs ${meses[parseInt(mes2)]}/${ano2}
                </div>
                
                <div class="cards">
                    <div class="card card-receitas">
                        <h3>RECEITAS</h3>
                        <div class="value">R$ ${totalReceitas1.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div class="value">R$ ${totalReceitas2.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div class="variation">
                            ${totalReceitas1 !== 0 ? 
                                ((totalReceitas2 - totalReceitas1) / totalReceitas1 * 100).toFixed(1) : '0.0'}%
                        </div>
                    </div>
                    
                    <div class="card card-despesas">
                        <h3>DESPESAS</h3>
                        <div class="value">R$ ${totalDespesas1.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div class="value">R$ ${totalDespesas2.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div class="variation">
                            ${totalDespesas1 !== 0 ? 
                                ((totalDespesas2 - totalDespesas1) / totalDespesas1 * 100).toFixed(1) : '0.0'}%
                        </div>
                    </div>
                    
                    <div class="card card-saldo">
                        <h3>SALDO</h3>
                        <div class="value">R$ ${saldo1.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div class="value">R$ ${saldo2.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div class="variation">
                            ${saldo1 !== 0 ? 
                                ((saldo2 - saldo1) / Math.abs(saldo1) * 100).toFixed(1) : '0.0'}%
                        </div>
                    </div>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>Categoria</th>
                            <th class="right">Receitas<br>${meses[parseInt(mes1)]}/${ano1}</th>
                            <th class="right">Despesas<br>${meses[parseInt(mes1)]}/${ano1}</th>
                            <th class="right">Receitas<br>${meses[parseInt(mes2)]}/${ano2}</th>
                            <th class="right">Despesas<br>${meses[parseInt(mes2)]}/${ano2}</th>
                            <th class="center">Variação</th>
                        </tr>
                    </thead>
                    <tbody>
        `);
        
        // Adicionar linhas de categorias
        Array.from(todasCategorias).sort().forEach(cat => {
            const cat1 = categorias1[cat] || { receitas: 0, despesas: 0 };
            const cat2 = categorias2[cat] || { receitas: 0, despesas: 0 };
            const saldoCat1 = cat1.receitas - cat1.despesas;
            const saldoCat2 = cat2.receitas - cat2.despesas;
            const variacao = saldoCat1 !== 0 ? 
                ((saldoCat2 - saldoCat1) / Math.abs(saldoCat1) * 100).toFixed(1) : '0.0';
            
            printWindow.document.write(`
                <tr>
                    <td><strong>${cat}</strong></td>
                    <td class="right receita">R$ ${cat1.receitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td class="right despesa">R$ ${cat1.despesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td class="right receita">R$ ${cat2.receitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td class="right despesa">R$ ${cat2.despesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td class="center ${parseFloat(variacao) >= 0 ? 'variacao-positiva' : 'variacao-negativa'}">
                        ${variacao}%
                    </td>
                </tr>
            `);
        });
        
        printWindow.document.write(`
                        <tr class="total">
                            <td>TOTAL</td>
                            <td class="right">R$ ${totalReceitas1.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                            <td class="right">R$ ${totalDespesas1.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                            <td class="right">R$ ${totalReceitas2.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                            <td class="right">R$ ${totalDespesas2.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                            <td class="center">-</td>
                        </tr>
                    </tbody>
                </table>
            </body>
            </html>
        `);
        
        printWindow.document.close();
        setTimeout(() => printWindow.print(), 250);
        
    } catch (error) {
        console.error('Erro ao exportar PDF:', error);
        alert('Erro ao gerar PDF do comparativo.');
    }
}

// Função para exportar comparativo de períodos em Excel
async function exportarComparativoExcel() {
    try {
        // Obter filtros dos períodos
        const ano1 = document.getElementById('filter-ano1').value;
        const mes1 = document.getElementById('filter-mes1').value;
        const ano2 = document.getElementById('filter-ano2').value;
        const mes2 = document.getElementById('filter-mes2').value;
        
        if (!ano1 || !mes1 || !ano2 || !mes2) {
            alert('Selecione os dois períodos para comparar.');
            return;
        }
        
        // Calcular datas de início e fim para cada período
        const data_inicio1 = `${ano1}-${mes1.padStart(2, '0')}-01`;
        const ultimoDia1 = new Date(ano1, parseInt(mes1), 0).getDate();
        const data_fim1 = `${ano1}-${mes1.padStart(2, '0')}-${ultimoDia1}`;
        
        const data_inicio2 = `${ano2}-${mes2.padStart(2, '0')}-01`;
        const ultimoDia2 = new Date(ano2, parseInt(mes2), 0).getDate();
        const data_fim2 = `${ano2}-${mes2.padStart(2, '0')}-${ultimoDia2}`;
        
        // Buscar dados dos dois períodos
        const [response1, response2] = await Promise.all([
            fetch(`/api/relatorios/fluxo-caixa?data_inicio=${data_inicio1}&data_fim=${data_fim1}`),
            fetch(`/api/relatorios/fluxo-caixa?data_inicio=${data_inicio2}&data_fim=${data_fim2}`)
        ]);
        
        if (!response1.ok || !response2.ok) throw new Error('Erro ao buscar dados');
        
        const lancamentos1 = await response1.json();
        const lancamentos2 = await response2.json();
        
        // Processar categorias período 1
        const categorias1 = {};
        let totalReceitas1 = 0;
        let totalDespesas1 = 0;
        
        lancamentos1.forEach(l => {
            const cat = l.categoria || 'Não Categorizado';
            if (!categorias1[cat]) categorias1[cat] = { receitas: 0, despesas: 0 };
            
            if (l.tipo === 'receita') {
                categorias1[cat].receitas += parseFloat(l.valor);
                totalReceitas1 += parseFloat(l.valor);
            } else {
                categorias1[cat].despesas += parseFloat(l.valor);
                totalDespesas1 += parseFloat(l.valor);
            }
        });
        
        // Processar categorias período 2
        const categorias2 = {};
        let totalReceitas2 = 0;
        let totalDespesas2 = 0;
        
        lancamentos2.forEach(l => {
            const cat = l.categoria || 'Não Categorizado';
            if (!categorias2[cat]) categorias2[cat] = { receitas: 0, despesas: 0 };
            
            if (l.tipo === 'receita') {
                categorias2[cat].receitas += parseFloat(l.valor);
                totalReceitas2 += parseFloat(l.valor);
            } else {
                categorias2[cat].despesas += parseFloat(l.valor);
                totalDespesas2 += parseFloat(l.valor);
            }
        });
        
        const todasCategorias = new Set([...Object.keys(categorias1), ...Object.keys(categorias2)]);
        
        // Nomes dos meses
        const meses = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
        
        // Preparar dados para Excel
        const dados = [];
        
        // Cabeçalho
        dados.push(['COMPARATIVO DE PERÍODOS']);
        dados.push([`${meses[parseInt(mes1)]}/${ano1} vs ${meses[parseInt(mes2)]}/${ano2}`]);
        dados.push([]);
        
        // Cabeçalhos das colunas
        dados.push([
            'Categoria',
            `Receitas ${meses[parseInt(mes1)]}/${ano1}`,
            `Despesas ${meses[parseInt(mes1)]}/${ano1}`,
            `Receitas ${meses[parseInt(mes2)]}/${ano2}`,
            `Despesas ${meses[parseInt(mes2)]}/${ano2}`,
            'Variação %'
        ]);
        
        // Dados das categorias
        Array.from(todasCategorias).sort().forEach(cat => {
            const cat1 = categorias1[cat] || { receitas: 0, despesas: 0 };
            const cat2 = categorias2[cat] || { receitas: 0, despesas: 0 };
            const saldoCat1 = cat1.receitas - cat1.despesas;
            const saldoCat2 = cat2.receitas - cat2.despesas;
            const variacao = saldoCat1 !== 0 ? 
                ((saldoCat2 - saldoCat1) / Math.abs(saldoCat1) * 100).toFixed(1) : '0.0';
            
            dados.push([
                cat,
                cat1.receitas,
                cat1.despesas,
                cat2.receitas,
                cat2.despesas,
                parseFloat(variacao)
            ]);
        });
        
        // Linha de total
        dados.push([
            'TOTAL',
            totalReceitas1,
            totalDespesas1,
            totalReceitas2,
            totalDespesas2,
            '-'
        ]);
        
        // Criar planilha
        const ws = XLSX.utils.aoa_to_sheet(dados);
        
        // Definir larguras das colunas
        ws['!cols'] = [
            { wch: 25 },  // Categoria
            { wch: 18 },  // Receitas 1
            { wch: 18 },  // Despesas 1
            { wch: 18 },  // Receitas 2
            { wch: 18 },  // Despesas 2
            { wch: 12 }   // Variação
        ];
        
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Comparativo');
        
        // Gerar arquivo
        XLSX.writeFile(wb, `comparativo_${meses[parseInt(mes1)]}_${ano1}_vs_${meses[parseInt(mes2)]}_${ano2}.xlsx`);
        
    } catch (error) {
        console.error('Erro ao exportar Excel:', error);
        alert('Erro ao gerar Excel do comparativo.');
    }
}

window.carregarComparativoPeriodos = carregarComparativoPeriodos;
window.exportarComparativoPDF = exportarComparativoPDF;
window.exportarComparativoExcel = exportarComparativoExcel;

// Função para gerar DRE
async function gerarDRE() {
    try {
        // Obter filtros do período
        const ano = document.getElementById('filter-ano-fluxo').value;
        const mes = document.getElementById('filter-mes-fluxo').value;
        const dataInicial = document.getElementById('filter-data-inicial-fluxo').value;
        const dataFinal = document.getElementById('filter-data-final-fluxo').value;
        
        // Determinar período
        let data_inicio, data_fim, periodoTexto;
        
        if (dataInicial && dataFinal) {
            data_inicio = dataInicial;
            data_fim = dataFinal;
            periodoTexto = `${new Date(dataInicial).toLocaleDateString('pt-BR')} a ${new Date(dataFinal).toLocaleDateString('pt-BR')}`;
        } else if (ano && ano.trim() !== '' && mes && mes.trim() !== '') {
            const anoNum = parseInt(ano);
            const mesNum = parseInt(mes);
            const mesPadded = mes.length === 1 ? '0' + mes : mes;
            const ultimoDia = new Date(anoNum, mesNum, 0).getDate();
            const diaPadded = String(ultimoDia).padStart(2, '0');
            data_inicio = `${anoNum}-${mesPadded}-01`;
            data_fim = `${anoNum}-${mesPadded}-${diaPadded}`;
            const mesNome = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][mesNum];
            periodoTexto = `${mesNome}/${ano}`;
        } else if (ano && ano.trim() !== '') {
            data_inicio = `${ano}-01-01`;
            data_fim = `${ano}-12-31`;
            periodoTexto = `Ano de ${ano}`;
        } else if (mes && mes.trim() !== '') {
            const hoje = new Date();
            const anoAtual = hoje.getFullYear();
            const mesNum = parseInt(mes);
            const mesPadded = mes.length === 1 ? '0' + mes : mes;
            const ultimoDia = new Date(anoAtual, mesNum, 0).getDate();
            const diaPadded = String(ultimoDia).padStart(2, '0');
            data_inicio = `${anoAtual}-${mesPadded}-01`;
            data_fim = `${anoAtual}-${mesPadded}-${diaPadded}`;
            const mesNome = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][mesNum];
            periodoTexto = `${mesNome}/${anoAtual}`;
        } else {
            const hoje = new Date();
            const anoAtual = hoje.getFullYear();
            const mesAtual = hoje.getMonth() + 1;
            const mesPadded = String(mesAtual).padStart(2, '0');
            const ultimoDia = new Date(anoAtual, mesAtual, 0).getDate();
            const diaPadded = String(ultimoDia).padStart(2, '0');
            data_inicio = `${anoAtual}-${mesPadded}-01`;
            data_fim = `${anoAtual}-${mesPadded}-${diaPadded}`;
            const mesNome = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][mesAtual - 1];
            periodoTexto = `${mesNome}/${anoAtual}`;
        }
        
        // Buscar lançamentos liquidados
        const response = await fetch(`/api/relatorios/fluxo-caixa?data_inicio=${data_inicio}&data_fim=${data_fim}`);
        const lancamentos = await response.json();
        
        // Agrupar por categoria (estrutura simples)
        const receitas = {};
        const despesas = {};
        let totalReceitas = 0;
        let totalDespesas = 0;
        
        lancamentos.forEach(l => {
            // Ignorar transferências bancárias no DRE (não afetam resultado)
            const tipoLower = (l.tipo || '').toLowerCase();
            const descricao = (l.descricao || '').toLowerCase();
            const categoria = (l.categoria || '').toLowerCase();
            
            // Identificar transferências por tipo, descrição ou categoria
            if (tipoLower === 'transferencia' || 
                tipoLower === 'transferência' ||
                descricao.includes('(saída)') || 
                descricao.includes('(entrada)') ||
                categoria.includes('transferência') ||
                categoria.includes('transferencia')) {
                return; // Pular transferências
            }
            
            const categoriaOriginal = l.categoria || 'Não Categorizado';
            const subcategoria = l.subcategoria || 'Geral';
            const valor = parseFloat(l.valor || 0);
            
            if (tipoLower === 'receita') {
                if (!receitas[categoriaOriginal]) {
                    receitas[categoriaOriginal] = { total: 0, subcategorias: {} };
                }
                if (!receitas[categoriaOriginal].subcategorias[subcategoria]) {
                    receitas[categoriaOriginal].subcategorias[subcategoria] = 0;
                }
                receitas[categoriaOriginal].subcategorias[subcategoria] += valor;
                receitas[categoriaOriginal].total += valor;
                totalReceitas += valor;
            } else if (tipoLower === 'despesa') {
                if (!despesas[categoriaOriginal]) {
                    despesas[categoriaOriginal] = { total: 0, subcategorias: {} };
                }
                if (!despesas[categoriaOriginal].subcategorias[subcategoria]) {
                    despesas[categoriaOriginal].subcategorias[subcategoria] = 0;
                }
                despesas[categoriaOriginal].subcategorias[subcategoria] += valor;
                despesas[categoriaOriginal].total += valor;
                totalDespesas += valor;
            }
        });
        
        // Cálculos simples
        const lucroLiquido = totalReceitas - totalDespesas;
        const margemLiquida = totalReceitas > 0 ? (lucroLiquido / totalReceitas * 100) : 0;
        
        // Gerar HTML do DRE
        const dataAtual = new Date().toLocaleDateString('pt-BR');
        
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>DRE - ${periodoTexto}</title>
                <style>
                    @page { size: portrait; margin: 12mm; }
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { 
                        font-family: 'Segoe UI', 'Arial', sans-serif; 
                        padding: 20px 30px; 
                        background: white;
                        color: #1a252f;
                        line-height: 1.5;
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 35px;
                        padding: 25px;
                        background: #2c3e50;
                        border-radius: 8px;
                        border: 3px solid #1a252f;
                    }
                    .header h1 {
                        color: white;
                        font-size: 22px;
                        font-weight: 700;
                        margin-bottom: 10px;
                        letter-spacing: 2.5px;
                        text-transform: uppercase;
                    }
                    .header .subtitle {
                        color: #ecf0f1;
                        font-size: 13px;
                        margin-top: 6px;
                        font-weight: 600;
                        letter-spacing: 1px;
                    }
                    .valor-positivo {
                        color: #27ae60 !important;
                        font-weight: 700;
                    }
                    .valor-negativo {
                        color: #e74c3c !important;
                        font-weight: 700;
                    }
                    .info-box {
                        background: white;
                        padding: 15px 20px;
                        margin-bottom: 30px;
                        display: flex;
                        justify-content: space-between;
                        border: 1px solid #d0d0d0;
                        border-radius: 0;
                    }
                    .info-item {
                        font-size: 11px;
                    }
                    .info-label {
                        color: #666;
                        font-weight: 600;
                        text-transform: uppercase;
                        font-size: 10px;
                        letter-spacing: 0.5px;
                    }
                    .info-value {
                        color: #1a1a1a;
                        font-weight: 700;
                        font-size: 12px;
                        margin-top: 3px;
                    }
                    .secao {
                        margin-bottom: 30px;
                        page-break-inside: avoid;
                        border-radius: 6px;
                        overflow: hidden;
                        border: 2px solid #34495e;
                    }
                    .secao-titulo {
                        background: #34495e;
                        color: white;
                        padding: 12px 20px;
                        font-weight: 700;
                        font-size: 13px;
                        margin-bottom: 0;
                        letter-spacing: 1.5px;
                    }
                    .categoria {
                        background: #f8f9fa;
                        padding: 12px 20px;
                        font-weight: 700;
                        margin-bottom: 0;
                        display: flex;
                        justify-content: space-between;
                        border-left: 4px solid #3498db;
                        border-bottom: 1px solid #d5d8dc;
                        font-size: 12px;
                        color: #1a252f;
                    }
                    .subcategoria {
                        padding: 10px 25px 10px 50px;
                        display: flex;
                        justify-content: space-between;
                        font-size: 11px;
                        color: #2c3e50;
                        border-bottom: 1px solid #f0f0f0;
                        background: white;
                    }
                    .subcategoria:last-of-type {
                        border-bottom: 2px solid #d5d8dc;
                    }
                    .total-secao {
                        background: #2c3e50;
                        color: white;
                        padding: 14px 20px;
                        font-weight: 700;
                        display: flex;
                        justify-content: space-between;
                        font-size: 13px;
                        letter-spacing: 0.8px;
                    }
                    .resultado-liquido {
                        display: flex;
                        align-items: center;
                        gap: 15px;
                        padding: 18px 25px;
                        margin: 30px 0 25px 0;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        border: 2px solid;
                        background: white;
                    }
                    .resultado-liquido.lucro {
                        border-color: #28a745;
                        color: #155724;
                    }
                    .resultado-liquido.prejuizo {
                        border-color: #dc3545;
                        color: #721c24;
                    }
                    .resultado-icone {
                        font-size: 28px;
                        font-weight: 700;
                        line-height: 1;
                    }
                    .resultado-conteudo {
                        flex: 1;
                    }
                    .resultado-label {
                        font-size: 11px;
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        margin-bottom: 5px;
                        opacity: 0.7;
                    }
                    .resultado-valor {
                        font-size: 20px;
                        font-weight: 700;
                        margin-bottom: 3px;
                    }
                    .resultado-margem {
                        font-size: 11px;
                        font-weight: 500;
                        opacity: 0.6;
                    }
                    .indicadores {
                        display: grid;
                        grid-template-columns: repeat(3, 1fr);
                        gap: 20px;
                        margin-top: 35px;
                    }
                    .indicador {
                        background: white;
                        padding: 16px;
                        border: 2px solid #d5d8dc;
                        border-radius: 6px;
                        text-align: center;
                    }
                    .indicador-label {
                        font-size: 11px;
                        color: #7f8c8d;
                        margin-bottom: 10px;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        font-weight: 700;
                    }
                    .indicador-valor {
                        font-size: 20px;
                        font-weight: 700;
                        color: #2c3e50;
                        margin-bottom: 5px;
                    }
                    .indicador-detalhe {
                        font-size: 10px;
                        color: #95a5a6;
                        font-weight: 500;
                        margin-top: 4px;
                        font-weight: 500;
                    }
                    .rodape {
                        margin-top: 40px;
                        padding: 15px;
                        border-top: 2px solid #bdc3c7;
                        text-align: center;
                        color: #7f8c8d;
                        font-size: 9px;
                        letter-spacing: 0.5px;
                        background: #f8f9fa;
                        border-radius: 4px;
                        font-weight: 500;
                    }
                    .rodape p {
                        margin: 3px 0;
                    }
                    @media print {
                        body { padding: 15px; background: white; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        .secao { page-break-inside: avoid; margin-bottom: 20px; }
                        .header { page-break-after: avoid; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        .resultado-liquido { page-break-before: avoid; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        .secao-titulo { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        .total-secao { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        .indicador { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        .categoria { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        .rodape { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                        .indicadores { page-break-inside: avoid; }
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Demonstração do Resultado do Exercício</h1>
                    <div class="subtitle">${periodoTexto}</div>
                </div>
                
                <!-- RECEITAS OPERACIONAIS -->
                <div class="secao">
                    <div class="secao-titulo">RECEITAS OPERACIONAIS</div>
                    ${Object.keys(receitas).sort((a, b) => receitas[b].total - receitas[a].total).map(categoria => `
                        <div class="categoria">
                            <span>${categoria}</span>
                            <span class="valor-positivo">R$ ${receitas[categoria].total.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
                        </div>
                        ${Object.keys(receitas[categoria].subcategorias).map(sub => `
                            <div class="subcategoria">
                                <span>${sub}</span>
                                <span>R$ ${receitas[categoria].subcategorias[sub].toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
                            </div>
                        `).join('')}
                    `).join('')}
                    <div class="total-secao">
                        <span>Total de Receitas</span>
                        <span class="valor-positivo">R$ ${totalReceitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
                    </div>
                </div>
                
                <!-- DESPESAS OPERACIONAIS -->
                <div class="secao">
                    <div class="secao-titulo">DESPESAS OPERACIONAIS</div>
                    ${Object.keys(despesas).sort((a, b) => despesas[b].total - despesas[a].total).map(categoria => `
                        <div class="categoria">
                            <span>${categoria}</span>
                            <span class="valor-negativo">R$ ${despesas[categoria].total.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
                        </div>
                        ${Object.keys(despesas[categoria].subcategorias).map(sub => `
                            <div class="subcategoria">
                                <span>${sub}</span>
                                <span>R$ ${despesas[categoria].subcategorias[sub].toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
                            </div>
                        `).join('')}
                    `).join('')}
                    <div class="total-secao">
                        <span>Total de Despesas</span>
                        <span class="valor-negativo">R$ ${totalDespesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
                    </div>
                </div>
                
                <!-- RESULTADO LÍQUIDO -->
                <div class="resultado-liquido ${lucroLiquido >= 0 ? 'lucro' : 'prejuizo'}">
                    <div class="resultado-icone">${lucroLiquido >= 0 ? '✓' : '✗'}</div>
                    <div class="resultado-conteudo">
                        <div class="resultado-label">${lucroLiquido >= 0 ? 'Lucro Líquido' : 'Prejuízo Líquido'}</div>
                        <div class="resultado-valor">R$ ${Math.abs(lucroLiquido).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div class="resultado-margem">Margem: ${margemLiquida.toFixed(1)}%</div>
                    </div>
                </div>
                
                <!-- INDICADORES FINANCEIROS -->
                <div class="indicadores">
                    <div class="indicador">
                        <div class="indicador-label">Receita Total</div>
                        <div class="indicador-valor valor-positivo">R$ ${totalReceitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div class="indicador-detalhe">${lancamentos.filter(l => l.tipo.toLowerCase() === 'receita').length} transações</div>
                    </div>
                    <div class="indicador">
                        <div class="indicador-label">Despesa Total</div>
                        <div class="indicador-valor valor-negativo">R$ ${totalDespesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div class="indicador-detalhe">${lancamentos.filter(l => l.tipo.toLowerCase() === 'despesa').length} transações</div>
                    </div>
                    <div class="indicador">
                        <div class="indicador-label">Margem Líquida</div>
                        <div class="indicador-valor" style="color: ${margemLiquida >= 0 ? '#27ae60' : '#e74c3c'};">${margemLiquida.toFixed(1)}%</div>
                        <div class="indicador-detalhe">${margemLiquida >= 0 ? 'Rentabilidade' : 'Déficit'}</div>
                    </div>
                </div>
                
                <div class="rodape">
                    <p>Demonstração do Resultado do Exercício (DRE)</p>
                    <p>Sistema de Gestão Financeira • Emitido em ${dataAtual}</p>
                    <p>Documento gerado automaticamente para fins gerenciais</p>
                </div>
            </body>
            </html>
        `);
        
        printWindow.document.close();
        
        setTimeout(() => {
            printWindow.print();
        }, 500);
        
    } catch (error) {
        console.error('Erro ao gerar DRE:', error);
        alert('Erro ao gerar DRE. Verifique o console para mais detalhes.');
    }
}

window.gerarDRE = gerarDRE;

// Função para exportar DRE para Excel
async function exportarDREExcel() {
    try {
        // Obter os mesmos filtros e dados do DRE
        const ano = document.getElementById('filter-ano-fluxo').value;
        const mes = document.getElementById('filter-mes-fluxo').value;
        const dataInicial = document.getElementById('filter-data-inicial-fluxo').value;
        const dataFinal = document.getElementById('filter-data-final-fluxo').value;
        
        // Determinar período
        let data_inicio, data_fim, periodoTexto;
        
        if (dataInicial && dataFinal) {
            data_inicio = dataInicial;
            data_fim = dataFinal;
            periodoTexto = `${new Date(dataInicial).toLocaleDateString('pt-BR')} a ${new Date(dataFinal).toLocaleDateString('pt-BR')}`;
        } else if (ano && ano.trim() !== '' && mes && mes.trim() !== '') {
            const anoNum = parseInt(ano);
            const mesNum = parseInt(mes);
            const mesPadded = mes.length === 1 ? '0' + mes : mes;
            const ultimoDia = new Date(anoNum, mesNum, 0).getDate();
            data_inicio = `${anoNum}-${mesPadded}-01`;
            data_fim = `${anoNum}-${mesPadded}-${String(ultimoDia).padStart(2, '0')}`;
            const mesNome = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][mesNum];
            periodoTexto = `${mesNome}/${ano}`;
        } else if (ano && ano.trim() !== '') {
            data_inicio = `${ano}-01-01`;
            data_fim = `${ano}-12-31`;
            periodoTexto = `Ano de ${ano}`;
        } else {
            const hoje = new Date();
            const anoAtual = hoje.getFullYear();
            const mesAtual = hoje.getMonth() + 1;
            const mesPadded = String(mesAtual).padStart(2, '0');
            const ultimoDia = new Date(anoAtual, mesAtual, 0).getDate();
            data_inicio = `${anoAtual}-${mesPadded}-01`;
            data_fim = `${anoAtual}-${mesPadded}-${String(ultimoDia).padStart(2, '0')}`;
            const mesNome = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][mesAtual - 1];
            periodoTexto = `${mesNome}/${anoAtual}`;
        }
        
        // Buscar lançamentos
        const response = await fetch(`/api/relatorios/fluxo-caixa?data_inicio=${data_inicio}&data_fim=${data_fim}`);
        const lancamentos = await response.json();
        
        // Agrupar por categoria (mesma lógica do DRE)
        const receitas = {};
        const despesas = {};
        let totalReceitas = 0;
        let totalDespesas = 0;
        
        lancamentos.forEach(l => {
            const tipoLower = (l.tipo || '').toLowerCase();
            const descricao = (l.descricao || '').toLowerCase();
            const categoria = (l.categoria || '').toLowerCase();
            
            if (tipoLower === 'transferencia' || tipoLower === 'transferência' ||
                descricao.includes('(saída)') || descricao.includes('(entrada)') ||
                categoria.includes('transferência') || categoria.includes('transferencia')) {
                return;
            }
            
            const categoriaOriginal = l.categoria || 'Não Categorizado';
            const subcategoria = l.subcategoria || 'Geral';
            const valor = parseFloat(l.valor || 0);
            
            if (tipoLower === 'receita') {
                if (!receitas[categoriaOriginal]) {
                    receitas[categoriaOriginal] = { total: 0, subcategorias: {} };
                }
                if (!receitas[categoriaOriginal].subcategorias[subcategoria]) {
                    receitas[categoriaOriginal].subcategorias[subcategoria] = 0;
                }
                receitas[categoriaOriginal].subcategorias[subcategoria] += valor;
                receitas[categoriaOriginal].total += valor;
                totalReceitas += valor;
            } else if (tipoLower === 'despesa') {
                if (!despesas[categoriaOriginal]) {
                    despesas[categoriaOriginal] = { total: 0, subcategorias: {} };
                }
                if (!despesas[categoriaOriginal].subcategorias[subcategoria]) {
                    despesas[categoriaOriginal].subcategorias[subcategoria] = 0;
                }
                despesas[categoriaOriginal].subcategorias[subcategoria] += valor;
                despesas[categoriaOriginal].total += valor;
                totalDespesas += valor;
            }
        });
        
        const lucroLiquido = totalReceitas - totalDespesas;
        const margemLiquida = totalReceitas > 0 ? (lucroLiquido / totalReceitas * 100) : 0;
        
        // Criar dados para Excel
        const dados = [];
        
        // Cabeçalho
        dados.push(['DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO']);
        dados.push([`Período: ${periodoTexto}`]);
        dados.push([`Data de Emissão: ${new Date().toLocaleDateString('pt-BR')}`]);
        dados.push([]);
        
        // Receitas
        dados.push(['RECEITAS OPERACIONAIS', '']);
        Object.keys(receitas).sort((a, b) => receitas[b].total - receitas[a].total).forEach(categoria => {
            dados.push([categoria, receitas[categoria].total]);
            Object.keys(receitas[categoria].subcategorias).forEach(sub => {
                dados.push([`  ${sub}`, receitas[categoria].subcategorias[sub]]);
            });
        });
        dados.push(['Total de Receitas', totalReceitas]);
        dados.push([]);
        
        // Despesas
        dados.push(['DESPESAS OPERACIONAIS', '']);
        Object.keys(despesas).sort((a, b) => despesas[b].total - despesas[a].total).forEach(categoria => {
            dados.push([categoria, despesas[categoria].total]);
            Object.keys(despesas[categoria].subcategorias).forEach(sub => {
                dados.push([`  ${sub}`, despesas[categoria].subcategorias[sub]]);
            });
        });
        dados.push(['Total de Despesas', totalDespesas]);
        dados.push([]);
        
        // Resultado
        dados.push([lucroLiquido >= 0 ? 'LUCRO LÍQUIDO' : 'PREJUÍZO LÍQUIDO', Math.abs(lucroLiquido)]);
        dados.push([`Margem Líquida: ${margemLiquida.toFixed(1)}%`, '']);
        dados.push([]);
        
        // Indicadores
        dados.push(['INDICADORES FINANCEIROS', '']);
        dados.push(['Receita Total', totalReceitas]);
        dados.push(['Despesa Total', totalDespesas]);
        dados.push(['Margem Líquida', `${margemLiquida.toFixed(1)}%`]);
        
        // Criar workbook
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.aoa_to_sheet(dados);
        
        // Ajustar largura das colunas
        ws['!cols'] = [
            { wch: 40 },
            { wch: 15 }
        ];
        
        XLSX.utils.book_append_sheet(wb, ws, 'DRE');
        
        // Salvar arquivo
        const nomeArquivo = `DRE_${periodoTexto.replace(/\//g, '-')}_${new Date().toISOString().split('T')[0]}.xlsx`;
        XLSX.writeFile(wb, nomeArquivo);
        
    } catch (error) {
        console.error('Erro ao exportar DRE para Excel:', error);
        alert('Erro ao exportar DRE. Verifique o console para mais detalhes.');
    }
}

window.exportarDREExcel = exportarDREExcel;

// Função para exportar Contas a Pagar em PDF
async function exportarContasPagarPDF() {
    try {
        // Obter filtros aplicados
        const statusFiltro = document.getElementById('filter-status-pagar').value;
        const categoriaFiltro = document.getElementById('filter-categoria-pagar').value;
        const fornecedorFiltro = document.getElementById('filter-fornecedor').value;
        const anoFiltro = document.getElementById('filter-ano-pagar').value;
        const mesFiltro = document.getElementById('filter-mes-pagar').value;
        const dataInicioFiltro = document.getElementById('filter-data-inicio-pagar').value;
        const dataFimFiltro = document.getElementById('filter-data-fim-pagar').value;
        
        // Buscar todos os lançamentos de despesa
        const response = await fetch('/api/lancamentos?tipo=despesa');
        const todosLancamentos = await response.json();
        
        // Aplicar os mesmos filtros da tela
        const lancamentosFiltrados = todosLancamentos.filter(l => {
            if (statusFiltro && l.status !== statusFiltro) return false;
            if (categoriaFiltro && l.categoria !== categoriaFiltro) return false;
            if (fornecedorFiltro && l.pessoa !== fornecedorFiltro) return false;
            
            const dataVenc = new Date(l.data_vencimento);
            
            if (dataInicioFiltro && dataFimFiltro) {
                const inicio = new Date(dataInicioFiltro);
                const fim = new Date(dataFimFiltro);
                if (dataVenc < inicio || dataVenc > fim) return false;
            } else if (anoFiltro && mesFiltro) {
                if (dataVenc.getFullYear() !== parseInt(anoFiltro) || (dataVenc.getMonth() + 1) !== parseInt(mesFiltro)) return false;
            } else if (anoFiltro) {
                if (dataVenc.getFullYear() !== parseInt(anoFiltro)) return false;
            } else if (mesFiltro) {
                if ((dataVenc.getMonth() + 1) !== parseInt(mesFiltro)) return false;
            }
            
            return true;
        });
        
        // Ordenar por data de vencimento (mais antigas primeiro)
        lancamentosFiltrados.sort((a, b) => new Date(a.data_vencimento) - new Date(b.data_vencimento));
        
        // Determinar título e subtítulo
        const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
        let periodo = '';
        let filtrosAplicados = [];
        
        if (dataInicioFiltro && dataFimFiltro) {
            periodo = `Período: ${new Date(dataInicioFiltro).toLocaleDateString('pt-BR')} a ${new Date(dataFimFiltro).toLocaleDateString('pt-BR')}`;
        } else if (anoFiltro && mesFiltro) {
            periodo = `Período: ${meses[parseInt(mesFiltro) - 1]}/${anoFiltro}`;
        } else if (anoFiltro) {
            periodo = `Período: Ano ${anoFiltro}`;
        } else if (mesFiltro) {
            periodo = `Período: ${meses[parseInt(mesFiltro) - 1]}`;
        } else {
            periodo = 'Período: Todos';
        }
        
        if (statusFiltro) filtrosAplicados.push(`Status: ${statusFiltro}`);
        if (categoriaFiltro) filtrosAplicados.push(`Categoria: ${categoriaFiltro}`);
        if (fornecedorFiltro) filtrosAplicados.push(`Fornecedor: ${fornecedorFiltro}`);
        
        const subtitulo = filtrosAplicados.length > 0 ? filtrosAplicados.join(' | ') : '';
        
        // Gerar PDF
        const printWindow = window.open('', '_blank');
        if (!printWindow) {
            alert('Erro: Pop-up bloqueado. Permita pop-ups para este site.');
            return;
        }
        
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Contas a Pagar - ${new Date().toLocaleDateString('pt-BR')}</title>
                <style>
                    @page { 
                        size: landscape; 
                        margin: 15mm 10mm; 
                    }
                    * { 
                        margin: 0; 
                        padding: 0; 
                        box-sizing: border-box; 
                    }
                    body { 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                        font-size: 10pt;
                        color: #333;
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 20px;
                        border-bottom: 3px solid #2c3e50;
                        padding-bottom: 15px;
                    }
                    .header h1 { 
                        color: #2c3e50; 
                        font-size: 24pt; 
                        font-weight: bold;
                        margin-bottom: 5px;
                    }
                    .header .periodo { 
                        color: #555; 
                        font-size: 11pt; 
                        margin: 5px 0;
                    }
                    .header .filtros { 
                        color: #777; 
                        font-size: 9pt;
                        font-style: italic;
                    }
                    .info-gerado {
                        text-align: right;
                        font-size: 8pt;
                        color: #999;
                        margin-bottom: 10px;
                    }
                    table { 
                        width: 100%; 
                        border-collapse: collapse; 
                        margin-top: 10px;
                    }
                    th { 
                        background: #34495e; 
                        color: white; 
                        padding: 10px 8px; 
                        text-align: left; 
                        font-weight: bold; 
                        font-size: 9pt;
                        border: 1px solid #2c3e50;
                    }
                    td { 
                        padding: 8px; 
                        border: 1px solid #ddd;
                        font-size: 9pt;
                    }
                    tbody tr:nth-child(odd) { 
                        background: #f9f9f9; 
                    }
                    tbody tr:hover { 
                        background: #f0f0f0; 
                    }
                    .valor-col { 
                        text-align: right; 
                        font-weight: 500;
                    }
                    .status-PENDENTE { 
                        color: #e74c3c; 
                        font-weight: bold; 
                    }
                    .status-PAGO { 
                        color: #27ae60; 
                        font-weight: bold; 
                    }
                    .status-CANCELADO { 
                        color: #95a5a6; 
                        font-weight: bold; 
                    }
                    .total-row { 
                        font-weight: bold; 
                        background: #ecf0f1 !important;
                        border-top: 2px solid #34495e;
                    }
                    .total-row td {
                        padding: 12px 8px;
                        font-size: 10pt;
                    }
                    .total-geral-row {
                        background: #d5e8d4 !important;
                        border-top: 3px solid #27ae60;
                    }
                    .rodape {
                        margin-top: 20px;
                        text-align: center;
                        font-size: 8pt;
                        color: #999;
                        border-top: 1px solid #ddd;
                        padding-top: 10px;
                    }
                    @media print {
                        body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>CONTAS A PAGAR</h1>
                    <div class="periodo">${periodo}</div>
                    ${subtitulo ? `<div class="filtros">${subtitulo}</div>` : ''}
                </div>
                <div class="info-gerado">
                    Relatório gerado em: ${new Date().toLocaleString('pt-BR')} | Total de registros: ${lancamentosFiltrados.length}
                </div>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 10%;">Data Venc.</th>
                            <th style="width: 18%;">Fornecedor</th>
                            <th style="width: 15%;">Categoria</th>
                            <th style="width: 15%;">Subcategoria</th>
                            <th style="width: 20%;">Descrição</th>
                            <th style="width: 10%;">Valor</th>
                            <th style="width: 8%;">Status</th>
                            <th style="width: 10%;">Data Pgto.</th>
                        </tr>
                    </thead>
                    <tbody>
        `);
        
        let totalPendente = 0;
        let totalPago = 0;
        let totalCancelado = 0;
        
        lancamentos.forEach(l => {
            const dataVenc = new Date(l.data_vencimento).toLocaleDateString('pt-BR');
            const dataPgto = l.data_pagamento ? new Date(l.data_pagamento).toLocaleDateString('pt-BR') : '-';
            const statusClass = l.status === 'PENDENTE' ? 'status-pendente' : l.status === 'PAGO' ? 'status-pago' : 'status-cancelado';
            
            printWindow.document.write(`
                <tr>
                    <td>${dataVenc}</td>
                    <td>${l.pessoa || '-'}</td>
                    <td>${l.categoria || '-'}</td>
                    <td>${l.subcategoria || '-'}</td>
                    <td>${l.descricao || '-'}</td>
                    <td>R$ ${l.valor.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td class="${statusClass}">${l.status}</td>
                    <td>${dataPgto}</td>
                </tr>
            `);
            
            if (l.status === 'PENDENTE') totalPendente += parseFloat(l.valor) || 0;
            else if (l.status === 'PAGO') totalPago += parseFloat(l.valor) || 0;
            else if (l.status === 'CANCELADO') totalCancelado += parseFloat(l.valor) || 0;
        });
        
        const totalGeral = totalPendente + totalPago + totalCancelado;
        
        // Mostrar apenas os totais dos status filtrados
        let totaisHtml = '';
        
        if (status) {
            // Se há filtro de status, mostrar apenas o total daquele status
            if (status === 'PENDENTE') {
                totaisHtml += `
                        <tr class="total">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL PENDENTE:</td>
                            <td style="text-align: left;">R$ ${totalPendente.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>`;
            } else if (status === 'PAGO') {
                totaisHtml += `
                        <tr class="total">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL PAGO:</td>
                            <td style="text-align: left;">R$ ${totalPago.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>`;
            } else if (status === 'CANCELADO') {
                totaisHtml += `
                        <tr class="total">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL CANCELADO:</td>
                            <td style="text-align: left;">R$ ${totalCancelado.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>`;
            }
        } else {
            // Sem filtro: mostrar todos os totais
            totaisHtml += `
                        <tr class="total">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL PENDENTE:</td>
                            <td style="text-align: left;">R$ ${totalPendente.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>
                        <tr class="total">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL PAGO:</td>
                            <td style="text-align: left;">R$ ${totalPago.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>
                        <tr class="total">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL CANCELADO:</td>
                            <td style="text-align: left;">R$ ${totalCancelado.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>
                        <tr class="total" style="background: #d4edda; font-size: 11px;">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL GERAL:</td>
                            <td style="text-align: left;">R$ ${totalGeral.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>`;
        }
        
        printWindow.document.write(totaisHtml);
        printWindow.document.write(`
                    </tbody>
                </table>
            </body>
            </html>
        `);
        
        printWindow.document.close();
        printWindow.print();
    } catch (error) {
        console.error('Erro ao exportar PDF:', error);
        alert('Erro ao gerar PDF');
    }
}

async function exportarContasReceberPDF() {
    try {
        // Obter filtros
        const status = document.getElementById('filter-status-receber').value;
        const categoria = document.getElementById('filter-categoria-receber').value;
        const cliente = document.getElementById('filter-cliente').value;
        const ano = document.getElementById('filter-ano-receber').value;
        const mes = document.getElementById('filter-mes-receber').value;
        const dataInicio = document.getElementById('filter-data-inicio-receber').value;
        const dataFim = document.getElementById('filter-data-fim-receber').value;
        
        // Buscar lançamentos
        const response = await fetch('/api/lancamentos?tipo=receita');
        let lancamentos = await response.json();
        
        // Aplicar filtros
        lancamentos = lancamentos.filter(l => {
            if (status && l.status !== status) return false;
            if (categoria && l.categoria !== categoria) return false;
            if (cliente && l.pessoa !== cliente) return false;
            
            const dataVenc = new Date(l.data_vencimento);
            
            if (dataInicio && dataFim) {
                const inicio = new Date(dataInicio);
                const fim = new Date(dataFim);
                if (dataVenc < inicio || dataVenc > fim) return false;
            } else if (ano && mes) {
                if (dataVenc.getFullYear() !== parseInt(ano) || (dataVenc.getMonth() + 1) !== parseInt(mes)) return false;
            } else if (ano) {
                if (dataVenc.getFullYear() !== parseInt(ano)) return false;
            } else if (mes) {
                if ((dataVenc.getMonth() + 1) !== parseInt(mes)) return false;
            }
            
            return true;
        });
        
        // Determinar título do período
        let periodo = '';
        if (dataInicio && dataFim) {
            periodo = `${new Date(dataInicio).toLocaleDateString('pt-BR')} a ${new Date(dataFim).toLocaleDateString('pt-BR')}`;
        } else if (ano && mes) {
            const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
            periodo = `${meses[parseInt(mes) - 1]}/${ano}`;
        } else if (ano) {
            periodo = `Ano ${ano}`;
        } else if (mes) {
            const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
            periodo = `${meses[parseInt(mes) - 1]}`;
        } else {
            periodo = 'Todos os Períodos';
        }
        
        // Criar janela de impressão
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Contas a Receber - ${periodo}</title>
                <style>
                    @page { size: landscape; margin: 10mm; }
                    body { font-family: Arial, sans-serif; margin: 0; padding: 15px; }
                    h1 { text-align: center; color: #2c3e50; margin-bottom: 5px; font-size: 20px; }
                    h2 { text-align: center; color: #7f8c8d; margin-bottom: 20px; font-size: 14px; font-weight: normal; }
                    table { width: 100%; border-collapse: collapse; font-size: 10px; }
                    th { background: white; color: black; padding: 8px; text-align: left; font-weight: bold; border-bottom: 2px solid #000; }
                    td { padding: 6px 8px; border-bottom: 1px solid #ecf0f1; }
                    tr:nth-child(even) { background: #f8f9fa; }
                    .total { font-weight: bold; background: #e8f4f8; }
                    .status-pendente { color: black; font-weight: bold; }
                    .status-pago { color: black; font-weight: bold; }
                    .status-cancelado { color: black; font-weight: bold; }
                </style>
            </head>
            <body>
                <h1>CONTAS A RECEBER</h1>
                <h2>${periodo}</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Data Venc.</th>
                            <th>Cliente</th>
                            <th>Categoria</th>
                            <th>Subcategoria</th>
                            <th>Descrição</th>
                            <th>Valor</th>
                            <th>Status</th>
                            <th>Data Pgto.</th>
                        </tr>
                    </thead>
                    <tbody>
        `);
        
        let totalPendente = 0;
        let totalPago = 0;
        let totalCancelado = 0;
        
        lancamentos.forEach(l => {
            const dataVenc = new Date(l.data_vencimento).toLocaleDateString('pt-BR');
            const dataPgto = l.data_pagamento ? new Date(l.data_pagamento).toLocaleDateString('pt-BR') : '-';
            const statusClass = l.status === 'PENDENTE' ? 'status-pendente' : l.status === 'PAGO' ? 'status-pago' : 'status-cancelado';
            
            printWindow.document.write(`
                <tr>
                    <td>${dataVenc}</td>
                    <td>${l.pessoa || '-'}</td>
                    <td>${l.categoria || '-'}</td>
                    <td>${l.subcategoria || '-'}</td>
                    <td>${l.descricao || '-'}</td>
                    <td>R$ ${l.valor.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td class="${statusClass}">${l.status}</td>
                    <td>${dataPgto}</td>
                </tr>
            `);
            
            if (l.status === 'PENDENTE') totalPendente += parseFloat(l.valor) || 0;
            else if (l.status === 'PAGO') totalPago += parseFloat(l.valor) || 0;
            else if (l.status === 'CANCELADO') totalCancelado += parseFloat(l.valor) || 0;
        });
        
        const totalGeral = totalPendente + totalPago + totalCancelado;
        
        // Mostrar apenas os totais dos status filtrados
        let totaisHtml = '';
        
        if (status) {
            // Se há filtro de status, mostrar apenas o total daquele status
            if (status === 'PENDENTE') {
                totaisHtml += `
                        <tr class="total">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL PENDENTE:</td>
                            <td style="text-align: left;">R$ ${totalPendente.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>`;
            } else if (status === 'PAGO') {
                totaisHtml += `
                        <tr class="total">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL PAGO:</td>
                            <td style="text-align: left;">R$ ${totalPago.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>`;
            } else if (status === 'CANCELADO') {
                totaisHtml += `
                        <tr class="total">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL CANCELADO:</td>
                            <td style="text-align: left;">R$ ${totalCancelado.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>`;
            }
        } else {
            // Sem filtro: mostrar todos os totais
            totaisHtml += `
                        <tr class="total">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL PENDENTE:</td>
                            <td style="text-align: left;">R$ ${totalPendente.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>
                        <tr class="total">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL PAGO:</td>
                            <td style="text-align: left;">R$ ${totalPago.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>
                        <tr class="total">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL CANCELADO:</td>
                            <td style="text-align: left;">R$ ${totalCancelado.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>
                        <tr class="total" style="background: #d4edda; font-size: 11px;">
                            <td colspan="7" style="text-align: right; padding-right: 20px;">TOTAL GERAL:</td>
                            <td style="text-align: left;">R$ ${totalGeral.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>`;
        }
        
        printWindow.document.write(totaisHtml);
        printWindow.document.write(`
                    </tbody>
                </table>
            </body>
            </html>
        `);
        
        printWindow.document.close();
        printWindow.print();
    } catch (error) {
        console.error('Erro ao exportar PDF:', error);
        alert('Erro ao gerar PDF');
    }
}

window.exportarContasPagarPDF = exportarContasPagarPDF;
window.exportarContasReceberPDF = exportarContasReceberPDF;

// === FUNÇÕES DO DASHBOARD ===

async function carregarDashboard() {
    console.log('Carregando dashboard...');
    
    try {
        // Obter filtros
        const ano = document.getElementById('filter-ano-dashboard')?.value || new Date().getFullYear();
        const mes = document.getElementById('filter-mes-dashboard')?.value || '';
        
        // Definir período baseado nos filtros
        let dataInicio, dataFim;
        
        if (mes) {
            // Mês específico
            dataInicio = `${ano}-${mes.padStart(2, '0')}-01`;
            const ultimoDia = new Date(ano, parseInt(mes), 0).getDate();
            dataFim = `${ano}-${mes.padStart(2, '0')}-${ultimoDia}`;
        } else {
            // Ano inteiro
            dataInicio = `${ano}-01-01`;
            dataFim = `${ano}-12-31`;
        }
        
        // Buscar lançamentos do período
        const [receitas, despesas] = await Promise.all([
            fetch(`/api/lancamentos?tipo=RECEITA&data_inicio=${dataInicio}&data_fim=${dataFim}`).then(r => r.json()),
            fetch(`/api/lancamentos?tipo=DESPESA&data_inicio=${dataInicio}&data_fim=${dataFim}`).then(r => r.json())
        ]);
        
        console.log(`📊 Dashboard: ${receitas.length} receitas, ${despesas.length} despesas`);
        
        // Atualizar gráfico
        atualizarGraficoCrescimento(receitas, despesas, ano, mes);
        
        // Atualizar análises detalhadas se a função existir
        if (typeof atualizarAnalisesDetalhadas === 'function') {
            atualizarAnalisesDetalhadas(receitas, despesas);
        }
        
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
        showToast('Erro ao carregar dados do dashboard', 'error');
    }
}

function atualizarGraficoCrescimento(receitas, despesas, ano, mes) {
    const canvas = document.getElementById('grafico-crescimento');
    if (!canvas) {
        console.log('Canvas do gráfico não encontrado');
        return;
    }
    
    // Preparar dados mensais
    const meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    const dadosReceitas = new Array(12).fill(0);
    const dadosDespesas = new Array(12).fill(0);
    
    // Agrupar receitas por mês
    receitas.forEach(r => {
        if (r.status === 'pago' || r.status === 'PAGO') {
            const data = new Date(r.data_pagamento || r.data_vencimento);
            const mesIndex = data.getMonth();
            dadosReceitas[mesIndex] += parseFloat(r.valor);
        }
    });
    
    // Agrupar despesas por mês
    despesas.forEach(d => {
        if (d.status === 'pago' || d.status === 'PAGO') {
            const data = new Date(d.data_pagamento || d.data_vencimento);
            const mesIndex = data.getMonth();
            dadosDespesas[mesIndex] += parseFloat(d.valor);
        }
    });
    
    // Calcular saldo acumulado
    const saldoAcumulado = [];
    let acumulado = 0;
    for (let i = 0; i < 12; i++) {
        acumulado += dadosReceitas[i] - dadosDespesas[i];
        saldoAcumulado.push(acumulado);
    }
    
    // Se Chart.js não estiver disponível, mostrar mensagem
    if (typeof Chart === 'undefined') {
        canvas.parentElement.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">' +
            '<p style="font-size: 16px; margin-bottom: 10px;">📊 Gráfico de Evolução Financeira</p>' +
            '<p style="font-size: 14px;">Receitas: R$ ' + dadosReceitas.reduce((a, b) => a + b, 0).toLocaleString('pt-BR', {minimumFractionDigits: 2}) + '</p>' +
            '<p style="font-size: 14px;">Despesas: R$ ' + dadosDespesas.reduce((a, b) => a + b, 0).toLocaleString('pt-BR', {minimumFractionDigits: 2}) + '</p>' +
            '<p style="font-size: 14px; font-weight: bold; color: ' + (acumulado >= 0 ? '#27ae60' : '#e74c3c') + ';">Saldo: R$ ' + acumulado.toLocaleString('pt-BR', {minimumFractionDigits: 2}) + '</p>' +
            '</div>';
        return;
    }
    
    // Destruir gráfico anterior se existir
    if (window.graficoCrescimento) {
        window.graficoCrescimento.destroy();
    }
    
    // Criar novo gráfico
    const ctx = canvas.getContext('2d');
    window.graficoCrescimento = new Chart(ctx, {
        type: 'line',
        data: {
            labels: meses,
            datasets: [{
                label: 'Receitas',
                data: dadosReceitas,
                borderColor: '#27ae60',
                backgroundColor: 'rgba(39, 174, 96, 0.1)',
                tension: 0.4
            }, {
                label: 'Despesas',
                data: dadosDespesas,
                borderColor: '#e74c3c',
                backgroundColor: 'rgba(231, 76, 60, 0.1)',
                tension: 0.4
            }, {
                label: 'Saldo Acumulado',
                data: saldoAcumulado,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: `Evolução Financeira - ${ano}`
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toLocaleString('pt-BR');
                        }
                    }
                }
            }
        }
    });
    
    console.log('✅ Gráfico atualizado com sucesso');
}

async function carregarIndicadores() {
    console.log('Carregando indicadores...');
    
    try {
        // Obter período selecionado
        const periodoSelect = document.getElementById('filter-periodo-indicadores');
        const periodo = periodoSelect ? periodoSelect.value : '365';
        
        console.log('📅 Período selecionado:', periodo);
        
        // Calcular data inicial baseada no período
        const dataFim = new Date();
        const dataInicio = new Date();
        
        if (periodo === 'custom') {
            const dataInicioInput = document.getElementById('filter-data-inicio-indicadores');
            const dataFimInput = document.getElementById('filter-data-fim-indicadores');
            if (dataInicioInput && dataFimInput) {
                dataInicio.setTime(new Date(dataInicioInput.value).getTime());
                dataFim.setTime(new Date(dataFimInput.value).getTime());
            }
        } else {
            dataInicio.setDate(dataFim.getDate() - parseInt(periodo));
        }
        
        console.log('📅 Data início:', dataInicio.toLocaleDateString('pt-BR'));
        console.log('📅 Data fim:', dataFim.toLocaleDateString('pt-BR'));
        
        // Buscar lançamentos
        const response = await fetch('/api/lancamentos');
        const lancamentos = await response.json();
        
        console.log('📦 Total de lançamentos:', lancamentos.length);
        
        // Filtrar por período
        const lancamentosFiltrados = lancamentos.filter(l => {
            const dataLanc = new Date(l.data_vencimento);
            return dataLanc >= dataInicio && dataLanc <= dataFim;
        });
        
        console.log('📦 Lançamentos filtrados:', lancamentosFiltrados.length);
        
        // Debug: mostrar amostra de lançamentos
        if (lancamentosFiltrados.length > 0) {
            console.log('🔍 Amostra de lançamento:', lancamentosFiltrados[0]);
            console.log('🔍 Tipos encontrados:', [...new Set(lancamentosFiltrados.map(l => l.tipo))]);
        }
        
        // Calcular indicadores (comparar em minúsculas)
        const receitas = lancamentosFiltrados.filter(l => l.tipo && l.tipo.toLowerCase() === 'receita');
        const despesas = lancamentosFiltrados.filter(l => l.tipo && l.tipo.toLowerCase() === 'despesa');
        
        console.log('💰 Receitas:', receitas.length);
        console.log('💸 Despesas:', despesas.length);
        
        const totalReceitas = receitas.reduce((sum, l) => sum + (l.valor || 0), 0);
        const totalDespesas = despesas.reduce((sum, l) => sum + (l.valor || 0), 0);
        const saldoPeriodo = totalReceitas - totalDespesas;
        
        console.log('💰 Total Receitas: R$', totalReceitas.toFixed(2));
        console.log('💸 Total Despesas: R$', totalDespesas.toFixed(2));
        console.log('💵 Saldo: R$', saldoPeriodo.toFixed(2));
        
        const receitasRecebidas = receitas.filter(l => l.status && l.status.toLowerCase() === 'pago');
        const despesasPagas = despesas.filter(l => l.status && l.status.toLowerCase() === 'pago');
        
        const totalReceitasRecebidas = receitasRecebidas.reduce((sum, l) => sum + (l.valor || 0), 0);
        const totalDespesasPagas = despesasPagas.reduce((sum, l) => sum + (l.valor || 0), 0);
        
        const receitasPendentes = receitas.filter(l => l.status && l.status.toLowerCase() === 'pendente');
        const despesasPendentes = despesas.filter(l => l.status && l.status.toLowerCase() === 'pendente');
        
        const totalReceitasPendentes = receitasPendentes.reduce((sum, l) => sum + (l.valor || 0), 0);
        const totalDespesasPendentes = despesasPendentes.reduce((sum, l) => sum + (l.valor || 0), 0);
        
        // Taxa de recebimento
        const taxaRecebimento = receitas.length > 0 ? (receitasRecebidas.length / receitas.length * 100) : 0;
        const taxaPagamento = despesas.length > 0 ? (despesasPagas.length / despesas.length * 100) : 0;
        
        // Ticket médio
        const ticketMedioReceita = receitas.length > 0 ? totalReceitas / receitas.length : 0;
        const ticketMedioDespesa = despesas.length > 0 ? totalDespesas / despesas.length : 0;
        
        // Renderizar HTML
        const content = document.getElementById('indicadores-content');
        content.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">💰 Total Receitas</div>
                    <div style="font-size: 28px; font-weight: bold;">R$ ${totalReceitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    <div style="font-size: 12px; opacity: 0.8; margin-top: 8px;">${receitas.length} lançamentos</div>
                </div>
                
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">💸 Total Despesas</div>
                    <div style="font-size: 28px; font-weight: bold;">R$ ${totalDespesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    <div style="font-size: 12px; opacity: 0.8; margin-top: 8px;">${despesas.length} lançamentos</div>
                </div>
                
                <div style="background: linear-gradient(135deg, ${saldoPeriodo >= 0 ? '#11998e 0%, #38ef7d' : '#ee0979 0%, #ff6a00'} 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">${saldoPeriodo >= 0 ? '✅' : '⚠️'} Saldo do Período</div>
                    <div style="font-size: 28px; font-weight: bold;">R$ ${saldoPeriodo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    <div style="font-size: 12px; opacity: 0.8; margin-top: 8px;">${((totalReceitas / (totalDespesas || 1)) * 100).toFixed(1)}% de margem</div>
                </div>
                
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">📊 Ticket Médio Receita</div>
                    <div style="font-size: 28px; font-weight: bold;">R$ ${ticketMedioReceita.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    <div style="font-size: 12px; opacity: 0.8; margin-top: 8px;">Por lançamento</div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">
                <div style="background: white; padding: 20px; border-radius: 12px; border: 2px solid #27ae60; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                    <div style="font-size: 14px; color: #27ae60; margin-bottom: 8px; font-weight: 600;">✅ Receitas Recebidas</div>
                    <div style="font-size: 24px; font-weight: bold; color: #27ae60;">R$ ${totalReceitasRecebidas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 8px;">${receitasRecebidas.length} de ${receitas.length} (${taxaRecebimento.toFixed(1)}%)</div>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 12px; border: 2px solid #e74c3c; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                    <div style="font-size: 14px; color: #e74c3c; margin-bottom: 8px; font-weight: 600;">✅ Despesas Pagas</div>
                    <div style="font-size: 24px; font-weight: bold; color: #e74c3c;">R$ ${totalDespesasPagas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 8px;">${despesasPagas.length} de ${despesas.length} (${taxaPagamento.toFixed(1)}%)</div>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 12px; border: 2px solid #f39c12; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                    <div style="font-size: 14px; color: #f39c12; margin-bottom: 8px; font-weight: 600;">⏳ Receitas Pendentes</div>
                    <div style="font-size: 24px; font-weight: bold; color: #f39c12;">R$ ${totalReceitasPendentes.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 8px;">${receitasPendentes.length} lançamentos</div>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 12px; border: 2px solid #e67e22; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                    <div style="font-size: 14px; color: #e67e22; margin-bottom: 8px; font-weight: 600;">⏳ Despesas Pendentes</div>
                    <div style="font-size: 24px; font-weight: bold; color: #e67e22;">R$ ${totalDespesasPendentes.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 8px;">${despesasPendentes.length} lançamentos</div>
                </div>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-top: 30px;">
                <h3 style="margin: 0 0 20px 0; color: #2c3e50;">📈 Distribuição Receitas vs Despesas</h3>
                <canvas id="chart-indicadores" style="max-height: 400px;"></canvas>
            </div>
        `;
        
        // Criar gráfico
        const ctx = document.getElementById('chart-indicadores');
        if (ctx) {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Receitas', 'Despesas'],
                    datasets: [{
                        data: [totalReceitas, totalDespesas],
                        backgroundColor: [
                            'rgba(102, 126, 234, 0.8)',
                            'rgba(231, 76, 60, 0.8)'
                        ],
                        borderColor: [
                            'rgba(102, 126, 234, 1)',
                            'rgba(231, 76, 60, 1)'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Distribuição de Receitas e Despesas'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: R$ ${value.toLocaleString('pt-BR', {minimumFractionDigits: 2})} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
            
            console.log('✅ Gráfico de indicadores criado com sucesso');
        }
        
    } catch (error) {
        console.error('❌ Erro ao carregar indicadores:', error);
        document.getElementById('indicadores-content').innerHTML = `
            <div style="text-align: center; padding: 40px; color: #e74c3c;">
                <p>❌ Erro ao carregar indicadores</p>
                <p style="font-size: 14px;">${error.message}</p>
            </div>
        `;
    }
}

function aplicarFiltroPeriodoIndicadores() {
    console.log('Aplicando filtro de período...');
    
    // Mostrar/ocultar campos de data personalizada
    const periodo = document.getElementById('filter-periodo-indicadores').value;
    const divInicio = document.getElementById('filtro-data-inicio-indicadores');
    const divFim = document.getElementById('filtro-data-fim-indicadores');
    
    if (periodo === 'custom') {
        if (divInicio) divInicio.style.display = 'block';
        if (divFim) divFim.style.display = 'block';
    } else {
        if (divInicio) divInicio.style.display = 'none';
        if (divFim) divFim.style.display = 'none';
        carregarIndicadores();
    }
}

function exportarIndicadoresPDF() {
    console.log('Exportando indicadores em PDF...');
    alert('Funcionalidade de exportação PDF em desenvolvimento');
}

function exportarIndicadoresExcel() {
    console.log('Exportando indicadores em Excel...');
    alert('Funcionalidade de exportação Excel em desenvolvimento');
}

async function carregarInadimplencia() {
    console.log('Carregando inadimplência...');
    
    try {
        const response = await fetch('/api/lancamentos');
        const lancamentos = await response.json();
        
        const hoje = new Date();
        hoje.setHours(0, 0, 0, 0);
        
        // Filtrar lançamentos vencidos e pendentes
        const inadimplentes = lancamentos.filter(l => {
            if (!l.status || l.status.toLowerCase() !== 'pendente') return false;
            if (!l.tipo || l.tipo.toLowerCase() !== 'receita') return false;
            
            const dataVenc = new Date(l.data_vencimento);
            return dataVenc < hoje;
        });
        
        console.log('📊 Total inadimplentes:', inadimplentes.length);
        
        // Calcular valores
        const totalInadimplente = inadimplentes.reduce((sum, l) => sum + (l.valor || 0), 0);
        
        // Agrupar por dias de atraso
        const atrasos = {
            '0-30': [],
            '31-60': [],
            '61-90': [],
            '90+': []
        };
        
        inadimplentes.forEach(l => {
            const dataVenc = new Date(l.data_vencimento);
            const diasAtraso = Math.floor((hoje - dataVenc) / (1000 * 60 * 60 * 24));
            
            if (diasAtraso <= 30) atrasos['0-30'].push(l);
            else if (diasAtraso <= 60) atrasos['31-60'].push(l);
            else if (diasAtraso <= 90) atrasos['61-90'].push(l);
            else atrasos['90+'].push(l);
        });
        
        // Renderizar HTML
        const content = document.getElementById('inadimplencia-content');
        content.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">
                <div style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">⚠️ Total Inadimplente</div>
                    <div style="font-size: 28px; font-weight: bold;">R$ ${totalInadimplente.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    <div style="font-size: 12px; opacity: 0.8; margin-top: 8px;">${inadimplentes.length} lançamentos</div>
                </div>
                
                <div style="background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">⏰ 0-30 dias</div>
                    <div style="font-size: 28px; font-weight: bold;">R$ ${atrasos['0-30'].reduce((s, l) => s + l.valor, 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    <div style="font-size: 12px; opacity: 0.8; margin-top: 8px;">${atrasos['0-30'].length} lançamentos</div>
                </div>
                
                <div style="background: linear-gradient(135deg, #e67e22 0%, #d35400 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">⏰ 31-60 dias</div>
                    <div style="font-size: 28px; font-weight: bold;">R$ ${atrasos['31-60'].reduce((s, l) => s + l.valor, 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    <div style="font-size: 12px; opacity: 0.8; margin-top: 8px;">${atrasos['31-60'].length} lançamentos</div>
                </div>
                
                <div style="background: linear-gradient(135deg, #c0392b 0%, #8e44ad 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">🚨 90+ dias</div>
                    <div style="font-size: 28px; font-weight: bold;">R$ ${atrasos['90+'].reduce((s, l) => s + l.valor, 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    <div style="font-size: 12px; opacity: 0.8; margin-top: 8px;">${atrasos['90+'].length} lançamentos</div>
                </div>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <h3 style="margin: 0 0 20px 0; color: #2c3e50;">📋 Lançamentos Inadimplentes</h3>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-bottom: 2px solid #764ba2;">
                                <th style="padding: 12px; text-align: left; font-size: 13px; color: #ffffff;">Descrição</th>
                                <th style="padding: 12px; text-align: left; font-size: 13px; color: #ffffff;">Cliente</th>
                                <th style="padding: 12px; text-align: center; font-size: 13px; color: #ffffff;">Vencimento</th>
                                <th style="padding: 12px; text-align: center; font-size: 13px; color: #ffffff;">Dias Atraso</th>
                                <th style="padding: 12px; text-align: right; font-size: 13px; color: #ffffff;">Valor</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${inadimplentes.length === 0 ? 
                                '<tr><td colspan="5" style="padding: 20px; text-align: center; color: #27ae60;">✅ Nenhum lançamento inadimplente</td></tr>' :
                                inadimplentes.map(l => {
                                    const dataVenc = new Date(l.data_vencimento);
                                    const diasAtraso = Math.floor((hoje - dataVenc) / (1000 * 60 * 60 * 24));
                                    let corAtraso = '#f39c12';
                                    if (diasAtraso > 60) corAtraso = '#e74c3c';
                                    else if (diasAtraso > 30) corAtraso = '#e67e22';
                                    
                                    return `
                                        <tr style="border-bottom: 1px solid #dee2e6;">
                                            <td style="padding: 12px; font-size: 13px;">${l.descricao || '-'}</td>
                                            <td style="padding: 12px; font-size: 13px;">${l.cliente_nome || '-'}</td>
                                            <td style="padding: 12px; text-align: center; font-size: 13px;">${dataVenc.toLocaleDateString('pt-BR')}</td>
                                            <td style="padding: 12px; text-align: center; font-size: 13px;">
                                                <span style="background: ${corAtraso}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">
                                                    ${diasAtraso} dias
                                                </span>
                                            </td>
                                            <td style="padding: 12px; text-align: right; font-size: 13px; font-weight: bold; color: #e74c3c;">
                                                R$ ${l.valor.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                                            </td>
                                        </tr>
                                    `;
                                }).join('')
                            }
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        // Atualizar badge
        const badge = document.getElementById('badge-inadimplencia');
        if (badge) badge.textContent = inadimplentes.length;
        
        console.log('✅ Inadimplência carregada com sucesso');
        
    } catch (error) {
        console.error('❌ Erro ao carregar inadimplência:', error);
        document.getElementById('inadimplencia-content').innerHTML = `
            <div style="text-align: center; padding: 40px; color: #e74c3c;">
                <p>❌ Erro ao carregar inadimplência</p>
                <p style="font-size: 14px;">${error.message}</p>
            </div>
        `;
    }
}

function exportarInadimplenciaPDF() {
    console.log('Exportando inadimplência em PDF...');
    alert('Funcionalidade de exportação PDF em desenvolvimento');
}

function exportarInadimplenciaExcel() {
    console.log('Exportando inadimplência em Excel...');
    alert('Funcionalidade de exportação Excel em desenvolvimento');
}

// ===== STUBS PARA FUNÇÕES REMOVIDAS/NÃO IMPLEMENTADAS =====
// Contratos (funcionalidade removida)
function openModalContrato() {
    console.warn('⚠️ Funcionalidade de Contratos foi removida');
    showToast('Funcionalidade de Contratos não está mais disponível', 'warning');
}

function exportarContratosPDF() {
    console.warn('⚠️ Funcionalidade de Contratos foi removida');
    showToast('Funcionalidade de Contratos não está mais disponível', 'warning');
}

// Agenda (funcionalidade removida)
function openModalAgenda() {
    console.warn('⚠️ Funcionalidade de Agenda foi removida');
    showToast('Funcionalidade de Agenda não está mais disponível', 'warning');
}

function visualizarCalendario() {
    console.warn('⚠️ Funcionalidade de Agenda foi removida');
    showToast('Funcionalidade de Agenda não está mais disponível', 'warning');
}

// Estoque de Produtos (funcionalidade removida)
function openModalProduto() {
    console.warn('⚠️ Funcionalidade de Estoque de Produtos foi removida');
    showToast('Funcionalidade de Estoque não está mais disponível', 'warning');
}

function exportarEstoquePDF() {
    console.warn('⚠️ Funcionalidade de Estoque de Produtos foi removida');
    showToast('Funcionalidade de Estoque não está mais disponível', 'warning');
}

function showEstoqueTab(tipo) {
    console.warn('⚠️ Funcionalidade de Estoque de Produtos foi removida');
    showToast('Funcionalidade de Estoque não está mais disponível', 'warning');
}

// Kits (funcionalidade removida)
function openModalKit() {
    console.warn('⚠️ Funcionalidade de Kits foi removida');
    showToast('Funcionalidade de Kits não está mais disponível', 'warning');
}

// Tags (funcionalidade removida)
function openModalTag() {
    console.warn('⚠️ Funcionalidade de Tags foi removida');
    showToast('Funcionalidade de Tags não está mais disponível', 'warning');
}

// Templates (funcionalidade removida)
function openModalTemplate() {
    console.warn('⚠️ Funcionalidade de Templates foi removida');
    showToast('Funcionalidade de Templates não está mais disponível', 'warning');
}

// Exportar funções globalmente
window.carregarDashboard = carregarDashboard;
window.carregarIndicadores = carregarIndicadores;
window.aplicarFiltroPeriodoIndicadores = aplicarFiltroPeriodoIndicadores;
window.exportarIndicadoresPDF = exportarIndicadoresPDF;
window.exportarIndicadoresExcel = exportarIndicadoresExcel;
window.carregarInadimplencia = carregarInadimplencia;
window.exportarInadimplenciaPDF = exportarInadimplenciaPDF;
window.exportarInadimplenciaExcel = exportarInadimplenciaExcel;

// Exportar stubs de funcionalidades removidas
window.openModalContrato = openModalContrato;
window.exportarContratosPDF = exportarContratosPDF;
window.openModalAgenda = openModalAgenda;
window.visualizarCalendario = visualizarCalendario;
window.openModalProduto = openModalProduto;
window.exportarEstoquePDF = exportarEstoquePDF;
window.showEstoqueTab = showEstoqueTab;
window.openModalKit = openModalKit;
window.openModalTag = openModalTag;
window.openModalTemplate = openModalTemplate;

console.log('%c ✓ Sistema Financeiro - app.js v20251223debug carregado ', 'background: #4CAF50; color: white; font-weight: bold');
console.log('%c 📊 Funções disponíveis (incluindo stubs de funcionalidades removidas): ', 'background: #2196F3; color: white; font-weight: bold');
console.log('  ✓ showContratoTab:', typeof window.showContratoTab);
console.log('  ✓ openModalContrato:', typeof window.openModalContrato, '(stub)');
console.log('  ✓ exportarContratosPDF:', typeof window.exportarContratosPDF, '(stub)');
console.log('  ✓ openModalAgenda:', typeof window.openModalAgenda, '(stub)');
console.log('  ✓ visualizarCalendario:', typeof window.visualizarCalendario, '(stub)');
console.log('  ✓ openModalProduto:', typeof window.openModalProduto, '(stub)');
console.log('  ✓ exportarEstoquePDF:', typeof window.exportarEstoquePDF, '(stub)');
console.log('  ✓ showEstoqueTab:', typeof window.showEstoqueTab, '(stub)');
console.log('  ✓ openModalKit:', typeof window.openModalKit, '(stub)');
console.log('  ✓ openModalTag:', typeof window.openModalTag, '(stub)');
console.log('  ✓ openModalTemplate:', typeof window.openModalTemplate, '(stub)');

