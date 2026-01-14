/**
 * ============================================================================
 * SISTEMA DE NAVEGAÇÃO
 * ============================================================================
 * Gerencia navegação entre páginas, sidebar, modais e rotas
 * ============================================================================
 */

const NavigationManager = {
    currentPage: 'dashboard',
    
    /**
     * Inicializa sistema de navegação
     */
    init() {
        console.log('🧭 Inicializando sistema de navegação...');
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        console.log('✅ Navegação inicializada');
    },
    
    /**
     * Configura event listeners de navegação
     */
    setupEventListeners() {
        // Botões de navegação
        document.querySelectorAll('.nav-button').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const pageId = button.getAttribute('onclick')?.match(/'([^']+)'/)?.[1] || 
                              button.dataset.page;
                
                if (pageId) {
                    this.navigateTo(pageId);
                }
            });
        });
        
        // Submenus
        document.querySelectorAll('.submenu-title').forEach(title => {
            title.addEventListener('click', () => {
                const submenu = title.nextElementSibling;
                if (submenu && submenu.classList.contains('submenu')) {
                    this.toggleSubmenu(title);
                }
            });
        });
        
        // Fechar modal ao clicar fora
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });
        
        console.log('✅ Event listeners de navegação configurados');
    },
    
    /**
     * Configura atalhos de teclado
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // ESC fecha modais
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
            
            // Ctrl/Cmd + teclas para navegação rápida
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'd':
                        e.preventDefault();
                        this.navigateTo('dashboard');
                        break;
                    case 'l':
                        e.preventDefault();
                        this.navigateTo('lancamentos');
                        break;
                }
            }
        });
        
        console.log('✅ Atalhos de teclado configurados');
    },
    
    /**
     * Navega para uma página específica
     * @param {string} pageId - ID da página
     */
    async navigateTo(pageId) {
        const context = `navigateTo(${pageId})`;
        
        try {
            console.log(`🧭 Navegando para: ${pageId}`);
            
            // Verifica permissão
            if (!PermissionManager.canAccessPage(pageId)) {
                window.showNotification('Você não tem permissão para acessar esta página', 'error');
                return;
            }
            
            // Oculta todas as páginas
            document.querySelectorAll('.page').forEach(page => {
                page.classList.remove('active');
                page.style.display = 'none';
            });
            
            // Mostra página solicitada
            const targetPage = document.getElementById(pageId);
            if (targetPage) {
                targetPage.style.display = 'block';
                setTimeout(() => targetPage.classList.add('active'), 10);
            } else {
                console.warn(`⚠️ Página não encontrada: ${pageId}`);
            }
            
            // Atualiza botões de navegação
            this.updateActiveButton(pageId);
            
            // Atualiza estado
            this.currentPage = pageId;
            if (window.AppState) {
                window.AppState.currentPage = pageId;
            }
            
            // Carrega dados da página
            await this.loadPageData(pageId);
            
            console.log(`✅ Navegação para ${pageId} concluída`);
            
        } catch (error) {
            console.error(`❌ Erro ao navegar para ${pageId}:`, error);
            window.showNotification(`Erro ao carregar página: ${pageId}`, 'error');
        }
    },
    
    /**
     * Atualiza botão ativo na navegação
     * @param {string} pageId - ID da página ativa
     */
    updateActiveButton(pageId) {
        // Remove active de todos os botões
        document.querySelectorAll('.nav-button').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Adiciona active ao botão correto
        const activeButton = document.querySelector(
            `.nav-button[onclick*="${pageId}"], .nav-button[data-page="${pageId}"]`
        );
        
        if (activeButton) {
            activeButton.classList.add('active');
        }
    },
    
    /**
     * Carrega dados específicos da página
     * @param {string} pageId - ID da página
     */
    async loadPageData(pageId) {
        const loaders = {
            'dashboard': () => window.loadDashboard?.(),
            'lancamentos': () => window.loadLancamentos?.(),
            'contas-receber': () => window.loadContasReceber?.(),
            'contas-pagar': () => window.loadContasPagar?.(),
            'contas': () => window.loadContas?.(),
            'categorias': () => window.loadCategorias?.(),
            'clientes': () => window.loadClientes?.(),
            'fornecedores': () => window.loadFornecedores?.(),
            'fluxo-caixa': () => window.loadFluxoCaixa?.(),
            'fluxo-projetado': () => window.loadFluxoProjetado?.(),
            'analise-contas': () => window.loadAnaliseContas?.(),
            'extrato-bancario': () => window.loadExtratoBancario?.()
        };
        
        const loader = loaders[pageId];
        if (loader) {
            try {
                await loader();
            } catch (error) {
                console.error(`Erro ao carregar dados de ${pageId}:`, error);
            }
        }
    },
    
    /**
     * Toggle submenu
     * @param {HTMLElement} element - Elemento do submenu
     */
    toggleSubmenu(element) {
        const submenu = element.nextElementSibling;
        if (!submenu) return;
        
        const isOpen = submenu.style.display === 'block';
        
        // Fecha outros submenus
        document.querySelectorAll('.submenu').forEach(s => {
            if (s !== submenu) {
                s.style.display = 'none';
            }
        });
        
        // Toggle submenu atual
        submenu.style.display = isOpen ? 'none' : 'block';
        
        // Atualiza ícone
        const icon = element.querySelector('.submenu-icon');
        if (icon) {
            icon.textContent = isOpen ? '▶' : '▼';
        }
    },
    
    /**
     * Abre modal
     * @param {string} modalId - ID do modal
     */
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
            
            console.log(`✅ Modal aberto: ${modalId}`);
        } else {
            console.warn(`⚠️ Modal não encontrado: ${modalId}`);
        }
    },
    
    /**
     * Fecha modal
     * @param {string} modalId - ID do modal
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            modal.style.display = 'none';
            document.body.style.overflow = '';
            
            // Limpa formulário se existir
            const form = modal.querySelector('form');
            if (form) {
                form.reset();
            }
            
            console.log(`✅ Modal fechado: ${modalId}`);
        }
    },
    
    /**
     * Fecha todos os modais abertos
     */
    closeAllModals() {
        document.querySelectorAll('.modal.active').forEach(modal => {
            this.closeModal(modal.id);
        });
    },
    
    /**
     * Mostra página (alias para compatibilidade)
     * @param {string} pageId - ID da página
     */
    showPage(pageId) {
        return this.navigateTo(pageId);
    },
    
    /**
     * Mostra seção (alias para compatibilidade)
     * @param {string} sectionId - ID da seção
     */
    showSection(sectionId) {
        return this.navigateTo(sectionId);
    }
};

// Aliases globais para compatibilidade
window.showPage = (pageId) => NavigationManager.navigateTo(pageId);
window.showSection = (sectionId) => NavigationManager.navigateTo(sectionId);
window.toggleSubmenu = (element) => NavigationManager.toggleSubmenu(element);
window.openModal = (modalId) => NavigationManager.openModal(modalId);
window.closeModal = (modalId) => NavigationManager.closeModal(modalId);

console.log('✅ navigation.js carregado');
