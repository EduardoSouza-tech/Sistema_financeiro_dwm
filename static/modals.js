// Modals - Sistema Financeiro
// ============================
console.log('%c ✓ MODALS.JS v20260119_SEM_NUM_DOCUMENTO CARREGADO ', 'background: #00ff00; color: black; font-size: 16px; font-weight: bold');

// === MODAL RECEITA ===
async function openModalReceita() {
    // Sempre recarregar categorias para pegar subcategorias atualizadas (se tiver permissão)
    const usuario = JSON.parse(sessionStorage.getItem('usuario') || '{}');
    const permissoes = usuario.permissoes || [];
    
    if (permissoes.includes('categorias_view') || permissoes.includes('lancamentos_view')) {
        console.log('Recarregando categorias...');
        await loadCategorias();
    }
    
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
        associacao: document.getElementById('receita-documento').value || '',
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
    console.log('🔍 CAMPO CRÍTICO - associacao:', data.associacao, 'tipo:', typeof data.associacao, 'length:', data.associacao?.length);
    
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
            
            // Verificar permissões antes de recarregar
            const usuario = JSON.parse(sessionStorage.getItem('usuario') || '{}');
            const permissoes = usuario.permissoes || [];
            
            if (typeof loadDashboard === 'function' && (permissoes.includes('dashboard') || permissoes.includes('relatorios_view'))) {
                loadDashboard();
            }
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
        console.log('🔍 DEBUG - Propriedades do lançamento:');
        console.log('   - id:', lancamento.id);
        console.log('   - pessoa:', lancamento.pessoa);
        console.log('   - categoria:', lancamento.categoria);
        console.log('   - subcategoria:', lancamento.subcategoria);
        console.log('   - data_vencimento:', lancamento.data_vencimento);
        console.log('   - associacao:', lancamento.associacao);
        console.log('   - numero_documento:', lancamento.numero_documento);
        console.log('   - descricao:', lancamento.descricao);
        console.log('   - valor:', lancamento.valor);
        console.log('   - observacoes:', lancamento.observacoes);
        
        if (lancamento) {
            console.log('🎨 Abrindo modal para edição...');
            // Preencher o modal com os dados
            await openModalReceita();
            
            console.log('📝 Preenchendo campo receita-id com:', lancamento.id);
            document.getElementById('receita-id').value = lancamento.id;
            console.log('✅ Campo receita-id preenchido. Valor atual:', document.getElementById('receita-id').value);
            
            console.log('📝 Preenchendo receita-cliente com:', lancamento.pessoa || '(vazio)');
            document.getElementById('receita-cliente').value = lancamento.pessoa || '';
            console.log('✅ receita-cliente preenchido:', document.getElementById('receita-cliente').value);
            
            console.log('📝 Preenchendo receita-categoria com:', lancamento.categoria || '(vazio)');
            document.getElementById('receita-categoria').value = lancamento.categoria || '';
            console.log('✅ receita-categoria preenchido:', document.getElementById('receita-categoria').value);
            
            // Aguardar subcategorias carregarem
            console.log('🔄 Atualizando subcategorias...');
            await atualizarSubcategoriasReceita();
            console.log('✅ Subcategorias atualizadas');
            
            console.log('📝 Preenchendo receita-subcategoria com:', lancamento.subcategoria || '(vazio)');
            document.getElementById('receita-subcategoria').value = lancamento.subcategoria || '';
            console.log('✅ receita-subcategoria preenchido:', document.getElementById('receita-subcategoria').value);
            
            const dataVencimento = lancamento.data_vencimento ? lancamento.data_vencimento.split('T')[0] : '';
            console.log('📝 Preenchendo receita-vencimento com:', dataVencimento || '(vazio)');
            document.getElementById('receita-vencimento').value = dataVencimento;
            console.log('✅ receita-vencimento preenchido:', document.getElementById('receita-vencimento').value);
            
            const documento = lancamento.associacao || lancamento.numero_documento || '';
            console.log('📝 Preenchendo receita-documento com:', documento || '(vazio)');
            document.getElementById('receita-documento').value = documento;
            console.log('✅ receita-documento preenchido:', document.getElementById('receita-documento').value);
            
            console.log('📝 Preenchendo receita-descricao com:', lancamento.descricao || '(vazio)');
            document.getElementById('receita-descricao').value = lancamento.descricao || '';
            console.log('✅ receita-descricao preenchido:', document.getElementById('receita-descricao').value);
            
            console.log('📝 Preenchendo receita-valor com:', lancamento.valor || '(vazio)');
            document.getElementById('receita-valor').value = lancamento.valor || '';
            console.log('✅ receita-valor preenchido:', document.getElementById('receita-valor').value);
            
            console.log('📝 Preenchendo receita-observacoes com:', lancamento.observacoes || '(vazio)');
            document.getElementById('receita-observacoes').value = lancamento.observacoes || '';
            console.log('✅ receita-observacoes preenchido:', document.getElementById('receita-observacoes').value);
            
            console.log('🎯 Modal preenchido completamente');
            console.log('🔍 Verificação final:');
            console.log('   - receita-id:', document.getElementById('receita-id').value);
            console.log('   - receita-cliente:', document.getElementById('receita-cliente').value);
            console.log('   - receita-categoria:', document.getElementById('receita-categoria').value);
            console.log('   - receita-subcategoria:', document.getElementById('receita-subcategoria').value);
            console.log('   - receita-vencimento:', document.getElementById('receita-vencimento').value);
            console.log('   - receita-documento:', document.getElementById('receita-documento').value);
            console.log('   - receita-descricao:', document.getElementById('receita-descricao').value);
            console.log('   - receita-valor:', document.getElementById('receita-valor').value);
            console.log('   - receita-observacoes:', document.getElementById('receita-observacoes').value);
            console.log('========== FIM EDITAR RECEITA ==========\n');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar receita para edição:', error);
        showToast('Erro ao carregar receita', 'error');
    }
}

// === MODAL DESPESA ===
async function openModalDespesa() {
    // Sempre recarregar categorias para pegar subcategorias atualizadas (se tiver permissão)
    const usuario = JSON.parse(sessionStorage.getItem('usuario') || '{}');
    const permissoes = usuario.permissoes || [];
    
    if (permissoes.includes('categorias_view') || permissoes.includes('lancamentos_view')) {
        console.log('Recarregando categorias...');
        await loadCategorias();
    }
    
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
        associacao: document.getElementById('despesa-documento').value || '',
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
    console.log('🔍 CAMPO CRÍTICO - associacao:', data.associacao, 'tipo:', typeof data.associacao, 'length:', data.associacao?.length);
    
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
            
            // Verificar permissões antes de recarregar
            const usuario = JSON.parse(sessionStorage.getItem('usuario') || '{}');
            const permissoes = usuario.permissoes || [];
            
            if (typeof loadDashboard === 'function' && (permissoes.includes('dashboard') || permissoes.includes('relatorios_view'))) {
                loadDashboard();
            }
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
        console.log('🔍 DEBUG - Propriedades do lançamento:');
        console.log('   - id:', lancamento.id);
        console.log('   - pessoa:', lancamento.pessoa);
        console.log('   - categoria:', lancamento.categoria);
        console.log('   - subcategoria:', lancamento.subcategoria);
        console.log('   - data_vencimento:', lancamento.data_vencimento);
        console.log('   - associacao:', lancamento.associacao);
        console.log('   - numero_documento:', lancamento.numero_documento);
        console.log('   - descricao:', lancamento.descricao);
        console.log('   - valor:', lancamento.valor);
        console.log('   - observacoes:', lancamento.observacoes);
        
        if (lancamento) {
            console.log('🎨 Abrindo modal para edição...');
            // Preencher o modal com os dados
            await openModalDespesa();
            
            console.log('📝 Preenchendo campo despesa-id com:', lancamento.id);
            document.getElementById('despesa-id').value = lancamento.id;
            console.log('✅ Campo despesa-id preenchido. Valor atual:', document.getElementById('despesa-id').value);
            
            console.log('📝 Preenchendo despesa-fornecedor com:', lancamento.pessoa || '(vazio)');
            document.getElementById('despesa-fornecedor').value = lancamento.pessoa || '';
            console.log('✅ despesa-fornecedor preenchido:', document.getElementById('despesa-fornecedor').value);
            
            console.log('📝 Preenchendo despesa-categoria com:', lancamento.categoria || '(vazio)');
            document.getElementById('despesa-categoria').value = lancamento.categoria || '';
            console.log('✅ despesa-categoria preenchido:', document.getElementById('despesa-categoria').value);
            
            // Aguardar subcategorias carregarem
            console.log('🔄 Atualizando subcategorias...');
            await atualizarSubcategoriasDespesa();
            console.log('✅ Subcategorias atualizadas');
            
            console.log('📝 Preenchendo despesa-subcategoria com:', lancamento.subcategoria || '(vazio)');
            document.getElementById('despesa-subcategoria').value = lancamento.subcategoria || '';
            console.log('✅ despesa-subcategoria preenchido:', document.getElementById('despesa-subcategoria').value);
            
            const dataVencimento = lancamento.data_vencimento ? lancamento.data_vencimento.split('T')[0] : '';
            console.log('📝 Preenchendo despesa-vencimento com:', dataVencimento || '(vazio)');
            document.getElementById('despesa-vencimento').value = dataVencimento;
            console.log('✅ despesa-vencimento preenchido:', document.getElementById('despesa-vencimento').value);
            
            const documento = lancamento.associacao || lancamento.numero_documento || '';
            console.log('📝 Preenchendo despesa-documento com:', documento || '(vazio)');
            document.getElementById('despesa-documento').value = documento;
            console.log('✅ despesa-documento preenchido:', document.getElementById('despesa-documento').value);
            
            console.log('📝 Preenchendo despesa-descricao com:', lancamento.descricao || '(vazio)');
            document.getElementById('despesa-descricao').value = lancamento.descricao || '';
            console.log('✅ despesa-descricao preenchido:', document.getElementById('despesa-descricao').value);
            
            console.log('📝 Preenchendo despesa-valor com:', lancamento.valor || '(vazio)');
            document.getElementById('despesa-valor').value = lancamento.valor || '';
            console.log('✅ despesa-valor preenchido:', document.getElementById('despesa-valor').value);
            
            console.log('📝 Preenchendo despesa-observacoes com:', lancamento.observacoes || '(vazio)');
            document.getElementById('despesa-observacoes').value = lancamento.observacoes || '';
            console.log('✅ despesa-observacoes preenchido:', document.getElementById('despesa-observacoes').value);
            
            console.log('🎯 Modal preenchido completamente');
            console.log('🔍 Verificação final:');
            console.log('   - despesa-id:', document.getElementById('despesa-id').value);
            console.log('   - despesa-fornecedor:', document.getElementById('despesa-fornecedor').value);
            console.log('   - despesa-categoria:', document.getElementById('despesa-categoria').value);
            console.log('   - despesa-subcategoria:', document.getElementById('despesa-subcategoria').value);
            console.log('   - despesa-vencimento:', document.getElementById('despesa-vencimento').value);
            console.log('   - despesa-documento:', document.getElementById('despesa-documento').value);
            console.log('   - despesa-descricao:', document.getElementById('despesa-descricao').value);
            console.log('   - despesa-valor:', document.getElementById('despesa-valor').value);
            console.log('   - despesa-observacoes:', document.getElementById('despesa-observacoes').value);
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

async function salvarContaBancaria(event) {
    if (event && event.preventDefault) event.preventDefault();
    
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
            
            // Verificar permissões antes de recarregar
            const usuario = JSON.parse(sessionStorage.getItem('usuario') || '{}');
            const permissoes = usuario.permissoes || [];
            
            if (typeof loadContasBancarias === 'function' && (permissoes.includes('contas_view') || permissoes.includes('lancamentos_view'))) {
                loadContasBancarias();
            }
            if (typeof loadContas === 'function' && (permissoes.includes('contas_view') || permissoes.includes('lancamentos_view'))) {
                loadContas();
            }
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
            
            // Verificar permissões antes de recarregar
            const usuario = JSON.parse(sessionStorage.getItem('usuario') || '{}');
            const permissoes = usuario.permissoes || [];
            
            if (typeof loadCategorias === 'function' && (permissoes.includes('categorias_view') || permissoes.includes('lancamentos_view'))) {
                await loadCategorias();
                console.log('✅ Lista de categorias recarregada!');
            } else {
                console.error('❌ Função loadCategorias não encontrada ou sem permissão!');
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
    const escapeHtml = (str) => (str || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    
    // 📝 Extrair TODOS os valores do cliente (com fallbacks)
    const nomeOriginal = isEdit ? (clienteEdit.razao_social || clienteEdit.nome || '') : '';
    const razaoSocial = isEdit ? (clienteEdit.razao_social || clienteEdit.nome || '') : '';
    const nomeFantasia = isEdit ? (clienteEdit.nome_fantasia || clienteEdit.nome || '') : '';
    const cnpj = isEdit ? (clienteEdit.cnpj || clienteEdit.cpf_cnpj || clienteEdit.documento || '') : '';
    const ie = isEdit ? (clienteEdit.ie || clienteEdit.inscricao_estadual || '') : '';
    const im = isEdit ? (clienteEdit.im || clienteEdit.inscricao_municipal || '') : '';
    const cep = isEdit ? (clienteEdit.cep || '') : '';
    const rua = isEdit ? (clienteEdit.logradouro || clienteEdit.rua || '') : '';
    const numero = isEdit ? (clienteEdit.numero || '') : '';
    const complemento = isEdit ? (clienteEdit.complemento || '') : '';
    const bairro = isEdit ? (clienteEdit.bairro || '') : '';
    const cidade = isEdit ? (clienteEdit.cidade || '') : '';
    const estado = isEdit ? (clienteEdit.estado || clienteEdit.uf || '') : '';
    const telefone = isEdit ? (clienteEdit.telefone || clienteEdit.contato || '') : '';
    const email = isEdit ? (clienteEdit.email || '') : '';
    
    const modal = createModal(titulo, `
        <form id="form-cliente" onsubmit="salvarCliente(event)">
            <input type="hidden" id="cliente-edit-mode" value="${isEdit}">
            <input type="hidden" id="cliente-nome-original" value="${escapeHtml(nomeOriginal)}">
            
            <div class="form-group">
                <label>*CNPJ:</label>
                <input type="text" id="cliente-cnpj" value="${escapeHtml(cnpj)}" required placeholder="00.000.000/0000-00" onblur="buscarDadosCNPJ()">
                <small style="color: #7f8c8d; font-size: 11px;">Digite o CNPJ para buscar dados automaticamente</small>
            </div>
            
            <div class="form-group">
                <label>*Razão Social:</label>
                <input type="text" id="cliente-razao" value="${escapeHtml(razaoSocial)}" required>
            </div>
            
            <div class="form-group">
                <label>*Nome Fantasia:</label>
                <input type="text" id="cliente-fantasia" value="${escapeHtml(nomeFantasia)}" required>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Inscrição Estadual:</label>
                    <input type="text" id="cliente-ie" value="${escapeHtml(ie)}">
                </div>
                
                <div class="form-group">
                    <label>Inscrição Municipal:</label>
                    <input type="text" id="cliente-im" value="${escapeHtml(im)}">
                </div>
            </div>
            
            <hr style="margin: 20px 0; border: none; border-top: 2px solid #ecf0f1;">
            <h3 style="color: #2c3e50; margin-bottom: 15px;">Endereço</h3>
            
            <div class="form-group">
                <label>CEP:</label>
                <input type="text" id="cliente-cep" value="${escapeHtml(cep)}" placeholder="00000-000" onblur="buscarCepCliente()">
            </div>
            
            <div class="form-group">
                <label>Rua/Avenida:</label>
                <input type="text" id="cliente-rua" value="${escapeHtml(rua)}">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Número:</label>
                    <input type="text" id="cliente-numero" value="${escapeHtml(numero)}">
                </div>
                
                <div class="form-group">
                    <label>Complemento:</label>
                    <input type="text" id="cliente-complemento" value="${escapeHtml(complemento)}">
                </div>
            </div>
            
            <div class="form-group">
                <label>Bairro:</label>
                <input type="text" id="cliente-bairro" value="${escapeHtml(bairro)}">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Cidade:</label>
                    <input type="text" id="cliente-cidade" value="${escapeHtml(cidade)}">
                </div>
                
                <div class="form-group">
                    <label>Estado:</label>
                    <select id="cliente-estado">
                        <option value="">Selecione...</option>
                        <option value="AC" ${estado === 'AC' ? 'selected' : ''}>AC</option>
                        <option value="AL" ${estado === 'AL' ? 'selected' : ''}>AL</option>
                        <option value="AP" ${estado === 'AP' ? 'selected' : ''}>AP</option>
                        <option value="AM" ${estado === 'AM' ? 'selected' : ''}>AM</option>
                        <option value="BA" ${estado === 'BA' ? 'selected' : ''}>BA</option>
                        <option value="CE" ${estado === 'CE' ? 'selected' : ''}>CE</option>
                        <option value="DF" ${estado === 'DF' ? 'selected' : ''}>DF</option>
                        <option value="ES" ${estado === 'ES' ? 'selected' : ''}>ES</option>
                        <option value="GO" ${estado === 'GO' ? 'selected' : ''}>GO</option>
                        <option value="MA" ${estado === 'MA' ? 'selected' : ''}>MA</option>
                        <option value="MT" ${estado === 'MT' ? 'selected' : ''}>MT</option>
                        <option value="MS" ${estado === 'MS' ? 'selected' : ''}>MS</option>
                        <option value="MG" ${estado === 'MG' ? 'selected' : ''}>MG</option>
                        <option value="PA" ${estado === 'PA' ? 'selected' : ''}>PA</option>
                        <option value="PB" ${estado === 'PB' ? 'selected' : ''}>PB</option>
                        <option value="PR" ${estado === 'PR' ? 'selected' : ''}>PR</option>
                        <option value="PE" ${estado === 'PE' ? 'selected' : ''}>PE</option>
                        <option value="PI" ${estado === 'PI' ? 'selected' : ''}>PI</option>
                        <option value="RJ" ${estado === 'RJ' ? 'selected' : ''}>RJ</option>
                        <option value="RN" ${estado === 'RN' ? 'selected' : ''}>RN</option>
                        <option value="RS" ${estado === 'RS' ? 'selected' : ''}>RS</option>
                        <option value="RO" ${estado === 'RO' ? 'selected' : ''}>RO</option>
                        <option value="RR" ${estado === 'RR' ? 'selected' : ''}>RR</option>
                        <option value="SC" ${estado === 'SC' ? 'selected' : ''}>SC</option>
                        <option value="SP" ${estado === 'SP' ? 'selected' : ''}>SP</option>
                        <option value="SE" ${estado === 'SE' ? 'selected' : ''}>SE</option>
                        <option value="TO" ${estado === 'TO' ? 'selected' : ''}>TO</option>
                    </select>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Telefone:</label>
                    <input type="text" id="cliente-telefone" value="${escapeHtml(telefone)}" placeholder="(00) 00000-0000">
                </div>
                
                <div class="form-group">
                    <label>E-mail:</label>
                    <input type="email" id="cliente-email" value="${escapeHtml(email)}">
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Salvar</button>
            </div>
        </form>
    `);
    
    // ✅ Todos os campos já estão preenchidos no HTML acima
    // Não precisa mais do setTimeout - dados já estão injetados
    if (isEdit) {
        console.log('✅ Modal de edição criado com todos os dados pré-preenchidos');
    }
}

async function buscarCepCliente() {
    const inputCep = document.getElementById('cliente-cep');
    const cep = inputCep.value.replace(/\D/g, '');
    
    // Validar tamanho do CEP
    if (cep.length !== 8) {
        if (cep.length > 0) {
            showToast('CEP deve conter 8 dígitos', 'warning');
        }
        return;
    }
    
    // 🔄 Mostrar loading no campo CEP
    const originalValue = inputCep.value;
    const originalBg = inputCep.style.background;
    inputCep.style.background = '#fff3cd';
    inputCep.disabled = true;
    inputCep.value = 'Buscando...';
    
    try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        
        if (!response.ok) {
            throw new Error('Erro ao consultar ViaCEP');
        }
        
        const data = await response.json();
        
        if (data.erro) {
            showToast('❌ CEP não encontrado', 'error');
            inputCep.value = originalValue;
        } else {
            // ✅ Preencher campos com dados do ViaCEP
            document.getElementById('cliente-rua').value = (data.logradouro || '').toUpperCase();
            document.getElementById('cliente-bairro').value = (data.bairro || '').toUpperCase();
            document.getElementById('cliente-cidade').value = (data.localidade || '').toUpperCase();
            document.getElementById('cliente-estado').value = data.uf || '';
            
            // Formatar CEP com hífen
            inputCep.value = `${cep.substr(0,5)}-${cep.substr(5)}`;
            
            // Focar no campo número (geralmente não vem do CEP)
            setTimeout(() => {
                document.getElementById('cliente-numero').focus();
            }, 100);
            
            showToast('✅ Endereço preenchido automaticamente!', 'success');
        }
    } catch (error) {
        console.error('Erro ao buscar CEP:', error);
        showToast('⚠️ Erro ao buscar CEP. Tente novamente.', 'error');
        inputCep.value = originalValue;
    } finally {
        // Restaurar estado do input
        inputCep.style.background = originalBg;
        inputCep.disabled = false;
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
        cpf_cnpj: document.getElementById('cliente-cnpj').value,
        documento: document.getElementById('cliente-cnpj').value,
        ie: document.getElementById('cliente-ie').value,
        im: document.getElementById('cliente-im').value,
        // 🌐 PARTE 7: Campos estruturados de endereço
        cep: document.getElementById('cliente-cep').value,
        logradouro: document.getElementById('cliente-rua').value,
        numero: document.getElementById('cliente-numero').value,
        complemento: document.getElementById('cliente-complemento').value,
        bairro: document.getElementById('cliente-bairro').value,
        cidade: document.getElementById('cliente-cidade').value,
        estado: document.getElementById('cliente-estado').value,
        // Campos de contato
        telefone: document.getElementById('cliente-telefone').value,
        contato: document.getElementById('cliente-telefone').value,
        email: document.getElementById('cliente-email').value.toLowerCase(),
        // Campo legado (para retrocompatibilidade)
        endereco: `${document.getElementById('cliente-rua').value}, ${document.getElementById('cliente-numero').value}`,
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
    }
    
    // Escapar HTML para valores de atributos
    const escapeHtml = (str) => (str || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    
    // 📝 Extrair TODOS os valores do fornecedor (com fallbacks)
    const nomeOriginal = isEdit ? (fornecedorEdit.razao_social || fornecedorEdit.nome || '') : '';
    const razaoSocial = isEdit ? (fornecedorEdit.razao_social || fornecedorEdit.nome || '') : '';
    const nomeFantasia = isEdit ? (fornecedorEdit.nome_fantasia || fornecedorEdit.nome || '') : '';
    const cnpj = isEdit ? (fornecedorEdit.cnpj || fornecedorEdit.cpf_cnpj || fornecedorEdit.documento || '') : '';
    const ie = isEdit ? (fornecedorEdit.ie || fornecedorEdit.inscricao_estadual || '') : '';
    const im = isEdit ? (fornecedorEdit.im || fornecedorEdit.inscricao_municipal || '') : '';
    const cep = isEdit ? (fornecedorEdit.cep || '') : '';
    const rua = isEdit ? (fornecedorEdit.logradouro || fornecedorEdit.rua || fornecedorEdit.endereco || '') : '';
    const numero = isEdit ? (fornecedorEdit.numero || '') : '';
    const complemento = isEdit ? (fornecedorEdit.complemento || '') : '';
    const bairro = isEdit ? (fornecedorEdit.bairro || '') : '';
    const cidade = isEdit ? (fornecedorEdit.cidade || '') : '';
    const estado = isEdit ? (fornecedorEdit.estado || fornecedorEdit.uf || '') : '';
    const telefone = isEdit ? (fornecedorEdit.telefone || fornecedorEdit.contato || '') : '';
    const email = isEdit ? (fornecedorEdit.email || '') : '';
    
    const modal = createModal(titulo, `
        <form id="form-fornecedor" onsubmit="salvarFornecedor(event)">
            <input type="hidden" id="fornecedor-edit-mode" value="${isEdit}">
            <input type="hidden" id="fornecedor-nome-original" value="${escapeHtml(nomeOriginal)}">
            
            <div class="form-group">
                <label>*CNPJ:</label>
                <input type="text" id="fornecedor-cnpj" value="${escapeHtml(cnpj)}" required placeholder="00.000.000/0000-00" onblur="buscarDadosCNPJFornecedor()">
                <small style="color: #7f8c8d; font-size: 11px;">Digite o CNPJ para buscar dados automaticamente</small>
            </div>
            
            <div class="form-group">
                <label>*Razão Social:</label>
                <input type="text" id="fornecedor-razao" value="${escapeHtml(razaoSocial)}" required>
            </div>
            
            <div class="form-group">
                <label>*Nome Fantasia:</label>
                <input type="text" id="fornecedor-fantasia" value="${escapeHtml(nomeFantasia)}" required>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Inscrição Estadual:</label>
                    <input type="text" id="fornecedor-ie" value="${escapeHtml(ie)}">
                </div>
                
                <div class="form-group">
                    <label>Inscrição Municipal:</label>
                    <input type="text" id="fornecedor-im" value="${escapeHtml(im)}">
                </div>
            </div>
            
            <hr style="margin: 20px 0; border: none; border-top: 2px solid #ecf0f1;">
            <h3 style="color: #2c3e50; margin-bottom: 15px;">Endereço</h3>
            
            <div class="form-group">
                <label>CEP:</label>
                <input type="text" id="fornecedor-cep" value="${escapeHtml(cep)}" placeholder="00000-000" onblur="buscarCepFornecedor()">
            </div>
            
            <div class="form-group">
                <label>Rua/Avenida:</label>
                <input type="text" id="fornecedor-rua" value="${escapeHtml(rua)}">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Número:</label>
                    <input type="text" id="fornecedor-numero" value="${escapeHtml(numero)}">
                </div>
                
                <div class="form-group">
                    <label>Complemento:</label>
                    <input type="text" id="fornecedor-complemento" value="${escapeHtml(complemento)}">
                </div>
            </div>
            
            <div class="form-group">
                <label>Bairro:</label>
                <input type="text" id="fornecedor-bairro" value="${escapeHtml(bairro)}">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Cidade:</label>
                    <input type="text" id="fornecedor-cidade" value="${escapeHtml(cidade)}">
                </div>
                
                <div class="form-group">
                    <label>Estado:</label>
                    <select id="fornecedor-estado">
                        <option value="">Selecione...</option>
                        <option value="AC" ${estado === 'AC' ? 'selected' : ''}>AC</option>
                        <option value="AL" ${estado === 'AL' ? 'selected' : ''}>AL</option>
                        <option value="AP" ${estado === 'AP' ? 'selected' : ''}>AP</option>
                        <option value="AM" ${estado === 'AM' ? 'selected' : ''}>AM</option>
                        <option value="BA" ${estado === 'BA' ? 'selected' : ''}>BA</option>
                        <option value="CE" ${estado === 'CE' ? 'selected' : ''}>CE</option>
                        <option value="DF" ${estado === 'DF' ? 'selected' : ''}>DF</option>
                        <option value="ES" ${estado === 'ES' ? 'selected' : ''}>ES</option>
                        <option value="GO" ${estado === 'GO' ? 'selected' : ''}>GO</option>
                        <option value="MA" ${estado === 'MA' ? 'selected' : ''}>MA</option>
                        <option value="MT" ${estado === 'MT' ? 'selected' : ''}>MT</option>
                        <option value="MS" ${estado === 'MS' ? 'selected' : ''}>MS</option>
                        <option value="MG" ${estado === 'MG' ? 'selected' : ''}>MG</option>
                        <option value="PA" ${estado === 'PA' ? 'selected' : ''}>PA</option>
                        <option value="PB" ${estado === 'PB' ? 'selected' : ''}>PB</option>
                        <option value="PR" ${estado === 'PR' ? 'selected' : ''}>PR</option>
                        <option value="PE" ${estado === 'PE' ? 'selected' : ''}>PE</option>
                        <option value="PI" ${estado === 'PI' ? 'selected' : ''}>PI</option>
                        <option value="RJ" ${estado === 'RJ' ? 'selected' : ''}>RJ</option>
                        <option value="RN" ${estado === 'RN' ? 'selected' : ''}>RN</option>
                        <option value="RS" ${estado === 'RS' ? 'selected' : ''}>RS</option>
                        <option value="RO" ${estado === 'RO' ? 'selected' : ''}>RO</option>
                        <option value="RR" ${estado === 'RR' ? 'selected' : ''}>RR</option>
                        <option value="SC" ${estado === 'SC' ? 'selected' : ''}>SC</option>
                        <option value="SP" ${estado === 'SP' ? 'selected' : ''}>SP</option>
                        <option value="SE" ${estado === 'SE' ? 'selected' : ''}>SE</option>
                        <option value="TO" ${estado === 'TO' ? 'selected' : ''}>TO</option>
                    </select>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Telefone:</label>
                    <input type="text" id="fornecedor-telefone" value="${escapeHtml(telefone)}" placeholder="(00) 00000-0000">
                </div>
                
                <div class="form-group">
                    <label>E-mail:</label>
                    <input type="email" id="fornecedor-email" value="${escapeHtml(email)}">
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Salvar</button>
            </div>
        </form>
    `);
    
    // ✅ Todos os campos já estão preenchidos no HTML acima
    // Não precisa mais do setTimeout - dados já estão injetados
    if (isEdit) {
        console.log('✅ Modal de edição de fornecedor criado com todos os dados pré-preenchidos');
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
window.salvarContaBancaria = salvarContaBancaria;
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
            
            // Verificar permissões antes de recarregar
            const usuario = JSON.parse(sessionStorage.getItem('usuario') || '{}');
            const permissoes = usuario.permissoes || [];
            
            if (typeof loadContasBancarias === 'function' && (permissoes.includes('contas_view') || permissoes.includes('lancamentos_view'))) {
                loadContasBancarias();
            }
            if (typeof loadFluxoCaixa === 'function' && (permissoes.includes('relatorios_view') || permissoes.includes('lancamentos_view'))) {
                loadFluxoCaixa();
            }
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
                    <select id="contrato-tipo" required onchange="alterarTipoContrato()">
                        <option value="Mensal" ${isEdit && contratoEdit.tipo === 'Mensal' ? 'selected' : ''}>Mensal</option>
                        <option value="Único" ${isEdit && contratoEdit.tipo === 'Único' ? 'selected' : ''}>Único</option>
                        <option value="Pacote" ${isEdit && contratoEdit.tipo === 'Pacote' ? 'selected' : ''}>Pacote</option>
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
            
            ${isEdit && contratoEdit.controle_horas_ativo ? `
            <!-- Controle de Horas (somente em edição) -->
            <div class="form-group" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white;">
                <h4 style="margin: 0 0 15px 0; font-size: 16px; font-weight: 600;">⏱️ Controle de Horas</h4>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">
                    <div>
                        <small style="opacity: 0.9;">Total Contratado</small>
                        <div style="font-size: 24px; font-weight: bold;">${(contratoEdit.horas_totais || 0).toFixed(1)}h</div>
                    </div>
                    <div>
                        <small style="opacity: 0.9;">Horas Utilizadas</small>
                        <div style="font-size: 24px; font-weight: bold;">${(contratoEdit.horas_utilizadas || 0).toFixed(1)}h</div>
                    </div>
                    <div>
                        <small style="opacity: 0.9;">Horas Restantes</small>
                        <div style="font-size: 24px; font-weight: bold; color: ${(contratoEdit.horas_restantes || 0) > 0 ? '#4ade80' : '#fbbf24'};">${(contratoEdit.horas_restantes || 0).toFixed(1)}h</div>
                    </div>
                    <div>
                        <small style="opacity: 0.9;">Horas Extras</small>
                        <div style="font-size: 24px; font-weight: bold; color: ${(contratoEdit.horas_extras || 0) > 0 ? '#f87171' : 'white'};">${(contratoEdit.horas_extras || 0).toFixed(1)}h</div>
                    </div>
                </div>
                
                <!-- Barra de progresso -->
                <div style="margin-top: 15px;">
                    <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 5px;">
                        <span>Progresso</span>
                        <span>${(contratoEdit.percentual_utilizado || 0).toFixed(1)}%</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.3); height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background: ${(contratoEdit.percentual_utilizado || 0) > 90 ? '#f87171' : '#4ade80'}; height: 100%; width: ${Math.min((contratoEdit.percentual_utilizado || 0), 100)}%; transition: width 0.3s;"></div>
                    </div>
                </div>
            </div>
            ` : ''}
            
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
        
        // 🔄 Ajustar campos do formulário baseado no tipo (especialmente Pacote)
        setTimeout(() => {
            alterarTipoContrato();
        }, 200);
    }
    
    // Calcular valor total inicial e ajustar campos por tipo
    if (!isEdit) {
        setTimeout(() => {
            alterarTipoContrato(); // Ajustar labels primeiro
            atualizarCalculoContrato(); // Depois calcular
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
    const campoHoras = document.getElementById('contrato-horas');
    const campoTotal = document.getElementById('contrato-valor-total');
    const campoTipo = document.getElementById('contrato-tipo');
    
    console.log('🧮 Calculando:');
    console.log('   📍 campoValorMensal existe?', !!campoValorMensal);
    console.log('   📍 campoMeses existe?', !!campoMeses);
    console.log('   📍 campoHoras existe?', !!campoHoras);
    console.log('   📍 campoTotal existe?', !!campoTotal);
    console.log('   📍 campoTipo existe?', !!campoTipo);
    
    if (!campoValorMensal || !campoMeses || !campoTotal || !campoTipo) {
        console.warn('⚠️ Campos de cálculo não encontrados - abortando atualização');
        return;
    }
    
    const tipo = campoTipo.value;
    let valorTotal = 0;
    
    // 🔧 Parse correto de valor brasileiro: remove pontos (milhar), troca vírgula por ponto (decimal)
    const valorMensalStr = String(campoValorMensal.value).replace(/\./g, '').replace(/,/g, '.');
    const valorMensal = parseFloat(valorMensalStr) || 0;
    const meses = parseInt(campoMeses.value) || 0;
    
    if (tipo === 'Pacote') {
        // === CÁLCULO TIPO PACOTE ===
        // valorTotal = valor_hora × qtd_pacotes × horas_pacote
        const horasPacote = parseInt(campoHoras.value) || 0;
        valorTotal = valorMensal * meses * horasPacote;
        
        console.log('🧮 Calculando (PACOTE):');
        console.log('   📝 Valor por Hora (.value):', campoValorMensal.value);
        console.log('   💰 Valor por Hora (parseado):', valorMensal);
        console.log('   📝 Qtd. Pacotes (.value):', campoMeses.value);
        console.log('   🔢 Qtd. Pacotes (parseado):', meses);
        console.log('   📝 Horas por Pacote (.value):', campoHoras.value);
        console.log('   🔢 Horas por Pacote (parseado):', horasPacote);
        console.log('   💵 Valor Total:', valorTotal, '=', valorMensal, '×', meses, '×', horasPacote);
        
    } else {
        // === CÁLCULO TIPO MENSAL/ÚNICO ===
        // valorTotal = valor_mensal × qtd_meses
        valorTotal = valorMensal * meses;
        
        console.log('🧮 Calculando (MENSAL/ÚNICO):');
        console.log('   📝 Valor Mensal (.value):', campoValorMensal.value);
        console.log('   💰 Valor Mensal (parseado):', valorMensal);
        console.log('   📝 Meses (.value):', campoMeses.value);
        console.log('   🔢 Meses (parseado):', meses);
        console.log('   💵 Valor Total:', valorTotal, '=', valorMensal, '×', meses);
    }
    
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
    
    // 🔧 Parse correto de valor brasileiro: remove pontos (milhar), troca vírgula por ponto (decimal)
    const valorMensalRaw = document.getElementById('contrato-valor-mensal').value;
    const valorMensalStr = String(valorMensalRaw).replace(/\./g, '').replace(/,/g, '.');
    const valorMensal = parseFloat(valorMensalStr) || 0;
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

/**
 * Renderiza botões de ação baseados no status da sessão
 */
function renderBotoesStatusSessao(sessao) {
    if (!sessao || !sessao.id) return '';
    
    const status = sessao.status || 'rascunho';
    const sessaoId = sessao.id;
    
    const badges = {
        'rascunho': { cor: '#94a3b8', label: '📝 Rascunho', icone: '📝' },
        'agendada': { cor: '#3b82f6', label: '📅 Agendada', icone: '📅' },
        'em_andamento': { cor: '#f59e0b', label: '⏳ Em Andamento', icone: '⏳' },
        'finalizada': { cor: '#10b981', label: '✅ Finalizada', icone: '✅' },
        'cancelada': { cor: '#ef4444', label: '❌ Cancelada', icone: '❌' },
        'reaberta': { cor: '#8b5cf6', label: '🔄 Reaberta', icone: '🔄' }
    };
    
    const badge = badges[status] || badges['rascunho'];
    
    let html = `
        <!-- Badge de Status -->
        <div style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 10px; background: ${badge.cor}; color: white; padding: 10px 20px; border-radius: 8px; font-weight: 600;">
            ${badge.label}
        </div>
    `;
    
    // Botões baseados no status
    switch(status) {
        case 'rascunho':
            html += `
                <button type="button" class="btn" style="background: #3b82f6; color: white;" onclick="confirmarSessao(${sessaoId})">
                    📅 Confirmar/Agendar
                </button>
                <button type="button" class="btn" style="background: #ef4444; color: white;" onclick="cancelarSessaoModal(${sessaoId})">
                    ❌ Cancelar
                </button>
            `;
            break;
            
        case 'agendada':
            html += `
                <button type="button" class="btn" style="background: #f59e0b; color: white;" onclick="iniciarSessao(${sessaoId})">
                    ▶️ Iniciar Sessão
                </button>
                <button type="button" class="btn" style="background: #10b981; color: white;" onclick="finalizarSessaoModal(${sessaoId})">
                    ✅ Finalizar Diretamente
                </button>
                <button type="button" class="btn" style="background: #ef4444; color: white;" onclick="cancelarSessaoModal(${sessaoId})">
                    ❌ Cancelar
                </button>
            `;
            break;
            
        case 'em_andamento':
            html += `
                <button type="button" class="btn" style="background: #10b981; color: white;" onclick="finalizarSessaoModal(${sessaoId})">
                    ✅ Finalizar Sessão
                </button>
                <button type="button" class="btn" style="background: #ef4444; color: white;" onclick="cancelarSessaoModal(${sessaoId})">
                    ❌ Cancelar
                </button>
            `;
            break;
            
        case 'finalizada':
            html += `
                <button type="button" class="btn" style="background: #8b5cf6; color: white;" onclick="reabrirSessaoModal(${sessaoId})">
                    🔄 Reabrir Sessão
                </button>
            `;
            break;
            
        case 'cancelada':
            html += `
                <button type="button" class="btn" style="background: #8b5cf6; color: white;" onclick="reabrirSessaoModal(${sessaoId})">
                    🔄 Reabrir Sessão
                </button>
            `;
            break;
            
        case 'reaberta':
            html += `
                <button type="button" class="btn" style="background: #3b82f6; color: white;" onclick="confirmarSessao(${sessaoId})">
                    📅 Agendar Novamente
                </button>
                <button type="button" class="btn" style="background: #10b981; color: white;" onclick="finalizarSessaoModal(${sessaoId})">
                    ✅ Finalizar
                </button>
                <button type="button" class="btn" style="background: #ef4444; color: white;" onclick="cancelarSessaoModal(${sessaoId})">
                    ❌ Cancelar
                </button>
            `;
            break;
    }
    
    return html;
}

/**
 * Confirma/Agenda uma sessão (rascunho → agendada)
 */
async function confirmarSessao(sessaoId) {
    if (!confirm('📅 Confirmar esta sessão?\n\nStatus será alterado para AGENDADA.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sessoes/${sessaoId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'agendada' })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast('✅ ' + result.message, 'success');
            closeModal();
            if (typeof loadSessoes === 'function') loadSessoes();
        } else {
            showToast('❌ Erro: ' + (result.message || result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao confirmar sessão:', error);
        showToast('❌ Erro: ' + error.message, 'error');
    }
}

/**
 * Inicia uma sessão (agendada → em_andamento)
 */
async function iniciarSessao(sessaoId) {
    if (!confirm('▶️ Iniciar esta sessão?\n\nStatus será alterado para EM ANDAMENTO.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sessoes/${sessaoId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'em_andamento' })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast('✅ ' + result.message, 'success');
            closeModal();
            if (typeof loadSessoes === 'function') loadSessoes();
        } else {
            showToast('❌ Erro: ' + (result.message || result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao iniciar sessão:', error);
        showToast('❌ Erro: ' + error.message, 'error');
    }
}

/**
 * Cancela uma sessão
 */
async function cancelarSessaoModal(sessaoId) {
    const motivo = prompt('❌ Cancelar sessão?\n\nInforme o motivo (opcional):');
    
    if (motivo === null) {
        return; // Usuário clicou em Cancelar
    }
    
    try {
        const response = await fetch(`/api/sessoes/${sessaoId}/cancelar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ motivo: motivo || undefined })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast('✅ ' + result.message, 'success');
            closeModal();
            if (typeof loadSessoes === 'function') loadSessoes();
        } else {
            showToast('❌ Erro: ' + (result.message || result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao cancelar sessão:', error);
        showToast('❌ Erro: ' + error.message, 'error');
    }
}

/**
 * Reabre uma sessão finalizada ou cancelada
 */
async function reabrirSessaoModal(sessaoId) {
    if (!confirm('🔄 Reabrir esta sessão?\n\n⚠️ ATENÇÃO: Se a sessão foi finalizada, as horas deduzidas do contrato NÃO serão devolvidas automaticamente.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sessoes/${sessaoId}/reabrir`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast('✅ ' + result.message, 'success');
            closeModal();
            if (typeof loadSessoes === 'function') loadSessoes();
        } else {
            showToast('❌ Erro: ' + (result.message || result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('❌ Erro ao reabrir sessão:', error);
        showToast('❌ Erro: ' + error.message, 'error');
    }
}

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
    if (!window.funcoesResponsaveis || window.funcoesResponsaveis.length === 0) {
        await loadFuncoesResponsaveis();
    }
    if (!window.custosOperacionais || window.custosOperacionais.length === 0) {
        await loadCustosOperacionais();
    }
    if (!window.tagsDisponiveis || window.tagsDisponiveis.length === 0) {
        await loadTags();
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
                <div id="sessao-tags-container">
                    ${renderizarSeletorTags(isEdit && sessaoEdit.tags_ids ? sessaoEdit.tags_ids : [])}
                </div>
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
                ${isEdit ? renderBotoesStatusSessao(sessaoEdit) : ''}
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
            
            // Configurar eventos de clique nas tags
            configurarEventosTags();
        }, 100);
    } else {
        // Se for criação, também configurar eventos das tags
        setTimeout(() => {
            configurarEventosTags();
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
    
    // Opções de funções (para datalist)
    const datalistId = 'funcoes-list-' + Date.now();
    const opcoesFuncoes = window.funcoesResponsaveis && window.funcoesResponsaveis.length > 0
        ? window.funcoesResponsaveis.map(f => `<option value="${f.nome}">`).join('')
        : '';
    
    const div = document.createElement('div');
    div.className = 'responsavel-item';
    div.style.cssText = 'display: grid; grid-template-columns: 2fr 1fr auto auto; gap: 10px; margin-bottom: 10px; align-items: center;';
    div.innerHTML = `
        <select class="responsavel-funcionario" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            <option value="">Selecione...</option>
            ${opcoesFuncionarios}
        </select>
        
        <div style="position: relative; display: flex; gap: 5px;">
            <input 
                type="text" 
                class="responsavel-funcao responsavel-funcao-select" 
                list="${datalistId}"
                placeholder="Captação, Edição..." 
                value="${dadosIniciais ? dadosIniciais.funcao || '' : ''}" 
                style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            <datalist id="${datalistId}">
                ${opcoesFuncoes}
            </datalist>
        </div>
        
        <button type="button" onclick="openModalAdicionarFuncao()" class="btn btn-sm" style="padding: 8px 12px; background: #10b981; color: white;" title="Adicionar Nova Função">
            ➕
        </button>
        
        <button type="button" onclick="this.closest('.responsavel-item').remove()" class="btn btn-sm btn-danger" style="padding: 8px 12px;">
            🗑️
        </button>
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
    
    // Criar datalist único para este input
    const datalistId = 'custos-list-' + Date.now();
    const opcoesCustos = window.custosOperacionais && window.custosOperacionais.length > 0
        ? window.custosOperacionais.map(c => {
            return `<option value="${c.nome}" data-valor="${c.valor_padrao}" data-categoria="${c.categoria}" data-unidade="${c.unidade}">`;
        }).join('')
        : '';
    
    const div = document.createElement('div');
    div.className = 'custo-adicional-item';
    div.style.cssText = 'display: grid; grid-template-columns: 2fr 1fr 1fr auto auto; gap: 10px; margin-bottom: 10px; align-items: center;';
    div.innerHTML = `
        <input 
            type="text" 
            class="custo-descricao custo-descricao-select" 
            list="${datalistId}"
            placeholder="Uber, Hotel, Alimentação..." 
            value="${dadosIniciais ? dadosIniciais.descricao || '' : ''}" 
            style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;"
            oninput="preencherDadosCusto(this)">
        <datalist id="${datalistId}">
            ${opcoesCustos}
        </datalist>
        
        <input 
            type="number" 
            class="custo-valor" 
            step="0.01" 
            min="0" 
            placeholder="65.00" 
            value="${dadosIniciais ? dadosIniciais.valor || '' : ''}" 
            style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        
        <input 
            type="text" 
            class="custo-tipo" 
            placeholder="Transporte" 
            value="${dadosIniciais ? dadosIniciais.tipo || '' : ''}" 
            style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        
        <button type="button" onclick="openModalAdicionarCusto()" class="btn btn-sm" style="padding: 8px 12px; background: #10b981; color: white;" title="Adicionar Novo Custo">
            ➕
        </button>
        
        <button type="button" onclick="this.closest('.custo-adicional-item').remove()" class="btn btn-sm btn-danger" style="padding: 8px 12px;">
            🗑️
        </button>
    `;
    container.appendChild(div);
}

/**
 * Preenche automaticamente valor e categoria ao selecionar custo
 */
function preencherDadosCusto(input) {
    const custoNome = input.value;
    const custo = window.custosOperacionais.find(c => c.nome === custoNome);
    
    if (custo) {
        const container = input.closest('.custo-adicional-item');
        const inputValor = container.querySelector('.custo-valor');
        const inputTipo = container.querySelector('.custo-tipo');
        
        if (inputValor && !inputValor.value) {
            inputValor.value = custo.valor_padrao;
        }
        
        if (inputTipo) {
            inputTipo.value = custo.categoria;
        }
        
        console.log('💰 Custo preenchido automaticamente:', custo.nome, '-', custo.valor_padrao);
    }
}

window.preencherDadosCusto = preencherDadosCusto;

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
        const pagamentoStr = String(item.querySelector('.equipe-pagamento').value).replace(/\./g, '').replace(/,/g, '.');
        const pagamento = parseFloat(pagamentoStr) || 0;
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
        const valorStr = String(item.querySelector('.eq-alugado-valor').value).replace(/\./g, '').replace(/,/g, '.');
        const valor = parseFloat(valorStr) || 0;
        const locadora = item.querySelector('.eq-alugado-locadora').value;
        if (nome) {
            equipamentos_alugados.push({ nome, valor, locadora });
        }
    });
    
    // Coletar custos adicionais
    const custos_adicionais = [];
    document.querySelectorAll('.custo-adicional-item').forEach(item => {
        const descricao = item.querySelector('.custo-descricao').value;
        const valorStr = String(item.querySelector('.custo-valor').value).replace(/\./g, '').replace(/,/g, '.');
        const valor = parseFloat(valorStr) || 0;
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
        tags_ids: obterTagsSelecionadas(),
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

async function finalizarSessaoModal(sessaoId) {
    if (!confirm('⚠️ Tem certeza que deseja FINALIZAR esta sessão?\n\n✅ As horas trabalhadas serão deduzidas do contrato\n❌ Esta ação não pode ser desfeita facilmente')) {
        return;
    }
    
    try {
        console.log('🏁 Finalizando sessão:', sessaoId);
        
        const response = await fetch(`/api/sessoes/${sessaoId}/finalizar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            console.log('✅ Sessão finalizada:', result);
            
            let mensagem = '✅ Sessão finalizada com sucesso!\n\n';
            
            if (result.controle_horas_ativo) {
                mensagem += `⏱️ Horas trabalhadas: ${result.horas_trabalhadas}h\n`;
                mensagem += `📉 Deduzido do contrato: ${result.horas_deduzidas}h\n`;
                
                if (result.horas_extras > 0) {
                    mensagem += `⚠️ Horas extras: ${result.horas_extras}h (saldo zerado)\n`;
                }
                
                mensagem += `✅ Saldo restante: ${result.saldo_restante}h`;
            }
            
            showToast(mensagem, 'success');
            closeModal();
            
            // Recarregar listas
            if (typeof loadSessoes === 'function') loadSessoes();
            if (typeof loadContratos === 'function') loadContratos();
        } else {
            showToast('❌ Erro: ' + (result.message || result.error || 'Erro desconhecido'), 'error');
            console.error('❌ Detalhes do erro:', result);
        }
        
    } catch (error) {
        console.error('❌ Erro ao finalizar sessão:', error);
        showToast('❌ Erro ao finalizar sessão: ' + error.message, 'error');
    }
}

window.openModalSessao = openModalSessao;
window.salvarSessao = salvarSessao;
window.finalizarSessaoModal = finalizarSessaoModal;
window.renderBotoesStatusSessao = renderBotoesStatusSessao;
window.confirmarSessao = confirmarSessao;
window.iniciarSessao = iniciarSessao;
window.cancelarSessaoModal = cancelarSessaoModal;
window.reabrirSessaoModal = reabrirSessaoModal;
window.adicionarEquipeSessao = adicionarEquipeSessao;
window.adicionarResponsavelSessao = adicionarResponsavelSessao;
window.adicionarEquipamentoAlugado = adicionarEquipamentoAlugado;
window.adicionarCustoAdicional = adicionarCustoAdicional;

// ========================================
// FUNÇÕES DE RESPONSÁVEIS
// ========================================

/**
 * Armazena cache de funções localmente
 */
window.funcoesResponsaveis = [];

/**
 * Carrega funções de responsáveis do backend
 */
async function loadFuncoesResponsaveis() {
    try {
        console.log('📋 Carregando funções de responsáveis...');
        const response = await fetch('/api/funcoes-responsaveis');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        const funcoes = result.success ? (result.data || []) : [];
        window.funcoesResponsaveis = funcoes;
        console.log('✅ Funções carregadas:', funcoes.length);
        return funcoes;
    } catch (error) {
        console.error('❌ Erro ao carregar funções:', error);
        window.funcoesResponsaveis = [];
        return [];
    }
}

/**
 * Abre modal rápido para adicionar nova função
 */
function openModalAdicionarFuncao() {
    const modal = createModal('➕ Nova Função', `
        <form id="form-funcao" onsubmit="salvarFuncaoRapida(event)" style="max-width: 500px;">
            <div class="form-group">
                <label>*Nome da Função:</label>
                <input type="text" id="funcao-nome" required placeholder="Ex: Fotógrafo, Videomaker, Editor..." 
                       style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
            </div>
            
            <div class="form-group">
                <label>Descrição (opcional):</label>
                <textarea id="funcao-descricao" rows="3" placeholder="Descrição da função..." 
                          style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"></textarea>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">➕ Adicionar Função</button>
            </div>
        </form>
    `);
    
    // Focar no campo nome
    setTimeout(() => {
        const campoNome = document.getElementById('funcao-nome');
        if (campoNome) campoNome.focus();
    }, 100);
}

/**
 * Salva nova função via API
 */
async function salvarFuncaoRapida(event) {
    event.preventDefault();
    
    const nome = document.getElementById('funcao-nome').value.trim();
    const descricao = document.getElementById('funcao-descricao').value.trim();
    
    if (!nome) {
        showToast('❌ Nome da função é obrigatório', 'error');
        return;
    }
    
    try {
        console.log('💾 Salvando função:', nome);
        
        const response = await fetch('/api/funcoes-responsaveis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, descricao })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast('✅ Função criada com sucesso!', 'success');
            
            // Recarregar funções
            await loadFuncoesResponsaveis();
            
            // Atualizar selects de funções abertos (se houver)
            atualizarSelectsFuncoes();
            
            closeModal();
        } else {
            showToast('❌ Erro: ' + (result.error || 'Erro desconhecido'), 'error');
            console.error('❌ Erro ao criar função:', result);
        }
    } catch (error) {
        console.error('❌ Erro ao salvar função:', error);
        showToast('❌ Erro ao salvar função: ' + error.message, 'error');
    }
}

/**
 * Atualiza todos os selects de funções na página
 */
function atualizarSelectsFuncoes() {
    // Atualizar selects de responsáveis em sessões
    document.querySelectorAll('.responsavel-funcao-select').forEach(select => {
        const valorAtual = select.value;
        
        // Limpar e recriar opções
        select.innerHTML = '<option value="">Digite ou selecione...</option>';
        
        window.funcoesResponsaveis.forEach(funcao => {
            const option = document.createElement('option');
            option.value = funcao.nome;
            option.textContent = funcao.nome;
            if (funcao.nome === valorAtual) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    });
    
    console.log('🔄 Selects de funções atualizados');
}

window.loadFuncoesResponsaveis = loadFuncoesResponsaveis;
window.openModalAdicionarFuncao = openModalAdicionarFuncao;
window.salvarFuncaoRapida = salvarFuncaoRapida;
window.atualizarSelectsFuncoes = atualizarSelectsFuncoes;

// ========================================
// CUSTOS OPERACIONAIS
// ========================================

/**
 * Armazena cache de custos operacionais
 */
window.custosOperacionais = [];

/**
 * Carrega custos operacionais do backend
 */
async function loadCustosOperacionais() {
    try {
        console.log('💰 Carregando custos operacionais...');
        const response = await fetch('/api/custos-operacionais');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        const custos = result.success ? (result.data || []) : [];
        window.custosOperacionais = custos;
        console.log('✅ Custos carregados:', custos.length);
        return custos;
    } catch (error) {
        console.error('❌ Erro ao carregar custos:', error);
        window.custosOperacionais = [];
        return [];
    }
}

/**
 * Abre modal rápido para adicionar novo custo operacional
 */
function openModalAdicionarCusto() {
    const modal = createModal('💰 Novo Custo Operacional', `
        <form id="form-custo" onsubmit="salvarCustoRapido(event)" style="max-width: 600px;">
            <div class="form-group">
                <label>*Nome do Custo:</label>
                <input type="text" id="custo-nome" required placeholder="Ex: Uber, Hotel, Alimentação..." 
                       style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
            </div>
            
            <div class="form-group">
                <label>*Categoria:</label>
                <select id="custo-categoria" required 
                        style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                    <option value="">Selecione...</option>
                    <option value="Transporte">Transporte</option>
                    <option value="Hospedagem">Hospedagem</option>
                    <option value="Alimentação">Alimentação</option>
                    <option value="Equipamento">Equipamento</option>
                    <option value="Outros">Outros</option>
                </select>
            </div>
            
            <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div class="form-group">
                    <label>Valor Padrão:</label>
                    <input type="number" id="custo-valor" step="0.01" min="0" placeholder="0.00" 
                           style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                </div>
                
                <div class="form-group">
                    <label>Unidade:</label>
                    <select id="custo-unidade" 
                            style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="unidade">Unidade</option>
                        <option value="diária">Diária</option>
                        <option value="hora">Hora</option>
                        <option value="km">Quilômetro</option>
                        <option value="litro">Litro</option>
                        <option value="pessoa">Por Pessoa</option>
                    </select>
                </div>
            </div>
            
            <div class="form-group">
                <label>Descrição (opcional):</label>
                <textarea id="custo-descricao-modal" rows="3" placeholder="Descrição do custo..." 
                          style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"></textarea>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">💰 Adicionar Custo</button>
            </div>
        </form>
    `);
    
    // Focar no campo nome
    setTimeout(() => {
        const campoNome = document.getElementById('custo-nome');
        if (campoNome) campoNome.focus();
    }, 100);
}

/**
 * Salva novo custo via API
 */
async function salvarCustoRapido(event) {
    event.preventDefault();
    
    const nome = document.getElementById('custo-nome').value.trim();
    const categoria = document.getElementById('custo-categoria').value;
    const valor_padrao = parseFloat(document.getElementById('custo-valor').value) || 0;
    const unidade = document.getElementById('custo-unidade').value;
    const descricao = document.getElementById('custo-descricao-modal').value.trim();
    
    if (!nome || !categoria) {
        showToast('❌ Nome e categoria são obrigatórios', 'error');
        return;
    }
    
    try {
        console.log('💾 Salvando custo:', nome);
        
        const response = await fetch('/api/custos-operacionais', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, categoria, valor_padrao, unidade, descricao })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast('✅ Custo criado com sucesso!', 'success');
            
            // Recarregar custos
            await loadCustosOperacionais();
            
            // Atualizar selects de custos abertos (se houver)
            atualizarSelectsCustos();
            
            closeModal();
        } else {
            showToast('❌ Erro: ' + (result.error || 'Erro desconhecido'), 'error');
            console.error('❌ Erro ao criar custo:', result);
        }
    } catch (error) {
        console.error('❌ Erro ao salvar custo:', error);
        showToast('❌ Erro ao salvar custo: ' + error.message, 'error');
    }
}

/**
 * Atualiza todos os datalists de custos na página
 */
function atualizarSelectsCustos() {
    // Atualizar datalists de custos em sessões
    document.querySelectorAll('.custo-descricao-select').forEach(input => {
        const datalistId = input.getAttribute('list');
        const datalist = document.getElementById(datalistId);
        
        if (!datalist) return;
        
        // Limpar e recriar opções
        datalist.innerHTML = '';
        
        window.custosOperacionais.forEach(custo => {
            const option = document.createElement('option');
            option.value = custo.nome;
            option.setAttribute('data-valor', custo.valor_padrao);
            option.setAttribute('data-categoria', custo.categoria);
            option.setAttribute('data-unidade', custo.unidade);
            datalist.appendChild(option);
        });
    });
    
    console.log('🔄 Datalists de custos atualizados');
}

window.loadCustosOperacionais = loadCustosOperacionais;
window.openModalAdicionarCusto = openModalAdicionarCusto;
window.salvarCustoRapido = salvarCustoRapido;
window.atualizarSelectsCustos = atualizarSelectsCustos;

// ========================================
// TAGS
// ========================================

/**
 * Armazena cache de tags
 */
window.tagsDisponiveis = [];

/**
 * Carrega tags do backend
 */
async function loadTags() {
    try {
        console.log('🏷️ Carregando tags...');
        const response = await fetch('/api/tags');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        const tags = result.success ? (result.data || []) : [];
        window.tagsDisponiveis = tags;
        console.log('✅ Tags carregadas:', tags.length);
        return tags;
    } catch (error) {
        console.error('❌ Erro ao carregar tags:', error);
        window.tagsDisponiveis = [];
        return [];
    }
}

/**
 * Abre modal rápido para adicionar nova tag
 */
function openModalAdicionarTag() {
    console.log('🔵 [DEBUG TAG] openModalAdicionarTag() INICIADA');
    const modal = createModal('🏷️ Nova Tag', `
        <form id="form-tag" onsubmit="salvarTagRapida(event)" style="max-width: 600px;">
            <div class="form-group">
                <label>*Nome da Tag:</label>
                <input type="text" id="tag-nome" required placeholder="Ex: Urgente, VIP, Comercial..." 
                       style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
            </div>
            
            <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div class="form-group">
                    <label>Cor:</label>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <input type="color" id="tag-cor" value="#3b82f6" 
                               style="width: 60px; height: 40px; border: 1px solid #ddd; border-radius: 4px; cursor: pointer;">
                        <input type="text" id="tag-cor-texto" value="#3b82f6" placeholder="#3b82f6"
                               style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                               oninput="sincronizarCorTag(this, 'tag-cor')">
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Ícone/Emoji:</label>
                    <input type="text" id="tag-icone" placeholder="🔥" value="🏷️" maxlength="10"
                           style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 20px; text-align: center;">
                </div>
            </div>
            
            <div class="form-group" style="margin-top: 15px;">
                <label>Preview:</label>
                <div id="tag-preview" style="padding: 15px; background: #f3f4f6; border-radius: 8px; border: 2px dashed #d1d5db;">
                    <span style="display: inline-block; padding: 6px 16px; border-radius: 20px; background: #3b82f6; color: white; font-size: 14px; font-weight: 500;">
                        <span id="preview-icone">🏷️</span> <span id="preview-nome">Nome da Tag</span>
                    </span>
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">🏷️ Adicionar Tag</button>
            </div>
        </form>
    `);
    
    console.log('🔵 [DEBUG TAG] Modal criado, aguardando 100ms para anexar listeners');
    
    // Sincronizar campos de cor
    setTimeout(() => {
        const campoNome = document.getElementById('tag-nome');
        const campoCor = document.getElementById('tag-cor');
        const campoCorTexto = document.getElementById('tag-cor-texto');
        const campoIcone = document.getElementById('tag-icone');
        
        console.log('🔵 [DEBUG TAG] Campos encontrados:', {
            campoNome: !!campoNome,
            campoCor: !!campoCor,
            campoCorTexto: !!campoCorTexto,
            campoIcone: !!campoIcone
        });
        
        // Listeners para preview
        if (campoNome) {
            campoNome.addEventListener('input', atualizarPreviewTag);
            campoNome.focus();
            console.log('🔵 [DEBUG TAG] Listeners anexados ao campo nome');
        }
        if (campoCor) {
            campoCor.addEventListener('input', (e) => {
                campoCorTexto.value = e.target.value;
                atualizarPreviewTag();
            });
        }
        if (campoIcone) {
            campoIcone.addEventListener('input', atualizarPreviewTag);
        }
    }, 100);
}

/**
 * Sincroniza campo de cor texto com color picker
 */
function sincronizarCorTag(input, colorPickerId) {
    const colorPicker = document.getElementById(colorPickerId);
    if (colorPicker) {
        colorPicker.value = input.value;
        atualizarPreviewTag();
    }
}

/**
 * Atualiza preview da tag em tempo real
 */
function atualizarPreviewTag() {
    const nome = document.getElementById('tag-nome')?.value || 'Nome da Tag';
    const cor = document.getElementById('tag-cor')?.value || '#3b82f6';
    const icone = document.getElementById('tag-icone')?.value || '🏷️';
    
    const previewNome = document.getElementById('preview-nome');
    const previewIcone = document.getElementById('preview-icone');
    const previewContainer = document.querySelector('#tag-preview span');
    
    if (previewNome) previewNome.textContent = nome;
    if (previewIcone) previewIcone.textContent = icone;
    if (previewContainer) previewContainer.style.background = cor;
}

/**
 * Salva nova tag via API
 */
async function salvarTagRapida(event) {
    console.log('🔵 [DEBUG TAG] salvarTagRapida() INICIADA');
    console.log('🔵 [DEBUG TAG] Event:', event);
    
    event.preventDefault();
    console.log('🔵 [DEBUG TAG] preventDefault() executado');
    
    const campoNome = document.getElementById('tag-nome');
    const campoCor = document.getElementById('tag-cor');
    const campoIcone = document.getElementById('tag-icone');
    
    console.log('🔵 [DEBUG TAG] Campos DOM:', {
        campoNome: campoNome,
        campoCor: campoCor,
        campoIcone: campoIcone
    });
    
    const nome = campoNome ? campoNome.value.trim() : '';
    const cor = campoCor ? campoCor.value : '#3b82f6';
    const icone = campoIcone ? campoIcone.value.trim() : '🏷️';
    
    console.log('🔵 [DEBUG TAG] Valores extraídos:', {
        nome: nome,
        cor: cor,
        icone: icone,
        nomeLength: nome.length
    });
    
    if (!nome) {
        console.error('🔴 [DEBUG TAG] ERRO: Nome vazio!');
        showToast('❌ Nome da tag é obrigatório', 'error');
        return;
    }
    
    try {
        console.log('� [DEBUG TAG] Preparando requisição POST');
        console.log('💾 Salvando tag:', nome);
        
        const payload = { nome, cor, icone };
        console.log('🔵 [DEBUG TAG] Payload:', payload);
        console.log('🔵 [DEBUG TAG] Payload JSON:', JSON.stringify(payload));
        
        console.log('🔵 [DEBUG TAG] Enviando para /api/tags...');
        const response = await fetch('/api/tags', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        console.log('🔵 [DEBUG TAG] Response recebido:', {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok
        });
        
        const result = await response.json();
        console.log('🔵 [DEBUG TAG] Response JSON:', result);
        
        if (response.ok && result.success) {
            console.log('✅ [DEBUG TAG] Sucesso!');
            showToast('✅ Tag criada com sucesso!', 'success');
            
            // Recarregar tags
            await loadTags();
            
            // Atualizar interface de seleção de tags
            atualizarInterfaceTags();
            
            closeModal();
        } else {
            console.error('🔴 [DEBUG TAG] Falha na requisição');
            showToast('❌ Erro: ' + (result.error || 'Erro desconhecido'), 'error');
            console.error('❌ Erro ao criar tag:', result);
        }
    } catch (error) {
        console.error('🔴 [DEBUG TAG] Exception capturada:', error);
        console.error('❌ Erro ao salvar tag:', error);
        showToast('❌ Erro ao salvar tag: ' + error.message, 'error');
    }
}

/**
 * Renderiza interface de seleção múltipla de tags
 */
function renderizarSeletorTags(tagsSelecionadas = []) {
    const tags = window.tagsDisponiveis || [];
    
    if (tags.length === 0) {
        return `
            <div style="padding: 20px; text-align: center; color: #6b7280; background: #f9fafb; border-radius: 8px;">
                <p>Nenhuma tag cadastrada</p>
                <button type="button" onclick="openModalAdicionarTag()" class="btn btn-sm" style="margin-top: 10px; background: #10b981; color: white;">
                    ➕ Criar Primeira Tag
                </button>
            </div>
        `;
    }
    
    return `
        <div id="tags-selector" style="display: flex; flex-wrap: wrap; gap: 8px; padding: 10px; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">
            ${tags.map(tag => {
                const selecionada = tagsSelecionadas.includes(tag.id) || tagsSelecionadas.includes(tag.nome);
                return `
                    <label style="cursor: pointer; user-select: none;">
                        <input 
                            type="checkbox" 
                            class="tag-checkbox" 
                            value="${tag.id}" 
                            ${selecionada ? 'checked' : ''}
                            style="display: none;">
                        <span class="tag-badge ${selecionada ? 'tag-selected' : ''}" 
                              data-tag-id="${tag.id}"
                              style="display: inline-block; padding: 6px 12px; border-radius: 16px; background: ${tag.cor}; color: white; font-size: 13px; font-weight: 500; border: 2px solid ${selecionada ? '#1f2937' : 'transparent'}; transition: all 0.2s;">
                            ${tag.icone} ${tag.nome}
                        </span>
                    </label>
                `;
            }).join('')}
            
            <button type="button" onclick="openModalAdicionarTag()" 
                    class="btn btn-sm" 
                    style="padding: 6px 12px; background: #10b981; color: white; border-radius: 16px; font-size: 13px; border: none; cursor: pointer;"
                    title="Adicionar Nova Tag">
                ➕ Nova Tag
            </button>
        </div>
    `;
}

/**
 * Atualiza interface de tags após criar nova
 */
function atualizarInterfaceTags() {
    const container = document.getElementById('tags-selector');
    if (container) {
        const tagsSelecionadas = obterTagsSelecionadas();
        container.outerHTML = renderizarSeletorTags(tagsSelecionadas);
        configurarEventosTags();
    }
}

/**
 * Configura eventos de clique nas tags
 */
function configurarEventosTags() {
    document.querySelectorAll('.tag-badge').forEach(badge => {
        badge.addEventListener('click', function() {
            const checkbox = this.closest('label').querySelector('.tag-checkbox');
            checkbox.checked = !checkbox.checked;
            
            if (checkbox.checked) {
                this.classList.add('tag-selected');
                this.style.borderColor = '#1f2937';
            } else {
                this.classList.remove('tag-selected');
                this.style.borderColor = 'transparent';
            }
        });
    });
}

/**
 * Obtém IDs das tags selecionadas
 */
function obterTagsSelecionadas() {
    const checkboxes = document.querySelectorAll('.tag-checkbox:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.value));
}

window.loadTags = loadTags;
window.openModalAdicionarTag = openModalAdicionarTag;
window.salvarTagRapida = salvarTagRapida;
window.renderizarSeletorTags = renderizarSeletorTags;
window.sincronizarCorTag = sincronizarCorTag;
window.atualizarPreviewTag = atualizarPreviewTag;
window.configurarEventosTags = configurarEventosTags;
window.obterTagsSelecionadas = obterTagsSelecionadas;

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

/**
 * FUNÇÃO: Altera dinamicamente os campos do formulário de contrato baseado no tipo
 */
function alterarTipoContrato() {
    const tipoSelect = document.getElementById('contrato-tipo');
    const tipo = tipoSelect ? tipoSelect.value : 'Mensal';
    
    const campoValorMensal = document.getElementById('contrato-valor-mensal');
    const campoMeses = document.getElementById('contrato-meses');
    const campoHoras = document.getElementById('contrato-horas');
    
    // Obter labels (parent > label)
    const labelValorMensal = campoValorMensal?.parentElement?.querySelector('label');
    const labelMeses = campoMeses?.parentElement?.querySelector('label');
    const labelHoras = campoHoras?.parentElement?.querySelector('label');
    
    if (tipo === 'Pacote') {
        // === MODO PACOTE ===
        // Altera label "Valor Mensal" → "Valor por Hora"
        if (labelValorMensal) labelValorMensal.textContent = '*Valor por Hora:';
        if (campoValorMensal) {
            campoValorMensal.placeholder = '150.00';
            campoValorMensal.title = 'Valor cobrado por hora de trabalho';
        }
        
        // Altera label "Qtd. Meses" → "Qtd. Pacotes"
        if (labelMeses) labelMeses.textContent = '*Qtd. Pacotes:';
        if (campoMeses) {
            campoMeses.placeholder = '10';
            campoMeses.title = 'Quantidade de pacotes contratados';
        }
        
        // Altera label "Horas Mensais" → "Horas por Pacote" e torna obrigatório
        if (labelHoras) labelHoras.textContent = '*Horas por Pacote:';
        if (campoHoras) {
            campoHoras.required = true;
            campoHoras.placeholder = '8';
            campoHoras.title = 'Horas incluídas em cada pacote';
            campoHoras.oninput = atualizarCalculoContrato; // Adiciona trigger de cálculo
        }
        
    } else {
        // === MODO MENSAL/ÚNICO ===
        // Restaura label "Valor por Hora" → "Valor Mensal"
        if (labelValorMensal) labelValorMensal.textContent = '*Valor Mensal:';
        if (campoValorMensal) {
            campoValorMensal.placeholder = '3500.00';
            campoValorMensal.title = 'Valor mensal do contrato';
        }
        
        // Restaura label "Qtd. Pacotes" → "Qtd. Meses"
        if (labelMeses) labelMeses.textContent = '*Qtd. Meses:';
        if (campoMeses) {
            campoMeses.placeholder = '12';
            campoMeses.title = 'Duração do contrato em meses';
        }
        
        // Restaura label "Horas por Pacote" → "Horas Mensais" e remove obrigatoriedade
        if (labelHoras) labelHoras.textContent = 'Horas Mensais:';
        if (campoHoras) {
            campoHoras.required = false;
            campoHoras.placeholder = '8';
            campoHoras.title = 'Horas mensais estimadas (opcional)';
            campoHoras.oninput = null; // Remove trigger de cálculo
        }
    }
    
    // Recalcula valor total com nova lógica
    atualizarCalculoContrato();
}

window.alterarTipoContrato = alterarTipoContrato;

// ==================== COMISSÕES CALCULADAS (PARTE 8) ====================

/**
 * Calcula valor da comissão baseado em tipo, percentual e valor base
 * @param {Object} comissao - Dados da comissão
 * @param {string} comissao.tipo - 'percentual' ou 'fixo'
 * @param {number} comissao.percentual - Percentual da comissão (ex: 10 para 10%)
 * @param {number} comissao.valor - Valor fixo (se tipo = 'fixo')
 * @param {number} valorBase - Valor base para cálculo (valor da sessão ou contrato)
 * @returns {number} Valor calculado da comissão
 */
function calcularValorComissao(comissao, valorBase = 0) {
    if (!comissao) return 0;
    
    // Se tipo é 'fixo' ou 'valor', retornar valor fixo
    if (comissao.tipo === 'fixo' || comissao.tipo === 'valor') {
        return parseFloat(comissao.valor) || 0;
    }
    
    // Se tipo é 'percentual', calcular baseado no valor base
    if (comissao.tipo === 'percentual') {
        const percentual = parseFloat(comissao.percentual) || 0;
        const base = parseFloat(valorBase) || 0;
        return (base * percentual) / 100;
    }
    
    return 0;
}

/**
 * Formata comissão para exibição
 * @param {Object} comissao - Dados da comissão
 * @param {number} valorCalculado - Valor calculado
 * @returns {string} Texto formatado (ex: "10% = R$ 150,00")
 */
function formatarComissao(comissao, valorCalculado) {
    if (!comissao) return '';
    
    if (comissao.tipo === 'percentual') {
        return `${comissao.percentual}% = ${formatarMoeda(valorCalculado)}`;
    } else {
        return formatarMoeda(valorCalculado);
    }
}

/**
 * Atualiza visualização de comissões calculadas em tempo real
 * @param {string} containerId - ID do container HTML
 * @param {Array} comissoes - Array de comissões
 * @param {number} valorBase - Valor base para cálculo
 */
function atualizarComissoesCalculadas(containerId, comissoes, valorBase) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (!comissoes || comissoes.length === 0) {
        container.innerHTML = '<p style="color: #7f8c8d; font-style: italic;">Nenhuma comissão cadastrada</p>';
        return;
    }
    
    let totalComissoes = 0;
    const html = comissoes.map(com => {
        const valorCalculado = calcularValorComissao(com, valorBase);
        totalComissoes += valorCalculado;
        
        return `
            <div style="display: flex; justify-content: space-between; padding: 8px; border-bottom: 1px solid #eee;">
                <span>${com.descricao || com.funcionario_nome || 'Comissão'}</span>
                <span style="font-weight: bold; color: #27ae60;">${formatarComissao(com, valorCalculado)}</span>
            </div>
        `;
    }).join('');
    
    container.innerHTML = `
        ${html}
        <div style="display: flex; justify-content: space-between; padding: 12px 8px; background: #ecf0f1; font-weight: bold; margin-top: 10px; border-radius: 4px;">
            <span>Total de Comissões:</span>
            <span style="color: #2c3e50;">${formatarMoeda(totalComissoes)}</span>
        </div>
    `;
}

/**
 * Adiciona listener para recalcular comissões quando valor base muda
 * @param {string} inputValorId - ID do input de valor
 * @param {string} containerComissoesId - ID do container de comissões
 * @param {Array} comissoes - Array de comissões
 */
function configurarCalculoAutomaticoComissoes(inputValorId, containerComissoesId, comissoes) {
    const inputValor = document.getElementById(inputValorId);
    if (!inputValor) return;
    
    inputValor.addEventListener('input', function() {
        const valorRaw = this.value || '0';
        const valorStr = String(valorRaw).replace(/\./g, '').replace(/,/g, '.');
        const valor = parseFloat(valorStr) || 0;
        
        atualizarComissoesCalculadas(containerComissoesId, comissoes, valor);
    });
    
    // Disparar cálculo inicial
    const evento = new Event('input');
    inputValor.dispatchEvent(evento);
}

// Expor funções globalmente
window.calcularValorComissao = calcularValorComissao;
window.formatarComissao = formatarComissao;
window.atualizarComissoesCalculadas = atualizarComissoesCalculadas;
window.configurarCalculoAutomaticoComissoes = configurarCalculoAutomaticoComissoes;

// ==================== FIM: COMISSÕES CALCULADAS ====================

console.log('✓ Modals.js v20251204lancamentos5 carregado com sucesso');