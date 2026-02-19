"""
Script para verificar e criar tabelas do Plano de Contas no Railway
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date

# Configuração Railway
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL não encontrada! Configure a variável de ambiente.")
    sys.exit(1)

print(f"🔗 Conectando ao Railway: {DATABASE_URL[:30]}...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("✅ Conectado ao banco Railway!")
    print()
    
    # =============================================================================
    # VERIFICAR SE TABELAS EXISTEM
    # =============================================================================
    
    print("🔍 Verificando tabelas do Plano de Contas...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('plano_contas_versao', 'plano_contas')
        ORDER BY table_name
    """)
    
    tabelas_existentes = [row['table_name'] for row in cursor.fetchall()]
    print(f"📋 Tabelas encontradas: {tabelas_existentes}")
    print()
    
    # =============================================================================
    # CRIAR TABELAS SE NÃO EXISTIREM
    # =============================================================================
    
    tabelas_necessarias = ['plano_contas_versao', 'plano_contas']
    tabelas_faltantes = [t for t in tabelas_necessarias if t not in tabelas_existentes]
    
    if tabelas_faltantes:
        print(f"⚠️ Tabelas faltantes: {tabelas_faltantes}")
        print("🔧 Criando tabelas...")
        
        # Criar plano_contas_versao
        if 'plano_contas_versao' in tabelas_faltantes:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plano_contas_versao (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                    nome_versao VARCHAR(200) NOT NULL,
                    exercicio_fiscal INTEGER NOT NULL,
                    data_inicio DATE,
                    data_fim DATE,
                    is_ativa BOOLEAN DEFAULT FALSE,
                    observacoes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT plano_contas_versao_empresa_id_nome_versao_key 
                        UNIQUE (empresa_id, nome_versao)
                );
                
                CREATE INDEX IF NOT EXISTS idx_plano_contas_versao_empresa 
                    ON plano_contas_versao(empresa_id);
                CREATE INDEX IF NOT EXISTS idx_plano_contas_versao_ativa 
                    ON plano_contas_versao(empresa_id, is_ativa) WHERE is_ativa = TRUE;
                
                -- RLS
                ALTER TABLE plano_contas_versao ENABLE ROW LEVEL SECURITY;
                
                DROP POLICY IF EXISTS plano_contas_versao_tenant_isolation ON plano_contas_versao;
                CREATE POLICY plano_contas_versao_tenant_isolation ON plano_contas_versao
                    USING (empresa_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
            """)
            print("   ✅ Tabela plano_contas_versao criada")
        
        # Criar plano_contas
        if 'plano_contas' in tabelas_faltantes:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plano_contas (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                    versao_id INTEGER NOT NULL REFERENCES plano_contas_versao(id) ON DELETE CASCADE,
                    codigo VARCHAR(50) NOT NULL,
                    descricao VARCHAR(255) NOT NULL,
                    tipo_conta VARCHAR(20) NOT NULL CHECK (tipo_conta IN ('analitica', 'sintetica')),
                    classificacao VARCHAR(50) NOT NULL,
                    natureza VARCHAR(20) NOT NULL CHECK (natureza IN ('devedora', 'credora')),
                    parent_id INTEGER REFERENCES plano_contas(id) ON DELETE SET NULL,
                    nivel INTEGER NOT NULL DEFAULT 1,
                    ordem INTEGER NOT NULL DEFAULT 0,
                    is_bloqueada BOOLEAN DEFAULT FALSE,
                    permite_lancamento BOOLEAN DEFAULT TRUE,
                    requer_centro_custo BOOLEAN DEFAULT FALSE,
                    codigo_speed VARCHAR(50),
                    codigo_referencial VARCHAR(50),
                    natureza_sped VARCHAR(2),
                    observacoes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT plano_contas_versao_codigo_key 
                        UNIQUE (versao_id, codigo)
                );
                
                CREATE INDEX IF NOT EXISTS idx_plano_contas_empresa 
                    ON plano_contas(empresa_id);
                CREATE INDEX IF NOT EXISTS idx_plano_contas_versao 
                    ON plano_contas(versao_id);
                CREATE INDEX IF NOT EXISTS idx_plano_contas_parent 
                    ON plano_contas(parent_id);
                CREATE INDEX IF NOT EXISTS idx_plano_contas_codigo 
                    ON plano_contas(versao_id, codigo);
                
                -- RLS
                ALTER TABLE plano_contas ENABLE ROW LEVEL SECURITY;
                
                DROP POLICY IF EXISTS plano_contas_tenant_isolation ON plano_contas;
                CREATE POLICY plano_contas_tenant_isolation ON plano_contas
                    USING (empresa_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
            """)
            print("   ✅ Tabela plano_contas criada")
        
        conn.commit()
        print("✅ Tabelas criadas com sucesso!")
        print()
    else:
        print("✅ Todas as tabelas já existem!")
        print()
    
    # =============================================================================
    # VERIFICAR DADOS EXISTENTES
    # =============================================================================
    
    print("🔍 Verificando dados existentes...")
    
    # Listar empresas
    cursor.execute("SELECT id, razao_social FROM empresas ORDER BY id")
    empresas = cursor.fetchall()
    print(f"📊 Total de empresas: {len(empresas)}")
    for emp in empresas:
        print(f"   • ID {emp['id']}: {emp['razao_social']}")
    print()
    
    # Verificar versões por empresa
    for empresa in empresas:
        cursor.execute("""
            SELECT id, nome_versao, exercicio_fiscal, is_ativa, created_at
            FROM plano_contas_versao
            WHERE empresa_id = %s
            ORDER BY exercicio_fiscal DESC, created_at DESC
        """, (empresa['id'],))
        
        versoes = cursor.fetchall()
        print(f"📋 Empresa {empresa['id']} ({empresa['razao_social']}): {len(versoes)} versão(ões)")
        
        if versoes:
            for v in versoes:
                ativa = "⭐ ATIVA" if v['is_ativa'] else ""
                print(f"   • ID {v['id']}: {v['nome_versao']} ({v['exercicio_fiscal']}) {ativa}")
                
                # Contar contas desta versão
                cursor.execute("""
                    SELECT COUNT(*) as total,
                           COUNT(*) FILTER (WHERE tipo_conta = 'sintetica') as sinteticas,
                           COUNT(*) FILTER (WHERE tipo_conta = 'analitica') as analiticas
                    FROM plano_contas
                    WHERE versao_id = %s
                """, (v['id'],))
                stats = cursor.fetchone()
                print(f"     └─ Contas: {stats['total']} ({stats['sinteticas']} sintéticas, {stats['analiticas']} analíticas)")
        else:
            print(f"   ⚠️ NENHUMA VERSÃO ENCONTRADA")
        print()
    
    # =============================================================================
    # APLICAR PLANO PADRÃO SE NECESSÁRIO
    # =============================================================================
    
    print("🔍 Verificando empresas sem plano de contas...")
    empresas_sem_plano = []
    
    for empresa in empresas:
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM plano_contas_versao
            WHERE empresa_id = %s
        """, (empresa['id'],))
        
        if cursor.fetchone()['total'] == 0:
            empresas_sem_plano.append(empresa)
    
    if empresas_sem_plano:
        print(f"⚠️ {len(empresas_sem_plano)} empresa(s) sem plano de contas:")
        for emp in empresas_sem_plano:
            print(f"   • ID {emp['id']}: {emp['razao_social']}")
        
        resposta = input("\n❓ Deseja aplicar o plano de contas padrão nessas empresas? (s/n): ").lower()
        
        if resposta == 's':
            print("\n🚀 Aplicando plano de contas padrão...")
            
            # Importar função de aplicação
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from contabilidade_functions import importar_plano_padrao
            
            for empresa in empresas_sem_plano:
                print(f"\n📦 Aplicando para empresa {empresa['id']} ({empresa['razao_social']})...")
                try:
                    resultado = importar_plano_padrao(empresa['id'], ano_fiscal=2026)
                    if resultado.get('success'):
                        print(f"   ✅ {resultado.get('contas_criadas', 0)} contas criadas")
                        print(f"   📋 Versão ID: {resultado.get('versao_id')}")
                    else:
                        print(f"   ❌ Erro: {resultado.get('error')}")
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
            
            print("\n✅ Aplicação concluída!")
        else:
            print("⏭️ Pulando aplicação automática")
    else:
        print("✅ Todas as empresas já possuem plano de contas!")
    
    print()
    print("="*80)
    print("✅ VERIFICAÇÃO COMPLETA!")
    print("="*80)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
