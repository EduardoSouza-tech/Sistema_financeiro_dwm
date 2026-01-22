/**
 * ============================================================================
 * LAZY LOADING & VIRTUAL SCROLLING - FASE 7.5
 * ============================================================================
 * Sistema de carregamento progressivo e paginação para listas grandes (100k+)
 * Usa IntersectionObserver para scroll infinito e cache inteligente
 * ============================================================================
 */

// ============================================================================
// CONFIGURAÇÃO DO LAZY LOADER
// ============================================================================

const LazyLoadConfig = {
    PAGE_SIZE: 50,              // Itens por página
    BUFFER_SIZE: 20,            // Itens extras carregados antecipadamente
    CACHE_TTL: 300000,          // 5 minutos em ms
    SCROLL_THRESHOLD: 0.8,      // Carregar quando 80% visível
    MAX_CACHED_PAGES: 10        // Máximo de páginas em cache
};

// ============================================================================
// CACHE DE DADOS
// ============================================================================

class DataCache {
    constructor() {
        this.cache = new Map();
        this.timestamps = new Map();
    }

    set(key, value) {
        this.cache.set(key, value);
        this.timestamps.set(key, Date.now());
        this._cleanup();
    }

    get(key) {
        if (!this.cache.has(key)) return null;
        
        const timestamp = this.timestamps.get(key);
        if (Date.now() - timestamp > LazyLoadConfig.CACHE_TTL) {
            this.cache.delete(key);
            this.timestamps.delete(key);
            return null;
        }
        
        return this.cache.get(key);
    }

    has(key) {
        return this.get(key) !== null;
    }

    clear() {
        this.cache.clear();
        this.timestamps.clear();
    }

    _cleanup() {
        if (this.cache.size <= LazyLoadConfig.MAX_CACHED_PAGES) return;
        
        // Remover páginas mais antigas
        const entries = Array.from(this.timestamps.entries())
            .sort((a, b) => a[1] - b[1]);
        
        const toRemove = entries.slice(0, entries.length - LazyLoadConfig.MAX_CACHED_PAGES);
        toRemove.forEach(([key]) => {
            this.cache.delete(key);
            this.timestamps.delete(key);
        });
    }

    getStats() {
        return {
            size: this.cache.size,
            maxSize: LazyLoadConfig.MAX_CACHED_PAGES,
            keys: Array.from(this.cache.keys())
        };
    }
}

// ============================================================================
// LAZY LOADER PRINCIPAL
// ============================================================================

class LazyLoader {
    constructor(endpoint, renderFunction, containerId) {
        this.endpoint = endpoint;
        this.renderFunction = renderFunction;
        this.containerId = containerId;
        
        this.currentPage = 1;
        this.totalPages = 1;
        this.totalItems = 0;
        this.isLoading = false;
        this.hasMore = true;
        
        this.cache = new DataCache();
        this.observer = null;
        this.sentinel = null;
        
        this.filters = {};
        this.sortBy = null;
        this.sortOrder = 'asc';
    }

    /**
     * Inicializa o lazy loader
     */
    async init(initialFilters = {}) {
        this.filters = initialFilters;
        this.currentPage = 1;
        this.hasMore = true;
        
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container ${this.containerId} não encontrado`);
            return;
        }

        // Limpar conteúdo anterior
        container.innerHTML = '';
        
        // Criar sentinel (elemento que dispara o carregamento)
        this._createSentinel(container);
        
        // Configurar IntersectionObserver
        this._setupObserver();
        
        // Carregar primeira página
        await this.loadPage(1);
    }

    /**
     * Carrega uma página específica
     */
    async loadPage(page) {
        if (this.isLoading || (!this.hasMore && page > 1)) {
            return;
        }

        const cacheKey = this._getCacheKey(page);
        
        // Verificar cache primeiro
        const cached = this.cache.get(cacheKey);
        if (cached) {
            console.log(`📦 Cache HIT: Página ${page}`);
            this._renderPage(cached.items, page);
            this._updatePagination(cached.pagination);
            return;
        }

        this.isLoading = true;
        this._showLoader();

        try {
            const url = this._buildUrl(page);
            console.log(`📡 Carregando página ${page}: ${url}`);
            
            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            
            // Estrutura esperada: { items: [...], pagination: {total, pages, current} }
            const items = Array.isArray(data) ? data : (data.items || data.data || []);
            const pagination = data.pagination || {
                total: items.length,
                pages: 1,
                current: page,
                per_page: items.length
            };

            // Salvar no cache
            this.cache.set(cacheKey, { items, pagination });

            // Renderizar
            this._renderPage(items, page);
            this._updatePagination(pagination);

            console.log(`✅ Página ${page} carregada: ${items.length} itens`);

        } catch (error) {
            console.error(`Erro ao carregar página ${page}:`, error);
            this._showError('Erro ao carregar dados. Tente novamente.');
        } finally {
            this.isLoading = false;
            this._hideLoader();
        }
    }

    /**
     * Carrega próxima página (scroll infinito)
     */
    async loadNext() {
        if (!this.hasMore) return;
        
        this.currentPage++;
        await this.loadPage(this.currentPage);
    }

    /**
     * Atualiza filtros e recarrega
     */
    async updateFilters(newFilters) {
        this.filters = { ...this.filters, ...newFilters };
        this.cache.clear();
        await this.init(this.filters);
    }

    /**
     * Atualiza ordenação
     */
    async updateSort(field, order = 'asc') {
        this.sortBy = field;
        this.sortOrder = order;
        this.cache.clear();
        await this.init(this.filters);
    }

    /**
     * Recarrega dados
     */
    async reload() {
        this.cache.clear();
        await this.init(this.filters);
    }

    // ========================================================================
    // MÉTODOS PRIVADOS
    // ========================================================================

    _getCacheKey(page) {
        const filterStr = JSON.stringify(this.filters);
        const sortStr = `${this.sortBy}-${this.sortOrder}`;
        return `${this.endpoint}-${page}-${filterStr}-${sortStr}`;
    }

    _buildUrl(page) {
        const params = new URLSearchParams({
            page: page,
            per_page: LazyLoadConfig.PAGE_SIZE,
            ...this.filters
        });

        if (this.sortBy) {
            params.set('sort_by', this.sortBy);
            params.set('sort_order', this.sortOrder);
        }

        return `${window.CONFIG.API_URL}${this.endpoint}?${params.toString()}`;
    }

    _renderPage(items, page) {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // Se for primeira página, limpar container E recriar sentinel
        if (page === 1) {
            container.innerHTML = '';
            // Recriar sentinel após limpar
            this._createSentinel(container);
        }

        // Renderizar items
        items.forEach(item => {
            const element = this.renderFunction(item);
            if (element) {
                // Inserir antes do sentinel
                container.insertBefore(element, this.sentinel);
            }
        });

        // Mensagem se vazio
        if (page === 1 && items.length === 0) {
            container.innerHTML = `
                <tr><td colspan="10" style="text-align: center; padding: 30px;">
                    📭 Nenhum registro encontrado
                </td></tr>
            `;
        }
    }

    _updatePagination(pagination) {
        this.totalItems = pagination.total || 0;
        this.totalPages = pagination.pages || 1;
        this.currentPage = pagination.current || 1;
        this.hasMore = this.currentPage < this.totalPages;

        // Atualizar UI de paginação se existir
        this._updatePaginationUI();
    }

    _updatePaginationUI() {
        const paginationContainer = document.getElementById(`${this.containerId}-pagination`);
        if (!paginationContainer) return;

        paginationContainer.innerHTML = `
            <div class="pagination-info">
                Página ${this.currentPage} de ${this.totalPages} 
                (${this.totalItems} itens no total)
            </div>
        `;
    }

    _createSentinel(container) {
        this.sentinel = document.createElement('tr');
        this.sentinel.id = `${this.containerId}-sentinel`;
        this.sentinel.style.height = '1px';
        this.sentinel.innerHTML = '<td colspan="10"></td>';
        container.appendChild(this.sentinel);
    }

    _setupObserver() {
        const options = {
            root: null,
            rootMargin: '200px', // Carregar antes de chegar no final
            threshold: 0.1
        };

        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !this.isLoading && this.hasMore) {
                    console.log('🔄 Sentinel visível - carregando próxima página...');
                    this.loadNext();
                }
            });
        }, options);

        if (this.sentinel) {
            this.observer.observe(this.sentinel);
        }
    }

    _showLoader() {
        const loader = document.getElementById(`${this.containerId}-loader`);
        if (loader) {
            loader.style.display = 'block';
        } else {
            // Criar loader se não existir
            const container = document.getElementById(this.containerId);
            if (container && container.parentElement) {
                const loaderDiv = document.createElement('div');
                loaderDiv.id = `${this.containerId}-loader`;
                loaderDiv.className = 'lazy-loader';
                loaderDiv.innerHTML = '⏳ Carregando...';
                container.parentElement.appendChild(loaderDiv);
            }
        }
    }

    _hideLoader() {
        const loader = document.getElementById(`${this.containerId}-loader`);
        if (loader) {
            loader.style.display = 'none';
        }
    }

    _showError(message) {
        if (typeof showNotification === 'function') {
            showNotification(message, 'error');
        } else {
            alert(message);
        }
    }

    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
        this.cache.clear();
    }
}

// ============================================================================
// INSTÂNCIAS GLOBAIS DOS LOADERS
// ============================================================================

const LazyLoaders = {
    lancamentos: null,
    contasReceber: null,
    contasPagar: null,
    clientes: null,
    fornecedores: null
};

// ============================================================================
// FUNÇÕES DE RENDERIZAÇÃO (para cada tipo de lista)
// ============================================================================

function renderLancamento(lanc) {
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
    return tr;
}

function renderContaReceber(lanc) {
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
    return tr;
}

function renderContaPagar(lanc) {
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
    return tr;
}

// ============================================================================
// FUNÇÕES DE INICIALIZAÇÃO (substituem as loadXXX antigas)
// ============================================================================

/**
 * Carrega contas a receber com lazy loading
 */
async function loadContasReceberLazy(filters = {}) {
    // Destruir loader anterior se existir
    if (LazyLoaders.contasReceber) {
        LazyLoaders.contasReceber.destroy();
    }

    // Criar novo loader
    LazyLoaders.contasReceber = new LazyLoader(
        '/lancamentos',
        renderContaReceber,
        'tbody-receber'
    );

    // Adicionar filtro de tipo
    filters.tipo = 'RECEITA';

    // Inicializar
    await LazyLoaders.contasReceber.init(filters);
}

/**
 * Carrega contas a pagar com lazy loading
 */
async function loadContasPagarLazy(filters = {}) {
    if (LazyLoaders.contasPagar) {
        LazyLoaders.contasPagar.destroy();
    }

    LazyLoaders.contasPagar = new LazyLoader(
        '/lancamentos',
        renderContaPagar,
        'tbody-pagar'
    );

    filters.tipo = 'DESPESA';
    await LazyLoaders.contasPagar.init(filters);
}

/**
 * Carrega lançamentos com lazy loading
 */
async function loadLancamentosLazy(filters = {}) {
    if (LazyLoaders.lancamentos) {
        LazyLoaders.lancamentos.destroy();
    }

    LazyLoaders.lancamentos = new LazyLoader(
        '/lancamentos',
        renderLancamento,
        'tbody-lancamentos'
    );

    await LazyLoaders.lancamentos.init(filters);
}

// ============================================================================
// EXPORTAR PARA USO GLOBAL
// ============================================================================

console.log('✅ Lazy Loading Module carregado (Fase 7.5)');
