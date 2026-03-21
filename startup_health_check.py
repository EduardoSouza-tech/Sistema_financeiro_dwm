"""
startup_health_check.py
=======================
Sistema de verificação e autocorreção de saúde no startup do Flask.

Responsabilidades:
  1. Verificar se todas as tabelas críticas existem (e criar se faltarem).
  2. Detectar problemas comuns de integridade de dados (ex: datas inválidas).
  3. Logar warnings claros para qualquer anomalia encontrada.

Como usar (em web_server.py, após db = DatabaseManager()):
    from startup_health_check import verificar_saude_startup
    verificar_saude_startup(db)
"""

import logging
import sys

logger = logging.getLogger(__name__)

# =============================================================================
# MAPA DE ROTAS → TABELAS DEPENDENTES
# Mantido aqui como fonte única da verdade para documentação e verificação.
# =============================================================================
ROTA_TABELA_MAP = {
    # Auth & Usuários
    "/api/auth/login":                   ["usuarios", "sessoes_login", "log_acessos"],
    "/api/auth/logout":                  ["sessoes_login"],
    "/api/auth/verify":                  ["sessoes_login", "usuarios"],
    "/api/auth/change-password":         ["usuarios"],
    "/api/auth/minhas-empresas":         ["usuarios", "empresas"],
    "/api/usuarios":                     ["usuarios", "permissoes", "usuario_permissoes"],
    "/api/permissoes":                   ["permissoes"],

    # Empresas
    "/api/empresas":                     ["empresas"],

    # Financeiro Core
    "/api/contas":                       ["contas_bancarias"],
    "/api/categorias":                   ["categorias"],
    "/api/lancamentos":                  ["lancamentos", "categorias", "contas_bancarias"],
    "/api/transferencias":               ["lancamentos", "contas_bancarias"],

    # Clientes & Fornecedores
    "/api/clientes":                     ["clientes"],
    "/api/fornecedores":                 ["fornecedores"],

    # Extratos & Conciliação
    "/api/extratos":                     ["transacoes_extrato", "contas_bancarias"],
    "/api/extratos/upload":              ["transacoes_extrato", "contas_bancarias"],
    "/api/regras-conciliacao":           ["conciliacoes"],
    "/api/config-extrato":               ["contas_bancarias"],
    "/api/ofx-filtros":                  ["ofx_filtros_memo"],

    # RH & Eventos
    "/api/funcionarios":                 ["funcionarios"],
    "/api/eventos":                      ["eventos", "funcionarios"],
    "/api/funcoes-evento":               ["funcoes_evento"],
    "/api/eventos/<id>/equipe":          ["evento_funcionarios", "funcionarios", "funcoes_evento", "eventos"],
    "/api/eventos/<id>/fornecedores":    ["eventos", "fornecedores"],

    # Comissões & Sessões
    "/api/comissoes":                    ["comissoes"],
    "/api/sessao-equipe":                ["sessao_equipe", "sessoes"],
    "/api/sessoes":                      ["sessoes", "tipos_sessao"],

    # Estoque / Produtos
    "/api/estoque/produtos":             ["produtos"],
    "/api/tags":                         ["tags"],
    "/api/templates-equipe":             ["templates_equipe"],
    "/api/custos-operacionais":          ["lancamentos", "categorias"],

    # Agenda
    "/api/agenda":                       ["agenda"],

    # Relatórios
    "/api/relatorios/dashboard":         ["lancamentos", "contas_bancarias", "categorias"],
    "/api/relatorios/fluxo-projetado":   ["lancamentos"],
    "/api/relatorios/analise-contas":    ["contas_bancarias", "lancamentos"],
    "/api/relatorios/inadimplencia":     ["lancamentos", "clientes"],

    # NFS-e
    "/api/nfse":                         ["nfse_config", "lancamentos"],

    # Contabilidade
    "/api/contabilidade":                ["lancamentos", "categorias"],
}

# =============================================================================
# TABELAS CRÍTICAS: existência é obrigatória para o sistema funcionar
# Order importa: tabelas com FK devem vir depois das referenciadas.
# =============================================================================
TABELAS_CRITICAS = [
    "empresas",
    "usuarios",
    "permissoes",
    "usuario_permissoes",
    "sessoes_login",
    "log_acessos",
    "contas_bancarias",
    "categorias",
    "clientes",
    "fornecedores",
    "lancamentos",
    "transacoes_extrato",
    "conciliacoes",
    "contratos",
    "agenda",
    "produtos",
    "kits",
    "kit_itens",
    "tags",
    "templates_equipe",
    "sessoes",
    "tipos_sessao",
    "comissoes",
    "sessao_equipe",
    "funcionarios",
    "eventos",
    "funcoes_evento",
    "evento_funcionarios",
    "compensacoes_horas",
]

# Tabelas criadas inline no web_server.py (não estão em criar_tabelas mas precisam existir)
TABELAS_INLINE = [
    "ofx_filtros_memo",
    "google_calendar_credentials",
    "logs_fiscais",
    "fiscal_cnpj_historico",
    "fiscal_certidoes",
]


# =============================================================================
# FUNÇÕES DE VERIFICAÇÃO
# =============================================================================

def _tabelas_existentes(conn) -> set:
    """Retorna o conjunto de tabelas existentes no schema public."""
    cur = conn.cursor()
    cur.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
    """)
    rows = cur.fetchall()
    cur.close()
    if rows and isinstance(rows[0], dict):
        return {r["tablename"] for r in rows}
    return {r[0] for r in rows}


def verificar_tabelas(db) -> dict:
    """
    Verifica se todas as tabelas críticas existem.
    Retorna dict com listas 'ok', 'faltando', 'criadas', 'erro'.
    Chama db.criar_tabelas() para auto-criar tabelas ausentes.
    """
    resultado = {"ok": [], "faltando": [], "criadas": [], "erro": []}

    try:
        with db.get_connection() as conn:
            existentes = _tabelas_existentes(conn)

        todas_necessarias = TABELAS_CRITICAS + TABELAS_INLINE
        faltando = [t for t in todas_necessarias if t not in existentes]

        if not faltando:
            logger.info("[HEALTH] Todas as %d tabelas críticas estão presentes.", len(todas_necessarias))
            resultado["ok"] = list(existentes & set(todas_necessarias))
            return resultado

        resultado["faltando"] = faltando
        logger.warning("[HEALTH] Tabelas ausentes detectadas: %s", faltando)
        logger.info("[HEALTH] Acionando criar_tabelas() para autocorreção...")

        try:
            db.criar_tabelas()
            logger.info("[HEALTH] criar_tabelas() executado com sucesso.")

            # Verificar novamente quais foram criadas
            with db.get_connection() as conn:
                existentes_apos = _tabelas_existentes(conn)

            for t in faltando:
                if t in existentes_apos:
                    resultado["criadas"].append(t)
                    logger.info("[HEALTH] ✅ Tabela '%s' criada com sucesso.", t)
                else:
                    resultado["erro"].append(t)
                    logger.error("[HEALTH] ❌ Tabela '%s' ainda ausente após criar_tabelas().", t)

        except Exception as e:
            logger.error("[HEALTH] Erro ao executar criar_tabelas(): %s", e)
            resultado["erro"] = faltando

    except Exception as e:
        logger.error("[HEALTH] Erro ao verificar tabelas: %s", e)
        resultado["erro"].append(str(e))

    return resultado


def verificar_datas_invalidas(db) -> list:
    """
    Verifica colunas DATE nas tabelas críticas em busca de anos fora do range Python (1-9999).
    Retorna lista de dicts com {'tabela', 'coluna', 'quantidade', 'exemplos'}.
    Não altera dados - apenas loga e retorna o relatório.
    """
    # Tabelas/colunas conhecidas com datas que podem ser problemáticas
    COLUNAS_DATA = [
        ("eventos", "data_evento"),
        ("lancamentos", "data_vencimento"),
        ("lancamentos", "data_pagamento"),
        ("agenda", "data_inicio"),
        ("agenda", "data_fim"),
        ("contratos", "data_inicio"),
        ("contratos", "data_fim"),
        ("funcionarios", "data_admissao"),
        ("funcionarios", "data_demissao"),
        ("funcionarios", "data_nascimento"),
    ]

    problemas = []

    try:
        with db.get_connection() as conn:
            existentes = _tabelas_existentes(conn)

            for tabela, coluna in COLUNAS_DATA:
                if tabela not in existentes:
                    continue
                try:
                    cur = conn.cursor()
                    cur.execute(f"""
                        SELECT COUNT(*) as qtd,
                               MIN(EXTRACT(YEAR FROM {coluna}::timestamp)) as min_ano,
                               MAX(EXTRACT(YEAR FROM {coluna}::timestamp)) as max_ano
                        FROM {tabela}
                        WHERE {coluna} IS NOT NULL
                          AND (
                              EXTRACT(YEAR FROM {coluna}::timestamp) > 9999
                              OR EXTRACT(YEAR FROM {coluna}::timestamp) < 1
                          )
                    """)
                    row = cur.fetchone()
                    cur.close()

                    if row:
                        qtd = row["qtd"] if isinstance(row, dict) else row[0]
                        min_ano = row["min_ano"] if isinstance(row, dict) else row[1]
                        max_ano = row["max_ano"] if isinstance(row, dict) else row[2]
                        if qtd and int(qtd) > 0:
                            logger.warning(
                                "[HEALTH] ⚠️  Datas inválidas em %s.%s: %d registro(s), "
                                "anos entre %s e %s.",
                                tabela, coluna, int(qtd), min_ano, max_ano
                            )
                            problemas.append({
                                "tabela": tabela,
                                "coluna": coluna,
                                "quantidade": int(qtd),
                                "ano_min": float(min_ano) if min_ano else None,
                                "ano_max": float(max_ano) if max_ano else None,
                            })
                except Exception as e:
                    logger.debug("[HEALTH] Não foi possível verificar %s.%s: %s", tabela, coluna, e)

    except Exception as e:
        logger.error("[HEALTH] Erro na verificação de datas: %s", e)

    if not problemas:
        logger.info("[HEALTH] Nenhuma data inválida encontrada.")

    return problemas


def verificar_saude_startup(db) -> dict:
    """
    Ponto de entrada principal. Chame logo após DatabaseManager() no startup.
    Executa todas as verificações e retorna um relatório consolidado.

    Exemplo:
        db = DatabaseManager()
        from startup_health_check import verificar_saude_startup
        relatorio = verificar_saude_startup(db)
    """
    print("\n" + "=" * 60)
    print("🏥 HEALTH CHECK – Verificação de integridade do sistema")
    print("=" * 60)

    relatorio = {}

    # 1. Verificar tabelas
    print("  [1/2] Verificando tabelas críticas...")
    relatorio["tabelas"] = verificar_tabelas(db)
    t = relatorio["tabelas"]
    print(f"        OK: {len(t.get('ok', []))} tabelas  |  "
          f"Faltando: {len(t.get('faltando', []))}  |  "
          f"Criadas agora: {len(t.get('criadas', []))}  |  "
          f"Erros: {len(t.get('erro', []))}")
    if t.get("criadas"):
        print(f"        ✅ Criadas: {', '.join(t['criadas'])}")
    if t.get("erro"):
        print(f"        ❌ Com erro: {', '.join(t['erro'])}")

    # 2. Verificar datas inválidas
    print("  [2/2] Verificando integridade de datas...")
    relatorio["datas_invalidas"] = verificar_datas_invalidas(db)
    if relatorio["datas_invalidas"]:
        for p in relatorio["datas_invalidas"]:
            print(f"        ⚠️  {p['tabela']}.{p['coluna']}: "
                  f"{p['quantidade']} registro(s) com ano "
                  f"{p['ano_min']:.0f}–{p['ano_max']:.0f}")
        print("        (A API retornará esses valores como string — não causará crash.)")
    else:
        print("        ✅ Nenhuma data inválida encontrada.")

    print("=" * 60 + "\n")
    return relatorio
