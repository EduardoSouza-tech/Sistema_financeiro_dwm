# Script para popular a versão 4 do Plano de Contas no Railway
# Executa: .\popular_versao4_railway.ps1

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  POPULAR VERSÃO 4 - PLANO DE CONTAS RAILWAY" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Obter DATABASE_URL do Railway
$databaseUrl = Read-Host "Cole a DATABASE_URL do Railway"

if ([string]::IsNullOrWhiteSpace($databaseUrl)) {
    Write-Host "❌ DATABASE_URL vazia!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔄 Executando popular_versao4_railway.py..." -ForegroundColor Yellow

# Criar arquivo Python temporário
$pythonScript = @"
import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL = os.environ.get('DATABASE_URL')
EMPRESA_ID = 20
VERSAO_ID = 4

print("🔗 Conectando ao banco de dados...")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)
print("✅ Conectado!")

# Verificar se versão existe e está vazia
cursor.execute("""
    SELECT COUNT(*) as total
    FROM plano_contas
    WHERE empresa_id = %s AND versao_id = %s AND deleted_at IS NULL
""", (EMPRESA_ID, VERSAO_ID))

total = cursor.fetchone()['total']
print(f"📊 Versão {VERSAO_ID} tem {total} contas")

if total > 0:
    print(f"⚠️ Versão já tem {total} contas. Abortando.")
    conn.close()
    exit(0)

print(f"🚀 Populando versão {VERSAO_ID}...")

# Plano de contas padrão simplificado
contas = [
    # ATIVO
    {'codigo': '1', 'nome': 'ATIVO', 'parent': None, 'nivel': 1, 'tipo': 'sintetica', 'classif': 'ativo', 'natureza': 'devedora'},
    {'codigo': '1.1', 'nome': 'ATIVO CIRCULANTE', 'parent': '1', 'nivel': 2, 'tipo': 'sintetica', 'classif': 'ativo', 'natureza': 'devedora'},
    {'codigo': '1.1.01', 'nome': 'Disponível', 'parent': '1.1', 'nivel': 3, 'tipo': 'sintetica', 'classif': 'ativo', 'natureza': 'devedora'},
    {'codigo': '1.1.01.001', 'nome': 'Caixa', 'parent': '1.1.01', 'nivel': 4, 'tipo': 'analitica', 'classif': 'ativo', 'natureza': 'devedora'},
    {'codigo': '1.1.01.002', 'nome': 'Bancos Conta Movimento', 'parent': '1.1.01', 'nivel': 4, 'tipo': 'analitica', 'classif': 'ativo', 'natureza': 'devedora'},
    {'codigo': '1.1.02', 'nome': 'Clientes', 'parent': '1.1', 'nivel': 3, 'tipo': 'sintetica', 'classif': 'ativo', 'natureza': 'devedora'},
    {'codigo': '1.1.02.001', 'nome': 'Clientes a Receber', 'parent': '1.1.02', 'nivel': 4, 'tipo': 'analitica', 'classif': 'ativo', 'natureza': 'devedora'},
    
    # PASSIVO
    {'codigo': '2', 'nome': 'PASSIVO', 'parent': None, 'nivel': 1, 'tipo': 'sintetica', 'classif': 'passivo', 'natureza': 'credora'},
    {'codigo': '2.1', 'nome': 'PASSIVO CIRCULANTE', 'parent': '2', 'nivel': 2, 'tipo': 'sintetica', 'classif': 'passivo', 'natureza': 'credora'},
    {'codigo': '2.1.01', 'nome': 'Fornecedores', 'parent': '2.1', 'nivel': 3, 'tipo': 'sintetica', 'classif': 'passivo', 'natureza': 'credora'},
    {'codigo': '2.1.01.001', 'nome': 'Fornecedores a Pagar', 'parent': '2.1.01', 'nivel': 4, 'tipo': 'analitica', 'classif': 'passivo', 'natureza': 'credora'},
    
    # PATRIMÔNIO LÍQUIDO
    {'codigo': '3', 'nome': 'PATRIMÔNIO LÍQUIDO', 'parent': None, 'nivel': 1, 'tipo': 'sintetica', 'classif': 'patrimonio_liquido', 'natureza': 'credora'},
    {'codigo': '3.1', 'nome': 'Capital Social', 'parent': '3', 'nivel': 2, 'tipo': 'analitica', 'classif': 'patrimonio_liquido', 'natureza': 'credora'},
    {'codigo': '3.2', 'nome': 'Reservas', 'parent': '3', 'nivel': 2, 'tipo': 'sintetica', 'classif': 'patrimonio_liquido', 'natureza': 'credora'},
    {'codigo': '3.2.01', 'nome': 'Reserva Legal', 'parent': '3.2', 'nivel': 3, 'tipo': 'analitica', 'classif': 'patrimonio_liquido', 'natureza': 'credora'},
    
    # RECEITA
    {'codigo': '4', 'nome': 'RECEITAS', 'parent': None, 'nivel': 1, 'tipo': 'sintetica', 'classif': 'receita', 'natureza': 'credora'},
    {'codigo': '4.1', 'nome': 'RECEITA OPERACIONAL', 'parent': '4', 'nivel': 2, 'tipo': 'sintetica', 'classif': 'receita', 'natureza': 'credora'},
    {'codigo': '4.1.01', 'nome': 'Receita de Vendas', 'parent': '4.1', 'nivel': 3, 'tipo': 'sintetica', 'classif': 'receita', 'natureza': 'credora'},
    {'codigo': '4.1.01.001', 'nome': 'Venda de Produtos', 'parent': '4.1.01', 'nivel': 4, 'tipo': 'analitica', 'classif': 'receita', 'natureza': 'credora'},
    {'codigo': '4.1.01.002', 'nome': 'Prestação de Serviços', 'parent': '4.1.01', 'nivel': 4, 'tipo': 'analitica', 'classif': 'receita', 'natureza': 'credora'},
    
    # DESPESA
    {'codigo': '5', 'nome': 'DESPESAS', 'parent': None, 'nivel': 1, 'tipo': 'sintetica', 'classif': 'despesa', 'natureza': 'devedora'},
    {'codigo': '5.1', 'nome': 'DESPESAS OPERACIONAIS', 'parent': '5', 'nivel': 2, 'tipo': 'sintetica', 'classif': 'despesa', 'natureza': 'devedora'},
    {'codigo': '5.1.01', 'nome': 'Despesas Administrativas', 'parent': '5.1', 'nivel': 3, 'tipo': 'sintetica', 'classif': 'despesa', 'natureza': 'devedora'},
    {'codigo': '5.1.01.001', 'nome': 'Salários e Encargos', 'parent': '5.1.01', 'nivel': 4, 'tipo': 'analitica', 'classif': 'despesa', 'natureza': 'devedora'},
    {'codigo': '5.1.01.002', 'nome': 'Aluguel', 'parent': '5.1.01', 'nivel': 4, 'tipo': 'analitica', 'classif': 'despesa', 'natureza': 'devedora'},
    {'codigo': '5.1.01.003', 'nome': 'Energia Elétrica', 'parent': '5.1.01', 'nivel': 4, 'tipo': 'analitica', 'classif': 'despesa', 'natureza': 'devedora'},
]

# Mapa de códigos para IDs
mapa = {}
criadas = 0

for conta in contas:
    # Resolver parent_id
    parent_id = None
    if conta['parent']:
        parent_id = mapa.get(conta['parent'])
        if not parent_id:
            print(f"⚠️ Conta {conta['codigo']}: parent {conta['parent']} não encontrado")
            continue
    
    # Calcular ordem
    cursor.execute("""
        SELECT COALESCE(MAX(ordem), 0) + 1 as proxima
        FROM plano_contas
        WHERE empresa_id = %s AND versao_id = %s 
          AND parent_id IS NOT DISTINCT FROM %s AND deleted_at IS NULL
    """, (EMPRESA_ID, VERSAO_ID, parent_id))
    
    ordem = cursor.fetchone()['proxima']
    
    # Inserir conta
    cursor.execute("""
        INSERT INTO plano_contas 
            (empresa_id, versao_id, codigo, descricao, parent_id, nivel, ordem,
             tipo_conta, classificacao, natureza, is_bloqueada, 
             requer_centro_custo, permite_lancamento)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        EMPRESA_ID,
        VERSAO_ID,
        conta['codigo'],
        conta['nome'],
        parent_id,
        conta['nivel'],
        ordem,
        conta['tipo'],
        conta['classif'],
        conta['natureza'],
        False,
        False,
        conta['tipo'] == 'analitica'
    ))
    
    conta_id = cursor.fetchone()['id']
    mapa[conta['codigo']] = conta_id
    criadas += 1
    print(f"  ✅ {conta['codigo']} - {conta['nome']}")

conn.commit()
cursor.close()
conn.close()

print("")
print(f"✅ SUCESSO! {criadas} contas criadas na versão {VERSAO_ID}")
print("🔄 Recarregue a página do Plano de Contas!")
"@

# Salvar script Python
$pythonScript | Out-File -FilePath "temp_popular_v4.py" -Encoding UTF8

# Executar Python com DATABASE_URL como variável de ambiente
$env:DATABASE_URL = $databaseUrl
python temp_popular_v4.py

# Limpar arquivo temporário
Remove-Item "temp_popular_v4.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "✅ Script finalizado!" -ForegroundColor Green
Write-Host "Recarregue a página (Ctrl+F5) para ver as contas" -ForegroundColor Yellow
Write-Host "===============================================" -ForegroundColor Cyan
