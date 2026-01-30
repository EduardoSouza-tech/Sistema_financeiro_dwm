/**
 * Script para limpar COMPLETAMENTE o cache do Service Worker e forçar reload
 * 
 * USO:
 * 1. Abra o console do browser (F12)
 * 2. Cole este código:
 *    fetch('/static/clear-cache.js').then(r => r.text()).then(eval)
 * 3. Aguarde a mensagem de sucesso
 */

(async function clearAllCache() {
    console.log('🧹 Iniciando limpeza COMPLETA de cache...');
    
    try {
        // 1. Desregistrar todos os Service Workers
        if ('serviceWorker' in navigator) {
            const registrations = await navigator.serviceWorker.getRegistrations();
            console.log(`📋 Encontrados ${registrations.length} Service Workers`);
            
            for (let registration of registrations) {
                await registration.unregister();
                console.log('✅ Service Worker desregistrado');
            }
        }
        
        // 2. Limpar TODOS os caches
        if ('caches' in window) {
            const cacheNames = await caches.keys();
            console.log(`📦 Encontrados ${cacheNames.length} caches:`, cacheNames);
            
            for (let cacheName of cacheNames) {
                await caches.delete(cacheName);
                console.log(`✅ Cache deletado: ${cacheName}`);
            }
        }
        
        // 3. Limpar localStorage
        console.log('🗑️ Limpando localStorage...');
        const tokenBackup = localStorage.getItem('token');
        localStorage.clear();
        if (tokenBackup) {
            localStorage.setItem('token', tokenBackup);
            console.log('💾 Token preservado');
        }
        
        // 4. Limpar sessionStorage
        console.log('🗑️ Limpando sessionStorage...');
        sessionStorage.clear();
        
        console.log('');
        console.log('✅ ============================================');
        console.log('✅ CACHE COMPLETAMENTE LIMPO!');
        console.log('✅ ============================================');
        console.log('');
        console.log('🔄 Recarregando página em 2 segundos...');
        
        // 5. Recarregar a página após 2 segundos
        setTimeout(() => {
            window.location.reload(true);
        }, 2000);
        
    } catch (error) {
        console.error('❌ Erro ao limpar cache:', error);
    }
})();
