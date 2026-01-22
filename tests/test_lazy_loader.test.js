/**
 * Testes para Lazy Loader - Sistema de Carregamento Progressivo
 * 
 * Testa comportamento crítico identificado nos últimos commits:
 * - Fix do sentinel após limpar container (commit a1ef342)
 * - Comportamento de primeira página vazia
 * - Limpeza e recriação de elementos DOM
 */

describe('Lazy Loader - Sistema de Carregamento Progressivo', () => {
    
    let container;
    let loader;
    let mockFetch;
    
    beforeEach(() => {
        // Setup DOM
        container = document.createElement('tbody');
        container.id = 'test-container';
        document.body.appendChild(container);
        
        // Mock window.CONFIG
        window.CONFIG = {
            API_URL: 'http://localhost:5000'
        };
        
        // Mock fetch
        mockFetch = jest.spyOn(global, 'fetch');
    });
    
    afterEach(() => {
        if (loader) {
            loader.destroy();
        }
        document.body.removeChild(container);
        mockFetch.mockRestore();
    });
    
    describe('Inicialização e Sentinel', () => {
        
        test('deve criar sentinel na inicialização', async () => {
            // Arrange
            mockFetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    items: [],
                    pagination: { total: 0, pages: 1, current: 1 }
                })
            });
            
            const renderFn = jest.fn();
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            
            // Act
            await loader.init();
            
            // Assert
            const sentinel = document.getElementById('test-container-sentinel');
            expect(sentinel).toBeTruthy();
            expect(sentinel.tagName).toBe('TR');
            expect(sentinel.style.height).toBe('1px');
        });
        
        test('deve recriar sentinel após limpar container na página 1 - FIX commit a1ef342', async () => {
            // Arrange - Primeira carga
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    items: [{ id: 1, name: 'Item 1' }],
                    pagination: { total: 1, pages: 1, current: 1 }
                })
            });
            
            const renderFn = jest.fn((item) => {
                const tr = document.createElement('tr');
                tr.textContent = item.name;
                return tr;
            });
            
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            await loader.init();
            
            // Verificar que sentinel existe após primeira carga
            let sentinel = document.getElementById('test-container-sentinel');
            expect(sentinel).toBeTruthy();
            const firstSentinel = sentinel;
            
            // Act - Recarregar página 1 (limpa container)
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    items: [{ id: 2, name: 'Item 2' }],
                    pagination: { total: 1, pages: 1, current: 1 }
                })
            });
            
            await loader.loadPage(1);
            
            // Assert - Sentinel deve existir e ser novo
            sentinel = document.getElementById('test-container-sentinel');
            expect(sentinel).toBeTruthy();
            expect(sentinel).not.toBe(firstSentinel); // Deve ser um novo elemento
            expect(container.contains(sentinel)).toBe(true);
        });
        
        test('deve inserir itens ANTES do sentinel', async () => {
            // Arrange
            mockFetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    items: [
                        { id: 1, name: 'Item 1' },
                        { id: 2, name: 'Item 2' }
                    ],
                    pagination: { total: 2, pages: 1, current: 1 }
                })
            });
            
            const renderFn = (item) => {
                const tr = document.createElement('tr');
                tr.className = 'data-row';
                tr.textContent = item.name;
                return tr;
            };
            
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            
            // Act
            await loader.init();
            
            // Assert
            const sentinel = document.getElementById('test-container-sentinel');
            const dataRows = container.querySelectorAll('.data-row');
            
            expect(dataRows.length).toBe(2);
            expect(sentinel).toBe(container.lastElementChild); // Sentinel deve ser o último
            expect(dataRows[0].nextElementSibling).toBe(dataRows[1]);
            expect(dataRows[1].nextElementSibling).toBe(sentinel);
        });
    });
    
    describe('Comportamento com Lista Vazia', () => {
        
        test('deve mostrar mensagem quando página 1 está vazia', async () => {
            // Arrange
            mockFetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    items: [],
                    pagination: { total: 0, pages: 1, current: 1 }
                })
            });
            
            const renderFn = jest.fn();
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            
            // Act
            await loader.init();
            
            // Assert
            expect(container.innerHTML).toContain('Nenhum registro encontrado');
            expect(container.innerHTML).toContain('📭');
        });
        
        test('não deve adicionar itens depois de lista vazia na página 2+', async () => {
            // Arrange - Página 1 com dados
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    items: [{ id: 1, name: 'Item 1' }],
                    pagination: { total: 1, pages: 2, current: 1 }
                })
            });
            
            const renderFn = (item) => {
                const tr = document.createElement('tr');
                tr.className = 'data-row';
                return tr;
            };
            
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            await loader.init();
            
            const rowsAfterPage1 = container.querySelectorAll('.data-row').length;
            expect(rowsAfterPage1).toBe(1);
            
            // Act - Página 2 vazia
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    items: [],
                    pagination: { total: 1, pages: 2, current: 2 }
                })
            });
            
            await loader.loadPage(2);
            
            // Assert - Não deve remover itens existentes
            const rowsAfterPage2 = container.querySelectorAll('.data-row').length;
            expect(rowsAfterPage2).toBe(1);
            expect(container.innerHTML).not.toContain('Nenhum registro encontrado');
        });
    });
    
    describe('Cache de Dados', () => {
        
        test('deve cachear página carregada', async () => {
            // Arrange
            mockFetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    items: [{ id: 1, name: 'Item 1' }],
                    pagination: { total: 1, pages: 1, current: 1 }
                })
            });
            
            const renderFn = jest.fn();
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            
            // Act - Primeira carga
            await loader.loadPage(1);
            expect(mockFetch).toHaveBeenCalledTimes(1);
            
            // Act - Segunda carga (deve usar cache)
            await loader.loadPage(1);
            
            // Assert
            expect(mockFetch).toHaveBeenCalledTimes(1); // Não deve fazer nova requisição
        });
        
        test('deve limpar cache ao recarregar', async () => {
            // Arrange
            mockFetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    items: [],
                    pagination: { total: 0, pages: 1, current: 1 }
                })
            });
            
            const renderFn = jest.fn();
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            
            // Act
            await loader.loadPage(1);
            const cacheStatsBefore = loader.cache.getStats();
            
            await loader.reload();
            const cacheStatsAfter = loader.cache.getStats();
            
            // Assert
            expect(cacheStatsBefore.size).toBeGreaterThan(0);
            expect(cacheStatsAfter.size).toBe(0);
        });
        
        test('deve limpar cache ao atualizar filtros', async () => {
            // Arrange
            mockFetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    items: [],
                    pagination: { total: 0, pages: 1, current: 1 }
                })
            });
            
            const renderFn = jest.fn();
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            await loader.init();
            
            // Act
            await loader.updateFilters({ status: 'ativo' });
            
            // Assert
            expect(loader.cache.getStats().size).toBe(1); // Apenas nova busca no cache
        });
    });
    
    describe('IntersectionObserver e Scroll Infinito', () => {
        
        test('deve configurar observer para sentinel', async () => {
            // Arrange
            const observeMock = jest.fn();
            global.IntersectionObserver = jest.fn(function(callback, options) {
                this.observe = observeMock;
                this.disconnect = jest.fn();
            });
            
            mockFetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    items: [],
                    pagination: { total: 0, pages: 1, current: 1 }
                })
            });
            
            const renderFn = jest.fn();
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            
            // Act
            await loader.init();
            
            // Assert
            expect(IntersectionObserver).toHaveBeenCalled();
            expect(observeMock).toHaveBeenCalledWith(loader.sentinel);
        });
        
        test('não deve carregar próxima página se já estiver carregando', async () => {
            // Arrange
            mockFetch.mockResolvedValue(new Promise(resolve => setTimeout(() => {
                resolve({
                    ok: true,
                    json: async () => ({
                        items: [],
                        pagination: { total: 0, pages: 2, current: 1 }
                    })
                });
            }, 100)));
            
            const renderFn = jest.fn();
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            
            // Act - Tentar carregar duas vezes simultâneo
            const promise1 = loader.loadNext();
            const promise2 = loader.loadNext();
            
            await Promise.all([promise1, promise2]);
            
            // Assert
            expect(mockFetch).toHaveBeenCalledTimes(1); // Apenas uma chamada
        });
    });
    
    describe('Tratamento de Erros', () => {
        
        test('deve mostrar erro quando API falha', async () => {
            // Arrange
            mockFetch.mockRejectedValue(new Error('Network error'));
            
            const renderFn = jest.fn();
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            
            // Mock showNotification
            global.showNotification = jest.fn();
            
            // Act
            await loader.init();
            
            // Assert
            expect(global.showNotification).toHaveBeenCalledWith(
                expect.stringContaining('Erro ao carregar dados'),
                'error'
            );
        });
        
        test('deve parar de carregar após erro', async () => {
            // Arrange
            mockFetch.mockRejectedValue(new Error('Server error'));
            
            const renderFn = jest.fn();
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            
            // Act
            await loader.init();
            
            // Assert
            expect(loader.isLoading).toBe(false);
        });
    });
    
    describe('Cleanup e Destroy', () => {
        
        test('deve desconectar observer ao destruir', async () => {
            // Arrange
            const disconnectMock = jest.fn();
            global.IntersectionObserver = jest.fn(function() {
                this.observe = jest.fn();
                this.disconnect = disconnectMock;
            });
            
            mockFetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    items: [],
                    pagination: { total: 0, pages: 1, current: 1 }
                })
            });
            
            const renderFn = jest.fn();
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            await loader.init();
            
            // Act
            loader.destroy();
            
            // Assert
            expect(disconnectMock).toHaveBeenCalled();
        });
        
        test('deve limpar cache ao destruir', async () => {
            // Arrange
            mockFetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    items: [{ id: 1 }],
                    pagination: { total: 1, pages: 1, current: 1 }
                })
            });
            
            const renderFn = jest.fn();
            loader = new LazyLoader('/api/test', renderFn, 'test-container');
            await loader.init();
            
            expect(loader.cache.getStats().size).toBeGreaterThan(0);
            
            // Act
            loader.destroy();
            
            // Assert
            expect(loader.cache.getStats().size).toBe(0);
        });
    });
});


describe('DataCache - Sistema de Cache', () => {
    
    let cache;
    
    beforeEach(() => {
        cache = new DataCache();
    });
    
    test('deve armazenar e recuperar dados', () => {
        cache.set('key1', { data: 'value1' });
        const result = cache.get('key1');
        
        expect(result).toEqual({ data: 'value1' });
    });
    
    test('deve expirar dados após TTL', (done) => {
        // Mock Date.now
        const realDateNow = Date.now;
        let mockTime = 1000000;
        
        Date.now = jest.fn(() => mockTime);
        
        cache.set('key1', { data: 'value1' });
        expect(cache.get('key1')).toBeTruthy();
        
        // Avançar tempo além do TTL (5 minutos = 300000ms)
        mockTime += 300001;
        
        expect(cache.get('key1')).toBeNull();
        
        Date.now = realDateNow;
        done();
    });
    
    test('deve limpar páginas antigas quando exceder MAX_CACHED_PAGES', () => {
        // Adicionar mais páginas que o máximo
        for (let i = 1; i <= 12; i++) {
            cache.set(`page${i}`, { data: `data${i}` });
        }
        
        const stats = cache.getStats();
        expect(stats.size).toBeLessThanOrEqual(LazyLoadConfig.MAX_CACHED_PAGES);
    });
    
    test('deve retornar stats corretos', () => {
        cache.set('key1', { data: 1 });
        cache.set('key2', { data: 2 });
        
        const stats = cache.getStats();
        
        expect(stats.size).toBe(2);
        expect(stats.maxSize).toBe(LazyLoadConfig.MAX_CACHED_PAGES);
        expect(stats.keys).toContain('key1');
        expect(stats.keys).toContain('key2');
    });
});
