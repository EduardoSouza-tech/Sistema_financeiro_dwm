// Sistema Financeiro - v20251204lancamentos2
// Gerenciamento completo do sistema financeiro
console.log('%c âœ“ Sistema Financeiro - app.js v20251204lancamentos2 carregado ', 'background: #4CAF50; color: white; font-size: 16px; font-weight: bold');

// Suprimir erros de extensÃµes do navegador
window.addEventListener('error', function(e) {
    if (e.message.includes('message channel closed')) {
        e.preventDefault();
        return;
    }
});

// Estados das tabs
window.clienteTabAtiva = 'ativos';
window.fornecedorTabAtiva = 'ativos';

// === FUNÃ‡Ã•ES DE TABS ===

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

// === FUNÃ‡Ã•ES DE CARREGAMENTO ===

// FunÃ§Ã£o auxiliar para carregar categorias no array global
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

// FunÃ§Ã£o auxiliar para carregar clientes no array global
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

// FunÃ§Ã£o auxiliar para carregar fornecedores no array global
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
        
        // Mostrar/ocultar coluna de data de inativaÃ§Ã£o
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
                    <button class="btn btn-primary btn-small btn-editar-cliente" data-index="${index}" title="Editar">âœï¸</button>
                    <button class="btn btn-warning btn-small" onclick="openModalInativarCliente('${nome}')" title="Inativar" style="background: #f39c12;">ðŸ”’</button>
                    <button class="btn btn-danger btn-small" onclick="excluirCliente('${nome}')" title="Excluir">ðŸ—‘ï¸</button>
                `;
            } else {
                const dataFormatada = cli.data_inativacao ? new Date(cli.data_inativacao).toLocaleDateString('pt-BR') : '-';
                dataInativacaoCell = `<td>${dataFormatada}</td>`;
                
                acoesBtns = `
                    <button class="btn btn-success btn-small" onclick="reativarCliente('${nome}')" title="Reativar">âœ…</button>
                    <button class="btn btn-info btn-small" onclick="verMotivoInativacao('${nome}', '${cli.motivo_inativacao || 'Sem motivo'}', '${cli.data_inativacao || ''}')" title="Ver Motivo">â„¹ï¸</button>
                    <button class="btn btn-danger btn-small" onclick="excluirCliente('${nome}')" title="Excluir">ðŸ—‘ï¸</button>
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
        
        // Mostrar/ocultar coluna de data de inativaÃ§Ã£o
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
                    <button class="btn btn-primary btn-small btn-editar-fornecedor" data-index="${index}" title="Editar">âœï¸</button>
                    <button class="btn btn-warning btn-small" onclick="openModalInativarFornecedor('${nome}')" title="Inativar" style="background: #f39c12;">ðŸ”’</button>
                    <button class="btn btn-danger btn-small" onclick="excluirFornecedor('${nome}')" title="Excluir">ðŸ—‘ï¸</button>
                `;
            } else {
                const dataFormatada = forn.data_inativacao ? new Date(forn.data_inativacao).toLocaleDateString('pt-BR') : '-';
                dataInativacaoCell = `<td>${dataFormatada}</td>`;
                
                acoesBtns = `
                    <button class="btn btn-success btn-small" onclick="reativarFornecedor('${nome}')" title="Reativar">âœ…</button>
                    <button class="btn btn-info btn-small" onclick="verMotivoInativacao('${nome}', '${forn.motivo_inativacao || 'Sem motivo'}', '${forn.data_inativacao || ''}')" title="Ver Motivo">â„¹ï¸</button>
                    <button class="btn btn-danger btn-small" onclick="excluirFornecedor('${nome}')" title="Excluir">ðŸ—‘ï¸</button>
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

// === FUNÃ‡Ã•ES DE INATIVAÃ‡ÃƒO ===

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
        alert('Por favor, informe o motivo da inativaÃ§Ã£o');
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
    if (!confirm(`Deseja realmente EXCLUIR o cliente ${nome}?\n\nATENÃ‡ÃƒO: Esta aÃ§Ã£o Ã© permanente e sÃ³ serÃ¡ permitida se nÃ£o houver lanÃ§amentos vinculados.`)) return;
    
    try {
        const response = await fetch(`/api/clientes/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Cliente excluÃ­do com sucesso!');
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
        alert('Por favor, informe o motivo da inativaÃ§Ã£o');
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
    if (!confirm(`Deseja realmente EXCLUIR o fornecedor ${nome}?\n\nATENÃ‡ÃƒO: Esta aÃ§Ã£o Ã© permanente e sÃ³ serÃ¡ permitida se nÃ£o houver lanÃ§amentos vinculados.`)) return;
    
    try {
        const response = await fetch(`/api/fornecedores/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Fornecedor excluÃ­do com sucesso!');
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
    }) : 'Data nÃ£o disponÃ­vel';
    
    document.getElementById('motivo-data').textContent = dataFormatada;
    document.getElementById('modal-motivo-inativacao').style.display = 'flex';
}

function closeModalMotivoInativacao() {
    document.getElementById('modal-motivo-inativacao').style.display = 'none';
}

// === FUNÃ‡Ã•ES DE CONTAS BANCÃRIAS ===

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
        console.error('Erro ao carregar contas bancÃ¡rias:', error);
        showToast('Erro ao carregar contas bancÃ¡rias', 'error');
    }
}

function atualizarFiltroBancos(contas) {
    const selectBanco = document.getElementById('filtro-banco');
    if (!selectBanco) return;
    
    // Extrair bancos Ãºnicos
    const bancosUnicos = [...new Set(contas.map(c => c.banco))].filter(b => b).sort();
    
    // Manter o valor selecionado atual
    const valorAtual = selectBanco.value;
    
    // Limpar e recriar opÃ§Ãµes
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
        console.error('Tabela de contas nÃ£o encontrada');
        return;
    }
    
    tbody.innerHTML = '';
    
    if (contas.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhuma conta bancÃ¡ria encontrada</td></tr>';
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
                <button class="btn btn-warning btn-small" onclick="editarConta('${conta.nome.replace(/'/g, "\\'")}')">âœï¸</button>
                <button class="btn btn-danger btn-small" onclick="excluirConta('${conta.nome.replace(/'/g, "\\'")}')">ðŸ—‘ï¸</button>
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
        console.error('Erro ao carregar conta para ediÃ§Ã£o:', error);
        showToast('Erro ao carregar conta', 'error');
    }
}

async function excluirConta(nome) {
    if (!confirm(`Deseja realmente excluir a conta bancÃ¡ria "${nome}"?\n\nAtenÃ§Ã£o: Esta aÃ§Ã£o nÃ£o pode ser desfeita!`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/contas/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('âœ“ Conta bancÃ¡ria excluÃ­da com sucesso!', 'success');
            loadContasBancarias();
            if (typeof loadContas === 'function') loadContas();
        } else {
            showToast('Erro: ' + (result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro ao excluir conta:', error);
        showToast('Erro ao excluir conta bancÃ¡ria', 'error');
    }
}

// === FUNÃ‡Ã•ES DE CATEGORIAS ===

async function loadCategoriasTable() {
    try {
        const response = await fetch('/api/categorias');
        const categoriasList = await response.json();
        
        const tbodyReceita = document.getElementById('tbody-categorias-receita');
        const tbodyDespesa = document.getElementById('tbody-categorias-despesa');
        
        if (!tbodyReceita || !tbodyDespesa) {
            console.error('Tabelas de categorias nÃ£o encontradas');
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
                        <button class="btn btn-info btn-small" data-categoria="${nomeEscaped}" title="Ver subcategorias">ðŸ”</button>
                        <button class="btn btn-warning btn-small" onclick="editarCategoria('${nomeEscaped}', '${cat.tipo}')" title="Editar categoria">âœï¸</button>
                        <button class="btn btn-danger btn-small" onclick="excluirCategoria('${nomeEscaped}')" title="Excluir categoria">ðŸ—‘ï¸</button>
                    </td>
                `;
                
                // Adicionar evento de click ao botÃ£o de subcategorias
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
                        <button class="btn btn-info btn-small" data-categoria="${nomeEscaped}" title="Ver subcategorias">ðŸ”</button>
                        <button class="btn btn-warning btn-small" onclick="editarCategoria('${nomeEscaped}', '${cat.tipo}')" title="Editar categoria">âœï¸</button>
                        <button class="btn btn-danger btn-small" onclick="excluirCategoria('${nomeEscaped}')" title="Excluir categoria">ðŸ—‘ï¸</button>
                    </td>
                `;
                
                // Adicionar evento de click ao botÃ£o de subcategorias
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
        console.error('Erro ao carregar categoria para ediÃ§Ã£o:', error);
        showToast('Erro ao carregar categoria', 'error');
    }
}

function verSubcategorias(nomeCategoria, subcategorias) {
    const modal = document.getElementById('modal-subcategorias');
    const titulo = document.getElementById('modal-subcategorias-titulo');
    const lista = document.getElementById('modal-subcategorias-lista');
    
    if (!modal || !titulo || !lista) {
        console.error('Elementos do modal de subcategorias nÃ£o encontrados');
        return;
    }
    
    // Atualizar tÃ­tulo
    titulo.textContent = `ðŸ“‹ Subcategorias de "${nomeCategoria}"`;
    
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
                <div class="subcategorias-empty-icon">ðŸ“­</div>
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
    if (!confirm(`Deseja realmente excluir a categoria "${nome}"?\n\nAtenÃ§Ã£o: Esta aÃ§Ã£o nÃ£o pode ser desfeita!`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/categorias/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('âœ“ Categoria excluÃ­da com sucesso!', 'success');
            if (typeof loadCategoriasTable === 'function') loadCategoriasTable();
        } else {
            showToast('Erro: ' + (result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro ao excluir categoria:', error);
        showToast('Erro ao excluir categoria', 'error');
    }
}

// Tornar funÃ§Ãµes globais
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
// === FUNÃ‡Ã•ES DE CONTAS A RECEBER/PAGAR ===

// FunÃ§Ã£o auxiliar para formatar data no padrÃ£o brasileiro
function formatarDataBR(dataISO) {
    if (!dataISO || dataISO === '-') return '-';
    
    try {
        // Extrair YYYY-MM-DD sem considerar fuso horÃ¡rio
        const partes = dataISO.split('T')[0].split('-');
        if (partes.length === 3) {
            const ano = partes[0];
            const mes = partes[1];
            const dia = partes[2];
            return `${dia}/${mes}/${ano}`;
        }
        
        // Fallback para mÃ©todo antigo
        const data = new Date(dataISO + 'T00:00:00');
        const d = String(data.getDate()).padStart(2, '0');
        const m = String(data.getMonth() + 1).padStart(2, '0');
        const a = data.getFullYear();
        return `${d}/${m}/${a}`;
    } catch (e) {
        return dataISO;
    }
}

// FunÃ§Ã£o para carregar saldos dos bancos
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

// FunÃ§Ã£o para atualizar saldo do banco selecionado
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
            console.error('Tabela de contas a receber nÃ£o encontrada');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (lancamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="empty-state">Nenhuma conta a receber cadastrada</td></tr>';
            return;
        }
        
        // Aplicar filtros se necessÃ¡rio
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
        
        lancamentosFiltrados.forEach(lanc => {
            const tr = document.createElement('tr');
            const valor = parseFloat(lanc.valor || 0);
            const dataVencimento = formatarDataBR(lanc.data_vencimento);
            let status = (lanc.status || 'PENDENTE').toUpperCase();
            
            // Verificar se estÃ¡ vencido
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
                statusText = 'âœ“ Pago';
            } else if (status === 'VENCIDO') {
                statusClass = 'status-vencido';
                statusText = 'âš ï¸ Vencido';
            } else if (status === 'PENDENTE') {
                statusClass = 'status-pendente';
                statusText = 'â³ Pendente';
            } else if (status === 'CANCELADO') {
                statusClass = 'status-cancelado';
                statusText = 'âœ– Cancelado';
            }
            
            const btnLiquidar = (status === 'PENDENTE' || status === 'VENCIDO')
                ? `<button class="btn btn-success btn-small" onclick="liquidarLancamento(${lanc.id}, 'RECEITA')" title="Liquidar">ðŸ’°</button>` 
                : '';
            
            tr.innerHTML = `
                <td><input type="checkbox" class="checkbox-lancamento" data-id="${lanc.id || ''}"></td>
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
                    <button class="btn btn-warning btn-small" onclick="editarLancamento(${lanc.id}, 'RECEITA')" title="Editar">âœï¸</button>
                    <button class="btn btn-danger btn-small" onclick="excluirLancamento(${lanc.id}, 'RECEITA')" title="Excluir">ðŸ—‘ï¸</button>
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
            console.error('Tabela de contas a pagar nÃ£o encontrada');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (lancamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="empty-state">Nenhuma conta a pagar cadastrada</td></tr>';
            return;
        }
        
        // Aplicar filtros se necessÃ¡rio
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
        
        lancamentosFiltrados.forEach(lanc => {
            const tr = document.createElement('tr');
            const valor = parseFloat(lanc.valor || 0);
            const dataVencimento = formatarDataBR(lanc.data_vencimento);
            let status = (lanc.status || 'PENDENTE').toUpperCase();
            
            // Verificar se estÃ¡ vencido
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
                statusText = 'âœ“ Pago';
            } else if (status === 'VENCIDO') {
                statusClass = 'status-vencido';
                statusText = 'âš ï¸ Vencido';
            } else if (status === 'PENDENTE') {
                statusClass = 'status-pendente';
                statusText = 'â³ Pendente';
            } else if (status === 'CANCELADO') {
                statusClass = 'status-cancelado';
                statusText = 'âœ– Cancelado';
            }
            
            const btnLiquidar = (status === 'PENDENTE' || status === 'VENCIDO')
                ? `<button class="btn btn-success btn-small" onclick="liquidarLancamento(${lanc.id}, 'DESPESA')" title="Liquidar">ðŸ’°</button>` 
                : '';
            
            tr.innerHTML = `
                <td><input type="checkbox" class="checkbox-lancamento" data-id="${lanc.id || ''}"></td>
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
                    <button class="btn btn-warning btn-small" onclick="editarLancamento(${lanc.id}, 'DESPESA')" title="Editar">âœï¸</button>
                    <button class="btn btn-danger btn-small" onclick="excluirLancamento(${lanc.id}, 'DESPESA')" title="Excluir">ðŸ—‘ï¸</button>
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

// === FUNÃ‡Ã•ES DE GERENCIAMENTO DE LANÃ‡AMENTOS ===

// VariÃ¡veis globais para liquidaÃ§Ã£o
let lancamentoParaLiquidar = null;
let tipoLancamentoParaLiquidar = null;
let tipoLiquidacaoEmMassa = null;

async function liquidarLancamento(id, tipo) {
    // Armazenar dados do lanÃ§amento
    lancamentoParaLiquidar = id;
    tipoLancamentoParaLiquidar = tipo;
    
    // Carregar contas bancÃ¡rias
    try {
        const response = await fetch('/api/contas');
        const contas = await response.json();
        
        const opcoesContas = contas.map(c => 
            `<option value="${c.nome}">${c.banco} - ${c.agencia}/${c.conta}</option>`
        ).join('');
        
        // Criar modal de liquidaÃ§Ã£o
        const modal = createModal('ðŸ’° Liquidar LanÃ§amento', `
            <form id="form-liquidacao" onsubmit="confirmarLiquidacao(event)">
                <div class="form-group">
                    <label>*Data de LiquidaÃ§Ã£o:</label>
                    <input type="date" id="liquidacao-data" value="${new Date().toISOString().split('T')[0]}" required>
                </div>
                
                <div class="form-group">
                    <label>*Conta BancÃ¡ria:</label>
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
                    <label>ObservaÃ§Ãµes:</label>
                    <textarea id="liquidacao-observacoes" rows="3" placeholder="Opcional"></textarea>
                </div>
                
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                    <button type="button" onclick="closeModal()" style="padding: 10px 20px; background: #95a5a6; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">Cancelar</button>
                    <button type="submit" style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold;">ðŸ’° Liquidar</button>
                </div>
            </form>
        `);
        
        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('active'), 10);
        
    } catch (error) {
        console.error('Erro ao abrir modal de liquidaÃ§Ã£o:', error);
        showToast('Erro ao carregar contas bancÃ¡rias', 'error');
    }
}

async function confirmarLiquidacao(event) {
    event.preventDefault();
    
    const data = document.getElementById('liquidacao-data').value;
    const conta = document.getElementById('liquidacao-conta').value;
    const juros = parseFloat(document.getElementById('liquidacao-juros').value) || 0;
    const desconto = parseFloat(document.getElementById('liquidacao-desconto').value) || 0;
    const observacoes = document.getElementById('liquidacao-observacoes').value;
    
    // ValidaÃ§Ã£o adicional
    if (!data || data.trim() === '') {
        showToast('âŒ Data de pagamento Ã© obrigatÃ³ria', 'error');
        return;
    }
    
    if (!conta || conta.trim() === '') {
        showToast('âŒ Conta bancÃ¡ria Ã© obrigatÃ³ria', 'error');
        return;
    }
    
    // Enviando dados de liquidaÃ§Ã£o
    
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
            showToast('âœ“ LanÃ§amento liquidado com sucesso!', 'success');
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
        console.error('Erro ao liquidar lanÃ§amento:', error);
        showToast('Erro ao liquidar lanÃ§amento', 'error');
    }
}

async function editarLancamento(id, tipo) {
    try {
        const response = await fetch(`/api/lancamentos/${id}`);
        const lancamento = await response.json();
        
        if (!lancamento || lancamento.error) {
            showToast('LanÃ§amento nÃ£o encontrado', 'error');
            return;
        }
        
        // Editando lanÃ§amento
        
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
                
                if (idField) idField.value = id; // PREENCHER O ID PARA EDIÃ‡ÃƒO
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
                
                // Mudar tÃ­tulo do modal
                const modalTitle = document.querySelector('#dynamic-modal h2');
                if (modalTitle) modalTitle.textContent = 'âœï¸ Editar Receita';
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
                
                if (idField) idField.value = id; // PREENCHER O ID PARA EDIÃ‡ÃƒO
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
                
                // Mudar tÃ­tulo do modal
                const modalTitle = document.querySelector('#dynamic-modal h2');
                if (modalTitle) modalTitle.textContent = 'âœï¸ Editar Despesa';
            }
        }
        
    } catch (error) {
        console.error('Erro ao editar lanÃ§amento:', error);
        showToast('Erro ao carregar lanÃ§amento', 'error');
    }
}

async function excluirLancamento(id, tipo) {
    if (!confirm('Deseja realmente excluir este lanÃ§amento?\n\nAtenÃ§Ã£o: Esta aÃ§Ã£o nÃ£o pode ser desfeita!')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/lancamentos/${id}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('âœ“ LanÃ§amento excluÃ­do com sucesso!', 'success');
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
        console.error('Erro ao excluir lanÃ§amento:', error);
        showToast('Erro ao excluir lanÃ§amento', 'error');
    }
}

// FunÃ§Ã£o para adicionar listeners aos checkboxes
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

// FunÃ§Ã£o para atualizar visibilidade dos botÃµes de aÃ§Ã£o em massa
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

// FunÃ§Ã£o para seleÃ§Ã£o em massa
function toggleSelectAll(tipo) {
    const checkboxAll = document.getElementById(`select-all-${tipo}`);
    const checkboxes = document.querySelectorAll(`#contas-${tipo}-section .checkbox-lancamento`);
    
    checkboxes.forEach(cb => {
        cb.checked = checkboxAll.checked;
    });
    
    // Atualizar visibilidade dos botÃµes
    atualizarVisibilidadeBotoesEmMassa(tipo);
}

async function liquidarEmMassa(tipoOriginal) {
    // Converter RECEITA/DESPESA para receber/pagar
    const tipo = tipoOriginal === 'RECEITA' ? 'receber' : 'pagar';
    const checkboxes = document.querySelectorAll(`#contas-${tipo}-section .checkbox-lancamento:checked`);
    
    if (checkboxes.length === 0) {
        showToast('Selecione pelo menos um lanÃ§amento', 'warning');
        return;
    }
    
    // Armazenar tipo para uso na confirmaÃ§Ã£o
    tipoLiquidacaoEmMassa = tipoOriginal;
    
    // Carregar contas bancÃ¡rias
    try {
        const response = await fetch('/api/contas');
        const contas = await response.json();
        
        const opcoesContas = contas.map(c => 
            `<option value="${c.nome}">${c.banco} - ${c.agencia}/${c.conta}</option>`
        ).join('');
        
        // Criar modal de liquidaÃ§Ã£o em massa
        const modal = createModal(`ðŸ’° Liquidar ${checkboxes.length} LanÃ§amento(s)`, `
            <form id="form-liquidacao-massa" onsubmit="return confirmarLiquidacaoEmMassa(event)">
                <div class="form-group">
                    <label>*Data de LiquidaÃ§Ã£o:</label>
                    <input type="date" id="liquidacao-massa-data" value="${new Date().toISOString().split('T')[0]}" required>
                </div>
                
                <div class="form-group">
                    <label>*Conta BancÃ¡ria:</label>
                    <select id="liquidacao-massa-conta" required>
                        <option value="">Selecione a conta...</option>
                        ${opcoesContas}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>ObservaÃ§Ãµes:</label>
                    <textarea id="liquidacao-massa-observacoes" rows="3" placeholder="Opcional"></textarea>
                </div>
                
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                    <button type="button" onclick="closeModal()" style="padding: 10px 20px; background: #95a5a6; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">Cancelar</button>
                    <button type="submit" style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold;">ðŸ’° Liquidar Todos</button>
                </div>
            </form>
        `);
        
        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('active'), 10);
        
    } catch (error) {
        console.error('Erro ao abrir modal de liquidaÃ§Ã£o em massa:', error);
        showToast('Erro ao carregar contas bancÃ¡rias', 'error');
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
    showToast(`âœ“ ${sucesso} lanÃ§amento(s) liquidado(s)${erro > 0 ? `, ${erro} erro(s)` : ''}`, sucesso > 0 ? 'success' : 'error');
    
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
        showToast('Selecione pelo menos um lanÃ§amento', 'warning');
        return;
    }
    
    if (!confirm(`Deseja realmente excluir ${checkboxes.length} lanÃ§amento(s)?\n\nAtenÃ§Ã£o: Esta aÃ§Ã£o nÃ£o pode ser desfeita!`)) {
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
    
    showToast(`âœ“ ${sucesso} lanÃ§amento(s) excluÃ­do(s)${erro > 0 ? `, ${erro} erro(s)` : ''}`, sucesso > 0 ? 'success' : 'error');
    
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
        
        // Determinar perÃ­odo
        let data_inicio, data_fim;
        
        if (dataInicial && dataFinal) {
            // Usar perÃ­odo personalizado (prioridade mÃ¡xima)
            data_inicio = dataInicial;
            data_fim = dataFinal;
            // PerÃ­odo personalizado
        } else if (ano && ano.trim() !== '' && mes && mes.trim() !== '') {
            // Usar ano/mÃªs especÃ­fico (ambos preenchidos)
            const anoNum = parseInt(ano);
            const mesNum = parseInt(mes);
            const mesPadded = mes.length === 1 ? '0' + mes : mes;
            
            // Calcular Ãºltimo dia do mÃªs corretamente
            const ultimoDia = new Date(anoNum, mesNum, 0).getDate();
            const diaPadded = String(ultimoDia).padStart(2, '0');
            
            data_inicio = `${anoNum}-${mesPadded}-01`;
            data_fim = `${anoNum}-${mesPadded}-${diaPadded}`;
            // Ano/mÃªs
        } else if (ano && ano.trim() !== '') {
            // Usar ano inteiro (sÃ³ ano preenchido)
            data_inicio = `${ano}-01-01`;
            data_fim = `${ano}-12-31`;
            // Ano inteiro
        } else if (mes && mes.trim() !== '') {
            // Usar mÃªs do ano atual (sÃ³ mÃªs preenchido)
            const hoje = new Date();
            const anoAtual = hoje.getFullYear();
            const mesNum = parseInt(mes);
            const mesPadded = mes.length === 1 ? '0' + mes : mes;
            const ultimoDia = new Date(anoAtual, mesNum, 0).getDate();
            const diaPadded = String(ultimoDia).padStart(2, '0');
            
            data_inicio = `${anoAtual}-${mesPadded}-01`;
            data_fim = `${anoAtual}-${mesPadded}-${diaPadded}`;
            // MÃªs do ano atual
        } else {
            // Usar mÃªs atual (padrÃ£o - nada preenchido)
            const hoje = new Date();
            const anoAtual = hoje.getFullYear();
            const mesAtual = hoje.getMonth() + 1; // 0-11 -> 1-12
            const mesPadded = String(mesAtual).padStart(2, '0');
            const ultimoDia = new Date(anoAtual, mesAtual, 0).getDate();
            const diaPadded = String(ultimoDia).padStart(2, '0');
            
            data_inicio = `${anoAtual}-${mesPadded}-01`;
            data_fim = `${anoAtual}-${mesPadded}-${diaPadded}`;
            // MÃªs atual (padrÃ£o)
        }
        
        // PerÃ­odo calculado
        
        // Buscar lanÃ§amentos liquidados
        const response = await fetch(`/api/relatorios/fluxo-caixa?data_inicio=${data_inicio}&data_fim=${data_fim}`);
        const lancamentos = await response.json();
        
        // LanÃ§amentos carregados
        
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
            // Banco especÃ­fico filtrado
            const contaFiltrada = contas.find(c => c.nome === banco);
            if (contaFiltrada) {
                const cor = contaFiltrada.saldo >= 0 ? '#27ae60' : '#e74c3c';
                html += `
                    <div style="background: white; padding: 12px 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <div style="font-size: 11px; color: #7f8c8d; margin-bottom: 2px;">ðŸ¦ BANCO FILTRADO</div>
                            <div style="font-size: 14px; font-weight: 600; color: #2c3e50;">${contaFiltrada.nome}</div>
                            <div style="font-size: 11px; color: #95a5a6;">${contaFiltrada.banco} â€¢ Ag: ${contaFiltrada.agencia} â€¢ Conta: ${contaFiltrada.conta}</div>
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
                        <div style="font-size: 11px; color: #7f8c8d; margin-bottom: 2px;">ðŸ’° TODAS AS CONTAS</div>
                        <div style="font-size: 14px; font-weight: 600; color: #2c3e50;">${contas.length} conta${contas.length > 1 ? 's' : ''} bancÃ¡ria${contas.length > 1 ? 's' : ''}</div>
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
                            <th style="padding: 12px; text-align: left;">RazÃ£o Social</th>
                            <th style="padding: 12px; text-align: left;">Categoria</th>
                            <th style="padding: 12px; text-align: left;">Subcategoria</th>
                            <th style="padding: 12px; text-align: left;">DescriÃ§Ã£o</th>
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
                        Nenhum lanÃ§amento liquidado encontrado no perÃ­odo
                    </td>
                </tr>
            `;
        } else {
            // Ordenar por data de pagamento (crescente - mais antiga para mais recente)
            lancamentosFiltrados.sort((a, b) => new Date(a.data_pagamento) - new Date(b.data_pagamento));
            
            lancamentosFiltrados.forEach(l => {
                const dataPagamento = l.data_pagamento ? new Date(l.data_pagamento + 'T00:00:00').toLocaleDateString('pt-BR') : '-';
                const tipo = l.tipo.toLowerCase() === 'receita' ? 'ðŸ’° Receita' : 'ðŸ’¸ Despesa';
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
                âŒ Erro ao carregar fluxo de caixa
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

// Exportar funÃ§Ãµes
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

// FunÃ§Ã£o para exportar Contas a Pagar em PDF
