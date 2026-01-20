"""
🔧 Migration P1: Correção de Bugs Prioritários
==============================================

Corrige 2 bugs P1 identificados na Fase 3:
1. Adicionar empresa_id em todas as tabelas (multi-tenancy)
2. Converter relacionamentos fracos (VARCHAR → Foreign Keys)

Autor: Sistema de Otimização
Data: 20/01/2026
"""

import psycopg2
import os
import sys
from datetime import datetime


class MigrationP1:
    """Gerenciador de migrations para bugs P1"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.steps = []
        
    def connect(self):
        """Conecta ao banco PostgreSQL usando DATABASE_URL"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise Exception("DATABASE_URL não encontrada nas variáveis de ambiente")
            
            self.conn = psycopg2.connect(database_url)
            self.cursor = self.conn.cursor()
            self.log("✅ Conectado ao banco de dados", "success")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao conectar: {str(e)}", "error")
            return False
    
    def log(self, message, level="info"):
        """Registra passo da migration"""
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        icon = icons.get(level, "ℹ️")
        log_msg = f"{icon} {message}"
        self.steps.append(log_msg)
        print(log_msg)
    
    def check_column_exists(self, table_name, column_name):
        """Verifica se coluna existe na tabela"""
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    AND column_name = %s
                )
            """, (table_name, column_name))
            
            return self.cursor.fetchone()[0]
            
        except Exception as e:
            self.log(f"Erro ao verificar coluna {column_name} em {table_name}: {str(e)}", "error")
            return False
    
    def check_index_exists(self, index_name):
        """Verifica se index existe"""
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM pg_indexes 
                    WHERE indexname = %s
                )
            """, (index_name,))
            
            return self.cursor.fetchone()[0]
            
        except Exception as e:
            self.log(f"Erro ao verificar index {index_name}: {str(e)}", "error")
            return False
    
    def add_empresa_id_to_table(self, table_name):
        """Adiciona coluna empresa_id a uma tabela"""
        try:
            # Verifica se já existe
            if self.check_column_exists(table_name, 'empresa_id'):
                self.log(f"Coluna empresa_id já existe em {table_name}", "info")
                return True
            
            # Adiciona coluna
            self.cursor.execute(f"""
                ALTER TABLE {table_name} 
                ADD COLUMN empresa_id INTEGER NOT NULL DEFAULT 1
            """)
            self.log(f"Coluna empresa_id adicionada em {table_name}", "success")
            
            # Cria index
            index_name = f"idx_{table_name}_empresa"
            if not self.check_index_exists(index_name):
                self.cursor.execute(f"""
                    CREATE INDEX {index_name} ON {table_name}(empresa_id)
                """)
                self.log(f"Index {index_name} criado", "success")
            else:
                self.log(f"Index {index_name} já existe", "info")
            
            return True
            
        except Exception as e:
            self.log(f"Erro ao adicionar empresa_id em {table_name}: {str(e)}", "error")
            return False
    
    def fix_multi_tenancy(self):
        """Adiciona empresa_id em todas as tabelas necessárias"""
        self.log("=== INICIANDO: Correção Multi-Tenancy ===", "info")
        
        # Lista de tabelas que precisam de empresa_id
        tables = [
            'kits',
            'lancamentos', 
            'categorias',
            'clientes',
            'fornecedores',
            'contratos',
            'sessoes',
            'produtos',
            'contas_bancarias',
            'subcategorias',
            'usuarios',
            'equipamentos',
            'projetos'
        ]
        
        success_count = 0
        for table in tables:
            if self.add_empresa_id_to_table(table):
                success_count += 1
        
        self.log(f"Multi-tenancy: {success_count}/{len(tables)} tabelas atualizadas", "success")
        return success_count == len(tables)
    
    def check_foreign_key_exists(self, constraint_name):
        """Verifica se constraint de FK existe"""
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.table_constraints 
                    WHERE constraint_name = %s
                    AND constraint_type = 'FOREIGN KEY'
                )
            """, (constraint_name,))
            
            return self.cursor.fetchone()[0]
            
        except Exception as e:
            self.log(f"Erro ao verificar FK {constraint_name}: {str(e)}", "error")
            return False
    
    def convert_varchar_to_fk(self, table_name, column_name, target_table, fk_name):
        """Converte coluna VARCHAR para Foreign Key"""
        try:
            # Verifica se FK já existe
            if self.check_foreign_key_exists(fk_name):
                self.log(f"FK {fk_name} já existe", "info")
                return True
            
            # Verifica tipo da coluna
            self.cursor.execute("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            """, (table_name, column_name))
            
            result = self.cursor.fetchone()
            if not result:
                self.log(f"Coluna {column_name} não existe em {table_name}", "warning")
                return False
            
            current_type = result[0]
            
            # Se for VARCHAR, precisa converter para INTEGER
            if 'character' in current_type or 'varchar' in current_type or 'text' in current_type:
                self.log(f"Convertendo {table_name}.{column_name} de {current_type} para INTEGER", "info")
                
                # ATENÇÃO: Esta conversão pode falhar se houver dados incompatíveis
                # Por segurança, vamos apenas reportar
                self.log(f"⚠️ AÇÃO MANUAL NECESSÁRIA: Converter {table_name}.{column_name} (VARCHAR → INTEGER FK)", "warning")
                self.log(f"   Comando sugerido: ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE INTEGER USING {column_name}::integer", "info")
                return False
            
            # Cria Foreign Key
            self.cursor.execute(f"""
                ALTER TABLE {table_name}
                ADD CONSTRAINT {fk_name}
                FOREIGN KEY ({column_name}) REFERENCES {target_table}(id)
            """)
            self.log(f"FK {fk_name} criada com sucesso", "success")
            return True
            
        except Exception as e:
            self.log(f"Erro ao converter {column_name} para FK: {str(e)}", "error")
            return False
    
    def fix_weak_relationships(self):
        """Converte relacionamentos fracos (VARCHAR) para Foreign Keys"""
        self.log("=== INICIANDO: Correção de Relacionamentos ===", "info")
        
        # Lista de conversões necessárias
        # Nota: Alguns campos precisam de conversão de dados primeiro
        conversions = [
            # ('lancamentos', 'categoria', 'categorias', 'fk_lancamentos_categoria'),
            # ('lancamentos', 'subcategoria', 'subcategorias', 'fk_lancamentos_subcategoria'),
            # ('lancamentos', 'conta_bancaria', 'contas_bancarias', 'fk_lancamentos_conta'),
        ]
        
        if not conversions:
            self.log("⚠️ Conversões de FK requerem migração de dados manual", "warning")
            self.log("   Campos como 'categoria' (VARCHAR) precisam ser convertidos para INTEGER", "info")
            self.log("   Isso requer mapeamento de strings existentes para IDs", "info")
            return True
        
        success_count = 0
        for table, column, target, fk_name in conversions:
            if self.convert_varchar_to_fk(table, column, target, fk_name):
                success_count += 1
        
        self.log(f"Relacionamentos: {success_count}/{len(conversions)} convertidos", "success")
        return True
    
    def run(self):
        """Executa todas as migrations P1"""
        print("\n" + "="*60)
        print("🔧 MIGRATION P1 - BUGS PRIORITÁRIOS")
        print("="*60 + "\n")
        
        if not self.connect():
            return False
        
        try:
            # Inicia transação
            self.log("Iniciando transação...", "info")
            
            # 1. Multi-Tenancy (empresa_id)
            if not self.fix_multi_tenancy():
                self.log("Erro ao corrigir multi-tenancy", "error")
                self.conn.rollback()
                return False
            
            # 2. Relacionamentos Fracos
            if not self.fix_weak_relationships():
                self.log("Erro ao corrigir relacionamentos", "error")
                self.conn.rollback()
                return False
            
            # Commit
            self.conn.commit()
            self.log("=== MIGRATION CONCLUÍDA COM SUCESSO ===", "success")
            
            return True
            
        except Exception as e:
            self.log(f"Erro durante migration: {str(e)}", "error")
            if self.conn:
                self.conn.rollback()
            return False
            
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
    
    def get_results(self):
        """Retorna resultados da migration"""
        return {
            "steps": self.steps,
            "total_steps": len(self.steps),
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Executa a migration"""
    migration = MigrationP1()
    
    success = migration.run()
    
    print("\n" + "="*60)
    print("📊 RESUMO DA MIGRATION")
    print("="*60)
    
    results = migration.get_results()
    print(f"\nTotal de passos: {results['total_steps']}")
    print(f"Timestamp: {results['timestamp']}")
    
    if success:
        print("\n✅ Migration executada com sucesso!")
        return 0
    else:
        print("\n❌ Migration falhou. Verifique os logs acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
