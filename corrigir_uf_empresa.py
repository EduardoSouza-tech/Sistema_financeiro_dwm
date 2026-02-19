"""
Script para corrigir o UF da empresa no banco de dados
Permite atualizar o campo 'estado' da tabela empresas
"""
import sys
import os

# Adiciona o diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import get_db_connection

def listar_empresas():
    """Lista todas as empresas para escolher qual corrigir"""
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, razao_social, cnpj, estado, cidade
            FROM empresas
            ORDER BY id
        """)
        return cursor.fetchall()

def atualizar_uf_empresa(empresa_id, novo_uf):
    """Atualiza o UF de uma empresa"""
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        
        # Busca dados antigos
        cursor.execute("""
            SELECT razao_social, estado
            FROM empresas
            WHERE id = %s
        """, (empresa_id,))
        
        empresa_antiga = cursor.fetchone()
        if not empresa_antiga:
            print(f"❌ Empresa ID {empresa_id} não encontrada!")
            return False
        
        if hasattr(empresa_antiga, '_asdict'):
            razao_social = empresa_antiga._asdict()['razao_social']
            uf_antigo = empresa_antiga._asdict()['estado']
        else:
            razao_social = empresa_antiga[0]
            uf_antigo = empresa_antiga[1]
        
        print(f"\n📋 Empresa: {razao_social}")
        print(f"   UF Atual: {uf_antigo}")
        print(f"   UF Novo: {novo_uf}")
        
        # Atualiza
        cursor.execute("""
            UPDATE empresas
            SET estado = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (novo_uf.upper(), empresa_id))
        
        conn.commit()
        
        print(f"✅ UF atualizado com sucesso!")
        return True

def menu_interativo():
    """Menu interativo para corrigir UF"""
    print("\n" + "="*80)
    print("🔧 CORREÇÃO DE UF DA EMPRESA")
    print("="*80 + "\n")
    
    try:
        # Lista empresas
        empresas = listar_empresas()
        
        if not empresas:
            print("❌ Nenhuma empresa cadastrada!")
            return
        
        print("📊 EMPRESAS CADASTRADAS:\n")
        for emp in empresas:
            if hasattr(emp, '_asdict'):
                emp_dict = emp._asdict()
                print(f"   ID: {emp_dict['id']} | {emp_dict['razao_social']}")
                print(f"   CNPJ: {emp_dict['cnpj']} | UF: {emp_dict['estado']} | Cidade: {emp_dict['cidade']}")
            else:
                print(f"   ID: {emp[0]} | {emp[1]}")
                print(f"   CNPJ: {emp[2]} | UF: {emp[3]} | Cidade: {emp[4]}")
            print()
        
        # Solicita ID da empresa
        print("\n" + "-"*80)
        empresa_id = input("Digite o ID da empresa que deseja corrigir (ou 'q' para sair): ").strip()
        
        if empresa_id.lower() == 'q':
            print("Cancelado pelo usuário.")
            return
        
        try:
            empresa_id = int(empresa_id)
        except ValueError:
            print("❌ ID inválido!")
            return
        
        # Solicita novo UF
        print("\n📍 ESTADOS VÁLIDOS:")
        print("   AC, AL, AP, AM, BA, CE, DF, ES, GO, MA, MT, MS, MG,")
        print("   PA, PB, PR, PE, PI, RJ, RN, RS, RO, RR, SC, SP, SE, TO")
        
        novo_uf = input("\nDigite o UF correto (sigla com 2 letras): ").strip().upper()
        
        if len(novo_uf) != 2:
            print("❌ UF deve ter exatamente 2 letras!")
            return
        
        ufs_validos = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
                       'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
                       'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
        
        if novo_uf not in ufs_validos:
            print(f"❌ '{novo_uf}' não é um UF válido!")
            return
        
        # Confirma
        print("\n⚠️  CONFIRMAÇÃO:")
        confirma = input(f"Tem certeza que deseja alterar o UF da empresa ID {empresa_id} para '{novo_uf}'? (s/n): ").strip().lower()
        
        if confirma != 's':
            print("Cancelado pelo usuário.")
            return
        
        # Executa atualização
        if atualizar_uf_empresa(empresa_id, novo_uf):
            print("\n" + "="*80)
            print("✅ CORREÇÃO CONCLUÍDA COM SUCESSO!")
            print("="*80)
            print("\n💡 PRÓXIMOS PASSOS:")
            print("   1. Recadastre o certificado digital")
            print("   2. O sistema agora usará o UF correto automaticamente")
            print()
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

def correcao_direta(empresa_id, novo_uf):
    """Correção direta sem menu (para uso em scripts)"""
    print("\n" + "="*80)
    print(f"🔧 CORRIGINDO UF DA EMPRESA ID {empresa_id} PARA '{novo_uf}'")
    print("="*80 + "\n")
    
    try:
        if atualizar_uf_empresa(empresa_id, novo_uf):
            print("\n✅ Correção concluída!")
        else:
            print("\n❌ Falha na correção!")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Verifica se foi passado argumentos na linha de comando
    if len(sys.argv) == 3:
        # Modo direto: python corrigir_uf_empresa.py EMPRESA_ID UF
        empresa_id = int(sys.argv[1])
        novo_uf = sys.argv[2].upper()
        correcao_direta(empresa_id, novo_uf)
    else:
        # Modo interativo
        menu_interativo()
