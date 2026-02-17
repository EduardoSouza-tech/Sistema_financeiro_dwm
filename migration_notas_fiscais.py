# -*- coding: utf-8 -*-
"""
Migração: Tabelas de Notas Fiscais (NF-e e NFS-e)
Data: 17/02/2026

Cria estrutura para armazenar notas fiscais eletrônicas
e vincular aos lançamentos contábeis e EFD-Contribuições
"""

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

from database_postgresql import get_connection


def criar_tabelas_notas_fiscais():
    """
    Cria tabelas de notas fiscais (NF-e e NFS-e)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        print("🔧 Criando tabelas de notas fiscais...")
        
        # ===== TABELA: notas_fiscais =====
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notas_fiscais (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                
                -- Identificação
                tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('NFE', 'NFSE', 'CTE', 'NFCE')),
                numero VARCHAR(20) NOT NULL,
                serie VARCHAR(10),
                modelo VARCHAR(10),
                chave_acesso VARCHAR(44) UNIQUE,
                
                -- Datas
                data_emissao DATE NOT NULL,
                data_entrada_saida DATE,
                data_competencia DATE,
                
                -- Operação
                direcao VARCHAR(10) NOT NULL CHECK (direcao IN ('ENTRADA', 'SAIDA')),
                natureza_operacao VARCHAR(200),
                cfop VARCHAR(10),
                
                -- Participante
                participante_tipo VARCHAR(20) CHECK (participante_tipo IN ('CLIENTE', 'FORNECEDOR', 'TRANSPORTADOR', 'OUTROS')),
                participante_id INTEGER,
                participante_cnpj_cpf VARCHAR(18),
                participante_nome VARCHAR(200),
                participante_ie VARCHAR(30),
                participante_uf VARCHAR(2),
                participante_municipio VARCHAR(100),
                
                -- Valores totais
                valor_total DECIMAL(15, 2) NOT NULL DEFAULT 0,
                valor_produtos DECIMAL(15, 2) DEFAULT 0,
                valor_servicos DECIMAL(15, 2) DEFAULT 0,
                valor_desconto DECIMAL(15, 2) DEFAULT 0,
                valor_frete DECIMAL(15, 2) DEFAULT 0,
                valor_seguro DECIMAL(15, 2) DEFAULT 0,
                valor_outras_despesas DECIMAL(15, 2) DEFAULT 0,
                
                -- Tributos
                base_calculo_icms DECIMAL(15, 2) DEFAULT 0,
                valor_icms DECIMAL(15, 2) DEFAULT 0,
                base_calculo_icms_st DECIMAL(15, 2) DEFAULT 0,
                valor_icms_st DECIMAL(15, 2) DEFAULT 0,
                valor_ipi DECIMAL(15, 2) DEFAULT 0,
                base_calculo_pis DECIMAL(15, 2) DEFAULT 0,
                valor_pis DECIMAL(15, 2) DEFAULT 0,
                base_calculo_cofins DECIMAL(15, 2) DEFAULT 0,
                valor_cofins DECIMAL(15, 2) DEFAULT 0,
                valor_iss DECIMAL(15, 2) DEFAULT 0,
                
                -- PIS/COFINS Detalhado
                aliquota_pis DECIMAL(8, 4) DEFAULT 0,
                aliquota_cofins DECIMAL(8, 4) DEFAULT 0,
                cst_pis VARCHAR(5),
                cst_cofins VARCHAR(5),
                
                -- Situação
                situacao VARCHAR(20) NOT NULL DEFAULT 'NORMAL' CHECK (situacao IN ('NORMAL', 'CANCELADA', 'DENEGADA', 'INUTILIZADA')),
                data_cancelamento TIMESTAMP,
                motivo_cancelamento TEXT,
                
                -- XML
                xml_completo TEXT,
                xml_importado BOOLEAN DEFAULT FALSE,
                data_importacao TIMESTAMP,
                
                -- Vinculações
                lancamento_contabil_id INTEGER REFERENCES lancamentos_contabeis(id),
                vinculado_contabil BOOLEAN DEFAULT FALSE,
                
                -- Observações
                informacoes_complementares TEXT,
                observacoes TEXT,
                
                -- Controle
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                CONSTRAINT fk_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
                CONSTRAINT uk_nota UNIQUE (empresa_id, tipo, numero, serie)
            );
        """)
        print("  ✅ Tabela notas_fiscais criada")
        
        # ===== TABELA: notas_fiscais_itens =====
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notas_fiscais_itens (
                id SERIAL PRIMARY KEY,
                nota_fiscal_id INTEGER NOT NULL REFERENCES notas_fiscais(id) ON DELETE CASCADE,
                
                -- Identificação
                numero_item INTEGER NOT NULL,
                codigo_produto VARCHAR(100),
                codigo_ean VARCHAR(20),
                codigo_ncm VARCHAR(20),
                descricao TEXT NOT NULL,
                
                -- Quantidade e valores
                quantidade DECIMAL(15, 4) NOT NULL DEFAULT 1,
                unidade VARCHAR(10) NOT NULL DEFAULT 'UN',
                valor_unitario DECIMAL(15, 4) NOT NULL,
                valor_total DECIMAL(15, 2) NOT NULL,
                valor_desconto DECIMAL(15, 2) DEFAULT 0,
                valor_frete DECIMAL(15, 2) DEFAULT 0,
                valor_seguro DECIMAL(15, 2) DEFAULT 0,
                valor_outras_despesas DECIMAL(15, 2) DEFAULT 0,
                
                -- CFOP
                cfop VARCHAR(10),
                
                -- ICMS
                cst_icms VARCHAR(5),
                origem_mercadoria VARCHAR(2),
                base_calculo_icms DECIMAL(15, 2) DEFAULT 0,
                aliquota_icms DECIMAL(8, 4) DEFAULT 0,
                valor_icms DECIMAL(15, 2) DEFAULT 0,
                base_calculo_icms_st DECIMAL(15, 2) DEFAULT 0,
                aliquota_icms_st DECIMAL(8, 4) DEFAULT 0,
                valor_icms_st DECIMAL(15, 2) DEFAULT 0,
                
                -- IPI
                cst_ipi VARCHAR(5),
                base_calculo_ipi DECIMAL(15, 2) DEFAULT 0,
                aliquota_ipi DECIMAL(8, 4) DEFAULT 0,
                valor_ipi DECIMAL(15, 2) DEFAULT 0,
                
                -- PIS
                cst_pis VARCHAR(5),
                base_calculo_pis DECIMAL(15, 2) DEFAULT 0,
                aliquota_pis DECIMAL(8, 4) DEFAULT 0,
                quantidade_pis DECIMAL(15, 4) DEFAULT 0,
                aliquota_pis_reais DECIMAL(15, 4) DEFAULT 0,
                valor_pis DECIMAL(15, 2) DEFAULT 0,
                
                -- COFINS
                cst_cofins VARCHAR(5),
                base_calculo_cofins DECIMAL(15, 2) DEFAULT 0,
                aliquota_cofins DECIMAL(8, 4) DEFAULT 0,
                quantidade_cofins DECIMAL(15, 4) DEFAULT 0,
                aliquota_cofins_reais DECIMAL(15, 4) DEFAULT 0,
                valor_cofins DECIMAL(15, 2) DEFAULT 0,
                
                -- Informações adicionais
                informacoes_adicionais TEXT,
                
                -- Vinculação contábil
                plano_contas_id INTEGER REFERENCES plano_contas(id),
                
                -- Controle
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CONSTRAINT fk_nota_fiscal FOREIGN KEY (nota_fiscal_id) REFERENCES notas_fiscais(id) ON DELETE CASCADE
            );
        """)
        print("  ✅ Tabela notas_fiscais_itens criada")
        
        # ===== TABELA: creditos_tributarios =====
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creditos_tributarios (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                
                -- Período
                mes INTEGER NOT NULL CHECK (mes >= 1 AND mes <= 12),
                ano INTEGER NOT NULL CHECK (ano >= 2000 AND ano <= 2100),
                
                -- Tipo de crédito
                tipo_credito VARCHAR(50) NOT NULL CHECK (tipo_credito IN (
                    'INSUMOS',
                    'ENERGIA',
                    'ALUGUEL',
                    'DEPRECIACAO',
                    'FRETE',
                    'ARMAZENAGEM',
                    'SERVICOS_PJ',
                    'OUTROS'
                )),
                
                -- Tributo
                tributo VARCHAR(10) NOT NULL CHECK (tributo IN ('PIS', 'COFINS')),
                
                -- Documento origem
                nota_fiscal_id INTEGER REFERENCES notas_fiscais(id),
                documento_numero VARCHAR(50),
                documento_data DATE,
                
                -- Valores
                base_calculo DECIMAL(15, 2) NOT NULL,
                aliquota DECIMAL(8, 4) NOT NULL,
                valor_credito DECIMAL(15, 2) NOT NULL,
                
                -- Detalhamento
                descricao TEXT,
                
                -- Situação
                aprovado BOOLEAN DEFAULT TRUE,
                data_aprovacao DATE,
                usuario_aprovacao INTEGER,
                
                -- Utilização
                utilizado BOOLEAN DEFAULT FALSE,
                data_utilizacao DATE,
                periodo_utilizacao VARCHAR(10),
                
                -- Controle
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CONSTRAINT fk_empresa_credito FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
                CONSTRAINT uk_credito UNIQUE (empresa_id, mes, ano, tipo_credito, tributo, nota_fiscal_id)
            );
        """)
        print("  ✅ Tabela creditos_tributarios criada")
        
        # ===== TABELA: operacoes_fiscais (CFOP, CST) =====
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operacoes_fiscais (
                id SERIAL PRIMARY KEY,
                
                -- CFOP
                codigo_cfop VARCHAR(10) UNIQUE NOT NULL,
                descricao_cfop TEXT NOT NULL,
                tipo_operacao VARCHAR(20) CHECK (tipo_operacao IN ('ENTRADA', 'SAIDA')),
                origem VARCHAR(20) CHECK (origem IN ('DENTRO_ESTADO', 'FORA_ESTADO', 'EXTERIOR')),
                
                -- CST PIS/COFINS
                cst_pis_padrao VARCHAR(5),
                cst_cofins_padrao VARCHAR(5),
                
                -- Configurações
                gera_credito_pis BOOLEAN DEFAULT FALSE,
                gera_credito_cofins BOOLEAN DEFAULT FALSE,
                gera_debito_pis BOOLEAN DEFAULT FALSE,
                gera_debito_cofins BOOLEAN DEFAULT FALSE,
                
                -- Alíquotas sugeridas
                aliquota_pis_sugerida DECIMAL(8, 4),
                aliquota_cofins_sugerida DECIMAL(8, 4),
                
                -- Controle
                ativo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("  ✅ Tabela operacoes_fiscais criada")
        
        # ===== ÍNDICES =====
        print("\n🔧 Criando índices...")
        
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_nf_empresa ON notas_fiscais(empresa_id)",
            "CREATE INDEX IF NOT EXISTS idx_nf_tipo ON notas_fiscais(tipo)",
            "CREATE INDEX IF NOT EXISTS idx_nf_emissao ON notas_fiscais(data_emissao)",
            "CREATE INDEX IF NOT EXISTS idx_nf_chave ON notas_fiscais(chave_acesso)",
            "CREATE INDEX IF NOT EXISTS idx_nf_participante ON notas_fiscais(participante_cnpj_cpf)",
            "CREATE INDEX IF NOT EXISTS idx_nf_lancamento ON notas_fiscais(lancamento_contabil_id)",
            
            "CREATE INDEX IF NOT EXISTS idx_nfi_nota ON notas_fiscais_itens(nota_fiscal_id)",
            "CREATE INDEX IF NOT EXISTS idx_nfi_produto ON notas_fiscais_itens(codigo_produto)",
            "CREATE INDEX IF NOT EXISTS idx_nfi_ncm ON notas_fiscais_itens(codigo_ncm)",
            "CREATE INDEX IF NOT EXISTS idx_nfi_cfop ON notas_fiscais_itens(cfop)",
            
            "CREATE INDEX IF NOT EXISTS idx_cred_empresa ON creditos_tributarios(empresa_id)",
            "CREATE INDEX IF NOT EXISTS idx_cred_periodo ON creditos_tributarios(ano, mes)",
            "CREATE INDEX IF NOT EXISTS idx_cred_tipo ON creditos_tributarios(tipo_credito, tributo)",
            "CREATE INDEX IF NOT EXISTS idx_cred_nota ON creditos_tributarios(nota_fiscal_id)",
            "CREATE INDEX IF NOT EXISTS idx_cred_utilizado ON creditos_tributarios(utilizado)",
            
            "CREATE INDEX IF NOT EXISTS idx_opfisc_cfop ON operacoes_fiscais(codigo_cfop)",
            "CREATE INDEX IF NOT EXISTS idx_opfisc_tipo ON operacoes_fiscais(tipo_operacao)"
        ]
        
        for idx_sql in indices:
            cursor.execute(idx_sql)
        
        print(f"  ✅ {len(indices)} índices criados")
        
        # ===== POPULAR CFOP BÁSICOS =====
        print("\n🔧 Populando CFOPs básicos...")
        
        cfops_basicos = [
            # Entradas
            ("1.102", "Compra para comercialização", "ENTRADA", "DENTRO_ESTADO", "50", "50", True, True, False, False),
            ("1.202", "Devolução de venda de mercadoria", "ENTRADA", "DENTRO_ESTADO", None, None, False, False, False, False),
            ("1.253", "Devolução de venda de energia elétrica", "ENTRADA", "DENTRO_ESTADO", "50", "50", True, True, False, False),
            ("1.401", "Compra para industrialização", "ENTRADA", "DENTRO_ESTADO", "50", "50", True, True, False, False),
            ("1.556", "Compra de material para uso/consumo", "ENTRADA", "DENTRO_ESTADO", "50", "50", True, True, False, False),
            ("2.102", "Compra para comercialização", "ENTRADA", "FORA_ESTADO", "50", "50", True, True, False, False),
            ("2.202", "Devolução de venda de mercadoria", "ENTRADA", "FORA_ESTADO", None, None, False, False, False, False),
            ("2.401", "Compra para industrialização", "ENTRADA", "FORA_ESTADO", "50", "50", True, True, False, False),
            ("2.556", "Compra de material para uso/consumo", "ENTRADA", "FORA_ESTADO", "50", "50", True, True, False, False),
            
            # Saídas
            ("5.101", "Venda de produção do estabelecimento", "SAIDA", "DENTRO_ESTADO", "01", "01", False, False, True, True),
            ("5.102", "Venda de mercadoria adquirida", "SAIDA", "DENTRO_ESTADO", "01", "01", False, False, True, True),
            ("5.202", "Devolução de compra para comercialização", "SAIDA", "DENTRO_ESTADO", None, None, False, False, False, False),
            ("5.933", "Prestação de serviços tributados pelo ISSQN", "SAIDA", "DENTRO_ESTADO", "01", "01", False, False, True, True),
            ("6.101", "Venda de produção do estabelecimento", "SAIDA", "FORA_ESTADO", "01", "01", False, False, True, True),
            ("6.102", "Venda de mercadoria adquirida", "SAIDA", "FORA_ESTADO", "01", "01", False, False, True, True),
            ("6.202", "Devolução de compra para comercialização", "SAIDA", "FORA_ESTADO", None, None, False, False, False, False),
            ("6.933", "Prestação de serviços tributados pelo ISSQN", "SAIDA", "FORA_ESTADO", "01", "01", False, False, True, True),
            ("7.102", "Venda para o exterior", "SAIDA", "EXTERIOR", "08", "08", False, False, False, False),
        ]
        
        for cfop in cfops_basicos:
            cursor.execute("""
                INSERT INTO operacoes_fiscais 
                (codigo_cfop, descricao_cfop, tipo_operacao, origem, cst_pis_padrao, cst_cofins_padrao,
                 gera_credito_pis, gera_credito_cofins, gera_debito_pis, gera_debito_cofins)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (codigo_cfop) DO NOTHING
            """, cfop)
        
        print(f"  ✅ {len(cfops_basicos)} CFOPs básicos inseridos")
        
        conn.commit()
        print("\n✅ Migração concluída com sucesso!")
        print("\n📊 Tabelas criadas:")
        print("   - notas_fiscais")
        print("   - notas_fiscais_itens")
        print("   - creditos_tributarios")
        print("   - operacoes_fiscais")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro na migração: {e}")
        raise
        
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("="*80)
    print("MIGRAÇÃO: Tabelas de Notas Fiscais e Créditos Tributários")
    print("="*80)
    print()
    
    try:
        criar_tabelas_notas_fiscais()
        print("\n" + "="*80)
        print("✅ Migração executada com sucesso!")
        print("="*80)
    except Exception as e:
        print("\n" + "="*80)
        print(f"❌ Erro ao executar migração: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()
