"""
Rotas da API para Sistema de Importação de Banco de Dados
"""

from flask import Blueprint, request, jsonify, session
from database_import_manager import DatabaseImportManager
from auth_middleware import require_permission
from datetime import datetime
from werkzeug.utils import secure_filename
import logging
import os
import tempfile
import json
import csv
import re

logger = logging.getLogger(__name__)

# Criar blueprint
import_bp = Blueprint('import_db', __name__, url_prefix='/api/admin/import')

# Configurações de upload
ALLOWED_EXTENSIONS = {'sql', 'dump', 'backup', 'csv', 'json', 'db', 'db-shm', 'db-wal', 'sqlite', 'sqlite3'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@import_bp.route('/upload', methods=['POST'])
@require_permission('admin')
def upload_file():
    """
    Recebe arquivo(s) de backup/dump e processa
    
    POST /api/admin/import/upload
    Form-data: file ou files[], empresa_id
    """
    try:
        # Verificar se é upload múltiplo (SQLite com .db-shm e .db-wal)
        multiple_files = request.files.getlist('files[]')
        
        if multiple_files:
            # Upload múltiplo (SQLite completo)
            logger.info(f"Upload múltiplo: {len(multiple_files)} arquivos")
            
            # Salvar todos os arquivos
            temp_dir = tempfile.gettempdir()
            db_file_path = None
            
            for file in multiple_files:
                if file.filename == '':
                    continue
                
                if not allowed_file(file.filename):
                    return jsonify({'error': f'Formato não suportado: {file.filename}'}), 400
                
                filename = secure_filename(file.filename)
                temp_path = os.path.join(temp_dir, f"import_{session.get('usuario_id')}_{filename}")
                file.save(temp_path)
                
                # Identificar o arquivo .db principal
                if filename.endswith('.db') or filename.endswith('.sqlite') or filename.endswith('.sqlite3'):
                    db_file_path = temp_path
                
                logger.info(f"Arquivo salvo: {temp_path}")
            
            if not db_file_path:
                return jsonify({'error': 'Arquivo .db principal não encontrado'}), 400
            
            # Processar o banco SQLite
            manager = DatabaseImportManager()
            schema = manager.parse_sqlite_database(db_file_path)
            
            return jsonify({
                'success': True,
                'schema': schema,
                'temp_file': db_file_path,
                'total_tabelas': len(schema),
                'total_registros': sum(t.get('total_registros', 0) for t in schema.values())
            })
        
        # Upload único (padrão)
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'Formato não suportado. Use: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Validar tamanho
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'Arquivo muito grande (máx: 100MB)'}), 400
        
        # Salvar arquivo temporariamente
        filename = secure_filename(file.filename)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"import_{session.get('usuario_id')}_{filename}")
        file.save(temp_path)
        
        logger.info(f"Arquivo salvo temporariamente: {temp_path}")
        
        # Processar baseado na extensão
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        manager = DatabaseImportManager()
        
        if file_ext == 'sql' or file_ext == 'dump' or file_ext == 'backup':
            # Processar dump SQL
            schema = manager.parse_sql_dump(temp_path)
        elif file_ext == 'csv':
            # Processar CSV
            schema = manager.parse_csv_file(temp_path)
        elif file_ext == 'json':
            # Processar JSON
            schema = manager.parse_json_file(temp_path)
        elif file_ext in ['db', 'db-shm', 'db-wal', 'sqlite', 'sqlite3']:
            # Processar SQLite
            schema = manager.parse_sqlite_database(temp_path)
        else:
            return jsonify({'error': 'Formato não reconhecido'}), 400
        
        # Manter arquivo temporário para importação posterior
        # Será deletado após a importação
        
        return jsonify({
            'success': True,
            'schema': schema,
            'temp_file': temp_path,
            'total_tabelas': len(schema),
            'total_registros': sum(t.get('total_registros', 0) for t in schema.values())
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar arquivo: {e}")
        return jsonify({'error': str(e)}), 500


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
    Obtém schema do banco de dados interno usando a mesma conexão do sistema
    
    GET /api/admin/import/schema/interno
    """
    try:
        from database_postgresql import DatabaseManager
        import psycopg2.extras
        
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Buscar todas as tabelas do schema public
        cursor.execute("""
            SELECT 
                table_name,
                (SELECT COUNT(*) FROM information_schema.columns 
                 WHERE table_schema = 'public' AND table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        schema = {}
        
        for table in tables:
            table_name = table['table_name']
            
            # Buscar colunas da tabela
            cursor.execute("""
                SELECT 
                    column_name as name,
                    data_type as type,
                    is_nullable,
                    column_default as default_value
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            # Debug: Log especial para tabela categorias
            if table_name == 'categorias':
                logger.info(f"📋 Tabela CATEGORIAS - Total de colunas: {len(columns)}")
                for col in columns:
                    logger.info(f"   - {col['name']}: {col['type']}")
            
            # Contar registros (com timeout)
            try:
                cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
                count_result = cursor.fetchone()
                total_registros = count_result['total'] if count_result else 0
            except:
                total_registros = 0
            
            schema[table_name] = {
                'columns': [dict(col) for col in columns],
                'total_registros': total_registros
            }
        
        conn.close()
        
        logger.info(f"✅ Schema interno carregado: {len(schema)} tabelas")
        
        return jsonify({
            'success': True,
            'schema': schema,
            'total_tabelas': len(schema)
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter schema interno: {e}")
        import traceback
        traceback.print_exc()
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
        
        # Aceitar empresa_id do body ou da sessão
        empresa_id = data.get('empresa_id') or session.get('empresa_id')
        
        logger.info(f"📝 Criar importação - Dados recebidos:")
        logger.info(f"   nome: {data.get('nome')}")
        logger.info(f"   empresa_id (body): {data.get('empresa_id')}")
        logger.info(f"   empresa_id (session): {session.get('empresa_id')}")
        logger.info(f"   empresa_id (final): {empresa_id}")
        logger.info(f"   usuario_id: {usuario_id}")
        logger.info(f"   mapeamentos: {len(data.get('mapeamentos', []))} items")
        
        # Validar campos obrigatórios
        if not data.get('nome'):
            logger.error("❌ Nome da importação não fornecido")
            return jsonify({'error': 'Nome da importação é obrigatório'}), 400
        if not empresa_id:
            logger.error("❌ Empresa não selecionada")
            return jsonify({'error': 'Empresa não selecionada'}), 400
        
        manager = DatabaseImportManager()
        manager.connect()
        
        try:
            # Criar registro de importação
            manager.cursor.execute("""
                INSERT INTO import_historico 
                (nome, descricao, banco_origem, empresa_id, usuario_id, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data['nome'],
                data.get('descricao', ''),
                data.get('banco_origem', ''),
                empresa_id,
                usuario_id,
                'preparando'
            ))
            
            import_id = manager.cursor.fetchone()['id']
            
            # Salvar mapeamentos (já faz commit internamente)
            if data.get('mapeamentos'):
                manager.save_import_mapping(import_id, data['mapeamentos'])
            else:
                # Se não tem mapeamentos, fazer commit aqui
                manager.conn.commit()
            
            logger.info(f"✅ Importação criada: ID {import_id}")
            
            return jsonify({
                'success': True,
                'import_id': import_id,
                'message': 'Importação criada com sucesso'
            })
        finally:
            manager.disconnect()
        
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
        "arquivo_path": "path/to/file.db" (opcional, para SQLite),
        "db_config": {...} (opcional, para conexão direta)
    }
    """
    try:
        data = request.json or {}
        arquivo_path = data.get('arquivo_path')
        
        logger.info(f"🚀 Executar importação {import_id}")
        logger.info(f"   arquivo_path: {arquivo_path}")
        
        # Se tem arquivo_path, usar o arquivo já upado
        if arquivo_path:
            # Construir caminho completo do arquivo
            file_path = f"/tmp/import_None_{arquivo_path}"
            logger.info(f"   Usando arquivo: {file_path}")
            
            manager = DatabaseImportManager()
            result = manager.execute_import_from_file(import_id, file_path)
        else:
            # Conexão direta (não implementado ainda)
            return jsonify({'error': 'Importação via conexão direta não implementada ainda'}), 400
        
        return jsonify({
            'success': result.get('sucesso', False),
            'registros_importados': result.get('registros_importados', 0),
            'registros_erro': result.get('registros_erro', 0),
            'erros': result.get('erros', [])[:10]  # Limitar primeiros 10 erros
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao executar importação: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
                u.nome_completo as usuario_nome,
                COUNT(imt.id) as total_tabelas
            FROM import_historico ih
            LEFT JOIN usuarios u ON ih.usuario_id = u.id
            LEFT JOIN import_mapeamento_tabelas imt ON ih.id = imt.import_id
            GROUP BY ih.id, u.nome_completo
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
            SELECT ih.*, u.nome_completo as usuario_nome
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
