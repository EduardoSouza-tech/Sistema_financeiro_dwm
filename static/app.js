/**
 * ============================================================================
 * SISTEMA FINANCEIRO - APLICAÇÃO PRINCIPAL
 * ============================================================================
 * Versão: 2.0.0
 * Última atualização: 2026-01-14
 * 
 * Este arquivo contém toda a lógica de frontend do sistema financeiro.
 * Estrutura modular com tratamento robusto de erros e validações completas.
 * ============================================================================
 */

// ============================================================================
// CONFIGURAÇÕES GLOBAIS
// ============================================================================

const CONFIG = {
    API_URL: window.location.origin + '/api',
    TIMEOUT: 30000, // 30 segundos
    RETRY_ATTEMPTS: 3,
    DEBOUNCE_DELAY: 300,
    DATE_FORMAT: 'pt-BR',
    CURRENCY_FORMAT: 'BRL'
};

// Expor CONFIG globalmente para lazy-loader.js e outros módulos
window.CONFIG = CONFIG;

// ============================================================================
// ESTADO GLOBAL DA APLICAÇÃO
// ============================================================================

const AppState = {
    currentPage: 'dashboard',
    contas: [],
    categorias: [],
    lancamentos: [],
    usuario: null,
    isLoading: false,
    errors: []
};

// Aliases para compatibilidade com código legado
let contas = AppState.contas;
let categorias = AppState.categorias;
let lancamentos = AppState.lancamentos;
let currentPage = AppState.currentPage;
const API_URL = CONFIG.API_URL; // Alias para código legado

// ============================================================================
// UTILITÁRIOS - TRATAMENTO DE ERROS
// ============================================================================

/**
 * Logger centralizado para erros
 * @param {string} context - Contexto onde ocorreu o erro
 * @param {Error} error - Objeto de erro
 * @param {Object} additionalData - Dados adicionais para debug
 */
function logError(context, error, additionalData = {}) {
    const errorLog = {
        timestamp: new Date().toISOString(),
        context,
        message: error.message,
        stack: error.stack,
        ...additionalData
    };
    
    console.error(`[ERRO - ${context}]`, errorLog);
    AppState.errors.push(errorLog);
    
    // Em produção, aqui você enviaria para um serviço de monitoramento
    // if (IS_PRODUCTION) sendToMonitoring(errorLog);
}

/**
 * Exibe mensagem de erro ao usuário de forma amigável
 * @param {string} message - Mensagem a ser exibida
 * @param {string} type - Tipo: 'error', 'warning', 'info', 'success'
 */
function showNotification(message, type = 'info') {
    try {
        // Remove notificações antigas
        const oldNotifications = document.querySelectorAll('.notification');
        oldNotifications.forEach(n => n.remove());
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-icon">${getNotificationIcon(type)}</span>
            <span class="notification-message">${escapeHtml(message)}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">&times;</button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remover após 5 segundos
        setTimeout(() => {
            if (notification.parentElement) {
                notification.classList.add('notification-fade-out');
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    } catch (error) {
        console.error('Erro ao exibir notificação:', error);
        // Fallback para alert nativo
        alert(message);
    }
}

/**
 * Retorna ícone baseado no tipo de notificação
 */
function getNotificationIcon(type) {
    const icons = {
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️',
        success: '✅'
    };
    return icons[type] || icons.info;
}

/**
 * Escapa HTML para prevenir XSS
 * @param {string} text - Texto a ser escapado
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Valida se um valor não é null ou undefined
 * @param {*} value - Valor a ser validado
 */
function isValidValue(value) {
    return value !== null && value !== undefined;
}

/**
 * Valida se uma string não está vazia
 * @param {string} str - String a ser validada
 */
function isNonEmptyString(str) {
    return typeof str === 'string' && str.trim().length > 0;
}

// ============================================================================
// UTILITÁRIOS - REQUISIÇÕES HTTP
// ============================================================================

/**
 * Wrapper para fetch com timeout, retry e tratamento de erros
 * @param {string} url - URL da requisição
 * @param {Object} options - Opções do fetch
 */
async function fetchWithTimeout(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), CONFIG.TIMEOUT);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        clearTimeout(timeoutId);
        
        // Verifica se a resposta é OK (200-299)
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        clearTimeout(timeoutId);
        
        if (error.name === 'AbortError') {
            throw new Error('Requisição excedeu o tempo limite. Verifique sua conexão.');
        }
        
        throw error;
    }
}

/**
 * Requisição GET com tratamento de erros
 * @param {string} endpoint - Endpoint da API
 */
async function apiGet(endpoint) {
    try {
        return await fetchWithTimeout(`${CONFIG.API_URL}${endpoint}`);
    } catch (error) {
        logError('apiGet', error, { endpoint });
        throw error;
    }
}

/**
 * Requisição POST com tratamento de erros
 * @param {string} endpoint - Endpoint da API
 * @param {Object} data - Dados a serem enviados
 */
async function apiPost(endpoint, data) {
    try {
        return await fetchWithTimeout(`${CONFIG.API_URL}${endpoint}`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    } catch (error) {
        logError('apiPost', error, { endpoint, data });
        throw error;
    }
}

/**
 * Requisição DELETE com tratamento de erros
 * @param {string} endpoint - Endpoint da API
 */
async function apiDelete(endpoint) {
    try {
        return await fetchWithTimeout(`${CONFIG.API_URL}${endpoint}`, {
            method: 'DELETE'
        });
    } catch (error) {
        logError('apiDelete', error, { endpoint });
        throw error;
    }
}

// ============================================================================
// UTILITÁRIOS - FORMATAÇÃO
// ============================================================================

/**
 * Formata valor monetário de forma segura
 * @param {number} valor - Valor a ser formatado
 * 
 * NOTA: Esta função agora usa a biblioteca utils.js (Fase 4)
 */
function formatarMoeda(valor) {
    // Delega para a função da biblioteca utils.js
    return Utils.formatarMoeda(valor);
}

/**
 * Formata data de forma segura
 * @param {string} data - Data a ser formatada
 * 
 * NOTA: Esta função agora usa a biblioteca utils.js (Fase 4)
 */
function formatarData(data) {
    // Delega para a função da biblioteca utils.js
    return Utils.formatarData(data);
}

/**
 * Valida e sanitiza valor numérico
 * @param {*} value - Valor a ser validado
 */
function sanitizeNumericValue(value) {
    const num = Number(value);
    return isNaN(num) ? 0 : num;
}

// ============================================================================
// UTILITÁRIOS - DOM
// ============================================================================

/**
 * Obtém elemento do DOM de forma segura
 * @param {string} id - ID do elemento
 * @param {string} context - Contexto para log de erro
 */
function getElement(id, context = 'getElement') {
    const element = document.getElementById(id);
    
    if (!element) {
        console.warn(`[${context}] Elemento não encontrado: ${id}`);
    }
    
    return element;
}

/**
 * Define valor de elemento de forma segura
 * @param {string} id - ID do elemento
 * @param {*} value - Valor a ser definido
 * @param {string} property - Propriedade a ser definida (textContent, innerHTML, value)
 */
function setElementValue(id, value, property = 'textContent') {
    try {
        const element = getElement(id);
        if (element && isValidValue(value)) {
            element[property] = value;
            return true;
        }
        return false;
    } catch (error) {
        logError('setElementValue', error, { id, value, property });
        return false;
    }
}

/**
 * Limpa conteúdo de elemento de forma segura
 * @param {string} id - ID do elemento
 */
function clearElement(id) {
    const element = getElement(id);
    if (element) {
        element.innerHTML = '';
        return true;
    }
    return false;
}

// ============================================================================
// INICIALIZAÇÃO DA APLICAÇÃO
// ============================================================================

/**
 * Inicializa a aplicação quando o DOM estiver pronto
 */
document.addEventListener('DOMContentLoaded', async function() {
    try {
        console.log('🚀 Inicializando Sistema Financeiro...');
        
        // 1. Inicializa sistema de permissões
        if (window.PermissionManager) {
            await window.PermissionManager.init();
        }
        
        // 2. Inicializa sistema de navegação
        if (window.NavigationManager) {
            window.NavigationManager.init();
        }
        
        // 3. Inicializa datas padrão
        initializeDefaultDates();
        
        // 4. Configura listeners da aplicação
        setupApplicationListeners();
        
        // 5. Carrega dados iniciais
        await loadInitialData();
        
        // 6. Configura listeners globais
        setupGlobalListeners();
        
        console.log('✅ Sistema Financeiro iniciado com sucesso!');
    } catch (error) {
        logError('DOMContentLoaded', error);
        showNotification('Erro ao inicializar o sistema. Por favor, recarregue a página.', 'error');
    }
});

/**
 * Inicializa datas padrão nos campos de filtro
 */
function initializeDefaultDates() {
    try {
        const hoje = new Date().toISOString().split('T')[0];
        const umMesAtras = new Date();
        umMesAtras.setMonth(umMesAtras.getMonth() - 1);
        const umMesAtrasStr = umMesAtras.toISOString().split('T')[0];
        
        const tresMesesFrente = new Date();
        tresMesesFrente.setMonth(tresMesesFrente.getMonth() + 3);
        const tresMesesFrenteStr = tresMesesFrente.toISOString().split('T')[0];
        
        // NOTA: IDs de datas alterados no HTML - filtros têm novos IDs agora
        // Se necessário no futuro, ajustar para os novos IDs:
        // - filter-data-inicial-fluxo / filter-data-final-fluxo (ao invés de fluxo-data-inicio/fim)
        // - filter-data-inicial-analise / filter-data-final-analise (ao invés de analise-data-inicio/fim)
        // setElementValue('fluxo-data-inicio', umMesAtrasStr, 'value');
        // setElementValue('fluxo-data-fim', hoje, 'value');
        // setElementValue('analise-data-inicio', umMesAtrasStr, 'value');
        // setElementValue('analise-data-fim', hoje, 'value');
        // setElementValue('projecao-data-final', tresMesesFrenteStr, 'value');
        
        // Preenche anos no comparativo de períodos
        const anoAtual = new Date().getFullYear();
        const anoAnterior = anoAtual - 1;
        
        setElementValue('filter-ano1', anoAnterior, 'value');
        setElementValue('filter-ano2', anoAtual, 'value');
    } catch (error) {
        logError('initializeDefaultDates', error);
    }
}

/**
 * Configura listeners específicos da aplicação
 * Conecta botões com data-attributes aos seus handlers
 */
function setupApplicationListeners() {
    console.log('⚙️ Configurando listeners da aplicação...');
    
    try {
        // ====================================================================
        // BOTÕES DE ABERTURA DE MODAL [data-modal]
        // ====================================================================
        document.querySelectorAll('[data-modal]').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const modalId = this.dataset.modal;
                const tipo = this.dataset.tipo; // Para lançamentos (RECEITA/DESPESA)
                
                if (window.NavigationManager) {
                    window.NavigationManager.openModal(modalId);
                }
                
                // Se for modal de lançamento, pré-seleciona o tipo
                if (modalId === 'modal-lancamento' && tipo) {
                    setTimeout(() => {
                        const tipoSelect = document.querySelector('#modal-lancamento select[name="tipo"]');
                        if (tipoSelect) tipoSelect.value = tipo;
                    }, 50);
                }
            });
        });
        
        // ====================================================================
        // BOTÕES DE FECHAR MODAL [data-close-modal]
        // ====================================================================
        document.querySelectorAll('[data-close-modal]').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const modalId = this.dataset.closeModal;
                
                if (window.NavigationManager) {
                    window.NavigationManager.closeModal(modalId);
                }
            });
        });
        
        // ====================================================================
        // BOTÕES DE AÇÃO [data-action]
        // ====================================================================
        document.querySelectorAll('[data-action]').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const action = this.dataset.action;
                
                // Mapeamento de ações
                const actionHandlers = {
                    // Exportações
                    'exportar-excel': () => window.exportarExcel?.(),
                    'exportar-pdf': () => window.exportarPDF?.(),
                    'exportar-lancamentos-excel': () => window.exportarLancamentosExcel?.(),
                    'exportar-extrato-excel': () => window.exportarExtratoExcel?.(),
                    'exportar-fluxo-excel': () => window.exportarFluxoExcel?.(),
                    
                    // Filtros
                    'aplicar-filtros-extrato': () => window.aplicarFiltrosExtrato?.(),
                    'limpar-filtros-extrato': () => window.limparFiltrosExtrato?.(),
                    
                    // Importações
                    'importar-extrato': () => window.importarExtrato?.(),
                    
                    // Atualizações
                    'atualizar-fluxo': () => window.loadFluxoCaixa?.(),
                    'atualizar-projecao': () => window.loadFluxoProjetado?.(),
                    'atualizar-analise': () => window.loadAnaliseContas?.(),
                    'atualizar-analise-categorias': () => window.loadAnaliseCategorias?.(),
                    
                    // Conciliação
                    'desconciliar': () => window.desconciliarTransacao?.(),
                    'criar-lancamento-conciliacao': () => window.criarLancamentoConciliacao?.()
                };
                
                const handler = actionHandlers[action];
                if (handler) {
                    handler();
                } else {
                    console.warn(`⚠️ Handler não encontrado para ação: ${action}`);
                }
            });
        });
        
        // ====================================================================
        // FORMULÁRIOS [data-form]
        // ====================================================================
        document.querySelectorAll('[data-form]').forEach(form => {
            form.addEventListener('submit', async function(e) {
                e.preventDefault();
                const formType = this.dataset.form;
                
                // Mapeamento de handlers de formulário
                const formHandlers = {
                    'lancamento': (e) => window.salvarLancamento?.(e),
                    'conta': (e) => window.salvarConta?.(e),
                    'categoria': (e) => window.salvarCategoria?.(e),
                    'cliente': (e) => window.salvarCliente?.(e),
                    'fornecedor': (e) => window.salvarFornecedor?.(e)
                };
                
                const handler = formHandlers[formType];
                if (handler) {
                    await handler(e);
                } else {
                    console.warn(`⚠️ Handler não encontrado para formulário: ${formType}`);
                }
            });
        });
        
        // ====================================================================
        // MUDANÇA DE CATEGORIA (carrega subcategorias)
        // ====================================================================
        const categoriaSelect = document.getElementById('select-categoria');
        if (categoriaSelect) {
            categoriaSelect.addEventListener('change', function() {
                const categoriaId = this.value;
                if (categoriaId && window.loadSubcategorias) {
                    window.loadSubcategorias(categoriaId);
                }
            });
        }
        
        console.log('✅ Listeners da aplicação configurados');
        
    } catch (error) {
        logError('setupApplicationListeners', error);
    }
}

/**
 * Carrega dados iniciais da aplicação
 */
async function loadInitialData() {
    try {
        console.log('⏳ Aguardando autenticação antes de carregar dados...');
        
        // Aguardar window.currentEmpresaId estar definido (máximo 5 segundos)
        let attempts = 0;
        while (!window.currentEmpresaId && attempts < 50) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        if (!window.currentEmpresaId) {
            console.warn('⚠️ currentEmpresaId não definido após 5 segundos. Continuando mesmo assim...');
        } else {
            console.log('✅ currentEmpresaId confirmado:', window.currentEmpresaId);
        }
        
        AppState.isLoading = true;
        
        // Carrega dados em paralelo para melhor performance
        await Promise.allSettled([
            loadDashboard(),
            loadContas(),
            loadCategorias()
        ]);
        
        AppState.isLoading = false;
    } catch (error) {
        AppState.isLoading = false;
        logError('loadInitialData', error);
        showNotification('Erro ao carregar dados iniciais', 'warning');
    }
}

/**
 * Configura listeners globais
 */
function setupGlobalListeners() {
    try {
        // Listener para tecla ESC fechar modais
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.modal.active');
                modals.forEach(modal => modal.classList.remove('active'));
            }
        });
        
        // Listener para cliques fora de modais fecharem
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('modal')) {
                e.target.classList.remove('active');
            }
        });
    } catch (error) {
        logError('setupGlobalListeners', error);
    }
}

// ============================================================================
// NAVEGAÇÃO
// ============================================================================
/**
 * Exibe uma página específica e carrega seus dados
 * @param {string} pageName - Nome da página a ser exibida
 */
function showPage(pageName) {
    try {
        if (!isNonEmptyString(pageName)) {
            throw new Error('Nome de página inválido');
        }
        
        console.log(`📄 Navegando para página: ${pageName}`);
        
        // Ocultar todas as páginas
        const pages = document.querySelectorAll('.page');
        pages.forEach(page => page.classList.remove('active'));
        
        // Mostrar página selecionada
        const targetPage = document.getElementById(`page-${pageName}`);
        if (!targetPage) {
            throw new Error(`Página não encontrada: ${pageName}`);
        }
        
        targetPage.classList.add('active');
        
        // Atualizar estado de navegação
        document.querySelectorAll('.nav-button').forEach(btn => {
            btn.classList.remove('active');
        });
        
        AppState.currentPage = pageName;
        
        // Carregar dados da página de forma assíncrona
        loadPageData(pageName).catch(error => {
            logError('loadPageData', error, { pageName });
            showNotification(`Erro ao carregar dados da página ${pageName}`, 'error');
        });
        
    } catch (error) {
        logError('showPage', error, { pageName });
        showNotification('Erro ao navegar entre páginas', 'error');
    }
}

/**
 * Carrega dados específicos de uma página
 * @param {string} pageName - Nome da página
 */
async function loadPageData(pageName) {
    const pageLoaders = {
        'dashboard': loadDashboard,
        'contas-receber': loadContasReceber,
        'contas-pagar': loadContasPagar,
        'lancamentos': loadLancamentos,
        'contas': loadContas,
        'categorias': loadCategorias,
        'clientes': loadClientes,
        'fornecedores': loadFornecedores,
        'contratos': loadContratos,
        'fluxo-caixa': loadFluxoCaixa,
        'fluxo-projetado': loadFluxoProjetado,
        'analise-contas': loadAnaliseContas,
        'extrato-bancario': async () => {
            await loadContasForExtrato();
            await loadExtratos();
        },
        'analise-categorias': loadAnaliseCategorias,
        'inadimplencia': loadInadimplencia
    };
    
    const loader = pageLoaders[pageName];
    if (loader && typeof loader === 'function') {
        await loader();
    }
}

/**
 * Toggle submenu na sidebar - DESABILITADA
 * Função movida para interface_nova.html (HEAD) com implementação correta
 * Esta versão antiga usava classList.toggle('open') que não funcionava
 */
/*
function toggleSubmenu(submenuName) {
    try {
        const submenu = getElement(`submenu-${submenuName}`, 'toggleSubmenu');
        if (submenu) {
            submenu.classList.toggle('open');
        }
    } catch (error) {
        logError('toggleSubmenu', error, { submenuName });
    }
}
*/

// ============================================================================
// MODAIS
// ============================================================================

/**
 * Exibe um modal
 * @param {string} modalId - ID do modal
 */
function showModal(modalId) {
    console.log('🔷 showModal chamada com ID:', modalId);
    try {
        const modal = getElement(modalId, 'showModal');
        console.log('   📍 Modal encontrado:', modal);
        
        if (modal) {
            console.log('   📊 Display ANTES:', modal.style.display);
            console.log('   📊 Classes ANTES:', modal.className);
            
            modal.classList.add('active');
            modal.style.display = 'flex'; // Forçar display flex para modais
            document.body.style.overflow = 'hidden'; // Previne scroll do body
            
            console.log('   📊 Display DEPOIS:', modal.style.display);
            console.log('   📊 Classes DEPOIS:', modal.className);
            console.log('   ✅ Modal deveria estar visível agora!');
        } else {
            console.error('   ❌ Modal NÃO ENCONTRADO!');
        }
    } catch (error) {
        console.error('❌ Erro em showModal:', error);
        logError('showModal', error, { modalId });
    }
}

/**
 * Fecha um modal
 * @param {string} modalId - ID do modal
 */
function closeModal(modalId) {
    try {
        console.log('🔷 closeModal chamada com ID:', modalId);
        const modal = getElement(modalId, 'closeModal');
        console.log('   📍 Modal encontrado:', modal);
        if (modal) {
            console.log('   📊 Display ANTES:', modal.style.display);
            console.log('   📊 Classes ANTES:', modal.className);
            
            modal.classList.remove('active');
            modal.style.display = 'none'; // Ocultar modal
            document.body.style.overflow = ''; // Restaura scroll
            
            console.log('   📊 Display DEPOIS:', modal.style.display);
            console.log('   📊 Classes DEPOIS:', modal.className);
            console.log('   ✅ Modal fechado!');
        } else {
            console.warn('   ⚠️ Modal não encontrado!');
        }
    } catch (error) {
        console.error('❌ Erro em closeModal:', error);
        logError('closeModal', error, { modalId });
    }
}

// Expor globalmente para uso em HTML inline
window.closeModal = closeModal;

/**
 * Abre um modal (alias para compatibilidade)
 * @param {string} modalId - ID do modal
 */
function openModal(modalId) {
    showModal(modalId);
}

// === DASHBOARD ===
// ============================================================================
// DASHBOARD
// ============================================================================

/**
 * Carrega dados do dashboard com tratamento robusto de erros
 */
async function loadDashboard() {
    const context = 'loadDashboard';
    
    try {
        console.log('📊 Carregando dashboard...');
        
        // Faz requisição com timeout
        const data = await apiGet('/relatorios/dashboard');
        
        // Valida estrutura da resposta
        if (!data || typeof data !== 'object') {
            throw new Error('Resposta inválida do servidor');
        }
        
        // NOTA: Cards do dashboard foram removidos - apenas gráfico é exibido agora
        // Se precisar atualizar elementos de resumo no futuro, descomentar:
        // const updates = {
        //     'saldo-total': formatarMoeda(sanitizeNumericValue(data.saldo_total)),
        //     'contas-receber': formatarMoeda(sanitizeNumericValue(data.contas_receber)),
        //     'contas-pagar': formatarMoeda(sanitizeNumericValue(data.contas_pagar)),
        //     'contas-vencidas': formatarMoeda(sanitizeNumericValue(data.contas_vencidas)),
        //     'total-contas': sanitizeNumericValue(data.total_contas),
        //     'total-lancamentos': sanitizeNumericValue(data.total_lancamentos)
        // };
        // Object.entries(updates).forEach(([id, value]) => {
        //     setElementValue(id, value);
        // });
        
        console.log('✅ Dashboard carregado com sucesso');
        
    } catch (error) {
        logError(context, error);
        showNotification('Erro ao carregar dados do dashboard', 'error');
        
        // NOTA: Cards removidos - valores padrão não são mais necessários
        // const defaultValues = {
        //     'saldo-total': 'R$ 0,00',
        //     'contas-receber': 'R$ 0,00',
        //     'contas-pagar': 'R$ 0,00',
        //     'contas-vencidas': 'R$ 0,00',
        //     'total-contas': '0',
        //     'total-lancamentos': '0'
        // };
        // Object.entries(defaultValues).forEach(([id, value]) => {
        //     setElementValue(id, value);
        // });
    }
}

// ============================================================================
// CONTAS BANCÁRIAS
// ============================================================================

/**
 * Carrega lista de contas bancárias com tratamento de erros
 */
async function loadContas() {
    const context = 'loadContas';
    
    try {
        console.log('🏦 Carregando contas bancárias...');
        
        const data = await apiGet('/contas');
        
        // Valida se é um array
        if (!Array.isArray(data)) {
            throw new Error('Formato de resposta inválido');
        }
        
        AppState.contas = data;
        contas = AppState.contas; // Sincroniza alias
        
        const tbody = document.getElementById('tbody-contas');
        const selectConta = document.getElementById('select-conta');
        const saldoTotalDisplay = document.getElementById('saldo-total-display');
        const filtroBanco = document.getElementById('filtro-banco');
        
        // Calcular saldo total de todas as contas
        let saldoTotal = 0;
        const bancosUnicos = new Set();
        
        // Verificar se os elementos existem antes de atualizar
        if (tbody) {
            tbody.innerHTML = '';
            
            data.forEach(conta => {
                // Somar saldo real (ou saldo_inicial se não tiver saldo_real)
                const saldoConta = conta.saldo_real !== undefined ? conta.saldo_real : conta.saldo_inicial || 0;
                saldoTotal += parseFloat(saldoConta) || 0;
                
                // Adicionar banco à lista de bancos únicos
                if (conta.banco) {
                    bancosUnicos.add(conta.banco);
                }
                
                // Tabela
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${conta.banco}</td>
                    <td>${conta.agencia}</td>
                    <td>${conta.conta}</td>
                    <td>${formatarMoeda(conta.saldo_inicial)}</td>
                    <td>${formatarMoeda(conta.saldo_real !== undefined ? conta.saldo_real : conta.saldo_inicial)}</td>
                    <td>
                        <button class="btn btn-primary" onclick="editarConta('${conta.nome}')" title="Editar conta">✏️ Editar</button>
                        <button class="btn btn-danger" onclick="excluirConta('${conta.nome}')" title="Excluir conta">🗑️ Excluir</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
        
        // Atualizar display do saldo total
        if (saldoTotalDisplay) {
            saldoTotalDisplay.textContent = formatarMoeda(saldoTotal);
        }
        
        // Atualizar filtro de bancos
        if (filtroBanco) {
            filtroBanco.innerHTML = '<option value="">Todos os Bancos</option>';
            Array.from(bancosUnicos).sort().forEach(banco => {
                const option = document.createElement('option');
                option.value = banco;
                option.textContent = banco;
                filtroBanco.appendChild(option);
            });
        }
        
        // Atualizar select de contas nos formulários
        if (selectConta) {
            selectConta.innerHTML = '<option value="">Selecione...</option>';
            
            data.forEach(conta => {
                const option = document.createElement('option');
                option.value = conta.nome;
                option.textContent = conta.nome;
                selectConta.appendChild(option);
            });
        }
        
        console.log('✅ Contas carregadas com sucesso');
        console.log('💰 Saldo total calculado:', formatarMoeda(saldoTotal));
        
    } catch (error) {
        logError(context, error);
        showNotification('Erro ao carregar contas bancárias', 'error');
    }
}

/**
 * Filtra contas bancárias por banco selecionado
 */
function filtrarPorBanco() {
    const filtroBanco = document.getElementById('filtro-banco');
    const tbody = document.getElementById('tbody-contas');
    const saldoTotalDisplay = document.getElementById('saldo-total-display');
    
    if (!filtroBanco || !tbody || !AppState.contas) return;
    
    const bancoSelecionado = filtroBanco.value;
    let saldoTotal = 0;
    
    // Limpar tabela
    tbody.innerHTML = '';
    
    // Filtrar e exibir contas
    const contasFiltradas = bancoSelecionado 
        ? AppState.contas.filter(conta => conta.banco === bancoSelecionado)
        : AppState.contas;
    
    contasFiltradas.forEach(conta => {
        // Somar saldo real (ou saldo_inicial se não tiver saldo_real)
        const saldoConta = conta.saldo_real !== undefined ? conta.saldo_real : conta.saldo_inicial || 0;
        saldoTotal += parseFloat(saldoConta) || 0;
        
        // Adicionar linha na tabela
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${conta.banco}</td>
            <td>${conta.agencia}</td>
            <td>${conta.conta}</td>
            <td>${formatarMoeda(conta.saldo_inicial)}</td>
            <td>${formatarMoeda(conta.saldo_real !== undefined ? conta.saldo_real : conta.saldo_inicial)}</td>
            <td>
                <button class="btn btn-danger" onclick="excluirConta('${conta.nome}')">🗑️</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    
    // Atualizar display do saldo total
    if (saldoTotalDisplay) {
        saldoTotalDisplay.textContent = formatarMoeda(saldoTotal);
    }
    
    console.log(`🔍 Filtro aplicado: ${bancoSelecionado || 'Todos os Bancos'}`);
    console.log(`💰 Saldo total filtrado: ${formatarMoeda(saldoTotal)}`);
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

/**
 * Atualiza saldo total de todos os bancos
 */
window.atualizarSaldoTotalBancos = async function atualizarSaldoTotalBancos(tipo) {
    try {
        console.log('🏦 atualizarSaldoTotalBancos - Buscando contas...');
        const response = await fetch(`${API_URL}/contas`);
        if (!response.ok) {
            console.error('❌ Erro ao buscar contas:', response.status);
            return;
        }
        
        const contas = await response.json();
        console.log('📦 Contas recebidas:', contas);
        console.log('📊 Primeira conta:', contas[0]);
        
        const saldoTotal = contas.reduce((sum, conta) => {
            const saldo = parseFloat(conta.saldo) || 0;
            console.log(`   💰 ${conta.nome}: R$ ${saldo.toFixed(2)} (saldo_inicial: ${conta.saldo_inicial})`);
            return sum + saldo;
        }, 0);
        
        console.log('✅ Saldo total calculado:', saldoTotal);
        
        const elementId = tipo === 'receber' ? 'saldo-total-bancos-receber' : 'saldo-total-bancos-pagar';
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = formatarMoeda(saldoTotal);
            console.log(`✅ Saldo atualizado no elemento ${elementId}:`, formatarMoeda(saldoTotal));
        } else {
            console.error(`❌ Elemento ${elementId} não encontrado`);
        }
    } catch (error) {
        console.error('❌ Erro ao atualizar saldo total:', error);
    }
}

/**
 * Carrega select de bancos
 */
window.carregarSelectBancos = async function carregarSelectBancos(tipo) {
    try {
        console.log('🏦 carregarSelectBancos - Buscando contas para select...');
        const response = await fetch(`${API_URL}/contas`);
        if (!response.ok) {
            console.error('❌ Erro ao buscar contas para select:', response.status);
            return;
        }
        
        const contas = await response.json();
        console.log('📦 Contas recebidas para select:', contas);
        
        const selectId = tipo === 'receber' ? 'select-banco-receber' : 'select-banco-pagar';
        const select = document.getElementById(selectId);
        
        if (select) {
            // Limpar opções existentes (exceto primeira)
            select.innerHTML = '<option value="">Selecione um banco</option>';
            
            // Adicionar opções
            contas.forEach(conta => {
                const option = document.createElement('option');
                option.value = conta.id;
                const textoOption = `${conta.nome} - ${formatarMoeda(conta.saldo)}`;
                option.textContent = textoOption;
                option.dataset.saldo = conta.saldo;
                console.log(`   📋 Option adicionada: ${textoOption} (saldo raw: ${conta.saldo})`);
                select.appendChild(option);
            });
            console.log(`✅ Select ${selectId} carregado com ${contas.length} bancos`);
        } else {
            console.error(`❌ Select ${selectId} não encontrado`);
        }
    } catch (error) {
        console.error('❌ Erro ao carregar select de bancos:', error);
    }
}

/**
 * Atualiza saldo do banco selecionado
 */
function atualizarSaldoBanco(tipo) {
    const selectId = tipo === 'receber' ? 'select-banco-receber' : 'select-banco-pagar';
    const saldoId = tipo === 'receber' ? 'saldo-banco-selecionado-receber' : 'saldo-banco-selecionado-pagar';
    
    const select = document.getElementById(selectId);
    const saldoDiv = document.getElementById(saldoId);
    
    if (!select || !saldoDiv) return;
    
    const selectedOption = select.options[select.selectedIndex];
    
    if (selectedOption && selectedOption.value) {
        const saldo = parseFloat(selectedOption.dataset.saldo) || 0;
        saldoDiv.textContent = formatarMoeda(saldo);
        saldoDiv.style.display = 'block';
    } else {
        saldoDiv.style.display = 'none';
    }
}

/**
 * Abre modal para editar uma conta bancária
 * @param {string} nome - Nome da conta a ser editada
 */
async function editarConta(nome) {
    try {
        console.log('🔧 editarConta chamada para:', nome);
        
        // Buscar dados da conta
        const response = await fetch(`${API_URL}/contas/${encodeURIComponent(nome)}`);
        
        if (!response.ok) {
            throw new Error('Erro ao buscar dados da conta');
        }
        
        const conta = await response.json();
        console.log('📦 Dados da conta recebidos do backend:', conta);
        console.log('   🔹 nome:', conta.nome);
        console.log('   🔹 saldo_inicial (raw):', conta.saldo_inicial, 'tipo:', typeof conta.saldo_inicial);
        console.log('   🔹 saldo (raw):', conta.saldo, 'tipo:', typeof conta.saldo);
        
        // Chamar função do modals.js para abrir modal em modo de edição
        if (typeof openModalConta === 'function') {
            openModalConta(conta);
        } else {
            console.error('Função openModalConta não encontrada');
            alert('Erro ao abrir modal de edição');
        }
    } catch (error) {
        console.error('Erro ao editar conta:', error);
        alert('Erro ao carregar dados da conta para edição');
    }
}

/**
 * Exclui uma conta bancária
 * @param {string} nome - Nome da conta a ser excluída
 */
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
    const context = 'loadCategorias';
    
    try {
        console.log('📂 Carregando categorias...');
        console.log('   🏢 window.currentEmpresaId:', window.currentEmpresaId);
        
        const data = await apiGet('/categorias');
        
        console.log('   📦 Resposta recebida:', data);
        console.log('   📊 Total de categorias:', data.length);
        
        if (!Array.isArray(data)) {
            throw new Error('Formato de resposta inválido');
        }
        
        // Log detalhado de cada categoria
        data.forEach((cat, index) => {
            console.log(`   [${index + 1}] ${cat.nome} (${cat.tipo}) - empresa_id: ${cat.empresa_id || 'N/A'}`);
            if (cat.subcategorias && cat.subcategorias.length > 0) {
                console.log(`       Subcategorias: ${cat.subcategorias.join(', ')}`);
            }
        });
        
        AppState.categorias = data;
        categorias = AppState.categorias; // Sincroniza alias
        window.categorias = data; // Expor globalmente para modals
        
        // CORREÇÃO: Usar os IDs corretos das tabelas separadas
        const tbodyReceita = document.getElementById('tbody-categorias-receita');
        const tbodyDespesa = document.getElementById('tbody-categorias-despesa');
        const selectCategoria = document.getElementById('select-categoria');
        
        console.log('   🔍 Elementos encontrados:');
        console.log('      tbody-categorias-receita:', tbodyReceita ? '✅' : '❌');
        console.log('      tbody-categorias-despesa:', tbodyDespesa ? '✅' : '❌');
        
        // Separar categorias por tipo
        const categoriasReceita = data.filter(cat => cat.tipo.toLowerCase() === 'receita');
        const categoriasDespesa = data.filter(cat => cat.tipo.toLowerCase() === 'despesa');
        
        console.log(`   📊 Receitas: ${categoriasReceita.length}, Despesas: ${categoriasDespesa.length}`);
        
        // Atualizar tabela de receitas
        if (tbodyReceita) {
            tbodyReceita.innerHTML = '';
            
            if (categoriasReceita.length === 0) {
                tbodyReceita.innerHTML = '<tr><td colspan="2">Nenhuma categoria de receita cadastrada</td></tr>';
            } else {
                categoriasReceita.forEach(cat => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${escapeHtml(cat.nome)}</td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="editarCategoria('${escapeHtml(cat.nome)}', '${escapeHtml(cat.tipo)}')" title="Editar categoria">✏️</button>
                            <button class="btn btn-sm btn-danger" onclick="excluirCategoria('${escapeHtml(cat.nome)}')" title="Excluir categoria">🗑️</button>
                        </td>
                    `;
                    tbodyReceita.appendChild(tr);
                });
            }
            console.log('   ✅ Tabela de receitas atualizada');
        } else {
            console.warn('   ⚠️ tbody-categorias-receita não encontrado!');
        }
        
        // Atualizar tabela de despesas
        if (tbodyDespesa) {
            tbodyDespesa.innerHTML = '';
            
            if (categoriasDespesa.length === 0) {
                tbodyDespesa.innerHTML = '<tr><td colspan="2">Nenhuma categoria de despesa cadastrada</td></tr>';
            } else {
                categoriasDespesa.forEach(cat => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${escapeHtml(cat.nome)}</td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="editarCategoria('${escapeHtml(cat.nome)}', '${escapeHtml(cat.tipo)}')" title="Editar categoria">✏️</button>
                            <button class="btn btn-sm btn-danger" onclick="excluirCategoria('${escapeHtml(cat.nome)}')" title="Excluir categoria">🗑️</button>
                        </td>
                    `;
                    tbodyDespesa.appendChild(tr);
                });
            }
            console.log('   ✅ Tabela de despesas atualizada');
        } else {
            console.warn('   ⚠️ tbody-categorias-despesa não encontrado!');
        }
        
        // Atualizar select de categorias nos formulários
        if (selectCategoria) {
            selectCategoria.innerHTML = '<option value="">Selecione...</option>';
            
            data.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.nome;
                option.textContent = cat.nome;
                option.dataset.subcategorias = JSON.stringify(cat.subcategorias || []);
                selectCategoria.appendChild(option);
            });
            
            // Listener para atualizar subcategorias
            selectCategoria.addEventListener('change', function() {
                const selectSubcategoria = document.getElementById('select-subcategoria');
                if (!selectSubcategoria) return;
                
                selectSubcategoria.innerHTML = '<option value="">Selecione...</option>';
                
                const selectedOption = this.options[this.selectedIndex];
                if (selectedOption && selectedOption.dataset.subcategorias) {
                    const subcats = JSON.parse(selectedOption.dataset.subcategorias);
                    subcats.forEach(sub => {
                        const option = document.createElement('option');
                        option.value = sub;
                        option.textContent = sub;
                        selectSubcategoria.appendChild(option);
                    });
                }
            });
        }
        
        console.log('✅ Categorias carregadas com sucesso');
        
    } catch (error) {
        logError(context, error);
        showNotification('Erro ao carregar categorias', 'error');
    }
}
// Expor globalmente para uso em showSection()
window.loadCategorias = loadCategorias;

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

// Função para editar categoria
async function editarCategoria(nome, tipo) {
    try {
        console.log('✏️ Editando categoria:', nome, 'Tipo:', tipo);
        
        // Validações básicas
        if (!nome) {
            showToast('Erro: Nome da categoria não informado', 'error');
            console.error('❌ Nome da categoria vazio!');
            return;
        }
        
        if (!window.currentEmpresaId) {
            showToast('Erro: Empresa não identificada. Recarregue a página.', 'error');
            console.error('❌ currentEmpresaId não definido!');
            return;
        }
        
        // Buscar dados da categoria
        const categoria = AppState.categorias.find(c => c.nome === nome);
        
        if (!categoria) {
            showToast('Erro: Categoria não encontrada', 'error');
            console.error('❌ Categoria não encontrada na lista:', nome);
            console.log('   📋 Categorias disponíveis:', AppState.categorias.map(c => c.nome));
            return;
        }
        
        console.log('✅ Categoria encontrada:', categoria);
        
        // Chamar função do modals.js para abrir modal de edição
        if (typeof openModalCategoria === 'function') {
            // Passar dados da categoria para preencher o formulário
            openModalCategoria(categoria);
            console.log('✅ Modal de edição aberto');
        } else {
            showToast('Erro: Função de edição não disponível', 'error');
            console.error('❌ Função openModalCategoria não encontrada!');
        }
        
    } catch (error) {
        console.error('❌ Erro ao editar categoria:', error);
        showToast('Erro ao abrir edição: ' + error.message, 'error');
    }
}

async function excluirCategoria(nome) {
    console.log('🗑️ excluirCategoria chamada com:', nome);
    
    if (!confirm(`Deseja realmente excluir a categoria "${nome}"?`)) {
        console.log('   ❌ Usuário cancelou');
        return;
    }
    
    try {
        // Obter CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        console.log('   🔑 CSRF Token:', csrfToken ? 'Presente' : 'AUSENTE');
        
        const url = `${API_URL}/categorias/${encodeURIComponent(nome)}`;
        console.log('   🌐 URL:', url);
        console.log('   📨 Method: DELETE');
        
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        
        console.log('   📡 Status:', response.status);
        console.log('   📡 Status Text:', response.statusText);
        
        const result = await response.json();
        console.log('   📦 Resposta:', result);
        
        if (response.ok && result.success) {
            showToast('✓ Categoria excluída com sucesso!', 'success');
            await loadCategorias();
            console.log('   ✅ Lista recarregada');
        } else {
            const errorMsg = result.error || 'Erro desconhecido';
            showToast('Erro ao excluir: ' + errorMsg, 'error');
            console.error('   ❌ Erro:', errorMsg);
        }
    } catch (error) {
        console.error('   ❌ Exception:', error);
        showToast('Erro ao excluir categoria', 'error');
    }
}

// === CLIENTES ===
async function loadClientes(ativos = true) {
    console.log('📋 Carregando clientes...', ativos ? 'Ativos' : 'Inativos');
    
    try {
        const response = await fetch(`${API_URL}/clientes?ativos=${ativos}`);
        const clientes = await response.json();
        
        console.log(`✅ ${clientes.length} clientes carregados`);
        
        // Armazenar clientes globalmente para uso nos modals
        if (ativos) {
            window.clientes = clientes;
            AppState.clientes = clientes;
        }
        
        const tbody = document.getElementById('tbody-clientes');
        if (!tbody) {
            console.warn('⚠️ tbody-clientes não encontrado, apenas armazenando dados');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (clientes.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5">${ativos ? 'Nenhum cliente ativo' : 'Nenhum cliente inativo'}</td></tr>`;
            return;
        }
        
        clientes.forEach(cliente => {
            const tr = document.createElement('tr');
            const nomeEscaped = escapeHtml(cliente.nome);
            
            // Botões diferentes para ativos e inativos
            const botoesAcao = ativos ? `
                <button class="btn btn-sm btn-primary" onclick="editarCliente('${nomeEscaped}')" title="Editar cliente">✏️</button>
                <button class="btn btn-sm btn-warning" onclick="inativarCliente('${nomeEscaped}')" title="Desativar cliente">⏸️</button>
                <button class="btn btn-sm btn-danger" onclick="excluirCliente('${nomeEscaped}')" title="Excluir cliente">🗑️</button>
            ` : `
                <button class="btn btn-sm btn-success" onclick="ativarCliente('${nomeEscaped}')" title="Reativar cliente">▶️ Ativar</button>
                <button class="btn btn-sm btn-danger" onclick="excluirCliente('${nomeEscaped}')" title="Excluir cliente">🗑️</button>
            `;
            
            tr.innerHTML = `
                <td>${cliente.nome}</td>
                <td>${cliente.documento || cliente.cpf_cnpj || '-'}</td>
                <td>${cliente.telefone || '-'}</td>
                <td>${cliente.email || '-'}</td>
                <td>${botoesAcao}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('❌ Erro ao carregar clientes:', error);
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

// Função para editar cliente
async function editarCliente(nome) {
    try {
        console.log('✏️ Editando cliente:', nome);
        
        if (!nome) {
            showToast('Erro: Nome do cliente não informado', 'error');
            return;
        }
        
        // Buscar dados do cliente
        const response = await fetch(`${API_URL}/clientes/${encodeURIComponent(nome)}`);
        const cliente = await response.json();
        
        if (!cliente) {
            showToast('Erro: Cliente não encontrado', 'error');
            return;
        }
        
        console.log('✅ Cliente encontrado:', cliente);
        
        // Chamar função do modals.js para abrir modal de edição
        if (typeof openModalCliente === 'function') {
            openModalCliente(cliente);
            console.log('✅ Modal de edição aberto');
        } else {
            showToast('Erro: Função de edição não disponível', 'error');
            console.error('❌ Função openModalCliente não encontrada!');
        }
        
    } catch (error) {
        console.error('❌ Erro ao editar cliente:', error);
        showToast('Erro ao abrir edição: ' + error.message, 'error');
    }
}
// Expor globalmente para uso em showSection()
window.loadClientes = loadClientes;

// Função para alternar abas de clientes (ativos/inativos)
function showClienteTab(tab) {
    console.log('🔄 Alternando aba de clientes:', tab);
    
    // Atualizar botões das abas
    document.querySelectorAll('.cliente-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeBtn = document.querySelector(`.cliente-tab-btn[onclick="showClienteTab('${tab}')"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // Carregar clientes filtrados por status
    const ativos = (tab === 'ativos');
    loadClientes(ativos);
    
    console.log('✅ Aba alternada:', tab, '- Ativos:', ativos);
}
// Expor globalmente para uso em onclick do HTML
window.showClienteTab = showClienteTab;

// Função para inativar cliente
async function inativarCliente(nome) {
    console.log('⏸️ inativarCliente chamada com:', nome);
    
    if (!confirm(`Deseja realmente desativar o cliente "${nome}"?`)) {
        console.log('   ❌ Usuário cancelou');
        return;
    }
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        console.log('   🔑 CSRF Token:', csrfToken ? 'Presente' : 'AUSENTE');
        
        const url = `${API_URL}/clientes/${encodeURIComponent(nome)}/inativar`;
        console.log('   🌐 URL:', url);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({})
        });
        
        console.log('   📡 Status:', response.status);
        
        const result = await response.json();
        console.log('   📦 Resposta:', result);
        
        if (response.ok && result.success) {
            showToast('✓ Cliente desativado com sucesso!', 'success');
            await loadClientes(true); // Recarregar ativos
            console.log('   ✅ Lista recarregada');
        } else {
            const errorMsg = result.error || 'Erro desconhecido';
            showToast('Erro ao desativar: ' + errorMsg, 'error');
            console.error('   ❌ Erro:', errorMsg);
        }
    } catch (error) {
        console.error('   ❌ Exception:', error);
        showToast('Erro ao desativar cliente', 'error');
    }
}

// Função para reativar cliente
async function ativarCliente(nome) {
    console.log('▶️ ativarCliente chamada com:', nome);
    
    if (!confirm(`Deseja realmente reativar o cliente "${nome}"?`)) {
        console.log('   ❌ Usuário cancelou');
        return;
    }
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        console.log('   🔑 CSRF Token:', csrfToken ? 'Presente' : 'AUSENTE');
        
        const url = `${API_URL}/clientes/${encodeURIComponent(nome)}/reativar`;
        console.log('   🌐 URL:', url);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({})
        });
        
        console.log('   📡 Status:', response.status);
        
        const result = await response.json();
        console.log('   📦 Resposta:', result);
        
        if (response.ok && result.success) {
            showToast('✓ Cliente reativado com sucesso!', 'success');
            await loadClientes(false); // Recarregar inativos
            console.log('   ✅ Lista recarregada');
        } else {
            const errorMsg = result.error || 'Erro desconhecido';
            showToast('Erro ao reativar: ' + errorMsg, 'error');
            console.error('   ❌ Erro:', errorMsg);
        }
    } catch (error) {
        console.error('   ❌ Exception:', error);
        showToast('Erro ao reativar cliente', 'error');
    }
}

async function excluirCliente(nome) {
    console.log('🗑️ excluirCliente chamada com:', nome);
    
    if (!confirm(`Deseja realmente excluir o cliente "${nome}"?`)) {
        console.log('   ❌ Usuário cancelou');
        return;
    }
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        console.log('   🔑 CSRF Token:', csrfToken ? 'Presente' : 'AUSENTE');
        
        const url = `${API_URL}/clientes/${encodeURIComponent(nome)}`;
        console.log('   🌐 URL:', url);
        
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        
        console.log('   📡 Status:', response.status);
        
        const result = await response.json();
        console.log('   📦 Resposta:', result);
        
        if (response.ok && result.success) {
            showToast('✓ Cliente excluído com sucesso!', 'success');
            await loadClientes();
            console.log('   ✅ Lista recarregada');
        } else {
            const errorMsg = result.error || 'Erro desconhecido';
            showToast('Erro ao excluir: ' + errorMsg, 'error');
            console.error('   ❌ Erro:', errorMsg);
        }
    } catch (error) {
        console.error('   ❌ Exception:', error);
        showToast('Erro ao excluir cliente', 'error');
    }
}

// === FORNECEDORES ===
async function loadFornecedores() {
    try {
        console.log('🏭 loadFornecedores - Buscando fornecedores...');
        const response = await fetch(`${API_URL}/fornecedores`);
        const fornecedores = await response.json();
        
        console.log('📦 Fornecedores recebidos:', fornecedores);
        console.log('📊 Total de fornecedores:', fornecedores.length);
        
        // Armazenar em window.fornecedores para uso nos modais
        window.fornecedores = fornecedores;
        console.log('✅ window.fornecedores definido:', window.fornecedores.length, 'fornecedores');
        
        const tbody = document.getElementById('tbody-fornecedores');
        if (!tbody) {
            console.log('⚠️ tbody-fornecedores não encontrado (provavelmente não está na página de fornecedores)');
            return;
        }
        
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
        
        console.log('✅ Tabela de fornecedores atualizada');
    } catch (error) {
        console.error('❌ Erro ao carregar fornecedores:', error);
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

async function editarFornecedor(nome) {
    try {
        console.log('✏️ Editando fornecedor:', nome);
        
        if (!nome) {
            showToast('Erro: Nome do fornecedor não informado', 'error');
            return;
        }
        
        // Buscar dados do fornecedor
        const response = await fetch(`${API_URL}/fornecedores/${encodeURIComponent(nome)}`);
        
        if (!response.ok) {
            throw new Error('Fornecedor não encontrado');
        }
        
        const fornecedor = await response.json();
        console.log('✅ Fornecedor encontrado:', fornecedor);
        
        // Abrir modal de edição
        if (typeof openModalFornecedor === 'function') {
            openModalFornecedor(fornecedor);
            console.log('✅ Modal de edição aberto');
        } else {
            showToast('Erro: Função de edição não disponível', 'error');
            console.error('❌ Função openModalFornecedor não encontrada!');
        }
        
    } catch (error) {
        console.error('❌ Erro ao editar fornecedor:', error);
        showToast('Erro ao abrir edição: ' + error.message, 'error');
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

// Função para inativar fornecedor
async function inativarFornecedor(nome) {
    console.log('⏸️ inativarFornecedor chamado com:', nome);
    
    if (!confirm(`Deseja realmente desativar o fornecedor "${nome}"?`)) {
        console.log('   ❌ Usuário cancelou');
        return;
    }
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        console.log('   🔑 CSRF Token:', csrfToken ? 'Presente' : 'AUSENTE');
        
        const url = `${API_URL}/fornecedores/${encodeURIComponent(nome)}/inativar`;
        console.log('   🌐 URL:', url);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        
        console.log('   📡 Status:', response.status);
        
        const result = await response.json();
        console.log('   📦 Resposta:', result);
        
        if (response.ok && result.success) {
            showToast('✓ Fornecedor desativado com sucesso!', 'success');
            await loadFornecedores(true); // Recarregar ativos
            console.log('   ✅ Lista recarregada');
        } else {
            const errorMsg = result.error || 'Erro desconhecido';
            showToast('Erro ao desativar: ' + errorMsg, 'error');
            console.error('   ❌ Erro:', errorMsg);
        }
    } catch (error) {
        console.error('   ❌ Exception:', error);
        showToast('Erro ao desativar fornecedor', 'error');
    }
}

// Função para reativar fornecedor
async function ativarFornecedor(nome) {
    console.log('▶️ ativarFornecedor chamado com:', nome);
    
    if (!confirm(`Deseja realmente reativar o fornecedor "${nome}"?`)) {
        console.log('   ❌ Usuário cancelou');
        return;
    }
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        console.log('   🔑 CSRF Token:', csrfToken ? 'Presente' : 'AUSENTE');
        
        const url = `${API_URL}/fornecedores/${encodeURIComponent(nome)}/reativar`;
        console.log('   🌐 URL:', url);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        
        console.log('   📡 Status:', response.status);
        
        const result = await response.json();
        console.log('   📦 Resposta:', result);
        
        if (response.ok && result.success) {
            showToast('✓ Fornecedor reativado com sucesso!', 'success');
            await loadFornecedores(false); // Recarregar inativos
            console.log('   ✅ Lista recarregada');
        } else {
            const errorMsg = result.error || 'Erro desconhecido';
            showToast('Erro ao reativar: ' + errorMsg, 'error');
            console.error('   ❌ Erro:', errorMsg);
        }
    } catch (error) {
        console.error('   ❌ Exception:', error);
        showToast('Erro ao reativar fornecedor', 'error');
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
    console.log('🔄 loadContasReceber CHAMADA!');
    try {
        console.log('   📡 Buscando lançamentos...');
        const response = await fetch(`${API_URL}/lancamentos`);
        const todosLancamentos = await response.json();
        console.log('   📦 Total de lançamentos recebidos:', todosLancamentos.length);
        if (todosLancamentos.length > 0) {
            console.log('   🔍 Exemplo de lançamento:', todosLancamentos[0]);
            console.log('   🔍 Tipos encontrados:', [...new Set(todosLancamentos.map(l => l.tipo))]);
        }
        
        const tbody = document.getElementById('tbody-receber');
        if (!tbody) {
            console.error('   ❌ Elemento tbody-receber NÃO ENCONTRADO!');
            return;
        }
        console.log('   ✅ Elemento tbody-receber encontrado');
        tbody.innerHTML = '';
        
        // Filtros (opcionais)
        const filterTextElement = document.getElementById('filter-receber');
        const filterStatusElement = document.getElementById('filter-status-receber');
        const filterText = filterTextElement ? filterTextElement.value.toLowerCase() : '';
        const filterStatus = filterStatusElement ? filterStatusElement.value : '';
        
        // Filtrar apenas receitas
        const receitas = todosLancamentos.filter(lanc => {
            const isReceita = lanc.tipo && lanc.tipo.toUpperCase() === 'RECEITA';
            const matchText = !filterText || lanc.descricao.toLowerCase().includes(filterText) || 
                             (lanc.pessoa && lanc.pessoa.toLowerCase().includes(filterText));
            const matchStatus = !filterStatus || lanc.status === filterStatus;
            return isReceita && matchText && matchStatus;
        });
        
        console.log('   💰 Total de receitas filtradas:', receitas.length);
        if (receitas.length > 0) {
            console.log('   📋 Primeira receita:', receitas[0]);
        }
        
        receitas.forEach(lanc => {
            const tr = document.createElement('tr');
            const statusClass = lanc.status && lanc.status.toUpperCase() === 'PAGO' ? 'badge-success' : 
                               lanc.status && lanc.status.toUpperCase() === 'VENCIDO' ? 'badge-danger' : 'badge-warning';
            
            tr.innerHTML = `
                <td><input type="checkbox" class="checkbox-receber" value="${lanc.id}"></td>
                <td>${formatarData(lanc.data_vencimento)}</td>
                <td>${lanc.pessoa || '-'}</td>
                <td>${lanc.id || '-'}</td>
                <td>${lanc.descricao}</td>
                <td>${lanc.categoria || '-'}</td>
                <td>${lanc.subcategoria || '-'}</td>
                <td style="font-weight: bold; color: #27ae60;">${formatarMoeda(lanc.valor)}</td>
                <td><span class="badge ${statusClass}">${lanc.status || 'PENDENTE'}</span></td>
                <td>
                    <button class="btn btn-primary" onclick="editarReceita(${lanc.id})" title="Editar">✏️</button>
                    <button class="btn btn-danger" onclick="excluirLancamento(${lanc.id})" title="Excluir">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        // Adicionar event listeners nos checkboxes
        document.querySelectorAll('.checkbox-receber').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                atualizarSomaSelecionados('receber');
                atualizarBotoesEmMassa('receber');
            });
        });
        
        if (receitas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 30px;">💰 Nenhuma conta a receber</td></tr>';
        }
        
        // Atualizar saldo total dos bancos e carregar select
        await atualizarSaldoTotalBancos('receber');
        await carregarSelectBancos('receber');
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
        
        // Filtros (opcionais)
        const filterTextElement = document.getElementById('filter-pagar');
        const filterStatusElement = document.getElementById('filter-status-pagar');
        const filterText = filterTextElement ? filterTextElement.value.toLowerCase() : '';
        const filterStatus = filterStatusElement ? filterStatusElement.value : '';
        
        // Filtrar apenas despesas
        const despesas = todosLancamentos.filter(lanc => {
            const isDespesa = lanc.tipo && lanc.tipo.toUpperCase() === 'DESPESA';
            const matchText = !filterText || lanc.descricao.toLowerCase().includes(filterText) || 
                             (lanc.pessoa && lanc.pessoa.toLowerCase().includes(filterText));
            const matchStatus = !filterStatus || lanc.status === filterStatus;
            return isDespesa && matchText && matchStatus;
        });
        
        despesas.forEach(lanc => {
            const tr = document.createElement('tr');
            const statusClass = lanc.status && lanc.status.toUpperCase() === 'PAGO' ? 'badge-success' : 
                               lanc.status && lanc.status.toUpperCase() === 'VENCIDO' ? 'badge-danger' : 'badge-warning';
            
            tr.innerHTML = `
                <td><input type="checkbox" class="checkbox-pagar" value="${lanc.id}"></td>
                <td>${formatarData(lanc.data_vencimento)}</td>
                <td>${lanc.pessoa || '-'}</td>
                <td>${lanc.id || '-'}</td>
                <td>${lanc.descricao}</td>
                <td>${lanc.categoria || '-'}</td>
                <td>${lanc.subcategoria || '-'}</td>
                <td style="font-weight: bold; color: #e74c3c;">${formatarMoeda(lanc.valor)}</td>
                <td><span class="badge ${statusClass}">${lanc.status || 'PENDENTE'}</span></td>
                <td>
                    <button class="btn btn-primary" onclick="editarDespesa(${lanc.id})" title="Editar">✏️</button>
                    <button class="btn btn-danger" onclick="excluirLancamento(${lanc.id})" title="Excluir">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        // Adicionar event listeners nos checkboxes
        document.querySelectorAll('.checkbox-pagar').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                atualizarSomaSelecionados('pagar');
                atualizarBotoesEmMassa('pagar');
            });
        });
        
        if (despesas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 30px;">💳 Nenhuma conta a pagar</td></tr>';
        }
        
        // Atualizar saldo total dos bancos e carregar select
        await atualizarSaldoTotalBancos('pagar');
        await carregarSelectBancos('pagar');
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
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        
        const response = await fetch(`${API_URL}/lancamentos/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('✓ Lançamento excluído com sucesso!', 'success');
            if (typeof loadContasReceber === 'function') loadContasReceber();
            if (typeof loadContasPagar === 'function') loadContasPagar();
            if (typeof loadDashboard === 'function') loadDashboard();
        } else {
            showToast('Erro: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Erro ao excluir lançamento:', error);
        showToast('Erro ao excluir lançamento', 'error');
    }
}

// ============================================================================
// FUNÇÕES DE SELEÇÃO EM MASSA
// ============================================================================

function toggleSelectAll(tipo) {
    const selectAllCheckbox = document.getElementById(`select-all-${tipo}`);
    const checkboxes = document.querySelectorAll(`.checkbox-${tipo}`);
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    atualizarSomaSelecionados(tipo);
    atualizarBotoesEmMassa(tipo);
}

function atualizarSomaSelecionados(tipo) {
    const checkboxes = document.querySelectorAll(`.checkbox-${tipo}:checked`);
    let soma = 0;
    
    checkboxes.forEach(checkbox => {
        const row = checkbox.closest('tr');
        const valorCell = row.querySelector('td:nth-child(8)'); // Coluna de valor
        if (valorCell) {
            const valorTexto = valorCell.textContent.replace('R$', '').replace(/\./g, '').replace(',', '.').trim();
            soma += parseFloat(valorTexto) || 0;
        }
    });
    
    const somaDiv = document.getElementById(`soma-selecionados-${tipo}`);
    const valorSpan = document.getElementById(`valor-soma-${tipo}`);
    
    if (checkboxes.length > 0) {
        somaDiv.style.display = 'block';
        valorSpan.textContent = formatarMoeda(soma);
    } else {
        somaDiv.style.display = 'none';
    }
}

function atualizarBotoesEmMassa(tipo) {
    const checkboxes = document.querySelectorAll(`.checkbox-${tipo}:checked`);
    const btnBaixar = document.getElementById(`btn-liquidar-massa-${tipo}`); // Alterado de btn-baixar para btn-liquidar
    const btnExcluir = document.getElementById(`btn-excluir-massa-${tipo}`);
    
    if (checkboxes.length > 0) {
        if (btnBaixar) btnBaixar.style.display = 'inline-block';
        if (btnExcluir) btnExcluir.style.display = 'inline-block';
    } else {
        if (btnBaixar) btnBaixar.style.display = 'none';
        if (btnExcluir) btnExcluir.style.display = 'none';
    }
}

async function baixarEmMassa(tipo) {
    const checkboxes = document.querySelectorAll(`.checkbox-${tipo === 'RECEITA' ? 'receber' : 'pagar'}:checked`);
    const ids = Array.from(checkboxes).map(cb => cb.value);
    
    if (ids.length === 0) {
        showToast('Selecione pelo menos um lançamento', 'warning');
        return;
    }
    
    if (!confirm(`Confirma baixa de ${ids.length} lançamento(s)?`)) return;
    
    try {
        let sucesso = 0;
        let erros = 0;
        
        for (const id of ids) {
            try {
                const response = await fetch(`${API_URL}/lancamentos/${id}/baixar`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ data_pagamento: new Date().toISOString().split('T')[0] })
                });
                
                const result = await response.json();
                if (result.success) sucesso++;
                else erros++;
            } catch {
                erros++;
            }
        }
        
        showToast(`✓ ${sucesso} baixado(s), ${erros} erro(s)`, sucesso > 0 ? 'success' : 'error');
        
        if (tipo === 'RECEITA') loadContasReceber();
        else loadContasPagar();
        loadDashboard();
    } catch (error) {
        console.error('Erro ao baixar em massa:', error);
        showToast('Erro ao baixar lançamentos', 'error');
    }
}

// Alias para compatibilidade com HTML
async function liquidarEmMassa(tipo) {
    return await baixarEmMassa(tipo);
}

async function excluirEmMassa(tipo) {
    const checkboxes = document.querySelectorAll(`.checkbox-${tipo === 'RECEITA' ? 'receber' : 'pagar'}:checked`);
    const ids = Array.from(checkboxes).map(cb => cb.value);
    
    if (ids.length === 0) {
        showToast('Selecione pelo menos um lançamento', 'warning');
        return;
    }
    
    if (!confirm(`ATENÇÃO: Confirma exclusão de ${ids.length} lançamento(s)? Esta ação não pode ser desfeita!`)) return;
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        let sucesso = 0;
        let erros = 0;
        
        for (const id of ids) {
            try {
                const response = await fetch(`${API_URL}/lancamentos/${id}`, { 
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    }
                });
                const result = await response.json();
                if (result.success) sucesso++;
                else erros++;
            } catch {
                erros++;
            }
        }
        
        showToast(`✓ ${sucesso} excluído(s), ${erros} erro(s)`, sucesso > 0 ? 'success' : 'error');
        
        if (tipo === 'RECEITA') loadContasReceber();
        else loadContasPagar();
        loadDashboard();
    } catch (error) {
        console.error('Erro ao excluir em massa:', error);
        showToast('Erro ao excluir lançamentos', 'error');
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
window.gerarDRE = async function() {
    try {
        if (!window.fluxoCaixaDados) {
            showToast('Carregue o fluxo de caixa primeiro', 'warning');
            return;
        }
        
        const dados = window.fluxoCaixaDados;
        const receitas = dados.totais?.receitas || 0;
        const despesas = dados.totais?.despesas || 0;
        const lucro = receitas - despesas;
        
        const dreHTML = `
            <div style="background: white; padding: 30px; border-radius: 12px; max-width: 600px; margin: 20px auto; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                <h2 style="text-align: center; color: #2c3e50; margin-bottom: 30px;">📈 DRE - Demonstrativo de Resultado</h2>
                
                <div style="margin-bottom: 20px; padding: 15px; background: #ecf0f1; border-radius: 8px;">
                    <div style="font-weight: bold; color: #27ae60; margin-bottom: 10px; font-size: 16px;">RECEITA OPERACIONAL BRUTA</div>
                    <div style="font-size: 24px; text-align: right; color: #27ae60;">${formatarMoeda(receitas)}</div>
                </div>
                
                <div style="margin-bottom: 20px; padding: 15px; background: #ecf0f1; border-radius: 8px;">
                    <div style="font-weight: bold; color: #e74c3c; margin-bottom: 10px; font-size: 16px;">(-) CUSTOS E DESPESAS</div>
                    <div style="font-size: 24px; text-align: right; color: #e74c3c;">${formatarMoeda(despesas)}</div>
                </div>
                
                <hr style="border: 2px solid #2c3e50; margin: 20px 0;">
                
                <div style="padding: 20px; background: ${lucro >= 0 ? '#d5f4e6' : '#fadbd8'}; border-radius: 8px;">
                    <div style="font-weight: bold; color: #2c3e50; margin-bottom: 10px; font-size: 18px;">${lucro >= 0 ? '✅ LUCRO' : '❌ PREJUÍZO'} LÍQUIDO DO EXERCÍCIO</div>
                    <div style="font-size: 32px; font-weight: bold; text-align: right; color: ${lucro >= 0 ? '#27ae60' : '#e74c3c'};">${formatarMoeda(Math.abs(lucro))}</div>
                </div>
                
                <div style="margin-top: 20px; text-align: center; color: #7f8c8d; font-size: 12px;">
                    Gerado em: ${new Date().toLocaleDateString('pt-BR')} às ${new Date().toLocaleTimeString('pt-BR')}
                </div>
            </div>
        `;
        
        // Criar modal para exibir DRE
        const modal = document.createElement('div');
        modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10000; display: flex; justify-content: center; align-items: center; overflow-y: auto;';
        modal.innerHTML = dreHTML + '<button onclick="this.parentElement.remove()" style="position: absolute; top: 20px; right: 20px; background: white; border: none; border-radius: 50%; width: 40px; height: 40px; font-size: 24px; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">×</button>';
        document.body.appendChild(modal);
        
    } catch (error) {
        console.error('Erro ao gerar DRE:', error);
        showToast('Erro ao gerar DRE', 'error');
    }
};

window.exportarFluxoPDF = async function() {
    try {
        if (!window.fluxoCaixaDados) {
            showToast('Carregue o fluxo de caixa primeiro', 'warning');
            return;
        }
        
        showToast('Funcionalidade PDF em desenvolvimento. Use a função de impressão do navegador (Ctrl+P)', 'info');
        
        // Criar versão para impressão
        const printWindow = window.open('', '_blank');
        const dados = window.fluxoCaixaDados;
        
        let html = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Fluxo de Caixa - ${new Date().toLocaleDateString('pt-BR')}</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    h1 { color: #2c3e50; text-align: center; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    th, td { padding: 12px; text-align: left; border: 1px solid #ddd; }
                    th { background: #3498db; color: white; }
                    .total { font-weight: bold; background: #ecf0f1; }
                    .positivo { color: #27ae60; }
                    .negativo { color: #e74c3c; }
                </style>
            </head>
            <body>
                <h1>📈 Fluxo de Caixa</h1>
                <p style="text-align: center; color: #7f8c8d;">Gerado em: ${new Date().toLocaleString('pt-BR')}</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Período</th>
                            <th style="text-align: right;">Receitas</th>
                            <th style="text-align: right;">Despesas</th>
                            <th style="text-align: right;">Saldo</th>
                        </tr>
                    </thead>
                    <tbody>`;
        
        if (dados.evolucao) {
            dados.evolucao.forEach(item => {
                html += `
                    <tr>
                        <td>${item.periodo}</td>
                        <td style="text-align: right;" class="positivo">${formatarMoeda(item.receitas)}</td>
                        <td style="text-align: right;" class="negativo">${formatarMoeda(item.despesas)}</td>
                        <td style="text-align: right;" class="${item.saldo >= 0 ? 'positivo' : 'negativo'}">${formatarMoeda(item.saldo)}</td>
                    </tr>`;
            });
        }
        
        html += `
                        <tr class="total">
                            <td><strong>TOTAL</strong></td>
                            <td style="text-align: right;" class="positivo"><strong>${formatarMoeda(dados.totais?.receitas || 0)}</strong></td>
                            <td style="text-align: right;" class="negativo"><strong>${formatarMoeda(dados.totais?.despesas || 0)}</strong></td>
                            <td style="text-align: right;" class="${(dados.totais?.saldo || 0) >= 0 ? 'positivo' : 'negativo'}"><strong>${formatarMoeda(dados.totais?.saldo || 0)}</strong></td>
                        </tr>
                    </tbody>
                </table>
            </body>
            </html>`;
        
        printWindow.document.write(html);
        printWindow.document.close();
        printWindow.focus();
        
        setTimeout(() => {
            printWindow.print();
        }, 250);
        
    } catch (error) {
        console.error('Erro ao exportar PDF:', error);
        showToast('Erro ao gerar PDF', 'error');
    }
};

function exportarFluxoExcel() {
    try {
        if (!window.fluxoCaixaDados) {
            showToast('Carregue o fluxo de caixa primeiro', 'warning');
            return;
        }
        
        const dados = window.fluxoCaixaDados;
        
        // Criar CSV (compatível com Excel)
        let csv = 'Período,Receitas,Despesas,Saldo\n';
        
        if (dados.evolucao) {
            dados.evolucao.forEach(item => {
                csv += `${item.periodo},${item.receitas.toFixed(2)},${item.despesas.toFixed(2)},${item.saldo.toFixed(2)}\n`;
            });
        }
        
        csv += `\nTOTAL,${(dados.totais?.receitas || 0).toFixed(2)},${(dados.totais?.despesas || 0).toFixed(2)},${(dados.totais?.saldo || 0).toFixed(2)}`;
        
        // Download do arquivo
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', `fluxo_caixa_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showToast('✅ Arquivo Excel exportado com sucesso!', 'success');
        
    } catch (error) {
        console.error('Erro ao exportar Excel:', error);
        showToast('Erro ao exportar para Excel', 'error');
    }
}

// === EXTRATO BANCÁRIO ===
let extratos = [];
let transacaoSelecionada = null;

// Carregar contas bancárias nos selects do extrato
async function loadContasForExtrato() {
    try {
        const response = await fetch(`${API_URL}/contas`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) throw new Error('Erro ao carregar contas');
        
        contas = await response.json();
        
        // Preencher selects
        const selectImportar = document.getElementById('extrato-conta-importar');
        const selectFiltro = document.getElementById('extrato-filter-conta');
        
        if (selectImportar) {
            selectImportar.innerHTML = '<option value="">Selecione a conta</option>';
            contas.forEach(conta => {
                selectImportar.innerHTML += `<option value="${conta.nome}">${conta.nome}</option>`;
            });
        }
        
        if (selectFiltro) {
            selectFiltro.innerHTML = '<option value="">Todas as contas</option>';
            contas.forEach(conta => {
                selectFiltro.innerHTML += `<option value="${conta.nome}">${conta.nome}</option>`;
            });
        }
        
    } catch (error) {
        console.error('Erro ao carregar contas para extrato:', error);
        showToast('Erro ao carregar contas bancárias', 'error');
    }
}

// Importar arquivo OFX
async function importarExtrato() {
    const fileInput = document.getElementById('extrato-file-input');
    const contaSelect = document.getElementById('extrato-conta-importar');
    
    if (!fileInput.files.length) {
        showToast('Selecione um arquivo OFX', 'error');
        return;
    }
    
    if (!contaSelect.value) {
        showToast('Selecione a conta bancária', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('arquivo', fileInput.files[0]);
    formData.append('conta_bancaria', contaSelect.value);
    
    try {
        showToast('Importando extrato...', 'info');
        
        const response = await fetch(`${API_URL}/extratos/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (!response.ok) throw new Error(result.error || 'Erro ao importar extrato');
        
        showToast(
            `✅ Importação concluída!\n` +
            `✔️ ${result.inseridas} transações inseridas\n` +
            `⚠️ ${result.duplicadas} transações duplicadas (ignoradas)`,
            'success'
        );
        
        // Limpar inputs
        fileInput.value = '';
        contaSelect.value = '';
        
        // Recarregar extratos
        loadExtratos();
        
    } catch (error) {
        console.error('Erro ao importar extrato:', error);
        showToast(`Erro ao importar extrato: ${error.message}`, 'error');
    }
}

// Carregar e exibir transações do extrato
async function loadExtratos() {
    try {
        console.log('📋 loadExtratos: INICIANDO carregamento de extratos...');
        
        // Obter filtros (com proteção contra null)
        const contaEl = document.getElementById('extrato-filter-conta');
        const dataInicioEl = document.getElementById('extrato-filter-data-inicio');
        const dataFimEl = document.getElementById('extrato-filter-data-fim');
        const conciliadoEl = document.getElementById('extrato-filter-conciliado');
        
        const conta = contaEl ? contaEl.value : '';
        const dataInicio = dataInicioEl ? dataInicioEl.value : '';
        const dataFim = dataFimEl ? dataFimEl.value : '';
        const conciliado = conciliadoEl ? conciliadoEl.value : '';
        
        console.log('📋 Filtros aplicados:', { conta, dataInicio, dataFim, conciliado });
        
        // Construir URL com query params
        const params = new URLSearchParams();
        if (conta) params.append('conta', conta);
        if (dataInicio) params.append('data_inicio', dataInicio);
        if (dataFim) params.append('data_fim', dataFim);
        if (conciliado) params.append('conciliado', conciliado);
        
        const url = `${API_URL}/extratos?${params.toString()}`;
        console.log('📡 Fazendo requisição para:', url);
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) throw new Error('Erro ao carregar extratos');
        
        extratos = await response.json();
        console.log(`✅ ${extratos.length} transações recebidas do backend`);
        
        // Renderizar tabela
        const tbody = document.getElementById('tbody-extratos');
        console.log('📍 Elemento tbody-extratos:', tbody);
        
        tbody.innerHTML = '';
        
        if (extratos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px;">Nenhuma transação encontrada</td></tr>';
            console.log('⚠️ Nenhuma transação para exibir');
            return;
        }
        
        console.log('🔄 Renderizando', extratos.length, 'transações...');
        
        extratos.forEach((transacao, index) => {
            console.log(`   [${index + 1}/${extratos.length}] Renderizando transação ID:`, transacao.id, 'Conciliado:', transacao.conciliado);
            
            const tr = document.createElement('tr');
            const statusIcon = transacao.conciliado ? '✅' : '⏳';
            const statusText = transacao.conciliado ? 'Conciliado' : 'Pendente';
            const statusColor = transacao.conciliado ? '#27ae60' : '#f39c12';
            
            // Determinar se é crédito ou débito (case-insensitive)
            const isCredito = transacao.tipo?.toUpperCase() === 'CREDITO' || transacao.valor > 0;
            const valorColor = isCredito ? '#27ae60' : '#c0392b';
            const tipoLabel = isCredito ? 'Crédito' : 'Débito';
            
            // Formatar valor com sinal correto
            const valorFormatado = formatarMoeda(transacao.valor);
            
            // Formatar saldo (pode ser positivo ou negativo)
            const saldoFormatado = formatarMoeda(transacao.saldo);
            const saldoColor = transacao.saldo >= 0 ? '#27ae60' : '#c0392b';
            
            // Determinar qual botão exibir
            const botaoAcao = !transacao.conciliado ? 
                `<button class="btn btn-sm btn-primary" onclick="console.log('🔵 Botão Conciliar clicado! ID:', ${transacao.id}); mostrarSugestoesConciliacao(${transacao.id})">
                    🔗 Conciliar
                </button>` 
                : 
                `<button class="btn btn-sm btn-secondary" onclick="console.log('🔵 Botão Ver clicado! ID:', ${transacao.id}); mostrarDetalheConciliacao(${transacao.id})">
                    👁️ Ver
                </button>`;
            
            console.log(`      ➡️ Botão renderizado para transação ${transacao.id}:`, transacao.conciliado ? 'Ver (conciliado)' : 'Conciliar (pendente)');
            
            tr.innerHTML = `
                <td>${formatarData(transacao.data)}</td>
                <td style="max-width: 300px;">${transacao.descricao}</td>
                <td style="color: ${valorColor}; font-weight: bold;">${valorFormatado}</td>
                <td><span class="badge badge-${isCredito ? 'success' : 'danger'}">${tipoLabel}</span></td>
                <td style="font-weight: bold; color: ${saldoColor};">${saldoFormatado}</td>
                <td>
                    <span style="color: ${statusColor}; font-weight: bold;">
                        ${statusIcon} ${statusText}
                    </span>
                </td>
                <td>
                    ${botaoAcao}
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        console.log('✅ loadExtratos: Tabela renderizada com sucesso!');
        console.log('📊 Total de linhas na tabela:', tbody.children.length);
        
    } catch (error) {
        console.error('❌ Erro ao carregar extratos:', error);
        showToast('Erro ao carregar transações do extrato', 'error');
    }
}

// Mostrar modal com sugestões de conciliação
async function mostrarSugestoesConciliacao(transacaoId) {
    try {
        console.log('🔍 mostrarSugestoesConciliacao chamada com ID:', transacaoId);
        
        // Encontrar transação no array global
        const transacao = window.extratos?.find(t => t.id === transacaoId);
        if (!transacao) {
            console.error('❌ Transação não encontrada!');
            showToast('Transação não encontrada', 'error');
            return;
        }
        
        console.log('✅ Transação encontrada:', transacao);
        console.log('   💰 Valor bruto da transação:', transacao.valor, 'tipo:', typeof transacao.valor);
        
        // Buscar categorias, clientes e fornecedores
        const [responseCategorias, responseClientes, responseFornecedores] = await Promise.all([
            fetch(`${API_URL}/categorias`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            }),
            fetch(`${API_URL}/clientes`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            }),
            fetch(`${API_URL}/fornecedores`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            })
        ]);
        
        const categorias = await responseCategorias.json();
        const clientes = await responseClientes.json();
        const fornecedores = await responseFornecedores.json();
        
        console.log('📦 Dados carregados:');
        console.log('   Categorias:', categorias.length);
        console.log('   Clientes:', clientes.length);
        console.log('   Fornecedores:', fornecedores.length);
        
        // Criar dicionário de matching CPF/CNPJ
        const clientesPorCPF = {};
        clientes.forEach(c => {
            const cpf_cnpj = (c.cpf || c.cnpj || '').replace(/\D/g, '');
            if (cpf_cnpj) clientesPorCPF[cpf_cnpj] = c.nome;
        });
        
        const fornecedoresPorCPF = {};
        fornecedores.forEach(f => {
            const cpf_cnpj = (f.cpf || f.cnpj || '').replace(/\D/g, '');
            if (cpf_cnpj) fornecedoresPorCPF[cpf_cnpj] = f.nome;
        });
        
        // Determinar tipo e cor
        console.log('🔍 Tipo da transação:', transacao.tipo);
        const isCredito = transacao.tipo?.toUpperCase() === 'CREDITO';
        console.log('   É crédito?', isCredito);
        const valorColor = isCredito ? '#27ae60' : '#e74c3c';
        
        // Tentar detectar CPF/CNPJ na descrição
        const numeros = transacao.descricao.replace(/\D/g, '');
        let razaoSugerida = '';
        if (numeros.length === 11 || numeros.length === 14) {
            razaoSugerida = isCredito ? 
                (clientesPorCPF[numeros] || '') : 
                (fornecedoresPorCPF[numeros] || '');
        }
        
        // Filtrar categorias por tipo (case-insensitive)
        const categoriasOpcoes = isCredito ? 
            categorias.filter(c => c.tipo?.toUpperCase() === 'RECEITA') : 
            categorias.filter(c => c.tipo?.toUpperCase() === 'DESPESA');
        
        console.log('📋 Categorias filtradas:', categoriasOpcoes.length);
        console.log('   Tipo buscado:', isCredito ? 'RECEITA' : 'DESPESA');
        if (categoriasOpcoes.length > 0) {
            console.log('   Primeira categoria:', categoriasOpcoes[0]);
        }
        
        // Montar formulário no estilo da conciliação geral
        const formHtml = `
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                    <div>
                        <strong>Data:</strong> ${formatarData(transacao.data)}
                    </div>
                    <div>
                        <strong>Conta:</strong> ${transacao.conta_bancaria || 'N/A'}
                    </div>
                    <div style="grid-column: 1 / -1;">
                        <strong>Descrição:</strong> ${transacao.descricao}
                    </div>
                    <div>
                        <strong>Valor:</strong> 
                        <span style="color: ${valorColor}; font-weight: bold; font-size: 18px;">
                            ${parseFloat(transacao.valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        </span>
                    </div>
                    <div>
                        <strong>Tipo:</strong>
                        <span class="badge badge-${isCredito ? 'success' : 'danger'}">
                            ${isCredito ? 'Crédito' : 'Débito'}
                        </span>
                    </div>
                </div>
            </div>
            
            <div style="background: white; border: 2px solid #ecf0f1; border-radius: 8px; padding: 20px;">
                <h3 style="margin-top: 0; color: #2c3e50;">Dados para Conciliação</h3>
                
                <div class="form-group" style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                        ${isCredito ? 'Cliente' : 'Fornecedor'} (Razão Social):
                    </label>
                    <select id="razao-individual" 
                            style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 5px; font-size: 14px;">
                        <option value="">Selecione ${isCredito ? 'o cliente' : 'o fornecedor'}...</option>
                        ${isCredito ? 
                            clientes.map(c => `<option value="${c.nome}" ${c.nome === razaoSugerida ? 'selected' : ''}>${c.nome}</option>`).join('') :
                            fornecedores.map(f => `<option value="${f.nome}" ${f.nome === razaoSugerida ? 'selected' : ''}>${f.nome}</option>`).join('')
                        }
                    </select>
                    <small style="color: #7f8c8d;">Selecione ${isCredito ? 'o cliente' : 'o fornecedor'} da lista</small>
                </div>
                
                <div class="form-group" style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Categoria:</label>
                    <select id="categoria-individual" 
                            onchange="carregarSubcategoriasIndividual(this.value)"
                            style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 5px; font-size: 14px;">
                        <option value="">Selecione a categoria...</option>
                        ${categoriasOpcoes.map(c => `<option value="${c.nome}">${c.nome}</option>`).join('')}
                    </select>
                </div>
                
                <div class="form-group" style="margin-bottom: 0;">
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Subcategoria:</label>
                    <select id="subcategoria-individual" 
                            disabled
                            style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 5px; font-size: 14px; background: #f5f5f5;">
                        <option value="">Primeiro selecione uma categoria</option>
                    </select>
                </div>
            </div>`;
        
        console.log('📝 HTML do formulário montado');
        console.log('   Tamanho do HTML:', formHtml.length, 'caracteres');
        
        const formElement = document.getElementById('transacao-conciliacao-form');
        console.log('📍 Elemento transacao-conciliacao-form:', formElement);
        
        if (!formElement) {
            console.error('❌ Elemento transacao-conciliacao-form não encontrado!');
            showToast('Erro: elemento do formulário não encontrado', 'error');
            return;
        }
        
        formElement.innerHTML = formHtml;
        console.log('✅ HTML inserido no formulário');
        
        // Verificar se os elementos foram criados
        const categoriaSelect = document.getElementById('categoria-individual');
        const subcategoriaSelect = document.getElementById('subcategoria-individual');
        console.log('🔍 Elementos após inserção:');
        console.log('   categoria-individual:', categoriaSelect, '- Opções:', categoriaSelect?.options.length);
        console.log('   subcategoria-individual:', subcategoriaSelect);
        
        // Armazenar dados para processamento
        window.transacaoIndividual = transacao;
        window.categoriasIndividual = categorias;
        
        // Mostrar modal
        showModal('modal-conciliacao');
        
        console.log('✅ Modal de conciliação individual aberto');
        
    } catch (error) {
        console.error('❌ Erro ao mostrar conciliação:', error);
        showToast('Erro ao carregar dados de conciliação', 'error');
    }
}

// Carregar subcategorias para conciliação individual
window.carregarSubcategoriasIndividual = function(categoriaNome) {
    const selectSubcat = document.getElementById('subcategoria-individual');
    
    if (!categoriaNome) {
        selectSubcat.innerHTML = '<option value="">Primeiro selecione uma categoria</option>';
        selectSubcat.disabled = true;
        return;
    }
    
    const categoria = window.categoriasIndividual.find(c => c.nome === categoriaNome);
    
    if (!categoria || !categoria.subcategorias || categoria.subcategorias.length === 0) {
        selectSubcat.innerHTML = '<option value="">Nenhuma subcategoria disponível</option>';
        selectSubcat.disabled = true;
        return;
    }
    
    selectSubcat.innerHTML = `
        <option value="">Selecione a subcategoria...</option>
        ${categoria.subcategorias.map(sub => `<option value="${sub}">${sub}</option>`).join('')}
    `;
    selectSubcat.disabled = false;
};

// Processar conciliação individual
window.conciliarTransacaoIndividual = async function() {
    console.log('🎯 conciliarTransacaoIndividual chamada!');
    try {
        const transacao = window.transacaoIndividual;
        console.log('📦 Transação armazenada:', transacao);
        
        if (!transacao) {
            console.error('❌ Transação não encontrada em window.transacaoIndividual');
            showToast('Transação não encontrada', 'error');
            return;
        }
        
        const razao = document.getElementById('razao-individual')?.value.trim();
        const categoria = document.getElementById('categoria-individual')?.value;
        const subcategoria = document.getElementById('subcategoria-individual')?.value;
        
        console.log('📝 Dados do formulário:', { razao, categoria, subcategoria });
        
        if (!categoria) {
            console.warn('⚠️ Categoria não selecionada');
            showToast('Selecione uma categoria', 'warning');
            return;
        }
        
        if (!subcategoria) {
            console.warn('⚠️ Subcategoria não selecionada');
            showToast('Selecione uma subcategoria', 'warning');
            return;
        }
        
        console.log('🚀 Conciliando transação individual:', {
            transacaoId: transacao.id,
            razao,
            categoria,
            subcategoria
        });
        
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        console.log('🔐 CSRF Token:', csrfToken ? 'Presente' : 'Ausente');
        
        console.log('📡 Enviando requisição para: /api/extratos/conciliacao-geral');
        
        // CORRIGIDO: Usar endpoint conciliacao-geral que CRIA o lançamento
        const response = await fetch(`${API_URL}/extratos/conciliacao-geral`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                transacoes: [{
                    transacao_id: transacao.id,
                    razao_social: razao,
                    categoria: categoria,
                    subcategoria: subcategoria
                }]
            })
        });
        
        console.log('📡 Response status:', response.status);
        console.log('📡 Response ok:', response.ok);
        
        if (!response.ok) {
            const error = await response.json();
            console.error('❌ Erro do servidor:', error);
            throw new Error(error.erro || 'Erro ao conciliar');
        }
        
        const result = await response.json();
        console.log('✅ Conciliação bem-sucedida:', result);
        
        showToast('✅ Transação conciliada com sucesso!', 'success');
        
        console.log('🚪 Tentando fechar modal...');
        console.log('   📍 window.closeModal existe?', typeof window.closeModal);
        console.log('   📍 closeModal existe?', typeof closeModal);
        
        // Usar explicitamente window.closeModal
        if (typeof window.closeModal === 'function') {
            console.log('   ✅ Chamando window.closeModal()');
            window.closeModal('modal-conciliacao');
        } else if (typeof closeModal === 'function') {
            console.log('   ✅ Chamando closeModal()');
            closeModal('modal-conciliacao');
        } else {
            console.error('   ❌ closeModal não encontrada!');
            // Fallback manual
            const modal = document.getElementById('modal-conciliacao');
            if (modal) {
                modal.style.display = 'none';
                modal.classList.remove('active');
                console.log('   ⚡ Modal fechado manualmente');
            }
        }
        
        console.log('🔄 Recarregando lista de extratos...');
        
        // Recarregar lista de extratos usando a função do HTML
        if (typeof window.loadExtratoTransacoes === 'function') {
            console.log('   ✅ Chamando window.loadExtratoTransacoes()');
            window.loadExtratoTransacoes();
        } else if (document.querySelector('[onclick*="loadExtratoTransacoes"]')) {
            // Se a função existir no HTML inline, recarregar a seção
            console.log('   ✅ Recarregando seção extrato-bancario');
            showSection('extrato-bancario');
        } else {
            console.warn('   ⚠️ Função loadExtratoTransacoes não encontrada');
        }
        
    } catch (error) {
        console.error('❌ ERRO CAPTURADO em conciliarTransacaoIndividual:', error);
        console.error('   Stack:', error.stack);
        showToast(error.message || 'Erro ao conciliar transação', 'error');
    }
    
    console.log('🏁 conciliarTransacaoIndividual finalizada');
};

// Desconciliar transação (desfazer conciliação)
window.desconciliarTransacao = async function(transacaoId) {
    console.log('🔙 desconciliarTransacao chamada com ID:', transacaoId);
    
    // Confirmar ação
    if (!confirm('⚠️ Deseja realmente desconciliar esta transação?\n\nIsso irá:\n- Marcar a transação como NÃO conciliada\n- EXCLUIR o lançamento criado em Contas a Pagar/Receber\n\nEsta ação não pode ser desfeita!')) {
        console.log('   ❌ Usuário cancelou a desconciliação');
        return;
    }
    
    try {
        console.log('🚀 Enviando requisição de desconciliação...');
        
        const response = await fetch(`/api/extratos/${transacaoId}/desconciliar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken || ''
            },
            credentials: 'include'
        });
        
        console.log('📡 Response status:', response.status);
        console.log('📡 Response ok:', response.ok);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao desconciliar transação');
        }
        
        const data = await response.json();
        console.log('✅ Desconciliação bem-sucedida:', data);
        
        showToast('Transação desconciliada com sucesso!', 'success');
        
        // Recarregar lista de extratos
        console.log('🔄 Recarregando lista de extratos...');
        if (typeof window.loadExtratoTransacoes === 'function') {
            console.log('   ✅ Chamando window.loadExtratoTransacoes()');
            window.loadExtratoTransacoes();
        } else {
            console.warn('   ⚠️ Função loadExtratoTransacoes não encontrada');
        }
        
    } catch (error) {
        console.error('❌ Erro ao desconciliar:', error);
        showToast(error.message || 'Erro ao desconciliar transação', 'error');
    }
    
    console.log('🏁 desconciliarTransacao finalizada');
};

// Mostrar detalhe de transação já conciliada
async function mostrarDetalheConciliacao(transacaoId) {
    try {
        const transacao = extratos.find(t => t.id === transacaoId);
        if (!transacao) throw new Error('Transação não encontrada');
        
        transacaoSelecionada = transacao;
        
        // Exibir info da transação
        const infoDiv = document.getElementById('transacao-info');
        const valorColor = transacao.tipo === 'CREDITO' ? '#27ae60' : '#c0392b';
        infoDiv.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                <div><strong>Data:</strong> ${formatarData(transacao.data)}</div>
                <div><strong>Conta:</strong> ${transacao.conta_bancaria}</div>
                <div><strong>Descrição:</strong> ${transacao.descricao}</div>
                <div><strong>Valor:</strong> <span style="color: ${valorColor}; font-weight: bold;">${formatarMoeda(transacao.valor)}</span></div>
                <div colspan="2"><strong>Status:</strong> <span style="color: #27ae60;">✅ Conciliado com lançamento #${transacao.lancamento_id}</span></div>
            </div>
        `;
        
        // Limpar sugestões
        document.getElementById('sugestoes-conciliacao').innerHTML = '<p style="text-align: center; padding: 20px; color: #27ae60;">Esta transação já está conciliada.</p>';
        
        // Exibir botão desconciliar
        document.getElementById('btn-desconciliar').style.display = 'inline-block';
        
        // Abrir modal
        showModal('modal-conciliacao');
        
    } catch (error) {
        console.error('Erro ao exibir detalhe:', error);
        showToast('Erro ao exibir detalhes da conciliação', 'error');
    }
}

// Conciliar transação com lançamento
async function conciliarTransacao(transacaoId, lancamentoId) {
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        
        const response = await fetch(`${API_URL}/extratos/${transacaoId}/conciliar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ lancamento_id: lancamentoId })
        });
        
        const result = await response.json();
        
        if (!response.ok) throw new Error(result.error || 'Erro ao conciliar');
        
        showToast('✅ Transação conciliada com sucesso!', 'success');
        
        // Fechar modal e recarregar
        closeModal('modal-conciliacao');
        
        // Só recarregar extratos se estivermos na página de extrato
        const extratoSection = document.getElementById('extrato-bancario-section');
        if (extratoSection && extratoSection.classList.contains('active')) {
            loadExtratos();
        }
        
    } catch (error) {
        console.error('Erro ao conciliar:', error);
        showToast(`Erro ao conciliar transação: ${error.message}`, 'error');
    }
}

// Desconciliar transação
async function desconciliarTransacao() {
    if (!transacaoSelecionada) return;
    
    if (!confirm('Deseja realmente desconciliar esta transação?')) return;
    
    try {
        const response = await fetch(`${API_URL}/extratos/${transacaoSelecionada.id}/conciliar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ lancamento_id: null })
        });
        
        const result = await response.json();
        
        if (!response.ok) throw new Error(result.error || 'Erro ao desconciliar');
        
        showToast('✅ Transação desconciliada!', 'success');
        
        // Fechar modal e recarregar
        closeModal('modal-conciliacao');
        loadExtratos();
        
    } catch (error) {
        console.error('Erro ao desconciliar:', error);
        showToast(`Erro ao desconciliar: ${error.message}`, 'error');
    }
}

// Aplicar filtros do extrato
function aplicarFiltrosExtrato() {
    loadExtratos();
}

// Limpar filtros do extrato
function limparFiltrosExtrato() {
    document.getElementById('extrato-filter-conta').value = '';
    document.getElementById('extrato-filter-data-inicio').value = '';
    document.getElementById('extrato-filter-data-fim').value = '';
    document.getElementById('extrato-filter-conciliado').value = '';
    loadExtratos();
}

// ============================================================================
// FUNÇÕES AUXILIARES PARA SESSÕES
// ============================================================================

/**
 * Carrega lista de funcionários/RH para uso em modais
 */
async function loadFuncionariosRH() {
    try {
        console.log('👥 Carregando funcionários para dropdown...');
        
        const response = await fetch('/api/rh/funcionarios', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao buscar funcionários');
        }
        
        const result = await response.json();
        
        if (result.success && result.data) {
            window.funcionarios = result.data;
            console.log('✅ Funcionários RH carregados:', window.funcionarios.length);
        } else {
            window.funcionarios = [];
            console.warn('⚠️ Nenhum funcionário encontrado');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar funcionários RH:', error);
        window.funcionarios = [];
    }
}

/**
 * Carrega lista de kits de equipamentos para uso em modais
 */
async function loadKits() {
    try {
        console.log('📦 Carregando kits de equipamentos...');
        
        const response = await fetch('/api/kits', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao buscar kits');
        }
        
        const result = await response.json();
        
        if (result.success && result.data) {
            window.kits = result.data;
            console.log('✅ Kits carregados:', window.kits.length);
        } else {
            window.kits = [];
            console.warn('⚠️ Nenhum kit encontrado');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar kits:', error);
        window.kits = [];
    }
}

/**
 * Carrega e renderiza tabela de kits
 */
async function loadKitsTable() {
    try {
        console.log('📦 Carregando tabela de kits...');
        
        await loadKits(); // Busca dados da API
        
        const tbody = document.getElementById('tbody-kits');
        
        if (!tbody) {
            console.warn('⚠️ Elemento tbody-kits não encontrado');
            return;
        }
        
        if (!window.kits || window.kits.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #999; padding: 20px;">Nenhum kit cadastrado</td></tr>';
            return;
        }
        
        tbody.innerHTML = window.kits.map(kit => {
            // Separar descrição e itens
            let descricaoLimpa = kit.descricao || '';
            let itensExtraidos = '';
            
            if (descricaoLimpa.includes('\n\nItens incluídos:\n')) {
                const partes = descricaoLimpa.split('\n\nItens incluídos:\n');
                descricaoLimpa = partes[0];
                itensExtraidos = partes[1] || '';
            }
            
            // Formatar preço
            const precoFormatado = kit.preco ? `R$ ${parseFloat(kit.preco).toFixed(2)}` : '-';
            
            return `
                <tr>
                    <td>${kit.nome}</td>
                    <td>${descricaoLimpa || '-'}</td>
                    <td>${itensExtraidos || '-'}</td>
                    <td>${precoFormatado}</td>
                    <td>
                        <button class="btn-icon" onclick='editarKit(${JSON.stringify(kit).replace(/'/g, "\\'")})'
                            title="Editar">✏️</button>
                        <button class="btn-icon" onclick="excluirKit(${kit.id})"
                            title="Excluir" style="color: #e74c3c;">🗑️</button>
                    </td>
                </tr>
            `;
        }).join('');
        
        console.log('✅ Tabela de kits renderizada');
    } catch (error) {
        console.error('❌ Erro ao carregar tabela de kits:', error);
        const tbody = document.getElementById('tbody-kits');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #e74c3c;">Erro ao carregar kits</td></tr>';
        }
    }
}

/**
 * Editar kit
 */
function editarKit(kit) {
    console.log('✏️ Editando kit:', kit);
    if (typeof openModalKit === 'function') {
        openModalKit(kit);
    } else {
        console.error('❌ Função openModalKit não encontrada');
        showToast('Erro: Modal de edição não disponível', 'error');
    }
}

/**
 * Excluir kit com confirmação
 */
async function excluirKit(id) {
    if (!confirm('Tem certeza que deseja excluir este kit?')) {
        return;
    }
    
    try {
        console.log(`🗑️ Excluindo kit ID: ${id}`);
        
        const response = await fetch(`/api/kits/${id}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast('✅ Kit excluído com sucesso!', 'success');
            loadKitsTable(); // Recarrega tabela
        } else {
            showToast('❌ Erro ao excluir kit: ' + (result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao excluir kit:', error);
        showToast('❌ Erro ao excluir kit: ' + error.message, 'error');
    }
}
// Expor globalmente para uso em showSection()
window.loadKitsTable = loadKitsTable;

// ============================================================================
// CONTRATOS E SESSÕES
// ============================================================================

/**
 * Carrega lista de contratos
 */
async function loadContratos() {
    const context = 'loadContratos';
    
    try {
        console.log('📋 Carregando contratos...');
        
        const contratos = await apiGet('/contratos');
        
        // Salvar em window para uso nos modais
        window.contratos = contratos;
        
        const tbody = document.getElementById('tbody-contratos');
        
        if (!tbody) {
            console.error('❌ tbody-contratos não encontrado');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (contratos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" style="text-align: center;">Nenhum contrato cadastrado</td></tr>';
            return;
        }
        
        contratos.forEach(contrato => {
            const tr = document.createElement('tr');
            
            // Preparar dados
            const dataInicio = contrato.data_inicio || contrato.data_contrato;
            const dataFormatada = dataInicio ? new Date(dataInicio).toLocaleDateString('pt-BR') : '-';
            
            tr.innerHTML = `
                <td>${escapeHtml(contrato.numero || '-')}</td>
                <td>${escapeHtml(contrato.cliente_nome || '-')}</td>
                <td><span class="badge" style="background: #3498db; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px;">${escapeHtml(contrato.tipo || '-')}</span></td>
                <td>${escapeHtml(contrato.nome || contrato.descricao || '-')}</td>
                <td>${formatarMoeda(contrato.valor_mensal || 0)}</td>
                <td style="text-align: center;">${contrato.quantidade_meses || '-'}</td>
                <td style="font-weight: bold; color: #27ae60;">${formatarMoeda(contrato.valor_total || contrato.valor || 0)}</td>
                <td>${dataFormatada}</td>
                <td><span style="font-size: 11px;">${escapeHtml(contrato.forma_pagamento || '-')}</span></td>
                <td><span class="status-badge status-${contrato.status || 'ativo'}">${contrato.status || 'Ativo'}</span></td>
                <td style="white-space: nowrap;">
                    <button class="btn btn-sm btn-primary" onclick="editarContrato(${contrato.id})" title="Editar">✏️</button>
                    <button class="btn btn-sm btn-danger" onclick="excluirContrato(${contrato.id})" title="Excluir">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        console.log('✅ Contratos carregados:', contratos.length);
        
    } catch (error) {
        logError(context, error);
        const tbody = document.getElementById('tbody-contratos');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="11" style="text-align: center; color: #e74c3c;">Erro ao carregar contratos</td></tr>';
        }
    }
}
// Expor globalmente para uso em showSection()
window.loadContratos = loadContratos;

/**
 * Carrega lista de sessões
 */
async function loadSessoes() {
    const context = 'loadSessoes';
    
    try {
        console.log('📷 Carregando sessões...');
        
        const sessoes = await apiGet('/sessoes');
        const tbody = document.getElementById('tbody-sessoes');
        
        if (!tbody) {
            console.error('❌ tbody-sessoes não encontrado');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (sessoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center;">Nenhuma sessão cadastrada</td></tr>';
            return;
        }
        
        sessoes.forEach(sessao => {
            // Tipos de captação
            const tipos = [];
            if (sessao.tipo_foto) tipos.push('Foto');
            if (sessao.tipo_video) tipos.push('Vídeo');
            if (sessao.tipo_mobile) tipos.push('Mobile');
            const tiposCaptacao = tipos.join(', ') || '-';
            
            // Status baseado no prazo
            let statusClass = 'badge-success';
            let statusText = 'No Prazo';
            const hoje = new Date();
            const prazo = sessao.prazo_entrega ? new Date(sessao.prazo_entrega) : null;
            
            if (prazo) {
                const diffDias = Math.ceil((prazo - hoje) / (1000 * 60 * 60 * 24));
                if (diffDias < 0) {
                    statusClass = 'badge-danger';
                    statusText = 'Atrasado';
                } else if (diffDias <= 3) {
                    statusClass = 'badge-warning';
                    statusText = 'Urgente';
                }
            }
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${sessao.data ? new Date(sessao.data).toLocaleDateString('pt-BR') : '-'}</td>
                <td>${escapeHtml(sessao.horario || '-')}</td>
                <td>${escapeHtml(sessao.cliente_nome || '-')}</td>
                <td>${escapeHtml(sessao.contrato_nome || '-')}</td>
                <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(sessao.endereco || '')}">${escapeHtml(sessao.endereco || '-')}</td>
                <td>${tiposCaptacao}</td>
                <td>${sessao.prazo_entrega ? new Date(sessao.prazo_entrega).toLocaleDateString('pt-BR') : '-'}</td>
                <td><span class="badge ${statusClass}">${statusText}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="editarSessao(${sessao.id})" title="Editar">✏️</button>
                    <button class="btn btn-sm btn-danger" onclick="excluirSessao(${sessao.id})" title="Excluir">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        console.log('✅ Sessões carregadas:', sessoes.length);
        
    } catch (error) {
        logError(context, error);
        const tbody = document.getElementById('tbody-sessoes');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: #e74c3c;">Erro ao carregar sessões</td></tr>';
        }
    }
}

/**
 * Carrega lista de comissões
 */
async function loadComissoes() {
    const context = 'loadComissoes';
    
    try {
        console.log('💰 Carregando comissões...');
        
        const comissoes = await apiGet('/comissoes');
        const tbody = document.getElementById('tbody-comissoes');
        
        if (!tbody) {
            console.error('❌ tbody-comissoes não encontrado');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (comissoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Nenhuma comissão cadastrada</td></tr>';
            return;
        }
        
        comissoes.forEach(comissao => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${escapeHtml(comissao.contrato_numero || '-')}</td>
                <td>${escapeHtml(comissao.cliente_nome || '')}</td>
                <td>${escapeHtml(comissao.tipo || '')}</td>
                <td>${formatarMoeda(comissao.valor || 0)}</td>
                <td>${comissao.percentual || 0}%</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="editarComissao(${comissao.id})" title="Editar">✏️</button>
                    <button class="btn btn-sm btn-danger" onclick="excluirComissao(${comissao.id})" title="Excluir">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        console.log('✅ Comissões carregadas:', comissoes.length);
        
    } catch (error) {
        logError(context, error);
        const tbody = document.getElementById('tbody-comissoes');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #e74c3c;">Erro ao carregar comissões</td></tr>';
        }
    }
}

// Funções auxiliares de contratos
async function editarContrato(id) {
    console.log('🔧 Editar contrato:', id);
    
    try {
        // Buscar dados do contrato
        const response = await fetch(`/api/contratos/${id}`);
        if (!response.ok) {
            throw new Error('Erro ao buscar contrato');
        }
        
        const result = await response.json();
        const contrato = result.contrato || result;
        
        console.log('📋 Dados do contrato:', contrato);
        
        // Abrir modal de edição
        if (typeof window.openModalContrato === 'function') {
            window.openModalContrato(contrato);
        } else {
            showToast('❌ Erro: Função openModalContrato não encontrada', 'error');
        }
        
    } catch (error) {
        console.error('❌ Erro ao editar contrato:', error);
        showToast('❌ Erro ao carregar dados do contrato: ' + error.message, 'error');
    }
}

async function excluirContrato(id) {
    if (!confirm('⚠️ Tem certeza que deseja excluir este contrato?\n\nEsta ação não pode ser desfeita!')) {
        return;
    }
    
    console.log('🗑️ Excluir contrato:', id);
    
    try {
        const response = await fetch(`/api/contratos/${id}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (result.success || response.ok) {
            showToast('✅ Contrato excluído com sucesso!', 'success');
            loadContratos(); // Recarregar lista
        } else {
            showToast('❌ Erro ao excluir contrato: ' + (result.error || 'Erro desconhecido'), 'error');
        }
        
    } catch (error) {
        console.error('❌ Erro ao excluir contrato:', error);
        showToast('❌ Erro ao excluir contrato: ' + error.message, 'error');
    }
}

async function editarSessao(id) {
    console.log('🔧 Editar sessão:', id);
    
    try {
        const response = await fetch(`/api/sessoes/${id}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        console.log('📋 Dados da sessão:', result);
        
        if (result.success && result.data) {
            window.openModalSessao(result.data);
        } else {
            showToast('❌ Erro ao carregar dados da sessão', 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao buscar sessão:', error);
        showToast('❌ Erro ao carregar sessão: ' + error.message, 'error');
    }
}

async function excluirSessao(id) {
    if (!confirm('Tem certeza que deseja excluir esta sessão?')) {
        return;
    }
    
    console.log('🗑️ Excluir sessão:', id);
    
    try {
        const response = await fetch(`/api/sessoes/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('✅ Sessão excluída com sucesso!', 'success');
            loadSessoes();
        } else {
            showToast('❌ Erro ao excluir sessão: ' + (result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao excluir sessão:', error);
        showToast('❌ Erro ao excluir sessão: ' + error.message, 'error');
    }
}

async function editarComissao(id) {
    try {
        console.log('🔧 Editando comissão ID:', id);
        
        // Buscar dados da comissão
        const response = await fetch(`/api/comissoes/${id}`);
        
        if (!response.ok) {
            throw new Error('Comissão não encontrada');
        }
        
        const result = await response.json();
        console.log('📋 Dados da comissão:', result);
        
        if (result.success && result.data) {
            // Verificar se existe modal específico de comissão
            if (typeof openModalComissao === 'function') {
                openModalComissao(result.data);
            } else {
                // Se não houver modal, mostrar dados em alert temporário
                console.warn('⚠️ Modal openModalComissao não encontrado');
                showToast('Modal de edição de comissão não implementado ainda', 'warning');
                // Aqui você pode abrir um modal genérico ou criar um novo
            }
        } else {
            showToast('❌ Erro ao carregar dados da comissão', 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao buscar comissão:', error);
        showToast('❌ Erro ao carregar comissão: ' + error.message, 'error');
    }
}

async function excluirComissao(id) {
    if (!confirm('Tem certeza que deseja excluir esta comissão?')) {
        console.log('   ❌ Usuário cancelou');
        return;
    }
    
    try {
        console.log('🗑️ Excluindo comissão ID:', id);
        
        const response = await fetch(`/api/comissoes/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content
            }
        });
        
        console.log('   📡 Status:', response.status);
        
        const result = await response.json();
        console.log('   📦 Resposta:', result);
        
        if (response.ok && result.success) {
            showToast('✅ Comissão excluída com sucesso!', 'success');
            
            // Recarregar lista de comissões (se houver função loadComissoes)
            if (typeof loadComissoes === 'function') {
                loadComissoes();
            } else if (typeof loadContratos === 'function') {
                // Pode estar dentro de contratos
                loadContratos();
            }
            
            console.log('   ✅ Lista recarregada');
        } else {
            const errorMsg = result.error || 'Erro desconhecido';
            showToast('❌ Erro ao excluir: ' + errorMsg, 'error');
            console.error('   ❌ Erro:', errorMsg);
        }
    } catch (error) {
        console.error('   ❌ Exception:', error);
        showToast('❌ Erro ao excluir comissão: ' + error.message, 'error');
    }
}

/**
 * Alterna entre as tabs de Contratos
 */
function showContratoTab(tabName) {
    console.log('📑 Alternando para tab:', tabName);
    
    // Ocultar todos os conteúdos
    const contents = ['contratos', 'sessoes', 'comissoes', 'equipe'];
    contents.forEach(name => {
        const content = document.getElementById(`tab-content-${name}`);
        if (content) content.style.display = 'none';
    });
    
    // Remover classe active de todos os botões
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(btn => {
        btn.style.background = '#bdc3c7';
        btn.style.color = '#555';
        btn.classList.remove('active');
    });
    
    // Mostrar conteúdo selecionado
    const selectedContent = document.getElementById(`tab-content-${tabName}`);
    if (selectedContent) {
        selectedContent.style.display = 'block';
    }
    
    // Ativar botão selecionado
    const selectedButton = document.getElementById(`tab-${tabName}`);
    if (selectedButton) {
        selectedButton.style.background = '#9b59b6';
        selectedButton.style.color = 'white';
        selectedButton.classList.add('active');
    }
    
    // Carregar dados da tab
    switch(tabName) {
        case 'contratos':
            loadContratos();
            break;
        case 'sessoes':
            loadSessoes();
            break;
        case 'comissoes':
            loadComissoes();
            break;
        case 'equipe':
            console.log('Tab Equipe - em desenvolvimento');
            break;
    }
}

// Funções de modal (placeholders - openModalContrato está em modals.js)
function openModalSessao() {
    showToast('Modal de nova sessão em desenvolvimento', 'info');
}

function openModalComissao() {
    showToast('Modal de nova comissão em desenvolvimento', 'info');
}

function openModalSessaoEquipe() {
    showToast('Modal de adicionar membro à equipe em desenvolvimento', 'info');
}

function exportarContratosPDF() {
    showToast('Exportação de contratos para PDF em desenvolvimento', 'info');
}

// ============================================================================
// EXPOSIÇÃO GLOBAL DE FUNÇÕES CRÍTICAS
// ============================================================================

// Funções de Contas
window.editarConta = editarConta;
window.excluirConta = excluirConta;
window.salvarConta = salvarConta;

// Funções de Categorias
window.editarCategoria = editarCategoria;
window.excluirCategoria = excluirCategoria;
window.salvarCategoria = salvarCategoria;

// Funções de Clientes
window.editarCliente = editarCliente;
window.excluirCliente = excluirCliente;
window.inativarCliente = inativarCliente;
window.ativarCliente = ativarCliente;
window.salvarCliente = salvarCliente;

// Funções de Fornecedores
window.editarFornecedor = editarFornecedor;
window.excluirFornecedor = excluirFornecedor;
window.inativarFornecedor = inativarFornecedor;
window.ativarFornecedor = ativarFornecedor;
window.salvarFornecedor = salvarFornecedor;

// Funções de Lançamentos
window.excluirLancamento = excluirLancamento;
window.salvarLancamento = salvarLancamento;
window.excluirEmMassa = excluirEmMassa;

// Funções de Kits
window.editarKit = editarKit;
window.excluirKit = excluirKit;

// Funções de Contratos e Sessões
window.editarContrato = editarContrato;
window.excluirContrato = excluirContrato;
window.editarSessao = editarSessao;
window.excluirSessao = excluirSessao;
window.showContratoTab = showContratoTab;

// Funções de Comissões
window.editarComissao = editarComissao;
window.excluirComissao = excluirComissao;

// Funções de Carregamento
window.loadDashboard = loadDashboard;
window.loadContas = loadContas;
window.loadLancamentos = loadLancamentos;
window.loadContasReceber = loadContasReceber;
window.loadContasPagar = loadContasPagar;
window.loadFluxoCaixa = loadFluxoCaixa;
window.loadAnaliseCategorias = loadAnaliseCategorias;
window.loadInadimplencia = loadInadimplencia;
window.loadFluxoProjetado = loadFluxoProjetado;
window.loadAnaliseContas = loadAnaliseContas;
window.loadFornecedores = loadFornecedores;
window.loadExtratos = loadExtratos;
window.loadFuncionariosRH = loadFuncionariosRH;
window.loadKits = loadKits;
window.loadSessoes = loadSessoes;
window.loadComissoes = loadComissoes;

// Funções de Exportação
window.exportarFluxoExcel = exportarFluxoExcel;
window.exportarContratosPDF = exportarContratosPDF;

// Funções de Interface
window.showPage = showPage;
window.showModal = showModal;
window.showSection = showSection;
window.showNotification = showNotification;

console.log('✅ Todas as funções críticas expostas globalmente');

// ============================================================================
// FUNÇÕES DE CARREGAMENTO - STUBS PARA SEÇÕES EM DESENVOLVIMENTO (Fase 7.5)
// ============================================================================

/**
 * Funções stub SOMENTE para seções que realmente não existem ainda.
 * As funções que JÁ EXISTEM no código são expostas globalmente após suas declarações.
 */

window.loadFornecedoresTable = async function() {
    console.log('📋 loadFornecedoresTable - Stub temporário');
    showToast('Seção de Fornecedores em desenvolvimento', 'info');
};

window.loadContasBancarias = async function() {
    try {
        console.log('🏦 loadContasBancarias - Carregando contas bancárias...');
        
        const response = await fetch(`${API_URL}/contas`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const contas = await response.json();
        console.log(`✅ ${contas.length} conta(s) bancária(s) carregada(s)`);
        
        const tbody = document.getElementById('tbody-contas');
        if (!tbody) {
            console.warn('⚠️ Elemento tbody-contas não encontrado');
            return;
        }
        
        if (contas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #95a5a6;">Nenhuma conta bancária cadastrada</td></tr>';
            document.getElementById('saldo-total-display').textContent = 'R$ 0,00';
            return;
        }
        
        // Calcular saldo total
        let saldoTotal = 0;
        contas.forEach(c => {
            saldoTotal += c.saldo || 0;
        });
        
        // Atualizar display de saldo total
        document.getElementById('saldo-total-display').textContent = 
            saldoTotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        
        // Preencher tabela
        tbody.innerHTML = contas.map(conta => `
            <tr>
                <td>${conta.banco || 'N/A'}</td>
                <td>${conta.agencia || 'N/A'}</td>
                <td>${conta.conta || 'N/A'}</td>
                <td>${(conta.saldo_inicial || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                <td style="font-weight: bold; color: ${(conta.saldo || 0) >= 0 ? '#27ae60' : '#e74c3c'};">
                    ${(conta.saldo || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                </td>
                <td>
                    <button class="btn btn-sm btn-info" onclick='editarConta(${JSON.stringify(conta).replace(/'/g, "\\'")})'
                            style="background: #3498db; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; margin-right: 5px;">
                        ✏️ Editar
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="excluirConta('${conta.nome}')"
                            style="background: #e74c3c; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer;">
                        🗑️ Excluir
                    </button>
                </td>
            </tr>
        `).join('');
        
        // Preencher filtro de bancos
        const filtroBanco = document.getElementById('filtro-banco');
        if (filtroBanco) {
            const bancosUnicos = [...new Set(contas.map(c => c.banco).filter(b => b))];
            filtroBanco.innerHTML = '<option value="">Todos os Bancos</option>' +
                bancosUnicos.map(banco => `<option value="${banco}">${banco}</option>`).join('');
        }
        
        console.log('✅ Contas bancárias carregadas com sucesso');
    } catch (error) {
        console.error('❌ Erro ao carregar contas bancárias:', error);
        const tbody = document.getElementById('tbody-contas');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #e74c3c;">❌ Erro ao carregar contas bancárias</td></tr>';
        }
    }
};

window.loadTiposSessao = async function() {
    console.log('📸 loadTiposSessao - Funcionalidade não implementada');
    // Seção de Tipos de Sessão (funcionalidade futura)
};

window.loadAgenda = async function() {
    console.log('📅 loadAgenda - Funcionalidade não implementada');
    // Agenda de Fotografia (funcionalidade futura)
};

window.loadProdutos = async function() {
    console.log('📦 loadProdutos - Stub temporário');
    showToast('Gestão de Estoque em desenvolvimento', 'info');
};

window.loadTags = async function() {
    console.log('🏷️ loadTags - Stub temporário');
    showToast('Tags de Trabalho em desenvolvimento', 'info');
};

window.loadTemplates = async function() {
    console.log('👥 loadTemplates - Stub temporário');
    showToast('Templates de Equipe em desenvolvimento', 'info');
};

window.carregarInadimplencia = async function() {
    console.log('💰 carregarInadimplencia - Stub temporário');
    showToast('Relatório de Inadimplência em desenvolvimento', 'info');
};

window.carregarIndicadores = async function() {
    console.log('🎯 carregarIndicadores - Stub temporário');
    showToast('Indicadores Financeiros em desenvolvimento', 'info');
};

window.carregarFluxoCaixa = async function() {
    try {
        console.log('📈 Carregando Fluxo de Caixa...');
        
        // Obter filtros
        const ano = document.getElementById('filter-ano-fluxo')?.value;
        const mes = document.getElementById('filter-mes-fluxo')?.value;
        const dataInicial = document.getElementById('filter-data-inicial-fluxo')?.value;
        const dataFinal = document.getElementById('filter-data-final-fluxo')?.value;
        const banco = document.getElementById('filter-banco-fluxo')?.value;
        
        // Construir datas do filtro
        let dataInicio, dataFim;
        
        if (dataInicial && dataFinal) {
            // Usar datas customizadas
            dataInicio = dataInicial;
            dataFim = dataFinal;
        } else if (ano && mes) {
            // Usar ano/mês específico
            dataInicio = `${ano}-${mes}-01`;
            const ultimoDia = new Date(parseInt(ano), parseInt(mes), 0).getDate();
            dataFim = `${ano}-${mes}-${ultimoDia}`;
        } else if (ano) {
            // Usar ano inteiro
            dataInicio = `${ano}-01-01`;
            dataFim = `${ano}-12-31`;
        } else {
            // Usar mês atual
            const hoje = new Date();
            const anoAtual = hoje.getFullYear();
            const mesAtual = String(hoje.getMonth() + 1).padStart(2, '0');
            dataInicio = `${anoAtual}-${mesAtual}-01`;
            const ultimoDia = new Date(anoAtual, hoje.getMonth() + 1, 0).getDate();
            dataFim = `${anoAtual}-${mesAtual}-${ultimoDia}`;
        }
        
        // Buscar dados do dashboard E contas a pagar/receber
        let url = `${API_URL}/relatorios/dashboard-completo?data_inicio=${dataInicio}&data_fim=${dataFim}`;
        if (banco) {
            url += `&conta=${encodeURIComponent(banco)}`;
        }
        
        const [responseRealizado, responseProjetado] = await Promise.all([
            fetch(url, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            }),
            fetch(`${API_URL}/relatorios/analise-contas`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            })
        ]);
        
        if (!responseRealizado.ok || !responseProjetado.ok) throw new Error('Erro ao carregar dados');
        
        const dadosRealizado = await responseRealizado.json();
        const dadosProjetado = await responseProjetado.json();
        
        // Calcular totais projetados (realizado + pendente)
        const receitasRealizadas = dadosRealizado.totais?.receitas || 0;
        const despesasRealizadas = dadosRealizado.totais?.despesas || 0;
        const saldoRealizado = dadosRealizado.totais?.saldo || 0;
        
        const contasReceber = dadosProjetado.total_receber || 0;
        const contasPagar = dadosProjetado.total_pagar || 0;
        const saldoProjetado = saldoRealizado + contasReceber - contasPagar;
        
        // Renderizar tabela de fluxo
        const content = document.getElementById('fluxo-caixa-content');
        
        let html = `
            <!-- Cards de Resumo -->
            <div style="margin-bottom: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div style="background: linear-gradient(135deg, #27ae60, #229954); color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 13px; opacity: 0.9; margin-bottom: 5px;">💰 Receitas Realizadas</div>
                    <div style="font-size: 24px; font-weight: bold;">${formatarMoeda(receitasRealizadas)}</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 5px;">✅ Já recebido</div>
                </div>
                <div style="background: linear-gradient(135deg, #3498db, #2980b9); color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 13px; opacity: 0.9; margin-bottom: 5px;">📅 Contas a Receber</div>
                    <div style="font-size: 24px; font-weight: bold;">${formatarMoeda(contasReceber)}</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 5px;">⏳ Pendente</div>
                </div>
                <div style="background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 13px; opacity: 0.9; margin-bottom: 5px;">💸 Despesas Realizadas</div>
                    <div style="font-size: 24px; font-weight: bold;">${formatarMoeda(despesasRealizadas)}</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 5px;">✅ Já pago</div>
                </div>
                <div style="background: linear-gradient(135deg, #e67e22, #d35400); color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 13px; opacity: 0.9; margin-bottom: 5px;">📅 Contas a Pagar</div>
                    <div style="font-size: 24px; font-weight: bold;">${formatarMoeda(contasPagar)}</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 5px;">⏳ Pendente</div>
                </div>
                <div style="background: linear-gradient(135deg, ${saldoRealizado >= 0 ? '#16a085, #138d75' : '#c0392b, #a93226'}); color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 13px; opacity: 0.9; margin-bottom: 5px;">📊 Saldo Realizado</div>
                    <div style="font-size: 24px; font-weight: bold;">${formatarMoeda(saldoRealizado)}</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 5px;">✅ Efetivo</div>
                </div>
                <div style="background: linear-gradient(135deg, ${saldoProjetado >= 0 ? '#8e44ad, #7d3c98' : '#e74c3c, #c0392b'}); color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 13px; opacity: 0.9; margin-bottom: 5px;">🔮 Saldo Projetado</div>
                    <div style="font-size: 24px; font-weight: bold;">${formatarMoeda(saldoProjetado)}</div>
                    <div style="font-size: 11px; opacity: 0.8; margin-top: 5px;">📊 Com pendentes</div>
                </div>
            </div>
            
            <!-- Abas -->
            <div style="display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid #ecf0f1;">
                <button onclick="mostrarAbaFluxo('realizado')" id="aba-realizado" class="aba-fluxo aba-ativa" style="padding: 12px 24px; border: none; background: none; cursor: pointer; font-weight: bold; color: #27ae60; border-bottom: 3px solid #27ae60;">
                    ✅ Fluxo Realizado
                </button>
                <button onclick="mostrarAbaFluxo('projetado')" id="aba-projetado" class="aba-fluxo" style="padding: 12px 24px; border: none; background: none; cursor: pointer; font-weight: bold; color: #95a5a6; border-bottom: 3px solid transparent;">
                    🔮 Fluxo Projetado
                </button>
            </div>
            
            <!-- Conteúdo Fluxo Realizado -->
            <div id="conteudo-realizado" class="conteudo-aba-fluxo">
                <div style="overflow-x: auto; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Período</th>
                                <th style="text-align: right; color: #27ae60;">Receitas</th>
                                <th style="text-align: right; color: #e74c3c;">Despesas</th>
                                <th style="text-align: right; color: #3498db;">Saldo</th>
                            </tr>
                        </thead>
                        <tbody>`;
        
        if (dadosRealizado.evolucao && dadosRealizado.evolucao.length > 0) {
            dadosRealizado.evolucao.forEach(item => {
                html += `
                    <tr>
                        <td><strong>${item.periodo}</strong></td>
                        <td style="text-align: right; color: #27ae60; font-weight: bold;">${formatarMoeda(item.receitas)}</td>
                        <td style="text-align: right; color: #e74c3c; font-weight: bold;">${formatarMoeda(item.despesas)}</td>
                        <td style="text-align: right; color: ${item.saldo >= 0 ? '#3498db' : '#e67e22'}; font-weight: bold;">${formatarMoeda(item.saldo)}</td>
                    </tr>`;
            });
        } else {
            html += '<tr><td colspan="4" style="text-align: center; padding: 40px; color: #999;">Nenhum lançamento pago encontrado no período</td></tr>';
        }
        
        html += `
                        </tbody>
                    </table>
                </div>
                <div style="margin-top: 10px; padding: 10px; background: #ecf0f1; border-radius: 5px; color: #7f8c8d; font-size: 13px;">
                    📌 <strong>Fluxo Realizado:</strong> Mostra apenas receitas e despesas já pagas/recebidas (lançamentos com status "Pago").
                </div>
            </div>
            
            <!-- Conteúdo Fluxo Projetado -->
            <div id="conteudo-projetado" class="conteudo-aba-fluxo" style="display: none;">
                <div style="overflow-x: auto; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Período</th>
                                <th style="text-align: right; color: #27ae60;">Receitas (Pagas)</th>
                                <th style="text-align: right; color: #3498db;">A Receber</th>
                                <th style="text-align: right; color: #e74c3c;">Despesas (Pagas)</th>
                                <th style="text-align: right; color: #e67e22;">A Pagar</th>
                                <th style="text-align: right; color: #8e44ad;">Saldo Projetado</th>
                            </tr>
                        </thead>
                        <tbody>`;
        
        if (dadosRealizado.evolucao && dadosRealizado.evolucao.length > 0) {
            dadosRealizado.evolucao.forEach(item => {
                const saldoProj = item.saldo + (contasReceber / dadosRealizado.evolucao.length) - (contasPagar / dadosRealizado.evolucao.length);
                html += `
                    <tr>
                        <td><strong>${item.periodo}</strong></td>
                        <td style="text-align: right; color: #27ae60; font-weight: bold;">${formatarMoeda(item.receitas)}</td>
                        <td style="text-align: right; color: #3498db;">${formatarMoeda(contasReceber / dadosRealizado.evolucao.length)}</td>
                        <td style="text-align: right; color: #e74c3c; font-weight: bold;">${formatarMoeda(item.despesas)}</td>
                        <td style="text-align: right; color: #e67e22;">${formatarMoeda(contasPagar / dadosRealizado.evolucao.length)}</td>
                        <td style="text-align: right; color: ${saldoProj >= 0 ? '#8e44ad' : '#c0392b'}; font-weight: bold;">${formatarMoeda(saldoProj)}</td>
                    </tr>`;
            });
        } else {
            html += '<tr><td colspan="6" style="text-align: center; padding: 40px; color: #999;">Nenhum dado disponível</td></tr>';
        }
        
        html += `
                        </tbody>
                    </table>
                </div>
                <div style="margin-top: 10px; padding: 10px; background: #ecf0f1; border-radius: 5px; color: #7f8c8d; font-size: 13px;">
                    📌 <strong>Fluxo Projetado:</strong> Inclui valores já pagos/recebidos + contas a pagar e receber pendentes. Os valores pendentes são distribuídos proporcionalmente nos meses.
                </div>
                <div style="margin-top: 15px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
                        <div style="font-weight: bold; color: #856404; margin-bottom: 5px;">⚠️ Contas Vencidas a Receber</div>
                        <div style="font-size: 20px; color: #856404;">${formatarMoeda(dadosProjetado.receber_vencidos || 0)}</div>
                    </div>
                    <div style="background: #f8d7da; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545;">
                        <div style="font-weight: bold; color: #721c24; margin-bottom: 5px;">⚠️ Contas Vencidas a Pagar</div>
                        <div style="font-size: 20px; color: #721c24;">${formatarMoeda(dadosProjetado.pagar_vencidos || 0)}</div>
                    </div>
                </div>
            </div>`;
        
        content.innerHTML = html;
        
        // Armazenar dados para exportação
        window.fluxoCaixaDados = {
            ...dadosRealizado,
            projetado: dadosProjetado,
            totais: {
                receitas: receitasRealizadas,
                despesas: despesasRealizadas,
                saldo: saldoRealizado,
                contasReceber,
                contasPagar,
                saldoProjetado
            }
        };
        
        showToast('Fluxo de Caixa carregado com sucesso!', 'success');
        
    } catch (error) {
        console.error('❌ Erro ao carregar fluxo de caixa:', error);
        const content = document.getElementById('fluxo-caixa-content');
        content.innerHTML = '<div style="text-align: center; padding: 40px; color: #e74c3c;">❌ Erro ao carregar dados do fluxo de caixa</div>';
        showToast('Erro ao carregar fluxo de caixa', 'error');
    }
};

window.mostrarAbaFluxo = function(aba) {
    // Atualizar botões
    document.querySelectorAll('.aba-fluxo').forEach(btn => {
        btn.style.color = '#95a5a6';
        btn.style.borderBottom = '3px solid transparent';
        btn.classList.remove('aba-ativa');
    });
    
    const btnAtivo = document.getElementById(`aba-${aba}`);
    if (btnAtivo) {
        btnAtivo.style.color = aba === 'realizado' ? '#27ae60' : '#8e44ad';
        btnAtivo.style.borderBottom = `3px solid ${aba === 'realizado' ? '#27ae60' : '#8e44ad'}`;
        btnAtivo.classList.add('aba-ativa');
    }
    
    // Mostrar conteúdo correto
    document.querySelectorAll('.conteudo-aba-fluxo').forEach(div => {
        div.style.display = 'none';
    });
    
    const conteudo = document.getElementById(`conteudo-${aba}`);
    if (conteudo) {
        conteudo.style.display = 'block';
    }
};

window.carregarBancosFluxo = async function() {
    try {
        const response = await fetch(`${API_URL}/contas`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) throw new Error('Erro ao carregar contas');
        
        const contas = await response.json();
        const select = document.getElementById('filter-banco-fluxo');
        
        if (select) {
            select.innerHTML = '<option value="">Todos</option>';
            contas.forEach(conta => {
                select.innerHTML += `<option value="${conta.nome}">${conta.nome}</option>`;
            });
        }
    } catch (error) {
        console.error('Erro ao carregar bancos:', error);
    }
};

window.limparFiltrosFluxo = function() {
    document.getElementById('filter-ano-fluxo').value = '';
    document.getElementById('filter-mes-fluxo').value = '';
    document.getElementById('filter-data-inicial-fluxo').value = '';
    document.getElementById('filter-data-final-fluxo').value = '';
    document.getElementById('filter-banco-fluxo').value = '';
    window.carregarFluxoCaixa();
};

window.carregarComparativoPeriodos = async function() {
    console.log('📉 carregarComparativoPeriodos - Stub temporário');
    showToast('Comparativo de Períodos em desenvolvimento', 'info');
};

// === TRANSFERÊNCIA ENTRE CONTAS ===
window.openModalTransferencia = async function() {
    try {
        // Carregar contas
        const response = await fetch(`${API_URL}/contas`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) throw new Error('Erro ao carregar contas');
        
        const contas = await response.json();
        
        // Preencher selects
        const selectOrigem = document.getElementById('transferencia-origem');
        const selectDestino = document.getElementById('transferencia-destino');
        
        const optionsHTML = '<option value="">Selecione...</option>' + 
            contas.map(c => `<option value="${c.nome}">${c.nome}</option>`).join('');
        
        selectOrigem.innerHTML = optionsHTML;
        selectDestino.innerHTML = optionsHTML;
        
        // Definir data de hoje
        document.getElementById('transferencia-data').value = new Date().toISOString().split('T')[0];
        
        // Limpar campos
        document.getElementById('transferencia-valor').value = '';
        document.getElementById('transferencia-observacoes').value = '';
        
        // Mostrar modal
        document.getElementById('modal-transferencia').style.display = 'flex';
        
    } catch (error) {
        console.error('Erro ao abrir modal de transferência:', error);
        showToast('Erro ao carregar contas', 'error');
    }
};

window.closeModalTransferencia = function() {
    document.getElementById('modal-transferencia').style.display = 'none';
};

window.salvarTransferencia = async function() {
    try {
        const origem = document.getElementById('transferencia-origem').value;
        const destino = document.getElementById('transferencia-destino').value;
        const valor = parseFloat(document.getElementById('transferencia-valor').value);
        const data = document.getElementById('transferencia-data').value;
        const observacoes = document.getElementById('transferencia-observacoes').value;
        
        // Validações
        if (!origem) {
            showToast('Selecione a conta de origem', 'error');
            return;
        }
        
        if (!destino) {
            showToast('Selecione a conta de destino', 'error');
            return;
        }
        
        if (origem === destino) {
            showToast('Conta de origem e destino não podem ser iguais', 'error');
            return;
        }
        
        if (!valor || valor <= 0) {
            showToast('Digite um valor válido', 'error');
            return;
        }
        
        if (!data) {
            showToast('Selecione a data da transferência', 'error');
            return;
        }
        
        // Enviar transferência
        const response = await fetch(`${API_URL}/transferencias`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
                conta_origem: origem,
                conta_destino: destino,
                valor: valor,
                data: data,
                observacoes: observacoes,
                empresa_id: window.currentEmpresaId
            })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Erro ao realizar transferência');
        }
        
        showToast('✅ Transferência realizada com sucesso!', 'success');
        closeModalTransferencia();
        
        // Recarregar dados se estiver na tela de fluxo
        if (window.location.hash === '#fluxo-caixa' || document.getElementById('fluxo-caixa-section')?.classList.contains('active')) {
            await carregarFluxoCaixa();
        }
        
    } catch (error) {
        console.error('Erro ao salvar transferência:', error);
        showToast(error.message || 'Erro ao realizar transferência', 'error');
    }
};
// === CONCILIAÇÃO GERAL DE EXTRATO ===
window.abrirConciliacaoGeral = async function() {
    try {
        // Obter extratos filtrados e não conciliados
        const conta = document.getElementById('extrato-filter-conta')?.value || document.getElementById('filtro-conta-extrato')?.value;
        const dataInicio = document.getElementById('extrato-filter-data-inicio')?.value || document.getElementById('filtro-data-inicio-extrato')?.value;
        const dataFim = document.getElementById('extrato-filter-data-fim')?.value || document.getElementById('filtro-data-fim-extrato')?.value;
        
        const params = new URLSearchParams();
        if (conta) params.append('conta', conta);
        if (dataInicio) params.append('data_inicio', dataInicio);
        if (dataFim) params.append('data_fim', dataFim);
        params.append('conciliado', 'false');  // Apenas não conciliados
        
        const response = await fetch(`${API_URL}/extratos?${params.toString()}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        
        if (!response.ok) throw new Error('Erro ao carregar extratos');
        
        const transacoes = await response.json();
        
        if (transacoes.length === 0) {
            showToast('Nenhuma transação não conciliada encontrada no período filtrado', 'warning');
            return;
        }
        
        // Buscar categorias e subcategorias
        const [responseCategorias, responseClientes, responseFornecedores] = await Promise.all([
            fetch(`${API_URL}/categorias`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            }),
            fetch(`${API_URL}/clientes`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            }),
            fetch(`${API_URL}/fornecedores`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            })
        ]);
        
        const categorias = await responseCategorias.json();
        const clientes = await responseClientes.json();
        const fornecedores = await responseFornecedores.json();
        
        // Criar dicionário de matching CPF/CNPJ
        window.clientesPorCPF = {};
        clientes.forEach(c => {
            const cpf_cnpj = (c.cpf || c.cnpj || '').replace(/\D/g, '');
            if (cpf_cnpj) window.clientesPorCPF[cpf_cnpj] = c.nome;
        });
        
        window.fornecedoresPorCPF = {};
        fornecedores.forEach(f => {
            const cpf_cnpj = (f.cpf || f.cnpj || '').replace(/\D/g, '');
            if (cpf_cnpj) window.fornecedoresPorCPF[cpf_cnpj] = f.nome;
        });
        
        // Agrupar categorias por tipo
        const categoriasDespesa = categorias.filter(c => c.tipo === 'DESPESA');
        const categoriasReceita = categorias.filter(c => c.tipo === 'RECEITA');
        
        // Renderizar lista de transações
        let html = `
            <div style="background: #ecf0f1; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="font-size: 16px;">${transacoes.length} transações encontradas</strong>
                        <div style="color: #7f8c8d; font-size: 13px; margin-top: 5px;">
                            ${dataInicio && dataFim ? `Período: ${formatarData(dataInicio)} a ${formatarData(dataFim)}` : 'Todas as datas'}
                            ${conta ? ` | Conta: ${conta}` : ''}
                        </div>
                    </div>
                    <label style="font-weight: bold; cursor: pointer;">
                        <input type="checkbox" id="selecionar-todos-conciliacao" onchange="toggleTodasConciliacoes(this.checked)" style="margin-right: 8px; transform: scale(1.3);">
                        Selecionar Todas
                    </label>
                </div>
            </div>
            
            <div style="max-height: 500px; overflow-y: auto;">
                <table class="data-table" style="width: 100%; border-collapse: collapse;">
                    <thead style="position: sticky; top: 0; background: #34495e; color: white; z-index: 1;">
                        <tr>
                            <th style="width: 50px; text-align: center;">✓</th>
                            <th style="width: 100px;">Data</th>
                            <th style="min-width: 250px;">Descrição</th>
                            <th style="width: 120px;">Valor</th>
                            <th style="width: 80px;">Tipo</th>
                            <th style="width: 200px;">Razão Social</th>
                            <th style="width: 200px;">Categoria</th>
                            <th style="width: 200px;">Subcategoria</th>
                        </tr>
                    </thead>
                    <tbody>`;
        
        transacoes.forEach((t, index) => {
            const isCredito = t.tipo?.toUpperCase() === 'CREDITO';
            const valorColor = isCredito ? '#27ae60' : '#e74c3c';
            
            // Tentar detectar CPF/CNPJ na descrição
            const numeros = t.descricao.replace(/\D/g, '');
            let razaoSugerida = '';
            if (numeros.length === 11 || numeros.length === 14) {
                razaoSugerida = isCredito ? 
                    (window.clientesPorCPF[numeros] || '') : 
                    (window.fornecedoresPorCPF[numeros] || '');
            }
            
            // Opções de categoria filtradas por tipo
            const categoriasOpcoes = isCredito ? categoriasReceita : categoriasDespesa;
            
            html += `
                <tr style="border-bottom: 1px solid #ecf0f1;">
                    <td style="text-align: center;">
                        <input type="checkbox" class="checkbox-conciliacao" data-index="${index}" style="transform: scale(1.3);">
                    </td>
                    <td>${formatarData(t.data)}</td>
                    <td style="font-size: 12px;">${t.descricao}</td>
                    <td style="color: ${valorColor}; font-weight: bold;">${formatarMoeda(t.valor)}</td>
                    <td>
                        <span class="badge badge-${isCredito ? 'success' : 'danger'}">
                            ${isCredito ? 'Crédito' : 'Débito'}
                        </span>
                    </td>
                    <td>
                        <input type="text" 
                               id="razao-${t.id}" 
                               value="${razaoSugerida}"
                               placeholder="${isCredito ? 'Cliente' : 'Fornecedor'}"
                               list="lista-${isCredito ? 'clientes' : 'fornecedores'}"
                               style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px;">
                    </td>
                    <td>
                        <select id="categoria-${t.id}" 
                                onchange="carregarSubcategoriasConciliacao(${t.id}, this.value)"
                                style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px;">
                            <option value="">Selecione...</option>
                            ${categoriasOpcoes.map(c => `<option value="${c.nome}">${c.nome}</option>`).join('')}
                        </select>
                    </td>
                    <td>
                        <select id="subcategoria-${t.id}" 
                                disabled
                                style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; background: #f5f5f5;">
                            <option value="">Primeiro selecione categoria</option>
                        </select>
                    </td>
                </tr>`;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
            
            <!-- Datalists para autocomplete -->
            <datalist id="lista-clientes">
                ${clientes.map(c => `<option value="${c.nome}">`).join('')}
            </datalist>
            <datalist id="lista-fornecedores">
                ${fornecedores.map(f => `<option value="${f.nome}">`).join('')}
            </datalist>`;
        
        document.getElementById('conciliacao-transacoes-lista').innerHTML = html;
        
        // Armazenar dados para processamento
        window.transacoesConciliacao = transacoes;
        window.categoriasConciliacao = categorias;
        
        // Mostrar modal
        document.getElementById('modal-conciliacao-geral').style.display = 'block';
        
    } catch (error) {
        console.error('Erro ao abrir conciliação geral:', error);
        showToast('Erro ao carregar dados de conciliação', 'error');
    }
};

window.toggleTodasConciliacoes = function(checked) {
    document.querySelectorAll('.checkbox-conciliacao').forEach(cb => {
        cb.checked = checked;
    });
};

window.carregarSubcategoriasConciliacao = function(transacaoId, categoria) {
    const selectSubcat = document.getElementById(`subcategoria-${transacaoId}`);
    
    if (!categoria) {
        selectSubcat.disabled = true;
        selectSubcat.innerHTML = '<option value="">Primeiro selecione categoria</option>';
        return;
    }
    
    // Buscar categoria completa
    const catObj = window.categoriasConciliacao.find(c => c.nome === categoria);
    
    if (!catObj || !catObj.subcategorias || catObj.subcategorias.length === 0) {
        selectSubcat.disabled = true;
        selectSubcat.innerHTML = '<option value="">Sem subcategorias</option>';
        return;
    }
    
    selectSubcat.disabled = false;
    selectSubcat.innerHTML = '<option value="">Opcional</option>' + 
        catObj.subcategorias.map(s => `<option value="${s}">${s}</option>`).join('');
};

window.processarConciliacaoGeral = async function() {
    try {
        // Coletar transações selecionadas
        const selecionadas = [];
        const checkboxes = document.querySelectorAll('.checkbox-conciliacao:checked');
        
        if (checkboxes.length === 0) {
            showToast('Selecione pelo menos uma transação', 'warning');
            return;
        }
        
        let errosValidacao = [];
        
        checkboxes.forEach(cb => {
            const index = parseInt(cb.dataset.index);
            const transacao = window.transacoesConciliacao[index];
            const categoria = document.getElementById(`categoria-${transacao.id}`).value;
            const subcategoria = document.getElementById(`subcategoria-${transacao.id}`).value;
            const razaoSocial = document.getElementById(`razao-${transacao.id}`).value;
            
            if (!categoria) {
                errosValidacao.push(`Transação "${transacao.descricao.substring(0, 30)}...": categoria não selecionada`);
                return;
            }
            
            selecionadas.push({
                transacao_id: transacao.id,
                categoria: categoria,
                subcategoria: subcategoria,
                razao_social: razaoSocial
            });
        });
        
        if (errosValidacao.length > 0) {
            showToast(`Erros de validação:\n${errosValidacao.join('\n')}`, 'error');
            return;
        }
        
        if (selecionadas.length === 0) {
            showToast('Nenhuma transação válida para conciliar', 'warning');
            return;
        }
        
        // Confirmar
        if (!confirm(`Deseja criar ${selecionadas.length} lançamento(s) em Contas a Pagar/Receber?`)) {
            return;
        }
        
        showToast('Processando conciliação...', 'info');
        
        // Enviar para backend
        const response = await fetch(`${API_URL}/extratos/conciliacao-geral`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
                transacoes: selecionadas
            })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Erro ao processar conciliação');
        }
        
        let mensagem = `✅ Conciliação concluída!\n${result.criados} lançamento(s) criado(s)`;
        
        if (result.erros && result.erros.length > 0) {
            mensagem += `\n\n⚠️ Avisos:\n${result.erros.slice(0, 3).join('\n')}`;
            if (result.erros.length > 3) {
                mensagem += `\n... e mais ${result.erros.length - 3} erro(s)`;
            }
        }
        
        showToast(mensagem, 'success');
        
        // Fechar modal e recarregar
        fecharConciliacaoGeral();
        await loadExtratos();
        
    } catch (error) {
        console.error('Erro ao processar conciliação:', error);
        showToast(error.message || 'Erro ao processar conciliação', 'error');
    }
};

window.fecharConciliacaoGeral = function() {
    document.getElementById('modal-conciliacao-geral').style.display = 'none';
    window.transacoesConciliacao = null;
    window.categoriasConciliacao = null;
};