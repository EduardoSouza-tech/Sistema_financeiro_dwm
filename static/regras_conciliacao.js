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
            console.log('📂 Carregando categorias...');
            
            const response = await fetch('/api/categorias');
            const data = await response.json();
            
            // Suporte ao novo formato de resposta
            this.categorias = Array.isArray(data) ? data : (data.data || data.categorias || []);
            
            // Organizar subcategorias por categoria
            this.subcategorias = {};
            this.categorias.forEach(cat => {
                if (cat.subcategorias) {
                    try {
                        this.subcategorias[cat.nome] = Array.isArray(cat.subcategorias) ? 
                            cat.subcategorias : JSON.parse(cat.subcategorias);
                    } catch (e) {
                        this.subcategorias[cat.nome] = [];
                    }
                } else {
                    this.subcategorias[cat.nome] = [];
                }
            });
            
            console.log(`✅ ${this.categorias.length} categoria(s) carregadas`);
            
        } catch (error) {
            console.error('❌ Erro ao carregar categorias:', error);
            this.categorias = [];
            this.subcategorias = {};
        }
    },

    /**
     * Carrega clientes e fornecedores
     */
    async carregarClientesFornecedores() {
        try {
            console.log('👥 Carregando clientes e fornecedores...');
            
            const [clientesResponse, fornecedoresResponse] = await Promise.all([
                fetch('/api/clientes'),
                fetch('/api/fornecedores')
            ]);
            
            const clientesData = await clientesResponse.json();
            const fornecedoresData = await fornecedoresResponse.json();
            
            // Suporte ao novo formato de resposta
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
        
        // Preencher opções
        subs.forEach(sub => {
            const option = document.createElement('option');
            option.value = sub;
            option.textContent = sub;
            subcategoriaSelect.appendChild(option);
        });
        
        subcategoriaSelect.disabled = false;
    },

    /**
     * Carrega regras existentes
     */
    async carregarRegras() {
        try {
            console.log('📋 Carregando regras existentes...');
            
            const response = await fetch('/api/regras-conciliacao');
            const data = await response.json();
            
            this.regras = Array.isArray(data) ? data : (data.data || data.regras || []);
            console.log(`✅ ${this.regras.length} regra(s) carregadas`);
            
        } catch (error) {
            console.error('❌ Erro ao carregar regras:', error);
            this.regras = [];
        }
    },

    /**
     * Preenche select de clientes/fornecedores
     */
    preencherSelectClientesFornecedores() {
        const select = document.getElementById('regra-cliente-padrao');
        if (!select) return;
        
        select.innerHTML = '<option value="">Nenhum (deixar vazio)</option>';
        
        // Adicionar grupo de Clientes
        if (this.clientes.length > 0) {
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
    },

    /**
     * Nova regra
     */
    novaRegra() {
        console.log('🆕 Abrindo formulário de nova regra...');
        
        // Limpar formulário
        document.getElementById('regra-id').value = '';
        document.getElementById('regra-palavra-chave').value = '';
        document.getElementById('regra-descricao').value = '';
        document.getElementById('regra-categoria').value = '';
        document.getElementById('regra-subcategoria').value = '';
        document.getElementById('regra-subcategoria').disabled = true;
        document.getElementById('regra-cliente-padrao').value = '';
        document.getElementById('regra-integracao-folha').checked = false;
        
        // Preencher selects
        this.preencherSelectCategorias();
        this.preencherSelectClientesFornecedores();
        
        // Atualizar título do modal
        document.getElementById('modal-regra-titulo').textContent = '➕ Nova Regra de Auto-Conciliação';
        
        // Abrir modal
        document.getElementById('modal-regra-conciliacao').style.display = 'flex';
        
        console.log('✅ Modal de nova regra aberto');
    },

    /**
     * Preenche select de categorias
     */
    preencherSelectCategorias() {
        const select = document.getElementById('regra-categoria');
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
            console.error('Regra não encontrada:', id);
            return;
        }

        // Preencher formulário
        document.getElementById('regra-id').value = regra.id;
        document.getElementById('regra-palavra-chave').value = regra.palavra_chave;
        document.getElementById('regra-descricao').value = regra.descricao || '';
        document.getElementById('regra-categoria').value = regra.categoria || '';
        document.getElementById('regra-subcategoria').value = regra.subcategoria || '';
        document.getElementById('regra-cliente-padrao').value = regra.cliente_padrao || '';
        document.getElementById('regra-integracao-folha').checked = regra.integracao_folha || false;
        
        // Preencher selects
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
                    selectCliente.value = regra.cliente_padrao;
                }
            }, 200);
        }
        
        // Abrir modal
        document.getElementById('modal-regra-conciliacao').style.display = 'flex';
        document.getElementById('modal-regra-titulo').textContent = '✏️ Editar Regra';  
        
        console.log('✅ Modal de edição aberto para regra:', regra);
    },
    
    /**
     * Fechar modal
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