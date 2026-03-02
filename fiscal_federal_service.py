"""
Módulo Fiscal Federal — Integra Contador API SERPRO
Serviços: CNPJ, CND, DCTFWeb, MIT, REINF, DARF, Pagamentos
Cada função constrói o payload correto e chama a API via integra_contador_functions
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)

# ─── Helpers ────────────────────────────────────────────────────────────────

def _limpar_doc(doc: str) -> str:
    """Remove pontuação de CPF/CNPJ."""
    return ''.join(c for c in (doc or '') if c.isdigit())


def _tipo_doc(doc: str) -> int:
    """1=CPF (11 dígitos), 2=CNPJ (14 dígitos)."""
    d = _limpar_doc(doc)
    return 1 if len(d) == 11 else 2


def _pedido(id_sistema: str, id_servico: str, dados: dict, versao: str = '1.0') -> dict:
    return {
        'idSistema': id_sistema,
        'idServico': id_servico,
        'versaoSistema': versao,
        'dados': json.dumps(dados, ensure_ascii=False),
    }


def _build_payload(
    contratante_cnpj: str,
    autor_doc: str,
    contribuinte_doc: str,
    pedido: dict,
) -> dict:
    cn = _limpar_doc(contratante_cnpj)
    ad = _limpar_doc(autor_doc)
    cd = _limpar_doc(contribuinte_doc)
    return {
        'contratante': {'numero': cn, 'tipo': 2},
        'autorPedidoDados': {'numero': ad, 'tipo': _tipo_doc(autor_doc)},
        'contribuinte': {'numero': cd, 'tipo': _tipo_doc(contribuinte_doc)},
        'pedidoDados': pedido,
    }


def _salvar_log(db, empresa_id, tipo_operacao, endpoint, request_data, response_data, status_http, protocolo=None):
    """Grava log na tabela logs_fiscais (best-effort, não bloqueia em erro)."""
    try:
        import psycopg2.extras
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO logs_fiscais
                    (empresa_id, tipo_operacao, endpoint, request, response, status_http, protocolo, data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                empresa_id,
                tipo_operacao,
                endpoint,
                json.dumps(request_data, ensure_ascii=False, default=str),
                json.dumps(response_data, ensure_ascii=False, default=str),
                status_http,
                protocolo,
            ))
            conn.commit()
            cur.close()
    except Exception as e:
        logger.warning(f"⚠️ Não foi possível salvar log fiscal: {e}")


def _chamada(tipo_operacao, payload):
    """Chama integra_contador_functions com retry em 429."""
    from integra_contador_functions import enviar_requisicao
    for tentativa in range(3):
        resultado = enviar_requisicao(tipo_operacao, payload)
        if resultado.get('status_code') == 429:
            import time
            espera = 2 ** tentativa
            logger.warning(f"Rate limit (429). Aguardando {espera}s... tentativa {tentativa+1}/3")
            time.sleep(espera)
            continue
        return resultado
    return resultado   # última tentativa


# ─── Módulo CNPJ ────────────────────────────────────────────────────────────

def consultar_cnpj(db, empresa_id, contratante_cnpj, autor_doc, cnpj_consultar):
    """Consulta dados completos de um CNPJ."""
    cnpj_limpo = _limpar_doc(cnpj_consultar)
    cnpj_base  = cnpj_limpo[:8]   # 8 primeiros = raiz CNPJ

    payload = _build_payload(
        contratante_cnpj, autor_doc, cnpj_limpo,
        _pedido('ReceitaFederal', 'consultar-dados-cadastrais-pj',
                {'cnpjBasico': cnpj_base})
    )

    resultado = _chamada('Consultar', payload)
    http_code = resultado.get('status_code', 0)
    _salvar_log(db, empresa_id, 'CNPJ', 'Consultar/consultar-dados-cadastrais-pj',
                {'cnpj': cnpj_limpo}, resultado, http_code)

    if resultado.get('success'):
        # Salvar histórico
        try:
            import psycopg2.extras
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO fiscal_cnpj_historico (empresa_id, cnpj, dados, consultado_em)
                    VALUES (%s, %s, %s, NOW())
                """, (empresa_id, cnpj_limpo,
                      json.dumps(resultado.get('data', {}), default=str)))
                conn.commit()
                cur.close()
        except Exception as e:
            logger.warning(f"Não foi possível salvar histórico CNPJ: {e}")

    return resultado


def listar_historico_cnpj(db, empresa_id, cnpj=None):
    """Lista histórico de consultas CNPJ da empresa."""
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        q = "SELECT * FROM fiscal_cnpj_historico WHERE empresa_id = %s"
        p = [empresa_id]
        if cnpj:
            q += " AND cnpj = %s"
            p.append(_limpar_doc(cnpj))
        q += " ORDER BY consultado_em DESC LIMIT 100"
        cur.execute(q, p)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
    return rows


# ─── Módulo CND ─────────────────────────────────────────────────────────────

def solicitar_cnd(db, empresa_id, contratante_cnpj, autor_doc, contribuinte_doc):
    """Solicita Certidão Negativa de Débitos (CND) Federal."""
    cd = _limpar_doc(contribuinte_doc)
    payload = _build_payload(
        contratante_cnpj, autor_doc, cd,
        _pedido('CND', 'emitir-certidao-negativa-debitos', {'ni': cd})
    )
    resultado = _chamada('Emitir', payload)
    http_code = resultado.get('status_code', 0)
    protocolo = resultado.get('data', {}).get('protocolo') or resultado.get('data', {}).get('nrProtocolo')
    _salvar_log(db, empresa_id, 'CND_SOLICITAR', 'Emitir/emitir-certidao-negativa-debitos',
                {'ni': cd}, resultado, http_code, protocolo)

    if resultado.get('success'):
        _salvar_certidao(db, empresa_id, cd, resultado, protocolo)

    return resultado


def consultar_cnd(db, empresa_id, contratante_cnpj, autor_doc, contribuinte_doc):
    """Consulta situação da CND de um contribuinte."""
    cd = _limpar_doc(contribuinte_doc)
    payload = _build_payload(
        contratante_cnpj, autor_doc, cd,
        _pedido('CND', 'consultar-situacao-certidao', {'ni': cd})
    )
    resultado = _chamada('Consultar', payload)
    http_code = resultado.get('status_code', 0)
    _salvar_log(db, empresa_id, 'CND_CONSULTAR', 'Consultar/consultar-situacao-certidao',
                {'ni': cd}, resultado, http_code)
    return resultado


def _salvar_certidao(db, empresa_id, cnpj, resultado, protocolo):
    """Salva certidão no banco."""
    try:
        data = resultado.get('data', {})
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO fiscal_certidoes
                    (empresa_id, cnpj, tipo, numero, data_emissao, data_vencimento,
                     pdf_base64, status, protocolo, criado_em)
                VALUES (%s, %s, 'CND_FEDERAL', %s, %s, %s, %s, %s, %s, NOW())
            """, (
                empresa_id, cnpj,
                data.get('numeroCertidao') or data.get('nrCertidao'),
                data.get('dataEmissao'),
                data.get('dataValidade') or data.get('dataVencimento'),
                data.get('pdf') or data.get('conteudoCertidao'),
                data.get('situacao', 'emitida'),
                protocolo,
            ))
            conn.commit()
            cur.close()
    except Exception as e:
        logger.warning(f"Não foi possível salvar certidão: {e}")


def listar_certidoes(db, empresa_id):
    """Lista certidões salvas da empresa."""
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, cnpj, tipo, numero, data_emissao, data_vencimento, status, protocolo, criado_em
            FROM fiscal_certidoes WHERE empresa_id = %s ORDER BY criado_em DESC
        """, (empresa_id,))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
    return rows


# ─── Módulo DCTFWeb ──────────────────────────────────────────────────────────

def consultar_dctfweb(db, empresa_id, contratante_cnpj, autor_doc, contribuinte_doc, competencia: str):
    """
    Consulta DCTFWeb por competência (formato AAAAMM, ex: '202501').
    Retorna débitos, situação e recibo.
    """
    cd = _limpar_doc(contribuinte_doc)
    payload = _build_payload(
        contratante_cnpj, autor_doc, cd,
        _pedido('DCTFWeb', 'consultar-debitos-declarados',
                {'cnpjBasico': cd[:8], 'pa': competencia})
    )
    resultado = _chamada('Consultar', payload)
    http_code = resultado.get('status_code', 0)
    _salvar_log(db, empresa_id, 'DCTFWEB', 'Consultar/consultar-debitos-declarados',
                {'cnpj': cd, 'competencia': competencia}, resultado, http_code)

    if resultado.get('success'):
        _salvar_dctfweb(db, empresa_id, cd, competencia, resultado)

    return resultado


def _salvar_dctfweb(db, empresa_id, cnpj, competencia, resultado):
    try:
        data = resultado.get('data', {})
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO fiscal_dctfweb (empresa_id, cnpj, competencia, situacao, valor_total, dados, consultado_em)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (empresa_id, cnpj, competencia)
                    DO UPDATE SET situacao = EXCLUDED.situacao,
                                  valor_total = EXCLUDED.valor_total,
                                  dados = EXCLUDED.dados,
                                  consultado_em = NOW()
            """, (empresa_id, cnpj, competencia,
                  data.get('situacao') or data.get('stDeclaracao'),
                  data.get('valorTotal') or data.get('vlTotalDebitos') or 0,
                  json.dumps(data, default=str)))
            conn.commit()
            cur.close()
    except Exception as e:
        logger.warning(f"Não foi possível salvar DCTFWeb: {e}")


def listar_dctfweb(db, empresa_id):
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, cnpj, competencia, situacao, valor_total, consultado_em
            FROM fiscal_dctfweb WHERE empresa_id = %s ORDER BY competencia DESC LIMIT 50
        """, (empresa_id,))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
    return rows


# ─── Módulo MIT ──────────────────────────────────────────────────────────────

def incluir_mit(db, empresa_id, contratante_cnpj, autor_doc, contribuinte_doc, dados_tributo):
    """Inclui débito via Módulo de Inclusão de Tributos (MIT)."""
    cd = _limpar_doc(contribuinte_doc)
    payload = _build_payload(
        contratante_cnpj, autor_doc, cd,
        _pedido('MIT', 'incluir-debito-tributario', dados_tributo)
    )
    resultado = _chamada('Declarar', payload)
    http_code = resultado.get('status_code', 0)
    protocolo = resultado.get('data', {}).get('protocolo') or resultado.get('data', {}).get('nrProtocolo')
    _salvar_log(db, empresa_id, 'MIT', 'Declarar/incluir-debito-tributario',
                {'cnpj': cd, 'dados': dados_tributo}, resultado, http_code, protocolo)
    return resultado


def consultar_mit(db, empresa_id, contratante_cnpj, autor_doc, contribuinte_doc, competencia: str):
    """Consulta débitos transmitidos via MIT."""
    cd = _limpar_doc(contribuinte_doc)
    payload = _build_payload(
        contratante_cnpj, autor_doc, cd,
        _pedido('MIT', 'consultar-debitos-transmitidos',
                {'cnpjBasico': cd[:8], 'pa': competencia})
    )
    resultado = _chamada('Consultar', payload)
    http_code = resultado.get('status_code', 0)
    _salvar_log(db, empresa_id, 'MIT_CONSULTA', 'Consultar/consultar-debitos-transmitidos',
                {'cnpj': cd, 'competencia': competencia}, resultado, http_code)
    return resultado


# ─── Módulo REINF ────────────────────────────────────────────────────────────

REINF_EVENTOS = {
    'R-1000': 'consultar-informacoes-cadastrais',
    'R-2010': 'consultar-servicos-tomados',
    'R-2020': 'consultar-servicos-prestados',
    'R-2099': 'consultar-fechamento-reinf',
}


def consultar_reinf(db, empresa_id, contratante_cnpj, autor_doc, contribuinte_doc,
                    evento: str, competencia: str):
    """Consulta evento REINF para uma competência."""
    cd      = _limpar_doc(contribuinte_doc)
    servico = REINF_EVENTOS.get(evento, 'consultar-eventos-reinf')

    payload = _build_payload(
        contratante_cnpj, autor_doc, cd,
        _pedido('eREINF', servico,
                {'cnpjBasico': cd[:8], 'pa': competencia, 'evento': evento})
    )
    resultado = _chamada('Consultar', payload)
    http_code = resultado.get('status_code', 0)
    protocolo = resultado.get('data', {}).get('nrRecibo') or resultado.get('data', {}).get('recibo')
    _salvar_log(db, empresa_id, f'REINF_{evento}', f'Consultar/{servico}',
                {'cnpj': cd, 'competencia': competencia, 'evento': evento},
                resultado, http_code, protocolo)

    if resultado.get('success'):
        _salvar_reinf(db, empresa_id, cd, competencia, evento,
                      protocolo, resultado.get('data', {}))

    return resultado


def _salvar_reinf(db, empresa_id, cnpj, competencia, evento, recibo, dados):
    try:
        status = dados.get('statusEvento') or dados.get('stEvento') or 'consultado'
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO fiscal_reinf (empresa_id, cnpj, competencia, evento, recibo, status, dados, consultado_em)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (empresa_id, cnpj, competencia, evento)
                    DO UPDATE SET recibo = EXCLUDED.recibo,
                                  status = EXCLUDED.status,
                                  dados = EXCLUDED.dados,
                                  consultado_em = NOW()
            """, (empresa_id, cnpj, competencia, evento, recibo, status,
                  json.dumps(dados, default=str)))
            conn.commit()
            cur.close()
    except Exception as e:
        logger.warning(f"Não foi possível salvar REINF: {e}")


def listar_reinf(db, empresa_id):
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, cnpj, competencia, evento, recibo, status, consultado_em
            FROM fiscal_reinf WHERE empresa_id = %s ORDER BY competencia DESC, evento ASC LIMIT 200
        """, (empresa_id,))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
    return rows


# ─── Módulo DARF ─────────────────────────────────────────────────────────────

def emitir_darf(db, empresa_id, contratante_cnpj, autor_doc, contribuinte_doc,
                codigo_receita, competencia, valor, data_vencimento):
    """Emite DARF para um débito/código de receita."""
    cd = _limpar_doc(contribuinte_doc)
    payload = _build_payload(
        contratante_cnpj, autor_doc, cd,
        _pedido('SIEFPAR', 'emitir-darf',
                {'cnpjCpf': cd, 'codigoReceita': codigo_receita,
                 'pa': competencia, 'valorPrincipal': float(valor),
                 'dataVencimento': str(data_vencimento)})
    )
    resultado = _chamada('Emitir', payload)
    http_code = resultado.get('status_code', 0)
    protocolo = resultado.get('data', {}).get('protocolo') or resultado.get('data', {}).get('nrProtocolo')
    _salvar_log(db, empresa_id, 'DARF_EMITIR', 'Emitir/emitir-darf',
                {'cnpj': cd, 'codigo': codigo_receita, 'competencia': competencia, 'valor': float(valor)},
                resultado, http_code, protocolo)

    if resultado.get('success'):
        _salvar_darf(db, empresa_id, cd, codigo_receita, competencia, valor, data_vencimento,
                     resultado.get('data', {}).get('pdf') or resultado.get('data', {}).get('conteudoDarf'),
                     protocolo)

    return resultado


def consultar_pagamento_darf(db, empresa_id, contratante_cnpj, autor_doc, contribuinte_doc,
                              codigo_receita, competencia):
    """Consulta pagamento de DARF."""
    cd = _limpar_doc(contribuinte_doc)
    payload = _build_payload(
        contratante_cnpj, autor_doc, cd,
        _pedido('SIEFPAR', 'consultar-pagamento-darf',
                {'cnpjCpf': cd, 'codigoReceita': codigo_receita, 'pa': competencia})
    )
    resultado = _chamada('Consultar', payload)
    http_code = resultado.get('status_code', 0)
    _salvar_log(db, empresa_id, 'DARF_CONSULTAR', 'Consultar/consultar-pagamento-darf',
                {'cnpj': cd, 'codigo': codigo_receita, 'competencia': competencia},
                resultado, http_code)

    # Se pago, marcar como liquidado
    if resultado.get('success'):
        data = resultado.get('data', {})
        situacao = data.get('situacao') or data.get('stPagamento', '')
        if 'pago' in str(situacao).lower() or 'liquidado' in str(situacao).lower():
            _marcar_darf_liquidado(db, empresa_id, cd, codigo_receita, competencia)

    return resultado


def _salvar_darf(db, empresa_id, cnpj, codigo_receita, competencia, valor, data_vencimento, pdf, protocolo):
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO fiscal_darf
                    (empresa_id, cnpj, codigo_receita, competencia, valor, data_vencimento,
                     status, pdf_base64, protocolo, criado_em)
                VALUES (%s, %s, %s, %s, %s, %s, 'emitido', %s, %s, NOW())
            """, (empresa_id, cnpj, codigo_receita, competencia, float(valor),
                  data_vencimento, pdf, protocolo))
            conn.commit()
            cur.close()
    except Exception as e:
        logger.warning(f"Não foi possível salvar DARF: {e}")


def _marcar_darf_liquidado(db, empresa_id, cnpj, codigo_receita, competencia):
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE fiscal_darf SET status = 'pago'
                WHERE empresa_id = %s AND cnpj = %s
                  AND codigo_receita = %s AND competencia = %s
                  AND status != 'pago'
            """, (empresa_id, cnpj, codigo_receita, competencia))
            conn.commit()
            cur.close()
    except Exception as e:
        logger.warning(f"Não foi possível marcar DARF como pago: {e}")


def listar_darfs(db, empresa_id):
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, cnpj, codigo_receita, competencia, valor, data_vencimento,
                   status, protocolo, lancamento_id, criado_em
            FROM fiscal_darf WHERE empresa_id = %s ORDER BY data_vencimento DESC LIMIT 200
        """, (empresa_id,))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
    return rows


# ─── Módulo Pagamentos ───────────────────────────────────────────────────────

def consultar_pagamentos(db, empresa_id, contratante_cnpj, autor_doc, contribuinte_doc, competencia):
    """Consulta pagamentos federais realizados."""
    cd = _limpar_doc(contribuinte_doc)
    payload = _build_payload(
        contratante_cnpj, autor_doc, cd,
        _pedido('ReceitaFederal', 'consultar-pagamentos-efetuados',
                {'ni': cd, 'pa': competencia})
    )
    resultado = _chamada('Consultar', payload)
    http_code = resultado.get('status_code', 0)
    _salvar_log(db, empresa_id, 'PAGAMENTOS', 'Consultar/consultar-pagamentos-efetuados',
                {'cnpj': cd, 'competencia': competencia}, resultado, http_code)
    return resultado


# ─── Logs & Dashboard ────────────────────────────────────────────────────────

def listar_logs(db, empresa_id, tipo=None, limit=100):
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        q = "SELECT id, tipo_operacao, endpoint, status_http, protocolo, data FROM logs_fiscais WHERE empresa_id = %s"
        p = [empresa_id]
        if tipo:
            q += " AND tipo_operacao = %s"
            p.append(tipo)
        q += " ORDER BY data DESC LIMIT %s"
        p.append(limit)
        cur.execute(q, p)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
    return rows


def obter_log_detalhe(db, empresa_id, log_id):
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM logs_fiscais WHERE id = %s AND empresa_id = %s", (log_id, empresa_id))
        row = cur.fetchone()
        cur.close()
    return dict(row) if row else None


def gerar_dashboard(db, empresa_id):
    """Retorna métricas agregadas para o dashboard fiscal."""
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Certidões (total, vencendo em 30 dias, vencidas)
        cur.execute("""
            SELECT
                COUNT(*) AS total_certidoes,
                COUNT(*) FILTER (WHERE data_vencimento < NOW()) AS certidoes_vencidas,
                COUNT(*) FILTER (WHERE data_vencimento BETWEEN NOW() AND NOW() + INTERVAL '30 days') AS certidoes_a_vencer,
                COUNT(*) FILTER (WHERE data_vencimento >= NOW()) AS certidoes_validas
            FROM fiscal_certidoes WHERE empresa_id = %s
        """, (empresa_id,))
        cert = dict(cur.fetchone() or {})

        # DARFs
        cur.execute("""
            SELECT
                COUNT(*) AS total_darfs,
                COUNT(*) FILTER (WHERE status = 'emitido' AND data_vencimento < CURRENT_DATE) AS darfs_vencidos,
                COUNT(*) FILTER (WHERE status = 'pago'
                    AND criado_em >= DATE_TRUNC('month', CURRENT_DATE)) AS darfs_pagos_mes,
                COALESCE(SUM(valor) FILTER (WHERE status = 'emitido'), 0) AS valor_pendente
            FROM fiscal_darf WHERE empresa_id = %s
        """, (empresa_id,))
        darf = dict(cur.fetchone() or {})

        # DCTFWeb (última competência)
        cur.execute("""
            SELECT competencia, situacao, valor_total
            FROM fiscal_dctfweb WHERE empresa_id = %s
            ORDER BY competencia DESC LIMIT 1
        """, (empresa_id,))
        row = cur.fetchone()
        dctf = dict(row) if row else {}

        # REINF (última competência por evento)
        cur.execute("""
            SELECT evento, status, competencia
            FROM fiscal_reinf WHERE empresa_id = %s
            ORDER BY consultado_em DESC LIMIT 5
        """, (empresa_id,))
        reinf_rows = [dict(r) for r in cur.fetchall()]

        # Alertas inteligentes
        alertas = []
        if cert.get('certidoes_vencidas', 0):
            alertas.append({'nivel': 'danger', 'msg': f"⚠️ {cert['certidoes_vencidas']} certidão(ões) vencida(s)"})
        if cert.get('certidoes_a_vencer', 0):
            alertas.append({'nivel': 'warning', 'msg': f"🕐 {cert['certidoes_a_vencer']} certidão(ões) vencem em 30 dias"})
        if darf.get('darfs_vencidos', 0):
            alertas.append({'nivel': 'danger', 'msg': f"💸 {darf['darfs_vencidos']} DARF(s) vencido(s) em aberto"})
        if dctf.get('situacao') and 'ativo' not in str(dctf.get('situacao', '')).lower():
            alertas.append({'nivel': 'warning', 'msg': f"📊 DCTFWeb ({dctf.get('competencia')}): {dctf.get('situacao')}"})
        for r in reinf_rows:
            if 'erro' in str(r.get('status', '')).lower():
                alertas.append({'nivel': 'danger', 'msg': f"❌ REINF {r.get('evento')} ({r.get('competencia')}): erro"})

        cur.close()

    return {
        'certidoes': cert,
        'darfs': darf,
        'dctfweb': dctf,
        'reinf_recentes': reinf_rows,
        'alertas': alertas,
    }
