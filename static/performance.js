/**
 * Sistema de Cache e Otimizações de Performance
 * Reduz requisições repetidas e melhora tempo de carregamento
 */

// ===== SISTEMA DE CACHE =====
const AppCache = {
    data: {},
    timestamps: {},
    config: {
        categorias: { ttl: 300000 }, // 5 minutos
        clientes: { ttl: 180000 },   // 3 minutos
        fornecedores: { ttl: 180000 },
        contas: { ttl: 300000 },
        lancamentos: { ttl: 60000 }  // 1 minuto (dados mais dinâmicos)
    },

    get(key) {
        const now = Date.now();
        const cached = this.data[key];
        const timestamp = this.timestamps[key];
        
        if (!cached || !timestamp) return null;
        
        // Verificar se cache está válido
        const config = this.config[key] || { ttl: 60000 };
        if (now - timestamp > config.ttl) {
            delete this.data[key];
            delete this.timestamps[key];
            return null;
        }
        
        console.log(`✓ Cache HIT: ${key}`);
        return cached;
    },

    set(key, value) {
        this.data[key] = value;
        this.timestamps[key] = Date.now();
        console.log(`✓ Cache SET: ${key}`);
    },

    invalidate(key) {
        delete this.data[key];
        delete this.timestamps[key];
        console.log(`✓ Cache INVALIDATE: ${key}`);
    },

    invalidateAll() {
        this.data = {};
        this.timestamps = {};
        console.log('✓ Cache CLEARED');
    }
};

// ===== FUNÇÕES OTIMIZADAS DE API =====

/**
 * Fetch com cache automático
 */
async function cachedFetch(url, cacheKey = null, options = {}) {
    const key = cacheKey || url;
    
    // Apenas GET pode usar cache
    if (!options.method || options.method === 'GET') {
        const cached = AppCache.get(key);
        if (cached) return cached;
    }
    
    try {
        const response = await fetch(url, options);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        // Salvar em cache se for GET
        if (!options.method || options.method === 'GET') {
            AppCache.set(key, data);
        }
        
        return data;
    } catch (error) {
        console.error(`Erro em cachedFetch(${url}):`, error);
        throw error;
    }
}

/**
 * Carregar dados em paralelo
 */
async function carregarDadosIniciais() {
    console.log('⏳ Carregando dados iniciais em paralelo...');
    
    try {
        const [categorias, clientes, fornecedores, contas] = await Promise.all([
            cachedFetch('/api/categorias', 'categorias'),
            cachedFetch('/api/clientes?ativos=true', 'clientes'),
            cachedFetch('/api/fornecedores?ativos=true', 'fornecedores'),
            cachedFetch('/api/contas', 'contas')
        ]);
        
        // Armazenar em variáveis globais se necessário
        window.categoriasCache = categorias;
        window.clientesCache = clientes;
        window.fornecedoresCache = fornecedores;
        window.contasCache = contas;
        
        console.log('✅ Dados iniciais carregados');
        return { categorias, clientes, fornecedores, contas };
    } catch (error) {
        console.error('❌ Erro ao carregar dados iniciais:', error);
        throw error;
    }
}

// ===== DEBOUNCE E THROTTLE =====

/**
 * Debounce - Executa função após delay de inatividade
 */
function debounce(func, wait = 300) {
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

/**
 * Throttle - Limita execução a uma vez por intervalo
 */
function throttle(func, limit = 300) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ===== LAZY LOADING DE IMAGENS =====

function setupLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// ===== PAGINAÇÃO DE TABELAS =====

class TablePagination {
    constructor(data, pageSize = 50) {
        this.data = data;
        this.pageSize = pageSize;
        this.currentPage = 1;
        this.totalPages = Math.ceil(data.length / pageSize);
    }

    getPage(page = this.currentPage) {
        const start = (page - 1) * this.pageSize;
        const end = start + this.pageSize;
        return this.data.slice(start, end);
    }

    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            return this.getPage();
        }
        return null;
    }

    prevPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            return this.getPage();
        }
        return null;
    }

    goToPage(page) {
        if (page >= 1 && page <= this.totalPages) {
            this.currentPage = page;
            return this.getPage();
        }
        return null;
    }
}

// ===== VIRTUAL SCROLL PARA LISTAS GRANDES =====

class VirtualScroll {
    constructor(container, items, rowHeight = 50) {
        this.container = container;
        this.items = items;
        this.rowHeight = rowHeight;
        this.visibleCount = Math.ceil(container.clientHeight / rowHeight) + 5;
        this.scrollTop = 0;
        
        this.init();
    }

    init() {
        this.container.style.overflowY = 'scroll';
        this.container.style.position = 'relative';
        
        // Criar espaçador para scroll
        const spacer = document.createElement('div');
        spacer.style.height = `${this.items.length * this.rowHeight}px`;
        this.container.appendChild(spacer);
        
        // Listener de scroll
        this.container.addEventListener('scroll', throttle(() => {
            this.scrollTop = this.container.scrollTop;
            this.render();
        }, 50));
        
        this.render();
    }

    render() {
        const startIndex = Math.floor(this.scrollTop / this.rowHeight);
        const endIndex = Math.min(startIndex + this.visibleCount, this.items.length);
        
        // Limpar itens anteriores
        const oldItems = this.container.querySelectorAll('.virtual-item');
        oldItems.forEach(item => item.remove());
        
        // Renderizar itens visíveis
        for (let i = startIndex; i < endIndex; i++) {
            const item = this.createItemElement(this.items[i], i);
            item.style.position = 'absolute';
            item.style.top = `${i * this.rowHeight}px`;
            item.classList.add('virtual-item');
            this.container.appendChild(item);
        }
    }

    createItemElement(data, index) {
        // Override este método para criar elementos customizados
        const div = document.createElement('div');
        div.textContent = JSON.stringify(data);
        return div;
    }
}

// ===== PRELOAD DE SEÇÕES =====

const preloadedSections = new Set();

function preloadSection(sectionName) {
    if (preloadedSections.has(sectionName)) {
        console.log(`✓ Seção ${sectionName} já carregada`);
        return;
    }
    
    console.log(`⏳ Preload: ${sectionName}`);
    
    // Carregar dados da seção em background
    switch(sectionName) {
        case 'dashboard':
            cachedFetch('/api/lancamentos?tipo=RECEITA', 'lancamentos_receita');
            cachedFetch('/api/lancamentos?tipo=DESPESA', 'lancamentos_despesa');
            break;
        case 'inadimplencia':
            cachedFetch('/api/lancamentos?tipo=receita&status=pendente', 'lancamentos_inadimplentes');
            break;
        case 'indicadores':
            cachedFetch('/api/lancamentos', 'lancamentos_all');
            break;
    }
    
    preloadedSections.add(sectionName);
}

// ===== OPTIMIZAÇÃO DE RENDERIZAÇÃO =====

/**
 * Batch DOM updates para evitar reflows
 */
function batchDOMUpdates(updates) {
    requestAnimationFrame(() => {
        updates.forEach(update => update());
    });
}

/**
 * Criar fragmento de documento para inserções múltiplas
 */
function createTableRows(data, createRowFn) {
    const fragment = document.createDocumentFragment();
    data.forEach(item => {
        const row = createRowFn(item);
        fragment.appendChild(row);
    });
    return fragment;
}

// ===== WEB WORKER PARA CÁLCULOS PESADOS =====

function createCalculationWorker() {
    const workerCode = `
        self.onmessage = function(e) {
            const { type, data } = e.data;
            
            switch(type) {
                case 'calcularIndicadores':
                    const result = calcularIndicadores(data);
                    self.postMessage({ type: 'indicadores', result });
                    break;
                    
                case 'filtrarLancamentos':
                    const filtered = filtrarLancamentos(data.lancamentos, data.filtros);
                    self.postMessage({ type: 'lancamentos', result: filtered });
                    break;
            }
        };
        
        function calcularIndicadores(lancamentos) {
            let totalReceitas = 0;
            let totalDespesas = 0;
            
            lancamentos.forEach(lanc => {
                if (lanc.tipo.toLowerCase() === 'receita') {
                    totalReceitas += parseFloat(lanc.valor);
                } else if (lanc.tipo.toLowerCase() === 'despesa') {
                    totalDespesas += parseFloat(lanc.valor);
                }
            });
            
            return {
                totalReceitas,
                totalDespesas,
                saldo: totalReceitas - totalDespesas,
                margemLucro: totalReceitas > 0 ? ((totalReceitas - totalDespesas) / totalReceitas * 100) : 0
            };
        }
        
        function filtrarLancamentos(lancamentos, filtros) {
            return lancamentos.filter(lanc => {
                if (filtros.tipo && lanc.tipo.toLowerCase() !== filtros.tipo.toLowerCase()) {
                    return false;
                }
                if (filtros.status && lanc.status.toLowerCase() !== filtros.status.toLowerCase()) {
                    return false;
                }
                if (filtros.dataInicio && lanc.data < filtros.dataInicio) {
                    return false;
                }
                if (filtros.dataFim && lanc.data > filtros.dataFim) {
                    return false;
                }
                return true;
            });
        }
    `;
    
    const blob = new Blob([workerCode], { type: 'application/javascript' });
    return new Worker(URL.createObjectURL(blob));
}

// ===== INICIALIZAÇÃO =====

// Carregar dados iniciais quando página carrega
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('🚀 Sistema de otimizações carregado');
        carregarDadosIniciais();
        setupLazyLoading();
        
        // Preload das seções mais usadas
        setTimeout(() => {
            preloadSection('dashboard');
            preloadSection('inadimplencia');
        }, 2000);
    });
} else {
    console.log('🚀 Sistema de otimizações carregado');
    carregarDadosIniciais();
    setupLazyLoading();
}

// Exportar para uso global
window.AppCache = AppCache;
window.cachedFetch = cachedFetch;
window.debounce = debounce;
window.throttle = throttle;
window.TablePagination = TablePagination;
window.VirtualScroll = VirtualScroll;
window.preloadSection = preloadSection;
window.batchDOMUpdates = batchDOMUpdates;
window.createTableRows = createTableRows;
window.carregarDadosIniciais = carregarDadosIniciais;

console.log('%c ✓ Performance Module Loaded ', 'background: #2ecc71; color: white; font-weight: bold; padding: 5px');
