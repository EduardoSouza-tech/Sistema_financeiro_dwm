#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Importador de Funcionários - coop.xlsx
Importa planilha Excel para a tabela funcionarios no PostgreSQL Railway
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import os
import sys

# Forçar UTF-8 no Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configurações do banco Railway
DB_CONFIG = {
    'host': 'centerbeam.proxy.rlwy.net',
    'port': 12659,
    'database': 'railway',
    'user': 'postgres',
    'password': 'JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT'
}

def conectar_banco():
    """Conecta ao banco PostgreSQL Railway"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conectado ao banco Railway com sucesso!")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        sys.exit(1)

def aplicar_migration(conn):
    """Aplica migration para adicionar campos novos"""
    try:
        cursor = conn.cursor()
        
        print("\n📝 Aplicando migration...")
        
        # Ler arquivo de migration
        with open('migration_funcionarios_completo.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        cursor.execute(migration_sql)
        conn.commit()
        
        print("✅ Migration aplicada com sucesso!")
        cursor.close()
        
    except Exception as e:
        print(f"⚠️ Aviso ao aplicar migration: {e}")
        print("Continuando com importação...")

def calcular_idade(data_nascimento):
    """Calcula idade a partir da data de nascimento"""
    if pd.isna(data_nascimento):
        return None
    try:
        if isinstance(data_nascimento, str):
            data_nasc = datetime.strptime(data_nascimento, '%d/%m/%Y')
        else:
            data_nasc = data_nascimento
        hoje = datetime.now()
        idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
        return idade
    except:
        return None

def limpar_cpf(cpf):
    """Remove formatação do CPF"""
    if pd.isna(cpf):
        return None
    return str(cpf).replace('.', '').replace('-', '').strip()

def limpar_telefone(telefone):
    """Remove formatação do telefone"""
    if pd.isna(telefone):
        return None
    return str(telefone).replace('(', '').replace(')', '').replace('-', '').replace(' ', '').strip()

def limpar_cep(cep):
    """Remove formatação do CEP"""
    if pd.isna(cep):
        return None
    return str(cep).replace('-', '').strip()

def importar_excel(arquivo, conn):
    """Importa dados do Excel para o banco"""
    try:
        print(f"\n📂 Lendo arquivo: {arquivo}")
        
        # Ler Excel
        df = pd.read_excel(arquivo)
        
        print(f"📊 Total de registros encontrados: {len(df)}")
        print(f"📋 Colunas: {list(df.columns)}")
        
        cursor = conn.cursor()
        
        # Buscar empresa_id da COOPSERVICOS
        cursor.execute("SELECT id FROM empresas WHERE razao_social = 'COOPSERVICOS' LIMIT 1")
        empresa = cursor.fetchone()
        
        if not empresa:
            print("⚠️ Empresa COOPSERVICOS não encontrada. Usando empresa_id = 20 (padrão)")
            empresa_id = 20
        else:
            empresa_id = empresa[0]
            print(f"✅ Empresa COOPSERVICOS encontrada - ID: {empresa_id}")
        
        # Mapear colunas do Excel para campos do banco
        mapeamento_colunas = {
            'Nome': 'nome',
            'Nacionalidade': 'nacionalidade',
            'Estado Civil': 'estado_civil',
            'Data de Nascimento': 'data_nascimento',
            'Idade': 'idade',
            'CPF': 'cpf',
            'Profissão': 'profissao',
            'Rua / Av.': 'rua_av',
            'Numero da residência': 'numero_residencia',
            'Complemento referente': 'complemento',
            'Bairro': 'bairro',
            'Cidade': 'cidade',
            'Estado': 'estado',
            'CEP': 'cep',
            'CELULAR': 'celular',
            'E-Mail': 'email',
            'Chave Pix': 'chave_pix',
            'PIS/PASEP': 'pis_pasep'
        }
        
        # Preparar dados para inserção
        dados_inserir = []
        erros = []
        
        for idx, row in df.iterrows():
            try:
                # Processar data de nascimento
                data_nasc = None
                if not pd.isna(row.get('Data de Nascimento')):
                    if isinstance(row['Data de Nascimento'], str):
                        data_nasc = datetime.strptime(row['Data de Nascimento'], '%d/%m/%Y').date()
                    else:
                        data_nasc = row['Data de Nascimento']
                
                # Calcular idade
                idade = calcular_idade(row.get('Data de Nascimento'))
                
                dados = {
                    'empresa_id': empresa_id,  # Adicionar empresa_id
                    'nome': str(row.get('Nome', '')).strip() if not pd.isna(row.get('Nome')) else None,
                    'nacionalidade': str(row.get('Nacionalidade', '')).strip() if not pd.isna(row.get('Nacionalidade')) else None,
                    'estado_civil': str(row.get('Estado Civil', '')).strip() if not pd.isna(row.get('Estado Civil')) else None,
                    'data_nascimento': data_nasc,
                    'idade': idade,
                    'cpf': limpar_cpf(row.get('CPF')),
                    'profissao': str(row.get('Profissão', '')).strip() if not pd.isna(row.get('Profissão')) else None,
                    'rua_av': str(row.get('Rua / Av.', '')).strip() if not pd.isna(row.get('Rua / Av.')) else None,
                    'numero_residencia': str(row.get('Numero da residência', '')).strip() if not pd.isna(row.get('Numero da residência')) else None,
                    'complemento': str(row.get('Complemento referente', '')).strip() if not pd.isna(row.get('Complemento referente')) else None,
                    'bairro': str(row.get('Bairro', '')).strip() if not pd.isna(row.get('Bairro')) else None,
                    'cidade': str(row.get('Cidade', '')).strip() if not pd.isna(row.get('Cidade')) else None,
                    'estado': str(row.get('Estado', '')).strip()[:2] if not pd.isna(row.get('Estado')) else None,
                    'cep': limpar_cep(row.get('CEP')),
                    'celular': limpar_telefone(row.get('CELULAR')),
                    'email': str(row.get('E-Mail', '')).strip() if not pd.isna(row.get('E-Mail')) else None,
                    'chave_pix': str(row.get('Chave Pix', '')).strip() if not pd.isna(row.get('Chave Pix')) else None,
                    'pis_pasep': str(row.get('PIS/PASEP', '')).strip() if not pd.isna(row.get('PIS/PASEP')) else None,
                    'ativo': True
                }
                
                dados_inserir.append(dados)
                
            except Exception as e:
                erros.append(f"Linha {idx + 2}: {str(e)}")
                print(f"⚠️ Erro na linha {idx + 2}: {e}")
        
        print(f"\n✅ Dados processados: {len(dados_inserir)} registros válidos")
        
        if erros:
            print(f"⚠️ {len(erros)} erros encontrados:")
            for erro in erros[:5]:  # Mostrar apenas primeiros 5
                print(f"   - {erro}")
        
        # Inserir no banco
        if dados_inserir:
            print("\n💾 Inserindo dados no banco...")
            
            sql_insert = """
                INSERT INTO funcionarios (
                    empresa_id, nome, nacionalidade, estado_civil, data_nascimento, idade,
                    cpf, profissao, rua_av, numero_residencia, complemento,
                    bairro, cidade, estado, cep, celular, email, chave_pix,
                    pis_pasep, ativo
                ) VALUES (
                    %(empresa_id)s, %(nome)s, %(nacionalidade)s, %(estado_civil)s, %(data_nascimento)s, %(idade)s,
                    %(cpf)s, %(profissao)s, %(rua_av)s, %(numero_residencia)s, %(complemento)s,
                    %(bairro)s, %(cidade)s, %(estado)s, %(cep)s, %(celular)s, %(email)s, %(chave_pix)s,
                    %(pis_pasep)s, %(ativo)s
                )
                ON CONFLICT (cpf) DO UPDATE SET
                    empresa_id = EXCLUDED.empresa_id,
                    nome = EXCLUDED.nome,
                    nacionalidade = EXCLUDED.nacionalidade,
                    estado_civil = EXCLUDED.estado_civil,
                    data_nascimento = EXCLUDED.data_nascimento,
                    idade = EXCLUDED.idade,
                    profissao = EXCLUDED.profissao,
                    rua_av = EXCLUDED.rua_av,
                    numero_residencia = EXCLUDED.numero_residencia,
                    complemento = EXCLUDED.complemento,
                    bairro = EXCLUDED.bairro,
                    cidade = EXCLUDED.cidade,
                    estado = EXCLUDED.estado,
                    cep = EXCLUDED.cep,
                    celular = EXCLUDED.celular,
                    email = EXCLUDED.email,
                    chave_pix = EXCLUDED.chave_pix,
                    pis_pasep = EXCLUDED.pis_pasep
            """
            
            inseridos = 0
            atualizados = 0
            
            for idx, dados in enumerate(dados_inserir, 1):
                try:
                    cursor.execute(sql_insert, dados)
                    inseridos += 1
                    
                    # Commit a cada 10 registros
                    if idx % 10 == 0:
                        conn.commit()
                        print(f"   💾 Checkpoint: {inseridos} registros processados...")
                        
                except psycopg2.IntegrityError as e:
                    conn.rollback()
                    if 'duplicate key' in str(e).lower():
                        atualizados += 1
                    else:
                        print(f"⚠️ Erro ao inserir {dados.get('nome')}: {e}")
                except Exception as e:
                    conn.rollback()
                    print(f"⚠️ Erro ao inserir {dados.get('nome')}: {e}")
            
            # Commit final
            conn.commit()
            
            print(f"\n✅ Importação concluída!")
            print(f"   📊 {inseridos} funcionários importados com sucesso!")
            
            # Mostrar estatísticas
            cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE ativo = TRUE")
            total_ativos = cursor.fetchone()[0]
            print(f"   👥 Total de funcionários ativos: {total_ativos}")
        
        cursor.close()
        
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {arquivo}")
        print("Certifique-se de que o arquivo coop.xlsx está no mesmo diretório deste script.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao importar Excel: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Função principal"""
    print("=" * 60)
    print("🚀 IMPORTADOR DE FUNCIONÁRIOS - coop.xlsx")
    print("=" * 60)
    
    # Conectar ao banco
    conn = conectar_banco()
    
    # Aplicar migration
    aplicar_migration(conn)
    
    # Importar Excel
    arquivo = 'coop.xlsx'
    
    # Verificar se arquivo existe, se não, tentar diretório pai
    if not os.path.exists(arquivo):
        arquivo_alternativo = os.path.join('..', 'coop.xlsx')
        if os.path.exists(arquivo_alternativo):
            arquivo = arquivo_alternativo
            print(f"📁 Arquivo encontrado em: {arquivo}")
    
    importar_excel(arquivo, conn)
    
    # Fechar conexão
    conn.close()
    print("\n👋 Conexão fechada. Importação finalizada!")
    print("=" * 60)

if __name__ == "__main__":
    main()
