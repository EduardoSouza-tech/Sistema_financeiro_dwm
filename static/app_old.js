// API Base URL - Usa URL relativa para funcionar tanto local quanto em produção
const API_URL = window.location.origin + '/api';

// Estado global
let currentPage = 'dashboard';
let contas = [];
let categorias = [];
let lancamentos = [];

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    loadContas();
    loadCategorias();
    
    // Definir datas padrão
    const hoje = new Date().toISOString().split('T')[0];
    const umMesAtras = new Date();
    umMesAtras.setMonth(umMesAtras.getMonth() - 1);
    const umMesAtrasStr = umMesAtras.toISOString().split('T')[0];
    
    const tresMesesFrente = new Date();
    tresMesesFrente.setMonth(tresMesesFrente.getMonth() + 3);
    const tresMesesFrenteStr = tresMesesFrente.toISOString().split('T')[0];
    
    document.getElementById('fluxo-data-inicio').value = umMesAtrasStr;
    document.getElementById('fluxo-data-fim').value = hoje;
    document.getElementById('analise-data-inicio').value = umMesAtrasStr;
    document.getElementById('analise-data-fim').value = hoje;
    document.getElementById('projecao-data-final').value = tresMesesFrenteStr;
});

// Navegação
function showPage(pageName) {
    // Ocultar todas as páginas
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Mostrar página selecionada
    document.getElementById(`page-${pageName}`).classList.add('active');
    
    // Atualizar botões da sidebar
    document.querySelectorAll('.nav-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    currentPage = pageName;
    
    // Carregar dados da página
    switch(pageName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'contas-receber':
            loadContasReceber();
            break;
        case 'contas-pagar':
            loadContasPagar();
            break;
        case 'contas-receber':
            loadContasReceber();
            break;
        case 'contas-pagar':
            loadContasPagar();
            break;
        case 'lancamentos':
            loadLancamentos();
            break;
        case 'contas':
            loadContas();
            break;
        case 'categorias':
            loadCategorias();
            break;
        case 'clientes':
            loadClientes();
            break;
        case 'fornecedores':
            loadFornecedores();
            break;
        case 'fluxo-caixa':
            loadFluxoCaixa();
            break;
        case 'fluxo-projetado':
            loadFluxoProjetado();
            break;
        case 'analise-contas':
            loadAnaliseContas();
            break;
        case 'analise-categorias':
            loadAnaliseCategorias();
            break;
        case 'inadimplencia':
            loadInadimplencia();
            break;
    }
}

function toggleSubmenu(submenuName) {
    const submenu = document.getElementById(`submenu-${submenuName}`);
    submenu.classList.toggle('open');
}

// Modals
function showModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    // Limpar formulário
    document.querySelector(`#${modalId} form`).reset();
}

// Formatação
function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

function formatarData(data) {
    if (!data) return '-';
    const d = new Date(data + 'T00:00:00');
    return d.toLocaleDateString('pt-BR');
}

// === DASHBOARD ===
async function loadDashboard() {
    try {
        const response = await fetch(`${API_URL}/relatorios/dashboard`);
        const data = await response.json();
        
        document.getElementById('saldo-total').textContent = formatarMoeda(data.saldo_total);
        document.getElementById('contas-receber').textContent = formatarMoeda(data.contas_receber);
        document.getElementById('contas-pagar').textContent = formatarMoeda(data.contas_pagar);
        document.getElementById('contas-vencidas').textContent = formatarMoeda(data.contas_vencidas);
        document.getElementById('total-contas').textContent = data.total_contas;
        document.getElementById('total-lancamentos').textContent = data.total_lancamentos;
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
        alert('Erro ao carregar dashboard. Verifique se o servidor está rodando.');
    }
}

// === CONTAS BANCÁRIAS ===
async function loadContas() {
    try {
        const response = await fetch(`${API_URL}/contas`);
        contas = await response.json();
        
        const tbody = document.getElementById('tbody-contas');
        tbody.innerHTML = '';
        
        // Atualizar select de contas nos formulários
        const selectConta = document.getElementById('select-conta');
        selectConta.innerHTML = '<option value="">Selecione...</option>';
        
        contas.forEach(conta => {
            // Tabela
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${conta.nome}</td>
                <td>${conta.banco}</td>
                <td>${conta.agencia}</td>
                <td>${conta.conta}</td>
                <td>${formatarMoeda(conta.saldo_inicial)}</td>
                <td>
                    <button class="btn btn-danger" onclick="excluirConta('${conta.nome}')">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
            
            // Select
            const option = document.createElement('option');
            option.value = conta.nome;
            option.textContent = conta.nome;
            selectConta.appendChild(option);
        });
    } catch (error) {
        console.error('Erro ao carregar contas:', error);
    }
}

async function salvarConta(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch(`${API_URL}/contas`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Conta adicionada com sucesso!');
            closeModal('modal-conta');
            loadContas();
        } else {
            alert('Erro: ' + result.error);
        }
    } catch (error) {
        console.error('Erro ao salvar conta:', error);
        alert('Erro ao salvar conta');
    }
}

async function excluirConta(nome) {
    if (!confirm(`Deseja realmente excluir a conta "${nome}"?`)) return;
    
    try {
        const response = await fetch(`${API_URL}/contas/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Conta excluída com sucesso!');
            loadContas();
        } else {
            alert('Erro: ' + result.error);
        }
    } catch (error) {
        console.error('Erro ao excluir conta:', error);
        alert('Erro ao excluir conta');
    }
}

// === CATEGORIAS ===
async function loadCategorias() {
    try {
        const response = await fetch(`${API_URL}/categorias`);
        categorias = await response.json();
        
        const tbody = document.getElementById('tbody-categorias');
        tbody.innerHTML = '';
        
        // Atualizar select de categorias nos formulários
        const selectCategoria = document.getElementById('select-categoria');
        selectCategoria.innerHTML = '<option value="">Selecione...</option>';
        
        categorias.forEach(cat => {
            // Tabela
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${cat.nome}</td>
                <td><span class="badge badge-${cat.tipo.toLowerCase()}">${cat.tipo}</span></td>
                <td>${cat.subcategorias.join(', ') || '-'}</td>
                <td>
                    <button class="btn btn-danger" onclick="excluirCategoria('${cat.nome}')">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
            
            // Select
            const option = document.createElement('option');
            option.value = cat.nome;
            option.textContent = cat.nome;
            option.dataset.subcategorias = JSON.stringify(cat.subcategorias);
            selectCategoria.appendChild(option);
        });
        
        // Listener para atualizar subcategorias
        selectCategoria.addEventListener('change', function() {
            const selectSubcategoria = document.getElementById('select-subcategoria');
            selectSubcategoria.innerHTML = '<option value="">Selecione...</option>';
            
            const selectedOption = this.options[this.selectedIndex];
            if (selectedOption.dataset.subcategorias) {
                const subcats = JSON.parse(selectedOption.dataset.subcategorias);
                subcats.forEach(sub => {
                    const option = document.createElement('option');
                    option.value = sub;
                    option.textContent = sub;
                    selectSubcategoria.appendChild(option);
                });
            }
        });
    } catch (error) {
        console.error('Erro ao carregar categorias:', error);
    }
}

async function salvarCategoria(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    // Converter subcategorias
    if (data.subcategorias) {
        data.subcategorias = data.subcategorias.split(',').map(s => s.trim()).filter(s => s);
    } else {
        data.subcategorias = [];
    }
    
    try {
        const response = await fetch(`${API_URL}/categorias`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Categoria adicionada com sucesso!');
            closeModal('modal-categoria');
            loadCategorias();
        } else {
            alert('Erro: ' + result.error);
        }
    } catch (error) {
        console.error('Erro ao salvar categoria:', error);
        alert('Erro ao salvar categoria');
    }
}

async function excluirCategoria(nome) {
    if (!confirm(`Deseja realmente excluir a categoria "${nome}"?`)) return;
    
    try {
        const response = await fetch(`${API_URL}/categorias/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Categoria excluída com sucesso!');
            loadCategorias();
        } else {
            alert('Erro: ' + result.error);
        }
    } catch (error) {
        console.error('Erro ao excluir categoria:', error);
        alert('Erro ao excluir categoria');
    }
}

// === CLIENTES ===
async function loadClientes() {
    try {
        const response = await fetch(`${API_URL}/clientes`);
        const clientes = await response.json();
        
        const tbody = document.getElementById('tbody-clientes');
        tbody.innerHTML = '';
        
        clientes.forEach(cliente => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${cliente.nome}</td>
                <td>${cliente.documento || '-'}</td>
                <td>${cliente.telefone || '-'}</td>
                <td>${cliente.email || '-'}</td>
                <td>
                    <button class="btn btn-danger" onclick="excluirCliente('${cliente.nome}')">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar clientes:', error);
    }
}

async function salvarCliente(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch(`${API_URL}/clientes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Cliente adicionado com sucesso!');
            closeModal('modal-cliente');
            loadClientes();
        } else {
            alert('Erro: ' + result.error);
        }
    } catch (error) {
        console.error('Erro ao salvar cliente:', error);
        alert('Erro ao salvar cliente');
    }
}

async function excluirCliente(nome) {
    if (!confirm(`Deseja realmente excluir o cliente "${nome}"?`)) return;
    
    try {
        const response = await fetch(`${API_URL}/clientes/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Cliente excluído com sucesso!');
            loadClientes();
        } else {
            alert('Erro: ' + result.error);
        }
    } catch (error) {
        console.error('Erro ao excluir cliente:', error);
        alert('Erro ao excluir cliente');
    }
}

// === FORNECEDORES ===
async function loadFornecedores() {
    try {
        const response = await fetch(`${API_URL}/fornecedores`);
        const fornecedores = await response.json();
        
        const tbody = document.getElementById('tbody-fornecedores');
        tbody.innerHTML = '';
        
        fornecedores.forEach(fornecedor => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${fornecedor.nome}</td>
                <td>${fornecedor.documento || '-'}</td>
                <td>${fornecedor.telefone || '-'}</td>
                <td>${fornecedor.email || '-'}</td>
                <td>
                    <button class="btn btn-danger" onclick="excluirFornecedor('${fornecedor.nome}')">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar fornecedores:', error);
    }
}

async function salvarFornecedor(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch(`${API_URL}/fornecedores`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Fornecedor adicionado com sucesso!');
            closeModal('modal-fornecedor');
            loadFornecedores();
        } else {
            alert('Erro: ' + result.error);
        }
    } catch (error) {
        console.error('Erro ao salvar fornecedor:', error);
        alert('Erro ao salvar fornecedor');
    }
}

async function excluirFornecedor(nome) {
    if (!confirm(`Deseja realmente excluir o fornecedor "${nome}"?`)) return;
    
    try {
        const response = await fetch(`${API_URL}/fornecedores/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Fornecedor excluído com sucesso!');
            loadFornecedores();
        } else {
            alert('Erro: ' + result.error);
        }
    } catch (error) {
        console.error('Erro ao excluir fornecedor:', error);
        alert('Erro ao excluir fornecedor');
    }
}

// === LANÇAMENTOS ===
async function loadLancamentos() {
    try {
        const response = await fetch(`${API_URL}/lancamentos`);
        lancamentos = await response.json();
        
        const tbody = document.getElementById('tbody-lancamentos');
        tbody.innerHTML = '';
        
        lancamentos.forEach(lanc => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><span class="badge badge-${lanc.tipo.toLowerCase()}">${lanc.tipo}</span></td>
                <td>${lanc.descricao}</td>
                <td>${formatarMoeda(lanc.valor)}</td>
                <td>${formatarData(lanc.data_vencimento)}</td>
                <td>${lanc.categoria || '-'}</td>
                <td><span class="badge badge-${lanc.status.toLowerCase()}">${lanc.status}</span></td>
                <td>
                    <button class="btn btn-danger" onclick="excluirLancamento(${lanc.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar lançamentos:', error);
    }
}

// === CONTAS A RECEBER ===
async function loadContasReceber() {
    try {
        const response = await fetch(`${API_URL}/lancamentos`);
        const todosLancamentos = await response.json();
        
        const tbody = document.getElementById('tbody-receber');
        tbody.innerHTML = '';
        
        // Filtros
        const filterText = document.getElementById('filter-receber').value.toLowerCase();
        const filterStatus = document.getElementById('filter-status-receber').value;
        
        // Filtrar apenas receitas
        const receitas = todosLancamentos.filter(lanc => {
            const isReceita = lanc.tipo === 'RECEITA';
            const matchText = lanc.descricao.toLowerCase().includes(filterText) || 
                             (lanc.pessoa && lanc.pessoa.toLowerCase().includes(filterText));
            const matchStatus = !filterStatus || lanc.status === filterStatus;
            return isReceita && matchText && matchStatus;
        });
        
        receitas.forEach(lanc => {
            const tr = document.createElement('tr');
            const statusClass = lanc.status === 'PAGO' ? 'badge-success' : lanc.status === 'VENCIDO' ? 'badge-danger' : 'badge-warning';
            
            tr.innerHTML = `
                <td>${lanc.pessoa || '-'}</td>
                <td>${lanc.descricao}</td>
                <td style="font-weight: bold; color: #27ae60;">${formatarMoeda(lanc.valor)}</td>
                <td>${formatarData(lanc.data_vencimento)}</td>
                <td>${lanc.categoria || '-'}</td>
                <td><span class="badge ${statusClass}">${lanc.status}</span></td>
                <td>
                    <button class="btn btn-danger" onclick="excluirLancamento(${lanc.id})" title="Excluir">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        if (receitas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 30px;">💰 Nenhuma conta a receber</td></tr>';
        }
    } catch (error) {
        console.error('Erro ao carregar contas a receber:', error);
    }
}

// === CONTAS A PAGAR ===
async function loadContasPagar() {
    try {
        const response = await fetch(`${API_URL}/lancamentos`);
        const todosLancamentos = await response.json();
        
        const tbody = document.getElementById('tbody-pagar');
        tbody.innerHTML = '';
        
        // Filtros
        const filterText = document.getElementById('filter-pagar').value.toLowerCase();
        const filterStatus = document.getElementById('filter-status-pagar').value;
        
        // Filtrar apenas despesas
        const despesas = todosLancamentos.filter(lanc => {
            const isDespesa = lanc.tipo === 'DESPESA';
            const matchText = lanc.descricao.toLowerCase().includes(filterText) || 
                             (lanc.pessoa && lanc.pessoa.toLowerCase().includes(filterText));
            const matchStatus = !filterStatus || lanc.status === filterStatus;
            return isDespesa && matchText && matchStatus;
        });
        
        despesas.forEach(lanc => {
            const tr = document.createElement('tr');
            const statusClass = lanc.status === 'PAGO' ? 'badge-success' : lanc.status === 'VENCIDO' ? 'badge-danger' : 'badge-warning';
            
            tr.innerHTML = `
                <td>${lanc.pessoa || '-'}</td>
                <td>${lanc.descricao}</td>
                <td style="font-weight: bold; color: #e74c3c;">${formatarMoeda(lanc.valor)}</td>
                <td>${formatarData(lanc.data_vencimento)}</td>
                <td>${lanc.categoria || '-'}</td>
                <td><span class="badge ${statusClass}">${lanc.status}</span></td>
                <td>
                    <button class="btn btn-danger" onclick="excluirLancamento(${lanc.id})" title="Excluir">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        if (despesas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 30px;">💳 Nenhuma conta a pagar</td></tr>';
        }
    } catch (error) {
        console.error('Erro ao carregar contas a pagar:', error);
    }
}

async function salvarLancamento(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch(`${API_URL}/lancamentos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Lançamento adicionado com sucesso!');
            closeModal('modal-lancamento');
            loadLancamentos();
            loadDashboard();
        } else {
            alert('Erro: ' + result.error);
        }
    } catch (error) {
        console.error('Erro ao salvar lançamento:', error);
        alert('Erro ao salvar lançamento');
    }
}

async function excluirLancamento(id) {
    if (!confirm('Deseja realmente excluir este lançamento?')) return;
    
    try {
        const response = await fetch(`${API_URL}/lancamentos/${id}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Lançamento excluído com sucesso!');
            loadLancamentos();
            loadDashboard();
        } else {
            alert('Erro: ' + result.error);
        }
    } catch (error) {
        console.error('Erro ao excluir lançamento:', error);
        alert('Erro ao excluir lançamento');
    }
}

// === FLUXO DE CAIXA ===
async function loadFluxoCaixa() {
    try {
        const dataInicio = document.getElementById('fluxo-data-inicio').value;
        const dataFim = document.getElementById('fluxo-data-fim').value;
        
        const response = await fetch(`${API_URL}/relatorios/fluxo-caixa?data_inicio=${dataInicio}&data_fim=${dataFim}`);
        const dados = await response.json();
        
        const tbody = document.getElementById('tbody-fluxo');
        tbody.innerHTML = '';
        
        dados.forEach(lanc => {
            const tr = document.createElement('tr');
            const entrada = lanc.tipo === 'RECEITA' ? formatarMoeda(lanc.valor) : '-';
            const saida = lanc.tipo === 'DESPESA' ? formatarMoeda(lanc.valor) : '-';
            
            tr.innerHTML = `
                <td><span class="badge badge-${lanc.tipo.toLowerCase()}">${lanc.tipo}</span></td>
                <td>${formatarData(lanc.data_pagamento)}</td>
                <td>${lanc.descricao}</td>
                <td>${lanc.categoria || '-'}</td>
                <td>${lanc.pessoa || '-'}</td>
                <td style="color: #27ae60; font-weight: bold;">${entrada}</td>
                <td style="color: #e74c3c; font-weight: bold;">${saida}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar fluxo de caixa:', error);
    }
}

// === ANÁLISE DE CATEGORIAS ===
async function loadAnaliseCategorias() {
    try {
        const dataInicio = document.getElementById('analise-data-inicio').value;
        const dataFim = document.getElementById('analise-data-fim').value;
        
        const response = await fetch(`${API_URL}/relatorios/fluxo-caixa?data_inicio=${dataInicio}&data_fim=${dataFim}`);
        const dados = await response.json();
        
        // Agrupar por categoria
        const receitas = {};
        const despesas = {};
        
        dados.forEach(lanc => {
            const categoria = lanc.categoria || 'Sem Categoria';
            const subcategoria = lanc.subcategoria || 'Sem Subcategoria';
            
            if (lanc.tipo === 'RECEITA') {
                if (!receitas[categoria]) receitas[categoria] = {};
                if (!receitas[categoria][subcategoria]) receitas[categoria][subcategoria] = 0;
                receitas[categoria][subcategoria] += lanc.valor;
            } else {
                if (!despesas[categoria]) despesas[categoria] = {};
                if (!despesas[categoria][subcategoria]) despesas[categoria][subcategoria] = 0;
                despesas[categoria][subcategoria] += lanc.valor;
            }
        });
        
        // Renderizar
        const content = document.getElementById('analise-content');
        content.innerHTML = '';
        
        // Receitas
        const receitasCard = document.createElement('div');
        receitasCard.className = 'analise-card';
        receitasCard.innerHTML = '<h3 style="color: #27ae60;">💰 RECEITAS</h3>';
        
        let totalReceitas = 0;
        Object.keys(receitas).sort().forEach(cat => {
            const catDiv = document.createElement('div');
            catDiv.className = 'analise-item';
            
            const totalCat = Object.values(receitas[cat]).reduce((a, b) => a + b, 0);
            totalReceitas += totalCat;
            
            catDiv.innerHTML = `<div class="analise-categoria">${cat} (${formatarMoeda(totalCat)})</div>`;
            
            Object.keys(receitas[cat]).sort().forEach(sub => {
                const subDiv = document.createElement('div');
                subDiv.className = 'analise-subcategoria';
                subDiv.innerHTML = `• ${sub}: ${formatarMoeda(receitas[cat][sub])}`;
                catDiv.appendChild(subDiv);
            });
            
            receitasCard.appendChild(catDiv);
        });
        
        receitasCard.innerHTML += `<div style="margin-top: 15px; padding: 15px; background: #d4edda; font-weight: bold; border-radius: 5px;">TOTAL: ${formatarMoeda(totalReceitas)}</div>`;
        content.appendChild(receitasCard);
        
        // Despesas
        const despesasCard = document.createElement('div');
        despesasCard.className = 'analise-card';
        despesasCard.innerHTML = '<h3 style="color: #e74c3c;">💳 DESPESAS</h3>';
        
        let totalDespesas = 0;
        Object.keys(despesas).sort().forEach(cat => {
            const catDiv = document.createElement('div');
            catDiv.className = 'analise-item';
            
            const totalCat = Object.values(despesas[cat]).reduce((a, b) => a + b, 0);
            totalDespesas += totalCat;
            
            catDiv.innerHTML = `<div class="analise-categoria">${cat} (${formatarMoeda(totalCat)})</div>`;
            
            Object.keys(despesas[cat]).sort().forEach(sub => {
                const subDiv = document.createElement('div');
                subDiv.className = 'analise-subcategoria';
                subDiv.innerHTML = `• ${sub}: ${formatarMoeda(despesas[cat][sub])}`;
                catDiv.appendChild(subDiv);
            });
            
            despesasCard.appendChild(catDiv);
        });
        
        despesasCard.innerHTML += `<div style="margin-top: 15px; padding: 15px; background: #f8d7da; font-weight: bold; border-radius: 5px;">TOTAL: ${formatarMoeda(totalDespesas)}</div>`;
        content.appendChild(despesasCard);
        
        // Resultado
        const resultado = totalReceitas - totalDespesas;
        const resultadoCard = document.createElement('div');
        resultadoCard.className = 'analise-card';
        resultadoCard.style.gridColumn = '1 / -1';
        resultadoCard.innerHTML = `
            <h3>📊 RESULTADO</h3>
            <div style="margin-top: 15px; padding: 20px; background: ${resultado >= 0 ? '#d4edda' : '#f8d7da'}; font-weight: bold; font-size: 18px; border-radius: 5px; text-align: center;">
                ${resultado >= 0 ? 'LUCRO' : 'PREJUÍZO'}: ${formatarMoeda(Math.abs(resultado))}
            </div>
        `;
        content.appendChild(resultadoCard);
        
    } catch (error) {
        console.error('Erro ao carregar análise de categorias:', error);
    }
}

// === INADIMPLÊNCIA ===
async function loadInadimplencia() {
    try {
        const response = await fetch(`${API_URL}/lancamentos`);
        const lancamentos = await response.json();
        
        const hoje = new Date();
        const vencidos = lancamentos.filter(l => {
            if (l.tipo !== 'RECEITA' || l.status !== 'PENDENTE') return false;
            const dataVenc = new Date(l.data_vencimento + 'T00:00:00');
            return dataVenc < hoje;
        });
        
        const tbody = document.getElementById('tbody-inadimplencia');
        tbody.innerHTML = '';
        
        vencidos.sort((a, b) => new Date(a.data_vencimento) - new Date(b.data_vencimento));
        
        vencidos.forEach(lanc => {
            const dataVenc = new Date(lanc.data_vencimento + 'T00:00:00');
            const diasAtraso = Math.floor((hoje - dataVenc) / (1000 * 60 * 60 * 24));
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${lanc.pessoa || '-'}</td>
                <td>${lanc.descricao}</td>
                <td>${formatarData(lanc.data_vencimento)}</td>
                <td style="color: ${diasAtraso > 60 ? '#c0392b' : diasAtraso > 30 ? '#e74c3c' : '#f39c12'}; font-weight: bold;">${diasAtraso}</td>
                <td style="color: #e74c3c; font-weight: bold;">${formatarMoeda(lanc.valor)}</td>
            `;
            tbody.appendChild(tr);
        });
        
        if (vencidos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 30px; color: #27ae60;">✅ Nenhuma conta vencida</td></tr>';
        }
    } catch (error) {
        console.error('Erro ao carregar inadimplência:', error);
    }
}

// === FLUXO PROJETADO ===
async function loadFluxoProjetado() {
    try {
        // Definir data padrão (90 dias à frente)
        const dataFinal = document.getElementById('projecao-data-final');
        if (!dataFinal.value) {
            const futuro = new Date();
            futuro.setDate(futuro.getDate() + 90);
            dataFinal.value = futuro.toISOString().split('T')[0];
        }
        
        const response = await fetch(`${API_URL}/relatorios/fluxo-projetado?data_final=${dataFinal.value}`);
        const dados = await response.json();
        
        // Atualizar cards
        document.getElementById('saldo-atual-projecao').textContent = formatarMoeda(dados.saldo_atual);
        document.getElementById('saldo-projetado').textContent = formatarMoeda(dados.saldo_projetado);
        
        // Preencher tabela
        const tbody = document.getElementById('tbody-projecao');
        tbody.innerHTML = '';
        
        dados.projecao.forEach(item => {
            const tr = document.createElement('tr');
            const corTipo = item.tipo === 'RECEITA' ? '#27ae60' : '#e74c3c';
            tr.innerHTML = `
                <td>${formatarData(item.data_vencimento)}</td>
                <td>${item.descricao}</td>
                <td style="color: ${corTipo}; font-weight: bold;">${item.tipo}</td>
                <td style="color: ${corTipo}; font-weight: bold;">${formatarMoeda(item.valor)}</td>
                <td>${item.categoria} - ${item.subcategoria}</td>
                <td style="font-weight: bold;">${formatarMoeda(item.saldo_projetado)}</td>
            `;
            tbody.appendChild(tr);
        });
        
        if (dados.projecao.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px;">📊 Nenhum lançamento pendente para projeção</td></tr>';
        }
    } catch (error) {
        console.error('Erro ao carregar fluxo projetado:', error);
    }
}

// === ANÁLISE DE CONTAS ===
async function loadAnaliseContas() {
    try {
        const response = await fetch(`${API_URL}/relatorios/analise-contas`);
        const dados = await response.json();
        
        // Atualizar cards
        document.getElementById('total-receber-analise').textContent = formatarMoeda(dados.total_receber);
        document.getElementById('total-pagar-analise').textContent = formatarMoeda(dados.total_pagar);
        document.getElementById('receber-vencidos').textContent = formatarMoeda(dados.receber_vencidos);
        document.getElementById('pagar-vencidos').textContent = formatarMoeda(dados.pagar_vencidos);
        
        // Preencher aging
        const tbody = document.getElementById('tbody-aging');
        tbody.innerHTML = '';
        
        const aging = [
            { periodo: '⚠️ Vencidos', valor: dados.aging.vencidos, cor: '#c0392b' },
            { periodo: '📅 Até 7 dias', valor: dados.aging.ate_7, cor: '#27ae60' },
            { periodo: '📅 8-15 dias', valor: dados.aging.ate_15, cor: '#27ae60' },
            { periodo: '📅 16-30 dias', valor: dados.aging.ate_30, cor: '#f39c12' },
            { periodo: '📅 31-60 dias', valor: dados.aging.ate_60, cor: '#e67e22' },
            { periodo: '📅 61-90 dias', valor: dados.aging.ate_90, cor: '#e74c3c' },
            { periodo: '📅 Acima de 90 dias', valor: dados.aging.acima_90, cor: '#c0392b' }
        ];
        
        aging.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="font-weight: bold;">${item.periodo}</td>
                <td style="color: ${item.cor}; font-weight: bold; font-size: 16px;">${formatarMoeda(item.valor)}</td>
            `;
            tbody.appendChild(tr);
        });
        
    } catch (error) {
        console.error('Erro ao carregar análise de contas:', error);
    }
}

// === EXPORTAÇÃO ===
function exportarFluxoExcel() {
    alert('Funcionalidade de exportação será implementada em breve!');
}

