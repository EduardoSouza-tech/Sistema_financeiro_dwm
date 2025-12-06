// ===================================
// FUNÇÕES DE EXPORTAÇÃO PARA EXCEL
// ===================================

console.log('✓ Funções Excel profissionais carregadas - v20251206');

// Exportar Contas a Pagar para Excel
async function exportarContasPagarExcel() {
    try {
        console.log('=== INÍCIO EXPORTAÇÃO CONTAS A PAGAR EXCEL ===');
        
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
        const todosLancamentos = await response.json();
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
    try {
        console.log('=== INÍCIO EXPORTAÇÃO CONTAS A RECEBER EXCEL ===');
        
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
        const todosLancamentos = await response.json();
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
        
    } catch (erro) {
        console.error('Erro ao gerar Excel:', erro);
        alert('Erro ao gerar arquivo Excel: ' + erro.message);
    }
}
