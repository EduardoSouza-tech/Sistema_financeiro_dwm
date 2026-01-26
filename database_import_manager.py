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
from config import DATABASE_CONFIG
import logging

logger = logging.getLogger(__name__)


class DatabaseImportManager:
    """Gerencia importações de banco de dados com mapeamento e rollback"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Conecta ao banco de dados"""
        try:
            self.conn = psycopg2.connect(**DATABASE_CONFIG)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            logger.info("✅ Conexão estabelecida com banco de dados")
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
        ext_cols = {col['column_name'].lower() for col in ext_info['columns']}
        int_cols = {col['column_name'].lower() for col in int_info['columns']}
        
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
        
        ext_col_names = {col['column_name'].lower(): col for col in ext_cols}
        int_col_names = {col['column_name'].lower(): col for col in int_cols}
        
        for ext_name, ext_col in ext_col_names.items():
            if ext_name in int_col_names:
                # Match exato
                mappings.append({
                    'coluna_origem': ext_col['column_name'],
                    'coluna_destino': int_col_names[ext_name]['column_name'],
                    'score': 100,
                    'tipo_origem': ext_col['data_type'],
                    'tipo_destino': int_col_names[ext_name]['data_type'],
                    'compativel': ext_col['data_type'] == int_col_names[ext_name]['data_type']
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
                    mappings.append({
                        'coluna_origem': ext_col['column_name'],
                        'coluna_destino': best_match['column_name'],
                        'score': round(best_score * 100, 2),
                        'tipo_origem': ext_col['data_type'],
                        'tipo_destino': best_match['data_type'],
                        'compativel': ext_col['data_type'] == best_match['data_type']
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
            self.connect()
            
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
            self.conn.rollback()
            logger.error(f"❌ Erro ao salvar mapeamento: {e}")
            return False
        finally:
            self.disconnect()
            
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
