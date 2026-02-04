"""
Debug: Verificar associação usuário x empresa
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URL_RAILWAY')

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Buscar usuário Operacional
    cursor.execute("""
        SELECT id, username, tipo, cliente_id, nome_completo, email
        FROM usuarios
        WHERE username = 'Operacional'
    """)
    usuario = cursor.fetchone()
    
    if usuario:
        print("\n" + "="*60)
        print("👤 USUÁRIO: Operacional")
        print("="*60)
        print(f"ID: {usuario[0]}")
        print(f"Username: {usuario[1]}")
        print(f"Tipo: {usuario[2]}")
        print(f"Cliente ID: {usuario[3]}")
        print(f"Nome Completo: {usuario[4]}")
        print(f"Email: {usuario[5]}")
        
        # Buscar empresas associadas
        cursor.execute("""
            SELECT empresa_id
            FROM usuario_empresas
            WHERE usuario_id = %s
        """, (usuario[0],))
        empresas = cursor.fetchall()
        
        print("\n🏢 EMPRESAS ASSOCIADAS:")
        for (emp_id,) in empresas:
            cursor.execute("SELECT razao_social FROM empresas WHERE id = %s", (emp_id,))
            razao = cursor.fetchone()
            nome = razao[0] if razao else "Desconhecida"
            print(f"   • ID {emp_id}: {nome}")
            
            # Contar funcionários dessa empresa
            cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE empresa_id = %s", (emp_id,))
            total = cursor.fetchone()[0]
            print(f"     └─ {total} funcionários")
        
        # Se tem cliente_id, verificar
        if usuario[3]:
            print(f"\n🔍 CLIENTE_ID = {usuario[3]}")
            cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE empresa_id = %s", (usuario[3],))
            total_cliente = cursor.fetchone()[0]
            print(f"   Funcionários: {total_cliente}")
    else:
        print("❌ Usuário 'Operacional' não encontrado")
    
    print("\n" + "="*60 + "\n")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
