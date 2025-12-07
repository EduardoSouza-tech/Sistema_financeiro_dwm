"""
Servidor Web para o Sistema Financeiro
"""
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from database import DatabaseManager
from database import pagar_lancamento as db_pagar_lancamento
from database import cancelar_lancamento as db_cancelar_lancamento
from database import obter_lancamento as db_obter_lancamento
from database import atualizar_cliente, atualizar_fornecedor
from models import ContaBancaria, Lancamento, Categoria, TipoLancamento, StatusLancamento
from decimal import Decimal
from datetime import datetime, date, timedelta
import json
import os
import sqlite3

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})

# Log de configuração
print("=" * 60)
print("CONFIGURAÇÃO DO SISTEMA")
print("=" * 60)
print(f"DATABASE_TYPE: {os.getenv('DATABASE_TYPE', 'sqlite')}")
print(f"DATABASE_URL exists: {bool(os.getenv('DATABASE_URL'))}")
print(f"PGHOST: {os.getenv('PGHOST', 'not set')}")
print(f"PGDATABASE: {os.getenv('PGDATABASE', 'not set')}")
print("=" * 60)

# Inicializar banco de dados
try:
    print("Inicializando DatabaseManager...")
    db = DatabaseManager()
    print("✅ DatabaseManager inicializado com sucesso!")
except Exception as e:
    print(f"❌ ERRO ao inicializar DatabaseManager: {e}")
    raise

# Migrar dados JSON se existir
if os.path.exists('dados_financeiros.json'):
    print("Migrando dados do JSON...")
    db.migrar_dados_json('dados_financeiros.json')
    print("✅ Migração concluída!")


# === ROTAS DE CONTAS BANCÁRIAS ===

@app.route('/api/contas', methods=['GET'])
def listar_contas():
    """Lista todas as contas bancárias com saldo real"""
    try:
        contas = db.listar_contas()
        lancamentos = db.listar_lancamentos()
        
        # Calcular saldo real de cada conta
        contas_com_saldo = []
        for c in contas:
            saldo_real = Decimal(str(c.saldo_inicial))
            
            # Somar/subtrair lançamentos pagos desta conta
            for lanc in lancamentos:
                if lanc.status == StatusLancamento.PAGO:
                    valor_decimal = Decimal(str(lanc.valor))
                    
                    if lanc.tipo == TipoLancamento.TRANSFERENCIA:
                        # Transferência: origem está em conta_bancaria, destino em subcategoria
                        if hasattr(lanc, 'conta_bancaria') and lanc.conta_bancaria == c.nome:
                            # Esta é a conta de origem - subtrai
                            saldo_real -= valor_decimal
                        if hasattr(lanc, 'subcategoria') and lanc.subcategoria == c.nome:
                            # Esta é a conta de destino - adiciona
                            saldo_real += valor_decimal
                    elif hasattr(lanc, 'conta_bancaria') and lanc.conta_bancaria == c.nome:
                        # Receitas e despesas normais
                        if lanc.tipo == TipoLancamento.RECEITA:
                            saldo_real += valor_decimal
                        elif lanc.tipo == TipoLancamento.DESPESA:
                            saldo_real -= valor_decimal
            
            contas_com_saldo.append({
                'nome': c.nome,
                'banco': c.banco,
                'agencia': c.agencia,
                'conta': c.conta,
                'saldo_inicial': float(c.saldo_inicial),
                'saldo': float(saldo_real)  # Saldo real com movimentações
            })
        
        return jsonify(contas_com_saldo)
    except Exception as e:
        print(f"❌ Erro em /api/contas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/contas', methods=['POST'])
def adicionar_conta():
    """Adiciona uma nova conta bancária"""
    try:
        data = request.json
        
        # Verificar contas existentes antes de adicionar
        contas_existentes = db.listar_contas()
        
        # Verificar se já existe
        for c in contas_existentes:
            if c.nome == data['nome']:
                print(f"CONFLITO: Conta '{data['nome']}' já existe!")
                return jsonify({'success': False, 'error': f'Já existe uma conta cadastrada com: Banco: {data["banco"]}, Agência: {data["agencia"]}, Conta: {data["conta"]}'}), 400
        
        conta = ContaBancaria(
            nome=data['nome'],  # type: ignore
            banco=data['banco'],  # type: ignore
            agencia=data['agencia'],  # type: ignore
            conta=data['conta'],  # type: ignore
            saldo_inicial=float(data.get('saldo_inicial', 0) if data else 0)  # type: ignore
        )
        
        conta_id = db.adicionar_conta(conta)
        return jsonify({'success': True, 'id': conta_id})
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        if 'UNIQUE constraint' in error_msg:
            error_msg = 'Já existe uma conta com este nome'
        return jsonify({'success': False, 'error': error_msg}), 400


@app.route('/api/contas/<path:nome>', methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])  # type: ignore
def modificar_conta(nome):
    """Busca, atualiza ou remove uma conta bancária"""
    
    # Responder ao preflight OPTIONS
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200
    
    if request.method == 'GET':
        try:
            contas = db.listar_contas()
            for conta in contas:
                if conta.nome == nome:
                    return jsonify({
                        'nome': conta.nome,
                        'banco': conta.banco,
                        'agencia': conta.agencia,
                        'conta': conta.conta,
                        'saldo_inicial': float(conta.saldo_inicial)
                    })
            return jsonify({'success': False, 'error': 'Conta não encontrada'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    elif request.method == 'PUT':
        try:
            data = request.json
            
            conta = ContaBancaria(
                nome=data['nome'],  # type: ignore
                banco=data['banco'],  # type: ignore
                agencia=data['agencia'],  # type: ignore
                conta=data['conta'],  # type: ignore
                saldo_inicial=float(data.get('saldo_inicial', 0) if data else 0)  # type: ignore
            )
            success = db.atualizar_conta(nome, conta)
            return jsonify({'success': success})
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            if 'UNIQUE constraint' in error_msg:
                error_msg = 'Já existe uma conta com este nome'
            return jsonify({'success': False, 'error': error_msg}), 400
    
    elif request.method == 'DELETE':
        try:
            success = db.excluir_conta(nome)
            return jsonify({'success': success})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/transferencias', methods=['POST'])
def criar_transferencia():
    """Cria uma transferência entre contas bancárias"""
    try:
        data = request.json
        
        # Validar dados
        if not data or not data.get('conta_origem') or not data.get('conta_destino'):
            return jsonify({'success': False, 'error': 'Contas de origem e destino são obrigatórias'}), 400
        
        if data['conta_origem'] == data['conta_destino']:
            return jsonify({'success': False, 'error': 'Conta de origem e destino não podem ser iguais'}), 400
        
        valor = float(data.get('valor', 0))
        if valor <= 0:
            return jsonify({'success': False, 'error': 'Valor deve ser maior que zero'}), 400
        
        # Buscar contas
        conta_origem = db.buscar_conta(data['conta_origem'])
        conta_destino = db.buscar_conta(data['conta_destino'])
        
        if not conta_origem:
            return jsonify({'success': False, 'error': 'Conta de origem não encontrada'}), 404
        if not conta_destino:
            return jsonify({'success': False, 'error': 'Conta de destino não encontrada'}), 404
        
        # Criar data da transferência
        data_transferencia = datetime.fromisoformat(data['data']) if data.get('data') else datetime.now()
        
        # Criar lançamento de transferência
        lancamento = Lancamento(
            descricao=f"Transferência: {conta_origem.nome} → {conta_destino.nome}",
            valor=valor,
            tipo=TipoLancamento.TRANSFERENCIA,
            categoria="Transferência Interna",
            data_vencimento=data_transferencia,
            data_pagamento=data_transferencia,
            conta_bancaria=data['conta_origem'],
            pessoa="",
            observacoes=f"Destino: {conta_destino.nome}. {data.get('observacoes', '')}",
            num_documento="",
            subcategoria=data['conta_destino']  # Usar subcategoria para armazenar conta destino
        )
        
        lancamento.status = StatusLancamento.PAGO
        lancamento_id = db.adicionar_lancamento(lancamento)
        
        return jsonify({'success': True, 'id': lancamento_id})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# === ROTAS DE CATEGORIAS ===

@app.route('/api/categorias', methods=['GET'])
def listar_categorias():
    """Lista todas as categorias"""
    categorias = db.listar_categorias()
    return jsonify([{
        'nome': c.nome,
        'tipo': c.tipo.value,
        'subcategorias': c.subcategorias
    } for c in categorias])


@app.route('/api/categorias', methods=['POST'])
def adicionar_categoria():
    """Adiciona uma nova categoria"""
    try:
        data = request.json
        
        # Converter tipo para minúscula para compatibilidade com o enum
        tipo_str = data['tipo'].lower() if data and data.get('tipo') else 'receita'  # type: ignore
        
        # Normalizar nome: uppercase e trim
        nome_normalizado = data['nome'].strip().upper() if data and data.get('nome') else ''  # type: ignore
        
        categoria = Categoria(
            nome=nome_normalizado,  # type: ignore
            tipo=TipoLancamento(tipo_str),  # type: ignore
            subcategorias=data.get('subcategorias', []) if data else []  # type: ignore
        )
        categoria_id = db.adicionar_categoria(categoria)
        return jsonify({'success': True, 'id': categoria_id})
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        if 'UNIQUE constraint' in error_msg:
            error_msg = 'Já existe uma categoria com este nome'
        return jsonify({'success': False, 'error': error_msg}), 400


@app.route('/api/categorias/<path:nome>', methods=['PUT', 'DELETE'])  # type: ignore
def modificar_categoria(nome):
    """Atualiza ou remove uma categoria"""
    if request.method == 'PUT':
        try:
            data = request.json
            
            # Converter tipo para minúscula para compatibilidade com o enum
            tipo_str = data['tipo'].lower() if data and data.get('tipo') else 'receita'  # type: ignore
            
            # Normalizar nome: uppercase e trim
            nome_normalizado = data['nome'].strip().upper() if data and data.get('nome') else ''  # type: ignore
            
            # Se o nome mudou, precisamos atualizar com atualizar_nome_categoria primeiro
            nome_original_normalizado = nome.strip().upper()
            
            # Se o nome mudou, atualizar o nome primeiro
            if nome_normalizado != nome_original_normalizado:
                db.atualizar_nome_categoria(nome_original_normalizado, nome_normalizado)
            
            categoria = Categoria(
                nome=nome_normalizado,  # type: ignore
                tipo=TipoLancamento(tipo_str),  # type: ignore
                subcategorias=data.get('subcategorias', []) if data else []  # type: ignore
            )
            success = db.atualizar_categoria(categoria)
            return jsonify({'success': success})
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            if 'UNIQUE constraint' in error_msg:
                error_msg = 'Já existe uma categoria com este nome'
            return jsonify({'success': False, 'error': error_msg}), 400
    
    elif request.method == 'DELETE':
        try:
            success = db.excluir_categoria(nome)
            return jsonify({'success': success})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400


# === ROTAS DE CLIENTES ===

@app.route('/api/clientes', methods=['GET'])
def listar_clientes():
    """Lista clientes ativos ou inativos"""
    ativos = request.args.get('ativos', 'true').lower() == 'true'
    clientes = db.listar_clientes(ativos=ativos)
    return jsonify(clientes)


@app.route('/api/clientes', methods=['POST'])
def adicionar_cliente():
    """Adiciona um novo cliente"""
    try:
        data = request.json
        
        cliente_id = db.adicionar_cliente(data)  # type: ignore
        return jsonify({'success': True, 'id': cliente_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/clientes/<path:nome>', methods=['PUT', 'DELETE'])  # type: ignore
def modificar_cliente(nome):
    """Atualiza ou remove um cliente"""
    if request.method == 'PUT':
        try:
            data = request.json
            print(f"\n=== Atualizando cliente ===")
            print(f"URL recebida: {request.url}")
            print(f"Nome da URL (raw): '{nome}'")
            print(f"Nome da URL (tipo): {type(nome)}")
            print(f"Dados recebidos: {data}")
            if data:
                print(f"Novo nome nos dados: '{data.get('nome')}'")
                print(f"Nova razão social nos dados: '{data.get('razao_social')}'")
            
            success = atualizar_cliente(nome, data)
            print(f"Cliente atualizado: {success}")
            return jsonify({'success': success})
        except Exception as e:
            print(f"ERRO ao atualizar cliente: {str(e)}")
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            if 'UNIQUE constraint' in error_msg:
                error_msg = 'Já existe um cliente com este nome'
            return jsonify({'success': False, 'error': error_msg}), 400
    
    elif request.method == 'DELETE':
        try:
            success, mensagem = db.excluir_cliente(nome)
            if success:
                return jsonify({'success': True, 'message': mensagem})
            else:
                return jsonify({'success': False, 'error': mensagem}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400


# === ROTAS DE FORNECEDORES ===

@app.route('/api/fornecedores', methods=['GET'])
def listar_fornecedores():
    """Lista fornecedores ativos ou inativos"""
    ativos = request.args.get('ativos', 'true').lower() == 'true'
    fornecedores = db.listar_fornecedores(ativos=ativos)
    return jsonify(fornecedores)


@app.route('/api/fornecedores', methods=['POST'])
def adicionar_fornecedor():
    """Adiciona um novo fornecedor"""
    try:
        data = request.json
        
        fornecedor_id = db.adicionar_fornecedor(data)  # type: ignore
        return jsonify({'success': True, 'id': fornecedor_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fornecedores/<path:nome>', methods=['PUT', 'DELETE'])  # type: ignore
def modificar_fornecedor(nome):
    """Atualiza ou remove um fornecedor"""
    if request.method == 'PUT':
        try:
            data = request.json
            
            success = atualizar_fornecedor(nome, data)
            return jsonify({'success': success})
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            if 'UNIQUE constraint' in error_msg:
                error_msg = 'Já existe um fornecedor com este nome'
            return jsonify({'success': False, 'error': error_msg}), 400
    
    elif request.method == 'DELETE':
        try:
            success, mensagem = db.excluir_fornecedor(nome)
            if success:
                return jsonify({'success': True, 'message': mensagem})
            else:
                return jsonify({'success': False, 'error': mensagem}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/clientes/<path:nome>/inativar', methods=['POST'])
def inativar_cliente(nome):
    """Inativa um cliente com motivo"""
    try:
        data = request.json
        motivo = data.get('motivo', '')
        
        if not motivo.strip():
            return jsonify({'success': False, 'error': 'Motivo é obrigatório'}), 400
        
        success, mensagem = db.inativar_cliente(nome, motivo)
        return jsonify({'success': success, 'message': mensagem})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/clientes/<path:nome>/reativar', methods=['POST'])
def reativar_cliente(nome):
    """Reativa um cliente"""
    try:
        success = db.reativar_cliente(nome)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fornecedores/<path:nome>/inativar', methods=['POST'])
def inativar_fornecedor(nome):
    """Inativa um fornecedor com motivo"""
    try:
        data = request.json
        motivo = data.get('motivo', '')
        
        if not motivo.strip():
            return jsonify({'success': False, 'error': 'Motivo é obrigatório'}), 400
        
        success, mensagem = db.inativar_fornecedor(nome, motivo)
        return jsonify({'success': success, 'message': mensagem})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fornecedores/<path:nome>/reativar', methods=['POST'])
def reativar_fornecedor(nome):
    """Reativa um fornecedor"""
    try:
        success = db.reativar_fornecedor(nome)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# === ROTAS DE LANÇAMENTOS ===

@app.route('/api/lancamentos', methods=['GET'])
def listar_lancamentos():
    """Lista todos os lançamentos"""
    tipo_filtro = request.args.get('tipo')
    lancamentos = db.listar_lancamentos()
    
    # Filtrar por tipo se especificado (case-insensitive)
    if tipo_filtro:
        lancamentos = [l for l in lancamentos if l.tipo.value.upper() == tipo_filtro.upper()]
    
    return jsonify([{
        'id': l.id if hasattr(l, 'id') else None,
        'tipo': l.tipo.value,
        'descricao': l.descricao,
        'valor': float(l.valor),
        'data_vencimento': l.data_vencimento.isoformat() if l.data_vencimento else None,
        'data_pagamento': l.data_pagamento.isoformat() if l.data_pagamento else None,
        'status': l.status.value,
        'categoria': l.categoria,
        'subcategoria': l.subcategoria,
        'conta_bancaria': l.conta_bancaria,
        'pessoa': l.pessoa,
        'observacoes': l.observacoes,
        'num_documento': getattr(l, 'num_documento', ''),
        'recorrente': getattr(l, 'recorrente', False),
        'frequencia_recorrencia': getattr(l, 'frequencia_recorrencia', '')
    } for l in lancamentos])


@app.route('/api/lancamentos', methods=['POST'])
def adicionar_lancamento():
    """Adiciona um novo lançamento (com suporte a parcelamento)"""
    try:
        data = request.json
        
        parcelas = int(data.get('parcelas', 1)) if data else 1
        
        if parcelas > 1:
            # Criar múltiplos lançamentos para parcelas
            from dateutil.relativedelta import relativedelta
            data_base = datetime.fromisoformat(data['data_vencimento']) if data and data.get('data_vencimento') else datetime.now()
            valor_parcela = float(data['valor']) / parcelas if data else 0.0
            tipo_str = data['tipo'].lower() if data and data.get('tipo') else 'receita'
            
            lancamentos_ids = []
            for i in range(parcelas):
                data_venc = data_base + relativedelta(months=i)
                descricao_parcela = f"{data['descricao']} ({i+1}/{parcelas})" if data else f"Parcela {i+1}/{parcelas}"
                
                lancamento = Lancamento(
                    descricao=descricao_parcela,
                    valor=valor_parcela,
                    tipo=TipoLancamento(tipo_str),
                    categoria=data.get('categoria', '') if data else '',
                    data_vencimento=data_venc,
                    data_pagamento=None,
                    conta_bancaria=data['conta_bancaria'] if data else '',
                    pessoa=data.get('pessoa', '') if data else '',
                    observacoes=data.get('observacoes', '') if data else '',
                    num_documento=data.get('num_documento', '') if data else '',
                    subcategoria=data.get('subcategoria', '') if data else ''
                )
                
                if data and data.get('status'):
                    lancamento.status = StatusLancamento(data['status'])
                
                lancamento_id = db.adicionar_lancamento(lancamento)
                lancamentos_ids.append(lancamento_id)
            
            print(f"Lançamentos parcelados adicionados! IDs: {lancamentos_ids}")
            return jsonify({'success': True, 'ids': lancamentos_ids})
        else:
            # Lançamento único (sem parcelamento)
            data_venc = datetime.fromisoformat(data['data_vencimento']) if data and data.get('data_vencimento') else datetime.now()
            data_pag = datetime.fromisoformat(data['data_pagamento']) if data and data.get('data_pagamento') else None
            tipo_str = data['tipo'].lower() if data and data.get('tipo') else 'receita'
            
            lancamento = Lancamento(
                descricao=data['descricao'] if data else '',
                valor=float(data['valor']) if data else 0.0,
                tipo=TipoLancamento(tipo_str),
                categoria=data.get('categoria', '') if data else '',
                data_vencimento=data_venc,
                data_pagamento=data_pag,
                conta_bancaria=data['conta_bancaria'] if data else '',
                pessoa=data.get('pessoa', '') if data else '',
                observacoes=data.get('observacoes', '') if data else '',
                num_documento=data.get('num_documento', '') if data else '',
                subcategoria=data.get('subcategoria', '') if data else ''
            )
            
            if data and data.get('status'):
                lancamento.status = StatusLancamento(data['status'])
            
            lancamento_id = db.adicionar_lancamento(lancamento)
            return jsonify({'success': True, 'id': lancamento_id})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/lancamentos/<int:lancamento_id>', methods=['GET'])
def obter_lancamento_route(lancamento_id):
    """Retorna os dados de um lançamento específico"""
    try:
        lancamento = db_obter_lancamento(lancamento_id)
        if lancamento:
            return jsonify(lancamento), 200
        else:
            return jsonify({'error': 'Lançamento não encontrado'}), 404
    except Exception as e:
        print(f"ERRO ao obter lançamento: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/lancamentos/<int:lancamento_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
def gerenciar_lancamento(lancamento_id):
    """Atualiza ou remove um lançamento"""
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200
    
    if request.method == 'PUT':
        conn = None
        try:
            data = request.get_json()
            
            # Atualizar lançamento
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            # Verificar se lançamento existe
            cursor.execute('SELECT id FROM lancamentos WHERE id = ?', (lancamento_id,))
            if not cursor.fetchone():
                print("ERRO: Lançamento não encontrado")
                return jsonify({'success': False, 'error': 'Lançamento não encontrado'}), 404
            
            # Buscar status e data_pagamento atual para preservar se já foi pago
            cursor.execute('SELECT status, data_pagamento, conta_bancaria FROM lancamentos WHERE id = ?', (lancamento_id,))
            row = cursor.fetchone()
            status_atual = row[0] if row else 'PENDENTE'
            data_pgto_atual = row[1] if row else None
            conta_bancaria_atual = row[2] if row else None
            
            cursor.execute('''
                UPDATE lancamentos 
                SET tipo = ?,
                    pessoa = ?,
                    categoria = ?,
                    subcategoria = ?,
                    num_documento = ?,
                    data_vencimento = ?,
                    descricao = ?,
                    valor = ?,
                    observacoes = ?,
                    status = ?,
                    data_pagamento = ?,
                    conta_bancaria = ?
                WHERE id = ?
            ''', (
                data['tipo'],
                data.get('pessoa', ''),
                data.get('categoria', ''),
                data.get('subcategoria', ''),
                data.get('num_documento', ''),
                data['data_vencimento'],
                data.get('descricao', ''),
                data['valor'],
                data.get('observacoes', ''),
                status_atual,  # Preserva status atual
                data_pgto_atual,  # Preserva data de pagamento
                conta_bancaria_atual,  # Preserva conta bancária
                lancamento_id
            ))
            
            conn.commit()
            print(f"Lançamento atualizado com sucesso! Linhas afetadas: {cursor.rowcount}")
            return jsonify({'success': True, 'id': lancamento_id})
            
        except Exception as e:
            print(f"ERRO ao atualizar lançamento: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 400
        finally:
            if conn:
                conn.close()
    
    # DELETE
    try:
        print(f"\n=== Excluindo lançamento ID: {lancamento_id} ===")
        success = db.excluir_lancamento(lancamento_id)
        print(f"Resultado da exclusão: {success}")
        
        if not success:
            print("AVISO: Nenhum registro foi excluído (ID não encontrado?)")
            return jsonify({'success': False, 'error': 'Lançamento não encontrado'}), 404
        
        print("Lançamento excluído com sucesso!")
        return jsonify({'success': True})
    except Exception as e:
        print(f"ERRO ao excluir lançamento: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


# === ROTAS DE RELATÓRIOS ===

@app.route('/api/relatorios/fluxo-caixa', methods=['GET'])
def relatorio_fluxo_caixa():
    """Relatório de fluxo de caixa"""
    data_inicio_str = request.args.get('data_inicio', (date.today() - timedelta(days=30)).isoformat())
    data_fim_str = request.args.get('data_fim', date.today().isoformat())
    
    # Converter strings para date objects
    if isinstance(data_inicio_str, str):
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
    else:
        data_inicio = data_inicio_str
        
    if isinstance(data_fim_str, str):
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    else:
        data_fim = data_fim_str
    
    lancamentos = db.listar_lancamentos()
    lancamentos_periodo = []
    for l in lancamentos:
        if l.status == StatusLancamento.PAGO and l.data_pagamento:
            # Converter data_pagamento para date se for datetime
            if isinstance(l.data_pagamento, datetime):
                data_pgto = l.data_pagamento.date()
            else:
                data_pgto = l.data_pagamento
            
            # Comparar apenas se ambos forem date
            try:
                if data_inicio <= data_pgto <= data_fim:
                    lancamentos_periodo.append(l)
            except TypeError as e:
                print(f"ERRO: tipo data_inicio={type(data_inicio)}, data_pgto={type(data_pgto)}, data_fim={type(data_fim)}")
                print(f"Valores: {data_inicio} <= {data_pgto} <= {data_fim}")
                raise
    
    resultado = []
    for l in lancamentos_periodo:
        data_pgto = l.data_pagamento
        if hasattr(data_pgto, 'date'):
            data_pgto = data_pgto.date()
        
        # Para transferências, criar dois registros: débito na origem e crédito no destino
        if l.tipo == TipoLancamento.TRANSFERENCIA:
            # Débito na conta origem (aparece como DESPESA)
            resultado.append({
                'tipo': 'despesa',
                'descricao': f"{l.descricao} (Saída)",
                'valor': float(l.valor),
                'data_pagamento': data_pgto.isoformat() if data_pgto else None,
                'categoria': l.categoria,
                'subcategoria': l.subcategoria,
                'pessoa': l.pessoa,
                'conta_bancaria': l.conta_bancaria if hasattr(l, 'conta_bancaria') else None
            })
            # Crédito na conta destino (aparece como RECEITA)
            resultado.append({
                'tipo': 'receita',
                'descricao': f"{l.descricao} (Entrada)",
                'valor': float(l.valor),
                'data_pagamento': data_pgto.isoformat() if data_pgto else None,
                'categoria': l.categoria,
                'subcategoria': l.conta_bancaria,  # Inverter: origem vai para subcategoria
                'pessoa': l.pessoa,
                'conta_bancaria': l.subcategoria  # Destino vira a conta bancária
            })
        else:
            # Receitas e despesas normais
            resultado.append({
                'tipo': l.tipo.value,
                'descricao': l.descricao,
                'valor': float(l.valor),
                'data_pagamento': data_pgto.isoformat() if data_pgto else None,
                'categoria': l.categoria,
                'subcategoria': l.subcategoria,
                'pessoa': l.pessoa,
                'conta_bancaria': l.conta_bancaria if hasattr(l, 'conta_bancaria') else None
            })
    return jsonify(resultado)


@app.route('/api/relatorios/dashboard', methods=['GET'])
def dashboard():
    """Dados para o dashboard"""
    try:
        lancamentos = db.listar_lancamentos()
        contas = db.listar_contas()
        
        # Calcular saldos
        saldo_total = Decimal('0')
        for c in contas:
            saldo_total += Decimal(str(c.saldo_inicial))
        
        for lanc in lancamentos:
            if lanc.status == StatusLancamento.PAGO and lanc.tipo != TipoLancamento.TRANSFERENCIA:
                valor_decimal = Decimal(str(lanc.valor))
                if lanc.tipo == TipoLancamento.RECEITA:
                    saldo_total += valor_decimal
                else:
                    saldo_total -= valor_decimal
        
        # Contas pendentes
        hoje = date.today()
        contas_receber = Decimal('0')
        contas_pagar = Decimal('0')
        contas_vencidas = Decimal('0')
        
        for l in lancamentos:
            if l.tipo != TipoLancamento.TRANSFERENCIA:
                valor_decimal = Decimal(str(l.valor))
                if l.tipo == TipoLancamento.RECEITA and l.status == StatusLancamento.PENDENTE:
                    contas_receber += valor_decimal
                if l.tipo == TipoLancamento.DESPESA and l.status == StatusLancamento.PENDENTE:
                    contas_pagar += valor_decimal
                # Converter datetime para date se necessário
                data_venc = l.data_vencimento.date() if hasattr(l.data_vencimento, 'date') else l.data_vencimento
                if l.status == StatusLancamento.PENDENTE and data_venc < hoje:
                    contas_vencidas += valor_decimal
        
        return jsonify({
            'saldo_total': float(saldo_total),
            'contas_receber': float(contas_receber),
            'contas_pagar': float(contas_pagar),
            'contas_vencidas': float(contas_vencidas),
            'total_contas': len(contas),
            'total_lancamentos': len(lancamentos)
        })
    except Exception as e:
        print(f"Erro no dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/relatorios/dashboard-completo', methods=['GET'])
def dashboard_completo():
    """Dashboard completo com análises detalhadas - apenas lançamentos liquidados"""
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        if not data_inicio or not data_fim:
            return jsonify({'error': 'Datas obrigatórias'}), 400
        
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
        
        lancamentos = db.listar_lancamentos()
        
        # Filtrar apenas lançamentos PAGOS/LIQUIDADOS no período (baseado na data de pagamento)
        # Excluir transferências dos relatórios
        lancamentos_periodo = []
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_inicio_obj <= data_pag <= data_fim_obj:
                    lancamentos_periodo.append(l)
        
        # Evolução mensal (baseado na data de pagamento)
        evolucao = []
        current_date = data_inicio_obj
        
        while current_date <= data_fim_obj:
            mes_inicio = current_date.replace(day=1)
            if current_date.month == 12:
                mes_fim = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                mes_fim = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
            
            # Filtrar por data de pagamento
            lancamentos_mes = [
                l for l in lancamentos_periodo
                if mes_inicio <= (l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento) <= mes_fim
            ]
            
            receitas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_mes if l.tipo == TipoLancamento.RECEITA)
            despesas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_mes if l.tipo == TipoLancamento.DESPESA)
            saldo_mes = receitas_mes - despesas_mes
            
            evolucao.append({
                'periodo': current_date.strftime('%b/%y'),
                'receitas': float(receitas_mes),
                'despesas': float(despesas_mes),
                'saldo': float(saldo_mes)
            })
            
            # Avançar para o próximo mês
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
        
        # Análise de Clientes
        clientes_resumo = {}
        for l in lancamentos_periodo:
            if l.tipo == TipoLancamento.RECEITA and l.pessoa:
                if l.pessoa not in clientes_resumo:
                    clientes_resumo[l.pessoa] = {'total': Decimal('0'), 'quantidade': 0}
                clientes_resumo[l.pessoa]['total'] += Decimal(str(l.valor))
                clientes_resumo[l.pessoa]['quantidade'] += 1
        
        melhor_cliente = None
        pior_cliente = None
        if clientes_resumo:
            melhor_cliente_nome = max(clientes_resumo, key=lambda x: clientes_resumo[x]['total'])
            pior_cliente_nome = min(clientes_resumo, key=lambda x: clientes_resumo[x]['total'])
            
            melhor_cliente = {
                'nome': melhor_cliente_nome,
                'total': float(clientes_resumo[melhor_cliente_nome]['total']),
                'quantidade': clientes_resumo[melhor_cliente_nome]['quantidade']
            }
            pior_cliente = {
                'nome': pior_cliente_nome,
                'total': float(clientes_resumo[pior_cliente_nome]['total']),
                'quantidade': clientes_resumo[pior_cliente_nome]['quantidade']
            }
        
        # Análise de Fornecedores
        fornecedores_resumo = {}
        for l in lancamentos_periodo:
            if l.tipo == TipoLancamento.DESPESA and l.pessoa:
                if l.pessoa not in fornecedores_resumo:
                    fornecedores_resumo[l.pessoa] = {'total': Decimal('0'), 'quantidade': 0}
                fornecedores_resumo[l.pessoa]['total'] += Decimal(str(l.valor))
                fornecedores_resumo[l.pessoa]['quantidade'] += 1
        
        maior_fornecedor = None
        menor_fornecedor = None
        if fornecedores_resumo:
            maior_fornecedor_nome = max(fornecedores_resumo, key=lambda x: fornecedores_resumo[x]['total'])
            menor_fornecedor_nome = min(fornecedores_resumo, key=lambda x: fornecedores_resumo[x]['total'])
            
            maior_fornecedor = {
                'nome': maior_fornecedor_nome,
                'total': float(fornecedores_resumo[maior_fornecedor_nome]['total']),
                'quantidade': fornecedores_resumo[maior_fornecedor_nome]['quantidade']
            }
            menor_fornecedor = {
                'nome': menor_fornecedor_nome,
                'total': float(fornecedores_resumo[menor_fornecedor_nome]['total']),
                'quantidade': fornecedores_resumo[menor_fornecedor_nome]['quantidade']
            }
        
        # Análise de Categorias - Receitas
        categorias_receita = {}
        for l in lancamentos_periodo:
            if l.tipo == TipoLancamento.RECEITA:
                cat = l.categoria or 'Sem categoria'
                subcat = l.subcategoria or 'Sem subcategoria'
                
                if cat not in categorias_receita:
                    categorias_receita[cat] = {}
                if subcat not in categorias_receita[cat]:
                    categorias_receita[cat][subcat] = Decimal('0')
                
                categorias_receita[cat][subcat] += Decimal(str(l.valor))
        
        melhor_categoria_receita = None
        if categorias_receita:
            melhor_cat = max(categorias_receita, key=lambda x: sum(categorias_receita[x].values()))
            melhor_subcat = max(categorias_receita[melhor_cat], key=lambda x: categorias_receita[melhor_cat][x])
            
            melhor_categoria_receita = {
                'categoria': melhor_cat,
                'subcategoria': melhor_subcat if melhor_subcat != 'Sem subcategoria' else None,
                'total': float(categorias_receita[melhor_cat][melhor_subcat])
            }
        
        # Análise de Categorias - Despesas
        categorias_despesa = {}
        for l in lancamentos_periodo:
            if l.tipo == TipoLancamento.DESPESA:
                cat = l.categoria or 'Sem categoria'
                subcat = l.subcategoria or 'Sem subcategoria'
                
                if cat not in categorias_despesa:
                    categorias_despesa[cat] = {}
                if subcat not in categorias_despesa[cat]:
                    categorias_despesa[cat][subcat] = Decimal('0')
                
                categorias_despesa[cat][subcat] += Decimal(str(l.valor))
        
        maior_categoria_despesa = None
        if categorias_despesa:
            maior_cat = max(categorias_despesa, key=lambda x: sum(categorias_despesa[x].values()))
            maior_subcat = max(categorias_despesa[maior_cat], key=lambda x: categorias_despesa[maior_cat][x])
            
            maior_categoria_despesa = {
                'categoria': maior_cat,
                'subcategoria': maior_subcat if maior_subcat != 'Sem subcategoria' else None,
                'total': float(categorias_despesa[maior_cat][maior_subcat])
            }
        
        return jsonify({
            'evolucao': evolucao,
            'melhor_cliente': melhor_cliente,
            'pior_cliente': pior_cliente,
            'maior_fornecedor': maior_fornecedor,
            'menor_fornecedor': menor_fornecedor,
            'melhor_categoria_receita': melhor_categoria_receita,
            'maior_categoria_despesa': maior_categoria_despesa
        })
        
    except Exception as e:
        print(f"Erro no dashboard completo: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/relatorios/fluxo-projetado', methods=['GET'])
def relatorio_fluxo_projetado():
    """Relatório de fluxo de caixa PROJETADO (incluindo lançamentos pendentes futuros)"""
    try:
        # Receber filtros - padrão é projetar próximos X dias
        dias = request.args.get('dias')
        dias = int(dias) if dias else 30
        
        hoje = date.today()
        data_inicial = hoje
        data_final = hoje + timedelta(days=dias)
        periodo_texto = f"PROJEÇÃO - PRÓXIMOS {dias} DIAS"
        
        lancamentos = db.listar_lancamentos()
        contas = db.listar_contas()
        
        # Saldo atual (saldo inicial + todos os lançamentos pagos até hoje)
        saldo_atual = Decimal('0')
        for c in contas:
            saldo_atual += Decimal(str(c.saldo_inicial))
        
        # Adicionar todas as receitas e despesas JÁ PAGAS até hoje (exceto transferências)
        for l in lancamentos:
            # Converter data_pagamento para date se for datetime
            if l.data_pagamento:
                if isinstance(l.data_pagamento, datetime):
                    data_pgto = l.data_pagamento.date()
                else:
                    data_pgto = l.data_pagamento
            else:
                data_pgto = None
            
            if l.status == StatusLancamento.PAGO and data_pgto and data_pgto <= hoje and l.tipo != TipoLancamento.TRANSFERENCIA:
                valor_decimal = Decimal(str(l.valor))
                if l.tipo == TipoLancamento.RECEITA:
                    saldo_atual += valor_decimal
                else:
                    saldo_atual -= valor_decimal
        
        # Buscar lançamentos PENDENTES para projeção (vencidos + futuros)
        lancamentos_futuros = []
        lancamentos_vencidos = []
        receitas_previstas = Decimal('0')
        despesas_previstas = Decimal('0')
        receitas_vencidas = Decimal('0')
        despesas_vencidas = Decimal('0')
        
        for l in lancamentos:
            if l.status == StatusLancamento.PENDENTE and l.tipo != TipoLancamento.TRANSFERENCIA:
                # Converter data_vencimento para date se for datetime
                if isinstance(l.data_vencimento, datetime):
                    data_venc = l.data_vencimento.date()
                else:
                    data_venc = l.data_vencimento
                
                valor_decimal = Decimal(str(l.valor))
                
                # Lançamentos vencidos (já passaram do vencimento)
                if data_venc < hoje:
                    lancamentos_vencidos.append(l)
                    if l.tipo == TipoLancamento.RECEITA:
                        receitas_vencidas += valor_decimal
                    else:
                        despesas_vencidas += valor_decimal
                
                # Lançamentos futuros (dentro do período de projeção)
                elif data_inicial <= data_venc <= data_final:
                    lancamentos_futuros.append(l)
                    if l.tipo == TipoLancamento.RECEITA:
                        receitas_previstas += valor_decimal
                    else:
                        despesas_previstas += valor_decimal
        
        # Calcular saldo projetado (incluindo vencidos)
        saldo_projetado = saldo_atual + (receitas_previstas + receitas_vencidas) - (despesas_previstas + despesas_vencidas)
        
        # Ordenar por data de vencimento
        lancamentos_vencidos.sort(key=lambda x: x.data_vencimento)
        lancamentos_futuros.sort(key=lambda x: x.data_vencimento)
        
        # Montar fluxo projetado dia a dia (VENCIDOS PRIMEIRO, depois futuros)
        fluxo = []
        saldo_acumulado = saldo_atual
        
        # Adicionar vencidos primeiro
        for lanc in lancamentos_vencidos:
            valor_decimal = Decimal(str(lanc.valor))
            if lanc.tipo == TipoLancamento.RECEITA:
                saldo_acumulado += valor_decimal
            else:
                saldo_acumulado -= valor_decimal
            
            # Calcular dias de atraso
            data_venc_date = lanc.data_vencimento.date() if isinstance(lanc.data_vencimento, datetime) else lanc.data_vencimento
            dias_atraso = (hoje - data_venc_date).days
            
            fluxo.append({
                'data_vencimento': lanc.data_vencimento.isoformat(),
                'descricao': lanc.descricao,
                'tipo': lanc.tipo.value,
                'valor': float(lanc.valor),
                'categoria': lanc.categoria,
                'subcategoria': lanc.subcategoria,
                'pessoa': lanc.pessoa,
                'conta_bancaria': lanc.conta_bancaria,
                'saldo_acumulado': float(saldo_acumulado),
                'status': 'VENCIDO',
                'dias_atraso': dias_atraso
            })
        
        # Adicionar lançamentos futuros
        for lanc in lancamentos_futuros:
            valor_decimal = Decimal(str(lanc.valor))
            if lanc.tipo == TipoLancamento.RECEITA:
                saldo_acumulado += valor_decimal
            else:
                saldo_acumulado -= valor_decimal
            
            fluxo.append({
                'data_vencimento': lanc.data_vencimento.isoformat(),
                'descricao': lanc.descricao,
                'tipo': lanc.tipo.value,
                'valor': float(lanc.valor),
                'categoria': lanc.categoria,
                'subcategoria': lanc.subcategoria,
                'pessoa': lanc.pessoa,
                'conta_bancaria': lanc.conta_bancaria,
                'saldo_acumulado': float(saldo_acumulado),
                'status': 'PENDENTE',
                'dias_atraso': 0
            })
        
        return jsonify({
            'periodo_texto': periodo_texto,
            'data_inicial': data_inicial.isoformat(),
            'data_final': data_final.isoformat(),
            'saldo_atual': float(saldo_atual),
            'receitas_previstas': float(receitas_previstas),
            'despesas_previstas': float(despesas_previstas),
            'receitas_vencidas': float(receitas_vencidas),
            'despesas_vencidas': float(despesas_vencidas),
            'saldo_projetado': float(saldo_projetado),
            'total_vencidos': len(lancamentos_vencidos),
            'total_futuros': len(lancamentos_futuros),
            'fluxo': fluxo
        })
    except Exception as e:
        print(f"Erro no fluxo projetado: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/relatorios/analise-contas', methods=['GET'])
def relatorio_analise_contas():
    """Relatório de análise de contas a pagar e receber"""
    lancamentos = db.listar_lancamentos()
    hoje = date.today()
    
    # Função auxiliar para converter datetime para date
    def get_date(data):
        return data.date() if hasattr(data, 'date') else data
    
    # Totais (excluindo transferências)
    total_receber = sum(l.valor for l in lancamentos 
                       if l.tipo == TipoLancamento.RECEITA and l.status == StatusLancamento.PENDENTE)
    total_pagar = sum(l.valor for l in lancamentos 
                     if l.tipo == TipoLancamento.DESPESA and l.status == StatusLancamento.PENDENTE)
    
    receber_vencidos = sum(l.valor for l in lancamentos 
                          if l.tipo == TipoLancamento.RECEITA and 
                          l.status == StatusLancamento.PENDENTE and 
                          get_date(l.data_vencimento) < hoje)
    pagar_vencidos = sum(l.valor for l in lancamentos 
                        if l.tipo == TipoLancamento.DESPESA and 
                        l.status == StatusLancamento.PENDENTE and 
                        get_date(l.data_vencimento) < hoje)
    
    # Aging (análise de vencimento) - excluindo transferências
    pendentes = [l for l in lancamentos if l.status == StatusLancamento.PENDENTE and l.tipo != TipoLancamento.TRANSFERENCIA]
    
    vencidos = sum(l.valor for l in pendentes if (get_date(l.data_vencimento) - hoje).days < 0)  # type: ignore
    ate_7 = sum(l.valor for l in pendentes if 0 <= (get_date(l.data_vencimento) - hoje).days <= 7)  # type: ignore
    ate_15 = sum(l.valor for l in pendentes if 7 < (get_date(l.data_vencimento) - hoje).days <= 15)  # type: ignore
    ate_30 = sum(l.valor for l in pendentes if 15 < (get_date(l.data_vencimento) - hoje).days <= 30)  # type: ignore
    ate_60 = sum(l.valor for l in pendentes if 30 < (get_date(l.data_vencimento) - hoje).days <= 60)  # type: ignore
    ate_90 = sum(l.valor for l in pendentes if 60 < (get_date(l.data_vencimento) - hoje).days <= 90)  # type: ignore
    acima_90 = sum(l.valor for l in pendentes if (get_date(l.data_vencimento) - hoje).days > 90)  # type: ignore
    
    return jsonify({
        'total_receber': float(total_receber),
        'total_pagar': float(total_pagar),
        'receber_vencidos': float(receber_vencidos),
        'pagar_vencidos': float(pagar_vencidos),
        'aging': {
            'vencidos': float(vencidos),
            'ate_7': float(ate_7),
            'ate_15': float(ate_15),
            'ate_30': float(ate_30),
            'ate_60': float(ate_60),
            'ate_90': float(ate_90),
            'acima_90': float(acima_90)
        }
    })


@app.route('/api/lancamentos/<int:lancamento_id>/pagar', methods=['PUT'])
def pagar_lancamento(lancamento_id):
    """Marca um lançamento como pago"""
    try:
        data = request.json
        conta = data.get('conta_bancaria', '') if data else ''
        data_pagamento = datetime.fromisoformat(data.get('data_pagamento', datetime.now().isoformat())).date() if data else date.today()
        juros = float(data.get('juros', 0)) if data else 0
        desconto = float(data.get('desconto', 0)) if data else 0
        observacoes = data.get('observacoes', '') if data else ''
        
        success = db_pagar_lancamento(lancamento_id, conta, data_pagamento, juros, desconto, observacoes)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/lancamentos/<int:lancamento_id>/liquidar', methods=['POST'])
def liquidar_lancamento(lancamento_id):
    """Liquida um lançamento (marca como pago com dados completos)"""
    try:
        data = request.json or {}
        
        conta = data.get('conta_bancaria', '')
        data_pagamento_str = data.get('data_pagamento', '')
        juros = float(data.get('juros', 0))
        desconto = float(data.get('desconto', 0))
        observacoes = data.get('observacoes', '')
        
        if not conta:
            return jsonify({'success': False, 'error': 'Conta bancária é obrigatória'}), 400
        
        if not data_pagamento_str or data_pagamento_str.strip() == '':
            return jsonify({'success': False, 'error': 'Data de pagamento é obrigatória'}), 400
        
        data_pagamento = datetime.fromisoformat(data_pagamento_str).date()
        
        success = db_pagar_lancamento(lancamento_id, conta, data_pagamento, juros, desconto, observacoes)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/lancamentos/<int:lancamento_id>/cancelar', methods=['PUT'])
def cancelar_lancamento_route(lancamento_id):
    """Cancela um lançamento"""
    try:
        success = db_cancelar_lancamento(lancamento_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# === ROTA PRINCIPAL ===

@app.route('/')
def index():
    """Página principal - Nova interface moderna"""
    return render_template('interface_nova.html')

@app.route('/old')
def old_index():
    """Página antiga (backup)"""
    return render_template('interface.html')

@app.route('/legacy')
def legacy_index():
    """Página legado"""
    return render_template('index.html')

@app.route('/teste')
def teste():
    """Página de teste JavaScript"""
    return render_template('teste.html')

@app.route('/teste-api')
def teste_api():
    """Página de teste API"""
    return render_template('teste_api.html')

# === ENDPOINTS DE RELATÓRIOS ===

@app.route('/api/relatorios/resumo-parceiros', methods=['GET'])
def relatorio_resumo_parceiros():
    """Relatório de resumo por cliente/fornecedor"""
    try:
        data_inicio = request.args.get('data_inicio', (date.today() - timedelta(days=30)).isoformat())
        data_fim = request.args.get('data_fim', date.today().isoformat())
        
        data_inicio = datetime.fromisoformat(data_inicio).date()
        data_fim = datetime.fromisoformat(data_fim).date()
        
        lancamentos = db.listar_lancamentos()
        
        # Agrupar por pessoa
        resumo_clientes = {}
        resumo_fornecedores = {}
        
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_inicio <= data_pag <= data_fim and l.pessoa:
                    valor = float(l.valor)
                    categoria = l.categoria or 'Sem categoria'
                    
                    if l.tipo == TipoLancamento.RECEITA:
                        if l.pessoa not in resumo_clientes:
                            resumo_clientes[l.pessoa] = {'total': 0, 'quantidade': 0, 'categorias': {}}
                        resumo_clientes[l.pessoa]['total'] += valor
                        resumo_clientes[l.pessoa]['quantidade'] += 1
                        # Contar por categoria
                        if categoria not in resumo_clientes[l.pessoa]['categorias']:
                            resumo_clientes[l.pessoa]['categorias'][categoria] = 0
                        resumo_clientes[l.pessoa]['categorias'][categoria] += valor
                    else:
                        if l.pessoa not in resumo_fornecedores:
                            resumo_fornecedores[l.pessoa] = {'total': 0, 'quantidade': 0, 'categorias': {}}
                        resumo_fornecedores[l.pessoa]['total'] += valor
                        resumo_fornecedores[l.pessoa]['quantidade'] += 1
                        # Contar por categoria
                        if categoria not in resumo_fornecedores[l.pessoa]['categorias']:
                            resumo_fornecedores[l.pessoa]['categorias'][categoria] = 0
                        resumo_fornecedores[l.pessoa]['categorias'][categoria] += valor
        
        # Adicionar categoria principal para cada cliente/fornecedor
        for pessoa, dados in resumo_clientes.items():
            if dados['categorias']:
                categoria_principal = max(dados['categorias'].items(), key=lambda x: x[1])
                dados['categoria_principal'] = categoria_principal[0]
            else:
                dados['categoria_principal'] = 'Sem categoria'
        
        for pessoa, dados in resumo_fornecedores.items():
            if dados['categorias']:
                categoria_principal = max(dados['categorias'].items(), key=lambda x: x[1])
                dados['categoria_principal'] = categoria_principal[0]
            else:
                dados['categoria_principal'] = 'Sem categoria'
        
        return jsonify({
            'clientes': resumo_clientes,
            'fornecedores': resumo_fornecedores,
            'periodo': {
                'inicio': data_inicio.isoformat(),
                'fim': data_fim.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/relatorios/analise-categorias', methods=['GET'])
def relatorio_analise_categorias():
    """Relatório de análise por categorias"""
    try:
        data_inicio = request.args.get('data_inicio', (date.today() - timedelta(days=30)).isoformat())
        data_fim = request.args.get('data_fim', date.today().isoformat())
        
        data_inicio = datetime.fromisoformat(data_inicio).date()
        data_fim = datetime.fromisoformat(data_fim).date()
        
        lancamentos = db.listar_lancamentos()
        
        # Agrupar por categoria e subcategoria
        receitas = {}
        despesas = {}
        
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_inicio <= data_pag <= data_fim:
                    categoria = l.categoria or 'Sem Categoria'
                    subcategoria = l.subcategoria or 'Sem Subcategoria'
                    valor = float(l.valor)
                    
                    if l.tipo == TipoLancamento.RECEITA:
                        if categoria not in receitas:
                            receitas[categoria] = {}
                        if subcategoria not in receitas[categoria]:
                            receitas[categoria][subcategoria] = {'total': 0, 'quantidade': 0}
                        receitas[categoria][subcategoria]['total'] += valor
                        receitas[categoria][subcategoria]['quantidade'] += 1
                    else:
                        if categoria not in despesas:
                            despesas[categoria] = {}
                        if subcategoria not in despesas[categoria]:
                            despesas[categoria][subcategoria] = {'total': 0, 'quantidade': 0}
                        despesas[categoria][subcategoria]['total'] += valor
                        despesas[categoria][subcategoria]['quantidade'] += 1
        
        return jsonify({
            'receitas': receitas,
            'despesas': despesas,
            'periodo': {
                'inicio': data_inicio.isoformat(),
                'fim': data_fim.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/relatorios/comparativo-periodos', methods=['GET'])
def relatorio_comparativo_periodos():
    """Relatório comparativo entre períodos"""
    try:
        # Período 1
        data_inicio1 = request.args.get('data_inicio1')
        data_fim1 = request.args.get('data_fim1')
        
        # Período 2
        data_inicio2 = request.args.get('data_inicio2')
        data_fim2 = request.args.get('data_fim2')
        
        if not all([data_inicio1, data_fim1, data_inicio2, data_fim2]):
            return jsonify({'error': 'Parâmetros de datas obrigatórios'}), 400
        
        data_inicio1 = datetime.fromisoformat(data_inicio1).date()
        data_fim1 = datetime.fromisoformat(data_fim1).date()
        data_inicio2 = datetime.fromisoformat(data_inicio2).date()
        data_fim2 = datetime.fromisoformat(data_fim2).date()
        
        lancamentos = db.listar_lancamentos()
        
        def calcular_periodo(data_ini, data_fim):
            receitas = Decimal('0')
            despesas = Decimal('0')
            receitas_por_categoria = {}
            despesas_por_categoria = {}
            receitas_por_subcategoria = {}
            despesas_por_subcategoria = {}
            
            for l in lancamentos:
                if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                    data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                    if data_ini <= data_pag <= data_fim:
                        valor = Decimal(str(l.valor))
                        categoria = l.categoria or 'Sem categoria'
                        subcategoria = l.subcategoria or 'Sem subcategoria'
                        chave_completa = f"{categoria} > {subcategoria}"
                        
                        if l.tipo == TipoLancamento.RECEITA:
                            receitas += valor
                            receitas_por_categoria[categoria] = receitas_por_categoria.get(categoria, Decimal('0')) + valor
                            receitas_por_subcategoria[chave_completa] = receitas_por_subcategoria.get(chave_completa, Decimal('0')) + valor
                        else:
                            despesas += valor
                            despesas_por_categoria[categoria] = despesas_por_categoria.get(categoria, Decimal('0')) + valor
                            despesas_por_subcategoria[chave_completa] = despesas_por_subcategoria.get(chave_completa, Decimal('0')) + valor
            
            # Encontrar maiores por categoria
            maior_receita_cat = max(receitas_por_categoria.items(), key=lambda x: x[1]) if receitas_por_categoria else ('Nenhuma', Decimal('0'))
            maior_despesa_cat = max(despesas_por_categoria.items(), key=lambda x: x[1]) if despesas_por_categoria else ('Nenhuma', Decimal('0'))
            
            # Encontrar maiores por subcategoria
            maior_receita_sub = max(receitas_por_subcategoria.items(), key=lambda x: x[1]) if receitas_por_subcategoria else ('Nenhuma', Decimal('0'))
            maior_despesa_sub = max(despesas_por_subcategoria.items(), key=lambda x: x[1]) if despesas_por_subcategoria else ('Nenhuma', Decimal('0'))
            
            # Top 3 categorias
            top_receitas = sorted(receitas_por_categoria.items(), key=lambda x: x[1], reverse=True)[:3]
            top_despesas = sorted(despesas_por_categoria.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return {
                'receitas': float(receitas),
                'despesas': float(despesas),
                'saldo': float(receitas - despesas),
                'maior_receita': {'categoria': maior_receita_cat[0], 'valor': float(maior_receita_cat[1])},
                'maior_despesa': {'categoria': maior_despesa_cat[0], 'valor': float(maior_despesa_cat[1])},
                'maior_receita_sub': {'subcategoria': maior_receita_sub[0], 'valor': float(maior_receita_sub[1])},
                'maior_despesa_sub': {'subcategoria': maior_despesa_sub[0], 'valor': float(maior_despesa_sub[1])},
                'top_receitas': [{'categoria': k, 'valor': float(v), 'percentual': float(v/receitas*100) if receitas > 0 else 0} for k, v in top_receitas],
                'top_despesas': [{'categoria': k, 'valor': float(v), 'percentual': float(v/despesas*100) if despesas > 0 else 0} for k, v in top_despesas],
                'qtd_categorias_receitas': len(receitas_por_categoria),
                'qtd_categorias_despesas': len(despesas_por_categoria)
            }
        
        periodo1 = calcular_periodo(data_inicio1, data_fim1)
        periodo2 = calcular_periodo(data_inicio2, data_fim2)
        
        # Calcular variações
        variacao_receitas = ((periodo2['receitas'] - periodo1['receitas']) / periodo1['receitas'] * 100) if periodo1['receitas'] > 0 else 0
        variacao_despesas = ((periodo2['despesas'] - periodo1['despesas']) / periodo1['despesas'] * 100) if periodo1['despesas'] > 0 else 0
        variacao_saldo = ((periodo2['saldo'] - periodo1['saldo']) / abs(periodo1['saldo']) * 100) if periodo1['saldo'] != 0 else 0
        
        return jsonify({
            'periodo1': {
                'datas': {'inicio': data_inicio1.isoformat(), 'fim': data_fim1.isoformat()},
                'dados': periodo1
            },
            'periodo2': {
                'datas': {'inicio': data_inicio2.isoformat(), 'fim': data_fim2.isoformat()},
                'dados': periodo2
            },
            'variacoes': {
                'receitas': round(variacao_receitas, 2),
                'despesas': round(variacao_despesas, 2),
                'saldo': round(variacao_saldo, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/relatorios/indicadores', methods=['GET'])
def relatorio_indicadores():
    """Relatório de indicadores financeiros"""
    try:
        lancamentos = db.listar_lancamentos()
        contas = db.listar_contas()
        
        # Obter filtros de data
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
        
        hoje = date.today()
        
        if data_inicio_str and data_fim_str:
            inicio_mes = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            fim_periodo = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        else:
            # Padrão: mês atual
            inicio_mes = date(hoje.year, hoje.month, 1)
            fim_periodo = hoje
        
        # Totais do mês atual
        receitas_mes = Decimal('0')
        despesas_mes = Decimal('0')
        
        # Totais a receber/pagar
        total_receber = Decimal('0')
        total_pagar = Decimal('0')
        
        # Vencidos
        vencidos_receber = Decimal('0')
        vencidos_pagar = Decimal('0')
        
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_pag >= inicio_mes and data_pag <= fim_periodo:
                    valor = Decimal(str(l.valor))
                    if l.tipo == TipoLancamento.RECEITA:
                        receitas_mes += valor
                    else:
                        despesas_mes += valor
            
            if l.status == StatusLancamento.PENDENTE:
                valor = Decimal(str(l.valor))
                data_venc = l.data_vencimento.date() if hasattr(l.data_vencimento, 'date') else l.data_vencimento
                
                if l.tipo == TipoLancamento.RECEITA:
                    total_receber += valor
                    if data_venc < hoje:
                        vencidos_receber += valor
                else:
                    total_pagar += valor
                    if data_venc < hoje:
                        vencidos_pagar += valor
        
        # Saldo em caixa
        saldo_caixa = sum(Decimal(str(c.saldo_inicial)) for c in contas)
        
        # Liquidez = (Saldo + A Receber) / A Pagar
        liquidez = float((saldo_caixa + total_receber) / total_pagar) if total_pagar > 0 else 0
        
        # Margem líquida = (Receitas - Despesas) / Receitas * 100
        margem = float((receitas_mes - despesas_mes) / receitas_mes * 100) if receitas_mes > 0 else 0
        
        return jsonify({
            'saldo_caixa': float(saldo_caixa),
            'mes_atual': {
                'receitas': float(receitas_mes),
                'despesas': float(despesas_mes),
                'saldo': float(receitas_mes - despesas_mes)
            },
            'pendentes': {
                'receber': float(total_receber),
                'pagar': float(total_pagar)
            },
            'vencidos': {
                'receber': float(vencidos_receber),
                'pagar': float(vencidos_pagar)
            },
            'indicadores': {
                'liquidez': round(liquidez, 2),
                'margem_liquida': round(margem, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/relatorios/inadimplencia', methods=['GET'])
def relatorio_inadimplencia():
    """Relatório de inadimplência"""
    try:
        lancamentos = db.listar_lancamentos()
        hoje = date.today()
        
        inadimplentes = []
        
        for l in lancamentos:
            # Excluir transferências e considerar apenas PENDENTES
            if l.tipo == TipoLancamento.TRANSFERENCIA:
                continue
                
            if l.status == StatusLancamento.PENDENTE:
                # Converter data_vencimento para date se for datetime
                data_venc = l.data_vencimento.date() if hasattr(l.data_vencimento, 'date') else l.data_vencimento
                
                # Verificar se está vencido (data anterior a hoje)
                if data_venc < hoje:
                    dias_atraso = (hoje - data_venc).days
                    inadimplentes.append({
                        'id': l.id,
                        'tipo': l.tipo.value.upper(),
                        'descricao': l.descricao,
                        'valor': float(l.valor),
                        'data_vencimento': data_venc.isoformat(),
                        'dias_atraso': dias_atraso,
                        'pessoa': l.pessoa or 'Não informado',
                        'categoria': l.categoria or 'Sem categoria'
                    })
        
        # Ordenar por dias de atraso (maior para menor)
        inadimplentes.sort(key=lambda x: x['dias_atraso'], reverse=True)
        
        total_inadimplente = sum(i['valor'] for i in inadimplentes)
        
        return jsonify({
            'inadimplentes': inadimplentes,
            'total': total_inadimplente,
            'quantidade': len(inadimplentes)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    """Retorna o favicon"""
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.svg',
        mimetype='image/svg+xml'
    )


# === EXPORTAÇÃO DE CLIENTES E FORNECEDORES ===

@app.route('/api/clientes/exportar/pdf', methods=['GET'])
def exportar_clientes_pdf():
    """Exporta clientes para PDF"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
        from io import BytesIO
        
        clientes = db.listar_clientes()
        
        # Criar PDF em memória
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=0.5*cm, leftMargin=0.5*cm, topMargin=1*cm, bottomMargin=1*cm)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#2c3e50'), spaceAfter=15, alignment=1)
        elements.append(Paragraph(f'LISTA DE CLIENTES - {datetime.now().strftime("%d/%m/%Y")}', title_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Estilo de parágrafo para células
        cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=7, leading=9, wordWrap='CJK')
        
        # Dados da tabela com Paragraph para quebra de linha
        data = [['Razão Social', 'Nome Fantasia', 'CNPJ', 'Cidade', 'Est', 'Telefone', 'Email']]
        
        for cli in clientes:
            # Truncar textos longos e usar Paragraph para quebra automática
            razao = cli.get('razao_social', '-') or '-'
            fantasia = cli.get('nome_fantasia', '-') or '-'
            cnpj = cli.get('cnpj', '-') or '-'
            cidade = cli.get('cidade', '-') or '-'
            estado = cli.get('estado', '-') or '-'
            telefone = cli.get('telefone', '-') or '-'
            email = cli.get('email', '-') or '-'
            
            # Limitar tamanho dos textos muito longos
            if len(razao) > 35:
                razao = razao[:32] + '...'
            if len(fantasia) > 30:
                fantasia = fantasia[:27] + '...'
            if len(cidade) > 20:
                cidade = cidade[:17] + '...'
            if len(email) > 25:
                email = email[:22] + '...'
            
            data.append([
                Paragraph(razao, cell_style),
                Paragraph(fantasia, cell_style),
                Paragraph(cnpj, cell_style),
                Paragraph(cidade, cell_style),
                estado,
                Paragraph(telefone, cell_style),
                Paragraph(email, cell_style)
            ])
        
        # Largura disponível: A4 landscape = 29.7cm, menos margens = ~28.7cm
        # Criar tabela com larguras proporcionais
        table = Table(data, colWidths=[6*cm, 5*cm, 3.5*cm, 4*cm, 1.5*cm, 3.5*cm, 4.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'clientes_{datetime.now().strftime("%Y%m%d")}.pdf')
    
    except Exception as e:
        print(f"Erro ao exportar PDF: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/clientes/exportar/excel', methods=['GET'])
def exportar_clientes_excel():
    """Exporta clientes para Excel"""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        from openpyxl.worksheet.worksheet import Worksheet
        from io import BytesIO
        
        clientes = db.listar_clientes()
        
        wb = openpyxl.Workbook()
        ws: Worksheet = wb.active  # type: ignore
        ws.title = "Clientes"
        
        headers = ['Razão Social', 'Nome Fantasia', 'CNPJ', 'IE', 'IM', 'Rua', 'Número', 'Complemento', 'Bairro', 'Cidade', 'Estado', 'CEP', 'Telefone', 'Email']
        ws.append(headers)
        
        header_fill = PatternFill(start_color="34495e", end_color="34495e", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for cli in clientes:
            ws.append([
                cli.get('razao_social', ''), cli.get('nome_fantasia', ''), cli.get('cnpj', ''),
                cli.get('ie', ''), cli.get('im', ''), cli.get('rua', ''), cli.get('numero', ''),
                cli.get('complemento', ''), cli.get('bairro', ''), cli.get('cidade', ''),
                cli.get('estado', ''), cli.get('cep', ''), cli.get('telefone', ''), cli.get('email', '')
            ])
        
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter  # type: ignore
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)
        
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return send_file(buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'clientes_{datetime.now().strftime("%Y%m%d")}.xlsx')
    
    except Exception as e:
        print(f"Erro ao exportar Excel: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/fornecedores/exportar/pdf', methods=['GET'])
def exportar_fornecedores_pdf():
    """Exporta fornecedores para PDF"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
        from io import BytesIO
        
        fornecedores = db.listar_fornecedores()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=0.5*cm, leftMargin=0.5*cm, topMargin=1*cm, bottomMargin=1*cm)
        
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#2c3e50'), spaceAfter=15, alignment=1)
        elements.append(Paragraph(f'LISTA DE FORNECEDORES - {datetime.now().strftime("%d/%m/%Y")}', title_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Estilo de parágrafo para células
        cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=7, leading=9, wordWrap='CJK')
        
        data = [['Razão Social', 'Nome Fantasia', 'CNPJ', 'Cidade', 'Est', 'Telefone', 'Email']]
        
        for forn in fornecedores:
            razao = forn.get('razao_social', '-') or '-'
            fantasia = forn.get('nome_fantasia', '-') or '-'
            cnpj = forn.get('cnpj', '-') or '-'
            cidade = forn.get('cidade', '-') or '-'
            estado = forn.get('estado', '-') or '-'
            telefone = forn.get('telefone', '-') or '-'
            email = forn.get('email', '-') or '-'
            
            # Limitar tamanho dos textos muito longos
            if len(razao) > 35:
                razao = razao[:32] + '...'
            if len(fantasia) > 30:
                fantasia = fantasia[:27] + '...'
            if len(cidade) > 20:
                cidade = cidade[:17] + '...'
            if len(email) > 25:
                email = email[:22] + '...'
            
            data.append([
                Paragraph(razao, cell_style),
                Paragraph(fantasia, cell_style),
                Paragraph(cnpj, cell_style),
                Paragraph(cidade, cell_style),
                estado,
                Paragraph(telefone, cell_style),
                Paragraph(email, cell_style)
            ])
        
        table = Table(data, colWidths=[6*cm, 5*cm, 3.5*cm, 4*cm, 1.5*cm, 3.5*cm, 4.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'fornecedores_{datetime.now().strftime("%Y%m%d")}.pdf')
    
    except Exception as e:
        print(f"Erro ao exportar PDF: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/fornecedores/exportar/excel', methods=['GET'])
def exportar_fornecedores_excel():
    """Exporta fornecedores para Excel"""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        from openpyxl.worksheet.worksheet import Worksheet
        from io import BytesIO
        
        fornecedores = db.listar_fornecedores()
        
        wb = openpyxl.Workbook()
        ws: Worksheet = wb.active  # type: ignore
        ws.title = "Fornecedores"
        
        headers = ['Razão Social', 'Nome Fantasia', 'CNPJ', 'IE', 'IM', 'Rua', 'Número', 'Complemento', 'Bairro', 'Cidade', 'Estado', 'CEP', 'Telefone', 'Email']
        ws.append(headers)
        
        header_fill = PatternFill(start_color="34495e", end_color="34495e", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for forn in fornecedores:
            ws.append([
                forn.get('razao_social', ''), forn.get('nome_fantasia', ''), forn.get('cnpj', ''),
                forn.get('ie', ''), forn.get('im', ''), forn.get('rua', ''), forn.get('numero', ''),
                forn.get('complemento', ''), forn.get('bairro', ''), forn.get('cidade', ''),
                forn.get('estado', ''), forn.get('cep', ''), forn.get('telefone', ''), forn.get('email', '')
            ])
        
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter  # type: ignore
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)
        
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return send_file(buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'fornecedores_{datetime.now().strftime("%Y%m%d")}.xlsx')
    
    except Exception as e:
        print(f"Erro ao exportar Excel: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Porta configurável (Railway usa variável de ambiente PORT)
    port = int(os.getenv('PORT', 5000))
    
    print("="*60)
    print("Sistema Financeiro - Versão Web")
    print("="*60)
    print(f"Servidor iniciado em: http://0.0.0.0:{port}")
    print(f"Banco de dados: {os.getenv('DATABASE_TYPE', 'sqlite')}")
    print("="*60)
    
    app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
