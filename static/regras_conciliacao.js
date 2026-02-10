/**
 * 🔧 Configuração de Regras de Auto-Conciliação
 * ==============================================
 * 
 * Sistema inteligente de detecção automática para conciliação de extratos
 * 
 * Funcionalidades:
 * - Cadastro de palavras-chave
 * - Vinculação com categoria/subcategoria
 * - Integração com Folha de Pagamento (detecta CPF de funcionários)
 * - Auto-preenchimento na conciliação
 * 
 * Data: 10/02/2026
 */

const RegrasConciliacao = {
    regras: [],
    categorias: [],
    subcategorias: {},
    clientes: [],
    fornecedores: [],
    
    /**
     * Inicializa o módulo
     */
    init() {
        console.log('🔧 Inicializando Regras de Auto-Conciliação...');
        this.carregarCategorias();
        this.carregarClientesFornecedores();
        this.carregarRegras();
        this.setupEventListeners();
    },
    
    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Listener para mudança de categoria
        const categoriaSelect = document.getElementById('regra-categoria');
        if (categoriaSelect) {
            categoriaSelect.addEventListener('change', (e) => {
                this.carregarSubcategorias(e.target.value);
            });
        }
    },
    
    /**
     * Carrega categorias disponíveis
     */
    async carregarCategorias() {
        try {
            const response = await fetch(`${API_URL}/categorias`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (!response.ok) throw new Error('Erro ao carregar categorias');
            
            const data = await response.json();
            this.categorias = Array.isArray(data) ? data : (data.data || data.categorias || []);
            
            console.log(`✅ ${this.categorias.length} categorias carregadas`);
            
            // Agrupar subcategorias por categoria
            this.categorias.forEach(cat => {
                if (cat.subcategorias && cat.subcategorias.length > 0) {
                    this.subcategorias[cat.nome] = cat.subcategorias;
                }
            });
            
        } catch (error) {
            console.error('❌ Erro ao carregar categorias:', error);
            showToast('Erro ao carregar categorias', 'error');
        }
    },
    
    /**
     * Carrega clientes e fornecedores
     */
    async carregarClientesFornecedores() {
        try {
            const [responseClientes, responseFornecedores] = await Promise.all([
                fetch(`${API_URL}/clientes`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                }),
                fetch(`${API_URL}/fornecedores`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                })
            ]);
            
            if (!responseClientes.ok || !responseFornecedores.ok) {
                throw new Error('Erro ao carregar clientes/fornecedores');
            }
            
            const clientesData = await responseClientes.json();
            const fornecedoresData = await responseFornecedores.json();
            
            // Extrair arrays (pode vir como {data: [...]} ou direto)
            this.clientes = Array.isArray(clientesData) ? clientesData : (clientesData.data || clientesData.clientes || []);
            this.fornecedores = Array.isArray(fornecedoresData) ? fornecedoresData : (fornecedoresData.data || fornecedoresData.fornecedores || []);
            
            console.log(`✅ ${this.clientes.length} cliente(s) e ${this.fornecedores.length} fornecedor(es) carregados`);
            
        } catch (error) {
            console.error('❌ Erro ao carregar clientes/fornecedores:', error);
            this.clientes = [];
            this.fornecedores = [];
        }
    },
    
    /**
     * Carrega subcategorias de uma categoria específica
     */
    carregarSubcategorias(categoriaNome) {
        const subcategoriaSelect = document.getElementById('regra-subcategoria');
        if (!subcategoriaSelect) return;
        
        // Limpar opções
        subcategoriaSelect.innerHTML = '<option value="">Selecione uma subcategoria...</option>';
        
        if (!categoriaNome) {
            subcategoriaSelect.disabled = true;
            return;
        }
        
        // Buscar subcategorias
        const subs = this.subcategorias[categoriaNome] || [];
        
        if (subs.length === 0) {
            subcategoriaSelect.disabled = true;
            return;
        }
        
        // Adicionar opções
        subs.forEach(sub => {
            const option = document.createElement('option');
            option.value = sub;
            option.textContent = sub;
            subcategoriaSelect.appendChild(option);
        });
        
        subcategoriaSelect.disabled = false;
    },
    
    /**
     * Carrega regras cadastradas
     */
    async carregarRegras() {
        try {
            const response = await fetch(`${API_URL}/regras-conciliacao`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (!response.ok) throw new Error('Erro ao carregar regras');
            
            const data = await response.json();
            this.regras = data.data || [];
            
            console.log(`✅ ${this.regras.length} regra(s) carregada(s)`);
            this.renderizarRegras();
            
        } catch (error) {
            console.error('❌ Erro ao carregar regras:', error);
            showToast('Erro ao carregar regras', 'error');
        }
    },
    
    /**
     * Renderiza tabela de regras
     */
    renderizarRegras() {
        const tbody = document.getElementById('regras-lista');
        if (!tbody) return;
        
        if (this.regras.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 40px; color: #7f8c8d;">
                        <div style="font-size: 48px; margin-bottom: 10px;">📋</div>
                        <div style="font-size: 16px; font-weight: bold;">Nenhuma regra cadastrada</div>
                        <div style="font-size: 14px; margin-top: 5px;">Clique em "Nova Regra" para começar</div>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = '';
        
        this.regras.forEach(regra => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <strong>${regra.palavra_chave}</strong>
                    ${regra.descricao ? `<br><small style="color: #7f8c8d;">${regra.descricao}</small>` : ''}
                </td>
                <td>${regra.categoria || '<span style="color: #95a5a6;">-</span>'}</td>
                <td>${regra.subcategoria || '<span style="color: #95a5a6;">-</span>'}</td>
                <td>${regra.cliente_padrao || '<span style="color: #95a5a6;">-</span>'}</td>
                <td style="text-align: center;">
                    ${regra.usa_integracao_folha ? 
                        '<span class="badge badge-success" style="padding: 5px 10px; border-radius: 12px; background: #27ae60; color: white; font-size: 11px;">✅ ATIVA</span>' : 
                        '<span class="badge badge-secondary" style="padding: 5px 10px; border-radius: 12px; background: #95a5a6; color: white; font-size: 11px;">DESATIVADA</span>'}
                </td>
                <td style="text-align: center;">
                    <button class="btn-icon" onclick="RegrasConciliacao.editarRegra(${regra.id})" 
                            title="Editar" style="background: #3498db; color: white; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; margin-right: 5px;">
                        ✏️
                    </button>
                    <button class="btn-icon" onclick="RegrasConciliacao.excluirRegra(${regra.id})"
                            title="Excluir" style="background: #e74c3c; color: white; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer;">
                        🗑️
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    },
    
    /**
     * Abre modal para criar nova regra
     */
    no
    
    /**
     * Preenche select de clientes/fornecedores
     */
    preencherSelectClientesFornecedores() {
        const select = document.getElementById('regra-cliente-padrao');
        if (!select) return;
        
        select.innerHTML = '<option value="">Nenhum (deixar vazio)</option>';
        
        // Adicionar grupo de C e clientes/fornecedores
        this.preencherSelectCategorias();
        this.preencherSelectClientesFornecedore {
            const optgroupClientes = document.createElement('optgroup');
            optgroupClientes.label = '👤 Clientes';
            
            this.clientes.forEach(cliente => {
                const option = document.createElement('option');
                option.value = cliente.nome;
                option.textContent = cliente.nome;
                optgroupClientes.appendChild(option);
            });
            
            select.appendChild(optgroupClientes);
        }
        
        // Adicionar grupo de Fornecedores
        if (this.fornecedores.length > 0) {
            const optgroupFornecedores = document.createElement('optgroup');
            optgroupFornecedores.label = '🏭 Fornecedores';
            
            this.fornecedores.forEach(fornecedor => {
                const option = document.createElement('option');
                option.value = fornecedor.nome;
                option.textContent = fornecedor.nome;
                optgroupFornecedores.appendChild(option);
            });
            
            select.appendChild(optgroupFornecedores);
        }
    },vaRegra() {
        // Limpar formulário
        document.getElementById('regra-id').value = '';
        document.getElementById('regra-palavra-chave').value = '';
        document.getElementById('regra-descricao').value = '';
        document.getElementById('regra-categoria').value = '';
        document.getElementById('regra-subcategoria').value = '';
        document.getElementById('regra-subcategoria').disabled = true;
        document.getElementById('regra-cliente-padrao').value = '';
        document.getElementById('regra-integracao-folha').checked = false;
        
        // Preencher categorias
        this.preencherSelectCat e clientes/fornecedores
        this.preencherSelectCategorias();
        this.preencherSelectClientesFornecedores();
        
        // Selecionar categoria
        if (regra.categoria) {
            document.getElementById('regra-categoria').value = regra.categoria;
            this.carregarSubcategorias(regra.categoria);
            
            // Aguardar carregamento e selecionar subcategoria
            setTimeout(() => {
                if (regra.subcategoria) {
                    document.getElementById('regra-subcategoria').value = regra.subcategoria;
                }
            }, 100);
        }
        
        // Selecionar cliente padrão se houver
        if (regra.cliente_padrao) {
            // Aguardar preenchimento do select
            setTimeout(() => {
                const selectCliente = document.getElementById('regra-cliente-padrao');
                if (selectCliente) {
                    selectCliente.value = regra.cliente_padrao
        if (!select) return;
        
        select.innerHTML = '<option value="">Selecione uma categoria (opcional)...</option>';
        
        this.categorias.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.nome;
            option.textContent = `${cat.nome} (${cat.tipo})`;
            select.appendChild(option);
        });
    },
    
    /**
     * Editar regra existente
     */
    editarRegra(id) {
        const regra = this.regras.find(r => r.id === id);
        if (!regra) {
            showToast('Regra não encontrada', 'error');
            return;
        }
        
        // Preencher formulário
        document.getElementById('regra-id').value = regra.id;
        document.getElementById('regra-palavra-chave').value = regra.palavra_chave;
        document.getElementById('regra-descricao').value = regra.descricao || '';
        document.getElementById('regra-cliente-padrao').value = regra.cliente_padrao || '';
        document.getElementById('regra-integracao-folha').checked = regra.usa_integracao_folha;
        
        // Preencher categorias
        this.preencherSelectCategorias();
        
        // Selecionar categoria
        if (regra.categoria) {
            document.getElementById('regra-categoria').value = regra.categoria;
            this.carregarSubcategorias(regra.categoria);
            
            // Aguardar carregamento e selecionar subcategoria
            setTimeout(() => {
                if (regra.subcategoria) {
                    document.getElementById('regra-subcategoria').value = regra.subcategoria;
                }
            }, 100);
        }
        
        // Abrir modal
        document.getElementById('modal-regra-conciliacao').style.display = 'flex';
        document.getElementById('modal-regra-titulo').textContent = '✏️ Editar Regra de Auto-Conciliação';
    },
    
    /**
     * Salva regra (criar ou atualizar)
     */
    async salvarRegra() {
        try {
            const id = document.getElementById('regra-id').value;
            const dados = {
                palavra_chave: document.getElementById('regra-palavra-chave').value.trim().toUpperCase(),
                descricao: document.getElementById('regra-descricao').value.trim(),
                categoria: document.getElementById('regra-categoria').value,
                subcategoria: document.getElementById('regra-subcategoria').value,
                cliente_padrao: document.getElementById('regra-cliente-padrao').value.trim(),
                usa_integracao_folha: document.getElementById('regra-integracao-folha').checked
            };
            
            // Validar
            if (!dados.palavra_chave) {
                showToast('Palavra-chave é obrigatória', 'error');
                return;
            }
            
            // Se tem integração folha, avisar sobre formato de descrição
            if (dados.usa_integracao_folha) {
                console.log('🔍 Integração Folha ATIVA - Sistema detectará CPF automaticamente');
            }
            
            const url = id ? `${API_URL}/regras-conciliacao/${id}` : `${API_URL}/regras-conciliacao`;
            const method = id ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(dados)
            });
            
            if (!response.ok) throw new Error('Erro ao salvar regra');
            
            const result = await response.json();
            
            if (result.success) {
                showToast(id ? 'Regra atualizada com sucesso' : 'Regra criada com sucesso', 'success');
                this.fecharModal();
                this.carregarRegras();
            } else {
                throw new Error(result.error || 'Erro desconhecido');
            }
            
        } catch (error) {
            console.error('❌ Erro ao salvar regra:', error);
            showToast(error.message || 'Erro ao salvar regra', 'error');
        }
    },
    
    /**
     * Exclui regra
     */
    async excluirRegra(id) {
        if (!confirm('Tem certeza que deseja excluir esta regra?')) return;
        
        try {
            const response = await fetch(`${API_URL}/regras-conciliacao/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (!response.ok) throw new Error('Erro ao excluir regra');
            
            const result = await response.json();
            
            if (result.success) {
                showToast('Regra excluída com sucesso', 'success');
                this.carregarRegras();
            } else {
                throw new Error(result.error || 'Erro desconhecido');
            }
            
        } catch (error) {
            console.error('❌ Erro ao excluir regra:', error);
            showToast(error.message || 'Erro ao excluir regra', 'error');
        }
    },
    
    /**
     * Detecta regra aplicável para uma descrição
     */
    async detectarRegra(descricao) {
        try {
            const response = await fetch(`${API_URL}/regras-conciliacao/detectar`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ descricao })
            });
            
            if (!response.ok) throw new Error('Erro ao detectar regra');
            
            const result = await response.json();
            return result;
            
        } catch (error) {
            console.error('❌ Erro ao detectar regra:', error);
            return { success: false, regra_encontrada: false };
        }
    },
    
    /**
     * Fecha modal
     */
    fecharModal() {
        document.getElementById('modal-regra-conciliacao').style.display = 'none';
    }
};

// Expor globalmente
window.RegrasConciliacao = RegrasConciliacao;

// Função para abrir configuração de regras
window.abrirConfiguracaoRegras = function() {
    RegrasConciliacao.init();
    document.getElementById('modal-config-regras').style.display = 'flex';
};

console.log('✅ regras_conciliacao.js carregado com sucesso');
