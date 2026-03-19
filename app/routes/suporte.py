"""
===============================================
ROTAS DE SUPORTE / CHAMADOS
===============================================
Sistema completo de tickets de suporte com:
- Abertura de chamados pelo usuário
- Captura automática de console logs do navegador
- Numeração auditável (protocolo + número sequencial)
- Painel administrativo para gestão
"""

from flask import Blueprint, request, jsonify, session
import hashlib
import time
import os
import sys

# Garantir que o diretório raiz do projeto está no path
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


def _get_user_info():
    """
    Obtém informações do usuário logado usando auth_middleware.
    Retorna dict com user_id, user_name, user_type, empresa_id ou None se não autenticado.
    Importação lazy para não bloquear registro do blueprint.
    """
    try:
        from auth_middleware import get_usuario_logado
        usuario = get_usuario_logado()
    except Exception as e:
        print(f"❌ [suporte] Erro ao importar/chamar get_usuario_logado: {e}")
        usuario = None

    if not usuario:
        print(f"⚠️ [suporte] Usuário não autenticado via get_usuario_logado, tentando session...")
        # Fallback: tentar session diretamente
        user_id = session.get('user_id')
        if not user_id:
            return None
        return {
            'user_id': user_id,
            'user_name': session.get('user_name', 'Usuário'),
            'user_type': session.get('user_type', 'cliente'),
            'empresa_id': session.get('empresa_id'),
        }

    # empresa_id: objeto do usuario > header X-Empresa-ID > session
    empresa_id = usuario.get('empresa_id')
    if not empresa_id:
        header_empresa = request.headers.get('X-Empresa-ID')
        empresa_id = int(header_empresa) if header_empresa and header_empresa.isdigit() else None
        empresa_id = empresa_id or session.get('empresa_id')

    info = {
        'user_id': usuario.get('id'),
        'user_name': usuario.get('nome_completo') or usuario.get('username', 'Usuário'),
        'user_type': (usuario.get('tipo') or 'cliente').strip().lower(),
        'empresa_id': empresa_id,
    }
    print(f"🔍 [suporte] _get_user_info: tipo={info['user_type']}, empresa_id={info['empresa_id']}, user={info['user_name']}")
    return info

suporte_bp = Blueprint('suporte', __name__, url_prefix='/api/suporte')

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_chamados_table(cur):
    """Cria a tabela chamados_suporte se ainda não existir."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chamados_suporte (
            id SERIAL PRIMARY KEY,
            numero_chamado VARCHAR(20) UNIQUE NOT NULL,
            protocolo VARCHAR(30) UNIQUE NOT NULL,
            empresa_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            usuario_nome VARCHAR(255) NOT NULL,
            titulo VARCHAR(255) NOT NULL,
            descricao TEXT NOT NULL,
            console_logs TEXT,
            navegador_info TEXT,
            url_pagina VARCHAR(500),
            screenshot_base64 TEXT,
            status VARCHAR(20) DEFAULT 'aberto'
                CHECK (status IN ('aberto', 'em_andamento', 'resolvido')),
            resposta_admin TEXT,
            admin_id INTEGER,
            admin_nome VARCHAR(255),
            prioridade VARCHAR(20) DEFAULT 'media'
                CHECK (prioridade IN ('baixa', 'media', 'alta', 'critica')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolvido_em TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_chamados_empresa
        ON chamados_suporte(empresa_id)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_chamados_status
        ON chamados_suporte(status)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_chamados_usuario
        ON chamados_suporte(usuario_id)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_chamados_numero
        ON chamados_suporte(numero_chamado)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_chamados_protocolo
        ON chamados_suporte(protocolo)
    """)
    # Tabela de sequência para numeração auditável
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chamados_sequencia (
            id SERIAL PRIMARY KEY,
            empresa_id INTEGER NOT NULL UNIQUE,
            ultimo_numero INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def _gerar_numero_chamado(cur, empresa_id):
    """
    Gera número de chamado sequencial auditável por empresa.
    Formato: CHM-EEEE-NNNNN (ex: CHM-0001-00042)
    Usa SELECT FOR UPDATE para garantir atomicidade.
    """
    cur.execute("""
        INSERT INTO chamados_sequencia (empresa_id, ultimo_numero, updated_at)
        VALUES (%s, 0, NOW())
        ON CONFLICT (empresa_id) DO NOTHING
    """, (empresa_id,))

    cur.execute("""
        UPDATE chamados_sequencia
        SET ultimo_numero = ultimo_numero + 1, updated_at = NOW()
        WHERE empresa_id = %s
        RETURNING ultimo_numero
    """, (empresa_id,))

    seq = cur.fetchone()['ultimo_numero']
    return f"CHM-{empresa_id:04d}-{seq:05d}"


def _gerar_protocolo(numero_chamado, usuario_id):
    """
    Gera protocolo único verificável.
    Formato: YYYYMMDD-HASH8 (ex: 20260318-A3F8D2C1)
    O hash é derivado do número do chamado + usuario + timestamp,
    garantindo que não é adivinhável e é verificável.
    """
    from datetime import datetime
    data = datetime.now().strftime('%Y%m%d')
    payload = f"{numero_chamado}:{usuario_id}:{time.time()}"
    hash_val = hashlib.sha256(payload.encode()).hexdigest()[:8].upper()
    return f"{data}-{hash_val}"


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------

@suporte_bp.route('/chamados', methods=['GET'])
def listar_chamados():
    """Lista chamados do usuário logado (ou todos para admin)."""
    try:
        from database_postgresql import get_db_connection

        info = _get_user_info()
        if not info:
            return jsonify({'error': 'Não autenticado'}), 401

        usuario_id = info['user_id']
        empresa_id = info['empresa_id']
        tipo_usuario = info['user_type']

        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_chamados_table(cur)

            if tipo_usuario == 'admin' and empresa_id:
                cur.execute("""
                    SELECT * FROM chamados_suporte
                    WHERE empresa_id = %s
                    ORDER BY
                        CASE status
                            WHEN 'aberto' THEN 1
                            WHEN 'em_andamento' THEN 2
                            WHEN 'resolvido' THEN 3
                        END,
                        created_at DESC
                """, (empresa_id,))
            elif tipo_usuario == 'admin':
                cur.execute("""
                    SELECT * FROM chamados_suporte
                    ORDER BY
                        CASE status
                            WHEN 'aberto' THEN 1
                            WHEN 'em_andamento' THEN 2
                            WHEN 'resolvido' THEN 3
                        END,
                        created_at DESC
                """)
            else:
                cur.execute("""
                    SELECT * FROM chamados_suporte
                    WHERE empresa_id = %s AND usuario_id = %s
                    ORDER BY created_at DESC
                """, (empresa_id, usuario_id))

            chamados = cur.fetchall()
            return jsonify({
                'success': True,
                'chamados': [dict(c) for c in chamados] if chamados else []
            })
    except Exception as e:
        print(f"❌ Erro ao listar chamados: {e}")
        return jsonify({'error': str(e)}), 500


@suporte_bp.route('/chamados', methods=['POST'])
def criar_chamado():
    """Cria um novo chamado de suporte."""
    try:
        from database_postgresql import get_db_connection

        info = _get_user_info()
        if not info:
            return jsonify({'error': 'Não autenticado'}), 401

        data = request.json
        usuario_id = info['user_id']
        usuario_nome = info['user_name']
        empresa_id = info['empresa_id']

        titulo = (data.get('titulo') or '').strip()
        descricao = (data.get('descricao') or '').strip()
        console_logs = data.get('console_logs', '')
        navegador_info = data.get('navegador_info', '')
        url_pagina = data.get('url_pagina', '')
        prioridade = data.get('prioridade', 'media')

        if not titulo or not descricao:
            return jsonify({'error': 'Título e descrição são obrigatórios'}), 400

        if prioridade not in ('baixa', 'media', 'alta', 'critica'):
            prioridade = 'media'

        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_chamados_table(cur)

            numero_chamado = _gerar_numero_chamado(cur, empresa_id)
            protocolo = _gerar_protocolo(numero_chamado, usuario_id)

            cur.execute("""
                INSERT INTO chamados_suporte
                    (numero_chamado, protocolo, empresa_id, usuario_id, usuario_nome,
                     titulo, descricao, console_logs, navegador_info, url_pagina, prioridade)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, numero_chamado, protocolo, created_at
            """, (numero_chamado, protocolo, empresa_id, usuario_id, usuario_nome,
                  titulo, descricao, console_logs, navegador_info, url_pagina, prioridade))

            row = cur.fetchone()
            print(f"✅ [criar_chamado] Chamado criado: id={row['id']}, numero={row['numero_chamado']}, empresa_id={empresa_id}, usuario={usuario_nome}")

            # Verificar se realmente persistiu
            cur.execute("SELECT COUNT(*) as total FROM chamados_suporte")
            total = cur.fetchone()['total']
            print(f"✅ [criar_chamado] Total de chamados na tabela agora: {total}")

            return jsonify({
                'success': True,
                'message': 'Chamado criado com sucesso!',
                'chamado': {
                    'id': row['id'],
                    'numero_chamado': row['numero_chamado'],
                    'protocolo': row['protocolo'],
                    'created_at': str(row['created_at'])
                }
            })
    except Exception as e:
        print(f"❌ Erro ao criar chamado: {e}")
        return jsonify({'error': str(e)}), 500


@suporte_bp.route('/chamados/<int:chamado_id>', methods=['GET'])
def detalhe_chamado(chamado_id):
    """Retorna detalhes de um chamado específico."""
    try:
        from database_postgresql import get_db_connection

        info = _get_user_info()
        if not info:
            return jsonify({'error': 'Não autenticado'}), 401

        usuario_id = info['user_id']
        empresa_id = info['empresa_id']
        tipo_usuario = info['user_type']

        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_chamados_table(cur)

            if tipo_usuario == 'admin':
                # Admin pode ver qualquer chamado
                cur.execute("""
                    SELECT * FROM chamados_suporte WHERE id = %s
                """, (chamado_id,))
            else:
                cur.execute("""
                    SELECT * FROM chamados_suporte WHERE id = %s AND empresa_id = %s
                """, (chamado_id, empresa_id))

            chamado = cur.fetchone()
            if not chamado:
                return jsonify({'error': 'Chamado não encontrado'}), 404

            # Usuário não-admin só pode ver seus próprios chamados
            if tipo_usuario != 'admin' and chamado['usuario_id'] != usuario_id:
                return jsonify({'error': 'Acesso negado'}), 403

            return jsonify({'success': True, 'chamado': dict(chamado)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@suporte_bp.route('/chamados/<int:chamado_id>/status', methods=['PUT', 'POST', 'PATCH'])
def atualizar_status_chamado(chamado_id):
    """Admin atualiza status e/ou resposta do chamado."""
    print(f"\n🔧 [SUPORTE] atualizar_status_chamado chamado_id={chamado_id} method={request.method}")
    try:
        from database_postgresql import get_db_connection

        info = _get_user_info()
        if not info:
            return jsonify({'error': 'Não autenticado'}), 401

        tipo_usuario = info['user_type']
        if tipo_usuario != 'admin':
            return jsonify({'error': 'Apenas administradores podem alterar status'}), 403

        data = request.json
        novo_status = data.get('status')
        resposta = data.get('resposta_admin', '')
        admin_id = info['user_id']
        admin_nome = info['user_name']

        if novo_status not in ('aberto', 'em_andamento', 'resolvido'):
            return jsonify({'error': 'Status inválido'}), 400

        # Textos padrão de notificação por status
        _notif_config = {
            'em_andamento': {
                'titulo': '🟡 Chamado em Andamento',
                'mensagem': 'Seu chamado {numero} está sendo analisado pela equipe de suporte.',
                'tipo': 'info',
                'dias_validade': 7,
            },
            'resolvido': {
                'titulo': '🟢 Chamado Resolvido',
                'mensagem': 'Seu chamado {numero} foi resolvido pela equipe de suporte.',
                'tipo': 'success',
                'dias_validade': 14,
            },
            'aberto': {
                'titulo': '🔴 Chamado Reaberto',
                'mensagem': 'Seu chamado {numero} foi reaberto para reavaliação.',
                'tipo': 'warning',
                'dias_validade': 7,
            },
        }

        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_chamados_table(cur)

            resolvido_clause = ", resolvido_em = NOW()" if novo_status == 'resolvido' else ""

            # Admin pode atualizar qualquer chamado (sem filtro empresa_id)
            cur.execute(f"""
                UPDATE chamados_suporte
                SET status = %s,
                    resposta_admin = COALESCE(%s, resposta_admin),
                    admin_id = %s,
                    admin_nome = %s,
                    updated_at = NOW()
                    {resolvido_clause}
                WHERE id = %s
                RETURNING id, numero_chamado, status, usuario_id, titulo
            """, (novo_status, resposta, admin_id, admin_nome, chamado_id))

            row = cur.fetchone()
            if not row:
                # Debug: verificar se o chamado existe
                cur.execute("SELECT id, status, empresa_id FROM chamados_suporte WHERE id = %s", (chamado_id,))
                existing = cur.fetchone()
                print(f"⚠️ [SUPORTE] UPDATE retornou vazio. chamado_id={chamado_id}, existe_no_banco={dict(existing) if existing else 'NÃO'}")
                return jsonify({'error': 'Chamado não encontrado'}), 404

            print(f"✅ [SUPORTE] Chamado {row['numero_chamado']} atualizado para {novo_status}")

            # Criar notificação in-app para o usuário do chamado
            try:
                import json as _json
                from datetime import datetime, timedelta

                notif = _notif_config.get(novo_status, _notif_config['em_andamento'])
                numero_chamado = row['numero_chamado']
                titulo_chamado = row['titulo']

                notif_titulo = notif['titulo']
                notif_msg = notif['mensagem'].format(numero=numero_chamado)
                if resposta:
                    notif_msg += f'\n\n💬 Resposta do suporte: {resposta}'
                notif_msg += f'\n📋 Assunto: {titulo_chamado}'

                expira_em = datetime.now() + timedelta(days=notif['dias_validade'])
                usuario_id_chamado = row['usuario_id']

                cur.execute("""
                    INSERT INTO avisos_sistema
                        (titulo, mensagem, tipo, destinatario, usuario_ids, expira_em, criado_por_nome)
                    VALUES (%s, %s, %s, 'usuarios', %s, %s, %s)
                """, (
                    notif_titulo,
                    notif_msg,
                    notif['tipo'],
                    _json.dumps([usuario_id_chamado]),
                    expira_em,
                    admin_nome,
                ))
                print(f"🔔 [SUPORTE] Notificação criada para usuario_id={usuario_id_chamado}")
            except Exception as notif_err:
                # Não falhar o update por causa da notificação
                print(f"⚠️ [SUPORTE] Erro ao criar notificação: {notif_err}")

            return jsonify({
                'success': True,
                'message': f'Chamado {row["numero_chamado"]} atualizado para {novo_status}',
                'chamado': dict(row)
            })
    except Exception as e:
        print(f"❌ Erro ao atualizar chamado: {e}")
        return jsonify({'error': str(e)}), 500


@suporte_bp.route('/chamados/stats', methods=['GET'])
def stats_chamados():
    """Estatísticas de chamados para o painel admin."""
    try:
        from database_postgresql import get_db_connection

        info = _get_user_info()
        tipo_usuario = info['user_type'] if info else 'cliente'

        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_chamados_table(cur)

            # Admin vê stats de TODOS; usuário normal vê só da sua empresa
            if tipo_usuario == 'admin':
                cur.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE status = 'aberto') AS abertos,
                        COUNT(*) FILTER (WHERE status = 'em_andamento') AS em_andamento,
                        COUNT(*) FILTER (WHERE status = 'resolvido') AS resolvidos,
                        COUNT(*) AS total
                    FROM chamados_suporte
                """)
            else:
                empresa_id = info['empresa_id'] if info else None
                cur.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE status = 'aberto') AS abertos,
                        COUNT(*) FILTER (WHERE status = 'em_andamento') AS em_andamento,
                        COUNT(*) FILTER (WHERE status = 'resolvido') AS resolvidos,
                        COUNT(*) AS total
                    FROM chamados_suporte
                    WHERE empresa_id = %s
                """, (empresa_id,))

            row = cur.fetchone()
            return jsonify({
                'success': True,
                'stats': dict(row) if row else {'abertos': 0, 'em_andamento': 0, 'resolvidos': 0, 'total': 0}
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Rota admin: listar TODOS os chamados (cross-empresa)
# ---------------------------------------------------------------------------
@suporte_bp.route('/admin/chamados', methods=['GET'])
def admin_listar_chamados():
    """Lista TODOS os chamados para o painel admin (super admin vê tudo)."""
    try:
        from database_postgresql import get_db_connection

        info = _get_user_info()
        if not info:
            print("❌ [admin_chamados] Usuário não autenticado")
            return jsonify({'error': 'Não autenticado'}), 401

        tipo_usuario = info['user_type']
        if tipo_usuario != 'admin':
            print(f"❌ [admin_chamados] Acesso negado - tipo: {tipo_usuario}")
            return jsonify({'error': 'Acesso negado'}), 403

        status_filter = request.args.get('status', '')

        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_chamados_table(cur)

            # Debug: contar total na tabela
            cur.execute("SELECT COUNT(*) as total FROM chamados_suporte")
            total_row = cur.fetchone()
            total_geral = total_row['total'] if total_row else 0
            print(f"🔍 [admin_chamados] Total de chamados na tabela: {total_geral}")

            # Admin vê TODOS os chamados (sem filtro de empresa)
            if status_filter and status_filter in ('aberto', 'em_andamento', 'resolvido'):
                cur.execute("""
                    SELECT * FROM chamados_suporte
                    WHERE status = %s
                    ORDER BY created_at DESC
                """, (status_filter,))
            else:
                cur.execute("""
                    SELECT * FROM chamados_suporte
                    ORDER BY
                        CASE status
                            WHEN 'aberto' THEN 1
                            WHEN 'em_andamento' THEN 2
                            WHEN 'resolvido' THEN 3
                        END,
                        created_at DESC
                """)

            chamados = cur.fetchall()
            result = [dict(c) for c in chamados] if chamados else []
            print(f"✅ [admin_chamados] Retornando {len(result)} chamados")
            return jsonify({
                'success': True,
                'chamados': result
            })
    except Exception as e:
        print(f"❌ [admin_chamados] Erro: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@suporte_bp.route('/debug/status', methods=['GET'])
def debug_chamados_status():
    """Rota de debug para verificar estado dos chamados no banco."""
    try:
        from database_postgresql import get_db_connection

        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_chamados_table(cur)

            cur.execute("SELECT COUNT(*) as total FROM chamados_suporte")
            total = cur.fetchone()['total']

            cur.execute("""
                SELECT id, numero_chamado, empresa_id, usuario_nome, status, titulo,
                       created_at
                FROM chamados_suporte
                ORDER BY created_at DESC
                LIMIT 10
            """)
            chamados = cur.fetchall()

            return jsonify({
                'success': True,
                'total_chamados': total,
                'ultimos_10': [dict(c) for c in chamados] if chamados else [],
                'tabela_existe': True
            })
    except Exception as e:
        return jsonify({'error': str(e), 'tabela_existe': False}), 500
