"""
Migration: Adicionar índices de performance
Cria índices em foreign keys e campos comuns de filtro para otimizar queries
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração do banco
DATABASE_URL = os.getenv('DATABASE_URL')

def create_indexes():
    """Cria índices para melhorar performance"""
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("🔧 Iniciando criação de índices de performance...")
    
    # Índices a criar
    indexes = [
        # LANCAMENTOS - Tabela mais consultada
        {
            'name': 'idx_lancamentos_empresa_id',
            'table': 'lancamentos',
            'columns': 'empresa_id',
            'description': 'Filtro por empresa (multi-tenancy)'
        },
        {
            'name': 'idx_lancamentos_data_lancamento',
            'table': 'lancamentos',
            'columns': 'data_lancamento',
            'description': 'Filtro por data em relatórios'
        },
        {
            'name': 'idx_lancamentos_data_vencimento',
            'table': 'lancamentos',
            'columns': 'data_vencimento',
            'description': 'Filtro para inadimplência'
        },
        {
            'name': 'idx_lancamentos_status',
            'table': 'lancamentos',
            'columns': 'status',
            'description': 'Filtro por status (pago/pendente)'
        },
        {
            'name': 'idx_lancamentos_tipo',
            'table': 'lancamentos',
            'columns': 'tipo',
            'description': 'Filtro por tipo (receita/despesa)'
        },
        {
            'name': 'idx_lancamentos_conta_id',
            'table': 'lancamentos',
            'columns': 'conta_id',
            'description': 'Foreign key para contas'
        },
        {
            'name': 'idx_lancamentos_categoria_id',
            'table': 'lancamentos',
            'columns': 'categoria_id',
            'description': 'Foreign key para categorias'
        },
        {
            'name': 'idx_lancamentos_empresa_data',
            'table': 'lancamentos',
            'columns': 'empresa_id, data_lancamento DESC',
            'description': 'Índice composto para queries comuns'
        },
        {
            'name': 'idx_lancamentos_empresa_status',
            'table': 'lancamentos',
            'columns': 'empresa_id, status',
            'description': 'Índice composto para filtros de status por empresa'
        },
        
        # CONTRATOS
        {
            'name': 'idx_contratos_empresa_id',
            'table': 'contratos',
            'columns': 'empresa_id',
            'description': 'Filtro por empresa'
        },
        {
            'name': 'idx_contratos_cliente_id',
            'table': 'contratos',
            'columns': 'cliente_id',
            'description': 'Foreign key para clientes'
        },
        {
            'name': 'idx_contratos_data_inicio',
            'table': 'contratos',
            'columns': 'data_inicio',
            'description': 'Filtro por data de início'
        },
        {
            'name': 'idx_contratos_status',
            'table': 'contratos',
            'columns': 'status',
            'description': 'Filtro por status (ativo/inativo)'
        },
        {
            'name': 'idx_contratos_numero',
            'table': 'contratos',
            'columns': 'numero',
            'description': 'Lookup por número único'
        },
        
        # SESSOES
        {
            'name': 'idx_sessoes_empresa_id',
            'table': 'sessoes',
            'columns': 'empresa_id',
            'description': 'Filtro por empresa'
        },
        {
            'name': 'idx_sessoes_contrato_id',
            'table': 'sessoes',
            'columns': 'contrato_id',
            'description': 'Foreign key para contratos'
        },
        {
            'name': 'idx_sessoes_cliente_id',
            'table': 'sessoes',
            'columns': 'cliente_id',
            'description': 'Foreign key para clientes'
        },
        {
            'name': 'idx_sessoes_data_sessao',
            'table': 'sessoes',
            'columns': 'data_sessao',
            'description': 'Filtro por data'
        },
        
        # KITS
        {
            'name': 'idx_kits_empresa_id',
            'table': 'kits',
            'columns': 'empresa_id',
            'description': 'Filtro por empresa'
        },
        {
            'name': 'idx_kits_ativo',
            'table': 'kits',
            'columns': 'ativo',
            'description': 'Filtro por status ativo'
        },
        
        # CLIENTES (Parceiros)
        {
            'name': 'idx_clientes_empresa_id',
            'table': 'clientes',
            'columns': 'empresa_id',
            'description': 'Filtro por empresa'
        },
        {
            'name': 'idx_clientes_tipo',
            'table': 'clientes',
            'columns': 'tipo',
            'description': 'Filtro por tipo (cliente/fornecedor)'
        },
        {
            'name': 'idx_clientes_documento',
            'table': 'clientes',
            'columns': 'documento',
            'description': 'Lookup por CPF/CNPJ'
        },
        
        # CONTAS
        {
            'name': 'idx_contas_empresa_id',
            'table': 'contas',
            'columns': 'empresa_id',
            'description': 'Filtro por empresa'
        },
        {
            'name': 'idx_contas_ativa',
            'table': 'contas',
            'columns': 'ativa',
            'description': 'Filtro por contas ativas'
        },
        
        # CATEGORIAS
        {
            'name': 'idx_categorias_empresa_id',
            'table': 'categorias',
            'columns': 'empresa_id',
            'description': 'Filtro por empresa'
        },
        {
            'name': 'idx_categorias_tipo',
            'table': 'categorias',
            'columns': 'tipo',
            'description': 'Filtro por tipo'
        },
        
        # SUBCATEGORIAS
        {
            'name': 'idx_subcategorias_categoria_id',
            'table': 'subcategorias',
            'columns': 'categoria_id',
            'description': 'Foreign key para categorias'
        },
        
        # FUNCIONARIOS
        {
            'name': 'idx_funcionarios_empresa_id',
            'table': 'funcionarios',
            'columns': 'empresa_id',
            'description': 'Filtro por empresa'
        },
        {
            'name': 'idx_funcionarios_cpf',
            'table': 'funcionarios',
            'columns': 'cpf',
            'description': 'Lookup por CPF'
        },
        
        # EVENTOS
        {
            'name': 'idx_eventos_empresa_id',
            'table': 'eventos',
            'columns': 'empresa_id',
            'description': 'Filtro por empresa'
        },
        {
            'name': 'idx_eventos_data_evento',
            'table': 'eventos',
            'columns': 'data_evento',
            'description': 'Filtro por data'
        },
    ]
    
    created = 0
    skipped = 0
    errors = 0
    
    for idx in indexes:
        try:
            # Verificar se índice já existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = %s
                )
            """, (idx['name'],))
            
            exists = cursor.fetchone()[0]
            
            if exists:
                print(f"⏭️  Índice {idx['name']} já existe")
                skipped += 1
                continue
            
            # Criar índice
            sql = f"CREATE INDEX {idx['name']} ON {idx['table']} ({idx['columns']})"
            cursor.execute(sql)
            conn.commit()
            
            print(f"✅ Criado: {idx['name']} - {idx['description']}")
            created += 1
            
        except Exception as e:
            print(f"❌ Erro ao criar {idx['name']}: {str(e)}")
            conn.rollback()
            errors += 1
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print(f"📊 Resumo:")
    print(f"   ✅ Criados: {created}")
    print(f"   ⏭️  Já existiam: {skipped}")
    print(f"   ❌ Erros: {errors}")
    print("="*60)
    
    return created, skipped, errors


def analyze_tables():
    """Atualiza estatísticas do PostgreSQL para melhorar planos de execução"""
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("\n🔍 Atualizando estatísticas das tabelas...")
    
    tables = [
        'lancamentos', 'contratos', 'sessoes', 'kits', 'clientes',
        'contas', 'categorias', 'subcategorias', 'funcionarios', 'eventos'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"ANALYZE {table}")
            conn.commit()
            print(f"✅ {table}: estatísticas atualizadas")
        except Exception as e:
            print(f"⚠️  {table}: {str(e)}")
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    print("✅ Análise concluída")


if __name__ == '__main__':
    print("🚀 MIGRATION: Performance Indexes")
    print("="*60)
    
    created, skipped, errors = create_indexes()
    
    if created > 0:
        analyze_tables()
    
    print("\n🎉 Migration concluída!")
    print(f"   Total de índices processados: {created + skipped + errors}")
