// ===================================
// FUNÇÕES DE EXPORTAÇÃO PARA EXCEL
// ===================================

console.log('✓ Funções Excel profissionais carregadas - v20251206');

// Garante que a biblioteca XLSX está carregada antes de usar (lazy load)
function _ensureXLSX(callback) {
    if (typeof XLSX !== 'undefined') { callback(); return; }
    if (typeof window.loadXLSX === 'function') {
        window.loadXLSX(callback);
    } else {
        // Fallback: carregar diretamente se o lazy loader não estiver disponível
        var s = document.createElement('script');
        s.src = 'https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js';
        s.onload = callback;
        document.head.appendChild(s);
    }
}

// Exportar Contas a Pagar para Excel
async function exportarContasPagarExcel() {
    if (typeof XLSX === 'undefined') {
        if (typeof showToast === 'function') showToast('⏳ Preparando exportação...', 'info');
        _ensureXLSX(() => exportarContasPagarExcel());
        return;
    }
    try {
        console.log('=== INÍCIO EXPORTAÇÃO CONTAS A PAGAR EXCEL ===');
        
        // Mostrar loading
        if (typeof showToast === 'function') {
            showToast('⏳ Gerando arquivo Excel...', 'info');
        }
        
        // Obter filtros atuais
        const filtros = {
            status: document.getElementById('filter-status-pagar')?.value || '',
            categoria: document.getElementById('filter-categoria-pagar')?.value || '',
            mes: document.getElementById('filter-mes-pagar')?.value || '',
            ano: document.getElementById('filter-ano-pagar')?.value || ''
        };
        
        console.log('Filtros aplicados:', filtros);
        
        // Buscar dados
        const response = await fetch('/api/lancamentos?tipo=despesa');
        const resultado = await response.json();
        const todosLancamentos = resultado.data || [];
        console.log('Total de lançamentos recebidos:', todosLancamentos.length);
        
        // Aplicar filtros
        const lancamentos = todosLancamentos.filter(l => {
            if (filtros.status) {
                const statusUpper = (l.status || '').toUpperCase();
                const filtroStatusUpper = filtros.status.toUpperCase();
                if (filtroStatusUpper === 'PENDENTE') {
                    if (statusUpper !== 'PENDENTE' && statusUpper !== 'VENCIDO') {
                        return false;
                    }
                } else if (statusUpper !== filtroStatusUpper) {
                    return false;
                }
            }
            if (filtros.categoria && l.categoria !== filtros.categoria) return false;
            
            const dataVenc = new Date(l.data_vencimento);
            if (filtros.ano) {
                if (dataVenc.getFullYear() !== parseInt(filtros.ano)) return false;
            } else if (filtros.mes) {
                if ((dataVenc.getMonth() + 1) !== parseInt(filtros.mes)) return false;
            }
            
            return true;
        });
        
        console.log('Lançamentos após filtro:', lancamentos.length);
        
        // Ordenar por data
        lancamentos.sort((a, b) => new Date(a.data_vencimento) - new Date(b.data_vencimento));
        
        // Calcular totais
        const totais = {
            pendente: 0,
            vencido: 0,
            pago: 0,
            cancelado: 0
        };
        
        const hoje = new Date();
        hoje.setHours(0, 0, 0, 0);
        
        lancamentos.forEach(l => {
            const valor = parseFloat(l.valor) || 0;
            const status = (l.status || '').toUpperCase();
            const dataVenc = new Date(l.data_vencimento);
            dataVenc.setHours(0, 0, 0, 0);
            
            // Se status é PENDENTE e data vencida, considerar como VENCIDO
            const statusReal = (status === 'PENDENTE' && dataVenc < hoje) ? 'VENCIDO' : status;
            
            if (statusReal === 'PENDENTE') totais.pendente += valor;
            else if (statusReal === 'VENCIDO') totais.vencido += valor;
            else if (statusReal === 'PAGO') totais.pago += valor;
            else if (statusReal === 'CANCELADO') totais.cancelado += valor;
        });
        
        console.log('TOTAIS CALCULADOS:', totais);
        
        // Preparar dados para Excel
        const dados = [];
        
        // Cabeçalho
        dados.push(['CONTAS A PAGAR']);
        dados.push([]);
        
        // Período
        const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
        let periodo = 'Todos os Períodos';
        if (filtros.ano && filtros.mes) {
            periodo = `${meses[parseInt(filtros.mes) - 1]} de ${filtros.ano}`;
        } else if (filtros.ano) {
            periodo = `Ano ${filtros.ano}`;
        } else if (filtros.mes) {
            periodo = meses[parseInt(filtros.mes) - 1];
        }
        dados.push(['Período:', periodo]);
        dados.push(['Total de Registros:', lancamentos.length]);
        dados.push([]);
        
        // Cabeçalhos da tabela
        dados.push(['Data Venc.', 'Fornecedor', 'Categoria', 'Subcategoria', 'Descrição', 'Valor', 'Status', 'Data Pgto.']);
        
        // Linhas de dados
        lancamentos.forEach(l => {
            const dataVenc = new Date(l.data_vencimento).toLocaleDateString('pt-BR');
            const dataPgto = l.data_pagamento ? new Date(l.data_pagamento).toLocaleDateString('pt-BR') : '-';
            const valor = parseFloat(l.valor);
            
            // Calcular status real
            const dataVencimento = new Date(l.data_vencimento);
            dataVencimento.setHours(0, 0, 0, 0);
            const status = (l.status.toUpperCase() === 'PENDENTE' && dataVencimento < hoje) ? 'vencido' : l.status;
            
            dados.push([
                dataVenc,
                l.pessoa || '-',
                l.categoria || '-',
                l.subcategoria || '-',
                l.descricao || '-',
                valor,
                status,
                dataPgto
            ]);
        });
        
        // Linha vazia antes dos totais
        dados.push([]);
        
        // Totais
        if (filtros.status) {
            const statusUpper = filtros.status.toUpperCase();
            if (statusUpper === 'PENDENTE') {
                dados.push(['TOTAL PENDENTE:', '', '', '', '', totais.pendente]);
                dados.push(['TOTAL VENCIDO:', '', '', '', '', totais.vencido]);
            } else if (statusUpper === 'PAGO') {
                dados.push(['TOTAL PAGO:', '', '', '', '', totais.pago]);
            } else if (statusUpper === 'CANCELADO') {
                dados.push(['TOTAL CANCELADO:', '', '', '', '', totais.cancelado]);
            }
        } else {
            dados.push(['TOTAL PENDENTE:', '', '', '', '', totais.pendente]);
            dados.push(['TOTAL VENCIDO:', '', '', '', '', totais.vencido]);
            dados.push(['TOTAL PAGO:', '', '', '', '', totais.pago]);
        }
        
        // Criar workbook e worksheet
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.aoa_to_sheet(dados);
        
        // Ajustar largura das colunas
        ws['!cols'] = [
            { wch: 12 },  // Data Venc.
            { wch: 25 },  // Fornecedor
            { wch: 20 },  // Categoria
            { wch: 20 },  // Subcategoria
            { wch: 30 },  // Descrição
            { wch: 15 },  // Valor
            { wch: 12 },  // Status
            { wch: 12 }   // Data Pgto.
        ];
        
        // Adicionar worksheet ao workbook
        XLSX.utils.book_append_sheet(wb, ws, 'Contas a Pagar');
        
        // Gerar nome do arquivo
        const dataAtual = new Date().toLocaleDateString('pt-BR').replace(/\//g, '-');
        const nomeArquivo = `Contas_a_Pagar_${dataAtual}.xlsx`;
        
        // Salvar arquivo
        XLSX.writeFile(wb, nomeArquivo);
        
        console.log('Excel exportado com sucesso:', nomeArquivo);
        
    } catch (erro) {
        console.error('Erro ao gerar Excel:', erro);
        alert('Erro ao gerar arquivo Excel: ' + erro.message);
    }
}

// Exportar Contas a Receber para Excel
async function exportarContasReceberExcel() {
    if (typeof XLSX === 'undefined') {
        if (typeof showToast === 'function') showToast('⏳ Preparando exportação...', 'info');
        _ensureXLSX(() => exportarContasReceberExcel());
        return;
    }
    try {
        console.log('=== INÍCIO EXPORTAÇÃO CONTAS A RECEBER EXCEL ===');
        
        // Mostrar loading
        if (typeof showToast === 'function') {
            showToast('⏳ Gerando arquivo Excel...', 'info');
        }
        
        // Obter filtros atuais
        const filtros = {
            status: document.getElementById('filter-status-receber')?.value || '',
            categoria: document.getElementById('filter-categoria-receber')?.value || '',
            mes: document.getElementById('filter-mes-receber')?.value || '',
            ano: document.getElementById('filter-ano-receber')?.value || ''
        };
        
        console.log('Filtros aplicados:', filtros);
        
        // Buscar dados
        const response = await fetch('/api/lancamentos?tipo=receita');
        const resultado = await response.json();
        const todosLancamentos = resultado.data || [];
        console.log('Total de lançamentos recebidos:', todosLancamentos.length);
        
        // Aplicar filtros
        const lancamentos = todosLancamentos.filter(l => {
            if (filtros.status) {
                const statusUpper = (l.status || '').toUpperCase();
                const filtroStatusUpper = filtros.status.toUpperCase();
                if (filtroStatusUpper === 'PENDENTE') {
                    if (statusUpper !== 'PENDENTE' && statusUpper !== 'VENCIDO') {
                        return false;
                    }
                } else if (statusUpper !== filtroStatusUpper) {
                    return false;
                }
            }
            if (filtros.categoria && l.categoria !== filtros.categoria) return false;
            
            const dataVenc = new Date(l.data_vencimento);
            if (filtros.ano) {
                if (dataVenc.getFullYear() !== parseInt(filtros.ano)) return false;
            } else if (filtros.mes) {
                if ((dataVenc.getMonth() + 1) !== parseInt(filtros.mes)) return false;
            }
            
            return true;
        });
        
        console.log('Lançamentos após filtro:', lancamentos.length);
        
        // Ordenar por data
        lancamentos.sort((a, b) => new Date(a.data_vencimento) - new Date(b.data_vencimento));
        
        // Calcular totais
        const totais = {
            pendente: 0,
            vencido: 0,
            pago: 0,
            cancelado: 0
        };
        
        const hoje = new Date();
        hoje.setHours(0, 0, 0, 0);
        
        lancamentos.forEach(l => {
            const valor = parseFloat(l.valor) || 0;
            const status = (l.status || '').toUpperCase();
            const dataVenc = new Date(l.data_vencimento);
            dataVenc.setHours(0, 0, 0, 0);
            
            // Se status é PENDENTE e data vencida, considerar como VENCIDO
            const statusReal = (status === 'PENDENTE' && dataVenc < hoje) ? 'VENCIDO' : status;
            
            if (statusReal === 'PENDENTE') totais.pendente += valor;
            else if (statusReal === 'VENCIDO') totais.vencido += valor;
            else if (statusReal === 'PAGO') totais.pago += valor;
            else if (statusReal === 'CANCELADO') totais.cancelado += valor;
        });
        
        console.log('TOTAIS CALCULADOS:', totais);
        
        // Preparar dados para Excel
        const dados = [];
        
        // Cabeçalho
        dados.push(['CONTAS A RECEBER']);
        dados.push([]);
        
        // Período
        const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
        let periodo = 'Todos os Períodos';
        if (filtros.ano && filtros.mes) {
            periodo = `${meses[parseInt(filtros.mes) - 1]} de ${filtros.ano}`;
        } else if (filtros.ano) {
            periodo = `Ano ${filtros.ano}`;
        } else if (filtros.mes) {
            periodo = meses[parseInt(filtros.mes) - 1];
        }
        dados.push(['Período:', periodo]);
        dados.push(['Total de Registros:', lancamentos.length]);
        dados.push([]);
        
        // Cabeçalhos da tabela
        dados.push(['Data Venc.', 'Cliente', 'Categoria', 'Subcategoria', 'Descrição', 'Valor', 'Status', 'Data Pgto.']);
        
        // Linhas de dados
        lancamentos.forEach(l => {
            const dataVenc = new Date(l.data_vencimento).toLocaleDateString('pt-BR');
            const dataPgto = l.data_pagamento ? new Date(l.data_pagamento).toLocaleDateString('pt-BR') : '-';
            const valor = parseFloat(l.valor);
            
            // Calcular status real
            const dataVencimento = new Date(l.data_vencimento);
            dataVencimento.setHours(0, 0, 0, 0);
            const status = (l.status.toUpperCase() === 'PENDENTE' && dataVencimento < hoje) ? 'vencido' : l.status;
            
            dados.push([
                dataVenc,
                l.pessoa || '-',
                l.categoria || '-',
                l.subcategoria || '-',
                l.descricao || '-',
                valor,
                status,
                dataPgto
            ]);
        });
        
        // Linha vazia antes dos totais
        dados.push([]);
        
        // Totais
        if (filtros.status) {
            const statusUpper = filtros.status.toUpperCase();
            if (statusUpper === 'PENDENTE') {
                dados.push(['TOTAL PENDENTE:', '', '', '', '', totais.pendente]);
                dados.push(['TOTAL VENCIDO:', '', '', '', '', totais.vencido]);
            } else if (statusUpper === 'PAGO') {
                dados.push(['TOTAL PAGO:', '', '', '', '', totais.pago]);
            } else if (statusUpper === 'CANCELADO') {
                dados.push(['TOTAL CANCELADO:', '', '', '', '', totais.cancelado]);
            }
        } else {
            dados.push(['TOTAL PENDENTE:', '', '', '', '', totais.pendente]);
            dados.push(['TOTAL VENCIDO:', '', '', '', '', totais.vencido]);
            dados.push(['TOTAL PAGO:', '', '', '', '', totais.pago]);
        }
        
        // Criar workbook e worksheet
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.aoa_to_sheet(dados);
        
        // Ajustar largura das colunas
        ws['!cols'] = [
            { wch: 12 },  // Data Venc.
            { wch: 25 },  // Cliente
            { wch: 20 },  // Categoria
            { wch: 20 },  // Subcategoria
            { wch: 30 },  // Descrição
            { wch: 15 },  // Valor
            { wch: 12 },  // Status
            { wch: 12 }   // Data Pgto.
        ];
        
        // Adicionar worksheet ao workbook
        XLSX.utils.book_append_sheet(wb, ws, 'Contas a Receber');
        
        // Gerar nome do arquivo
        const dataAtual = new Date().toLocaleDateString('pt-BR').replace(/\//g, '-');
        const nomeArquivo = `Contas_a_Receber_${dataAtual}.xlsx`;
        
        // Salvar arquivo
        XLSX.writeFile(wb, nomeArquivo);
        
        console.log('Excel exportado com sucesso:', nomeArquivo);
        
        // Mostrar sucesso
        if (typeof showToast === 'function') {
            showToast(`✅ Arquivo Excel gerado: ${nomeArquivo}`, 'success');
        }
        
    } catch (erro) {
        console.error('Erro ao gerar Excel:', erro);
        if (typeof showToast === 'function') {
            showToast('❌ Erro ao gerar arquivo Excel: ' + erro.message, 'error');
        } else {
            alert('Erro ao gerar arquivo Excel: ' + erro.message);
        }
    }
}
// ========== EXPORTAÇÃO DE CLIENTES EXCEL ==========
async function exportarClientesExcel() {
    try {
        console.log('📊 Exportando clientes para Excel...');
        
        // Redirecionar para o endpoint de exportação
        window.open('/api/clientes/exportar/excel', '_blank');
        
        showToast('✅ Excel de clientes gerado com sucesso!', 'success');
    } catch (error) {
        console.error('❌ Erro ao exportar clientes Excel:', error);
        showToast('Erro ao gerar Excel de clientes: ' + error.message, 'error');
    }
}

// ========== EXPORTAÇÃO DE FORNECEDORES EXCEL ==========
async function exportarFornecedoresExcel() {
    try {
        console.log('📊 Exportando fornecedores para Excel...');
        
        // Redirecionar para o endpoint de exportação
        window.open('/api/fornecedores/exportar/excel', '_blank');
        
        showToast('✅ Excel de fornecedores gerado com sucesso!', 'success');
    } catch (error) {
        console.error('❌ Erro ao exportar fornecedores Excel:', error);
        showToast('Erro ao gerar Excel de fornecedores: ' + error.message, 'error');
    }
}

// ========== EXPOR FUNÇÕES GLOBALMENTE ==========
window.exportarContasPagarExcel = exportarContasPagarExcel;
window.exportarContasReceberExcel = exportarContasReceberExcel;
window.exportarClientesExcel = exportarClientesExcel;
window.exportarFornecedoresExcel = exportarFornecedoresExcel;

console.log('✅ Funções Excel expostas globalmente:', {
    exportarContasPagarExcel: typeof window.exportarContasPagarExcel,
    exportarContasReceberExcel: typeof window.exportarContasReceberExcel,
    exportarClientesExcel: typeof window.exportarClientesExcel,
    exportarFornecedoresExcel: typeof window.exportarFornecedoresExcel
});
