# 🎨 Padrão de Loading Moderno

## 📋 Visão Geral

Este documento descreve o padrão de animação de loading ultra-moderno implementado no sistema. Use este padrão em qualquer funcionalidade que precise mostrar carregamento ao usuário.

**Características:**
- ✨ Glassmorphism (efeito de vidro fosco)
- 🌊 Wave animation com 3 dots coloridos
- 🎭 Texto com gradiente animado
- 📊 Progress bar com gradiente deslizante
- 💫 Animações suaves com cubic-bezier
- 🎨 Paleta moderna: Verde, Azul, Roxo

---

## 🎨 CSS - Adicionar no `<style>`

```css
/* Loading Overlay Animation - MODERNO */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, rgba(39, 174, 96, 0.15), rgba(41, 128, 185, 0.15));
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 99999;
    animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.loading-container {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 50px 60px;
    border-radius: 24px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3),
                0 0 100px rgba(39, 174, 96, 0.2);
    animation: scaleIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    border: 1px solid rgba(255, 255, 255, 0.3);
}

.loading-dots {
    display: flex;
    gap: 12px;
    margin-bottom: 30px;
    justify-content: center;
}

.loading-dot {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: linear-gradient(135deg, #27ae60, #2ecc71);
    animation: wave 1.4s ease-in-out infinite;
    box-shadow: 0 4px 12px rgba(39, 174, 96, 0.4);
}

.loading-dot:nth-child(1) {
    animation-delay: 0s;
    background: linear-gradient(135deg, #27ae60, #2ecc71);
}

.loading-dot:nth-child(2) {
    animation-delay: 0.2s;
    background: linear-gradient(135deg, #2980b9, #3498db);
}

.loading-dot:nth-child(3) {
    animation-delay: 0.4s;
    background: linear-gradient(135deg, #8e44ad, #9b59b6);
}

.loading-text {
    margin: 0;
    font-size: 24px;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(135deg, #27ae60, #2980b9, #8e44ad);
    background-size: 200% 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradientShift 3s ease infinite;
    letter-spacing: -0.5px;
}

.loading-subtext {
    margin-top: 15px;
    color: #555;
    font-size: 15px;
    font-weight: 500;
    text-align: center;
    animation: floatText 2s ease-in-out infinite;
}

.loading-progress-bar {
    width: 100%;
    height: 4px;
    background: rgba(39, 174, 96, 0.1);
    border-radius: 10px;
    margin-top: 25px;
    overflow: hidden;
    position: relative;
}

.loading-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #27ae60, #2980b9, #8e44ad);
    background-size: 200% 100%;
    border-radius: 10px;
    animation: progressSlide 2s ease-in-out infinite;
    box-shadow: 0 0 10px rgba(39, 174, 96, 0.5);
}

@keyframes wave {
    0%, 100% {
        transform: translateY(0) scale(1);
    }
    25% {
        transform: translateY(-20px) scale(1.1);
    }
    50% {
        transform: translateY(0) scale(1);
    }
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes floatText {
    0%, 100% { transform: translateY(0px); opacity: 0.8; }
    50% { transform: translateY(-5px); opacity: 1; }
}

@keyframes fadeIn {
    from { 
        opacity: 0;
        transform: scale(0.95);
    }
    to { 
        opacity: 1;
        transform: scale(1);
    }
}

@keyframes scaleIn {
    from {
        opacity: 0;
        transform: scale(0.8) translateY(20px);
    }
    to {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

@keyframes progressSlide {
    0% {
        transform: translateX(-100%);
        background-position: 0% 0%;
    }
    100% {
        transform: translateX(100%);
        background-position: 200% 0%;
    }
}
```

---

## 📝 HTML - Estrutura do Loading

```html
<!-- Loading Overlay para [NOME DA FUNCIONALIDADE] -->
<div id="loading-[IDENTIFICADOR]" class="loading-overlay" style="display: none;">
    <div class="loading-container">
        <div class="loading-dots">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
        <div class="loading-text">⚡ [TÍTULO DA OPERAÇÃO]</div>
        <div class="loading-subtext">[DESCRIÇÃO DO PROCESSO]</div>
        <div class="loading-progress-bar">
            <div class="loading-progress-fill"></div>
        </div>
    </div>
</div>
```

### 📌 Exemplo Real (Conciliação Geral)

```html
<!-- Loading Overlay para Conciliação Geral -->
<div id="loading-conciliacao" class="loading-overlay" style="display: none;">
    <div class="loading-container">
        <div class="loading-dots">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
        <div class="loading-text">⚡ Conciliação Geral</div>
        <div class="loading-subtext">Processando 694 transações em lote...</div>
        <div class="loading-progress-bar">
            <div class="loading-progress-fill"></div>
        </div>
    </div>
</div>
```

---

## 💻 JavaScript - Como Integrar

### ✅ Padrão Básico

```javascript
async function minhaFuncaoComLoading() {
    // 1. MOSTRAR loading no início
    document.getElementById('loading-[IDENTIFICADOR]').style.display = 'flex';
    
    try {
        // 2. Executar operação demorada
        const response = await fetch('/api/endpoint', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ dados: valor })
        });
        
        const data = await response.json();
        
        // 3. ESCONDER loading após sucesso
        document.getElementById('loading-[IDENTIFICADOR]').style.display = 'none';
        
        // 4. Mostrar resultado (modal, mensagem, etc)
        alert('Operação concluída com sucesso!');
        
    } catch (error) {
        console.error('Erro:', error);
        
        // 5. ESCONDER loading em caso de erro
        document.getElementById('loading-[IDENTIFICADOR]').style.display = 'none';
        
        alert('Erro ao processar operação.');
    }
}
```

### ✅ Exemplo Real (Conciliação Geral)

```javascript
async function abrirConciliacaoGeral() {
    console.log('🔄 Abrindo Conciliação Geral...');
    
    // Mostrar loading overlay
    document.getElementById('loading-conciliacao').style.display = 'flex';
    
    try {
        // Buscar transações não conciliadas
        const response = await fetch('/api/extratos?conciliado=false', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        
        const responseData = await response.json();
        let transacoes = Array.isArray(responseData) ? responseData : (responseData.transacoes || []);
        
        if (transacoes.length === 0) {
            document.getElementById('loading-conciliacao').style.display = 'none';
            alert('✅ Não há transações pendentes de conciliação!');
            return;
        }
        
        // ... processamento de dados ...
        
        // Esconder loading e mostrar modal
        document.getElementById('loading-conciliacao').style.display = 'none';
        document.getElementById('modal-conciliacao-geral').style.display = 'flex';
        
    } catch (error) {
        console.error('❌ Erro ao abrir conciliação geral:', error);
        document.getElementById('loading-conciliacao').style.display = 'none';
        alert('❌ Erro ao carregar transações para conciliação. Verifique o console.');
    }
}
```

---

## 🎯 Checklist de Implementação

Ao aplicar este padrão em uma nova funcionalidade, siga esta checklist:

- [ ] 1. **CSS adicionado** no `<style>` do arquivo HTML (copiar todo o bloco de estilos)
- [ ] 2. **HTML adicionado** antes do modal/conteúdo principal
  - [ ] Alterar `id="loading-[IDENTIFICADOR]"` para ID único
  - [ ] Personalizar texto principal `.loading-text`
  - [ ] Personalizar subtexto `.loading-subtext`
- [ ] 3. **JavaScript integrado** na função assíncrona
  - [ ] `display = 'flex'` no **início** da função
  - [ ] `display = 'none'` **antes** de mostrar resultado de sucesso
  - [ ] `display = 'none'` **no bloco catch** de erro
  - [ ] `display = 'none'` em **retornos antecipados** (early returns)
- [ ] 4. **Testado** os 3 cenários:
  - [ ] ✅ Sucesso (loading aparece e some, resultado aparece)
  - [ ] ⚠️ Dados vazios (loading aparece e some, mensagem aparece)
  - [ ] ❌ Erro (loading aparece e some, erro aparece)

---

## 🎨 Personalizações Comuns

### 📝 Alterar Texto

```html
<!-- Exemplo: Relatório de Vendas -->
<div class="loading-text">📊 Gerando Relatório</div>
<div class="loading-subtext">Analisando 1.245 vendas do período...</div>
```

### 🎨 Alterar Cores (opcional)

Se quiser cores específicas para uma funcionalidade, adicione ID único:

```css
/* Loading para Relatório Financeiro - Tons de Azul */
#loading-relatorio .loading-dot:nth-child(1) {
    background: linear-gradient(135deg, #2980b9, #3498db);
}

#loading-relatorio .loading-dot:nth-child(2) {
    background: linear-gradient(135deg, #1e3a8a, #2563eb);
}

#loading-relatorio .loading-text {
    background: linear-gradient(135deg, #2980b9, #1e3a8a, #0ea5e9);
}
```

### ⏱️ Alterar Velocidade das Animações

```css
/* Mais rápido (1s ao invés de 1.4s) */
.loading-dot {
    animation: wave 1s ease-in-out infinite;
}

/* Mais lento (2s ao invés de 1.4s) */
.loading-dot {
    animation: wave 2s ease-in-out infinite;
}
```

---

## 📍 Onde Este Padrão Está Implementado

### ✅ Implementado

1. **Conciliação Geral de Extrato** (`interface_nova.html`)
   - Função: `abrirConciliacaoGeral()`
   - ID: `loading-conciliacao`
   - Processamento: 694 transações em batch
   - Tempo: ~2-3 segundos

---

## 🚀 Próximas Implementações Sugeridas

### 1. **Importação de Arquivos OFX**
```html
<div id="loading-importacao-ofx" class="loading-overlay" style="display: none;">
    <div class="loading-container">
        <div class="loading-dots">...</div>
        <div class="loading-text">📥 Importando Extrato</div>
        <div class="loading-subtext">Processando arquivo OFX...</div>
        <div class="loading-progress-bar">...</div>
    </div>
</div>
```

### 2. **Geração de Relatórios**
```html
<div id="loading-relatorio" class="loading-overlay" style="display: none;">
    <div class="loading-container">
        <div class="loading-dots">...</div>
        <div class="loading-text">📊 Gerando Relatório</div>
        <div class="loading-subtext">Compilando dados financeiros...</div>
        <div class="loading-progress-bar">...</div>
    </div>
</div>
```

### 3. **Sincronização/Backup**
```html
<div id="loading-backup" class="loading-overlay" style="display: none;">
    <div class="loading-container">
        <div class="loading-dots">...</div>
        <div class="loading-text">💾 Salvando Backup</div>
        <div class="loading-subtext">Sincronizando dados...</div>
        <div class="loading-progress-bar">...</div>
    </div>
</div>
```

### 4. **Análise de Dados**
```html
<div id="loading-analise" class="loading-overlay" style="display: none;">
    <div class="loading-container">
        <div class="loading-dots">...</div>
        <div class="loading-text">🔍 Analisando Dados</div>
        <div class="loading-subtext">Processando informações...</div>
        <div class="loading-progress-bar">...</div>
    </div>
</div>
```

---

## 💡 Dicas de UX

1. **Sempre mostre o loading IMEDIATAMENTE** após o clique do usuário
   - Não espere a requisição começar para mostrar

2. **Seja específico no texto**
   - ✅ "Processando 694 transações em lote..."
   - ❌ "Carregando..."

3. **Sempre esconda o loading antes de mostrar qualquer feedback**
   - Modal de sucesso
   - Alert de erro
   - Mensagem de aviso

4. **Teste todos os cenários**
   - Conexão lenta
   - Conexão rápida
   - Erro de rede
   - Dados vazios

5. **Nunca deixe o loading "preso"**
   - Sempre tenha `display = 'none'` em TODOS os caminhos de saída da função

---

## 🐛 Troubleshooting

### Problema: Loading não aparece
**Solução:** Verifique se o CSS foi adicionado e se o ID está correto

### Problema: Loading fica preso na tela
**Solução:** Certifique-se que TODOS os caminhos da função (try, catch, early returns) escondem o loading

### Problema: Animações não funcionam
**Solução:** Verifique se todos os @keyframes foram copiados

### Problema: Backdrop-filter não funciona em navegadores antigos
**Solução:** O fallback já está incluído com `-webkit-backdrop-filter`. Em navegadores muito antigos, o fundo será semi-transparente sem blur.

---

## 📊 Performance

- **Tamanho CSS:** ~3KB
- **Impacto no carregamento:** Mínimo (inline no HTML)
- **Compatibilidade:** Chrome 76+, Firefox 103+, Safari 15.4+, Edge 79+
- **FPS das animações:** 60fps em dispositivos modernos

---

## 📝 Changelog

### v1.0 (2026-02-25) - Implementação Inicial
- ✨ Glassmorphism com backdrop-filter
- 🌊 Wave animation com 3 dots coloridos
- 🎭 Texto com gradiente animado tri-color
- 📊 Progress bar com gradiente deslizante
- 💫 Animações suaves com cubic-bezier
- 🎨 Paleta moderna: Verde, Azul, Roxo

---

## 📧 Suporte

Para dúvidas ou sugestões sobre este padrão de loading, consulte este documento ou peça ajuda ao time de desenvolvimento.

---

**🎨 Use este padrão para manter a consistência visual em todo o sistema!**
