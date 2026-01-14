/**
 * ============================================================================
 * SERVICE WORKER - GERENCIAMENTO DE CACHE
 * ============================================================================
 * Garante que sempre carregue a versão mais recente dos arquivos
 * ============================================================================
 */

const CACHE_NAME = 'sistema-financeiro-v1';
const urlsToCache = [];

// Evento de instalação - limpa cache antigo
self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker: Instalando...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    console.log('🗑️ Service Worker: Limpando cache antigo:', cacheName);
                    return caches.delete(cacheName);
                })
            );
        }).then(() => {
            console.log('✅ Service Worker: Instalado e cache limpo!');
            return self.skipWaiting(); // Ativa imediatamente
        })
    );
});

// Evento de ativação - assume controle imediatamente
self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker: Ativando...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((cacheName) => cacheName !== CACHE_NAME)
                    .map((cacheName) => {
                        console.log('🗑️ Service Worker: Deletando cache desatualizado:', cacheName);
                        return caches.delete(cacheName);
                    })
            );
        }).then(() => {
            console.log('✅ Service Worker: Ativado!');
            return self.clients.claim(); // Assume controle de todas as páginas
        })
    );
});

// Evento de fetch - SEMPRE busca da rede (sem cache)
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    
    // Para arquivos estáticos, sempre busca da rede
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            fetch(event.request, {
                cache: 'no-store' // Força buscar da rede
            }).catch(() => {
                console.error('❌ Erro ao buscar:', url.pathname);
                return new Response('Offline', { status: 503 });
            })
        );
    } else {
        // Para outras requisições, apenas passa adiante
        event.respondWith(fetch(event.request));
    }
});

// Limpa cache quando recebe mensagem
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        console.log('🗑️ Service Worker: Recebeu comando para limpar cache');
        
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        console.log('🗑️ Limpando cache:', cacheName);
                        return caches.delete(cacheName);
                    })
                );
            }).then(() => {
                console.log('✅ Cache limpo com sucesso!');
                // Notifica todos os clientes
                return self.clients.matchAll();
            }).then((clients) => {
                clients.forEach((client) => {
                    client.postMessage({
                        type: 'CACHE_CLEARED',
                        message: 'Cache limpo com sucesso!'
                    });
                });
            })
        );
    }
});

console.log('✅ Service Worker carregado e pronto!');
