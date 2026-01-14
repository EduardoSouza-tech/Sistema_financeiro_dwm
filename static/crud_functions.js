/**
 * ============================================================================
 * FUNÇÕES DE CRUD - Create, Read, Update, Delete
 * ============================================================================
 * Gerencia operações de salvar, editar e deletar registros
 * ============================================================================
 */

// ============================================================================
// LANÇAMENTOS
// ============================================================================

/**
 * Salva ou atualiza um lançamento
 * @param {Event} event - Evento do formulário
 */
async function salvarLancamento(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const id = formData.get('id');
    
    try {
        const data = {
            tipo: formData.get('tipo'),
            descricao: formData.get('descricao'),
            valor: parseFloat(formData.get('valor')),
            data_vencimento: formData.get('data_vencimento'),
            categoria_id: formData.get('categoria_id') || null,
            subcategoria_id: formData.get('subcategoria_id') || null,
            conta_bancaria_id: formData.get('conta_bancaria_id'),
            pessoa: formData.get('pessoa') || null,
            status: formData.get('status'),
            data_pagamento: formData.get('data_pagamento') || null,
            observacoes: formData.get('observacoes') || null
        };
        
        let response;
        if (id) {
            // Atualizar
            response = await fetch(`${CONFIG.API_URL}/lancamentos/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        } else {
            // Criar
            response = await fetch(`${CONFIG.API_URL}/lancamentos`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }
        
        if (response.ok) {
            showNotification('Lançamento salvo com sucesso!', 'success');
            closeModal('modal-lancamento');
            form.reset();
            
            // Recarrega dados
            await loadLancamentos();
            await loadDashboard();
        } else {
            const error = await response.json();
            showNotification(`Erro: ${error.message || 'Erro desconhecido'}`, 'error');
        }
    } catch (error) {
        logError('salvarLancamento', error);
        showNotification('Erro ao salvar lançamento', 'error');
    }
}

/**
 * Edita um lançamento
 * @param {number} id - ID do lançamento
 */
async function editarLancamento(id) {
    try {
        const response = await fetch(`${CONFIG.API_URL}/lancamentos/${id}`);
        if (!response.ok) throw new Error('Lançamento não encontrado');
        
        const lancamento = await response.json();
        
        // Preenche formulário
        document.getElementById('lancamento-id').value = lancamento.id;
        document.querySelector('#form-lancamento [name="tipo"]').value = lancamento.tipo;
        document.querySelector('#form-lancamento [name="descricao"]').value = lancamento.descricao;
        document.querySelector('#form-lancamento [name="valor"]').value = lancamento.valor;
        document.querySelector('#form-lancamento [name="data_vencimento"]').value = lancamento.data_vencimento;
        document.querySelector('#form-lancamento [name="categoria_id"]').value = lancamento.categoria_id || '';
        document.querySelector('#form-lancamento [name="subcategoria_id"]').value = lancamento.subcategoria_id || '';
        document.querySelector('#form-lancamento [name="conta_bancaria_id"]').value = lancamento.conta_bancaria_id;
        document.querySelector('#form-lancamento [name="pessoa"]').value = lancamento.pessoa || '';
        document.querySelector('#form-lancamento [name="status"]').value = lancamento.status;
        document.querySelector('#form-lancamento [name="data_pagamento"]').value = lancamento.data_pagamento || '';
        document.querySelector('#form-lancamento [name="observacoes"]').value = lancamento.observacoes || '';
        
        openModal('modal-lancamento');
    } catch (error) {
        logError('editarLancamento', error);
        showNotification('Erro ao carregar lançamento', 'error');
    }
}

/**
 * Deleta um lançamento
 * @param {number} id - ID do lançamento
 */
async function deletarLancamento(id) {
    if (!confirm('Tem certeza que deseja excluir este lançamento?')) return;
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/lancamentos/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Lançamento excluído com sucesso!', 'success');
            await loadLancamentos();
            await loadDashboard();
        } else {
            showNotification('Erro ao excluir lançamento', 'error');
        }
    } catch (error) {
        logError('deletarLancamento', error);
        showNotification('Erro ao excluir lançamento', 'error');
    }
}

// ============================================================================
// CONTAS BANCÁRIAS
// ============================================================================

/**
 * Salva ou atualiza uma conta bancária
 * @param {Event} event - Evento do formulário
 */
async function salvarConta(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const id = formData.get('id');
    
    try {
        const data = {
            nome: formData.get('nome'),
            banco: formData.get('banco'),
            agencia: formData.get('agencia'),
            conta: formData.get('conta'),
            saldo_inicial: parseFloat(formData.get('saldo_inicial') || 0)
        };
        
        let response;
        if (id) {
            response = await fetch(`${CONFIG.API_URL}/contas/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        } else {
            response = await fetch(`${CONFIG.API_URL}/contas`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }
        
        if (response.ok) {
            showNotification('Conta salva com sucesso!', 'success');
            closeModal('modal-conta');
            form.reset();
            await loadContas();
        } else {
            const error = await response.json();
            showNotification(`Erro: ${error.message || 'Erro desconhecido'}`, 'error');
        }
    } catch (error) {
        logError('salvarConta', error);
        showNotification('Erro ao salvar conta', 'error');
    }
}

/**
 * Edita uma conta bancária
 * @param {number} id - ID da conta
 */
async function editarConta(id) {
    try {
        const response = await fetch(`${CONFIG.API_URL}/contas/${id}`);
        if (!response.ok) throw new Error('Conta não encontrada');
        
        const conta = await response.json();
        
        document.getElementById('conta-id').value = conta.id;
        document.querySelector('#form-conta [name="nome"]').value = conta.nome;
        document.querySelector('#form-conta [name="banco"]').value = conta.banco;
        document.querySelector('#form-conta [name="agencia"]').value = conta.agencia;
        document.querySelector('#form-conta [name="conta"]').value = conta.conta;
        document.querySelector('#form-conta [name="saldo_inicial"]').value = conta.saldo_inicial;
        
        openModal('modal-conta');
    } catch (error) {
        logError('editarConta', error);
        showNotification('Erro ao carregar conta', 'error');
    }
}

/**
 * Deleta uma conta bancária
 * @param {number} id - ID da conta
 */
async function deletarConta(id) {
    if (!confirm('Tem certeza que deseja excluir esta conta?')) return;
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/contas/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Conta excluída com sucesso!', 'success');
            await loadContas();
        } else {
            showNotification('Erro ao excluir conta', 'error');
        }
    } catch (error) {
        logError('deletarConta', error);
        showNotification('Erro ao excluir conta', 'error');
    }
}

// ============================================================================
// CATEGORIAS
// ============================================================================

/**
 * Salva ou atualiza uma categoria
 * @param {Event} event - Evento do formulário
 */
async function salvarCategoria(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const id = formData.get('id');
    
    try {
        const data = {
            nome: formData.get('nome'),
            tipo: formData.get('tipo'),
            descricao: formData.get('descricao') || null
        };
        
        let response;
        if (id) {
            response = await fetch(`${CONFIG.API_URL}/categorias/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        } else {
            response = await fetch(`${CONFIG.API_URL}/categorias`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }
        
        if (response.ok) {
            showNotification('Categoria salva com sucesso!', 'success');
            closeModal('modal-categoria');
            form.reset();
            await loadCategorias();
        } else {
            const error = await response.json();
            showNotification(`Erro: ${error.message || 'Erro desconhecido'}`, 'error');
        }
    } catch (error) {
        logError('salvarCategoria', error);
        showNotification('Erro ao salvar categoria', 'error');
    }
}

/**
 * Edita uma categoria
 * @param {number} id - ID da categoria
 */
async function editarCategoria(id) {
    try {
        const response = await fetch(`${CONFIG.API_URL}/categorias/${id}`);
        if (!response.ok) throw new Error('Categoria não encontrada');
        
        const categoria = await response.json();
        
        document.getElementById('categoria-id').value = categoria.id;
        document.querySelector('#form-categoria [name="nome"]').value = categoria.nome;
        document.querySelector('#form-categoria [name="tipo"]').value = categoria.tipo;
        document.querySelector('#form-categoria [name="descricao"]').value = categoria.descricao || '';
        
        openModal('modal-categoria');
    } catch (error) {
        logError('editarCategoria', error);
        showNotification('Erro ao carregar categoria', 'error');
    }
}

/**
 * Deleta uma categoria
 * @param {number} id - ID da categoria
 */
async function deletarCategoria(id) {
    if (!confirm('Tem certeza que deseja excluir esta categoria?')) return;
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/categorias/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Categoria excluída com sucesso!', 'success');
            await loadCategorias();
        } else {
            showNotification('Erro ao excluir categoria', 'error');
        }
    } catch (error) {
        logError('deletarCategoria', error);
        showNotification('Erro ao excluir categoria', 'error');
    }
}

// ============================================================================
// CLIENTES
// ============================================================================

/**
 * Salva ou atualiza um cliente
 * @param {Event} event - Evento do formulário
 */
async function salvarCliente(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const id = formData.get('id');
    
    try {
        const data = {
            nome: formData.get('nome'),
            documento: formData.get('documento') || null,
            telefone: formData.get('telefone') || null,
            email: formData.get('email') || null,
            endereco: formData.get('endereco') || null,
            observacoes: formData.get('observacoes') || null
        };
        
        let response;
        if (id) {
            response = await fetch(`${CONFIG.API_URL}/clientes/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        } else {
            response = await fetch(`${CONFIG.API_URL}/clientes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }
        
        if (response.ok) {
            showNotification('Cliente salvo com sucesso!', 'success');
            closeModal('modal-cliente');
            form.reset();
            if (window.loadClientes) await loadClientes();
        } else {
            const error = await response.json();
            showNotification(`Erro: ${error.message || 'Erro desconhecido'}`, 'error');
        }
    } catch (error) {
        logError('salvarCliente', error);
        showNotification('Erro ao salvar cliente', 'error');
    }
}

/**
 * Edita um cliente
 * @param {number} id - ID do cliente
 */
async function editarCliente(id) {
    try {
        const response = await fetch(`${CONFIG.API_URL}/clientes/${id}`);
        if (!response.ok) throw new Error('Cliente não encontrado');
        
        const cliente = await response.json();
        
        document.getElementById('cliente-id').value = cliente.id;
        document.querySelector('#form-cliente [name="nome"]').value = cliente.nome;
        document.querySelector('#form-cliente [name="documento"]').value = cliente.documento || '';
        document.querySelector('#form-cliente [name="telefone"]').value = cliente.telefone || '';
        document.querySelector('#form-cliente [name="email"]').value = cliente.email || '';
        document.querySelector('#form-cliente [name="endereco"]').value = cliente.endereco || '';
        document.querySelector('#form-cliente [name="observacoes"]').value = cliente.observacoes || '';
        
        openModal('modal-cliente');
    } catch (error) {
        logError('editarCliente', error);
        showNotification('Erro ao carregar cliente', 'error');
    }
}

/**
 * Deleta um cliente
 * @param {number} id - ID do cliente
 */
async function deletarCliente(id) {
    if (!confirm('Tem certeza que deseja excluir este cliente?')) return;
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/clientes/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Cliente excluído com sucesso!', 'success');
            if (window.loadClientes) await loadClientes();
        } else {
            showNotification('Erro ao excluir cliente', 'error');
        }
    } catch (error) {
        logError('deletarCliente', error);
        showNotification('Erro ao excluir cliente', 'error');
    }
}

// ============================================================================
// FORNECEDORES
// ============================================================================

/**
 * Salva ou atualiza um fornecedor
 * @param {Event} event - Evento do formulário
 */
async function salvarFornecedor(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const id = formData.get('id');
    
    try {
        const data = {
            nome: formData.get('nome'),
            documento: formData.get('documento') || null,
            telefone: formData.get('telefone') || null,
            email: formData.get('email') || null,
            endereco: formData.get('endereco') || null,
            observacoes: formData.get('observacoes') || null
        };
        
        let response;
        if (id) {
            response = await fetch(`${CONFIG.API_URL}/fornecedores/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        } else {
            response = await fetch(`${CONFIG.API_URL}/fornecedores`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }
        
        if (response.ok) {
            showNotification('Fornecedor salvo com sucesso!', 'success');
            closeModal('modal-fornecedor');
            form.reset();
            if (window.loadFornecedores) await loadFornecedores();
        } else {
            const error = await response.json();
            showNotification(`Erro: ${error.message || 'Erro desconhecido'}`, 'error');
        }
    } catch (error) {
        logError('salvarFornecedor', error);
        showNotification('Erro ao salvar fornecedor', 'error');
    }
}

/**
 * Edita um fornecedor
 * @param {number} id - ID do fornecedor
 */
async function editarFornecedor(id) {
    try {
        const response = await fetch(`${CONFIG.API_URL}/fornecedores/${id}`);
        if (!response.ok) throw new Error('Fornecedor não encontrado');
        
        const fornecedor = await response.json();
        
        document.getElementById('fornecedor-id').value = fornecedor.id;
        document.querySelector('#form-fornecedor [name="nome"]').value = fornecedor.nome;
        document.querySelector('#form-fornecedor [name="documento"]').value = fornecedor.documento || '';
        document.querySelector('#form-fornecedor [name="telefone"]').value = fornecedor.telefone || '';
        document.querySelector('#form-fornecedor [name="email"]').value = fornecedor.email || '';
        document.querySelector('#form-fornecedor [name="endereco"]').value = fornecedor.endereco || '';
        document.querySelector('#form-fornecedor [name="observacoes"]').value = fornecedor.observacoes || '';
        
        openModal('modal-fornecedor');
    } catch (error) {
        logError('editarFornecedor', error);
        showNotification('Erro ao carregar fornecedor', 'error');
    }
}

/**
 * Deleta um fornecedor
 * @param {number} id - ID do fornecedor
 */
async function deletarFornecedor(id) {
    if (!confirm('Tem certeza que deseja excluir este fornecedor?')) return;
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/fornecedores/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Fornecedor excluído com sucesso!', 'success');
            if (window.loadFornecedores) await loadFornecedores();
        } else {
            showNotification('Erro ao excluir fornecedor', 'error');
        }
    } catch (error) {
        logError('deletarFornecedor', error);
        showNotification('Erro ao excluir fornecedor', 'error');
    }
}

// ============================================================================
// SUBCATEGORIAS
// ============================================================================

/**
 * Carrega subcategorias de uma categoria
 * @param {number} categoriaId - ID da categoria
 */
async function loadSubcategorias(categoriaId) {
    const subcategoriaSelect = document.getElementById('select-subcategoria');
    if (!subcategoriaSelect) return;
    
    try {
        subcategoriaSelect.innerHTML = '<option value="">Nenhuma subcategoria</option>';
        
        if (!categoriaId) return;
        
        const response = await fetch(`${CONFIG.API_URL}/categorias/${categoriaId}/subcategorias`);
        if (!response.ok) return;
        
        const subcategorias = await response.json();
        
        subcategorias.forEach(sub => {
            const option = document.createElement('option');
            option.value = sub.id;
            option.textContent = sub.nome;
            subcategoriaSelect.appendChild(option);
        });
    } catch (error) {
        logError('loadSubcategorias', error);
    }
}

console.log('✅ crud_functions.js carregado');
