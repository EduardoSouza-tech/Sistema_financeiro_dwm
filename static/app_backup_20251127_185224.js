// Sistema Financeiro - JavaScript Principal
// ==========================================

// Variáveis globais (window para acessibilidade entre arquivos)
window.categorias = [];
window.clientes = [];
window.fornecedores = [];
window.contas = [];

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('Sistema Financeiro carregado');
    loadDashboard();
    loadCategorias();
    loadClientes();
    loadFornecedores();
    loadContas();
});

// === NAVEGAÇÃO ===
function showSection(sectionName) {
    // Esconder todas as seções
    document.querySelectorAll('.content-card').forEach(section => {
        section.classList.add('hidden');
    });
    
    // Remover active de todos os botões
    document.querySelectorAll('.nav-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Mostrar seção selecionada
    const section = document.getElementById(sectionName + '-section');
    if (section) {
        section.classList.remove('hidden');
    }
    
    // Ativar botão correspondente
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Carregar dados da seção
    switch(sectionName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'contas-receber':
            loadContasReceber();
            break;
        case 'contas-pagar':
            loadContasPagar();
            break;
        case 'fluxo-caixa':
            loadFluxoCaixa();
            break;
        case 'contas-bancarias':
            loadContasBancarias();
            break;
        case 'categorias':
            loadCategoriasTable();
            break;
        case 'clientes':
            loadClientesTable();
            break;
        case 'fornecedores':
            loadFornecedoresTable();
            break;
    }
}

// === FUNÇÕES UTILITÁRIAS ===
function showAlert(message, type = 'success') {
    const alertId = type === 'success' ? 'alert-success' : 'alert-error';
    const alert = document.getElementById(alertId);
    if (alert) {
        alert.textContent = message;
        alert.style.display = 'block';
        setTimeout(() => {
            alert.style.display = 'none';
        }, 5000);
    }
}

function formatMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

function formatData(dataString) {
    if (!dataString) return '-';
    const data = new Date(dataString);
    return data.toLocaleDateString('pt-BR');
}

function getStatusColor(status) {
    switch(status) {
        case 'PENDENTE': return '#f39c12';
        case 'PAGO': return '#27ae60';
        case 'CANCELADO': return '#95a5a6';
        default: return '#2c3e50';
    }
}

// === DASHBOARD ===
async function loadDashboard() {
    try {
        const response = await fetch('/api/relatorios/dashboard');
        const data = await response.json();
        
        const statReceber = document.getElementById('stat-receber');
        const statPagar = document.getElementById('stat-pagar');
        const statSaldo = document.getElementById('stat-saldo');
        const statVencidas = document.getElementById('stat-vencidas');
        
        if (statReceber) statReceber.textContent = formatMoeda(data.contas_receber);
        if (statPagar) statPagar.textContent = formatMoeda(data.contas_pagar);
        if (statSaldo) statSaldo.textContent = formatMoeda(data.saldo_total);
        if (statVencidas) statVencidas.textContent = formatMoeda(data.contas_vencidas);
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
    }
}

// === CONTAS A RECEBER ===
async function loadContasReceber() {
    try {
        const statusFilter = document.getElementById('filter-status-receber')?.value || '';
        const categoriaFilter = document.getElementById('filter-categoria-receber')?.value || '';
        const clienteFilter = document.getElementById('filter-cliente')?.value || '';
        
        const response = await fetch('/api/lancamentos?tipo=RECEITA');
        let lancamentos = await response.json();
        
        // Aplicar filtros
        if (statusFilter) {
            lancamentos = lancamentos.filter(l => l.status === statusFilter);
        }
        if (categoriaFilter) {
            lancamentos = lancamentos.filter(l => l.categoria === categoriaFilter);
        }
        if (clienteFilter) {
            lancamentos = lancamentos.filter(l => l.pessoa === clienteFilter);
        }
        
        // Ordenar por data de vencimento
        lancamentos.sort((a, b) => new Date(a.data_vencimento) - new Date(b.data_vencimento));
        
        const tbody = document.getElementById('tbody-receber');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (lancamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state">Nenhuma receita encontrada</td></tr>';
            return;
        }
        
        lancamentos.forEach(lanc => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${formatData(lanc.data_vencimento)}</td>
                <td>${lanc.pessoa || '-'}</td>
                <td>${lanc.descricao}</td>
                <td>${lanc.categoria || '-'}</td>
                <td>${formatMoeda(lanc.valor)}</td>
                <td><span style="color: ${getStatusColor(lanc.status)}">${lanc.status}</span></td>
                <td class="action-buttons">
                    ${lanc.status === 'PENDENTE' ? `
                        <button class="btn btn-success btn-small" onclick="pagarLancamento(${lanc.id})">✓ Liquidar</button>
                    ` : ''}
                    <button class="btn btn-danger btn-small" onclick="excluirLancamento(${lanc.id}, 'RECEITA')">🗑</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar contas a receber:', error);
        showAlert('Erro ao carregar contas a receber', 'error');
    }
}

// === CONTAS A PAGAR ===
async function loadContasPagar() {
    try {
        const statusFilter = document.getElementById('filter-status-pagar')?.value || '';
        const categoriaFilter = document.getElementById('filter-categoria-pagar')?.value || '';
        const fornecedorFilter = document.getElementById('filter-fornecedor')?.value || '';
        
        const response = await fetch('/api/lancamentos?tipo=DESPESA');
        let lancamentos = await response.json();
        
        // Aplicar filtros
        if (statusFilter) {
            lancamentos = lancamentos.filter(l => l.status === statusFilter);
        }
        if (categoriaFilter) {
            lancamentos = lancamentos.filter(l => l.categoria === categoriaFilter);
        }
        if (fornecedorFilter) {
            lancamentos = lancamentos.filter(l => l.pessoa === fornecedorFilter);
        }
        
        // Ordenar por data de vencimento
        lancamentos.sort((a, b) => new Date(a.data_vencimento) - new Date(b.data_vencimento));
        
        const tbody = document.getElementById('tbody-pagar');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (lancamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state">Nenhuma despesa encontrada</td></tr>';
            return;
        }
        
        lancamentos.forEach(lanc => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${formatData(lanc.data_vencimento)}</td>
                <td>${lanc.pessoa || '-'}</td>
                <td>${lanc.descricao}</td>
                <td>${lanc.categoria || '-'}</td>
                <td>${formatMoeda(lanc.valor)}</td>
                <td><span style="color: ${getStatusColor(lanc.status)}">${lanc.status}</span></td>
                <td class="action-buttons">
                    ${lanc.status === 'PENDENTE' ? `
                        <button class="btn btn-success btn-small" onclick="pagarLancamento(${lanc.id})">✓ Liquidar</button>
                    ` : ''}
                    <button class="btn btn-danger btn-small" onclick="excluirLancamento(${lanc.id}, 'DESPESA')">🗑</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar contas a pagar:', error);
        showAlert('Erro ao carregar contas a pagar', 'error');
    }
}

// === PAGAR/EXCLUIR LANÇAMENTO ===
async function pagarLancamento(id) {
    if (!confirm('Deseja liquidar este lançamento?')) return;
    
    // Carregar contas bancárias se necessário
    if (contas.length === 0) {
        await loadContas();
    }
    
    // Selecionar conta bancária
    let contaSelecionada = '';
    if (contas.length > 0) {
        const listaContas = contas.map((c, i) => `${i+1}. ${c.nome} - ${c.banco}`).join('\n');
        const select = prompt(`Selecione a conta bancária (digite o número):\n${listaContas}`);
        if (select) {
            const index = parseInt(select) - 1;
            if (index >= 0 && index < contas.length) {
                contaSelecionada = contas[index].nome;
            }
        }
    }
    
    try {
        const response = await fetch(`/api/lancamentos/${id}/pagar`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                data_pagamento: new Date().toISOString(),
                conta_bancaria: contaSelecionada,
                juros: 0
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Lançamento liquidado com sucesso!');
            loadDashboard();
            loadContasReceber();
            loadContasPagar();
        } else {
            showAlert('Erro ao liquidar lançamento: ' + (data.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro ao pagar lançamento:', error);
        showAlert('Erro ao liquidar lançamento', 'error');
    }
}

async function excluirLancamento(id, tipo) {
    if (!confirm('Deseja realmente excluir este lançamento?')) return;
    
    try {
        const response = await fetch(`/api/lancamentos/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Lançamento excluído com sucesso!');
            loadDashboard();
            if (tipo === 'RECEITA') {
                loadContasReceber();
            } else {
                loadContasPagar();
            }
        } else {
            showAlert('Erro ao excluir lançamento: ' + (data.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro ao excluir lançamento:', error);
        showAlert('Erro ao excluir lançamento', 'error');
    }
}

// === FLUXO DE CAIXA ===
async function loadFluxoCaixa() {
    try {
        const response = await fetch('/api/relatorios/fluxo-projetado');
        const data = await response.json();
        
        const content = document.getElementById('fluxo-caixa-content');
        if (!content) return;
        
        let html = `
            <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin-bottom: 20px;">
                <div style="font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;">Saldo Atual</div>
                <div style="font-size: 32px; font-weight: bold; color: #3498db;">${formatMoeda(data.saldo_atual)}</div>
            </div>
            <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin-bottom: 20px;">
                <div style="font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;">Saldo Projetado</div>
                <div style="font-size: 32px; font-weight: bold; color: ${data.saldo_projetado >= 0 ? '#27ae60' : '#e74c3c'};">${formatMoeda(data.saldo_projetado)}</div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Descrição</th>
                        <th>Tipo</th>
                        <th>Valor</th>
                        <th>Saldo Projetado</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        if (data.projecao && data.projecao.length > 0) {
            data.projecao.forEach(item => {
                html += `
                    <tr>
                        <td>${formatData(item.data_vencimento)}</td>
                        <td>${item.descricao}</td>
                        <td><span style="color: ${item.tipo === 'RECEITA' ? '#27ae60' : '#e74c3c'}">${item.tipo}</span></td>
                        <td>${formatMoeda(item.valor)}</td>
                        <td style="font-weight: bold; color: ${item.saldo_projetado >= 0 ? '#27ae60' : '#e74c3c'};">${formatMoeda(item.saldo_projetado)}</td>
                    </tr>
                `;
            });
        } else {
            html += '<tr><td colspan="5" class="empty-state">Nenhuma projeção disponível</td></tr>';
        }
        
        html += '</tbody></table>';
        content.innerHTML = html;
    } catch (error) {
        console.error('Erro ao carregar fluxo de caixa:', error);
        const content = document.getElementById('fluxo-caixa-content');
        if (content) {
            content.innerHTML = '<div class="empty-state">Erro ao carregar dados</div>';
        }
    }
}

// === CONTAS BANCÁRIAS ===
async function loadContasBancarias() {
    try {
        const response = await fetch('/api/contas');
        const contasList = await response.json();
        
        const tbody = document.getElementById('tbody-contas');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (contasList.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhuma conta cadastrada</td></tr>';
            return;
        }
        
        contasList.forEach(conta => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${conta.nome}</td>
                <td>${conta.banco}</td>
                <td>${conta.agencia}</td>
                <td>${conta.conta}</td>
                <td>${formatMoeda(conta.saldo_inicial)}</td>
                <td>
                    <button class="btn btn-danger btn-small" onclick="excluirConta('${conta.nome}')">🗑 Excluir</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar contas:', error);
    }
}

async function excluirConta(nome) {
    if (!confirm(`Deseja realmente excluir a conta "${nome}"?`)) return;
    
    try {
        const response = await fetch(`/api/contas/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Conta excluída com sucesso!');
            loadContasBancarias();
            loadContas();
        } else {
            showAlert('Erro ao excluir conta: ' + (data.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro ao excluir conta:', error);
        showAlert('Erro ao excluir conta', 'error');
    }
}

// === CATEGORIAS ===
async function loadCategorias() {
    try {
        const response = await fetch('/api/categorias');
        window.categorias = await response.json();
        categorias = window.categorias;
        console.log('Categorias carregadas:', categorias.length, categorias);
        
        // Atualizar filtros
        const filterReceber = document.getElementById('filter-categoria-receber');
        const filterPagar = document.getElementById('filter-categoria-pagar');
        
        if (filterReceber) {
            filterReceber.innerHTML = '<option value="">Todas</option>';
            categorias.filter(c => c.tipo === 'RECEITA').forEach(cat => {
                filterReceber.innerHTML += `<option value="${cat.nome}">${cat.nome}</option>`;
            });
        }
        
        if (filterPagar) {
            filterPagar.innerHTML = '<option value="">Todas</option>';
            categorias.filter(c => c.tipo === 'DESPESA').forEach(cat => {
                filterPagar.innerHTML += `<option value="${cat.nome}">${cat.nome}</option>`;
            });
        }
    } catch (error) {
        console.error('Erro ao carregar categorias:', error);
    }
}

async function loadCategoriasTable() {
    try {
        const response = await fetch('/api/categorias');
        const categoriasList = await response.json();
        
        const tbody = document.getElementById('tbody-categorias');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (categoriasList.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-state">Nenhuma categoria cadastrada</td></tr>';
            return;
        }
        
        categoriasList.forEach(cat => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${cat.nome}</td>
                <td>${cat.tipo}</td>
                <td>${cat.subcategorias.join(', ') || '-'}</td>
                <td>
                    <button class="btn btn-danger btn-small" onclick="excluirCategoria('${cat.nome}')">🗑 Excluir</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar categorias:', error);
    }
}

async function excluirCategoria(nome) {
    if (!confirm(`Deseja realmente excluir a categoria "${nome}"?`)) return;
    
    try {
        const response = await fetch(`/api/categorias/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Categoria excluída com sucesso!');
            loadCategoriasTable();
            loadCategorias();
        } else {
            showAlert('Erro ao excluir categoria: ' + (data.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro ao excluir categoria:', error);
        showAlert('Erro ao excluir categoria', 'error');
    }
}

// === CLIENTES ===
async function loadClientes() {
    try {
        const response = await fetch('/api/clientes');
        window.clientes = await response.json();
        clientes = window.clientes;
        console.log('Clientes carregados:', clientes.length, clientes);
        
        const filterCliente = document.getElementById('filter-cliente');
        if (filterCliente) {
            filterCliente.innerHTML = '<option value="">Todos</option>';
            clientes.forEach(cli => {
                const nome = cli.razao_social || cli.nome || '';
                if (nome) {
                    filterCliente.innerHTML += `<option value="${nome}">${nome}</option>`;
                }
            });
        }
    } catch (error) {
        console.error('Erro ao carregar clientes:', error);
    }
}

async function loadClientesTable() {
    try {
        const response = await fetch('/api/clientes');
        const clientesList = await response.json();
        
        const tbody = document.getElementById('tbody-clientes');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (clientesList.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhum cliente cadastrado</td></tr>';
            return;
        }
        
        clientesList.forEach(cli => {
            const tr = document.createElement('tr');
            const nome = cli.nome || cli.razao_social || '';
            tr.innerHTML = `
                <td>${cli.razao_social || cli.nome || '-'}</td>
                <td>${cli.nome_fantasia || '-'}</td>
                <td>${cli.cnpj || '-'}</td>
                <td>${cli.cidade || '-'}</td>
                <td>${cli.telefone || cli.contato || '-'}</td>
                <td>
                    <button class="btn btn-danger btn-small" onclick="excluirCliente('${nome}')">🗑 Excluir</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar clientes:', error);
    }
}

async function excluirCliente(nome) {
    if (!confirm(`Deseja realmente excluir o cliente "${nome}"?`)) return;
    
    try {
        const response = await fetch(`/api/clientes/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Cliente excluído com sucesso!');
            loadClientesTable();
            loadClientes();
        } else {
            showAlert('Erro ao excluir cliente: ' + (data.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro ao excluir cliente:', error);
        showAlert('Erro ao excluir cliente', 'error');
    }
}

// === FORNECEDORES ===
async function loadFornecedores() {
    try {
        const response = await fetch('/api/fornecedores');
        window.fornecedores = await response.json();
        fornecedores = window.fornecedores;
        
        const filterFornecedor = document.getElementById('filter-fornecedor');
        if (filterFornecedor) {
            filterFornecedor.innerHTML = '<option value="">Todos</option>';
            fornecedores.forEach(forn => {
                const nome = forn.razao_social || forn.nome || '';
                if (nome) {
                    filterFornecedor.innerHTML += `<option value="${nome}">${nome}</option>`;
                }
            });
        }
    } catch (error) {
        console.error('Erro ao carregar fornecedores:', error);
    }
}

async function loadFornecedoresTable() {
    try {
        const response = await fetch('/api/fornecedores');
        const fornecedoresList = await response.json();
        
        const tbody = document.getElementById('tbody-fornecedores');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (fornecedoresList.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhum fornecedor cadastrado</td></tr>';
            return;
        }
        
        fornecedoresList.forEach(forn => {
            const tr = document.createElement('tr');
            const nome = forn.nome || forn.razao_social || '';
            tr.innerHTML = `
                <td>${forn.razao_social || forn.nome || '-'}</td>
                <td>${forn.nome_fantasia || '-'}</td>
                <td>${forn.cnpj || '-'}</td>
                <td>${forn.cidade || '-'}</td>
                <td>${forn.telefone || forn.contato || '-'}</td>
                <td>
                    <button class="btn btn-danger btn-small" onclick="excluirFornecedor('${nome}')">🗑 Excluir</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar fornecedores:', error);
    }
}

async function excluirFornecedor(nome) {
    if (!confirm(`Deseja realmente excluir o fornecedor "${nome}"?`)) return;
    
    try {
        const response = await fetch(`/api/fornecedores/${encodeURIComponent(nome)}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Fornecedor excluído com sucesso!');
            loadFornecedoresTable();
            loadFornecedores();
        } else {
            showAlert('Erro ao excluir fornecedor: ' + (data.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro ao excluir fornecedor:', error);
        showAlert('Erro ao excluir fornecedor', 'error');
    }
}

// === CONTAS ===
async function loadContas() {
    try {
        const response = await fetch('/api/contas');
        window.contas = await response.json();
        contas = window.contas;
    } catch (error) {
        console.error('Erro ao carregar contas:', error);
    }
}

console.log('Sistema Financeiro - app.js carregado com sucesso');

