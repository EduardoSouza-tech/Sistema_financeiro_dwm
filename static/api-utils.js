/**
 * 🔧 Utilitário para padronizar tratamento de respostas da API
 * Sistema Financeiro DWM
 * 
 * Funções auxiliares para lidar com respostas padronizadas do backend
 */

/**
 * Processa resposta da API no formato padronizado
 * 
 * @param {Response} response - Resposta do fetch
 * @returns {Promise<Object>} Dados processados
 * @throws {Error} Se houver erro real na API
 * 
 * @example
 * // Antes (com erro em lista vazia):
 * const data = await fetch('/api/lancamentos').then(r => r.json());
 * 
 * // Depois (diferencia lista vazia de erro):
 * const result = await processarRespostaAPI(await fetch('/api/lancamentos'));
 * if (result.data.length === 0) {
 *   console.log(result.message); // "Nenhum lançamento encontrado"
 * }
 */
export async function processarRespostaAPI(response) {
    // Verificar se resposta é OK (200-299)
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Erro HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    // Se resposta já está no formato padronizado { success, data, total, message }
    if (data.hasOwnProperty('success')) {
        if (!data.success) {
            throw new Error(data.error || 'Erro desconhecido');
        }
        return data;
    }
    
    // Se resposta é array direto (formato antigo), converter para padronizado
    if (Array.isArray(data)) {
        return {
            success: true,
            data: data,
            total: data.length,
            message: data.length === 0 ? 'Nenhum dado encontrado' : null
        };
    }
    
    // Se resposta é objeto simples, retornar como está
    return {
        success: true,
        data: data,
        total: 1,
        message: null
    };
}

/**
 * Wrapper para fetch com tratamento de erros melhorado
 * 
 * @param {string} url - URL da API
 * @param {Object} options - Opções do fetch
 * @returns {Promise<Object>} Resposta processada
 * 
 * @example
 * try {
 *   const result = await fetchAPI('/api/lancamentos');
 *   if (result.data.length === 0) {
 *     mostrarMensagemInfo(result.message);
 *   } else {
 *     preencherTabela(result.data);
 *   }
 * } catch (error) {
 *   mostrarMensagemErro(error.message);
 * }
 */
export async function fetchAPI(url, options = {}) {
    try {
        const response = await fetch(url, options);
        return await processarRespostaAPI(response);
    } catch (error) {
        console.error(`Erro ao buscar ${url}:`, error);
        throw error;
    }
}

/**
 * Mostra mensagem apropriada baseada na resposta
 * 
 * @param {Object} result - Resultado da API processado
 * @param {HTMLElement} container - Elemento onde mostrar mensagem
 * @param {string} tipoRecurso - Nome do recurso (ex: "lançamentos", "clientes")
 */
export function mostrarMensagemResultado(result, container, tipoRecurso = 'dados') {
    if (result.data.length === 0 && result.message) {
        // Lista vazia - mostrar mensagem informativa, não erro
        const mensagemDiv = document.createElement('div');
        mensagemDiv.className = 'alert alert-info';
        mensagemDiv.innerHTML = `
            <i class="bi bi-info-circle"></i>
            <strong>Nenhum ${tipoRecurso} encontrado</strong>
            <p class="mb-0 mt-2">${result.message}</p>
        `;
        container.innerHTML = '';
        container.appendChild(mensagemDiv);
        return false; // Indica que não há dados
    }
    return true; // Indica que há dados
}

/**
 * Mostra mensagem de erro real
 * 
 * @param {Error} error - Erro capturado
 * @param {HTMLElement} container - Elemento onde mostrar erro
 */
export function mostrarMensagemErro(error, container) {
    const erroDiv = document.createElement('div');
    erroDiv.className = 'alert alert-danger';
    erroDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle"></i>
        <strong>Erro ao carregar dados</strong>
        <p class="mb-0 mt-2">${error.message}</p>
        <button class="btn btn-sm btn-outline-danger mt-2" onclick="location.reload()">
            <i class="bi bi-arrow-clockwise"></i> Tentar novamente
        </button>
    `;
    container.innerHTML = '';
    container.appendChild(erroDiv);
}

/**
 * Exemplo de uso integrado
 * 
 * @example
 * async function carregarLancamentos() {
 *   const container = document.getElementById('lista-lancamentos');
 *   
 *   try {
 *     const result = await fetchAPI('/api/lancamentos');
 *     
 *     if (!mostrarMensagemResultado(result, container, 'lançamentos')) {
 *       // Não há dados - mensagem já foi mostrada
 *       return;
 *     }
 *     
 *     // Há dados - preencher tabela
 *     preencherTabela(result.data);
 *     
 *   } catch (error) {
 *     mostrarMensagemErro(error, container);
 *   }
 * }
 */

// Para compatibilidade com código existente (não-module)
if (typeof window !== 'undefined') {
    window.processarRespostaAPI = processarRespostaAPI;
    window.fetchAPI = fetchAPI;
    window.mostrarMensagemResultado = mostrarMensagemResultado;
    window.mostrarMensagemErro = mostrarMensagemErro;
}
