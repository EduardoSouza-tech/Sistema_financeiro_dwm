"""
MIGRAÇÃO COMPLETA: Sistema Multi-Tenant SaaS
===========================================

Converte o sistema de multi-tenancy baseado em usuário (errado)
para multi-tenancy baseado em EMPRESA (correto).

MODELO ANTIGO (ERRADO):
- Dados pertenciam ao usuário (proprietario_id)
- 1 usuário = 1 tenant

MODELO NOVO (CORRETO):
- 1 EMPRESA = 1 tenant
- 1 empresa tem N usuários
- Dados pertencem à empresa

ESTRUTURA:
1. Criar tabela 'empresas'
2. Adicionar empresa_id em 'usuarios'
3. Renomear proprietario_id → empresa_id em todas tabelas
4. Criar empresa padrão e migrar dados existentes
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def conectar_banco():
    """Conecta ao banco de dados"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise Exception("DATABASE_URL não configurada")
    
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    return psycopg2.connect(DATABASE_URL)


def criar_tabela_empresas(cursor):
    """
    Cria a tabela de empresas (tenants)
    """
    print("\n📋 ETAPA 1: Criando tabela EMPRESAS...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id SERIAL PRIMARY KEY,
            
            -- Dados da Empresa
            razao_social VARCHAR(200) NOT NULL,
            nome_fantasia VARCHAR(200),
            cnpj VARCHAR(18) UNIQUE,
            
            -- Contato
            email VARCHAR(100) NOT NULL UNIQUE,
            telefone VARCHAR(20),
            whatsapp VARCHAR(20),
            site VARCHAR(200),
            
            -- Endereço
            endereco TEXT,
            cidade VARCHAR(100),
            estado VARCHAR(2),
            cep VARCHAR(10),
            
            -- Plano e Limites
            plano VARCHAR(50) DEFAULT 'basico',  -- basico, profissional, empresarial
            max_usuarios INTEGER DEFAULT 5,
            max_clientes INTEGER DEFAULT 100,
            max_lancamentos_mes INTEGER DEFAULT 500,
            espaco_storage_mb INTEGER DEFAULT 1024,
            
            -- Status
            ativo BOOLEAN DEFAULT true,
            data_ativacao TIMESTAMP DEFAULT NOW(),
            data_suspensao TIMESTAMP,
            motivo_suspensao TEXT,
            
            -- Auditoria
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            created_by INTEGER,
            
            -- Metadados
            configuracoes JSONB DEFAULT '{}',
            observacoes TEXT
        );
    """)
    
    # Índices
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_empresas_cnpj ON empresas(cnpj);
        CREATE INDEX IF NOT EXISTS idx_empresas_email ON empresas(email);
        CREATE INDEX IF NOT EXISTS idx_empresas_ativo ON empresas(ativo);
    """)
    
    print("   ✅ Tabela 'empresas' criada com sucesso")


def adicionar_empresa_id_usuarios(cursor):
    """
    Adiciona empresa_id na tabela usuarios
    """
    print("\n👥 ETAPA 2: Adicionando empresa_id em USUARIOS...")
    
    # Verificar se já existe
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'usuarios' 
        AND column_name = 'empresa_id'
    """)
    
    if cursor.fetchone():
        print("   ✓ Coluna empresa_id já existe em usuarios")
        return
    
    # Adicionar coluna (temporariamente nullable para migração)
    cursor.execute("""
        ALTER TABLE usuarios 
        ADD COLUMN IF NOT EXISTS empresa_id INTEGER 
        REFERENCES empresas(id) ON DELETE CASCADE;
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_usuarios_empresa 
        ON usuarios(empresa_id);
    """)
    
    print("   ✅ Coluna empresa_id adicionada em usuarios")


def criar_empresa_padrao_e_migrar(cursor, conn):
    """
    Cria empresa padrão e migra usuários existentes
    """
    print("\n🏢 ETAPA 3: Criando empresa padrão e migrando dados...")
    
    # Verificar se já existe empresa
    cursor.execute("SELECT COUNT(*) FROM empresas")
    if cursor.fetchone()[0] > 0:
        print("   ✓ Empresas já existem, pulando criação")
        return
    
    # Criar empresa padrão
    cursor.execute("""
        INSERT INTO empresas (
            razao_social, 
            nome_fantasia, 
            email, 
            plano,
            max_usuarios,
            max_clientes,
            observacoes
        ) VALUES (
            'Empresa Principal',
            'Sistema Financeiro',
            'admin@sistema.local',
            'empresarial',
            999,
            9999,
            'Empresa padrão criada na migração'
        )
        RETURNING id;
    """)
    
    empresa_id = cursor.fetchone()[0]
    print(f"   ✅ Empresa padrão criada (ID: {empresa_id})")
    
    # Migrar todos os usuários para a empresa padrão
    cursor.execute("""
        UPDATE usuarios 
        SET empresa_id = %s 
        WHERE empresa_id IS NULL
    """, (empresa_id,))
    
    usuarios_migrados = cursor.rowcount
    print(f"   ✅ {usuarios_migrados} usuários migrados para empresa padrão")
    
    conn.commit()


def renomear_proprietario_para_empresa(cursor, conn):
    """
    Renomeia proprietario_id para empresa_id em todas as tabelas
    """
    print("\n🔄 ETAPA 4: Renomeando proprietario_id → empresa_id...")
    
    tabelas_com_proprietario = [
        'categorias',
        'clientes',
        'contas_bancarias',
        'fornecedores',
        'lancamentos',
        'contratos',
        'sessoes',
        'comissoes',
        'contrato_comissoes',
        'estoque_produtos',
        'estoque_movimentacoes',
        'produtos',
        'kits',
        'kits_equipamentos',
        'templates_equipe',
        'tags',
        'tags_trabalho',
        'tipos_sessao',
        'agenda',
        'agenda_fotografia'
    ]
    
    for tabela in tabelas_com_proprietario:
        try:
            # Verificar se proprietario_id existe
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{tabela}' 
                AND column_name = 'proprietario_id'
            """)
            
            if not cursor.fetchone():
                # Verificar se empresa_id já existe
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{tabela}' 
                    AND column_name = 'empresa_id'
                """)
                
                if cursor.fetchone():
                    print(f"   ✓ {tabela.ljust(25)} - empresa_id já existe")
                else:
                    # Criar empresa_id do zero
                    cursor.execute(f"""
                        ALTER TABLE {tabela} 
                        ADD COLUMN empresa_id INTEGER 
                        REFERENCES empresas(id) ON DELETE CASCADE
                    """)
                    
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_{tabela}_empresa 
                        ON {tabela}(empresa_id)
                    """)
                    
                    print(f"   ✅ {tabela.ljust(25)} - empresa_id CRIADO")
                continue
            
            # Dropar constraint antiga se existir
            cursor.execute(f"""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = '{tabela}' 
                AND constraint_name LIKE '%proprietario%'
            """)
            
            constraints = cursor.fetchall()
            for constraint in constraints:
                cursor.execute(f"""
                    ALTER TABLE {tabela} 
                    DROP CONSTRAINT IF EXISTS {constraint[0]}
                """)
            
            # Renomear coluna
            cursor.execute(f"""
                ALTER TABLE {tabela} 
                RENAME COLUMN proprietario_id TO empresa_id
            """)
            
            # Adicionar nova foreign key
            cursor.execute(f"""
                ALTER TABLE {tabela} 
                ADD CONSTRAINT fk_{tabela}_empresa 
                FOREIGN KEY (empresa_id) 
                REFERENCES empresas(id) 
                ON DELETE CASCADE
            """)
            
            # Criar índice
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{tabela}_empresa 
                ON {tabela}(empresa_id)
            """)
            
            conn.commit()
            print(f"   ✅ {tabela.ljust(25)} - proprietario_id → empresa_id")
            
        except Exception as e:
            conn.rollback()
            print(f"   ⚠️  {tabela.ljust(25)} - Erro: {str(e)[:50]}")


def atualizar_dados_empresa_padrao(cursor, conn):
    """
    Atualiza todos os registros sem empresa_id para a empresa padrão
    """
    print("\n📊 ETAPA 5: Populando empresa_id em registros órfãos...")
    
    # Pegar ID da primeira empresa
    cursor.execute("SELECT id FROM empresas ORDER BY id LIMIT 1")
    resultado = cursor.fetchone()
    
    if not resultado:
        print("   ⚠️  Nenhuma empresa encontrada")
        return
    
    empresa_id = resultado[0]
    
    tabelas = [
        'categorias', 'clientes', 'contas_bancarias', 'fornecedores', 
        'lancamentos', 'contratos', 'sessoes', 'comissoes',
        'contrato_comissoes', 'estoque_produtos', 'estoque_movimentacoes',
        'produtos', 'kits', 'kits_equipamentos', 'templates_equipe',
        'tags', 'tags_trabalho', 'tipos_sessao', 'agenda', 'agenda_fotografia'
    ]
    
    total_atualizados = 0
    
    for tabela in tabelas:
        try:
            cursor.execute(f"""
                UPDATE {tabela} 
                SET empresa_id = %s 
                WHERE empresa_id IS NULL
            """, (empresa_id,))
            
            count = cursor.rowcount
            if count > 0:
                print(f"   ✅ {tabela.ljust(25)} - {count} registros atualizados")
                total_atualizados += count
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"   ⚠️  {tabela.ljust(25)} - {str(e)[:40]}")
    
    print(f"\n   📊 Total: {total_atualizados} registros atualizados")


def tornar_empresa_id_obrigatorio(cursor, conn):
    """
    Torna empresa_id NOT NULL após migração
    """
    print("\n🔒 ETAPA 6: Tornando empresa_id obrigatório...")
    
    tabelas = [
        'usuarios', 'categorias', 'clientes', 'contas_bancarias', 
        'fornecedores', 'lancamentos'
    ]
    
    for tabela in tabelas:
        try:
            cursor.execute(f"""
                ALTER TABLE {tabela} 
                ALTER COLUMN empresa_id SET NOT NULL
            """)
            
            conn.commit()
            print(f"   ✅ {tabela.ljust(25)} - empresa_id NOT NULL")
            
        except Exception as e:
            conn.rollback()
            print(f"   ⚠️  {tabela.ljust(25)} - {str(e)[:40]}")


def verificar_migracao(cursor):
    """
    Verifica o resultado da migração
    """
    print("\n" + "="*70)
    print("📊 VERIFICAÇÃO FINAL")
    print("="*70)
    
    # Contar empresas
    cursor.execute("SELECT COUNT(*) FROM empresas")
    total_empresas = cursor.fetchone()[0]
    print(f"\n✅ Empresas cadastradas: {total_empresas}")
    
    # Contar usuários por empresa
    cursor.execute("""
        SELECT e.razao_social, COUNT(u.id) as total_usuarios
        FROM empresas e
        LEFT JOIN usuarios u ON u.empresa_id = e.id
        GROUP BY e.id, e.razao_social
    """)
    
    print("\n👥 Usuários por empresa:")
    for row in cursor.fetchall():
        print(f"   • {row[0]}: {row[1]} usuários")
    
    # Listar tabelas com empresa_id
    cursor.execute("""
        SELECT DISTINCT table_name
        FROM information_schema.columns
        WHERE column_name = 'empresa_id'
        AND table_schema = 'public'
        ORDER BY table_name
    """)
    
    tabelas = [row[0] for row in cursor.fetchall()]
    print(f"\n📋 Tabelas com empresa_id ({len(tabelas)}):")
    for tabela in tabelas:
        print(f"   • {tabela}")
    
    print("\n" + "="*70)


def executar_migracao_completa():
    """
    Executa todas as etapas da migração
    """
    print("\n" + "="*70)
    print("🚀 MIGRAÇÃO MULTI-TENANT SAAS")
    print("="*70)
    print("Convertendo sistema para arquitetura baseada em EMPRESAS")
    print("="*70)
    
    conn = None
    cursor = None
    
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        
        # Etapa 1: Criar tabela empresas
        criar_tabela_empresas(cursor)
        conn.commit()
        
        # Etapa 2: Adicionar empresa_id em usuarios
        adicionar_empresa_id_usuarios(cursor)
        conn.commit()
        
        # Etapa 3: Criar empresa padrão
        criar_empresa_padrao_e_migrar(cursor, conn)
        
        # Etapa 4: Renomear proprietario_id → empresa_id
        renomear_proprietario_para_empresa(cursor, conn)
        
        # Etapa 5: Popular empresa_id em órfãos
        atualizar_dados_empresa_padrao(cursor, conn)
        
        # Etapa 6: Tornar NOT NULL
        tornar_empresa_id_obrigatorio(cursor, conn)
        
        # Verificação final
        verificar_migracao(cursor)
        
        print("\n✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA MIGRAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == '__main__':
    executar_migracao_completa()
