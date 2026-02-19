"""
Script para aplicar plano de contas padrão via Railway - FORÇAR CRIAÇÃO
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

# Adicionar diretório ao path para importar funções
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*80)
print("🚀 APLICAR PLANO DE CONTAS PADRÃO - RAILWAY")
print("="*80)
print()

DATABASE_URL = input("📋 Cole a DATABASE_URL do Railway: ").strip()

if not DATABASE_URL:
    print("❌ DATABASE_URL vazia!")
    exit(1)

print(f"\n🔗 Conectando: {DATABASE_URL[:30]}...")

try:
    # Conectar
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    print("✅ Conectado!\n")
    
    # Listar empresas
    cursor.execute("SELECT id, razao_social FROM empresas ORDER BY id")
    empresas = cursor.fetchall()
    
    print("📊 EMPRESAS DISPONÍVEIS:")
    for emp in empresas:
        print(f"   {emp['id']}. {emp['razao_social']}")
    
    print()
    empresa_id = int(input("📋 Digite o ID da empresa para aplicar o plano: "))
    
    # Verificar se já existe
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM plano_contas_versao
        WHERE empresa_id = %s
    """, (empresa_id,))
    
    total = cursor.fetchone()['total']
    
    if total > 0:
        print(f"\n⚠️ A empresa {empresa_id} já possui {total} versão(ões) do plano de contas!")
        resposta = input("   Deseja criar uma nova versão mesmo assim? (s/n): ").lower()
        
        if resposta != 's':
            print("⏭️ Operação cancelada")
            exit(0)
    
    print(f"\n🚀 Aplicando plano de contas padrão para empresa {empresa_id}...")
    
    # Importar e executar
    from contabilidade_functions import importar_plano_padrao
    
    # Temporariamente definir conexão
    os.environ['USANDO_CONEXAO_MANUAL'] = 'true'
    os.environ['CONEXAO_MANUAL_URL'] = DATABASE_URL
    
    resultado = importar_plano_padrao(empresa_id, ano_fiscal=2026)
    
    if resultado.get('success'):
        print(f"\n✅ SUCESSO!")
        print(f"   📋 Versão ID: {resultado.get('versao_id')}")
        print(f"   📊 Contas criadas: {resultado.get('contas_criadas')}")
        print(f"   📝 Mensagem: {resultado.get('message')}")
        
        if resultado.get('erros'):
            print(f"\n⚠️ Erros encontrados ({len(resultado['erros'])}):")
            for erro in resultado['erros'][:5]:  # Mostrar só os 5 primeiros
                print(f"   • {erro}")
    else:
        print(f"\n❌ ERRO: {resultado.get('error')}")
    
    cursor.close()
    conn.close()
    
    print()
    print("="*80)
    print("✅ PROCESSO CONCLUÍDO")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
