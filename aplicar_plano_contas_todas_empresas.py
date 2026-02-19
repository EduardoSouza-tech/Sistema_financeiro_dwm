"""
Script para aplicar o Plano de Contas Padrão em todas as empresas do sistema
Execução única - 19/02/2026
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Carregar variáveis de ambiente do .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv não instalado, usar variáveis de ambiente do sistema

from database_postgresql import get_db_connection, log
from contabilidade_functions import importar_plano_padrao

def verificar_empresa_tem_plano(empresa_id):
    """Verifica se a empresa já possui plano de contas"""
    try:
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            # Verificar se existe alguma versão de plano de contas
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM plano_contas_versao
                WHERE empresa_id = %s
            """, (empresa_id,))
            
            resultado = cursor.fetchone()
            total = resultado['total'] if isinstance(resultado, dict) else resultado[0]
            
            return total > 0
            
    except Exception as e:
        log(f"Erro ao verificar plano da empresa {empresa_id}: {e}")
        return False


def aplicar_plano_todas_empresas():
    """
    Aplica o plano de contas padrão em todas as empresas que não o possuem
    """
    try:
        print("=" * 80)
        print("APLICAÇÃO DE PLANO DE CONTAS PADRÃO - TODAS AS EMPRESAS")
        print("=" * 80)
        print()
        
        # Usar allow_global=True para consultar todas as empresas
        with get_db_connection(allow_global=True) as conn:
            cursor = conn.cursor()
            
            # Buscar todas as empresas ativas
            cursor.execute("""
                SELECT id, razao_social, nome_fantasia, cnpj
                FROM empresas
                WHERE ativo = TRUE
                ORDER BY id
            """)
            
            empresas = cursor.fetchall()
            
            if not empresas:
                print("❌ Nenhuma empresa encontrada no sistema.")
                return
            
            print(f"📊 Total de empresas ativas: {len(empresas)}\n")
            
            # Estatísticas
            total_empresas = len(empresas)
            empresas_com_plano = 0
            empresas_aplicadas = 0
            empresas_erro = 0
            
            for empresa in empresas:
                empresa_id = empresa['id'] if isinstance(empresa, dict) else empresa[0]
                razao_social = empresa['razao_social'] if isinstance(empresa, dict) else empresa[1]
                nome_fantasia = empresa['nome_fantasia'] if isinstance(empresa, dict) else empresa[2]
                cnpj = empresa['cnpj'] if isinstance(empresa, dict) else empresa[3]
                
                nome_exibir = nome_fantasia or razao_social
                cnpj_exibir = f" - CNPJ: {cnpj}" if cnpj else ""
                
                print(f"🏢 Empresa ID {empresa_id}: {nome_exibir}{cnpj_exibir}")
                
                # Verificar se já possui plano de contas
                if verificar_empresa_tem_plano(empresa_id):
                    print(f"   ✅ JÁ POSSUI plano de contas configurado")
                    empresas_com_plano += 1
                else:
                    # Aplicar plano padrão
                    print(f"   ⏳ Aplicando plano de contas padrão...")
                    
                    try:
                        resultado = importar_plano_padrao(empresa_id, 2026)
                        
                        if resultado.get('success'):
                            contas_importadas = resultado.get('contas_importadas', 0)
                            print(f"   ✅ APLICADO com sucesso! {contas_importadas} contas importadas")
                            empresas_aplicadas += 1
                        else:
                            erro = resultado.get('error', 'Erro desconhecido')
                            print(f"   ❌ ERRO ao aplicar: {erro}")
                            empresas_erro += 1
                            
                    except Exception as e:
                        print(f"   ❌ EXCEÇÃO ao aplicar: {e}")
                        empresas_erro += 1
                
                print()
            
            # Resumo final
            print("=" * 80)
            print("RESUMO DA APLICAÇÃO")
            print("=" * 80)
            print(f"📊 Total de empresas processadas: {total_empresas}")
            print(f"✅ Empresas que JÁ tinham plano: {empresas_com_plano}")
            print(f"🎉 Empresas com plano APLICADO agora: {empresas_aplicadas}")
            print(f"❌ Empresas com erro: {empresas_erro}")
            print("=" * 80)
            
            if empresas_aplicadas > 0:
                print(f"\n🎉 Sucesso! Plano de contas aplicado em {empresas_aplicadas} empresa(s)!")
            
            if empresas_erro > 0:
                print(f"\n⚠️  Atenção: {empresas_erro} empresa(s) com erro. Verifique os logs acima.")
            
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Iniciando aplicação do Plano de Contas Padrão...\n")
    aplicar_plano_todas_empresas()
    print("\n✅ Processo finalizado!\n")
