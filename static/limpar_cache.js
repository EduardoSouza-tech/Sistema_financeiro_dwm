/**
 * Script de emergência para limpar COMPLETAMENTE o cache do navegador
 * Cole este código no console do navegador (F12 -> Console)
 */

(async function limparCacheCompleto() {
    console.log('🧹 Iniciando limpeza completa de cache...');
    
    try {
        // 1. Limpar Service Workers
        if ('serviceWorker' in navigator) {
            const registrations = await navigator.serviceWorker.getRegistrations();
            for (let registration of registrations) {
                await registration.unregister();
                console.log('✅ Service Worker removido:', registration.scope);
            }
        }
        
        // 2. Limpar Cache Storage
        if ('caches' in window) {
            const cacheNames = await caches.keys();
            for (let cacheName of cacheNames) {
                await caches.delete(cacheName);
                console.log('✅ Cache deletado:', cacheName);
            }
        }
        
        // 3. Limpar Local Storage
        localStorage.clear();
        console.log('✅ LocalStorage limpo');
        
        // 4. Limpar Session Storage
        sessionStorage.clear();
        console.log('✅ SessionStorage limpo');
        
        // 5. Limpar IndexedDB (se existir)
        if ('indexedDB' in window) {
            const databases = await indexedDB.databases();
            for (let db of databases) {
                indexedDB.deleteDatabase(db.name);
                console.log('✅ IndexedDB deletado:', db.name);
            }
        }
        
        console.log('\n');
        console.log('=' .repeat(70));
        console.log('✅ CACHE LIMPO COM SUCESSO!');
        console.log('=' .repeat(70));
        console.log('🔄 Recarregando página em 2 segundos...');
        console.log('⚠️ Se o erro persistir, feche TODAS as abas e reabra.');
        
        setTimeout(() => {
            location.reload(true);
        }, 2000);
        
    } catch (error) {
        console.error('❌ Erro ao limpar cache:', error);
        console.log('🔄 Tentando reload forçado mesmo assim...');
        setTimeout(() => {
            location.reload(true);
        }, 1000);
    }
})();
