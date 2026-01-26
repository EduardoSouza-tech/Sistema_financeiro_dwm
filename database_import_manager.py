"""
Sistema de Importação Inteligente de Banco de Dados
Permite importar dados de clientes com mapeamento de tabelas e rollback
"""

import psycopg2
import psycopg2.extras
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import sqlite3

logger = logging.getLogger(__name__)


class DatabaseImportManager:
    """Gerencia importações de banco de dados com mapeamento e rollback"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Conecta ao banco de dados usando DatabaseManager"""
        try:
            from database_postgresql import DatabaseManager
            db_manager = DatabaseManager()
            self.conn = db_manager.get_connection()
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            logger.info("✅ Conexão estabelecida com banco de dados (DatabaseManager)")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {e}")
            raise
            
    def disconnect(self):
        """Desconecta do banco de dados"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            
    def create_import_tables(self):
        """Cria tabelas para gerenciar importações"""
        try:
            self.connect()
            
            # Tabela de histórico de importações
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS import_historico (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    descricao TEXT,
                    banco_origem VARCHAR(255),
                    empresa_id INTEGER NOT NULL,
                    data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_id INTEGER,
                    status VARCHAR(50) DEFAULT 'em_andamento',
                    total_registros INTEGER DEFAULT 0,
                    registros_importados INTEGER DEFAULT 0,
                    registros_erro INTEGER DEFAULT 0,
                    tempo_execucao INTEGER,
                    hash_dados VARCHAR(64),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
                )
            """)
            
            # Tabela de mapeamento de tabelas
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS import_mapeamento_tabelas (
                    id SERIAL PRIMARY KEY,
                    import_id INTEGER NOT NULL,
                    tabela_origem VARCHAR(255) NOT NULL,
                    tabela_destino VARCHAR(255) NOT NULL,
                    condicao_importacao TEXT,
                    ordem_execucao INTEGER DEFAULT 0,
                    ativo BOOLEAN DEFAULT true,
                    FOREIGN KEY (import_id) REFERENCES import_historico(id) ON DELETE CASCADE,
                    UNIQUE(import_id, tabela_origem, tabela_destino)
                )
            """)
            
            # Tabela de mapeamento de colunas
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS import_mapeamento_colunas (
                    id SERIAL PRIMARY KEY,
                    mapeamento_tabela_id INTEGER NOT NULL,
                    coluna_origem VARCHAR(255) NOT NULL,
                    coluna_destino VARCHAR(255) NOT NULL,
                    tipo_transformacao VARCHAR(50),
                    valor_padrao TEXT,
                    obrigatorio BOOLEAN DEFAULT false,
                    FOREIGN KEY (mapeamento_tabela_id) REFERENCES import_mapeamento_tabelas(id) ON DELETE CASCADE
                )
            """)
            
            # Tabela de backup (snapshot antes da importação)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS import_backup (
                    id SERIAL PRIMARY KEY,
                    import_id INTEGER NOT NULL,
                    tabela VARCHAR(255) NOT NULL,
                    registro_id INTEGER NOT NULL,
                    dados_antigos JSONB,
                    operacao VARCHAR(20) NOT NULL,
                    data_backup TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (import_id) REFERENCES import_historico(id) ON DELETE CASCADE
                )
            """)
            
            # Tabela de log de erros
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS import_log_erros (
                    id SERIAL PRIMARY KEY,
                    import_id INTEGER NOT NULL,
                    tabela VARCHAR(255),
                    registro JSONB,
                    erro TEXT,
                    data_erro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (import_id) REFERENCES import_historico(id) ON DELETE CASCADE
                )
            """)
            
            self.conn.commit()
            logger.info("✅ Tabelas de importação criadas com sucesso")
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao criar tabelas: {e}")
            raise
        finally:
            self.disconnect()
            
    def get_external_database_schema(self, db_config: Dict) -> Dict:
        """
        Obtém o schema de um banco de dados externo
        
        Args:
            db_config: Configurações de conexão do banco externo
            
        Returns:
            Dict com estrutura das tabelas
        """
        try:
            external_conn = psycopg2.connect(**db_config)
            external_cursor = external_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Buscar todas as tabelas
            external_cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            tables = external_cursor.fetchall()
            schema = {}
            
            for table in tables:
                table_name = table['table_name']
                
                # Buscar colunas da tabela
                external_cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = external_cursor.fetchall()
                
                # Contar registros
                external_cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
                count = external_cursor.fetchone()['total']
                
                schema[table_name] = {
                    'columns': [dict(col) for col in columns],
                    'total_registros': count
                }
            
            external_cursor.close()
            external_conn.close()
            
            logger.info(f"✅ Schema externo obtido: {len(schema)} tabelas")
            return schema
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter schema externo: {e}")
            raise
            
    def get_internal_database_schema(self) -> Dict:
        """
        Obtém o schema do banco de dados interno
        
        Returns:
            Dict com estrutura das tabelas
        """
        try:
            self.connect()
            
            # Buscar todas as tabelas
            self.cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND table_name NOT LIKE 'import_%'
                ORDER BY table_name
            """)
            
            tables = self.cursor.fetchall()
            schema = {}
            
            for table in tables:
                table_name = table['table_name']
                
                # Buscar colunas da tabela
                self.cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = self.cursor.fetchall()
                
                schema[table_name] = {
                    'columns': [dict(col) for col in columns]
                }
            
            logger.info(f"✅ Schema interno obtido: {len(schema)} tabelas")
            return schema
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter schema interno: {e}")
            raise
        finally:
            self.disconnect()
    
    def parse_sql_dump(self, file_path: str) -> Dict:
        """
        Analisa um arquivo SQL dump e extrai estrutura das tabelas
        
        Args:
            file_path: Caminho do arquivo SQL
            
        Returns:
            Dict com schema das tabelas
        """
        import re
        
        schema = {}
        current_table = None
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Encontrar CREATE TABLE statements
            create_table_pattern = r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?["`]?(\w+)["`]?\s*\((.*?)\);'
            matches = re.finditer(create_table_pattern, content, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                table_name = match.group(1)
                columns_def = match.group(2)
                
                # Extrair colunas
                columns = []
                for line in columns_def.split(','):
                    line = line.strip()
                    if not line or line.upper().startswith(('PRIMARY', 'FOREIGN', 'UNIQUE', 'KEY', 'CONSTRAINT', 'INDEX')):
                        continue
                    
                    # Parse: nome_coluna tipo [NULL|NOT NULL] [DEFAULT ...]
                    parts = line.split()
                    if len(parts) >= 2:
                        col_name = parts[0].strip('`"')
                        col_type = parts[1].upper()
                        
                        # Normalizar tipos
                        if 'INT' in col_type:
                            col_type = 'integer'
                        elif 'VARCHAR' in col_type or 'TEXT' in col_type or 'CHAR' in col_type:
                            col_type = 'character varying'
                        elif 'DECIMAL' in col_type or 'NUMERIC' in col_type:
                            col_type = 'numeric'
                        elif 'TIMESTAMP' in col_type or 'DATETIME' in col_type:
                            col_type = 'timestamp without time zone'
                        elif 'DATE' in col_type:
                            col_type = 'date'
                        elif 'BOOL' in col_type:
                            col_type = 'boolean'
                        
                        columns.append({
                            'column_name': col_name,
                            'data_type': col_type,
                            'is_nullable': 'NO' if 'NOT NULL' in line.upper() else 'YES'
                        })
                
                if columns:
                    schema[table_name] = {
                        'columns': columns,
                        'total_registros': 0  # Não temos como contar sem importar
                    }
            
            logger.info(f"✅ SQL Dump parseado: {len(schema)} tabelas encontradas")
            return schema
            
        except Exception as e:
            logger.error(f"❌ Erro ao parsear SQL dump: {e}")
            raise
    
    def parse_csv_file(self, file_path: str) -> Dict:
        """
        Analisa um arquivo CSV e cria schema baseado nas colunas
        
        Args:
            file_path: Caminho do arquivo CSV
            
        Returns:
            Dict com schema inferido
        """
        import csv
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                
                # Contar registros
                rows = list(reader)
                total_rows = len(rows)
                
                # Inferir tipos baseado nos valores
                columns = []
                for field in fieldnames:
                    # Tentar detectar tipo
                    sample_values = [row[field] for row in rows[:100] if row.get(field)]
                    
                    col_type = 'character varying'  # Default
                    
                    if sample_values:
                        # Tentar detectar número
                        if all(v.replace('.', '').replace('-', '').isdigit() for v in sample_values if v):
                            col_type = 'numeric'
                        # Tentar detectar inteiro
                        elif all(v.replace('-', '').isdigit() for v in sample_values if v):
                            col_type = 'integer'
                        # Tentar detectar data
                        elif any(v.count('-') == 2 or v.count('/') == 2 for v in sample_values if v):
                            col_type = 'date'
                    
                    columns.append({
                        'column_name': field,
                        'data_type': col_type,
                        'is_nullable': 'YES'
                    })
                
                # Nome da tabela baseado no arquivo
                table_name = file_path.split('/')[-1].split('\\')[-1].replace('.csv', '').replace(' ', '_').lower()
                
                schema = {
                    table_name: {
                        'columns': columns,
                        'total_registros': total_rows
                    }
                }
                
                logger.info(f"✅ CSV parseado: {total_rows} registros")
                return schema
                
        except Exception as e:
            logger.error(f"❌ Erro ao parsear CSV: {e}")
            raise
    
    def parse_json_file(self, file_path: str) -> Dict:
        """
        Analisa um arquivo JSON e cria schema baseado na estrutura
        
        Args:
            file_path: Caminho do arquivo JSON
            
        Returns:
            Dict com schema inferido
        """
        import json
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Assumir que JSON é um dict de tabelas ou array de objetos
            schema = {}
            
            if isinstance(data, dict):
                # Formato: { "tabela1": [{...}, {...}], "tabela2": [...] }
                for table_name, records in data.items():
                    if isinstance(records, list) and records:
                        columns = []
                        first_record = records[0]
                        
                        for key, value in first_record.items():
                            col_type = 'character varying'
                            
                            if isinstance(value, int):
                                col_type = 'integer'
                            elif isinstance(value, float):
                                col_type = 'numeric'
                            elif isinstance(value, bool):
                                col_type = 'boolean'
                            
                            columns.append({
                                'column_name': key,
                                'data_type': col_type,
                                'is_nullable': 'YES'
                            })
                        
                        schema[table_name] = {
                            'columns': columns,
                            'total_registros': len(records)
                        }
            
            elif isinstance(data, list) and data:
                # Formato: [{...}, {...}] - Uma única tabela
                table_name = file_path.split('/')[-1].split('\\')[-1].replace('.json', '').replace(' ', '_').lower()
                columns = []
                first_record = data[0]
                
                for key, value in first_record.items():
                    col_type = 'character varying'
                    
                    if isinstance(value, int):
                        col_type = 'integer'
                    elif isinstance(value, float):
                        col_type = 'numeric'
                    elif isinstance(value, bool):
                        col_type = 'boolean'
                    
                    columns.append({
                        'column_name': key,
                        'data_type': col_type,
                        'is_nullable': 'YES'
                    })
                
                schema[table_name] = {
                    'columns': columns,
                    'total_registros': len(data)
                }
            
            logger.info(f"✅ JSON parseado: {len(schema)} tabela(s)")
            return schema
            
        except Exception as e:
            logger.error(f"❌ Erro ao parsear JSON: {e}")
            raise
    
    def parse_sqlite_database(self, file_path: str) -> Dict:
        """
        Analisa um banco de dados SQLite e extrai estrutura completa
        
        Args:
            file_path: Caminho do arquivo .db
            
        Returns:
            Dict com schema das tabelas
        """
        try:
            # Conectar ao SQLite
            conn = sqlite3.connect(file_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Buscar todas as tabelas (exceto sqlite_*)
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            
            tables = cursor.fetchall()
            schema = {}
            
            for table_row in tables:
                table_name = table_row[0]
                
                # Obter informações das colunas
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                
                columns = []
                for col in columns_info:
                    col_name = col[1]
                    col_type = col[2].upper()
                    not_null = col[3]
                    
                    # Mapear tipos SQLite para PostgreSQL
                    pg_type = 'character varying'  # Default
                    
                    if 'INT' in col_type:
                        pg_type = 'integer'
                    elif 'REAL' in col_type or 'FLOAT' in col_type or 'DOUBLE' in col_type:
                        pg_type = 'numeric'
                    elif 'TEXT' in col_type or 'CHAR' in col_type or 'CLOB' in col_type:
                        pg_type = 'character varying'
                    elif 'BLOB' in col_type:
                        pg_type = 'bytea'
                    elif 'NUMERIC' in col_type or 'DECIMAL' in col_type:
                        pg_type = 'numeric'
                    elif 'DATE' in col_type:
                        pg_type = 'date'
                    elif 'TIME' in col_type:
                        pg_type = 'timestamp without time zone'
                    elif 'BOOL' in col_type:
                        pg_type = 'boolean'
                    
                    columns.append({
                        'column_name': col_name,
                        'data_type': pg_type,
                        'is_nullable': 'NO' if not_null else 'YES'
                    })
                
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_registros = cursor.fetchone()[0]
                
                schema[table_name] = {
                    'columns': columns,
                    'total_registros': total_registros
                }
            
            conn.close()
            logger.info(f"✅ SQLite parseado: {len(schema)} tabelas, {sum(t['total_registros'] for t in schema.values())} registros")
            return schema
            
        except Exception as e:
            logger.error(f"❌ Erro ao parsear SQLite: {e}")
            raise
            
    def suggest_table_mapping(self, external_schema: Dict, internal_schema: Dict) -> List[Dict]:
        """
        Sugere mapeamento automático entre tabelas baseado em similaridade
        
        Args:
            external_schema: Schema do banco externo
            internal_schema: Schema do banco interno
            
        Returns:
            Lista de sugestões de mapeamento
        """
        suggestions = []
        
        for ext_table, ext_info in external_schema.items():
            best_match = None
            best_score = 0
            
            for int_table, int_info in internal_schema.items():
                # Calcular score de similaridade
                score = self._calculate_table_similarity(
                    ext_table, ext_info, 
                    int_table, int_info
                )
                
                if score > best_score:
                    best_score = score
                    best_match = int_table
            
            if best_match and best_score > 0.5:  # Threshold de 50%
                suggestions.append({
                    'tabela_origem': ext_table,
                    'tabela_destino': best_match,
                    'score_similaridade': round(best_score * 100, 2),
                    'total_registros': ext_info['total_registros'],
                    'colunas_origem': len(ext_info['columns']),
                    'colunas_destino': len(internal_schema[best_match]['columns']),
                    'mapeamento_colunas': self._suggest_column_mapping(
                        ext_info['columns'],
                        internal_schema[best_match]['columns']
                    )
                })
        
        logger.info(f"✅ {len(suggestions)} sugestões de mapeamento geradas")
        return suggestions
        
    def _calculate_table_similarity(self, ext_name: str, ext_info: Dict, 
                                   int_name: str, int_info: Dict) -> float:
        """Calcula score de similaridade entre duas tabelas"""
        score = 0.0
        
        # Similaridade de nome (40% do score)
        name_similarity = self._string_similarity(ext_name, int_name)
        score += name_similarity * 0.4
        
        # Similaridade de colunas (60% do score)
        ext_cols = {col.get('name', col.get('column_name', '')).lower() for col in ext_info['columns'] if col.get('name') or col.get('column_name')}
        int_cols = {col.get('name', col.get('column_name', '')).lower() for col in int_info['columns'] if col.get('name') or col.get('column_name')}
        
        if ext_cols and int_cols:
            common_cols = len(ext_cols & int_cols)
            total_cols = len(ext_cols | int_cols)
            column_similarity = common_cols / total_cols if total_cols > 0 else 0
            score += column_similarity * 0.6
        
        return score
        
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calcula similaridade entre duas strings usando Levenshtein simplificado"""
        s1, s2 = s1.lower(), s2.lower()
        
        # Exact match
        if s1 == s2:
            return 1.0
            
        # Contains
        if s1 in s2 or s2 in s1:
            return 0.8
            
        # Levenshtein distance simplificado
        len1, len2 = len(s1), len(s2)
        max_len = max(len1, len2)
        
        if max_len == 0:
            return 0.0
            
        distance = sum(c1 != c2 for c1, c2 in zip(s1, s2))
        distance += abs(len1 - len2)
        
        return 1.0 - (distance / max_len)
        
    def _suggest_column_mapping(self, ext_cols: List[Dict], int_cols: List[Dict]) -> List[Dict]:
        """Sugere mapeamento de colunas"""
        mappings = []
        
        ext_col_names = {col.get('name', col.get('column_name', '')).lower(): col for col in ext_cols if col.get('name') or col.get('column_name')}
        int_col_names = {col.get('name', col.get('column_name', '')).lower(): col for col in int_cols if col.get('name') or col.get('column_name')}
        
        for ext_name, ext_col in ext_col_names.items():
            if ext_name in int_col_names:
                # Match exato
                ext_col_name = ext_col.get('name', ext_col.get('column_name', 'unknown'))
                int_col = int_col_names[ext_name]
                int_col_name = int_col.get('name', int_col.get('column_name', 'unknown'))
                ext_col_type = ext_col.get('type', ext_col.get('data_type', 'unknown'))
                int_col_type = int_col.get('type', int_col.get('data_type', 'unknown'))
                
                mappings.append({
                    'coluna_origem': ext_col_name,
                    'coluna_destino': int_col_name,
                    'score': 100,
                    'tipo_origem': ext_col_type,
                    'tipo_destino': int_col_type,
                    'compativel': ext_col_type == int_col_type
                })
            else:
                # Procurar similar
                best_match = None
                best_score = 0
                
                for int_name, int_col in int_col_names.items():
                    score = self._string_similarity(ext_name, int_name)
                    if score > best_score and score > 0.7:
                        best_score = score
                        best_match = int_col
                
                if best_match:
                    ext_col_name = ext_col.get('name', ext_col.get('column_name', 'unknown'))
                    int_col_name = best_match.get('name', best_match.get('column_name', 'unknown'))
                    ext_col_type = ext_col.get('type', ext_col.get('data_type', 'unknown'))
                    int_col_type = best_match.get('type', best_match.get('data_type', 'unknown'))
                    
                    mappings.append({
                        'coluna_origem': ext_col_name,
                        'coluna_destino': int_col_name,
                        'score': round(best_score * 100, 2),
                        'tipo_origem': ext_col_type,
                        'tipo_destino': int_col_type,
                        'compativel': ext_col_type == int_col_type
                    })
        
        return mappings
        
    def save_import_mapping(self, import_id: int, mappings: List[Dict]) -> bool:
        """
        Salva mapeamento de importação no banco
        
        Args:
            import_id: ID da importação
            mappings: Lista de mapeamentos
            
        Returns:
            bool: Sucesso da operação
        """
        try:
            # Não conectar se já estiver conectado
            if not self.conn or self.conn.closed:
                self.connect()
                auto_disconnect = True
            else:
                auto_disconnect = False
            
            for idx, mapping in enumerate(mappings):
                # Inserir mapeamento de tabela
                self.cursor.execute("""
                    INSERT INTO import_mapeamento_tabelas 
                    (import_id, tabela_origem, tabela_destino, ordem_execucao)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (
                    import_id,
                    mapping['tabela_origem'],
                    mapping['tabela_destino'],
                    idx
                ))
                
                mapeamento_id = self.cursor.fetchone()['id']
                
                # Inserir mapeamento de colunas
                for col_map in mapping.get('mapeamento_colunas', []):
                    self.cursor.execute("""
                        INSERT INTO import_mapeamento_colunas
                        (mapeamento_tabela_id, coluna_origem, coluna_destino)
                        VALUES (%s, %s, %s)
                    """, (
                        mapeamento_id,
                        col_map['coluna_origem'],
                        col_map['coluna_destino']
                    ))
            
            self.conn.commit()
            logger.info(f"✅ Mapeamento salvo: {len(mappings)} tabelas")
            return True
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"❌ Erro ao salvar mapeamento: {e}")
            return False
        finally:
            # Só desconectar se foi auto-conectado
            if auto_disconnect:
                self.disconnect()
    
    def create_import_record(self, empresa_id: int, usuario_id: int, fonte_tipo: str, 
                            mapeamentos: List[Dict], schema_externo: Dict) -> int:
        """
        Cria registro de importação no histórico
        
        Args:
            empresa_id: ID da empresa
            usuario_id: ID do usuário
            fonte_tipo: Tipo da fonte (sqlite, mysql, postgresql)
            mapeamentos: Lista de mapeamentos de tabelas
            schema_externo: Schema do banco externo
            
        Returns:
            int: ID da importação criada
        """
        try:
            # Inserir histórico
            self.cursor.execute("""
                INSERT INTO import_historico 
                (empresa_id, usuario_id, data_importacao, fonte_tipo, fonte_host, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (empresa_id, usuario_id, datetime.now(), fonte_tipo, 'arquivo', 'pendente'))
            
            import_id = self.cursor.fetchone()['id']
            
            # Inserir mapeamentos de tabelas
            for mapa in mapeamentos:
                tabela_origem = mapa.get('tabela_origem')
                tabela_destino = mapa.get('tabela_destino')
                colunas_mapeamento = mapa.get('colunas', [])
                
                self.cursor.execute("""
                    INSERT INTO import_mapeamento_tabelas
                    (import_id, tabela_origem, tabela_destino, ativo)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (import_id, tabela_origem, tabela_destino, True))
                
                mapeamento_tabela_id = self.cursor.fetchone()['id']
                
                # Inserir mapeamentos de colunas
                for col_map in colunas_mapeamento:
                    coluna_origem = col_map.get('origem')
                    coluna_destino = col_map.get('destino')
                    transformacao = col_map.get('transformacao')
                    
                    self.cursor.execute("""
                        INSERT INTO import_mapeamento_colunas
                        (mapeamento_tabela_id, coluna_origem, coluna_destino, transformacao)
                        VALUES (%s, %s, %s, %s)
                    """, (mapeamento_tabela_id, coluna_origem, coluna_destino, transformacao))
            
            self.conn.commit()
            logger.info(f"✅ Importação {import_id} criada com sucesso")
            return import_id
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao criar registro de importação: {e}")
            raise
            
    def execute_import(self, import_id: int, external_db_config: Dict) -> Dict:
        """
        Executa importação de dados
        
        Args:
            import_id: ID da importação
            external_db_config: Config do banco externo
            
        Returns:
            Dict com resultado da importação
        """
        start_time = datetime.now()
        result = {
            'sucesso': False,
            'registros_importados': 0,
            'registros_erro': 0,
            'erros': []
        }
        
        try:
            self.connect()
            external_conn = psycopg2.connect(**external_db_config)
            external_cursor = external_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Buscar mapeamentos
            self.cursor.execute("""
                SELECT * FROM import_mapeamento_tabelas
                WHERE import_id = %s AND ativo = true
                ORDER BY ordem_execucao
            """, (import_id,))
            
            mappings = self.cursor.fetchall()
            
            for mapping in mappings:
                logger.info(f"📊 Importando {mapping['tabela_origem']} -> {mapping['tabela_destino']}")
                
                # Buscar mapeamento de colunas
                self.cursor.execute("""
                    SELECT * FROM import_mapeamento_colunas
                    WHERE mapeamento_tabela_id = %s
                """, (mapping['id'],))
                
                column_mappings = self.cursor.fetchall()
                
                # Buscar dados da tabela origem
                external_cursor.execute(f"SELECT * FROM {mapping['tabela_origem']}")
                rows = external_cursor.fetchall()
                
                for row in rows:
                    try:
                        # Criar backup
                        self._create_backup_entry(import_id, mapping['tabela_destino'], row)
                        
                        # Transformar dados usando mapeamento
                        transformed_data = self._transform_row(row, column_mappings)
                        
                        # Inserir na tabela destino
                        self._insert_transformed_data(mapping['tabela_destino'], transformed_data)
                        
                        result['registros_importados'] += 1
                        
                    except Exception as e:
                        result['registros_erro'] += 1
                        result['erros'].append({
                            'tabela': mapping['tabela_origem'],
                            'registro': dict(row),
                            'erro': str(e)
                        })
                        
                        # Log de erro
                        self.cursor.execute("""
                            INSERT INTO import_log_erros
                            (import_id, tabela, registro, erro)
                            VALUES (%s, %s, %s, %s)
                        """, (import_id, mapping['tabela_origem'], json.dumps(dict(row)), str(e)))
            
            # Atualizar status da importação
            end_time = datetime.now()
            execution_time = int((end_time - start_time).total_seconds())
            
            self.cursor.execute("""
                UPDATE import_historico
                SET status = %s,
                    registros_importados = %s,
                    registros_erro = %s,
                    tempo_execucao = %s
                WHERE id = %s
            """, (
                'concluido' if result['registros_erro'] == 0 else 'concluido_com_erros',
                result['registros_importados'],
                result['registros_erro'],
                execution_time,
                import_id
            ))
            
            self.conn.commit()
            external_cursor.close()
            external_conn.close()
            
            result['sucesso'] = True
            logger.info(f"✅ Importação concluída: {result['registros_importados']} registros")
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro na importação: {e}")
            result['erros'].append({'geral': str(e)})
        finally:
            self.disconnect()
            
        return result
        
    def _create_backup_entry(self, import_id: int, table: str, data: Dict):
        """Cria entrada de backup antes de inserir"""
        # Implementar lógica de backup se registro já existe
        pass
        
    def _transform_row(self, row: Dict, column_mappings: List[Dict]) -> Dict:
        """Transforma registro usando mapeamento de colunas"""
        transformed = {}
        
        for mapping in column_mappings:
            value = row.get(mapping['coluna_origem'])
            transformed[mapping['coluna_destino']] = value
            
        return transformed
        
    def _insert_transformed_data(self, table: str, data: Dict):
        """Insere dados transformados na tabela destino"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = list(data.values())
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(query, values)
        
    def rollback_import(self, import_id: int) -> bool:
        """
        Desfaz uma importação usando os backups
        
        Args:
            import_id: ID da importação a ser desfeita
            
        Returns:
            bool: Sucesso da operação
        """
        try:
            self.connect()
            
            # Buscar backups
            self.cursor.execute("""
                SELECT * FROM import_backup
                WHERE import_id = %s
                ORDER BY id DESC
            """, (import_id,))
            
            backups = self.cursor.fetchall()
            
            for backup in backups:
                if backup['operacao'] == 'INSERT':
                    # Deletar registro inserido
                    self.cursor.execute(
                        f"DELETE FROM {backup['tabela']} WHERE id = %s",
                        (backup['registro_id'],)
                    )
                elif backup['operacao'] == 'UPDATE':
                    # Restaurar dados antigos
                    # Implementar restauração
                    pass
            
            # Atualizar status
            self.cursor.execute("""
                UPDATE import_historico
                SET status = 'revertido'
                WHERE id = %s
            """, (import_id,))
            
            self.conn.commit()
            logger.info(f"✅ Importação {import_id} revertida com sucesso")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao reverter importação: {e}")
            return False
        finally:
            self.disconnect()


if __name__ == "__main__":
    # Criar tabelas de importação
    manager = DatabaseImportManager()
    manager.create_import_tables()
