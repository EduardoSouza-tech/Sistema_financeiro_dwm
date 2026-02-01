# 🚀 GUIA: Como Executar Migrations Direto no Railway

## 📋 Resumo
Este guia mostra como executar migrations SQL diretamente no banco PostgreSQL do Railway usando Python, sem precisar fazer deploy ou recarregar o servidor.

## ✅ Método Testado e Funcionando

### 1️⃣ Pré-requisitos

**Python instalado no sistema:**
```powershell
# Verificar se Python está instalado
Get-Command python* | Where-Object {$_.Source -notlike "*WindowsApps*"}
```

**Instalar psycopg2-binary:**
```powershell
C:\Users\Nasci\AppData\Local\Programs\Python\Python312\python.exe -m pip install psycopg2-binary
```

### 2️⃣ Credenciais do Railway

Acesse o Railway → PostgreSQL → **Variables** e copie:

```
Host: centerbeam.proxy.rlwy.net
Port: 12659
Database: railway
User: postgres
Password: JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT
```

Ou use a URL completa:
```
postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway
```

### 3️⃣ Script Python para Executar Migration

**Arquivo: `executar_migration_direto.py`**

```python
import sys
sys.path.insert(0, r'c:\Users\Nasci\OneDrive\Documents\Programas VS Code\DWM\sistema_financeiro\Sistema_financeiro_dwm')

try:
    import psycopg2
    
    print("="*80)
    print("🚀 EXECUTANDO MIGRATION NO RAILWAY")
    print("="*80)
    
    # CONECTAR ao Railway
    print("\n📡 Conectando...")
    conn = psycopg2.connect(
        host='centerbeam.proxy.rlwy.net',
        port=12659,
        database='railway',
        user='postgres',
        password='JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT'
    )
    cursor = conn.cursor()
    print("✅ CONECTADO!")
    
    # LER arquivo SQL da migration
    sql_file = r'c:\Users\Nasci\OneDrive\Documents\Programas VS Code\DWM\sistema_financeiro\Sistema_financeiro_dwm\migration_evento_funcionarios.sql'
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"\n📝 Executando {len(sql)} caracteres de SQL...")
    
    # EXECUTAR SQL
    cursor.execute(sql)
    conn.commit()
    print("✅ MIGRATION EXECUTADA E COMMITADA!")
    
    # VERIFICAR resultado
    cursor.execute("SELECT COUNT(*) FROM funcoes_evento")
    total = cursor.fetchone()[0]
    print(f"\n✅✅✅ {total} FUNÇÕES CRIADAS! ✅✅✅")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
    print("="*80)
    print("\n🔄 Recarregue a página (F5)")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
```

### 4️⃣ Como Executar

**Opção A: Via PowerShell**
```powershell
cd "c:\Users\Nasci\OneDrive\Documents\Programas VS Code\DWM\sistema_financeiro"
C:\Users\Nasci\AppData\Local\Programs\Python\Python312\python.exe executar_migration_direto.py
```

**Opção B: Via Batch (duplo clique)**

Criar arquivo `EXECUTAR_MIGRATION.bat`:
```batch
@echo off
cd /d "C:\Users\Nasci\OneDrive\Documents\Programas VS Code\DWM\sistema_financeiro"
echo ================================================================================
echo EXECUTANDO MIGRATION NO RAILWAY
echo ================================================================================
C:\Users\Nasci\AppData\Local\Programs\Python\Python312\python.exe executar_migration_direto.py
pause
```

## 📝 Template: Script Genérico para Qualquer Migration

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEMPLATE: Executar Migration Direto no Railway
"""
import psycopg2
import os

# ====================
# CONFIGURAÇÃO
# ====================
HOST = "centerbeam.proxy.rlwy.net"
PORT = 12659
DATABASE = "railway"
USER = "postgres"
PASSWORD = "JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT"

# Caminho do arquivo SQL da migration
SQL_FILE = "migration_evento_funcionarios.sql"  # ⬅️ ALTERAR AQUI

# Nome das tabelas para verificar (opcional)
TABELAS_ESPERADAS = ['funcoes_evento', 'evento_funcionarios']  # ⬅️ ALTERAR AQUI

# ====================
# EXECUÇÃO
# ====================
print("="*80)
print(f"🚀 EXECUTANDO MIGRATION: {SQL_FILE}")
print("="*80)

try:
    # CONECTAR
    print(f"\n📡 Conectando a {HOST}:{PORT}...")
    conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        database=DATABASE,
        user=USER,
        password=PASSWORD
    )
    cursor = conn.cursor()
    print("✅ CONECTADO!")
    
    # VERIFICAR SE TABELAS JÁ EXISTEM (opcional)
    if TABELAS_ESPERADAS:
        print("\n🔍 Verificando tabelas existentes...")
        placeholders = ', '.join(f"'{t}'" for t in TABELAS_ESPERADAS)
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name IN ({placeholders})
        """)
        count = cursor.fetchone()[0]
        print(f"   Encontradas: {count}/{len(TABELAS_ESPERADAS)} tabelas")
        
        if count == len(TABELAS_ESPERADAS):
            print("\n⚠️ TABELAS JÁ EXISTEM!")
            resposta = input("   Deseja reexecutar a migration? (s/N): ").lower()
            if resposta != 's':
                print("\n✅ Operação cancelada")
                cursor.close()
                conn.close()
                exit(0)
    
    # LER SQL
    print(f"\n📂 Lendo {SQL_FILE}...")
    sql_path = os.path.join(os.path.dirname(__file__), SQL_FILE)
    
    if not os.path.exists(sql_path):
        print(f"❌ ERRO: Arquivo não encontrado: {sql_path}")
        exit(1)
    
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"✅ SQL lido ({len(sql_content)} caracteres)")
    
    # EXECUTAR
    print("\n📝 EXECUTANDO MIGRATION...")
    cursor.execute(sql_content)
    conn.commit()
    print("✅ SQL EXECUTADO E COMMITADO!")
    
    # VERIFICAR RESULTADO
    if TABELAS_ESPERADAS:
        print("\n🔍 Verificando resultado...")
        cursor.execute(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name IN ({placeholders})
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"\n✅ {len(tables)} TABELAS:")
        for table in tables:
            print(f"   ✓ {table[0]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅✅✅ MIGRATION CONCLUÍDA COM SUCESSO! ✅✅✅")
    print("="*80)
    print("\n🔄 Recarregue a página (F5)")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
```

## 🔧 Alternativa: Query Console do Railway

Se preferir executar diretamente no Railway:

1. Acesse **Railway Dashboard** → PostgreSQL
2. Vá na aba **"Query"**
3. Cole o conteúdo COMPLETO do arquivo SQL
4. Clique em **"Run Query"**

## ⚠️ Problemas Comuns

### Erro: Python não encontrado
```powershell
# Encontrar Python instalado
Get-Command python* | Where-Object {$_.Source -notlike "*WindowsApps*"}

# Usar o caminho completo
C:\Users\Nasci\AppData\Local\Programs\Python\Python312\python.exe script.py
```

### Erro: psycopg2 não instalado
```powershell
python -m pip install psycopg2-binary
```

### Erro: Connection timeout
- Verificar se as credenciais estão corretas
- Verificar se o Railway não está em manutenção
- Usar a **DATABASE_PUBLIC_URL** (porta TCP proxy)

### Erro: "relation already exists"
- A migration já foi executada
- Adicionar `IF NOT EXISTS` nas cláusulas `CREATE TABLE`

## 📊 Histórico de Migrations

### Migration 1: Evento Funcionários (2026-02-01)
- ✅ **Arquivo:** `migration_evento_funcionarios.sql`
- ✅ **Tabelas:** `funcoes_evento`, `evento_funcionarios`
- ✅ **Executada em:** 2026-02-01
- ✅ **Status:** Sucesso (11 funções inseridas)

## 🎯 Boas Práticas

1. **Sempre verificar antes de executar:**
   - Checar se tabelas já existem
   - Fazer backup se necessário
   - Testar em ambiente local primeiro

2. **Usar transações:**
   ```python
   cursor.execute(sql)
   conn.commit()  # ✅ Commitar após sucesso
   ```

3. **Adicionar verificações:**
   ```sql
   -- Verificar dependências
   DO $$
   BEGIN
       IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'eventos') THEN
           RAISE EXCEPTION 'Tabela eventos não encontrada';
       END IF;
   END $$;
   ```

4. **Usar IF NOT EXISTS:**
   ```sql
   CREATE TABLE IF NOT EXISTS funcoes_evento (...)
   ```

5. **Documentar no código:**
   - Data de criação
   - Versão
   - Dependências
   - Rollback instructions

## 🔄 Rollback de Migration

Se precisar reverter a migration:

```sql
-- Rollback: migration_evento_funcionarios.sql
DROP TABLE IF EXISTS evento_funcionarios CASCADE;
DROP TABLE IF EXISTS funcoes_evento CASCADE;
```

Execute o rollback usando o mesmo método (script Python ou Query Console).

---

**Última atualização:** 2026-02-01  
**Autor:** Sistema Financeiro DWM  
**Status:** ✅ Testado e Funcionando
