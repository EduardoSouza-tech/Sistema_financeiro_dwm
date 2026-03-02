/**
 * EFD-Reinf — Módulo Completo
 * Todos os eventos, dashboard, motor inteligente, DCTFWeb sync.
 */
const ReinfModule = (function () {
  'use strict';

  // ── Estado ──────────────────────────────────────────────────────────────
  let _cfg = {};   // {contratante_cnpj, autor_doc}
  let _comp = '';  // competência atual (MMAAAA ou raw)

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
      console.warn('REINF: não foi possível carregar dados da empresa', e);
    }
  }

  // ── Helpers ──────────────────────────────────────────────────────────────
  function _toApiComp(v) {
    const d = (v || '').replace(/\D/g, '');
    if (d.length === 6) return d.slice(2) + d.slice(0, 2);
    return d;
  }
  function _fmtComp(v) {
    const s = String(v || '').replace(/\D/g, '');
    if (s.length === 6) return `${s.slice(4, 6)}/${s.slice(0, 4)}`;
    return v;
  }
  function _api(method, url, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    return fetch(url, opts).then(r => r.json());
  }
  function _toast(msg, tipo = 'success') {
    if (window.showToast) { window.showToast(msg, tipo); return; }
    const colors = { success: '#22c55e', danger: '#ef4444', warning: '#f59e0b', info: '#3b82f6' };
    const d = document.createElement('div');
    d.style.cssText = `position:fixed;top:1.5rem;right:1.5rem;z-index:9999;padding:.75rem 1.25rem;
      border-radius:8px;background:${colors[tipo] || colors.info};color:#fff;
      font-weight:600;box-shadow:0 4px 15px rgba(0,0,0,.3);max-width:380px`;
    d.textContent = msg;
    document.body.appendChild(d);
    setTimeout(() => d.remove(), 4000);
  }
  function _el(id) { return document.getElementById(id); }
  function _html(id, h) { const e = _el(id); if (e) e.innerHTML = h; }
  function _val(id) { const e = _el(id); return e ? e.value.trim() : ''; }
  function _loadCfg() {
    try { _cfg = JSON.parse(localStorage.getItem('reinf_cfg') || '{}'); } catch { _cfg = {}; }
    // Auto-preencher com CNPJ da empresa se não houver config salva
    const cnpjEmpresa = _empresaCnpj();
    if (cnpjEmpresa) {
      if (!_cfg.contratante_cnpj) _cfg.contratante_cnpj = cnpjEmpresa;
      if (!_cfg.autor_doc)        _cfg.autor_doc        = cnpjEmpresa;
    }
  }
  function _saveCfg(o) { _cfg = o; localStorage.setItem('reinf_cfg', JSON.stringify(o)); }

  // ── Catálogo de eventos ─────────────────────────────────────────────────
  const EVENTOS = {
    'R-1000': 'Informações do Contribuinte',
    'R-1070': 'Processos Administrativos/Judiciais',
    'R-2010': 'Retenção CP — Serviços Tomados',
    'R-2020': 'Retenção CP — Serviços Prestados',
    'R-2030': 'Recursos Recebidos — Assoc. Desportiva',
    'R-2040': 'Recursos Repassados — Assoc. Desportiva',
    'R-2050': 'Comercialização Produção Rural (PJ)',
    'R-2055': 'Aquisição de Produção Rural',
    'R-2060': 'CPRB — Contrib. Prev. Receita Bruta',
    'R-3010': 'Espetáculo Desportivo',
    'R-4010': 'Pagamentos/Créditos — Pessoa Física',
    'R-4020': 'Pagamentos/Créditos — Pessoa Jurídica',
    'R-4040': 'Pagamentos — Beneficiário Não Identificado',
    'R-4080': 'Retenção no Recebimento (Auto Retenção)',
    'R-4099': 'Fechamento dos Eventos Periódicos (R-4xxx)',
    'R-2098': 'Reabertura',
    'R-2099': 'Fechamento (R-2xxx)',
    'R-9000': 'Exclusão de Eventos',
    'R-9011': 'Consolidação de Bases e Tributos',
    'R-9015': 'Totalização de Bases e Tributos',
  };

  const STATUS_ICONS = {
    pendente: '⏳', enviado: '📤', processando: '🔄',
    autorizado: '✅', erro: '❌', excluido: '🗑️',
  };
  const STATUS_COLORS = {
    pendente: '#f59e0b', enviado: '#3b82f6', processando: '#8b5cf6',
    autorizado: '#22c55e', erro: '#ef4444', excluido: '#6b7280',
  };

  // ── Init ─────────────────────────────────────────────────────────────────
  async function init() {
    await _ensureEmpresaData();  // garante currentEmpresaData antes de tudo
    _loadCfg();
    _renderCompSelect();
    _bindEvents();
    const saved = sessionStorage.getItem('reinf_comp_atual');
    if (saved) {
      // Validar formato MMAAAA: primeiros 2 dígitos devem ser mês 01-12
      const mm = parseInt(saved.slice(0, 2), 10);
      if (mm >= 1 && mm <= 12 && saved.length === 6) {
        _comp = saved;
        _el('reinf-comp-sel') && (_el('reinf-comp-sel').value = saved);
      } else {
        sessionStorage.removeItem('reinf_comp_atual'); // limpa AAAAMM obsoleto
      }
    }
    _renderDashboard();
  }

  function _bindEvents() {
    const cs = _el('reinf-comp-sel');
    if (cs) cs.addEventListener('change', () => { _comp = cs.value; sessionStorage.setItem('reinf_comp_atual', _comp); _renderDashboard(); });
  }

  // ── Competência select ───────────────────────────────────────────────────
  function _renderCompSelect() {
    const sel = _el('reinf-comp-sel');
    if (!sel) return;
    _api('GET', '/api/reinf/competencias').then(r => {
      if (!r.success) return;
      const comps = r.data || [];
      // Opção atual do mês — valor SEMPRE em MMAAAA (ex: 032026)
      const now = new Date();
      const mm = String(now.getMonth() + 1).padStart(2, '0');
      const yyyy = now.getFullYear();
      const atualVal = `${mm}${yyyy}`;            // MMAAAA ← _comp usa este formato
      const atualDisplay = `${mm}/${yyyy}`;

      let opts = `<option value="${atualVal}">${atualDisplay} — Atual</option>`;
      comps.forEach(c => {
        // DB retorna AAAAMM — converte para MMAAAA para usar como value
        const s = String(c.competencia || '').replace(/\D/g, '');
        const mmaaaa = s.length === 6 ? `${s.slice(4, 6)}${s.slice(0, 4)}` : c.competencia;
        if (mmaaaa !== atualVal) {
          const lbl = `${_fmtComp(c.competencia)} — ${c.total} evento(s)`;
          opts += `<option value="${mmaaaa}">${lbl}</option>`;
        }
      });
      sel.innerHTML = opts;
      if (!_comp) _comp = sel.value;
    }).catch(() => {});
  }

  // ── Dashboard ─────────────────────────────────────────────────────────────
  function _renderDashboard() {
    if (!_comp) return;
    const cont = _el('reinf-dashboard-cont');
    if (cont) cont.innerHTML = '<div style="color:#94a3b8;padding:1rem">Carregando...</div>';

    _api('GET', `/api/reinf/dashboard/${_comp}`).then(r => {
      if (!r.success) { _html('reinf-dashboard-cont', `<p class="text-danger">${r.error}</p>`); return; }
      const d = r.data;
      const ps = d.por_status || {};
      const t  = d.totais    || {};

      const alertasHtml = (d.alertas || []).map(a =>
        `<div class="alert-chip ${a.tipo}">${a.msg}</div>`
      ).join('');

      const pendenciasHtml = (d.pendencias || []).length
        ? `<div class="reinf-pendencias">⚠️ <strong>Pendências:</strong><ul>${d.pendencias.map(p => `<li>${p}</li>`).join('')}</ul></div>`
        : '';

      const statusBadges = Object.entries(ps).map(([s, q]) =>
        `<span class="reinf-status-badge" style="background:${STATUS_COLORS[s] || '#6b7280'}">${STATUS_ICONS[s] || ''} ${q} ${s}</span>`
      ).join('');

      const fechadaTag = d.status === 'fechada'
        ? '<span class="reinf-tag fechada">🔒 Fechada</span>'
        : '<span class="reinf-tag aberta">🔓 Aberta</span>';

      const totHtml = `
        <div class="reinf-totais-grid">
          <div class="reinf-total-card"><span>Base CP</span><strong>R$ ${_fmt2(t.total_base)}</strong></div>
          <div class="reinf-total-card"><span>INSS</span><strong>R$ ${_fmt2(t.total_inss)}</strong></div>
          <div class="reinf-total-card"><span>IR</span><strong>R$ ${_fmt2(t.total_ir)}</strong></div>
          <div class="reinf-total-card"><span>CSLL</span><strong>R$ ${_fmt2(t.total_csll)}</strong></div>
          <div class="reinf-total-card"><span>PIS</span><strong>R$ ${_fmt2(t.total_pis)}</strong></div>
          <div class="reinf-total-card"><span>COFINS</span><strong>R$ ${_fmt2(t.total_cofins)}</strong></div>
        </div>`;

      const sugestoesHtml = _renderSugestoes(d.sugestoes || []);

      const eventosHtml = _renderEventosList(d.eventos || []);

      const html = `
        <div class="reinf-dashboard">
          <div class="reinf-dash-header">
            <div>
              <h3>Competência ${d.competencia}</h3>
              ${fechadaTag}
            </div>
            <div class="reinf-dash-actions">
              <button class="btn-reinf btn-sm" onclick="ReinfModule.openNovoEvento()">➕ Novo Evento</button>
              <button class="btn-reinf btn-sm secondary" onclick="ReinfModule.fecharComp()">🔒 Fechar Comp.</button>
              <button class="btn-reinf btn-sm secondary" onclick="ReinfModule.reabrirComp()">🔓 Reabrir</button>
              <button class="btn-reinf btn-sm secondary" onclick="ReinfModule.sincDctfweb()">🔄 Sinc. DCTFWeb</button>
            </div>
          </div>
          ${alertasHtml}
          ${pendenciasHtml}
          <div class="reinf-status-row">${statusBadges || '<span style="color:#64748b">Nenhum evento nesta competência.</span>'}</div>
          <div class="reinf-section-title">📊 Totalizadores</div>
          ${totHtml}
          ${sugestoesHtml}
          <div class="reinf-section-title">📋 Eventos</div>
          ${eventosHtml}
        </div>`;

      _html('reinf-dashboard-cont', html);
    }).catch(e => {
      _html('reinf-dashboard-cont', `<p class="text-danger">Erro: ${e.message}</p>`);
    });
  }

  function _fmt2(v) { return parseFloat(v || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 }); }

  function _renderSugestoes(sugestoes) {
    if (!sugestoes.length) return '';
    const rows = sugestoes.map(s => `
      <div class="reinf-sugestao-card">
        <strong>${s.evento}</strong> — ${EVENTOS[s.evento] || ''}
        <p>${s.motivo}</p>
        <button class="btn-reinf btn-xs" onclick="ReinfModule.criarPorSugestao('${s.evento}')">➕ Criar Evento</button>
      </div>`).join('');
    return `<div class="reinf-section-title">🤖 Motor Inteligente — Sugestões</div><div class="reinf-sugestoes">${rows}</div>`;
  }

  function _renderEventosList(eventos) {
    if (!eventos.length) return '<p style="color:#64748b;font-style:italic">Nenhum evento registrado.</p>';
    const rows = eventos.map(ev => `
      <tr>
        <td><strong>${ev.evento}</strong></td>
        <td style="font-size:.75rem;color:#94a3b8">${EVENTOS[ev.evento] || ''}</td>
        <td><span class="reinf-status-badge sm" style="background:${STATUS_COLORS[ev.status] || '#6b7280'}">${STATUS_ICONS[ev.status] || ''} ${ev.status}</span></td>
        <td style="font-size:.75rem">${ev.recibo || ev.protocolo || '—'}</td>
        <td style="font-size:.75rem">${ev.enviado_em ? ev.enviado_em.slice(0, 16).replace('T', ' ') : '—'}</td>
        <td>
          <button class="btn-reinf btn-xs secondary" onclick="ReinfModule.enviarEvento('${ev.id}')">📤</button>
          <button class="btn-reinf btn-xs secondary" onclick="ReinfModule.consultarStatus('${ev.id}')">🔍</button>
          <button class="btn-reinf btn-xs secondary" onclick="ReinfModule.exportarXml('${ev.id}','${ev.evento}')">⬇️ XML</button>
          <button class="btn-reinf btn-xs danger"    onclick="ReinfModule.excluirEvento('${ev.id}','${ev.evento}')">🗑️</button>
        </td>
      </tr>`).join('');
    return `
      <div style="overflow-x:auto">
        <table class="reinf-table">
          <thead><tr><th>Evento</th><th>Descrição</th><th>Status</th><th>Recibo/Protocolo</th><th>Enviado em</th><th>Ações</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  // ── Config Modal ──────────────────────────────────────────────────────────
  function openCfgModal() {
    const cnpjEmpresa = _empresaCnpj();
    _html('reinf-cfg-modal', `
      <div class="modal-backdrop" onclick="ReinfModule.closeCfgModal()">
        <div class="modal-box" onclick="event.stopPropagation()">
          <h3>⚙️ Configurações REINF</h3>
          <label>CNPJ Contratante</label>
          <input id="rcfg-contratante" class="form-control mb-2" placeholder="00.000.000/0000-00"
                 value="${_cfg.contratante_cnpj || cnpjEmpresa || ''}">
          <label>CPF/CNPJ Autor do Pedido</label>
          <input id="rcfg-autor" class="form-control mb-2" placeholder="000.000.000-00"
                 value="${_cfg.autor_doc || cnpjEmpresa || ''}">
          <div style="text-align:right;margin-top:1rem">
            <button class="btn-reinf secondary" onclick="ReinfModule.closeCfgModal()">Cancelar</button>
            <button class="btn-reinf" onclick="ReinfModule.saveCfg()">Salvar</button>
          </div>
        </div>
      </div>`);
  }
  function closeCfgModal() { _html('reinf-cfg-modal', ''); }
  function saveCfg() {
    const o = {
      contratante_cnpj: (_val('rcfg-contratante') || '').replace(/\D/g, ''),
      autor_doc:        (_val('rcfg-autor')        || '').replace(/\D/g, ''),
    };
    if (!o.contratante_cnpj || !o.autor_doc) { _toast('Preencha todos os campos.', 'warning'); return; }
    _saveCfg(o);
    closeCfgModal();
    _toast('Configurações salvas!');
  }

  // ── Novo Evento Modal ─────────────────────────────────────────────────────
  function openNovoEvento(eventoPreSel) {
    const opts = Object.entries(EVENTOS).map(([k, v]) =>
      `<option value="${k}" ${k === (eventoPreSel || '') ? 'selected' : ''}>${k} — ${v}</option>`
    ).join('');

    _html('reinf-form-modal', `
      <div class="modal-backdrop" onclick="ReinfModule.closeFormModal()">
        <div class="modal-box large" onclick="event.stopPropagation()">
          <h3>➕ Novo Evento REINF</h3>
          <div class="reinf-form-grid">
            <div>
              <label>Competência (MMAAAA)</label>
              <input id="rfe-comp" class="form-control mb-2" placeholder="032026" value="${_comp}">
            </div>
            <div>
              <label>Evento</label>
              <select id="rfe-evento" class="form-control mb-2" onchange="ReinfModule.onEventoChange()">${opts}</select>
            </div>
          </div>
          <div id="rfe-campos-dinamicos">${_camposPorEvento(eventoPreSel || 'R-4010')}</div>
          <div style="text-align:right;margin-top:1rem">
            <button class="btn-reinf secondary" onclick="ReinfModule.closeFormModal()">Cancelar</button>
            <button class="btn-reinf" onclick="ReinfModule.salvarNovoEvento()">Salvar Evento</button>
          </div>
        </div>
      </div>`);
  }
  function closeFormModal() { _html('reinf-form-modal', ''); }

  function _compToInput(apiComp) {
    if (!apiComp) return '';
    const s = String(apiComp).replace(/\D/g, '');
    if (s.length === 6) return s.slice(4, 6) + s.slice(0, 4); // AAAAMM → MMAAAA
    return s;
  }

  function onEventoChange() {
    const ev = _val('rfe-evento');
    _html('rfe-campos-dinamicos', _camposPorEvento(ev));
  }

  function _camposPorEvento(ev) {
    // Campos dinâmicos comuns por grupo de evento
    const baseRetencao = `
      <div class="reinf-form-grid">
        <div><label>CNPJ/CPF Beneficiário</label>
          <input id="rfe-cnpj" class="form-control mb-2" placeholder="00.000.000/0000-00 ou 000.000.000-00"></div>
        <div><label>Valor Base INSS (R$)</label>
          <input id="rfe-vlr-base-inss" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
        <div><label>Valor INSS (R$)</label>
          <input id="rfe-vlr-inss" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
        <div><label>Valor Base IR (R$)</label>
          <input id="rfe-vlr-base-ir" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
        <div><label>Valor IR (R$)</label>
          <input id="rfe-vlr-ir" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
        <div><label>Descrição</label>
          <input id="rfe-descricao" class="form-control mb-2" placeholder="Descrição"></div>
      </div>`;

    const r4010 = `
      <div class="reinf-form-grid">
        <div><label>CPF Beneficiário</label>
          <input id="rfe-cnpj" class="form-control mb-2" placeholder="000.000.000-00"></div>
        <div><label>Nome</label>
          <input id="rfe-nome" class="form-control mb-2" placeholder="Nome completo"></div>
        <div><label>Natureza do Rendimento</label>
          <input id="rfe-nat" class="form-control mb-2" placeholder="Ex: 13001"></div>
        <div><label>Valor Bruto (R$)</label>
          <input id="rfe-vlr-bruto" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
        <div><label>Valor IR (R$)</label>
          <input id="rfe-vlr-ir" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
        <div><label>Valor CSLL (R$)</label>
          <input id="rfe-vlr-csll" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
        <div><label>Valor PIS (R$)</label>
          <input id="rfe-vlr-pis" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
        <div><label>Valor COFINS (R$)</label>
          <input id="rfe-vlr-cofins" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
      </div>`;

    const r4020 = `
      <div class="reinf-form-grid">
        <div><label>CNPJ Beneficiário</label>
          <input id="rfe-cnpj" class="form-control mb-2" placeholder="00.000.000/0000-00"></div>
        <div><label>Razão Social</label>
          <input id="rfe-nome" class="form-control mb-2" placeholder="Razão social"></div>
        <div><label>Natureza do Rendimento</label>
          <input id="rfe-nat" class="form-control mb-2" placeholder="Ex: 22001"></div>
        <div><label>Valor Bruto (R$)</label>
          <input id="rfe-vlr-bruto" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
        <div><label>Valor IR (R$)</label>
          <input id="rfe-vlr-ir" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
        <div><label>Valor CSLL (R$)</label>
          <input id="rfe-vlr-csll" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
        <div><label>Valor PIS (R$)</label>
          <input id="rfe-vlr-pis" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
        <div><label>Valor COFINS (R$)</label>
          <input id="rfe-vlr-cofins" class="form-control mb-2" placeholder="0.00" type="number" step="0.01"></div>
      </div>`;

    const r1000 = `
      <div class="reinf-form-grid">
        <div><label>CNPJ</label>
          <input id="rfe-cnpj" class="form-control mb-2" placeholder="CNPJ do contribuinte"></div>
        <div><label>Classificação Tributária</label>
          <select id="rfe-class-trib" class="form-control mb-2">
            <option value="01">01 — Pessoa Jurídica em Geral</option>
            <option value="02">02 — Entidade Imune/Isenta</option>
            <option value="03">03 — Pessoa Física</option>
          </select></div>
        <div><label>Regime de Tributação</label>
          <select id="rfe-regime" class="form-control mb-2">
            <option value="1">Lucro Real</option>
            <option value="2">Lucro Presumido</option>
            <option value="3">Lucro Arbitrado</option>
            <option value="4">Simples Nacional</option>
          </select></div>
        <div><label>Início Vigência (MMAAAA)</label>
          <input id="rfe-inicio" class="form-control mb-2" placeholder="012020"></div>
      </div>`;

    const r9000 = `
      <div class="reinf-form-grid">
        <div><label>Evento a Excluir</label>
          <select id="rfe-ev-excluir" class="form-control mb-2">
            ${Object.keys(EVENTOS).filter(k => !['R-9000','R-2099','R-4099','R-2098'].includes(k)).map(k => `<option value="${k}">${k}</option>`).join('')}
          </select></div>
        <div><label>Número do Recibo (nrRec)</label>
          <input id="rfe-nr-rec" class="form-control mb-2" placeholder="Recibo do evento a excluir"></div>
        <div><label>Motivo</label>
          <input id="rfe-motivo" class="form-control mb-2" placeholder="Motivo da exclusão"></div>
      </div>`;

    const generico = `
      <div><label>Dados (JSON livre)</label>
        <textarea id="rfe-json-livre" class="form-control mb-2" rows="5" placeholder='{"chave": "valor"}'></textarea>
      </div>`;

    const map = {
      'R-1000': r1000,
      'R-2010': baseRetencao, 'R-2020': baseRetencao, 'R-2030': baseRetencao,
      'R-2040': baseRetencao, 'R-2050': baseRetencao, 'R-2055': baseRetencao,
      'R-2060': baseRetencao,
      'R-4010': r4010,
      'R-4020': r4020,
      'R-4040': generico, 'R-4080': generico,
      'R-9000': r9000,
    };
    return map[ev] || generico;
  }

  function _coletarDados(ev) {
    const dados = {};
    const campos = {
      'rfe-cnpj':        'cnpj',
      'rfe-nome':        'nome',
      'rfe-nat':         'natRend',
      'rfe-class-trib':  'classTrib',
      'rfe-regime':      'regimeTrib',
      'rfe-inicio':      'iniVig',
      'rfe-vlr-base-inss': 'vlrBaseInss',
      'rfe-vlr-inss':    'vlrInss',
      'rfe-vlr-base-ir': 'vlrBaseIr',
      'rfe-vlr-ir':      'vlrIr',
      'rfe-vlr-csll':    'vlrCsll',
      'rfe-vlr-pis':     'vlrPis',
      'rfe-vlr-cofins':  'vlrCofins',
      'rfe-vlr-bruto':   'vlrBruto',
      'rfe-descricao':   'descricao',
      'rfe-ev-excluir':  'evento_excluido',
      'rfe-nr-rec':      'nrRec',
      'rfe-motivo':      'motivo',
    };
    Object.entries(campos).forEach(([id, key]) => {
      const e = _el(id);
      if (e && e.value.trim()) dados[key] = e.value.trim();
    });
    const jsonLivre = _el('rfe-json-livre');
    if (jsonLivre && jsonLivre.value.trim()) {
      try { Object.assign(dados, JSON.parse(jsonLivre.value)); } catch {}
    }
    return dados;
  }

  function salvarNovoEvento() {
    const ev   = _val('rfe-evento');
    const comp = _val('rfe-comp');
    if (!ev || !comp) { _toast('Selecione evento e competência.', 'warning'); return; }

    const dados = _coletarDados(ev);

    _api('POST', '/api/reinf/evento/criar', {
      evento: ev, competencia: comp, dados
    }).then(r => {
      if (r.success) {
        _toast(`Evento ${ev} criado!`);
        closeFormModal();
        _renderDashboard();
      } else {
        _toast(`Erro: ${r.error}`, 'danger');
      }
    }).catch(e => _toast(`Erro: ${e.message}`, 'danger'));
  }

  function criarPorSugestao(evento) { openNovoEvento(evento); }

  // ── Ações de evento (lista) ───────────────────────────────────────────────
  function _cfgPayload() {
    _loadCfg();
    if (!_cfg.contratante_cnpj || !_cfg.autor_doc) {
      _toast('Configure o CNPJ Contratante e Autor do Pedido primeiro.', 'warning');
      openCfgModal();
      return null;
    }
    return { contratante_cnpj: _cfg.contratante_cnpj, autor_doc: _cfg.autor_doc };
  }

  function enviarEvento(eventoId) {
    const payload = _cfgPayload();
    if (!payload) return;
    _toast('Enviando evento…', 'info');
    _api('POST', `/api/reinf/evento/${eventoId}/enviar`, payload).then(r => {
      _toast(r.message || (r.success ? 'Enviado!' : r.error), r.success ? 'success' : 'danger');
      _renderDashboard();
    }).catch(e => _toast(`Erro: ${e.message}`, 'danger'));
  }

  function consultarStatus(eventoId) {
    const payload = _cfgPayload();
    if (!payload) return;
    _api('POST', `/api/reinf/evento/${eventoId}/consultar-status`, payload).then(r => {
      _toast(r.success ? `Status: ${r.status}` : r.error, r.success ? 'success' : 'danger');
      if (r.success) _renderDashboard();
    }).catch(e => _toast(`Erro: ${e.message}`, 'danger'));
  }

  function excluirEvento(eventoId, eventoNome) {
    if (!confirm(`Excluir evento ${eventoNome}? Se já autorizado, um R-9000 será gerado automaticamente.`)) return;
    const motivo = prompt('Informe o motivo da exclusão:', 'Exclusão corretiva') || 'Exclusão manual';
    _api('POST', `/api/reinf/evento/${eventoId}/excluir`, { motivo }).then(r => {
      _toast(r.success ? 'Evento excluído.' : r.error, r.success ? 'success' : 'danger');
      if (r.success) _renderDashboard();
    }).catch(e => _toast(`Erro: ${e.message}`, 'danger'));
  }

  function exportarXml(eventoId, eventoNome) {
    window.open(`/api/reinf/exportar-xml/${eventoId}`, '_blank');
  }

  // ── Fechamento / Reabertura ───────────────────────────────────────────────
  function fecharComp() {
    const payload = _cfgPayload();
    if (!payload) return;
    const tipo = prompt('Tipo de fechamento: R-2099 (eventos 2xxx) ou R-4099 (eventos 4xxx)? Digite o código:', 'R-2099');
    if (!tipo) return;
    if (!['R-2099', 'R-4099'].includes(tipo.toUpperCase())) { _toast('Tipo inválido.', 'warning'); return; }
    _toast('Fechando competência…', 'info');
    _api('POST', '/api/reinf/fechar', { competencia: _comp, tipo: tipo.toUpperCase(), ...payload }).then(r => {
      _toast(r.message || (r.success ? 'Fechamento enviado!' : r.error), r.success ? 'success' : 'danger');
      if (r.success) _renderDashboard();
    }).catch(e => _toast(`Erro: ${e.message}`, 'danger'));
  }

  function reabrirComp() {
    const payload = _cfgPayload();
    if (!payload) return;
    if (!confirm('Reabrir esta competência emitindo R-2098?')) return;
    _toast('Reabrindo…', 'info');
    _api('POST', '/api/reinf/reabrir', { competencia: _comp, ...payload }).then(r => {
      _toast(r.message || (r.success ? 'Reabertura enviada!' : r.error), r.success ? 'success' : 'danger');
      if (r.success) _renderDashboard();
    }).catch(e => _toast(`Erro: ${e.message}`, 'danger'));
  }

  // ── Sync DCTFWeb ──────────────────────────────────────────────────────────
  function sincDctfweb() {
    const payload = _cfgPayload();
    if (!payload) return;
    _toast('Sincronizando com DCTFWeb…', 'info');
    _api('POST', '/api/reinf/sincronizar-dctfweb', { competencia: _comp, ...payload }).then(r => {
      const cont = _el('reinf-sinc-result');
      if (!r.success) { _toast(r.error, 'danger'); return; }
      const divs = r.divergencias && r.divergencias.length
        ? `<ul style="color:#f59e0b">${r.divergencias.map(d => `<li>${d}</li>`).join('')}</ul>`
        : '<p style="color:#22c55e">✅ Valores conferem com DCTFWeb.</p>';
      _html('reinf-sinc-result', `<div class="reinf-sinc-panel"><strong>${r.message}</strong>${divs}</div>`);
      _toast(r.message, r.divergencias && r.divergencias.length ? 'warning' : 'success');
    }).catch(e => _toast(`Erro: ${e.message}`, 'danger'));
  }

  // ── API pública ───────────────────────────────────────────────────────────
  return {
    init,
    openCfgModal, closeCfgModal, saveCfg,
    openNovoEvento, closeFormModal, onEventoChange, salvarNovoEvento,
    criarPorSugestao,
    enviarEvento, consultarStatus, excluirEvento, exportarXml,
    fecharComp, reabrirComp, sincDctfweb,
    reload: _renderDashboard,
  };
})();
