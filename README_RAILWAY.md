# Sistema Financeiro

Sistema completo de gestão financeira com controle de receitas, despesas, fluxo de caixa, DRE e comparativos de períodos.

## 🚀 Deploy no Railway

### Passo 1: Criar PostgreSQL

1. No Railway, clique em **"New"** → **"Add PostgreSQL"**
2. O Railway criará automaticamente as variáveis de ambiente:
   - `PGHOST`
   - `PGPORT`
   - `PGUSER`
   - `PGPASSWORD`
   - `PGDATABASE`

### Passo 2: Configurar o Projeto

1. Conecte este repositório ao Railway
2. Adicione as variáveis de ambiente:
   ```
   DATABASE_TYPE=postgresql
   ENABLE_AUTO_TEST=true  # (Opcional) Ativa auto-teste na inicialização
   ```

### Passo 3: Deploy

O Railway detectará automaticamente:
- `Procfile` → Comando de inicialização
- `requirements_web.txt` → Dependências Python
- `runtime.txt` → Versão do Python

## 📦 Dependências

- Flask 3.0.0
- Flask-CORS 4.0.0
- psycopg2-binary 2.9.9 (PostgreSQL)

## 🗄️ Bancos de Dados Suportados

- **PostgreSQL** (Produção - Railway)
- **MySQL** (Opcional)
- **SQLite** (Desenvolvimento local)

## 🔧 Desenvolvimento Local

1. Clone o repositório:
```bash
git clone https://github.com/MatheusAlcantara20/Sistema-Financeiro.git
cd Sistema-Financeiro
```

2. Crie um ambiente virtual:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. Instale as dependências:
```bash
pip install -r requirements_web.txt
```

4. Execute o servidor:
```bash
python web_server.py
```

5. Acesse: `http://localhost:5000`

## 📊 Funcionalidades

- ✅ Gestão de contas bancárias
- ✅ Controle de receitas e despesas
- ✅ Categorização com subcategorias
- ✅ Fluxo de caixa com filtros
- ✅ DRE (Demonstração do Resultado do Exercício)
- ✅ Comparativo de períodos
- ✅ Exportação para PDF e Excel
- ✅ Dashboard com gráficos
- ✅ Gestão de clientes e fornecedores
- ✅ Lançamentos recorrentes

## 🎯 Variáveis de Ambiente (Railway)

```env
# Tipo de banco (obrigatório)
DATABASE_TYPE=postgresql

# PostgreSQL (fornecido automaticamente pelo Railway)
PGHOST=xxxxx.railway.app
PGPORT=5432
PGUSER=postgres
PGPASSWORD=xxxxx
PGDATABASE=railway

# Porta (fornecido automaticamente pelo Railway)
PORT=5000
```

## 📝 Licença

Este projeto é de código aberto.

## 👨‍💻 Autor

Matheus Alcantara
