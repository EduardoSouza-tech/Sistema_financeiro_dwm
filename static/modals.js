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
    
    console.log('\n' + '='.repeat(80));
    console.log('🔵 INICIANDO salvarCategoria()');
    console.log('='.repeat(80));
    
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
    
    console.log('📋 DADOS DA CATEGORIA:');
    console.log('   Modo edição:', isEdit);
    console.log('   Nome original:', nomeOriginal);
    console.log('   Nome novo:', data.nome);
    console.log('   Tipo:', data.tipo);
    console.log('   Subcategorias:', data.subcategorias);
    console.log('   Empresa ID:', data.empresa_id);
    
    // Obter CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    console.log('🔑 CSRF Token:', csrfToken ? 'PRESENTE ✓' : '⚠️ AUSENTE');
    if (!csrfToken) {
        console.error('❌ CSRF TOKEN NÃO ENCONTRADO! Requisição será bloqueada!');
        showToast('Erro: Token de segurança não encontrado. Recarregue a página.', 'error');
        return;
    }
    
    try {
        const url = isEdit ? `/api/categorias/${encodeURIComponent(nomeOriginal)}` : '/api/categorias';
        const method = isEdit ? 'PUT' : 'POST';
        
        console.log('🌐 REQUISIÇÃO HTTP:');
        console.log('   Method:', method);
        console.log('   URL:', url);
        console.log('   Headers:', {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken ? '***PRESENTE***' : 'AUSENTE'
        });
        console.log('   Body:', JSON.stringify(data, null, 2));
        
        const response = await fetch(url, {
            method: method,
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        });
        
        console.log('📡 RESPOSTA HTTP:');
        console.log('   Status:', response.status, response.statusText);
        console.log('   OK?:', response.ok);
        
        const result = await response.json();
        console.log('   Body:', result);
        
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
        console.error('❌ EXCEPTION:', error);
        console.error('   Stack:', error.stack);
    }
    
    console.log('='.repeat(80));
    console.log('🔵 FIM salvarCategoria()');
    console.log('='.repeat(80) + '\n');
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
        console.log('nome_fantasia:', clienteEdit.nome_fantasia);
    }
    
    // Escapar HTML para valores de atributos
    // Backend pode retornar só 'nome' ou 'razao_social'
    const nomeOriginal = isEdit ? (clienteEdit.razao_social || clienteEdit.nome || '') : '';
    const nomeOriginalEscaped = nomeOriginal.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    
    // Usar nome como razao_social se razao_social não existir
    const razaoSocial = isEdit ? (clienteEdit.razao_social || clienteEdit.nome || '') : '';
    const nomeFantasia = isEdit ? (clienteEdit.nome_fantasia || clienteEdit.nome || '') : '';
    const cnpj = isEdit ? (clienteEdit.cnpj || clienteEdit.cpf_cnpj || clienteEdit.documento || '') : '';
    
    const modal = createModal(titulo, `
        <form id="form-cliente" onsubmit="salvarCliente(event)">
            <input type="hidden" id="cliente-edit-mode" value="${isEdit}">
            <input type="hidden" id="cliente-nome-original" value="${nomeOriginalEscaped}">
            
            <div class="form-group">
                <label>*CNPJ:</label>
                <input type="text" id="cliente-cnpj" value="${cnpj}" required placeholder="00.000.000/0000-00" onblur="buscarDadosCNPJ()">
                <small style="color: #7f8c8d; font-size: 11px;">Digite o CNPJ para buscar dados automaticamente</small>
            </div>
            
            <div class="form-group">
                <label>*Razão Social:</label>
                <input type="text" id="cliente-razao" value="${razaoSocial}" required>
            </div>
            
            <div class="form-group">
                <label>*Nome Fantasia:</label>
                <input type="text" id="cliente-fantasia" value="${nomeFantasia}" required>
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
            console.log('📝 Preenchendo campos de edição com:', clienteEdit);
            
            // Preencher campos adicionais que não estavam no HTML inicial
            const campoIE = document.getElementById('cliente-ie');
            const campoIM = document.getElementById('cliente-im');
            const campoCEP = document.getElementById('cliente-cep');
            const campoRua = document.getElementById('cliente-rua');
            const campoNumero = document.getElementById('cliente-numero');
            const campoComplemento = document.getElementById('cliente-complemento');
            const campoBairro = document.getElementById('cliente-bairro');
            const campoCidade = document.getElementById('cliente-cidade');
            const campoEstado = document.getElementById('cliente-estado');
            const campoTelefone = document.getElementById('cliente-telefone');
            const campoEmail = document.getElementById('cliente-email');
            
            if (campoIE) campoIE.value = clienteEdit.ie || '';
            if (campoIM) campoIM.value = clienteEdit.im || '';
            if (campoCEP) campoCEP.value = clienteEdit.cep || '';
            if (campoRua) campoRua.value = clienteEdit.rua || clienteEdit.endereco || '';
            if (campoNumero) campoNumero.value = clienteEdit.numero || '';
            if (campoComplemento) campoComplemento.value = clienteEdit.complemento || '';
            if (campoBairro) campoBairro.value = clienteEdit.bairro || '';
            if (campoCidade) campoCidade.value = clienteEdit.cidade || '';
            if (campoEstado) campoEstado.value = clienteEdit.estado || clienteEdit.uf || '';
            if (campoTelefone) campoTelefone.value = clienteEdit.telefone || clienteEdit.contato || '';
            if (campoEmail) campoEmail.value = clienteEdit.email || '';
            
            console.log('✅ Campos preenchidos com sucesso');
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
        console.log('cnpj:', fornecedorEdit.cnpj);
        console.log('telefone:', fornecedorEdit.telefone);
        console.log('email:', fornecedorEdit.email);
        console.log('endereco:', fornecedorEdit.endereco);
    }
    
    // Escapar HTML para valores de atributos
    // Backend pode retornar só 'nome' ou 'razao_social'
    const nomeOriginal = isEdit ? (fornecedorEdit.razao_social || fornecedorEdit.nome || '') : '';
    const nomeOriginalEscaped = nomeOriginal.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    
    // Usar nome como fallback para razao_social
    const razaoSocial = isEdit ? (fornecedorEdit.razao_social || fornecedorEdit.nome || '') : '';
    const nomeFantasia = isEdit ? (fornecedorEdit.nome_fantasia || fornecedorEdit.nome || '') : '';
    const cnpj = isEdit ? (fornecedorEdit.cnpj || fornecedorEdit.cpf_cnpj || fornecedorEdit.documento || '') : '';
    const telefone = isEdit ? (fornecedorEdit.telefone || fornecedorEdit.contato || '') : '';
    const email = isEdit ? (fornecedorEdit.email || '') : '';
    const endereco = isEdit ? (fornecedorEdit.endereco || fornecedorEdit.rua || '') : '';
    
    const modal = createModal(titulo, `
        <form id="form-fornecedor" onsubmit="salvarFornecedor(event)">
            <input type="hidden" id="fornecedor-edit-mode" value="${isEdit}">
            <input type="hidden" id="fornecedor-nome-original" value="${nomeOriginalEscaped}">
            
            <div class="form-group">
                <label>*CNPJ:</label>
                <input type="text" id="fornecedor-cnpj" value="${cnpj}" required placeholder="00.000.000/0000-00" onblur="buscarDadosCNPJFornecedor()">
                <small style="color: #7f8c8d; font-size: 11px;">Digite o CNPJ para buscar dados automaticamente</small>
            </div>
            
            <div class="form-group">
                <label>*Razão Social:</label>
                <input type="text" id="fornecedor-razao" value="${razaoSocial}" required>
            </div>
            
            <div class="form-group">
                <label>*Nome Fantasia:</label>
                <input type="text" id="fornecedor-fantasia" value="${nomeFantasia}" required>
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
            console.log('📝 Preenchendo campos de fornecedor com:', fornecedorEdit);
            
            const campoIE = document.getElementById('fornecedor-ie');
            const campoIM = document.getElementById('fornecedor-im');
            const campoCEP = document.getElementById('fornecedor-cep');
            const campoRua = document.getElementById('fornecedor-rua');
            const campoNumero = document.getElementById('fornecedor-numero');
            const campoComplemento = document.getElementById('fornecedor-complemento');
            const campoBairro = document.getElementById('fornecedor-bairro');
            const campoCidade = document.getElementById('fornecedor-cidade');
            const campoEstado = document.getElementById('fornecedor-estado');
            const campoTelefone = document.getElementById('fornecedor-telefone');
            const campoEmail = document.getElementById('fornecedor-email');
            
            if (campoIE) campoIE.value = fornecedorEdit.ie || '';
            if (campoIM) campoIM.value = fornecedorEdit.im || '';
            if (campoCEP) campoCEP.value = fornecedorEdit.cep || '';
            if (campoRua) campoRua.value = fornecedorEdit.rua || fornecedorEdit.endereco || '';
            if (campoNumero) campoNumero.value = fornecedorEdit.numero || '';
            if (campoComplemento) campoComplemento.value = fornecedorEdit.complemento || '';
            if (campoBairro) campoBairro.value = fornecedorEdit.bairro || '';
            if (campoCidade) campoCidade.value = fornecedorEdit.cidade || '';
            if (campoEstado) campoEstado.value = fornecedorEdit.estado || fornecedorEdit.uf || '';
            if (campoTelefone) campoTelefone.value = fornecedorEdit.telefone || fornecedorEdit.contato || '';
            if (campoEmail) campoEmail.value = fornecedorEdit.email || '';
            
            console.log('✅ Campos de fornecedor preenchidos');
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

function closeModal(modalId) {
    console.log('🔷 [modals.js] closeModal chamada com ID:', modalId);
    
    // Se não passou modalId, tenta fechar o dynamic-modal (comportamento antigo)
    if (!modalId) {
        const modal = document.getElementById('dynamic-modal');
        if (modal) {
            console.log('   📍 Removendo dynamic-modal');
            modal.remove();
            return;
        }
        console.warn('   ⚠️ Nenhum modalId fornecido e dynamic-modal não encontrado');
        return;
    }
    
    // Fecha o modal especificado
    const modal = document.getElementById(modalId);
    console.log('   📍 Modal encontrado:', modal);
    
    if (modal) {
        console.log('   📊 Display ANTES:', modal.style.display);
        console.log('   📊 Classes ANTES:', modal.className);
        
        // Se o modal tem classe modal-overlay, remover do DOM (modais criados dinamicamente)
        if (modal.classList.contains('modal-overlay')) {
            console.log('   🗑️ Modal dinâmico - removendo do DOM');
            modal.remove();
            document.body.style.overflow = '';
            console.log('   ✅ Modal removido!');
        } else {
            // Modal estático - apenas ocultar
            modal.classList.remove('active');
            modal.style.display = 'none';
            document.body.style.overflow = '';
            console.log('   📊 Display DEPOIS:', modal.style.display);
            console.log('   📊 Classes DEPOIS:', modal.className);
            console.log('   ✅ Modal fechado com sucesso!');
        }
    } else {
        console.warn('   ⚠️ Modal não encontrado:', modalId);
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
        
        // Filtrar apenas contas ativas
        const contasAtivas = contas.filter(c => c.ativa !== false);
        
        const selectOrigem = document.getElementById('transferencia-origem');
        const selectDestino = document.getElementById('transferencia-destino');
        
        if (selectOrigem && selectDestino) {
            // Limpar e preencher selects
            selectOrigem.innerHTML = '<option value="">Selecione a conta de origem</option>';
            selectDestino.innerHTML = '<option value="">Selecione a conta de destino</option>';
            
            contasAtivas.forEach(conta => {
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

// ============================================================================
// MODAL CONTRATO
// ============================================================================

async function openModalContrato(contratoEdit = null) {
    console.log('📋 openModalContrato chamada', contratoEdit ? 'MODO EDIÇÃO' : 'MODO CRIAÇÃO');
    
    if (contratoEdit) {
        console.log('📦 Dados COMPLETOS do contrato recebidos:', contratoEdit);
        console.log('📝 Campos específicos:');
        console.log('   - descricao:', contratoEdit.descricao);
        console.log('   - data_inicio:', contratoEdit.data_inicio);
        console.log('   - data_contrato:', contratoEdit.data_contrato);
        console.log('   - valor:', contratoEdit.valor, '(tipo:', typeof contratoEdit.valor + ')');
        console.log('   - valor_total:', contratoEdit.valor_total);
        console.log('   - valor_mensal:', contratoEdit.valor_mensal);
        console.log('   - quantidade_meses:', contratoEdit.quantidade_meses);
        console.log('   - imposto:', contratoEdit.imposto);
        console.log('   - imposto_percentual:', contratoEdit.imposto_percentual);
        console.log('   - comissoes:', contratoEdit.comissoes);
    }
    
    // Carregar clientes se necessário
    if (!window.clientes || window.clientes.length === 0) {
        await loadClientes();
    }
    
    // Carregar funcionários se necessário
    if (!window.funcionarios || window.funcionarios.length === 0) {
        await loadFuncionarios();
    }
    
    const isEdit = contratoEdit !== null;
    const titulo = isEdit ? 'Editar Contrato' : 'Novo Contrato';
    
    // Converter data para formato yyyy-MM-dd se necessário
    let dataContratoFormatada = '';
    if (isEdit && (contratoEdit.data_inicio || contratoEdit.data_contrato)) {
        const dataRaw = contratoEdit.data_inicio || contratoEdit.data_contrato;
        try {
            const dataObj = new Date(dataRaw);
            dataContratoFormatada = dataObj.toISOString().split('T')[0]; // yyyy-MM-dd
            console.log('📅 Data convertida:', dataRaw, '→', dataContratoFormatada);
        } catch (e) {
            console.error('❌ Erro ao converter data:', e);
            dataContratoFormatada = '';
        }
    }
    
    // Calcular valor total para exibição
    let valorTotalFormatado = 'R$ 0,00';
    if (isEdit) {
        const valor = parseFloat(contratoEdit.valor || contratoEdit.valor_total || 0) || 
                     (contratoEdit.valor_mensal * contratoEdit.quantidade_meses) || 0;
        valorTotalFormatado = 'R$ ' + valor.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        console.log('💰 Valor Total calculado para modal:', valor, '→', valorTotalFormatado);
    }
    
    // Opções de clientes
    const opcoesClientes = window.clientes && window.clientes.length > 0
        ? window.clientes.map(c => {
            const selected = isEdit && contratoEdit.cliente_id === c.id ? 'selected' : '';
            return `<option value="${c.id}" ${selected}>${c.razao_social || c.nome}</option>`;
        }).join('')
        : '<option value="">Nenhum cliente cadastrado</option>';
    
    const modal = createModal(titulo, `
        <form id="form-contrato" onsubmit="salvarContrato(event)" style="max-height: 80vh; overflow-y: auto;">
            <input type="hidden" id="contrato-id" value="${isEdit ? contratoEdit.id : ''}">
            <input type="hidden" id="contrato-numero" value="${isEdit && contratoEdit.numero ? contratoEdit.numero : ''}">
            
            <!-- Linha 1: Cliente e Tipo -->
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 15px;">
                <div class="form-group">
                    <label>*Cliente:</label>
                    <select id="contrato-cliente" required>
                        <option value="">Selecione...</option>
                        ${opcoesClientes}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>*Tipo:</label>
                    <select id="contrato-tipo" required onchange="atualizarCalculoContrato()">
                        <option value="Mensal" ${isEdit && contratoEdit.tipo === 'Mensal' ? 'selected' : ''}>Mensal</option>
                        <option value="Único" ${isEdit && contratoEdit.tipo === 'Único' ? 'selected' : ''}>Único</option>
                        <option value="Anual" ${isEdit && contratoEdit.tipo === 'Anual' ? 'selected' : ''}>Anual</option>
                    </select>
                </div>
            </div>
            
            <!-- Linha 2: Nome e Descrição -->
            <div class="form-group">
                <label>*Nome do Contrato:</label>
                <input type="text" id="contrato-nome" required value="${isEdit ? contratoEdit.nome || '' : ''}" placeholder="Ex: Mensal 2026">
            </div>
            
            <div class="form-group">
                <label>Descrição:</label>
                <textarea id="contrato-descricao" rows="3" placeholder="Ex: Contrato mensal de horas para captação de fotos e vídeos...">${isEdit ? contratoEdit.descricao || '' : ''}</textarea>
            </div>
            
            <!-- Linha 3: Valores e Meses -->
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                <div class="form-group">
                    <label>*Valor Mensal:</label>
                    <input type="number" id="contrato-valor-mensal" step="any" min="0" required value="${isEdit ? contratoEdit.valor_mensal || '' : ''}" placeholder="3500.00" oninput="atualizarCalculoContrato()">
                </div>
                
                <div class="form-group">
                    <label>*Qtd. Meses:</label>
                    <input type="number" id="contrato-meses" min="1" step="1" required value="${isEdit ? contratoEdit.quantidade_meses || '1' : '1'}" oninput="atualizarCalculoContrato()">
                </div>
                
                <div class="form-group">
                    <label>Valor Total:</label>
                    <input type="text" id="contrato-valor-total" readonly="readonly" disabled style="background: #f0f0f0; font-weight: bold; color: #27ae60; font-size: 16px;" value="${valorTotalFormatado}">
                </div>
            </div>
            
            <!-- Linha 4: Horas, Pagamento, Parcelas -->
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                <div class="form-group">
                    <label>Horas Mensais:</label>
                    <input type="number" id="contrato-horas" min="0" value="${isEdit ? contratoEdit.horas_mensais || '' : ''}" placeholder="8">
                </div>
                
                <div class="form-group">
                    <label>*Forma Pagamento:</label>
                    <select id="contrato-pagamento" required>
                        <option value="PIX" ${isEdit && contratoEdit.forma_pagamento === 'PIX' ? 'selected' : ''}>PIX</option>
                        <option value="Boleto" ${isEdit && contratoEdit.forma_pagamento === 'Boleto' ? 'selected' : ''}>Boleto</option>
                        <option value="Transferência" ${isEdit && contratoEdit.forma_pagamento === 'Transferência' ? 'selected' : ''}>Transferência</option>
                        <option value="Dinheiro" ${isEdit && contratoEdit.forma_pagamento === 'Dinheiro' ? 'selected' : ''}>Dinheiro</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>*Qtd. Parcelas:</label>
                    <input type="number" id="contrato-parcelas" min="1" required value="${isEdit ? contratoEdit.quantidade_parcelas || '1' : '1'}">
                </div>
            </div>
            
            <!-- Linha 5: Datas -->
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 15px;">
                <div class="form-group">
                    <label>*Data Contrato:</label>
                    <input type="date" id="contrato-data" required value="${dataContratoFormatada}">
                </div>
                
                <div class="form-group">
                    <label>Dia Pagamento:</label>
                    <input type="number" id="contrato-dia-pagamento" min="1" max="31" placeholder="10" value="${isEdit && contratoEdit.dia_pagamento ? contratoEdit.dia_pagamento : ''}">
                </div>
                
                <div class="form-group">
                    <label>Dia Emissão NF:</label>
                    <input type="number" id="contrato-dia-nf" min="1" max="31" placeholder="3" value="${isEdit && contratoEdit.dia_emissao_nf ? contratoEdit.dia_emissao_nf : ''}">
                </div>
                
                <div class="form-group">
                    <label>Imposto (%):</label>
                    <input type="number" id="contrato-imposto" step="0.01" min="0" max="100" placeholder="10.00" value="${isEdit && contratoEdit.imposto !== null && contratoEdit.imposto !== undefined ? contratoEdit.imposto : (isEdit && contratoEdit.imposto_percentual !== null && contratoEdit.imposto_percentual !== undefined ? contratoEdit.imposto_percentual : '')}">
                </div>
            </div>
            
            <!-- Comissões -->
            <div class="form-group">
                <label>Comissões:</label>
                <div id="contrato-comissoes-container" style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: #f9f9f9;">
                    <div id="contrato-comissoes-list"></div>
                    <button type="button" onclick="adicionarComissaoContrato()" class="btn btn-sm" style="margin-top: 10px; background: #3498db; color: white;">➕ Adicionar Comissão</button>
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px; position: sticky; bottom: 0; background: white; padding: 15px 0; border-top: 2px solid #eee;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Salvar Contrato</button>
            </div>
        </form>
    `);
    
    // Verificar se o ID e NUMERO foram corretamente setados
    setTimeout(() => {
        const contratoIdField = document.getElementById('contrato-id');
        const contratoNumeroField = document.getElementById('contrato-numero');
        
        console.log('🔍 Verificação após criar modal:');
        console.log('   📝 Campo contrato-id existe?', !!contratoIdField);
        console.log('   📝 Valor do campo ID:', contratoIdField ? contratoIdField.value : 'CAMPO NÃO ENCONTRADO');
        console.log('   📝 Campo contrato-numero existe?', !!contratoNumeroField);
        console.log('   📝 Valor do campo NUMERO:', contratoNumeroField ? contratoNumeroField.value : 'CAMPO NÃO ENCONTRADO');
        console.log('   📝 isEdit:', isEdit);
        console.log('   📝 contratoEdit.id:', contratoEdit ? contratoEdit.id : 'N/A');
        console.log('   📝 contratoEdit.numero:', contratoEdit ? contratoEdit.numero : 'N/A');
        
        // Se estiver editando, forçar os valores novamente
        if (isEdit && contratoEdit) {
            if (contratoIdField && contratoEdit.id) {
                contratoIdField.value = contratoEdit.id;
                console.log('   ✅ ID forçado novamente para:', contratoEdit.id);
            }
            if (contratoNumeroField && contratoEdit.numero) {
                contratoNumeroField.value = contratoEdit.numero;
                console.log('   ✅ NUMERO forçado novamente para:', contratoEdit.numero);
            }
        }
    }, 50);
    
    // Preencher comissões existentes se estiver editando
    if (isEdit && contratoEdit.comissoes) {
        setTimeout(() => {
            const container = document.getElementById('contrato-comissoes-list');
            if (container) {
                container.innerHTML = ''; // Limpar antes de preencher
                if (Array.isArray(contratoEdit.comissoes)) {
                    contratoEdit.comissoes.forEach(com => {
                        adicionarComissaoContrato(com);
                    });
                }
            }
        }, 150);
    }
    
    // Calcular valor total inicial apenas em modo de criação
    // Em modo de edição, o valor já foi pré-calculado
    if (!isEdit) {
        setTimeout(() => {
            atualizarCalculoContrato();
        }, 100);
    }
}

// Helper para converter valor formatado pt-BR para número
function parseValorBR(valor) {
    if (typeof valor === 'number') return valor;
    if (!valor) return 0;
    
    // Remover espaços e R$
    let valorLimpo = valor.toString().trim().replace(/R\$\s*/g, '');
    
    // Remover pontos (separador de milhar)
    valorLimpo = valorLimpo.replace(/\./g, '');
    
    // Substituir vírgula por ponto (separador decimal)
    valorLimpo = valorLimpo.replace(/,/g, '.');
    
    const resultado = parseFloat(valorLimpo) || 0;
    console.log(`   🔄 parseValorBR("${valor}") = ${resultado}`);
    return resultado;
}

function atualizarCalculoContrato() {
    const campoValorMensal = document.getElementById('contrato-valor-mensal');
    const campoMeses = document.getElementById('contrato-meses');
    const campoTotal = document.getElementById('contrato-valor-total');
    
    console.log('🧮 Calculando:');
    console.log('   📍 campoValorMensal existe?', !!campoValorMensal);
    console.log('   📍 campoMeses existe?', !!campoMeses);
    console.log('   📍 campoTotal existe?', !!campoTotal);
    
    if (!campoValorMensal || !campoMeses || !campoTotal) {
        console.warn('⚠️ Campos de cálculo não encontrados - abortando atualização');
        return;
    }
    
    // Campo é type="number", então .value já é string numérica
    const valorMensal = parseFloat(campoValorMensal.value) || 0;
    const meses = parseInt(campoMeses.value) || 0;
    const valorTotal = valorMensal * meses;
    
    console.log('🧮 Calculando:');
    console.log('   📝 Valor Mensal (.value):', campoValorMensal.value);
    console.log('   💰 Valor Mensal (parseado):', valorMensal);
    console.log('   📝 Meses (.value):', campoMeses.value);
    console.log('   🔢 Meses (parseado):', meses);
    console.log('   💵 Valor Total:', valorTotal);
    
    // Formatar e exibir
    const valorFormatado = 'R$ ' + valorTotal.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    
    console.log('   🎨 Valor formatado:', valorFormatado);
    console.log('   📍 Campo existe?', !!campoTotal);
    console.log('   📍 Campo ID:', campoTotal ? campoTotal.id : 'N/A');
    console.log('   📍 Campo readonly?', campoTotal ? campoTotal.readOnly : 'N/A');
    console.log('   📍 Valor ANTES:', campoTotal.value);
    
    // Tentar ambos os métodos
    campoTotal.value = valorFormatado;
    campoTotal.setAttribute('value', valorFormatado);
    
    console.log('   📍 Valor DEPOIS (.value):', campoTotal.value);
    console.log('   📍 Valor DEPOIS (getAttribute):', campoTotal.getAttribute('value'));
    console.log('   ✅ Campo atualizado');
}

function adicionarComissaoContrato(dadosIniciais = null) {
    const container = document.getElementById('contrato-comissoes-list');
    if (!container) return;
    
    const opcoesFuncionarios = window.funcionarios && window.funcionarios.length > 0
        ? window.funcionarios.map(f => {
            const selected = dadosIniciais && dadosIniciais.funcionario_id === f.id ? 'selected' : '';
            return `<option value="${f.id}" ${selected}>${f.nome}</option>`;
        }).join('')
        : '<option value="">Nenhum funcionário</option>';
    
    const div = document.createElement('div');
    div.className = 'comissao-item';
    div.style.cssText = 'display: grid; grid-template-columns: 2fr 1fr auto; gap: 10px; margin-bottom: 10px; align-items: center;';
    div.innerHTML = `
        <select class="comissao-funcionario" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            <option value="">Selecione...</option>
            ${opcoesFuncionarios}
        </select>
        <input type="number" class="comissao-percentual" step="0.01" min="0" max="100" placeholder="4.25" value="${dadosIniciais ? dadosIniciais.percentual || '' : ''}" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        <button type="button" onclick="this.parentElement.remove()" class="btn btn-sm btn-danger" style="padding: 8px 12px;">🗑️</button>
    `;
    container.appendChild(div);
}

async function salvarContrato(event) {
    event.preventDefault();
    
    console.log('\n💾 ========== SALVAR CONTRATO ==========');
    
    const id = document.getElementById('contrato-id').value;
    const isEdit = id && id.trim() !== '';
    
    console.log('🎯 Modo:', isEdit ? 'EDIÇÃO' : 'CRIAÇÃO');
    console.log('📋 ID:', id);
    
    // Coletar comissões
    const comissoes = [];
    document.querySelectorAll('.comissao-item').forEach(item => {
        const funcionario_id = item.querySelector('.comissao-funcionario').value;
        const percentual = item.querySelector('.comissao-percentual').value;
        if (funcionario_id && percentual) {
            comissoes.push({
                funcionario_id: parseInt(funcionario_id),
                percentual: parseFloat(percentual)
            });
        }
    });
    
    // Pegar valor sem formatação (campo type="number" retorna string numérica pura)
    const valorMensalRaw = document.getElementById('contrato-valor-mensal').value;
    const valorMensal = parseFloat(valorMensalRaw.replace(/[^\d.-]/g, '')) || 0;
    const quantidadeMeses = parseInt(document.getElementById('contrato-meses').value) || 1;
    const valorTotal = valorMensal * quantidadeMeses;
    
    console.log('💰 Valores coletados no salvar:');
    console.log('   📝 Valor Mensal (campo .value RAW):', valorMensalRaw);
    console.log('   💰 Valor Mensal (parseado):', valorMensal);
    console.log('   🔢 Qtd Meses (campo .value):', document.getElementById('contrato-meses').value);
    console.log('   🔢 Qtd Meses (parseado):', quantidadeMeses);
    console.log('   💵 Valor Total calculado:', valorTotal);
    
    // Recuperar numero do campo hidden (preservado do edit)
    const numero = document.getElementById('contrato-numero')?.value || undefined;
    console.log('   🔢 Numero (campo hidden):', numero);
    
    // Capturar descrição
    const campoDescricao = document.getElementById('contrato-descricao');
    console.log('   🔍 Campo descricao encontrado?', !!campoDescricao);
    console.log('   🔍 Campo descricao element:', campoDescricao);
    
    const descricao = campoDescricao?.value || '';
    console.log('   📝 Descrição (campo textarea):', descricao);
    console.log('   📝 Descrição length:', descricao.length);
    
    // Verificar se há múltiplos elementos com mesmo ID (BUG)
    const todosDescricao = document.querySelectorAll('#contrato-descricao');
    console.log('   ⚠️ Total de campos com ID contrato-descricao:', todosDescricao.length);
    if (todosDescricao.length > 1) {
        console.log('   🚨 ERRO: Múltiplos campos com mesmo ID!');
        todosDescricao.forEach((el, idx) => {
            console.log(`      [${idx}] value: "${el.value}"`);
        });
    }
    
    const data = {
        numero: numero,  // Preservar número no edit via campo hidden
        cliente_id: parseInt(document.getElementById('contrato-cliente').value),
        tipo: document.getElementById('contrato-tipo').value,
        nome: document.getElementById('contrato-nome').value,
        descricao: descricao,
        valor_mensal: valorMensal,
        quantidade_meses: quantidadeMeses,
        valor_total: valorTotal,
        horas_mensais: parseInt(document.getElementById('contrato-horas').value) || null,
        forma_pagamento: document.getElementById('contrato-pagamento').value,
        quantidade_parcelas: parseInt(document.getElementById('contrato-parcelas').value),
        data_contrato: document.getElementById('contrato-data').value,
        dia_pagamento: parseInt(document.getElementById('contrato-dia-pagamento').value) || null,
        dia_emissao_nf: parseInt(document.getElementById('contrato-dia-nf').value) || null,
        imposto: parseFloat(document.getElementById('contrato-imposto').value) || null,
        comissoes: comissoes
    };
    
    console.log('📦 Dados a enviar:', JSON.stringify(data, null, 2));
    
    try {
        const url = isEdit ? `/api/contratos/${id}` : '/api/contratos';
        const method = isEdit ? 'PUT' : 'POST';
        
        console.log('🌐 URL:', url);
        console.log('📤 Method:', method);
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        console.log('📡 Status da resposta:', response.status);
        
        let result;
        try {
            result = await response.json();
            console.log('📡 Resposta do servidor:', result);
        } catch (e) {
            console.error('❌ Erro ao parsear JSON:', e);
            const text = await response.text();
            console.error('📄 Resposta em texto:', text);
            throw new Error('Resposta inválida do servidor');
        }
        
        if (result.success || response.ok) {
            showToast(isEdit ? '✅ Contrato atualizado com sucesso!' : '✅ Contrato criado com sucesso!', 'success');
            closeModal();
            if (typeof loadContratos === 'function') loadContratos();
        } else {
            showToast('❌ Erro: ' + (result.error || 'Erro desconhecido'), 'error');
            console.error('❌ Detalhes do erro:', result);
        }
        
    } catch (error) {
        console.error('❌ Erro ao salvar contrato:', error);
        showToast('❌ Erro ao salvar contrato: ' + error.message, 'error');
    }
} // Fecha a função salvarContrato

window.openModalContrato = openModalContrato;
window.salvarContrato = salvarContrato;
window.atualizarCalculoContrato = atualizarCalculoContrato;
window.adicionarComissaoContrato = adicionarComissaoContrato;

// ========================================
// SESSÕES
// ========================================

async function openModalSessao(sessaoEdit = null) {
    console.log('📋 openModalSessao chamada', sessaoEdit ? 'MODO EDIÇÃO' : 'MODO CRIAÇÃO');
    
    // Carregar dependências
    if (!window.clientes || window.clientes.length === 0) {
        await loadClientes();
    }
    if (!window.contratos || window.contratos.length === 0) {
        await loadContratos();
    }
    if (!window.funcionarios || window.funcionarios.length === 0) {
        await loadFuncionariosRH();
    }
    if (!window.kits || window.kits.length === 0) {
        await loadKits();
    }
    
    const isEdit = sessaoEdit !== null;
    const titulo = isEdit ? 'Editar Sessão' : 'Nova Sessão';
    
    // Debug: Verificar dados carregados
    console.log('🔍 Dados carregados para modal:');
    console.log('  - Clientes:', window.clientes ? window.clientes.length : 0);
    console.log('  - Contratos:', window.contratos ? window.contratos.length : 0);
    console.log('  - Funcionários:', window.funcionarios ? window.funcionarios.length : 0);
    console.log('  - Kits:', window.kits ? window.kits.length : 0);
    
    if (window.funcionarios && window.funcionarios.length > 0) {
        console.log('  - Exemplo funcionário:', window.funcionarios[0]);
    }
    
    // Opções de clientes
    const opcoesClientes = window.clientes && window.clientes.length > 0
        ? window.clientes.map(c => {
            const selected = isEdit && sessaoEdit.cliente_id === c.id ? 'selected' : '';
            return `<option value="${c.id}" ${selected}>${c.razao_social || c.nome}</option>`;
        }).join('')
        : '<option value="">Nenhum cliente cadastrado</option>';
    
    // Opções de contratos
    const opcoesContratos = window.contratos && window.contratos.length > 0
        ? window.contratos.map(c => {
            const selected = isEdit && sessaoEdit.contrato_id === c.id ? 'selected' : '';
            return `<option value="${c.id}" ${selected}>${c.nome || c.numero}</option>`;
        }).join('')
        : '<option value="">Nenhum contrato cadastrado</option>';
    
    // Opções de funcionários
    const opcoesFuncionarios = window.funcionarios && window.funcionarios.length > 0
        ? window.funcionarios.map(f => `<option value="${f.id}">${f.nome}</option>`).join('')
        : '<option value="">Nenhum funcionário cadastrado</option>';
    
    // Checkboxes de kits
    const kitsDisponiveis = window.kits && window.kits.length > 0
        ? window.kits.map(k => {
            const checked = isEdit && sessaoEdit.equipamentos && sessaoEdit.equipamentos.includes(k.id) ? 'checked' : '';
            return `<label style="display: inline-block; margin-right: 15px; margin-bottom: 10px;">
                <input type="checkbox" class="kit-checkbox" value="${k.id}" ${checked}> ${k.nome}
            </label>`;
        }).join('')
        : '<p>Nenhum kit cadastrado</p>';
    
    const modal = createModal(titulo, `
        <form id="form-sessao" onsubmit="salvarSessao(event)" style="max-height: 85vh; overflow-y: auto;">
            <input type="hidden" id="sessao-id" value="${isEdit ? sessaoEdit.id : ''}">
            
            <!-- Linha 1: Cliente e Contrato -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div class="form-group">
                    <label>*Cliente:</label>
                    <select id="sessao-cliente" required>
                        <option value="">Selecione...</option>
                        ${opcoesClientes}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>*Contrato:</label>
                    <select id="sessao-contrato" required>
                        <option value="">Selecione...</option>
                        ${opcoesContratos}
                    </select>
                </div>
            </div>
            
            <!-- Linha 2: Data, Horário, Quantidade de Horas -->
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                <div class="form-group">
                    <label>*Data:</label>
                    <input type="date" id="sessao-data" required value="${isEdit && sessaoEdit.data ? sessaoEdit.data.split('T')[0] : ''}">
                </div>
                
                <div class="form-group">
                    <label>*Horário:</label>
                    <input type="text" id="sessao-horario" required value="${isEdit ? sessaoEdit.horario || '' : ''}" placeholder="14h às 18h">
                </div>
                
                <div class="form-group">
                    <label>Quantidade de Horas:</label>
                    <input type="number" id="sessao-horas" step="0.5" min="0" value="${isEdit ? sessaoEdit.quantidade_horas || '' : ''}" placeholder="4">
                </div>
            </div>
            
            <!-- Linha 3: Endereço -->
            <div class="form-group">
                <label>*Endereço:</label>
                <input type="text" id="sessao-endereco" required value="${isEdit ? sessaoEdit.endereco || '' : ''}" placeholder="R. Mourato Coelho, 1300 - Vl Madalena / São Paulo">
            </div>
            
            <!-- Linha 4: Tipo de Captação -->
            <div class="form-group">
                <label>*Tipo de Captação:</label>
                <div style="display: flex; gap: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                    <label><input type="checkbox" id="sessao-tipo-foto" ${isEdit && sessaoEdit.tipo_foto ? 'checked' : ''}> Foto</label>
                    <label><input type="checkbox" id="sessao-tipo-video" ${isEdit && sessaoEdit.tipo_video ? 'checked' : ''}> Vídeo</label>
                    <label><input type="checkbox" id="sessao-tipo-mobile" ${isEdit && sessaoEdit.tipo_mobile ? 'checked' : ''}> Mobile</label>
                </div>
            </div>
            
            <!-- Linha 5: Descrição -->
            <div class="form-group">
                <label>*Descrição da Sessão:</label>
                <textarea id="sessao-descricao" rows="3" required placeholder="Fotos dos coquetéis de carnaval com a linha nova de sabores da Monin.">${isEdit ? sessaoEdit.descricao || '' : ''}</textarea>
            </div>
            
            <!-- Linha 6: Tags -->
            <div class="form-group">
                <label>Tags:</label>
                <input type="text" id="sessao-tags" value="${isEdit ? sessaoEdit.tags || '' : ''}" placeholder="Redes sociais, press kit">
            </div>
            
            <!-- Linha 7: Prazo de Entrega -->
            <div class="form-group">
                <label>*Prazo de Entrega:</label>
                <input type="date" id="sessao-prazo" required value="${isEdit && sessaoEdit.prazo_entrega ? sessaoEdit.prazo_entrega.split('T')[0] : ''}">
            </div>
            
            <!-- Seção: Equipe -->
            <div class="form-group">
                <label style="font-size: 18px; font-weight: bold; color: #2c3e50; margin-top: 20px; border-bottom: 2px solid #3498db; padding-bottom: 5px;">Equipe</label>
                <div id="sessao-equipe-container" style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: #f9f9f9; margin-top: 10px;">
                    <div id="sessao-equipe-list"></div>
                    <button type="button" onclick="adicionarEquipeSessao()" class="btn btn-sm" style="margin-top: 10px; background: #3498db; color: white;">➕ Adicionar Membro</button>
                </div>
            </div>
            
            <!-- Seção: Responsáveis -->
            <div class="form-group">
                <label style="font-size: 18px; font-weight: bold; color: #2c3e50; margin-top: 20px; border-bottom: 2px solid #3498db; padding-bottom: 5px;">Responsáveis</label>
                <div id="sessao-responsaveis-container" style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: #f9f9f9; margin-top: 10px;">
                    <div id="sessao-responsaveis-list"></div>
                    <button type="button" onclick="adicionarResponsavelSessao()" class="btn btn-sm" style="margin-top: 10px; background: #3498db; color: white;">➕ Adicionar Responsável</button>
                </div>
            </div>
            
            <!-- Seção: Equipamentos -->
            <div class="form-group">
                <label style="font-size: 18px; font-weight: bold; color: #2c3e50; margin-top: 20px; border-bottom: 2px solid #3498db; padding-bottom: 5px;">Equipamentos</label>
                <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: #f9f9f9; margin-top: 10px;">
                    ${kitsDisponiveis}
                </div>
            </div>
            
            <!-- Seção: Equipamentos Alugados -->
            <div class="form-group">
                <label style="font-size: 18px; font-weight: bold; color: #2c3e50; margin-top: 20px; border-bottom: 2px solid #3498db; padding-bottom: 5px;">Equipamentos Alugados</label>
                <div id="sessao-equipamentos-alugados-container" style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: #f9f9f9; margin-top: 10px;">
                    <div id="sessao-equipamentos-alugados-list"></div>
                    <button type="button" onclick="adicionarEquipamentoAlugado()" class="btn btn-sm" style="margin-top: 10px; background: #3498db; color: white;">➕ Adicionar Equipamento</button>
                </div>
            </div>
            
            <!-- Seção: Custos Adicionais -->
            <div class="form-group">
                <label style="font-size: 18px; font-weight: bold; color: #2c3e50; margin-top: 20px; border-bottom: 2px solid #3498db; padding-bottom: 5px;">Custos Adicionais</label>
                <div id="sessao-custos-container" style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: #f9f9f9; margin-top: 10px;">
                    <div id="sessao-custos-list"></div>
                    <button type="button" onclick="adicionarCustoAdicional()" class="btn btn-sm" style="margin-top: 10px; background: #3498db; color: white;">➕ Adicionar Custo</button>
                </div>
            </div>
            
            <!-- Seção: Observações -->
            <div class="form-group">
                <label>Observações Adicionais:</label>
                <textarea id="sessao-observacoes" rows="3" placeholder="Observações gerais sobre a sessão...">${isEdit ? sessaoEdit.observacoes || '' : ''}</textarea>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px; position: sticky; bottom: 0; background: white; padding: 15px 0; border-top: 2px solid #eee;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Salvar Sessão</button>
            </div>
        </form>
    `);
    
    // Verificar e forçar ID após criar modal (CRÍTICO para evitar duplicação)
    setTimeout(() => {
        const sessaoIdField = document.getElementById('sessao-id');
        
        console.log('🔍 Verificação após criar modal:');
        console.log('   📝 Campo sessao-id existe?', !!sessaoIdField);
        console.log('   📝 Valor do campo ID:', sessaoIdField ? sessaoIdField.value : 'CAMPO NÃO ENCONTRADO');
        console.log('   📝 isEdit:', isEdit);
        console.log('   📝 sessaoEdit.id:', sessaoEdit ? sessaoEdit.id : 'N/A');
        
        // Se estiver editando, forçar o valor novamente (PREVINE DUPLICAÇÃO)
        if (isEdit && sessaoEdit) {
            if (sessaoIdField && sessaoEdit.id) {
                sessaoIdField.value = sessaoEdit.id;
                console.log('   ✅ ID forçado novamente para:', sessaoEdit.id);
            }
        }
    }, 50);
    
    // Preencher listas dinâmicas se estiver editando
    if (isEdit) {
        setTimeout(() => {
            if (sessaoEdit.equipe) {
                sessaoEdit.equipe.forEach(e => {
                    adicionarEquipeSessao(e);
                });
            }
            if (sessaoEdit.responsaveis) {
                sessaoEdit.responsaveis.forEach(r => {
                    adicionarResponsavelSessao(r);
                });
            }
            if (sessaoEdit.equipamentos_alugados) {
                sessaoEdit.equipamentos_alugados.forEach(ea => {
                    adicionarEquipamentoAlugado(ea);
                });
            }
            if (sessaoEdit.custos_adicionais) {
                sessaoEdit.custos_adicionais.forEach(ca => {
                    adicionarCustoAdicional(ca);
                });
            }
        }, 100);
    }
}

function adicionarEquipeSessao(dadosIniciais = null) {
    const container = document.getElementById('sessao-equipe-list');
    if (!container) return;
    
    const opcoesFuncionarios = window.funcionarios && window.funcionarios.length > 0
        ? window.funcionarios.map(f => {
            const selected = dadosIniciais && dadosIniciais.funcionario_id === f.id ? 'selected' : '';
            return `<option value="${f.id}" ${selected}>${f.nome}</option>`;
        }).join('')
        : '<option value="">Nenhum funcionário</option>';
    
    const div = document.createElement('div');
    div.className = 'equipe-item';
    div.style.cssText = 'display: grid; grid-template-columns: 2fr 1fr 1fr auto; gap: 10px; margin-bottom: 10px; align-items: center;';
    div.innerHTML = `
        <select class="equipe-funcionario" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            <option value="">Selecione...</option>
            ${opcoesFuncionarios}
        </select>
        <input type="text" class="equipe-funcao" placeholder="Fotógrafo" value="${dadosIniciais ? dadosIniciais.funcao || '' : ''}" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        <input type="number" class="equipe-pagamento" step="0.01" min="0" placeholder="1000.00" value="${dadosIniciais ? dadosIniciais.pagamento || '' : ''}" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        <button type="button" onclick="this.parentElement.remove()" class="btn btn-sm btn-danger" style="padding: 8px 12px;">🗑️</button>
    `;
    container.appendChild(div);
}

function adicionarResponsavelSessao(dadosIniciais = null) {
    const container = document.getElementById('sessao-responsaveis-list');
    if (!container) return;
    
    const opcoesFuncionarios = window.funcionarios && window.funcionarios.length > 0
        ? window.funcionarios.map(f => {
            const selected = dadosIniciais && dadosIniciais.funcionario_id === f.id ? 'selected' : '';
            return `<option value="${f.id}" ${selected}>${f.nome}</option>`;
        }).join('')
        : '<option value="">Nenhum funcionário</option>';
    
    const div = document.createElement('div');
    div.className = 'responsavel-item';
    div.style.cssText = 'display: grid; grid-template-columns: 2fr 1fr auto; gap: 10px; margin-bottom: 10px; align-items: center;';
    div.innerHTML = `
        <select class="responsavel-funcionario" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            <option value="">Selecione...</option>
            ${opcoesFuncionarios}
        </select>
        <input type="text" class="responsavel-funcao" placeholder="Captação" value="${dadosIniciais ? dadosIniciais.funcao || '' : ''}" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        <button type="button" onclick="this.parentElement.remove()" class="btn btn-sm btn-danger" style="padding: 8px 12px;">🗑️</button>
    `;
    container.appendChild(div);
}

function adicionarEquipamentoAlugado(dadosIniciais = null) {
    const container = document.getElementById('sessao-equipamentos-alugados-list');
    if (!container) return;
    
    const div = document.createElement('div');
    div.className = 'equipamento-alugado-item';
    div.style.cssText = 'display: grid; grid-template-columns: 2fr 1fr 1fr auto; gap: 10px; margin-bottom: 10px; align-items: center;';
    div.innerHTML = `
        <input type="text" class="eq-alugado-nome" placeholder="Lente Cânon RF 10-20mm" value="${dadosIniciais ? dadosIniciais.nome || '' : ''}" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        <input type="number" class="eq-alugado-valor" step="0.01" min="0" placeholder="300.00" value="${dadosIniciais ? dadosIniciais.valor || '' : ''}" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        <input type="text" class="eq-alugado-locadora" placeholder="Freshcam" value="${dadosIniciais ? dadosIniciais.locadora || '' : ''}" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        <button type="button" onclick="this.parentElement.remove()" class="btn btn-sm btn-danger" style="padding: 8px 12px;">🗑️</button>
    `;
    container.appendChild(div);
}

function adicionarCustoAdicional(dadosIniciais = null) {
    const container = document.getElementById('sessao-custos-list');
    if (!container) return;
    
    const div = document.createElement('div');
    div.className = 'custo-adicional-item';
    div.style.cssText = 'display: grid; grid-template-columns: 2fr 1fr 1fr auto; gap: 10px; margin-bottom: 10px; align-items: center;';
    div.innerHTML = `
        <input type="text" class="custo-descricao" placeholder="Estacionamento" value="${dadosIniciais ? dadosIniciais.descricao || '' : ''}" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        <input type="number" class="custo-valor" step="0.01" min="0" placeholder="65.00" value="${dadosIniciais ? dadosIniciais.valor || '' : ''}" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        <input type="text" class="custo-tipo" placeholder="Transporte" value="${dadosIniciais ? dadosIniciais.tipo || '' : ''}" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        <button type="button" onclick="this.parentElement.remove()" class="btn btn-sm btn-danger" style="padding: 8px 12px;">🗑️</button>
    `;
    container.appendChild(div);
}

async function salvarSessao(event) {
    event.preventDefault();
    
    console.log('\n💾 ========== SALVAR SESSÃO ==========');
    
    const id = document.getElementById('sessao-id').value;
    const isEdit = id && id.trim() !== '';
    
    console.log('🎯 Modo:', isEdit ? 'EDIÇÃO' : 'CRIAÇÃO');
    
    // Coletar equipe
    const equipe = [];
    document.querySelectorAll('.equipe-item').forEach(item => {
        const funcionario_id = item.querySelector('.equipe-funcionario').value;
        const funcao = item.querySelector('.equipe-funcao').value;
        const pagamento = parseFloat(item.querySelector('.equipe-pagamento').value) || 0;
        if (funcionario_id) {
            equipe.push({ funcionario_id: parseInt(funcionario_id), funcao, pagamento });
        }
    });
    
    // Coletar responsáveis
    const responsaveis = [];
    document.querySelectorAll('.responsavel-item').forEach(item => {
        const funcionario_id = item.querySelector('.responsavel-funcionario').value;
        const funcao = item.querySelector('.responsavel-funcao').value;
        if (funcionario_id) {
            responsaveis.push({ funcionario_id: parseInt(funcionario_id), funcao });
        }
    });
    
    // Coletar equipamentos selecionados
    const equipamentos = [];
    document.querySelectorAll('.kit-checkbox:checked').forEach(checkbox => {
        equipamentos.push(parseInt(checkbox.value));
    });
    
    // Coletar equipamentos alugados
    const equipamentos_alugados = [];
    document.querySelectorAll('.equipamento-alugado-item').forEach(item => {
        const nome = item.querySelector('.eq-alugado-nome').value;
        const valor = parseFloat(item.querySelector('.eq-alugado-valor').value) || 0;
        const locadora = item.querySelector('.eq-alugado-locadora').value;
        if (nome) {
            equipamentos_alugados.push({ nome, valor, locadora });
        }
    });
    
    // Coletar custos adicionais
    const custos_adicionais = [];
    document.querySelectorAll('.custo-adicional-item').forEach(item => {
        const descricao = item.querySelector('.custo-descricao').value;
        const valor = parseFloat(item.querySelector('.custo-valor').value) || 0;
        const tipo = item.querySelector('.custo-tipo').value;
        if (descricao) {
            custos_adicionais.push({ descricao, valor, tipo });
        }
    });
    
    const data = {
        cliente_id: parseInt(document.getElementById('sessao-cliente').value),
        contrato_id: parseInt(document.getElementById('sessao-contrato').value),
        data: document.getElementById('sessao-data').value,
        horario: document.getElementById('sessao-horario').value,
        quantidade_horas: parseFloat(document.getElementById('sessao-horas').value) || null,
        endereco: document.getElementById('sessao-endereco').value,
        tipo_foto: document.getElementById('sessao-tipo-foto').checked,
        tipo_video: document.getElementById('sessao-tipo-video').checked,
        tipo_mobile: document.getElementById('sessao-tipo-mobile').checked,
        descricao: document.getElementById('sessao-descricao').value,
        tags: document.getElementById('sessao-tags').value,
        prazo_entrega: document.getElementById('sessao-prazo').value,
        equipe: equipe,
        responsaveis: responsaveis,
        equipamentos: equipamentos,
        equipamentos_alugados: equipamentos_alugados,
        custos_adicionais: custos_adicionais,
        observacoes: document.getElementById('sessao-observacoes').value
    };
    
    console.log('📦 Dados a enviar:', JSON.stringify(data, null, 2));
    
    try {
        const url = isEdit ? `/api/sessoes/${id}` : '/api/sessoes';
        const method = isEdit ? 'PUT' : 'POST';
        
        console.log('🌐 URL:', url);
        console.log('📤 Method:', method);
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        console.log('📡 Status da resposta:', response.status);
        
        let result;
        try {
            result = await response.json();
            console.log('📡 Resposta do servidor:', result);
        } catch (e) {
            console.error('❌ Erro ao parsear JSON:', e);
            const text = await response.text();
            console.error('📄 Resposta em texto:', text);
            throw new Error('Resposta inválida do servidor');
        }
        
        if (result.success || response.ok) {
            showToast(isEdit ? '✅ Sessão atualizada com sucesso!' : '✅ Sessão criada com sucesso!', 'success');
            closeModal();
            if (typeof loadSessoes === 'function') loadSessoes();
        } else {
            showToast('❌ Erro: ' + (result.error || 'Erro desconhecido'), 'error');
            console.error('❌ Detalhes do erro:', result);
        }
        
    } catch (error) {
        console.error('❌ Erro ao salvar sessão:', error);
        showToast('❌ Erro ao salvar sessão: ' + error.message, 'error');
    }
}

window.openModalSessao = openModalSessao;
window.salvarSessao = salvarSessao;
window.adicionarEquipeSessao = adicionarEquipeSessao;
window.adicionarResponsavelSessao = adicionarResponsavelSessao;
window.adicionarEquipamentoAlugado = adicionarEquipamentoAlugado;
window.adicionarCustoAdicional = adicionarCustoAdicional;

// ========================================
// KITS DE EQUIPAMENTOS
// ========================================

/**
 * Abre modal para criar ou editar kit
 */
function openModalKit(kitEdit = null) {
    console.log('📦 openModalKit chamada', kitEdit ? 'MODO EDIÇÃO' : 'MODO CRIAÇÃO');
    
    const isEdit = kitEdit !== null;
    const titulo = isEdit ? 'Editar Kit' : 'Novo Kit';
    
    // Separar descrição e itens ao editar
    let descricao = '';
    let itens = '';
    
    if (isEdit && kitEdit.descricao) {
        const partes = kitEdit.descricao.split('\n\nItens incluídos:\n');
        descricao = partes[0] || '';
        itens = partes[1] || '';
        
        console.log('🔍 Separando descrição:', { original: kitEdit.descricao, descricao, itens });
    }
    
    const modal = createModal(titulo, `
        <form id="form-kit" novalidate style="max-height: 70vh; overflow-y: auto;">
            <input type="hidden" id="kit-id" name="kit-id" value="${isEdit ? kitEdit.id : ''}">
            
            <div class="form-group">
                <label>*Nome do Kit:</label>
                <input type="text" 
                    id="kit-nome" 
                    name="kit-nome"
                    value="${isEdit ? kitEdit.nome : ''}" 
                    placeholder="Ex: Kit Fotografia Básico"
                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            </div>
            
            <div class="form-group">
                <label>Descrição:</label>
                <textarea 
                    id="kit-descricao" 
                    name="kit-descricao"
                    rows="4"
                    placeholder="Descreva o que está incluso no kit..."
                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; resize: vertical;"
                >${isEdit ? descricao : ''}</textarea>
            </div>
            
            <div class="form-group">
                <label>Itens do Kit:</label>
                <textarea 
                    id="kit-itens" 
                    name="kit-itens"
                    rows="3"
                    placeholder="Liste os itens incluídos (ex: Câmera Canon, Tripé, Lentes 50mm...)"
                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; resize: vertical;"
                >${isEdit ? itens : ''}</textarea>
            </div>
            
            <div class="form-group">
                <label>Valor Total (R$):</label>
                <input type="number" 
                    id="kit-preco" 
                    name="kit-preco"
                    step="0.01"
                    min="0"
                    value="${isEdit ? (kitEdit.preco || 0) : 0}" 
                    placeholder="0.00"
                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px; justify-content: flex-end;">
                <button type="button" class="btn" onclick="closeModal()" 
                    style="background: #95a5a6; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">
                    Cancelar
                </button>
                <button type="submit" class="btn btn-primary" 
                    style="background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
                    ${isEdit ? 'Atualizar' : 'Criar'} Kit
                </button>
            </div>
        </form>
    `);
    
    // Registrar event listener DEPOIS que o DOM for atualizado
    setTimeout(() => {
        const form = document.getElementById('form-kit');
        if (form) {
            // Remover listeners antigos se existirem
            form.removeEventListener('submit', salvarKit);
            
            console.log('✅ Registrando event listener no formulário');
            form.addEventListener('submit', salvarKit, { once: false });
            
            // Verificar se não está sendo disparado imediatamente
            console.log('🔍 Formulário pronto. Aguardando preenchimento...');
        } else {
            console.error('❌ Formulário form-kit não encontrado!');
        }
    }, 100); // Aumentar delay para 100ms
}

/**
 * Salva kit (criar ou atualizar)
 */
async function salvarKit(event) {
    console.log('🎯 salvarKit INICIADA');
    console.log('   📍 event:', event);
    console.log('   📍 event.type:', event?.type);
    console.log('   📍 event.target:', event?.target);
    
    if (!event) {
        console.error('❌ Event é null!');
        return;
    }
    
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    
    // Prevenir dupla submissão
    const form = event.target;
    if (form.dataset.submitting === 'true') {
        console.log('⚠️ Já está processando, ignorando...');
        return;
    }
    form.dataset.submitting = 'true';
    
    const idInput = form.elements['kit-id'];
    const id = idInput?.value || '';
    const isEdit = id !== '' && id !== null && id !== undefined;
    
    console.log('🔑 ID capturado:', id, '| Modo:', isEdit ? 'EDIÇÃO' : 'CRIAÇÃO');
    
    // CAPTURAR VALORES PELO FORMULÁRIO (não por getElementById)
    const nomeInput = form.elements['kit-nome'];
    const descricaoInput = form.elements['kit-descricao'];
    const itensInput = form.elements['kit-itens'];
    const precoInput = form.elements['kit-preco'];
    
    console.log('🔍 DEBUG COMPLETO:');
    console.log('   1. nomeInput element:', nomeInput);
    console.log('   2. nomeInput.value:', nomeInput?.value);
    console.log('   3. descricaoInput element:', descricaoInput);
    console.log('   4. descricaoInput.value:', descricaoInput?.value);
    console.log('   5. itensInput.value:', itensInput?.value);
    console.log('   6. precoInput.value:', precoInput?.value);
    
    const dados = {
        nome: (nomeInput?.value || '').trim(),
        descricao: (descricaoInput?.value || '').trim(),
        itens: (itensInput?.value || '').trim(),
        preco: parseFloat(precoInput?.value || 0)
    };
    
    console.log('📦 DADOS COLETADOS:', dados);
    
    if (!dados.nome) {
        console.error('❌ VALIDAÇÃO FALHOU - nome está vazio');
        form.dataset.submitting = 'false';
        showToast('❌ Nome do kit é obrigatório', 'error');
        return;
    }
    
    try {
        console.log(isEdit ? '✏️ Atualizando kit...' : '➕ Criando kit...', dados);
        
        const url = isEdit ? `/api/kits/${id}` : '/api/kits';
        const method = isEdit ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        console.log('📡 Response status:', response.status);
        const result = await response.json();
        console.log('📦 Response data (RAW):', result);
        console.log('📦 Response data (JSON):', JSON.stringify(result, null, 2));
        
        if (response.ok && result.success) {
            showToast(isEdit ? '✅ Kit atualizado com sucesso!' : '✅ Kit criado com sucesso!', 'success');
            closeModal();
            if (typeof loadKitsTable === 'function') {
                loadKitsTable(); // Recarrega tabela
            }
        } else {
            form.dataset.submitting = 'false';
            const errorMsg = result.error || result.message || 'Erro desconhecido';
            showToast('❌ Erro: ' + errorMsg, 'error');
            console.error('❌ Detalhes do erro completo:', result);
            console.error('❌ Status HTTP:', response.status);
        }
        
    } catch (error) {
        form.dataset.submitting = 'false';
        console.error('❌ Erro ao salvar kit:', error);
        showToast('❌ Erro ao salvar kit: ' + error.message, 'error');
    }
}

window.openModalKit = openModalKit;
window.salvarKit = salvarKit;

console.log('✓ Modals.js v20251204lancamentos5 carregado com sucesso');