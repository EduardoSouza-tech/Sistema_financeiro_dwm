"""
Módulo de geração de backup do banco de dados.
Gera um .zip em memória com os dados de todas as empresas (um JSON por tabela),
para download manual pelo painel admin. Envio automático por e-mail foi desativado.
"""
import os
import json
import io
import zipfile
from datetime import datetime

import psycopg2
import psycopg2.extras


# ─── CONFIGURAÇÃO ────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv('DATABASE_URL', '')

# Tabelas que têm coluna empresa_id (dados isolados por empresa)
TABELAS_POR_EMPRESA = [
    'clientes',
    'fornecedores',
    'contas_bancarias',
    'categorias',
    'lancamentos',
    'contratos',
    'sessoes',
    'funcionarios',
    'eventos',
    'transacoes_extrato',
    'conciliacoes',
    'contrato_parcelas',
    'evento_funcionarios',
]

# Tabelas globais (sem empresa_id)
TABELAS_GLOBAIS = [
    'empresas',
    'usuarios',
    'permissoes',
    'usuario_permissoes',
]


def _json_default(obj):
    """Serializa tipos não-padrão (datetime, date, Decimal)"""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return str(obj)


def gerar_backup_zip_por_empresa():
    """
    Gera backup completo do banco separado por empresa.
    Estrutura do zip:
      empresa_1_NomeEmpresa/clientes.json
      empresa_1_NomeEmpresa/lancamentos.json
      ...
      _global/empresas.json
      _global/usuarios.json
      _resumo.json
    Retorna (bytes_do_zip, nome_do_arquivo, info_resumo).
    """
    agora = datetime.now()
    nome_arquivo = f"backup_DWM_empresas_{agora.strftime('%Y%m%d_%H%M')}.zip"

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Listar todas as empresas
    cur.execute("SELECT id, razao_social, nome_fantasia FROM empresas ORDER BY id")
    empresas = [dict(r) for r in cur.fetchall()]

    zip_buffer = io.BytesIO()
    resumo = {'empresas': {}, 'global': {}}

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Dados por empresa
        for empresa in empresas:
            eid = empresa['id']
            nome_empresa = (empresa.get('razao_social') or empresa.get('nome_fantasia') or f'empresa_{eid}')
            # Sanitizar nome para usar como pasta
            nome_pasta = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in nome_empresa)
            pasta = f"empresa_{eid}_{nome_pasta}"
            resumo['empresas'][pasta] = {}

            for tabela in TABELAS_POR_EMPRESA:
                try:
                    cur.execute(f"SELECT * FROM {tabela} WHERE empresa_id = %s ORDER BY id", (eid,))
                    rows = [dict(r) for r in cur.fetchall()]
                    conteudo = json.dumps(rows, ensure_ascii=False, indent=2, default=_json_default)
                    zf.writestr(f"{pasta}/{tabela}.json", conteudo)
                    resumo['empresas'][pasta][tabela] = len(rows)
                except Exception as e:
                    zf.writestr(f"{pasta}/{tabela}_ERRO.txt", str(e))
                    resumo['empresas'][pasta][tabela] = f'ERRO: {e}'

        # Tabelas globais
        for tabela in TABELAS_GLOBAIS:
            try:
                cur.execute(f"SELECT * FROM {tabela} ORDER BY id")
                rows = [dict(r) for r in cur.fetchall()]
                # Mascarar senhas
                if tabela == 'usuarios':
                    for row in rows:
                        if 'password_hash' in row:
                            row['password_hash'] = '*** REDACTED ***'
                conteudo = json.dumps(rows, ensure_ascii=False, indent=2, default=_json_default)
                zf.writestr(f"_global/{tabela}.json", conteudo)
                resumo['global'][tabela] = len(rows)
            except Exception as e:
                zf.writestr(f"_global/{tabela}_ERRO.txt", str(e))
                resumo['global'][tabela] = f'ERRO: {e}'

        total_registros = sum(
            v for emp_tabs in resumo['empresas'].values()
            for v in emp_tabs.values() if isinstance(v, int)
        ) + sum(v for v in resumo['global'].values() if isinstance(v, int))

        info = {
            'gerado_em': agora.isoformat(),
            'total_empresas': len(empresas),
            'total_registros': total_registros,
            'empresas': resumo['empresas'],
            'global': resumo['global'],
        }
        zf.writestr('_resumo.json', json.dumps(info, ensure_ascii=False, indent=2))

    cur.close()
    conn.close()

    zip_buffer.seek(0)
    return zip_buffer.read(), nome_arquivo, info
