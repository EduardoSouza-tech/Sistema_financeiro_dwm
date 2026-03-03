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

// Debug: Confirmar que app.js foi carregado
console.log('📦 app.js carregado - versão 2.0.0');

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
        const response = await fetchWithTimeout(`${CONFIG.API_URL}${endpoint}`);
        
        console.log(`🔍 apiGet(${endpoint}):`, {
            tipo: typeof response,
            temSuccess: 'success' in (response || {}),
            temData: 'data' in (response || {}),
            isArray: Array.isArray(response),
            keys: response ? Object.keys(response).slice(0, 5) : []
        });
        
        // Suporte ao novo formato de resposta { success, data, total, message }
        // Se a resposta tiver os campos do novo formato, extrai os dados
        if (response && typeof response === 'object' && 'success' in response && 'data' in response) {
            console.log(`   ✅ Novo formato detectado! Extraindo campo 'data'`);
            // Se não houver dados, mostrar mensagem informativa ao invés de erro
            if (response.data.length === 0 && response.message) {
                console.info(`   ℹ️ ${response.message}`);
            }
            return response.data;
        }
        
        // Retrocompatibilidade: retorna resposta original se não for o novo formato
        console.log(`   ⚠️ Formato antigo detectado, retornando resposta original`);
        return response;
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
    // String YYYY-MM-DD: formatar direto sem Date (evita bug timezone UTC-3)
    if (typeof data === 'string' && data.match(/^\d{4}-\d{2}-\d{2}/)) {
        const parts = data.substring(0, 10).split('-');
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    // Outros formatos: delega para utils.js
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
        
        // Verificar permissões do usuário antes de carregar dados
        const usuario = JSON.parse(sessionStorage.getItem('usuario') || '{}');
        const permissoes = usuario.permissoes || [];
        
        // Carregar apenas dados que o usuário tem permissão
        const promises = [];
        
        if (permissoes.includes('dashboard') || permissoes.includes('relatorios_view')) {
            promises.push(loadDashboard());
        } else {
            console.log('⏭️ Dashboard: Usuário sem permissão, não carregando');
        }
        
        if (permissoes.includes('contas_view') || permissoes.includes('lancamentos_view')) {
            promises.push(loadContas());
        } else {
            console.log('⏭️ Contas: Usuário sem permissão, não carregando');
        }
        
        if (permissoes.includes('categorias_view') || permissoes.includes('lancamentos_view')) {
            promises.push(loadCategorias());
        } else {
            console.log('⏭️ Categorias: Usuário sem permissão, não carregando');
        }
        
        // Carrega dados em paralelo apenas os permitidos
        if (promises.length > 0) {
            await Promise.allSettled(promises);
        }
        
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
        // Verificar permissão antes de carregar
        const usuario = JSON.parse(sessionStorage.getItem('usuario') || '{}');
        const permissoes = usuario.permissoes || [];
        if (!permissoes.includes('dashboard') && !permissoes.includes('relatorios_view')) {
            console.log('⏭️ Dashboard: Usuário sem permissão');
            return;
        }
        
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
        // Verificar permissão antes de carregar
        const usuario = JSON.parse(sessionStorage.getItem('usuario') || '{}');
        const permissoes = usuario.permissoes || [];
        if (!permissoes.includes('contas_view') && !permissoes.includes('lancamentos_view')) {
            console.log('⏭️ Contas: Usuário sem permissão');
            return;
        }
        
        console.log('🏦 Carregando contas bancárias...');
        
        let data = await apiGet('/contas');
        
        console.log('   📦 Resposta RAW:', data);
        console.log('   📊 Tipo:', typeof data, '| É array?', Array.isArray(data));
        
        // CORREÇÃO DIRETA: Se vier no novo formato {success, data, total, message}, extrair
        if (data && typeof data === 'object' && 'success' in data && 'data' in data) {
            console.log('   ✅ Detectado formato novo! Extraindo campo data...');
            if (data.data.length === 0 && data.message) {
                console.info(`   ℹ️ ${data.message}`);
            }
            data = data.data;
        }
        
        console.log('   📊 Total de contas:', data.length);
        
        // Valida se é um array
        if (!Array.isArray(data)) {
            console.error('   ❌ ERRO: data não é array após extração!', data);
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
                
                // Determinar status da conta
                const isAtiva = conta.ativa !== false;
                const badgeStatus = isAtiva 
                    ? '<span class="badge badge-success" style="background: #27ae60; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold;">✓ ATIVA</span>'
                    : '<span class="badge badge-secondary" style="background: #95a5a6; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold;">● INATIVA</span>';
                
                const botaoToggle = isAtiva
                    ? `<button class="btn" onclick="toggleAtivoConta('${conta.nome}')" style="background: #f39c12; color: white; padding: 6px 12px; border-radius: 4px; border: none; cursor: pointer; font-size: 12px;" title="Inativar conta">⏸️ Inativar</button>`
                    : `<button class="btn" onclick="toggleAtivoConta('${conta.nome}')" style="background: #27ae60; color: white; padding: 6px 12px; border-radius: 4px; border: none; cursor: pointer; font-size: 12px;" title="Reativar conta">🔄 Reativar</button>`;
                
                // Tabela
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${conta.banco} ${badgeStatus}</td>
                    <td>${conta.agencia}</td>
                    <td>${conta.conta}</td>
                    <td>${formatarMoeda(conta.saldo_inicial)}</td>
                    <td>${formatarMoeda(conta.saldo_real !== undefined ? conta.saldo_real : conta.saldo_inicial)}</td>
                    <td style="white-space: nowrap; text-align: center;">
                        <button onclick="editarConta('${conta.nome}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar conta">✏️</button>
                        ${botaoToggle}
                        <button onclick="excluirConta('${conta.nome}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir conta">🗑️</button>
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
            
            // Filtrar apenas contas ativas para seleção em formulários
            const contasAtivas = data.filter(c => c.ativa !== false);
            
            contasAtivas.forEach(conta => {
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
        
        // Determinar status da conta
        const isAtiva = conta.ativa !== false;
        const badgeStatus = isAtiva 
            ? '<span class="badge badge-success" style="background: #27ae60; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold;">✓ ATIVA</span>'
            : '<span class="badge badge-secondary" style="background: #95a5a6; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold;">● INATIVA</span>';
        
        const botaoToggle = isAtiva
            ? `<button class="btn" onclick="toggleAtivoConta('${conta.nome}')" style="background: #f39c12; color: white; padding: 6px 12px; border-radius: 4px; border: none; cursor: pointer; font-size: 12px;" title="Inativar conta">⏸️ Inativar</button>`
            : `<button class="btn" onclick="toggleAtivoConta('${conta.nome}')" style="background: #27ae60; color: white; padding: 6px 12px; border-radius: 4px; border: none; cursor: pointer; font-size: 12px;" title="Reativar conta">🔄 Reativar</button>`;
        
        // Adicionar linha na tabela
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${conta.banco} ${badgeStatus}</td>
            <td>${conta.agencia}</td>
            <td>${conta.conta}</td>
            <td>${formatarMoeda(conta.saldo_inicial)}</td>
            <td>${formatarMoeda(conta.saldo_real !== undefined ? conta.saldo_real : conta.saldo_inicial)}</td>
            <td style="white-space: nowrap; text-align: center;">
                <button onclick="editarConta('${conta.nome}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar conta">✏️</button>
                ${botaoToggle}
                <button onclick="excluirConta('${conta.nome}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir conta">🗑️</button>
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
        
        let contas = await response.json();
        
        // Suporte ao novo formato de resposta { success, data, total, message }
        if (contas && typeof contas === 'object' && 'success' in contas && 'data' in contas) {
            contas = contas.data;
        }
        
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
        
        let contas = await response.json();
        
        // Suporte ao novo formato de resposta { success, data, total, message }
        if (contas && typeof contas === 'object' && 'success' in contas && 'data' in contas) {
            contas = contas.data;
        }
        
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
        console.log('🗑️ Excluindo conta:', nome);
        
        const response = await fetch(`${API_URL}/contas/${encodeURIComponent(nome)}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        const result = await response.json();
        console.log('📡 Resposta da exclusão:', result);
        
        if (result.success) {
            showToast('Conta excluída com sucesso!', 'success');
            loadContasBancarias();
        } else {
            showToast('Erro: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao excluir conta:', error);
        showToast('Erro ao excluir conta', 'error');
    }
}

/**
 * Ativa ou inativa uma conta bancária
 * @param {string} nome - Nome da conta
 */
async function toggleAtivoConta(nome) {
    try {
        console.log('🔄 Alterando status da conta:', nome);
        
        const response = await fetch(`${API_URL}/contas/${encodeURIComponent(nome)}/toggle-ativo`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        const result = await response.json();
        console.log('📡 Resposta:', result);
        
        if (result.success) {
            const acao = result.ativa ? 'reativada' : 'inativada';
            showToast(`Conta ${acao} com sucesso!`, 'success');
            loadContasBancarias();
        } else {
            showToast('Erro: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao alterar status da conta:', error);
        showToast('Erro ao alterar status da conta', 'error');
    }
}

// === CATEGORIAS ===
async function loadCategorias() {
    const context = 'loadCategorias';
    
    try {
        // Verificar permissão antes de carregar
        const usuario = JSON.parse(sessionStorage.getItem('usuario') || '{}');
        const permissoes = usuario.permissoes || [];
        if (!permissoes.includes('categorias_view') && !permissoes.includes('lancamentos_view')) {
            console.log('⏭️ Categorias: Usuário sem permissão');
            return;
        }
        
        console.log('📂 Carregando categorias...');
        console.log('   🏢 window.currentEmpresaId:', window.currentEmpresaId);
        
        let data = await apiGet('/categorias');
        
        console.log('   📦 Resposta RAW:', data);
        console.log('   📊 Tipo:', typeof data, '| É array?', Array.isArray(data));
        
        // CORREÇÃO DIRETA: Se vier no novo formato {success, data, total, message}, extrair
        if (data && typeof data === 'object' && 'success' in data && 'data' in data) {
            console.log('   ✅ Detectado formato novo! Extraindo campo data...');
            if (data.data.length === 0 && data.message) {
                console.info(`   ℹ️ ${data.message}`);
            }
            data = data.data;
        }
        
        console.log('   📊 Total de categorias:', data.length);
        
        if (!Array.isArray(data)) {
            console.error('   ❌ ERRO: data não é array após extração!', data);
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
                        <td style="text-align: center;">
                            <button onclick="editarCategoria('${escapeHtml(cat.nome)}', '${escapeHtml(cat.tipo)}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar categoria">✏️</button>
                            <button onclick="excluirCategoria('${escapeHtml(cat.nome)}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir categoria">🗑️</button>
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
                        <td style="text-align: center;">
                            <button onclick="editarCategoria('${escapeHtml(cat.nome)}', '${escapeHtml(cat.tipo)}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar categoria">✏️</button>
                            <button onclick="excluirCategoria('${escapeHtml(cat.nome)}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir categoria">🗑️</button>
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
        // Popular filtros de categoria em Contas a Receber/Pagar
        popularFiltrosCategorias();
        
    } catch (error) {
        logError(context, error);
        showNotification('Erro ao carregar categorias', 'error');
    }
}
// Expor globalmente para uso em showSection()
window.loadCategorias = loadCategorias;

/**
 * Popular selects de categoria nos filtros de Receber e Pagar
 */
async function popularFiltrosCategorias() {
    let cats = window.categorias || [];
    // Se ainda não carregou, buscar direto da API
    if (!cats.length) {
        try {
            const resp = await fetch(`${API_URL}/categorias`);
            const raw = await resp.json();
            cats = Array.isArray(raw) ? raw : (raw.data || []);
            window.categorias = cats;
        } catch(e) {
            console.warn('⚠️ popularFiltrosCategorias: erro ao buscar categorias', e);
            return;
        }
    }
    if (!cats.length) return;

    function preencherSelect(elId, tipo) {
        const sel = document.getElementById(elId);
        if (!sel) return;
        const valorAtual = sel.value;
        sel.innerHTML = '<option value="">Todas</option>';
        cats.filter(c => c.tipo.toLowerCase() === tipo).forEach(c => {
            const o = document.createElement('option');
            o.value = c.nome;
            o.textContent = c.nome;
            o.dataset.subcategorias = JSON.stringify(c.subcategorias || []);
            sel.appendChild(o);
        });
        if (valorAtual) sel.value = valorAtual;
    }

    preencherSelect('filter-categoria-receber', 'receita');
    preencherSelect('filter-categoria-pagar', 'despesa');
    console.log('✅ Filtros de categoria populados');
}
window.popularFiltrosCategorias = popularFiltrosCategorias;

function atualizarSubcategoriasReceber() {
    const catSel = document.getElementById('filter-categoria-receber');
    const subSel = document.getElementById('filter-subcategoria-receber');
    if (!subSel) return;
    subSel.innerHTML = '<option value="">Todas</option>';
    if (!catSel || !catSel.value) return;
    const opt = catSel.options[catSel.selectedIndex];
    if (opt && opt.dataset.subcategorias) {
        JSON.parse(opt.dataset.subcategorias).forEach(s => {
            const o = document.createElement('option');
            o.value = s; o.textContent = s;
            subSel.appendChild(o);
        });
    }
}
window.atualizarSubcategoriasReceber = atualizarSubcategoriasReceber;

function atualizarSubcategoriasPagar() {
    const catSel = document.getElementById('filter-categoria-pagar');
    const subSel = document.getElementById('filter-subcategoria-pagar');
    if (!subSel) return;
    subSel.innerHTML = '<option value="">Todas</option>';
    if (!catSel || !catSel.value) return;
    const opt = catSel.options[catSel.selectedIndex];
    if (opt && opt.dataset.subcategorias) {
        JSON.parse(opt.dataset.subcategorias).forEach(s => {
            const o = document.createElement('option');
            o.value = s; o.textContent = s;
            subSel.appendChild(o);
        });
    }
}
window.atualizarSubcategoriasPagar = atualizarSubcategoriasPagar;

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
        let clientes = await response.json();
        
        // Suporte ao novo formato de resposta { success, data, total, message }
        if (clientes && typeof clientes === 'object' && 'success' in clientes && 'data' in clientes) {
            if (clientes.data.length === 0 && clientes.message) {
                console.info(`ℹ️ ${clientes.message}`);
            }
            clientes = clientes.data;
        }
        
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
            // Usar razao_social como identificador se existir, senão usar nome
            const identificador = cliente.razao_social || cliente.nome || '';
            const nomeEscaped = escapeHtml(identificador);
            
            // Botões diferentes para ativos e inativos
            const botoesAcao = ativos ? `
                <button onclick="editarCliente('${nomeEscaped}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar cliente">✏️</button>
                <button onclick="inativarCliente('${nomeEscaped}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Desativar cliente">⏸️</button>
                <button onclick="excluirCliente('${nomeEscaped}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir cliente">🗑️</button>
            ` : `
                <button onclick="ativarCliente('${nomeEscaped}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Reativar cliente">▶️</button>
                <button onclick="excluirCliente('${nomeEscaped}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir cliente">🗑️</button>
            `;
            
            const dataInativacaoCell = ativos ? '' : `<td>${cliente.data_inativacao || '-'}</td>`;
            
            tr.innerHTML = `
                <td>${cliente.razao_social || cliente.nome || '-'}</td>
                <td>${cliente.nome_fantasia || '-'}</td>
                <td>${cliente.cnpj || cliente.documento || cliente.cpf_cnpj || '-'}</td>
                <td>${cliente.cidade || '-'}</td>
                <td>${cliente.telefone || '-'}</td>
                ${dataInativacaoCell}
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
    const abaAtivos = document.getElementById('tab-clientes-ativos');
    const abaInativos = document.getElementById('tab-clientes-inativos');
    
    // Mostrar/ocultar coluna de data de inativação
    const thDataInativacao = document.getElementById('th-data-inativacao-cliente');
    
    if (tab === 'ativos') {
        abaAtivos?.classList.add('active');
        abaAtivos?.setAttribute('style', 'padding: 10px 20px; border: none; background: #9b59b6; color: white; cursor: pointer; border-radius: 5px 5px 0 0; font-weight: bold;');
        abaInativos?.classList.remove('active');
        abaInativos?.setAttribute('style', 'padding: 10px 20px; border: none; background: #bdc3c7; color: #555; cursor: pointer; border-radius: 5px 5px 0 0;');
        if (thDataInativacao) thDataInativacao.style.display = 'none';
        loadClientes(true);
    } else {
        abaInativos?.classList.add('active');
        abaInativos?.setAttribute('style', 'padding: 10px 20px; border: none; background: #9b59b6; color: white; cursor: pointer; border-radius: 5px 5px 0 0; font-weight: bold;');
        abaAtivos?.classList.remove('active');
        abaAtivos?.setAttribute('style', 'padding: 10px 20px; border: none; background: #bdc3c7; color: #555; cursor: pointer; border-radius: 5px 5px 0 0;');
        if (thDataInativacao) thDataInativacao.style.display = 'table-cell';
        loadClientes(false);
    }
    
    console.log('✅ Aba alternada:', tab);
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
        let fornecedores = await response.json();
        
        // Suporte ao novo formato de resposta { success, data, total, message }
        if (fornecedores && typeof fornecedores === 'object' && 'success' in fornecedores && 'data' in fornecedores) {
            if (fornecedores.data.length === 0 && fornecedores.message) {
                console.info(`ℹ️ ${fornecedores.message}`);
            }
            fornecedores = fornecedores.data;
        }
        
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
                <td style="text-align: center;">
                    <button onclick="excluirFornecedor('${fornecedor.nome}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
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
                <td style="text-align: center;">
                    <button onclick="excluirLancamento(${lanc.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
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
        // Auto-corrige lançamentos com tipo errado (DÉBITO→receita) antes de carregar
        await fetch(`${API_URL}/lancamentos/corrigir-tipos-conciliacao`, { method: 'POST' }).catch(() => {});

        console.log('   📡 Buscando lançamentos...');
        const perPageSelect = document.getElementById('per-page-receber');
        const perPage = perPageSelect ? perPageSelect.value : 300;
        const response = await fetch(`${API_URL}/lancamentos?per_page=${perPage}&page=1&tipo=receita`);
        const responseData = await response.json();
        const todosLancamentos = Array.isArray(responseData) ? responseData : (responseData.data || []);
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
        
        // Filtros (sem pré-preenchimento de data para exibir todos os registros)
        const filterTextElement = document.getElementById('filter-receber');
        const filterDataInicioElement = document.getElementById('filter-data-inicio-receber');
        const filterDataFimElement = document.getElementById('filter-data-fim-receber');
        const filterStatusElement = document.getElementById('filter-status-receber');
        const filterCategoriaElement = document.getElementById('filter-categoria-receber');
        const filterClienteElement = document.getElementById('filter-cliente');
        const filterAnoElement = document.getElementById('filter-ano-receber');
        const filterMesElement = document.getElementById('filter-mes-receber');
        
        const filterText = filterTextElement ? filterTextElement.value.toLowerCase() : '';
        const filterStatus = filterStatusElement ? filterStatusElement.value : '';
        const filterCategoria = filterCategoriaElement ? filterCategoriaElement.value : '';
        const filterCliente = filterClienteElement ? filterClienteElement.value : '';
        const filterAno = filterAnoElement ? filterAnoElement.value : '';
        const filterMes = filterMesElement ? filterMesElement.value : '';
        const filterDataInicio = filterDataInicioElement ? filterDataInicioElement.value : '';
        const filterDataFim = filterDataFimElement ? filterDataFimElement.value : '';
        
        // Filtrar receitas
        const receitas = todosLancamentos.filter(lanc => {
            const isReceita = lanc.tipo && lanc.tipo.toUpperCase() === 'RECEITA';
            if (!isReceita) return false;
            
            const matchText = !filterText || lanc.descricao.toLowerCase().includes(filterText) || 
                             (lanc.pessoa && lanc.pessoa.toLowerCase().includes(filterText));
            const matchStatus = !filterStatus || (lanc.status && lanc.status.toUpperCase() === filterStatus.toUpperCase());
            const matchCategoria = !filterCategoria || lanc.categoria === filterCategoria;
            const matchCliente = !filterCliente || lanc.pessoa === filterCliente;
            
            // Filtro por ano
            if (filterAno) {
                const dataVenc = new Date(lanc.data_vencimento);
                if (dataVenc.getFullYear() !== parseInt(filterAno)) return false;
            }
            
            // Filtro por mês
            if (filterMes) {
                const dataVenc = new Date(lanc.data_vencimento);
                const mes = String(dataVenc.getMonth() + 1).padStart(2, '0');
                if (mes !== filterMes) return false;
            }
            
            // Filtro por data inicial
            if (filterDataInicio) {
                const dataVenc = new Date(lanc.data_vencimento);
                const dataInicio = new Date(filterDataInicio);
                if (dataVenc < dataInicio) return false;
            }
            
            // Filtro por data final
            if (filterDataFim) {
                const dataVenc = new Date(lanc.data_vencimento);
                const dataFim = new Date(filterDataFim);
                if (dataVenc > dataFim) return false;
            }
            
            return matchText && matchStatus && matchCategoria && matchCliente;
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
                <td>${lanc.associacao || lanc.numero_documento || '-'}</td>
                <td>${lanc.descricao}</td>
                <td>${lanc.categoria || '-'}</td>
                <td>${lanc.subcategoria || '-'}</td>
                <td style="font-weight: bold; color: #27ae60;">${formatarMoeda(lanc.valor)}</td>
                <td><span class="badge ${statusClass}">${lanc.status || 'PENDENTE'}</span></td>
                <td style="white-space: nowrap; text-align: center;">
                    <button onclick="editarReceita(${lanc.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar">✏️</button>
                    <button onclick="excluirLancamento(${lanc.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
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
        
        // Atualizar contador de registros
        const contadorElement = document.getElementById('total-registros-receber');
        if (contadorElement) {
            contadorElement.textContent = receitas.length;
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
        // Auto-corrige lançamentos com tipo errado (CRÉDITO→despesa) antes de carregar
        await fetch(`${API_URL}/lancamentos/corrigir-tipos-conciliacao`, { method: 'POST' }).catch(() => {});

        const perPageSelect = document.getElementById('per-page-pagar');
        const perPage = perPageSelect ? perPageSelect.value : 300;
        const response = await fetch(`${API_URL}/lancamentos?per_page=${perPage}&page=1&tipo=despesa`);
        const responseData = await response.json();
        const todosLancamentos = Array.isArray(responseData) ? responseData : (responseData.data || []);
        
        const tbody = document.getElementById('tbody-pagar');
        tbody.innerHTML = '';
        
        // Filtros (sem pré-preenchimento de data para exibir todos os registros)
        const filterTextElement = document.getElementById('filter-pagar');
        const filterDataInicioElement = document.getElementById('filter-data-inicio-pagar');
        const filterDataFimElement = document.getElementById('filter-data-fim-pagar');
        const filterStatusElement = document.getElementById('filter-status-pagar');
        const filterCategoriaElement = document.getElementById('filter-categoria-pagar');
        const filterFornecedorElement = document.getElementById('filter-fornecedor');
        const filterAnoElement = document.getElementById('filter-ano-pagar');
        const filterMesElement = document.getElementById('filter-mes-pagar');
        
        const filterText = filterTextElement ? filterTextElement.value.toLowerCase() : '';
        const filterStatus = filterStatusElement ? filterStatusElement.value : '';
        const filterCategoria = filterCategoriaElement ? filterCategoriaElement.value : '';
        const filterFornecedor = filterFornecedorElement ? filterFornecedorElement.value : '';
        const filterAno = filterAnoElement ? filterAnoElement.value : '';
        const filterMes = filterMesElement ? filterMesElement.value : '';
        const filterDataInicio = filterDataInicioElement ? filterDataInicioElement.value : '';
        const filterDataFim = filterDataFimElement ? filterDataFimElement.value : '';
        
        // Filtrar despesas
        const despesas = todosLancamentos.filter(lanc => {
            const isDespesa = lanc.tipo && lanc.tipo.toUpperCase() === 'DESPESA';
            if (!isDespesa) return false;
            
            const matchText = !filterText || lanc.descricao.toLowerCase().includes(filterText) || 
                             (lanc.pessoa && lanc.pessoa.toLowerCase().includes(filterText));
            const matchStatus = !filterStatus || (lanc.status && lanc.status.toUpperCase() === filterStatus.toUpperCase());
            const matchCategoria = !filterCategoria || lanc.categoria === filterCategoria;
            const matchFornecedor = !filterFornecedor || lanc.pessoa === filterFornecedor;
            
            // Filtro por ano
            if (filterAno) {
                const dataVenc = new Date(lanc.data_vencimento);
                if (dataVenc.getFullYear() !== parseInt(filterAno)) return false;
            }
            
            // Filtro por mês
            if (filterMes) {
                const dataVenc = new Date(lanc.data_vencimento);
                const mes = String(dataVenc.getMonth() + 1).padStart(2, '0');
                if (mes !== filterMes) return false;
            }
            
            // Filtro por data inicial
            if (filterDataInicio) {
                const dataVenc = new Date(lanc.data_vencimento);
                const dataInicio = new Date(filterDataInicio);
                if (dataVenc < dataInicio) return false;
            }
            
            // Filtro por data final
            if (filterDataFim) {
                const dataVenc = new Date(lanc.data_vencimento);
                const dataFim = new Date(filterDataFim);
                if (dataVenc > dataFim) return false;
            }
            
            return matchText && matchStatus && matchCategoria && matchFornecedor;
        });
        
        // Atualizar contador de registros
        const contadorElement = document.getElementById('total-registros-pagar');
        if (contadorElement) {
            contadorElement.textContent = despesas.length;
        }
        
        despesas.forEach(lanc => {
            const tr = document.createElement('tr');
            const statusClass = lanc.status && lanc.status.toUpperCase() === 'PAGO' ? 'badge-success' : 
                               lanc.status && lanc.status.toUpperCase() === 'VENCIDO' ? 'badge-danger' : 'badge-warning';
            
            tr.innerHTML = `
                <td><input type="checkbox" class="checkbox-pagar" value="${lanc.id}"></td>
                <td>${formatarData(lanc.data_vencimento)}</td>
                <td>${lanc.pessoa || '-'}</td>
                <td>${lanc.associacao || lanc.numero_documento || '-'}</td>
                <td>${lanc.descricao}</td>
                <td>${lanc.categoria || '-'}</td>
                <td>${lanc.subcategoria || '-'}</td>
                <td style="font-weight: bold; color: #e74c3c;">${formatarMoeda(lanc.valor)}</td>
                <td><span class="badge ${statusClass}">${lanc.status || 'PENDENTE'}</span></td>
                <td style="white-space: nowrap; text-align: center;">
                    <button onclick="editarDespesa(${lanc.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar">✏️</button>
                    <button onclick="excluirLancamento(${lanc.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
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

async function excluirTudoNaTela(tbodyTipo) {
    // Coleta apenas IDs dentro do tbody correto (escopo seguro)
    const tbody = document.getElementById(`tbody-${tbodyTipo}`);
    const checkboxes = tbody ? tbody.querySelectorAll(`.checkbox-${tbodyTipo}`) : [];
    const ids = Array.from(checkboxes).map(cb => cb.value).filter(Boolean);

    if (ids.length === 0) {
        showToast('Nenhum registro na tela para excluir.', 'warning');
        return;
    }

    const tipo = tbodyTipo === 'receber' ? 'Contas a Receber' : 'Contas a Pagar';

    // Verifica se algum filtro está ativo — sem filtros significa excluir TODOS os registros
    const filterIds = [
        `filter-${tbodyTipo}`,
        `filter-status-${tbodyTipo}`,
        `filter-categoria-${tbodyTipo}`,
        `filter-subcategoria-${tbodyTipo}`,
        `filter-ano-${tbodyTipo}`,
        `filter-mes-${tbodyTipo}`,
        `filter-data-inicio-${tbodyTipo}`,
        `filter-data-fim-${tbodyTipo}`,
    ];
    const semFiltros = filterIds.every(id => {
        const el = document.getElementById(id);
        return !el || !el.value;
    });
    if (semFiltros) {
        if (!confirm(`🚨 PERIGO — SEM FILTROS ATIVOS!\n\nNenhum filtro está ativo. Isso irá excluir TODOS os ${ids.length} registro(s) de ${tipo} desta página!\n\nSe você tem mais registros do que o limite de página (300), os demais NÃO serão apagados agora, mas esta ação ainda é IRREVERSÍVEL.\n\nTem certeza absoluta que deseja excluir TUDO?`)) return;
    }

    if (!confirm(`⚠️ ATENÇÃO!\n\nIsso irá excluir PERMANENTEMENTE ${ids.length} registro(s) de ${tipo}.\n\nEsta ação NÃO pode ser desfeita!\n\nConfirma?`)) return;
    // Segunda confirmação — ação destrutiva em massa
    if (!confirm(`Última confirmação: excluir ${ids.length} registro(s) de ${tipo}?`)) return;

    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

        showToast(`Excluindo ${ids.length} registro(s)... aguarde.`, 'info');

        const res = await fetch(`${API_URL}/lancamentos/bulk-delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ ids: ids.map(Number) })
        });
        const r = await res.json();

        if (r.success) {
            showToast(`✅ ${r.deleted} registro(s) excluído(s) com sucesso.`, 'success');
        } else {
            showToast(`❌ Erro ao excluir: ${r.error}`, 'error');
        }

        if (tbodyTipo === 'receber') loadContasReceber();
        else loadContasPagar();
        if (typeof loadDashboard === 'function') loadDashboard();
    } catch (error) {
        console.error('Erro ao excluir tudo na tela:', error);
        showToast('Erro ao excluir registros.', 'error');
    }
}
window.excluirTudoNaTela = excluirTudoNaTela;

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

        const res = await fetch(`${API_URL}/lancamentos/bulk-delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ ids: ids.map(Number) })
        });
        const result = await res.json();

        if (result.success) {
            showToast(`✅ ${result.deleted} excluído(s).`, 'success');
        } else {
            showToast(`❌ Erro: ${result.error}`, 'error');
        }
        
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

// === CONTROLE DE HORAS ===
async function loadControleHoras() {
    try {
        console.log('⏱️ Carregando relatório de controle de horas...');
        
        const response = await fetch(`${API_URL}/relatorios/controle-horas`);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Erro ao carregar relatório');
        }
        
        const dados = result.dados;
        const resumo = dados.resumo;
        const contratos = dados.contratos;
        
        // Renderizar resumo em cards
        const resumoContainer = document.getElementById('controle-horas-resumo');
        resumoContainer.innerHTML = `
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">Total de Contratos</div>
                <div style="font-size: 28px; font-weight: bold;">${resumo.total_contratos}</div>
                <div style="font-size: 12px; opacity: 0.8; margin-top: 5px;">${resumo.contratos_ativos} ativos</div>
            </div>
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">Com Controle de Horas</div>
                <div style="font-size: 28px; font-weight: bold;">${resumo.contratos_com_controle_horas}</div>
                <div style="font-size: 12px; opacity: 0.8; margin-top: 5px;">${resumo.total_sessoes} sessões</div>
            </div>
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">Horas Contratadas</div>
                <div style="font-size: 28px; font-weight: bold;">${parseFloat(resumo.total_horas_contratadas).toFixed(1)}h</div>
                <div style="font-size: 12px; opacity: 0.8; margin-top: 5px;">Total disponível</div>
            </div>
            <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">Horas Utilizadas</div>
                <div style="font-size: 28px; font-weight: bold;">${parseFloat(resumo.total_horas_utilizadas).toFixed(1)}h</div>
                <div style="font-size: 12px; opacity: 0.8; margin-top: 5px;">${(resumo.total_horas_contratadas > 0 ? (resumo.total_horas_utilizadas / resumo.total_horas_contratadas * 100) : 0).toFixed(1)}% usado</div>
            </div>
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 20px; border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">Horas Restantes</div>
                <div style="font-size: 28px; font-weight: bold;">${parseFloat(resumo.total_horas_restantes).toFixed(1)}h</div>
                <div style="font-size: 12px; opacity: 0.8; margin-top: 5px;">Disponível</div>
            </div>
            <div style="background: linear-gradient(135deg, #ff0844 0%, #ffb199 100%); padding: 20px; border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">Horas Extras</div>
                <div style="font-size: 28px; font-weight: bold;">${parseFloat(resumo.total_horas_extras).toFixed(1)}h</div>
                <div style="font-size: 12px; opacity: 0.8; margin-top: 5px;">Acima do contratado</div>
            </div>
        `;
        
        // Renderizar tabela de contratos
        const contratosContainer = document.getElementById('controle-horas-contratos');
        const emptyContainer = document.getElementById('controle-horas-empty');
        
        if (contratos.length === 0) {
            contratosContainer.style.display = 'none';
            emptyContainer.style.display = 'block';
            return;
        }
        
        contratosContainer.style.display = 'block';
        emptyContainer.style.display = 'none';
        
        let tabelaHTML = `
            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
                <thead>
                    <tr style="background: #34495e; color: white;">
                        <th style="padding: 12px; text-align: left; font-size: 13px;">Nº Contrato</th>
                        <th style="padding: 12px; text-align: left; font-size: 13px;">Cliente</th>
                        <th style="padding: 12px; text-align: center; font-size: 13px;">H. Totais</th>
                        <th style="padding: 12px; text-align: center; font-size: 13px;">H. Utilizadas</th>
                        <th style="padding: 12px; text-align: center; font-size: 13px;">H. Restantes</th>
                        <th style="padding: 12px; text-align: center; font-size: 13px;">H. Extras</th>
                        <th style="padding: 12px; text-align: center; font-size: 13px;">% Utilizado</th>
                        <th style="padding: 12px; text-align: center; font-size: 13px;">Status</th>
                        <th style="padding: 12px; text-align: center; font-size: 13px;">Sessões</th>
                        <th style="padding: 12px; text-align: center; font-size: 13px;">Ações</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        contratos.forEach((contrato, index) => {
            const bgColor = index % 2 === 0 ? '#f8f9fa' : '#ffffff';
            const percentual = contrato.percentual_utilizado || 0;
            
            let statusIcon = '✅';
            let statusText = 'OK';
            let statusColor = '#27ae60';
            
            if (contrato.horas_extras > 0) {
                statusIcon = '⚠️';
                statusText = 'Extras';
                statusColor = '#e74c3c';
            } else if (contrato.horas_restantes <= 5) {
                statusIcon = '⚡';
                statusText = 'Baixo';
                statusColor = '#f39c12';
            }
            
            tabelaHTML += `
                <tr style="background: ${bgColor}; border-bottom: 1px solid #ecf0f1;">
                    <td style="padding: 12px; font-size: 13px; font-weight: bold;">${contrato.numero}</td>
                    <td style="padding: 12px; font-size: 13px;">${contrato.cliente_nome}</td>
                    <td style="padding: 12px; text-align: center; font-size: 13px;">${parseFloat(contrato.horas_totais).toFixed(1)}h</td>
                    <td style="padding: 12px; text-align: center; font-size: 13px;">${parseFloat(contrato.horas_utilizadas).toFixed(1)}h</td>
                    <td style="padding: 12px; text-align: center; font-size: 13px; font-weight: bold; color: ${contrato.horas_restantes < 0 ? '#e74c3c' : '#27ae60'};">
                        ${parseFloat(contrato.horas_restantes).toFixed(1)}h
                    </td>
                    <td style="padding: 12px; text-align: center; font-size: 13px; ${contrato.horas_extras > 0 ? 'color: #e74c3c; font-weight: bold;' : ''}">
                        ${parseFloat(contrato.horas_extras).toFixed(1)}h
                    </td>
                    <td style="padding: 12px; text-align: center; font-size: 13px;">
                        <div style="background: #ecf0f1; border-radius: 10px; height: 20px; overflow: hidden; position: relative;">
                            <div style="background: ${percentual > 90 ? '#e74c3c' : percentual > 75 ? '#f39c12' : '#27ae60'}; height: 100%; width: ${Math.min(percentual, 100)}%;"></div>
                            <span style="position: absolute; top: 0; left: 0; right: 0; text-align: center; line-height: 20px; font-size: 11px; font-weight: bold; color: #2c3e50;">
                                ${percentual.toFixed(1)}%
                            </span>
                        </div>
                    </td>
                    <td style="padding: 12px; text-align: center; font-size: 13px;">
                        <span style="background: ${statusColor}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: bold;">
                            ${statusIcon} ${statusText}
                        </span>
                    </td>
                    <td style="padding: 12px; text-align: center; font-size: 13px;">${contrato.total_sessoes}</td>
                    <td style="padding: 12px; text-align: center; font-size: 13px;">
                        <button 
                            onclick="abrirCompensacaoHoras(${contrato.id})" 
                            style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold; transition: transform 0.2s;"
                            onmouseover="this.style.transform='scale(1.05)'"
                            onmouseout="this.style.transform='scale(1)'"
                            title="Compensar horas entre contratos do mesmo cliente">
                            🔄 Compensar
                        </button>
                    </td>
                </tr>
            `;
        });
        
        tabelaHTML += `
                </tbody>
            </table>
        `;
        
        contratosContainer.innerHTML = tabelaHTML;
        
        console.log('✅ Relatório de controle de horas carregado com sucesso');
        
    } catch (error) {
        console.error('❌ Erro ao carregar controle de horas:', error);
        showToast('Erro ao carregar relatório de controle de horas', 'error');
    }
}

/**
 * Exporta relatório de controle de horas para PDF
 */
function exportarControleHorasPDF() {
    console.log('📄 Exportando controle de horas para PDF');
    window.location.href = '/api/relatorios/controle-horas/exportar/pdf';
}

/**
 * Exporta relatório de controle de horas para Excel
 */
function exportarControleHorasExcel() {
    console.log('📊 Exportando controle de horas para Excel');
    window.location.href = '/api/relatorios/controle-horas/exportar/excel';
}

// === COMPENSAÇÃO DE HORAS ENTRE CONTRATOS ===

/**
 * Abre modal de compensação de horas entre contratos
 */
async function abrirCompensacaoHoras(contratoId) {
    try {
        console.log(`🔄 Abrindo compensação de horas para contrato ${contratoId}`);
        
        // Remover modal anterior se existir
        const modalAnterior = document.getElementById('modal-compensacao-overlay');
        if (modalAnterior) {
            console.log('🗑️ Removendo modal anterior');
            modalAnterior.remove();
        }
        
        // Buscar todos os contratos do mesmo cliente
        const response = await fetch(`${API_URL}/contratos`);
        const contratos = await response.json();
        
        // Buscar contrato selecionado
        const contratoAtual = contratos.find(c => c.id === contratoId);
        console.log('📋 Contrato atual:', contratoAtual);
        
        if (!contratoAtual) {
            showToast('Contrato não encontrado', 'error');
            console.error('❌ Contrato não encontrado com ID:', contratoId);
            return;
        }
        
        console.log('👤 Cliente ID do contrato:', contratoAtual.cliente_id);
        console.log('📊 Total de contratos disponíveis:', contratos.length);

        if (!contratoAtual.cliente_id) {
            showToast('Este contrato não possui cliente vinculado. Associe um cliente ao contrato para usar a compensação de horas.', 'error');
            return;
        }
        
        // Filtrar contratos do mesmo cliente com controle de horas
        const contratosMesmoCliente = contratos.filter(c => 
            c.cliente_id === contratoAtual.cliente_id &&
            c.controle_horas_ativo &&
            c.id !== contratoId
        );
        
        console.log(`🔍 Contratos do mesmo cliente encontrados: ${contratosMesmoCliente.length}`);
        
        if (contratosMesmoCliente.length === 0) {
            showToast('Este cliente não possui outros contratos com controle de horas', 'info');
            console.warn('⚠️ Nenhum outro contrato do mesmo cliente com controle de horas');
            return;
        }
        
        // Calcular saldo disponível do contrato atual
        const saldoAtual = (parseFloat(contratoAtual.horas_totais) || 0) - (parseFloat(contratoAtual.horas_utilizadas) || 0);
        
        // Criar modal
        const modalHTML = `
            <div class="modal-overlay" id="modal-compensacao-overlay" onclick="if(event.target === this) fecharCompensacaoHoras()">
                <div class="modal-dialog" style="max-width: 600px;" onclick="event.stopPropagation()">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3 style="margin: 0; color: #2c3e50; display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 24px;">🔄</span>
                                Compensar Horas Entre Contratos
                            </h3>
                            <button type="button" class="close" onclick="fecharCompensacaoHoras()" style="font-size: 28px; border: none; background: none; cursor: pointer; color: #95a5a6;">
                                &times;
                            </button>
                        </div>
                        <div class="modal-body" style="padding: 25px;">
                            <!-- Info do Contrato Atual -->
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 10px; color: white; margin-bottom: 20px;">
                                <div style="font-size: 13px; opacity: 0.9; margin-bottom: 5px;">Contrato Selecionado</div>
                                <div style="font-size: 18px; font-weight: bold;">${contratoAtual.numero}</div>
                                <div style="font-size: 14px; margin-top: 5px;">${contratoAtual.cliente_nome}</div>
                                <div style="font-size: 13px; margin-top: 8px; opacity: 0.95;">
                                    💰 Saldo Disponível: <strong>${saldoAtual.toFixed(1)}h</strong>
                                </div>
                            </div>
                            
                            <!-- Tipo de Operação -->
                            <div class="form-group" style="margin-bottom: 20px;">
                                <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #2c3e50;">
                                    Tipo de Compensação
                                </label>
                                <select id="tipo-compensacao" class="form-control" onchange="atualizarOpcoesCompensacao(${contratoId})" style="padding: 10px; border-radius: 6px; border: 1px solid #ddd;">
                                    <option value="doar">Doar horas deste contrato para outro</option>
                                    <option value="receber">Receber horas de outro contrato</option>
                                </select>
                            </div>
                            
                            <!-- Contrato Origem/Destino -->
                            <div class="form-group" style="margin-bottom: 20px;">
                                <label id="label-outro-contrato" style="display: block; font-weight: 600; margin-bottom: 8px; color: #2c3e50;">
                                    Contrato Destino (receberá as horas)
                                </label>
                                <select id="outro-contrato" class="form-control" style="padding: 10px; border-radius: 6px; border: 1px solid #ddd;">
                                    ${contratosMesmoCliente.map(c => {
                                        const saldo = (parseFloat(c.horas_totais) || 0) - (parseFloat(c.horas_utilizadas) || 0);
                                        return `<option value="${c.id}" data-saldo="${saldo}">${c.numero} - Saldo: ${saldo.toFixed(1)}h</option>`;
                                    }).join('')}
                                </select>
                            </div>
                            
                            <!-- Quantidade de Horas -->
                            <div class="form-group" style="margin-bottom: 20px;">
                                <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #2c3e50;">
                                    Quantidade de Horas
                                </label>
                                <input type="number" id="quantidade-horas-compensacao" class="form-control" 
                                    step="0.5" min="0.5" max="${saldoAtual}" 
                                    placeholder="Ex: 10.5"
                                    style="padding: 10px; border-radius: 6px; border: 1px solid #ddd;">
                                <small id="max-horas-info" style="color: #7f8c8d; font-size: 12px; margin-top: 5px; display: block;">
                                    Máximo disponível: ${saldoAtual.toFixed(1)}h
                                </small>
                            </div>
                            
                            <!-- Observação/Motivo -->
                            <div class="form-group" style="margin-bottom: 20px;">
                                <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #2c3e50;">
                                    Motivo da Compensação
                                </label>
                                <textarea id="observacao-compensacao" class="form-control" rows="3" 
                                    placeholder="Ex: Compensar excesso de horas extras em eventos..."
                                    style="padding: 10px; border-radius: 6px; border: 1px solid #ddd; resize: vertical;"></textarea>
                            </div>
                        </div>
                        <div class="modal-footer" style="padding: 15px 25px; background: #f8f9fa; border-top: 1px solid #dee2e6; display: flex; gap: 10px; justify-content: flex-end;">
                            <button type="button" class="btn btn-secondary" onclick="fecharCompensacaoHoras()" style="padding: 10px 20px;">
                                Cancelar
                            </button>
                            <button type="button" class="btn btn-primary" onclick="executarCompensacaoHoras(${contratoId})" style="padding: 10px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none;">
                                🔄 Confirmar Compensação
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Inserir modal no DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Verificar se modal foi criado
        const modalCriado = document.getElementById('modal-compensacao-overlay');
        if (modalCriado) {
            console.log('✅ Modal de compensação criado e encontrado no DOM');
            console.log('📍 Display do modal:', window.getComputedStyle(modalCriado).display);
            console.log('📍 Visibility do modal:', window.getComputedStyle(modalCriado).visibility);
            console.log('📍 Z-index do modal:', window.getComputedStyle(modalCriado).zIndex);
            
            // Forçar visibilidade e z-index com !important
            modalCriado.style.cssText = `
                display: flex !important;
                opacity: 1 !important;
                visibility: visible !important;
                z-index: 10000 !important;
            `;
            modalCriado.style.zIndex = '10000';
            
            console.log('🎯 Modal forçado a ser visível');
        } else {
            console.error('❌ Modal NÃO foi encontrado no DOM após inserção!');
        }
        
    } catch (error) {
        console.error('❌ Erro ao abrir compensação:', error);
        showToast('Erro ao abrir modal de compensação', 'error');
    }
}

/**
 * Atualiza opções do modal baseado no tipo de compensação
 */
function atualizarOpcoesCompensacao(contratoId) {
    const tipo = document.getElementById('tipo-compensacao').value;
    const label = document.getElementById('label-outro-contrato');
    const maxHorasInfo = document.getElementById('max-horas-info');
    const inputHoras = document.getElementById('quantidade-horas-compensacao');
    
    if (tipo === 'doar') {
        label.textContent = 'Contrato Destino (receberá as horas)';
        // Máximo é o saldo do contrato atual
    } else {
        label.textContent = 'Contrato Origem (doará as horas)';
        // Máximo é o saldo do contrato selecionado
        const select = document.getElementById('outro-contrato');
        const saldoOutro = parseFloat(select.selectedOptions[0].dataset.saldo);
        inputHoras.max = saldoOutro;
        maxHorasInfo.textContent = `Máximo disponível: ${saldoOutro.toFixed(1)}h`;
    }
}

/**
 * Executa a compensação de horas
 */
async function executarCompensacaoHoras(contratoAtualId) {
    try {
        const tipo = document.getElementById('tipo-compensacao').value;
        const outroContratoId = parseInt(document.getElementById('outro-contrato').value);
        const quantidade = parseFloat(document.getElementById('quantidade-horas-compensacao').value);
        const observacao = document.getElementById('observacao-compensacao').value;
        
        // Validações
        if (!quantidade || quantidade <= 0) {
            showToast('Informe uma quantidade válida de horas', 'warning');
            return;
        }
        
        if (!observacao.trim()) {
            showToast('Informe o motivo da compensação', 'warning');
            return;
        }
        
        // Determinar origem e destino baseado no tipo
        let origemId, destinoId;
        if (tipo === 'doar') {
            origemId = contratoAtualId;
            destinoId = outroContratoId;
        } else {
            origemId = outroContratoId;
            destinoId = contratoAtualId;
        }
        
        console.log(`🔄 Executando compensação: ${origemId} → ${destinoId} (${quantidade}h)`);
        
        // Executar compensação
        const response = await fetch(`${API_URL}/contratos/${origemId}/compensar-horas`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken || ''
            },
            body: JSON.stringify({
                contrato_destino_id: destinoId,
                quantidade_horas: quantidade,
                observacao: observacao
            })
        });
        
        const result = await response.json();
        
        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Erro ao compensar horas');
        }
        
        console.log('✅ Compensação realizada:', result);
        
        showToast(`✅ Compensadas ${quantidade}h com sucesso!`, 'success');
        
        // Fechar modal
        fecharCompensacaoHoras();
        
        // Recarregar controle de horas se estiver na tela
        if (typeof loadControleHoras === 'function') {
            setTimeout(() => loadControleHoras(), 500);
        }
        
    } catch (error) {
        console.error('❌ Erro ao compensar horas:', error);
        showToast(error.message || 'Erro ao compensar horas', 'error');
    }
}

/**
 * Fecha modal de compensação
 */
function fecharCompensacaoHoras() {
    const overlay = document.getElementById('modal-compensacao-overlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * Exporta relatório de inadimplência para PDF
 */
function exportarInadimplenciaPDF() {
    console.log('📄 Exportando inadimplência para PDF');
    showToast('Exportação PDF em desenvolvimento', 'info');
}

/**
 * Exporta relatório de inadimplência para Excel
 */
function exportarInadimplenciaExcel() {
    console.log('📊 Exportando inadimplência para Excel');
    showToast('Exportação Excel em desenvolvimento', 'info');
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
        if (!window.fluxoCaixaTransacoes || window.fluxoCaixaTransacoes.length === 0) {
            showToast('Carregue o fluxo de caixa primeiro', 'warning');
            return;
        }
        
        // Criar versão para impressão com transações detalhadas
        const printWindow = window.open('', '_blank');
        const transacoes = window.fluxoCaixaTransacoes;
        
        let html = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Fluxo de Caixa - ${new Date().toLocaleDateString('pt-BR')}</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; font-size: 12px; }
                    h1 { color: #2c3e50; text-align: center; margin-bottom: 5px; }
                    .subtitle { text-align: center; color: #7f8c8d; margin-bottom: 20px; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    th, td { padding: 8px; text-align: left; border: 1px solid #ddd; font-size: 11px; }
                    th { background: #34495e; color: white; font-weight: bold; }
                    .entrada { color: #27ae60; font-weight: bold; text-align: right; }
                    .saida { color: #e74c3c; font-weight: bold; text-align: right; }
                    .total { font-weight: bold; background: #ecf0f1; }
                    @media print {
                        body { margin: 0; padding: 10px; }
                        table { page-break-inside: auto; }
                        tr { page-break-inside: avoid; }
                    }
                </style>
            </head>
            <body>
                <h1>📈 Fluxo de Caixa - Transações Detalhadas</h1>
                <p class="subtitle">Gerado em: ${new Date().toLocaleString('pt-BR')}</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Data</th>
                            <th>Descrição</th>
                            <th>Categoria</th>
                            <th style="text-align: right;">Entrada</th>
                            <th style="text-align: right;">Saída</th>
                            <th>Conta</th>
                            <th>Associação</th>
                        </tr>
                    </thead>
                    <tbody>`;
        
        let totalEntradas = 0;
        let totalSaidas = 0;
        
        transacoes.forEach(t => {
            const entrada = t.tipo === 'receita' ? t.valor : 0;
            const saida = t.tipo === 'despesa' ? t.valor : 0;
            
            totalEntradas += entrada;
            totalSaidas += saida;
            
            html += `
                <tr>
                    <td>${formatarData(t.data_pagamento)}</td>
                    <td>${t.descricao || '-'}</td>
                    <td>${t.categoria || '-'}</td>
                    <td class="entrada">${entrada > 0 ? formatarMoeda(entrada) : '-'}</td>
                    <td class="saida">${saida > 0 ? formatarMoeda(saida) : '-'}</td>
                    <td>${t.conta_bancaria || '-'}</td>
                    <td>${t.associacao || '-'}</td>
                </tr>`;
        });
        
        html += `
                        <tr class="total">
                            <td colspan="3"><strong>TOTAL</strong></td>
                            <td class="entrada"><strong>${formatarMoeda(totalEntradas)}</strong></td>
                            <td class="saida"><strong>${formatarMoeda(totalSaidas)}</strong></td>
                            <td colspan="2"><strong>Saldo: ${formatarMoeda(totalEntradas - totalSaidas)}</strong></td>
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
        if (!window.fluxoCaixaTransacoes || window.fluxoCaixaTransacoes.length === 0) {
            showToast('Carregue o fluxo de caixa primeiro', 'warning');
            return;
        }
        
        const transacoes = window.fluxoCaixaTransacoes;
        
        // Criar CSV (compatível com Excel) com transações detalhadas
        let csv = 'Data,Descrição,Categoria,Entrada,Saída,Conta,Associação\n';
        
        let totalEntradas = 0;
        let totalSaidas = 0;
        
        transacoes.forEach(t => {
            const entrada = t.tipo === 'receita' ? t.valor : 0;
            const saida = t.tipo === 'despesa' ? t.valor : 0;
            
            totalEntradas += entrada;
            totalSaidas += saida;
            
            const data = formatarData(t.data_pagamento);
            const descricao = (t.descricao || '-').replace(/,/g, ';'); // Escapar vírgulas
            const categoria = (t.categoria || '-').replace(/,/g, ';');
            const conta = (t.conta_bancaria || '-').replace(/,/g, ';');
            const associacao = (t.associacao || '-').replace(/,/g, ';');
            
            csv += `${data},${descricao},${categoria},${entrada.toFixed(2)},${saida.toFixed(2)},${conta},${associacao}\n`;
        });
        
        csv += `\nTOTAL,,,${totalEntradas.toFixed(2)},${totalSaidas.toFixed(2)},,\n`;
        csv += `SALDO,,,,,${(totalEntradas - totalSaidas).toFixed(2)},`;
        
        // Download do arquivo
        const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' }); // \uFEFF = BOM para UTF-8
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', `fluxo_caixa_detalhado_${new Date().toISOString().split('T')[0]}.csv`);
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
        
        // Filtrar apenas contas ativas
        const contasAtivas = contas.filter(c => c.ativa !== false);
        
        // Preencher selects (ambos IDs por compatibilidade)
        const selectImportar = document.getElementById('conta-bancaria-extrato') || document.getElementById('extrato-conta-importar');
        const selectFiltro = document.getElementById('filtro-conta-extrato') || document.getElementById('extrato-filter-conta');
        
        if (selectImportar) {
            selectImportar.innerHTML = '<option value="">Selecione a conta</option>';
            contasAtivas.forEach(conta => {
                selectImportar.innerHTML += `<option value="${conta.nome}">${conta.nome}</option>`;
            });
        }
        
        if (selectFiltro) {
            // Filtro pode mostrar todas (incluindo inativas) para visualização
            selectFiltro.innerHTML = '<option value="">Todas as contas</option>';
            contas.forEach(conta => {
                const statusLabel = conta.ativa === false ? ' (INATIVA)' : '';
                selectFiltro.innerHTML += `<option value="${conta.nome}">${conta.nome}${statusLabel}</option>`;
            });
        }
        
        // 🚀 Preencher filtros de data automaticamente (início do mês até hoje)
        const hoje = new Date();
        const primeiroDiaMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
        
        // Formatar datas para YYYY-MM-DD (formato do input date)
        const dataInicioFormatada = primeiroDiaMes.toISOString().split('T')[0];
        const dataHojeFormatada = hoje.toISOString().split('T')[0];
        
        console.log('🔍 Tentando preencher datas:', { inicio: dataInicioFormatada, fim: dataHojeFormatada });
        
        // Tentar com pequeno delay para garantir que elementos existam e seção esteja ativa
        setTimeout(() => {
            // Verificar se seção está ativa
            const secaoExtrato = document.getElementById('extrato-bancario-section');
            console.log('🔍 Seção extrato-bancario-section:', secaoExtrato ? 'ENCONTRADA' : 'NÃO ENCONTRADA');
            console.log('🔍 Seção está ativa?', secaoExtrato && !secaoExtrato.classList.contains('hidden'));
            
            const dataInicioEl = document.getElementById('filtro-data-inicio-extrato') || document.getElementById('extrato-filter-data-inicio');
            const dataFimEl = document.getElementById('filtro-data-fim-extrato') || document.getElementById('extrato-filter-data-fim');
            
            console.log('🔍 Elementos encontrados:', { 
                dataInicio: dataInicioEl ? 'SIM ✅' : 'NÃO ❌', 
                dataFim: dataFimEl ? 'SIM ✅' : 'NÃO ❌'
            });
            
            if (dataInicioEl) {
                dataInicioEl.value = dataInicioFormatada;
                console.log('📅 ✅ Data início preenchida com:', dataInicioEl.value);
            } else {
                console.error('❌ Elemento filtro-data-inicio-extrato NÃO ENCONTRADO');
                console.log('🔍 Tentando buscar todos inputs date na página...');
                const todosInputsDate = document.querySelectorAll('input[type="date"]');
                console.log('📋 Total de inputs date encontrados:', todosInputsDate.length);
                todosInputsDate.forEach((input, idx) => {
                    console.log(`   [${idx}] ID: ${input.id || 'sem-id'}, Name: ${input.name || 'sem-name'}`);
                });
            }
            
            if (dataFimEl) {
                dataFimEl.value = dataHojeFormatada;
                console.log('📅 ✅ Data fim preenchida com:', dataFimEl.value);
            } else {
                console.error('❌ Elemento filtro-data-fim-extrato NÃO ENCONTRADO');
            }
            
            console.log('✅ Processamento de filtros de data concluído');
        }, 200);
        
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
        
        // 🔒 Tratamento especial para conflito de período (409)
        if (response.status === 409 && result.details) {
            const details = result.details;
            showToast(
                `⚠️ Período já importado!\n\n` +
                `📅 Período do arquivo: ${details.periodo_tentado.inicio} até ${details.periodo_tentado.fim}\n` +
                `📦 Período existente: ${details.periodo_existente.inicio} até ${details.periodo_existente.fim}\n` +
                `📊 Transações existentes: ${details.periodo_existente.transacoes}\n\n` +
                `${details.mensagem}`,
                'warning',
                10000  // 10 segundos
            );
            return;
        }
        
        if (!response.ok) throw new Error(result.error || 'Erro ao importar extrato');
        
        showToast(
            `✅ Importação concluída!\n` +
            `✔️ ${result.transacoes_importadas || result.inseridas || 0} transações inseridas\n` +
            `⚠️ ${result.transacoes_duplicadas || result.duplicadas || 0} transações duplicadas (ignoradas)`,
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
        // Tentar ambos os IDs por compatibilidade (extrato-filter-* e filtro-*-extrato)
        const contaEl = document.getElementById('filtro-conta-extrato') || document.getElementById('extrato-filter-conta');
        const dataInicioEl = document.getElementById('filtro-data-inicio-extrato') || document.getElementById('extrato-filter-data-inicio');
        const dataFimEl = document.getElementById('filtro-data-fim-extrato') || document.getElementById('extrato-filter-data-fim');
        
        // 🚀 PREENCHER DATAS AUTOMATICAMENTE SE ESTIVEREM VAZIAS (fallback)
        if (dataInicioEl && !dataInicioEl.value) {
            const hoje = new Date();
            const primeiroDiaMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
            dataInicioEl.value = primeiroDiaMes.toISOString().split('T')[0];
            console.log('📅 FALLBACK: Data início preenchida com:', dataInicioEl.value);
        }
        if (dataFimEl && !dataFimEl.value) {
            const hoje = new Date();
            dataFimEl.value = hoje.toISOString().split('T')[0];
            console.log('📅 FALLBACK: Data fim preenchida com:', dataFimEl.value);
        }
        
        const conciliadoEl = document.getElementById('filtro-conciliado-extrato') || document.getElementById('extrato-filter-conciliado');
        
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
        
        const responseData = await response.json();
        
        // Suportar novo formato (objeto com transacoes + saldo_anterior) e formato antigo (array direto)
        let extratos, saldoAnterior;
        
        if (Array.isArray(responseData)) {
            // Formato antigo (array direto)
            extratos = responseData;
            saldoAnterior = null;
            console.log(`✅ ${extratos.length} transações recebidas (formato antigo)`);
        } else {
            // Novo formato (objeto com transacoes e saldo_anterior)
            extratos = responseData.transacoes || [];
            saldoAnterior = responseData.saldo_anterior;
            console.log(`✅ ${extratos.length} transações recebidas, saldo anterior: R$ ${saldoAnterior?.toFixed(2) || 'N/A'}`);
        }
        
        // 🔥 IMPORTANTE: Salvar em variável global para uso nas funções de conciliação
        window.extratos = extratos;
        console.log('💾 Transações salvas em window.extratos:', window.extratos.length);
        
        // Renderizar tabela
        const tbody = document.getElementById('tbody-extrato');
        console.log('📍 Elemento tbody-extrato:', tbody);
        
        tbody.innerHTML = '';
        
        if (extratos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px;">Nenhuma transação encontrada</td></tr>';
            console.log('⚠️ Nenhuma transação para exibir');
            return;
        }
        
        console.log('🔄 Renderizando', extratos.length, 'transações...');
        
        // 🏦 ADICIONAR LINHA DE SALDO INICIAL (como nos extratos bancários reais)
        if (extratos.length > 0) {
            let saldoInicial;
            
            // Usar saldo_anterior do backend se disponível, senão calcular
            if (saldoAnterior !== null && saldoAnterior !== undefined) {
                saldoInicial = saldoAnterior;
                console.log('🏦 Usando saldo anterior do backend:', saldoInicial);
            } else {
                // Fallback: calcular como antes (saldo da primeira transação - seu valor)
                const primeiraTransacao = extratos[0];
                saldoInicial = primeiraTransacao.saldo - primeiraTransacao.valor;
                console.log('🏦 Calculando saldo inicial (fallback):', saldoInicial);
            }
            const saldoInicialFormatado = formatarMoeda(saldoInicial);
            const saldoInicialColor = saldoInicial >= 0 ? '#27ae60' : '#c0392b';
            
            const trSaldo = document.createElement('tr');
            trSaldo.style.backgroundColor = '#f8f9fa';
            trSaldo.style.fontWeight = 'bold';
            trSaldo.innerHTML = `
                <td></td>
                <td style="text-transform: uppercase; color: #555;">SALDO</td>
                <td></td>
                <td></td>
                <td style="text-align: right; color: ${saldoInicialColor}; font-size: 16px;">${saldoInicialFormatado}</td>
                <td></td>
                <td></td>
                <td></td>
            `;
            tbody.appendChild(trSaldo);
            console.log('🏦 Linha de saldo inicial adicionada:', saldoInicialFormatado);
        }
        
        // 🔄 RECALCULAR SALDOS: Se temos saldo_anterior, recalcular todos os saldos progressivamente
        // Isso corrige problemas de saldos incorretos causados por duplicatas/múltiplas importações
        let saldoCorrente = saldoAnterior !== null && saldoAnterior !== undefined ? saldoAnterior : 
                            (extratos.length > 0 ? extratos[0].saldo - extratos[0].valor : 0);
        
        console.log(`🔄 Recalculando saldos a partir de R$ ${saldoCorrente.toFixed(2)}`);
        
        extratos.forEach((transacao, index) => {
            // 🔄 RECALCULAR SALDO: somar valor da transação ao saldo corrente
            saldoCorrente += parseFloat(transacao.valor);
            const saldoRecalculado = saldoCorrente;
            
            console.log(`   [${index + 1}/${extratos.length}] ID:${transacao.id} Valor:${transacao.valor} SaldoArmazenado:${transacao.saldo} SaldoRecalculado:${saldoRecalculado.toFixed(2)}`);
            
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
            
            // 🔄 USAR SALDO RECALCULADO ao invés do saldo armazenado (que pode estar errado)
            const saldoFormatado = formatarMoeda(saldoRecalculado);
            const saldoColor = saldoRecalculado >= 0 ? '#27ae60' : '#c0392b';
            
            // Nome da conta bancária (campo correto: conta_bancaria)
            const nomeConta = transacao.conta_bancaria || 'Sem conta';
            
            // Determinar qual botão exibir
            const botaoAcao = !transacao.conciliado ? 
                `<button class="btn btn-sm btn-primary" onclick="console.log('🔵 Botão Conciliar clicado! ID:', ${transacao.id}); mostrarSugestoesConciliacao(${transacao.id})" style="background: #3498db; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">
                    🔗 Conciliar
                </button>` 
                : 
                `<button class="btn btn-sm btn-warning" onclick="console.log('🔵 Botão Desconciliar clicado! ID:', ${transacao.id}); window.desconciliarTransacao(${transacao.id})" style="background: #9b59b6; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">
                    ⚠️ Desconciliar
                </button>`;
            
            console.log(`      ➡️ Botão renderizado para transação ${transacao.id}:`, transacao.conciliado ? 'Desconciliar (conciliado)' : 'Conciliar (pendente)');
            
            tr.innerHTML = `
                <td>${formatarData(transacao.data)}</td>
                <td style="max-width: 300px;">${transacao.descricao}</td>
                <td style="color: ${valorColor}; font-weight: bold; text-align: right;">${valorFormatado}</td>
                <td style="text-align: center;"><span class="badge badge-${isCredito ? 'success' : 'danger'}">${tipoLabel}</span></td>
                <td style="font-weight: bold; color: ${saldoColor}; text-align: right;">${saldoFormatado}</td>
                <td>${nomeConta}</td>
                <td style="text-align: center;">
                    <span style="color: ${statusColor}; font-weight: bold;">
                        ${statusIcon} ${statusText}
                    </span>
                </td>
                <td style="text-align: center;">
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

// Alias para compatibilidade com HTML (onChange chama loadExtratoTransacoes)
window.loadExtratoTransacoes = function() { return loadExtratos(); };

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
        
        const categoriasData = await responseCategorias.json();
        const clientesData = await responseClientes.json();
        const fornecedoresData = await responseFornecedores.json();
        
        // Extrair arrays dos dados (pode vir como {data: [...]} ou direto)
        const categorias = Array.isArray(categoriasData) ? categoriasData : (categoriasData.categorias || categoriasData.data || []);
        const clientes = Array.isArray(clientesData) ? clientesData : (clientesData.clientes || clientesData.data || []);
        const fornecedores = Array.isArray(fornecedoresData) ? fornecedoresData : (fornecedoresData.fornecedores || fornecedoresData.data || []);
        
        console.log('📦 Dados carregados:');
        console.log('   Categorias:', categorias);
        console.log('   Clientes:', clientes);
        console.log('   Fornecedores:', fornecedores);
        
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
        
        // 🤖 DETECTAR REGRA DE AUTO-CONCILIAÇÃO
        let regraDetectada = null;
        let categoriaPreSelecionada = '';
        let subcategoriaPreSelecionada = '';
        let razaoPreSelecionada = '';
        
        try {
            const detectResponse = await fetch(`${API_URL}/regras-conciliacao/detectar`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ descricao: transacao.descricao })
            });
            
            if (detectResponse.ok) {
                const detectResult = await detectResponse.json();
                
                if (detectResult.success && detectResult.regra_encontrada) {
                    regraDetectada = detectResult.regra;
                    console.log('🎯 Regra detectada automaticamente:', regraDetectada);
                    
                    // Pré-selecionar categoria e subcategoria
                    if (regraDetectada.categoria) {
                        categoriaPreSelecionada = regraDetectada.categoria;
                    }
                    if (regraDetectada.subcategoria) {
                        subcategoriaPreSelecionada = regraDetectada.subcategoria;
                    }
                    
                    // Se tem integração com folha e encontrou funcionário
                    if (detectResult.funcionario) {
                        razaoPreSelecionada = detectResult.funcionario.nome;
                        console.log('👤 Funcionário detectado automaticamente:', detectResult.funcionario.nome);
                        showToast(`✅ Funcionário detectado: ${detectResult.funcionario.nome}`, 'success');
                    }
                    // Senão usar cliente padrão da regra
                    else if (regraDetectada.cliente_padrao) {
                        razaoPreSelecionada = regraDetectada.cliente_padrao;
                    }
                    
                    if (regraDetectada.palavra_chave) {
                        showToast(`🤖 Auto-conciliação: "${regraDetectada.palavra_chave}" detectado`, 'info');
                    }
                }
            }
        } catch (error) {
            console.warn('⚠️ Erro ao detectar regra (não crítico):', error);
        }
        
        // Determinar tipo e cor
        console.log('🔍 Tipo da transação:', transacao.tipo);
        const isCredito = transacao.tipo?.toUpperCase() === 'CREDITO';
        console.log('   É crédito?', isCredito);
        const valorColor = isCredito ? '#27ae60' : '#e74c3c';
        
        // Tentar detectar CPF/CNPJ na descrição (se não foi detectado por regra)
        if (!razaoPreSelecionada) {
            const numeros = transacao.descricao.replace(/\D/g, '');
            if (numeros.length === 11 || numeros.length === 14) {
                razaoPreSelecionada = isCredito ? 
                    (clientesPorCPF[numeros] || '') : 
                    (fornecedoresPorCPF[numeros] || '');
            }
        }
        const razaoSugerida = razaoPreSelecionada;
        
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
                            ${formatarMoeda(transacao.valor)}
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
                        ${categoriasOpcoes.map(c => `<option value="${c.nome}" ${c.nome === categoriaPreSelecionada ? 'selected' : ''}>${c.nome}</option>`).join('')}
                    </select>
                    ${categoriaPreSelecionada ? '<small style="color: #27ae60; font-weight: bold;">✅ Auto-selecionado pela regra</small>' : ''}
                </div>
                
                <div class="form-group" style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Subcategoria:</label>
                    <select id="subcategoria-individual" 
                            ${!categoriaPreSelecionada ? 'disabled' : ''}
                            style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 5px; font-size: 14px; background: ${categoriaPreSelecionada ? 'white' : '#f5f5f5'};">
                        <option value="">Primeiro selecione uma categoria</option>
                    </select>
                    ${subcategoriaPreSelecionada ? '<small style="color: #27ae60; font-weight: bold;">✅ Auto-selecionado pela regra</small>' : ''}
                </div>
                
                <div class="form-group" style="margin-bottom: 0;">
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">📝 Descrição:</label>
                    <input type="text" id="descricao-individual" 
                           value="${(transacao.descricao || '').replace(/"/g, '&quot;')}" 
                           placeholder="Descrição personalizada (opcional)" 
                           style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 5px; font-size: 14px; background: #fffef7;">
                    <small style="color: #7f8c8d;">Campo opcional - Deixe em branco para usar a descrição original</small>
                </div>
            </div>`;
        
        console.log('📝 HTML do formulário montado');
        console.log('   Tamanho do HTML:', formHtml.length, 'caracteres');
        console.log('   🎯 Categoria pré-selecionada:', categoriaPreSelecionada || 'Nenhuma');
        console.log('   🎯 Subcategoria pré-selecionada:', subcategoriaPreSelecionada || 'Nenhuma');
        console.log('   🎯 Razão pré-selecionada:', razaoSugerida || 'Nenhuma');
        
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
        
        // Se categoria foi pré-selecionada carregar subcategorias e pré-selecionar
        if (categoriaPreSelecionada) {
            // Aguardar um momento para o DOM estar pronto
            setTimeout(() => {
                carregarSubcategoriasIndividual(categoriaPreSelecionada);
                
                // Se tem subcategoria pré-selecionada, aplicar
                if (subcategoriaPreSelecionada) {
                    setTimeout(() => {
                        const subcatSelect = document.getElementById('subcategoria-individual');
                        if (subcatSelect) {
                            subcatSelect.value = subcategoriaPreSelecionada;
                            console.log('✅ Subcategoria pré-selecionada aplicada:', subcategoriaPreSelecionada);
                        }
                    }, 100);
                }
            }, 50);
        }
        
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

// Debug: Confirmar que a função foi registrada
console.log('✅ window.desconciliarTransacao definida:', typeof window.desconciliarTransacao);

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

// 🆕 Conciliar transação individual (criar lançamento + conciliar)
window.conciliarTransacaoIndividual = async function() {
    try {
        console.log('🔄 Conciliando transação individual...');
        
        // Verificar se  temos transação selecionada
        const transacao = window.transacaoIndividual;
        if (!transacao) {
            showToast('❌ Nenhuma transação selecionada', 'error');
            return;
        }
        
        // Ler dados do formulário
        const razaoSocial = document.getElementById('razao-individual')?.value?.trim();
        const categoria = document.getElementById('categoria-individual')?.value?.trim();
        const subcategoria = document.getElementById('subcategoria-individual')?.value?.trim();
        const descricaoCustom = document.getElementById('descricao-individual')?.value?.trim();
        
        console.log('📋 Dados do formulário:', { razaoSocial, categoria, subcategoria, descricaoCustom });
        
        // Validações
        if (!razaoSocial) {
            showToast('⚠️ Selecione o cliente/fornecedor', 'warning');
            document.getElementById('razao-individual')?.focus();
            return;
        }
        
        if (!categoria) {
            showToast('⚠️ Selecione a categoria', 'warning');
            document.getElementById('categoria-individual')?.focus();
            return;
        }
        
        if (!subcategoria) {
            showToast('⚠️ Selecione a subcategoria', 'warning');
            document.getElementById('subcategoria-individual')?.focus();
            return;
        }
        
        // Determinar tipo do lançamento baseado no tipo da transação
        // ⚠️ FIX: usar tipo como fonte definitiva; valor apenas como fallback quando tipo ausente
        // Nunca deixar parseFloat(valor) > 0 sobrepor um tipo='DEBITO' explícito
        const tipoExtratoUpper = (transacao.tipo || '').toUpperCase();
        const isCredito = tipoExtratoUpper === 'CREDITO'
            || (tipoExtratoUpper !== 'DEBITO' && parseFloat(transacao.valor) > 0);
        const tipo = isCredito ? 'RECEITA' : 'DESPESA';
        
        console.log('💰 Tipo detectado:', tipo, '| tipo_extrato:', transacao.tipo, '| valor:', transacao.valor, '| isCredito:', isCredito);
        
        // Preparar dados do lançamento
        const lancamentoData = {
            tipo: tipo,
            descricao: descricaoCustom || transacao.descricao,
            valor: Math.abs(parseFloat(transacao.valor)),
            data_vencimento: transacao.data,
            data_pagamento: transacao.data, // Já foi pago (consta no extrato)
            status: 'pago',
            categoria: categoria,
            subcategoria: subcategoria,
            pessoa: razaoSocial,  // Campo correto: pessoa (exibido como "Razão Social" na interface)
            associacao: transacao.fitid || `EXT-${transacao.id}`,  // Campo correto: associacao (exibido como "Nº Documento")
            conta_bancaria: transacao.conta_bancaria,
            observacoes: `Importado do extrato bancário (${transacao.fitid || transacao.id})`
        };
        
        console.log('📦 Dados do lançamento a criar:', lancamentoData);
        
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        
        // 1️⃣ CRIAR O LANÇAMENTO
        console.log('1️⃣ Criando lançamento...');
        const responseLancamento = await fetch(`${API_URL}/lancamentos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(lancamentoData)
        });
        
        if (!responseLancamento.ok) {
            const error = await responseLancamento.json();
            throw new Error(error.error || 'Erro ao criar lançamento');
        }
        
        const resultLancamento = await responseLancamento.json();
        const lancamentoId = resultLancamento.id || resultLancamento.data?.id;
        
        if (!lancamentoId) {
            throw new Error('ID do lançamento não retornado pelo servidor');
        }
        
        console.log('✅ Lançamento criado com ID:', lancamentoId);
        
        // 2️⃣ CONCILIAR A TRANSAÇÃO COM O LANÇAMENTO
        console.log('2️⃣ Conciliando transação', transacao.id, 'com lançamento', lancamentoId);
        const responseConciliacao = await fetch(`${API_URL}/extratos/${transacao.id}/conciliar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ lancamento_id: lancamentoId })
        });
        
        if (!responseConciliacao.ok) {
            const error = await responseConciliacao.json();
            throw new Error(error.error || 'Erro ao conciliar');
        }
        
        console.log('✅ Conciliação realizada com sucesso!');
        
        // 3️⃣ SUCESSO!
        showToast('✅ Lançamento criado e conciliado com sucesso!', 'success');
        
        // Fechar modal
        closeModal('modal-conciliacao');
        
        // Sempre recarregar extratos (independentemente da seção ativa)
        if (typeof loadExtratos === 'function') {
            await loadExtratos();
            console.log('✅ Extrato atualizado após conciliação');
        }
        
    } catch (error) {
        console.error('❌ Erro ao conciliar transação individual:', error);
        showToast(`❌ Erro: ${error.message}`, 'error');
    }
};

// Aplicar filtros do extrato
function aplicarFiltrosExtrato() {
    loadExtratos();
}

// Limpar filtros do extrato
function limparFiltrosExtrato() {
    // Tentar ambos os IDs por compatibilidade
    const contaEl = document.getElementById('filtro-conta-extrato') || document.getElementById('extrato-filter-conta');
    const dataInicioEl = document.getElementById('filtro-data-inicio-extrato') || document.getElementById('extrato-filter-data-inicio');
    const dataFimEl = document.getElementById('filtro-data-fim-extrato') || document.getElementById('extrato-filter-data-fim');
    const conciliadoEl = document.getElementById('filtro-conciliado-extrato') || document.getElementById('extrato-filter-conciliado');
    
    if (contaEl) contaEl.value = '';
    if (dataInicioEl) dataInicioEl.value = '';
    if (dataFimEl) dataFimEl.value = '';
    if (conciliadoEl) conciliadoEl.value = '';
    loadExtratos();
}

// Alias para compatibilidade com HTML (botão limpar chama limparFiltrosExtratoOFX)
window.limparFiltrosExtratoOFX = limparFiltrosExtrato;

// ============================================================================
// RECURSOS HUMANOS - FUNCIONÁRIOS
// ============================================================================

/**
 * Carrega lista de funcionários (RH)
 */
async function carregarFuncionariosRH() {
    try {
        console.log('👥 Carregando funcionários RH...');
        
        const response = await fetch('/api/funcionarios', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao buscar funcionários');
        }
        
        const result = await response.json();
        
        // Normalizar resposta (pode vir como array, {success, data} ou {funcionarios})
        let funcionarios = [];
        if (Array.isArray(result)) {
            funcionarios = result;
        } else if (result.success && result.data) {
            funcionarios = result.data;
        } else if (result.funcionarios) {
            funcionarios = result.funcionarios;
        }
        
        window.funcionarios = funcionarios;
        console.log('✅ Funcionários carregados:', funcionarios.length);
        
        // Renderizar na tabela
        const tbody = document.getElementById('tbody-funcionarios');
        if (!tbody) {
            console.warn('⚠️ Elemento tbody-funcionarios não encontrado');
            return;
        }
        
        if (funcionarios.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px;">Nenhum funcionário cadastrado</td></tr>';
            return;
        }
        
        tbody.innerHTML = funcionarios.map(func => `
            <tr>
                <td style="padding: 12px 15px;">${func.nome || ''}</td>
                <td style="padding: 12px 15px;">${func.cpf || ''}</td>
                <td style="padding: 12px 15px;">${func.endereco || ''}</td>
                <td style="padding: 12px 15px;">${func.email || ''}</td>
                <td style="padding: 12px 15px;">${func.tipo_chave_pix || ''}</td>
                <td style="padding: 12px 15px;">${func.chave_pix || ''}</td>
                <td style="padding: 12px 15px;">
                    <span class="badge ${func.ativo ? 'badge-success' : 'badge-danger'}">
                        ${func.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                </td>
                <td style="padding: 12px 15px; text-align: center;">
                    <button onclick="editarFuncionario(${func.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar">✏️</button>
                    <button onclick="toggleAtivoFuncionario(${func.id}, ${func.ativo})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="${func.ativo ? 'Inativar' : 'Ativar'}">
                        ${func.ativo ? '🔴' : '🟢'}
                    </button>
                    <button onclick="deletarFuncionario(${func.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
                </td>
            </tr>
        `).join('');
        
        console.log('✅ Tabela de funcionários renderizada');
        
    } catch (error) {
        console.error('❌ Erro ao carregar funcionários RH:', error);
        const tbody = document.getElementById('tbody-funcionarios');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: red;">Erro ao carregar funcionários</td></tr>';
        }
    }
}

/**
 * Edita um funcionário existente
 */
async function editarFuncionario(id) {
    try {
        console.log('✏️ Editando funcionário ID:', id);
        
        if (!id) {
            showToast('Erro: ID do funcionário não informado', 'error');
            return;
        }
        
        // Buscar dados do funcionário
        const response = await fetch(`${API_URL}/funcionarios/${id}`);
        
        if (!response.ok) {
            throw new Error('Funcionário não encontrado');
        }
        
        const funcionario = await response.json();
        console.log('✅ Funcionário encontrado:', funcionario);
        
        // Chamar função do interface_nova.html para abrir modal de edição
        if (typeof abrirModalFuncionario === 'function') {
            abrirModalFuncionario(funcionario);
            console.log('✅ Modal de edição aberto');
        } else {
            showToast('Erro: Função de edição não disponível', 'error');
            console.error('❌ Função abrirModalFuncionario não encontrada!');
        }
        
    } catch (error) {
        console.error('❌ Erro ao editar funcionário:', error);
        showToast('Erro ao abrir edição: ' + error.message, 'error');
    }
}

/**
 * Deleta um funcionário
 */
async function deletarFuncionario(id) {
    try {
        console.log('🗑️ Deletando funcionário ID:', id);
        
        if (!id) {
            showToast('Erro: ID do funcionário não informado', 'error');
            return;
        }
        
        if (!confirm('Deseja realmente excluir este funcionário?')) {
            console.log('❌ Exclusão cancelada pelo usuário');
            return;
        }
        
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        
        const response = await fetch(`${API_URL}/funcionarios/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao excluir funcionário');
        }
        
        const result = await response.json();
        console.log('✅ Funcionário excluído:', result);
        
        showToast('Funcionário excluído com sucesso!', 'success');
        
        // Recarregar lista
        await loadFuncionarios();
        
    } catch (error) {
        console.error('❌ Erro ao deletar funcionário:', error);
        showToast('Erro ao excluir: ' + error.message, 'error');
    }
}

/**
 * Ativa ou inativa um funcionário
 */
async function toggleAtivoFuncionario(id, ativoAtual) {
    try {
        console.log('🔄 Alterando status do funcionário ID:', id, 'Ativo atual:', ativoAtual);
        
        if (!id) {
            showToast('Erro: ID do funcionário não informado', 'error');
            return;
        }
        
        const acao = ativoAtual ? 'inativar' : 'ativar';
        const mensagem = ativoAtual 
            ? 'Ao inativar, este funcionário não poderá ser usado em novos cadastros. Deseja continuar?' 
            : 'Deseja realmente ativar este funcionário?';
        
        if (!confirm(mensagem)) {
            console.log('❌ Ação cancelada pelo usuário');
            return;
        }
        
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        
        const response = await fetch(`${API_URL}/funcionarios/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ ativo: !ativoAtual })
        });
        
        if (!response.ok) {
            throw new Error('Erro ao alterar status do funcionário');
        }
        
        const result = await response.json();
        console.log(`✅ Funcionário ${acao}do:`, result);
        
        showToast(`Funcionário ${acao}do com sucesso!`, 'success');
        
        // Recarregar lista
        await loadFuncionarios();
        
    } catch (error) {
        console.error('❌ Erro ao alterar status do funcionário:', error);
        showToast('Erro ao alterar status: ' + error.message, 'error');
    }
}

// Expor funções globalmente
window.editarFuncionario = editarFuncionario;
window.deletarFuncionario = deletarFuncionario;
window.toggleAtivoFuncionario = toggleAtivoFuncionario;
// loadFuncionariosRH é um alias para loadFuncionarios (usada em modals.js)
window.loadFuncionariosRH = async function() { return loadFuncionarios(); };

/**
 * Carrega lista de funcionários para uso em modais (endpoint simplificado)
 */
async function loadFuncionarios() {
    try {
        console.log('👥 Carregando funcionários...');
        
        const response = await fetch(`${API_URL}/funcionarios`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao buscar funcionários');
        }
        
        const data = await response.json();
        console.log('📦 Resposta /api/funcionarios:', data);
        
        // API pode retornar { success: true, data: [...] } ou array direto
        let todosFuncionarios = [];
        if (Array.isArray(data)) {
            todosFuncionarios = data;
        } else if (data.success && Array.isArray(data.data)) {
            todosFuncionarios = data.data;
        } else if (data.funcionarios && Array.isArray(data.funcionarios)) {
            todosFuncionarios = data.funcionarios;
        }
        
        // Armazenar TODOS os funcionários (sem filtrar por ativo)
        window.funcionarios = todosFuncionarios;
        
        console.log('✅ Funcionários carregados:', window.funcionarios.length, '(todos)');
        if (window.funcionarios.length > 0) {
            console.log('   📋 Primeiro funcionário:', window.funcionarios[0]);
        }
        
        return window.funcionarios;
    } catch (error) {
        console.error('❌ Erro ao carregar funcionários:', error);
        window.funcionarios = [];
        return [];
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
                    <td style="text-align: center;">
                        <button onclick='editarKit(${JSON.stringify(kit).replace(/'/g, "\\'")})' style="background: none; border: none; cursor: pointer; font-size: 16px;"
                            title="Editar">✏️</button>
                        <button onclick="excluirKit(${kit.id})"
                            style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
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
            
            // FORÇAR conversão para número antes de formatar
            // valor vem como string "21000.00" do banco, precisa converter primeiro
            const valorTotal = parseFloat(contrato.valor_total || contrato.valor || 0);
            const valorMensal = parseFloat(contrato.valor_mensal || 0);
            
            console.log(`📊 Contrato ${contrato.numero}:`, {
                valor_total_raw: contrato.valor_total,
                valor_raw: contrato.valor,
                valor_mensal_raw: contrato.valor_mensal,
                valorTotal_parsed: valorTotal,
                valorMensal_parsed: valorMensal,
                tipo_valorTotal: typeof valorTotal,
                tipo_valor: typeof contrato.valor
            });
            
            tr.innerHTML = `
                <td>${escapeHtml(contrato.numero || '-')}</td>
                <td>${escapeHtml(contrato.cliente_nome || '-')}</td>
                <td><span class="badge" style="background: #3498db; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px;">${escapeHtml(contrato.tipo || '-')}</span></td>
                <td>${escapeHtml(contrato.nome || contrato.descricao || '-')}</td>
                <td>${formatarMoeda(valorMensal)}</td>
                <td style="text-align: center;">${contrato.quantidade_meses || '-'}</td>
                <td style="font-weight: bold; color: #27ae60;">${formatarMoeda(valorTotal)}</td>
                <td>${dataFormatada}</td>
                <td><span style="font-size: 11px;">${escapeHtml(contrato.forma_pagamento || '-')}</span></td>
                <td><span class="status-badge status-${contrato.status || 'ativo'}">${contrato.status || 'Ativo'}</span></td>
                <td style="white-space: nowrap; text-align: center;">
                    <button onclick="editarContrato(${contrato.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar">✏️</button>
                    <button onclick="excluirContrato(${contrato.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
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
        console.log('🔍 [DEBUG] Iniciando apiGet para /sessoes');
        
        const sessoes = await apiGet('/sessoes');
        console.log('🔍 [DEBUG] apiGet retornou:', sessoes);
        console.log('🔍 [DEBUG] Tipo:', typeof sessoes, 'É array?', Array.isArray(sessoes));
        console.log('🔍 [DEBUG] Sessões length:', sessoes?.length);
        
        const tbody = document.getElementById('tbody-sessoes');
        console.log('🔍 [DEBUG] tbody encontrado?', !!tbody);
        
        if (!tbody) {
            console.error('❌ tbody-sessoes não encontrado');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (!sessoes || sessoes.length === 0) {
            console.log('📋 [DEBUG] Nenhuma sessão encontrada, mostrando mensagem');
            const mensagem = '<tr><td colspan="9" style="text-align: center; padding: 20px; color: #666;">Nenhuma sessão cadastrada</td></tr>';
            tbody.innerHTML = mensagem;
            console.log('📋 [DEBUG] tbody.innerHTML atualizado:', tbody.innerHTML);
            console.log('📋 [DEBUG] tbody visível?', tbody.offsetParent !== null);
            console.log('📋 [DEBUG] Tabela visível?', document.getElementById('table-sessoes')?.style.display);
            return;
        }
        
        console.log('📋 [DEBUG] Renderizando', sessoes.length, 'sessões');
        
        sessoes.forEach(sessao => {
            // Tipos de captação
            const tipos = [];
            if (sessao.tipo_foto) tipos.push('Foto');
            if (sessao.tipo_video) tipos.push('Vídeo');
            if (sessao.tipo_mobile) tipos.push('Mobile');
            const tiposCaptacao = tipos.join(', ') || '-';
            
            // Badge de Status da Sessão
            const statusSessao = sessao.status || 'rascunho';
            const badgesStatus = {
                'rascunho': { cor: '#94a3b8', label: '📝 Rascunho' },
                'agendada': { cor: '#3b82f6', label: '📅 Agendada' },
                'em_andamento': { cor: '#f59e0b', label: '⏳ Em Andamento' },
                'finalizada': { cor: '#10b981', label: '✅ Finalizada' },
                'concluida': { cor: '#059669', label: '🏁 Concluída' },
                'cancelada': { cor: '#ef4444', label: '❌ Cancelada' },
                'reaberta': { cor: '#8b5cf6', label: '🔄 Reaberta' }
            };
            const badgeStatus = badgesStatus[statusSessao] || badgesStatus['rascunho'];
            
            // Status baseado no prazo
            let statusPrazoClass = 'badge-success';
            let statusPrazoText = 'No Prazo';
            const hoje = new Date();
            const prazo = sessao.prazo_entrega ? new Date(sessao.prazo_entrega) : null;
            
            if (prazo) {
                const diffDias = Math.ceil((prazo - hoje) / (1000 * 60 * 60 * 24));
                if (diffDias < 0) {
                    statusPrazoClass = 'badge-danger';
                    statusPrazoText = 'Atrasado';
                } else if (diffDias <= 3) {
                    statusPrazoClass = 'badge-warning';
                    statusPrazoText = 'Urgente';
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
                <td>
                    <span style="display: inline-block; background: ${badgeStatus.cor}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-bottom: 4px;">
                        ${badgeStatus.label}
                    </span>
                    <br>
                    <span class="badge ${statusPrazoClass}">${statusPrazoText}</span>
                </td>
                <td style="text-align: center;">
                    <button onclick="editarSessao(${sessao.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar">✏️</button>
                    <button onclick="excluirSessao(${sessao.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
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
                <td style="text-align: center;">
                    <button onclick="editarComissao(${comissao.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar">✏️</button>
                    <button onclick="excluirComissao(${comissao.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
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
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ Erro do servidor:', response.status, errorText);
            showToast(`❌ Erro ao carregar sessão (${response.status})`, 'error');
            return;
        }
        
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
    const contents = ['resumo', 'contratos', 'sessoes', 'controle-horas', 'comissoes', 'equipe'];
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
        case 'resumo':
            loadResumoContratos();
            break;
        case 'contratos':
            loadContratos();
            break;
        case 'sessoes':
            loadSessoes();
            break;
        case 'controle-horas':
            loadControleHoras();
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
// RESUMO E ANÁLISE DE CONTRATOS
// ============================================================================

let chartContratosLucro = null; // Armazena instância do gráfico

async function loadResumoContratos() {
    try {
        console.log('='.repeat(80));
        console.log('📊 INICIANDO loadResumoContratos()');
        console.log('='.repeat(80));
        
        console.log('🔍 API_URL:', API_URL);
        console.log('🔍 Empresa atual:', window.currentEmpresaId);
        
        // Carregar contratos e sessões
        console.log('📡 Fazendo requisições para contratos e sessões...');
        const [contratosRes, sessoesRes] = await Promise.all([
            fetch(`${API_URL}/contratos`),
            fetch(`${API_URL}/sessoes`)
        ]);
        
        console.log('📦 Response Contratos:', contratosRes.status, contratosRes.statusText);
        console.log('📦 Response Sessões:', sessoesRes.status, sessoesRes.statusText);
        
        if (!contratosRes.ok) {
            throw new Error(`Erro ao carregar contratos: ${contratosRes.status}`);
        }
        
        if (!sessoesRes.ok) {
            throw new Error(`Erro ao carregar sessões: ${sessoesRes.status}`);
        }
        
        const contratos = await contratosRes.json();
        const sessoes = await sessoesRes.json();
        
        console.log('📦 Total de Contratos recebidos:', contratos.length);
        console.log('📦 Total de Sessões recebidas:', sessoes.length);
        
        if (contratos.length > 0) {
            console.log('📋 Primeiro contrato:', contratos[0]);
            console.log('📋 ESTRUTURA COMPLETA DO CONTRATO:');
            console.log('   🔑 Campos disponíveis:', Object.keys(contratos[0]));
            console.log('   📝 Valores:', JSON.stringify(contratos[0], null, 2));
        }
        
        if (sessoes.length > 0) {
            console.log('📋 Primeira sessão:', sessoes[0]);
            console.log('📋 ESTRUTURA COMPLETA DA SESSÃO:');
            console.log('   🔑 Campos disponíveis:', Object.keys(sessoes[0]));
            console.log('   📝 Valores:', JSON.stringify(sessoes[0], null, 2));
        }
        
        // Calcular análise
        console.log('🧮 Calculando análise...');
        const analise = calcularAnaliseContratos(contratos, sessoes);
        
        console.log('📊 Análise calculada:');
        console.log('   - Contratos analisados:', analise.contratos.length);
        console.log('   - Receita Total:', analise.totais.receitaTotal);
        console.log('   - Custos Totais:', analise.totais.custosTotal);
        console.log('   - Lucro Líquido:', analise.totais.lucroLiquido);
        console.log('   - Margem:', analise.totais.margemLucro.toFixed(2) + '%');
        
        // Atualizar KPIs
        console.log('📈 Atualizando KPIs...');
        atualizarKPIs(analise);
        
        // Renderizar tabela
        console.log('📋 Renderizando tabela...');
        renderizarTabelaResumo(analise.contratos);
        
        // Renderizar gráfico
        console.log('📊 Renderizando gráfico...');
        renderizarGraficoLucro(analise.contratos);
        
        console.log('='.repeat(80));
        console.log('✅ Resumo carregado com sucesso!');
        console.log('='.repeat(80));
        
    } catch (error) {
        console.log('='.repeat(80));
        console.error('❌ ERRO ao carregar resumo:', error);
        console.error('Stack trace:', error.stack);
        console.log('='.repeat(80));
        showToast('Erro ao carregar análise de contratos: ' + error.message, 'error');
    }
}

function calcularAnaliseContratos(contratos, sessoes) {
    console.log('🧮 calcularAnaliseContratos - INÍCIO');
    console.log('   Contratos recebidos:', contratos.length);
    console.log('   Sessões recebidas:', sessoes.length);
    
    let receitaTotal = 0;
    let custosTotal = 0;
    let impostosTotal = 0;
    let comissoesTotal = 0;
    let custosSessoesTotal = 0;
    
    const contratosAnalise = contratos.map((contrato, index) => {
        console.log(`   📋 Analisando contrato ${index + 1}/${contratos.length}:`, contrato.numero || contrato.nome);
        
        // Receita bruta do contrato - USAR 'valor' em vez de 'valor_total'
        const receitaBruta = parseFloat(contrato.valor) || 0;
        console.log(`      💰 Receita Bruta: R$ ${receitaBruta}`);
        
        // Impostos
        const percentualImposto = parseFloat(contrato.imposto) || 0;
        const valorImpostos = receitaBruta * (percentualImposto / 100);
        console.log(`      📊 Imposto ${percentualImposto}%: R$ ${valorImpostos}`);
        
        // Comissões - pode ser array com percentual ou valor direto
        let valorComissoes = 0;
        if (Array.isArray(contrato.comissoes)) {
            valorComissoes = contrato.comissoes.reduce((sum, com) => {
                // Se tem percentual, calcular sobre receita bruta
                if (com.percentual) {
                    return sum + (receitaBruta * (parseFloat(com.percentual) || 0) / 100);
                }
                // Caso contrário, usar valor direto
                return sum + (parseFloat(com.valor) || 0);
            }, 0);
        } else {
            valorComissoes = parseFloat(contrato.comissoes) || 0;
        }
        console.log(`      💸 Comissões (${contrato.comissoes?.length || 0} item(s)): R$ ${valorComissoes}`);
        
        // Buscar sessões do contrato
        const sessoesContrato = sessoes.filter(s => 
            s.contrato_id === contrato.id || 
            s.contrato_numero === contrato.numero ||
            s.contrato_id === contrato.numero
        );
        console.log(`      📸 Sessões encontradas: ${sessoesContrato.length}`);
        
        // Calcular custos das sessões
        let custosSessoes = 0;
        sessoesContrato.forEach((sessao, idx) => {
            let custoEquipe = 0;
            let custoEquip = 0;
            let custoAd = 0;
            
            // Custo da equipe - VERIFICAR dados_json.equipe[].pagamento
            if (sessao.dados_json && sessao.dados_json.equipe) {
                custoEquipe = sessao.dados_json.equipe.reduce((sum, membro) => 
                    sum + (parseFloat(membro.pagamento) || 0), 0);
            } else if (sessao.equipe && Array.isArray(sessao.equipe)) {
                custoEquipe = sessao.equipe.reduce((sum, membro) => 
                    sum + (parseFloat(membro.pagamento) || 0), 0);
            }
            
            // Equipamentos alugados
            if (sessao.equipamentos_alugados && Array.isArray(sessao.equipamentos_alugados)) {
                custoEquip = sessao.equipamentos_alugados.reduce((sum, equip) => 
                    sum + (parseFloat(equip.valor) || 0), 0);
            }
            
            // Custos adicionais
            if (sessao.custos_adicionais && Array.isArray(sessao.custos_adicionais)) {
                custoAd = sessao.custos_adicionais.reduce((sum, custo) => 
                    sum + (parseFloat(custo.valor) || 0), 0);
            }
            
            const totalSessao = custoEquipe + custoEquip + custoAd;
            
            console.log(`         Sessão ${idx + 1}: Equipe=${custoEquipe}, Equipamentos=${custoEquip}, Adicionais=${custoAd}, Total=${totalSessao}`);
            
            custosSessoes += totalSessao;
        });
        console.log(`      🎬 Total custos sessões: R$ ${custosSessoes}`);
        
        // Receita líquida
        const receitaLiquida = receitaBruta - valorImpostos - valorComissoes;
        console.log(`      💵 Receita Líquida: R$ ${receitaLiquida}`);
        
        // Resultado (lucro ou prejuízo)
        const resultado = receitaLiquida - custosSessoes;
        const statusEmoji = resultado >= 0 ? '✅' : '❌';
        console.log(`      ${statusEmoji} RESULTADO: R$ ${resultado}`);
        
        // Margem
        const margem = receitaBruta > 0 ? (resultado / receitaBruta) * 100 : 0;
        console.log(`      📊 Margem: ${margem.toFixed(2)}%`);
        
        // Acumular totais
        receitaTotal += receitaBruta;
        impostosTotal += valorImpostos;
        comissoesTotal += valorComissoes;
        custosSessoesTotal += custosSessoes;
        custosTotal += (valorImpostos + valorComissoes + custosSessoes);
        
        return {
            ...contrato,
            receitaBruta,
            valorImpostos,
            valorComissoes,
            custosSessoes,
            receitaLiquida,
            resultado,
            margem,
            numSessoes: sessoesContrato.length
        };
    });
    
    const lucroLiquido = receitaTotal - custosTotal;
    const margemLucro = receitaTotal > 0 ? (lucroLiquido / receitaTotal) * 100 : 0;
    
    console.log('🧮 calcularAnaliseContratos - TOTAIS:');
    console.log('   💰 Receita Total: R$', receitaTotal);
    console.log('   💸 Custos Total: R$', custosTotal);
    console.log('   📈 Lucro Líquido: R$', lucroLiquido);
    console.log('   📊 Margem: ', margemLucro.toFixed(2) + '%');
    
    return {
        contratos: contratosAnalise,
        totais: {
            receitaTotal,
            custosTotal,
            impostosTotal,
            comissoesTotal,
            custosSessoesTotal,
            receitaLiquidaTotal: receitaTotal - impostosTotal - comissoesTotal,
            lucroLiquido,
            margemLucro
        }
    };
}

function atualizarKPIs(analise) {
    const { totais } = analise;
    
    document.getElementById('kpi-receita-total').textContent = 
        `R$ ${totais.receitaTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    
    document.getElementById('kpi-custos-totais').textContent = 
        `R$ ${totais.custosTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    
    const lucroElement = document.getElementById('kpi-lucro-liquido');
    lucroElement.textContent = 
        `R$ ${totais.lucroLiquido.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    lucroElement.parentElement.style.background = totais.lucroLiquido >= 0 
        ? 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
        : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
    
    const margemElement = document.getElementById('kpi-margem-lucro');
    margemElement.textContent = `${totais.margemLucro.toFixed(1)}%`;
    margemElement.parentElement.style.background = totais.margemLucro >= 20 
        ? 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
        : totais.margemLucro >= 0
        ? 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
        : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
}

function renderizarTabelaResumo(contratos) {
    const tbody = document.getElementById('tbody-resumo-contratos');
    tbody.innerHTML = '';
    
    let totais = {
        receitaBruta: 0,
        impostos: 0,
        comissoes: 0,
        custosSessoes: 0,
        receitaLiquida: 0,
        resultado: 0
    };
    
    contratos.forEach(contrato => {
        const tr = document.createElement('tr');
        
        const statusClass = contrato.resultado >= 0 ? 'success' : 'danger';
        const statusIcon = contrato.resultado >= 0 ? '📈' : '📉';
        const statusText = contrato.resultado >= 0 ? 'LUCRO' : 'PREJUÍZO';
        const statusColor = contrato.resultado >= 0 ? '#27ae60' : '#e74c3c';
        
        tr.innerHTML = `
            <td style="padding: 12px 15px;">${contrato.numero || '-'}</td>
            <td style="padding: 12px 15px;">${contrato.cliente_nome || '-'}</td>
            <td style="padding: 12px 15px; text-align: right; font-weight: 600;">
                R$ ${contrato.receitaBruta.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </td>
            <td style="padding: 12px 15px; text-align: right; color: #e74c3c;">
                R$ ${contrato.valorImpostos.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </td>
            <td style="padding: 12px 15px; text-align: right; color: #e74c3c;">
                R$ ${contrato.valorComissoes.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </td>
            <td style="padding: 12px 15px; text-align: right; color: #e74c3c;">
                R$ ${contrato.custosSessoes.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </td>
            <td style="padding: 12px 15px; text-align: right; font-weight: 600; color: #3498db;">
                R$ ${contrato.receitaLiquida.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </td>
            <td style="padding: 12px 15px; text-align: right; font-weight: 700; font-size: 15px; color: ${statusColor};">
                R$ ${contrato.resultado.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </td>
            <td style="padding: 12px 15px; text-align: center;">
                <span style="background: ${statusColor}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 700; white-space: nowrap; display: inline-block;">
                    ${statusIcon} ${statusText}
                </span>
            </td>
        `;
        
        tbody.appendChild(tr);
        
        // Acumular totais
        totais.receitaBruta += contrato.receitaBruta;
        totais.impostos += contrato.valorImpostos;
        totais.comissoes += contrato.valorComissoes;
        totais.custosSessoes += contrato.custosSessoes;
        totais.receitaLiquida += contrato.receitaLiquida;
        totais.resultado += contrato.resultado;
    });
    
    // Atualizar rodapé com totais
    document.getElementById('total-receita-bruta').textContent = 
        `R$ ${totais.receitaBruta.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    document.getElementById('total-impostos').textContent = 
        `R$ ${totais.impostos.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    document.getElementById('total-comissoes').textContent = 
        `R$ ${totais.comissoes.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    document.getElementById('total-custos-sessoes').textContent = 
        `R$ ${totais.custosSessoes.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    document.getElementById('total-receita-liquida').textContent = 
        `R$ ${totais.receitaLiquida.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    
    const totalResultadoEl = document.getElementById('total-resultado');
    totalResultadoEl.textContent = 
        `R$ ${totais.resultado.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    totalResultadoEl.style.color = totais.resultado >= 0 ? '#27ae60' : '#e74c3c';
}

function renderizarGraficoLucro(contratos) {
    const ctx = document.getElementById('chart-contratos-lucro');
    if (!ctx) return;
    
    // Destruir gráfico anterior se existir
    if (chartContratosLucro) {
        chartContratosLucro.destroy();
    }
    
    // Preparar dados
    const labels = contratos.map(c => c.numero || c.nome || 'Sem nome');
    const receitas = contratos.map(c => c.receitaBruta);
    const custos = contratos.map(c => c.valorImpostos + c.valorComissoes + c.custosSessoes);
    const lucros = contratos.map(c => c.resultado);
    
    // Criar gráfico
    chartContratosLucro = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Receita Bruta',
                    data: receitas,
                    backgroundColor: 'rgba(52, 152, 219, 0.8)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 2
                },
                {
                    label: 'Custos Totais',
                    data: custos,
                    backgroundColor: 'rgba(231, 76, 60, 0.8)',
                    borderColor: 'rgba(231, 76, 60, 1)',
                    borderWidth: 2
                },
                {
                    label: 'Resultado',
                    data: lucros,
                    backgroundColor: lucros.map(v => v >= 0 ? 'rgba(39, 174, 96, 0.8)' : 'rgba(231, 76, 60, 0.8)'),
                    borderColor: lucros.map(v => v >= 0 ? 'rgba(39, 174, 96, 1)' : 'rgba(231, 76, 60, 1)'),
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        font: {
                            size: 12,
                            weight: 'bold'
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += 'R$ ' + context.parsed.y.toLocaleString('pt-BR', {minimumFractionDigits: 2});
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toLocaleString('pt-BR', {minimumFractionDigits: 0});
                        }
                    }
                }
            }
        }
    });
}

// Expor função globalmente
window.loadResumoContratos = loadResumoContratos;

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

// Função de carregamento do Fluxo de Caixa
async function loadFluxoCaixa() {
    console.log('📈 Inicializando seção Fluxo de Caixa...');
    await carregarBancosFluxo();
    // Definir mês atual nos filtros
    const hoje = new Date();
    const anoAtual = hoje.getFullYear();
    const mesAtual = String(hoje.getMonth() + 1).padStart(2, '0');
    document.getElementById('filter-ano-fluxo').value = anoAtual;
    document.getElementById('filter-mes-fluxo').value = mesAtual;
    await carregarFluxoCaixa();
}

// Funções de Carregamento
window.loadDashboard = loadDashboard;
window.loadContas = loadContas;
window.loadLancamentos = loadLancamentos;
window.loadContasReceber = loadContasReceber;
window.loadContasPagar = loadContasPagar;
window.loadFluxoCaixa = loadFluxoCaixa;
window.loadAnaliseCategorias = loadAnaliseCategorias;
window.loadInadimplencia = loadInadimplencia;
window.loadControleHoras = loadControleHoras;
window.loadFluxoProjetado = loadFluxoProjetado;
window.loadAnaliseContas = loadAnaliseContas;
window.loadFornecedores = loadFornecedores;
window.loadExtratos = loadExtratos;
// loadFuncionariosRH já exposto acima como alias de loadFuncionarios
window.loadKits = loadKits;
window.loadSessoes = loadSessoes;
window.loadComissoes = loadComissoes;

// Funções de Exportação
window.exportarFluxoExcel = exportarFluxoExcel;
window.exportarContratosPDF = exportarContratosPDF;
window.exportarControleHorasPDF = exportarControleHorasPDF;
window.exportarControleHorasExcel = exportarControleHorasExcel;
window.exportarInadimplenciaPDF = exportarInadimplenciaPDF;
window.exportarInadimplenciaExcel = exportarInadimplenciaExcel;

// Funções de Compensação de Horas
window.abrirCompensacaoHoras = abrirCompensacaoHoras;
window.executarCompensacaoHoras = executarCompensacaoHoras;
window.fecharCompensacaoHoras = fecharCompensacaoHoras;
window.atualizarOpcoesCompensacao = atualizarOpcoesCompensacao;

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

// === FORNECEDORES ===
async function loadFornecedores(ativos = true) {
    try {
        console.log('🏭 Carregando fornecedores... (Ativos:', ativos, ')');
        
        const response = await fetch(`${API_URL}/fornecedores?ativos=${ativos}`);
        if (!response.ok) throw new Error('Erro ao carregar fornecedores');
        
        let fornecedores = await response.json();
        
        // Suporte ao novo formato de resposta { success, data, total, message }
        if (fornecedores && typeof fornecedores === 'object' && 'success' in fornecedores && 'data' in fornecedores) {
            if (fornecedores.data.length === 0 && fornecedores.message) {
                console.info(`ℹ️ ${fornecedores.message}`);
            }
            fornecedores = fornecedores.data;
        }
        
        console.log(`📦 ${fornecedores.length} fornecedores recebidos`);
        
        // Armazenar em window.fornecedores para uso nos modais de despesa
        window.fornecedores = fornecedores;
        console.log('✅ window.fornecedores definido:', window.fornecedores.length, 'fornecedores');
        
        const tbody = document.getElementById('tbody-fornecedores');
        if (!tbody) {
            console.error('❌ tbody-fornecedores não encontrado!');
            return;
        }
        
        tbody.innerHTML = '';
        
        // Mostrar/ocultar coluna de data de inativação
        const thDataInativacao = document.getElementById('th-data-inativacao-fornecedor');
        if (thDataInativacao) {
            thDataInativacao.style.display = ativos ? 'none' : 'table-cell';
        }
        
        if (fornecedores.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: #999;">Nenhum fornecedor encontrado</td></tr>';
            return;
        }
        
        fornecedores.forEach(forn => {
            const tr = document.createElement('tr');
            
            const dataInativacaoCell = ativos ? '' : `<td>${forn.data_inativacao || '-'}</td>`;
            
            const botoesAcao = ativos ? `
                <button onclick="editarFornecedor('${forn.nome.replace(/'/g, "\\'")}')"
                    style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar">✏️</button>
                <button onclick="inativarFornecedor('${forn.nome.replace(/'/g, "\\'")}')"
                    style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Inativar">⏸️</button>
            ` : `
                <button onclick="editarFornecedor('${forn.nome.replace(/'/g, "\\'")}')"
                    style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar">✏️</button>
                <button onclick="reativarFornecedor('${forn.nome.replace(/'/g, "\\'")}')"
                    style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Reativar">▶️</button>
                <button onclick="excluirFornecedor('${forn.nome.replace(/'/g, "\\'")}')"
                    style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
            `;
            
            tr.innerHTML = `
                <td>${forn.nome || '-'}</td>
                <td>${forn.nome_fantasia || '-'}</td>
                <td>${forn.cnpj || '-'}</td>
                <td>${forn.cidade || '-'}</td>
                <td>${forn.telefone || '-'}</td>
                ${dataInativacaoCell}
                <td>${botoesAcao}</td>
            `;
            tbody.appendChild(tr);
        });
        
        console.log('✅ Tabela de fornecedores atualizada');
    } catch (error) {
        console.error('❌ Erro ao carregar fornecedores:', error);
        showToast('Erro ao carregar fornecedores', 'error');
    }
}

async function editarFornecedor(nome) {
    try {
        console.log('✏️ Editando fornecedor:', nome);
        
        const response = await fetch(`${API_URL}/fornecedores/${encodeURIComponent(nome)}`);
        const fornecedor = await response.json();
        
        if (!fornecedor) {
            showToast('Erro: Fornecedor não encontrado', 'error');
            return;
        }
        
        if (typeof openModalFornecedor === 'function') {
            openModalFornecedor(fornecedor);
        } else {
            showToast('Erro: Função de edição não disponível', 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao editar fornecedor:', error);
        showToast('Erro ao abrir edição: ' + error.message, 'error');
    }
}

async function inativarFornecedor(nome) {
    console.log('⏸️ inativarFornecedor chamada com:', nome);
    
    if (!confirm(`Deseja realmente desativar o fornecedor "${nome}"?`)) {
        return;
    }
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        const url = `${API_URL}/fornecedores/${encodeURIComponent(nome)}/inativar`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({})
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast('✓ Fornecedor desativado com sucesso!', 'success');
            await loadFornecedores(true);
        } else {
            showToast('Erro ao desativar: ' + (result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('❌ Exception:', error);
        showToast('Erro ao desativar fornecedor', 'error');
    }
}

async function reativarFornecedor(nome) {
    console.log('▶️ reativarFornecedor chamada com:', nome);
    
    if (!confirm(`Deseja realmente reativar o fornecedor "${nome}"?`)) {
        return;
    }
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        const url = `${API_URL}/fornecedores/${encodeURIComponent(nome)}/reativar`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({})
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast('✓ Fornecedor reativado com sucesso!', 'success');
            await loadFornecedores(false);
        } else {
            showToast('Erro ao reativar: ' + (result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('❌ Exception:', error);
        showToast('Erro ao reativar fornecedor', 'error');
    }
}

async function excluirFornecedor(nome) {
    console.log('🗑️ excluirFornecedor chamada com:', nome);
    
    if (!confirm(`ATENÇÃO: Deseja realmente EXCLUIR permanentemente o fornecedor "${nome}"?\n\nEsta ação não pode ser desfeita!`)) {
        return;
    }
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        const url = `${API_URL}/fornecedores/${encodeURIComponent(nome)}`;
        
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast('✓ Fornecedor excluído permanentemente!', 'success');
            await loadFornecedores(false);
        } else {
            showToast('Erro ao excluir: ' + (result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('❌ Exception:', error);
        showToast('Erro ao excluir fornecedor', 'error');
    }
}

function showFornecedorTab(tab) {
    console.log('🔄 Alternando aba de fornecedores:', tab);
    
    // Atualizar botões das abas
    const abaAtivos = document.getElementById('tab-fornecedores-ativos');
    const abaInativos = document.getElementById('tab-fornecedores-inativos');
    
    if (tab === 'ativos') {
        abaAtivos?.classList.add('active');
        abaAtivos?.setAttribute('style', 'padding: 10px 20px; border: none; background: #9b59b6; color: white; cursor: pointer; border-radius: 5px 5px 0 0; font-weight: bold;');
        abaInativos?.classList.remove('active');
        abaInativos?.setAttribute('style', 'padding: 10px 20px; border: none; background: #bdc3c7; color: #555; cursor: pointer; border-radius: 5px 5px 0 0;');
        loadFornecedores(true);
    } else {
        abaInativos?.classList.add('active');
        abaInativos?.setAttribute('style', 'padding: 10px 20px; border: none; background: #9b59b6; color: white; cursor: pointer; border-radius: 5px 5px 0 0; font-weight: bold;');
        abaAtivos?.classList.remove('active');
        abaAtivos?.setAttribute('style', 'padding: 10px 20px; border: none; background: #bdc3c7; color: #555; cursor: pointer; border-radius: 5px 5px 0 0;');
        loadFornecedores(false);
    }
}

// Exportações PDF e Excel
async function exportarFornecedoresPDF() {
    try {
        const response = await fetch(`${API_URL}/fornecedores/exportar/pdf`);
        if (!response.ok) throw new Error('Erro ao gerar PDF');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `fornecedores_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        
        showToast('✓ PDF gerado com sucesso!', 'success');
    } catch (error) {
        console.error('❌ Erro ao exportar PDF:', error);
        showToast('Erro ao gerar PDF', 'error');
    }
}

async function exportarFornecedoresExcel() {
    try {
        const response = await fetch(`${API_URL}/fornecedores/exportar/excel`);
        if (!response.ok) throw new Error('Erro ao gerar Excel');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `fornecedores_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        
        showToast('✓ Excel gerado com sucesso!', 'success');
    } catch (error) {
        console.error('❌ Erro ao exportar Excel:', error);
        showToast('Erro ao gerar Excel', 'error');
    }
}

// Expor globalmente
window.loadFornecedores = loadFornecedores;
window.loadFornecedoresTable = loadFornecedores; // Alias para compatibilidade
window.editarFornecedor = editarFornecedor;
window.inativarFornecedor = inativarFornecedor;
window.reativarFornecedor = reativarFornecedor;
window.excluirFornecedor = excluirFornecedor;
window.showFornecedorTab = showFornecedorTab;
window.exportarFornecedoresPDF = exportarFornecedoresPDF;
window.exportarFornecedoresExcel = exportarFornecedoresExcel;

window.loadContasBancarias = async function() {
    try {
        // Verificar permissão antes de carregar
        const usuario = JSON.parse(sessionStorage.getItem('usuario') || '{}');
        const permissoes = usuario.permissoes || [];
        if (!permissoes.includes('contas_view') && !permissoes.includes('lancamentos_view')) {
            console.log('⏭️ Contas bancárias: Usuário sem permissão');
            return;
        }
        
        console.log('🏦 loadContasBancarias - Carregando contas bancárias...');
        
        const response = await fetch(`${API_URL}/contas`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        let contas = await response.json();
        
        // Suporte ao novo formato de resposta { success, data, total, message }
        if (contas && typeof contas === 'object' && 'success' in contas && 'data' in contas) {
            if (contas.data.length === 0 && contas.message) {
                console.info(`ℹ️ ${contas.message}`);
            }
            contas = contas.data;
        }
        
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
        tbody.innerHTML = contas.map(conta => {
            const statusBadge = conta.ativa !== false ? 
                '<span style="background: #27ae60; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">● ATIVA</span>' :
                '<span style="background: #95a5a6; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">● INATIVA</span>';
            
            const toggleButton = conta.ativa !== false ?
                `<button class="btn btn-sm" onclick="toggleAtivoConta('${conta.nome.replace(/'/g, "\\'")}')"
                        style="background: #f39c12; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; margin-right: 5px;">
                    🔒 Inativar
                </button>` :
                `<button class="btn btn-sm" onclick="toggleAtivoConta('${conta.nome.replace(/'/g, "\\'")}')"
                        style="background: #27ae60; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; margin-right: 5px;">
                    🔓 Reativar
                </button>`;
            
            return `
            <tr style="${conta.ativa === false ? 'opacity: 0.6; background: #f8f9fa;' : ''}">
                <td>${conta.banco || 'N/A'} ${statusBadge}</td>
                <td>${conta.agencia || 'N/A'}</td>
                <td>${conta.conta || 'N/A'}</td>
                <td>${(conta.saldo_inicial || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                <td style="font-weight: bold; color: ${(conta.saldo || 0) >= 0 ? '#27ae60' : '#e74c3c'};">
                    ${(conta.saldo || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                </td>
                <td style="text-align: center;">
                    <button onclick="editarConta('${conta.nome.replace(/'/g, "\\'")}')"
                            style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar conta">✏️</button>
                    ${toggleButton}
                    <button onclick="excluirConta('${conta.nome.replace(/'/g, "\\'")}')"
                            style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir conta">🗑️</button>
                </td>
            </tr>
        `;
        }).join('');
        
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
        
        // Carregar transações do período (fonte principal dos cards)
        await carregarTransacoesDetalhadas(dataInicio, dataFim, banco);
        
        // Calcular totais diretamente das transações carregadas
        const transacoes = window.fluxoCaixaTransacoes || [];
        const totalEntradas = transacoes
            .filter(t => (t.tipo || '').toLowerCase() === 'receita')
            .reduce((sum, t) => sum + parseFloat(t.valor || 0), 0);
        const totalSaidas = transacoes
            .filter(t => (t.tipo || '').toLowerCase() === 'despesa')
            .reduce((sum, t) => sum + parseFloat(t.valor || 0), 0);
        const saldoPeriodo = totalEntradas - totalSaidas;

        // Buscar dados auxiliares (dashboard + análise) — não bloqueiam os cards
        let url = `${API_URL}/relatorios/dashboard-completo?data_inicio=${dataInicio}&data_fim=${dataFim}`;
        if (banco) url += `&conta=${encodeURIComponent(banco)}`;
        Promise.all([
            fetch(url, { credentials: 'include', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.csrfToken || '' } }),
            fetch(`${API_URL}/relatorios/analise-contas`, { credentials: 'include', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.csrfToken || '' } })
        ]).catch(e => console.warn('Dados auxiliares indisponíveis:', e));
        
        // Atualizar valores dos cards
        const cardEntradas = document.getElementById('card-total-entradas');
        const cardSaidas = document.getElementById('card-total-saidas');
        const cardSaldo = document.getElementById('card-saldo-periodo');
        const cardSaldoAtual = document.getElementById('card-saldo-atual');
        const cardSaldoAtualLabel = document.getElementById('card-saldo-atual-label');
        
        if (cardEntradas) cardEntradas.textContent = formatarMoeda(totalEntradas);
        if (cardSaidas) cardSaidas.textContent = formatarMoeda(totalSaidas);
        if (cardSaldo) cardSaldo.textContent = formatarMoeda(saldoPeriodo);
        
        // Buscar saldo atual do banco
        try {
            const responseContas = await fetch('/api/contas', {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrfToken || ''
                }
            });
            
            if (responseContas.ok) {
                const resultContas = await responseContas.json();
                const contas = resultContas.data || resultContas;
                
                let saldoAtual = 0;
                let labelSaldo = 'Saldo em conta';
                
                if (banco && Array.isArray(contas)) {
                    // Filtro específico - mostrar saldo do banco selecionado
                    const contaFiltrada = contas.find(c => c.nome === banco);
                    if (contaFiltrada) {
                        saldoAtual = parseFloat(contaFiltrada.saldo || 0);
                        labelSaldo = `Saldo em ${banco}`;
                    }
                } else if (Array.isArray(contas)) {
                    // Todos os bancos - somar saldo total
                    saldoAtual = contas.reduce((sum, c) => sum + parseFloat(c.saldo || 0), 0);
                    labelSaldo = 'Saldo total em contas';
                }
                
                if (cardSaldoAtual) cardSaldoAtual.textContent = formatarMoeda(saldoAtual);
                if (cardSaldoAtualLabel) cardSaldoAtualLabel.textContent = labelSaldo;
            }
        } catch (error) {
            console.error('Erro ao buscar saldo atual:', error);
        }
        
        // Armazenar dados para exportação
        window.fluxoCaixaDados = {
            totalEntradas,
            totalSaidas,
            saldoPeriodo,
            dataInicio,
            dataFim,
            banco: banco || 'Todas as contas'
        };
        
        showToast('Fluxo de Caixa carregado com sucesso!', 'success');
        
    } catch (error) {
        console.error('❌ Erro ao carregar fluxo de caixa:', error);
        const tbody = document.getElementById('tbody-transacoes-fluxo');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #e74c3c;">❌ Erro ao carregar dados do fluxo de caixa</td></tr>';
        }
        showToast('Erro ao carregar fluxo de caixa', 'error');
    }
};

// Função removida - abas Realizado e Projetado foram excluídas

// Função para carregar transações detalhadas
async function carregarTransacoesDetalhadas(dataInicio, dataFim, banco) {
    try {
        let url = `${API_URL}/relatorios/fluxo-caixa?data_inicio=${dataInicio}&data_fim=${dataFim}`;
        if (banco) {
            // Filtrar por banco no frontend já que o backend não suporta esse filtro ainda
        }
        
        const response = await fetch(url, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken || ''
            }
        });
        
        if (!response.ok) throw new Error('Erro ao carregar transações');
        
        let transacoes = await response.json();
        
        // Filtrar por banco se especificado
        if (banco) {
            transacoes = transacoes.filter(t => t.conta_bancaria === banco);
        }
        
        // Armazenar para exportação
        window.fluxoCaixaTransacoes = transacoes;
        
        const tbody = document.getElementById('tbody-transacoes-fluxo');
        
        if (!tbody) {
            console.error('Elemento tbody-transacoes-fluxo não encontrado!');
            return;
        }
        
        if (transacoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #999;">Nenhuma transação paga encontrada no período</td></tr>';
            return;
        }
        
        tbody.innerHTML = '';
        
        transacoes.forEach((transacao, index) => {
            const entrada = transacao.tipo === 'receita' ? formatarMoeda(transacao.valor) : '-';
            const saida = transacao.tipo === 'despesa' ? formatarMoeda(transacao.valor) : '-';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${formatarData(transacao.data_pagamento)}</td>
                <td>${transacao.descricao || '-'}</td>
                <td>${transacao.categoria || '-'}</td>
                <td>${transacao.subcategoria || '-'}</td>
                <td style="text-align: right; color: #27ae60; font-weight: bold;">${entrada}</td>
                <td style="text-align: right; color: #e74c3c; font-weight: bold;">${saida}</td>
                <td>${transacao.conta_bancaria || '-'}</td>
                <td>
                    <input 
                        type="text" 
                        class="input-associacao-fluxo" 
                        value="${transacao.associacao || ''}" 
                        placeholder="Digite aqui..." 
                        data-lancamento-id="${transacao.id}"
                        data-index="${index}"
                        style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px;"
                        onblur="salvarAssociacaoFluxo(this)"
                        title="Digite e o sistema salvará automaticamente ao sair do campo"
                    />
                </td>
            `;
            tbody.appendChild(tr);
        });
        
    } catch (error) {
        console.error('Erro ao carregar transações detalhadas:', error);
        const tbody = document.getElementById('tbody-transacoes-fluxo');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #e74c3c;">❌ Erro ao carregar transações</td></tr>';
        }
    }
}

// Função para salvar associação automaticamente
window.salvarAssociacaoFluxo = async function(input) {
    const lancamentoId = input.dataset.lancamentoId;
    const novaAssociacao = input.value.trim();
    const index = input.dataset.index;
    
    // Se não tem ID (transferências duplicadas na exibição), não salvar
    if (!lancamentoId || lancamentoId === 'null' || lancamentoId === 'undefined') {
        console.log('⚠️ Transação sem ID (provavelmente transferência duplicada na visualização), não será salva');
        return;
    }
    
    try {
        // Indicador visual de salvamento
        const originalBorder = input.style.border;
        input.style.border = '2px solid #3498db';
        input.disabled = true;
        
        const response = await fetch(`${API_URL}/lancamentos/${lancamentoId}/associacao`, {
            method: 'PATCH',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken || ''
            },
            body: JSON.stringify({ associacao: novaAssociacao })
        });
        
        const resultado = await response.json();
        
        if (resultado.success) {
            // Sucesso - borda verde por 1 segundo
            input.style.border = '2px solid #27ae60';
            
            // Atualizar dados em memória
            if (window.fluxoCaixaTransacoes && window.fluxoCaixaTransacoes[index]) {
                window.fluxoCaixaTransacoes[index].associacao = novaAssociacao;
            }
            
            setTimeout(() => {
                input.style.border = originalBorder;
                input.disabled = false;
            }, 1000);
            
        } else {
            // Erro - borda vermelha
            input.style.border = '2px solid #e74c3c';
            showToast(`Erro ao salvar: ${resultado.error}`, 'error');
            
            setTimeout(() => {
                input.style.border = originalBorder;
                input.disabled = false;
            }, 2000);
        }
        
    } catch (error) {
        console.error('Erro ao salvar associação:', error);
        input.style.border = '2px solid #e74c3c';
        showToast('Erro ao salvar associação', 'error');
        
        setTimeout(() => {
            input.style.border = '1px solid #ddd';
            input.disabled = false;
        }, 2000);
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
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken || ''
            }
        });
        
        if (!response.ok) throw new Error('Erro ao carregar contas');
        
        const result = await response.json();
        const contas = result.data || result; // Suporta formato {data: [...]} ou array direto
        const select = document.getElementById('filter-banco-fluxo');
        
        if (select && Array.isArray(contas)) {
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

// ============================================================================
// EXPORTAÇÃO FLUXO DE CAIXA - PDF E EXCEL
// ============================================================================

window.exportarFluxoCaixaPDF = function() {
    if (!window.fluxoCaixaTransacoes || window.fluxoCaixaTransacoes.length === 0) {
        showToast('⚠️ Nenhuma transação para exportar', 'warning');
        return;
    }
    
    const dados = window.fluxoCaixaDados || {};
    const transacoes = window.fluxoCaixaTransacoes;
    
    // Abrir janela de impressão para gerar PDF
    const win = window.open('', '_blank');
    if (!win) {
        alert('Bloqueador de pop-up ativo. Por favor, permita pop-ups para este site.');
        return;
    }
    
    win.document.write(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Fluxo de Caixa</title>
    <style>
        @page { size: landscape; margin: 15mm; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; font-size: 10pt; color: #333; }
        
        .cabecalho {
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 15px;
            margin-bottom: 15px;
        }
        .cabecalho h1 {
            font-size: 24pt;
            color: #2c3e50;
            margin-bottom: 8px;
        }
        .cabecalho .periodo {
            font-size: 12pt;
            color: #555;
            margin-bottom: 5px;
        }
        .cabecalho .info {
            font-size: 9pt;
            color: #888;
        }
        
        .resumo {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-around;
        }
        .resumo-item {
            text-align: center;
        }
        .resumo-item .label {
            font-size: 9pt;
            color: #666;
            margin-bottom: 5px;
        }
        .resumo-item .valor {
            font-size: 14pt;
            font-weight: bold;
        }
        .resumo-item.entrada .valor { color: #27ae60; }
        .resumo-item.saida .valor { color: #e74c3c; }
        .resumo-item.saldo .valor { color: #3498db; }
        
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
            font-size: 9pt;
            font-weight: bold;
        }
        td {
            padding: 8px;
            border-bottom: 1px solid #ddd;
            font-size: 9pt;
        }
        tbody tr:nth-child(odd) { background: #f9f9f9; }
        tbody tr:nth-child(even) { background: white; }
        
        .valor { text-align: right; font-weight: 500; }
        .tipo-receita { color: #27ae60; font-weight: bold; }
        .tipo-despesa { color: #e74c3c; font-weight: bold; }
        
        @media print {
            body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
        }
    </style>
</head>
<body>
    <div class="cabecalho">
        <h1>FLUXO DE CAIXA</h1>
        <div class="periodo">Período: ${formatarData(dados.dataInicio)} até ${formatarData(dados.dataFim)}</div>
        <div class="info">Conta: ${dados.banco || 'Todas as contas'} • Gerado em ${new Date().toLocaleString('pt-BR')} • ${transacoes.length} transação(ões)</div>
    </div>
    
    <div class="resumo">
        <div class="resumo-item entrada">
            <div class="label">💰 Total de Entradas</div>
            <div class="valor">R$ ${(dados.totalEntradas || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="resumo-item saida">
            <div class="label">💸 Total de Saídas</div>
            <div class="valor">R$ ${(dados.totalSaidas || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="resumo-item saldo">
            <div class="label">📊 Saldo do Período</div>
            <div class="valor">R$ ${(dados.saldoPeriodo || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th style="width: 10%;">Data</th>
                <th style="width: 8%;">Tipo</th>
                <th style="width: 20%;">Descrição</th>
                <th style="width: 14%;">Categoria</th>
                <th style="width: 14%;">Subcategoria</th>
                <th style="width: 12%;">Valor</th>
                <th style="width: 12%;">Conta</th>
                <th style="width: 10%;">Associação</th>
            </tr>
        </thead>
        <tbody>
`);
    
    // Linhas de dados
    transacoes.forEach(t => {
        const data = t.data_pagamento ? new Date(t.data_pagamento).toLocaleDateString('pt-BR') : '-';
        const tipo = (t.tipo || '').toLowerCase() === 'receita' ? 'ENTRADA' : 'SAÍDA';
        const tipoClass = (t.tipo || '').toLowerCase() === 'receita' ? 'tipo-receita' : 'tipo-despesa';
        const valor = parseFloat(t.valor).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        
        win.document.write(`
        <tr>
            <td>${data}</td>
            <td class="${tipoClass}">${tipo}</td>
            <td>${t.descricao || '-'}</td>
            <td>${t.categoria || '-'}</td>
            <td>${t.subcategoria || '-'}</td>
            <td class="valor">R$ ${valor}</td>
            <td>${t.conta_bancaria || '-'}</td>
            <td>${t.associacao || '-'}</td>
        </tr>`);
    });
    
    win.document.write(`
        </tbody>
    </table>
</body>
</html>`);
    
    win.document.close();
    setTimeout(() => win.print(), 250);
    
    showToast('✅ Relatório PDF gerado com sucesso!', 'success');
};

// ========== EXPORTAÇÃO FLUXO DE CAIXA EXCEL ==========
window.exportarFluxoCaixaExcel = function() {
    if (!window.fluxoCaixaTransacoes || window.fluxoCaixaTransacoes.length === 0) {
        showToast('⚠️ Nenhuma transação para exportar', 'warning');
        return;
    }
    
    const dados = window.fluxoCaixaDados || {};
    const transacoes = window.fluxoCaixaTransacoes;
    
    // Criar HTML que o Excel pode abrir com formatação
    let html = '<html xmlns:x="urn:schemas-microsoft-com:office:excel">\n';
    html += '<head>\n';
    html += '<meta charset="UTF-8">\n';
    html += '<style>\n';
    html += 'table { border-collapse: collapse; width: 100%; font-family: Arial; font-size: 11pt; }\n';
    html += 'th { background-color: #34495e; color: white; padding: 10px; text-align: left; font-weight: bold; border: 1px solid #000; }\n';
    html += 'td { padding: 8px; border: 1px solid #ddd; }\n';
    html += '.header { background-color: #f8f9fa; font-weight: bold; padding: 5px; margin: 10px 0; }\n';
    html += '.resumo { background-color: #ecf0f1; padding: 10px; margin: 10px 0; }\n';
    html += '.receita { color: #27ae60; font-weight: bold; }\n';
    html += '.despesa { color: #e74c3c; font-weight: bold; }\n';
    html += '.right { text-align: right; }\n';
    html += '</style>\n';
    html += '</head>\n';
    html += '<body>\n';
    
    // Cabeçalho com resumo
    html += '<div class="header">\n';
    html += '<h2>FLUXO DE CAIXA - RELATÓRIO DETALHADO</h2>\n';
    html += `<p><strong>Período:</strong> ${formatarData(dados.dataInicio)} até ${formatarData(dados.dataFim)}</p>\n`;
    html += `<p><strong>Conta:</strong> ${dados.banco || 'Todas as contas'}</p>\n`;
    html += `<p><strong>Emissão:</strong> ${new Date().toLocaleString('pt-BR')}</p>\n`;
    html += '</div>\n';
    
    html += '<div class="resumo">\n';
    html += '<h3>RESUMO FINANCEIRO</h3>\n';
    html += `<p><strong>Total de Entradas:</strong> <span style="color: #27ae60;">${formatarMoeda(dados.totalEntradas || 0)}</span></p>\n`;
    html += `<p><strong>Total de Saídas:</strong> <span style="color: #e74c3c;">${formatarMoeda(dados.totalSaidas || 0)}</span></p>\n`;
    html += `<p><strong>Saldo do Período:</strong> ${formatarMoeda(dados.saldoPeriodo || 0)}</p>\n`;
    html += '</div>\n';
    
    // Tabela de transações
    html += '<table>\n';
    html += '<thead>\n';
    html += '<tr>\n';
    html += '<th>Data</th>\n';
    html += '<th>Descrição</th>\n';
    html += '<th>Categoria</th>\n';
    html += '<th>Subcategoria</th>\n';
    html += '<th>Tipo</th>\n';
    html += '<th style="text-align: right;">Valor</th>\n';
    html += '<th>Conta</th>\n';
    html += '<th>Associação</th>\n';
    html += '</tr>\n';
    html += '</thead>\n';
    html += '<tbody>\n';
    
    // Dados
    transacoes.forEach(t => {
        const isReceita = t.tipo === 'receita';
        const valor = parseFloat(t.valor || 0);
        const valorFormatado = isReceita ? formatarMoeda(valor) : `- ${formatarMoeda(valor)}`;
        const corValor = isReceita ? '#27ae60' : '#e74c3c';
        
        html += '<tr>\n';
        html += `<td>${formatarData(t.data_pagamento)}</td>\n`;
        html += `<td>${escapeHtml(t.descricao || '-')}</td>\n`;
        html += `<td>${escapeHtml(t.categoria || '-')}</td>\n`;
        html += `<td>${escapeHtml(t.subcategoria || '-')}</td>\n`;
        html += `<td>${isReceita ? 'ENTRADA' : 'SAÍDA'}</td>\n`;
        html += `<td style="text-align: right; color: ${corValor}; font-weight: bold;">${valorFormatado}</td>\n`;
        html += `<td>${escapeHtml(t.conta_bancaria || '-')}</td>\n`;
        html += `<td>${escapeHtml(t.associacao || '-')}</td>\n`;
        html += '</tr>\n';
    });
    
    html += '</tbody>\n';
    html += '</table>\n';
    html += '</body>\n';
    html += '</html>';
    
    // Download do arquivo
    const blob = new Blob([html], { type: 'application/vnd.ms-excel;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fluxo_caixa_${new Date().toISOString().split('T')[0]}.xls`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    showToast('✅ Planilha Excel exportada com sucesso!', 'success');
};

// Função auxiliar para escapar HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// === HISTÓRICO DE CONCILIAÇÃO BANCÁRIA ===

let _historicoConciData = []; // cache para o modal de edição

window.abrirHistoricoConciliacao = async function() {
    const modal = document.getElementById('modal-historico-conciliacao');
    if (!modal) return;
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';

    // Preencher select de contas
    const selectConta = document.getElementById('hist-filtro-conta');
    if (selectConta && selectConta.options.length <= 1) {
        try {
            const resp = await fetch(`${API_URL}/contas`, { credentials: 'include', headers: { 'X-CSRFToken': window.csrfToken || '' } });
            if (resp.ok) {
                const result = await resp.json();
                const contas = result.data || result;
                selectConta.innerHTML = '<option value="">Todas as contas</option>';
                contas.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.nome;
                    opt.textContent = c.nome;
                    selectConta.appendChild(opt);
                });
            }
        } catch (e) { console.warn('Contas indisponíveis:', e); }
    }

    // Pré-preencher datas com o mês atual se vazios
    const hoje = new Date();
    const ini = document.getElementById('hist-filtro-inicio');
    const fim = document.getElementById('hist-filtro-fim');
    if (ini && !ini.value) {
        ini.value = new Date(hoje.getFullYear(), hoje.getMonth(), 1).toISOString().split('T')[0];
    }
    if (fim && !fim.value) {
        fim.value = hoje.toISOString().split('T')[0];
    }

    await carregarHistoricoConciliacao();
};

window.fecharHistoricoConciliacao = function() {
    const modal = document.getElementById('modal-historico-conciliacao');
    if (modal) modal.style.display = 'none';
    document.body.style.overflow = '';
};

window.carregarHistoricoConciliacao = async function() {
    const tbody = document.getElementById('tbody-historico-conciliacao');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="12" style="padding:40px; text-align:center; color:#95a5a6;">⏳ Carregando histórico...</td></tr>';

    const conta     = document.getElementById('hist-filtro-conta')?.value || '';
    const inicio    = document.getElementById('hist-filtro-inicio')?.value || '';
    const fim       = document.getElementById('hist-filtro-fim')?.value || '';
    const evento    = document.getElementById('hist-filtro-evento')?.value || '';

    const params = new URLSearchParams();
    if (conta)   params.append('conta', conta);
    if (inicio)  params.append('data_inicio', inicio);
    if (fim)     params.append('data_fim', fim);
    if (evento)  params.append('evento', evento);

    try {
        const resp = await fetch(`${API_URL}/extratos/historico-conciliacao?${params}`, {
            credentials: 'include',
            headers: { 'X-CSRFToken': window.csrfToken || '' }
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const dados = await resp.json();
        _historicoConciData = dados;

        const badge = document.getElementById('hist-total-badge');
        if (badge) badge.textContent = `${dados.length} registro(s)`;

        if (!dados.length) {
            tbody.innerHTML = '<tr><td colspan="12" style="padding:40px; text-align:center; color:#95a5a6;">Nenhuma conciliação encontrada para os filtros selecionados.</td></tr>';
            return;
        }

        // Coletar sugestões para datalists do modal de edição
        const categorias    = [...new Set(dados.map(d => d.categoria).filter(Boolean))].sort();
        const subcategorias = [...new Set(dados.map(d => d.subcategoria).filter(Boolean))].sort();
        const pessoas       = [...new Set(dados.map(d => d.pessoa).filter(Boolean))].sort();
        _preencherDatalist('edit-conc-categorias-list', categorias);
        _preencherDatalist('edit-conc-subcategorias-list', subcategorias);
        _preencherDatalist('edit-conc-pessoas-list', pessoas);

        tbody.innerHTML = dados.map((item, idx) => {
            // valor já vem como ABS() do banco — sempre positivo, sem manipulação de sinal
            const valor     = Math.abs(parseFloat(item.valor || 0));
            const tipoRaw   = (item.tipo_extrato || '').toUpperCase();
            const isDebito  = tipoRaw.includes('DEB') || tipoRaw.includes('DÉBITO') || tipoRaw.includes('DEBITO');
            const corValor  = isDebito ? '#e74c3c' : '#27ae60';
            const valorFmt  = 'R$ ' + valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            const tipoBadge = isDebito
                ? '<span style="background:#fee; color:#c0392b; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600;">DÉBITO</span>'
                : '<span style="background:#eafaf1; color:#27ae60; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600;">CRÉDITO</span>';
            const dataConc  = item.data_conciliacao ? item.data_conciliacao.split('T')[0] : '-';
            const bg        = idx % 2 === 0 ? '#fff' : '#f8f9fa';

            return `<tr style="background:${bg};">
                <td style="padding:10px 12px; white-space:nowrap; color:#555;">${item.data_transacao || '-'}</td>
                <td style="padding:10px 12px; font-size:12px; color:#555;">${escapeHtml(item.conta_bancaria || '')}</td>
                <td style="padding:10px 12px; max-width:260px; word-break:break-word; line-height:1.4; font-size:12px;">${escapeHtml(item.descricao_extrato || '')}${item.memo && item.memo !== item.descricao_extrato ? `<br><span style="color:#95a5a6; font-size:11px;">${escapeHtml(item.memo)}</span>` : ''}</td>
                <td style="padding:10px 12px; text-align:right; font-weight:700; color:${corValor}; white-space:nowrap; font-size:13px;">${valorFmt}</td>
                <td style="padding:10px 12px; text-align:center;">${tipoBadge}</td>
                <td style="padding:10px 12px; font-size:12px;">${escapeHtml(item.categoria || '<span style="color:#bdc3c7">—</span>')}</td>
                <td style="padding:10px 12px; font-size:12px;">${escapeHtml(item.subcategoria || '')||'<span style="color:#bdc3c7">—</span>'}</td>
                <td style="padding:10px 12px; font-size:12px; font-weight:500;">${escapeHtml(item.pessoa || '')||'<span style="color:#bdc3c7">—</span>'}</td>
                <td style="padding:10px 12px; font-size:12px; max-width:200px; word-break:break-word;">${escapeHtml(item.descricao_lancamento || '')||'<span style="color:#bdc3c7">—</span>'}</td>
                <td style="padding:10px 12px; font-size:12px; white-space:nowrap; color:#7f8c8d;">${dataConc}</td>
                <td style="padding:10px 12px; text-align:center;">
                    ${item.evento === 'desconciliado'
                        ? '<span style="background:#fee2e2; color:#c0392b; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700;">❌ Desconciliado</span>'
                        : '<span style="background:#d5f5e3; color:#1e8449; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700;">✅ Conciliado</span>'}
                </td>
                <td style="padding:10px 12px; text-align:center;">
                    ${item.evento === 'conciliado' && item.conciliacao_id
                        ? `<button onclick="abrirEdicaoConciliacao(${item.conciliacao_id})"
                            style="padding:5px 12px; background:#e67e22; color:white; border:none; border-radius:4px; cursor:pointer; font-size:12px; font-weight:600;"
                            title="Editar esta conciliação">✏️ Editar</button>`
                        : `<span style="font-size:11px; color:#bdc3c7;">—</span>`}
                </td>
            </tr>`;
        }).join('');

    } catch (e) {
        console.error('Erro ao carregar histórico:', e);
        tbody.innerHTML = `<tr><td colspan="12" style="padding:30px; text-align:center; color:#e74c3c;">❌ Erro ao carregar histórico: ${e.message}</td></tr>`;
    }
};

function _preencherDatalist(id, items) {
    const dl = document.getElementById(id);
    if (!dl) return;
    dl.innerHTML = items.map(i => `<option value="${escapeHtml(i)}">`).join('');
}

window.limparFiltrosHistoricoConc = function() {
    const ini = document.getElementById('hist-filtro-inicio');
    const fim = document.getElementById('hist-filtro-fim');
    const cta = document.getElementById('hist-filtro-conta');
    if (ini) ini.value = '';
    if (fim) fim.value = '';
    if (cta) cta.value = '';
    const evt = document.getElementById('hist-filtro-evento');
    if (evt) evt.value = '';
    carregarHistoricoConciliacao();
};

window.abrirEdicaoConciliacao = function(conciliacaoId) {
    const item = _historicoConciData.find(d => d.conciliacao_id === conciliacaoId);
    if (!item) { showToast('Registro não encontrado', 'error'); return; }

    document.getElementById('edit-conc-id').value          = conciliacaoId;
    document.getElementById('edit-conc-descricao').value   = item.descricao_lancamento || '';
    document.getElementById('edit-conc-categoria').value   = item.categoria || '';
    document.getElementById('edit-conc-subcategoria').value = item.subcategoria || '';
    document.getElementById('edit-conc-pessoa').value      = item.pessoa || '';
    document.getElementById('edit-conc-observacoes').value = item.observacoes || '';

    // Info somente-leitura
    const valor   = parseFloat(item.valor || 0);
    const sinal   = valor < 0 ? '-' : '+';
    document.getElementById('edit-conc-info-extrato').textContent =
        `${item.data_transacao}  •  ${item.conta_bancaria}  •  ${item.descricao_extrato}  •  ${sinal} R$ ${Math.abs(valor).toLocaleString('pt-BR', {minimumFractionDigits:2})}`;

    const modal = document.getElementById('modal-editar-conciliacao');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
};

window.fecharEdicaoConciliacao = function() {
    const modal = document.getElementById('modal-editar-conciliacao');
    if (modal) modal.style.display = 'none';
};

window.salvarEdicaoConciliacao = async function() {
    const id = document.getElementById('edit-conc-id').value;
    if (!id) return;

    const payload = {
        descricao_lancamento: document.getElementById('edit-conc-descricao').value.trim(),
        categoria:            document.getElementById('edit-conc-categoria').value.trim(),
        subcategoria:         document.getElementById('edit-conc-subcategoria').value.trim(),
        pessoa:               document.getElementById('edit-conc-pessoa').value.trim(),
        observacoes:          document.getElementById('edit-conc-observacoes').value.trim()
    };

    try {
        const resp = await fetch(`${API_URL}/extratos/conciliacao/${id}`, {
            method: 'PATCH',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.csrfToken || '' },
            body: JSON.stringify(payload)
        });
        const result = await resp.json();
        if (!resp.ok) throw new Error(result.erro || result.error || 'Erro ao salvar');

        showToast('✅ Conciliação atualizada com sucesso!', 'success');
        fecharEdicaoConciliacao();

        // Atualizar cache local e recarregar tabela
        const item = _historicoConciData.find(d => d.conciliacao_id === parseInt(id));
        if (item) {
            item.descricao_lancamento = payload.descricao_lancamento;
            item.categoria            = payload.categoria;
            item.subcategoria         = payload.subcategoria;
            item.pessoa               = payload.pessoa;
            item.observacoes          = payload.observacoes;
        }
        await carregarHistoricoConciliacao();

    } catch (e) {
        console.error('Erro ao salvar edição:', e);
        showToast(`Erro ao salvar: ${e.message}`, 'error');
    }
};

// === REGERAR CONCILIAÇÃO ===
window.abrirRegerarConciliacao = function() {
    const conta = document.getElementById('hist-filtro-conta')?.value || '';
    const inicio = document.getElementById('hist-filtro-inicio')?.value || '';
    const fim = document.getElementById('hist-filtro-fim')?.value || '';

    if (!conta) {
        mostrarToast('Selecione uma conta bancária específica antes de regerar.', 'warning');
        return;
    }
    if (!inicio || !fim) {
        mostrarToast('Defina Data Início e Data Fim antes de regerar.', 'warning');
        return;
    }
    if (inicio > fim) {
        mostrarToast('Data Início não pode ser maior que Data Fim.', 'warning');
        return;
    }

    // Populate summary
    const contaEl = document.getElementById('hist-filtro-conta');
    const contaText = contaEl?.options[contaEl.selectedIndex]?.text || conta;
    const totalBadge = document.getElementById('hist-total-badge')?.textContent || '—';

    document.getElementById('regerar-resumo-conta').textContent = contaText;
    document.getElementById('regerar-resumo-inicio').textContent = inicio.split('-').reverse().join('/');
    document.getElementById('regerar-resumo-fim').textContent = fim.split('-').reverse().join('/');
    document.getElementById('regerar-resumo-total').textContent = totalBadge;

    // Reset UI state
    const progress = document.getElementById('regerar-progress');
    const footer = document.getElementById('regerar-footer');
    const btnFechar = document.getElementById('btn-fechar-regerar');
    const btnConfirmar = document.getElementById('btn-confirmar-regerar');
    if (progress) progress.style.display = 'none';
    if (footer) footer.style.display = 'flex';
    if (btnFechar) btnFechar.disabled = false;
    if (btnConfirmar) btnConfirmar.disabled = false;

    document.getElementById('modal-regerar-conciliacao').style.display = 'flex';
};

window.fecharRegerarConciliacao = function() {
    document.getElementById('modal-regerar-conciliacao').style.display = 'none';
};

window.confirmarRegerarConciliacao = async function() {
    const conta = document.getElementById('hist-filtro-conta')?.value || '';
    const inicio = document.getElementById('hist-filtro-inicio')?.value || '';
    const fim = document.getElementById('hist-filtro-fim')?.value || '';

    // Show progress, hide footer
    const progress = document.getElementById('regerar-progress');
    const footer = document.getElementById('regerar-footer');
    const btnFechar = document.getElementById('btn-fechar-regerar');
    const btnConfirmar = document.getElementById('btn-confirmar-regerar');
    if (progress) progress.style.display = 'block';
    if (footer) footer.style.display = 'none';
    if (btnFechar) btnFechar.disabled = true;
    if (btnConfirmar) btnConfirmar.disabled = true;

    try {
        const empresaId = window.currentEmpresaId || localStorage.getItem('empresa_id');
        const response = await fetch('/api/extratos/regerar-conciliacao', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Empresa-ID': empresaId
            },
            body: JSON.stringify({ conta, data_inicio: inicio, data_fim: fim })
        });

        const data = await response.json();
        fecharRegerarConciliacao();

        if (response.ok && data.success) {
            const tipo = data.erros > 0 ? 'warning' : 'success';
            mostrarToast(data.message || `✅ Regenerados: ${data.criados} lançamentos.`, tipo);
        } else {
            mostrarToast(data.erro || data.message || 'Erro ao regerar conciliações.', 'error');
        }

        await carregarHistoricoConciliacao();
        // Atualizar Contas a Receber e Contas a Pagar com os novos lançamentos
        if (typeof loadContasReceber === 'function') await loadContasReceber();
        if (typeof loadContasPagar   === 'function') await loadContasPagar();
        if (typeof loadDashboard     === 'function') loadDashboard();
    } catch (err) {
        console.error('Erro ao regerar conciliação:', err);
        fecharRegerarConciliacao();
        mostrarToast('Erro de conexão ao regerar conciliações.', 'error');
    }
};

// === CONCILIAÇÃO GERAL DE EXTRATO ===
window.abrirConciliacaoGeral = async function() {
    console.log('🔄 [APP.JS] Abrindo Conciliação Geral...');
    
    try {
        // Obter extratos filtrados e não conciliados
        console.log('📡 Buscando transações não conciliadas...');
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
        
        const responseData = await response.json();
        
        // Suportar novo formato (objeto com transacoes + saldo_anterior) e formato antigo (array direto)
        let transacoes;
        if (Array.isArray(responseData)) {
            transacoes = responseData;
        } else {
            transacoes = responseData.transacoes || [];
        }
        
        console.log('📊 Transações não conciliadas:', transacoes.length);
        
        if (transacoes.length === 0) {
            showToast('Nenhuma transação não conciliada encontrada no período filtrado', 'warning');
            return;
        }
        
        // Buscar categorias e subcategorias
        console.log('📡 Buscando categorias, clientes e fornecedores...');
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
        
        const categoriasData = await responseCategorias.json();
        const clientesData = await responseClientes.json();
        const fornecedoresData = await responseFornecedores.json();
        
        // Extrair arrays dos dados (pode vir como {data: [...]} ou direto)
        const categorias = Array.isArray(categoriasData) ? categoriasData : (categoriasData.categorias || categoriasData.data || []);
        const clientes = Array.isArray(clientesData) ? clientesData : (clientesData.clientes || clientesData.data || []);
        const fornecedores = Array.isArray(fornecedoresData) ? fornecedoresData : (fornecedoresData.fornecedores || fornecedoresData.data || []);
        
        console.log('📂 Categorias carregadas:', categorias.length);
        console.log('👥 Clientes:', clientes.length, '| Fornecedores:', fornecedores.length);
        
        // Debug: mostrar primeira categoria
        if (categorias.length > 0) {
            console.log('🔍 Primeira categoria:', categorias[0]);
            console.log('   - nome:', categorias[0].nome);
            console.log('   - tipo:', categorias[0].tipo, '(type:', typeof categorias[0].tipo + ')');
            console.log('   - subcategorias:', categorias[0].subcategorias);
        }
        
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
        
        // 🔧 FIX: Agrupar categorias por tipo usando LOWERCASE
        const categoriasDespesa = categorias.filter(c => (c.tipo || '').toLowerCase() === 'despesa');
        const categoriasReceita = categorias.filter(c => (c.tipo || '').toLowerCase() === 'receita');
        
        console.log('📊 Categorias filtradas:');
        console.log('   - Despesas:', categoriasDespesa.length);
        console.log('   - Receitas:', categoriasReceita.length);
        if (categoriasDespesa.length > 0) {
            console.log('   - Despesa exemplo:', categoriasDespesa[0].nome);
        }
        if (categoriasReceita.length > 0) {
            console.log('   - Receita exemplo:', categoriasReceita[0].nome);
        }
        
        // 🔧 NOVO: Carregar regras de auto-conciliação
        console.log('📋 Carregando regras de auto-conciliação...');
        let regrasAtivas = [];
        try {
            const regrasResponse = await fetch(`${API_URL}/regras-conciliacao`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            const regrasData = await regrasResponse.json();
            regrasAtivas = Array.isArray(regrasData) ? regrasData : (regrasData.data || regrasData.regras || []);
            regrasAtivas = regrasAtivas.filter(r => r.ativo); // Apenas ativas
            console.log('✅', regrasAtivas.length, 'regra(s) ativa(s) carregadas');
        } catch (error) {
            console.warn('⚠️ Não foi possível carregar regras:', error);
        }
        
        // Preparar listas de razão social
        const clientesOpcoes = clientes.map(c => ({
            value: c.razao_social || c.nome,
            label: c.razao_social || c.nome
        }));
        const fornecedoresOpcoes = fornecedores.map(f => ({
            value: f.razao_social || f.nome,
            label: f.razao_social || f.nome
        }));
        
        // Renderizar lista de transações
        let html = `
            <div style="background: #ecf0f1; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="font-size: 16px;"><span id="conciliacao-count-visivel">${transacoes.length}</span> de ${transacoes.length} transações</strong>
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
            
            <!-- Filtros da Conciliação Geral -->
            <div style="background: #fff; padding: 12px 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #ddd; display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap;">
                <div style="flex: 0 0 140px;">
                    <label style="display: block; font-size: 11px; font-weight: bold; color: #555; margin-bottom: 4px;">🔽 Tipo</label>
                    <select id="filtro-tipo-conciliacao" onchange="filtrarConciliacaoGeral()" 
                            style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px;">
                        <option value="">Todos</option>
                        <option value="DEBITO">Débito</option>
                        <option value="CREDITO">Crédito</option>
                    </select>
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <label style="display: block; font-size: 11px; font-weight: bold; color: #555; margin-bottom: 4px;">🔍 Descrição</label>
                    <input type="text" id="filtro-descricao-conciliacao" oninput="filtrarConciliacaoGeral()" placeholder="Buscar na descrição..."
                           style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px;">
                </div>
                <div style="flex: 0 0 140px;">
                    <label style="display: block; font-size: 11px; font-weight: bold; color: #555; margin-bottom: 4px;">📅 Valor mín.</label>
                    <input type="number" id="filtro-valor-min-conciliacao" oninput="filtrarConciliacaoGeral()" placeholder="0,00" step="0.01"
                           style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px;">
                </div>
                <div style="flex: 0 0 140px;">
                    <label style="display: block; font-size: 11px; font-weight: bold; color: #555; margin-bottom: 4px;">📅 Valor máx.</label>
                    <input type="number" id="filtro-valor-max-conciliacao" oninput="filtrarConciliacaoGeral()" placeholder="0,00" step="0.01"
                           style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px;">
                </div>
                <div style="flex: 0 0 auto;">
                    <button onclick="limparFiltrosConciliacao()" style="padding: 6px 14px; background: #e74c3c; color: white; border: none; border-radius: 4px; font-size: 12px; cursor: pointer;">
                        ✕ Limpar Filtros
                    </button>
                </div>
            </div>
            
            <div style="max-height: 500px; overflow-y: auto;" id="conciliacao-tabela-container">
                <table class="data-table" style="width: 100%; border-collapse: collapse;">
                    <thead style="position: sticky; top: 0; background: #34495e; color: white; z-index: 1;">
                        <tr>
                            <th style="width: 50px; text-align: center;">✓</th>
                            <th style="width: 100px;">Data</th>
                            <th style="min-width: 200px;">Descrição Original</th>
                            <th style="width: 120px;">Valor</th>
                            <th style="width: 80px;">Tipo</th>
                            <th style="width: 200px;">Razão Social</th>
                            <th style="width: 200px;">Categoria</th>
                            <th style="width: 200px;">Subcategoria</th>
                            <th style="min-width: 250px;">📝 Descrição</th>
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
            
            // Debug primeira transação
            if (index === 0) {
                console.log(`🔍 Transação #${t.id}:`);
                console.log('   - Tipo:', t.tipo, '| isCredito:', isCredito);
                console.log('   - Categorias disponíveis:', categoriasOpcoes.length);
            }
            
            html += `
                <tr style="border-bottom: 1px solid #ecf0f1;" data-tipo="${isCredito ? 'CREDITO' : 'DEBITO'}" data-descricao="${(t.descricao || '').replace(/"/g, '&quot;').toUpperCase()}" data-valor="${Math.abs(parseFloat(t.valor || 0))}">
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
                        <select id="razao-${t.id}"
                                style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px;">
                            <option value="">Selecione ${isCredito ? 'Cliente' : 'Fornecedor'}...</option>
                            ${(isCredito ? clientesOpcoes : fornecedoresOpcoes).map(p => 
                                `<option value="${p.value}" ${p.value === razaoSugerida ? 'selected' : ''}>${p.label}</option>`
                            ).join('')}
                        </select>
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
                    <td>
                        <input type="text" id="descricao-${t.id}" 
                               value="${(t.descricao || '').replace(/"/g, '&quot;')}" 
                               placeholder="Descrição personalizada (opcional)" 
                               style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; background: #fffef7;">
                    </td>
                </tr>`;
        });
        
        html += `
                    </tbody>
                </table>
            </div>`;
        
        document.getElementById('conciliacao-transacoes-lista').innerHTML = html;
        
        // ⚙️ Armazenar dados para processamento (ANTES de aplicar regras!)
        window.transacoesConciliacao = transacoes;
        window.categoriasConciliacao = categorias;
        
        // 🤖 Aplicar regras de auto-conciliação
        if (regrasAtivas.length > 0) {
            console.log('🤖 Aplicando regras de auto-conciliação...');
            let aplicadas = 0;
            
            transacoes.forEach(t => {
                const descricao = (t.descricao || '').toUpperCase();
                
                // Procurar regra que faça match
                for (const regra of regrasAtivas) {
                    const palavraChave = (regra.palavra_chave || '').toUpperCase();
                    
                    if (palavraChave && descricao.includes(palavraChave)) {
                        console.log(`   ✓ Match encontrado: "${palavraChave}" em transação #${t.id}`);
                        
                        // Auto-preencher categoria
                        const catSelect = document.getElementById(`categoria-${t.id}`);
                        if (catSelect && regra.categoria) {
                            catSelect.value = regra.categoria;
                            
                            // Auto-carregar subcategorias
                            carregarSubcategoriasConciliacao(t.id, regra.categoria);
                            
                            // Auto-preencher subcategoria (após delay para aguardar carregamento)
                            if (regra.subcategoria) {
                                setTimeout(() => {
                                    const subSelect = document.getElementById(`subcategoria-${t.id}`);
                                    if (subSelect) {
                                        subSelect.value = regra.subcategoria;
                                    }
                                }, 150);
                            }
                        }
                        
                        // Auto-preencher razão social (cliente_padrao)
                        if (regra.cliente_padrao) {
                            const razaoSelect = document.getElementById(`razao-${t.id}`);
                            if (razaoSelect) {
                                razaoSelect.value = regra.cliente_padrao;
                            }
                        }
                        
                        aplicadas++;
                        break; // Primeira regra que der match
                    }
                }
            });
            
            if (aplicadas > 0) {
                console.log(`✅ ${aplicadas} regra(s) aplicada(s) automaticamente de ${transacoes.length} transações`);
            } else {
                console.log('⚠️ Nenhuma regra aplicada (nenhum match encontrado)');
            }
        }
        
        console.log('✅ Modal renderizado com sucesso');
        
        // Mostrar modal
        document.getElementById('modal-conciliacao-geral').style.display = 'block';
        
    } catch (error) {
        console.error('❌ Erro ao abrir conciliação geral:', error);
        showToast('Erro ao carregar dados de conciliação', 'error');
    }
};

window.toggleTodasConciliacoes = function(checked) {
    // Selecionar apenas as checkboxes das linhas VISÍVEIS
    document.querySelectorAll('.checkbox-conciliacao').forEach(cb => {
        const row = cb.closest('tr');
        if (row && row.style.display !== 'none') {
            cb.checked = checked;
        }
    });
};

// Filtrar transações da Conciliação Geral (client-side, preserva dados preenchidos)
window.filtrarConciliacaoGeral = function() {
    const filtroTipo = (document.getElementById('filtro-tipo-conciliacao')?.value || '').toUpperCase();
    const filtroDescricao = (document.getElementById('filtro-descricao-conciliacao')?.value || '').toUpperCase().trim();
    const filtroValorMin = parseFloat(document.getElementById('filtro-valor-min-conciliacao')?.value || '');
    const filtroValorMax = parseFloat(document.getElementById('filtro-valor-max-conciliacao')?.value || '');
    
    const container = document.getElementById('conciliacao-tabela-container');
    if (!container) return;
    
    const rows = container.querySelectorAll('tbody tr');
    let visiveis = 0;
    
    rows.forEach(row => {
        const tipo = row.getAttribute('data-tipo') || '';
        const descricao = row.getAttribute('data-descricao') || '';
        const valor = parseFloat(row.getAttribute('data-valor') || '0');
        
        let mostrar = true;
        
        // Filtro por tipo
        if (filtroTipo && tipo !== filtroTipo) {
            mostrar = false;
        }
        
        // Filtro por descrição
        if (filtroDescricao && !descricao.includes(filtroDescricao)) {
            mostrar = false;
        }
        
        // Filtro por valor mínimo
        if (!isNaN(filtroValorMin) && valor < filtroValorMin) {
            mostrar = false;
        }
        
        // Filtro por valor máximo
        if (!isNaN(filtroValorMax) && valor > filtroValorMax) {
            mostrar = false;
        }
        
        row.style.display = mostrar ? '' : 'none';
        if (mostrar) visiveis++;
    });
    
    // Atualizar contador
    const countEl = document.getElementById('conciliacao-count-visivel');
    if (countEl) {
        countEl.textContent = visiveis;
    }
};

// Limpar filtros da Conciliação Geral (preserva dados preenchidos pelo usuário)
window.limparFiltrosConciliacao = function() {
    const tipoSelect = document.getElementById('filtro-tipo-conciliacao');
    const descInput = document.getElementById('filtro-descricao-conciliacao');
    const valorMinInput = document.getElementById('filtro-valor-min-conciliacao');
    const valorMaxInput = document.getElementById('filtro-valor-max-conciliacao');
    
    if (tipoSelect) tipoSelect.value = '';
    if (descInput) descInput.value = '';
    if (valorMinInput) valorMinInput.value = '';
    if (valorMaxInput) valorMaxInput.value = '';
    
    // Mostrar todas as linhas
    const container = document.getElementById('conciliacao-tabela-container');
    if (container) {
        const rows = container.querySelectorAll('tbody tr');
        rows.forEach(row => { row.style.display = ''; });
        
        const countEl = document.getElementById('conciliacao-count-visivel');
        if (countEl) countEl.textContent = rows.length;
    }
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
            const descricao = document.getElementById(`descricao-${transacao.id}`).value.trim();
            
            if (!categoria) {
                errosValidacao.push(`Transação "${transacao.descricao.substring(0, 30)}...": categoria não selecionada`);
                return;
            }
            
            selecionadas.push({
                transacao_id: transacao.id,
                categoria: categoria,
                subcategoria: subcategoria,
                razao_social: razaoSocial,
                descricao: descricao || null
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
        
        if (!response.ok) {
            // Erro HTTP (400, 500, etc)
            const errorData = await response.json().catch(() => ({ error: 'Erro desconhecido' }));
            console.error('❌ Erro HTTP na conciliação:', response.status);
            console.error('📦 Dados do erro:', JSON.stringify(errorData, null, 2));
            
            fecharConciliacaoGeral();
            
            // Extrair mensagem de erro (pode vir em error, message, ou erros array)
            let mensagemErro = '';
            if (errorData.error) {
                mensagemErro = errorData.error;
            } else if (errorData.message) {
                mensagemErro = errorData.message;
            } else if (errorData.erros && Array.isArray(errorData.erros) && errorData.erros.length > 0) {
                mensagemErro = errorData.erros.slice(0, 3).join('\n');
                if (errorData.erros.length > 3) {
                    mensagemErro += `\n\n... e mais ${errorData.erros.length - 3} erro(s)`;
                }
            } else {
                mensagemErro = `Erro ${response.status} ao processar conciliação`;
            }
            
            console.error('💬 Mensagem final:', mensagemErro);
            showToast(mensagemErro, 'error');
            
            // Recarregar extratos se a função existir
            if (typeof window.loadExtratoTransacoes === 'function') {
                await window.loadExtratoTransacoes();
            }
            return;
        }
        
        const result = await response.json();
        
        // Verificar se houve falha total (nenhuma conciliação bem-sucedida)
        if (!result.success || result.criados === 0) {
            // Fechar modal ANTES de mostrar erro
            fecharConciliacaoGeral();
            
            let mensagemErro = result.message || 'Erro ao processar conciliação';
            
            if (result.erros && result.erros.length > 0) {
                mensagemErro = result.erros.join('\n\n');
            }
            
            showToast(mensagemErro, 'error');
            
            // Recarregar extratos se a função existir
            if (typeof window.loadExtratoTransacoes === 'function') {
                await window.loadExtratoTransacoes();
            }
            return;
        }
        
        let mensagem = `✅ Conciliação concluída!\n${result.criados} lançamento(s) criado(s)`;
        
        if (result.erros && result.erros.length > 0) {
            mensagem += `\n\n⚠️ Avisos:\n${result.erros.slice(0, 3).join('\n')}`;
            if (result.erros.length > 3) {
                mensagem += `\n... e mais ${result.erros.length - 3} erro(s)`;
            }
        }
        
        showToast(mensagem, result.erros && result.erros.length > 0 ? 'warning' : 'success');
        
        // Fechar modal e recarregar
        fecharConciliacaoGeral();
        
        // Recarregar extratos se a função existir
        if (typeof window.loadExtratoTransacoes === 'function') {
            await window.loadExtratoTransacoes();
        }
        
    } catch (error) {
        console.error('Erro ao processar conciliação:', error);
        
        // Fechar modal ANTES de mostrar erro
        fecharConciliacaoGeral();
        
        showToast(error.message || 'Erro ao processar conciliação', 'error');
        
        // Recarregar lista mesmo com erro
        if (typeof window.loadExtratoTransacoes === 'function') {
            try {
                await window.loadExtratoTransacoes();
            } catch (reloadError) {
                console.error('Erro ao recarregar extratos:', reloadError);
            }
        }
    }
};

window.fecharConciliacaoGeral = function() {
    document.getElementById('modal-conciliacao-geral').style.display = 'none';
    window.transacoesConciliacao = null;
    window.categoriasConciliacao = null;
};

// ============================================================================
// MÓDULO NFS-e (Notas Fiscais de Serviço Eletrônica)
// ============================================================================

window.nfsesCarregadas = [];
window.municipiosNFSe = [];

// Carregar seção NFS-e
window.loadNFSeSection = async function() {
    console.log('📄 Carregando seção NFS-e...');
    
    // Data inicial: Carregar preferência salva ou usar 01/01/2020 como padrão
    const dataInicialSalva = localStorage.getItem('nfse_data_inicial');
    const dataInicial = dataInicialSalva || '2020-01-01';
    
    // Data final: Sempre usar o último dia do mês atual
    const hoje = new Date();
    const ultimoDia = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0);
    
    document.getElementById('nfse-data-inicial').value = dataInicial;
    document.getElementById('nfse-data-final').value = ultimoDia.toISOString().split('T')[0];
    
    // Salvar preferência quando usuário alterar a data inicial
    document.getElementById('nfse-data-inicial').addEventListener('change', function(e) {
        localStorage.setItem('nfse_data_inicial', e.target.value);
        console.log(`💾 Data inicial salva: ${e.target.value}`);
    });
    
    // Carregar lista de municípios configurados
    await window.carregarMunicipiosNFSe();

    // Auto-preencher CNPJ no formulário de Configurar Municípios a partir do certificado ativo
    await window.preencherCNPJMunicipioDosCertificados();
    
    // Auto-carregar NFS-e do período
    await window.consultarNFSeLocal();
};

// Carregar municípios configurados no dropdown
window.carregarMunicipiosNFSe = async function() {
    try {
        const response = await fetch('/api/nfse/config', {
            method: 'GET',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.municipiosNFSe = data.configs || [];
            
            const select = document.getElementById('nfse-municipio');
            select.innerHTML = '<option value="">Todos os municípios</option>';
            
            window.municipiosNFSe.forEach(config => {
                const option = document.createElement('option');
                option.value = config.codigo_municipio;
                option.textContent = `${config.nome_municipio}/${config.uf} - ${config.provedor}`;
                select.appendChild(option);
            });
            
            console.log(`✅ ${window.municipiosNFSe.length} municípios carregados`);
        } else {
            console.error('❌ Erro ao carregar municípios:', data.error);
        }
    } catch (error) {
        console.error('❌ Erro ao carregar municípios:', error);
    }
};

// Auto-preenche o campo CNPJ do form de Configurar Municípios com o certificado ativo
// Consulta BrasilAPI com CNPJ e preenche Nome do Município, Código IBGE e UF
window.consultarCNPJPreencherMunicipio = async function(cnpj) {
    if (!cnpj) return;
    const digits = cnpj.replace(/\D/g, '');
    if (digits.length !== 14) return;

    const nomeInput = document.getElementById('config-nome-municipio');
    const ibgeInput = document.getElementById('config-codigo-municipio');
    const ufSelect  = document.getElementById('config-uf');
    if (!nomeInput || !ibgeInput || !ufSelect) return;

    const statusEl = document.getElementById('config-cnpj-status');
    if (statusEl) { statusEl.textContent = '⏳ Consultando CNPJ...'; statusEl.style.color = '#888'; }

    try {
        // 1) Dados da empresa na Receita Federal
        const resp = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${digits}`, {
            headers: { 'Accept': 'application/json' }
        });
        if (!resp.ok) {
            if (statusEl) { statusEl.textContent = '⚠️ CNPJ não encontrado na Receita Federal'; statusEl.style.color = '#e67e22'; }
            return;
        }
        const empresa = await resp.json();

        const uf = (empresa.uf || '').toUpperCase().trim();
        // BrasilAPI CNPJ retorna nome em maiúsculas — normalizar para Title Case
        const nomeBruto = (empresa.municipio || '').toLowerCase();
        const nomeMunicipio = nomeBruto.replace(/\b\w/g, c => c.toUpperCase());

        // 2) Buscar código IBGE de 7 dígitos via API oficial do IBGE
        //    (BrasilAPI CNPJ retorna código TOM de 4 dígitos da Receita Federal,
        //     não o IBGE de 7 dígitos exigido pelos webservices NFS-e)
        const normalizar = s => (s || '').toLowerCase()
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .replace(/[^a-z0-9 ]/g, '').trim();

        let codigoIBGE = '';
        if (uf && nomeBruto) {
            try {
                // API oficial IBGE — retorna [{id: 5002704, nome: "Campo Grande"}, ...]
                const ibgeResp = await fetch(
                    `https://servicodados.ibge.gov.br/api/v1/localidades/estados/${uf}/municipios`,
                    { headers: { 'Accept': 'application/json' } }
                );
                if (ibgeResp.ok) {
                    const municipios = await ibgeResp.json();
                    const nomeBuscado = normalizar(nomeBruto);
                    console.log(`🔍 Buscando IBGE para: "${nomeBuscado}" em ${uf} (${municipios.length} municípios)`);
                    const encontrado = municipios.find(m => normalizar(m.nome) === nomeBuscado);
                    if (encontrado) {
                        codigoIBGE = String(encontrado.id || '').trim();
                        console.log(`✅ IBGE encontrado: ${encontrado.nome} → ${codigoIBGE}`);
                    } else {
                        console.warn(`⚠️ Município "${nomeBuscado}" não encontrado na lista IBGE de ${uf}`);
                    }
                }
            } catch (ibgeErr) {
                console.warn('⚠️ Erro ao buscar IBGE:', ibgeErr);
            }
        }

        // 3) Preencher campos (só se estiverem vazios)
        if (nomeMunicipio && (!nomeInput.value || nomeInput.value.trim() === '')) {
            nomeInput.value = nomeMunicipio;
        }
        if (codigoIBGE && (!ibgeInput.value || ibgeInput.value.trim() === '')) {
            ibgeInput.value = codigoIBGE;
        }
        if (uf && ufSelect.value === '') {
            for (const opt of ufSelect.options) {
                if (opt.value === uf) { ufSelect.value = uf; break; }
            }
        }

        const ibgeDisplay = codigoIBGE || '(IBGE não encontrado — preencha manualmente)';
        if (statusEl) {
            statusEl.textContent = nomeMunicipio
                ? `✅ ${nomeMunicipio}/${uf} — IBGE: ${ibgeDisplay}`
                : '✅ CNPJ encontrado';
            statusEl.style.color = codigoIBGE ? '#27ae60' : '#e67e22';
        }
        console.log(`✅ CNPJ lookup: municipio=${nomeMunicipio}, uf=${uf}, ibge=${codigoIBGE}`);

    } catch (err) {
        console.warn('⚠️ Erro ao consultar CNPJ:', err);
        if (statusEl) { statusEl.textContent = '⚠️ Erro ao consultar CNPJ'; statusEl.style.color = '#e74c3c'; }
    }
};

window.preencherCNPJMunicipioDosCertificados = async function() {
    try {
        const cnpjInput = document.getElementById('config-cnpj');
        if (!cnpjInput) return;

        // Registrar listener para quando o usuário mudar o CNPJ manualmente
        if (!cnpjInput._cnpjListenerAdded) {
            cnpjInput._cnpjListenerAdded = true;
            cnpjInput.addEventListener('change', function() {
                // ao alterar, limpa campos de município para permitir novo preenchimento
                const nomeInput = document.getElementById('config-nome-municipio');
                const ibgeInput = document.getElementById('config-codigo-municipio');
                const ufSelect  = document.getElementById('config-uf');
                if (nomeInput) nomeInput.value = '';
                if (ibgeInput) ibgeInput.value = '';
                if (ufSelect)  ufSelect.value  = '';
                window.consultarCNPJPreencherMunicipio(cnpjInput.value);
            });
        }

        // Só preenche CNPJ se estiver vazio (não sobrescreve edição manual)
        if (!cnpjInput.value || cnpjInput.value.trim() === '') {
            const response = await fetch('/api/relatorios/certificados', {
                method: 'GET',
                credentials: 'include'
            });
            if (!response.ok) return;
            const data = await response.json();

            const certs = data.certificados || [];
            const ativo = certs.find(c => c.ativo) || certs[0];
            if (!ativo) return;

            const cnpj = ativo.cnpj || '';
            if (cnpj) {
                cnpjInput.value = cnpj;
                console.log(`✅ CNPJ preenchido do certificado ativo: ${cnpj}`);
            }
        }

        // Consulta Receita Federal e preenche município, IBGE e UF
        if (cnpjInput.value) {
            await window.consultarCNPJPreencherMunicipio(cnpjInput.value);
        }

    } catch (err) {
        console.warn('⚠️ Não foi possível obter CNPJ do certificado:', err);
    }
};

// Consultar NFS-e no banco local (sem API SOAP)
window.consultarNFSeLocal = async function() {
    const dataInicial = document.getElementById('nfse-data-inicial').value;
    const dataFinal = document.getElementById('nfse-data-final').value;
    const codigoMunicipio = document.getElementById('nfse-municipio').value;
    
    if (!dataInicial || !dataFinal) {
        showToast('⚠️ Selecione o período (data inicial e final)', 'warning');
        return;
    }
    
    console.log('🔍 Consultando NFS-e localmente:', { dataInicial, dataFinal, codigoMunicipio });
    
    // Resetar paginação
    window.nfsePaginacao = {
        paginaAtual: 1,
        registrosPorPagina: parseInt(document.getElementById('nfse-registros-por-pagina').value) || 100,
        totalRegistros: 0,
        totalPaginas: 0
    };
    
    // Mostrar loading
    const tbody = document.getElementById('tbody-nfse');
    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px;"><div style="font-size: 24px;">⏳</div><p>Consultando banco de dados...</p></td></tr>';
    
    try {
        const body = {
            data_inicial: dataInicial,
            data_final: dataFinal
            // NÃO enviar limit - API retorna TODOS os registros
        };
        
        if (codigoMunicipio) {
            body.codigo_municipio = codigoMunicipio;
        }
        
        const response = await fetch('/api/nfse/consultar', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.nfsesCarregadas = data.nfses || [];
            window.nfsePaginacao.totalRegistros = window.nfsesCarregadas.length;
            window.nfsePaginacao.totalPaginas = Math.ceil(window.nfsePaginacao.totalRegistros / window.nfsePaginacao.registrosPorPagina);
            
            window.exibirNFSePaginado();
            window.atualizarResumoNFSe(window.nfsesCarregadas);
            window.atualizarControlesPaginacao();
            
            showToast(`✅ ${window.nfsesCarregadas.length} NFS-e encontradas`, 'success');
        } else {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 40px; color: #e74c3c;"><div style="font-size: 48px;">❌</div><h3>Erro ao Consultar</h3><p>${data.error}</p></td></tr>`;
            showToast(`❌ Erro: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao consultar NFS-e:', error);
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #e74c3c;"><div style="font-size: 48px;">❌</div><h3>Erro de Conexão</h3><p>Não foi possível conectar ao servidor.</p></td></tr>';
        showToast('❌ Erro ao consultar NFS-e', 'error');
    }
};

// Buscar NFS-e via API SOAP (download das prefeituras)
window.buscarNFSeAPI = async function() {
    const dataInicial = document.getElementById('nfse-data-inicial').value;
    const dataFinal = document.getElementById('nfse-data-final').value;
    const codigoMunicipio = document.getElementById('nfse-municipio').value;
    
    // Datas são opcionais — o backend detecta automaticamente o período ideal
    const periodoMsg = (dataInicial && dataFinal)
        ? `período ${dataInicial} a ${dataFinal}`
        : 'período automático (incremental ou histórico completo)';
    
    console.log('⬇️ Baixando NFS-e:', { dataInicial, dataFinal, codigoMunicipio, periodoMsg });
    
    // Confirmar ação (pode demorar)
    if (!confirm(`⚠️ Esta operação pode levar alguns minutos.\n\n📡 Será feita busca de NFS-e — ${periodoMsg}.\n\n💾 As notas serão salvas no banco de dados.\n\nDeseja continuar?`)) {
        return;
    }
    
    // Obter método de busca selecionado
    const metodoSelect = document.getElementById('nfse-metodo');
    const metodo = metodoSelect ? metodoSelect.value : 'ambiente_nacional';
    
    // Mostrar loading
    const loading = document.getElementById('loading-nfse');
    loading.style.display = 'block';
    
    const tbody = document.getElementById('tbody-nfse');
    
    // Mensagem de loading baseada no método
    const periodoLabel = (dataInicial && dataFinal)
        ? `${dataInicial} a ${dataFinal}`
        : '(período automático)';
    let loadingMsg = '';
    if (metodo === 'ambiente_nacional') {
        loadingMsg = `<tr><td colspan="8" style="text-align: center; padding: 40px;"><div style="font-size: 48px;">🌐</div><p style="font-size: 18px; font-weight: bold; color: #27ae60;">Buscando via Ambiente Nacional...</p><p style="color: #856404; font-size: 14px;">API REST oficial do governo federal</p><p style="color: #7f8c8d; font-size: 13px;">Período: ${periodoLabel} • Se for a primeira busca, pode demorar mais (histórico completo)</p></td></tr>`;
    } else {
        loadingMsg = `<tr><td colspan="8" style="text-align: center; padding: 40px;"><div style="font-size: 48px;">📡</div><p style="font-size: 18px; font-weight: bold;">Buscando via SOAP Municipal...</p><p style="color: #856404; font-size: 14px;">Período: ${periodoLabel}</p><p style="color: #7f8c8d; font-size: 13px;">Isso pode levar vários minutos dependendo da quantidade de notas.</p></td></tr>`;
    }
    tbody.innerHTML = loadingMsg;
    
    try {
        const body = {
            metodo: metodo
        };
        // Só envia datas se o usuário preencheu explicitamente
        if (dataInicial) body.data_inicial = dataInicial;
        if (dataFinal)   body.data_final   = dataFinal;
        
        if (codigoMunicipio) {
            body.codigos_municipios = [codigoMunicipio];
        }
        
        const response = await fetch('/api/nfse/buscar', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        loading.style.display = 'none';
        
        // Tratar erros HTTP
        if (!response.ok) {
            let errorMsg = 'Erro desconhecido';
            let errorDetail = '';
            
            if (response.status === 502) {
                errorMsg = '⏱️ Busca demorou muito';
                errorDetail = 'A busca excedeu o tempo limite do servidor. Tente novamente — a busca incremental continuará de onde parou.';
            } else if (response.status === 504) {
                errorMsg = '⏱️ Timeout na busca';
                errorDetail = 'A busca está demorando muito. Tente reduzir o período ou número de municípios.';
            } else if (response.status === 400) {
                try {
                    const data = await response.json();
                    errorMsg = data.error || 'Requisição inválida';
                    if (errorMsg.toLowerCase().includes('cnpj')) {
                        errorDetail = '<strong>💡 Solução:</strong> Acesse <a href="#" onclick="showSection(\'empresa\');return false;" style="color:#e74c3c;">Dados da Empresa</a> e preencha o CNPJ antes de buscar NFS-e.';
                    }
                } catch {
                    errorMsg = 'Requisição inválida';
                }
            } else {
                try {
                    const data = await response.json();
                    errorMsg = data.error || `Erro ${response.status}`;
                } catch {
                    errorMsg = `Erro ${response.status}`;
                }
            }
            
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 40px; color: #e74c3c;"><div style="font-size: 48px;">❌</div><h3>${errorMsg}</h3><p>${errorDetail}</p></td></tr>`;
            showToast(`❌ ${errorMsg}`, 'error', 8000);
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            const resultado = data.resultado;
            
            showToast(`✅ Busca concluída!\n📄 ${resultado.total_nfse} NFS-e encontradas\n💾 ${resultado.nfse_novas} novas, ${resultado.nfse_atualizadas} atualizadas`, 'success', 5000);
            
            // Atualizar tabela com consulta local
            await window.consultarNFSeLocal();
        } else {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 40px; color: #e74c3c;"><div style="font-size: 48px;">❌</div><h3>Erro ao Buscar NFS-e</h3><p>${data.error}</p></td></tr>`;
            showToast(`❌ Erro: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao buscar NFS-e via API:', error);
        loading.style.display = 'none';
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #e74c3c;"><div style="font-size: 48px;">❌</div><h3>Erro de Conexão</h3><p>Não foi possível conectar ao servidor.</p><p style="font-size: 12px; color: #7f8c8d; margin-top: 10px;">Tente novamente. A busca incremental continuará de onde parou.</p></td></tr>';
        showToast('❌ Erro ao buscar NFS-e', 'error');
    }
};

// Exibir NFS-e na tabela
window.exibirNFSe = function(nfses) {
    const tbody = document.getElementById('tbody-nfse');
    
    if (nfses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 60px; color: #7f8c8d;"><div style="font-size: 48px; margin-bottom: 20px;">📄</div><h3 style="color: #34495e;">Nenhuma NFS-e encontrada</h3><p style="font-size: 14px;">Tente ajustar o período ou buscar via API SOAP.</p></td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    
    nfses.forEach(nfse => {
        const tr = document.createElement('tr');
        
        // Formatações
        let dataEmissao = '-';
        if (nfse.data_emissao) {
            try {
                // Remove parte do horário se existir e pega só a data
                const dataStr = nfse.data_emissao.split('T')[0];
                const [ano, mes, dia] = dataStr.split('-');
                dataEmissao = `${dia}/${mes}/${ano}`;
            } catch (e) {
                dataEmissao = '-';
            }
        }
        const valorServico = nfse.valor_servico ? parseFloat(nfse.valor_servico).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : 'R$ 0,00';
        const valorIss = nfse.valor_iss ? parseFloat(nfse.valor_iss).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : 'R$ 0,00';
        const valorLiquido = nfse.valor_liquido ? parseFloat(nfse.valor_liquido).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : 'R$ 0,00';
        
        // Badge situação
        let badgeSituacao = '';
        switch (nfse.situacao) {
            case 'NORMAL':
                badgeSituacao = '<span style="background: #27ae60; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">✅ NORMAL</span>';
                break;
            case 'CANCELADA':
                badgeSituacao = '<span style="background: #e74c3c; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">❌ CANCELADA</span>';
                break;
            case 'SUBSTITUIDA':
                badgeSituacao = '<span style="background: #f39c12; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">🔄 SUBSTITUÍDA</span>';
                break;
            default:
                badgeSituacao = `<span style="background: #95a5a6; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">${nfse.situacao || '?'}</span>`;
        }
        
        tr.innerHTML = `
            <td style="text-align: center; font-weight: bold;">${nfse.numero_nfse || '-'}</td>
            <td style="text-align: center;">${dataEmissao}</td>
            <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${nfse.razao_social_tomador || '-'}">${nfse.razao_social_tomador || '-'}</td>
            <td style="text-align: center;">${nfse.nome_municipio || '-'}/${nfse.uf || '-'}</td>
            <td style="text-align: right; font-weight: bold; color: #27ae60;">${valorServico}</td>
            <td style="text-align: right; font-weight: bold; color: #3498db;">${valorIss}</td>
            <td style="text-align: right; font-weight: bold; color: #8e44ad;">${valorLiquido}</td>
            <td style="text-align: center;">${badgeSituacao}</td>
            <td style="text-align: center; white-space: nowrap;">
                <button onclick="verDetalhesNFSe(${nfse.id})" class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px; background: #3498db;" title="Ver Detalhes">👁️</button>
                <button onclick="gerarPdfNFSe(${nfse.id})" class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px; background: #e74c3c; margin-left: 2px;" title="Gerar PDF">📄</button>
                <button onclick="excluirNFSe(${nfse.id})" style="background: none; border: none; cursor: pointer; font-size: 16px; margin-left: 2px;" title="Excluir NFS-e">🗑️</button>
            </td>
        `;
        
        tbody.appendChild(tr);
    });
};

// Exibir NFS-e com paginação no frontend
window.exibirNFSePaginado = function() {
    if (!window.nfsesCarregadas || window.nfsesCarregadas.length === 0) {
        window.exibirNFSe([]);
        document.getElementById('nfse-paginacao').style.display = 'none';
        return;
    }
    
    const { paginaAtual, registrosPorPagina } = window.nfsePaginacao;
    const inicio = (paginaAtual - 1) * registrosPorPagina;
    const fim = inicio + registrosPorPagina;
    const nfsesPagina = window.nfsesCarregadas.slice(inicio, fim);
    
    window.exibirNFSe(nfsesPagina);
    
    // Mostrar controles de paginação se houver mais de uma página
    if (window.nfsePaginacao.totalPaginas > 1) {
        document.getElementById('nfse-paginacao').style.display = 'block';
    } else {
        document.getElementById('nfse-paginacao').style.display = 'none';
    }
};

// Atualizar controles de paginação
window.atualizarControlesPaginacao = function() {
    if (!window.nfsePaginacao) return;
    
    const { paginaAtual, totalPaginas, totalRegistros, registrosPorPagina } = window.nfsePaginacao;
    
    // Atualizar texto
    const inicio = (paginaAtual - 1) * registrosPorPagina + 1;
    const fim = Math.min(paginaAtual * registrosPorPagina, totalRegistros);
    document.getElementById('nfse-info-pagina').textContent = 
        `Página ${paginaAtual} de ${totalPaginas} (${inicio}-${fim} de ${totalRegistros})`;
    
    // Habilitar/desabilitar botões
    document.getElementById('nfse-primeira-pagina').disabled = paginaAtual === 1;
    document.getElementById('nfse-pagina-anterior').disabled = paginaAtual === 1;
    document.getElementById('nfse-proxima-pagina').disabled = paginaAtual === totalPaginas;
    document.getElementById('nfse-ultima-pagina').disabled = paginaAtual === totalPaginas;
};

// Mudar página (relativo)
window.mudarPaginaNFSe = function(direcao) {
    if (!window.nfsePaginacao) return;
    
    const novaPagina = window.nfsePaginacao.paginaAtual + direcao;
    if (novaPagina >= 1 && novaPagina <= window.nfsePaginacao.totalPaginas) {
        window.nfsePaginacao.paginaAtual = novaPagina;
        window.exibirNFSePaginado();
        window.atualizarControlesPaginacao();
    }
};

// Ir para página específica
window.irPaginaNFSe = function(pagina) {
    if (!window.nfsePaginacao) return;
    
    if (pagina === 'ultima') {
        pagina = window.nfsePaginacao.totalPaginas;
    }
    
    if (pagina >= 1 && pagina <= window.nfsePaginacao.totalPaginas) {
        window.nfsePaginacao.paginaAtual = pagina;
        window.exibirNFSePaginado();
        window.atualizarControlesPaginacao();
    }
};

// Atualizar registros por página
window.atualizarRegistrosPorPagina = function() {
    if (!window.nfsePaginacao || !window.nfsesCarregadas) return;
    
    window.nfsePaginacao.registrosPorPagina = parseInt(document.getElementById('nfse-registros-por-pagina').value) || 100;
    window.nfsePaginacao.totalPaginas = Math.ceil(window.nfsePaginacao.totalRegistros / window.nfsePaginacao.registrosPorPagina);
    window.nfsePaginacao.paginaAtual = 1; // Resetar para primeira página
    
    window.exibirNFSePaginado();
    window.atualizarControlesPaginacao();
};

// Atualizar cards de resumo
window.atualizarResumoNFSe = function(nfses) {
    const totalNotas = nfses.length;
    const valorTotal = nfses.reduce((sum, nfse) => sum + (parseFloat(nfse.valor_servico) || 0), 0);
    const issTotal = nfses.reduce((sum, nfse) => sum + (parseFloat(nfse.valor_iss) || 0), 0);
    const municipiosUnicos = [...new Set(nfses.map(nfse => nfse.codigo_municipio))].length;
    
    document.getElementById('total-nfse').textContent = totalNotas;
    document.getElementById('valor-total-nfse').textContent = valorTotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    document.getElementById('iss-total-nfse').textContent = issTotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    document.getElementById('municipios-nfse').textContent = municipiosUnicos;
};

// Diagnóstico de omissões
window.diagnosticarOmissoesNFSe = async function() {
    const dataInicial = document.getElementById('nfse-data-inicial').value;
    const dataFinal = document.getElementById('nfse-data-final').value;
    const codigoMunicipio = document.getElementById('nfse-municipio').value;
    
    if (!dataInicial || !dataFinal) {
        showToast('⚠️ Selecione o período (data inicial e final)', 'warning');
        return;
    }
    
    console.log('🔍 Executando diagnóstico de NFS-e...');
    
    try {
        const body = {
            data_inicial: dataInicial,
            data_final: dataFinal
        };
        
        if (codigoMunicipio) {
            body.codigo_municipio = codigoMunicipio;
        }
        
        const response = await fetch('/api/nfse/diagnostico', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (data.success) {
            let mensagem = `📊 DIAGNÓSTICO DE NFS-e\n\n`;
            mensagem += `📦 Total no Banco: ${data.total_banco} notas\n`;
            mensagem += `✅ Exibidas (NORMAL): ${data.total_interface} notas\n`;
            
            if (data.total_omitidas > 0) {
                mensagem += `\n⚠️ OMITIDAS: ${data.total_omitidas} notas\n\n`;
                mensagem += `📋 Detalhamento por situação:\n`;
                
                data.por_situacao.forEach(sit => {
                    const valor = sit.valor_total ? sit.valor_total.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'}) : 'R$ 0,00';
                    mensagem += `   ${sit.situacao}: ${sit.total} notas (${valor})\n`;
                });
                
                if (data.exemplos_omitidas.length > 0) {
                    mensagem += `\n🔍 Exemplos de notas omitidas:\n`;
                    data.exemplos_omitidas.slice(0, 5).forEach(nota => {
                        const valor = parseFloat(nota.valor_servico).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
                        mensagem += `   • ${nota.numero_nfse} - ${nota.data_emissao} - ${valor} - ${nota.situacao}\n`;
                    });
                }
                
                mensagem += `\nℹ️ A interface só exibe notas com situação "NORMAL".\n`;
                mensagem += `Para ver todas as notas (incluindo CANCELADAS/SUBSTITUÍDAS),\n`;
                mensagem += `será necessário remover o filtro de situação no código.`;
                
                alert(mensagem);
                showToast(`⚠️ ${data.total_omitidas} notas omitidas (${data.total_interface} exibidas de ${data.total_banco} no banco)`, 'warning');
            } else {
                mensagem += `\n✅ Não há omissões! Todas as ${data.total_interface} notas são NORMAIS.`;
                alert(mensagem);
                showToast('✅ Sem omissões - todas as notas estão sendo exibidas', 'success');
            }
        } else {
            showToast(`❌ Erro: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao executar diagnóstico:', error);
        showToast('❌ Erro ao executar diagnóstico', 'error');
    }
};

// Controle de ordenação
window.nfseOrdenacao = {
    campo: null,
    ascendente: true
};

// Ordenar NFS-e por campo
window.ordenarNFSe = function(campo) {
    // Se clicar no mesmo campo, inverte a ordem
    if (window.nfseOrdenacao.campo === campo) {
        window.nfseOrdenacao.ascendente = !window.nfseOrdenacao.ascendente;
    } else {
        // Novo campo, sempre começa ascendente
        window.nfseOrdenacao.campo = campo;
        window.nfseOrdenacao.ascendente = true;
    }
    
    // Limpar todos os indicadores de ordenação
    ['numero_nfse', 'data_emissao', 'razao_social_tomador', 'nome_municipio', 'valor_servico', 'valor_iss', 'valor_liquido', 'situacao'].forEach(c => {
        const el = document.getElementById(`sort-${c}`);
        if (el) el.textContent = '';
    });
    
    // Adicionar indicador no campo atual
    const indicador = document.getElementById(`sort-${campo}`);
    if (indicador) {
        indicador.textContent = window.nfseOrdenacao.ascendente ? ' ▲' : ' ▼';
    }
    
    // Ordenar o array
    window.nfsesCarregadas.sort((a, b) => {
        let valorA = a[campo];
        let valorB = b[campo];
        
        // Tratar valores nulos
        if (valorA === null || valorA === undefined) valorA = '';
        if (valorB === null || valorB === undefined) valorB = '';
        
        // Ordenação numérica para valores
        if (campo === 'valor_servico' || campo === 'valor_iss' || campo === 'valor_liquido') {
            valorA = parseFloat(valorA) || 0;
            valorB = parseFloat(valorB) || 0;
        }
        
        // Ordenação de data
        if (campo === 'data_emissao') {
            valorA = new Date(valorA || '1900-01-01');
            valorB = new Date(valorB || '1900-01-01');
        }
        
        // Comparação
        let comparacao = 0;
        if (valorA < valorB) comparacao = -1;
        if (valorA > valorB) comparacao = 1;
        
        return window.nfseOrdenacao.ascendente ? comparacao : -comparacao;
    });
    
    // Atualizar exibição com paginação
    window.nfsePaginacao.paginaAtual = 1; // Resetar para primeira página após ordenar
    window.exibirNFSePaginado();
    window.atualizarControlesPaginacao();
    
    console.log(`📊 Ordenado por ${campo} (${window.nfseOrdenacao.ascendente ? 'crescente' : 'decrescente'})`);
};

// Exportar NFS-e para Excel (CSV)
window.exportarNFSeExcel = async function() {
    const dataInicial = document.getElementById('nfse-data-inicial').value;
    const dataFinal = document.getElementById('nfse-data-final').value;
    
    if (!dataInicial || !dataFinal) {
        showToast('⚠️ Selecione o período para exportação', 'warning');
        return;
    }
    
    if (window.nfsesCarregadas.length === 0) {
        showToast('⚠️ Nenhuma NFS-e para exportar. Faça uma consulta primeiro.', 'warning');
        return;
    }
    
    console.log('📊 Exportando NFS-e para Excel/CSV...');
    showToast('⏳ Gerando arquivo Excel...', 'info');
    
    try {
        const response = await fetch('/api/nfse/export/excel', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                data_inicial: dataInicial,
                data_final: dataFinal
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `nfse_${dataInicial}_${dataFinal}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            
            showToast('✅ Arquivo CSV baixado com sucesso!', 'success');
        } else {
            const data = await response.json();
            showToast(`❌ Erro: ${data.error || 'Erro desconhecido'}`, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao exportar NFS-e:', error);
        showToast('❌ Erro ao exportar NFS-e', 'error');
    }
};

// Exportar XMLs em arquivo ZIP
window.exportarNFSeXMLs = async function() {
    const dataInicial = document.getElementById('nfse-data-inicial').value;
    const dataFinal = document.getElementById('nfse-data-final').value;
    
    if (!dataInicial || !dataFinal) {
        showToast('⚠️ Selecione o período para exportação', 'warning');
        return;
    }
    
    if (window.nfsesCarregadas.length === 0) {
        showToast('⚠️ Nenhuma NFS-e para exportar. Faça uma consulta primeiro.', 'warning');
        return;
    }
    
    console.log('📄 Exportando XMLs das NFS-e...');
    showToast('⏳ Gerando arquivo ZIP com XMLs...', 'info');
    
    try {
        const response = await fetch('/api/nfse/export/xml', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                data_inicial: dataInicial,
                data_final: dataFinal
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `nfse_xmls_${dataInicial}_${dataFinal}.zip`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            
            showToast('✅ Arquivo ZIP com XMLs baixado com sucesso!', 'success');
        } else {
            const data = await response.json();
            showToast(`❌ Erro: ${data.error || 'Erro desconhecido'}`, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao exportar XMLs:', error);
        showToast('❌ Erro ao exportar XMLs', 'error');
    }
};

// Excluir NFS-e (arquivo XML,PDF e registro do banco)
window.excluirNFSe = async function(nfseId) {
    if (!confirm('⚠️ ATENÇÃO!\n\nEsta ação irá excluir permanentemente:\n• O registro da NFS-e no banco de dados\n• O arquivo XML salvo\n• O arquivo PDF salvo\n\nDeseja realmente excluir esta NFS-e?')) {
        return;
    }
    
    console.log(`🗑️ Excluindo NFS-e ID: ${nfseId}`);
    showToast('⏳ Excluindo NFS-e...', 'info');
    
    try {
        const response = await fetch(`/api/nfse/${nfseId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('✅ NFS-e excluída com sucesso!', 'success');
            
            // Atualizar lista de NFS-e
            await window.consultarNFSeLocal();
        } else {
            showToast(`❌ Erro: ${data.error || 'Erro desconhecido'}`, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao excluir NFS-e:', error);
        showToast('❌ Erro ao excluir NFS-e', 'error');
    }
};

// Apagar TODAS as NFS-e do período selecionado
window.apagarTodasNFSe = async function() {
    // Pegar filtros atuais
    const dataInicial = document.getElementById('nfse-data-inicial').value;
    const dataFinal = document.getElementById('nfse-data-final').value;
    const municipioCodigo = document.getElementById('nfse-municipio').value;
    
    if (!dataInicial || !dataFinal) {
        showToast('⚠️ Selecione o período (Data Inicial e Final) antes de apagar', 'warning');
        return;
    }
    
    // Confirmação tripla com aviso severo
    const msg1 = `⚠️⚠️⚠️ ATENÇÃO CRÍTICA! ⚠️⚠️⚠️\n\nVocê está prestes a APAGAR TODAS as NFS-e:\n\n📅 Período: ${dataInicial} a ${dataFinal}\n🏙️ Município: ${municipioCodigo || 'TODOS os municípios'}\n\nEsta ação irá:\n❌ EXCLUIR TODOS os registros no banco de dados\n❌ APAGAR TODOS os arquivos XML\n❌ APAGAR TODOS os arquivos PDF\n\n⚠️ ESTA AÇÃO NÃO PODE SER DESFEITA!\n\nDeseja continuar?`;
    
    if (!confirm(msg1)) {
        return;
    }
    
    // Segunda confirmação
    const msg2 = `⚠️ SEGUNDA CONFIRMAÇÃO\n\nVocê tem ABSOLUTA CERTEZA que deseja apagar TODAS as NFS-e do período selecionado?\n\nEsta é sua ÚLTIMA CHANCE de cancelar!`;
    
    if (!confirm(msg2)) {
        return;
    }
    
    // Terceira confirmação - digitar "APAGAR TUDO"
    const confirmacao = prompt('⚠️ CONFIRMAÇÃO FINAL\n\nPara confirmar a exclusão permanente, digite exatamente:\nAPAGAR TUDO');
    
    if (confirmacao !== 'APAGAR TUDO') {
        showToast('❌ Operação cancelada - texto de confirmação incorreto', 'info');
        return;
    }
    
    console.log(`🗑️ Apagando TODAS as NFS-e do período: ${dataInicial} a ${dataFinal}`);
    showToast('⏳ Apagando todas as NFS-e... Aguarde!', 'info');
    
    try {
        const params = new URLSearchParams({
            data_inicial: dataInicial,
            data_final: dataFinal
        });
        
        if (municipioCodigo) {
            params.append('codigo_municipio', municipioCodigo);
        }
        
        const response = await fetch(`/api/nfse/all?${params}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const total = data.total_excluidas || 0;
            const arquivos = data.total_arquivos_excluidos || 0;
            showToast(`✅ ${total} NFS-e(s) excluídas com sucesso! (${arquivos} arquivos removidos)`, 'success');
            
            // Atualizar lista de NFS-e
            await window.consultarNFSeLocal();
        } else {
            showToast(`❌ Erro: ${data.error || 'Erro desconhecido'}`, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao apagar todas as NFS-e:', error);
        showToast('❌ Erro ao apagar NFS-e', 'error');
    }
};

// Mostrar configuração de municípios (agora inline na aba NFS-e do fiscal)
window.mostrarConfigMunicipiosNFSe = async function() {
    // Garantir que a seção fiscal e a aba NFS-e estejam abertas
    if (typeof window.showSection === 'function') window.showSection('fiscal');
    setTimeout(async function() {
        if (typeof window.showFiscalTab === 'function') window.showFiscalTab('nfse');
        // Aguardar renderização e rolar até a config
        setTimeout(function() {
            const configDiv = document.getElementById('nfse-municipios-config');
            if (configDiv) configDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 150);
        await window.carregarListaMunicipiosNFSe();
    }, 100);
};

// Fechar configuração de municípios (legacy - no-op pois agora é inline)
window.fecharModalConfigMunicipios = function() {
    const form = document.getElementById('form-novo-municipio-nfse');
    if (form) form.reset();
};

// Carregar lista de municípios configurados na tabela do modal
window.carregarListaMunicipiosNFSe = async function() {
    try {
        const response = await fetch('/api/nfse/config', {
            method: 'GET',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const municipios = data.configs || [];
            const tbody = document.getElementById('tbody-municipios-nfse');
            
            if (municipios.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px; color: #999;">Nenhum município configurado.</td></tr>';
                return;
            }
            
            tbody.innerHTML = '';
            
            municipios.forEach(config => {
                const tr = document.createElement('tr');
                
                const statusBadge = config.ativo 
                    ? '<span style="background: #27ae60; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">✅ ATIVO</span>'
                    : '<span style="background: #95a5a6; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">⏸️ INATIVO</span>';
                
                tr.innerHTML = `
                    <td>${config.nome_municipio || '-'}</td>
                    <td style="text-align: center;">${config.uf || '-'}</td>
                    <td style="text-align: center;">${config.codigo_municipio || '-'}</td>
                    <td style="text-align: center;">${config.provedor || '-'}</td>
                    <td style="text-align: center;">${statusBadge}</td>
                    <td style="text-align: center;">
                        <button onclick="editarMunicipioNFSe(${config.id})" style="background: none; border: none; cursor: pointer; font-size: 16px; margin-right: 5px;" title="Editar">✏️</button>
                        <button onclick="excluirMunicipioNFSe(${config.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
                    </td>
                `;
                
                tbody.appendChild(tr);
            });
        } else {
            console.error('❌ Erro ao carregar lista de municípios:', data.error);
        }
    } catch (error) {
        console.error('❌ Erro ao carregar lista de municípios:', error);
    }
};

// Salvar novo município
window.salvarMunicipioNFSe = async function(event) {
    event.preventDefault();
    
    const codigoMunicipio = document.getElementById('config-codigo-municipio').value;
    const urlCustomizada = document.getElementById('config-url-customizada').value;
    
    // Validação específica para Belo Horizonte (código 3106200)
    if (codigoMunicipio === '3106200' && !urlCustomizada) {
        if (!confirm(
            '⚠️ ATENÇÃO: Belo Horizonte\n\n' +
            'A URL do webservice de BH não é conhecida automaticamente.\n\n' +
            '❌ Sem a URL customizada, as buscas de NFS-e FALHARÃO.\n\n' +
            '📋 Você precisa:\n' +
            '1. Acessar o site da prefeitura de BH\n' +
            '2. Obter a URL correta do webservice\n' +
            '3. Preencher o campo "URL Customizada"\n\n' +
            'Deseja salvar mesmo assim? (NÃO RECOMENDADO)'
        )) {
            return;
        }
    }
    
    const novoMunicipio = {
        cnpj_cpf: document.getElementById('config-cnpj').value.replace(/\D/g, ''),
        codigo_municipio: document.getElementById('config-codigo-municipio').value,
        nome_municipio: document.getElementById('config-nome-municipio').value,
        uf: document.getElementById('config-uf').value,
        inscricao_municipal: document.getElementById('config-inscricao-municipal').value,
        provedor: document.getElementById('config-provedor').value || null,
        url_customizada: document.getElementById('config-url-customizada').value || null
    };
    
    // Verificar se está editando ou criando novo
    const configIdEditando = window.nfseConfigIdEditando;
    const isEdicao = configIdEditando !== undefined && configIdEditando !== null;
    
    console.log(isEdicao ? '✏️ Atualizando município:' : '💾 Salvando novo município:', novoMunicipio);
    showToast(isEdicao ? '⏳ Atualizando configuração...' : '⏳ Salvando configuração...', 'info');
    
    try {
        const url = isEdicao ? `/api/nfse/config/${configIdEditando}` : '/api/nfse/config';
        const method = isEdicao ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(novoMunicipio)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(isEdicao ? '✅ Município atualizado com sucesso!' : '✅ Município configurado com sucesso!', 'success');
            document.getElementById('form-novo-municipio-nfse').reset();
            
            // Limpar modo de edição
            window.nfseConfigIdEditando = null;
            
            // Restaurar aparência normal dos campos
            ['config-cnpj', 'config-codigo-municipio', 'config-nome-municipio', 'config-inscricao-municipal'].forEach(id => {
                const input = document.getElementById(id);
                if (input) {
                    input.style.background = '';
                    input.style.borderColor = '';
                    input.style.borderWidth = '';
                    input.readOnly = false;
                }
            });
            
            const ufSelect = document.getElementById('config-uf');
            if (ufSelect) {
                ufSelect.style.background = '';
                ufSelect.disabled = false;
            }
            
            const provedorSelect = document.getElementById('config-provedor');
            if (provedorSelect) provedorSelect.style.background = '';
            
            await window.carregarListaMunicipiosNFSe();
            await window.carregarMunicipiosNFSe(); // Atualizar dropdown na seção principal
        } else {
            showToast(`❌ Erro: ${data.error || 'Erro desconhecido'}`, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao salvar município:', error);
        showToast('❌ Erro ao salvar município', 'error');
    }
};

// Editar município existente
window.editarMunicipioNFSe = async function(configId) {
    console.log('✏️ Editando município ID:', configId);
    showToast('⏳ Carregando dados...', 'info');
    
    try {
        // Buscar dados da config
        const response = await fetch('/api/nfse/config', {
            method: 'GET',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const config = data.configs.find(c => c.id === configId);
            
            if (!config) {
                showToast('❌ Configuração não encontrada', 'error');
                return;
            }
            
            // Armazenar ID da config sendo editada
            window.nfseConfigIdEditando = configId;
            
            // Preencher formulário com dados existentes
            document.getElementById('config-cnpj').value = config.cnpj_cpf || '';
            document.getElementById('config-codigo-municipio').value = config.codigo_municipio || '';
            document.getElementById('config-nome-municipio').value = config.nome_municipio || '';
            document.getElementById('config-uf').value = config.uf || '';
            document.getElementById('config-inscricao-municipal').value = config.inscricao_municipal || '';
            document.getElementById('config-provedor').value = config.provedor || '';
            document.getElementById('config-url-customizada').value = config.url_customizada || '';
            
            // Destacar formulário
            const form = document.getElementById('form-novo-municipio-nfse');
            if (form) {
                form.style.background = '#fff3cd';
                form.style.border = '2px solid #ffc107';
                form.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            
            // Focar no campo de inscrição municipal (geralmente o que precisa ser preenchido)
            const inscricaoInput = document.getElementById('config-inscricao-municipal');
            if (inscricaoInput) {
                inscricaoInput.focus();
                inscricaoInput.select();
            }
            
            showToast('✏️ Editando município. Altere os dados e clique em Salvar.', 'info', 4000);
        }
    } catch (error) {
        console.error('❌ Erro ao carregar dados do município:', error);
        showToast('❌ Erro ao carregar dados', 'error');
    }
};

// Excluir município
window.excluirMunicipioNFSe = async function(configId) {
    if (!confirm('⚠️ Deseja excluir esta configuração de município?\n\n⚠️ As NFS-e já baixadas não serão excluídas, apenas a configuração será removida.')) {
        return;
    }
    
    console.log('🗑️ Excluindo município ID:', configId);
    showToast('⏳ Excluindo...', 'info');
    
    try {
        const response = await fetch(`/api/nfse/config/${configId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('✅ Configuração excluída com sucesso!', 'success');
            await window.carregarListaMunicipiosNFSe();
            await window.carregarMunicipiosNFSe();
        } else {
            showToast(`❌ Erro: ${data.error || 'Erro desconhecido'}`, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao excluir município:', error);
        showToast('❌ Erro ao excluir município', 'error');
    }
};

// Ver detalhes de NFS-e
window.verDetalhesNFSe = async function(nfseId) {
    console.log('👁️ Carregando detalhes da NFS-e ID:', nfseId);
    
    document.getElementById('modal-detalhes-nfse').style.display = 'block';
    document.getElementById('detalhes-nfse-content').innerHTML = '<p style="text-align: center; color: #999; padding: 30px;">⏳ Carregando detalhes...</p>';
    
    try {
        const response = await fetch(`/api/nfse/${nfseId}`, {
            method: 'GET',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const nfse = data.nfse;
            
            // Preencher dados
            document.getElementById('det-numero').textContent = nfse.numero_nfse || '-';
            document.getElementById('det-codigo-verificacao').textContent = nfse.codigo_verificacao || '-';
            
            // Formatar data de emissão
            let dataEmissao = '-';
            if (nfse.data_emissao) {
                try {
                    const dataStr = nfse.data_emissao.split('T')[0];
                    const [ano, mes, dia] = dataStr.split('-');
                    dataEmissao = `${dia}/${mes}/${ano}`;
                } catch (e) {
                    dataEmissao = '-';
                }
            }
            document.getElementById('det-data-emissao').textContent = dataEmissao;
            
            let situacaoHtml = '';
            switch (nfse.situacao) {
                case 'NORMAL':
                    situacaoHtml = '<span style="background: #27ae60; color: white; padding: 6px 12px; border-radius: 12px; font-weight: bold;">✅ NORMAL</span>';
                    break;
                case 'CANCELADA':
                    situacaoHtml = '<span style="background: #e74c3c; color: white; padding: 6px 12px; border-radius: 12px; font-weight: bold;">❌ CANCELADA</span>';
                    break;
                case 'SUBSTITUIDA':
                    situacaoHtml = '<span style="background: #f39c12; color: white; padding: 6px 12px; border-radius: 12px; font-weight: bold;">🔄 SUBSTITUÍDA</span>';
                    break;
                default:
                    situacaoHtml = `<span style="background: #95a5a6; color: white; padding: 6px 12px; border-radius: 12px; font-weight: bold;">${nfse.situacao || '?'}</span>`;
            }
            document.getElementById('det-situacao').innerHTML = situacaoHtml;
            
            document.getElementById('det-cnpj-prestador').textContent = nfse.cnpj_prestador || '-';
            document.getElementById('det-cnpj-tomador').textContent = nfse.cnpj_tomador || '-';
            document.getElementById('det-razao-social-tomador').textContent = nfse.razao_social_tomador || '-';
            
            document.getElementById('det-valor-servico').textContent = nfse.valor_servico ? parseFloat(nfse.valor_servico).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : 'R$ 0,00';
            document.getElementById('det-valor-deducoes').textContent = nfse.valor_deducoes ? parseFloat(nfse.valor_deducoes).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : 'R$ 0,00';
            document.getElementById('det-valor-iss').textContent = nfse.valor_iss ? parseFloat(nfse.valor_iss).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : 'R$ 0,00';
            
            document.getElementById('det-discriminacao').textContent = nfse.discriminacao || '-';
            
            // XML (formatado)
            document.getElementById('det-xml-content').textContent = nfse.xml_content || '(XML não disponível)';
            
            // Mostrar aba de dados por padrão
            window.mostrarAbaDetalhesNFSe('dados');
        } else {
            document.getElementById('detalhes-nfse-content').innerHTML = `<p style="text-align: center; color: #e74c3c; padding: 30px;">❌ Erro: ${data.error}</p>`;
        }
    } catch (error) {
        console.error('❌ Erro ao carregar detalhes:', error);
        document.getElementById('detalhes-nfse-content').innerHTML = '<p style="text-align: center; color: #e74c3c; padding: 30px;">❌ Erro ao carregar detalhes</p>';
    }
};

// Fechar modal de detalhes
window.fecharModalDetalhesNFSe = function() {
    document.getElementById('modal-detalhes-nfse').style.display = 'none';
};

// Alternar abas no modal de detalhes
window.mostrarAbaDetalhesNFSe = function(aba) {
    const tabDados = document.getElementById('tab-dados-nfse');
    const tabXml = document.getElementById('tab-xml-nfse');
    const conteudoDados = document.getElementById('conteudo-dados-nfse');
    const conteudoXml = document.getElementById('conteudo-xml-nfse');
    
    if (aba === 'dados') {
        tabDados.style.background = '#3498db';
        tabXml.style.background = '#95a5a6';
        conteudoDados.style.display = 'block';
        conteudoXml.style.display = 'none';
    } else {
        tabDados.style.background = '#95a5a6';
        tabXml.style.background = '#3498db';
        conteudoDados.style.display = 'none';
        conteudoXml.style.display = 'block';
    }
};

// Copiar XML para área de transferência
window.copiarXMLNFSe = async function() {
    const xmlContent = document.getElementById('det-xml-content').textContent;
    
    try {
        await navigator.clipboard.writeText(xmlContent);
        showToast('✅ XML copiado para área de transferência!', 'success');
    } catch (error) {
        console.error('❌ Erro ao copiar XML:', error);
        showToast('❌ Erro ao copiar XML', 'error');
    }
};

// ============================================================================
// CERTIFICADO DIGITAL A1
// ============================================================================

// Carregar status do certificado ativo
window.carregarCertificadoNFSe = async function() {
    const container = document.getElementById('cert-status');
    if (!container) return;
    
    try {
        const response = await fetch('/api/nfse/certificado', {
            method: 'GET',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success && data.certificado) {
            const cert = data.certificado;
            const validadeFim = cert.validade_fim ? new Date(cert.validade_fim) : null;
            const hoje = new Date();
            const expirado = validadeFim && validadeFim < hoje;
            const diasRestantes = validadeFim ? Math.ceil((validadeFim - hoje) / (1000 * 60 * 60 * 24)) : 0;
            
            let statusBadge = '';
            if (expirado) {
                statusBadge = '<span style="background: #e74c3c; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">❌ EXPIRADO</span>';
            } else if (diasRestantes <= 30) {
                statusBadge = `<span style="background: #f39c12; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">⚠️ EXPIRA EM ${diasRestantes} DIAS</span>`;
            } else {
                statusBadge = '<span style="background: #27ae60; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">✅ VÁLIDO</span>';
            }
            
            const cnpjFmt = cert.cnpj_extraido && cert.cnpj_extraido.length === 14 
                ? `${cert.cnpj_extraido.substr(0,2)}.${cert.cnpj_extraido.substr(2,3)}.${cert.cnpj_extraido.substr(5,3)}/${cert.cnpj_extraido.substr(8,4)}-${cert.cnpj_extraido.substr(12,2)}`
                : cert.cnpj_extraido || '-';
            
            const validadeFormatada = validadeFim ? validadeFim.toLocaleDateString('pt-BR') : '-';
            const municipioInfo = cert.nome_municipio ? `${cert.nome_municipio}/${cert.uf}` : '-';
            
            container.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>
                        <div style="font-size: 11px; opacity: 0.8;">CNPJ:</div>
                        <div style="font-weight: bold; font-size: 14px;">${cnpjFmt}</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; opacity: 0.8;">Razão Social:</div>
                        <div style="font-weight: bold; font-size: 13px;">${cert.razao_social || '-'}</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; opacity: 0.8;">Município:</div>
                        <div style="font-weight: bold;">${municipioInfo}</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; opacity: 0.8;">Validade até:</div>
                        <div style="font-weight: bold;">${validadeFormatada} ${statusBadge}</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; opacity: 0.8;">Emitente:</div>
                        <div style="font-size: 12px;">${cert.emitente || '-'}</div>
                    </div>
                    <div style="display: flex; align-items: flex-end;">
                        <button onclick="excluirCertificadoNFSe(${cert.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Remover Certificado">
                            🗑️ Remover Certificado
                        </button>
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div style="text-align: center; padding: 5px;">
                    <span style="font-size: 20px;">🔓</span>
                    <p style="margin: 5px 0 0 0; font-size: 13px; opacity: 0.9;">Nenhum certificado configurado. Faça o upload do seu certificado A1 (.pfx) abaixo.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('❌ Erro ao carregar certificado:', error);
        container.innerHTML = '<span style="font-size: 13px; opacity: 0.8;">⚠️ Erro ao verificar certificado</span>';
    }
};

// Upload de certificado digital
// Preencher formulário de município com dados do certificado
window.preencherFormMunicipioComCertificado = function(cert) {
    console.log('📝 Preenchendo formulário com dados do certificado:', cert);
    console.log('📊 DADOS DO CERTIFICADO:');
    console.log('   - cnpj:', cert.cnpj);
    console.log('   - codigo_municipio:', cert.codigo_municipio);
    console.log('   - nome_municipio:', cert.nome_municipio);
    console.log('   - uf:', cert.uf);
    console.log('   - config_criada:', cert.config_criada);
    
    // Se config já foi criada automaticamente, avisar usuário
    if (cert.config_criada) {
        console.warn('⚠️ Config já foi criada! Não preenchendo formulário.');
        showToast('ℹ️ Município já configurado! Se precisar editar, use os botões na lista de municípios abaixo.', 'info', 5000);
        // Scroll suave até a lista de municípios
        const listaMunicipios = document.getElementById('lista-municipios-nfse');
        if (listaMunicipios) {
            listaMunicipios.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        return; // Não preencher formulário se config já existe
    }
    
    console.log('🔧 Preenchendo campos do formulário...');
    
    // Preencher campos do formulário com dados do certificado
    if (cert.cnpj) {
        const cnpjInput = document.getElementById('config-cnpj');
        console.log('   - Campo CNPJ:', cnpjInput ? '✅ Encontrado' : '❌ NÃO encontrado');
        if (cnpjInput) {
            cnpjInput.value = cert.cnpj;
            cnpjInput.style.background = '#e8f5e9'; // Verde claro para indicar auto-preenchido
            cnpjInput.readOnly = true; // Bloquear edição de dados vindos do certificado
            console.log('   ✅ CNPJ preenchido:', cert.cnpj);
        }
    } else {
        console.warn('   ⚠️ CNPJ não disponível no certificado');
    }
    
    if (cert.codigo_municipio) {
        const codigoInput = document.getElementById('config-codigo-municipio');
        console.log('   - Campo Código IBGE:', codigoInput ? '✅ Encontrado' : '❌ NÃO encontrado');
        if (codigoInput) {
            codigoInput.value = cert.codigo_municipio;
            codigoInput.style.background = '#e8f5e9';
            codigoInput.readOnly = true;
            console.log('   ✅ Código IBGE preenchido:', cert.codigo_municipio);
        }
    } else {
        console.warn('   ⚠️ Código IBGE não disponível no certificado');
    }
    
    if (cert.nome_municipio) {
        const nomeInput = document.getElementById('config-nome-municipio');
        console.log('   - Campo Nome Município:', nomeInput ? '✅ Encontrado' : '❌ NÃO encontrado');
        if (nomeInput) {
            nomeInput.value = cert.nome_municipio;
            nomeInput.style.background = '#e8f5e9';
            nomeInput.readOnly = true;
            console.log('   ✅ Nome município preenchido:', cert.nome_municipio);
        }
    } else {
        console.warn('   ⚠️ Nome do município não disponível no certificado');
    }
    
    if (cert.uf) {
        const ufSelect = document.getElementById('config-uf');
        console.log('   - Campo UF:', ufSelect ? '✅ Encontrado' : '❌ NÃO encontrado');
        if (ufSelect) {
            ufSelect.value = cert.uf;
            ufSelect.style.background = '#e8f5e9';
            ufSelect.disabled = true; // Desabilitar dropdown se veio do certificado
            console.log('   ✅ UF preenchida:', cert.uf);
        }
    } else {
        console.warn('   ⚠️ UF não disponível no certificado');
    }
    
    // Selecionar provedor padrão (GINFES)
    const provedorSelect = document.getElementById('config-provedor');
    console.log('   - Campo Provedor:', provedorSelect ? '✅ Encontrado' : '❌ NÃO encontrado');
    if (provedorSelect) {
        provedorSelect.value = 'GINFES';
        provedorSelect.style.background = '#e8f5e9';
        console.log('   ✅ Provedor configurado: GINFES');
    }
    
    // Focar no campo Inscrição Municipal (único que usuário precisa preencher)
    const inscricaoInput = document.getElementById('config-inscricao-municipal');
    console.log('   - Campo Inscrição Municipal:', inscricaoInput ? '✅ Encontrado' : '❌ NÃO encontrado');
    if (inscricaoInput) {
        inscricaoInput.value = ''; // Limpar qualquer valor
        inscricaoInput.focus();
        inscricaoInput.style.background = '#fff3cd'; // Amarelo claro para destacar
        inscricaoInput.style.borderColor = '#ffc107';
        inscricaoInput.style.borderWidth = '2px';
        console.log('   ✅ Foco definido no campo Inscrição Municipal');
        
        // Scroll suave até o formulário
        inscricaoInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    console.log('✅ Preenchimento do formulário CONCLUÍDO!');
    
    // Adicionar mensagem informativa no formulário
    showToast('📝 Formulário preenchido automaticamente! Complete apenas a Inscrição Municipal e clique em Salvar.', 'info', 6000);
};

window.uploadCertificadoNFSe = async function(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('cert-arquivo');
    const senhaInput = document.getElementById('cert-senha');
    const btnUpload = document.getElementById('btn-upload-cert');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        showToast('⚠️ Selecione o arquivo do certificado (.pfx)', 'warning');
        return;
    }
    
    if (!senhaInput.value) {
        showToast('⚠️ Digite a senha do certificado', 'warning');
        return;
    }
    
    const arquivo = fileInput.files[0];
    const ext = arquivo.name.split('.').pop().toLowerCase();
    
    if (!['pfx', 'p12'].includes(ext)) {
        showToast('⚠️ Formato inválido. Use arquivo .pfx ou .p12', 'warning');
        return;
    }
    
    // Confirmar upload
    if (!confirm('🔐 Deseja carregar este certificado digital?\n\nO sistema vai:\n1. Extrair o CNPJ automaticamente\n2. Buscar o código do município\n3. Armazenar o certificado para consulta de NFS-e\n\nDeseja continuar?')) {
        return;
    }
    
    btnUpload.disabled = true;
    btnUpload.textContent = '⏳ Processando...';
    showToast('⏳ Processando certificado...', 'info');
    
    try {
        const formData = new FormData();
        formData.append('certificado', arquivo);
        formData.append('senha', senhaInput.value);
        
        const response = await fetch('/api/nfse/certificado/upload', {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            const cert = data.certificado;
            
            // Usar mensagem do backend (inclui info sobre auto-configuração)
            showToast(data.message, 'success', 6000);
            
            // Mostrar detalhes em alert
            let msg = `✅ Certificado processado com sucesso!\n\n`;
            msg += `📋 CNPJ: ${cert.cnpj || '-'}\n`;
            msg += `🏢 ${cert.razao_social || '-'}\n`;
            msg += `🏙️ Município: ${cert.nome_municipio || '-'}/${cert.uf || '-'}\n`;
            msg += `📅 Validade: ${cert.validade_fim ? new Date(cert.validade_fim).toLocaleDateString('pt-BR') : '-'}\n`;
            
            if (cert.config_criada) {
                msg += `\n✅ Município configurado automaticamente!\n`;
                msg += `⚠️ IMPORTANTE: Complete a Inscrição Municipal em "⚙️ Configurar Municípios"`;
            } else if (cert.codigo_municipio) {
                msg += `\n⚠️ Configure o município em "⚙️ Configurar Municípios"`;
            }
            
            alert(msg);
            
            // Resetar form
            document.getElementById('form-upload-certificado').reset();
            
            // Recarregar status e municípios
            await window.carregarCertificadoNFSe();
            
            // Se criou configuração, recarregar lista de municípios também
            if (cert.config_criada && window.loadNFSeConfigs) {
                await window.loadNFSeConfigs();
            }
            
            // PREENCHER FORMULÁRIO AUTOMATICAMENTE COM DADOS DO CERTIFICADO
            window.preencherFormMunicipioComCertificado(cert);
        } else {
            showToast(`❌ Erro: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao fazer upload do certificado:', error);
        showToast('❌ Erro ao processar certificado', 'error');
    } finally {
        btnUpload.disabled = false;
        btnUpload.textContent = '🔑 Enviar Certificado';
    }
};

// Excluir certificado
window.excluirCertificadoNFSe = async function(certId) {
    if (!confirm('⚠️ Deseja remover este certificado digital?\n\nAs NFS-e já baixadas não serão afetadas.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/nfse/certificado/${certId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('✅ Certificado removido com sucesso!', 'success');
            await window.carregarCertificadoNFSe();
        } else {
            showToast(`❌ Erro: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao excluir certificado:', error);
        showToast('❌ Erro ao excluir certificado', 'error');
    }
};

// ============================================================================
// GERAÇÃO DE PDF (DANFSE)
// ============================================================================

// Gerar PDF de uma NFS-e
window.gerarPdfNFSe = async function(nfseId) {
    console.log('📄 Gerando PDF da NFS-e ID:', nfseId);
    showToast('⏳ Gerando PDF da NFS-e...', 'info');
    
    try {
        const response = await fetch(`/api/nfse/${nfseId}/pdf`, {
            method: 'GET',
            credentials: 'include'
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `nfse_${nfseId}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            
            showToast('✅ PDF gerado com sucesso!', 'success');
        } else {
            let errorMsg = 'Erro ao gerar PDF';
            try {
                const data = await response.json();
                errorMsg = data.error || errorMsg;
            } catch (e) {}
            showToast(`❌ ${errorMsg}`, 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao gerar PDF:', error);
        showToast('❌ Erro ao gerar PDF da NFS-e', 'error');
    }
};

// FIM MÓDULO NFS-e

// ============================================================================
// MÓDULO CONTABILIDADE - PLANO DE CONTAS
// ============================================================================

// Estado do módulo
window.pcContas = [];
window.pcVisualizacao = 'lista'; // 'lista' ou 'arvore'
window.pcOrdenacao = { campo: 'codigo', direcao: 'asc' };

// Carregar seção (chamada pelo showSection)
window.loadPlanoContas = async function() {
    console.log('📒 Carregando módulo Plano de Contas...');
    await carregarVersoesDropdown();
};

// Carregar dropdown de versões
async function carregarVersoesDropdown() {
    try {
        console.log('🔄 Carregando versões do dropdown...');
        const response = await fetch('/api/contabilidade/versoes', { credentials: 'include' });
        const data = await response.json();
        console.log('📦 Versões recebidas:', data);
        console.log('📦 data.versoes é array?', Array.isArray(data.versoes));
        console.log('📦 data.versoes.length:', data.versoes ? data.versoes.length : 'undefined');
        if (data.versoes && data.versoes.length > 0) {
            console.log('📦 Primeira versão:', JSON.stringify(data.versoes[0]));
        }
        
        if (data.success) {
            const select = document.getElementById('pcVersaoFiltro');
            const valorAtual = select.value;
            console.log('🔍 Valor atual do select:', valorAtual);
            select.innerHTML = '<option value="">-- Selecione --</option>';
            
            let versaoAtiva = null;
            data.versoes.forEach(v => {
                console.log('➕ Adicionando versão:', v.id, '-', v.nome_versao);
                const opt = document.createElement('option');
                opt.value = v.id;
                opt.textContent = `${v.nome_versao} (${v.exercicio_fiscal})${v.is_ativa ? ' ★' : ''}`;
                select.appendChild(opt);
                if (v.is_ativa) versaoAtiva = v.id;
            });
            console.log('⭐ Versão ativa encontrada:', versaoAtiva);
            console.log('⭐ Versão ativa encontrada:', versaoAtiva);
            
            // Restaurar seleção ou selecionar ativa ou primeira disponível
            if (valorAtual) {
                select.value = valorAtual;
                console.log('✅ Restaurado valor anterior:', valorAtual);
            } else if (versaoAtiva) {
                select.value = versaoAtiva;
                console.log('✅ Selecionada versão ativa:', versaoAtiva);
            } else if (data.versoes.length > 0) {
                // Auto-selecionar primeira versão disponível (melhoria UX)
                select.value = data.versoes[0].id;
                console.log('✅ Auto-selecionada primeira versão:', data.versoes[0].id, '-', data.versoes[0].nome_versao);
            }
            
            console.log('🎯 Valor final do select:', select.value);
            
            if (select.value) {
                console.log('🚀 Chamando carregarPlanoContas()...');
                carregarPlanoContas();
            } else {
                console.warn('⚠️ Nenhuma versão selecionada automaticamente');
            }
        }
    } catch (error) {
        console.error('Erro ao carregar versões:', error);
    }
}

// Carregar contas do plano
window.carregarPlanoContas = async function() {
    const versaoId = document.getElementById('pcVersaoFiltro').value;
    console.log('🔍 carregarPlanoContas - versaoId:', versaoId, 'tipo:', typeof versaoId);
    
    if (!versaoId || versaoId === '' || versaoId === 'id') {
        console.warn('⚠️ versaoId inválido:', versaoId);
        document.getElementById('pcTabelaBody').innerHTML = 
            '<tr><td colspan="7" style="text-align: center; padding: 40px; color: #999;">Selecione uma versão válida</td></tr>';
        return;
    }
    
    const classificacao = document.getElementById('pcClassificacaoFiltro').value;
    const tipo = document.getElementById('pcTipoFiltro').value;
    const busca = document.getElementById('pcBusca').value;
    
    let url = `/api/contabilidade/plano-contas?versao_id=${versaoId}`;
    console.log('🌐 Fazendo requisição para URL:', url);
    if (classificacao) url += `&classificacao=${classificacao}`;
    if (tipo) url += `&tipo_conta=${tipo}`;
    if (busca) url += `&busca=${encodeURIComponent(busca)}`;
    
    console.log('🌐 URL final:', url);
    
    try {
        console.log('⏳ Iniciando fetch...');
        const response = await fetch(url, { credentials: 'include' });
        console.log('✅ Response recebido:', response.status, response.statusText);
        
        const data = await response.json();
        console.log('📦 Data parseado:', data);
        console.log('📊 data.success:', data.success);
        console.log('📊 data.contas:', data.contas);
        console.log('📊 data.contas.length:', data.contas ? data.contas.length : 'undefined');
        
        if (data.success) {
            console.log('✅ Sucesso! Processando', data.contas.length, 'contas');
            window.pcContas = data.contas;
            
            console.log('📊 Atualizando estatísticas...');
            atualizarEstatisticasPC(data.contas);
            
            console.log('🎨 Visualização:', window.pcVisualizacao);
            if (window.pcVisualizacao === 'arvore') {
                console.log('🌳 Renderizando árvore...');
                renderizarArvorePC(versaoId);
            } else {
                console.log('📋 Renderizando tabela...');
                renderizarTabelaPC(data.contas);
            }
            console.log('✅ Renderização concluída!');
        } else {
            console.error('❌ Erro no data.success:', data.error);
            showToast('❌ ' + (data.error || 'Erro ao carregar contas'), 'error');
        }
    } catch (error) {
        console.error('❌ Erro no try/catch:', error);
        console.error('❌ Stack:', error.stack);
        showToast('❌ Erro ao carregar plano de contas', 'error');
    }
};

// Atualizar estatísticas
function atualizarEstatisticasPC(contas) {
    console.log('📊 atualizarEstatisticasPC chamada');
    console.log('   📦 contas:', contas);
    console.log('   📊 contas.length:', contas ? contas.length : 'null/undefined');
    
    const totalEl = document.getElementById('pcTotalContas');
    const sinteticasEl = document.getElementById('pcTotalSinteticas');
    const analiticasEl = document.getElementById('pcTotalAnaliticas');
    const bloqueadasEl = document.getElementById('pcTotalBloqueadas');
    
    console.log('   📍 Elementos encontrados:', {
        total: !!totalEl,
        sinteticas: !!sinteticasEl,
        analiticas: !!analiticasEl,
        bloqueadas: !!bloqueadasEl
    });
    
    if (!totalEl || !sinteticasEl || !analiticasEl || !bloqueadasEl) {
        console.error('   ❌ Elementos de estatísticas não encontrados!');
        return;
    }
    
    const total = contas.length;
    const sinteticas = contas.filter(c => c.tipo_conta === 'sintetica').length;
    const analiticas = contas.filter(c => c.tipo_conta === 'analitica').length;
    const bloqueadas = contas.filter(c => c.is_bloqueada).length;
    
    console.log('   📊 Estatísticas calculadas:', { total, sinteticas, analiticas, bloqueadas });
    
    totalEl.textContent = total;
    sinteticasEl.textContent = sinteticas;
    analiticasEl.textContent = analiticas;
    bloqueadasEl.textContent = bloqueadas;
    
    console.log('   ✅ Estatísticas atualizadas');
}

// Labels para classificação
const classificacaoLabels = {
    'ativo': '🟦 Ativo',
    'passivo': '🟥 Passivo',
    'patrimonio_liquido': '🟨 Patr. Líquido',
    'receita': '🟩 Receita',
    'despesa': '🟧 Despesa',
    'compensacao': '⬜ Compensação'
};

const classificacaoCores = {
    'ativo': '#3498db',
    'passivo': '#e74c3c',
    'patrimonio_liquido': '#f39c12',
    'receita': '#27ae60',
    'despesa': '#e67e22',
    'compensacao': '#95a5a6'
};

// Renderizar tabela
function renderizarTabelaPC(contas) {
    console.log('🎨 renderizarTabelaPC chamada');
    console.log('   📦 contas:', contas);
    console.log('   📊 contas.length:', contas ? contas.length : 'null/undefined');
    
    const tbody = document.getElementById('pcTabelaBody');
    console.log('   📍 tbody element:', tbody);
    
    if (!contas || contas.length === 0) {
        console.log('   ⚠️ Nenhuma conta para exibir');
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px; color: #999;">Nenhuma conta encontrada</td></tr>';
        return;
    }
    
    console.log('   ✅ Renderizando', contas.length, 'contas...');
    
    // Ordenar
    const { campo, direcao } = window.pcOrdenacao;
    contas.sort((a, b) => {
        let va = a[campo] || '';
        let vb = b[campo] || '';
        if (typeof va === 'string') va = va.toLowerCase();
        if (typeof vb === 'string') vb = vb.toLowerCase();
        if (va < vb) return direcao === 'asc' ? -1 : 1;
        if (va > vb) return direcao === 'asc' ? 1 : -1;
        return 0;
    });
    
    tbody.innerHTML = contas.map(c => {
        const indent = (c.nivel - 1) * 20;
        const isSintetica = c.tipo_conta === 'sintetica';
        const classCor = classificacaoCores[c.classificacao] || '#333';
        const bloqueadaBadge = c.is_bloqueada ? '<span style="background: #e74c3c; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px;">🔒</span>' : '<span style="background: #27ae60; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px;">✅</span>';
        
        return `<tr style="border-bottom: 1px solid #eee; ${isSintetica ? 'background: #f8f9fa; font-weight: 600;' : ''}">
            <td style="padding: 8px 12px; font-family: monospace; font-size: 13px; padding-left: ${12 + indent}px;">
                ${isSintetica ? '📁' : '📄'} ${c.codigo}
            </td>
            <td style="padding: 8px 12px;">${c.descricao}</td>
            <td style="padding: 8px 12px; text-align: center;">
                <span style="background: ${isSintetica ? '#e8e8e8' : '#e8f4fd'}; padding: 3px 8px; border-radius: 4px; font-size: 12px;">
                    ${isSintetica ? 'Sintética' : 'Analítica'}
                </span>
            </td>
            <td style="padding: 8px 12px; text-align: center;">
                <span style="color: ${classCor}; font-weight: 500; font-size: 13px;">${classificacaoLabels[c.classificacao] || c.classificacao}</span>
            </td>
            <td style="padding: 8px 12px; text-align: center; font-size: 13px;">
                ${c.natureza === 'devedora' ? '📉 Devedora' : '📈 Credora'}
            </td>
            <td style="padding: 8px 12px; text-align: center;">${bloqueadaBadge}</td>
            <td style="padding: 8px 12px; text-align: center;">
                <button onclick="editarContaContabil(${c.id})" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Editar">✏️</button>
                <button onclick="excluirContaPC(${c.id}, '${c.codigo}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
            </td>
        </tr>`;
    }).join('');
    
    console.log('   ✅ HTML da tabela gerado (' + tbody.innerHTML.length + ' chars)');
    console.log('   ✅ renderizarTabelaPC concluída!');
}

// Ordenar tabela
window.ordenarPlanoContas = function(campo) {
    if (window.pcOrdenacao.campo === campo) {
        window.pcOrdenacao.direcao = window.pcOrdenacao.direcao === 'asc' ? 'desc' : 'asc';
    } else {
        window.pcOrdenacao.campo = campo;
        window.pcOrdenacao.direcao = 'asc';
    }
    renderizarTabelaPC(window.pcContas);
};

// Toggle visualização Lista/Árvore
window.toggleVisualizacao = function() {
    const btn = document.getElementById('btnToggleViz');
    if (window.pcVisualizacao === 'lista') {
        window.pcVisualizacao = 'arvore';
        document.getElementById('pcVisualizacaoLista').style.display = 'none';
        document.getElementById('pcVisualizacaoArvore').style.display = 'block';
        btn.textContent = '📋 Lista';
        const versaoId = document.getElementById('pcVersaoFiltro').value;
        if (versaoId) renderizarArvorePC(versaoId);
    } else {
        window.pcVisualizacao = 'lista';
        document.getElementById('pcVisualizacaoLista').style.display = 'block';
        document.getElementById('pcVisualizacaoArvore').style.display = 'none';
        btn.textContent = '🌲 Árvore';
        renderizarTabelaPC(window.pcContas);
    }
};

// Renderizar árvore
async function renderizarArvorePC(versaoId) {
    const container = document.getElementById('pcArvoreContainer');
    container.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">Carregando árvore...</p>';
    
    try {
        const response = await fetch(`/api/contabilidade/plano-contas/tree?versao_id=${versaoId}`, { credentials: 'include' });
        const data = await response.json();
        
        if (data.success && data.tree.length > 0) {
            container.innerHTML = renderizarNodoArvore(data.tree);
        } else {
            container.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">Nenhuma conta encontrada nesta versão</p>';
        }
    } catch (error) {
        container.innerHTML = '<p style="text-align: center; color: #e74c3c;">Erro ao carregar árvore</p>';
    }
}

function renderizarNodoArvore(nodos, nivel = 0) {
    if (!nodos || nodos.length === 0) return '';
    
    return nodos.map(n => {
        const isSintetica = n.tipo_conta === 'sintetica';
        const hasChildren = n.children && n.children.length > 0;
        const cor = classificacaoCores[n.classificacao] || '#333';
        const nodeId = `tree-node-${n.id}`;
        
        return `
        <div style="margin-left: ${nivel * 24}px; margin-bottom: 2px;">
            <div style="display: flex; align-items: center; padding: 6px 10px; border-radius: 6px; cursor: pointer; transition: background 0.2s;"
                 onmouseover="this.style.background='#f0f4f8'" onmouseout="this.style.background='transparent'"
                 onclick="${hasChildren ? `toggleTreeNode('${nodeId}')` : ''}">
                <span style="width: 20px; text-align: center; color: #999; font-size: 12px;">
                    ${hasChildren ? `<span id="${nodeId}-icon">▶</span>` : '•'}
                </span>
                <span style="font-family: monospace; font-size: 12px; color: ${cor}; margin-right: 8px; font-weight: 600;">${n.codigo}</span>
                <span style="flex: 1; font-size: 13px; ${isSintetica ? 'font-weight: 600;' : ''}">${isSintetica ? '📁' : '📄'} ${n.descricao}</span>
                <span style="font-size: 11px; color: #999; margin-right: 8px;">${n.natureza === 'devedora' ? 'D' : 'C'}</span>
                ${n.is_bloqueada ? '<span style="font-size: 11px;">🔒</span>' : ''}
                <button onclick="event.stopPropagation(); editarContaContabil(${n.id})" style="background: none; border: none; cursor: pointer; font-size: 14px; padding: 2px;">✏️</button>
                <button onclick="event.stopPropagation(); excluirContaPC(${n.id}, '${n.codigo}')" style="background: none; border: none; cursor: pointer; font-size: 14px; padding: 2px;">🗑️</button>
            </div>
            ${hasChildren ? `<div id="${nodeId}" style="display: none;">${renderizarNodoArvore(n.children, nivel + 1)}</div>` : ''}
        </div>`;
    }).join('');
}

window.toggleTreeNode = function(nodeId) {
    const node = document.getElementById(nodeId);
    const icon = document.getElementById(nodeId + '-icon');
    if (node) {
        if (node.style.display === 'none') {
            node.style.display = 'block';
            if (icon) icon.textContent = '▼';
        } else {
            node.style.display = 'none';
            if (icon) icon.textContent = '▶';
        }
    }
};

// ========================
// CRUD Contas
// ========================

// Abrir modal para nova conta
window.abrirModalConta = function(parentId) {
    document.getElementById('modalContaTitulo').textContent = '➕ Nova Conta';
    document.getElementById('contaEditId').value = '';
    document.getElementById('contaCodigo').value = '';
    document.getElementById('contaDescricao').value = '';
    document.getElementById('contaTipoConta').value = 'analitica';
    document.getElementById('contaClassificacao').value = 'ativo';
    document.getElementById('contaNatureza').value = 'devedora';
    document.getElementById('contaBloqueada').checked = false;
    document.getElementById('contaCentroCusto').checked = false;
    document.getElementById('contaPermiteLancamento').checked = true;
    // Campos Speed
    document.getElementById('contaCodigoSpeed').value = '';
    document.getElementById('contaCodigoReferencial').value = '';
    document.getElementById('contaNaturezaSped').value = '01';
    
    // Carregar contas sintéticas como possíveis pais
    carregarListaPais(parentId);
    
    document.getElementById('modalConta').style.display = 'flex';
};

window.fecharModalConta = function() {
    document.getElementById('modalConta').style.display = 'none';
};

// Carregar lista de contas pai (sintéticas)
async function carregarListaPais(selectedParentId) {
    const select = document.getElementById('contaParentId');
    select.innerHTML = '<option value="">-- Raiz (Nível 1) --</option>';
    
    const sinteticas = window.pcContas.filter(c => c.tipo_conta === 'sintetica');
    sinteticas.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = `${c.codigo} - ${c.descricao}`;
        if (selectedParentId && c.id == selectedParentId) opt.selected = true;
        select.appendChild(opt);
    });
}

// Editar conta contábil existente (Plano de Contas)
window.editarContaContabil = async function(contaId) {
    const conta = window.pcContas.find(c => c.id === contaId);
    if (!conta) { showToast('❌ Conta contábil não encontrada', 'error'); return; }
    
    document.getElementById('modalContaTitulo').textContent = '✏️ Editar Conta';
    document.getElementById('contaEditId').value = conta.id;
    document.getElementById('contaCodigo').value = conta.codigo;
    document.getElementById('contaDescricao').value = conta.descricao;
    document.getElementById('contaTipoConta').value = conta.tipo_conta;
    document.getElementById('contaClassificacao').value = conta.classificacao;
    document.getElementById('contaNatureza').value = conta.natureza;
    document.getElementById('contaBloqueada').checked = conta.is_bloqueada;
    document.getElementById('contaCentroCusto').checked = conta.requer_centro_custo;
    document.getElementById('contaPermiteLancamento').checked = conta.permite_lancamento;
    // Campos Speed
    document.getElementById('contaCodigoSpeed').value = conta.codigo_speed || '';
    document.getElementById('contaCodigoReferencial').value = conta.codigo_referencial || '';
    document.getElementById('contaNaturezaSped').value = conta.natureza_sped || '01';
    
    await carregarListaPais(conta.parent_id);
    
    document.getElementById('modalConta').style.display = 'flex';
};

// Salvar conta (nova ou edição)
window.salvarConta = async function(event) {
    if (event && event.preventDefault) event.preventDefault();
    const editId = document.getElementById('contaEditId').value;
    const versaoId = document.getElementById('pcVersaoFiltro').value;
    
    if (!versaoId) {
        showToast('⚠️ Selecione uma versão primeiro', 'warning');
        return;
    }
    
    const dados = {
        versao_id: parseInt(versaoId),
        codigo: document.getElementById('contaCodigo').value.trim(),
        descricao: document.getElementById('contaDescricao').value.trim(),
        tipo_conta: document.getElementById('contaTipoConta').value,
        classificacao: document.getElementById('contaClassificacao').value,
        natureza: document.getElementById('contaNatureza').value,
        parent_id: document.getElementById('contaParentId').value ? parseInt(document.getElementById('contaParentId').value) : null,
        is_bloqueada: document.getElementById('contaBloqueada').checked,
        requer_centro_custo: document.getElementById('contaCentroCusto').checked,
        permite_lancamento: document.getElementById('contaPermiteLancamento').checked,
        // Campos Speed
        codigo_speed: document.getElementById('contaCodigoSpeed').value.trim() || null,
        codigo_referencial: document.getElementById('contaCodigoReferencial').value.trim() || null,
        natureza_sped: document.getElementById('contaNaturezaSped').value
    };
    
    if (!dados.codigo || !dados.descricao) {
        showToast('⚠️ Código e Descrição são obrigatórios', 'warning');
        return;
    }
    
    try {
        let url = '/api/contabilidade/plano-contas';
        let method = 'POST';
        
        if (editId) {
            url += `/${editId}`;
            method = 'PUT';
        }
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(dados)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`✅ Conta ${editId ? 'atualizada' : 'criada'} com sucesso!`, 'success');
            fecharModalConta();
            carregarPlanoContas();
        } else {
            showToast('❌ ' + (data.error || 'Erro ao salvar'));
        }
    } catch (error) {
        console.error('Erro ao salvar conta:', error);
        showToast('❌ Erro ao salvar conta', 'error');
    }
};

// Excluir conta
window.excluirContaPC = async function(contaId, codigo) {
    if (!confirm(`⚠️ Deseja excluir a conta ${codigo} e todas as suas subcontas?\n\nEsta ação não pode ser desfeita.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/contabilidade/plano-contas/${contaId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`✅ ${data.message}`, 'success');
            carregarPlanoContas();
        } else {
            showToast('❌ ' + (data.error || 'Erro ao excluir'));
        }
    } catch (error) {
        console.error('Erro ao excluir conta:', error);
        showToast('❌ Erro ao excluir conta', 'error');
    }
};

// ========================
// Versões
// ========================

window.abrirModalVersaoPlano = async function() {
    document.getElementById('modalVersoes').style.display = 'flex';
    await carregarListaVersoes();
};

window.fecharModalVersoes = function() {
    document.getElementById('modalVersoes').style.display = 'none';
};

async function carregarListaVersoes() {
    const container = document.getElementById('listaVersoes');
    container.innerHTML = '<p style="text-align: center; color: #999;">Carregando...</p>';
    
    try {
        const response = await fetch('/api/contabilidade/versoes', { credentials: 'include' });
        const data = await response.json();
        
        if (data.success && data.versoes.length > 0) {
            container.innerHTML = data.versoes.map(v => `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; border-bottom: 1px solid #eee;">
                    <div>
                        <strong>${v.nome_versao}</strong> 
                        <span style="color: #999; font-size: 13px;">(Exercício: ${v.exercicio_fiscal})</span>
                        ${v.is_ativa ? '<span style="background: #27ae60; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-left: 8px;">ATIVA</span>' : ''}
                    </div>
                    <div style="display: flex; gap: 8px;">
                        ${!v.is_ativa ? `<button onclick="ativarVersao(${v.id})" style="background: #27ae60; color: white; border: none; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">Ativar</button>` : ''}
                        <button onclick="excluirVersaoPlano(${v.id}, '${v.nome_versao}')" style="background: none; border: none; cursor: pointer; font-size: 16px;" title="Excluir">🗑️</button>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">Nenhuma versão cadastrada</p>';
        }
    } catch (error) {
        container.innerHTML = '<p style="text-align: center; color: #e74c3c;">Erro ao carregar versões</p>';
    }
}

window.criarVersaoPlano = async function() {
    const nome = document.getElementById('novaVersaoNome').value.trim();
    const exercicio = document.getElementById('novaVersaoExercicio').value;
    
    if (!nome || !exercicio) {
        showToast('⚠️ Preencha nome e exercício fiscal', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/contabilidade/versoes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                nome_versao: nome,
                exercicio_fiscal: parseInt(exercicio),
                is_ativa: true
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('✅ Versão criada com sucesso!', 'success');
            document.getElementById('novaVersaoNome').value = '';
            document.getElementById('novaVersaoExercicio').value = '';
            await carregarListaVersoes();
            await carregarVersoesDropdown();
        } else {
            showToast('❌ ' + (data.error || 'Erro ao criar versão'));
        }
    } catch (error) {
        showToast('❌ Erro ao criar versão', 'error');
    }
};

window.ativarVersao = async function(versaoId) {
    try {
        const response = await fetch(`/api/contabilidade/versoes/${versaoId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ is_ativa: true, nome_versao: '', exercicio_fiscal: 0 })
        });
        
        // Recarregar para obter dados completos
        const resp2 = await fetch('/api/contabilidade/versoes', { credentials: 'include' });
        const data2 = await resp2.json();
        if (data2.success) {
            const versao = data2.versoes.find(v => v.id === versaoId);
            if (versao) {
                await fetch(`/api/contabilidade/versoes/${versaoId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        nome_versao: versao.nome_versao,
                        exercicio_fiscal: versao.exercicio_fiscal,
                        is_ativa: true,
                        observacoes: versao.observacoes || ''
                    })
                });
            }
        }
        
        showToast('✅ Versão ativada!', 'success');
        await carregarListaVersoes();
        await carregarVersoesDropdown();
    } catch (error) {
        showToast('❌ Erro ao ativar versão', 'error');
    }
};

window.excluirVersaoPlano = async function(versaoId, nome) {
    if (!confirm(`⚠️ Excluir versão "${nome}"?\n\nTodas as contas desta versão serão removidas!`)) return;
    
    try {
        const response = await fetch(`/api/contabilidade/versoes/${versaoId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('✅ Versão excluída', 'success');
            await carregarListaVersoes();
            await carregarVersoesDropdown();
        } else {
            showToast('❌ ' + (data.error || 'Erro ao excluir'));
        }
    } catch (error) {
        showToast('❌ Erro ao excluir versão', 'error');
    }
};

// ========================
// Import / Export
// ========================

window.importarPlanoContas = function() {
    const versaoId = document.getElementById('pcVersaoFiltro').value;
    if (!versaoId) {
        showToast('⚠️ Selecione uma versão primeiro', 'warning');
        return;
    }
    document.getElementById('modalImportar').style.display = 'flex';
};

window.fecharModalImportar = function() {
    document.getElementById('modalImportar').style.display = 'none';
};

window.processarImportCSV = async function() {
    const fileInput = document.getElementById('csvImportFile');
    const file = fileInput.files[0];
    if (!file) { showToast('⚠️ Selecione um arquivo CSV', 'warning'); return; }
    
    const versaoId = document.getElementById('pcVersaoFiltro').value;
    
    const text = await file.text();
    const linhas = text.split('\n').filter(l => l.trim());
    
    if (linhas.length < 2) { showToast('⚠️ CSV vazio ou sem dados', 'warning'); return; }
    
    // Parsear cabeçalho
    const separador = linhas[0].includes(';') ? ';' : ',';
    const headers = linhas[0].split(separador).map(h => h.trim().toLowerCase().replace(/"/g, ''));
    
    const dados = [];
    for (let i = 1; i < linhas.length; i++) {
        const valores = linhas[i].split(separador).map(v => v.trim().replace(/"/g, ''));
        const obj = {};
        headers.forEach((h, idx) => { obj[h] = valores[idx] || ''; });
        if (obj.codigo && obj.descricao) {
            dados.push(obj);
        }
    }
    
    if (dados.length === 0) { showToast('⚠️ Nenhum dado válido no CSV', 'warning'); return; }
    
    try {
        const response = await fetch('/api/contabilidade/plano-contas/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ versao_id: parseInt(versaoId), linhas: dados })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`✅ ${data.importadas} contas importadas!${data.erros && data.erros.length > 0 ? ` (${data.erros.length} erros)` : ''}`, 'success');
            fecharModalImportar();
            fileInput.value = '';
            carregarPlanoContas();
        } else {
            showToast('❌ ' + (data.error || 'Erro na importação'));
        }
    } catch (error) {
        showToast('❌ Erro ao importar CSV', 'error');
    }
};

window.exportarPlanoContas = async function() {
    const versaoId = document.getElementById('pcVersaoFiltro').value;
    if (!versaoId) { showToast('⚠️ Selecione uma versão primeiro', 'warning'); return; }
    
    try {
        const response = await fetch(`/api/contabilidade/plano-contas/export?versao_id=${versaoId}`, { credentials: 'include' });
        const data = await response.json();
        
        if (data.success && data.contas.length > 0) {
            // Gerar CSV
            const headers = ['codigo', 'descricao', 'tipo_conta', 'classificacao', 'natureza', 'nivel', 'is_bloqueada', 'requer_centro_custo'];
            const csv = [
                headers.join(';'),
                ...data.contas.map(c => headers.map(h => `"${c[h] || ''}"`).join(';'))
            ].join('\n');
            
            const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `plano_contas_export.csv`;
            a.click();
            window.URL.revokeObjectURL(url);
            
            showToast(`✅ ${data.contas.length} contas exportadas!`, 'success');
        } else {
            showToast('⚠️ Nenhuma conta para exportar', 'warning');
        }
    } catch (error) {
        showToast('❌ Erro ao exportar', 'error');
    }
};

window.importarPlanoPadrao = async function() {
    // Confirmar com o usuário
    const anoFiscal = new Date().getFullYear();
    const confirmar = confirm(
        `📦 Importar Plano de Contas Padrão?\n\n` +
        `Será criada uma nova versão do plano de contas com a estrutura padrão brasileira.\n\n` +
        `Ano Fiscal: ${anoFiscal}\n` +
        `Total de contas: ~100\n\n` +
        `Você poderá editar, excluir e incluir contas após a importação.\n\n` +
        `Confirma?`
    );
    
    if (!confirmar) return;
    
    try {
        showToast('⏳ Importando plano de contas padrão...', 'info');
        
        const response = await fetch('/api/contabilidade/plano-contas/importar-padrao', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ ano_fiscal: anoFiscal })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(
                `✅ Plano de contas padrão importado com sucesso!\n\n` +
                `${data.contas_criadas} contas criadas` +
                (data.erros && data.erros.length > 0 ? `\n${data.erros.length} erros encontrados` : ''),
                'success'
            );
            
            // Recarregar versões e selecionar a nova
            await carregarVersoesDropdown();
            document.getElementById('pcVersaoFiltro').value = data.versao_id;
            await carregarPlanoContas();
        } else {
            showToast('❌ ' + (data.error || 'Erro ao importar plano padrão'), 'error');
        }
    } catch (error) {
        console.error('Erro ao importar plano padrão:', error);
        showToast('❌ Erro ao importar plano padrão', 'error');
    }
};

// FIM MÓDULO CONTABILIDADE

// =============================================================================
// MÓDULO INTEGRA CONTADOR - API SERPRO
// =============================================================================

// Variável global para armazenar o tipo de operação selecionado
window.integraContadorState = {
    tipoOperacao: null
};

/**
 * Função para selecionar o tipo de operação (Apoiar, Consultar, Declarar, Emitir, Monitorar)
 */
window.selecionarTipoOperacao = function(tipo) {
    window.integraContadorState.tipoOperacao = tipo;
    
    // Atualizar UI
    document.getElementById('tipo-operacao-selecionado').textContent = tipo;
    document.getElementById('form-integra-contador').style.display = 'block';
    document.getElementById('integra-empty-state').style.display = 'none';
    document.getElementById('resposta-integra-contador').style.display = 'none';
    
    showToast(`✅ Tipo de operação selecionado: ${tipo}`, 'success');
};

/**
 * Limpa o formulário
 */
window.limparFormIntegra = function() {
    document.getElementById('ic-contratante-numero').value = '';
    document.getElementById('ic-autor-numero').value = '';
    document.getElementById('ic-contribuinte-numero').value = '';
    document.getElementById('ic-id-sistema').value = '';
    document.getElementById('ic-id-servico').value = '';
    document.getElementById('ic-versao-sistema').value = '1.0';
    document.getElementById('ic-dados-json').value = '';
    
    document.getElementById('resposta-integra-contador').style.display = 'none';
    
    showToast('Formulário limpo', 'info');
};

/**
 * Valida os campos do formulário
 */
function validarFormulario() {
    const contratanteNumero = document.getElementById('ic-contratante-numero').value.trim();
    const autorNumero = document.getElementById('ic-autor-numero').value.trim();
    const contribuinteNumero = document.getElementById('ic-contribuinte-numero').value.trim();
    const idSistema = document.getElementById('ic-id-sistema').value.trim();
    const idServico = document.getElementById('ic-id-servico').value.trim();
    const versaoSistema = document.getElementById('ic-versao-sistema').value.trim();
    const dadosJson = document.getElementById('ic-dados-json').value.trim();
    
    if (!contratanteNumero || contratanteNumero.length !== 14) {
        showToast('❌ CNPJ do Contratante deve ter 14 dígitos', 'error');
        return false;
    }
    
    if (!autorNumero) {
        showToast('❌ Número do Autor do Pedido é obrigatório', 'error');
        return false;
    }
    
    const autorTipo = parseInt(document.getElementById('ic-autor-tipo').value);
    if (autorTipo === 1 && autorNumero.length !== 11) {
        showToast('❌ CPF do Autor deve ter 11 dígitos', 'error');
        return false;
    }
    if (autorTipo === 2 && autorNumero.length !== 14) {
        showToast('❌ CNPJ do Autor deve ter 14 dígitos', 'error');
        return false;
    }
    
    if (!contribuinteNumero) {
        showToast('❌ Número do Contribuinte é obrigatório', 'error');
        return false;
    }
    
    const contribuinteTipo = parseInt(document.getElementById('ic-contribuinte-tipo').value);
    if (contribuinteTipo === 1 && contribuinteNumero.length !== 11) {
        showToast('❌ CPF do Contribuinte deve ter 11 dígitos', 'error');
        return false;
    }
    if (contribuinteTipo === 2 && contribuinteNumero.length !== 14) {
        showToast('❌ CNPJ do Contribuinte deve ter 14 dígitos', 'error');
        return false;
    }
    
    if (!idSistema) {
        showToast('❌ ID Sistema é obrigatório', 'error');
        return false;
    }
    
    if (!idServico) {
        showToast('❌ ID Serviço é obrigatório', 'error');
        return false;
    }
    
    if (!versaoSistema) {
        showToast('❌ Versão do Sistema é obrigatória', 'error');
        return false;
    }
    
    if (!dadosJson) {
        showToast('❌ Dados (JSON) é obrigatório', 'error');
        return false;
    }
    
    // Validar se dados é um JSON válido
    try {
        JSON.parse(dadosJson);
    } catch (e) {
        showToast('❌ Dados (JSON) está em formato inválido', 'error');
        return false;
    }
    
    return true;
}

/**
 * Envia a requisição para a API Integra Contador
 */
window.enviarRequisicaoIntegra = async function() {
    if (!window.integraContadorState.tipoOperacao) {
        showToast('❌ Selecione um tipo de operação primeiro', 'error');
        return;
    }
    
    if (!validarFormulario()) {
        return;
    }
    
    try {
        // Coletar dados do formulário
        const contratanteNumero = document.getElementById('ic-contratante-numero').value.trim();
        const contratanteTipo = parseInt(document.getElementById('ic-contratante-tipo').value);
        
        const autorNumero = document.getElementById('ic-autor-numero').value.trim();
        const autorTipo = parseInt(document.getElementById('ic-autor-tipo').value);
        
        const contribuinteNumero = document.getElementById('ic-contribuinte-numero').value.trim();
        const contribuinteTipo = parseInt(document.getElementById('ic-contribuinte-tipo').value);
        
        const idSistema = document.getElementById('ic-id-sistema').value.trim();
        const idServico = document.getElementById('ic-id-servico').value.trim();
        const versaoSistema = document.getElementById('ic-versao-sistema').value.trim();
        const dadosJson = document.getElementById('ic-dados-json').value.trim();
        
        // Parsear JSON dos dados
        const dadosObj = JSON.parse(dadosJson);
        
        // Montar payload
        const payload = {
            contratante: {
                numero: contratanteNumero,
                tipo: contratanteTipo
            },
            autorPedidoDados: {
                numero: autorNumero,
                tipo: autorTipo
            },
            contribuinte: {
                numero: contribuinteNumero,
                tipo: contribuinteTipo
            },
            pedidoDados: {
                idSistema: idSistema,
                idServico: idServico,
                versaoSistema: versaoSistema,
                dados: dadosObj
            }
        };
        
        // Enviar para backend
        showToast('⏳ Enviando requisição...', 'info');
        
        const response = await fetch('/api/integra-contador/enviar', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken || ''
            },
            body: JSON.stringify({
                tipoOperacao: window.integraContadorState.tipoOperacao,
                payload: payload
            })
        });
        
        const data = await response.json();
        
        // Exibir resposta
        const respostaDiv = document.getElementById('resposta-integra-contador');
        const respostaJson = document.getElementById('resposta-integra-json');
        
        respostaJson.textContent = JSON.stringify(data, null, 2);
        respostaDiv.style.display = 'block';
        
        // Scroll para a resposta
        respostaDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        if (data.success) {
            showToast('✅ Requisição enviada com sucesso!', 'success');
        } else {
            showToast(`❌ Erro: ${data.error}`, 'error');
        }
        
    } catch (error) {
        console.error('Erro ao enviar requisição:', error);
        showToast(`❌ Erro: ${error.message}`, 'error');
    }
};

/**
 * Copia a resposta para a área de transferência
 */
window.copiarResposta = function() {
    const respostaJson = document.getElementById('resposta-integra-json').textContent;
    
    navigator.clipboard.writeText(respostaJson).then(() => {
        showToast('✅ Resposta copiada!', 'success');
    }).catch(err => {
        console.error('Erro ao copiar:', err);
        showToast('❌ Erro ao copiar', 'error');
    });
};

/**
 * Faz download da resposta como arquivo JSON
 */
window.downloadResposta = function() {
    const respostaJson = document.getElementById('resposta-integra-json').textContent;
    const blob = new Blob([respostaJson], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `integra-contador-${new Date().toISOString()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    showToast('✅ Download iniciado!', 'success');
};

/**
 * Testa conexão com a API
 */
window.testarConexaoIntegra = async function() {
    try {
        showToast('⏳ Testando conexão...', 'info');
        
        const response = await fetch('/api/integra-contador/testar', {
            credentials: 'include',
            headers: {
                'X-CSRFToken': window.csrfToken || ''
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`✅ ${data.message}`, 'success');
        } else {
            showToast(`❌ Erro: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Erro ao testar conexão:', error);
        showToast('❌ Erro ao testar conexão', 'error');
    }
};

// FIM MÓDULO INTEGRA CONTADOR
