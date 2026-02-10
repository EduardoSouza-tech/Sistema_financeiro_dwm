/*
 * Módulo de Remessa de Pagamentos - Sicredi
 * JavaScript para gerenciamento de remessas bancárias
 * Versão: 1.0.0 - 09/02/2026
 */

const RemessaPagamento = {
    // Estado do módulo
    state: {
        contasSelecionadas: [],
        filtros: {
            dataInicio: null,
            dataFim: null,
            tipoPagamento: 'TODOS',
            statusVencimento: 'TODOS'
        },
        remessas: [],
        configuracao: null
    },

    // Inicializar módulo
    init() {
        console.log('🏦 Inicializando módulo de Remessa de Pagamento');
        this.carregarConfiguracao();
        this.setupEventListeners();
    },

    // =============================================================================
    // EVENT LISTENERS
    // =============================================================================

    setupEventListeners() {
        // Filtros
        document.getElementById('filtro-data-inicio')?.addEventListener('change', () => this.aplicarFiltros());
        document.getElementById('filtro-data-fim')?.addEventListener('change', () => this.aplicarFiltros());
        document.getElementById('filtro-tipo-pagamento')?.addEventListener('change', () => this.aplicarFiltros());
        document.getElementById('filtro-vencimento')?.addEventListener('change', () => this.aplicarFiltros());

        // Botões
        document.getElementById('btn-limpar-filtros')?.addEventListener('click', () => this.limparFiltros());
        document.getElementById('btn-gerar-remessa')?.addEventListener('click', () => this.abrirModalGerarRemessa());
        document.getElementById('btn-historico')?.addEventListener('click', () => this.carregarHistorico());
        document.getElementById('btn-configuracao')?.addEventListener('click', () => this.abrirModalConfiguracao());

        // Selecionar/Desselecionar todos
        document.getElementById('selecionar-todos')?.addEventListener('change', (e) => this.selecionarTodos(e.target.checked));
    },

    // =============================================================================
    // CARREGAR DADOS
    // =============================================================================

    async carregarConfiguracao() {
        try {
            const response = await fetch('/api/remessa/config', {
                method: 'GET',
                credentials: 'include'
            });

            const data = await response.json();

            if (data.success) {
                this.state.configuracao = data.configuracao;

                if (!data.configuracao) {
                    this.mostrarAlerta('warning', 
                        'Configuração Sicredi não encontrada. Configure o convênio para usar o módulo de remessa.',
                        'abrirModalConfiguracao()'
                    );
                }
            } else {
                console.error('❌ Erro ao carregar configuração:', data.error);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar configuração:', error);
        }
    },

    async carregarContasPendentes() {
        try {
            this.mostrarLoading(true);

            const params = new URLSearchParams();

            if (this.state.filtros.dataInicio) {
                params.append('data_inicio', this.state.filtros.dataInicio);
            }

            if (this.state.filtros.dataFim) {
                params.append('data_fim', this.state.filtros.dataFim);
            }

            if (this.state.filtros.tipoPagamento !== 'TODOS') {
                params.append('tipo_pagamento', this.state.filtros.tipoPagamento);
            }

            if (this.state.filtros.statusVencimento !== 'TODOS') {
                params.append('vencimento', this.state.filtros.statusVencimento);
            }

            const response = await fetch(`/api/remessa/contas-pagar/pendentes?${params}`, {
                method: 'GET',
                credentials: 'include'
            });

            const data = await response.json();

            if (data.success) {
                this.renderizarContas(data.contas);
                this.atualizarEstatisticas(data);
            } else {
                this.mostrarAlerta('error', data.error);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar contas:', error);
            this.mostrarAlerta('error', 'Erro ao carregar contas pendentes');
        } finally {
            this.mostrarLoading(false);
        }
    },

    async carregarHistorico(limite = 50, offset = 0) {
        try {
            this.mostrarLoading(true, 'historico');

            const response = await fetch(`/api/remessa/historico?limite=${limite}&offset=${offset}`, {
                method: 'GET',
                credentials: 'include'
            });

            const data = await response.json();

            if (data.success) {
                this.state.remessas = data.remessas;
                this.renderizarHistorico(data.remessas, data.total);
            } else {
                this.mostrarAlerta('error', data.error);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar histórico:', error);
            this.mostrarAlerta('error', 'Erro ao carregar histórico de remessas');
        } finally {
            this.mostrarLoading(false, 'historico');
        }
    },

    // =============================================================================
    // RENDERIZAÇÃO
    // =============================================================================

    renderizarContas(contas) {
        const tbody = document.getElementById('tabela-contas-body');

        if (!tbody) {
            console.error('❌ Elemento tabela-contas-body não encontrado');
            return;
        }

        if (contas.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align: center; padding: 40px; color: #7f8c8d;">
                        <i class="fas fa-inbox" style="font-size: 48px; margin-bottom: 16px; display: block;"></i>
                        Nenhuma conta a pagar pendente encontrada
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = contas.map(conta => {
            const classeVencimento = this.getClasseVencimento(conta.status_vencimento);
            const iconeTipo = this.getIconeTipo(conta.tipo_pagamento_sugerido);
            const selecionada = this.state.contasSelecionadas.includes(conta.id);

            return `
                <tr class="${selecionada ? 'selecionada' : ''}" data-id="${conta.id}">
                    <td style="text-align: center;">
                        <input type="checkbox" 
                               class="checkbox-conta" 
                               value="${conta.id}"
                               ${selecionada ? 'checked' : ''}
                               onchange="RemessaPagamento.toggleSelecao(${conta.id})">
                    </td>
                    <td>
                        <span class="badge badge-${classeVencimento}">
                            ${this.formatarData(conta.data_vencimento)}
                        </span>
                    </td>
                    <td>
                        <div style="font-weight: 500;">${this.truncar(conta.descricao, 50)}</div>
                        ${conta.fornecedor ? `<small style="color: #7f8c8d;">${conta.fornecedor}</small>` : ''}
                    </td>
                    <td style="text-align: right; font-weight: 600;">
                        ${this.formatarMoeda(conta.valor)}
                    </td>
                    <td style="text-align: center;">
                        <span class="badge badge-tipo badge-${conta.tipo_pagamento_sugerido.toLowerCase()}">
                            ${iconeTipo} ${conta.tipo_pagamento_sugerido}
                        </span>
                    </td>
                    <td style="font-size: 12px; color: #7f8c8d;">
                        ${conta.categoria || '-'}
                    </td>
                    <td style="font-size: 12px;">
                        ${this.formatarDadosBancarios(conta)}
                    </td>
                    <td style="text-align: center;">
                        <span class="badge badge-status-${conta.status_vencimento.toLowerCase()}">
                            ${this.getLabelVencimento(conta.status_vencimento)}
                        </span>
                    </td>
                    <td style="text-align: center;">
                        <button class="btn-icon" 
                                onclick="RemessaPagamento.visualizarDetalhe(${conta.id})"
                                title="Ver detalhes">
                            <i class="fas fa-eye"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    },

    renderizarHistorico(remessas, total) {
        const container = document.getElementById('historico-remessas');

        if (!container) {
            console.error('❌ Elemento historico-remessas não encontrado');
            return;
        }

        if (remessas.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 60px; color: #7f8c8d;">
                    <i class="fas fa-file-invoice" style="font-size: 64px; margin-bottom: 20px; display: block;"></i>
                    <h3>Nenhuma remessa gerada ainda</h3>
                    <p>Gere sua primeira remessa de pagamento</p>
                </div>
            `;
            return;
        }

        container.innerHTML = remessas.map(remessa => {
            const classeStatus = this.getClasseStatus(remessa.status);
            const iconeStatus = this.getIconeStatus(remessa.status);

            return `
                <div class="card-remessa" onclick="RemessaPagamento.visualizarRemessa(${remessa.id})">
                    <div class="card-remessa-header">
                        <div>
                            <h3>Remessa #${remessa.numero_sequencial}</h3>
                            <small>${this.formatarDataHora(remessa.data_geracao)}</small>
                        </div>
                        <span class="badge badge-${classeStatus}">
                            ${iconeStatus} ${remessa.status}
                        </span>
                    </div>
                    <div class="card-remessa-body">
                        <div class="info-item">
                            <span class="label">Arquivo:</span>
                            <span class="value">${remessa.nome_arquivo}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">Quantidade:</span>
                            <span class="value">${remessa.quantidade_pagamentos} pagamentos</span>
                        </div>
                        <div class="info-item">
                            <span class="label">Valor Total:</span>
                            <span class="value" style="font-weight: 700; color: #27ae60;">
                                ${this.formatarMoeda(remessa.valor_total)}
                            </span>
                        </div>
                    </div>
                    <div class="card-remessa-footer">
                        <div class="remessa-stats">
                            ${remessa.quantidade_ted > 0 ? `<span class="stat">TED: ${remessa.quantidade_ted}</span>` : ''}
                            ${remessa.quantidade_pix > 0 ? `<span class="stat">PIX: ${remessa.quantidade_pix}</span>` : ''}
                            ${remessa.quantidade_boleto > 0 ? `<span class="stat">Boleto: ${remessa.quantidade_boleto}</span>` : ''}
                        </div>
                        <div class="remessa-actions">
                            <button class="btn-icon" 
                                    onclick="event.stopPropagation(); RemessaPagamento.downloadRemessa(${remessa.id})"
                                    title="Fazer download">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    },

    atualizarEstatisticas(data) {
        document.getElementById('stat-total-contas').textContent = data.total;
        document.getElementById('stat-total-valor').textContent = this.formatarMoeda(data.total_valor);

        if (data.por_tipo) {
            const tiposHtml = Object.entries(data.por_tipo).map(([tipo, stats]) => {
                const icone = this.getIconeTipo(tipo);
                return `
                    <div class="stat-tipo">
                        <span class="stat-tipo-label">${icone} ${tipo}:</span>
                        <span class="stat-tipo-value">${stats.quantidade} (${this.formatarMoeda(stats.valor)})</span>
                    </div>
                `;
            }).join('');

            document.getElementById('stat-por-tipo').innerHTML = tiposHtml;
        }

        document.getElementById('stat-selecionadas').textContent = this.state.contasSelecionadas.length;
        const valorSelecionado = this.calcularValorSelecionado();
        document.getElementById('stat-valor-selecionado').textContent = this.formatarMoeda(valorSelecionado);
    },

    // =============================================================================
    // AÇÕES
    // =============================================================================

    aplicarFiltros() {
        this.state.filtros = {
            dataInicio: document.getElementById('filtro-data-inicio').value,
            dataFim: document.getElementById('filtro-data-fim').value,
            tipoPagamento: document.getElementById('filtro-tipo-pagamento').value,
            statusVencimento: document.getElementById('filtro-vencimento').value
        };

        this.carregarContasPendentes();
    },

    limparFiltros() {
        document.getElementById('filtro-data-inicio').value = '';
        document.getElementById('filtro-data-fim').value = '';
        document.getElementById('filtro-tipo-pagamento').value = 'TODOS';
        document.getElementById('filtro-vencimento').value = 'TODOS';

        this.state.filtros = {
            dataInicio: null,
            dataFim: null,
            tipoPagamento: 'TODOS',
            statusVencimento: 'TODOS'
        };

        this.carregarContasPendentes();
    },

    toggleSelecao(contaId) {
        const index = this.state.contasSelecionadas.indexOf(contaId);

        if (index > -1) {
            this.state.contasSelecionadas.splice(index, 1);
        } else {
            this.state.contasSelecionadas.push(contaId);
        }

        this.atualizarEstatisticasSelecionadas();
    },

    selecionarTodos(selecionar) {
        const checkboxes = document.querySelectorAll('.checkbox-conta');
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = selecionar;
            const contaId = parseInt(checkbox.value);

            if (selecionar) {
                if (!this.state.contasSelecionadas.includes(contaId)) {
                    this.state.contasSelecionadas.push(contaId);
                }
            } else {
                const index = this.state.contasSelecionadas.indexOf(contaId);
                if (index > -1) {
                    this.state.contasSelecionadas.splice(index, 1);
                }
            }
        });

        this.atualizarEstatisticasSelecionadas();
    },

    async gerarRemessa() {
        if (this.state.contasSelecionadas.length === 0) {
            this.mostrarAlerta('warning', 'Selecione pelo menos uma conta para incluir na remessa');
            return;
        }

        if (!this.state.configuracao) {
            this.mostrarAlerta('error', 'Configure o convênio Sicredi primeiro');
            this.abrirModalConfiguracao();
            return;
        }

        const dataPagamento = document.getElementById('modal-data-pagamento').value;
        const observacoes = document.getElementById('modal-observacoes').value;

        if (!dataPagamento) {
            this.mostrarAlerta('warning', 'Informe a data de pagamento');
            return;
        }

        try {
            this.mostrarLoading(true, 'modal-gerar');

            const response = await fetch('/api/remessa/gerar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    lancamentos: this.state.contasSelecionadas,
                    data_pagamento: dataPagamento,
                    observacoes: observacoes
                })
            });

            const data = await response.json();

            if (data.success) {
                this.mostrarAlerta('success', `Remessa gerada com sucesso! Arquivo: ${data.nome_arquivo}`);
                this.fecharModal('modal-gerar-remessa');

                // Download automático
                this.downloadArquivoCNAB(data.conteudo_cnab, data.nome_arquivo);

                // Recarregar listas
                this.state.contasSelecionadas = [];
                this.carregarContasPendentes();
                this.carregarHistorico();
            } else {
                this.mostrarAlerta('error', data.error);
            }
        } catch (error) {
            console.error('❌ Erro ao gerar remessa:', error);
            this.mostrarAlerta('error', 'Erro ao gerar remessa de pagamento');
        } finally {
            this.mostrarLoading(false, 'modal-gerar');
        }
    },

    async salvarConfiguracao() {
        const config = {
            codigo_beneficiario: document.getElementById('config-codigo-beneficiario').value,
            codigo_convenio: document.getElementById('config-codigo-convenio').value,
            agencia: document.getElementById('config-agencia').value,
            conta: document.getElementById('config-conta').value,
            posto: document.getElementById('config-posto').value,
            codigo_cedente: document.getElementById('config-codigo-cedente').value
        };

        // Validar campos obrigatórios
        if (!config.codigo_beneficiario || !config.codigo_convenio || !config.agencia || !config.conta) {
            this.mostrarAlerta('warning', 'Preencha todos os campos obrigatórios');
            return;
        }

        try {
            this.mostrarLoading(true, 'modal-config');

            const response = await fetch('/api/remessa/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(config)
            });

            const data = await response.json();

            if (data.success) {
                this.mostrarAlerta('success', 'Configuração salva com sucesso!');
                this.fecharModal('modal-configuracao');
                this.carregarConfiguracao();
            } else {
                this.mostrarAlerta('error', data.error);
            }
        } catch (error) {
            console.error('❌ Erro ao salvar configuração:', error);
            this.mostrarAlerta('error', 'Erro ao salvar configuração');
        } finally {
            this.mostrarLoading(false, 'modal-config');
        }
    },

    // =============================================================================
   // UTILITÁRIOS
    // =============================================================================

    formatarData(data) {
        if (!data) return '-';
        const d = new Date(data + 'T00:00:00');
        return d.toLocaleDateString('pt-BR');
    },

    formatarDataHora(dataHora) {
        if (!dataHora) return '-';
        const d = new Date(dataHora);
        return d.toLocaleString('pt-BR');
    },

    formatarMoeda(valor) {
        if (!valor) return 'R$ 0,00';
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor);
    },

    truncar(texto, tamanho) {
        if (!texto) return '';
        return texto.length > tamanho ? texto.substring(0, tamanho) + '...' : texto;
    },

    downloadArquivoCNAB(conteudo, nomeArquivo) {
        const blob = new Blob([conteudo], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = nomeArquivo;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    },

    mostrarLoading(mostrar, contexto = 'principal') {
        const elemento = document.getElementById(`loading-${contexto}`);
        if (elemento) {
            elemento.style.display = mostrar ? 'block' : 'none';
        }
    },

    mostrarAlerta(tipo, mensagem, acao = null) {
        // Implementar sistema de alertas (toast, sweetalert, etc.)
        console.log(`[${tipo.toUpperCase()}] ${mensagem}`);
        alert(mensagem);
    },

    // Métodos auxiliares adicionais
    getClasseVencimento(status) {
        const classes = {
            'VENCIDO': 'danger',
            'VENCE_HOJE': 'warning',
            'VENCE_SEMANA': 'info',
            'A_VENCER': 'secondary'
        };
        return classes[status] || 'secondary';
    },

    getIconeTipo(tipo) {
        const icones = {
            'TED': '<i class="fas fa-university"></i>',
            'PIX': '<i class="fas fa-mobile-alt"></i>',
            'BOLETO': '<i class="fas fa-barcode"></i>',
            'TRIBUTO': '<i class="fas fa-file-invoice-dollar"></i>',
            'INDEFINIDO': '<i class="fas fa-question-circle"></i>'
        };
        return icones[tipo] || '<i class="fas fa-file"></i>';
    },

    getLabelVencimento(status) {
        const labels = {
            'VENCIDO': 'Vencido',
            'VENCE_HOJE': 'Vence hoje',
            'VENCE_SEMANA': 'Vence esta semana',
            'A_VENCER': 'A vencer'
        };
        return labels[status] || status;
    },

    getClasseStatus(status) {
        const classes = {
            'GERADO': 'info',
            'ENVIADO': 'warning',
            'PROCESSADO': 'success',
            'ERRO': 'danger'
        };
        return classes[status] || 'secondary';
    },

    getIconeStatus(status) {
        const icones = {
            'GERADO': '<i class="fas fa-file-alt"></i>',
            'ENVIADO': '<i class="fas fa-paper-plane"></i>',
            'PROCESSADO': '<i class="fas fa-check-circle"></i>',
            'ERRO': '<i class="fas fa-exclamation-triangle"></i>'
        };
        return icones[status] || '<i class="fas fa-file"></i>';
    },

    formatarDadosBancarios(conta) {
        if (conta.tipo_pagamento_sugerido === 'PIX' && conta.chave_pix) {
            return `PIX: ${this.truncar(conta.chave_pix, 20)}`;
        }

        if (conta.tipo_pagamento_sugerido === 'BOLETO' && conta.codigo_barras) {
            return `Boleto: ${this.truncar(conta.codigo_barras, 20)}`;
        }

        if (conta.tipo_pagamento_sugerido === 'TED') {
            return `${conta.banco_favorecido || ''} Ag: ${conta.agencia_favorecido || ''} Cc: ${conta.conta_favorecido || ''}`;
        }

        return '-';
    },

    calcularValorSelecionado() {
        // Buscar valores das contas selecionadas
        let total = 0;
        const tbody = document.getElementById('tabela-contas-body');
        
        if (tbody) {
            const rows = tbody.querySelectorAll('tr');
            rows.forEach(row => {
                const checkbox = row.querySelector('.checkbox-conta');
                if (checkbox && checkbox.checked) {
                    // Extrair valor da célula (formato: R$ 1.234,56)
                    const valorCell = row.cells[3].textContent.trim();
                    const valorNumerico = parseFloat(valorCell.replace('R$', '').replace(/\./g, '').replace(',', '.'));
                    if (!isNaN(valorNumerico)) {
                        total += valorNumerico;
                    }
                }
            });
        }
        
        return total;
    },

    atualizarEstatisticasSelecionadas() {
        const selecionadas = this.state.contasSelecionadas.length;
        const valorSelecionado = this.calcularValorSelecionado();
        
        document.getElementById('stat-selecionadas').textContent = selecionadas;
        document.getElementById('stat-valor-selecionado').textContent = this.formatarMoeda(valorSelecionado);

        // Habilitar/desabilitar botão gerar remessa
        const btnGerar = document.getElementById('btn-gerar-remessa');
        if (btnGerar) {
            btnGerar.disabled = selecionadas === 0;
        }
    },

    abrirModalGerarRemessa() {
        if (this.state.contasSelecionadas.length === 0) {
            this.mostrarAlerta('warning', 'Selecione pelo menos uma conta para incluir na remessa');
            return;
        }

        // Definir data padrão (próximo dia útil)
        const hoje = new Date();
        const dataMinima = new Date(hoje);
        dataMinima.setDate(dataMinima.getDate() + 1);

        document.getElementById('modal-data-pagamento').min = dataMinima.toISOString().split('T')[0];
        document.getElementById('modal-data-pagamento').value = dataMinima.toISOString().split('T')[0];

        this.abrirModal('modal-gerar-remessa');
    },

    abrirModalConfiguracao() {
        // Carregar configuração atual se existir
        if (this.state.configuracao) {
            document.getElementById('config-codigo-beneficiario').value = this.state.configuracao.codigo_beneficiario || '';
            document.getElementById('config-codigo-convenio').value = this.state.configuracao.codigo_convenio || '';
            document.getElementById('config-agencia').value = this.state.configuracao.agencia || '';
            document.getElementById('config-conta').value = this.state.configuracao.conta || '';
            document.getElementById('config-posto').value = this.state.configuracao.posto || '';
            document.getElementById('config-codigo-cedente').value = this.state.configuracao.codigo_cedente || '';
        }

        this.abrirModal('modal-configuracao');
    },

    abrirModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    },

    fecharModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    },

    async downloadRemessa(remessaId) {
        try {
            const response = await fetch(`/api/remessa/${remessaId}/download`, {
                method: 'GET',
                credentials: 'include'
            });

            if (response.ok) {
                const blob = await response.blob();
                const contentDisposition = response.headers.get('Content-Disposition');
                const filename = contentDisposition ? contentDisposition.split('filename=')[1].replace(/"/g, '') : `remessa_${remessaId}.txt`;

                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);

                this.mostrarAlerta('success', 'Arquivo baixado com sucesso!');
            } else {
                this.mostrarAlerta('error', 'Erro ao baixar arquivo');
            }
        } catch (error) {
            console.error('❌ Erro ao baixar remessa:', error);
            this.mostrarAlerta('error', 'Erro ao baixar arquivo da remessa');
        }
    },

    async visualizarRemessa(remessaId) {
        try {
            const response = await fetch(`/api/remessa/${remessaId}`, {
                method: 'GET',
                credentials: 'include'
            });

            const data = await response.json();

            if (data.success) {
                this.mostrarDetalhesRemessa(data.remessa);
            } else {
                this.mostrarAlerta('error', data.error);
            }
        } catch (error) {
            console.error('❌ Erro ao visualizar remessa:', error);
            this.mostrarAlerta('error', 'Erro ao carregar detalhes da remessa');
        }
    },

    mostrarDetalhesRemessa(remessa) {
        // Implementar modal com detalhes da remessa
        console.log('Detalhes da remessa:', remessa);
        alert(`Remessa #${remessa.numero_sequencial}\n\nQuantidade: ${remessa.quantidade_pagamentos}\nValor: ${this.formatarMoeda(remessa.valor_total)}\nStatus: ${remessa.status}`);
    },

    visualizarDetalhe(contaId) {
        // Implementar modal com detalhes da conta
        console.log('Visualizar conta:', contaId);
        alert(`Detalhes da conta #${contaId}`);
    }
};

// Inicializar quando carregar a seção
window.RemessaPagamento = RemessaPagamento;
