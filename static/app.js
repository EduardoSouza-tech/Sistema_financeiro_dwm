// Sistema Financeiro - v20251204lancamentos2
// Gerenciamento completo do sistema financeiro
console.log('%c ✓ Sistema Financeiro - app.js v20251204lancamentos2 carregado ', 'background: #4CAF50; color: white; font-size: 16px; font-weight: bold');

// Suprimir erros de extensões do navegador
window.addEventListener('error', function(e) {
    if (e.message.includes('message channel closed')) {
        e.preventDefault();
        return;
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
    const conta = document.getElementById('liquidacao-banco')?.value;
    const juros = parseFloat(document.getElementById('liquidacao-juros')?.value) || 0;
    const desconto = parseFloat(document.getElementById('liquidacao-desconto')?.value) || 0;
    const observacoes = document.getElementById('liquidacao-observacoes')?.value || '';
    
    // Validação adicional
    if (!data) {
        showToast('❌ Data de pagamento é obrigatória', 'error');
        return;
    }
    
    if (!conta) {
        showToast('❌ Conta bancária é obrigatória', 'error');
        return;
    }
    
    // Enviando dados de liquidação
    
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
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #34495e; color: white;">
                            <th style="padding: 12px; text-align: left;">Data Pagamento</th>
                            <th style="padding: 12px; text-align: left;">Tipo</th>
                            <th style="padding: 12px; text-align: left;">Razão Social</th>
                            <th style="padding: 12px; text-align: left;">Categoria</th>
                            <th style="padding: 12px; text-align: left;">Subcategoria</th>
                            <th style="padding: 12px; text-align: left;">Descrição</th>
                            <th style="padding: 12px; text-align: left;">Banco</th>
                            <th style="padding: 12px; text-align: right;">Valor</th>
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
                        <td style="padding: 12px; color: #2c3e50; font-weight: 500;">${dataPagamento}</td>
                        <td style="padding: 12px;"><span style="color: ${cor}; font-weight: 600;">${tipo}</span></td>
                        <td style="padding: 12px; color: #2c3e50; font-weight: 500;">${l.pessoa || '-'}</td>
                        <td style="padding: 12px; color: #2c3e50; font-weight: 500;">${l.categoria || '-'}</td>
                        <td style="padding: 12px; color: #2c3e50; font-weight: 500;">${l.subcategoria || '-'}</td>
                        <td style="padding: 12px; color: #2c3e50;">${l.descricao || '-'}</td>
                        <td style="padding: 12px; color: #2c3e50; font-weight: 500;">${l.conta_bancaria || '-'}</td>
                        <td style="padding: 12px; text-align: right; font-weight: bold; color: ${cor};">R$ ${l.valor.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
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

function carregarIndicadores() {
    console.log('Carregando indicadores...');
    carregarDashboard();
}

function aplicarFiltroPeriodoIndicadores() {
    console.log('Aplicando filtro de período...');
    carregarIndicadores();
}

// Exportar funções globalmente
window.carregarDashboard = carregarDashboard;
window.carregarIndicadores = carregarIndicadores;
window.aplicarFiltroPeriodoIndicadores = aplicarFiltroPeriodoIndicadores;

console.log('✓ Sistema Financeiro - app.js v20251205filtro3 carregado');
