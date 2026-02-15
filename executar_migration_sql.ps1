# Script SQL para adicionar coluna associacao
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " EXECUTANDO MIGRATION: Coluna 'associacao' na tabela lancamentos" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# URL do Railway
$DATABASE_URL = "postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway"

# SQL para executar
$SQL = @"
-- Verificar se coluna existe
DO `$`$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='lancamentos' AND column_name='associacao'
    ) THEN
        -- Adicionar coluna associacao
        ALTER TABLE lancamentos ADD COLUMN associacao TEXT DEFAULT '';
        
        -- Copiar valores de numero_documento para associacao (sincronização inicial)
        UPDATE lancamentos SET associacao = COALESCE(numero_documento, '') WHERE associacao = '';
        
        -- Criar índice
        CREATE INDEX IF NOT EXISTS idx_lancamentos_associacao 
        ON lancamentos(associacao) 
        WHERE associacao IS NOT NULL AND associacao != '';
        
        RAISE NOTICE 'Coluna associacao adicionada com sucesso!';
    ELSE
        RAISE NOTICE 'Coluna associacao já existe';
    END IF;
END
`$`$;
"@

# Verificar se psql está disponível
$psql = Get-Command psql -ErrorAction SilentlyContinue

if ($psql) {
    Write-Host "✅ psql encontrado, executando migration via psql..." -ForegroundColor Green
    Write-Host ""
    
    $SQL | & psql $DATABASE_URL
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "================================================================================" -ForegroundColor Cyan
        Write-Host " ✅ MIGRATION CONCLUÍDA COM SUCESSO!" -ForegroundColor Green
        Write-Host "================================================================================" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Erro ao executar SQL" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  psql não encontrado, tentando via Python..." -ForegroundColor Yellow
    Write-Host ""
    
    # Criar script Python temporário
    $pythonScript = @"
import psycopg2
import sys

DATABASE_URL = "$DATABASE_URL"

sql = """
-- Verificar se coluna existe
DO \$\$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='lancamentos' AND column_name='associacao'
    ) THEN
        -- Adicionar coluna associacao
        ALTER TABLE lancamentos ADD COLUMN associacao TEXT DEFAULT '';
        
        -- Copiar valores de numero_documento para associacao (sincronização inicial)
        UPDATE lancamentos SET associacao = COALESCE(numero_documento, '') WHERE associacao = '';
        
        -- Criar índice
        CREATE INDEX IF NOT EXISTS idx_lancamentos_associacao 
        ON lancamentos(associacao) 
        WHERE associacao IS NOT NULL AND associacao != '';
        
        RAISE NOTICE 'Coluna associacao adicionada com sucesso!';
    ELSE
        RAISE NOTICE 'Coluna associacao já existe';
    END IF;
END
\$\$;
"""

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Migration executada com sucesso!")
    sys.exit(0)
except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)
"@
    
    $tempFile = [System.IO.Path]::GetTempFileName() + ".py"
    $pythonScript | Out-File -FilePath $tempFile -Encoding UTF8
    
    # Tentar diferentes versões do Python
    $pythonCommands = @("python", "python3", "py", "python.exe")
    $success = $false
    
    foreach ($cmd in $pythonCommands) {
        try {
            $pythonExe = Get-Command $cmd -ErrorAction SilentlyContinue
            if ($pythonExe) {
                Write-Host "Tentando com $cmd..." -ForegroundColor Gray
                & $cmd $tempFile
                if ($LASTEXITCODE -eq 0) {
                    $success = $true
                    break
                }
            }
        } catch {
            continue
        }
    }
    
    Remove-Item $tempFile -ErrorAction SilentlyContinue
    
    if ($success) {
        Write-Host ""
        Write-Host "================================================================================" -ForegroundColor Cyan
        Write-Host " ✅ MIGRATION CONCLUÍDA COM SUCESSO!" -ForegroundColor Green
        Write-Host "================================================================================" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Não foi possível executar a migration com Python" -ForegroundColor Red
        Write-Host ""
        Write-Host "Execute o SQL manualmente no Railway:" -ForegroundColor Yellow
        Write-Host $SQL -ForegroundColor Gray
        exit 1
    }
}
