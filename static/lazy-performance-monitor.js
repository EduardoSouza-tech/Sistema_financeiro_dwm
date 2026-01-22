/**
 * ============================================================================
 * LAZY LOADING PERFORMANCE MONITOR
 * ============================================================================
 * Sistema de monitoramento e análise de performance do lazy loading
 * Coleta métricas em tempo real e gera relatórios
 * ============================================================================
 */

class LazyLoadPerformanceMonitor {
    constructor() {
        this.metrics = {
            pageLoads: [],
            cacheHits: 0,
            cacheMisses: 0,
            errors: [],
            renderTimes: [],
            scrollEvents: 0,
            networkRequests: []
        };
        
        this.startTime = Date.now();
        this.enabled = true;
    }

    /**
     * Registra carregamento de página
     */
    logPageLoad(page, duration, fromCache, itemCount) {
        if (!this.enabled) return;
        
        this.metrics.pageLoads.push({
            page,
            duration,
            fromCache,
            itemCount,
            timestamp: Date.now()
        });
        
        if (fromCache) {
            this.metrics.cacheHits++;
        } else {
            this.metrics.cacheMisses++;
            this.metrics.networkRequests.push({
                page,
                duration,
                timestamp: Date.now()
            });
        }
    }

    /**
     * Registra tempo de renderização
     */
    logRenderTime(itemCount, duration) {
        if (!this.enabled) return;
        
        this.metrics.renderTimes.push({
            itemCount,
            duration,
            timestamp: Date.now()
        });
    }

    /**
     * Registra erro
     */
    logError(page, error, context = {}) {
        if (!this.enabled) return;
        
        this.metrics.errors.push({
            page,
            error: error.message || String(error),
            stack: error.stack,
            context,
            timestamp: Date.now()
        });
    }

    /**
     * Registra evento de scroll
     */
    logScrollEvent() {
        if (!this.enabled) return;
        this.metrics.scrollEvents++;
    }

    /**
     * Gera relatório de performance
     */
    generateReport() {
        const totalTime = Date.now() - this.startTime;
        const totalPages = this.metrics.pageLoads.length;
        const totalItems = this.metrics.pageLoads.reduce((sum, p) => sum + p.itemCount, 0);
        
        // Calcular médias
        const avgLoadTime = totalPages > 0
            ? this.metrics.pageLoads.reduce((sum, p) => sum + p.duration, 0) / totalPages
            : 0;
        
        const avgRenderTime = this.metrics.renderTimes.length > 0
            ? this.metrics.renderTimes.reduce((sum, r) => sum + r.duration, 0) / this.metrics.renderTimes.length
            : 0;
        
        // Taxa de cache
        const totalCacheAttempts = this.metrics.cacheHits + this.metrics.cacheMisses;
        const cacheHitRate = totalCacheAttempts > 0
            ? (this.metrics.cacheHits / totalCacheAttempts * 100).toFixed(2)
            : 0;
        
        // Network performance
        const avgNetworkTime = this.metrics.networkRequests.length > 0
            ? this.metrics.networkRequests.reduce((sum, r) => sum + r.duration, 0) / this.metrics.networkRequests.length
            : 0;
        
        return {
            summary: {
                sessionDuration: totalTime,
                totalPagesLoaded: totalPages,
                totalItemsRendered: totalItems,
                scrollEvents: this.metrics.scrollEvents,
                errors: this.metrics.errors.length
            },
            performance: {
                avgLoadTime: Math.round(avgLoadTime),
                avgRenderTime: Math.round(avgRenderTime),
                avgNetworkTime: Math.round(avgNetworkTime)
            },
            cache: {
                hits: this.metrics.cacheHits,
                misses: this.metrics.cacheMisses,
                hitRate: `${cacheHitRate}%`
            },
            network: {
                totalRequests: this.metrics.networkRequests.length,
                avgLatency: Math.round(avgNetworkTime)
            },
            errors: this.metrics.errors.map(e => ({
                page: e.page,
                error: e.error,
                timestamp: new Date(e.timestamp).toISOString()
            })),
            recommendations: this._generateRecommendations()
        };
    }

    /**
     * Gera recomendações baseadas nas métricas
     */
    _generateRecommendations() {
        const recommendations = [];
        const report = this.generateReport();
        
        // Verificar taxa de cache
        if (parseFloat(report.cache.hitRate) < 30) {
            recommendations.push({
                level: 'warning',
                message: 'Taxa de cache baixa (<30%). Considere aumentar CACHE_TTL ou MAX_CACHED_PAGES.'
            });
        }
        
        // Verificar tempo de rede
        if (report.performance.avgNetworkTime > 1000) {
            recommendations.push({
                level: 'error',
                message: `Latência de rede alta (${report.performance.avgNetworkTime}ms). Investigar performance do backend.`
            });
        }
        
        // Verificar tempo de renderização
        if (report.performance.avgRenderTime > 500) {
            recommendations.push({
                level: 'warning',
                message: `Renderização lenta (${report.performance.avgRenderTime}ms). Otimizar função de renderização.`
            });
        }
        
        // Verificar erros
        if (report.errors.length > 0) {
            recommendations.push({
                level: 'error',
                message: `${report.errors.length} erro(s) detectado(s). Verificar logs para detalhes.`
            });
        }
        
        if (recommendations.length === 0) {
            recommendations.push({
                level: 'success',
                message: 'Performance está ótima! Nenhum problema detectado.'
            });
        }
        
        return recommendations;
    }

    /**
     * Imprime relatório no console
     */
    printReport() {
        const report = this.generateReport();
        
        console.log('\n' + '='.repeat(80));
        console.log('📊 RELATÓRIO DE PERFORMANCE - LAZY LOADING');
        console.log('='.repeat(80) + '\n');
        
        console.log('📈 RESUMO DA SESSÃO:');
        console.log(`   Duração: ${(report.summary.sessionDuration / 1000).toFixed(1)}s`);
        console.log(`   Páginas carregadas: ${report.summary.totalPagesLoaded}`);
        console.log(`   Itens renderizados: ${report.summary.totalItemsRendered}`);
        console.log(`   Eventos de scroll: ${report.summary.scrollEvents}`);
        console.log(`   Erros: ${report.summary.errors}\n`);
        
        console.log('⚡ PERFORMANCE:');
        console.log(`   Tempo médio de carregamento: ${report.performance.avgLoadTime}ms`);
        console.log(`   Tempo médio de renderização: ${report.performance.avgRenderTime}ms`);
        console.log(`   Latência média de rede: ${report.performance.avgNetworkTime}ms\n`);
        
        console.log('📦 CACHE:');
        console.log(`   Hits: ${report.cache.hits}`);
        console.log(`   Misses: ${report.cache.misses}`);
        console.log(`   Taxa de acerto: ${report.cache.hitRate}\n`);
        
        console.log('🌐 REDE:');
        console.log(`   Total de requisições: ${report.network.totalRequests}`);
        console.log(`   Latência média: ${report.network.avgLatency}ms\n`);
        
        if (report.errors.length > 0) {
            console.log('❌ ERROS:');
            report.errors.forEach((error, i) => {
                console.log(`   ${i + 1}. Página ${error.page}: ${error.error}`);
                console.log(`      Timestamp: ${error.timestamp}`);
            });
            console.log();
        }
        
        console.log('💡 RECOMENDAÇÕES:');
        report.recommendations.forEach(rec => {
            const emoji = {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌'
            }[rec.level] || '📌';
            console.log(`   ${emoji} ${rec.message}`);
        });
        
        console.log('\n' + '='.repeat(80) + '\n');
        
        return report;
    }

    /**
     * Exporta relatório como JSON
     */
    exportJSON() {
        return JSON.stringify(this.generateReport(), null, 2);
    }

    /**
     * Envia relatório para backend (para análise)
     */
    async sendToBackend() {
        const report = this.generateReport();
        
        try {
            const response = await fetch(`${window.CONFIG.API_URL}/api/analytics/lazy-loading`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(report)
            });
            
            if (response.ok) {
                console.log('✅ Relatório enviado para backend');
            } else {
                console.warn('⚠️ Falha ao enviar relatório:', response.status);
            }
        } catch (error) {
            console.warn('⚠️ Erro ao enviar relatório:', error.message);
        }
    }

    /**
     * Reset das métricas
     */
    reset() {
        this.metrics = {
            pageLoads: [],
            cacheHits: 0,
            cacheMisses: 0,
            errors: [],
            renderTimes: [],
            scrollEvents: 0,
            networkRequests: []
        };
        this.startTime = Date.now();
    }

    /**
     * Habilitar/desabilitar monitoramento
     */
    setEnabled(enabled) {
        this.enabled = enabled;
    }
}

// ============================================================================
// INTEGRAÇÃO COM LAZY LOADER
// ============================================================================

/**
 * Instrumenta um LazyLoader com monitoramento de performance
 */
function instrumentLazyLoader(loader, monitorName = 'default') {
    const monitor = new LazyLoadPerformanceMonitor();
    window.lazyLoadMonitors = window.lazyLoadMonitors || {};
    window.lazyLoadMonitors[monitorName] = monitor;
    
    // Interceptar loadPage
    const originalLoadPage = loader.loadPage.bind(loader);
    loader.loadPage = async function(page) {
        const startTime = performance.now();
        const cacheKey = this._getCacheKey(page);
        const fromCache = this.cache.has(cacheKey);
        
        try {
            await originalLoadPage(page);
            const duration = performance.now() - startTime;
            
            // Estimar número de itens (pode ser melhorado)
            const itemCount = LazyLoadConfig.PAGE_SIZE;
            
            monitor.logPageLoad(page, duration, fromCache, itemCount);
        } catch (error) {
            monitor.logError(page, error);
            throw error;
        }
    };
    
    // Interceptar _renderPage para medir tempo de renderização
    const originalRenderPage = loader._renderPage.bind(loader);
    loader._renderPage = function(items, page) {
        const startTime = performance.now();
        
        try {
            originalRenderPage(items, page);
            const duration = performance.now() - startTime;
            monitor.logRenderTime(items.length, duration);
        } catch (error) {
            monitor.logError(page, error, { context: 'render' });
            throw error;
        }
    };
    
    return monitor;
}

// ============================================================================
// CONSOLE COMMANDS (para debug no navegador)
// ============================================================================

/**
 * Comandos disponíveis no console do navegador:
 * 
 * - window.lazyLoadMonitors.default.printReport()
 * - window.lazyLoadMonitors.default.exportJSON()
 * - window.lazyLoadMonitors.default.sendToBackend()
 * - window.lazyLoadMonitors.default.reset()
 */

// Export para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        LazyLoadPerformanceMonitor,
        instrumentLazyLoader
    };
}
