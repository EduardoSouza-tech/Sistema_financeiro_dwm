"""
Script para verificar os dados cadastrados da empresa
Para identificar por que o UF está sendo preenchido incorretamente
"""
import sys
import os

# Adiciona o diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import get_db_connection

def verificar_empresas():
    """Verifica todos os dados de empresas cadastradas"""
    print("\n" + "="*80)
    print("🔍 VERIFICAÇÃO DE DADOS DAS EMPRESAS CADASTRADAS")
    print("="*80 + "\n")
    
    try:
        with get_db_connection(allow_global=True) as conn:
            cursor = conn.cursor()
            
            # Busca todas as empresas
            cursor.execute("""
                SELECT 
                    id,
                    razao_social,
                    nome_fantasia,
                    cnpj,
                    estado,
                    cidade,
                    ativo
                FROM empresas
                ORDER BY id
            """)
            
            empresas = cursor.fetchall()
            
            if not empresas:
                print("❌ Nenhuma empresa encontrada no banco de dados!\n")
                return
            
            print(f"✅ Total de empresas encontradas: {len(empresas)}\n")
            
            # Mapa de códigos UF
            uf_para_codigo = {
                'AC': '12', 'AL': '27', 'AP': '16', 'AM': '13', 'BA': '29',
                'CE': '23', 'DF': '53', 'ES': '32', 'GO': '52', 'MA': '21',
                'MT': '51', 'MS': '50', 'MG': '31', 'PA': '15', 'PB': '25',
                'PR': '41', 'PE': '26', 'PI': '22', 'RJ': '33', 'RN': '24',
                'RS': '43', 'RO': '11', 'RR': '14', 'SC': '42', 'SP': '35',
                'SE': '28', 'TO': '17'
            }
            
            for emp in empresas:
                if hasattr(emp, '_asdict'):
                    emp_dict = emp._asdict()
                else:
                    emp_dict = dict(zip(['id', 'razao_social', 'nome_fantasia', 'cnpj', 'estado', 'cidade', 'ativo'], emp))
                
                print(f"📋 Empresa ID: {emp_dict['id']}")
                print(f"   Razão Social: {emp_dict['razao_social']}")
                print(f"   Nome Fantasia: {emp_dict['nome_fantasia']}")
                print(f"   CNPJ: {emp_dict['cnpj']}")
                print(f"   🌎 Estado (UF): {emp_dict['estado']}")
                print(f"   🏙️  Cidade: {emp_dict['cidade']}")
                
                # Verifica o mapeamento para código IBGE
                estado_upper = (emp_dict['estado'] or '').upper()
                cuf = uf_para_codigo.get(estado_upper, 'NÃO MAPEADO')
                
                if estado_upper == 'SP':
                    print(f"   ⚠️  CÓDIGO IBGE: {cuf} ← ESTE É O PROBLEMA!")
                    print(f"   ⚠️  Sistema vai usar código 35 (São Paulo) por causa deste campo!")
                elif estado_upper == 'MG':
                    print(f"   ✅ CÓDIGO IBGE: {cuf} (correto para MG)")
                else:
                    print(f"   📊 CÓDIGO IBGE: {cuf}")
                
                print(f"   Status: {'✅ Ativo' if emp_dict['ativo'] else '❌ Inativo'}")
                print()
            
            # Verifica certificados cadastrados para essas empresas
            print("\n" + "="*80)
            print("📜 CERTIFICADOS DIGITAIS CADASTRADOS")
            print("="*80 + "\n")
            
            cursor.execute("""
                SELECT 
                    c.id,
                    c.empresa_id,
                    e.razao_social,
                    c.nome_certificado,
                    c.cnpj,
                    c.cuf,
                    c.ativo
                FROM certificados_digitais c
                JOIN empresas e ON e.id = c.empresa_id
                ORDER BY c.id
            """)
            
            certificados = cursor.fetchall()
            
            if not certificados:
                print("ℹ️  Nenhum certificado cadastrado ainda.\n")
            else:
                # Mapa reverso (código → sigla)
                codigo_para_uf = {v: k for k, v in uf_para_codigo.items()}
                
                for cert in certificados:
                    if hasattr(cert, '_asdict'):
                        cert_dict = cert._asdict()
                    else:
                        cert_dict = dict(zip(['id', 'empresa_id', 'razao_social', 'nome_certificado', 'cnpj', 'cuf', 'ativo'], cert))
                    
                    uf_sigla = codigo_para_uf.get(str(cert_dict['cuf']), '?')
                    
                    print(f"🔐 Certificado ID: {cert_dict['id']}")
                    print(f"   Empresa: {cert_dict['razao_social']} (ID: {cert_dict['empresa_id']})")
                    print(f"   Nome: {cert_dict['nome_certificado']}")
                    print(f"   CNPJ: {cert_dict['cnpj']}")
                    print(f"   UF Cadastrada: {cert_dict['cuf']} ({uf_sigla})")
                    print(f"   Status: {'✅ Ativo' if cert_dict['ativo'] else '❌ Inativo'}")
                    print()
            
    except Exception as e:
        print(f"\n❌ ERRO ao verificar empresas: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ VERIFICAÇÃO CONCLUÍDA")
    print("="*80 + "\n")

if __name__ == "__main__":
    verificar_empresas()
