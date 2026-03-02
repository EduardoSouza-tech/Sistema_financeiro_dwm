/**
 * fiscal_federal.js — Módulo Fiscal Federal (Integra Contador SERPRO)
 * Tabs: Dashboard | CNPJ | CND | DCTFWeb | MIT | REINF | DARF | Logs | Fila
 */

// ─── Estado Global ────────────────────────────────────────────────────────────
const FiscalFederal = (() => {
  const STORAGE_KEY = 'fiscal_federal_config';
  let _config = {};

  // Retorna o CNPJ da empresa logada (sem máscara)
  function _empresaCnpj() {
    const d = window.currentEmpresaData || {};
    return (d.cnpj || d.cnpj_cpf || '').replace(/\D/g, '');
  }

  // Garante que currentEmpresaData está preenchido (busca da API se necessário)
  async function _ensureEmpresaData() {
    if (window.currentEmpresaData && window.currentEmpresaData.cnpj) return;
    const eid = window.currentEmpresaId;
    if (!eid) return;
    try {
      const r = await fetch(`/api/empresas/${eid}`);
      const j = await r.json();
      if (j.success && j.empresa) window.currentEmpresaData = j.empresa;
    } catch (e) {
      console.warn('FiscalFederal: não foi possível carregar dados da empresa', e);
    }
  }

  function loadConfig() {
    try {
      _config = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch { _config = {}; }
    // Auto-preencher com CNPJ da empresa se não houver config salva
    const cnpjEmpresa = _empresaCnpj();
    if (cnpjEmpresa) {
      if (!_config.contratante_cnpj) _config.contratante_cnpj = cnpjEmpresa;
      if (!_config.autor_doc)        _config.autor_doc        = cnpjEmpresa;
    }
  }

  function saveConfig() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(_config));
  }

  function getConfig() { return { ..._config }; }

  function setConfig(updates) {
    _config = { ..._config, ...updates };
    saveConfig();
    _applyConfigToForms();
  }

  function _applyConfigToForms() {
    const fields = ['contratante_cnpj', 'autor_doc', 'contribuinte_doc'];
    fields.forEach(f => {
      const el = document.querySelectorAll(`[data-fiscal-field="${f}"]`);
      el.forEach(e => { if (_config[f]) e.value = _config[f]; });
    });
  }

  // ─── Helpers ─────────────────────────────────────────────────────────────
  function fmtDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    return isNaN(d) ? iso : d.toLocaleDateString('pt-BR');
  }

  function fmtDateTime(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    return isNaN(d) ? iso : d.toLocaleString('pt-BR');
  }

  function fmtBRL(v) {
    const n = parseFloat(v);
    if (isNaN(n)) return '—';
    return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }

  function maskCNPJ(v) {
    return v.replace(/\D/g, '')
            .replace(/^(\d{2})(\d)/, '$1.$2')
            .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
            .replace(/\.(\d{3})(\d)/, '.$1/$2')
            .replace(/(\d{4})(\d)/, '$1-$2').slice(0, 18);
  }

  function rawCNPJ(v) { return v.replace(/\D/g, ''); }

  // Converte entrada do usuário MMAAAA → AAAAMM (formato da API SERPRO)
  function _toApiComp(mmaaaa) {
    const v = mmaaaa.replace(/\D/g, '');
    if (v.length !== 6) return v;
    return v.slice(2) + v.slice(0, 2); // MMAAAA → AAAAMM
  }

  // Exibe competência armazenada (AAAAMM) como MM/AAAA
  function _fmtComp(aaaamm) {
    if (!aaaamm) return '—';
    const v = String(aaaamm).replace(/\D/g, '');
    if (v.length === 6) return v.slice(4) + '/' + v.slice(0, 4); // AAAAMM → MM/AAAA
    return aaaamm;
  }

  function toast(msg, type = 'info') {
    if (typeof mostrarNotificacao === 'function') {
      mostrarNotificacao(msg, type);
    } else {
      console.log(`[${type.toUpperCase()}] ${msg}`);
    }
  }

  // ─── API Call ─────────────────────────────────────────────────────────────
  async function apiFiscal(endpoint, method = 'GET', body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include'
    };
    if (body && method !== 'GET') opts.body = JSON.stringify(body);
    const resp = await fetch(`/api/fiscal/${endpoint}`, opts);
    const json = await resp.json();
    if (!json.success && method !== 'GET') {
      throw new Error(json.error || 'Erro desconhecido');
    }
    return json;
  }

  // ─── Tab switcher ─────────────────────────────────────────────────────────
  function switchTab(tabId) {
    document.querySelectorAll('.fiscal-tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.fiscal-tab-pane').forEach(p => p.classList.remove('active'));
    const btn = document.querySelector(`.fiscal-tab-btn[data-tab="${tabId}"]`);
    const pane = document.getElementById(`fiscal-tab-${tabId}`);
    if (btn) btn.classList.add('active');
    if (pane) pane.classList.add('active');
    // lazy-load
    const loaders = { dashboard: loadDashboard, logs: loadLogs, fila: loadFila };
    if (loaders[tabId]) loaders[tabId]();
  }

  // ─── Config Modal ─────────────────────────────────────────────────────────
  function openConfigModal() {
    const cfg = getConfig();
    const cnpjEmpresa = _empresaCnpj();
    document.getElementById('fiscal-cfg-contratante').value = cfg.contratante_cnpj || cnpjEmpresa || '';
    document.getElementById('fiscal-cfg-autor').value        = cfg.autor_doc        || cnpjEmpresa || '';
    document.getElementById('fiscal-cfg-contribuinte').value = cfg.contribuinte_doc || cnpjEmpresa || '';
    document.getElementById('fiscal-config-modal').style.display = 'flex';
  }

  function closeConfigModal() {
    document.getElementById('fiscal-config-modal').style.display = 'none';
  }

  function saveConfigFromModal() {
    setConfig({
      contratante_cnpj: rawCNPJ(document.getElementById('fiscal-cfg-contratante').value),
      autor_doc: rawCNPJ(document.getElementById('fiscal-cfg-autor').value),
      contribuinte_doc: rawCNPJ(document.getElementById('fiscal-cfg-contribuinte').value)
    });
    closeConfigModal();
    toast('Configurações salvas!', 'success');
  }

  // ─── Dashboard ────────────────────────────────────────────────────────────
  async function loadDashboard() {
    const el = document.getElementById('fiscal-dashboard-content');
    if (!el) return;
    el.innerHTML = '<div class="fiscal-loading">Carregando dashboard...</div>';
    try {
      const resp = await apiFiscal('dashboard');
      const d = resp.data || {};
      el.innerHTML = renderDashboard(d);
    } catch (e) {
      el.innerHTML = `<div class="fiscal-error">Erro ao carregar dashboard: ${e.message}</div>`;
    }
  }

  function renderDashboard(d) {
    const cnt = d.counters || {};
    const alerts = d.alertas || [];
    const certidoes = d.certidoes_ativas || [];

    const cards = [
      { label: 'Certidões', value: cnt.certidoes ?? 0, icon: '📜', color: '#4CAF50' },
      { label: 'DARFs', value: cnt.darfs ?? 0, icon: '💸', color: '#2196F3' },
      { label: 'DCTFWeb', value: cnt.dctfweb ?? 0, icon: '📊', color: '#9C27B0' },
      { label: 'REINF', value: cnt.reinf ?? 0, icon: '🔄', color: '#FF9800' },
      { label: 'Logs', value: cnt.logs ?? 0, icon: '📝', color: '#607D8B' },
      { label: 'Fila', value: cnt.fila_pendente ?? 0, icon: '⏳', color: '#F44336' }
    ];

    const cardsHtml = cards.map(c => `
      <div class="fiscal-card" style="border-left:4px solid ${c.color}">
        <span class="fiscal-card-icon">${c.icon}</span>
        <div class="fiscal-card-info">
          <span class="fiscal-card-value">${c.value}</span>
          <span class="fiscal-card-label">${c.label}</span>
        </div>
      </div>`).join('');

    const alertsHtml = alerts.length
      ? alerts.map(a => `<div class="fiscal-alert fiscal-alert-${a.tipo || 'info'}">${a.mensagem}</div>`).join('')
      : '<p class="fiscal-empty">Nenhum alerta no momento.</p>';

    const certHtml = certidoes.length
      ? `<table class="fiscal-table"><thead><tr><th>CNPJ</th><th>Tipo</th><th>Número</th><th>Vencimento</th><th>Status</th></tr></thead>
         <tbody>${certidoes.map(c => `<tr>
           <td>${c.cnpj || '—'}</td><td>${c.tipo || '—'}</td>
           <td>${c.numero || '—'}</td><td>${fmtDate(c.data_vencimento)}</td>
           <td><span class="fiscal-badge fiscal-badge-${c.status === 'emitida' ? 'ok' : 'warn'}">${c.status}</span></td>
         </tr>`).join('')}</tbody></table>`
      : '<p class="fiscal-empty">Nenhuma certidão registrada.</p>';

    return `
      <div class="fiscal-cards-grid">${cardsHtml}</div>
      <div class="fiscal-section-title">⚠️ Alertas</div>
      <div class="fiscal-alerts-wrap">${alertsHtml}</div>
      <div class="fiscal-section-title">📜 Certidões Ativas</div>
      ${certHtml}`;
  }

  // ─── CNPJ ─────────────────────────────────────────────────────────────────
  async function consultarCNPJ() {
    const cfg = getConfig();
    const cnpj = rawCNPJ(document.getElementById('fiscal-cnpj-input').value || cfg.contribuinte_doc || '');
    if (cnpj.length < 14) { toast('Informe um CNPJ válido (14 dígitos)', 'warning'); return; }
    const btn = document.getElementById('btn-fiscal-cnpj');
    btn.disabled = true; btn.textContent = 'Consultando...';
    try {
      const resp = await apiFiscal('cnpj/consultar', 'POST', {
        contratante_cnpj: cfg.contratante_cnpj,
        autor_doc: cfg.autor_doc,
        contribuinte_doc: cnpj
      });
      renderCNPJResult(resp);
      toast('CNPJ consultado com sucesso!', 'success');
    } catch (e) {
      toast('Erro: ' + e.message, 'error');
    } finally {
      btn.disabled = false; btn.textContent = 'Consultar';
    }
  }

  function renderCNPJResult(resp) {
    const el = document.getElementById('fiscal-cnpj-result');
    if (!el) return;
    const d = resp.dados || resp.data || resp;
    el.innerHTML = `<pre class="fiscal-json">${JSON.stringify(d, null, 2)}</pre>`;
  }

  async function loadCNPJHistorico() {
    const el = document.getElementById('fiscal-cnpj-historico');
    if (!el) return;
    el.innerHTML = '<em>Carregando...</em>';
    try {
      const resp = await apiFiscal('cnpj/historico');
      const rows = resp.data || [];
      if (!rows.length) { el.innerHTML = '<p class="fiscal-empty">Sem histórico.</p>'; return; }
      el.innerHTML = `<table class="fiscal-table"><thead><tr><th>CNPJ</th><th>Consultado em</th><th>Ação</th></tr></thead>
        <tbody>${rows.map(r => `<tr>
          <td>${r.cnpj || '—'}</td>
          <td>${fmtDateTime(r.consultado_em)}</td>
          <td><button class="fiscal-btn-sm" onclick="FiscalFederal.verJSON(${encodeURIComponent(JSON.stringify(r.dados))})">Ver</button></td>
        </tr>`).join('')}</tbody></table>`;
    } catch (e) {
      el.innerHTML = `<p class="fiscal-error">${e.message}</p>`;
    }
  }

  // ─── CND ──────────────────────────────────────────────────────────────────
  async function solicitarCND() {
    const cfg = getConfig();
    try {
      const resp = await apiFiscal('cnd/solicitar', 'POST', {
        contratante_cnpj: cfg.contratante_cnpj,
        autor_doc: cfg.autor_doc,
        contribuinte_doc: rawCNPJ(document.getElementById('fiscal-cnd-cnpj').value || cfg.contribuinte_doc || '')
      });
      toast(resp.message || 'CND solicitada!', 'success');
      loadCNDLista();
    } catch (e) { toast('Erro: ' + e.message, 'error'); }
  }

  async function carregarCNDPorProtocolo() {
    const cfg = getConfig();
    const protocolo = document.getElementById('fiscal-cnd-protocolo').value.trim();
    if (!protocolo) { toast('Informe o protocolo', 'warning'); return; }
    try {
      const resp = await apiFiscal('cnd/consultar', 'POST', {
        contratante_cnpj: cfg.contratante_cnpj,
        autor_doc: cfg.autor_doc,
        contribuinte_doc: rawCNPJ(document.getElementById('fiscal-cnd-cnpj').value || cfg.contribuinte_doc || ''),
        protocolo
      });
      document.getElementById('fiscal-cnd-result').innerHTML =
        `<pre class="fiscal-json">${JSON.stringify(resp, null, 2)}</pre>`;
      toast('CND consultada!', 'success');
      loadCNDLista();
    } catch (e) { toast('Erro: ' + e.message, 'error'); }
  }

  async function loadCNDLista() {
    const el = document.getElementById('fiscal-cnd-lista');
    if (!el) return;
    try {
      const resp = await apiFiscal('cnd/lista');
      const rows = resp.data || [];
      if (!rows.length) { el.innerHTML = '<p class="fiscal-empty">Nenhuma certidão.</p>'; return; }
      el.innerHTML = `<table class="fiscal-table"><thead><tr>
        <th>CNPJ</th><th>Tipo</th><th>Número</th><th>Emissão</th><th>Vencimento</th><th>Status</th>
      </tr></thead><tbody>${rows.map(r => `<tr>
        <td>${r.cnpj || '—'}</td><td>${r.tipo || '—'}</td><td>${r.numero || '—'}</td>
        <td>${fmtDate(r.data_emissao)}</td><td>${fmtDate(r.data_vencimento)}</td>
        <td><span class="fiscal-badge fiscal-badge-${r.status === 'emitida' ? 'ok' : 'warn'}">${r.status}</span></td>
      </tr>`).join('')}</tbody></table>`;
    } catch (e) {
      el.innerHTML = `<p class="fiscal-error">${e.message}</p>`;
    }
  }

  // ─── DCTFWeb ──────────────────────────────────────────────────────────────
  async function consultarDCTFWeb() {
    const cfg = getConfig();
    const competencia = document.getElementById('fiscal-dctf-comp').value.trim();
    if (!competencia) { toast('Informe a competência (MMAAAA — ex: 032026)', 'warning'); return; }
    try {
      const resp = await apiFiscal('dctfweb/consultar', 'POST', {
        contratante_cnpj: cfg.contratante_cnpj,
        autor_doc: cfg.autor_doc,
        contribuinte_doc: rawCNPJ(document.getElementById('fiscal-dctf-cnpj').value || cfg.contribuinte_doc || ''),
        competencia: _toApiComp(competencia)
      });
      document.getElementById('fiscal-dctf-result').innerHTML =
        `<pre class="fiscal-json">${JSON.stringify(resp, null, 2)}</pre>`;
      toast('DCTFWeb consultada!', 'success');
      loadDCTFWebLista();
    } catch (e) { toast('Erro: ' + e.message, 'error'); }
  }

  async function loadDCTFWebLista() {
    const el = document.getElementById('fiscal-dctf-lista');
    if (!el) return;
    try {
      const resp = await apiFiscal('dctfweb/lista');
      const rows = resp.data || [];
      if (!rows.length) { el.innerHTML = '<p class="fiscal-empty">Nenhuma DCTFWeb.</p>'; return; }
      el.innerHTML = `<table class="fiscal-table"><thead><tr>
        <th>CNPJ</th><th>Competência</th><th>Situação</th><th>Valor Total</th><th>Consultado</th>
      </tr></thead><tbody>${rows.map(r => `<tr>
        <td>${r.cnpj || '—'}</td><td>${_fmtComp(r.competencia)}</td>
        <td>${r.situacao || '—'}</td><td>${fmtBRL(r.valor_total)}</td>
        <td>${fmtDateTime(r.consultado_em)}</td>
      </tr>`).join('')}</tbody></table>`;
    } catch (e) {
      el.innerHTML = `<p class="fiscal-error">${e.message}</p>`;
    }
  }

  // ─── MIT ──────────────────────────────────────────────────────────────────
  async function incluirMIT() {
    const cfg = getConfig();
    const dadosRaw = document.getElementById('fiscal-mit-dados').value;
    let dados = {};
    try { dados = JSON.parse(dadosRaw); } catch { toast('JSON inválido nos dados MIT', 'error'); return; }
    try {
      const resp = await apiFiscal('mit/incluir', 'POST', {
        contratante_cnpj: cfg.contratante_cnpj,
        autor_doc: cfg.autor_doc,
        contribuinte_doc: rawCNPJ(document.getElementById('fiscal-mit-cnpj').value || cfg.contribuinte_doc || ''),
        dados_mit: dados
      });
      document.getElementById('fiscal-mit-result').innerHTML =
        `<pre class="fiscal-json">${JSON.stringify(resp, null, 2)}</pre>`;
      toast('MIT incluída!', 'success');
    } catch (e) { toast('Erro: ' + e.message, 'error'); }
  }

  async function consultarMIT() {
    const cfg = getConfig();
    const protocolo = document.getElementById('fiscal-mit-protocolo').value.trim();
    if (!protocolo) { toast('Informe o protocolo', 'warning'); return; }
    try {
      const resp = await apiFiscal('mit/consultar', 'POST', {
        contratante_cnpj: cfg.contratante_cnpj,
        autor_doc: cfg.autor_doc,
        contribuinte_doc: rawCNPJ(document.getElementById('fiscal-mit-cnpj').value || cfg.contribuinte_doc || ''),
        protocolo
      });
      document.getElementById('fiscal-mit-result').innerHTML =
        `<pre class="fiscal-json">${JSON.stringify(resp, null, 2)}</pre>`;
      toast('MIT consultada!', 'success');
    } catch (e) { toast('Erro: ' + e.message, 'error'); }
  }

  // ─── REINF ────────────────────────────────────────────────────────────────
  async function consultarREINF() {
    const cfg = getConfig();
    const evento = document.getElementById('fiscal-reinf-evento').value;
    const competencia = document.getElementById('fiscal-reinf-comp').value.trim();
    if (!competencia) { toast('Informe a competência (MMAAAA — ex: 032026)', 'warning'); return; }
    try {
      const resp = await apiFiscal('reinf/consultar', 'POST', {
        contratante_cnpj: cfg.contratante_cnpj,
        autor_doc: cfg.autor_doc,
        contribuinte_doc: rawCNPJ(document.getElementById('fiscal-reinf-cnpj').value || cfg.contribuinte_doc || ''),
        evento,
        competencia: _toApiComp(competencia)
      });
      document.getElementById('fiscal-reinf-result').innerHTML =
        `<pre class="fiscal-json">${JSON.stringify(resp, null, 2)}</pre>`;
      toast('REINF consultada!', 'success');
      loadREINFLista();
    } catch (e) { toast('Erro: ' + e.message, 'error'); }
  }

  async function loadREINFLista() {
    const el = document.getElementById('fiscal-reinf-lista');
    if (!el) return;
    try {
      const resp = await apiFiscal('reinf/lista');
      const rows = resp.data || [];
      if (!rows.length) { el.innerHTML = '<p class="fiscal-empty">Nenhum REINF.</p>'; return; }
      el.innerHTML = `<table class="fiscal-table"><thead><tr>
        <th>CNPJ</th><th>Competência</th><th>Evento</th><th>Recibo</th><th>Status</th><th>Consultado</th>
      </tr></thead><tbody>${rows.map(r => `<tr>
        <td>${r.cnpj || '—'}</td><td>${_fmtComp(r.competencia)}</td>
        <td>${r.evento || '—'}</td><td>${r.recibo || '—'}</td>
        <td>${r.status || '—'}</td><td>${fmtDateTime(r.consultado_em)}</td>
      </tr>`).join('')}</tbody></table>`;
    } catch (e) {
      el.innerHTML = `<p class="fiscal-error">${e.message}</p>`;
    }
  }

  // ─── DARF ─────────────────────────────────────────────────────────────────
  function onDarfCodigoChange(sel) {
    const inp = document.getElementById('fiscal-darf-codigo');
    if (sel.value === '__outro__') {
      inp.style.display = 'block';
      inp.focus();
    } else {
      inp.style.display = 'none';
      inp.value = '';
    }
  }

  function _getDarfCodigo() {
    const sel = document.getElementById('fiscal-darf-codigo-sel');
    if (!sel) return document.getElementById('fiscal-darf-codigo').value.trim();
    if (sel.value === '__outro__') return document.getElementById('fiscal-darf-codigo').value.trim();
    return sel.value;
  }

  async function emitirDARF() {
    const cfg = getConfig();
    const campos = {
      codigo_receita: _getDarfCodigo(),
      competencia: _toApiComp(document.getElementById('fiscal-darf-comp').value.trim()),
      valor: parseFloat(document.getElementById('fiscal-darf-valor').value),
      data_vencimento: document.getElementById('fiscal-darf-venc').value.trim()
    };
    if (!campos.codigo_receita || !campos.competencia || isNaN(campos.valor)) {
      toast('Preencha código da receita, competência e valor', 'warning'); return;
    }
    try {
      const resp = await apiFiscal('darf/emitir', 'POST', {
        contratante_cnpj: cfg.contratante_cnpj,
        autor_doc: cfg.autor_doc,
        contribuinte_doc: rawCNPJ(document.getElementById('fiscal-darf-cnpj').value || cfg.contribuinte_doc || ''),
        ...campos
      });
      document.getElementById('fiscal-darf-result').innerHTML =
        `<pre class="fiscal-json">${JSON.stringify(resp, null, 2)}</pre>`;
      toast('DARF emitido!', 'success');
      loadDARFLista();
    } catch (e) { toast('Erro: ' + e.message, 'error'); }
  }

  async function verificarPagamentoDARF(darfId, protocolo) {
    const cfg = getConfig();
    try {
      const resp = await apiFiscal('darf/consultar-pagamento', 'POST', {
        contratante_cnpj: cfg.contratante_cnpj,
        autor_doc: cfg.autor_doc,
        protocolo: protocolo || '',
        darf_id: darfId || null
      });
      toast(resp.message || 'Pagamento verificado', 'info');
      loadDARFLista();
    } catch (e) { toast('Erro: ' + e.message, 'error'); }
  }

  async function loadDARFLista() {
    const el = document.getElementById('fiscal-darf-lista');
    if (!el) return;
    try {
      const resp = await apiFiscal('darf/lista');
      const rows = resp.data || [];
      if (!rows.length) { el.innerHTML = '<p class="fiscal-empty">Nenhum DARF.</p>'; return; }
      el.innerHTML = `<table class="fiscal-table"><thead><tr>
        <th>CNPJ</th><th>Cód. Receita</th><th>Competência</th><th>Valor</th>
        <th>Vencimento</th><th>Status</th><th>Ações</th>
      </tr></thead><tbody>${rows.map(r => `<tr>
        <td>${r.cnpj || '—'}</td><td>${r.codigo_receita || '—'}</td>
        <td>${r.competencia ? _fmtComp(r.competencia) : '—'}</td><td>${fmtBRL(r.valor)}</td>
        <td>${fmtDate(r.data_vencimento)}</td>
        <td><span class="fiscal-badge fiscal-badge-${r.status === 'pago' ? 'ok' : 'warn'}">${r.status}</span></td>
        <td>
          ${r.status !== 'pago' ? `<button class="fiscal-btn-sm" onclick="FiscalFederal.verificarPagamentoDARF(${r.id},'${r.protocolo || ''}')">Verificar</button>` : ''}
          ${r.pdf_base64 ? `<button class="fiscal-btn-sm" onclick="FiscalFederal.baixarPDF('${r.pdf_base64}','darf_${r.id}.pdf')">PDF</button>` : ''}
        </td>
      </tr>`).join('')}</tbody></table>`;
    } catch (e) {
      el.innerHTML = `<p class="fiscal-error">${e.message}</p>`;
    }
  }

  // ─── Logs ─────────────────────────────────────────────────────────────────
  async function loadLogs() {
    const el = document.getElementById('fiscal-logs-lista');
    if (!el) return;
    el.innerHTML = '<em>Carregando...</em>';
    const tipo = document.getElementById('fiscal-logs-tipo')?.value;
    const limite = document.getElementById('fiscal-logs-limite')?.value || 50;
    let url = `logs?limite=${limite}`;
    if (tipo) url += `&tipo=${encodeURIComponent(tipo)}`;
    try {
      const resp = await apiFiscal(url);
      const rows = resp.data || [];
      if (!rows.length) { el.innerHTML = '<p class="fiscal-empty">Sem logs.</p>'; return; }
      el.innerHTML = `<table class="fiscal-table"><thead><tr>
        <th>Data</th><th>Operação</th><th>Status HTTP</th><th>Protocolo</th><th>Ação</th>
      </tr></thead><tbody>${rows.map(r => `<tr>
        <td>${fmtDateTime(r.data)}</td>
        <td>${r.tipo_operacao || '—'}</td>
        <td><span class="fiscal-badge fiscal-badge-${parseInt(r.status_http) < 300 ? 'ok' : 'err'}">${r.status_http || '—'}</span></td>
        <td>${r.protocolo || '—'}</td>
        <td><button class="fiscal-btn-sm" onclick="FiscalFederal.verLogDetalhe(${r.id})">Ver</button></td>
      </tr>`).join('')}</tbody></table>`;
    } catch (e) {
      el.innerHTML = `<p class="fiscal-error">${e.message}</p>`;
    }
  }

  async function verLogDetalhe(id) {
    try {
      const resp = await apiFiscal(`logs/${id}`);
      const d = resp.data || resp;
      openJSONModal(`Log #${id} — ${d.tipo_operacao || ''}`, d);
    } catch (e) { toast('Erro: ' + e.message, 'error'); }
  }

  // ─── Fila ─────────────────────────────────────────────────────────────────
  async function loadFila() {
    const el = document.getElementById('fiscal-fila-lista');
    if (!el) return;
    const statusFiltro = document.getElementById('fiscal-fila-status')?.value;
    let url = 'fila';
    if (statusFiltro) url += `?status=${encodeURIComponent(statusFiltro)}`;
    el.innerHTML = '<em>Carregando...</em>';
    try {
      const resp = await apiFiscal(url);
      const rows = resp.data || [];
      if (!rows.length) { el.innerHTML = '<p class="fiscal-empty">Fila vazia.</p>'; return; }
      el.innerHTML = `<table class="fiscal-table"><thead><tr>
        <th>Tipo</th><th>Status</th><th>Tentativas</th><th>Criado</th><th>Processado</th>
      </tr></thead><tbody>${rows.map(r => `<tr>
        <td>${r.tipo || '—'}</td>
        <td><span class="fiscal-badge fiscal-badge-${r.status === 'concluido' ? 'ok' : r.status === 'erro' ? 'err' : 'warn'}">${r.status}</span></td>
        <td>${r.tentativas ?? 0}</td>
        <td>${fmtDateTime(r.criado_em)}</td>
        <td>${fmtDateTime(r.processado_em)}</td>
      </tr>`).join('')}</tbody></table>`;
    } catch (e) {
      el.innerHTML = `<p class="fiscal-error">${e.message}</p>`;
    }
  }

  // ─── JSON Modal / PDF ──────────────────────────────────────────────────────
  function openJSONModal(title, data) {
    let modal = document.getElementById('fiscal-json-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'fiscal-json-modal';
      modal.className = 'fiscal-modal-overlay';
      modal.innerHTML = `
        <div class="fiscal-modal">
          <div class="fiscal-modal-header">
            <span id="fiscal-json-modal-title"></span>
            <button onclick="document.getElementById('fiscal-json-modal').style.display='none'">✕</button>
          </div>
          <div class="fiscal-modal-body"><pre id="fiscal-json-modal-body" class="fiscal-json"></pre></div>
        </div>`;
      document.body.appendChild(modal);
    }
    document.getElementById('fiscal-json-modal-title').textContent = title;
    document.getElementById('fiscal-json-modal-body').textContent = JSON.stringify(data, null, 2);
    modal.style.display = 'flex';
  }

  function verJSON(encodedData) {
    try {
      const data = JSON.parse(decodeURIComponent(encodedData));
      openJSONModal('Dados', data);
    } catch { toast('Erro ao exibir dados', 'error'); }
  }

  function baixarPDF(base64, filename) {
    const link = document.createElement('a');
    link.href = 'data:application/pdf;base64,' + base64;
    link.download = filename;
    link.click();
  }

  // ─── Init ─────────────────────────────────────────────────────────────────
  async function init() {
    await _ensureEmpresaData();  // garante currentEmpresaData antes de aplicar config
    loadConfig();
    // Bind CNPJ masks
    document.querySelectorAll('.fiscal-cnpj-mask').forEach(el => {
      el.addEventListener('input', e => { e.target.value = maskCNPJ(e.target.value); });
    });
    // Auto-fill from config
    _applyConfigToForms();
    // Load initial tab
    loadDashboard();
    loadCNDLista();
    loadDCTFWebLista();
    loadREINFLista();
    loadDARFLista();
  }

  // Public API
  return {
    init,
    switchTab,
    openConfigModal,
    closeConfigModal,
    saveConfigFromModal,
    loadDashboard,
    consultarCNPJ,
    loadCNPJHistorico,
    solicitarCND,
    carregarCNDPorProtocolo,
    loadCNDLista,
    consultarDCTFWeb,
    loadDCTFWebLista,
    incluirMIT,
    consultarMIT,
    consultarREINF,
    loadREINFLista,
    emitirDARF,
    verificarPagamentoDARF,
    loadDARFLista,
    onDarfCodigoChange,
    loadLogs,
    verLogDetalhe,
    loadFila,
    verJSON,
    baixarPDF,
    openJSONModal
  };
})();
