// Modals - Sistema Financeiro
// ============================
console.log('%c ✓ MODALS.JS v20260119_SEM_NUM_DOCUMENTO CARREGADO ', 'background: #00ff00; color: black; font-size: 16px; font-weight: bold');

// === MODAL RECEITA ===
async function openModalReceita() {
    // Sempre recarregar categorias para pegar subcategorias atualizadas
    console.log('Recarregando categorias...');
    await loadCategorias();
    
    if (!window.clientes || window.clientes.length === 0) {
        console.log('Carregando clientes...');
        await loadClientes();
    }
    
    // Aguardar um momento para garantir que os dados foram carregados
    await new Promise(resolve => setTimeout(resolve, 200));
    
    console.log('=== DEBUG openModalReceita ===');
    console.log('window.clientes:', window.clientes);
    console.log('window.clientes.length:', window.clientes ? window.clientes.length : 0);
    console.log('window.categorias:', window.categorias);
    console.log('window.categorias.length:', window.categorias ? window.categorias.length : 0);
    
    const categoriasReceita = window.categorias ? window.categorias.filter(c => c.tipo && c.tipo.toUpperCase() === 'RECEITA') : [];
    console.log('Categorias de RECEITA filtradas:', categoriasReceita);
    console.log('Quantidade de categorias RECEITA:', categoriasReceita.length);
    
    // Gerar opções de clientes DEPOIS de carregar
    const opcoesClientes = window.clientes && window.clientes.length > 0
        ? window.clientes.map(c => `<option value="${c.razao_social || c.nome}">${c.razao_social || c.nome}</option>`).join('')
        : '<option value="">Nenhum cliente cadastrado</option>';
    
    console.log('HTML de opcoesClientes gerado:', opcoesClientes.substring(0, 100) + '...');
    
    // Gerar opções de categorias de receita DEPOIS de carregar
    const opcoesCategorias = categoriasReceita.length > 0
        ? categoriasReceita.map(cat => `<option value="${cat.nome}">${cat.nome}</option>`).join('')
        : '<option value="">Nenhuma categoria cadastrada</option>';
    
    console.log('HTML de opcoesCategorias gerado:', opcoesCategorias.substring(0, 100) + '...');
    console.log('=== FIM DEBUG ===');
    
    const modal = createModal('Nova Receita', `
        <form id="form-receita" onsubmit="salvarReceita(event)">
            <input type="hidden" id="receita-id" value="">
            <div class="form-group">
                <label>*Cliente:</label>
                <select id="receita-cliente" required>
                    <option value="">Selecione...</option>
                    ${opcoesClientes}
                </select>
            </div>
            
            <div class="form-group">
                <label>*Categoria:</label>
                <select id="receita-categoria" required onchange="atualizarSubcategoriasReceita()">
                    <option value="">Selecione...</option>
                    ${opcoesCategorias}
                </select>
            </div>
            
            <div class="form-group">
                <label>Subcategoria:</label>
                <select id="receita-subcategoria">
                    <option value="">Selecione uma categoria primeiro...</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Nº Documento:</label>
                <input type="text" id="receita-documento">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Data de Emissão:</label>
                    <input type="date" id="receita-emissao" value="${new Date().toISOString().split('T')[0]}">
                </div>
                
                <div class="form-group">
                    <label>Competência:</label>
                    <input type="month" id="receita-competencia" value="${new Date().toISOString().slice(0,7)}">
                </div>
            </div>
            
            <div class="form-group">
                <label>*Vencimento:</label>
                <input type="date" id="receita-vencimento" required>
            </div>
            
            <div class="form-group">
                <label>Descrição:</label>
                <input type="text" id="receita-descricao" placeholder="Opcional">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>*Valor:</label>
                    <input type="number" id="receita-valor" step="0.01" min="0" required>
                </div>
                
                <div class="form-group">
                    <label>Parcelas:</label>
                    <input type="number" id="receita-parcelas" min="1" value="1" placeholder="1">
                </div>
            </div>
            
            <div class="form-group">
                <label>Observações:</label>
                <textarea id="receita-observacoes" rows="3"></textarea>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Salvar</button>
            </div>
        </form>
    `);
    
    // NOTA: NÃO limpar o ID aqui, pois a função editarReceita precisa definir o ID após abrir o modal
    // O campo hidden receita-id começa vazio por padrão no HTML acima
}

function atualizarSubcategoriasReceita() {
    const categoriaSel = document.getElementById('receita-categoria').value;
    const subcatSelect = document.getElementById('receita-subcategoria');
    
    console.log('=== atualizarSubcategoriasReceita ===');
    console.log('Categoria selecionada:', categoriaSel);
    console.log('window.categorias disponíveis:', window.categorias);
    
    if (!subcatSelect) {
        console.error('❌ Elemento receita-subcategoria não encontrado!');
        return;
    }
    
    subcatSelect.innerHTML = '<option value="">Selecione...</option>';
    
    if (!categoriaSel) {
        console.log('⚠️ Nenhuma categoria selecionada');
        return;
    }
    
    const categoria = window.categorias.find(c => c.nome === categoriaSel);
    console.log('Categoria encontrada:', categoria);
    console.log('Tipo de subcategorias:', typeof categoria?.subcategorias);
    console.log('É array?', Array.isArray(categoria?.subcategorias));
    console.log('Valor de subcategorias:', categoria?.subcategorias);
    
    if (categoria && categoria.subcategorias) {
        // Se subcategorias for string, converter para array
        let subs = categoria.subcategorias;
        if (typeof subs === 'string') {
            console.log('Subcategorias é string, convertendo...');
            subs = subs.split(',').map(s => s.trim());
        }
        
        console.log('Subcategorias processadas:', subs);
        
        if (Array.isArray(subs) && subs.length > 0) {
            subs.forEach(sub => {
                if (sub) {
                    console.log('Adicionando subcategoria:', sub);
                    subcatSelect.innerHTML += `<option value="${sub}">${sub}</option>`;
                }
            });
            console.log('✅ Subcategorias adicionadas com sucesso!');
            console.log('HTML final do select:', subcatSelect.innerHTML);
        } else {
            console.log('⚠️ Array vazio ou inválido');
        }
    } else {
        console.log('⚠️ Nenhuma subcategoria encontrada para esta categoria');
    }
    console.log('=== FIM atualizarSubcategoriasReceita ===');
}

async function salvarReceita(event) {
    event.preventDefault();
    
    console.log('\n💾 ========== SALVAR RECEITA ==========');
    
    // Validar empresa_id
    if (!window.currentEmpresaId) {
        showToast('Erro: Empresa não identificada. Por favor, recarregue a página.', 'error');
        console.error('❌ window.currentEmpresaId não está definido!');
        return;
    }
    
    const id = document.getElementById('receita-id').value;
    console.log('🔍 ID do campo receita-id:', id, 'tipo:', typeof id, 'length:', id?.length);
    
    const isEdicao = id && id.trim() !== '';
    console.log('🎯 Modo detectado:', isEdicao ? '✏️ EDIÇÃO' : '🆕 CRIAÇÃO');
    const parcelas = parseInt(document.getElementById('receita-parcelas').value) || 1;
    const campoValor = document.getElementById('receita-valor');
    
    const data = {
        tipo: 'RECEITA',
        pessoa: document.getElementById('receita-cliente').value,
        categoria: document.getElementById('receita-categoria').value,
        subcategoria: document.getElementById('receita-subcategoria').value,
        data_vencimento: document.getElementById('receita-vencimento').value,
        descricao: document.getElementById('receita-descricao').value || document.getElementById('receita-documento').value || '',
        valor: typeof obterValorReal === 'function' ? obterValorReal(campoValor) : parseFloat(campoValor.value),
        observacoes: document.getElementById('receita-observacoes').value,
        conta_bancaria: '',
        status: 'pendente',
        parcelas: isEdicao ? 1 : parcelas,  // Não parcelar em edição
        empresa_id: window.currentEmpresaId
    };
    
    console.log(isEdicao ? '=== Atualizando Receita ===' : '=== Criando Nova Receita ===');
    console.log('📋 ID:', id);
    console.log('📦 Dados a enviar:', data);
    
    try {
        const url = isEdicao ? `/api/lancamentos/${id}` : '/api/lancamentos';
        const method = isEdicao ? 'PUT' : 'POST';
        
        console.log('🌐 URL:', url);
        console.log('📤 Method:', method);
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        console.log('Resposta do servidor:', result);
        
        if (result.success) {
            const mensagem = isEdicao ? '✓ Receita atualizada com sucesso!' : '✓ Receita adicionada com sucesso!';
            showToast(mensagem, 'success');
            closeModal();
            
            console.log('🔄 Recarregando dados após salvar...');
            console.log('   loadDashboard existe?', typeof loadDashboard);
            console.log('   loadContasReceber existe?', typeof loadContasReceber);
            
            if (typeof loadDashboard === 'function') loadDashboard();
            if (typeof loadContasReceber === 'function') {
                console.log('   ✅ Chamando loadContasReceber...');
                loadContasReceber();
            } else {
                console.error('   ❌ loadContasReceber não é uma função!');
            }
            if (typeof atualizarBadgeInadimplencia === 'function') {
                atualizarBadgeInadimplencia();
            }
        } else {
            console.error('Erro do servidor:', result.error);
            showToast('Erro: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Erro ao salvar receita:', error);
        showToast('Erro ao salvar receita', 'error');
    }
}

// Função para editar receita
async function editarReceita(id) {
    console.log('\n🔧 ========== EDITAR RECEITA ==========');
    console.log('📥 ID recebido:', id, 'tipo:', typeof id);
    
    try {
        console.log('📡 Buscando lançamento...');
        const response = await fetch(`${API_URL}/lancamentos/${id}`);
        const lancamento = await response.json();
        console.log('✅ Lançamento recebido:', lancamento);
        
        if (lancamento) {
            console.log('🎨 Abrindo modal para edição...');
            // Preencher o modal com os dados
            await openModalReceita();
            
            console.log('📝 Preenchendo campo receita-id com:', lancamento.id);
            document.getElementById('receita-id').value = lancamento.id;
            console.log('✅ Campo receita-id preenchido. Valor atual:', document.getElementById('receita-id').value);
            document.getElementById('receita-cliente').value = lancamento.pessoa || '';
            document.getElementById('receita-categoria').value = lancamento.categoria || '';
            
            // Aguardar subcategorias carregarem
            await atualizarSubcategoriasReceita();
            document.getElementById('receita-subcategoria').value = lancamento.subcategoria || '';
            
            document.getElementById('receita-vencimento').value = lancamento.data_vencimento ? lancamento.data_vencimento.split('T')[0] : '';
            document.getElementById('receita-descricao').value = lancamento.descricao || '';
            document.getElementById('receita-valor').value = lancamento.valor || '';
            document.getElementById('receita-observacoes').value = lancamento.observacoes || '';
            
            console.log('🎯 Modal preenchido completamente');
            console.log('🔍 Verificação final do ID:', document.getElementById('receita-id').value);
            console.log('========== FIM EDITAR RECEITA ==========\n');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar receita para edição:', error);
        showToast('Erro ao carregar receita', 'error');
    }
}

// === MODAL DESPESA ===
async function openModalDespesa() {
    // Sempre recarregar categorias para pegar subcategorias atualizadas
    console.log('Recarregando categorias...');
    await loadCategorias();
    
    if (!window.fornecedores || window.fornecedores.length === 0) {
        console.log('Carregando fornecedores...');
        await loadFornecedores();
    }
    
    // Aguardar um momento para garantir que os dados foram carregados
    await new Promise(resolve => setTimeout(resolve, 200));
    
    console.log('=== DEBUG openModalDespesa ===');
    console.log('window.fornecedores:', window.fornecedores);
    console.log('window.fornecedores.length:', window.fornecedores ? window.fornecedores.length : 0);
    console.log('window.categorias:', window.categorias);
    console.log('window.categorias.length:', window.categorias ? window.categorias.length : 0);
    
    const categoriasDespesa = window.categorias ? window.categorias.filter(c => c.tipo && c.tipo.toUpperCase() === 'DESPESA') : [];
    console.log('Categorias de DESPESA filtradas:', categoriasDespesa);
    console.log('Quantidade de categorias DESPESA:', categoriasDespesa.length);
    
    // Gerar opções de fornecedores DEPOIS de carregar
    const opcoesFornecedores = window.fornecedores && window.fornecedores.length > 0
        ? window.fornecedores.map(f => `<option value="${f.razao_social || f.nome}">${f.razao_social || f.nome}</option>`).join('')
        : '<option value="">Nenhum fornecedor cadastrado</option>';
    
    console.log('HTML de opcoesFornecedores gerado:', opcoesFornecedores.substring(0, 100) + '...');
    
    // Gerar opções de categorias de despesa DEPOIS de carregar
    const opcoesCategorias = categoriasDespesa.length > 0
        ? categoriasDespesa.map(cat => `<option value="${cat.nome}">${cat.nome}</option>`).join('')
        : '<option value="">Nenhuma categoria cadastrada</option>';
    
    console.log('HTML de opcoesCategorias gerado:', opcoesCategorias.substring(0, 100) + '...');
    console.log('=== FIM DEBUG ===');
    
    const modal = createModal('Nova Despesa', `
        <form id="form-despesa" onsubmit="salvarDespesa(event)">
            <input type="hidden" id="despesa-id" value="">
            <div class="form-group">
                <label>*Fornecedor:</label>
                <select id="despesa-fornecedor" required>
                    <option value="">Selecione...</option>
                    ${opcoesFornecedores}
                </select>
            </div>
            
            <div class="form-group">
                <label>*Categoria:</label>
                <select id="despesa-categoria" required onchange="atualizarSubcategoriasDespesa()">
                    <option value="">Selecione...</option>
                    ${opcoesCategorias}
                </select>
            </div>
            
            <div class="form-group">
                <label>Subcategoria:</label>
                <select id="despesa-subcategoria">
                    <option value="">Selecione uma categoria primeiro...</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Nº Documento:</label>
                <input type="text" id="despesa-documento">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Data de Emissão:</label>
                    <input type="date" id="despesa-emissao" value="${new Date().toISOString().split('T')[0]}">
                </div>
                
                <div class="form-group">
                    <label>Competência:</label>
                    <input type="month" id="despesa-competencia" value="${new Date().toISOString().slice(0,7)}">
                </div>
            </div>
            
            <div class="form-group">
                <label>*Vencimento:</label>
                <input type="date" id="despesa-vencimento" required>
            </div>
            
            <div class="form-group">
                <label>Descrição:</label>
                <input type="text" id="despesa-descricao" placeholder="Opcional">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>*Valor:</label>
                    <input type="number" id="despesa-valor" step="0.01" min="0" required>
                </div>
                
                <div class="form-group">
                    <label>Parcelas:</label>
                    <input type="number" id="despesa-parcelas" min="1" value="1" placeholder="1">
                </div>
            </div>
            
            <div class="form-group">
                <label>Observações:</label>
                <textarea id="despesa-observacoes" rows="3"></textarea>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Salvar</button>
            </div>
        </form>
    `);
    
    // NOTA: NÃO limpar o ID aqui, pois a função editarDespesa precisa definir o ID após abrir o modal
    // O campo hidden despesa-id começa vazio por padrão no HTML acima
}

function atualizarSubcategoriasDespesa() {
    const categoriaSel = document.getElementById('despesa-categoria').value;
    const subcatSelect = document.getElementById('despesa-subcategoria');
    
    console.log('=== atualizarSubcategoriasDespesa ===');
    console.log('Categoria selecionada:', categoriaSel);
    console.log('window.categorias disponíveis:', window.categorias);
    
    subcatSelect.innerHTML = '<option value="">Selecione...</option>';
    
    const categoria = window.categorias.find(c => c.nome === categoriaSel);
    console.log('Categoria encontrada:', categoria);
    console.log('Tipo de subcategorias:', typeof categoria?.subcategorias);
    console.log('É array?', Array.isArray(categoria?.subcategorias));
    console.log('Valor de subcategorias:', categoria?.subcategorias);
    
    if (categoria && categoria.subcategorias) {
        // Se subcategorias for string, converter para array
        let subs = categoria.subcategorias;
        if (typeof subs === 'string') {
            console.log('Subcategorias é string, convertendo...');
            subs = subs.split(',').map(s => s.trim());
        }
        
        console.log('Subcategorias processadas:', subs);
        
        if (Array.isArray(subs) && subs.length > 0) {
            subs.forEach(sub => {
                if (sub) {
                    subcatSelect.innerHTML += `<option value="${sub}">${sub}</option>`;
                }
            });
            console.log('Subcategorias adicionadas com sucesso!');
        } else {
            console.log('Array vazio ou inválido');
        }
    } else {
        console.log('Nenhuma subcategoria encontrada');
    }
}

async function salvarDespesa(event) {
    event.preventDefault();
    
    console.log('\n💾 ========== SALVAR DESPESA ==========');
    
    // Validar empresa_id
    if (!window.currentEmpresaId) {
        showToast('Erro: Empresa não identificada. Por favor, recarregue a página.', 'error');
        console.error('❌ window.currentEmpresaId não está definido!');
        return;
    }
    
    const id = document.getElementById('despesa-id').value;
    console.log('🔍 ID do campo despesa-id:', id, 'tipo:', typeof id, 'length:', id?.length);
    
    const isEdicao = id && id.trim() !== '';
    console.log('🎯 Modo detectado:', isEdicao ? '✏️ EDIÇÃO' : '🆕 CRIAÇÃO');
    const parcelas = parseInt(document.getElementById('despesa-parcelas').value) || 1;
    const campoValor = document.getElementById('despesa-valor');
    
    const data = {
        tipo: 'DESPESA',
        pessoa: document.getElementById('despesa-fornecedor').value,
        categoria: document.getElementById('despesa-categoria').value,
        subcategoria: document.getElementById('despesa-subcategoria').value,
        data_vencimento: document.getElementById('despesa-vencimento').value,
        descricao: document.getElementById('despesa-descricao').value || document.getElementById('despesa-documento').value || '',
        valor: typeof obterValorReal === 'function' ? obterValorReal(campoValor) : parseFloat(campoValor.value),
        observacoes: document.getElementById('despesa-observacoes').value,
        conta_bancaria: '',
        status: 'pendente',
        parcelas: isEdicao ? 1 : parcelas,  // Não parcelar em edição
        empresa_id: window.currentEmpresaId
    };
    
    console.log(isEdicao ? '=== Atualizando Despesa ===' : '=== Criando Nova Despesa ===');
    console.log('📋 ID:', id);
    console.log('📦 Dados a enviar:', data);
    
    try {
        const url = isEdicao ? `/api/lancamentos/${id}` : '/api/lancamentos';
        const method = isEdicao ? 'PUT' : 'POST';
        
        console.log('🌐 URL:', url);
        console.log('📤 Method:', method);
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        console.log('Resposta do servidor:', result);
        
        if (result.success) {
            const mensagem = isEdicao ? '✓ Despesa atualizada com sucesso!' : '✓ Despesa adicionada com sucesso!';
            showToast(mensagem, 'success');
            closeModal();
            if (typeof loadDashboard === 'function') loadDashboard();
            if (typeof loadContasPagar === 'function') loadContasPagar();
            if (typeof atualizarBadgeInadimplencia === 'function') {
                atualizarBadgeInadimplencia();
            }
        } else {
            console.error('Erro do servidor:', result.error);
            showToast('Erro: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Erro ao salvar despesa:', error);
        showToast('Erro ao salvar despesa', 'error');
    }
}

// Função para editar despesa
async function editarDespesa(id) {
    console.log('\n🔧 ========== EDITAR DESPESA ==========');
    console.log('📥 ID recebido:', id, 'tipo:', typeof id);
    
    try {
        console.log('📡 Buscando lançamento...');
        const response = await fetch(`${API_URL}/lancamentos/${id}`);
        const lancamento = await response.json();
        console.log('✅ Lançamento recebido:', lancamento);
        
        if (lancamento) {
            console.log('🎨 Abrindo modal para edição...');
            // Preencher o modal com os dados
            await openModalDespesa();
            
            console.log('📝 Preenchendo campo despesa-id com:', lancamento.id);
            document.getElementById('despesa-id').value = lancamento.id;
            console.log('✅ Campo despesa-id preenchido. Valor atual:', document.getElementById('despesa-id').value);
            document.getElementById('despesa-fornecedor').value = lancamento.pessoa || '';
            document.getElementById('despesa-categoria').value = lancamento.categoria || '';
            
            // Aguardar subcategorias carregarem
            await atualizarSubcategoriasDespesa();
            document.getElementById('despesa-subcategoria').value = lancamento.subcategoria || '';
            
            document.getElementById('despesa-vencimento').value = lancamento.data_vencimento ? lancamento.data_vencimento.split('T')[0] : '';
            document.getElementById('despesa-descricao').value = lancamento.descricao || '';
            document.getElementById('despesa-valor').value = lancamento.valor || '';
            document.getElementById('despesa-observacoes').value = lancamento.observacoes || '';
            
            console.log('🎯 Modal preenchido completamente');
            console.log('🔍 Verificação final do ID:', document.getElementById('despesa-id').value);
            console.log('========== FIM EDITAR DESPESA ==========\n');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar despesa para edição:', error);
        showToast('Erro ao carregar despesa', 'error');
    }
}

// === MODAL CONTA BANCÁRIA ===
function openModalConta(contaEdit = null) {
    console.log('=== openModalConta chamada ===');
    console.log('Conta para editar:', contaEdit);
    
    const isEdit = contaEdit !== null;
    const titulo = isEdit ? 'Editar Conta Bancária' : 'Nova Conta Bancária';
    
    if (isEdit) {
        console.log('🔍 Modo EDIÇÃO');
        console.log('   📊 saldo_inicial recebido:', contaEdit.saldo_inicial, 'tipo:', typeof contaEdit.saldo_inicial);
        console.log('   📊 saldo recebido:', contaEdit.saldo, 'tipo:', typeof contaEdit.saldo);
        const valorFormatado = formatarValorParaExibicao(contaEdit.saldo_inicial || 0);
        console.log('   ✏️ Valor formatado para exibição:', valorFormatado);
    }
    
    const modal = createModal(titulo, `
        <form id="form-conta" onsubmit="salvarConta(event)">
            <input type="hidden" id="conta-edit-mode" value="${isEdit}">
            <input type="hidden" id="conta-nome-original" value="${isEdit ? (contaEdit.nome || '') : ''}">
            
            <div class="form-group">
                <label>*Banco:</label>
                <input type="text" id="conta-banco" value="${isEdit ? (contaEdit.banco || '') : ''}" required placeholder="Ex: Banco do Brasil">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>*Agência:</label>
                    <input type="text" id="conta-agencia" value="${isEdit ? (contaEdit.agencia || '') : ''}" required placeholder="0000">
                </div>
                
                <div class="form-group">
                    <label>*Conta:</label>
                    <input type="text" id="conta-conta" value="${isEdit ? (contaEdit.conta || '') : ''}" required placeholder="00000-0">
                </div>
            </div>
            
            <div class="form-group">
                <label>*Saldo Inicial:</label>
                <input type="text" id="conta-saldo" inputmode="numeric" placeholder="0,00" value="${isEdit ? formatarValorParaExibicao(contaEdit.saldo_inicial || 0) : ''}" required>
            </div>
            
            <div class="form-group">
                <label>*Data de Início do Saldo:</label>
                <input type="date" id="conta-data-inicio" value="${isEdit && contaEdit.data_inicio ? contaEdit.data_inicio : ''}" required>
                <small style="color: #7f8c8d; font-size: 11px;">
                    📅 Data em que o saldo inicial foi registrado/implantado na conta. Esta data não será alterada ao importar extratos.
                </small>
            </div>
            
            <div class="form-group">
                <label>*Tipo de Saldo Inicial:</label>
                <select id="conta-tipo-saldo" required>
                    <option value="">Selecione...</option>
                    <option value="credor" ${isEdit && contaEdit.tipo_saldo_inicial === 'credor' ? 'selected' : ''}>💰 Credor (Positivo - Tenho dinheiro)</option>
                    <option value="devedor" ${isEdit && contaEdit.tipo_saldo_inicial === 'devedor' ? 'selected' : ''}>⚠️ Devedor (Negativo - Devo dinheiro)</option>
                </select>
                <small style="color: #7f8c8d; font-size: 11px;">
                    <strong>Credor:</strong> Conta com saldo positivo (você tem dinheiro)<br>
                    <strong>Devedor:</strong> Conta com saldo negativo (você deve ao banco, ex: cheque especial usado)
                </small>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Salvar</button>
            </div>
        </form>
    `);
    
    // Aplicar formatação de moeda ao campo após criar o modal
    setTimeout(() => {
        const campoSaldo = document.getElementById('conta-saldo');
        if (campoSaldo && typeof aplicarFormatacaoMoeda === 'function') {
            aplicarFormatacaoMoeda(campoSaldo);
            if (isEdit && contaEdit.saldo_inicial) {
                // Simular blur para formatar o valor inicial
                campoSaldo.blur();
                campoSaldo.focus();
                campoSaldo.blur();
            }
        }
    }, 100);
}

function formatarValorParaExibicao(valor) {
    console.log('💱 formatarValorParaExibicao - entrada:', valor, 'tipo:', typeof valor);
    if (!valor || valor === 0) return '';
    
    // Converte o valor para string com vírgula (formato brasileiro)
    const valorNum = parseFloat(valor);
    console.log('   📍 valorNum parseFloat:', valorNum);
    
    // Formatar para padrão brasileiro: 560.00 -> "560,00"
    const resultado = valorNum.toFixed(2).replace('.', ',');
    console.log('   ✅ Resultado formatado (BR):', resultado);
    return resultado;
}

async function salvarConta(event) {
    event.preventDefault();
    
    // Validar empresa_id
    if (!window.currentEmpresaId) {
        showToast('Erro: Empresa não identificada. Por favor, recarregue a página.', 'error');
        console.error('❌ window.currentEmpresaId não está definido!');
        return;
    }
    
    const isEdit = document.getElementById('conta-edit-mode').value === 'true';
    const nomeOriginal = document.getElementById('conta-nome-original').value;
    
    const banco = document.getElementById('conta-banco').value.trim();
    const agencia = document.getElementById('conta-agencia').value.trim();
    const conta = document.getElementById('conta-conta').value.trim();
    const campoSaldo = document.getElementById('conta-saldo');
    const dataInicio = document.getElementById('conta-data-inicio').value;
    const tipoSaldo = document.getElementById('conta-tipo-saldo').value;
    
    // Validar campos obrigatórios
    if (!banco) {
        showToast('⚠️ Preencha o nome do banco', 'warning');
        document.getElementById('conta-banco').focus();
        return;
    }
    
    if (!agencia) {
        showToast('⚠️ Preencha a agência', 'warning');
        document.getElementById('conta-agencia').focus();
        return;
    }
    
    if (!conta) {
        showToast('⚠️ Preencha o número da conta', 'warning');
        document.getElementById('conta-conta').focus();
        return;
    }
    
    if (!dataInicio) {
        showToast('⚠️ Preencha a data de início do saldo', 'warning');
        document.getElementById('conta-data-inicio').focus();
        return;
    }
    
    if (!tipoSaldo) {
        showToast('⚠️ Selecione o tipo de saldo inicial (Credor ou Devedor)', 'warning');
        document.getElementById('conta-tipo-saldo').focus();
        return;
    }
    
    // Gerar nome automático: BANCO - AGENCIA/CONTA
    const nomeGerado = `${banco} - ${agencia}/${conta}`;
    
    console.log('Nome gerado para a conta:', nomeGerado);
    console.log('É edição?', isEdit);
    console.log('Nome original:', nomeOriginal);
    
    // Obter valor real do saldo (tratando formatação brasileira)
    let saldoInicial = 0;
    if (typeof obterValorReal === 'function' && campoSaldo.dataset.valorReal) {
        saldoInicial = obterValorReal(campoSaldo);
    } else {
        // Fallback: converte manualmente se não tiver dataset
        const valorTexto = campoSaldo.value.replace(/\./g, '').replace(',', '.');
        saldoInicial = parseFloat(valorTexto) || 0;
    }
    
    // Se for devedor, o saldo deve ser negativo
    if (tipoSaldo === 'devedor' && saldoInicial > 0) {
        saldoInicial = -saldoInicial;
    }
    // Se for credor, o saldo deve ser positivo
    if (tipoSaldo === 'credor' && saldoInicial < 0) {
        saldoInicial = Math.abs(saldoInicial);
    }
    
    const data = {
        nome: nomeGerado,
        banco: banco,
        agencia: agencia,
        conta: conta,
        saldo_inicial: saldoInicial,
        data_inicio: dataInicio,
        tipo_saldo_inicial: tipoSaldo,
        empresa_id: window.currentEmpresaId
    };
    
    console.log('=== Salvando Conta ===');
    console.log('Modo de edição:', isEdit);
    console.log('Nome original:', nomeOriginal);
    console.log('Data de início:', dataInicio);
    console.log('Tipo de saldo:', tipoSaldo);
    console.log('Saldo ajustado:', saldoInicial);
    console.log('Dados a enviar:', data);
    
    try {
        const url = isEdit ? `/api/contas/${encodeURIComponent(nomeOriginal)}` : '/api/contas';
        const method = isEdit ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        console.log('Resposta do servidor:', result);
        
        if (result.success) {
            showToast(isEdit ? '✓ Conta bancária atualizada com sucesso!' : '✓ Conta bancária adicionada com sucesso!', 'success');
            closeModal();
            if (typeof loadContasBancarias === 'function') loadContasBancarias();
            if (typeof loadContas === 'function') loadContas();
        } else {
            console.error('Erro do servidor:', result.error);
            showToast('Erro: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Erro ao salvar conta:', error);
        showToast('Erro ao salvar conta bancária', 'error');
    }
}

// === MODAL CATEGORIA ===
function openModalCategoria(categoriaEdit = null) {
    const isEdit = categoriaEdit !== null;
    const titulo = isEdit ? 'Editar Categoria' : 'Nova Categoria';
    const subcatsText = isEdit && categoriaEdit.subcategorias ? categoriaEdit.subcategorias.join('\n') : '';
    
    const modal = createModal(titulo, `
        <form id="form-categoria" onsubmit="salvarCategoria(event)">
            <input type="hidden" id="categoria-edit-mode" value="${isEdit}">
            <input type="hidden" id="categoria-nome-original" value="${isEdit ? (categoriaEdit.nome || '') : ''}">
            
            <div class="form-group">
                <label>*Nome da Categoria:</label>
                <input type="text" id="categoria-nome" value="${isEdit ? (categoriaEdit.nome || '') : ''}" required placeholder="Ex: VENDAS">
            </div>
            
            <div class="form-group">
                <label>*Tipo:</label>
                <select id="categoria-tipo" required>
                    <option value="">Selecione...</option>
                    <option value="RECEITA" ${isEdit && categoriaEdit.tipo && categoriaEdit.tipo.toUpperCase() === 'RECEITA' ? 'selected' : ''}>Receita</option>
                    <option value="DESPESA" ${isEdit && categoriaEdit.tipo && categoriaEdit.tipo.toUpperCase() === 'DESPESA' ? 'selected' : ''}>Despesa</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Subcategorias (uma por linha):</label>
                <textarea id="categoria-subcategorias" rows="5" placeholder="VENDA PRODUTO A&#10;VENDA PRODUTO B&#10;VENDA SERVIÇO">${subcatsText}</textarea>
                <small style="color: #7f8c8d;">Digite cada subcategoria em uma linha separada</small>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Salvar</button>
            </div>
        </form>
    `);
}

async function salvarCategoria(event) {
    event.preventDefault();
    
    const isEdit = document.getElementById('categoria-edit-mode').value === 'true';
    const nomeOriginal = document.getElementById('categoria-nome-original').value;
    
    const subcategoriasText = document.getElementById('categoria-subcategorias').value;
    const subcategorias = subcategoriasText
        .split('\n')
        .map(s => s.trim())
        .filter(s => s.length > 0);
    
    // Normalizar nome: uppercase e trim
    const nomeInput = document.getElementById('categoria-nome').value.trim().toUpperCase();
    
    // Validar empresa_id
    console.log('🔍 VERIFICANDO window.currentEmpresaId:', window.currentEmpresaId);
    if (!window.currentEmpresaId) {
        showToast('Erro: Empresa não identificada. Por favor, recarregue a página.', 'error');
        console.error('❌ window.currentEmpresaId não está definido!');
        return;
    }
    console.log('✅ window.currentEmpresaId validado:', window.currentEmpresaId);
    
    const data = {
        nome: nomeInput,
        tipo: document.getElementById('categoria-tipo').value,
        subcategorias: subcategorias,
        empresa_id: window.currentEmpresaId
    };
    
    console.log('=== Salvando Categoria ===');
    console.log('Modo de edição:', isEdit);
    console.log('Nome original:', nomeOriginal);
    console.log('Dados a enviar:', data);
    console.log('📦 JSON.stringify(data):', JSON.stringify(data, null, 2));
    
    try {
        const url = isEdit ? `/api/categorias/${encodeURIComponent(nomeOriginal)}` : '/api/categorias';
        const method = isEdit ? 'PUT' : 'POST';
        
        console.log('🌐 Fazendo requisição:', method, url);
        console.log('📨 Body:', JSON.stringify(data));
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        console.log('📡 Resposta recebida:', result);
        console.log('   Status HTTP:', response.status);
        console.log('   response.ok:', response.ok);
        console.log('   result.success:', result.success);
        
        if (response.ok && result.success) {
            showToast(isEdit ? '✓ Categoria atualizada com sucesso!' : '✓ Categoria adicionada com sucesso!', 'success');
            closeModal();
            
            // Recarregar lista de categorias
            console.log('♻️ Recarregando lista de categorias...');
            if (typeof loadCategorias === 'function') {
                await loadCategorias();
                console.log('✅ Lista de categorias recarregada!');
            } else {
                console.error('❌ Função loadCategorias não encontrada!');
            }
        } else {
            // Melhorar mensagem de erro para duplicatas
            let errorMsg = result.error || 'Erro desconhecido';
            if (errorMsg.includes('Já existe uma categoria')) {
                errorMsg = errorMsg + ' Verifique a lista de categorias existentes na aba "Categorias".';
            }
            showToast(errorMsg, 'error');
            console.error('❌ Erro do servidor:', result.error);
        }
    } catch (error) {
        showToast('Erro ao salvar categoria', 'error');
        console.error('Erro completo:', error);
    }
}

// === MODAL CLIENTE ===
function openModalCliente(clienteEdit = null) {
    const isEdit = clienteEdit !== null;
    const titulo = isEdit ? 'Editar Cliente' : 'Novo Cliente';
    
    console.log('=== openModalCliente ===' );
    console.log('isEdit:', isEdit);
    if (isEdit) {
        console.log('Cliente recebido:', clienteEdit);
        console.log('razao_social:', clienteEdit.razao_social);
        console.log('nome:', clienteEdit.nome);
    }
    
    // Escapar HTML para valores de atributos
    const nomeOriginal = isEdit ? (clienteEdit.razao_social || clienteEdit.nome || '') : '';
    const nomeOriginalEscaped = nomeOriginal.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    
    const modal = createModal(titulo, `
        <form id="form-cliente" onsubmit="salvarCliente(event)">
            <input type="hidden" id="cliente-edit-mode" value="${isEdit}">
            <input type="hidden" id="cliente-nome-original" value="${nomeOriginalEscaped}">
            
            <div class="form-group">
                <label>*CNPJ:</label>
                <input type="text" id="cliente-cnpj" value="${isEdit ? (clienteEdit.cnpj || '') : ''}" required placeholder="00.000.000/0000-00" onblur="buscarDadosCNPJ()">
                <small style="color: #7f8c8d; font-size: 11px;">Digite o CNPJ para buscar dados automaticamente</small>
            </div>
            
            <div class="form-group">
                <label>*Razão Social:</label>
                <input type="text" id="cliente-razao" value="${isEdit ? (clienteEdit.razao_social || '') : ''}" required>
            </div>
            
            <div class="form-group">
                <label>*Nome Fantasia:</label>
                <input type="text" id="cliente-fantasia" value="${isEdit ? (clienteEdit.nome_fantasia || '') : ''}" required>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Inscrição Estadual:</label>
                    <input type="text" id="cliente-ie">
                </div>
                
                <div class="form-group">
                    <label>Inscrição Municipal:</label>
                    <input type="text" id="cliente-im">
                </div>
            </div>
            
            <hr style="margin: 20px 0; border: none; border-top: 2px solid #ecf0f1;">
            <h3 style="color: #2c3e50; margin-bottom: 15px;">Endereço</h3>
            
            <div class="form-group">
                <label>CEP:</label>
                <input type="text" id="cliente-cep" placeholder="00000-000" onblur="buscarCepCliente()">
            </div>
            
            <div class="form-group">
                <label>Rua/Avenida:</label>
                <input type="text" id="cliente-rua">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Número:</label>
                    <input type="text" id="cliente-numero">
                </div>
                
                <div class="form-group">
                    <label>Complemento:</label>
                    <input type="text" id="cliente-complemento">
                </div>
            </div>
            
            <div class="form-group">
                <label>Bairro:</label>
                <input type="text" id="cliente-bairro">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Cidade:</label>
                    <input type="text" id="cliente-cidade">
                </div>
                
                <div class="form-group">
                    <label>Estado:</label>
                    <select id="cliente-estado">
                        <option value="">Selecione...</option>
                        <option value="AC">AC</option>
                        <option value="AL">AL</option>
                        <option value="AP">AP</option>
                        <option value="AM">AM</option>
                        <option value="BA">BA</option>
                        <option value="CE">CE</option>
                        <option value="DF">DF</option>
                        <option value="ES">ES</option>
                        <option value="GO">GO</option>
                        <option value="MA">MA</option>
                        <option value="MT">MT</option>
                        <option value="MS">MS</option>
                        <option value="MG">MG</option>
                        <option value="PA">PA</option>
                        <option value="PB">PB</option>
                        <option value="PR">PR</option>
                        <option value="PE">PE</option>
                        <option value="PI">PI</option>
                        <option value="RJ">RJ</option>
                        <option value="RN">RN</option>
                        <option value="RS">RS</option>
                        <option value="RO">RO</option>
                        <option value="RR">RR</option>
                        <option value="SC">SC</option>
                        <option value="SP">SP</option>
                        <option value="SE">SE</option>
                        <option value="TO">TO</option>
                    </select>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Telefone:</label>
                    <input type="text" id="cliente-telefone" placeholder="(00) 00000-0000">
                </div>
                
                <div class="form-group">
                    <label>E-mail:</label>
                    <input type="email" id="cliente-email">
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Salvar</button>
            </div>
        </form>
    `);
    
    // Preencher campos se for edição
    if (isEdit && clienteEdit) {
        setTimeout(() => {
            document.getElementById('cliente-ie').value = clienteEdit.ie || '';
            document.getElementById('cliente-im').value = clienteEdit.im || '';
            document.getElementById('cliente-cep').value = clienteEdit.cep || '';
            document.getElementById('cliente-rua').value = clienteEdit.rua || '';
            document.getElementById('cliente-numero').value = clienteEdit.numero || '';
            document.getElementById('cliente-complemento').value = clienteEdit.complemento || '';
            document.getElementById('cliente-bairro').value = clienteEdit.bairro || '';
            document.getElementById('cliente-cidade').value = clienteEdit.cidade || '';
            document.getElementById('cliente-estado').value = clienteEdit.estado || '';
            document.getElementById('cliente-telefone').value = clienteEdit.telefone || clienteEdit.contato || '';
            document.getElementById('cliente-email').value = clienteEdit.email || '';
        }, 100);
    }
}

async function buscarCepCliente() {
    const cep = document.getElementById('cliente-cep').value.replace(/\D/g, '');
    if (cep.length !== 8) return;
    
    try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const data = await response.json();
        
        if (!data.erro) {
            document.getElementById('cliente-rua').value = (data.logradouro || '').toUpperCase();
            document.getElementById('cliente-bairro').value = (data.bairro || '').toUpperCase();
            document.getElementById('cliente-cidade').value = (data.localidade || '').toUpperCase();
            document.getElementById('cliente-estado').value = data.uf;
        }
    } catch (error) {
        console.error('Erro ao buscar CEP:', error);
    }
}

async function salvarCliente(event) {
    event.preventDefault();
    
    // Validar empresa_id
    if (!window.currentEmpresaId) {
        showToast('Erro: Empresa não identificada. Por favor, recarregue a página.', 'error');
        console.error('❌ window.currentEmpresaId não está definido!');
        return;
    }
    
    const isEdit = document.getElementById('cliente-edit-mode').value === 'true';
    const nomeOriginal = document.getElementById('cliente-nome-original').value;
    
    console.log('=== salvarCliente ===');
    console.log('isEdit:', isEdit);
    console.log('nomeOriginal do campo hidden:', nomeOriginal);
    console.log('Tamanho do nomeOriginal:', nomeOriginal.length);
    
    const data = {
        nome: document.getElementById('cliente-razao').value,
        razao_social: document.getElementById('cliente-razao').value,
        nome_fantasia: document.getElementById('cliente-fantasia').value,
        cnpj: document.getElementById('cliente-cnpj').value,
        ie: document.getElementById('cliente-ie').value,
        im: document.getElementById('cliente-im').value,
        cep: document.getElementById('cliente-cep').value,
        rua: document.getElementById('cliente-rua').value,
        numero: document.getElementById('cliente-numero').value,
        complemento: document.getElementById('cliente-complemento').value,
        bairro: document.getElementById('cliente-bairro').value,
        cidade: document.getElementById('cliente-cidade').value,
        estado: document.getElementById('cliente-estado').value,
        telefone: document.getElementById('cliente-telefone').value,
        contato: document.getElementById('cliente-telefone').value,
        email: document.getElementById('cliente-email').value.toLowerCase(),
        endereco: `${document.getElementById('cliente-rua').value}, ${document.getElementById('cliente-numero').value}`,
        documento: document.getElementById('cliente-cnpj').value,
        empresa_id: window.currentEmpresaId
    };
    
    console.log('=== Salvando Cliente ===');
    console.log('Modo de edição:', isEdit);
    console.log('Nome original:', nomeOriginal);
    console.log('Dados a enviar:', data);
    
    try {
        const url = isEdit ? `/api/clientes/${encodeURIComponent(nomeOriginal)}` : '/api/clientes';
        const method = isEdit ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(isEdit ? '✓ Cliente atualizado com sucesso!' : '✓ Cliente adicionado com sucesso!', 'success');
            closeModal();
            if (typeof loadClientes === 'function') await loadClientes();
            if (typeof loadClientes === 'function') loadClientes();
        } else {
            showToast('Erro: ' + result.error, 'error');
            console.error('Erro do servidor:', result.error);
        }
    } catch (error) {
        showToast('Erro ao salvar cliente', 'error');
        console.error('Erro completo:', error);
    }
}

// === MODAL FORNECEDOR ===
function openModalFornecedor(fornecedorEdit = null) {
    const isEdit = fornecedorEdit !== null;
    const titulo = isEdit ? 'Editar Fornecedor' : 'Novo Fornecedor';
    
    console.log('=== openModalFornecedor ===' );
    console.log('isEdit:', isEdit);
    if (isEdit) {
        console.log('Fornecedor recebido:', fornecedorEdit);
        console.log('razao_social:', fornecedorEdit.razao_social);
        console.log('nome:', fornecedorEdit.nome);
    }
    
    // Escapar HTML para valores de atributos
    const nomeOriginal = isEdit ? (fornecedorEdit.razao_social || fornecedorEdit.nome || '') : '';
    const nomeOriginalEscaped = nomeOriginal.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    
    const modal = createModal(titulo, `
        <form id="form-fornecedor" onsubmit="salvarFornecedor(event)">
            <input type="hidden" id="fornecedor-edit-mode" value="${isEdit}">
            <input type="hidden" id="fornecedor-nome-original" value="${nomeOriginalEscaped}">
            
            <div class="form-group">
                <label>*CNPJ:</label>
                <input type="text" id="fornecedor-cnpj" value="${isEdit ? (fornecedorEdit.cnpj || '') : ''}" required placeholder="00.000.000/0000-00" onblur="buscarDadosCNPJFornecedor()">
                <small style="color: #7f8c8d; font-size: 11px;">Digite o CNPJ para buscar dados automaticamente</small>
            </div>
            
            <div class="form-group">
                <label>*Razão Social:</label>
                <input type="text" id="fornecedor-razao" value="${isEdit ? (fornecedorEdit.razao_social || '') : ''}" required>
            </div>
            
            <div class="form-group">
                <label>*Nome Fantasia:</label>
                <input type="text" id="fornecedor-fantasia" value="${isEdit ? (fornecedorEdit.nome_fantasia || '') : ''}" required>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Inscrição Estadual:</label>
                    <input type="text" id="fornecedor-ie">
                </div>
                
                <div class="form-group">
                    <label>Inscrição Municipal:</label>
                    <input type="text" id="fornecedor-im">
                </div>
            </div>
            
            <hr style="margin: 20px 0; border: none; border-top: 2px solid #ecf0f1;">
            <h3 style="color: #2c3e50; margin-bottom: 15px;">Endereço</h3>
            
            <div class="form-group">
                <label>CEP:</label>
                <input type="text" id="fornecedor-cep" placeholder="00000-000" onblur="buscarCepFornecedor()">
            </div>
            
            <div class="form-group">
                <label>Rua/Avenida:</label>
                <input type="text" id="fornecedor-rua">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Número:</label>
                    <input type="text" id="fornecedor-numero">
                </div>
                
                <div class="form-group">
                    <label>Complemento:</label>
                    <input type="text" id="fornecedor-complemento">
                </div>
            </div>
            
            <div class="form-group">
                <label>Bairro:</label>
                <input type="text" id="fornecedor-bairro">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Cidade:</label>
                    <input type="text" id="fornecedor-cidade">
                </div>
                
                <div class="form-group">
                    <label>Estado:</label>
                    <select id="fornecedor-estado">
                        <option value="">Selecione...</option>
                        <option value="AC">AC</option>
                        <option value="AL">AL</option>
                        <option value="AP">AP</option>
                        <option value="AM">AM</option>
                        <option value="BA">BA</option>
                        <option value="CE">CE</option>
                        <option value="DF">DF</option>
                        <option value="ES">ES</option>
                        <option value="GO">GO</option>
                        <option value="MA">MA</option>
                        <option value="MT">MT</option>
                        <option value="MS">MS</option>
                        <option value="MG">MG</option>
                        <option value="PA">PA</option>
                        <option value="PB">PB</option>
                        <option value="PR">PR</option>
                        <option value="PE">PE</option>
                        <option value="PI">PI</option>
                        <option value="RJ">RJ</option>
                        <option value="RN">RN</option>
                        <option value="RS">RS</option>
                        <option value="RO">RO</option>
                        <option value="RR">RR</option>
                        <option value="SC">SC</option>
                        <option value="SP">SP</option>
                        <option value="SE">SE</option>
                        <option value="TO">TO</option>
                    </select>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Telefone:</label>
                    <input type="text" id="fornecedor-telefone" placeholder="(00) 00000-0000">
                </div>
                
                <div class="form-group">
                    <label>E-mail:</label>
                    <input type="email" id="fornecedor-email">
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Salvar</button>
            </div>
        </form>
    `);
    
    // Preencher campos se for edição
    if (isEdit && fornecedorEdit) {
        setTimeout(() => {
            document.getElementById('fornecedor-ie').value = fornecedorEdit.ie || '';
            document.getElementById('fornecedor-im').value = fornecedorEdit.im || '';
            document.getElementById('fornecedor-cep').value = fornecedorEdit.cep || '';
            document.getElementById('fornecedor-rua').value = fornecedorEdit.rua || '';
            document.getElementById('fornecedor-numero').value = fornecedorEdit.numero || '';
            document.getElementById('fornecedor-complemento').value = fornecedorEdit.complemento || '';
            document.getElementById('fornecedor-bairro').value = fornecedorEdit.bairro || '';
            document.getElementById('fornecedor-cidade').value = fornecedorEdit.cidade || '';
            document.getElementById('fornecedor-estado').value = fornecedorEdit.estado || '';
            document.getElementById('fornecedor-telefone').value = fornecedorEdit.telefone || fornecedorEdit.contato || '';
            document.getElementById('fornecedor-email').value = fornecedorEdit.email || '';
        }, 100);
    }
}

async function buscarCepFornecedor() {
    const cep = document.getElementById('fornecedor-cep').value.replace(/\D/g, '');
    if (cep.length !== 8) return;
    
    try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const data = await response.json();
        
        if (!data.erro) {
            document.getElementById('fornecedor-rua').value = (data.logradouro || '').toUpperCase();
            document.getElementById('fornecedor-bairro').value = (data.bairro || '').toUpperCase();
            document.getElementById('fornecedor-cidade').value = (data.localidade || '').toUpperCase();
            document.getElementById('fornecedor-estado').value = data.uf;
        }
    } catch (error) {
        console.error('Erro ao buscar CEP:', error);
    }
}

async function salvarFornecedor(event) {
    event.preventDefault();
    
    // Validar empresa_id
    if (!window.currentEmpresaId) {
        showToast('Erro: Empresa não identificada. Por favor, recarregue a página.', 'error');
        console.error('❌ window.currentEmpresaId não está definido!');
        return;
    }
    
    const isEdit = document.getElementById('fornecedor-edit-mode').value === 'true';
    const nomeOriginal = document.getElementById('fornecedor-nome-original').value;
    
    const data = {
        nome: document.getElementById('fornecedor-razao').value,
        razao_social: document.getElementById('fornecedor-razao').value,
        nome_fantasia: document.getElementById('fornecedor-fantasia').value,
        cnpj: document.getElementById('fornecedor-cnpj').value,
        ie: document.getElementById('fornecedor-ie').value,
        im: document.getElementById('fornecedor-im').value,
        cep: document.getElementById('fornecedor-cep').value,
        rua: document.getElementById('fornecedor-rua').value,
        numero: document.getElementById('fornecedor-numero').value,
        complemento: document.getElementById('fornecedor-complemento').value,
        bairro: document.getElementById('fornecedor-bairro').value,
        cidade: document.getElementById('fornecedor-cidade').value,
        estado: document.getElementById('fornecedor-estado').value,
        telefone: document.getElementById('fornecedor-telefone').value,
        contato: document.getElementById('fornecedor-telefone').value,
        email: document.getElementById('fornecedor-email').value.toLowerCase(),
        endereco: `${document.getElementById('fornecedor-rua').value}, ${document.getElementById('fornecedor-numero').value}`,
        documento: document.getElementById('fornecedor-cnpj').value,
        empresa_id: window.currentEmpresaId
    };
    
    console.log('=== Salvando Fornecedor ===');
    console.log('Modo de edição:', isEdit);
    console.log('Nome original:', nomeOriginal);
    console.log('Dados a enviar:', JSON.stringify(data, null, 2));
    
    try {
        const url = isEdit ? `/api/fornecedores/${encodeURIComponent(nomeOriginal)}` : '/api/fornecedores';
        const method = isEdit ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(isEdit ? '✓ Fornecedor atualizado com sucesso!' : '✓ Fornecedor adicionado com sucesso!', 'success');
            closeModal();
            if (typeof loadFornecedoresTable === 'function') loadFornecedoresTable();
            if (typeof loadFornecedores === 'function') loadFornecedores();
        } else {
            showToast('Erro: ' + result.error, 'error');
            console.error('Erro do servidor:', result.error);
        }
    } catch (error) {
        showToast('Erro ao salvar fornecedor', 'error');
        console.error('Erro completo:', error);
    }
}

// === FUNÇÕES AUXILIARES DE MODAL ===
function createModal(title, content) {
    // Remove modal existente se houver
    const existingModal = document.getElementById('dynamic-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Criar novo modal
    const modal = document.createElement('div');
    modal.id = 'dynamic-modal';
    modal.className = 'modal';
    modal.style.display = 'block';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                ${title}
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            ${content}
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Fechar ao clicar fora
    modal.onclick = function(event) {
        if (event.target === modal) {
            closeModal();
        }
    };
    
    return modal;
}

function closeModal() {
    const modal = document.getElementById('dynamic-modal');
    if (modal) {
        modal.remove();
    }
}

// === EDITAR LANÇAMENTO ===
// Exportar funções para escopo global
window.openModalReceita = openModalReceita;
window.salvarReceita = salvarReceita;
window.editarReceita = editarReceita;
window.openModalDespesa = openModalDespesa;
window.salvarDespesa = salvarDespesa;
window.editarDespesa = editarDespesa;
window.openModalCliente = openModalCliente;
window.salvarCliente = salvarCliente;
window.openModalFornecedor = openModalFornecedor;
window.salvarFornecedor = salvarFornecedor;
window.openModalConta = openModalConta;
window.salvarConta = salvarConta;
window.openModalCategoria = openModalCategoria;
window.salvarCategoria = salvarCategoria;
window.closeModal = closeModal;

// === MODAL TRANSFERÊNCIA ===

async function openModalTransferencia() {
    console.log('=== openModalTransferencia chamada ===');
    
    const modal = document.getElementById('modal-transferencia');
    if (!modal) {
        console.error('Modal de transferência não encontrado');
        return;
    }
    
    // Carregar contas bancárias
    try {
        const response = await fetch('/api/contas');
        const contas = await response.json();
        
        const selectOrigem = document.getElementById('transferencia-origem');
        const selectDestino = document.getElementById('transferencia-destino');
        
        if (selectOrigem && selectDestino) {
            // Limpar e preencher selects
            selectOrigem.innerHTML = '<option value="">Selecione a conta de origem</option>';
            selectDestino.innerHTML = '<option value="">Selecione a conta de destino</option>';
            
            contas.forEach(conta => {
                const optionOrigem = document.createElement('option');
                optionOrigem.value = conta.nome;
                optionOrigem.textContent = `${conta.banco} - ${conta.agencia}/${conta.conta}`;
                selectOrigem.appendChild(optionOrigem);
                
                const optionDestino = document.createElement('option');
                optionDestino.value = conta.nome;
                optionDestino.textContent = `${conta.banco} - ${conta.agencia}/${conta.conta}`;
                selectDestino.appendChild(optionDestino);
            });
        }
        
        // Definir data de hoje
        const dataInput = document.getElementById('transferencia-data');
        if (dataInput) {
            const hoje = new Date().toISOString().split('T')[0];
            dataInput.value = hoje;
        }
        
        // Limpar campos
        const valorInput = document.getElementById('transferencia-valor');
        const obsInput = document.getElementById('transferencia-observacoes');
        if (valorInput) valorInput.value = '';
        if (obsInput) obsInput.value = '';
        
        // Mostrar modal
        modal.style.display = 'flex';
        
    } catch (error) {
        console.error('Erro ao carregar contas para transferência:', error);
        showToast('Erro ao carregar contas bancárias', 'error');
    }
}

function closeModalTransferencia() {
    const modal = document.getElementById('modal-transferencia');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function salvarTransferencia() {
    // Validar empresa_id
    if (!window.currentEmpresaId) {
        showToast('Erro: Empresa não identificada. Por favor, recarregue a página.', 'error');
        console.error('❌ window.currentEmpresaId não está definido!');
        return;
    }
    
    const origem = document.getElementById('transferencia-origem').value;
    const destino = document.getElementById('transferencia-destino').value;
    const valor = parseFloat(document.getElementById('transferencia-valor').value);
    const data = document.getElementById('transferencia-data').value;
    const observacoes = document.getElementById('transferencia-observacoes').value;
    
    // Validações
    if (!origem) {
        showToast('⚠️ Selecione a conta de origem', 'warning');
        return;
    }
    
    if (!destino) {
        showToast('⚠️ Selecione a conta de destino', 'warning');
        return;
    }
    
    if (origem === destino) {
        showToast('⚠️ A conta de origem e destino não podem ser iguais', 'warning');
        return;
    }
    
    if (!valor || valor <= 0) {
        showToast('⚠️ Informe um valor válido para a transferência', 'warning');
        return;
    }
    
    if (!data) {
        showToast('⚠️ Informe a data da transferência', 'warning');
        return;
    }
    
    const dados = {
        conta_origem: origem,
        conta_destino: destino,
        valor: valor,
        data: data,
        descricao: observacoes || `Transferência de ${origem} para ${destino}`,
        empresa_id: window.currentEmpresaId
    };
    
    console.log('Dados da transferência:', dados);
    
    try {
        const response = await fetch('/api/transferencias', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        console.log('Resposta do servidor:', result);
        
        if (result.success) {
            showToast('✓ Transferência realizada com sucesso!', 'success');
            closeModalTransferencia();
            
            // Recarregar listas se existirem
            if (typeof loadContasBancarias === 'function') loadContasBancarias();
            if (typeof loadFluxoCaixa === 'function') loadFluxoCaixa();
        } else {
            showToast('Erro: ' + (result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Erro ao salvar transferência:', error);
        showToast('Erro ao realizar transferência', 'error');
    }
}

// Buscar dados do CNPJ na API BrasilAPI
async function buscarDadosCNPJ() {
    const cnpjInput = document.getElementById('cliente-cnpj');
    if (!cnpjInput) return;
    
    let cnpj = cnpjInput.value.replace(/\D/g, ''); // Remove caracteres não numéricos
    
    if (cnpj.length !== 14) {
        console.log('CNPJ incompleto, aguardando...');
        return;
    }
    
    console.log('🔍 Buscando dados do CNPJ:', cnpj);
    
    // Criar elemento de loading
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'cnpj-loading';
    loadingDiv.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 30px 40px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        z-index: 10001;
        text-align: center;
    `;
    loadingDiv.innerHTML = `
        <div style="display: inline-block; width: 50px; height: 50px; border: 5px solid #f3f3f3; border-top: 5px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        <p style="margin: 15px 0 0 0; color: #2c3e50; font-weight: 600; font-size: 15px;">🔍 Buscando dados do CNPJ...</p>
        <p style="margin: 5px 0 0 0; color: #7f8c8d; font-size: 12px;">Aguarde, estamos consultando a Receita Federal</p>
        <style>
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    `;
    
    // Adicionar backdrop
    const backdrop = document.createElement('div');
    backdrop.id = 'cnpj-backdrop';
    backdrop.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 10000;
    `;
    
    document.body.appendChild(backdrop);
    document.body.appendChild(loadingDiv);
    
    try {
        // Desabilitar campo
        cnpjInput.disabled = true;
        
        const response = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpj}`);
        
        if (!response.ok) {
            throw new Error('CNPJ não encontrado');
        }
        
        const dados = await response.json();
        console.log('✅ Dados recebidos:', dados);
        
        // Preencher campos
        if (dados.razao_social) {
            document.getElementById('cliente-razao').value = dados.razao_social;
        }
        
        if (dados.nome_fantasia) {
            document.getElementById('cliente-fantasia').value = dados.nome_fantasia;
        } else {
            document.getElementById('cliente-fantasia').value = dados.razao_social; // Usar razão social se não tiver fantasia
        }
        
        // Endereço
        if (dados.cep) {
            document.getElementById('cliente-cep').value = dados.cep.replace(/(\d{5})(\d{3})/, '$1-$2');
        }
        
        if (dados.logradouro) {
            document.getElementById('cliente-rua').value = dados.logradouro;
        }
        
        if (dados.numero) {
            document.getElementById('cliente-numero').value = dados.numero;
        }
        
        if (dados.complemento) {
            document.getElementById('cliente-complemento').value = dados.complemento;
        }
        
        if (dados.bairro) {
            document.getElementById('cliente-bairro').value = dados.bairro;
        }
        
        if (dados.municipio) {
            document.getElementById('cliente-cidade').value = dados.municipio;
        }
        
        if (dados.uf) {
            document.getElementById('cliente-estado').value = dados.uf;
        }
        
        // Contatos
        if (dados.ddd_telefone_1) {
            const tel = dados.ddd_telefone_1.replace(/(\d{2})(\d{4,5})(\d{4})/, '($1) $2-$3');
            document.getElementById('cliente-telefone').value = tel;
        }
        
        if (dados.email) {
            document.getElementById('cliente-email').value = dados.email;
        }
        
        showToast('✅ Dados do CNPJ carregados com sucesso!', 'success');
        
    } catch (error) {
        console.error('❌ Erro ao buscar CNPJ:', error);
        showToast('⚠️ CNPJ não encontrado ou inválido', 'warning');
    } finally {
        // Remover loading
        const loadingDiv = document.getElementById('cnpj-loading');
        const backdrop = document.getElementById('cnpj-backdrop');
        if (loadingDiv) loadingDiv.remove();
        if (backdrop) backdrop.remove();
        
        cnpjInput.disabled = false;
    }
}

// Buscar dados do CNPJ para Fornecedor
async function buscarDadosCNPJFornecedor() {
    const cnpjInput = document.getElementById('fornecedor-cnpj');
    if (!cnpjInput) return;
    
    let cnpj = cnpjInput.value.replace(/\D/g, '');
    
    if (cnpj.length !== 14) {
        console.log('CNPJ incompleto, aguardando...');
        return;
    }
    
    console.log('🔍 Buscando dados do CNPJ (Fornecedor):', cnpj);
    
    // Criar elemento de loading
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'cnpj-loading';
    loadingDiv.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 30px 40px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        z-index: 10001;
        text-align: center;
    `;
    loadingDiv.innerHTML = `
        <div style="display: inline-block; width: 50px; height: 50px; border: 5px solid #f3f3f3; border-top: 5px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        <p style="margin: 15px 0 0 0; color: #2c3e50; font-weight: 600; font-size: 15px;">🔍 Buscando dados do CNPJ...</p>
        <p style="margin: 5px 0 0 0; color: #7f8c8d; font-size: 12px;">Aguarde, estamos consultando a Receita Federal</p>
        <style>
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    `;
    
    const backdrop = document.createElement('div');
    backdrop.id = 'cnpj-backdrop';
    backdrop.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 10000;
    `;
    
    document.body.appendChild(backdrop);
    document.body.appendChild(loadingDiv);
    
    try {
        cnpjInput.disabled = true;
        
        const response = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpj}`);
        
        if (!response.ok) {
            throw new Error('CNPJ não encontrado');
        }
        
        const dados = await response.json();
        console.log('✅ Dados recebidos:', dados);
        
        // Preencher campos
        if (dados.razao_social) {
            document.getElementById('fornecedor-razao').value = dados.razao_social;
        }
        
        if (dados.nome_fantasia) {
            document.getElementById('fornecedor-fantasia').value = dados.nome_fantasia;
        } else {
            document.getElementById('fornecedor-fantasia').value = dados.razao_social;
        }
        
        // Endereço
        if (dados.cep) {
            document.getElementById('fornecedor-cep').value = dados.cep.replace(/(\d{5})(\d{3})/, '$1-$2');
        }
        
        if (dados.logradouro) {
            document.getElementById('fornecedor-rua').value = dados.logradouro;
        }
        
        if (dados.numero) {
            document.getElementById('fornecedor-numero').value = dados.numero;
        }
        
        if (dados.complemento) {
            document.getElementById('fornecedor-complemento').value = dados.complemento;
        }
        
        if (dados.bairro) {
            document.getElementById('fornecedor-bairro').value = dados.bairro;
        }
        
        if (dados.municipio) {
            document.getElementById('fornecedor-cidade').value = dados.municipio;
        }
        
        if (dados.uf) {
            document.getElementById('fornecedor-estado').value = dados.uf;
        }
        
        // Contatos
        if (dados.ddd_telefone_1) {
            const tel = dados.ddd_telefone_1.replace(/(\d{2})(\d{4,5})(\d{4})/, '($1) $2-$3');
            document.getElementById('fornecedor-telefone').value = tel;
        }
        
        if (dados.email) {
            document.getElementById('fornecedor-email').value = dados.email;
        }
        
        showToast('✅ Dados do CNPJ carregados com sucesso!', 'success');
        
    } catch (error) {
        console.error('❌ Erro ao buscar CNPJ:', error);
        showToast('⚠️ CNPJ não encontrado ou inválido', 'warning');
    } finally {
        const loadingDiv = document.getElementById('cnpj-loading');
        const backdrop = document.getElementById('cnpj-backdrop');
        if (loadingDiv) loadingDiv.remove();
        if (backdrop) backdrop.remove();
        
        cnpjInput.disabled = false;
    }
}

window.createModal = createModal;
window.openModalTransferencia = openModalTransferencia;
window.closeModalTransferencia = closeModalTransferencia;
window.salvarTransferencia = salvarTransferencia;
window.buscarDadosCNPJ = buscarDadosCNPJ;
window.buscarDadosCNPJFornecedor = buscarDadosCNPJFornecedor;

console.log('✓ Modals.js v20251204lancamentos5 carregado com sucesso');

