# 🏢 Sistema Financeiro DWM

Sistema completo de gestão financeira e operacional para condomínios, desenvolvido com Flask e PostgreSQL.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [API Endpoints](#-api-endpoints)
- [Deploy](#-deploy)
- [Desenvolvimento](#-desenvolvimento)

## 🎯 Visão Geral

Sistema ERP completo para gestão de condomínios, incluindo:
- Controle financeiro (contas, lançamentos, categorias)
- Gestão de clientes e fornecedores
- Menu operacional (contratos, agenda, estoque, etc)
- Relatórios e análises
- Interface web responsiva

## ✨ Funcionalidades

### 💰 Gestão Financeira
- **Contas Bancárias**: Cadastro e controle de múltiplas contas
- **Lançamentos**: Receitas e despesas com categorização
- **Categorias**: Organização personalizada de transações
- **Relatórios**: Análise de fluxo de caixa e balanços

### 👥 Cadastros
- **Clientes**: Gestão completa de clientes do condomínio
- **Fornecedores**: Controle de prestadores de serviço
- **Usuários**: Sistema de autenticação e permissões

### 🎯 Menu Operacional
- **Contratos**: Gestão de contratos com clientes
- **Agenda**: Agendamentos e eventos
- **Produtos**: Controle de estoque de produtos
- **Kits**: Pacotes e combos de produtos
- **Tags**: Organização e categorização
- **Templates**: Modelos para equipes
- **Sessões**: Registro de sessões de trabalho
- **Comissões**: Controle de comissionamentos
- **Sessão-Equipe**: Alocação de equipes em sessões

## 🛠 Tecnologias

### Backend
- **Python 3.11+**
- **Flask 3.0.0**: Framework web
- **PostgreSQL**: Banco de dados principal (Railway)
- **SQLite**: Desenvolvimento local
- **psycopg2**: Driver PostgreSQL
- **Flask-CORS**: Suporte a CORS

### Frontend
- **HTML5/CSS3**
- **JavaScript (ES6+)**
- **Bootstrap 5**: Framework CSS
- **Chart.js**: Gráficos e visualizações

### Deploy
- **Railway**: Hospedagem e banco de dados
- **Gunicorn**: Servidor WSGI
- **Git/GitHub**: Controle de versão

## 📦 Instalação

### Pré-requisitos
```bash
Python 3.11 ou superior
PostgreSQL 16 (para produção)
Git
```

### Instalação Local

1. **Clone o repositório**
```bash
git clone https://github.com/EduardoSouza-tech/Sistema_financeiro_dwm.git
cd Sistema_financeiro_dwm
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure o banco de dados**
```bash
python -c "import database; db = database.DatabaseManager(); db.criar_tabelas(); print('Tabelas criadas!')"
```

5. **Execute o servidor**
```bash
python web_server.py
```

Acesse: `http://localhost:5000`

## ⚙️ Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Tipo de banco de dados
DATABASE_TYPE=postgresql  # ou 'sqlite' para desenvolvimento

# PostgreSQL (Railway)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Flask
SECRET_KEY=sua-chave-secreta-aqui
FLASK_ENV=production  # ou 'development'
```

### Arquivo `config.py`

```python
import os

# Tipo de banco de dados
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')

# PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL', '')

# SQLite (desenvolvimento local)
SQLITE_DB = 'sistema_financeiro.db'
```

## 📁 Estrutura do Projeto

```
sistema_financeiro/
├── static/
│   ├── app.js              # Frontend JavaScript
│   ├── style.css           # Estilos customizados
│   ├── modals.js           # Funções de modais
│   ├── pdf_functions.js    # Geração de PDFs
│   └── excel_functions.js  # Exportação Excel
├── templates/
│   ├── index.html          # Interface principal
│   └── interface.html      # Interface alternativa
├── backups/                # Backups automáticos
├── documentacao/           # Documentação adicional
├── database.py             # Abstração do banco
├── database_postgresql.py  # Implementação PostgreSQL
├── database_sqlite.py      # Implementação SQLite
├── models.py               # Modelos de dados
├── web_server.py           # API Flask
├── config.py               # Configurações
├── requirements.txt        # Dependências
├── requirements_web.txt    # Dependências web
├── runtime.txt             # Versão Python (Railway)
├── Procfile                # Configuração Railway
└── README.md               # Este arquivo
```

## 🔌 API Endpoints

### Gestão Financeira

#### Contas Bancárias
```
GET    /api/contas           # Listar contas
POST   /api/contas           # Criar conta
DELETE /api/contas/<id>      # Excluir conta
```

#### Lançamentos
```
GET    /api/lancamentos      # Listar lançamentos
POST   /api/lancamentos      # Criar lançamento
PUT    /api/lancamentos/<id> # Atualizar lançamento
DELETE /api/lancamentos/<id> # Excluir lançamento
POST   /api/lancamentos/<id>/pagar    # Pagar lançamento
POST   /api/lancamentos/<id>/cancelar # Cancelar lançamento
```

#### Categorias
```
GET    /api/categorias       # Listar categorias
POST   /api/categorias       # Criar categoria
PUT    /api/categorias/<id>  # Atualizar categoria
DELETE /api/categorias/<id>  # Excluir categoria
```

### Cadastros

#### Clientes
```
GET    /api/clientes         # Listar clientes
POST   /api/clientes         # Criar cliente
PUT    /api/clientes/<id>    # Atualizar cliente
DELETE /api/clientes/<id>    # Excluir cliente
```

#### Fornecedores
```
GET    /api/fornecedores     # Listar fornecedores
POST   /api/fornecedores     # Criar fornecedor
PUT    /api/fornecedores/<id> # Atualizar fornecedor
DELETE /api/fornecedores/<id> # Excluir fornecedor
```

### Menu Operacional

#### Contratos
```
GET    /api/contratos        # Listar contratos
POST   /api/contratos        # Criar contrato
PUT    /api/contratos/<id>   # Atualizar contrato
DELETE /api/contratos/<id>   # Excluir contrato
```

#### Agenda
```
GET    /api/agenda           # Listar eventos
POST   /api/agenda           # Criar evento
PUT    /api/agenda/<id>      # Atualizar evento
DELETE /api/agenda/<id>      # Excluir evento
```

#### Produtos
```
GET    /api/estoque/produtos # Listar produtos
POST   /api/estoque/produtos # Criar produto
PUT    /api/estoque/produtos/<id>    # Atualizar produto
DELETE /api/estoque/produtos/<id>    # Excluir produto
```

#### Kits
```
GET    /api/kits             # Listar kits
POST   /api/kits             # Criar kit
PUT    /api/kits/<id>        # Atualizar kit
DELETE /api/kits/<id>        # Excluir kit
```

#### Tags
```
GET    /api/tags             # Listar tags
POST   /api/tags             # Criar tag
PUT    /api/tags/<id>        # Atualizar tag
DELETE /api/tags/<id>        # Excluir tag
```

#### Templates de Equipe
```
GET    /api/templates-equipe # Listar templates
POST   /api/templates-equipe # Criar template
PUT    /api/templates-equipe/<id>    # Atualizar template
DELETE /api/templates-equipe/<id>    # Excluir template
```

#### Sessões
```
GET    /api/sessoes          # Listar sessões
POST   /api/sessoes          # Criar sessão
PUT    /api/sessoes/<id>     # Atualizar sessão
DELETE /api/sessoes/<id>     # Excluir sessão
```

#### Comissões
```
GET    /api/comissoes        # Listar comissões
POST   /api/comissoes        # Criar comissão
PUT    /api/comissoes/<id>   # Atualizar comissão
DELETE /api/comissoes/<id>   # Excluir comissão
```

#### Sessão-Equipe
```
GET    /api/sessao-equipe    # Listar alocações
POST   /api/sessao-equipe    # Criar alocação
PUT    /api/sessao-equipe/<id>      # Atualizar alocação
DELETE /api/sessao-equipe/<id>      # Excluir alocação
```

## 🚀 Deploy

### Railway

1. **Crie uma conta no Railway**
   - Acesse: https://railway.app
   - Conecte sua conta GitHub

2. **Configure o PostgreSQL**
   - Adicione um serviço PostgreSQL
   - Copie a `DATABASE_URL`

3. **Deploy do projeto**
   - Conecte o repositório GitHub
   - Configure as variáveis de ambiente
   - Railway fará deploy automático

4. **Variáveis necessárias**
```
DATABASE_TYPE=postgresql
DATABASE_URL=<sua-url-postgresql>
SECRET_KEY=<chave-segura>
```

### Arquivos de Deploy

- **Procfile**: Configura o servidor Gunicorn
```
web: gunicorn web_server:app
```

- **runtime.txt**: Define versão do Python
```
python-3.11.5
```

- **requirements_web.txt**: Dependências de produção

## 👨‍💻 Desenvolvimento

### Estrutura de Código

#### Backend - Padrão de Delegação
```python
# database.py - Abstração
def adicionar_cliente(dados: Dict) -> int:
    return _delegate_to_specific_db('adicionar_cliente', dados)

# database_postgresql.py - Implementação
def adicionar_cliente(dados: Dict) -> int:
    db = DatabaseManager()
    conn = db.get_connection()
    # ... código PostgreSQL
```

#### Frontend - Padrão Modal
```javascript
// app.js
function openModalCliente(clienteId = null) {
    if (clienteId) {
        // Editar - carregar dados
        fetch(`/api/clientes/${clienteId}`)
            .then(response => response.json())
            .then(cliente => {
                // Preencher formulário
            });
    } else {
        // Criar - formulário vazio
    }
    modal.show();
}
```

### Banco de Dados

#### Tabelas Principais

**Financeiro**
- `contas_bancarias`: Contas do sistema
- `lancamentos`: Receitas e despesas
- `categorias`: Categorias de lançamentos

**Cadastros**
- `clientes`: Clientes do condomínio
- `fornecedores`: Prestadores de serviço

**Operacional**
- `contratos`: Contratos com clientes
- `agenda`: Eventos e agendamentos
- `produtos`: Estoque de produtos
- `kits`: Pacotes de produtos
- `kit_itens`: Itens dos kits
- `tags`: Tags de organização
- `templates_equipe`: Templates para equipes
- `sessoes`: Sessões de trabalho
- `comissoes`: Comissões
- `sessao_equipe`: Alocação de equipes

### Scripts Úteis

#### Migração SQLite → PostgreSQL
```bash
python migrar_para_railway.py
```

#### Backup do Banco
```bash
python -c "import database; database.backup_database()"
```

#### Teste de Endpoints
```bash
python testar_endpoints.py
```

#### Verificar Instalação
```bash
python verificar_instalacao.py
```

### Testes

```bash
# Testar menu operacional
python testar_menu_operacional.py

# Testar endpoints
python testar_endpoints.py

# Testar tipos de data
python testar_tipos_data.py
```

## 🔒 Segurança

- ✅ Validação de entrada em todos os endpoints
- ✅ Prepared statements (proteção SQL Injection)
- ✅ CORS configurado adequadamente
- ✅ Variáveis de ambiente para dados sensíveis
- ✅ Backups automáticos do banco de dados

## 📊 Recursos Avançados

### Exportação de Dados
- **PDF**: Geração de relatórios em PDF
- **Excel**: Exportação de tabelas para Excel
- **Backup**: Sistema automático de backup

### Formatação
- **Moeda**: Formatação brasileira (R$)
- **Datas**: Formato dd/mm/aaaa
- **Números**: Separadores de milhar

### Interface
- **Responsiva**: Funciona em desktop e mobile
- **Modais**: Interface limpa com modais Bootstrap
- **Validação**: Validação em tempo real
- **Feedback**: Alertas e notificações

## 🐛 Troubleshooting

### Erro de Conexão PostgreSQL
```bash
# Verifique a DATABASE_URL
echo $DATABASE_URL

# Teste a conexão
python -c "import database_postgresql; db = database_postgresql.DatabaseManager(); print(db.test_connection())"
```

### Tabelas não criadas
```bash
# Recrie as tabelas
python criar_tabelas_railway.py
```

### Erro 500 em endpoints
```bash
# Verifique os logs
tail -f railway.log  # Railway
python web_server.py # Local
```

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👥 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 📧 Contato

**Desenvolvedor**: Eduardo Souza  
**GitHub**: [@EduardoSouza-tech](https://github.com/EduardoSouza-tech)  
**Projeto**: [Sistema Financeiro DWM](https://github.com/EduardoSouza-tech/Sistema_financeiro_dwm)

## 🙏 Agradecimentos

- Flask por ser um framework incrível
- Railway pela hospedagem gratuita
- Bootstrap pela interface responsiva
- Comunidade Python pelo suporte

---

**Desenvolvido com ❤️ para gestão eficiente de condomínios**
