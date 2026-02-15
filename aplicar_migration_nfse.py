#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar migração NFS-e no banco PostgreSQL Railway
Cria tabelas: nfse_config, nfse_baixadas, rps, nsu_nfse, nfse_audit_log
"""
import psycopg2
import os
import sys

def executar_migration():
    """Executa migration_nfse.sql no banco"""
    
    # Obter DATABASE_URL do ambiente
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL não configurada!")
        print("Configure: export DATABASE_URL='postgresql://user:pass@host:port/db'")
        sys.exit(1)
    
    print("=" * 80)
    print("🔧 MIGRAÇÃO: Sistema NFS-e")
    print("=" * 80)
    
    try:
        # Conectar ao banco
        print("\n📡 Conectando ao banco de dados...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        print("✅ Conectado!")
        
        # Ler arquivo SQL
        print("\n📄 Lendo migration_nfse.sql...")
        sql_file = os.path.join(os.path.dirname(__file__), 'migration_nfse.sql')
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"✅ Arquivo lido: {len(sql_content)} caracteres")
        
        # Executar SQL
        print("\n⚙️  Executando migração...")
        cursor.execute(sql_content)
        conn.commit()
        print("✅ Migração executada com sucesso!")
        
        # Verificar tabelas criadas
        print("\n🔍 Verificando tabelas criadas...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('nfse_config', 'nfse_baixadas', 'rps', 'nsu_nfse', 'nfse_certificados', 'nfse_audit_log')
            ORDER BY table_name
        """)
        
        tabelas = cursor.fetchall()
        
        if tabelas:
            print(f"✅ {len(tabelas)} tabelas NFS-e encontradas:")
            for (tabela,) in tabelas:
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                count = cursor.fetchone()[0]
                print(f"   ✓ {tabela}: {count} registros")
        else:
            print("⚠️  Nenhuma tabela NFS-e encontrada!")
        
        # Verificar views
        print("\n🔍 Verificando views criadas...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'vw_nfse%'
            ORDER BY table_name
        """)
        
        views = cursor.fetchall()
        
        if views:
            print(f"✅ {len(views)} views NFS-e encontradas:")
            for (view,) in views:
                print(f"   ✓ {view}")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        print("\n📋 Tabelas criadas:")
        print("   • nfse_config - Configurações de municípios")
        print("   • nfse_baixadas - NFS-e consultadas e baixadas")
        print("   • rps - Recibos Provisórios de Serviços")
        print("   • nsu_nfse - Controle NSU para sincronização")
        print("   • nfse_certificados - Certificados digitais A1")
        print("   • nfse_audit_log - Log de auditoria")
        print("\n📊 Views criadas:")
        print("   • vw_nfse_resumo_empresa")
        print("   • vw_nfse_resumo_mensal")
        print("   • vw_rps_pendentes")
        print("\n🔄 Triggers configurados para atualização automática de timestamps")
        print("\n🚀 Sistema NFS-e pronto para uso!")
        
    except psycopg2.Error as e:
        print(f"\n❌ Erro PostgreSQL: {e}")
        print(f"   Code: {e.pgcode}")
        print(f"   Message: {e.pgerror}")
        sys.exit(1)
        
    except FileNotFoundError:
        print(f"\n❌ Arquivo migration_nfse.sql não encontrado!")
        print(f"   Procurado em: {sql_file}")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    executar_migration()
