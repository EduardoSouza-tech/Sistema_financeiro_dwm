/**
 * ============================================================================
 * INTEGRAÇÃO LAZY LOADING - FASE 7.5
 * ============================================================================
 * Patch para integrar o lazy-loader.js com as funções existentes do app.js
 * Adicione este código ao final do app.js ou carregue separadamente
 * ============================================================================
 */

// Flag para ativar/desativar lazy loading
const LAZY_LOADING_ENABLED = true;

// ============================================================================
// SUBSTITUIR FUNÇÕES ANTIGAS POR VERSÕES COM LAZY LOADING
// ============================================================================

/**
 * Substitui loadContasReceber pela versão com lazy loading
 */
const loadContasReceberOriginal = typeof loadContasReceber !== 'undefined' ? loadContasReceber : null;

async function loadContasReceber() {
    if (LAZY_LOADING_ENABLED && typeof loadContasReceberLazy !== 'undefined') {
        console.log('⚡ Usando lazy loading para Contas a Receber');
        
        // Obter filtros atuais
        const filterText = document.getElementById('filter-receber')?.value || '';
        const filterStatus = document.getElementById('filter-status-receber')?.value || '';
        
        const filters = {};
        if (filterText) filters.search = filterText;
        if (filterStatus) filters.status = filterStatus;
        
        await loadContasReceberLazy(filters);
        
        // Atualizar saldo e selects
        await window.atualizarSaldoTotalBancos('receber');
        await window.carregarSelectBancos('receber');
    } else if (loadContasReceberOriginal) {
        console.log('📊 Usando carregamento tradicional para Contas a Receber');
        await loadContasReceberOriginal();
    } else {
        console.error('❌ Nenhuma função de carregamento disponível para Contas a Receber');
    }
}

/**
 * Substitui loadContasPagar pela versão com lazy loading
 */
const loadContasPagarOriginal = typeof loadContasPagar !== 'undefined' ? loadContasPagar : null;

async function loadContasPagar() {
    if (LAZY_LOADING_ENABLED && typeof loadContasPagarLazy !== 'undefined') {
        console.log('⚡ Usando lazy loading para Contas a Pagar');
        
        const filterText = document.getElementById('filter-pagar')?.value || '';
        const filterStatus = document.getElementById('filter-status-pagar')?.value || '';
        
        const filters = {};
        if (filterText) filters.search = filterText;
        if (filterStatus) filters.status = filterStatus;
        
        await loadContasPagarLazy(filters);
        
        await window.atualizarSaldoTotalBancos('pagar');
        await window.carregarSelectBancos('pagar');
    } else if (loadContasPagarOriginal) {
        console.log('📊 Usando carregamento tradicional para Contas a Pagar');
        await loadContasPagarOriginal();
    } else {
        console.error('❌ Nenhuma função de carregamento disponível para Contas a Pagar');
    }
}

/**
 * Substitui loadLancamentos pela versão com lazy loading
 */
const loadLancamentosOriginal = typeof loadLancamentos !== 'undefined' ? loadLancamentos : null;

async function loadLancamentos() {
    if (LAZY_LOADING_ENABLED && typeof loadLancamentosLazy !== 'undefined') {
        console.log('⚡ Usando lazy loading para Lançamentos');
        await loadLancamentosLazy();
    } else if (loadLancamentosOriginal) {
        console.log('📊 Usando carregamento tradicional para Lançamentos');
        await loadLancamentosOriginal();
    } else {
        console.error('❌ Nenhuma função de carregamento disponível para Lançamentos');
    }
}

// ============================================================================
// EVENT LISTENERS PARA FILTROS
// ============================================================================

/**
 * Adiciona listeners para filtros de Contas a Receber
 */
function setupFiltrosReceber() {
    const filterInput = document.getElementById('filter-receber');
    const filterStatus = document.getElementById('filter-status-receber');
    
    if (filterInput) {
        filterInput.addEventListener('input', debounce(() => {
            if (LAZY_LOADING_ENABLED && LazyLoaders.contasReceber) {
                const filters = {
                    search: filterInput.value,
                    status: filterStatus?.value || ''
                };
                LazyLoaders.contasReceber.updateFilters(filters);
            } else {
                loadContasReceber();
            }
        }, 500));
    }
    
    if (filterStatus) {
        filterStatus.addEventListener('change', () => {
            if (LAZY_LOADING_ENABLED && LazyLoaders.contasReceber) {
                const filters = {
                    search: filterInput?.value || '',
                    status: filterStatus.value
                };
                LazyLoaders.contasReceber.updateFilters(filters);
            } else {
                loadContasReceber();
            }
        });
    }
}

/**
 * Adiciona listeners para filtros de Contas a Pagar
 */
function setupFiltrosPagar() {
    const filterInput = document.getElementById('filter-pagar');
    const filterStatus = document.getElementById('filter-status-pagar');
    
    if (filterInput) {
        filterInput.addEventListener('input', debounce(() => {
            if (LAZY_LOADING_ENABLED && LazyLoaders.contasPagar) {
                const filters = {
                    search: filterInput.value,
                    status: filterStatus?.value || ''
                };
                LazyLoaders.contasPagar.updateFilters(filters);
            } else {
                loadContasPagar();
            }
        }, 500));
    }
    
    if (filterStatus) {
        filterStatus.addEventListener('change', () => {
            if (LAZY_LOADING_ENABLED && LazyLoaders.contasPagar) {
                const filters = {
                    search: filterInput?.value || '',
                    status: filterStatus.value
                };
                LazyLoaders.contasPagar.updateFilters(filters);
            } else {
                loadContasPagar();
            }
        });
    }
}

/**
 * Debounce helper
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============================================================================
// INICIALIZAÇÃO
// ============================================================================

// Executar quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLazyLoadingIntegration);
} else {
    initLazyLoadingIntegration();
}

function initLazyLoadingIntegration() {
    console.log('🚀 Inicializando integração Lazy Loading...');
    
    // Aguardar um pouco para garantir que app.js carregou
    setTimeout(() => {
        setupFiltrosReceber();
        setupFiltrosPagar();
        
        if (LAZY_LOADING_ENABLED) {
            console.log('✅ Lazy Loading ATIVADO - Performance otimizada');
            console.log('   📊 Cache configurado:', LazyLoadConfig);
        } else {
            console.log('📊 Lazy Loading DESATIVADO - Usando carregamento tradicional');
        }
    }, 500);
}

// ============================================================================
// FUNÇÕES DE UTILIDADE
// ============================================================================

/**
 * Recarrega dados com lazy loading
 */
function reloadLazyData(tipo) {
    if (!LAZY_LOADING_ENABLED) return;
    
    switch(tipo) {
        case 'receber':
            if (LazyLoaders.contasReceber) {
                LazyLoaders.contasReceber.reload();
            }
            break;
        case 'pagar':
            if (LazyLoaders.contasPagar) {
                LazyLoaders.contasPagar.reload();
            }
            break;
        case 'lancamentos':
            if (LazyLoaders.lancamentos) {
                LazyLoaders.lancamentos.reload();
            }
            break;
    }
}

/**
 * Limpa cache do lazy loading
 */
function clearLazyCache() {
    if (!LAZY_LOADING_ENABLED) return;
    
    Object.values(LazyLoaders).forEach(loader => {
        if (loader && loader.cache) {
            loader.cache.clear();
        }
    });
    
    console.log('🗑️ Cache do Lazy Loading limpo');
}

/**
 * Exibe estatísticas do cache
 */
function showLazyCacheStats() {
    if (!LAZY_LOADING_ENABLED) {
        console.log('Lazy Loading desativado');
        return;
    }
    
    console.log('📊 Estatísticas do Cache Lazy Loading:');
    
    Object.entries(LazyLoaders).forEach(([nome, loader]) => {
        if (loader && loader.cache) {
            const stats = loader.cache.getStats();
            console.log(`   ${nome}:`, stats);
        }
    });
}

// Expor no console para debug
window.lazyLoadingDebug = {
    enable: () => { LAZY_LOADING_ENABLED = true; console.log('✅ Lazy Loading ATIVADO'); },
    disable: () => { LAZY_LOADING_ENABLED = false; console.log('❌ Lazy Loading DESATIVADO'); },
    reload: reloadLazyData,
    clearCache: clearLazyCache,
    stats: showLazyCacheStats,
    loaders: LazyLoaders
};

console.log('✅ Integração Lazy Loading carregada');
console.log('💡 Use window.lazyLoadingDebug para controlar o sistema');
