// ===================================
// FUNÇÕES DE ANÁLISE DETALHADA
// ===================================

console.log('✓ Funções de Análise Detalhada carregadas - v20251206');

// Trocar aba de análise
function trocarAbaAnalise(aba) {
    // Remover active de todos os botões
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
        btn.style.borderBottom = '3px solid transparent';
        btn.style.color = '#666';
    });
    
    // Esconder todos os conteúdos
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });
    
    // Ativar aba selecionada
    const btnAtivo = document.getElementById(`tab-${aba}`);
    if (btnAtivo) {
        btnAtivo.classList.add('active');
        btnAtivo.style.borderBottom = '3px solid #2196F3';
        btnAtivo.style.color = '#2196F3';
    }
    
    const contentAtivo = document.getElementById(`content-${aba}`);
    if (contentAtivo) {
        contentAtivo.style.display = 'block';
    }
}

// Carregar resumo por Cliente/Fornecedor
async function carregarResumoParceiros() {
    try {
        const ano = document.getElementById('filter-ano-parceiros')?.value || new Date().getFullYear();
        const mes = document.getElementById('filter-mes-parceiros')?.value || '';
        
        const content = document.getElementById('resumo-parceiros-content');
        content.innerHTML = '<div class="loading">Carregando dados...</div>';
        
        // Buscar receitas e despesas
        const [receitas, despesas] = await Promise.all([
            fetch('/api/lancamentos?tipo=RECEITA').then(r => r.json()),
            fetch('/api/lancamentos?tipo=DESPESA').then(r => r.json())
        ]);
        
        console.log('📊 Receitas totais:', receitas.length);
        console.log('📊 Despesas totais:', despesas.length);
        
        // Filtrar por período
        const filtrarPorPeriodo = (lancamentos) => {
            return lancamentos.filter(l => {
                // Aceitar apenas lançamentos PAGOS
                const status = (l.status || '').toUpperCase();
                if (status !== 'PAGO') return false;
                
                // Usar data de pagamento se existir, senão data de vencimento
                const dataRef = l.data_pagamento || l.data_vencimento;
                if (!dataRef) return false;
                
                const data = new Date(dataRef);
                if (isNaN(data.getTime())) return false;
                
                if (ano && data.getFullYear() !== parseInt(ano)) return false;
                if (mes && (data.getMonth() + 1) !== parseInt(mes)) return false;
                
                return true;
            });
        };
        
        const receitasFiltradas = filtrarPorPeriodo(receitas);
        const despesasFiltradas = filtrarPorPeriodo(despesas);
        
        console.log('📊 Receitas filtradas (PAGAS):', receitasFiltradas.length);
        console.log('📊 Despesas filtradas (PAGAS):', despesasFiltradas.length);
        
        // Agrupar por pessoa
        const resumoPorPessoa = {};
        
        receitasFiltradas.forEach(l => {
            const pessoa = l.pessoa || 'Não informado';
            if (!resumoPorPessoa[pessoa]) {
                resumoPorPessoa[pessoa] = { receitas: 0, despesas: 0, saldo: 0 };
            }
            resumoPorPessoa[pessoa].receitas += parseFloat(l.valor || 0);
        });
        
        despesasFiltradas.forEach(l => {
            const pessoa = l.pessoa || 'Não informado';
            if (!resumoPorPessoa[pessoa]) {
                resumoPorPessoa[pessoa] = { receitas: 0, despesas: 0, saldo: 0 };
            }
            resumoPorPessoa[pessoa].despesas += parseFloat(l.valor || 0);
        });
        
        // Calcular saldo
        Object.keys(resumoPorPessoa).forEach(pessoa => {
            resumoPorPessoa[pessoa].saldo = resumoPorPessoa[pessoa].receitas - resumoPorPessoa[pessoa].despesas;
        });
        
        // Ordenar por maior volume (receitas + despesas)
        const pessoas = Object.keys(resumoPorPessoa).sort((a, b) => {
            const volumeA = resumoPorPessoa[a].receitas + resumoPorPessoa[a].despesas;
            const volumeB = resumoPorPessoa[b].receitas + resumoPorPessoa[b].despesas;
            return volumeB - volumeA;
        });
        
        // Gerar HTML
        let html = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Cliente/Fornecedor</th>
                        <th>Receitas</th>
                        <th>Despesas</th>
                        <th>Saldo</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        let totais = { receitas: 0, despesas: 0, saldo: 0 };
        
        pessoas.forEach(pessoa => {
            const dados = resumoPorPessoa[pessoa];
            totais.receitas += dados.receitas;
            totais.despesas += dados.despesas;
            totais.saldo += dados.saldo;
            
            const saldoClass = dados.saldo >= 0 ? 'positivo' : 'negativo';
            
            html += `
                <tr>
                    <td>${pessoa}</td>
                    <td style="color: #27ae60;">R$ ${dados.receitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td style="color: #e74c3c;">R$ ${dados.despesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td style="color: ${dados.saldo >= 0 ? '#27ae60' : '#e74c3c'}; font-weight: bold;">R$ ${dados.saldo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                </tr>
            `;
        });
        
        html += `
                </tbody>
                <tfoot>
                    <tr style="font-weight: bold; background: #f8f9fa;">
                        <td>TOTAL</td>
                        <td style="color: #27ae60;">R$ ${totais.receitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td style="color: #e74c3c;">R$ ${totais.despesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td style="color: ${totais.saldo >= 0 ? '#27ae60' : '#e74c3c'};">R$ ${totais.saldo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    </tr>
                </tfoot>
            </table>
        `;
        
        // Calcular métricas adicionais
        const numTransacoesReceitas = receitasFiltradas.length;
        const numTransacoesDespesas = despesasFiltradas.length;
        const numParceiros = pessoas.length;
        const ticketMedioReceitas = numTransacoesReceitas > 0 ? totais.receitas / numTransacoesReceitas : 0;
        const ticketMedioDespesas = numTransacoesDespesas > 0 ? totais.despesas / numTransacoesDespesas : 0;
        const saldoLiquido = totais.saldo;
        
        // Encontrar melhor cliente e maior fornecedor
        let melhorCliente = null;
        let maiorReceita = 0;
        let maiorFornecedor = null;
        let maiorDespesa = 0;
        
        pessoas.forEach(pessoa => {
            const dados = resumoPorPessoa[pessoa];
            if (dados.receitas > maiorReceita) {
                maiorReceita = dados.receitas;
                melhorCliente = pessoa;
            }
            if (dados.despesas > maiorDespesa) {
                maiorDespesa = dados.despesas;
                maiorFornecedor = pessoa;
            }
        });
        
        // Adicionar resumo executivo
        html += `
            <div style="margin-top: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h3 style="margin: 0 0 20px 0; color: #333; font-size: 16px; border-bottom: 2px solid #333; padding-bottom: 10px;">📊 RESUMO EXECUTIVO</h3>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                    <div style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">🏆 MELHOR CLIENTE</div>
                        <div style="font-size: 14px; font-weight: bold; color: #333; margin-bottom: 3px;">${melhorCliente || 'N/A'}</div>
                        <div style="font-size: 16px; font-weight: bold; color: #27ae60;">R$ ${maiorReceita.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    </div>
                    
                    <div style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">📊 MAIOR FORNECEDOR</div>
                        <div style="font-size: 14px; font-weight: bold; color: #333; margin-bottom: 3px;">${maiorFornecedor || 'N/A'}</div>
                        <div style="font-size: 16px; font-weight: bold; color: #e74c3c;">R$ ${maiorDespesa.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    </div>
                    
                    <div style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">📈 TICKET MÉDIO (Receitas)</div>
                        <div style="font-size: 14px; color: #666; margin-bottom: 3px;">${numTransacoesReceitas} transações</div>
                        <div style="font-size: 16px; font-weight: bold; color: #27ae60;">R$ ${ticketMedioReceitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    </div>
                    
                    <div style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">📉 TICKET MÉDIO (Despesas)</div>
                        <div style="font-size: 14px; color: #666; margin-bottom: 3px;">${numTransacoesDespesas} transações</div>
                        <div style="font-size: 16px; font-weight: bold; color: #e74c3c;">R$ ${ticketMedioDespesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    </div>
                    
                    <div style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">🔢 TOTAL DE PARCEIROS</div>
                        <div style="font-size: 14px; color: #666; margin-bottom: 3px;">Analisados no período</div>
                        <div style="font-size: 16px; font-weight: bold; color: #333;">${numParceiros}</div>
                    </div>
                    
                    <div style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">⚖️ SALDO LÍQUIDO</div>
                        <div style="font-size: 14px; color: #666; margin-bottom: 3px;">Receitas - Despesas</div>
                        <div style="font-size: 16px; font-weight: bold; color: ${saldoLiquido >= 0 ? '#27ae60' : '#e74c3c'};">R$ ${saldoLiquido.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    </div>
                </div>
            </div>
        `;
        
        content.innerHTML = html;
        
    } catch (error) {
        console.error('Erro ao carregar resumo por parceiros:', error);
        document.getElementById('resumo-parceiros-content').innerHTML = '<div class="error">Erro ao carregar dados</div>';
    }
}

// Carregar análise por Categorias
async function carregarAnaliseCategorias() {
    try {
        const ano = document.getElementById('filter-ano-categorias')?.value || new Date().getFullYear();
        const mes = document.getElementById('filter-mes-categorias')?.value || '';
        
        const content = document.getElementById('analise-categorias-content');
        content.innerHTML = '<div class="loading">Carregando dados...</div>';
        
        // Buscar receitas e despesas
        const [receitas, despesas] = await Promise.all([
            fetch('/api/lancamentos?tipo=RECEITA').then(r => r.json()),
            fetch('/api/lancamentos?tipo=DESPESA').then(r => r.json())
        ]);
        
        console.log('📊 Receitas totais:', receitas.length);
        console.log('📊 Despesas totais:', despesas.length);
        
        // Filtrar por período
        const filtrarPorPeriodo = (lancamentos) => {
            return lancamentos.filter(l => {
                // Aceitar apenas lançamentos PAGOS
                const status = (l.status || '').toUpperCase();
                if (status !== 'PAGO') return false;
                
                // Usar data de pagamento se existir, senão data de vencimento
                const dataRef = l.data_pagamento || l.data_vencimento;
                if (!dataRef) return false;
                
                const data = new Date(dataRef);
                if (isNaN(data.getTime())) return false;
                
                if (ano && data.getFullYear() !== parseInt(ano)) return false;
                if (mes && (data.getMonth() + 1) !== parseInt(mes)) return false;
                
                return true;
            });
        };
        
        const receitasFiltradas = filtrarPorPeriodo(receitas);
        const despesasFiltradas = filtrarPorPeriodo(despesas);
        
        console.log('📊 Receitas filtradas (PAGAS):', receitasFiltradas.length);
        console.log('📊 Despesas filtradas (PAGAS):', despesasFiltradas.length);
        
        // Agrupar por categoria
        const resumoPorCategoria = {};
        
        receitasFiltradas.forEach(l => {
            const categoria = l.categoria || 'Não informado';
            if (!resumoPorCategoria[categoria]) {
                resumoPorCategoria[categoria] = { receitas: 0, despesas: 0, saldo: 0, subcategorias: {} };
            }
            resumoPorCategoria[categoria].receitas += parseFloat(l.valor || 0);
            
            // Subcategoria
            const subcategoria = l.subcategoria || 'Geral';
            if (!resumoPorCategoria[categoria].subcategorias[subcategoria]) {
                resumoPorCategoria[categoria].subcategorias[subcategoria] = { receitas: 0, despesas: 0 };
            }
            resumoPorCategoria[categoria].subcategorias[subcategoria].receitas += parseFloat(l.valor || 0);
        });
        
        despesasFiltradas.forEach(l => {
            const categoria = l.categoria || 'Não informado';
            if (!resumoPorCategoria[categoria]) {
                resumoPorCategoria[categoria] = { receitas: 0, despesas: 0, saldo: 0, subcategorias: {} };
            }
            resumoPorCategoria[categoria].despesas += parseFloat(l.valor || 0);
            
            // Subcategoria
            const subcategoria = l.subcategoria || 'Geral';
            if (!resumoPorCategoria[categoria].subcategorias[subcategoria]) {
                resumoPorCategoria[categoria].subcategorias[subcategoria] = { receitas: 0, despesas: 0 };
            }
            resumoPorCategoria[categoria].subcategorias[subcategoria].despesas += parseFloat(l.valor || 0);
        });
        
        // Calcular saldo
        Object.keys(resumoPorCategoria).forEach(categoria => {
            resumoPorCategoria[categoria].saldo = resumoPorCategoria[categoria].receitas - resumoPorCategoria[categoria].despesas;
        });
        
        // Ordenar por maior volume
        const categorias = Object.keys(resumoPorCategoria).sort((a, b) => {
            const volumeA = resumoPorCategoria[a].receitas + resumoPorCategoria[a].despesas;
            const volumeB = resumoPorCategoria[b].receitas + resumoPorCategoria[b].despesas;
            return volumeB - volumeA;
        });
        
        // Gerar HTML
        let html = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Categoria</th>
                        <th>Subcategoria</th>
                        <th>Receitas</th>
                        <th>Despesas</th>
                        <th>Saldo</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        let totais = { receitas: 0, despesas: 0, saldo: 0 };
        
        categorias.forEach(categoria => {
            const dados = resumoPorCategoria[categoria];
            totais.receitas += dados.receitas;
            totais.despesas += dados.despesas;
            totais.saldo += dados.saldo;
            
            // Linha da categoria
            html += `
                <tr style="background: #e8e8e8; font-weight: bold;">
                    <td colspan="2">${categoria}</td>
                    <td style="color: #27ae60;">R$ ${dados.receitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td style="color: #e74c3c;">R$ ${dados.despesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td style="color: ${dados.saldo >= 0 ? '#27ae60' : '#e74c3c'};">R$ ${dados.saldo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                </tr>
            `;
            
            // Linhas das subcategorias
            Object.keys(dados.subcategorias).forEach(subcategoria => {
                const subDados = dados.subcategorias[subcategoria];
                const subSaldo = subDados.receitas - subDados.despesas;
                
                html += `
                    <tr>
                        <td></td>
                        <td style="padding-left: 20px;">↳ ${subcategoria}</td>
                        <td style="color: #27ae60;">R$ ${subDados.receitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td style="color: #e74c3c;">R$ ${subDados.despesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td style="color: ${subSaldo >= 0 ? '#27ae60' : '#e74c3c'};">R$ ${subSaldo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    </tr>
                `;
            });
        });
        
        html += `
                </tbody>
                <tfoot>
                    <tr style="font-weight: bold; background: #f8f9fa;">
                        <td colspan="2">TOTAL</td>
                        <td style="color: #27ae60;">R$ ${totais.receitas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td style="color: #e74c3c;">R$ ${totais.despesas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td style="color: ${totais.saldo >= 0 ? '#27ae60' : '#e74c3c'};">R$ ${totais.saldo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    </tr>
                </tfoot>
            </table>
        `;
        
        // Calcular métricas adicionais
        let maiorReceitaCategoria = null;
        let maiorReceitaSubcategoria = null;
        let maiorReceitaValor = 0;
        let maiorDespesaCategoria = null;
        let maiorDespesaSubcategoria = null;
        let maiorDespesaValor = 0;
        
        let categoriaEquilibrada = null;
        let menorDiferenca = Infinity;
        let categoriaMaiorDeficit = null;
        let maiorDeficit = 0;
        
        categorias.forEach(categoria => {
            const dados = resumoPorCategoria[categoria];
            
            // Verificar categoria mais equilibrada (menor diferença entre receitas e despesas)
            const diferenca = Math.abs(dados.saldo);
            if (diferenca < menorDiferenca && (dados.receitas > 0 || dados.despesas > 0)) {
                menorDiferenca = diferenca;
                categoriaEquilibrada = categoria;
            }
            
            // Verificar categoria com maior déficit
            if (dados.saldo < 0 && Math.abs(dados.saldo) > maiorDeficit) {
                maiorDeficit = Math.abs(dados.saldo);
                categoriaMaiorDeficit = categoria;
            }
            
            // Verificar subcategorias para maior receita e despesa
            Object.keys(dados.subcategorias).forEach(subcategoria => {
                const subDados = dados.subcategorias[subcategoria];
                
                if (subDados.receitas > maiorReceitaValor) {
                    maiorReceitaValor = subDados.receitas;
                    maiorReceitaCategoria = categoria;
                    maiorReceitaSubcategoria = subcategoria;
                }
                
                if (subDados.despesas > maiorDespesaValor) {
                    maiorDespesaValor = subDados.despesas;
                    maiorDespesaCategoria = categoria;
                    maiorDespesaSubcategoria = subcategoria;
                }
            });
        });
        
        // Calcular distribuição percentual
        const distribuicaoReceitas = {};
        const distribuicaoDespesas = {};
        
        categorias.forEach(categoria => {
            const dados = resumoPorCategoria[categoria];
            if (totais.receitas > 0) {
                distribuicaoReceitas[categoria] = (dados.receitas / totais.receitas * 100).toFixed(1);
            }
            if (totais.despesas > 0) {
                distribuicaoDespesas[categoria] = (dados.despesas / totais.despesas * 100).toFixed(1);
            }
        });
        
        // Adicionar resumo executivo
        html += `
            <div style="margin-top: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h3 style="margin: 0 0 20px 0; color: #333; font-size: 16px; border-bottom: 2px solid #333; padding-bottom: 10px;">📊 RESUMO EXECUTIVO</h3>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                    <div style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">💰 MAIOR RECEITA</div>
                        <div style="font-size: 14px; font-weight: bold; color: #333; margin-bottom: 3px;">${maiorReceitaCategoria || 'N/A'}</div>
                        <div style="font-size: 12px; color: #666; margin-bottom: 3px;">↳ ${maiorReceitaSubcategoria || ''}</div>
                        <div style="font-size: 16px; font-weight: bold; color: #27ae60;">R$ ${maiorReceitaValor.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    </div>
                    
                    <div style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">💸 MAIOR DESPESA</div>
                        <div style="font-size: 14px; font-weight: bold; color: #333; margin-bottom: 3px;">${maiorDespesaCategoria || 'N/A'}</div>
                        <div style="font-size: 12px; color: #666; margin-bottom: 3px;">↳ ${maiorDespesaSubcategoria || ''}</div>
                        <div style="font-size: 16px; font-weight: bold; color: #e74c3c;">R$ ${maiorDespesaValor.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    </div>
                    
                    <div style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">⚖️ CATEGORIA EQUILIBRADA</div>
                        <div style="font-size: 14px; font-weight: bold; color: #333; margin-bottom: 3px;">${categoriaEquilibrada || 'N/A'}</div>
                        <div style="font-size: 12px; color: #666; margin-bottom: 3px;">Menor variação</div>
                        <div style="font-size: 16px; font-weight: bold; color: #2196F3;">R$ ${menorDiferenca !== Infinity ? menorDiferenca.toLocaleString('pt-BR', {minimumFractionDigits: 2}) : '0,00'}</div>
                    </div>
                    
                    <div style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">📉 MAIOR DÉFICIT</div>
                        <div style="font-size: 14px; font-weight: bold; color: #333; margin-bottom: 3px;">${categoriaMaiorDeficit || 'N/A'}</div>
                        <div style="font-size: 12px; color: #666; margin-bottom: 3px;">Despesas > Receitas</div>
                        <div style="font-size: 16px; font-weight: bold; color: #e74c3c;">R$ ${maiorDeficit.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    </div>
                    
                    <div style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 8px;">📊 DISTRIBUIÇÃO (Receitas)</div>
                        ${Object.keys(distribuicaoReceitas).slice(0, 3).map(cat => 
                            `<div style="font-size: 11px; margin-bottom: 4px;">
                                <span style="font-weight: 500;">${cat}:</span> 
                                <span style="color: #27ae60; font-weight: bold;">${distribuicaoReceitas[cat]}%</span>
                            </div>`
                        ).join('')}
                    </div>
                    
                    <div style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 8px;">📊 DISTRIBUIÇÃO (Despesas)</div>
                        ${Object.keys(distribuicaoDespesas).slice(0, 3).map(cat => 
                            `<div style="font-size: 11px; margin-bottom: 4px;">
                                <span style="font-weight: 500;">${cat}:</span> 
                                <span style="color: #e74c3c; font-weight: bold;">${distribuicaoDespesas[cat]}%</span>
                            </div>`
                        ).join('')}
                    </div>
                </div>
            </div>
        `;
        
        content.innerHTML = html;
        
    } catch (error) {
        console.error('Erro ao carregar análise por categorias:', error);
        document.getElementById('analise-categorias-content').innerHTML = '<div class="error">Erro ao carregar dados</div>';
    }
}

// Inicializar ao carregar a seção
window.addEventListener('DOMContentLoaded', () => {
    // Carregar dados iniciais ao abrir a aba de análise detalhada
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.target.id === 'analise-detalhada-section' && !mutation.target.classList.contains('hidden')) {
                carregarResumoParceiros();
            }
        });
    });
    
    const section = document.getElementById('analise-detalhada-section');
    if (section) {
        observer.observe(section, { attributes: true, attributeFilter: ['class'] });
    }
});


// ===================================
// FUNÇÕES DE EXPORTAÇÃO PDF
// ===================================

function exportarResumoParceirosPDF() {
    const content = document.getElementById('resumo-parceiros-content');
    if (!content || content.innerHTML === '<div class="loading">Carregando dados...</div>') {
        alert('Por favor, gere o relatório antes de exportar!');
        return;
    }
    
    const ano = document.getElementById('filter-ano-parceiros')?.value || new Date().getFullYear();
    const mes = document.getElementById('filter-mes-parceiros')?.value || '';
    const mesNome = mes ? ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][parseInt(mes)] : 'Ano Inteiro';
    
    const dataAtual = new Date().toLocaleDateString('pt-BR');
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Análise por Cliente/Fornecedor - ${ano}${mes ? '/' + mes : ''}</title>
            <style>
                @page { size: landscape; margin: 15mm; }
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    padding: 20px; 
                    background: white;
                }
                .header {
                    text-align: center;
                    margin-bottom: 15px;
                    border-bottom: 2px solid #2196F3;
                    padding-bottom: 10px;
                }
                .header h1 {
                    color: #2196F3;
                    font-size: 13px;
                    margin-bottom: 4px;
                }
                .header .subtitle {
                    color: #666;
                    font-size: 9px;
                }
                .info-row {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 8px;
                    padding: 4px;
                    background: #f8f9fa;
                    border-radius: 3px;
                }
                .info-item {
                    font-size: 8px;
                }
                .info-label {
                    color: #666;
                    font-weight: 500;
                }
                .info-value {
                    color: #333;
                    font-weight: bold;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 8px;
                }
                th {
                    background: #2196F3;
                    color: white;
                    padding: 4px 6px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 8px;
                }
                td {
                    padding: 3px 6px;
                    border-bottom: 1px solid #e0e0e0;
                    font-size: 8px;
                }
                tbody tr:hover {
                    background: #f5f5f5;
                }
                tfoot tr {
                    background: #f8f9fa;
                    font-weight: bold;
                }
                .valor-positivo { color: #27ae60; font-weight: 600; }
                .valor-negativo { color: #e74c3c; font-weight: 600; }
                .resumo-cards {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 6px;
                    margin: 8px 0;
                    page-break-inside: avoid;
                }
                .card {
                    border: 1px solid #e0e0e0;
                    border-radius: 3px;
                    padding: 6px;
                }
                .card-title {
                    font-size: 7px;
                    color: #666;
                    margin-bottom: 2px;
                }
                .card-value {
                    font-size: 9px;
                    font-weight: bold;
                }
                .card-subtitle {
                    font-size: 7px;
                    color: #666;
                    margin: 1px 0;
                }
                @media print {
                    body { padding: 10px; }
                    .header { page-break-after: avoid; }
                    table { page-break-inside: avoid !important; }
                    thead { display: table-header-group; }
                    tfoot { display: table-footer-group; }
                    tr { page-break-inside: avoid; }
                    .resumo-cards { page-break-inside: avoid; }
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📇 Análise Detalhada por Cliente/Fornecedor</h1>
                <div class="subtitle">Período: ${mesNome} de ${ano}</div>
            </div>
            
            <div class="info-row">
                <div class="info-item">
                    <span class="info-label">Data de Emissão:</span>
                    <span class="info-value">${dataAtual}</span>
                </div>
            </div>
            
            ${content.innerHTML}
            
            <div style="margin-top: 15px; padding-top: 8px; border-top: 1px solid #e0e0e0; text-align: center; color: #999; font-size: 7px;">
                Gerado automaticamente pelo Sistema Financeiro - ${dataAtual}
            </div>
        </body>
        </html>
    `);
    
    printWindow.document.close();
    
    setTimeout(() => {
        printWindow.print();
    }, 500);
}

function exportarAnaliseCategoriasPDF() {
    const content = document.getElementById('analise-categorias-content');
    if (!content || content.innerHTML === '<div class="loading">Carregando dados...</div>') {
        alert('Por favor, gere a análise antes de exportar!');
        return;
    }
    
    const ano = document.getElementById('filter-ano-categorias')?.value || new Date().getFullYear();
    const mes = document.getElementById('filter-mes-categorias')?.value || '';
    const mesNome = mes ? ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][parseInt(mes)] : 'Ano Inteiro';
    
    const dataAtual = new Date().toLocaleDateString('pt-BR');
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Análise por Categoria - ${ano}${mes ? '/' + mes : ''}</title>
            <style>
                @page { size: landscape; margin: 15mm; }
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    padding: 20px; 
                    background: white;
                }
                .header {
                    text-align: center;
                    margin-bottom: 15px;
                    border-bottom: 2px solid #2196F3;
                    padding-bottom: 10px;
                }
                .header h1 {
                    color: #2196F3;
                    font-size: 13px;
                    margin-bottom: 4px;
                }
                .header .subtitle {
                    color: #666;
                    font-size: 9px;
                }
                .info-row {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 8px;
                    padding: 4px;
                    background: #f8f9fa;
                    border-radius: 3px;
                }
                .info-item {
                    font-size: 8px;
                }
                .info-label {
                    color: #666;
                    font-weight: 500;
                }
                .info-value {
                    color: #333;
                    font-weight: bold;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 8px;
                }
                th {
                    background: #2196F3;
                    color: white;
                    padding: 4px 6px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 8px;
                }
                td {
                    padding: 3px 6px;
                    border-bottom: 1px solid #e0e0e0;
                    font-size: 8px;
                }
                tbody tr:hover {
                    background: #f5f5f5;
                }
                tbody tr[style*="background: #e8e8e8"] {
                    background: #e8e8e8 !important;
                    font-weight: bold;
                }
                tfoot tr {
                    background: #f8f9fa;
                    font-weight: bold;
                }
                .valor-positivo { color: #27ae60; font-weight: 600; }
                .valor-negativo { color: #e74c3c; font-weight: 600; }
                .resumo-cards {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 6px;
                    margin: 8px 0;
                    page-break-inside: avoid;
                }
                .card {
                    border: 1px solid #e0e0e0;
                    border-radius: 3px;
                    padding: 6px;
                }
                .card-title {
                    font-size: 7px;
                    color: #666;
                    margin-bottom: 2px;
                }
                .card-value {
                    font-size: 9px;
                    font-weight: bold;
                }
                .card-subtitle {
                    font-size: 7px;
                    color: #666;
                    margin: 1px 0;
                }
                @media print {
                    body { padding: 10px; }
                    .header { page-break-after: avoid; }
                    table { page-break-inside: avoid !important; }
                    thead { display: table-header-group; }
                    tfoot { display: table-footer-group; }
                    tr { page-break-inside: avoid; }
                    .resumo-cards { page-break-inside: avoid; }
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📁 Análise Detalhada por Categoria</h1>
                <div class="subtitle">Período: ${mesNome} de ${ano}</div>
            </div>
            
            <div class="info-row">
                <div class="info-item">
                    <span class="info-label">Data de Emissão:</span>
                    <span class="info-value">${dataAtual}</span>
                </div>
            </div>
            
            ${content.innerHTML}
            
            <div style="margin-top: 15px; padding-top: 8px; border-top: 1px solid #e0e0e0; text-align: center; color: #999; font-size: 7px;">
                Gerado automaticamente pelo Sistema Financeiro - ${dataAtual}
            </div>
        </body>
        </html>
    `);
    
    printWindow.document.close();
    
    setTimeout(() => {
        printWindow.print();
    }, 500);
}
