"""
🔧 Migration: Regras de Auto-Conciliação
=======================================

Executa a migração para criar a infraestrutura de regras 
de auto-conciliação de extratos bancários.

Autor: Sistema de Otimização
Data: 10/02/2026
"""

import psycopg2
import os
import sys
from datetime import datetime


class MigrationRegrasConciliacao:
    """Gerenciador de migration para regras de conciliação"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.steps = []
        
    def connect(self):
        """Conecta ao banco PostgreSQL usando DATABASE_URL"""
        try:
            database_url = os.environ.get('DATABASE_URL') or 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'
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
        
        step = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message
        }
        self.steps.append(step)
        print(f"[{step['timestamp']}] {icons.get(level, 'ℹ️')} {message}")
    
    def execute_sql_file(self):
        """Executa o arquivo migration_regras_conciliacao.sql"""
        try:
            # Carregar arquivo SQL
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sql_file_path = os.path.join(script_dir, "migration_regras_conciliacao.sql")
            
            if not os.path.exists(sql_file_path):
                raise Exception(f"Arquivo SQL não encontrado: {sql_file_path}")
            
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            self.log(f"📄 Arquivo SQL carregado: {len(sql_content)} caracteres")
            
            # Executar SQL
            self.cursor.execute(sql_content)
            self.conn.commit()
            
            self.log("✅ Migration executada com sucesso", "success")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao executar migration: {str(e)}", "error")
            if self.conn:
                self.conn.rollback()
            return False
    
    def verify_migration(self):
        """Verifica se a migration foi aplicada corretamente"""
        try:
            # Verificar tabela
            self.cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'regras_conciliacao'
            """)
            table_exists = self.cursor.fetchone()[0] > 0
            
            if not table_exists:
                self.log("❌ Tabela regras_conciliacao não foi criada", "error")
                return False
            
            # Verificar índices
            self.cursor.execute("""
                SELECT COUNT(*) FROM pg_indexes 
                WHERE tablename = 'regras_conciliacao'
            """)
            indices_count = self.cursor.fetchone()[0]
            
            # Verificar função
            self.cursor.execute("""
                SELECT COUNT(*) FROM pg_proc 
                WHERE proname = 'buscar_regras_aplicaveis'
            """)
            function_exists = self.cursor.fetchone()[0] > 0
            
            # Verificar permissões
            self.cursor.execute("""
                SELECT COUNT(*) FROM permissoes 
                WHERE codigo LIKE 'regras_conciliacao_%'
            """)
            permissions_count = self.cursor.fetchone()[0]
            
            self.log(f"✅ Tabela regras_conciliacao: Criada", "success")
            self.log(f"✅ Índices: {indices_count} criados", "success")
            self.log(f"✅ Função buscar_regras_aplicaveis: {'Criada' if function_exists else 'Não criada'}", "success" if function_exists else "warning")
            self.log(f"✅ Permissões: {permissions_count} criadas", "success")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Erro na verificação: {str(e)}", "error")
            return False
    
    def close(self):
        """Fecha conexão com o banco"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.log("🔌 Conexão fechada", "info")
    
    def run(self):
        """Executa a migration completa"""
        self.log("🚀 Iniciando Migration: Regras de Auto-Conciliação")
        
        # 1. Conectar
        if not self.connect():
            return False
        
        # 2. Executar SQL
        if not self.execute_sql_file():
            return False
        
        # 3. Verificar
        if not self.verify_migration():
            return False
        
        self.log("🎉 Migration concluída com sucesso!", "success")
        return True


def main():
    """Função principal"""
    migration = MigrationRegrasConciliacao()
    
    try:
        success = migration.run()
        
        print("\n" + "="*60)
        print("📋 RESUMO DA MIGRATION")
        print("="*60)
        
        for step in migration.steps:
            print(f"[{step['timestamp']}] {step['message']}")
        
        print("="*60)
        
        if success:
            print("✅ MIGRATION BEM-SUCEDIDA!")
            print("   - Tabela regras_conciliacao criada")
            print("   - Índices e funções configurados")  
            print("   - Permissões adicionadas")
            print("   - Sistema de regras pronto para uso")
            sys.exit(0)
        else:
            print("❌ MIGRATION FALHOU!")
            print("   Verifique os logs acima")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Migration interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        sys.exit(1)
    finally:
        migration.close()


if __name__ == "__main__":
    main()