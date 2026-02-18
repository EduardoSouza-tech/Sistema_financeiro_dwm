"""
Corrigir certificados com nome "⏳ Validando certificado..." no Railway
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# URL do Railway
DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("🔧 CORRIGINDO CERTIFICADOS COM NOME INVÁLIDO")
print("=" * 80)

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    # Buscar certificados com nome problemático
    print("\n📋 1. Buscando certificados com nome inválido...")
    
    cursor.execute("""
        SELECT id, nome_certificado, cnpj, ativo, valido_ate
        FROM certificados_digitais
        WHERE nome_certificado LIKE '%Validando%' 
        OR nome_certificado LIKE '%⏳%'
        OR nome_certificado = ''
        OR nome_certificado IS NULL
    """)
    
    certificados_invalidos = cursor.fetchall()
    
    if not certificados_invalidos:
        print("   ✅ Nenhum certificado com nome inválido encontrado!")
        cursor.close()
        conn.close()
        exit(0)
    
    print(f"   ⚠️  Encontrados {len(certificados_invalidos)} certificado(s) com nome inválido:")
    
    for cert in certificados_invalidos:
        print(f"\n   → ID: {cert['id']}")
        print(f"     Nome atual: '{cert['nome_certificado']}'")
        print(f"     CNPJ: {cert['cnpj']}")
        print(f"     Ativo: {'Sim' if cert['ativo'] else 'Não'}")
        print(f"     Validade: {cert['valido_ate']}")
    
    # Corrigir cada certificado
    print("\n📋 2. Corrigindo certificados...")
    
    corrigidos = 0
    for cert in certificados_invalidos:
        # Buscar razão social da empresa pelo CNPJ
        cursor.execute("""
            SELECT razao_social, nome_fantasia
            FROM empresas
            WHERE cnpj = %s
            LIMIT 1
        """, (cert['cnpj'],))
        
        empresa = cursor.fetchone()
        
        if empresa and empresa['razao_social']:
            novo_nome = f"Certificado Digital A1 - {empresa['razao_social']}"
        elif empresa and empresa['nome_fantasia']:
            novo_nome = f"Certificado Digital A1 - {empresa['nome_fantasia']}"
        else:
            # Formatar CNPJ: 56.237.242/0001-58
            cnpj_formatado = cert['cnpj']
            if cnpj_formatado and len(cnpj_formatado) == 14:
                cnpj_formatado = f"{cnpj_formatado[:2]}.{cnpj_formatado[2:5]}.{cnpj_formatado[5:8]}/{cnpj_formatado[8:12]}-{cnpj_formatado[12:]}"
            novo_nome = f"Certificado Digital A1 - CNPJ {cnpj_formatado}"
        
        # Atualizar certificado
        cursor.execute("""
            UPDATE certificados_digitais
            SET nome_certificado = %s
            WHERE id = %s
        """, (novo_nome, cert['id']))
        
        print(f"\n   ✅ Certificado ID {cert['id']} corrigido:")
        print(f"      Antigo: '{cert['nome_certificado']}'")
        print(f"      Novo:   '{novo_nome}'")
        
        corrigidos += 1
    
    conn.commit()
    
    # Verificar resultado
    print("\n" + "=" * 80)
    print("🔍 VERIFICAÇÃO FINAL")
    print("=" * 80)
    
    cursor.execute("""
        SELECT id, nome_certificado, cnpj, ativo
        FROM certificados_digitais
        WHERE ativo = TRUE
    """)
    
    certificados_ativos = cursor.fetchall()
    
    if certificados_ativos:
        print(f"\n✅ Certificado(s) ativo(s) ({len(certificados_ativos)}):")
        for cert in certificados_ativos:
            print(f"\n   ID {cert['id']}: {cert['nome_certificado']}")
            print(f"   CNPJ: {cert['cnpj']}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print(f"✅ {corrigidos} CERTIFICADO(S) CORRIGIDO(S) COM SUCESSO!")
    print("=" * 80)
    print("\n🎯 AÇÃO:")
    print("   Recarregue a página com Ctrl+F5 e veja o nome correto do certificado!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
