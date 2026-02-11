/**
 * 🔧 Configuração de Regras de Auto-Conciliação
 * ==============================================
 * 
 * Sistema inteligente de detecção automática para conciliação de extratos
 * 
 * Funcionalidades:
 * - Cadastro de palavras-chave
 * - Vinculação com categoria/subcategoria
 * - Integração com Folha de Pagamento (detecta CPF de funcionários)
 * - Auto-preenchimento na conciliação
 * 
 * Data: 10/02/2026
 */

const RegrasConciliacao = {
    regras: [],
    categorias: [],
    subcategorias: {},
    clientes: [],
    fornecedores: [],
    configIntegracaoFolha: false, // Estado da configuração global
    
    /**
     * Inicializa o módulo
     */
    init() {
        console.log('🔧 Inicializando Regras de Auto-Conciliação...');
        
        // Inicializar array global para validação de duplicatas
        if (!window.regrasAtivas) {
            window.regrasAtivas = [];
        }
        
        this.carregarConfigIntegracao();
        this.carregarCategorias();
        this.carregarClientesFornecedores();
        this.carregarRegras();
        this.setupEventListeners();
    },
    
    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Listener para mudança de categoria
        const categoriaSelect = document.getElementById('regra-categoria');
        if (categoriaSelect) {
            categoriaSelect.addEventListener('change', (e) => {
                this.carregarSubcategorias(e.target.value);
            });
        }
    },
    
    /**
     * Carrega configuração de integração com folha
     */
    async carregarConfigIntegracao() {
        try {
            console.log('📄 Carregando configuração de integração com folha...');
            
            const response = await fetch('/api/config-extrato');
            const data = await response.json();
            
            if (data.success && data.data) {
                this.configIntegracaoFolha = data.data.integrar_folha_pagamento || false;
                
                // Atualizar checkbox
                const checkbox = document.getElementById('config-integracao-folha');
                const status = document.getElementById('config-integracao-status');
                
                if (checkbox) {
                    checkbox.checked = this.configIntegracaoFolha;
                }
                
                if (status) {
                    status.textContent = this.configIntegracaoFolha ? 'Ativado ✅' : 'Ativar';
                    status.style.color = this.configIntegracaoFolha ? '#00b894' : '#2d3436';
                }
                
                console.log(`✅ Integração com folha: ${this.configIntegracaoFolha ? 'ATIVADA' : 'DESATIVADA'}`);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar configuração:', error);
        }
    },
    
    /**
     * Toggle integração com folha de pagamento
     */
    async toggleIntegracaoFolha(ativo) {
        try {
            console.log(`🔄 Atualizando integração com folha: ${ativo ? 'ATIVAR' : 'DESATIVAR'}`);
            
            const response = await fetch('/api/config-extrato', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    integrar_folha_pagamento: ativo
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.configIntegracaoFolha = ativo;
                
                // Atualizar status visual
                const status = document.getElementById('config-integracao-status');
                if (status) {
                    status.textContent = ativo ? 'Ativado ✅' : 'Ativar';
                    status.style.color = ativo ? '#00b894' : '#2d3436';
                }
                
                // Feedback visual
                const mensagem = ativo 
                    ? '✅ Integração ativada! O sistema detectará CPF automaticamente em todos os extratos.'
                    : '⚠️ Integração desativada. CPF não será mais detectado automaticamente.';
                
                alert(mensagem);
                
                console.log(`✅ Configuração atualizada com sucesso`);
            } else {
                throw new Error(data.error || 'Erro ao atualizar configuração');
            }
        } catch (error) {
            console.error('❌ Erro ao atualizar integração:', error);
            alert('❌ Erro ao atualizar configuração: ' + error.message);
            
            // Reverter checkbox em caso de erro
            const checkbox = document.getElementById('config-integracao-folha');
            if (checkbox) {
                checkbox.checked = this.configIntegracaoFolha;
            }
        }
    },
    
    /**
     * Carrega categorias disponíveis
     */
    async carregarCategorias() {
        try {
            console.log('📂 Carregando categorias...');
            
            const response = await fetch('/api/categorias');
            const data = await response.json();
            
            // Suporte ao novo formato de resposta
            this.categorias = Array.isArray(data) ? data : (data.data || data.categorias || []);
            
            // Organizar subcategorias por categoria
            this.subcategorias = {};
            this.categorias.forEach(cat => {
                if (cat.subcategorias) {
                    try {
                        this.subcategorias[cat.nome] = Array.isArray(cat.subcategorias) ? 
                            cat.subcategorias : JSON.parse(cat.subcategorias);
                    } catch (e) {
                        this.subcategorias[cat.nome] = [];
                    }
                } else {
                    this.subcategorias[cat.nome] = [];
                }
            });
            
            console.log(`✅ ${this.categorias.length} categoria(s) carregadas`);
            
        } catch (error) {
            console.error('❌ Erro ao carregar categorias:', error);
            this.categorias = [];
            this.subcategorias = {};
        }
    },

    /**
     * Carrega clientes e fornecedores
     */
    async carregarClientesFornecedores() {
        try {
            console.log('👥 Carregando clientes e fornecedores...');
            
            const [clientesResponse, fornecedoresResponse] = await Promise.all([
                fetch('/api/clientes'),
                fetch('/api/fornecedores')
            ]);
            
            const clientesData = await clientesResponse.json();
            const fornecedoresData = await fornecedoresResponse.json();
            
            // Suporte ao novo formato de resposta
            this.clientes = Array.isArray(clientesData) ? clientesData : (clientesData.data || clientesData.clientes || []);
            this.fornecedores = Array.isArray(fornecedoresData) ? fornecedoresData : (fornecedoresData.data || fornecedoresData.fornecedores || []);
            
            console.log(`✅ ${this.clientes.length} cliente(s) e ${this.fornecedores.length} fornecedor(es) carregados`);
            
        } catch (error) {
            console.error('❌ Erro ao carregar clientes/fornecedores:', error);
            this.clientes = [];
            this.fornecedores = [];
        }
    },

    /**
     * Carrega subcategorias de uma categoria específica
     */
    carregarSubcategorias(categoriaNome) {
        const subcategoriaSelect = document.getElementById('regra-subcategoria');
        if (!subcategoriaSelect) return;
        
        // Limpar opções
        subcategoriaSelect.innerHTML = '<option value="">Selecione uma subcategoria...</option>';
        
        if (!categoriaNome) {
            subcategoriaSelect.disabled = true;
            return;
        }
        
        // Buscar subcategorias
        const subs = this.subcategorias[categoriaNome] || [];
        
        if (subs.length === 0) {
            subcategoriaSelect.disabled = true;
            return;
        }
        
        // Preencher opções
        subs.forEach(sub => {
            const option = document.createElement('option');
            option.value = sub;
            option.textContent = sub;
            subcategoriaSelect.appendChild(option);
        });
        
        subcategoriaSelect.disabled = false;
    },

    /**
     * Carrega regras existentes
     */
    async carregarRegras() {
        try {
            console.log('📋 Carregando regras existentes...');
            
            const response = await fetch('/api/regras-conciliacao');
            const data = await response.json();
            
            this.regras = Array.isArray(data) ? data : (data.data || data.regras || []);
            console.log(`✅ ${this.regras.length} regra(s) carregadas`);
            
            // Armazenar globalmente para validação de duplicatas
            window.regrasAtivas = this.regras.filter(r => r.ativo);
            
            // Renderizar tabela
            this.renderizarTabela();
            
        } catch (error) {
            console.error('❌ Erro ao carregar regras:', error);
            this.regras = [];
            this.renderizarTabela();
        }
    },

    /**
     * Renderiza a tabela de regras
     */
    renderizarTabela() {
        const tbody = document.getElementById('regras-lista');
        if (!tbody) {
            console.warn('⚠️ Elemento regras-lista não encontrado');
            return;
        }
        
        if (this.regras.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 40px; color: #7f8c8d;">
                        <div style="font-size: 48px; margin-bottom: 10px;">📋</div>
                        <div style="font-size: 16px;">Nenhuma regra cadastrada ainda.</div>
                        <div style="font-size: 14px; margin-top: 10px; color: #95a5a6;">
                            Clique em "➕ Nova Regra" para criar sua primeira regra de auto-conciliação
                        </div>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = this.regras.map(regra => `
            <tr style="border-bottom: 1px solid #dee2e6; ${!regra.ativo ? 'opacity: 0.5;' : ''}">
                <td style="padding: 15px;">
                    <div style="font-weight: 600; color: #2c3e50; margin-bottom: 4px;">
                        ${this.escapeHtml(regra.palavra_chave)}
                    </div>
                    ${regra.descricao ? `
                        <div style="font-size: 12px; color: #7f8c8d;">
                            ${this.escapeHtml(regra.descricao)}
                        </div>
                    ` : ''}
                </td>
                <td style="padding: 15px; color: #495057;">
                    ${regra.categoria ? this.escapeHtml(regra.categoria) : '<span style="color: #95a5a6;">-</span>'}
                </td>
                <td style="padding: 15px; color: #495057;">
                    ${regra.subcategoria ? this.escapeHtml(regra.subcategoria) : '<span style="color: #95a5a6;">-</span>'}
                </td>
                <td style="padding: 15px; color: #495057;">
                    ${regra.cliente_padrao ? this.escapeHtml(regra.cliente_padrao) : '<span style="color: #95a5a6;">-</span>'}
                </td>
                <td style="padding: 15px; text-align: center;">
                    <button onclick="RegrasConciliacao.editarRegra(${regra.id})" 
                            style="background: #3498db; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; margin-right: 4px;"
                            title="Editar regra">
                        ✏️
                    </button>
                    <button onclick="RegrasConciliacao.excluirRegra(${regra.id})" 
                            style="background: #e74c3c; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;"
                            title="Excluir regra">
                        🗑️
                    </button>
                </td>
            </tr>
        `).join('');
        
        console.log('✅ Tabela renderizada com', this.regras.length, 'regra(s)');
    },

    /**
     * Escapa HTML para prevenir XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Preenche select de clientes/fornecedores
     */
    preencherSelectClientesFornecedores() {
        const select = document.getElementById('regra-cliente-padrao');
        if (!select) return;
        
        select.innerHTML = '<option value="">Nenhum (deixar vazio)</option>';
        
        // Adicionar grupo de Clientes
        if (this.clientes.length > 0) {
            const optgroupClientes = document.createElement('optgroup');
            optgroupClientes.label = '👤 Clientes';
            
            this.clientes.forEach(cliente => {
                const option = document.createElement('option');
                option.value = cliente.nome;
                option.textContent = cliente.nome;
                optgroupClientes.appendChild(option);
            });
            
            select.appendChild(optgroupClientes);
        }
        
        // Adicionar grupo de Fornecedores
        if (this.fornecedores.length > 0) {
            const optgroupFornecedores = document.createElement('optgroup');
            optgroupFornecedores.label = '🏭 Fornecedores';
            
            this.fornecedores.forEach(fornecedor => {
                const option = document.createElement('option');
                option.value = fornecedor.nome;
                option.textContent = fornecedor.nome;
                optgroupFornecedores.appendChild(option);
            });
            
            select.appendChild(optgroupFornecedores);
        }
    },

    /**
     * Nova regra
     */
    novaRegra() {
        console.log('🆕 Abrindo formulário de nova regra...');
        
        // Limpar formulário
        document.getElementById('regra-id').value = '';
        document.getElementById('regra-palavra-chave').value = '';
        document.getElementById('regra-descricao').value = '';
        document.getElementById('regra-categoria').value = '';
        document.getElementById('regra-subcategoria').value = '';
        document.getElementById('regra-subcategoria').disabled = true;
        document.getElementById('regra-cliente-padrao').value = '';
        
        // Preencher selects
        this.preencherSelectCategorias();
        this.preencherSelectClientesFornecedores();
        
        // Atualizar título do modal
        document.getElementById('modal-regra-titulo').textContent = '➕ Nova Regra de Auto-Conciliação';
        
        // Abrir modal
        document.getElementById('modal-regra-conciliacao').style.display = 'flex';
        
        console.log('✅ Modal de nova regra aberto');
    },

    /**
     * Preenche select de categorias
     */
    preencherSelectCategorias() {
        const select = document.getElementById('regra-categoria');
        if (!select) return;
        
        select.innerHTML = '<option value="">Selecione uma categoria (opcional)...</option>';
        
        this.categorias.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.nome;
            option.textContent = `${cat.nome} (${cat.tipo})`;
            select.appendChild(option);
        });
    },
    
    /**
     * Editar regra existente
     */
    editarRegra(id) {
        const regra = this.regras.find(r => r.id === id);
        if (!regra) {
            console.error('Regra não encontrada:', id);
            return;
        }

        // Preencher formulário
        document.getElementById('regra-id').value = regra.id;
        document.getElementById('regra-palavra-chave').value = regra.palavra_chave;
        document.getElementById('regra-descricao').value = regra.descricao || '';
        document.getElementById('regra-categoria').value = regra.categoria || '';
        document.getElementById('regra-subcategoria').value = regra.subcategoria || '';
        document.getElementById('regra-cliente-padrao').value = regra.cliente_padrao || '';
        
        // Preencher selects
        this.preencherSelectCategorias();
        this.preencherSelectClientesFornecedores();
        
        // Selecionar categoria
        if (regra.categoria) {
            document.getElementById('regra-categoria').value = regra.categoria;
            this.carregarSubcategorias(regra.categoria);
            
            // Aguardar carregamento e selecionar subcategoria
            setTimeout(() => {
                if (regra.subcategoria) {
                    document.getElementById('regra-subcategoria').value = regra.subcategoria;
                }
            }, 100);
        }
        
        // Selecionar cliente padrão se houver
        if (regra.cliente_padrao) {
            // Aguardar preenchimento do select
            setTimeout(() => {
                const selectCliente = document.getElementById('regra-cliente-padrao');
                if (selectCliente) {
                    selectCliente.value = regra.cliente_padrao;
                }
            }, 200);
        }
        
        // Abrir modal
        document.getElementById('modal-regra-conciliacao').style.display = 'flex';
        document.getElementById('modal-regra-titulo').textContent = '✏️ Editar Regra';  
        
        console.log('✅ Modal de edição aberto para regra:', regra);
    },
    
    /**
     * Fechar modal
     */
    fecharModal() {
        document.getElementById('modal-regra-conciliacao').style.display = 'none';
    },

    /**
     * Salvar regra (criar ou atualizar)
     */
    async salvarRegra() {
        console.log('💾 Salvando regra...');
        
        try {
            // Coletar dados do formulário
            const regraId = document.getElementById('regra-id').value;
            const palavraChave = document.getElementById('regra-palavra-chave').value.trim();
            const descricao = document.getElementById('regra-descricao').value.trim();
            const categoria = document.getElementById('regra-categoria').value;
            const subcategoria = document.getElementById('regra-subcategoria').value;
            const clientePadrao = document.getElementById('regra-cliente-padrao').value;
            
            // Validações
            if (!palavraChave) {
                alert('❌ Palavra-chave é obrigatória!');
                document.getElementById('regra-palavra-chave').focus();
                return;
            }
            
            // Preparar dados
            const dados = {
                palavra_chave: palavraChave,
                descricao: descricao || null,
                categoria: categoria || null,
                subcategoria: subcategoria || null,
                cliente_padrao: clientePadrao || null,
                ativo: true
            };
            
            console.log('📤 Dados a enviar:', dados);
            
            // Determinar método e URL
            const isEdicao = regraId && regraId !== '';
            
            // Se não é edição, verificar se já existe regra com essa palavra-chave
            if (!isEdicao) {
                const regraExistente = window.regrasAtivas.find(r => 
                    r.palavra_chave.toUpperCase() === palavraChave.toUpperCase()
                );
                
                if (regraExistente) {
                    alert(`⚠️ Já existe uma regra com a palavra-chave "${palavraChave}"!\n\nEdite a regra existente ao invés de criar uma nova.`);
                    document.getElementById('regra-palavra-chave').focus();
                    return;
                }
            }
            
            const url = isEdicao 
                ? `/api/regras-conciliacao/${regraId}` 
                : '/api/regras-conciliacao';
            const method = isEdicao ? 'PUT' : 'POST';
            
            console.log(`🌐 ${method} ${url}`);
            
            // Enviar para API
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(dados)
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                console.log('✅ Regra salva com sucesso!', result);
                alert(`✅ Regra ${isEdicao ? 'atualizada' : 'criada'} com sucesso!`);
                
                // Fechar modal
                this.fecharModal();
                
                // Recarregar lista de regras
                await this.carregarRegras();
                
            } else {
                console.error('❌ Erro ao salvar regra:', result);
                alert(`❌ Erro ao salvar regra: ${result.error || 'Erro desconhecido'}`);
            }
            
        } catch (error) {
            console.error('❌ Erro ao salvar regra:', error);
            alert('❌ Erro ao salvar regra. Verifique o console para detalhes.');
        }
    },

    /**
     * Excluir regra
     */
    async excluirRegra(id) {
        console.log('🗑️ Solicitação para excluir regra:', id);
        
        if (!confirm('⚠️ Tem certeza que deseja excluir esta regra?')) {
            console.log('❌ Exclusão cancelada pelo usuário');
            return;
        }
        
        try {
            const response = await fetch(`/api/regras-conciliacao/${id}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                console.log('✅ Regra excluída com sucesso!');
                alert('✅ Regra excluída com sucesso!');
                
                // Recarregar lista
                await this.carregarRegras();
                
            } else {
                console.error('❌ Erro ao excluir regra:', result);
                alert(`❌ Erro ao excluir regra: ${result.error || 'Erro desconhecido'}`);
            }
            
        } catch (error) {
            console.error('❌ Erro ao excluir regra:', error);
            alert('❌ Erro ao excluir regra. Verifique o console.');
        }
    }
};

// Expor globalmente
window.RegrasConciliacao = RegrasConciliacao;

// Função para abrir configuração de regras
window.abrirConfiguracaoRegras = function() {
    RegrasConciliacao.init();
    document.getElementById('modal-config-regras').style.display = 'flex';
};

console.log('✅ regras_conciliacao.js carregado com sucesso');