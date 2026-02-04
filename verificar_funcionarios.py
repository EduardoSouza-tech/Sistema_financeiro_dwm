"""
Script para verificar quantos funcionários existem no banco de dados
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Conectar ao banco de dados Railway
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URL_RAILWAY')

if not DATABASE_URL:
    print("❌ DATABASE_URL_RAILWAY não encontrado no .env")
    exit(1)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Contar total de funcionários
    cursor.execute("SELECT COUNT(*) FROM funcionarios")
    total = cursor.fetchone()[0]
    
    # Contar funcionários ativos
    cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE ativo = true")
    ativos = cursor.fetchone()[0]
    
    # Contar funcionários inativos
    cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE ativo = false")
    inativos = cursor.fetchone()[0]
    
    # Contar funcionários por empresa
    cursor.execute("""
        SELECT empresa_id, COUNT(*) as total
        FROM funcionarios
        GROUP BY empresa_id
        ORDER BY total DESC
    """)
    por_empresa = cursor.fetchall()
    
    print("\n" + "="*60)
    print("📊 ESTATÍSTICAS DE FUNCIONÁRIOS NO BANCO")
    print("="*60)
    print(f"\n📈 TOTAL GERAL: {total} funcionários")
    print(f"✅ Ativos: {ativos}")
    print(f"❌ Inativos: {inativos}")
    
    print("\n🏢 FUNCIONÁRIOS POR EMPRESA:")
    for emp_id, qtd in por_empresa:
        cursor.execute("SELECT razao_social FROM empresas WHERE id = %s", (emp_id,))
        razao = cursor.fetchone()
        nome_empresa = razao[0] if razao else f"Empresa ID {emp_id}"
        print(f"   • {nome_empresa}: {qtd} funcionários")
    
    # Verificar empresa COOPSERVICOS
    cursor.execute("""
        SELECT id, razao_social 
        FROM empresas 
        WHERE razao_social ILIKE '%coop%'
    """)
    coop = cursor.fetchall()
    
    if coop:
        print("\n🔍 EMPRESA COOPSERVICOS:")
        for emp_id, razao in coop:
            cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE empresa_id = %s", (emp_id,))
            total_coop = cursor.fetchone()[0]
            print(f"   • ID: {emp_id}")
            print(f"   • Razão Social: {razao}")
            print(f"   • Total de Funcionários: {total_coop}")
    
    # Mostrar alguns exemplos de funcionários
    cursor.execute("""
        SELECT id, nome, cpf, profissao, cidade, ativo
        FROM funcionarios
        ORDER BY id
        LIMIT 5
    """)
    exemplos = cursor.fetchall()
    
    print("\n📋 PRIMEIROS 5 FUNCIONÁRIOS:")
    for func in exemplos:
        status = "✅ Ativo" if func[5] else "❌ Inativo"
        print(f"   • ID {func[0]}: {func[1]} - CPF {func[2]} - {func[3] or 'Sem profissão'} - {func[4] or 'Sem cidade'} - {status}")
    
    print("\n" + "="*60 + "\n")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erro ao conectar ao banco: {e}")
    import traceback
    traceback.print_exc()
