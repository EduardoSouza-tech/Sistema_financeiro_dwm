"""
Rotas da API para Sistema de Importação de Banco de Dados
"""

from flask import Blueprint, request, jsonify, session
from database_import_manager import DatabaseImportManager
from auth_middleware import require_permission
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Criar blueprint
import_bp = Blueprint('import_db', __name__, url_prefix='/api/admin/import')


@import_bp.route('/schema/externo', methods=['POST'])
@require_permission('admin')
def get_external_schema():
    """
    Obtém schema de banco de dados externo
    
    POST /api/admin/import/schema/externo
    Body: {
        "host": "localhost",
        "port": 5432,
        "database": "cliente_db",
        "user": "postgres",
        "password": "senha"
    }
    """
    try:
        db_config = request.json
        
        # Validar configurações obrigatórias
        required_fields = ['host', 'database', 'user', 'password']
        for field in required_fields:
            if field not in db_config:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        manager = DatabaseImportManager()
        schema = manager.get_external_database_schema(db_config)
        
        return jsonify({
            'success': True,
            'schema': schema,
            'total_tabelas': len(schema),
            'total_registros': sum(t['total_registros'] for t in schema.values())
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter schema externo: {e}")
        return jsonify({'error': str(e)}), 500


@import_bp.route('/schema/interno', methods=['GET'])
@require_permission('admin')
def get_internal_schema():
    """
    Obtém schema do banco de dados interno
    
    GET /api/admin/import/schema/interno
    """
    try:
        manager = DatabaseImportManager()
        schema = manager.get_internal_database_schema()
        
        return jsonify({
            'success': True,
            'schema': schema,
            'total_tabelas': len(schema)
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter schema interno: {e}")
        return jsonify({'error': str(e)}), 500


@import_bp.route('/sugestao-mapeamento', methods=['POST'])
@require_permission('admin')
def suggest_mapping():
    """
    Sugere mapeamento automático entre schemas
    
    POST /api/admin/import/sugestao-mapeamento
    Body: {
        "schema_externo": {...},
        "schema_interno": {...}
    }
    """
    try:
        data = request.json
        schema_externo = data.get('schema_externo', {})
        schema_interno = data.get('schema_interno', {})
        
        if not schema_externo or not schema_interno:
            return jsonify({'error': 'Schemas externo e interno são obrigatórios'}), 400
        
        manager = DatabaseImportManager()
        suggestions = manager.suggest_table_mapping(schema_externo, schema_interno)
        
        return jsonify({
            'success': True,
            'sugestoes': suggestions,
            'total_mapeamentos': len(suggestions)
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar sugestões: {e}")
        return jsonify({'error': str(e)}), 500


@import_bp.route('/criar', methods=['POST'])
@require_permission('admin')
def create_import():
    """
    Cria nova importação
    
    POST /api/admin/import/criar
    Body: {
        "nome": "Importação Cliente XYZ",
        "descricao": "Importação de dados do cliente",
        "banco_origem": "cliente_db",
        "db_config": {...},
        "mapeamentos": [...]
    }
    """
    try:
        data = request.json
        usuario_id = session.get('usuario_id')
        
        # Validar campos obrigatórios
        if not data.get('nome'):
            return jsonify({'error': 'Nome da importação é obrigatório'}), 400
        
        manager = DatabaseImportManager()
        manager.connect()
        
        # Criar registro de importação
        manager.cursor.execute("""
            INSERT INTO import_historico 
            (nome, descricao, banco_origem, usuario_id, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['nome'],
            data.get('descricao', ''),
            data.get('banco_origem', ''),
            usuario_id,
            'preparando'
        ))
        
        import_id = manager.cursor.fetchone()['id']
        
        # Salvar mapeamentos
        if data.get('mapeamentos'):
            manager.save_import_mapping(import_id, data['mapeamentos'])
        
        manager.conn.commit()
        manager.disconnect()
        
        return jsonify({
            'success': True,
            'import_id': import_id,
            'message': 'Importação criada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar importação: {e}")
        return jsonify({'error': str(e)}), 500


@import_bp.route('/executar/<int:import_id>', methods=['POST'])
@require_permission('admin')
def execute_import(import_id):
    """
    Executa importação
    
    POST /api/admin/import/executar/<import_id>
    Body: {
        "db_config": {...}
    }
    """
    try:
        data = request.json
        db_config = data.get('db_config', {})
        
        if not db_config:
            return jsonify({'error': 'Configuração do banco é obrigatória'}), 400
        
        manager = DatabaseImportManager()
        result = manager.execute_import(import_id, db_config)
        
        return jsonify({
            'success': result['sucesso'],
            'registros_importados': result['registros_importados'],
            'registros_erro': result['registros_erro'],
            'erros': result['erros'][:10]  # Limitar primeiros 10 erros
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao executar importação: {e}")
        return jsonify({'error': str(e)}), 500


@import_bp.route('/listar', methods=['GET'])
@require_permission('admin')
def list_imports():
    """
    Lista todas as importações
    
    GET /api/admin/import/listar
    """
    try:
        manager = DatabaseImportManager()
        manager.connect()
        
        manager.cursor.execute("""
            SELECT 
                ih.*,
                u.nome as usuario_nome,
                COUNT(imt.id) as total_tabelas
            FROM import_historico ih
            LEFT JOIN usuarios u ON ih.usuario_id = u.id
            LEFT JOIN import_mapeamento_tabelas imt ON ih.id = imt.import_id
            GROUP BY ih.id, u.nome
            ORDER BY ih.data_importacao DESC
        """)
        
        imports = manager.cursor.fetchall()
        manager.disconnect()
        
        return jsonify({
            'success': True,
            'imports': [dict(imp) for imp in imports]
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar importações: {e}")
        return jsonify({'error': str(e)}), 500


@import_bp.route('/detalhes/<int:import_id>', methods=['GET'])
@require_permission('admin')
def get_import_details(import_id):
    """
    Obtém detalhes de uma importação
    
    GET /api/admin/import/detalhes/<import_id>
    """
    try:
        manager = DatabaseImportManager()
        manager.connect()
        
        # Buscar importação
        manager.cursor.execute("""
            SELECT ih.*, u.nome as usuario_nome
            FROM import_historico ih
            LEFT JOIN usuarios u ON ih.usuario_id = u.id
            WHERE ih.id = %s
        """, (import_id,))
        
        import_data = manager.cursor.fetchone()
        
        if not import_data:
            return jsonify({'error': 'Importação não encontrada'}), 404
        
        # Buscar mapeamentos
        manager.cursor.execute("""
            SELECT 
                imt.*,
                json_agg(
                    json_build_object(
                        'coluna_origem', imc.coluna_origem,
                        'coluna_destino', imc.coluna_destino,
                        'tipo_transformacao', imc.tipo_transformacao
                    )
                ) as colunas
            FROM import_mapeamento_tabelas imt
            LEFT JOIN import_mapeamento_colunas imc ON imt.id = imc.mapeamento_tabela_id
            WHERE imt.import_id = %s
            GROUP BY imt.id
            ORDER BY imt.ordem_execucao
        """, (import_id,))
        
        mappings = manager.cursor.fetchall()
        
        # Buscar erros se houver
        manager.cursor.execute("""
            SELECT * FROM import_log_erros
            WHERE import_id = %s
            ORDER BY data_erro DESC
            LIMIT 50
        """, (import_id,))
        
        errors = manager.cursor.fetchall()
        
        manager.disconnect()
        
        return jsonify({
            'success': True,
            'import': dict(import_data),
            'mapeamentos': [dict(m) for m in mappings],
            'erros': [dict(e) for e in errors]
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter detalhes: {e}")
        return jsonify({'error': str(e)}), 500


@import_bp.route('/reverter/<int:import_id>', methods=['POST'])
@require_permission('admin')
def rollback_import(import_id):
    """
    Reverte uma importação
    
    POST /api/admin/import/reverter/<import_id>
    """
    try:
        manager = DatabaseImportManager()
        success = manager.rollback_import(import_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Importação revertida com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erro ao reverter importação'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Erro ao reverter importação: {e}")
        return jsonify({'error': str(e)}), 500


@import_bp.route('/deletar/<int:import_id>', methods=['DELETE'])
@require_permission('admin')
def delete_import(import_id):
    """
    Deleta uma importação e seus mapeamentos
    
    DELETE /api/admin/import/deletar/<import_id>
    """
    try:
        manager = DatabaseImportManager()
        manager.connect()
        
        # Verificar se já foi executada
        manager.cursor.execute("""
            SELECT status FROM import_historico WHERE id = %s
        """, (import_id,))
        
        import_data = manager.cursor.fetchone()
        
        if not import_data:
            return jsonify({'error': 'Importação não encontrada'}), 404
        
        if import_data['status'] == 'concluido':
            return jsonify({
                'error': 'Não é possível deletar importação já executada. Use reverter primeiro.'
            }), 400
        
        # Deletar (CASCADE remove mapeamentos e logs)
        manager.cursor.execute("""
            DELETE FROM import_historico WHERE id = %s
        """, (import_id,))
        
        manager.conn.commit()
        manager.disconnect()
        
        return jsonify({
            'success': True,
            'message': 'Importação deletada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao deletar importação: {e}")
        return jsonify({'error': str(e)}), 500
