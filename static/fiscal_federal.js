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
    if (typeof showToast === 'function') {
      showToast(msg, type);
    } else {
      const d = document.createElement('div');
      d.style.cssText = 'position:fixed;top:1.5rem;right:1.5rem;z-index:9999;padding:.75rem 1.25rem;border-radius:8px;background:#22c55e;color:#fff;font-weight:600;box-shadow:0 4px 15px rgba(0,0,0,.3)';
      d.textContent = msg;
      document.body.appendChild(d);
      setTimeout(() => d.remove(), 3500);
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
    // Ao abrir DARF: pré-preencher competência com mês ANTERIOR (apuração fiscal)
    if (tabId === 'darf') {
      const fc = document.getElementById('fiscal-darf-comp');
      if (fc && !fc.value) fc.value = _compAnterior();
      _calcularEPreencherVencimento();
    }
  }

  // ─── Config Modal ─────────────────────────────────────────────────────────
  // Retorna competência do mês ANTERIOR em formato MMAAAA (ex: mar/2026 → '022026')
  function _compAnterior() {
    const now = new Date();
    let m = now.getMonth(); // 0-indexed: getMonth()=2 (mar) → m=2 = fevereiro (1-indexed)
    let y = now.getFullYear();
    if (m === 0) { m = 12; y -= 1; } // janeiro → dezembro do ano anterior
    return String(m).padStart(2, '0') + String(y);
  }

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

  // ─── DCTFWeb — Dashboard Executivo ───────────────────────────────────────

  // Mapa de status da API → apresentação visual
  const API_STATUS_MAP = {
    'EM_ABERTO':        { label: 'Em Aberto',    cls: 'EM_ABERTO',        risk: 'red'    },
    'PAGO':             { label: 'Pago',          cls: 'PAGO',             risk: 'green'  },
    'PARCELADO':        { label: 'Parcelado',     cls: 'PARCELADO',        risk: 'blue'   },
    'SUSPENSO':         { label: 'Suspenso',      cls: 'SUSPENSO',         risk: 'gray'   },
    'EM_PROCESSAMENTO': { label: 'Processando',   cls: 'EM_PROCESSAMENTO', risk: 'yellow' },
  };

  function _statusBadge(api) {
    const m = API_STATUS_MAP[api] || { label: api || '—', cls: 'default' };
    return `<span class="dctf-badge dctf-badge-${m.cls}">${m.label}</span>`;
  }

  function _riskIcon(row) {
    const hoje = new Date(); hoje.setHours(0,0,0,0);
    if (row.situacao === 'PAGO') return '<span class="dctf-conc-ok" title="Pago e conciliado">✔</span>';
    if (row.data_vencimento) {
      const venc = new Date(row.data_vencimento + 'T00:00:00');
      if (venc < hoje && row.situacao !== 'PAGO') return '<span class="dctf-conc-warn" title="Vencido — pendente pagamento">⚠</span>';
    }
    return '<span class="dctf-conc-link" title="Não conciliado">🔗</span>';
  }

  let _dctfRows = [];           // cache das linhas originais
  let _dctfSortCol = null;
  let _dctfSortDir = 1;
  let _dctfPollId = null;

  async function consultarDCTFWeb() {
    const cfg = getConfig();
    const competencia = document.getElementById('fiscal-dctf-comp').value.trim();
    if (!competencia) { toast('Informe a competência (MMAAAA — ex: 032026)', 'warning'); return; }
    const btn = document.querySelector('.dctf-btn-primary');
    if (btn) { btn.textContent = '⌛ Consultando...'; btn.disabled = true; }
    try {
      await apiFiscal('dctfweb/consultar', 'POST', {
        contratante_cnpj: cfg.contratante_cnpj,
        autor_doc: cfg.autor_doc,
        contribuinte_doc: rawCNPJ(document.getElementById('fiscal-dctf-cnpj').value || cfg.contribuinte_doc || ''),
        competencia: _toApiComp(competencia)
      });
      toast('DCTFWeb consultada com sucesso!', 'success');
      loadDCTFWebLista();
    } catch (e) { toast('Erro: ' + e.message, 'error'); }
    finally { if (btn) { btn.textContent = '📊 Consultar'; btn.disabled = false; } }
  }

  async function loadDCTFWebLista() {
    const el = document.getElementById('fiscal-dctf-lista');
    if (!el) return;
    el.innerHTML = '<div class="dctf-empty-state">⌛ Carregando...</div>';
    try {
      const resp = await apiFiscal('dctfweb/lista');
      _dctfRows = resp.data || [];
      _atualizarCards();
      _renderDCTFAlerts();
      _renderDCTFTable(_dctfRows);
    } catch (e) {
      el.innerHTML = `<div class="dctf-empty-state" style="color:#dc2626">❌ ${e.message}</div>`;
    }
  }

  function _atualizarCards() {
    const hoje = new Date(); hoje.setHours(0,0,0,0);
    let aberto = 0, pago = 0, vencido = 0, aVencer = 0;
    let ultimaTrans = '—', ultimoRecibo = '—';
    _dctfRows.forEach(r => {
      const val = Number(r.valor_total || r.valor || 0);
      const status = (r.situacao || '').toUpperCase();
      if (status === 'PAGO') { pago += val; return; }
      if (status === 'EM_ABERTO' || !status) {
        aberto += val;
        if (r.data_vencimento) {
          const venc = new Date(r.data_vencimento + 'T00:00:00');
          if (venc < hoje) vencido += val; else aVencer += val;
        } else { aVencer += val; }
      }
      if (r.consultado_em && ultimaTrans === '—') ultimaTrans = fmtDateTime(r.consultado_em);
      if (r.recibo && ultimoRecibo === '—') ultimoRecibo = r.recibo;
    });
    const upd = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    upd('dctf-c-aberto', fmtBRL(aberto));
    upd('dctf-c-pago', fmtBRL(pago));
    upd('dctf-c-vencido', fmtBRL(vencido));
    upd('dctf-c-vencer', fmtBRL(aVencer));
    upd('dctf-c-transmissao', ultimaTrans);
    upd('dctf-c-recibo', ultimoRecibo);
  }

  function _renderDCTFAlerts() {
    const el = document.getElementById('dctf-alertas-banner');
    if (!el) return;
    const hoje = new Date(); hoje.setHours(0,0,0,0);
    const em3 = new Date(hoje); em3.setDate(em3.getDate() + 3);
    const alertas = [];
    let semTransmissao = _dctfRows.length === 0;
    _dctfRows.forEach(r => {
      const status = (r.situacao || '').toUpperCase();
      if (status === 'PAGO') return;
      if (r.data_vencimento) {
        const venc = new Date(r.data_vencimento + 'T00:00:00');
        if (venc < hoje)   alertas.push({ tipo:'danger', msg:`⚠ Débito vencido: ${r.tributo || r.codigo_receita || ''} — ${_fmtComp(r.competencia)} (${fmtBRL(r.valor_total || 0)})` });
        else if (venc <= em3) alertas.push({ tipo:'warn',   msg:`⏰ Vence em breve: ${r.tributo || r.codigo_receita || ''} — ${_fmtComp(r.competencia)} (${fmtBRL(r.valor_total || 0)})` });
      }
    });
    if (semTransmissao) alertas.push({ tipo:'info', msg:'ℹ DCTFWeb não transmitida nesta competência. Consulte ou transmita.' });
    el.innerHTML = alertas.map(a => `<div class="dctf-alert-bar ${a.tipo}">${a.msg}</div>`).join('');
  }

  function _renderDCTFTable(rows) {
    const el = document.getElementById('fiscal-dctf-lista');
    if (!el) return;
    if (!rows.length) {
      el.innerHTML = '<div class="dctf-empty-state">📭 Nenhum débito encontrado para os filtros aplicados.</div>';
      const cnt = document.getElementById('dctf-f-count');
      if (cnt) cnt.textContent = '0 registros';
      return;
    }
    const hoje = new Date(); hoje.setHours(0,0,0,0);
    const cols = [
      { key:'competencia',     label:'Competência',     fmt: v => _fmtComp(v) },
      { key:'codigo_receita',  label:'Cód. Receita',    fmt: v => v || '—' },
      { key:'tributo',         label:'Tributo',         fmt: v => v || '—' },
      { key:'valor_principal', label:'Principal',       fmt: v => fmtBRL(Number(v||0)), cls:'td-valor' },
      { key:'multa',           label:'Multa',           fmt: v => fmtBRL(Number(v||0)), cls:'td-valor' },
      { key:'juros',           label:'Juros',           fmt: v => fmtBRL(Number(v||0)), cls:'td-valor' },
      { key:'valor_total',     label:'Total Atualizado',fmt: v => fmtBRL(Number(v||0)), cls:'td-valor' },
      { key:'data_vencimento', label:'Vencimento',      fmt: v => v ? v.slice(0,10) : '—' },
      { key:'situacao',        label:'Situação',        fmt: v => _statusBadge(v) },
      { key:'_risco',          label:'',                fmt: (v,row) => _riskIcon(row) },
    ];
    const thead = cols.map((c,i) => {
      const sc = _dctfSortCol === i ? (_dctfSortDir === 1 ? ' sorted-asc' : ' sorted-desc') : '';
      return `<th class="${sc}" onclick="FiscalFederal.dctfSort(${i})">${c.label}</th>`;
    }).join('');
    const tbody = rows.map(r => {
      let rowCls = '';
      const status = (r.situacao || '').toUpperCase();
      if (r.data_vencimento && status !== 'PAGO') {
        const venc = new Date(r.data_vencimento + 'T00:00:00');
        if (venc < hoje) rowCls = ' row-vencido';
      }
      const tds = cols.map(c => {
        const v = c.key === '_risco' ? null : r[c.key];
        const val = c.fmt(v, r);
        return `<td class="${c.cls||''}">${val}</td>`;
      }).join('');
      const dataStr = encodeURIComponent(JSON.stringify(r));
      return `<tr class="${rowCls}" onclick="FiscalFederal.dctfDrawerOpen('${dataStr}')">${tds}</tr>`;
    }).join('');
    el.innerHTML = `<table class="dctf-table"><thead><tr>${thead}</tr></thead><tbody>${tbody}</tbody></table>`;
    const cnt = document.getElementById('dctf-f-count');
    if (cnt) cnt.textContent = `${rows.length} registro(s)`;
  }

  function dctfFiltrar() {
    const fComp   = (document.getElementById('dctf-f-comp')?.value   || '').toLowerCase();
    const fTribu  = (document.getElementById('dctf-f-tributo')?.value || '').toLowerCase();
    const fStatus = (document.getElementById('dctf-f-status')?.value  || '').toLowerCase();
    const filtered = _dctfRows.filter(r => {
      if (fComp   && !(_fmtComp(r.competencia) || '').toLowerCase().includes(fComp))   return false;
      if (fTribu  && !(r.tributo || '').toLowerCase().includes(fTribu))                 return false;
      if (fStatus && !(r.situacao || '').toLowerCase().includes(fStatus))               return false;
      return true;
    });
    _renderDCTFTable(filtered);
  }

  function dctfLimparFiltros() {
    ['dctf-f-comp','dctf-f-tributo','dctf-f-status'].forEach(id => {
      const el = document.getElementById(id); if (el) el.value = '';
    });
    _renderDCTFTable(_dctfRows);
  }

  function dctfSort(colIdx) {
    const cols = ['competencia','codigo_receita','tributo','valor_principal','multa','juros','valor_total','data_vencimento','situacao'];
    const key = cols[colIdx];
    if (!key) return;
    if (_dctfSortCol === colIdx) _dctfSortDir *= -1; else { _dctfSortCol = colIdx; _dctfSortDir = 1; }
    const sorted = [..._dctfRows].sort((a, b) => {
      const av = a[key] || ''; const bv = b[key] || '';
      return av < bv ? -_dctfSortDir : av > bv ? _dctfSortDir : 0;
    });
    _renderDCTFTable(sorted);
  }

  function dctfDrawerOpen(dataStr) {
    const row = JSON.parse(decodeURIComponent(dataStr));
    const drawer = document.getElementById('dctf-drawer');
    const body   = document.getElementById('dctf-drawer-body');
    if (!drawer || !body) return;
    const fields = [
      ['Competência',      _fmtComp(row.competencia)],
      ['Código Receita',   row.codigo_receita || '—'],
      ['Tributo',          row.tributo || '—'],
      ['Situação',         _statusBadge(row.situacao)],
      ['Valor Principal',  fmtBRL(Number(row.valor_principal||0))],
      ['Multa',            fmtBRL(Number(row.multa||0))],
      ['Juros',            fmtBRL(Number(row.juros||0))],
      ['Total Atualizado', fmtBRL(Number(row.valor_total||0))],
      ['Data Vencimento',  row.data_vencimento ? row.data_vencimento.slice(0,10) : '—'],
      ['Protocolo',        row.protocolo || '—'],
      ['Origem',           row.origem || 'DCTFWeb'],
      ['Recibo',           row.recibo || '—'],
      ['Consultado em',    fmtDateTime(row.consultado_em)],
      ['CNPJ',             row.cnpj || '—'],
    ];
    const rowsHtml = fields.map(([k,v]) =>
      `<div class="dctf-drawer-row"><span class="dctf-drawer-key">${k}</span><span class="dctf-drawer-val">${v}</span></div>`
    ).join('');
    body.innerHTML = `
      ${rowsHtml}
      <div class="dctf-drawer-btns">
        <button class="dctf-drawer-btn" onclick="FiscalFederal.emitirDARFFromDebito(${encodeURIComponent(JSON.stringify(row))})">🧾 Emitir DARF</button>
        <button class="dctf-drawer-btn" onclick="FiscalFederal.consultarPagamento('${row.protocolo||''}')">💳 Consultar Pagamento</button>
        <button class="dctf-drawer-btn" onclick="alert('Comprovante não disponível para este débito.')">📥 Baixar Comprovante</button>
        <button class="dctf-drawer-btn" onclick="FiscalFederal.verEventoOrigem('${row.origem||''}','${row.competencia||''}')">📋 Ver Evento Origem</button>
      </div>`;
    drawer.style.display = 'block';
  }

  function dctfDrawerClose() {
    const d = document.getElementById('dctf-drawer');
    if (d) d.style.display = 'none';
  }

  function emitirDARFFromDebito(rowStr) {
    const row = typeof rowStr === 'string' ? JSON.parse(decodeURIComponent(rowStr)) : rowStr;
    dctfDrawerClose();
    // Pré-preencher aba DARF e trocar de tab
    setTimeout(() => {
      const tabBtn = document.querySelector('[data-fiscal-tab="darf"]');
      if (tabBtn) tabBtn.click();
      setTimeout(() => {
        const fComp   = document.getElementById('fiscal-darf-comp');
        const fCodSel = document.getElementById('fiscal-darf-codigo-sel');
        if (fComp)   fComp.value   = _compToDisplay(row.competencia);
        if (fCodSel) fCodSel.value = row.codigo_receita || '';
      }, 200);
    }, 100);
  }

  function consultarPagamento(protocolo) {
    toast('Consulta de pagamento: ' + (protocolo || 'sem protocolo'), 'info');
  }

  function verEventoOrigem(origem, competencia) {
    const tabBtn = document.querySelector('[data-fiscal-tab="reinf"]') || document.querySelector('[data-fiscal-tab="dctfweb"]');
    if (tabBtn) tabBtn.click();
    toast(`Evento origem: ${origem} — Competência: ${_fmtComp(competencia)}`, 'info');
  }

  function _compToDisplay(aaaamm) {
    const s = String(aaaamm || '').replace(/\D/g,'');
    if (s.length === 6) return s.slice(4) + s.slice(0,4); // AAAAMM→MMAAAA
    return aaaamm;
  }

  function dctfPollToggle() {
    const btn = document.getElementById('dctf-poll-btn');
    if (_dctfPollId) {
      clearInterval(_dctfPollId); _dctfPollId = null;
      if (btn) { btn.textContent = '⏱ Auto'; btn.classList.remove('active'); }
      toast('Atualização automática desativada', 'info');
    } else {
      _dctfPollId = setInterval(loadDCTFWebLista, 30000);
      if (btn) { btn.textContent = '⏱ Auto ●'; btn.classList.add('active'); }
      toast('Atualizando a cada 30s', 'success');
    }
  }

  // ─── MIT ──────────────────────────────────────────────────────────────────

  const MIT_TIMELINE = ['Criado', 'Enviado', 'Processado', 'Aceito'];
  const MIT_STATUS_STEP = { criado:0, enviado:1, processado:2, aceito:3, rejeitado:3 };

  function mitNovaModal() {
    const modal = document.getElementById('mit-modal');
    if (modal) modal.style.display = 'block';
  }
  function mitFecharModal() {
    const modal = document.getElementById('mit-modal');
    if (modal) modal.style.display = 'none';
  }

  async function incluirMIT() {
    const cfg = getConfig();
    const dadosRaw = document.getElementById('fiscal-mit-dados').value;
    let dados = {};
    try { dados = JSON.parse(dadosRaw); } catch { toast('JSON inválido nos dados MIT', 'error'); return; }
    const resEl = document.getElementById('fiscal-mit-result');
    if (resEl) resEl.innerHTML = '<div style="color:#64748b;font-size:12px">⌛ Enviando...</div>';
    try {
      const resp = await apiFiscal('mit/incluir', 'POST', {
        contratante_cnpj: cfg.contratante_cnpj,
        autor_doc: cfg.autor_doc,
        contribuinte_doc: rawCNPJ(document.getElementById('fiscal-mit-cnpj').value || cfg.contribuinte_doc || ''),
        dados_mit: dados
      });
      if (resEl) resEl.innerHTML =
        `<div class="dctf-alert-bar info" style="margin-top:8px">✅ MIT incluída com sucesso! Protocolo: <strong>${resp.protocolo || '—'}</strong></div>`;
      toast('MIT incluída!', 'success');
      mitFecharModal();
      loadMITLista();
    } catch (e) {
      if (resEl) resEl.innerHTML = `<div class="dctf-alert-bar danger" style="margin-top:8px">❌ ${e.message}</div>`;
      toast('Erro: ' + e.message, 'error');
    }
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
      toast('MIT consultada!', 'success');
      const rows = Array.isArray(resp.data) ? resp.data : (resp.data ? [resp.data] : []);
      _renderMITLista(rows);
    } catch (e) { toast('Erro: ' + e.message, 'error'); }
  }

  async function loadMITLista() {
    const el = document.getElementById('mit-lista-cont');
    if (!el) return;
    el.innerHTML = '<div class="dctf-empty-state">⌛ Carregando...</div>';
    try {
      const resp = await apiFiscal('mit/lista');
      const rows = resp.data || [];
      _atualizarCardsMIT(rows);
      _renderMITAlerts(rows);
      _renderMITLista(rows);
    } catch (e) {
      el.innerHTML = `<div class="dctf-empty-state" style="color:#dc2626">❌ ${e.message}</div>`;
    }
  }

  function _atualizarCardsMIT(rows) {
    let total=0, aceitas=0, rejeitadas=0, pend=0;
    rows.forEach(r => {
      total++;
      const s = (r.status||'').toLowerCase();
      if (s==='aceito') aceitas++;
      else if (s==='rejeitado') rejeitadas++;
      else pend++;
    });
    const upd = (id, v) => { const el=document.getElementById(id); if(el) el.textContent=v; };
    upd('mit-c-total', total); upd('mit-c-aceitas', aceitas);
    upd('mit-c-rejeitadas', rejeitadas); upd('mit-c-pendentes', pend);
  }

  function _renderMITAlerts(rows) {
    const el = document.getElementById('mit-alertas-banner');
    if (!el) return;
    const alertas = [];
    const rejeits = rows.filter(r => (r.status||'').toLowerCase()==='rejeitado');
    const pends   = rows.filter(r => ['criado','enviado'].includes((r.status||'').toLowerCase()));
    if (rejeits.length) alertas.push({ tipo:'danger', msg:`❌ ${rejeits.length} MIT(s) rejeitada(s). Verifique os erros de validação.` });
    if (pends.length)   alertas.push({ tipo:'warn',   msg:`⏳ ${pends.length} MIT(s) pendente(s) de processamento.` });
    el.innerHTML = alertas.map(a => `<div class="dctf-alert-bar ${a.tipo}">${a.msg}</div>`).join('');
  }

  function _renderMITLista(rows) {
    const el = document.getElementById('mit-lista-cont');
    if (!el) return;
    if (!rows.length) {
      el.innerHTML = '<div class="dctf-empty-state">📭 Nenhuma MIT encontrada.</div>';
      return;
    }
    el.innerHTML = rows.map(r => {
      const status = (r.status || 'criado').toLowerCase();
      const step   = MIT_STATUS_STEP[status] ?? 0;
      const isRej  = status === 'rejeitado';
      const timeline = MIT_TIMELINE.map((lbl, i) => {
        let dotCls = '';
        if (isRej && i === 3)          dotCls = 'error';
        else if (i < step)             dotCls = 'done';
        else if (i === step)           dotCls = 'active';
        const icon = dotCls==='done'?'✓': dotCls==='error'?'✗': dotCls==='active'?'●':'○';
        const tlLbl = i===3 && isRej ? 'Rejeitado' : lbl;
        return `<div class="mit-tl-step">
          <div class="mit-tl-dot ${dotCls}">${icon}</div>
          <div class="mit-tl-label">${tlLbl}</div>
        </div>`;
      }).join('');
      const errosHtml = (r.erros && r.erros.length)
        ? `<div class="mit-erros">⛔ Erros de validação:<ul>${r.erros.map(e=>`<li>${e}</li>`).join('')}</ul></div>`
        : '';
      return `<div class="mit-item">
        <div class="mit-item-header">
          <span class="mit-item-proto">📋 ${r.protocolo || 'Sem protocolo'}</span>
          ${_statusBadge(r.status?.toUpperCase() || 'EM_PROCESSAMENTO')}
        </div>
        <div style="font-size:11px;color:#64748b;margin-bottom:6px">
          Nº Controle: <strong>${r.numero_controle || '—'}</strong> &nbsp;|&nbsp;
          Competência: <strong>${_fmtComp(r.competencia)}</strong> &nbsp;|&nbsp;
          Enviado: <strong>${fmtDateTime(r.enviado_em)}</strong>
        </div>
        <div class="mit-timeline">${timeline}</div>
        ${errosHtml}
      </div>`;
    }).join('');
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
  // ─── Motor de Vencimento DARF ─────────────────────────────────────────────
  // Regras: { dia_base, mes_offset } por código de receita
  const DARF_REGRAS = {
    // PIS
    '8109': { tributo:'PIS Cumulativo',       dia: 25, offset: 1 },
    '6912': { tributo:'PIS Não Cumulativo',    dia: 25, offset: 1 },
    '5952': { tributo:'PIS Retido na Fonte',   dia: 25, offset: 1 },
    // COFINS
    '2172': { tributo:'COFINS Cumulativa',     dia: 25, offset: 1 },
    '5856': { tributo:'COFINS Não Cumulativa', dia: 25, offset: 1 },
    '5960': { tributo:'COFINS Retida Fonte',   dia: 25, offset: 1 },
    // CSLL
    '2372': { tributo:'CSLL Lucro Presumido',  dia: 30, offset: 1 },
    '2484': { tributo:'CSLL Lucro Real',       dia: 30, offset: 1 },
    '2370': { tributo:'CSLL Retida Fonte',     dia: 25, offset: 1 },
    // IRPJ
    '2089': { tributo:'IRPJ Lucro Presumido',  dia: 30, offset: 1 },
    '2120': { tributo:'IRPJ Lucro Real',       dia: 30, offset: 1 },
    '2088': { tributo:'IRPJ Ajuste Anual',     dia: 31, offset: 3 },
    // IRRF
    '0561': { tributo:'IRRF',                  dia: 20, offset: 1 },
    // IRPF
    '0190': { tributo:'IRPF Carnê-Leão',       dia: 31, offset: 1 },
    '4600': { tributo:'IRPF Ganho de Capital', dia: 31, offset: 1 },
    '1889': { tributo:'IRPF Rendimentos',      dia: 31, offset: 1 },
  };

  // Feriados nacionais fixos e de 2025-2027 (lei 6.802/80 e correlatas)
  const _FERIADOS = new Set([
    // Feriados fixos (repetem todo ano) — gerados para 2025-2027
    ...([2025,2026,2027].flatMap(y => [
      `${y}-01-01`, // Ano Novo
      `${y}-04-21`, // Tiradentes
      `${y}-05-01`, // Trabalho
      `${y}-09-07`, // Independência
      `${y}-10-12`, // N.Sra.Aparecida
      `${y}-11-02`, // Finados
      `${y}-11-15`, // Proclamação República
      `${y}-11-20`, // Consciência Negra
      `${y}-12-25`, // Natal
    ])),
    // Páscoa e Carnaval (móveis)
    '2025-03-04','2025-03-05','2025-04-18','2025-04-20',
    '2026-02-17','2026-02-18','2026-04-03','2026-04-05',
    '2027-02-09','2027-02-10','2027-03-26','2027-03-28',
    // Corpus Christi
    '2025-06-19','2026-06-04','2027-05-27',
  ]);

  // Retorna o dia útil anterior se d for fim de semana/feriado
  function _diaUtilAnterior(d) {
    const dt = new Date(d);
    while (dt.getDay() === 0 || dt.getDay() === 6 || _FERIADOS.has(_isoDate(dt))) {
      dt.setDate(dt.getDate() - 1);
    }
    return dt;
  }

  function _isoDate(d) {
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  }

  // Último dia real do mês (para dia_base >= 29)
  function _lastDayOfMonth(y, m) {
    return new Date(y, m, 0).getDate(); // m é 1-based, new Date(y,m,0) = último dia de (m-1)
  }

  /**
   * Calcula o vencimento dado código e competência (MMAAAA).
   * Retorna { iso, display, ddmmaaaa, tributo, regra } ou null.
   */
  function calcularVencimentoDARF(codigo, competencia) {
    const regra = DARF_REGRAS[String(codigo).trim()];
    if (!regra || !competencia) return null;
    const s = String(competencia).replace(/\D/g,'');
    if (s.length !== 6) return null;
    const mm = parseInt(s.slice(0,2), 10); // entrada MMAAAA
    const yyyy = parseInt(s.slice(2,6), 10);
    if (mm < 1 || mm > 12) return null;

    // Mês/ano destino após aplicar offset
    let dstMonth = mm + regra.offset; // 1-based
    let dstYear  = yyyy;
    while (dstMonth > 12) { dstMonth -= 12; dstYear++; }

    // Dia base (clamped ao último dia do mês)
    const ultimo = _lastDayOfMonth(dstYear, dstMonth);
    const diaBase = Math.min(regra.dia, ultimo);

    // Data base (UTC para evitar TZ issues)
    const base = new Date(`${dstYear}-${String(dstMonth).padStart(2,'0')}-${String(diaBase).padStart(2,'0')}T12:00:00`);
    const util = _diaUtilAnterior(base);

    const dd   = String(util.getDate()).padStart(2,'0');
    const mOut = String(util.getMonth()+1).padStart(2,'0');
    const aaaa = util.getFullYear();
    return {
      iso:      `${aaaa}-${mOut}-${dd}`,
      display:  `${dd}/${mOut}/${aaaa}`,
      ddmmaaaa: `${dd}${mOut}${aaaa}`,
      tributo:  regra.tributo,
      ajustado: util.getDate() !== diaBase,
    };
  }

  function _calcularEPreencherVencimento() {
    let codigo = _getDarfCodigo();
    const comp = (document.getElementById('fiscal-darf-comp')?.value || '').trim();
    const badge = document.getElementById('darf-venc-badge');
    const inp   = document.getElementById('fiscal-darf-venc');
    if (!codigo || !comp || comp.length !== 6) {
      if (badge) badge.style.display = 'none';
      return;
    }
    const r = calcularVencimentoDARF(codigo, comp);
    if (!r) { if (badge) badge.style.display = 'none'; return; }
    // Preencher campo (ISO para <input type="date">)
    if (inp) inp.value = r.iso;
    // Badge informativo
    if (badge) {
      badge.style.display = 'flex';
      badge.innerHTML = `<span style="color:#059669">✔ Calculado automaticamente</span>
        <span style="color:#64748b">${r.tributo} — vence <strong>${r.display}</strong>${r.ajustado ? ' <em>(antecipado — feriado/fim de semana)</em>' : ''}</span>`;
    }
  }

  function onDarfCodigoChange(sel) {
    const inp = document.getElementById('fiscal-darf-codigo');
    if (sel.value === '__outro__') {
      inp.style.display = 'block';
      inp.focus();
    } else {
      inp.style.display = 'none';
      inp.value = '';
    }
    _calcularEPreencherVencimento();
  }

  function onDarfCompChange() {
    _calcularEPreencherVencimento();
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
    dctfFiltrar,
    dctfLimparFiltros,
    dctfSort,
    dctfDrawerOpen,
    dctfDrawerClose,
    dctfPollToggle,
    emitirDARFFromDebito,
    consultarPagamento,
    verEventoOrigem,
    incluirMIT,
    consultarMIT,
    loadMITLista,
    mitNovaModal,
    mitFecharModal,
    consultarREINF,
    loadREINFLista,
    emitirDARF,
    verificarPagamentoDARF,
    loadDARFLista,
    onDarfCodigoChange,
    onDarfCompChange,
    calcularVencimentoDARF,
    loadLogs,
    verLogDetalhe,
    loadFila,
    verJSON,
    baixarPDF,
    openJSONModal
  };
})();
