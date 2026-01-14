/**
 * ============================================================================
 * SISTEMA DE PERMISSÕES
 * ============================================================================
 * Gerencia permissões de usuário e visibilidade de elementos
 * ============================================================================
 */

const PermissionManager = {
    // Permissões do usuário atual (carregadas do backend)
    userPermissions: [],
    
    /**
     * Inicializa sistema de permissões
     */
    async init() {
        try {
            console.log('🔐 Inicializando sistema de permissões...');
            await this.loadUserPermissions();
            this.applyPermissions();
            console.log('✅ Permissões carregadas');
        } catch (error) {
            console.error('❌ Erro ao carregar permissões:', error);
            // Em caso de erro, permite tudo (modo desenvolvimento)
            this.userPermissions = ['*'];
        }
    },
    
    /**
     * Carrega permissões do usuário do backend
     */
    async loadUserPermissions() {
        try {
            // Por enquanto, define permissões padrão
            // TODO: Implementar endpoint /api/auth/permissions
            this.userPermissions = [
                'dashboard',
                'lancamentos_view',
                'lancamentos_edit',
                'contas_view',
                'contas_edit',
                'categorias_view',
                'categorias_edit',
                'clientes_view',
                'clientes_edit',
                'fornecedores_view',
                'fornecedores_edit',
                'relatorios_view'
            ];
        } catch (error) {
            console.warn('Usando permissões padrão');
            this.userPermissions = ['*']; // Permite tudo em caso de erro
        }
    },
    
    /**
     * Verifica se usuário tem permissão específica
     * @param {string} permission - Nome da permissão
     * @returns {boolean}
     */
    hasPermission(permission) {
        if (!permission) return true;
        
        // Administrador tem todas as permissões
        if (this.userPermissions.includes('*') || this.userPermissions.includes('admin')) {
            return true;
        }
        
        // Verifica permissão específica
        return this.userPermissions.includes(permission);
    },
    
    /**
     * Aplica permissões aos elementos do DOM
     */
    applyPermissions() {
        // Oculta elementos sem permissão
        document.querySelectorAll('[data-permission]').forEach(element => {
            const permission = element.dataset.permission;
            
            if (!this.hasPermission(permission)) {
                element.style.display = 'none';
                element.disabled = true;
            }
        });
        
        console.log('✅ Permissões aplicadas ao DOM');
    },
    
    /**
     * Verifica se pode acessar uma página
     * @param {string} pageName - Nome da página
     * @returns {boolean}
     */
    canAccessPage(pageName) {
        const pagePermissions = {
            'dashboard': 'dashboard',
            'contas-receber': 'lancamentos_view',
            'contas-pagar': 'lancamentos_view',
            'lancamentos': 'lancamentos_view',
            'contas': 'contas_view',
            'categorias': 'categorias_view',
            'clientes': 'clientes_view',
            'fornecedores': 'fornecedores_view',
            'fluxo-caixa': 'relatorios_view',
            'fluxo-projetado': 'relatorios_view',
            'analise-contas': 'relatorios_view',
            'extrato-bancario': 'lancamentos_view'
        };
        
        const requiredPermission = pagePermissions[pageName];
        return !requiredPermission || this.hasPermission(requiredPermission);
    }
};

// Alias global para compatibilidade
window.hasPermission = (permission) => PermissionManager.hasPermission(permission);

console.log('✅ permissions.js carregado');
