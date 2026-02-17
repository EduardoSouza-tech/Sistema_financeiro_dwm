"""
Módulo de Contabilidade - Plano de Contas
Operações de banco de dados e lógica de negócios
"""
import logging
import traceback
from datetime import datetime
from database_postgresql import get_db_connection

logger = logging.getLogger(__name__)


# =============================================================================
# VERSÕES DO PLANO DE CONTAS
# =============================================================================

def listar_versoes(empresa_id):
    """Lista todas as versões do plano de contas da empresa"""
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome_versao, exercicio_fiscal, data_inicio, data_fim,
                   is_ativa, observacoes, created_at
            FROM plano_contas_versao
            WHERE empresa_id = %s
            ORDER BY exercicio_fiscal DESC, nome_versao
        """, (empresa_id,))
        
        colunas = [desc[0] for desc in cursor.description]
        versoes = []
        for row in cursor.fetchall():
            v = dict(zip(colunas, row))
            # Converter datas para string
            for key in ['data_inicio', 'data_fim', 'created_at']:
                if v.get(key):
                    v[key] = v[key].isoformat() if hasattr(v[key], 'isoformat') else str(v[key])
            versoes.append(v)
        cursor.close()
        return versoes


def criar_versao(empresa_id, dados):
    """Cria uma nova versão do plano de contas"""
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO plano_contas_versao 
                (empresa_id, nome_versao, exercicio_fiscal, data_inicio, data_fim, is_ativa, observacoes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            empresa_id,
            dados['nome_versao'],
            dados['exercicio_fiscal'],
            dados.get('data_inicio'),
            dados.get('data_fim'),
            dados.get('is_ativa', False),
            dados.get('observacoes', '')
        ))
        versao_id = cursor.fetchone()[0]
        
        # Se esta versão é ativa, desativar as outras
        if dados.get('is_ativa'):
            cursor.execute("""
                UPDATE plano_contas_versao 
                SET is_ativa = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE empresa_id = %s AND id != %s
            """, (empresa_id, versao_id))
        
        cursor.close()
        return versao_id


def atualizar_versao(empresa_id, versao_id, dados):
    """Atualiza uma versão do plano de contas"""
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE plano_contas_versao SET
                nome_versao = %s,
                exercicio_fiscal = %s,
                data_inicio = %s,
                data_fim = %s,
                is_ativa = %s,
                observacoes = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
        """, (
            dados['nome_versao'],
            dados['exercicio_fiscal'],
            dados.get('data_inicio'),
            dados.get('data_fim'),
            dados.get('is_ativa', False),
            dados.get('observacoes', ''),
            versao_id,
            empresa_id
        ))
        
        # Se esta versão é ativa, desativar as outras
        if dados.get('is_ativa'):
            cursor.execute("""
                UPDATE plano_contas_versao 
                SET is_ativa = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE empresa_id = %s AND id != %s
            """, (empresa_id, versao_id))
        
        cursor.close()
        return cursor.rowcount > 0


def excluir_versao(empresa_id, versao_id):
    """Exclui uma versão e todas as contas associadas"""
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        # CASCADE vai remover as contas associadas
        cursor.execute("""
            DELETE FROM plano_contas_versao 
            WHERE id = %s AND empresa_id = %s
        """, (versao_id, empresa_id))
        deleted = cursor.rowcount
        cursor.close()
        return deleted > 0


# =============================================================================
# CONTAS DO PLANO
# =============================================================================

def listar_contas(empresa_id, versao_id=None, classificacao=None, tipo_conta=None, busca=None):
    """Lista contas do plano com filtros opcionais"""
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT pc.id, pc.codigo, pc.descricao, pc.parent_id, pc.nivel, pc.ordem,
                   pc.tipo_conta, pc.classificacao, pc.natureza,
                   pc.is_bloqueada, pc.requer_centro_custo, pc.permite_lancamento,
                   pc.versao_id, pc.created_at, pc.updated_at
            FROM plano_contas pc
            WHERE pc.empresa_id = %s AND pc.deleted_at IS NULL
        """
        params = [empresa_id]
        
        if versao_id:
            query += " AND pc.versao_id = %s"
            params.append(versao_id)
        
        if classificacao:
            query += " AND pc.classificacao = %s"
            params.append(classificacao)
        
        if tipo_conta:
            query += " AND pc.tipo_conta = %s"
            params.append(tipo_conta)
        
        if busca:
            query += " AND (pc.codigo ILIKE %s OR pc.descricao ILIKE %s)"
            params.extend([f'%{busca}%', f'%{busca}%'])
        
        query += " ORDER BY pc.codigo"
        
        cursor.execute(query, params)
        colunas = [desc[0] for desc in cursor.description]
        contas = []
        for row in cursor.fetchall():
            c = dict(zip(colunas, row))
            for key in ['created_at', 'updated_at']:
                if c.get(key):
                    c[key] = c[key].isoformat() if hasattr(c[key], 'isoformat') else str(c[key])
            contas.append(c)
        cursor.close()
        return contas


def obter_arvore_contas(empresa_id, versao_id):
    """Retorna contas organizadas em estrutura de árvore"""
    contas = listar_contas(empresa_id, versao_id=versao_id)
    
    # Criar mapa de contas por id
    mapa = {c['id']: {**c, 'children': []} for c in contas}
    
    # Construir árvore
    raizes = []
    for conta in contas:
        if conta['parent_id'] and conta['parent_id'] in mapa:
            mapa[conta['parent_id']]['children'].append(mapa[conta['id']])
        else:
            raizes.append(mapa[conta['id']])
    
    return raizes


def criar_conta(empresa_id, dados):
    """Cria uma nova conta no plano"""
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # Calcular nível e validar parent
        nivel = 1
        parent_id = dados.get('parent_id')
        if parent_id:
            cursor.execute("""
                SELECT nivel, tipo_conta FROM plano_contas 
                WHERE id = %s AND empresa_id = %s AND deleted_at IS NULL
            """, (parent_id, empresa_id))
            parent = cursor.fetchone()
            if not parent:
                raise ValueError("Conta pai não encontrada")
            if parent[1] == 'analitica':
                raise ValueError("Não é possível adicionar subconta a uma conta analítica")
            nivel = parent[0] + 1
        
        # Validar código único
        cursor.execute("""
            SELECT id FROM plano_contas 
            WHERE empresa_id = %s AND versao_id = %s AND codigo = %s AND deleted_at IS NULL
        """, (empresa_id, dados['versao_id'], dados['codigo']))
        if cursor.fetchone():
            raise ValueError(f"Código {dados['codigo']} já existe nesta versão")
        
        # Calcular ordem
        cursor.execute("""
            SELECT COALESCE(MAX(ordem), 0) + 1 FROM plano_contas
            WHERE empresa_id = %s AND versao_id = %s AND parent_id IS NOT DISTINCT FROM %s
              AND deleted_at IS NULL
        """, (empresa_id, dados['versao_id'], parent_id))
        ordem = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO plano_contas 
                (empresa_id, versao_id, codigo, descricao, parent_id, nivel, ordem,
                 tipo_conta, classificacao, natureza, is_bloqueada, 
                 requer_centro_custo, permite_lancamento)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            empresa_id,
            dados['versao_id'],
            dados['codigo'],
            dados['descricao'],
            parent_id,
            nivel,
            ordem,
            dados.get('tipo_conta', 'analitica'),
            dados['classificacao'],
            dados.get('natureza', 'devedora'),
            dados.get('is_bloqueada', False),
            dados.get('requer_centro_custo', False),
            dados.get('permite_lancamento', True)
        ))
        conta_id = cursor.fetchone()[0]
        cursor.close()
        return conta_id


def atualizar_conta(empresa_id, conta_id, dados):
    """Atualiza uma conta existente"""
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # Verificar se conta existe
        cursor.execute("""
            SELECT id, versao_id FROM plano_contas 
            WHERE id = %s AND empresa_id = %s AND deleted_at IS NULL
        """, (conta_id, empresa_id))
        conta = cursor.fetchone()
        if not conta:
            raise ValueError("Conta não encontrada")
        
        # Verificar código duplicado
        cursor.execute("""
            SELECT id FROM plano_contas 
            WHERE empresa_id = %s AND versao_id = %s AND codigo = %s 
              AND id != %s AND deleted_at IS NULL
        """, (empresa_id, conta[1], dados['codigo'], conta_id))
        if cursor.fetchone():
            raise ValueError(f"Código {dados['codigo']} já existe nesta versão")
        
        cursor.execute("""
            UPDATE plano_contas SET
                codigo = %s,
                descricao = %s,
                tipo_conta = %s,
                classificacao = %s,
                natureza = %s,
                is_bloqueada = %s,
                requer_centro_custo = %s,
                permite_lancamento = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
        """, (
            dados['codigo'],
            dados['descricao'],
            dados.get('tipo_conta', 'analitica'),
            dados['classificacao'],
            dados.get('natureza', 'devedora'),
            dados.get('is_bloqueada', False),
            dados.get('requer_centro_custo', False),
            dados.get('permite_lancamento', True),
            conta_id,
            empresa_id
        ))
        cursor.close()
        return True


def excluir_conta(empresa_id, conta_id):
    """Soft delete de uma conta (e suas subcontas)"""
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # Verificar se a conta existe
        cursor.execute("""
            SELECT id FROM plano_contas 
            WHERE id = %s AND empresa_id = %s AND deleted_at IS NULL
        """, (conta_id, empresa_id))
        if not cursor.fetchone():
            raise ValueError("Conta não encontrada")
        
        # Soft delete da conta e subcontas recursivamente
        cursor.execute("""
            WITH RECURSIVE subcontas AS (
                SELECT id FROM plano_contas WHERE id = %s AND empresa_id = %s
                UNION ALL
                SELECT pc.id FROM plano_contas pc
                JOIN subcontas s ON pc.parent_id = s.id
                WHERE pc.empresa_id = %s AND pc.deleted_at IS NULL
            )
            UPDATE plano_contas SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id IN (SELECT id FROM subcontas)
        """, (conta_id, empresa_id, empresa_id))
        
        deleted = cursor.rowcount
        cursor.close()
        return deleted


def mover_conta(empresa_id, conta_id, novo_parent_id):
    """Move uma conta para outro pai (drag-and-drop)"""
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # Verificar conta
        cursor.execute("""
            SELECT id, versao_id, codigo FROM plano_contas
            WHERE id = %s AND empresa_id = %s AND deleted_at IS NULL
        """, (conta_id, empresa_id))
        conta = cursor.fetchone()
        if not conta:
            raise ValueError("Conta não encontrada")
        
        # Verificar novo parent (se informado)
        novo_nivel = 1
        if novo_parent_id:
            cursor.execute("""
                SELECT id, nivel, tipo_conta FROM plano_contas
                WHERE id = %s AND empresa_id = %s AND deleted_at IS NULL
            """, (novo_parent_id, empresa_id))
            parent = cursor.fetchone()
            if not parent:
                raise ValueError("Conta pai destino não encontrada")
            if parent[2] == 'analitica':
                raise ValueError("Não é possível mover para uma conta analítica")
            novo_nivel = parent[1] + 1
            
            # Verificar circularidade
            cursor.execute("""
                WITH RECURSIVE ascendentes AS (
                    SELECT id, parent_id FROM plano_contas WHERE id = %s
                    UNION ALL
                    SELECT pc.id, pc.parent_id FROM plano_contas pc
                    JOIN ascendentes a ON pc.id = a.parent_id
                )
                SELECT id FROM ascendentes WHERE id = %s
            """, (novo_parent_id, conta_id))
            if cursor.fetchone():
                raise ValueError("Movimento circular detectado")
        
        # Atualizar parent_id e nível
        cursor.execute("""
            UPDATE plano_contas SET
                parent_id = %s,
                nivel = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
        """, (novo_parent_id, novo_nivel, conta_id, empresa_id))
        
        # Atualizar níveis das subcontas recursivamente
        cursor.execute("""
            WITH RECURSIVE subcontas AS (
                SELECT id, %s as novo_nivel FROM plano_contas WHERE parent_id = %s AND empresa_id = %s AND deleted_at IS NULL
                UNION ALL
                SELECT pc.id, s.novo_nivel + 1 FROM plano_contas pc
                JOIN subcontas s ON pc.parent_id = s.id
                WHERE pc.empresa_id = %s AND pc.deleted_at IS NULL
            )
            UPDATE plano_contas SET nivel = subcontas.novo_nivel + 1
            FROM subcontas WHERE plano_contas.id = subcontas.id
        """, (novo_nivel, conta_id, empresa_id, empresa_id))
        
        cursor.close()
        return True


def importar_contas_csv(empresa_id, versao_id, linhas):
    """
    Importa contas de um CSV. Cada linha deve ter:
    codigo, descricao, tipo_conta, classificacao, natureza
    """
    importadas = 0
    erros = []
    
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        for i, linha in enumerate(linhas, 1):
            try:
                codigo = linha.get('codigo', '').strip()
                descricao = linha.get('descricao', '').strip()
                
                if not codigo or not descricao:
                    erros.append(f"Linha {i}: código ou descrição vazia")
                    continue
                
                # Determinar parent pelo código
                parent_id = None
                partes = codigo.rsplit('.', 1)
                if len(partes) > 1:
                    codigo_pai = partes[0]
                    cursor.execute("""
                        SELECT id FROM plano_contas
                        WHERE empresa_id = %s AND versao_id = %s AND codigo = %s AND deleted_at IS NULL
                    """, (empresa_id, versao_id, codigo_pai))
                    pai = cursor.fetchone()
                    if pai:
                        parent_id = pai[0]
                
                nivel = len(codigo.split('.'))
                tipo_conta = linha.get('tipo_conta', 'analitica').strip().lower()
                classificacao = linha.get('classificacao', 'ativo').strip().lower()
                natureza = linha.get('natureza', 'devedora').strip().lower()
                
                # Upsert
                cursor.execute("""
                    INSERT INTO plano_contas 
                        (empresa_id, versao_id, codigo, descricao, parent_id, nivel,
                         tipo_conta, classificacao, natureza)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (empresa_id, versao_id, codigo)
                    DO UPDATE SET descricao = EXCLUDED.descricao,
                                  tipo_conta = EXCLUDED.tipo_conta,
                                  classificacao = EXCLUDED.classificacao,
                                  natureza = EXCLUDED.natureza,
                                  updated_at = CURRENT_TIMESTAMP
                """, (empresa_id, versao_id, codigo, descricao, parent_id, nivel,
                      tipo_conta, classificacao, natureza))
                importadas += 1
                
            except Exception as e:
                erros.append(f"Linha {i}: {str(e)}")
        
        cursor.close()
    
    return {'importadas': importadas, 'erros': erros}


def exportar_contas(empresa_id, versao_id):
    """Exporta contas para lista de dicionários (para CSV/Excel)"""
    contas = listar_contas(empresa_id, versao_id=versao_id)
    return [{
        'codigo': c['codigo'],
        'descricao': c['descricao'],
        'tipo_conta': c['tipo_conta'],
        'classificacao': c['classificacao'],
        'natureza': c['natureza'],
        'nivel': c['nivel'],
        'is_bloqueada': c['is_bloqueada'],
        'requer_centro_custo': c['requer_centro_custo']
    } for c in contas]


def obter_versao_ativa(empresa_id):
    """Retorna a versão ativa do plano de contas"""
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome_versao, exercicio_fiscal, data_inicio, data_fim, observacoes
            FROM plano_contas_versao
            WHERE empresa_id = %s AND is_ativa = TRUE
            ORDER BY exercicio_fiscal DESC
            LIMIT 1
        """, (empresa_id,))
        row = cursor.fetchone()
        cursor.close()
        if row:
            return {
                'id': row[0], 'nome_versao': row[1], 'exercicio_fiscal': row[2],
                'data_inicio': row[3].isoformat() if row[3] else None,
                'data_fim': row[4].isoformat() if row[4] else None,
                'observacoes': row[5]
            }
        return None


def importar_plano_padrao(empresa_id, ano_fiscal=None):
    """
    Importa o plano de contas padrão para uma empresa
    Cria uma nova versão e adiciona todas as contas padrão
    
    Args:
        empresa_id: ID da empresa
        ano_fiscal: Ano fiscal (default: ano corrente)
    
    Returns:
        dict com versao_id, contas_criadas e erros
    """
    from plano_contas_padrao import obter_plano_contas_padrao
    from datetime import datetime
    
    if not ano_fiscal:
        ano_fiscal = datetime.now().year
    
    try:
        # Criar versão para o plano padrão
        versao_dados = {
            'nome_versao': f'Plano Padrão {ano_fiscal}',
            'exercicio_fiscal': ano_fiscal,
            'data_inicio': f'{ano_fiscal}-01-01',
            'data_fim': f'{ano_fiscal}-12-31',
            'is_ativa': True,
            'observacoes': 'Plano de contas padrão importado automaticamente'
        }
        
        versao_id = criar_versao(empresa_id, versao_dados)
        logger.info(f"Versão {versao_id} criada para empresa {empresa_id}")
        
        # Obter contas padrão
        contas_padrao = obter_plano_contas_padrao()
        
        # Mapa para resolver parent_id
        mapa_codigos = {}  # codigo -> id
        contas_criadas = 0
        erros = []
        
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            # Inserir contas em ordem (já vêm na ordem correta)
            for conta in contas_padrao:
                try:
                    # Resolver parent_id
                    parent_id = None
                    if conta['parent_codigo']:
                        parent_id = mapa_codigos.get(conta['parent_codigo'])
                        if not parent_id:
                            erros.append(f"Conta {conta['codigo']}: parent {conta['parent_codigo']} não encontrado")
                            continue
                    
                    # Determinar tipo_conta (sintética ou analítica)
                    # Se há contas que a referenciam como parent, é sintética
                    tipo_conta = 'sintetica' if any(c['parent_codigo'] == conta['codigo'] for c in contas_padrao) else 'analitica'
                    
                    # Determinar natureza baseada na classificação
                    if conta['classificacao'] in ['ativo', 'despesa']:
                        natureza = 'devedora'
                    elif conta['classificacao'] in ['passivo', 'patrimonio_liquido', 'receita']:
                        natureza = 'credora'
                    else:
                        natureza = 'devedora'
                    
                    # Calcular ordem
                    cursor.execute("""
                        SELECT COALESCE(MAX(ordem), 0) + 1 FROM plano_contas
                        WHERE empresa_id = %s AND versao_id = %s 
                          AND parent_id IS NOT DISTINCT FROM %s AND deleted_at IS NULL
                    """, (empresa_id, versao_id, parent_id))
                    ordem = cursor.fetchone()[0]
                    
                    # Inserir conta
                    cursor.execute("""
                        INSERT INTO plano_contas 
                            (empresa_id, versao_id, codigo, descricao, parent_id, nivel, ordem,
                             tipo_conta, classificacao, natureza, is_bloqueada, 
                             requer_centro_custo, permite_lancamento)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        empresa_id,
                        versao_id,
                        conta['codigo'],
                        conta['nome'],
                        parent_id,
                        conta['nivel'],
                        ordem,
                        tipo_conta,
                        conta['classificacao'],
                        natureza,
                        False,  # is_bloqueada
                        False,  # requer_centro_custo
                        tipo_conta == 'analitica'  # permite_lancamento apenas para analíticas
                    ))
                    
                    conta_id = cursor.fetchone()[0]
                    mapa_codigos[conta['codigo']] = conta_id
                    contas_criadas += 1
                    
                except Exception as e:
                    erros.append(f"Erro ao criar conta {conta['codigo']}: {str(e)}")
                    logger.error(f"Erro ao criar conta {conta['codigo']}: {str(e)}")
                    logger.error(traceback.format_exc())
            
            cursor.close()
        
        logger.info(f"Plano padrão importado: {contas_criadas} contas criadas, {len(erros)} erros")
        
        return {
            'versao_id': versao_id,
            'contas_criadas': contas_criadas,
            'erros': erros
        }
        
    except Exception as e:
        logger.error(f"Erro ao importar plano padrão: {str(e)}")
        logger.error(traceback.format_exc())
        raise
