"""
EFD-Reinf — Módulo Completo (Integra Contador SERPRO)
Suporte a todos os eventos vigentes: R-1000, R-1070, R-2010..R-4099, R-9000, R-9011, R-9015

Tabelas usadas:
  reinf_eventos       — controle de cada evento enviado
  reinf_dados         — payload JSONB estruturado por evento
  reinf_totalizadores — apurações consolidadas por competência
  logs_fiscais        — log unificado (já criado pelo fiscal_federal_service)
"""

import json
import logging
import uuid
from datetime import datetime, date
from decimal import Decimal

logger = logging.getLogger(__name__)

# ─── Catálogo de Eventos ────────────────────────────────────────────────────

EVENTOS_REINF = {
    # Tabela
    'R-1000': {'desc': 'Informações do Contribuinte',               'grupo': 'tabela',        'obrigatorio': True},
    'R-1070': {'desc': 'Processos Administrativos/Judiciais',       'grupo': 'tabela',        'obrigatorio': False},
    # Periódicos
    'R-2010': {'desc': 'Retenção CP — Serviços Tomados',            'grupo': 'periodico',     'obrigatorio': False},
    'R-2020': {'desc': 'Retenção CP — Serviços Prestados',          'grupo': 'periodico',     'obrigatorio': False},
    'R-2030': {'desc': 'Recursos Recebidos — Assoc. Desportiva',    'grupo': 'periodico',     'obrigatorio': False},
    'R-2040': {'desc': 'Recursos Repassados — Assoc. Desportiva',   'grupo': 'periodico',     'obrigatorio': False},
    'R-2050': {'desc': 'Comercialização Produção — PJ Rural',       'grupo': 'periodico',     'obrigatorio': False},
    'R-2055': {'desc': 'Aquisição de Produção Rural',               'grupo': 'periodico',     'obrigatorio': False},
    'R-2060': {'desc': 'CPRB — Contrib. Prev. Receita Bruta',       'grupo': 'periodico',     'obrigatorio': False},
    'R-3010': {'desc': 'Espetáculo Desportivo',                     'grupo': 'periodico',     'obrigatorio': False},
    'R-4010': {'desc': 'Pagamentos/Créditos — Pessoa Física',        'grupo': 'periodico',     'obrigatorio': False},
    'R-4020': {'desc': 'Pagamentos/Créditos — Pessoa Jurídica',      'grupo': 'periodico',     'obrigatorio': False},
    'R-4040': {'desc': 'Pagamentos — Beneficiário Não Identificado', 'grupo': 'periodico',     'obrigatorio': False},
    'R-4080': {'desc': 'Retenção no Recebimento (Auto Retenção)',   'grupo': 'periodico',     'obrigatorio': False},
    'R-4099': {'desc': 'Fechamento dos Eventos Periódicos (R-4xxx)','grupo': 'fechamento',    'obrigatorio': False},
    'R-2098': {'desc': 'Reabertura',                                 'grupo': 'nao_periodico', 'obrigatorio': False},
    'R-2099': {'desc': 'Fechamento (R-2xxx)',                        'grupo': 'fechamento',    'obrigatorio': False},
    'R-9000': {'desc': 'Exclusão de Eventos',                       'grupo': 'nao_periodico', 'obrigatorio': False},
    'R-9011': {'desc': 'Consolidação de Bases e Tributos',           'grupo': 'nao_periodico', 'obrigatorio': False},
    'R-9015': {'desc': 'Totalização de Bases e Tributos',            'grupo': 'nao_periodico', 'obrigatorio': False},
}

STATUS_LABELS = {
    'pendente':     '⏳ Pendente',
    'enviado':      '📤 Enviado',
    'processando':  '🔄 Processando',
    'autorizado':   '✅ Autorizado',
    'erro':         '❌ Erro',
    'excluido':     '🗑️ Excluído',
}

# ─── Helpers ────────────────────────────────────────────────────────────────

def _row_to_dict(row):
    if row is None:
        return None
    if hasattr(row, 'keys'):
        d = dict(row)
    elif hasattr(row, '_mapping'):
        d = dict(row._mapping)
    else:
        return row
    # serializar datas
    for k, v in d.items():
        if isinstance(v, (datetime, date)):
            d[k] = v.isoformat()
        elif isinstance(v, Decimal):
            d[k] = float(v)
    return d


def _rows_to_list(rows):
    return [_row_to_dict(r) for r in rows]


def _limpar_doc(doc: str) -> str:
    return ''.join(c for c in (doc or '') if c.isdigit())


def _tipo_doc(doc: str) -> int:
    d = _limpar_doc(doc)
    return 1 if len(d) == 11 else 2


# competência MMAAAA → AAAAMM para API
def _to_api_comp(comp: str) -> str:
    v = ''.join(c for c in (comp or '') if c.isdigit())
    if len(v) == 6:
        return v[2:] + v[:2]
    return v


# AAAAMM → MM/AAAA para exibição
def _fmt_comp(aaaamm: str) -> str:
    v = str(aaaamm or '').replace('-', '').replace('/', '').strip()
    if len(v) == 6:
        return f"{v[4:6]}/{v[0:4]}"
    return aaaamm


def _build_payload(contratante_cnpj, autor_doc, contribuinte_doc, pedido):
    cn = _limpar_doc(contratante_cnpj)
    ad = _limpar_doc(autor_doc)
    cd = _limpar_doc(contribuinte_doc)
    return {
        'contratante':     {'numero': cn, 'tipo': 2},
        'autorPedidoDados':{'numero': ad, 'tipo': _tipo_doc(autor_doc)},
        'contribuinte':    {'numero': cd, 'tipo': _tipo_doc(contribuinte_doc)},
        'pedidoDados':     pedido,
    }


def _pedido(id_sistema, id_servico, dados, versao='1.0'):
    return {
        'idSistema':     id_sistema,
        'idServico':     id_servico,
        'versaoSistema': versao,
        'dados':         json.dumps(dados, ensure_ascii=False),
    }


def _chamada(tipo_operacao, payload):
    from integra_contador_functions import enviar_requisicao
    import time
    for tentativa in range(3):
        resultado = enviar_requisicao(tipo_operacao, payload)
        if resultado.get('status_code') == 429:
            espera = 2 ** tentativa
            logger.warning(f"Rate limit (429). Aguardando {espera}s...")
            time.sleep(espera)
            continue
        return resultado
    return resultado


def _salvar_log(db, empresa_id, tipo, endpoint, req, resp, http_code, protocolo=None):
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO logs_fiscais
                   (empresa_id, tipo_operacao, endpoint, request, response, status_http, protocolo, data)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,NOW())""",
                (empresa_id, tipo, endpoint,
                 json.dumps(req, ensure_ascii=False, default=str),
                 json.dumps(resp, ensure_ascii=False, default=str),
                 http_code, protocolo)
            )
            conn.commit()
            cur.close()
    except Exception as e:
        logger.warning(f"⚠️ log fiscal: {e}")


# ─── Gerenciamento de Eventos ────────────────────────────────────────────────

def criar_evento(db, empresa_id, competencia, evento, payload_dados, identificador=None):
    """
    Cria um registro em reinf_eventos + reinf_dados.
    Retorna o dict do evento criado.
    """
    import psycopg2.extras
    api_comp = _to_api_comp(competencia)

    # Verificar duplicidade (mesmo evento+competencia ainda não enviado/autorizado)
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, status FROM reinf_eventos
            WHERE empresa_id=%s AND competencia=%s AND evento=%s
              AND status NOT IN ('erro', 'excluido')
        """, (empresa_id, api_comp, evento))
        existente = cur.fetchone()
        cur.close()

    if existente:
        return {'success': False,
                'error': f"Já existe evento {evento} para competência {_fmt_comp(api_comp)} "
                         f"com status '{existente['status']}'. Exclua antes de reenviar."}

    # Validação especial: R-2099/R-4099 exigem R-1000 autorizado
    if evento in ('R-2099', 'R-4099'):
        err = _validar_prerequisito_r1000(db, empresa_id)
        if err:
            return {'success': False, 'error': err}

    # Inserir evento
    evento_id = str(uuid.uuid4())
    ident = identificador or f"{empresa_id}-{api_comp}-{evento}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reinf_eventos
                (id, empresa_id, competencia, evento, identificador_evento, status, created_at)
            VALUES (%s,%s,%s,%s,%s,'pendente',NOW())
        """, (evento_id, empresa_id, api_comp, evento, ident))
        cur.execute("""
            INSERT INTO reinf_dados (id, evento_id, payload)
            VALUES (%s,%s,%s)
        """, (str(uuid.uuid4()), evento_id,
              json.dumps(payload_dados, ensure_ascii=False, default=str)))
        conn.commit()
        cur.close()

    return {'success': True, 'evento_id': evento_id,
            'message': f'Evento {evento} criado. Status: pendente.'}


def listar_eventos(db, empresa_id, competencia=None, evento=None, status=None):
    """Lista eventos de uma empresa com filtros opcionais."""
    import psycopg2.extras
    q = """SELECT e.id, e.competencia, e.evento, e.status, e.protocolo, e.recibo,
                  e.erro, e.enviado_em, e.created_at, e.identificador_evento,
                  d.payload
           FROM reinf_eventos e
           LEFT JOIN reinf_dados d ON d.evento_id = e.id
           WHERE e.empresa_id = %s"""
    params = [empresa_id]
    if competencia:
        q += ' AND e.competencia = %s'; params.append(_to_api_comp(competencia))
    if evento:
        q += ' AND e.evento = %s'; params.append(evento)
    if status:
        q += ' AND e.status = %s'; params.append(status)
    q += ' ORDER BY e.competencia DESC, e.evento, e.created_at DESC'

    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(q, params)
        rows = _rows_to_list(cur.fetchall())
        cur.close()
    return rows


def obter_evento(db, empresa_id, evento_id):
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT e.*, d.payload FROM reinf_eventos e
            LEFT JOIN reinf_dados d ON d.evento_id = e.id
            WHERE e.id=%s AND e.empresa_id=%s
        """, (evento_id, empresa_id))
        row = cur.fetchone()
        cur.close()
    return _row_to_dict(row)


def excluir_evento(db, empresa_id, evento_id, motivo='Exclusão manual'):
    """Marca evento como excluído e cria R-9000 se já foi enviado."""
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM reinf_eventos WHERE id=%s AND empresa_id=%s",
                    (evento_id, empresa_id))
        ev = cur.fetchone()
        cur.close()

    if not ev:
        return {'success': False, 'error': 'Evento não encontrado'}

    ev = _row_to_dict(ev)
    if ev['status'] in ('autorizado', 'enviado', 'processando'):
        # Precisa gerar R-9000
        r9000_payload = {
            'evento_excluido': ev['evento'],
            'nrRec':           ev.get('recibo', ''),
            'motivo':          motivo,
        }
        criar_evento(db, empresa_id, ev['competencia'], 'R-9000', r9000_payload)

    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE reinf_eventos SET status='excluido', erro=%s WHERE id=%s",
            (f"Excluído: {motivo}", evento_id)
        )
        conn.commit()
        cur.close()

    return {'success': True, 'message': 'Evento excluído. R-9000 gerado automaticamente se necessário.'}


# ─── Envio para API ──────────────────────────────────────────────────────────

def enviar_evento(db, empresa_id, evento_id, contratante_cnpj, autor_doc):
    """Envia um evento pendente para a API Integra Contador."""
    import psycopg2.extras
    ev = obter_evento(db, empresa_id, evento_id)
    if not ev:
        return {'success': False, 'error': 'Evento não encontrado'}

    if ev['status'] == 'autorizado':
        return {'success': False, 'error': 'Evento já autorizado. Exclua antes de reenviar.'}

    if ev['status'] not in ('pendente', 'erro'):
        return {'success': False, 'error': f"Evento com status '{ev['status']}' não pode ser reenviado."}

    # Montar payload para API
    payload_dados = ev.get('payload') or {}
    if isinstance(payload_dados, str):
        try: payload_dados = json.loads(payload_dados)
        except: payload_dados = {}

    contribuinte_cnpj = payload_dados.get('cnpj') or contratante_cnpj
    api_evento = ev['evento'].replace('-', '_').lower()

    payload = _build_payload(
        contratante_cnpj, autor_doc, contribuinte_cnpj,
        _pedido('eREINF', f'enviar-evento-{api_evento}',
                {'competencia': ev['competencia'],
                 'evento': ev['evento'],
                 'dados': payload_dados})
    )

    # Marcar como processando
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE reinf_eventos SET status='processando', enviado_em=NOW(), "
                    "xml_enviado=%s WHERE id=%s",
                    (json.dumps(payload, ensure_ascii=False), evento_id))
        conn.commit()
        cur.close()

    resultado = _chamada('Declarar', payload)
    http_code = resultado.get('status_code', 0)
    protocolo = (resultado.get('data') or {}).get('protocolo') or \
                (resultado.get('data') or {}).get('nrProtocolo')
    recibo    = (resultado.get('data') or {}).get('nrRec') or \
                (resultado.get('data') or {}).get('recibo')

    sucesso = resultado.get('success') or (200 <= int(http_code or 0) < 300)
    novo_status = 'enviado' if sucesso else 'erro'
    erro_msg = None if sucesso else (resultado.get('error') or str(resultado.get('data', '')))

    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE reinf_eventos
            SET status=%s, protocolo=%s, recibo=%s, xml_retorno=%s, erro=%s
            WHERE id=%s
        """, (novo_status, protocolo, recibo,
              json.dumps(resultado, ensure_ascii=False, default=str),
              erro_msg, evento_id))
        conn.commit()
        cur.close()

    _salvar_log(db, empresa_id, f'REINF_ENVIAR_{ev["evento"]}',
                f'Declarar/enviar-evento-{api_evento}',
                payload, resultado, http_code, protocolo)

    return {
        'success': sucesso,
        'status':  novo_status,
        'protocolo': protocolo,
        'recibo':    recibo,
        'message':   'Evento enviado com sucesso!' if sucesso else f'Erro: {erro_msg}',
        'data':      resultado.get('data'),
    }


def consultar_status_evento(db, empresa_id, evento_id, contratante_cnpj, autor_doc):
    """Consulta status de um evento enviado via protocolo."""
    ev = obter_evento(db, empresa_id, evento_id)
    if not ev or not ev.get('protocolo'):
        return {'success': False, 'error': 'Protocolo não disponível'}

    payload = _build_payload(
        contratante_cnpj, autor_doc, contratante_cnpj,
        _pedido('eREINF', 'consultar-status-evento',
                {'nrProtocolo': ev['protocolo']})
    )
    resultado = _chamada('Consultar', payload)
    http_code = resultado.get('status_code', 0)

    data = resultado.get('data') or {}
    situacao = str(data.get('situacao') or data.get('cdResposta') or '').lower()

    novo_status = None
    if 'autorizado' in situacao or situacao == '0':
        novo_status = 'autorizado'
    elif 'erro' in situacao or 'rejeic' in situacao:
        novo_status = 'erro'

    if novo_status:
        recibo = data.get('nrRec') or data.get('recibo') or ev.get('recibo')
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE reinf_eventos SET status=%s, recibo=%s, xml_retorno=%s WHERE id=%s",
                (novo_status, recibo,
                 json.dumps(resultado, ensure_ascii=False, default=str), evento_id)
            )
            conn.commit()
            cur.close()

    _salvar_log(db, empresa_id, 'REINF_CONSULTA_STATUS',
                'Consultar/consultar-status-evento',
                {'protocolo': ev['protocolo']}, resultado, http_code)

    return {'success': True, 'status': novo_status or ev['status'], 'data': data}


# ─── Fechamento ──────────────────────────────────────────────────────────────

def fechar_competencia(db, empresa_id, competencia, tipo_fechamento,
                       contratante_cnpj, autor_doc):
    """
    Envia R-2099 (eventos R-2xxx) ou R-4099 (eventos R-4xxx).
    Valida pré-condições antes.
    """
    api_comp = _to_api_comp(competencia)

    # Verificar se há eventos com erro
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT COUNT(*) as qtd FROM reinf_eventos
            WHERE empresa_id=%s AND competencia=%s AND status='erro'
        """, (empresa_id, api_comp))
        row = _row_to_dict(cur.fetchone())
        cur.close()

    if row and row.get('qtd', 0) > 0:
        return {'success': False,
                'error': f"Há {row['qtd']} evento(s) com erro. Corrija antes do fechamento."}

    # Verificar R-1000
    err = _validar_prerequisito_r1000(db, empresa_id)
    if err:
        return {'success': False, 'error': err}

    evento_fechamento = tipo_fechamento  # 'R-2099' ou 'R-4099'
    payload_dados = {
        'cnpj':        _limpar_doc(contratante_cnpj),
        'competencia': api_comp,
    }
    res_criar = criar_evento(db, empresa_id, competencia, evento_fechamento, payload_dados)
    if not res_criar.get('success'):
        return res_criar

    return enviar_evento(db, empresa_id, res_criar['evento_id'], contratante_cnpj, autor_doc)


def reabrir_competencia(db, empresa_id, competencia, contratante_cnpj, autor_doc):
    """Envia R-2098 para reabrir competência fechada."""
    api_comp = _to_api_comp(competencia)
    payload_dados = {'cnpj': _limpar_doc(contratante_cnpj), 'competencia': api_comp}
    res_criar = criar_evento(db, empresa_id, competencia, 'R-2098', payload_dados)
    if not res_criar.get('success'):
        return res_criar
    return enviar_evento(db, empresa_id, res_criar['evento_id'], contratante_cnpj, autor_doc)


# ─── Validações ──────────────────────────────────────────────────────────────

def _validar_prerequisito_r1000(db, empresa_id):
    """Retorna mensagem de erro se não houver R-1000 autorizado; None se OK."""
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id FROM reinf_eventos
            WHERE empresa_id=%s AND evento='R-1000' AND status='autorizado'
            LIMIT 1
        """, (empresa_id,))
        row = cur.fetchone()
        cur.close()
    if not row:
        return "R-1000 não encontrado ou não autorizado. Envie R-1000 primeiro."
    return None


def validar_evento(db, empresa_id, evento, payload_dados, competencia):
    """Validação pré-envio. Retorna lista de erros encontrados."""
    erros = []
    api_comp = _to_api_comp(competencia)

    # CNPJ/CPF básico
    cnpj = payload_dados.get('cnpj') or payload_dados.get('cpf') or ''
    if cnpj and len(_limpar_doc(cnpj)) not in (11, 14):
        erros.append(f"CPF/CNPJ inválido: {cnpj}")

    # Fechamentos requerem R-1000
    if evento in ('R-2099', 'R-4099', 'R-2098'):
        err = _validar_prerequisito_r1000(db, empresa_id)
        if err:
            erros.append(err)

    # Verificar duplicidade
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, status FROM reinf_eventos
            WHERE empresa_id=%s AND competencia=%s AND evento=%s AND status NOT IN ('erro','excluido')
        """, (empresa_id, api_comp, evento))
        dupl = cur.fetchone()
        cur.close()
    if dupl:
        erros.append(f"Evento {evento} já existe para {_fmt_comp(api_comp)} "
                     f"com status '{dupl['status']}'.")

    # Valores negativos em retenção
    for campo in ('vlrBaseInss', 'vlrInss', 'vlrBaseIr', 'vlrIr'):
        v = payload_dados.get(campo)
        if v is not None and float(v) < 0:
            erros.append(f"Campo {campo} não pode ser negativo.")

    return erros


# ─── Motor Inteligente — Sugestões ───────────────────────────────────────────

def gerar_sugestoes(db, empresa_id, competencia):
    """
    Analisa dados financeiros e de lançamentos para sugerir quais eventos
    REINF devem ser enviados na competência.
    """
    api_comp  = _to_api_comp(competencia)
    ano  = api_comp[:4]
    mes  = api_comp[4:6]
    sugestoes = []
    alertas   = []

    try:
        import psycopg2.extras
        with db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Verificar R-1000
            cur.execute(
                "SELECT id FROM reinf_eventos WHERE empresa_id=%s AND evento='R-1000' AND status='autorizado'",
                (empresa_id,)
            )
            if not cur.fetchone():
                alertas.append({'tipo': 'danger', 'msg': 'R-1000 não enviado! Configure as informações do contribuinte.'})

            # Pagamentos a PF/PJ no período (R-4010 / R-4020)
            # Nota: join com fornecedores evitado pois coluna de FK pode variar;
            #       usamos heurística por descricao/categoria para separar PF de PJ.
            cur.execute("""
                SELECT COUNT(*) as qtd, SUM(ABS(valor)) as total
                FROM lancamentos
                WHERE empresa_id=%s AND EXTRACT(YEAR FROM data_pagamento)=%s
                  AND EXTRACT(MONTH FROM data_pagamento)=%s
                  AND tipo='saida'
                  AND (descricao ILIKE '%%pessoa fisica%%' OR descricao ILIKE '%%autônomo%%'
                       OR descricao ILIKE '%%autonomo%%' OR descricao ILIKE '%%RPA%%'
                       OR descricao ILIKE '%%pró-labore%%' OR descricao ILIKE '%%pro labore%%')
            """, (empresa_id, ano, mes))
            row = _row_to_dict(cur.fetchone())
            if row and row.get('qtd', 0) > 0:
                sugestoes.append({
                    'evento': 'R-4010',
                    'motivo': f"{row['qtd']} pagamento(s) a pessoa física detectado(s) — Total: R$ {row.get('total', 0):.2f}",
                    'valor':  float(row.get('total') or 0),
                })

            cur.execute("""
                SELECT COUNT(*) as qtd, SUM(ABS(valor)) as total
                FROM lancamentos
                WHERE empresa_id=%s AND EXTRACT(YEAR FROM data_pagamento)=%s
                  AND EXTRACT(MONTH FROM data_pagamento)=%s
                  AND tipo='saida'
                  AND (descricao ILIKE '%%CNPJ%%' OR descricao ILIKE '%%NF%%'
                       OR descricao ILIKE '%%nota fiscal%%' OR descricao ILIKE '%%pessoa juridica%%'
                       OR descricao ILIKE '%%prestador%%' OR categoria ILIKE '%%serviço%%'
                       OR categoria ILIKE '%%fornecedor%%')
            """, (empresa_id, ano, mes))
            row = _row_to_dict(cur.fetchone())
            if row and row.get('qtd', 0) > 0:
                sugestoes.append({
                    'evento': 'R-4020',
                    'motivo': f"{row['qtd']} pagamento(s) a pessoa jurídica detectado(s) — Total: R$ {row.get('total', 0):.2f}",
                    'valor':  float(row.get('total') or 0),
                })

            # Verificar retenções (notas fiscais com INSS/IR retido)
            cur.execute("""
                SELECT COUNT(*) as qtd
                FROM lancamentos
                WHERE empresa_id=%s AND tipo='saida'
                  AND EXTRACT(YEAR FROM data_pagamento)=%s
                  AND EXTRACT(MONTH FROM data_pagamento)=%s
                  AND (descricao ILIKE '%%retenção%%' OR descricao ILIKE '%%inss%%'
                       OR descricao ILIKE '%%serviços%%' OR categoria ILIKE '%%serviço%%')
            """, (empresa_id, ano, mes))
            row = _row_to_dict(cur.fetchone())
            if row and row.get('qtd', 0) > 0:
                sugestoes.append({
                    'evento': 'R-2010',
                    'motivo': 'Detectados lançamentos de serviços tomados com possível retenção CP.',
                    'valor':  0,
                })

            cur.close()
    except Exception as e:
        logger.warning(f"Motor inteligente: {e}")
        alertas.append({'tipo': 'warning', 'msg': f'Motor inteligente: dados parciais ({e})'})

    return {'sugestoes': sugestoes, 'alertas': alertas}


# ─── Totalizadores ───────────────────────────────────────────────────────────

def calcular_totalizadores(db, empresa_id, competencia):
    """Agrega totais de todos os eventos autorizados da competência."""
    import psycopg2.extras
    api_comp = _to_api_comp(competencia)

    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT d.payload FROM reinf_eventos e
            JOIN reinf_dados d ON d.evento_id = e.id
            WHERE e.empresa_id=%s AND e.competencia=%s
              AND e.status IN ('autorizado', 'enviado')
        """, (empresa_id, api_comp))
        rows = cur.fetchall()
        cur.close()

    totais = {
        'total_base': 0.0, 'total_inss': 0.0, 'total_ir': 0.0,
        'total_csll': 0.0, 'total_pis': 0.0, 'total_cofins': 0.0,
    }
    for row in rows:
        payload = row['payload']
        if isinstance(payload, str):
            try: payload = json.loads(payload)
            except: continue
        if not isinstance(payload, dict):
            continue
        totais['total_base']   += float(payload.get('vlrBaseInss')  or 0)
        totais['total_inss']   += float(payload.get('vlrInss')       or 0)
        totais['total_ir']     += float(payload.get('vlrBaseIr')     or 0)
        totais['total_csll']   += float(payload.get('vlrCsll')       or 0)
        totais['total_pis']    += float(payload.get('vlrPis')        or 0)
        totais['total_cofins'] += float(payload.get('vlrCofins')     or 0)

    # Salvar/atualizar na tabela
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO reinf_totalizadores
                    (empresa_id, competencia, total_base, total_inss, total_ir,
                     total_csll, total_pis, total_cofins, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT (empresa_id, competencia)
                DO UPDATE SET total_base=%s, total_inss=%s, total_ir=%s,
                              total_csll=%s, total_pis=%s, total_cofins=%s,
                              created_at=NOW()
            """, (
                empresa_id, api_comp,
                totais['total_base'], totais['total_inss'], totais['total_ir'],
                totais['total_csll'], totais['total_pis'], totais['total_cofins'],
                totais['total_base'], totais['total_inss'], totais['total_ir'],
                totais['total_csll'], totais['total_pis'], totais['total_cofins'],
            ))
            conn.commit()
            cur.close()
    except Exception as e:
        logger.warning(f"Totalizadores: {e}")

    return totais


def obter_totalizadores(db, empresa_id, competencia):
    import psycopg2.extras
    api_comp = _to_api_comp(competencia)
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM reinf_totalizadores WHERE empresa_id=%s AND competencia=%s",
            (empresa_id, api_comp)
        )
        row = cur.fetchone()
        cur.close()
    return _row_to_dict(row)


# ─── Dashboard ───────────────────────────────────────────────────────────────

def dashboard_reinf(db, empresa_id, competencia):
    """Retorna todos os dados para o painel REINF de uma competência."""
    import psycopg2.extras
    api_comp = _to_api_comp(competencia)

    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Contagem por status
        cur.execute("""
            SELECT status, COUNT(*) as qtd
            FROM reinf_eventos WHERE empresa_id=%s AND competencia=%s
            GROUP BY status
        """, (empresa_id, api_comp))
        por_status = {r['status']: r['qtd'] for r in cur.fetchall()}

        # Status da competência (aberta/fechada)
        cur.execute("""
            SELECT evento, status FROM reinf_eventos
            WHERE empresa_id=%s AND competencia=%s
              AND evento IN ('R-2099','R-4099') AND status='autorizado'
            LIMIT 1
        """, (empresa_id, api_comp))
        fechamento = cur.fetchone()

        # Eventos enviados
        cur.execute("""
            SELECT evento, status, recibo, protocolo, enviado_em
            FROM reinf_eventos
            WHERE empresa_id=%s AND competencia=%s
            ORDER BY evento
        """, (empresa_id, api_comp))
        eventos = _rows_to_list(cur.fetchall())

        cur.close()

    totais = obter_totalizadores(db, empresa_id, competencia) or {}
    sugestoes_data = gerar_sugestoes(db, empresa_id, competencia)

    status_comp = 'fechada' if fechamento else 'aberta'

    # Pendências
    pendencias = []
    err_r1000 = _validar_prerequisito_r1000(db, empresa_id)
    if err_r1000:
        pendencias.append(err_r1000)
    erros = por_status.get('erro', 0)
    if erros:
        pendencias.append(f"{erros} evento(s) com erro precisam ser corrigidos.")

    return {
        'competencia':    _fmt_comp(api_comp),
        'competencia_raw': api_comp,
        'status':         status_comp,
        'por_status':     por_status,
        'eventos':        eventos,
        'totais':         totais,
        'pendencias':     pendencias,
        'sugestoes':      sugestoes_data.get('sugestoes', []),
        'alertas':        sugestoes_data.get('alertas', []),
    }


# ─── Integração DCTFWeb ──────────────────────────────────────────────────────

def sincronizar_dctfweb(db, empresa_id, competencia, contratante_cnpj, autor_doc):
    """Após fechamento, busca totalizadores e compara com DCTFWeb."""
    totais = calcular_totalizadores(db, empresa_id, competencia)
    api_comp = _to_api_comp(competencia)

    # Buscar DCTFWeb do mesmo período
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM fiscal_dctfweb WHERE empresa_id=%s AND competencia=%s",
            (empresa_id, api_comp)
        )
        dctf = _row_to_dict(cur.fetchone())
        cur.close()

    divergencias = []
    if dctf:
        inss_dctf = float((dctf.get('dados') or {}).get('vlrInss') or 0)
        if abs(totais.get('total_inss', 0) - inss_dctf) > 0.01:
            divergencias.append(
                f"INSS: REINF apurou R$ {totais['total_inss']:.2f} vs DCTFWeb R$ {inss_dctf:.2f}"
            )

    return {
        'success':     True,
        'totais_reinf': totais,
        'dctfweb':     dctf,
        'divergencias': divergencias,
        'message':     'Divergências encontradas!' if divergencias else 'Valores conferem.',
    }


# ─── Exportação XML ──────────────────────────────────────────────────────────

def exportar_xml_evento(db, empresa_id, evento_id):
    ev = obter_evento(db, empresa_id, evento_id)
    if not ev:
        return None
    xml = ev.get('xml_enviado') or json.dumps(ev.get('payload') or {}, indent=2, ensure_ascii=False)
    return xml


# ─── Listar competências com atividade ───────────────────────────────────────

def listar_competencias(db, empresa_id):
    import psycopg2.extras
    with db.get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT competencia, COUNT(*) as total,
                   SUM(CASE WHEN status='autorizado' THEN 1 ELSE 0 END) as autorizados,
                   SUM(CASE WHEN status='erro'       THEN 1 ELSE 0 END) as erros,
                   MAX(CASE WHEN evento IN ('R-2099','R-4099') AND status='autorizado'
                            THEN 1 ELSE 0 END) as fechada
            FROM reinf_eventos WHERE empresa_id=%s
            GROUP BY competencia ORDER BY competencia DESC
        """, (empresa_id,))
        rows = _rows_to_list(cur.fetchall())
        cur.close()

    # Formatar competências para exibição
    for r in rows:
        r['competencia_fmt'] = _fmt_comp(r.get('competencia', ''))
    return rows
