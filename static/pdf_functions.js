// ========== FUNÇÕES DE EXPORTAÇÃO PDF PROFISSIONAL ==========

async function exportarContasPagarPDF() {
    try {
        console.log('=== INÍCIO EXPORTAÇÃO CONTAS A PAGAR PDF ===');
        
        // Capturar filtros aplicados
        const filtros = {
            status: document.getElementById('filter-status-pagar')?.value || '',
            categoria: document.getElementById('filter-categoria-pagar')?.value || '',
            fornecedor: document.getElementById('filter-fornecedor')?.value || '',
            ano: document.getElementById('filter-ano-pagar')?.value || '',
            mes: document.getElementById('filter-mes-pagar')?.value || '',
            dataInicio: document.getElementById('filter-data-inicio-pagar')?.value || '',
            dataFim: document.getElementById('filter-data-fim-pagar')?.value || ''
        };
        
        console.log('Filtros aplicados:', filtros);
        
        // Buscar lançamentos
        const response = await fetch('/api/lancamentos?tipo=despesa');
        const resultado = await response.json();
        const todosLancamentos = resultado.data || [];
        
        console.log('Total de lançamentos recebidos:', todosLancamentos.length);
        
        // Aplicar filtros
        const lancamentos = todosLancamentos.filter(l => {
            if (filtros.status) {
                const statusUpper = (l.status || '').toUpperCase();
                const filtroStatusUpper = filtros.status.toUpperCase();
                console.log(`Verificando lançamento: status="${l.status}", statusUpper="${statusUpper}", filtro="${filtros.status}", filtroUpper="${filtroStatusUpper}"`);
                // Se filtrar PENDENTE, incluir PENDENTE e VENCIDO
                if (filtroStatusUpper === 'PENDENTE') {
                    if (statusUpper !== 'PENDENTE' && statusUpper !== 'VENCIDO') {
                        console.log(`  -> Rejeitado (não é PENDENTE nem VENCIDO)`);
                        return false;
                    }
                    console.log(`  -> Aceito (é PENDENTE ou VENCIDO)`);
                } else if (statusUpper !== filtroStatusUpper) {
                    return false;
                }
            }
            if (filtros.categoria && l.categoria !== filtros.categoria) return false;
            if (filtros.fornecedor && l.pessoa !== filtros.fornecedor) return false;
            
            const dataVenc = new Date(l.data_vencimento);
            
            if (filtros.dataInicio && filtros.dataFim) {
                const inicio = new Date(filtros.dataInicio);
                const fim = new Date(filtros.dataFim);
                if (dataVenc < inicio || dataVenc > fim) return false;
            } else if (filtros.ano && filtros.mes) {
                if (dataVenc.getFullYear() !== parseInt(filtros.ano) || 
                    (dataVenc.getMonth() + 1) !== parseInt(filtros.mes)) return false;
            } else if (filtros.ano) {
                if (dataVenc.getFullYear() !== parseInt(filtros.ano)) return false;
            } else if (filtros.mes) {
                if ((dataVenc.getMonth() + 1) !== parseInt(filtros.mes)) return false;
            }
            
            return true;
        });
        
        console.log('Lançamentos após filtro:', lancamentos.length);
        if (lancamentos.length > 0) {
            console.log('Primeiro lançamento:', lancamentos[0]);
        }
        
        // Ordenar por data de vencimento
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
        
        console.log('TOTAIS CALCULADOS:', `Pendente: ${totais.pendente}, Vencido: ${totais.vencido}, Pago: ${totais.pago}, Cancelado: ${totais.cancelado}`);
        
        // Montar título
        const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
        let periodo = 'Todos os Períodos';
        
        if (filtros.dataInicio && filtros.dataFim) {
            periodo = `${new Date(filtros.dataInicio).toLocaleDateString('pt-BR')} a ${new Date(filtros.dataFim).toLocaleDateString('pt-BR')}`;
        } else if (filtros.ano && filtros.mes) {
            periodo = `${meses[parseInt(filtros.mes) - 1]}/${filtros.ano}`;
        } else if (filtros.ano) {
            periodo = `Ano ${filtros.ano}`;
        } else if (filtros.mes) {
            periodo = meses[parseInt(filtros.mes) - 1];
        }
        
        // Gerar PDF
        const win = window.open('', '_blank');
        if (!win) {
            alert('Bloqueador de pop-up ativo. Por favor, permita pop-ups para este site.');
            return;
        }
        
        win.document.write(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Contas a Pagar</title>
    <style>
        @page { size: landscape; margin: 15mm; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; font-size: 10pt; color: #333; }
        
        .cabecalho {
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 15px;
            margin-bottom: 15px;
        }
        .cabecalho h1 {
            font-size: 24pt;
            color: #2c3e50;
            margin-bottom: 8px;
        }
        .cabecalho .periodo {
            font-size: 12pt;
            color: #555;
            margin-bottom: 5px;
        }
        .cabecalho .info {
            font-size: 9pt;
            color: #888;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th {
            background: #34495e;
            color: white;
            padding: 10px 8px;
            text-align: left;
            font-size: 9pt;
            font-weight: bold;
        }
        td {
            padding: 8px;
            border-bottom: 1px solid #ddd;
            font-size: 9pt;
        }
        tbody tr:nth-child(odd) { background: #f9f9f9; }
        tbody tr:nth-child(even) { background: white; }
        
        .valor { text-align: right; font-weight: 500; }
        .status-PENDENTE { color: #e74c3c; font-weight: bold; }
        .status-PAGO { color: #27ae60; font-weight: bold; }
        .status-CANCELADO { color: #95a5a6; font-weight: bold; }
        
        .totais-container {
            margin-top: 30px;
            border-top: 3px solid #2c3e50;
            padding-top: 20px;
        }
        .linha-total {
            display: flex;
            justify-content: flex-end;
            padding: 8px 0;
            font-size: 11pt;
        }
        .linha-total .label {
            font-weight: bold;
            margin-right: 20px;
            min-width: 200px;
            text-align: right;
        }
        .linha-total .valor-total {
            font-weight: bold;
            min-width: 150px;
            text-align: right;
        }
        .total-geral {
            background: #d5e8d4;
            padding: 12px 20px;
            border-radius: 5px;
            margin-top: 10px;
            border: 2px solid #27ae60;
            font-size: 13pt;
        }
        
        @media print {
            body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
        }
    </style>
</head>
<body>
    <div class="cabecalho">
        <h1>CONTAS A PAGAR</h1>
        <div class="periodo">${periodo}</div>
        <div class="info">Gerado em ${new Date().toLocaleString('pt-BR')} • ${lancamentos.length} registro(s)</div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th style="width: 10%;">Data Venc.</th>
                <th style="width: 18%;">Fornecedor</th>
                <th style="width: 14%;">Categoria</th>
                <th style="width: 14%;">Subcategoria</th>
                <th style="width: 20%;">Descrição</th>
                <th style="width: 10%;">Valor</th>
                <th style="width: 8%;">Status</th>
                <th style="width: 10%;">Data Pgto.</th>
            </tr>
        </thead>
        <tbody>
`);
        
        // Linhas de dados
        lancamentos.forEach(l => {
            const dataVenc = new Date(l.data_vencimento).toLocaleDateString('pt-BR');
            const dataPgto = l.data_pagamento ? new Date(l.data_pagamento).toLocaleDateString('pt-BR') : '-';
            const valor = parseFloat(l.valor).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            
            // Calcular status real (verificar se está vencido)
            const dataVencimento = new Date(l.data_vencimento);
            dataVencimento.setHours(0, 0, 0, 0);
            const status = (l.status.toUpperCase() === 'PENDENTE' && dataVencimento < hoje) ? 'vencido' : l.status;
            
            win.document.write(`
            <tr>
                <td>${dataVenc}</td>
                <td>${l.pessoa || '-'}</td>
                <td>${l.categoria || '-'}</td>
                <td>${l.subcategoria || '-'}</td>
                <td>${l.descricao || '-'}</td>
                <td class="valor">R$ ${valor}</td>
                <td class="status-${status}">${status}</td>
                <td>${dataPgto}</td>
            </tr>`);
        });
        
        // Totais no final da página
        win.document.write(`
        </tbody>
    </table>
    
    <div class="totais-container">`);
        
        if (filtros.status) {
            // Com filtro: mostrar apenas o total do status filtrado
            const statusUpper = filtros.status.toUpperCase();
            if (statusUpper === 'PENDENTE') {
                // Quando filtrar PENDENTE, mostrar PENDENTE + VENCIDO separadamente
                const totalPendenteVencido = totais.pendente + totais.vencido;
                console.log(`Exibindo total filtrado PENDENTE: ${totais.pendente}, VENCIDO: ${totais.vencido}, Total: ${totalPendenteVencido}`);
                win.document.write(`
        <div class="linha-total">
            <div class="label">TOTAL PENDENTE:</div>
            <div class="valor-total">R$ ${totais.pendente.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="linha-total">
            <div class="label">TOTAL VENCIDO:</div>
            <div class="valor-total">R$ ${totais.vencido.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>`);
            } else {
                const valorTotal = statusUpper === 'PAGO' ? totais.pago : totais.cancelado;
                console.log(`Exibindo total filtrado: status=${statusUpper}, valor=${valorTotal}`);
                win.document.write(`
        <div class="linha-total">
            <div class="label">TOTAL ${statusUpper}:</div>
            <div class="valor-total">R$ ${valorTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>`);
            }
        } else {
            // Sem filtro: mostrar todos os totais
            win.document.write(`
        <div class="linha-total">
            <div class="label">TOTAL PENDENTE:</div>
            <div class="valor-total">R$ ${totais.pendente.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="linha-total">
            <div class="label">TOTAL VENCIDO:</div>
            <div class="valor-total">R$ ${totais.vencido.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="linha-total">
            <div class="label">TOTAL PAGO:</div>
            <div class="valor-total">R$ ${totais.pago.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="linha-total">
            <div class="label">TOTAL CANCELADO:</div>
            <div class="valor-total">R$ ${totais.cancelado.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>`);
        }
        
        win.document.write(`
    </div>
</body>
</html>`);
        
        win.document.close();
        setTimeout(() => win.print(), 250);
        
    } catch (error) {
        console.error('Erro ao gerar PDF:', error);
        alert('Erro ao gerar PDF: ' + error.message);
    }
}

async function exportarContasReceberPDF() {
    try {
        console.log('=== INÍCIO EXPORTAÇÃO CONTAS A RECEBER PDF ===');
        
        // Capturar filtros aplicados
        const filtros = {
            status: document.getElementById('filter-status-receber')?.value || '',
            categoria: document.getElementById('filter-categoria-receber')?.value || '',
            cliente: document.getElementById('filter-cliente')?.value || '',
            ano: document.getElementById('filter-ano-receber')?.value || '',
            mes: document.getElementById('filter-mes-receber')?.value || '',
            dataInicio: document.getElementById('filter-data-inicio-receber')?.value || '',
            dataFim: document.getElementById('filter-data-fim-receber')?.value || ''
        };
        
        console.log('Filtros aplicados:', filtros);
        
        // Buscar lançamentos
        const response = await fetch('/api/lancamentos?tipo=receita');
        const resultado = await response.json();
        const todosLancamentos = resultado.data || [];
        
        console.log('Total de lançamentos recebidos:', todosLancamentos.length);
        
        // Aplicar filtros
        const lancamentos = todosLancamentos.filter(l => {
            if (filtros.status) {
                const statusUpper = (l.status || '').toUpperCase();
                const filtroStatusUpper = filtros.status.toUpperCase();
                console.log(`[RECEBER] Verificando lançamento: status="${l.status}", statusUpper="${statusUpper}", filtro="${filtros.status}", filtroUpper="${filtroStatusUpper}"`);
                // Se filtrar PENDENTE, incluir PENDENTE e VENCIDO
                if (filtroStatusUpper === 'PENDENTE') {
                    if (statusUpper !== 'PENDENTE' && statusUpper !== 'VENCIDO') {
                        console.log(`  -> Rejeitado (não é PENDENTE nem VENCIDO)`);
                        return false;
                    }
                    console.log(`  -> Aceito (é PENDENTE ou VENCIDO)`);
                } else if (statusUpper !== filtroStatusUpper) {
                    return false;
                }
            }
            if (filtros.categoria && l.categoria !== filtros.categoria) return false;
            if (filtros.cliente && l.pessoa !== filtros.cliente) return false;
            
            const dataVenc = new Date(l.data_vencimento);
            
            if (filtros.dataInicio && filtros.dataFim) {
                const inicio = new Date(filtros.dataInicio);
                const fim = new Date(filtros.dataFim);
                if (dataVenc < inicio || dataVenc > fim) return false;
            } else if (filtros.ano && filtros.mes) {
                if (dataVenc.getFullYear() !== parseInt(filtros.ano) || 
                    (dataVenc.getMonth() + 1) !== parseInt(filtros.mes)) return false;
            } else if (filtros.ano) {
                if (dataVenc.getFullYear() !== parseInt(filtros.ano)) return false;
            } else if (filtros.mes) {
                if ((dataVenc.getMonth() + 1) !== parseInt(filtros.mes)) return false;
            }
            
            return true;
        });
        
        console.log('Lançamentos após filtro:', lancamentos.length);
        if (lancamentos.length > 0) {
            console.log('Primeiro lançamento:', lancamentos[0]);
        }
        
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
        
        console.log('TOTAIS CALCULADOS:', `Pendente: ${totais.pendente}, Vencido: ${totais.vencido}, Pago: ${totais.pago}, Cancelado: ${totais.cancelado}`);
        
        // Montar título
        const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
        let periodo = 'Todos os Períodos';
        
        if (filtros.dataInicio && filtros.dataFim) {
            periodo = `${new Date(filtros.dataInicio).toLocaleDateString('pt-BR')} a ${new Date(filtros.dataFim).toLocaleDateString('pt-BR')}`;
        } else if (filtros.ano && filtros.mes) {
            periodo = `${meses[parseInt(filtros.mes) - 1]}/${filtros.ano}`;
        } else if (filtros.ano) {
            periodo = `Ano ${filtros.ano}`;
        } else if (filtros.mes) {
            periodo = meses[parseInt(filtros.mes) - 1];
        }
        
        // Gerar PDF
        const win = window.open('', '_blank');
        if (!win) {
            alert('Bloqueador de pop-up ativo. Por favor, permita pop-ups para este site.');
            return;
        }
        
        win.document.write(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Contas a Receber</title>
    <style>
        @page { size: landscape; margin: 15mm; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; font-size: 10pt; color: #333; }
        
        .cabecalho {
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 15px;
            margin-bottom: 15px;
        }
        .cabecalho h1 {
            font-size: 24pt;
            color: #2c3e50;
            margin-bottom: 8px;
        }
        .cabecalho .periodo {
            font-size: 12pt;
            color: #555;
            margin-bottom: 5px;
        }
        .cabecalho .info {
            font-size: 9pt;
            color: #888;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th {
            background: #34495e;
            color: white;
            padding: 10px 8px;
            text-align: left;
            font-size: 9pt;
            font-weight: bold;
        }
        td {
            padding: 8px;
            border-bottom: 1px solid #ddd;
            font-size: 9pt;
        }
        tbody tr:nth-child(odd) { background: #f9f9f9; }
        tbody tr:nth-child(even) { background: white; }
        
        .valor { text-align: right; font-weight: 500; }
        .status-PENDENTE { color: #e74c3c; font-weight: bold; }
        .status-PAGO { color: #27ae60; font-weight: bold; }
        .status-CANCELADO { color: #95a5a6; font-weight: bold; }
        
        .totais-container {
            margin-top: 30px;
            border-top: 3px solid #2c3e50;
            padding-top: 20px;
        }
        .linha-total {
            display: flex;
            justify-content: flex-end;
            padding: 8px 0;
            font-size: 11pt;
        }
        .linha-total .label {
            font-weight: bold;
            margin-right: 20px;
            min-width: 200px;
            text-align: right;
        }
        .linha-total .valor-total {
            font-weight: bold;
            min-width: 150px;
            text-align: right;
        }
        .total-geral {
            background: #d5e8d4;
            padding: 12px 20px;
            border-radius: 5px;
            margin-top: 10px;
            border: 2px solid #27ae60;
            font-size: 13pt;
        }
        
        @media print {
            body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
        }
    </style>
</head>
<body>
    <div class="cabecalho">
        <h1>CONTAS A RECEBER</h1>
        <div class="periodo">${periodo}</div>
        <div class="info">Gerado em ${new Date().toLocaleString('pt-BR')} • ${lancamentos.length} registro(s)</div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th style="width: 10%;">Data Venc.</th>
                <th style="width: 18%;">Cliente</th>
                <th style="width: 14%;">Categoria</th>
                <th style="width: 14%;">Subcategoria</th>
                <th style="width: 20%;">Descrição</th>
                <th style="width: 10%;">Valor</th>
                <th style="width: 8%;">Status</th>
                <th style="width: 10%;">Data Pgto.</th>
            </tr>
        </thead>
        <tbody>
`);
        
        // Linhas de dados
        lancamentos.forEach(l => {
            const dataVenc = new Date(l.data_vencimento).toLocaleDateString('pt-BR');
            const dataPgto = l.data_pagamento ? new Date(l.data_pagamento).toLocaleDateString('pt-BR') : '-';
            const valor = parseFloat(l.valor).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            
            // Calcular status real (verificar se está vencido)
            const dataVencimento = new Date(l.data_vencimento);
            dataVencimento.setHours(0, 0, 0, 0);
            const status = (l.status.toUpperCase() === 'PENDENTE' && dataVencimento < hoje) ? 'vencido' : l.status;
            
            win.document.write(`
            <tr>
                <td>${dataVenc}</td>
                <td>${l.pessoa || '-'}</td>
                <td>${l.categoria || '-'}</td>
                <td>${l.subcategoria || '-'}</td>
                <td>${l.descricao || '-'}</td>
                <td class="valor">R$ ${valor}</td>
                <td class="status-${status}">${status}</td>
                <td>${dataPgto}</td>
            </tr>`);
        });
        
        // Totais no final da página
        win.document.write(`
        </tbody>
    </table>
    
    <div class="totais-container">`);
        
        if (filtros.status) {
            // Com filtro: mostrar apenas o total do status filtrado
            const statusUpper = filtros.status.toUpperCase();
            if (statusUpper === 'PENDENTE') {
                // Quando filtrar PENDENTE, mostrar PENDENTE + VENCIDO separadamente
                const totalPendenteVencido = totais.pendente + totais.vencido;
                console.log(`Exibindo total filtrado PENDENTE: ${totais.pendente}, VENCIDO: ${totais.vencido}, Total: ${totalPendenteVencido}`);
                win.document.write(`
        <div class="linha-total">
            <div class="label">TOTAL PENDENTE:</div>
            <div class="valor-total">R$ ${totais.pendente.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="linha-total">
            <div class="label">TOTAL VENCIDO:</div>
            <div class="valor-total">R$ ${totais.vencido.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>`);
            } else {
                const valorTotal = statusUpper === 'PAGO' ? totais.pago : totais.cancelado;
                console.log(`Exibindo total filtrado: status=${statusUpper}, valor=${valorTotal}`);
                win.document.write(`
        <div class="linha-total">
            <div class="label">TOTAL ${statusUpper}:</div>
            <div class="valor-total">R$ ${valorTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>`);
            }
        } else {
            // Sem filtro: mostrar todos os totais
            win.document.write(`
        <div class="linha-total">
            <div class="label">TOTAL PENDENTE:</div>
            <div class="valor-total">R$ ${totais.pendente.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="linha-total">
            <div class="label">TOTAL VENCIDO:</div>
            <div class="valor-total">R$ ${totais.vencido.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="linha-total">
            <div class="label">TOTAL PAGO:</div>
            <div class="valor-total">R$ ${totais.pago.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
        <div class="linha-total">
            <div class="label">TOTAL CANCELADO:</div>
            <div class="valor-total">R$ ${totais.cancelado.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>`);
        }
        
        win.document.write(`
    </div>
</body>
</html>`);
        
        win.document.close();
        setTimeout(() => win.print(), 250);
        
    } catch (error) {
        console.error('Erro ao gerar PDF:', error);
        alert('Erro ao gerar PDF: ' + error.message);
    }
}

// ========== EXPORTAÇÃO DE CLIENTES PDF ==========
async function exportarClientesPDF() {
    try {
        console.log('📄 Exportando clientes para PDF...');
        
        // Redirecionar para o endpoint de exportação
        window.open('/api/clientes/exportar/pdf', '_blank');
        
        showToast('✅ PDF de clientes gerado com sucesso!', 'success');
    } catch (error) {
        console.error('❌ Erro ao exportar clientes PDF:', error);
        showToast('Erro ao gerar PDF de clientes: ' + error.message, 'error');
    }
}

// ========== EXPORTAÇÃO DE FORNECEDORES PDF ==========
async function exportarFornecedoresPDF() {
    try {
        console.log('📄 Exportando fornecedores para PDF...');
        
        // Redirecionar para o endpoint de exportação
        window.open('/api/fornecedores/exportar/pdf', '_blank');
        
        showToast('✅ PDF de fornecedores gerado com sucesso!', 'success');
    } catch (error) {
        console.error('❌ Erro ao exportar fornecedores PDF:', error);
        showToast('Erro ao gerar PDF de fornecedores: ' + error.message, 'error');
    }
}

// Exportar funções globalmente
window.exportarContasPagarPDF = exportarContasPagarPDF;
window.exportarContasReceberPDF = exportarContasReceberPDF;
window.exportarClientesPDF = exportarClientesPDF;
window.exportarFornecedoresPDF = exportarFornecedoresPDF;
