"""
Blueprint de Remessa de Pagamentos - Sicredi
Rotas para gerenciamento de remessas bancárias CNAB 240
Extraído como módulo independente - não afeta outras rotas
"""
from flask import Blueprint, request, jsonify, send_file, session
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict
import io
import sys
import os

# Adicionar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Importar dependências do projeto
import database_postgresql as db
from auth_middleware import require_permission
from app.utils.remessa_pagamento import (
    GeradorCNAB240, ProcessadorRetornoCNAB240,
    validar_cpf, validar_cnpj, validar_codigo_barras, validar_dados_bancarios,
    gerar_hash_remessa, formatar_nome_arquivo_remessa
)

# Criar blueprint (NÃO AFETA OUTRAS ROTAS)
remessa_bp = Blueprint('remessa', __name__, url_prefix='/api/remessa')


# ============================================================================
# ROTAS DE CONSULTA
# ============================================================================

@remessa_bp.route('/contas-pagar/pendentes', methods=['GET'])
@require_permission('remessa_view')
def listar_contas_pagar_pendentes():
    """
    Lista contas a pagar pendentes para inclusão em remessa
    Não afeta nenhuma outra funcionalidade do sistema
    """
    try:
        # Obter empresa da sessão (segurança multi-tenant)
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 401
        
        # Filtros opcionais
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        tipo_pagamento = request.args.get('tipo_pagamento')
        vencimento = request.args.get('vencimento')
        
        # USAR CONTEXT MANAGER - conexão sempre retorna ao pool
        with db.get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            # Usar view otimizada criada na migration
            query = """
                SELECT 
                    id, descricao, fornecedor, data_vencimento, valor,
                    tipo_pagamento_sugerido, status_vencimento, categoria,
                    banco_favorecido, agencia_favorecido, conta_favorecido,
                    chave_pix, tipo_chave_pix, codigo_barras
                FROM v_contas_pagar_pendentes_remessa
                WHERE empresa_id = %s
            """
            params = [empresa_id]
            
            # Aplicar filtros
            if data_inicio:
                query += " AND data_vencimento >= %s"
                params.append(data_inicio)
            
            if data_fim:
                query += " AND data_vencimento <= %s"
                params.append(data_fim)
            
            if tipo_pagamento and tipo_pagamento != 'TODOS':
                query += " AND tipo_pagamento_sugerido = %s"
                params.append(tipo_pagamento)
            
            if vencimento and vencimento != 'TODOS':
                query += " AND status_vencimento = %s"
                params.append(vencimento)
            
            query += " ORDER BY data_vencimento ASC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            contas = []
            total_valor = 0
            por_tipo = {}
            
            for row in rows:
                conta = {
                    'id': row[0],
                    'descricao': row[1],
                    'fornecedor': row[2],
                    'data_vencimento': row[3].isoformat() if row[3] else None,
                    'valor': float(row[4]) if row[4] else 0,
                    'tipo_pagamento_sugerido': row[5],
                    'status_vencimento': row[6],
                    'categoria': row[7],
                    'banco_favorecido': row[8],
                    'agencia_favorecido': row[9],
                    'conta_favorecido': row[10],
                    'chave_pix': row[11],
                    'tipo_chave_pix': row[12],
                    'codigo_barras': row[13]
                }
                contas.append(conta)
                
                # Estatísticas
                total_valor += conta['valor']
                tipo = conta['tipo_pagamento_sugerido']
                if tipo not in por_tipo:
                    por_tipo[tipo] = {'quantidade': 0, 'valor': 0}
                por_tipo[tipo]['quantidade'] += 1
                por_tipo[tipo]['valor'] += conta['valor']
            
            cursor.close()
        # Conexão automaticamente retorna ao pool aqui
        
        return jsonify({
            'success': True,
            'contas': contas,
            'total': len(contas),
            'total_valor': total_valor,
            'por_tipo': por_tipo
        })
        
    except Exception as e:
        print(f"❌ Erro ao listar contas pendentes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@remessa_bp.route('/historico', methods=['GET'])
@require_permission('remessa_view')
def listar_historico():
    """Lista histórico de remessas geradas"""
    try:
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 401
        
        limite = int(request.args.get('limite', 50))
        offset = int(request.args.get('offset', 0))
        status = request.args.get('status')
        
        # USAR CONTEXT MANAGER - conexão sempre retorna ao pool
        with db.get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM v_remessas_resumo
                WHERE empresa_id = %s
            """
            params = [empresa_id]
            
            if status:
                query += " AND status = %s"
                params.append(status)
            
            query += " ORDER BY data_geracao DESC LIMIT %s OFFSET %s"
            params.extend([limite, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            remessas = []
            for row in rows:
                remessas.append({
                    'id': row[0],
                    'numero_sequencial': row[2],
                    'nome_arquivo': row[4],
                    'quantidade_pagamentos': row[6],
                    'quantidade_ted': row[7],
                    'quantidade_pix': row[8],
                    'quantidade_boleto': row[9],
                    'quantidade_tributo': row[10],
                    'valor_total': float(row[11]) if row[11] else 0,
                    'status': row[12],
                    'data_geracao': row[13].isoformat() if row[13] else None,
                    'empresa_nome': row[21] if len(row) > 21 else None,
                    'criado_por_nome': row[22] if len(row) > 22 else None
                })
            
            # Contar total
            cursor.execute("SELECT COUNT(*) FROM remessas_pagamento WHERE empresa_id = %s", [empresa_id])
            total = cursor.fetchone()[0]
            
            cursor.close()
        # Conexão automaticamente retorna ao pool aqui
        
        return jsonify({
            'success': True,
            'remessas': remessas,
            'total': total,
            'limite': limite,
            'offset': offset
        })
        
    except Exception as e:
        print(f"❌ Erro ao listar histórico: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@remessa_bp.route('/<int:remessa_id>', methods=['GET'])
@require_permission('remessa_view')
def obter_detalhes(remessa_id):
    """Obtém detalhes completos de uma remessa"""
    try:
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 401
        
        # USAR CONTEXT MANAGER - conexão sempre retorna ao pool
        with db.get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            # Buscar remessa (validar empresa_id para segurança)
            cursor.execute("""
                SELECT * FROM remessas_pagamento 
                WHERE id = %s AND empresa_id = %s
            """, [remessa_id, empresa_id])
            
            row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Remessa não encontrada'}), 404
            
            remessa = {
                'id': row[0],
                'numero_sequencial': row[2],
                'tipo_arquivo': row[3],
                'nome_arquivo': row[4],
                'hash_arquivo': row[5],
                'quantidade_pagamentos': row[6],
                'valor_total': float(row[11]) if row[11] else 0,
                'status': row[12],
                'data_geracao': row[13].isoformat() if row[13] else None,
                'observacoes': row[20]
            }
            
            # Buscar itens
            cursor.execute("""
                SELECT * FROM remessas_pagamento_itens 
                WHERE remessa_id = %s 
                ORDER BY sequencial_lote, sequencial_registro
            """, [remessa_id])
            
            itens_rows = cursor.fetchall()
            itens = []
            
            for item_row in itens_rows:
                itens.append({
                    'id': item_row[0],
                    'tipo_pagamento': item_row[3],
                    'nome_favorecido': item_row[6],
                    'cpf_cnpj_favorecido': item_row[7],
                    'banco_favorecido': item_row[8],
                    'agencia_favorecido': item_row[9],
                    'conta_favorecido': item_row[10],
                    'chave_pix': item_row[12],
                    'valor_total': float(item_row[20]) if item_row[20] else 0,
                    'data_pagamento': item_row[22].isoformat() if item_row[22] else None,
                    'status': item_row[25]
                })
            
            remessa['itens'] = itens
            
            cursor.close()
        # Conexão automaticamente retorna ao pool aqui
        
        return jsonify({'success': True, 'remessa': remessa})
        
    except Exception as e:
        print(f"❌ Erro ao obter detalhes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROTAS DE AÇÃO
# ============================================================================

@remessa_bp.route('/gerar', methods=['POST'])
@require_permission('remessa_criar')
def gerar_remessa():
    """
    Gera arquivo CNAB 240 com lançamentos selecionados
    Operação atômica com rollback em caso de erro
    """
    try:
        from auth_middleware import get_usuario_logado
        
        # Obter usuario_id corretamente via get_usuario_logado()
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
        
        empresa_id = session.get('empresa_id')
        usuario_id = usuario.get('id')
        
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 401
        
        data_request = request.get_json()
        lancamentos_ids = data_request.get('lancamentos', [])
        data_pagamento = data_request.get('data_pagamento')
        observacoes = data_request.get('observacoes', '')
        
        if not lancamentos_ids:
            return jsonify({'success': False, 'error': 'Nenhum lançamento selecionado'}), 400
        
        if not data_pagamento:
            return jsonify({'success': False, 'error': 'Data de pagamento obrigatória'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Iniciar transação
        conn.autocommit = False
        
        try:
            # 1. Buscar configuração Sicredi
            cursor.execute("""
                SELECT codigo_beneficiario, codigo_convenio, agencia, conta
                FROM sicredi_configuracao
                WHERE empresa_id = %s AND ativo = TRUE
            """, [empresa_id])
            
            config_row = cursor.fetchone()
            if not config_row:
                raise Exception("Configuração Sicredi não encontrada. Configure antes de gerar remessa.")
            
            convenio = {
                'codigo_beneficiario': config_row[0],
                'codigo_convenio': config_row[1]
            }
            
            # 2. Buscar dados da empresa
            cursor.execute("""
                SELECT razao_social, cnpj
                FROM empresas
                WHERE id = %s
            """, [empresa_id])
            
            empresa_row = cursor.fetchone()
            empresa = {
                'razao_social': empresa_row[0],
                'cnpj': empresa_row[1],
                'agencia': config_row[2],
                'conta': config_row[3]
            }
            
            # 3. Buscar lançamentos com dados dos fornecedores
            placeholders = ','.join(['%s'] * len(lancamentos_ids))
            cursor.execute(f"""
                SELECT 
                    l.id, l.descricao, l.valor, l.data_vencimento, l.codigo_barras,
                    f.nome, f.cpf_cnpj, f.banco, f.agencia, f.conta, 
                    f.chave_pix, f.tipo_chave_pix
                FROM lancamentos l
                LEFT JOIN fornecedores f ON l.fornecedor_id = f.id
                WHERE l.id IN ({placeholders})
                  AND l.empresa_id = %s
                  AND l.status = 'PENDENTE'
            """, lancamentos_ids + [empresa_id])
            
            lancamentos_rows = cursor.fetchall()
            
            if not lancamentos_rows:
                raise Exception("Nenhum lançamento válido encontrado")
            
            # 4. Classificar pagamentos por tipo
            pagamentos = []
            quantidade_ted = 0
            quantidade_pix = 0
            quantidade_boleto = 0
            quantidade_tributo = 0
            valor_total = 0
            
            for row in lancamentos_rows:
                lancamento_id = row[0]
                valor = float(row[2]) if row[2] else 0
                favorecido = row[5]
                cpf_cnpj = row[6]
                banco = row[7]
                agencia = row[8]
                conta = row[9]
                chave_pix = row[10]
                tipo_chave = row[11]
                codigo_barras = row[4]
                
                pagamento = {
                    'lancamento_id': lancamento_id,
                    'favorecido': favorecido or 'Sem nome',
                    'cpf_cnpj': cpf_cnpj,
                    'valor': valor,
                    'data_pagamento': datetime.strptime(data_pagamento, '%Y-%m-%d').date(),
                    'data_vencimento': row[3],
                    'seu_numero': str(lancamento_id)
                }
                
                # Classificar tipo
                if codigo_barras:
                    pagamento['tipo'] = 'BOLETO'
                    pagamento['codigo_barras'] = codigo_barras
                    quantidade_boleto += 1
                elif chave_pix:
                    pagamento['tipo'] = 'PIX'
                    pagamento['chave_pix'] = chave_pix
                    pagamento['tipo_chave'] = tipo_chave or 'ALEATORIA'
                    quantidade_pix += 1
                elif banco and agencia and conta:
                    pagamento['tipo'] = 'TED'
                    pagamento['banco'] = banco
                    pagamento['agencia'] = agencia
                    pagamento['conta'] = conta
                    quantidade_ted += 1
                else:
                    # Pular pagamentos sem dados suficientes
                    continue
                
                pagamentos.append(pagamento)
                valor_total += valor
            
            if not pagamentos:
                raise Exception("Nenhum pagamento com dados bancários completos")
            
            # 5. Gerar arquivo CNAB
            gerador = GeradorCNAB240(empresa, convenio)
            conteudo_cnab = gerador.gerar_remessa(pagamentos)
            
            # 6. Calcular hash
            hash_arquivo = gerar_hash_remessa(conteudo_cnab)
            
            # 7. Obter próximo sequencial (função atômica)
            cursor.execute("SELECT obter_proximo_sequencial_remessa(%s)", [empresa_id])
            sequencial = cursor.fetchone()[0]
            
            # 8. Formatar nome arquivo
            nome_arquivo = formatar_nome_arquivo_remessa(empresa_id, sequencial, date.today())
            
            # 9. Inserir remessa
            cursor.execute("""
                INSERT INTO remessas_pagamento (
                    empresa_id, numero_sequencial, tipo_arquivo, nome_arquivo, hash_arquivo,
                    quantidade_pagamentos, quantidade_ted, quantidade_pix, quantidade_boleto, quantidade_tributo,
                    valor_total, status, data_geracao, arquivo_retorno, created_by, observacoes
                ) VALUES (
                    %s, %s, 'CNAB240', %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, 'GERADO', CURRENT_TIMESTAMP, %s, %s, %s
                ) RETURNING id
            """, [
                empresa_id, sequencial, nome_arquivo, hash_arquivo,
                len(pagamentos), quantidade_ted, quantidade_pix, quantidade_boleto, quantidade_tributo,
                valor_total, conteudo_cnab, usuario_id, observacoes
            ])
            
            remessa_id = cursor.fetchone()[0]
            
            # 10. Inserir itens
            sequencial_registro = 1
            for pag in pagamentos:
                cursor.execute("""
                    INSERT INTO remessas_pagamento_itens (
                        remessa_id, lancamento_id, tipo_pagamento,
                        sequencial_lote, sequencial_registro,
                        nome_favorecido, cpf_cnpj_favorecido,
                        banco_favorecido, agencia_favorecido, conta_favorecido,
                        chave_pix, tipo_chave_pix, codigo_barras,
                        valor_total, data_vencimento, data_pagamento,
                        seu_numero, status
                    ) VALUES (
                        %s, %s, %s, 1, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s, 'PENDENTE'
                    )
                """, [
                    remessa_id, pag['lancamento_id'], pag['tipo'], sequencial_registro,
                    pag['favorecido'], pag.get('cpf_cnpj'),
                    pag.get('banco'), pag.get('agencia'), pag.get('conta'),
                    pag.get('chave_pix'), pag.get('tipo_chave'), pag.get('codigo_barras'),
                    pag['valor'], pag.get('data_vencimento'), pag['data_pagamento'],
                    pag['seu_numero']
                ])
                sequencial_registro += 1
            
            # 11. Atualizar lançamentos (marcar como incluídos em remessa)
            cursor.execute(f"""
                UPDATE lancamentos
                SET remessa_id = %s, status_remessa = 'INCLUIDO'
                WHERE id IN ({placeholders})
            """, [remessa_id] + lancamentos_ids)
            
            # Commit da transação
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'remessa_id': remessa_id,
                'nome_arquivo': nome_arquivo,
                'sequencial': sequencial,
                'quantidade_pagamentos': len(pagamentos),
                'valor_total': valor_total,
                'hash': hash_arquivo,
                'conteudo_cnab': conteudo_cnab
            })
            
        except Exception as e:
            # Rollback em caso de erro
            conn.rollback()
            # IMPORTANTE: Fechar conexão mesmo após rollback
            try:
                cursor.close()
            except:
                pass
            try:
                conn.close()
            except:
                pass
            raise e
        
    except Exception as e:
        print(f"❌ Erro ao gerar remessa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@remessa_bp.route('/<int:remessa_id>/download', methods=['GET'])
@require_permission('remessa_view')
def download_remessa(remessa_id):
    """Faz download do arquivo CNAB"""
    try:
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 401
        
        # USAR CONTEXT MANAGER - conexão sempre retorna ao pool
        with db.get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT nome_arquivo, arquivo_retorno
                FROM remessas_pagamento
                WHERE id = %s AND empresa_id = %s
            """, [remessa_id, empresa_id])
            
            row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Remessa não encontrada'}), 404
            
            nome_arquivo = row[0]
            conteudo = row[1]
            
            cursor.close()
        # Conexão automaticamente retorna ao pool aqui
        
        # Retornar arquivo para download
        return send_file(
            io.BytesIO(conteudo.encode('utf-8')),
            mimetype='text/plain',
            as_attachment=True,
            download_name=nome_arquivo
        )
        
    except Exception as e:
        print(f"❌ Erro ao baixar remessa: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

@remessa_bp.route('/config', methods=['GET', 'POST', 'PUT'])
@require_permission('remessa_config')
def gerenciar_configuracao():
    """Gerencia configuração Sicredi da empresa"""
    try:
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 401
        
        # USAR CONTEXT MANAGER - conexão sempre retorna ao pool
        with db.get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            if request.method == 'GET':
                # Buscar configuração existente
                cursor.execute("""
                    SELECT * FROM sicredi_configuracao
                    WHERE empresa_id = %s
                """, [empresa_id])
                
                row = cursor.fetchone()
                
                if row:
                    config = {
                        'id': row[0],
                        'empresa_id': row[1],
                        'codigo_beneficiario': row[2],
                        'codigo_convenio': row[3],
                        'posto': row[4],
                        'codigo_cedente': row[5],
                        'banco': row[6],
                        'agencia': row[7],
                        'agencia_dv': row[8],
                        'conta': row[9],
                        'conta_dv': row[10],
                        'ultimo_sequencial_remessa': row[15]
                    }
                else:
                    config = None
                
                cursor.close()
                # Conexão automaticamente retorna ao pool aqui
                
                return jsonify({'success': True, 'configuracao': config})
            
            else:  # POST ou PUT
                data = request.get_json()
                
                # Validar campos obrigatórios
                campos_obrigatorios = ['codigo_beneficiario', 'codigo_convenio', 'agencia', 'conta']
                for campo in campos_obrigatorios:
                    if not data.get(campo):
                        return jsonify({'success': False, 'error': f'Campo {campo} é obrigatório'}), 400
                
                # Upsert (inserir ou atualizar)
                cursor.execute("""
                    INSERT INTO sicredi_configuracao (
                        empresa_id, codigo_beneficiario, codigo_convenio,
                        posto, codigo_cedente, agencia, conta, ativo
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, TRUE
                    )
                    ON CONFLICT (empresa_id) 
                    DO UPDATE SET
                        codigo_beneficiario = EXCLUDED.codigo_beneficiario,
                        codigo_convenio = EXCLUDED.codigo_convenio,
                        posto = EXCLUDED.posto,
                        codigo_cedente = EXCLUDED.codigo_cedente,
                        agencia = EXCLUDED.agencia,
                        conta = EXCLUDED.conta,
                        updated_at = CURRENT_TIMESTAMP
                """, [
                    empresa_id,
                    data['codigo_beneficiario'],
                    data['codigo_convenio'],
                    data.get('posto'),
                    data.get('codigo_cedente'),
                    data['agencia'],
                    data['conta']
                ])
                
                conn.commit()
                cursor.close()
            # Conexão automaticamente retorna ao pool aqui
            
            return jsonify({
                'success': True,
                'message': 'Configuração salva com sucesso'
            })
        
    except Exception as e:
        print(f"❌ Erro ao gerenciar configuração: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# PROCESSAMENTO DE RETORNO (TODO - Implementação futura)
# ============================================================================

@remessa_bp.route('/<int:remessa_id>/processar-retorno', methods=['POST'])
@require_permission('remessa_processar')
def processar_retorno(remessa_id):
    """
    Processa arquivo de retorno do banco
    TODO: Implementar upload e parsing completo
    """
    return jsonify({
        'success': False,
        'error': 'Funcionalidade em desenvolvimento'
    }), 501


print("✅ Blueprint 'remessa' carregado - Rotas independentes criadas em /api/remessa/*")
