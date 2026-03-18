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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

        usuario_id = session.get('user_id')
        empresa_id = session.get('empresa_id', 1)
        tipo_usuario = session.get('user_type', 'cliente')

        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_chamados_table(cur)

            if tipo_usuario == 'admin':
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

        data = request.json
        usuario_id = session.get('user_id')
        usuario_nome = session.get('user_name', 'Usuário')
        empresa_id = session.get('empresa_id', 1)

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

        usuario_id = session.get('user_id')
        empresa_id = session.get('empresa_id', 1)
        tipo_usuario = session.get('user_type', 'cliente')

        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_chamados_table(cur)

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


@suporte_bp.route('/chamados/<int:chamado_id>/status', methods=['PUT'])
def atualizar_status_chamado(chamado_id):
    """Admin atualiza status e/ou resposta do chamado."""
    try:
        from database_postgresql import get_db_connection

        tipo_usuario = session.get('user_type', 'cliente')
        if tipo_usuario != 'admin':
            return jsonify({'error': 'Apenas administradores podem alterar status'}), 403

        data = request.json
        novo_status = data.get('status')
        resposta = data.get('resposta_admin', '')
        admin_id = session.get('user_id')
        admin_nome = session.get('user_name', 'Admin')
        empresa_id = session.get('empresa_id', 1)

        if novo_status not in ('aberto', 'em_andamento', 'resolvido'):
            return jsonify({'error': 'Status inválido'}), 400

        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_chamados_table(cur)

            resolvido_clause = ", resolvido_em = NOW()" if novo_status == 'resolvido' else ""

            cur.execute(f"""
                UPDATE chamados_suporte
                SET status = %s,
                    resposta_admin = COALESCE(%s, resposta_admin),
                    admin_id = %s,
                    admin_nome = %s,
                    updated_at = NOW()
                    {resolvido_clause}
                WHERE id = %s AND empresa_id = %s
                RETURNING id, numero_chamado, status
            """, (novo_status, resposta, admin_id, admin_nome, chamado_id, empresa_id))

            row = cur.fetchone()
            if not row:
                return jsonify({'error': 'Chamado não encontrado'}), 404

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

        empresa_id = session.get('empresa_id', 1)

        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_chamados_table(cur)

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
    """Lista todos os chamados para o painel admin (filtra por empresa_id da session)."""
    try:
        from database_postgresql import get_db_connection

        tipo_usuario = session.get('user_type', 'cliente')
        if tipo_usuario != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403

        status_filter = request.args.get('status', '')
        empresa_id = session.get('empresa_id', 1)

        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_chamados_table(cur)

            if status_filter and status_filter in ('aberto', 'em_andamento', 'resolvido'):
                cur.execute("""
                    SELECT * FROM chamados_suporte
                    WHERE empresa_id = %s AND status = %s
                    ORDER BY created_at DESC
                """, (empresa_id, status_filter))
            else:
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

            chamados = cur.fetchall()
            return jsonify({
                'success': True,
                'chamados': [dict(c) for c in chamados] if chamados else []
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
