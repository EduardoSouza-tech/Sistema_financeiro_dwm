/**
 * 🛠️ Utils.js - Biblioteca de Utilidades Frontend
 * ================================================
 * 
 * Funções compartilhadas para uso em toda a aplicação.
 * Reduz duplicação e padroniza comportamentos.
 * 
 * Autor: Sistema de Otimização - Fase 4
 * Data: 20/01/2026
 */

// ============================================================================
// FORMATAÇÃO DE MOEDA
// ============================================================================

/**
 * Formata valor como moeda brasileira
 * @param {number|string} valor - Valor a formatar
 * @param {string} moeda - Símbolo da moeda (padrão: R$)
 * @returns {string} Valor formatado (ex: "R$ 1.234,56")
 * 
 * @example
 * formatarMoeda(1234.56) // "R$ 1.234,56"
 * formatarMoeda(1000, "USD") // "USD 1.000,00"
 */
function formatarMoeda(valor, moeda = 'R$') {
    try {
        if (valor === null || valor === undefined) {
            return `${moeda} 0,00`;
        }
        
        // Converte para número
        const numero = typeof valor === 'string' ? parseFloat(valor.replace(/[^0-9,-]/g, '').replace(',', '.')) : parseFloat(valor);
        
        if (isNaN(numero)) {
            return `${moeda} 0,00`;
        }
        
        // Formata com separadores brasileiros
        const formatado = numero.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        
        return `${moeda} ${formatado}`;
    } catch (e) {
        console.error('Erro ao formatar moeda:', e);
        return `${moeda} 0,00`;
    }
}

/**
 * Converte string de moeda para número
 * @param {string} valorStr - String formatada (ex: "R$ 1.234,56")
 * @returns {number} Valor numérico
 * 
 * @example
 * parseMoeda("R$ 1.234,56") // 1234.56
 * parseMoeda("1.500,00") // 1500.0
 */
function parseMoeda(valorStr) {
    try {
        if (!valorStr) return 0;
        
        // Remove símbolos e converte vírgula para ponto
        const limpo = valorStr
            .replace(/[R$USD€\s]/g, '')
            .replace(/\./g, '')
            .replace(',', '.');
        
        const numero = parseFloat(limpo);
        return isNaN(numero) ? 0 : numero;
    } catch (e) {
        console.error('Erro ao parsear moeda:', e);
        return 0;
    }
}

/**
 * Formata porcentagem
 * @param {number} valor - Valor numérico (ex: 15.5 para 15.5%)
 * @param {number} decimais - Casas decimais (padrão: 2)
 * @returns {string} Valor formatado (ex: "15,50%")
 */
function formatarPorcentagem(valor, decimais = 2) {
    try {
        const numero = parseFloat(valor);
        if (isNaN(numero)) return '0,00%';
        
        return numero.toFixed(decimais).replace('.', ',') + '%';
    } catch (e) {
        return '0,00%';
    }
}

// ============================================================================
// FORMATAÇÃO DE DATA
// ============================================================================

/**
 * Formata data no padrão brasileiro
 * @param {string|Date} data - Data a formatar (ISO ou objeto Date)
 * @param {boolean} incluirHora - Se true, inclui hora (dd/mm/yyyy HH:MM)
 * @returns {string} Data formatada
 * 
 * @example
 * formatarData("2026-01-20") // "20/01/2026"
 * formatarData(new Date(), true) // "20/01/2026 14:30"
 */
function formatarData(data, incluirHora = false) {
    try {
        if (!data) return '';
        
        const dataObj = typeof data === 'string' ? new Date(data) : data;
        
        if (isNaN(dataObj.getTime())) return '';
        
        const dia = String(dataObj.getDate()).padStart(2, '0');
        const mes = String(dataObj.getMonth() + 1).padStart(2, '0');
        const ano = dataObj.getFullYear();
        
        let formatado = `${dia}/${mes}/${ano}`;
        
        if (incluirHora) {
            const hora = String(dataObj.getHours()).padStart(2, '0');
            const min = String(dataObj.getMinutes()).padStart(2, '0');
            formatado += ` ${hora}:${min}`;
        }
        
        return formatado;
    } catch (e) {
        console.error('Erro ao formatar data:', e);
        return '';
    }
}

/**
 * Converte data brasileira para formato ISO
 * @param {string} dataBr - Data em formato dd/mm/yyyy
 * @returns {string} Data em formato ISO (yyyy-mm-dd)
 * 
 * @example
 * dataParaISO("20/01/2026") // "2026-01-20"
 */
function dataParaISO(dataBr) {
    try {
        const partes = dataBr.split('/');
        if (partes.length !== 3) return '';
        
        const [dia, mes, ano] = partes;
        return `${ano}-${mes.padStart(2, '0')}-${dia.padStart(2, '0')}`;
    } catch (e) {
        return '';
    }
}

/**
 * Obtém data atual formatada
 * @returns {string} Data atual em dd/mm/yyyy
 */
function getDataAtual() {
    return formatarData(new Date());
}

/**
 * Calcula dias entre duas datas
 * @param {string|Date} data1 - Primeira data
 * @param {string|Date} data2 - Segunda data
 * @returns {number} Número de dias
 */
function diasEntre(data1, data2) {
    try {
        const d1 = typeof data1 === 'string' ? new Date(data1) : data1;
        const d2 = typeof data2 === 'string' ? new Date(data2) : data2;
        
        const diffTime = Math.abs(d2 - d1);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    } catch (e) {
        return 0;
    }
}

// ============================================================================
// NOTIFICAÇÕES E TOASTS
// ============================================================================

/**
 * Exibe notificação toast
 * @param {string} mensagem - Mensagem a exibir
 * @param {string} tipo - Tipo de notificação: 'success', 'error', 'warning', 'info'
 * @param {number} duracao - Duração em ms (padrão: 3000)
 * 
 * @example
 * mostrarToast("Salvo com sucesso!", "success")
 * mostrarToast("Erro ao salvar", "error", 5000)
 */
function mostrarToast(mensagem, tipo = 'info', duracao = 3000) {
    // Se já existe função showNotification, usa ela
    if (typeof showNotification === 'function') {
        showNotification(mensagem, tipo);
        return;
    }
    
    // Caso contrário, cria toast simples
    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;
    toast.textContent = mensagem;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${tipo === 'success' ? '#28a745' : tipo === 'error' ? '#dc3545' : tipo === 'warning' ? '#ffc107' : '#17a2b8'};
        color: white;
        border-radius: 4px;
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duracao);
}

// ============================================================================
// VALIDAÇÃO DE FORMULÁRIOS
// ============================================================================

/**
 * Valida email
 * @param {string} email - Email a validar
 * @returns {boolean} True se válido
 */
function validarEmail(email) {
    const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return regex.test(email);
}

/**
 * Valida CPF
 * @param {string} cpf - CPF a validar (com ou sem formatação)
 * @returns {boolean} True se válido
 */
function validarCPF(cpf) {
    cpf = cpf.replace(/[^\d]/g, '');
    
    if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) {
        return false;
    }
    
    let soma = 0;
    for (let i = 0; i < 9; i++) {
        soma += parseInt(cpf.charAt(i)) * (10 - i);
    }
    let digito1 = 11 - (soma % 11);
    if (digito1 >= 10) digito1 = 0;
    
    soma = 0;
    for (let i = 0; i < 10; i++) {
        soma += parseInt(cpf.charAt(i)) * (11 - i);
    }
    let digito2 = 11 - (soma % 11);
    if (digito2 >= 10) digito2 = 0;
    
    return parseInt(cpf.charAt(9)) === digito1 && parseInt(cpf.charAt(10)) === digito2;
}

/**
 * Valida CNPJ
 * @param {string} cnpj - CNPJ a validar (com ou sem formatação)
 * @returns {boolean} True se válido
 */
function validarCNPJ(cnpj) {
    cnpj = cnpj.replace(/[^\d]/g, '');
    
    if (cnpj.length !== 14 || /^(\d)\1{13}$/.test(cnpj)) {
        return false;
    }
    
    const calcularDigito = (cnpj, peso) => {
        let soma = 0;
        for (let i = 0; i < peso.length; i++) {
            soma += parseInt(cnpj.charAt(i)) * peso[i];
        }
        const digito = 11 - (soma % 11);
        return digito >= 10 ? 0 : digito;
    };
    
    const peso1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    const digito1 = calcularDigito(cnpj, peso1);
    
    const peso2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    const digito2 = calcularDigito(cnpj, peso2);
    
    return parseInt(cnpj.charAt(12)) === digito1 && parseInt(cnpj.charAt(13)) === digito2;
}

/**
 * Valida telefone brasileiro
 * @param {string} telefone - Telefone a validar
 * @returns {boolean} True se válido
 */
function validarTelefone(telefone) {
    const limpo = telefone.replace(/[^\d]/g, '');
    return limpo.length === 10 || limpo.length === 11;
}

/**
 * Valida se campo não está vazio
 * @param {*} valor - Valor a validar
 * @returns {boolean} True se preenchido
 */
function validarObrigatorio(valor) {
    return valor !== null && valor !== undefined && String(valor).trim() !== '';
}

// ============================================================================
// MANIPULAÇÃO DE DOM
// ============================================================================

/**
 * Mostra elemento (remove classe 'd-none')
 * @param {string|HTMLElement} elemento - Seletor ou elemento DOM
 */
function mostrarElemento(elemento) {
    const el = typeof elemento === 'string' ? document.querySelector(elemento) : elemento;
    if (el) el.classList.remove('d-none');
}

/**
 * Esconde elemento (adiciona classe 'd-none')
 * @param {string|HTMLElement} elemento - Seletor ou elemento DOM
 */
function esconderElemento(elemento) {
    const el = typeof elemento === 'string' ? document.querySelector(elemento) : elemento;
    if (el) el.classList.add('d-none');
}

/**
 * Toggle visibilidade de elemento
 * @param {string|HTMLElement} elemento - Seletor ou elemento DOM
 */
function toggleElemento(elemento) {
    const el = typeof elemento === 'string' ? document.querySelector(elemento) : elemento;
    if (el) el.classList.toggle('d-none');
}

/**
 * Limpa formulário
 * @param {string|HTMLFormElement} form - Seletor ou elemento de formulário
 */
function limparFormulario(form) {
    const formulario = typeof form === 'string' ? document.querySelector(form) : form;
    if (formulario) {
        formulario.reset();
        // Remove classes de validação
        formulario.querySelectorAll('.is-invalid, .is-valid').forEach(el => {
            el.classList.remove('is-invalid', 'is-valid');
        });
    }
}

// ============================================================================
// UTILITÁRIOS GERAIS
// ============================================================================

/**
 * Debounce - Limita frequência de execução de função
 * @param {Function} func - Função a executar
 * @param {number} wait - Tempo de espera em ms
 * @returns {Function} Função com debounce
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Copia texto para clipboard
 * @param {string} texto - Texto a copiar
 * @returns {Promise<boolean>} True se copiado com sucesso
 */
async function copiarParaClipboard(texto) {
    try {
        await navigator.clipboard.writeText(texto);
        return true;
    } catch (e) {
        // Fallback para navegadores antigos
        const textarea = document.createElement('textarea');
        textarea.value = texto;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        const sucesso = document.execCommand('copy');
        document.body.removeChild(textarea);
        return sucesso;
    }
}

/**
 * Sanitiza HTML para prevenir XSS
 * @param {string} texto - Texto a sanitizar
 * @returns {string} Texto sanitizado
 */
function sanitizarHTML(texto) {
    const div = document.createElement('div');
    div.textContent = texto;
    return div.innerHTML;
}

/**
 * Gera ID único
 * @returns {string} ID único
 */
function gerarID() {
    return `id_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ============================================================================
// EXPORTAR PARA USO GLOBAL
// ============================================================================

// Se houver sistema de módulos, exporta
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        // Moeda
        formatarMoeda,
        parseMoeda,
        formatarPorcentagem,
        
        // Data
        formatarData,
        dataParaISO,
        getDataAtual,
        diasEntre,
        
        // Notificações
        mostrarToast,
        
        // Validação
        validarEmail,
        validarCPF,
        validarCNPJ,
        validarTelefone,
        validarObrigatorio,
        
        // DOM
        mostrarElemento,
        esconderElemento,
        toggleElemento,
        limparFormulario,
        
        // Utilitários
        debounce,
        copiarParaClipboard,
        sanitizarHTML,
        gerarID
    };
}

// Adiciona ao objeto global window para uso direto no HTML
if (typeof window !== 'undefined') {
    window.Utils = {
        formatarMoeda,
        parseMoeda,
        formatarPorcentagem,
        formatarData,
        dataParaISO,
        getDataAtual,
        diasEntre,
        mostrarToast,
        validarEmail,
        validarCPF,
        validarCNPJ,
        validarTelefone,
        validarObrigatorio,
        mostrarElemento,
        esconderElemento,
        toggleElemento,
        limparFormulario,
        debounce,
        copiarParaClipboard,
        sanitizarHTML,
        gerarID
    };
}

console.log('✅ Utils.js carregado - Biblioteca de utilidades disponível');
