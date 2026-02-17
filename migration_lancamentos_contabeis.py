#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIGRATION: Criar estrutura de Lançamentos Contábeis
FASE 2 - Speed Integration
Data: 17/02/2026

Cria tabelas para lançamentos contábeis com partidas dobradas:
- lancamentos_contabeis (cabeçalho do lançamento)
- lancamentos_contabeis_itens (débitos e créditos)
"""

import psycopg2
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def executar_migration():
    """Executa a migration de criação de lançamentos contábeis"""
    
    conn = None
    try:
        print("🔄 Conectando ao banco de dados...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("\n📋 MIGRATION: Criação de Lançamentos Contábeis")
        print("=" * 70)
        
        # ===================================================================
        # 1. CRIAR TABELA lancamentos_contabeis (CABEÇALHO)
        # ===================================================================
        print("\n1️⃣ Criando tabela 'lancamentos_contabeis'...")
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos_contabeis (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                versao_plano_id INTEGER REFERENCES plano_contas_versao(id) ON DELETE SET NULL,
                numero_lancamento VARCHAR(20),
                data_lancamento DATE NOT NULL,
                historico TEXT,
                tipo_lancamento VARCHAR(20) DEFAULT 'manual', -- 'manual', 'automatico', 'importado'
                origem VARCHAR(50), -- 'conta_pagar', 'conta_receber', 'nfse', 'manual', etc
                origem_id INTEGER, -- ID da transação que gerou o lançamento
                valor_total DECIMAL(15,2) NOT NULL DEFAULT 0,
                is_estornado BOOLEAN DEFAULT FALSE,
                lancamento_estorno_id INTEGER REFERENCES lancamentos_contabeis(id),
                observacoes TEXT,
                created_by INTEGER REFERENCES usuarios(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
            );
        """)
        print("   ✅ Tabela 'lancamentos_contabeis' criada!")
        
        # ===================================================================
        # 2. CRIAR TABELA lancamentos_contabeis_itens (DÉBITOS/CRÉDITOS)
        # ===================================================================
        print("\n2️⃣ Criando tabela 'lancamentos_contabeis_itens'...")
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos_contabeis_itens (
                id SERIAL PRIMARY KEY,
                lancamento_id INTEGER NOT NULL REFERENCES lancamentos_contabeis(id) ON DELETE CASCADE,
                plano_contas_id INTEGER NOT NULL REFERENCES plano_contas(id) ON DELETE RESTRICT,
                tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('debito', 'credito')),
                valor DECIMAL(15,2) NOT NULL CHECK (valor > 0),
                historico_complementar TEXT,
                centro_custo VARCHAR(100), -- Nome do centro de custo (texto livre por enquanto)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_lancamento FOREIGN KEY (lancamento_id) REFERENCES lancamentos_contabeis(id) ON DELETE CASCADE,
                CONSTRAINT fk_plano_contas FOREIGN KEY (plano_contas_id) REFERENCES plano_contas(id) ON DELETE RESTRICT
            );
        """)
        print("   ✅ Tabela 'lancamentos_contabeis_itens' criada!")
        
        # ===================================================================
        # 3. CRIAR ÍNDICES PARA PERFORMANCE
        # ===================================================================
        print("\n3️⃣ Criando índices de performance...")
        
        indices = [
            ("idx_lancamentos_empresa", "lancamentos_contabeis", "empresa_id"),
            ("idx_lancamentos_data", "lancamentos_contabeis", "data_lancamento"),
            ("idx_lancamentos_tipo", "lancamentos_contabeis", "tipo_lancamento"),
            ("idx_lancamentos_origem", "lancamentos_contabeis", "origem, origem_id"),
            ("idx_lancamentos_numero", "lancamentos_contabeis", "numero_lancamento"),
            ("idx_lancamentos_itens_lancamento", "lancamentos_contabeis_itens", "lancamento_id"),
            ("idx_lancamentos_itens_conta", "lancamentos_contabeis_itens", "plano_contas_id"),
            ("idx_lancamentos_itens_tipo", "lancamentos_contabeis_itens", "tipo"),
        ]
        
        for idx_name, table_name, columns in indices:
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} 
                ON {table_name} ({columns});
            """)
            print(f"   ✅ Índice '{idx_name}' criado em {table_name}({columns})")
        
        # ===================================================================
        # 4. ADICIONAR COMENTÁRIOS NAS TABELAS
        # ===================================================================
        print("\n4️⃣ Adicionando comentários nas tabelas...")
        
        cur.execute("""
            COMMENT ON TABLE lancamentos_contabeis IS 
            'Cabeçalho dos lançamentos contábeis - Speed Integration FASE 2';
            
            COMMENT ON COLUMN lancamentos_contabeis.numero_lancamento IS 
            'Número sequencial do lançamento contábil (gerado automaticamente)';
            
            COMMENT ON COLUMN lancamentos_contabeis.tipo_lancamento IS 
            'Tipo: manual (inserido pelo usuário), automatico (gerado pelo sistema), importado (do Speed)';
            
            COMMENT ON COLUMN lancamentos_contabeis.origem IS 
            'Origem do lançamento: conta_pagar, conta_receber, nfse, manual, estorno, etc';
            
            COMMENT ON COLUMN lancamentos_contabeis.origem_id IS 
            'ID da transação que originou o lançamento (ex: id da conta a pagar)';
            
            COMMENT ON TABLE lancamentos_contabeis_itens IS 
            'Itens do lançamento contábil - débitos e créditos (partidas dobradas)';
            
            COMMENT ON COLUMN lancamentos_contabeis_itens.tipo IS 
            'Tipo de lançamento: debito ou credito';
        """)
        print("   ✅ Comentários adicionados!")
        
        # ===================================================================
        # 5. CRIAR SEQUÊNCIA PARA NUMERAÇÃO DE LANÇAMENTOS
        # ===================================================================
        print("\n5️⃣ Criando sequência para numeração automática...")
        
        cur.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_numero_lancamento
            START WITH 1
            INCREMENT BY 1
            NO MAXVALUE
            CACHE 1;
        """)
        print("   ✅ Sequência 'seq_numero_lancamento' criada!")
        
        # ===================================================================
        # 6. CRIAR FUNÇÃO PARA VALIDAR PARTIDAS DOBRADAS
        # ===================================================================
        print("\n6️⃣ Criando função de validação de partidas dobradas...")
        
        cur.execute("""
            CREATE OR REPLACE FUNCTION validar_partidas_dobradas()
            RETURNS TRIGGER AS $$
            DECLARE
                v_total_debito DECIMAL(15,2);
                v_total_credito DECIMAL(15,2);
            BEGIN
                -- Calcula totais de débito e crédito
                SELECT 
                    COALESCE(SUM(CASE WHEN tipo = 'debito' THEN valor ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN tipo = 'credito' THEN valor ELSE 0 END), 0)
                INTO v_total_debito, v_total_credito
                FROM lancamentos_contabeis_itens
                WHERE lancamento_id = NEW.lancamento_id;
                
                -- Verifica se estão balanceados
                IF v_total_debito != v_total_credito THEN
                    RAISE EXCEPTION 'Partidas não estão dobradas! Débito: %, Crédito: %', 
                        v_total_debito, v_total_credito;
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        print("   ✅ Função 'validar_partidas_dobradas' criada!")
        
        # ===================================================================
        # 7. CRIAR TRIGGER PARA VALIDAÇÃO AUTOMÁTICA
        # ===================================================================
        print("\n7️⃣ Criando trigger de validação...")
        
        cur.execute("""
            DROP TRIGGER IF EXISTS trg_validar_partidas 
            ON lancamentos_contabeis_itens;
            
            CREATE TRIGGER trg_validar_partidas
            AFTER INSERT OR UPDATE ON lancamentos_contabeis_itens
            FOR EACH ROW
            EXECUTE FUNCTION validar_partidas_dobradas();
        """)
        print("   ✅ Trigger 'trg_validar_partidas' criado!")
        
        # ===================================================================
        # 8. CRIAR VIEW PARA CONSULTA DE LANÇAMENTOS COMPLETOS
        # ===================================================================
        print("\n8️⃣ Criando view de lançamentos completos...")
        
        cur.execute("""
            CREATE OR REPLACE VIEW vw_lancamentos_completos AS
            SELECT 
                lc.id AS lancamento_id,
                lc.empresa_id,
                lc.numero_lancamento,
                lc.data_lancamento,
                lc.historico,
                lc.tipo_lancamento,
                lc.origem,
                lc.origem_id,
                lc.valor_total,
                lc.is_estornado,
                lc.created_at,
                lci.id AS item_id,
                lci.tipo AS item_tipo,
                lci.valor AS item_valor,
                lci.historico_complementar,
                lci.centro_custo,
                pc.codigo AS conta_codigo,
                pc.descricao AS conta_nome,
                pc.classificacao AS conta_classificacao,
                u.username AS criado_por
            FROM lancamentos_contabeis lc
            INNER JOIN lancamentos_contabeis_itens lci ON lci.lancamento_id = lc.id
            INNER JOIN plano_contas pc ON pc.id = lci.plano_contas_id
            LEFT JOIN usuarios u ON u.id = lc.created_by
            ORDER BY lc.data_lancamento DESC, lc.numero_lancamento, lci.id;
        """)
        print("   ✅ View 'vw_lancamentos_completos' criada!")
        
        # ===================================================================
        # COMMIT
        # ===================================================================
        conn.commit()
        
        print("\n" + "=" * 70)
        print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
        print("=" * 70)
        print("\n📊 Estrutura criada:")
        print("   ✓ Tabela lancamentos_contabeis")
        print("   ✓ Tabela lancamentos_contabeis_itens")
        print("   ✓ 9 índices de performance")
        print("   ✓ Sequência para numeração automática")
        print("   ✓ Função de validação de partidas dobradas")
        print("   ✓ Trigger de validação automática")
        print("   ✓ View vw_lancamentos_completos")
        print("\n🚀 Sistema pronto para registrar lançamentos contábeis!")
        
        return True
        
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print(f"\n❌ ERRO NO BANCO DE DADOS:")
        print(f"   Código: {e.pgcode}")
        print(f"   Mensagem: {e.pgerror}")
        return False
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"\n❌ ERRO INESPERADO: {str(e)}")
        return False
        
    finally:
        if conn:
            cur.close()
            conn.close()
            print("\n🔌 Conexão com o banco encerrada.")


if __name__ == '__main__':
    print("🚀 INICIANDO MIGRATION - LANÇAMENTOS CONTÁBEIS")
    print("📅 Data: 17/02/2026")
    print("🎯 FASE 2 - Speed Integration\n")
    
    sucesso = executar_migration()
    
    if sucesso:
        print("\n✅ Migration executada com sucesso!")
        exit(0)
    else:
        print("\n❌ Migration falhou. Verifique os erros acima.")
        exit(1)
